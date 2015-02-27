# -*- coding: utf-8 -*-
# This file is part of Invenio.
# Copyright (C) 2013, 2014 CERN.
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

"""Main Communities Blueprint."""

from __future__ import absolute_import

from flask import Blueprint, abort, jsonify, \
    render_template, request
from flask.ext.breadcrumbs import register_breadcrumb
from flask.ext.login import current_user, login_required
from flask.ext.menu import register_menu, current_menu

from invenio.base.decorators import wash_arguments
from invenio.base.globals import cfg
from invenio.base.i18n import _
from invenio.ext.cache import cache
from invenio.ext.principal import permission_required
from invenio.ext.sqlalchemy import db
from invenio.ext.sslify import ssl_required
from invenio.modules.formatter import format_record
from invenio.utils.pagination import Pagination

from ..models import Community, FeaturedCommunity
from ..signals import curate_record


blueprint = Blueprint(
    'communities', __name__,
    url_prefix="/communities",
    template_folder='../templates',
    static_folder='../static'
)


@blueprint.app_template_filter('community_id')
def community_id(coll):
    """Determine if current user is owner of a given record.

    :param coll: Collection object
    """
    if coll:
        identifier = coll.name
        if identifier.startswith(
                cfg['COMMUNITIES_ID_PREFIX_PROVISIONAL'] + "-"):
            return identifier[len(
                cfg['COMMUNITIES_ID_PREFIX_PROVISIONAL'] + "-"):]
        elif identifier.startswith(
                cfg['COMMUNITIES_ID_PREFIX'] + "-"):
            return identifier[len(cfg['COMMUNITIES_ID_PREFIX'] + "-"):]
    return ""


@blueprint.app_template_filter('curation_action')
def curation_action(recid, ucoll_id=None):
    """Determine if curation action is underway."""
    return cache.get("community_curate:%s_%s" % (ucoll_id, recid))


@blueprint.app_template_filter('communities')
def communities(bfo, is_owner=False, provisional=False, public=True,
                exclude=None):
    """Map collection identifiers to community collection objects.

    :param bfo: BibFormat Object
    :param is_owner: Set to true to only return user collections which the
                     current user owns.
    :param provisional: Return provisional collections (default to false)
    :param public: Return public collections (default to true)
    :param exclude: List of collection that should be excluded.
    """
    colls = []
    if is_owner and current_user.is_guest:
        return colls

    for cid in bfo.fields('980__a'):
        if exclude is not None and cid in exclude:
            continue
        if (
            provisional and cid.startswith(
                cfg['COMMUNITIES_ID_PREFIX_PROVISIONAL'] + "-")
        ):
            colls.append(
                cid[len(cfg['COMMUNITIES_ID_PREFIX_PROVISIONAL'] + "-"):])
        elif public and cid.startswith(cfg['COMMUNITIES_ID_PREFIX'] + "-"):
            colls.append(cid[len(cfg['COMMUNITIES_ID_PREFIX'] + "-"):])

    query = [Community.id.in_(colls)]
    if is_owner:
        query.append(Community.id_user == current_user.get_id())

    return Community.query.filter(*query).all()


@blueprint.app_template_filter('community_state')
def community_state(bfo, ucoll_id=None):
    """Determine if current user is owner of a given record.

    :param coll: Collection object
    """
    coll_id_reject = cfg['COMMUNITIES_ID_PREFIX_PROVISIONAL'] + \
        ("-%s" % ucoll_id)
    coll_id_accept = cfg['COMMUNITIES_ID_PREFIX'] + ("-%s" % ucoll_id)
    for cid in bfo.fields('980__a'):
        if cid == coll_id_accept:
            return "accepted"
        elif cid == coll_id_reject:
            return "provisional"
    return "rejected"


@blueprint.app_template_filter('mycommunities_ctx')
def mycommunities_ctx():
    """Helper method for return ctx used by many views."""
    return {
        'mycommunities': Community.query.filter_by(
            id_user=current_user.get_id()).order_by(
                db.asc(Community.title)).all()
    }


@blueprint.route('/', methods=['GET', ])
@register_breadcrumb(blueprint, '.', _('Communities'))
@register_menu(blueprint, 'main.communities', _('Communities'), order=2)
@wash_arguments({'p': (unicode, ''),
                 'so': (unicode, ''),
                 'page': (int, 1),
                 })
def index(p, so, page):
    """Index page with uploader and list of existing depositions."""
    ctx = mycommunities_ctx()

    if not so:
        so = cfg.get('COMMUNITIES_DEFAULT_SORTING_OPTION')

    communities = Community.filter_communities(p, so)
    featured_community = FeaturedCommunity.get_current()
    per_page = cfg.get('COMMUNITIES_DISPLAYED_PER_PAGE', 10)
    per_page = 10
    page = max(page, 1)
    p = Pagination(page, per_page, communities.count())

    ctx.update({
        'r_from': max(p.per_page*(p.page-1), 0),
        'r_to': min(p.per_page*p.page, p.total_count),
        'r_total': p.total_count,
        'pagination': p,
        'title': _('Community Collections'),
        'communities': communities.slice(
            per_page*(page-1), per_page*page).all(),
        'featured_community': featured_community,
        'format_record': format_record,
    })

    return render_template(
        "communities/index.html",
        **ctx
    )


@blueprint.route('/curate/', methods=['GET', 'POST'])
@ssl_required
@login_required
@permission_required('submit')
def curate():
    """Index page with uploader and list of existing depositions."""
    from invenio.legacy.search_engine import get_fieldvalues
    action = request.values.get('action')
    community_id = request.values.get('collection')
    recid = request.values.get('recid', 0, type=int)
    # Allowed actions
    if action not in ['accept', 'reject', 'remove']:
        abort(400)

    # Check recid
    if not recid:
        abort(400)
    recid = int(recid)

    # Does community exists
    u = Community.query.filter_by(id=community_id).first()
    if not u:
        abort(400)
    # Check permission to perform action on this record
    # - Accept and reject is done by community owner
    # - Remove  is done by record owner
    if action in ['accept', 'reject', ]:
        if u.id_user != current_user.get_id():
            abort(403)
    elif action == 'remove':
        try:
            email = get_fieldvalues(recid, '8560_f')[0]
            if email != current_user['email']:
                abort(403)
            # inform interested parties of removing collection/community
            curate_record.send(u, action=action, recid=recid, user=current_user)
        except (IndexError, KeyError):
            abort(403)

    # Prevent double requests (i.e. give bibupload a chance to make the change)
    key = "community_curate:%s_%s" % (community_id, recid)
    cache_action = cache.get(key)
    if cache_action == action or cache_action in ['reject', 'remove']:
        return jsonify({'status': 'success', 'cache': 1})
    elif cache_action:
        # Operation under way, but the same action
        return jsonify({'status': 'failure', 'cache': 1})

    if action == "accept":
        res = u.accept_record(recid)
    elif action == "reject" or action == "remove":
        res = u.reject_record(recid)
    if res:
        # Set 5 min cache to allow bibupload/webcoll to finish
        cache.set(key, action, timeout=5*60)
        return jsonify({'status': 'success', 'cache': 0})
    else:
        return jsonify({'status': 'failure', 'cache': 0})
