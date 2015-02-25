# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014 CERN.
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

"""JSON storage engine interface."""


class Storage(object):

    """Default storage engine interface."""

    #TODO: set return values on success and error and setup a log function
    #TODO: create a query class to mimic SQLAlchemy query object

    def __init__(self, model, **kargs):
        """
        Initialize the Storage with the model.

        :param: model:
        """
        raise NotImplemented

    def save_one(self, json, id=None):
        """Store one json in the storage system."""
        raise NotImplemented

    def save_many(self, jsons, ids=None):
        """Store many JSON as elements on the iterable jsons."""
        raise NotImplemented

    def update_one(self, json, id=None):
        """
        Update one JSON.

        If id is None a field representing the id is expected inside the
        JSON object.
        """
        raise NotImplemented

    def update_many(self, jsons, ids=None):
        """Update many json objects following the same rule as update_one."""
        raise NotImplemented

    def get_one(self, id):
        """Return the json matching the id."""
        raise NotImplemented

    def get_many(self, ids):
        """Return an iterable of json objects which id is inside ids."""
        raise NotImplemented

    def get_field_values(self, ids, field, repetitive_values=True, count=False,
                         include_recid=False, split_by=0):
        """
        Return a list of field values for field for the given ids.

        :param ids: list (or iterable) of integers
        :param repetitive_values: if set to True, returns all values even if
            they are doubled.  If set to False, then return unique values only.
        :param count: in combination with repetitive_values=False, adds to the
            result the number of occurrences of the field.
        :param split: specifies the size of the output.
        """
        raise NotImplemented

    def get_fields_values(self, ids, fields, repetitive_values=True,
                          count=False, include_recid=False, split_by=0):
        """
        Return a dictionary of field values for field for the given ids.

        As in :meth:`~invenio.modules.jsonalchemy.storage.Storage.get_field_values`
        but in this case returns a dictionary with each of
        the fields and the list of field values.
        """
        raise NotImplemented

    def search(self, query):
        """
        Retrieve all entries which match the query JSON prototype document.

        This method should not be used on storage engines without native JSON
        support (e.g., MySQL). Returns a cursor over the matched documents.

        :param query: dictionary specifying the search prototype document
        """
        raise NotImplemented

    def create(self):
        """Create underlying empty storage."""
        raise NotImplemented

    def drop(self):
        """Drop data from underlying storage."""
        raise NotImplemented
