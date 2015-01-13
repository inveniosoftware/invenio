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

"""
WebAuthorProfile daemon
"""

from sys import stdout
from invenio import bibtask
from invenio.bibauthorid_dbinterface import get_existing_authors
from invenio.webauthorprofile_dbapi import get_expired_person_ids
from invenio.webauthorprofile_corefunctions import _compute_cache_for_person


def webauthorprofile_daemon():
    """ Constructs the webauthorprofile bibtask. """
    bibtask.task_init(authorization_action='runbibclassify',
        authorization_msg="WebAuthorProfile Task Submission",
        description="""
Purpose:
  Precompute WebAuthorProfile caches.
Examples:
    $webauthorprofile -u admin --all
""",
        help_specific_usage="""
  webauthorprofile [OPTIONS]

  OPTIONS
    Options for update personid
      (default)             Computes all caches for all persons with at least one expired cache

    --all                   Computes all caches for all persons

    --mp        Enables multiprocessing computation

""",
        version="Invenio WebAuthorProfile v 1.0",
        specific_params=("i:", ["all", "mp"]),
        task_submit_elaborate_specific_parameter_fnc=_task_submit_elaborate_specific_parameter,
        task_submit_check_options_fnc=_task_submit_check_options,
        task_run_fnc=_task_run_core)

def _task_submit_elaborate_specific_parameter(key, value, opts, args):
    """
    Given the string key it checks it's meaning, eventually using the
    value. Usually, it fills some key in the options dict.
    It must return True if it has elaborated the key, False, if it doesn't
    know that key.
    """
    if key in ("--all",):
        bibtask.task_set_option("all_pids", True)
    elif key in ("--mp",):
        bibtask.task_set_option("mp", True)
    else:
        return False

    return True

def _task_run_core():
    """ Runs the requested task in the bibsched environment. """
    def compute_cache_f(mp):
        if mp:
            return compute_cache_mp
        else:
            return compute_cache

    all_pids = bibtask.task_get_option('all_pids', False)
    mp = bibtask.task_get_option('mp', False)

    if all_pids:
        pids = list(get_existing_authors(with_papers_only=True))
        compute_cache_f(mp)(pids)
    else:
        pids = get_expired_person_ids()
        if pids:
            compute_cache_f(mp)(pids)

    return 1

def _task_submit_check_options():
    """ Required by bibtask. Checks the options. """
    return True

def compute_cache(pids):
    bibtask.write_message("WebAuthorProfile: %s persons to go" % len(pids),
                          stream=stdout, verbose=0)
    for _, p in enumerate(pids):
        bibtask.write_message("WebAuthorProfile: doing %s out of %s (personid: %s)" % (pids.index(p) + 1, len(pids), p))
        bibtask.task_update_progress("WebAuthorProfile: doing %s out of %s (personid: %s)" % (pids.index(p) + 1, len(pids), p))
        _compute_cache_for_person(p)
        bibtask.task_sleep_now_if_required(can_stop_too=True)

def compute_cache_mp(pids):
    from multiprocessing import Pool
    p = Pool()
    bibtask.write_message("WebAuthorProfileMP: %s persons to go" % len(pids),
                          stream=stdout, verbose=0)
    sl = 100
    ss = [pids[i: i + sl] for i in range(0, len(pids), sl)]
    for i, bunch in enumerate(ss):
        bibtask.write_message("WebAuthorProfileMP: doing bunch %s out of %s" % (str(i + 1), len(ss)))
        bibtask.task_update_progress("WebAuthorProfileMP: doing bunch %s out of %s" % (str(i + 1), len(ss)))
        p.map(_compute_cache_for_person, bunch)
        bibtask.task_sleep_now_if_required(can_stop_too=True)
