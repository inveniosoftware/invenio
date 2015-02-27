# -*- coding: utf-8 -*-

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

"""Community Teams Blueprint."""

from __future__ import absolute_import

from flask import render_template, abort, request, \
    redirect, url_for, jsonify, Blueprint
from flask.ext.breadcrumbs import register_breadcrumb
from flask.ext.login import current_user, login_required

from invenio.base.i18n import _
from invenio.ext.cache import cache
from invenio.ext.principal import permission_required
from invenio.ext.sslify import ssl_required
from invenio.ext.sqlalchemy import db
from invenio.utils.pagination import Pagination

from ..models import Community, FeaturedCommunity
from ..signals import curate_record
from invenio.base.globals import cfg


blueprint = Blueprint(
    'community_teams', __name__,
    url_prefix="/account/settings/communities",
    template_folder='../templates',
    static_folder='../static'
)


@blueprint.app_template_filter('mycommunities_ctx')
def mycommunities_ctx():
    """Helper method for return ctx used by many views."""
    return {
        'mycommunities': Community.query.filter_by(
            id_user=current_user.get_id()).order_by(db.asc(Community.title)).all()
    }


@blueprint.route('/<string:community_id>/teams/', methods=['GET', 'POST'])
@ssl_required
@login_required
@permission_required('submit')
@register_breadcrumb(
    blueprint, 'breadcrumbs.settings.communities.teams', _('Teams'),
    dynamic_list_constructor=lambda:
        [{'text': request.view_args['community_id'].title()},
         {'text': _('Teams')}]
)
def teams(community_id):
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
        "communities/teams.html",
        **ctx
    )


@blueprint.route('/<string:community_id>/teams/<string:team_id>/members/', methods=['GET', 'POST'])
@ssl_required
@login_required
@permission_required('submit')
@register_breadcrumb(
    blueprint, 'breadcrumbs.settings.communities.team_members', _('Members'),
    dynamic_list_constructor=lambda:
        [{'text': request.view_args['community_id'].title()},
         {'text': _('Teams')},
         {'text': request.view_args['team_id'].title()},
         {'text': _('Members')}]
)
def teams_members(community_id, team_id):
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
        "communities/teams_members.html",
        **ctx
    )


@blueprint.route('/<string:community_id>/teams/<string:team_id>/settings/', methods=['GET', 'POST'])
@ssl_required
@login_required
@permission_required('submit')
@register_breadcrumb(
    blueprint, 'breadcrumbs.settings.communities.team_settings', _('Settings'),
    dynamic_list_constructor=lambda:
        [{'text': request.view_args['community_id'].title()},
         {'text': _('Teams')},
         {'text': request.view_args['team_id'].title()},
         {'text': _('Settings')}]
)
def teams_new(community_id, team_id=""):
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
        "communities/teams_new.html",
        **ctx
    )
