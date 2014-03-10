# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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

"""WebSubmit Unit Test Suite."""

__revision__ = "$Id$"

from invenio.testutils import InvenioTestCase
from invenio.testutils import make_test_suite, run_test_suite
from mock import MagicMock, patch

class WebSubmitAuthorFunctions(InvenioTestCase):
    def test_convert_json_to_field_value_dictionary(self):
        from invenio.websubmit_functions.process_authors_json import _convert_json_to_field_value_dictionary

        json = """{"items":[{"inspireid":"INSPIRE-00210892","cernccid":"371254","affiliation":"SLAC National Accelerator Laboratory","email":"asai@slac.stanford.edu","initials":"M.","name":"Asai, Makoto"},{"inspireid":"","cernccid":"747181","affiliation":"School of Physics, University of the Witwatersrand","email":"joseph.asare@cern.ch","initials":"J.","name":"Asare, Joseph"},{"inspireid":"INSPIRE-00001575","cernccid":"722949","affiliation":"KEK, High Energy Accelerator Research Organization","email":"masato.aoki@cern.ch","initials":"M.","name":"Aoki, Masato"},{"inspireid":"INSPIRE-00211056","cernccid":"652506","affiliation":"European Laboratory for Particle Physics, CERN","email":" Fernando.Pedrosa@cern.ch","initials":"F.","name":"Baltasar Dos Santos Pedrosa, Fernando"},{"inspireid":"INSPIRE-00399337","cernccid":"753637","affiliation":"Petersburg Nuclear Physics Institute","email":"artem.basalaev@cern.ch","initials":"A.","name":"Basalaev, Artem"}]}"""
        expected_output = [{'AUTHOR_EMAIL': u'asai@slac.stanford.edu', 'AUTHOR_FULLNAME': u'Asai, Makoto', 'AUTHOR_ID': u'AUTHOR|(INSPIRE)INSPIRE-00210892</subfield><subfield code="0">AUTHOR|(SzGeCERN)371254', 'AUTHOR_AFFILIATION': u'SLAC National Accelerator Laboratory', 'AUTHOR_CONTRIBUTION': ''}, {'AUTHOR_EMAIL': u'joseph.asare@cern.ch', 'AUTHOR_FULLNAME': u'Asare, Joseph', 'AUTHOR_ID': u'AUTHOR|(SzGeCERN)747181', 'AUTHOR_AFFILIATION': u'School of Physics, University of the Witwatersrand', 'AUTHOR_CONTRIBUTION': ''}, {'AUTHOR_EMAIL': u'masato.aoki@cern.ch', 'AUTHOR_FULLNAME': u'Aoki, Masato', 'AUTHOR_ID': u'AUTHOR|(INSPIRE)INSPIRE-00001575</subfield><subfield code="0">AUTHOR|(SzGeCERN)722949', 'AUTHOR_AFFILIATION': u'KEK, High Energy Accelerator Research Organization', 'AUTHOR_CONTRIBUTION': ''}, {'AUTHOR_EMAIL': u' Fernando.Pedrosa@cern.ch', 'AUTHOR_FULLNAME': u'Baltasar Dos Santos Pedrosa, Fernando', 'AUTHOR_ID': u'AUTHOR|(INSPIRE)INSPIRE-00211056</subfield><subfield code="0">AUTHOR|(SzGeCERN)652506', 'AUTHOR_AFFILIATION': u'European Laboratory for Particle Physics, CERN', 'AUTHOR_CONTRIBUTION': ''}, {'AUTHOR_EMAIL': u'artem.basalaev@cern.ch', 'AUTHOR_FULLNAME': u'Basalaev, Artem', 'AUTHOR_ID': u'AUTHOR|(INSPIRE)INSPIRE-00399337</subfield><subfield code="0">AUTHOR|(SzGeCERN)753637', 'AUTHOR_AFFILIATION': u'Petersburg Nuclear Physics Institute', 'AUTHOR_CONTRIBUTION': ''}]
        output = _convert_json_to_field_value_dictionary(json)
        assert expected_output == output

    @patch('invenio.websubmit_engine.ParamFromFile')
    @patch('invenio.websubmit_engine.PluginContainer')
    @patch('invenio.websubmit_engine.collect_user_info')
    def test_get_authors_from_allowed_sources(self, collect_user_info, PluginContainer, ParamFromFile):
        from invenio.websubmit_engine import get_authors_from_allowed_sources

        authors_sample_dict = [{'affiliation': u'KEK, High Energy Accelerator Research Organization', 'cernccid': u'722949', 'email': u'masato.aoki@cern.ch', 'firstname': u'Masato', 'initials': u'M.', 'inspireid': u'INSPIRE-00001575', 'lastname': u'Aoki'},{'affiliation': u'Harvard University, Department of Physics', 'cernccid': u'416501', 'email': u'morii@fas.harvard.edu', 'firstname': u'Masahiro', 'initials': u'M.', 'inspireid': u'INSPIRE-00108914', 'lastname': u'Morii'},{'affiliation': u'International Center for Elementary Particle Physics and Department of Physics, The University of Tokyo', 'cernccid': u'727439', 'email': u'masahiro.morinaga@cern.ch', 'firstname': u'Masahiro', 'initials': u'M.', 'inspireid': u'INSPIRE-00381150', 'lastname': u'Morinaga'},{'affiliation': u'Osaka University', 'cernccid': u'418640', 'email': u'nomachi@lns.sci.osaka-u.ac.jp', 'firstname': u'Masaharu', 'initials': u'M.', 'inspireid': u'INSPIRE-00111877', 'lastname': u'Nomachi'},{'affiliation': u'International Center for Elementary Particle Physics and Department of Physics, The University of Tokyo', 'cernccid': u'758549', 'email': u'yamatani@icepp.s.u-tokyo.ac.jp', 'firstname': u'Masahiro', 'initials': u'M.', 'inspireid': u'', 'lastname': u'Yamatani'}]

        def mock_author_source_query_function(author_name):
            return authors_sample_dict

        def PluginContainer_side_effect(*args, **kwargs):
            return {'test_source': {"query_function": mock_author_source_query_function}}

        params = ['test_source', 'test@mail.com']

        def ParamFromFile_side_effect(*args, **kwargs):
            if len(args) > 0:
                if "AUTHOR_SOURCES" in args[0]:
                    return params[0]
                elif "SuE" in args[0]:
                    return params[1]

        def collect_user_info_side_effect(*args, **kwargs):
            return {'email': 'test@mail.com'}

        ParamFromFile.side_effect = ParamFromFile_side_effect
        PluginContainer.side_effect = PluginContainer_side_effect
        collect_user_info.side_effect = collect_user_info_side_effect

        result, error = get_authors_from_allowed_sources('', '', '')

        assert ParamFromFile.call_count == 2
        assert PluginContainer.call_count == 1
        assert collect_user_info.call_count == 1
        assert authors_sample_dict == result

    def test__convert_record_authors_to_json(self):
        from invenio.websubmit_engine import _convert_record_authors_to_json

        expected_output = "{'items': [{'affiliation': 'Aachen, Tech. Hochsch.', 'name': 'Heister, A'}, {'name': 'Schael, S'}, {'name': 'Barate, R'}, {'name': 'Bruneliere, R'}, {'name': 'De Bonis, I'}, {'name': 'Decamp, D'}, {'name': 'Goy, C'}, {'name': 'Jezequel, S'}, {'name': 'Lees, J P'}, {'name': 'Martin, F'}, {'name': 'Merle, E'}, {'name': 'Minard, M N'}, {'name': 'Pietrzyk, B'}, {'name': 'Trocme, B'}, {'name': 'Boix, G'}, {'name': 'Bravo, S'}, {'name': 'Casado, M P'}, {'name': 'Chmeissani, M'}, {'name': 'Crespo, J M'}, {'name': 'Fernandez, E'}, {'name': 'Fernandez-Bosman, M'}, {'name': 'Garrido, L'}, {'name': 'Grauges, E'}, {'name': 'Lopez, J'}, {'name': 'Martinez, M'}, {'name': 'Merino, G'}, {'name': 'Miquel, R'}, {'name': 'Mir, L M'}, {'name': 'Pacheco, A'}, {'name': 'Paneque, D'}, {'name': 'Ruiz, H'}, {'name': 'Colaleo, A'}, {'name': 'Creanza, D'}, {'name': 'De Filippis, N'}, {'name': 'De Palma, M'}, {'name': 'Iaselli, G'}, {'name': 'Maggi, G'}, {'name': 'Maggi, M'}, {'name': 'Nuzzo, S'}, {'name': 'Ranieri, A'}, {'name': 'Raso, G'}, {'name': 'Ruggieri, F'}, {'name': 'Selvaggi, G'}, {'name': 'Silvestris, L'}, {'name': 'Tempesta, P'}, {'name': 'Tricomi, A'}, {'name': 'Zito, G'}, {'name': 'Huang, X'}, {'name': 'Lin, J'}, {'name': 'Ouyang, Q'}, {'name': 'Wang, T'}, {'name': 'Xie, Y'}, {'name': 'Xu, R'}, {'name': 'Xue, S'}, {'name': 'Zhang, J'}, {'name': 'Zhang, L'}, {'name': 'Zhao, W'}, {'name': 'Abbaneo, D'}, {'name': 'Azzurri, P'}, {'name': 'Barklow, T'}, {'name': 'Buchmuller, O'}, {'name': 'Cattaneo, M'}, {'name': 'Cerutti, F'}, {'name': 'Clerbaux, B'}, {'name': 'Drevermann, H'}, {'name': 'Forty, R W'}, {'name': 'Frank, M'}, {'name': 'Gianotti, F'}, {'name': 'Greening, T C'}, {'name': 'Hansen, J B'}, {'name': 'Harvey, J'}, {'name': 'Hutchcroft, D E'}, {'name': 'Janot, P'}, {'name': 'Jost, B'}, {'name': 'Kado, M'}, {'name': 'Maley, P'}, {'name': 'Mato, P'}, {'name': 'Moutoussi, A'}, {'name': 'Ranjard, F'}, {'name': 'Rolandi, L'}, {'name': 'Schlatter, D'}, {'name': 'Sguazzoni, G'}, {'name': 'Tejessy, W'}, {'name': 'Teubert, F'}, {'name': 'Valassi, A'}, {'name': 'Videau, I'}, {'name': 'Ward, J J'}, {'name': 'Badaud, F'}, {'name': 'Dessagne, S'}, {'name': 'Falvard, A'}, {'name': 'Fayolle, D'}, {'name': 'Gay, P'}, {'name': 'Jousset, J'}, {'name': 'Michel, B'}, {'name': 'Monteil, S'}, {'name': 'Pallin, D'}, {'name': 'Pascolo, J M'}, {'name': 'Perret, P'}, {'name': 'Hansen, J D'}, {'name': 'Hansen, J R'}, {'name': 'Hansen, P H'}, {'name': 'Nilsson, B S'}, {'name': 'Waananen, A'}, {'name': 'Kyriakis, A'}, {'name': 'Markou, C'}, {'name': 'Simopoulou, E'}, {'name': 'Vayaki, A'}, {'name': 'Zachariadou, K'}, {'name': 'Blondel, A'}, {'name': 'Brient, J C'}, {'name': 'Machefert, F P'}, {'name': 'Rouge, A'}, {'name': 'Swynghedauw, M'}, {'name': 'Tanaka, R'}, {'name': 'Videau, H L'}, {'name': 'Ciulli, V'}, {'name': 'Focardi, E'}, {'name': 'Parrini, G'}, {'name': 'Antonelli, A'}, {'name': 'Antonelli, M'}, {'name': 'Bencivenni, G'}, {'name': 'Bologna, G'}, {'name': 'Bossi, F'}, {'name': 'Campana, P'}, {'name': 'Capon, G'}, {'name': 'Chiarella, V'}, {'name': 'Laurelli, P'}, {'name': 'Mannocchi, G'}, {'name': 'Murtas, F'}, {'name': 'Murtas, G P'}, {'name': 'Passalacqua, L'}, {'name': 'Pepe-Altarelli, M'}, {'name': 'Spagnolo, P'}, {'name': 'Kennedy, J'}, {'name': 'Lynch, J G'}, {'name': 'Negus, P'}, {'name': 'O'Shea, V'}, {'name': 'Smith, D'}, {'name': 'Thompson, A S'}, {'name': 'Wasserbaech, S R'}, {'name': 'Cavanaugh, R'}, {'name': 'Dhamotharan, S'}, {'name': 'Geweniger, C'}, {'name': 'Hanke, P'}, {'name': 'Hepp, V'}, {'name': 'Kluge, E E'}, {'name': 'Leibenguth, G'}, {'name': 'Putzer, A'}, {'name': 'Stenzel, H'}, {'name': 'Tittel, K'}, {'name': 'Werner, S'}, {'name': 'Wunsch, M'}, {'name': 'Beuselinck, R'}, {'name': 'Binnie, D M'}, {'name': 'Cameron, W'}, {'name': 'Davies, G'}, {'name': 'Dornan, P J'}, {'name': 'Girone, M'}, {'name': 'Hill, R D'}, {'name': 'Marinelli, N'}, {'name': 'Nowell, J'}, {'name': 'Przysiezniak, H'}, {'name': 'Rutherford, S A'}, {'name': 'Sedgbeer, J K'}, {'name': 'Thompson, J C'}, {'name': 'White, R'}, {'name': 'Ghete, V M'}, {'name': 'Girtler, P'}, {'name': 'Kneringer, E'}, {'name': 'Kuhn, D'}, {'name': 'Rudolph, G'}, {'name': 'Bouhova-Thacker, E'}, {'name': 'Bowdery, C K'}, {'name': 'Clarke, D P'}, {'name': 'Ellis, G'}, {'name': 'Finch, A J'}, {'name': 'Foster, F'}, {'name': 'Hughes, G'}, {'name': 'Jones, R W L'}, {'name': 'Pearson, M R'}, {'name': 'Robertson, N A'}, {'name': 'Smizanska, M'}, {'name': 'Lema\\u00eetre, V'}, {'name': 'Blumenschein, U'}, {'name': 'Holldorfer, F'}, {'name': 'Jakobs, K'}, {'name': 'Kayser, F'}, {'name': 'Kleinknecht, K'}, {'name': 'Muller, A S'}, {'name': 'Quast, G'}, {'name': 'Renk, B'}, {'name': 'Sander, H G'}, {'name': 'Schmeling, S'}, {'name': 'Wachsmuth, H'}, {'name': 'Zeitnitz, C'}, {'name': 'Ziegler, T'}, {'name': 'Bonissent, A'}, {'name': 'Carr, J'}, {'name': 'Coyle, P'}, {'name': 'Curtil, C'}, {'name': 'Ealet, A'}, {'name': 'Fouchez, D'}, {'name': 'Leroy, O'}, {'name': 'Kachelhoffer, T'}, {'name': 'Payre, P'}, {'name': 'Rousseau, D'}, {'name': 'Tilquin, A'}, {'name': 'Ragusa, F'}, {'name': 'David, A'}, {'name': 'Dietl, H'}, {'name': 'Ganis, G'}, {'name': 'Huttmann, K'}, {'name': 'Lutjens, G'}, {'name': 'Mannert, C'}, {'name': 'Manner, W'}, {'name': 'Moser, H G'}, {'name': 'Settles, R'}, {'name': 'Wolf, G'}, {'name': 'Boucrot, J'}, {'name': 'Callot, O'}, {'name': 'Davier, M'}, {'name': 'Duflot, L'}, {'name': 'Grivaz, J F'}, {'name': 'Heusse, P'}, {'name': 'Jacholkowska, A'}, {'name': 'Loomis, C'}, {'name': 'Serin, L'}, {'name': 'Veillet, J J'}, {'name': 'De Vivie de Regie, J B'}, {'name': 'Yuan, C'}, {'name': 'Bagliesi, G'}, {'name': 'Boccali, T'}, {'name': 'Fo\\u00e0, L'}, {'name': 'Giammanco, A'}, {'name': 'Giassi, A'}, {'name': 'Ligabue, F'}, {'name': 'Messineo, A'}, {'name': 'Palla, F'}, {'name': 'Sanguinetti, G'}, {'name': 'Sciaba, A'}, {'name': 'Tenchini, R'}, {'name': 'Venturi, A'}, {'name': 'Verdini, P G'}, {'name': 'Awunor, O'}, {'name': 'Blair, G A'}, {'name': 'Coles, J'}, {'name': 'Cowan, G'}, {'name': 'Garc\\u00eda-Bellido, A'}, {'name': 'Green, M G'}, {'name': 'Jones, L T'}, {'name': 'Medcalf, T'}, {'name': 'Misiejuk, A'}, {'name': 'Strong, J A'}, {'name': 'Teixeira-Dias, P'}, {'name': 'Clifft, R W'}, {'name': 'Edgecock, T R'}, {'name': 'Norton, P R'}, {'name': 'Tomalin, I R'}, {'name': 'Bloch-Devaux, B'}, {'name': 'Boumediene, D'}, {'name': 'Colas, P'}, {'name': 'Fabbro, B'}, {'name': 'Lancon, E'}, {'name': 'Lemaire, M C'}, {'name': 'Locci, E'}, {'name': 'Perez, P'}, {'name': 'Rander, J'}, {'name': 'Renardy, J F'}, {'name': 'Rosowsky, A'}, {'name': 'Seager, P'}, {'name': 'Trabelsi, A'}, {'name': 'Tuchming, B'}, {'name': 'Vallage, B'}, {'name': 'Konstantinidis, N P'}, {'name': 'Litke, A M'}, {'name': 'Taylor, G'}, {'name': 'Booth, C N'}, {'name': 'Cartwright, S'}, {'name': 'Combley, F'}, {'name': 'Hodgson, P N'}, {'name': 'Lehto, M H'}, {'name': 'Thompson, L F'}, {'name': 'Affholderbach, K'}, {'name': 'Bohrer, A'}, {'name': 'Brandt, S'}, {'name': 'Grupen, C'}, {'name': 'Hess, J'}, {'name': 'Ngac, A'}, {'name': 'Prange, G'}, {'name': 'Sieler, U'}, {'name': 'Borean, C'}, {'name': 'Giannini, G'}, {'name': 'He, H'}, {'name': 'Putz, J'}, {'name': 'Rothberg, J E'}, {'name': 'Armstrong, S R'}, {'name': 'Berkelman, K'}, {'name': 'Cranmer, K'}, {'name': 'Ferguson, D P S'}, {'name': 'Gao, Y'}, {'name': 'Gonzalez, S'}, {'name': 'Hayes, O J'}, {'name': 'Hu, H'}, {'name': 'Jin, S'}, {'name': 'Kile, J'}, {'name': 'McNamara, P A'}, {'name': 'Nielsen, J'}, {'name': 'Pan, Y B'}, {'name': 'Von Wimmersperg-Toller, J H'}, {'name': 'Wiedenmann, W'}, {'name': 'Wu, J'}, {'name': 'Wu, S L'}, {'name': 'Wu, X'}, {'name': 'Zobernig, G'}, {'name': 'Dissertori, G'}]}"
        output = _convert_record_authors_to_json(10)
        assert expected_output == output

TEST_SUITE = make_test_suite(WebSubmitAuthorFunctions)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
