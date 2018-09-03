#!/usr/bin/env python

import sys
import random
import string

def getRandomString(num):
    chars = string.ascii_letters + string.digits
    return ''.join( [ chars[int(random.random()*len(chars))] for i in range(num) ] )

if __name__ == "__main__":
    print(getRandomString(16))
