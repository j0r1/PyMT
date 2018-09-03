#!/usr/bin/env python

from __future__ import print_function
import pexpect
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

def saveConfig(mtFileName, addr, user = "admin", password = "", logFile = None):
    child = mtexpect.mtSpawn(addr, user, password, logFile)

    debugLog("Got prompt, sending 'system backup' command")
    child.sendline('system backup\r\n')
    child.expect(u'.*admin@.*] /system backup> ', timeout=10)

    debugLog("Got new system prompt, sending save command")
    child.sendline('save name={}\r\n'.format(mtFileName))
    child.sendline('/\r\n')
    child.expect(u'.*admin@.*] > ', timeout=30)

def main():

    fileName = sys.argv[1]
    macAddr = sys.argv[2]
    user = "admin"
    passw = ""

    if len(sys.argv) > 3:
        user = sys.argv[3]
    if len(sys.argv) > 4:
        passw = sys.argv[4]

    if os.path.exists(fileName):
        raise Exception("File {} already exists".format(fileName))

    print("Obtaining IP for " + macAddr)
    info = mtgetip.getIPAddress(macAddr, user, passw)
    ip = info["ip"]
    print("Using IP address", ip)

    mtFileName = randomstring.getRandomString(16)
    saveConfig(mtFileName, macAddr, user, passw)
    mtextractfile.extractFile(mtFileName + ".backup", fileName, ip, user, passw)
    
    print("Config saved in {}".format(fileName))

if __name__ == "__main__":
    main()
