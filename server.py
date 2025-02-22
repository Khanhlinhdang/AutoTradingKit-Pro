import pandas as pd
import numpy as np
import pandas_ta as ta

# Sample OHLC data
data = pd.DataFrame({
    "close": np.random.random(500) * 100,
    "high": np.random.random(500) * 100,
    "low": np.random.random(500) * 100
})

# Input parameters
Len2 = 14
pmom = 65
nmom = 32

# Calculate RSI
data['rsi'] = ta.rsi(data['close'], length=Len2)

# Calculate Momentum
data['ema_close_5'] = ta.ema(data['close'], length=5)
data['ema_high_5'] = ta.ema(data['high'], length=5)
data['ema_low_10'] = ta.ema(data['low'], length=10)

data['p_mom'] = (
    (data['rsi'].shift(1) < pmom) &
    (data['rsi'] > pmom) &
    (data['rsi'] > nmom) &
    (data['ema_close_5'].diff() > 0)
)

data['n_mom'] = (
    (data['rsi'] < nmom) &
    (data['ema_close_5'].diff() < 0)
)

# Initialize conditions
data['positive'] = False
data['negative'] = False

# Apply conditions
data.loc[data['p_mom'], 'positive'] = True
data.loc[data['n_mom'], 'negative'] = True

# Entry conditions
data['pcondition'] = data['positive'] & ~data['positive'].shift(1).dropna()
data['ncondition'] = data['negative'] & ~data['negative'].shift(1).dropna()

# Results
positive_signals = data.loc[data['pcondition'], ['close', 'rsi']]
negative_signals = data.loc[data['ncondition'], ['close', 'rsi']]

# Output results
print("Positive Signals:")
print(positive_signals)

print("\nNegative Signals:")
print(negative_signals)
