# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

"""Ingestion database configuration."""

from __future__ import unicode_literals

__revision__ = "$Id$"

# The name of the default collection
CFG_BIBINGEST_DEFAULT_COLLECTION_NAME = 'DEFAULT'

# If True, pre-create one instance for each storage engine for every storage
# engine. Otherwise pre-create one instance for each storage engine
# for every collection.
CFG_BIBINGEST_ONE_STORAGE_ENGINE_INSTANCE_PER_STORAGE_ENGINE = False
#CFG_BIBINGEST_ONE_STORAGE_ENGINE_INSTANCE_PER_COLLECTION = \
#    not CFG_BIBINGEST_ONE_STORAGE_ENGINE_INSTANCE_PER_STORAGE_ENGINE

# If True, create on the fly a new instance for each ingestion package for every
# new request. Otherwise pre-create one instance for each ingestion package
# for every collection.
CFG_BIBINGEST_ONE_INGESTION_PACKAGE_INSTANCE_PER_REQUEST = False
#CFG_BIBINGEST_ONE_INGESTION_PACKAGE_INSTANCE_PER_COLLECTION = \
#    not CFG_BIBINGEST_ONE_INGESTION_PACKAGE_INSTANCE_PER_REQUEST

# If True, whenever an ingestion package is updated old versions will be kept
CFG_BIBINGEST_VERSIONING = True

# For each collection set the ingestion package type and storage engine.
# Additional settings can be defined here for the storage engines.
CFG_BIBINGEST_COLLECTIONS = {
    'DEFAULT' : {
        'ingestion_package' : {
            'name' : 'default',
        },
        'storage_engine' : {
            'name' : 'mongodb_pymongo',
            #'settings' : {
            #    '_collection_name' : 'DEFAULT'
            #}
        },
    },
    'BLOG' : {
        'ingestion_package' : {
            'name' : 'blog',
        },
        'storage_engine' : {
            'name' : 'mongodb_pymongo',
            'settings' : {
                '_collection_name' : 'BLOG'
            }
        },
    },
    'BLOGPOST' : {
        'ingestion_package' : {
            'name' : 'blogpost',
        },
        'storage_engine' : {
            'name' : 'mongodb_pymongo',
            'settings' : {
                '_collection_name' : 'BLOGPOST'
            }
        },
    },
    'COMMENT' : {
        'ingestion_package' : {
            'name' : 'comment',
        },
        'storage_engine' : {
            'name' : 'mongodb_pymongo',
            'settings' : {
                '_collection_name' : 'COMMENT'
            }
        },
    },
}
