"""
Tests for serialization and timeframe normalization.

Covers:
- Timeframe alias normalization
- Relative timestamp computation
- Streaming cache behavior (bounded, non-blocking)
"""

from __future__ import annotations

import pytest

from ctrader_mcp_server.tools.market_data import (
    _normalize_timeframe,
    _relative_start,
)
from ctrader_mcp_server.session import StreamingCache


class TestTimeframeNormalization:
    """Tests for timeframe alias normalization."""

    def test_standard_timeframes(self):
        assert _normalize_timeframe("M1") == "M1"
        assert _normalize_timeframe("M5") == "M5"
        assert _normalize_timeframe("H1") == "H1"
        assert _normalize_timeframe("D1") == "D1"

    def test_case_insensitive(self):
        assert _normalize_timeframe("m1") == "M1"
        assert _normalize_timeframe("h4") == "H4"
        assert _normalize_timeframe("d1") == "D1"

    def test_whitespace_handling(self):
        assert _normalize_timeframe("  M5  ") == "M5"

    def test_custom_numeric_timeframes(self):
        assert _normalize_timeframe("2m") == "2M"
        assert _normalize_timeframe("3h") == "3H"

    def test_unknown_passthrough(self):
        assert _normalize_timeframe("UNKNOWN") == "UNKNOWN"


class TestRelativeStart:
    """Tests for relative timestamp computation."""

    def test_zero_returns_zero(self):
        assert _relative_start(0, 0, 0) == 0

    def test_days_lookback(self):
        import time
        now = int(time.time())
        result = _relative_start(days=1)
        assert result > 0
        # Should be approximately now - 24 hours (with some tolerance)
        expected = now - 24 * 3600
        assert abs(result - expected) < 5  # Within 5 seconds

    def test_hours_lookback(self):
        import time
        now = int(time.time())
        result = _relative_start(hours=2)
        assert result > 0
        expected = now - 2 * 3600
        assert abs(result - expected) < 5

    def test_minutes_lookback(self):
        import time
        now = int(time.time())
        result = _relative_start(minutes=30)
        assert result > 0
        expected = now - 30 * 60
        assert abs(result - expected) < 5


class TestStreamingCache:
    """Tests for the bounded streaming event cache."""

    def test_add_and_poll_spots(self):
        cache = StreamingCache(max_size=10)
        cache.add_spot("1", {"bid": 1.1, "ask": 1.2})
        cache.add_spot("1", {"bid": 1.11, "ask": 1.21})

        events = cache.poll_spots("1")
        assert len(events) == 2
        assert events[0]["bid"] == 1.1
        assert events[1]["bid"] == 1.11

    def test_poll_clears_cache(self):
        cache = StreamingCache(max_size=10)
        cache.add_spot("1", {"bid": 1.1})

        # First poll returns the event
        events = cache.poll_spots("1")
        assert len(events) == 1

        # Second poll returns empty (cache cleared)
        events = cache.poll_spots("1")
        assert len(events) == 0

    def test_bounded_cache(self):
        cache = StreamingCache(max_size=3)
        for i in range(10):
            cache.add_spot("1", {"bid": i})

        events = cache.poll_spots("1")
        assert len(events) == 3
        # Should keep the most recent 3
        assert events[-1]["bid"] == 9

    def test_poll_nonexistent_symbol(self):
        cache = StreamingCache()
        events = cache.poll_spots("999")
        assert events == []

    def test_clear_all(self):
        cache = StreamingCache()
        cache.add_spot("1", {"bid": 1.0})
        cache.add_trendbar("2", {"open": 1.0})
        cache.add_depth("3", {"price": 1.0})

        cache.clear()
        assert cache.poll_spots("1") == []
        assert cache.poll_trendbars("2") == []
        assert cache.poll_depth("3") == []

    def test_separate_symbol_isolation(self):
        cache = StreamingCache()
        cache.add_spot("1", {"bid": 1.0})
        cache.add_spot("2", {"bid": 2.0})

        events_1 = cache.poll_spots("1")
        events_2 = cache.poll_spots("2")
        assert len(events_1) == 1
        assert len(events_2) == 1
        assert events_1[0]["bid"] == 1.0
        assert events_2[0]["bid"] == 2.0
