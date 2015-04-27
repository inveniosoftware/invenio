# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2010, 2011, 2013, 2014, 2015 CERN.
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

"""Test suite for BibClassify module."""

import sys
import tempfile
import cStringIO
import os
import time
import stat
import shutil

from flask_registry import PkgResourcesDirDiscoveryRegistry, \
    ImportPathRegistry, RegistryProxy
from invenio.testsuite import make_test_suite, run_test_suite, nottest, \
    InvenioTestCase

TEST_PACKAGE = 'invenio.modules.classifier.testsuite'

test_registry = RegistryProxy('test_registry', ImportPathRegistry,
                              initial=[TEST_PACKAGE])

taxonomies_registry = lambda: PkgResourcesDirDiscoveryRegistry(
    'taxonomies', registry_namespace=test_registry)


class BibClassifyTestCase(InvenioTestCase):

    """ Abusive test suite - the one that takes sooooo long """

    def setUp(self):
        """Initialize stuff."""
        from invenio import config
        self.original_tmpdir = config.CFG_TMPDIR
        config.CFG_TMPDIR = tempfile.gettempdir()

        self.oldstdout = sys.stdout
        self.oldstderr = sys.stderr
        self.stdout = None
        self.stderr = None

        self.taxonomy_name = "test"
        from invenio.legacy.bibclassify import config as bconfig
        self.log = bconfig.get_logger("bibclassify.tests")
        self.log_level = bconfig.logging_level
        bconfig.set_global_level(bconfig.logging.CRITICAL)
        self.app.extensions['registry']['classifierext.taxonomies'] = \
            taxonomies_registry()

    def tearDown(self):
        from invenio import config
        config.CFG_TMPDIR = self.original_tmpdir
        if self.stdout:
            self.unredirect()
        from invenio.legacy.bibclassify import config as bconfig
        bconfig.set_global_level(self.log_level)

    def redirect(self):
        # just for debugging in Eclipse (to see messages printed)
        if 'stdout' in sys.argv:
            self.stdout = sys.stdout
            self.stderr = sys.stderr
        else:
            self.stdout = cStringIO.StringIO()
            self.stderr = cStringIO.StringIO()

        sys.stdout = self.stdout
        sys.stderr = self.stderr

    def unredirect(self):
        sin, serr = '', ''
        if self.stdout:
            self.stdout.flush()
            self.stdout.seek(0)
            sin = self.stdout.read()
            self.stderr.flush()
            self.stderr.seek(0)
            serr = self.stderr.read()

            self.stdout.close()
            self.stderr.close()
        self.stdout = None
        self.stderr = None
        sys.stdout = self.oldstdout
        sys.stderr = self.oldstderr

        return sin, serr

    @nottest
    def get_test_file(self, recid, type='Main', format='pdf'):

        from invenio.legacy.bibdocfile import api as bibdocfile
        br = bibdocfile.BibRecDocs(recid)
        bibdocs = br.list_bibdocs(type)
        # we grab the first
        for b in bibdocs:
            x = b.get_file(format)
            if x:
                return x.get_full_path(), x.get_url()


class BibClassifyTest(BibClassifyTestCase):

    def test_keywords(self):
        """"""


    def test_rebuild_cache(self):
        """bibclassify - test rebuilding cache (takes long time)"""
        from invenio.legacy.bibclassify import ontology_reader as bibclassify_ontology_reader
        info = bibclassify_ontology_reader._get_ontology(self.taxonomy_name)

        self.assertTrue(info[0])
        cache = bibclassify_ontology_reader._get_cache_path(info[0])

        if os.path.exists(cache):
            ctime = os.stat(cache)[stat.ST_CTIME]
        else:
            ctime = -1

        rex = bibclassify_ontology_reader.get_regular_expressions(
            self.taxonomy_name, rebuild=True)
        self.assertTrue(os.path.exists(cache))
        ntime = os.stat(cache)[stat.ST_CTIME]
        self.assertTrue((ntime > ctime))

        self.assertEqual(len(rex[0]) + len(rex[1]), 63)

    def test_cache_accessibility(self):
        """bibclassify - test cache accessibility/writability"""
        from flask import current_app
        from invenio.modules.classifier.registry import taxonomies
        from invenio.legacy.bibclassify import ontology_reader as bibclassify_ontology_reader
        # we will do tests with a copy of test taxonomy, in case anything goes
        # wrong...
        orig_name, orig_taxonomy_path, orig_taxonomy_url = bibclassify_ontology_reader._get_ontology(
            self.taxonomy_name)

        taxonomy_name = self.taxonomy_name + '.copy'
        taxonomy_path = os.path.join(
            current_app.config['CFG_TMPDIR'], taxonomy_name + '.rdf')

        shutil.copy(orig_taxonomy_path, taxonomy_path)
        taxonomies[taxonomy_name] = taxonomy_path
        assert(os.path.exists(taxonomy_path))

        name, taxonomy_path, taxonomy_url = bibclassify_ontology_reader._get_ontology(
            taxonomy_name)
        cache = bibclassify_ontology_reader._get_cache_path(
            os.path.basename(taxonomy_path))

        if not name:
            raise Exception("Taxonomy wasn't found")

        if os.path.exists(cache):
            os.remove(cache)

        bibclassify_ontology_reader.get_regular_expressions(
            taxonomy_name, rebuild=True, no_cache=False)
        assert(os.path.exists(cache))

        self.log.error('Testing corrupted states, please ignore errors...')

        # set cache unreadable
        os.chmod(cache, 000)
        try:
            bibclassify_ontology_reader.get_regular_expressions(
                taxonomy_name, rebuild=False, no_cache=False)
        except:
            pass
        else:
            raise Exception('cache chmod to 000 but no exception raised')

        # set cache unreadable and test writing
        os.chmod(cache, 000)
        try:
            bibclassify_ontology_reader.get_regular_expressions(
                taxonomy_name, rebuild=True, no_cache=False)
        except:
            pass
        else:
            raise Exception('cache chmod to 000 but no exception raised')

        # set cache unreadable but don't care for it
        os.chmod(cache, 000)
        bibclassify_ontology_reader.get_regular_expressions(
            taxonomy_name, rebuild=False, no_cache=True)
        bibclassify_ontology_reader.get_regular_expressions(
            taxonomy_name, rebuild=True, no_cache=True)

        # set cache readable and test writing
        os.chmod(cache, 600)
        try:
            bibclassify_ontology_reader.get_regular_expressions(
                taxonomy_name, rebuild=True, no_cache=False)
        except:
            pass
        else:
            raise Exception('cache chmod to 600 but no exception raised')

        # set cache writable only
        os.chmod(cache, 200)
        bibclassify_ontology_reader.get_regular_expressions(
            taxonomy_name, rebuild=True, no_cache=False)
        bibclassify_ontology_reader.get_regular_expressions(
            taxonomy_name, rebuild=False, no_cache=False)

        # set cache readable/writable but corrupted (must rebuild itself)
        os.chmod(cache, 600)
        os.remove(cache)
        open(cache, 'w').close()
        bibclassify_ontology_reader.get_regular_expressions(
            taxonomy_name, rebuild=False, no_cache=False)

        # set cache readable/writable but corrupted (must rebuild itself)
        open(cache, 'w').close()
        try:
            try:
                os.rename(taxonomy_path, taxonomy_path + 'x')
                open(taxonomy_path, 'w').close()
                bibclassify_ontology_reader.get_regular_expressions(
                    taxonomy_name, rebuild=False, no_cache=False)
            except:
                pass
        finally:
            os.rename(taxonomy_path + 'x', taxonomy_path)

        # make cache ok, but corrupt source
        bibclassify_ontology_reader.get_regular_expressions(
            taxonomy_name, rebuild=True, no_cache=False)

        try:
            try:
                os.rename(taxonomy_path, taxonomy_path + 'x')
                open(taxonomy_path, 'w').close()
                time.sleep(.1)
                # touch the taxonomy to be older
                os.utime(cache, (time.time() + 100, time.time() + 100))
                bibclassify_ontology_reader.get_regular_expressions(
                    taxonomy_name, rebuild=False, no_cache=False)
            except:
                os.rename(taxonomy_path + 'x', taxonomy_path)
                raise Exception('Cache exists and is ok, but was ignored')
        finally:
            os.rename(taxonomy_path + 'x', taxonomy_path)

        # make cache ok (but old), and corrupt source
        bibclassify_ontology_reader.get_regular_expressions(
            taxonomy_name, rebuild=True, no_cache=False)
        try:
            try:
                os.rename(taxonomy_path, taxonomy_path + 'x')
                open(taxonomy_path, 'w').close()
                bibclassify_ontology_reader.get_regular_expressions(
                    taxonomy_name, rebuild=False, no_cache=False)
            except:
                pass
        finally:
            os.rename(taxonomy_path + 'x', taxonomy_path)

        self.log.error('...testing of corrupted states finished.')

        name, taxonomy_path, taxonomy_url = bibclassify_ontology_reader._get_ontology(
            taxonomy_name)
        cache = bibclassify_ontology_reader._get_cache_path(name)
        os.remove(taxonomy_path)
        os.remove(cache)


TEST_SUITE = make_test_suite(BibClassifyTest)


if __name__ == '__main__':
    run_test_suite(TEST_SUITE)
