# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011, 2012 CERN.
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

import re
import os
import operator
from itertools import izip, starmap
from invenio.bibauthorid_general_utils import print_tortoise_memory_log
from invenio.bibauthorid_general_utils import clear_tortoise_memory_log
import invenio.bibauthorid_config as bconfig

coefs = [1. / 17., -1., 0.]

def to_number(stry):
    return int(re.sub("\D", "", stry))

def dict_by_file(fpath):
    fp = open(fpath)
    content = fp.read()
    fp.close()
    return dict(x.split(':') for x in content.split("\n")[:-1])

def get_free_memory():
    mem = dict_by_file("/proc/meminfo")
    return sum(map(to_number, (mem['MemFree'], mem['Buffers'], mem['Cached'])))

def get_total_memory():
    mem = dict_by_file("/proc/meminfo")
    return to_number(mem['MemTotal'])

def get_peak_mem():
    pid = os.getpid()
    mem = dict_by_file("/proc/%d/status" % pid)
    return map(to_number, (mem["VmPeak"], mem["VmHWM"]))

def estimate_ram_usage(bibs):
    return sum(starmap(operator.mul, izip(coefs, (bibs * bibs, bibs, 1))))

def get_biggest_below(lim, arr):
    for idx, elem in enumerate(arr):
        if elem > lim:
            return idx - 1
    return len(arr) - 1

def initialize_ram_estimation():
    global coefs
    coefs[2] = get_peak_mem()[0] * 0.9

def get_cores_count():
    import multiprocessing
    return multiprocessing.cpu_count()

def schedule(job, args, sizs):
    assert len(args) == len(sizs)

    max_workers = get_cores_count()
    pid_2_size = {}
    #free = get_free_memory()
    free = get_total_memory()

    bibs = sizs
    initialize_ram_estimation()
    sizs = map(estimate_ram_usage, sizs)

    if bconfig.DEBUG_PROCESS_PEAK_MEMORY:
        clear_tortoise_memory_log()

    too_big = sorted((idx for idx in xrange(len(sizs)) if sizs[idx] > free), reverse=True)
    for idx in too_big:
        pid = os.fork()
        if pid == 0: # child
            job(*args[idx])
            if bconfig.DEBUG_PROCESS_PEAK_MEMORY:
                pid = os.getpid()
                print_tortoise_memory_log(
                    {'pid'  : pid,
                     'peak' : get_peak_mem(),
                     'est'  : sizs[idx],
                     'bibs' : bibs[idx]})

            os._exit(0)
        else: # parent
            del args[idx]
            del sizs[idx]
            del bibs[idx]
            cpid, status = os.wait()
            assert cpid == pid

    while args or pid_2_size:
        while len(pid_2_size) < max_workers:
            idx = get_biggest_below(free, sizs)

            if idx != -1:
                pid = os.fork()
                if pid == 0: # child
                    job(*args[idx])
                    if bconfig.DEBUG_PROCESS_PEAK_MEMORY:
                        pid = os.getpid()
                        print_tortoise_memory_log(
                            {'pid'  : pid,
                             'peak' : get_peak_mem(),
                             'est'  : sizs[idx],
                             'bibs' : bibs[idx]})

                    os._exit(0)
                else: # parent
                    pid_2_size[pid] = (sizs[idx], args[idx])
                    assert free > sizs[idx]
                    free -= sizs[idx]
                    del args[idx]
                    del sizs[idx]
                    del bibs[idx]
            else:
                break

        pid, status = os.wait()
        assert pid in pid_2_size
        freed, name = pid_2_size[pid]
        if status != 0:
            import sys
            print >> sys.stderr, "Worker %s died." % str(name)
            sys.stderr.flush()
            assert False

        free += freed
        del pid_2_size[pid]

    assert not pid_2_size

