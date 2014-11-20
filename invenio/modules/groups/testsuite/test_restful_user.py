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


class TestUserRestfulAPI(APITestCase):

    """Test url /api/groups/[:id_usergroup]/users/[:id_user]."""

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

    def test_get_group_user(self):
        """Test GET /api/groups/[:id_usergroup]/users/[:id_user]."""
        from invenio.modules.accounts.models import UserUsergroup
        get_answer = self.get(
            endpoint='userresource',
            urlargs={
                'id_usergroup': self.group_1.id,
                'id_user': self.user_3.id,
            },
            code=200,
        )

        answer = get_answer.json

        test_uug = self.uug_31
        assert UserUsergroup.USER_STATUS[answer['user_status']] == \
            test_uug.user_status
        assert 'user_status_date' in answer
        assert 'user' in answer
        user = answer['user']
        test_user = test_uug.user
        assert user['nickname'] == test_user.nickname
        assert user['email'] == test_user.email
        assert user['id'] == test_user.id

    def test_get_group_user_404(self):
        """Test GET /api/groups/[:id_usergroup]/users/[:id_user]."""
        self.get(
            endpoint='userresource',
            urlargs={
                'id_usergroup': self.group_1.id,
                'id_user': self.user_2.id,
            },
            code=404,
        )

    def test_post_group_user(self):
        """Test POST /api/groups/[:id_usergroup]/users/[:id_user]."""
        from invenio.modules.accounts.models import UserUsergroup

        data = dict(
            user_status='PENDING'
        )

        get_answer = self.post(
            endpoint='userresource',
            urlargs={
                'id_usergroup': self.group_1.id,
                'id_user': self.user_2.id,
            },
            data=data,
            code=200,
        )

        answer = get_answer.json

        # check database
        test_uug = UserUsergroup.query.filter_by(
            id_user=self.user_2.id, id_usergroup=self.group_1.id
        ).one()
        assert UserUsergroup.USER_STATUS[data['user_status']] == \
            test_uug.user_status
        assert 'user_status_date' in answer
        assert 'user' in answer
        user = answer['user']
        test_user = test_uug.user
        assert user['nickname'] == test_user.nickname
        assert user['email'] == test_user.email
        assert user['id'] == test_user.id

        # check input and output
        assert data['user_status'] == answer['user_status']

        # remove uug from database
        db.session.delete(test_uug)

        db.session.commit()

    def test_post_group_user_401_not_enough_right(self):
        """Test POST /api/groups/[:id_usergroup]/users/[:id_user]."""
        data = dict(
            user_status='PENDING'
        )

        self.post(
            endpoint='userresource',
            urlargs={
                'id_usergroup': self.group_2.id,
                'id_user': self.user_2.id,
            },
            data=data,
            code=401,
        )

    def test_put_group_user(self):
        """Test PUT /api/groups/[:id_usergroup]/users/[:id_user]."""
        from invenio.modules.accounts.models import UserUsergroup

        data = dict(
            user_status='ADMIN'
        )

        get_answer = self.post(
            endpoint='userresource',
            urlargs={
                'id_usergroup': self.group_1.id,
                'id_user': self.user_3.id,
            },
            data=data,
            code=200,
        )

        answer = get_answer.json

        # check database
        test_uug = UserUsergroup.query.filter_by(
            id_user=self.user_3.id, id_usergroup=self.group_1.id
        ).one()
        assert UserUsergroup.USER_STATUS[data['user_status']] == \
            test_uug.user_status
        assert 'user_status_date' in answer
        assert 'user' in answer
        user = answer['user']
        test_user = test_uug.user
        assert user['nickname'] == test_user.nickname
        assert user['email'] == test_user.email
        assert user['id'] == test_user.id

        # check input and output
        assert data['user_status'] == answer['user_status']

    def test_put_group_user_401_not_enough_right(self):
        """Test PUT /api/groups/[:id_usergroup]/users/[:id_user]."""
        data = dict(
            user_status='ADMIN'
        )

        self.post(
            endpoint='userresource',
            urlargs={
                'id_usergroup': self.group_2.id,
                'id_user': self.user_3.id,
            },
            data=data,
            code=401,
        )

    def test_delete_group_user(self):
        """Test DELETE /api/groups/[:id_usergroup]/users/[:id_user]."""
        from invenio.modules.accounts.models import UserUsergroup

        self.delete(
            endpoint='userresource',
            urlargs={
                'id_usergroup': self.group_1.id,
                'id_user': self.user_3.id,
            },
            code=204,
        )

        # check database
        db_uug = UserUsergroup.query.filter(
            UserUsergroup.id_user == self.uug_31.id_user,
            UserUsergroup.id_usergroup == self.uug_31.id_usergroup
        ).first()

        assert db_uug is None

    def test_delete_group_user_401_not_enough_right(self):
        """Test DELETE /api/groups/[:id_usergroup]/users/[:id_user]."""
        self.delete(
            endpoint='userresource',
            urlargs={
                'id_usergroup': self.group_2.id,
                'id_user': self.user_3.id,
            },
            code=401,
        )


TEST_SUITE = make_test_suite(TestUserRestfulAPI)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
