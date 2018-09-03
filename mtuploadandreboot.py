#!/usr/bin/env python

from __future__ import print_function
import pexpect
import sys
import time
import os
import ftplib
import mndp
import mtgetip
import mtexpect
from debuglog import debugLog

def rebootDevice(addr, user = "admin", password = "", logFile = None):

    child = mtexpect.mtSpawn(addr, user, password, logFile)

    debugLog("Got prompt, sending 'system' command")
    child.sendline('system\r\n')
    child.expect(u'.*admin@.*] /system>.*', timeout=10)

    debugLog("Got new system prompt, sending reboot command")
    child.sendline('reboot\r\n')
    child.expect(u'.*Reboot, yes?.*', timeout=10)

    debugLog("Sending confirmation")
    child.sendline('y\r\n')
    time.sleep(2)

def uploadFile(fileName, ipAddr, user, passw):
    ftp = ftplib.FTP(ipAddr)
    ftp.login(user, passw)
    print("Dir before upload")
    ftp.dir()
    with open(fileName, "rb") as f:
        ftp.storbinary("STOR " + os.path.basename(fileName), f)
    print("Dir after upload")
    ftp.dir()

def main():

    fileName = sys.argv[1]
    hwType = sys.argv[2]
    macAddr = sys.argv[3]
    user = "admin"
    passw = ""

    if len(sys.argv) > 4:
        user = sys.argv[4]
    if len(sys.argv) > 5:
        passw = sys.argv[5]

    print("Getting IP address for " + macAddr) 
    info = mtgetip.getIPAddress(macAddr, user, passw)
    ip = info["ip"]
    if info["hw"] != hwType:
        raise Exception("hwType doesn't match ({} vs {})".format(hwType, info["hw"]))

    print("Using IP address", ip)

    uploadFile(fileName, ip, user, passw)
    rebootDevice(ip, user, passw)

if __name__ == "__main__":
    main()
