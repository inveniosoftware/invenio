# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.


from invenio.ext.restful.utils import APITestCase
from invenio.testsuite import make_test_suite, run_test_suite
from invenio.base.wrappers import lazy_import

db = lazy_import('invenio.ext.sqlalchemy.db')


class TestRecordsRestfulAPI(APITestCase):

    def setUp(self):
        """Run before each test."""
        from invenio.modules.accounts.models import User

        self.user_a = User(email='user_a@example.com', _password='iamusera',
                           nickname='user_a')
        try:
            db.session.add(self.user_a)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        self.create_oauth_token(self.user_a.id, scopes=[""])

    def tearDown(self):
        """Run after every test."""
        from invenio.modules.accounts.models import User

        self.remove_oauth_token()
        User.query.filter(User.nickname.in_([
            self.user_a.nickname,
        ])).delete(synchronize_session=False)
        db.session.commit()

    def test_405_methods_recordresource(self):
        """Test methods that return 405."""
        methods_405_recordresource = [self.patch, self.options, self.put,
                                      self.post, self.head]
        for m in methods_405_recordresource:
            m(
                'recordresource',
                user_id=self.user_a.id,
                is_json=False,
                urlargs=dict(record_id=1),
                code=405,
            )

    def test_get_record_marcxml(self):
        response = self.get(
            'recordresource',
            user_id=self.user_a.id,
            is_json=False,
            urlargs=dict(record_id=1),
            data='',
            headers=[('Accept', 'application/marcxml+xml')]
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'],
                         'application/marcxml+xml')

    def test_get_record_recjson(self):
        response = self.get(
            'recordresource',
            user_id=self.user_a.id,
            is_json=False,
            urlargs=dict(record_id=1),
            data='',
            headers=[('Accept', 'application/json')]
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'application/json')

    def test_unsupported_media_type(self):
        response = self.get(
            'recordresource',
            user_id=self.user_a.id,
            is_json=False,
            urlargs=dict(record_id=1),
            data='',
            headers=[('Accept', 'application/non-existent')]
        )
        self.assertEqual(response.status_code, 415)

    def test_get_records_list_marcxml(self):
        test_params = dict(
            query='Ellis',
            sort_field='title',
            sort_order='a',
            page=1,
            per_page=5
        )

        response = self.get(
            'recordlistresource',
            user_id=self.user_a.id,
            is_json=False,
            urlargs=test_params,
            data='',
            headers=[('Accept', 'application/marcxml+xml')]
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'],
                         'application/marcxml+xml')

    def test_get_records_list_recjson(self):
        test_params = dict(
            query='Ellis',
            sort_field='title',
            sort_order='a',
            page=1,
            per_page=5
        )

        response = self.get(
            'recordlistresource',
            user_id=self.user_a.id,
            is_json=False,
            urlargs=test_params,
            data='',
            headers=[('Accept', 'application/json')]
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'application/json')


TEST_SUITE = make_test_suite(TestRecordsRestfulAPI)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
