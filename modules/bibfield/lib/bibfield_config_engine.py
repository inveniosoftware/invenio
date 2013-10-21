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

from invenio.config import CFG_BIBFIELD_MASTER_FORMATS, CFG_ETCDIR, CFG_PYLIBDIR
from invenio.bibfield_utils import BibFieldDict

from pyparsing import ParseException, FollowedBy, Suppress, OneOrMore, Literal, \
    LineEnd, ZeroOrMore, Optional, Forward, Word, QuotedString, alphas, \
    alphanums, originalTextFor, oneOf, nestedExpr, quotedString, removeQuotes, \
    lineEnd, empty, col, restOfLine, delimitedList, nums


def _create_config_parser():
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

    decorators ::= (peristent_identfier | legacy | do_not_cache | parse_first | depends_on | only_if)*
    peristent_identfier ::= @persitent_identifier( level )
    legacy ::= "@legacy(" correspondences+ ")"
    correspondences ::= "(" source_tag [ "," tag_name ] "," json_id ")"
    parse_first ::= "@parse_first(" jsonid+ ")"
    depends_on ::= "@depends_on(" json_id+ ")"
    only_if ::= "@only_if(" python_condition+ ")"

    inherit_from ::= "@inherit_from()"
    do_not_cache ::= "@do_not_cache"

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
    depends_on = (Suppress("@depends_on") + originalTextFor(nestedExpr("(", ")")))\
                 .setResultsName("depends_on")
    parse_first = (Suppress("@parse_first") + originalTextFor(nestedExpr("(", ")")))\
                  .setResultsName("parse_first")
    do_not_cache = (Suppress("@") + "do_not_cache")\
                   .setResultsName("do_not_cache")
    field_decorator = parse_first ^ depends_on ^ only_if ^ do_not_cache ^ legacy

    #Independent decorators
    inherit_from = (Suppress("@inherit_from") + originalTextFor(nestedExpr("(", ")")))\
                    .setResultsName("inherit_from")

    master_format = (Suppress("@master_format") + originalTextFor(nestedExpr("(", ")")))\
                    .setResultsName("master_format")

    derived_calculated_body = ZeroOrMore(field_decorator) + python_allowed_expr

    derived = "derived" + Suppress(":") + INDENT + derived_calculated_body + UNDENT
    calculated = "calculated" + Suppress(":") + INDENT + derived_calculated_body + UNDENT

    source_tag = quotedString\
                 .setParseAction(removeQuotes)\
                 .setResultsName("source_tag", listAllMatches=True)
    source_format = oneOf(CFG_BIBFIELD_MASTER_FORMATS)\
                    .setResultsName("source_format", listAllMatches=True)
    creator_body = (ZeroOrMore(field_decorator) + source_format + Suppress(",") + source_tag + Suppress(",") + python_allowed_expr)\
                   .setResultsName("creator_def", listAllMatches=True)
    creator = "creator" + Suppress(":") + INDENT + OneOrMore(creator_body) + UNDENT

    checker_function = (Optional(master_format) + ZeroOrMore(ident + ".") + ident + originalTextFor(nestedExpr('(', ')')))\
                       .setResultsName("checker_function", listAllMatches=True)
    checker = ("checker" + Suppress(":") + INDENT + OneOrMore(checker_function) + UNDENT)

    doc_string = QuotedString(quoteChar='"""', multiline=True) | quotedString.setParseAction(removeQuotes)
    subfield = (Suppress("@subfield") + Word(alphanums + "_" + '.') + Suppress(":") + Optional(doc_string))\
                 .setResultsName("subfields", listAllMatches=True)
    documentation = ("documentation" + Suppress(":") + INDENT + Optional(doc_string).setResultsName("main_doc") + ZeroOrMore(subfield) + UNDENT)\
                     .setResultsName("documentation")

    producer_code = Word(alphas + "_", alphanums + "_")\
                    .setResultsName("producer_code", listAllMatches=True)
    producer_body = (producer_code + Suppress(",") + python_allowed_expr)\
                    .setResultsName("producer_def", listAllMatches=True)
    producer = "producer"  + Suppress(":") + INDENT + OneOrMore(producer_body) + UNDENT

    field_def = (creator | derived | calculated)\
                .setResultsName("type_field", listAllMatches=True)

    body = Optional(inherit_from) + Optional(field_def) + Optional(checker) + Optional(documentation) + Optional(producer)
    comment = Literal("#") + restOfLine + LineEnd()
    include = (Suppress("include") + quotedString)\
              .setResultsName("includes", listAllMatches=True)
    rule = (Optional(persistent_identifier) + json_id + Optional(Suppress(",") + aliases) + Suppress(":") + INDENT + body + UNDENT)\
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

        self.config_rules = {}
        self.legacy_rules = {}

        self._unresolved_inheritence = []
        self._create_config_rules()

    def write_to_file(self, file_name=CFG_PYLIBDIR + '/invenio/bibfield_config.py'):
        """
        Writes into file_name config_rules and to access
        then afterwards from the readers
        """
        fd = open(file_name, 'w')
        fd.write('config_rules=%s' % (repr(self.config_rules), ))
        fd.write('\n')
        fd.write('legacy_rules=%s' % (repr(self.legacy_rules), ))
        fd.write('\n')
        fd.close()

    def _create_config_rules(self):
        """
        Fills up config_rules dictionary with the rules defined inside the
        configuration file.

        It also resolve the includes present inside the main configuration file
        and recursively the ones in the other files.

        It uses @see: _create_creator_rule() and @see: _create_derived_calculated_rule()
        to fill up config_rules
        """
        parser = _create_config_parser()
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
            if rule.inherit_from or rule.type_field[0] == "creator":
                self._create_creator_rule(rule)
            elif rule.type_field[0] == "derived" or rule.type_field[0] == "calculated":
                self._create_derived_calculated_rule(rule)
            else:
                assert False, 'Type creator, derived or calculated expected or inherit field'

        #Resolve inheritance
        for i in xrange(len(self._unresolved_inheritence) - 1, -1, -1):
            self._resolve_inheritance(self._unresolved_inheritence[i])
            del self._unresolved_inheritence[i]

    def _create_creator_rule(self, rule):
        """
        Creates the config_rule entries for the creator rules.
        The result looks like this:

        {'json_id':{'rules': { 'inherit_from'        : (inherit_from_list),
                               'source_format'       : [translation_rules],
                               'parse_first'         : (parse_first_json_ids),
                               'depends_on'          : (depends_on_json_id),
                               'only_if'             : (only_if_boolean_expressions),
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

        #Workaround to keep clean doctype files
        #Just creates a dict entry with the main json field name and points it to
        #the full one i.e.: 'authors' : ['authors[0]', 'authors[n]']
        if '[0]' in json_id or '[n]' in json_id:
            main_json_id = re.sub('(\[n\]|\[0\])', '', json_id)
            if not main_json_id in self.config_rules:
                self.config_rules[main_json_id] = []
            self.config_rules[main_json_id].append(json_id)

        aliases = []
        if rule.aliases:
            aliases = rule.aliases.asList()

        persistent_id = None
        if rule.persistent_identifier:
            persistent_id = int(rule.persistent_identifier[0][0])

        inherit_from = None
        if rule.inherit_from:
            self._unresolved_inheritence.append(json_id)
            inherit_from = eval(rule.inherit_from[0])

        rules = {}
        for creator in rule.creator_def:

            source_format = creator.source_format[0]

            if source_format not in rules:
                #Allow several tags point to the same json id
                rules[source_format] = []

            (depends_on, only_if, parse_first) = self._create_decorators_content(creator)
            self._create_legacy_rules(creator.legacy, json_id, source_format)

            rules[source_format].append({'source_tag'           : creator.source_tag[0].split(),
                                         'value'                : creator.value[0],
                                         'depends_on'           : depends_on,
                                         'only_if'              : only_if,
                                         'parse_first'          : parse_first})

        #Chech duplicate names to overwrite configuration
        if not json_id in self.config_rules:
            self.config_rules[json_id] = {'inherit_from'  : inherit_from,
                                          'rules'         : rules,
                                          'checker'       : [],
                                          'documentation' : BibFieldDict(),
                                          'producer'        : {},
                                          'type'          : 'real',
                                          'aliases'       : aliases,
                                          'persistent_identifier': persistent_id,
                                          'overwrite'     : False}
        else:
            self.config_rules[json_id]['overwrite'] = True
            self.config_rules[json_id]['rules'].update(rules)
            self.config_rules[json_id]['aliases'] = \
                    aliases or self.config_rules[json_id]['aliases']
            self.config_rules[json_id]['persistent_identifier'] = \
                    persistent_id or self.config_rules[json_id]['persistent_identifier']
            self.config_rules[json_id]['inherit_from'] = \
                    inherit_from or self.config_rules[json_id]['inherit_from']

        self._create_checkers(rule)
        self._create_documentation(rule)
        self._create_producer(rule)

    def _create_derived_calculated_rule(self, rule):
        """
        Creates the config_rules entries for the virtual fields
        The result is similar to the one of real fields but in this case there is
        only one rule.
        """
        json_id = rule.json_id[0]
        #Chech duplicate names
        if json_id in self.config_rules:
            raise BibFieldParserException("Name error: '%s' field name already defined"
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

        (depends_on, only_if, parse_first) = self._create_decorators_content(rule)
        self._create_legacy_rules(rule.legacy, json_id)

        self.config_rules[json_id] = {'rules'        : {},
                                      'checker'      : [],
                                      'documentation': BibFieldDict(),
                                      'producer'       : {},
                                      'aliases'      : aliases,
                                      'type'         : rule.type_field[0],
                                      'persistent_identifier' : persistent_id,
                                      'overwrite'    : False}

        self.config_rules[json_id]['rules'] = {'value'               : rule.value[0],
                                               'depends_on'          : depends_on,
                                               'only_if'             : only_if,
                                               'parse_first'         : parse_first,
                                               'do_not_cache'        : do_not_cache}

        self._create_checkers(rule)
        self._create_documentation(rule)
        self._create_producer(rule)

    def _create_decorators_content(self, rule):
        """
        Extracts from the rule all the possible decorators.
        """
        depends_on = only_if = parse_first = None

        if rule.depends_on:
            depends_on = rule.depends_on[0]
        if rule.only_if:
            only_if = rule.only_if[0]
        if rule.parse_first:
            parse_first = rule.parse_first[0]

        return (depends_on, only_if, parse_first)

    def _create_legacy_rules(self, legacy_rules, json_id, source_format=None):
        """
        Creates the legacy rules dictionary:

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

            if not inner_source_format in self.legacy_rules:
                self.legacy_rules[inner_source_format] = {}

            for field_legacy_rule in legacy_rule:
                #Allow string and tuple in the config file
                legacy_fields = isinstance(field_legacy_rule[0], basestring) and (field_legacy_rule[0], ) or field_legacy_rule[0]
                json_field = json_id
                if field_legacy_rule[-1]:
                    json_field = '.'.join((json_field, field_legacy_rule[-1]))
                for legacy_field in legacy_fields:
                    if not legacy_field in self.legacy_rules[inner_source_format]:
                        self.legacy_rules[inner_source_format][legacy_field] = []
                    self.legacy_rules[inner_source_format][legacy_field].append(json_field)

    def _resolve_inheritance(self, json_id):
        """docstring for _resolve_inheritance"""
        inherit_from_list = self.config_rules[json_id]['inherit_from']
        rule = self.config_rules[json_id]
        for inherit_json_id in inherit_from_list:
            #Check if everithing is fine
            if inherit_json_id == json_id:
                raise BibFieldParserException("Inheritance from itself")
            if inherit_json_id not in self.config_rules:
                raise BibFieldParserException("Unable to solve %s inheritance" % (inherit_json_id,))
            if inherit_json_id in self._unresolved_inheritence:
                self._resolve_inheritance(inherit_json_id)
                self._unresolved_inheritence.remove(inherit_json_id)
            inherit_rule = self.config_rules[inherit_json_id]
            for format in inherit_rule['rules']:
                if not format in rule['rules']:
                    rule['rules'][format] = []
                rule['rules'][format].extend(inherit_rule['rules'][format])
            rule['checker'].extend(inherit_rule['checker'])

    def _create_checkers(self, rule):
        """
        Creates the list of checker functions and arguments for the given rule
        """
        json_id = rule.json_id[0]
        assert json_id in self.config_rules

        if rule.checker_function:
            if self.config_rules[json_id]['overwrite']:
                self.config_rules[json_id]['checker'] = []
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
                self.config_rules[json_id]['checker'].append((master_format,
                                                              checker_function_name,
                                                              arguments))

    def _create_documentation(self, rule):
        """
        Creates the documentation dictionary for the given rule
        """
        json_id = rule.json_id[0]
        assert json_id in self.config_rules

        if rule.documentation:
            if self.config_rules[json_id]['overwrite']:
                self.config_rules[json_id]['documentation'] = BibFieldDict()
            config_doc = self.config_rules[json_id]['documentation']
            config_doc['doc_string'] = rule.documentation.main_doc
            config_doc['subfields'] = None

            if rule.documentation.subfields:
                for subfield in rule.documentation.subfields:
                    key = "%s.%s" % ('subfields', subfield[0].replace('.', '.subfields.'))
                    config_doc[key] = {'doc_string': subfield[1],
                                       'subfields' : None}

    def _create_producer(self, rule):
        """
        Creates the dictionary of possible producer formats for the given rule
        """
        json_id = rule.json_id[0]
        assert json_id in self.config_rules

        if rule.producer_def:
            if self.config_rules[json_id]['overwrite']:
                self.config_rules[json_id]['producer'] = {}
            for producer in rule.producer_def:
                producer_code = producer.producer_code[0]
                rule = producer.value[0]
                if not producer_code in self.config_rules[json_id]['producer']:
                    self.config_rules[json_id]['producer'][producer_code] = []
                self.config_rules[json_id]['producer'][producer_code].append(eval(rule))
