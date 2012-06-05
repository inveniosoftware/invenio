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


def __print_func(*args):
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

    status_len = 65
    comment_len = 40

    def padd(stry, l):
        return stry[:l].ljust(l)

    def update_status(percent, comment=""):
        percent = int(percent * 100)
        progress = padd("[%s%s] %d%% done" % ("#" * (percent / 2), "-" * (50 - percent / 2), percent), status_len)
        comment = padd(comment, comment_len)
        print progress, comment, '\r',

    def update_status_final(comment=""):
        update_status(1., comment)
        print ""
        sys.stdout.flush()

else:
    def update_status(percent, comment=""):
        pass

    def update_status_final(comment=""):
        pass

mem_file = '/tmp/tortoise_memory.log'

def print_tortoise_memory_log(summary):
    fp = open(mem_file, 'a')
    stry = "PID:\t%s\tPEAK:\t%s\tEST:\t%s\tBIBS:\t%s\n" % (summary['pid'], summary['peak'], summary['est'], summary['bibs'])
    fp.write(stry)
    fp.close()

def clear_tortoise_memory_log():
    fp = open(mem_file, 'w')
    fp.close()

