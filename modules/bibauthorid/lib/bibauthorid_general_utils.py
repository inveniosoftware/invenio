# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
'''
bibauthorid_general_utils
    Bibauthorid utilities used by many parts of the framework
'''

import bibauthorid_config as bconfig
from datetime import datetime
PRINT_TS = bconfig.DEBUG_TIMESTAMPS
PRINT_TS_US = bconfig.DEBUG_TIMESTAMPS_UPDATE_STATUS and PRINT_TS

def __print_func(*args):
    if PRINT_TS:
        print datetime.now(),
    for arg in args:
        print arg,
    print ""

def __dummy_print(*args):
    pass

def __create_conditional_print(cond):
    if cond:
        return __print_func
    else:
        return __dummy_print

bibauthor_print = __create_conditional_print(bconfig.DEBUG_OUTPUT)
name_comparison_print = __create_conditional_print(bconfig.DEBUG_NAME_COMPARISON_OUTPUT)
metadata_comparison_print = __create_conditional_print(bconfig.DEBUG_METADATA_COMPARISON_OUTPUT)
wedge_print = __create_conditional_print(bconfig.DEBUG_WEDGE_OUTPUT)


if bconfig.DEBUG_OUTPUT:
    import sys

    status_len = 68
    comment_len = 40

    def padd(stry, l):
        return stry[:l].ljust(l)

    def update_status(percent, comment="", print_ts=False):
        filled = int(percent * 50)
        bar = "[%s%s] " % ("#" * filled, "-" * (50 - filled))
        percent = ("%.2f%% done" % (percent * 100)).rjust(12)
        progress = padd(bar + percent, status_len)
        comment = padd(comment, comment_len)
        if print_ts or PRINT_TS_US:
            print  datetime.now(),
        print progress, comment, '\r',

    def update_status_final(comment=""):
        update_status(1., comment, print_ts=PRINT_TS)
        print ""
        sys.stdout.flush()

else:
    def update_status(percent, comment=""):
        pass

    def update_status_final(comment=""):
        pass

def print_tortoise_memory_log(summary, fp):
    stry = "PID:\t%s\tPEAK:\t%s,%s\tEST:\t%s\tBIBS:\t%s\n" % (summary['pid'], summary['peak1'], summary['peak2'], summary['est'], summary['bibs'])
    fp.write(stry)


def parse_tortoise_memory_log(memfile_path):
    f = open(memfile_path)
    lines = f.readlines()
    f.close()

    def line_2_dict(line):
        line = line.split('\t')
        ret = {  'mem1' : int(line[3].split(",")[0]),
                 'mem2' : int(line[3].split(",")[1]),
                 'est'  : float(line[5]),
                 'bibs' : int(line[7])
                 }
        return ret

    return map(line_2_dict, lines)


eps = 1e-6
def is_eq(v1, v2):
    return v1 + eps > v2 and v2 + eps > v1
