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
import sys
from bibauthorid_general_utils import print_tortoise_memory_log
from bibauthorid_least_squares import to_function as create_approx_func
import bibauthorid_config as bconfig
from bibauthorid_general_utils import is_eq, update_status, update_status_final

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


class Estimator(object):
    def __init__(self, coefs):
        self.estimate = create_approx_func(coefs)


matrix_coefs = [1133088., 4., 0.016]
wedge_coefs = [800000., 230., 0.018]


def get_biggest_below(lim, arr):
    for idx, elem in enumerate(arr):
        if elem > lim:
            return idx - 1
    return len(arr) - 1


def get_cores_count():
    import multiprocessing
    return multiprocessing.cpu_count()


def schedule(jobs, sizs, estimator, memfile_path=None):
    if bconfig.DEBUG_PROCESS_PEAK_MEMORY and memfile_path:
        def register_memory_usage():
            pid = os.getpid()
            peak = get_peak_mem()
            fp = open(memfile_path, 'a')
            print_tortoise_memory_log(
                {'pid'  : pid,
                 'peak1': peak[0],
                 'peak2': peak[1],
                 'est'  : sizs[idx],
                 'bibs' : bibs[idx]
                 },
                fp
                )
            fp.close()
    else:
        def register_memory_usage():
            pass

    def run_job(idx):
        try:
            sys.stdout = output_killer
            jobs[idx]()
            register_memory_usage()
            os._exit(os.EX_OK)
        except Exception, e:
            f = open('/tmp/exception-%s' % str(os.getpid()), "w")
            f.write(str(e) + '\n')
            f.close()
            os._exit(os.EX_SOFTWARE)

    output_killer = open(os.devnull, 'w')
    assert len(jobs) == len(sizs)
    ret_status = [None] * len(jobs)

    max_workers = get_cores_count()
    pid_2_idx_size = {}
    #free = get_free_memory()
    initial = get_total_memory()
    free = initial

    bibs = sizs
    sizs = map(estimator.estimate, sizs)

    done = 0.
    total = sum(sizs)
    jobs_n = len(jobs)

    update_status(0., "%d / %d" % (0, jobs_n))
    too_big = sorted((idx for idx, size in enumerate(sizs) if size > free), reverse=True)
    for idx in too_big:
        pid = os.fork()
        if pid == 0: # child
            run_job(idx)
        else: # parent
            done += sizs[idx]
            cpid, status = os.wait()
            update_status(done / total, "%d / %d" % (jobs_n - len(jobs), jobs_n))
            ret_status[idx] = status
            assert cpid == pid
            del jobs[idx]
            del sizs[idx]
            del bibs[idx]

    while jobs or pid_2_idx_size:
        while len(pid_2_idx_size) < max_workers:
            idx = get_biggest_below(free, sizs)
            if idx != -1:
                pid = os.fork()
                if pid == 0: # child
                    run_job(idx)
                else: # parent
                    pid_2_idx_size[pid] = (idx, sizs[idx])
                    assert free > sizs[idx]
                    free -= sizs[idx]
                    del jobs[idx]
                    del sizs[idx]
                    del bibs[idx]
            else:
                break

        pid, status = os.wait()
        assert pid in pid_2_idx_size
        idx, freed = pid_2_idx_size[pid]
        done += freed
        update_status(done / total, "%d / %d" % (jobs_n - len(jobs) - len(pid_2_idx_size), jobs_n))
        ret_status[idx] = status
        free += freed
        del pid_2_idx_size[pid]

    update_status_final("%d / %d" % (jobs_n, jobs_n))
    assert is_eq(free, initial)
    assert not pid_2_idx_size
    assert all(stat != None for stat in ret_status)

    return ret_status
