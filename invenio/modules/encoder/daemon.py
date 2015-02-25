# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011 CERN.
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

"""Bibencode daemon submodule"""

import os
import re
import shutil
from invenio.utils.json import json_decode_file
from invenio.modules.encoder.utils import generate_timestamp, getval
from invenio.legacy.bibsched.bibtask import (
                             task_low_level_submission,
                             task_get_task_param,
                             write_message,
                             task_update_progress
                             )
from invenio.modules.encoder.config import (
                        CFG_BIBENCODE_DAEMON_DIR_NEWJOBS,
                        CFG_BIBENCODE_DAEMON_DIR_OLDJOBS
                        )

# Globals used to generate a unique task name
_TASKID = None
_TIMESTAMP = generate_timestamp()
_NUMBER = 0

def has_signature(string_to_check):
    """ Checks if the given string has the signature of a job file
    """
    sig_re = re.compile("^.*\.job$")
    if sig_re.match(string_to_check):
        return True
    else:
        return False

def job_to_args(job):
    """ Maps the key-value pairs of the job file to CLI arguments for a
    low-level task submission
    @param job: job dictionary to process
    @type job: dictionary
    """
    argument_mapping = {
        'profile': '-p',
        'input': '--input',
        'output': '--output',
        'mode': '--mode',
        'acodec': '--acodec',
        'vcodec': '--vcodec',
        'abitrate': '--abitrate',
        'vbitrate': '--vbitrate',
        'size': '--resolution',
        'passes': '--passes',
        'special': '--special',
        'specialfirst': '--specialfirst',
        'specialsecond': '--specialsecond',
        'numberof': '--number',
        'positions': '--positions',
        'dump': '--dump',
        'write': '--write',
        'new_job_folder': '--newjobfolder',
        'old_job_folder': '--oldjobfolder',
        'recid': '--recid',
        'collection': '--collection',
        'search': '--search'
    }
    args = []
    ## Set a unique name for the task, this way there can be more than
    ## one bibencode task running at the same time
    task_unique_name = '%(mode)s-%(tid)d-%(ts)s-%(num)d' % {
                                'mode': job['mode'],
                                'tid': _TASKID,
                                'ts': _TIMESTAMP,
                                'num': _NUMBER
                                }
    args.append('-N')
    args.append(task_unique_name)
    ## Transform the pairs of the job dictionary to CLI arguments
    for key in job:
        if key in argument_mapping:
            args.append(argument_mapping[key]) # This is the new key
            args.append(job[key]) # This is the value from the job file
    return args

def launch_task(args):
    """ Launches the job as a new bibtask through the low-level submission
    interface
    """
    return task_low_level_submission('bibencode', 'bibencode:daemon', *args)

def process_batch(jobfile_path):
    """ Processes the job if it is a batch job
    @param jobfile_path: fullpath to the batchjob file
    @type jobfile_path: string
    @return: True if the task was successfully launche, False if not
    @rtype: bool
    """
    args = []
    task_unique_name = '%(mode)s-%(tid)d-%(ts)s-%(num)d' % {
                                'mode': 'batch',
                                'tid': _TASKID,
                                'ts': _TIMESTAMP,
                                'num': _NUMBER
                                }
    args.append('-N')
    args.append(task_unique_name)
    args.append('-m')
    args.append('batch')
    args.append('-i')
    args.append(jobfile_path)
    return launch_task(args)

def watch_directory(new_job_dir=CFG_BIBENCODE_DAEMON_DIR_NEWJOBS,
                    old_job_dir=CFG_BIBENCODE_DAEMON_DIR_OLDJOBS):
    """ Checks a folder job files, parses and executes them
    @param new_job_dir: path to the directory with new jobs
    @type new_job_dir: string
    @param old_job_dir: path to the directory where the old jobs are moved
    @type old_job_dir: string
    """
    global _NUMBER, _TASKID
    write_message('Checking directory %s for new jobs' % new_job_dir)
    task_update_progress('Checking for new jobs')
    _TASKID = task_get_task_param('task_id')
    files = os.listdir(new_job_dir)
    for file in files:
        file_fullpath = os.path.join(new_job_dir, file)
        if has_signature(file_fullpath):
            write_message('New Job found: %s' % file)
            job = json_decode_file(file_fullpath)
            if not getval(job, 'isbatch'):
                args = job_to_args(job)
                if not launch_task(args):
                    write_message('Error submitting task')
            else:
                ## We need the job description for the batch engine
                ## So we need to use the new path inside the oldjobs dir
                process_batch(os.path.join(old_job_dir, file))
            ## Move the file to the done dir
            shutil.move(file_fullpath, os.path.join(old_job_dir, file))
            ## Update number for next job
            _NUMBER += 1
    return 1
