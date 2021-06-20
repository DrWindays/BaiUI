 #!/usr/bin/python
# -*- coding: utf-8 -*-

'''
https://github.com/PeterDing/BaiduPCS-Py
----------------------------------------------------
Changes:

#2021-05-25
draft version.

#2021-06-18
#sudo mount -t vfat -o uid=1000,iocharset=utf8 /dev/sda /mnt/usb

----------------------------------------------------
'''
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QLineEdit,QLabel, QTextEdit,QComboBox,QFileDialog,QCheckBox,QTabBar
from PyQt5.QtWidgets import QHBoxLayout,QVBoxLayout,QGridLayout,QPushButton,QTabWidget,QWidget
from PyQt5.QtGui import QTextCursor, QIcon,QPainter
from PyQt5.QtWidgets import QStyle, QStyleOption,QStylePainter,QStyleOptionTab
from PyQt5.QtWidgets import QTableWidget,QTableWidgetItem,QAbstractItemView
from PyQt5.QtCore import QRect,QPoint
import sys,os,subprocess
import backend
from LogRecord import *

class BaiTabWidget(QTabWidget):
    def __init__(self):
        super().__init__()
        self.setTabBar(BaiTabBar())
        self.setTabPosition(QTabWidget.West)

class BaiTabBar(QTabBar):
    def __init__(self):
        super().__init__()

    def tabSizeHint(self,index):
        s = super().tabSizeHint(index)
        s.transpose()
        s.setHeight(50)
        s.setWidth(100)
        return s

    def paintEvent(self,QPaintEvent):
        painter = QStylePainter(self)
        opt = QStyleOptionTab()
        
        for i in range(self.count()):
            self.initStyleOption(opt, i)
            painter.drawControl(QStyle.CE_TabBarTabShape, opt)
            painter.save()
            
            s = opt.rect.size()
            s.transpose()
            r = QRect(QPoint(),s)
            r.moveCenter(opt.rect.center())
            opt.rect = r
            
            c = self.tabRect(i).center()
            painter.translate(c)
            painter.rotate(90)
            painter.translate(-c)
            painter.drawControl(QStyle.CE_TabBarTabLabel,opt)
            painter.restore()

class FileItem(QWidget):
    def __init__(self, id, name, size, date, time):
        super().__init__()

        self.mainwidget = QWidget()
        self.hbox = QHBoxLayout()
        self.setLayout(self.hbox)

        self.checkbox = QCheckBox()
        self.idlbl = QLabel(id)
        self.namelbl = QLabel(name)
        self.sizelbl = QLabel(size)
        self.timelbl = QLabel(date+' '+time)

        self.hbox.addWidget(self.checkbox)
        self.hbox.addWidget(self.idlbl)
        self.hbox.addWidget(self.namelbl)
        self.hbox.addWidget(self.sizelbl)
        self.hbox.addWidget(self.timelbl)

        self.currentDir = ""

class FileList(QTableWidget):
    fileListDoubleClicked = QtCore.pyqtSignal(list)
    def __init__(self, filelst=[] ,parent=None):
        super().__init__(len(filelst), 5, parent)

        #connect slot event
        self.cellDoubleClicked.connect(self.FileListDoubleClicked)
        self.updateFileList(filelst)

    def updateFileList(self,filelst):
        self.filelst = [["0","0","0","0","../"]] + filelst
        self.checkbox = []
        log.debug(filelst)

        self.clear()
        self.setRowCount(len(self.filelst))

        item_rtnback = QTableWidgetItem("../")
        self.setItem(0, 0, item_rtnback)
        self.setRowHeight(0, 40)
        i = 1
        for file in filelst:
            id, size, date,time , name= file
            item0 = QTableWidgetItem(str(int(id)+1))
            item1 = QTableWidgetItem(size)
            item2 = QTableWidgetItem(date+' '+time)
            item3 = QTableWidgetItem(name)

            checkbox = QCheckBox()

            self.checkbox.append(checkbox)
            self.setCellWidget(i, 0, checkbox)
            #self.setItem(i, 1, item0)
            self.setItem(i, 2, item1)
            self.setItem(i, 3, item2)
            self.setItem(i, 1, item3)
            self.setRowHeight(i,40)
            i+=1

        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.horizontalHeader().setVisible(False)
        self.verticalHeader().setVisible(False)
        #self.resizeRowsToContents()
        self.resizeColumnsToContents()
        self.setShowGrid(False);
        self.setStyleSheet(
        "QTableWidget{border:0px solid rgb(0,0,0);}"
        "QTableWidget::Item{border:0px solid rgb(0,0,0);"
        "border-bottom:1px solid rgb(0,0,0);}")

    def getCheckedFiles(self):
        result = []
        i = 0
        for c in self.checkbox:
            if c.isChecked() == True:
                id, size, date, time, name = self.filelst[i]
                result.append(name)
            i+=1
        return result

    def selectAllFiles(self,check):
        for c in self.checkbox:
            c.setChecked(check)

    #SLOT EVENT#
    def FileListDoubleClicked(self, row, column):
        self.fileListDoubleClicked.emit(self.filelst[row])

class BaiUI(QWidget):
    updateFileListSignal = QtCore.pyqtSignal(list)
    updateDirSignal = QtCore.pyqtSignal(str)
    changeDirSingal = QtCore.pyqtSignal()
    downloadFilesSignal = QtCore.pyqtSignal(list)

    def __init__(self):
        super().__init__()

        #initialize all things
        self.mypan_vbox = QVBoxLayout()
        self.now_down_vbox = QVBoxLayout()
        self.comp_down_vbox = QVBoxLayout()
        self.currentDirLbl = QLabel()
        self.now_down_l = QLabel("正在下载")
        self.comp_down_l = QLabel("完成下载")
        self.file_tree_l = QLabel("当前文件")
        self.tabWidget = BaiTabWidget()
        self.now_down_tab = QWidget()
        self.comp_down_tab = QWidget()
        self.mypan_tab = QWidget()
        self.downloadBtn = QPushButton("下载")
        self.selectAllBtn = QPushButton("全选")
        self.now_down_name_lbl = QLabel()
        self.now_down_progress_lbl = QLabel()

        self.selectFlag = False
        self.now_download_list = []
        #get backend handler: xer
        self.xer = backend.Processer(self.processCallback,self)
        #self.xer.registerCallback()

        self.filelist = FileList([],self)

        self.xer.getAllFiles()
        self.xer.getCurrentDir()
        #self.updateFileList()

        #connect all slot
        self.downloadBtn.clicked.connect(self.DownloadClicked)
        self.selectAllBtn.clicked.connect(self.SelectAllClicked)
        self.filelist.fileListDoubleClicked.connect(self.FileListDoubleClicked)

        self.updateFileListSignal.connect(self.updateFileList)
        self.updateDirSignal.connect(self.updateDir)
        self.changeDirSingal.connect(self.changeDir)
        self.downloadFilesSignal.connect(self.downloadFiles)

        self.initUI()
    def __del__(self):
        del self.xer

    def initUI(self):
        god_vbox_main = QVBoxLayout()
        top_hbox_nav = QHBoxLayout()
        center_vbox_container = QVBoxLayout()
        blank_l = QLabel("    ")

        self.setLayout(god_vbox_main)

        #self.tabWidget.setTabPosition(BaiTabWidget.West)
        #self.tabWidget.addTab(self.tabWidget, '正在下载')
        self.tabWidget.addTab(self.mypan_tab, '全部文件')
        self.tabWidget.addTab(self.now_down_tab, '正在下载')
        self.tabWidget.addTab(self.comp_down_tab, '传输完成')

        self.mypan_tab.setLayout(self.mypan_vbox)
        self.now_down_tab.setLayout(self.now_down_vbox)

        god_vbox_main.addLayout(top_hbox_nav)
        
        #create the navigation button at the most top of the app.
        top_hbox_nav.addWidget(self.downloadBtn)
        top_hbox_nav.addWidget(self.selectAllBtn)
        #top_hbox_nav.addWidget(self.currentDirLbl)

        god_vbox_main.addLayout(center_vbox_container)
        center_vbox_container.addWidget(self.tabWidget)

        self.setGeometry(300, 300, 300, 220)
        self.setFixedSize(800,600)

        self.currentDirLbl.setStyleSheet(
            "QLabel{border:0px solid rgb(0,0,0);"
            "font:bold;"
            "color:purple}")
        self.currentDirLbl.setContentsMargins(0,3,0,0)

        #create the mypan tab 
        self.mypan_vbox.addWidget(self.currentDirLbl)
        self.mypan_vbox.addWidget(self.filelist)

        #create now download tab
        self.now_down_vbox.addWidget(self.now_down_name_lbl)
        self.now_down_vbox.addWidget(self.now_down_progress_lbl)
        self.show()

    def updateFileList(self, list):
        self.filelist.updateFileList(list)
    def updateDir(self, str):
        self.currentDirLbl.setText("当前目录： " + str)

    def changeDir(self):
        self.xer.getCurrentDir()
        self.xer.getAllFiles()

    def downloadFiles(self, result):
        downid = result[0][8:]
        log.debug("down_id: " + downid)
        for r in result[1:]:
            if "文件路径" in r:
                #if self.now_download_list[downid] == None:
                #    self.now_download_list.append([r])
                #else:
                #    self.now_download_list[downid] = [r]
                self.now_down_name_lbl.setText(r)
            if "[1] ↓" in r:
                #if self.now_download_list[downid] == None:
                #    if self.now_download_list[downid][1] == None:
                #    self.now_download_list[downid][1].append()
                self.now_down_progress_lbl.setText(r [r.rfind("[1] ↓"):] )


    def processCallback(self, func, result):
        log.debug("call processCallback")
        log.debug(func)
        log.debug(result)

        if func == "getAllFiles" :
            self.updateFileListSignal.emit(result)
        if func == "getCurrentDir" :
            self.updateDirSignal.emit(result)
        if func == "changeDir" :
            self.changeDirSingal.emit()
        if func == "downloadFiles" :
            self.downloadFilesSignal.emit(result)

    #SLOT EVENT#
    def DownloadClicked(self):
        log.debug(self.filelist.getCheckedFiles())
        self.xer.downloadFiles(self.filelist.getCheckedFiles())

    def SelectAllClicked(self):
        if self.selectFlag == True:
            self.selectAllBtn.setText("全选")
            self.selectFlag = False
        else :
            self.selectAllBtn.setText("全不选")
            self.selectFlag = True
        self.filelist.selectAllFiles(self.selectFlag)

    def FileListDoubleClicked(self, line):
        log.debug(line)
        dir = ""
        if "../" in line[4]:
            log.debug("return back to up path "+line[4])
            dir = self.currentDirLbl.text()
            dir = dir[ dir.find("： ") + 2 : dir.rfind("/") + 1]
        elif "/" in line[4]:
            log.debug("current dir: "+line[4])
            dir = line[4]

        log.debug(dir)
        if dir != "":
            self.xer.changeDir(dir)
        else :
            log.debug("start download " + line[4])
            self.xer.downloadFiles(line[4])
    def closeEvent(self,event):
        log.debug("closeEvent")
        self.xer.closeAllThread()

if __name__ == "__main__":
    log.debug("Program Start")
    BaiAPP = QtWidgets.QApplication(sys.argv)
    BaiUI = BaiUI()

    sys.exit(BaiAPP.exec_())
