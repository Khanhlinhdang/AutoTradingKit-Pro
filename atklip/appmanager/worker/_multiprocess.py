from PySide6 import QtCore
from PySide6.QtCore import Signal,Slot
import multiprocess as mp

class LoadDataBaseSignal(QtCore.QObject):
    sendStatusBarMessage = Signal(str, str)

class LoadDataBaseThread(QtCore.QRunnable):
    def __init__(self, databaseAbsPath:str,
                       progressBarId: int):

        super(LoadDataBaseThread, self).__init__()

        self.signal = LoadDataBaseSignal()

        self.databaseAbsPath = databaseAbsPath
        self.progressBarId     = progressBarId

        # If set to True, stop the run
        self._stop = False

    @Slot()
    def run(self):
        self.signal.sendStatusBarMessage.emit('Gathering runs informations', 'orange')
        # Queue will contain the numpy array of the run data
        queueData: mp.Queue = mp.Queue()
        queueDone: mp.Queue = mp.Queue()
        self.worker = mp.Process(target=getRunInfosmp,
                                 args=(self.databaseAbsPath,
                                       queueData))
        self.worker.start()

        done = False
        while not done:
            QtCore.QThread.msleep(config['delayBetweenProgressBarUpdate'])
            # We check if the thread ias being stopped
            if self._stop:
                return
            progressBar = queueProgressBar.get()
            queueProgressBar.put(progressBar)

            self.signal.updateProgressBar.emit(self.progressBarId, progressBar, 'Loading database: {:.0f}%'.format(progressBar))
            done = queueDone.get()
            queueDone.put(done)
        runInfos: dict = queueData.get()
        queueData.close()
        queueData.join_thread()
        queueDone.close()
        queueDone.join_thread()
        self.worker.join()

        # We check if the thread ias being stopped
        if self._stop:
            return
