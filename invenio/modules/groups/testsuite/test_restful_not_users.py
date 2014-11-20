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


class TestNotUsersRestfulAPI(APITestCase):

    """Test url /api/groups/[:id_usergroup]/not-users."""

    def setUp(self):
        """Setup test."""
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

    def test_get_not_users(self):
        """Test GET /api/groups/[:id_usergroup]/not-users."""
        pass


TEST_SUITE = make_test_suite(TestNotUsersRestfulAPI)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
