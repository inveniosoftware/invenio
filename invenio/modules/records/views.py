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

from functools import wraps

from flask import g, render_template, request, flash, redirect, url_for, \
    current_app, abort, Blueprint
from flask.ext.login import current_user

from invenio.base.decorators import wash_arguments
from invenio.base.globals import cfg
from invenio.config import CFG_SITE_RECORD
from invenio.ext.template.context_processor import \
    register_template_context_processor
from invenio.modules.search.models import Collection
from invenio.modules.search.signals import record_viewed
from invenio.modules.records.models import Record as Bibrec
from invenio.base.i18n import _
from invenio.utils import apache
from flask.ext.breadcrumbs import default_breadcrumb_root

blueprint = Blueprint('record', __name__, url_prefix="/" + CFG_SITE_RECORD,
                      static_url_path='/record', template_folder='templates',
                      static_folder='static')

default_breadcrumb_root(blueprint, '.')


def request_record(f):
    @wraps(f)
    def decorated(recid, *args, **kwargs):
        from invenio.modules.access.mailcookie import \
            mail_cookie_create_authorize_action
        from invenio.modules.access.local_config import VIEWRESTRCOLL
        from invenio.legacy.search_engine import guess_primary_collection_of_a_record, \
            check_user_can_view_record
        from invenio.legacy.websearch.adminlib import get_detailed_page_tabs,\
            get_detailed_page_tabs_counts
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
                'collection': g.collection.name})
            url_args = {'action': cookie, 'ln': g.ln, 'referer': request.url}
            flash(_("Authorization failure"), 'error')
            return redirect(url_for('webaccount.login', **url_args))
        elif auth_code:
            flash(auth_msg, 'error')
            abort(apache.HTTP_UNAUTHORIZED)

        from invenio.modules.records.api import get_record
        from invenio.legacy.search_engine import record_exists, get_merged_recid
        # check if the current record has been deleted
        # and has been merged, case in which the deleted record
        # will be redirect to the new one
        record_status = record_exists(recid)
        merged_recid = get_merged_recid(recid)
        if record_status == -1 and merged_recid:
            return redirect(url_for('record.metadata', recid=merged_recid))
        elif record_status == -1:
            abort(apache.HTTP_GONE)  # The record is gone!

        g.bibrec = Bibrec.query.get(recid)
        record = get_record(recid)

        if record is None:
            return render_template('404.html')

        title = record.get('title.title', '')

        # b = [(_('Home'), '')] + collection.breadcrumbs()[1:]
        # b += [(title, 'record.metadata', dict(recid=recid))]
        # current_app.config['breadcrumbs_map'][request.endpoint] = b
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
                b = 'comments'
            if k == 'linkbacks':
                b = 'weblinkback'
                k = 'index'

            t['key'] = b + '.' + k
            t['count'] = counts.get(k.capitalize(), -1)

            t.update(v)
            tabs.append(t)
            if v['visible']:
                g.record_tab_keys.append(b+'.'+k)

        if cfg.get('CFG_WEBLINKBACK_TRACKBACK_ENABLED'):
            @register_template_context_processor
            def trackback_context():
                from invenio.legacy.weblinkback.templates import get_trackback_auto_discovery_tag
                return dict(headerLinkbackTrackbackLink=get_trackback_auto_discovery_tag(recid))

        def _format_record(recid, of='hd', user_info=current_user, *args, **kwargs):
            from invenio.legacy.search_engine import print_record
            return print_record(recid, format=of, user_info=user_info, *args, **kwargs)

        @register_template_context_processor
        def record_context():
            from invenio.modules.comments.api import get_mini_reviews
            return dict(recid=recid,
                        record=record,
                        tabs=tabs,
                        title=title,
                        get_mini_reviews=lambda *args, **kwargs:
                        get_mini_reviews(*args, **kwargs).decode('utf8'),
                        collection=collection,
                        format_record=_format_record
                        )
        return f(recid, *args, **kwargs)
    return decorated


@blueprint.route('/<int:recid>/metadata', methods=['GET', 'POST'])
@blueprint.route('/<int:recid>/', methods=['GET', 'POST'])
@blueprint.route('/<int:recid>', methods=['GET', 'POST'])
@wash_arguments({'of': (unicode, 'hd')})
@request_record
def metadata(recid, of='hd'):
    from invenio.legacy.bibrank.downloads_similarity import register_page_view_event
    from invenio.modules.formatter import get_output_format_content_type
    register_page_view_event(recid, current_user.get_id(), str(request.remote_addr))
    if get_output_format_content_type(of) != 'text/html':
        return redirect('/%s/%d/export/%s' % (CFG_SITE_RECORD, recid, of))

    # Send the signal 'document viewed'
    record_viewed.send(
        current_app._get_current_object(),
        recid=recid,
        id_user=current_user.get_id(),
        request=request)

    return render_template('records/metadata.html', of=of)


@blueprint.route('/<int:recid>/references', methods=['GET', 'POST'])
@request_record
def references(recid):
    return render_template('records/references.html')


@blueprint.route('/<int:recid>/files', methods=['GET', 'POST'])
@request_record
def files(recid):
    def get_files():
        from invenio.legacy.bibdocfile.api import BibRecDocs
        for bibdoc in BibRecDocs(recid).list_bibdocs():
            for file in bibdoc.list_all_files():
                yield file.get_url()

    return render_template('records/files.html', files=list(get_files()))


@blueprint.route('/<int:recid>/citations', methods=['GET', 'POST'])
@request_record
def citations(recid):
    from invenio.legacy.bibrank.citation_searcher import calculate_cited_by_list,\
        get_self_cited_by, calculate_co_cited_with_list
    citations = dict(
        citinglist=calculate_cited_by_list(recid),
        selfcited=get_self_cited_by(recid),
        co_cited=calculate_co_cited_with_list(recid)
        )
    return render_template('records/citations.html',
                           citations=citations)


@blueprint.route('/<int:recid>/keywords', methods=['GET', 'POST'])
@request_record
def keywords(recid):
    from invenio.legacy.bibclassify.webinterface import record_get_keywords
    found, keywords, record = record_get_keywords(recid)
    return render_template('records/keywords.html',
                           found=found,
                           keywords=keywords)


@blueprint.route('/<int:recid>/usage', methods=['GET', 'POST'])
@request_record
def usage(recid):
    from invenio.legacy.bibrank.downloads_similarity import calculate_reading_similarity_list
    from invenio.legacy.bibrank.downloads_grapher import create_download_history_graph_and_box
    viewsimilarity = calculate_reading_similarity_list(recid, "pageviews")
    downloadsimilarity = calculate_reading_similarity_list(recid, "downloads")
    downloadgraph = create_download_history_graph_and_box(recid)

    return render_template('records/usage.html',
                           viewsimilarity=viewsimilarity,
                           downloadsimilarity=downloadsimilarity,
                           downloadgraph=downloadgraph)


@blueprint.route('/', methods=['GET', 'POST'])
def no_recid():
    return redirect("/")
