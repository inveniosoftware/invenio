# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

"""REST API for knowledge."""

from functools import wraps

from flask_restful import Resource, abort, fields, marshal_with, reqparse

from invenio.ext.restful import pagination

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound


from . import api, models


def error_handler(f):
    """Handle exceptions."""
    @wraps(f)
    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except NoResultFound:
            abort(404)
        except IntegrityError:
            abort(500)
    return inner


knwkb_mappings_resource_fields = {
    'from': fields.String(attribute='m_key'),
    'to': fields.String(attribute='m_value'),
}

knwkb_resource_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'description': fields.String,
    'type': fields.String(attribute='kbtype'),
    'mappings': fields.Nested(knwkb_mappings_resource_fields),
}


def check_knowledge_access(kb):
    """Check if the knowledge is accessible from api, otherwise abort."""
    if not kb.is_api_accessible:
        abort(403, message="Access Forbidden")


class KnwKBAllResource(Resource):

    """KnwKB resource."""

    method_decorators = [
        error_handler
    ]

    def get(self):
        """Get KnwKB."""
        abort(405)

    def head(self):
        """Head knowledge."""
        abort(405)

    def options(self):
        """Option knowledge."""
        abort(405)

    def post(self):
        """Post knowledge."""
        abort(405)

    def put(self):
        """Put knowledge."""
        abort(405)


class KnwKBResource(Resource):

    """KnwKB resource."""

    method_decorators = [
        error_handler
    ]

    @marshal_with(knwkb_resource_fields)
    def get(self, slug):
        """Get KnwKB.

        Url parameters:
            - from: filter "mappings from"
            - to: filter "mappings to"
            - page
            - per_page
            - match_type: s=substring, e=exact, sw=startswith
            - sortby: 'from' or 'to'
        """
        kb = api.get_kb_by_slug(slug)

        # check if is accessible from api
        check_knowledge_access(kb)

        parser = reqparse.RequestParser()
        parser.add_argument(
            'from', type=str,
            help="Return only entries where key matches this.")
        parser.add_argument(
            'to', type=str,
            help="Return only entries where value matches this.")
        parser.add_argument('page', type=int,
                            help="Require a specific page")
        parser.add_argument('per_page', type=int,
                            help="Set how much result per page")
        parser.add_argument('match_type', type=str,
                            help="s=substring, e=exact, sw=startswith")
        parser.add_argument('sortby', type=str,
                            help="the sorting criteria ('from' or 'to')")
        args = parser.parse_args()
        kb_dict = kb.to_dict()
        kb_dict['mappings'] = KnwKBMappingsResource \
            .search_mappings(kb=kb, key=args['from'], value=args['to'],
                             match_type=args['match_type'],
                             sortby=args['sortby'], page=args['page'],
                             per_page=args['per_page'])
        return kb_dict

    def head(self, slug):
        """Head knowledge."""
        abort(405)

    def options(self, slug):
        """Option knowledge."""
        abort(405)

    def post(self, slug):
        """Post knowledge."""
        abort(405)

    def put(self, slug):
        """Put knowledge."""
        abort(405)


class KnwKBMappingsResource(Resource):

    """KnwKB Mappings resource.

    It returns something like:
        [
            {
                "from": "PICTURE",
                "to": "Pictures"
            },
            {
                "from": "PREPRINT",
                "to": "Preprint"
            },
        ]
    """

    method_decorators = [
        error_handler
    ]

    @staticmethod
    def search_mappings(kb, key=None, value=None, match_type=None,
                        sortby=None, page=None, per_page=None):
        """Search tags for knowledge."""
        if kb.kbtype == models.KnwKB.KNWKB_TYPES['written_as']:
            return pagination.RestfulSQLAlchemyPagination(
                api.query_kb_mappings(
                    kbid=kb.id,
                    key=key or '',
                    value=value or '',
                    match_type=match_type or 's',
                    sortby=sortby or 'to',
                ), page=page or 1, per_page=per_page or 10
            ).items
        return []

    @marshal_with(knwkb_mappings_resource_fields)
    def get(self, slug):
        """Get list of mappings.

        Url parameters:
            - from: filter "mappings from"
            - to: filter "mappings to"
            - page
            - per_page
            - match_type: s=substring, e=exact, sw=startswith
            - sortby: 'from' or 'to'
        """
        kb = api.get_kb_by_slug(slug)

        # check if is accessible from api
        check_knowledge_access(kb)

        parser = reqparse.RequestParser()
        parser.add_argument(
            'from', type=str,
            help="Return only entries where 'from' matches this.")
        parser.add_argument(
            'to', type=str,
            help="Return only entries where 'to' matches this.")
        parser.add_argument('page', type=int,
                            help="Require a specific page")
        parser.add_argument('per_page', type=int,
                            help="Set how much result per page")
        parser.add_argument('match_type', type=str,
                            help="s=substring, e=exact, sw=startswith")
        parser.add_argument('sortby', type=str,
                            help="the sorting criteria ('from' or 'to')")
        args = parser.parse_args()
        return KnwKBMappingsResource \
            .search_mappings(kb, args['from'], args['to'],
                             args['match_type'], args['sortby'],
                             args['page'], args['per_page'])

    def head(self, slug):
        """Head knowledge."""
        abort(405)

    def options(self, slug):
        """Option knowledge."""
        abort(405)

    def post(self, slug):
        """Post knowledge."""
        abort(405)

    def put(self, slug):
        """Put knowledge."""
        abort(405)


class KnwKBMappingsToResource(Resource):

    """KnwKB List mappings "to" resource.

    It returns something like:

    .. code-block:: javascript

        [
            "Pictures",
            "Preprint",
            "Published Article"
        ]

    The array is a list of available values.
    """

    method_decorators = [
        error_handler
    ]

    @staticmethod
    def search_list(kb, value=None, match_type=None,
                    page=None, per_page=None, unique=False):
        """Search "mappings to" for knowledge."""
        # init
        page = page or 1
        per_page = per_page or 10

        if kb.kbtype == models.KnwKB.KNWKB_TYPES['written_as']:
            # get the base query
            query = api.query_kb_mappings(
                kbid=kb.id,
                value=value or '',
                match_type=match_type or 's'
            ).with_entities(models.KnwKBRVAL.m_value)
            # if you want a 'unique' list
            if unique:
                query = query.distinct()
            # run query and paginate
            return [item.m_value for item in
                    pagination.RestfulSQLAlchemyPagination(
                        query, page=page or 1,
                        per_page=per_page or 10
                    ).items]
        elif kb.kbtype == models.KnwKB.KNWKB_TYPES['dynamic']:
            items = api.get_kbd_values(kb.name, value)
            return pagination.RestfulPagination(
                page=page, per_page=per_page,
                total_count=len(items)
            ).slice(items)
        return []

    def get(self, slug):
        """Get list of "mapping to".

        Url parameters
            - unique: if set, return a unique list
            - filter: filter "mappings to"
            - page
            - per_page
            - match_type: s=substring, e=exact, sw=startswith
        """
        kb = api.get_kb_by_slug(slug)

        # check if is accessible from api
        check_knowledge_access(kb)

        parser = reqparse.RequestParser()
        parser.add_argument(
            'unique', type=bool,
            help="The list contains unique names of 'mapping to'")
        parser.add_argument(
            'filter', type=str,
            help="Return only entries where 'to' matches this.")
        parser.add_argument('page', type=int,
                            help="Require a specific page")
        parser.add_argument('per_page', type=int,
                            help="Set how much result per page")
        parser.add_argument('match_type', type=str,
                            help="s=substring, e=exact, sw=startswith")
        args = parser.parse_args()
        return KnwKBMappingsToResource \
            .search_list(kb, args['filter'],
                         args['match_type'],
                         args['page'], args['per_page'], args['unique'])

    def head(self, slug):
        """Head knowledge."""
        abort(405)

    def options(self, slug):
        """Option knowledge."""
        abort(405)

    def post(self, slug):
        """Post knowledge."""
        abort(405)

    def put(self, slug):
        """Put knowledge."""
        abort(405)


class KnwKBMappingsFromResource(Resource):

    """KnwKB List mappings "from" resource.

    It returns something like:

    .. code-block:: javascript

        [
            "PICTURE",
            "PREPRINT",
            "ARTICLE",
            "REPORT"
        ]

    The array is a list of available values.
    """

    method_decorators = [
        error_handler
    ]

    @staticmethod
    def search_list(kb, from_=None, match_type=None,
                    page=None, per_page=None, unique=False):
        """Search "mapping from" for knowledge."""
        # init
        page = page or 1
        per_page = per_page or 10

        if kb.kbtype == models.KnwKB.KNWKB_TYPES['written_as']:
            # get the base query
            query = api.query_kb_mappings(
                kbid=kb.id,
                key=from_ or '',
                match_type=match_type or 's'
            ).with_entities(models.KnwKBRVAL.m_key)
            # if you want a 'unique' list
            if unique:
                query = query.distinct()
            # run query and paginate
            return [item.m_key for item in
                    pagination.RestfulSQLAlchemyPagination(
                        query, page=page or 1,
                        per_page=per_page or 10
                    ).items]
        return []

    def get(self, slug):
        """Get list of "mappings from".

        Url parameters
            - unique: if set, return a unique list
            - filter: filter "mappings from"
            - page
            - per_page
            - match_type: s=substring, e=exact, sw=startswith
        """
        kb = api.get_kb_by_slug(slug)

        # check if is accessible from api
        check_knowledge_access(kb)

        parser = reqparse.RequestParser()
        parser.add_argument(
            'unique', type=bool,
            help="The list contains unique names of 'mapping to'")
        parser.add_argument(
            'filter', type=str,
            help="Return only entries where 'from' matches this.")
        parser.add_argument('page', type=int,
                            help="Require a specific page")
        parser.add_argument('per_page', type=int,
                            help="Set how much result per page")
        parser.add_argument('match_type', type=str,
                            help="s=substring, e=exact, sw=startswith")
        args = parser.parse_args()
        return KnwKBMappingsFromResource \
            .search_list(kb, args['filter'],
                         args['match_type'],
                         args['page'], args['per_page'], args['unique'])

    def head(self, slug):
        """Head knowledge."""
        abort(405)

    def options(self, slug):
        """Option knowledge."""
        abort(405)

    def post(self, slug):
        """Post knowledge."""
        abort(405)

    def put(self, slug):
        """Put knowledge."""
        abort(405)


class NotImplementedKnowledegeResource(Resource):

    """Path not used in REST API."""

    method_decorators = [
        error_handler
    ]

    def get(self, slug, foo, bar=None):
        """Get."""
        abort(405)

    def head(self, slug, foo, bar=None):
        """Head."""
        abort(405)

    def options(self, slug, foo, bar=None):
        """Option."""
        abort(405)

    def post(self, slug, foo, bar=None):
        """Post."""
        abort(405)

    def put(self, slug, foo, bar=None):
        """Put."""
        abort(405)


def setup_app(app, api):
    """setup the resources urls."""
    api.add_resource(
        KnwKBAllResource,
        '/api/knowledge'
    )
    api.add_resource(
        KnwKBResource,
        '/api/knowledge/<string:slug>'
    )
    api.add_resource(
        KnwKBMappingsResource,
        '/api/knowledge/<string:slug>/mappings'
    )
    api.add_resource(
        KnwKBMappingsToResource,
        '/api/knowledge/<string:slug>/mappings/to'
    )
    api.add_resource(
        KnwKBMappingsFromResource,
        '/api/knowledge/<string:slug>/mappings/from'
    )

    # for other urls, return "Method Not Allowed"
    api.add_resource(
        NotImplementedKnowledegeResource,
        '/api/knowledge/<string:slug>/<path:foo>'
    )
