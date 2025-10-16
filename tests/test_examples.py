# tests/unit/test_economy.py
import pytest
#from money.pal import *

import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

@pytest.mark.parametrize("a,b,sum", [
   (1, 2, 3),
   (1.5, 2.5, 4),
])
def test_addition(a, b, sum):
    assert a + b == sum