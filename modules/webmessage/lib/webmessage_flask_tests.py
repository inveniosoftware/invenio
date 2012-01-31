import base64
from flask import current_app, request
from invenio.sqlalchemyutils import db
from invenio.webmessage_config import CFG_WEBMESSAGE_STATUS_CODE
from flask import session, g

from invenio.testutils import make_flask_test_suite, run_test_suite, \
                              FlaskSQLAlchemyTest

from fixture import SQLAlchemyFixture
from invenio.webaccount_fixtures import UserData

#class UsergroupData(DataSet):
#    class thesisViewers:
#        name = 'Theses viewers'
#        all_users = set([UserData.romeo, UserData.juliet])
#    class montagueFamily:
#        name = 'montague-family'

## This was used when there are subtransactions in test.
#class FlaskSQLAlchemyFixture(SQLAlchemyFixture):
#    def create_transaction(self):
#        if self.connection is not None:
#            transaction = self.session.begin(subtransactions=True)
#        else:
#            transaction = self.session.begin(subtransactions=True)
#        return transaction

from invenio.websession_model import *
from invenio.webmessage_model import *

fixture = SQLAlchemyFixture(
        env={'UserData': User},
        engine=db.metadata.bind,
        session=db.session
        )


class MsgMESSAGETest(FlaskSQLAlchemyTest):

    @fixture.with_data(UserData)
    def test_index(data, self):
        users = data.UserData

        admin = User.query.filter(User.nickname.like('admin')).one()
        romeo = User.query.filter(User.nickname.like('romeo')).one()
        juliet= User.query.filter(User.nickname.like('juliet')).one()

        m = MsgMESSAGE()
        m.subject = 'Message 1 Subject'
        m.body = 'body'
        try:
            m.sent_to_user_nicks = 'admin, NOTEXISTS'
        except:
            assert m.sent_to_user_nicks == None
        m.sent_to_user_nicks = ', '.join([users.admin.nickname,
                                          users.romeo.nickname])

        try:
            m.sent_to_user_nicks = 'admin, NOTEXISTS'
        except:
            # Remove unnecessary space
            assert m.sent_to_user_nicks == ','.join([users.admin.nickname,
                                                     users.romeo.nickname])


        m.sent_to_group_names = ''
        m.id_user_from = users.admin.id
        db.session.add(m)
        db.session.commit()

        m = MsgMESSAGE.query.first()
        assert admin in m.recipients
        assert romeo in m.recipients
        assert juliet not in m.recipients

        response = self.login(users.admin.nickname, users.admin.password)
        assert '<p class="flash-info">You have been logged in.</p>' in response.data
        response = self.client.get("/yourmessages/", follow_redirects=True)
        assert 'Message 1 Subject' in response.data
        self.logout()

        response = self.login(users.romeo.nickname, users.romeo.password)
        assert '<p class="flash-info">You have been logged in.</p>' in response.data
        response = self.client.get("/yourmessages/", follow_redirects=True)
        assert 'Message 1 Subject' in response.data
        self.logout()

        response = self.login(users.juliet.nickname, users.juliet.password)
        assert '<p class="flash-info">You have been logged in.</p>' in response.data
        response = self.client.get("/yourmessages/", follow_redirects=True)
        assert 'Message 1 Subject' not in response.data
        self.logout()

        # Avoid problems with foreign keys.
        UserMsgMESSAGE.query.delete()
        MsgMESSAGE.query.delete()
        db.session.commit()

    @fixture.with_data(UserData)
    def test_send_later(data, self):
        users = data.UserData
        romeo = User.query.filter(User.nickname.like('romeo')).one()

        #response = self.login('romeo', '')

        import time
        from datetime import datetime, timedelta

        sent = datetime.now()
        received = sent + timedelta(seconds=5)

        m = MsgMESSAGE()
        m.subject = 'sent_now'
        m.body = 'body'
        m.sent_to_user_nicks = 'admin'
        m.sent_to_group_names = ''
        m.id_user_from = users.romeo.id
        m.sent_date = sent
        db.session.add(m)
        db.session.commit()

        m = MsgMESSAGE()
        m.subject = 'sent_later'
        m.body = 'body'
        m.sent_to_user_nicks = 'admin'
        m.sent_to_group_names = ''
        m.id_user_from = romeo.id
        m.sent_date = sent
        m.received_date=received#.strftime('%Y-%m-%d %H:%M:%S')
        for um in m.sent_to_users:
            um.status = CFG_WEBMESSAGE_STATUS_CODE['REMINDER']
        db.session.add(m)
        db.session.commit()

        #response = self.client.post('/yourmessages/add',
        #        #base_url=request.base_url.replace('http:','https:'),
        #        data=dict(
        #        sent_to_user_nicks='admin',
        #        sent_to_group_names=' ',
        #        subject='sent_later',
        #        body='test',
        #        received_date=received.strftime('%Y-%m-%d %H:%M:%S')
        #       ), follow_redirects=True,
        #       headers=[('X-Requested-With', 'XMLHttpRequest')])

        #self.logout()
        response = self.login(users.admin.nickname, users.admin.password)

        response = self.client.get("/yourmessages/", follow_redirects=True)
        assert 'sent_now' in response.data
        assert 'sent_later' not in response.data

        while datetime.now() <= received:
            time.sleep(1)
            print '.'

        time.sleep(1)

        response = self.client.get("/yourmessages/", follow_redirects=True)
        assert 'sent_now' in response.data
        assert 'sent_later' in response.data

        # Avoid problems with foreign keys.
        UserMsgMESSAGE.query.delete()
        MsgMESSAGE.query.delete()
        db.session.commit()

    @fixture.with_data(UserData)
    def test_with_fixture(data, self):
        u = User.query.all()
        assert len(u) == len(dict(data.UserData))

    def test_without_fixture(self):
        u = User.query.all()
        assert len(u) == 0


TEST_SUITE = make_flask_test_suite(MsgMESSAGETest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)

