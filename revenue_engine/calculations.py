"""Pure financial functions; annual rates are fractions, e.g. 0.01 = 1%."""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import TypedDict

from .contracts import ImpactDirection

CENT = Decimal("0.01")
PERIODS_PER_YEAR = {"annual": 1, "quarterly": 4, "monthly": 12}


class FeeComparison(TypedDict):
    annual_difference: Decimal
    impact_direction: ImpactDirection


def decimal_value(value) -> Decimal:
    """Convert through text to avoid importing binary floating-point error."""
    if isinstance(value, bool):
        raise ValueError("Financial values cannot be booleans")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Invalid financial value") from exc
    if not result.is_finite():
        raise ValueError("Financial values must be finite")
    return result


def money(value) -> Decimal:
    return decimal_value(value).quantize(CENT, rounding=ROUND_HALF_UP)


def calculate_expected_fee(aum, annual_rate, *, excluded_assets=0) -> Decimal:
    """Calculate a flat annual fee on the explicitly billable assets.

    Excluded assets here are excluded from billing, not just tier qualification.
    Tiered pricing is reserved for the next engine milestone.
    """
    assets = decimal_value(aum)
    excluded = decimal_value(excluded_assets)
    rate = decimal_value(annual_rate)
    if assets < 0 or not Decimal(0) <= excluded <= assets:
        raise ValueError("AUM and exclusions must define a nonnegative billable balance")
    if not Decimal(0) <= rate <= Decimal(1):
        raise ValueError("Annual rate must be a fraction between 0 and 1")
    return money((assets - excluded) * rate)


def calculate_actual_fee(aum, annual_rate) -> Decimal:
    """Annualize a flat billing configuration when no posted fee is available."""
    return calculate_expected_fee(aum, annual_rate)


def annualize_impact(period_amount, billing_frequency: str) -> Decimal:
    """Recurring run-rate estimate; not a claim of realized annual charges."""
    if billing_frequency not in PERIODS_PER_YEAR:
        raise ValueError("Billing frequency must be annual, quarterly or monthly")
    return money(decimal_value(period_amount) * PERIODS_PER_YEAR[billing_frequency])


def compare_expected_vs_actual(expected_annual_fee, actual_annual_fee) -> FeeComparison:
    expected = money(expected_annual_fee)
    actual = money(actual_annual_fee)
    if expected < 0 or actual < 0:
        raise ValueError("Fees must be nonnegative")
    signed_difference = expected - actual
    direction: ImpactDirection = "no_discrepancy"
    if signed_difference > 0:
        direction = "potential_underbilling"
    elif signed_difference < 0:
        direction = "potential_overbilling"
    return {"annual_difference": abs(signed_difference), "impact_direction": direction}
