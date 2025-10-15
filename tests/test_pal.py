# tests/unit/test_economy.py
import pytest
#from money.pal import *
from money import economy
from money import pal

import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

@pytest.mark.parametrize("cpi_start,cpi_end,expected", [
    (100, 103, 0.03),
    (255.0, 260.1, pytest.approx(0.019999, rel=1e-6)),
])
def test_annual_inflation(cpi_start, cpi_end, expected):
    econ = economy.EconomicConditions()
    keys = list(econ.pal_rates.keys())
    assert keys == sorted(keys)

    assert pal.find_pal_multiplier(keys[0], econ) == 1 + econ.pal_rates[keys[0]]
    for i in range(0, len(keys)):

        # Ensure that when you reach a threshold you get that pal rate exactly.
        key = keys[i]
        assert pal.find_pal_multiplier(key, econ) == 1 + econ.pal_rates[key]

        # Ensure that you still get that pal rate up until the next threshold.
        if i < len(keys) - 1:
            next_key = keys[i+1]
            assert pal.find_pal_multiplier(next_key - 1, econ) == 1 + econ.pal_rates[key]