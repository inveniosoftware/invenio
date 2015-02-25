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
"""Ingestion utilities."""

__revision__ = "$Id$"

from .config import \
    CFG_BIBINGEST_COLLECTIONS, \
    CFG_BIBINGEST_DEFAULT_COLLECTION_NAME, \
    CFG_BIBINGEST_ONE_STORAGE_ENGINE_INSTANCE_PER_STORAGE_ENGINE, \
    CFG_BIBINGEST_ONE_INGESTION_PACKAGE_INSTANCE_PER_REQUEST

from .regitry import ingestion_packages, storage_engines

_STORAGE_ENGINES = storage_engines
_INGESTION_PACKAGES = ingestion_packages
_collections = {}

# ****************
# Helper functions
# ****************

prepare_kwargs = lambda **kwargs:kwargs

# **************
# Main functions
# **************

def list(collection = None):
    """
    Returns the list of available collections.
    """

    if collection is not None:
        return CFG_BIBINGEST_COLLECTIONS.get(collection)
    return CFG_BIBINGEST_COLLECTIONS.keys()

def select(collection_name):
    """
    Given a collection name, this function returns the ingestion package
    instance which corresponds to it. CRUD functions can be then exectured
    on that instance.
    """

    if not _collections.has_key(collection_name):
        collection_name = CFG_BIBINGEST_DEFAULT_COLLECTION_NAME

    if CFG_BIBINGEST_ONE_INGESTION_PACKAGE_INSTANCE_PER_REQUEST:
        if CFG_BIBINGEST_ONE_STORAGE_ENGINE_INSTANCE_PER_STORAGE_ENGINE:
            ingestion_package_class, \
            storage_engine_instance, \
            storage_engine_settings = _collections.get(collection_name)
            return ingestion_package_class(storage_engine_instance, storage_engine_settings)
        else:
            ingestion_package_class, \
            storage_engine_instance, \
            dummy = _collections.get(collection_name)
            return ingestion_package_class(storage_engine_instance)

    else:
        if CFG_BIBINGEST_ONE_STORAGE_ENGINE_INSTANCE_PER_STORAGE_ENGINE:
            ingestion_package_instance =  _collections.get(collection_name)
            ingestion_package_instance.reconfigure_storage_engine()
            return ingestion_package_instance
        else:
            ingestion_package_instance =  _collections.get(collection_name)
            return ingestion_package_instance

def _start():
    """
    Populates the private collections dictionary.
    """

    # If we only have on instance per engine we need to temporarily store
    # those instances in a dictionary as we create and reuse them.
    if CFG_BIBINGEST_ONE_STORAGE_ENGINE_INSTANCE_PER_STORAGE_ENGINE:
        storage_engines_instances = {}

    for collection_name, collection_configuration in CFG_BIBINGEST_COLLECTIONS.iteritems():

        # Storage engines
        storage_engine_configuration = collection_configuration.get('storage_engine')
        storage_engine_name = storage_engine_configuration.get('name')
        storage_engine_settings = storage_engine_configuration.get('settings')
        if CFG_BIBINGEST_ONE_STORAGE_ENGINE_INSTANCE_PER_STORAGE_ENGINE:
            # One storage engine per storage engine.
            # Since each collection might have different settings for the
            # storage engine instance we only instanciate it here without
            # passing any settings.
            storage_engine_instance = \
                storage_engines_instances.get(storage_engine_name)
            if storage_engine_instance is None:
                storage_engine_instance = \
                    _STORAGE_ENGINES.get(storage_engine_name)()
                storage_engines_instances[storage_engine_name] = \
                    storage_engine_instance
        else:
            # One storage engine per collection.
            # In this case we can instantiate the storage engine and pass
            # its collection-specific settings at the same time.
            storage_engine_instance = _STORAGE_ENGINES.get(storage_engine_name)(storage_engine_settings)

        # Ingestion packages
        ingestion_package_configuration = collection_configuration.get('ingestion_package')
        ingestion_package_name = ingestion_package_configuration.get('name')
        if CFG_BIBINGEST_ONE_INGESTION_PACKAGE_INSTANCE_PER_REQUEST:
            ingestion_package_class = _INGESTION_PACKAGES.get(ingestion_package_name)
        else:
            if CFG_BIBINGEST_ONE_STORAGE_ENGINE_INSTANCE_PER_STORAGE_ENGINE:
                ingestion_package_instance = _INGESTION_PACKAGES.get(ingestion_package_name)(storage_engine_instance,
                                                                                             storage_engine_settings)
            else:
                ingestion_package_instance = _INGESTION_PACKAGES.get(ingestion_package_name)(storage_engine_instance)

        # Collections
        if CFG_BIBINGEST_ONE_INGESTION_PACKAGE_INSTANCE_PER_REQUEST:
            _collections[collection_name] = (ingestion_package_class, storage_engine_instance, storage_engine_settings)
        else:
            _collections[collection_name] = (ingestion_package_instance)

_start()
