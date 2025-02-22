import numpy as np
import pandas as pd
import pandas_ta as ta
from talib import ATR

class SmartMoneyConcepts:
    def __init__(self, df, 
                 swings_length=50,
                 internal_length=5,
                 equal_highs_lows_length=3,
                 equal_highs_lows_threshold=0.1,
                 order_block_filter='Atr',
                 order_block_mitigation='High/Low',
                 show_internal_structure=True,
                 show_swing_structure=True):
        
        self.df = df.copy()
        self.swing_length = swings_length
        self.internal_length = internal_length
        self.equal_length = equal_highs_lows_length
        self.equal_threshold = equal_highs_lows_threshold
        self.order_block_filter = order_block_filter
        self.order_block_mitigation = order_block_mitigation
        self.show_internal = show_internal_structure
        self.show_swing = show_swing_structure
        
        # Initialize indicators
        self._calculate_indicators()
        self._detect_swings()
        self._detect_internal_structure()
        self._detect_order_blocks()
        self._detect_fvg()
        self._detect_equal_highs_lows()

    def _calculate_indicators(self):
        # Calculate ATR and volatility measure
        self.df['atr'] = ATR(self.df.high, self.df.low, self.df.close, timeperiod=200)
        self.df['cumulative_range'] = (self.df.high - self.df.low).cumsum() / (self.df.index + 1)
        
        # Determine high volatility bars
        if self.order_block_filter == 'Atr':
            self.df['high_vol'] = (self.df.high - self.df.low) >= 2 * self.df['atr']
        else:
            self.df['high_vol'] = (self.df.high - self.df.low) >= 2 * self.df['cumulative_range']
        
        # Parsed high/low for order blocks
        self.df['parsed_high'] = np.where(self.df['high_vol'], self.df.low, self.df.high)
        self.df['parsed_low'] = np.where(self.df['high_vol'], self.df.high, self.df.low)

    def _detect_swings(self, col_prefix='swing'):
        # Swing high/low detection using rolling windows
        self.df[f'{col_prefix}_high'] = self.df.high.rolling(self.swing_length, center=True).max()
        self.df[f'{col_prefix}_low'] = self.df.low.rolling(self.swing_length, center=True).min()
        
        # Crossovers for structure breaks
        self.df[f'{col_prefix}_high_break'] = (self.df.close > self.df[f'{col_prefix}_high']).astype(int)
        self.df[f'{col_prefix}_low_break'] = (self.df.close < self.df[f'{col_prefix}_low']).astype(int)

    def _detect_internal_structure(self):
        if self.show_internal:
            self._detect_swings(col_prefix='internal')

    def _detect_order_blocks(self):
        # Bullish order blocks (swing low with high volatility)
        bullish_ob = self.df[(self.df['high_vol']) & 
                           (self.df.low == self.df.parsed_low.rolling(self.swing_length).min())]
        self.bullish_ob = bullish_ob[['high', 'low', 'open_time']].copy()
        self.bullish_ob['type'] = 'bullish'
        
        # Bearish order blocks (swing high with high volatility)
        bearish_ob = self.df[(self.df['high_vol']) & 
                           (self.df.high == self.df.parsed_high.rolling(self.swing_length).max())]
        self.bearish_ob = bearish_ob[['high', 'low', 'open_time']].copy()
        self.bearish_ob['type'] = 'bearish'
        
        # Combine order blocks
        self.order_blocks = pd.concat([self.bullish_ob, self.bearish_ob]).sort_index()

    def _detect_fvg(self):
        # Detect Fair Value Gaps using shift operations
        self.df['prev_high'] = self.df.high.shift(2)
        self.df['prev_low'] = self.df.low.shift(2)
        
        self.df['bullish_fvg'] = (self.df.low > self.df.prev_high) & (self.df.close > self.df.prev_high)
        self.df['bearish_fvg'] = (self.df.high < self.df.prev_low) & (self.df.close < self.df.prev_low)

    def _detect_equal_highs_lows(self):
        # Equal highs detection
        self.df['equal_high'] = self.df.high.rolling(self.equal_length).apply(
            lambda x: np.all(np.abs(x - x[-1]) < self.equal_threshold * self.df['atr'].iloc[-1]))
        
        # Equal lows detection
        self.df['equal_low'] = self.df.low.rolling(self.equal_length).apply(
            lambda x: np.all(np.abs(x - x[-1]) < self.equal_threshold * self.df['atr'].iloc[-1]))

    def get_signals(self):
        signals = self.df[['swing_high_break', 'swing_low_break', 
                          'bullish_fvg', 'bearish_fvg',
                          'equal_high', 'equal_low']].copy()
        
        # Add order block mitigation signals
        signals['bullish_ob_mitigation'] = self.df.close > self.order_blocks.high.shift(1)
        signals['bearish_ob_mitigation'] = self.df.close < self.order_blocks.low.shift(1)
        
        return signals

# Usage example:
# Load your OHLC data into a DataFrame df
# smc = SmartMoneyConcepts(df)
# signals = smc.get_signals()