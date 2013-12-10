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
    invenio.modules.jsonalchemy.parser
    ---------------------------------

    Fields and models configuration loader.

    This module uses `pyparsing <http://pyparsing.wikispaces.com/>` to read from
    thedifferent configuration files the field and model definitions.

    Extensions to both parsers could be added inside jsonext.parsers
"""
import os
import re
import six

from pyparsing import ParseException, FollowedBy, Suppress, OneOrMore, Word, \
    LineEnd, ZeroOrMore, Optional, Literal, alphas, alphanums, \
    originalTextFor, oneOf, nestedExpr, quotedString, removeQuotes, lineEnd, \
    empty, col, restOfLine, delimitedList, Each, indentedBlock


from .errors import FieldParserException, ModelParserException
from .registry import fields_definitions, models_definitions, parsers

json_id = (Word(alphas + "_", alphanums + "_") + Optional(oneOf("[0] [n]")))\
            .setResultsName("json_id", listAllMatches=True)\
            .setParseAction(lambda toks: "".join(toks))

ident = Word(alphas + "_", alphanums + "_")
dict_def = originalTextFor(nestedExpr('{', '}'))
list_def = originalTextFor(nestedExpr('[', ']'))
dict_access = list_access = originalTextFor(ident + nestedExpr('[', ']'))
function_call = originalTextFor(ZeroOrMore(ident + ".") + ident + nestedExpr('(', ')'))

python_allowed_expr = (dict_def ^ list_def ^ dict_access ^ \
        list_access ^ function_call ^ restOfLine)\
        .setResultsName("value", listAllMatches=True)

def _create_record_field_parser():
    """
    Creates the base parser that can handle field definitions and adds any
    extension placed inside jsonext.parsers.

    BFN like base libray::
        line ::= python_comment | include | field_def

        include ::= "include(" PATH ")"

        field_def ::= [persitent_identifier] [inherit_from] [override] [extend] json_id ["[0]" | "[n]"] "," aliases":" INDENT field_def_body UNDENT
        field_def_body ::= [default] (creator | derived | calculated)
        aliases ::= json_id ["[0]" | "[n]"] ["," aliases]
        json_id ::= (alphas + '_') (alphanums + '_')

        creator ::= "creator:" INDENT creator_body+ UNDENT
        creator_body ::= [decorators] source_format "," source_tags "," python_allowed_expr
        source_format ::= MASTER_FORMATS
        source_tag ::= QUOTED_STRING #reStrucuredText

        derived ::= "derived:" INDENT derived_calculated_body UNDENT
        calculated ::= "calculated:" INDENT derived_calculated_body UNDENT
        derived_calculated_body ::= [decorators] "," python_allowed_exp

        decorators ::= (legacy | memoize | parse_first | depends_on | only_if | only_if_master_value)*
        legacy ::= "@legacy(" correspondences+ ")"
        correspondences ::= "(" source_tag [ "," field_tag_name ] "," subfield ")" # If no subfield needed empty string
        parse_first ::= "@parse_first(" json_id+ ")"
        depends_on ::= "@depends_on(" json_id+ ")"
        only_if ::= "@only_if(" python_condition+ ")"
        only_if_master_value ::= "@only_if_master_value(" python_condition+  ")"

        persistent_identifier ::= @persistent_identifier( level )
        inherit_from ::= "@inherit_from(" json_id+ ")"
        override ::= "@override"
        extend ::= "@extend"
        memoize ::= "@memoize(time)"

        python_allowed_exp ::= ident | list_def | dict_def | list_access | dict_access | function_call | one_line_expr
    """
    indent_stack = [1]

    def check_sub_indent(string, location, tokens):
        cur_col = col(location, string)
        if cur_col > indent_stack[-1]:
            indent_stack.append(cur_col)
        else:
            raise ParseException(string, location, "not a subentry")

    def check_unindent(string, location, tokens):
        if location >= len(string):
            return
        cur_col = col(location, string)
        if not(cur_col < indent_stack[-1] and cur_col <= indent_stack[-2]):
            raise ParseException(string, location, "not an unindent")

    def do_unindent():
        indent_stack.pop()

    INDENT = lineEnd.suppress() + empty + empty.copy().setParseAction(check_sub_indent)
    UNDENT = FollowedBy(empty).setParseAction(check_unindent)
    UNDENT.setParseAction(do_unindent)

    aliases = delimitedList((Word(alphanums + "_") + Optional(oneOf("[0] [n]")))\
            .setParseAction(lambda toks: "".join(toks)))\
            .setResultsName("aliases")

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

    body = Each([Optional(field_def),] + \
            [Optional(p.parser.parse_element(indent_stack)) for p in parsers])
    comment = Literal("#") + restOfLine + LineEnd()
    include = (Suppress("include") + quotedString)\
              .setResultsName("includes", listAllMatches=True)
    rule = (Optional(persistent_identifier) + Optional(inherit_from) + \
            Optional(override) + Optional(extend) +json_id + \
            Optional(Suppress(",") + aliases) + Suppress(":") + \
            INDENT + body + UNDENT)\
           .setResultsName("rules", listAllMatches=True)

    return OneOrMore(rule | include | comment.suppress())


def _create_record_model_parser():
    """
    Creates a parser that can handle model definitions.

    BFN like grammar::

        record_model ::= python_comment | fields
        fields ::= "fields:" INDENT [inherit_from] [list_of_fields]
        inherit_from ::= "@inherit_from(" json_id+  ")"
        list_of_fields ::= json_id [ "=" json_id ] # new field name = existing field name

    Note: Unlike the field configuration files where you can specify more than
    one field inside each file for the record models only one definition is
    allowed by file.
    """
    indent_stack = [1]

    field_def = (Word(alphas + "_", alphanums + "_") + \
                 Optional(Suppress("=") + \
                 Word(alphas + "_", alphanums + "_")))\
                .setResultsName("field_definition")
    inherit_from = (Suppress("@inherit_from") + \
                    originalTextFor(nestedExpr("(", ")")))\
                   .setResultsName("inherit_from")

    fields = (Suppress("fields:") + \
              indentedBlock(inherit_from | field_def, indent_stack))\
             .setResultsName("fields")
    comment = Literal("#") + restOfLine + LineEnd()
    return OneOrMore(comment | Each([fields, ] + \
            [Optional(p.parser.parse_element(indent_stack)) for p in parsers]))


class FieldParser(object):
    """Field definitions parser"""

    _field_definitions = {}
    """Dictionary containing all the rules needed to create and validate json fields"""

    _legacy_field_matchings = {}
    """Dictionary containing matching between the legacy master format and the current json"""

    def __init__(self, namespace):
        self.files = list(fields_definitions(namespace))
        self.__namespace = namespace
        self.__inherit_rules = []
        self.__unresolved_inheritence = []
        self.__override_rules = []
        self.__extend_rules = []

    @classmethod
    def field_definitions(cls, namespace):
        if namespace not in cls._field_definitions:
            cls.reparse(namespace)
        return cls._field_definitions.get(namespace)

    @classmethod
    def field_definition_model_based(cls, field_name, model_name, namespace):
        if model_name in ModelParser.model_definitions(namespace):
            field_name = ModelParser.model_definitions(namespace)[model_name] \
                    ['fields'].get(field_name, field_name)
        return cls.field_definitions(namespace).get(field_name, None)

    @classmethod
    def legacy_field_matchings(cls, namespace):
        if namespace not in cls._legacy_field_matchings:
            cls.reparse(namespace)
        return cls._legacy_field_matchings

    @classmethod
    def reparse(cls, namespace):
        cls._field_definitions[namespace] = {}
        cls._legacy_field_matchings = {}
        cls(namespace)._create()
        # It invalidates the Model definitions too as they relay on the field definitions
        ModelParser.reparse(namespace)

    def _create(self):
        """
        Fills up _field_definitions and _legacy_field_matchings dictionary with
        the rules defined inside the configuration files.

        It also resolve the includes present inside the configuration files and
        recursively the ones in the other files.

        This method should not be used (unless you really know what your are doing),
        use instead :meth:`reparse`
        """
        already_included = [os.path.basename(f) for f in self.files]
        for field_file in self.files:
            parser = _create_record_field_parser()
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
        if json_id in self.__class__._field_definitions[self.__namespace] and not override and not extend:
            raise FieldParserException("Name error: '%s' field name already defined"
                                    % (rule.json_id[0],))
        if not json_id in self.__class__._field_definitions[self.__namespace] and (override or extend):
            raise FieldParserException("Name error: '%s' field name not defined"
                                    % (rule.json_id[0],))

        #Workaround to keep clean doctype files
        #Just creates a dict entry with the main json field name and points it to
        #the full one i.e.: 'authors' : ['authors[0]', 'authors[n]']
        if '[0]' in json_id or '[n]' in json_id:
            main_json_id = re.sub('(\[n\]|\[0\])', '', json_id)
            if not main_json_id in self.__class__._field_definitions[self.__namespace]:
                self.__class__._field_definitions[self.__namespace][main_json_id] = []
            self.__class__._field_definitions[self.__namespace][main_json_id].append(json_id)

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
            rules = self.__class__._field_definitions[self.__namespace][json_id]['rules']
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
            self.__class__._field_definitions[self.__namespace][json_id]['override'] = override
            self.__class__._field_definitions[self.__namespace][json_id]['rules'].update(rules)
            self.__class__._field_definitions[self.__namespace][json_id]['aliases'] = \
                    aliases or self.__class__._field_definitions[self.__namespace][json_id]['aliases']
            self.__class__._field_definitions[self.__namespace][json_id]['persistent_identifier'] = \
                    persistent_id or self.__class__._field_definitions[self.__namespace][json_id]['persistent_identifier']
            self.__class__._field_definitions[self.__namespace][json_id]['inherit_from'] = \
                    inherit_from or self.__class__._field_definitions[self.__namespace][json_id]['inherit_from']
        elif extend:
            self.__class__._field_definitions[self.__namespace][json_id]['extend'] = extend
            self.__class__._field_definitions[self.__namespace][json_id]['aliases'].extend(aliases)
        else:
            self.__class__._field_definitions[self.__namespace][json_id] = {'inherit_from'  : inherit_from,
                                               'rules'         : rules,
                                               'aliases'       : aliases,
                                               'persistent_identifier': persistent_id,
                                               'override'     : override,
                                               'extend'       : extend,
                                              }

        self.__resolve_parser_extensions(rule)


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
                legacy_rule = legacy_rule[1]
            else:
                inner_source_format = source_format

            if not inner_source_format in self.__class__._legacy_field_matchings:
                self.__class__._legacy_field_matchings[inner_source_format] = {}

            for field_legacy_rule in legacy_rule:
                #Allow string and tuple in the config file
                legacy_fields = isinstance(field_legacy_rule[0], six.string_types) and (field_legacy_rule[0], ) or field_legacy_rule[0]
                json_field = json_id
                if field_legacy_rule[-1]:
                    json_field = '.'.join((json_field, field_legacy_rule[-1]))
                for legacy_field in legacy_fields:
                    if not legacy_field in self.__class__._legacy_field_matchings[inner_source_format]:
                        self.__class__._legacy_field_matchings[inner_source_format][legacy_field] = []
                    self.__class__._legacy_field_matchings[inner_source_format][legacy_field].append(json_field)

    def __resolve_parser_extensions(self, rule):
        """
        For each of the extension available it tries to apply it in the incoming
        rule
        """
        json_id = rule.json_id[0]
        assert json_id in self.__class__._field_definitions[self.__namespace]
        for parser_extension in parsers:
            if getattr(rule, parser_extension.parser.__name__, None):
                self.__class__._field_definitions[self.__namespace][json_id][parser_extension.parser.__name__] = \
                        parser_extension.parser.create_element(rule, self.__namespace)

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
            rule = self.__class__._field_definitions[self.__namespace][json_id]
            inherit_from_list = self.__class__._field_definitions[self.__namespace][json_id]['inherit_from']
            for inherit_json_id in inherit_from_list:
                #Check if everithing is fine
                if inherit_json_id == json_id:
                    raise FieldParserException("Inheritance from itself")
                if inherit_json_id not in self.__class__._field_definitions[self.__namespace]:
                    raise FieldParserException("Unable to solve %s inheritance" % (inherit_json_id,))
                if inherit_json_id in self.__unresolved_inheritence:
                    self._resolve_inheritance(inherit_json_id)
                    self.__unresolved_inheritence.remove(inherit_json_id)
                inherit_rule = self.__class__._field_definitions[self.__namespace][inherit_json_id]
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


class ModelParser(object):
    """Record model parser"""

    _model_definitions = {}
    """ """

    def __init__(self, namespace):
        #Autodiscover .cfg files
        self.files = list(models_definitions(namespace))
        self.__namespace = namespace

    @classmethod
    def model_definitions(cls, namespace):
        if namespace not in cls._model_definitions:
            cls.reparse(namespace)
        return cls._model_definitions.get(namespace)

    @classmethod
    def reparse(cls, namespace):
        cls._model_definitions[namespace] = {}
        cls(namespace)._create()

    def _create(self):
        """
        Fills up _model_definitions dictionary with what is written inside the
        *.cfg  model descriptions

        It also resolve inheritance at creation time and name matching for the
        field names present inside the model file

        The result looks like this::

            {'model': {'fields': {'name_for_fieldfield1': json_id1,
                                  'name_for_field2': json_id2,
                                            ....
                                  'name_for_fieldN': fieldN },
                       'inherit_from: [(inherit_from_list), ...]
                       },
             ...
            }

        This method should not be used (unless you really know what your are doing),
        use instead :meth:`reparse`

        :raises: ModelParserException in case of missing model definition
                 (helpful if we use inheritance) or in case of unknown field name.
        """
        for model_file in self.files:
            parser = _create_record_model_parser()
            model_name = os.path.basename(model_file).split('.')[0]
            if model_name in self.__class__._model_definitions[self.__namespace]:
                raise ModelParserException("Already defined record model: %s" % (model_name,))
            self.__class__._model_definitions[self.__namespace][model_name] = {'fields': {},
                                                             'super': [],
                                                            }
            model_definition = parser.parseFile(model_file, parseAll=True)

            if not model_definition.fields:
                raise ModelParserException("Field definition needed")
            for field_def in model_definition.fields[0]:
                if field_def.inherit_from:
                    self.__class__._model_definitions[self.__namespace][model_name]['super'].extend(eval(field_def[0]))
                else:
                    if len(field_def) == 1:
                        json_id = field_def[0]
                        field_name = json_id
                    else:
                        field_name = field_def[0]
                        json_id = field_def[1]
                    if not json_id in FieldParser.field_definitions(self.__namespace):
                        raise ModelParserException("Unknown field name: %s" % (json_id,))

                    self.__class__._model_definitions[self.__namespace][model_name]['fields'][field_name] = json_id

            self.__resolve_parser_extensions(model_name, model_definition)

        for model, model_definition in self.__class__._model_definitions[self.__namespace].items():
            model_definition['fields'] = self.__resolve_inheritance(model)

    def __resolve_inheritance(self, model):
        """
        Resolves the inheritance

        :param model: name of the super model
        :type model: string

        :return: List of new fields to be added to the son model
        :raises: ModelParserException if the super model does not exist.
        """
        try:
            model_definition = self.__class__._model_definitions[self.__namespace][model]
        except KeyError:
            raise ModelParserException("Missing model definition for %s" % (model,))
        fields = {}
        for super_model in model_definition['super']:
            fields.update(self.__resolve_inheritance(super_model))
        fields.update(model_definition['fields'])
        return fields

    def __resolve_parser_extensions(self, model_name, model_def):
        """
        For each of the extension available it tries to apply it in the incoming
        rule
        """
        assert model_name in self.__class__._model_definitions[self.__namespace]
        for parser_extension in parsers:
            if getattr(model_def, parser_extension.parser.__name__, None):
                self.__class__._model_definitions[self.__namespace][model_name][parser_extension.parser.__name__] = \
                        parser_extension.parser.create_element(model_def, self.__namespace)

def guess_legacy_field_names(fields, master_format, namespace):
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
            res[field] = FieldParser.legacy_field_matchings(namespace)[master_format].get(field, [])
        except:
            res[field] = []
    return res

def get_producer_rules(field, code, namespace):
    """docstring for get_producer_rules"""

    rule = FieldParser.field_definitions(namespace)[field]
    if isinstance(rule, list):
        if len(rule) == 1:
            # case field[n]
            return [(rule[0].replace('[n]', ''), FieldParser.field_definitions(namespace)[rule[0]]['producer'].get(code, {}))]
        else:
            # case field[1], field[n]
            rules = []
            for new_field in rule:
                rules.append((new_field.replace('[n]', '[1:]'), FieldParser.field_definitions(namespace)[new_field]['producer'].get(code, {})))
            return rules
    else:
        return [(field, rule['producer'].get(code, {}))]

#pylint: disable=R0921
class BaseExtensionParser(object):
    """Base class for the configuration file extensions"""
    @classmethod
    def parse_element(cls, indent_stack):
        """
        Using pyparsing defines a piece of the grammar to parse the
        extension from configuration file

        :return: pyparsing ParseElement
        """
        raise NotImplemented

    @classmethod
    def create_element(cls, rule, namespace):
        """
        Once the extension is parsed defines the actions that have to be taken
        to store inside the field_definitions the information needed or useful.

        :return: content of the key cls.__name__ inside the field_definitions
        """
        raise NotImplemented

    @classmethod
    def add_info_to_field(cls, json_id, info):
        """
        Optional method to define which information goes inside the
        __meta_metadata__ dictionary and how.

        :return: dictionary to update the existing one inside __meta_metadata__
        """
        return dict()
