#!/usr/bin/env python

from __future__ import print_function
import mndp
import sys
import os
from batch_common import runBatch
from debuglog import debugLog
import mtuploadandreboot
import mtgetip
import getstacktrace

def uploadAndReboot(dev, fileName):

    user = "admin"
    passw = ""
   
    ip = dev["ip"]
    if not ip:
        macAddr = dev["mac"]
        print("Getting IP address for " + macAddr) 
        info = mtgetip.getIPAddress(macAddr, user, passw)
        ip = info["ip"]

    mtuploadandreboot.uploadFile(fileName, ip, user, passw)
    mtuploadandreboot.rebootDevice(ip, user, passw)

def main():

    if len(sys.argv) < 2:
        print("\nUsage: {} firmarefile.npk [ filtername1 filtervalue1 ... ] \n".format(sys.argv[0]))
        print("Filter names can be one of: ")
        for n in mndp.getAllowedPropertyNames():
            print("    " + n)

        print()
        sys.exit(-1)

    fileName = sys.argv[1]
    if not os.path.exists(fileName):
        print("\nError: specified file does not exist\n")
        sys.exit(-1)

    try:
        runBatch(sys.argv[2:], "Upload and reboot firmware for this device? [y/n]", uploadAndReboot, fileName)
    except Exception as e:
        print(getstacktrace.getStackTrace(e))
        sys.exit(-1)

if __name__ == "__main__":
    main()
