# tests/unit/test_economy.py
import pytest

import pandas as pd

from money import portfolio as pf
from money import annual_returns
from money import economy

@pytest.mark.parametrize("principal, basis, growth, conversion, result, postbasis", [
   (1000, 0.5, 1.0, 0, 2000.0, 0.25),
   (1000, 0.25, 0.25, 0, 1250.0, 0.2),
   # Conversion happens before growth, causes basis to rise.
   (1000, 0.5, 0.25, 1000, 2500.0, 0.6),
   # Money grows to cancel out prior losses, basis should return to 1.0.
   (1000, 1.2, 0.2, 0, 1200.0, 1.0),
   # Basis is entirely withdrawn before growth.
   (1000, 0.5, 0.0, -500, 500.0, 0),
   (1000, 0.5, 1.0, -500, 1000.0, 0),
   # Going back to zero should set basis back to 1.0
   (1000, 0.5, 1.0, -1000, 0.0, 1.0),
])
def test_growth_and_basis(principal, basis, growth, conversion, result, postbasis):
  assert pf.PortfolioProjection.growth_and_basis(principal, basis, growth, conversion) == (result, postbasis)

def test_prepare_new_year():
  econ = economy.EconomicConditions()
  simulated_returns = annual_returns.RandomAnnualStockReturns(years=2, reversion_strength=2)[1]
  start = pf.PortfolioStart()
  folio = pf.PortfolioProjection(portfolio_start = start, annual_returns=simulated_returns)
  initial_year = folio.df.loc[2025]
  prepped_year = folio.df.loc[2026]
  folio.PrepareForNewYear(initial_year, prepped_year)

  assert prepped_year.name == initial_year.name + 1
  for field in ['cash', 'annual_expenses', 'standard_deduction']:
    assert prepped_year.cash == initial_year.cash * (1 + econ.inflation_rate)
  for field in ['pretax', 'value_roth', 'basis_roth', 'value_broker', 'basis_broker',
                'pal_loan', 'inflation_rate']:
    assert prepped_year[field] == initial_year[field]
  for field in ['taxfree_withdraw', 'income', 'capgains']:
    assert prepped_year[field] == 0.0
  pass

def test_grow_iras_migrate():
  simulated_returns = annual_returns.RandomAnnualStockReturns(years=2, reversion_strength=2)[1]
  start = pf.PortfolioStart()
  folio = pf.PortfolioProjection(portfolio_start = start, annual_returns=simulated_returns)
  last_year = folio.df.loc[2025]
  curr_year = folio.df.loc[2026]
  folio.PrepareForNewYear(last_year, curr_year)

  folio.GrowIRAsAndMigrate(curr_year=curr_year, last_year=last_year)
  expected_pretax = (last_year.pretax - curr_year.standard_deduction) * (1 + curr_year.annual_returns)
  assert curr_year.pretax == expected_pretax
  new_roth_value = (last_year.value_roth + curr_year.standard_deduction) * (1 + curr_year.annual_returns)
  assert curr_year.value_roth == new_roth_value
  new_basis_raw = (last_year.value_roth * last_year.basis_roth + curr_year.standard_deduction)
  assert curr_year.basis_roth == new_basis_raw / new_roth_value

def test_grow_stocks():
  simulated_returns = annual_returns.RandomAnnualStockReturns(years=2, reversion_strength=2)[1]
  start = pf.PortfolioStart()
  folio = pf.PortfolioProjection(portfolio_start = start, annual_returns=simulated_returns)
  last_year = folio.df.loc[2025]
  curr_year = folio.df.loc[2026]
  folio.PrepareForNewYear(last_year, curr_year)

  folio.GrowStocks(curr_year=curr_year, last_year=last_year)

  new_broker_value, new_broker_basis = folio.growth_and_basis(last_year.value_broker, last_year.basis_broker, curr_year.annual_returns)
  assert curr_year.value_broker == new_broker_value
  assert curr_year.basis_broker == new_broker_basis

def test_broker_taxfree():
  econ = economy.EconomicConditions()
  taxfree_amount = 10000
  basis = 0.25
  econ.single_capgains_brackets = {0: 0.0, taxfree_amount: 0.1}
  simulated_returns = annual_returns.RandomAnnualStockReturns(years=2, reversion_strength=2)[1]
  start = pf.PortfolioStart()
  folio = pf.PortfolioProjection(portfolio_start = start, annual_returns=simulated_returns, econ=econ)
  last_year = folio.df.loc[2025]
  curr_year = folio.df.loc[2026]
  folio.PrepareForNewYear(last_year, curr_year)
  curr_year.basis_broker = basis

  folio.BrokerageTaxFreeSales(last_year=last_year, curr_year=curr_year)
  assert curr_year.taxfree_withdraw == taxfree_amount / (1.0-basis)

# Every list is a before/after value for the specific test
@pytest.mark.parametrize(
   "expenses, cash,          broker,    bbasis, roth,      rbasis,  tax_threshold", [
   # No expenses -> no change
   (0,        [10, 10],      [10, 10],  [1, 1], [10, 10],  [1, 1],  0),
   # Pay for expenses out of cash, go negative/bankrupt if no balance anywhere.
   (100,      [100, 0],      [0, 0],    [1, 1], [0, 0],    [1, 1],  0),
   (150,      [100, -50],    [0, 0],    [1, 1], [0, 0],    [0, 0],  0),
   # Take money from brokerage if not enough cash.
   (100,      [0, 0],        [100, 0],  [1, 1], [0, 0],    [1, 1],  0),
   (101,      [0, -1],       [100, 0],  [1, 1], [0, 0],    [1, 1],  0),
   # Take money out of cash before anything, and roth basis before brokerage.
   (100,      [90, 0],       [20, 20],  [1, 1], [10, 0],   [1, 1],  0),
   # Take money out of cash before anything, and brokerage before roth earnings.
   (100,      [90, 0],       [20, 10],  [1, 1], [10, 10],  [0, 0],  0),
   # Take money from roth if nothing available in cash/brokerage.
   (100,      [0, 0],        [0, 0],    [1, 1], [100, 0],  [1, 1],  0),
   (101,      [0, -1],       [0, 0],    [1, 1], [100, 0],  [1, 1],  0),
   # Cash is negative here, so it should be added to expenses.
   (100,      [-10, 0],      [0, 0],    [1, 1], [110, 0],  [1, 1],  0),
   # Account for 75% earnings taxation on brokerage/roth
   (100,      [0, 0],        [410, 10], [0, 0], [0, 0],    [1, 1],  0),
   # TODO: implement withdrawal from roth earnings.
   #(100,      [0, 0],        [0, 0],    [1, 1], [500, 100],  [0, 0],  0),
])
def test_pay_expenses(expenses, cash, broker, bbasis, roth, rbasis, tax_threshold):
  econ = economy.EconomicConditions()
  econ.single_capgains_brackets = {tax_threshold:0.75}
  simulated_returns = annual_returns.RandomAnnualStockReturns(years=2, reversion_strength=2)[1]
  start = pf.PortfolioStart()
  folio = pf.PortfolioProjection(portfolio_start = start, annual_returns=simulated_returns, econ=econ)
  last_year = folio.df.loc[2025]
  curr_year = folio.df.loc[2026]
  folio.PrepareForNewYear(last_year, curr_year)
  curr_year.pretax = 0
  expected = curr_year.copy(deep=True)
  
  # Set the before/after state
  curr_year.annual_expenses, expected.annual_expenses = expenses, expenses
  curr_year.cash, expected.cash = cash
  curr_year.value_broker, expected.value_broker = broker
  curr_year.basis_broker, expected.basis_broker = bbasis
  curr_year.value_roth, expected.value_roth = roth
  curr_year.basis_roth, expected.basis_roth = rbasis
  curr_year.taxfree_withdraw, expected.taxfree_withdraw = tax_threshold, tax_threshold

  # Pay for expenses and expect the specified result.
  folio.PayForExpenses(curr_year=curr_year)
  pd.testing.assert_series_equal(curr_year, expected)

  # Running out of cash should be bankruptcy.
  if expected.cash < 0 or folio.bankrupt_year is not None:
    assert expected.cash < 0
    assert folio.bankrupt_year is not None



def test_calculate_income_tax():
    simulated_returns = annual_returns.RandomAnnualStockReturns(years=2, reversion_strength=2)[1]
    pd.set_option('display.float_format', '{:.3f}'.format)


    start = pf.PortfolioStart()
    folio = pf.PortfolioProjection(portfolio_start = start, annual_returns=simulated_returns)
    folio.simulate_portfolio()
    #print(simulated_returns)
    print(folio.df.annual_returns)
    #print(folio.df.annual_returns.loc[2025])
    # print(folio.df.loc[2026])
    # print(folio.df.loc[2027])
    assert folio.df.pretax.loc[2025] != folio.df.pretax.loc[2026]