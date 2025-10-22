from numpy import Infinity
from money import taxes


test_brackets = {
    0: 0.1,
    10000: 0.2,
    100000: 0.3,
    1000000: 0.4,
}

# tests/unit/test_economy.py
import pytest

@pytest.mark.parametrize("income, deduction, tax", [
   (0, 0, 0),
   (0, 5000, 0),
   (6000, 5000, 100),
   (10000, 0, 1000),
   (10000, 5000, 500),
   (15000, 5000, 1000),
   (50000, 0, 1000 + 8000),
   (50000, 10000, 1000 + 6000),
   (50000, 20000, 1000 + 4000),
   (100000, 0, 1000 + 18000),
   (100001, 0, 1000 + 18000 + 0.3),
   (200000, 0, 1000 + 18000 + 30000),
   (2000000, 0, 1000 + 18000 + 270000 + 400000)
])
def test_calculate_income_tax(income, deduction, tax):
    assert taxes.calculate_income_tax(income, test_brackets, deduction) == tax

    # Ensure that the same holds for capgains, but without deduction.
    assert taxes.calculate_capgains(income-deduction, test_brackets) == tax

# TODO: rewrite calculate_withdrawal with a deterministic approach and write a test here.
@pytest.mark.parametrize("target, available, gains_fraction, prior_withdrawals, expected", [
   # The taxrate specified above is 10%, so use that in the divisor to find the total.
   (100, 1000, 1, 0, 100/0.9),
   (100, 1000, 0.5, 0, 100/0.95),

   # The withdrawal is capped by the available funds.
   (100, 102, 0.5, 0, 102),

   # We already withdrew 10000 earlier, so use the higher 0.2 bracket that starts at 10000.
   (100, 1000, 1, 10000, 100/0.8),
   (100, 1000, 0.5, 10000, 100/0.9),
   (100, 1000, 0.25, 10000, 100/0.95),

   # We already withdrew 20000 earlier, so use the higher 0.2 bracket that starts at 10000.
   # This verifies that the implementation doesn't glitch out at high prior withdrawal values.
   (100, 1000, 1, 20000, 100/0.8),
   (100, 1000, 0.5, 20000, 100/0.9),

   # Try out the other brackets and inbetween values for exhaustive coverage.
   (100, 1000, 1, 1e5, 100/0.7),
   (100, 1000, 0.5, 1e5, 100/0.85),
   (100, 1000, 1, 2e5, 100/0.7),
   (100, 1000, 0.5, 2e5, 100/0.85),
   (100, 1000, 1, 1e6, 100/0.6),
   (100, 1000, 0.5, 1e6, 100/0.8),
   (100, 1000, 1, 2e6, 100/0.6),
   (100, 1000, 0.5, 2e6, 100/0.8),
])
def test_calculate_withdrawal(target, available, gains_fraction, prior_withdrawals, expected):
  assert taxes.calculate_withdrawal(target, available, gains_fraction, test_brackets, prior_withdrawals) == expected


@pytest.mark.parametrize("earnings, basis_frac, expected", [
   (100, 0.5, 200),
   (100, 0.4, 250),
   (100, 0.1, 1000),
])
def test_earnings_to_total(earnings, basis_frac, expected):
    assert taxes.earnings_to_total(earnings, basis_frac) == expected

@pytest.mark.parametrize("earnings, basis_frac", [
   (0, 0),
   (5, 0),
])
def test_earnings_to_total_div_zero(earnings, basis_frac):
    with pytest.raises(Exception, match="Basis cannot be 0"):
        taxes.earnings_to_total(earnings, basis_frac)