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

"""Tests for featured community model."""

import datetime

from invenio.base.wrappers import lazy_import
from invenio.testsuite import InvenioTestCase, make_test_suite, run_test_suite
from invenio.ext.sqlalchemy import db

FeaturedCommunity = lazy_import('invenio.modules.communities.models:'
                                'FeaturedCommunity')
Community = lazy_import('invenio.modules.communities.models:Community')


class FeaturedCommunityModelTest(InvenioTestCase):

    test_name = "test_featured_comm"
    test_day = datetime.datetime(2010, 10, 10)

    def setUp(self):
        FeaturedCommunity.query.delete()

        withStartDate = {'id': 1,
                         'id_community': self.test_name,
                         'start_date': self.test_day}
        withoutStartDate = {'id': 2,
                            'id_community': self.test_name}
        communityData = {'id': self.test_name,
                         'title': self.test_name}

        self.fc1 = FeaturedCommunity(**withStartDate)
        self.fc2 = FeaturedCommunity(**withoutStartDate)
        self.c = Community(id_user=1, **communityData)

        db.session.add_all([self.fc1, self.fc2, self.c])
        db.session.commit()

    def tearDown(self):
        db.session.delete(self.fc1)
        db.session.delete(self.fc2)
        db.session.delete(self.c)
        db.session.commit()

    def test_1_new_feature_community(self):
        """communities - creates new featured community."""
        fc = FeaturedCommunity.query.filter_by(
            id_community=self.test_name).first()
        self.assertEqual(fc.id_community, self.test_name)

    def test_2_default_start_date(self):
        """communities - checks if start_date is set to today by default."""
        date = FeaturedCommunity.query.get(2).start_date.date()
        self.assertEqual(date, datetime.date.today())

    def test_3_get_latest_featured_community(self):
        """communities - get latest featured community."""
        fc = FeaturedCommunity.get_current()
        self.assertEqual(fc.community.id, self.test_name)


TEST_SUITE = make_test_suite(FeaturedCommunityModelTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
