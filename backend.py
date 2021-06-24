#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys,os,subprocess
import threading
import ctypes
import time
from LogRecord import *
from PyQt5.Qt import QObject
import tempfile
import platform

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
        self.execute_rt_inoutflag = []
        self.execute_rt_id = 0
        self.execute_rt_semaphore = threading.Semaphore(1)
        #self.subp = subprocess.Popen("BaiduPCS-Go.exe", shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        #self.processthread = threading.Thread(target=Processer.subprocess_inout,args=(self,))
        #self.threadlist.append(self.processthread)
        #self.processthread.start()


    def closeAllThread(self):
        log.info("closeAllThread")
        for th in self.threadlist:
            try:
                stop_thread(th)
                log.info("stop thread ")
            except:
                log.error("not exist thread")

        for sub in self.subprocesslist:
            try:
                sub.terminate()
                log.info("stop subprocess")
            except:
                log.error("not exist subprocess")

    def registerCallback(self,callback):
        self.callback = callback

    def getAllFiles_thread(self, parm):
        #type name
        lists = self.subprocess_execute(PROGRAM_RUN + "ls")
        result = []
        for l in lists[ 4 : len(lists)-2 ]:
            l = ' '.join(l.split()) #多个空格合并成一个空格
            l = l.split(' ')
            result.append([l[0], l[1] ,l[2],l[3],l[4]])
        return result

    def getCurrentDir_thread(self, parm):
        result = self.subprocess_execute(PROGRAM_RUN + "pwd")
        return result[0][:-1]

    def getCurrentUid_thread(self,parm):
        result = self.subprocess_execute(PROGRAM_RUN + "who")
        return result[0][ result[0].find("uid: ") + 5 : result[0].find(", 用")]

    def changeDir_thread(self, parm):
        result = self.subprocess_execute(PROGRAM_RUN + "cd " + parm[0])
        return

    def downloadFiles_thread(self, parm):
        result = self.subprocess_execute_realtime(PROGRAM_RUN + "d -p 1 " + parm[0])
        return result

    def deleteFiles_thread(self,filename):
        pass

    def subprocess_execute(self, cmd):
        result_text = []
        out_temp = tempfile.TemporaryFile()
        fileno = out_temp.fileno()
        subp = subprocess.Popen(cmd, shell=True, stdout=fileno, stderr=fileno)
        self.subprocesslist.append(subp)
        subp.wait()
        out_temp.seek(0)
        log.info(cmd)
        for line in out_temp.readlines():
            log.info("subprocess_execute " + str(line, encoding = "utf-8"))
            result_text.append(str(line, encoding = "utf-8"))
        return result_text

    def subprocess_execute_realtime(self, cmd):
        result_text = []
        self.execute_rt_semaphore.acquire()
        execute_rt_id = self.execute_rt_id

        self.execute_rt_id+=1

        self.execute_rt_out_file.append(tempfile.TemporaryFile())
        self.execute_rt_inoutflag.append(1)
        self.execute_rt_semaphore.release()

        fileno = self.execute_rt_out_file[execute_rt_id].fileno()

        log.info("subprocess_execute_realtime " + cmd)

        processthread = threading.Thread(target=Processer.subprocess_inout,args=(self,execute_rt_id,))
        self.threadlist.append(processthread)
        processthread.start()

        subp = subprocess.Popen(cmd, shell=True, stdout=fileno, stderr=fileno)
        self.subprocesslist.append(subp)
        subp.wait()

        time.sleep(1)
        self.execute_rt_inoutflag[execute_rt_id] = 0
        return ['execute_id:'+str(execute_rt_id), 'Complete']

    def subprocess_inout(self,execute_id):
        offset = 0
        while True:
            if self.execute_rt_inoutflag[execute_id] == 1:
                result_text = []
                result_text.append('execute_id:' + str(execute_id))
                result_text.append('')
                tmp_file = self.execute_rt_out_file[execute_id]
                tmp_file.seek(offset)
                before_offset = offset
                for line in tmp_file.readlines():
                    log.debug("subprocess_execute " + str(line, encoding = "utf-8"))
                    try:
                        result_text.append(str(line, encoding = "utf-8"))
                    except e:
                        result_text.append('need retry, error : ' + e)
                    offset += len(line)
                #offset = len(tmp_file.readlines())
                #log.info("subprocess_execute " + str(result_text))
                if before_offset == offset:
                    continue
                if self.callback != None:
                    self.callback(self.func.__name__[:-7], result_text)
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

    def getAllFiles(self):
        parm = []
        th = threading.Thread(target=self.startThread,args=(self.getAllFiles_thread,parm))
        self.threadlist.append(th)
        th.start()

    def getCurrentDir(self):
        parm = []
        th = threading.Thread(target=self.startThread,args=(self.getCurrentDir_thread,parm))
        self.threadlist.append(th)
        th.start()

    def changeDir(self, dir):
        parm = []
        parm.append(dir)
        th = threading.Thread(target=self.startThread,args=(self.changeDir_thread, parm))
        self.threadlist.append(th)
        th.start()

    def downloadFiles(self, filename):
        parm = []
        parm.append(filename)
        th = threading.Thread(target=self.startThread,args=(self.downloadFiles_thread, parm))
        self.threadlist.append(th)
        th.start()

    def getCurrentUid(self):
        parm = []
        th = threading.Thread(target=self.startThread,args=(self.getCurrentUid_thread,parm))
        self.threadlist.append(th)
        th.start()
