# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2008, 2009, 2010, 2011 CERN.
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


""" Bibcirculation web interface """

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

# others invenio imports
from invenio.config import CFG_SITE_LANG, \
                           CFG_SITE_URL, \
                           CFG_SITE_SECURE_URL, \
                           CFG_ACCESS_CONTROL_LEVEL_SITE, \
                           CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS


from invenio.webuser import getUid, page_not_authorized, isGuestUser, \
                            collect_user_info
from invenio.webpage import page, pageheaderonly, pagefooteronly
from invenio.search_engine import create_navtrail_links, \
     guess_primary_collection_of_a_record, \
     get_colID, check_user_can_view_record, \
     record_exists
from invenio.urlutils import redirect_to_url, \
                             make_canonical_urlargd
from invenio.messages import gettext_set_language
from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory
from invenio.websearchadminlib import get_detailed_page_tabs
from invenio.access_control_config import VIEWRESTRCOLL
from invenio.access_control_mailcookie import mail_cookie_create_authorize_action
import invenio.template
webstyle_templates = invenio.template.load('webstyle')
websearch_templates = invenio.template.load('websearch')

# bibcirculation imports
bibcirculation_templates = invenio.template.load('bibcirculation')
from invenio.bibcirculation import perform_new_request, \
                                   perform_new_request_send, \
                                   perform_get_holdings_information, \
                                   perform_borrower_loans, \
                                   perform_loanshistoricaloverview, \
                                   display_ill_form, \
                                   ill_register_request, \
                                   ill_request_with_recid, \
                                   ill_register_request_with_recid

class WebInterfaceYourLoansPages(WebInterfaceDirectory):
    """Defines the set of /yourloans pages."""


    _exports = ['', 'display', 'loanshistoricaloverview']

    def index(self, req, form):
        """ The function called by default
        """
        redirect_to_url(req, "%s/yourloans/display?%s" % (CFG_SITE_URL,
                                                          req.args))

    def display(self, req, form):
        """
        Displays all loans of a given user
        @param ln:  language
        @return the page for inbox
        """

        argd = wash_urlargd(form, {'barcode': (str, ""),
                                   'borrower_id': (int, 0),
                                   'request_id': (int, 0)})

        # Check if user is logged
        uid = getUid(req)
        if CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "%s/yourloans/display" % \
                                       (CFG_SITE_URL,),
                                       navmenuid="yourloans")
        elif uid == -1 or isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                CFG_SITE_SECURE_URL,
                make_canonical_urlargd({
                    'referer' : "%s/yourloans/display%s" % (
                        CFG_SITE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})), norobot=True)

        _ = gettext_set_language(argd['ln'])

        user_info = collect_user_info(req)
        if not user_info['precached_useloans']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use loans."))

        body = perform_borrower_loans(uid=uid,
                                      barcode=argd['barcode'],
                                      borrower_id=argd['borrower_id'],
                                      request_id=argd['request_id'],
                                      ln=argd['ln'])

        return page(title       = _("Your Loans"),
                    body        = body,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = argd['ln'],
                    navmenuid   = "yourloans",
                    secure_page_p=1)

    def loanshistoricaloverview(self, req, form):
        """
        Show loans historical overview.
        """

        argd = wash_urlargd(form, {})

        # Check if user is logged
        uid = getUid(req)
        if CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "%s/yourloans/loanshistoricaloverview" % \
                                       (CFG_SITE_URL,),
                                       navmenuid="yourloans")
        elif uid == -1 or isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                CFG_SITE_SECURE_URL,
                make_canonical_urlargd({
                    'referer' : "%s/yourloans/loanshistoricaloverview%s" % (
                        CFG_SITE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})), norobot=True)

        _ = gettext_set_language(argd['ln'])

        user_info = collect_user_info(req)
        if not user_info['precached_useloans']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use loans."))

        body = perform_loanshistoricaloverview(uid=uid,
                                               ln=argd['ln'])

        return page(title       = _("Loans - historical overview"),
                    body        = body,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = argd['ln'],
                    navmenuid   = "yourloans",
                    secure_page_p=1)


class WebInterfaceILLPages(WebInterfaceDirectory):
    """Defines the set of /ill pages."""


    _exports = ['', 'display', 'register_request']

    def index(self, req, form):
        """ The function called by default
        """
        redirect_to_url(req, "%s/ill/display?%s" % (CFG_SITE_URL,
                                                          req.args))

    def display(self, req, form):
        """
        Displays all loans of a given user
        @param ln:  language
        @return the page for inbox
        """

        argd = wash_urlargd(form, {})

        # Check if user is logged
        uid = getUid(req)
        if CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "%s/ill/display" % \
                                       (CFG_SITE_URL,),
                                       navmenuid="ill")
        elif uid == -1 or isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                CFG_SITE_SECURE_URL,
                make_canonical_urlargd({
                    'referer' : "%s/ill/display%s" % (
                        CFG_SITE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})), norobot=True)

        _ = gettext_set_language(argd['ln'])

        user_info = collect_user_info(req)
        if not user_info['precached_useloans']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use ill."))

        body = display_ill_form(ln=argd['ln'])

        return page(title       = _("Interlibrary loan request for books"),
                    body        = body,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = argd['ln'],
                    navmenuid   = "ill")


    def register_request(self, req, form):
        """
        Displays all loans of a given user
        @param ln:  language
        @return the page for inbox
        """


        argd = wash_urlargd(form, {'ln': (str, ""),
                                   'title': (str, ""),
                                   'authors': (str, ""),
                                   'place': (str, ""),
                                   'publisher': (str, ""),
                                   'year': (str, ""),
                                   'edition': (str, ""),
                                   'isbn': (str, ""),
                                   'period_of_interest_from': (str, ""),
                                   'period_of_interest_to': (str, ""),
                                   'additional_comments': (str, ""),
                                   'conditions': (str, ""),
                                   'only_edition': (str, ""),
                                   })

        # Check if user is logged
        uid = getUid(req)
        if CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "%s/ill/register_request" % \
                                       (CFG_SITE_URL,),
                                       navmenuid="ill")
        elif uid == -1 or isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                CFG_SITE_SECURE_URL,
                make_canonical_urlargd({
                    'referer' : "%s/ill/register_request%s" % (
                        CFG_SITE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})), norobot=True)

        _ = gettext_set_language(argd['ln'])

        user_info = collect_user_info(req)
        if not user_info['precached_useloans']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use ill."))

        body = ill_register_request(uid=uid,
                                    title=argd['title'],
                                    authors=argd['authors'],
                                    place=argd['place'],
                                    publisher=argd['publisher'],
                                    year=argd['year'],
                                    edition=argd['edition'],
                                    isbn=argd['isbn'],
                                    period_of_interest_from =  argd['period_of_interest_from'],
                                    period_of_interest_to =  argd['period_of_interest_to'],
                                    additional_comments =  argd['additional_comments'],
                                    conditions = argd['conditions'],
                                    only_edition = argd['only_edition'],
                                    request_type='book',
                                    ln=argd['ln'])

        return page(title       = _("Interlibrary loan request for books"),
                    body        = body,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = argd['ln'],
                    navmenuid   = "ill")



class WebInterfaceHoldingsPages(WebInterfaceDirectory):
    """Defines the set of /holdings pages."""

    _exports = ['', 'display', 'request', 'send', 'ill_request_with_recid', 'ill_register_request_with_recid']

    def __init__(self, recid=-1):
        self.recid = recid


    def index(self, req, form):
        """
        Redirects to display function
        """

        return self.display(req, form)

    def display(self, req, form):
        """
        Show the tab 'holdings'.
        """

        argd = wash_urlargd(form, {'do': (str, "od"),
                                   'ds': (str, "all"),
                                   'nb': (int, 100),
                                   'p': (int, 1),
                                   'voted': (int, -1),
                                   'reported': (int, -1),
                                   })
        _ = gettext_set_language(argd['ln'])

        record_exists_p = record_exists(self.recid)
        if record_exists_p != 1:
            if record_exists_p == -1:
                msg = _("The record has been deleted.")
            else:
                msg = _("Requested record does not seem to exist.")
            msg = '<span class="quicknote">' + msg + '</span>'
            title, description, keywords = \
                   websearch_templates.tmpl_record_page_header_content(req, self.recid, argd['ln'])
            return page(title = title,
                        show_title_p = False,
                        body = msg,
                        description = description,
                        keywords = keywords,
                        uid = getUid(req),
                        language = argd['ln'],
                        req = req,
                        navmenuid='search')

        body = perform_get_holdings_information(self.recid, req, argd['ln'])

        uid = getUid(req)


        user_info = collect_user_info(req)
        (auth_code, auth_msg) = check_user_can_view_record(user_info, self.recid)
        if auth_code and user_info['email'] == 'guest':
            cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {'collection' : guess_primary_collection_of_a_record(self.recid)})
            target = '/youraccount/login' + \
                make_canonical_urlargd({'action': cookie, 'ln' : argd['ln'], 'referer' : \
                CFG_SITE_URL + user_info['uri']}, {})
            return redirect_to_url(req, target, norobot=True)
        elif auth_code:
            return page_not_authorized(req, "../", \
                text = auth_msg)


        unordered_tabs = get_detailed_page_tabs(get_colID(guess_primary_collection_of_a_record(self.recid)),
                                                    self.recid,
                                                    ln=argd['ln'])
        ordered_tabs_id = [(tab_id, values['order']) for (tab_id, values) in unordered_tabs.iteritems()]
        ordered_tabs_id.sort(lambda x, y: cmp(x[1], y[1]))
        link_ln = ''
        if argd['ln'] != CFG_SITE_LANG:
            link_ln = '?ln=%s' % argd['ln']
        tabs = [(unordered_tabs[tab_id]['label'], \
                 '%s/record/%s/%s%s' % (CFG_SITE_URL, self.recid, tab_id, link_ln), \
                 tab_id in ['holdings'],
                 unordered_tabs[tab_id]['enabled']) \
                for (tab_id, _order) in ordered_tabs_id
                if unordered_tabs[tab_id]['visible'] == True]
        top = webstyle_templates.detailed_record_container_top(self.recid,
                                                               tabs,
                                                               argd['ln'])
        bottom = webstyle_templates.detailed_record_container_bottom(self.recid,
                                                                     tabs,
                                                                     argd['ln'])

        title = websearch_templates.tmpl_record_page_header_content(req, self.recid, argd['ln'])[0]
        navtrail = create_navtrail_links(cc=guess_primary_collection_of_a_record(self.recid), ln=argd['ln'])
        navtrail += ' &gt; <a class="navtrail" href="%s/record/%s?ln=%s">'% (CFG_SITE_URL, self.recid, argd['ln'])
        navtrail += title
        navtrail += '</a>'

        return pageheaderonly(title=title,
                              navtrail=navtrail,
                              uid=uid,
                              verbose=1,
                              req=req,
                              metaheaderadd = "<link rel=\"stylesheet\" href=\"%s/img/jquery-ui.css\" type=\"text/css\" />" % CFG_SITE_URL,
                              language=argd['ln'],
                              navmenuid='search',
                              navtrail_append_title_p=0) + \
                              websearch_templates.tmpl_search_pagestart(argd['ln']) + \
                              top + body + bottom + \
                              websearch_templates.tmpl_search_pageend(argd['ln']) + \
                              pagefooteronly(lastupdated=__lastupdated__, language=argd['ln'], req=req)

    # Return the same page wether we ask for /record/123 or /record/123/
    __call__ = index


    def request(self, req, form):
        """
        Show new hold request form.
        """
        argd = wash_urlargd(form, {'ln': (str, ""), 'barcode': (str, "")})

        _ = gettext_set_language(argd['ln'])
        uid = getUid(req)

        body = perform_new_request(recid=self.recid,
                                   barcode=argd['barcode'],
                                   ln=argd['ln'])

        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../holdings/request",
                                       navmenuid = 'yourbaskets')

        if isGuestUser(uid):
            if not CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS:
                return redirect_to_url(req, "%s/youraccount/login%s" % (
                    CFG_SITE_SECURE_URL,
                        make_canonical_urlargd({
                    'referer' : "%s/record/%s/holdings/request%s" % (
                        CFG_SITE_URL,
                        self.recid,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})), norobot=True)


        user_info = collect_user_info(req)
        (auth_code, auth_msg) = check_user_can_view_record(user_info, self.recid)
        if auth_code and user_info['email'] == 'guest':
            cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {'collection' : guess_primary_collection_of_a_record(self.recid)})
            target = '/youraccount/login' + \
                     make_canonical_urlargd({'action': cookie, 'ln' : argd['ln'], 'referer' : \
                CFG_SITE_URL + user_info['uri']}, {})
            return redirect_to_url(req, target, norobot=True)
        elif auth_code:
            return page_not_authorized(req, "../", \
                text = auth_msg)



        unordered_tabs = get_detailed_page_tabs(get_colID(guess_primary_collection_of_a_record(self.recid)),
                                                    self.recid,
                                                    ln=argd['ln'])
        ordered_tabs_id = [(tab_id, values['order']) for (tab_id, values) in unordered_tabs.iteritems()]
        ordered_tabs_id.sort(lambda x, y: cmp(x[1], y[1]))
        link_ln = ''
        if argd['ln'] != CFG_SITE_LANG:
            link_ln = '?ln=%s' % argd['ln']
        tabs = [(unordered_tabs[tab_id]['label'], \
                 '%s/record/%s/%s%s' % (CFG_SITE_URL, self.recid, tab_id, link_ln), \
                 tab_id in ['holdings'],
                 unordered_tabs[tab_id]['enabled']) \
                for (tab_id, _order) in ordered_tabs_id
                if unordered_tabs[tab_id]['visible'] == True]
        top = webstyle_templates.detailed_record_container_top(self.recid,
                                                               tabs,
                                                               argd['ln'])
        bottom = webstyle_templates.detailed_record_container_bottom(self.recid,
                                                                     tabs,
                                                                     argd['ln'])

        title = websearch_templates.tmpl_record_page_header_content(req, self.recid, argd['ln'])[0]
        navtrail = create_navtrail_links(cc=guess_primary_collection_of_a_record(self.recid), ln=argd['ln'])
        navtrail += ' &gt; <a class="navtrail" href="%s/record/%s?ln=%s">'% (CFG_SITE_URL, self.recid, argd['ln'])
        navtrail += title
        navtrail += '</a>'

        return pageheaderonly(title=title,
                              navtrail=navtrail,
                              uid=uid,
                              verbose=1,
                              req=req,
                              metaheaderadd = "<link rel=\"stylesheet\" href=\"%s/img/jquery-ui.css\" type=\"text/css\" />" % CFG_SITE_URL,
                              language=argd['ln'],
                              navmenuid='search',
                              navtrail_append_title_p=0) + \
                              websearch_templates.tmpl_search_pagestart(argd['ln']) + \
                              top + body + bottom + \
                              websearch_templates.tmpl_search_pageend(argd['ln']) + \
                              pagefooteronly(lastupdated=__lastupdated__, language=argd['ln'], req=req)


    def send(self, req, form):
        """
        Create a new hold request.
        """
        argd = wash_urlargd(form, {'period_from': (str, ""),
                                   'period_to': (str, ""),
                                   'barcode': (str, "")
                                   })

        uid = getUid(req)

        body = perform_new_request_send(recid=self.recid,
                                        uid=uid,
                                        period_from=argd['period_from'],
                                        period_to=argd['period_to'],
                                        barcode=argd['barcode'])

        ln = CFG_SITE_LANG
        _ = gettext_set_language(ln)


        user_info = collect_user_info(req)
        (auth_code, auth_msg) = check_user_can_view_record(user_info, self.recid)
        if auth_code and user_info['email'] == 'guest':
            cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {'collection' : guess_primary_collection_of_a_record(self.recid)})
            target = '/youraccount/login' + \
                     make_canonical_urlargd({'action': cookie, 'ln' : argd['ln'], 'referer' : \
                CFG_SITE_URL + user_info['uri']}, {})
            return redirect_to_url(req, target)
        elif auth_code:
            return page_not_authorized(req, "../", \
                text = auth_msg)



        unordered_tabs = get_detailed_page_tabs(get_colID(guess_primary_collection_of_a_record(self.recid)),
                                                    self.recid,
                                                    ln=ln)
        ordered_tabs_id = [(tab_id, values['order']) for (tab_id, values) in unordered_tabs.iteritems()]
        ordered_tabs_id.sort(lambda x, y: cmp(x[1], y[1]))
        link_ln = ''
        if argd['ln'] != CFG_SITE_LANG:
            link_ln = '?ln=%s' % ln
        tabs = [(unordered_tabs[tab_id]['label'], \
                 '%s/record/%s/%s%s' % (CFG_SITE_URL, self.recid, tab_id, link_ln), \
                 tab_id in ['holdings'],
                 unordered_tabs[tab_id]['enabled']) \
                for (tab_id, _order) in ordered_tabs_id
                if unordered_tabs[tab_id]['visible'] == True]
        top = webstyle_templates.detailed_record_container_top(self.recid,
                                                               tabs,
                                                               argd['ln'])
        bottom = webstyle_templates.detailed_record_container_bottom(self.recid,
                                                                     tabs,
                                                                     argd['ln'])

        title = websearch_templates.tmpl_record_page_header_content(req, self.recid, argd['ln'])[0]
        navtrail = create_navtrail_links(cc=guess_primary_collection_of_a_record(self.recid), ln=argd['ln'])
        navtrail += ' &gt; <a class="navtrail" href="%s/record/%s?ln=%s">'% (CFG_SITE_URL, self.recid, argd['ln'])
        navtrail += title
        navtrail += '</a>'

        return pageheaderonly(title=title,
                              navtrail=navtrail,
                              uid=uid,
                              verbose=1,
                              req=req,
                              language=argd['ln'],
                              navmenuid='search',
                              navtrail_append_title_p=0) + \
                              websearch_templates.tmpl_search_pagestart(argd['ln']) + \
                              top + body + bottom + \
                              websearch_templates.tmpl_search_pageend(argd['ln']) + \
                              pagefooteronly(lastupdated=__lastupdated__,
                                             language=argd['ln'], req=req)




    def ill_request_with_recid(self, req, form):
        """
        Show ILL request form.
        """


        argd = wash_urlargd(form, {'ln': (str, "")})

        _ = gettext_set_language(argd['ln'])
        uid = getUid(req)

        body = ill_request_with_recid(recid=self.recid,
                                      ln=argd['ln'])

        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../holdings/ill_request_with_recid",
                                       navmenuid = 'yourbaskets')

        if isGuestUser(uid):
            if not CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS:
                return redirect_to_url(req, "%s/youraccount/login%s" % (
                    CFG_SITE_SECURE_URL,
                        make_canonical_urlargd({
                    'referer' : "%s/record/%s/holdings/ill_request_with_recid%s" % (
                        CFG_SITE_URL,
                        self.recid,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))


        user_info = collect_user_info(req)
        (auth_code, auth_msg) = check_user_can_view_record(user_info, self.recid)
        if auth_code and user_info['email'] == 'guest':
            cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {'collection' : guess_primary_collection_of_a_record(self.recid)})
            target = '/youraccount/login' + \
                     make_canonical_urlargd({'action': cookie, 'ln' : argd['ln'], 'referer' : \
                CFG_SITE_URL + user_info['uri']}, {})
            return redirect_to_url(req, target)
        elif auth_code:
            return page_not_authorized(req, "../", \
                text = auth_msg)



        unordered_tabs = get_detailed_page_tabs(get_colID(guess_primary_collection_of_a_record(self.recid)),
                                                    self.recid,
                                                    ln=argd['ln'])
        ordered_tabs_id = [(tab_id, values['order']) for (tab_id, values) in unordered_tabs.iteritems()]
        ordered_tabs_id.sort(lambda x, y: cmp(x[1], y[1]))
        link_ln = ''
        if argd['ln'] != CFG_SITE_LANG:
            link_ln = '?ln=%s' % argd['ln']
        tabs = [(unordered_tabs[tab_id]['label'], \
                 '%s/record/%s/%s%s' % (CFG_SITE_URL, self.recid, tab_id, link_ln), \
                 tab_id in ['holdings'],
                 unordered_tabs[tab_id]['enabled']) \
                for (tab_id, _order) in ordered_tabs_id
                if unordered_tabs[tab_id]['visible'] == True]
        top = webstyle_templates.detailed_record_container_top(self.recid,
                                                               tabs,
                                                               argd['ln'])
        bottom = webstyle_templates.detailed_record_container_bottom(self.recid,
                                                                     tabs,
                                                                     argd['ln'])

        title = websearch_templates.tmpl_record_page_header_content(req, self.recid, argd['ln'])[0]
        navtrail = create_navtrail_links(cc=guess_primary_collection_of_a_record(self.recid), ln=argd['ln'])
        navtrail += ' &gt; <a class="navtrail" href="%s/record/%s?ln=%s">'% (CFG_SITE_URL, self.recid, argd['ln'])
        navtrail += title
        navtrail += '</a>'

        return pageheaderonly(title=title,
                              navtrail=navtrail,
                              uid=uid,
                              verbose=1,
                              req=req,
                              metaheaderadd = "<link rel=\"stylesheet\" href=\"%s/img/jquery-ui.css\" type=\"text/css\" />" % CFG_SITE_URL,
                              language=argd['ln'],
                              navmenuid='search',
                              navtrail_append_title_p=0) + \
                              websearch_templates.tmpl_search_pagestart(argd['ln']) + \
                              top + body + bottom + \
                              websearch_templates.tmpl_search_pageend(argd['ln']) + \
                              pagefooteronly(lastupdated=__lastupdated__, language=argd['ln'], req=req)


    def ill_register_request_with_recid(self, req, form):
        """
        Register ILL request.
        """

        argd = wash_urlargd(form, {'ln': (str, ""),
                                   'period_of_interest_from': (str, ""),
                                   'period_of_interest_to': (str, ""),
                                   'additional_comments': (str, ""),
                                   'conditions': (str, ""),
                                   'only_edition': (str, ""),
                                   })

        _ = gettext_set_language(argd['ln'])
        uid = getUid(req)

        body = ill_register_request_with_recid(recid=self.recid,
                                               uid=uid,
                                               period_of_interest_from =  argd['period_of_interest_from'],
                                               period_of_interest_to =  argd['period_of_interest_to'],
                                               additional_comments =  argd['additional_comments'],
                                               conditions = argd['conditions'],
                                               only_edition = argd['only_edition'],
                                               ln=argd['ln'])

        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../holdings/ill_request_with_recid",
                                       navmenuid = 'yourbaskets')

        if isGuestUser(uid):
            if not CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS:
                return redirect_to_url(req, "%s/youraccount/login%s" % (
                    CFG_SITE_SECURE_URL,
                        make_canonical_urlargd({
                    'referer' : "%s/record/%s/holdings/ill_request_with_recid%s" % (
                        CFG_SITE_URL,
                        self.recid,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))


        user_info = collect_user_info(req)
        (auth_code, auth_msg) = check_user_can_view_record(user_info, self.recid)
        if auth_code and user_info['email'] == 'guest':
            cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {'collection' : guess_primary_collection_of_a_record(self.recid)})
            target = '/youraccount/login' + \
                     make_canonical_urlargd({'action': cookie, 'ln' : argd['ln'], 'referer' : \
                CFG_SITE_URL + user_info['uri']}, {})
            return redirect_to_url(req, target)
        elif auth_code:
            return page_not_authorized(req, "../", \
                text = auth_msg)



        unordered_tabs = get_detailed_page_tabs(get_colID(guess_primary_collection_of_a_record(self.recid)),
                                                    self.recid,
                                                    ln=argd['ln'])
        ordered_tabs_id = [(tab_id, values['order']) for (tab_id, values) in unordered_tabs.iteritems()]
        ordered_tabs_id.sort(lambda x, y: cmp(x[1], y[1]))
        link_ln = ''
        if argd['ln'] != CFG_SITE_LANG:
            link_ln = '?ln=%s' % argd['ln']
        tabs = [(unordered_tabs[tab_id]['label'], \
                 '%s/record/%s/%s%s' % (CFG_SITE_URL, self.recid, tab_id, link_ln), \
                 tab_id in ['holdings'],
                 unordered_tabs[tab_id]['enabled']) \
                for (tab_id, _order) in ordered_tabs_id
                if unordered_tabs[tab_id]['visible'] == True]
        top = webstyle_templates.detailed_record_container_top(self.recid,
                                                               tabs,
                                                               argd['ln'])
        bottom = webstyle_templates.detailed_record_container_bottom(self.recid,
                                                                     tabs,
                                                                     argd['ln'])

        title = websearch_templates.tmpl_record_page_header_content(req, self.recid, argd['ln'])[0]
        navtrail = create_navtrail_links(cc=guess_primary_collection_of_a_record(self.recid), ln=argd['ln'])
        navtrail += ' &gt; <a class="navtrail" href="%s/record/%s?ln=%s">'% (CFG_SITE_URL, self.recid, argd['ln'])
        navtrail += title
        navtrail += '</a>'

        return pageheaderonly(title=title,
                              navtrail=navtrail,
                              uid=uid,
                              verbose=1,
                              req=req,
                              language=argd['ln'],
                              navmenuid='search',
                              navtrail_append_title_p=0) + \
                              websearch_templates.tmpl_search_pagestart(argd['ln']) + \
                              top + body + bottom + \
                              websearch_templates.tmpl_search_pageend(argd['ln']) + \
                              pagefooteronly(lastupdated=__lastupdated__, language=argd['ln'], req=req)
