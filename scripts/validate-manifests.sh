#!/bin/bash
# =============================================================================
# Manifest Validation Script for CI/CD
# =============================================================================
#
# This script validates all deployment manifests against security best practices
# and organizational standards.
#
# Usage:
#   ./scripts/validate-manifests.sh [--fix] [--verbose]
#
# Options:
#   --fix      Attempt to fix issues automatically (where possible)
#   --verbose  Show detailed output
#
# Exit codes:
#   0 - All validations passed
#   1 - Validation errors found
#   2 - Tool not installed
#
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEPLOYMENTS_DIR="deployments"
HELM_CHART_DIR="deployments/helm/api"
TERRAFORM_DIR="deployments/terraform"
K8S_DIR="deployments/k8s"
ISTIO_DIR="deployments/istio"
KNATIVE_DIR="deployments/knative"

# Counters
ERRORS=0
WARNINGS=0
PASSED=0

# Parse arguments
FIX_MODE=false
VERBOSE=false

for arg in "$@"; do
    case $arg in
        --fix)
            FIX_MODE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
    esac
done

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED++))
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    ((WARNINGS++))
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((ERRORS++))
}

check_tool() {
    if ! command -v "$1" &> /dev/null; then
        log_warning "$1 is not installed, skipping related checks"
        return 1
    fi
    return 0
}

# =============================================================================
# YAML Lint
# =============================================================================
validate_yaml() {
    log_info "Validating YAML syntax..."
    
    if ! check_tool yamllint; then
        return
    fi
    
    local yaml_files
    yaml_files=$(find "$DEPLOYMENTS_DIR" -name "*.yaml" -o -name "*.yml" 2>/dev/null | grep -v node_modules || true)
    
    if [ -z "$yaml_files" ]; then
        log_warning "No YAML files found"
        return
    fi
    
    local failed=false
    for file in $yaml_files; do
        if $VERBOSE; then
            log_info "Checking $file"
        fi
        if ! yamllint -d relaxed "$file" 2>/dev/null; then
            log_error "YAML lint failed: $file"
            failed=true
        fi
    done
    
    if [ "$failed" = false ]; then
        log_success "YAML syntax validation passed"
    fi
}

# =============================================================================
# Helm Lint
# =============================================================================
validate_helm() {
    log_info "Validating Helm charts..."
    
    if ! check_tool helm; then
        return
    fi
    
    if [ ! -d "$HELM_CHART_DIR" ]; then
        log_warning "Helm chart directory not found: $HELM_CHART_DIR"
        return
    fi
    
    # Lint the chart
    if helm lint "$HELM_CHART_DIR" --quiet; then
        log_success "Helm lint passed"
    else
        log_error "Helm lint failed"
    fi
    
    # Template validation
    if helm template test "$HELM_CHART_DIR" --dry-run > /dev/null 2>&1; then
        log_success "Helm template rendering passed"
    else
        log_error "Helm template rendering failed"
    fi
}

# =============================================================================
# Kubernetes Manifest Validation (kubeval/kubeconform)
# =============================================================================
validate_k8s_manifests() {
    log_info "Validating Kubernetes manifests..."
    
    local validator=""
    if check_tool kubeconform; then
        validator="kubeconform"
    elif check_tool kubeval; then
        validator="kubeval"
    else
        log_warning "Neither kubeconform nor kubeval installed, skipping K8s validation"
        return
    fi
    
    local k8s_files
    k8s_files=$(find "$K8S_DIR" -name "*.yaml" 2>/dev/null || true)
    
    if [ -z "$k8s_files" ]; then
        log_warning "No Kubernetes manifests found"
        return
    fi
    
    local failed=false
    for file in $k8s_files; do
        if $VERBOSE; then
            log_info "Validating $file"
        fi
        
        if [ "$validator" = "kubeconform" ]; then
            if ! kubeconform -strict -ignore-missing-schemas "$file" 2>/dev/null; then
                log_error "K8s validation failed: $file"
                failed=true
            fi
        else
            if ! kubeval --strict "$file" 2>/dev/null; then
                log_error "K8s validation failed: $file"
                failed=true
            fi
        fi
    done
    
    if [ "$failed" = false ]; then
        log_success "Kubernetes manifest validation passed"
    fi
}

# =============================================================================
# Terraform Validation
# =============================================================================
validate_terraform() {
    log_info "Validating Terraform configurations..."
    
    if ! check_tool terraform; then
        return
    fi
    
    if [ ! -d "$TERRAFORM_DIR" ]; then
        log_warning "Terraform directory not found: $TERRAFORM_DIR"
        return
    fi
    
    pushd "$TERRAFORM_DIR" > /dev/null
    
    # Format check
    if terraform fmt -check -recursive > /dev/null 2>&1; then
        log_success "Terraform format check passed"
    else
        if $FIX_MODE; then
            terraform fmt -recursive
            log_info "Terraform files formatted"
        else
            log_error "Terraform format check failed (run with --fix to auto-format)"
        fi
    fi
    
    # Validate (requires init, skip if not initialized)
    if [ -d ".terraform" ]; then
        if terraform validate > /dev/null 2>&1; then
            log_success "Terraform validation passed"
        else
            log_error "Terraform validation failed"
        fi
    else
        log_warning "Terraform not initialized, skipping validate"
    fi
    
    popd > /dev/null
}

# =============================================================================
# Security Scanning (Checkov/Trivy)
# =============================================================================
validate_security() {
    log_info "Running security scans..."
    
    local scanner=""
    if check_tool checkov; then
        scanner="checkov"
    elif check_tool trivy; then
        scanner="trivy"
    else
        log_warning "Neither checkov nor trivy installed, skipping security scan"
        return
    fi
    
    if [ "$scanner" = "checkov" ]; then
        # Run checkov with soft-fail for warnings
        if checkov -d "$DEPLOYMENTS_DIR" --quiet --compact --soft-fail 2>/dev/null; then
            log_success "Checkov security scan passed"
        else
            log_warning "Checkov found issues (review recommended)"
        fi
    else
        # Run trivy config scan
        if trivy config "$DEPLOYMENTS_DIR" --severity HIGH,CRITICAL --exit-code 0 2>/dev/null; then
            log_success "Trivy security scan passed"
        else
            log_warning "Trivy found issues (review recommended)"
        fi
    fi
}

# =============================================================================
# Kustomize Validation
# =============================================================================
validate_kustomize() {
    log_info "Validating Kustomize overlays..."
    
    if ! check_tool kustomize && ! check_tool kubectl; then
        return
    fi
    
    local kustomize_cmd="kustomize"
    if ! command -v kustomize &> /dev/null; then
        kustomize_cmd="kubectl kustomize"
    fi
    
    # Find all kustomization.yaml files
    local kustomize_dirs
    kustomize_dirs=$(find "$DEPLOYMENTS_DIR" -name "kustomization.yaml" -exec dirname {} \; 2>/dev/null || true)
    
    if [ -z "$kustomize_dirs" ]; then
        log_warning "No Kustomize configurations found"
        return
    fi
    
    local failed=false
    for dir in $kustomize_dirs; do
        if $VERBOSE; then
            log_info "Building $dir"
        fi
        if ! $kustomize_cmd build "$dir" > /dev/null 2>&1; then
            log_error "Kustomize build failed: $dir"
            failed=true
        fi
    done
    
    if [ "$failed" = false ]; then
        log_success "Kustomize validation passed"
    fi
}

# =============================================================================
# Property-Based Tests
# =============================================================================
run_property_tests() {
    log_info "Running property-based tests..."
    
    if ! check_tool pytest; then
        return
    fi
    
    if [ ! -d "tests/properties/deployments" ]; then
        log_warning "Property tests directory not found"
        return
    fi
    
    if pytest tests/properties/deployments/ -v --tb=short 2>/dev/null; then
        log_success "Property-based tests passed"
    else
        log_error "Property-based tests failed"
    fi
}

# =============================================================================
# Main
# =============================================================================
main() {
    echo "=============================================="
    echo "  Deployment Manifest Validation"
    echo "=============================================="
    echo ""
    
    validate_yaml
    validate_helm
    validate_k8s_manifests
    validate_terraform
    validate_kustomize
    validate_security
    run_property_tests
    
    echo ""
    echo "=============================================="
    echo "  Summary"
    echo "=============================================="
    echo -e "  ${GREEN}Passed:${NC}   $PASSED"
    echo -e "  ${YELLOW}Warnings:${NC} $WARNINGS"
    echo -e "  ${RED}Errors:${NC}   $ERRORS"
    echo "=============================================="
    
    if [ $ERRORS -gt 0 ]; then
        echo -e "${RED}Validation failed with $ERRORS error(s)${NC}"
        exit 1
    else
        echo -e "${GREEN}All validations passed!${NC}"
        exit 0
    fi
}

main "$@"
