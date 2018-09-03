#!/usr/bin/env python

from __future__ import print_function
import sys
import time
import sys
import ftplib
import os
from debuglog import debugLog

def extractFile(mtFile, fileName, ipAddr, user, passw):
    ftp = ftplib.FTP(ipAddr)
    ftp.login(user, passw)

    with open(fileName, "wb") as f:
        debugLog("Files before extraction:")
        for n in ftp.nlst():
            debugLog("    " + n)

        debugLog("Waiting for file to become complete")
        while True:
            time.sleep(1)
            files = ftp.nlst()
            if not mtFile + ".in_progress" in files:
                break

        debugLog("Retrieving file")
        ftp.retrbinary("RETR {}".format(mtFile), f.write)

    ftp.delete("{}".format(mtFile))
    debugLog("Files after extraction:")
    for n in ftp.nlst():
        debugLog("    " + n)

