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

"""Tests for communities model."""

import os
import shutil
from datetime import datetime, timedelta

from invenio.base.wrappers import lazy_import
from flask import url_for, current_app
from six import iteritems
from invenio.testsuite import InvenioTestCase, \
    make_test_suite, \
    run_test_suite
from invenio.ext.sqlalchemy import db
from flask_login import current_user

from invenio.modules.communities.config import COMMUNITIES_ID_PREFIX, \
    COMMUNITIES_ID_PREFIX_PROVISIONAL, \
    COMMUNITIES_OUTPUTFORMAT, \
    COMMUNITIES_OUTPUTFORMAT_PROVISIONAL

Community = lazy_import('invenio.modules.communities.models:Community')
Collection = lazy_import('invenio.modules.search.models:Collection')
calculate_rank_for_community = lazy_import('invenio.modules.communities.tasks:calculate_rank_for_community')

class CommunityModelTest(InvenioTestCase):

    test_name = 'test_comm'

    def setUp(self):
        Community.query.delete()
        self.login('admin', '')
        uid = current_user.get_id()
        data = {'id': self.test_name,
                'title': self.test_name}
        self.c = Community(id_user=uid, **data)
        db.session.add(self.c)
        db.session.commit()
        self.c.save_collections()

    def tearDown(self):
        self.c.delete_collections()
        self.logout()
        db.session.delete(self.c)
        db.session.commit()

    def _find_community_info(self):
        c = Community.query.filter_by(id=self.test_name).first()
        return c

    def test_1_new_community(self):
        """communities - create new community"""
        self.assertEqual(self._find_community_info().title, self.test_name)

    def test_2_community_collections(self):
        """communities - checks collections for community"""
        c = self._find_community_info()
        self.assertTrue(COMMUNITIES_ID_PREFIX + "-" + self.test_name,
                        c.collection.name)
        self.assertTrue(COMMUNITIES_ID_PREFIX_PROVISIONAL + "-" + self.test_name,
                        c.collection_provisional.name)

    def test_3_community_collections_formats(self):
        """communities - checks if formats were created for community"""
        c = self._find_community_info()
        self.assertEqual(c.collection.formats[0].format.code,
                         COMMUNITIES_OUTPUTFORMAT)
        self.assertEqual(c.collection_provisional.formats[0].format.code,
                         COMMUNITIES_OUTPUTFORMAT_PROVISIONAL)

    def test_4_community_protalboxes(self):
        """communities - checks if portalboxes were created for community"""
        c = self._find_community_info()
        self.assertTrue(len(c.collection.portalboxes[0].portalbox.body) > 0)
        self.assertTrue(len(c.collection_provisional.portalboxes[0].portalbox.body) > 0)

    def test_5_delete_community(self):
        """communities - delete community"""
        from invenio.config import CFG_TMPSHAREDDIR
        exists = os.path.exists(CFG_TMPSHAREDDIR)
        if not exists:
            os.mkdir(CFG_TMPSHAREDDIR)
        c = self._find_community_info()
        c.delete_collections()
        db.session.delete(c)
        db.session.commit()
        if not exists:
            shutil.rmtree(CFG_TMPSHAREDDIR)
        self.assertEqual(self._find_community_info(), None)
        # Re-create the community collection.
        self.setUp()


class CommunityRankerTest(InvenioTestCase):

    test_name = 'test_comm'

    def _create_comunity(self, options={}):
        """
            Creates community and adds a collection to it.
            Collection has number of records set to 1.
        """
        c = Community()
        for key,value in iteritems(options):
            setattr(c, key, value)
        # add a collection with "one" record
        coll = Collection()
        coll.nbrecs = 1
        setattr(c, "collection", coll)
        return c

    def test_rank_community_with_one_record(self):
        """communities - test community rank basic"""
        c = self._create_comunity({'id': self.test_name,
                                   'id_user': 1,
                                   'last_record_accepted': datetime.now()-timedelta(days=100),
                                   'fixed_points': 0})
        self.assertEqual(calculate_rank_for_community(c, 2), 5)

    def test_rank_community_last_accepted(self):
        """communities - test community rank new record accepted"""
        c = self._create_comunity({'id': self.test_name,
                                   'id_user': 1,
                                   'last_record_accepted': datetime.now(),
                                   'fixed_points': 20})
        self.assertEqual(calculate_rank_for_community(c, 2), 29)


TEST_SUITE = make_test_suite(CommunityModelTest,
                             CommunityRankerTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
