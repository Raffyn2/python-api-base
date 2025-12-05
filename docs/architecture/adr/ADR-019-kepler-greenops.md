# ADR-019: Kepler Integration for GreenOps Sustainability

## Status

Accepted

## Context

Organizations are increasingly required to measure and report on their environmental impact, including carbon emissions from IT infrastructure. Cloud-native workloads running on Kubernetes contribute significantly to energy consumption and carbon footprint.

Key drivers for this decision:
- **Regulatory Compliance**: Growing requirements for sustainability reporting (EU CSRD, SEC climate disclosure)
- **Cost Optimization**: Energy costs represent significant operational expenses
- **Corporate Sustainability Goals**: Net-zero commitments require accurate measurement
- **Developer Awareness**: Teams need visibility into the environmental impact of their applications

## Decision

We will integrate **Kepler** (Kubernetes-based Efficient Power Level Exporter), a CNCF Sandbox project, to measure energy consumption at the container, pod, and node level. This will be combined with carbon intensity data to calculate emissions and support GreenOps practices.

### Key Components

1. **Kepler DaemonSet**: Deployed to all nodes to collect energy metrics using eBPF and hardware sensors (RAPL, ACPI)
2. **Sustainability Service**: Python module for carbon calculations, cost estimation, and reporting
3. **API Endpoints**: REST API for querying sustainability metrics
4. **Grafana Dashboard**: Visualization of energy consumption and carbon emissions
5. **Prometheus Alerts**: Threshold-based alerts for energy anomalies

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Kepler    │  │   Kepler    │  │   Kepler    │         │
│  │  (Node 1)   │  │  (Node 2)   │  │  (Node N)   │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                          ▼                                  │
│                   ┌─────────────┐                           │
│                   │ Prometheus  │                           │
│                   └──────┬──────┘                           │
│                          │                                  │
│         ┌────────────────┼────────────────┐                 │
│         ▼                ▼                ▼                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Grafana   │  │Sustainability│  │Alertmanager │         │
│  │  Dashboard  │  │   Service   │  │             │         │
│  └─────────────┘  └──────┬──────┘  └─────────────┘         │
│                          │                                  │
│                          ▼                                  │
│                   ┌─────────────┐                           │
│                   │  REST API   │                           │
│                   │/sustainability│                          │
│                   └─────────────┘                           │
└─────────────────────────────────────────────────────────────┘
```

## Alternatives Considered

### 1. Cloud Provider Native Tools
- **AWS Customer Carbon Footprint Tool**: Limited to AWS, no real-time data
- **Google Cloud Carbon Footprint**: Limited to GCP, monthly granularity
- **Azure Emissions Impact Dashboard**: Limited to Azure

**Rejected**: Vendor lock-in, limited granularity, no container-level attribution

### 2. OpenCost with Carbon Extension
- Provides cost allocation with carbon estimates
- Less accurate energy measurement than Kepler

**Rejected**: Kepler provides more accurate energy data via eBPF/RAPL

### 3. Custom eBPF Solution
- Build custom energy monitoring
- Full control over implementation

**Rejected**: Significant development effort, Kepler is mature CNCF project

### 4. Scaphandre
- Rust-based energy monitoring agent
- Similar capabilities to Kepler

**Rejected**: Kepler has broader CNCF community support and integration

## Consequences

### Positive

1. **Accurate Energy Measurement**: eBPF-based measurement provides container-level granularity
2. **Carbon Attribution**: Ability to attribute emissions to specific workloads
3. **Cost Visibility**: Energy costs correlated with cloud spending
4. **Standards Compliance**: Supports sustainability reporting requirements
5. **Developer Awareness**: Teams can see environmental impact of their code
6. **Optimization Opportunities**: Data-driven decisions for energy efficiency

### Negative

1. **Resource Overhead**: Kepler DaemonSet consumes CPU/memory on each node
2. **Privileged Access**: Requires privileged containers for eBPF/RAPL access
3. **Hardware Dependency**: Accuracy depends on hardware sensor availability
4. **External API Dependency**: Carbon intensity data requires external API

### Neutral

1. **Learning Curve**: Teams need to understand sustainability metrics
2. **Maintenance**: Additional component to maintain and upgrade
3. **Data Volume**: Increased metrics storage requirements

## Implementation Notes

### Kepler Metrics

Key Prometheus metrics exposed by Kepler:
- `kepler_container_joules_total`: Total energy consumption per container
- `kepler_node_core_joules_total`: CPU core energy consumption
- `kepler_node_dram_joules_total`: Memory energy consumption
- `kepler_node_package_joules_total`: CPU package energy consumption

### Carbon Calculation

```
Carbon Emissions (gCO2) = Energy (kWh) × Carbon Intensity (gCO2/kWh)
```

Carbon intensity varies by region and time based on the electricity grid mix.

### Security Considerations

- Kepler requires privileged access for eBPF probes
- ServiceAccount with minimal RBAC permissions
- Network policies to restrict metrics access
- No sensitive data in energy metrics

## References

- [Kepler Project](https://github.com/sustainable-computing-io/kepler)
- [CNCF TAG Environmental Sustainability](https://tag-env-sustainability.cncf.io/)
- [Green Software Foundation](https://greensoftware.foundation/)
- [Electricity Maps API](https://www.electricitymap.org/)
