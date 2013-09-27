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
    invenio.core.record.config_engine
    ---------------------------------

    Record fields and models configuration loader.

    This module uses `pyparsing <http://pyparsing.wikispaces.com/>` to read from the
    different configuration files the field and model definitions.
"""

import os
import re

from invenio.base.globals import cfg
from invenio.base.utils import autodiscover_non_python_files

from pyparsing import ParseException, FollowedBy, Suppress, OneOrMore, Literal, \
    LineEnd, ZeroOrMore, Optional, Forward, Word, QuotedString, alphas, nums, \
    alphanums, originalTextFor, oneOf, nestedExpr, quotedString, removeQuotes, \
    lineEnd, empty, col, restOfLine, delimitedList, indentedBlock

class FieldParserException(Exception):
    """Exception raised when some error happens parsing field definitions"""
    pass


class ModelParserException(Exception):
    """Exception raised when some error happens parsing model definitions"""
    pass


def _create_record_field_parser():
    """
    Creates a parser that can handle field definitions.

    BFN like grammar::

        line ::= python_doc_string | python_comment | include | field_def

        include ::= "include(" PATH ")"

        field_def ::= [persitent_identifier] [inherit_from] [override] json_id ["[0]" | "[n]"] "," aliases":" INDENT field_def_body UNDENT
        field_def_body ::= (creator | derived | calculated) [checker] [producer] [documentation]
        aliases ::= json_id ["[0]" | "[n]"] ["," aliases]
        json_id ::= (alphas + '_') (alphanums + '_')

        creator ::= "creator:" INDENT creator_body+ UNDENT
        creator_body ::= [decorators] source_format "," source_tags "," python_allowed_expr
        source_format ::= MASTER_FORMATS
        source_tag ::= QUOTED_STRING #This quoted string can contain a space separated list

        derived ::= "derived" INDENT derived_calculated_body UNDENT
        calculated ::= "calculated:" INDENT derived_calculated_body UNDENT
        derived_calculated_body ::= [decorators] "," python_allowed_exp

        decorators ::= (legacy | do_not_cache | parse_first | depends_on | only_if | only_if_master_value)*
        legacy ::= "@legacy(" correspondences+ ")"
        correspondences ::= "(" source_tag [ "," tag_name ] "," json_id ")"
        parse_first ::= "@parse_first(" json_id+ ")"
        depends_on ::= "@depends_on(" json_id+ ")"
        only_if ::= "@only_if(" python_condition+ ")"
        only_if_master_value ::= "@only_if_master_value(" python_condition+  ")"

        persistent_identifier ::= @persistent_identifier( level )
        inherit_from ::= "@inherit_from(" json_id+ ")"
        override ::= "@override"
        extend ::= "@extend"
        do_not_cache ::= "@do_not_cache"

        checker ::= "checker:" INDENT checker_function+ UNDENT

        documentation ::= INDENT doc_string UNDENT
        doc_string ::= QUOTED_STRING #reStructuredText string

        producer ::= "producer:" INDENT producer_body UNDENT
        producer_body ::= producer_code "," python_dictionary
        producer_code ::= ident

        python_allowed_exp ::= ident | list_def | dict_def | list_access | dict_access | function_call | one_line_expr
    """
    indent_stack = [1]

    def check_sub_indent(str, location, tokens):
        cur_col = col(location, str)
        if cur_col > indent_stack[-1]:
            indent_stack.append(cur_col)
        else:
            raise ParseException(str, location, "not a subentry")

    def check_unindent(str, location, tokens):
        if location >= len(str):
            return
        cur_col = col(location, str)
        if not(cur_col < indent_stack[-1] and cur_col <= indent_stack[-2]):
            raise ParseException(str, location, "not an unindent")

    def do_unindent():
        indent_stack.pop()

    INDENT = lineEnd.suppress() + empty + empty.copy().setParseAction(check_sub_indent)
    UNDENT = FollowedBy(empty).setParseAction(check_unindent)
    UNDENT.setParseAction(do_unindent)

    json_id = (Word(alphas + "_", alphanums + "_") + Optional(oneOf("[0] [n]")))\
              .setResultsName("json_id", listAllMatches=True)\
              .setParseAction(lambda tokens: "".join(tokens))
    aliases = delimitedList((Word(alphanums + "_") + Optional(oneOf("[0] [n]")))
                            .setParseAction(lambda tokens: "".join(tokens)))\
              .setResultsName("aliases")
    python_allowed_expr = Forward()
    ident = Word(alphas + "_", alphanums + "_")
    dict_def = originalTextFor(nestedExpr('{', '}'))
    list_def = originalTextFor(nestedExpr('[', ']'))
    dict_access = list_access = originalTextFor(ident + nestedExpr('[', ']'))
    function_call = originalTextFor(ZeroOrMore(ident + ".") + ident + nestedExpr('(', ')'))

    python_allowed_expr << (ident ^ dict_def ^ list_def ^ dict_access ^ list_access ^ function_call ^ restOfLine)\
                           .setResultsName("value", listAllMatches=True)

    persistent_identifier = (Suppress("@persistent_identifier") +  nestedExpr("(", ")"))\
                            .setResultsName("persistent_identifier")
    legacy = (Suppress("@legacy") + originalTextFor(nestedExpr("(", ")")))\
             .setResultsName("legacy", listAllMatches=True)
    only_if = (Suppress("@only_if") + originalTextFor(nestedExpr("(", ")")))\
              .setResultsName("only_if")
    only_if_master_value = (Suppress("@only_if_value") + originalTextFor(nestedExpr("(", ")")))\
                    .setResultsName("only_if_master_value")
    depends_on = (Suppress("@depends_on") + originalTextFor(nestedExpr("(", ")")))\
                 .setResultsName("depends_on")
    parse_first = (Suppress("@parse_first") + originalTextFor(nestedExpr("(", ")")))\
                  .setResultsName("parse_first")
    do_not_cache = (Suppress("@") + "do_not_cache")\
                   .setResultsName("do_not_cache")
    field_decorator = parse_first ^ depends_on ^ only_if ^ only_if_master_value ^ do_not_cache ^ legacy

    #Independent decorators
    inherit_from = (Suppress("@inherit_from") + originalTextFor(nestedExpr("(", ")")))\
                    .setResultsName("inherit_from")
    override = (Suppress("@") + "override")\
                   .setResultsName("override")
    extend = (Suppress("@") + "extend")\
                   .setResultsName("extend")

    master_format = (Suppress("@master_format") + originalTextFor(nestedExpr("(", ")")))\
                    .setResultsName("master_format")

    derived_calculated_body = ZeroOrMore(field_decorator) + python_allowed_expr

    derived = "derived" + Suppress(":") + INDENT + derived_calculated_body + UNDENT
    calculated = "calculated" + Suppress(":") + INDENT + derived_calculated_body + UNDENT

    source_tag = quotedString\
                 .setParseAction(removeQuotes)\
                 .setResultsName("source_tag", listAllMatches=True)
    source_format = oneOf(cfg['CFG_RECORD_MASTER_FORMATS'])\
                    .setResultsName("source_format", listAllMatches=True)
    creator_body = (ZeroOrMore(field_decorator) + source_format + Suppress(",") + source_tag + Suppress(",") + python_allowed_expr)\
                   .setResultsName("creator_def", listAllMatches=True)
    creator = "creator" + Suppress(":") + INDENT + OneOrMore(creator_body) + UNDENT

    checker_function = (Optional(master_format) + ZeroOrMore(ident + ".") + ident + originalTextFor(nestedExpr('(', ')')))\
                       .setResultsName("checker_function", listAllMatches=True)
    checker = "checker" + Suppress(":") + INDENT + OneOrMore(checker_function) + UNDENT

    doc_string = QuotedString(quoteChar='"""', multiline=True) | quotedString.setParseAction(removeQuotes)
    documentation = "documentation" + Suppress(":") + \
                     INDENT + Optional(doc_string).setResultsName("documentation") + UNDENT

    producer_code = Word(alphas + "_", alphanums + "_")\
                    .setResultsName("producer_code", listAllMatches=True)
    producer_body = (producer_code + Suppress(",") + python_allowed_expr)\
                    .setResultsName("producer_def", listAllMatches=True)
    producer = "producer"  + Suppress(":") + INDENT + OneOrMore(producer_body) + UNDENT

    field_def = (creator | derived | calculated)\
                .setResultsName("type_field", listAllMatches=True)

    body = Optional(field_def) + Optional(checker) + Optional(producer) + Optional(documentation)
    comment = Literal("#") + restOfLine + LineEnd()
    include = (Suppress("include") + quotedString)\
              .setResultsName("includes", listAllMatches=True)
    rule = (Optional(persistent_identifier) + Optional(inherit_from) + Optional(override) + json_id + Optional(Suppress(",") + aliases) + Suppress(":") + INDENT + body + UNDENT)\
           .setResultsName("rules", listAllMatches=True)

    return OneOrMore(rule | include | comment.suppress())


def _create_record_model_parser():
    """
    Creates a parser that can handle model definitions.

    BFN like grammar::

        record_model ::= python_doc_string | python_comment | fields [documentation] [checker]
        fields ::= "fields:" INDENT [inherit_from] [list_of_fields]
        inherit_from ::= "@inherit_from(" json_id+  ")"
        list_of_fields ::= json_id [ "=" json_id ]

        documentation ::= INDENT QUOTED_STRING  UNDENT

        checker ::= "checker:" INDENT checker_function+ UNDENT

    Note: Unlike the field configuration files where you can specify more than
    one field inside each file for the record models only one definition is 
    allowed by file.
    """
    indentStack = [1]

    field_def = (Word(alphas + "_", alphanums + "_") + \
                 Optional(Suppress("=") + \
                 Word(alphas + "_", alphanums + "_")))\
                .setResultsName("field_definition")
    inherit_from = (Suppress("@inherit_from") + \
                    originalTextFor(nestedExpr("(", ")")))\
                   .setResultsName("inherit_from")

    fields = (Suppress("fields:") + \
              indentedBlock(inherit_from | field_def, indentStack))\
             .setResultsName("fields")

    ident = Word(alphas + "_", alphanums + "_")
    checker_function = (ZeroOrMore(ident + ".") +\
                        ident + \
                        originalTextFor(nestedExpr('(', ')')))\
                       .setResultsName("checker_function", listAllMatches=True)
    checker = (Suppress("checker:") + \
               indentedBlock(OneOrMore(checker_function), indentStack))\
              .setResultsName("checker")

    doc_string = QuotedString(quoteChar='"""', multiline=True) | \
                 quotedString.setParseAction(removeQuotes)
    documentation = (Suppress("documentation:") + \
                     indentedBlock(doc_string, indentStack))\
                    .setResultsName("documentation")
    comment = Literal("#") + restOfLine + LineEnd()

    return OneOrMore(comment | fields + Optional(documentation) + Optional(checker))


class FieldParser(object):
    """Field definitions parser"""
    def __init__(self):
        #Autodiscover .cfg files
        self.files = autodiscover_non_python_files('.*\.cfg',
                'recordext.fields')
        self.field_definitions = {}
        self.legacy_field_matchings = {}
        self.__inherit_rules = []
        self.__unresolved_inheritence = []
        self.__override_rules = []
        self.__extend_rules = []

    def create(self):
        """
        Fills up field_definitions and legacy_field_matchings dictionary with
        the rules defined inside the configuration files.

        It also resolve the includes present inside the configuration files and
        recursively the ones in the other files.
        """
        parser = _create_record_field_parser()
        already_included = [os.path.basename(f) for f in self.files]
        for field_file in self.files:
            field_descs = parser.parseFile(field_file, parseAll=True)
            for include in field_descs.includes:
                if include[0] in already_included:
                    continue
                if not os.path.exists(include[0]):
                    raise FieldParserException("Can't find file: %s" % (include[0], ))
                self.files.append(include[0])
            for rule in field_descs.rules:
                if rule.override:
                    self.__override_rules.append(rule)
                elif rule.extend:
                    self.__extend_rules.append(rule)
                elif rule.type_field[0] == 'creator':
                    self._create_creator_rule(rule)
                elif rule.type_field[0] == "derived" or rule.type_field[0] == "calculated":
                    self._create_derived_calculated_rule(rule)
                elif rule.inherit_from:
                    self.__inherit_rules.append(rule)
                else:
                    assert False, 'Type creator, derived or calculated, or inherit field or overwrite field expected'

        self.__resolve_inherit_rules()
        self.__resolve_override_rules()
        self.__resolve_extend_rules()

        return (self.field_definitions, self.legacy_field_matchings)

    def _create_creator_rule(self, rule, override=False, extend=False):
        """
        Creates the config_rule entries for the creator rules.
        The result looks like this::

            {'json_id':{'rules': { 'inherit_from'        : (inherit_from_list),
                                   'source_format'       : [translation_rules],
                                   'parse_first'         : (parse_first_json_ids),
                                   'depends_on'          : (depends_on_json_id),
                                   'only_if'             : (only_if_boolean_expressions),
                                   'only_if_master_value': (only_if_master_value_boolean_expressions),
                                 },
                        'checker': [(function_name, arguments), ...]
                        'documentation' : {'doc_string': '...',
                                           'subfields' : .....},
                        'type' : 'real'
                        'aliases' : [list_of_aliases_ids]
                       },
                     ....
            }
        """
        json_id = rule.json_id[0]
        #Chech duplicate names
        if json_id in self.field_definitions and not override and not extend:
            raise FieldParserException("Name error: '%s' field name already defined"
                                    % (rule.json_id[0],))
        if not json_id in self.field_definitions and (override or extend):
            raise FieldParserException("Name error: '%s' field name not defined"
                                    % (rule.json_id[0],))

        #Workaround to keep clean doctype files
        #Just creates a dict entry with the main json field name and points it to
        #the full one i.e.: 'authors' : ['authors[0]', 'authors[n]']
        if '[0]' in json_id or '[n]' in json_id:
            main_json_id = re.sub('(\[n\]|\[0\])', '', json_id)
            if not main_json_id in self.field_definitions:
                self.field_definitions[main_json_id] = []
            self.field_definitions[main_json_id].append(json_id)

        aliases = []
        if rule.aliases:
            aliases = rule.aliases.asList()

        persistent_id = None
        if rule.persistent_identifier:
            persistent_id = int(rule.persistent_identifier[0][0])

        inherit_from = None
        if rule.inherit_from:
            self.__unresolved_inheritence.append(json_id)
            inherit_from = eval(rule.inherit_from[0])

        rules = {}
        for creator in rule.creator_def:

            source_format = creator.source_format[0]

            if source_format not in rules:
                #Allow several tags point to the same json id
                rules[source_format] = []

            (depends_on, only_if, only_if_master_value, parse_first) = self.__create_decorators_content(creator)
            self._create_legacy_rules(creator.legacy, json_id, source_format)

            rules[source_format].append({'source_tag'           : creator.source_tag[0].split(),
                                         'value'                : creator.value[0],
                                         'depends_on'           : depends_on,
                                         'only_if'              : only_if,
                                         'only_if_master_value' : only_if_master_value,
                                         'parse_first'          : parse_first})
        if not override and not extend:
            self.field_definitions[json_id] = {'inherit_from'  : inherit_from,
                                          'rules'         : rules,
                                          'checker'       : [],
                                          'documentation' : '',
                                          'producer'        : {},
                                          'type'          : 'real',
                                          'aliases'       : aliases,
                                          'persistent_identifier': persistent_id,
                                          'overwrite'     : False}
        elif override:
            self.field_definitions[json_id]['overwrite'] = True
            self.field_definitions[json_id]['rules'].update(rules)
            self.field_definitions[json_id]['aliases'] = \
                    aliases or self.field_definitions[json_id]['aliases']
            self.field_definitions[json_id]['persistent_identifier'] = \
                    persistent_id or self.field_definitions[json_id]['persistent_identifier']
            self.field_definitions[json_id]['inherit_from'] = \
                    inherit_from or self.field_definitions[json_id]['inherit_from']
        elif extend:
            pass

        self._create_checkers(rule)
        self._create_documentation(rule)
        self._create_producer(rule)

    def _create_derived_calculated_rule(self, rule, override=False):
        """
        Creates the field_definitions entries for the virtual fields
        The result is similar to the one of real fields but in this case there is
        only one rule.
        """
        json_id = rule.json_id[0]
        #Chech duplicate names
        if json_id in self.field_definitions and not override:
            raise FieldParserException("Name error: '%s' field name already defined"
                                    % (rule.json_id[0],))
        if not json_id in self.field_definitions and override:
            raise FieldParserException("Name error: '%s' field name not defined"
                                    % (rule.json_id[0],))

        aliases = []
        if rule.aliases:
            aliases = rule.aliases.asList()
        if re.search('^_[a-zA-Z0-9]', json_id):
            aliases.append(json_id[1:])

        do_not_cache = False
        if rule.do_not_cache:
            do_not_cache = True

        persistent_id = None
        if rule.persistent_identifier:
            persistent_id = int(rule.persistent_identifier[0][0])

        (depends_on, only_if, only_if_master_value, parse_first) = self.__create_decorators_content(rule)
        self._create_legacy_rules(rule.legacy, json_id)

        self.field_definitions[json_id] = {'rules'        : {},
                                      'checker'      : [],
                                      'documentation': '',
                                      'producer'       : {},
                                      'aliases'      : aliases,
                                      'type'         : rule.type_field[0],
                                      'persistent_identifier' : persistent_id,
                                      'overwrite'    : False}

        self.field_definitions[json_id]['rules'] = {'value'               : rule.value[0],
                                               'depends_on'          : depends_on,
                                               'only_if'             : only_if,
                                               'only_if_master_value': only_if_master_value,
                                               'parse_first'         : parse_first,
                                               'do_not_cache'        : do_not_cache}

        self._create_checkers(rule)
        self._create_documentation(rule)
        self._create_producer(rule)

    def _create_legacy_rules(self, legacy_rules, json_id, source_format=None):
        """
        Creates the legacy rules dictionary::

            {'100'   : ['authors[0]'],
             '100__' : ['authors[0]'],
             '100__%': ['authors[0]'],
             '100__a': ['auhtors[0].full_name'],
             .......
            }
        """
        if not legacy_rules:
            return
        for legacy_rule in legacy_rules:
            legacy_rule = eval(legacy_rule[0])

            if source_format is None:
                inner_source_format = legacy_rule[0]
                legacy_rule = legacy_rule[1]
            else:
                inner_source_format = source_format

            if not inner_source_format in self.legacy_field_matchings:
                self.legacy_field_matchings[inner_source_format] = {}

            for field_legacy_rule in legacy_rule:
                #Allow string and tuple in the config file
                legacy_fields = isinstance(field_legacy_rule[0], basestring) and (field_legacy_rule[0], ) or field_legacy_rule[0]
                json_field = json_id
                if field_legacy_rule[-1]:
                    json_field = '.'.join((json_field, field_legacy_rule[-1]))
                for legacy_field in legacy_fields:
                    if not legacy_field in self.legacy_field_matchings[inner_source_format]:
                        self.legacy_field_matchings[inner_source_format][legacy_field] = []
                    self.legacy_field_matchings[inner_source_format][legacy_field].append(json_field)


    def _create_checkers(self, rule):
        """
        Creates the list of checker functions and arguments for the given rule
        """
        json_id = rule.json_id[0]
        assert json_id in self.field_definitions

        if rule.checker_function:
            if self.field_definitions[json_id]['overwrite']:
                self.field_definitions[json_id]['checker'] = []
            for checker in rule.checker_function:
                if checker.master_format:
                    master_format = eval(rule.master_format[0])
                    checker_function_name = checker[1]
                    arguments = checker[2][1:-1]
                else:
                    master_format = ('all',)
                    checker_function_name = checker[0]
                    arguments = checker[1][1:-1]

                #json_id : (master_format, checker_name, parameters)
                self.field_definitions[json_id]['checker'].append((master_format,
                                                              checker_function_name,
                                                              arguments))


    def _create_documentation(self, rule):
        """
        Creates the documentation dictionary for the given rule
        """
        json_id = rule.json_id[0]
        assert json_id in self.field_definitions

        if rule.documentation:
            self.field_definitions[json_id]['documentation'] = rule.documentation
    def _create_producer(self, rule):
        """
        Creates the dictionary of possible producer formats for the given rule
        """
        json_id = rule.json_id[0]
        assert json_id in self.field_definitions

        if rule.producer_def:
            if self.field_definitions[json_id]['overwrite']:
                self.field_definitions[json_id]['producer'] = {}
            for producer in rule.producer_def:
                producer_code = producer.producer_code[0]
                rule = producer.value[0]
                if not producer_code in self.field_definitions[json_id]['producer']:
                    self.field_definitions[json_id]['producer'][producer_code] = []
                self.field_definitions[json_id]['producer'][producer_code].append(eval(rule))

    def __create_decorators_content(self, rule):
        """
        Extracts from the rule all the possible decorators.
        """
        depends_on = only_if = only_if_master_value = parse_first = None

        if rule.depends_on:
            depends_on = rule.depends_on[0]
        if rule.only_if:
            only_if = rule.only_if[0]
        if rule.only_if_master_value:
            only_if_master_value = rule.only_if_master_value[0]
        if rule.parse_first:
            parse_first = rule.parse_first[0]

        return (depends_on, only_if, only_if_master_value, parse_first)

    def __resolve_inherit_rules(self):
        """
        Iterates over all the 'inherit' fields after all the normal field
        creation to avoid problem when creating this rules.
        """
        def resolve_inheritance(json_id):
            rule = self.field_definitions[json_id]
            inherit_from_list = self.field_definitions[json_id]['inherit_from']
            for inherit_json_id in inherit_from_list:
                #Check if everithing is fine
                if inherit_json_id == json_id:
                    raise FieldParserException("Inheritance from itself")
                if inherit_json_id not in self.field_definitions:
                    raise FieldParserException("Unable to solve %s inheritance" % (inherit_json_id,))
                if inherit_json_id in self._unresolved_inheritence:
                    self._resolve_inheritance(inherit_json_id)
                    self._unresolved_inheritence.remove(inherit_json_id)
                inherit_rule = self.field_definitions[inherit_json_id]
                for format in inherit_rule['rules']:
                    if not format in rule['rules']:
                        rule['rules'][format] = []
                    rule['rules'][format].extend(inherit_rule['rules'][format])
                rule['checker'].extend(inherit_rule['checker'])

        for rule in self.__inherit_rules:
            if rule.type_field[0] == 'creator':
                self._create_creator_rule(rule)
            elif rule.type_field[0] == "derived" or rule.type_field[0] == "calculated":
                self._create_derived_calculated_rule(rule)

        #Resolve inheritance
        for i in xrange(len(self.__unresolved_inheritence) - 1, -1, -1):
            resolve_inheritance(self.__unresolved_inheritence[i])
            del self.__unresolved_inheritence[i]


    def __resolve_override_rules(self):
        """
        Iterates over all the 'override' field to override the already created
        fields.
        """
        for rule in self.__override_rules:
            if rule.type_field[0] == 'creator':
                self._create_creator_rule(rule, override=True)
            elif rule.type_field[0] == "derived" or rule.type_field[0] == "calculated":
                self._create_derived_calculated_rule(rule, override=True)

    def __resolve_extend_rules(self):
        """
        Iterates over all the 'extend' field to extend the rule definition of this
        field.
        """
        for rule in self.__extend_rules:
            if rule.type_field[0] == 'creator':
                self._create_creator_rule(rule, extend=True)
            elif rule.type_field[0] == "derived" or rule.type_field[0] == "calculated":
                self._create_derived_calculated_rule(rule, extend=True)



class ModelParser(object):
    """Record model parser"""
    def __init__(self):
        #Autodiscover .cfg files
        self.files = autodiscover_non_python_files('.*\.cfg',
                'recordext.models')
        self.model_definitions = {}

    def create(self):
        """
        Fills up model_definitions dictionary with what is written inside the
        *.cfg present in the base directory / models

        It also resolve inheritance at creation time and name matching for the
        field names present inside the model file

        The result looks like this::

            {'model': {'fields': {json_id1: 'name_for_fieldfield1',
                                  json_id2: 'name_for_field2',
                                            ....
                                    'name_for_fieldN': fieldN },
                       'inherit_from: [(inherit_from_list), ...]
                       'documentation': 'doc_string',
                       'checker': [(functiona_name, arguments), ...]
                       },
             ...


        :raises: ModelParserException in case of missing model definition
                 (helpful if we use inheritance) or in case of unknown field name.
        """
        from .definitions import field_definitions
        parser = _create_record_model_parser()
        for model_file in self.files:
            model_name = os.path.basename(model_file).split('.')[0]
            if model_name in self.model_definitions:
                raise ModelParserException("Already defined record model: %s" % (model_name,))
            self.model_definitions[model_name] = {'fields': {},
                                                  'super': [],
                                                  'documentation': '',
                                                  'checker': []
                                                 }
            model_definition = parser.parseFile(model_file, parseAll=True)
            if model_definition.documentation:
                self.model_definitions[model_name]['documentation'] = model_definition.documentation[0][0][0]
            if model_definition.checker:
                for checker in model_definition.checker[0][0].checker_function:
                    self.model_definitions[model_name]['checker'].append((checker[0], checker[1][1:-1]))
            if not model_definition.fields:
                raise ModelParserException("Field definition needed")
            for field_def in model_definition.fields[0]:
                if field_def.inherit_from:
                    self.model_definitions[model_name]['super'].extend(eval(field_def[0]))
                else:
                    if len(field_def) == 1:
                        json_id = field_def[0]
                    else:
                        json_id = field_def[1]
                    if not json_id in field_definitions:
                        raise ModelParserException("Unknown field name: %s" % (json_id,))

                    self.model_definitions[model_name]['fields'][json_id] = field_def[0]

        for model, model_definition in self.model_definitions.iteritems():
            model_definition['fields'] = self.__resolve_inheritance(model)

        return self.model_definitions


    def __resolve_inheritance(self, model):
        """
        Resolves the inheritance

        :param model: name of the super model
        :type model: string

        :return: List of new fields to be added to the son model
        :raises: ModelParserException if the super model does not exist.
        """
        try:
            model_definition = self.model_definitions[model]
        except KeyError:
            raise ModelParserException("Missing model definition for %s" % (model,))
        fields = {}
        for super_model in model_definition['super']:
            fields.update(resolve_inheritance(super_model))
        fields.update(model_definition['fields'])
        return fields
