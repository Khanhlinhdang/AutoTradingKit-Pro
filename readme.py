from PySide6.QtCore import QUrl, Qt, QSettings
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLineEdit, QFileDialog, QPushButton, QMenu
from PySide6.QtGui import QAction
from PySide6.QtWebEngineWidgets import QWebEngineView


class ReadmeViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Readme Viewer")
        self.setGeometry(0, 28, 1000, 750)
        self.layout = QVBoxLayout(self)
        self.webView = QWebEngineView()
        self.webView.settings().setAttribute(self.webView.settings().WebAttribute.PluginsEnabled, True)
        self.webView.settings().setAttribute(self.webView.settings().WebAttribute.PdfViewerEnabled, True)
        self.layout.addWidget(self.webView)
        self.webView.setUrl(QUrl("file:///" + "readme.pdf".replace('\\', '/')))
        


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    win = ReadmeViewer()
    win.show()
    sys.exit(app.exec())


# Works - tested on txt, htm/html, images, svg, pdf, and mp3