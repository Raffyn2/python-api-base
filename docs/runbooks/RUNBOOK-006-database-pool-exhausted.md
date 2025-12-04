# RUNBOOK-006: Database Connection Pool Exhausted

**Alert:** DatabaseConnectionPoolCritical
**Severity:** P0 (Critical)
**Component:** Database
**Response Time:** 2 minutes

---

## 📋 Overview

Database connection pool has reached maximum capacity (>95% utilization). New database operations cannot acquire connections, causing requests to timeout or fail.

---

## 🚨 Symptoms

- Alert `DatabaseConnectionPoolCritical` firing
- HTTP requests timing out or returning 500 errors
- Application logs showing "Connection pool exhausted" errors
- Grafana showing connection pool at/near 100%

**Example Errors:**
```
[ERROR] sqlalchemy.exc.TimeoutError: QueuePool limit of size 20 overflow 10 reached
[ERROR] Failed to acquire database connection after 30.0 seconds
[ERROR] Connection pool exhausted - rejecting new requests
```

---

## 🔍 Diagnosis

### 1. Check Current Pool Status

```bash
# Check pool utilization
curl http://prometheus:9090/api/v1/query \
  -d 'query=(db_pool_connections_active / db_pool_connections_max) * 100'

# Expected: > 95%

# Check active connections
curl http://prometheus:9090/api/v1/query \
  -d 'query=db_pool_connections_active'

# Check idle connections
curl http://prometheus:9090/api/v1/query \
  -d 'query=db_pool_connections_idle'
```

### 2. Identify Long-Running Queries

```sql
-- Connect to database
psql -h postgres -U app_user -d app_db

-- Find long-running queries (> 30 seconds)
SELECT
    pid,
    now() - query_start AS duration,
    state,
    query
FROM pg_stat_activity
WHERE state != 'idle'
  AND query NOT LIKE '%pg_stat_activity%'
  AND (now() - query_start) > interval '30 seconds'
ORDER BY duration DESC;
```

**Example Output:**
```
 pid  | duration  | state  | query
------+-----------+--------+---------------------------------------
 1234 | 00:05:23  | active | SELECT * FROM orders WHERE...
 5678 | 00:02:15  | active | UPDATE users SET status...
```

### 3. Check for Connection Leaks

```bash
# Check application logs for unclosed connections
kubectl logs -l app=api --tail=500 | grep -i "connection\|leak"

# Check for transactions not committed/rolled back
kubectl logs -l app=api --tail=500 | grep -i "transaction"
```

### 4. Analyze Connection Wait Time

```bash
# Check connection wait time
curl http://prometheus:9090/api/v1/query \
  -d 'query=histogram_quantile(0.95,
    sum(rate(db_pool_wait_time_seconds_bucket[5m])) by (le)
  ) * 1000'

# If > 1000ms, pool is heavily contended
```

### 5. Review Recent Code Changes

```bash
# Check recent deployments
kubectl rollout history deployment/api

# Check recent database-related code changes
git log --oneline --since="1 day ago" -- src/infrastructure/db/
```

---

## 🔧 Mitigation

### Option 1: Kill Long-Running Queries (Immediate)

```sql
-- Find queries to kill
SELECT pid, query_start, state, query
FROM pg_stat_activity
WHERE state = 'active'
  AND (now() - query_start) > interval '5 minutes'
ORDER BY query_start;

-- Kill specific query
SELECT pg_terminate_backend(1234);  -- Replace with actual PID

-- Kill all long-running queries (CAREFUL!)
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'active'
  AND pid != pg_backend_pid()
  AND (now() - query_start) > interval '5 minutes';
```

**Expected:** Immediate release of connections

### Option 2: Increase Pool Size Temporarily

```bash
# Method 1: Environment Variable (requires restart)
kubectl set env deployment/api \
  DATABASE_POOL_SIZE=40 \
  DATABASE_POOL_MAX_OVERFLOW=20

# Apply changes
kubectl rollout restart deployment/api

# Method 2: Direct configuration (if supported)
curl -X POST http://api:8000/admin/config \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "database": {
      "pool_size": 40,
      "max_overflow": 20
    }
  }'
```

**Expected:** Pool capacity doubles (20→40)

### Option 3: Restart Application

```bash
# Quick restart to reset connections
kubectl rollout restart deployment/api

# Wait for rollout
kubectl rollout status deployment/api

# Verify pool reset
curl http://prometheus:9090/api/v1/query \
  -d 'query=db_pool_connections_active'
```

**Expected:** Connections reset to baseline

### Option 4: Scale Application

```bash
# Scale up to distribute load
kubectl scale deployment/api --replicas=6  # From 3 to 6

# Verify scaling
kubectl get pods -l app=api

# Monitor pool utilization across pods
watch 'kubectl top pods -l app=api'
```

**Expected:** Load distributed, per-pod connection usage reduced

---

## ✅ Resolution

### 1. Root Cause Analysis

**Common Causes:**

#### A. Connection Leaks
```python
# BAD: Connection not returned to pool
async def get_user(user_id):
    conn = await pool.acquire()
    result = await conn.fetch("SELECT * FROM users WHERE id=$1", user_id)
    # Missing: await pool.release(conn)
    return result

# GOOD: Use context manager
async def get_user(user_id):
    async with pool.acquire() as conn:
        result = await conn.fetch("SELECT * FROM users WHERE id=$1", user_id)
        return result
```

#### B. Long-Running Transactions
```python
# BAD: Transaction held too long
async with session.begin():
    users = await session.execute(select(User))
    # Expensive operation with transaction open
    await process_users(users)  # Takes 60 seconds!
    await session.commit()

# GOOD: Minimize transaction scope
users = await session.execute(select(User))
processed_data = await process_users(users)  # Outside transaction

async with session.begin():
    await session.execute(update(User).values(processed_data))
    await session.commit()
```

#### C. N+1 Query Problem
```python
# BAD: N+1 queries (1 + N connections)
users = await session.execute(select(User)).scalars().all()
for user in users:
    orders = await session.execute(
        select(Order).where(Order.user_id == user.id)
    ).scalars().all()

# GOOD: Eager loading (1 connection)
users = await session.execute(
    select(User).options(selectinload(User.orders))
).scalars().all()
```

#### D. Missing Connection Timeout
```python
# BAD: No timeout
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    # Missing timeout!
)

# GOOD: With timeout
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30.0,  # Timeout after 30s
    pool_recycle=3600,  # Recycle connections after 1h
)
```

### 2. Fix Root Cause

**Update SQLAlchemy Configuration:**
```python
# src/infrastructure/db/session.py

engine = create_async_engine(
    settings.DATABASE_URL,
    # Pool configuration
    pool_size=20,  # Base connections
    max_overflow=10,  # Extra connections
    pool_timeout=30.0,  # Wait timeout
    pool_recycle=3600,  # Recycle after 1h
    pool_pre_ping=True,  # Verify connection health

    # Statement timeout (PostgreSQL)
    connect_args={
        "server_settings": {
            "statement_timeout": "30000",  # 30s timeout
        }
    },

    # Logging
    echo_pool=True,  # Log pool events (development only)
)
```

**Add Connection Lifecycle Middleware:**
```python
# src/infrastructure/db/middleware/connection_tracking.py

from contextlib import asynccontextmanager

class ConnectionTrackingMiddleware:
    """Track connection lifecycle and detect leaks."""

    def __init__(self, engine):
        self.engine = engine
        self.active_connections = {}

    @asynccontextmanager
    async def track_connection(self):
        conn_id = id(self)
        self.active_connections[conn_id] = {
            "acquired_at": time.time(),
            "stack_trace": traceback.format_stack(),
        }

        try:
            async with self.engine.connect() as conn:
                yield conn
        finally:
            duration = time.time() - self.active_connections[conn_id]["acquired_at"]
            if duration > 60.0:  # Held for > 1 minute
                logger.warning(
                    f"Connection held for {duration:.2f}s",
                    extra={
                        "connection_id": conn_id,
                        "stack_trace": self.active_connections[conn_id]["stack_trace"],
                    }
                )
            del self.active_connections[conn_id]
```

### 3. Verify Resolution

```bash
# 1. Check pool utilization dropped
curl http://prometheus:9090/api/v1/query \
  -d 'query=(db_pool_connections_active / db_pool_connections_max) * 100'

# Expected: < 70%

# 2. Check no long-running queries
psql -c "
SELECT count(*)
FROM pg_stat_activity
WHERE state = 'active'
  AND (now() - query_start) > interval '30 seconds';
"

# Expected: 0

# 3. Monitor connection wait time
curl http://prometheus:9090/api/v1/query \
  -d 'query=histogram_quantile(0.95,
    sum(rate(db_pool_wait_time_seconds_bucket[5m])) by (le)
  ) * 1000'

# Expected: < 100ms
```

---

## 🛡️ Prevention

### 1. Set Proper Pool Configuration

```python
# Recommended configuration
DATABASE_POOL_SIZE = 20  # Per instance
DATABASE_POOL_MAX_OVERFLOW = 10  # Additional connections
DATABASE_POOL_TIMEOUT = 30.0  # Seconds
DATABASE_POOL_RECYCLE = 3600  # Recycle after 1h

# Calculate total connections needed
# Formula: (instances * pool_size) + (instances * max_overflow)
# Example: (3 instances * 20) + (3 * 10) = 90 max connections
# Ensure PostgreSQL max_connections > 90 + buffer (e.g., 150)
```

### 2. Add Statement Timeout

```sql
-- Set statement timeout at database level
ALTER DATABASE app_db SET statement_timeout = '30s';

-- Or per connection
SET statement_timeout = '30s';
```

### 3. Implement Connection Pooler (PgBouncer)

```yaml
# kubernetes/pgbouncer-deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pgbouncer
spec:
  template:
    spec:
      containers:
      - name: pgbouncer
        image: pgbouncer/pgbouncer:1.21
        env:
        - name: POOL_MODE
          value: "transaction"  # Connection pooling mode
        - name: MAX_CLIENT_CONN
          value: "1000"  # Max client connections
        - name: DEFAULT_POOL_SIZE
          value: "25"  # Connections to PostgreSQL
```

### 4. Add Monitoring

```python
# Export pool metrics
from prometheus_client import Gauge

pool_connections_active = Gauge(
    "db_pool_connections_active",
    "Number of active database connections"
)

pool_connections_idle = Gauge(
    "db_pool_connections_idle",
    "Number of idle database connections"
)

# Update metrics periodically
@app.on_event("startup")
async def start_pool_monitoring():
    async def update_metrics():
        while True:
            pool_connections_active.set(engine.pool.checked_out_connections())
            pool_connections_idle.set(engine.pool.idle())
            await asyncio.sleep(10)

    asyncio.create_task(update_metrics())
```

### 5. Add Alerts

```yaml
# Already configured in prometheus-alerts-http-infrastructure.yml
- alert: DatabaseConnectionPoolCritical
  expr: (db_pool_connections_active / db_pool_connections_max) * 100 > 95
  for: 2m
  labels:
    severity: critical
```

---

## 📊 Monitoring

### Key Metrics

```promql
# Pool utilization
(db_pool_connections_active / db_pool_connections_max) * 100

# Connection wait time p95
histogram_quantile(0.95,
  sum(rate(db_pool_wait_time_seconds_bucket[5m])) by (le)
) * 1000

# Active connections trend
rate(db_pool_connections_active[5m])

# Long-running query count (in PostgreSQL)
count(pg_stat_activity{state="active", duration_seconds>30})
```

### Dashboards

- **Infrastructure Dashboard:** `https://grafana.example.com/d/infrastructure`
- **Database Pool Panel:** Real-time utilization
- **Connection Wait Time:** Latency monitoring

---

## 📞 Escalation

### Response Times

| Severity | Response Time | Team |
|----------|---------------|------|
| P0 | 2 minutes | On-Call Engineer |
| P1 | 15 minutes | Database Team |

### Contacts

- **On-Call:** PagerDuty escalation
- **Database Team:** @database-team (Slack)
- **DevOps:** @devops-team (Slack)
- **#database-alerts:** Slack channel

---

**Version:** 1.0
**Last Updated:** 2025-01-02
**Next Review:** 2025-04-01
