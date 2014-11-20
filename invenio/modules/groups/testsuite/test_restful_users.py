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


class TestUsersRestfulAPI(APITestCase):

    """Test url /api/groups/[:id_usergroup]/users."""

    def setUp(self):
        """Setup test."""
        from invenio.modules.accounts.models import User, Usergroup, \
            UserUsergroup

        # create users
        self.user_1 = User(email='inveniouser1@example.com',
                           _password='invenio1',
                           nickname='inveniouser1')
        self.user_2 = User(email='inveniouser2@example.com',
                           _password='invenio2',
                           nickname='inveniouser2')
        self.user_3 = User(email='inveniouser3@example.com',
                           _password='invenio3',
                           nickname='inveniouser3')
        try:
            db.session.add(self.user_1)
            db.session.add(self.user_2)
            db.session.add(self.user_3)
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

        # create connection user 1 <--> group 1
        self.uug_11 = UserUsergroup(
            id_user=self.user_1.id,
            id_usergroup=self.group_1.id,
            user_status=UserUsergroup.USER_STATUS['ADMIN']
        )

        # create connection user 3 <--> group 2
        self.uug_32 = UserUsergroup(
            id_user=self.user_3.id,
            id_usergroup=self.group_2.id,
            user_status=UserUsergroup.USER_STATUS['ADMIN']
        )

        # create connection user 3 <--> group 1
        self.uug_31 = UserUsergroup(
            id_user=self.user_3.id,
            id_usergroup=self.group_1.id,
            user_status=UserUsergroup.USER_STATUS['MEMBER']
        )

        try:
            db.session.add(self.uug_11)
            db.session.add(self.uug_32)
            db.session.add(self.uug_31)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        # create oauth token
        self.create_oauth_token(
            self.user_1.id,
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

        # remove users
        User.query.filter(User.nickname.in_([
            self.user_1.nickname,
            self.user_2.nickname,
            self.user_3.nickname,
        ])).delete(synchronize_session=False)

        db.session.commit()

    def test_get_group_users(self):
        """Test GET /api/groups/[:id_usergroup]/users."""
        from invenio.modules.accounts.models import UserUsergroup
        get_answer = self.get(
            endpoint='usersresource',
            urlargs={
                'id_usergroup': self.group_1.id
            },
            code=200,
        )

        answer = get_answer.json

        assert len(answer) == 2

        # check response 1
        uugs = filter(lambda item: item['user']['nickname'] == self.user_1.nickname, answer)
        assert len(uugs) == 1
        uug = uugs[0]
        test_uug = self.uug_11
        assert UserUsergroup.USER_STATUS[uug['user_status']] == \
            test_uug.user_status
        assert 'user_status_date' in uug
        assert 'user' in uug
        user = uug['user']
        test_user = test_uug.user
        assert user['nickname'] == test_user.nickname
        assert user['email'] == test_user.email
        assert user['id'] == test_user.id

        # check response 2
        uugs = filter(lambda item: item['user']['nickname'] == self.user_3.nickname, answer)
        assert len(uugs) == 1
        uug = uugs[0]
        test_uug = self.uug_31
        assert UserUsergroup.USER_STATUS[uug['user_status']] == \
            test_uug.user_status
        assert 'user_status_date' in uug
        assert 'user' in uug
        user = uug['user']
        test_user = test_uug.user
        assert user['nickname'] == test_user.nickname
        assert user['email'] == test_user.email
        assert user['id'] == test_user.id

    def test_get_group_users_per_page_1(self):
        """Test GET /api/groups/[:id_usergroup]/users."""
        get_answer = self.get(
            endpoint='usersresource',
            urlargs={
                'id_usergroup': self.group_1.id,
                'page': 1,
                'per_page': 1,
            },
            code=200,
        )

        answer = get_answer.json

        assert len(answer) == 1

TEST_SUITE = make_test_suite(TestUsersRestfulAPI)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
