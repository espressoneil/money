import numpy as np

# Portfolio Start
class PortfolioStart:
  def __init__(self):
    self.start_401k = 400_000
    self.roth_start = 200_000
    self.roth_basis = 0.8
    self.roth_taxfree_year = 28
    self.invest_start = 1_600_000
    self.initial_spend = 60_000
    self.basis_fraction = 0.5

    self.use_pal = False
    self.pal_cap = 0.3
    self.pal_capped_behavior = 'roth'

    self.first_bracket_expenses = 11600 # hardcoded to the first graduation on the single income tax bracket

  def display(self):
    # Display the portfolio's starting values
    print(f"Start 401k: ${self.start_401k:,.0f}")
    print(f"401k Basis: {self.basis_401k * 100:.1f}%")
    print(f"Roth Start: ${self.roth_start:,.0f}")
    print(f"Roth Basis: {self.roth_basis * 100:.1f}%")
    print(f"Investment Start: ${self.invest_start:,.0f}")
    print(f"Initial Spend: ${self.initial_spend:,.0f}")
    print(f"Basis Fraction: {self.basis_fraction * 100:.1f}%")


class PortfolioProjection:
  def __init__(self, portfolio_start: PortfolioStart, years):
    # Initialize lists based on the fields of PortfolioStart
    self.years = years
    self.portfolio_start = portfolio_start
    self.value_401k = np.concatenate(([portfolio_start.start_401k], np.zeros(years)))
    new_var = years - 1
    self.value_roth = np.concatenate(([portfolio_start.roth_start], np.zeros(years)))
    self.basis_roth = np.concatenate(([portfolio_start.roth_basis], np.zeros(years)))
    self.value_broker = np.concatenate(([portfolio_start.invest_start], np.zeros(years)))
    self.basis_broker = np.concatenate(([portfolio_start.basis_fraction], np.zeros(years)))
    self.annual_expenses = np.concatenate(([portfolio_start.initial_spend], np.zeros(years)))
    self.value_pal = np.zeros(years+1)
    self.taxfree_withdraw = np.zeros(years+1)
    self.bankrupt = False


  def display(self):
    # Display all values for the first year (index 0)
    print("Year 0:")
    print(f"401k Value: ${self.value_401k[0]:,.0f}")
    print(f"Roth Value: ${self.value_roth[0]:,.0f}")
    print(f"Roth Basis: {self.basis_roth[0] * 100:.1f}%")
    print(f"Broker Value: ${self.value_broker[0]:,.0f}")
    print(f"Broker Basis: {self.basis_broker[0] * 100:.1f}%")
    print(f"Pal Value: ${self.value_pal[0]:,.0f}")
    print(f"Annual Expenses: ${self.annual_expenses[0]:,.0f}")


  def display(self, year):
    # Display values for a specific year (index)
    try:
      print(f"Year {year}:")
      print(f"401k Value: ${self.value_401k[year]:,.0f}")
      print(f"Roth Value: ${self.value_roth[year]:,.0f}")
      print(f"Roth Basis: {self.basis_roth[year] * 100:.1f}%")
      print(f"Broker Value: ${self.value_broker[year]:,.0f}")
      print(f"Broker Basis: {self.basis_broker[year] * 100:.1f}%")
      print(f"Pal Value: ${self.value_pal[year]:,.0f}")
      print(f"Annual Expenses: ${self.annual_expenses[year]:,.0f}")

    except IndexError:
      print(f"Data for year {year} is not available.")

  def growth_and_basis(value, basis_frac, growth_rate, conversion=0):
    earnings = value * growth_rate
    if (value + earnings + conversion == 0):
      return 0, 1
    # Conversion and whatever was already in the basis are the basis.
    new_basis = ((value * basis_frac) + conversion) / (value + earnings + conversion)
    #print('growth and basis ', earnings, new_basis, value, growth_rate)

    return value+earnings+conversion, new_basis


  def simulate_portfolio(self, econ=EconomicConditions(), annuals_returns=None):
    years = self.years
    x = np.arange(0, years, 1)
    self.annual_expenses = self.annual_expenses[0] * pow((1 + econ.inflation_rate), x)

    #print(self.annual_expenses)

    # Simulate the portfolio over the specified number of years
    annual_stock_returns = econ.annual_stock_returns
    for y in range(1, years + 1):
      print('Year:', y)
      income = 0
      capital_gains = 0
      cash = 0

      if annuals_returns is not None:
        annual_stock_returns = annuals_returns[y]
      # Calculate how much to migrate from 401k to roth, with no taxation.
      standard_deduction = 14600 * pow((1 + econ.inflation_rate), y)

      # Calculate how much the 401k has grown and withdraw a roth migration.
      self.value_401k[y] = PortfolioProjection.growth_and_basis(self.value_401k[y-1], 1, annual_stock_returns)[0]
      roth_migration = min(standard_deduction, self.value_401k[y])
      self.value_401k[y] -= roth_migration
      income += roth_migration

      # Calculate how much the roth 401k has grown
      self.value_roth[y] = PortfolioProjection.growth_and_basis(self.value_roth[y-1], 1, annual_stock_returns, conversion=roth_migration)[0]
      print('roth ', self.value_roth[y], self.basis_roth[y])

      # Calculate how much the brokerage portfolio has grown.
      print('broker0 ', self.value_broker[y-1], self.basis_broker[y-1], annual_stock_returns, self.value_broker[y-1] * annual_stock_returns)
      #prior_basis = self.basis_broker[y-1]
      self.value_broker[y], self.basis_broker[y] = PortfolioProjection.growth_and_basis(self.value_broker[y-1], self.basis_broker[y-1], annual_stock_returns)
      print('broker2 ', self.value_broker[y], self.basis_broker[y])

      # Personal Expenses
      remaining_expenses = self.annual_expenses[y-1]

      # Pay for expenses with brokerage taxfree capital gains and withdrawal.
      cash = taxes.max_taxfree_withdrawal((1-self.basis_broker[y]), self.value_broker[y], econ.single_capgains_brackets)
      print('broker3 ', self.value_broker[y], self.basis_broker[y], econ.single_capgains_brackets, cash)
      capital_gains += cash * self.basis_broker[y]
      self.taxfree_withdraw[y] = cash
      #print(cash)
      self.value_broker[y] -= cash
      paid_with_cash = min(cash, remaining_expenses)
      remaining_expenses -= paid_with_cash
      cash -= paid_with_cash

      # Pay for expenses from PAL
      pal_loan = 0
      pal_available = 0
      if self.portfolio_start.use_pal and remaining_expenses > 0:
        pal_available = max(0, self.value_broker[y] * self.portfolio_start.pal_cap - self.value_pal[y-1])
        pal_loan = min(pal_available, remaining_expenses)

        remaining_expenses -= pal_loan
      self.value_pal[y] = future_value_pal(pal_loan, n=1, value=self.value_pal[y-1])
      print('pal loan:', pal_loan, pal_available, remaining_expenses)

      # Pay for expenses from ROTH basis
      roth_withdrawal = 0
      if remaining_expenses > 0:
        roth_basis = self.basis_roth[y] if self.portfolio_start.roth_taxfree_year > y else 1
        total_roth_basis = self.value_roth[y] * roth_basis
        roth_withdrawal = min(remaining_expenses, total_roth_basis)
        self.value_roth[y] -= roth_withdrawal
        self.basis_roth[y] = (total_roth_basis - roth_withdrawal) / self.value_roth[y]
        remaining_expenses -= roth_withdrawal

      # Pay for expenses from Brokerage
      # UNTESTED
      full_brokerage_withdrawal = 0
      posttax_brokerage_withdrawal = 0

      if remaining_expenses > 0:
        full_broker_funds = self.taxfree_withdraw[y] + remaining_expenses
        full_brokerage_withdrawal = taxes.calculate_withdrawal(full_broker_funds, self.value_broker[y], (1-self.basis_broker[y]), econ.single_capgains_brackets, prior_withdrawals=self.taxfree_withdraw[y])
        #brokerage_withdrawal_taxes = calculate_income_tax(full_brokerage_withdrawal, tax_brackets=econ.single_capgains_brackets, deduction=0)
        brokerage_withdrawal_taxes = taxes.calculate_capgains(income=full_brokerage_withdrawal*(1-self.basis_broker[y]), capgains_brackets=econ.single_capgains_brackets)


        net_cash = full_brokerage_withdrawal - brokerage_withdrawal_taxes - self.taxfree_withdraw[y]
        # calculate_withdrawal  103842.38301855858 8746.522725101613 95095.86029345696 95094.86029345698
        # taxable brokerage         8  15623.855280730495  15489.294 79471.00501272648         103843      (94961)        8882.699999999999           15489.294987273519
        print('Given a withrawal of', full_brokerage_withdrawal, ' this leads to capgains of ', brokerage_withdrawal_taxes, '. Prior withdrawal was ', self.taxfree_withdraw[y], ' leaving ', net_cash, ' to pay off expenses. Remaining Expenses are ', remaining_expenses, ' limited by: ', self.value_broker[y])
        #print('taxable brokerage ', y, remaining_expenses, net_cash, self.taxfree_withdraw[y], full_brokerage_withdrawal, brokerage_withdrawal_taxes, net_cash)
        additional_withdrawal = full_brokerage_withdrawal - self.taxfree_withdraw[y]
        if additional_withdrawal > 0:
          self.value_broker[y] -= additional_withdrawal
        remaining_expenses -= net_cash
        # taxable brokerage         8  135.4102934569819   15488.44  79471.00501272648         103842 8882.55             15488.444987273513


      print('broker4 ', self.value_broker[y], self.basis_broker[y], self.value_broker[y-1], self.basis_broker[y-1])

      # Pay for expenses from Roth earnings
      # TODO

      # Pay for expenses from 401k
      # TODO

      # Return any remaining cash to the brokerage account
      # TODO
      if cash > 0:
        self.value_broker[y], self.basis_broker[y] = PortfolioProjection.growth_and_basis(self.value_broker[y], self.basis_broker[y], 0, conversion=cash)
        cash = 0
      print('broker5 ', self.value_broker[y], self.basis_broker[y], )

      #self.value_broker[y], self.basis_broker[y] = PortfolioProjection.growth_and_basis(self.value_broker[y], self.basis_broker[y], growth_rate=0, conversion=remaining_deposit)
      #print(self.value_broker[y])
      # Calculate how many expenses are being paid from PAL
      # pal_loan = 0
      # withdrawal = 0
      # if self.portfolio_start.use_pal:
      #   pal_available = max(0, self.value_broker[y] * self.portfolio_start.pal_cap - self.value_pal[y-1])
      #   pal_loan = min(pal_available, remaining_expenses)
      #   self.value_pal[y] = future_value_pal(pal_loan, n=1, value=self.value_pal[y-1])
      #   #print(self.value_pal[y-1], "->", self.value_pal[y])
      #   remaining_expenses -= pal_loan
      #   #print(pal_available, self.portfolio_start.pal_cap)
      # else:
      #   # Calculate the amount you have to withdraw to pay expenses.
      #   #print("Regular Withdrawal")
      #   withdrawal = calculate_withdrawal(remaining_expenses, self.value_broker[y]-1, self.basis_broker[y], econ.single_capgains_brackets)
      # #print(self.value_broker[y])
      # # Subtract the annual expense from brokerage money
      # self.value_broker[y] -= withdrawal
      # remaining_expenses -= withdrawal

      # # If expenses aren't satisfied, start withdrawing from roth.
      # roth_withdrawal = 0
      # if remaining_expenses > 0:
      #   # TODO: IMPLEMENT TAXATION

      #   roth_withdrawal = calculate_withdrawal(expenses, self.value_roth[y], self.basis_roth[y], econ.single_capgains_brackets)
      #   #print("Roth Withdrawal: ", roth_withdrawal)
      #   #roth_withdrawal = min(expenses, self.value_roth[y])
      #   self.value_roth[y] -= roth_withdrawal
      #   remaining_expenses -= roth_withdrawal


      if remaining_expenses > 0:
        # Two bugs: Why doesn't the PAL case withdraw from broker?
        # Why isn't the PAL case satisfied by a roth withdrawal?
        # 8 135.4102934569819 79471.00501272648 103842 0.0 1403702.4077441266 327048.4343263615 357141.94833330397
        print('bankrupt:', y, remaining_expenses)
        print('bankrupt withdrawals:', self.taxfree_withdraw[y], full_brokerage_withdrawal, roth_withdrawal)
        print('bankrupt broker:', self.value_broker[y], self.basis_broker[y])
        print('bankrupt roth:', self.value_roth[y], self.basis_roth[y])
        print('bankrupt 401k:', self.value_401k[y])
        self.bankrupt = True
        break
    #print(self.value_broker)
    return self.value_broker