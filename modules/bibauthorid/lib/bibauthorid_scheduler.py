# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.


#
# This has been temporarily deprecated, please use schedule_workes from general utils instead#
#

import re
import os
import sys
from itertools import dropwhile, chain
from invenio.bibauthorid_general_utils import print_tortoise_memory_log
from invenio import bibauthorid_config as bconfig
from invenio.bibauthorid_general_utils import is_eq
from invenio.bibauthorid_logutils import Logger

logger = Logger("scheduler")

# python2.4 compatibility
from invenio.bibauthorid_general_utils import bai_all as all


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


# matrix_coefs = [1133088., 0., 1.5]
# wedge_coefs = [800000., 0., 2.]

matrix_coefs = [1000., 500., 0.01]
wedge_coefs = [1000., 500., 0.02]


def get_biggest_job_below(lim, arr):
    return dropwhile(lambda x: x[1] < lim, enumerate(chain(arr, [lim]))).next()[0] - 1


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
                {'pid': pid,
                 'peak1': peak[0],
                 'peak2': peak[1],
                 'est': sizs[idx],
                 'bibs': bibs[idx]
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
        except Exception as e:
            f = open('/tmp/exception-%s' % str(os.getpid()), "w")
            f.write(str(e) + '\n')
            f.close()
            os._exit(os.EX_SOFTWARE)

    max_workers = get_cores_count()
    pid_2_idx = {}
    # free = get_free_memory()
    initial = get_total_memory()
    free = initial
    output_killer = open(os.devnull, 'w')

    ret_status = [None] * len(jobs)
    bibs = sizs
    sizs = map(estimator, sizs)
    free_idxs = range(len(jobs))
    assert len(jobs) == len(sizs) == len(ret_status) == len(bibs) == len(free_idxs)

    done = 0.
    total = sum(sizs)
    biggest = max(sizs)

    logger.update_status(0., "0 / %d" % len(jobs))
    too_big = [idx for idx in free_idxs if sizs[idx] > free]
    for idx in too_big:
        pid = os.fork()
        if pid == 0:  # child
            run_job(idx)
        else:  # parent
            done += sizs[idx]
            del free_idxs[idx]
            cpid, status = os.wait()
            logger.update_status(done / total, "%d / %d" % (len(jobs) - len(free_idxs), len(jobs)))
            ret_status[idx] = status
            assert cpid == pid

    while free_idxs or pid_2_idx:
        while len(pid_2_idx) < max_workers:
            idx = get_biggest_job_below(free, (sizs[idx] for idx in free_idxs))
            if idx != -1:
                job_idx = free_idxs[idx]
                pid = os.fork()
                if pid == 0:  # child
                    os.nice(int((float(sizs[idx]) * 20.0 / biggest)))
                    run_job(job_idx)
                else:  # parent
                    pid_2_idx[pid] = job_idx
                    assert free > sizs[job_idx]
                    free -= sizs[job_idx]
                    del free_idxs[idx]
            else:
                break

        pid, status = os.wait()
        assert pid in pid_2_idx
        idx = pid_2_idx[pid]
        freed = sizs[idx]
        done += freed
        ret_status[idx] = status
        free += freed
        del pid_2_idx[pid]
        logger.update_status(done / total, "%d / %d" % (len(jobs) - len(free_idxs) - len(pid_2_idx), len(jobs)))

    logger.update_status_final("%d / %d" % (len(jobs), len(jobs)))
    assert is_eq(free, initial)
    assert not pid_2_idx
    assert not free_idxs
    assert len(jobs) == len(sizs) == len(ret_status) == len(bibs)
    assert all(stat is not None for stat in ret_status)

    return ret_status
