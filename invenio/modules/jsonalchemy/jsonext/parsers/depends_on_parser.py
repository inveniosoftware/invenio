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

from pyparsing import Keyword, Literal, delimitedList, quotedString, \
    removeQuotes
from invenio.modules.jsonalchemy.parser import \
    DecoratorBeforeEvalBaseExtensionParser


class DependsOnParser(DecoratorBeforeEvalBaseExtensionParser):

    """
    Handle the @depends_on decorator::

        authors:
            derived:
                @depends_on('creators', 'contributors')
                self.get_list('creators') + self.get_list(contributors)
    """

    __parsername__ = 'depends_on'

    @classmethod
    def parse_element(cls, indent_stack):
        return (Keyword("@depends_on").suppress() +
                Literal('(').suppress() +
                delimitedList(quotedString.setParseAction(removeQuotes)) +
                Literal(')').suppress()
                ).setResultsName("depends_on")

    @classmethod
    def create_element(cls, rule, field_def, content, namespace):
        """Just returns the list with the field names"""
        return content.asList()

    @classmethod
    def evaluate(cls, reader, args):
        """
        Tries to apply the rules for each field, if it fails on one of them
        returns False
        """
        for key in args:
            if key in reader._json:
                continue
            if not reader._unpack_rule(key):
                return False
        return True

parser = DependsOnParser
