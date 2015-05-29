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
import string
import time

from math import ceil

from flask import (Blueprint, abort, current_app, flash, g, jsonify,
                   make_response, redirect, render_template, request, session,
                   url_for)
from flask_breadcrumbs import (current_breadcrumbs, default_breadcrumb_root,
                               register_breadcrumb)
from flask_login import current_user
from six import iteritems
from werkzeug.http import http_date
from werkzeug.local import LocalProxy

from invenio.base.decorators import templated, wash_arguments
from invenio.base.i18n import _
from invenio.base.signals import websearch_before_browse
from invenio.ext.template.context_processor import \
    register_template_context_processor
from invenio.modules.collections.decorators import check_collection
from invenio.modules.indexer.models import IdxINDEX
from invenio.modules.search.registry import facets
from invenio.utils.pagination import Pagination

from .. import receivers
from ..api import Query
from ..cache import get_search_query_id
from ..forms import EasySearchForm
from ..models import Field
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

"""Collection output format."""


def min_length(length, code=406):
    """TODO."""
    def checker(value):
        if len(value) < 3:
            abort(code)
        return value
    return checker


def response_formated_records(recids, collection, of, **kwargs):
    """Return formatter records.

    Response contains correct Cache and TTL information in HTTP headers.
    """
    from invenio.modules.formatter import (get_output_format_content_type,
                                           print_records)
    response = make_response(print_records(recids, collection=collection,
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


class SearchUrlargs(object):

    """TODO."""

    DEFAULT_URLARGS = {
        'p': {'title': 'Search', 'store': None},
        'cc': {'title': 'Collection', 'store': None},
        'c': {'title': 'Collection', 'store': None},
        'rg': {'title': 'Records in Groups',
               'store': 'websearch_group_records'},
        'sf': {'title': 'Sort Field', 'store': None},
        'so': {'title': 'Sort Option', 'store': 'websearch_sort_option'},
        'rm': {'title': 'Rank Method', 'store': 'websearch_rank_method'}
    }

    def __init__(self, session=None, user=None, **kwargs):
        """TODO."""
        self.session = session
        self.user = user
        self._url_args = kwargs

    @property
    def args(self):
        """TODO."""
        out = self.user_args
        out.update(self.url_args)
        return out

    @property
    def user_storable_args(self):
        """TODO."""
        return dict(map(lambda (k, v): (v['store'], k),
                    filter(lambda (k, v): v['store'],
                    iteritems(self.DEFAULT_URLARGS))))

    @property
    def url_args(self):
        """TODO."""
        return filter(lambda (k, v): k in self.DEFAULT_URLARGS.keys(),
                      iteritems(self._url_args))

    @property
    def user_args(self):
        """TODO."""
        if not self.user:
            return {}

        user_storable_args = self.user_storable_args
        args_keys = user_storable_args.keys()
        if self.user.settings is None:
            self.user.settings = dict()
        return dict(map(lambda (k, v): (user_storable_args[k], v),
                    filter(lambda (k, v): k in args_keys,
                    iteritems(self.user.settings))))


def _create_neareset_term_box(argd_orig):
    try:
        p = argd_orig.pop('p', '')
        f = argd_orig.pop('f', '')
        if 'rg' in argd_orig and 'rg' not in request.values:
            del argd_orig['rg']
        if f == '' and ':' in p:
            fx, px = p.split(':', 1)
            if Field.get_field_name(fx) is not None:
                f, p = fx, px

        from invenio.legacy.search_engine import create_nearest_terms_box
        return create_nearest_terms_box(argd_orig,
                                        p=p,
                                        f=f.lower(),
                                        ln=g.ln,
                                        intro_text_p=True)
    except:  # FIXME catch all exception is bad
        return '<!-- not found -->'  # no comments


def sort_and_rank_records(recids, so=None, rm=None, sf=None, sp=None, p='',
                          jrec=None, rg=None, of='id'):
    """TODO."""
    from invenio.legacy.search_engine import sort_or_rank_records
    return sort_or_rank_records(
        request.get_legacy_request(), recids, rm, sf, so, sp, p,
        jrec=jrec, rg=rg, of=of
    )


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
@templated('search/browse.html')
@wash_arguments({'p': (unicode, ''),
                 'f': (unicode, None),
                 'of': (unicode, 'hb'),
                 'so': (unicode, None),
                 'rm': (unicode, None),
                 'rg': (int, 10),
                 'jrec': (int, 1)})
@check_collection(default_collection=True)
def browse(collection, p, f, of, so, rm, rg, jrec):
    """Render browse page."""
    from invenio.legacy.search_engine import browse_pattern_phrases
    argd = argd_orig = wash_search_urlargd(request.args)

    colls = [collection.name] + request.args.getlist('c')
    if f is None and ':' in p[1:]:
        f, p = string.split(p, ":", 1)
        argd['f'] = f
        argd['p'] = p

    websearch_before_browse.send(collection, **argd)

    records = map(
        lambda (r, h): (r.decode('utf-8'), h),
        browse_pattern_phrases(req=request.get_legacy_request(),
                               colls=colls, p=p, f=f, rg=rg, ln=g.ln))

    @register_template_context_processor
    def index_context():
        box = lambda: _create_neareset_term_box(argd_orig)
        pagination = Pagination(int(ceil(jrec / float(rg))), rg, len(records))
        breadcrumbs = current_breadcrumbs + collection_breadcrumbs(collection)
        return dict(
            collection=collection,
            create_nearest_terms_box=box,
            pagination=pagination,
            rg=rg, p=p, f=f,
            easy_search_form=EasySearchForm(csrf_enabled=False),
            breadcrumbs=breadcrumbs
        )

    return dict(records=records)

websearch_before_browse.connect(receivers.websearch_before_browse_handler)


@blueprint.route('/rss', methods=['GET'])
# FIXME caching issue of response object
@wash_arguments({'p': (unicode, ''),
                 'jrec': (int, 1),
                 'so': (unicode, None),
                 'rm': (unicode, None)})
@check_collection(default_collection=True)
def rss(collection, p, jrec, so, rm):
    """Render RSS feed."""
    of = 'xr'
    argd = wash_search_urlargd(request.args)
    argd['of'] = 'id'

    # update search arguments with the search user preferences
    if 'rg' not in request.values and current_user.get('rg'):
        argd['rg'] = current_user.get('rg')
    rg = int(argd['rg'])

    qid = get_search_query_id(**argd)
    recids = Query(p).search(collection=collection.name)

    ctx = dict(
        records=len(recids),
        qid=qid,
        rg=rg
    )

    return response_formated_records(recids, collection, of, **ctx)


@blueprint.route('/search', methods=['GET', 'POST'])
@register_breadcrumb(blueprint, '.browse', _('Search results'))
@wash_arguments({'p': (unicode, ''),
                 'of': (unicode, collection_of),
                 'ot': (unicode, None),
                 'so': (unicode, None),
                 'sf': (unicode, None),
                 'sp': (unicode, None),
                 'rm': (unicode, None)})
@check_collection(default_collection=True)
def search(collection, p, of, ot, so, sf, sp, rm):
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

    argd = argd_orig = wash_search_urlargd(request.args)

    # fix for queries like `/search?p=+ellis`
    p = p.strip().encode('utf-8')
    jrec = request.values.get('jrec', 1, type=int)

    # update search arguments with the search user preferences
    if 'rg' not in request.values and current_user.get('rg'):
        argd['rg'] = int(current_user.get('rg'))
    rg = int(argd['rg'])

    collection_breadcrumbs(collection)

    qid = get_search_query_id(p=p, cc=collection.name)
    recids = Query(p).search(collection=collection.name)
    records = len(recids)
    recids = sort_and_rank_records(recids, so=so, rm=rm, sf=sf,
                                   sp=sp, p=p, of='id', rg=rg, jrec=jrec)

    # back-to-search related code
    if request and not isinstance(request.get_legacy_request(),
                                  cStringIO.OutputType):
        # store the last search results page
        session['websearch-last-query'] = request.get_legacy_request() \
                                                 .unparsed_uri
        hit_limit = current_app.config['CFG_WEBSEARCH_PREV_NEXT_HIT_LIMIT']
        if len(recids) > hit_limit:
            last_query_hits = None
        else:
            last_query_hits = recids
        # store list of results if user wants to display hits
        # in a single list, or store list of collections of records
        # if user displays hits split by collections:
        session["websearch-last-query-hits"] = last_query_hits

    ctx = dict(
        facets=facets.get_facets_config(collection, qid),
        records=records,
        rg=rg,
        create_nearest_terms_box=lambda: _create_neareset_term_box(argd_orig),
        easy_search_form=EasySearchForm(csrf_enabled=False),
        ot=ot
    )

    # TODO add search services
    # # WebSearch services
    # from invenio.modules.search import services
    # if jrec <= 1 and \
    #        (em == "" and True or (EM_REPOSITORY["search_services"] in em)):
    #     user_info = collect_user_info(req)
    #     # display only on first search page, and only if wanted
    #     # when 'em' param set.
    #     for answer_relevance, answer_html in services.get_answers(
    #             req, user_info, of, cc, colls_to_search, p, f, ln):
    #         req.write('<div class="searchservicebox">')
    #         req.write(answer_html)
    #         if verbose > 8:
    #             write_warning("Service relevance: %i" %
    #                           answer_relevance, req=req)
    #         req.write('</div>')

    # TODO add external collection search
    # if not of in ['hcs', 'hcs2']:
    #       perform_external_collection_search_with_em(
    #           req, cc, [p, p1, p2, p3], f, ec, verbose,
    #           ln, selected_external_collections_infos, em=em)

    return response_formated_records(recids, collection, of, **ctx)


@blueprint.route('/facet/<name>/<qid>', methods=['GET', 'POST'])
def facet(name, qid):
    """
    Create list of fields specified facet.

    :param name: facet identifier
    :param qid: query identifier

    :return: jsonified facet list sorted by number of records
    """
    try:
        out = facets[name].get_facets_for_query(
            qid, limit=request.args.get('limit', 20))
    except KeyError:
        abort(406)

    if request.is_xhr:
        return jsonify(facet=out)
    else:
        response = make_response('<html><body>%s</body></html>' % str(out))
        response.mimetype = 'text/html'
        return response


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
    IdxPHRASE = IdxINDEX.idxPHRASEF(field, fallback=False)
    results = IdxPHRASE.query.filter(
        IdxPHRASE.term.contains(q)).limit(20).values('term')
    results = map(lambda r: {'value': r[0]}, results)

    return jsonify(results=results)


@blueprint.route('/search/dispatch', methods=['GET', 'POST'])
def dispatch():
    """Redirect request to appropriate methods from search page."""
    action = request.values.get('action')
    if action not in ['addtobasket', 'export']:
        abort(406)

    if action == 'export':
        return redirect(url_for('.export',
                                **request.values.to_dict(flat=False)))

    if action == 'addtobasket':
        recids = request.values.getlist('recid', type=int)
        lang = (request.values.get('ln') or 'en')
        new_url = '/yourbaskets/add?ln={ln}&'.format(ln=lang)
        new_url += '&'.join(['recid=' + str(r) for r in recids])
        return redirect(new_url)

        # ERROR: parser of GET arguments in 'next' does not parse lists
        # only the first element of a list is passed to webbasket.add
        # (however, this url works in 'master' with the same webbasket module)

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
    return response_formated_records(recids, collection, of, ot=ot)


@blueprint.route('/opensearchdescription')
def opensearchdescription():
    """Render OpenSearch description file."""
    response = make_response(render_template(
        'search/opensearchdescription.xml'))
    response.headers['Content-Type'] = 'application/opensearchdescription+xml'
    return response
