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

"""
    invenio.modules.jsonalchemy.reader
    ----------------------------------

    Default reader, it could be considered as an interface to be implemented by
    the other readers.
"""
import datetime
import six

from invenio.base.utils import try_to_eval
from invenio.utils.datastructures import SmartDict

from .errors import ReaderException
from .parser import FieldParser, ModelParser
from .registry import functions, parsers


class Reader(object):
    """Default reader"""

    def __init__(self, blob=None, **kwargs):
        """
        :param blob:
        """
        self.blob = blob
        self.json = None
        self._additional_info = kwargs
        self._additional_info['model'] = kwargs.get('model', '__default__')
        self._additional_info['namespace'] = kwargs.get('namespace', None)

        if self._additional_info['namespace'] is None:
            raise ReaderException('A namespace is needed to instantiate a reader')

        if self._additional_info['model'] != '__default__' and \
                isinstance(self._additional_info['model'], six.string_types):
            self._additional_info['model'] = [self._additional_info['model'], ]

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
        """Helper property to get the field definitions from the current namespace"""
        return FieldParser.field_definitions(self.json_additional_info['namespace'])

    @property
    def model_definitions(self):
        """Helper property to get the model definitions from the current namespace"""
        return ModelParser.model_definitions(self.json_additional_info['namespace'])

    @property
    def functions(self):
        """Helper property to get the functions from the current namespace"""
        return functions(self.json_additional_info['namespace'])

    @property
    def json_additional_info(self):
        """Helper property to get the additional infor from the current json obj"""
        try:
            return self.json['__meta_metadata__']['__additional_info__']
        except KeyError:
            return self._additional_info

    def translate(self, blob=None):
        """
        It transforms the incoming blob into a json structure using the rules
        described into the field and model definitions.
        To apply this rules it takes into account the type of the reader, which
        in fact means the type of the source format or `master_format`

        :return: Json structure (typically a dictionary)
        """
        if blob is not None:
            self.blob = blob
            self.json = None

        if self.blob is None:
            raise ReaderException("To perform a 'translate' operation a blob is needed")

        # If we already have the json return it, use add or update to modify it
        if self.json:
            return self.json

        self.json = {}
        self.json['__meta_metadata__'] = {}
        self.json['__meta_metadata__']['__additional_info__'] = self.json_additional_info
        self.json['__meta_metadata__']['__aliases__'] = {}
        self.json['__meta_metadata__']['__errors__'] = []
        self.json['__meta_metadata__']['__continuable_errors__'] = []

        return self.add(self.json, self.blob)

    def add(self, json, blob, fields=None):
        """Adds the list of fields to the json structure"""
        self.json = json if isinstance(json, SmartDict) else SmartDict(json)
        self.blob = blob

        if self.blob is None or self.json is None:
            raise ReaderException("To perform an 'add' operation a json structure and a blob are needed")

        self._prepare_blob()

        if self.json_additional_info['model'] == '__default__':
            self.json_additional_info['model'] = \
                self.guess_model_from_input()

        if not isinstance(fields, dict):
            if isinstance(fields, six.string_types):
                fields = (fields, )
            fields = self._get_fields_from_model(fields)

        for field_name, json_id in fields.items():
            self._unpack_rule(json_id, field_name)

        self._post_process_json()

        return self.json._dict

    def set(self, json, field, value=None):
        """
        When adding a new field to the json object tries to find as much information
        about this field as possible and attaches it to the json object.
        ``self.json['__meta_metadata__'][field]``
        """
        self.json = json if isinstance(json, SmartDict) else SmartDict(json)

        if field in self.json['__meta_metadata__']:
            if value:
                self.json[field] = value
            return self.json._dict

        try:
            model = self.json_additional_info['model']
        except KeyError as e:
            raise ReaderException('The json structure must contain a model (%s)' % (e, ))

        json_id = ModelParser.resolve_models(model, self.json_additional_info['namespace']).get(field, field)

        try:
            #FIXME: find solution for cases like authors or keywords
            rule_def = self.field_definitions[json_id]
        except KeyError:
            rule_def = {}
            self.json['__meta_metadata__']['__continuable_errors__']\
                    .append("Adding a new field '%s' without definition" % (field))

        try:
            if self.json_additional_info['master_format'] in rule_def['rules']:
                rule = rule_def['rules'][self.json_additional_info['master_format']][0]
                rule_type = 'creator'
            elif 'derived' in rule_def['rules']:
                rule = rule_def['rules']['derived'][0]
                rule_type = 'derived'
            elif 'calculated' in rule_def['rules']:
                rule = rule_def['rules']['calculated'][0]
                rule_type = 'calculated'
            else:
                rule = {}
                rule_type = 'UNKNOWN'
        except KeyError:
            rule = {}
            rule_type = 'UNKNOWN'

        self.json['__meta_metadata__'][field] = \
                self._find_meta_metadata(json_id, field, rule_type, rule, rule_def)

        if value:
            self.json[field] = value

        return self.json._dict

    def update(self, json, blob, fields=None):
        """
        Tries to update the json structure with the fields given.
        If no fields are given then it will try to update all the fields inside
        the json structure.
        """

        if not blob or not json:
            raise ReaderException("To perform an 'update' operation a json structure and a blob are needed")

        self.json = json if isinstance(json, SmartDict) else SmartDict(json)
        self.blob = blob

        try:
            model = self.json_additional_info['model']
        except KeyError as e:
            raise ReaderException('The json structure must contain a model (%s)' % (e, ))

        if not fields:
            fields = dict(zip(json.keys(), json.keys()))
            fields.update(ModelParser.resolve_models(model,
                self.json_additional_info['namespace']).get('fields', {}))
        elif not isinstance(fields, dict):
            if isinstance(fields, six.string_types):
                fields = (fields, )

            fields = dict((field, ModelParser.resolve_models(model,
                self.json_additional_info['namespace']).get('fields', {}).get(field, field))
                          for field in fields)

        return self.add(json, blob, fields)

    def guess_model_from_input(self):
        """
        Dummy method to guess the model of a given input.
        Should be redefined in the dedicated readers.

        .. seealso:: modules :py:mod:`invenio.modules.jsonalchemy.jsonext.readers`
        """
        return '__default__'

    def _prepare_blob(self, *args, **kwargs):
        """
        Responsible of doing any kind of transformation over the blob before the
        translation begins

        .. seealso:: modules :py:mod:`invenio.modules.jsonalchemy.jsonext.readers`
        """
        raise NotImplementedError()

    def _get_elements_from_blob(self, regex_key):
        """
        Should handle 'entire_record' and '*'
        Not an iterator!

        .. seealso:: modules :py:mod:`invenio.modules.jsonalchemy.jsonext.readers`       
        """
        raise NotImplementedError()

    def _get_fields_from_model(self, fields=None):
        """
        Helper function to get all the fields from the current model (if any)

        :param fields: List containing the name of the fields to disambiguate.
            If None searches for all possible fields.
        """
        if self.json_additional_info['model'] == '__default__' or \
                all(model not in self.model_definitions for model in self.json_additional_info['model']):
            if not fields:
                return dict(zip(self.field_definitions.keys(), self.field_definitions.keys()))
            else:
                return dict(zip(fields, fields))
        else:
            full_model = ModelParser.resolve_models(self.json_additional_info['model'],
                    self.json_additional_info['namespace'])
            if not fields:
                return full_model['fields']
            else:
                return dict((field, full_model.get(field, field))
                            for field in fields)
        return dict()

    def _unpack_rule(self, json_id, field_name=None):
        """From the field definitions extract the rules an tries to apply them"""
        try:
            rule_def = self.field_definitions[json_id]
        except KeyError as e:
            self.json['__meta_metadata__']['__continuable_errors__']\
                    .append("Error - Unable to find '%s' field definition" % (json_id, ))
            return False

        if not field_name:
            field_name = self._get_fields_from_model((json_id, ))[json_id]

        # Undo the workaround for [0] and [n]
        if isinstance(rule_def, list):
            return all(map(self._unpack_rule, rule_def))

        # Already parsed, avoid doing it again
        if (json_id, field_name) in self._parsed:
            return field_name in self.json

        self._parsed.append((json_id, field_name))
        apply_rule = self._apply_rules(json_id, field_name, rule_def)
        apply_virtual_rule = self._apply_virtual_rules(json_id, field_name, rule_def)
        return  apply_rule or apply_virtual_rule

    def _apply_rules(self, json_id, field_name, rule_def):
        """Tries to apply a 'creator' rule"""
        applied = False
        for rule in rule_def['rules'].get(
                self.json_additional_info['master_format'], []):
            elements = self._get_elements_from_blob(rule['source_tag'])
            if not elements:
                self._set_default_value(json_id, field_name)
                return False
            if not self._evaluate_decorators(rule):
                return False
            if 'entire_record' in rule['source_tag'] or '*' in rule['source_tag']:
                try:
                    value = try_to_eval(rule['value'], self.functions, value=elements, self=self.json)
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
                           not all(try_to_eval(rule['only_if_master_value'],
                               self.functions, value=e, self=self.json)):
                            applied = applied or False
                        else:
                            try:
                                value = try_to_eval(rule['value'], self.functions,
                                        value=e, self=self.json)
                                info = self._find_meta_metadata(json_id,
                                        field_name, 'creator', rule, rule_def)
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

    def _find_meta_metadata(self, json_id, field_name, rule_type=None, rule=None, rule_def=None):
        """Given one rule fills up the parallel dictionary with the needed meta-metadata"""
        if rule_def is None:
            rule_def = self.field_definitions[json_id]
        if rule is None or rule_type is None:
            if self.json_additional_info['master_format'] in rule_def['rules']:
                rule = rule_def['rules'][self.json_additional_info['master_format']][0]
                rule_type = 'creator'
            elif 'derived' in rule_def['rules']:
                rule = rule_def['rules']['derived'][0]
                rule_type = 'derived'
            elif 'calculated' in rule_def['rules']:
                rule = rule_def['rules']['calculated'][0]
                rule_type = 'calculated'
            else:
                rule = {}
                rule_type = 'UNKNOWN'

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

        #Check the extensions
        for parser_extension in parsers:
            info.update(parser_extension.parser.add_info_to_field(json_id, rule_def))

        return info

    def _set_default_value(self, json_id, field_name):
        """Finds the default value inside the schema, if any"""
        def remove_metadata(field_name):
            """Handy closure to remove metadata when not needed"""
            try:
                del self.json['__meta_metadata__'][field_name]
            except KeyError:
                pass

        schema = self.field_definitions[json_id].get('schema', {}).get(json_id)
        if schema and 'default' in schema:
            try:
                value = schema['default']()
                try:
                    value = self.field_definitions[json_id]['json_ext']['dumps'](value)
                except KeyError:
                    pass
                self.json.set(field_name, value, extend=True)
                self.json['__meta_metadata__.%s' % (SmartDict.main_key_pattern.sub('', field_name), )] = \
                        self._find_meta_metadata(json_id, field_name)
            except Exception as e:
                self.json['__meta_metadata__']['__continuable_errors__']\
                        .append('Default Value CError - Unable to set default value for %s - %s' % (field_name, str(e)))
                remove_metadata(field_name)
        else:
            remove_metadata(field_name)

    def _post_process_json(self):
        """
        Responsible of doing any kind of transformation over the json structure
        after it is created, e.g. pruning the json to delete None values or
        singletons.
        """
        def remove_none_values(obj):
            """Handy closure to remove recursively None values from obj"""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if value is None:
                        del obj[key]
                    else:
                        remove_none_values(value)
            if isinstance(obj, list):
                for element in obj:
                    if element is None:
                        obj.remove(element)
                    else:
                        remove_none_values(element)

        map(remove_none_values, [value for key, value in self.json.items() if not key == '__meta_metadata__'])

