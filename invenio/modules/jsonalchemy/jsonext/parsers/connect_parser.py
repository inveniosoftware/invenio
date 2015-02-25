# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from pyparsing import Keyword, Literal, SkipTo, Optional, quotedString, \
    removeQuotes

from invenio.base.utils import try_to_eval

from invenio.modules.jsonalchemy.errors import FieldParserException
from invenio.modules.jsonalchemy.parser import \
    DecoratorAfterEvalBaseExtensionParser


class ConnectParser(DecoratorAfterEvalBaseExtensionParser):
    """
    Handles the @connect decorator::

        authors:
            derived:
                @connect('creators', handler_function)
                @connect('contributors' handler_function)
                self.get_list('creators') + self.get_list(contributors)

    The handler functions will receive as parameters ``self`` and the current
    value of the field
    """

    __parsername__ = 'connect'

    @classmethod
    def parse_element(cls, indent_stack):
        """Sets ``connect`` attribute to the rule"""
        return (Keyword("@connect").suppress() +
                Literal('(').suppress() +
                quotedString.setResultsName('field')
                .setParseAction(removeQuotes) +
                Optional(Literal(',').suppress() +
                         SkipTo(')')).setResultsName('func') +
                Literal(')').suppress()
                ).setResultsName("connect").setParseAction(
                    lambda toks: {
                        'connected_field': toks.field,
                        'update_function': toks.func[0]
                        if toks.func else None
                    })

    @classmethod
    def create_element(cls, rule, field_def, content, namespace):
        """Simply returns the list with the tuples"""
        from invenio.modules.jsonalchemy.parser import FieldParser
        if isinstance(content, dict):
            content = (content, )
        else:
            content = content.asList()
        # Conect to the other side
        for connect in content:
            try:
                connected_field = FieldParser.field_definitions(
                    namespace)[connect['connected_field']]
            except KeyError:
                raise FieldParserException(
                    "Definition for '%(field)s' not found, maybe adding "
                    "@parse_first('%(field)s') could help" %
                    {'field': connect['connected_field']})
            # Add it to all the rules (all master format, derived and
            # calculated)
            for connected_rules in connected_field['rules'].values():
                for connected_rule in connected_rules:
                    # Add parse_first for connected field
                    if 'parse_first' not in connected_rule['decorators'][
                            'before']:
                        connected_rule['decorators']['before'][
                            'parse_first'] = []
                    connected_rule['decorators']['before']['parse_first']\
                        .append(rule.field['json_id'])
                    # Connect fields
                    if 'connect' not in connected_rule['decorators']['after']:
                        connected_rule['decorators']['after']['connect'] = []
                    connected_rule['decorators']['after']['connect']\
                        .append({'connected_field': rule.field['json_id'],
                                 'update_function': connect['update_function']
                                 })

        return content

    @classmethod
    def add_info_to_field(cls, json_id, info, args):
        """Simply returns the list with the tuples"""
        return args

    @classmethod
    def evaluate(cls, json, field_name, action, args):
        """
        Applies the connect funtion with json, field_name and action parameters
        if any functions availabe, otherwise it will put the content of the
        current field into the connected one.
        """
        if action == 'get':
            return

        from invenio.modules.jsonalchemy.registry import functions
        for info in args:
            if info['update_function'] is None:
                json.__setitem__(info['connected_field'],
                                 json[field_name],
                                 exclude='connect')
            else:
                try_to_eval(info['update_function'],
                            functions(json.additional_info.namespace))(
                                json, field_name, info['connected_field'],
                                action)

parser = ConnectParser
