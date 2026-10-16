import pytest

from estimator import estimate_monthly_cost


def test_sonnet_example_costs_138():
    cost = estimate_monthly_cost("Claude Sonnet 5.5", 1000, 800, 300)
    assert cost == pytest.approx(138)
