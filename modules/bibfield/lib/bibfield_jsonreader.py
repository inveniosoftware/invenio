# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011 CERN.
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

import re

from invenio.bibfield_utils import BibFieldDict, BibFieldCheckerException
from invenio.bibfield_config import config_rules


class JsonReader(BibFieldDict):
    """
    Base class inside the hierarchy that contains several method implementations
    that will be shared, eventually, by all the *Reader classes.
    In this particular case this class is expecting that the base format is json,
    so no conversion is needed.
    """

    def __init__(self, blob_wrapper=None):
        """
        blob -> _prepare_blob(...) -> rec_tree -> _translate(...) -> json_dict -> check_record(...)
        """
        super(JsonReader, self).__init__()
        self.blob_wrapper = blob_wrapper
        self.rec_tree = None  # all record information represented as a tree (intermediate structure)
        self.rec_json = {}  # bibfield recjson structure

        self._missing_cfg = []
        self._warning_messages = []

        self.__parsed = []

        if self.blob_wrapper:
            try:
                self['__master_format'] = self.blob_wrapper.master_format
            except AttributeError:
                pass  # We are retrieving the cached version from the data base containing __master_format

            self._prepare_blob()
            self._translate()
            self._post_process_json()
            self.check_record()
        else:
            self['__master_format'] = 'json'

        self._init_fase = False

    @staticmethod
    def split_blob(blob):
        """
        In case of several records inside the blob this method specify how to split
        then and work one by one afterwards
        """
        raise NotImplementedError("This method must be implemented by each reader")

    def is_empty(self):
        """
        One record is empty if there is nothing stored inside rec_json or there is
        only '__master_format'
        """
        if not self.rec_json:
            return True
        if self.keys() == ['__master_format']:
            return True
        return False

    def check_record(self):
        """
        Using the checking rules defined inside bibfied configurations files checks
        if the record is well build. If not it stores the problems inside
        self._warning_messages
        """
        def check_rules(checker_functions, key):
            """docstring for check_rule"""
            for checker_function in checker_functions:
                if 'all' in checker_function[0] or self['__master_format'] in checker_function[0]:
                    try:
                        self._try_to_eval("%s(self,'%s',%s)" % (checker_function[1], key, checker_function[2]))
                    except BibFieldCheckerException, err:
                        self._warning_messages.append(err.message)
        for key in self.keys():
            try:
                check_rules(config_rules[key]['checker'], key)
            except TypeError:
                for kkey in config_rules[key]:
                    check_rules(config_rules[kkey]['checker'], kkey)
            except KeyError:
                continue

    def legacy_export_as_marc(self):
        """
        It creates a valid marcxml using the legacy rules defined in the config
        file
        """
        from cgi import escape

        formatstring_controlfield = "<controlfield tag='{tag}'>{content}</controlfield>"
        formatstring_datafield = "<datafield tag='{tag}' ind1='{ind1}' ind2='{ind2}'>{content}</datafield>"

        def create_marc_representation(key, value, legacy_rules):
            """
            Helper function to create the marc representation of one field

            #FIXME: refactor this spaghetti code
            """
            output = ''
            content = ''
            tag = ''
            ind1 = ''
            ind2 = ''

            if not value:
                return ''

            for legacy_rule in legacy_rules:
                if not '%' in legacy_rule[0]:
                    if len(legacy_rule[0]) == 3 and legacy_rule[0].startswith('00'):
                        # Control Field (No indicators no subfields)
                        formatstring = None
                        if legacy_rule[0] == '005':
                            #Especial format for date only for 005 tag
                            formatstring = "%Y%m%d%H%M%S.0"
                        output += formatstring_controlfield.format(tag=legacy_rule[0],
                                                                   content=self.get(key,
                                                                                    default='',
                                                                                    formatstring=formatstring,
                                                                                    formatfunction=escape)
                                                                   )
                    elif len(legacy_rule[0]) == 6:
                        #Data Field
                        if not (tag == legacy_rule[0][:3] and ind1 == legacy_rule[0][3].replace('_', '') and ind2 == legacy_rule[0][4].replace('_', '')):
                            tag = legacy_rule[0][:3]
                            ind1 = legacy_rule[0][3].replace('_', '')
                            ind2 = legacy_rule[0][4].replace('_', '')
                            if content:
                                output += formatstring_datafield.format(tag=tag,
                                                                        ind1=ind1,
                                                                        ind2=ind2,
                                                                        content=content)
                                content = ''
                        try:
                            tmp = value.get(legacy_rule[-1])
                            if tmp:
                                tmp = escape(tmp)
                            else:
                                continue
                        except AttributeError:
                            tmp = escape(value)
                        content += "<subfield code='%s'>%s</subfield>" % (legacy_rule[0][5], tmp)
            if content:
                output += formatstring_datafield.format(tag=tag,
                                                        ind1=ind1,
                                                        ind2=ind2,
                                                        content=content)
            return output

        export = '<collection xmlns="http://www.loc.gov/MARC21/slim"><record>'

        for key in [k for k in config_rules.iterkeys() if k in self]:
            values = self[key.replace('[n]', '[1:]')]
            if not isinstance(values, list):
                values = [values]
            for value in values:
                try:
                    export += create_marc_representation(key, value, sum([rule['legacy'] for rule in config_rules[key]['rules']['marc']], ()))
                except (TypeError, KeyError):
                    break

        export += "</record> </collection>"
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
        """docstring for _get_elements_from_rec_tree"""
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
            return self._apply_virtual_rule(field_name, rule_def['rules'], rule_def['type'])

    def _apply_rule(self, field_name, aliases, rule):
        """docstring for _apply_rule"""
        if 'entire_record' in rule['source_tag'] or any(key in self.rec_tree for key in rule['source_tag']):
            if rule['parse_first'] and not all(self._unpack_rule(json_id) for json_id in self._try_to_eval(rule['parse_first'])):
                return False
            if 'entire_record' in rule['source_tag']:
                self[field_name] = self._try_to_eval(rule['value'], value=self.rec_tree)
            else:
                for elements in self._get_elements_from_rec_tree(rule['source_tag']):
                    if isinstance(elements, list):
                        for element in elements:
                            self[field_name] = self._try_to_eval(rule['value'], value=element)
                    else:
                        self[field_name] = self._try_to_eval(rule['value'], value=elements)
            for alias in aliases:
                self._aliases[alias] = field_name
            return True
        else:
            return False

    def _apply_virtual_rule(self, field_name, rule, type):
        if rule['parse_first'] and not all(self._unpack_rule(json_id) for json_id in self._try_to_eval(rule['parse_first'])):
            return False
        if rule['parse_first'] and not all(k in self for k in self._try_to_eval(rule['depends_on'])):
            return False
        if rule['only_if'] and not all(self._try_to_eval(rule['only_if'])):
            return False
        #Apply rule
        if type == 'derived':
            self[field_name] = self._try_to_eval(rule['value'])
        else:
            self[field_name] = [self._try_to_eval(rule['value']), rule['value']]

        if rule['do_not_cache']:
            self._do_not_cache.append(field_name)

        return True

    def _post_process_json(self):
        """
        If needed this method will post process the json structure, e.g. pruning
        the json to delete None values
        """
        pass

## Compulsory plugin interface
readers = JsonReader
