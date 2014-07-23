# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013, 2014 CERN.
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

"""Memoisation utilities."""

from abc import ABCMeta, abstractmethod
from random import shuffle

import functools


class MemoizerBase(object):

    """Interface for creating memoizers."""

    __metaclass__ = ABCMeta

    def __init__(self, cache_limit=1000000):
        self.cache = {}
        self.func = lambda *args: args

        if cache_limit:
            self.cache_limit = cache_limit
        else:
            cache_limit = False

    @abstractmethod
    def __call__(self, *args):
        pass

    def __repr__(self):

        """Return the function's docstring."""

        return self.func.__doc__

    def __get__(self, obj, objtype):

        """Support instance methods."""

        return functools.partial(self.__call__, obj)

    def _memoize(self, key, *args):

        """Read the result from cache. If it doesn't exist there, put function
        result into the cache and return it. Check for cache overflow and
        remove elements if there is an overflow.
        """

        if key in self.cache:
            return self.cache[key]
        else:
            value = self.func(*args)
            self.cache[key] = value
            if self.cache_limit and len(self.cache) > self.cache_limit:
                keys = self.cache.keys()
                shuffle(keys)
                to_keep = keys[0:self.cache_limit / 2]
                self.cache = {key: self.cache[key] for key in to_keep}
            return value


class InstanceMethodMemoize(MemoizerBase):

    """Decorator. Caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned
    (not reevaluated). This is the memoizer which should be used for instance
    methods. If the memoized function uses instance variables, you
    should provide all fields' names in instance_variable_names argument.
    The field cache_limit indicates how many records can be memoized.

    Usage.
    .. code-block:: python

        class Foo():
            def __init__(self):
                self.b = 2

            @InstanceMethodMemoize(instance_variables_names=['b'])
            def change_values(c):
                self.b = self.b + c
                return self.b * 2

    If there is more than one instance of this class, they will use the same
    values from the cache if identical values of input variables are provided.
    """

    def __init__(self, instance_variables_names=None, cache_limit=1000000):

        MemoizerBase.__init__(self, cache_limit)

        self.argument_tuple = tuple()
        self.instance_variables_names = instance_variables_names or []

    def __call__(self, func, *args):

        self.func = func

        def wrap(*args, **kwargs):

            """A memoizer wrapper."""

            if kwargs:
                return self.func(*args, **kwargs)
            self.argument_tuple = self._non_local_variables_tuple(args[0])
            all_args = args[1:] + self.argument_tuple
            try:
                key = hash(all_args)
            except TypeError:
                return self.func(*args)
            return self._memoize(key, *args)

        return wrap

    def _non_local_variables_tuple(self, obj):

        """Get a tuple of evaluted arguments
        from instance variable names list
        """

        evaluated_list = [getattr(obj, x)
                          for x in self.instance_variables_names]
        return tuple(evaluated_list)


class Memoize(MemoizerBase):

    """Decorator. Caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned
    (not reevaluated). Should not be used for instance methods.
    """

    def __init__(self, func):

        MemoizerBase.__init__(self)

        self.func = func

    def __call__(self, *args, **kwargs):
        if kwargs:
            return self.func(*args, **kwargs)
        try:
            key = hash(args)
        except TypeError:
            return self.func(*args)

        return self._memoize(key, *args)
