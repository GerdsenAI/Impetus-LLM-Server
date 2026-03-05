"""
Request latency percentile calculator for performance monitoring.
"""

from collections import deque


class MetricsCalculator:
    """Tracks request latencies and computes p50/p95/p99 percentiles."""

    def __init__(self, maxlen: int = 1000):
        self._latencies: deque[float] = deque(maxlen=maxlen)

    def record(self, latency_ms: float) -> None:
        """Record a request latency in milliseconds."""
        self._latencies.append(latency_ms)

    @property
    def count(self) -> int:
        """Number of recorded latencies."""
        return len(self._latencies)

    def _percentile(self, pct: float) -> float:
        """Compute a percentile from the current latency window."""
        if not self._latencies:
            return 0.0
        sorted_vals = sorted(self._latencies)
        idx = int(pct / 100.0 * (len(sorted_vals) - 1))
        return sorted_vals[idx]

    @property
    def p50(self) -> float:
        """50th percentile (median) latency in ms."""
        return self._percentile(50)

    @property
    def p95(self) -> float:
        """95th percentile latency in ms."""
        return self._percentile(95)

    @property
    def p99(self) -> float:
        """99th percentile latency in ms."""
        return self._percentile(99)

    def reset(self) -> None:
        """Clear all recorded latencies."""
        self._latencies.clear()


# Singleton instance
metrics_calculator = MetricsCalculator()
