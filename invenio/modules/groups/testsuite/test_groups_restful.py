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

""" Test groups REST API. """

from invenio.testsuite import make_test_suite, run_test_suite
from invenio.base.wrappers import lazy_import
from invenio.ext.restful.utils import APITestCase

db = lazy_import('invenio.ext.sqlalchemy.db')


class TestGroupsRestfulAPI(APITestCase):

    def setUp(self):
        from invenio.modules.accounts.models import User

        self.user = User(email='inveniouser@example.com', _password='invenio',
                         nickname='inveniouser')
        try:
            db.session.add(self.user)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        self.create_oauth_token(self.user.id, scopes=[""])

    def tearDown(self):
        """Run after every test."""
        from invenio.modules.accounts.models import User

        self.remove_oauth_token()
        User.query.filter(User.nickname.in_([
            self.user.nickname,
        ])).delete(synchronize_session=False)
        db.session.commit()

    def test_create_delete_group(self):
        from invenio.modules.accounts.models import Usergroup

        # create a group
        data = dict(
            name="CERN IT group",
            join_policy="VO",
            login_method="INTERNAL",
            description="A group dedicated to CERN IT people"
        )
        response = self.post(
            endpoint='userresource',
            user_id=self.user.id,
            data=data,
            code=201
        )
        self.assertEqual(response.json['name'], data['name'])

        # find the created group
        group = Usergroup.query.filter(
            Usergroup.name == response.json['name']
        ).one()

        # and delete it
        self.delete(
            endpoint='groupresource',
            user_id=self.user.id,
            urlargs=dict(id_usergroup=group.id),
            code=204
        )

    def test_get_groups_of_user(self):
        self.get(
            endpoint='userresource',
            user_id=self.user.id,
            data='',
            urlargs=dict(page=1),
            code=400
        )

TEST_SUITE = make_test_suite(TestGroupsRestfulAPI)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
