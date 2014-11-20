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


class TestGroupRestfulAPI(APITestCase):

    """Test url /api/groups/[:id_usergroup]."""

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

    def test_get_group(self):
        """Test GET /api/groups/[:id_usergroup]."""
        get_answer = self.get(
            endpoint='groupresource',
            urlargs={
                'id_usergroup': self.group_1.id
            },
            code=200,
        )

        group = get_answer.json

        assert group['name'] == self.group_1.name
        assert group['description'] == self.group_1.description
        assert group['login_method'] == self.group_1.login_method.value
        assert group['join_policy'] == self.group_1.join_policy.value

    def test_put_group(self):
        """Test PUT /api/groups/[:id_usergroup]."""
        from invenio.modules.accounts.models import Usergroup
        # update first group
        data = dict(
            name="[Testsuite update] CERN IT group",
            join_policy='VISIBLEEXTERNAL',
            login_method='EXTERNAL',
            description="Test update group information.."
        )
        get_answer = self.put(
            endpoint='groupresource',
            urlargs={
                'id_usergroup': self.group_1.id
            },
            data=data,
            code=200
        )

        group = get_answer.json

        # check returned values
        assert group['name'] == data['name']
        assert group['description'] == data['description']
        assert group['login_method'] == data['login_method']
        assert group['join_policy'] == data['join_policy']

        # find the created group
        db_group = Usergroup.query.filter(
            Usergroup.name == group['name']
        ).one()

        # check db information
        assert db_group.name == data['name']
        assert db_group.description == data['description']
        assert db_group.login_method \
            == Usergroup.LOGIN_METHODS[data['login_method']]
        assert db_group.join_policy \
            == Usergroup.JOIN_POLICIES[data['join_policy']]

    def test_delete_group(self):
        """Test DELETE /api/groups/[:id_usergroup]."""
        from invenio.modules.accounts.models import Usergroup, UserUsergroup

        # create group 3
        self.group_3 = Usergroup(
            name='testsuite group 3',
            description='testsuite group 3 - description',
            join_policy=Usergroup.JOIN_POLICIES['VISIBLEEXTERNAL'],
            login_method=Usergroup.LOGIN_METHODS['INTERNAL']
        )

        try:
            db.session.add(self.group_3)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        # create connection user <--> group 3
        self.uug_3 = UserUsergroup(
            id_user=self.user.id,
            id_usergroup=self.group_3.id,
            user_status=UserUsergroup.USER_STATUS['ADMIN']
        )

        try:
            db.session.add(self.uug_3)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        # delete group 3
        self.delete(
            endpoint='groupresource',
            urlargs={
                'id_usergroup': self.group_3.id
            },
            code=204
        )

        # check if is deleted in database
        db_group = Usergroup.query.filter(
            Usergroup.name == self.group_3.name
        ).first()

        assert db_group is None

TEST_SUITE = make_test_suite(TestGroupRestfulAPI)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
