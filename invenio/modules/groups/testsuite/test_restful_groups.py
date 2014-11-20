# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2014, 2015 CERN.
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

""" Test groups REST API. """

from invenio.base.wrappers import lazy_import
from invenio.ext.restful.utils import APITestCase
from invenio.testsuite import make_test_suite, run_test_suite


db = lazy_import('invenio.ext.sqlalchemy.db')


class TestGroupsRestfulAPI(APITestCase):

    """Test url /api/groups."""

    def setUp(self):
        """Setup test."""
        from invenio.modules.accounts.models import User, Usergroup, \
            UserUsergroup
        # create user
        self.user = User(
            email='inveniouser@example.com',
            _password='invenio',
            nickname='inveniouser')
        try:
            db.session.add(self.user)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        # create group 1
        self.group_1 = Usergroup(
            name='testsuite group 1',
            description='testsuite group 1 - description',
            join_policy=Usergroup.JOIN_POLICIES['VISIBLEEXTERNAL'],
            login_method=Usergroup.LOGIN_METHODS['INTERNAL']
        )

        # create group 2
        self.group_2 = Usergroup(
            name='testsuite group 2',
            description='testsuite group 2 - description',
            join_policy=Usergroup.JOIN_POLICIES['INVISIBLEOPEN'],
            login_method=Usergroup.LOGIN_METHODS['EXTERNAL']
        )

        try:
            db.session.add(self.group_1)
            db.session.add(self.group_2)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        # create connection user <--> group 1
        self.uug_1 = UserUsergroup(
            id_user=self.user.id,
            id_usergroup=self.group_1.id,
            user_status=UserUsergroup.USER_STATUS['ADMIN']
        )

        # create connection user <--> group 2
        self.uug_2 = UserUsergroup(
            id_user=self.user.id,
            id_usergroup=self.group_2.id,
            user_status=UserUsergroup.USER_STATUS['MEMBER']
        )

        try:
            db.session.add(self.uug_1)
            db.session.add(self.uug_2)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        # create oauth token
        self.create_oauth_token(
            self.user.id,
            scopes=['groups:read', 'groups:write'])

    def tearDown(self):
        """Run after every test."""
        from invenio.modules.accounts.models import User, Usergroup
        # remove oauth
        self.remove_oauth_token()

        # remove groups
        db.session.delete(
            Usergroup.query.filter_by(id=self.group_1.id).one())
        db.session.delete(
            Usergroup.query.filter_by(id=self.group_2.id).one())

        # remove user
        User.query.filter(User.nickname.in_([
            self.user.nickname,
        ])).delete(synchronize_session=False)

        db.session.commit()

    def test_get_groups(self):
        """Test GET /api/groups."""
        get_answer = self.get(
            endpoint='groupsresource',
            code=200,
        )

        answer = get_answer.json

        assert len(answer) == 2

        # check group 1
        groups = filter(lambda item: item['name'] == self.group_1.name, answer)
        assert len(groups) == 1
        group = groups[0]
        test_group = self.group_1
        assert group['name'] == test_group.name
        assert group['description'] == test_group.description
        assert group['login_method'] == test_group.login_method.value
        assert group['join_policy'] == test_group.join_policy.value

        # check group 2
        groups = filter(lambda item: item['name'] == self.group_2.name, answer)
        assert len(groups) == 1
        group = groups[0]
        test_group = self.group_2
        assert group['name'] == test_group.name
        assert group['description'] == test_group.description
        assert group['login_method'] == test_group.login_method.value
        assert group['join_policy'] == test_group.join_policy.value

    def test_get_groups_per_page_1(self):
        """Test GET /api/groups."""
        get_answer = self.get(
            endpoint='groupsresource',
            urlargs=dict(page=1, per_page=1),
            code=200,
        )

        answer = get_answer.json

        assert len(answer) == 1

    def test_post_group(self):
        """Test POST /api/groups."""
        from invenio.modules.accounts.models import Usergroup

        # create a group
        data = dict(
            name="[Testsuite] CERN IT group",
            join_policy='VISIBLEOPEN',
            login_method='INTERNAL',
            description="A group dedicated to CERN IT people"
        )
        get_answer = self.post(
            endpoint='groupsresource',
            data=data,
            code=200
        )

        group = get_answer.json

        assert group['name'] == data['name']
        assert group['description'] == data['description']
        assert group['login_method'] == data['login_method']
        assert group['join_policy'] == data['join_policy']

        # find the created group
        Usergroup.query.filter(
            Usergroup.name == group['name']
        ).one()

        # and delete it
        # FIXME
        db.session.delete(
            Usergroup.query.filter_by(id=group['id']).one())


TEST_SUITE = make_test_suite(TestGroupsRestfulAPI)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
