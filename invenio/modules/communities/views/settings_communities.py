# -*- coding: utf-8 -*-

## This file is part of Invenio.
## Copyright (C) 2013, 2014, 2015 CERN.
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

"""Settings Communities Blueprint."""

from flask import Blueprint, flash, redirect, render_template, request, \
    url_for, abort
from flask.ext.breadcrumbs import register_breadcrumb
from flask.ext.login import current_user, login_required
from flask.ext.menu import register_menu
from invenio.base.decorators import wash_arguments
from invenio.base.i18n import _
from invenio.ext.sqlalchemy import db
from invenio.ext.principal import permission_required
from invenio.ext.sslify import ssl_required
from ..forms import CommunityForm, DeleteCommunityForm, \
    EditCommunityForm
from ..models import Community


blueprint = Blueprint(
    'settings_communities', __name__,
    url_prefix="/account/settings/communities",
    template_folder='../templates',
    static_folder='../static'
)


# FIXME refactor, probably get rid of this
@blueprint.app_template_filter('mycommunities_ctx')
def mycommunities_ctx():
    """Helper method for return ctx used by many views."""
    return {
        'mycommunities': Community.query.filter_by(
            id_user=current_user.get_id()).order_by(
                db.asc(Community.title)).all()
    }


@blueprint.route("/", methods=['GET'])
@ssl_required
@login_required
@register_menu(
    blueprint, 'settings.communities',
    _('%(icon)s My Communities', icon='<i class="fa fa-users fa-fw"></i>'),
    order=12,  # FIXME which order to choose
    active_when=lambda: request.endpoint.startswith("settings_communities.")
)
@register_breadcrumb(
    blueprint, 'breadcrumbs.settings.communities', _('Communities')
)
@wash_arguments({
    'page': (int, 1),
    'per_page': (int, 5),
    'p': (unicode, '')
})
def index(page, per_page, p):
    """List user's communities."""
    # FIXME can check be done differently?
    if page <= 0:
        page = 1
    if per_page <= 0:
        per_page = 5

    # TODO use api / improve queries
    if p:
        communities = Community.query.filter(
            db.or_(
                Community.id.like("%" + p + "%"),
                Community.title.like("%" + p + "%"),
                Community.description.like("%" + p + "%"),
            )
        ).order_by(
            db.asc(Community.title)
        ).paginate(page, per_page, error_out=False)
    else:
        communities = Community.query.filter_by(
            id_user=current_user.get_id()).order_by(
                db.asc(Community.title)
            ).paginate(page, per_page, error_out=False)

    return render_template(
        "communities/settings.html",
        communities=communities,
        page=page,
        p=p,
    )


@blueprint.route('/new/', methods=['GET', 'POST'])
@ssl_required
@login_required
@permission_required('submit')  # FIXME what's that persmission?
@register_breadcrumb(
    blueprint, 'breadcrumbs.settings.communities.new', _('New')
)
def new():
    """Create or edit a community."""
    uid = current_user.get_id()
    form = CommunityForm(request.values, crsf_enabled=False)

    ctx = mycommunities_ctx()
    ctx.update({
        'form': form,
        'is_new': True,
        'community': None,
    })

    if request.method == 'POST' and form.validate():
        # Map form
        data = form.data
        data['id'] = data['identifier']
        del data['identifier']
        c = Community(id_user=uid, **data)
        db.session.add(c)
        db.session.commit()
        c.save_collections()
        flash(
            _("Community was successfully created."), category='success')
        return redirect(url_for('.index'))

    return render_template(
        "communities/new.html",
        **ctx
    )


@blueprint.route('/delete/<string:community_id>/', methods=['POST'])
@ssl_required
@login_required
@permission_required('submit')
@register_breadcrumb(blueprint, '.delete', _('Delete'))
def delete(community_id):
    """Delete a community."""
    # Check existence of community
    u = Community.query.filter_by(id=community_id).first_or_404()
    uid = current_user.get_id()

    # Check ownership
    if u.id_user != uid:
        abort(404)

    deleteform = DeleteCommunityForm(request.values)
    ctx = mycommunities_ctx()
    ctx.update({
        'deleteform': deleteform,
        'is_new': False,
        'community': u,
    })

    if request.method == 'POST' and deleteform.validate():
        u.delete_collections()
        db.session.delete(u)
        db.session.commit()
        flash("Community was successfully deleted.", category='success')
        return redirect(url_for('.index'))
    else:
        flash("Community could not be deleted.", category='warning')
        return redirect(url_for('.edit', community_id=u.id))
