"""Unit tests for sustainability alerts module."""

from decimal import Decimal

import pytest

from src.infrastructure.sustainability.alerts import (
    generate_alert_rule,
    generate_all_alerts,
    generate_carbon_alert_rule,
    generate_cost_alert_rule,
)
from src.infrastructure.sustainability.models import AlertThreshold


class TestGenerateAlertRule:
    """Tests for generate_alert_rule function."""

    def test_generate_alert_rule_cluster_wide(self) -> None:
        """Test generating cluster-wide alert rule."""
        threshold = AlertThreshold(
            namespace=None,
            deployment=None,
            energy_threshold_kwh=Decimal("100"),
            carbon_threshold_gco2=Decimal("40000"),
            cost_threshold=Decimal("12"),
            severity="warning",
        )

        rule = generate_alert_rule(threshold)

        assert rule.name == "sustainability_energy_threshold_cluster_warning"
        assert "kepler_container_joules_total" in rule.expr
        assert "> 100" in rule.expr
        assert rule.duration == "5m"
        assert rule.severity == "warning"
        assert "summary" in rule.annotations
        assert "description" in rule.annotations
        assert rule.labels["team"] == "platform"

    def test_generate_alert_rule_namespace_scoped(self) -> None:
        """Test generating namespace-scoped alert rule."""
        threshold = AlertThreshold(
            namespace="production",
            deployment=None,
            energy_threshold_kwh=Decimal("50"),
            carbon_threshold_gco2=Decimal("20000"),
            cost_threshold=Decimal("6"),
            severity="critical",
        )

        rule = generate_alert_rule(threshold)

        assert rule.name == "sustainability_energy_threshold_namespace_production_critical"
        assert 'namespace="production"' in rule.expr
        assert "> 50" in rule.expr
        assert rule.severity == "critical"


    def test_generate_alert_rule_deployment_scoped(self) -> None:
        """Test generating deployment-scoped alert rule."""
        threshold = AlertThreshold(
            namespace="production",
            deployment="api-server",
            energy_threshold_kwh=Decimal("25"),
            carbon_threshold_gco2=Decimal("10000"),
            cost_threshold=Decimal("3"),
            severity="warning",
        )

        rule = generate_alert_rule(threshold)

        assert rule.name == "sustainability_energy_threshold_deployment_api-server_warning"
        assert 'namespace="production"' in rule.expr
        assert 'deployment="api-server"' in rule.expr
        assert "> 25" in rule.expr


class TestGenerateCarbonAlertRule:
    """Tests for generate_carbon_alert_rule function."""

    def test_generate_carbon_alert_cluster_wide(self) -> None:
        """Test generating cluster-wide carbon alert."""
        threshold = AlertThreshold(
            namespace=None,
            deployment=None,
            energy_threshold_kwh=Decimal("100"),
            carbon_threshold_gco2=Decimal("40000"),
            cost_threshold=Decimal("12"),
            severity="warning",
        )

        rule = generate_carbon_alert_rule(threshold)

        assert rule.name == "sustainability_carbon_threshold_cluster_warning"
        assert "* 400" in rule.expr  # Carbon intensity factor
        assert "> 40000" in rule.expr
        assert "Carbon emissions" in rule.annotations["summary"]

    def test_generate_carbon_alert_namespace_scoped(self) -> None:
        """Test generating namespace-scoped carbon alert."""
        threshold = AlertThreshold(
            namespace="staging",
            deployment=None,
            energy_threshold_kwh=Decimal("50"),
            carbon_threshold_gco2=Decimal("20000"),
            cost_threshold=Decimal("6"),
            severity="critical",
        )

        rule = generate_carbon_alert_rule(threshold)

        assert "namespace_staging" in rule.name
        assert 'namespace="staging"' in rule.expr
        assert rule.severity == "critical"


class TestGenerateCostAlertRule:
    """Tests for generate_cost_alert_rule function."""

    def test_generate_cost_alert_cluster_wide(self) -> None:
        """Test generating cluster-wide cost alert."""
        threshold = AlertThreshold(
            namespace=None,
            deployment=None,
            energy_threshold_kwh=Decimal("100"),
            carbon_threshold_gco2=Decimal("40000"),
            cost_threshold=Decimal("12"),
            severity="warning",
        )

        rule = generate_cost_alert_rule(threshold, Decimal("0.12"))

        assert rule.name == "sustainability_cost_threshold_cluster_warning"
        assert "* 0.12" in rule.expr  # Price per kWh
        assert "> 12" in rule.expr
        assert "$12" in rule.annotations["summary"]

    def test_generate_cost_alert_with_custom_price(self) -> None:
        """Test generating cost alert with custom price."""
        threshold = AlertThreshold(
            namespace="production",
            deployment=None,
            energy_threshold_kwh=Decimal("100"),
            carbon_threshold_gco2=Decimal("40000"),
            cost_threshold=Decimal("20"),
            severity="critical",
        )

        rule = generate_cost_alert_rule(threshold, Decimal("0.25"))

        assert "* 0.25" in rule.expr
        assert "> 20" in rule.expr


class TestGenerateAllAlerts:
    """Tests for generate_all_alerts function."""

    def test_generate_all_alerts_returns_three_rules(self) -> None:
        """Test that generate_all_alerts returns all three alert types."""
        threshold = AlertThreshold(
            namespace="production",
            deployment=None,
            energy_threshold_kwh=Decimal("100"),
            carbon_threshold_gco2=Decimal("40000"),
            cost_threshold=Decimal("12"),
            severity="warning",
        )

        rules = generate_all_alerts(threshold)

        assert len(rules) == 3
        names = [r.name for r in rules]
        assert any("energy" in n for n in names)
        assert any("carbon" in n for n in names)
        assert any("cost" in n for n in names)

    def test_generate_all_alerts_with_custom_price(self) -> None:
        """Test generate_all_alerts with custom price."""
        threshold = AlertThreshold(
            namespace=None,
            deployment=None,
            energy_threshold_kwh=Decimal("50"),
            carbon_threshold_gco2=Decimal("20000"),
            cost_threshold=Decimal("10"),
            severity="critical",
        )

        rules = generate_all_alerts(threshold, Decimal("0.20"))

        cost_rule = next(r for r in rules if "cost" in r.name)
        assert "* 0.20" in cost_rule.expr

    def test_generate_all_alerts_all_have_same_severity(self) -> None:
        """Test that all generated alerts have the same severity."""
        threshold = AlertThreshold(
            namespace="test",
            deployment=None,
            energy_threshold_kwh=Decimal("100"),
            carbon_threshold_gco2=Decimal("40000"),
            cost_threshold=Decimal("12"),
            severity="critical",
        )

        rules = generate_all_alerts(threshold)

        for rule in rules:
            assert rule.severity == "critical"
