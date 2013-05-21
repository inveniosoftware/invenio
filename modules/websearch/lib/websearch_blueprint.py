# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012 CERN.
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

import os
import json
from math import ceil
from itertools import groupby
from flask import make_response, g, render_template, request, flash, jsonify, \
    redirect, url_for, current_app, abort

from invenio import bibindex_model as BibIndex
from invenio.config import CFG_PYLIBDIR, CFG_WEBSEARCH_SEARCH_CACHE_TIMEOUT, \
    CFG_SITE_LANG
from invenio.cache import cache
from invenio.errorlib import register_exception
from invenio.pluginutils import PluginContainer
from invenio.websearch_cache import search_results_cache, \
    get_search_query_id, get_search_results_cache_key_from_qid
from invenio.intbitset import intbitset as HitSet
from invenio.access_control_engine import acc_authorize_action
from invenio.access_control_config import VIEWRESTRCOLL
from invenio.sqlalchemyutils import db
from invenio.websearch_forms import EasySearchForm
from invenio.websearch_model import Collection, Format
from invenio.webinterface_handler_flask_utils import _, InvenioBlueprint, \
    register_template_context_processor
from invenio.webuser_flask import current_user

from invenio.bibindex_engine import get_index_id_from_index_name
from invenio.search_engine import get_creation_date, perform_request_search,\
    search_pattern, print_record, create_nearest_terms_box

blueprint = InvenioBlueprint('search', __name__, url_prefix="",
                             config='invenio.search_engine_config',
                             breadcrumbs=[],
                             menubuilder=[('main.search', _('Search'),
                                           'search.index', 1)])


def cached_format_record(recIDs, of, ln='', verbose=0,
                         search_pattern=None, xml_records=None, user_info=None,
                         record_prefix=None, record_separator=None,
                         record_suffix=None, prologue="", epilogue="",
                         req=None, on_the_fly=False):
    return print_record(recIDs, of, ln=ln, verbose=verbose,
                        brief_links=False)


@cache.memoize()
def get_export_formats():
    return Format.query.filter(db.and_(
        Format.content_type != 'text/html',
        Format.visibility == 1)
    ).order_by(Format.name).all()


@blueprint.route('/', methods=['GET', 'POST'])
@blueprint.invenio_templated('websearch_index.html')
def index():
    """ Renders homepage. """
    collection = Collection.query.get_or_404(1)
    # inject functions to the template

    @register_template_context_processor
    def index_context():
        return dict(
            easy_search_form=EasySearchForm(csrf_enabled=False),
            format_record=cached_format_record,
            get_creation_date=get_creation_date
        )
    return dict(collection=collection)


#@blueprint.invenio_memoize(3600)
def get_collection_breadcrumbs(collection, breadcrumbs=None, builder=None,
                               ln=CFG_SITE_LANG):
    if breadcrumbs is None:
        breadcrumbs = []
    if collection is not None:
        if collection.id == 1:
            return breadcrumbs
        breadcrumbs = get_collection_breadcrumbs(collection.most_specific_dad,
                                                 breadcrumbs, builder=builder)
        if builder is not None:
            crumb = builder(collection)
        else:
            crumb = (collection.name_ln,
                     'search.collection',
                     dict(name=collection.name))
        breadcrumbs.append(crumb)
    return breadcrumbs


@blueprint.route('/collection/<name>', methods=['GET', 'POST'])
@blueprint.invenio_templated('websearch_collection.html')
def collection(name):
    collection = Collection.query.filter(Collection.name == name).first_or_404()
    #FIXME cache per language
    b = get_collection_breadcrumbs(collection, [(_('Home'), '')], ln=g.ln)
    current_app.config['breadcrumbs_map'][request.endpoint] = b

    @register_template_context_processor
    def index_context():
        return dict(
            format_record=cached_format_record,
            easy_search_form=EasySearchForm(csrf_enabled=False),
            get_creation_date=get_creation_date)
    return dict(collection=collection)


class Pagination(object):

    def __init__(self, page, per_page, total_count):
        self.page = page
        self.per_page = per_page
        self.total_count = total_count

    @property
    def pages(self):
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    def iter_pages(self, left_edge=1, left_current=1,
                   right_current=3, right_edge=1):
        last = 0
        for num in xrange(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num


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


from invenio.search_engine_utils import get_fieldvalues
from invenio.bibrank_citation_searcher import get_cited_by_count
from invenio.webcommentadminlib import get_nb_reviews, get_nb_comments


class RecordInfo(object):

    def __init__(self, recid):
        self.recid = recid

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.recid)

    def get_nb_reviews(self, count_deleted=False):
        @cache.cached(key_prefix='record_info::get_nb_reviews::' +
                      str(self.recid) + '::' + str(count_deleted))
        def cached():
            return get_nb_reviews(self.recid, count_deleted)
        return cached()

    def get_nb_comments(self, count_deleted=False):
        @cache.cached(key_prefix='record_info::get_nb_comments::' + \
                      str(self.recid) + '::' + str(count_deleted))
        def cached():
            return get_nb_comments(self.recid, count_deleted)
        return cached()

    def get_cited_by_count(self):
        return get_cited_by_count(self.recid)

    def get_fieldvalues(self, fieldname):
        @cache.cached(key_prefix='record_info::get_fieldvalues::' + \
                      str(self.recid) + '::' + str(fieldname))
        def cached():
            return get_fieldvalues(self.recid, fieldname)
        return cached()


def _create_neareset_term_box(argd_orig):
    try:
        return create_nearest_terms_box(argd_orig,
            request.args.get('p', '').encode('ascii', 'ignore'),
            '', ln=g.ln).decode('utf8')
    except:
        return '<!-- not found -->'


from invenio.websearch_facet_builders import \
    get_current_user_records_that_can_be_displayed


def _invenio_facet_plugin_builder(plugin_name, plugin_code):
    """
    Handy function to bridge pluginutils with (Invenio) facets.
    """
    from invenio.websearch_facet_builders import FacetBuilder
    if 'facet' in dir(plugin_code):
        candidate = getattr(plugin_code, 'facet')
        if isinstance(candidate, FacetBuilder):
            return candidate
    raise ValueError('%s is not a valid facet plugin' % plugin_name)


@blueprint.before_app_first_request
def load_facet_builders():
    ## Let's load all facets.
    _FACETS = PluginContainer(
        os.path.join(CFG_PYLIBDIR, 'invenio', 'websearch_facets', 'facet_*.py'),
        plugin_builder=_invenio_facet_plugin_builder)

    FACET_DICTS = dict((f.name, f) for f in _FACETS.values())
    FACET_SORTED_LIST = sorted(FACET_DICTS.values(), key=lambda x: x.order)

    current_app.config['FACET_DICTS'] = FACET_DICTS
    current_app.config['FACET_SORTED_LIST'] = FACET_SORTED_LIST


@blueprint.route('/search', methods=['GET', 'POST'])
@blueprint.invenio_set_breadcrumb(_('Search results'))
@blueprint.invenio_templated('websearch_search.html')
def search():
    """
    Renders search pages.

    @FIXME: add parameter stream=True
    """

    uid = current_user.get_id()
    #url_args = SearchUrlargs(user=user, session=session, **request.args)

    name = request.args.get('cc')
    if name:
        collection = Collection.query.filter(Collection.name == name).first_or_404()
    else:
        collection = Collection.query.get_or_404(1)

    if collection.is_restricted:
        (auth_code, auth_msg) = acc_authorize_action(uid, VIEWRESTRCOLL,
                                                     collection=collection.name)
        if auth_code and current_user.is_guest:
            return redirect(url_for('webaccount.login',
                                    referer=request.url))
        elif auth_code:
            return abort(401)

    from invenio.websearch_webinterface import wash_search_urlargd
    argd = argd_orig = wash_search_urlargd(request.args)
    argd['of'] = 'id'

    #FIXME
    b = []

    def _crumb_builder(collection):
        qargs = request.args.to_dict()
        qargs['cc'] = collection.name
        return (collection.name_ln, 'search.search', qargs)

    if collection.id > 1:
        qargs = request.args.to_dict()
        qargs['cc'] = Collection.query.get_or_404(1).name
        b = get_collection_breadcrumbs(collection,
                                       [(_('Home'), 'search.search', qargs)],
                                       builder=_crumb_builder)
    current_app.config['breadcrumbs_map'][request.endpoint] = b

    rg = request.args.get('rg', 10, type=int)
    page = request.args.get('jrec', 1, type=int)
    qid = get_search_query_id(**argd)

    recids = perform_request_search(req=request, **argd)
    if (argd_orig.get('so') or argd_orig.get('rm')):
        recids.reverse()

    of = request.args.get('of', 'hb')
    #TODO deduplicate code used also in `export`
    if of.startswith('x'):
        rg = request.args.get('rg', len(recids), type=int)
        page = request.args.get('jrec', 1, type=int)
        pages = int(ceil(page / float(rg))) if rg > 0 else 1
        try:
            content_type = Format.query.filter(Format.code == of).one().content_type
        except:
            register_exception()
            content_type = 'text/xml'

        @register_template_context_processor
        def index_context():
            return dict(collection=collection,
                        RecordInfo=RecordInfo,
                        rg=rg,
                        pagination=Pagination(pages, rg, len(recids)))

        from invenio.bibformat import print_records
        response = make_response(print_records(recids, of=of, ln=g.ln))
        response.content_type = content_type
        return response

    FACET_SORTED_LIST = current_app.config.get('FACET_SORTED_LIST', [])
    facets = map(lambda x: x.get_conf(collection=collection, qid=qid),
                 FACET_SORTED_LIST)

    @register_template_context_processor
    def index_context():
        return dict(collection=collection,
                    facets=facets,
                    RecordInfo=RecordInfo,
                    create_nearest_terms_box=lambda: _create_neareset_term_box(argd_orig),
                    pagination=Pagination(int(ceil(page / float(rg))), rg, len(recids)),
                    rg=rg,
                    qid=qid,
                    easy_search_form=EasySearchForm(csrf_enabled=False),
                    format_record=cached_format_record,
                    #FIXME: move to DB layer
                    export_formats=get_export_formats())
    return dict(recids=recids)


@blueprint.route('/facet/<name>/<qid>', methods=['GET', 'POST'])
def facet(name, qid):
    """
    Creates list of fields specified facet.

    @param name: facet identifier
    @param qid: query identifier

    @return: jsonified facet list sorted by number of records
    """
    FACET_DICTS = current_app.config.get('FACET_DICTS', {})
    if name not in FACET_DICTS:
        abort(406)

    facet = FACET_DICTS[name]
    out = facet.get_facets_for_query(qid, limit=request.args.get('limit', 20))

    if request.is_xhr:
        return jsonify(facet=out)
    else:
        response = make_response('<html><body>%s</body></html>' % str(out))
        response.mimetype = 'text/html'
        return response


@blueprint.invenio_memoize(timeout=CFG_WEBSEARCH_SEARCH_CACHE_TIMEOUT / 2)
def get_value_recids(value, facet):
    p = '"' + str(value) + '"'
    return search_pattern(p=p, f=facet)


@blueprint.invenio_memoize(timeout=CFG_WEBSEARCH_SEARCH_CACHE_TIMEOUT / 4)
def get_facet_recids(facet, values):
    return reduce(lambda x, y: x.union(y),
                  [get_value_recids(v, facet) for v in values],
                  HitSet())


@blueprint.route('/results/<qid>', methods=['GET', 'POST'])
def results(qid):
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

    cc = search_results_cache.get(
        get_search_results_cache_key_from_qid(qid) + '::cc')

    try:
        filter = json.loads(request.values.get('filter', '[]'))
    except:
        return _('Invalid filter data')
    collection = Collection.query.filter(Collection.name == cc).first_or_404()

    sortkeytype = lambda v: v[0]
    sortfacet = lambda v: v[1]
    data = sorted(filter, key=sortkeytype)
    out = {}
    for t, vs in groupby(data, key=sortkeytype):
        out[t] = {}
        for v, k in groupby(sorted(vs, key=sortfacet), key=sortfacet):
            out[t][v] = map(lambda i: i[2], k)

    filter = out
    output = recIDsHitSet
    FACET_DICTS = current_app.config.get('FACET_DICTS', {})

    if '+' in filter:
        values = filter['+']
        for key, facet in FACET_DICTS.iteritems():
            if key in values:
                output.intersection_update(facet.get_facet_recids(values[key]))

    if '-' in filter:
        values = filter['-']
        for key, facet in FACET_DICTS.iteritems():
            if key in values:
                output.difference_update(facet.get_facet_recids(values[key]))

    #TODO sort
    if request.values.get('so'):
        recids = output.tolist()
        recids.reverse()
    elif request.values.get('rm'):
        from invenio.bibrank_record_sorter import rank_records
        ranked = rank_records(
                    request.values.get('rm'),
                    0, output, request.values.get('p', '').split())
        if ranked[0]:
            recids = ranked[0]
            recids.reverse()
        else:
            recids = output.tolist()
    else:
        recids = output.tolist()
        recids.reverse()

    rg = request.values.get('rg', 10, type=int)
    page = request.values.get('jrec', 1, type=int)

    @register_template_context_processor
    def index_context():
        return dict(
            collection=collection,
            RecordInfo=RecordInfo,
            create_nearest_terms_box=_create_neareset_term_box,
            pagination=Pagination(int(ceil(page / float(rg))), rg, len(recids)),
            rg=rg,
            format_record=cached_format_record)

    if len(recids):
        return render_template('websearch_results.html', recids=recids,
                               export_formats=get_export_formats())
    else:
        return _('Your search did not match any records. Please try again.')
    #return jsonify(recids = output.tolist())


@blueprint.route('/list/<field>', methods=['GET', 'POST'])
def autocomplete(field):
    """
    Autocompletes data from indexes.

    It uses POSTed arguments with name `q` that has to be longer than 3
    characters in order to returns any results.

    @param field: index name

    @return: list of values matching query.
    """

    #FIXME: possible vulnerability when guest users are quering index.

    if field not in [
            'exactauthor',
            'keyword',
            'affiliation',
            'reportnumber',
            'collaboration']:
        abort(406)

    q = request.args.get('q', '')
    if len(q) < 3:
        abort(406)

    IdxPHRASE = BibIndex.__getattribute__('IdxPHRASE%02dF' %
                                          get_index_id_from_index_name(field))

    results = IdxPHRASE.query.filter(IdxPHRASE.term.contains(q)).all()
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

    flash("Not implemented action " + action, 'error')
    return redirect(request.referrer)


@blueprint.route('/export', methods=['GET', 'POST'])
def export():
    """
    Exports requested records to defined output format.

    It uses following request values:
        * of (string): output format
        * recid ([int]): list of record IDs

    """
    of = request.values.get('of', 'xm')
    recids = request.values.getlist('recid', type=int)
    rg = request.args.get('rg', len(recids), type=int)
    page = request.args.get('jrec', 1, type=int)
    pages = int(ceil(page / float(rg))) if rg > 0 else 1
    try:
        content_type = Format.query.filter(Format.code == of).one().content_type
    except:
        register_exception()
        content_type = 'text/xml'

    name = request.args.get('cc')
    if name:
        collection = Collection.query.filter(Collection.name == name).\
            first_or_404()
    else:
        collection = Collection.query.get_or_404(1)

    @register_template_context_processor
    def index_context():
        return dict(
            collection=collection,
            RecordInfo=RecordInfo,
            rg=rg,
            pagination=Pagination(pages, rg, len(recids)))

    from invenio.bibformat import print_records
    response = make_response(print_records(recids, of=of, ln=g.ln))
    response.content_type = content_type
    return response
