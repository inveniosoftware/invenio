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

"""Tests for community team model."""

from invenio.base.wrappers import lazy_import
from invenio.testsuite import InvenioTestCase, make_test_suite, run_test_suite
from invenio.ext.sqlalchemy import db

CommunityTeam = lazy_import('invenio.modules.communities.models:'
                            'CommunityTeam')
Community = lazy_import('invenio.modules.communities.models:Community')
Usergroup = lazy_import('invenio.modules.accounts.models:Usergroup')


class CommunityTeamModelTest(InvenioTestCase):

    def setUp(self):
        communityData = {'id': 'TEST_COMMUNITY',
                         'title': 'TEST_COMMUNITY'}
        usergroupData = {'name': 'TEST_UGROUP',
                         'description': 'TEST_DESC',
                         'join_policy': 'VO',
                         'login_method': 'INTERNAL'}
        communityteamData = {'id_community': communityData['id'],
                             'id_usergroup': usergroupData['id']}

        self.c = Community(id_user=1, **communityData)
        self.ug = Usergroup(**usergroupData)
        self.ct = CommunityTeam(**communityteamData)

        db.session.add_all([self.c, self.ug, self.ct])
        db.session.commit()

    def tearDown(self):
        db.session.delete(self.ct)
        db.session.delete(self.c)
        db.session.delete(self.ug)
        db.session.commit()

    def test_1_new_communityteam_created(self):
        """."""
        ct = CommunityTeam.query.filter(
            CommunityTeam.id_community == 'TEST_COMMUNITY').all()

        self.assertEqual(len(ct), 1)
        self.assertEqual(ct[0].team_rights, 'R')

    def test_2_deleting_community_imply_deleting_communityteam_and_team(self):
        """."""
        ct = CommunityTeam.query.filter(
            CommunityTeam.id_community == 'TEST_COMMUNITY').first()
        com = Community.query.filter(
            Community.id == 'TEST_COMMUNITY').first()
        ug = Usergroup.query.filter(
            Usergroup.name == 'TEST_UGROUP').first()

        self.assertNotEqual(ct, None)
        self.assertNotEqual(com, None)
        self.assertNotEqual(ug, None)

        db.session.delete(com)
        db.session.commit()

        ct = CommunityTeam.query.filter(
            CommunityTeam.id_community == 'TEST_COMMUNITY').first()
        com = Community.query.filter(
            Community.id == 'TEST_COMMUNITY').first()
        ug = Usergroup.query.filter(
            Usergroup.name == 'TEST_UGROUP').first()

        self.assertEqual(ct, None)
        self.assertEqual(com, None)
        self.assertEqual(ug, None)

    def test_3_deleting_usergroup_imply_deleting_only_communityteam(self):
        """."""
        ct = CommunityTeam.query.filter(
            CommunityTeam.id_community == 'TEST_COMMUNITY').first()
        com = Community.query.filter(
            Community.id == 'TEST_COMMUNITY').first()
        ug = Usergroup.query.filter(
            Usergroup.name == 'TEST_UGROUP').first()

        self.assertNotEqual(ct, None)
        self.assertNotEqual(com, None)
        self.assertNotEqual(ug, None)

        db.session.delete(ug)
        db.session.commit()

        ct = CommunityTeam.query.filter(
            CommunityTeam.id_community == 'TEST_COMMUNITY').first()
        com = Community.query.filter(
            Community.id == 'TEST_COMMUNITY').first()
        ug = Usergroup.query.filter(
            Usergroup.name == 'TEST_UGROUP').first()

        self.assertNotEqual(com, None)
        self.assertEqual(ct, None)
        self.assertEqual(ug, None)

TEST_SUITE = make_test_suite(CommunityTeamModelTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
