#!/usr/bin/env python

from __future__ import print_function
import os
import select
import sys
import subprocess
import time
import random
import inspect
import shlex
import pickle
import copy
import signal
import socket
import json
import pprint
import re
from timeit import default_timer as timer

class TimedIOException(Exception):
    pass

class TimedIOTimeoutException(Exception):
    pass

class TimedIOConnectionClosedException(TimedIOException):
    def __str__(self):
        return "Connection closed"

# Set up functions B and S to convert a string to bytes or vice versa. Useful
# for both python 2 and 3 support
if sys.version_info[0] == 2:
    B = lambda s: s
    S = B
else:
    B = lambda s: bytes(s, 'UTF-8')
    S = lambda b: b.decode(encoding='UTF-8')

# Set up a function called 'debugLog', which is enabled or disabled depending on
# the existence of the environment variable TIMEDIO_VERBOSE
if os.environ.get("TIMEDIO_VERBOSE") is not None:
    def debugLog(s):
        lines = s.splitlines()
        t = time.time()
        intT = int(t)
        fracT = t - intT
        pref = "%s.%03d" % (time.strftime("%H:%M:%S", time.gmtime(t)), int(fracT*1000.0))
        pref += " [ %s ] " % currentNodeName
        spcs = " " * len(pref)

        sys.stderr.write(pref + lines[0] + "\n")
        for i in range(1,len(lines)):
            sys.stderr.write(spcs + lines[i] + "\n")

        sys.stderr.flush()
else:
    def debugLog(s):
        pass

# A helper class to read from/write to file descriptors. Can use a timeout
class TimedIO(object):
    def __init__(self, readFileDesc, writeFileDesc, defaultReadTimeout = 20):
        self.readFileDesc = readFileDesc
        self.writeFileDesc = writeFileDesc
        self.defaultReadTimeout = defaultReadTimeout
        self.inputClosed = False

        if readFileDesc is not None:
            self.pollObject = select.poll()
            self.pollObject.register(readFileDesc, select.POLLIN|select.POLLERR|select.POLLHUP)

    def writeBytes(self, b):
        if self.writeFileDesc is None:
            raise TimedIOException("TimedIO.writeBytes: no write file descriptor has been set")

        if os.write(self.writeFileDesc, b) != len(b):
            raise TimedIOException("Unable to write specified number of bytes")
        
        debugLog("Writing '%s' on PID %d\n" % (repr(b), os.getpid()))

    def writeLine(self, l):
        self.writeBytes(B(l) + b"\n")

    def readBytes(self, num, timeout=-1):
        
        if self.inputClosed:
            raise TimedIOConnectionClosedException

        if self.readFileDesc is None:
            raise TimedIOException("TimedIO.readBytes: no read file descriptor has been set")

        if num <= 0:
            raise TimedIOException("TimedIO.readBytes: invalid number of bytes")

        if timeout < 0:
            timeout = self.defaultReadTimeout

        startTime = timer()
        dt = timeout*1.0

        b = b"" 
        while len(b) < num and dt >= 0:

            r = self.pollObject.poll(dt*1000.0)
            if len(r) == 0:
                raise TimedIOTimeoutException
            if r[0][1]&select.POLLIN == 0:
                self.inputClosed = True
                raise TimedIOConnectionClosedException
        
            x = os.read(self.readFileDesc, 1)
            if len(x) == 0:
                self.inputClosed = True
                raise TimedIOConnectionClosedException

            b += x

            dt = timeout - (timer()-startTime)

        if len(b) != num:
            raise TimedIOTimeoutException

        debugLog("Read bytes '%s'" % repr(b))
        return b

    def readLine(self, timeout=-1):
        
        if self.inputClosed:
            raise TimedIOConnectionClosedException

        if self.readFileDesc is None:
            raise TimedIOException("TimedIO.readLine: no read file descriptor has been set")

        if timeout < 0:
            timeout = self.defaultReadTimeout

        startTime = timer()
        dt = timeout*1.0

        l = b"" 
        while dt >= 0:

            r = self.pollObject.poll(dt*1000.0)
            if len(r) == 0:
                raise TimedIOTimeoutException
            if r[0][1]&select.POLLIN == 0:
                # Connection is closed
                if len(l) != 0:
                    break

                self.inputClosed = True
                raise TimedIOConnectionClosedException

            c = os.read(self.readFileDesc, 1)
            if c == b"\n":
                break

            l += c

            dt = timeout - (timer()-startTime)

        l = S(l)
        debugLog("Read line '%s'" % l)
        return l

    def canRead(self):
        
        if self.inputClosed:
            raise TimedIOConnectionClosedException

        if self.readFileDesc is None:
            raise TimedIOException("TimedIO.canRead: no read file descriptor has been set")

        r = self.pollObject.poll(0)
        if len(r) == 0:
            return False
        
        if r[0][1]&select.POLLIN == 0:
            self.inputClosed = True
            raise TimedIOConnectionClosedException

        return True

