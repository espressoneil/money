import pandas as pd
from io import StringIO
import numpy as np
from scipy.stats import gaussian_kde

def load_annual_returns():
  data = """
date,value
  1928-12-31,37.88
  1929-12-31,-11.91
  1930-12-31,-28.48
  1931-12-31,-47.07
  1932-12-31,-15.15
  1933-12-30,46.59
  1934-12-31,-5.94
  1935-12-31,41.37
  1936-12-31,27.92
  1937-12-31,-38.59
  1938-12-31,25.21
  1939-12-30,-5.45
  1940-12-31,-15.29
  1941-12-31,-17.86
  1942-12-31,12.43
  1943-12-31,19.45
  1944-12-30,13.8
  1945-12-31,30.72
  1946-12-31,-11.87
  1947-12-31,0
  1948-12-31,-0.65
  1949-12-31,10.26
  1950-12-30,21.78
  1951-12-31,16.46
  1952-12-31,11.78
  1953-12-31,-6.62
  1954-12-31,45.02
  1955-12-30,26.4
  1956-12-31,2.62
  1957-12-31,-14.31
  1958-12-31,38.06
  1959-12-31,8.48
  1960-12-30,-2.97
  1961-12-29,23.13
  1962-12-31,-11.81
  1963-12-31,18.89
  1964-12-31,12.97
  1965-12-31,9.06
  1966-12-30,-13.09
  1967-12-29,20.09
  1968-12-31,7.66
  1969-12-31,-11.36
  1970-12-31,0.1
  1971-12-31,10.79
  1972-12-29,15.63
  1973-12-31,-17.37
  1974-12-31,-29.72
  1975-12-31,31.55
  1976-12-31,19.15
  1977-12-30,-11.5
  1978-12-29,1.06
  1979-12-31,12.31
  1980-12-31,25.77
  1981-12-31,-9.73
  1982-12-31,14.76
  1983-12-30,17.27
  1984-12-31,1.4
  1985-12-31,26.33
  1986-12-31,14.62
  1987-12-31,2.03
  1988-12-30,12.4
  1989-12-29,27.25
  1990-12-31,-6.56
  1991-12-31,26.31
  1992-12-31,4.46
  1993-12-31,7.06
  1994-12-30,-1.54
  1995-12-29,34.11
  1996-12-31,20.26
  1997-12-31,31.01
  1998-12-31,26.67
  1999-12-31,19.53
  2000-12-29,-10.14
  2001-12-31,-13.04
  2002-12-31,-23.37
  2003-12-31,26.38
  2004-12-31,8.99
  2005-12-30,3
  2006-12-29,13.62
  2007-12-31,3.53
  2008-12-31,-38.49
  2009-12-31,23.45
  2010-12-31,12.78
  2011-12-30,0
  2012-12-31,13.41
  2013-12-31,29.6
  2014-12-31,11.39
  2015-12-31,-0.73
  2016-12-30,9.54
  2017-12-29,19.42
  2018-12-31,-6.24
  2019-12-31,28.88
  2020-12-31,16.26
  2021-12-31,26.89
  2022-12-31,-19.44
  2023-12-29,24.23
  2024-10-09,21.43
  """
  # Create the DataFrame
  annual_returns = pd.read_csv(StringIO(data), parse_dates=['date'])
  return annual_returns

def AnnualReturnsRecent():
  annual_returns = load_annual_returns()
  return annual_returns[annual_returns['date'] >= '1970-12-31']['value']/100

def AnnualReturnsKDEAll():
  return gaussian_kde(load_annual_returns()['value']/100)

def AnnualReturnsKDERecent():
  data = AnnualReturnsRecent()
  return gaussian_kde(data)

# Example data: fitting KDE
def RandomAnnualStockReturns(years, historical_data=AnnualReturnsRecent(), kde=AnnualReturnsKDERecent(), reversion_strength=1):
  # Mean of the original data
  mean_value = np.mean(historical_data)

  # Sample size
  mean_reverting_samples = []
  mean_reverting_returns = []
  original_samples = []
  original_returns = []

  # Define a dynamic mean-reversion strength factor (adjustable)
  reversion_strength = 1  # Strength of pull back towards the mean after each draw

  # Sample progressively with dynamic mean reversion
  for i in range(years):
      # Draw a sample from the KDE
      sample = kde.resample(1)[0][0]

      # Apply a reversion towards the mean, based on previous samples
      if len(mean_reverting_samples) > 0:
          # Compute the current mean of the drawn samples so far
          current_sample_mean = np.mean(mean_reverting_samples)

          # Adjust the new sample towards the global mean based on how far the current sample set has drifted
          adjusted_sample = sample + reversion_strength * (mean_value - current_sample_mean)
      else:
          # No prior samples, just take the first sample as-is
          adjusted_sample = sample

      # Append the adjusted sample to the list
      original_samples.append(sample)
      mean_reverting_samples.append(adjusted_sample)
      if i == 0:
        original_returns.append(1+sample)
        mean_reverting_returns.append(1+adjusted_sample)
      else:
        #print(1+sample, 1+adjusted_sample)
        original_returns.append((1+sample) * original_returns[i-1])
        mean_reverting_returns.append((1+adjusted_sample) * mean_reverting_returns[i-1])

  # Convert the list to a numpy array for easy manipulation
  mean_reverting_samples = np.array(mean_reverting_samples)
  return original_samples, mean_reverting_samples

def GrowthFromReturns(returns):
  growth = []
  growth.append(1+returns[0])
  for i in range(1, len(returns)):
    growth.append(growth[i-1] * (1+returns[i]))
  #print(len(returns), len(growth))
  return np.array(growth)





# # Example data: fitting KDE
def RandomAnnualStockReturns(years, historical_data=annual_returns.AnnualReturnsRecent(), kde=annual_returns.AnnualReturnsKDERecent(), reversion_strength=1):
  # Mean of the original data
  mean_value = np.mean(historical_data)

  # Sample size
  mean_reverting_samples = []
  mean_reverting_returns = []
  original_samples = []
  original_returns = []

  # Define a dynamic mean-reversion strength factor (adjustable)
  reversion_strength = 1  # Strength of pull back towards the mean after each draw

  # Sample progressively with dynamic mean reversion
  for i in range(years):
      # Draw a sample from the KDE
      sample = kde.resample(1)[0][0]

      # Apply a reversion towards the mean, based on previous samples
      if len(mean_reverting_samples) > 0:
          # Compute the current mean of the drawn samples so far
          current_sample_mean = np.mean(mean_reverting_samples)

          # Adjust the new sample towards the global mean based on how far the current sample set has drifted
          adjusted_sample = sample + reversion_strength * (mean_value - current_sample_mean)
      else:
          # No prior samples, just take the first sample as-is
          adjusted_sample = sample

      # Append the adjusted sample to the list
      original_samples.append(sample)
      mean_reverting_samples.append(adjusted_sample)
      if i == 0:
        original_returns.append(1+sample)
        mean_reverting_returns.append(1+adjusted_sample)
      else:
        #print(1+sample, 1+adjusted_sample)
        original_returns.append((1+sample) * original_returns[i-1])
        mean_reverting_returns.append((1+adjusted_sample) * mean_reverting_returns[i-1])

  # Convert the list to a numpy array for easy manipulation
  mean_reverting_samples = np.array(mean_reverting_samples)
  return original_samples, mean_reverting_samples

def GrowthFromReturns(returns):
  growth = []
  growth.append(1+returns[0])
  for i in range(1, len(returns)):
    growth.append(growth[i-1] * (1+returns[i]))
  #print(len(returns), len(growth))
  return np.array(growth)