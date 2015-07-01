# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""Unit tests for forms."""

from invenio.testsuite import InvenioTestCase, make_test_suite, run_test_suite


class FormsTestCase(InvenioTestCase):

    """Test form classes."""

    def setUp(self):
        """Set up."""
        from invenio.modules.accounts.models import User
        from flask import current_app
        from invenio.base.globals import cfg

        self.min_len = cfg['CFG_ACCOUNT_MIN_PASSWORD_LENGTH'] or 1

        # disable csrf validation
        current_app.config['WTF_CSRF_ENABLED'] = False

        self.nickname = "test-form"
        self.password = "p" * self.min_len
        self.email = "test-email@fuu.it"

        self.user = User(nickname=self.nickname,
                         password=self.password,
                         email=self.email)

        self.create_objects([self.user])

    def tearDown(self):
        """Run after the tests."""
        self.delete_objects([self.user])

    def test_login_form_nickname(self):
        """Test login form."""
        from invenio.modules.accounts.forms import LoginForm

        loginform = LoginForm(
            nickname=self.nickname
        )
        assert loginform.validate() is True

        self.delete_objects([self.user])
        assert loginform.validate() is False

    def test_profile_form_nickname(self):
        """Test ProfileForm nickname."""
        from invenio.modules.accounts.forms import ProfileForm
        from flask_login import login_user, logout_user
        from invenio.ext.login import UserInfo

        form = ProfileForm(
            nickname=self.nickname,
            email=self.email,
            repeat_email=self.email
        )
        assert form.validate() is False

        form = ProfileForm(
            nickname=" nickname",
            email=self.email,
            repeat_email=self.email
        )
        assert form.validate() is False

        form = ProfileForm(
            nickname="nickname ",
            email=self.email,
            repeat_email=self.email
        )
        assert form.validate() is False

        form = ProfileForm(
            nickname="nick.name",
            email=self.email,
            repeat_email=self.email
        )
        assert form.validate() is False

        form = ProfileForm(
            nickname="nick@name",
            email=self.email,
            repeat_email=self.email
        )
        assert form.validate() is False

        form = ProfileForm(
            nickname="ni@ck.name",
            email=self.email,
            repeat_email=self.email
        )
        assert form.validate() is False

        form = ProfileForm(
            nickname="guest",
            email=self.email,
            repeat_email=self.email
        )
        assert form.validate() is False

        form = ProfileForm(
            nickname="Guest",
            email=self.email,
            repeat_email=self.email
        )
        assert form.validate() is False

        login_user(UserInfo(self.user.id))
        form = ProfileForm(
            nickname=self.nickname,
            email=self.email,
            repeat_email=self.email
        )
        assert form.validate() is True

        self.delete_objects([self.user])
        form = ProfileForm(
            nickname=self.nickname,
            email=self.email,
            repeat_email=self.email
        )
        assert form.validate() is True

        logout_user()

    def test_profile_form_email(self):
        """Test ProfileForm email."""
        from invenio.modules.accounts.forms import ProfileForm

        form = ProfileForm(
            nickname=self.nickname,
            email="not-email",
            repeat_email="not-email",
        )
        assert form.validate() is False

        form = ProfileForm(
            nickname=self.nickname,
            email="not@email",
            repeat_email="not@email"
        )
        assert form.validate() is False

        form = ProfileForm(
            nickname=self.nickname,
            email="not-exists@email.it",
            repeat_email="not-exists@email.it"
        )
        assert form.validate() is False

        form = ProfileForm(
            nickname=self.nickname,
            email="",
            repeat_email=""
        )
        assert form.validate() is False

        form = ProfileForm(
            nickname=self.nickname,
            email=self.email,
            repeat_email=self.email
        )
        assert form.validate() is False

        self.delete_objects([self.user])
        form = ProfileForm(
            nickname=self.nickname,
            email=self.email,
            repeat_email=self.email
        )
        assert form.validate() is True

    def test_profile_form_repeat_email(self):
        """Test ProfileForm repeat email."""
        from invenio.modules.accounts.forms import ProfileForm

        self.delete_objects([self.user])

        form = ProfileForm(
            nickname=self.nickname,
            email=self.email,
            repeat_email=self.email+'fuu',
        )
        assert form.validate() is False

        form = ProfileForm(
            nickname=self.nickname,
            email=self.email,
            repeat_email=self.email,
        )
        assert form.validate() is True

    def test_lost_password_form_email(self):
        """Test LostPasswordForm email."""
        from invenio.modules.accounts.forms import LostPasswordForm
        from invenio.base.globals import cfg

        cfg['CFG_ACCESS_CONTROL_LIMIT_REGISTRATION_TO_DOMAIN'] = ''

        form = LostPasswordForm(
            email="not-email",
        )
        assert form.validate() is False

        form = LostPasswordForm(
            email="not@email",
        )
        assert form.validate() is False

        form = LostPasswordForm(
            email="notemail",
        )
        assert form.validate() is False

        form = LostPasswordForm(
            email="not-exists-but-valid@email.it",
        )
        assert form.validate() is True

        form = LostPasswordForm(
            email="",
        )
        assert form.validate() is False

        form = LostPasswordForm(
            email=self.email,
        )
        assert form.validate() is True

        self.delete_objects([self.user])
        form = LostPasswordForm(
            email=self.email,
        )
        assert form.validate() is True

        cfg['CFG_ACCESS_CONTROL_LIMIT_REGISTRATION_TO_DOMAIN'] = 'fuu.it'

        form = LostPasswordForm(
            email="test@email.it",
        )
        assert form.validate() is False

        email = "fuu@" + cfg['CFG_ACCESS_CONTROL_LIMIT_REGISTRATION_TO_DOMAIN']
        form = LostPasswordForm(
            email=email,
        )
        assert form.validate() is True

    def test_reset_password_password(self):
        """Test ResetPasswordForm password."""
        from invenio.modules.accounts.forms import ResetPasswordForm

        not_valid_pwd = "x" * (self.min_len - 1)
        valid_pwd = "x" * self.min_len

        form = ResetPasswordForm(
            password=self.password,
            password2=self.password
        )
        assert form.validate() is True

        form = ResetPasswordForm(
            password=not_valid_pwd,
            password2=not_valid_pwd
        )
        assert form.validate() is False

        form = ResetPasswordForm(
            password=valid_pwd,
            password2=valid_pwd
        )
        assert form.validate() is True

    def test_reset_password_password2(self):
        """Test ResetPasswordForm password2."""
        from invenio.modules.accounts.forms import ResetPasswordForm

        form = ResetPasswordForm(
            password=self.password,
            password2=self.password
        )
        assert form.validate() is True

        form = ResetPasswordForm(
            password=self.password,
            password2=self.password+"different"
        )
        assert form.validate() is False

    def test_change_password_current_password(self):
        """Test ChangePasswordForm current password."""
        from invenio.modules.accounts.forms import ChangePasswordForm
        from flask_login import login_user, logout_user
        from invenio.ext.login import UserInfo

        valid_pwd = "x" * self.min_len

        login_user(UserInfo(self.user.id))
        form = ChangePasswordForm(
            current_password=self.password,
            password=valid_pwd,
            password2=valid_pwd
        )
        assert form.validate() is True
        logout_user()

        form = ChangePasswordForm(
            current_password=self.password,
            password=valid_pwd,
            password2=valid_pwd
        )
        assert form.validate() is False

        form = ChangePasswordForm(
            current_password="",
            password=valid_pwd,
            password2=valid_pwd
        )
        assert form.validate() is False

    def test_change_password_password(self):
        """Test ChangePasswordForm password."""
        from invenio.modules.accounts.forms import ChangePasswordForm
        from flask_login import login_user, logout_user
        from invenio.ext.login import UserInfo

        not_valid_pwd = "x" * (self.min_len - 1)
        valid_pwd = "x" * self.min_len

        login_user(UserInfo(self.user.id))
        form = ChangePasswordForm(
            current_password=self.password,
            password=valid_pwd,
            password2=valid_pwd
        )
        assert form.validate() is True

        form = ChangePasswordForm(
            current_password=self.password,
            password=not_valid_pwd,
            password2=not_valid_pwd
        )
        assert form.validate() is False

        form = ChangePasswordForm(
            current_password=self.password,
            password=valid_pwd,
            password2=valid_pwd+'different'
        )
        assert form.validate() is False

        logout_user()

    def test_register_form_email(self):
        """Test RegisterForm email."""
        from invenio.modules.accounts.forms import RegisterForm
        from invenio.base.globals import cfg

        cfg['CFG_ACCESS_CONTROL_LIMIT_REGISTRATION_TO_DOMAIN'] = ''

        valid_pwd = "x" * self.min_len

        form = RegisterForm(
            email="valid@email.it",
            nickname="testvalidnickname",
            password=valid_pwd,
            password2=valid_pwd
        )
        assert form.validate() is True

        form = RegisterForm(
            email="",
            nickname="testvalidnickname",
            password=valid_pwd,
            password2=valid_pwd
        )
        assert form.validate() is False

        form = RegisterForm(
            email=self.email,
            nickname="testvalidnickname",
            password=valid_pwd,
            password2=valid_pwd
        )
        assert form.validate() is False

        form = RegisterForm(
            email="email@fuu",
            nickname="testvalidnickname",
            password=valid_pwd,
            password2=valid_pwd
        )
        assert form.validate() is False

        form = RegisterForm(
            email="email.fuu",
            nickname="testvalidnickname",
            password=valid_pwd,
            password2=valid_pwd
        )
        assert form.validate() is False

        cfg['CFG_ACCESS_CONTROL_LIMIT_REGISTRATION_TO_DOMAIN'] = 'fuu.it'

        form = RegisterForm(
            email="email@bar.it",
            nickname="testvalidnickname",
            password=valid_pwd,
            password2=valid_pwd
        )
        assert form.validate() is False

        email = "fu@" + cfg['CFG_ACCESS_CONTROL_LIMIT_REGISTRATION_TO_DOMAIN']
        form = RegisterForm(
            email=email,
            nickname="testvalidnickname",
            password=valid_pwd,
            password2=valid_pwd
        )
        assert form.validate() is True

    def test_register_form_nickname(self):
        """Test RegisterForm nickname."""
        from invenio.modules.accounts.forms import RegisterForm

        valid_pwd = "x" * self.min_len

        form = RegisterForm(
            email="valid@email.it",
            nickname="testvalidnickname",
            password=valid_pwd,
            password2=valid_pwd
        )
        assert form.validate() is True

        form = RegisterForm(
            email="valid@email.it",
            nickname="",
            password=valid_pwd,
            password2=valid_pwd
        )
        assert form.validate() is False

        form = RegisterForm(
            email="valid@email.it",
            nickname="notvalid@user",
            password=valid_pwd,
            password2=valid_pwd
        )
        assert form.validate() is False

        form = RegisterForm(
            email="valid@email.it",
            nickname="notvalid,user",
            password=valid_pwd,
            password2=valid_pwd
        )
        assert form.validate() is False

        form = RegisterForm(
            email="valid@email.it",
            nickname=" testnickname",
            password=valid_pwd,
            password2=valid_pwd
        )
        assert form.validate() is False

        form = RegisterForm(
            email="valid@email.it",
            nickname="testnickname ",
            password=valid_pwd,
            password2=valid_pwd
        )
        assert form.validate() is False

        form = RegisterForm(
            email="valid@email.it",
            nickname="guest",
            password=valid_pwd,
            password2=valid_pwd
        )
        assert form.validate() is False

    def test_register_form_password(self):
        """Test RegisterForm password."""
        from invenio.modules.accounts.forms import RegisterForm

        not_valid_pwd = "x" * (self.min_len - 1)
        valid_pwd = "x" * self.min_len

        form = RegisterForm(
            email="valid@email.it",
            nickname="testvalidnickname",
            password=valid_pwd,
            password2=valid_pwd
        )
        assert form.validate() is True

        form = RegisterForm(
            email="valid@email.it",
            nickname="testvalidnickname",
            password=not_valid_pwd,
            password2=not_valid_pwd
        )
        assert form.validate() is False

        form = RegisterForm(
            email="valid@email.it",
            nickname="testvalidnickname",
            password=valid_pwd,
            password2=valid_pwd+"different"
        )
        assert form.validate() is False


TEST_SUITE = make_test_suite(FormsTestCase)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
