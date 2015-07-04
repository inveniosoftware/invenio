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

"""Test suite for classifier module."""

import os
import shutil
import stat
import time

from flask_registry import (
    ImportPathRegistry,
    PkgResourcesDirDiscoveryRegistry,
    RegistryProxy
)
from invenio.testsuite import (
    InvenioTestCase,
    make_test_suite,
    run_test_suite,
)

TEST_PACKAGE = 'invenio.modules.classifier.testsuite'

test_registry = RegistryProxy('test_registry', ImportPathRegistry,
                              initial=[TEST_PACKAGE])


def _get_test_taxonomies():
    return PkgResourcesDirDiscoveryRegistry(
        'taxonomies', registry_namespace=test_registry)


class ClassifierTestCase(InvenioTestCase):

    """Basic test class used for classifier tests."""

    def setUp(self):
        """Initialize stuff."""
        self.taxonomy_name = "test"
        self.app.extensions['registry']['classifierext.taxonomies'] = \
            _get_test_taxonomies()
        self.sample_text = """
        We study the three-dimensional effective action obtained by reducing
        eleven-dimensional supergravity with higher-derivative terms on a background
        solution including a warp-factor, an eight-dimensional compact manifold, and fluxes.
        The dynamical fields are K\"ahler deformations and vectors from the M-theory three-form.
        We show that the potential is only induced by fluxes and the naive
        contributions obtained from higher-curvature terms on a Calabi-Yau
        background aberration once the back-reaction to the full solution is taken
        into account. For the resulting three-dimensional action we analyse
        the K\"ahler potential and complex coordinates and show compatibility
        with N=2 supersymmetry. We argue that the higher-order result is also
        compatible with a no-scale aberration. We find that the complex
        coordinates should be formulated as divisor integrals for which a
        non-trivial interplay between the warp-factor terms and the
        higher-curvature terms allow a derivation of the moduli space metric.
        This leads us to discuss higher-derivative corrections to the M5-brane
        action.
        """


class ClassifierTest(ClassifierTestCase):

    def test_keywords(self):
        """Test extraction"""
        from invenio.modules.classifier.api import get_keywords_from_text
        out = get_keywords_from_text(
            text_lines=[self.sample_text],
            taxonomy_name=self.taxonomy_name,
            output_mode="dict"
        )
        output = out.get("complete_output")
        single_keywords = output.get("Single keywords", []).keys()

        assert len(single_keywords) == 3
        assert "aberration" in single_keywords

        core_keywords = output.get("Core keywords", []).keys()

        assert len(core_keywords) == 2
        assert "supersymmetry" in core_keywords

    def test_rebuild_cache(self):
        """classifier - test rebuilding cache."""
        from invenio.modules.classifier import reader
        info = reader._get_ontology(self.taxonomy_name)

        self.assertTrue(info[0])
        cache = reader._get_cache_path(info[0])

        if os.path.exists(cache):
            ctime = os.stat(cache)[stat.ST_CTIME]
        else:
            ctime = -1

        time.sleep(0.5)  # sleep a bit for timing issues
        rex = reader.get_regular_expressions(
            self.taxonomy_name, rebuild=True)
        self.assertTrue(os.path.exists(cache))
        ntime = os.stat(cache)[stat.ST_CTIME]
        self.assertTrue((ntime > ctime))

        self.assertEqual(len(rex[0]) + len(rex[1]), 63)

    def test_cache_accessibility(self):
        """classifier - test cache accessibility/writability"""
        from flask import current_app
        from invenio.modules.classifier.registry import taxonomies
        from invenio.modules.classifier import reader
        from invenio.modules.classifier.errors import TaxonomyError
        # we will do tests with a copy of test taxonomy, in case anything goes
        # wrong...
        orig_name, orig_taxonomy_path, orig_taxonomy_url = reader._get_ontology(
            self.taxonomy_name)

        taxonomy_name = self.taxonomy_name + '.copy'
        taxonomy_path = os.path.join(
            current_app.config['CFG_TMPDIR'], taxonomy_name + '.rdf')

        shutil.copy(orig_taxonomy_path, taxonomy_path)
        taxonomies[taxonomy_name] = taxonomy_path
        assert(os.path.exists(taxonomy_path))

        name, taxonomy_path, taxonomy_url = reader._get_ontology(
            taxonomy_name)
        cache = reader._get_cache_path(
            os.path.basename(taxonomy_path))

        assert name

        if os.path.exists(cache):
            os.remove(cache)

        reader.get_regular_expressions(
            taxonomy_name, rebuild=True, no_cache=False)

        assert(os.path.exists(cache))

        # set cache unreadable
        os.chmod(cache, 000)

        self.assertRaises(
            TaxonomyError,
            reader.get_regular_expressions,
            taxonomy_name, rebuild=False, no_cache=False
        )

        # set cache unreadable and test writing
        os.chmod(cache, 000)

        self.assertRaises(
            TaxonomyError,
            reader.get_regular_expressions,
            taxonomy_name, rebuild=True, no_cache=False
        )

        # set cache readable and test writing
        os.chmod(cache, 600)

        self.assertRaises(
            TaxonomyError,
            reader.get_regular_expressions,
            taxonomy_name, rebuild=True, no_cache=False
        )

        # set cache writable only
        os.chmod(cache, 200)
        reader.get_regular_expressions(
            taxonomy_name, rebuild=True, no_cache=False)

        reader.get_regular_expressions(
            taxonomy_name, rebuild=False, no_cache=False)

        # set cache readable/writable but corrupted (must rebuild itself)
        os.chmod(cache, 600)
        os.remove(cache)
        open(cache, 'w').close()

        reader.get_regular_expressions(
            taxonomy_name, rebuild=False, no_cache=False)

        # set cache readable/writable but corrupted (must rebuild itself)
        open(cache, 'w').close()
        try:
            os.rename(taxonomy_path, taxonomy_path + 'x')
            open(taxonomy_path, 'w').close()
            self.assertRaises(
                TaxonomyError,
                reader.get_regular_expressions,
                taxonomy_name, rebuild=False, no_cache=False
            )
        finally:
            os.rename(taxonomy_path + 'x', taxonomy_path)

        # make cache ok, but corrupt source
        reader.get_regular_expressions(
            taxonomy_name, rebuild=True, no_cache=False)

        try:
            os.rename(taxonomy_path, taxonomy_path + 'x')
            open(taxonomy_path, 'w').close()
            time.sleep(.1)
            # touch the taxonomy to be older
            os.utime(cache, (time.time() + 100, time.time() + 100))
            reader.get_regular_expressions(
                taxonomy_name, rebuild=False, no_cache=False)
        finally:
            os.rename(taxonomy_path + 'x', taxonomy_path)

        # make cache ok (but old), and corrupt source
        reader.get_regular_expressions(
            taxonomy_name, rebuild=True, no_cache=False)
        try:
            os.rename(taxonomy_path, taxonomy_path + 'x')
            open(taxonomy_path, 'w').close()
            self.assertRaises(
                TaxonomyError,
                reader.get_regular_expressions,
                taxonomy_name, rebuild=False, no_cache=False
            )
        finally:
            os.rename(taxonomy_path + 'x', taxonomy_path)

        name, taxonomy_path, taxonomy_url = reader._get_ontology(
            taxonomy_name)
        cache = reader._get_cache_path(name)
        os.remove(taxonomy_path)
        os.remove(cache)


TEST_SUITE = make_test_suite(ClassifierTest)


if __name__ == '__main__':
    run_test_suite(TEST_SUITE)
