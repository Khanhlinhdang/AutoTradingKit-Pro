from concurrent.futures import Future
from typing import Optional
from psygnal import Signal
from .threadpool import Heavy_ProcessPoolExecutor_global, ThreadPoolExecutor_global

class HeavyProcess():
    update_signal = Signal(object)
    finished_signal = Signal()
    def __init__(self,fn:callable=None,callback:Optional[callable]=None, *args, **kwargs):
        self.fn = fn
        self.callback = callback
        self.args = args
        self.kwargs = kwargs.copy()
        self.executor = Heavy_ProcessPoolExecutor_global
    #     self.thread = ThreadPoolExecutor_global

    # def start(self):
    #     self.thread.submit(
    #         self.process
    #     )
    def start(self):
        self.future = self.executor.submit(
            self.fn,
            *self.args, 
            **self.kwargs
        )
        if self.callback:
            # self.callback(self.future)
            self.future.add_done_callback(self.callback)
        else:
            # self._callback(self.future)
            self.future.add_done_callback(self._callback)
            
    def _callback(self, future: Future):
        # print(future.result())
        self.update_signal.emit(future.result())
        return future.result()


class ReturnProcess():
    def __init__(self,fn:callable=None, *args, **kwargs):
        self.fn = fn
        self.args = args
        self.kwargs = kwargs.copy()
        self.executor = Heavy_ProcessPoolExecutor_global
    def get(self):
        self.future = self.executor.submit(
            self.fn,
            *self.args, 
            **self.kwargs
        )
        data = self.future.result()
        print(data)
        return data
            


