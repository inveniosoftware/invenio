# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2013 CERN.
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

"""Unit tests for the webinterface module."""

__revision__ = "$Id$"


import cgi
from invenio.base.wrappers import lazy_import
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase

# SLIPPERY SLOPE AHEAD
#
# Trick mod_python into believing there is already an _apache module
# available, which is used only for its parse_qs functions anyway.
#
# This must be done early, as many imports somehow end up importing
# apache in turn, which makes the trick useless.


class _FakeApache(object):

    SERVER_RETURN = 'RETURN'

    def __init__(self):
        self.table = None
        self.log_error = None
        self.table = None
        self.config_tree = None
        self.server_root = None
        self.mpm_query = lambda dummy: False
        self.exists_config_define = None
        self.stat = None
        self.AP_CONN_UNKNOWN = None
        self.AP_CONN_CLOSE = None
        self.AP_CONN_KEEPALIVE = None
        self.APR_NOFILE = None
        self.APR_REG = None
        self.APR_DIR = None
        self.APR_CHR = None
        self.APR_BLK = None
        self.APR_PIPE = None
        self.APR_LNK = None
        self.APR_SOCK = None
        self.APR_UNKFILE = None

    def parse_qs(self, *args, **kargs):
        return cgi.parse_qs(*args, **kargs)

    def parse_qsl(self, *args, **kargs):
        return cgi.parse_qsl(*args, **kargs)

class _FakeReq(object):

    def __init__(self, q):
        self.args = q
        self.method = "GET"
        return

FieldStorage = lazy_import('invenio.legacy.wsgi.utils:FieldStorage')
# --------------------------------------------------

webinterface_handler = lazy_import('invenio.ext.legacy.handler')


class TestWashArgs(InvenioTestCase):
    """webinterface - Test for washing of URL query arguments"""

    def _check(self, query, default, expected):
        req = _FakeReq(query)
        form = FieldStorage(req, keep_blank_values=True)
        result = webinterface_handler.wash_urlargd(form, default)

        if not 'ln' in expected:
            from invenio.config import CFG_SITE_LANG
            expected['ln'] = CFG_SITE_LANG

        self.failUnlessEqual(result, expected)

    def test_single_string(self):
        """ webinterface - check retrieval of a single string field """

        default = {'c': (str, 'default')}

        self._check('c=Test1', default, {'c': 'Test1'})
        self._check('d=Test1', default, {'c': 'default'})
        self._check('c=Test1&c=Test2', default, {'c': 'Test1'})

    def test_string_list(self):
        """ webinterface - check retrieval of a list of values """

        default = {'c': (list, ['default'])}

        self._check('c=Test1', default, {'c': ['Test1']})
        self._check('c=Test1&c=Test2', default, {'c': ['Test1', 'Test2']})
        self._check('d=Test1', default, {'c': ['default']})

    def test_int_casting(self):
        """ webinterface - check casting into an int. """

        default = {'jrec': (int, -1)}

        self._check('jrec=12', default, {'jrec': 12})
        self._check('jrec=', default, {'jrec': -1})
        self._check('jrec=foo', default, {'jrec': -1})
        self._check('jrec=foo&jrec=1', default, {'jrec': -1})
        self._check('jrec=12&jrec=foo', default, {'jrec': 12})


TEST_SUITE = make_test_suite(TestWashArgs,)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
