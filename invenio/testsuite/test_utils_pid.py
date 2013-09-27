# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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
Persistent identifier utilities tests
"""

from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase
from invenio import pidutils

identifiers = [
    ('urn:isbn:0451450523', ['urn', ], ''),
    ('urn:isan:0000-0000-9E59-0000-O-0000-0000-2', ['urn', ], ''),
    ('urn:issn:0167-6423', ['urn', ], ''),
    ('urn:ietf:rfc:2648', ['urn', ], ''),
    ('urn:mpeg:mpeg7:schema:2001', ['urn', ], ''),
    ('urn:oid:2.16.840', ['urn', ], ''),
    ('urn:uuid:6e8bc430-9c3a-11d9-9669-0800200c9a66', ['urn', ], ''),
    ('urn:nbn:de:bvb:19-146642', ['urn', ], ''),
    ('urn:lex:eu:council:directive:2010-03-09;2010-19-UE', ['urn', ], ''),
    ('ark:/13030/tqb3kh97gh8w', ['ark'], ''),
    ('http://www.example.org/ark:/13030/tqb3kh97gh8w', ['ark', 'url'], ''),
    ('10.1016/j.epsl.2011.11.037', ['doi', 'handle'],
        '10.1016/j.epsl.2011.11.037'),
    ('doi:10.1016/j.epsl.2011.11.037', ['doi', 'handle'],
        '10.1016/j.epsl.2011.11.037'),
    ('http://dx.doi.org/10.1016/j.epsl.2011.11.037', ['doi', 'url', ],
        '10.1016/j.epsl.2011.11.037'),
    ('9783468111242', ['isbn', 'ean13'], ''),
    ('4006381333931', ['ean13'], ''),
    ('73513537', ['ean8'], ''),
    ('1562-6865', ['issn'], ''),  # 'eiss, ''n'
    ('10013/epic.10033', ['handle'], ''),
    ('hdl:10013/epic.10033', ['handle'], '10013/epic.10033'),
    ('http://hdl.handle.net/10013/epic.10033', ['handle', 'url'],
        '10013/epic.10033'),
    ('978-3-905673-82-1', ['isbn'], ''),
    ('0077-5606', ['issn'], ''),
    ('urn:lsid:ubio.org:namebank:11815', ['lsid', 'urn'], ''),
    ('0A9 2002 12B4A105 7', ['istc'], ''),
    ('1188-1534', ['issn'], ''),  # 'liss, ''n'
    ('12082125', ['pmid'], ''),
    ('pmid:12082125', ['pmid'], '12082125'),
    ('http://purl.oclc.org/foo/bar', ['purl', 'url'], ''),
    #('123456789999', ['upc'], ''),
    ('http://www.heatflow.und.edu/index2.html', ['url'], ''),
    ('urn:nbn:de:101:1-201102033592', ['urn'], ''),
    ('PMC2631623', ['pmcid'], ''),
    ('2011ApJS..192...18K', ['ads'], ''),
    ('ads:2011ApJS..192...18K', ['ads'], '2011ApJS..192...18K'),
    ('0000 0002 1825 0097', ['orcid', 'isni'], ''),
    ('0000-0002-1694-233X', ['orcid', 'isni'], ''),
    ('1422-4586-3573-0476', ['isni'], ''),
    ('arXiv:1310.2590', ['arxiv', ], '')
]


class PersistentIdentifierUtilities(InvenioTestCase):

    def test_detect_schemes(self):
        for i, expected_schemes, normalized_value in identifiers:
            schemes = pidutils.detect_identifier_schemes(i)
            self.assertEqual(
                schemes,
                expected_schemes,
                "Found %s for identifier %s, but expected %s" % (
                    schemes, i, expected_schemes
                )
            )

    def test_is_type(self):
        for i, schemes, normalized_value in identifiers:
            for s in schemes:
                self.assertTrue(getattr(pidutils, 'is_%s' % s)(i))

    def test_normalize_pid(self):
        for i, expected_schemes, normalized_value in identifiers:
            self.assertEqual(
                pidutils.normalize_pid(i, expected_schemes[0]),
                normalized_value or i
            )


TEST_SUITE = make_test_suite(PersistentIdentifierUtilities)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
