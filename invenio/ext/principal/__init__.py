# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012, 2013 CERN.
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

"""
    invenio.ext.principal
    ---------------------

    This module provides initialization and configuration for
    `flask.ext.principal` module.
"""

from flask import current_app
from flask.ext.login import current_user, user_logged_in, user_logged_out
from flask.ext.principal import Principal, Identity, AnonymousIdentity, \
    identity_changed, Permission

principals = Principal()


class AccAuthorizeActionPermission(Permission):

    def __init__(self, action, **kwargs):
        self.action = action
        self.params = kwargs
        super(self.__class__, self).__init__()

    def allows(self, identity):
        from invenio.access_control_engine import acc_authorize_action
        auth, message = acc_authorize_action(
            identity.id, self.action, **dict(
                (k, v() if callable(v) else v)
                for (k, v) in self.params.iteritems()))
        if auth == 0:
            return True
        current_app.logger.info(message)
        return False


def permission_required(action, **kwargs):
    return AccAuthorizeActionPermission(action, **kwargs).require()


def setup_app(app):

    principals.init_app(app)

    @user_logged_in.connect_via(app)
    def _logged_in(sender, user):
        identity_changed.send(sender, identity=Identity(user.get_id()))

    @user_logged_out.connect_via(app)
    def _logged_out(sender, user):
        identity_changed.send(sender, identity=AnonymousIdentity())

    #@identity_loaded.connect_via(app)
    #def on_identity_loaded(sender, identity):
    #    """One can modify idenity object."""
    #    pass

    return app
