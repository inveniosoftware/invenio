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

"""Test for access models."""

from __future__ import unicode_literals

from invenio.testsuite import InvenioTestCase, make_test_suite, run_test_suite


class UserAccROLETests(InvenioTestCase):

    """Test UserAccROLE class."""

    def setUp(self):
        """Run before the test."""
        from invenio.modules.access.models import AccROLE, UserAccROLE
        from invenio_accounts.models import User
        import datetime

        self.user = User(nickname="test-user", email="test-email@test.it",
                         password="test")

        self.create_objects([self.user])

        # useraccrole

        self.role_uar_1 = AccROLE(name='test-role-uac-1',
                                  description='test-desc-uac-1')
        self.role_uar_2 = AccROLE(name='test-role-uac-2',
                                  description='test-desc-uac-2')

        self.create_objects([self.role_uar_1, self.role_uar_2])

        expiration = datetime.datetime.now()
        self.useraccroles = [
            UserAccROLE(id_user=self.user.id, id_accROLE=self.role_uar_1.id,
                        expiration=expiration),
            UserAccROLE(id_user=self.user.id, id_accROLE=self.role_uar_2.id,
                        expiration=expiration),
        ]

        self.create_objects(self.useraccroles)

        # test factory()

        self.role_factory_1 = AccROLE(name='test-role-factory-1')
        self.role_factory_2 = AccROLE(name='test-role-factory-2')

        self.create_objects([self.role_factory_1, self.role_factory_2])

        self.userrole_factory_1 = UserAccROLE(
            id_user=self.user.id,
            id_accROLE=self.role_factory_1.id,
            expiration=datetime.datetime.strptime(
                '9999-12-31 23:59', '%Y-%m-%d %H:%M'))

        yesterday = datetime.date.today() - datetime.timedelta(1)
        self.userrole_factory_2 = UserAccROLE(
            id_user=self.user.id,
            id_accROLE=self.role_factory_2.id,
            expiration=yesterday)

        self.create_objects([self.userrole_factory_1, self.userrole_factory_2])

        # count(), tests

        self.counts_roles = [
            AccROLE(
                name='test-counts-role-uac-'+str(i)
            ) for i in range(1, 6)]
        self.create_objects(self.counts_roles)

        self.counts_useraccroles = [
            UserAccROLE(
                id_user=self.user.id,
                id_accROLE=self.counts_roles[i-1].id
            ) for i in range(1, 6)]
        self.create_objects(self.counts_useraccroles)

        # test is_user_in_any_role()

        self.iuiar_role = AccROLE(name="test-is-user-in-any-role")
        self.create_objects([self.iuiar_role])

        self.iuiar_useraccrole = UserAccROLE(
            id_user=self.user.id,
            id_accROLE=self.iuiar_role.id,
            expiration=datetime.date.today() + datetime.timedelta(1)
        )
        self.create_objects([self.iuiar_useraccrole])

    def tearDown(self):
        """Run after the tests."""
        self.delete_objects([self.user])
        self.delete_objects([self.role_uar_1, self.role_uar_2])
        self.delete_objects(self.useraccroles)
        self.delete_objects([
            self.role_factory_1, self.role_factory_2,
            self.userrole_factory_1, self.userrole_factory_2])
        self.delete_objects(self.counts_roles)
        self.delete_objects(self.counts_useraccroles)
        self.delete_objects([self.iuiar_role, self.iuiar_useraccrole])

    def test_useraccrole_bulk_update(self):
        """Test update multiple useraccroles."""
        from invenio.modules.access.models import UserAccROLE
        import datetime
        new_expiration = datetime.datetime.now() + datetime.timedelta(days=1)
        old_expiration = self.useraccroles[0].expiration
        id_user = self.useraccroles[0].id_user
        id_accrole_0 = self.useraccroles[0].id_accROLE
        id_accrole_1 = self.useraccroles[1].id_accROLE

        criteria = [
            UserAccROLE.id_user == id_user,
            UserAccROLE.id_accROLE.in_([
                self.useraccroles[0].id_accROLE,
            ])
        ]

        updates = {
            'expiration': new_expiration,
        }

        UserAccROLE.update(criteria, updates)

        useraccrole_0 = UserAccROLE.query.filter_by(
            id_user=self.useraccroles[0].id_user,
            id_accROLE=self.useraccroles[0].id_accROLE).first()
        useraccrole_1 = UserAccROLE.query.filter_by(
            id_user=self.useraccroles[1].id_user,
            id_accROLE=self.useraccroles[1].id_accROLE).first()

        # test expiration changed for useraccrole 0
        assert useraccrole_0.expiration.day == new_expiration.day

        # test expiration not changed for useraccrole 1
        assert useraccrole_1.expiration.day == old_expiration.day

        # test not changed
        assert useraccrole_0.id_user == id_user
        assert useraccrole_1.id_user == id_user
        assert useraccrole_0.id_accROLE == id_accrole_0
        assert useraccrole_1.id_accROLE == id_accrole_1

    def test_factory(self):
        """Test factory."""
        from invenio.modules.access.models import UserAccROLE
        import datetime

        # test get userrole that already exists (not expired)
        userrole = UserAccROLE.factory(
            id_user=self.userrole_factory_1.id_user,
            id_accROLE=self.userrole_factory_1.id_accROLE,
            expiration=datetime.datetime.now()
        )
        assert userrole.id_user == self.userrole_factory_1.id_user
        assert userrole.id_accROLE == self.userrole_factory_1.id_accROLE
        assert userrole.expiration == self.userrole_factory_1.expiration

        # test get userrole that already exists (expired)
        userrole = UserAccROLE.factory(
            id_user=self.userrole_factory_2.id_user,
            id_accROLE=self.userrole_factory_2.id_accROLE,
            expiration=datetime.datetime.now()
        )
        assert userrole.id_user == self.userrole_factory_2.id_user
        assert userrole.id_accROLE == self.userrole_factory_2.id_accROLE
        assert userrole.expiration == self.userrole_factory_2.expiration

        # test create new userrole

        userrole = UserAccROLE.factory(
            id_user=self.user.id,
            id_accROLE=self.role_uar_1.id
        )

        userrole_loaded = UserAccROLE.query.filter_by(
            id_user=self.user.id,
            id_accROLE=self.role_uar_1.id
        ).first()

        assert userrole_loaded.id_user == self.user.id
        assert userrole_loaded.id_accROLE == self.role_uar_1.id
        assert userrole.expiration == userrole.expiration
        assert userrole.expiration >= datetime.datetime.now()

    def test_count(self):
        """Test count."""
        from invenio.modules.access.models import UserAccROLE

        filters = [
            UserAccROLE.id_user == self.user.id,
            UserAccROLE.id_accROLE.in_([r.id for r in self.counts_roles])
        ]

        assert UserAccROLE.count(*filters) == len(self.counts_useraccroles)

    def test_is_user_in_any_role(self):
        """Test is_user_in_any_role function."""
        from invenio.modules.access.models import UserAccROLE
        user_info = {'uid': self.user.id}
        assert UserAccROLE.is_user_in_any_role(user_info, [self.iuiar_role.id])

        self.delete_objects([self.iuiar_useraccrole])
        assert not UserAccROLE.is_user_in_any_role(user_info,
                                                   [self.iuiar_role.id])
        # TODO test the for each


class AccROLETests(InvenioTestCase):

    """Test AccROLE class."""

    def setUp(self):
        """Run before the test."""
        from invenio.modules.access.models import AccROLE
        from invenio.modules.access.local_config import SUPERADMINROLE

        # roles
        self.roles = [
            AccROLE(name='test-role-1', description='test-desc-1'),
            AccROLE(name='test-role-2', description='test-desc-2'),
            AccROLE(name='test-role-3', description='test-desc-3'),
        ]
        self.create_objects(self.roles)

        # check firerol_def
        self.role_firerol_def = AccROLE(
            name='test-role_firerol_def',
            firerole_def_src="allow remote_ip '127.0.0.0/24'"
        )
        self.role_firerol_def_2 = AccROLE(
            name='test-role_firerol_def-2',
            firerole_def_src=None
        )
        self.create_objects([self.role_firerol_def, self.role_firerol_def_2])

        # test factory

        self.role_factory = AccROLE(
            name='test-role_factory-name',
            description='test-role_factory-description',
            firerole_def_src="allow remote_ip '127.0.0.0/24'"
        )

        self.create_objects([self.role_factory])

        # test delete SUPERADMINROLE

        self.role_superadmin = AccROLE(
            name=SUPERADMINROLE+"-test",
            description='test-role_factory-description',
            firerole_def_src="allow remote_ip '127.0.0.0/24'"
        )

        self.create_objects([self.role_superadmin])

        # test exists()

        self.exists_role = AccROLE(
            name="test-exists-role",
            description='test-role_exists-description',
            firerole_def_src="allow remote_ip '127.0.0.0/24'"
        )

        self.create_objects([self.exists_role])

        # test firerole_def_ser setter()

        self.firerole_role = AccROLE(
            name="test-firerole-role",
            description='test-role_firerole-description',
        )

        self.create_objects([self.firerole_role])

    def tearDown(self):
        """Run after the tests."""
        self.delete_objects(self.roles)
        self.delete_objects([self.role_firerol_def, self.role_firerol_def_2])
        self.delete_objects([self.role_factory])
        self.delete_objects([self.role_superadmin])
        self.delete_objects([self.exists_role])
        self.delete_objects([self.firerole_role])

    def test_role_bulk_update(self):
        """Test update multiple roles."""
        from invenio.modules.access.models import AccROLE
        new_description = 'test-desc-modified'
        old_description = self.roles[2].description
        name_0 = self.roles[0].name
        name_1 = self.roles[1].name
        name_2 = self.roles[2].name

        criteria = [
            AccROLE.id.in_([self.roles[0].id,
                            self.roles[1].id])
        ]

        updates = {
            'description': new_description,
        }

        AccROLE.update(criteria, updates)

        rule_0 = AccROLE.query.get(self.roles[0].id)
        rule_1 = AccROLE.query.get(self.roles[1].id)
        rule_2 = AccROLE.query.get(self.roles[2].id)

        # test description changed for rule 0,1
        assert rule_0.description == new_description
        assert rule_1.description == new_description

        # test description not changed for rule 2
        assert rule_2.description == old_description

        # test name not changed
        assert rule_0.name == name_0
        assert rule_1.name == name_1
        assert rule_2.name == name_2

    def test_firerol_ser(self):
        """Test firerole ser."""
        from invenio.modules.access.models import AccROLE
        from invenio.modules.access.firerole import \
            compile_role_definition

        firerole = self.role_firerol_def.firerole_def_src
        # read from the db
        id = self.role_firerol_def.id
        role_from_db = AccROLE.query.get(id)
        # test
        assert role_from_db.firerole_def_src == firerole
        assert role_from_db.firerole_def_ser == \
            compile_role_definition(firerole)

    def test_firerol_ser_none(self):
        """Test firerole ser."""
        from invenio.modules.access.models import AccROLE
        from invenio.modules.access.firerole import \
            compile_role_definition
        firerole = self.role_firerol_def_2.firerole_def_src
        # read from the db
        id = self.role_firerol_def_2.id
        role_from_db = AccROLE.query.get(id)
        # test
        assert role_from_db.firerole_def_src == firerole
        assert role_from_db.firerole_def_ser == \
            compile_role_definition(firerole)

    def test_factory(self):
        """Test factory."""
        from invenio.modules.access.models import AccROLE
        from invenio.modules.access.local_config import \
            CFG_ACC_EMPTY_ROLE_DEFINITION_SRC

        # test: get role that already exists
        role = AccROLE.factory(self.role_factory.name)

        assert role.id == self.role_factory.id
        assert role.name == self.role_factory.name
        assert role.description == self.role_factory.description
        assert role.firerole_def_src == self.role_factory.firerole_def_src
        assert role.firerole_def_ser == self.role_factory.firerole_def_ser

        # test: create new role (setting description and firerole)
        name = self.role_factory.name
        description = "test factory test desc"
        firerole_def_src = "deny remote_ip '127.0.0.0/24'"
        self.delete_objects([self.role_factory])
        role = AccROLE.factory(name=name, description=description,
                               firerole_def_src=firerole_def_src)
        assert role.name == name
        assert role.description == description
        assert role.firerole_def_src == firerole_def_src

        # test: create new role (with default description and firerole)
        name = self.role_factory.name
        self.delete_objects([role])
        role = AccROLE.factory(name=name)

        assert role.name == name
        assert role.description is None
        assert role.firerole_def_src == CFG_ACC_EMPTY_ROLE_DEFINITION_SRC

        self.delete_objects([role])

    def test_exists(self):
        """Test argument exists."""
        from invenio.modules.access.models import AccROLE
        id = self.exists_role.id
        # test True
        assert AccROLE.exists(AccROLE.id == id) is True
        # test False
        self.delete_objects([self.exists_role])
        assert AccROLE.exists(AccROLE.id == id) is False

    def test_firerole_setter(self):
        """Test firerole setter."""
        self.assertRaises(
            Exception,
            setattr,
            self.firerole_role.firerole_def_ser,
            "allow remote_ip '127.0.0.0/24'"
        )


class AccARGUMENTTests(InvenioTestCase):

    """Test AccARGUMENT class."""

    def setUp(self):
        """Run before the test."""
        from invenio.modules.access.models import AccARGUMENT

        # exists() tests
        self.exists_argument = AccARGUMENT(keyword="fuu", value="bar")
        self.create_objects([self.exists_argument])

        # factory() tests
        self.factory_argument = AccARGUMENT(keyword="test-factory-keyword",
                                            value="test-factory-value")
        self.create_objects([self.factory_argument])

    def tearDown(self):
        """Run after the tests."""
        self.delete_objects([self.exists_argument])
        self.delete_objects([self.factory_argument])

    def test_argument_exists(self):
        """Test argument exists."""
        from invenio.modules.access.models import AccARGUMENT
        id_arg = self.exists_argument.id
        # test True
        assert AccARGUMENT.exists(AccARGUMENT.id == id_arg) is True
        # test False
        self.delete_objects([self.exists_argument])
        assert AccARGUMENT.exists(AccARGUMENT.id == id_arg) is False

    def test_factory(self):
        """Test factory."""
        from invenio.modules.access.models import AccARGUMENT

        keyword = self.factory_argument.keyword
        value = self.factory_argument.value

        # test if argument already exists
        argument = AccARGUMENT.factory(keyword=keyword, value=value)

        assert argument.id == self.factory_argument.id
        assert argument.keyword == self.factory_argument.keyword
        assert argument.value == self.factory_argument.value

        # test if not exists
        self.delete_objects([self.factory_argument])
        argument = AccARGUMENT.factory(keyword=keyword, value=value)

        assert argument.keyword == keyword
        assert argument.value == value

        self.delete_objects([argument])


class AccAuthorizationTests(InvenioTestCase):

    """Test AccAuthorization class."""

    def setUp(self):
        """Run before the test."""
        from invenio.modules.access.models import AccAuthorization, \
            AccACTION, AccROLE
        # exists() tests
        self.exists_auth = AccAuthorization()
        self.create_objects([self.exists_auth])
        # counts() tests
        self.counts_auth = [
            AccAuthorization(argumentlistid=i) for i in range(1, 6)]
        self.create_objects(self.counts_auth)

        # factory_with_no_arguments tests

        self.role_fwna = AccROLE(name='test-factory-no-args-role')
        self.create_objects([self.role_fwna])

        self.actions_fwna = [
            AccACTION(
                allowedkeywords='fuu',
                optional='yes'
            ),
            AccACTION(
                allowedkeywords='fuu',
                optional='no'
            ),
            AccACTION(
                allowedkeywords='',
                optional='yes'
            ),
            AccACTION(
                allowedkeywords='',
                optional='no'
            ),
        ]
        self.create_objects(self.actions_fwna)

    def tearDown(self):
        """Run after the tests."""
        self.delete_objects([self.exists_auth])
        self.delete_objects(self.counts_auth)
        self.delete_objects(self.actions_fwna)
        self.delete_objects([self.role_fwna])

    def test_authorization_exists(self):
        """Test authorization exists."""
        from invenio.modules.access.models import AccAuthorization
        id_auth = self.exists_auth.id
        # test True
        assert AccAuthorization.exists(AccAuthorization.id == id_auth) is True
        # test False
        self.delete_objects([self.exists_auth])
        assert AccAuthorization.exists(AccAuthorization.id == id_auth) is False

    def test_authorization_count(self):
        """Test authorization count."""
        from invenio.modules.access.models import AccAuthorization
        ids = [auth.id for auth in self.counts_auth]
        # test True
        assert AccAuthorization.count(
            AccAuthorization.argumentlistid < 3,
            AccAuthorization.id.in_(ids)
        ) == 2
        # test False
        AccAuthorization.query.filter(
            AccAuthorization.argumentlistid > 1).delete()
        assert AccAuthorization.count(
            AccAuthorization.argumentlistid < 3,
            AccAuthorization.id.in_(ids)
        ) == 1

    def test_factory_with_no_arguments_1(self):
        """Test factory with no arguments."""
        from invenio.modules.access.models import AccAuthorization
        # factory_with_no_arguments() tests
        auths = AccAuthorization.factory(
            role=self.role_fwna,
            action=self.actions_fwna[0],
        )
        assert len(auths) == 1
        assert auths[0].argumentlistid == -1
        assert auths[0].id_accARGUMENT == -1
        self.delete_objects(auths)

    def test_factory_with_no_arguments_2(self):
        """Test factory with no arguments."""
        from invenio.modules.access.models import AccAuthorization
        # factory_with_no_arguments() tests
        auths = AccAuthorization.factory(
            role=self.role_fwna,
            action=self.actions_fwna[3],
        )
        assert len(auths) == 1
        assert auths[0].id_accARGUMENT is None
        assert auths[0].argumentlistid == 0

        # try again
        id = auths[0].id
        id_accROLE = auths[0].id_accROLE
        id_accACTION = auths[0].id_accACTION
        id_accARGUMENT = auths[0].id_accARGUMENT
        argumentlistid = auths[0].argumentlistid

        auths2 = AccAuthorization.factory(
            role=self.role_fwna,
            action=self.actions_fwna[3],
        )
        assert len(auths2) == 1

        assert auths2[0].id == id
        assert auths2[0].id_accROLE == id_accROLE
        assert auths2[0].id_accACTION == id_accACTION
        assert auths2[0].id_accARGUMENT == id_accARGUMENT
        assert auths2[0].argumentlistid == argumentlistid

        self.delete_objects(auths)
        self.delete_objects(auths2)

    def test_factory_with_no_arguments_3(self):
        """Test factory with no arguments."""
        from invenio.modules.access.models import AccAuthorization, AccARGUMENT
        from invenio.modules.access.errors import AccessFactoryError
        # factory_with_no_arguments() tests
        self.assertRaises(
            AccessFactoryError,
            AccAuthorization.factory,
            role=self.role_fwna,
            action=self.actions_fwna[1],
            argumentlistid=0,
            arguments=[AccARGUMENT(keyword="nopermitted")]
        )


class AccACTIONTests(InvenioTestCase):

    """Test AccACTION class."""

    def setUp(self):
        """Run before the test."""
        from invenio.modules.access.models import AccACTION, AccAuthorization

        # bulk update() tests

        self.actions = [
            AccACTION(name='test-action-1', description='test-desc-1'),
            AccACTION(name='test-action-2', description='test-desc-2'),
            AccACTION(name='test-action-3', description='test-desc-3'),
        ]
        self.create_objects(self.actions)

        # count(), tests

        self.counts_actions = [
            AccACTION(
                name="test-count-action-"+str(i),
                description='test-count-action'
            ) for i in range(1, 6)]
        self.create_objects(self.counts_actions)

        # update allowedkeywords, optional test

        self.action_update = AccACTION(
            name="test-action-update-allowedkeywords",
            description='test-action-update-allowedkeywords',
            allowedkeywords="tochange",
            optional='yes'
        )
        self.action_update_2 = AccACTION(
            name="test-action-update-optional",
            description='test-action-update-optional',
            optional='no'
        )
        self.create_objects([self.action_update, self.action_update_2])

        self.auth_update = AccAuthorization(
            action=self.action_update,
            id_accARGUMENT=None,
            argumentlistid=-1
        )
        self.auth_update_2 = AccAuthorization(
            action=self.action_update_2,
            id_accARGUMENT=-1,
            argumentlistid=-1
        )
        self.auth_update_3 = AccAuthorization(
            action=self.action_update_2,
            id_accARGUMENT=None,
            argumentlistid=-1
        )
        self.auth_update_4 = AccAuthorization(
            action=self.action_update,
            id_accARGUMENT=-1,
            argumentlistid=-1
        )
        self.create_objects([self.auth_update, self.auth_update_2,
                             self.auth_update_3, self.auth_update_4])

        # allowedkeywords on new action tests

        self.allowedkeywords_auth_empty = AccAuthorization(
            id_accACTION=None,
            id_accARGUMENT=None
        )
        self.create_objects([self.allowedkeywords_auth_empty])

        # optional on new action tests

        self.optional_auth_new_obj = AccAuthorization(
            id_accACTION=None,
            id_accARGUMENT=-1,
            argumentlistid=-1
        )
        self.create_objects([self.optional_auth_new_obj])

    def tearDown(self):
        """Run after the tests."""
        self.delete_objects(self.actions)
        self.delete_objects(self.counts_actions)
        self.delete_objects([self.action_update, self.action_update_2,
                             self.auth_update, self.auth_update_2,
                             self.auth_update_3, self.auth_update_4])
        self.delete_objects([self.allowedkeywords_auth_empty])
        self.delete_objects([self.optional_auth_new_obj])

    def test_set_allowedkeywords_new_action_empty_value(self):
        """Test allowedkeywords for new action."""
        from invenio.modules.access.models import AccACTION, AccAuthorization
        id_auth = self.allowedkeywords_auth_empty.id

        action = AccACTION(
            name="test-set-allowedkeywords-new-action",
            allowedkeywords=""
        )
        self.create_objects([action])
        assert AccAuthorization.count(AccAuthorization.id == id_auth) == 1
        self.delete_objects([action])

    def test_set_allowedkeywords_new_action_not_empty_value(self):
        """Test allowedkeywords for new action."""
        from invenio.modules.access.models import AccACTION, AccAuthorization
        id_auth = self.allowedkeywords_auth_empty.id

        action = AccACTION(
            name="test-set-allowedkeywords-new-action",
            allowedkeywords="not-empty-value"
        )
        self.create_objects([action])
        assert AccAuthorization.count(AccAuthorization.id == id_auth) == 1
        self.delete_objects([action])

    def test_set_optional_set_no(self):
        """Test set optional on new object: set 'no'."""
        from invenio.modules.access.models import AccACTION, AccAuthorization
        id_auth = self.optional_auth_new_obj.id

        action = AccACTION(
            name="test-set-optional-new-action",
            optional='no'
        )
        self.create_objects([action])
        assert action.is_optional() is False
        assert AccAuthorization.count(AccAuthorization.id == id_auth) == 1
        self.delete_objects([action])

    def test_set_optional_set_yes(self):
        """Test set optional on new object: set 'yes'."""
        from invenio.modules.access.models import AccACTION, AccAuthorization
        id_auth = self.optional_auth_new_obj.id

        action = AccACTION(
            name="test-set-optional-new-action",
            optional='yes'
        )
        self.create_objects([action])
        assert action.is_optional() is True
        assert AccAuthorization.count(AccAuthorization.id == id_auth) == 1
        self.delete_objects([action])

    def test_action_bulk_update(self):
        """Test update multiple actions."""
        from invenio.modules.access.models import AccACTION
        new_description = 'test-desc-modified'
        old_description = self.actions[2].description
        name_0 = self.actions[0].name
        name_1 = self.actions[1].name
        name_2 = self.actions[2].name

        criteria = [
            AccACTION.id.in_([self.actions[0].id,
                              self.actions[1].id])
        ]

        updates = {
            'description': new_description,
        }

        AccACTION.update(criteria, updates)

        action_0 = AccACTION.query.get(self.actions[0].id)
        action_1 = AccACTION.query.get(self.actions[1].id)
        action_2 = AccACTION.query.get(self.actions[2].id)

        # test description changed for action 0,1
        assert action_0.description == new_description
        assert action_1.description == new_description

        # test description not changed for action 2
        assert action_2.description == old_description

        # test name not changed
        assert action_0.name == name_0
        assert action_1.name == name_1
        assert action_2.name == name_2

    def test_actions_count(self):
        """Test actions count."""
        from invenio.modules.access.models import AccACTION

        ids = [action.id for action in self.counts_actions]
        # test True
        assert AccACTION.count(
            AccACTION.id.in_(ids)
        ) == len(self.counts_actions)
        # test False
        AccACTION.delete(AccACTION.id.in_(ids))
        assert AccACTION.count(
            AccACTION.id.in_(ids)
        ) == 0

    def test_update_allowedkeyword_1(self):
        """Test allowedkeywords change."""
        from invenio.ext.sqlalchemy import db
        from invenio.modules.access.models import AccAuthorization

        orig_value = self.action_update.allowedkeywords
        auth_id = self.auth_update.id

        # set original value
        self.action_update.allowedkeywords = orig_value
        db.session.merge(self.action_update)
        db.session.commit()
        # test if already exists connected authorization
        assert AccAuthorization.count(AccAuthorization.id == auth_id) == 1

        # set different value
        orig_value.append("changed")
        self.action_update.allowedkeywords = orig_value
        db.session.merge(self.action_update)
        db.session.commit()
        # test if connected authorization is deleted
        assert AccAuthorization.count(AccAuthorization.id == auth_id) == 0

    def test_update_allowedkeyword_2(self):
        """Test allowedkeywords change."""
        from invenio.ext.sqlalchemy import db
        from invenio.modules.access.models import AccAuthorization

        orig_value = self.action_update.allowedkeywords
        auth_id = self.auth_update_2.id

        # set original value
        self.action_update.allowedkeywords = orig_value
        db.session.merge(self.action_update)
        db.session.commit()
        # test if already exists connected authorization
        assert AccAuthorization.count(AccAuthorization.id == auth_id) == 1

        # set different value
        orig_value.append("changed")
        self.action_update.allowedkeywords = orig_value
        db.session.merge(self.action_update)
        db.session.commit()
        # test if connected authorization is deleted
        assert AccAuthorization.count(AccAuthorization.id == auth_id) == 1

    def test_update_optional_action_1(self):
        """Test optional change."""
        from invenio.ext.sqlalchemy import db
        from invenio.modules.access.models import AccAuthorization

        auth_id = self.auth_update.id

        # set original value
        self.action_update.optional = 'yes'
        db.session.merge(self.action_update)
        db.session.commit()
        # test if already exists connected authorization
        assert AccAuthorization.count(AccAuthorization.id == auth_id) == 1

        # set different value
        self.action_update.optional = 'no'
        db.session.merge(self.action_update)
        db.session.commit()
        # test if connected authorization is deleted
        assert AccAuthorization.count(AccAuthorization.id == auth_id) == 1

    def test_update_optional_action_2(self):
        """Test optional change."""
        from invenio.ext.sqlalchemy import db
        from invenio.modules.access.models import AccAuthorization

        auth_id = self.auth_update.id

        # set original value
        self.action_update_2.optional = 'no'
        db.session.merge(self.action_update_2)
        db.session.commit()
        # test if already exists connected authorization
        assert AccAuthorization.count(AccAuthorization.id == auth_id) == 1

        # set different value
        self.action_update_2.optional = 'yes'
        db.session.merge(self.action_update_2)
        db.session.commit()
        # test if connected authorization is deleted
        assert AccAuthorization.count(AccAuthorization.id == auth_id) == 1

    def test_update_optional_action_3(self):
        """Test optional change."""
        from invenio.ext.sqlalchemy import db
        from invenio.modules.access.models import AccAuthorization

        auth_id = self.auth_update_3.id

        # set original value
        self.action_update.optional = 'yes'
        db.session.merge(self.action_update)
        db.session.commit()
        # test if already exists connected authorization
        assert AccAuthorization.count(AccAuthorization.id == auth_id) == 1

        # set different value
        self.action_update.optional = 'no'
        db.session.merge(self.action_update)
        db.session.commit()
        # test if connected authorization is deleted
        assert AccAuthorization.count(AccAuthorization.id == auth_id) == 1

    def test_update_optional_action_4(self):
        """Test optional change."""
        from invenio.ext.sqlalchemy import db
        from invenio.modules.access.models import AccAuthorization

        auth_id = self.auth_update_4.id

        # set original value
        self.action_update_2.optional = 'no'
        db.session.merge(self.action_update_2)
        db.session.commit()
        # test if already exists connected authorization
        assert AccAuthorization.count(AccAuthorization.id == auth_id) == 1

        # set different value
        self.action_update_2.optional = 'yes'
        db.session.merge(self.action_update_2)
        db.session.commit()
        # test if connected authorization is deleted
        assert AccAuthorization.count(AccAuthorization.id == auth_id) == 1

    def test_allowedkeywords_string(self):
        """Test to set string as allowedkeywords."""
        from invenio.modules.access.models import AccACTION

        keywords_string = 'test,insert,keywords,as,a,string'
        keywords_list = keywords_string.split(',')

        # create object
        action = AccACTION(
            allowedkeywords=keywords_string
        )
        assert action.allowedkeywords == keywords_list
        self.create_objects([action])
        # test read from db
        action_read_by_db = AccACTION.query.get(action.id)
        assert action_read_by_db.allowedkeywords == keywords_list

    def test_allowedkeywords_list(self):
        """Test to set list as allowedkeywords."""
        from invenio.modules.access.models import AccACTION

        keywords_string = 'test,insert,keywords,as,a,string'
        keywords_list = sorted(keywords_string.split(','))

        # create object
        action = AccACTION(
            allowedkeywords=keywords_list
        )
        assert action.allowedkeywords == keywords_list
        self.create_objects([action])
        # test read from db
        action_read_by_db = AccACTION.query.get(action.id)
        assert action_read_by_db.allowedkeywords == keywords_list


class ModelDeleteTest(InvenioTestCase):

    """Test AccACTION class."""

    def setUp(self):
        """Run before the test."""
        from invenio.modules.access.models import AccACTION, \
            AccAuthorization, AccARGUMENT, AccROLE, UserAccROLE
        from invenio_accounts.models import User

        self.user = User(nickname="test-user", email="test-email@test.it",
                         password="test")

        self.create_objects([self.user])

        # delete() tests

        self.role = AccROLE(name="test-role")
        self.action = AccACTION(name="test-action")
        self.argument = AccARGUMENT(keyword="test-key", value="test-value")

        self.create_objects([self.role, self.action, self.argument])

        self.authorization = AccAuthorization(
            role=self.role,
            action=self.action,
            _id_accARGUMENT=self.argument.id
        )

        self.create_objects([self.authorization])

        self.useraccrole = UserAccROLE(
            id_user=self.user.id,
            id_accROLE=self.role.id)

        self.create_objects([self.useraccrole])

    def tearDown(self):
        """Run after the tests."""
        # delete() tests
        self.delete_objects([self.role, self.action, self.argument,
                             self.authorization, self.user,
                             self.useraccrole])

    def test_delete_objects_authorization(self):
        """Test delete role."""
        from invenio.ext.sqlalchemy import db
        from invenio.modules.access.models import AccACTION, \
            AccAuthorization, AccARGUMENT, AccROLE, UserAccROLE
        from invenio_accounts.models import User

        AccAuthorization.delete(AccAuthorization.id == self.authorization.id)

        # assure that role, action, user, useraccrole still exist
        self.assertTrue(
            db.session.query(
                AccROLE.query.filter(
                    AccROLE.id == self.role.id
                ).exists()).scalar())
        self.assertTrue(
            db.session.query(
                AccACTION.query.filter(
                    AccACTION.id == self.action.id
                ).exists()).scalar())
        self.assertTrue(
            db.session.query(
                User.query.filter(
                    User.id == self.user.id
                ).exists()).scalar())
        self.assertTrue(
            db.session.query(
                UserAccROLE.query.filter(
                    UserAccROLE.id_user == self.useraccrole.id_user,
                    UserAccROLE.id_accROLE == self.useraccrole.id_accROLE,
                ).exists()).scalar())

        # assure that argument is removed
        self.assertFalse(
            db.session.query(
                AccARGUMENT.query.filter(
                    AccARGUMENT.id == self.argument.id
                ).exists()).scalar())

    def test_delete_objects_role(self):
        """Test delete role."""
        from invenio.ext.sqlalchemy import db
        from invenio.modules.access.models import AccACTION, \
            AccAuthorization, AccARGUMENT, AccROLE, UserAccROLE
        from invenio_accounts.models import User

        AccROLE.delete(AccROLE.id == self.role.id)

        # assure that action, user still exists
        self.assertTrue(
            db.session.query(
                AccACTION.query.filter(
                    AccACTION.id == self.action.id
                ).exists()).scalar())
        self.assertTrue(
            db.session.query(
                User.query.filter(
                    User.id == self.user.id
                ).exists()).scalar())

        # assure that argument, authorization, useraccrole are removed
        self.assertFalse(
            db.session.query(
                AccAuthorization.query.filter(
                    AccAuthorization.id == self.authorization.id
                ).exists()).scalar())
        self.assertFalse(
            db.session.query(
                AccARGUMENT.query.filter(
                    AccARGUMENT.id == self.argument.id
                ).exists()).scalar())
        self.assertFalse(
            db.session.query(
                UserAccROLE.query.filter(
                    UserAccROLE.id_user == self.useraccrole.id_user,
                    UserAccROLE.id_accROLE == self.useraccrole.id_accROLE,
                ).exists()).scalar())

    def test_delete_objects_action(self):
        """Test delete role."""
        from invenio.ext.sqlalchemy import db
        from invenio.modules.access.models import AccACTION, \
            AccAuthorization, AccARGUMENT, AccROLE, UserAccROLE
        from invenio_accounts.models import User

        AccACTION.delete(AccACTION.id == self.action.id)

        # assure that role, user, useraccrole still exists
        self.assertTrue(
            db.session.query(
                AccROLE.query.filter(
                    AccROLE.id == self.role.id
                ).exists()).scalar())
        self.assertTrue(
            db.session.query(
                User.query.filter(
                    User.id == self.user.id
                ).exists()).scalar())
        self.assertTrue(
            db.session.query(
                UserAccROLE.query.filter(
                    UserAccROLE.id_user == self.useraccrole.id_user,
                    UserAccROLE.id_accROLE == self.useraccrole.id_accROLE,
                ).exists()).scalar())

        # assure that argument and authorization are removed
        self.assertFalse(
            db.session.query(
                AccAuthorization.query.filter(
                    AccAuthorization.id == self.authorization.id
                ).exists()).scalar())
        self.assertFalse(
            db.session.query(
                AccARGUMENT.query.filter(
                    AccARGUMENT.id == self.argument.id
                ).exists()).scalar())

    def test_delete_objects_argument(self):
        """Test delete role."""
        from invenio.ext.sqlalchemy import db
        from invenio.modules.access.models import AccACTION, \
            AccARGUMENT, AccAuthorization, AccROLE, UserAccROLE
        from invenio_accounts.models import User

        AccARGUMENT.delete(AccARGUMENT.id == self.argument.id)

        # assure that role, action, authorization, user, useraccrole
        # still exists
        self.assertTrue(
            db.session.query(
                AccROLE.query.filter(
                    AccROLE.id == self.role.id
                ).exists()).scalar())
        self.assertTrue(
            db.session.query(
                AccACTION.query.filter(
                    AccACTION.id == self.action.id
                ).exists()).scalar())
        self.assertTrue(
            db.session.query(
                AccAuthorization.query.filter(
                    AccAuthorization.id == self.authorization.id
                ).exists()).scalar())
        self.assertTrue(
            db.session.query(
                User.query.filter(
                    User.id == self.user.id
                ).exists()).scalar())
        self.assertTrue(
            db.session.query(
                UserAccROLE.query.filter(
                    UserAccROLE.id_user == self.useraccrole.id_user,
                    UserAccROLE.id_accROLE == self.useraccrole.id_accROLE,
                ).exists()).scalar())

    def test_delete_objects_useraccrole(self):
        """Test delete useraccrole."""
        from invenio.ext.sqlalchemy import db
        from invenio.modules.access.models import AccACTION, \
            AccARGUMENT, AccAuthorization, AccROLE, UserAccROLE
        from invenio_accounts.models import User

        UserAccROLE.delete(
            UserAccROLE.id_user == self.useraccrole.id_user,
            UserAccROLE.id_accROLE == self.useraccrole.id_accROLE)

        # assure that role, action, authorization, argument, user
        # still exists
        self.assertTrue(
            db.session.query(
                AccROLE.query.filter(
                    AccROLE.id == self.role.id
                ).exists()).scalar())
        self.assertTrue(
            db.session.query(
                AccACTION.query.filter(
                    AccACTION.id == self.action.id
                ).exists()).scalar())
        self.assertTrue(
            db.session.query(
                AccAuthorization.query.filter(
                    AccAuthorization.id == self.authorization.id
                ).exists()).scalar())
        self.assertTrue(
            db.session.query(
                AccARGUMENT.query.filter(
                    AccARGUMENT.id == self.argument.id
                ).exists()).scalar())
        self.assertTrue(
            db.session.query(
                User.query.filter(
                    User.id == self.user.id
                ).exists()).scalar())

    def test_delete_objects_user(self):
        """Test delete user."""
        from invenio.ext.sqlalchemy import db
        from invenio.modules.access.models import AccACTION, \
            AccARGUMENT, AccAuthorization, AccROLE, UserAccROLE
        from invenio_accounts.models import User

        db.session.delete(User.query.filter(User.id == self.user.id).first())
        db.session.commit()

        # assure that role, action, authorization, argument, useraccrole
        # still exists
        self.assertTrue(
            db.session.query(
                AccROLE.query.filter(
                    AccROLE.id == self.role.id
                ).exists()).scalar())
        self.assertTrue(
            db.session.query(
                AccACTION.query.filter(
                    AccACTION.id == self.action.id
                ).exists()).scalar())
        self.assertTrue(
            db.session.query(
                AccAuthorization.query.filter(
                    AccAuthorization.id == self.authorization.id
                ).exists()).scalar())
        self.assertTrue(
            db.session.query(
                AccARGUMENT.query.filter(
                    AccARGUMENT.id == self.argument.id
                ).exists()).scalar())

        # assure that useraccrole is deleted
        self.assertFalse(
            db.session.query(
                UserAccROLE.query.filter(
                    UserAccROLE.id_user == self.useraccrole.id_user,
                    UserAccROLE.id_accROLE == self.useraccrole.id_accROLE,
                ).exists()).scalar())

TEST_SUITE = make_test_suite(
    UserAccROLETests, AccROLETests, AccAuthorizationTests, AccACTIONTests,
    ModelDeleteTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
