import math

def calculate_income_tax(income, tax_brackets, deduction):
    """
    Calculate total income tax based on income, tax brackets, and standard deduction.

    Parameters:
    - income (float): The total taxable income.
    - tax_brackets (dict): A dictionary where the keys are the starting incomes for each tax rate,
                           and the values are the tax rates (as decimals, e.g., 0.10 for 10%).
    - standard_deduction (float): The standard deduction for the filing status.

    Returns:
    - total_tax (float): The total amount of income tax owed.
    """
    # Subtract the standard deduction from the income
    taxable_income = max(0, income - deduction)

    total_tax = 0

    # Sort the tax brackets by income thresholds in ascending order
    sorted_brackets = sorted(tax_brackets.items())

    # Calculate the tax based on the taxable income
    for i, (threshold, rate) in enumerate(sorted_brackets):
        if taxable_income > threshold:
            # Calculate the taxable income in the current bracket
            if i + 1 < len(sorted_brackets):
                next_threshold = sorted_brackets[i + 1][0]
                taxable_income_in_bracket = min(taxable_income, next_threshold) - threshold
            else:
                taxable_income_in_bracket = taxable_income - threshold

            # Calculate the tax for this bracket and add to the total tax
            tax_in_bracket = taxable_income_in_bracket * rate
            total_tax += tax_in_bracket
        else:
            break

    return total_tax

def calculate_capgains(income, capgains_brackets):
  return calculate_income_tax(income, tax_brackets=capgains_brackets, deduction=0)

def calculate_withdrawal(target, available, gains_fraction, tax_brackets, prior_withdrawals=0):
  if target <= 0:
      return 0
  withdrawal = target
  capgains = calculate_capgains((withdrawal + prior_withdrawals) * gains_fraction, tax_brackets)
  # TODO: This can overshoot when it enters a new tax bracket with a higher marginal rate.
  while withdrawal - capgains < target-1:
    print(withdrawal, capgains)
    withdrawal *= (target+1) / (withdrawal - capgains)
    capgains = calculate_capgains((withdrawal + prior_withdrawals) * gains_fraction, tax_brackets)
    #break

  print('withdrawal of ', withdrawal, ' leads to capgains of ', capgains, '. Given prior income of ', prior_withdrawals, ' this leaves behind cash value of ', withdrawal - capgains - prior_withdrawals)
  return min(available, math.ceil(withdrawal))


def max_taxfree_withdrawal(gains_fraction, available, tax_brackets):
  if (gains_fraction <= 0):
    return available
  taxfree_gains = 0
  for key in sorted(tax_brackets):
    if tax_brackets[key] > 0:
      taxfree_gains = key
      break
  return min(available, earnings_to_total(taxfree_gains, gains_fraction))

def earnings_to_total(earnings, basis_frac):
  if basis_frac == 0:
    raise Exception("Basis cannot be 0")
  return earnings / basis_frac


