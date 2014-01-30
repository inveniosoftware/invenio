# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011 CERN.
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

"""
WebAuthorProfile web interface logic and URL handler
"""

# pylint: disable=W0105
# pylint: disable=C0301
# pylint: disable=W0613

from sys import hexversion
from urllib import urlencode
from datetime import datetime, timedelta

from invenio import webinterface_handler_config
from invenio.bibauthorid_webauthorprofileinterface import is_valid_canonical_id, \
    is_valid_bibref, get_person_id_from_paper, get_person_id_from_canonical_id, \
    search_person_ids_by_name, get_papers_by_person_id, get_person_redirect_link, \
    author_has_papers, get_authors_by_name
from invenio.bibauthorid_webapi import history_log_visit

from invenio.webauthorprofile_corefunctions import get_pubs, get_person_names_dicts, \
    get_institute_pubs, get_pubs_per_year, get_coauthors, get_summarize_records, \
    get_total_downloads, get_kwtuples, get_fieldtuples, get_veryfy_my_pubs_list_link, \
    get_hepnames_data, get_self_pubs, get_collabtuples, get_internal_publications, \
    get_external_publications, expire_all_cache_for_person, get_person_oldest_date, \
    get_datasets

from invenio.webpage import page
from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory
from invenio.urlutils import redirect_to_url
from invenio.jsonutils import json_unicode_to_utf8
from invenio.bibauthorid_templates import WebProfileMenu, WebProfilePage
from invenio.bibauthorid_webinterface import WebInterfaceAuthorTicketHandling
import invenio.bibauthorid_webapi as webapi

import invenio.template
import cProfile, pstats, cStringIO

websearch_templates = invenio.template.load('websearch')
webauthorprofile_templates = invenio.template.load('webauthorprofile')
bibauthorid_template = invenio.template.load('bibauthorid')

from invenio.search_engine import page_end
JSON_OK = False

if hexversion < 0x2060000:
    try:
        import simplejson as json
        JSON_OK = True
    except ImportError:
        # Okay, no Ajax app will be possible, but continue anyway,
        # since this package is only recommended, not mandatory.
        JSON_OK = False
else:
    try:
        import json
        JSON_OK = True
    except ImportError:
        JSON_OK = False

from webauthorprofile_config import CFG_SITE_LANG, CFG_SITE_URL, \
    CFG_WEBAUTHORPROFILE_USE_BIBAUTHORID

RECOMPUTE_ALLOWED_DELAY = timedelta(minutes=30)


def wrap_json_req_profiler(func):

    def json_req_profiler(self, req, form):
        if "ajaxProfile" in form:
            profiler = cProfile.Profile()
            return_val = profiler.runcall(func, self, req, form)

            results = cStringIO.StringIO()
            stats = pstats.Stats(profiler, stream=results)
            stats.sort_stats('cumulative')
            stats.print_stats(100)

            json_data = json.loads(return_val)
            json_data.update({"profilerStats": "<pre style='overflow: scroll'>" + results.getvalue() + "</pre>"})
            return json.dumps(json_data)

        else:
            return func(self, req, form)

    return json_req_profiler

class WebAuthorPages(WebInterfaceDirectory):
    '''
    Handles webauthorpages /author/profile/
    '''
    _exports = ['',
                'create_authorpage_affiliations',
                'create_authorpage_authors_pubs',
                'create_authorpage_citations',
                'create_authorpage_coauthors',
                'create_authorpage_collaborations',
                'create_authorpage_combined_papers',
                'create_authorpage_fieldcodes',
                'create_authorpage_hepdata',
                'create_authorpage_keywords',
                'create_authorpage_name_variants',
                'create_authorpage_pubs',
                'create_authorpage_pubs_graph',
                'create_authorpage_pubs_list']


    def __init__(self, identifier=None):
        '''
        Constructor of the web interface.

        @param identifier: identifier of an author. Can be one of:
            - an author id: e.g. "14"
            - a canonical id: e.g. "J.R.Ellis.1"
            - a bibrefrec: e.g. "100:1442,155"
        @type identifier: str
        '''
        self.person_id = -1   # -1 is a non valid author identifier
        self.cid = None
        self.original_search_parameter = identifier

        if (not CFG_WEBAUTHORPROFILE_USE_BIBAUTHORID or
            identifier is None or
            not isinstance(identifier, str)):
            return

        # check if it's a canonical id: e.g. "J.R.Ellis.1"
        pid = int(get_person_id_from_canonical_id(identifier))
        if pid >= 0:
            self.person_id = pid
            self.cid = get_person_redirect_link(self.person_id)
            return

        # check if it's an author id: e.g. "14"
        try:
            pid = int(identifier)
            if author_has_papers(pid):
                self.person_id = pid
                cid = get_person_redirect_link(pid)
                # author may not have a canonical id
                if is_valid_canonical_id(cid):
                    self.cid = cid
                return
        except ValueError:
            pass

        # check if it's a bibrefrec: e.g. "100:1442,155"
        if is_valid_bibref(identifier):
            pid = int(get_person_id_from_paper(identifier))
            if pid >= 0:
                self.person_id = pid
                self.cid = get_person_redirect_link(self.person_id)
                return


    def _lookup(self, component, path):
        '''
        This handler parses dynamic URLs:
            - /author/profile/1332 shows the page of author with id: 1332
            - /author/profile/100:5522,1431 shows the page of the author
              identified by the bibrefrec: '100:5522,1431'
        '''
        if not component in self._exports:
            return WebAuthorPages(component), path

    def _is_profile_owner(self, pid):
        return self.person_id == int(pid)

    def _is_admin(self, pinfo):
        return pinfo['ulevel'] == 'admin'

    def __call__(self, req, form):
        '''
        Serves the main person page.
        Will use the object's person id to get a person's information.

        @param req: apache request object
        @type req: apache request object
        @param form: POST/GET variables of the request
        @type form: dict

        @return: a full page formatted in HTML
        @rtype: str
        '''
        if not CFG_WEBAUTHORPROFILE_USE_BIBAUTHORID:
            self.person_id = self.original_search_parameter
            return self.index(req, form)

        argd = wash_urlargd(form, {'ln': (str, CFG_SITE_LANG),
                                   'recid': (int, -1),
                                   'verbose': (int, 0)})

        ln = argd['ln']
        verbose = argd['verbose']
        url_args = dict()
        if ln != CFG_SITE_LANG:
            url_args['ln'] = ln
        if verbose:
            url_args['verbose'] = str(verbose)
        encoded = urlencode(url_args)
        if encoded:
            encoded = '?' + encoded

        if self.cid is not None and self.original_search_parameter != self.cid:
            return redirect_to_url(req, '%s/author/profile/%s%s' % (CFG_SITE_URL, self.cid, encoded))

        # author may have only author identifier and not a canonical id
        if self.person_id > -1:
            return self.index(req, form)

        recid = argd['recid']

        if recid > -1:
            possible_authors = get_authors_by_name(self.original_search_parameter,
                                                         limit_to_recid = recid)

            if len(possible_authors) == 1:
                self.person_id = possible_authors.pop()[0]
                self.cid = get_person_redirect_link(self.person_id)
                redirect_to_url(req, '%s/author/profile/%s%s' % (CFG_SITE_URL, self.cid, encoded))

        encoded = urlencode(url_args)
        if encoded:
            encoded = '&' + encoded

        return redirect_to_url(req, '%s/author/search?q=%s%s' %
                                    (CFG_SITE_URL, self.original_search_parameter, encoded))


    def index(self, req, form):
        '''
        Serve the main person page.
        Will use the object's person id to get a person's information.

        @param req: apache request object
        @type req: apache request object
        @param form: POST/GET variables of the request
        @type form: dict

        @return: a full page formatted in HTML
        @return: str
        '''

        webapi.session_bareinit(req)
        session = webapi.get_session(req)
        pinfo = session['personinfo']
        ulevel = pinfo['ulevel']

        argd = wash_urlargd(form, {'ln': (str, CFG_SITE_LANG),
                                   'recompute': (int, 0),
                                   'verbose': (int, 0)})

        ln = argd['ln']
        debug = "verbose" in argd and argd["verbose"] > 0

        # Create Page Markup and Menu
        cname = webapi.get_canonical_id_from_person_id(self.person_id)
        menu = WebProfileMenu(str(cname), "profile", ln, self._is_profile_owner(pinfo['pid']), self._is_admin(pinfo))

        profile_page = WebProfilePage("profile", webapi.get_longest_name_from_pid(self.person_id))
        profile_page.add_profile_menu(menu)

        gboxstatus = self.person_id
        gpid = self.person_id
        gNumOfWorkers = 3   # to do: read it from conf file
        gReqTimeout = 5000
        gPageTimeout = 120000

        profile_page.add_bootstrapped_data(json.dumps({
            "other": "var gBOX_STATUS = '%s';var gPID = '%s'; var gNumOfWorkers= '%s'; var gReqTimeout= '%s'; var gPageTimeout= '%s';" % (gboxstatus, gpid, gNumOfWorkers, gReqTimeout, gPageTimeout),
            "backbone": """
            (function(ticketbox) {
                var app = ticketbox.app;
                app.userops.set(%s);
                app.bodyModel.set({userLevel: "%s"});
            })(ticketbox);""" % (WebInterfaceAuthorTicketHandling.bootstrap_status(pinfo, "user"), ulevel)
        }))

        if debug:
            profile_page.add_debug_info(pinfo)

        verbose = argd['verbose']
        url_args = dict()
        if ln != CFG_SITE_LANG:
            url_args['ln'] = ln
        if verbose:
            url_args['verbose'] = str(verbose)
        encoded = urlencode(url_args)
        if encoded:
            encoded = '&' + encoded

        if CFG_WEBAUTHORPROFILE_USE_BIBAUTHORID:
            if self.person_id < 0:
                return redirect_to_url(req, '%s/author/search?q=%s%s' %
                                            (CFG_SITE_URL, self.original_search_parameter, encoded))
        else:
            self.person_id = self.original_search_parameter

        assert not form.has_key('jsondata'), "Content type should be only text/html."

        title_message = 'Author Publication Profile Page'
        expire_cache = False

        if argd['recompute'] and req.get_method() == 'POST':
            expire_cache = True

        content = self.create_authorpage_websearch(req, form, ln, expire_cache)
        history_log_visit(req, 'profile', pid = self.person_id)

        if isinstance(content, dict):
            meta = profile_page.get_head() + content['head']
            body = profile_page.get_wrapped_body(content['body'])
            return page(title=title_message,
                        metaheaderadd=meta.encode('utf-8'),
                        body=body.encode('utf-8'),
                        req=req,
                        language=ln,
                        show_title_p=False)
        else:
            return page(title=title_message,
                        metaheaderadd="",
                        body="Error, no content returned!".encode('utf-8'),
                        req=req,
                        language=ln,
                        show_title_p=False)

    @wrap_json_req_profiler
    def create_authorpage_name_variants(self, req, form):
        if form.has_key('jsondata'):
            json_response = {'boxes_info': {}}
            json_data = json.loads(str(form['jsondata']))
            json_data = json_unicode_to_utf8(json_data)
            if json_data.has_key('personId'):
                person_id = json_data['personId']

                namesdict, namesdictStatus = get_person_names_dicts(person_id)
                if not namesdict:
                    namesdict = dict()
                try:
                    db_names_dict = namesdict['db_names_dict']
                except (IndexError, KeyError):
                    db_names_dict = dict()

                person_link, person_linkStatus = get_veryfy_my_pubs_list_link(person_id)
                bibauthorid_data = {'is_baid': True, 'pid': person_id, 'cid': None}
                if person_link and person_linkStatus:
                    bibauthorid_data = {'is_baid': True, 'pid': person_id, 'cid': person_link}

                json_response['boxes_info'].update({'name_variants': {'status': namesdictStatus, 'html_content': webauthorprofile_templates.tmpl_author_name_variants_box(db_names_dict, bibauthorid_data, ln='en', add_box=False, loading=not db_names_dict)}})
                req.content_type = 'application/json'
                return json.dumps(json_response)

    @wrap_json_req_profiler
    def create_authorpage_combined_papers(self, req, form):
        if form.has_key('jsondata'):
            json_response = {'boxes_info': {}}
            json_data = json.loads(str(form['jsondata']))
            json_data = json_unicode_to_utf8(json_data)
            if json_data.has_key('personId'):
                person_id = json_data['personId']

                pubs, pubsStatus = get_pubs(person_id)
                if not pubs:
                    pubs = list()

                selfpubs, selfpubsStatus = get_self_pubs(person_id)
                if not selfpubs:
                    selfpubs = list()

                person_link, person_linkStatus = get_veryfy_my_pubs_list_link(person_id)
                bibauthorid_data = {'is_baid': True, 'pid': person_id, 'cid': None}
                if person_link and person_linkStatus:
                    bibauthorid_data = {'is_baid': True, 'pid': person_id, 'cid': person_link}

                totaldownloads, totaldownloadsStatus = get_total_downloads(person_id)
                if not totaldownloads:
                    totaldownloads = 0

                json_response['boxes_info'].update({'combined_papers': {'status': selfpubsStatus, 'html_content': webauthorprofile_templates.tmpl_papers_with_self_papers_box(pubs, selfpubs, bibauthorid_data, totaldownloads, ln='en', add_box=False, loading=not selfpubsStatus)}})
                req.content_type = 'application/json'
                return json.dumps(json_response)

    @wrap_json_req_profiler
    def create_authorpage_keywords(self, req, form):
        if form.has_key('jsondata'):
            json_response = {'boxes_info': {}}
            json_data = json.loads(str(form['jsondata']))
            json_data = json_unicode_to_utf8(json_data)
            if json_data.has_key('personId'):
                person_id = json_data['personId']

                kwtuples, kwtuplesStatus = get_kwtuples(person_id)
                if kwtuples:
                    pass
                    # kwtuples = kwtuples[0:MAX_KEYWORD_LIST]
                else:
                    kwtuples = list()

                person_link, person_linkStatus = get_veryfy_my_pubs_list_link(person_id)
                bibauthorid_data = {'is_baid': True, 'pid': person_id, 'cid': None}
                if person_link and person_linkStatus:
                    bibauthorid_data = {'is_baid': True, 'pid': person_id, 'cid': person_link}

                json_response['boxes_info'].update({'keywords': {'status': kwtuplesStatus, 'html_content': webauthorprofile_templates.tmpl_keyword_box(kwtuples, bibauthorid_data, ln='en', add_box=False, loading=not kwtuplesStatus)}})
                req.content_type = 'application/json'
                return json.dumps(json_response)

    @wrap_json_req_profiler
    def create_authorpage_fieldcodes(self, req, form):
        if form.has_key('jsondata'):
            json_response = {'boxes_info': {}}
            json_data = json.loads(str(form['jsondata']))
            json_data = json_unicode_to_utf8(json_data)
            if json_data.has_key('personId'):
                person_id = json_data['personId']

                fieldtuples, fieldtuplesStatus = get_fieldtuples(person_id)
                if fieldtuples:
                    pass
                    # fieldtuples = fieldtuples[0:MAX_FIELDCODE_LIST]
                else:
                    fieldtuples = list()

                person_link, person_linkStatus = get_veryfy_my_pubs_list_link(person_id)
                bibauthorid_data = {'is_baid': True, 'pid': person_id, 'cid': None}
                if person_link and person_linkStatus:
                    bibauthorid_data = {'is_baid': True, 'pid': person_id, 'cid': person_link}

                json_response['boxes_info'].update({'fieldcodes': {'status': fieldtuplesStatus, 'html_content': webauthorprofile_templates.tmpl_fieldcode_box(fieldtuples, bibauthorid_data, ln='en', add_box=False, loading=not fieldtuplesStatus)}})
                req.content_type = 'application/json'
                return json.dumps(json_response)

    @wrap_json_req_profiler
    def create_authorpage_affiliations(self, req, form):
        if form.has_key('jsondata'):
            json_response = {'boxes_info': {}}
            json_data = json.loads(str(form['jsondata']))
            json_data = json_unicode_to_utf8(json_data)
            if json_data.has_key('personId'):
                person_id = json_data['personId']

                author_aff_pubs, author_aff_pubsStatus = get_institute_pubs(person_id)
                if not author_aff_pubs:
                    author_aff_pubs = dict()

                json_response['boxes_info'].update({'affiliations': {'status': author_aff_pubsStatus, 'html_content': webauthorprofile_templates.tmpl_affiliations_box(author_aff_pubs, ln='en', add_box=False, loading=not author_aff_pubsStatus)}})
                req.content_type = 'application/json'
                return json.dumps(json_response)

    @wrap_json_req_profiler
    def create_authorpage_coauthors(self, req, form):
        if form.has_key('jsondata'):
            json_response = {'boxes_info': {}}
            json_data = json.loads(str(form['jsondata']))
            json_data = json_unicode_to_utf8(json_data)
            if json_data.has_key('personId'):
                person_id = json_data['personId']

                person_link, person_linkStatus = get_veryfy_my_pubs_list_link(person_id)
                bibauthorid_data = {'is_baid': True, 'pid': person_id, 'cid': None}
                if person_link and person_linkStatus:
                    bibauthorid_data = {'is_baid': True, 'pid': person_id, 'cid': person_link}

                coauthors, coauthorsStatus = get_coauthors(person_id)
                if not coauthors:
                    coauthors = dict()

                json_response['boxes_info'].update({'coauthors': {'status': coauthorsStatus, 'html_content': webauthorprofile_templates.tmpl_coauthor_box(bibauthorid_data, coauthors, ln='en', add_box=False, loading=not coauthorsStatus)}})
                req.content_type = 'application/json'
                return json.dumps(json_response)

    @wrap_json_req_profiler
    def create_authorpage_pubs(self, req, form):
        if form.has_key('jsondata'):
            json_response = {'boxes_info': {}}
            json_data = json.loads(str(form['jsondata']))
            json_data = json_unicode_to_utf8(json_data)
            if json_data.has_key('personId'):
                person_id = json_data['personId']

                pubs, pubsStatus = get_pubs(person_id)
                if not pubs:
                    pubs = list()

                person_link, person_linkStatus = get_veryfy_my_pubs_list_link(person_id)
                bibauthorid_data = {'is_baid': True, 'pid': person_id, 'cid': None}
                if person_link and person_linkStatus:
                    bibauthorid_data = {'is_baid': True, 'pid': person_id, 'cid': person_link}

                json_response['boxes_info'].update({'numpaperstitle': {'status': pubsStatus, 'html_content': webauthorprofile_templates.tmpl_numpaperstitle(bibauthorid_data, pubs)}})
                req.content_type = 'application/json'
                return json.dumps(json_response)

    @wrap_json_req_profiler
    def create_authorpage_authors_pubs(self, req, form):
        if form.has_key('jsondata'):
            json_response = {'boxes_info': {}}
            json_data = json.loads(str(form['jsondata']))
            json_data = json_unicode_to_utf8(json_data)
            if json_data.has_key('personId'):
                person_id = json_data['personId']

                namesdict, namesdictStatus = get_person_names_dicts(person_id)
                if not namesdict:
                    namesdict = dict()
                try:
                    authorname = namesdict['longest']
                except (IndexError, KeyError):
                    authorname = 'None'

                person_link, person_linkStatus = get_veryfy_my_pubs_list_link(person_id)
                bibauthorid_data = {'is_baid': True, 'pid': person_id, 'cid': person_link}
                if not person_link or not person_linkStatus:
                    bibauthorid_data = {'is_baid': True, 'pid': person_id, 'cid': None}
                    person_link = str(person_id)

                pubs, pubsStatus = get_pubs(person_id)
                if not pubs:
                    pubs = list()

                json_response['boxes_info'].update({'authornametitle': {'status': (namesdictStatus and namesdictStatus and pubsStatus), 'html_content': webauthorprofile_templates.tmpl_authornametitle(authorname, bibauthorid_data, pubs, person_link, ln='en', loading=not (namesdictStatus and namesdictStatus and pubsStatus))}})
                req.content_type = 'application/json'
                return json.dumps(json_response)

    @wrap_json_req_profiler
    def create_authorpage_citations(self, req, form):
        if form.has_key('jsondata'):
            json_response = {'boxes_info': {}}
            json_data = json.loads(str(form['jsondata']))
            json_data = json_unicode_to_utf8(json_data)
            if json_data.has_key('personId'):
                person_id = json_data['personId']

                summarize_records, summarize_recordsStatus = get_summarize_records(person_id)
                if not summarize_records:
                    summarize_records = 'None'

                pubs, pubsStatus = get_pubs(person_id)
                if not pubs:
                    pubs = list()

                json_response['boxes_info'].update({'citations': {'status': (summarize_recordsStatus and pubsStatus), 'html_content': webauthorprofile_templates.tmpl_citations_box(summarize_records, pubs, ln='en', add_box=False, loading=not (summarize_recordsStatus and pubsStatus))}})
                req.content_type = 'application/json'
                return json.dumps(json_response)

    @wrap_json_req_profiler
    def create_authorpage_pubs_graph(self, req, form):
        if form.has_key('jsondata'):
            json_response = {'boxes_info': {}}
            json_data = json.loads(str(form['jsondata']))
            json_data = json_unicode_to_utf8(json_data)
            if json_data.has_key('personId'):
                person_id = json_data['personId']

                pubs_per_year, pubs_per_yearStatus = get_pubs_per_year(person_id)
                if not pubs_per_year:
                    pubs_per_year = dict()

                json_response['boxes_info'].update({'pubs_graph': {'status': pubs_per_yearStatus, 'html_content': webauthorprofile_templates.tmpl_graph_box(pubs_per_year, ln='en', add_box=False, loading=not pubs_per_yearStatus)}})
                req.content_type = 'application/json'
                return json.dumps(json_response)

    @wrap_json_req_profiler
    def create_authorpage_hepdata(self, req, form):
        if form.has_key('jsondata'):
            json_response = {'boxes_info': {}}
            json_data = json.loads(str(form['jsondata']))
            json_data = json_unicode_to_utf8(json_data)
            if json_data.has_key('personId'):
                person_id = json_data['personId']

                hepdict, hepdictStatus = get_hepnames_data(person_id)

                json_response['boxes_info'].update({'hepdata': {'status': hepdictStatus, 'html_content': bibauthorid_template.tmpl_hepnames_box(hepdict, ln='en', add_box=False, loading=not hepdictStatus)}})
                req.content_type = 'application/json'
                return json.dumps(json_response)

    @wrap_json_req_profiler
    def create_authorpage_collaborations(self, req, form):
        if form.has_key('jsondata'):
            json_response = {'boxes_info': {}}
            json_data = json.loads(str(form['jsondata']))
            json_data = json_unicode_to_utf8(json_data)
            if json_data.has_key('personId'):
                person_id = json_data['personId']

                collab, collabStatus = get_collabtuples(person_id)

                person_link, person_linkStatus = get_veryfy_my_pubs_list_link(person_id)
                bibauthorid_data = {'is_baid': True, 'pid': person_id, 'cid': None}
                if person_link and person_linkStatus:
                    bibauthorid_data = {'is_baid': True, 'pid': person_id, 'cid': person_link}

                json_response['boxes_info'].update({'collaborations': {'status': collabStatus, 'html_content': webauthorprofile_templates.tmpl_collab_box(collab, bibauthorid_data, ln='en', add_box=False, loading=not collabStatus)}})
                req.content_type = 'application/json'
                return json.dumps(json_response)

    @wrap_json_req_profiler
    def create_authorpage_pubs_list(self, req, form):
        if form.has_key('jsondata'):
            json_response = {'boxes_info': {}}
            json_data = json.loads(str(form['jsondata']))
            json_data = json_unicode_to_utf8(json_data)
            if json_data.has_key('personId'):
                person_id = json_data['personId']

                internal_pubs, internal_pubsStatus = get_internal_publications(person_id)
                external_pubs, external_pubsStatus = get_external_publications(person_id)
                datasets_pubs, datasets_pubsStatus = get_datasets(person_id)

#                if not internal_pubs:
#                    internal_pubs = None
#                if not external_pubs:
#                    external_pubs = None
                # switched from 'orcid_info' to 'pubs_list'
                json_response['boxes_info'].update(
                             {'pubs_list': {'status': (internal_pubsStatus and external_pubsStatus and datasets_pubsStatus),
                             'html_content': webauthorprofile_templates.tmpl_pubs_list(internal_pubs,
                                             external_pubs, datasets_pubs, ln='en',
                              add_box=False, loading=not (internal_pubsStatus and external_pubsStatus))}})
                req.content_type = 'application/json'
                return json.dumps(json_response)


    def create_authorpage_websearch(self, req, form, ln='en', expire_cache=False):
        if CFG_WEBAUTHORPROFILE_USE_BIBAUTHORID:
            if self.person_id < 0:
                return ("Critical Error. Author identifier should never be smaller than 0!")

        assert not form.has_key('jsondata'), "Content type should be only text/html."

        oldest_cache_date = get_person_oldest_date(self.person_id)

        delay = datetime.now() - oldest_cache_date
        if delay > RECOMPUTE_ALLOWED_DELAY:
            recompute_allowed = True
            if expire_cache:
                expire_all_cache_for_person(self.person_id)
                return self.create_authorpage_websearch(req, form, ln, expire_cache=False)
        else:
            recompute_allowed = False

        gboxstatus = self.person_id
        gpid = self.person_id
        gNumOfWorkers = 3   # to do: read it from conf file
        gReqTimeout = 3000
        gPageTimeout = 12000

        head = '<script type="text/javascript">var gBOX_STATUS = "%s";var gPID = "%s"; var gNumOfWorkers= "%s"; var gReqTimeout= "%s"; var gPageTimeout= "%s";</script>' \
               % (gboxstatus, gpid, gNumOfWorkers, gReqTimeout, gPageTimeout)

        body = webauthorprofile_templates.tmpl_author_page(ln, self.cid, oldest_cache_date, recompute_allowed)

        return {'head': head, 'body': body}

