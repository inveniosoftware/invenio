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

from pyparsing import Optional, Suppress, OneOrMore, indentedBlock, nestedExpr,\
        originalTextFor

from invenio.modules.jsonalchemy.parser import BaseExtensionParser, \
        function_call


class CheckerParser(BaseExtensionParser):
    """
    """

    @classmethod
    def parse_element(cls, indent_stack):
        master_format = (Suppress("@master_format") + \
                originalTextFor(nestedExpr("(", ")")))\
                .setResultsName("master_format")\
                .setParseAction(lambda toks: toks[0])
        checker_body = indentedBlock((Optional (master_format) + \
                function_call.setResultsName('func')), indent_stack)

        return (Suppress('checker:') + OneOrMore(checker_body))\
                .setResultsName('checker')\
                .setParseAction(lambda toks: toks[0])

    @classmethod
    def create_element(cls, rule, namespace):
        return None

CheckerParser.__name__ = 'checker'
parser = CheckerParser
