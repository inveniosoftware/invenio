"""Implement an invenion query AST to elasticsearch dsl converter"""

from invenio_query_parser import ast
from invenio_query_parser.visitor import make_visitor


class ASTtoDSLConverter(object):
    visitor = make_visitor()

    def __init__(self, conf_dict):
        """Provide a dictinary mapping invenio keywords
           to elasticsearch fields as a list
           eg. {"author": ["author.last_name, author.first_name"]}
        """
        self.keyword_dict = conf_dict

    def map_keyword_to_fields(self, keyword):
        if self.keyword_dict:
            res = self.keyword_dict.get(keyword)
            return res if res else [str(keyword)]
        return [str(keyword)]

    @visitor(ast.KeywordOp)
    def visit(self, node, keyword, value):
        """This function should return either a filter or a query
           For now on it returns only queries
        """
        l = self.map_keyword_to_fields(keyword.value)
        if keyword.value == "fulltext":
            nested_dict = {
                "nested": {
                    "path": "documents",
                    "query": value(l)
                    }
                }
            return nested_dict
        return value(l)

    @visitor(ast.AndOp)
    def visit(self, node, left, right):
        return {"bool": {"must": [left, right]}}

    @visitor(ast.OrOp)
    def visit(self, node, left, right):
        return {"bool": {"should": [left, right]}}

    @visitor(ast.NotOp)
    def visit(self, node, child):
        return {"bool": {"must_not": [child]}}

    @visitor(ast.ValueQuery)
    def visit(self, node, child):
        return child(["_all"])

    @visitor(ast.Keyword)
    def visit(self, node):
        return node

    @visitor(ast.Value)
    def visit(self, node):
        return lambda x: {
            "multi_match": {
                "query": str(node.value),
                "fields": x
            }
            }

    @visitor(ast.SingleQuotedValue)
    def visit(self, node):
        return lambda x: {
            "multi_match": {
                "query": str(node.value),
                "type": "phrase",
                "fields": x
                }
            }

    @visitor(ast.DoubleQuotedValue)
    def visit(self, node):
        return lambda x: {"bool": {
            "should": [{"term": {str(k): str(node.value)}} for k in x]
            }
            } if x[0] != "_all" else {
                "bool": {
                    "should": [{"term": {str(k): str(node.value)}} for k in
                               self.map_keyword_to_fields("raw_fields")]
                    }
                }

    @visitor(ast.RangeOp)
    def visit(self, node, left, right):
        return lambda x: {"range": {str(x): {"gte": node.left.value,
                                             "lte": node.right.value}}}
