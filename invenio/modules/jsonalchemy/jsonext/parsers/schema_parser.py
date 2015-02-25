# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013 CERN.
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
# 60 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from pyparsing import Keyword

from invenio.base.utils import try_to_eval

from invenio.modules.jsonalchemy.registry import functions
from invenio.modules.jsonalchemy.parser import FieldBaseExtensionParser, \
    DICT_DEF, indentedBlock


class SchemaParser(FieldBaseExtensionParser):

    """
    Parse the schema definitions for fields, using cerberus.

    .. code-block:: ini

        modification_date:
            schema:
                {'modification_date': {
                    'type': 'datetime',
                    'required': True,
                    'default': lambda: __import__('datetime').datetime.now()}}
    """

    @classmethod
    def parse_element(cls, indent_stack):
        """Set the ``schema`` attribute inside the rule."""
        return (Keyword('schema:').suppress() +
                indentedBlock(DICT_DEF, indent_stack)
                ).setParseAction(lambda toks: toks[0]).setResultsName('schema')

    @classmethod
    def create_element(cls, rule, namespace):
        """Just evaluate the content of the schema to a python dictionary."""
        return try_to_eval(rule.schema, functions(namespace))

parser = SchemaParser
