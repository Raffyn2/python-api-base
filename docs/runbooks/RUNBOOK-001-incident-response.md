# RUNBOOK-001: Incident Response Guide

**Version:** 1.0
**Last Updated:** 2025-01-02
**Owner:** DevOps Team
**Status:** Active

---

## 📋 Quick Reference

| Incident Type | Priority | Response Time | Runbook |
|---------------|----------|---------------|---------|
| Service Down | P0 | 5 minutes | [RB-002](#rb-002-service-down) |
| High Error Rate | P0 | 10 minutes | [RB-003](#rb-003-high-error-rate) |
| Circuit Breaker Open | P1 | 15 minutes | [RB-004](#rb-004-circuit-breaker-open) |
| Slow Queries | P1 | 30 minutes | [RB-005](#rb-005-slow-queries) |
| DB Pool Exhausted | P0 | 10 minutes | [RB-006](#rb-006-database-pool-exhausted) |

---

## 🚨 General Incident Response Process

### 1. ACKNOWLEDGE (0-2 minutes)

**Actions:**
```bash
# 1. Acknowledge alert in monitoring system
# 2. Join incident channel
#    Slack: #incidents
#    Teams: Incidents Channel

# 3. Declare severity
#    P0: Service Down / Critical
#    P1: Degraded Performance
#    P2: Minor Issue
```

**Communication Template:**
```
🚨 INCIDENT DECLARED
Severity: P0/P1/P2
Service: [service-name]
Symptoms: [brief description]
Incident Commander: @[your-name]
Status Page: [link]
```

---

### 2. ASSESS (2-10 minutes)

**Health Checks:**
```bash
# Check service health
curl https://api.example.com/health/ready
curl https://api.example.com/health/live

# Check infrastructure
make health

# Check Docker containers
docker ps
docker logs api-container --tail=100

# Check database
psql -h localhost -U postgres -c "SELECT version();"
```

**Metrics Dashboard:**
- Navigate to Grafana: `https://grafana.example.com`
- Check dashboards:
  - HTTP Metrics
  - Infrastructure
  - Business Metrics

**Log Analysis:**
```bash
# Recent errors (last 10 minutes)
kubectl logs -l app=api --since=10m | grep ERROR

# Correlation ID search
kubectl logs -l app=api | grep "correlation_id:abc123"

# Slow queries
kubectl logs -l app=api | grep "Slow query"
```

---

### 3. MITIGATE (10-30 minutes)

**Quick Mitigations:**

#### A. Restart Service (if unresponsive)
```bash
# Kubernetes
kubectl rollout restart deployment/api

# Docker
docker restart api-container

# Systemd
systemctl restart api.service
```

#### B. Scale Up (if overloaded)
```bash
# Kubernetes - scale to 10 replicas
kubectl scale deployment/api --replicas=10

# Verify scaling
kubectl get pods -l app=api
```

#### C. Enable Circuit Breaker (if external service failing)
```bash
# Update config to enable resilience
# Edit config/production.yaml
resilience:
  circuit_breaker:
    enabled: true

# Apply config
kubectl apply -f config/production.yaml
kubectl rollout restart deployment/api
```

#### D. Rollback (if recent deployment caused issue)
```bash
# Kubernetes rollback
kubectl rollout undo deployment/api

# Verify rollback
kubectl rollout status deployment/api
kubectl get pods -l app=api
```

---

### 4. RESOLVE (30+ minutes)

**Root Cause Analysis:**
1. Review recent changes (last 24h)
2. Analyze metrics trends
3. Check external dependencies
4. Review error logs in detail

**Permanent Fix:**
1. Identify root cause
2. Implement fix
3. Test in staging
4. Deploy to production
5. Monitor for 30 minutes

---

### 5. DOCUMENT (Post-Incident)

**Incident Report Template:**
```markdown
# Incident Report: [YYYY-MM-DD] [Brief Title]

## Summary
- **Date:** YYYY-MM-DD HH:MM UTC
- **Duration:** X hours Y minutes
- **Severity:** P0/P1/P2
- **Impact:** [description]

## Timeline
- HH:MM - Incident detected
- HH:MM - Acknowledged
- HH:MM - Mitigation started
- HH:MM - Service restored
- HH:MM - Root cause identified
- HH:MM - Permanent fix deployed

## Root Cause
[Detailed explanation]

## Resolution
[What fixed the issue]

## Impact
- Users affected: X
- Requests failed: Y
- Revenue impact: $Z

## Action Items
- [ ] Fix A (Owner: @person, Due: DATE)
- [ ] Fix B (Owner: @person, Due: DATE)
- [ ] Postmortem meeting (Date: DATE)

## Lessons Learned
1. ...
2. ...
```

---

## 🔧 Specific Runbooks

### RB-002: Service Down

**Symptoms:**
- Health check `/health/ready` returning 503
- All requests failing with 502/503
- Pods in CrashLoopBackOff

**Diagnosis:**
```bash
# Check pod status
kubectl get pods -l app=api

# Check recent logs
kubectl logs -l app=api --tail=100

# Check events
kubectl get events --sort-by='.lastTimestamp'

# Check resource usage
kubectl top pods -l app=api
```

**Common Causes & Solutions:**

#### A. Database Connection Failed
```bash
# Check database connectivity
kubectl exec -it api-pod -- psql -h postgres -U user -c "SELECT 1"

# Restart database (if needed)
kubectl rollout restart statefulset/postgres

# Verify connection pool
# Check logs for: "Connection pool exhausted"
```

#### B. Out of Memory (OOMKilled)
```bash
# Check OOM events
kubectl get events | grep OOMKilled

# Increase memory limit
# Edit deployment.yaml
resources:
  limits:
    memory: 2Gi  # was 1Gi
  requests:
    memory: 1Gi  # was 512Mi

# Apply changes
kubectl apply -f deployment.yaml
```

#### C. Failed Startup (Config Error)
```bash
# Check startup logs
kubectl logs api-pod | grep "startup"

# Common issues:
# - Missing environment variable
# - Invalid config value
# - Failed database migration

# Fix config and restart
kubectl apply -f config.yaml
kubectl rollout restart deployment/api
```

**Recovery Time:** 5-15 minutes

---

### RB-003: High Error Rate

**Symptoms:**
- Error rate > 1% (normal < 0.1%)
- 500 errors in logs
- Alert: "HTTP 5xx errors spike"

**Diagnosis:**
```bash
# Check error rate
# Prometheus query: rate(http_requests_total{status=~"5.."}[5m])

# Get recent errors
kubectl logs -l app=api --since=10m | grep "ERROR"

# Check error distribution
kubectl logs -l app=api | grep ERROR | cut -d' ' -f5 | sort | uniq -c | sort -rn
```

**Common Causes & Solutions:**

#### A. Database Slow Queries
```bash
# Check slow query log
kubectl logs -l app=api | grep "Slow query"

# Connect to database
psql -h postgres -U user -d dbname

# Check active queries
SELECT pid, now() - query_start as duration, query
FROM pg_stat_activity
WHERE state = 'active'
ORDER BY duration DESC;

# Kill long-running query (if needed)
SELECT pg_terminate_backend(PID);
```

#### B. External Service Timeout
```bash
# Check circuit breaker state
# Prometheus query: circuit_breaker_state{service="payment_api"}

# Enable circuit breaker if not enabled
# Update config to fail-fast instead of waiting

# Check external service health
curl https://external-api.example.com/health
```

#### C. Memory Leak
```bash
# Check memory usage trend
# Grafana: Memory Usage dashboard

# Force garbage collection (Python)
kubectl exec -it api-pod -- python -c "import gc; gc.collect()"

# Restart pods with high memory
kubectl delete pod api-pod-xyz
```

**Recovery Time:** 10-30 minutes

---

### RB-004: Circuit Breaker Open

**Symptoms:**
- Alert: "Circuit breaker open for payment_service"
- Metrics show circuit_breaker_state = 2 (OPEN)
- Requests fail immediately with "Circuit is open"

**Diagnosis:**
```bash
# Check circuit breaker metrics
# Prometheus queries:
# - circuit_breaker_state{service="payment_api"}
# - circuit_breaker_failures_total{service="payment_api"}

# Check external service health
curl https://payment-api.example.com/health

# Check recent failures
kubectl logs -l app=api | grep "payment_api" | grep "ERROR"
```

**Resolution:**

#### A. External Service Recovered
```bash
# Verify external service is healthy
curl https://payment-api.example.com/health
# Expected: 200 OK

# Wait for circuit breaker to transition to HALF_OPEN
# Default: 60 seconds

# Circuit breaker will automatically test and close if successful
# Monitor: circuit_breaker_state metric should change to 0 (CLOSED)
```

#### B. External Service Still Down
```bash
# 1. Notify external service team
# 2. Enable fallback behavior

# Update config to use fallback
fallback:
  enabled: true
  strategy: cache  # Use cached data

# Apply config
kubectl apply -f config.yaml
kubectl rollout restart deployment/api

# Update status page
# Message: "Payment processing using cached rates"
```

#### C. Manual Circuit Breaker Reset (Emergency Only)
```bash
# ⚠️  Only reset if you're sure the issue is resolved

# Port-forward to admin API
kubectl port-forward svc/api-admin 9000:9000

# Reset circuit breaker
curl -X POST http://localhost:9000/admin/circuit-breaker/payment_api/reset

# Verify state
curl http://localhost:9000/admin/circuit-breaker/payment_api/state
# Expected: {"state": "CLOSED"}
```

**Recovery Time:** 1-60 minutes (depends on circuit breaker timeout)

---

### RB-005: Slow Queries

**Symptoms:**
- Alert: "Database query latency p99 > 500ms"
- Logs show "Slow query detected (XXXms > 100ms)"
- User reports slow response times

**Diagnosis:**
```bash
# Check query timing stats
# Connect to database
psql -h postgres -U user -d dbname

# Find slowest queries
SELECT
  query,
  mean_exec_time,
  calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

# Check table sizes
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

# Check missing indexes
SELECT
  schemaname,
  tablename,
  attname,
  n_distinct,
  correlation
FROM pg_stats
WHERE schemaname = 'public'
  AND n_distinct > 100
ORDER BY n_distinct DESC;
```

**Solutions:**

#### A. Add Missing Index
```sql
-- Example: Add index on frequently queried column
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
-- CONCURRENTLY allows table to remain accessible during index creation

-- Verify index created
\d users
```

#### B. Optimize Query
```sql
-- Before: N+1 query
SELECT * FROM users;
-- Then for each user:
SELECT * FROM orders WHERE user_id = ?;

-- After: Single query with JOIN
SELECT u.*, o.*
FROM users u
LEFT JOIN orders o ON o.user_id = u.id;

-- Or use eager loading in ORM
# Python/SQLAlchemy
stmt = select(User).options(joinedload(User.orders))
```

#### C. Add Query Cache
```python
# Add caching for expensive queries
@cache(ttl=300)  # Cache for 5 minutes
async def get_user_with_orders(user_id: str):
    # Expensive query here
    pass
```

#### D. Partition Large Table
```sql
-- For tables > 10GB
CREATE TABLE orders_partitioned (
  id BIGSERIAL,
  user_id INT,
  created_at TIMESTAMP,
  ...
) PARTITION BY RANGE (created_at);

-- Create monthly partitions
CREATE TABLE orders_2025_01 PARTITION OF orders_partitioned
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
```

**Recovery Time:** 5 minutes (add index) to 2 hours (query optimization)

---

### RB-006: Database Pool Exhausted

**Symptoms:**
- Error: "Connection pool exhausted"
- Error: "QueuePool limit exceeded"
- Requests hanging/timing out

**Diagnosis:**
```bash
# Check connection pool metrics
# Prometheus query: db_connection_pool_size
# Prometheus query: db_connection_pool_in_use

# Check active connections in database
psql -h postgres -U user -c "
SELECT
  count(*) as connections,
  state,
  wait_event_type,
  wait_event
FROM pg_stat_activity
WHERE datname = 'your_db'
GROUP BY state, wait_event_type, wait_event
ORDER BY connections DESC;"

# Check for connection leaks
psql -h postgres -U user -c "
SELECT
  pid,
  now() - backend_start as connection_age,
  state,
  query
FROM pg_stat_activity
WHERE datname = 'your_db'
  AND backend_start < now() - interval '10 minutes'
ORDER BY backend_start;"
```

**Solutions:**

#### A. Increase Pool Size (Quick Fix)
```python
# Edit database configuration
# config/database.py
engine = create_async_engine(
    DATABASE_URL,
    pool_size=30,  # was 20
    max_overflow=20,  # was 10
    pool_timeout=30,
)

# Restart application
kubectl rollout restart deployment/api
```

#### B. Fix Connection Leaks
```python
# Ensure connections are properly closed
# Always use context managers

# ❌ Bad - connection leak
session = SessionLocal()
users = session.query(User).all()
# session never closed!

# ✅ Good - automatic cleanup
async with get_session() as session:
    users = await session.execute(select(User))
    # session automatically closed
```

#### C. Kill Idle Connections
```sql
-- Find idle connections
SELECT
  pid,
  now() - state_change as idle_time,
  query
FROM pg_stat_activity
WHERE state = 'idle'
  AND now() - state_change > interval '5 minutes';

-- Kill idle connections (if safe)
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
  AND now() - state_change > interval '5 minutes';
```

#### D. Configure Statement Timeout
```sql
-- Set global statement timeout (prevents long-running queries)
ALTER DATABASE your_db SET statement_timeout = '30s';

-- Set for specific role
ALTER ROLE api_user SET statement_timeout = '30s';
```

**Recovery Time:** 2-10 minutes

---

## 📞 Escalation Contacts

| Role | Primary | Secondary | Slack | Phone |
|------|---------|-----------|-------|-------|
| Incident Commander | @john.doe | @jane.smith | #incidents | +1-555-0001 |
| Database DBA | @db.admin | @db.backup | #database | +1-555-0002 |
| Infrastructure | @devops.lead | @devops.backup | #devops | +1-555-0003 |
| Application Owner | @tech.lead | @dev.senior | #api-team | +1-555-0004 |

---

## 🔗 Useful Links

- **Monitoring:**
  - Grafana: https://grafana.example.com
  - Prometheus: https://prometheus.example.com
  - Kibana: https://kibana.example.com

- **Documentation:**
  - Architecture: `/docs/architecture.md`
  - API Docs: https://api.example.com/docs
  - ADRs: `/docs/adr/`

- **Tools:**
  - kubectl cheat sheet: https://kubernetes.io/docs/reference/kubectl/cheatsheet/
  - PostgreSQL docs: https://www.postgresql.org/docs/

---

## ✅ Post-Incident Checklist

- [ ] Incident resolved and verified
- [ ] Status page updated (incident closed)
- [ ] Incident report created
- [ ] Action items created and assigned
- [ ] Postmortem meeting scheduled (within 48h)
- [ ] Monitoring/alerting improved (if needed)
- [ ] Documentation updated
- [ ] Team debriefed

---

**Version History:**
- v1.0 (2025-01-02): Initial version based on code review recommendations

**Next Review:** 2025-04-01
