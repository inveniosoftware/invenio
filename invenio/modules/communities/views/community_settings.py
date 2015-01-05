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

"""Community Settings Blueprint."""

from flask import Blueprint, render_template, \
    request, abort, flash, redirect, url_for, g
from flask.ext.breadcrumbs import register_breadcrumb
from flask.ext.login import current_user, login_required

from invenio.base.i18n import _
from invenio.ext.sqlalchemy import db
from invenio.ext.sslify import ssl_required
from invenio.ext.principal import permission_required

from .communities import mycommunities_ctx
from ..forms import EditCommunityForm, DeleteCommunityForm
from ..models import Community


blueprint = Blueprint(
    'community_settings', __name__,
    url_prefix="/account/settings/communities",
    template_folder='../templates',
    static_folder='../static'
)


@blueprint.route('/<string:community_id>/settings/', methods=['GET', 'POST'])
@ssl_required
@login_required
@permission_required('submit')
@register_breadcrumb(
    blueprint, 'breadcrumbs.settings.communities.settings', _('Settings'),
    dynamic_list_constructor=lambda:
        [{'text': request.view_args['community_id'].title()},
         {'text': _('Settings')}]
)
def edit(community_id):
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
        for field, val in form.data.items():
            setattr(u, field, val)
        db.session.commit()
        u.save_collections()
        flash("Community successfully edited.", category='success')
        return redirect(url_for('.edit', community_id=u.id))

    return render_template(
        "communities/new.html",
        **ctx
    )
