#!/usr/bin/env python

import pexpect
import sys
import time
import sys
import mtexpect
from debuglog import debugLog

def resetDevice(addr, user = "admin", password = "", logFile = None):

    child = mtexpect.mtSpawn(addr, user, password, logFile)

    debugLog("Removing all files on device")
    child.sendline("file\r\n")
    child.expect(u'.*admin@.*] /file> ', timeout=10)
    child.sendline("remove [find]\r\n")
    child.sendline("/\r\n")
    child.expect(u'.*admin@.*] > ', timeout=10)

    debugLog("Got prompt, sending 'system' command")
    child.sendline('system\r\n')
    child.expect(u'.*admin@.*] /system> ', timeout=10)

    debugLog("Got new system prompt, sending reset command")
    child.sendline('reset-configuration no-defaults=yes skip-backup=yes\r\n')
    child.expect(u'.*Dangerous! Reset anyway?.*', timeout=10)

    debugLog("Sending confirmation")
    child.sendline('y\r\n')
    time.sleep(2)

def main():
    addr = sys.argv[1]
    user = "admin"
    passw = ""

    if len(sys.argv) > 2:
        user = sys.argv[2]
    if len(sys.argv) > 3:
        passw = sys.argv[3]

    resetDevice(addr, user, passw)

if __name__ == "__main__":
    main()
