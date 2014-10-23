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

from sqlalchemy.exc import IntegrityError

from flask import (Blueprint, render_template, request, jsonify, flash,
                   url_for, redirect)
from flask.ext.breadcrumbs import default_breadcrumb_root, register_breadcrumb
from flask.ext.login import current_user, login_required
from flask.ext.menu import register_menu
from invenio.base.decorators import wash_arguments
from invenio.base.i18n import _
from invenio.ext.sqlalchemy import db
from invenio.modules.accounts.errors import AccountSecurityError, \
    IntegrityUsergroupError
from invenio.modules.accounts.models import User, Usergroup, UserUsergroup, \
    get_groups_user_not_joined

from forms import JoinUsergroupForm, UsergroupForm, UserJoinGroupForm

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
    form = JoinUsergroupForm()
    form.id_usergroup.query = get_groups_user_not_joined(
        current_user['uid']).order_by(Usergroup.name).all()
    user = User.query.get(uid)
    uugs = dict(map(lambda uug: (uug.usergroup.name, uug),
                    user.usergroups))

    return render_template(
        'groups/index.html',
        uugs=uugs,
        form=form,
    )


@blueprint.route('/new', methods=['GET', 'POST'])
@register_breadcrumb(blueprint, '.new', _('New Group'))
@login_required
def new():
    """Create new user group."""
    form = UsergroupForm(request.form)

    if form.validate_on_submit():
        ug = Usergroup()
        id_user = current_user.get_id()
        user2join = User.query.get_or_404(id_user)
        form.populate_obj(ug)
        ug.join(status=UserUsergroup.USER_STATUS['ADMIN'],
                user=user2join)
        db.session.add(ug)
        try:
            db.session.commit()
        except IntegrityError:
            # catch integrity error
            db.session.rollback()
            flash(_('Group properies error'), 'error')
            # reload form with old values
            return render_template(
                "groups/new.html",
                form=form,
                action=_('Create'),
                subtitle=_("New group"),
            )
        except:
            # catch unknown error
            db.session.rollback()
            raise
        # group finally created
        current_user.reload()
        flash(_('Group "%(name)s" successfully created',
                name=ug.name), 'success')
        return redirect(url_for(".index"))

    return render_template(
        "groups/new.html",
        form=form,
        action=_('Create'),
        subtitle=_("New group"),
    )


@blueprint.route('/leave/<int:id_usergroup>')
@blueprint.route('/leave/<int:id_usergroup>/user/<int:id_user>')
@login_required
def leave(id_usergroup, id_user=None):
    """Leave user group.

    :param id_usergroup: Identifier of user group.
    """
    group = Usergroup.query.get_or_404(id_usergroup)
    id_user2remove = id_user or current_user.get_id()
    user2remove = User.query.get_or_404(id_user2remove)
    try:
        group.leave(user2remove)
    except AccountSecurityError:
        flash(_(
            'You have not enough right to '
            'remove user "{0}" from group "{1}"'
            .format(user2remove.nickname, group.name)), "error")
        return redirect(url_for('.index'))
    except IntegrityUsergroupError:
        flash(_(
            'Sorry, user "{0}" can leave the group "{1}" '
            'without admins, please delete the '
            'group if you want to leave.'
            .format(user2remove.nickname, group.name)), "error")
        return redirect(url_for('.index'))

    try:
        db.session.merge(group)
        db.session.commit()
    except:
        db.session.rollback()
        raise

    current_user.reload()
    flash(_('%(user)s left the group "%(name)s".',
            user='User "'+user2remove.nickname+'"' if id_user else "You",
            name=group.name), 'success')
    if id_user and id_user != current_user.get_id():
        return redirect(url_for('.members', id_usergroup=id_usergroup))
    else:
        return redirect(url_for('.index'))


@blueprint.route('/join', methods=['GET', 'POST'])
@blueprint.route('/join/<int:id_usergroup>/users/<int:id_user>',
                 methods=['GET', 'POST'])
@login_required
@wash_arguments({"id_usergroup": (int, 0), "id_user": (int, 0)})
def join(id_usergroup, id_user=None, status=None):
    """Join group."""
    group = Usergroup.query.get_or_404(id_usergroup)
    id_user2join = id_user or current_user.get_id()
    user2join = User.query.get_or_404(id_user2join)
    form = UserJoinGroupForm()
    user_status = None
    if form.user_status and form.user_status.data:
            user_status = UserUsergroup.USER_STATUS['ADMIN']

    try:
        group.join(user2join, status=user_status)
    except AccountSecurityError:
        flash(_(
            'You have not enough right to '
            'add user "{0}" to the group "{1}"'
            .format(user2join.nickname, group.name)), "error")
        return redirect(url_for('.index'))

    current_user.reload()
    flash(_('%(user)s join the group "%(name)s".',
            user='User "'+user2join.nickname+'"' if id_user else "You",
            name=group.name), 'success')
    if id_user:
        return redirect(url_for('.members', id_usergroup=id_usergroup))
    else:
        return redirect(url_for('.index'))


@blueprint.route('/manage/<int:id_usergroup>', methods=['GET', 'POST'])
@register_breadcrumb(blueprint, '.manage', _('Manage Group'))
def manage(id_usergroup):
    """Manage user group."""
    ug = Usergroup.query.filter_by(id=id_usergroup).one()
    form = UsergroupForm(request.form, obj=ug)

    if form.validate_on_submit():
        if not ug.is_admin(current_user.get_id()):
            # not enough right to modify group
            flash(_('Sorry, you don\'t have enough right to be able '
                    'to manage the group "%(name)s"', name=ug.name), 'error')
            return redirect(url_for(".index"))

        # get form data
        ug2form = Usergroup()
        form.populate_obj(ug2form)
        # update group
        oldname = ug.name
        ug.name = ug2form.name
        ug.description = ug2form.description
        ug.join_policy = ug2form.join_policy
        ug.login_method = ug2form.login_method

        # update in db
        try:
            db.session.merge(ug)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash(_('Group properies error'), 'error')
            # reload form with old values
            return render_template(
                "groups/new.html",
                form=form,
                action=_('Update'),
                subtitle=oldname,
            )
        except:
            db.session.rollback()
            raise

        current_user.reload()
        return redirect(url_for(".index"))

    return render_template(
        "groups/new.html",
        form=form,
        action=_('Update'),
        subtitle=ug.name,
    )


@blueprint.route('/manage/<int:id_usergroup>/delete',
                 methods=['GET', 'DELETE'])
def delete(id_usergroup):
    """Delete a group."""
    group = Usergroup.query.get_or_404(id_usergroup)
    id_user = current_user.get_id()
    if group.is_admin(id_user):
        db.session.delete(group)
        db.session.commit()
        current_user.reload()
    else:
        flash(_('Sorry, but you are not an admin of the group "%(name)s".',
                name=group.name), "error")

    return redirect(url_for(".index"))


@blueprint.route('/members/<int:id_usergroup>', methods=['GET', 'POST'])
@register_breadcrumb(blueprint, '.members', _('Members'))
def members(id_usergroup):
    """List user group members."""
    group = Usergroup.query.get_or_404(id_usergroup)
    current_uug = UserUsergroup.query.filter(
        UserUsergroup.id_user == current_user.get_id(),
        UserUsergroup.id_usergroup == group.id).one()
    users_not_in_this_group = UserJoinGroupForm(request.form)
    users_not_in_this_group.id_user.query = group \
        .get_users_not_in_this_group().order_by(User.nickname).all()

    return render_template(
        "groups/members.html",
        group=group,
        current_uug=current_uug,
        form=users_not_in_this_group,
    )


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
