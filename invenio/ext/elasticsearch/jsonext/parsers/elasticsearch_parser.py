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

"""JsonAchemy parser for elasticsearch Invenio extension."""

from pyparsing import Keyword, Suppress, Word, Optional, Each, \
    OneOrMore, alphanums, restOfLine

from invenio.base.utils import try_to_eval
from invenio.modules.jsonalchemy.parser import FieldBaseExtensionParser, \
    indentedBlock, DICT_DEF
from invenio.modules.jsonalchemy.registry import functions


class ElasticSearchParser(FieldBaseExtensionParser):

    """ElasticSearch jsonalchemy extension."""

    __parsername__ = 'elasticsearch'

    @classmethod
    def parse_element(cls, indent_stack):
        """Parse ``elasticsearch`` section.

        This is an example of the content of this section::
            @extend
            title:
                elasticsearch:
                    mapping: {
                        "properties": {
                            "title": {
                                "index_name": "title",
                                "type": "multi_field",
                                "fields": {
                                    "title": {
                                        "type": "string",
                                        "analyzer": "standard"
                                        },
                                    "sort_title": {
                                        "type": "string",
                                        "analyzer": "simple"
                                        }
                                    }
                                }
                            }
                        }
                    local_tokenizer:
                        title.title, invenio.ext.elasticsearch.token1
                        title.subtitle, invenio.ext.elasticsearch.token2
                    facets: {
                        "authors": {
                            "terms" : {
                                "field" : "facet_authors",
                                "size": 10,
                                "order" : { "_count" : "desc" }
                                }
                            }
                        }
                    highlights: {
                            "number_of_fragments" : 3,
                                "fragment_size" : 70
                        }


        """
        mapping = (Keyword('mapping:').suppress() + DICT_DEF)\
            .setResultsName('mapping')\
            .setParseAction(lambda toks: toks[0])
        tokenizer_field = Word(alphanums + '_' + '.')
        local_tokenizer = (Keyword('local_tokenizer:').suppress() +
                           indentedBlock(
                               OneOrMore(tokenizer_field +
                                         Suppress(',') +
                                         restOfLine), indent_stack)
                           ).setResultsName('local_tokenizer')
        facets = (Keyword('facets:').suppress() + DICT_DEF)\
            .setResultsName('facets')\
            .setParseAction(lambda toks: toks[0])

        highlights = (Keyword('highlights:').suppress() + DICT_DEF)\
            .setResultsName('highlights')\
            .setParseAction(lambda toks: toks[0])

        return (Keyword('elasticsearch:').suppress() +
                indentedBlock(
                    Each([Optional(mapping),
                          Optional(local_tokenizer),
                          Optional(facets),
                          Optional(highlights)]),
                    indent_stack)
                ).setResultsName('elasticsearch')

    @classmethod
    def create_element(cls, rule, namespace):
        """Create the dictionary with the info from the configuratin file."""
        element = dict()
        element['mapping'] = try_to_eval(
            rule.mapping, functions(namespace)) if rule.mapping else {}
        element['facets'] = try_to_eval(
            rule.facets, functions(namespace)) if rule.facets else {}
        element['highlights'] = try_to_eval(
            rule.highlights, functions(namespace)) if rule.highlights else {}
        element['local_tokenizer'] = []
        if rule.local_tokenizer:
            for i in range(0, len(rule.local_tokenizer), 2):
                element['local_tokenizer'].append(
                    (rule.local_tokenizer[i], rule.local_tokenizer[i + 1]))
        return element

parser = ElasticSearchParser
