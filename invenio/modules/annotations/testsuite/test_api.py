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

__revision__ = "$Id$"

from datetime import datetime

from invenio.base.wrappers import lazy_import
from invenio.testsuite import make_test_suite, run_test_suite, nottest, \
    InvenioTestCase

CFG = lazy_import('invenio.base.globals.cfg')
USER = lazy_import('invenio.modules.accounts.models.User')
API = lazy_import('invenio.modules.annotations.api')
NOTEUTILS = lazy_import('invenio.modules.annotations.noteutils')
COMMENT = lazy_import('invenio.modules.comments.models.CmtRECORDCOMMENT')


class AnnotationTestCase(InvenioTestCase):

    def setUp(self):
        self.app.config['ANNOTATIONS_ENGINE'] = \
            "invenio.modules.jsonalchemy.jsonext.engines.memory:MemoryStorage"


class TestAnnotation(AnnotationTestCase):

    def test_initialization(self):
        u = USER(id=1)
        a = API.Annotation.create({"who": u, "what": "lorem", "where": "/"})
        self.assert_(len(a.validate()) == 0)
        self.assert_(type(a["when"]) == datetime)
        self.assert_(a["who"].get_id() == 1)

        # invalid annotation
        a = API.Annotation.create({"who": u, "what": "lorem", "where": "/",
                                   "perm": {"public": True, "groups": []},
                                   "uuid": "1m"})
        self.assert_(len(a.validate()) == 1)

    def test_jsonld(self):
        u = USER(id=1, nickname="johndoe")
        a = API.Annotation.create({"who": u, "what": "lorem", "where": "/",
                                   "perm": {"public": True, "groups": []}})
        ld = a.get_jsonld("oaf")
        self.assert_(ld["hasTarget"]["@id"] == CFG["CFG_SITE_URL"] + "/")
        self.assert_(ld["hasBody"]["chars"] == "lorem")


class TestJSONLD(AnnotationTestCase):

    @nottest
    def test(self):
        u = USER(id=1)
        data = {"who": u, "what": "lorem",
                "where": {"record": 1, "marker": "P.1_T.2a.2_L.100"},
                "comment": 1}
        a = API.add_annotation(model='annotation_note', **data)

        # JSONAlchemy issue with overwriting fields
        self.assert_(len(a.validate()) == 0)

        ld = a.get_jsonld("oaf",
                          new_context={"ST": "http://www.w3.org/ns/oa#"
                                             "FragmentSelector"},
                          format="compacted")

        self.assert_(ld["http://www.w3.org/ns/oa#hasTarget"]
                       ["http://www.w3.org/ns/oa#hasSelector"]
                       ["@type"] == "ST")
        self.assert_(ld["http://www.w3.org/ns/oa#hasTarget"]
                       ["http://www.w3.org/ns/oa#hasSelector"]
                       ["http://www.w3.org/1999/02/22-rdf-syntax-ns#value"] ==
                     "P.1_T.2a.2_L.100")


TEST_SUITE = make_test_suite(TestAnnotation, TestJSONLD)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
