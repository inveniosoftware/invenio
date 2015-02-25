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
"""The ingestion package interface."""

__revision__ = "$Id$"

from datetime import datetime

try:
    from hashlib import md5
except:
    import md5

from .config import CFG_BIBINGEST_VERSIONING, \
    CFG_BIBINGEST_ONE_STORAGE_ENGINE_INSTANCE_PER_STORAGE_ENGINE

# ********************
# Validation functions
# ********************

class IngestionFieldValidationError(Exception):
    """
    Custom Exception class when field validation errors occur.
    """
    pass

def positive_int(fieldname, value):
    try:
        value = int(value)
        if value > 0:
            return value
        else:
            msg = "For field name %s, received a negative integer, expected a positive integer" % (fieldname,)
            raise IngestionFieldValidationError(msg)
    except:
        msg = "For field name %s, received a non integer, expected a positive integer" % (fieldname,)
        raise IngestionFieldValidationError(msg)

def valid_string(fieldname, value):
    if not value or not (isinstance(value, str) or isinstance(value, unicode)):
        msg = "For field name %s, received an invalid or zero length string, expected a non zero length string" % (fieldname,)
        raise IngestionFieldValidationError(msg)
    else:
        return value

_STANDARD_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
def valid_date(fieldname, value):
    if isinstance(value, datetime):
        return str(value.strftime(_STANDARD_TIME_FORMAT))
    else:
        try:
            if isinstance(datetime.strptime(value , _STANDARD_TIME_FORMAT), datetime):
                return value
        except:
            msg = "For field name %s, received an unrecognizable datetime format '%s', expected a string like '2002-04-18 14:57:11' or an instance of datetime.datetime" % (fieldname, str(value))
            raise IngestionFieldValidationError(msg)

def valid_bit(dummy, value):
    if value:
        return 1
    return 0

_ACCEPTED_FIELD_NAMES = {
    # Don't use underscores ('_') for the field names.

    # example
    # 'fieldname': (default_value, validation_function),

    # the ingestion package submission ID
    'subid' :   (lambda:'0', valid_string),

    # the ingestion package record ID
    'recid' :   (lambda:0, positive_int),

    # the date on which the ingestion package was submitted
    'date' :    (lambda:datetime.now().strftime(_STANDARD_TIME_FORMAT), valid_date),

    # the ingestion package itself
    'content' : (lambda:None, valid_string),

    # the source of the ingestion package
    'source' :  (lambda:None, valid_string),
}

if CFG_BIBINGEST_VERSIONING:
    version = {
        # the version of the ingestion package
        'version' :  (lambda:1, valid_bit),
    }
    _ACCEPTED_FIELD_NAMES.update(version)

_ACCEPTED_FIELD_OPERATORS = (

    #'value', # When no operator is used, the "value" keyword is reserved

    # values greater than this
    'from',

    # values greater or equal than this
    'and_from',

    # values lower than this
    'to',

     # values lower or equal than this
    'and_to',

    # this value should be treated as a regular expression
    'regex',

     # range of values
    'in',

    # sort results ascending
    'sort_by_asc',

    # sort results descending
    'sort_by_desc',

    # group results
    'group_by',

    # limit the number results
    'limit',

    # skip this number of results from the beginning
    'skip',

)

class IngestionPackage(object):
    """The Ingestion Package default class"""

    def __init__(self, storage_engine_instance, storage_engine_settings = None):
        """
        The constructor.
        """
        self._accepted_field_names     = _ACCEPTED_FIELD_NAMES
        self._accepted_field_operators = _ACCEPTED_FIELD_OPERATORS
        self._storage_engine           = storage_engine_instance
        self._storage_engine_settings  = storage_engine_settings
        if self._storage_engine_settings is not None:
            self.reconfigure_storage_engine()

    def reconfigure_storage_engine(self):
        """
        Reconfigures the storage engine according to the given settings.
        """

        self._storage_engine.reconfigure(self._storage_engine_settings)

    # Helper functions
    def _parse_kwargs(self, kwargs):
        """
        Parses the given kwargs based on the list of accepted field names and
        operators and returns a dictionary.
        """

        parsed_kwargs = {}

        if kwargs is None:
            return parsed_kwargs

        for kwarg_key, kwarg_value in kwargs.iteritems():
            # Split the fieldname from the operator
            kwarg_key_field_name_and_operator = kwarg_key.split('_', 1)
            if len(kwarg_key_field_name_and_operator) == 1:
                # Received a fieldname without any operators
                kwarg_key_field_name, kwarg_key_field_operator = (kwarg_key_field_name_and_operator[0], '')
            else:
                # Received a fieldname with an operator
                kwarg_key_field_name, kwarg_key_field_operator = kwarg_key_field_name_and_operator
            if kwarg_key_field_name:
                # Check if this field name is in the list of accpeted field names
                if kwarg_key_field_name in self._accepted_field_names.keys():
                    # Check if this field name is already in the list of parsed keyword arguments
                    if parsed_kwargs.has_key(kwarg_key_field_name):
                        # Check if there is an operator set for this field name
                        if kwarg_key_field_operator:
                            # Check if the operator is in the list of accepted field operators
                            if kwarg_key_field_operator in self._accepted_field_operators:
                                # Add this field operator and its value to the parsed keyword arguments
                                parsed_kwargs[kwarg_key_field_name][kwarg_key_field_operator] = kwarg_value
                        else:
                            # No field operator was set, therefore add the value for this field
                            # to the parser keyword arguments
                            kwarg_value = self._accepted_field_names[kwarg_key_field_name][1](kwarg_key_field_name, kwarg_value)
                            parsed_kwargs[kwarg_key_field_name]['value'] = kwarg_value
                    else:
                        # This is a new field name. Check if an operator was set for this field name
                        if kwarg_key_field_operator:
                            # Check if the operator is in the list of accepted field operators
                            if kwarg_key_field_operator in self._accepted_field_operators:
                                # Add this field operator and its value to the parsed keyword arguments
                                parsed_kwargs[kwarg_key_field_name] = { kwarg_key_field_operator : kwarg_value }
                        else:
                            # No field operator was set, therefore add the value for this field
                            # to the parser keyword arguments
                            kwarg_value = self._accepted_field_names[kwarg_key_field_name][1](kwarg_key_field_name, kwarg_value)
                            parsed_kwargs[kwarg_key_field_name] = { 'value' : kwarg_value }
            else:
                # The kwarg_key_field_name is empty, it means we have
                # an operator like filter, skip, etc
                if kwarg_key_field_operator in self._accepted_field_operators:
                    if parsed_kwargs.has_key('_operators'):
                        parsed_kwargs['_operators'][kwarg_key_field_operator] = kwarg_value
                    else:
                        parsed_kwargs['_operators'] = { kwarg_key_field_operator : kwarg_value }

        if CFG_BIBINGEST_VERSIONING:
            # Set the latest version, unless it has been explicitly set
            version_field_name = 'version'
            version_default_value = self._accepted_field_names[version_field_name][0]()
            parsed_kwargs.setdefault(version_field_name, { 'value' : version_default_value })

        return parsed_kwargs

    def _complete_parsed_kwargs(self, parsed_kwargs):
        """
        Completes the dictionary of parsed_kwargs with the necessary default values.
        """

        for items in self._accepted_field_names.iteritems():
            fieldname = items[0]
            default_value = items[1][0]()
            if fieldname not in parsed_kwargs.keys() and default_value is not None:
               parsed_kwargs[fieldname] = { 'value' : default_value }
        return parsed_kwargs

    # Implement all the CRUD functions: create, read, update and delete

    # Read one
    def get_one(self, unique_id):
        """
        Retrieves the ingestion package from the database given its unique ID.
        """

        # TODO: what if we have concurrent requests and the storage engine
        # gets reconfigured before actually executing the query?
        if CFG_BIBINGEST_ONE_STORAGE_ENGINE_INSTANCE_PER_STORAGE_ENGINE:
            self.reconfigure_storage_engine()
        return self._storage_engine.get_one(unique_id)

    # Read many
    def get_many(self, **kwargs):
        """
        Retrieves all the ingestion packages from the database that match the given
        arguments. Arguments must comply to a specified list of argument names.
        """

        parsed_kwargs = self._parse_kwargs(kwargs)

        if CFG_BIBINGEST_ONE_STORAGE_ENGINE_INSTANCE_PER_STORAGE_ENGINE:
            self.reconfigure_storage_engine()
        return self._storage_engine.get_many(parsed_kwargs)

    # Create one
    def store_one(self, **kwargs):
        """
        Stores the ingestion package into the database.
        Returns the id of the ingestion_package in the storage engine.
        """

        parsed_kwargs = self._parse_kwargs(kwargs)
        parsed_kwargs = self._complete_parsed_kwargs(parsed_kwargs)

        if CFG_BIBINGEST_ONE_STORAGE_ENGINE_INSTANCE_PER_STORAGE_ENGINE:
            self.reconfigure_storage_engine()
        # TODO: add optional check to make sure we don't store duplicates
        # could do a get_many before storing to check if any results come up
        return self._storage_engine.store_one(parsed_kwargs)

    # Create many
    def store_many(self, ingestion_packages):
        """
        Stores the ingestion packages into the database.
        Must be given an iterable of dictionaries as input.
        Each dictionary must contain "key: value" pairs containing field names and
        their values as they would have been give to the store_ingestion_package
        function.
        """

        data = []
        for ingestion_package in ingestion_packages:
            parsed_kwargs = self._parse_kwargs(ingestion_package)
            parsed_kwargs = self._complete_parsed_kwargs(parsed_kwargs)
            data.append(parsed_kwargs)

        if CFG_BIBINGEST_ONE_STORAGE_ENGINE_INSTANCE_PER_STORAGE_ENGINE:
            self.reconfigure_storage_engine()
        # TODO: add optional check to make sure we don't store duplicates
        # could do a get_many before storing to check if any results come up
        return self._storage_engine.store_many(data)

    # Delete one
    def remove_one(self, unique_id):
        """
        Removes the ingestion package given its unique ID.
        """

        if CFG_BIBINGEST_ONE_STORAGE_ENGINE_INSTANCE_PER_STORAGE_ENGINE:
            self.reconfigure_storage_engine()
        return self._storage_engine.remove_one(unique_id)

    # Delete many
    def remove_many(self, **kwargs):
        """
        Removes the ingestion packages based on the given arguments.
        """

        parsed_kwargs = self._parse_kwargs(kwargs)

        if CFG_BIBINGEST_ONE_STORAGE_ENGINE_INSTANCE_PER_STORAGE_ENGINE:
            self.reconfigure_storage_engine()

        if CFG_BIBINGEST_VERSIONING:
            # MAYBE: check if version is set as 0 (old versions) and don't continue?
            version_field_name = 'version'
            version_default_value = self._accepted_field_names[version_field_name][0]()
            #changes = { version_field_name : int( not version_default_value ) }
            #parsed_changes = self._parse_kwargs(changes)
            parsed_changes = { version_field_name : { 'value' : int( not version_default_value ) } }
            return self._storage_engine.update_many(parsed_changes, parsed_kwargs)
        else:
            return self._storage_engine.remove_many(parsed_kwargs)

    # Update one
    def update_one(self, changes = None, **kwargs):
        """
        Updates one ingestion package (the first one found) matching the kwargs
        according to the changes dictionary.
        The changes dictionary must contain "key: value" pairs containing field names
        and their values as they would have been given to the
        store_ingestion_package function.
        """

        parsed_kwargs  = self._parse_kwargs(kwargs)

        if CFG_BIBINGEST_ONE_STORAGE_ENGINE_INSTANCE_PER_STORAGE_ENGINE:
            self.reconfigure_storage_engine()

        if CFG_BIBINGEST_VERSIONING:
            version_field_name = 'version'
            version_default_value = self._accepted_field_names[version_field_name][0]()
            matching_entries = self._storage_engine.get_many(parsed_kwargs)
            for matching_entry in matching_entries:
                matching_entry.update({ version_field_name : int( not version_default_value ) })
                parsed_matching_entry = self._parse_kwargs(matching_entry)
                self._storage_engine.store_one(parsed_matching_entry)
                break

        date_field_name = 'date'
        date_now_value  = datetime.now().strftime(_STANDARD_TIME_FORMAT)
        date_changes    = { date_field_name : date_now_value }
        changes.update(date_changes)
        parsed_changes  = self._parse_kwargs(changes)
        return self._storage_engine.update_one(parsed_changes, parsed_kwargs)

    # Update many
    def update_many(self, changes = None, **kwargs):
        """
        Updates all the ingestion package matching the kwargs
        according to the changes dictionary.
        The changes dictionary must contain "key: value" pairs containing field names
        and their values as they would have been given to the
        store_ingestion_package function.
        """

        parsed_kwargs  = self._parse_kwargs(kwargs)

        if CFG_BIBINGEST_ONE_STORAGE_ENGINE_INSTANCE_PER_STORAGE_ENGINE:
            self.reconfigure_storage_engine()

        if CFG_BIBINGEST_VERSIONING:
            version_field_name = 'version'
            version_default_value = self._accepted_field_names[version_field_name][0]()
            matching_entries = self._storage_engine.get_many(parsed_kwargs)
            # TODO: make this more efficient. Gather all the matching entries,
            # change 'version' for all of them and then run store_many
            # for all of them together
            for matching_entry in matching_entries:
                matching_entry.update({ version_field_name : int( not version_default_value ) })
                parsed_matching_entry = self._parse_kwargs(matching_entry)
                self._storage_engine.store_one(parsed_matching_entry)

        date_field_name = 'date'
        date_now_value  = datetime.now().strftime(_STANDARD_TIME_FORMAT)
        date_changes    = { date_field_name : date_now_value }
        changes.update(date_changes)
        parsed_changes  = self._parse_kwargs(changes)
        return self._storage_engine.update_many(parsed_changes, parsed_kwargs)

    # Other functions

    def count(self):
        """
        Returns the count of total entries for this ingestion package.
        """

        if CFG_BIBINGEST_ONE_STORAGE_ENGINE_INSTANCE_PER_STORAGE_ENGINE:
            self.reconfigure_storage_engine()
        return self._storage_engine.count()

    # Validate
    def validate(self, content, md5_hash):
        """
        Validates the ingestion package by checking its md5 hash.
        """

        try:
            # when we pass to python >= 2.5 we should
            # be able to use md5 from hashlib
            content_md5_hash = md5(content).hexdigest()
        except:
            content_md5_hash = md5.new(content).hexdigest()

        return content_md5_hash == md5_hash
