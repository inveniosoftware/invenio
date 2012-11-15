from flask import current_app, request
from invenio.sqlalchemyutils import db
from flask import session, g
from invenio.webuser_flask import current_user, login_user, logout_user

from invenio.testutils import make_flask_test_suite, run_test_suite, \
                              FlaskSQLAlchemyTest

from fixture import SQLAlchemyFixture
from invenio.webaccount_fixtures import UserData, UsergroupData, \
                                        UserUsergroupData
from invenio.websession_model import User, Usergroup, UserUsergroup

fixture = SQLAlchemyFixture(
        env={'UserData': User, 'UsergroupData': Usergroup,
             'UserUsergroupData': UserUsergroup},
        engine=db.metadata.bind,
        session=db.session
        )

class WebAccountTest(FlaskSQLAlchemyTest):

    @fixture.with_data(UserData)
    def test_low_level_login(data, self):
        users = data.UserData

        assert current_user.is_guest
        login_user(users.admin.id)
        assert current_user.get_id() == users.admin.id
        logout_user()
        assert current_user.get_id() != users.admin.id
        assert current_user.is_guest
        login_user(users.romeo.id)
        assert not current_user.is_guest
        assert current_user.get_id() == users.romeo.id
        login_user(users.admin.id)
        assert current_user.get_id() == users.admin.id
        logout_user()


    @fixture.with_data(UserData)
    def test_login(data, self):
        users = data.UserData

        # Valid credentials.
        for name, u in users:
            response = self.login(u.nickname, u.password)
            assert 'You have been' in response.data
            self.logout()

        # Empty form should not work.
        response = self.login('', '')
        assert 'You have been' not in response.data
        # Not existing user.
        response = self.login('NOT EXISTS', '')
        assert 'You have been' not in response.data
        # Existing password with not existing user name.
        response = self.login('NOT EXISTS', users.romeo.password)
        assert 'You have been' not in response.data
        # Invalid password for admin.
        response = self.login(users.admin.nickname, 'FAIL')
        assert 'You have been' not in response.data

    @fixture.with_data(UserData)
    def test_change_password(data, self):
        NEW_PASSWORD = 'admin'
        users = data.UserData

        response = self.login(users.admin.nickname, users.admin.password)
        assert 'You have been logged in' in response.data
        self.logout()

        admin = User.query.filter(User.id == users.admin.id).one()
        admin.password = NEW_PASSWORD
        db.session.merge(admin)
        db.session.commit()

        new_passwd = db.session.query(User.password).filter(User.id == users.admin.id).one()
        assert users.admin.password != new_passwd

        # Invalid password for admin.
        response = self.login(users.admin.nickname, users.admin.password)
        assert 'You have been' not in response.data

        # Valid credentials.
        response = self.login(users.admin.nickname, NEW_PASSWORD)
        assert 'You have been logged in' in response.data
        self.logout()


class UserGroupTest(FlaskSQLAlchemyTest):

    @fixture.with_data(UserData, UsergroupData, UserUsergroupData)
    def test_group_relation_consistency(data, self):
        orig_len = len(dict(data.UserUsergroupData))
        user_len = sum(len(u.usergroups) for u in User.query.all())
        ugrp_len = sum(len(g.users) for g in Usergroup.query.all())

        assert orig_len == user_len
        assert user_len == ugrp_len


TEST_SUITE = make_flask_test_suite(WebAccountTest, UserGroupTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)

