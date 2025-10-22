import numpy as np
from . import economy

def find_pal_multiplier(P, econ=economy.EconomicConditions()):
  rate = econ.pal_rates[0]
  for key in econ.pal_rates:
      #print(P, key, rate, econ.pal_rates)
      
      if P >= key:
          rate = econ.pal_rates[key]
      else:
          break
  #print(P, rate, econ.pal_rates)
  return 1 + rate

def future_value_pal_helper(initial_cost, n, econ=economy.EconomicConditions(), value=0):
  start_value = value
  annual_cost = initial_cost
  #print(n)
  for i in range(0, int(n)):
    rate = find_pal_multiplier(value, econ)
    value *= rate
    value = value + annual_cost
    annual_cost *= 1+econ.inflation_rate
    #print(rate, annual_cost, econ.inflation_rate)
  #print(start_value, "->", value)
  return value

def future_value_pal(initial_cost, n, econ=economy.EconomicConditions(), value=0):
  if isinstance(n, float) or isinstance(n, int):
    #print(n)
    return future_value_pal_helper(initial_cost, n, econ=econ, value=value)

  values = np.zeros(len(n))
  for i in range(0, len(n)):
    values[i] = future_value_pal_helper(initial_cost, n[i], econ=econ)
  return values