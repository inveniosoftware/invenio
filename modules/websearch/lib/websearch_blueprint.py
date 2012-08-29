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

import pprint
from string import rfind, strip
from datetime import datetime
from hashlib import md5

from flask import Blueprint, session, make_response, g, render_template, \
                  request, flash, jsonify, redirect, url_for, current_app,\
                  abort
from invenio.cache import cache
from invenio.intbitset import intbitset as HitSet
from invenio.access_control_engine import acc_authorize_action
from invenio.access_control_config import VIEWRESTRCOLL
from invenio.sqlalchemyutils import db
from invenio.websearch_model import Collection, CollectionCollection
from invenio.websession_model import User
from invenio.webinterface_handler_flask_utils import _, InvenioBlueprint
from invenio.webuser_flask import current_user

from invenio.bibformat import format_record
from invenio.search_engine import search_pattern_parenthesised,\
                                  get_creation_date,\
                                  perform_request_search,\
                                  search_pattern

from sqlalchemy.sql import operators

blueprint = InvenioBlueprint('search', __name__, url_prefix="",
                             config='invenio.search_engine_config',
                             breadcrumbs=[],
                             menubuilder=[('main.search', _('Search'),
                                           'search.index', 1)])

@blueprint.invenio_memoize(3600)
def cached_format_record(recIDs, of, ln='', verbose=0,
                         search_pattern=None, xml_records=None, user_info=None,
                         record_prefix=None, record_separator=None,
                         record_suffix=None, prologue="", epilogue="", req=None,
                         on_the_fly=False):
    return format_record(recIDs, of, ln=ln, verbose=verbose).decode('utf8')
    #,
    #                     search_pattern=search_pattern, xml_records=xml_records,
    #                     user_info=user_info,
    #                     record_prefix=record_prefix,
    #                     record_separator=record_separator,
    #                     record_suffix=record_suffix, prologue=prologue,
    #                     epilogue=epilogue, req=req,
    #                     on_the_fly=on_the_fly).decode('utf8')

@blueprint.route('/', methods=['GET', 'POST'])
#@blueprint.invenio_sorted(MsgMESSAGE)
#@blueprint.invenio_filtered(MsgMESSAGE, columns={
#                    'subject':operators.startswith_op,
#                    'user_from.nickname':operators.contains_op},
#                    form=FilterMsgMESSAGEForm)
@blueprint.invenio_templated('websearch_index.html')
def index(sort=False, filter=None):
    uid = current_user.get_id()
    collection = Collection.query.get_or_404(1)

    return dict(collection=collection,
        get_creation_date=get_creation_date,
        format_record=lambda *args, **kwargs: \
            format_record(*args, **kwargs).decode('utf8'))


@blueprint.invenio_memoize(3600)
def get_collection_breadcrumbs(collection, breadcrumbs=None):
    if breadcrumbs is None:
        breadcrumbs = []
    if collection is not None:
        if collection.id == 1:
            return breadcrumbs
        breadcrumbs = get_collection_breadcrumbs(
                            collection.most_specific_dad,
                            breadcrumbs)
        breadcrumbs.append((collection.name_ln, 'search.collection',
                           dict(name=collection.name)))
    return breadcrumbs


@blueprint.route('/collection/<name>', methods=['GET', 'POST'])
@blueprint.invenio_templated('websearch_index.html')
def collection(name):
    collection = Collection.query.filter(Collection.name==name).first_or_404()
    #FIXME cache per language
    b = get_collection_breadcrumbs(collection, [(_('Home'),'')])
    current_app.config['breadcrumbs_map'][request.endpoint] = b
    current_app.template_context_processors[None].append(lambda: dict(
                format_record=cached_format_record))
    return dict(collection=collection,
        get_creation_date=get_creation_date)


from math import ceil
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
               (num > self.page - left_current - 1 and \
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
        'rg': {'title': 'Records in Groups', 'store': 'websearch_group_records'},
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
        return dict(map(lambda (k,v): (v['store'], k),
                    filter(lambda (k,v): v['store'],
                    self.DEFAULT_URLARGS.iteritems())))

    @property
    def url_args(self):
        return filter(lambda (k,v): k in self.DEFAULT_URLARGS.keys(),
                      self._url_args.iteritems())

    @property
    def user_args(self):
        if not self.user:
            return {}

        user_storable_args = self.user_storable_args
        args_keys = user_storable_args.keys()
        if self.user.settings is None:
            self.user.settings = dict()
        return dict(map(lambda (k,v): (user_storable_args[k], v),
                    filter(lambda (k,v): k in args_keys,
                    self.user.settings.iteritems())))


from invenio.search_engine_utils import get_fieldvalues
from invenio.bibrank_citation_searcher import get_cited_by_count
from invenio.webcommentadminlib import get_nb_reviews, get_nb_comments

class RecordInfo(object):

    def __init__(self, recid):
        self.recid = recid

    def get_nb_reviews(self, count_deleted=False):
        return get_nb_reviews(self.recid, count_deleted)

    def get_nb_comments(self, count_deleted=False):
        return get_nb_comments(self.recid, count_deleted)

    def get_cited_by_count(self):
        return get_cited_by_count(self.recid)

    def get_fieldvalues(self, fieldname):
        return get_fieldvalues(self.recid, fieldname)


def _create_neareset_term_box():
    try:
        return create_nearest_terms_box(argd_orig,
            p.encode('ascii', 'ignore'),
            '', ln=g.ln).decode('utf8')
    except:
        return '<!-- not found -->'



@blueprint.route('/search', methods=['GET', 'POST'])
@blueprint.invenio_set_breadcrumb(_('Search results'))
@blueprint.invenio_templated('websearch_search.html') #, stream=True)
def search():

    uid = current_user.get_id()
    user = User.query.get(uid) if not current_user.is_guest() else None
    url_args = SearchUrlargs(user=user, session=session, **request.args)
    current_app.logger.info('URL'+str(url_args.args))

    name = request.args.get('cc')
    if name:
        collection = Collection.query.filter(Collection.name==name).first_or_404()
    else:
        collection = Collection.query.get_or_404(1)

    if collection.is_restricted:
        (auth_code, auth_msg) = acc_authorize_action(uid,
                                        VIEWRESTRCOLL,
                                        collection=collection.name)
        if auth_code and current_user.is_guest():
            return redirect(url_for('youraccount.login',
                                    referer=request.url))
        elif auth_code:
            return abort(401)

    from invenio.websearch_webinterface import wash_search_urlargd
    argd = argd_orig = wash_search_urlargd(request.args)
    argd['of'] = 'id'

    p = request.args.get('p')
    f = request.args.get('f')
    colls_to_search = request.args.get('cc')
    wl = request.args.get('wl')

    recids = perform_request_search(**argd)
    qid = md5(repr((p,f,colls_to_search, wl))).hexdigest()
    if 'facet' not in session:
        session['facet'] = {}

    if (request.args.get('so') or request.args.get('rm')):
        recids.reverse()

    cache.set('facet_'+qid, {
        'recids': HitSet(recids).fastdump(),
        'cc': collection.name
        }, timeout=60*5) # 5 minutes

    rg = request.args.get('rg', 10, type=int)
    page = request.args.get('jrec', 1, type=int)
    facets = [{'title': g._(f.capitalize()),
               'url': url_for('.facet', name=f, qid=qid),
               'facet': f}  for f in ['collection', 'collectionname', 'author', 'year']]

    current_app.template_context_processors[None].append(lambda: dict(
                collection = collection,
                facets = facets,
                RecordInfo = RecordInfo,
                create_nearest_terms_box = _create_neareset_term_box,
                pagination = Pagination(int(ceil(page/float(rg))), rg, len(recids)),
                rg = rg,
                qid = qid,
                format_record=cached_format_record))
    return dict(recids = recids)

from invenio.search_engine import get_field_tags, \
        get_most_popular_field_values, \
        create_nearest_terms_box

@blueprint.route('/facet/<name>/<qid>', methods=['GET', 'POST'])
def facet(name, qid):
    if name not in ['collectionname', 'collection', 'author', 'year']:
        return None

    data = cache.get('facet_'+qid)
    try:
        recIDsHitSet = HitSet().fastload(data['recids'])
        recIDs = recIDsHitSet.tolist()
    except KeyError:
        recIDs = []

    limit = 50

    if name == 'collectionname':
        collection = Collection.query.filter(Collection.name==data['cc']).first_or_404()
        facet = []
        for c in collection.collection_children:
            num_records = len(c.reclist.intersection(recIDsHitSet))
            if num_records:
                facet.append((c.name, num_records, c.name_ln))
        return jsonify(facet=sorted(facet, key=lambda x:x[1], reverse=True)[0:limit])

    facet=list(get_most_popular_field_values(
                            recIDs,
                            get_field_tags(name)))

    if name == 'collection':
        for i,f in enumerate(facet):
            c = Collection.query.filter(
                    Collection.dbquery.contains(f[0])).first()
            if name:
                facet[i] = f[0],f[1],c.name_ln

    return jsonify(facet=facet[0:limit])


@blueprint.invenio_memoize(60*5)
def get_value_recids(value, facet):
    p = '"'+str(value)+'"'
    return search_pattern(p=p, f=facet)

@blueprint.invenio_memoize(60)
def get_facet_recids(facet, values):
    return reduce(lambda x,y: x.union(y),
                  [get_value_recids(v, facet) for v in values],
                  HitSet())

import json
@blueprint.route('/results/<qid>', methods=['GET', 'POST'])
def results(qid):
    data = cache.get('facet_'+qid)
    if data is None:
        return _('Please reload the page')

    filter = json.loads(request.form.get('filter'))
    collection = Collection.query.filter(Collection.name==data['cc']).first_or_404()

    try:
       recIDsHitSet = HitSet().fastload(data['recids'])
    except KeyError:
        return ''


    output = recIDsHitSet

    if '+' in filter:
        values = filter['+']
        for facet in ['collection', 'author', 'year']:
            if facet in values:
                output.intersection_update(get_facet_recids(facet, values[facet]))

    if '+' in filter and 'collectionname' in filter['+'] and len(filter['+']['collectionname']):
        limitTo = reduce(lambda x,y: x.union(y),
            [c.reclist for c in Collection.query.filter(
                Collection.name.in_(filter['+']['collectionname'])
            )],
            HitSet())
        output.intersection_update(limitTo)


    if '-' in filter:
        values = filter['-']
        for facet in ['collection', 'author', 'year']:
            if facet in values:
                output.difference_update(get_facet_recids(facet, values[facet]))

    if '-' in filter and 'collectionname' in filter['-'] and len(filter['-']['collectionname']):
        exclude = reduce(lambda x,y: x.union(y),
            [c.reclist for c in Collection.query.filter(
                Collection.name.in_(filter['-']['collectionname'])
            )],
            HitSet())
        current_app.logger.info(output)
        current_app.logger.info(exclude)
        output.difference_update(exclude)

    #TODO sort
    if request.form.get('so'):
        recids = output.tolist()
    elif request.form.get('rm'):
        from invenio.bibrank_record_sorter import rank_records
        ranked = rank_records(
                    request.form.get('rm'),
                    0, output, request.form.get('p').split())
        if ranked[0]:
            recids = ranked[0]
            recids.reverse()
        else:
            recids = output.tolist()
    else:
        recids = output.tolist()

    rg = request.form.get('rg', 10, type=int)
    page = request.form.get('jrec', 1, type=int)
    current_app.template_context_processors[None].append(lambda: dict(
                collection = collection,
                RecordInfo = RecordInfo,
                create_nearest_terms_box = _create_neareset_term_box,
                pagination = Pagination(int(ceil(page/float(rg))), rg, len(recids)),
                rg = rg,
                format_record=cached_format_record))

    if len(recids):
        return render_template('websearch_results.html', recids=recids)
    else:
        return _('Your search did not match any records. Please try again.')
    #return jsonify(recids = output.tolist())


