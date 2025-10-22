import numpy as np
import pandas as pd
from . import economy
from . import taxes
from . import pal

# Portfolio Start
class PortfolioStart:
  def __init__(self):
    self.start_year = 2025
    self.pretax = 545_000
    self.cash = 226_000
    self.roth_start = 275_000
    self.roth_basis = 0.8
    self.roth_taxfree_year = 2052
    self.invest_start = 1_966_000
    self.initial_spend = 80_000
    self.basis_fraction = 0.5
    self.standard_deduction = 14600

    self.use_pal = False
    self.pal_cap = 0.3
    self.pal_capped_behavior = 'roth'

    self.first_bracket_expenses = 11600 # hardcoded to the first graduation on the single income tax bracket

  def display(self):
    # Display the portfolio's starting values
    print(f"Start pretax: ${self.pretax:,.0f}")
    print(f"Start cash: ${self.cash:,.0f}")
    print(f"Roth Start: ${self.roth_start:,.0f}")
    print(f"Roth Basis: {self.roth_basis * 100:.1f}%")
    print(f"Investment Start: ${self.invest_start:,.0f}")
    print(f"Initial Spend: ${self.initial_spend:,.0f}")
    print(f"Basis Fraction: {self.basis_fraction * 100:.1f}%")


class PortfolioProjection:
  def __init__(self, portfolio_start: PortfolioStart, annual_returns, econ = economy.EconomicConditions()):
    # Initialize lists based on the fields of PortfolioStart
    years = annual_returns.shape[0]
    self.years = years
    self.start_year = portfolio_start.start_year
    self.portfolio_start = portfolio_start
    self.econ = econ
    

    cash = np.concatenate(([portfolio_start.cash], np.zeros(years)))
    pretax = np.concatenate(([portfolio_start.pretax], np.zeros(years)))
    value_roth = np.concatenate(([portfolio_start.roth_start], np.zeros(years)))
    basis_roth = np.concatenate(([portfolio_start.roth_basis], np.zeros(years)))
    value_broker = np.concatenate(([portfolio_start.invest_start], np.zeros(years)))
    basis_broker = np.concatenate(([portfolio_start.basis_fraction], np.zeros(years)))
    annual_expenses = np.concatenate(([portfolio_start.initial_spend], np.zeros(years)))
    standard_deduction = np.concatenate(([portfolio_start.standard_deduction], np.zeros(years)))
    pal_loan = np.zeros(years + 1)
    taxfree_withdraw = np.zeros(years + 1)
    income = np.zeros(years + 1)
    capgains = np.zeros(years + 1)
    annual_returns = np.concatenate(([0], annual_returns))
    print(annual_returns)
    inflation_rate = np.full(years + 1, self.econ.inflation_rate)

    m = np.stack([
        cash,
        pretax,
        value_roth,
        basis_roth,
        value_broker,
        basis_broker,
        annual_expenses,
        standard_deduction,
        pal_loan,
        taxfree_withdraw,
        income,
        capgains,
        annual_returns,
        inflation_rate,
    ], axis=1)
    

    years = np.arange(self.start_year, self.start_year + m.shape[0])  # define start_year as needed
    self.df = pd.DataFrame(m, index=years, columns=self.asset_names())
    print(self.df.annual_returns)
    self.bankrupt_year = None

  def display(self, year=0):
    print(self.df.loc[year])

  @staticmethod
  def asset_names():
    return [
        "cash",
        "pretax",
        "value_roth",
        "basis_roth",
        "value_broker",
        "basis_broker",
        "annual_expenses",
        "standard_deduction",
        "pal_loan",
        "taxfree_withdraw",
        "income",
        "capgains",
        "annual_returns",
        "inflation_rate",
    ]

  @staticmethod
  def growth_and_basis(value, basis_frac, growth_rate, conversion=0):
    postconversion = value + conversion
    postconversion_basis = max(0, (value * basis_frac) + conversion)
    earnings = postconversion * growth_rate
    if (postconversion + earnings == 0):
      return 0.0, 1.0
    # Conversion and whatever was already in the basis are the basis.
    new_basis = max(0, (postconversion_basis) / (postconversion + earnings))
    #print('growth and basis ', earnings, new_basis, value, growth_rate)

    return postconversion+earnings, new_basis


  def simulate_portfolio(self):
    # Simulate the portfolio over the specified number of years
    for y in range(1, self.years + 1):
      last_year = self.df.loc[self.start_year + y - 1]
      #curr_year = self.df.loc[self.start_year + y]
      curr_year = self.PrepareForNewYear(last_year, curr_year = self.df.loc[self.start_year + y])
      self.simulate_year(curr_year = curr_year)
      # The only field we don't want to copy from last year is the annual returns.
      curr_year.annual_returns = self.df.loc[self.start_year + y].annual_returns
      self.df.loc[self.start_year + y] = curr_year
      if self.bankrupt_year:
        print('bankrupt curr_year:', curr_year)
        print('bankrupt last_year:', last_year)
        return self.df.value_broker
      #print(curr_year)
      #print('Year:', y)
    return self.df.value_broker

  def simulate_year(self, curr_year):
    self.GrowIRAsAndMigrate(curr_year)

    # Calculate how much the brokerage portfolio has grown.
    self.GrowStocks(curr_year)

    # Sell as many stocks in the brokerage tax-free as possible.
    self.BrokerageTaxFreeSales(curr_year)

    # Personal Expenses
    self.PayForExpenses(curr_year)

    # Deposit excess cash
    if curr_year.cash > curr_year.annual_expenses:
      to_deposit = curr_year.cash - curr_year.annual_expenses
      curr_year.value_broker, curr_year.basis_broker = PortfolioProjection.growth_and_basis(
          curr_year.value_broker, curr_year.basis_broker, 0, conversion=to_deposit
      )
      curr_year.cash -= to_deposit
    #print('broker5 ', curr_year.value_broker, curr_year.basis_broker, )

    return curr_year


  def PrepareForNewYear(self, last_year, curr_year):
    for field in ["cash", "pretax", "value_roth", "basis_roth",
                  "value_broker", "basis_broker", "annual_expenses",
                  "standard_deduction", "pal_loan"]:
      curr_year[field] = last_year[field]
    #curr_year = last_year.copy(deep=True)
    curr_year.name = last_year.name + 1
    #print(curr_year)
    #print(last_year)

    curr_year.annual_expenses = last_year.annual_expenses * (1 + self.econ.inflation_rate)
    # Assume cash on hand is deposited into high yield accounts or bonds
    # TODO: hysa/bonds don't always beat out inflation...
    curr_year.cash = last_year.cash * (1 + self.econ.inflation_rate)
    curr_year.standard_deduction = last_year.standard_deduction * (1 + self.econ.inflation_rate)
    curr_year.taxfree_withdraw = 0

    if curr_year.pal_loan > 0:
      curr_year.pal_loan = pal.future_value_pal(0, n=1, econ=self.econ, value=last_year.pal_loan)


    return curr_year

  def GrowIRAsAndMigrate(self, curr_year):
    # Use up standard deduction to migrate from pretax to roth. Considered income.
    #print(curr_year)
    #print(last_year)
    roth_migration = min(curr_year.standard_deduction, curr_year.pretax)
    curr_year.pretax = PortfolioProjection.growth_and_basis(curr_year.pretax, 1, curr_year.annual_returns, conversion=-roth_migration)[0]
    curr_year.value_roth, curr_year.basis_roth = PortfolioProjection.growth_and_basis(
        curr_year.value_roth, curr_year.basis_roth, curr_year.annual_returns, conversion=roth_migration
    )
    curr_year.income = roth_migration
    #print('roth ', curr_year.value_roth, curr_year.basis_roth, ', pretax ', curr_year.pretax)


    

  def GrowStocks(self, curr_year):
    #print('broker0 ', last_year.value_broker, last_year.basis_broker, curr_year.annual_returns, last_year.value_broker * curr_year.annual_returns)
    curr_year.value_broker, curr_year.basis_broker = PortfolioProjection.growth_and_basis(
        curr_year.value_broker, curr_year.basis_broker, curr_year.annual_returns, conversion=0
    )
    print('broker2 ', curr_year.value_broker, curr_year.basis_broker)

  def BrokerageTaxFreeSales(self, curr_year):
    # TODO: track capital losses here. 
    curr_year.taxfree_withdraw = taxes.max_taxfree_withdrawal(
        (1 - curr_year.basis_broker), curr_year.value_broker, self.econ.single_capgains_brackets
    )
    curr_year.cash = curr_year.cash + curr_year.taxfree_withdraw
    # TODO: track capital losses
    curr_year.value_broker, curr_year.basis_broker = PortfolioProjection.growth_and_basis(
        value=curr_year.value_broker, basis_frac = curr_year.basis_broker,
        growth_rate=0, conversion = -curr_year.taxfree_withdraw
    )

    #print('broker3 ', curr_year.value_broker, curr_year.basis_broker, self.econ.single_capgains_brackets, curr_year.cash)
    


  def PayForExpenses(self, curr_year):
    remaining_expenses = curr_year.annual_expenses

    # Pay for expenses with loose cash first.
    # If cash is negative for some reason, add it into it expenses.
    cash_payment = min(remaining_expenses, curr_year.cash)
    remaining_expenses -= cash_payment
    curr_year.cash -= cash_payment

    if remaining_expenses <= 0:
      return

    # Pay for expenses from PAL (if configured to do so)
    if self.portfolio_start.use_pal:
      pal_available = max(0, curr_year.value_broker * self.portfolio_start.pal_cap - curr_year.pal_loan)
      pal_loan = min(pal_available, remaining_expenses)

      remaining_expenses -= pal_loan
      curr_year.pal_loan = pal.future_value_pal(pal_loan, n=0, value=curr_year.pal_loan)
      #print('additional pal loan to pay expenses:', pal_loan, ' from avail ', pal_available, ' with remaining expenses ',  remaining_expenses)

    if remaining_expenses <= 0:
      return

    # Pay for expenses from ROTH basis
    roth_withdrawal = 0
    if curr_year.value_roth > 0:
      roth_basis = curr_year.basis_roth if self.portfolio_start.roth_taxfree_year > curr_year.name else 1
      #print(roth_basis)
      total_roth_basis = curr_year.value_roth * roth_basis
      #print(total_roth_basis)
      roth_withdrawal = min(remaining_expenses, total_roth_basis)
      curr_year.value_roth, curr_year.basis_roth = self.growth_and_basis(
        curr_year.value_roth, basis_frac = roth_basis,
        growth_rate = 0, conversion=-roth_withdrawal)
      #print(curr_year)

      remaining_expenses -= roth_withdrawal

    
    full_brokerage_withdrawal = 0

    if remaining_expenses <= 0:
      return

    # Pay for expenses from Brokerage
    # UNTESTED
    full_broker_funds = curr_year.taxfree_withdraw + remaining_expenses
    # We estimate the total amount, given taxes, that we will need to withdraw this year.
    # We later subtract out the part that was already withdrawn.
    full_brokerage_withdrawal = taxes.calculate_withdrawal(
        full_broker_funds, curr_year.value_broker, (1 - curr_year.basis_broker),
        self.econ.single_capgains_brackets, prior_withdrawals=curr_year.taxfree_withdraw
    )
    #brokerage_withdrawal_taxes = calculate_income_tax(full_brokerage_withdrawal, tax_brackets=econ.single_capgains_brackets, deduction=0)
    brokerage_withdrawal_taxes = taxes.calculate_capgains(
        income=full_brokerage_withdrawal * (1 - curr_year.basis_broker),
        capgains_brackets=self.econ.single_capgains_brackets
    )

    # Subtract out the taxes and the already-happened taxfree withdrawal.
    net_cash = full_brokerage_withdrawal - brokerage_withdrawal_taxes - curr_year.taxfree_withdraw
    # calculate_withdrawal  103842.38301855858 8746.522725101613 95095.86029345696 95094.86029345698
    # taxable brokerage         8  15623.855280730495  15489.294 79471.00501272648         103843      (94961)        8882.699999999999           15489.294987273519
    #print('Given a withrawal of', full_brokerage_withdrawal, ' this leads to capgains of ', brokerage_withdrawal_taxes, '. Prior withdrawal was ', curr_year.taxfree_withdraw, ' leaving ', net_cash, ' to pay off expenses. Remaining Expenses are ', remaining_expenses, ' limited by: ', curr_year.value_broker)
    #print('taxable brokerage ', y, remaining_expenses, net_cash, curr_year.taxfree_withdraw, full_brokerage_withdrawal, brokerage_withdrawal_taxes, net_cash)
    additional_withdrawal = full_brokerage_withdrawal - curr_year.taxfree_withdraw
    if additional_withdrawal > 0:
      curr_year.value_broker -= additional_withdrawal
    remaining_expenses -= net_cash
    # taxable brokerage         8  135.4102934569819   15488.44  79471.00501272648         103842 8882.55             15488.444987273513

    #print('broker4 ', curr_year.value_broker, curr_year.basis_broker)
    
    if remaining_expenses <= 0:
      return
    
    # Pay for expenses from Roth earnings
    # TODO

    if remaining_expenses <= 0:
      return

    # Pay for expenses from pretax
    # TODO

    if remaining_expenses <= 0:
      return


    # This should now be negative
    curr_year.cash -= remaining_expenses
    self.bankrupt_year = curr_year.name

    # Two bugs: Why doesn't the PAL case withdraw from broker?
    # Why isn't the PAL case satisfied by a roth withdrawal?
    print('bankrupt last payments:', cash_payment, full_brokerage_withdrawal, roth_withdrawal)
    

    return
