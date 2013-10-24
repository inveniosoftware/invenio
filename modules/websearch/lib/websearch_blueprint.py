# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012, 2013 CERN.
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

"""WebSearch Flask Blueprint"""

import json
import string
import functools
import cStringIO
from math import ceil
from flask import make_response, g, request, flash, jsonify, \
    redirect, url_for, current_app, abort, session

from invenio import bibindex_model as BibIndex
from invenio import websearch_receivers
from invenio.bibindex_engine import get_index_id_from_index_name
from invenio.bibformat import get_output_format_content_type, print_records
from invenio.cache import cache
from invenio.config import CFG_WEBSEARCH_RSS_TTL, \
    CFG_WEBSEARCH_PREV_NEXT_HIT_LIMIT
from invenio.websearch_cache import \
    get_search_query_id, get_collection_name_from_cache
from invenio.access_control_engine import acc_authorize_action
from invenio.access_control_config import VIEWRESTRCOLL
from invenio.intbitset import intbitset
from invenio.signalutils import websearch_before_browse, websearch_before_search
from invenio.websearch_forms import EasySearchForm
from invenio.websearch_model import Collection
from invenio.websearch_webinterface import wash_search_urlargd
from invenio.webinterface_handler_flask_utils import _, InvenioBlueprint, \
    register_template_context_processor
from invenio.webuser_flask import current_user
from invenio.websearch_facet_builders import \
    get_current_user_records_that_can_be_displayed, faceted_results_filter, \
    FacetLoader
from invenio.search_engine import get_creation_date, perform_request_search,\
    print_record, create_nearest_terms_box, browse_pattern_phrases
from invenio.paginationutils import Pagination
    
blueprint = InvenioBlueprint('search', __name__, url_prefix="",
                             config='invenio.search_engine_config',
                             breadcrumbs=[],
                             menubuilder=[('main.search', _('Search'),
                                           'search.index', 1)])


FACETS = FacetLoader()
def collection_name_from_request():
    collection = request.values.get('cc')
    if collection is None and len(request.values.getlist('c')) == 1:
        collection = request.values.get('c')
    return collection


def min_length(length, code=406):
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
            collection = Collection.query.filter(Collection.name == name).first_or_404()
        elif default_collection:
            collection = Collection.query.get_or_404(1)
        else:
            return abort(404)

        if collection.is_restricted:
            (auth_code, auth_msg) = acc_authorize_action(uid, VIEWRESTRCOLL,
                                                         collection=collection.name)
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
    response = make_response(print_records(recids, collection=collection,
                                           of=of, **kwargs))
    response.mimetype = get_output_format_content_type(of)
    return response


@blueprint.route('/index.py', methods=['GET', 'POST'])
@blueprint.route('/', methods=['GET', 'POST'])
@blueprint.invenio_templated('websearch_index.html')
def index():
    """ Renders homepage. """

    # legacy app support
    c = request.values.get('c')
    if c == current_app.config['CFG_SITE_NAME']:
        return redirect(url_for('.index', ln=g.ln))
    elif c is not None:
        return redirect(url_for('.collection', name=c, ln=g.ln))

    collection = Collection.query.get_or_404(1)
    # inject functions to the template

    @register_template_context_processor
    def index_context():
        return dict(
            easy_search_form=EasySearchForm(csrf_enabled=False),
            format_record=print_record,
            get_creation_date=get_creation_date
        )
    return dict(collection=collection)


@blueprint.route('/collection/<name>', methods=['GET', 'POST'])
@blueprint.invenio_templated('websearch_collection.html')
def collection(name):
    collection = Collection.query.filter(Collection.name == name).first_or_404()
    b = [(_('Home'), '.index')] + collection.breadcrumbs(ln=g.ln)[1:]
    current_app.config['breadcrumbs_map'][request.endpoint] = b

    @register_template_context_processor
    def index_context():
        return dict(
            format_record=print_record,
            easy_search_form=EasySearchForm(csrf_enabled=False),
            get_creation_date=get_creation_date)
    return dict(collection=collection)


class SearchUrlargs(object):

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
        self.session = session
        self.user = user
        self._url_args = kwargs

    @property
    def args(self):
        out = self.user_args
        out.update(self.url_args)
        return out

    @property
    def user_storable_args(self):
        return dict(map(lambda (k, v): (v['store'], k),
                    filter(lambda (k, v): v['store'],
                    self.DEFAULT_URLARGS.iteritems())))

    @property
    def url_args(self):
        return filter(lambda (k, v): k in self.DEFAULT_URLARGS.keys(),
                      self._url_args.iteritems())

    @property
    def user_args(self):
        if not self.user:
            return {}

        user_storable_args = self.user_storable_args
        args_keys = user_storable_args.keys()
        if self.user.settings is None:
            self.user.settings = dict()
        return dict(map(lambda (k, v): (user_storable_args[k], v),
                    filter(lambda (k, v): k in args_keys,
                    self.user.settings.iteritems())))


def _create_neareset_term_box(argd_orig):
    #try:
    p = argd_orig.pop('p', '')#.encode('utf-8')
    f = argd_orig.pop('f', '')#.encode('utf-8')
    if 'rg' in argd_orig and not 'rg' in request.values:
        del argd_orig['rg']
    if f == '' and ':' in p:
        fx, px = p.split(':', 1)
        from invenio.search_engine import get_field_name
        if get_field_name(fx) != "":
            f, p = fx, px

    return create_nearest_terms_box(argd_orig,
        p=p, f=f.lower(), ln=g.ln, intro_text_p=True)
    #except:
    #return '<!-- not found -->'


def sort_and_rank_records(recids, so=None, rm=None, p=''):
    output = recids.tolist()
    if so:
        output.reverse()
    elif rm:
        from invenio.bibrank_record_sorter import rank_records
        ranked = rank_records(rm, 0, output, p.split())
        if ranked[0]:
            output = ranked[0]
            output.reverse()
        else:
            output = output.tolist()
    else:
        output.reverse()
    return output


def crumb_builder(url):
    def _crumb_builder(collection):
        qargs = request.args.to_dict()
        qargs['cc'] = collection.name
        return (collection.name_ln, url, qargs)
    return _crumb_builder


def collection_breadcrumbs(collection, endpoint=None):
    b = []
    if endpoint is None:
        endpoint = request.endpoint
    if collection.id > 1:
        qargs = request.args.to_dict()
        k = 'cc' if 'cc' in qargs else 'c'
        del qargs[k]
        b = [(_('Home'), endpoint, qargs)] + collection.breadcrumbs(
            builder=crumb_builder(endpoint), ln=g.ln)[1:]
    current_app.config['breadcrumbs_map'][request.endpoint] = b


@blueprint.route('/browse', methods=['GET', 'POST'])
@blueprint.invenio_set_breadcrumb(_('Browse results'))
@blueprint.invenio_templated('websearch_browse.html')
@blueprint.invenio_wash_urlargd({'p': (unicode, ''),
                                 'f': (unicode, None),
                                 'of': (unicode, 'hb'),
                                 'so': (unicode, None),
                                 'rm': (unicode, None),
                                 'rg': (int, 10),
                                 'jrec': (int, 1)})
@check_collection(default_collection=True)
def browse(collection, p, f, of, so, rm, rg, jrec):

    from invenio.websearch_webinterface import wash_search_urlargd
    argd = argd_orig = wash_search_urlargd(request.args)

    collection_breadcrumbs(collection)

    colls = [collection.name] + request.args.getlist('c')
    if f is None and ':' in p[1:]:
        f, p = string.split(p, ":", 1)
        argd['f'] = f
        argd['p'] = p


    websearch_before_browse.send(collection, **argd)

    records = map(lambda (r, h): (r.decode('utf-8'), h),
                  browse_pattern_phrases(req=request.get_legacy_request(),
                                         colls=colls, p=p, f=f, rg=rg, ln=g.ln))

    @register_template_context_processor
    def index_context():
        return dict(collection=collection,
                    create_nearest_terms_box=lambda: _create_neareset_term_box(argd_orig),
                    pagination=Pagination(int(ceil(jrec / float(rg))), rg, len(records)),
                    rg=rg, p=p, f=f,
                    easy_search_form=EasySearchForm(csrf_enabled=False),
                    )

    return dict(records=records)

websearch_before_browse.connect(websearch_receivers.websearch_before_browse_handler)


@blueprint.route('/rss', methods=['GET'])
# FIXME caching issue of response object
#@cache.cached(timeout=CFG_WEBSEARCH_RSS_TTL)
@blueprint.invenio_wash_urlargd({'p': (unicode, ''),
                                 'jrec': (int, 1),
                                 'so': (unicode, None),
                                 'rm': (unicode, None)})
@check_collection(default_collection=True)
def rss(collection, p, jrec, so, rm):
    of = 'xr'
    argd = argd_orig = wash_search_urlargd(request.args)
    argd['of'] = 'id'

    # update search arguments with the search user preferences
    if 'rg' not in request.values and current_user.get('rg'):
        argd['rg'] = current_user.get('rg')
    rg = int(argd['rg'])

    qid = get_search_query_id(**argd)
    recids = perform_request_search(req=request.get_legacy_request(), **argd)

    if so or rm:
        recids.reverse()

    ctx = dict(records=len(get_current_user_records_that_can_be_displayed(qid)),
               qid=qid, rg=rg)

    return response_formated_records(recids, collection, of, **ctx)


@blueprint.route('/search', methods=['GET', 'POST'])
@blueprint.invenio_set_breadcrumb(_('Search results'))
@blueprint.invenio_wash_urlargd({'p': (unicode, ''),
                                 'of': (unicode, 'hb'),
                                 'so': (unicode, None),
                                 'rm': (unicode, None)})
@check_collection(default_collection=True)
def search(collection, p, of, so, rm):
    """
    Renders search pages.
    """

    if 'action_browse' in request.args \
            or request.args.get('action', '') == 'browse':
        return browse()

    if 'c' in request.args and len(request.args) == 1 \
            and len(request.args.getlist('c')) == 1:
        return redirect(url_for('.collection', name=request.args.get('c')))

    from invenio.websearch_webinterface import wash_search_urlargd
    argd = argd_orig = wash_search_urlargd(request.args)
    argd['of'] = 'id'

    # update search arguments with the search user preferences
    if 'rg' not in request.values and current_user.get('rg'):
        argd['rg'] = current_user.get('rg')
    rg = int(argd['rg'])

    collection_breadcrumbs(collection)

    qid = get_search_query_id(**argd)
    recids = perform_request_search(req=request.get_legacy_request(), **argd)

    #if so or rm:
    if len(of)>0 and of[0] == 'h':
        recids.reverse()

    # back-to-search related code
    if request and not isinstance(request.get_legacy_request(), cStringIO.OutputType):
        # store the last search results page
        session['websearch-last-query'] = request.get_legacy_request().unparsed_uri
        if len(recids) > CFG_WEBSEARCH_PREV_NEXT_HIT_LIMIT:
            last_query_hits = None
        else:
            last_query_hits = recids
        # store list of results if user wants to display hits
        # in a single list, or store list of collections of records
        # if user displays hits split by collections:
        session["websearch-last-query-hits"] = last_query_hits

    ctx = dict(facets=FACETS.config(collection=collection, qid=qid),
               records=len(get_current_user_records_that_can_be_displayed(qid)),
               qid=qid, rg=rg,
               create_nearest_terms_box=lambda: _create_neareset_term_box(argd_orig),
               easy_search_form=EasySearchForm(csrf_enabled=False))

    return response_formated_records(recids, collection, of, **ctx)


@blueprint.route('/facet/<name>/<qid>', methods=['GET', 'POST'])
def facet(name, qid):
    """
    Creates list of fields specified facet.

    @param name: facet identifier
    @param qid: query identifier

    @return: jsonified facet list sorted by number of records
    """
    try:
        out = FACETS[name].get_facets_for_query(
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
@blueprint.invenio_wash_urlargd({'p': (unicode, ''),
                                 'of': (unicode, 'hb'),
                                 'so': (unicode, None),
                                 'rm': (unicode, None)})
def results(qid, p, of, so, rm):
    """
    Generates results for cached query using POSTed filter.

    @param qid: query indentifier
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
        recids = faceted_results_filter(recIDsHitSet, filter_data, FACETS.elements)
        recids = sort_and_rank_records(recids, so=so, rm=rm, p=p)

        return response_formated_records(
            recids, collection, of,
            create_nearest_terms_box=_create_neareset_term_box, qid=qid)

    return make_results()


@blueprint.route('/list/<any(exactauthor, keyword, affiliation, reportnumber, collaboration):field>', methods=['GET', 'POST'])
@blueprint.invenio_wash_urlargd({'q': (min_length(3), '')})
def autocomplete(field, q):
    """
    Autocompletes data from indexes.

    It uses POSTed arguments with name `q` that has to be longer than 3
    characters in order to returns any results.

    @param field: index name
    @param q: query string for index term

    @return: list of values matching query.
    """

    IdxPHRASE = BibIndex.__getattribute__('IdxPHRASE%02dF' %
                                          get_index_id_from_index_name(field))

    results = IdxPHRASE.query.filter(IdxPHRASE.term.contains(q)).limit(20).all()
    results = map(lambda r: r.term, results)

    return jsonify(results=results)


@blueprint.route('/search/dispatch', methods=['GET', 'POST'])
def dispatch():
    """ Redirects request to appropriate methods from search page. """
    action = request.values.get('action')
    if action not in ['addtobasket', 'export']:
        abort(406)

    if action == 'export':
        return redirect(url_for('.export', **request.values.to_dict(flat=False)))

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
@blueprint.invenio_wash_urlargd({'of': (unicode, 'xm')})
@check_collection(default_collection=True)
def export(collection, of):
    """
    Exports requested records to defined output format.

    It uses following request values:
        * of (string): output format
        * recid ([int]): list of record IDs

    """
    # Get list of integers with record IDs.
    recids = request.values.getlist('recid', type=int)
    return response_formated_records(recids, collection, of)
