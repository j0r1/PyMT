
Specifying a filter
-------------------
When you run `./mndp.py`, you'll get to see records like the following:

    {'hw': u'RB750Gr2',
     'id': u'MikroTik',
     'iface': u'ether2',
     'ip': u'172.18.15.11',
     'mac': 'e4:8d:8c:ad:12:8a',
     'platform': u'MikroTik',
     'softid': u'IJ47-CMK9',
     'up': u'12999',
     'version': u'6.33.5 (stable)'}

Each of the names `hw`, `id`, `iface`, `ip`, `mac`, `platform`, `softid`,
`up` and `version` can be used to filter the output. When present, a
filter string for such a name will be compared to the corresponding value
in the record. The filter string will be interpreted as a regular expression,
see [https://docs.python.org/2/library/re.html](https://docs.python.org/2/library/re.html) 
for more information.

Filter names that are not specified always match the corresponding string
value. So in the example above, specifying only the filter string `RB.*` (so 
any string starting with the letters 'RB') for the name `hw` will match the 
record.

**Important remarks**:

 1. Care must be taken when using an asterisk `*` on the command line, since
    this may be expanded to a filename by the shell in use (e.g. 'bash') before
    the actual parameter is passed to the program. When in doubt, surround the
    string on the command line with single or double quotes.

 2. The matching algorithm only looks at the string as present in the record
    above, and for the MAC address only lowercase letters will be used in such
    a record. This means that when specifying a filter for a MAC address, 
    lowercase letters need to be used. In the example, specifying `e4.*` for
    the `mac` property will match, but `E4.*` won't. This also applies to
    full MAC addresses: specifying `E4:8D:8C:AD:12:8A` will _not_ match!

Debug info
----------
Set environment variable PYMT_VERBOSE for more debugging output. This can
be done for all following commands using

    export PYMT_VERBOSE=1

It can also be set just for the command to be executed by specifying
it on the same line, for example

    PYMT_VERBOSE=1 ./batch_resetanduploadconfig.py -single conf.txt



