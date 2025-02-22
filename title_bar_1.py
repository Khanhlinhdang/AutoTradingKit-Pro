import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QTabBar, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QMimeData, QPoint
from PySide6.QtGui import QDrag


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
        self.tab_bar.setAcceptDrops(True)
        # self.tab_bar.setDragEnabled(True)
        # self.tab_bar.setDragDropMode(QTabBar.DragDrop)
        
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
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return
        
        # Lấy index của tab được kéo
        tab_index = self.tab_bar.tabAt(self.drag_start_position)
        if tab_index == -1:
            return
        
        # Tạo QDrag object
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(f"tab_{tab_index}")
        drag.setMimeData(mime_data)
        
        # Thực hiện drag
        drag.exec(Qt.MoveAction)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
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
        self.tab_content = QLabel("Content of Tab 1")
        self.layout.addWidget(self.tab_content)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasText() and event.mimeData().text().startswith("tab_"):
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        if event.mimeData().hasText() and event.mimeData().text().startswith("tab_"):
            # Tạo một MainWindow mới
            new_window = MainWindow()
            new_window.show()
            
            # Di chuyển tab từ cửa sổ cũ sang cửa sổ mới
            tab_index = int(event.mimeData().text().split("_")[1])
            tab_text = self.title_bar.tab_bar.tabText(tab_index)
            self.title_bar.tab_bar.removeTab(tab_index)
            new_window.title_bar.tab_bar.addTab(tab_text)
            
            # Di chuyển nội dung tab
            new_window.tab_content.setText(self.tab_content.text())
            self.tab_content.setText("")
            
            event.acceptProposedAction()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())