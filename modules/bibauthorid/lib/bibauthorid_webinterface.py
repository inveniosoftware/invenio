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
"""Bibauthorid Web Interface Logic and URL handler."""
# pylint: disable=W0105
# pylint: disable=C0301
# pylint: disable=W0613

from cgi import escape
from copy import deepcopy
from pprint import pformat

try:
    from invenio.jsonutils import json, CFG_JSON_AVAILABLE
except:
    CFG_JSON_AVAILABLE = False
    json = None

from invenio.bibauthorid_config import CLAIMPAPER_ADMIN_ROLE
from invenio.bibauthorid_config import CLAIMPAPER_USER_ROLE
#from invenio.bibauthorid_config import EXTERNAL_CLAIMED_RECORDS_KEY
from invenio.config import CFG_SITE_LANG
from invenio.config import CFG_SITE_URL
from invenio.config import CFG_SITE_NAME
from invenio.config import CFG_INSPIRE_SITE
#from invenio.config import CFG_SITE_SECURE_URL
from invenio.webpage import page, pageheaderonly, pagefooteronly
from invenio.messages import gettext_set_language #, wash_language
from invenio.template import load
from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory
from invenio.session import get_session
from invenio.urlutils import redirect_to_url
from invenio.webuser import getUid, page_not_authorized, collect_user_info, set_user_preferences
from invenio.webuser import email_valid_p, emailUnique
from invenio.webuser import get_email_from_username, get_uid_from_email, isUserSuperAdmin
from invenio.access_control_admin import acc_find_user_role_actions
from invenio.access_control_admin import acc_get_user_roles, acc_get_role_id
from invenio.search_engine import perform_request_search, sort_records
from invenio.search_engine_utils import get_fieldvalues

import invenio.bibauthorid_webapi as webapi
import invenio.bibauthorid_config as bconfig

from invenio.bibauthorid_frontinterface import get_bibrefrec_name_string

TEMPLATE = load('bibauthorid')

class WebInterfaceBibAuthorIDPages(WebInterfaceDirectory):
    """
    Handle /person pages and AJAX requests

    Supplies the methods
        /person/<string>
        /person/action
        /person/welcome
        /person/search
        /person/you -> /person/<string>
        /person/export
        /person/claimstub
    """
    _exports = ['', 'action', 'welcome', 'search', 'you', 'export', 'tickets_admin', 'claimstub']


    def __init__(self, person_id=None):
        """
        Constructor of the web interface.

        @param person_id: The identifier of a user. Can be one of:
            - a bibref: e.g. "100:1442,155"
            - a person id: e.g. "14"
            - a canonical id: e.g. "Ellis_J_1"
        @type person_id: string

        @return: will return an empty object if the identifier is of wrong type
        @rtype: None (if something is not right)
        """
        pid = -1
        is_bibref = False
        is_canonical_id = False
        self.adf = self.__init_call_dispatcher()

        if (not isinstance(person_id, str)) or (not person_id):
            self.person_id = pid
            return None

        if person_id.count(":") and person_id.count(","):
            is_bibref = True
        elif webapi.is_valid_canonical_id(person_id):
            is_canonical_id = True

        if is_bibref and pid > -2:
            bibref = person_id
            table, ref, bibrec = None, None, None

            if not bibref.count(":"):
                pid = -2

            if not bibref.count(","):
                pid = -2

            try:
                table = bibref.split(":")[0]
                ref = bibref.split(":")[1].split(",")[0]
                bibrec = bibref.split(":")[1].split(",")[1]
            except IndexError:
                pid = -2

            try:
                table = int(table)
                ref = int(ref)
                bibrec = int(bibrec)
            except (ValueError, TypeError):
                pid = -2

            if pid == -1:
                try:
                    pid = int(webapi.get_person_id_from_paper(person_id))
                except (ValueError, TypeError):
                    pid = -1
            else:
                pid = -1
        elif is_canonical_id:
            try:
                pid = int(webapi.get_person_id_from_canonical_id(person_id))
            except (ValueError, TypeError):
                pid = -1
        else:
            try:
                pid = int(person_id)
            except ValueError:
                pid = -1

        self.person_id = pid


    def __call__(self, req, form):
        '''
        Serve the main person page.
        Will use the object's person id to get a person's information.

        @param req: Apache Request Object
        @type req: Apache Request Object
        @param form: Parameters sent via GET or POST request
        @type form: dict

        @return: a full page formatted in HTML
        @return: string
        '''
        self._session_bareinit(req)
        argd = wash_urlargd(form, {'ln': (str, CFG_SITE_LANG),
                                   'verbose': (int, 0),
                                   'ticketid': (int, -1),
                                   'open_claim': (str, None)})

        ln = argd['ln']
        # ln = wash_language(argd['ln'])

        rt_ticket_id = argd['ticketid']
        req.argd = argd #needed for perform_req_search
        session = get_session(req)
        ulevel = self.__get_user_role(req)
        uid = getUid(req)

        if self.person_id < 0:
            return redirect_to_url(req, "%s/person/search" % (CFG_SITE_URL))

        if isUserSuperAdmin({'uid': uid}):
            ulevel = 'admin'

        no_access = self._page_access_permission_wall(req, [self.person_id])

        if no_access:
            return no_access

        try:
            pinfo = session["personinfo"]
        except KeyError:
            pinfo = dict()
            session['personinfo'] = pinfo

        if 'open_claim' in argd and argd['open_claim']:
            pinfo['claim_in_process'] = True
        elif "claim_in_process" in pinfo and pinfo["claim_in_process"]:
            pinfo['claim_in_process'] = True
        else:
            pinfo['claim_in_process'] = False

        uinfo = collect_user_info(req)
        uinfo['precached_viewclaimlink'] = pinfo['claim_in_process']
        set_user_preferences(uid, uinfo)

        pinfo['ulevel'] = ulevel
        if self.person_id != -1:
            pinfo["claimpaper_admin_last_viewed_pid"] = self.person_id
        pinfo["ln"] = ln

        if not "ticket" in pinfo:
            pinfo["ticket"] = []

        if rt_ticket_id:
            pinfo["admin_requested_ticket_id"] = rt_ticket_id

        session.save()

        content = ''
        for part in ['optional_menu', 'ticket_box', 'personid_info', 'tabs', 'footer']:
            content += self.adf[part][ulevel](req, form, ln)

        title = self.adf['title'][ulevel](req, form, ln)
        body = TEMPLATE.tmpl_person_detail_layout(content)
        metaheaderadd = self._scripts()
        self._clean_ticket(req)

        return page(title=title,
            metaheaderadd=metaheaderadd,
            body=body,
            req=req,
            language=ln)


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

        if not bconfig.AID_ENABLED:
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
                if user_pid[1]:
                    user_pid = user_pid[0][0]
                else:
                    user_pid = -1

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


    def _session_bareinit(self, req):
        '''
        Initializes session personinfo entry if none exists
        @param req: Apache Request Object
        @type req: Apache Request Object
        '''
        session = get_session(req)
        uid = getUid(req)
        ulevel = self.__get_user_role(req)

        if isUserSuperAdmin({'uid': uid}):
            ulevel = 'admin'

        try:
            pinfo = session["personinfo"]
            pinfo['ulevel'] = ulevel
            if "claimpaper_admin_last_viewed_pid" not in pinfo:
                pinfo["claimpaper_admin_last_viewed_pid"] = -2
            if 'ln' not in pinfo:
                pinfo["ln"] = 'en'
            if 'ticket' not in pinfo:
                pinfo["ticket"] = []
            session.save()
        except KeyError:
            pinfo = dict()
            session['personinfo'] = pinfo
            pinfo['ulevel'] = ulevel
            pinfo["claimpaper_admin_last_viewed_pid"] = -2
            pinfo["ln"] = 'en'
            pinfo["ticket"] = []
            session.save()


    def _lookup(self, component, path):
        """
        This handler parses dynamic URLs:
        - /person/1332 shows the page of person 1332
        - /person/100:5522,1431 shows the page of the person
            identified by the table:bibref,bibrec pair
        """
        if not component in self._exports:
            return WebInterfaceBibAuthorIDPages(component), path


    def __init_call_dispatcher(self):
        '''
        Initialization of call dispacher dictionary

        @return: call dispatcher dictionary
        @rtype: dict
        '''
        #author_detail_functions
        adf = dict()
        adf['title'] = dict()
        adf['optional_menu'] = dict()
        adf['ticket_box'] = dict()
        adf['tabs'] = dict()
        adf['footer'] = dict()
        adf['personid_info'] = dict()
        adf['ticket_dispatch'] = dict()
        adf['ticket_commit'] = dict()

        adf['title']['guest'] = self._generate_title_guest
        adf['title']['user'] = self._generate_title_user
        adf['title']['admin'] = self._generate_title_admin

        adf['optional_menu']['guest'] = self._generate_optional_menu_guest
        adf['optional_menu']['user'] = self._generate_optional_menu_user
        adf['optional_menu']['admin'] = self._generate_optional_menu_admin

        adf['ticket_box']['guest'] = self._generate_ticket_box_guest
        adf['ticket_box']['user'] = self._generate_ticket_box_user
        adf['ticket_box']['admin'] = self._generate_ticket_box_admin

        adf['personid_info']['guest'] = self._generate_person_info_box_guest
        adf['personid_info']['user'] = self._generate_person_info_box_user
        adf['personid_info']['admin'] = self._generate_person_info_box_admin

        adf['tabs']['guest'] = self._generate_tabs_guest
        adf['tabs']['user'] = self._generate_tabs_user
        adf['tabs']['admin'] = self._generate_tabs_admin

        adf['footer']['guest'] = self._generate_footer_guest
        adf['footer']['user'] = self._generate_footer_user
        adf['footer']['admin'] = self._generate_footer_admin

        adf['ticket_dispatch']['guest'] = self._ticket_dispatch_user
        adf['ticket_dispatch']['user'] = self._ticket_dispatch_user
        adf['ticket_dispatch']['admin'] = self._ticket_dispatch_admin

        adf['ticket_commit']['guest'] = self._ticket_commit_guest
        adf['ticket_commit']['user'] = self._ticket_commit_user
        adf['ticket_commit']['admin'] = self._ticket_commit_admin

        return adf


    def _generate_title_guest(self, req, form, ln):
        '''
        Generate the title for a guest user
        @param req: Apache Request Object
        @type req: Apache Request Object
        @param form: POST/GET variables of the request
        @type form: dict
        @param ln: language to show this page in
        @type ln: string
        '''
        if self.person_id:
            return 'Attribute papers for: ' + str(webapi.get_person_redirect_link(self.person_id))
        else:
            return 'Attribute papers'


    def _generate_title_user(self, req, form, ln):
        '''
        Generate the title for a regular user
        @param req: Apache Request Object
        @type req: Apache Request Object
        @param form: POST/GET variables of the request
        @type form: dict
        @param ln: language to show this page in
        @type ln: string
        '''
        if self.person_id:
            return 'Attribute papers (user interface) for: ' + str(webapi.get_person_redirect_link(self.person_id))
        else:
            return 'Attribute papers'

    def _generate_title_admin(self, req, form, ln):
        '''
        Generate the title for an admin user
        @param req: Apache Request Object
        @type req: Apache Request Object
        @param form: POST/GET variables of the request
        @type form: dict
        @param ln: language to show this page in
        @type ln: string
        '''
        if self.person_id:
            return 'Attribute papers (administrator interface) for: ' + str(webapi.get_person_redirect_link(self.person_id))
        else:
            return 'Attribute papers'


    def _generate_optional_menu_guest(self, req, form, ln):
        '''
        Generate the menu for a guest user
        @param req: Apache Request Object
        @type req: Apache Request Object
        @param form: POST/GET variables of the request
        @type form: dict
        @param ln: language to show this page in
        @type ln: string
        '''
        argd = wash_urlargd(form, {'ln': (str, CFG_SITE_LANG),
                                   'verbose': (int, 0)})
        menu = TEMPLATE.tmpl_person_menu()

        if "verbose" in argd and argd["verbose"] > 0:
            session = get_session(req)
            pinfo = session['personinfo']
            menu += "\n<pre>" + pformat(pinfo) + "</pre>\n"

        return menu


    def _generate_optional_menu_user(self, req, form, ln):
        '''
        Generate the menu for a regular user
        @param req: Apache Request Object
        @type req: Apache Request Object
        @param form: POST/GET variables of the request
        @type form: dict
        @param ln: language to show this page in
        @type ln: string
        '''
        argd = wash_urlargd(form, {'ln': (str, CFG_SITE_LANG),
                                   'verbose': (int, 0)})
        menu = TEMPLATE.tmpl_person_menu()

        if "verbose" in argd and argd["verbose"] > 0:
            session = get_session(req)
            pinfo = session['personinfo']
            menu += "\n<pre>" + pformat(pinfo) + "</pre>\n"

        return menu


    def _generate_optional_menu_admin(self, req, form, ln):
        '''
        Generate the title for an admin user
        @param req: Apache Request Object
        @type req: Apache Request Object
        @param form: POST/GET variables of the request
        @type form: dict
        @param ln: language to show this page in
        @type ln: string
        '''
        argd = wash_urlargd(form, {'ln': (str, CFG_SITE_LANG),
                                   'verbose': (int, 0)})
        menu = TEMPLATE.tmpl_person_menu_admin()

        if "verbose" in argd and argd["verbose"] > 0:
            session = get_session(req)
            pinfo = session['personinfo']
            menu += "\n<pre>" + pformat(pinfo) + "</pre>\n"

        return menu


    def _generate_ticket_box_guest(self, req, form, ln):
        '''
        Generate the semi-permanent info box for a guest user
        @param req: Apache Request Object
        @type req: Apache Request Object
        @param form: POST/GET variables of the request
        @type form: dict
        @param ln: language to show this page in
        @type ln: string
        '''
        session = get_session(req)
        pinfo = session['personinfo']
        ticket = pinfo['ticket']
        pendingt = []
        donet = []
        for t in ticket:
            if 'execution_result' in t:
                if t['execution_result'] == True:
                    donet.append(t)
            else:
                pendingt.append(t)

        if len(pendingt) == 1:
            message = 'There is ' + str(len(pendingt)) + ' transaction in progress.'
        else:
            message = 'There are ' + str(len(pendingt)) + ' transactions in progress.'

        teaser = 'Claim in process!'
        if len(pendingt) == 0:
            box = ""
        else:
            box = TEMPLATE.tmpl_ticket_box(teaser, message)

        if len(donet) > 0:
            teaser = 'Success!'
            if len(donet) == 1:
                message = str(len(donet)) + ' transaction successfully executed.'
            else:
                message = str(len(donet)) + ' transactions successfully executed.'

            box = box + TEMPLATE.tmpl_notification_box(message, teaser)
        return box


    def _generate_ticket_box_user(self, req, form, ln):
        '''
        Generate the semi-permanent info box for a regular user
        @param req: Apache Request Object
        @type req: Apache Request Object
        @param form: POST/GET variables of the request
        @type form: dict
        @param ln: language to show this page in
        @type ln: string
        '''
        return self._generate_ticket_box_guest(req, form, ln)


    def _generate_ticket_box_admin(self, req, form, ln):
        '''
        Generate the semi-permanent info box for an admin user
        @param req: Apache Request Object
        @type req: Apache Request Object
        @param form: POST/GET variables of the request
        @type form: dict
        @param ln: language to show this page in
        @type ln: string
        '''
        return self._generate_ticket_box_guest(req, form, ln)


    def _generate_person_info_box_guest(self, req, form, ln):
        '''
        Generate the name info box for a guest user
        @param req: Apache Request Object
        @type req: Apache Request Object
        @param form: POST/GET variables of the request
        @type form: dict
        @param ln: language to show this page in
        @type ln: string
        '''
        return self._generate_person_info_box_admin(req, form, ln)


    def _generate_person_info_box_user(self, req, form, ln):
        '''
        Generate the name info box for a regular user
        @param req: Apache Request Object
        @type req: Apache Request Object
        @param form: POST/GET variables of the request
        @type form: dict
        @param ln: language to show this page in
        @type ln: string
        '''
        return self._generate_person_info_box_admin(req, form, ln)


    def _generate_person_info_box_admin(self, req, form, ln):
        '''
        Generate the name info box for an admin user
        @param req: Apache Request Object
        @type req: Apache Request Object
        @param form: POST/GET variables of the request
        @type form: dict
        @param ln: language to show this page in
        @type ln: string
        '''
        names = webapi.get_person_names_from_id(self.person_id)
        box = TEMPLATE.tmpl_admin_person_info_box(ln, person_id=self.person_id,
                                                  names=names)

        return box


    def _generate_tabs_guest(self, req, form, ln):
        '''
        Generate the tabs content for a guest user
        @param req: Apache Request Object
        @type req: Apache Request Object
        @param form: POST/GET variables of the request
        @type form: dict
        @param ln: language to show this page in
        @type ln: string
        '''
        session = get_session(req)
#        uid = getUid(req)
        pinfo = session["personinfo"]
        if 'ln' in pinfo:
            ln = pinfo["ln"]
        else:
            ln = CFG_SITE_LANG
        _ = gettext_set_language(ln)

        links = [] # ['delete', 'commit','del_entry','commit_entry']
        tabs = ['records', 'repealed', 'review']
        verbiage_dict = {'confirmed': 'Papers', 'repealed': _('Papers removed from this profile'),
                                         'review': _('Papers in need of review'),
                                         'tickets': _('Open Tickets'), 'data': _('Data'),
                                         'confirmed_ns': _('Papers of this Person'),
                                         'repealed_ns': _('Papers _not_ of this Person'),
                                         'review_ns': _('Papers in need of review'),
                                         'tickets_ns': _('Tickets for this Person'),
                                         'data_ns': _('Additional Data for this Person')}

        buttons_verbiage_dict = {'mass_buttons': {'no_doc_string': _('Sorry, there are currently no documents to be found in this category.'),
                                                  'b_confirm': _('Yes, those papers are by this person.'),
                                                  'b_repeal': _('No, those papers are not by this person'),
                                                  'b_to_others': _('Assign to other person'),
                                                  'b_forget': _('Forget decision')},
                                 'record_undecided': {'alt_confirm': _('Confirm!'),
                                                     'confirm_text': _('Yes, this paper is by this person.'),
                                                     'alt_repeal': _('Rejected!'),
                                                     'repeal_text': _('No, this paper is <i>not</i> by this person'),
                                                     'to_other_text': _('Assign to another person'),
                                                     'alt_to_other': _('To other person!')},
                                 'record_confirmed': {'alt_confirm': _('Confirmed.'),
                                                       'confirm_text': _('Marked as this person\'s paper'),
                                                       'alt_forget': _('Forget decision!'),
                                                       'forget_text': _('Forget decision.'),
                                                       'alt_repeal': _('Repeal!'),
                                                       'repeal_text': _('But it\'s <i>not</i> this person\'s paper.'),
                                                       'to_other_text': _('Assign to another person'),
                                                       'alt_to_other': _('To other person!')},
                                 'record_repealed': {'alt_confirm': _('Confirm!'),
                                                    'confirm_text': _('But it <i>is</i> this person\'s paper.'),
                                                    'alt_forget': _('Forget decision!'),
                                                    'forget_text': _('Forget decision.'),
                                                    'alt_repeal': _('Repealed'),
                                                    'repeal_text': _('Marked as not this person\'s paper'),
                                                    'to_other_text': _('Assign to another person'),
                                                    'alt_to_other': _('To other person!')}}

        return self._generate_tabs_admin(req, form, ln, show_tabs=tabs, ticket_links=links,
                                         show_reset_button=False,
                                         open_tickets=[], verbiage_dict=verbiage_dict,
                                         buttons_verbiage_dict=buttons_verbiage_dict)


    def _generate_tabs_user(self, req, form, ln):
        '''
        Generate the tabs content for a regular user
        @param req: Apache Request Object
        @type req: Apache Request Object
        @param form: POST/GET variables of the request
        @type form: dict
        @param ln: language to show this page in
        @type ln: string
        '''
        session = get_session(req)
        uid = getUid(req)
        pinfo = session['personinfo']
        if 'ln' in pinfo:
            ln = pinfo["ln"]
        else:
            ln = CFG_SITE_LANG
        _ = gettext_set_language(ln)

        links = ['delete', 'del_entry']
        tabs = ['records', 'repealed', 'review', 'tickets']
        if pinfo["claimpaper_admin_last_viewed_pid"] == webapi.get_pid_from_uid(uid)[0][0]:
            verbiage_dict = {'confirmed': _('Your papers'), 'repealed': _('Not your papers'),
                                             'review': _('Papers in need of review'),
                                             'tickets': _('Your tickets'), 'data': _('Data'),
                                             'confirmed_ns': _('Your papers'),
                                             'repealed_ns': _('Not your papers'),
                                             'review_ns': _('Papers in need of review'),
                                             'tickets_ns': _('Your tickets'),
                                             'data_ns': _('Additional Data for this Person')}
            buttons_verbiage_dict = {'mass_buttons': {'no_doc_string': _('Sorry, there are currently no documents to be found in this category.'),
                                                                  'b_confirm': _('These are mine!'),
                                                                  'b_repeal': _('These are not mine!'),
                                                                  'b_to_others': _('It\'s not mine, but I know whose it is!'),
                                                                  'b_forget': _('Forget decision')},
                                                 'record_undecided': {'alt_confirm': _('Mine!'),
                                                                     'confirm_text': _('This is my paper!'),
                                                                     'alt_repeal': _('Not mine!'),
                                                                     'repeal_text': _('This is not my paper!'),
                                                                     'to_other_text': _('Assign to another person'),
                                                                     'alt_to_other': _('To other person!')},
                                                 'record_confirmed': {'alt_confirm': _('Not Mine.'),
                                                                       'confirm_text': _('Marked as my paper!'),
                                                                       'alt_forget': _('Forget decision!'),
                                                                       'forget_text': _('Forget assignment decision'),
                                                                       'alt_repeal': _('Not Mine!'),
                                                                       'repeal_text': _('But this is mine!'),
                                                                       'to_other_text': _('Assign to another person'),
                                                                       'alt_to_other': _('To other person!')},
                                                 'record_repealed': {'alt_confirm': _('Mine!'),
                                                                    'confirm_text': _('But this is my paper!'),
                                                                    'alt_forget': _('Forget decision!'),
                                                                    'forget_text': _('Forget decision!'),
                                                                    'alt_repeal': _('Not Mine!'),
                                                                    'repeal_text': _('Marked as not your paper.'),
                                                                     'to_other_text': _('Assign to another person'),
                                                                     'alt_to_other': _('To other person!')}}
        else:
            verbiage_dict = {'confirmed': _('Papers'), 'repealed': _('Papers removed from this profile'),
                                 'review': _('Papers in need of review'),
                                 'tickets': _('Your tickets'), 'data': _('Data'),
                                 'confirmed_ns': _('Papers of this Person'),
                                 'repealed_ns': _('Papers _not_ of this Person'),
                                 'review_ns': _('Papers in need of review'),
                                 'tickets_ns': _('Tickets you created about this person'),
                                 'data_ns': _('Additional Data for this Person')}
            buttons_verbiage_dict = {'mass_buttons': {'no_doc_string': _('Sorry, there are currently no documents to be found in this category.'),
                                                  'b_confirm': _('Yes, those papers are by this person.'),
                                                  'b_repeal': _('No, those papers are not by this person'),
                                                  'b_to_others': _('Assign to other person'),
                                                  'b_forget': _('Forget decision')},
                                 'record_undecided': {'alt_confirm': _('Confirm!'),
                                                     'confirm_text': _('Yes, this paper is by this person.'),
                                                     'alt_repeal': _('Rejected!'),
                                                     'repeal_text': _('No, this paper is <i>not</i> by this person'),
                                                     'to_other_text': _('Assign to another person'),
                                                     'alt_to_other': _('To other person!')},
                                 'record_confirmed': {'alt_confirm': _('Confirmed.'),
                                                       'confirm_text': _('Marked as this person\'s paper'),
                                                       'alt_forget': _('Forget decision!'),
                                                       'forget_text': _('Forget decision.'),
                                                       'alt_repeal': _('Repeal!'),
                                                       'repeal_text': _('But it\'s <i>not</i> this person\'s paper.'),
                                                       'to_other_text': _('Assign to another person'),
                                                       'alt_to_other': _('To other person!')},
                                 'record_repealed': {'alt_confirm': _('Confirm!'),
                                                    'confirm_text': _('But it <i>is</i> this person\'s paper.'),
                                                    'alt_forget': _('Forget decision!'),
                                                    'forget_text': _('Forget decision.'),
                                                    'alt_repeal': _('Repealed'),
                                                    'repeal_text': _('Marked as not this person\'s paper'),
                                                    'to_other_text': _('Assign to another person'),
                                                    'alt_to_other': _('To other person!')}}
        session = get_session(req)
        uid = getUid(req)
        open_tickets = webapi.get_person_request_ticket(self.person_id)
        tickets = []
        for t in open_tickets:
            owns = False
            for row in t[0]:
                if row[0] == 'uid-ip' and row[1].split('||')[0] == str(uid):
                    owns = True
            if owns:
                tickets.append(t)
        return self._generate_tabs_admin(req, form, ln, show_tabs=tabs, ticket_links=links,
                                         open_tickets=tickets, verbiage_dict=verbiage_dict,
                                         buttons_verbiage_dict=buttons_verbiage_dict)


    def _generate_tabs_admin(self, req, form, ln,
                             show_tabs=['records', 'repealed', 'review', 'comments', 'tickets', 'data'],
                             open_tickets=None, ticket_links=['delete', 'commit', 'del_entry', 'commit_entry'],
                             verbiage_dict=None, buttons_verbiage_dict=None, show_reset_button=True):
        '''
        Generate the tabs content for an admin user
        @param req: Apache Request Object
        @type req: Apache Request Object
        @param form: POST/GET variables of the request
        @type form: dict
        @param ln: language to show this page in
        @type ln: string
        @param show_tabs: list of tabs to display
        @type show_tabs: list of strings
        @param ticket_links: list of links to display
        @type ticket_links: list of strings
        @param verbiage_dict: language for the elements
        @type verbiage_dict: dict
        @param buttons_verbiage_dict: language for the buttons
        @type buttons_verbiage_dict: dict
        '''
        session = get_session(req)
        personinfo = {}

        try:
            personinfo = session["personinfo"]
        except KeyError:
            return ""

        if 'ln' in personinfo:
            ln = personinfo["ln"]
        else:
            ln = CFG_SITE_LANG
        _ = gettext_set_language(ln)

        if not verbiage_dict:
            verbiage_dict = self._get_default_verbiage_dicts_for_admin(req)
        if not buttons_verbiage_dict:
            buttons_verbiage_dict = self._get_default_buttons_verbiage_dicts_for_admin(req)

        all_papers = webapi.get_papers_by_person_id(self.person_id,
                                                    ext_out=True)

        records = [{'recid': paper[0],
                    'bibref': paper[1],
                    'flag': paper[2],
                    'authorname': paper[3],
                    'authoraffiliation': paper[4],
                    'paperdate': paper[5],
                    'rt_status': paper[6],
                    'paperexperiment': paper[7]}
                    for paper in all_papers]

        rejected_papers = [row for row in records if row['flag'] < -1]
        rest_of_papers = [row for row in records if row['flag'] >= -1]
        review_needed = webapi.get_review_needing_records(self.person_id)

        if len(review_needed) < 1:
            if 'review' in show_tabs:
                show_tabs.remove('review')

        rt_tickets = None

        if open_tickets == None:
            open_tickets = webapi.get_person_request_ticket(self.person_id)
        else:
            if len(open_tickets) < 1:
                if 'tickets' in show_tabs:
                    show_tabs.remove('tickets')

        if "admin_requested_ticket_id" in personinfo:
            rt_tickets = personinfo["admin_requested_ticket_id"]

        # Send data to template function
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


    def _get_default_verbiage_dicts_for_admin(self, req):

        session = get_session(req)
        personinfo = {}

        try:
            personinfo = session["personinfo"]
        except KeyError:
            return ""

        if 'ln' in personinfo:
            ln = personinfo["ln"]
        else:
            ln = CFG_SITE_LANG
        _ = gettext_set_language(ln)

        verbiage_dict = {'confirmed': _('Papers'), 'repealed': _('Papers removed from this profile'),
                                 'review': _('Papers in need of review'),
                                 'tickets': _('Tickets'), 'data': _('Data'),
                                 'confirmed_ns': _('Papers of this Person'),
                                 'repealed_ns': _('Papers _not_ of this Person'),
                                 'review_ns': _('Papers in need of review'),
                                 'tickets_ns': _('Request Tickets'),
                                 'data_ns': _('Additional Data for this Person')}
        return verbiage_dict


    def _get_default_buttons_verbiage_dicts_for_admin(self, req):

        session = get_session(req)
        personinfo = {}

        try:
            personinfo = session["personinfo"]
        except KeyError:
            return ""

        if 'ln' in personinfo:
            ln = personinfo["ln"]
        else:
            ln = CFG_SITE_LANG
        _ = gettext_set_language(ln)

        buttons_verbiage_dict = {'mass_buttons': {'no_doc_string': _('Sorry, there are currently no documents to be found in this category.'),
                                                  'b_confirm': _('Yes, those papers are by this person.'),
                                                  'b_repeal': _('No, those papers are not by this person'),
                                                  'b_to_others': _('Assign to other person'),
                                                  'b_forget': _('Forget decision')},
                                 'record_undecided': {'alt_confirm': _('Confirm!'),
                                                     'confirm_text': _('Yes, this paper is by this person.'),
                                                     'alt_repeal': _('Rejected!'),
                                                     'repeal_text': _('No, this paper is <i>not</i> by this person'),
                                                     'to_other_text': _('Assign to another person'),
                                                     'alt_to_other': _('To other person!')},
                                 'record_confirmed': {'alt_confirm': _('Confirmed.'),
                                                       'confirm_text': _('Marked as this person\'s paper'),
                                                       'alt_forget': _('Forget decision!'),
                                                       'forget_text': _('Forget decision.'),
                                                       'alt_repeal': _('Repeal!'),
                                                       'repeal_text': _('But it\'s <i>not</i> this person\'s paper.'),
                                                       'to_other_text': _('Assign to another person'),
                                                       'alt_to_other': _('To other person!')},
                                 'record_repealed': {'alt_confirm': _('Confirm!'),
                                                    'confirm_text': _('But it <i>is</i> this person\'s paper.'),
                                                    'alt_forget': _('Forget decision!'),
                                                    'forget_text': _('Forget decision.'),
                                                    'alt_repeal': _('Repealed'),
                                                    'repeal_text': _('Marked as not this person\'s paper'),
                                                    'to_other_text': _('Assign to another person'),
                                                    'alt_to_other': _('To other person!')}}
        return buttons_verbiage_dict


    def _generate_footer_guest(self, req, form, ln):
        return self._generate_footer_admin(req, form, ln)


    def _generate_footer_user(self, req, form, ln):
        return self._generate_footer_admin(req, form, ln)


    def _generate_footer_admin(self, req, form, ln):
        return TEMPLATE.tmpl_invenio_search_box()


    def _ticket_dispatch_guest(self, req):
        '''
        Takes care of the ticket  when in guest mode
        '''
        return self._ticket_dispatch_user(req)


    def _ticket_dispatch_user(self, req):
        '''
        Takes care of the ticket  when in user and guest mode

        '''
        session = get_session(req)
        uid = getUid(req)
        pinfo = session["personinfo"]
#        ulevel = pinfo["ulevel"]
        ticket = pinfo["ticket"]
        bibref_check_required = self._ticket_review_bibref_check(req)

        if bibref_check_required:
            return bibref_check_required

        for t in ticket:
            t['status'] = webapi.check_transaction_permissions(uid,
                                                               t['bibref'],
                                                               t['pid'],
                                                               t['action'])
        session.save()
        return self._ticket_final_review(req)


    def _ticket_dispatch_admin(self, req):
        '''
        Takes care of the ticket  when in administrator mode

        '''
        return self._ticket_dispatch_user(req)


    def _ticket_review_bibref_check(self, req):
        '''
        checks if some of the transactions on the ticket are needing a review.
        If it's the case prompts the user to select the right bibref
        '''
        session = get_session(req)
        pinfo = session["personinfo"]
        ticket = pinfo["ticket"]

        if 'arxiv_name' in pinfo:
            arxiv_name = [pinfo['arxiv_name']]
        else:
            arxiv_name = None

        if 'ln' in pinfo:
            ln = pinfo["ln"]
        else:
            ln = CFG_SITE_LANG

        _ = gettext_set_language(ln)

        if ("bibref_check_required" in pinfo and pinfo["bibref_check_required"]
            and "bibref_check_reviewed_bibrefs" in pinfo):

            for rbibreft in pinfo["bibref_check_reviewed_bibrefs"]:
                if not rbibreft.count("||") or not rbibreft.count(","):
                    continue

                rpid, rbibref = rbibreft.split("||")
                rrecid = rbibref.split(",")[1]
                rpid = webapi.wash_integer_id(rpid)

                for ticket_update in [row for row in ticket
                                      if (row['bibref'] == str(rrecid) and
                                          row['pid'] == rpid)]:
                    ticket_update["bibref"] = rbibref
                    del(ticket_update["incomplete"])

            for ticket_remove in [row for row in ticket
                                  if ('incomplete' in row)]:
                ticket.remove(ticket_remove)

            if ("bibrefs_auto_assigned" in pinfo):
                del(pinfo["bibrefs_auto_assigned"])

            if ("bibrefs_to_confirm" in pinfo):
                del(pinfo["bibrefs_to_confirm"])

            del(pinfo["bibref_check_reviewed_bibrefs"])
            pinfo["bibref_check_required"] = False
            session.save()

            return ""

        else:
            bibrefs_auto_assigned = {}
            bibrefs_to_confirm = {}
            needs_review = []

#            if ("bibrefs_auto_assigned" in pinfo
#                 and pinfo["bibrefs_auto_assigned"]):
#                bibrefs_auto_assigned = pinfo["bibrefs_auto_assigned"]
#
#            if ("bibrefs_to_confirm" in pinfo
#                 and pinfo["bibrefs_to_confirm"]):
#                bibrefs_to_confirm = pinfo["bibrefs_to_confirm"]

            for transaction in ticket:
                if not webapi.is_valid_bibref(transaction['bibref']):
                    transaction['incomplete'] = True
                    needs_review.append(transaction)

            if not needs_review:
                pinfo["bibref_check_required"] = False
                session.save()
                return ""

            for transaction in needs_review:
                recid = webapi.wash_integer_id(transaction['bibref'])

                if recid < 0:
                    continue #this doesn't look like a recid--discard!

                pid = transaction['pid']

                if ((pid in bibrefs_auto_assigned
                     and 'bibrecs' in bibrefs_auto_assigned[pid]
                     and recid in bibrefs_auto_assigned[pid]['bibrecs'])
                    or
                    (pid in bibrefs_to_confirm
                     and 'bibrecs' in bibrefs_to_confirm[pid]
                     and recid in bibrefs_to_confirm[pid]['bibrecs'])):
                    continue # we already assessed those bibrefs.

                fctptr = webapi.get_possible_bibrefs_from_pid_bibrec
                bibrec_refs = fctptr(pid, [recid], additional_names=arxiv_name)
                person_name = webapi.get_most_frequent_name_from_pid(pid, allow_none=True)

                if not person_name:
                    if arxiv_name:
                        person_name = ''.join(arxiv_name)
                    else:
                        person_name = " "

                for brr in bibrec_refs:
                    if len(brr[1]) == 1:
                        if not pid in bibrefs_auto_assigned:
                            bibrefs_auto_assigned[pid] = {
                                'person_name': person_name,
                                'canonical_id': "TBA",
                                'bibrecs': {brr[0]: brr[1]}}
                        else:
                            bibrefs_auto_assigned[pid]['bibrecs'][brr[0]] = brr[1]
                    else:
                        if not brr[1]:
                            tmp = webapi.get_bibrefs_from_bibrecs([brr[0]])

                            try:
                                brr[1] = tmp[0][1]
                            except IndexError:
                                continue # No bibrefs on record--discard

                        if not pid in bibrefs_to_confirm:
                            bibrefs_to_confirm[pid] = {
                                'person_name': person_name,
                                'canonical_id': "TBA",
                                'bibrecs': {brr[0]: brr[1]}}
                        else:
                            bibrefs_to_confirm[pid]['bibrecs'][brr[0]] = brr[1]

            if bibrefs_to_confirm or bibrefs_auto_assigned:
                pinfo["bibref_check_required"] = True
                baa = deepcopy(bibrefs_auto_assigned)
                btc = deepcopy(bibrefs_to_confirm)

                for pid in baa:
                    for rid in baa[pid]['bibrecs']:
                        baa[pid]['bibrecs'][rid] = []

                for pid in btc:
                    for rid in btc[pid]['bibrecs']:
                        btc[pid]['bibrecs'][rid] = []

                pinfo["bibrefs_auto_assigned"] = baa
                pinfo["bibrefs_to_confirm"] = btc
            else:
                pinfo["bibref_check_required"] = False

            session.save()

            if 'external_first_entry' in pinfo and pinfo['external_first_entry']:
                del(pinfo["external_first_entry"])
                pinfo['external_first_entry_skip_review'] = True
                session.save()
                return "" # don't bother the user the first time

            body = TEMPLATE.tmpl_bibref_check(bibrefs_auto_assigned,
                                          bibrefs_to_confirm)
            body = TEMPLATE.tmpl_person_detail_layout(body)

            metaheaderadd = self._scripts(kill_browser_cache=True)
            title = _("Submit Attribution Information")

            return page(title=title,
                metaheaderadd=metaheaderadd,
                body=body,
                req=req,
                language=ln)


    def _ticket_final_review(self, req):
        '''
        displays the user what can/cannot finally be done, leaving the option of kicking some
        transactions from the ticket before commit
        '''
        session = get_session(req)
        uid = getUid(req)
        userinfo = collect_user_info(uid)
        pinfo = session["personinfo"]
        ulevel = pinfo["ulevel"]
        ticket = pinfo["ticket"]
        ticket = [row for row in ticket if not "execution_result" in row]
        skip_checkout_page = True
        upid = -1
        user_first_name = ""
        user_first_name_sys = False
        user_last_name = ""
        user_last_name_sys = False
        user_email = ""
        user_email_sys = False

        if 'ln' in pinfo:
            ln = pinfo["ln"]
        else:
            ln = CFG_SITE_LANG

        _ = gettext_set_language(ln)

        if ("external_firstname" in userinfo
              and userinfo["external_firstname"]):
            user_first_name = userinfo["external_firstname"]
            user_first_name_sys = True
        elif "user_first_name" in pinfo and pinfo["user_first_name"]:
            user_first_name = pinfo["user_first_name"]

        if ("external_familyname" in userinfo
              and userinfo["external_familyname"]):
            user_last_name = userinfo["external_familyname"]
            user_last_name_sys = True
        elif "user_last_name" in pinfo and pinfo["user_last_name"]:
            user_last_name = pinfo["user_last_name"]

        if ("email" in userinfo
              and not userinfo["email"] == "guest"):
            user_email = userinfo["email"]
            user_email_sys = True
        elif "user_email" in pinfo and pinfo["user_email"]:
            user_email = pinfo["user_email"]

        pinfo["user_first_name"] = user_first_name
        pinfo["user_first_name_sys"] = user_first_name_sys
        pinfo["user_last_name"] = user_last_name
        pinfo["user_last_name_sys"] = user_last_name_sys
        pinfo["user_email"] = user_email
        pinfo["user_email_sys"] = user_email_sys

        if "upid" in pinfo and pinfo["upid"]:
            upid = pinfo["upid"]
        else:
            dbpid = webapi.get_pid_from_uid(uid)

            if dbpid and dbpid[1]:
                if dbpid[0] and not dbpid[0] == -1:
                    upid = dbpid[0][0]
                    pinfo["upid"] = upid

        session.save()

        if not (user_first_name or user_last_name or user_email):
            skip_checkout_page = False

        if [row for row in ticket
            if row["status"] in ["denied", "warning_granted",
                                 "warning_denied"]]:
            skip_checkout_page = False

        if 'external_first_entry_skip_review' in pinfo and pinfo['external_first_entry_skip_review']:
            del(pinfo["external_first_entry_skip_review"])
            skip_checkout_page = True
            session.save()

        if (not ticket or skip_checkout_page
            or ("checkout_confirmed" in pinfo
                and pinfo["checkout_confirmed"]
                and "checkout_faulty_fields" in pinfo
                and not pinfo["checkout_faulty_fields"])):
            self.adf['ticket_commit'][ulevel](req)

            if "checkout_confirmed" in pinfo:
                del(pinfo["checkout_confirmed"])

            if "checkout_faulty_fields" in pinfo:
                del(pinfo["checkout_faulty_fields"])

            if "bibref_check_required" in pinfo:
                del(pinfo["bibref_check_required"])

#            if "user_ticket_comments" in pinfo:
#                del(pinfo["user_ticket_comments"])

            session.save()
            return self._ticket_dispatch_end(req)

        for tt in list(ticket):
            if not 'bibref' in tt or not 'pid' in tt:
                del(ticket[tt])
                continue

            tt['authorname_rec'] = get_bibrefrec_name_string(tt['bibref'])
            tt['person_name'] = webapi.get_most_frequent_name_from_pid(tt['pid'])

        mark_yours = []
        mark_not_yours = []

        if upid >= 0:
            mark_yours = [row for row in ticket
                          if (str(row["pid"]) == str(upid) and
                              row["action"] in ["to_other_person", "confirm"])]
            mark_not_yours = [row for row in ticket
                              if (str(row["pid"]) == str(upid) and
                                  row["action"] in ["repeal", "reset"])]
        mark_theirs = [row for row in ticket
                       if ((not str(row["pid"]) == str(upid)) and
                           row["action"] in ["to_other_person", "confirm"])]
        mark_not_theirs = [row for row in ticket
                           if ((not str(row["pid"]) == str(upid)) and
                               row["action"] in ["repeal", "reset"])]

        session.save()

        body = TEMPLATE.tmpl_ticket_final_review(req, mark_yours,
                                                 mark_not_yours,
                                                 mark_theirs,
                                                 mark_not_theirs)
        body = TEMPLATE.tmpl_person_detail_layout(body)
        metaheaderadd = self._scripts(kill_browser_cache=True)
        title = _("Please review your actions")

        #body = body + '<pre>' + pformat(pinfo) + '</pre>'
        return page(title=title,
            metaheaderadd=metaheaderadd,
            body=body,
            req=req,
            language=ln)


    def _ticket_commit_admin(self, req):
        '''
        Actual execution of the ticket transactions
        '''
        self._clean_ticket(req)
        session = get_session(req)
        uid = getUid(req)
        pinfo = session["personinfo"]
        ticket = pinfo["ticket"]

        userinfo = {'uid-ip': "%s||%s" % (uid, req.remote_ip)}

        if "user_ticket_comments" in pinfo:
            userinfo['comments'] = pinfo["user_ticket_comments"]
        if "user_first_name" in pinfo:
            userinfo['firstname'] = pinfo["user_first_name"]
        if "user_last_name" in pinfo:
            userinfo['lastname'] = pinfo["user_last_name"]
        if "user_email" in pinfo:
            userinfo['email'] = pinfo["user_email"]

        for t in ticket:
            t['execution_result'] = webapi.execute_action(t['action'], t['pid'], t['bibref'], uid,
                                                          userinfo['uid-ip'], str(userinfo))
        session.save()


    def _ticket_commit_user(self, req):
        '''
        Actual execution of the ticket transactions
        '''
        self._clean_ticket(req)
        session = get_session(req)
        uid = getUid(req)
        pinfo = session["personinfo"]
        ticket = pinfo["ticket"]
        ok_tickets = []

        userinfo = {'uid-ip': "%s||%s" % (uid, req.remote_ip)}

        if "user_ticket_comments" in pinfo:
            userinfo['comments'] = pinfo["user_ticket_comments"]
        if "user_first_name" in pinfo:
            userinfo['firstname'] = pinfo["user_first_name"]
        if "user_last_name" in pinfo:
            userinfo['lastname'] = pinfo["user_last_name"]
        if "user_email" in pinfo:
            userinfo['email'] = pinfo["user_email"]

        for t in list(ticket):
            if t['status'] in ['granted', 'warning_granted']:
                t['execution_result'] = webapi.execute_action(t['action'],
                                                    t['pid'], t['bibref'], uid,
                                                    userinfo['uid-ip'], str(userinfo))
                ok_tickets.append(t)
                ticket.remove(t)


        if ticket:
            webapi.create_request_ticket(userinfo, ticket)

        if CFG_INSPIRE_SITE and ok_tickets:
            webapi.send_user_commit_notification_email(userinfo, ok_tickets)

        for t in ticket:
            t['execution_result'] = True

        ticket[:] = ok_tickets
        session.save()


    def _ticket_commit_guest(self, req):
        '''
        Actual execution of the ticket transactions
        '''
        self._clean_ticket(req)
        session = get_session(req)
        pinfo = session["personinfo"]
        uid = getUid(req)
        userinfo = {'uid-ip': "userid: %s (from %s)" % (uid, req.remote_ip)}

        if "user_ticket_comments" in pinfo:
            if pinfo["user_ticket_comments"]:
                userinfo['comments'] = pinfo["user_ticket_comments"]
            else:
                userinfo['comments'] = "No comments submitted."
        if "user_first_name" in pinfo:
            userinfo['firstname'] = pinfo["user_first_name"]
        if "user_last_name" in pinfo:
            userinfo['lastname'] = pinfo["user_last_name"]
        if "user_email" in pinfo:
            userinfo['email'] = pinfo["user_email"]

        ticket = pinfo['ticket']
        webapi.create_request_ticket(userinfo, ticket)

        for t in ticket:
            t['execution_result'] = True

        session.save()


    def _ticket_dispatch_end(self, req):
        '''
        The ticket dispatch is finished, redirect to the original page of
        origin or to the last_viewed_pid
        '''
        session = get_session(req)
        pinfo = session["personinfo"]

        if 'claim_in_process' in pinfo:
            pinfo['claim_in_process'] = False

        uinfo = collect_user_info(req)
        uinfo['precached_viewclaimlink'] = True
        uid = getUid(req)
        set_user_preferences(uid, uinfo)

        if "referer" in pinfo and pinfo["referer"]:
            referer = pinfo["referer"]
            del(pinfo["referer"])
            session.save()
            return redirect_to_url(req, referer)

        return redirect_to_url(req, "%s/person/%s?open_claim=True" % (CFG_SITE_URL,
                                 webapi.get_person_redirect_link(
                                   pinfo["claimpaper_admin_last_viewed_pid"])))


    def _clean_ticket(self, req):
        '''
        Removes from a ticket the transactions with an execution_result flag
        '''
        session = get_session(req)
        pinfo = session["personinfo"]
        ticket = pinfo["ticket"]
        for t in list(ticket):
            if 'execution_result' in t:
                ticket.remove(t)
        session.save()


    def __get_user_role(self, req):
        '''
        Determines whether a user is guest, user or admin
        '''
        minrole = 'guest'
        role = 'guest'

        if not req:
            return minrole

        uid = getUid(req)

        if not isinstance(uid, int):
            return minrole

        admin_role_id = acc_get_role_id(CLAIMPAPER_ADMIN_ROLE)
        user_role_id = acc_get_role_id(CLAIMPAPER_USER_ROLE)

        user_roles = acc_get_user_roles(uid)

        if admin_role_id in user_roles:
            role = 'admin'
        elif user_role_id in user_roles:
            role = 'user'

        if role == 'guest' and webapi.is_external_user(uid):
            role = 'user'

        return role


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


    def _scripts(self, kill_browser_cache=False):
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
            if "user_first_name" in argd:
                if not argd["user_first_name"] and not skip_checkout_faulty_fields:
                    pinfo["checkout_faulty_fields"].append("user_first_name")
                else:
                    pinfo["user_first_name"] = escape(argd["user_first_name"])

        if not ("user_last_name_sys" in pinfo and pinfo["user_last_name_sys"]):
            if "user_last_name" in argd:
                if not argd["user_last_name"] and not skip_checkout_faulty_fields:
                    pinfo["checkout_faulty_fields"].append("user_last_name")
                else:
                    pinfo["user_last_name"] = escape(argd["user_last_name"])

        if not ("user_email_sys" in pinfo and pinfo["user_email_sys"]):
            if "user_email" in argd:
                if (not argd["user_email"]
                    or not email_valid_p(argd["user_email"])):
                    pinfo["checkout_faulty_fields"].append("user_email")
                else:
                    pinfo["user_email"] = escape(argd["user_email"])

                if (ulevel == "guest"
                    and emailUnique(argd["user_email"]) > 0):
                    pinfo["checkout_faulty_fields"].append("user_email_taken")

        if "user_comments" in argd:
            if argd["user_comments"]:
                pinfo["user_ticket_comments"] = escape(argd["user_comments"])
            else:
                pinfo["user_ticket_comments"] = ""

        session.save()


    def action(self, req, form):
        '''
        Initial step in processing of requests: ticket generation/update.
        Also acts as action dispatcher for interface mass action requests

        Valid mass actions are:
        - confirm: confirm assignments to a person
        - repeal: repeal assignments from a person
        - reset: reset assignments of a person
        - cancel: clean the session (erase tickets and so on)
        - to_other_person: assign a document from a person to another person

        @param req: Apache Request Object
        @type req: Apache Request Object
        @param form: Parameters sent via GET or POST request
        @type form: dict

        @return: a full page formatted in HTML
        @return: string
        '''
        self._session_bareinit(req)
        argd = wash_urlargd(
            form,
            {'ln': (str, CFG_SITE_LANG),
             'pid': (int, None),
             'confirm': (str, None),
             'repeal': (str, None),
             'reset': (str, None),
             'cancel': (str, None),
             'cancel_stage': (str, None),
             'bibref_check_submit': (str, None),
             'checkout': (str, None),
             'checkout_continue_claiming': (str, None),
             'checkout_submit': (str, None),
             'checkout_remove_transaction': (str, None),
             'to_other_person': (str, None),
             'cancel_search_ticket': (str, None),
             'user_first_name': (str, None),
             'user_last_name': (str, None),
             'user_email': (str, None),
             'user_comments': (str, None),
             'claim': (str, None),
             'cancel_rt_ticket': (str, None),
             'commit_rt_ticket': (str, None),
             'rt_id': (int, None),
             'rt_action': (str, None),
             'selection': (list, []),
             'set_canonical_name': (str, None),
             'canonical_name': (str, None)})

        ln = argd['ln']
        # ln = wash_language(argd['ln'])
        pid = None
        action = None
        bibrefs = None

        session = get_session(req)
        uid = getUid(req)
        pinfo = session["personinfo"]
        ulevel = pinfo["ulevel"]
        ticket = pinfo["ticket"]
        tempticket = []

        if not "ln" in pinfo:
            pinfo["ln"] = ln
            session.save()

        if 'confirm' in argd and argd['confirm']:
            action = 'confirm'
        elif 'repeal' in argd and argd['repeal']:
            action = 'repeal'
        elif 'reset' in argd and argd['reset']:
            action = 'reset'
        elif 'bibref_check_submit' in argd and argd['bibref_check_submit']:
            action = 'bibref_check_submit'
        elif 'cancel' in argd and argd['cancel']:
            action = 'cancel'
        elif 'cancel_stage' in argd and argd['cancel_stage']:
            action = 'cancel_stage'
        elif 'cancel_search_ticket' in argd and argd['cancel_search_ticket']:
            action = 'cancel_search_ticket'
        elif 'checkout' in argd and argd['checkout']:
            action = 'checkout'
        elif 'checkout_submit' in argd and argd['checkout_submit']:
            action = 'checkout_submit'
        elif ('checkout_remove_transaction' in argd
            and argd['checkout_remove_transaction']):
            action = 'checkout_remove_transaction'
        elif ('checkout_continue_claiming' in argd
            and argd['checkout_continue_claiming']):
            action = "checkout_continue_claiming"
        elif 'cancel_rt_ticket' in argd and argd['cancel_rt_ticket']:
            action = 'cancel_rt_ticket'
        elif 'commit_rt_ticket' in argd and argd['commit_rt_ticket']:
            action = 'commit_rt_ticket'
        elif 'to_other_person' in argd and argd['to_other_person']:
            action = 'to_other_person'
        elif 'claim' in argd and argd['claim']:
            action = 'claim'
        elif 'set_canonical_name' in argd and argd['set_canonical_name']:
            action = 'set_canonical_name'

        no_access = self._page_access_permission_wall(req, pid)

        if no_access and not action in ["claim"]:
            return no_access

        if action in ['to_other_person', 'claim']:
            if 'selection' in argd and len(argd['selection']) > 0:
                bibrefs = argd['selection']
            else:
                return self._error_page(req, ln,
                                        "Fatal: cannot create ticket without any bibrefrec")
            if action == 'claim':
                return self._ticket_open_claim(req, bibrefs, ln)
            else:
                return self._ticket_open_assign_to_other_person(req, bibrefs, form)

        if action in ["cancel_stage"]:
            if 'bibref_check_required' in pinfo:
                del(pinfo['bibref_check_required'])

            if 'bibrefs_auto_assigned' in pinfo:
                del(pinfo['bibrefs_auto_assigned'])

            if 'bibrefs_to_confirm' in pinfo:
                del(pinfo['bibrefs_to_confirm'])

            for tt in [row for row in ticket if 'incomplete' in row]:
                ticket.remove(tt)

            session.save()

            return self._ticket_dispatch_end(req)

        if action in ["checkout_submit"]:
            pinfo["checkout_faulty_fields"] = []
            self._check_user_fields(req, form)

            if not ticket:
                pinfo["checkout_faulty_fields"].append("tickets")

            if pinfo["checkout_faulty_fields"]:
                pinfo["checkout_confirmed"] = False
            else:
                pinfo["checkout_confirmed"] = True

            session.save()
            return self.adf['ticket_dispatch'][ulevel](req)
            #return self._ticket_final_review(req)

        if action in ["checkout_remove_transaction"]:
            bibref = argd['checkout_remove_transaction']

            if webapi.is_valid_bibref(bibref):
                for rmt in [row for row in ticket
                            if row["bibref"] == bibref]:
                    ticket.remove(rmt)

            pinfo["checkout_confirmed"] = False
            session.save()
            return self.adf['ticket_dispatch'][ulevel](req)
            #return self._ticket_final_review(req)

        if action in ["checkout_continue_claiming"]:
            pinfo["checkout_faulty_fields"] = []
            self._check_user_fields(req, form)

            return self._ticket_dispatch_end(req)

        if (action in ['bibref_check_submit']
            or (not action
                and "bibref_check_required" in pinfo
                and pinfo["bibref_check_required"])):
            if not action in ['bibref_check_submit']:
                if "bibref_check_reviewed_bibrefs" in pinfo:
                    del(pinfo["bibref_check_reviewed_bibrefs"])
                    session.save()

                return self.adf['ticket_dispatch'][ulevel](req)

            pinfo["bibref_check_reviewed_bibrefs"] = []
            add_rev = pinfo["bibref_check_reviewed_bibrefs"].append

            if ("bibrefs_auto_assigned" in pinfo
                or "bibrefs_to_confirm" in pinfo):
                person_reviews = []

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
                            elements = []

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

                                        if (webapi.is_valid_bibref(tref) and
                                            tpid > -1):
                                            add_rev(element + "," + str(bibrec))
            session.save()

            return self.adf['ticket_dispatch'][ulevel](req)

        if not action:
            return self._error_page(req, ln,
                                    "Fatal: cannot create ticket if no action selected.")

        if action in ['confirm', 'repeal', 'reset']:
            if 'pid' in argd:
                pid = argd['pid']
            else:
                return self._error_page(req, ln,
                                        "Fatal: cannot create ticket without a person id!")

            if 'selection' in argd and len(argd['selection']) > 0:
                bibrefs = argd['selection']
            else:
                if pid == -3:
                    return self._error_page(req, ln,
                                        "Fatal: Please select a paper to assign to the new person first!")
                else:
                    return self._error_page(req, ln,
                                        "Fatal: cannot create ticket without any paper selected!")

            if 'rt_id' in argd and argd['rt_id']:
                rt_id = argd['rt_id']
                for b in bibrefs:
                    self._cancel_transaction_from_rt_ticket(rt_id, pid, action, b)
            #create temporary ticket
            if pid == -3:
                pid = webapi.create_new_person(uid)

            for bibref in bibrefs:
                tempticket.append({'pid': pid, 'bibref': bibref, 'action': action})

            #check if ticket targets (bibref for pid) are already in ticket
            for t in tempticket:
                for e in list(ticket):
                    if e['pid'] == t['pid'] and e['bibref'] == t['bibref']:
                        ticket.remove(e)
                ticket.append(t)
            if 'search_ticket' in pinfo:
                del(pinfo['search_ticket'])

            #start ticket processing chain
            pinfo["claimpaper_admin_last_viewed_pid"] = pid
            session.save()
            return self.adf['ticket_dispatch'][ulevel](req)
#            return self.perform(req, form)

        elif action in ['cancel']:
            self.__session_cleanup(req)
#            return self._error_page(req, ln,
#                                    "Not an error! Session cleaned! but "
#                                    "redirect to be implemented")
            return self._ticket_dispatch_end(req)

        elif action in ['cancel_search_ticket']:
            if 'search_ticket' in pinfo:
                del(pinfo['search_ticket'])
            session.save()
            if "claimpaper_admin_last_viewed_pid" in pinfo:
                pid = pinfo["claimpaper_admin_last_viewed_pid"]
                return redirect_to_url(req, "/person/%s" % webapi.get_person_redirect_link(pid))
            return self.search(req, form)

        elif action in ['checkout']:
            return self.adf['ticket_dispatch'][ulevel](req)
            #return self._ticket_final_review(req)

        elif action in ['cancel_rt_ticket', 'commit_rt_ticket']:
            if 'selection' in argd and len(argd['selection']) > 0:
                bibref = argd['selection']
            else:
                return self._error_page(req, ln,
                                        "Fatal: cannot cancel unknown ticket")
            if 'pid' in argd and argd['pid'] > -1:
                pid = argd['pid']
            else:
                return self._error_page(req, ln,
                                        "Fatal: cannot cancel unknown ticket")
            if action == 'cancel_rt_ticket':
                if 'rt_id' in argd and argd['rt_id'] and 'rt_action' in argd and argd['rt_action']:
                    rt_id = argd['rt_id']
                    rt_action = argd['rt_action']
                    if 'selection' in argd and len(argd['selection']) > 0:
                        bibrefs = argd['selection']
                    else:
                        return self._error_page(req, ln,
                                        "Fatal: no bibref")
                    for b in bibrefs:
                        self._cancel_transaction_from_rt_ticket(rt_id, pid, rt_action, b)
                        return redirect_to_url(req, "/person/%s" % webapi.get_person_redirect_link(pid))
                return self._cancel_rt_ticket(req, bibref[0], pid)
            elif action == 'commit_rt_ticket':
                return self._commit_rt_ticket(req, bibref[0], pid)

        elif action == 'set_canonical_name':
            if 'pid' in argd and argd['pid'] > -1:
                pid = argd['pid']
            else:
                return self._error_page(req, ln,
                                        "Fatal: cannot set canonical name to unknown person")
            if 'canonical_name' in argd and argd['canonical_name']:
                cname = argd['canonical_name']
            else:
                return self._error_page(req, ln,
                        "Fatal: cannot set a custom canonical name without a suggestion")

            uid = getUid(req)
            userinfo = "%s||%s" % (uid, req.remote_ip)
            webapi.update_person_canonical_name(pid, cname, userinfo)

            return redirect_to_url(req, "/person/%s" % webapi.get_person_redirect_link(pid))

        else:
            return self._error_page(req, ln,
                                    "Fatal: What were I supposed to do?")


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
        session.save()
        pid = -1
        search_enabled = True

        if not no_access and uinfo["precached_usepaperclaim"]:
            tpid = webapi.get_pid_from_uid(uid)

            if tpid and tpid[0] and tpid[1] and tpid[0][0]:
                pid = tpid[0][0]

        if (not no_access
            and "claimpaper_admin_last_viewed_pid" in pinfo
            and pinfo["claimpaper_admin_last_viewed_pid"]):
            names = webapi.get_person_names_from_id(pinfo["claimpaper_admin_last_viewed_pid"])
            names = sorted([i for i in names], key=lambda k: k[1], reverse=True)
            if len(names) > 0:
                if len(names[0]) > 0:
                    last_viewed_pid = [pinfo["claimpaper_admin_last_viewed_pid"], names[0][0]]
                else:
                    last_viewed_pid = False
            else:
                last_viewed_pid = False
        else:
            last_viewed_pid = False

        if no_access:
            search_enabled = False

        pinfo["referer"] = uinfo["referer"]
        session.save()
        body = TEMPLATE.tmpl_open_claim(bibrefs, pid, last_viewed_pid,
                                        search_enabled=search_enabled)
        body = TEMPLATE.tmpl_person_detail_layout(body)
        title = _('Claim this paper')
        metaheaderadd = self._scripts(kill_browser_cache=True)

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
        search_ticket['action'] = 'confirm'
        search_ticket['bibrefs'] = bibrefs
        session.save()
        return self.search(req, form)


    def comments(self, req, form):
        return ""


    def _cancel_rt_ticket(self, req, tid, pid):
        '''
        deletes an RT ticket
        '''
        webapi.delete_request_ticket(pid, tid)
        return redirect_to_url(req, "/person/%s" %
                               webapi.get_person_redirect_link(str(pid)))


    def _cancel_transaction_from_rt_ticket(self, tid, pid, action, bibref):
        '''
        deletes a transaction from an rt ticket
        '''
        webapi.delete_transaction_from_request_ticket(pid, tid, action, bibref)


    def _commit_rt_ticket(self, req, bibref, pid):
        '''
        Commit of an rt ticket: creates a real ticket and commits.
        '''
        session = get_session(req)
        pinfo = session["personinfo"]
        ulevel = pinfo["ulevel"]
        ticket = pinfo["ticket"]

        open_rt_tickets = webapi.get_person_request_ticket(pid)
        tic = [a for a in open_rt_tickets if str(a[1]) == str(bibref)]
        if len(tic) > 0:
            tic = tic[0][0]
        #create temporary ticket
        tempticket = []
        for t in tic:
            if t[0] in ['confirm', 'repeal']:
                tempticket.append({'pid': pid, 'bibref': t[1], 'action': t[0]})

        #check if ticket targets (bibref for pid) are already in ticket
        for t in tempticket:
            for e in list(ticket):
                if e['pid'] == t['pid'] and e['bibref'] == t['bibref']:
                    ticket.remove(e)
            ticket.append(t)
        session.save()
        #start ticket processing chain
        webapi.delete_request_ticket(pid, bibref)
        return self.adf['ticket_dispatch'][ulevel](req)


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

        #pinfo['ulevel'] = ulevel
#        pinfo["claimpaper_admin_last_viewed_pid"] = -1
        pinfo["admin_requested_ticket_id"] = -1
        session.save()


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

        if 'ln' in pinfo:
            ln = pinfo["ln"]
        else:
            ln = CFG_SITE_LANG

        _ = gettext_set_language(ln)
        if 'search_ticket' in pinfo:
            search_ticket = pinfo['search_ticket']
        if not search_ticket:
            return ''
        else:
            teaser = _('Person search for assignment in progress!')
            message = _('You are searching for a person to assign the following papers:')
            return TEMPLATE.tmpl_search_ticket_box(teaser, message, search_ticket)


    def search(self, req, form, is_fallback=False, fallback_query='', fallback_title='', fallback_message=''):
        '''
        Function used for searching a person based on a name with which the
        function is queried.

        @param req: Apache Request Object
        @type req: Apache Request Object
        @param form: Parameters sent via GET or POST request
        @type form: dict

        @return: a full page formatted in HTML
        @return: string
        '''
        self._session_bareinit(req)
        session = get_session(req)
        no_access = self._page_access_permission_wall(req)
        new_person_link = False

        if no_access:
            return no_access

        pinfo = session["personinfo"]
        search_ticket = None
        if 'search_ticket' in pinfo:
            search_ticket = pinfo['search_ticket']

        if "ulevel" in pinfo:
            if pinfo["ulevel"] == "admin":
                new_person_link = True

        body = ''
        if search_ticket:
            body = body + self._generate_search_ticket_box(req)

        max_num_show_papers = 5
        argd = wash_urlargd(
            form,
            {'ln': (str, CFG_SITE_LANG),
             'verbose': (int, 0),
             'q': (str, None)})

        ln = argd['ln']
        # ln = wash_language(argd['ln'])
        query = None
        recid = None
        nquery = None
        search_results = None
        title = "Person Search"

        if 'q' in argd:
            if argd['q']:
                query = escape(argd['q'])

        if is_fallback and fallback_query:
            query = fallback_query

        if query:
            authors = []

            if query.count(":"):
                try:
                    left, right = query.split(":")
                    try:
                        recid = int(left)
                        nquery = str(right)
                    except (ValueError, TypeError):
                        try:
                            recid = int(right)
                            nquery = str(left)
                        except (ValueError, TypeError):
                            recid = None
                            nquery = query
                except ValueError:
                    recid = None
                    nquery = query

            else:
                nquery = query

            sorted_results = webapi.search_person_ids_by_name(nquery)

            for index, results in enumerate(sorted_results):
                pid = results[0]
#                authorpapers = webapi.get_papers_by_person_id(pid, -1)
#                authorpapers = sorted(authorpapers, key=itemgetter(0),
#                                      reverse=True)
                if index < bconfig.PERSON_SEARCH_RESULTS_SHOW_PAPERS_PERSON_LIMIT:
                    authorpapers = [[paper] for paper in
                                    sort_records(None, [i[0] for i in
                                                 webapi.get_papers_by_person_id(pid, -1)],
                                                 sort_field="year", sort_order="a")]
                else:
                    authorpapers = [['Not retrieved to increase performances.']]

                if (recid and
                    not (str(recid) in [row[0] for row in authorpapers])):
                    continue

                authors.append([results[0], results[1],
                                authorpapers[0:max_num_show_papers], len(authorpapers)])

            search_results = authors

        if recid and (len(search_results) == 1) and not is_fallback:
            return redirect_to_url(req, "/person/%s" % search_results[0][0])

        body = body + TEMPLATE.tmpl_author_search(query, search_results, search_ticket, author_pages_mode=True, fallback_mode=is_fallback,
                                                  fallback_title=fallback_title, fallback_message=fallback_message, new_person_link=new_person_link)

        if not is_fallback:
            body = TEMPLATE.tmpl_person_detail_layout(body)

        return page(title=title,
                    metaheaderadd=self._scripts(kill_browser_cache=True),
                    body=body,
                    req=req,
                    language=ln)


    def claimstub(self, req, form):
        '''
        Generate stub page before claiming process

        @param req: Apache request object
        @type req: Apache request object
        @param form: GET/POST request params
        @type form: dict
        '''
        argd = wash_urlargd(
            form,
            {'ln': (str, CFG_SITE_LANG),
             'person': (str, '')})

        ln = argd['ln']
        # ln = wash_language(argd['ln'])
        _ = gettext_set_language(ln)

        person = '-1'
        if 'person' in argd and argd['person']:
            person = argd['person']

        session = get_session(req)
        try:
            pinfo = session["personinfo"]
            if pinfo['ulevel'] == 'admin':
                return redirect_to_url(req, '%s/person/%s?open_claim=True' % (CFG_SITE_URL, person))
        except KeyError:
            pass

        if bconfig.BIBAUTHORID_UI_SKIP_ARXIV_STUB_PAGE:
            return redirect_to_url(req, '%s/person/%s?open_claim=True' % (CFG_SITE_URL, person))

        body = TEMPLATE.tmpl_claim_stub(person)

        pstr = 'Person ID missing or invalid'
        if person != '-1':
            pstr = person
        title = _('You are going to claim papers for: %s' % pstr)

        return page(title=title,
                    metaheaderadd=self._scripts(kill_browser_cache=True),
                    body=body,
                    req=req,
                    language=ln)

    def welcome(self, req, form):
        '''
        Generate SSO landing/welcome page

        @param req: Apache request object
        @type req: Apache request object
        @param form: GET/POST request params
        @type form: dict
        '''
        uid = getUid(req)
        self._session_bareinit(req)
        argd = wash_urlargd(
            form,
            {'ln': (str, CFG_SITE_LANG)})

        ln = argd['ln']
        # ln = wash_language(argd['ln'])
        _ = gettext_set_language(ln)

        if uid == 0:
            return page_not_authorized(req, text=_("This page in not accessible directly."))

        title_message = _('Welcome!')

        # start continuous writing to the browser...
        req.content_type = "text/html"
        req.send_http_header()
        ssl_param = 0

        if req.is_https():
            ssl_param = 1

        req.write(pageheaderonly(req=req, title=title_message,
                                 language=ln, secure_page_p=ssl_param))

        req.write(TEMPLATE.tmpl_welcome_start())

        body = ""

        if CFG_INSPIRE_SITE:
            body = TEMPLATE.tmpl_welcome_arxiv()
        else:
            body = TEMPLATE.tmpl_welcome()

        req.write(body)

        # now do what will take time...
        pid = webapi.arxiv_login(req)
        #session must be read after webapi.arxiv_login did it's stuff
        session = get_session(req)
        pinfo = session["personinfo"]
        pinfo["claimpaper_admin_last_viewed_pid"] = pid
        session.save()

        link = TEMPLATE.tmpl_welcome_link()
        req.write(link)
        req.write("<br><br>")
        uinfo = collect_user_info(req)

        arxivp = []
        if 'external_arxivids' in uinfo and uinfo['external_arxivids']:
            try:
                for i in uinfo['external_arxivids'].split(';'):
                    arxivp.append(i)
            except (IndexError, KeyError):
                pass

        req.write(TEMPLATE.tmpl_welcome_arXiv_papers(arxivp))
        if CFG_INSPIRE_SITE:
            #logs arXive logins, for debug purposes.
            dbg = ('uinfo= ' + str(uinfo) + '\npinfo= ' + str(pinfo) + '\nreq= ' + str(req)
                    + '\nsession= ' + str(session))
            userinfo = "%s||%s" % (uid, req.remote_ip)
            webapi.insert_log(userinfo, pid, 'arXiv_login', 'dbg', '', comment=dbg)

        req.write(TEMPLATE.tmpl_welcome_end())
        req.write(pagefooteronly(req=req))

    def tickets_admin(self, req, form):
        '''
        Generate SSO landing/welcome page

        @param req: Apache request object
        @type req: Apache request object
        @param form: GET/POST request params
        @type form: dict
        '''
        self._session_bareinit(req)
        no_access = self._page_access_permission_wall(req, req_level='admin')
        if no_access:
            return no_access

        tickets = webapi.get_persons_with_open_tickets_list()
        tickets = list(tickets)

        for t in list(tickets):
            tickets.remove(t)
            tickets.append([webapi.get_most_frequent_name_from_pid(int(t[0])),
                         webapi.get_person_redirect_link(t[0]), t[0], t[1]])

        body = TEMPLATE.tmpl_tickets_admin(tickets)
        body = TEMPLATE.tmpl_person_detail_layout(body)

        title = 'Open RT tickets'

        return page(title=title,
                    metaheaderadd=self._scripts(),
                    body=body,
                    req=req)

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

        if not request in bconfig.VALID_EXPORT_FILTERS:
            return "500_filter_invalid"

        if request == "arxiv":
            query = "(recid:"
            query += " OR recid:".join(papers)
            query += ") AND 037:arxiv"
            db_docs = perform_request_search(p=query)
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
    me = welcome
    you = welcome
# pylint: enable=C0301
# pylint: enable=W0613
