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

from __future__ import absolute_import

from invenio.ext.sqlalchemy import db

from invenio.testsuite import InvenioTestCase, make_test_suite, run_test_suite


class BaseTestCase(InvenioTestCase):
    def setUp(self):
        from ..models import RemoteAccount, RemoteToken
        RemoteToken.query.delete()
        RemoteAccount.query.delete()
        db.session.commit()
        db.session.expunge_all()

    def tearDown(self):
        from ..models import RemoteAccount, RemoteToken
        RemoteToken.query.delete()
        RemoteAccount.query.delete()
        db.session.commit()
        db.session.expunge_all()
        db.session.expunge_all()


class RemoteAccountTestCase(BaseTestCase):
    def test_get_create(self):
        from ..models import RemoteAccount

        created_acc = RemoteAccount.create(1, "dev", dict(somekey="somevalue"))
        assert created_acc

        retrieved_acc = RemoteAccount.get(1, "dev")
        assert created_acc.id == retrieved_acc.id
        assert retrieved_acc.extra_data == dict(somekey="somevalue")

        db.session.delete(retrieved_acc)
        assert RemoteAccount.get(1, "dev") is None


class RemoteTokenTestCase(BaseTestCase):
    def setUp(self):
        super(RemoteTokenTestCase, self).setUp()
        from invenio_accounts.models import User
        u1 = User(nickname='RemoteTokenTestCaseUser1', password='')
        u2 = User(nickname='RemoteTokenTestCaseUser2', password='')
        u3 = User(nickname='RemoteTokenTestCaseUser3', password='')
        db.session.add(u1)
        db.session.add(u2)
        db.session.add(u3)
        db.session.commit()

        self.u1 = u1.id
        self.u2 = u2.id
        self.u3 = u3.id
        db.session.expunge_all()

    def tearDown(self):
        super(RemoteTokenTestCase, self).tearDown()
        from invenio_accounts.models import User
        User.query.filter_by(id=self.u1).delete()
        User.query.filter_by(id=self.u2).delete()
        User.query.filter_by(id=self.u3).delete()
        db.session.commit()
        db.session.expunge_all()

    def test_get_create(self):
        from ..models import RemoteAccount, RemoteToken

        t = RemoteToken.create(self.u1, "dev", "mytoken", "mysecret")
        assert t
        assert t.token() == ('mytoken', 'mysecret')

        acc = RemoteAccount.get(self.u1, "dev")
        assert acc
        assert t.remote_account.id == acc.id
        assert t.token_type == ''

        t2 = RemoteToken.create(
            self.u1, "dev", "mytoken2", "mysecret2",
            token_type='t2'
        )
        assert t2.remote_account.id == acc.id
        assert t2.token_type == 't2'

        t3 = RemoteToken.get(self.u1, "dev")
        t4 = RemoteToken.get(self.u1, "dev", token_type="t2")
        assert t4.token() != t3.token()

        assert RemoteToken.query.count() == 2
        acc.delete()
        assert RemoteToken.query.count() == 0

    def test_get_regression(self):
        from ..models import RemoteToken

        t3 = RemoteToken.create(self.u2, "dev", "mytoken", "mysecret")
        t4 = RemoteToken.create(self.u3, "dev", "mytoken", "mysecret")

        assert RemoteToken.get(self.u2, "dev").remote_account.user_id == \
            t3.remote_account.user_id
        assert RemoteToken.get(self.u3, "dev").remote_account.user_id == \
            t4.remote_account.user_id


TEST_SUITE = make_test_suite(RemoteAccountTestCase, RemoteTokenTestCase)


if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
