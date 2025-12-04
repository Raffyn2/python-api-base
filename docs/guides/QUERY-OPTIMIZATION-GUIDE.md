# Query Optimization Guide

**Version:** 1.0
**Last Updated:** 2025-01-02
**Owner:** Database Team
**Status:** Active

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Quick Reference](#quick-reference)
3. [Identification](#identification)
4. [Analysis](#analysis)
5. [Optimization Techniques](#optimization-techniques)
6. [PostgreSQL Specific](#postgresql-specific)
7. [SQLAlchemy Patterns](#sqlalchemy-patterns)
8. [Monitoring](#monitoring)
9. [Testing](#testing)
10. [Case Studies](#case-studies)

---

## Overview

### Purpose

This guide provides practical techniques for identifying, analyzing, and optimizing slow database queries in our Python API Base application.

### Target Audience

- Backend developers
- Database administrators
- DevOps engineers
- Performance engineers

### Prerequisites

- Understanding of SQL
- Familiarity with PostgreSQL
- Knowledge of SQLAlchemy ORM
- Access to production monitoring tools

---

## Quick Reference

### Performance Targets

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| **p50 latency** | < 50ms | > 100ms | > 250ms |
| **p95 latency** | < 100ms | > 250ms | > 500ms |
| **p99 latency** | < 250ms | > 500ms | > 1000ms |
| **Slow query %** | < 1% | > 5% | > 10% |
| **Query timeout** | 30s | 60s | 120s |

### Common Issues Quick Fix

| Symptom | Likely Cause | Quick Fix |
|---------|--------------|-----------|
| Query > 100ms | Missing index | Add index on WHERE/JOIN columns |
| High lock waits | Long transactions | Reduce transaction scope |
| Sequential scans | No index | Create appropriate index |
| N+1 queries | Lazy loading | Use eager loading (joinedload) |
| High CPU | Complex calculations | Move to application layer |
| High I/O | Large result sets | Add LIMIT, pagination |

---

## Identification

### 1. Real-Time Monitoring

**Grafana Dashboard:**
```
http://grafana.example.com/d/database-query-performance
```

**Key Panels:**
- Query Rate by Type
- Query Duration p99
- Slow Query Percentage
- Slowest Queries Table

### 2. Application Logs

**Slow Query Log:**
```python
# Automatically logged by QueryTimingMiddleware
# Location: logs/app.log
# Format:
[2025-01-02 10:15:30] WARNING: Slow query detected (250.45ms > 100ms)
{
  "duration_ms": 250.45,
  "statement": "SELECT * FROM users WHERE email = ...",
  "query_type": "SELECT",
  "is_slow": true
}
```

### 3. Database Statistics

**PostgreSQL pg_stat_statements:**
```sql
-- Top 10 slowest queries
SELECT
    query,
    calls,
    mean_exec_time,
    total_exec_time,
    rows
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

**Active Queries:**
```sql
-- Currently running queries
SELECT
    pid,
    now() - query_start AS duration,
    state,
    query
FROM pg_stat_activity
WHERE state != 'idle'
  AND query NOT LIKE '%pg_stat_activity%'
ORDER BY duration DESC;
```

### 4. Prometheus Metrics

**PromQL Queries:**
```promql
# Slow query rate
rate(db_slow_queries_total[5m])

# p99 latency by query type
histogram_quantile(0.99,
  sum(rate(db_query_duration_seconds_bucket[5m])) by (le, query_type)
) * 1000

# Slow query percentage
(sum(rate(db_slow_queries_total[5m])) / sum(rate(db_queries_total[5m]))) * 100
```

---

## Analysis

### 1. Query Execution Plan

**EXPLAIN ANALYZE:**
```sql
EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
SELECT u.id, u.name, u.email
FROM users u
WHERE u.created_at > '2025-01-01'
  AND u.status = 'active';
```

**Output Analysis:**
```
Seq Scan on users u  (cost=0.00..35050.00 rows=100 width=48) (actual time=0.045..145.234 rows=15000 loops=1)
  Filter: ((created_at > '2025-01-01'::date) AND (status = 'active'::text))
  Rows Removed by Filter: 985000
  Buffers: shared hit=15050
Planning Time: 0.125 ms
Execution Time: 145.456 ms
```

**Red Flags:**
- ❌ **Seq Scan** on large tables (> 10k rows)
- ❌ **High "Rows Removed by Filter"** (> 90%)
- ❌ **Nested Loop** with large datasets
- ❌ **Bitmap Heap Scan** on large result sets
- ❌ **Sort** operations without indexes

**Green Signals:**
- ✅ **Index Scan** or **Index Only Scan**
- ✅ **Low "Rows Removed by Filter"** (< 10%)
- ✅ **Hash Join** for large joins
- ✅ **Merge Join** for sorted data
- ✅ **Low buffer reads**

### 2. Index Usage

**Check if Index is Used:**
```sql
-- Index usage statistics
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
```

**Unused Indexes:**
```sql
-- Find indexes that are never used
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND indexrelname NOT LIKE 'pg_toast%'
ORDER BY pg_relation_size(indexrelid) DESC;
```

### 3. Lock Analysis

**Current Locks:**
```sql
SELECT
    locktype,
    relation::regclass,
    mode,
    transactionid AS tid,
    pid,
    granted
FROM pg_locks
WHERE NOT granted
ORDER BY relation;
```

**Blocking Queries:**
```sql
SELECT
    blocked_locks.pid AS blocked_pid,
    blocked_activity.usename AS blocked_user,
    blocking_locks.pid AS blocking_pid,
    blocking_activity.usename AS blocking_user,
    blocked_activity.query AS blocked_statement,
    blocking_activity.query AS blocking_statement
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks
    ON blocking_locks.locktype = blocked_locks.locktype
    AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
    AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
    AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
    AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
    AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
    AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
    AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
    AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
    AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
    AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;
```

---

## Optimization Techniques

### 1. Indexing Strategies

#### A. Single Column Index

**When to Use:**
- WHERE clause filters on single column
- ORDER BY on single column
- Foreign key columns

**Example:**
```sql
-- Create index
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);

-- Query benefits
SELECT * FROM users WHERE email = 'user@example.com';
```

**SQLAlchemy Model:**
```python
from sqlalchemy import Index

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False)

    # Add index
    __table_args__ = (
        Index('idx_users_email', 'email'),
    )
```

#### B. Composite Index

**When to Use:**
- WHERE clause filters on multiple columns
- Query always uses same column combination

**Example:**
```sql
-- Create composite index
CREATE INDEX CONCURRENTLY idx_orders_user_status
ON orders(user_id, status);

-- Query benefits
SELECT * FROM orders
WHERE user_id = 123 AND status = 'pending';
```

**Column Order Matters:**
```sql
-- ✅ Uses index (user_id is first column)
WHERE user_id = 123 AND status = 'pending'

-- ✅ Uses index (user_id is first column)
WHERE user_id = 123

-- ❌ May not use index (status is second column)
WHERE status = 'pending'
```

**Rule:** Most selective column first, or column used most frequently first.

#### C. Partial Index

**When to Use:**
- Query always filters on specific value
- Index only subset of rows

**Example:**
```sql
-- Index only active users
CREATE INDEX CONCURRENTLY idx_users_active_email
ON users(email)
WHERE status = 'active';

-- Query benefits
SELECT * FROM users
WHERE email = 'user@example.com'
  AND status = 'active';
```

**Savings:**
- Smaller index size
- Faster index scans
- Less maintenance overhead

#### D. Covering Index (Index-Only Scan)

**When to Use:**
- Query selects specific columns frequently
- Want to avoid table access

**Example:**
```sql
-- Include frequently selected columns
CREATE INDEX CONCURRENTLY idx_users_email_covering
ON users(email)
INCLUDE (name, created_at);

-- Query benefits (Index-Only Scan)
SELECT email, name, created_at
FROM users
WHERE email = 'user@example.com';
```

#### E. Expression Index

**When to Use:**
- Query uses function or expression in WHERE clause

**Example:**
```sql
-- Index for case-insensitive search
CREATE INDEX CONCURRENTLY idx_users_lower_email
ON users(LOWER(email));

-- Query benefits
SELECT * FROM users
WHERE LOWER(email) = LOWER('User@Example.com');
```

**SQLAlchemy:**
```python
from sqlalchemy import func, Index

class User(Base):
    # ...
    __table_args__ = (
        Index('idx_users_lower_email', func.lower(email)),
    )
```

### 2. Query Optimization

#### A. Avoid SELECT *

**❌ Bad:**
```python
# Fetches all columns (slow, high memory)
users = session.query(User).filter(User.status == 'active').all()
```

**✅ Good:**
```python
# Fetch only needed columns
users = session.query(User.id, User.name, User.email)\
    .filter(User.status == 'active')\
    .all()
```

#### B. Use Pagination

**❌ Bad:**
```python
# Loads all rows into memory
orders = session.query(Order).filter(Order.user_id == user_id).all()
```

**✅ Good:**
```python
# Paginate results
page = 1
page_size = 50
orders = session.query(Order)\
    .filter(Order.user_id == user_id)\
    .limit(page_size)\
    .offset((page - 1) * page_size)\
    .all()
```

**Even Better - Keyset Pagination:**
```python
# More efficient for large offsets
last_id = request.args.get('last_id', 0)
orders = session.query(Order)\
    .filter(Order.user_id == user_id)\
    .filter(Order.id > last_id)\
    .order_by(Order.id)\
    .limit(page_size)\
    .all()
```

#### C. Fix N+1 Queries

**❌ Bad (N+1 Query Problem):**
```python
# 1 query to fetch users
users = session.query(User).all()

# N queries to fetch orders for each user
for user in users:
    orders = user.orders  # Lazy load - 1 query per user!
```

**✅ Good (Eager Loading):**
```python
from sqlalchemy.orm import joinedload

# 1 query with JOIN
users = session.query(User)\
    .options(joinedload(User.orders))\
    .all()

# No additional queries
for user in users:
    orders = user.orders  # Already loaded!
```

**Options:**
- `joinedload()` - LEFT OUTER JOIN (1 query)
- `selectinload()` - Separate SELECT IN query (2 queries, but more efficient for large datasets)
- `subqueryload()` - Subquery (2 queries)

#### D. Use EXISTS Instead of COUNT

**❌ Bad:**
```python
# Counts all matching rows
has_orders = session.query(func.count(Order.id))\
    .filter(Order.user_id == user_id)\
    .scalar() > 0
```

**✅ Good:**
```python
# Stops at first match
has_orders = session.query(Order)\
    .filter(Order.user_id == user_id)\
    .exists()

has_orders = session.query(has_orders).scalar()
```

**SQL Generated:**
```sql
-- EXISTS (fast)
SELECT EXISTS(
    SELECT 1 FROM orders WHERE user_id = 123
) AS anon_1;

-- vs COUNT (slow)
SELECT COUNT(orders.id) AS count_1
FROM orders
WHERE orders.user_id = 123;
```

#### E. Batch Operations

**❌ Bad:**
```python
# N individual INSERT queries
for item_data in items_to_create:
    item = Item(**item_data)
    session.add(item)
    session.commit()  # Commit each individually!
```

**✅ Good:**
```python
# Bulk insert - 1 query
session.bulk_insert_mappings(Item, items_to_create)
session.commit()

# Or batch with add_all
items = [Item(**data) for data in items_to_create]
session.add_all(items)
session.commit()
```

### 3. JOIN Optimization

#### A. JOIN Type Selection

**INNER JOIN vs LEFT JOIN:**
```python
# Use INNER JOIN when you need matches from both tables
query = session.query(User)\
    .join(Order)\  # INNER JOIN
    .filter(Order.status == 'completed')

# Use LEFT JOIN when you need all left table rows
query = session.query(User)\
    .outerjoin(Order)\  # LEFT JOIN
    .filter(or_(Order.status == 'completed', Order.id == None))
```

#### B. JOIN Order

**❌ Bad:**
```sql
-- Large table first
SELECT *
FROM orders o  -- 10M rows
JOIN users u ON u.id = o.user_id  -- 100K rows
WHERE u.status = 'active';
```

**✅ Good:**
```sql
-- Filter first, then join
SELECT *
FROM users u  -- 100K rows
JOIN orders o ON o.user_id = u.id
WHERE u.status = 'active';  -- Reduces to 10K rows before join
```

#### C. Avoid JOIN in Subqueries

**❌ Bad:**
```python
# Subquery with JOIN
subquery = session.query(Order.user_id)\
    .join(Item)\
    .filter(Item.price > 100)\
    .subquery()

users = session.query(User)\
    .filter(User.id.in_(select([subquery.c.user_id])))\
    .all()
```

**✅ Good:**
```python
# Direct JOIN
users = session.query(User)\
    .join(Order)\
    .join(Item)\
    .filter(Item.price > 100)\
    .all()
```

### 4. Filtering Optimization

#### A. Use IN for Multiple Values

**❌ Bad:**
```python
# Multiple OR conditions
users = session.query(User)\
    .filter(or_(
        User.id == 1,
        User.id == 2,
        User.id == 3,
        # ... 100 more
    ))\
    .all()
```

**✅ Good:**
```python
# Use IN clause
user_ids = [1, 2, 3, ...]
users = session.query(User)\
    .filter(User.id.in_(user_ids))\
    .all()
```

#### B. Avoid Functions on Indexed Columns

**❌ Bad:**
```python
# Function prevents index usage
users = session.query(User)\
    .filter(func.year(User.created_at) == 2025)\
    .all()
```

**✅ Good:**
```python
# Range query uses index
from datetime import datetime

start_date = datetime(2025, 1, 1)
end_date = datetime(2025, 12, 31, 23, 59, 59)

users = session.query(User)\
    .filter(User.created_at.between(start_date, end_date))\
    .all()
```

#### C. Use LIMIT Early

**❌ Bad:**
```python
# Fetch all, then slice in Python
all_orders = session.query(Order).all()
recent_orders = all_orders[:10]  # Takes top 10 in Python
```

**✅ Good:**
```python
# LIMIT in database
recent_orders = session.query(Order)\
    .order_by(Order.created_at.desc())\
    .limit(10)\
    .all()
```

---

## PostgreSQL Specific

### 1. VACUUM and ANALYZE

**Purpose:**
- VACUUM: Reclaim storage, prevent bloat
- ANALYZE: Update statistics for query planner

**Schedule:**
```sql
-- Manual VACUUM
VACUUM ANALYZE users;

-- Full VACUUM (locks table)
VACUUM FULL users;

-- Check last vacuum
SELECT
    schemaname,
    relname,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
ORDER BY last_autovacuum DESC NULLS LAST;
```

### 2. Connection Pooling

**SQLAlchemy Configuration:**
```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,  # Number of connections to maintain
    max_overflow=10,  # Additional connections when pool is full
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,  # Recycle connections after 1 hour
)
```

### 3. Prepared Statements

**Automatic in SQLAlchemy:**
```python
# SQLAlchemy automatically uses prepared statements
stmt = select(User).where(User.id == bindparam('user_id'))

# Executed multiple times with different parameters
result1 = session.execute(stmt, {'user_id': 1})
result2 = session.execute(stmt, {'user_id': 2})
# PostgreSQL reuses execution plan
```

### 4. Partitioning

**Range Partitioning (Time-based):**
```sql
-- Parent table
CREATE TABLE orders (
    id SERIAL,
    user_id INTEGER,
    created_at TIMESTAMP,
    total DECIMAL
) PARTITION BY RANGE (created_at);

-- Partitions
CREATE TABLE orders_2024_q1 PARTITION OF orders
    FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');

CREATE TABLE orders_2024_q2 PARTITION OF orders
    FOR VALUES FROM ('2024-04-01') TO ('2024-07-01');

-- Queries automatically use correct partition
SELECT * FROM orders
WHERE created_at >= '2024-02-01'
  AND created_at < '2024-03-01';
-- Only scans orders_2024_q1 partition
```

---

## SQLAlchemy Patterns

### 1. Query Object Pattern

```python
from typing import Optional
from sqlalchemy.orm import Session, Query

class UserQuery:
    """Reusable user queries."""

    def __init__(self, session: Session):
        self.session = session

    def base_query(self) -> Query:
        """Base query with common joins and filters."""
        return self.session.query(User)\
            .options(selectinload(User.profile))\
            .filter(User.deleted_at == None)

    def active_users(self) -> Query:
        """Get active users."""
        return self.base_query()\
            .filter(User.status == 'active')

    def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email."""
        return self.base_query()\
            .filter(User.email == email)\
            .first()

    def paginate(self, page: int = 1, per_page: int = 50) -> list[User]:
        """Paginate results."""
        return self.base_query()\
            .limit(per_page)\
            .offset((page - 1) * per_page)\
            .all()

# Usage
query = UserQuery(session)
users = query.active_users().all()
user = query.find_by_email('test@example.com')
```

### 2. Lazy vs Eager Loading

```python
from sqlalchemy.orm import lazyload, joinedload, selectinload

# Lazy (default) - separate query for each relationship
users = session.query(User).all()

# Eager - joinedload (LEFT OUTER JOIN)
users = session.query(User)\
    .options(joinedload(User.profile))\
    .all()

# Eager - selectinload (SELECT IN query)
users = session.query(User)\
    .options(selectinload(User.orders))\
    .all()

# Mixed loading
users = session.query(User)\
    .options(
        joinedload(User.profile),  # 1:1 relationship
        selectinload(User.orders).joinedload(Order.items)  # 1:N relationship
    )\
    .all()
```

### 3. Query Optimization Decorator

```python
from functools import wraps
from time import perf_counter

def measure_query(func):
    """Decorator to measure query execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = perf_counter()
        result = func(*args, **kwargs)
        duration_ms = (perf_counter() - start) * 1000

        logger.info(
            f"Query {func.__name__} executed in {duration_ms:.2f}ms",
            extra={
                "function": func.__name__,
                "duration_ms": duration_ms,
            }
        )

        return result
    return wrapper

# Usage
@measure_query
def get_active_users(session: Session) -> list[User]:
    return session.query(User)\
        .filter(User.status == 'active')\
        .all()
```

---

## Monitoring

### 1. Query Performance Dashboard

**Access:** `http://grafana.example.com/d/database-query-performance`

**Key Metrics:**
- Query rate (QPS)
- Query latency percentiles (p50, p95, p99)
- Slow query rate and percentage
- Query distribution by type

### 2. Alerting

**Prometheus Alerts:**
- `SlowQueryRateCritical` - > 10% slow queries for 5min
- `QueryLatencyP99Critical` - p99 > 1000ms for 5min
- `QueryRateSpike` - 2x increase for 10min

**AlertManager:**
- Critical alerts → PagerDuty
- Warning alerts → Slack #database-alerts

### 3. Logging

**Slow Query Logs:**
```python
# Automatically logged by QueryTimingMiddleware
# Configuration in src/infrastructure/db/middleware/query_timing.py

middleware = QueryTimingMiddleware(
    engine=engine,
    slow_query_threshold_ms=100.0,  # Log queries > 100ms
    log_all_queries=False,  # Only log slow queries
    collect_stats=True,  # Collect statistics
)
```

---

## Testing

### 1. Load Testing

**Use Locust:**
```python
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def get_users(self):
        self.client.get("/api/v1/users")

    @task(3)  # 3x weight
    def get_user_orders(self):
        user_id = random.randint(1, 1000)
        self.client.get(f"/api/v1/users/{user_id}/orders")

# Run: locust -f load_test.py --users 100 --spawn-rate 10
```

### 2. Query Benchmarking

```python
import time
from sqlalchemy import text

def benchmark_query(session, sql: str, iterations: int = 100):
    """Benchmark query execution time."""
    times = []

    for _ in range(iterations):
        start = time.perf_counter()
        session.execute(text(sql))
        times.append(time.perf_counter() - start)

    avg_time = sum(times) / len(times) * 1000
    p95_time = sorted(times)[int(len(times) * 0.95)] * 1000
    p99_time = sorted(times)[int(len(times) * 0.99)] * 1000

    print(f"Average: {avg_time:.2f}ms")
    print(f"p95: {p95_time:.2f}ms")
    print(f"p99: {p99_time:.2f}ms")

# Usage
benchmark_query(session, "SELECT * FROM users WHERE status = 'active'")
```

### 3. A/B Testing Queries

```python
def compare_queries(session, query_a: str, query_b: str):
    """Compare performance of two queries."""
    print("Query A:")
    benchmark_query(session, query_a)

    print("\nQuery B:")
    benchmark_query(session, query_b)

# Usage
compare_queries(
    session,
    "SELECT * FROM users WHERE status = 'active'",  # No index
    "SELECT * FROM users WHERE status = 'active' AND id > 0"  # With index hint
)
```

---

## Case Studies

### Case Study 1: N+1 Query Problem

**Problem:**
```python
# API endpoint taking 5+ seconds
users = session.query(User).limit(100).all()
for user in users:
    orders = user.orders  # N+1 query!
    print(f"{user.name}: {len(orders)} orders")
```

**Analysis:**
- 1 query to fetch 100 users
- 100 queries to fetch orders for each user
- Total: 101 queries

**Solution:**
```python
from sqlalchemy.orm import selectinload

users = session.query(User)\
    .options(selectinload(User.orders))\
    .limit(100)\
    .all()

for user in users:
    orders = user.orders  # Already loaded!
    print(f"{user.name}: {len(orders)} orders")
```

**Result:**
- 2 queries total (users + orders)
- Response time: **5s → 50ms (100x improvement)**

---

### Case Study 2: Missing Index

**Problem:**
```sql
-- Query taking 2+ seconds
SELECT * FROM orders
WHERE user_id = 123
  AND status = 'pending';

-- EXPLAIN shows Seq Scan
Seq Scan on orders (cost=0.00..35050.00 rows=100 width=128)
  Filter: (user_id = 123 AND status = 'pending')
  Rows Removed by Filter: 999900
```

**Analysis:**
- Sequential scan on 1M rows
- Filters 99.99% of rows
- No index on (user_id, status)

**Solution:**
```sql
-- Add composite index
CREATE INDEX CONCURRENTLY idx_orders_user_status
ON orders(user_id, status);

-- After index creation
Index Scan using idx_orders_user_status on orders (cost=0.42..8.44 rows=100 width=128)
  Index Cond: (user_id = 123 AND status = 'pending')
```

**Result:**
- Response time: **2000ms → 5ms (400x improvement)**
- Index size: 50MB

---

### Case Study 3: Inefficient Pagination

**Problem:**
```python
# Page 1000 taking 10+ seconds
page = 1000
page_size = 50
orders = session.query(Order)\
    .order_by(Order.created_at.desc())\
    .limit(page_size)\
    .offset((page - 1) * page_size)\  # OFFSET 49950
    .all()
```

**Analysis:**
- OFFSET must scan and skip 49,950 rows
- Inefficient for large offsets

**Solution:**
```python
# Keyset pagination (seek method)
last_created_at = request.args.get('last_created_at')
last_id = request.args.get('last_id')

query = session.query(Order)\
    .order_by(Order.created_at.desc(), Order.id.desc())

if last_created_at and last_id:
    query = query.filter(
        or_(
            Order.created_at < last_created_at,
            and_(
                Order.created_at == last_created_at,
                Order.id < last_id
            )
        )
    )

orders = query.limit(page_size).all()
```

**Result:**
- Response time: **10s → 20ms (500x improvement)**
- Consistent performance regardless of page number

---

### Case Study 4: Unnecessary Data Fetching

**Problem:**
```python
# Fetching entire order objects just to count
orders = session.query(Order)\
    .filter(Order.user_id == user_id)\
    .all()
order_count = len(orders)  # Count in Python
```

**Analysis:**
- Fetches all order data from database
- Transfers large amount of data over network
- Counts in application layer

**Solution:**
```python
# Count in database
order_count = session.query(func.count(Order.id))\
    .filter(Order.user_id == user_id)\
    .scalar()
```

**Better Solution (if just checking existence):**
```python
# Use EXISTS
has_orders = session.query(
    exists().where(Order.user_id == user_id)
).scalar()
```

**Result:**
- Response time: **500ms → 5ms (100x improvement)**
- Network transfer: **10MB → 10 bytes**

---

## Summary Checklist

### Before Deploying New Query

- [ ] Run EXPLAIN ANALYZE
- [ ] Check if indexes are used
- [ ] Verify no sequential scans on large tables
- [ ] Test with production-like data volume
- [ ] Add monitoring for slow queries
- [ ] Document expected performance

### When Query is Slow

1. [ ] Identify slow query (logs, monitoring)
2. [ ] Run EXPLAIN ANALYZE
3. [ ] Check for missing indexes
4. [ ] Look for N+1 queries
5. [ ] Verify data volume
6. [ ] Test optimization
7. [ ] Deploy with monitoring

### Regular Maintenance

- [ ] Review pg_stat_statements weekly
- [ ] Check for unused indexes monthly
- [ ] VACUUM ANALYZE critical tables weekly
- [ ] Review slow query logs daily
- [ ] Update query optimization guide quarterly

---

**Version:** 1.0
**Last Updated:** 2025-01-02
**Next Review:** 2025-04-01
