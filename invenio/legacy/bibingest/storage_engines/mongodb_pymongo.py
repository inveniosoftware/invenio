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
"""The MongoDB ingestion engine."""

__revision__ = "$Id$"

from invenio.legacy.bibingest.storage_engine_interface import StorageEngine
from invenio.base.config import CFG_LOGDIR

import pymongo
from bson.objectid import ObjectId
from time import sleep, localtime, strftime

# Helper functions for the mappings
# Field mappings
_DO_NOTHING   = lambda x: x
# Operator mappings
_IN           = lambda y, f: [f(i) for i in y]
_SORT_BY_ASC  = lambda y, dummy: y and pymongo.ASCENDING or pymongo.DESCENDING
_SORT_BY_DESC = lambda y, dummy: y and pymongo.DESCENDING or pymongo.ASCENDING

# Instantiation and usage settings for the database
_SETTINGS = {
#   '_authentication_settings': {
#      'user': 'root',
#      'password': '123456',
#   },
    '_connection_settings': {
        'host': 'localhost',
        'port': 27017,
        ## max_pool_size is supported in pymongo versions >= 1.11
        #'max_pool_size': 10,
        'network_timeout': None,
    },
    '_database_name'    : 'invenio',
    '_collection_name'  : 'DEFAULT',
    '_field_mapping'    : {
        'content' : ('content', _DO_NOTHING),
        'subid'   : ('subid',   str),
        'recid'   : ('recid',   int),
        'source'  : ('source',  _DO_NOTHING),
        'date'    : ('date',    _DO_NOTHING),
    },
    '_operator_mapping' : {
        'value'        : ('value',  None),
        'from'         : ('$gt',    None),
        'and_from'     : ('$gte',   None),
        'to'           : ('$lt',    None),
        'and_to'       : ('$lte',   None),
        'regex'        : ('$regex', None),
        'in'           : ('$in',    _IN),
        'sort_by_asc'  : ('sort',   _SORT_BY_ASC),
        'sort_by_desc' : ('sort',   _SORT_BY_DESC),
#        'group_by'     : ('sort',   None),
        'limit'        : ('limit',  int),
        'skip'         : ('skip',   int),
    },
}

# Decorator that takes care of bad connections
def _check_connection(function):
    """
    Decorator function to check and report on the connection.
    It automatically reconnects if needed.
    """
    def retry(*args, **kwargs):
        """
        The function the decorator returns.
        """
        _max_tries = 10
        _sleep_time = 0.1 # in seconds
        count = 0
        while count < _max_tries:
            try:
                return function(*args, **kwargs)
            except pymongo.errors.AutoReconnect, error:
                print('Temporary connection failure: failed to execute %s [%s]. Retrying in %i seconds.' % \
                    (function.__name__, error, _sleep_time))
                if count == _max_tries - 1:
                    print('Connection failure: maximum tries to execute %s reached [%s]' % \
                        (function.__name__, error))
            except AttributeError, error:
                print('Bad connection: failed to execute %s [%s]' % \
                    (function.__name__, error))
            sleep(_sleep_time)
            count += 1
    return retry

def _log(message, error=False):
    """
    Private function that logs the given message
    """
    log = open(CFG_LOGDIR + "/bibingest-%s.%s"
               % (MongoDB.__engine_name__, error and 'err' or 'log'), "a")
    log.write(strftime("%Y-%m-%d %H:%M:%S --> ", localtime()))
    log.write(message)
    log.write("\n")
    log.close()

class MongoDB(StorageEngine):
    """
    The Ingestion Storage Engine Implementation for MongoDB.
    """

    __engine_name__ = 'mongodb_pymongo'

    def __init__(self, configuration = None):
        """
        The constructor.
        """

        self._connection_settings = {}
        self._authentication_settings = {}
        self._database_name = ""
        self._collection_name = ""
        self._field_mapping = {}
        self._operator_mapping = {}

        for (name, value) in _SETTINGS.iteritems():
            setattr(self, name, value)

        if configuration is not None:
            StorageEngine.__init__(self, configuration)

#        if self._authentication_settings:
#            self._user = self._authentication_settings['user']
#            self._password = self._authentication_settings['password']

        self._connection = self._get_connection()
        if self._connection is not None:
            self._database = self._get_database()
            self._collection = self._get_collection()
        else:
            self._database = None
            self._collection = None

    def _get_connection(self):
        """
        Private function.
        Returns a connection to the database server.
        """

        try:
            return pymongo.Connection(**self._connection_settings)
        except pymongo.errors.ConnectionFailure, error:
            print('Connection failure [%s]' % (error,))
            return None

    def _get_database(self):
        """
        Private function.
        Returns a database object.
        """

        return self._connection[self._database_name]

    def _get_collection(self):
        """
        Private function.
        Returns a collection object.
        """

        return self._database[self._collection_name]

    def reconfigure(self, configuration):
        """
        Reconfigures the current instance resetting
        instance variables if necessary.
        """

        if configuration is None or not configuration:
            configuration = _SETTINGS

        for (name, value) in configuration.iteritems():
            setattr(self, name, value)

        #if configuration.has_key('authentication_settings'):
        #    pass

        if configuration.has_key('_connection_settings'):
            self._connection = self._get_connection()
            if self._connection is not None:
                self._database = self._get_database()
                self._collection = self._get_collection()
            else:
                self._database = None
                self._collection = None

        elif configuration.has_key('_database_name'):
            if self._connection is not None:
                self._database = self._get_database()
                self._collection = self._get_collection()
            else:
                self._database = None
                self._collection = None

        elif configuration.has_key('_collection_name'):
            if self._database is not None:
                self._collection = self._get_collection()
            else:
                self._collection = None

    def _translate_kwargs(self, kwargs):
        """
        Private function.
        Given a mapping of argument names, this function translates
        the generic argument names to local specific ones.
        """

        # In the end we will return the translated fields and operators
        translated_fields = {}
        translated_operators = {}

        # First, let's see if we have operators
        operators = kwargs.pop('_operators', None)
        # Example: '_operators': {'limit': 10, 'skip': 20}
        if operators:
            for operator_key, operator_value in operators.iteritems():
            # Example: operator_key = 'limit'
            #          operator_value = 2
                # Get the mapping for that operator
                translated_operator_key, translated_operator_function = \
                    self._operator_mapping.get(operator_key, (None, None))
                if translated_operator_key is not None:
                    # Apply the mapping function on the operator value
                    translated_operator_value = \
                        translated_operator_function is not None and \
                            translated_operator_function(operator_value) or \
                            operator_value
                    # Finally, set the operator
                    translated_operators[translated_operator_key] = \
                            translated_operator_value

        # Now we can parse the various field names
        for field_key, field_value in kwargs.iteritems():
            #
            # Examples: 'date': {'value': 1, 'sort_by_asc': True}
            #           field_key = 'date'
            #           field_value = {'value': 1, 'sort_by_asc': True}
            #
            #           'date': {'and_from': 1, 'to': 5}
            #           field_key = 'date'
            #           field_value = {'and_from': 1, 'to': 5}
            #
            # Get the mapping for this field
            translated_field_key, translated_field_function = \
                self._field_mapping.get(field_key, (field_key, _DO_NOTHING))

            if translated_field_key is not None:
                for field_value_key, field_value_value in field_value.iteritems():
                    # Examples: field_value_key = 'value'
                    #           field_value_value = 1
                    #
                    #           field_value_key = 'sort_by_asc'
                    #           field_value_value = True
                    #
                    # Get the mapping for each operator
                    translated_field_value_key, translated_field_value_function = \
                        self._operator_mapping.get(field_value_key, (None, None))
                    if translated_field_value_key is not None:
                        # Apply the mapping function for the operator
                        # (including the one for the field value) on the field value
                        translated_field_value_value = \
                            translated_field_value_function is not None and \
                            translated_field_value_function(field_value_value, translated_field_function) or \
                            translated_field_function(field_value_value)
                        # Special operator: value. Directly assign
                        # the field value to the field name
                        if translated_field_value_key == 'value':
                            translated_fields[translated_field_key] = \
                                translated_field_value_value
                        # For all the operators that start by '$' assign
                        # a dictionary of operators with their value
                        # to the field name
                        elif translated_field_value_key.startswith('$'):
                            if translated_fields.has_key(translated_field_key):
                                translated_fields[translated_field_key][translated_field_value_key] = \
                                    translated_field_value_value
                            else:
                                translated_fields[translated_field_key] = \
                                    {translated_field_value_key: translated_field_value_value}
                        # Other operators should go into the
                        # translated_operators dictionary
                        else:
                            # Sepcial operator: sort. This operator is parsed
                            # separately as pymongo defines a specific way for
                            # its application
                            if translated_field_value_key == 'sort':
                                if translated_operators.has_key('sort'):
                                    translated_operators['sort'].append((translated_field_key, translated_field_value_value))
                                else:
                                    translated_operators['sort'] = [(translated_field_key, translated_field_value_value)]
                            # All other operators at this point are added into
                            # the translated_operators dictionary
                            else:
                                # the rest of the operators
                                translated_operators[translated_field_value_key] = \
                                    translated_field_value_value

        return translated_fields, translated_operators

    def _check_for_errors(self):
        """
        Checks the database for errors on the last query
        and appends them to the log
        """

        error = self._database.error()
        if error:
            _log(repr(error), True)

    @_check_connection
    def get_one(self, uid):
        """
        Retrieves the ingestion package from the database given its UID.
        """

        out = self._collection.find_one(ObjectId(uid))
        self._check_for_errors()
        return out

    @_check_connection
    def get_many(self, kwargs):
        """
        Searches the database for ingestion packages matching the given criteria.
        Returns an iterator on the results.
        """

        kwargs, operators = self._translate_kwargs(kwargs)
        out = self._collection.find(kwargs, **operators)
        self._check_for_errors()
        return out

    @_check_connection
    def store_one(self, kwargs):
        """
        Stores the ingestion package into the database.
        """

        kwargs, dummy = self._translate_kwargs(kwargs)
        out = self._collection.insert(kwargs)
        self._check_for_errors()
        return out

    @_check_connection
    def store_many(self, data):
        """
        Stores the ingestion packages in data into the database.
        Must be given an iterable as input.
        """
        parsed_data = []
        for datum in data:
            fields, dummy = self._translate_kwargs(datum)
            parsed_data.append(fields)
        out = self._collection.insert(parsed_data, continue_on_error=True)
        self._check_for_errors()
        return out

    @_check_connection
    def remove_one(self, uid):
        """
        Removes the ingestion package from the database given its uid.
        """

        out = self._collection.remove(ObjectId(uid))
        self._check_for_errors()
        return out

    @_check_connection
    def remove_many(self, kwargs):
        """
        Removes the ingestion package from the database given its uid.
        """

        kwargs, dummy = self._translate_kwargs(kwargs)
        out = self._collection.remove(kwargs)
        self._check_for_errors()
        return out

    @_check_connection
    def update_one(self, changes, kwargs):
        """
        Updates the first ingestion package matching the given kwargs
        according to the changes dictionary.
        """

        changes, dummy = self._translate_kwargs(changes)
        kwargs, dummy = self._translate_kwargs(kwargs)
        out = self._collection.update(kwargs, {'$set': changes})
        self._check_for_errors()
        return out

    @_check_connection
    def update_many(self, changes, kwargs):
        """
        Updates all the ingestion packages matching the given kwargs
        according to the changes dictionary.
        """

        changes, dummy = self._translate_kwargs(changes)
        kwargs, dummy = self._translate_kwargs(kwargs)
        out = self._collection.update(kwargs, {'$set': changes}, multi = True)
        self._check_for_errors()
        return out

    @_check_connection
    def count(self):
        """
        Returns the count of total entries for this ingestion package.
        """

        return self.get_many({}).count()

def mongodb_pymongo(configuration = None):
    """
    Instantiates the Ingestion storage engine with the given settings.
    """

    return MongoDB(configuration)

storage_engine = MongoDB
