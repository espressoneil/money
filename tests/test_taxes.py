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