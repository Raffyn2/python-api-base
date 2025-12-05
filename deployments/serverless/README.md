# Serverless Deployments

This directory contains adapters for deploying the Python API Base to serverless platforms.

## Supported Platforms

| Platform | Directory | Status | Type |
|----------|-----------|--------|------|
| Knative | `../knative/` | ✅ Ready | Kubernetes-native |
| AWS Lambda | `aws-lambda/` | ✅ Ready | FaaS |
| Vercel | `vercel/` | ✅ Ready | FaaS |

> **Note**: Knative is the recommended serverless option for Kubernetes environments. See [Knative README](../knative/README.md) for details.

## Quick Reference

### AWS Lambda

```bash
# Using SAM CLI
sam build --template deployments/serverless/aws-lambda/template.yaml
sam deploy --guided
```

**Handler:** `deployments.serverless.aws_lambda.handler.handler`

### Vercel

```bash
cd deployments/serverless/vercel
vercel --prod
```

**Handler:** `api/index.py` (auto-detected)

## Architecture Comparison

| Feature | Knative | AWS Lambda | Vercel |
|---------|---------|------------|--------|
| Cold Start | ~1-5s | ~1-3s | ~500ms-2s |
| Max Duration | Configurable | 15min | 30s (Pro) |
| Max Memory | Configurable | 10GB | 3GB |
| Scale-to-Zero | ✅ | ✅ | ✅ |
| VPC Support | ✅ (K8s) | ✅ | ❌ |
| Edge Functions | Via Istio | Via CloudFront | ✅ Native |
| Vendor Lock-in | None | High | Medium |
| Traffic Splitting | ✅ Native | Via ALB | ✅ Native |
| Event Sources | Kafka, HTTP | AWS Services | HTTP |
| Pricing | K8s infra | Pay per invocation | Free tier + usage |

## Common Considerations

### Database Connections

Serverless functions don't maintain persistent connections. Use:

- **Connection Poolers**: PgBouncer, RDS Proxy
- **Serverless Databases**: Neon, PlanetScale, Supabase
- **Redis**: Upstash (serverless Redis)

### Environment Variables

All platforms support environment variables via their dashboards:

```bash
# Required
DATABASE__URL=postgresql://...
SECURITY__SECRET_KEY=your-secret-key

# Optional
OBSERVABILITY__REDIS_URL=redis://...
OBSERVABILITY__LOG_LEVEL=INFO
```

### Cold Start Optimization

1. **Minimize dependencies**: Use lightweight alternatives
2. **Lazy loading**: Import heavy modules only when needed
3. **Connection pooling**: Reuse connections across invocations
4. **Provisioned concurrency** (Lambda): Keep instances warm

## Testing Locally

### Lambda

```bash
# Install SAM CLI
pip install aws-sam-cli

# Start local API
sam local start-api
```

### Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Run locally
vercel dev
```


## Knative (Kubernetes-native Serverless)

For Kubernetes environments, Knative provides a powerful serverless platform with:

- Auto-scaling including scale-to-zero
- Traffic splitting for canary deployments
- CloudEvents support for event-driven architectures
- Integration with Istio for mTLS and observability
- No vendor lock-in

```bash
# Deploy to Kubernetes with Knative
kubectl apply -k ../knative/overlays/prod

# Get service URL
kubectl get ksvc python-api-base -n my-api -o jsonpath='{.status.url}'
```

See [Knative README](../knative/README.md) for complete documentation.
