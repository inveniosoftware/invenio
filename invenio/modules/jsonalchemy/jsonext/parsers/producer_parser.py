# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014 CERN.
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

"""Producer parser extension."""

from pyparsing import Suppress, OneOrMore, Word, alphanums, nestedExpr, \
    originalTextFor, Keyword

from invenio.modules.jsonalchemy.parser import FieldBaseExtensionParser, \
    FieldParser, PYTHON_ALLOWED_EXPR, indentedBlock


class ProducerParser(FieldBaseExtensionParser):

    """Handles the producer section from a field definition.

    An example of this section could be::

        recid:
            producer:
                json_for_marc(), {'001': ''}

        title:
            producer:
                json_for_marc(), {'a': 'title'}

        creator:
            producer:
                json_for_marc('100__'), {....}
                json_for_marc('1001_'), {....}
                json_for_marc('100[^1][^_]'), {....}

    The parameter passed to the producer could be used by the producer for
    example to decide if the current producer rule will be applied depending
    on the tag from the master format. Typically is a string or a `regex` but
    it should be double check with the producer implementation.

    To view the list of possible producer, check the `producer` folder inside
    jsonext or simply::

        >>> from invenio.modules.jsonalchemy.registry import producers
        >>> dict(producers)

    """

    __parsername__ = 'producer'

    @classmethod
    def parse_element(cls, indent_stack):
        """Set. to the rule the list of producers in ``producer`` attribute."""
        producer_body = (Word(alphanums + "_") +
                         originalTextFor(nestedExpr()) +
                         Suppress(',') +
                         PYTHON_ALLOWED_EXPR
                         ).setParseAction(
            lambda toks: {'code': toks[0],
                          'params': eval(toks[1]),
                          'rule': eval(toks[2])})
        return (Keyword('producer:').suppress() +
                indentedBlock(OneOrMore(producer_body), indent_stack)
                ).setResultsName('producer')

    @classmethod
    def create_element(cls, rule, namespace):
        """Prepare the list of producers with their names and parameters."""
        id_ = rule.field['json_id']

        producers = {} if not rule.extend else \
            FieldParser.field_definitions(namespace)[id_].get('producer', {})
        for producer in rule.producer:
            if producer['code'] not in producers:
                producers[producer['code']] = []
            producers[producer['code']].append((producer['params'],
                                                producer['rule']))
        return producers

parser = ProducerParser
