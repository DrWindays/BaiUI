#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys,os,subprocess
import threading
import ctypes
import time
from LogRecord import *
from PyQt5.Qt import QObject
import tempfile
import inspect
import platform
from shutil import copyfile

MAX_DOWNLOAD_TASK = 3
PROGRAM_RUN = ""
if(platform.system()=='Windows'):
    log.info('Welcome Windows!')
    PROGRAM_RUN = "BaiduPCS-Go.exe "
elif(platform.system()=='Linux'):
    log.info('Hello Linux')
    PROGRAM_RUN = "./BaiduPCS-Go "
else:
    log.info('not guarrented system')

def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    '''if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")'''
 
def stop_thread(thread):
    _async_raise(thread.ident, SystemExit)


class Processer(QObject):
    outbuf = []

    def __init__(self, callback = None,parent=None):
        super().__init__(parent=parent)
        self.outbuf = []
        self.callback = callback
        self.threadlist = []
        self.subprocesslist = []
        self.func = 0
        self.execute_rt_func = 0
        self.execute_rt_out_file = []
        self.execute_rt_in_file = []
        self.execute_rt_inoutflag = []
        self.execute_rt_sub = []

        self.execute_rt_id = 0
        self.execute_rt_semaphore = threading.Semaphore(1)
        self.execute_rt_max_thread_sem = threading.Semaphore(MAX_DOWNLOAD_TASK)
        #self.subp = subprocess.Popen("BaiduPCS-Go.exe", shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        #self.processthread = threading.Thread(target=Processer.subprocess_inout,args=(self,))
        #self.threadlist.append(self.processthread)
        #self.processthread.start()


    def closeAllThread(self):
        log.info("closeAllThread")

        for sub in self.subprocesslist:
            try:
                sub.terminate()
                log.info("stop subprocess")
            except:
                log.error("not exist subprocess")

        for f in self.execute_rt_out_file:
            log.info("file close")
            try:
                f.close()
            except:
                log.error("not exist filse")

        for th in self.threadlist:
            self.execute_rt_max_thread_sem.release()
            self.execute_rt_semaphore.release()
            try:
                stop_thread(th)
                log.info("stop thread ")
            except:
                log.error("not exist thread")


    def registerCallback(self,callback):
        self.callback = callback

    def getAllFiles_thread(self, parm):
        #type name
        lists = self.subprocess_execute(PROGRAM_RUN + "ls")
        result = []
        for l in lists[ 4 : len(lists)-2 ]:
            l = ' '.join(l.split()) #?????????????????????????????????
            l2 = l.split(' ')
            if len(l2) > 5:
                offset = l[ : l.rfind(' ') - 1].rfind(' ')
                l2 = l [ : offset ].split(' ')
                l2.append(l[offset+1:])
                log.debug(l2)
            l = l2
            log.debug(l)
            if l[0] == '???:':
                break
            result.append([l[0], l[1] ,l[2],l[3],l[4]])
        return result

    def getCurrentDir_thread(self, parm):
        result = self.subprocess_execute(PROGRAM_RUN + "pwd")
        return result[0][:-1]

    def getCurrentUid_thread(self,parm):
        result = self.subprocess_execute(PROGRAM_RUN + "who")
        return result[0][ result[0].find("uid: ") + 5 : result[0].find(", ???")]

    def changeDir_thread(self, parm):
        result = self.subprocess_execute(PROGRAM_RUN + "cd " + parm[1])
        return

    def downloadFiles_thread(self, parm):
        result = self.subprocess_execute_realtime(PROGRAM_RUN + "d -p 1 " + parm[1], parm[0])
        return result

    def deleteFiles_thread(self,filename):
        pass

    def loginAccount_thread(self, parm):
        result = self.subprocess_execute_realtime(PROGRAM_RUN + 
            "login --username " + parm[1] + " --password " + parm[2], parm[0])
        return result

    def logoutAccount_thread(self, parm):
        result = self.subprocess_execute_realtime(PROGRAM_RUN + "logout", parm[0])
        return result

    def getAllConfigs_thread(self, parm):
        result = self.subprocess_execute(PROGRAM_RUN + "config")
        return result

    def updateConfig_thread(self,parm):
        result = self.subprocess_execute(PROGRAM_RUN + "config set --" + parm[1] + " " + str(parm[2]))
        return result

    def inputData_thread(self, parm):
        execute_id, inputdata = parm[1:]
        log.debug("inputData_thread " + str(execute_id) + " " + str(inputdata))

        execute_id = int(execute_id)
        inputdata = str.encode(inputdata)
        self.execute_rt_sub[execute_id].stdin.write(inputdata)
        self.execute_rt_sub[execute_id].stdin.write(b"\n")
        self.execute_rt_sub[execute_id].stdin.flush() # ????????????????????????flush??????
        return

    def subprocess_execute(self, cmd):
        result_text = []
        out_temp = tempfile.NamedTemporaryFile()
        fileno = out_temp.fileno()
        subp = subprocess.Popen(cmd, shell=True, stdout=fileno, stderr=fileno)
        self.subprocesslist.append(subp)
        subp.wait()
        out_temp.seek(0)
        log.info(cmd)
        for line in out_temp.readlines():
            log.info("subprocess_execute " + str(line , encoding = "utf-8"))
            result_text.append(str(line, encoding = "utf-8"))
        return result_text

    def subprocess_execute_realtime(self, cmd, func):
        self.execute_rt_semaphore.acquire()
        execute_rt_id = self.execute_rt_id

        self.execute_rt_id+=1

        result_text = []
        if func == "downloadFiles":
            if self.callback != None:
                result = ['execute_id:'+str(execute_rt_id), '', '[1] ???????????? /' + cmd[ cmd.find("-p 1 ") + 5: ]+' ']
                self.callback(func, result)
        self.execute_rt_semaphore.release()

        self.execute_rt_max_thread_sem.acquire()
        self.execute_rt_semaphore.acquire()

        self.execute_rt_out_file.append(tempfile.NamedTemporaryFile())
        self.execute_rt_inoutflag.append(1)

        fileno = self.execute_rt_out_file[execute_rt_id].fileno()

        subp = subprocess.Popen(cmd, shell=True, stdout=fileno, stdin=subprocess.PIPE)
        #self.subprocesslist.append(subp)
        self.execute_rt_sub.append(subp)

        self.execute_rt_semaphore.release()


        log.info("subprocess_execute_realtime " + cmd)

        processthread = threading.Thread(target=Processer.subprocess_inout,args=(self,execute_rt_id,func,))
        self.threadlist.append(processthread)
        processthread.start()

        subp.wait()

        self.execute_rt_inoutflag[execute_rt_id] = 0
        #stop_thread(processthread)
        self.execute_rt_max_thread_sem.release()

        return ['execute_id:'+str(execute_rt_id), 'Complete']

    def subprocess_inout(self,execute_id, func):
        offset = 0
        while True:
            if self.execute_rt_inoutflag[execute_id] != 0:
                result_text = []
                result_text.append('execute_id:' + str(execute_id))
                result_text.append('')
                out_file = self.execute_rt_out_file[execute_id]
                tmp_file = tempfile.NamedTemporaryFile()

                copyfile(out_file.name,tmp_file.name)

                tmp_file.seek(offset)

                before_offset = offset
                for line in tmp_file.readlines():
                    try:
                        result_text.append(str(line, encoding = "utf-8"))
                    except:
                        result_text.append('need retry, error : ')
                    log.debug("line: " + str(line, encoding = "utf-8") + " len " + str(len(line)) + " offset " + str(offset))
                    offset += len(line)

                tmp_file.close()

                if before_offset == offset:
                    continue
                if self.callback != None:
                    self.callback(func, result_text)

                #tmp_in_file = self.execute_rt_in_file[execute_id]
                #for line_in in tmp_in_file:
                #    log.debug("subprocess_execute input " + str(line, encoding = "utf-8"))
            else:
                log.info("subprocess_inout exit")
                break
            #time.sleep(0.5)



    #THREAD ENTRY#
    def startThread(self, func, parm):
        log.info("start Thread: " + func.__name__[:-7])
        self.func = func
        result = func(parm)
        if self.callback != None:
            self.callback(func.__name__[:-7], result)
        log.info("end Thread")

    def inputData(self, execute_id, inputdata, func):
        parm = []
        parm.append(func)
        parm.append(execute_id)
        parm.append(inputdata)
        th = threading.Thread(target=self.startThread,args=(self.inputData_thread,parm))
        self.threadlist.append(th)
        th.start()

    def getAllFiles(self):
        parm = []
        parm.append('getAllFiles')
        th = threading.Thread(target=self.startThread,args=(self.getAllFiles_thread,parm))
        self.threadlist.append(th)
        th.start()

    def getCurrentDir(self):
        parm = []
        parm.append('getCurrentDir')
        th = threading.Thread(target=self.startThread,args=(self.getCurrentDir_thread,parm))
        self.threadlist.append(th)
        th.start()

    def changeDir(self, dir):
        parm = []
        parm.append('changeDir')
        parm.append(dir)
        th = threading.Thread(target=self.startThread,args=(self.changeDir_thread, parm))
        self.threadlist.append(th)
        th.start()

    def downloadFiles(self, filename):
        parm = []
        parm.append('downloadFiles')
        parm.append(filename)
        th = threading.Thread(target=self.startThread,args=(self.downloadFiles_thread, parm))
        self.threadlist.append(th)
        th.start()

    def loginAccount(self, username, password):
        parm = []
        parm.append('loginAccount')
        parm.append(username)
        parm.append(password)
        th = threading.Thread(target=self.startThread,args=(self.loginAccount_thread, parm))
        self.threadlist.append(th)
        th.start()

    def logoutAccount(self):
        parm = []
        parm.append('logoutAccount')
        th = threading.Thread(target=self.startThread,args=(self.logoutAccount_thread, parm))
        self.threadlist.append(th)
        th.start()


    def getCurrentUid(self):
        parm = []
        parm.append('getCurrentUid')
        th = threading.Thread(target=self.startThread,args=(self.getCurrentUid_thread,parm))
        self.threadlist.append(th)
        th.start()

    def getAllConfigs(self):
        parm = []
        parm.append('getAllConfigs')
        th = threading.Thread(target=self.startThread,args=(self.getAllConfigs_thread,parm))
        self.threadlist.append(th)
        th.start()

    def updateConfig(self, config, value):
        parm = []
        parm.append('updateConfig')
        parm.append(config)
        parm.append(value)
        th = threading.Thread(target=self.startThread,args=(self.updateConfig_thread,parm))
        self.threadlist.append(th)
        th.start()


    def setCapcha(self, execute_id, cap):
        self.inputData(execute_id, cap, 'setCapcha')

    def setValidateType(self, execute_id, validate_type):
        self.inputData(execute_id, validate_type, 'setValidateType')

    def setValidateCode(self, execute_id, code):
        self.inputData(execute_id, code, 'setValidateCode')

    def logoutCheck(self, execute_id, check):
        self.inputData(execute_id, check, 'logoutCheck')

