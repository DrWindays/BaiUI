 #!/usr/bin/python
# -*- coding: utf-8 -*-

'''
https://github.com/qjfoidnh/BaiduPCS-Go
https://south-plus.org/index.php
----------------------------------------------------
Changes:

#2021-05-25
draft version.

#2021-06-18
#sudo mount -t vfat -o uid=1000,iocharset=utf8 /dev/sda /mnt/usb

#2021-06-21
使用BaiduPCS-Go v3.81

----------------------------------------------------
'''
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QLineEdit,QLabel, QTextEdit,QComboBox,QFileDialog,QCheckBox,QTabBar
from PyQt5.QtWidgets import QHBoxLayout,QVBoxLayout,QGridLayout,QPushButton,QTabWidget,QWidget,QDialog
from PyQt5.QtGui import QTextCursor, QIcon,QPainter,QPixmap
from PyQt5.QtWidgets import QStyle, QStyleOption,QStylePainter,QStyleOptionTab
from PyQt5.QtWidgets import QTableWidget,QTableWidgetItem,QAbstractItemView,QProgressBar,QHeaderView
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

class DownloadFileList(QTableWidget):
    def __init__(self, filelst = []):
        super().__init__(len(filelst), 5)

        self.filelist = []

        for f in filelst:
            addDownloadFile(filelst[0], filelst[1])
        self.horizontalHeader().setVisible(False)
        self.verticalHeader().setVisible(False)


    def addDownloadFile(self, execute_id, name):
        row = len(self.filelist)+1
        log.info(row)
        #self.clear()
        self.setRowCount(row)
        item0 = QTableWidgetItem(name[ name.rfind("/") + 1 : len(name) - 1])
        item1 = QTableWidgetItem('0MB/0MB')
        statuslbl = QLabel('0B/s - 剩余时间: --:--:--')
        progress_bar = QProgressBar()

        self.filelist.append([execute_id, name,
                              item0, item1, statuslbl, progress_bar])

        self.setItem(row - 1, 0, item0)
        self.setItem(row - 1, 1, item1)

        progress_widget = QWidget()
        progress_vbox = QVBoxLayout()
        
        progress_widget.setLayout(progress_vbox)
        progress_vbox.addWidget(progress_bar)
        progress_vbox.addWidget(statuslbl)

        #self.setItem(row - 1, 2, item2)
        self.setCellWidget(row - 1, 2, progress_widget)

        self.setRowHeight(row - 1, 60)
        self.setColumnWidth(0, 200)
        self.setColumnWidth(1, 150)
        self.setColumnWidth(2, 250)
        #self.setColumnWidth(3, 20)


        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.horizontalHeader().setVisible(False)
        self.verticalHeader().setVisible(False)
        self.resizeRowsToContents()
        #self.resizeColumnsToContents()
        self.setShowGrid(False);
        self.setStyleSheet(
        "QTableWidget{border:0px solid rgb(0,0,0);}"
        "QTableWidget::Item{border:0px solid rgb(0,0,0);"
        "border-bottom:1px solid rgb(0,0,0);}")

    def getExecuteId(self):
        return self.execute_id

    def splitProgressStr(self, progress_str):
        offset = 0
        if progress_str[ progress_str.find("B ") - 1] >= '0' and progress_str[ progress_str.find("B ") - 1] <='9' :
            offset = 1
        else:
            offset = 2

        offset_complete = 0
        if progress_str[ progress_str.find("B") - 1] >= '0' and progress_str[ progress_str.find("B") - 1] <='9' :
            offset_complete = 1
        else:
            offset_complete = 2

        allsize = progress_str[ progress_str.find("B/") + 2 : progress_str.find("B ") - offset + 1]

        unit_allsize = progress_str[ progress_str.find("B ") - offset + 1: progress_str.find("B ") + 1]
        
        complete = progress_str[ progress_str.find("↓") + 1 : progress_str.find("B") - offset_complete + 1]

        unit_complete = progress_str[ progress_str.find("B/") - offset_complete + 1: progress_str.find("B/") + 1]

        speed = progress_str[progress_str.find("MB ") + 3 : progress_str.find(" in")]
        elapse = progress_str[progress_str.find(" in") + 3 : progress_str.find("s,") + 1]
        left = progress_str[progress_str.find('left ') + 5 : progress_str.find(' .....')]
        if left == '-':
            left = '--:--:--'
        return allsize,unit_allsize,complete,unit_complete,speed,left

    def updateProgress(self, execute_id, progress_str):
        item = self.getItemByExecuteID(execute_id)
        if item != None:

            allsize,unit_allsize,complete,unit_complete,speed,left = self.splitProgressStr(progress_str)
            log.debug(complete + ' ' + allsize)
            item[3].setText(complete + unit_complete + '/'+ allsize + unit_allsize)
            item[4].setText(speed + ' - ' + '剩余时间: ' + left)
            item[5].setValue( int( float(complete)/float(allsize) * 100))

    def updateStatus(self, execute_id, str):
        item = self.getItemByExecuteID(execute_id)
        if item != None:
            item[4].setText(str)
            #item[5].setValue( int( float(complete)/float(allsize) * 100))

    def getItemByExecuteID(self, execute_id):
        for f in self.filelist:
            if f[0] == execute_id:
                return f
        return None


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
        log.info(filelst)

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
                id, size, date, time, name = self.filelst[i+1]
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
    getCurrentUidSignal = QtCore.pyqtSignal(str)
    loginAccountSignal = QtCore.pyqtSignal(list)
    logoutAccountSignal = QtCore.pyqtSignal(list)

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
        self.downloadFileList = DownloadFileList()
        self.top_hbox_nav = QHBoxLayout()
        self.logoutbtn = QPushButton("登出")
 
        self.now_down_vbox.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)

        self.selectFlag = False
        self.now_download_list = []
        #get backend handler: xer
        self.xer = backend.Processer(self.processCallback,self)
        #self.xer.registerCallback()

        self.filelist = FileList([],self)
        self.xer.getCurrentUid()

        #connect all slot
        self.downloadBtn.clicked.connect(self.DownloadClicked)
        self.selectAllBtn.clicked.connect(self.SelectAllClicked)
        self.filelist.fileListDoubleClicked.connect(self.FileListDoubleClicked)
        self.logoutbtn.clicked.connect(self.LogoutClicked)
 
        self.updateFileListSignal.connect(self.updateFileList)
        self.updateDirSignal.connect(self.updateDir)
        self.changeDirSingal.connect(self.changeDir)
        self.downloadFilesSignal.connect(self.downloadFiles)
        self.getCurrentUidSignal.connect(self.getCurrentUid)
        self.loginAccountSignal.connect(self.loginAccount)
        self.logoutAccountSignal.connect(self.logoutAccount)

        self.initUI()

    def initUI(self):
        god_vbox_main = QVBoxLayout()
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

        god_vbox_main.addLayout(self.top_hbox_nav)
        
        #create the navigation button at the most top of the app.
        #top_hbox_nav.addWidget(self.downloadBtn)
        #top_hbox_nav.addWidget(self.selectAllBtn)
        #top_hbox_nav.addWidget(self.currentDirLbl)

        god_vbox_main.addLayout(center_vbox_container)
        center_vbox_container.addWidget(self.tabWidget)

        self.setGeometry(300, 300, 300, 220)
        self.setFixedSize(900,700)

        self.currentDirLbl.setStyleSheet(
            "QLabel{border:0px solid rgb(0,0,0);"
            "font:bold;"
            "color:purple}")
        self.currentDirLbl.setContentsMargins(0,3,0,0)

        #create the mypan tab
        down_nav_widget = QWidget()
        down_nav_hbox = QHBoxLayout()
        down_nav_hbox.addWidget(self.downloadBtn)
        down_nav_hbox.addWidget(self.selectAllBtn)

        down_nav_widget.setLayout(down_nav_hbox)
        
        self.mypan_vbox.addWidget(down_nav_widget)
        self.mypan_vbox.addWidget(self.currentDirLbl)
        self.mypan_vbox.addWidget(self.filelist)

        #create now download tab
        self.now_down_vbox.addWidget(self.downloadFileList)

        self.show()

    # download function #
    def updateFileList(self, list):
        self.filelist.updateFileList(list)
    def updateDir(self, str):
        self.currentDirLbl.setText("当前目录： " + str)
    def getCurrentUid(self,uid):
        log.info("uid: " + uid)
        if uid == '0':
            log.info("not login")
            self.username = QLabel('用户名')
            self.username_input = QLineEdit('')
            self.password = QLabel('密码')
            self.password_input = QLineEdit('')
            self.loginbtn = QPushButton('登录')
            self.loginbtn.clicked.connect(self.LoginBtnClicked)
            self.password_input.setEchoMode(QLineEdit.Password)
            
            self.top_hbox_nav.addWidget(self.username)
            self.top_hbox_nav.addWidget(self.username_input)
            self.top_hbox_nav.addWidget(self.password)
            self.top_hbox_nav.addWidget(self.password_input)
            self.top_hbox_nav.addWidget(self.loginbtn)

        else:
            self.xer.getAllFiles()
            self.xer.getCurrentDir()
            self.top_hbox_nav.addWidget(self.logoutbtn)
            #self.updateFileList()

    def changeDir(self):
        self.xer.getCurrentDir()
        self.xer.getAllFiles()

    def getFileSize(self,filePath):
     
        fsize = os.path.getsize(filePath)
        fsize = fsize/float(1024 * 1024)
     
        return round(fsize, 2)

    def downloadFiles(self, result):
        execute_id = result[0][11:]
        log.debug("execute_id: " + execute_id)
        for r in result[1:]:
            if "文件路径" in r:
                #if self.downloadFileList.getItemByExecuteID(execute_id) == None:
                self.downloadFileList.addDownloadFile(execute_id, r[ r.find("/"): ])
            if "[1] ↓" in r:
                #if self.now_download_list[downid] == None:
                #    if self.now_download_list[downid][1] == None:
                #    self.now_download_list[downid][1].append()
                #self.now_down_progress_lbl.setText(r [r.rfind("[1] ↓"):] )
                #self.updateProgress(execute_id, r [r.rfind("[1] ↓"):] )
                self.downloadFileList.updateProgress(execute_id, r [r.rfind("[1] ↓"):] )
            if "[1] 下载文件失败" in r:
                #self.updateStatus(execute_id, r)
                self.downloadFileList.updateStatus(execute_id, r[r.rfind("[1] 下载文件失败"):-1])

            if "[1] 文件已经存在" in r:
                filesize = self.getFileSize( r[ r.find("[1] 文件已经存在") + 12: r.find(',') ] )
                self.downloadFileList.updateProgress(execute_id,
                     "[1] ↓" + str(filesize)+"MB/" + str(filesize)+"MB 0B/s in 0s, left - ........")
                self.downloadFileList.updateStatus(execute_id, "文件已经存在")
            #if "Complete" in r:
            #    self.updateStatus(r)

    def loginAccount(self, result):
        execute_id = result[0][11:]
        log.debug("execute_id: " + execute_id + str(result[1:]))
        recha = 0
        for r in result[1:]:
            if "打开以下路径, 以查看验证码" in r:
                log.debug("recha")
                recha = 1
                continue
            if "选择一种验证方式" in r:
                log.debug("validate")
                recha = 2
                continue

            if "请输入接收到的验证码" in r:
                log.debug("validate code")
                recha = 3

                self.validatecode_dialog = QDialog()
                readme = QLabel('请输入接收到的验证码', self.validatecode_dialog)
                self.validatecodetext = QLineEdit(self.validatecode_dialog)
                self.validatecodebtn = QPushButton('确定',self.validatecode_dialog)
                self.validatecodebtn.clicked.connect(lambda: self.ValidateCodeClicked(execute_id))
                readme.move(30,40)
                self.validatecodetext.move(30,90)
                self.validatecodebtn.move(30,120)
                self.validatecode_dialog.setWindowTitle("请输入接收到的验证码")
                self.validatecode_dialog.exec_()
                continue

            if "百度帐号登录成功:" in r:
                log.debug("login success")
                self.xer.getAllFiles()
                self.xer.getCurrentDir()

                self.top_hbox_nav.removeWidget(self.username)
                self.top_hbox_nav.removeWidget(self.username_input)
                self.top_hbox_nav.removeWidget(self.password)
                self.top_hbox_nav.removeWidget(self.password_input)
                self.top_hbox_nav.removeWidget(self.loginbtn)

                self.username.deleteLater()
                self.username_input.deleteLater()
                self.password.deleteLater()
                self.password_input.deleteLater()
                self.loginbtn.deleteLater()

                self.top_hbox_nav.addWidget(self.logoutbtn)
                break

            if recha == 1:
                log.debug(r)
                self.captcha_dialog = QDialog()
                self.captchatext = QLineEdit(self.captcha_dialog)
                self.captchabtn = QPushButton('确定',self.captcha_dialog)
                self.captchabtn.clicked.connect(lambda: self.CaptchaClicked(execute_id))
                picture = QLabel(self.captcha_dialog)
                #调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
                png = QPixmap(r[:-1])
                png.scaled(100,40)

                picture.setPixmap(png)
                picture.setScaledContents(True)

                picture.move(30,0)
                self.captchatext.move(30,40)
                self.captchabtn.move(30,100)
                self.captcha_dialog.setWindowTitle("请输入验证码")
                self.captcha_dialog.exec_()

                recha = 0
            if recha == 2:
                log.debug(r)
                self.validate_dialog = QDialog()
                readme = QLabel('选择一种验证方式：\n'+ r[:-1] +'，2：邮箱 \n请输入验证方式(1 或 2)', self.validate_dialog)
                self.validatetext = QLineEdit(self.validate_dialog)
                self.validatebtn = QPushButton('确定',self.validate_dialog)
                self.validatebtn.clicked.connect(lambda: self.ValidateClicked(execute_id))
                readme.move(30,40)
                self.validatetext.move(30,90)
                self.validatebtn.move(30,120)
                self.validate_dialog.setWindowTitle("请选择验证方式")
                self.validate_dialog.exec_()

                recha = 0

    def logoutAccount(self, result):
        execute_id = result[0][11:]
        log.debug("execute_id: " + execute_id + str(result))
        for r in result[1:]:
            log.debug(r)
            if '确认退出百度帐号' in r:
                self.xer.inputData(execute_id, 'y', 'logoutAccount')
                self.xer.getCurrentUid()
                self.top_hbox_nav.removeWidget(self.logoutbtn)
                self.logoutbtn.deleteLater()

    def processCallback(self, func, result):
        log.debug("call processCallback")
        log.debug(func)
        log.debug(str(result))

        if func == "getAllFiles" :
            self.updateFileListSignal.emit(result)
        if func == "getCurrentDir" :
            self.updateDirSignal.emit(result)
        if func == "changeDir" :
            self.changeDirSingal.emit()
        if func == "downloadFiles" :
            self.downloadFilesSignal.emit(result)
        if func == "getCurrentUid" :
            self.getCurrentUidSignal.emit(result)
        if func == "loginAccount" :
            self.loginAccountSignal.emit(result)
        if func == "logoutAccount" :
            self.logoutAccountSignal.emit(result)

    #SLOT EVENT#
    def CaptchaClicked(self, execute_id):
        cap_input = self.captchatext.text()
        self.captcha_dialog.close()
        self.xer.setCapcha(execute_id,cap_input)

    def ValidateClicked(self, execute_id):
        validate_input = self.validatetext.text()
        self.validate_dialog.close()
        self.xer.setValidateType(execute_id,validate_input)

    def ValidateCodeClicked(self, execute_id):
        validate_input = self.validatecodetext.text()
        self.validatecode_dialog.close()
        self.xer.setValidateType(execute_id,validate_input)

    def DownloadClicked(self):
        log.info(self.filelist.getCheckedFiles())
        for f in self.filelist.getCheckedFiles():
            if "../" in f:
                continue
            self.xer.downloadFiles(f)

    def SelectAllClicked(self):
        if self.selectFlag == True:
            self.selectAllBtn.setText("全选")
            self.selectFlag = False
        else :
            self.selectAllBtn.setText("全不选")
            self.selectFlag = True
        self.filelist.selectAllFiles(self.selectFlag)

    def FileListDoubleClicked(self, line):
        log.info(line)
        dir = ""
        if "../" in line[4]:
            log.info("return back to up path "+line[4])
            dir = self.currentDirLbl.text()
            dir = dir[ dir.find("： ") + 2 : dir.rfind("/") + 1]
        elif "/" in line[4]:
            log.info("current dir: "+line[4])
            dir = line[4]

        log.info(dir)
        if dir != "":
            self.xer.changeDir(dir)
        else :
            log.info("start download " + line[4])
            self.xer.downloadFiles(line[4])

    def LoginBtnClicked(self):
        self.xer.loginAccount(self.username_input.text(), self.password_input.text())

    def LogoutClicked(self):
        self.xer.logoutAccount()

    def closeEvent(self,event):
        log.info("closeEvent")
        self.xer.closeAllThread()

if __name__ == "__main__":
    log.info("Program Start")
    BaiAPP = QtWidgets.QApplication(sys.argv)
    BaiUI = BaiUI()

    sys.exit(BaiAPP.exec_())
