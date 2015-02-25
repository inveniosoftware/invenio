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

import json
from flask import url_for
from flask_registry import RegistryError
from invenio.testsuite import InvenioTestCase, make_test_suite, run_test_suite


from ..models import Event, Receiver, InvalidPayload, CeleryReceiver, \
    ReceiverDoesNotExists, InvalidSignature
from ..signatures import get_hmac

from invenio.celery import celery


class ReceiverTestCase(InvenioTestCase):
    def setUp(self):
        self.called = 0
        self.payload = None
        self.user_id = None
        # Force synchronously task running
        celery.conf['CELERY_ALWAYS_EAGER'] = True

        @celery.task(ignore_result=True)
        def test_task(event_state):
            e = Event()
            e.__setstate__(event_state)
            self.called += 1
            self.payload = e.payload
            self.user_id = e.user_id

        self.task_callable = test_task

    def tearDown(self):
        self.called = None
        self.payload = None
        self.user_id = None

    def callable(self, event):
        self.called += 1
        self.payload = event.payload
        self.user_id = event.user_id

    def callable_wrong_signature(self):
        self.called += 1

    def test_receiver_registration(self):
        r = Receiver(self.callable)
        r_invalid = Receiver(self.callable_wrong_signature)

        Receiver.register('test-receiver', r)
        Receiver.register('test-invalid', r_invalid)

        assert 'test-receiver' in Receiver.all()
        assert Receiver.get('test-receiver') == r

        # Double registration
        self.assertRaises(RegistryError, Receiver.register, 'test-receiver', r)

        Receiver.unregister('test-receiver')
        assert 'test-receiver' not in Receiver.all()

        Receiver.register('test-receiver', r)

        # JSON payload parsing
        payload = json.dumps(dict(somekey='somevalue'))
        headers = [('Content-Type', 'application/json')]
        with self.app.test_request_context(headers=headers, data=payload):
            r.consume_event(2)
            assert self.called == 1
            assert self.payload == json.loads(payload)
            assert self.user_id == 2

            self.assertRaises(TypeError, r_invalid.consume_event, 2)
            assert self.called == 1

        # Form encoded values payload parsing
        payload = dict(somekey='somevalue')
        with self.app.test_request_context(method='POST', data=payload):
            r.consume_event(2)
            assert self.called == 2
            assert self.payload == dict(somekey=['somevalue'])

        # Test invalid post data
        with self.app.test_request_context(method='POST', data="invaliddata"):
            self.assertRaises(InvalidPayload, r.consume_event, 2)

        # Test Celery Receiver
        rcelery = CeleryReceiver(self.task_callable)
        CeleryReceiver.register('celery-receiver', rcelery)

        # Form encoded values payload parsing
        payload = dict(somekey='somevalue')
        with self.app.test_request_context(method='POST', data=payload):
            rcelery.consume_event(1)

        assert self.called == 3
        assert self.payload == dict(somekey=['somevalue'])
        assert self.user_id == 1

    def test_unknown_receiver(self):
        self.assertRaises(ReceiverDoesNotExists, Receiver.get, 'unknown')

    def test_hookurl(self):
        r = Receiver(self.callable)
        Receiver.register('test-receiver', r)

        self.assertEqual(
            Receiver.get_hook_url('test-receiver', 'token'),
            url_for(
                'receivereventlistresource',
                receiver_id='test-receiver',
                access_token='token',
                _external=True
            )
        )

        self.app.config['WEBHOOKS_DEBUG_RECEIVER_URLS'] = {
            'test-receiver': 'http://test.local/?access_token=%(token)s'
        }

        self.assertEqual(
            Receiver.get_hook_url('test-receiver', 'token'),
            'http://test.local/?access_token=token'
        )

    def test_signature_checking(self):
        """
        webhooks - checks signatures for payload
        """
        r = Receiver(self.callable, signature='X-Hub-Signature')
        Receiver.register('test-receiver-sign', r)

        # check correct signature
        payload = json.dumps(dict(somekey='somevalue'))
        headers = [('Content-Type', 'application/json'),
                   ('X-Hub-Signature', get_hmac(payload))]
        with self.app.test_request_context(headers=headers, data=payload):
            r.consume_event(2)
            assert self.payload == json.loads(payload)

        # check signature with prefix
        headers = [('Content-Type', 'application/json'),
                   ('X-Hub-Signature', 'sha1=' + get_hmac(payload))]
        with self.app.test_request_context(headers=headers, data=payload):
            r.consume_event(2)
            assert self.payload == json.loads(payload)

        # check incorrect signature
        headers = [('Content-Type', 'application/json'),
                   ('X-Hub-Signature', get_hmac("somevalue"))]
        with self.app.test_request_context(headers=headers, data=payload):
            self.assertRaises(InvalidSignature, r.consume_event, 2)


TEST_SUITE = make_test_suite(ReceiverTestCase)


if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
