#!/usr/bin/env python

from __future__ import print_function
import sys
import time
import sys
import ftplib
import mndp
import mtgetip
import os
import randomstring
import mtextractfile
import mtexpect
from debuglog import debugLog

class MTImportError(Exception):
    pass

def importSettingsOld(fileName, ip, user, passw, useLogCallback = False):

    prefix = randomstring.getRandomString(16)
    mtFileName = prefix + ".auto.rsc"
    logFileName = prefix + ".auto.log"

    with open(fileName, "rb") as f:
        ftp = ftplib.FTP(ip)
        ftp.login(user, passw)
        ftp.storbinary("STOR " + mtFileName, f)

    startTime = time.time()
    timeout = 10.0
    while time.time() - startTime < timeout:
        time.sleep(1)
        files = ftp.nlst()
        if logFileName in files:
            break

    logObj = { "log": "" }
    def logWrite(data):
        logObj["log"] += data
    
    ftp.retrlines("RETR " + logFileName, logWrite)

    if useLogCallback:
        print("Output from log file:")
        print(logObj["log"])

    if not "successfully" in logObj["log"]:
        raise MTImportError("Uploaded settings file does not seem to be ok, import manually to get feedback")

def importSettingsNew(fileName, ip, user, passw, useLogCallback = False):

    prefix = randomstring.getRandomString(16)
    mtFileName = prefix + ".rsc"

    with open(fileName, "rb") as f:
        ftp = ftplib.FTP(ip)
        ftp.login(user, passw)
        ftp.storbinary("STOR " + mtFileName, f)

    del ftp # allow it to be garbage collected, closing the connection
    time.sleep(1)

    class LogObject:
        def __init__(self):
            self.logString = ""

        def write(self, data):
            self.logString += data

        def flush(self):
            pass

    log = LogObject()

    child = mtexpect.mtSpawn(ip, user, passw)
    child.logfile_read = log
    child.sendline("/import {}\r\n".format(mtFileName))
    child.sendline("/ip\r\n")
    child.expect(u'.*admin@.*] /ip> ', timeout=30)

    retVal = log.logString

    debugLog("Read from MikroTik process: " + str(repr(retVal)))

    retVal = retVal.replace('\r\n','\n')
    lines = retVal.splitlines()

    filteredLines = [ ]
    recording = False
    for l in lines:
        #print("Investigating", l)
        if not recording:
            if "/import {}".format(mtFileName) in l and l.startswith("[admin@"):
                recording = True
        else:
            if l.startswith("[admin@"):
                break
            else:
                filteredLines.append(l)


    startIdx = 0
    while startIdx < len(filteredLines):
        if len(filteredLines[startIdx]) == 0:
            startIdx += 1
        else:
            break

    filteredLines = filteredLines[startIdx:]

    endIdx = len(filteredLines)
    while endIdx > 0:
        if len(filteredLines[endIdx-1]) == 0:
            endIdx -= 1
        else:
            break

    filteredLines = filteredLines[:endIdx]
    response = "\n".join(filteredLines)
    #print(repr(response))

    if useLogCallback:
        print("Output:")
        print(response)

    if not "successfully" in response:
        raise MTImportError("Import response: {}".format(repr(response)))

importSettings = importSettingsNew

def main():

    fileName = sys.argv[1]
    macAddr = sys.argv[2]
    user = "admin"
    passw = ""

    if len(sys.argv) > 3:
        user = sys.argv[3]
    if len(sys.argv) > 4:
        passw = sys.argv[4]

    print("Obtaining IP address for " + macAddr)
    info = mtgetip.getIPAddress(macAddr, user, passw)
    ip = info["ip"]
    print("Using IP address", ip)

    importSettings(fileName, ip, user, passw, sys.stdout.write)

    print()
    print()
    print("Done.")

if __name__ == "__main__":
    main()
