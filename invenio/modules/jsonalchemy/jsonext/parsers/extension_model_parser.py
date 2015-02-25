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

from pyparsing import Keyword, OneOrMore, quotedString, restOfLine, removeQuotes
from werkzeug.utils import import_string

from invenio.base.utils import try_to_eval

from invenio.modules.jsonalchemy.parser import ModelBaseExtensionParser, \
    indentedBlock


class ExtensionModelParser(ModelBaseExtensionParser):  # pylint: disable=W0232
    """
    Handles the extension section in the model definitions::

        fields:
            ....
            extensions:
                'invenio.modules.records.api:RecordIter'
                'invenio.modules.jsonalchemy.bases:Versinable'

    """

    __parsername__ = 'extensions'

    @classmethod
    def parse_element(cls, indent_stack):
        """Sets ``extensions`` attribute to the rule definition"""
        import_line = quotedString.setParseAction(removeQuotes) + restOfLine
        return (Keyword('extensions:').suppress() +
                indentedBlock(OneOrMore(import_line), indent_stack)
                ).setResultsName('extensions')

    @classmethod
    def create_element(cls, rule, namespace):  # pylint: disable=W0613
        """Simply returns the list of extensions"""
        return [e.strip() for e in rule.extensions.asList() if e]

    @classmethod
    def inherit_model(cls, current_value, base_value):
        """Extends the list of extensions with the new ones without repeating"""
        if current_value is None:
            return base_value
        elif base_value is None:
            return current_value
        return list(set(base_value + current_value))

    @classmethod
    def extend_model(cls, current_value, new_value):
        """Like inherit"""
        return cls.inherit_model(current_value, new_value)

    @classmethod
    def add_info_to_field(cls, info):
        """Adds the list of extensions to the model information"""
        return info

    @classmethod
    def evaluate(cls, obj, args):
        """Extend the incoming object with all the new things from args"""
        if args is None:
            return
        extensions = []
        for ext in args:
            try:
                extensions.append(import_string(ext))
            except ImportError:
                extensions.append(try_to_eval(ext))
        extensions.append(obj.__class__)

        obj.__class__ = type(obj.__class__.__name__, tuple(extensions), {})

parser = ExtensionModelParser
