# TODO: PySide6/PyQt5 to PyQt6 conversion
# -> In order to call "Window" or "WindowText" in QPallete, you need to use the enum "ColorRole" 
#   like this: (QtGui.QPalette.ColorRole.Window) = read here: https://doc.qt.io/qt-6/qpalette.html
#
# -> "qtc.Qt.white" does not work anymore in PyQt6, use the enum "GlobalColor"
#   like this: (QtCore.Qt.GlobalColor.black) = read here: https://doc.qt.io/qt-6/qt.html
#   
# -> error: AttributeError: type object 'Qt' has no attribute 'FramelessWindowHint'. solution: use enum "WindowType"
#   like this: (QtCore.Qt.WindowType.FramelessWindowHint) = read here: https://stackoverflow.com/questions/69747328/pyqt6-attributeerror-qt
#
# -> error: AttributeError: type object 'Qt' has no attribute 'AlignCenter'. solution: use enum "AlignmentFlag" 
#   like this: (QtCore.Qt.AlignmentFlag.AlignCenter) = read here: https://doc.qt.io/qt-6/qt.html#AlignmentFlag-enum
#
# -> error: AttributeError: type object 'QSizePolicy' has no attribute 'Expanding'. solution: use enum "Policy"
#   like this: (QtWidgets.QSizePolicy.Policy.Expanding) = read here: https://doc.qt.io/qt-6/qsizepolicy.html


import sys
from PySide6 import QtWidgets as qtw
from PySide6 import QtCore as qtc
from PySide6 import QtGui as qtg
from pathlib import Path


class TitleBar(qtw.QWidget):
    height = 35
    def __init__(self, parent):
        super(TitleBar, self).__init__(parent)

        self.nav_maximize = """
            QToolButton[accessibleName="btn_max"] {
                image: url(./icons/nav_maximize.png);
                background: #1c2028;
                border: nobutton_stylene;
                padding-right: 3px; 
            }
            QToolButton[accessibleName="btn_max"]:hover {
                image: url(./icons/colored_maximize.png);
                background: #1c2028;
                border: none;
            }
        """

        self.nav_normal =  """
                QToolButton[accessibleName="btn_max"]{
                    image: url(./icons/nav_normal.png);
                    background: #1c2028;
                    border: none;
                    
                }
                QToolButton[accessibleName="btn_max"]:hover{
                    image: url(./icons/colored_normal.png);
                    background: #1c2028;
                    border: none;
                    
                }
            """

        ### for window movement ###
        self.prevGeo = self.geometry() # save window geometry: QtCore.QRect(int x, int y, int width, int height)
        self.pressing = False
        self.maximizedWindow=False
        ### [ end ] ###
        
        self.current_editor = self.parent().create_editor()
        self.current_editor.setFocus()
        self.text_editors = []
        self.tabs = qtw.QTabWidget()
        self.tabs.setTabsClosable(True) 
        self.tabs.tabBar().setMovable(True)

        self.parent()._createActions()
        self.parent()._connectActions()
        
        self.layout = qtw.QHBoxLayout()
        self.layout.setContentsMargins(0,0,10,0) 
        
        self.menubar = qtw.QMenuBar()
  
        file_menu = self.menubar.addMenu('File')
        file_menu.addAction(self.parent().new_action)
        file_menu.addAction(self.parent().open_action)
        file_menu.addSeparator()
        file_menu.addAction(self.parent().exit_action)

        self.layout.addWidget(self.menubar) 

        self.window_title = qtw.QLabel("Visual Studio Code") # Notes
        self.window_title.setAlignment(qtc.Qt.AlignmentFlag.AlignCenter)
        self.window_title.setAccessibleName("lbl_title") 
        self.window_title.setFixedHeight(self.height)
        self.layout.addStretch(1) # this stretches the self.window_title qlabel to take-up all the remaining space
        self.layout.addWidget(self.window_title)

        self.setSizePolicy(qtw.QSizePolicy.Policy.Expanding, qtw.QSizePolicy.Policy.Fixed)
        self.maximizedWindow=False
       
        self.closeButton = qtw.QToolButton() 
        self.closeButton.setAccessibleName("btn_close")                           
        self.closeButton.clicked.connect(self.onClickClose)

        self.maxButton = qtw.QToolButton()
        self.maxButton.setAccessibleName("btn_max")  
        self.maxButton.setStyleSheet(self.nav_maximize)
        self.maxButton.clicked.connect(self.showMaxRestore)

        self.hideButton = qtw.QToolButton()
        self.hideButton.setAccessibleName("btn_min")  
        self.hideButton.clicked.connect(self.onClickHide)

        self.layout.addWidget(self.hideButton)
        self.layout.addWidget(self.maxButton)
        self.layout.addWidget(self.closeButton)
        self.setLayout(self.layout)

    #####################################################
    ## TITLE BAR MINIMIZE, MAXIMIZE, CLOSE METHODS
    #####################################################
    def onClickClose(self):
        main.close()
            
    def onClickHide(self):
        main.showMinimized()

    def showMaxRestore(self):
        # QWidget.showNormal() # https://doc.qt.io/qt-6/qwidget.html#showNormal
        #-- Restores the widget after it has been maximized or minimized.
        if(self.maximizedWindow):
            # self.prevGeo = self.geometry() 
            main.showNormal()
            self.maximizedWindow = False
            self.maxButton.setStyleSheet(self.nav_maximize)
        else:
        # QWidget.showMaximized() # https://doc.qt.io/qt-6/qwidget.html#showMaximized
        #-- Shows the widget maximized.
            self.prevGeo = self.geometry() # save current window geometry. this helps with centering the mouse cursor in the titlebar
            main.showMaximized()
            self.maximizedWindow = True
            self.maxButton.setStyleSheet(self.nav_normal)
    
    # EVENT FUNCTIONS
    # window will maximize if mouse cursor is positioned at less then 10 pixels in y-coordinate
    def mouseReleaseEvent(self, event):
        if event.globalPosition().toPoint().y() < 10:
            self.showMaxRestore() # maximize window
            return

    def mousePressEvent(self, event):
        # getting previous mouse x and y coordinates
        self.prevMousePos = event.scenePosition() # coordinates of prev mouse position
        # print("previous mouse pos",self.prevMousePos)
        self.pressing = True
        
        if event.type() == qtc.QEvent.Type.MouseButtonDblClick:
            self.showMaxRestore()
            return

    def mouseMoveEvent(self, event): # this is responsible for the mouse drag on title bar

        if(self.maximizedWindow): 
        # if the window is moved while maximized, 
        # it is automatically returned to its normal state upon mouse drag
                main.showNormal()
                self.maximizedWindow= False
                self.maxButton.setStyleSheet(self.nav_maximize)
                # mouse cursor re-positioning on the window
                self.prevMousePos = qtc.QPointF((self.prevGeo.width()*.5), (self.prevGeo.height()*.5)) # setting the mouse position to be exactly at the center of the titlebar

        if self.pressing: # this is for moving the window
            # GLOBAL POSITION: https://stackoverflow.com/questions/67723421/deprecationwarning-function-when-moving-app-removed-titlebar-pyside6
            mousePosition = event.globalPosition()
            print("mousePosition",mousePosition)
            pos = mousePosition-self.prevMousePos
            # "toPoint()" rounds the the float value of QPointF to the nearest integer
            x = pos.toPoint().x()
            y = pos.toPoint().y() 
            main.move(x,y) # .move() only accepts integer values that's why we use .toPoint()

      
    #####################################################
    ##                      END
    #####################################################


class MainWindow(qtw.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.statusbar = self.statusBar()
        self.statusbar.showMessage("Ready")

        self.current_editor = self.create_editor()
        self.current_editor.setFocus()
        self.text_editors = []

        # WINDOW FLAGS: https://doc.qt.io/qtforpython/overviews/qtwidgets-widgets-windowflags-example.html?highlight=windowminimizebuttonhint
        self.setMinimumSize(400,250)
        self.resize(700,500)
        self.setWindowFlags(qtc.Qt.WindowType.FramelessWindowHint|
                            qtc.Qt.WindowType.WindowMaximizeButtonHint|
                            qtc.Qt.WindowType.WindowMinimizeButtonHint |
                            qtc.Qt.WindowType.WindowStaysOnTopHint  # make window on top of taskbar
                            )

        self.title_bar  = TitleBar(self)
        self.tabs = qtw.QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabBar().setMovable(True)
        self.tabs.tabCloseRequested.connect(self.remove_editor)
        self.tabs.currentChanged.connect(self.change_text_editor)
        self.tabs.tabBar().setMovable(True)
        
        self._createToolBars()
        
        # Cannot set QxxLayout directly on the QMainWindow
        # Need to create a QWidget and set it as the central widget
        widget = qtw.QWidget()
        layout = qtw.QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.title_bar,1)
        layout.addWidget(self.file_toolbar,2)
        layout.addWidget(self.tabs,3)
        layout.setSpacing(0) 
        widget.setLayout(layout)
     
        self.setCentralWidget(widget)
        self.new_tab()
        self.closeTab()
        self._createActions()
        self._connectActions()

    def create_editor(self):
        current_editor = qtw.QTextEdit()
        # Set the tab stop width to around 33 pixels which is
        # about 8 spaces
        current_editor.setTabStopDistance(33)
        return current_editor

    def change_text_editor(self, index):
        if index < len(self.text_editors):
            self.current_editor = self.text_editors[index]

    def remove_editor(self, index):
        if self.tabs.count() < 2: 
            return True

        self.tabs.removeTab(index)
        if index < len(self.text_editors):
            del self.text_editors[index]
        
    def closeTab(self): 
        close_tab = qtg.QShortcut(qtg.QKeySequence("Ctrl+W"), self)
        close_tab.activated.connect(lambda:self.remove_editor(self.tabs.currentIndex()))

    def close(self): # close entire program
        qtw.QApplication.quit()

    def new_tab(self, checked = False, title = "Untitled.txt"):
        self.widget = qtw.QMainWindow()
        self.tabs.addTab(self.widget, title)
        self.tabs.setCurrentWidget(self.current_editor) # set the current tab selected as current widget
        
        self.current_editor = self.create_editor() # create a QTextEdit
        self.text_editors.append(self.current_editor) # add current editor to the array list 
        self.widget.setCentralWidget(self.current_editor)
    
    def open_document(self):
        # guide on pyqt6: QFileDialog = read here: https://zetcode.com/pyqt6/dialogs/
        home_dir = str(Path.home())
        self.filename, _ = qtw.QFileDialog.getOpenFileName(
            self, 'Open File',".",
            "Text Files (*.txt);;Python Files (*.py)",
            home_dir
        )
        if self.filename:
            with open(self.filename,"rt") as file:
                content = file.read()
                self.current_editor = self.create_editor() 
                currentIndex = self.tabs.addTab(self.current_editor, str(self.filename))   # use that widget as the new tab
                self.current_editor.setText(content) # set the contents of the file as the text
                self.tabs.setCurrentIndex(currentIndex) # make current opened tab be on focus
                
    def _createToolBars(self):
        # create toolbars
        self.file_toolbar = self.addToolBar("File")
        self.file_toolbar.setIconSize(qtc.QSize(22,22))
        self.file_toolbar.addAction(self.new_action)
        self.file_toolbar.addAction(self.open_action)
        
    def _createActions(self): 
        # FILE MENU
        self.new_action = qtg.QAction(qtg.QIcon("./icons/new_file.png"),"New", self)
        self.open_action = qtg.QAction(qtg.QIcon("./icons/folder.png"),"Open", self)
        self.exit_action = qtg.QAction(qtg.QIcon("./icons/close.png"), "Exit", self)
   
        self.new_action.setShortcut("Ctrl+N")
        self.open_action.setShortcut("Ctrl+O")
        self.exit_action.setShortcut("Ctrl+Shift+Q")

        self.new_action.setToolTip("New file")
        self.open_action.setToolTip("Open a file")
        self.exit_action.setToolTip("Exit Program")

    def _connectActions(self):
        # Connect File actions
        self.new_action.triggered.connect(self.new_tab)
        self.open_action.triggered.connect(self.open_document)
        self.exit_action.triggered.connect(self.close)


if __name__ == "__main__":
    app = qtw.QApplication(sys.argv)
    app.setStyle(qtw.QStyleFactory.create("Fusion")) # ['windowsvista', 'Windows', 'Fusion']
    print(qtw.QStyleFactory.keys())
    # DARKER COLOR OR LIGHTER: https://pinetools.com/darken-color
    # COLOR READABILITY CHECKER: https://coolors.co/contrast-checker/dfdcd1-1c2028
    # QPallete documentation: https://doc.qt.io/qt-6/qpalette.html
    palette = qtg.QPalette()
    palette.setColor(qtg.QPalette.ColorRole.Window, qtg.QColor("#1c2028")) # general background color
    palette.setColor(qtg.QPalette.ColorRole.WindowText, qtg.QColor("#BFBDB6")) # for the window title
    palette.setColor(qtg.QPalette.ColorRole.Button, qtg.QColor("#1c2028")) # overflow buttons color for the qtabbar
    palette.setColor(qtg.QPalette.ColorRole.Window, qtg.QColor("#1c2028")) # menu border color
    palette.setColor(qtg.QPalette.ColorRole.Text, qtg.QColor("#BFBDB6")) # menu unhighlited text color
    palette.setColor(qtg.QPalette.ColorRole.Base, qtg.QColor("#1c2028")) # menu unhighlited bg color
    palette.setColor(qtg.QPalette.ColorRole.Highlight, qtg.QColor("#0086b6")) # menu mouse hover highlight color 
    palette.setColor(qtg.QPalette.ColorRole.HighlightedText, qtg.QColor("#000000")) # menu highlighted text color 
    app.setPalette(palette)
    main = MainWindow()
    main.setStyleSheet(
         """
            /* css styling properties: https://www.w3schools.com/cssref/pr_border-bottom_style.asp */
            
            QMainWindow{ border-style: none;}
            QStatusBar { color: #BFBDB6; background: #1c2028; }
            QMenuBar::item:pressed {  color: #BFBDB6; background: #1c2028; }
            QMenuBar::item { color: #BFBDB6; background: #1c2028; }
            
            /* styling Qmenu: https://doc.qt.io/qt-5/stylesheet-examples.html#customizing-qmenu */
            
            QTextEdit QMenu::item {color: #BFBDB6; font-weight: normal;} /* for context menu> right click -> textedit*/
            QTextEdit QMenu::item:selected { /* when user selects item using mouse or keyboard */
                background-color: #0086b6;
                color: #000;
            }
            
            QTabWidget::pane { border: none; }
            QTabBar::tab { border: none; }
            QTabBar::tab:top:selected { background: #161a21;}
            QTabBar::tab:top:!selected { background: #1c2028; }
            QTabBar::close-button { image: url(./icons/close_default.png); margin: 2px}
            QTabBar::close-button:hover { image: url(./icons/close_active.png);  margin: 2px}
            QTabBar::tab:selected {
                color: #ffb454;
                background: #1c2028;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            
            QTabBar::tab:!selected {
                color: #BFBDB6;
                background: #1c2028;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:top, QTabBar::tab:bottom {
                min-width: 8ex;
                margin-right: -1px;
                padding: 5px 10px 5px 10px;
            }
            QTextEdit
            {
                border: none;
                font: "Consolas";
                color: #BFBDB6;
                background: #161a21;
                selection-background-color: #ffb454;
                selection-color: #000000;
            }
            QMenuBar
            {
                color: #BFBDB6;
                background: #1c2028;
                border: none;
                border-style: none;
            }
            QMenuBar::item:selected 
            { 
                color: #BFBDB6;
                background: #1c2028; 
            } 
            QToolBar
            {
                background: #1c2028;
                border: none;
                border-style: none;
            }
            /*  -----------------------------//
                -  The css below affects the QToolbar buttons (or any QToolButton)
                -----------------------------//
            */
                QToolButton::hover{
                background-color: #1c2028;
            }
            /*  ---------- [end] ------------*/

                QToolButton[accessibleName="btn_max"]{
                image: url(./icons/nav_normal.png);
                background: #1c2028;
                border: none;  
            }
            QToolButton[accessibleName="btn_max"]:hover{
                image: url(./icons/colored_normal.png);
                background: #1c2028;
                border: none;
            }
            QToolButton[accessibleName="btn_max"] {
                image: url(./icons/nav_maximize.png);
                background: #1c2028;
                border: nobutton_stylene;
                padding-right: 3px; 
            }
            QToolButton[accessibleName="btn_max"]:hover {
                image: url(./icons/colored_maximize.png);
                background: #1c2028;
                border: none;
            }
            QMenuBar{
                color: #fff;
                font: "Consolas";
                font-size: 14px;
                padding: 3px; 
            }
            QLabel[accessibleName="lbl_title"]{
                background-color: #1c2028; 
                font-size: 13px;
                font: "Consolas";
                padding-right: 425px;
            }
            QToolButton[accessibleName="btn_close"] {
                image: url(./icons/nav_close.png);
                background: #1c2028;
                border: none;
            }
            QToolButton[accessibleName="btn_close"]:hover {
                image: url(./icons/colored_close.png);
                background: #1c2028;
                border: none;
            }    
            QToolButton[accessibleName="btn_min"] {
                image: url(./icons/nav_minimize.png);
                background: #1c2028;
                border: none;
                padding-right: 3px;
            }
            QToolButton[accessibleName="btn_min"]:hover {
                image: url(./icons/colored_minimize.png);
                background: #1c2028;
                border: none;
                padding-right: 3px;
            }
            QScrollBar:vertical {
                border: none;
                width: 14px;
                margin: 0px 0 0px 0;
                background-color: #1c2028;
                border-radius: 0px;
            }
            QScrollBar:handle:vertical {
                background-color: #292c35;
            }
            QScrollBar:handle:vertical:hover {
                background-color: #4c4a4a;
            }
            QScrollBar:handle:vertical:pressed {
                background-color: #5c5b5b;
            }
            QScrollBar:horizontal {
                border: none;
                height: 14px;
                margin: 0px 0 0 0;
                background-color: #1c2028;
                border-radius: 0px;
            }
            QScrollBar:handle:horizontal {
                background-color: #292c35;
            }
            QScrollBar:handle:horizontal:hover {
                background-color: #4c4a4a;
            }
            QScrollBar:handle:horizontal:pressed {
                background-color: #5c5b5b;
            }
            /*  -----------------------------//
                -  The css below removes the QScrollBar's Arrow keys both aesthetically AND functionally
                -----------------------------//
            */
            QScrollBar::left-arrow:horizontal, QScrollBar::right-arrow:horizontal,
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal{
                border: none;
                background-color: none;
                color: none;
                width:0px;
                height:0px;
            }
            QScrollBar::sub-line, QScrollBar::add-line{
                border: none;
                background-color: none;
                width:0px;
                height:0px;
            }
            /*  ---------- [end] ----------  */
        """
    )
    main.show()
    sys.exit(app.exec())