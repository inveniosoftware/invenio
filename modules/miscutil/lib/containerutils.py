## This file is part of Invenio.
## Copyright (C) 2012 CERN.
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
This module contains functions for basic containers (dict, list, str)
"""

import re

def get_substructure(data, path):
    """
    Tries to retrieve a sub-structure within some data. If the path does not
    match any sub-structure, returns None.

    >>> data = {'a': 5, 'b': {'c': [1, 2, [{'f': [57]}], 4], 'd': 'test'}}
    >>> get_substructure(island, "bc")
    [1, 2, [{'f': [57]}], 4]
    >>> get_substructure(island, ['b', 'c'])
    [1, 2, [{'f': [57]}], 4]
    >>> get_substructure(island, ['b', 'c', 2, 0, 'f', 0])
    57
    >>> get_substructure(island, ['b', 'c', 2, 0, 'f', 'd'])
    None

    @param data: a container
    @type data: str|dict|list|(an indexable container)

    @param path: location of the data
    @type path: list|str

    @rtype: *
    """

    if not len(path):
        return data

    try:
        return get_substructure(data[path[0]], path[1:])
    except (TypeError, IndexError, KeyError):
        return None

try:
    from collections import defaultdict
except:
    class defaultdict(dict):
        """
        Python 2.4 backport of defaultdict
        GPL licensed code taken from NLTK - http://code.google.com/p/nltk/
        collections.defaultdict
        originally contributed by Yoav Goldberg <yoav.goldberg@gmail.com>
        new version by Jason Kirtland from Python cookbook.
        <http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/523034>
        """
        def __init__(self, default_factory=None, *a, **kw):
            if (default_factory is not None and
                 not hasattr(default_factory, '__call__')):
                raise TypeError('first argument must be callable')
            dict.__init__(self, *a, **kw)
            self.default_factory = default_factory
        def __getitem__(self, key):
            try:
                return dict.__getitem__(self, key)
            except KeyError:
                return self.__missing__(key)
        def __missing__(self, key):
            if self.default_factory is None:
                raise KeyError(key)
            self[key] = value = self.default_factory()
            return value
        def __reduce__(self):
            if self.default_factory is None:
                args = tuple()
            else:
                args = self.default_factory,
            return type(self), args, None, None, self.items()
        def copy(self):
            return self.__copy__()
        def __copy__(self):
            return type(self)(self.default_factory, self)
        def __deepcopy__(self, memo):
            import copy
            return type(self)(self.default_factory,
                              copy.deepcopy(self.items()))
        def __repr__(self):
            return 'defaultdict(%s, %s)' % (self.default_factory,
                                             dict.__repr__(self))


class SmartDict(object):
    """
    This dictionary allows to do some 'smart queries' to its content::

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
    """

    split_key_pattern = re.compile('\.|\[')
    main_key_pattern = re.compile('\..*|\[.*')

    def __init__(self, d=None):
        self._dict = d if not d is None else dict()

    def __getitem__(self, key):
        """
        As in C{dict.__getitem__} but using 'smart queries'
        """
        def getitem(k, v):
            if isinstance(v, dict):
                return v[k]
            elif ']' in k:
                k = k[:-1].replace('n', '-1')
                #Work around for list indexes and slices
                try:
                    return v[int(k)]
                except ValueError:
                    return v[slice(*map(lambda x: int(x.strip()) if x.strip() else None, k.split(':')))]
            else:
                tmp = []
                for inner_v in v:
                    tmp.append(getitem(k, inner_v))
                return tmp


        #Check if we are using python regular keys
        try:
            return self._dict[key]
        except KeyError:
            pass

        keys = SmartDict.split_key_pattern.split(key)
        value = self._dict
        for k in keys:
            value = getitem(k, value)
        return value

    def __setitem__(self, key, value, extend=False):
        #TODO: Check repeatable fields
        if '.' not in key and ']' not in key and not extend:
            self._dict[key] = value
        else:
            keys = SmartDict.split_key_pattern.split(key)
            self.__setitem(self._dict, keys[0], keys[1:], value, extend)

    def __delitem__(self, key):
        """Note: It only works with first keys"""
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
        return self._dict.iteritems()

    def iterkeys(self):
        return self._dict.iterkeys()

    def itervalues(self):
        return self._dict.itervalues()

    def has_key(self, key):
        return key in self

    def __repr__(self):
        return repr(self._dict)

    def __setitem(self, chunk, key, keys, value, extend=False):
        """ Helper function to fill up the dictionary"""

        def setitem(chunk):
            if keys:
                return self.__setitem(chunk, keys[0], keys[1:], value, extend)
            else:
                return value

        if ']' in key:  # list
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
        else: # dict
            if extend:
                if chunk is None:
                    chunk = {}
                    chunk[key] = None
                    chunk[key] = setitem(chunk[key])
                elif not key in chunk:
                    chunk[key] = None
                    chunk[key] = setitem(chunk[key])
                else:
                    if keys:
                        chunk[key] = setitem(chunk[key])
                    else:
                        if not isinstance(chunk[key], list):
                            chunk[key] = [chunk[key],]
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
        try:
            return self[key]
        except KeyError:
            return default

    def set(self, key, value, extend=False):
        self.__setitem__(key, value, extend)

    def update(self, E, **F):
        self._dict.update(E, **F)
