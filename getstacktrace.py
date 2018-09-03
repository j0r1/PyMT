#!/usr/bin/env python
from __future__ import print_function
import traceback
import sys

def getStackTrace(ex):
    _, _, ex_traceback = sys.exc_info()
    if ex_traceback is None:
        ex_traceback = ex.__traceback__
    tb_lines = traceback.format_exception(ex.__class__, ex, ex_traceback)
    return "\n\nERROR! Encountered exception: %s\n\n\n%s" % (str(ex),''.join(tb_lines))

def main():
    try:
        raise Exception("Test error")
    except Exception as e:
        print(getStackTrace(e))

if __name__ == "__main__":
    main()


