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
import netutils
from timedio import TimedIO, TimedIOException, TimedIOTimeoutException, TimedIOConnectionClosedException
from timeit import default_timer as timer
from debuglog import debugLog

class MNDPJsonParseException(Exception):
    pass

class MNDPNoDefaultGatewayException(Exception):
    pass

def subst(l, search, repl):
    n = ""
    for c in l:
        try:
            idx = search.index(c)
            n += repl[idx]
        except ValueError:
            n += c
        
    return n

def adjustMAC(mac):
    parts = mac.split(":")
    newParts = [ ]
    for p in parts:
        x = int(p, 16)
        n = "%02x" % x
        newParts.append(n)

    return ":".join(newParts)

def runMndp(timeout, specificMac = None):

    # This is a wrapper: the mndp program binds to 5678, which is sometimes in use,
    # causing a closed connection error. The error is generate immediately, so
    # it shouldn't affect the timeout too much

    attempts = 10
    success = False
    foundDevices = None

    while attempts > 0 and not success:
        attempts -= 1

        try:
            foundDevices = runMndpInternal(timeout, specificMac)
            success = True
        except (TimedIOConnectionClosedException, MNDPJsonParseException):
            debugLog("Got a closed connection or parse error, trying again in one second")
            time.sleep(1)

    if not success:
        raise TimedIOConnectionClosedException

    return foundDevices

def runMndpInternal(timeout, specificMac = None):

    if not "PYMT_NODEFAULTGWCHECK" in os.environ:
        if not netutils.hasDefaultGateway():
            raise MNDPNoDefaultGatewayException("""No default gateway could be detected, this will interfere with the normal
operation of the program. To skip the check and proceed anyway, set the
PYMT_NODEFAULTGWCHECK environment variable.""")

    if specificMac:
        specificMac = specificMac.lower()

    foundDevices = { }
    mndp = None
    try:
        mndp = subprocess.Popen( [ "./mactelnet", "-l", "-B" ], stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = open(os.devnull, 'w'))
        debugLog("Waiting for mndp results")

        rw = TimedIO(mndp.stdout.fileno(), mndp.stdin.fileno(), defaultReadTimeout = 1.0)

        startTime = time.time()
        runSecs = timeout
        first = True
        
        while time.time() - startTime < runSecs:
        
            try:
                l = rw.readLine()
                while l:
                    debugLog("    mndp line: " + l)
                    if not first:
                        l = subst(l, ["'"], ['"'])
                        l2 = "[" + l + "]"
                        try:
                            arr = json.loads(l2)
                        except Exception as e:
                            print("Warning, couldn't parse json")
                            print(l2)
                            raise MNDPJsonParseException("Error parsing JSON: " + str(e))

                        mac = adjustMAC(arr[0])
                        ip = arr[8]
                        if ip == "0.0.0.0":
                            ip = ""

                        obj = { 
                                "mac": mac,
                                "id": arr[1],
                                "platform": arr[2],
                                "version": arr[3],
                                "hw": arr[4],
                                "up": arr[5],
                                "softid": arr[6],
                                "iface": arr[7],
                                "ip": ip
                            }
                        foundDevices[mac] = obj

                        if specificMac and specificMac == mac:
                            return obj
                    else:
                        if l.strip() != "MAC-Address,Identity,Platform,Version,Hardware,Uptime,Softid,Ifname,IP":
                            raise Exception("First line of output is not what's expected")

                    first = False
                    l = rw.readLine()

            except TimedIOTimeoutException:
                pass
    finally:
        if mndp is not None:
            try:
                mndp.send_signal(signal.SIGTERM)
                time.sleep(1)
                mndp.send_signal(signal.SIGKILL)
            except Exception as e:
                #debugLog("Warning, exception while killing process: ", e)
                pass

    if specificMac is not None: # If we get here in this case, it means we didn't find it
        return None

    foundDevices = [ (n, foundDevices[n]) for n in foundDevices ]
    debugLog("Device order before sort:")
    for n, d in foundDevices:
        debugLog("  {}".format(n))

    foundDevices.sort()
    debugLog("Device order after sort:")
    for n, d in foundDevices:
        debugLog("  {}".format(n))

    foundDevices = [ e[1] for e in foundDevices ]
    return foundDevices

class PyMNDPException(Exception):
    pass

def getAllowedPropertyNames():
    return [ "mac", "id", "platform", "version", "hw", "up", "softid", "iface", "ip" ]

def _filterDevicesInterval(ownFilters, devsOrFunction, *extraargs):

    allowedNames = getAllowedPropertyNames()

    filters = { }
    for n in allowedNames:
        filters[n] = ".*"

    if ownFilters:
        for n in ownFilters:
            if not n in allowedNames:
                raise PyMNDPException("Filter name '{}' is not allowed, should be one of {}".format(n, allowedNames))

            filters[n] = ownFilters[n]

    if hasattr(devsOrFunction, '__call__'): # it's a function, use it
        devs = devsOrFunction(*extraargs)
    else: # assume that the devices themselves were specified
        devs = devsOrFunction 

    filteredDevs = [ ]
    for d in devs:
        ok = True
        for n in filters:
            filt = filters[n]
            devVal = d[n]

            m = re.match(filt, devVal)
            if not m or m.group(0) != devVal:
                ok = False
                break

        if ok:
            filteredDevs.append(d)

    return (filteredDevs, devs)

def runFilteredMndp(timeout, ownFilters = None):
    return _filterDevicesInterval(ownFilters, runMndp, timeout)

def filterMndpResults(devs, ownFilters = None):
    return _filterDevicesInterval(ownFilters, devs)

def getFiltersFromArgs(args):

    filters = { }
    if len(args)%2 != 0:
        raise PyMNDPException("Number of filter arguments must be a multiple of two")

    for idx in range(0, len(args), 2):
        if idx+1 < len(args):
            name = args[idx]
            value = args[idx+1]
            filters[name] = value

    return filters

def main():

    t0 = time.time()

    filters = getFiltersFromArgs(sys.argv[1:])
    (filteredDevs, devs) = runFilteredMndp(10, filters)

    #debugLog("ALL")
    #pprint.pprint(devs)
    print("Filtered")
    pprint.pprint(filteredDevs)

    t1 = time.time()
    #print("Elapsed time: ", t1-t0)
    #
    #print("\nExtra test")
    #(filteredDevs, devs ) = filterMndpResults(devs, filters)
    #print("Filtered again:")
    #pprint.pprint(filteredDevs)
    #print("Full:")
    #pprint.pprint(devs)

if __name__ == "__main__":
    main()
