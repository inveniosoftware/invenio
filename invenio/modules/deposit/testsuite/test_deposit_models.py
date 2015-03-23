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

"""Unit tests for the Deposit models."""

from flask_registry import RegistryError
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase


class DepositionTest(InvenioTestCase):
    def setUp(self):
        from invenio.modules.deposit.models import DepositionType
        from invenio.modules.deposit.registry import deposit_types, \
            deposit_default_type

        # Unregister any default types
        try:
            deposit_default_type.unregister()
        except RegistryError:
            pass

        # Create some test types.
        class DefaultType(DepositionType):
            pass

        class AnotherType(DepositionType):
            pass

        # Register types
        self.DefaultType = DefaultType
        self.AnotherType = AnotherType
        deposit_types.register(DefaultType)
        deposit_types.register(AnotherType)
        deposit_default_type.register(DefaultType)

    def test_create(self):
        from invenio.ext.login.legacy_user import UserInfo
        from invenio.modules.deposit.models import Deposition

        user = UserInfo(uid=1)
        d = Deposition.create(user)
        assert d.type == self.DefaultType
        assert Deposition.get(d.id).type == self.DefaultType
        d = Deposition.create(user, type=self.AnotherType)
        assert d.type == self.AnotherType
        assert Deposition.get(d.id).type == self.AnotherType

TEST_SUITE = make_test_suite(DepositionTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
