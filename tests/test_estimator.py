import pytest

from estimator import estimate_monthly_cost


def test_sonnet_example_costs_138():
    cost = estimate_monthly_cost("Claude Sonnet 5.5", 1000, 800, 300)
    assert cost == pytest.approx(138)


def test_days_changes_total():
    cost = estimate_monthly_cost("Claude Sonnet 5.5", 1000, 800, 300, days=1)
    assert cost == pytest.approx(4.6)


def test_zero_requests_costs_zero():
    cost = estimate_monthly_cost("Claude Sonnet 5.5", 0, 800, 300)
    assert cost == 0


def test_unknown_model_raises():
    with pytest.raises(ValueError, match="Unknown model"):
        estimate_monthly_cost("GPT-99", 1000, 800, 300)


def test_negative_requests_raises():
    with pytest.raises(ValueError, match="requests_per_day"):
        estimate_monthly_cost("Claude Sonnet 5.5", -1000, 800, 300)
