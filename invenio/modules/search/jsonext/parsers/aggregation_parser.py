# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""Aggregation parser extension."""

from pyparsing import Suppress, OneOrMore, Word, alphanums, nestedExpr, \
    originalTextFor, Keyword

from invenio.modules.jsonalchemy.parser import FieldBaseExtensionParser, \
    FieldParser, PYTHON_ALLOWED_EXPR, indentedBlock


class AggregationParser(FieldBaseExtensionParser):

    """Handles the aggregation section from a field definition.

    An example of this section could be::

        title:
            aggregation:
                title(), {'<aggregation_type>': '<aggregagtion_body>'}

        authors:
            aggregation:
                author('native'), {....}
                author('elasticsearch'), {....}

    The parameter passed to the aggregation could be used by the aggregation
    for example to decide if the current aggregation rule will be applied
    depending on the search engine.
    """

    __parsername__ = 'aggregation'

    @classmethod
    def parse_element(cls, indent_stack):
        """Set to the rule the list of aggregations."""
        aggregation_body = (
            Word(alphanums + "_") +
            originalTextFor(nestedExpr()) +
            Suppress(',') +
            PYTHON_ALLOWED_EXPR
        ).setParseAction(lambda toks: {
            'name': toks[0],
            'engine': eval(toks[1]),
            'rule': eval(toks[2])
        })
        return (Keyword('aggregation:').suppress() +
                indentedBlock(OneOrMore(aggregation_body), indent_stack)
                ).setResultsName('aggregation')

    @classmethod
    def create_element(cls, rule, namespace):
        """Prepare the list of aggregations with their names and parameters."""
        id_ = rule.field['json_id']

        aggregations = {} if not rule.extend else \
            FieldParser.field_definitions(namespace)[id_].get(
                'aggregation', {})
        for aggregation in rule.aggregation:
            if aggregation['name'] not in aggregations:
                aggregations[aggregation['name']] = []
            aggregations[aggregation['name']].append((
                aggregation['engine'], aggregation['rule']))
        return aggregations

parser = AggregationParser
