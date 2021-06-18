#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys,os,subprocess
import threading
import ctypes
import time
from LogRecord import *
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


class Processer:
    outbuf = []
    def __init__(self):
        self.outbuf = []

        #self.subp = subprocess.Popen("BaiduPCS-Go.exe", shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        #self.processthread = threading.Thread(target=Processer.subprocess_inout,args=(self,))
        #self.processthread.start()
    def __del__(self):
        print("__del__")
        #stop_thread(self.processthread)
        
    def getAllFiles(self):
        #type name
        lists = self.subprocess_execute("./BaiduPCS-Go ls")
        result = []
        for l in lists[ 4 : len(lists)-2 ]:
            l = ' '.join(l.split()) #多个空格合并成一个空格
            l = l.split(' ')
            result.append([l[0], l[1] ,l[2],l[3],l[4]])
        return result

    def getCurrentDir(self):
        result = self.subprocess_execute("./BaiduPCS-Go pwd")
        return result[0][:-1]

    def changeDir(self,dir):
        result = self.subprocess_execute("./BaiduPCS-Go cd " + dir)

    def downloadFiles(self, filename):
        result = self.subprocess_execute("./BaiduPCS-Go d " + filename)
        log.debug(result)

    def deleteFiles(self,filename):
        pass
    def subprocess_execute(self, cmd):
        result_text = []
        subp = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        for line in subp.stdout.readlines():
            result_text.append(str(line, encoding = "utf-8"))

        return result_text
    def subprocess_inout(self):
        while True:
            result_text = self.subp.stdout.readline()
            #print(str(result_text, encoding = "utf-8") )
            
            self.outbuf.append(str(result_text, encoding = "utf-8"))
