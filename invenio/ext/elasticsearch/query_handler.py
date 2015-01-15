"""This file is responsible for formating the elasticsearch query using the
   invenio_query_parser
"""
from invenio_query_parser.walkers.pypeg_to_ast import PypegConverter
from invenio_query_parser import parser
from ast_to_dsl import ASTtoDSLConverter
from config import es_config
from config import query_mapping
from pypeg2 import *


class QueryHandler(object):

    def __init__(self):
        self.astCreator = PypegConverter()
        self.dslCreator = ASTtoDSLConverter(query_mapping.fields)

    def get_dsl_query(self, query):
        if query == "*":  # this is what the UI returns FIXME
            return {"match_all": {}}
        peg = parse(query, parser.Main, whitespace="")
        ast = peg.accept(self.astCreator)
        dsl_query = ast.accept(self.dslCreator)
        return dsl_query

    def get_doc_type(self, query):
        """For now on only records
            Do we need more types?
        """
        pass

    def format_filters(self, filters):
        """Accepts a list of dictionaries
           Each dictionary is a filter
           At first only term filters are supported
        """
        f = lambda x: {"term": x}
        filters = map(f, filters)
        res = {"bool": {"must": filters}}
        return res

    def format_query(self, query, filters=None):
        dsl_query = {"query": query}
        if filters:
            dsl_query = {"query": {
                "filtered": {
                    "query": query,
                    "filter": self.format_filters(filters)
                    }
                }
            }

        # apply aggegation for facets
        dsl_query["aggs"] = es_config.get_records_facets_config()
        dsl_query["highlight"] = es_config.get_records_highlights_config()
        dsl_query["_source"] = es_config.should_return_source
        return dsl_query

    def process_query(self, query, filters):
        dsl_query = self.get_dsl_query(query)
        doc_type = self.get_doc_type(dsl_query)
        return self.format_query(dsl_query, filters)
