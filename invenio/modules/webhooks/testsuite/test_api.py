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

from __future__ import absolute_import


from invenio.testsuite import make_test_suite, run_test_suite
from invenio.ext.sqlalchemy import db
from invenio.ext.restful.utils import APITestCase

from ..models import Receiver


class WebHooksTestCase(APITestCase):
    def setUp(self):
        from invenio.modules.accounts.models import User
        self.user = User(
            email='info@invenio-software.org', nickname='tester'
        )
        self.user.password = "tester"
        db.session.add(self.user)
        db.session.commit()
        self.create_oauth_token(self.user.id, scopes=["webhooks:event"])

        self.called = 0
        self.payload = None
        self.user_id = None

    def tearDown(self):
        self.remove_oauth_token()
        if self.user:
            db.session.delete(self.user)
            db.session.commit()

        self.called = None
        self.payload = None
        self.user_id = None

    def callable(self, event):
        self.called += 1
        self.payload = event.payload
        self.user_id = event.user_id

    def callable_wrong_signature(self):
        self.called += 1

    def test_405_methods(self):
        methods = [
            self.get, self.put, self.delete, self.head, self.options,
            self.patch
        ]

        for m in methods:
            m(
                'receivereventlistresource',
                urlargs=dict(receiver_id='test-receiver'),
                code=405,
            )

    def test_webhook_post(self):
        self.post(
            'receivereventlistresource',
            urlargs=dict(receiver_id='test-receiver'),
            code=404,
            user_id=self.user.id,
        )

        r = Receiver(self.callable)
        r_invalid = Receiver(self.callable_wrong_signature)

        Receiver.register('test-receiver', r)
        Receiver.register('test-broken-receiver', r_invalid)

        payload = dict(somekey='somevalue')
        self.post(
            'receivereventlistresource',
            urlargs=dict(receiver_id='test-receiver'),
            data=payload,
            code=202,
            user_id=self.user.id,
        )

        assert self.called == 1
        assert self.user_id == self.user.id
        assert self.payload == payload

        # Test invalid payload
        import pickle
        payload = dict(somekey='somevalue')
        self.post(
            'receivereventlistresource',
            urlargs=dict(receiver_id='test-receiver'),
            data=pickle.dumps(payload),
            is_json=False,
            headers=[('Content-Type', 'application/python-pickle')],
            code=415,
            user_id=self.user.id,
        )

        # Test invalid payload, with wrong content-type
        import pickle
        self.post(
            'receivereventlistresource',
            urlargs=dict(receiver_id='test-receiver'),
            data=pickle.dumps(payload),
            is_json=False,
            headers=[('Content-Type', 'application/json')],
            code=400,
            user_id=self.user.id,
        )


class WebHooksScopesTestCase(APITestCase):
    def setUp(self):
        from invenio.modules.accounts.models import User
        self.user = User(
            email='info@invenio-software.org', nickname='tester'
        )
        self.user.password = "tester"
        db.session.add(self.user)
        db.session.commit()
        self.create_oauth_token(self.user.id, scopes=[""])

    def tearDown(self):
        self.remove_oauth_token()
        if self.user:
            db.session.delete(self.user)
            db.session.commit()

    def callable(self, event):
        pass

    def test_405_methods_no_scope(self):
        methods = [
            self.get, self.put, self.delete, self.head, self.options,
            self.patch
        ]

        for m in methods:
            m(
                'receivereventlistresource',
                urlargs=dict(receiver_id='test-receiver'),
                code=405,
            )

    def test_webhook_post(self):
        r = Receiver(self.callable)
        Receiver.register('test-receiver-no-scope', r)

        payload = dict(somekey='somevalue')
        self.post(
            'receivereventlistresource',
            urlargs=dict(receiver_id='test-receiver-no-scope'),
            data=payload,
            code=403,
            user_id=self.user.id,
        )

TEST_SUITE = make_test_suite(WebHooksTestCase, WebHooksScopesTestCase)


if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
