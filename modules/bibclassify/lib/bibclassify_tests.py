# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2010, 2011 CERN.
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

"""
Test suite for BibClassify module - this unit-test is actually abusing
an idea of unit-testing. Some of the test require a lot of time (several
seconds) to run: they download files, process fulltexts, rebuild cache etc
[rca]

This module is STANDALONE SAFE
"""

import sys

import unittest
import tempfile
import cStringIO
import random
import copy
import os
import glob
import time
import stat
import shutil

import bibclassify_config as bconfig
from testutils import make_test_suite, run_test_suite
import config
import bibclassify_engine
import bibclassify_cli
import bibclassify_ontology_reader

# do this only if not in STANDALONE mode
bibclassify_daemon = dbquery = None
if not bconfig.STANDALONE:
    import dbquery
    import bibclassify_daemon


class BibClassifyTest(unittest.TestCase):
    """ Abusive test suite - the one that takes sooooo long """

    def setUp(self):
        """Initialize stuff"""
        #self.tmpdir = invenio.config.CFG_TMPDIR
        config.CFG_TMPDIR = tempfile.gettempdir()

        self.oldstdout = sys.stdout
        self.oldstderr = sys.stderr

        # just for debugging in Eclipse (to see messages printed)
        if 'stdout' in sys.argv:
            self.stdout = sys.stdout
            self.stderr = sys.stderr
        else:
            self.stdout = cStringIO.StringIO()
            self.stderr = cStringIO.StringIO()

        sys.stdout = self.stdout
        sys.stderr = self.stderr

        self.taxonomy_name = "HEP"

    def tearDown(self):
        self.stdout.close()
        self.stderr.close()
        sys.stdout = self.oldstdout
        sys.stderr = self.oldstderr

    def test_cli_extract_from_url(self):
        """bibclassify -k HEP.rdf http://arxiv.org/pdf/0808.1825"""

        args = "-k HEP.rdf http://arxiv.org/pdf/0808.1825".split()
        options = bibclassify_cli._read_options(args)

        bibclassify_engine.output_keywords_for_sources(options["text_files"],
            options["taxonomy"],
            rebuild_cache=options["rebuild_cache"],
            no_cache=options["no_cache"],
            output_mode=options["output_mode"],
            output_limit=options["output_limit"],
            spires=options["spires"],
            match_mode=options["match_mode"],
            with_author_keywords=options["with_author_keywords"],
            extract_acronyms=options["extract_acronyms"],
            only_core_tags=options["only_core_tags"])


        self.stdout.seek(0)
        results = self.stdout.read()
        self.stderr.seek(0)
        errors = self.stderr.read()


        res, msg = check_pdf0(results)
        if not res:
            self.fail(msg)





    def test_cli_extract_from_filepath(self):
        """bibclassify -k HEP.rdf {cache}/article.pdf"""


        path = os.path.join(os.path.dirname(__file__), '../../../var/data/files/g0/90/9611103.pdf;1')
        if not os.path.exists(path):
            sys.stderr.write("No PDF for testing found, returning")
            return

        args = ("-k HEP.rdf %s" % path).split()
        options = bibclassify_cli._read_options(args)

        bibclassify_engine.output_keywords_for_sources(options["text_files"],
            options["taxonomy"],
            rebuild_cache=options["rebuild_cache"],
            no_cache=options["no_cache"],
            output_mode=options["output_mode"],
            output_limit=options["output_limit"],
            spires=options["spires"],
            match_mode=options["match_mode"],
            with_author_keywords=options["with_author_keywords"],
            extract_acronyms=options["extract_acronyms"],
            only_core_tags=options["only_core_tags"])


        self.stdout.flush()
        self.stdout.seek(0)
        results = self.stdout.read()
        self.stderr.flush()
        self.stderr.seek(0)
        errors = self.stderr.read()


        res, msg = check_pdf2(results)
        if not res:
            self.fail(msg)



    def test_cli_extract_from_directory(self):
        """bibclassify -k HEP.rdf directory/"""


        path = os.path.abspath(os.path.dirname(__file__) + '/../../../var/data/files/g0/90')

        if not os.path.exists(path):
            print "No PDF folder for testing found, returning"
            return


        args = ("-k HEP.rdf %s" % path).split()
        options = bibclassify_cli._read_options(args)

        bibclassify_engine.output_keywords_for_sources(options["text_files"],
            options["taxonomy"],
            rebuild_cache=options["rebuild_cache"],
            no_cache=options["no_cache"],
            output_mode=options["output_mode"],
            output_limit=options["output_limit"],
            spires=options["spires"],
            match_mode=options["match_mode"],
            with_author_keywords=options["with_author_keywords"],
            extract_acronyms=options["extract_acronyms"],
            only_core_tags=options["only_core_tags"])


        self.stdout.flush()
        self.stdout.seek(0)
        results = self.stdout.read()
        self.stderr.flush()
        self.stderr.seek(0)
        errors = self.stderr.read()

        res, msg = check_pdf2(results)
        if not res:
            self.fail(msg)

    def test_full_and_partial_matching_mode(self):
        """bibclassify - difference of extraction on part or full contents of pdf"""

        path = os.path.join(os.path.dirname(__file__), '../../../var/data/files/g0/90/9611103.pdf;1')
        if not os.path.exists(path):
            sys.stderr.write("No PDF for testing found, returning")
            return

        results = []
        for case in ["-k HEP.rdf %s" % path, "-k HEP.rdf %s -m partial" % path]:
            args = (case).split()
            options = bibclassify_cli._read_options(args)

            self.stdout.truncate(0)
            self.stderr.truncate(0)

            bibclassify_engine.output_keywords_for_sources(options["text_files"],
                options["taxonomy"],
                rebuild_cache=options["rebuild_cache"],
                no_cache=options["no_cache"],
                output_mode=options["output_mode"],
                output_limit=options["output_limit"],
                spires=options["spires"],
                match_mode=options["match_mode"],
                with_author_keywords=options["with_author_keywords"],
                extract_acronyms=options["extract_acronyms"],
                only_core_tags=options["only_core_tags"])


            self.stdout.flush()
            self.stdout.seek(0)
            results.append(self.stdout.read())
            self.stderr.flush()
            self.stderr.seek(0)
            errors = self.stderr.read()

        res, msg = check_pdf1(results[1])
        if not res:
            self.fail(msg)
        res, msg = check_pdf2(results[0])
        if not res:
            self.fail(msg)






    def test_rebuild_cache(self):
        """bibclassify - test rebuilding cache (takes long time)"""

        info = bibclassify_ontology_reader._get_ontology(self.taxonomy_name)

        if info[0]:
            cache = bibclassify_ontology_reader._get_cache_path(info[0])

            if os.path.exists(cache):
                ctime = os.stat(cache)[stat.ST_CTIME]
            else:
                ctime = -1

            rex = bibclassify_ontology_reader.get_regular_expressions(self.taxonomy_name, rebuild=True)

            self.assertTrue(os.path.exists(cache))
            ntime = os.stat(cache)[stat.ST_CTIME]

            self.assertTrue(ntime > ctime)
        else:
            raise Exception("Taxonomy wasn't found")


    def test_extract_using_recid(self):
        """bibclassify  - extracting data from database (using recID to find fulltext)"""
        if not bconfig.STANDALONE:
            bibtask = bibclassify_daemon.bibtask
            #first test if the record exists in the database
            record = dbquery.run_sql("SELECT * FROM bibrec WHERE id=94")
            #print record
            if len(record):

                bibtask.task_set_task_param('verbose', 0)
                bibtask.task_set_task_param('task_id', 1)

                results = bibclassify_daemon._analyze_documents([94], self.taxonomy_name, "XXX", output_limit=100)

            res, msg = check_pdf3(results)
            if not res:
                self.fail(msg)

    def test_cache_accessibility(self):
        """Test cache accessibility/writability"""

        # we will do tests with a copy of test taxonomy, in case anything goes wrong...
        name, taxonomy_path, taxonomy_url = bibclassify_ontology_reader._get_ontology('test')
        shutil.copy(taxonomy_path, taxonomy_path +'.copy')
        assert(os.path.exists(taxonomy_path + '.copy'))
        self.taxonomy_name = 'test.rdf.copy'

        taxonomy_name = self.taxonomy_name

        name, taxonomy_path, taxonomy_url = bibclassify_ontology_reader._get_ontology(self.taxonomy_name)
        cache = bibclassify_ontology_reader._get_cache_path(name)

        if not name:
            raise Exception("Taxonomy wasn't found")

        if os.path.exists(cache):
            os.remove(cache)

        bibclassify_ontology_reader.get_regular_expressions(taxonomy_name, rebuild=True, no_cache=False)
        assert(os.path.exists(cache))

        # set cache unreadable
        os.chmod(cache, 000)
        try: bibclassify_ontology_reader.get_regular_expressions(taxonomy_name, rebuild=False, no_cache=False)
        except: pass
        else: raise Exception('cache chmod to 000 but no exception raised')

        # set cache unreadable and test writing
        os.chmod(cache, 000)
        try: bibclassify_ontology_reader.get_regular_expressions(taxonomy_name, rebuild=True, no_cache=False)
        except: pass
        else: raise Exception('cache chmod to 000 but no exception raised')

        # set cache unreadable but don't care for it
        os.chmod(cache, 000)
        bibclassify_ontology_reader.get_regular_expressions(taxonomy_name, rebuild=False, no_cache=True)
        bibclassify_ontology_reader.get_regular_expressions(taxonomy_name, rebuild=True, no_cache=True)

        # set cache readable and test writing
        os.chmod(cache, 600)
        try: bibclassify_ontology_reader.get_regular_expressions(taxonomy_name, rebuild=True, no_cache=False)
        except: pass
        else: raise Exception('cache chmod to 600 but no exception raised')

        # set cache writable only
        os.chmod(cache, 200)
        bibclassify_ontology_reader.get_regular_expressions(taxonomy_name, rebuild=True, no_cache=False)
        bibclassify_ontology_reader.get_regular_expressions(taxonomy_name, rebuild=False, no_cache=False)

        # set cache readable/writable but corrupted (must rebuild itself)
        os.chmod(cache, 600)
        os.remove(cache)
        open(cache, 'w').close()
        bibclassify_ontology_reader.get_regular_expressions(taxonomy_name, rebuild=False, no_cache=False)

        # set cache readable/writable but corrupted (must rebuild itself)
        open(cache, 'w').close()
        try:
            os.rename(taxonomy_path, taxonomy_path + 'x')
            open(taxonomy_path, 'w').close()
            bibclassify_ontology_reader.get_regular_expressions(taxonomy_name, rebuild=False, no_cache=False)
        except:
            pass
        finally:
            os.rename(taxonomy_path+'x', taxonomy_path)

        # make cache ok, but corrupt source
        bibclassify_ontology_reader.get_regular_expressions(taxonomy_name, rebuild=True, no_cache=False)
        try:
            os.rename(taxonomy_path, taxonomy_path + 'x')
            open(taxonomy_path, 'w').close()
            time.sleep(.1)
            os.utime(cache, (time.time() + 100, time.time() + 100))  #touch the taxonomy to be older
            bibclassify_ontology_reader.get_regular_expressions(taxonomy_name, rebuild=False, no_cache=False)
        except:
            os.rename(taxonomy_path+'x', taxonomy_path)
            raise Exception('Cache exists and is ok, but was ignored')
        finally:
            os.rename(taxonomy_path+'x', taxonomy_path)

        # make cache ok (but old), and corrupt source
        bibclassify_ontology_reader.get_regular_expressions(taxonomy_name, rebuild=True, no_cache=False)
        try:
            os.rename(taxonomy_path, taxonomy_path + 'x')
            open(taxonomy_path, 'w').close()
            bibclassify_ontology_reader.get_regular_expressions(taxonomy_name, rebuild=False, no_cache=False)
        except:
            pass
        finally:
            os.rename(taxonomy_path+'x', taxonomy_path)

        name, taxonomy_path, taxonomy_url = bibclassify_ontology_reader._get_ontology(self.taxonomy_name)
        cache = bibclassify_ontology_reader._get_cache_path(name)
        os.remove(taxonomy_path)
        os.remove(cache)

    def xtest_ingest_taxonomy_by_url(self):
        pass

    def xtest_ingest_taxonomy_by_name(self):
        pass

    def xtest_ingest_taxonomy_by_path(self):
        pass

    def xtest_ingest_taxonomy_db_name(self):
        pass

    def xtest_ouput_modes(self):
        pass

    def xtest_get_single_keywords(self):
        """test the function returns {<keyword>: [ [spans...] ] }"""

    def xtest_get_composite_keywords(self):
        """test the function returns {<keyword>: [ [spans...], [correct component counts] ] }"""


def check_pdf0(result):
    """
    Results for: http://arxiv.org/PS_cache/arxiv/pdf/0808/0808.1825v1.pdf
                 http://arxiv.org/pdf/0808.1825

    These results will depend on the taxonomy, but let's have them, as they can
    serve as early-warning.

    """

    output = """
Composite keywords:
9  top: mass [10, 22]
3  W: mass [11, 22]
2  Higgs particle: mass [3, 22]
2  electroweak interaction: radiative correction [5, 3]
1  mass: transverse [22, 1]
1  W: transverse [11, 1]
1  particle: massive [4, 1]
1  correction: quantum [1, 2]
1  boson: vector [2, 1]
1  p: beam [2, 1]

Single keywords:
11  CERN LHC Coll
9  Batavia TEVATRON Coll
9  CERN LEP Stor
7  ATLAS
7  SLD
4  SLAC SLC Linac
2  statistics
2  background
2  lepton
1  leptonic decay
1  supersymmetry
1  higher-order
1  accelerator
1  Monte Carlo
1  CERN Lab
1  hadron
1  W W
1  CDF

Core keywords:
11  CERN LHC Coll
9  Batavia TEVATRON Coll
9  CERN LEP Stor
7  ATLAS
7  SLD
4  SLAC SLC Linac
1  supersymmetry
1  CERN Lab
1  CDF """
    return check_pdf(result, output)

def check_pdf1(result):
    """ test for:
    /opt/cds-invenio/var/data/files/g0/90/9611103.pdf -m partial
    """

    output = """
Composite keywords:
4  gauge field theory: Yang-Mills [0, 2]
3  gaugefieldtheory: Yang-Mills: supersymmetry [4, 8]
2  supersymmetry: transformation [8, 4]
2  dimension: 10 [6, 6]
2  dimension: 2 [6, 6]
2  Yang-Mills: supersymmetry [2, 8]
2  symmetry: gauge [3, 4]
2  field equations: Yang-Mills [2, 2]
1  dimension: 1 [6, 8]
1  quantum mechanics: model [2, 4]
1  invariance: gauge [2, 4]
1  dimension: 11 [6, 1]
1  field theory: vector [0, 3]
1  invariance: Lorentz [2, 1]

Single keywords:
3  matrix model
2  dimensional reduction
2  commutation relations
2  light cone
2  M-theory
2  algebra
1  invariance gauge
1  field strength
1  expansion 1/N
1  translation
1  F-theory

Core keywords:
2  M-theory"""
    return check_pdf(result, output)

def check_pdf2(result):
    """ test for:
    /opt/cds-invenio/var/data/files/g0/90/9611103.pdf -m full
    """

    output = """
Composite keywords:
5  symmetry: gauge [8, 10]
5  invariance: Lorentz [9, 6]
5  gauge field theory: Yang-Mills [0, 4]
3  dimension: 2 [9, 15]
3  gaugefieldtheory: Yang-Mills: supersymmetry [4, 14]
3  Yang-Mills: supersymmetry [4, 14]
3  field equations: Yang-Mills [5, 4]
2  dimension: 10 [9, 13]
2  dimension: 1 [9, 13]
2  supersymmetry: transformation [14, 6]
2  supersymmetry: algebra [14, 5]
2  invariance: gauge [9, 10]
2  operator: translation [3, 6]
1  quantum mechanics: model [3, 8]
1  matrix model: action [5, 5]
1  group: Lorentz [4, 6]
1  dimension: 11 [9, 2]
1  constraint: solution [7, 1]
1  field theory: vector [0, 4]
1  geometry: noncommutative [2, 1]

Single keywords:
4  dimensional reduction
3  light cone
2  commutation relations
2  invariance gauge
2  quantum gravity
2  background
2  M-theory
1  equivalence principle
1  uncertainty relations
1  field strength
1  expansion 1/N
1  F-theory
1  D-brane

Core keywords:
2  quantum gravity
2  M-theory
1  D-brane
"""
    return check_pdf(result, output)

def check_pdf3(result):
    """ test for:
    /opt/cds-invenio/var/data/files/g0/90/9611103.pdf -m full -o marcxml
    """

    output = """
<record>
<controlfield tag="001">94</controlfield>
<datafield tag="653" ind1="1" ind2="">
    <subfield code="a">matrix model</subfield>
    <subfield code="n">3</subfield>
    <subfield code="9">BibClassify/HEP</subfield>
</datafield>
<datafield tag="653" ind1="1" ind2="">
    <subfield code="a">dimensional reduction</subfield>
    <subfield code="n">2</subfield>
    <subfield code="9">BibClassify/HEP</subfield>
</datafield>
<datafield tag="653" ind1="1" ind2="">
    <subfield code="a">commutation relations</subfield>
    <subfield code="n">2</subfield>
    <subfield code="9">BibClassify/HEP</subfield>
</datafield>
<datafield tag="653" ind1="1" ind2="">
    <subfield code="a">light cone</subfield>
    <subfield code="n">2</subfield>
    <subfield code="9">BibClassify/HEP</subfield>
</datafield>
<datafield tag="653" ind1="1" ind2="">
    <subfield code="a">M-theory</subfield>
    <subfield code="n">2</subfield>
    <subfield code="9">BibClassify/HEP</subfield>
</datafield>
<datafield tag="653" ind1="1" ind2="">
    <subfield code="a">algebra</subfield>
    <subfield code="n">2</subfield>
    <subfield code="9">BibClassify/HEP</subfield>
</datafield>
<datafield tag="653" ind1="1" ind2="">
    <subfield code="a">invariance gauge</subfield>
    <subfield code="n">1</subfield>
    <subfield code="9">BibClassify/HEP</subfield>
</datafield>
<datafield tag="653" ind1="1" ind2="">
    <subfield code="a">field strength</subfield>
    <subfield code="n">1</subfield>
    <subfield code="9">BibClassify/HEP</subfield>
</datafield>
<datafield tag="653" ind1="1" ind2="">
    <subfield code="a">expansion 1/N</subfield>
    <subfield code="n">1</subfield>
    <subfield code="9">BibClassify/HEP</subfield>
</datafield>
<datafield tag="653" ind1="1" ind2="">
    <subfield code="a">translation</subfield>
    <subfield code="n">1</subfield>
    <subfield code="9">BibClassify/HEP</subfield>
</datafield>
<datafield tag="653" ind1="1" ind2="">
    <subfield code="a">F-theory</subfield>
    <subfield code="n">1</subfield>
    <subfield code="9">BibClassify/HEP</subfield>
</datafield>
<datafield tag="653" ind1="1" ind2="">
    <subfield code="a">gauge field theory: Yang-Mills</subfield>
    <subfield code="n">4</subfield>
    <subfield code="9">BibClassify/HEP</subfield>
</datafield>
<datafield tag="653" ind1="1" ind2="">
    <subfield code="a">gaugefieldtheory: Yang-Mills: supersymmetry</subfield>
    <subfield code="n">3</subfield>
    <subfield code="9">BibClassify/HEP</subfield>
</datafield>
<datafield tag="653" ind1="1" ind2="">
    <subfield code="a">supersymmetry: transformation</subfield>
    <subfield code="n">2</subfield>
    <subfield code="9">BibClassify/HEP</subfield>
</datafield>
<datafield tag="653" ind1="1" ind2="">
    <subfield code="a">dimension: 10</subfield>
    <subfield code="n">2</subfield>
    <subfield code="9">BibClassify/HEP</subfield>
</datafield>
<datafield tag="653" ind1="1" ind2="">
    <subfield code="a">dimension: 2</subfield>
    <subfield code="n">2</subfield>
    <subfield code="9">BibClassify/HEP</subfield>
</datafield>
<datafield tag="653" ind1="1" ind2="">
    <subfield code="a">Yang-Mills: supersymmetry</subfield>
    <subfield code="n">2</subfield>
    <subfield code="9">BibClassify/HEP</subfield>
</datafield>
<datafield tag="653" ind1="1" ind2="">
    <subfield code="a">symmetry: gauge</subfield>
    <subfield code="n">2</subfield>
    <subfield code="9">BibClassify/HEP</subfield>
</datafield>
<datafield tag="653" ind1="1" ind2="">
    <subfield code="a">field equations: Yang-Mills</subfield>
    <subfield code="n">2</subfield>
    <subfield code="9">BibClassify/HEP</subfield>
</datafield>
<datafield tag="653" ind1="1" ind2="">
    <subfield code="a">dimension: 1</subfield>
    <subfield code="n">1</subfield>
    <subfield code="9">BibClassify/HEP</subfield>
</datafield>
<datafield tag="653" ind1="1" ind2="">
    <subfield code="a">quantum mechanics: model</subfield>
    <subfield code="n">1</subfield>
    <subfield code="9">BibClassify/HEP</subfield>
</datafield>
<datafield tag="653" ind1="1" ind2="">
    <subfield code="a">invariance: gauge</subfield>
    <subfield code="n">1</subfield>
    <subfield code="9">BibClassify/HEP</subfield>
</datafield>
<datafield tag="653" ind1="1" ind2="">
    <subfield code="a">dimension: 11</subfield>
    <subfield code="n">1</subfield>
    <subfield code="9">BibClassify/HEP</subfield>
</datafield>
<datafield tag="653" ind1="1" ind2="">
    <subfield code="a">field theory: vector</subfield>
    <subfield code="n">1</subfield>
    <subfield code="9">BibClassify/HEP</subfield>
</datafield>
<datafield tag="653" ind1="1" ind2="">
    <subfield code="a">invariance: Lorentz</subfield>
    <subfield code="n">1</subfield>
    <subfield code="9">BibClassify/HEP</subfield>
</datafield>

</record>
 """
    return check_pdf(result, output)


def check_pdf(result, output):
    for line in output.splitlines():
        line = line.strip()
        if line:
            if line not in result:
                return (False, "\nGot: %s\nMissing: \"%s\"" % (result,line))
    return (True, True)



def suite():
    tests = ['test_cache_accessibility']
    return unittest.TestSuite(map(BibClassifyTest, tests))

if 'custom' in sys.argv:
    TEST_SUITE = suite()
else:
    TEST_SUITE = make_test_suite(BibClassifyTest)


if __name__ == '__main__':
    run_test_suite(TEST_SUITE)
