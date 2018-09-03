#!/usr/bin/env python

import subprocess
import sys
import os

class PingError(Exception):
    pass

def ping(ip):
    devnull = open(os.devnull, 'wb')
    try:
        subprocess.check_call(["ping", "-c1", "-w5", ip], stdout=devnull, stderr=devnull)
    except subprocess.CalledProcessError:
        raise PingError("Can't ping host {}".format(ip))

def hasDefaultGateway():
    routeExe = None
    possiblePaths = os.environ["PATH"].split(":")
    possiblePaths += [ "/bin", "/sbin", "/usr/bin", "/usr/sbin", "/usr/local/bin", "/usr/local/sbin" ]

    for p in possiblePaths:
        r = os.path.join(p, "route")
        if os.path.isfile(r) and os.access(r, os.X_OK):
            routeExe = r
            break

    if not routeExe:
        raise RouteError("No 'route' executable could be located")

    output = subprocess.check_output([routeExe, "-n"])
    lines = output.splitlines()
    for l in lines:
        parts = l.split()
        if len(parts) > 0 and parts[0] == "0.0.0.0":
            return True

    return False

if __name__ == "__main__":
    ping(sys.argv[1])
    print("Ok, host reachable")

    print("Default gateway: {}".format(hasDefaultGateway()))
