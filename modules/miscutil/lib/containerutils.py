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
