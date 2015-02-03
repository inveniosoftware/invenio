# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2014, 2015 CERN.
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

"""Groups Flask Blueprint."""

from __future__ import unicode_literals

from flask import Blueprint, flash, jsonify, redirect, render_template, \
    request, url_for

from flask_breadcrumbs import default_breadcrumb_root, register_breadcrumb

from flask_login import current_user, login_required

from flask_menu import register_menu

from invenio.base.decorators import wash_arguments
from invenio.base.i18n import _
from invenio.ext.principal import permission_required
from invenio.ext.sqlalchemy import db
from invenio.modules.accounts.errors import AccountSecurityError, \
    IntegrityUsergroupError
from invenio.modules.accounts.models import User, UserUsergroup, Usergroup, \
    get_groups_user_not_joined

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from .api import GroupsAPI
from .config import GROUPS_AUTOCOMPLETE_LIMIT
from .forms import JoinUsergroupForm, UserJoinGroupForm, UsergroupForm

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
@permission_required('usegroups')
def index():
    """List all user groups."""
    uid = current_user.get_id()
    # current_user.reload()
    form = JoinUsergroupForm()
    form.id_usergroup.set_remote(
        url_for('webgroup.search_groups', id_user=uid)
        + "?query=%QUERY")
    ouugs = GroupsAPI.query_list_userusergroups(uid).all()
    uugs = dict(map(lambda uug: (uug.usergroup.name, uug), ouugs))

    return render_template(
        'groups/index.html',
        uugs=uugs,
        form=form,
    )


@blueprint.route('/new', methods=['GET', 'POST'])
@register_breadcrumb(blueprint, '.new', _('New Group'))
@login_required
@permission_required('usegroups')
def new():
    """Create new user group."""
    form = UsergroupForm(request.form)

    if form.validate_on_submit():
        ug = Usergroup()
        id_user = current_user.get_id()
        form.populate_obj(ug)
        try:
            ug = GroupsAPI.create_group(uid=id_user, group=ug)
        except (IntegrityError, AccountSecurityError,
                IntegrityUsergroupError, IntegrityError) as e:
            db.session.rollback()
            flash(str(e), 'error')
            # reload form with old values
            return render_template(
                "groups/new.html",
                form=form,
                action=_('Create'),
                subtitle=_("New group"),
            )
        # update user info
        current_user.reload()
        # redirect to see the group's list
        flash(_('Group "%(name)s" successfully created',
                name=ug.name), 'success')
        return redirect(url_for(".index"))

    # open the form to create new group
    return render_template(
        "groups/new.html",
        form=form,
        action=_('Create'),
        subtitle=_("New group"),
    )


@blueprint.route('/approve/<int:id_usergroup>')
@blueprint.route('/approve/<int:id_usergroup>/user/<int:id_user>')
@login_required
@permission_required('usegroups')
def approve(id_usergroup, id_user=None):
    """Approve a user."""
    # load data
    curr_uid = current_user.get_id()
    id_user2approve = id_user or curr_uid
    user2approve = User.query.get_or_404(id_user2approve)
    gapi = GroupsAPI(user_group=GroupsAPI.get_group(id_usergroup))
    try:
        gapi.approve_user_in_group(id_user=id_user2approve)
    except AccountSecurityError, e:
        flash(str(e), 'error')
        # redirect
        return redirect(url_for('.members', id_usergroup=id_usergroup))

    # after user update
    current_user.reload()
    flash(_('%(user)s successfully approved in the group "%(name)s".',
            user='User "'+user2approve.nickname+'"' if id_user else "You",
            name=gapi.user_group.name), 'success')
    return redirect(url_for('.members', id_usergroup=id_usergroup))


@blueprint.route('/leave/<int:id_usergroup>')
@blueprint.route('/leave/<int:id_usergroup>/user/<int:id_user>')
@login_required
@permission_required('usegroups')
def leave(id_usergroup, id_user=None):
    """Leave user group.

    :param id_usergroup: Identifier of user group.
    """
    # load data
    curr_uid = current_user.get_id()
    id_user2remove = id_user or curr_uid
    user2remove = User.query.get_or_404(id_user2remove)
    gapi = GroupsAPI(user_group=GroupsAPI.get_group(id_usergroup))
    # user leave the group
    try:
        gapi.remove_user_from_group(id_user=id_user2remove)
    except (AccountSecurityError, IntegrityUsergroupError) as e:
        # catch security errors
        flash(str(e), "error")
        return redirect(url_for('.index'))

    # return successful message
    current_user.reload()
    flash(_('%(user)s left the group "%(name)s".',
            user='User "'+user2remove.nickname+'"' if id_user else "You",
            name=gapi.user_group.name), 'success')
    if id_user and id_user != curr_uid:
        return redirect(url_for('.members', id_usergroup=id_usergroup))
    else:
        return redirect(url_for('.index'))


@blueprint.route('/join', methods=['GET', 'POST'])
@blueprint.route('/join/<int:id_usergroup>/users/<int:id_user>',
                 methods=['GET', 'POST'])
@login_required
@wash_arguments({"id_usergroup": (int, 0), "id_user": (int, 0)})
@permission_required('usegroups')
def join(id_usergroup, id_user=None, status=None):
    """Join group."""
    # load data
    curr_uid = current_user.get_id()
    id_user2join = id_user or curr_uid
    user2join = User.query.get_or_404(id_user2join)
    form = UserJoinGroupForm()
    user_status = None
    # read status from the form (checkbox)
    if form.user_status and form.user_status.data:
        user_status = UserUsergroup.USER_STATUS['ADMIN']
    else:
        user_status = UserUsergroup.USER_STATUS['MEMBER']
    gapi = GroupsAPI(user_group=GroupsAPI.get_group(id_usergroup))
    # user join the group
    try:
        gapi.add_user_to_group(id_user=user2join.id, status=user_status)
    except (AccountSecurityError, SQLAlchemyError) as e:
        # catch security errors
        flash(str(e), "error")
        return redirect(url_for('.index'))
        if id_user:
            return redirect(url_for('.members', id_usergroup=id_usergroup))
        else:
            return redirect(url_for('.index'))

    # return successful message
    current_user.reload()
    flash(_('%(user)s join the group "%(name)s".',
            user='User "'+user2join.nickname+'"' if id_user else "You",
            name=gapi.user_group.name), 'success')

    redirect_url = form.redirect_url.data or url_for('.index')
    return redirect(redirect_url)


@blueprint.route('/manage/<int:id_usergroup>', methods=['GET', 'POST'])
@login_required
@register_breadcrumb(blueprint, '.manage', _('Manage Group'))
@permission_required('usegroups')
def manage(id_usergroup):
    """Manage user group."""
    gapi = GroupsAPI(user_group=GroupsAPI.get_group(id_usergroup))
    # load data
    form = UsergroupForm(request.form, obj=gapi.user_group)

    if form.validate_on_submit():
        # get form data
        ug2form = Usergroup()
        form.populate_obj(ug2form)
        # save old group's name
        oldname = gapi.user_group.name

        # update in db
        try:
            gapi.update_group(group=ug2form)
        except (AccountSecurityError, IntegrityError, SQLAlchemyError) as e:
            db.session.rollback()
            flash(str(e), 'error')
            # reload form with old values
            return render_template(
                "groups/new.html",
                form=form,
                action=_('Update'),
                subtitle=oldname,
            )

        # return successful message
        current_user.reload()
        return redirect(url_for(".index"))

    # load form
    return render_template(
        "groups/new.html",
        form=form,
        action=_('Update'),
        subtitle=gapi.user_group.name,
    )


@blueprint.route('/manage/<int:id_usergroup>/delete',
                 methods=['GET', 'DELETE'])
@login_required
@permission_required('usegroups')
def delete(id_usergroup):
    """Delete a group."""
    # load data
    gapi = GroupsAPI(user_group=GroupsAPI.get_group(id_usergroup))
    group_name = gapi.user_group.name
    # delete group
    try:
        gapi.delete_group()
    except AccountSecurityError, e:
        flash(str(e), "error")
        return redirect(url_for(".index"))

    # return successful message
    flash(_('Successfully removed the group "%(group_name)s"',
            group_name=group_name), 'success')
    return redirect(url_for(".index"))


@blueprint.route('/members/<int:id_usergroup>', methods=['GET', 'POST'])
@login_required
@register_breadcrumb(blueprint, '.members', _('Members'))
@permission_required('usegroups')
def members(id_usergroup):
    """List user group members."""
    # load data
    try:
        gapi = GroupsAPI(user_group=GroupsAPI.get_group(id_usergroup))
    except AccountSecurityError, e:
        flash(str(e), 'error')
        return redirect(url_for('.index'))

    current_uug = gapi.get_info_about_user_in_group()

    unitg = UserJoinGroupForm(request.form)
    unitg.id_user.set_remote(
        url_for('webgroup.search_users', id_usergroup=id_usergroup)
        + "?query=%QUERY")
    unitg.id_usergroup.data = id_usergroup
    unitg.redirect_url.data = url_for(
        ".members", id_usergroup=id_usergroup)

    return render_template(
        "groups/members.html",
        group=gapi.user_group,
        current_uug=current_uug,
        form=unitg,
    )


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


@blueprint.route("/search/group/<int:id_usergroup>/users",
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
