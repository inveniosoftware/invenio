# -*- coding: utf-8 -*-
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""CDS Invenio Bibliographic Task Configuration."""

__revision__ = "$Id$"

from invenio.config import CFG_LOGDIR

# Which tasks are recognized as valid?
CFG_BIBTASK_VALID_TASKS = ("bibindex", "bibupload", "bibreformat",
                           "webcoll", "bibtaskex", "bibrank",
                           "oaiharvest", "oairepositoryupdater", "inveniogc",
                           "webstatadmin", "bibclassify", "bibexport",
                           "dbdump", "batchuploader")

# Task that should not be reinstatiated
CFG_BIBTASK_NON_REPETITIVE_TASK = ('bibupload')

## Default options for each bibtasks
# for each bibtask name are specified those settings that the bibtask expects
# to find initialized. Webcoll is empty because current webcoll algorithms
# relays on parameters not being initialized at all.
CFG_BIBTASK_DEFAULT_TASK_SETTINGS = {
    'inveniogc' : {
        'logs' : False,
        'guests' : False,
        'bibxxx' : False,
        'documents' : False,
        'cache' : False,
        'tasks' : False,
    },
    'oaiharvest' : {
        'repository' : None,
        'dates' : None,
    },
    'oairepositoryupdater' : {
        'no_upload' : 0,
    },
    'bibupload' : {
        'mode' : None,
        'verbose' : 1,
        'tag' : None,
        'file_path' : None,
        'notimechange' : 0,
        'stage_to_start_from' : 1,
        'pretend' : False,
    },
    'bibindex' : {
        'cmd' : 'add',
        'id' : [],
        'modified' : [],
        'collection' : [],
        'maxmem' : 0,
        'flush' : 10000,
        'windex' : None,
        'reindex' : False,
    },
    'bibrank' : {
        'quick' : 'yes',
        'cmd' : 'add',
        'flush' : 100000,
        'collection' : [],
        'id' : [],
        'check' : "",
        'stat' : "",
        'modified' : "",
        'last_updated' : 'last_updated',
        'run' : [],
    },
    'webcoll' : {
    },
    'bibreformat' : {
        'format' : 'hb',
    },
    'bibtaskex' : {
        'number' : 30,
    },
    'bibexport' : {
        'wjob' : None,
    },
    'dbdump' : {
        'output': CFG_LOGDIR,
        'number': 5,
    },
}
