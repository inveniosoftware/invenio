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

from pyparsing import Optional, Suppress, OneOrMore, Word, alphas, alphanums, \
        indentedBlock, nestedExpr, originalTextFor

from invenio.modules.jsonalchemy.parser import BaseExtensionParser, FieldParser,\
        python_allowed_expr


class ProducerParser(BaseExtensionParser):
    """
    """

    @classmethod
    def parse_element(cls, indent_stack):
        producer_code = (Word(alphas, alphanums + "_")\
                + originalTextFor(nestedExpr("(", ")")))\
                .setResultsName('producer_code')
        producer_rule = (Suppress(',') + python_allowed_expr)\
                .setResultsName('producer_rule')\
                .setParseAction(lambda toks: toks[0])
        producer_body = indentedBlock(producer_code + producer_rule, indent_stack)\
                .setParseAction(lambda toks: toks[0])

        return (Suppress('producer:') + OneOrMore(producer_body))\
                .setResultsName('producer')

    @classmethod
    def create_element(cls, rule, namespace):
        json_id = rule.json_id[0]
        assert json_id in FieldParser.field_definitions(namespace)

        producers = {}
        for producer in rule.producer:
            if producer.producer_code[0] not in producers:
                producers[producer.producer_code[0]] = []
            producers[producer.producer_code[0]].append(
                    (eval(producer.producer_code[1]), eval(producer.producer_rule)))#FIXME: remove eval
        return producers

ProducerParser.__name__ = 'producer'
parser = ProducerParser
