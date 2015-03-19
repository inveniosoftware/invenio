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

from flask import url_for, request
from flask_restful import Resource

from invenio.testsuite import InvenioTestCase, make_test_suite, run_test_suite
from invenio.ext.restful import require_api_auth, require_oauth_scopes, \
    require_header
from invenio.ext.sqlalchemy import db


class DecoratorsTestCase(InvenioTestCase):
    def setUp(self):
        from invenio.modules.accounts.models import User
        from invenio.modules.oauth2server.registry import scopes
        from invenio.modules.oauth2server.models import Token, Scope

        # Setup variables:
        self.called = dict()

        # Setup test scopes
        with self.app.app_context():
            scopes.register(Scope(
                'test:testscope',
                group='Test',
                help_text='Test scope',
            ))

        # Setup API resources
        class Test1Resource(Resource):
            # NOTE: Method decorators are applied in reverse order
            method_decorators = [
                require_oauth_scopes('test:testscope'),
                require_api_auth(),
            ]

            def get(self):
                assert request.oauth.access_token
                return "success", 200

            def post(self):
                assert request.oauth.access_token
                return "success", 200

            @require_header('Content-Type', 'application/json')
            def put(self):
                return "success", 200

        class Test2Resource(Resource):
            @require_api_auth()
            @require_oauth_scopes('test:testscope')
            def get(self):
                assert request.oauth.access_token
                return "success", 200

            @require_api_auth()
            @require_oauth_scopes('test:testscope')
            def post(self):
                assert request.oauth.access_token
                return "success", 200

            @require_header('Content-Type', 'text/html')
            def put(self):
                return "success", 200

        # Register API resources
        api = self.app.extensions['restful']
        api.add_resource(
            Test1Resource,
            '/api/test1/decoratorstestcase/'
        )
        api.add_resource(
            Test2Resource,
            '/api/test2/decoratorstestcase/'
        )

        # Create a user
        self.user = User(
            email='info@invenio-software.org', nickname='tester'
        )
        self.user.password = "tester"
        db.session.add(self.user)
        db.session.commit()

        # Create tokens
        self.token = Token.create_personal(
            'test-', self.user.id, scopes=['test:testscope'], is_internal=True)
        self.token_noscope = Token.create_personal(
            'test-', self.user.id, scopes=[], is_internal=True)

    def tearDown(self):
        db.session.delete(self.user)
        db.session.delete(self.token.client)
        db.session.delete(self.token)
        db.session.delete(self.token_noscope.client)
        db.session.delete(self.token_noscope)
        db.session.commit()

    def test_require_api_auth_test1(self):
        res = self.client.get(url_for('test1resource'))
        self.assert401(res)
        res = self.client.get(
            url_for('test1resource', access_token=self.token.access_token))
        self.assert200(res)

    def test_require_api_auth_test2(self):
        res = self.client.get(url_for('test2resource'))
        self.assert401(res)
        res = self.client.get(
            url_for('test2resource', access_token=self.token.access_token))
        self.assert200(res)

    def test_require_oauth_scopes_test1(self):
        res = self.client.post(
            url_for('test1resource', access_token=self.token.access_token))
        self.assert200(res)
        res = self.client.post(
            url_for('test1resource',
                    access_token=self.token_noscope.access_token))
        self.assertStatus(res, 403)

    def test_require_oauth_scopes_test2(self):
        res = self.client.post(
            url_for('test2resource', access_token=self.token.access_token))
        self.assert200(res)
        res = self.client.post(
            url_for('test2resource',
                    access_token=self.token_noscope.access_token))
        self.assertStatus(res, 403)

    def test_require_header_test1(self):
        res = self.client.put(
            url_for('test1resource', access_token=self.token.access_token),
            headers=[('Content-Type', 'application/json')])
        self.assert200(res)
        res = self.client.put(
            url_for('test1resource', access_token=self.token.access_token),
            headers=[('Content-Type', 'text/html')])
        self.assertStatus(res, 415)

    def test_require_header_test2(self):
        res = self.client.put(
            url_for('test2resource'),
            headers=[('Content-Type', 'text/html; charset=UTF-8')])
        self.assert200(res)
        res = self.client.put(
            url_for('test2resource'),
            headers=[('Content-Type', 'application/json')])
        self.assertStatus(res, 415)


class RestfulPaginationTestCase(InvenioTestCase):

    def setUp(self):
        """Set up some dummy data and a resource."""
        from invenio.modules.accounts.models import User
        from invenio.modules.oauth2server.models import Token

        self.data = range(25)

        # setup test api resources

        class TestDataResource(Resource):

            method_decorators = [
                require_api_auth()
            ]

            @require_header('Content-Type', 'application/json')
            def get(self):
                import json
                from flask import make_response
                from invenio.ext.restful.errors import(
                    InvalidPageError
                )
                from invenio.ext.restful import pagination
                # Test to see that the exceptions are raised correctly
                # In restful.py it is not needed because the error_hanler
                # takes care of exceptions
                response = None
                try:
                    # test data
                    testdata = range(25)
                    endpoint = request.endpoint
                    args = request.args
                    page = int(args.get('page', 1))
                    per_page = int(args.get('per_page', 10))
                    p = pagination.RestfulPagination(
                        page=page, per_page=per_page, total_count=len(testdata)
                    )
                    data_to_return = p.slice(testdata)
                    kwargs = {}
                    kwargs['endpoint'] = endpoint
                    kwargs['args'] = request.args
                    link_header = p.link_header(**kwargs)
                    response = make_response(json.dumps(data_to_return))
                    response.headers[link_header[0]] = link_header[1]
                    response.headers['Content-Type'] = request.headers['Content-Type']
                except InvalidPageError as e:
                    exception = {}
                    exception['message'] = e.error_msg
                    exception['type'] = "{0}".format(type(e))
                    response = make_response(json.dumps(exception))
                return response

        # Register API resources
        api = self.app.extensions['restful']
        api.add_resource(
            TestDataResource,
            '/api/testdata/'
        )

        # Create a user
        self.user = User(
            email='info@invenio-software.org', nickname='tester'
        )
        self.user.password = "tester"
        db.session.add(self.user)
        db.session.commit()

        # create token
        self.token = Token.create_personal(
            'test-', self.user.id, scopes=[], is_internal=True)

    def tearDown(self):
        """Delete the dummy data."""
        del self.data
        db.session.delete(self.user)
        db.session.delete(self.token.client)
        db.session.delete(self.token)
        db.session.commit()

    def test_paginate_page1(self):
        endpoint = "/api/testdata/?"
        link_template = '<{}per_page={}&page={}>; rel="{}"'
        answer_get = self.client.get(
            url_for('testdataresource', access_token=self.token.access_token,
                    per_page=10),
            headers=[('Content-Type', 'application/json')])
        data_returned = answer_get.json
        links_string = answer_get.headers['Link']
        # expected answers
        expected_data = self.data[0:10]
        first_link = link_template.format(endpoint, 10, 1, "first")
        next_link = link_template.format(endpoint, 10, 2, "next")
        last_link = link_template.format(endpoint, 10, 3, "last")
        expected_links_string = "{0},{1},{2}".format(
            first_link,
            next_link,
            last_link
        )
        self.assertEqual(data_returned, expected_data)
        self.assertEqual(links_string, expected_links_string)

    def test_paginate_page2(self):
        endpoint = "/api/testdata/?"
        link_template = '<{}per_page={}&page={}>; rel="{}"'
        answer_get = self.client.get(
            url_for('testdataresource', access_token=self.token.access_token,
                    page=2, per_page=10),
            headers=[('Content-Type', 'application/json')])
        data_returned = answer_get.json
        links_string = answer_get.headers['Link']
        # expected answers
        expected_data = self.data[10:20]
        first_link = link_template.format(endpoint, 10, 1, "first")
        prev_link = link_template.format(endpoint, 10, 1, "prev")
        next_link = link_template.format(endpoint, 10, 3, "next")
        last_link = link_template.format(endpoint, 10, 3, "last")
        expected_links_string = "{0},{1},{2},{3}".format(
            first_link,
            prev_link,
            next_link,
            last_link
        )
        self.assertEqual(data_returned, expected_data)
        self.assertEqual(links_string, expected_links_string)

    def test_paginate_lastpage(self):
        endpoint = "/api/testdata/?"
        link_template = '<{}per_page={}&page={}>; rel="{}"'
        answer_get = self.client.get(
            url_for('testdataresource', access_token=self.token.access_token,
                    page=3, per_page=10),
            headers=[('Content-Type', 'application/json')])
        data_returned = answer_get.json
        links_string = answer_get.headers['Link']

        # expected answers
        expected_data = self.data[20:25]
        first_link = link_template.format(endpoint, 10, 1, "first")
        prev_link = link_template.format(endpoint, 10, 2, "prev")
        last_link = link_template.format(endpoint, 10, 3, "last")
        expected_links_string = "{0},{1},{2}".format(
            first_link,
            prev_link,
            last_link
        )
        self.assertEqual(data_returned, expected_data)
        self.assertEqual(links_string, expected_links_string)

    def test_paginate_nonexistentpage(self):
        from invenio.ext.restful import errors
        answer_get = self.client.get(
            url_for('testdataresource',
                    access_token=self.token.access_token,
                    page=-2, per_page=10),
            headers=[('Content-Type', 'application/json')])
        # Test/assert to see that the exceptions are raised correctly
        expected = {}
        error_msg = "Invalid page number ('{0}').".format(-2)
        expected['message'] = error_msg
        expected['type'] = "{0}".format(errors.InvalidPageError)
        self.assertEqual(answer_get.json, expected)

    def test_paginate_per_pageerror(self):
        from invenio.ext.restful import errors
        answer_get = self.client.get(
            url_for('testdataresource',
                    access_token=self.token.access_token,
                    page=1, per_page=-5),
            headers=[('Content-Type', 'application/json')])
        # Test/assert to see that the exceptions are raised correctly
        expected = {}
        error_msg = (
            "Invalid per_page argument ('{0}'). Number of items "
            "per pages must be positive integer.".format(-5)
        )
        expected['message'] = error_msg
        expected['type'] = "{0}".format(errors.InvalidPageError)
        self.assertEqual(answer_get.json, expected)


class RestfulSQLAlchemyPaginationTestCase(InvenioTestCase):

    def setUp(self):
        from flask_restful import Resource, fields, marshal
        from invenio.modules.accounts.models import User
        from invenio.modules.oauth2server.models import Token

        class TagRepresenation(object):

            """A representation of a tag.

            This class will be only used to return a tag as JSON.
            """

            marshaling_fields = dict(
                id=fields.Integer,
                name=fields.String,
                id_user=fields.Integer
            )

            def __init__(self, retrieved_tag):
                """Initialization.

                Declared the attributes to marshal with a tag.
                :param retrieved_tag: a tag from the database
                """
                #get fields from the given tag
                self.id = retrieved_tag.id
                self.name = retrieved_tag.name
                self.id_user = retrieved_tag.id_user

            def marshal(self):
                """Marshal the Tag."""
                return marshal(self, self.marshaling_fields)

        class TestTagsResource(Resource):

            method_decorators = [
                require_api_auth()
            ]

            @require_header('Content-Type', 'application/json')
            def get(self):
                import json
                from flask import make_response
                from invenio.modules.tags.models import WtgTAG
                from invenio.ext.restful.errors import(
                    RestfulError, InvalidPageError
                )
                from invenio.ext.restful import pagination

                response = None
                try:
                    endpoint = request.endpoint
                    args = request.args
                    page = int(args.get('page', 1))
                    per_page = int(args.get('per_page', 2))
                    # check values arguments and raise exceptions if any errors
                    if per_page < 0:
                        raise RestfulError(
                            error_msg="Invalid per_page: {}".format(per_page),
                            status_code=400
                        )
                    if page < 0:
                        raise InvalidPageError(
                            error_msg="Invalid page: {}".format(page),
                            status_code=400
                        )

                    # need to sort by id
                    # also assuming only one user so no need to filter
                    # user's id
                    tags_q = WtgTAG.query.order_by(WtgTAG.id)
                    p = pagination.RestfulSQLAlchemyPagination(
                        query=tags_q, page=page, per_page=per_page
                    )
                    if page > p.pages:
                        raise InvalidPageError(
                            error_msg="Invalid page: {}".format(page),
                            status_code=400
                        )
                    tags_to_return = map(
                        lambda x: TagRepresenation(x).marshal(),
                        p.items
                    )

                    kwargs = {}
                    kwargs['endpoint'] = endpoint
                    kwargs['args'] = request.args
                    link_header = p.link_header(**kwargs)
                    response = make_response(json.dumps(tags_to_return))
                    response.headers[link_header[0]] = link_header[1]
                    response.headers['Content-Type'] = request.headers['Content-Type']
                except (RestfulError, InvalidPageError) as e:
                    exception = {}
                    exception['message'] = e.error_msg
                    exception['type'] = "{0}".format(type(e))
                    response = make_response(json.dumps(exception))
                return response

        # Register API resources
        api = self.app.extensions['restful']
        api.add_resource(
            TestTagsResource,
            '/api/testtags/'
        )

        # Create a user
        self.user = User(
            email='info@invenio-software.org', nickname='tester'
        )
        self.user.password = "tester"
        db.session.add(self.user)
        db.session.commit()

        # create token
        self.token = Token.create_personal(
            'test-', self.user.id, scopes=[], is_internal=True)

    def tearDown(self):
        db.session.delete(self.user)
        db.session.delete(self.token.client)
        db.session.delete(self.token)
        db.session.commit()

    def test_pagination_flow(self):
        from invenio.modules.tags import api as tags_api
        # template of tags names
        tag_name_template = "tag{}"
        # endpoint
        endpoint = "/api/testtags/?"
        # links template
        link_template = '<{}per_page={}&page={}>; rel="{}"'
        # create tags
        for i in range(1, 7):
            tag_name = tag_name_template.format(i)
            tags_api.create_tag_for_user(self.user.id, tag_name)

        # request first page
        answer_get = self.client.get(
            url_for('testtagsresource', access_token=self.token.access_token,
                    page=1, per_page=2),
            headers=[('Content-Type', 'application/json')])
        # check to ensure correct results
        tags_names_from_request = [x['name'] for x in answer_get.json]
        links_string = answer_get.headers['Link']
        expected_names = []
        for i in range(1, 3):
            expected_name = tag_name_template.format(i)
            expected_names.append(expected_name)

        first_link = link_template.format(endpoint, 2, 1, "first")
        next_link = link_template.format(endpoint, 2, 2, "next")
        last_link = link_template.format(endpoint, 2, 3, "last")
        expected_links_string = "{0},{1},{2}".format(
            first_link,
            next_link,
            last_link
        )
        self.assertEqual(set(tags_names_from_request), set(expected_names))
        self.assertEqual(links_string, expected_links_string)

        tags_names_from_request = []
        expected_names = []
        # request second page
        answer_get = self.client.get(
            url_for('testtagsresource', access_token=self.token.access_token,
                    page=2, per_page=2),
            headers=[('Content-Type', 'application/json')])
        # check to ensure correct results
        tags_names_from_request = [x['name'] for x in answer_get.json]
        links_string = answer_get.headers['Link']
        # check if names of tags are the expected ones
        expected_names = []
        for i in range(3, 5):
            expected_name = tag_name_template.format(i)
            expected_names.append(expected_name)

        first_link = link_template.format(endpoint, 2, 1, "first")
        prev_link = link_template.format(endpoint, 2, 1, "prev")
        next_link = link_template.format(endpoint, 2, 3, "next")
        last_link = link_template.format(endpoint, 2, 3, "last")
        expected_links_string = "{0},{1},{2},{3}".format(
            first_link,
            prev_link,
            next_link,
            last_link
        )

        self.assertEqual(set(tags_names_from_request), set(expected_names))
        self.assertEqual(links_string, expected_links_string)

        tags_names_from_request = []
        expected_names = []
        # request third(last) page
        answer_get = self.client.get(
            url_for('testtagsresource', access_token=self.token.access_token,
                    page=3, per_page=2),
            headers=[('Content-Type', 'application/json')])
        # check to ensure correct results
        tags_names_from_request = [x['name'] for x in answer_get.json]
        links_string = answer_get.headers['Link']
        # check if names of tags are the expected ones
        expected_names = []
        for i in range(5, 7):
            expected_name = tag_name_template.format(i)
            expected_names.append(expected_name)

        first_link = link_template.format(endpoint, 2, 1, "first")
        prev_link = link_template.format(endpoint, 2, 2, "prev")
        last_link = link_template.format(endpoint, 2, 3, "last")
        expected_links_string = "{0},{1},{2}".format(
            first_link,
            prev_link,
            last_link
        )

        self.assertEqual(set(tags_names_from_request), set(expected_names))
        self.assertEqual(links_string, expected_links_string)

        # delete created tags
        tags_api.delete_all_tags_from_user(self.user.id)

    def test_paginate_nonexistentpage(self):
        from invenio.ext.restful import errors
        answer_get = self.client.get(
            url_for('testtagsresource',
                    access_token=self.token.access_token,
                    page=-2),
            headers=[('Content-Type', 'application/json')])
        # Test/assert to see that the exceptions are raised correctly
        expected = {}
        expected['message'] = "Invalid page: {0}".format(-2)
        expected['type'] = "{0}".format(errors.InvalidPageError)
        self.assertEqual(answer_get.json, expected)

    def test_paginate_per_pageerror(self):
        from invenio.ext.restful import errors
        answer_get = self.client.get(
            url_for('testtagsresource',
                    access_token=self.token.access_token,
                    per_page=-5),
            headers=[('Content-Type', 'application/json')])
        # Test/assert to see that the exceptions are raised correctly
        expected = {}
        expected['message'] = "Invalid per_page: {0}".format(-5)
        expected['type'] = "{0}".format(errors.RestfulError)
        self.assertEqual(answer_get.json, expected)


TEST_SUITE = make_test_suite(DecoratorsTestCase, RestfulPaginationTestCase,
                             RestfulSQLAlchemyPaginationTestCase)


if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
