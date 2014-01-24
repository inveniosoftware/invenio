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
BibField Utils

Helper classes and functions to work with BibField
"""

__revision__ = "$Id$"

import datetime
import os
import re
import six

from invenio.config import CFG_PYLIBDIR
from invenio.pluginutils import PluginContainer
from invenio.containerutils import SmartDict
from invenio.importutils import try_to_eval

from invenio.bibfield_config_engine import BibFieldParser as FieldParser

CFG_BIBFIELD_FUNCTIONS = PluginContainer(os.path.join(CFG_PYLIBDIR, 'invenio', 'bibfield_functions', '*.py'))
CFG_BIBFIELD_PRODUCERS = PluginContainer(os.path.join(CFG_PYLIBDIR, 'invenio', 'bibfield_functions', 'produce_*.py'))


class BibFieldException(Exception):
    """
    General exception to use within BibField
    """
    pass


class InvenioBibFieldContinuableError(Exception):
    """BibField continuable error"""
    pass


class InvenioBibFieldError(Exception):
    """BibField fatal error, @see CFG_BIBUPLOAD_BIBFIELD_STOP_ERROR_POLICY"""


class SmartJson(SmartDict):
    """Base class for record Json structure"""

    def __init__(self, json):
        super(SmartJson, self).__init__(json)
        self._dict_bson = SmartDict()
        self._validator = None

        # if '__meta_metadata__.__additional_info__.model_meta_classes' in self:
        #     meta_classes = [import_string(str_cls)
        #             for str_cls in self['__meta_metadata__.__additional_info__.model_meta_classes']]
        #     self.__class__ = type(self.__class__.__name__,
        #             [self.__class__] + meta_classes, {})

    def __getitem__(self, key):
        """
        Uses the load capabilities to output the information stored in the DB.
        """
        try:
            return self._dict_bson[key]
        except KeyError:
            #We will try to find the key inside the json dict and load it
            pass

        main_key = SmartDict.main_key_pattern.sub('', key)
        if main_key in self._dict['__meta_metadata__']['__aliases__']:
            try:
                rest_of_key = SmartDict.main_key_pattern.findall(key)[0]
            except IndexError:
                rest_of_key = ''
            return self[self._dict['__meta_metadata__']['__aliases__'][main_key] + rest_of_key]
        try:
            if self._dict['__meta_metadata__'][main_key]['type'] == 'calculated':
                self._load_precalculated_value(main_key)
            else:
                self._loads(main_key)
        except KeyError:
            self._loads(main_key)

        return self._dict_bson[key]


    def __setitem__(self, key, value):
        """
        Uses the dumps capabilities to set the items to store them in the DB
        """
        main_key = SmartDict.main_key_pattern.sub('', key)
        if main_key in self:
            self._dict_bson[key] = value
        else:
            from invenio.bibfield import CFG_BIBFIELD_READERS as readers
            reader = readers['bibfield_%sreader.py' % (self['__meta_metadata__']['__additional_info__']['master_format'], )]()
            reader.set(self, main_key)
            self._dict_bson[key] = value

        self._dumps(main_key)

    def __eq__(self, other):
        try:
            for key in self.keys():
                if key in ('__meta_metadata__', ):
                    pass
                if not self.get(k) == other.get(k):
                    return False
        except:
            return False
        return True

    def items(self):
        for key in self.keys():
            yield (key, self[key])

    @property
    def fatal_errors(self):
        """@return All the fatal/non-continuable errors that check_record has found"""
        return self.get('__meta_metadata__.__errors__', [])

    @property
    def continuable_errors(self):
        """@return All the continuable errors that check_record has found"""
        return self.get('__meta_metadata__.__continuable_errors__', [])
    @property
    def validation_errors(self):
        if self._validator is None:
            self.validate()
        return self._validator.errors

    def check_record(self, reset=True):
        """
        Using the checking rules defined inside bibfied configurations files checks
        if the record is well build. If not it stores the problems inside
        self['__error_messages'] splitting then by continuable errors and fatal/non-continuable
        errors
        """
        def check_rules(checker_functions, key):
            """docstring for check_rule"""
            for checker_function in checker_functions:
                if 'all' in checker_function[0] or self['__meta_metadata__.__additional_info__.master_format'] in checker_function[0]:
                    try:
                        try_to_eval("%s(self,'%s',%s)" % (checker_function[1], key, checker_function[2]))
                    except InvenioBibFieldContinuableError, err:
                        self['__meta_metadata__']['__continuable_errors__'].append('Checking CError - ' + str(err))
                    except InvenioBibFieldError, err:
                        self['__meta_metadata__']['__errors__'].append('Checking Error - ' + str(err))

        if reset or '__meta_metadata___.__errors__' not in self or  '__meta_metadata___.__continuable_error__' not in self:
            self['__meta_metadata__']['__errors__'] = []
            self['__meta_metadata__']['__continuable_errors__'] = []

        for key in self.keys():
            try:
                check_rules(FieldParser.field_definitions()[key]['checker'], key)
            except TypeError:
                for kkey in FieldParser.field_definitions()[key]:
                    check_rules(FieldParser.field_definitions()[kkey]['checker'], kkey)
            except KeyError:
                continue

    def get(self, key, default=None, reset_cache=False):
        if reset_cache:
            main_key = SmartDict.main_key_pattern.sub('', key)
            self._load_precalculated_value(main_key, force=True)
        try:
            return self[key]
        except KeyError:
            return default

    def get_persistent_identifiers(self):
        """
        Using _persistent_identifiers_keys calculated fields gets a subset
        of the record containing al persistent indentifiers
        """
        return dict((key, self[key]) for key in self.get('persistent_identifiers_keys', reset_cache=True))

    # def is_empty(self):
    #     """
    #     One record is empty if there is nothing stored inside rec_json or there is
    #     only '__key'
    #     """
    #     if len(self.keys()) == 0 or \
    #         all(key.startswith('__') for key in self.keys()):
    #         return True
    #     return False

    def dumps(self):
        """ """
        for key in self._dict_bson.keys():
            if key == '__meta_metadata__':
                continue
            self._dumps(key)
        return self._dict

    def loads(self):
        """ """
        for key in self._dict.keys():
            if key == '__meta_metadata__':
                continue
            self._loads(key)
        return self._dict_bson._dict

    def produce(self, output, fields=None):
        return CFG_BIBFIELD_PRODUCERS['produce_' + output](self, fields=fields)

    def validate(self):

        def find_schema(json_id):
            schema = FieldParser.field_definitions(self['__meta_metadata__']['__additional_info__']['namespace']).get(json_id, {})
            if isinstance(schema, list):
                for jjson_id in schema:
                    yield FieldParser.field_definitions(self['__meta_metadata__']['__additional_info__']['namespace']).get(jjson_id, {}).get('schema', {})
                raise StopIteration()
            yield schema.get('schema', {})

        if self._validator is None:
            schema = {}
            # model_fields = ModelParser.model_definitions(self['__meta_metadata__']['__additional_info__']['namespace']).get(fields, {})
            # if model_fields:
            #     for field in self.document.keys():
            #         if field not in model_fields:
            #             model_fields[field] = field
            #     model_field = [json_id for json_id in model_fields.values()]
            # else:
            #     model_fields = self.document.keys()

            model_fields = self.document.keys()

            for json_id in model_fields:
                for schema in find_schema(json_id):
                    self.schema.update(schema)
            self._validator = Validator(schema=shema)

        return self._validator.validate(self)

    def _dumps(self, field):
        """ """
        try:
            self._dict[field] = reduce(lambda obj, key: obj[key], \
                    self._dict['__meta_metadata__'][field]['dumps'], \
                    FieldParser.field_definitions(self['__meta_metadata__']['__additional_info__']['namespace']))(self._dict_bson[field])
        except (KeyError, IndexError):
            if self['__meta_metadata__'][field]['memoize'] or \
                    self['__meta_metadata__'][field]['type'] in ('derived', 'creator', 'UNKNOW'):
                self._dict[field] = self._dict_bson[field]

    def _loads(self, field):
        """ """
        try:
            self._dict_bson[field] = reduce(lambda obj, key: obj[key], \
                    self._dict['__meta_metadata__'][field]['loads'], \
                    FieldParser.field_definition(self['__meta_metadata__']['__additional_info__']['namespace']))(self._dict[field])
        except (KeyError, IndexError):
            self._dict_bson[field] = self._dict[field]

    def _load_precalculated_value(self, field, force=False):
        """

        """
        if self._dict['__meta_metadata__'][field]['memoize'] is None:
            func = reduce(lambda obj, key: obj[key], \
                    self._dict['__meta_metadata__'][field]['function'], \
                    FieldParser.field_definitions())
            self._dict_bson[field] = try_to_eval(func, CFG_BIBFIELD_FUNCTIONS, self=self)
        else:
            live_time = datetime.timedelta(0, self._dict['__meta_metadata__'][field]['memoize'])
            timestamp = datetime.datetime.strptime(self._dict['__meta_metadata__'][field]['timestamp'], "%Y-%m-%dT%H:%M:%S")
            if datetime.datetime.now() > timestamp + live_time or force:
                old_value = self._dict_bson[field]
                func = reduce(lambda obj, key: obj[key], \
                    self._dict['__meta_metadata__'][field]['function'], \
                    FieldParser.field_definitions(self['__meta_metadata__']['__additional_info__']['namespace']))
                self._dict_bson[field] = try_to_eval(func, CFG_BIBFIELD_FUNCTIONS, self=self)
                if not old_value == self._dict_bson[field]:
                    #FIXME: trigger update in DB and fire signal to update others
                    pass

    # Legacy methods, try not to use them as they are already deprecated

    def legacy_export_as_marc(self):
        """
        It creates a valid marcxml using the legacy rules defined in the config
        file
        """
        from collections import Iterable
        def encode_for_marcxml(value):
            from invenio.textutils import encode_for_xml
            if isinstance(value, unicode):
                value = value.encode('utf8')
            return encode_for_xml(str(value))

        export = '<record>'
        marc_dicts = self.produce('json_for_marc')
        for marc_dict in marc_dicts:
            content = ''
            tag = ''
            ind1 = ''
            ind2 = ''
            for key, value in marc_dict.iteritems():
                if isinstance(value, six.string_types) or not isinstance(value, Iterable):
                    value = [value]
                for v in value:
                    if v is None:
                        continue
                    if key.startswith('00') and len(key) == 3:
                        # Control Field (No indicators no subfields)
                        export += '<controlfield tag="%s">%s</controlfield>\n' % (key, encode_for_marcxml(v))
                    elif len(key) == 6:
                        if not (tag == key[:3] and ind1 == key[3].replace('_', '') and ind2 == key[4].replace('_', '')):
                            tag = key[:3]
                            ind1 = key[3].replace('_', '')
                            ind2 = key[4].replace('_', '')
                            if content:
                                export += '<datafield tag="%s" ind1="%s" ind2="%s">%s</datafield>\n' % (tag, ind1, ind2, content)
                                content = ''
                        content += '<subfield code="%s">%s</subfield>' % (key[5], encode_for_marcxml(v))
                    else:
                        pass

            if content:
                export += '<datafield tag="%s" ind1="%s" ind2="%s">%s</datafield>\n' % (tag, ind1, ind2, content)

        export += '</record>'
        return export

    def legacy_create_recstruct(self):
        """
        It creates the recstruct representation using the legacy rules defined in
        the configuration file

        #CHECK: it might be a bit overkilling
        """
        from invenio.bibrecord import create_record
        return create_record(self.legacy_export_as_marc())[0]


    # def is_cacheable(self, field):
    #     """
    #     Check if a field is inside the __do_not_cache or not

    #     @return True if it is not in __do_not_cache
    #     """
    #     return not get_main_field(field) in self.rec_json['__do_not_cache']


    # def update_field_cache(self, field):
    #     """
    #     Updates the value of the cache for the given calculated field
    #     """
    #     field = get_main_field(field)
    #     if re.search('^_[a-zA-Z0-9]', field) and not field in self.rec_json['__do_not_cache']:
    #         self.rec_json[field] = self._recalculate_field_value(field)[field]


#TODO: waiting for a pull request to Cerberus to be merged

from cerberus import Validator as ValidatorBase
from cerberus import ValidationError, SchemaError
from cerberus import errors


class Validator(ValidatorBase):
    """

    """

    def __init__(self, schema=None, transparent_schema_rules=True,
                 ignore_none_values=False, allow_unknown=True):
       super(Validator, self).__init__(schema, transparent_schema_rules,
               ignore_none_values, allow_unknown)

    def _validate(self, document, schema=None, update=False):
        self._errors = {}
        self.update = update

        if schema is not None:
            self.schema = schema
        elif self.schema is None:
            raise SchemaError(errors.ERROR_SCHEMA_MISSING)
        if not isinstance(self.schema, dict):
            raise SchemaError(errors.ERROR_SCHEMA_FORMAT % str(self.schema))

        if document is None:
            raise ValidationError(errors.ERROR_DOCUMENT_MISSING)
        if not hasattr(document, 'get'):
            raise ValidationError(errors.ERROR_DOCUMENT_FORMAT % str(document))
        self.document = document

        special_rules = ["required", "nullable", "type"]
        for field, value in self.document.items():

            if self.ignore_none_values and value is None:
                continue

            definition = self.schema.get(field)
            if definition:
                if isinstance(definition, dict):

                    if definition.get("nullable", False) == True \
                       and value is None:  # noqa
                        continue

                    if 'type' in definition:
                        self._validate_type(definition['type'], field, value)
                        if self.errors:
                            continue

                    definition_rules = [rule for rule in definition.keys()
                                        if rule not in special_rules]
                    for rule in definition_rules:
                        validatorname = "_validate_" + rule.replace(" ", "_")
                        validator = getattr(self, validatorname, None)
                        if validator:
                            validator(definition[rule], field, value)
                        elif not self.transparent_schema_rules:
                            raise SchemaError(errors.ERROR_UNKNOWN_RULE %
                                              (rule, field))
                else:
                    raise SchemaError(errors.ERROR_DEFINITION_FORMAT % field)

            else:
                if not self.allow_unknown:
                    self._error(field, errors.ERROR_UNKNOWN_FIELD)

        if not self.update:
            self._validate_required_fields()

        return len(self._errors) == 0
