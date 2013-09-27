# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2012, 2013 CERN.
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
Invenio special data structures
"""


class LazyDict(object):
    """
    Lazy dictionary that evaluates its content when it is first accessed.

    Example of use:

    def my_dict():
        from werkzeug.utils import import_string
        return {'foo': import_string('foo')}

    lazy_dict = LazyDict(my_dict)
    # at this point the internal dictionary is empty
    lazy_dict['foo']
    """
    def __init__(self, function=dict):
        """
        :param function: it must return a dictionary like structure
        """
        super(LazyDict, self).__init__()
        self._cached_dict = None
        self._function = function

    def _evaluate_function(self):
        self._cached_dict = self._function()

    def __getitem__(self, key):
        if self._cached_dict is None:
            self._evaluate_function()
        return self._cached_dict.__getitem__(key)

    def __setitem__(self, key, value):
        if self._cached_dict is None:
            self._evaluate_function()
        return self._cached_dict.__setitem__(key, value)

    def __getattr__(self, key):
        if self._cached_dict is None:
            self._evaluate_function()
        return getattr(self._cached_dict, key)

    def __iter__(self):
        if self._cached_dict is None:
            self._evaluate_function()
        return self._cached_dict.__iter__()

    def iteritems(self):
        if self._cached_dict is None:
            self._evaluate_function()
        return self._cached_dict.iteritems()

    def iterkeys(self):
        if self._cached_dict is None:
            self._evaluate_function()
        return self._cached_dict.iterkeys()

    def itervalues(self):
        if self._cached_dict is None:
            self._evaluate_function()
        return self._cached_dict.itervalues()

    def expunge(self):
        self._cached_dict = None

    def get(self, key, default=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default


class LaziestDict(LazyDict):
    """
    Even lazier dictionary (maybe the laziest), it doesn't have content
    and when a key is accessed it tries to evaluate only this key.

    Example of use:

    def reader_discover(key):
        from werkzeug.utils import import_string
        return import_string('invenio.bibfield_%sreader:reader' % (key))

    laziest_dict = LaziestDict(reader_discover)

    laziest_dict['json']
    # It will give you the JsonReader class
    """

    def __init__(self, function):
        """
        @param function: it must accept one parameter (the key of the dictionary)
        and returns the element which will be store that key.
        """
        super(LaziestDict, self).__init__(function)

    def _evaluate_function(self):
        """
        It doesn't know how to create the full dictionary, in case
        is really needed an empty dictionary is created.
        """
        if self._cached_dict is None:
            self._cached_dict = {}

    def __getitem__(self, key):
        if self._cached_dict is None:
            self._evaluate_function()
        if not key in self._cached_dict:
            try:
                self._cached_dict.__setitem__(key, self._function(key))
            except:
                raise KeyError(key)
        return self._cached_dict.__getitem__(key)

    def __contains__(self, key):
        if self._cached_dict is None:
            self._evaluate_function()
        if not key in self._cached_dict:
            try:
                self.__getitem__(key)
            except:
                return False
        return True


def flatten_multidict(multidict):
    return dict([(key, value if len(value) > 1 else value[0])
                for (key, value) in multidict.iterlists()])
