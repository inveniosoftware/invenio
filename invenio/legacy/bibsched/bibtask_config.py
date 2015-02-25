# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2008, 2009, 2010, 2011, 2012, 2014 CERN.
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

"""Invenio Bibliographic Task Configuration."""

__revision__ = "$Id$"

import os
import sys
import time
from invenio.config import CFG_LOGDIR, CFG_PYLIBDIR, CFG_INSPIRE_SITE, \
    CFG_BIBSCHED_LOGDIR

# Which tasks are recognized as valid?
CFG_BIBTASK_VALID_TASKS = ("bibindex", "bibupload", "bibreformat",
                           "webcoll", "bibtaskex", "bibrank",
                           "oaiharvest", "oairepositoryupdater", "inveniogc",
                           "webstatadmin", "bibclassify", "bibexport",
                           "dbdump", "batchuploader", "bibencode",
                           "bibtasklet", "refextract", "bibcircd", "bibsort",
                           "selfcites", "hepdataharvest",
                           "arxiv-pdf-checker", "bibcatalog", "bibtex",
                           "bibcheck")

# Tasks that should be run as standalone task
if CFG_INSPIRE_SITE:
    CFG_BIBTASK_MONOTASKS = ("dbdump", "inveniogc")
else:
    CFG_BIBTASK_MONOTASKS = ("bibupload", "dbdump", "inveniogc")

# Tasks that should be run during fixed times
CFG_BIBTASK_FIXEDTIMETASKS = ("oaiharvest", )

# Task that should not be reinstatiated
CFG_BIBTASK_NON_REPETITIVE_TASK = ('bibupload', )

# Default options for any bibtasks
# This is then overridden by each specific BibTask in
# CFG_BIBTASK_DEFAULT_TASK_SETTINGS
CFG_BIBTASK_DEFAULT_GLOBAL_TASK_SETTINGS = {
    'version': '',
    'task_stop_helper_fnc': None,
    'task_name': os.path.basename(sys.argv[0]),
    'task_specific_name': '',
    'task_id': 0,
    'user': '',
    # If the task is not initialized (usually a developer debugging
    # a single method), output all messages.
    'verbose': 9,
    'sleeptime': '',
    'runtime': time.strftime("%Y-%m-%d %H:%M:%S"),
    'priority': 0,
    'runtime_limit': None,
    'profile': [],
    'post-process': [],
    'sequence-id': None,
    'stop_queue_on_error': not CFG_INSPIRE_SITE,
    'fixed_time': False,
    'email_logs_to': [],
    }

# Default options for each bibtasks
# for each bibtask name are specified those settings that the bibtask expects
# to find initialized. Webcoll is empty because current webcoll algorithms
# relays on parameters not being initialized at all.
CFG_BIBTASK_DEFAULT_TASK_SETTINGS = {
    'inveniogc': {
        'logs': False,
        'guests': False,
        'bibxxx': False,
        'documents': False,
        'cache': False,
        'tasks': False,
    },
    'oaiharvest': {
        'repository': None,
        'dates': None,
        'fixed_time': True
    },
    'oairepositoryupdater': {
        'no_upload': 0,
    },
    'bibupload': {
        'mode': None,
        'verbose': 1,
        'tag': None,
        'file_path': None,
        'notimechange': 0,
        'stage_to_start_from': 1,
        'pretend': False,
        'force': False,
    },
    'bibindex': {
        'cmd': 'add',
        'id': [],
        'modified': [],
        'collection': [],
        'maxmem': 0,
        'flush': 10000,
        'windex': None,
        'reindex': False,
    },
    'bibrank': {
        'quick': 'yes',
        'cmd': 'add',
        'flush': 100000,
        'collection': [],
        'id': [],
        'check': "",
        'stat': "",
        'modified': "",
        'last_updated': 'last_updated',
        'run': [],
    },
    'webcoll': {
    },
    'bibtaskex': {
        'number': 30,
    },
    'bibexport': {
        'wjob': None,
    },
    'dbdump': {
        'output': CFG_LOGDIR,
        'number': 5,
    },
    'bibencode': {
    },
    'refextract': {
        'recids': [],
        'collections': [],
    },
}

CFG_BIBTASK_TASKLETS_PATH = os.path.join(
    CFG_PYLIBDIR, 'invenio', 'bibsched_tasklets')
CFG_BIBSCHED_LOGDIR = os.path.join(CFG_LOGDIR, CFG_BIBSCHED_LOGDIR)

CFG_BIBTASK_LOG_FORMAT = ('%(asctime)s --> %(message)s', '%Y-%m-%d %H:%M:%S')
