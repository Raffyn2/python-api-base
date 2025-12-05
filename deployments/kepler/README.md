# Kepler Deployment

Kepler (Kubernetes-based Efficient Power Level Exporter) is a CNCF Sandbox project that measures energy consumption at the container, pod, and node level in Kubernetes clusters.

## Overview

This deployment provides:
- **DaemonSet**: Kepler pods running on every node
- **ServiceMonitor**: Prometheus integration for metrics scraping
- **RBAC**: Minimal permissions for Kepler operation

## Prerequisites

- Kubernetes 1.25+
- Prometheus Operator (for ServiceMonitor)
- Nodes with RAPL support (Intel) or ACPI for accurate measurements
- Privileged container support

## Installation

### Using Kustomize

```bash
# Development environment
kubectl apply -k deployments/kepler/overlays/development

# Production environment
kubectl apply -k deployments/kepler/overlays/production
```

### Verify Installation

```bash
# Check DaemonSet status
kubectl get daemonset -n kepler-system

# Check pod status
kubectl get pods -n kepler-system

# Verify metrics endpoint
kubectl port-forward -n kepler-system daemonset/kepler 9102:9102
curl http://localhost:9102/metrics | grep kepler_container_joules
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `KEPLER_LOG_LEVEL` | `1` | Log verbosity (1-5) |
| `ENABLE_GPU` | `false` | Enable GPU energy monitoring |
| `ENABLE_EBPF_CGROUPID` | `true` | Use eBPF for cgroup tracking |
| `EXPOSE_HARDWARE_COUNTER_METRICS` | `true` | Expose hardware counters |
| `MODEL_SERVER_ENABLE` | `false` | Enable ML model server |

### Resource Limits

Development:
- CPU: 50m-200m
- Memory: 200Mi-512Mi

Production:
- CPU: 100m-1000m
- Memory: 400Mi-2Gi

## Metrics

### Key Metrics

| Metric | Description |
|--------|-------------|
| `kepler_container_joules_total` | Total energy per container |
| `kepler_node_core_joules_total` | CPU core energy per node |
| `kepler_node_dram_joules_total` | Memory energy per node |
| `kepler_node_package_joules_total` | CPU package energy |

### Example PromQL Queries

```promql
# Energy consumption by namespace (kWh/h)
sum by (namespace) (rate(kepler_container_joules_total[5m])) / 3600000

# Top 10 energy-consuming pods
topk(10, sum by (pod) (rate(kepler_container_joules_total[5m])))

# Total cluster energy consumption
sum(rate(kepler_container_joules_total[5m])) / 3600000
```

## Troubleshooting

### Kepler Pod Not Starting

1. Check node capabilities:
```bash
kubectl describe node <node-name> | grep -i rapl
```

2. Verify privileged containers are allowed:
```bash
kubectl auth can-i create pods --as=system:serviceaccount:kepler-system:kepler
```

### No Metrics Available

1. Check Kepler logs:
```bash
kubectl logs -n kepler-system -l app.kubernetes.io/name=kepler
```

2. Verify eBPF support:
```bash
kubectl exec -n kepler-system -it <kepler-pod> -- cat /sys/kernel/debug/tracing/available_events | grep power
```

### Inaccurate Readings

- Ensure RAPL is available on Intel CPUs
- For VMs, Kepler uses ML models for estimation
- Check `source` label in metrics for measurement method

## Security

- Kepler requires privileged access for eBPF probes
- Minimal RBAC permissions (read-only access to pods/nodes)
- No sensitive data in metrics
- Consider network policies to restrict metrics access

## References

- [Kepler Documentation](https://sustainable-computing.io/)
- [Kepler GitHub](https://github.com/sustainable-computing-io/kepler)
- [CNCF TAG Environmental Sustainability](https://tag-env-sustainability.cncf.io/)
