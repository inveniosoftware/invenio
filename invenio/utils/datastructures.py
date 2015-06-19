# -*- coding: utf-8 -*-
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2014, 2015 CERN.
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

"""Invenio special data structures."""

import re

from collections import MutableMapping
from six import iteritems


class LazyDict(object):

    """Lazy dictionary that evaluates its content when it is first accessed.

    Example:

    .. code-block:: python

        def my_dict():
            from werkzeug.utils import import_string
            return {'foo': import_string('foo')}

        lazy_dict = LazyDict(my_dict)
        # at this point the internal dictionary is empty
        lazy_dict['foo']
    """

    def __init__(self, function=dict):
        """Initialize lazy dictionary with given function.

        :param function: it must return a dictionary like structure
        """
        super(LazyDict, self).__init__()
        self._cached_dict = None
        self._function = function

    def _evaluate_function(self):
        self._cached_dict = self._function()

    def __getitem__(self, key):
        """Return item from cache if it exists else create it."""
        if self._cached_dict is None:
            self._evaluate_function()
        return self._cached_dict.__getitem__(key)

    def __setitem__(self, key, value):
        """Set item to cache if it exists else create it."""
        if self._cached_dict is None:
            self._evaluate_function()
        return self._cached_dict.__setitem__(key, value)

    def __delitem__(self, key):
        """Delete item from cache if it exists else create it."""
        if self._cached_dict is None:
            self._evaluate_function()
        return self._cached_dict.__delitem__(key)

    def __getattr__(self, key):
        """Get cache attribute if it exists else create it."""
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
        return iteritems(self._cached_dict)

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

    """Even lazier dictionary (maybe the laziest).

    It does not have content and when a key is accessed it tries to evaluate
    only this key.

    Example:

    .. code-block:: python

        def reader_discover(key):
            from werkzeug.utils import import_string
            return import_string(
                'invenio.jsonalchemy.jsonext.readers%sreader:reader' % (key)
            )

        laziest_dict = LaziestDict(reader_discover)

        laziest_dict['json']
        # It will give you the JsonReader class
    """

    def __init__(self, function=dict):
        """Initialize laziest dictionary with given function.

        :param function: it must accept one parameter (the key of the
            dictionary) and returns the element which will be store that key.
        """
        super(LaziestDict, self).__init__(function)

    def _evaluate_function(self):
        """Create empty dict if necessary."""
        if self._cached_dict is None:
            self._cached_dict = {}

    def __getitem__(self, key):
        if self._cached_dict is None:
            self._evaluate_function()
        if key not in self._cached_dict:
            try:
                self._cached_dict.__setitem__(key, self._function(key))
            except:
                raise KeyError(key)
        return self._cached_dict.__getitem__(key)

    def __contains__(self, key):
        if self._cached_dict is None:
            self._evaluate_function()
        if key not in self._cached_dict:
            try:
                self.__getitem__(key)
            except:
                return False
        return True


class SmartDict(object):

    """This dictionary allows to do some 'smart queries' to its content.

    Example:

    .. code-block:: python

        >>> d = SmartDict()
        >>> d['foo'] = {'a': 'world', 'b':'hello'}
        >>> d['a'] = [ {'b':1}, {'b':2}, {'b':3} ]
        >>> d['a']
        [ {'b':1}, {'b':2}, {'b':3} ]
        >>> d['a[0]']
        {'b':1}
        >>> d['a.b']
        [1,2,3]
        >>> d['a[1:]']
        [{'b':2}, {'b':3}]

    .. note::
        You can't use the reserved words '.', '[', ']' like a key.

        .. code-block:: python

            >>> d['.']
            >>> d[']']
            >>> d['.a']

        It is also not recommended initialize `SmartDict` with keys from
        within the list of reserved words.

        .. code-block:: python

            >>> d = SmartDict({'a': 3, 'b': {'.': 5}})
    """

    split_key_pattern = re.compile('\.|\[')
    main_key_pattern = re.compile('\..*|\[.*')

    def __init__(self, d=None):
        self._dict = d if d is not None else dict()

    def __getitem__(self, key):
        """Return item as `dict.__getitem__` but using 'smart queries'.

        .. note::
            Accessing one value in a normal way, meaning d['a'], is almost as
            fast as accessing a regular dictionary. But using the special
            name convention is a bit slower than using the regular access:

            .. code-block:: python

                >>> %timeit x = dd['a[0].b']
                100000 loops, best of 3: 3.94 us per loop
                >>> %timeit x = dd['a'][0]['b']
                1000000 loops, best of 3: 598 ns per loop
        """
        def getitem(k, v):
            if isinstance(v, dict):
                return v[k]
            elif ']' in k:
                k = k[:-1].replace('n', '-1')
                # Work around for list indexes and slices
                try:
                    return v[int(k)]
                except ValueError:
                    return v[slice(*map(
                        lambda x: int(x.strip()) if x.strip() else None,
                        k.split(':')
                    ))]
            else:
                tmp = []
                for inner_v in v:
                    try:
                        tmp.append(getitem(k, inner_v))
                    except KeyError:
                        continue
                return tmp

        # Check if we are using python regular keys
        try:
            return self._dict[key]
        except KeyError:
            pass

        keys = SmartDict.split_key_pattern.split(key)
        value = self._dict
        for k in keys:
            value = getitem(k, value)
        return value

    def __setitem__(self, key, value, extend=False, **kwargs):
        # check if the key is composed only by special chars
        if key[0] in ['.', ']', '[']:
            # this kind of key is not supported!
            raise KeyError

        if '.' not in key and ']' not in key and not extend:
            self._dict[key] = value
        else:
            keys = SmartDict.split_key_pattern.split(key)
            self.__setitem(self._dict, keys[0], keys[1:], value, extend)

    def __delitem__(self, key):
        """Delete item only from first level dictionary keys."""
        del self._dict[key]

    def __contains__(self, key):

        if '.' not in key and '[' not in key:
            return key in self._dict
        try:
            self[key]
        except:
            return False
        return True

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                and self._dict == other._dict)

    def __iter__(self):
        return iter(self._dict)

    def __len__(self):
        return len(self._dict)

    def keys(self):
        return self._dict.keys()

    def items(self):
        return self._dict.items()

    def iteritems(self):
        """Proxy to `dict.iteritems`."""
        return iteritems(self._dict)

    def iterkeys(self):
        """Proxy to `dict.iterkeys`."""
        return self._dict.iterkeys()

    def itervalues(self):
        """Proxy to `dict.itervalues`."""
        return self._dict.itervalues()

    def has_key(self, key):
        """Return ``True`` if ``key`` is in dictionary."""
        return key in self

    def __repr__(self):
        """Proxy to `dict.__repr__`."""
        return repr(self._dict)

    def __setitem(self, chunk, key, keys, value, extend=False):
        """Helper function to fill up the dictionary."""
        def setitem(chunk):
            if keys:
                return self.__setitem(chunk, keys[0], keys[1:], value, extend)
            else:
                return value

        if key in ['.', ']']:
            chunk[key] = value
        elif ']' in key:  # list
            key = int(key[:-1].replace('n', '-1'))
            if extend:
                if chunk is None:
                    chunk = [None, ]
                else:
                    if not isinstance(chunk, list):
                        chunk = [chunk, ]
                    if key != -1:
                        chunk.insert(key, None)
                    else:
                        chunk.append(None)
            else:
                if chunk is None:
                    chunk = [None, ]
            chunk[key] = setitem(chunk[key])
        else:  # dict
            if extend:
                if chunk is None:
                    chunk = {}
                    chunk[key] = None
                    chunk[key] = setitem(chunk[key])
                elif key not in chunk:
                    chunk[key] = None
                    chunk[key] = setitem(chunk[key])
                else:
                    if keys:
                        chunk[key] = setitem(chunk[key])
                    else:
                        if not isinstance(chunk[key], list):
                            chunk[key] = [chunk[key], ]
                        chunk[key].append(None)
                        chunk[key][-1] = setitem(chunk[key][-1])
            else:
                if chunk is None:
                    chunk = {}
                if key not in chunk:
                    chunk[key] = None
                chunk[key] = setitem(chunk[key])

        return chunk

    def get(self, key, default=None):
        """Return value for given ``key`` or ``default`` value."""
        try:
            return self[key]
        except KeyError:
            return default

    def set(self, key, value, extend=False, **kwargs):
        """Extended standard set function."""
        self.__setitem__(key, value, extend, **kwargs)

    def update(self, E, **F):
        """Proxy `dict` update method."""
        self._dict.update(E, **F)

MutableMapping.register(SmartDict)


class DotableDict(dict):

    """Make nested python dictionaries accessable using dot notation.

    Example:

    .. code-block:: python

        >>> dotable = DotableDict({'a': [{'b': 3, 'c': 5}]})
        >>> dotable.a
        ...  [{'b': 3, 'c': 5}]
    """

    def __getattr__(self, key):
        """Return value from dictionary.

        .. todo:: allow ``dotable.a[0].b``
        """
        return self[key]

    def __setattr__(self, key, value):
        """Set value for given key in dictionary."""
        self[key] = value


def flatten_multidict(multidict):
    """Return flattened dictionary from ``MultiDict``."""
    return dict([(key, value if len(value) > 1 else value[0])
                for (key, value) in multidict.iterlists()])
