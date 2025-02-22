from random import randrange
from PySide6 import QtCore, QtGui, QtWidgets

class Loader(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__(parent)

        self.gradient = QtGui.QConicalGradient(.5, .5, 0)
        self.gradient.setCoordinateMode(QtGui.QGradient.CoordinateMode.ObjectBoundingMode)
        self.gradient.setColorAt(.25, QtCore.Qt.transparent)
        self.gradient.setColorAt(.75, QtCore.Qt.transparent)

        self.animation = QtCore.QVariantAnimation(
            startValue=0., endValue=1., 
            duration=1000, loopCount=-1, 
            valueChanged=self.updateGradient
            )

        self.stopTimer = QtCore.QTimer(singleShot=True, timeout=self.stop)

        self.focusWidget = None
        self.hide()
        parent.installEventFilter(self)

    def start(self, timeout=None):
        self.show()
        self.raise_()
        self.focusWidget = QtWidgets.QApplication.focusWidget()
        self.setFocus()
        if timeout:
            self.stopTimer.start(timeout)
        else:
            self.stopTimer.setInterval(0)

    def stop(self):
        self.hide()
        self.stopTimer.stop()
        if self.focusWidget:
            self.focusWidget.setFocus()
            self.focusWidget = None

    def updateGradient(self, value):
        self.gradient.setAngle(-value * 360)
        self.update()

    def eventFilter(self, source, event):
        # ensure that we always cover the whole parent area
        if event.type() == QtCore.QEvent.Resize:
            self.setGeometry(source.rect())
        return super().eventFilter(source, event)

    def showEvent(self, event):
        self.setGeometry(self.parent().rect())
        self.animation.start()

    def hideEvent(self, event):
        # stop the animation when hidden, just for performance
        self.animation.stop()

    def paintEvent(self, event):
        qp = QtGui.QPainter(self)
        # qp.setRenderHints(qp.Antialiasing)
        color = self.palette().window().color()
        color.setAlpha(max(color.alpha() * .5, 128))
        qp.fillRect(self.rect(), color)

        text = 'Loading...'
        interval = self.stopTimer.interval()
        if interval:
            remaining = int(max(0, interval - self.stopTimer.remainingTime()) / interval * 100)
            textWidth = self.fontMetrics().width(text + ' 000%')
            text += ' {}%'.format(remaining)
        else:
            textWidth = self.fontMetrics().width(text)
        textHeight = self.fontMetrics().height()
        # ensure that there's enough space for the text
        if textWidth > self.width() or textHeight * 3 > self.height():
            drawText = False
            size = max(0, min(self.width(), self.height()) - textHeight * 2)
        else:
            size = size = min(self.height() / 3, max(textWidth, textHeight))
            drawText = True

        circleRect = QtCore.QRect(0, 0, size, size)
        circleRect.moveCenter(self.rect().center())

        if drawText:
            # text is going to be drawn, move the circle rect higher
            circleRect.moveTop(circleRect.top() - textHeight)
            middle = circleRect.center().x()
            qp.drawText(
                middle - textWidth / 2, circleRect.bottom() + textHeight, 
                textWidth, textHeight, 
                QtCore.Qt.AlignCenter, text)

        self.gradient.setColorAt(.5, self.palette().windowText().color())
        qp.setPen(QtGui.QPen(self.gradient, textHeight))
        qp.drawEllipse(circleRect)


class LoadingExtension(object):
    # a base class to extend any QWidget subclass's top level window with a loader
    def startLoading(self, timeout=0):
        window = self.window()
        if not hasattr(window, '_loader'):
            window._loader = Loader(window)
        window._loader.start(timeout)

        # this is just for testing purposes
        if not timeout:
            QtCore.QTimer.singleShot(randrange(1000, 5000), window._loader.stop)

    def loadingFinished(self):
        if hasattr(self.window(), '_loader'):
            self.window()._loader.stop()


class Test(QtWidgets.QWidget, LoadingExtension):
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QGridLayout(self)

        # just a test widget
        textEdit = QtWidgets.QTextEdit()
        layout.addWidget(textEdit, 0, 0, 1, 2)
        textEdit.setMinimumHeight(20)

        layout.addWidget(QtWidgets.QLabel('Timeout:'))
        self.timeoutSpin = QtWidgets.QSpinBox(maximum=5000, singleStep=250, specialValueText='Random')
        layout.addWidget(self.timeoutSpin, 1, 1)
        self.timeoutSpin.setValue(2000)

        btn = QtWidgets.QPushButton('Start loading...')
        layout.addWidget(btn, 2, 0, 1, 2)
        btn.clicked.connect(lambda: self.startLoading(self.timeoutSpin.value()))


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    test = Test()
    test.show()
    sys.exit(app.exec_())