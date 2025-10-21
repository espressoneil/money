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
    self.roth_taxfree_year = 28
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
  def __init__(self, portfolio_start: PortfolioStart, annual_returns):
    # Initialize lists based on the fields of PortfolioStart
    years = annual_returns.shape[0]
    self.years = years
    self.start_year = portfolio_start.start_year
    self.portfolio_start = portfolio_start
    self.annual_returns = np.concatenate(([0], annual_returns))

    self.cash = np.concatenate(([portfolio_start.cash], np.zeros(years)))
    self.pretax = np.concatenate(([portfolio_start.pretax], np.zeros(years)))
    self.value_roth = np.concatenate(([portfolio_start.roth_start], np.zeros(years)))
    self.basis_roth = np.concatenate(([portfolio_start.roth_basis], np.zeros(years)))
    self.value_broker = np.concatenate(([portfolio_start.invest_start], np.zeros(years)))
    self.basis_broker = np.concatenate(([portfolio_start.basis_fraction], np.zeros(years)))
    self.annual_expenses = np.concatenate(([portfolio_start.initial_spend], np.zeros(years)))
    self.standard_deduction = np.concatenate(([portfolio_start.standard_deduction], np.zeros(years)))
    self.value_pal = np.zeros(years+1)
    self.taxfree_withdraw = np.zeros(years+1)
    self.income = np.zeros(years+1)
    self.capgains = np.zeros(years+1)

    
    m = np.stack([
        self.cash,
        self.pretax,
        self.value_roth,
        self.basis_roth,
        self.value_broker,
        self.basis_broker,
        self.annual_expenses,
        self.standard_deduction,
        self.value_pal,
        self.taxfree_withdraw,
        self.income,
        self.capgains,
        self.annual_returns
    ], axis=1)
    self.asset_names = [
        "cash",
        "pretax",
        "value_roth",
        "basis_roth",
        "value_broker",
        "basis_broker",
        "annual_expenses",
        "standard_deduction",
        "value_pal",
        "taxfree_withdraw",
        "income",
        "capgains",
        "annual_returns"
    ]

    years = np.arange(self.start_year, self.start_year + m.shape[0])  # define start_year as needed
    self.df = pd.DataFrame(m, index=years, columns=self.asset_names)

    self.bankrupt = False

  def display(self, year=0):
    # Display values for a specific year (index)
    try:
      print(f"Year {year}:")
      print(f"Cash Value: ${self.cash[year]:,.0f}")
      print(f"Pretax Value: ${self.pretax[year]:,.0f}")
      print(f"Roth Value: ${self.value_roth[year]:,.0f}")
      print(f"Roth Basis: {self.basis_roth[year] * 100:.1f}%")
      print(f"Broker Value: ${self.value_broker[year]:,.0f}")
      print(f"Broker Basis: {self.basis_broker[year] * 100:.1f}%")
      print(f"Pal Value: ${self.value_pal[year]:,.0f}")
      print(f"Annual Expenses: ${self.annual_expenses[year]:,.0f}")

    except IndexError:
      print(f"Data for year {year} is not available.")

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


  def simulate_portfolio(self, econ=economy.EconomicConditions()):
    # Simulate the portfolio over the specified number of years
    for y in range(1, self.years + 1):
      curr_year = self.simulate_year(y, last_year = self.df.loc[self.start_year + y - 1], econ = econ)
      self.df.loc[self.start_year + y] = curr_year
      print(curr_year)
      #print('Year:', y)
    return self.value_broker


  def simulate_year(self, y, last_year, econ=economy.EconomicConditions()):
    annual_returns = self.annual_returns
    #df = self.df
    curr_year = last_year.copy(deep=True)
    print(curr_year)
    #print(last_year)

    curr_year.annual_expenses = last_year.annual_expenses * (1 + econ.inflation_rate);
    # Assume cash on hand is deposited into high yield accounts or bonds
    # TODO: hysa/bonds don't always beat out inflation...
    curr_year.cash = last_year.cash * (1 + econ.inflation_rate)
    curr_year.standard_deduction = last_year.standard_deduction * (1 + econ.inflation_rate);

    # Use up standard deduction to migrate from pretax to roth. Considered income.
    roth_migration = min(curr_year.standard_deduction, last_year.pretax)
    curr_year.pretax = PortfolioProjection.growth_and_basis(last_year.pretax, 1, annual_returns[y], conversion=-roth_migration)[0]
    curr_year.value_roth, curr_year.basis_roth = PortfolioProjection.growth_and_basis(
        last_year.value_roth, last_year.basis_roth, annual_returns[y], conversion=roth_migration
    )
    curr_year.income = roth_migration
    print('roth ', curr_year.value_roth, curr_year.basis_roth, ', pretax ', curr_year.pretax)

    # Calculate how much the brokerage portfolio has grown.
    print('broker0 ', last_year.value_broker, last_year.basis_broker, annual_returns[y], last_year.value_broker * annual_returns[y])
    #prior_basis = last_year.basis_broker
    curr_year.value_broker, curr_year.basis_broker = PortfolioProjection.growth_and_basis(
        last_year.value_broker, last_year.basis_broker, annual_returns[y]
    )
    print('broker2 ', curr_year.value_broker, curr_year.basis_broker)

    # Personal Expenses
    remaining_expenses = last_year.annual_expenses

    # Pay for expenses with brokerage taxfree capital gains and withdrawal.
    # TODO: track capital losses here. 
    curr_year.cash = last_year.cash + taxes.max_taxfree_withdrawal(
        (1 - curr_year.basis_broker), curr_year.value_broker, econ.single_capgains_brackets
    )
    print('broker3 ', curr_year.value_broker, curr_year.basis_broker, econ.single_capgains_brackets, curr_year.cash)
    # TODO: handle capital losses

    #print(cash)
    curr_year.value_broker -= curr_year.taxfree_withdraw
    paid_with_cash = min(curr_year.taxfree_withdraw, remaining_expenses)
    remaining_expenses -= paid_with_cash
    curr_year.cash -= paid_with_cash

    # Pay for expenses from PAL
    pal_loan = 0
    pal_available = 0
    if self.portfolio_start.use_pal and remaining_expenses > 0:
      pal_available = max(0, curr_year.value_broker * self.portfolio_start.pal_cap - last_year.value_pal)
      pal_loan = min(pal_available, remaining_expenses)

      remaining_expenses -= pal_loan
    curr_year.value_pal = pal.future_value_pal(pal_loan, n=1, value=last_year.value_pal)
    print('pal loan:', pal_loan, pal_available, remaining_expenses)

    # Pay for expenses from ROTH basis
    roth_withdrawal = 0
    if remaining_expenses > 0:
      roth_basis = curr_year.basis_roth if self.portfolio_start.roth_taxfree_year > y else 1
      total_roth_basis = curr_year.value_roth * roth_basis
      roth_withdrawal = min(remaining_expenses, total_roth_basis)
      curr_year.value_roth -= roth_withdrawal
      curr_year.basis_roth = (total_roth_basis - roth_withdrawal) / curr_year.value_roth
      remaining_expenses -= roth_withdrawal

    # Pay for expenses from Brokerage
    # UNTESTED
    full_brokerage_withdrawal = 0
    posttax_brokerage_withdrawal = 0

    if remaining_expenses > 0:
      full_broker_funds = curr_year.taxfree_withdraw + remaining_expenses
      full_brokerage_withdrawal = taxes.calculate_withdrawal(
          full_broker_funds, curr_year.value_broker, (1 - curr_year.basis_broker),
          econ.single_capgains_brackets, prior_withdrawals=curr_year.taxfree_withdraw
      )
      #brokerage_withdrawal_taxes = calculate_income_tax(full_brokerage_withdrawal, tax_brackets=econ.single_capgains_brackets, deduction=0)
      brokerage_withdrawal_taxes = taxes.calculate_capgains(
          income=full_brokerage_withdrawal * (1 - curr_year.basis_broker),
          capgains_brackets=econ.single_capgains_brackets
      )

      net_cash = full_brokerage_withdrawal - brokerage_withdrawal_taxes - curr_year.taxfree_withdraw
      # calculate_withdrawal  103842.38301855858 8746.522725101613 95095.86029345696 95094.86029345698
      # taxable brokerage         8  15623.855280730495  15489.294 79471.00501272648         103843      (94961)        8882.699999999999           15489.294987273519
      print('Given a withrawal of', full_brokerage_withdrawal, ' this leads to capgains of ', brokerage_withdrawal_taxes, '. Prior withdrawal was ', curr_year.taxfree_withdraw, ' leaving ', net_cash, ' to pay off expenses. Remaining Expenses are ', remaining_expenses, ' limited by: ', curr_year.value_broker)
      #print('taxable brokerage ', y, remaining_expenses, net_cash, curr_year.taxfree_withdraw, full_brokerage_withdrawal, brokerage_withdrawal_taxes, net_cash)
      additional_withdrawal = full_brokerage_withdrawal - curr_year.taxfree_withdraw
      if additional_withdrawal > 0:
        curr_year.value_broker -= additional_withdrawal
      remaining_expenses -= net_cash
      # taxable brokerage         8  135.4102934569819   15488.44  79471.00501272648         103842 8882.55             15488.444987273513

    print('broker4 ', curr_year.value_broker, curr_year.basis_broker, last_year.value_broker, last_year.basis_broker)

    # Pay for expenses from Roth earnings
    # TODO

    # Pay for expenses from pretax
    # TODO

    # Return any remaining cash to the brokerage account
    # TODO
    if curr_year.cash > 0:
      curr_year.value_broker, curr_year.basis_broker = PortfolioProjection.growth_and_basis(
          curr_year.value_broker, curr_year.basis_broker, 0, conversion=curr_year.cash
      )
      curr_year.cash = 0
    print('broker5 ', curr_year.value_broker, curr_year.basis_broker, )

    #curr_year.value_broker, curr_year.basis_broker = PortfolioProjection.growth_and_basis(curr_year.value_broker, curr_year.basis_broker, growth_rate=0, conversion=remaining_deposit)
    #print(curr_year.value_broker)
    # Calculate how many expenses are being paid from PAL
    # pal_loan = 0
    # withdrawal = 0
    # if self.portfolio_start.use_pal:
    #   pal_available = max(0, curr_year.value_broker * self.portfolio_start.pal_cap - last_year.value_pal)
    #   pal_loan = min(pal_available, remaining_expenses)
    #   curr_year.value_pal = future_value_pal(pal_loan, n=1, value=last_year.value_pal)
    #   #print(curr_year.value_pal)
    #   remaining_expenses -= pal_loan
    #   #print(pal_available, self.portfolio_start.pal_cap)
    # else:
    #   # Calculate the amount you have to withdraw to pay expenses.
    #   #print("Regular Withdrawal")
    #   withdrawal = calculate_withdrawal(remaining_expenses, curr_year.value_broker-1, curr_year.basis_broker, econ.single_capgains_brackets)
    # #print(curr_year.value_broker)
    # # Subtract the annual expense from brokerage money
    # curr_year.value_broker -= withdrawal
    # remaining_expenses -= withdrawal

    # # If expenses aren't satisfied, start withdrawing from roth.
    # roth_withdrawal = 0
    # if remaining_expenses > 0:
    #   # TODO: IMPLEMENT TAXATION

    #   roth_withdrawal = calculate_withdrawal(expenses, curr_year.value_roth, curr_year.basis_roth, econ.single_capgains_brackets)
    #   #print("Roth Withdrawal: ", roth_withdrawal)
    #   #roth_withdrawal = min(expenses, curr_year.value_roth)
    #   curr_year.value_roth -= roth_withdrawal
    #   remaining_expenses -= roth_withdrawal

    if remaining_expenses > 0:
      # Two bugs: Why doesn't the PAL case withdraw from broker?
      # Why isn't the PAL case satisfied by a roth withdrawal?
      # 8 135.4102934569819 79471.00501272648 103842 0.0 1403702.4077441266 327048.4343263615 357141.94833330397
      print('bankrupt:', y, remaining_expenses)
      print('bankrupt withdrawals:', curr_year.taxfree_withdraw, full_brokerage_withdrawal, roth_withdrawal)
      print('bankrupt broker:', curr_year.value_broker, curr_year.basis_broker)
      print('bankrupt roth:', curr_year.value_roth, curr_year.basis_roth)
      print('bankrupt pretax:', curr_year.pretax)
      self.bankrupt = True
      return curr_year
    #print(curr_year.value_broker)
    return curr_year
