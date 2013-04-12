# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2010, 2011 CERN.
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
from invenio import web_api_key

"""Unit tests for REST like authentication API."""

try:
    import hashlib
except:
    pass
import unittest
import re
import hmac
import urllib
import time
import string

from invenio.testutils import make_test_suite, run_test_suite
from invenio.dbquery import run_sql

web_api_key.CFG_WEB_API_KEY_ALLOWED_URL = [('/search\?*', 0, True),
                                        ('/bad\?*', -1, True)] #Just for testing

web_api_key._CFG_WEB_API_KEY_ALLOWED_URL = [(re.compile(_url), _authorized_time, _need_timestamp)
        for _url, _authorized_time, _need_timestamp in web_api_key.CFG_WEB_API_KEY_ALLOWED_URL]

def build_web_request(path, params, api_key=None, secret_key=None):
    items = (hasattr(params, 'items') and [params.items()] or [list(params)])[0]
    if api_key:
        items.append(('apikey', api_key))
    if secret_key:
        items.append(('timestamp', str(int(time.time()))))
        items = sorted(items, key=lambda x: x[0].lower())
        url = '%s?%s' % (path, urllib.urlencode(items))
        signature = hmac.new(secret_key, url, hashlib.sha1).hexdigest()
        items.append(('signature', signature))
    if not items:
        return path
    return '%s?%s' % (path, urllib.urlencode(items))

class APIKeyTest(unittest.TestCase):
    """ Test functions related to the REST authentication API """
    def setUp(self):
        self.id_admin = run_sql('SELECT id FROM user WHERE nickname="admin"')[0][0]

    def test_create_remove_show_key(self):
        """apikey - create/list/delete REST key"""
        self.assertEqual(0, len(web_api_key.show_web_api_keys(uid=self.id_admin)))
        web_api_key.create_new_web_api_key(self.id_admin, "Test key I")
        web_api_key.create_new_web_api_key(self.id_admin, "Test key II")
        web_api_key.create_new_web_api_key(self.id_admin, "Test key III")
        web_api_key.create_new_web_api_key(self.id_admin, "Test key IV")
        web_api_key.create_new_web_api_key(self.id_admin, "Test key V")
        self.assertEqual(5, len(web_api_key.show_web_api_keys(uid=self.id_admin)))
        self.assertEqual(5, len(web_api_key.show_web_api_keys(uid=self.id_admin, diff_status='')))
        keys_info = web_api_key.show_web_api_keys(uid=self.id_admin)
        web_api_key.mark_web_api_key_as_removed(keys_info[0][0])
        self.assertEqual(4, len(web_api_key.show_web_api_keys(uid=self.id_admin)))
        self.assertEqual(5, len(web_api_key.show_web_api_keys(uid=self.id_admin, diff_status='')))

        run_sql("UPDATE webapikey SET status='WARNING' WHERE id=%s", (keys_info[1][0],))
        run_sql("UPDATE webapikey SET status='REVOKED' WHERE id=%s", (keys_info[2][0],))

        self.assertEqual(4, len(web_api_key.show_web_api_keys(uid=self.id_admin)))
        self.assertEqual(5, len(web_api_key.show_web_api_keys(uid=self.id_admin, diff_status='')))

        run_sql("DELETE FROM webapikey")

    def test_acc_get_uid_from_request(self):
        """webapikey - Login user from request using REST key"""
        path = '/search'
        params = 'ln=es&sc=1&c=Articles & Preprints&action_search=Buscar&p=ellis'

        self.assertEqual(0, len(web_api_key.show_web_api_keys(uid=self.id_admin)))
        web_api_key.create_new_web_api_key(self.id_admin, "Test key I")

        key_info = run_sql("SELECT id FROM webapikey WHERE id_user=%s", (self.id_admin,))
        url = web_api_key.build_web_request(path, params, api_key=key_info[0][0])
        url = string.split(url, '?')
        uid = web_api_key.acc_get_uid_from_request(url[0], url[1])
        self.assertEqual(uid, self.id_admin)

        url = web_api_key.build_web_request(path, params, api_key=key_info[0][0])
        url += "123" # corrupt the key
        url = string.split(url, '?')
        uid = web_api_key.acc_get_uid_from_request(url[0], url[1])
        self.assertEqual(uid, -1)

        path = '/bad'
        uid = web_api_key.acc_get_uid_from_request(path, "")
        self.assertEqual(uid, -1)
        params = {'nocache': 'yes', 'limit': 123}
        url = web_api_key.build_web_request(path, params, api_key=key_info[0][0])
        url = string.split(url, '?')
        uid = web_api_key.acc_get_uid_from_request(url[0], url[1])
        self.assertEqual(uid, -1)

        run_sql("DELETE FROM webapikey")

TEST_SUITE = make_test_suite(APIKeyTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
    run_sql("DELETE FROM webapikey")
