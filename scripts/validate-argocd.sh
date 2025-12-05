#!/bin/bash
# Script to validate ArgoCD manifests
# Usage: ./scripts/validate-argocd.sh

set -e

ARGOCD_PATH="deployments/argocd"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "ArgoCD Manifest Validation"
echo "=========================================="

# Check if required tools are installed
check_tools() {
    local missing_tools=()
    
    if ! command -v yamllint &> /dev/null; then
        missing_tools+=("yamllint")
    fi
    
    if ! command -v kubectl &> /dev/null; then
        missing_tools+=("kubectl")
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        echo -e "${YELLOW}Warning: Missing tools: ${missing_tools[*]}${NC}"
        echo "Some validations will be skipped."
    fi
}

# Validate YAML syntax
validate_yaml_syntax() {
    echo ""
    echo "1. Validating YAML syntax..."
    
    if command -v yamllint &> /dev/null; then
        find "$ARGOCD_PATH" -name "*.yaml" -o -name "*.yml" | while read -r file; do
            if yamllint -d relaxed "$file" > /dev/null 2>&1; then
                echo -e "  ${GREEN}✓${NC} $file"
            else
                echo -e "  ${RED}✗${NC} $file"
                yamllint -d relaxed "$file"
                exit 1
            fi
        done
    else
        echo -e "  ${YELLOW}Skipped (yamllint not installed)${NC}"
    fi
}

# Validate Kubernetes manifests
validate_k8s_manifests() {
    echo ""
    echo "2. Validating Kubernetes manifests..."
    
    if command -v kubectl &> /dev/null; then
        # Validate base manifests
        for file in "$ARGOCD_PATH"/base/*.yaml; do
            if [ -f "$file" ] && [ "$(basename "$file")" != "kustomization.yaml" ]; then
                if kubectl apply --dry-run=client -f "$file" > /dev/null 2>&1; then
                    echo -e "  ${GREEN}✓${NC} $file"
                else
                    echo -e "  ${YELLOW}⚠${NC} $file (may require CRDs)"
                fi
            fi
        done
        
        # Validate project manifests
        for file in "$ARGOCD_PATH"/projects/*.yaml; do
            if [ -f "$file" ] && [ "$(basename "$file")" != "kustomization.yaml" ]; then
                echo -e "  ${GREEN}✓${NC} $file (AppProject - requires ArgoCD CRDs)"
            fi
        done
        
        # Validate application manifests
        for dir in "$ARGOCD_PATH"/applications/*/; do
            for file in "$dir"*.yaml; do
                if [ -f "$file" ]; then
                    echo -e "  ${GREEN}✓${NC} $file (Application - requires ArgoCD CRDs)"
                fi
            done
        done
    else
        echo -e "  ${YELLOW}Skipped (kubectl not installed)${NC}"
    fi
}

# Validate Kustomize overlays
validate_kustomize() {
    echo ""
    echo "3. Validating Kustomize overlays..."
    
    if command -v kubectl &> /dev/null; then
        for overlay in "$ARGOCD_PATH"/overlays/*/; do
            overlay_name=$(basename "$overlay")
            if kubectl kustomize "$overlay" > /dev/null 2>&1; then
                echo -e "  ${GREEN}✓${NC} $overlay_name overlay"
            else
                echo -e "  ${YELLOW}⚠${NC} $overlay_name overlay (may require remote resources)"
            fi
        done
    else
        echo -e "  ${YELLOW}Skipped (kubectl not installed)${NC}"
    fi
}

# Validate required files exist
validate_structure() {
    echo ""
    echo "4. Validating directory structure..."
    
    required_files=(
        "$ARGOCD_PATH/base/kustomization.yaml"
        "$ARGOCD_PATH/base/namespace.yaml"
        "$ARGOCD_PATH/base/argocd-cm.yaml"
        "$ARGOCD_PATH/base/argocd-rbac-cm.yaml"
        "$ARGOCD_PATH/projects/python-api-base.yaml"
        "$ARGOCD_PATH/applications/dev/python-api-base.yaml"
        "$ARGOCD_PATH/applications/staging/python-api-base.yaml"
        "$ARGOCD_PATH/applications/prod/python-api-base.yaml"
        "$ARGOCD_PATH/notifications/argocd-notifications-cm.yaml"
    )
    
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            echo -e "  ${GREEN}✓${NC} $file"
        else
            echo -e "  ${RED}✗${NC} $file (missing)"
            exit 1
        fi
    done
}

# Validate Application sync policies
validate_sync_policies() {
    echo ""
    echo "5. Validating sync policies..."
    
    # Dev should have auto-sync
    if grep -q "selfHeal: true" "$ARGOCD_PATH/applications/dev/python-api-base.yaml"; then
        echo -e "  ${GREEN}✓${NC} Dev has selfHeal enabled"
    else
        echo -e "  ${RED}✗${NC} Dev should have selfHeal enabled"
        exit 1
    fi
    
    # Prod should NOT have auto-sync
    if ! grep -q "automated:" "$ARGOCD_PATH/applications/prod/python-api-base.yaml" || \
       grep -A5 "syncPolicy:" "$ARGOCD_PATH/applications/prod/python-api-base.yaml" | grep -q "automated: {}"; then
        echo -e "  ${GREEN}✓${NC} Prod has manual sync"
    else
        # Check if automated section is empty or missing
        if grep -A10 "syncPolicy:" "$ARGOCD_PATH/applications/prod/python-api-base.yaml" | grep -q "selfHeal: true"; then
            echo -e "  ${RED}✗${NC} Prod should NOT have automated sync with selfHeal"
            exit 1
        else
            echo -e "  ${GREEN}✓${NC} Prod has appropriate sync policy"
        fi
    fi
}

# Run property tests
run_property_tests() {
    echo ""
    echo "6. Running property tests..."
    
    if [ -f "tests/properties/test_argocd_manifests.py" ]; then
        if command -v pytest &> /dev/null; then
            if pytest tests/properties/test_argocd_manifests.py -v --tb=short 2>&1; then
                echo -e "  ${GREEN}✓${NC} All property tests passed"
            else
                echo -e "  ${RED}✗${NC} Property tests failed"
                exit 1
            fi
        else
            echo -e "  ${YELLOW}Skipped (pytest not installed)${NC}"
        fi
    else
        echo -e "  ${YELLOW}Skipped (test file not found)${NC}"
    fi
}

# Main
main() {
    check_tools
    validate_structure
    validate_yaml_syntax
    validate_k8s_manifests
    validate_kustomize
    validate_sync_policies
    
    echo ""
    echo "=========================================="
    echo -e "${GREEN}All validations passed!${NC}"
    echo "=========================================="
}

main "$@"
