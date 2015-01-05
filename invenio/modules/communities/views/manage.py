# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014, 2015 CERN.
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

"""Community Manage Blueprint."""

from __future__ import absolute_import

from flask import Blueprint, render_template, \
    request, abort, flash, redirect, url_for, jsonify
from flask.ext.breadcrumbs import register_breadcrumb
from flask.ext.login import current_user, login_required
from invenio.base.i18n import _
from invenio.ext.sslify import ssl_required
from invenio.ext.principal import permission_required
from invenio.ext.sqlalchemy import db
from invenio.modules.accounts.models import Usergroup
from invenio.modules.groups.api import GroupsAPI

from ..helpers import save_and_validate_logo
from .communities import mycommunities_ctx
from ..forms import EditCommunityForm, DeleteCommunityForm, EditTeamForm
from ..models import Community, CommunityTeam


blueprint = Blueprint(
    'community_manage', __name__,
    url_prefix="/account/settings/communities",
    template_folder='../templates',
    static_folder='../static'
)


@blueprint.route('/<string:community_id>/guides/', methods=['GET', 'POST'])
@ssl_required
@login_required
@permission_required('submit')
@register_breadcrumb(
    blueprint, 'breadcrumbs.settings.communities.guides', _('Guides'),
    dynamic_list_constructor=lambda:
        [{'text': get_community_title(request.view_args['community_id'])},
         {'text': _('Guides')}]
)
def guides(community_id):
    u = Community.query.filter_by(id=community_id).first_or_404()
    uid = current_user.get_id()

    # Check ownership
    if u.id_user != uid:
        abort(404)

    ctx = mycommunities_ctx()
    ctx.update({
        'community': u,
    })

    return render_template(
        "communities/guides.html",
        **ctx
    )


@blueprint.route('/<string:community_id>/people/', methods=['GET', 'POST'])
@ssl_required
@login_required
@permission_required('submit')
@register_breadcrumb(
    blueprint, 'breadcrumbs.settings.communities.people', _('People'),
    dynamic_list_constructor=lambda:
        [{'text': get_community_title(request.view_args['community_id'])},
         {'text': _('People')}]
)
def people(community_id):
    u = Community.query.filter_by(id=community_id).first_or_404()
    uid = current_user.get_id()

    members = []

    for team in u.teams:
        for uug in team.usergroup.users:
            members.append(uug.user)

    # Check ownership
    if u.id_user != uid:
        abort(404)

    ctx = mycommunities_ctx()
    ctx.update({
        'community': u,
    })

    return render_template(
        "communities/people.html",
        members=members,
        **ctx
    )


def get_community_title(c_id):
    u = Community.query.filter_by(id=c_id).first_or_404()
    return u.title


@blueprint.route('/<string:community_id>/settings/', methods=['GET', 'POST'])
@ssl_required
@login_required
@permission_required('submit')
@register_breadcrumb(
    blueprint, 'breadcrumbs.settings.communities.settings', _('Settings'),
    dynamic_list_constructor=lambda:
        [{'text': get_community_title(request.view_args['community_id'])},
         {'text': _('Settings')}]
)
def manage(community_id):
    """Create or edit a community."""
    # Check existence of community
    u = Community.query.filter_by(id=community_id).first_or_404()
    uid = current_user.get_id()

    # Check ownership
    if u.id_user != uid:
        abort(404)

    form = EditCommunityForm(request.values, u, crsf_enabled=False)
    deleteform = DeleteCommunityForm()
    ctx = mycommunities_ctx()
    ctx.update({
        'form': form,
        'is_new': False,
        'community': u,
        'deleteform': deleteform,
    })

    if request.method == 'POST' and form.validate():
        file = request.files.get('logo', None)
        if file:
            logo_ext = save_and_validate_logo(file, u.id, u.logo_ext)
            if not logo_ext:
                form.logo.errors.append(
                    _(
                        'Cannot add this file as a logo.'
                        ' Supported formats: png and jpg.'
                        ' Max file size: 1.5MB'
                    )
                )
            else:
                setattr(u, 'logo_ext', logo_ext)
        if not file or (file and logo_ext):
            for field, val in form.data.items():
                if field == "logo":
                    continue
                setattr(u, field, val)
            db.session.commit()
            u.save_collections()
            flash("Community successfully edited.", category='success')
            return redirect(url_for('.manage', community_id=u.id))

    return render_template(
        "communities/manage.html",
        **ctx
    )


@blueprint.route('/<string:community_id>/teams/', methods=['GET', 'POST'])
@ssl_required
@login_required
@permission_required('submit')
@register_breadcrumb(
    blueprint, 'breadcrumbs.settings.communities.teams', _('Teams'),
    dynamic_list_constructor=lambda:
        [{'text': get_community_title(request.view_args['community_id'])},
         {'text': _('Teams')}]
)
def teams(community_id):
    u = Community.query.filter_by(id=community_id).first_or_404()
    uid = current_user.get_id()

    # Check ownership
    if u.id_user != uid:
        abort(404)

    teams = CommunityTeam.query.filter(CommunityTeam.id_community == u.id).all()

    ctx = mycommunities_ctx()
    ctx.update({
        'community': u,
        'teams': teams,
    })

    return render_template(
        "communities/teams.html",
        **ctx
    )


@blueprint.route(
    '/<string:community_id>/teams/new',
    methods=['GET', 'POST'])
@ssl_required
@login_required
@permission_required('submit')
@register_breadcrumb(
    blueprint, 'breadcrumbs.settings.communities.team_new', _('New'),
    dynamic_list_constructor=lambda:
        [{'text': get_community_title(request.view_args['community_id'])},
         {'text': _('Teams')},
         {'text': _('New')}]
)
def teams_new(community_id):
    u = Community.query.filter_by(id=community_id).first_or_404()
    uid = current_user.get_id()
    form = EditTeamForm(request.values, crsf_enabled=False)

    # Check ownership
    if u.id_user != uid:
        abort(404)

    if request.method == 'POST' and form.validate():
        ug = Usergroup(
            name=form.data['name'],
            description=form.data['description']
        )
        try:
            ug = GroupsAPI.create(uid=uid, group=ug)
        except Exception as e:
            db.session.rollback()
            flash(str(e), 'error')
            # reload form with old values
            return render_template(
                "communities/teams_new.html",
                community=u,
                form=form,
            )
        ct = CommunityTeam(
            id_community=u.id,
            id_usergroup=ug.id,
            team_rights=form.data['permissions'],
        )
        db.session.add(ct)
        db.session.commit()
        # redirect to see the group's list
        flash(_('Team "%(name)s" successfully created',
                name=ug.name), 'success')
        return redirect(url_for(".teams", community_id=u.id))

    ctx = mycommunities_ctx()
    ctx.update({
        'community': u,
        'form': form,
        'isNew': True
    })

    return render_template(
        "communities/teams_new.html",
        **ctx
    )


@blueprint.route(
    '/<string:community_id>/teams/<string:team>/settings/',
    methods=['GET', 'POST'])
@ssl_required
@login_required
@permission_required('submit')
@register_breadcrumb(
    blueprint, 'breadcrumbs.settings.communities.team_settings', _('Settings'),
    dynamic_list_constructor=lambda:
        [{'text': get_community_title(request.view_args['community_id'])},
         {'text': _('Teams')},
         {'text': request.view_args['team'].title()},
         {'text': _('Settings')}]
)
def teams_manage(community_id, team=""):
    u = Community.query.filter_by(id=community_id).first_or_404()
    uid = current_user.get_id()

    ug = Usergroup.query.filter(Usergroup.name == team).first_or_404()
    ct = CommunityTeam.query.filter(
        CommunityTeam.id_usergroup == ug.id).first_or_404()
    form = EditTeamForm(
        name=ug.name,
        description=ug.description,
        permissions=ct.team_rights,
        crsf_enabled=False)

    # Check ownership
    if u.id_user != uid:
        abort(404)

    if request.method == 'POST' and form.validate():
        ug.name = form.data['name']
        ug.description = form.data['description']
        ct.team_rights = form.data['permissions']
        db.session.add(ug)
        db.session.add(ct)
        db.session.commit()
        # redirect to see the group's list
        flash(_('Team "%(name)s" successfully updated',
                name=ug.name), 'success')
        return redirect(url_for(".teams", community_id=u.id))

    ctx = mycommunities_ctx()
    ctx.update({
        'community': u,
        'form': form,
        'group': ug,
        'team': ct,
        'isNew': False
    })

    return render_template(
        "communities/teams_manage.html",
        **ctx
    )


@blueprint.route(
    '/<string:community_id>/teams/<string:team>/delete/',
    methods=['POST'])
@ssl_required
@login_required
@permission_required('submit')
def teams_delete(community_id, team=""):
    u = Community.query.filter_by(id=community_id).first_or_404()
    ug = Usergroup.query.filter(Usergroup.name == team).first_or_404()
    ct = CommunityTeam.query.filter(
        CommunityTeam.id_usergroup == ug.id).first_or_404()
    db.session.delete(ct)
    db.session.commit()

    flash(_('Team "%(name)s" successfully deleted',
            name=ug.name), 'success')
    return redirect(url_for(".teams", community_id=u.id))


@blueprint.route(
    '/<string:community_id>/teams/<string:team>/members/',
    methods=['GET', 'POST'])
@ssl_required
@login_required
@permission_required('submit')
@register_breadcrumb(
    blueprint, 'breadcrumbs.settings.communities.team_members', _('Members'),
    dynamic_list_constructor=lambda:
        [{'text': get_community_title(request.view_args['community_id'])},
         {'text': _('Teams')},
         {'text': request.view_args['team'].title()},
         {'text': _('Members')}]
)
def teams_members(community_id, team):
    u = Community.query.filter_by(id=community_id).first_or_404()
    uid = current_user.get_id()

    ug = Usergroup.query.filter(Usergroup.name == team).first_or_404()

    # Check ownership
    if u.id_user != uid:
        abort(404)

    ctx = mycommunities_ctx()
    ctx.update({
        'community': u,
        'members': ug.users,
        'group': ug,
    })

    return render_template(
        "communities/teams_members.html",
        **ctx
    )


@blueprint.route(
    '/<string:community_id>/people/invite',
    methods=['GET', 'POST'])
@ssl_required
@login_required
@permission_required('submit')
@register_breadcrumb(
    blueprint, 'breadcrumbs.settings.communities.team_members', _('Members'),
    dynamic_list_constructor=lambda:
        [{'text': get_community_title(request.view_args['community_id'])},
         {'text': _('People')},
         {'text': _('Invite')}]
)
def people_invite(community_id):
    u = Community.query.filter_by(id=community_id).first_or_404()
    uid = current_user.get_id()

    # Check ownership
    if u.id_user != uid:
        abort(404)

    if request.method == "POST":
        import ipdb
        ipdb.set_trace()

    ctx = mycommunities_ctx()
    ctx.update({
        'community': u,
    })

    return render_template(
        "communities/people_invite.html",
        **ctx
    )


@blueprint.route('/<string:community_id>/delete', methods=['POST'])
@ssl_required
@login_required
@permission_required('submit')
def delete(community_id):
    """Delete a community."""
    # Check existence of community

    u = Community.query.filter_by(id=community_id).first_or_404()
    uid = current_user.get_id()

    # Check ownership
    if u.id_user != uid:
        abort(404)

    ctx = mycommunities_ctx()
    ctx.update({
        'community': u,
    })

    if request.method == 'POST':
        u.delete_collections()
        db.session.delete(u)
        db.session.commit()
        flash("Community was successfully deleted.", category='success')
        return redirect(url_for('communities_settings.index'))
    else:
        flash("Community could not be deleted.", category='warning')
        return redirect(url_for('community_manage.manage', community_id=u.id))
