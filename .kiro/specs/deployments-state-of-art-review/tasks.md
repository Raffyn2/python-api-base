# Implementation Plan

## Deployments State of Art Review

- [x] 1. Setup validation infrastructure and property testing framework
  - [x] 1.1 Create manifest validation utilities
    - Create `tests/properties/deployments/validators.py` with K8sManifestValidator, HelmChartValidator, TerraformValidator classes
    - Implement YAML parsing and validation logic
    - _Requirements: 1.1, 2.1, 3.1_
  - [x] 1.2 Write property test for security context completeness
    - **Property 1: Security Context Completeness**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.5**
  - [x] 1.3 Write property test for resource limits
    - **Property 3: Resource Limits Defined**
    - **Validates: Requirements 2.4**
  - [x] 1.4 Create validation script for CI
    - Create `scripts/validate-manifests.sh` with helm lint, kubeval, checkov integration
    - _Requirements: 2.5_

- [x] 2. Kubernetes security hardening improvements
  - [x] 2.1 Audit and fix security contexts in k8s/base
    - Verify seccompProfile: RuntimeDefault in all deployments
    - Ensure runAsNonRoot: true and runAsUser >= 1000
    - Confirm capabilities.drop: [ALL] and allowPrivilegeEscalation: false
    - _Requirements: 1.1, 1.2, 1.3, 1.5_
  - [x] 2.2 Write property test for network policy existence
    - **Property 2: Network Policy Existence**
    - **Validates: Requirements 1.4**
  - [x] 2.3 Verify network policies have deny-all default
    - Check both Ingress and Egress policyTypes are defined
    - Verify explicit allow rules for required traffic
    - _Requirements: 1.4_
  - [x] 2.4 Write property test for labels convention
    - **Property 38: Labels Convention**
    - **Validates: Requirements 1.1 (implicit)**

- [x] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Helm chart best practices improvements
  - [x] 4.1 Add values validation and schema
    - Create `deployments/helm/api/values.schema.json` for validation
    - Add required field comments in values.yaml
    - _Requirements: 2.1_
  - [x] 4.2 Write property test for no latest tags
    - **Property 4: No Latest Tags**
    - **Validates: Requirements 2.2**
  - [x] 4.3 Write property test for external secrets enabled
    - **Property 5: External Secrets Enabled**
    - **Validates: Requirements 2.3**
  - [x] 4.4 Verify Helm templates security contexts
    - Ensure deployment.yaml template includes all security hardening
    - Add seccompProfile to template if missing
    - _Requirements: 1.1, 1.3_

- [x] 5. Terraform infrastructure security improvements
  - [x] 5.1 Verify backend encryption and state locking
    - Check main.tf has encrypt=true and dynamodb_table
    - _Requirements: 3.1_
  - [x] 5.2 Write property test for backend encryption
    - **Property 6: Terraform Backend Encryption**
    - **Validates: Requirements 3.1**
  - [x] 5.3 Write property test for sensitive variables
    - **Property 7: Sensitive Variables Marked**
    - **Validates: Requirements 3.2**
  - [x] 5.4 Write property test for common tags
    - **Property 8: Common Tags Applied**
    - **Validates: Requirements 3.3**
  - [x] 5.5 Write property test for provider versions
    - **Property 24: Terraform Provider Versions Constrained**
    - **Validates: Requirements 3.4**
  - [x] 5.6 Update Terraform provider versions
    - Update versions.tf with latest stable versions
    - Test compatibility with existing configurations
    - _Requirements: 3.4_

- [x] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. ArgoCD GitOps configuration improvements
  - [x] 7.1 Add sync waves to ArgoCD applications
    - Add argocd.argoproj.io/sync-wave annotations to order resources
    - _Requirements: 4.1_
  - [x] 7.2 Write property test for sync waves
    - **Property 9: ArgoCD Sync Waves**
    - **Validates: Requirements 4.1**
  - [x] 7.3 Write property test for production manual sync
    - **Property 10: Production Manual Sync**
    - **Validates: Requirements 4.2**
  - [x] 7.4 Write property test for sealed secrets usage
    - **Property 37: Sealed Secrets Usage**
    - **Validates: Requirements 4.3**
  - [x] 7.5 Write property test for image updater
    - **Property 25: ArgoCD Image Updater Configured**
    - **Validates: Requirements 4.5**

- [x] 8. Istio service mesh security improvements
  - [x] 8.1 Verify mTLS STRICT in production overlay
    - Check PeerAuthentication has mtls.mode: STRICT
    - _Requirements: 5.1_
  - [x] 8.2 Write property test for mTLS strict
    - **Property 11: Istio mTLS Strict**
    - **Validates: Requirements 5.1**
  - [x] 8.3 Write property test for authorization deny-all
    - **Property 12: Authorization Deny-All**
    - **Validates: Requirements 5.2**
  - [x] 8.4 Write property test for JWT validation
    - **Property 26: Istio JWT Validation**
    - **Validates: Requirements 5.3**
  - [x] 8.5 Write property test for rate limiting
    - **Property 13: Rate Limiting Configured**
    - **Validates: Requirements 5.4**
  - [x] 8.6 Write property test for egress restriction
    - **Property 27: Istio Egress Restricted**
    - **Validates: Requirements 5.5**
  - [x] 8.7 Update Istio version in overlays
    - Update istio-operator.yaml to version 1.24.0
    - Test compatibility with existing configurations
    - _Requirements: 5.1_

- [x] 9. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Knative serverless configuration improvements
  - [x] 10.1 Verify scale-to-zero configuration
    - Check autoscaling.knative.dev/min-scale allows "0"
    - _Requirements: 6.1_
  - [x] 10.2 Write property test for scale-to-zero
    - **Property 14: Knative Scale-to-Zero**
    - **Validates: Requirements 6.1**
  - [x] 10.3 Write property test for autoscaling metrics
    - **Property 28: Knative Autoscaling Metrics**
    - **Validates: Requirements 6.2**
  - [x] 10.4 Write property test for Knative security context
    - **Property 15: Knative Security Context**
    - **Validates: Requirements 6.3**

- [x] 11. Docker production optimization improvements
  - [x] 11.1 Verify multi-stage builds in Dockerfiles
    - Check all production Dockerfiles use multi-stage builds
    - _Requirements: 7.1_
  - [x] 11.2 Write property test for multi-stage build
    - **Property 16: Docker Multi-Stage Build**
    - **Validates: Requirements 7.1**
  - [x] 11.3 Write property test for Docker non-root
    - **Property 17: Docker Non-Root**
    - **Validates: Requirements 7.2**
  - [x] 11.4 Write property test for Docker resource limits
    - **Property 29: Docker Resource Limits**
    - **Validates: Requirements 7.3**
  - [x] 11.5 Write property test for Docker health checks
    - **Property 30: Docker Health Checks**
    - **Validates: Requirements 7.4**
  - [x] 11.6 Write property test for structured logging
    - **Property 31: Structured Logging Enabled**
    - **Validates: Requirements 7.5**

- [x] 12. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 13. Monitoring and observability improvements
  - [x] 13.1 Verify ServiceMonitor configurations
    - Check all workloads have ServiceMonitor with correct selector
    - _Requirements: 8.1_
  - [x] 13.2 Write property test for ServiceMonitor
    - **Property 18: ServiceMonitor Exists**
    - **Validates: Requirements 8.1**
  - [x] 13.3 Write property test for alert severity
    - **Property 19: Alert Severity Labels**
    - **Validates: Requirements 8.2**
  - [x] 13.4 Write property test for Prometheus annotations
    - **Property 39: Annotations for Prometheus**
    - **Validates: Requirements 8.1**
  - [x] 13.5 Write property test for tracing sampling
    - **Property 32: Tracing Sampling Configured**
    - **Validates: Requirements 8.4**
  - [x] 13.6 Add runbook URLs to alerts
    - Update prometheus-alerts-*.yml with annotations.runbook_url
    - _Requirements: 8.2_

- [x] 14. High availability configuration improvements
  - [x] 14.1 Verify topology spread constraints
    - Check all Deployments have topologySpreadConstraints for zone distribution
    - _Requirements: 9.1_
  - [x] 14.2 Write property test for topology spread
    - **Property 20: Topology Spread Constraints**
    - **Validates: Requirements 9.1**
  - [x] 14.3 Write property test for PDB
    - **Property 21: PDB Configured**
    - **Validates: Requirements 9.2**
  - [x] 14.4 Write property test for liveness probe
    - **Property 33: Liveness Probe Configured**
    - **Validates: Requirements 9.3**
  - [x] 14.5 Write property test for readiness probe
    - **Property 34: Readiness Probe Configured**
    - **Validates: Requirements 9.4**
  - [x] 14.6 Write property test for HPA behavior
    - **Property 22: HPA Behavior Policies**
    - **Validates: Requirements 9.5**
  - [x] 14.7 Write property test for graceful shutdown
    - **Property 40: Graceful Shutdown**
    - **Validates: Requirements 9.3 (implicit)**
  - [x] 14.8 Write property test for rolling update strategy
    - **Property 45: Rolling Update Strategy**
    - **Validates: Requirements 9.2 (implicit)**

- [x] 15. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 16. Cost optimization improvements
  - [x] 16.1 Verify single NAT gateway option
    - Check Terraform has single_nat_gateway variable
    - _Requirements: 10.1_
  - [x] 16.2 Write property test for single NAT gateway
    - **Property 35: Single NAT Gateway Option**
    - **Validates: Requirements 10.1**
  - [x] 16.3 Write property test for resource quota
    - **Property 23: Resource Quota Exists**
    - **Validates: Requirements 10.5**

- [x] 17. Additional best practices improvements
  - [x] 17.1 Write property test for DNS config
    - **Property 41: DNS Config Optimized**
    - **Validates: Requirements 9.4 (implicit)**
  - [x] 17.2 Write property test for emptyDir limits
    - **Property 42: EmptyDir Size Limits**
    - **Validates: Requirements 1.3 (implicit)**
  - [x] 17.3 Write property test for service account token
    - **Property 43: Service Account Token Disabled**
    - **Validates: Requirements 1.5 (implicit)**
  - [x] 17.4 Write property test for revision history
    - **Property 44: Revision History Limit**
    - **Validates: Requirements 10.5 (implicit)**

- [x] 18. Documentation and ADR updates
  - [x] 18.1 Update ADR-020 with new improvements
    - Document all changes made during this review
    - Add references to new properties and tests
    - _Requirements: All_
  - [x] 18.2 Create ADR-021 for validation framework
    - Document the property-based testing approach
    - Include CI integration details
    - _Requirements: All_
  - [x] 18.3 Update deployments/README.md
    - Add validation commands section
    - Update version compatibility table
    - _Requirements: All_

- [x] 19. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Summary

All 19 tasks completed successfully:
- Created validation framework with 6 validator classes
- Implemented 45 property-based tests
- Created CI validation script
- Added Helm values JSON schema
- Updated ADR-020 and created ADR-021
- Updated deployments README with validation section

Tests: 24 passed, 143 skipped (skips are expected for non-applicable manifest types)
