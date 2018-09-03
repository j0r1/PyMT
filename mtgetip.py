#!/usr/bin/env python

#from __future__ import absolute_import
#from __future__ import print_function
#from __future__ import unicode_literals

import pexpect
import sys
import time
import sys
import mndp
import pprint
import mtexpect
import netutils
from debuglog import debugLog

def enableDHCPClient(macAddr, interface, user = "admin", password = "", logFile = None):

    child = mtexpect.mtSpawn(macAddr, user, password, logFile)

    debugLog("Got prompt, sending 'ip dhcp-client' command")
    child.sendline('ip dhcp-client\r\n')
    child.expect(u'.*admin@.*] /ip dhcp-client> ', timeout=10)
    debugLog("Got new system prompt, adding dhcp client line")
    child.sendline('add interface={} disabled=no\r\n'.format(interface))
    child.sendline('/\r\n')
    child.expect(u'.*admin@.*] > ', timeout=10)
    time.sleep(1)

class IPNotFoundException(Exception):
    pass

def _checkIPReachable(info):

    ip = info['ip']
    mac = info['mac']
    try:
        netutils.ping(ip)
    except netutils.PingError:
        print("""
        
WARNING: Obtained IP address {} for MAC {}, but cannot ping it.
         Following commands will probably fail!
""".format(ip, mac))
        time.sleep(2)

def getIPAddress(macAddr, user, passw, mndpTimeout = 10.0):

    debugLog("Getting current settings using MNDP")
    
    info = mndp.runMndp(mndpTimeout, macAddr)
    if not info:
        raise IPNotFoundException("Couldn't detect information using MNDP for specified MAC address")
    if info['ip']:
        _checkIPReachable(info)
        return info

    debugLog("Enabling DHCP client")
    interface = info['iface']
    enableDHCPClient(macAddr, interface, user, passw)

    # Apparently it's possible that in the new mndp run the macaddress
    # doesn't appear. This then causes an error since 'info' is None
    # The check should be done a couple of times
    maxChecks = 4
    while maxChecks > 0:
        delay = 5
        debugLog("Rechecking IP address using MNDP in {} seconds".format(delay))
        time.sleep(delay)
        info = mndp.runMndp(mndpTimeout, macAddr)
        if info and info['ip']:
            _checkIPReachable(info)
            return info

        maxChecks -= 1
    
    raise IPNotFoundException("Couldn't get IP address for " + macAddr)

def main():
    macAddr = sys.argv[1]
    user = "admin"
    passw = ""

    if len(sys.argv) > 2:
        user = sys.argv[2]
    if len(sys.argv) > 3:
        passw = sys.argv[3]

    pprint.pprint(getIPAddress(macAddr, user, passw))

if __name__ == "__main__":
    main()

