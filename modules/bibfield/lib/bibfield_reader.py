# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011, 2013 CERN.
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
BibField Reader
"""

__revision__ = "$Id$"

import datetime
import six

from invenio.importutils import try_to_eval
from invenio.containerutils import SmartDict

from invenio.bibfield_config_engine import BibFieldParser as FieldParser


class ReaderException(Exception):
    """Exception raised when some error happens reading a blob"""
    pass


class Reader(object):
    """
    Base class inside the hierarchy that contains several method implementations
    that will be shared, eventually, by all the *Reader classes.
    In this particular case this class is expecting that the base format is json,
    so no conversion is needed.
    """
    """Default reader"""

    def __init__(self, blob=None, **kwargs):
        """
        :param blob:
        """
        self.blob = blob
        self.json = None
        self._additional_info = kwargs
        # self._additional_info['model'] = kwargs.get('model', '__default__')

        self._parsed = []

    @staticmethod
    def split_blob(blob, schema=None, **kwargs):
        """
        In case of several records inside the blob this method specify how to
        split then and work one by one afterwards.
        """
        raise NotImplementedError()

    @property
    def field_definitions(self):
        return FieldParser.field_definitions()

    @property
    def functions(self):
        from invenio.bibfield_utils import CFG_BIBFIELD_FUNCTIONS
        return CFG_BIBFIELD_FUNCTIONS

    def translate(self):
        """
        It transforms the incoming blob into a json structure using the rules
        described into the field and model definitions.
        To apply this rules it takes into account the type of the reader, which
        in fact means the type of the source format or `master_format`

        :return: Json structure (typically a dictionary)
        """
        if not self.blob:
            raise ReaderException("To perform a 'translate' operation a blob is needed")

        # If we already have the json return it, use add or update to modify it
        if self.json:
            return self.json

        self.json = {}
        self.json['__meta_metadata__'] = {}
        self.json['__meta_metadata__']['__additional_info__'] = self._additional_info
        self.json['__meta_metadata__']['__aliases__'] = {}
        self.json['__meta_metadata__']['__errors__'] = []
        self.json['__meta_metadata__']['__continuable_errors__'] = []
        # if self._additional_info['model'] == '__default__' or \
        #         self._additional_info['model'] not in self.model_definitions:
        #     self.json['__meta_metadata__']['__continuable_errors__']\
        #             .append("Warning - Using 'default' model for 'transalte', given model: '%s'" % (self._additional_info['model'], ))
        #     fields = dict(zip(self.field_definitions.keys(), self.field_definitions.keys()))
        # else:
        #     fields = self.model_definitions[self._additional_info['model']]['fields']
        fields = dict(zip(self.field_definitions.keys(), self.field_definitions.keys()))
        self.add(self.json, self.blob, fields)
        return self.json._dict

    def add(self, json, blob, fields):
        """Adds the list of fields to the json structure"""
        self.json = json if isinstance(json, SmartDict) else SmartDict(json)
        self.blob = blob

        if not self.blob or not self.json:
            raise ReaderException("To perform an 'add' operation a json structure and a blob are needed")

        if not isinstance(fields, dict):
            if isinstance(fields, six.string_types):
                fields = (fields, )
            # try:
            #     model = self.json['__meta_metadata__']['__additional_info__']['model']
            # except KeyError as e:
            #     raise ReaderException('The json structure must contain a model (%s)' % (e, ))

            # if model == '__default__' or model not in self.model_definitions:
            #     self.json['__meta_metadata__']['__continuable_errors__']\
            #         .append("Warning - Using 'default' model for 'add', given model: '%s'" % (model, ))
            #     fields = dict(zip(fields, fields))
            # else:
            #     fields = dict((field, self.model_definitions[model]['fields'].get(field, field))
            #             for field in fields)
            fields = dict(zip(fields, fields))

        self._prepare_blob()

        for field_name, json_id in fields.items():
            self._unpack_rule(json_id, field_name)

        self._post_process_json()


    def set(self, json, field):
        """

        """
        self.json = json if isinstance(json, SmartDict) else SmartDict(json)
        # try:
        #     model = self.json['__meta_metadata__']['__additional_info__']['model']
        # except KeyError as e:
        #     raise ReaderException('The json structure must contain a model (%s)' % (e, ))

        # if model == '__default__' or model not in self.model_definitions:
        #     self.json['__meta_metadata__']['__continuable_errors__']\
        #             .append("Warning - Using 'default' model for 'add', given model: '%s'" % (model, ))
        #     json_id = field
        # else:
        #     json_id = self.model_definitions[model]['fields'].get(field, field)
        json_id = field

        try:
            rule = self.field_definitions[json_id]
        except KeyError:
            rule = {}
            self.json['__meta_metadata__']['__continuable_errors__']\
                    .append("Adding a new field '%s' without definition" % (field))

        try:
            if self.json['__meta_metadata__']['__additional_info__']['master_format'] in rule['rules']:
                rule_def = rule['rules'][self.json['__meta_metadata__']['__additional_info__']['master_format']][0]
                rule_type = 'creator'
            elif 'derived' in rule['rules']:
                rule_def = rule['rules']['derived'][0]
                rule_type = 'derived'
            elif 'calculated' in rule['rules']:
                rule_def = rule['rules']['calculated'][0]
                rule_type = 'calculated'
            else:
                rule_def = {}
                rule_type = 'UNKNOWN'
        except KeyError:
            rule_def = {}
            rule_type = 'UNKNOWN'

        self.json['__meta_metadata__'][field] = self._find_meta_metadata(json_id, field, rule_type, rule, rule_def)

    def update(self, json, blob, fields=None):
        """
        Tries to update the json structure with the fields given.
        If no fields are given then it will try to update all the fields inside
        the json structure.
        """

        if not blob or not blob:
            raise ReaderException("To perform an 'add' operation a json structure and a blob are needed")

        # try:
        #     model = json['__meta_metadata__']['__additional_info__']['model']
        # except KeyError as e:
        #     raise ReaderException('The json structure must contain a model (%s)' % (e, ))

        if not fields:
            fields = dict(zip(json.keys(), json.keys()))
            # if model == '__default__' or model not in self.model_definitions:
            #     json['__meta_metadata__']['__continuable_errors__']\
            #         .append("Warning - Using 'default' model for 'update', given model: '%s'" % (model, ))
            # else:
            #     fields = dict(fields, **self.model_definitions[model]['fields'])
        elif not isinstance(fields, dict):
            if isinstance(fields, six.string_types):
                fields = (fields, )
            # if model == '__default__' or model not in self.model_definitions:
            #     json['__meta_metadata__']['__continuable_errors__']\
            #         .append("Warning - Using 'default' model for 'update', given model: '%s'" % (model, ))
            #     fields = dict(zip(fields, fields))
            # else:
            #     fields = dict((field, self.model_definitions[model]['fields'].get(field, field))
            #             for field in fields)
            fields = dict(zip(fields, fields))

#         for key in fields.keys():
#             del json['key']

        self.add(json, blob, fields)


    def validate(self, reset=True):
        """docstring for validate"""
        pass

    def _prepare_blob(self, *args, **kwargs):
        """
        Responsible of doing any kind of transformation over the blob before the
        translation begins
        """
        raise NotImplemented

    def _get_elements_from_blob(self, regex_key):
        """
        Should handle 'entire_record' and '*'
        Not an iterator!
        """
        raise NotImplemented


    def _unpack_rule(self, json_id, field_name=None):
        """From the field definitions extract the rules an tries to apply them"""
        try:
            rule_def = self.field_definitions[json_id]
        except KeyError as e:
            self.json['__meta_metadata__']['__continuable_errors__'].append("Error - Unable to find '%s' field definition" % (json_id, ))
            return False

        # if not field_name:
        #     model = self.json['__meta_metadata__']['__additional_info__']['model']
        #     if model == '__default__' or model not in self.model_definitions:
        #         field_name = json_id
        #     else:
        #         field_name = self.model_definitions[model].get(json_id, json_id)
        field_name = json_id

        # Undo the workaround for [0] and [n]
        if isinstance(rule_def, list):
            return all(map(self._unpack_rule, rule_def))

        # Already parsed, avoid doing it again
        if (json_id, field_name) in self._parsed:
            return field_name in self.json

        self._parsed.append((json_id, field_name))
        return self._apply_rules(json_id, field_name, rule_def) or \
                self._apply_virtual_rules(json_id, field_name, rule_def)

    def _apply_rules(self, json_id, field_name, rule_def):
        """Tries to apply a 'creator' rule"""
        applied = False
        for rule in rule_def['rules'].get(
                self.json['__meta_metadata__']['__additional_info__']['master_format'], []):
            elements = self._get_elements_from_blob(rule['source_tag'])
            if not elements:
                self._set_default_value(json_id, field_name)
                return False
            if not self._evaluate_decorators(rule):
                return False
            if 'entire_record' in rule['source_tag'] or '*' in rule['source_tag']:
                try:
                    value = try_to_eval(rule['value'], self.functions, value=elements, self=self.json)
                    self._remove_none_values(value)
                    info = self._find_meta_metadata(json_id, field_name, 'creator', rule, rule_def)
                    if 'json_ext' in rule_def:
                        value = rule_def['json_ext']['dumps'](value)
                    self.json.set(field_name, value, extend=True)
                    self.json['__meta_metadata__.%s' % (SmartDict.main_key_pattern.sub('', field_name), )] = info
                    applied = True
                except Exception as e:
                    self.json['__meta_metadata__']['__errors__']\
                            .append('Rule Error - Unable to apply rule for field %s - %s' % (field_name, str(e)),)
                    applied = False

            else:
                for element in elements:
                    if not isinstance(element, (list, tuple)):
                        element = (element, )
                    applied = False
                    for e in element:
                        if rule['only_if_master_value'] and \
                           not all(try_to_eval(rule['only_if_master_value'], self.functions, value=e, self=self.json)):
                            applied = applied or False
                        else:
                            try:
                                value = try_to_eval(rule['value'], self.functions, value=e, self=self.json)
                                self._remove_none_values(value)
                                info = self._find_meta_metadata(json_id, field_name, 'creator', rule, rule_def)
                                if 'json_ext' in rule_def:
                                    value = rule_def['json_ext']['dumps'](value)
                                self.json.set(field_name, value, extend=True)
                                self.json['__meta_metadata__.%s' % (SmartDict.main_key_pattern.sub('', field_name), )] = info
                                applied = applied or True
                            except Exception as e:
                                self.json['__meta_metadata__']['__errors__']\
                                        .append('Rule Error - Unable to apply rule for field %s - %s' % (field_name, str(e)),)
                                applied = applied or False

        if field_name not in self.json or not applied:
            self._set_default_value(json_id, field_name)

        return applied

    def _apply_virtual_rules(self, json_id, field_name, rule_def):
        """Tries to apply either a 'derived' or 'calculated' rule"""
        rules = []
        rules.append(('calculated', rule_def['rules'].get('calculated', [])))
        rules.append(('derived', rule_def['rules'].get('derived', [])))
        for (rule_type, rrules) in rules:
            for rule in rrules:
                if not self._evaluate_decorators(rule):
                    return False
                try:
                    info = self._find_meta_metadata(json_id, field_name, rule_type, rule, rule_def)
                    if rule_type == 'derived' or rule['memoize']:
                        value = try_to_eval(rule['value'], self.functions, self=self.json)
                        if 'json_ext' in rule_def:
                            value = rule_def['json_ext']['dumps'](value)
                        self._remove_none_values(value)
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

    def _evaluate_decorators(self, rule):
        """Evaluates all 'decorators' related with the current rule"""
        if rule['parse_first']:
            map(self._unpack_rule, try_to_eval(rule['parse_first']))
        if rule['depends_on']:
            for key in try_to_eval(rule['depends_on']):
                if key in self.json:
                    continue
                main_key = SmartDict.main_key_pattern.sub('', key)
                if not self._unpack_rule(main_key):
                    return False
        if rule['only_if'] and not all(try_to_eval(rule['only_if'], self.functions, self=self.json)):
            return False
        return True

    def _find_meta_metadata(self, json_id, field_name, rule_type, rule, rule_def):
        """Given one rule fills up the parallel dictionary with the needed meta-metadata"""
        for alias in rule_def.get('aliases', []):
            self.json['__meta_metadata__.__aliases__.%s' % (alias, )] = field_name
        info = {}
        info['timestamp'] = datetime.datetime.now().isoformat()
        if rule_def.get('persistent_identifier', None) is not None:
            info['pid'] = rule_def['persistent_identifier']
        info['memoize'] = rule.get('memoize', None)
        info['type'] = rule_type
        if rule_type in ('calculated', 'derived'):
            info['function'] = (json_id, 'rules', rule_type, 0, 'value')
        elif rule_type == 'UNKNOWN':
            info['function'] = 'UNKNOWN'
            info['source_tag'] = 'UNKNOWN'
        else:
            info['source_tag'] = rule['source_tag']

        if 'json_ext' in rule:
            info['dumps'] = (json_id, 'json_ext', 'dumps')
            info['loads'] = (json_id, 'json_ext', 'loads')

        return info

    def _set_default_value(self, json_id, field_name):
        """
        Finds the default value inside the schema, if any

        :return: tuple containing if the value is required and the default value.
        """
        schema = self.field_definitions[json_id].get('schema', {}).get(json_id)
        if schema and 'default' in schema:
            try:
                value = schema['default']()
                try:
                    value = self.field_definitions[json_id]['json_ext']['dumps'](value)
                except KeyError:
                    pass
                self.json.set(field_name, value, extend=True)
            except Exception, e:
                self.json['__meta_metadata__']['__continuable_errors__']\
                        .append('Default Value CError - Unable to set default value for %s - %s' % (field_name, str(e)))


    def _remove_none_values(self, obj):
        """Handy closure to remove recursively None values from obj"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if value is None:
                    del obj[key]
                else:
                    self._remove_none_values(value)
        if isinstance(obj, list):
            for element in obj:
                if element is None:
                    obj.remove(element)
                else:
                    self._remove_none_values(element)


    def _post_process_json(self):
        """
        Responsible of doing any kind of transformation over the json structure
        after it is created, e.g. pruning the json to delete None values or
        singletons.
        """
        pass

