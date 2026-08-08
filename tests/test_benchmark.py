# tests/test_benchmark.py
import pytest

from bench import benchmark, bucketed


@pytest.mark.slow
def test_benchmark_keys():
    r = benchmark(frames=300)
    for k in ("total_s", "mean_us", "median_us", "p95_us", "p99_us", "fps"):
        assert k in r
    assert r["mean_us"] > 0


@pytest.mark.slow
def test_bucketed_keys():
    r = bucketed(frames=300)
    for k in ("push_us", "physics_us", "combat_us"):
        assert k in r
