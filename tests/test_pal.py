from money import economy
from money import pal

def test_pal_multiplier():
    econ = economy.EconomicConditions()
    keys = list(econ.pal_rates.keys())
    assert keys == sorted(keys)

    assert pal.find_pal_multiplier(keys[0], econ) == 1 + econ.pal_rates[keys[0]]
    for i in range(0, len(keys)):

        # Ensure that when you reach a threshold you get that pal rate exactly.
        key = keys[i]
        assert pal.find_pal_multiplier(key, econ) == 1 + econ.pal_rates[key]

        # Ensure that you still get that pal rate up until the next threshold.
        if i < len(keys) - 1:
            next_key = keys[i+1]
            assert pal.find_pal_multiplier(next_key - 1, econ) == 1 + econ.pal_rates[key]


def test_future_value_pal_one_year():
    econ = economy.EconomicConditions()
    n = 1.0
    marginal_cost = 100
    initial_loan = 1000
    assert pal.future_value_pal(marginal_cost, n=n, value=initial_loan) == 1000*(1+econ.pal_rates[0]) + marginal_cost
    
def test_future_value_pal_one_year_float():
    econ = economy.EconomicConditions()
    n = 1.0
    marginal_cost = 100
    initial_loan = 1000
    assert pal.future_value_pal(marginal_cost, n=n+0.5, value=initial_loan) == 1000*(1+econ.pal_rates[0]) + marginal_cost

def test_future_value_pal_two_year():
    econ = economy.EconomicConditions()
    n = 2
    marginal_cost = 100
    initial_loan = 1000
    interest_rate = 1+econ.pal_rates[0]
    inflation_rate = 1+econ.inflation_rate
    one_year = (1000*(interest_rate) + marginal_cost)
    two_year = one_year*interest_rate + marginal_cost*inflation_rate
    assert pal.future_value_pal(marginal_cost, n=n, value=initial_loan) == two_year