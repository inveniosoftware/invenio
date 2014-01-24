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

import re

from invenio.base.utils import try_to_eval
from invenio.utils.datastructures import SmartDict


class SmartJson(SmartDict):
    """

    """

    def __init__(self, json=None, bson=None):
        super(SmartJson, self).__init__(json)
        self._dict_bson = bson if not bson is None else SmartDict()
        if '__meta_metadata__' in bson:
            try:
                self._dict['__meta_metadata__'].update(bson.get('__meta_metadata__', {}))
            except KeyError:
                self._dict['__meta_metadata__'] = bson.get('__meta_metadata__', {})

    def __getitem__(self, key):
        """

        """
        try:
            return self._dict_bson[key]
        except KeyError:
            #We will try to fin the key inside the json dict and load it
            pass

        main_key = SmartDict.main_key_pattern.sub('', key)
        if main_key in self._dict['__meta_metadata__']['__aliases__']:
            try:
                rest_of_key = SmartDict.main_key_pattern.findall(key)[0]
            except IndexError:
                rest_of_key = ''
            return self[self._dict['__meta_metadata__']['__aliases__'][main_key] + rest_of_key]


        if main_key in self._dict['__meta_metadata__']['__do_not_dump__']:
            self._dict_bson[main_key] = try_to_eval(self._dict['__meta_metadata__'][main_key]['function'],
                                                    self.field_function_context, self=self)
        else:
            try:
                load_function = self._dict['__meta_metadata__'][main_key]['loads'] or 'lambda x:x' # Never going to be used, jus for security
                load_function = try_to_eval(load_function)
                self._dict_bson[main_key] = load_function(self._dict[main_key])
            except KeyError:
                self._dict_bson[main_key] = self._dict[main_key]

        return self._dict_bson[key]


    def __setitem__(self, key, value, extend=False):
        """

        """
        self._dict_bson.set(key, value, extend)
        main_key = SmartDict.main_key_patter.sub('', key)
        try:
            dump_function = self._dict['__meta_metadata__'][main_key]['dumps']
            if dump_function:
                self._dict[main_key] = dump_function(self._dict_bson[main_key])
            else:
                self._dict[main_key] = self._dict_bson[main_key]
        except KeyError:
            self._dict[main_key] = self._dict_bson[main_key]

    def invalidate_cache(self, key):
        """

        """
        main_key = SmartDict.main_key_patter.sub('', key)
        del self._dict_bson[key]

    def dumps(self):
        """docstring for dumps"""
        for key in self._dict_bson:
            try:
                if key in self._dict['__meta_metadata__']['__do_not_dump__']:
                    self._dict[key] = None
                    continue
                dump_function = self._dict['__meta_metadata__'][key]['dumps']
                if dump_function:
                    dump_function = try_to_eval(dump_function)
                    self._dict[key] = dump_function(self._dict_bson[key])
                else:
                    self._dict[key] = self._dict_bson[key]
            except KeyError, e:
                self._dict[key] = self._dict_bson[key]
        return self._dict

    def save(self):
        """docstring for save"""
        raise NotImplementedError()

    @property
    def field_function_context(self):
        """docstring for field_function_context"""
        raise NotImplementedError()
