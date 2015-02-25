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
"""The ingestion storage engine interface."""

__revision__ = "$Id$"

class StorageEngine(object):
    """The Ingestion Storage Engine default class"""

    def __init__(self, configuration):
        """
        The constructor.
        """
        for (name, value) in configuration.iteritems():
            setattr(self, name, value)

    def reconfigure(self, configuration):
        """
        """
        pass

    def get_one(self, uid):
        """
        Returns one ingestion package based on its UID.
        """
        pass

    def get_many(self, kwargs):
        """
        Returns many ingestion packages based on the given arguments.
        """
        pass

    def store_one(self, kwargs):
        """
        Sets one ingestion package with the given arguments.
        """
        pass

    def store_many(self, data):
        """
        Sets many ingestion packages, as elements on the iterable data.
        """
        pass

    def remove_one(self, uid):
        """
        Removes one ingestion package based on its UID.
        """
        pass

    def remove_many(self, kwargs):
        """
        Removes many ingestion packages based on the given arguments.
        """
        pass

    def update_one(self, specs, kwargs):
        """
        Updates one ingestion package (the first one found) based on the specs
        with the given arguments.
        """
        pass

    def update_many(self, specs, kwargs):
        """
        Updates many ingestion packages found based on the specs with the
        given arguments.
        """
        pass

    def count(self):
        """
        Returns the count of total entries for the specific ingestion package.
        """
        pass
