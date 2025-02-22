from typing import Dict, Tuple, List,TYPE_CHECKING
import numpy as np

from PySide6.QtCore import Signal, QRect, QRectF, QPointF,QThreadPool,Qt,QLineF
from PySide6.QtGui import QPainter, QPicture
from PySide6.QtWidgets import QGraphicsItem,QStyleOptionGraphicsItem,QWidget
from atklip.graphics.pyqtgraph import mkPen, GraphicsObject, mkBrush

from atklip.appmanager import FastWorker

if TYPE_CHECKING:
    from atklip.graphics.chart_component.viewchart import Chart
    from atklip.graphics.chart_component.sub_panel_indicator import ViewSubPanel

class OptimationLine(GraphicsObject):
    """Live candlestick plot, plotting data [[open, close, min, max], ...]"""
    sigPlotChanged = Signal(object)
    sig_change_yaxis_range = Signal()
    
    sig_update_histogram = Signal(tuple,str)
    sig_reset_histogram = Signal(tuple,str)
    sig_add_histogram = Signal(tuple,str)
    sig_load_historic_histogram = Signal(tuple,str)
    
    def __init__(self,chart,trend_color) -> None:
        """Choose colors of candle"""
        GraphicsObject.__init__(self)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemUsesExtendedStyleOption,True)
        self.chart:Chart = chart

        precision = 1
        
        self.has = {
            "name": f"Optimation Line",
            "y_axis_show":False,
            "inputs":{
                    "source":self.chart.jp_candle,
                    "source_name":self.chart.jp_candle.source_name,
                    "show":True
                    },

            "styles":{
                    'pen': "gray",
                    "trend_color":trend_color,
                    'width': 1,
                    'style': Qt.PenStyle.SolidLine,}
        }

        self.precision = precision
        self.output_y_data: List[float] = []


        self.x_data, self.y_data ,self.trend= np.array([]),np.array([]),np.array([])
        
        self._bar_picutures: Dict[int, QPicture] = {}
        self.picture: QPicture = None
        self._rect_area: Tuple[float, float] = None
        self._to_update: bool = False
        self._is_change_source: bool = False
        self._start:int = None
        self._stop:int = None
        
        self.sig_reset_histogram.connect(self.threadpool_asyncworker,Qt.ConnectionType.AutoConnection)
        self.sig_add_histogram.connect(self.update_asyncworker,Qt.ConnectionType.AutoConnection)
        self.sig_update_histogram.connect(self.update_asyncworker,Qt.ConnectionType.AutoConnection)
        self.sig_load_historic_histogram.connect(self.threadpool_asyncworker,Qt.ConnectionType.AutoConnection)

    def get_inputs(self):
        inputs =  {}
        return inputs
    
    def get_styles(self):
        styles =  {"pen_high_historgram":self.has["styles"]["pen_high_historgram"],
                    "pen_low_historgram":self.has["styles"]["pen_low_historgram"],
                    "brush_high_historgram":self.has["styles"]["brush_high_historgram"],
                    "brush_low_historgram":self.has["styles"]["brush_low_historgram"],}
        return styles

    def update_styles(self, _input,data):
        self._is_change_source = True
        _style = self.has["styles"][_input]
        if _input == "brush_high_historgram":
            self.has["styles"]["brush_high_historgram"] = mkBrush(_style,width=0.7)
        elif _input == "brush_low_historgram":
            self.has["styles"]["brush_low_historgram"] = mkBrush(_style,width=0.7)
        self.threadpool_asyncworker(data,"reset")
        
    def get_min_max(self):
        x_data, y_data = self.has["inputs"]["source"].get_index_volumes(stop=len(self.has["inputs"]["source"].candles))
        values = [y[2] for y in y_data]
        _min,_max = None,None
        if values != []:
            _min,_max = min(values), max(values)
        return _min,_max
    
    def threadpool_asyncworker(self,data,_type):
        self.worker = None
        self.worker = FastWorker(self.update_last_data,data,_type)
        self.worker.signals.setdata.connect(self.setData,Qt.ConnectionType.AutoConnection)
        self.worker.start()
    
    
    def update_asyncworker(self,data,_type):
        self.worker = None
        self.worker = FastWorker(self.update_last_data,data,_type)
        self.worker.signals.setdata.connect(self.updateData,Qt.ConnectionType.AutoConnection)
        self.worker.start()    
    
    def updateData(self, data) -> None:
        """y_data must be in format [[open, close, min, max], ...]"""
        self._to_update = False
        x_data, y_data, trend = data[0],data[1],data[2]
        
    
        if x_data[-1] == self.x_data[-1]:
            self.y_data[-2:] = y_data[-2:]
            self.trend[-2:] = trend[-2:]
        else:
            self.x_data[-1] = x_data[-2]
            self.y_data[-1] = y_data[-2]
            self.trend[-1] = trend[-2]
            
            self.x_data = np.append(self.x_data, x_data[-1])  
            self.y_data = np.append(self.y_data, y_data[-1])
            self.trend = np.append(self.trend, trend[-1])
        
        self.draw_single_volume(-1)
        
        self._to_update = True
        # self.prepareGeometryChange()
        # self.informViewBoundsChanged()
        self.update(self.boundingRect())
    
    
    def get_yaxis_param(self):
        if len(self.has["inputs"]["source"].candles) > 0:
            last_candle = self.has["inputs"]["source"].last_data()
            last_volume_ = last_candle.volume
            last_close_price_ = last_candle.close
            last_open_price_ = last_candle.open
            colorline = "green" if last_close_price_ >= last_open_price_ else "red"
            last_color,last_close_price = colorline,last_close_price_
            return None,None
            return last_volume_,last_color
        else:
            return None,None
    def get_xaxis_param(self):
        return None,None
    

    def update_last_data(self,data,_type, setdata) -> None:
        x_data, y_data, trend = data[0],data[1], data[2]
        try:
            if _type == "reset":
                self._is_change_source = True
                setdata.emit((x_data, y_data,trend))
            if _type == "load_historic":
                _len = len(self._bar_picutures)
                setdata.emit((x_data, y_data,trend))
            if _type == "add":
                setdata.emit((x_data, y_data,trend))
        except Exception as e:
            pass
    
    def paint(self,painter: QPainter,opt: QStyleOptionGraphicsItem,w: QWidget) -> None:
        """
        Reimplement the paint method of parent class.

        This function is called by external QGraphicsView.
        """
        self.picture.play(painter)

    def _draw_item_picture(self, min_ix: int, max_ix: int) -> None:
        """
        Draw the picture of item in specific range.
        """
        self.picture = QPicture()
        painter = QPainter(self.picture)
        [self.play_bar(painter,ix) for ix in range(min_ix, max_ix)]
        painter.end()
    
    def play_bar(self,painter,ix):
        bar_picture = self._bar_picutures.get(ix,None)
        if bar_picture:
            bar_picture.play(painter)   
    
    
    def boundingRect(self) -> QRectF:
        x_left,x_right = int(self.chart.xAxis.range[0]),int(self.chart.xAxis.range[1])   
        start_index = self.chart.jp_candle.start_index
        stop_index = self.chart.jp_candle.stop_index
        if x_left > start_index:
            self._start = x_left+2
        elif x_left > stop_index:
            self._start = start_index+2
        else:
            self._start = start_index+2
            
        if x_right < stop_index:
            self._stop = x_right+2
        else:
            self._stop = stop_index+2

        rect_area: tuple = (self._start, self._stop)
        if self._to_update:
            self._rect_area = rect_area
            self._draw_item_picture(self._start, self._stop)
            self._to_update = False
        elif rect_area != self._rect_area:
            self._rect_area = rect_area
            self._draw_item_picture(self._start, self._stop)
        return self.picture.boundingRect()

    def draw_volume(self,x_data,index):
        "dieu kien de han che viec ve lai khi add new candle"
        t = x_data[index]
        if not self._bar_picutures.get(t):
            self.draw_single_volume(index)
            return True
        return False
        
    def draw_single_volume(self,index):
        pre_t = self.x_data[index-1]
        pre_value = self.y_data[index-1]
        pre_trend = self.trend[index-1]
        cr_trend = self.trend[index]
        t = self.x_data[index]
        value = self.y_data[index]
        candle_picture:QPicture =QPicture()
        p:QPainter =QPainter(candle_picture)
        if pre_trend and cr_trend:
            color = self.has["styles"]["trend_color"]
            width = 2
            style = Qt.PenStyle.SolidLine
        else:
            color = self.has["styles"]["pen"]
            width = 0.5
            style = Qt.PenStyle.DotLine
        
        outline_pen = mkPen(color=color,width=width,style=style)
        p.setPen(outline_pen)
        _line = QLineF(QPointF(pre_t, pre_value), QPointF(t, value))
        p.drawLine(_line)
        p.end()
        self._bar_picutures[t] = candle_picture
            
    def setData(self, data) -> None:
        """y_data must be in format [[open, close, min, max], ...]"""
        self._to_update = False
        
        x_data, y_data, trend = data[0],data[1],data[2]
        
        self.x_data, self.y_data, self.trend = x_data, y_data, trend

        if self._is_change_source:
            self._bar_picutures.clear()
            self._is_change_source = False
        [self.draw_volume(x_data,index) for index in range(1,len(y_data))]
        self._to_update = True
        self.chart.sig_update_y_axis.emit()
        # self.prepareGeometryChange()
        # self.informViewBoundsChanged()
        self.update(self.boundingRect())
         
    def getData(self) -> Tuple[List[float], List[Tuple[float, ...]]]:
        return self.x_data, self.y_data
    

class SuperTrendLine(GraphicsObject):
    """Live candlestick plot, plotting data [[open, close, min, max], ...]"""
    sigPlotChanged = Signal(object)
    sig_change_yaxis_range = Signal()
    
    sig_update_histogram = Signal(tuple,str)
    sig_reset_histogram = Signal(tuple,str)
    sig_add_histogram = Signal(tuple,str)
    sig_load_historic_histogram = Signal(tuple,str)
    
    def __init__(self,chart,trend_color) -> None:
        """Choose colors of candle"""
        GraphicsObject.__init__(self)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemUsesExtendedStyleOption,True)
        self.chart:Chart = chart

        precision = 1
        
        self.has = {
            "name": f"Optimation Line",
            "y_axis_show":False,
            "inputs":{
                    "source":self.chart.jp_candle,
                    "source_name":self.chart.jp_candle.source_name,
                    "show":True
                    },

            "styles":{
                    'pen': "gray",
                    "trend_color":trend_color,
                    'width': 1,
                    'style': Qt.PenStyle.SolidLine,}
        }

        self.precision = precision
        self.output_y_data: List[float] = []


        self.x_data, self.y_data ,self.trend= np.array([]),np.array([]),np.array([])
        
        self._bar_picutures: Dict[int, QPicture] = {}
        self.picture: QPicture = None
        self._rect_area: Tuple[float, float] = None
        self._to_update: bool = False
        self._is_change_source: bool = False
        self._start:int = None
        self._stop:int = None
        
        self.sig_reset_histogram.connect(self.threadpool_asyncworker,Qt.ConnectionType.AutoConnection)
        self.sig_add_histogram.connect(self.update_asyncworker,Qt.ConnectionType.AutoConnection)
        self.sig_update_histogram.connect(self.update_asyncworker,Qt.ConnectionType.AutoConnection)
        self.sig_load_historic_histogram.connect(self.threadpool_asyncworker,Qt.ConnectionType.AutoConnection)

    def get_inputs(self):
        inputs =  {}
        return inputs
    
    def get_styles(self):
        styles =  {"pen_high_historgram":self.has["styles"]["pen_high_historgram"],
                    "pen_low_historgram":self.has["styles"]["pen_low_historgram"],
                    "brush_high_historgram":self.has["styles"]["brush_high_historgram"],
                    "brush_low_historgram":self.has["styles"]["brush_low_historgram"],}
        return styles

    def update_styles(self, _input,data):
        self._is_change_source = True
        _style = self.has["styles"][_input]
        if _input == "brush_high_historgram":
            self.has["styles"]["brush_high_historgram"] = mkBrush(_style,width=0.7)
        elif _input == "brush_low_historgram":
            self.has["styles"]["brush_low_historgram"] = mkBrush(_style,width=0.7)
        self.threadpool_asyncworker(data,"reset")
        
    def get_min_max(self):
        x_data, y_data = self.has["inputs"]["source"].get_index_volumes(stop=len(self.has["inputs"]["source"].candles))
        values = [y[2] for y in y_data]
        _min,_max = None,None
        if values != []:
            _min,_max = min(values), max(values)
        return _min,_max
    
    def threadpool_asyncworker(self,data,_type):
        self.worker = None
        self.worker = FastWorker(self.update_last_data,data,_type)
        self.worker.signals.setdata.connect(self.setData,Qt.ConnectionType.AutoConnection)
        self.worker.start()
    
    
    def update_asyncworker(self,data,_type):
        self.worker = None
        self.worker = FastWorker(self.update_last_data,data,_type)
        self.worker.signals.setdata.connect(self.updateData,Qt.ConnectionType.AutoConnection)
        self.worker.start()    
    
    def updateData(self, data) -> None:
        """y_data must be in format [[open, close, min, max], ...]"""
        self._to_update = False
        x_data, y_data, trend = data[0],data[1],data[2]
        
    
        if x_data[-1] == self.x_data[-1]:
            self.y_data[-2:] = y_data[-2:]
            self.trend[-2:] = trend[-2:]
        else:
            self.x_data[-1] = x_data[-2]
            self.y_data[-1] = y_data[-2]
            self.trend[-1] = trend[-2]
            
            self.x_data = np.append(self.x_data, x_data[-1])  
            self.y_data = np.append(self.y_data, y_data[-1])
            self.trend = np.append(self.trend, trend[-1])
        
        self.draw_single_volume(-1)
        
        self._to_update = True
        # self.prepareGeometryChange()
        # self.informViewBoundsChanged()
        self.update(self.boundingRect())
    
    
    def get_yaxis_param(self):
        if len(self.has["inputs"]["source"].candles) > 0:
            last_candle = self.has["inputs"]["source"].last_data()
            last_volume_ = last_candle.volume
            last_close_price_ = last_candle.close
            last_open_price_ = last_candle.open
            colorline = "green" if last_close_price_ >= last_open_price_ else "red"
            last_color,last_close_price = colorline,last_close_price_
            return None,None
            return last_volume_,last_color
        else:
            return None,None
    def get_xaxis_param(self):
        return None,None
    

    def update_last_data(self,data,_type, setdata) -> None:
        x_data, y_data, trend = data[0],data[1], data[2]
        try:
            if _type == "reset":
                self._is_change_source = True
                setdata.emit((x_data, y_data,trend))
            if _type == "load_historic":
                _len = len(self._bar_picutures)
                setdata.emit((x_data, y_data,trend))
            if _type == "add":
                setdata.emit((x_data, y_data,trend))
        except Exception as e:
            pass
    
    def paint(self,painter: QPainter,opt: QStyleOptionGraphicsItem,w: QWidget) -> None:
        """
        Reimplement the paint method of parent class.

        This function is called by external QGraphicsView.
        """
        self.picture.play(painter)

    def _draw_item_picture(self, min_ix: int, max_ix: int) -> None:
        """
        Draw the picture of item in specific range.
        """
        self.picture = QPicture()
        painter = QPainter(self.picture)
        [self.play_bar(painter,ix) for ix in range(min_ix, max_ix)]
        painter.end()
    
    def play_bar(self,painter,ix):
        bar_picture = self._bar_picutures.get(ix,None)
        if bar_picture:
            bar_picture.play(painter)   
    
    
    def boundingRect(self) -> QRectF:
        x_left,x_right = int(self.chart.xAxis.range[0]),int(self.chart.xAxis.range[1])   
        start_index = self.chart.jp_candle.start_index
        stop_index = self.chart.jp_candle.stop_index
        if x_left > start_index:
            self._start = x_left+2
        elif x_left > stop_index:
            self._start = start_index+2
        else:
            self._start = start_index+2
            
        if x_right < stop_index:
            self._stop = x_right+2
        else:
            self._stop = stop_index+2

        rect_area: tuple = (self._start, self._stop)
        if self._to_update:
            self._rect_area = rect_area
            self._draw_item_picture(self._start, self._stop)
            self._to_update = False
        elif rect_area != self._rect_area:
            self._rect_area = rect_area
            self._draw_item_picture(self._start, self._stop)
        return self.picture.boundingRect()

    def draw_volume(self,x_data,index):
        "dieu kien de han che viec ve lai khi add new candle"
        t = x_data[index]
        if not self._bar_picutures.get(t):
            self.draw_single_volume(index)
            return True
        return False
        
    def draw_single_volume(self,index):
        pre_t = self.x_data[index-1]
        pre_value = self.y_data[index-1]
        pre_trend = self.trend[index-1]
        cr_trend = self.trend[index]
        t = self.x_data[index]
        value = self.y_data[index]
        color = None
        if self.has["styles"]["trend_color"] == "green":
            if pre_trend > 0:
                color = "green"
                width = 1
                style = Qt.PenStyle.SolidLine
        elif self.has["styles"]["trend_color"] == "red":
            if pre_trend < 0:
                color = "red"
                width = 1
                style = Qt.PenStyle.SolidLine
        if color:
            candle_picture:QPicture =QPicture()
            p:QPainter =QPainter(candle_picture)
            outline_pen = mkPen(color=color,width=width,style=style)
            p.setPen(outline_pen)
            _line = QLineF(QPointF(pre_t, pre_value), QPointF(t, value))
            p.drawLine(_line)
            p.end()
            self._bar_picutures[t] = candle_picture
            
    def setData(self, data) -> None:
        """y_data must be in format [[open, close, min, max], ...]"""
        self._to_update = False
        
        x_data, y_data, trend = data[0],data[1],data[2]
        
        self.x_data, self.y_data, self.trend = x_data, y_data, trend

        if self._is_change_source:
            self._bar_picutures.clear()
            self._is_change_source = False
        [self.draw_volume(x_data,index) for index in range(1,len(y_data))]
        self._to_update = True
        self.chart.sig_update_y_axis.emit()
        # self.prepareGeometryChange()
        # self.informViewBoundsChanged()
        self.update(self.boundingRect())
         
    def getData(self) -> Tuple[List[float], List[Tuple[float, ...]]]:
        return self.x_data, self.y_data
    


class TrendLine(GraphicsObject):
    """Live candlestick plot, plotting data [[open, close, min, max], ...]"""
    sigPlotChanged = Signal(object)
    sig_change_yaxis_range = Signal()
    
    sig_update_histogram = Signal(tuple,str)
    sig_reset_histogram = Signal(tuple,str)
    sig_add_histogram = Signal(tuple,str)
    sig_load_historic_histogram = Signal(tuple,str)
    
    def __init__(self,chart) -> None:
        """Choose colors of candle"""
        GraphicsObject.__init__(self)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemUsesExtendedStyleOption,True)
        self.chart:Chart = chart

        precision = 1
        
        self.has = {
            "name": f"Optimation Line",
            "y_axis_show":False,
            "inputs":{
                    "source":self.chart.jp_candle,
                    "source_name":self.chart.jp_candle.source_name,
                    "show":True
                    },

            "styles":{
                    "up_trend_color":"green",
                    "down_trend_color":"red",
                    "sideway_trend_color":"orange",
                    'width': 1,
                    'style': Qt.PenStyle.SolidLine,}
        }

        self.precision = precision
        self.output_uptrend: List[float] = []


        self.x_data, self.uptrend ,self.downtrend= np.array([]),np.array([]),np.array([])
        
        self._bar_picutures: Dict[int, QPicture] = {}
        self.picture: QPicture = None
        self._rect_area: Tuple[float, float] = None
        self._to_update: bool = False
        self._is_change_source: bool = False
        self._start:int = None
        self._stop:int = None
        
        self.sig_reset_histogram.connect(self.threadpool_asyncworker,Qt.ConnectionType.AutoConnection)
        self.sig_add_histogram.connect(self.update_asyncworker,Qt.ConnectionType.AutoConnection)
        self.sig_update_histogram.connect(self.update_asyncworker,Qt.ConnectionType.AutoConnection)
        self.sig_load_historic_histogram.connect(self.threadpool_asyncworker,Qt.ConnectionType.AutoConnection)

    def get_inputs(self):
        inputs =  {}
        return inputs
    
    def get_styles(self):
        styles =  {"pen_high_historgram":self.has["styles"]["pen_high_historgram"],
                    "pen_low_historgram":self.has["styles"]["pen_low_historgram"],
                    "brush_high_historgram":self.has["styles"]["brush_high_historgram"],
                    "brush_low_historgram":self.has["styles"]["brush_low_historgram"],}
        return styles

    def update_styles(self, _input,data):
        self._is_change_source = True
        _style = self.has["styles"][_input]
        if _input == "brush_high_historgram":
            self.has["styles"]["brush_high_historgram"] = mkBrush(_style,width=0.7)
        elif _input == "brush_low_historgram":
            self.has["styles"]["brush_low_historgram"] = mkBrush(_style,width=0.7)
        self.threadpool_asyncworker(data,"reset")
        
    def get_min_max(self):
        x_data, uptrend = self.has["inputs"]["source"].get_index_volumes(stop=len(self.has["inputs"]["source"].candles))
        values = [y[2] for y in uptrend]
        _min,_max = None,None
        if values != []:
            _min,_max = min(values), max(values)
        return _min,_max
    
    def threadpool_asyncworker(self,data,_type):
        self.worker = None
        self.worker = FastWorker(self.update_last_data,data,_type)
        self.worker.signals.setdata.connect(self.setData,Qt.ConnectionType.AutoConnection)
        self.worker.start()
    
    
    def update_asyncworker(self,data,_type):
        self.worker = None
        self.worker = FastWorker(self.update_last_data,data,_type)
        self.worker.signals.setdata.connect(self.updateData,Qt.ConnectionType.AutoConnection)
        self.worker.start()    
    
    def updateData(self, data) -> None:
        """uptrend must be in format [[open, close, min, max], ...]"""
        self._to_update = False
        x_data, uptrend, downtrend = data[0],data[1],data[2]
        
    
        if x_data[-1] == self.x_data[-1]:
            self.uptrend[-2:] = uptrend[-2:]
            self.downtrend[-2:] = downtrend[-2:]
        else:
            self.x_data[-1] = x_data[-2]
            self.uptrend[-1] = uptrend[-2]
            self.downtrend[-1] = downtrend[-2]
            
            self.x_data = np.append(self.x_data, x_data[-1])  
            self.uptrend = np.append(self.uptrend, uptrend[-1])
            self.downtrend = np.append(self.downtrend, downtrend[-1])
        
        self.draw_single_volume(-1)
        
        self._to_update = True
        # self.prepareGeometryChange()
        # self.informViewBoundsChanged()
        self.update(self.boundingRect())
    
    
    def get_yaxis_param(self):
        if len(self.has["inputs"]["source"].candles) > 0:
            last_candle = self.has["inputs"]["source"].last_data()
            last_volume_ = last_candle.volume
            last_close_price_ = last_candle.close
            last_open_price_ = last_candle.open
            colorline = "green" if last_close_price_ >= last_open_price_ else "red"
            last_color,last_close_price = colorline,last_close_price_
            return None,None
            return last_volume_,last_color
        else:
            return None,None
    def get_xaxis_param(self):
        return None,None
    

    def update_last_data(self,data,_type, setdata) -> None:
        x_data, uptrend, downtrend = data[0],data[1], data[2]
        try:
            if _type == "reset":
                self._is_change_source = True
                setdata.emit((x_data, uptrend,downtrend))
            if _type == "load_historic":
                _len = len(self._bar_picutures)
                setdata.emit((x_data, uptrend,downtrend))
            if _type == "add":
                setdata.emit((x_data, uptrend,downtrend))
        except Exception as e:
            pass
    
    def paint(self,painter: QPainter,opt: QStyleOptionGraphicsItem,w: QWidget) -> None:
        """
        Reimplement the paint method of parent class.

        This function is called by external QGraphicsView.
        """
        self.picture.play(painter)

    def _draw_item_picture(self, min_ix: int, max_ix: int) -> None:
        """
        Draw the picture of item in specific range.
        """
        self.picture = QPicture()
        painter = QPainter(self.picture)
        [self.play_bar(painter,ix) for ix in range(min_ix, max_ix)]
        painter.end()
    
    def play_bar(self,painter,ix):
        bar_picture = self._bar_picutures.get(ix,None)
        if bar_picture:
            bar_picture.play(painter)   
    
    
    def boundingRect(self) -> QRectF:
        x_left,x_right = int(self.chart.xAxis.range[0]),int(self.chart.xAxis.range[1])   
        start_index = self.chart.jp_candle.start_index
        stop_index = self.chart.jp_candle.stop_index
        if x_left > start_index:
            self._start = x_left+2
        elif x_left > stop_index:
            self._start = start_index+2
        else:
            self._start = start_index+2
            
        if x_right < stop_index:
            self._stop = x_right+2
        else:
            self._stop = stop_index+2

        rect_area: tuple = (self._start, self._stop)
        if self._to_update:
            self._rect_area = rect_area
            self._draw_item_picture(self._start, self._stop)
            self._to_update = False
        elif rect_area != self._rect_area:
            self._rect_area = rect_area
            self._draw_item_picture(self._start, self._stop)
        return self.picture.boundingRect()

    def draw_volume(self,x_data,index):
        "dieu kien de han che viec ve lai khi add new candle"
        t = x_data[index]
        if not self._bar_picutures.get(t):
            self.draw_single_volume(index)
            return True
        return False
        
    def draw_single_volume(self,index):
        pre_t = self.x_data[index-1]
        pre_uptrend = self.uptrend[index-1]
        pre_downtrend = self.downtrend[index-1]
        
        t = self.x_data[index]
        cr_uptrend = self.uptrend[index]
        cr_downtrend = self.downtrend[index]
        
        color = None
        width = 1
        style = Qt.PenStyle.SolidLine
        if pre_uptrend:
            color = self.has["styles"]["up_trend_color"]
        elif pre_downtrend:
            color = self.has["styles"]["down_trend_color"]
        else:
            color = self.has["styles"]["sideway_trend_color"]
        
        if color:
            candle_picture:QPicture =QPicture()
            p:QPainter =QPainter(candle_picture)
            outline_pen = mkBrush(color=color)
            p.setBrush(outline_pen)
            # _line = QLineF(QPointF(pre_t, 0), QPointF(t, 0))
            rect = QRectF(pre_t, -0.5,t-pre_t,1)
            # p.drawLine(_line)
            p.fillRect(rect,outline_pen)
            p.end()
            self._bar_picutures[t] = candle_picture
            
    def setData(self, data) -> None:
        """uptrend must be in format [[open, close, min, max], ...]"""
        self._to_update = False
        
        x_data, uptrend, downtrend = data[0],data[1],data[2]
        
        self.x_data, self.uptrend, self.downtrend = x_data, uptrend, downtrend

        if self._is_change_source:
            self._bar_picutures.clear()
            self._is_change_source = False
        [self.draw_volume(x_data,index) for index in range(1,len(uptrend))]
        self._to_update = True
        self.chart.sig_update_y_axis.emit()
        # self.prepareGeometryChange()
        # self.informViewBoundsChanged()
        self.update(self.boundingRect())
        
         
    def getData(self) -> Tuple[List[float], List[Tuple[float, ...]]]:
        return self.x_data, self.uptrend
    
