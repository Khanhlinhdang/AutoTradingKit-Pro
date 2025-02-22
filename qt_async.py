import vectorbt as vbt
import pandas as pd
import numpy as np
import talib
import datetime as dt
import json
import requests
URL = 'https://api.binance.com/api/v3/klines'
 
intervals_to_secs = {
    '1m':60,
    '3m':180,
    '5m':300,
    '15m':900,
    '30m':1800,
    '1h':3600,
    '2h':7200,
    '4h':14400,
    '6h':21600,
    '8h':28800,
    '12h':43200,
    '1d':86400,
    '3d':259200,
    '1w':604800,
    '1M':2592000
}
 
def download_kline_data(start: dt.datetime, end:dt.datetime ,ticker:str, interval:str)-> pd.DataFrame:
    start = int(start.timestamp()*1000)
    end = int(end.timestamp()*1000)
    full_data = pd.DataFrame()
     
    while start < end:
        par = {'symbol': ticker, 'interval': interval, 'startTime': str(start), 'endTime': str(end), 'limit':1000}
        data = pd.DataFrame(json.loads(requests.get(URL, params= par).text))
 
        data.index = [dt.datetime.fromtimestamp(x/1000.0) for x in data.iloc[:,0]]
        data=data.astype(float)
        full_data = pd.concat([full_data,data])
         
        start+=intervals_to_secs[interval]*1000*1000
         
    full_data.columns = ['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume','Close_time', 'Qav', 'Num_trades','Taker_base_vol', 'Taker_quote_vol', 'Ignore']
     
    return full_data

# UT Bot Parameters
SENSITIVITY = 1
ATR_PERIOD = 10
 
# Ticker and timeframe
TICKER = "BTCUSDT"
INTERVAL = "5m"
 
# Backtest start/end date
START = dt.datetime(2024,10,25)
END   = dt.datetime.now()

	
# Get data from Binance
pd_data = download_kline_data(START, END, TICKER, INTERVAL)
pd_data["xATR"] = talib.ATR(pd_data["High"], pd_data["Low"], pd_data["Close"], timeperiod=ATR_PERIOD)
pd_data["nLoss"] = SENSITIVITY * pd_data["xATR"]
 
#Drop all rows that have nan, X first depending on the ATR preiod for the moving average
pd_data = pd_data.dropna()
pd_data = pd_data.reset_index()

# Compute ATR And nLoss variable
pd_data["xATR"] = talib.ATR(pd_data["High"], pd_data["Low"], pd_data["Close"], timeperiod=ATR_PERIOD)
pd_data["nLoss"] = SENSITIVITY * pd_data["xATR"]
 
#Drop all rows that have nan, X first depending on the ATR preiod for the moving average
pd_data = pd_data.dropna()
pd_data = pd_data.reset_index()

# Function to compute ATRTrailingStop
def xATRTrailingStop_func(close, prev_close, prev_atr, nloss):
    if close > prev_atr and prev_close > prev_atr:
        return max(prev_atr, close - nloss)
    elif close < prev_atr and prev_close < prev_atr:
        return min(prev_atr, close + nloss)
    elif close > prev_atr:
        return close - nloss
    else:
        return close + nloss
 
# # Filling ATRTrailingStop Variable
# pd_data["ATRTrailingStop"] = [0.0] + [np.nan for i in range(len(pd_data) - 1)]

pd_data["ATRTrailingStop"] = np.nan
pd_data.loc[0, "ATRTrailingStop"] = 0.0  # Set the first value

for i in range(1, len(pd_data)):
    pd_data.loc[i, "ATRTrailingStop"] = xATRTrailingStop_func(
        pd_data.loc[i, "Close"],
        pd_data.loc[i - 1, "Close"],
        pd_data.loc[i - 1, "ATRTrailingStop"],
        pd_data.loc[i, "nLoss"],
    )

# def xATRTrailingStop(row):
#     """Calculate the ATR trailing stop based on the current and previous row."""
#     if row['Close'] > row['Prev_ATR'] and row['Prev_Close'] > row['Prev_ATR']:
#         return max(row['Prev_ATR'], row['Close'] - row['nLoss'])
#     elif row['Close'] < row['Prev_ATR'] and row['Prev_Close'] < row['Prev_ATR']:
#         return min(row['Prev_ATR'], row['Close'] + row['nLoss'])
#     elif row['Close'] > row['Prev_ATR']:
#         return row['Close'] - row['nLoss']
#     else:
#         return row['Close'] + row['nLoss']

# def calculate_atr_trailing_stop(pd_data: pd.DataFrame) -> pd.DataFrame:
#     """Fill the ATRTrailingStop column in the DataFrame."""
#     # Initialize the ATRTrailingStop column
#     pd_data["ATRTrailingStop"] = np.nan
#     pd_data.loc[0, "ATRTrailingStop"] = 0.0  # Set the first value

#     # Create previous columns for calculations
#     pd_data['Prev_Close'] = pd_data['Close'].shift(1)
#     pd_data['Prev_ATR'] = pd_data['ATRTrailingStop'].shift(1)

#     # Apply the trailing stop calculation
#     pd_data['ATRTrailingStop'] = pd_data.apply(xATRTrailingStop, axis=1)

#     # Drop the temporary columns
#     pd_data.drop(columns=['Prev_Close', 'Prev_ATR'], inplace=True)

#     return pd_data

# # Giả sử pd_data đã được định nghĩa và chứa các cột cần thiết
# pd_data = calculate_atr_trailing_stop(pd_data)

# Calculating signals
ema = vbt.MA.run(pd_data["Close"], 1, short_name='EMA', ewm=True)
 
pd_data["Above"] = ema.ma_crossed_above(pd_data["ATRTrailingStop"])
pd_data["Below"] = ema.ma_crossed_below(pd_data["ATRTrailingStop"])
 
pd_data["Buy"] = (pd_data["Close"] > pd_data["ATRTrailingStop"]) & (pd_data["Above"]==True)
pd_data["Sell"] = (pd_data["Close"] < pd_data["ATRTrailingStop"]) & (pd_data["Below"]==True)


print(pd_data.loc[(pd_data["Buy"]==True)| ( pd_data["Sell"]==True)])

