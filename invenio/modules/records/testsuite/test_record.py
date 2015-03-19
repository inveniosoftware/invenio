# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

"""Test Record API."""

import os
import pkg_resources

from flask_registry import (
    ImportPathRegistry, PkgResourcesDirDiscoveryRegistry, RegistryProxy
)

from invenio.base.wrappers import lazy_import
from invenio.ext.registry import ModuleAutoDiscoverySubRegistry
from invenio.testsuite import (
    InvenioTestCase, make_test_suite, nottest, run_test_suite
)

from mock import patch

Record = lazy_import('invenio.modules.records.api:Record')
Document = lazy_import('invenio.modules.documents.api:Document')

Field_parser = lazy_import('invenio.modules.jsonalchemy.parser:FieldParser')
Model_parser = lazy_import('invenio.modules.jsonalchemy.parser:ModelParser')

TEST_PACKAGE = 'invenio.modules.records.testsuite'

test_registry = RegistryProxy('testsuite', ImportPathRegistry,
                              initial=[TEST_PACKAGE])


def field_definitions():
    """Load field definitions."""
    return PkgResourcesDirDiscoveryRegistry(
        'fields', registry_namespace=test_registry)


def model_definitions():
    """Load model definitions."""
    return PkgResourcesDirDiscoveryRegistry(
        'models', registry_namespace=test_registry)


def function_proxy():
    """Load functions."""
    return ModuleAutoDiscoverySubRegistry(
        'functions', registry_namespace=test_registry)


class TestRecord(InvenioTestCase):
    """Record - demo file parsing test."""

    @classmethod
    def setUpClass(cls):
        """Invalidate any previous field definition"""
        Field_parser._field_definitions = {}
        Field_parser._legacy_field_matchings = {}
        Model_parser._model_definitions = {}

    def setUp(self):
        """Initialize stuff"""
        self.app.extensions['registry']['testsuite.fields'] = field_definitions()
        self.app.extensions['registry']['testsuite.models'] = model_definitions()
        self.app.extensions['registry']['testsuite.functions'] = function_proxy()

    def tearDown(self):
        del self.app.extensions['registry']['testsuite.fields']
        del self.app.extensions['registry']['testsuite.models']
        del self.app.extensions['registry']['testsuite.functions']

    @nottest
    def test_records_created(self):
        """Record - demo file how many records are created."""
        xmltext = pkg_resources.resource_string(
            'invenio.testsuite',
            os.path.join('data', 'demo_record_marc_data.xml'))
        recs = [record for record in Record.create_many(xmltext, master_format='marc')]
        self.assertEqual(141, len(recs))

    def test_accented_unicode_letterst_test(self):
        """Record - accented Unicode letters."""
        xml = '''<record>
          <datafield tag="041" ind1=" " ind2=" ">
            <subfield code="a">eng</subfield>
          </datafield>
          <datafield tag="100" ind1=" " ind2=" ">
            <subfield code="a">Döè1, John</subfield>
          </datafield>
          <datafield tag="245" ind1=" " ind2=" ">
            <subfield code="a">Пушкин</subfield>
          </datafield>
        </record>
        '''
        rec = Record.create(xml, master_format='marc', namespace='testsuite')
        self.assertEquals(rec['authors[0].full_name'], 'Döè1, John')
        self.assertEquals(rec['title.title'], 'Пушкин')

    def test_create_empty_record(self):
        """Record - Create empty record."""
        rec = Record(master_format='marc', namespace='testsuite')
        self.assertTrue('__meta_metadata__' in rec)
        self.assertEquals(list(rec.keys()), ['__meta_metadata__'])
        rec['title'] = {'title': 'My title'}
        self.assertTrue('title' in rec)
        self.assertTrue('title' in rec['__meta_metadata__'])
        rec.set('title', {'title': 'Second title?'}, extend=True)
        self.assertEquals(len(rec['title']), 2)

    def test_validate(self):
        """Record - Validate record."""
        rec = Record(master_format='marc', namespace='testsuite')
        self.assertTrue('__meta_metadata__' in rec)
        self.assertTrue('recid' in rec.validate())
        rec['recid'] = '1'
        self.assertTrue('recid' in rec.validate())
        self.assertEquals(rec.validate()['recid'], 'must be of integer type')


class TestLegacyExport(InvenioTestCase):
    """Record - Legacy methods test."""

    @classmethod
    def setUpClass(cls):
        """Invalidate any previous field definition"""
        Field_parser._field_definitions = {}
        Field_parser._legacy_field_matchings = {}
        Model_parser._model_definitions = {}

    def setUp(self):
        """Initialize stuff"""
        self.app.extensions['registry']['testsuite.fields'] = field_definitions()
        self.app.extensions['registry']['testsuite.models'] = model_definitions()
        self.app.extensions['registry']['testsuite.functions'] = function_proxy()

    def tearDown(self):
        del self.app.extensions['registry']['testsuite.fields']
        del self.app.extensions['registry']['testsuite.models']
        del self.app.extensions['registry']['testsuite.functions']

    def test_legacy_export_marcxml(self):
        """Record - legacy export marxml."""
        # FIXME: use a better way to compare
        from invenio.legacy.bibrecord import create_record, records_identical
        blob = '''
            <record>
              <controlfield tag="001">8</controlfield>
              <datafield tag="100" ind1=" " ind2=" ">
                <subfield code="a">Efstathiou, G P</subfield>
                <subfield code="u">Cambridge University</subfield>
              </datafield>
              <datafield tag="245" ind1=" " ind2=" ">
                <subfield code="a">Title</subfield>
                <subfield code="b">SubTitle</subfield>
              </datafield>
              <datafield tag="700" ind1=" " ind2=" ">
               <subfield code="a">Lasenby, A N</subfield>
              </datafield>
              <datafield tag="980" ind1=" " ind2=" ">
                <subfield code="a">Articles</subfield>
              </datafield>
            </record>
        '''
        rec = Record.create(blob, master_format='marc', namespace='testsuite')
        recstruct, _, _ = create_record(blob)
        json_recstruct, _, _ = create_record(rec.legacy_export_as_marc())
        self.assertTrue(records_identical(json_recstruct, recstruct,
                                          ignore_subfield_order=True))

    def test_legacy_create_recstruct(self):
        """Record - create recstruct."""
        from invenio.legacy.bibrecord import create_record, records_identical

        blob = '''
            <record>
              <controlfield tag="001">8</controlfield>
              <datafield tag="100" ind1=" " ind2=" ">
                <subfield code="a">Efstathiou, G P</subfield>
                <subfield code="u">Cambridge University</subfield>
              </datafield>
              <datafield tag="245" ind1=" " ind2=" ">
                <subfield code="a">Title</subfield>
                <subfield code="b">SubTitle</subfield>
              </datafield>
              <datafield tag="700" ind1=" " ind2=" ">
               <subfield code="a">Lasenby, A N</subfield>
              </datafield>
              <datafield tag="980" ind1=" " ind2=" ">
                <subfield code="a">Articles</subfield>
              </datafield>
            </record>
        '''
        rec = Record.create(blob, master_format='marc', namespace='testsuite')
        json_recstruct = rec.legacy_create_recstruct()
        recstruct, _, _ = create_record(blob)
        self.assertTrue(records_identical(json_recstruct, recstruct,
                                          ignore_subfield_order=True))


class TestMarcRecordCreation(InvenioTestCase):
    """Records from marc."""

    @classmethod
    def setUpClass(cls):
        """Invalidate any previous field definition"""
        Field_parser._field_definitions = {}
        Field_parser._legacy_field_matchings = {}
        Model_parser._model_definitions = {}

    def setUp(self):
        """Initialize stuff"""
        self.app.extensions['registry']['testsuite.fields'] = field_definitions()
        self.app.extensions['registry']['testsuite.models'] = model_definitions()

    def tearDown(self):
        del self.app.extensions['registry']['testsuite.fields']
        del self.app.extensions['registry']['testsuite.models']

    def test_rec_json_creation_from_marcxml(self):
        """Record - recjson from marcxml"""
        xml = """
            <record>
                <datafield tag="037" ind1=" " ind2=" ">
                <subfield code="a">astro-ph/9812226</subfield>
                </datafield>
                <datafield tag="041" ind1=" " ind2=" ">
                <subfield code="a">eng</subfield>
                </datafield>
                <datafield tag="100" ind1=" " ind2=" ">
                <subfield code="a">Efstathiou, G P</subfield>
                <subfield code="u">Cambridge University</subfield>
                </datafield>
                <datafield tag="245" ind1=" " ind2=" ">
                <subfield code="a">Constraints on $\Omega_{\Lambda}$ and $\Omega_{m}$from Distant Type 1a Supernovae and Cosmic Microwave Background Anisotropies</subfield>
                </datafield>
                <datafield tag="260" ind1=" " ind2=" ">
                <subfield code="c">14 Dec 1998</subfield>
                </datafield>
                <datafield tag="300" ind1=" " ind2=" ">
                <subfield code="a">6 p</subfield>
                </datafield>
                <datafield tag="520" ind1=" " ind2=" ">
                <subfield code="a">We perform a combined likelihood analysis of the latest cosmic microwave background anisotropy data and distant Type 1a Supernova data of Perlmutter etal (1998a). Our analysis is restricted tocosmological models where structure forms from adiabatic initial fluctuations characterised by a power-law spectrum with negligible tensor component. Marginalizing over other parameters, our bestfit solution gives Omega_m = 0.25 (+0.18, -0.12) and Omega_Lambda = 0.63 (+0.17, -0.23) (95 % confidence errors) for the cosmic densities contributed by matter and a cosmological constantrespectively. The results therefore strongly favour a nearly spatially flat Universe with a non-zero cosmological constant.</subfield>
                </datafield>
                <datafield tag="595" ind1=" " ind2=" ">
                <subfield code="a">LANL EDS</subfield>
                </datafield>
                <datafield tag="650" ind1="1" ind2="7">
                <subfield code="2">SzGeCERN</subfield>
                <subfield code="a">Astrophysics and Astronomy</subfield>
                </datafield>
                <datafield tag="700" ind1=" " ind2=" ">
                <subfield code="a">Lasenby, A N</subfield>
                </datafield>
                <datafield tag="700" ind1=" " ind2=" ">
                <subfield code="a">Hobson, M P</subfield>
                </datafield>
                <datafield tag="700" ind1=" " ind2=" ">
                <subfield code="a">Ellis, R S</subfield>
                </datafield>
                <datafield tag="700" ind1=" " ind2=" ">
                <subfield code="a">Bridle, S L</subfield>
                </datafield>
                <datafield tag="856" ind1="0" ind2=" ">
                <subfield code="f">George Efstathiou &lt;gpe@ast.cam.ac.uk&gt;</subfield>
                </datafield>
                <datafield tag="FFT" ind1=" " ind2=" ">
                <subfield code="a">http://invenio-software.org/download/invenio-demo-site-files/9812226.pdf</subfield>
                </datafield>
                <datafield tag="FFT" ind1=" " ind2=" ">
                <subfield code="a">http://invenio-software.org/download/invenio-demo-site-files/9812226.fig1.ps.gz</subfield>
                <subfield code="t">Additional</subfield>
                </datafield>
                <datafield tag="FFT" ind1=" " ind2=" ">
                <subfield code="a">http://invenio-software.org/download/invenio-demo-site-files/9812226.fig3.ps.gz</subfield>
                <subfield code="t">Additional</subfield>
                </datafield>
                <datafield tag="FFT" ind1=" " ind2=" ">
                <subfield code="a">http://invenio-software.org/download/invenio-demo-site-files/9812226.fig5.ps.gz</subfield>
                <subfield code="t">Additional</subfield>
                </datafield>
                <datafield tag="FFT" ind1=" " ind2=" ">
                <subfield code="a">http://invenio-software.org/download/invenio-demo-site-files/9812226.fig6.ps.gz</subfield>
                <subfield code="t">Additional</subfield>
                </datafield>
                <datafield tag="FFT" ind1=" " ind2=" ">
                <subfield code="a">http://invenio-software.org/download/invenio-demo-site-files/9812226.fig7.ps.gz</subfield>
                <subfield code="t">Additional</subfield>
                </datafield>
                <datafield tag="909" ind1="C" ind2="0">
                <subfield code="y">1998</subfield>
                </datafield>
                <datafield tag="909" ind1="C" ind2="0">
                <subfield code="b">11</subfield>
                </datafield>
                <datafield tag="909" ind1="C" ind2="1">
                <subfield code="c">1998-12-14</subfield>
                <subfield code="l">50</subfield>
                <subfield code="m">2001-04-07</subfield>
                <subfield code="o">BATCH</subfield>
                </datafield>
                <datafield tag="909" ind1="C" ind2="4">
                <subfield code="p">Mon. Not. R. Astron. Soc.</subfield>
                </datafield>
                <datafield tag="909" ind1="C" ind2="O">
                <subfield code="i">SLAC</subfield>
                <subfield code="s">4162242</subfield>
                </datafield>
                <datafield tag="909" ind1="C" ind2="5">
                <subfield code="b">CER</subfield>
                </datafield>
                <datafield tag="909" ind1="C" ind2="S">
                <subfield code="s">n</subfield>
                <subfield code="w">200231</subfield>
                </datafield>
                <datafield tag="980" ind1=" " ind2=" ">
                <subfield code="a">PREPRINT</subfield>
                </datafield>
                <datafield tag="999" ind1="C" ind2="5">
                <subfield code="m">Bond, J.R. 1996, Theory and Observations of the Cosmic Background Radiation, in "Cosmology and Large Scale Structure", Les Houches Session LX, August 1993, eds. R. Schaeffer, J. Silk, M. Spiro and J. Zinn-Justin, Elsevier SciencePress, Amsterdam, p469</subfield>
                </datafield>
                <datafield tag="999" ind1="C" ind2="5">
                <subfield code="m">Bond J.R., Efstathiou G., Tegmark M., 1997</subfield>
                <subfield code="p">L33</subfield>
                <subfield code="t">Mon. Not. R. Astron. Soc.</subfield>
                <subfield code="v">291</subfield>
                <subfield code="y">1997</subfield>
                <subfield code="s">Mon. Not. R. Astron. Soc. 291 (1997) L33</subfield>
                </datafield>
                <datafield tag="999" ind1="C" ind2="5">
                <subfield code="m">Bond, J.R., Jaffe, A. 1997, in Proc. XXXI Rencontre de Moriond, ed. F. Bouchet, Edition Fronti eres, in press</subfield>
                <subfield code="r">astro-ph/9610091</subfield>
                </datafield>
                <datafield tag="999" ind1="C" ind2="5">
                <subfield code="m">Bond J.R., Jaffe A.H. and Knox L.E., 1998</subfield>
                <subfield code="r">astro-ph/9808264</subfield>
                <subfield code="s">Astrophys.J. 533 (2000) 19</subfield>
                </datafield>
                <datafield tag="999" ind1="C" ind2="5">
                <subfield code="m">Burles S., Tytler D., 1998a, to appear in the Proceedings of the Second Oak Ridge Symposium on Atomic &amp; Nuclear Astrophysics, ed. A. Mezzacappa, Institute of Physics, Bristol</subfield>
                <subfield code="r">astro-ph/9803071</subfield>
                </datafield>
                <datafield tag="999" ind1="C" ind2="5">
                <subfield code="m">Burles S., Tytler D., 1998b, Astrophys. J.in press</subfield>
                <subfield code="r">astro-ph/9712109</subfield>
                <subfield code="s">Astrophys.J. 507 (1998) 732</subfield>
                </datafield>
                <datafield tag="999" ind1="C" ind2="5">
                <subfield code="m">Caldwell, R.R., Dave, R., Steinhardt P.J., 1998</subfield>
                <subfield code="p">1582</subfield>
                <subfield code="t">Phys. Rev. Lett.</subfield>
                <subfield code="v">80</subfield>
                <subfield code="y">1998</subfield>
                <subfield code="s">Phys. Rev. Lett. 80 (1998) 1582</subfield>
                </datafield>
                <datafield tag="999" ind1="C" ind2="5">
                <subfield code="m">Carroll S.M., Press W.H., Turner E.L., 1992, Ann. Rev. Astr. Astrophys., 30, 499. Chaboyer B., 1998</subfield>
                <subfield code="r">astro-ph/9808200</subfield>
                <subfield code="s">Phys.Rept. 307 (1998) 23</subfield>
                </datafield>
                <datafield tag="999" ind1="C" ind2="5">
                <subfield code="m">Devlin M.J., De Oliveira-Costa A., Herbig T., Miller A.D., Netterfield C.B., Page L., Tegmark M., 1998, submitted to Astrophys. J</subfield>
                <subfield code="r">astro-ph/9808043</subfield>
                <subfield code="s">Astrophys. J. 509 (1998) L69-72</subfield>
                </datafield>
                <datafield tag="999" ind1="C" ind2="5">
                <subfield code="m">Efstathiou G. 1996, Observations of Large-Scale Structure in the Universe, in "Cosmology and Large Scale Structure", Les Houches Session LX, August 1993, eds. R. Schaeffer, J. Silk, M. Spiro and J. Zinn-Justin, Elsevier SciencePress, Amsterdam, p135. Efstathiou G., Bond J.R., Mon. Not. R. Astron. Soc.in press</subfield>
                <subfield code="r">astro-ph/9807130</subfield>
                <subfield code="s">Astrophys. J. 518 (1999) 2-23</subfield>
                </datafield>
                <datafield tag="999" ind1="C" ind2="5">
                <subfield code="m">Evrard G., 1998, submitted to Mon. Not. R. Astron. Soc</subfield>
                <subfield code="r">astro-ph/9701148</subfield>
                <subfield code="s">Mon.Not.Roy.Astron.Soc. 292 (1997) 289</subfield>
                </datafield>
                <datafield tag="999" ind1="C" ind2="5">
                <subfield code="m">Freedman J.B., Mould J.R., Kennicutt R.C., Madore B.F., 1998</subfield>
                <subfield code="r">astro-ph/9801090</subfield>
                <subfield code="s">Astrophys. J. 480 (1997) 705</subfield>
                </datafield>
                <datafield tag="999" ind1="C" ind2="5">
                <subfield code="m">Garnavich P.M. et al. 1998</subfield>
                <subfield code="r">astro-ph/9806396</subfield>
                <subfield code="s">Astrophys.J. 509 (1998) 74-79</subfield>
                </datafield>
                <datafield tag="999" ind1="C" ind2="5">
                <subfield code="m">Goobar A., Perlmutter S., 1995</subfield>
                <subfield code="p">14</subfield>
                <subfield code="t">Astrophys. J.</subfield>
                <subfield code="v">450</subfield>
                <subfield code="y">1995</subfield>
                <subfield code="s">Astrophys. J. 450 (1995) 14</subfield>
                </datafield>
                <datafield tag="999" ind1="C" ind2="5">
                <subfield code="m">Hamuy M., Phillips M.M., Maza J., Suntzeff N.B., Schommer R.A., Aviles R. 1996</subfield>
                <subfield code="p">2391</subfield>
                <subfield code="t">Astrophys. J.</subfield>
                <subfield code="v">112</subfield>
                <subfield code="y">1996</subfield>
                <subfield code="s">Astrophys. J. 112 (1996) 2391</subfield>
                </datafield>
                <datafield tag="999" ind1="C" ind2="5">
                <subfield code="m">Hancock S., Gutierrez C.M., Davies R.D., Lasenby A.N., Rocha G., Rebolo R., Watson R.A., Tegmark M., 1997</subfield>
                <subfield code="p">505</subfield>
                <subfield code="t">Mon. Not. R. Astron. Soc.</subfield>
                <subfield code="v">298</subfield>
                <subfield code="y">1997</subfield>
                <subfield code="s">Mon. Not. R. Astron. Soc. 298 (1997) 505</subfield>
                </datafield>
                <datafield tag="999" ind1="C" ind2="5">
                <subfield code="m">Hancock S., Rocha G., Lasenby A.N., Gutierrez C.M., 1998</subfield>
                <subfield code="p">L1</subfield>
                <subfield code="t">Mon. Not. R. Astron. Soc.</subfield>
                <subfield code="v">294</subfield>
                <subfield code="y">1998</subfield>
                <subfield code="s">Mon. Not. R. Astron. Soc. 294 (1998) L1</subfield>
                </datafield>
                <datafield tag="999" ind1="C" ind2="5">
                <subfield code="m">Herbig T., De Oliveira-Costa A., Devlin M.J., Miller A.D., Page L., Tegmark M., 1998, submitted to Astrophys. J</subfield>
                <subfield code="r">astro-ph/9808044</subfield>
                <subfield code="s">Astrophys.J. 509 (1998) L73-76</subfield>
                </datafield>
                <datafield tag="999" ind1="C" ind2="5">
                <subfield code="m">Lineweaver C.H., 1998. Astrophys. J.505, L69. Lineweaver, C.H., Barbosa D., 1998a</subfield>
                <subfield code="p">624</subfield>
                <subfield code="t">Astrophys. J.</subfield>
                <subfield code="v">446</subfield>
                <subfield code="y">1998</subfield>
                <subfield code="s">Astrophys. J. 446 (1998) 624</subfield>
                </datafield>
                <datafield tag="999" ind1="C" ind2="5">
                <subfield code="m">Lineweaver, C.H., Barbosa D., 1998b</subfield>
                <subfield code="p">799</subfield>
                <subfield code="t">Astron. Astrophys.</subfield>
                <subfield code="v">329</subfield>
                <subfield code="y">1998</subfield>
                <subfield code="s">Astron. Astrophys. 329 (1998) 799</subfield>
                </datafield>
                <datafield tag="999" ind1="C" ind2="5">
                <subfield code="m">De Oliveira-Costa A., Devlin M.J., Herbig T., Miller A.D., Netterfield C.B. Page L., Tegmark M., 1998, submitted to Astrophys. J</subfield>
                <subfield code="r">astro-ph/9808045</subfield>
                <subfield code="s">Astrophys. J. 509 (1998) L77-80</subfield>
                </datafield>
                <datafield tag="999" ind1="C" ind2="5">
                <subfield code="m">Ostriker J.P., Steinhardt P.J., 1995</subfield>
                <subfield code="p">600</subfield>
                <subfield code="t">Nature</subfield>
                <subfield code="v">377</subfield>
                <subfield code="y">1995</subfield>
                <subfield code="s">Nature 377 (1995) 600</subfield>
                </datafield>
                <datafield tag="999" ind1="C" ind2="5">
                <subfield code="m">Peebles P.J.E., 1993, Principles of Physical Cosmology, Princeton University Press, Princeton, New Jersey. Perlmutter S, et al., 1995, In Presentations at the NATO ASI in Aiguablava, Spain, LBL-38400; also published in Thermonuclear Supernova, P. Ruiz-Lapuente, R. Cana and J. Isern (eds), Dordrecht, Kluwer, 1997, p749. Perlmutter S, et al., 1997</subfield>
                <subfield code="p">565</subfield>
                <subfield code="t">Astrophys. J.</subfield>
                <subfield code="v">483</subfield>
                <subfield code="y">1997</subfield>
                <subfield code="s">Astrophys. J. 483 (1997) 565</subfield>
                </datafield>
                <datafield tag="999" ind1="C" ind2="5">
                <subfield code="m">Perlmutter S. et al., 1998a, Astrophys. J.in press. (P98)</subfield>
                <subfield code="r">astro-ph/9812133</subfield>
                <subfield code="s">Astrophys. J. 517 (1999) 565-586</subfield>
                </datafield>
                <datafield tag="999" ind1="C" ind2="5">
                <subfield code="m">Perlmutter S. et al., 1998b, In Presentation at the January 1988 Meeting of the American Astronomical Society, Washington D.C., LBL-42230, available at www-supernova.lbl.gov; B.A.A.S., volume : 29 (1997) 1351Perlmutter S, et al., 1998c</subfield>
                <subfield code="p">51</subfield>
                <subfield code="t">Nature</subfield>
                <subfield code="v">391</subfield>
                <subfield code="y">1998</subfield>
                <subfield code="s">Nature 391 (1998) 51</subfield>
                </datafield>
                <datafield tag="999" ind1="C" ind2="5">
                <subfield code="m">Ratra B., Peebles P.J.E., 1988</subfield>
                <subfield code="p">3406</subfield>
                <subfield code="t">Phys. Rev., D</subfield>
                <subfield code="v">37</subfield>
                <subfield code="y">1988</subfield>
                <subfield code="s">Phys. Rev. D 37 (1988) 3406</subfield>
                </datafield>
                <datafield tag="999" ind1="C" ind2="5">
                <subfield code="m">Riess A. et al. 1998, Astrophys. J.in press</subfield>
                <subfield code="r">astro-ph/9805201</subfield>
                <subfield code="s">Astron. J. 116 (1998) 1009-1038</subfield>
                </datafield>
                <datafield tag="999" ind1="C" ind2="5">
                <subfield code="m">Seljak U., Zaldarriaga M. 1996</subfield>
                <subfield code="p">437</subfield>
                <subfield code="t">Astrophys. J.</subfield>
                <subfield code="v">469</subfield>
                <subfield code="y">1996</subfield>
                <subfield code="s">Astrophys. J. 469 (1996) 437</subfield>
                </datafield>
                <datafield tag="999" ind1="C" ind2="5">
                <subfield code="m">Seljak U. &amp; Zaldarriaga M., 1998</subfield>
                <subfield code="r">astro-ph/9811123</subfield>
                <subfield code="s">Phys. Rev. D60 (1999) 043504</subfield>
                </datafield>
                <datafield tag="999" ind1="C" ind2="5">
                <subfield code="m">Tegmark M., 1997</subfield>
                <subfield code="p">3806</subfield>
                <subfield code="t">Phys. Rev. Lett.</subfield>
                <subfield code="v">79</subfield>
                <subfield code="y">1997</subfield>
                <subfield code="s">Phys. Rev. Lett. 79 (1997) 3806</subfield>
                </datafield>
                <datafield tag="999" ind1="C" ind2="5">
                <subfield code="m">Tegmark M. 1998, submitted to Astrophys. J</subfield>
                <subfield code="r">astro-ph/9809201</subfield>
                <subfield code="s">Astrophys. J. 514 (1999) L69-L72</subfield>
                </datafield>
                <datafield tag="999" ind1="C" ind2="5">
                <subfield code="m">Tegmark, M., Eisenstein D.J., Hu W., Kron R.G., 1998</subfield>
                <subfield code="r">astro-ph/9805117</subfield>
                </datafield>
                <datafield tag="999" ind1="C" ind2="5">
                <subfield code="m">Wambsganss J., Cen R., Ostriker J.P., 1998</subfield>
                <subfield code="p">29</subfield>
                <subfield code="t">Astrophys. J.</subfield>
                <subfield code="v">494</subfield>
                <subfield code="y">1998</subfield>
                <subfield code="s">Astrophys. J. 494 (1998) 29</subfield>
                </datafield>
                <datafield tag="999" ind1="C" ind2="5">
                <subfield code="m">Webster M., Bridle S.L., Hobson M.P., Lasenby A.N., Lahav O., Rocha, G., 1998, Astrophys. J.in press</subfield>
                <subfield code="r">astro-ph/9802109</subfield>
                </datafield>
                <datafield tag="999" ind1="C" ind2="5">
                <subfield code="m">White M., 1998, Astrophys. J.in press</subfield>
                <subfield code="r">astro-ph/9802295</subfield>
                <subfield code="s">Astrophys. J. 506 (1998) 495</subfield>
                </datafield>
                <datafield tag="999" ind1="C" ind2="5">
                <subfield code="m">Zaldarriaga, M., Spergel D.N., Seljak U., 1997</subfield>
                <subfield code="p">1</subfield>
                <subfield code="t">Astrophys. J.</subfield>
                <subfield code="v">488</subfield>
                <subfield code="y">1997</subfield>
                <subfield code="s">Astrophys. J. 488 (1997) 1</subfield>
                </datafield>
            </record>
        """
        r = Record.create(xml, master_format='marc', namespace='testsuite', schema='xml')

        self.assertEquals(r.additional_info.master_format, 'marc')
        self.assertTrue('authors' in r)
        self.assertEquals(r['authors[0].full_name'], "Efstathiou, G P")
        self.assertEquals(len(r['authors']), 5)
        self.assertTrue('title.title' in r)
        self.assertEquals(r['title.title'], "Constraints on $\Omega_{\Lambda}$ and $\Omega_{m}$from Distant Type 1a Supernovae and Cosmic Microwave Background Anisotropies")
        self.assertTrue('abstract.summary' in r)
        self.assertEquals(r['abstract.summary'], "We perform a combined likelihood analysis of the latest cosmic microwave background anisotropy data and distant Type 1a Supernova data of Perlmutter etal (1998a). Our analysis is restricted tocosmological models where structure forms from adiabatic initial fluctuations characterised by a power-law spectrum with negligible tensor component. Marginalizing over other parameters, our bestfit solution gives Omega_m = 0.25 (+0.18, -0.12) and Omega_Lambda = 0.63 (+0.17, -0.23) (95 % confidence errors) for the cosmic densities contributed by matter and a cosmological constantrespectively. The results therefore strongly favour a nearly spatially flat Universe with a non-zero cosmological constant.")
        self.assertTrue('reference' in r)
        self.assertEquals(len(r['reference']), 36)

    def test_error_catching(self):
        """ Record - catch any record conversion issues """
        from invenio.modules.jsonalchemy.errors import ReaderException
        from invenio.legacy.bibrecord import _select_parser
        blob = """<?xml version="1.0" encoding="UTF-8"?>
        <collection>
        <record>
          <datafield tag="FFT" ind1=" " ind2=" ">
            <subfield code="a">/path/to</subfield>
            <subfield code="t">Test</subfield>
            </record>
        </collection>
        """

        # lxml is super resilient to a tag soup, it won't fail on such a simple
        # mistake.
        if _select_parser() != 'lxml':
            with self.assertRaises(ReaderException):
                Record.create(blob, master_format='marc',
                              namespace='testsuite', schema='xml')


class TestRecordDocuments(InvenioTestCase):

    """Test record doccuments behaviour."""

    def setUp(self):
        self.app.config['DOCUMENTS_ENGINE'] = \
            "invenio.modules.jsonalchemy.jsonext.engines.memory:MemoryStorage"

    @patch('invenio.legacy.search_engine.check_user_can_view_record')
    def test_restricted_record_non_restricted_document(
            self, check_user_can_view_record_patch):
        """Record - Restrcited access to record documents."""
        d = Document.create({'title': 'Document 1',
                             'description': 'Testing 1',
                             'restriction': {'email': 'user@invenio.org'},
                             'recids': [1, 2, 3],
                             },
                            model='record_document_base')
        user_info = {'email': 'user@invenio.org',
                     'uid': -1}
        self.app.config['RECORD_DOCUMENT_VIEWRESTR_POLICY'] = 'ANY'
        check_user_can_view_record_patch.return_value = (0, '')
        self.assertEquals(d.is_authorized(user_info)[0], 0)

        check_user_can_view_record_patch.return_value = (1, '')
        self.assertEquals(d.is_authorized(user_info)[0], 1)

        check_user_can_view_record_patch.side_effect = \
            lambda user_info, recid: (recid % 2, '')

        # At least one record must be authorized
        self.assertEquals(d.is_authorized(user_info)[0], 0)

        # All records must be authorized
        self.app.config['RECORD_DOCUMENT_VIEWRESTR_POLICY'] = 'ALL'
        self.assertEquals(d.is_authorized(user_info)[0], 1)

        check_user_can_view_record_patch.side_effect = None
        check_user_can_view_record_patch.return_value = (0, '')

        self.assertEquals(d.is_authorized(user_info)[0], 0)


TEST_SUITE = make_test_suite(
    TestLegacyExport,
    TestMarcRecordCreation,
    TestRecord,
    TestRecordDocuments,
)

if __name__ == '__main__':
    run_test_suite(TEST_SUITE)
