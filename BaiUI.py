#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
https://github.com/PeterDing/BaiduPCS-Py
----------------------------------------------------
Changes:

#2021-05-25
draft version.

----------------------------------------------------
'''
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QLineEdit,QLabel, QTextEdit,QComboBox,QFileDialog,QCheckBox,QTabBar
from PyQt5.QtWidgets import QHBoxLayout,QVBoxLayout,QGridLayout,QPushButton,QTabWidget,QWidget
from PyQt5.QtGui import QTextCursor, QIcon,QPainter
from PyQt5.QtWidgets import QStyle, QStyleOption,QStylePainter,QStyleOptionTab,
from PyQt5.QtWidgets import QTableWidget,QTableWidgetItem
from PyQt5.QtCore import QRect,QPoint
import sys,os,subprocess
import backend

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

class FileList(QTableWidget):
    def __init__(self, filelst,parent=None):
        super().__init__(len(filelst), 4, parent)
        i = 0
        for file in filelst:
            id, size, date,time , name= file
            item0 = QTableWidgetItem(id)
            item1 = QTableWidgetItem(size)
            item2 = QTableWidgetItem(date+' '+time)
            item3 = QTableWidgetItem(name)
            self.setItem(i, 0, item0)
            self.setItem(i, 1, item1)
            self.setItem(i, 2, item2)
            self.setItem(i, 3, item3)
            i+=1


class BaiUI(QWidget):

    now_down_l = 0
    comp_down_l = 0
    
    file_tree_l = 0
    
    tabWidget = 0
    now_down_tab = 0
    comp_down_tab = 0
    mypan_tab = 0

    def __init__(self):
        super().__init__()
        self.initUI()


        self.xer = backend.Processer()
        files = self.xer.getAllFiles()

        print(files)
        self. addAllFiles(files)
    def initUI(self):
        vbox_main = QVBoxLayout()
        hbox_top = QHBoxLayout()
        vbox_bottom = QVBoxLayout()
        
        self.now_down_l = QLabel("正在下载")
        self.comp_down_l = QLabel("完成下载")
        self.file_tree_l = QLabel("当前文件")
        blank_l = QLabel("    ")
        
        self.setLayout(vbox_main)
        
        self.tabWidget = BaiTabWidget()
        self.now_down_tab = QWidget()
        self.comp_down_tab = QWidget()
        self.mypan_tab = QWidget()

        #self.tabWidget.setTabPosition(BaiTabWidget.West)
        #self.tabWidget.addTab(self.tabWidget, '正在下载')
        self.tabWidget.addTab(self.mypan_tab, '全部文件')
        self.tabWidget.addTab(self.now_down_tab, '正在下载')
        self.tabWidget.addTab(self.comp_down_tab, '传输完成')
        

        self.mypan_vbox = QVBoxLayout()
        self.mypan_tab.setLayout(self.mypan_vbox)

        vbox_main.addLayout(hbox_top)
        vbox_main.addLayout(vbox_bottom)
        
        #vbox_bottom.addLayout(vbox_left)
        #vbox_bottom.addLayout(vbox_right)
        
        hbox_top.addWidget(blank_l)
        #hbox_top.addWidget(self.file_tree_l)
        
        vbox_bottom.addWidget(self.tabWidget)

        self.setGeometry(300, 300, 300, 220)
        self.setFixedSize(800,600)

        self.show()

    def addAllFiles(self, filelst):

        #for file in filelst:
        #    id, size, date,time , name= file
        #    self.mypan_vbox.addWidget(FileItem(id, name, size, date, time))
        self.mypan_vbox.addWidget(FileList(filelst))

if __name__ == "__main__":
    BaiAPP = QtWidgets.QApplication(sys.argv)
    BaiUI = BaiUI()
    





    sys.exit(BaiAPP.exec_())
