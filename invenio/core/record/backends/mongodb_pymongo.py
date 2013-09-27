# -*- coding: utf-8 -*-

## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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
    invenio.core.record.backends.mongo_pymongo
    ------------------------------------------

    Configuration:
    RECORD_BACKEND_MONGO_HOST = localhost
    RECORD_BACKEND_MONGO_PORT = 27017
    RECORD_BACKEND_MONGO_DB_NAME = invenio

"""

import pymongo

from flask import current_app


class Storage(object):
    """
    Record storage interface
    """
    #FIXME: manage errors and return values

    def __init__(self, *args, **kwards):
        host = current_app.config.get('RECORD_BACKEND_MONGO_HOST', 'localhost')
        port = current_app.config.get('RECORD_BACKEND_MONGO_PORT', 27017)
        database = current_app.config.get('RECORD_BACKEND_MONGO_DB_NAME', 'invenio')
        self.__connection = pymongo.MongoClient(host=host,port=port)
        self.__database = self.__conection[database]
        self.__collection = self.__database['record_metadata']
        #Create index on recid
        self.__collection.create_index("recid")

    def save_one(self, json, recid=None):
        """Stores one json record in the storage system"""
        if not recid is None:
            json['recid'] = recid
            json['_id'] = recid

        self.__collection.insert(json)

    def save_many(self, jsons, recids=None):
        """
        Stores many json records in the storage system, as elements on the
        iterable jsons
        """
        if not recids is None:
            def add_id(t):
                t[0]['recid'] = t[1]
                t[0]['_id'] = t[1]
                return t[0]
            jsons = impa(add_id, izip(jsons, recids))

        self.__collection.insert(jsons, continue_on_error=True)

    def update_one(self, json, recid=None):
        """
        Updates one json record, if recid is None field recid is expected inside
        the json object
        """
        #FIXME: what if we get only the fields that have change
        if not recid is None:
            json['recid'] = recid
            json['_id'] = recid

        self.__collection.save(json)

    def update_many(self, jsons, recids=None):
        """Update many json records following the same rule as update_one"""
        #FIXME: what if we get only the fields that have change
        if not recids is None:
            def add_id(t):
                t[0]['recid'] = t[1]
                t[0]['_id'] = t[1]
                return t[0]
            jsons = impa(add_id, izip(jsons, recids))

        map(self.__collection.save, jsons)

    def get_one(self, recid):
        """Returns the json record matching the recid"""
        return self.__collection.find_one(recid)

    def get_many(self, recids):
        """Returns an iterable of json records which recid is inside recids"""
        return self.__collection.find({'_id': {'$in':recids}})

    def get_field_values(recids, field, repetitive_values=True, count=False,
            include_recid=False, split_by=0):
        """
        Returns a list of field values for field for the given record ids.

        :param recids: list (or iterable) of integers
        :param repetitive_values: if set to True, returns all values even if
        they are doubled.  If set to False, then return unique values only.
        :param count: in combination with repetitive_values=False, adds to the
        result the number of occurrences of the field.
        :param split: specifies the size of the output.
        """
        raise NotImplementedError()

    def get_fields_values(recids, fields, repetitive_values=True, count=False,
            include_recid=False, split_by=0):
        """
        As in :meth:`get_field_values` but in this case returns a dictionary with each
        of the fields and the list of field values.
        """
        raise NotImplementedError()



