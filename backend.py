#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys,os,subprocess
import threading
import ctypes
import time

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

        self.subp = subprocess.Popen("BaiduPCS-Go.exe", shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        #command = bytes("help\r\n", encoding="utf-8")
        self.processthread = threading.Thread(target=Processer.subprocess_inout,args=(self,))
        self.processthread.start()
    def __del__(self):
        print("__del__")
        stop_thread(self.processthread)
        
    def getAllFiles(self):
        #type name
        lists = [{'d', 'testd1'},
                 {'d', 'testd2'},
                 {'f', 'test1.png'},
                 {'f', 'test2.png'}]
        return self.subprocess_execute("help")
    def downloadFiles(self, filename):
        pass
    def deleteFiles(self,filename):
        pass
    def subprocess_execute(self, cmd):
        command = bytes(cmd+"\r\n", encoding="utf-8")
        self.subp.stdin.write(command)
        self.subp.stdin.flush()
        time.sleep(1)
        result_text = []
        while len(self.outbuf) > 0:
            result_text.append(self.outbuf.pop(0))
        return result_text
    def subprocess_inout(self):
        while True:
            result_text = self.subp.stdout.readline()
            #print(str(result_text, encoding = "utf-8") )
            
            self.outbuf.append(str(result_text, encoding = "utf-8"))
