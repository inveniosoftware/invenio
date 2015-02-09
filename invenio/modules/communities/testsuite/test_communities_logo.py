# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2014, 2015 CERN.
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

"""Tests for communities logo."""

import os
import shutil
import tempfile

from invenio.base.globals import cfg
from invenio.base.wrappers import lazy_import
from invenio.testsuite import InvenioTestCase, \
    make_test_suite, \
    run_test_suite

from ..helpers import save_and_validate_logo

Community = lazy_import('invenio.modules.communities.models:Community')


class CommunityLogoTest(InvenioTestCase):

    test_name = "test_logo"
    test_name_2 = "test_logo_2"

    def setUp(self):
        """Method called to prepare the test fixture."""
        self.TEST_DIR = tempfile.mkdtemp(dir=cfg['CFG_TMPDIR'])
        self.STATIC_ROOT = cfg['COLLECT_STATIC_ROOT']
        cfg['COLLECT_STATIC_ROOT'] = self.TEST_DIR

    def tearDown(self):
        """Method called to prepare the test fixture."""
        cfg['COLLECT_STATIC_ROOT'] = self.STATIC_ROOT
        shutil.rmtree(self.TEST_DIR)

    def test_1_accept_restricted_set_of_formats(self):
        """Should allow only restircted set of extenions."""
        unsupported_ext = ".gif"
        fp = tempfile.NamedTemporaryFile(
            dir=self.TEST_DIR, suffix=unsupported_ext, delete=False)
        fp.write('TEST')
        fp.seek(0)

        def logo():
            pass
        logo.filename = fp.name
        logo.stream = fp
        result = save_and_validate_logo(logo, self.test_name)
        self.assertEqual(None, result)

        supported_ext = cfg['COMMUNITIES_LOGO_EXTENSIONS'][-1]
        fp = tempfile.NamedTemporaryFile(
            dir=self.TEST_DIR, suffix=supported_ext, delete=False)
        fp.write('TEST')
        fp.seek(0)

        def logo():
            pass
        logo.filename = fp.name
        logo.stream = fp
        result = save_and_validate_logo(logo, self.test_name)
        self.assertEqual(supported_ext, result)

    def test_2_accept_restricted_limit_size_new(self):
        """Should accept only limited size. Case - new upload."""
        supported_ext = cfg['COMMUNITIES_LOGO_EXTENSIONS'][-1]
        fp = tempfile.NamedTemporaryFile(
            dir=self.TEST_DIR, suffix=supported_ext, delete=False)
        fp.write('TEST' * 1024 * 256 * 10)
        fp.seek(0)

        def logo():
            pass
        logo.filename = fp.name
        logo.stream = fp
        result = save_and_validate_logo(logo, self.test_name)
        self.assertEqual(None, result)

        fp = tempfile.NamedTemporaryFile(
            dir=self.TEST_DIR, suffix=supported_ext, delete=False)
        fp.write('TEST')
        fp.seek(0)

        def logo():
            pass
        logo.filename = fp.name
        logo.stream = fp
        result = save_and_validate_logo(logo, self.test_name_2)
        self.assertEqual(supported_ext, result)

    def test_3_accept_restricted_limit_size_edit_same_ext(self):
        """Should accept only limited size. Case - existing and same ext.
           Old logo file should remaing unchanged."""
        supported_ext = cfg['COMMUNITIES_LOGO_EXTENSIONS'][-1]
        fp = tempfile.NamedTemporaryFile(
            dir=self.TEST_DIR, suffix=supported_ext, delete=False)
        fp.write('OLD')
        fp.seek(0)

        def logo():
            pass
        logo.filename = fp.name
        logo.stream = fp
        result = save_and_validate_logo(logo, self.test_name)
        self.assertEqual(supported_ext, result)

        fp2 = tempfile.NamedTemporaryFile(
            dir=self.TEST_DIR, suffix=supported_ext, delete=False)
        fp2.write('TEST' * 1024 * 256 * 10)
        fp2.seek(0)

        def logo():
            pass
        logo.filename = fp2.name
        logo.stream = fp2
        result = save_and_validate_logo(logo, self.test_name, supported_ext)
        self.assertEqual(None, result)

        path_to_verify = os.path.join(
            cfg['COLLECT_STATIC_ROOT'],
            'user', self.test_name + supported_ext)
        self.assertEqual(True, os.path.isfile(path_to_verify))
        with open(path_to_verify, "rb") as f:
            content = f.read()
            self.assertEqual('OLD', content)

    def test_4_accept_restricted_limit_size_edit_dff_ext(self):
        """Should accept only limited size. Case - existing and diff ext.
           Old logo file should remaing unchanged."""
        supported_ext = cfg['COMMUNITIES_LOGO_EXTENSIONS'][-1]
        fp = tempfile.NamedTemporaryFile(
            dir=self.TEST_DIR, suffix=supported_ext, delete=False)
        fp.write('OLD')
        fp.seek(0)

        def logo():
            pass
        logo.filename = fp.name
        logo.stream = fp
        result = save_and_validate_logo(logo, self.test_name)
        self.assertEqual(supported_ext, result)

        supported_ext_2 = cfg['COMMUNITIES_LOGO_EXTENSIONS'][-2]
        fp2 = tempfile.NamedTemporaryFile(
            dir=self.TEST_DIR, suffix=supported_ext_2, delete=False)
        fp2.write('TEST' * 1024 * 256 * 10)
        fp2.seek(0)

        def logo():
            pass
        logo.filename = fp2.name
        logo.stream = fp2
        result = save_and_validate_logo(logo, self.test_name, supported_ext)
        self.assertEqual(None, result)

        path_to_verify = os.path.join(
            cfg['COLLECT_STATIC_ROOT'],
            'user', self.test_name + supported_ext)
        self.assertEqual(True, os.path.isfile(path_to_verify))
        with open(path_to_verify, "rb") as f:
            content = f.read()
            self.assertEqual('OLD', content)

    def test_5_update_same_ext(self):
        """Should properly replace the old logo with the valid new.
           Case - same extensions."""
        supported_ext = cfg['COMMUNITIES_LOGO_EXTENSIONS'][-1]
        fp = tempfile.NamedTemporaryFile(
            dir=self.TEST_DIR, suffix=supported_ext, delete=False)
        fp.write('OLD')
        fp.seek(0)

        def logo():
            pass
        logo.filename = fp.name
        logo.stream = fp
        result = save_and_validate_logo(logo, self.test_name)
        self.assertEqual(supported_ext, result)

        fp2 = tempfile.NamedTemporaryFile(
            dir=self.TEST_DIR, suffix=supported_ext, delete=False)
        fp2.write('NEW')
        fp2.seek(0)

        def logo():
            pass
        logo.filename = fp2.name
        logo.stream = fp2
        result = save_and_validate_logo(logo, self.test_name, supported_ext)
        self.assertEqual(supported_ext, result)

        path_to_verify = os.path.join(
            cfg['COLLECT_STATIC_ROOT'],
            'user', self.test_name + supported_ext)
        self.assertEqual(True, os.path.isfile(path_to_verify))
        with open(path_to_verify, "rb") as f:
            content = f.read()
            self.assertEqual('NEW', content)

    def test_6_update_diff_ext(self):
        """Should properly replace the old logo with the valid new.
           Case - diff extensions."""
        supported_ext = cfg['COMMUNITIES_LOGO_EXTENSIONS'][-1]
        fp = tempfile.NamedTemporaryFile(
            dir=self.TEST_DIR, suffix=supported_ext, delete=False)
        fp.write('OLD')
        fp.seek(0)

        def logo():
            pass
        logo.filename = fp.name
        logo.stream = fp
        result = save_and_validate_logo(logo, self.test_name)
        self.assertEqual(supported_ext, result)

        supported_ext_2 = cfg['COMMUNITIES_LOGO_EXTENSIONS'][-2]
        fp2 = tempfile.NamedTemporaryFile(
            dir=self.TEST_DIR, suffix=supported_ext_2, delete=False)
        fp2.write('NEW')
        fp2.seek(0)

        def logo():
            pass
        logo.filename = fp2.name
        logo.stream = fp2
        result = save_and_validate_logo(logo, self.test_name, supported_ext)
        self.assertEqual(supported_ext_2, result)

        path_to_verify = os.path.join(
            cfg['COLLECT_STATIC_ROOT'],
            'user', self.test_name + supported_ext_2)
        self.assertEqual(True, os.path.isfile(path_to_verify))
        with open(path_to_verify, "rb") as f:
            content = f.read()
            self.assertEqual('NEW', content)

TEST_SUITE = make_test_suite(CommunityLogoTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
