# -*- coding: utf-8 -*-

## This file is part of Invenio.
## Copyright (C) 2012, 2013, 2014, 2015 CERN.
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

"""Groups Helpers Blueprint."""

from flask import Blueprint, jsonify
from flask.ext.breadcrumbs import default_breadcrumb_root
from flask.ext.login import login_required

from invenio.base.decorators import wash_arguments
from invenio.ext.principal import permission_required
from invenio.ext.sqlalchemy import db
from invenio.modules.accounts.models import User, UserUsergroup, Usergroup

from ..api import GroupsAPI
from ..config import GROUPS_AUTOCOMPLETE_LIMIT

# TODO unified search interface

blueprint = Blueprint(
    'groups_helpers', __name__,
    url_prefix="/account/settings/groups",
    template_folder='../templates',
    static_folder='../static')

default_breadcrumb_root(blueprint, '.settings.groups')


@blueprint.route("/search", methods=['GET', 'POST'])
@login_required
@wash_arguments({"query": (unicode, ""), "term": (unicode, "")})
@permission_required('usegroups')
def search(query, term):
    """Search user groups."""
    # FIXME user can access to all users name?
    # e.g. is better to return only users name that are at least in one group
    # together?
    if query == 'users' and len(term) >= 3:
        res = db.session.query(User.nickname).filter(
            User.nickname.like("%s%%" % term)).limit(10).all()
        return jsonify(nicknames=[elem for elem, in res])
    elif query == 'groups' and len(term) >= 3:
        res = db.session.query(db.func.distinct(Usergroup.name)).\
            join(UserUsergroup).filter(
                Usergroup.name.like("%s%%" % term)).limit(10).all()
        return jsonify(groups=[elem for elem, in res])
    return jsonify()


@blueprint.route("<int:id_usergroup>/users",
                 methods=['GET', 'POST'])
@login_required
@wash_arguments({"query": (unicode, "")})
@permission_required('usegroups')
def search_users(id_usergroup, query):
    """Search user not in a specific group."""
    # group = Usergroup.query.get_or_404(id_usergroup)
    gapi = GroupsAPI(user_group=GroupsAPI.get_group(id_usergroup))
    users = gapi.query_users_not_in_this_group(query="%%%s%%" % query) \
        .limit(GROUPS_AUTOCOMPLETE_LIMIT).all()
    return jsonify(results=[{'id': user.id, 'nickname': user.nickname}
                            for user in users])


@blueprint.route("/search/user/<int:id_user>/groups",
                 methods=['GET', 'POST'])
@login_required
@wash_arguments({"query": (unicode, "")})
@permission_required('usegroups')
def search_groups(id_user, query):
    """Search groups that user not joined."""
    groups = GroupsAPI.query_groups_user_not_joined(
        id_user=id_user, group_name="%%%s%%" % query) \
        .limit(GROUPS_AUTOCOMPLETE_LIMIT).all()
    return jsonify(results=[{'id': group.id, 'name': group.name}
                            for group in groups])


@blueprint.route("/tokenize", methods=['GET', 'POST'])
@login_required
@wash_arguments({"q": (unicode, "")})
@permission_required('usegroups')
def tokenize(q):
    """FIXME."""
    # FIXME can we deprecate this function?
    res = Usergroup.query.filter(
        Usergroup.name.like("%s%%" % q)).limit(GROUPS_AUTOCOMPLETE_LIMIT).all()
    return jsonify(data=map(dict, res))
