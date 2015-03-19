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

import json
import string
import functools
import cStringIO
from math import ceil
from flask import make_response, g, request, flash, jsonify, \
    redirect, url_for, current_app, abort, session, Blueprint, \
    render_template
from flask_login import current_user
from six import iteritems
from werkzeug.local import LocalProxy

from .. import receivers
from ..cache import get_search_query_id, get_collection_name_from_cache
from ..facet_builders import get_current_user_records_that_can_be_displayed, \
    faceted_results_filter
from ..forms import EasySearchForm
from ..models import Collection
from ..washers import wash_search_urlargd
from flask_menu import register_menu
from invenio.base.signals import websearch_before_browse
from invenio.modules.indexer import models as BibIndex
from invenio.modules.formatter import format_record
from invenio.base.i18n import _
from invenio.base.decorators import wash_arguments, templated
from flask_breadcrumbs import \
    register_breadcrumb, current_breadcrumbs, default_breadcrumb_root
from invenio.ext.template.context_processor import \
    register_template_context_processor
from invenio.utils.pagination import Pagination
from invenio.utils.text import slugify
from invenio.modules.search.registry import facets

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


def collection_name_from_request():
    """TODO."""
    collection = request.values.get('cc')
    if collection is None and len(request.values.getlist('c')) == 1:
        collection = request.values.get('c')
    return collection


def min_length(length, code=406):
    """TODO."""
    def checker(value):
        if len(value) < 3:
            abort(code)
        return value
    return checker


def check_collection(method=None, name_getter=collection_name_from_request,
                     default_collection=False):
    """Check collection existence and authorization for current user."""
    if method is None:
        return functools.partial(check_collection, name_getter=name_getter,
                                 default_collection=default_collection)

    @functools.wraps(method)
    def decorated(*args, **kwargs):
        uid = current_user.get_id()
        name = name_getter()
        if name:
            g.collection = collection = Collection.query.filter(
                Collection.name == name).first_or_404()
        elif default_collection:
            g.collection = collection = Collection.query.get_or_404(1)
        else:
            return abort(404)

        if collection.is_restricted:
            from invenio.modules.access.engine import acc_authorize_action
            from invenio.modules.access.local_config import VIEWRESTRCOLL
            (auth_code, auth_msg) = acc_authorize_action(
                uid,
                VIEWRESTRCOLL,
                collection=collection.name
            )
            if auth_code:
                flash(_('This collection is restricted.'), 'error')
            if auth_code and current_user.is_guest:
                return redirect(url_for('webaccount.login',
                                        referer=request.url))
            elif auth_code:
                return abort(401)

        return method(collection, *args, **kwargs)
    return decorated


def response_formated_records(recids, collection, of, **kwargs):
    """TODO."""
    from invenio.modules.formatter import (get_output_format_content_type,
                                           print_records)
    response = make_response(print_records(recids, collection=collection,
                                           of=of, **kwargs))
    response.mimetype = get_output_format_content_type(of)
    return response


@blueprint.route('/index.html', methods=['GET', 'POST'])
@blueprint.route('/index.py', methods=['GET', 'POST'])
@blueprint.route('/', methods=['GET', 'POST'])
@templated('search/index.html')
@register_menu(blueprint, 'main.search', _('Search'), order=1)
@register_breadcrumb(blueprint, '.', _('Home'))
def index():
    """Render the homepage."""
    # legacy app support
    c = request.values.get('c')
    if c == current_app.config['CFG_SITE_NAME']:
        return redirect(url_for('.index', ln=g.ln))
    elif c is not None:
        return redirect(url_for('.collection', name=c, ln=g.ln))

    collection = Collection.query.get_or_404(1)

    @register_template_context_processor
    def index_context():
        return dict(
            of=request.values.get('of', collection.formatoptions[0]['code']),
            easy_search_form=EasySearchForm(csrf_enabled=False),
            format_record=format_record,
        )
    return dict(collection=collection)


@blueprint.route('/collection/', methods=['GET', 'POST'])
@blueprint.route('/collection/<name>', methods=['GET', 'POST'])
def collection(name=None):
    """Render the collection page.

    It renders it either with a collection specific template (aka
    collection_{collection_name}.html) or with the default collection
    template (collection.html)
    """
    if name is None:
        return redirect(url_for('.collection',
                                name=current_app.config['CFG_SITE_NAME']))
    collection = Collection.query.filter(Collection.name == name) \
                                 .first_or_404()

    @register_template_context_processor
    def index_context():
        breadcrumbs = current_breadcrumbs + collection.breadcrumbs(ln=g.ln)[1:]
        return dict(
            of=request.values.get('of', collection.formatoptions[0]['code']),
            format_record=format_record,
            easy_search_form=EasySearchForm(csrf_enabled=False),
            breadcrumbs=breadcrumbs)

    return render_template(['search/collection_{0}.html'.format(collection.id),
                            'search/collection_{0}.html'.format(slugify(name,
                                                                        '_')),
                            'search/collection.html'],
                           collection=collection)


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
            from invenio.legacy.search_engine import get_field_name
            if get_field_name(fx) != "":
                f, p = fx, px

        from invenio.legacy.search_engine import create_nearest_terms_box
        return create_nearest_terms_box(argd_orig,
                                        p=p,
                                        f=f.lower(),
                                        ln=g.ln,
                                        intro_text_p=True)
    except:  # FIXME catch all exception is bad
        return '<!-- not found -->'  # no comments


def sort_and_rank_records(recids, so=None, rm=None, sf=None, sp=None, p=''):
    """TODO."""
    from invenio.legacy.search_engine import sort_or_rank_records
    return sort_or_rank_records(
        request.get_legacy_request(), recids, rm, sf, so, sp, p
    )


def crumb_builder(url):
    """TODO."""
    def _crumb_builder(collection):
        qargs = request.args.to_dict()
        qargs['cc'] = collection.name
        #return (collection.name_ln, url, qargs)
        return dict(text=collection.name_ln, url=url_for(url, **qargs))
    return _crumb_builder


def collection_breadcrumbs(collection, endpoint=None):
    """TODO."""
    b = []
    if endpoint is None:
        endpoint = request.endpoint
    if collection.id > 1:
        qargs = request.args.to_dict()
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
    from invenio.legacy.search_engine import perform_request_search
    of = 'xr'
    argd = wash_search_urlargd(request.args)
    argd['of'] = 'id'

    # update search arguments with the search user preferences
    if 'rg' not in request.values and current_user.get('rg'):
        argd['rg'] = current_user.get('rg')
    rg = int(argd['rg'])

    qid = get_search_query_id(**argd)
    recids = perform_request_search(req=request.get_legacy_request(), **argd)

    ctx = dict(
        records=len(get_current_user_records_that_can_be_displayed(qid)),
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
                 'rm': (unicode, None)})
@check_collection(default_collection=True)
def search(collection, p, of, ot, so, rm):
    """Render search page."""
    from invenio.legacy.search_engine import perform_request_search

    if 'action_browse' in request.args \
            or request.args.get('action', '') == 'browse':
        return browse()

    if 'c' in request.args and len(request.args) == 1 \
            and len(request.args.getlist('c')) == 1:
        return redirect(url_for('.collection', name=request.args.get('c')))

    argd = argd_orig = wash_search_urlargd(request.args)
    argd['of'] = 'id'

    # fix for queries like `/search?p=+ellis`
    if 'p' in argd:
        argd['p'] = argd['p'].strip()

    # update search arguments with the search user preferences
    if 'rg' not in request.values and current_user.get('rg'):
        argd['rg'] = int(current_user.get('rg'))
    rg = int(argd['rg'])

    collection_breadcrumbs(collection)

    qid = get_search_query_id(**argd)
    recids = perform_request_search(req=request.get_legacy_request(), **argd)

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
        records=len(get_current_user_records_that_can_be_displayed(qid)),
        qid=qid, rg=rg,
        create_nearest_terms_box=lambda: _create_neareset_term_box(argd_orig),
        easy_search_form=EasySearchForm(csrf_enabled=False),
        ot=ot
    )

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


@blueprint.route('/results/<qid>', methods=['GET', 'POST'])
@wash_arguments({'p': (unicode, ''),
                 'of': (unicode, 'hb'),
                 'so': (unicode, None),
                 'sf': (unicode, None),
                 'sp': (unicode, None),
                 'rm': (unicode, None)})
def results(qid, p, of, so, sf, sp, rm):
    """
    Generate results for cached query using POSTed filter.

    :param qid: query indentifier
    """
    try:
        recIDsHitSet = get_current_user_records_that_can_be_displayed(qid)
    except KeyError:
        return 'KeyError'
    except:
        return _('Please reload the page')

    try:
        filter_data = json.loads(request.values.get('filter', '[]'))
    except:
        return _('Invalid filter data')

    @check_collection(
        name_getter=functools.partial(get_collection_name_from_cache, qid))
    def make_results(collection):
        recids = faceted_results_filter(recIDsHitSet,
                                        filter_data,
                                        facets)
        jrec = request.values.get('jrec', 1, type=int)
        rg = request.values.get('rg', 10, type=int)
        recids = sort_and_rank_records(recids, so=so, rm=rm, sf=sf,
                                       sp=sp, p=p)
        records = len(recids)

        if records > 0 and records < jrec:
            args = request.values.to_dict()
            args["jrec"] = 1
            return redirect(url_for(request.endpoint, qid=qid, **args))

        return response_formated_records(
            recids[jrec-1:jrec-1+rg], collection, of,
            create_nearest_terms_box=_create_neareset_term_box, qid=qid,
            records=records)

    return make_results()


@blueprint.route('/list/<any(exactauthor, keyword, affiliation, reportnumber, '
                 'collaboration):field>',
                 methods=['GET', 'POST'])
@wash_arguments({'q': (min_length(3), '')})
def autocomplete(field, q):
    """
    Autocomplete data from indexes.

    It uses POSTed arguments with name `q` that has to be longer than 3
    characters in order to returns any results.

    :param field: index name
    :param q: query string for index term

    :return: list of values matching query.
    """
    from invenio.legacy.bibindex.engine import get_index_id_from_index_name
    IdxPHRASE = BibIndex.__getattribute__('IdxPHRASE%02dF' %
                                          get_index_id_from_index_name(field))

    results = IdxPHRASE.query.filter(IdxPHRASE.term.contains(q))\
                             .limit(20).all()
    results = map(lambda r: {'value': r.term}, results)

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
