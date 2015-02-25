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

import six

from pyparsing import Keyword, originalTextFor, nestedExpr

from invenio.modules.jsonalchemy.parser import FieldParser, \
    DecoratorOnEvalBaseExtensionParser


class LegacyParser(DecoratorOnEvalBaseExtensionParser):

    """
    Handle the ``@legacy`` decorator.

    .. code-block:: ini

        doi:
            creator:
                @legacy((("024", "0247_", "0247_%"), ""),
                        ("0247_a", ""))
                marc, "0247_", get_doi(value)


        files:
            calculated:
                 @legacy('marc', ("8564_z", "comment"),
                         ("8564_y", "caption", "description"),
                         ("8564_q", "eformat"),
                         ("8564_f", "name"),
                         ("8564_s", "size"),
                         ("8564_u", "url", "url")
                        )
                @parse_first(('recid', ))
                {'url': 'http://example.org'}
    """

    __parsername__ = 'legacy'

    @classmethod
    def parse_element(cls, indent_stack):
        return (Keyword("@legacy").suppress() +
                originalTextFor(nestedExpr("(", ")"))
                ).setResultsName("legacy", listAllMatches=True)

    @classmethod
    def create_element(cls, rule, field_def, content, namespace):
        """Special case of decorator.

        It creates the legacy rules dictionary and it doesn't have any effect
        to the field definitions::

            {'100'   : ['authors[0]'],
             '100__' : ['authors[0]'],
             '100__%': ['authors[0]'],
             '100__a': ['authors[0].full_name'],
             .......
            }
        """
        if namespace not in FieldParser._legacy_field_matchings:
            FieldParser._legacy_field_matchings[namespace] = {}

        for legacy_rule in content:
            legacy_rule = eval(legacy_rule[0])

            if field_def['source_format'] in ('derived', 'calculated'):
                inner_source_format = legacy_rule[0]
                legacy_rule = legacy_rule[1:]
            else:
                inner_source_format = field_def['source_format']

            if inner_source_format not in \
                    FieldParser._legacy_field_matchings[namespace]:
                FieldParser._legacy_field_matchings[namespace][
                    inner_source_format] = {}

            for field_legacy_rule in legacy_rule:
                # Allow string and tuple in the config file
                legacy_fields = (field_legacy_rule[0], ) \
                    if isinstance(field_legacy_rule[0], six.string_types) \
                    else field_legacy_rule[0]
                json_field = rule.field['json_id']
                if field_legacy_rule[-1]:
                    json_field = '.'.join((json_field, field_legacy_rule[-1]))

                for legacy_field in legacy_fields:
                    if legacy_field not in FieldParser._legacy_field_matchings[
                            namespace][inner_source_format]:
                        FieldParser._legacy_field_matchings[
                            namespace][inner_source_format][legacy_field] = []
                    FieldParser._legacy_field_matchings[
                        namespace][inner_source_format][legacy_field]\
                        .append(json_field)

    @classmethod
    def evaluate(cls, value, namespace, args):
        """Evaluate parser.

        This is a special case where the real evaluation of the decorator
        happened before the evaluation.
        """
        return True

parser = LegacyParser
