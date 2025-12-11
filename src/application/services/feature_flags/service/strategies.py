"""Feature flag evaluation strategies.

DEPRECATED: Import directly from application.services.feature_flags.strategies

This module exists only for backward compatibility.
All strategy classes are now in the strategies/ submodule.

**Feature: application-layer-improvements-2025**
"""

# Re-export for backward compatibility only
from application.services.feature_flags.strategies import (
    CustomRuleStrategy,
    DefaultValueStrategy,
    DisabledStrategy,
    EnabledStrategy,
    EvaluationStrategy,
    FlagEvaluationResult,
    GroupTargetingStrategy,
    PercentageRolloutStrategy,
    StrategyChain,
    UserTargetingStrategy,
    create_default_strategy_chain,
)

__all__ = [
    "CustomRuleStrategy",
    "DefaultValueStrategy",
    "DisabledStrategy",
    "EnabledStrategy",
    "EvaluationStrategy",
    "FlagEvaluationResult",
    "GroupTargetingStrategy",
    "PercentageRolloutStrategy",
    "StrategyChain",
    "UserTargetingStrategy",
    "create_default_strategy_chain",
]
