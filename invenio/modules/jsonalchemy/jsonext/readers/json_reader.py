# -*- coding: utf-8 -*-
##
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

"""
    invenio.modules.jsonalchemy.jsonext.readers.json_reader
    --------------------------------------------------------

"""
from invenio.utils.datastructures import SmartDict
from invenio.base.utils import try_to_eval

from invenio.modules.jsonalchemy.reader import Reader

class JsonReader(Reader):
    """Default reader"""

    __master_format__ = 'json'

    def __init__(self, blob=None, **kwargs):
        """
        :param blob:
        """
        super(JsonReader, self).__init__(blob=blob, **kwargs)
        self._additional_info['master_format'] = 'json'

    @staticmethod
    def split_blob(blob, schema=None, **kwargs):
        """
        In case of several objs inside the blob this method specify how to
        split then and work one by one afterwards.
        """
        return blob.splitlines()

    def _prepare_blob(self, *args, **kwargs):
        self.json.update(self.blob)

    def _get_elements_from_blob(self, regex_key):
        if regex_key in ('entire_record', '*'):
            return self.blob
        return [self.blob.get(key) for key in regex_key]

    def _apply_rules(self, json_id, field_name, rule_def):
        try:
            info = self._find_meta_metadata(json_id, field_name, 'creator', {'source_tag':json_id}, rule_def)
            if 'json_ext' in rule_def and field_name in self.json:
                self.json[field_name] = rule_def['json_ext']['dumps'](self.json[field_name])
            self.json['__meta_metadata__.%s' % (field_name, )] = info
        except KeyError:
            self._set_default_value(json_id, field_name)
        except Exception as e:
            self.json['__meta_metadata__']['__errors__']\
                    .append('Rule Error - Unable to apply rule for field %s - %s' % (field_name, str(e)),)
            return False
        if field_name not in self.json:
            self._set_default_value(json_id, field_name)

        return True

    def _apply_virtual_rules(self, json_id, field_name, rule_def):
        rules = []
        rules.append(('calculated', rule_def['rules'].get('calculated', [])))
        rules.append(('derived', rule_def['rules'].get('derived', [])))
        for (rule_type, rrules) in rules:
            for rule in rrules:
                if not self._evaluate_decorators(rule) and \
                        field_name not in self.json:
                    return False
                try:
                    info = self._find_meta_metadata(json_id, field_name, rule_type, rule, rule_def)
                    if field_name not in self.json:
                        if rule_type == 'derived' or rule['memoize']:
                            value = try_to_eval(rule['value'], self.functions, self=self.json)
                            if 'json_ext' in rule_def:
                                value = rule_def['json_ext']['dumps'](value)
                        else:
                            value = None

                        self.json.set(field_name, value, extend=True)

                    self.json['__meta_metadata__.%s' % (SmartDict.main_key_pattern.sub('', field_name), )] = info
                except Exception as e:
                    self.json['__meta_metadata__']['__continuable_errors__']\
                            .append('Virtual Rule CError - Unable to evaluate %s - %s' % (field_name, str(e)))
                    return False

        if field_name not in self.json:
            self._set_default_value(json_id, field_name)
        return True

reader = JsonReader
