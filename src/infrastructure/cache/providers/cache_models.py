"""Cache models and configuration dataclasses.

**Feature: api-best-practices-review-2025**
**Validates: Requirements 22.1, 22.5, 22.6**

Extracted from redis_jitter.py for better modularity and reusability.
"""

from dataclasses import dataclass


@dataclass
class JitterConfig:
    """Configuration for TTL jitter.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 22.1**
    
    Attributes:
        min_jitter_percent: Minimum jitter as percentage (e.g., 0.05 for 5%).
        max_jitter_percent: Maximum jitter as percentage (e.g., 0.15 for 15%).
        lock_timeout_seconds: Timeout for distributed locks.
        early_recompute_window: Seconds before expiry to consider early recompute.
        early_recompute_probability: Probability of triggering early recompute.
    """

    min_jitter_percent: float = 0.05
    max_jitter_percent: float = 0.15
    lock_timeout_seconds: int = 5
    early_recompute_window: int = 30
    early_recompute_probability: float = 0.1


@dataclass
class TTLPattern:
    """TTL configuration for a key pattern.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 22.5**
    
    Attributes:
        pattern: Key pattern to match (glob-style).
        ttl_seconds: TTL in seconds for matching keys.
        enable_jitter: Whether to apply TTL jitter.
        enable_early_recompute: Whether to enable early recomputation.
    """

    pattern: str
    ttl_seconds: int
    enable_jitter: bool = True
    enable_early_recompute: bool = False


@dataclass
class CacheStats:
    """Statistics for cache operations.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 22.6**
    
    Attributes:
        hits: Number of cache hits.
        misses: Number of cache misses.
        stampede_prevented: Number of cache stampedes prevented.
        early_recomputes: Number of early recomputation triggers.
        jittered_sets: Number of sets with jitter applied.
    """

    hits: int = 0
    misses: int = 0
    stampede_prevented: int = 0
    early_recomputes: int = 0
    jittered_sets: int = 0

    @property
    def hit_ratio(self) -> float:
        """Calculate cache hit ratio.
        
        Returns:
            Hit ratio between 0.0 and 1.0.
        """
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    @property
    def total_requests(self) -> int:
        """Get total number of cache requests."""
        return self.hits + self.misses
