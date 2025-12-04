# Database Query Performance Monitoring

**Feature:** performance-monitoring-2025
**Status:** Production Ready
**Created:** 2025-01-02
**Owner:** DevOps Team

---

## 📋 Overview

Complete monitoring solution for database query performance including:
- **Query Timing Middleware** - SQLAlchemy instrumentation
- **Prometheus Metrics** - Exportação de métricas
- **Grafana Dashboard** - Visualização em tempo real
- **Alerting Rules** - Alertas automáticos
- **AlertManager** - Roteamento e notificações

---

## 🏗️ Architecture

```
┌─────────────┐
│ Application │
│   (FastAPI) │
└──────┬──────┘
       │
       │ SQLAlchemy
       ▼
┌─────────────────────────────┐
│ QueryTimingPrometheusMiddleware │
│  - Query timing              │
│  - Slow query detection      │
│  - Metrics export            │
└──────┬──────────────────────┘
       │
       │ Prometheus metrics
       ▼
┌─────────────┐     ┌─────────────┐
│ Prometheus  │────▶│ AlertManager│
│  - Scraping │     │  - Routing  │
│  - Storage  │     │  - Notif.   │
│  - Alerts   │     └──────┬──────┘
└──────┬──────┘            │
       │                   │
       │                   ▼
       │            ┌─────────────┐
       │            │ PagerDuty/  │
       │            │ Slack/Email │
       │            └─────────────┘
       ▼
┌─────────────┐
│   Grafana   │
│  - Dashboard│
│  - Viz.     │
└─────────────┘
```

---

## 📦 Components

### 1. Query Timing Middleware

**File:** `src/infrastructure/db/middleware/query_timing_prometheus.py`

**Purpose:** Instrument SQLAlchemy engine to collect query metrics

**Metrics Exported:**
- `db_queries_total{query_type}` - Total queries by type (Counter)
- `db_slow_queries_total{query_type}` - Slow queries by type (Counter)
- `db_query_duration_seconds{query_type}` - Query duration (Histogram)

**Usage:**
```python
from sqlalchemy import create_async_engine
from infrastructure.db.middleware import install_query_timing_with_prometheus
from infrastructure.prometheus import get_registry

# Create engine
engine = create_async_engine(DATABASE_URL)

# Install middleware
middleware = install_query_timing_with_prometheus(
    engine,
    slow_query_threshold_ms=100.0,
    prometheus_registry=get_registry(),
)

# Metrics now exported at /metrics endpoint
```

**Configuration:**
```python
# Adjust slow query threshold
slow_query_threshold_ms = 100.0  # 100ms

# Enable/disable logging
log_all_queries = False  # Only log slow queries

# Enable/disable statistics
collect_stats = True
```

---

### 2. Grafana Dashboard

**File:** `grafana-dashboard-database-queries.json`

**Panels:**
1. **Query Rate by Type** - Queries/second timeline
2. **Query Duration p99** - 99th percentile latency gauge
3. **Query Duration Percentiles** - p50, p95, p99 comparison
4. **Slow Query Rate by Type** - Slow queries/second
5. **Slow Query Percentage** - % of slow queries gauge
6. **Query Distribution** - Pie chart by query type
7. **Query Statistics Table** - QPS and p99 by type

**Import to Grafana:**
```bash
# Via UI
1. Go to Grafana UI
2. Dashboards → Import
3. Upload grafana-dashboard-database-queries.json

# Via API
curl -X POST http://grafana:3000/api/dashboards/db \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -H "Content-Type: application/json" \
  -d @grafana-dashboard-database-queries.json

# Via ConfigMap (Kubernetes)
kubectl create configmap grafana-dashboard-database \
  --from-file=grafana-dashboard-database-queries.json \
  -n monitoring
```

**Access:**
- URL: `https://grafana.example.com/d/database-query-performance`
- Refresh: 5 seconds
- Time Range: Last 15 minutes (default)

---

### 3. Prometheus Alert Rules

**File:** `prometheus-alerts-database.yml`

**Alert Severities:**
- **Critical (P0):** Page on-call engineer, immediate response
- **Warning (P1):** Notify team, investigate within SLA
- **Info:** Low priority, for awareness

**Alerts:**

| Alert Name | Severity | Threshold | For | Description |
|------------|----------|-----------|-----|-------------|
| SlowQueryRateCritical | Critical | >10% | 5m | Very high slow query rate |
| SlowQueryRateWarning | Warning | >5% | 10m | High slow query rate |
| QueryLatencyP99Critical | Critical | >1000ms | 5m | Extremely high p99 latency |
| QueryLatencyP99Warning | Warning | >500ms | 15m | High p99 latency |
| QueryRateSpike | Warning | >2x baseline | 10m | Sudden query rate increase |
| QueryRateDrop | Warning | <50% baseline | 10m | Sudden query rate decrease |
| HighSlowQueryVolume | Warning | >1 qps | 15m | High volume of slow queries |
| DatabaseMetricsNotReporting | Warning | absent | 5m | Metrics not being collected |

**Installation:**
```yaml
# prometheus.yml
rule_files:
  - 'prometheus-alerts-database.yml'

alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - 'alertmanager:9093'
```

**Testing:**
```bash
# Validate syntax
promtool check rules prometheus-alerts-database.yml

# Run unit tests
promtool test rules prometheus-alerts-database-tests.yml

# Expected output:
# Unit Testing:  prometheus-alerts-database-tests.yml
#   SUCCESS
```

---

### 4. AlertManager Configuration

**File:** `alertmanager-config.yml`

**Receivers:**
- **PagerDuty** - Critical alerts (P0)
- **Slack #database-alerts** - Warning alerts (P1)
- **Slack #database-info** - Info alerts
- **Email** - All alerts to team

**Routing Logic:**
```
Critical → PagerDuty + Slack + Email
Warning → Slack + Email
Info → Slack (#database-info)
```

**Inhibition Rules:**
- Critical suppresses Warning (same alert)
- Service Down suppresses query alerts
- Query Rate Drop suppresses Slow Query alerts

**Installation:**
```bash
# Start AlertManager
alertmanager --config.file=alertmanager-config.yml

# Set environment variables
export SMTP_PASSWORD="your-smtp-password"
export PAGERDUTY_SERVICE_KEY="your-pagerduty-key"
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."

# Validate configuration
amtool check-config alertmanager-config.yml

# Test routing
amtool config routes test \
  --config.file=alertmanager-config.yml \
  --tree alertname=SlowQueryRateCritical severity=critical
```

---

## 🚀 Quick Start

### 1. Install Middleware (Application)

```python
# src/main.py
from infrastructure.db.middleware import install_query_timing_with_prometheus
from infrastructure.prometheus import get_registry

# After creating engine
middleware = install_query_timing_with_prometheus(
    engine,
    slow_query_threshold_ms=100.0,
    prometheus_registry=get_registry(),
)
```

### 2. Configure Prometheus

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'

rule_files:
  - 'prometheus-alerts-database.yml'

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']
```

### 3. Start Monitoring Stack

```bash
# Docker Compose
docker-compose -f deployments/monitoring/docker-compose.yml up -d

# Kubernetes
kubectl apply -f deployments/monitoring/k8s/
```

### 4. Import Grafana Dashboard

1. Access Grafana: `http://grafana:3000`
2. Login (admin/admin)
3. Dashboards → Import
4. Upload `grafana-dashboard-database-queries.json`
5. Select Prometheus datasource

### 5. Verify Metrics

```bash
# Check metrics endpoint
curl http://localhost:8000/metrics | grep db_queries

# Expected output:
# db_queries_total{query_type="SELECT"} 1234
# db_slow_queries_total{query_type="SELECT"} 56
# db_query_duration_seconds_bucket{query_type="SELECT",le="0.1"} 1000
```

---

## 📊 Metrics Reference

### db_queries_total

**Type:** Counter
**Labels:** `query_type` (SELECT, INSERT, UPDATE, DELETE)
**Description:** Total number of database queries executed
**Example:**
```promql
# Query rate by type
rate(db_queries_total[5m])

# Total queries in last hour
sum(increase(db_queries_total[1h]))
```

### db_slow_queries_total

**Type:** Counter
**Labels:** `query_type`
**Description:** Total number of slow queries (> threshold)
**Example:**
```promql
# Slow query rate
rate(db_slow_queries_total[5m])

# Slow query percentage
(sum(rate(db_slow_queries_total[5m])) / sum(rate(db_queries_total[5m]))) * 100
```

### db_query_duration_seconds

**Type:** Histogram
**Labels:** `query_type`
**Buckets:** 1ms, 5ms, 10ms, 25ms, 50ms, 100ms, 250ms, 500ms, 1s, 2.5s, 5s, 10s
**Description:** Database query duration distribution
**Example:**
```promql
# p99 latency
histogram_quantile(0.99, sum(rate(db_query_duration_seconds_bucket[5m])) by (le))

# Average latency
rate(db_query_duration_seconds_sum[5m]) / rate(db_query_duration_seconds_count[5m])
```

---

## 🎯 Alert Response Procedures

### SlowQueryRateCritical

**Severity:** P0 (Critical)
**Response Time:** 5 minutes
**Runbook:** [RB-005](../../docs/runbooks/RUNBOOK-001-incident-response.md#rb-005-slow-queries)

**Steps:**
1. Check Grafana dashboard for affected query types
2. Connect to database and identify slow queries:
   ```sql
   SELECT query, mean_exec_time, calls
   FROM pg_stat_statements
   ORDER BY mean_exec_time DESC
   LIMIT 10;
   ```
3. Kill long-running queries if necessary
4. Check for missing indexes
5. Scale database if needed

### QueryLatencyP99Critical

**Severity:** P0 (Critical)
**Response Time:** 5 minutes
**Runbook:** [RB-005](../../docs/runbooks/RUNBOOK-001-incident-response.md#rb-005-slow-queries)

**Steps:**
1. Check query distribution in Grafana
2. Identify bottleneck query type
3. Review query execution plans
4. Add missing indexes (CONCURRENTLY)
5. Consider query caching

---

## 🧪 Testing

### Unit Tests

```bash
# Run middleware tests
pytest tests/unit/infrastructure/db/middleware/ -v

# Run integration tests
pytest tests/integration/infrastructure/db/ -v
```

### Load Testing

```bash
# Generate test load
python scripts/load_test_db.py --queries=1000 --slow-ratio=0.1

# Expected metrics:
# - db_queries_total should increase
# - db_slow_queries_total ~10% of total
# - Alerts should fire if thresholds exceeded
```

### Alert Testing

```bash
# Test alert rule syntax
promtool check rules prometheus-alerts-database.yml

# Run alert unit tests
promtool test rules prometheus-alerts-database-tests.yml

# Send test alert
amtool alert add alertname=TestSlowQuery severity=warning \
  --alertmanager.url=http://localhost:9093
```

---

## 📈 Performance Impact

### Middleware Overhead

**Benchmarks:**
- Query timing: ~0.01ms per query
- Prometheus metric update: ~0.005ms per query
- **Total overhead: <0.02ms** (negligible for queries >100ms)

**Memory:**
- Middleware: ~50KB
- Metrics storage: ~10KB per query type

### Prometheus Storage

**Estimated Storage:**
- 3 metrics × 4 query types = 12 time series
- @15s scrape interval = 240 samples/hour/series
- ~3KB/hour total

**Retention:**
- Recommended: 15 days
- Estimated size: ~1MB

---

## 🔧 Troubleshooting

### Problem: Metrics Not Appearing

**Check:**
```bash
# 1. Verify middleware installed
curl http://localhost:8000/metrics | grep db_

# 2. Check Prometheus targets
curl http://prometheus:9090/api/v1/targets

# 3. Check logs
kubectl logs -l app=api | grep "QueryTimingPrometheusMiddleware"
```

### Problem: Alerts Not Firing

**Check:**
```bash
# 1. Verify rules loaded
curl http://prometheus:9090/api/v1/rules

# 2. Check alert state
curl http://prometheus:9090/api/v1/alerts

# 3. Verify thresholds
# Review prometheus-alerts-database.yml expressions
```

### Problem: Grafana Dashboard Empty

**Check:**
```bash
# 1. Verify datasource configured
# Grafana → Configuration → Data Sources → Prometheus

# 2. Test query in Explore
# Grafana → Explore → Query: db_queries_total

# 3. Check time range
# Ensure time range includes recent data
```

---

## 📚 References

### Documentation
- [Query Timing Middleware](../../src/infrastructure/db/middleware/query_timing_prometheus.py)
- [Incident Response Runbook](../../docs/runbooks/RUNBOOK-001-incident-response.md)
- [Improvements Summary](../../docs/IMPROVEMENTS-COMPLETED-2025-01-02.md)

### External
- [Prometheus Alerting](https://prometheus.io/docs/alerting/latest/overview/)
- [Grafana Dashboards](https://grafana.com/docs/grafana/latest/dashboards/)
- [SQLAlchemy Events](https://docs.sqlalchemy.org/en/20/core/events.html)

---

## 🔄 Maintenance

### Weekly
- Review slow query alerts
- Check dashboard for anomalies
- Verify alert routing

### Monthly
- Review and update thresholds
- Analyze query distribution trends
- Optimize slow queries

### Quarterly
- Review and update runbooks
- Load test alert thresholds
- Update Grafana dashboard

---

## ✅ Checklist

### Pre-Production
- [ ] Middleware installed in application
- [ ] Metrics endpoint verified (/metrics)
- [ ] Prometheus scraping configured
- [ ] Alert rules loaded and tested
- [ ] AlertManager configured with receivers
- [ ] Grafana dashboard imported
- [ ] Team trained on runbooks
- [ ] On-call rotation configured

### Post-Deployment
- [ ] Verify metrics collecting (24h)
- [ ] Test alert firing with synthetic load
- [ ] Confirm notifications received
- [ ] Review baseline metrics
- [ ] Adjust thresholds if needed
- [ ] Document baseline values
- [ ] Create postmortem template

---

**Version:** 1.0
**Last Updated:** 2025-01-02
**Next Review:** 2025-04-01
