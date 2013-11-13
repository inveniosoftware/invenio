# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012 CERN.
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

# pylint: disable=C0301

"""Regression tests for the BatchUploader."""

from invenio.testutils import InvenioTestCase
import os
import os.path
import urllib2
import urlparse
import socket
from urllib import urlencode

from invenio.testsuite import make_test_suite, run_test_suite
from invenio.legacy.dbquery import run_sql
from invenio.utils.json import json
from invenio.config import CFG_DEVEL_SITE, CFG_SITE_URL, CFG_TMPDIR, CFG_BINDIR
from invenio.bibsched import get_last_taskid, delete_task
from invenio.shellutils import run_shell_command
from invenio.bibupload_regression_tests import GenericBibUploadTest
from invenio.utils.url import make_user_agent_string

CFG_HAS_CURL = os.path.exists("/usr/bin/curl")

## NOTE: default invenio.conf authorization are granted only to 127.0.0.1
## or 127.0.1.1, a.k.a. localhost, so the following checks if the current host
## is well recognized as localhost. Otherwise disable tests since they would
## fail due to not enough authorizations.
CFG_LOCALHOST_OK = socket.gethostbyname(urlparse.urlparse(CFG_SITE_URL)[1].split(':')[0]) in ('127.0.0.1', '127.0.1.1')

class BatchUploaderRobotUploadTests(GenericBibUploadTest):
    """
    Testing Class for robotupload
    """
    def setUp(self):
        GenericBibUploadTest.setUp(self)
        self.callback_result_path = os.path.join(CFG_TMPDIR, 'robotupload.json')
        self.callback_url = CFG_SITE_URL + '/httptest/post2?%s' % urlencode({
                    "save": self.callback_result_path})
        self.oracle_callback_url = CFG_SITE_URL + '/httptest/oraclefriendly?%s' % urlencode({
                    "save": self.callback_result_path})
        if os.path.exists(self.callback_result_path):
            os.remove(self.callback_result_path)
        self.last_taskid = get_last_taskid()
        self.marcxml = """\
<record>
  <datafield tag="100" ind1=" " ind2=" ">
    <subfield code="a">Doe, John</subfield>
  </datafield>
  <datafield tag="245" ind1=" " ind2=" ">
    <subfield code="a">The title</subfield>
  </datafield>
  <datafield tag="980" ind1=" " ind2=" ">
    <subfield code="a">TEST</subfield>
  </datafield>
</record>"""
        self.req = urllib2.Request(CFG_SITE_URL + '/batchuploader/robotupload/insert')
        self.req.add_header('Content-Type', 'application/marcxml+xml')
        self.req.add_header('User-Agent', make_user_agent_string('BatchUploader'))
        self.req.add_data(self.marcxml)
        self.req_callback = urllib2.Request(CFG_SITE_URL + '/batchuploader/robotupload/insert?' + urlencode({
                'callback_url': self.callback_url}))
        self.req_callback.add_header('Content-Type', 'application/marcxml+xml')
        self.req_callback.add_header('User-Agent', 'invenio_webupload')
        self.req_callback.add_data(self.marcxml)
        self.nonce_url = CFG_SITE_URL + '/batchuploader/robotupload/insert?' + urlencode({
                'nonce': "1234",
                'callback_url': self.callback_url})
        self.req_nonce = urllib2.Request(self.nonce_url)
        self.req_nonce.add_header('Content-Type', 'application/marcxml+xml')
        self.req_nonce.add_header('User-Agent', 'invenio_webupload')
        self.req_nonce.add_data(self.marcxml)
        self.oracle_url = CFG_SITE_URL + '/batchuploader/robotupload/insert?' + urlencode({
                'special_treatment': 'oracle',
                'callback_url': self.oracle_callback_url})
        self.req_oracle = urllib2.Request(self.oracle_url)
        self.req_oracle.add_header('Content-Type', 'application/marcxml+xml')
        self.req_oracle.add_header('User-Agent', 'invenio_webupload')
        self.req_oracle.add_data(self.marcxml)
        self.legacy_url = CFG_SITE_URL + '/batchuploader/robotupload'

    def tearDown(self):
        GenericBibUploadTest.tearDown(self)
        if os.path.exists(self.callback_result_path):
            os.remove(self.callback_result_path)
        current_task = get_last_taskid()
        if current_task != self.last_taskid:
            delete_task(current_task)

    if CFG_LOCALHOST_OK:
        def test_bad_marcxml(self):
            """batchuploader - robotupload bad MARCXML"""
            self.req.add_data("BLABLA")
            result = urllib2.urlopen(self.req).read()
            self.assertEqual(result, "[ERROR] MARCXML is not valid.\n")

    if CFG_LOCALHOST_OK:
        def test_bad_agent(self):
            """batchuploader - robotupload bad agent"""
            self.req.add_header('User-Agent', 'badagent')
            result = urllib2.urlopen(self.req).read()
            self.assertEqual(result, "[ERROR] Sorry, the badagent useragent cannot use the service.\n")

    if CFG_LOCALHOST_OK:
        def test_simple_insert(self):
            """batchuploader - robotupload simple insert"""
            from invenio.search_engine import get_record
            result = urllib2.urlopen(self.req).read()
            self.failUnless("[INFO]" in result)
            current_task = get_last_taskid()
            run_shell_command("%s/bibupload %%s" % CFG_BINDIR, [str(current_task)])
            current_recid = run_sql("SELECT MAX(id) FROM bibrec")[0][0]
            self.failIfEqual(self.last_recid, current_recid)
            record = get_record(current_recid)
            self.assertEqual(record['245'][0][0], [('a', 'The title')])

    if CFG_DEVEL_SITE and CFG_LOCALHOST_OK:
        ## This expect a particular testing web handler that is available
        ## only when CFG_DEVEL_SITE is set up correctly
        def test_insert_with_callback(self):
            """batchuploader - robotupload insert with callback"""
            result = urllib2.urlopen(self.req_callback).read()
            self.failUnless("[INFO]" in result, '"%s" did not contained [INFO]' % result)
            current_task = get_last_taskid()
            run_shell_command("%s/bibupload %%s" % CFG_BINDIR, [str(current_task)])
            results = json.loads(open(self.callback_result_path).read())
            self.failUnless('results' in results)
            self.assertEqual(len(results['results']), 1)
            self.failUnless(results['results'][0]['success'])
            self.failUnless(results['results'][0]['recid'] > 0)
            self.failUnless("""<subfield code="a">Doe, John</subfield>""" in results['results'][0]['marcxml'], results['results'][0]['marcxml'])

        def test_insert_with_nonce(self):
            """batchuploader - robotupload insert with nonce"""
            result = urllib2.urlopen(self.req_nonce).read()
            self.failUnless("[INFO]" in result, '"%s" did not contained "[INFO]"' % result)
            current_task = get_last_taskid()
            run_shell_command("%s/bibupload %%s" % CFG_BINDIR, [str(current_task)])
            results = json.loads(open(self.callback_result_path).read())
            self.failUnless('results' in results, '"%s" did not contained "results" key' % results)
            self.assertEqual(len(results['results']), 1)
            self.assertEqual(results['nonce'], "1234")
            self.failUnless(results['results'][0]['success'])
            self.failUnless(results['results'][0]['recid'] > 0)
            self.failUnless("""<subfield code="a">Doe, John</subfield>""" in results['results'][0]['marcxml'], results['results'][0]['marcxml'])

        def test_insert_with_oracle(self):
            """batchuploader - robotupload insert with oracle special treatment"""
            import os
            if os.path.exists('/opt/invenio/var/log/invenio.err'):
                os.remove('/opt/invenio/var/log/invenio.err')
            result = urllib2.urlopen(self.req_oracle).read()
            self.failUnless("[INFO]" in result, '"%s" did not contained "[INFO]"' % result)
            current_task = get_last_taskid()
            run_shell_command("%s/bibupload %%s" % CFG_BINDIR, [str(current_task)])
            results = json.loads(open(self.callback_result_path).read())
            self.failUnless('results' in results, '"%s" did not contained "results" key' % results)
            self.assertEqual(len(results['results']), 1)
            self.failUnless(results['results'][0]['success'])
            self.failUnless(results['results'][0]['recid'] > 0)
            self.failUnless("""<subfield code="a">Doe, John</subfield>""" in results['results'][0]['marcxml'], results['results'][0]['marcxml'])

        if CFG_HAS_CURL:
            def test_insert_via_curl(self):
                """batchuploader - robotupload insert via CLI curl"""
                curl_input_file = os.path.join(CFG_TMPDIR, 'curl_test.xml')
                open(curl_input_file, "w").write(self.marcxml)
                try:
                    result = run_shell_command('/usr/bin/curl -T %s %s -A %s -H "Content-Type: application/marcxml+xml"', [curl_input_file, self.nonce_url, make_user_agent_string('BatchUploader')])[1]
                    self.failUnless("[INFO]" in result)
                    current_task = get_last_taskid()
                    run_shell_command("%s/bibupload %%s" % CFG_BINDIR, [str(current_task)])
                    results = json.loads(open(self.callback_result_path).read())
                    self.failUnless('results' in results, '"%s" did not contained [INFO]' % result)
                    self.assertEqual(len(results['results']), 1)
                    self.assertEqual(results['nonce'], "1234")
                    self.failUnless(results['results'][0]['success'])
                    self.failUnless(results['results'][0]['recid'] > 0)
                    self.failUnless("""<subfield code="a">Doe, John</subfield>""" in results['results'][0]['marcxml'], results['results'][0]['marcxml'])
                finally:
                    os.remove(curl_input_file)

            def test_legacy_insert_via_curl(self):
                """batchuploader - robotupload legacy insert via CLI curl"""
                curl_input_file = os.path.join(CFG_TMPDIR, 'curl_test.xml')
                open(curl_input_file, "w").write(self.marcxml)
                try:
                    ## curl -F 'file=@localfile.xml' -F 'mode=-i' [-F 'callback_url=http://...'] [-F 'nonce=1234'] http://cds.cern.ch/batchuploader/robotupload -A invenio_webupload
                    code, result, err = run_shell_command("/usr/bin/curl -v -F file=@%s -F 'mode=-i' -F callback_url=%s -F nonce=1234 %s -A %s", [curl_input_file, self.callback_url, self.legacy_url, make_user_agent_string('BatchUploader')])
                    self.failUnless("[INFO]" in result, '[INFO] not find in results: %s, %s' % (result, err))
                    current_task = get_last_taskid()
                    run_shell_command("%s/bibupload %%s" % CFG_BINDIR, [str(current_task)])
                    results = json.loads(open(self.callback_result_path).read())
                    self.failUnless('results' in results, '"%s" did not contained [INFO]' % result)
                    self.assertEqual(len(results['results']), 1)
                    self.assertEqual(results['nonce'], "1234")
                    self.failUnless(results['results'][0]['success'])
                    self.failUnless(results['results'][0]['recid'] > 0)
                    self.failUnless("""<subfield code="a">Doe, John</subfield>""" in results['results'][0]['marcxml'], results['results'][0]['marcxml'])
                finally:
                    os.remove(curl_input_file)


TEST_SUITE = make_test_suite(BatchUploaderRobotUploadTests)


if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)
