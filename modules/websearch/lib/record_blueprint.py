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
from functools import wraps
from string import rfind, strip
from datetime import datetime
from hashlib import md5

from flask import Blueprint, session, make_response, g, render_template, \
                  request, flash, jsonify, redirect, url_for, current_app
from invenio.cache import cache
from invenio.config import CFG_SITE_RECORD
from invenio.intbitset import intbitset as HitSet
from invenio.webinterface_handler_flask_utils import unicodifier
from invenio.sqlalchemyutils import db
from invenio.websearch_model import Collection, CollectionCollection
from invenio.websession_model import User
from invenio.bibedit_model import Bibrec
from invenio.webcomment_model import CmtSUBSCRIPTION
from invenio.webinterface_handler_flask_utils import _, InvenioBlueprint, \
                                  register_template_context_processor
from invenio.webuser_flask import current_user

from invenio.search_engine import search_pattern_parenthesised,\
                                  get_creation_date,\
                                  perform_request_search,\
                                  search_pattern,\
                                  guess_primary_collection_of_a_record, \
                                  print_record

from sqlalchemy.sql import operators
from invenio.webcomment import get_mini_reviews
from invenio.websearchadminlib import get_detailed_page_tabs,\
                                      get_detailed_page_tabs_counts

from invenio.websearch_blueprint import get_collection_breadcrumbs, \
                                        cached_format_record
from invenio.search_engine_utils import get_fieldvalues

blueprint = InvenioBlueprint('record', __name__, url_prefix="/"+CFG_SITE_RECORD,
                             config='invenio.search_engine_config',
                             breadcrumbs=[])
                             #menubuilder=[('main.search', _('Search'),
                             #              'search.index', 1)])

def request_record(f):
    @wraps(f)
    def decorated(recid, *args, **kwargs):
        g.collection = collection = Collection.query.filter(
            Collection.name==guess_primary_collection_of_a_record(recid)).\
            one()

        Bibrec.user_comment_subscritions = db.relationship(
            CmtSUBSCRIPTION,
            primaryjoin=lambda: db.and_(
                CmtSUBSCRIPTION.id_bibrec==Bibrec.id,
                CmtSUBSCRIPTION.id_user==current_user.get_id()
            ),
            viewonly=True)

        g.record = record = Bibrec.query.get(recid)
        user = None
        if not current_user.is_guest:
            user = User.query.get(current_user.get_id())
        title = get_fieldvalues(recid, '245__a')
        title = title[0].decode('utf-8') if len(title) > 0 else ''

        b = get_collection_breadcrumbs(collection, [(_('Home'),'')])
        b += [(title, 'record.metadata', dict(recid=recid))]
        current_app.config['breadcrumbs_map'][request.endpoint] = b
        g.record_tab_keys = []
        tabs = []
        for k,v in get_detailed_page_tabs(collection.id, recid,
                                          g.ln).iteritems():
            b = 'record'
            if k == '':
                k = 'metadata'
            if k == 'comments' or k == 'reviews':
                b = 'webcomment'
            if k == 'linkbacks':
                b = 'weblinkback'
                k = 'index'

            t = {'key':b+'.'+k}
            t.update(v)
            tabs.append(unicodifier(t))
            if v['visible']:
                g.record_tab_keys.append(b+'.'+k)

        @register_template_context_processor
        def record_context():
            return dict(
                recid = recid,
                record = record,
                user = user,
                tabs = tabs,
                title = title,
                get_mini_reviews = lambda *args, **kwargs: get_mini_reviews(
                                          *args, **kwargs).decode('utf8'),
                collection = collection,
                format_record = cached_format_record
                )
        return f(recid, *args, **kwargs)
    return decorated

@blueprint.route('/<int:recid>/metadata', methods=['GET', 'POST'])
@blueprint.route('/<int:recid>/', methods=['GET', 'POST'])
@blueprint.route('/<int:recid>', methods=['GET', 'POST'])
@request_record
def metadata(recid):
    uid = current_user.get_id()
    return render_template('record_metadata.html')

@blueprint.route('/<int:recid>/references', methods=['GET', 'POST'])
@request_record
def references(recid):
    uid = current_user.get_id()
    return render_template('record_references.html')


@blueprint.route('/<int:recid>/files', methods=['GET', 'POST'])
@request_record
def files(recid):
    uid = current_user.get_id()
    return render_template('record_files.html')


from invenio.bibrank_citation_searcher import calculate_cited_by_list,\
                                              get_self_cited_by, \
                                              calculate_co_cited_with_list

@blueprint.route('/<int:recid>/citations', methods=['GET', 'POST'])
@request_record
def citations(recid):
    uid = current_user.get_id()
    citations = dict(
        citinglist = calculate_cited_by_list(recid),
        selfcited = get_self_cited_by(recid),
        co_cited = calculate_co_cited_with_list(recid)
        )
    return render_template('record_citations.html',
                           citations = citations)


from bibclassify_webinterface import record_get_keywords

@blueprint.route('/<int:recid>/keywords', methods=['GET', 'POST'])
@request_record
def keywords(recid):
    uid = current_user.get_id()
    found, keywords, record = record_get_keywords(recid)
    return render_template('record_keywords.html',
                           found = found,
                           keywords = keywords)


from invenio.bibrank_downloads_similarity import calculate_reading_similarity_list
from invenio.bibrank_downloads_grapher import create_download_history_graph_and_box

@blueprint.route('/<int:recid>/usage', methods=['GET', 'POST'])
@request_record
def usage(recid):
    uid = current_user.get_id()
    viewsimilarity = calculate_reading_similarity_list(recid, "pageviews")
    downloadsimilarity = calculate_reading_similarity_list(recid, "downloads")
    downloadgraph = create_download_history_graph_and_box(recid)

    return render_template('record_usage.html',
                            viewsimilarity = viewsimilarity,
                            downloadsimilarity = downloadsimilarity,
                            downloadgraph = downloadgraph)



