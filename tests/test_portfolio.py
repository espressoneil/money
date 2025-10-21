# tests/unit/test_economy.py
import pytest

import pandas as pd

from money import portfolio
from money import annual_returns

# @pytest.mark.parametrize("income, deduction, tax", [
#    (0, 0, 0),
#    (0, 5000, 0),
#    (6000, 5000, 100),
#    (10000, 0, 1000),
#    (10000, 5000, 500),
#    (15000, 5000, 1000),
#    (50000, 0, 1000 + 8000),
#    (50000, 10000, 1000 + 6000),
#    (50000, 20000, 1000 + 4000),
#    (100000, 0, 1000 + 18000),
#    (100001, 0, 1000 + 18000 + 0.3),
#    (200000, 0, 1000 + 18000 + 30000),
#    (2000000, 0, 1000 + 18000 + 270000 + 400000)
# ])
def test_calculate_income_tax():
    simulated_returns = annual_returns.RandomAnnualStockReturns(years=2, reversion_strength=2)[1]
    pd.set_option('display.float_format', '{:.0f}'.format)


    start = portfolio.PortfolioStart()
    folio = portfolio.PortfolioProjection(portfolio_start = start, annual_returns=simulated_returns)
    folio.simulate_portfolio()
    print(folio.df.loc[2025])
    print(folio.df.loc[2026])
    print(folio.df.loc[2027])
    #print(folio.df.loc[2025])
    assert folio.pretax[0] != folio.pretax[1]