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
BibField Json Reader
"""

__revision__ = "$Id$"

import os
import re

import sys
if sys.version_info < (2,5):
    def all(list):
        for element in list:
            if not element:
                return False
        return True
    def any(list):
        for element in list:
            if element:
                return True
        return False

from invenio.config import CFG_PYLIBDIR
from invenio.pluginutils import PluginContainer

from invenio.bibfield_utils import BibFieldDict, \
                                   InvenioBibFieldContinuableError, \
                                   InvenioBibFieldError
from invenio.bibfield_config import config_rules


class JsonReader(BibFieldDict):
    """
    Base class inside the hierarchy that contains several method implementations
    that will be shared, eventually, by all the *Reader classes.
    In this particular case this class is expecting that the base format is json,
    so no conversion is needed.
    """

    def __init__(self, blob_wrapper=None, check = False):
        """
        blob -> _prepare_blob(...) -> rec_tree -> _translate(...) -> rec_json -> check_record(...)
        """
        super(JsonReader, self).__init__()
        self.blob_wrapper = blob_wrapper
        self.rec_tree = None  # all record information represented as a tree (intermediate structure)

        self.__parsed = []

        if self.blob_wrapper:
            try:
                self['__master_format'] = self.blob_wrapper.master_format
            except AttributeError:
                pass  # We are retrieving the cached version from the data base containing __master_format

            self._prepare_blob()
            self._translate()
            self._post_process_json()
            if check:
                self.check_record()
            self.is_init_phase = False
        else:
            self['__master_format'] = 'json'

    @staticmethod
    def split_blob(blob):
        """
        In case of several records inside the blob this method specify how to split
        then and work one by one afterwards
        """
        raise NotImplementedError("This method must be implemented by each reader")

    def get_persistent_identifiers(self):
        """
        Using _persistent_identifiers_keys calculated fields gets a subset
        of the record containing al persistent indentifiers
        """
        return dict((key, self[key]) for key in self.get('_persistent_identifiers_keys', reset_cache=True))

    def is_empty(self):
        """
        One record is empty if there is nothing stored inside rec_json or there is
        only '__key'
        """
        if self.rec_json is None or len(self.rec_json.keys()) == 0:
            return True
        if all(key.startswith('_') for key in self.keys()):
            return True
        return False

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
                if 'all' in checker_function[0] or self['__master_format'] in checker_function[0]:
                    try:
                        self._try_to_eval("%s(self,'%s',%s)" % (checker_function[1], key, checker_function[2]))
                    except InvenioBibFieldContinuableError, err:
                        self['__error_messages']['cerror'].append('Checking CError - ' + str(err))
                    except InvenioBibFieldError, err:
                        self['__error_messages']['error'].append('Checking Error - ' + str(err))

        if reset or '__error_messages.error' not in self or  '__error_messages.cerror' not in self:
            self.rec_json['__error_messages'] = {'error': [], 'cerror': []}

        for key in self.keys():
            try:
                check_rules(config_rules[key]['checker'], key)
            except TypeError:
                for kkey in config_rules[key]:
                    check_rules(config_rules[kkey]['checker'], kkey)
            except KeyError:
                continue

    @property
    def fatal_errors(self):
        """@return All the fatal/non-continuable errors that check_record has found"""
        return self.get('__error_messages.error', [])

    @property
    def continuable_errors(self):
        """@return All the continuable errors that check_record has found"""
        return self.get('__error_messages.cerror', [])

    def legacy_export_as_marc(self):
        """
        It creates a valid marcxml using the legacy rules defined in the config
        file
        """
        def encode_for_marcxml(value):
            from invenio.textutils import encode_for_xml
            if isinstance(value, unicode):
                value = value.encode('utf8')
            return encode_for_xml(str(value))

        export = '<record>'
        marc_dicts = self.produce_json_for_marc()
        for marc_dict in marc_dicts:
            content = ''
            tag = ''
            ind1 = ''
            ind2 = ''
            for key, value in marc_dict.iteritems():
                if isinstance(value, basestring) or not hasattr(value, '__iter__'):
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

    def get_legacy_recstruct(self):
        """
        It creates the recstruct representation using the legacy rules defined in
        the configuration file

        #CHECK: it might be a bit overkilling
        """
        from invenio.bibrecord import create_record
        return create_record(self.legacy_export_as_marc())[0]

    def _prepare_blob(self):
        """
        This method might be overwritten by the *Reader and should take care of
        transforming the blob into an homogeneous format that the _translate()
        method understands
        Overwriting this method is optional if there is no need of transforming
        the blob into something that _translate understands
        """
        #In this case no translation needed
        self.rec_tree = self.rec_json = self.blob_wrapper.blob

    def _translate(self):
        """
        Using the intermediate structure (self.rec_tree) that _prepare_blob has
        created it transforms the record into a jsonic structure using the rules
        present into the bibfield configuration file.
        To apply this rules it takes into account the type of the reader (which
        indeed means the type of source format) and the doctype.
        """

        if self.__class__.__name__ == 'JsonReader':
            #No translation needed for json
            pass
        else:
            #TODO: allow a list of doctypes and get the union of them
            # fields = doctype_definition[blob.doctype]['fields']
            # Now just getting all the possible field from config_rules
            fields = dict(zip(config_rules.keys(), config_rules.keys()))
            for json_id, field_name in fields.iteritems():
                self._unpack_rule(json_id, field_name)

    def _get_elements_from_rec_tree(self, regex_rules):
        for regex_rule in regex_rules:
            for element in self.rec_tree[re.compile(regex_rule)]:
                yield element

    def _unpack_rule(self, json_id, field_name=None):
        if not field_name:
            field_name = json_id

        rule_def = config_rules[json_id]

        if isinstance(rule_def, list):  # Undo the workaround for [0] and [n]
            return all([self._unpack_rule(json_id_rule) for json_id_rule in rule_def])
        if (json_id, field_name) in self.__parsed:
            return field_name in self

        self.__parsed.append((json_id, field_name))

        if rule_def['type'] == 'real':
            try:
                rules = rule_def['rules'][self['__master_format']]
            except KeyError:
                return False
            return all(self._apply_rule(field_name, rule_def['aliases'], rule) for rule in rules)
        else:
            return self._apply_virtual_rule(field_name, rule_def['aliases'], rule_def['rules'], rule_def['type'])

    def _apply_rule(self, field_name, aliases, rule):
        if 'entire_record' in rule['source_tag'] or any(key in self.rec_tree for key in rule['source_tag']):
            if rule['parse_first']:
                for json_id in self._try_to_eval(rule['parse_first']):
                    self._unpack_rule(json_id)
            if rule['depends_on'] and not all(k in self for k in self._try_to_eval(rule['depends_on'])):
                return False
            if rule['only_if'] and not all(self._try_to_eval(rule['only_if'])):
                return False
            if 'entire_record' in rule['source_tag']:
                self[field_name] = self._try_to_eval(rule['value'], value=self.rec_tree)
            else:
                for elements in self._get_elements_from_rec_tree(rule['source_tag']):
                    if isinstance(elements, list):
                        returned_value = False
                        for element in elements:
                            if rule['only_if_master_value'] and not all(self._try_to_eval(rule['only_if_master_value'], value=element)):
                                returned_value = returned_value or False
                            else:
                                try:
                                    self[field_name] = self._try_to_eval(rule['value'], value=element)
                                    returned_value = returned_value or True
                                except Exception, e:
                                    self['__error_messages.error[n]'] = 'Rule Error - Unable to apply rule for field %s - %s' % (field_name, str(e))
                                    returned_value = returned_value or False
                    else:
                        if rule['only_if_master_value'] and not all(self._try_to_eval(rule['only_if_master_value'], value=elements)):
                            return False
                        else:
                            try:
                                self[field_name] = self._try_to_eval(rule['value'], value=elements)
                            except Exception, e:
                                self['__error_messages.error[n]'] = 'Rule Error - Unable to apply rule for field %s - %s' % (field_name, str(e))
                                returned_value = returned_value or False

            for alias in aliases:
                self['__aliases'][alias] = field_name
            return True
        else:
            return False

    def _apply_virtual_rule(self, field_name, aliases, rule, rule_type):
        if rule['parse_first']:
            for json_id in self._try_to_eval(rule['parse_first']):
                self._unpack_rule(json_id)
        if rule['depends_on'] and not all(k in self for k in self._try_to_eval(rule['depends_on'])):
            return False
        if rule['only_if'] and not all(self._try_to_eval(rule['only_if'])):
            return False
        #Apply rule
        if rule_type == 'derived':
            try:
                self[field_name] = self._try_to_eval(rule['value'])
            except Exception, e:
                self['__error_messages.cerror[n]'] = 'Virtual Rule CError - Unable to evaluate %s - %s' % (field_name, str(e))
        else:
            self['__calculated_functions'][field_name] = rule['value']
            if rule['do_not_cache']:
                self['__do_not_cache'].append(field_name)
                self[field_name] = None
            else:
                try:
                    self[field_name] = self._try_to_eval(rule['value'])
                except Exception, e:
                    self['__error_messages.cerror[n]'] = 'Virtual Rule CError - Unable to evaluate %s - %s' % (field_name, str(e))

        for alias in aliases:
            self['__aliases'][alias] = field_name

        return True

    def _post_process_json(self):
        """
        If needed this method will post process the json structure, e.g. pruning
        the json to delete None values
        """
        pass


for key, value in PluginContainer(os.path.join(CFG_PYLIBDIR, 'invenio', 'bibfield_functions', 'produce_json_for_*.py')).iteritems():
    setattr(JsonReader, key, value)

## Compulsory plugin interface
readers = JsonReader
