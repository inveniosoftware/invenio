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

from pyparsing import QuotedString, Suppress, indentedBlock

from invenio.modules.jsonalchemy.parser import BaseExtensionParser


class DescriptionParser(BaseExtensionParser):
    """
    
    """

    @classmethod
    def parse_element(cls, indent_stack):
        doc_double = QuotedString(quoteChar='"""', multiline=True)
        doc_single = QuotedString(quoteChar="'''", multiline=True)
        doc_string = indentedBlock((doc_double | doc_single), indent_stack)
        description = (Suppress('description:') + doc_string).\
                setParseAction(lambda toks: toks[0][0])
        return (description | doc_double | doc_single).setResultsName('description')


    @classmethod
    def create_element(cls, rule, namespace):
        return rule.description

DescriptionParser.__name__ = 'description'
parser = DescriptionParser
