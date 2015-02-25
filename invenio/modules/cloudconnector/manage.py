# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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

"""Manage cloudconnector module."""

from invenio.ext.script import Manager

manager = Manager(usage=__doc__)


@manager.command
@manager.option("-u", "--user", dest="user")
def upload(service, src, dest, user=None):
    """Upload a file."""
    from invenio.ext.login import login_user, logout_user
    from invenio.ext.sqlalchemy import db

    from invenio.modules.accounts.models import User
    from invenio.modules.cloudconnector import utils
    from invenio.modules.oauthclient.views.client import setup_app

    # Get user instance
    user = User.query.filter(db.or_(
        User.nickname == user,
        User.email == user,
        User.id == user)).one()

    login_user(user.id)
    setup_app()
    utils.upload(service, src, dest)
    logout_user()


def main():
    """Execute script."""
    from invenio.base.factory import create_app
    app = create_app()
    manager.app = app
    manager.run()

if __name__ == '__main__':
    main()
