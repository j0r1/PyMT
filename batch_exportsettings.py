#!/usr/bin/env python

from __future__ import print_function
import mndp
import sys
import os
import json
from batch_common import runBatch
from debuglog import debugLog
import mtuploadandreboot
import mtgetip
import getstacktrace
import mtextractfile
import mtexportsettings
import randomstring

def saveDeviceForLater(dev, savedDevices):
    savedDevices.append(dev)

def commentDhcpLines(fileName):
    with open(fileName, "rt") as f:
        lines = f.readlines()

    newLines = [ ]
    skipping = False
    for l in lines:
        if l.startswith("/ip dhcp-client"):
            skipping = True
        else:
            if skipping and l.startswith("/"):
                skipping = False

        if not skipping:
            newLines.append(l)
        else:
            newLines.append("# " + l)

    with open(fileName, "wt") as f:
        f.write("".join(newLines))

def usage():
    print("\nUsage: {} configoutputspecifier jsonfilename [--commentdhcp] [--usefilterinjson filter --usefilterinjson filter ] [ filtername1 filtervalue1 ... ] \n".format(sys.argv[0]))
    print("Filter names can be one of: ")
    for n in mndp.getAllowedPropertyNames():
        print("    " + n)

    print("""
Filters to use in JSON file are the same, or "none" to clear the filter in the
output file.

Output specifier can be something like "outfile-{mac}"

""")
    sys.exit(-1)

def main():

    user = "admin"
    passw = ""

    try:
        outSpec = sys.argv[1]

        jsonFile = sys.argv[2]
        if os.path.exists(jsonFile):
            print("Specified JSON file already exists!")
            sys.exit(-1)
        
        commentDhcp = False
        filterArgs = [ ]
        jsonFilterArgs = None

        idx = 3
        while idx < len(sys.argv):
            if sys.argv[idx] == "--commentdhcp":
                commentDhcp = True
                idx += 1
            elif sys.argv[idx] == "--usefilterinjson":
                if jsonFilterArgs is None:
                    jsonFilterArgs = [ ]
                jsonFilterArgs.append(sys.argv[idx+1])
                idx += 2
            else:
                filterArgs = sys.argv[idx:]
                break

        if jsonFilterArgs is None:
            jsonFilterArgs = set([ 'mac' ]) # This is the default
        else:
            tmpSet = set()
            for f in jsonFilterArgs:
                f = f.lower()
                if f == 'none':
                    tmpSet.clear()
                else:
                    if not f in mndp.getAllowedPropertyNames():
                        raise Exception("'{}' is not an allowed filter name to use in the json file".format(f))
                    tmpSet.add(f)

            jsonFilterArgs = tmpSet

        #print("jsonFilterArgs = ")
        #print(jsonFilterArgs)

    except Exception as e:
        print("ERROR: got exception: {}".format(e))
        print()
        usage()

    try:
        savedDevices = [ ]
        runBatch(filterArgs, "Save config for this device? [y/n]", saveDeviceForLater, savedDevices)

        if len(savedDevices) == 0:
            raise Exception("No devices selected")
        
        # Check if filenames exist already
        for dev in savedDevices:
            outFile = outSpec.format(**dev)
            if os.path.exists(outFile):
                raise Exception("Config output file '{}' already exists".format(outFile))

        devConfigList = [ ]

        print("Saving device configurations")
        # Obtain config settings
        for dev in savedDevices:
            outFile = outSpec.format(**dev)
            if os.path.exists(outFile):
                raise Exception("Config output file '{}' already exists".format(outFile))

            print("  " + dev["mac"], end="")
            sys.stdout.flush()

            info = mtgetip.getIPAddress(dev["mac"], user, passw)
            ip = info["ip"]

            mtFileName = randomstring.getRandomString(16)
            mtexportsettings.saveConfig(mtFileName, ip, user, passw)
            mtextractfile.extractFile(mtFileName + ".rsc", outFile, ip, user, passw)

            print(" -> " + outFile)
            devConfigList.append((dev, outFile))

            if commentDhcp:
                commentDhcpLines(outFile)

        outList = [ ]
        print("Creating json file")
        for x in devConfigList:
            dev, outFile = x[0], x[1]
            
            filterDict = { }
            for f in jsonFilterArgs:
                filterDict[f] = dev[f]

            d = { "file": outFile, "count": 1, "filter": filterDict }
            outList.append(d)

        with open(jsonFile, "wt") as f:
            f.write("[\n")
            for i in range(len(outList)):
                e = outList[i]
                s = json.dumps(e,sort_keys=True)
                f.write("  " + s)
                if i != len(outList)-1:
                    f.write(",")
                f.write("\n")

            f.write("]\n")

    except Exception as e:
        print(getstacktrace.getStackTrace(e))
        sys.exit(-1)

    print("\nDone.")


if __name__ == "__main__":
    main()
