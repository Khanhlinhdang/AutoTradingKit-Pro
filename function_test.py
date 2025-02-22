import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QTabBar, QWidget, QVBoxLayout, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt

class BrowserTitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        
        # Layout chính
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Tab bar
        self.tab_bar = QTabBar()
        self.tab_bar.setShape(QTabBar.RoundedNorth)
        self.tab_bar.setMovable(True)
        self.tab_bar.setTabsClosable(True)
        self.tab_bar.tabCloseRequested.connect(self.close_tab)
        
        # Thêm nút thêm tab
        self.add_tab_button = QPushButton("+")
        self.add_tab_button.setFixedSize(30, 30)
        self.add_tab_button.clicked.connect(self.add_tab)
        
        # Thêm các widget vào layout
        self.layout.addWidget(self.tab_bar)
        self.layout.addWidget(self.add_tab_button)
        
        # Thêm tab mặc định
        self.add_tab()
    
    def add_tab(self):
        index = self.tab_bar.addTab(f"Tab {self.tab_bar.count() + 1}")
        self.tab_bar.setCurrentIndex(index)
    
    def close_tab(self, index):
        self.tab_bar.removeTab(index)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowTitle("Custom Title Bar")
        self.setGeometry(100, 100, 800, 600)
        
        # Tạo custom title bar
        self.title_bar = BrowserTitleBar(self)
        self.setMenuWidget(self.title_bar)
        
        # Nội dung chính của cửa sổ
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Layout chính
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.addWidget(QPushButton("Button 1"))
        self.layout.addWidget(QPushButton("Button 2"))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())