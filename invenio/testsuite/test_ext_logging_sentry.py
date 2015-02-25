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

""" Tests for Sentry sensitive data sanitation. """

from mock import Mock
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase

from invenio.ext.logging.backends.sentry import InvenioSanitizeProcessor

VARS = {
    'foo': 'bar',
    'password': 'hello',
    'access_token': 'hello',
}


class InvenioSantizeProcessorTest(InvenioTestCase):
    def _check_vars_sanitized(self, vars, proc):
        """ Helper to check that keys have been sanitized. """
        self.assertTrue('foo' in vars)
        self.assertEquals(vars['foo'], 'bar')
        # Raven default processor takes care of this one
        self.assertTrue('password' in vars)
        self.assertEquals(vars['password'], 'hello')
        self.assertTrue('access_token' in vars)
        self.assertEquals(vars['access_token'], proc.MASK)

    def test_http(self):
        data = {
            'request': {
                'data': VARS,
                'env': VARS,
                'headers': VARS,
                'cookies': VARS,
            }
        }

        proc = InvenioSanitizeProcessor(Mock())
        result = proc.process(data)

        self.assertTrue('request' in result)
        http = result['request']
        for n in ('data', 'env', 'headers', 'cookies'):
            self.assertTrue(n in http)
            self._check_vars_sanitized(http[n], proc)

    def test_querystring_as_string(self):
        data = {
            'request': {
                'query_string': 'foo=bar&password=hello&access_token=hello',
            }
        }

        proc = InvenioSanitizeProcessor(Mock())
        result = proc.process(data)

        self.assertTrue('request' in result)
        http = result['request']
        self.assertEquals(
            http['query_string'],
            'foo=bar&password=hello&access_token=%(m)s' % dict(m=proc.MASK)
        )


TEST_SUITE = make_test_suite(InvenioSantizeProcessorTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
