# -*- coding: utf-8 -*-
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
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.A

"""Test invenio.base.scripts.config."""

import os
import sys
import mock
import tempfile

from flask import current_app
from invenio.base.wrappers import lazy_import
from invenio.testsuite import make_test_suite, InvenioTestCase

config = lazy_import("invenio.base.scripts.config")


class TestConfig(InvenioTestCase):

    """Testing the config command utility."""

    def setUp(self):
        """Set up default configuration file."""
        fp, self._tmp = tempfile.mkstemp(dir=current_app.instance_path,
                                         text=True)
        os.write(fp, """SECRET_KEY = "53Cr37 k3Y"
DEBUG = True
""")
        os.close(fp)
        self.cfg = os.path.basename(self._tmp)

    def tearDown(self):
        """Remove default configuration file."""
        os.unlink(self._tmp)

    def test_set_true(self):
        """Test setting a True value."""
        with current_app.app_context():
            config.set_("SPAM", "True", self.cfg)

        with open(self._tmp) as f:
            self.assertRegexpMatches(f.read(), "SPAM\s*=\s*True")

    def test_set_false(self):
        """Test setting a False value."""
        with current_app.app_context():
            config.set_("EGGS", "False", self.cfg)

        with open(self._tmp) as f:
            self.assertRegexpMatches(f.read(), "EGGS\s*=\s*False")

    def test_set_unicode(self):
        """Test setting a unicode string."""
        with current_app.app_context():
            config.set_("URL", u"http://тест.укр/", self.cfg)

        with open(self._tmp) as f:
            self.assertRegexpMatches(f.read(), u"URL\s*=\s*u'http://\\\\u")

    def test_set_explicit_unicode(self):
        """Test setting an explicit unicode string (u + quotes)."""
        with current_app.app_context():
            config.set_("URL", u"u'http://тест.укр/'", self.cfg)

        with open(self._tmp) as f:
            self.assertRegexpMatches(f.read(), u"URL\s*=\s*u'http://\\\\u")

    def test_set_list_of_strings(self):
        """Test setting a list of string."""
        with current_app.app_context():
            config.set_("FOO", "['bar', 'biz']", self.cfg)

        with open(self._tmp) as f:
            self.assertRegexpMatches(f.read(), "FOO\s*=\s*\['bar',\s?'biz'\]")

    def test_set_list_of_lists(self):
        """Test setting a list with sublists."""
        with current_app.app_context():
            config.set_("FOO", "['bar', 'biz', [1, 2, 3]]", self.cfg)

        with open(self._tmp) as f:
            self.assertRegexpMatches(f.read(),
                                     "FOO\s*=\s*\['bar', 'biz', \[1, 2, 3\]\]")

    def test_set_existing(self):
        """Test setting existing entry fails."""
        def exit(*args, **kwargs):
            pass
        _stdout = sys.stdout
        _exit = sys.exit
        sys.stdout = config.StringIO()
        sys.exit = exit

        with current_app.app_context():
            config.set_("DEBUG", "False", self.cfg)

        self.assertRegexpMatches(sys.stdout.getvalue(),
                                 "DEBUG is already filled")

        sys.exit = _exit
        sys.stdout = _stdout

    def test_update_true_to_false(self):
        """Test updating an existing value from True to False."""
        _stdout = sys.stdout
        sys.stdout = config.StringIO()

        side_effect = [
            '',  # CFG_DATABASE_HOST
            '',  # CFG_DATABASE_NAME
            '',  # CFG_DATABASE_PASS
            '',  # CFG_DATABASE_PORT
            '',  # CFG_DATABASE_SLAVE
            '',  # CFG_DATABASE_TYPE
            '',  # CFG_DATABASE_USER
            'False',  # DEBUG
            '',  # SECRET_KEY
        ]
        with mock.patch('__builtin__.raw_input', side_effect=side_effect):
            config.update(self.cfg)

        with open(self._tmp) as f:
            self.assertRegexpMatches(f.read(), "DEBUG\s*=\s*False")

        sys.stdout = _stdout


TEST_SUITE = make_test_suite(TestConfig)
