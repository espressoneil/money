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

# Attempts to withdraw 'target' aftertax dollars from the 'available' amount, given that a certain
# fraction of the 'available' is gains. Uses the tax_brackets to 
def calculate_withdrawal(target, available, gains_fraction, tax_brackets, prior_withdrawals=0):
  if target <= 0:
      return 0

  if gains_fraction <= 0:
    return min(target, available)

  ordered_brackets = []
  for key in sorted(tax_brackets):
    # All tax brackets trigger sooner based on the prior withdrawals. Negative is fine.
    ordered_brackets.append([key - prior_withdrawals, tax_brackets[key]])

  remaining_aftertax_withdrawal = target
  total_withdrawal = 0

  for i in range(0, len(ordered_brackets)):
    effective_taxrate = ordered_brackets[i][1] * gains_fraction

    # The aftertax withdrawal is simply the remaining amount IF this is the highest bracket.
    aftertax_withdrawal = remaining_aftertax_withdrawal
    if i + 1 < len(ordered_brackets):
      # any bracket start can be negative due to 'prior_withdrawals' simplifications.
      bracket_limit = max(0, ordered_brackets[i+1][0] - max(0, ordered_brackets[i][0]))
      max_withdrawal = bracket_limit / gains_fraction
      max_aftertax_withdrawal = max_withdrawal * (1 - effective_taxrate)
      aftertax_withdrawal = min(max_aftertax_withdrawal, remaining_aftertax_withdrawal)
    withdrawal = aftertax_withdrawal / (1 - effective_taxrate)

    total_withdrawal += withdrawal
    remaining_aftertax_withdrawal -= aftertax_withdrawal

    #print(gains_fraction, ordered_brackets[i][1], effective_taxrate, aftertax_withdrawal, total_withdrawal)

  return min(available, total_withdrawal)


def max_taxfree_withdrawal(gains_fraction, available, tax_brackets):
  if (gains_fraction <= 0):
    return available
  taxfree_gains = 0
  for key in sorted(tax_brackets):
    if tax_brackets[key] > 0:
      taxfree_gains = key
      break
  max_withdrawal = earnings_to_total(taxfree_gains, gains_fraction)
  #print(f"{max_withdrawal} max from {taxfree_gains} allowed gains with fraction {gains_fraction}")
  return min(available, max_withdrawal)

def earnings_to_total(earnings, basis_frac):
  if basis_frac == 0:
    raise Exception("Basis cannot be 0")
  return earnings / basis_frac


