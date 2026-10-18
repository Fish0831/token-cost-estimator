import pytest

from estimator import compare_models, estimate_monthly_cost


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


def test_compare_sorts_cheapest_first():
    results = compare_models(1000, 800, 300)
    assert len(results) == 5
    assert results[0][0] == "Claude Haiku 5.5"
    assert results[-1][0] == "GPT-5.6 Terra"
