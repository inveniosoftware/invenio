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

from functools import wraps
from invenio import webinterface_handler_config as apache

from flask import g, render_template, request, flash, redirect, url_for, \
    current_app, abort
from invenio.config import CFG_SITE_RECORD, CFG_WEBLINKBACK_TRACKBACK_ENABLED
from invenio.access_control_config import VIEWRESTRCOLL
from invenio.access_control_mailcookie import \
    mail_cookie_create_authorize_action
from invenio.bibformat import format_record
from invenio.websearch_model import Collection
from invenio.websession_model import User
from invenio.bibedit_model import Bibrec
from invenio.webinterface_handler_flask_utils import _, InvenioBlueprint, \
    register_template_context_processor
from invenio.webuser_flask import current_user

from invenio.search_engine import guess_primary_collection_of_a_record, \
    check_user_can_view_record

from invenio.webcomment import get_mini_reviews
from invenio.websearchadminlib import get_detailed_page_tabs,\
                                      get_detailed_page_tabs_counts
from invenio.search_engine_utils import get_fieldvalues
from invenio.bibrank_downloads_similarity import register_page_view_event

blueprint = InvenioBlueprint('record', __name__, url_prefix="/"+CFG_SITE_RECORD,
                             config='invenio.search_engine_config',
                             breadcrumbs=[])
                             #menubuilder=[('main.search', _('Search'),
                             #              'search.index', 1)])


def request_record(f):
    @wraps(f)
    def decorated(recid, *args, **kwargs):
        # ensure recid to be integer
        recid = int(recid)
        g.collection = collection = Collection.query.filter(
            Collection.name == guess_primary_collection_of_a_record(recid)).\
            one()

        (auth_code, auth_msg) = check_user_can_view_record(current_user, recid)

        # only superadmins can use verbose parameter for obtaining debug information
        if not current_user.is_super_admin and 'verbose' in kwargs:
            kwargs['verbose'] = 0

        if auth_code and current_user.is_guest:
            cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {
                'collection': guess_primary_collection_of_a_record(recid)})
            url_args = {'action': cookie, 'ln': g.ln, 'referer': request.referrer}
            flash(_("Authorization failure"), 'error')
            return redirect(url_for('webaccount.login', **url_args))
        elif auth_code:
            flash(auth_msg, 'error')
            abort(apache.HTTP_UNAUTHORIZED)

        from invenio.search_engine import record_exists, get_merged_recid
        # check if the current record has been deleted
        # and has been merged, case in which the deleted record
        # will be redirect to the new one
        record_status = record_exists(recid)
        merged_recid = get_merged_recid(recid)
        if record_status == -1 and merged_recid:
            return redirect(url_for('record.metadata', recid=merged_recid))
        elif record_status == -1:
            abort(apache.HTTP_GONE)  # The record is gone!

        g.record = record = Bibrec.query.get(recid)
        user = None
        if not current_user.is_guest:
            user = User.query.get(current_user.get_id())
        title = get_fieldvalues(recid, '245__a')
        title = title[0] if len(title) > 0 else ''

        b = [(_('Home'), '')] + collection.breadcrumbs()[1:]
        b += [(title, 'record.metadata', dict(recid=recid))]
        current_app.config['breadcrumbs_map'][request.endpoint] = b
        g.record_tab_keys = []
        tabs = []
        counts = get_detailed_page_tabs_counts(recid)
        for k, v in get_detailed_page_tabs(collection.id, recid,
                                           g.ln).iteritems():
            t = {}
            b = 'record'
            if k == '':
                k = 'metadata'
            if k == 'comments' or k == 'reviews':
                b = 'webcomment'
            if k == 'linkbacks':
                b = 'weblinkback'
                k = 'index'

            t['key'] = b + '.' + k
            t['count'] = counts.get(k.capitalize(), -1)

            t.update(v)
            tabs.append(t)
            if v['visible']:
                g.record_tab_keys.append(b+'.'+k)

        if CFG_WEBLINKBACK_TRACKBACK_ENABLED:
            @register_template_context_processor
            def trackback_context():
                from invenio.weblinkback_templates import get_trackback_auto_discovery_tag
                return dict(headerLinkbackTrackbackLink=get_trackback_auto_discovery_tag(recid))

        @register_template_context_processor
        def record_context():
            return dict(recid=recid,
                        record=record,
                        user=user,
                        tabs=tabs,
                        title=title,
                        get_mini_reviews=lambda *args, **kwargs:
                        get_mini_reviews(*args, **kwargs).decode('utf8'),
                        collection=collection,
                        format_record=lambda recID, of='hb', ln=g.ln: format_record(
                            recID, of=of, ln=ln, verbose=0,
                            search_pattern='',
                            on_the_fly=False)
                        )
        return f(recid, *args, **kwargs)
    return decorated


@blueprint.route('/<int:recid>/metadata', methods=['GET', 'POST'])
@blueprint.route('/<int:recid>/', methods=['GET', 'POST'])
@blueprint.route('/<int:recid>', methods=['GET', 'POST'])
@request_record
def metadata(recid):
    register_page_view_event(recid, current_user.get_id(), str(request.remote_addr))
    return render_template('record_metadata.html')


@blueprint.route('/<int:recid>/references', methods=['GET', 'POST'])
@request_record
def references(recid):
    return render_template('record_references.html')


@blueprint.route('/<int:recid>/files', methods=['GET', 'POST'])
@request_record
def files(recid):
    return render_template('record_files.html')


from invenio.bibrank_citation_searcher import calculate_cited_by_list,\
                                              get_self_cited_by, \
                                              calculate_co_cited_with_list

@blueprint.route('/<int:recid>/citations', methods=['GET', 'POST'])
@request_record
def citations(recid):
    citations = dict(
        citinglist = calculate_cited_by_list(recid),
        selfcited = get_self_cited_by(recid),
        co_cited = calculate_co_cited_with_list(recid)
        )
    return render_template('record_citations.html',
                           citations = citations)


from invenio.bibclassify_webinterface import record_get_keywords

@blueprint.route('/<int:recid>/keywords', methods=['GET', 'POST'])
@request_record
def keywords(recid):
    found, keywords, record = record_get_keywords(recid)
    return render_template('record_keywords.html',
                           found = found,
                           keywords = keywords)


from invenio.bibrank_downloads_similarity import calculate_reading_similarity_list
from invenio.bibrank_downloads_grapher import create_download_history_graph_and_box

@blueprint.route('/<int:recid>/usage', methods=['GET', 'POST'])
@request_record
def usage(recid):
    viewsimilarity = calculate_reading_similarity_list(recid, "pageviews")
    downloadsimilarity = calculate_reading_similarity_list(recid, "downloads")
    downloadgraph = create_download_history_graph_and_box(recid)

    return render_template('record_usage.html',
                            viewsimilarity = viewsimilarity,
                            downloadsimilarity = downloadsimilarity,
                            downloadgraph = downloadgraph)
