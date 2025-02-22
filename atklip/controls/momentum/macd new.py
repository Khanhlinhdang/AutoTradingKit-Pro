# -*- coding: utf-8 -*-
from concurrent.futures import Future
from pandas import concat, DataFrame, Series
from atklip.appmanager.worker.return_worker import HeavyProcess
from atklip.controls.pandas_ta.ma import ma
from atklip.controls.pandas_ta._typing import DictLike, Int
from atklip.controls.pandas_ta.maps import Imports
from atklip.controls.pandas_ta.utils import (
    signals,
    v_offset,
    v_pos_default,
    v_series,
    v_talib
)



def macd(
    close: Series, fast: Int = None, slow: Int = None,
    signal: Int = None,  mamode="ema", talib: bool = False,
    offset: Int = None, **kwargs: DictLike
) -> DataFrame:
    """Moving Average Convergence Divergence (MACD)

    The MACD is a popular indicator to that is used to identify a security's
    trend. While APO and MACD are the same calculation, MACD also returns
    two more series called Signal and Histogram. The Signal is an EMA of
    MACD and the Histogram is the difference of MACD and Signal.

    Sources:
        https://www.tradingview.com/wiki/MACD_(Moving_Average_Convergence/Divergence)
        AS Mode: https://tr.tradingview.com/script/YFlKXHnP/

    Args:
        close (pd.Series): Series of 'close's
        fast (int): The short period. Default: 12
        slow (int): The long period. Default: 26
        signal (int): The signal period. Default: 9
        talib (bool): If TA Lib is installed and talib is True, Returns
            the TA Lib version. Default: True
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        asmode (value, optional): When True, enables AS version of MACD.
            Default: False
        fillna (value, optional): pd.DataFrame.fillna(value)

    Returns:
        pd.DataFrame: macd, histogram, signal columns
    """
    # Validate
    fast = v_pos_default(fast, 12)
    slow = v_pos_default(slow, 26)
    signal = v_pos_default(signal, 9)
    if slow < fast:
        fast, slow = slow, fast
    _length = slow + signal - 1
    close = v_series(close, _length)

    if close is None:
        return

    mode_tal = v_talib(talib)
    offset = v_offset(offset)
    as_mode = kwargs.setdefault("asmode", False)

    # Calculate
    if Imports["talib"] and mode_tal:
        from atklip.controls.talib import MACD
        macd, signalma, histogram = MACD(close, fast, slow, signal)
    else:
        fastma = ma(mamode,close, length=fast)
        slowma = ma(mamode,close, length=slow)

        macd = fastma - slowma
        macd_fvi = macd.loc[macd.first_valid_index():, ]
        signalma = ma(mamode,macd_fvi, length=signal)
        histogram = macd - signalma

    if as_mode:
        macd = macd - signalma
        macd_fvi = macd.loc[macd.first_valid_index():, ]
        signalma = ma(mamode,macd_fvi, length=signal)
        histogram = macd - signalma

    # Offset
    if offset != 0:
        macd = macd.shift(offset)
        histogram = histogram.shift(offset)
        signalma = signalma.shift(offset)

    # Fill
    if "fillna" in kwargs:
        macd.fillna(kwargs["fillna"], inplace=True)
        histogram.fillna(kwargs["fillna"], inplace=True)
        signalma.fillna(kwargs["fillna"], inplace=True)

    # Name and Category
    _asmode = "AS" if as_mode else ""
    _props = f"_{fast}_{slow}_{signal}"
    macd.name = f"MACD{_asmode}{_props}"
    histogram.name = f"HISTOGRAM{_asmode}h{_props}"
    signalma.name = f"SIGNAL{_asmode}s{_props}"
    macd.category = histogram.category = signalma.category = "momentum"

    data = {
        macd.name: macd,
        histogram.name: histogram,
        signalma.name: signalma
    }
    df = DataFrame(data, index=close.index)
    df.name = f"MACD{_asmode}{_props}"
    df.category = macd.category

    signal_indicators = kwargs.pop("signal_indicators", False)
    if signal_indicators:
        signalsdf = concat(
            [
                df,
                signals(
                    indicator=histogram,
                    xa=kwargs.pop("xa", 0),
                    xb=kwargs.pop("xb", None),
                    xserie=kwargs.pop("xserie", None),
                    xserie_a=kwargs.pop("xserie_a", None),
                    xserie_b=kwargs.pop("xserie_b", None),
                    cross_values=kwargs.pop("cross_values", True),
                    cross_series=kwargs.pop("cross_series", True),
                    offset=offset,
                ),
                signals(
                    indicator=macd,
                    xa=kwargs.pop("xa", 0),
                    xb=kwargs.pop("xb", None),
                    xserie=kwargs.pop("xserie", None),
                    xserie_a=kwargs.pop("xserie_a", None),
                    xserie_b=kwargs.pop("xserie_b", None),
                    cross_values=kwargs.pop("cross_values", False),
                    cross_series=kwargs.pop("cross_series", True),
                    offset=offset,
                ),
            ],
            axis=1,
        )

        return signalsdf
    else:
        return df

import numpy as np
import pandas as pd
from typing import List
from atklip.controls.ohlcv import   OHLCV
from atklip.controls.candle import JAPAN_CANDLE,HEIKINASHI,SMOOTH_CANDLE,N_SMOOTH_CANDLE
from atklip.appmanager import ThreadPoolExecutor_global as ApiThreadPool

from PySide6.QtCore import Signal,QObject

class MACD(QObject):
    sig_update_candle = Signal()
    sig_add_candle = Signal()
    sig_reset_all = Signal()
    signal_delete = Signal()    
    sig_add_historic = Signal(int)
    def __init__(self,_candles,dict_ta_params) -> None:
        super().__init__(parent=None)

        self._candles: JAPAN_CANDLE|HEIKINASHI|SMOOTH_CANDLE|N_SMOOTH_CANDLE =_candles
                
        self.source:str = dict_ta_params.get("source")       
        self.slow_period:int = dict_ta_params.get("slow_period") 
        self.fast_period:int = dict_ta_params.get("fast_period") 
        self.signal_period:int = dict_ta_params.get("signal_period") 
        self.mamode: str = dict_ta_params.get("mamode") 
        self.offset :int=dict_ta_params.get("drift",0)

        #self.signal_delete.connect(self.deleteLater)
        self.first_gen = False
        self.is_genering = True
        self.is_current_update = False
        self.is_histocric_load = False
        self._name = f"MACD {self.source} {self.mamode} {self.slow_period} {self.fast_period} {self.signal_period}"

        self.df = pd.DataFrame([])
        self.worker = ApiThreadPool
        
        self.xdata,self.macd_data,self.histogram,self.signalma = np.array([]),np.array([]),np.array([]),np.array([])

        self.connect_signals()
    
    @property
    def source_name(self)-> str:
        return self._source_name
    @source_name.setter
    def source_name(self,source_name):
        self._source_name = source_name
    
    def change_input(self,candles=None,dict_ta_params:dict={}):
        if candles != None:
            self.disconnect_signals()
            self._candles : JAPAN_CANDLE|HEIKINASHI|SMOOTH_CANDLE|N_SMOOTH_CANDLE= candles
            self.connect_signals()
        
        if dict_ta_params != {}:
            self.source:str = dict_ta_params.get("source")       
            self.slow_period:int = dict_ta_params.get("slow_period") 
            self.fast_period:int = dict_ta_params.get("fast_period") 
            self.signal_period:int = dict_ta_params.get("signal_period") 
            self.mamode: str = dict_ta_params.get("mamode") 
            self.offset :int=dict_ta_params.get("drift",0)
            
            ta_name:str=dict_ta_params.get("ta_name")
            obj_id:str=dict_ta_params.get("obj_id") 
            
            ta_param = f"{obj_id}-{ta_name}-{self.source}-{self.mamode}-{self.slow_period}-{self.fast_period}-{self.signal_period}"

            self._name = ta_param
        
        self.first_gen = False
        self.is_genering = True
        self.is_current_update = False
        
        self.fisrt_gen_data()
    
    def disconnect_signals(self):
        try:
            self._candles.sig_reset_all.disconnect(self.started_worker)
            self._candles.sig_update_candle.disconnect(self.update_worker)
            self._candles.sig_add_candle.disconnect(self.add_worker)
            self._candles.signal_delete.disconnect(self.signal_delete)
            self._candles.sig_add_historic.disconnect(self.add_historic_worker)
        except RuntimeError:
                    pass
    
    def connect_signals(self):
        self._candles.sig_reset_all.connect(self.started_worker)
        self._candles.sig_update_candle.connect(self.update_worker)
        self._candles.sig_add_candle.connect(self.add_worker)
        self._candles.sig_add_historic.connect(self.add_historic_worker)
        self._candles.signal_delete.connect(self.signal_delete)
    
    
    def change_source(self,_candles:JAPAN_CANDLE|HEIKINASHI|SMOOTH_CANDLE|N_SMOOTH_CANDLE):
        self.disconnect_signals()
        self._candles =_candles
        self.connect_signals()
        self.started_worker()
    
    
    @property
    def name(self):
        return self._name
    @name.setter
    def name(self,_name):
        self._name = _name
    
    def get_df(self,n:int=None):
        if not n:
            return self.df
        return self.df.tail(n)
    
    def get_data(self,start:int=0,stop:int=0):
        if len(self.xdata) == 0:
            return [],[],[],[]
        if start == 0 and stop == 0:
            x_data = self.xdata
            macd_data,signalma,histogram=self.macd_data,self.signalma,self.histogram
        elif start == 0 and stop != 0:
            x_data = self.xdata[:stop]
            macd_data,signalma,histogram=self.macd_data[:stop],self.signalma[:stop],self.histogram[:stop]
        elif start != 0 and stop == 0:
            x_data = self.xdata[start:]
            macd_data,signalma,histogram=self.macd_data[start:],self.signalma[start:],self.histogram[start:]
        else:
            x_data = self.xdata[start:stop]
            macd_data,signalma,histogram=self.macd_data[start:stop],self.signalma[start:stop],self.histogram[start:stop]
        return x_data,macd_data,signalma,histogram
    
    def get_last_row_df(self):
        return self.df.iloc[-1] 

    
    def update_worker(self,candle):
        self.worker.submit(self.update,candle)

    def add_worker(self,candle):
        self.worker.submit(self.add,candle)

    
    def add_historic_worker(self,n):        
        self.worker.submit(self.add_historic,n)

    def started_worker(self):
        self.worker.submit(self.fisrt_gen_data)
    
    
    @staticmethod
    def paire_data(INDICATOR:DataFrame):
        try:
            column_names = INDICATOR.columns.tolist()
            macd_name = ''
            histogram_name = ''
            signalma_name = ''
            for name in column_names:
                if name.__contains__("MACD"):
                    macd_name = name
                elif name.__contains__("HISTOGRAM"):
                    histogram_name = name
                elif name.__contains__("SIGNAL"):
                    signalma_name = name

            macd = INDICATOR[macd_name].dropna().round(6)
            histogram = INDICATOR[histogram_name].dropna().round(6)
            signalma = INDICATOR[signalma_name].dropna().round(6)
            return macd,histogram,signalma
        except:
            return Series([]),Series([]),Series([])
    

    @staticmethod
    def calculate(df: pd.DataFrame,source,fast_period,slow_period,signal_period,mamode,offset):
        INDICATOR = macd(close=df[source],
                        fast=fast_period,
                        slow=slow_period,
                        signal = signal_period,
                        mamode=mamode,
                        offset=offset)
        column_names = INDICATOR.columns.tolist()
        macd_name = ''
        histogram_name = ''
        signalma_name = ''
        for name in column_names:
            if name.__contains__("MACD"):
                macd_name = name
            elif name.__contains__("HISTOGRAM"):
                histogram_name = name
            elif name.__contains__("SIGNAL"):
                signalma_name = name

        macd_data = INDICATOR[macd_name].dropna().round(6)
        histogram = INDICATOR[histogram_name].dropna().round(6)
        signalma = INDICATOR[signalma_name].dropna().round(6)
        
        _len = min([len(histogram),len(macd_data),len(signalma), int(len(df)-slow_period)])
        
        _index = df["index"]
        return pd.DataFrame({
                            'index':_index.tail(_len),
                            "macd":macd_data.tail(_len),
                            "histogram":histogram.tail(_len),
                            "signalma":signalma.tail(_len)
                            })
    
    
    def callback_first_gen(self, future: Future):
        self.df = future.result()
        self.xdata,self.macd_data,self.histogram,self.signalma = self.df["index"].to_numpy(),\
                                                                    self.df["macd"].to_numpy(),\
                                                                    self.df["histogram"].to_numpy(),\
                                                                    self.df["signalma"].to_numpy()
        self.is_genering = False
        if self.first_gen == False:
            self.first_gen = True
            self.is_genering = False
        #self.is_current_update = True
        self.sig_reset_all.emit()
    
    def fisrt_gen_data(self):
        self.is_current_update = False
        self.is_genering = True
        self.df = pd.DataFrame([])
        df:pd.DataFrame = self._candles.get_df()
        process = HeavyProcess(self.calculate,
                               self.callback_first_gen,
                               df,
                               self.source,
                               self.fast_period,
                               self.slow_period,
                               self.signal_period,
                               self.mamode,
                               self.offset)
        process.start()
        
    
    def callback_gen_historic_data(self, future: Future):
        _df = future.result()
        _len = len(_df)
        self.df = pd.concat([_df,self.df],ignore_index=True)        
        
        self.xdata = np.concatenate((_df["index"].to_numpy(), self.xdata)) 
        self.macd_data = np.concatenate((_df["macd"].to_numpy(), self.macd_data))   
        self.histogram = np.concatenate((_df["histogram"].to_numpy(), self.histogram))
        self.signalma = np.concatenate((_df["signalma"].to_numpy(), self.signalma))
                
        self.is_genering = False
        if self.first_gen == False:
            self.first_gen = True
            self.is_genering = False
        self.is_histocric_load = True
        self.sig_add_historic.emit(_len)
    
    def add_historic(self,n:int):
        self.is_genering = True
        self.is_histocric_load = False
        _pre_len = len(self.df)
        candle_df = self._candles.get_df()
        df:pd.DataFrame = candle_df.head(-_pre_len)
        
        process = HeavyProcess(self.calculate,
                               self.callback_gen_historic_data,
                               df,
                               self.source,
                               self.fast_period,
                               self.slow_period,
                               self.signal_period,
                               self.mamode,
                               self.offset)
        process.start()
        
    
    def add_update_calculate(self,df: pd.DataFrame):
        INDICATOR = macd(close=df[self.source],
                        fast=self.fast_period,
                        slow=self.slow_period,
                        signal = self.signal_period,
                        mamode=self.mamode,
                        offset=self.offset)
        return self.paire_data(INDICATOR)
    
    def add(self,new_candles:List[OHLCV]):
        new_candle:OHLCV = new_candles[-1]
        self.is_current_update = False
        if (self.first_gen == True) and (self.is_genering == False):
            df:pd.DataFrame = self._candles.get_df(self.slow_period*5)
                    
            macd_data,histogram,signalma = self.add_update_calculate(df)
            
            new_frame = pd.DataFrame({
                                    'index':[new_candle.index],
                                    "macd":[macd_data.iloc[-1]],
                                    "histogram":[histogram.iloc[-1]],
                                    "signalma":[signalma.iloc[-1]]
                                    })
            
            self.df = pd.concat([self.df,new_frame],ignore_index=True)
                                
            self.xdata = np.concatenate((self.xdata,np.array([new_candle.index])))
            self.macd_data = np.concatenate((self.macd_data,np.array([macd_data.iloc[-1]])))
            self.histogram = np.concatenate((self.histogram,np.array([histogram.iloc[-1]])))
            self.signalma = np.concatenate((self.signalma,np.array([signalma.iloc[-1]])))

            self.sig_add_candle.emit()
        #self.is_current_update = True
        
    def update(self, new_candles:List[OHLCV]):
        new_candle:OHLCV = new_candles[-1]
        self.is_current_update = False
        if (self.first_gen == True) and (self.is_genering == False):
            df:pd.DataFrame = self._candles.get_df(self.slow_period*5)
                    
            macd_data,histogram,signalma = self.add_update_calculate(df)
                    
            self.df.iloc[-1] = [new_candle.index,macd_data.iloc[-1],histogram.iloc[-1],signalma.iloc[-1]]
                    
            self.xdata[-1],self.macd_data[-1],self.histogram[-1],self.signalma[-1] = new_candle.index,macd_data.iloc[-1],histogram.iloc[-1],signalma.iloc[-1]

            self.sig_update_candle.emit()
        #self.is_current_update = True
            
            
