import asyncio
import traceback
import re
import requests

from atklip.gui.qfluentwidgets.components.widgets import SearchLineEdit
from atklip.gui.qfluentwidgets.components.container import HWIDGET
from atklip.gui.qfluentwidgets import EchangeIcon as EI,FluentStyleSheet
from atklip.gui.components import ScrollInterface,ICON_TEXT_BUTTON_SYMBOL,Symbol_Item,MovingWidget

from PySide6.QtWidgets import QStackedWidget,QAbstractScrollArea, QWidget,QApplication
from PySide6.QtCore import QEvent, Signal,QCoreApplication
from PySide6.QtGui import Qt

from atklip.exchanges import list_exchanges, CryptoExchange
from atklip.appmanager.worker import RequestAsyncWorker,ThreadingAsyncWorker
from atklip.gui.components import LoadingProgress
from atklip.gui.qfluentwidgets.common.icon import *
from atklip.appmanager import AppConfig, AppLogger
from atklip.app_utils import *

class RightMenu(ScrollInterface):
    def __init__(self,parent:QWidget=None):
        super(RightMenu,self).__init__(parent)
        self.setObjectName("ExChanges Menu")
        self._parent:ListSymbolMenuByExchange = parent
        self.setFixedHeight(600)

        self.FAVORITE = ICON_TEXT_BUTTON_SYMBOL(list_exchanges.FAVORITE,self._parent,"Favorite Markets",EI.FAVORITE)
        self.addWidget(self.FAVORITE)

        self.BINANCE_SPOT = ICON_TEXT_BUTTON_SYMBOL(list_exchanges.BINANCE_SPOT,self._parent,"Binance",EI.BINANCE_ICON)
        self.addWidget(self.BINANCE_SPOT)
        self.BINANCE_PERPETUAL_FUTURES = ICON_TEXT_BUTTON_SYMBOL(list_exchanges.BINANCE_PERPETUAL_FUTURES,self._parent,"Binance Perpetual",EI.BINANCE_TEXT)
        self.addWidget(self.BINANCE_PERPETUAL_FUTURES)
        # self.BINANCE_COIN_FUTURES = ICON_TEXT_BUTTON_SYMBOL(list_exchanges.BINANCE_COIN_FUTURES,self._parent,"Binance Coin",EI.BINANCE_TEXT)
        # self.addWidget(self.BINANCE_COIN_FUTURES)
        # self.BITVAVO = ICON_TEXT_BUTTON_SYMBOL(list_exchanges.BITVAVO,self._parent,"BitVAVO",EI.BITVAVO)
        # self.addWidget(self.BITVAVO)
        self.BYBIT = ICON_TEXT_BUTTON_SYMBOL(list_exchanges.BYBIT,self._parent,"ByBit",EI.BYBIT)
        self.addWidget(self.BYBIT)
        
        self.MEXC = ICON_TEXT_BUTTON_SYMBOL(list_exchanges.MEXC,self._parent,"Mexc",EI.MEXC)
        self.addWidget(self.MEXC)
        self.KUCOIN_FUTURES = ICON_TEXT_BUTTON_SYMBOL(list_exchanges.KUCOIN_FUTURES,self._parent,"Kucoin Futures",EI.KUCOIN_FUTURES)
        self.addWidget(self.KUCOIN_FUTURES)
        self.KUCOIN_SPOT = ICON_TEXT_BUTTON_SYMBOL(list_exchanges.KUCOIN_SPOT,self._parent,"Kucoin Spot",EI.KUCOIN)
        self.addWidget(self.KUCOIN_SPOT)
        
        self.DERIBIT = ICON_TEXT_BUTTON_SYMBOL(list_exchanges.DERIBIT,self._parent,"DeriBit",EI.DERIBIT)
        self.addWidget(self.DERIBIT)
        # self.HITBTC = ICON_TEXT_BUTTON_SYMBOL(list_exchanges.HITBTC,self._parent,"HitBTC",EI.HITBTC)
        # self.addWidget(self.HITBTC)
        self.HUOBI = ICON_TEXT_BUTTON_SYMBOL(list_exchanges.HUOBI,self._parent,"HuoBi",EI.HUOBI)
        self.addWidget(self.HUOBI)
        self.OKEX = ICON_TEXT_BUTTON_SYMBOL(list_exchanges.OKEX,self._parent,"OKX",EI.OKEX)
        self.addWidget(self.OKEX)
        self.COINBASE_EXCHANGE = ICON_TEXT_BUTTON_SYMBOL(list_exchanges.COINBASE_EXCHANGE,self._parent,"Coinbase Exchange",EI.COINBASE_PRO)
        self.addWidget(self.COINBASE_EXCHANGE)
        
        self.COINBASE = ICON_TEXT_BUTTON_SYMBOL(list_exchanges.COINBASE,self._parent,"Coinbase Advanced",EI.COINBASE_PRO)
        self.addWidget(self.COINBASE)
        
        self.BINGX = ICON_TEXT_BUTTON_SYMBOL(list_exchanges.BINGX,self._parent,"BingX",EI.BINGX)
        self.addWidget(self.BINGX)
        self.BITFINEX2 = ICON_TEXT_BUTTON_SYMBOL(list_exchanges.BITFINEX2,self._parent,"Bitfinex",EI.BITFINEX2)
        self.addWidget(self.BITFINEX2)
        self.BITGET = ICON_TEXT_BUTTON_SYMBOL(list_exchanges.BITGET,self._parent,"Bitget",EI.BITGET)
        self.addWidget(self.BITGET)
        self.BITMART = ICON_TEXT_BUTTON_SYMBOL(list_exchanges.BITMART,self._parent,"BitMart",EI.BITMART)
        self.addWidget(self.BITMART)
        self.BITMEX = ICON_TEXT_BUTTON_SYMBOL(list_exchanges.BITMEX,self._parent,"BitMex",EI.BITMEX)
        self.addWidget(self.BITMEX)
        
        self.KRAKEN_SPOT = ICON_TEXT_BUTTON_SYMBOL(list_exchanges.KRAKEN_SPOT,self._parent,"Kraken Spot",EI.KRAKEN_SPOT)
        self.addWidget(self.KRAKEN_SPOT)
        # self.KRAKEN_FUTURES = ICON_TEXT_BUTTON_SYMBOL(list_exchanges.KRAKEN_FUTURES,self._parent,"Kraken Futures",EI.KRAKEN_FUTURES)
        # self.addWidget(self.KRAKEN_FUTURES)
        # self.COINEX = ICON_TEXT_BUTTON_SYMBOL(list_exchanges.COINEX,self._parent,"CoinEX",EI.COINEX)
        # self.addWidget(self.COINEX)
        #self.addSpacer()

class BaseMenu(ScrollInterface):
    sig_show_process = Signal(bool)
    sig_update_symbol = Signal(int)
    sig_add_item = Signal(object)
    sig_remove_item = Signal(object)
    sig_add_to_favorite = Signal(tuple)
    sig_update_symbols = Signal(str)
    def __init__(self,sig_add_remove_favorite,sig_change_symbol,parent:QWidget=None,exchange_id:str=""):
        super(BaseMenu,self).__init__(parent)
        self._parent = self.parent()
        self.setObjectName(f"{exchange_id}")

        self.dict_favorites = {}

        self.sig_add_remove_favorite = sig_add_remove_favorite

        self.exchange_id = exchange_id
        self.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.setFixedHeight(600)
        self._list_symbols = []
        self.loading = False
        self.is_get_symbol = False
        self.sig_change_symbol = sig_change_symbol

        self.installEventFilter(self)

        self.process = LoadingProgress(self,size=40)
        self.process.hide()

        self.sig_show_process.connect(self.process.run_process,Qt.ConnectionType.AutoConnection)
        self.sig_update_symbol.connect(self.update_symbol,Qt.ConnectionType.AutoConnection)
        self.sig_add_item.connect(self.add_Widget,Qt.ConnectionType.AutoConnection)
        self.sig_remove_item.connect(self.remove_Widget,Qt.ConnectionType.AutoConnection)
        self.sig_add_to_favorite.connect(self.add_to_favorite_from_load,Qt.ConnectionType.AutoConnection)
        self.sig_update_symbols.connect(self.check_new_symbol_from_ex,Qt.ConnectionType.AutoConnection)
        self.load_favorite()

    def add_remove_favorite_item(self,_is_add,_symbol,_exchange_id):
        if _is_add:
            self.add_to_favorite(_symbol,_exchange_id)
        else:
            self.remove_from_favorite(_symbol,_exchange_id)
    def add_to_favorite(self,symbol,exchange_id):
        if self.exchange_id == "favorite":
            if exchange_id not in list(self.dict_favorites.keys()):
                self.dict_favorites[exchange_id] = [symbol]
                item = Symbol_Item(self.sig_add_remove_favorite,self.sig_change_symbol,symbol,exchange_id,self)
                item.btn_fovarite.added_to_favorite()
                self.sig_add_item.emit(item)
            else:
                if symbol not in self.dict_favorites[exchange_id]:
                    self.dict_favorites[exchange_id].append(symbol)
                    item = Symbol_Item(self.sig_add_remove_favorite,self.sig_change_symbol,symbol,exchange_id,self)
                    item.btn_fovarite.added_to_favorite()
                    self.sig_add_item.emit(item)
            AppConfig.sig_set_single_data.emit((f"topbar.symbol.favorite.{exchange_id}",self.dict_favorites[exchange_id]))
            
            self.dict_favorites = AppConfig.get_config_value(f"topbar.symbol.favorite")

    def remove_from_favorite(self,symbol,exchange_id):
        if exchange_id not in list(self.dict_favorites.keys()):
            return
        if symbol not in self.dict_favorites[exchange_id]:
            return
        if self.exchange_id == exchange_id:
            _item = self.findChild(Symbol_Item,f"{symbol}_{exchange_id}")
            if isinstance(_item,Symbol_Item):
                _item.btn_fovarite.reject_from_favorite()
        if self.exchange_id == "favorite":
            self.dict_favorites[exchange_id].remove(symbol)
            AppConfig.sig_set_single_data.emit((f"topbar.symbol.favorite.{exchange_id}",self.dict_favorites[exchange_id]))
            item = self.findChild(Symbol_Item,f"{symbol}_{exchange_id}")
            if item != None:
                self.sig_remove_item.emit(item)
        self.dict_favorites = AppConfig.get_config_value(f"topbar.symbol.favorite")

    def add_to_favorite_from_load(self,emit_data):
        symbol,exchange_id = emit_data[0],emit_data[1]
        item = Symbol_Item(self.sig_add_remove_favorite,self.sig_change_symbol,symbol,exchange_id)
        # item.moveToThread(QApplication.instance().thread())
        item.btn_fovarite.added_to_favorite()
        self.sig_add_item.emit(item)
        # #QCoreApplication.processEvents()

    def load_favorite(self):
        #self.sig_show_process.emit(True)
        self._favorite()

    def check_new_symbol_from_ex(self,exchange_id):
        worker = ThreadingAsyncWorker(self.update_symbols,exchange_id)
        worker.start_thread()

    def _favorite(self):
        self.is_get_symbol = True
        self.dict_favorites = AppConfig.get_config_value(f"topbar.symbol.favorite")
        if self.dict_favorites == None:
            AppConfig.sig_set_single_data.emit((f"topbar.symbol.favorite",{}))
            self.dict_favorites = AppConfig.get_config_value(f"topbar.symbol.favorite")
            return
        if self.dict_favorites != {}:
            if self.exchange_id == "favorite":
                for exchange_id in list(self.dict_favorites.keys()):
                    _list_symbols = self.dict_favorites[exchange_id]
                    for symbol in _list_symbols:
                        self.sig_add_to_favorite.emit((symbol,exchange_id))
                        QCoreApplication.processEvents()
        #self.sig_show_process.emit(False)

    def get_all_symbols_by_exchange(self,exchange_id):
        if not self.isAdded:
            self.is_get_symbol = True
            self.sig_show_process.emit(True)
            worker = RequestAsyncWorker(self.get_symbol,exchange_id)
            worker.signals.update_signal.connect(self.add_symbol,Qt.ConnectionType.AutoConnection)
            worker.start_thread()

    def read_config_setting(self,update_signal):
        if self.dict_favorites != {}:
            for exchange_id in list(self.dict_favorites.keys()):
                _list_symbols = self.dict_favorites[exchange_id]
                update_signal.emit([_list_symbols,exchange_id])
                QCoreApplication.processEvents()
            
    def add_Widget(self,widget):
        wgs = self.vBoxLayout.widgets
        self.insertWidget(-1,widget,stretch=0, alignment=Qt.AlignmentFlag.AlignBottom)
        
        #self.addWidget(widget,stretch=0, alignment=Qt.AlignTop)
    
    def remove_Widget(self,widget):
        self.removeWidget(widget)

    async def update_symbols(self,exchange_id):
        crypto_ex = CryptoExchange(None)
        exchange = crypto_ex.setupEchange(exchange_name=exchange_id)
        try:
            await exchange.load_markets()
            markets = []
            for market in list(exchange.markets.keys()):
                if exchange.markets[market]['active'] == True:
                    markets.append(exchange.markets[market]['symbol'])
            # markets = exchange.symbols
            if markets != []:
                symbols = [re.findall(r'(.*?):', market)[0] for market in markets if re.findall(r'(.*?):', market) != []]
                if symbols == []:
                    symbols = [market for market in markets if re.findall(r'(.*?):', market) == []]
                for symbol in  symbols:
                    if "/" in symbol:
                        first_symbol = re.findall(r'(.*?)/', symbol)
                        if check_icon_exist(first_symbol[0]):
                            if symbol not in self._list_symbols:
                                self._list_symbols.append(symbol)
                        else:
                            "đây là chỗ tìm coin chưa có icon để bổ sung"
                            url = f"https://s3-symbol-logo.tradingview.com/crypto/XTVC{first_symbol[0]}.svg"
                            res = requests.get(url)
                            if res.status_code == 200:
                                with open(f"{get_real_path()}/{str(first_symbol[0]).lower()}.svg", "w") as f:
                                    f.writelines(res.text)
                                    f.close() 
                            else:
                                url = f"https://s3-symbol-logo.tradingview.com/crypto/XTVCUSDT.svg"
                                res = requests.get(url)
                                with open(f"{get_real_path()}/{str(first_symbol[0]).lower()}.svg", "w") as f:
                                    f.writelines(res.text)
                                    f.close() 
                    else:
                        AppLogger.writer("INFO", f"{exchange_id} {symbol} dont have /")
                AppLogger.writer("INFO", f"{exchange_id} {symbol} LOADED >>> DONE")
                AppConfig.sig_set_single_data.emit((f"topbar.symbol.{exchange_id}",self._list_symbols))
        except Exception as e:
            traceback.print_exception(e)
        await exchange.close()
        crypto_ex.deleteLater()

    async def get_symbol(self,exchange_id,update_signal):
        self._list_symbols = AppConfig.get_config_value(f"topbar.symbol.{exchange_id}",[])

        if self._list_symbols == []:
            crypto_ex = CryptoExchange(self)
            exchange = crypto_ex.setupEchange(exchange_name=exchange_id)
            try:
                await exchange.load_markets()
                markets = []
                for market in list(exchange.markets.keys()):
                    if exchange.markets[market]['active'] == True:
                        markets.append(exchange.markets[market]['symbol'])
                # markets = exchange.symbols
                if markets != []:
                    symbols = [re.findall(r'(.*?):', market)[0] for market in markets if re.findall(r'(.*?):', market) != []]
                    if symbols == []:
                        symbols = [market for market in markets if re.findall(r'(.*?):', market) == []]

                    for symbol in  symbols:
                        if "/" in symbol:
                            first_symbol = re.findall(r'(.*?)/', symbol)
                            if check_icon_exist(first_symbol[0]):
                                if symbol not in self._list_symbols:
                                    self._list_symbols.append(symbol)
                            else:
                                "đây là chỗ tìm coin chưa có icon để bổ sung"
                                pass
                    AppConfig.sig_set_single_data.emit((f"topbar.symbol.{exchange_id}",self._list_symbols))
                    
                    update_signal.emit([self._list_symbols,exchange_id])
                    #QCoreApplication.processEvents()
            except Exception as e:
                traceback.print_exception(e)
            await exchange.close()
            crypto_ex.deleteLater()
        else:
            update_signal.emit([self._list_symbols,exchange_id])
            #QCoreApplication.processEvents()
          
    def add_symbol(self, data):
        self.dict_favorites = AppConfig.get_config_value(f"topbar.symbol.favorite")
        symbols,exchange = data[0], data[1]
        if self.exchange_id == "favorite":
            n = len(symbols)
        else:
            if len(symbols) > 50:
                n = 50
            else:
                n = len(symbols)
        for symbol in symbols[:n]:
            item = Symbol_Item(self.sig_add_remove_favorite,self.sig_change_symbol,symbol,exchange,self)
            if self.exchange_id in list(self.dict_favorites.keys()):
                    _list_symbols = self.dict_favorites[self.exchange_id]
                    if symbol in _list_symbols:
                        item.btn_fovarite.added_to_favorite()
            self.sig_add_item.emit(item)
            QCoreApplication.processEvents()
        self.isAdded = True
        self.sig_update_symbols.emit(exchange)
        self.sig_show_process.emit(False)
    def update_symbol(self,n):
        self.dict_favorites = AppConfig.get_config_value(f"topbar.symbol.favorite")
        if self.exchange_id == "favorite":
            return
        self.loading = True
        symbols = []
        if  n+50 < len(self._list_symbols):
            symbols = self._list_symbols[n:n+50]
        else:
            if n < len(self._list_symbols):
                symbols = self._list_symbols[n:]
        for symbol in symbols:
            item = Symbol_Item(self.sig_add_remove_favorite,self.sig_change_symbol,symbol,self.exchange_id,self)
            if self.exchange_id in list(self.dict_favorites.keys()):
                    _list_symbols = self.dict_favorites[self.exchange_id]
                    if symbol in _list_symbols:
                        item.btn_fovarite.added_to_favorite()
            self.sig_add_item.emit(item)
            QCoreApplication.processEvents()
            #time.sleep(0.01)
        self.loading = False
        self.sig_show_process.emit(False)

    def eventFilter(self, obj, e: QEvent):
        if e.type() == QEvent.Wheel:
            _widgets = self.vBoxLayout.get_widgets()
            n = len(_widgets)
            if self.old_vertival_val == None:
                self.old_vertival_val = self.verticalScrollBar().value()
            elif self.old_vertival_val < self.verticalScrollBar().value():
                self.old_vertival_val = self.verticalScrollBar().value()
            # elif self.old_vertival_val > self.verticalScrollBar().value():
            #     self.old_vertival_val = self.verticalScrollBar().value()
            elif self.old_vertival_val >= self.verticalScrollBar().maximum()-60:
                self.old_vertival_val = self.verticalScrollBar().value()
                if not self.loading and self.exchange_id!="favorite":
                    self.sig_show_process.emit(True)
                    self.sig_update_symbol.emit(n)
                    #QCoreApplication.processEvents()
                    #self.old_vertival_val = None
            if e.angleDelta().y() < 0:
                self.delegate.vScrollBar.scrollValue(60)
            if e.angleDelta().y() > 0:
                self.delegate.vScrollBar.scrollValue(-60)
            else:
                self.delegate.hScrollBar.scrollValue(-e.angleDelta().x())
            e.setAccepted(True)
            return True
        return super().eventFilter(obj, e)

class ListSymbolMenuByExchange(QStackedWidget):
    sig_add_remove_favorite = Signal(tuple)
    sig_add_basemenu = Signal(object)
    def __init__(self,sig_change_symbol,parent:QWidget=None):
        super(ListSymbolMenuByExchange,self).__init__(parent)
        self.setContentsMargins(0,0,0,0)
        _exchanges =  list_exchanges.__dict__
        self._list_menu:List[BaseMenu] = []
        self.sig_add_basemenu.connect(self.addWidget,Qt.ConnectionType.AutoConnection)
        #print(_exchanges)
        for exchange in list(_exchanges.values()):
            menu = BaseMenu(self.sig_add_remove_favorite,sig_change_symbol,self,exchange)
            self._list_menu.append(menu)
            self.sig_add_basemenu.emit(menu)
            #QCoreApplication.processEvents()
        #self.setSpacing(0)
        self.changePage("favorite")
        self.sig_add_remove_favorite.connect(self.add_remove_favorite_item,Qt.ConnectionType.AutoConnection)
    
    def add_remove_favorite_item(self,item_data):
        """(bool, ("change_symbol",symbol,self.exchange_id,exchange_name,symbol_icon_path,echange_icon_path,_mode))"""
        is_add = item_data[0]
        data = item_data[1]
        symbol = data[1]
        exchange_id = data[2]
        favorite_menu =  self.get_exchange_menu("favorite")
        exchange_menu =  self.get_exchange_menu(exchange_id)
        exchange_menu.add_remove_favorite_item(is_add,symbol,exchange_id)
        favorite_menu.add_remove_favorite_item(is_add,symbol,exchange_id)

    def get_exchange_menu(self,exchange_name:str)->'BaseMenu':
        return self.findChild(BaseMenu,exchange_name)
        # for i in range(self.count()):
        #     if self.widget(i).objectName() == exchange_name:
        #         return self.widget(i)
        # return None
    def setCurrentWidget(self, widget):
        return super().setCurrentWidget(widget)
    # def setCurrentIndex(self, index, popOut=False):
    #     return super().setCurrentIndex(index, popOut)
    def changePage(self,exchange_name):
        #print(item_name)
        _wg = self.get_exchange_menu(exchange_name)
        if isinstance(_wg,BaseMenu):
            self.setCurrentWidget(_wg)
            if not _wg.is_get_symbol or exchange_name != "favorite":
                _wg.get_all_symbols_by_exchange(exchange_name)
            
class MainMenu(HWIDGET):
    def __init__(self,sig_change_symbol,parent:QWidget=None):
        super(MainMenu,self).__init__(parent)
        #self.setSpacing(0)
        #self.setContentsMargins(0,0,0,0)
        self.ListSymbols = ListSymbolMenuByExchange(sig_change_symbol,self)
        self.rightmenu = RightMenu(self.ListSymbols)
        self.rightmenu.setMinimumWidth(300)
        self.addWidget(self.rightmenu)
        self.addSeparator(_type = "VERTICAL",w=2,h=self.parent().height())
        self.addWidget(self.ListSymbols)
        
        # for menu in self.ListSymbols._list_menu:
        #     # if menu.exchange_id == "favorite":
        #     menu.load_favorite()

class SymbolSearchMenu(MovingWidget):
    def __init__(self,sig_remove_menu,sig_change_symbol,parent:QWidget=None):
        super(SymbolSearchMenu, self).__init__(parent,"Search Symbol")
        self.title.btn_close.clicked.connect(sig_remove_menu,Qt.ConnectionType.AutoConnection)
        self.setFixedSize(700,700)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        #self.setFixedWidth(700)
        #self.setSpacing(2)
        self.search_box = SearchLineEdit(self)
        self.search_box.setFixedHeight(35)
        self.addWidget(self.search_box)
        self.main_menu = MainMenu(sig_change_symbol,self)
        self.addWidget(self.main_menu)
        sig_change_symbol.connect(self.remove_menu)
        FluentStyleSheet.INDICATORMENU.apply(self)
    def remove_menu(self,data):
        self.title.btn_close.clicked.emit()