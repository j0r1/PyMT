#!/usr/bin/env python

from __future__ import print_function
import mndp
import sys
import os
from debuglog import debugLog

def confirmed():

    # Should help python 2/3 compat
    try:
       input = raw_input
    except NameError:
       pass

    while True:
        a = input().lower()
        if a in [ "yes", "y" ]:
            return True
        elif a in [ "no", "n" ]:
            return False
        else:
            print("Please enter yes or no")

def runBatchOnDevices(filteredDevs, question, count, confirmationCallback, *args):
    idx = 0
    for d in filteredDevs:
        idx += 1

        if count > 0:
            extra = "(still need {})".format(count)
        else:
            extra = "(no count specified)"

        print("\n------------------------------------------")
        print("Selected device ({}/{}) {}: ".format(idx, len(filteredDevs), extra))
        for n in d:
            print("    {} = {}".format(n, d[n]))

        
        print()
        print(question)
        if confirmed():
            print("Confirmed")
            confirmationCallback(d, *args)

            count -= 1
            if count == 0:
                print("Got the requested number of devices")
                break
        else:
            print("Skipping")

def runBatch(filterargs, question, confirmationCallback, *args):

    print("\nDiscovering devices...\n")
    filters = mndp.getFiltersFromArgs(filterargs)
    (filteredDevs, devs) = mndp.runFilteredMndp(10, filters)

    runBatchOnDevices(filteredDevs, question, -1, confirmationCallback, *args)

