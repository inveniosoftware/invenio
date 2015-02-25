# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013 CERN.
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

"""Json Reader."""

import re

from invenio.modules.jsonalchemy.reader import ModelParser
from invenio.modules.jsonalchemy.reader import Reader


class JsonReader(Reader):
    """JSON reader."""

    __master_format__ = 'json'

    @staticmethod
    def split_blob(blob, schema=None, **kwargs):
        """
        In case of several objs inside the blob this method specify how to
        split then and work one by one afterwards.
        """
        return blob.splitlines()

    def _prepare_blob(self):
        """

        """
        model_fields = ModelParser.resolve_models(
            self._json.model_info.names,
            self._json.additional_info.namespace).get('fields', {})
        model_json_ids = list(model_fields.keys())
        model_field_names = list(model_fields.values())
        for key in list(self._blob.keys()):
            if key in model_field_names and key not in model_json_ids:
                _key = model_json_ids[model_field_names.index(key)]
                self._blob[_key] = self._blob[key]
                del self._blob[key]

    def _get_elements_from_blob(self, regex_key):
        if regex_key in ('entire_record', '*'):
            return self._blob
        elements = []
        for k in regex_key:
            regex = re.compile(k)
            keys = filter(regex.match, self._blob.keys())
            values = []
            for key in keys:
                values.append(self._blob.get(key))
            elements.extend(values)
        return elements

    def _unpack_rule(self, json_id, field_name=None):
        super(JsonReader, self)._unpack_rule(json_id, field_name)

    def _apply_virtual_rules(self, json_id, field_name, rule):
        """JSON if a bit special as you can set the value of this fields"""
        if json_id in self._blob:
            field_defs = []
            field_defs.append(('calculated',
                               rule['rules'].get('calculated', [])))
            field_defs.append(('derived', rule['rules'].get('derived', [])))
            for (field_type, ffield_def) in field_defs:
                for field_def in ffield_def:
                    info = self._find_field_metadata(json_id, field_name,
                                                     field_type, field_def)
                    self._json['__meta_metadata__'][field_name] = info
                    self._json.__setitem__(field_name, self._blob[json_id],
                                           extend=False,
                                           exclude=['decorators', 'extensions'])
                    return
        else:
            super(JsonReader, self)._apply_virtual_rules(json_id, field_name,
                                                         rule)


reader = JsonReader
