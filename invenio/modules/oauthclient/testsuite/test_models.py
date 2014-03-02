from __future__ import absolute_import

from invenio.testsuite import InvenioTestCase
from invenio.ext.sqlalchemy import db


class BaseTestCase(InvenioTestCase):
    def setUp(self):
        from ..models import RemoteAccount, RemoteToken
        RemoteToken.query.delete()
        RemoteAccount.query.delete()
        db.session.commit()
        db.session.expunge_all()

    def tearDown(self):
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
    def test_get_create(self):
        from ..models import RemoteAccount, RemoteToken

        t = RemoteToken.create(2, "dev", "mytoken", "mysecret")
        assert t
        assert t.token() == ('mytoken', 'mysecret')

        acc = RemoteAccount.get(2, "dev")
        assert acc
        assert t.remote_account.id == acc.id
        assert t.token_type == ''

        t2 = RemoteToken.create(
            2, "dev", "mytoken2", "mysecret2",
            token_type='t2'
        )
        assert t2.remote_account.id == acc.id
        assert t2.token_type == 't2'

        t3 = RemoteToken.get(2, "dev")
        t4 = RemoteToken.get(2, "dev", token_type="t2")
        assert t4.token() != t3.token()

        assert RemoteToken.query.count() == 2
        acc.delete()
        assert RemoteToken.query.count() == 0
