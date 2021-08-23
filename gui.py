import sys
from types import LambdaType
from PyQt5.QtWidgets import QApplication, QGridLayout, QLabel, QLayout, QListWidget, QListWidgetItem, QPushButton, QScrollArea, QWidget, QComboBox, QVBoxLayout, QSpacerItem, QSizePolicy, QCheckBox, QLineEdit, QHBoxLayout, QPlainTextEdit, QProgressBar, QListView, QInputDialog, QTextEdit
from PyQt5.QtGui import QIcon, QTextLine, QStandardItem, QStandardItemModel, QPainter, QPixmap
from PyQt5.QtCore import QRectF, QSize, Qt
from PyQt5.QtSvg import QSvgWidget, QSvgRenderer
from PyQt5.QtCore import QObject, pyqtSignal
import pickle

from oracles import *
import glob

import os
os.chdir(os.path.dirname(__file__))

class App(QWidget):
    update = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.title = 'Oracle Manager'
        self.left = 200
        self.top = 200
        self.width = 1300
        self.height = 1000
        self.parent_layout = QVBoxLayout()
        self.setLayout(self.parent_layout)
        self.init()

    def init(self):
        self.readConfig()
        self.initUI()
        self.connectSignals()

    def readConfig(self):
        self.builder = OracleBuilder()
        self.oracles = []
        for file in glob.glob(os.path.join(os.getcwd(), "oracles", "*.json")):
            oracle = self.builder.buildFromFile(file)
            self.oracles.append(oracle)
            
        try:
            if not os.path.isfile('workspace.pickle'):
                raise Exception("no workspace file")
            with open('workspace.pickle', 'rb') as f:
                self.workspace = pickle.load(f)
                self.workspace.update()
        except:
            self.workspace = Workspace("Oracles")
            self.workspace.addNewRecord("Values")
            self.workspace.selectedRecord = 0
    
    def connectSignals(self):
        self.update.connect(self.updateWorkspaceWidget)
        pass
    
    def oneLine(self, a: QWidget, b: QWidget, a_s: int = 1, b_s: int = 1) -> QWidget:
        fl = QHBoxLayout()
        fl.addWidget(a, a_s)
        fl.addWidget(b, b_s)
        flw = QWidget()
        flw.setLayout(fl)
        fl.setContentsMargins(0, 0, 0, 0)
        return flw
    
    def addOracleToWorkspace(self):
        self.workspace.addNewOracle(self.oracles[self.oraclesList.currentIndex()])
        self.updateWorkspaceWidget()
    
    def iconButton(self, icon: str) -> QWidget:
        b = QPushButton("")
        b.setFixedSize(36,36)
        b.setIcon(QIcon(QPixmap("images/icons/{}.png".format(icon))))
        return b

        
    def oraclesSelectWidget(self) -> QWidget:
        self.oraclesList = QComboBox()
        for oracle in self.oracles:
            self.oraclesList.addItem(oracle.spec.get("name", os.path.basename(oracle.path)))
        self.parent_layout.addWidget(self.oraclesList)
        addButton = self.iconButton("plus")
        addButton.clicked.connect(self.addOracleToWorkspace)

        return self.oneLine(self.oraclesList, addButton, 3, 1)
    
    def workspaceWidget(self) -> QWidget:
        self._workspaceWidget = self.hLayout()
        self.updateWorkspaceWidget()
        return self._workspaceWidget
    
    def oracleWidget(self, oracle: Oracle) -> QWidget:
        w = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        w.setLayout(layout)
        layout.addWidget(QLabel("<b style='font-size: 18px'>{}</b>".format(oracle.getName())))
        count = ""
        if oracle.source.finite:
            count = "{}".format(len(oracle.source.values))
        else:
            count = "∞"
        count += " / {}".format(oracle.source.total)
        layout.addWidget(QLabel(count))
        state = ""
        if oracle.source.finite:
            if oracle.source.shuffled:
                state = "shuffled"
            else:
                state = "unshuffled"
        else:
            state = "infinite"
        layout.addWidget(QLabel(state))
        buttons = QHBoxLayout()
        b_w = QWidget()
        b_w.setLayout(buttons)
        layout.addWidget(b_w)
        buttons.addItem(QSpacerItem(
            20, 40, QSizePolicy.Expanding, QSizePolicy.Minimum))

        pb = self.iconButton("pick")
        pb.clicked.connect(lambda: self.pickFromOracle(oracle))
        buttons.addWidget(pb)

        if oracle.source.finite:
            shb = self.iconButton("shuffle")
            buttons.addWidget(shb)
            shb.clicked.connect(lambda: self.shuffleOracle(oracle))

        cb = self.iconButton("choose")
        buttons.addWidget(cb)
        cb.clicked.connect(lambda: self.chooseFromOracle(oracle))

        rb = self.iconButton("remove")
        buttons.addWidget(rb)
        rb.clicked.connect(lambda: self.removeOracle(oracle))
        
        w.setFixedHeight(60)

        return w
    
    def scroll(self, widget: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        return scroll
        
    
    def recordWidget(self, record: Record) -> QWidget:
        self.record = QWidget()
        layout = QVBoxLayout()
        self.record.setLayout(layout)
        self.updateRecordWidget()
        return self.scroll(self.record)
    
    def clearWidget(self, widget: QWidget):
        for i in reversed(range(widget.layout().count())): 
            if widget.layout().itemAt(i).widget():
                widget.layout().itemAt(i).widget().deleteLater()
            else:
                widget.layout().removeItem(widget.layout().itemAt(i))
    
    def updateRecordWidget(self):
        self.clearWidget(self.record)
        record = self.workspace.records[self.workspace.selectedRecord]
        layout = self.record.layout()
        name = QLabel("<b style='font-size: 22px'>{}</b>".format(record.name))
        buttons = self.hLayout()
        layout.addWidget(self.oneLine(name, buttons))
        buttons.layout().addItem(QSpacerItem(
            20, 40, QSizePolicy.Expanding, QSizePolicy.Minimum))


        rb = self.iconButton("rename")
        rb.clicked.connect(lambda: self.renameRecord(record))
        cb = self.iconButton("clear")
        cb.clicked.connect(lambda: self.clearRecord(record))
        rmb = self.iconButton("remove")
        rmb.clicked.connect(lambda: self.removeRecord(record))
        buttons.layout().addWidget(rb)
        buttons.layout().addWidget(cb)
        buttons.layout().addWidget(rmb)

        for value in record.values:
            layout.addWidget(self.valueWidget(record, value))
        if not record.values:
            layout.addWidget(QLabel("No values here yet"))
        layout.addItem(QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
    
    def vLayout(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        w.setLayout(layout)
        return w
        
    def hLayout(self) -> QWidget:
        w = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        w.setLayout(layout)
        return w
    
    def removeValue(self, record, value):
        record.discard(value)
        self.updateWorkspaceWidget()

    def returnValue(self, record, value):
        record.returnValue(value)
        self.updateWorkspaceWidget()
        
    def copyImage(self, image):
        QApplication.clipboard().setPixmap(QPixmap(image))

    def valueWidget(self, record: Record, value: Value) -> QWidget:
        w = self.hLayout()
        w.layout().setContentsMargins(6, 6, 6, 6)
        w.setObjectName(value.id.replace(" ", "_"))
        w.setStyleSheet(
            "QWidget#{} {{border: 1px solid darkgrey;}}".format(w.objectName()))

        image = value.getImage()
        image_width = 150
        if image and image.endswith(".svg"):
            widget = QSvgWidget(value.getImage())
            # image_width = widget.renderer().viewBox().width()
        elif image:
            widget = QPushButton("")
            widget.setFlat(True)
            pixmap = QPixmap(image).scaledToHeight(image_width)
            # widget.setPixmap(pixmap)
            widget.setIcon(QIcon(pixmap))
            widget.setIconSize(QSize(image_width, 200))
            w.layout().setContentsMargins(24, 6, 6, 6)
            widget.clicked.connect(lambda: self.copyImage(image))
        if image:
            widget.setFixedHeight(180)
            widget.setFixedWidth(image_width)
            w.layout().addWidget(widget, 1)
        content = self.vLayout()
        w.layout().addWidget(content, 10)
        layout = content.layout()
        line1 = self.hLayout()
        name = "<span style='font-size: 18px'><b>{}</b>: {}</span>".format(value.oracle.getName(), value.getName())
        if value.state:
            name += " [<b>{}</b>]".format(value.state)
        line1.layout().addWidget(QLabel(name))
        line1.layout().addItem(QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        if value.state:
            reb = self.iconButton("change")
            line1.layout().addWidget(reb)
            reb.clicked.connect(lambda: self.changeValueState(value))
        rb = QPushButton("")
        line1.layout().addWidget(rb)
        rb.setFixedSize(36,36)
        rb.setIcon(QIcon(QPixmap("images/icons/discard.png")))
        rb.clicked.connect(lambda: self.removeValue(record, value))

        if value.oracle.source.finite:
            reb = QPushButton("")
            reb.setFixedSize(36,36)
            reb.setIcon(QIcon(QPixmap("images/icons/return.png")))
            line1.layout().addWidget(reb)
            reb.clicked.connect(lambda: self.returnValue(record, value))
            

        layout.addWidget(line1)
        meaning = value.getMeaning()
        if meaning:
            text = QTextEdit(meaning)
            text.setReadOnly(True)
            text.setMaximumHeight(80)
            layout.addWidget(text)
            text.selectionChanged.connect(lambda: QApplication.clipboard().setText(text.toPlainText()))
        desc = value.getDesc()
        if desc:
            d_text = QTextEdit(desc)
            d_text.setReadOnly(True)
            d_text.setMaximumHeight(120)
            d_text.selectionChanged.connect(lambda: QApplication.clipboard().setText(d_text.toPlainText()))
            layout.addWidget(d_text)

        # w.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        w.setMaximumHeight(200)
        return w
    
    def changeValueState(self, value: Value):
        states = value.oracle.spec["states"]
        value.state = states[(states.index(value.state)+1)%len(states)]
        self.updateWorkspaceWidget()

    def removeOracle(self, oracle: Oracle):
        self.workspace.oracles.remove(oracle)
        self.updateWorkspaceWidget()

    def chooseFromOracle(self, oracle: Oracle):
        self.dialog = QWidget()
        self.dialog.setGeometry(250, 250, 500, 100)
        self.dialog.setWindowTitle("Choose from {}".format(oracle.getName()))

        self.dialog.setLayout(QVBoxLayout())
        # self.dialog.layout().addWidget(self.oraclesSelectWidget())
        valuesList = QComboBox()
        for value in oracle.source.values:
            valuesList.addItem(value)
        self.dialog.layout().addWidget(valuesList)
        addButton = QPushButton("")
        addButton.setFixedSize(36,36)
        addButton.setIcon(QIcon(QPixmap("images/icons/plus.png")))
        self.dialog.layout().addWidget(self.oneLine(valuesList, addButton, 3, 1))
        addButton.clicked.connect(lambda: self.addChoosedValue(oracle.pickById(oracle.source.values[valuesList.currentIndex()])))

        self.dialog.show()
        
    def addChoosedValue(self, value):
        self.workspace.records[self.workspace.selectedRecord].add(value)
        self.updateWorkspaceWidget()
        if value.oracle.source.finite:
            self.dialog.close()
            self.chooseFromOracle(value.oracle)
    
    def pickFromOracle(self, oracle: Oracle):
        value = oracle.pick()
        self.workspace.records[self.workspace.selectedRecord].add(value)
        self.updateWorkspaceWidget()

    def shuffleOracle(self, oracle: Oracle):
        oracle.shuffle()
        self.updateWorkspaceWidget()

    def resetWorkspace(self):
        self.workspace.reset()
        self.workspace.addNewRecord("Values")
        self.updateWorkspaceWidget()
        
    def addOracleDialog(self):
        self.dialog = QWidget()
        self.dialog.setGeometry(250, 250, 500, 100)
        self.dialog.setWindowTitle("Add Oracle")

        self.dialog.setLayout(QVBoxLayout())
        self.dialog.layout().addWidget(self.oraclesSelectWidget())
        self.dialog.show()
        
    def toolbar(self) -> QWidget:
        buttons = self.hLayout()
        buttons.layout().addItem(QSpacerItem(
            20, 40, QSizePolicy.Expanding, QSizePolicy.Minimum))
        return buttons
        
    def updateWorkspace(self):
        self.workspace.update()
        self.updateWorkspaceWidget()

    def updateWorkspaceWidget(self):
        layout = self._workspaceWidget.layout()
        self.clearWidget(self._workspaceWidget)

        left = self.vLayout()
        right = self.vLayout()
        layout.addWidget(left, 2)
        layout.addWidget(right, 3)

        name = QLabel("<b style='font-size: 24px'>{}</b>".format(self.workspace.name))
        buttons = self.toolbar()
        left.layout().addWidget(self.oneLine(name, buttons))

        cb = QPushButton("")
        cb.setFixedSize(36,36)
        cb.setIcon(QIcon(QPixmap("images/icons/clear.png")))
        cb.clicked.connect(lambda: self.resetWorkspace())

        addButton = QPushButton("")
        addButton.setFixedSize(36,36)
        addButton.setIcon(QIcon(QPixmap("images/icons/plus.png")))
        addButton.clicked.connect(self.addOracleDialog)

        upb = self.iconButton("update")
        upb.clicked.connect(self.updateWorkspace)

        rb = self.iconButton("rename")
        rb.clicked.connect(lambda: self.renameWorkspace(self.workspace))

        buttons.layout().addWidget(addButton)
        buttons.layout().addWidget(upb)
        buttons.layout().addWidget(rb)
        buttons.layout().addWidget(cb)
        oracles = self.vLayout()
        oracles.layout().setContentsMargins(6, 6, 6, 6)
        for oracle in self.workspace.oracles:
            oracles.layout().addWidget(self.oracleWidget(oracle))
        if not self.workspace.oracles:
            left.layout().addWidget(QLabel("No oracles here yet"))
        else:
            o_scroll = self.scroll(oracles)
            o_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
            left.layout().addWidget(o_scroll)
            

        self.records = QListWidget()
        # model = QStandardItemModel()
        # records.setModel(model)
        self.updateRecordsWidget()
        
        buttons = self.toolbar()
        left.layout().addWidget(self.oneLine(QLabel("<b style='font-size: 18px'>Records</b>"), buttons))
        left.layout().addWidget(self.records)

        addButton = self.iconButton("plus")
        addButton.clicked.connect(self.addRecord)
        buttons.layout().addWidget(addButton)

        self.records.currentRowChanged.connect(self.selectRecord)

        record = self.workspace.records[self.workspace.selectedRecord]
        item = self.recordWidget(record)
        right.layout().addWidget(item)

        left.layout().addItem(QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
            
        with open('workspace.pickle', 'wb') as f:
            pickle.dump(self.workspace, f)
            
    def updateRecordsWidget(self):
        for n, record in enumerate(self.workspace.records):
            item = QListWidgetItem("{} [{}]".format(record.name, len(record.values)))
            item.setSelected(n == self.workspace.selectedRecord)
            self.records.addItem(item)
            
    def selectRecord(self, row):
        self.workspace.selectedRecord = row
        # self.update.emit()
        # self.updateWorkspaceWidget()
        self.updateRecordWidget()
        
    
    def renameWorkspace(self, woekspace: Workspace):
        text, okPressed = QInputDialog.getText(
            self, "Rename workspace", "Workspace name", QLineEdit.Normal, woekspace.name)
        woekspace.name = text
        self.updateWorkspaceWidget()
        
    def clearRecord(self, record: Record):
        for value in record.values:
            value.returnValue()
        record.values = []
        self.updateWorkspaceWidget()
    def removeRecord(self, record: Record):
        for value in record.values:
            value.returnValue()
        self.workspace.records.remove(record)
        self.workspace.selectedRecord = 0
        self.updateWorkspaceWidget()
    def renameRecord(self, record: Record):
        text, okPressed = QInputDialog.getText(
            self, "Rename record", "Record name", QLineEdit.Normal, record.name)
        record.name = text
        self.updateWorkspaceWidget()
            
    def addRecord(self):
        text, okPressed = QInputDialog.getText(
            self, "New record", "Record name", QLineEdit.Normal, "")
        self.workspace.addNewRecord(text)
        self.updateWorkspaceWidget()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        scriptDir = os.path.dirname(os.path.realpath(__file__))
        self.setWindowIcon(QIcon(os.path.join(scriptDir, "images", "icons", 'crystal-ball.png')))

        # self.parent_layout.addWidget(self.oraclesSelectWidget())
        self.parent_layout.addWidget(self.workspaceWidget())

        # self.parent_layout.addItem(QSpacerItem(
        #     20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        
        self.show()
        

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())