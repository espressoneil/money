# tests/unit/test_economy.py
import pytest
#from money.pal import *

@pytest.mark.parametrize("a,b,sum", [
   (1, 2, 3),
   (1.5, 2.5, 4),
])
def test_addition(a, b, sum):
    assert a + b == sum