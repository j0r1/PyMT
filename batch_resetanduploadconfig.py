#!/usr/bin/env python

from __future__ import print_function
import mndp
import sys
import os
import json
from batch_common import runBatch, runBatchOnDevices
from debuglog import debugLog
import mtgetip
import mtreset
from mtimportsettings import importSettings, MTImportError
import time
import getstacktrace
import mtuploadandreboot

def saveDeviceForLater(dev, savedDevices, fileName, allDevs = None):
    if "processed" in dev: # this is an older check, should not be necessary anymore
        raise Exception("This device was already selected for another file, quitting!")

    savedDevices.append([fileName, dev])
    dev["processed"] = True

    if allDevs is not None: # need to remove the device from the list
        for i in range(len(allDevs)):
            if allDevs[i] is dev:
                del allDevs[i]
                return
    
        raise Exception("Internal error: device not found in allDevs list")

def resetAndUploadToSelectedDevices(devsAndFiles):

    if len(devsAndFiles) == 0:
        print("\nNo devices were selected, nothing to do\n")
        return

    user = "admin"
    passw = ""

    print("\nResetting devices:")
    for entry in devsAndFiles: # entries are [ fileName, device ] arrays
        dev = entry[1]
        ip = dev["ip"]
        addr = dev["mac"]
        if ip:
            addr = ip

        print("    " + dev["mac"])
        mtreset.resetDevice(addr, user, passw)

    time.sleep(2)
    print()
    print("\nUploading configurations (may take a while before the reset is complete and an IP address was obtained):")
    for entry in devsAndFiles: # entries are [ fileName, device ] arrays
        fileName = entry[0]
        dev = entry[1]
        addr = dev["mac"]

        # Run getIP again, if this works, the device has been reset
        maxAttempts = 10
        info = None
        while True:
            try:
                info = mtgetip.getIPAddress(addr, user, passw)
                break
            except mtgetip.IPNotFoundException:
                maxAttempts -= 1
                if maxAttempts <= 0:
                    raise

        ip = info["ip"]
        print("    " + addr + ", " + ip + ": " + fileName + " ", end="")
        sys.stdout.flush()

        configOk = False
        try:
            importSettings(fileName, ip, user, passw)
            configOk = True
            print("Ok, rebooting device")
        except MTImportError as e:
            print("ERROR:", e)

        if configOk:
            mtuploadandreboot.rebootDevice(ip, user, passw)
        
def main():

    ok = True
    useDescription = True

    if len(sys.argv) < 3:
        ok = False
    else:
        if sys.argv[1] == "-desc":
            if len(sys.argv) != 3:
                ok = False

        elif sys.argv[1] == "-single":
            useDescription = False
        else:
            ok = False

    if not ok:
        print("\nUsage: {} -single configfile [ filtername1 filtervalue1 ... ] \n".format(sys.argv[0]))
        print("       or")
        print("\n       {} -desc description.json".format(sys.argv[0]))
        print("""
The first version sends the same config file to one or more devices. The second
version uses a description file in json format to specify which config files
should be uploaded to which devices.

Note that the device is rebooted after the configuration has been applied 
successfully.

The json file containing a description of which files should go to which device
should look something like this:

[
    { "file": "settings1.exp", "count": 2, "filter": { "hw": "RB.*" } },
    { "file": "settings2.exp", "count": -1, "filter": { "mac": "12:34:56:78:90:ab" } },
    ...
]

Lines that have a '#' as the very first character are ignored, allowing you to
place comments in the file.
""")
        print("Filter names can be one of: ")
        for n in mndp.getAllowedPropertyNames():
            print("    " + n)

        print()
        sys.exit(-1)

    if useDescription:
        descFile = sys.argv[2]

        try:
            data = open(descFile, "rt").read()
            # Filter lines that start with a '#'
            data = '\n'.join([ l for l in data.splitlines() if len(l) > 0 and l[0] != '#' ])
            descJson = json.loads(data)
        except Exception as e:
            print("\nError: couldn't load specified description file:", e)
            sys.exit(-1)

    else:
        fileNameToUpload = sys.argv[2]
        if not os.path.exists(fileNameToUpload):
            print("\nError: specified file does not exist\n")
            sys.exit(-1)

        filterArgs = sys.argv[3:]

    try:
        savedDevices = [ ]

        if not useDescription:
            runBatch(filterArgs, "Reset, upload config and reboot this device? [y/n]", saveDeviceForLater, savedDevices, fileNameToUpload)
            resetAndUploadToSelectedDevices(savedDevices)
        else:

            # Check if the filenames exists, and if 'count' is valid
            entryNumber = 0
            for settingsLine in descJson:
                entryNumber += 1

                fileName = settingsLine["file"]
                if not os.path.exists(fileName):
                    raise Exception("Specified file '{}' does not exist (entry number {})".format(fileName, entryNumber))

                if not "count" in settingsLine:
                    raise Exception("Entry number {} does not contain a 'count'".format(entryNumber))

                try:
                    x = int(settingsLine["count"])
                    if x == 0:
                        raise Exception("'count' cannot be zero")
                except Exception as e:
                    raise Exception("Cannot interpret 'count' in entry line {}: {}".format(entryNumber, e))
            
            print("\nObtaining info about available devices")
            allDevs = mndp.runMndp(10)
            savedDevices = [ ]

            # First check if we can find at least one match for all lines in the description file
            entryNumber = 0
            for settingsLine in descJson:
                entryNumber += 1

                (filteredDevices, devs) = mndp.filterMndpResults(allDevs, settingsLine["filter"])
                if not filteredDevices:
                    raise Exception("No devices found to apply entry number {} from description file".format(entryNumber))

            # In a second run we'll actually ask which devices to use
            entryNumber = 0
            for settingsLine in descJson:
                entryNumber += 1

                fileName = settingsLine["file"]
                # Note that allDevs will be modified in the confirmation callback if selected, so afterwards
                # the filteredDevs may be empty
                (filteredDevices, devs) = mndp.filterMndpResults(allDevs, settingsLine["filter"])
                if not filteredDevices:
                    raise Exception("No devices found to apply entry number {} from description file".format(entryNumber))

                print("\nProcessing entry {} from description file".format(entryNumber))
                print("===========================================\n")

                count = settingsLine["count"]
                runBatchOnDevices(filteredDevices, "Reset, upload '{}' and reboot this device? [y/n]".format(fileName), count, saveDeviceForLater, savedDevices, fileName, allDevs)

            resetAndUploadToSelectedDevices(savedDevices)

    except Exception as e:
        print(getstacktrace.getStackTrace(e))
        sys.exit(-1)

    print("\nDone.")

if __name__ == "__main__":
    main()
