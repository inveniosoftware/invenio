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

"""
WebSearch Flask Blueprint.

Template hierarchy.
-------------------

- ``searchbar_frame_base.html``
    - ``searchbar_frame.html``
        - ``collection_base.html``
            - ``collection.html`` used by ``/collection/<collection>``
                - ``index_base.html``
                    - ``index.html`` used by ``/``
        - ``search_base.html``
            - ``search.html``
        - ``browse_base.html``
            - ``browse.html`` used by ``/browse``
    - ``results_base.html``
        - ``results.html``
- ``helpers_base.html`` macros
    - ``helpers.html``

"""

import cStringIO
import datetime
import time


from flask import (Blueprint, abort, current_app, flash, g, jsonify,
                   make_response, redirect, render_template, request, session,
                   url_for)
from flask_breadcrumbs import (current_breadcrumbs, default_breadcrumb_root,
                               register_breadcrumb)
from flask_login import current_user
from six import iteritems
from werkzeug.http import http_date
from werkzeug.local import LocalProxy

from invenio.base.globals import cfg
from invenio.base.decorators import templated, wash_arguments
from invenio.base.i18n import _
from invenio.ext.template.context_processor import \
    register_template_context_processor
from invenio.modules.collections.decorators import check_collection
from invenio.modules.formatter import (
    get_output_format_content_type, format_records
)
from invenio.modules.search.registry import facets
from invenio.utils.pagination import Pagination

from invenio_records.api import get_record

from ..api import Query
from ..cache import get_search_query_id
from ..forms import EasySearchForm
from ..washers import wash_search_urlargd

blueprint = Blueprint('search', __name__, url_prefix="",
                      template_folder='../templates',
                      static_url_path='',  # static url path has to be empty
                                           # if url_prefix is empty
                      static_folder='../static')

default_breadcrumb_root(blueprint, '.')


def _collection_of():
    """Get output format from user settings."""
    of = current_user['settings'].get('of')
    if of is not None and of != '':
        return of
    return g.collection.formatoptions[0]['code']

collection_of = LocalProxy(_collection_of)


def _default_rg():
    """Get number of records per page from user settings."""
    rg = cfg['CFG_WEBSEARCH_DEF_RECORDS_IN_GROUPS']
    if 'rg' not in request.values and current_user.get('rg'):
        rg = current_user.get('rg')
    return int(rg) or 1

default_rg = LocalProxy(_default_rg)


"""Collection output format."""


def min_length(length, code=406):
    """TODO."""
    def checker(value):
        if len(value) < 3:
            abort(code)
        return value
    return checker


def response_formated_records(records, collection, of, **kwargs):
    """Return formatter records.

    Response contains correct Cache and TTL information in HTTP headers.
    """
    response = make_response(format_records(records, collection=collection,
                                            of=of, **kwargs))

    response.mimetype = get_output_format_content_type(of)
    current_time = datetime.datetime.now()
    response.headers['Last-Modified'] = http_date(
        time.mktime(current_time.timetuple())
    )
    expires = current_app.config.get(
        'CFG_WEBSEARCH_SEARCH_CACHE_TIMEOUT', None)

    if expires is None:
        response.headers['Cache-Control'] = (
            'no-store, no-cache, must-revalidate, '
            'post-check=0, pre-check=0, max-age=0'
        )
        response.headers['Expires'] = '-1'
    else:
        expires_time = current_time + datetime.timedelta(seconds=expires)
        response.headers['Vary'] = 'Accept'
        response.headers['Cache-Control'] = (
            'public' if current_user.is_guest else 'private'
        )
        response.headers['Expires'] = http_date(time.mktime(
            expires_time.timetuple()
        ))
    return response


def crumb_builder(url):
    """TODO."""
    def _crumb_builder(collection):
        qargs = request.args.to_dict()
        qargs['cc'] = collection.name
        return dict(text=collection.name_ln, url=url_for(url, **qargs))
    return _crumb_builder


def collection_breadcrumbs(collection, endpoint=None):
    """TODO."""
    b = []
    if endpoint is None:
        endpoint = request.endpoint
    if collection.id > 1:
        qargs = request.values.to_dict()
        k = 'cc' if 'cc' in qargs else 'c'
        del qargs[k]
        b = [(_('Home'), endpoint, qargs)] + collection.breadcrumbs(
            builder=crumb_builder(endpoint), ln=g.ln)[1:]
    return b


@blueprint.route('/browse', methods=['GET', 'POST'])
@register_breadcrumb(blueprint, '.browse', _('Browse results'))
@wash_arguments({'p': (unicode, ''),
                 'f': (unicode, None),
                 'of': (unicode, 'hb'),
                 'so': (unicode, None),
                 'rm': (unicode, None),
                 'rg': (int, default_rg),
                 'jrec': (int, 1)})
@check_collection(default_collection=True)
def browse(collection, p, f, of, so, rm, rg, jrec):
    """Render browse page."""
    return 'Not supported.'


@blueprint.route('/rss', methods=['GET'])
# FIXME caching issue of response object
@wash_arguments({'p': (unicode, ''),
                 'jrec': (int, 1),
                 'so': (unicode, None),
                 'rm': (unicode, None),
                 'rg': (int, default_rg)})
@check_collection(default_collection=True)
def rss(collection, p, jrec, so, rm, rg):
    """Render RSS feed."""
    response = Query(p).search(collection=collection.name)
    response.body.update({
        'size': rg,
        'from': jrec-1,
    })

    return response_formated_records(
        response.records(), collection, 'xr',
        records=len(response),
        rg=rg,
    )


@blueprint.route('/search', methods=['GET', 'POST'])
@register_breadcrumb(blueprint, '.browse', _('Search results'))
@wash_arguments({'p': (unicode, ''),
                 'of': (unicode, collection_of),
                 'ot': (unicode, None),
                 'so': (unicode, None),
                 'sf': (unicode, None),
                 'sp': (unicode, None),
                 'rm': (unicode, None),
                 'rg': (int, default_rg),
                 'jrec': (int, 1)})
@check_collection(default_collection=True)
def search(collection, p, of, ot, so, sf, sp, rm, rg, jrec):
    """Render search page."""
    if 'action_browse' in request.args \
            or request.args.get('action', '') == 'browse':
        return browse()

    if 'c' in request.args and len(request.args) == 1 \
            and len(request.args.getlist('c')) == 1:
        return redirect(url_for('.collection', name=request.args.get('c')))

    if 'f' in request.args:
        args = request.args.copy()
        args['p'] = "{0}:{1}".format(args['f'], args['p'])
        del args['f']
        return redirect('.search', **args)

    # fix for queries like `/search?p=+ellis`
    p = p.strip().encode('utf-8')

    collection_breadcrumbs(collection)

    response = Query(p).search(collection=collection.name)
    response.body.update({
        'size': int(rg),
        'from': jrec-1,
        'aggs': {
            "Collections": {"terms": {"field": "_collections"}},
            "Authors": {"terms": {"field": "authors.raw"}},
        },
    })

    pagination = Pagination((jrec-1) // rg + 1, rg, len(response))

    ctx = dict(
        facets={},  # facets.get_facets_config(collection, qid),
        response=response,
        rg=rg,
        create_nearest_terms_box=lambda: _("Try to modify the query."),
        easy_search_form=EasySearchForm(csrf_enabled=False),
        ot=ot,
        pagination=pagination,
    )

    # TODO add search services
    # TODO add external collection search

    return response_formated_records(response.records(), collection, of, **ctx)


@blueprint.route('/facet/<name>/<qid>', methods=['GET', 'POST'])
def facet(name, qid):
    """
    Create list of fields specified facet.

    :param name: facet identifier
    :param qid: query identifier

    :return: jsonified facet list sorted by number of records
    """
    return jsonify(facet={})


@blueprint.route('/list/<any(exactauthor, keyword, affiliation, reportnumber, '
                 'collaboration):field>',
                 methods=['GET', 'POST'])
@wash_arguments({'q': (min_length(3), '')})
def autocomplete(field, q):
    """Autocomplete data from indexes.

    It uses POSTed arguments with name `q` that has to be longer than 3
    characters in order to returns any results.

    :param field: index name
    :param q: query string for index term

    :return: list of values matching query.
    """
    return jsonify(results={})


@blueprint.route('/search/dispatch', methods=['GET', 'POST'])
def dispatch():
    """Redirect request to appropriate methods from search page."""
    action = request.values.get('action')
    if action not in ['export']:
        abort(406)

    if action == 'export':
        return redirect(url_for('.export',
                                **request.values.to_dict(flat=False)))

    flash("Not implemented action " + action, 'error')
    return redirect(request.referrer)


@blueprint.route('/export', methods=['GET', 'POST'])
@wash_arguments({'of': (unicode, 'xm'), 'ot': (unicode, None)})
@check_collection(default_collection=True)
def export(collection, of, ot):
    """
    Export requested records to defined output format.

    It uses following request values:
        * of (string): output format
        * recid ([int]): list of record IDs

    """
    # Get list of integers with record IDs.
    recids = request.values.getlist('recid', type=int)
    return response_formated_records([get_record(recid) for recid in recids],
                                     collection, of, ot=ot)


@blueprint.route('/opensearchdescription')
def opensearchdescription():
    """Render OpenSearch description file."""
    response = make_response(render_template(
        'search/opensearchdescription.xml'))
    response.headers['Content-Type'] = 'application/opensearchdescription+xml'
    return response
