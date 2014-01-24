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
BibField configuration loader

This module uses pyparsing to read from the configuration file all the rules.

http://pyparsing.wikispaces.com/

"""

import os
import re
import six

from pyparsing import ParseException, FollowedBy, Suppress, OneOrMore, Word, \
    LineEnd, ZeroOrMore, Optional, Literal, alphas, alphanums, \
    originalTextFor, oneOf, nestedExpr, quotedString, removeQuotes, lineEnd, \
    empty, col, restOfLine, delimitedList, Each, indentedBlock, QuotedString

from invenio.config import CFG_ETCDIR
from invenio.importutils import try_to_eval


def _create_field_parser():
    """
    Creates a parser using pyparsing that works with bibfield rule definitions

    BNF like grammar:

    rule ::= ([persitent_identifier] json_id ["[0]" | "[n]"] "," aliases":" INDENT body UNDENT) | include | python_comment
    include ::= "include(" PATH ")"
    body ::=  [inherit_from] (creator | derived | calculated) [checker] [documentation] [producer]
    aliases ::= json_id ["[0]" | "[n]"] ["," aliases]

    creator ::= "creator:" INDENT creator_body+ UNDENT
    creator_body ::= [decorators] source_format "," source_tag "," python_allowed_expr
    source_format ::= MASTER_FORMATS
    source_tag ::= QUOTED_STRING

    derived ::= "derived" INDENT derived_calculated_body UNDENT
    calculated ::= "calculated:" INDENT derived_calculated_body UNDENT
    derived_calculated_body ::= [decorators] "," python_allowed_exp

    decorators ::= (peristent_identfier | legacy | do_not_cache | parse_first | depends_on | only_if | only_if_master_value)*
    peristent_identfier ::= @persitent_identifier( level )
    legacy ::= "@legacy(" correspondences+ ")"
    correspondences ::= "(" source_tag [ "," tag_name ] "," json_id ")"
    parse_first ::= "@parse_first(" jsonid+ ")"
    depends_on ::= "@depends_on(" json_id+ ")"
    only_if ::= "@only_if(" python_condition+ ")"
    only_if_master_value ::= "@only_if_master_value(" python_condition+  ")"

    inherit_from ::= "@inherit_from()"

    python_allowed_exp ::= ident | list_def | dict_def | list_access | dict_access | function_call

    checker ::= "checker:" INDENT checker_function+ UNDENT

    documentation ::= INDENT doc_string subfield* UNDENT
    doc_string ::= QUOTED_STRING
    subfield ::= "@subfield" json_id["."json_id*] ":" docstring

    producer ::= "producer:" INDENT producer_body UNDENT
    producer_body ::= producer_code "," python_dictionary
    producer_code ::= ident
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
    ident = Word(alphas + "_", alphanums + "_")
    dict_def = originalTextFor(nestedExpr('{', '}'))
    list_def = originalTextFor(nestedExpr('[', ']'))
    dict_access = list_access = originalTextFor(ident + nestedExpr('[', ']'))
    function_call = originalTextFor(ZeroOrMore(ident + ".") + ident + nestedExpr('(', ')'))

    python_allowed_expr = (dict_def ^ list_def ^ dict_access ^ \
            list_access ^ function_call ^ restOfLine)\
            .setResultsName("value", listAllMatches=True)

    persistent_identifier = (Suppress("@persistent_identifier") + \
            nestedExpr("(", ")"))\
            .setResultsName("persistent_identifier")
    legacy = (Suppress("@legacy") + originalTextFor(nestedExpr("(", ")")))\
            .setResultsName("legacy", listAllMatches=True)
    only_if = (Suppress("@only_if") + originalTextFor(nestedExpr("(", ")")))\
            .setResultsName("only_if")
    only_if_master_value = (Suppress("@only_if_value") + \
            originalTextFor(nestedExpr("(", ")")))\
            .setResultsName("only_if_master_value")
    depends_on = (Suppress("@depends_on") + \
            originalTextFor(nestedExpr("(", ")")))\
            .setResultsName("depends_on")
    parse_first = (Suppress("@parse_first") + \
            originalTextFor(nestedExpr("(", ")")))\
            .setResultsName("parse_first")
    memoize = (Suppress("@memoize") + nestedExpr("(", ")"))\
            .setResultsName("memoize")
    field_decorator = parse_first ^ depends_on ^ only_if ^ \
            only_if_master_value ^ memoize ^ legacy

    #Independent decorators
    inherit_from = (Suppress("@inherit_from") + \
            originalTextFor(nestedExpr("(", ")")))\
            .setResultsName("inherit_from")
    override = (Suppress("@") + "override")\
            .setResultsName("override")
    extend = (Suppress("@") + "extend")\
            .setResultsName("extend")
    master_format = (Suppress("@master_format") + \
            originalTextFor(nestedExpr("(", ")")))\
            .setResultsName("master_format") \
            .setParseAction(lambda toks: toks[0])

    derived_calculated_body = (ZeroOrMore(field_decorator) + python_allowed_expr)\
            .setResultsName('derived_calculated_def')

    derived = "derived" + Suppress(":") + \
            INDENT + derived_calculated_body + UNDENT
    calculated = "calculated" + Suppress(":") + \
            INDENT + derived_calculated_body + UNDENT

    source_tag = quotedString\
            .setParseAction(removeQuotes)\
            .setResultsName("source_tag", listAllMatches=True)
    source_format = Word(alphas, alphanums + "_")\
                    .setResultsName("source_format", listAllMatches=True)
    creator_body = (ZeroOrMore(field_decorator) + source_format + \
            Suppress(",") + source_tag + Suppress(",") + python_allowed_expr)\
            .setResultsName("creator_def", listAllMatches=True)
    creator = "creator" + Suppress(":") + \
            INDENT + OneOrMore(creator_body) + UNDENT
    field_def = (creator | derived | calculated)\
                .setResultsName("type_field", listAllMatches=True)

    #JsonExtra
    json_dumps = (Suppress('dumps') + Suppress(',') + python_allowed_expr)\
        .setResultsName("dumps")\
        .setParseAction(lambda toks: toks.value[0])
    json_loads = (Suppress("loads") + Suppress(",") + python_allowed_expr)\
        .setResultsName("loads")\
        .setParseAction(lambda toks: toks.value[0])

    json_extra = (Suppress('json:') + \
            INDENT + Each((json_dumps, json_loads)) + UNDENT)\
            .setResultsName('json_ext')

    #Checker
    checker_function = (Optional(master_format) + ZeroOrMore(ident + ".") + ident + originalTextFor(nestedExpr('(', ')')))\
                       .setResultsName("checker", listAllMatches=True)
    checker = ("checker" + Suppress(":") + INDENT + OneOrMore(checker_function) + UNDENT)

    #Description/Documentation
    doc_double = QuotedString(quoteChar='"""', multiline=True)
    doc_single = QuotedString(quoteChar="'''", multiline=True)
    doc_string = INDENT + (doc_double | doc_single) + UNDENT
    description_body = (Suppress('description:') + doc_string).\
                setParseAction(lambda toks: toks[0][0])
    description = (description_body | doc_double | doc_single)\
            .setResultsName('description')

    #Producer
    producer_code = (Word(alphas, alphanums + "_")\
           + originalTextFor(nestedExpr("(", ")")))\
           .setResultsName('producer_code', listAllMatches=True)
    producer_body = (producer_code + Suppress(",") + python_allowed_expr)\
                    .setResultsName("producer_rule", listAllMatches=True)
    producer = Suppress("producer:") + INDENT + OneOrMore(producer_body) + UNDENT

    schema = (Suppress('schema:') + INDENT + dict_def + UNDENT)\
            .setParseAction(lambda toks: toks[0])\
            .setResultsName('schema')

    body = Optional(field_def) & Optional(checker) & Optional(json_extra) \
            & Optional(description) & Optional(producer) & Optional(schema)
    comment = Literal("#") + restOfLine + LineEnd()
    include = (Suppress("include") + quotedString)\
              .setResultsName("includes", listAllMatches=True)
    rule = (Optional(persistent_identifier) + Optional(inherit_from) + \
            Optional(override) + Optional(extend) +json_id + \
            Optional(Suppress(",") + aliases) + Suppress(":") + \
            INDENT + body + UNDENT)\
           .setResultsName("rules", listAllMatches=True)

    return OneOrMore(rule | include | comment.suppress())


class BibFieldParserException(Exception):
    """
     Exception raised when some error happens when parsing doctype and rule
     documents
    """
    pass


class BibFieldParser(object):
    """
    BibField rule parser
    """

    _field_definitions = {}
    """Dictionary containing all the rules needed to create and validate json fields"""

    _legacy_field_matchings = {}
    """Dictionary containing matching between the legacy master format and the current json"""

    def __init__(self,
                 base_dir=CFG_ETCDIR + '/bibfield',
                 main_config_file='bibfield.cfg'):
        """
        Creates the parsers for the rules and parses all the
        documents inside base_dir


        @param base_dir: Full path where the configuration files are placed
        @param main_config_file: Name of the main file that contains the rules
        to perform the translation
        """
        self.base_dir = base_dir
        self.main_config_file = main_config_file

        self.__inherit_rules = []
        self.__unresolved_inheritence = []
        self.__override_rules = []
        self.__extend_rules = []

    @classmethod
    def field_definitions(cls):
        if not cls._field_definitions:
            cls.reparse()
        return cls._field_definitions

    @classmethod
    def legacy_field_matchings(cls):
        if  not cls._legacy_field_matchings:
            cls.reparse()
        return cls._legacy_field_matchings

    @classmethod
    def reparse(cls):
        cls._field_definitions = {}
        cls._legacy_field_matchings = {}
        cls()._create()

    def _create(self):
        """
        Fills up config_rules dictionary with the rules defined inside the
        configuration file.

        It also resolve the includes present inside the main configuration file
        and recursively the ones in the other files.

        It uses @see: _create_creator_rule() and @see: _create_derived_calculated_rule()
        to fill up config_rules
        """
        parser = _create_field_parser()
        main_rules = parser \
                     .parseFile(self.base_dir + '/' + self.main_config_file,
                                parseAll=True)
        rules = main_rules.rules
        includes = main_rules.includes
        already_includes = [self.main_config_file]

        #Resolve includes
        for include in includes:
            if include[0] in already_includes:
                continue
            already_includes.append(include[0])
            if os.path.exists(include[0]):
                tmp = parser.parseFile(include[0], parseAll=True)
            else:
                #CHECK: This will raise an IOError if the file doesn't exist
                tmp = parser.parseFile(self.base_dir + '/' + include[0],
                                       parseAll=True)
            if rules and tmp.rules:
                rules += tmp.rules
            else:
                rules = tmp.rules
            if includes and tmp.includes:
                includes += tmp.includes
            else:
                includes = tmp.includes

        #Create config rules
        for rule in rules:
            if rule.override:
                self.__override_rules.append(rule)
            elif rule.extend:
                self.__extend_rules.append(rule)
            elif rule.inherit_from:
                self.__inherit_rules.append(rule)
            else:
                self._create_rule(rule)

        self.__resolve_inherit_rules()
        self.__resolve_override_rules()
        self.__resolve_extend_rules()

    def _create_rule(self, rule, override=False, extend=False):
        """
        Creates the field and legacy definitions.
        The result looks like this::

            {key: [key1, key2],
             key1: {inherit_from: [],
                    override: True/False,
                    extend: True/False,
                    aliases: [],
                    persistent_identifier: num/None,
                    rules: {'master_format_1': [{rule1}, {rule2}, ...],
                            'master_format_2': [....],
                             ......
                            'calculated': [....],
                            'derived': [...]}
                   }
            }

        Each of the rule (rule1, rule2, etc.) has the same content::

            {'source_format'       : [translation_rules]/None,
             'parse_first'         : (parse_first_json_ids),
             'depends_on'          : (depends_on_json_id),
             'only_if'             : (only_if_boolean_expressions),
             'only_if_master_value': (only_if_master_value_boolean_expressions),
             'memoize'             : time,
             'value'               : value coming from master format
            }

        """
        json_id = rule.json_id[0]
        #Chech duplicate names
        if json_id in self.__class__._field_definitions and not override and not extend:
            raise BibFieldParserException("Name error: '%s' field name already defined"
                                    % (rule.json_id[0],))
        if not json_id in self.__class__._field_definitions and (override or extend):
            raise BibFieldParserException("Name error: '%s' field name not defined"
                                    % (rule.json_id[0],))

        #Workaround to keep clean doctype files
        #Just creates a dict entry with the main json field name and points it to
        #the full one i.e.: 'authors' : ['authors[0]', 'authors[n]']
        if '[0]' in json_id or '[n]' in json_id:
            main_json_id = re.sub('(\[n\]|\[0\])', '', json_id)
            if not main_json_id in self.__class__._field_definitions:
                self.__class__._field_definitions[main_json_id] = []
            self.__class__._field_definitions[main_json_id].append(json_id)

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

        if extend:
            rules = self.__class__._field_definitions[json_id]['rules']
        else:
            rules = {}

        #TODO: check if pyparsing can handle this!
        all_type_def = []
        if rule.creator_def:
            all_type_def = [r for r in rule.creator_def]
        if all_type_def and rule.derived_calculated_def:
            all_type_def.append(rule.derived_calculated_def)
        elif rule.derived_calculated_def:
            all_type_def = [rule.derived_calculated_def]

        for r in all_type_def:
            if r.source_format:
                source = r.source_format[0]
                source_tag = r.source_tag[0].split()
            else:
                source = rule.type_field[0]
                source_tag = None

            if source not in rules:
                #Allow several tags point to the same json id
                rules[source] = []
            (depends_on, only_if, only_if_master_value,
             parse_first, memoize) = self.__create_decorators_content(r)
            self._create_legacy_rules(r.legacy, json_id, source)

            rules[source].append({'source_tag'          : source_tag,
                                  'parse_first'         : parse_first,
                                  'depends_on'          : depends_on,
                                  'only_if'             : only_if,
                                  'only_if_master_value': only_if_master_value,
                                  'memoize'             : memoize,
                                  'value'               : compile(r.value[0].strip(), '', 'eval'),
                                 })

        if override:
            self.__class__._field_definitions[json_id]['override'] = override
            self.__class__._field_definitions[json_id]['rules'].update(rules)
            self.__class__._field_definitions[json_id]['aliases'] = \
                    aliases or self.__class__._field_definitions[json_id]['aliases']
            self.__class__._field_definitions[json_id]['persistent_identifier'] = \
                    persistent_id or self.__class__._field_definitions[json_id]['persistent_identifier']
            self.__class__._field_definitions[json_id]['inherit_from'] = \
                    inherit_from or self.__class__._field_definitions[json_id]['inherit_from']
        elif extend:
            self.__class__._field_definitions[json_id]['extend'] = extend
            self.__class__._field_definitions[json_id]['aliases'].extend(aliases)
        else:
            self.__class__._field_definitions[json_id] = {'inherit_from'  : inherit_from,
                                               'rules'         : rules,
                                               'aliases'       : aliases,
                                               'persistent_identifier': persistent_id,
                                               'override'     : override,
                                               'extend'       : extend,
                                              }

        self.__create_checker(rule)
        self.__create_description(rule)
        self.__create_producer(rule)
        self.__create_schema(rule)
        self.__create_json_extra(rule)

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

            if source_format in ('derived', 'calculated'):
                inner_source_format = legacy_rule[0]
                legacy_rule = legacy_rule[1:]
            else:
                inner_source_format = source_format

            if not inner_source_format in self.__class__._legacy_field_matchings:
                self.__class__._legacy_field_matchings[inner_source_format] = {}

            for field_legacy_rule in legacy_rule:
                #Allow string and tuple in the config file
                legacy_fields = isinstance(field_legacy_rule[0], basestring) and (field_legacy_rule[0], ) or field_legacy_rule[0]
                json_field = json_id
                if field_legacy_rule[-1]:
                    json_field = '.'.join((json_field, field_legacy_rule[-1]))
                for legacy_field in legacy_fields:
                    if not legacy_field in self.__class__._legacy_field_matchings[inner_source_format]:
                        self.__class__._legacy_field_matchings[inner_source_format][legacy_field] = []
                    self.__class__._legacy_field_matchings[inner_source_format][legacy_field].append(json_field)

    def __create_checker(self, rule):
        json_id = rule.json_id[0]
        checkers = []
        for checker in rule.checker:

            if checker.master_format:
                master_format = eval(rule.master_format)
                checker_function_name = checker[1]
                arguments = checker[2][1:-1]
            else:
                master_format = ('all',)
                checker_function_name = checker[0]
                arguments = checker[1][1:-1]
            checkers.append((master_format, checker_function_name, arguments))

        self.__class__._field_definitions[json_id]['checker'] = checkers

    def __create_description(self, rule):
        json_id = rule.json_id[0]
        self.__class__._field_definitions[json_id]['description'] = rule.description

    def __create_producer(self, rule):
        json_id = rule.json_id[0]
        producers = dict()
        for producer in rule.producer_rule:
            if producer.producer_code[0][0] not in producers:
                producers[producer.producer_code[0][0]] = []
            producers[producer.producer_code[0][0]].append(
                    (eval(producer.producer_code[0][1]), eval(producer.value[0])))#FIXME: remove eval
        self.__class__._field_definitions[json_id]['producer'] = producers

    def __create_schema(self, rule):
        json_id = rule.json_id[0]
        self.__class__._field_definitions[json_id]['schema'] = rule.schema if rule.schema else {}

    def __create_json_extra(self, rule):
        from invenio.bibfield_utils import CFG_BIBFIELD_FUNCTIONS
        json_id = rule.json_id[0]
        if rule.json_ext:
            self.__class__._field_definitions[json_id]['json_ext'] = \
                    {'loads': try_to_eval(rule.json_ext.loads.strip(), CFG_BIBFIELD_FUNCTIONS),
                     'dumps': try_to_eval(rule.json_ext.dumps.strip(), CFG_BIBFIELD_FUNCTIONS)}

    #FIXME: it might be nice to have the decorators also extendibles
    def __create_decorators_content(self, rule):
        """
        Extracts from the rule all the possible decorators.
        """
        depends_on = only_if = only_if_master_value = parse_first = memoize = None

        if rule.depends_on:
            depends_on = rule.depends_on[0]
        if rule.only_if:
            only_if = rule.only_if[0]
        if rule.only_if_master_value:
            only_if_master_value = rule.only_if_master_value[0]
        if rule.parse_first:
            parse_first = rule.parse_first[0]
        if rule.memoize:
            try:
                memoize = int(rule.memoize[0][0])
            except IndexError:
                memoize = 300 # FIXME: Default value will be used

        return (depends_on, only_if, only_if_master_value, parse_first, memoize)

    def __resolve_inherit_rules(self):
        """
        Iterates over all the 'inherit' fields after all the normal field
        creation to avoid problem when creating this rules.
        """
        def resolve_inheritance(json_id):
            rule = self.__class__._field_definitions[json_id]
            inherit_from_list = self.__class__._field_definitions[json_id]['inherit_from']
            for inherit_json_id in inherit_from_list:
                #Check if everithing is fine
                if inherit_json_id == json_id:
                    raise BibFieldParserException("Inheritance from itself")
                if inherit_json_id not in self.__class__._field_definitions:
                    raise BibFieldParserException("Unable to solve %s inheritance" % (inherit_json_id,))
                if inherit_json_id in self.__unresolved_inheritence:
                    self._resolve_inheritance(inherit_json_id)
                    self.__unresolved_inheritence.remove(inherit_json_id)
                inherit_rule = self.__class__._field_definitions[inherit_json_id]
                for format in inherit_rule['rules']:
                    if not format in rule['rules']:
                        rule['rules'][format] = []
                    rule['rules'][format].extend(inherit_rule['rules'][format])
                # rule['checker'].extend(inherit_rule['checker'])

        for rule in self.__inherit_rules:
            self._create_rule(rule)

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
            self._create_rule(rule, override=True)

    def __resolve_extend_rules(self):
        """
        Iterates over all the 'extend' field to extend the rule definition of this
        field.
        """
        for rule in self.__extend_rules:
            self._create_rule(rule, extend=True)


def guess_legacy_field_names(fields, master_format):
    """
    Using the legacy rules written in the config file (@legacy) tries to find
    the equivalent json field for one or more legacy fields.

    >>> guess_legacy_fields(('100__a', '245'), 'marc')
    {'100__a':['authors[0].full_name'], '245':['title']}
    """
    res = {}
    if isinstance(fields, six.string_types):
        fields = (fields, )
    for field in fields:
        try:
            res[field] = BibFieldParser.legacy_field_matchings()[master_format].get(field, [])
        except:
            res[field] = []
    return res

def get_producer_rules(field, code):
    """docstring for get_producer_rules"""

    rule = BibFieldParser.field_definitions()[field]
    if isinstance(rule, list):
        if len(rule) == 1:
            # case field[n]
            return [(rule[0].replace('[n]', ''), BibFieldParser.field_definitions()[rule[0]]['producer'].get(code, {}))]
        else:
            # case field[1], field[n]
            rules = []
            for new_field in rule:
                rules.append((new_field.replace('[n]', '[1:]'), BibFieldParser.field_definitions()[new_field]['producer'].get(code, {})))
            return rules
    else:
        return [(field, rule['producer'].get(code, {}))]

