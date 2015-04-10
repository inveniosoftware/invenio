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

"""Groups Settings Blueprint."""

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

from ..api import GroupsAPI
from ..forms import UsergroupForm, UsergroupNewMemberForm


# TODO `add` view


blueprint = Blueprint(
    'groups_settings', __name__,
    url_prefix="/account/settings/groups",
    template_folder='../templates',
    static_folder='../static')

default_breadcrumb_root(blueprint, '.settings.groups')


@blueprint.route('/')
@blueprint.route('/index')
@register_menu(
    blueprint, 'settings.groups',
    _('%(icon)s My Groups', icon='<i class="fa fa-users fa-fw"></i>'),
    order=13,  # FIXME which order to choose
    active_when=lambda: request.endpoint.startswith("groups_settings.")
)
@register_breadcrumb(blueprint, '.', _('Groups'))
@login_required
@permission_required('usegroups')
@wash_arguments({
    'page': (int, 1),
    'per_page': (int, 5),
    'p': (unicode, '')
})
def index(page, per_page, p):
    """List all user groups."""
    # FIXME can check be done differently?
    if page <= 0:
        page = 1
    if per_page <= 0:
        per_page = 5

    uid = current_user.get_id()
    ugs = GroupsAPI.query_list_usergroups(
        uid, p).paginate(page, per_page, error_out=False)
    pending_ugs = GroupsAPI.query_pending_usergroups(uid).all()
    members = dict(
        (
            ug.id, filter(lambda uug: uug.user_status != "PENDING", ug.users)
        ) for ug in ugs.items
    )

    return render_template(
        'groups/settings.html',
        ugs=ugs,
        pending_ugs=pending_ugs,
        members=members,
        page=page,
        per_page=per_page,
        p=p
    )


@blueprint.route('/new', methods=['GET', 'POST'])
@register_breadcrumb(blueprint, '.new', _('New'))
@login_required
@permission_required('usegroups')
def new():
    """Create new user group."""
    form = UsergroupForm(request.form)

    if request.method == 'POST' and form.validate():
        ug = Usergroup()
        id_user = current_user.get_id()
        form.populate_obj(ug)
        try:
            ug = GroupsAPI.create(uid=id_user, group=ug)
        except (IntegrityError, AccountSecurityError,
                IntegrityUsergroupError, IntegrityError) as e:
            db.session.rollback()
            flash(str(e), 'error')
            # reload form with old values
            return render_template(
                "groups/new.html",
                form=form,
            )
        # redirect to see the group's list
        flash(_('Group "%(name)s" successfully created',
                name=ug.name), 'success')
        return redirect(url_for(".index"))

    # open the form to create new group
    return render_template(
        "groups/new.html",
        form=form,
    )


@blueprint.route('/<int:ug_id>/members/approve')
@blueprint.route('/<int:ug_id>/members/<int:id_user>/approve')
@login_required
@permission_required('usegroups')
def approve(ug_id, id_user=None):
    """Approve a user."""
    # load data
    curr_uid = not current_user.get_id()
    id_user2approve = id_user or curr_uid
    user2approve = User.query.get_or_404(id_user2approve)
    gapi = GroupsAPI(user_group=GroupsAPI.get_group(ug_id))
    try:
        gapi.approve_user(id_user=id_user2approve)
    except AccountSecurityError, e:
        flash(str(e), 'error')
        # redirect
        return redirect(url_for('.members', ug_id=ug_id))

    flash(_('%(user)s successfully approved in the group "%(name)s".',
            user='User "'+user2approve.nickname+'"' if id_user else "You",
            name=gapi.user_group.name), 'success')
    return redirect(url_for('.members', ug_id=ug_id))


@blueprint.route('/<int:ug_id>/members/accept')
@login_required
@permission_required('usegroups')
def accept(ug_id):
    """Approve a user."""
    # load data
    curr_uid = current_user.get_id()
    user2approve = User.query.get_or_404(curr_uid)
    gapi = GroupsAPI(user_group=GroupsAPI.get_group(ug_id))
    try:
        gapi.approve_user(id_user=curr_uid)
    except AccountSecurityError, e:
        flash(str(e), 'error')
        # redirect
        return redirect(url_for('.members', ug_id=ug_id))

    flash(_('%(user)s successfully approved in the group "%(name)s".',
            user='User "'+user2approve.nickname+'"',
            name=gapi.user_group.name), 'success')
    return redirect(url_for('.members', ug_id=ug_id))


@blueprint.route('/<int:ug_id>/members/<int:id_user>/remove')
@blueprint.route('/<int:ug_id>/members/<int:id_user>/reject')
@blueprint.route('/<int:ug_id>/leave')
@login_required
@permission_required('usegroups')
def leave(ug_id, id_user=None):
    """Leave user group.

    :param ug_id: Identifier of user group.
    """
    # load data
    curr_uid = current_user.get_id()
    id_user2remove = id_user or curr_uid
    user2remove = User.query.get_or_404(id_user2remove)
    gapi = GroupsAPI(user_group=GroupsAPI.get_group(ug_id))
    # user leave the group
    try:
        gapi.remove(id_user=id_user2remove)
    except (AccountSecurityError, IntegrityUsergroupError) as e:
        # catch security errors
        flash(str(e), "error")
        return redirect(url_for('.index'))

    # return successful message
    flash(_('%(user)s left the group "%(name)s".',
            user='User "'+user2remove.nickname+'"' if id_user else "You",
            name=gapi.user_group.name), 'success')
    if id_user and id_user != curr_uid:
        return redirect(url_for('.members', ug_id=ug_id))
    else:
        return redirect(url_for('.index'))


@blueprint.route('/<int:ug_id>/members/reject')
@login_required
@permission_required('usegroups')
def reject(ug_id):
    """Leave user group.

    :param ug_id: Identifier of user group.
    """
    # load data
    curr_uid = current_user.get_id()
    user2remove = User.query.get_or_404(curr_uid)
    gapi = GroupsAPI(user_group=GroupsAPI.get_group(ug_id))
    # user leave the group
    try:
        gapi.remove(id_user=curr_uid)
    except (AccountSecurityError, IntegrityUsergroupError) as e:
        # catch security errors
        flash(str(e), "error")
        return redirect(url_for('.index'))

    # return successful message
    flash(_('%(user)s left the group "%(name)s".',
            user='User "'+user2remove.nickname+'"',
            name=gapi.user_group.name), 'success')
    return redirect(url_for('.index'))


@blueprint.route('/<int:ug_id>/members/<int:id_user>/add',
                 methods=['GET', 'POST'])
@login_required
@wash_arguments({"ug_id": (int, 0), "id_user": (int, 0)})
@permission_required('usegroups')
def join(ug_id, id_user=None, status=None):
    """Join group."""
    # load data
    curr_uid = current_user.get_id()
    id_user2join = id_user or curr_uid
    user2join = User.query.get_or_404(id_user2join)
    user_status = None
    # read status from the form (checkbox)
    user_status = u'PENDING'
    gapi = GroupsAPI(user_group=GroupsAPI.get_group(ug_id))
    # user join the group
    try:
        gapi.add(id_user=user2join.id, status=user_status)
    except (AccountSecurityError, SQLAlchemyError) as e:
        # catch security errors
        flash(str(e), "error")
        return redirect(url_for('.index'))
        if id_user:
            return redirect(url_for('.members', ug_id=ug_id))
        else:
            return redirect(url_for('.index'))

    # return successful message
    flash(_('%(user)s join the group "%(name)s".',
            user='User "'+user2join.nickname+'"' if id_user else "You",
            name=gapi.user_group.name), 'success')

    redirect_url = url_for('.index')
    return redirect(redirect_url)


@blueprint.route('/<int:ug_id>/manage', methods=['GET', 'POST'])
@blueprint.route('/<int:ug_id>/', methods=['GET', 'POST'])
@login_required
@register_breadcrumb(
    blueprint, '.manage', _('Manage'),
    dynamic_list_constructor=lambda:
        [{'text': get_group_name(request.view_args['ug_id'])},
         {'text': _('Manage')}]
)
@permission_required('usegroups')
def manage(ug_id):
    """Manage user group."""
    gapi = GroupsAPI(user_group=GroupsAPI.get_group(ug_id))
    try:
        gapi.check_access()
    except AccountSecurityError, e:
        flash(str(e), "error")
        return redirect(url_for(".index"))
    # load data
    form = UsergroupForm(request.form, obj=gapi.user_group)

    if request.method == 'POST' and form.validate():
        # get form data
        ug2form = Usergroup()
        form.populate_obj(ug2form)
        # save old group's name
        oldname = gapi.user_group.name

        # update in db
        try:
            gapi.update(group=ug2form)
        except (AccountSecurityError, IntegrityError, SQLAlchemyError) as e:
            db.session.rollback()
            flash(str(e), 'error')
            # reload form with old values
            return render_template(
                "groups/new.html",
                form=form,
                group=gapi.user_group,
            )

        # return successful message
        return redirect(url_for(".index"))

    # load form
    return render_template(
        "groups/new.html",
        form=form,
        group=gapi.user_group,
    )


@blueprint.route('/<int:ug_id>/delete',
                 methods=['GET', 'DELETE'])
@login_required
@permission_required('usegroups')
def delete(ug_id):
    """Delete a group."""
    # load data
    gapi = GroupsAPI(user_group=GroupsAPI.get_group(ug_id))
    try:
        gapi.check_access()
        # delete group
        gapi.delete()
    except AccountSecurityError, e:
        flash(str(e), "error")
        return redirect(url_for(".index"))

    group_name = gapi.user_group.name
    # return successful message
    flash(_('Successfully removed the group "%(group_name)s"',
            group_name=group_name), 'success')
    return redirect(url_for(".index"))


def get_group_name(ug_id):
    try:
        gapi = GroupsAPI(user_group=GroupsAPI.get_group(ug_id))
        gapi.check_access()
        return gapi.user_group.name
    except AccountSecurityError:
        return ''


@blueprint.route('/<int:ug_id>/members', methods=['GET', 'POST'])
@login_required
@register_breadcrumb(
    blueprint, '.members', _('Members'),
    dynamic_list_constructor=lambda:
        [{'text': get_group_name(request.view_args['ug_id'])},
         {'text': _('Members')}]
)
@permission_required('usegroups')
@wash_arguments({
    'page': (int, 1),
    'per_page': (int, 5),
    'p': (unicode, ''),
    's': (unicode, ''),
})
def members(ug_id, page, per_page, p, s):
    """List user group members."""
    # FIXME can check be done differently?
    if page <= 0:
        page = 1
    if per_page <= 0:
        per_page = 5

    # load data
    try:
        gapi = GroupsAPI(user_group=GroupsAPI.get_group(ug_id))
        gapi.check_access()
        if (
            not gapi.user_group.is_admin(current_user.get_id()) and
            gapi.user_group.members_visibility == "INVISIBLE"
        ):
            raise AccountSecurityError(_('Cannot see other members'))
    except AccountSecurityError, e:
        flash(str(e), 'error')
        return redirect(url_for('.index'))

    group = gapi.user_group
    members = gapi.query_members(p, s).paginate(page, per_page, error_out=False)

    return render_template(
        "groups/members.html",
        group=group,
        members=members,
        page=page,
        per_page=per_page,
        p=p,
        s=s,
    )


@blueprint.route('/<int:ug_id>/members/new', methods=['GET', 'POST'])
@login_required
@register_breadcrumb(blueprint, '.members.new', _('New'))
@permission_required('usegroups')
def new_member(ug_id):
    """List user group members."""
    try:
        gapi = GroupsAPI(user_group=GroupsAPI.get_group(ug_id))
        gapi.check_access()
    except AccountSecurityError, e:
        flash(str(e), 'error')
        return redirect(url_for('.index'))

    form = UsergroupNewMemberForm(request.form)

    if request.method == 'POST':
        data = request.get_json()
        try:
            gapi.invite(emails=data['emails'], status=data['user_status'])
            url = url_for(".members", ug_id=gapi.user_group.id)
            return jsonify(url=url)
        except Exception:
            pass

    return render_template(
        "groups/new_member.html",
        group=gapi.user_group,
        form=form,
    )
