# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012, 2013, 2014 CERN.
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

"""Groups Flask Blueprint."""

from flask import (Blueprint, render_template, request, jsonify, flash,
                   url_for, redirect, abort)
from flask.ext.login import current_user, login_required
from flask.ext.menu import register_menu
from invenio.base.decorators import wash_arguments
from invenio.base.i18n import _
from flask.ext.breadcrumbs import default_breadcrumb_root, register_breadcrumb
from invenio.ext.sqlalchemy import db
from invenio.modules.accounts.models import User, Usergroup, UserUsergroup

from .forms import JoinUsergroupForm, UsergroupForm

blueprint = Blueprint('webgroup', __name__, url_prefix="/yourgroups",
                      template_folder='templates', static_folder='static')

default_breadcrumb_root(blueprint, '.settings.groups')


@blueprint.route('/')
@blueprint.route('/index')
@register_menu(
    blueprint, 'settings.groups',
    _('%(icon)s Groups', icon='<i class="fa fa-group fa-fw"></i>'),
    order=0,
    active_when=lambda: request.endpoint.startswith("webgroup.")
)
@register_breadcrumb(blueprint, '.', _('Groups'))
@login_required
def index():
    """List all user groups."""
    uid = current_user.get_id()
    current_user.reload()
    mg = UserUsergroup.query.join(UserUsergroup.usergroup).filter(
        UserUsergroup.id_user == uid).all()
    member_groups = dict(map(lambda ug: (ug.usergroup.name, ug), mg))

    return render_template(
        'groups/index.html',
        member_groups=member_groups,
        form=JoinUsergroupForm(),
    )


@blueprint.route('/new', methods=['GET', 'POST'])
@register_breadcrumb(blueprint, '.new', _('New Group'))
@login_required
def new():
    """Create new user group."""
    form = UsergroupForm(request.form)

    if form.validate_on_submit():
        ug = Usergroup()
        form.populate_obj(ug)
        ug.join(status=UserUsergroup.USER_STATUS['ADMIN'])
        db.session.add(ug)
        db.session.commit()
        current_user.reload()
        return redirect(url_for(".index"))

    return render_template(
        "groups/new.html",
        form=form,
    )


@blueprint.route('/leave/<int:id_usergroup>')
@login_required
def leave(id_usergroup):
    """Leave user group.

    :param id_usergroup: Identifier of user group.
    """
    group = Usergroup.query.get(id_usergroup)
    if group is None:
        return abort(400)
    group.leave()
    db.session.merge(group)
    db.session.commit()
    current_user.reload()
    flash(_('You left a group %(name)s.', name=group.name), 'success')
    return redirect(url_for('.index'))


@blueprint.route('/join', methods=['GET', 'POST'])
@blueprint.route('/join/<int:id_usergroup>', methods=['GET', 'POST'])
@login_required
@wash_arguments({"id_usergroup": (int, 0)})
def join(id_usergroup, status=None):
    """Join group."""
    group = Usergroup.query.get(id_usergroup)
    if group is None:
        return abort(400)
    group.join()
    db.session.merge(group)
    db.session.commit()
    current_user.reload()
    flash(_('You join a group %(name)s.', name=group.name), 'success')
    return redirect(url_for('.index'))


@blueprint.route('/manage/<int:id_usergroup>', methods=['GET', 'POST'])
def manage(id_usergroup):
    """Manage user group."""
    raise NotImplemented()


@blueprint.route('/members/<int:id_usergroup>', methods=['GET', 'POST'])
def members(id_usergroup):
    """List user group members."""
    raise NotImplemented()


@blueprint.route("/search", methods=['GET', 'POST'])
@wash_arguments({"query": (unicode, ""), "term": (unicode, "")})
def search(query, term):
    """Search user groups."""
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


@blueprint.route("/tokenize", methods=['GET', 'POST'])
@wash_arguments({"q": (unicode, "")})
def tokenize(q):
    """FIXME."""
    res = Usergroup.query.filter(
        Usergroup.name.like("%s%%" % q)).limit(10).all()
    return jsonify(data=map(dict, res))
