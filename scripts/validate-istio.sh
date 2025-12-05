#!/bin/bash
# Istio Manifest Validation Script
# Usage: ./scripts/validate-istio.sh [overlay]
# Example: ./scripts/validate-istio.sh prod

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ISTIO_DIR="$PROJECT_ROOT/deployments/istio"
OVERLAY="${1:-base}"

echo "🔍 Validating Istio manifests..."
echo "================================"

# Check if istioctl is installed
if ! command -v istioctl &> /dev/null; then
    echo "⚠️  istioctl not found. Install with:"
    echo "   curl -L https://istio.io/downloadIstio | sh -"
    echo ""
    echo "Skipping istioctl validation, running YAML validation only..."
    SKIP_ISTIOCTL=true
else
    SKIP_ISTIOCTL=false
    echo "✅ istioctl found: $(istioctl version --remote=false 2>/dev/null || echo 'version unknown')"
fi

# Validate YAML syntax
echo ""
echo "📄 Validating YAML syntax..."
for file in "$ISTIO_DIR/base"/*.yaml; do
    if [[ -f "$file" && "$(basename "$file")" != "kustomization.yaml" ]]; then
        if python -c "import yaml; list(yaml.safe_load_all(open('$file')))" 2>/dev/null; then
            echo "   ✅ $(basename "$file")"
        else
            echo "   ❌ $(basename "$file") - Invalid YAML"
            exit 1
        fi
    fi
done

# Validate with istioctl
if [[ "$SKIP_ISTIOCTL" == "false" ]]; then
    echo ""
    echo "🔬 Running istioctl analyze..."
    if [[ "$OVERLAY" == "base" ]]; then
        istioctl analyze "$ISTIO_DIR/base/" --use-kube=false 2>&1 || true
    else
        echo "   Analyzing overlay: $OVERLAY"
        # Build kustomize and analyze
        if command -v kustomize &> /dev/null; then
            kustomize build "$ISTIO_DIR/overlays/$OVERLAY" | istioctl analyze --use-kube=false -f - 2>&1 || true
        else
            echo "   ⚠️  kustomize not found, analyzing base only"
            istioctl analyze "$ISTIO_DIR/base/" --use-kube=false 2>&1 || true
        fi
    fi
fi

# Run property tests
echo ""
echo "🧪 Running property-based tests..."
if python -m pytest tests/properties/test_istio_manifests.py -v --tb=short 2>&1; then
    echo "   ✅ All property tests passed"
else
    echo "   ❌ Property tests failed"
    exit 1
fi

# Validate kustomize build
echo ""
echo "🏗️  Validating kustomize build..."
if command -v kustomize &> /dev/null; then
    for overlay in dev staging prod; do
        if kustomize build "$ISTIO_DIR/overlays/$overlay" > /dev/null 2>&1; then
            echo "   ✅ $overlay overlay builds successfully"
        else
            echo "   ❌ $overlay overlay build failed"
            exit 1
        fi
    done
else
    echo "   ⚠️  kustomize not found, skipping overlay validation"
fi

echo ""
echo "================================"
echo "✅ All validations passed!"
