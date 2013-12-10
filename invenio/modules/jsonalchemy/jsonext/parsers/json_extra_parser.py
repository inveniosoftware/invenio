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
## 60 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from pyparsing import Optional, Suppress, indentedBlock, Each

from invenio.base.utils import try_to_eval

from invenio.modules.jsonalchemy.registry import functions
from invenio.modules.jsonalchemy.parser import BaseExtensionParser, FieldParser, \
        python_allowed_expr


class JsonExtraParser(BaseExtensionParser):
    """
    Class to parse and store the information related with how to load and dump
    a non-json object.

    It parses something like this::

        json:
            loads, function_to_load(field)
            dumps, function_to_dump(field)

    The functions to load and dump must have one parameter which is the field
    to parse.
    """

    @classmethod
    def parse_element(cls, indent_stack):
        json_dumps = (Suppress('dumps') + Suppress(',') + python_allowed_expr)\
                .setResultsName("dumps")\
                .setParseAction(lambda toks: toks.value[0])
        json_loads = (Suppress("loads") + Suppress(",") + python_allowed_expr)\
                .setResultsName("loads")\
                .setParseAction(lambda toks: toks.value[0])

        func = indentedBlock(Each((json_dumps, json_loads)), indent_stack)
        return (Suppress('json:') + func)\
                .setResultsName('json_ext')\
                .setParseAction(lambda toks: toks[0][0])

    @classmethod
    def create_element(cls, rule, namespace):
        json_id = rule.json_id[0]

        return {'loads': try_to_eval(rule.json_ext.loads.strip(), functions(namespace)),
                'dumps': try_to_eval(rule.json_ext.dumps.strip(), functions(namespace))}

    @classmethod
    def add_info_to_field(cls, json_id, rule):
        info = {}
        if 'json_ext' in rule:
            info['dumps'] = (json_id, 'json_ext', 'dumps')
            info['loads'] = (json_id, 'json_ext', 'loads')
        return info


JsonExtraParser.__name__ = 'json_ext'
parser = JsonExtraParser
