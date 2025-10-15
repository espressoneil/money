# Economic Conditions
class EconomicConditions:
  def __init__(self):
    self.annual_stock_returns = 0.08  # 8% annual stock returns
    self.sp_dividend_rate = 0.013 # 1.3% qualified dividend annually
    # Annualized inflation rate over 30 years
    self.inflation_rate = 0.025  # 2.5% inflation
    # Estimated annualized fed funds rate
    self.fed_funds_rate = 0.054  # 5.4% fed funds rate

    # PAL fees based on investment amounts
    self.pal_fees = {0: 0.0125, 50e3: 0.0105, 1000e3: 0.0075, 5000e3: 0.005}
    self.pal_rates = {}
    for threshold in self.pal_fees:
      self.pal_rates[threshold] = self.fed_funds_rate + self.pal_fees[threshold]

    # Standard tax deductions
    self.tax_deductions = 14600  # Assume no custom deductions
    self.standard_deduction = 14600

    # Single filing tax brackets (2024 rates)
    self.single_brackets = {
      0: 0.10,
      11600: 0.12,
      44725: 0.22,
      95375: 0.24,
      182100: 0.32,
      231250: 0.35,
      578125: 0.37
    }

    # Capital gains tax brackets for single filers
    self.single_capgains_brackets = {
      0: 0.00,       # 0% tax rate for income up to $44,625
      44625: 0.15,   # 15% tax rate for income between $44,626 and $492,300
      492300: 0.20   # 20% tax rate for income over $492,300
    }

  def display(self):
    print(f"Annual Stock Returns: {self.annual_stock_returns * 100:.2f}%")
    print(f"Inflation Rate: {self.inflation_rate * 100:.2f}%")
    print(f"Federal Funds Rate: {self.fed_funds_rate * 100:.2f}%")
    print(f"Standard Deduction: ${self.standard_deduction}")
    print("PAL Fees and Rates by Investment Threshold:")
    for threshold, rate in self.pal_rates.items():
      print(f"  Investment >= ${threshold}: {rate * 100:.2f}%")
    print("\nSingle Filing Tax Brackets:")
    for income, rate in self.single_brackets.items():
      print(f"  Income >= ${income}: {rate * 100:.2f}%")
    print("\nSingle Filing Capital Gains Tax Brackets:")
    for income, rate in self.single_capgains_brackets.items():
      print(f"  Income >= ${income}: {rate * 100:.2f}%")

