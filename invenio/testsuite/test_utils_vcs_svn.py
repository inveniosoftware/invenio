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

"""Unit tests for SVN interactions"""

__revision__ = "$Id$"

from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase
from invenio.base.globals import cfg
from invenio.utils.vcs.svn import harvest_repo
from invenio.utils.shell import which
from tempfile import mkdtemp
from subprocess import call
from shutil import rmtree
from os import chdir, path
import tarfile


class SVNHarvestTest(InvenioTestCase):
    """Test harvesting of SVN respo"""

    def setUp(self):

        from invenio.utils.vcs.svn import svn_exists, get_which_svn
        if not svn_exists():
            from unittest import SkipTest
            raise SkipTest("SVN not found. It probably needs installing.")

        self.which_svn = get_which_svn()

        self.svntest = mkdtemp(dir=cfg['CFG_TMPDIR'])
        self.repo = path.join(self.svntest, 'temprepo', '')
        self.src = path.join(self.svntest, 'tempsrc', '')
        self.archive_dir = path.join(mkdtemp(dir=cfg['CFG_TMPDIR']), '')
        self.archive_path = path.join(self.archive_dir, 'test.tar.gz')

        chdir(self.svntest)
        call([which('svnadmin'), '--fs-type', 'fsfs', 'create', self.repo])
        call([self.which_svn, 'co', 'file://' + self.repo, self.src])
        chdir(self.src)
        call([self.which_svn, 'mkdir', 'trunk', 'tags', 'branches'])
        call([self.which_svn, 'commit', '-m', "'Initial import'"])
        chdir(self.svntest)
        chdir(self.src + 'trunk')
        call(['touch', 'test.txt'])
        call([self.which_svn, 'add', 'test.txt'])
        call([self.which_svn, 'commit', '-m', "'test.txt added'"])
        call([self.which_svn, 'copy', 'file://' + self.repo + 'trunk',
              'file://' + self.repo + 'tags/release-1', '-m', "'release1"])
        chdir(self.src + 'trunk')
        call([self.which_svn, 'update'])
        call(['touch', 'test2.txt'])
        call([self.which_svn, 'add', 'test2.txt'])
        call([self.which_svn, 'commit', '-m', "'2nd version'"])
        call([self.which_svn, 'copy', 'file://' + self.repo + 'trunk',
              'file://' + self.repo + 'tags/release-2', '-m', "'release2"])

    def tearDown(self):
        rmtree(self.svntest)

    def test_harvest_with_tag_1(self):
        """Test harvesting of tag release-1"""
        harvest_repo('file://' + self.repo, self.archive_path, tag="release-1")
        fs_list = tarfile.open(self.archive_path).getnames()
        self.assertTrue('test.txt' in fs_list)
        self.assertFalse('test2.txt' in fs_list)

    def test_harvest_with_tag_2(self):
        """Test harvesting of tag release-2"""
        harvest_repo('file://' + self.repo, self.archive_path, tag="release-2")
        fs_list = tarfile.open(self.archive_path).getnames()
        self.assertTrue('test.txt' in fs_list)
        self.assertTrue('test2.txt' in fs_list)

    def test_harvest_without_tag(self):
        """Test harvesting of HEAD"""
        harvest_repo('file://' + self.repo, self.archive_path)
        fs_list = tarfile.open(self.archive_path).getnames()
        self.assertTrue('test.txt' in fs_list)
        self.assertTrue('test2.txt' in fs_list)

TEST_SUITE = make_test_suite(SVNHarvestTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
