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
import netutils
from debuglog import debugLog

def isMac(addr):
    parts = addr.split(":")
    if len(parts) == 6:
        return True
    return False

def mtSpawn(addr, user = "admin", password = "", logFile = None):

    if isMac(addr):
        debugLog("Starting MAC-telnet")
        child = pexpect.spawnu('./mactelnet -u "{}+cte" -p "{}" {}'.format(user, password, addr), logfile=logFile)
        child.expect(u'Connecting to .*')
        debugLog("Connected to " + addr)
    else:    
        debugLog("Starting telnet")
        # Make sure the host is reachable by pinging it first, otherwist
        # we'll get a strang error from pexpect since the telnet output
        # will not make much sense
        netutils.ping(addr)

        child = pexpect.spawnu("telnet {}".format(addr))
        child.expect(u'Login: ')
        child.sendline(user + "+cte")
        child.expect(u'Password: ')
        child.sendline(password)

    debugLog("Waiting for prompt...")
    child.expect(u'.*admin@.*] > ', timeout=30)
    debugLog("Got prompt!")
    return child

def main():
    child = mtSpawn(sys.argv[1], 'admin', '', sys.stderr)

if __name__ == "__main__":
    main()

