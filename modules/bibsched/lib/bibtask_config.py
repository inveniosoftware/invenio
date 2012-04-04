# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2008, 2009, 2010, 2011 CERN.
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

"""Invenio Bibliographic Task Configuration."""

__revision__ = "$Id$"

import os
from invenio.config import CFG_LOGDIR, CFG_PYLIBDIR

# Which tasks are recognized as valid?
CFG_BIBTASK_VALID_TASKS = ("bibindex", "bibupload", "bibreformat",
                           "webcoll", "bibtaskex", "bibrank",
                           "oaiharvest", "oairepositoryupdater", "inveniogc",
                           "webstatadmin", "bibclassify", "bibexport",
                           "dbdump", "batchuploader", "bibauthorid", 'bibencode',
                           "bibtasklet", "refextract", "bibsort")

# Tasks that should be run as standalone task
CFG_BIBTASK_MONOTASKS = ("bibupload", "dbdump", "inveniogc")

# Tasks that should be run during fixed times
CFG_BIBTASK_FIXEDTIMETASKS = ("oaiharvest", )

# Task that should not be reinstatiated
CFG_BIBTASK_NON_REPETITIVE_TASK = ('bibupload', )

## Default options for each bibtasks
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
        'stop_queue_on_error': True,
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
    'bibreformat': {
        'format': 'hb',
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
    'bibencode' : {
    },
    'refextract' : {
        'recids'       : [],
        'collections'  : [],
    },
}

CFG_BIBTASK_TASKLETS_PATH = os.path.join(CFG_PYLIBDIR, 'invenio', 'bibsched_tasklets')
