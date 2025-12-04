# RUNBOOK-004: Circuit Breaker Open

**Alert:** CircuitBreakerOpen
**Severity:** P0 (Critical)
**Component:** Resilience
**Response Time:** 5 minutes

---

## 📋 Overview

Circuit breaker has transitioned to OPEN state, indicating repeated failures to a downstream service. Requests to the affected service are being rejected immediately without attempting to contact the service.

---

## 🚨 Symptoms

- Alert `CircuitBreakerOpen` firing
- Requests to specific endpoints failing with 503 Service Unavailable
- Grafana dashboard showing circuit breaker in OPEN state
- Application logs showing circuit breaker errors

**Example Log:**
```
[ERROR] Circuit breaker 'external-api' is OPEN - rejecting request
```

---

## 🔍 Diagnosis

### 1. Identify Affected Service

```bash
# Check circuit breaker states
curl http://prometheus:9090/api/v1/query \
  -d 'query=circuit_breaker_state{state="open"}'

# Expected output shows which service(s):
# circuit_breaker_state{service="payment-api",state="open"} 1
```

### 2. Check Service Health

```bash
# Direct health check to affected service
curl -v https://payment-api.example.com/health

# Check from application pod
kubectl exec -it api-pod -- curl http://payment-api:8080/health
```

### 3. Review Recent Changes

```bash
# Check recent deployments
kubectl rollout history deployment/payment-api

# Check recent commits
git log --oneline --since="1 hour ago" -- services/payment-api/
```

### 4. Analyze Error Patterns

```bash
# Check application logs for errors
kubectl logs -l app=api --tail=100 | grep -i circuit

# Check service logs
kubectl logs -l app=payment-api --tail=100 | grep ERROR
```

### 5. Check Dependencies

```bash
# Database connectivity
kubectl exec -it payment-api-pod -- nc -zv postgres 5432

# Redis connectivity
kubectl exec -it payment-api-pod -- nc -zv redis 6379

# External APIs
kubectl exec -it payment-api-pod -- curl -v https://external-api.com/health
```

---

## 🔧 Mitigation

### Option 1: Service Recovery (Preferred)

If service is healthy but circuit breaker hasn't recovered:

```bash
# 1. Wait for half-open state (automatic after 60s)
# Monitor Grafana dashboard for state transition

# 2. If still open after 5 minutes, force restart
kubectl rollout restart deployment/api

# 3. Verify circuit breaker transitions to HALF_OPEN
watch 'curl -s http://prometheus:9090/api/v1/query \
  -d "query=circuit_breaker_state{service=\"payment-api\"}" | jq'
```

### Option 2: Downstream Service Restart

If downstream service is failing:

```bash
# 1. Restart failing service
kubectl rollout restart deployment/payment-api

# 2. Wait for readiness
kubectl rollout status deployment/payment-api

# 3. Verify health
curl https://payment-api.example.com/health

# 4. Monitor circuit breaker recovery
# Should transition: OPEN → HALF_OPEN → CLOSED
```

### Option 3: Fallback Mode

If service cannot be recovered immediately:

```bash
# 1. Enable fallback configuration
kubectl set env deployment/api \
  PAYMENT_API_FALLBACK_ENABLED=true \
  PAYMENT_API_FALLBACK_MODE=mock

# 2. Restart to apply config
kubectl rollout restart deployment/api

# 3. Verify fallback is active
kubectl logs -l app=api --tail=20 | grep fallback
```

### Option 4: Feature Flag Disable

If feature can be disabled:

```bash
# 1. Disable feature via feature flag
curl -X POST http://feature-flags:8080/api/v1/flags/payment-api-integration \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"enabled": false}'

# 2. Verify feature is disabled
curl http://feature-flags:8080/api/v1/flags/payment-api-integration

# 3. Monitor for reduction in circuit breaker trips
```

---

## ✅ Resolution

### 1. Root Cause Analysis

Determine why circuit breaker opened:

**Common Causes:**
- ⚠️ Downstream service timeout (>30s)
- ⚠️ High error rate from downstream (>50%)
- ⚠️ Network connectivity issues
- ⚠️ Database connection problems
- ⚠️ Rate limiting by external API
- ⚠️ Recent deployment issues

### 2. Fix Root Cause

**For Timeout Issues:**
```python
# Adjust timeout configuration
# src/infrastructure/resilience/circuit_breaker.py

circuit_breaker = CircuitBreaker(
    service_name="payment-api",
    failure_threshold=5,  # Number of failures before opening
    recovery_timeout=60,  # Seconds before attempting recovery
    timeout=5.0,  # Request timeout in seconds (was 30.0)
)
```

**For Error Rate Issues:**
```python
# Review and fix error handling
# Check for proper exception handling in service calls

try:
    response = await payment_api_client.create_payment(data)
    return Ok(response)
except PaymentAPIError as e:
    logger.error(f"Payment API error: {e}", extra={"context": data})
    return Err(PaymentProcessingError(str(e)))
```

**For Network Issues:**
```bash
# Check network policies
kubectl get networkpolicies

# Verify service discovery
kubectl get services payment-api

# Test connectivity
kubectl run -it --rm debug --image=nicolaka/netshoot -- curl payment-api:8080/health
```

### 3. Verify Recovery

```bash
# 1. Check circuit breaker state
curl http://prometheus:9090/api/v1/query \
  -d 'query=circuit_breaker_state{service="payment-api"}'

# Expected: state="closed"

# 2. Monitor success rate
curl http://prometheus:9090/api/v1/query \
  -d 'query=rate(circuit_breaker_successes_total{service="payment-api"}[5m])'

# 3. Check for no new failures
curl http://prometheus:9090/api/v1/query \
  -d 'query=rate(circuit_breaker_failures_total{service="payment-api"}[5m])'
```

### 4. Load Test

```bash
# Run smoke test
python scripts/smoke_test.py --endpoint=/api/v1/payments --requests=100

# Expected: 100% success rate, no circuit breaker trips
```

---

## 🛡️ Prevention

### 1. Improve Resilience Configuration

```python
# src/config/resilience.py

CIRCUIT_BREAKER_CONFIG = {
    "payment-api": {
        "failure_threshold": 5,  # Failures before opening
        "success_threshold": 2,  # Successes to close from half-open
        "recovery_timeout": 60,  # Seconds before half-open
        "timeout": 5.0,  # Request timeout
        "fallback_enabled": True,  # Enable fallback
    }
}
```

### 2. Add Retry Logic

```python
from infrastructure.resilience import RetryPolicy

retry_policy = RetryPolicy(
    max_attempts=3,
    backoff_strategy="exponential",
    initial_delay=1.0,
    max_delay=10.0,
)

@retry_policy.retry
async def call_payment_api(data):
    return await payment_api_client.create_payment(data)
```

### 3. Implement Health Checks

```python
# Add health check for downstream service
@app.get("/ready")
async def readiness_check():
    checks = []

    # Check payment API
    try:
        await payment_api_client.health_check(timeout=1.0)
        checks.append({"service": "payment-api", "status": "up"})
    except Exception:
        checks.append({"service": "payment-api", "status": "down"})

    all_healthy = all(c["status"] == "up" for c in checks)

    if not all_healthy:
        raise HTTPException(status_code=503, detail=checks)

    return {"status": "ready", "checks": checks}
```

### 4. Add Monitoring

```python
# Add circuit breaker metrics
from infrastructure.prometheus import circuit_breaker_state_gauge

circuit_breaker.on_state_change(
    lambda old_state, new_state:
        circuit_breaker_state_gauge.labels(
            service="payment-api",
            state=new_state
        ).set(1)
)
```

### 5. Create Alerts

```yaml
# Already configured in prometheus-alerts-http-infrastructure.yml
- alert: CircuitBreakerOpen
  expr: sum(circuit_breaker_state{state="open"}) > 0
  for: 5m
  labels:
    severity: critical
```

---

## 📊 Monitoring

### Key Metrics

```promql
# Circuit breaker state
circuit_breaker_state{service="payment-api"}

# Failure rate
rate(circuit_breaker_failures_total{service="payment-api"}[5m])

# Success rate after recovery
rate(circuit_breaker_successes_total{service="payment-api"}[5m])

# State transitions
circuit_breaker_transitions_total{service="payment-api"}
```

### Dashboards

- **Infrastructure Dashboard:** `https://grafana.example.com/d/infrastructure`
- **Circuit Breaker Panel:** Shows real-time state
- **Alerts:** PagerDuty, Slack #incidents

---

## 📞 Escalation

### Response Times

| Severity | Response Time | Team |
|----------|---------------|------|
| P0 | 5 minutes | On-Call Engineer |
| P1 | 30 minutes | Backend Team |

### Contacts

- **On-Call:** PagerDuty escalation
- **Backend Lead:** @backend-lead (Slack)
- **DevOps:** @devops-team (Slack)
- **#incidents:** Slack channel

---

## 📝 Postmortem Template

```markdown
# Incident: Circuit Breaker Open - [Service Name]

**Date:** YYYY-MM-DD
**Duration:** HH:MM
**Severity:** P0

## Timeline
- HH:MM - Alert fired
- HH:MM - On-call engineer acknowledged
- HH:MM - Root cause identified
- HH:MM - Mitigation applied
- HH:MM - Service recovered
- HH:MM - Incident resolved

## Root Cause
[Describe root cause]

## Impact
- Users affected: [number]
- Requests failed: [percentage]
- Revenue impact: [if applicable]

## Resolution
[Describe how it was resolved]

## Prevention
- [ ] Action item 1
- [ ] Action item 2
- [ ] Action item 3

## Lessons Learned
[Key takeaways]
```

---

**Version:** 1.0
**Last Updated:** 2025-01-02
**Next Review:** 2025-04-01
