# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011, 2012 CERN.
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
""" Bibauthorid Web Interface Logic and URL handler. """

# pylint: disable=W0105
# pylint: disable=C0301
# pylint: disable=W0613

from cgi import escape

from pprint import pformat
from operator import itemgetter
import re

try:
    from invenio.jsonutils import json, json_unicode_to_utf8, CFG_JSON_AVAILABLE
except ImportError:
    CFG_JSON_AVAILABLE = False
    json = None

from invenio.bibauthorid_webapi import add_cname_to_hepname_record
from invenio.config import CFG_SITE_URL, CFG_BASE_URL
from invenio.bibauthorid_config import AID_ENABLED, PERSON_SEARCH_RESULTS_SHOW_PAPERS_PERSON_LIMIT, \
                            BIBAUTHORID_UI_SKIP_ARXIV_STUB_PAGE, VALID_EXPORT_FILTERS, PERSONS_PER_PAGE, \
                            MAX_NUM_SHOW_PAPERS

from invenio.config import CFG_SITE_LANG, CFG_SITE_URL, CFG_SITE_NAME, CFG_INSPIRE_SITE, CFG_SITE_SECURE_URL

from invenio.bibauthorid_name_utils import most_relevant_name
from invenio.webpage import page, pageheaderonly, pagefooteronly
from invenio.messages import gettext_set_language  # , wash_language
from invenio.template import load
from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory
from invenio.session import get_session
from invenio.urlutils import redirect_to_url, get_canonical_and_alternates_urls
from invenio.webuser import (getUid,
                             page_not_authorized,
                             collect_user_info,
                             set_user_preferences,
                             get_user_preferences,
                             email_valid_p,
                             emailUnique,
                             get_email_from_username,
                             get_uid_from_email,
                             isGuestUser)
from invenio.access_control_admin import acc_get_user_roles
from invenio.search_engine import perform_request_search
from invenio.search_engine_utils import get_fieldvalues
from invenio.bibauthorid_config import CREATE_NEW_PERSON
import invenio.webinterface_handler_config as apache
import invenio.webauthorprofile_interface as webauthorapi
import invenio.bibauthorid_webapi as webapi
from invenio.bibauthorid_general_utils import get_title_of_doi, get_title_of_arxiv_pubid, is_valid_orcid
from invenio.bibauthorid_backinterface import update_external_ids_of_authors, get_orcid_id_of_author, \
            get_validated_request_tickets_for_author, get_title_of_paper, get_claimed_papers_of_author
from invenio.bibauthorid_dbinterface import defaultdict, remove_arxiv_papers_of_author
from invenio.webauthorprofile_orcidutils import get_dois_from_orcid

from invenio.bibauthorid_webauthorprofileinterface import is_valid_canonical_id, get_person_id_from_canonical_id, \
    get_person_redirect_link, author_has_papers

from invenio.bibauthorid_templates import WebProfileMenu, WebProfilePage

# Imports related to hepnames update form
from invenio.bibedit_utils import get_bibrecord
from invenio.bibrecord import record_get_field_value, record_get_field_values, \
                              record_get_field_instances, field_get_subfield_values


TEMPLATE = load('bibauthorid')

class WebInterfaceBibAuthorIDClaimPages(WebInterfaceDirectory):
    '''
    Handles /author/claim pages and AJAX requests.

    Supplies the methods:
        /author/claim/<string>
        /author/claim/action
        /author/claim/claimstub
        /author/claim/export
        /author/claim/generate_autoclaim_data
        /author/claim/merge_profiles_ajax
        /author/claim/search_box_ajax
        /author/claim/tickets_admin

        /author/claim/search
    '''
    _exports = ['',
                'action',
                'claimstub',
                'export',
                'generate_autoclaim_data',
                'merge_profiles_ajax',
                'search_box_ajax',
                'tickets_admin'
                ]

    def _lookup(self, component, path):
        '''
        This handler parses dynamic URLs:
            - /author/profile/1332 shows the page of author with id: 1332
            - /author/profile/100:5522,1431 shows the page of the author
              identified by the bibrefrec: '100:5522,1431'
        '''
        if not component in self._exports:
            return WebInterfaceBibAuthorIDClaimPages(component), path

    def _is_profile_owner(self, pid):
        return self.person_id == int(pid)

    def _is_admin(self, pinfo):
        return pinfo['ulevel'] == 'admin'

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

        if identifier is None or not isinstance(identifier, str):
            return

        # check if it's a canonical id: e.g. "J.R.Ellis.1"
        pid = int(webapi.get_person_id_from_canonical_id(identifier))
        if pid >= 0:
            self.person_id = pid
            return

        # check if it's an author id: e.g. "14"
        try:
            pid = int(identifier)
            if webapi.author_has_papers(pid):
                self.person_id = pid
                return
        except ValueError:
            pass

        # check if it's a bibrefrec: e.g. "100:1442,155"
        if webapi.is_valid_bibref(identifier):
            pid = int(webapi.get_person_id_from_paper(identifier))
            if pid >= 0:
                self.person_id = pid
                return

    def __call__(self, req, form):
        '''
        Serve the main person page.
        Will use the object's person id to get a person's information.

        @param req: apache request object
        @type req: apache request object
        @param form: POST/GET variables of the request
        @type form: dict

        @return: a full page formatted in HTML
        @rtype: str
        '''
        webapi.session_bareinit(req)
        session = get_session(req)
        pinfo = session['personinfo']
        ulevel = pinfo['ulevel']

        argd = wash_urlargd(form, {'ln': (str, CFG_SITE_LANG),
                                   'open_claim': (str, None),
                                   'ticketid': (int, -1),
                                   'verbose': (int, 0)})

        debug = "verbose" in argd and argd["verbose"] > 0

        ln = argd['ln']
        req.argd = argd   # needed for perform_req_search

        if self.person_id < 0:
            return redirect_to_url(req, '%s/author/search' % (CFG_SITE_URL))

        no_access = self._page_access_permission_wall(req, [self.person_id])
        if no_access:
            return no_access

        pinfo['claim_in_process'] = True

        user_info = collect_user_info(req)
        user_info['precached_viewclaimlink'] = pinfo['claim_in_process']
        session.dirty = True

        if self.person_id != -1:
            pinfo['claimpaper_admin_last_viewed_pid'] = self.person_id

        rt_ticket_id = argd['ticketid']
        if rt_ticket_id != -1:
            pinfo["admin_requested_ticket_id"] = rt_ticket_id

        session.dirty = True

        ## Create menu and page using templates
        cname = webapi.get_canonical_id_from_person_id(self.person_id)
        menu = WebProfileMenu(str(cname), "claim", ln, self._is_profile_owner(pinfo['pid']), self._is_admin(pinfo))

        profile_page = WebProfilePage("claim", webapi.get_longest_name_from_pid(self.person_id))
        profile_page.add_profile_menu(menu)

        gboxstatus = self.person_id
        gpid = self.person_id
        gNumOfWorkers = 3   # to do: read it from conf file
        gReqTimeout = 3000
        gPageTimeout = 12000

        profile_page.add_bootstrapped_data(json.dumps({
            "other": "var gBOX_STATUS = '%s';var gPID = '%s'; var gNumOfWorkers= '%s'; var gReqTimeout= '%s'; var gPageTimeout= '%s';" % (gboxstatus, gpid, gNumOfWorkers, gReqTimeout, gPageTimeout),
            "backbone": """
            (function(ticketbox) {
                 var app = ticketbox.app;
                 app.userops.set(%s);
                 app.bodyModel.set({userLevel: "%s", guestPrompt: true});
            })(ticketbox);""" % (WebInterfaceAuthorTicketHandling.bootstrap_status(pinfo, "user"), ulevel)
        }))

        if debug:
            profile_page.add_debug_info(pinfo)

        # content += self._generate_person_info_box(ulevel, ln) #### Name variants
        # metaheaderadd = self._scripts() + '\n <meta name="robots" content="nofollow" />'
        # body = self._generate_optional_menu(ulevel, req, form)

        content = self._generate_tabs(ulevel, req)
        content += self._generate_footer(ulevel)
        content = content.decode('utf-8', 'strict')

        webapi.history_log_visit(req, 'claim', pid=self.person_id)
        return page(title=self._generate_title(ulevel),
                    metaheaderadd=profile_page.get_head().encode('utf-8'),
                    body=profile_page.get_wrapped_body(content).encode('utf-8'),
                    req=req,
                    language=ln,
                    show_title_p=False)


    def _page_access_permission_wall(self, req, req_pid=None, req_level=None):
        '''
        Display an error page if user not authorized to use the interface.

        @param req: Apache Request Object for session management
        @type req: Apache Request Object
        @param req_pid: Requested person id
        @type req_pid: int
        @param req_level: Request level required for the page
        @type req_level: string
        '''
        session = get_session(req)
        uid = getUid(req)
        pinfo = session["personinfo"]
        uinfo = collect_user_info(req)

        if 'ln' in pinfo:
            ln = pinfo["ln"]
        else:
            ln = CFG_SITE_LANG

        _ = gettext_set_language(ln)
        is_authorized = True
        pids_to_check = []

        if not AID_ENABLED:
            return page_not_authorized(req, text=_("Fatal: Author ID capabilities are disabled on this system."))

        if req_level and 'ulevel' in pinfo and pinfo["ulevel"] != req_level:
            return page_not_authorized(req, text=_("Fatal: You are not allowed to access this functionality."))

        if req_pid and not isinstance(req_pid, list):
            pids_to_check = [req_pid]
        elif req_pid and isinstance(req_pid, list):
            pids_to_check = req_pid

        if (not (uinfo['precached_usepaperclaim']
                  or uinfo['precached_usepaperattribution'])
            and 'ulevel' in pinfo
            and not pinfo["ulevel"] == "admin"):
            is_authorized = False

        if is_authorized and not webapi.user_can_view_CMP(uid):
            is_authorized = False
        if is_authorized and 'ticket' in pinfo:
            for tic in pinfo["ticket"]:
                if 'pid' in tic:
                    pids_to_check.append(tic['pid'])

        if pids_to_check and is_authorized:
            user_pid = webapi.get_pid_from_uid(uid)

            if not uinfo['precached_usepaperattribution']:
                if (not user_pid in pids_to_check
                    and 'ulevel' in pinfo
                    and not pinfo["ulevel"] == "admin"):
                    is_authorized = False

            elif (user_pid in pids_to_check
                  and 'ulevel' in pinfo
                  and not pinfo["ulevel"] == "admin"):
                for tic in list(pinfo["ticket"]):
                    if not tic["pid"] == user_pid:
                        pinfo['ticket'].remove(tic)

        if not is_authorized:
            return page_not_authorized(req, text=_("Fatal: You are not allowed to access this functionality."))
        else:
            return ""

    def _generate_title(self, ulevel):
        '''
        Generates the title for the specified user permission level.

        @param ulevel: user permission level
        @type ulevel: str

        @return: title
        @rtype: str
        '''
        def generate_title_guest():
            title = 'Assign papers'
            if self.person_id:
                title = 'Assign papers for: ' + str(webapi.get_person_redirect_link(self.person_id))
            return title

        def generate_title_user():
            title = 'Assign papers'
            if self.person_id:
                title = 'Assign papers (user interface) for: ' + str(webapi.get_person_redirect_link(self.person_id))
            return title

        def generate_title_admin():
            title = 'Assign papers'
            if self.person_id:
                title = 'Assign papers (administrator interface) for: ' + str(webapi.get_person_redirect_link(self.person_id))
            return title


        generate_title = {'guest': generate_title_guest,
                          'user': generate_title_user,
                          'admin': generate_title_admin}

        return generate_title[ulevel]()


    def _generate_optional_menu(self, ulevel, req, form):
        '''
        Generates the menu for the specified user permission level.

        @param ulevel: user permission level
        @type ulevel: str
        @param req: apache request object
        @type req: apache request object
        @param form: POST/GET variables of the request
        @type form: dict

        @return: menu
        @rtype: str
        '''
        def generate_optional_menu_guest(req, form):
            argd = wash_urlargd(form, {'ln': (str, CFG_SITE_LANG),
                                       'verbose': (int, 0)})
            menu = TEMPLATE.tmpl_person_menu(self.person_id, argd['ln'])

            if "verbose" in argd and argd["verbose"] > 0:
                session = get_session(req)
                pinfo = session['personinfo']
                menu += "\n<pre>" + pformat(pinfo) + "</pre>\n"

            return menu

        def generate_optional_menu_user(req, form):
            argd = wash_urlargd(form, {'ln': (str, CFG_SITE_LANG),
                                       'verbose': (int, 0)})
            menu = TEMPLATE.tmpl_person_menu(self.person_id, argd['ln'])

            if "verbose" in argd and argd["verbose"] > 0:
                session = get_session(req)
                pinfo = session['personinfo']
                menu += "\n<pre>" + pformat(pinfo) + "</pre>\n"

            return menu

        def generate_optional_menu_admin(req, form):
            argd = wash_urlargd(form, {'ln': (str, CFG_SITE_LANG),
                                       'verbose': (int, 0)})
            menu = TEMPLATE.tmpl_person_menu_admin(self.person_id, argd['ln'])

            if "verbose" in argd and argd["verbose"] > 0:
                session = get_session(req)
                pinfo = session['personinfo']
                menu += "\n<pre>" + pformat(pinfo) + "</pre>\n"

            return menu


        generate_optional_menu = {'guest': generate_optional_menu_guest,
                                  'user': generate_optional_menu_user,
                                  'admin': generate_optional_menu_admin}

        return "<div class=\"clearfix\">" + generate_optional_menu[ulevel](req, form) + "</div>"


    def _generate_ticket_box(self, ulevel, req):
        '''
        Generates the semi-permanent info box for the specified user permission
        level.

        @param ulevel: user permission level
        @type ulevel: str
        @param req: apache request object
        @type req: apache request object

        @return: info box
        @rtype: str
        '''
        def generate_ticket_box_guest(req):
            session = get_session(req)
            pinfo = session['personinfo']
            ticket = pinfo['ticket']
            results = list()
            pendingt = list()
            for t in ticket:
                if 'execution_result' in t:
                    for res in t['execution_result']:
                        results.append(res)
                else:
                    pendingt.append(t)

            box = ""
            if pendingt:
                box += TEMPLATE.tmpl_ticket_box('in_process', 'transaction', len(pendingt))

            if results:
                failed = [messages for status, messages in results if not status]
                if failed:
                    box += TEMPLATE.tmpl_transaction_box('failure', failed)

                successfull = [messages for status, messages in results if status]
                if successfull:
                    box += TEMPLATE.tmpl_transaction_box('success', successfull)

            return box

        def generate_ticket_box_user(req):
            return generate_ticket_box_guest(req)

        def generate_ticket_box_admin(req):
            return generate_ticket_box_guest(req)


        generate_ticket_box = {'guest': generate_ticket_box_guest,
                               'user': generate_ticket_box_user,
                               'admin': generate_ticket_box_admin}

        return generate_ticket_box[ulevel](req)


    def _generate_person_info_box(self, ulevel, ln):
        '''
        Generates the name info box for the specified user permission level.

        @param ulevel: user permission level
        @type ulevel: str
        @param ln: page display language
        @type ln: str

        @return: name info box
        @rtype: str
        '''
        def generate_person_info_box_guest(ln):
            names = webapi.get_person_names_from_id(self.person_id)
            box = TEMPLATE.tmpl_admin_person_info_box(ln, person_id=self.person_id,
                                                      names=names)
            return box

        def generate_person_info_box_user(ln):
            return generate_person_info_box_guest(ln)

        def generate_person_info_box_admin(ln):
            return generate_person_info_box_guest(ln)


        generate_person_info_box = {'guest': generate_person_info_box_guest,
                                    'user': generate_person_info_box_user,
                                    'admin': generate_person_info_box_admin}

        return generate_person_info_box[ulevel](ln)


    def _generate_tabs(self, ulevel, req):
        '''
        Generates the tabs content for the specified user permission level.

        @param ulevel: user permission level
        @type ulevel: str
        @param req: apache request object
        @type req: apache request object

        @return: tabs content
        @rtype: str
        '''
        from invenio.bibauthorid_templates import verbiage_dict as tmpl_verbiage_dict
        from invenio.bibauthorid_templates import buttons_verbiage_dict as tmpl_buttons_verbiage_dict

        def generate_tabs_guest(req):
            links = list()   # ['delete', 'commit','del_entry','commit_entry']
            tabs = ['records', 'repealed', 'review']

            return generate_tabs_admin(req, show_tabs=tabs, ticket_links=links,
                                       open_tickets=list(),
                                       verbiage_dict=tmpl_verbiage_dict['guest'],
                                       buttons_verbiage_dict=tmpl_buttons_verbiage_dict['guest'],
                                       show_reset_button=False)

        def generate_tabs_user(req):
            links = ['delete', 'del_entry']
            tabs = ['records', 'repealed', 'review', 'tickets']

            session = get_session(req)
            pinfo = session['personinfo']
            uid = getUid(req)
            user_is_owner = 'not_owner'
            if pinfo["claimpaper_admin_last_viewed_pid"] == webapi.get_pid_from_uid(uid):
                user_is_owner = 'owner'

            open_tickets = webapi.get_person_request_ticket(self.person_id)
            tickets = list()
            for t in open_tickets:
                owns = False
                for row in t[0]:
                    if row[0] == 'uid-ip' and row[1].split('||')[0] == str(uid):
                        owns = True
                if owns:
                    tickets.append(t)

            return generate_tabs_admin(req, show_tabs=tabs, ticket_links=links,
                                       open_tickets=tickets,
                                       verbiage_dict=tmpl_verbiage_dict['user'][user_is_owner],
                                       buttons_verbiage_dict=tmpl_buttons_verbiage_dict['user'][user_is_owner])

        def generate_tabs_admin(req, show_tabs=['records', 'repealed', 'review', 'comments', 'tickets', 'data'],
                                ticket_links=['delete', 'commit', 'del_entry', 'commit_entry'], open_tickets=None,
                                verbiage_dict=None, buttons_verbiage_dict=None, show_reset_button=True):
            session = get_session(req)
            personinfo = dict()

            try:
                personinfo = session["personinfo"]
            except KeyError:
                return ""

            if 'ln' in personinfo:
                ln = personinfo["ln"]
            else:
                ln = CFG_SITE_LANG

            all_papers = webapi.get_papers_by_person_id(self.person_id, ext_out=True)
            records = [{'recid': paper[0],
                        'bibref': paper[1],
                        'flag': paper[2],
                        'authorname': paper[3],
                        'authoraffiliation': paper[4],
                        'paperdate': paper[5],
                        'rt_status': paper[6],
                        'paperexperiment': paper[7]} for paper in all_papers]
            rejected_papers = [row for row in records if row['flag'] < -1]
            rest_of_papers = [row for row in records if row['flag'] >= -1]
            review_needed = webapi.get_review_needing_records(self.person_id)

            if len(review_needed) < 1:
                if 'review' in show_tabs:
                    show_tabs.remove('review')

            if open_tickets == None:
                open_tickets = webapi.get_person_request_ticket(self.person_id)
            else:
                if len(open_tickets) < 1 and 'tickets' in show_tabs:
                    show_tabs.remove('tickets')

            rt_tickets = None
            if "admin_requested_ticket_id" in personinfo:
                rt_tickets = personinfo["admin_requested_ticket_id"]

            if verbiage_dict is None:
                verbiage_dict = translate_dict_values(tmpl_verbiage_dict['admin'], ln)
            if buttons_verbiage_dict is None:
                buttons_verbiage_dict = translate_dict_values(tmpl_buttons_verbiage_dict['admin'], ln)

            # send data to the template function
            tabs = TEMPLATE.tmpl_admin_tabs(ln, person_id=self.person_id,
                                            rejected_papers=rejected_papers,
                                            rest_of_papers=rest_of_papers,
                                            review_needed=review_needed,
                                            rt_tickets=rt_tickets,
                                            open_rt_tickets=open_tickets,
                                            show_tabs=show_tabs,
                                            ticket_links=ticket_links,
                                            verbiage_dict=verbiage_dict,
                                            buttons_verbiage_dict=buttons_verbiage_dict,
                                            show_reset_button=show_reset_button)

            return tabs

        def translate_dict_values(dictionary, ln):
            def translate_str_values(dictionary, f=lambda x: x):
                translated_dict = dict()
                for key, value in dictionary.iteritems():
                    if isinstance(value, str):
                        translated_dict[key] = f(value)
                    elif isinstance(value, dict):
                        translated_dict[key] = translate_str_values(value, f)
                    else:
                        raise TypeError("Value should be either string or dictionary.")
                return translated_dict

            return translate_str_values(dictionary, f=gettext_set_language(ln))


        generate_tabs = {'guest': generate_tabs_guest,
                         'user': generate_tabs_user,
                         'admin': generate_tabs_admin}

        return generate_tabs[ulevel](req)


    def _generate_footer(self, ulevel):
        '''
        Generates the footer for the specified user permission level.

        @param ulevel: user permission level
        @type ulevel: str

        @return: footer
        @rtype: str
        '''
        def generate_footer_guest():
            return TEMPLATE.tmpl_invenio_search_box()

        def generate_footer_user():
            return generate_footer_guest()

        def generate_footer_admin():
            return generate_footer_guest()

        generate_footer = {'guest': generate_footer_guest,
                           'user': generate_footer_user,
                           'admin': generate_footer_admin}

        return generate_footer[ulevel]()


    def _ticket_dispatch_end(self, req):
        '''
        The ticket dispatch is finished, redirect to the original page of
        origin or to the last_viewed_pid or return to the papers autoassigned box to populate its data
        '''
        session = get_session(req)
        pinfo = session["personinfo"]
        webapi.session_bareinit(req)
        if 'claim_in_process' in pinfo:
            pinfo['claim_in_process'] = False

        if "merge_ticket" in pinfo and pinfo['merge_ticket']:
            pinfo['merge_ticket'] = []

        user_info = collect_user_info(req)
        user_info['precached_viewclaimlink'] = True
        session.dirty = True

        if "referer" in pinfo and pinfo["referer"]:
            referer = pinfo["referer"]
            del(pinfo["referer"])
            session.dirty = True
            return redirect_to_url(req, referer)

        # if we are coming fromt he autoclaim box we should not redirect and just return to the caller function
        if 'autoclaim' in pinfo and pinfo['autoclaim']['review_failed'] == False and pinfo['autoclaim']['begin_autoclaim'] == True:
            pinfo['autoclaim']['review_failed'] = False
            pinfo['autoclaim']['begin_autoclaim'] = False
            session.dirty = True
        else:
            redirect_page = webapi.history_get_last_visited_url(pinfo['visit_diary'], limit_to_page=['manage_profile', 'claim'])
            if not redirect_page:
                redirect_page = webapi.get_fallback_redirect_link(req)
            if 'autoclaim' in pinfo and pinfo['autoclaim']['review_failed'] == True and pinfo['autoclaim']['checkout'] == True:
                redirect_page = '%s/author/claim/action?checkout=True'  % (CFG_SITE_URL,)
                pinfo['autoclaim']['checkout'] = False
                session.dirty = True
            elif not 'manage_profile' in redirect_page:
                pinfo['autoclaim']['review_failed'] = False
                pinfo['autoclaim']['begin_autoclaim'] == False
                pinfo['autoclaim']['checkout'] = True
                session.dirty = True
                redirect_page = '%s/author/claim/%s?open_claim=True'  % (CFG_SITE_URL, webapi.get_person_redirect_link(pinfo["claimpaper_admin_last_viewed_pid"]))
            else:
                pinfo['autoclaim']['review_failed'] = False
                pinfo['autoclaim']['begin_autoclaim'] == False
                pinfo['autoclaim']['checkout'] = True
                session.dirty = True
            return redirect_to_url(req, redirect_page)

#            redirect_link = diary('get_redirect_link', caller='_ticket_dispatch_end', parameters=[('open_claim','True')])
#            return redirect_to_url(req, redirect_link)


    # need review if should be deleted
    def __user_is_authorized(self, req, action):
        '''
        Determines if a given user is authorized to perform a specified action

        @param req: Apache Request Object
        @type req: Apache Request Object
        @param action: the action the user wants to perform
        @type action: string

        @return: True if user is allowed to perform the action, False if not
        @rtype: boolean
        '''
        if not req:
            return False

        if not action:
            return False
        else:
            action = escape(action)

        uid = getUid(req)

        if not isinstance(uid, int):
            return False

        if uid == 0:
            return False

        allowance = [i[1] for i in acc_find_user_role_actions({'uid': uid})
                     if i[1] == action]

        if allowance:
            return True

        return False


    @staticmethod
    def _scripts(kill_browser_cache=False):
        '''
        Returns html code to be included in the meta header of the html page.
        The actual code is stored in the template.

        @return: html formatted Javascript and CSS inclusions for the <head>
        @rtype: string
        '''
        return TEMPLATE.tmpl_meta_includes(kill_browser_cache)


    def _check_user_fields(self, req, form):
        argd = wash_urlargd(
            form,
            {'ln': (str, CFG_SITE_LANG),
             'user_first_name': (str, None),
             'user_last_name': (str, None),
             'user_email': (str, None),
             'user_comments': (str, None)})
        session = get_session(req)
        pinfo = session["personinfo"]
        ulevel = pinfo["ulevel"]
        skip_checkout_faulty_fields = False

        if ulevel in ['user', 'admin']:
            skip_checkout_faulty_fields = True

        if not ("user_first_name_sys" in pinfo and pinfo["user_first_name_sys"]):
            if "user_first_name" in argd and argd['user_first_name']:
                if not argd["user_first_name"] and not skip_checkout_faulty_fields:
                    pinfo["checkout_faulty_fields"].append("user_first_name")
                else:
                    pinfo["user_first_name"] = escape(argd["user_first_name"])

        if not ("user_last_name_sys" in pinfo and pinfo["user_last_name_sys"]):
            if "user_last_name" in argd and argd['user_last_name']:
                if not argd["user_last_name"] and not skip_checkout_faulty_fields:
                    pinfo["checkout_faulty_fields"].append("user_last_name")
                else:
                    pinfo["user_last_name"] = escape(argd["user_last_name"])

        if not ("user_email_sys" in pinfo and pinfo["user_email_sys"]):
            if "user_email" in argd and argd['user_email']:
                if not email_valid_p(argd["user_email"]):
                    pinfo["checkout_faulty_fields"].append("user_email")
                else:
                    pinfo["user_email"] = escape(argd["user_email"])

                if (ulevel == "guest"
                    and emailUnique(argd["user_email"]) > 0):
                    pinfo["checkout_faulty_fields"].append("user_email_taken")
            else:
                pinfo["checkout_faulty_fields"].append("user_email")

        if "user_comments" in argd:
            if argd["user_comments"]:
                pinfo["user_ticket_comments"] = escape(argd["user_comments"])
            else:
                pinfo["user_ticket_comments"] = ""

        session.dirty = True


    def action(self, req, form):
        '''
        Initial step in processing of requests: ticket generation/update.
        Also acts as action dispatcher for interface mass action requests.

        Valid mass actions are:
        - add_external_id: add an external identifier to an author
        - add_missing_external_ids: add missing external identifiers of an author
        - bibref_check_submit:
        - cancel: clean the session (erase tickets and so on)
        - cancel_rt_ticket:
        - cancel_search_ticket:
        - cancel_stage:
        - checkout:
        - checkout_continue_claiming:
        - checkout_remove_transaction:
        - checkout_submit:
        - claim: claim papers for an author
        - commit_rt_ticket:
        - confirm: confirm assignments to an author
        - delete_external_ids: delete external identifiers of an author
        - repeal: repeal assignments from an author
        - reset: reset assignments of an author
        - set_canonical_name: set/swap the canonical name of an author
        - to_other_person: assign a document from an author to another author

        @param req: apache request object
        @type req: apache request object
        @param form: parameters sent via GET or POST request
        @type form: dict

        @return: a full page formatted in HTML
        @return: str
        '''
        webapi.session_bareinit(req)
        session = get_session(req)
        pinfo = session["personinfo"]
        argd = wash_urlargd(form,
                            {'autoclaim_show_review':(str, None),
                             'canonical_name': (str, None),
                             'existing_ext_ids': (list, None),
                             'ext_id': (str, None),
                             'uid': (int, None),
                             'ext_system': (str, None),
                             'ln': (str, CFG_SITE_LANG),
                             'pid': (int, -1),
                             'primary_profile':(str, None),
                             'search_param': (str, None),
                             'rt_action': (str, None),
                             'rt_id': (int, None),
                             'selection': (list, None),

                             # permitted actions
                             'add_external_id': (str, None),
                             'set_uid': (str, None),
                             'add_missing_external_ids': (str, None),
                             'associate_profile': (str, None),
                             'bibref_check_submit': (str, None),
                             'cancel': (str, None),
                             'cancel_merging': (str, None),
                             'cancel_rt_ticket': (str, None),
                             'cancel_search_ticket': (str, None),
                             'cancel_stage': (str, None),
                             'checkout': (str, None),
                             'checkout_continue_claiming': (str, None),
                             'checkout_remove_transaction': (str, None),
                             'checkout_submit': (str, None),
                             'assign': (str, None),
                             'commit_rt_ticket': (str, None),
                             'confirm': (str, None),
                             'delete_external_ids': (str, None),
                             'merge': (str, None),
                             'reject': (str, None),
                             'repeal': (str, None),
                             'reset': (str, None),
                             'send_message': (str, None),
                             'set_canonical_name': (str, None),
                             'to_other_person': (str, None)})

        ulevel = pinfo["ulevel"]
        ticket = pinfo["ticket"]
        uid = getUid(req)
        ln = argd['ln']
        action = None

        permitted_actions = ['add_external_id',
                             'set_uid',
                             'add_missing_external_ids',
                             'associate_profile',
                             'bibref_check_submit',
                             'cancel',
                             'cancel_merging',
                             'cancel_rt_ticket',
                             'cancel_search_ticket',
                             'cancel_stage',
                             'checkout',
                             'checkout_continue_claiming',
                             'checkout_remove_transaction',
                             'checkout_submit',
                             'assign',
                             'commit_rt_ticket',
                             'confirm',
                             'delete_external_ids',
                             'merge',
                             'reject',
                             'repeal',
                             'reset',
                             'send_message',
                             'set_canonical_name',
                             'to_other_person']

        for act in permitted_actions:
            # one action (the most) is enabled in the form
            if argd[act] is not None:
                action = act

        no_access = self._page_access_permission_wall(req, None)
        if no_access and action not in ["assign"]:
            return no_access

        # incomplete papers (incomplete paper info or other problems) trigger action function without user's interference
        # in order to fix those problems and claim papers or remove them from the ticket
        if (action is None
             and "bibref_check_required" in pinfo
             and pinfo["bibref_check_required"]):

            if "bibref_check_reviewed_bibrefs" in pinfo:
                del(pinfo["bibref_check_reviewed_bibrefs"])
                session.dirty = True

        def add_external_id():
            '''
            associates the user with pid to the external id ext_id
            '''
            if argd['pid'] > -1:
                pid = argd['pid']
            else:
                return self._error_page(req, ln,
                            "Fatal: cannot add external id to unknown person")

            if argd['ext_system'] is not None:
                ext_sys = argd['ext_system']
            else:
                return self._error_page(req, ln,
                            "Fatal: cannot add an external id without specifying the system")

            if argd['ext_id'] is not None:
                ext_id = argd['ext_id']
            else:
                return self._error_page(req, ln,
                            "Fatal: cannot add a custom external id without a suggestion")

            userinfo = "%s||%s" % (uid, req.remote_ip)
            webapi.add_person_external_id(pid, ext_sys, ext_id, userinfo)

            return redirect_to_url(req, "%s/author/manage_profile/%s" % (CFG_SITE_URL, webapi.get_person_redirect_link(pid)))

        def set_uid():
            '''
            associates the user with pid to the external id ext_id
            '''
            if argd['pid'] > -1:
                pid = argd['pid']
            else:
                return self._error_page(req, ln,
                            "Fatal: current user is unknown")

            if argd['uid'] is not None:
                dest_uid = int(argd['uid'])
            else:
                return self._error_page(req, ln,
                            "Fatal: user id is not valid")

            userinfo = "%s||%s" % (uid, req.remote_ip)
            webapi.set_person_uid(pid, dest_uid, userinfo)

            # remove arxiv pubs of current pid
            remove_arxiv_papers_of_author(pid)
            dest_uid_pid = webapi.get_pid_from_uid(dest_uid)
            if dest_uid_pid > -1:
                # move the arxiv pubs of the dest_uid to the current pid
                dest_uid_arxiv_papers = webapi.get_arxiv_papers_of_author(dest_uid_pid)
                webapi.add_arxiv_papers_to_author(dest_uid_arxiv_papers, pid)

            return redirect_to_url(req, "%s/author/manage_profile/%s" % (CFG_SITE_URL, webapi.get_person_redirect_link(pid)))

        def add_missing_external_ids():
            if argd['pid'] > -1:
                pid = argd['pid']
            else:
                return self._error_page(req, ln,
                            "Fatal: cannot recompute external ids for an unknown person")

            update_external_ids_of_authors([pid], overwrite=False)

            return redirect_to_url(req, "%s/author/manage_profile/%s" % (CFG_SITE_URL, webapi.get_person_redirect_link(pid)))

        def associate_profile():
            '''
            associates the user with user id to the person profile with pid
            '''
            if argd['pid'] > -1:
                pid = argd['pid']
            else:
                return self._error_page(req, ln,
                        "Fatal: cannot associate profile without a person id.")

            uid = getUid(req)

            pid, profile_claimed = webapi.claim_profile(uid, pid)

            redirect_pid = pid

            if profile_claimed:
                pinfo['pid'] = pid
                pinfo['should_check_to_autoclaim'] = True
                pinfo["login_info_message"] = "confirm_success"
                session.dirty = True
                redirect_to_url(req, '%s/author/manage_profile/%s' % (CFG_SITE_URL, redirect_pid))
            # if someone have already claimed this profile it redirects to choose_profile with an error message
            else:
                param=''
                if 'search_param' in argd and argd['search_param']:
                    param = '&search_param=' + argd['search_param']
                redirect_to_url(req, '%s/author/choose_profile?failed=%s%s' % (CFG_SITE_URL, True, param))

        def bibref_check_submit():
            pinfo["bibref_check_reviewed_bibrefs"] = list()
            add_rev = pinfo["bibref_check_reviewed_bibrefs"].append

            if ("bibrefs_auto_assigned" in pinfo
                 or "bibrefs_to_confirm" in pinfo):
                person_reviews = list()

                if ("bibrefs_auto_assigned" in pinfo
                     and pinfo["bibrefs_auto_assigned"]):
                    person_reviews.append(pinfo["bibrefs_auto_assigned"])

                if ("bibrefs_to_confirm" in pinfo
                     and pinfo["bibrefs_to_confirm"]):
                    person_reviews.append(pinfo["bibrefs_to_confirm"])

                for ref_review in person_reviews:
                    for person_id in ref_review:
                        for bibrec in ref_review[person_id]["bibrecs"]:
                            rec_grp = "bibrecgroup%s" % bibrec
                            elements = list()

                            if rec_grp in form:
                                if isinstance(form[rec_grp], str):
                                    elements.append(form[rec_grp])
                                elif isinstance(form[rec_grp], list):
                                    elements += form[rec_grp]
                                else:
                                    continue

                                for element in elements:
                                    test = element.split("||")

                                    if test and len(test) > 1 and test[1]:
                                        tref = test[1] + "," + str(bibrec)
                                        tpid = webapi.wash_integer_id(test[0])

                                        if (webapi.is_valid_bibref(tref)
                                             and tpid > -1):
                                            add_rev(element + "," + str(bibrec))
            session.dirty = True

        def cancel():
            self.__session_cleanup(req)

            return self._ticket_dispatch_end(req)

        def cancel_merging():
            '''
            empties the session out of merge content and redirects to the manage profile page
            that the user was viewing before the merge
            '''
            if argd['primary_profile']:
                primary_cname = argd['primary_profile']
            else:
                return self._error_page(req, ln,
                                        "Fatal: Couldn't redirect to the previous page")

            webapi.session_bareinit(req)
            session = get_session(req)
            pinfo = session['personinfo']

            if pinfo['merge_profiles']:
                pinfo['merge_profiles'] = list()

            session.dirty = True

            redirect_url = "%s/author/manage_profile/%s" % (CFG_SITE_URL, primary_cname)
            return redirect_to_url(req, redirect_url)

        def cancel_rt_ticket():
            if argd['selection'] is not None:
                bibrefrecs = argd['selection']
            else:
                return self._error_page(req, ln,
                            "Fatal: cannot cancel unknown ticket")

            if argd['pid'] > -1:
                pid = argd['pid']
            else:
                return self._error_page(req, ln, "Fatal: cannot cancel unknown ticket")

            if argd['rt_id'] is not None and argd['rt_action'] is not None:
                rt_id = int(argd['rt_id'])
                rt_action = argd['rt_action']

                for bibrefrec in bibrefrecs:
                    webapi.delete_transaction_from_request_ticket(pid, rt_id, rt_action, bibrefrec)
            else:
                rt_id = int(bibrefrecs[0])
                webapi.delete_request_ticket(pid, rt_id)

            return redirect_to_url(req, "%s/author/claim/%s" % (CFG_SITE_URL, pid))

        def cancel_search_ticket(without_return=False):
            if 'search_ticket' in pinfo:
                del(pinfo['search_ticket'])
            session.dirty = True

            if "claimpaper_admin_last_viewed_pid" in pinfo:
                pid = pinfo["claimpaper_admin_last_viewed_pid"]

                if not without_return:
                    return redirect_to_url(req, "%s/author/claim/%s" % (CFG_SITE_URL, webapi.get_person_redirect_link(pid)))

            if not without_return:
                return self.search(req, form)

        def cancel_stage():
            if 'bibref_check_required' in pinfo:
                del(pinfo['bibref_check_required'])

            if 'bibrefs_auto_assigned' in pinfo:
                del(pinfo['bibrefs_auto_assigned'])

            if 'bibrefs_to_confirm' in pinfo:
                del(pinfo['bibrefs_to_confirm'])

            for tt in [row for row in ticket if 'incomplete' in row]:
                ticket.remove(tt)

            session.dirty = True

            return self._ticket_dispatch_end(req)

        def checkout():
            pass
            # return self._ticket_final_review(req)

        def checkout_continue_claiming():
            pinfo["checkout_faulty_fields"] = list()
            self._check_user_fields(req, form)

            return self._ticket_dispatch_end(req)

        def checkout_remove_transaction():
            bibref = argd['checkout_remove_transaction']

            if webapi.is_valid_bibref(bibref):
                for rmt in [row for row in ticket if row["bibref"] == bibref]:
                    ticket.remove(rmt)

            pinfo["checkout_confirmed"] = False
            session.dirty = True
            # return self._ticket_final_review(req)

        def checkout_submit():
            pinfo["checkout_faulty_fields"] = list()
            self._check_user_fields(req, form)

            if not ticket:
                pinfo["checkout_faulty_fields"].append("tickets")

            pinfo["checkout_confirmed"] = True
            if pinfo["checkout_faulty_fields"]:
                pinfo["checkout_confirmed"] = False

            session.dirty = True

            # return self._ticket_final_review(req)

        def claim():
            if argd['selection'] is not None:
                bibrefrecs = argd['selection']
            else:
                return self._error_page(req, ln,
                            "Fatal: cannot create ticket without any bibrefrec")
            if argd['pid'] > -1:
                pid = argd['pid']
            else:
                return self._error_page(req, ln,
                            "Fatal: cannot claim papers to an unknown person")

            if action == 'assign':
                claimed_recs = [paper[2] for paper in get_claimed_papers_of_author(pid)]
                for bibrefrec in list(bibrefrecs):
                    _, rec = webapi.split_bibrefrec(bibrefrec)
                    if rec in claimed_recs:
                        bibrefrecs.remove(bibrefrec)

            for bibrefrec in bibrefrecs:
                operation_parts = {'pid': pid,
                                   'action': action,
                                   'bibrefrec': bibrefrec}

                operation_to_be_added = webapi.construct_operation(operation_parts, pinfo, uid)
                if operation_to_be_added is None:
                    continue

                ticket = pinfo['ticket']
                webapi.add_operation_to_ticket(operation_to_be_added, ticket)

            session.dirty = True

            return redirect_to_url(req, "%s/author/claim/%s" % (CFG_SITE_URL, webapi.get_person_redirect_link(pid)))

        def claim_to_other_person():
            if argd['selection'] is not None:
                bibrefrecs = argd['selection']
            else:
                return self._error_page(req, ln,
                            "Fatal: cannot create ticket without any bibrefrec")

            return self._ticket_open_assign_to_other_person(req, bibrefrecs, form)

        def commit_rt_ticket():
            if argd['selection'] is not None:
                tid = argd['selection'][0]
            else:
                return self._error_page(req, ln,
                            "Fatal: cannot cancel unknown ticket")

            if argd['pid'] > -1:
                pid = argd['pid']
            else:
                return self._error_page(req, ln,
                            "Fatal: cannot cancel unknown ticket")

            return self._commit_rt_ticket(req, tid, pid)

        def confirm_repeal_reset():
            if argd['pid'] > -1 or int(argd['pid']) == CREATE_NEW_PERSON:
                pid = argd['pid']
                cancel_search_ticket(without_return = True)
            else:
                return self._ticket_open_assign_to_other_person(req, argd['selection'], form)
                #return self._error_page(req, ln, "Fatal: cannot create ticket without a person id! (crr %s)" %repr(argd))

            bibrefrecs = argd['selection']

            if argd['confirm']:
                action = 'assign'
            elif argd['repeal']:
                action = 'reject'
            elif argd['reset']:
                action = 'reset'
            else:
                return self._error_page(req, ln, "Fatal: not existent action!")

            for bibrefrec in bibrefrecs:
                form['jsondata'] = json.dumps({'pid': str(pid),
                                               'action': action,
                                               'bibrefrec': bibrefrec,
                                               'on': 'user'})

                t = WebInterfaceAuthorTicketHandling()
                t.add_operation(req, form)

            return redirect_to_url(req, "%s/author/claim/%s" % (CFG_SITE_URL, webapi.get_person_redirect_link(pid)))

        def delete_external_ids():
            '''
            deletes association between the user with pid and the external id ext_id
            '''
            if argd['pid'] > -1:
                pid = argd['pid']
            else:
                return self._error_page(req, ln,
                            "Fatal: cannot delete external ids from an unknown person")

            if argd['existing_ext_ids'] is not None:
                existing_ext_ids = argd['existing_ext_ids']
            else:
                return self._error_page(req, ln,
                            "Fatal: you must select at least one external id in order to delete it")

            userinfo = "%s||%s" % (uid, req.remote_ip)
            webapi.delete_person_external_ids(pid, existing_ext_ids, userinfo)

            return redirect_to_url(req, "%s/author/manage_profile/%s" % (CFG_SITE_URL, webapi.get_person_redirect_link(pid)))

        def none_action():
            return self._error_page(req, ln,
                        "Fatal: cannot create ticket if no action selected.")

        def merge():
            '''
            performs a merge if allowed on the profiles that the user chose
            '''
            if argd['primary_profile']:
                primary_cname = argd['primary_profile']
            else:
                return self._error_page(req, ln,
                                        "Fatal: cannot perform a merge without a primary profile!")

            if argd['selection']:
                profiles_to_merge = argd['selection']
            else:
                return self._error_page(req, ln,
                                        "Fatal: cannot perform a merge without any profiles selected!")

            webapi.session_bareinit(req)
            session = get_session(req)
            pinfo = session['personinfo']
            uid = getUid(req)

            primary_pid = webapi.get_person_id_from_canonical_id(primary_cname)
            pids_to_merge = [webapi.get_person_id_from_canonical_id(cname) for cname in profiles_to_merge]

            is_admin = False
            if pinfo['ulevel'] == 'admin':
                is_admin = True

            # checking if there are restrictions regarding this merge
            can_perform_merge, preventing_pid = webapi.merge_is_allowed(primary_pid, pids_to_merge, is_admin)

            if not can_perform_merge:
                # when redirected back to the merge profiles page display an error message about the currently attempted merge
                pinfo['merge_info_message'] = ("failure", "confirm_failure")
                session.dirty = True

                redirect_url = "%s/author/merge_profiles?primary_profile=%s" % (CFG_SITE_URL, primary_cname)
                return redirect_to_url(req, redirect_url)

            if is_admin:
                webapi.merge_profiles(primary_pid, pids_to_merge)
                # when redirected back to the manage profile page display a message about the currently attempted merge
                pinfo['merge_info_message'] = ("success", "confirm_success")

            else:
                name = ''
                if 'user_last_name' in pinfo:
                    name = pinfo['user_last_name']

                if 'user_first_name' in pinfo:
                    name += pinfo['user_first_name']

                email = ''
                if 'user_email' in pinfo:
                    email = pinfo['user_email']

                selection_str = "&selection=".join(profiles_to_merge)

                userinfo = {'uid-ip': "userid: %s (from %s)" % (uid, req.remote_ip),
                            'name': name,
                            'email': email,
                            'merge link': "%s/author/merge_profiles?primary_profile=%s&selection=%s" % (CFG_SITE_URL, primary_cname, selection_str)}
                # a message is sent to the admin with info regarding the currently attempted merge
                webapi.create_request_message(userinfo, subj='Merge profiles request')

                # when redirected back to the manage profile page display a message about the merge
                pinfo['merge_info_message'] = ("success", "confirm_operation")

            pinfo['merge_profiles'] = list()

            session.dirty = True

            redirect_url = "%s/author/manage_profile/%s" % (CFG_SITE_URL, primary_cname)
            return redirect_to_url(req, redirect_url)

        def send_message():
            '''
            sends a message from the user to the admin
            '''
            webapi.session_bareinit(req)
            session = get_session(req)
            pinfo = session['personinfo']
            #pp = pprint.PrettyPrinter(indent=4)
            #session_dump = pp.pprint(pinfo)
            session_dump = str(pinfo)
            name = ''
            name_changed = False
            name_given = ''
            email = ''
            email_changed = False
            email_given = ''
            comment = ''
            last_page_visited = ''

            if "user_last_name" in pinfo:
                name = pinfo["user_last_name"]

            if "user_first_name" in pinfo:
                name += pinfo["user_first_name"]
            name = name.rstrip()

            if "user_email" in pinfo:
                email = pinfo["user_email"]
            email = email.rstrip()

            if 'Name' in form:
                if not name:
                    name = form['Name']
                elif name != form['Name']:
                    name_given = form['Name']
                    name_changed = True
                name = name.rstrip()

            if 'E-mail'in form:
                if not email:
                    email = form['E-mail']
                elif name != form['E-mail']:
                    email_given = form['E-mail']
                    email_changed = True
                email = email.rstrip()

            if 'Comment' in form:
                comment = form['Comment']
                comment = comment.rstrip()


            if not name or not comment or not email:
                redirect_to_url(req, '%s/author/help?incomplete_params=%s' % (CFG_SITE_URL, True))
            if 'last_page_visited' in form:
                last_page_visited = form['last_page_visited']

            uid = getUid(req)
            userinfo = {'uid-ip': "userid: %s (from %s)" % (uid, req.remote_ip),
                        'name': name,
                        'email': email,
                        'comment': comment,
                        'last_page_visited': last_page_visited,
                        'session_dump': session_dump,
                        'name_given': name_given,
                        'email_given': email_given,
                        'name_changed': name_changed,
                        'email_changed': email_changed}

            webapi.create_request_message(userinfo)

        def set_canonical_name():
            if argd['pid'] > -1:
                pid = argd['pid']
            else:
                return self._error_page(req, ln,
                            "Fatal: cannot set canonical name to unknown person")

            if argd['canonical_name'] is not None:
                cname = argd['canonical_name']
            else:
                return self._error_page(req, ln,
                            "Fatal: cannot set a custom canonical name without a suggestion")

            userinfo = "%s||%s" % (uid, req.remote_ip)
            if webapi.is_valid_canonical_id(cname):
                webapi.swap_person_canonical_name(pid, cname, userinfo)
            else:
                webapi.update_person_canonical_name(pid, cname, userinfo)

            return redirect_to_url(req, "%s/author/claim/%s%s" % (CFG_SITE_URL, webapi.get_person_redirect_link(pid), '#tabData'))

        action_functions = {'add_external_id': add_external_id,
                            'set_uid': set_uid,
                            'add_missing_external_ids': add_missing_external_ids,
                            'associate_profile': associate_profile,
                            'bibref_check_submit': bibref_check_submit,
                            'cancel': cancel,
                            'cancel_merging': cancel_merging,
                            'cancel_rt_ticket': cancel_rt_ticket,
                            'cancel_search_ticket': cancel_search_ticket,
                            'cancel_stage': cancel_stage,
                            'checkout': checkout,
                            'checkout_continue_claiming': checkout_continue_claiming,
                            'checkout_remove_transaction': checkout_remove_transaction,
                            'checkout_submit': checkout_submit,
                            'assign': claim,
                            'commit_rt_ticket': commit_rt_ticket,
                            'confirm': confirm_repeal_reset,
                            'delete_external_ids': delete_external_ids,
                            'merge': merge,
                            'reject': claim,
                            'repeal': confirm_repeal_reset,
                            'reset': confirm_repeal_reset,
                            'send_message': send_message,
                            'set_canonical_name': set_canonical_name,
                            'to_other_person': claim_to_other_person,
                            None: none_action}

        return action_functions[action]()


    def _ticket_open_claim(self, req, bibrefs, ln):
        '''
        Generate page to let user choose how to proceed

        @param req: Apache Request Object
        @type req: Apache Request Object
        @param bibrefs: list of record IDs to perform an action on
        @type bibrefs: list of int
        @param ln: language to display the page in
        @type ln: string
        '''
        session = get_session(req)
        uid = getUid(req)
        uinfo = collect_user_info(req)
        pinfo = session["personinfo"]

        if 'ln' in pinfo:
            ln = pinfo["ln"]
        else:
            ln = CFG_SITE_LANG

        _ = gettext_set_language(ln)
        no_access = self._page_access_permission_wall(req)
        session.dirty = True
        pid = -1
        search_enabled = True

        if not no_access and uinfo["precached_usepaperclaim"]:
            tpid = webapi.get_pid_from_uid(uid)

            if tpid > -1:
                pid = tpid

        last_viewed_pid = False
        if (not no_access
            and "claimpaper_admin_last_viewed_pid" in pinfo
            and pinfo["claimpaper_admin_last_viewed_pid"]):
            names = webapi.get_person_names_from_id(pinfo["claimpaper_admin_last_viewed_pid"])
            names = sorted([i for i in names], key=lambda k: k[1], reverse=True)
            if len(names) > 0:
                if len(names[0]) > 0:
                    last_viewed_pid = [pinfo["claimpaper_admin_last_viewed_pid"], names[0][0]]

        if no_access:
            search_enabled = False

        pinfo["referer"] = uinfo["referer"]
        session.dirty = True
        body = TEMPLATE.tmpl_open_claim(bibrefs, pid, last_viewed_pid,
                                        search_enabled=search_enabled)
        body = TEMPLATE.tmpl_person_detail_layout(body)
        title = _('Claim this paper')
        metaheaderadd = WebInterfaceBibAuthorIDClaimPages._scripts(kill_browser_cache=True)

        return page(title=title,
            metaheaderadd=metaheaderadd,
            body=body,
            req=req,
            language=ln)

    def _ticket_open_assign_to_other_person(self, req, bibrefs, form):
        '''
        Initializes search to find a person to attach the selected records to

        @param req: Apache request object
        @type req: Apache request object
        @param bibrefs: list of record IDs to consider
        @type bibrefs: list of int
        @param form: GET/POST request parameters
        @type form: dict
        '''
        session = get_session(req)
        pinfo = session["personinfo"]
        pinfo["search_ticket"] = dict()
        search_ticket = pinfo["search_ticket"]
        search_ticket['action'] = 'assign'
        search_ticket['bibrefs'] = bibrefs
        session.dirty = True
        return self.search(req, form)


    def _cancel_rt_ticket(self, req, tid, pid):
        '''
        deletes an RT ticket
        '''
        webapi.delete_request_ticket(pid, tid)
        return redirect_to_url(req, "%s/author/claim/%s" %
                               (CFG_SITE_URL, webapi.get_person_redirect_link(str(pid))))


    def _cancel_transaction_from_rt_ticket(self, tid, pid, action, bibref):
        '''
        deletes a transaction from an rt ticket
        '''
        webapi.delete_transaction_from_request_ticket(pid, tid, action, bibref)


    def _commit_rt_ticket(self, req, tid, pid):
        '''
        Commit of an rt ticket: creates a real ticket and commits.
        '''
        session = get_session(req)
        pinfo = session["personinfo"]
        ticket = pinfo["ticket"]
        uid = getUid(req)
        tid = int(tid)

        rt_ticket = get_validated_request_tickets_for_author(pid, tid)[0]

        for action, bibrefrec in rt_ticket['operations']:
            operation_parts = {'pid': pid,
                               'action': action,
                               'bibrefrec': bibrefrec}
            operation_to_be_added = webapi.construct_operation(operation_parts, pinfo, uid)
            webapi.add_operation_to_ticket(operation_to_be_added, ticket)

        session.dirty = True

        webapi.delete_request_ticket(pid, tid)

        redirect_to_url(req, "%s/author/claim/%s" % (CFG_SITE_URL, pid))


    def _error_page(self, req, ln=CFG_SITE_LANG, message=None, intro=True):
        '''
        Create a page that contains a message explaining the error.

        @param req: Apache Request Object
        @type req: Apache Request Object
        @param ln: language
        @type ln: string
        @param message: message to be displayed
        @type message: string
        '''
        body = []

        _ = gettext_set_language(ln)

        if not message:
            message = "No further explanation available. Sorry."

        if intro:
            body.append(_("<p>We're sorry. An error occurred while "
                        "handling your request. Please find more information "
                        "below:</p>"))
        body.append("<p><strong>%s</strong></p>" % message)

        return page(title=_("Notice"),
                body="\n".join(body),
                description="%s - Internal Error" % CFG_SITE_NAME,
                keywords="%s, Internal Error" % CFG_SITE_NAME,
                language=ln,
                req=req)


    def __session_cleanup(self, req):
        '''
        Cleans the session from all bibauthorid specific settings and
        with that cancels any transaction currently in progress.

        @param req: Apache Request Object
        @type req: Apache Request Object
        '''
        session = get_session(req)
        try:
            pinfo = session["personinfo"]
        except KeyError:
            return

        if "ticket" in pinfo:
            pinfo['ticket'] = []
        if "search_ticket" in pinfo:
            pinfo['search_ticket'] = dict()

        # clear up bibref checker if it's done.
        if ("bibref_check_required" in pinfo
            and not pinfo["bibref_check_required"]):
            if 'bibrefs_to_confirm' in pinfo:
                del(pinfo['bibrefs_to_confirm'])

            if "bibrefs_auto_assigned" in pinfo:
                del(pinfo["bibrefs_auto_assigned"])

            del(pinfo["bibref_check_required"])

        if "checkout_confirmed" in pinfo:
            del(pinfo["checkout_confirmed"])

        if "checkout_faulty_fields" in pinfo:
            del(pinfo["checkout_faulty_fields"])

        # pinfo['ulevel'] = ulevel
        # pinfo["claimpaper_admin_last_viewed_pid"] = -1
        pinfo["admin_requested_ticket_id"] = -1
        session.dirty = True

    def _generate_search_ticket_box(self, req):
        '''
        Generate the search ticket to remember a pending search for Person
        entities in an attribution process

        @param req: Apache request object
        @type req: Apache request object
        '''
        session = get_session(req)
        pinfo = session["personinfo"]
        search_ticket = None

        if 'search_ticket' in pinfo:
            search_ticket = pinfo['search_ticket']
        if not search_ticket:
            return ''
        else:
            return TEMPLATE.tmpl_search_ticket_box('person_search', 'assign_papers', search_ticket['bibrefs'])

    def search_box(self, query, shown_element_functions):
        '''
        collecting the persons' data that the search function returned

        @param req: Apache request object
        @type req: Apache request object

        @param query: the query string
        @type query: string

        @param shown_element_functions: contains the functions that will tell to the template which columns to show and what buttons to print
        @type shown_element_functions: dict

        @return: html body
        @rtype: string
        '''
        pid_list = self._perform_search(query)
        search_results = []
        for pid in pid_list:
            result = defaultdict(list)
            result['pid'] = pid
            result['canonical_id'] = webapi.get_canonical_id_from_person_id(pid)
            result['name_variants'] = webapi.get_person_names_from_id(pid)
            result['external_ids'] = webapi.get_external_ids_from_person_id(pid)
            # this variable shows if we want to use the following data in the search template
            if 'pass_status' in shown_element_functions and shown_element_functions['pass_status']:
                result['status'] = webapi.is_profile_available(pid)
            search_results.append(result)

        body = TEMPLATE.tmpl_author_search(query, search_results, shown_element_functions)

        body = TEMPLATE.tmpl_person_detail_layout(body)

        return body

    def search(self, req, form):
        '''
        Function used for searching a person based on a name with which the
        function is queried.

        @param req: Apache Request Object
        @type form: dict

        @return: a full page formatted in HTML
        @rtype: string
        '''
        webapi.session_bareinit(req)
        session = get_session(req)

        pinfo = session['personinfo']
        ulevel = pinfo['ulevel']
        person_id = self.person_id
        uid = getUid(req)

        argd = wash_urlargd(
            form,
            {'ln': (str, CFG_SITE_LANG),
             'verbose': (int, 0),
             'q': (str, None)})

        debug = "verbose" in argd and argd["verbose"] > 0
        ln = argd['ln']

        cname = ''
        is_owner = False
        last_visited_pid = webapi.history_get_last_visited_pid(session['personinfo']['visit_diary'])
        if last_visited_pid is not None:
            cname = webapi.get_canonical_id_from_person_id(last_visited_pid)
            try:
                int(cname)
            except ValueError:
                is_owner = False
            else:
                is_owner = self._is_profile_owner(last_visited_pid)

        menu = WebProfileMenu(str(cname), "search", ln, is_owner, self._is_admin(pinfo))

        title = "Person search"
        # Create Wrapper Page Markup
        profile_page = WebProfilePage("search", title, no_cache=True)
        profile_page.add_profile_menu(menu)

        profile_page.add_bootstrapped_data(json.dumps({
            "other": "var gBOX_STATUS = '10';var gPID = '10'; var gNumOfWorkers= '10'; var gReqTimeout= '10'; var gPageTimeout= '10';",
            "backbone": """
            (function(ticketbox) {
                 var app = ticketbox.app;
                 app.userops.set(%s);
                 app.bodyModel.set({userLevel: "%s"});
            })(ticketbox);""" % (WebInterfaceAuthorTicketHandling.bootstrap_status(pinfo, "user"), ulevel)
        }))

        if debug:
            profile_page.add_debug_info(pinfo)


        no_access = self._page_access_permission_wall(req)
        shown_element_functions = dict()
        shown_element_functions['show_search_bar'] = TEMPLATE.tmpl_general_search_bar()

        if no_access:
            return no_access

        search_ticket = None
        bibrefs = []

        if 'search_ticket' in pinfo:
            search_ticket = pinfo['search_ticket']
            for r in search_ticket['bibrefs']:
                bibrefs.append(r)

        if search_ticket and "ulevel" in pinfo:
            if pinfo["ulevel"] == "admin":
                shown_element_functions['new_person_gen'] = TEMPLATE.tmpl_assigning_search_new_person_generator(bibrefs)

        content = ""

        if search_ticket:
            shown_element_functions['button_gen'] = TEMPLATE.tmpl_assigning_search_button_generator(bibrefs)
            content = content + self._generate_search_ticket_box(req)


        query = None

        if 'q' in argd:
            if argd['q']:
                query = escape(argd['q'])

        content += self.search_box(query, shown_element_functions)
        body = profile_page.get_wrapped_body(content)

        parameter = None
        if query:
            parameter = '?search_param=%s' + query
        webapi.history_log_visit(req, 'search', params = parameter)


        return page(title=title,
                    metaheaderadd=profile_page.get_head().encode('utf-8'),
                    body=body.encode('utf-8'),
                    req=req,
                    language=ln,
                    show_title_p=False)

    def merge_profiles(self, req, form):
        '''
        begginig of the proccess that performs the merge over multipe person profiles

        @param req: Apache Request Object
        @type form: dict

        @return: a full page formatted in HTML
        @rtype: string
        '''
        argd = wash_urlargd(form, {'ln': (str, CFG_SITE_LANG),
                                   'primary_profile': (str, None),
                                   'search_param': (str, ''),
                                   'selection': (list, None),
                                   'verbose': (int, 0)})

        ln = argd['ln']
        primary_cname = argd['primary_profile']
        search_param = argd['search_param']
        selection = argd['selection']
        debug = 'verbose' in argd and argd['verbose'] > 0

        webapi.session_bareinit(req)
        session = get_session(req)
        pinfo = session['personinfo']
        profiles_to_merge = pinfo['merge_profiles']
        _ = gettext_set_language(ln)

        if not primary_cname:
            return page_not_authorized(req, text=_('This page is not accessible directly.'))

        no_access = self._page_access_permission_wall(req)
        if no_access:
            return no_access

        if selection is not None:
            profiles_to_merge_session = [cname for cname, is_available in profiles_to_merge]

            for profile in selection:
                if profile not in profiles_to_merge_session:
                    pid = webapi.get_person_id_from_canonical_id(profile)
                    is_available = webapi.is_profile_available(pid)
                    pinfo['merge_profiles'].append([profile, '1' if is_available else '0'])

            session.dirty = True

        primary_pid = webapi.get_person_id_from_canonical_id(primary_cname)
        is_available = webapi.is_profile_available(primary_pid)

        body = ''

        cname = ''
        is_owner = False
        last_visited_pid = webapi.history_get_last_visited_pid(session['personinfo']['visit_diary'])
        if last_visited_pid is not None:
            cname = webapi.get_canonical_id_from_person_id(last_visited_pid)
            is_owner = self._is_profile_owner(last_visited_pid)

        title = 'Merge Profiles'
        menu = WebProfileMenu(str(cname), "manage_profile", ln, is_owner, self._is_admin(pinfo))
        merge_page = WebProfilePage("merge_profile", title, no_cache=True)
        merge_page.add_profile_menu(menu)

        if debug:
            merge_page.add_debug_info(pinfo)

        # display status for any previously attempted merge
        if pinfo['merge_info_message']:
            teaser_key, message = pinfo['merge_info_message']
            body += TEMPLATE.tmpl_merge_transaction_box(teaser_key, [message])
            pinfo['merge_info_message'] = None

            session.dirty = True

        body += TEMPLATE.tmpl_merge_ticket_box('person_search', 'merge_profiles', primary_cname)

        shown_element_functions = dict()
        shown_element_functions['show_search_bar'] = TEMPLATE.tmpl_merge_profiles_search_bar(primary_cname)
        shown_element_functions['button_gen'] = TEMPLATE.merge_profiles_button_generator()
        shown_element_functions['pass_status'] = 'True'

        merge_page.add_bootstrapped_data(json.dumps({
            "other": "var gMergeProfile = %s; var gMergeList = %s;" % ([primary_cname, '1' if is_available else '0'], profiles_to_merge)
        }))

        body += self.search_box(search_param, shown_element_functions)
        body = merge_page.get_wrapped_body(body)

        return page(title=title,
                    metaheaderadd=merge_page.get_head().encode('utf-8'),
                    body=body.encode('utf-8'),
                    req=req,
                    language=ln,
                    show_title_p=False)

    def _perform_search(self, search_param):
        '''
        calls the search function on the search_param and returns the results

        @param search_param: query string
        @type search_param: String


        @return: list of pids that the search found they match with the search query
        @return: list

        '''
        pid_canditates_list = []
        nquery = None
        if search_param:
            if search_param.count(":"):
                try:
                    left, right = search_param.split(":")
                    try:
                        nsearch_param = str(right)
                    except (ValueError, TypeError):
                        try:
                            nsearch_param = str(left)
                        except (ValueError, TypeError):
                            nsearch_param = search_param
                except ValueError:
                    nsearch_param = search_param
            else:
                nsearch_param = search_param

            sorted_results = webapi.search_person_ids_by_name(nsearch_param)

            for result in sorted_results:
                pid_canditates_list.append(result[0])
        return pid_canditates_list

    def merge_profiles_ajax(self, req, form):
        '''
        Function used for handling Ajax requests used in order to add/remove profiles
        in/from the merging profiles list, which is saved in the session.

        @param req: Apache Request Object
        @type req: Apache Request Object
        @param form: Parameters sent via Ajax request
        @type form: dict

        @return: json data
        '''
        # Abort if the simplejson module isn't available
        if not CFG_JSON_AVAILABLE:
            print "Json not configurable"

        # If it is an Ajax request, extract any JSON data.
        ajax_request = False
        # REcent papers request
        if form.has_key('jsondata'):
            json_data = json.loads(str(form['jsondata']))
            # Deunicode all strings (Invenio doesn't have unicode
            # support).
            json_data = json_unicode_to_utf8(json_data)
            ajax_request = True
            json_response = {'resultCode': 0}

        # Handle request.
        if ajax_request:
            req_type = json_data['requestType']
            if req_type == 'addProfile':
                if json_data.has_key('profile'):
                    profile = json_data['profile']
                    person_id = webapi.get_person_id_from_canonical_id(profile)
                    if person_id != -1:
                        webapi.session_bareinit(req)
                        session = get_session(req)
                        profiles_to_merge = session["personinfo"]["merge_profiles"]
                        profile_availability = webapi.is_profile_available(person_id)
                        if profile_availability:
                            profile_availability = "1"
                        else:
                            profile_availability = "0"
                        if profile not in [el[0] for el in profiles_to_merge]:
                            profiles_to_merge.append([profile, profile_availability])
                            session.dirty = True
                            # TODO check access rights and get profile from db
                            json_response.update({'resultCode': 1})
                            json_response.update({'addedPofile': profile})
                            json_response.update({'addedPofileAvailability': profile_availability})
                        else:
                            json_response.update({'result': 'Error: Profile does not exist'})
                    else:
                        json_response.update({'result': 'Error: Profile was already in the list'})
                else:
                    json_response.update({'result': 'Error: Missing profile'})
            elif req_type == 'removeProfile':
                if json_data.has_key('profile'):
                    profile = json_data['profile']
                    if webapi.get_person_id_from_canonical_id(profile) != -1:
                        webapi.session_bareinit(req)
                        session = get_session(req)
                        profiles_to_merge = session["personinfo"]["merge_profiles"]
                        # print (str(profiles_to_merge))
                        if profile in [el[0] for el in profiles_to_merge]:
                            for prof in list(profiles_to_merge):
                                if prof[0] == profile:
                                    profiles_to_merge.remove(prof)
                            session.dirty = True
                            # TODO check access rights and get profile from db
                            json_response.update({'resultCode': 1})
                            json_response.update({'removedProfile': profile})
                        else:
                            json_response.update({'result': 'Error: Profile was missing already from the list'})
                    else:
                        json_response.update({'result': 'Error: Profile does not exist'})
                else:
                    json_response.update({'result': 'Error: Missing profile'})
            elif req_type == 'setPrimaryProfile':
                if json_data.has_key('profile'):
                    profile = json_data['profile']
                    profile_id = webapi.get_person_id_from_canonical_id(profile)
                    if profile_id != -1:
                        webapi.session_bareinit(req)
                        session = get_session(req)
                        profile_availability = webapi.is_profile_available(profile_id)
                        if profile_availability:
                            profile_availability = "1"
                        else:
                            profile_availability = "0"
                        profiles_to_merge = session["personinfo"]["merge_profiles"]
                        if profile in [el[0] for el in profiles_to_merge if el and el[0]]:
                            for prof in list(profiles_to_merge):
                                if prof[0] == profile:
                                    profiles_to_merge.remove(prof)
                        primary_profile = session["personinfo"]["merge_primary_profile"]
                        if primary_profile not in profiles_to_merge:
                            profiles_to_merge.append(primary_profile)
                        session["personinfo"]["merge_primary_profile"] = [profile, profile_availability]
                        session.dirty = True
                        json_response.update({'resultCode': 1})
                        json_response.update({'primaryProfile': profile})
                        json_response.update({'primaryPofileAvailability': profile_availability})
                    else:
                        json_response.update({'result': 'Error: Profile was already in the list'})
                else:
                    json_response.update({'result': 'Error: Missing profile'})
            else:
                json_response.update({'result': 'Error: Wrong request type'})
            return json.dumps(json_response)

    def search_box_ajax(self, req, form):
        '''
        Function used for handling Ajax requests used in the search box.

        @param req: Apache Request Object
        @type req: Apache Request Object
        @param form: Parameters sent via Ajax request
        @type form: dict

        @return: json data
        '''
        # Abort if the simplejson module isn't available
        if not CFG_JSON_AVAILABLE:
            print "Json not configurable"

        # If it is an Ajax request, extract any JSON data.
        ajax_request = False
        # REcent papers request
        if form.has_key('jsondata'):
            json_data = json.loads(str(form['jsondata']))
            # Deunicode all strings (Invenio doesn't have unicode
            # support).
            json_data = json_unicode_to_utf8(json_data)
            ajax_request = True
            json_response = {'resultCode': 0}

        # Handle request.
        if ajax_request:
            req_type = json_data['requestType']
            if req_type == 'getPapers':
                if json_data.has_key('personId'):
                    pId = json_data['personId']
                    papers = sorted([[p[0]] for p in webapi.get_papers_by_person_id(int(pId), -1)],
                                          key=itemgetter(0))
                    papers_html = TEMPLATE.tmpl_gen_papers(papers[0:MAX_NUM_SHOW_PAPERS])
                    json_response.update({'result': "\n".join(papers_html)})
                    json_response.update({'totalPapers': len(papers)})
                    json_response.update({'resultCode': 1})
                    json_response.update({'pid': str(pId)})
                else:
                    json_response.update({'result': 'Error: Missing person id'})
            elif req_type == 'getNames':
                if json_data.has_key('personId'):
                    pId = json_data['personId']
                    names = webapi.get_person_names_from_id(int(pId))
                    names_html = TEMPLATE.tmpl_gen_names(names)
                    json_response.update({'result': "\n".join(names_html)})
                    json_response.update({'resultCode': 1})
                    json_response.update({'pid': str(pId)})
            elif req_type == 'getIDs':
                if json_data.has_key('personId'):
                    pId = json_data['personId']
                    ids = webapi.get_external_ids_from_person_id(int(pId))
                    ids_html = TEMPLATE.tmpl_gen_ext_ids(ids)
                    json_response.update({'result': "\n".join(ids_html)})
                    json_response.update({'resultCode': 1})
                    json_response.update({'pid': str(pId)})
            elif req_type == 'isProfileClaimed':
                if json_data.has_key('personId'):
                    pId = json_data['personId']
                    isClaimed = webapi.get_uid_from_personid(pId)
                    if isClaimed != -1:
                        json_response.update({'resultCode': 1})
                    json_response.update({'pid': str(pId)})
            else:
                json_response.update({'result': 'Error: Wrong request type'})
            return json.dumps(json_response)


    def choose_profile(self, req, form):
        '''
        Generate SSO landing/choose_profile page

        @param req: Apache request object
        @type req: Apache request object
        @param form: GET/POST request params
        @type form: dict
        '''
        argd = wash_urlargd(form, {'ln': (str, CFG_SITE_LANG),
                                   'search_param': (str, None),
                                   'failed': (str, None),
                                   'verbose': (int, 0)})
        ln = argd['ln']

        debug = "verbose" in argd and argd["verbose"] > 0

        req.argd = argd   # needed for perform_req_search
        search_param = argd['search_param']

        webapi.session_bareinit(req)
        session = get_session(req)
        uid = getUid(req)
        pinfo = session['personinfo']

        failed = True
        if not argd['failed']:
            failed = False

        _ = gettext_set_language(ln)

        if not CFG_INSPIRE_SITE:
            return page_not_authorized(req, text=_("This page is not accessible directly."))

        params = WebInterfaceBibAuthorIDClaimPages.get_params_to_check_login_info(session)
        login_info = webapi.get_login_info(uid, params)

        if 'arXiv' not in login_info['logged_in_to_remote_systems']:
            return page_not_authorized(req, text=_("This page is not accessible directly."))

        pid = webapi.get_user_pid(login_info['uid'])

        # Create Wrapper Page Markup
        is_owner = False
        menu = WebProfileMenu('', "choose_profile", ln, is_owner, self._is_admin(pinfo))
        choose_page = WebProfilePage("choose_profile", "Choose your profile", no_cache=True)
        choose_page.add_profile_menu(menu)

        if debug:
            choose_page.add_debug_info(pinfo)

        content = TEMPLATE.tmpl_choose_profile(failed)
        body = choose_page.get_wrapped_body(content)

        #In any case, when we step by here, an autoclaim should be performed right after!
        pinfo = session["personinfo"]
        pinfo['should_check_to_autoclaim'] = True
        session.dirty = True

        last_visited_pid = webapi.history_get_last_visited_pid(session['personinfo']['visit_diary'])

        # if already logged in then redirect the user to the page he was viewing
        if pid != -1:
            redirect_pid = pid
            if last_visited_pid:
                redirect_pid = last_visited_pid
            redirect_to_url(req, '%s/author/manage_profile/%s' % (CFG_SITE_URL, str(redirect_pid)))
        else:
            # get name strings and email addresses from SSO/Oauth logins: {'system':{'name':[variant1,...,variantn], 'email':'blabla@bla.bla', 'pants_size':20}}
            remote_login_systems_info = webapi.get_remote_login_systems_info(req, login_info['logged_in_to_remote_systems'])
            # get union of recids that are associated to the ids from all the external systems: set(inspire_recids_list)
            recids = webapi.get_remote_login_systems_recids(req, login_info['logged_in_to_remote_systems'])
            # this is the profile with the biggest intersection of papers  so it's more probable that this is the profile the user seeks
            probable_pid = webapi.match_profile(req, recids, remote_login_systems_info)

#            if not search_param and probable_pid > -1 and probable_pid == last_visited_pid:
#                # try to assign the user to the profile he chose. If for some reason the profile is not available we assign him to an empty profile
#                redirect_pid, profile_claimed = webapi.claim_profile(login_info['uid'], probable_pid)
#                if profile_claimed:
#                    redirect_to_url(req, '%s/author/claim/action?associate_profile=True&redirect_pid=%s' % (CFG_SITE_URL, str(redirect_pid)))

            probable_profile_suggestion_info = None
            last_viewed_profile_suggestion_info = None

            if last_visited_pid > -1 and webapi.is_profile_available(last_visited_pid):
                # get information about the most probable profile and show it to the user
                last_viewed_profile_suggestion_info = webapi.get_profile_suggestion_info(req, last_visited_pid, recids)

            if probable_pid > -1 and webapi.is_profile_available(probable_pid):
                # get information about the most probable profile and show it to the user
                probable_profile_suggestion_info = webapi.get_profile_suggestion_info(req, probable_pid, recids )

            if not search_param:
                # we prefil the search with most relevant among the names that we get from external systems
                name_variants = webapi.get_name_variants_list_from_remote_systems_names(remote_login_systems_info)
                search_param = most_relevant_name(name_variants)

            body = body + TEMPLATE.tmpl_probable_profile_suggestion(probable_profile_suggestion_info, last_viewed_profile_suggestion_info, search_param)

            shown_element_functions = dict()
            shown_element_functions['button_gen'] = TEMPLATE.tmpl_choose_profile_search_button_generator()
            shown_element_functions['new_person_gen'] = TEMPLATE.tmpl_choose_profile_search_new_person_generator()
            shown_element_functions['show_search_bar'] = TEMPLATE.tmpl_choose_profile_search_bar()
            # show in the templates the column status (if profile is bound to a user or not)
            shown_element_functions['show_status'] = True
            # pass in the templates the data of the column status (if profile is bound to a user or not)
            # we might need the data without having to show them in the columne (fi merge_profiles
            shown_element_functions['pass_status'] = True
            # show search results to the user
            body = body + self.search_box(search_param, shown_element_functions)
            body = body + TEMPLATE.tmpl_choose_profile_footer()

            title = _(' ')
            return page(title=title,
                        metaheaderadd=choose_page.get_head().encode('utf-8'),
                        body=body,
                        req=req,
                        language=ln)

    @staticmethod
    def _arxiv_box(req, login_info, person_id, user_pid):
        '''
        Proccess and collect data for arXiv box

        @param req: Apache request object
        @type req: Apache request object

        @param login_info: status of login in the following format: {'logged_in': True, 'uid': 2, 'logged_in_to_remote_systems':['Arxiv', ...]}
        @type login_info: dict

        @param login_info: person id of the current page's profile
        @type login_info: int

        @param login_info: person id of the user
        @type login_info: int

        @return: data required to built the arXiv box
        @rtype: dict
        '''
        session = get_session(req)
        pinfo = session["personinfo"]
        arxiv_data = dict()

        arxiv_data['view_own_profile'] = person_id == user_pid

        # if the user is not a guest and he is connected through arXiv
        arxiv_data['login'] = login_info['logged_in']

        arxiv_data['user_pid'] = user_pid
        arxiv_data['user_has_pid'] = user_pid != -1

        # if the profile the use is logged in is the same with the profile of the page that the user views

        arxiv_data['view_own_profile'] = user_pid == person_id

        return arxiv_data

    @staticmethod
    def _orcid_box(arxiv_logged_in, person_id, user_pid, ulevel):
        '''
        Proccess and collect data for orcid box

        @param req: Apache request object
        @type req: Apache request object

        @param arxiv_logged_in: shows if the user is logged in through arXiv or not
        @type arxiv_logged_in: boolean

        @param person_id: person id of the current page's profile
        @type person_id: int

        @param user_pid: person id of the user
        @type user_pid: int

        @param ulevel: user's level
        @type ulevel: string

        @return: data required to built the orcid box
        @rtype: dict
        '''
        orcid_data = dict()
        orcid_data['arxiv_login'] = arxiv_logged_in
        orcid_data['orcids'] = None
        orcid_data['add_power'] = False
        orcid_data['own_profile'] = False
        orcid_data['pid'] = person_id
        # if the profile the use is logged in is the same with the profile of the page that the user views
        if person_id == user_pid:
            orcid_data['own_profile'] = True

        # if the user is an admin then he can add an existing orcid to the profile
        if ulevel == "admin":
            orcid_data['add_power'] = True

        orcids = webapi.get_orcids_by_pid(person_id)

        if orcids:
            orcid_data['orcids'] = orcids

        return orcid_data

    @staticmethod
    def _autoclaim_papers_box(req, person_id, user_pid, remote_logged_in_systems):
        '''
        Proccess and collect data for orcid box

        @param req: Apache request object
        @type req: Apache request object

        @param person_id: person id of the current page's profile
        @type person_id: int

        @param user_pid: person id of the user
        @type user_pid: int

        @param remote_logged_in_systems: the remote logged in systems
        @type remote_logged_in_systems: list

        @return: data required to built the autoclaim box
        @rtype: dict
        '''
        autoclaim_data = dict()
        # if no autoclaim should occur or had occured and results should be shown then the box should remain hidden
        autoclaim_data['hidden'] = True
        autoclaim_data['person_id'] = person_id

        # if the profile the use is logged in is the same with the profile of the page that the user views
        if person_id == user_pid:
            recids_to_autoclaim = webapi.get_remote_login_systems_recids(req, remote_logged_in_systems)
            autoclaim_data['hidden'] = False
            autoclaim_data['num_of_claims'] = len(recids_to_autoclaim)

        return autoclaim_data


############################################
#        New autoclaim functions           #
############################################

    def generate_autoclaim_data(self, req, form):
        # Abort if the simplejson module isn't available
        assert CFG_JSON_AVAILABLE, "Json not available"
        # Fail if no json data exists in the Ajax request
        if not form.has_key('jsondata'):
            return self._fail(req, apache.HTTP_NOT_FOUND)

        json_data = json.loads(str(form['jsondata']))
        json_data = json_unicode_to_utf8(json_data)

        try:
            pid = int(json_data['personId'])
        except:
            raise NotImplementedError("Some error with the parameter from the Ajax request occured.")

        webapi.session_bareinit(req)
        session = get_session(req)
        pinfo = session['personinfo']

        # If autoclaim was done already and no new remote systems exist
        # in order to autoclaim new papers send the cached result
        if not pinfo['orcid']['import_pubs'] and pinfo['autoclaim']['res'] is not None:
            autoclaim_data = pinfo['autoclaim']['res']
            json_response = {'resultCode': 1, 'result': TEMPLATE.tmpl_autoclaim_box(autoclaim_data, CFG_SITE_LANG, add_box=False, loading=False)}
            return json.dumps(json_response)

        external_pubs_association = pinfo['autoclaim']['external_pubs_association']
        autoclaim_ticket = pinfo['autoclaim']['ticket']
        ulevel = pinfo['ulevel']
        uid = getUid(req)

        params = WebInterfaceBibAuthorIDClaimPages.get_params_to_check_login_info(session)
        login_status = webapi.get_login_info(uid, params)
        remote_systems = login_status['logged_in_to_remote_systems']

        papers_to_autoclaim = set(webapi.get_papers_from_remote_systems(remote_systems, params, external_pubs_association))
        already_claimed_recids = set([rec for _, _, rec in get_claimed_papers_of_author(pid)]) & papers_to_autoclaim
        papers_to_autoclaim = papers_to_autoclaim - set([rec for _, _, rec in get_claimed_papers_of_author(pid)])

        for paper in papers_to_autoclaim:
            operation_parts = {'pid': pid,
                               'action': 'assign',
                               'bibrefrec': str(paper)}

            operation_to_be_added = webapi.construct_operation(operation_parts, pinfo, uid)

            if operation_to_be_added is None:
                # In case the operation could not be created (because of an
                # erroneous bibrefrec) ignore it and continue with the rest
                continue

            webapi.add_operation_to_ticket(operation_to_be_added, autoclaim_ticket)

        additional_info = {'first_name': '', 'last_name': '', 'email': '',
                           'comments': 'Assigned automatically when autoclaim was triggered.'}
        userinfo = webapi.fill_out_userinfo(additional_info, uid, req.remote_ip, ulevel, strict_check=False)

        webapi.commit_operations_from_ticket(autoclaim_ticket, userinfo, uid, ulevel)
        autoclaim_data = dict()
        autoclaim_data['hidden'] = False
        autoclaim_data['person_id'] = pid
        autoclaim_data['successfull_recids'] = set([op['rec'] for op in webapi.get_ticket_status(autoclaim_ticket) if 'execution_result' in op]) | already_claimed_recids
        webapi.clean_ticket(autoclaim_ticket)
        autoclaim_data['unsuccessfull_recids'] = [op['rec'] for op in webapi.get_ticket_status(autoclaim_ticket)]
        autoclaim_data['num_of_unsuccessfull_recids'] = len(autoclaim_data['unsuccessfull_recids'])
        autoclaim_data['recids_to_external_ids'] = dict()
        for key, value in external_pubs_association.iteritems():
            ext_system, ext_id = key
            rec = value
            title = get_title_of_paper(rec)
            autoclaim_data['recids_to_external_ids'][rec] = title

        # cache the result in the session
        pinfo['autoclaim']['res'] = autoclaim_data
        if pinfo['orcid']['import_pubs']:
            pinfo['orcid']['import_pubs'] = False
        session.dirty = True

        json_response = {'resultCode': 1, 'result': TEMPLATE.tmpl_autoclaim_box(autoclaim_data, CFG_SITE_LANG, add_box=False, loading=False)}
        req.write(json.dumps(json_response))


    @staticmethod
    def get_params_to_check_login_info(session):

        def get_params_to_check_login_info_of_arxiv(session):
            try:
                return session['user_info']
            except KeyError:
                return None

        def get_params_to_check_login_info_of_orcid(session):
            pinfo = session['personinfo']

            try:
                pinfo['orcid']['has_orcid_id'] = bool(get_orcid_id_of_author(pinfo['pid'])[0][0] and pinfo['orcid']['import_pubs'])
            except:
                pinfo['orcid']['has_orcid_id'] = False

            session.dirty = True

            return pinfo['orcid']

        get_params_for_remote_system = {'arXiv': get_params_to_check_login_info_of_arxiv,
                                        'orcid': get_params_to_check_login_info_of_orcid}

        params = dict()
        for system, get_params in get_params_for_remote_system.iteritems():
            params[system] = get_params(session)

        return params


    @staticmethod
    def _claim_paper_box(person_id):
        '''
        Proccess and collect data for claim paper box

        @param person_id: person id of the current page's profile
        @type person_id: int

        @return: data required to built the claim paper box
        @rtype: dict
        '''
        claim_paper_data = dict()
        claim_paper_data['canonical_id'] = str(webapi.get_canonical_id_from_person_id(person_id))
        return claim_paper_data

    @staticmethod
    def _support_box():
        '''
        Proccess and collect data for support box

        @return: data required to built the support box
        @rtype: dict
        '''
        support_data = dict()
        return support_data

    @staticmethod
    def _merge_box(person_id):
        '''
        Proccess and collect data for merge box

        @param person_id: person id of the current page's profile
        @type person_id: int

        @return: data required to built the merge box
        @rtype: dict
        '''
        merge_data = dict()
        search_param = webapi.get_canonical_id_from_person_id(person_id)
        name_variants = [element[0] for element in webapi.get_person_names_from_id(person_id)]
        relevant_name = most_relevant_name(name_variants)

        if relevant_name:
            search_param = relevant_name.split(",")[0]

        merge_data['search_param'] = search_param
        merge_data['canonical_id'] = webapi.get_canonical_id_from_person_id(person_id)
        return merge_data

    @staticmethod
    def _internal_ids_box(person_id, user_pid, ulevel):
        '''
        Proccess and collect data for external_ids box

        @param person_id: person id of the current page's profile
        @type person_id: int

        @param user_pid: person id of the user
        @type user_pid: int

        @param remote_logged_in_systems: the remote logged in systems
        @type remote_logged_in_systems: list

        @return: data required to built the external_ids box
        @rtype: dict
        '''
        external_ids_data = dict()
        external_ids_data['uid'],external_ids_data['old_uids'] = webapi.get_internal_user_id_from_person_id(person_id)
        external_ids_data['person_id'] = person_id
        external_ids_data['user_pid'] = user_pid
        external_ids_data['ulevel'] = ulevel

        return external_ids_data

    @staticmethod
    def _external_ids_box(person_id, user_pid, ulevel):
        '''
        Proccess and collect data for external_ids box

        @param person_id: person id of the current page's profile
        @type person_id: int

        @param user_pid: person id of the user
        @type user_pid: int

        @param remote_logged_in_systems: the remote logged in systems
        @type remote_logged_in_systems: list

        @return: data required to built the external_ids box
        @rtype: dict
        '''
        internal_ids_data = dict()
        internal_ids_data['ext_ids'] = webapi.get_external_ids_from_person_id(person_id)
        internal_ids_data['person_id'] = person_id
        internal_ids_data['user_pid'] = user_pid
        internal_ids_data['ulevel'] = ulevel

        return internal_ids_data

    @staticmethod
    def _hepnames_box(person_id):
        return webapi.get_hepnames(person_id)

    def tickets_admin(self, req, form):
        '''
        Generate SSO landing/welcome page

        @param req: Apache request object
        @type req: Apache request object
        @param form: GET/POST request params
        @type form: dict
        '''
        argd = wash_urlargd(form, {'ln': (str, CFG_SITE_LANG)})
        ln = argd['ln']

        webapi.session_bareinit(req)
        no_access = self._page_access_permission_wall(req, req_level='admin')
        if no_access:
            return no_access

        session = get_session(req)
        pinfo = session['personinfo']

        cname = ''
        is_owner = False
        last_visited_pid = webapi.history_get_last_visited_pid(pinfo['visit_diary'])
        if last_visited_pid is not None:
            cname = webapi.get_canonical_id_from_person_id(last_visited_pid)
            is_owner = self._is_profile_owner(last_visited_pid)

        menu = WebProfileMenu(str(cname), "open_tickets", ln, is_owner, self._is_admin(pinfo))

        title = "Open RT tickets"
        profile_page = WebProfilePage("help", title, no_cache=True)
        profile_page.add_profile_menu(menu)

        tickets = webapi.get_persons_with_open_tickets_list()
        tickets = list(tickets)

        for t in list(tickets):
            tickets.remove(t)
            tickets.append([webapi.get_most_frequent_name_from_pid(int(t[0])),
                         webapi.get_person_redirect_link(t[0]), t[0], t[1]])

        content = TEMPLATE.tmpl_tickets_admin(tickets)
        content = TEMPLATE.tmpl_person_detail_layout(content)

        body = profile_page.get_wrapped_body(content)

        return page(title=title,
                    metaheaderadd=profile_page.get_head().encode('utf-8'),
                    body=body.encode('utf-8'),
                    req=req,
                    language=ln,
                    show_title_p=False)

    def help(self, req, form):
        argd = wash_urlargd(form, {'ln': (str, CFG_SITE_LANG)})
        ln = argd['ln']
        _ = gettext_set_language(ln)

        if not CFG_INSPIRE_SITE:
            return page_not_authorized(req, text=_("This page is not accessible directly."))

        webapi.session_bareinit(req)
        session = get_session(req)
        pinfo = session['personinfo']

        cname = ''
        is_owner = False
        last_visited_pid = webapi.history_get_last_visited_pid(pinfo['visit_diary'])
        if last_visited_pid is not None:
            cname = webapi.get_canonical_id_from_person_id(last_visited_pid)
            is_owner = self._is_profile_owner(last_visited_pid)

        menu = WebProfileMenu(str(cname), "help", ln, is_owner, self._is_admin(pinfo))

        title = "Help page"
        profile_page = WebProfilePage("help", title, no_cache=True)
        profile_page.add_profile_menu(menu)

        content = TEMPLATE.tmpl_help_page()

        body = profile_page.get_wrapped_body(content)

        return page(title=title,
                    metaheaderadd=profile_page.get_head().encode('utf-8'),
                    body=body.encode('utf-8'),
                    req=req,
                    language=ln,
                    show_title_p=False)


    def export(self, req, form):
        '''
        Generate JSONized export of Person data

        @param req: Apache request object
        @type req: Apache request object
        @param form: GET/POST request params
        @type form: dict
        '''
        argd = wash_urlargd(
            form,
            {'ln': (str, CFG_SITE_LANG),
             'request': (str, None),
             'userid': (str, None)})

        if not CFG_JSON_AVAILABLE:
            return "500_json_not_found__install_package"

        # session = get_session(req)
        request = None
        userid = None

        if "userid" in argd and argd['userid']:
            userid = argd['userid']
        else:
            return "404_user_not_found"

        if "request" in argd and argd['request']:
            request = argd["request"]

        # find user from ID
        user_email = get_email_from_username(userid)

        if user_email == userid:
            return "404_user_not_found"

        uid = get_uid_from_email(user_email)
        uinfo = collect_user_info(uid)
        # find person by uid
        pid = webapi.get_pid_from_uid(uid)
        # find papers py pid that are confirmed through a human.
        papers = webapi.get_papers_by_person_id(pid, 2)
        # filter by request param, e.g. arxiv
        if not request:
            return "404__no_filter_selected"

        if not request in VALID_EXPORT_FILTERS:
            return "500_filter_invalid"

        if request == "arxiv":
            query = "(recid:"
            query += " OR recid:".join(papers)
            query += ") AND 037:arxiv"
            db_docs = perform_request_search(p=query, rg=0)
            nickmail = ""
            nickname = ""
            db_arxiv_ids = []

            try:
                nickname = uinfo["nickname"]
            except KeyError:
                pass

            if not nickname:
                try:
                    nickmail = uinfo["email"]
                except KeyError:
                    nickmail = user_email

                nickname = nickmail

            db_arxiv_ids = get_fieldvalues(db_docs, "037__a")
            construct = {"nickname": nickname,
                         "claims": ";".join(db_arxiv_ids)}

            jsondmp = json.dumps(construct)

            signature = webapi.sign_assertion("arXiv", jsondmp)
            construct["digest"] = signature

            return json.dumps(construct)


    index = __call__


class WebInterfaceBibAuthorIDManageProfilePages(WebInterfaceDirectory):
    _exports = ['',
                'import_orcid_pubs',
                'connect_author_with_hepname',
                'connect_author_with_hepname_ajax',
                'suggest_orcid',
                'suggest_orcid_ajax']

    def _lookup(self, component, path):
        '''
        This handler parses dynamic URLs:
            - /author/profile/1332 shows the page of author with id: 1332
            - /author/profile/100:5522,1431 shows the page of the author
              identified by the bibrefrec: '100:5522,1431'
        '''
        if not component in self._exports:
            return WebInterfaceBibAuthorIDManageProfilePages(component), path

    def _is_profile_owner(self, pid):
        return self.person_id == int(pid)

    def _is_admin(self, pinfo):
        return pinfo['ulevel'] == 'admin'

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

        if identifier is None or not isinstance(identifier, str):
            self.original_identifier = " "
            return

        self.original_identifier = identifier
        # check if it's a canonical id: e.g. "J.R.Ellis.1"

        try:
            pid = int(identifier)
        except ValueError:
            pid = int(webapi.get_person_id_from_canonical_id(identifier))

        if pid >= 0:
            self.person_id = pid
            return

        # check if it's an author id: e.g. "14"
        try:
            pid = int(identifier)
            if webapi.author_has_papers(pid):
                self.person_id = pid
                return
        except ValueError:
            pass

        # check if it's a bibrefrec: e.g. "100:1442,155"
        if webapi.is_valid_bibref(identifier):
            pid = int(webapi.get_person_id_from_paper(identifier))
            if pid >= 0:
                self.person_id = pid
                return

    def __call__(self, req, form):
        '''
            Generate SSO landing/author management page

            @param req: Apache request object
            @type req: Apache request object
            @param form: GET/POST request params
            @type form: dict
        '''
        webapi.session_bareinit(req)
        session = get_session(req)

        pinfo = session['personinfo']
        ulevel = pinfo['ulevel']
        person_id = self.person_id
        uid = getUid(req)

        pinfo['claim_in_process'] = True

        argd = wash_urlargd(form, {
            'ln': (str, CFG_SITE_LANG),
            'verbose': (int, 0)})

        debug = "verbose" in argd and argd["verbose"] > 0

        ln = argd['ln']
        _ = gettext_set_language(ln)

        if not CFG_INSPIRE_SITE or self.person_id is None:
            return page_not_authorized(req, text=_("This page is not accessible directly."))

        if person_id < 0:
            return self._error_page(req, message=("Identifier %s is not a valid person identifier or does not exist anymore!" % self.original_identifier))

        # log the visit
        webapi.history_log_visit(req, 'manage_profile', pid=person_id)

        # store the arxiv papers the user owns
        if uid > 0 and not pinfo['arxiv_status']:
            uinfo = collect_user_info(req)
            arxiv_papers = list()

            if 'external_arxivids' in uinfo and uinfo['external_arxivids']:
                arxiv_papers = uinfo['external_arxivids'].split(';')

            if arxiv_papers:
                webapi.add_arxiv_papers_to_author(arxiv_papers, person_id)

            pinfo['arxiv_status'] = True

        params = WebInterfaceBibAuthorIDClaimPages.get_params_to_check_login_info(session)
        login_info = webapi.get_login_info(uid, params)

        title_message = _('Profile management')

        ssl_param = 0
        if req.is_https():
            ssl_param = 1


        # Create Wrapper Page Markup

        cname = webapi.get_canonical_id_from_person_id(self.person_id)
        if cname == self.person_id:
            return page_not_authorized(req, text=_("This page is not accessible directly."))

        menu = WebProfileMenu(cname, "manage_profile", ln, self._is_profile_owner(pinfo['pid']), self._is_admin(pinfo))
        profile_page = WebProfilePage("manage_profile", webapi.get_longest_name_from_pid(self.person_id), no_cache=True)
        profile_page.add_profile_menu(menu)

        gboxstatus = self.person_id
        gpid = self.person_id
        gNumOfWorkers = 3   # to do: read it from conf file
        gReqTimeout = 3000
        gPageTimeout = 12000

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

        user_pid = webapi.get_user_pid(login_info['uid'])
        person_data = webapi.get_person_info_by_pid(person_id)

        # proccess and collect data for every box [LEGACY]
        arxiv_data = WebInterfaceBibAuthorIDClaimPages._arxiv_box(req, login_info, person_id, user_pid)
        orcid_data = WebInterfaceBibAuthorIDClaimPages._orcid_box(arxiv_data['login'], person_id, user_pid, ulevel)
        claim_paper_data = WebInterfaceBibAuthorIDClaimPages._claim_paper_box(person_id)
        support_data = WebInterfaceBibAuthorIDClaimPages._support_box()
        ext_ids_data = None
        int_ids_data = None
        if ulevel == 'admin':
            ext_ids_data = WebInterfaceBibAuthorIDClaimPages._external_ids_box(person_id, user_pid, ulevel)
            int_ids_data = WebInterfaceBibAuthorIDClaimPages._internal_ids_box(person_id, user_pid, ulevel)
        autoclaim_data = WebInterfaceBibAuthorIDClaimPages._autoclaim_papers_box(req, person_id, user_pid, login_info['logged_in_to_remote_systems'])
        merge_data = WebInterfaceBibAuthorIDClaimPages._merge_box(person_id)
        hepnames_data = WebInterfaceBibAuthorIDClaimPages._hepnames_box(person_id)


        content = ''
        # display status for any previously attempted merge
        if pinfo['merge_info_message']:
            teaser_key, message = pinfo['merge_info_message']
            content += TEMPLATE.tmpl_merge_transaction_box(teaser_key, [message])
            pinfo['merge_info_message'] = None

            session.dirty = True

        content += TEMPLATE.tmpl_profile_management(ln, person_data, arxiv_data,
                                                    orcid_data, claim_paper_data,
                                                    int_ids_data, ext_ids_data,
                                                    autoclaim_data, support_data,
                                                    merge_data, hepnames_data)

        body = profile_page.get_wrapped_body(content)

        return page(title=title_message,
                    metaheaderadd=profile_page.get_head().encode('utf-8'),
                    body=body.encode('utf-8'),
                    req=req,
                    language=ln,
                    show_title_p=False)


    def import_orcid_pubs(self, req, form):
        webapi.session_bareinit(req)
        session = get_session(req)
        pinfo = session['personinfo']
        orcid_info = pinfo['orcid']

        # author should have already an orcid if this method was triggered
        orcid_id = get_orcid_id_of_author(pinfo['pid'])[0][0]
        orcid_dois = get_dois_from_orcid(orcid_id)
        # TODO: what to do in case some ORCID server error occurs?
        if orcid_dois is None:
            redirect_to_url(req, "%s/author/manage_profile/%s" % (CFG_SITE_SECURE_URL, pinfo['pid']))

        # TODO: it would be smarter if:
        # 1. we save in the db the orcid_dois
        # 2. to expire only the external pubs box in the profile page
        webauthorapi.expire_all_cache_for_personid(pinfo['pid'])

        orcid_info['imported_pubs'] = orcid_dois
        orcid_info['import_pubs'] = True
        session.dirty = True

        redirect_to_url(req, "%s/author/manage_profile/%s" % (CFG_SITE_SECURE_URL, pinfo['pid']))


    def connect_author_with_hepname(self, req, form):
        argd = wash_urlargd(form, {'cname':(str, None),
                                   'hepname': (str, None),
                                   'ln': (str, CFG_SITE_LANG)})
        ln = argd['ln']
        if argd['cname'] is not None:
            cname = argd['cname']
        else:
            return self._error_page(req, ln, "Fatal: cannot associate a hepname without a person id.")

        if argd['hepname'] is not None:
            hepname = argd['hepname']
        else:
            return self._error_page(req, ln, "Fatal: cannot associate an author with a non valid hepname.")

        webapi.connect_author_with_hepname(cname, hepname)
        webapi.session_bareinit(req)
        session = get_session(req)
        pinfo = session['personinfo']
        last_visited_page = webapi.history_get_last_visited_url(pinfo['visit_diary'], just_page=True)

        redirect_to_url(req, "%s/author/%s/%s" % (CFG_SITE_URL, last_visited_page, cname))


    def connect_author_with_hepname_ajax(self, req, form):
        '''
        Function used for handling Ajax requests.

        @param req: apache request object
        @type req: apache request object
        @param form: parameters sent via Ajax request
        @type form: dict

        @return:
        @rtype: json data
        '''
        # Abort if the simplejson module isn't available
        assert CFG_JSON_AVAILABLE, "Json not available"
        # Fail if no json data exists in the Ajax request
        if not form.has_key('jsondata'):
            return self._fail(req, apache.HTTP_NOT_FOUND)

        json_data = json.loads(str(form['jsondata']))
        json_data = json_unicode_to_utf8(json_data)

        try:
            cname = json_data['cname']
            hepname = json_data['hepname']
        except:
            return self._fail(req, apache.HTTP_NOT_FOUND)

        webapi.session_bareinit(req)
        session = get_session(req)
        pinfo = session['personinfo']
        if not self._is_admin(pinfo):
            webapi.connect_author_with_hepname(cname, hepname)
        else:
            uid = getUid(req)
            add_cname_to_hepname_record(cname, hepname, uid)


    def suggest_orcid(self, req, form):
        argd = wash_urlargd(form, {'orcid':(str, None),
                                   'pid': (int, -1),
                                   'ln': (str, CFG_SITE_LANG)})
        ln = argd['ln']
        if argd['pid'] > -1:
            pid = argd['pid']
        else:
            return self._error_page(req, ln, "Fatal: cannot associate an orcid without a person id.")

        if argd['orcid'] is not None and is_valid_orcid(argd['orcid']):
            orcid = argd['orcid']
        else:
            return self._error_page(req, ln, "Fatal: cannot associate an author with a non valid ORCiD.")

        webapi.connect_author_with_orcid(webapi.get_canonical_id_from_person_id(pid), orcid)
        redirect_to_url(req, "%s/author/manage_profile/%s" % (CFG_SITE_URL, pid))


    def suggest_orcid_ajax(self, req, form):
        '''
        Function used for handling Ajax requests.

        @param req: apache request object
        @type req: apache request object
        @param form: parameters sent via Ajax request
        @type form: dict

        @return:
        @rtype: json data
        '''
        # Abort if the simplejson module isn't available
        assert CFG_JSON_AVAILABLE, "Json not available"
        # Fail if no json data exists in the Ajax request
        if not form.has_key('jsondata'):
            return self._fail(req, apache.HTTP_NOT_FOUND)

        json_data = json.loads(str(form['jsondata']))
        json_data = json_unicode_to_utf8(json_data)

        try:
            orcid = json_data['orcid']
            pid = json_data['pid']
        except:
            return self._fail(req, apache.HTTP_NOT_FOUND)

        if not is_valid_orcid(orcid):
            return self._fail(req, apache.HTTP_NOT_FOUND)

        webapi.connect_author_with_orcid(webapi.get_canonical_id_from_person_id(pid), orcid)


    def _fail(self, req, code):
        req.status = code
        return

    def _error_page(self, req, ln=CFG_SITE_LANG, message=None, intro=True):
        '''
        Create a page that contains a message explaining the error.

        @param req: Apache Request Object
        @type req: Apache Request Object
        @param ln: language
        @type ln: string
        @param message: message to be displayed
        @type message: string
        '''
        body = []

        _ = gettext_set_language(ln)

        if not message:
            message = "No further explanation available. Sorry."

        if intro:
            body.append(_("<p>We're sorry. An error occurred while "
                        "handling your request. Please find more information "
                        "below:</p>"))
        body.append("<p><strong>%s</strong></p>" % message)

        return page(title=_("Notice"),
                body="\n".join(body),
                description="%s - Internal Error" % CFG_SITE_NAME,
                keywords="%s, Internal Error" % CFG_SITE_NAME,
                language=ln,
                req=req)


    index = __call__


class WebInterfaceAuthorTicketHandling(WebInterfaceDirectory):

    _exports = ['get_status',
                'update_status',
                'add_operation',
                'modify_operation',
                'remove_operation',
                'commit',
                'abort']

    @staticmethod
    def bootstrap_status(pinfo, on_ticket):
        '''
        Function used for generating get_status json bootstrapping.

        @param pinfo: person_info
        @type req: dict
        @param on_ticket: ticket target
        @type on_ticket: str

        @return:
        @rtype: json data
        '''
        # Abort if the simplejson module isn't available
        assert CFG_JSON_AVAILABLE, "Json not available"

        author_ticketing = WebInterfaceAuthorTicketHandling()

        ticket = author_ticketing._get_according_ticket(on_ticket, pinfo)
        if ticket is None:
            return "{}"

        ticket_status = webapi.get_ticket_status(ticket)

        return json.dumps(ticket_status)

    def get_status(self, req, form):
        '''
        Function used for handling Ajax requests.

        @param req: apache request object
        @type req: apache request object
        @param form: parameters sent via Ajax request
        @type form: dict

        @return:
        @rtype: json data
        '''
        # Abort if the simplejson module isn't available
        assert CFG_JSON_AVAILABLE, "Json not available"
        # Fail if no json data exists in the Ajax request
        if not form.has_key('jsondata'):
            return self._fail(req, apache.HTTP_NOT_FOUND)

        json_data = json.loads(str(form['jsondata']))
        json_data = json_unicode_to_utf8(json_data)

        try:
            on_ticket = json_data['on']
        except:
            return self._fail(req, apache.HTTP_NOT_FOUND)

        webapi.session_bareinit(req)
        session = get_session(req)
        pinfo = session['personinfo']

        ticket = self._get_according_ticket(on_ticket, pinfo)
        if ticket is None:
            return self._fail(req, apache.HTTP_NOT_FOUND)

        ticket_status = webapi.get_ticket_status(ticket)

        session.dirty = True

        req.content_type = 'application/json'
        req.write(json.dumps(ticket_status))


    def update_status(self, req, form):
        '''
        Function used for handling Ajax requests.

        @param req: apache request object
        @type req: apache request object
        @param form: parameters sent via Ajax request
        @type form: dict

        @return:
        @rtype: json data
        '''
        # Abort if the simplejson module isn't available
        assert CFG_JSON_AVAILABLE, "Json not available"
        # Fail if no json data exists in the Ajax request
        if not form.has_key('jsondata'):
            return self._fail(req, apache.HTTP_NOT_FOUND)

        json_data = json.loads(str(form['jsondata']))
        json_data = json_unicode_to_utf8(json_data)

        try:
            on_ticket = json_data['on']
        except:
            return self._fail(req, apache.HTTP_NOT_FOUND)

        webapi.session_bareinit(req)
        session = get_session(req)
        pinfo = session['personinfo']

        ticket = self._get_according_ticket(on_ticket, pinfo)
        if ticket is None:
            return self._fail(req, apache.HTTP_NOT_FOUND)

        webapi.update_ticket_status(ticket)

        session.dirty = True


    def add_operation(self, req, form):
        '''
        Function used for handling Ajax requests.

        @param req: apache request object
        @type req: apache request object
        @param form: parameters sent via Ajax request
        @type form: dict

        @return:
        @rtype: json data
        '''
        # Abort if the simplejson module isn't available
        assert CFG_JSON_AVAILABLE, "Json not available"
        # Fail if no json data exists in the Ajax request
        if not form.has_key('jsondata'):
            return self._fail(req, apache.HTTP_NOT_FOUND)

        json_data = json.loads(str(form['jsondata']))
        json_data = json_unicode_to_utf8(json_data)

        try:
            operation_parts = {'pid': int(json_data['pid']),
                               'action': json_data['action'],
                               'bibrefrec': json_data['bibrefrec']}
            on_ticket = json_data['on']
        except:
            return self._fail(req, apache.HTTP_NOT_FOUND)

        webapi.session_bareinit(req)
        session = get_session(req)
        pinfo = session['personinfo']
        uid = getUid(req)

        operation_to_be_added = webapi.construct_operation(operation_parts, pinfo, uid)
        if operation_to_be_added is None:
            return self._fail(req, apache.HTTP_NOT_FOUND)

        ticket = self._get_according_ticket(on_ticket, pinfo)
        if ticket is None:
            return self._fail(req, apache.HTTP_NOT_FOUND)

        webapi.add_operation_to_ticket(operation_to_be_added, ticket)

        session.dirty = True


    def modify_operation(self, req, form):
        '''
        Function used for handling Ajax requests.

        @param req: apache request object
        @type req: apache request object
        @param form: parameters sent via Ajax request
        @type form: dict

        @return:
        @rtype: json data
        '''
        # Abort if the simplejson module isn't available
        assert CFG_JSON_AVAILABLE, "Json not available"
        # Fail if no json data exists in the Ajax request
        if not form.has_key('jsondata'):
            return self._fail(req, apache.HTTP_NOT_FOUND)

        json_data = json.loads(str(form['jsondata']))
        json_data = json_unicode_to_utf8(json_data)

        try:
            operation_parts = {'pid': int(json_data['pid']),
                               'action': json_data['action'],
                               'bibrefrec': json_data['bibrefrec']}
            on_ticket = json_data['on']
        except:
            return self._fail(req, apache.HTTP_NOT_FOUND)

        webapi.session_bareinit(req)
        session = get_session(req)
        pinfo = session['personinfo']
        uid = getUid(req)

        operation_to_be_modified = webapi.construct_operation(operation_parts, pinfo, uid, should_have_bibref=False)
        if operation_to_be_modified is None:
            return self._fail(req, apache.HTTP_NOT_FOUND)

        ticket = self._get_according_ticket(on_ticket, pinfo)
        if ticket is None:
            return self._fail(req, apache.HTTP_NOT_FOUND)

        operation_is_modified = webapi.modify_operation_from_ticket(operation_to_be_modified, ticket)
        if not operation_is_modified:
            # Operation couldn't be modified because it doesn't exist in the
            # ticket. Wrong parameters were given hence we should fail!
            return self._fail(req, apache.HTTP_NOT_FOUND)

        session.dirty = True


    def remove_operation(self, req, form):
        '''
        Function used for handling Ajax requests.

        @param req: apache request object
        @type req: apache request object
        @param form: parameters sent via Ajax request
        @type form: dict

        @return:
        @rtype: json data
        '''
        # Abort if the simplejson module isn't available
        assert CFG_JSON_AVAILABLE, "Json not available"
        # Fail if no json data exists in the Ajax request
        if not form.has_key('jsondata'):
            return self._fail(req, apache.HTTP_NOT_FOUND)

        json_data = json.loads(str(form['jsondata']))
        json_data = json_unicode_to_utf8(json_data)

        try:
            operation_parts = {'pid': int(json_data['pid']),
                               'action': json_data['action'],
                               'bibrefrec': json_data['bibrefrec']}
            on_ticket = json_data['on']
        except:
            return self._fail(req, apache.HTTP_NOT_FOUND)

        webapi.session_bareinit(req)
        session = get_session(req)
        pinfo = session['personinfo']
        uid = getUid(req)

        operation_to_be_removed = webapi.construct_operation(operation_parts, pinfo, uid)
        if operation_to_be_removed is None:
            return self._fail(req, apache.HTTP_NOT_FOUND)

        ticket = self._get_according_ticket(on_ticket, pinfo)
        if ticket is None:
            return self._fail(req, apache.HTTP_NOT_FOUND)

        operation_is_removed = webapi.remove_operation_from_ticket(operation_to_be_removed, ticket)
        if not operation_is_removed:
            # Operation couldn't be removed because it doesn't exist in the
            # ticket. Wrong parameters were given hence we should fail!
            return self._fail(req, apache.HTTP_NOT_FOUND)

        session.dirty = True


    def commit(self, req, form):
        '''
        Function used for handling Ajax requests.

        @param req: apache request object
        @type req: apache request object
        @param form: parameters sent via Ajax request
        @type form: dict

        @return:
        @rtype: json data
        '''
        # Abort if the simplejson module isn't available
        assert CFG_JSON_AVAILABLE, "Json not available"
        # Fail if no json data exists in the Ajax request
        if not form.has_key('jsondata'):
            return self._fail(req, apache.HTTP_NOT_FOUND)

        json_data = json.loads(str(form['jsondata']))
        json_data = json_unicode_to_utf8(json_data)

        try:
            additional_info = {'first_name': json_data.get('first_name',"Default"),
                               'last_name': json_data.get('last_name',"Default"),
                               'email': json_data.get('email',"Default"),
                               'comments': json_data['comments']}
            on_ticket = json_data['on']
        except:
            return self._fail(req, apache.HTTP_NOT_FOUND)

        webapi.session_bareinit(req)
        session = get_session(req)
        pinfo = session['personinfo']
        ulevel = pinfo['ulevel']
        uid = getUid(req)

        user_is_guest = isGuestUser(uid)

        if not user_is_guest:
            try:
                additional_info['first_name'] = session['user_info']['external_firstname']
                additional_info['last_name'] = session['user_info']['external_familyname']
                additional_info['email'] = session['user_info']['email']
            except KeyError:
                additional_info['first_name'] = additional_info['last_name'] = additional_info['email'] = str(uid)

        ticket = self._get_according_ticket(on_ticket, pinfo)
        if ticket is None:
            return self._fail(req, apache.HTTP_NOT_FOUND)

        # When a guest is claiming we should not commit if he
        # doesn't provide us his full personal information
        strict_check = user_is_guest
        userinfo = webapi.fill_out_userinfo(additional_info, uid, req.remote_ip, ulevel, strict_check=strict_check)
        if userinfo is None:
            return self._fail(req, apache.HTTP_NOT_FOUND)

        webapi.commit_operations_from_ticket(ticket, userinfo, uid, ulevel)

        session.dirty = True


    def abort(self, req, form):
        '''
        Function used for handling Ajax requests.

        @param req: apache request object
        @type req: apache request object
        @param form: parameters sent via Ajax request
        @type form: dict

        @return:
        @rtype: json data
        '''
        # Abort if the simplejson module isn't available
        assert CFG_JSON_AVAILABLE, "Json not available"
        # Fail if no json data exists in the Ajax request
        if not form.has_key('jsondata'):
            return self._fail(req, apache.HTTP_NOT_FOUND)

        json_data = json.loads(str(form['jsondata']))
        json_data = json_unicode_to_utf8(json_data)

        try:
            on_ticket = json_data['on']
        except:
            return self._fail(req, apache.HTTP_NOT_FOUND)

        webapi.session_bareinit(req)
        session = get_session(req)
        pinfo = session['personinfo']

        ticket = self._get_according_ticket(on_ticket, pinfo)
        if ticket is None:
            return self._fail(req, apache.HTTP_NOT_FOUND)

        # When a user is claiming we should completely delete his ticket if he
        # aborts the claiming procedure
        delete_ticket = (on_ticket == 'user')
        webapi.abort_ticket(ticket, delete_ticket=delete_ticket)

        session.dirty = True


    def _get_according_ticket(self, on_ticket, pinfo):
        ticket = None
        if on_ticket == 'user':
            ticket = pinfo['ticket']
        elif on_ticket == 'autoclaim':
            ticket = pinfo['autoclaim']['ticket']

        return ticket


    def _fail(self, req, code):
        req.status = code
        return


class WebAuthorSearch(WebInterfaceDirectory):
    """
    Provides an interface to profile search using AJAX queries.
    """
    _exports = ['list',
                'details']

    # This class requires JSON libraries
    assert CFG_JSON_AVAILABLE, "[WebAuthorSearch] JSON must be enabled."

    class QueryPerson(WebInterfaceDirectory):
        _exports = ['']

        MIN_QUERY_LENGTH = 2
        QUERY_REGEX = re.compile(r"[\w\s\.\-,@]+$", re.UNICODE)

        def __init__(self, query=None):
            self.query = query

        def _lookup(self, component, path):
            if component not in self._exports:
                return WebAuthorSearch.QueryPerson(component), path

        def __call__(self, req, form):
            if self.query is None or len(self.query) < self.MIN_QUERY_LENGTH:
                req.status = apache.HTTP_BAD_REQUEST
                return "Query too short"
            if not self.QUERY_REGEX.match(self.query):
                req.status = apache.HTTP_BAD_REQUEST
                return "Invalid query."

            pid_results = [{"pid": pid[0]} for pid in webapi.search_person_ids_by_name(self.query)]
            req.content_type = 'application/json'
            return json.dumps(pid_results)

        # Request for index handled by __call__
        index = __call__

    def _JSON_received(self, form):
        try:
            return "jsondata" in form
        except TypeError:
            return False

    def _extract_JSON(self, form):
        try:
            json_data = json.loads(str(form['jsondata']))
            json_data = json_unicode_to_utf8(json_data)
            return json_data
        except ValueError:
            return None

    def _get_pid_details(self, pid):
        details = webapi.get_person_info_by_pid(pid)
        details.update({
            "names": [{"name": x, "paperCount": y} for x, y in webapi.get_person_names_from_id(pid)],
            "externalIds": [{x: y} for x, y in webapi.get_external_ids_from_person_id(pid).items()]
        })
        details['cname'] = details.pop("canonical_name", None)
        return details

    def details(self, req, form):
        if self._JSON_received(form):
            try:
                json_data = self._extract_JSON(form)
                pids = json_data['pids']

                req.content_type = 'application/json'
                details = [self._get_pid_details(pid) for pid in pids]
                return json.dumps(details)

            except (TypeError, KeyError):
                req.status = apache.HTTP_BAD_REQUEST
                return "Invalid query."
        else:
            req.status = apache.HTTP_BAD_REQUEST
            return "Incorrect query format."

    list = QueryPerson()


class WebInterfaceAuthor(WebInterfaceDirectory):
    '''
    Handles /author/* pages.

    Supplies the methods:
        /author/choose_profile
        /author/claim/
        /author/help
        /author/manage_profile
        /author/merge_profiles
        /author/profile/
        /author/search
        /author/ticket/
    '''
    _exports = ['',
                'choose_profile',
                'claim',
                'help',
                'manage_profile',
                'merge_profiles',
                'profile',
                'search',
                'search_ajax',
                'ticket']

    from invenio.webauthorprofile_webinterface import WebAuthorPages

    claim = WebInterfaceBibAuthorIDClaimPages()
    profile = WebAuthorPages()
    choose_profile = claim.choose_profile
    help = claim.help
    manage_profile = WebInterfaceBibAuthorIDManageProfilePages()
    merge_profiles = claim.merge_profiles
    search = claim.search
    search_ajax = WebAuthorSearch()
    ticket = WebInterfaceAuthorTicketHandling()

    def _lookup(self, component, path):
        if component not in self._exports:
            return WebInterfaceAuthor(component), path

    def __init__(self, component=None):
        self.path = component

    def __call__(self, req, form):
        if self.path is None or len(self.path) < 1:
            redirect_to_url(req, "%s/author/search" % CFG_BASE_URL)

        # Check if canonical id: e.g. "J.R.Ellis.1"
        pid = get_person_id_from_canonical_id(self.path)
        if pid >= 0:
            url = "%s/author/profile/%s" % (CFG_BASE_URL, get_person_redirect_link(pid))
            redirect_to_url(req, url, redirection_type=apache.HTTP_MOVED_PERMANENTLY)
            return
        else:
            try:
                pid = int(self.path)
            except ValueError:
                redirect_to_url(req, "%s/author/search?q=%s" % (CFG_BASE_URL, self.path))
                return
            else:
                if author_has_papers(pid):
                    cid = get_person_redirect_link(pid)
                    if is_valid_canonical_id(cid):
                        redirect_id = cid
                    else:
                        redirect_id = pid
                    url = "%s/author/profile/%s" % (CFG_BASE_URL, redirect_id)
                    redirect_to_url(req, url, redirection_type=apache.HTTP_MOVED_PERMANENTLY)
                    return

        redirect_to_url(req, "%s/author/search" % CFG_BASE_URL)
        return

    index = __call__


class WebInterfacePerson(WebInterfaceDirectory):
    '''
    Handles /person/* pages.

    Supplies the methods:
        /person/welcome
    '''
    _exports = ['welcome','update', 'you']

    def welcome(self, req, form):
        redirect_to_url(req, "%s/author/choose_profile" % CFG_SITE_SECURE_URL)

    def you(self, req, form):
        redirect_to_url(req, "%s/author/choose_profile" % CFG_SITE_SECURE_URL)

    def update(self, req, form):
        """
        Generate hepnames update form
        """
        argd = wash_urlargd(form,
                            {'ln': (str, CFG_SITE_LANG),
                             'email': (str, ''),
                             'IRN': (str, ''),
                            })
        # Retrieve info for HEP name based on email or IRN
        recids = []
        if argd['email']:
            recids = perform_request_search(p="371__m:%s" % argd['email'], cc="HepNames")
        elif argd['IRN']:
            recids = perform_request_search(p="001:%s" % argd['IRN'], cc="HepNames")
        else:
            redirect_to_url(req, "%s/collection/HepNames" % (CFG_SITE_URL))
        if not recids:
            redirect_to_url(req, "%s/collection/HepNames" % (CFG_SITE_URL))
        else:
            hepname_bibrec = get_bibrecord(recids[0])

        # Extract all info from recid that should be included in the form
        full_name = record_get_field_value(hepname_bibrec, tag="100", ind1="", ind2="", code="a")
        display_name = record_get_field_value(hepname_bibrec, tag="880", ind1="", ind2="", code="a")
        email = record_get_field_value(hepname_bibrec, tag="371", ind1="", ind2="", code="m")
        status = record_get_field_value(hepname_bibrec, tag="100", ind1="", ind2="", code="g")
        keynumber = record_get_field_value(hepname_bibrec, tag="970", ind1="", ind2="", code="a")
        try:
            keynumber = keynumber.split('-')[1]
        except IndexError:
            pass
        research_field_list = record_get_field_values(hepname_bibrec, tag="650", ind1="1", ind2="7", code="a")
        institution_list = []
        for instance in record_get_field_instances(hepname_bibrec, tag="371", ind1="", ind2=""):
            if not instance or field_get_subfield_values(instance, "m"):
                continue
            institution_info = ["", "", "", "", ""]
            if field_get_subfield_values(instance, "a"):
                institution_info[0] = field_get_subfield_values(instance, "a")[0]
            if field_get_subfield_values(instance, "r"):
                institution_info[1] = field_get_subfield_values(instance, "r")[0]
            if field_get_subfield_values(instance, "s"):
                institution_info[2] = field_get_subfield_values(instance, "s")[0]
            if field_get_subfield_values(instance, "t"):
                institution_info[3] = field_get_subfield_values(instance, "t")[0]
            if field_get_subfield_values(instance, "z"):
                institution_info[4] = field_get_subfield_values(instance, "z")[0]
            institution_list.append(institution_info)
        phd_advisor_list = record_get_field_values(hepname_bibrec, tag="701", ind1="", ind2="", code="a")
        experiment_list = record_get_field_values(hepname_bibrec, tag="693", ind1="", ind2="", code="e")
        web_page = record_get_field_value(hepname_bibrec, tag="856", ind1="1", ind2="", code="u")

        # Create form and pass as parameters all the content from the record
        body = TEMPLATE.tmpl_update_hep_name(full_name, display_name, email,
                                             status, research_field_list,
                                             institution_list, phd_advisor_list,
                                             experiment_list, web_page)
        title = "HEPNames"
        return page(title=title,
                    metaheaderadd = TEMPLATE.tmpl_update_hep_name_headers(),
                    body=body,
                    req=req,
                    )


# pylint: enable=C0301
# pylint: enable=W0613
