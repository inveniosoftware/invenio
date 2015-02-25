# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.


"""Invenio Bibcirculation User (URLs) Interface.
   When applicable, methods should be renamed, refactored and
   appropriate documentation added.
"""

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

import time
import cgi
from six import iteritems
from invenio.config import CFG_SITE_LANG, \
                           CFG_SITE_URL, \
                           CFG_SITE_SECURE_URL, \
                           CFG_ACCESS_CONTROL_LEVEL_SITE, \
                           CFG_SITE_RECORD, \
                           CFG_CERN_SITE
from invenio.legacy.webuser import getUid, page_not_authorized, isGuestUser, \
                            collect_user_info
from invenio.legacy.webpage import page, pageheaderonly, pagefooteronly
from invenio.ext.email import send_email
from invenio.legacy.search_engine import create_navtrail_links, \
     guess_primary_collection_of_a_record, \
     check_user_can_view_record, \
     record_exists, get_fieldvalues
from invenio.utils.url import redirect_to_url, \
                             make_canonical_urlargd
from invenio.base.i18n import gettext_set_language
from invenio.ext.legacy.handler import wash_urlargd, WebInterfaceDirectory
from invenio.legacy.websearch.adminlib import get_detailed_page_tabs
from invenio.modules.access.local_config import VIEWRESTRCOLL
from invenio.modules.access.mailcookie import mail_cookie_create_authorize_action
import invenio.legacy.template

import invenio.legacy.bibcirculation.db_layer as db
from invenio.legacy.bibcirculation.utils import book_title_from_MARC, search_user
from invenio.legacy.bibcirculation.api import perform_new_request, \
                                   perform_new_request_send, \
                                   perform_book_proposal_send, \
                                   perform_get_holdings_information, \
                                   perform_borrower_loans, \
                                   perform_loanshistoricaloverview, \
                                   ill_register_request, \
                                   ill_request_with_recid, \
                                   ill_register_request_with_recid
from invenio.legacy.bibcirculation.adminlib import is_adminuser, \
                                           load_template
from invenio.legacy.bibcirculation.config import CFG_BIBCIRCULATION_ILLS_EMAIL, \
                                          CFG_BIBCIRCULATION_ILL_STATUS_NEW, \
                                          CFG_BIBCIRCULATION_ACQ_STATUS_NEW, \
                                          AMZ_ACQUISITION_IDENTIFIER_TAG

from invenio.modules.collections.models import Collection
get_colID = lambda name: Collection.query.filter_by(name=name).value('id')


webstyle_templates = invenio.legacy.template.load('webstyle')
websearch_templates = invenio.legacy.template.load('websearch')
bc_templates = invenio.legacy.template.load('bibcirculation')

class WebInterfaceYourLoansPages(WebInterfaceDirectory):
    """Defines the set of /yourloans pages."""

    _exports = ['', 'display', 'loanshistoricaloverview']

    def __init__(self, recid=-1):
        self.recid = recid

    def index(self, req, form):
        """
            The function called by default
        """
        redirect_to_url(req, "%s/yourloans/display?%s" % (CFG_SITE_SECURE_URL,
                                                          req.args))

    def display(self, req, form):
        """
        Displays all loans of a given user
        @param ln:  language
        @return the page for inbox
        """

        argd = wash_urlargd(form, {'barcode': (str, ""),
                                   'borrower_id': (int, 0),
                                   'request_id': (int, 0),
                                   'action': (str, "")})

        # Check if user is logged
        uid = getUid(req)
        if CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "%s/yourloans/display" % \
                                       (CFG_SITE_SECURE_URL,),
                                       navmenuid="yourloans")
        elif uid == -1 or isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                CFG_SITE_SECURE_URL,
                make_canonical_urlargd({
                    'referer' : "%s/yourloans/display%s" % (
                        CFG_SITE_SECURE_URL, make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})),
                    norobot=True)

        _ = gettext_set_language(argd['ln'])

        user_info = collect_user_info(req)
        if not user_info['precached_useloans']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use loans."))

        body = perform_borrower_loans(uid=uid,
                                      barcode=argd['barcode'],
                                      borrower_id=argd['borrower_id'],
                                      request_id=argd['request_id'],
                                      action=argd['action'],
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
                                       (CFG_SITE_SECURE_URL,),
                                       navmenuid="yourloans")
        elif uid == -1 or isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                CFG_SITE_SECURE_URL,
                make_canonical_urlargd({
                    'referer' : "%s/yourloans/loanshistoricaloverview%s" % (
                        CFG_SITE_SECURE_URL,
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


    _exports = ['', 'register_request', 'book_request_step1',
                'book_request_step2','book_request_step3',
                'article_request_step1', 'article_request_step2',
                'article_request_step3', 'purchase_request_step1',
                'purchase_request_step2']

    def index(self, req, form):
        """ The function called by default
        """
        redirect_to_url(req, "%s/ill/book_request_step1?%s" % (CFG_SITE_SECURE_URL,
                                                          req.args))

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
                                       (CFG_SITE_SECURE_URL,),
                                       navmenuid="ill")
        elif uid == -1 or isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                CFG_SITE_SECURE_URL,
                make_canonical_urlargd({
                    'referer' : "%s/ill/register_request%s" % (
                        CFG_SITE_SECURE_URL,
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
                        period_of_interest_from=argd['period_of_interest_from'],
                        period_of_interest_to=argd['period_of_interest_to'],
                        additional_comments=argd['additional_comments'],
                        conditions=argd['conditions'],
                        only_edition=argd['only_edition'],
                        request_type='book',
                        ln=argd['ln'])

        return page(title       = _("Interlibrary loan request for books"),
                    body        = body,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = argd['ln'],
                    navmenuid   = "ill")

    def book_request_step1(self, req, form):
        """
        Displays all loans of a given user
        @param ln:  language
        @return the page for inbox
        """

        argd = wash_urlargd(form, {})

        # Check if user is logged
        uid = getUid(req)
        if CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "%s/ill/book_request_step1" % \
                                       (CFG_SITE_SECURE_URL,),
                                       navmenuid="ill")
        elif uid == -1 or isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                CFG_SITE_SECURE_URL,
                make_canonical_urlargd({
                    'referer' : "%s/ill/book_request_step1%s" % (
                        CFG_SITE_SECURE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})), norobot=True)

        _ = gettext_set_language(argd['ln'])

        user_info = collect_user_info(req)
        if not user_info['precached_useloans']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use ill."))

        ### get borrower_id ###
        borrower_id = search_user('email', user_info['email'])
        if borrower_id == ():
            body = "wrong user id"
        else:
            body = bc_templates.tmpl_register_ill_request_with_no_recid_step1([], None, False, argd['ln'])

        return page(title       = _("Interlibrary loan request for books"),
                    body        = body,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = argd['ln'],
                    navmenuid   = "ill")

    def book_request_step2(self, req, form):
        """
        Displays all loans of a given user
        @param ln:  language
        @return the page for inbox
        """

        argd = wash_urlargd(form, {'title': (str, None), 'authors': (str, None),
            'place': (str, None), 'publisher': (str, None), 'year': (str, None),
            'edition': (str, None), 'isbn': (str, None), 'budget_code': (str, ''),
            'period_of_interest_from': (str, None), 'period_of_interest_to': (str, None),
            'additional_comments': (str, None), 'only_edition': (str, 'No'),'ln': (str, "en")})

        title = argd['title']
        authors = argd['authors']
        place = argd['place']
        publisher = argd['publisher']
        year = argd['year']
        edition = argd['edition']
        isbn = argd['isbn']
        budget_code = argd['budget_code']
        period_of_interest_from = argd['period_of_interest_from']
        period_of_interest_to = argd['period_of_interest_to']
        additional_comments = argd['additional_comments']
        only_edition = argd['only_edition']
        ln = argd['ln']

        if title is not None:
            title = title.strip()
        if authors is not None:
            authors = authors.strip()
        if place is not None:
            place = place.strip()
        if publisher is not None:
            publisher = publisher.strip()
        if year is not None:
            year = year.strip()
        if edition is not None:
            edition =  edition.strip()
        if isbn is not None:
            isbn = isbn.strip()
        if budget_code is not None:
            budget_code = budget_code.strip()
        if period_of_interest_from is not None:
            period_of_interest_from = period_of_interest_from.strip()
        if period_of_interest_to is not None:
            period_of_interest_to = period_of_interest_to.strip()

        # Check if user is logged
        uid = getUid(req)
        if CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "%s/ill/book_request_step2" % \
                                       (CFG_SITE_URL,),
                                       navmenuid="ill")
        elif uid == -1 or isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                CFG_SITE_SECURE_URL,
                make_canonical_urlargd({
                    'referer' : "%s/ill/book_request_step2%s" % (
                        CFG_SITE_SECURE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : ln}, {})), norobot=True)

        _ = gettext_set_language(ln)

        user_info = collect_user_info(req)
        if not user_info['precached_useloans']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use ill."))

        if CFG_CERN_SITE:
            borrower = search_user('ccid', user_info['external_personid'])
        else:
            borrower = search_user('email', user_info['email'])

        if borrower != ():
            borrower_id = borrower[0][0]

            book_info = (title, authors, place, publisher,
                         year, edition, isbn)
            user_info = db.get_borrower_data_by_id(borrower_id)

            request_details = (budget_code, period_of_interest_from,
                               period_of_interest_to, additional_comments,
                               only_edition)
            body = bc_templates.tmpl_register_ill_request_with_no_recid_step3(
                                        book_info, user_info, request_details, False, ln)

        else:
            body = "wrong user id"

        return page(title       = _("Interlibrary loan request for books"),
                    body        = body,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = ln,
                    navmenuid   = "ill")

    def book_request_step3(self, req, form):
        """
        Displays all loans of a given user
        @param ln:  language
        @return the page for inbox
        """

        argd = wash_urlargd(form, {'title': (str, None), 'authors': (str, None),
            'place': (str, None), 'publisher': (str, None), 'year': (str, None),
            'edition': (str, None), 'isbn': (str, None), 'borrower_id': (str, None),
            'budget_code': (str, ''), 'period_of_interest_from': (str, None),
            'period_of_interest_to': (str, None), 'additional_comments': (str, None),
            'only_edition': (str, None), 'ln': (str, "en")})

        title = argd['title']
        authors = argd['authors']
        place = argd['place']
        publisher = argd['publisher']
        year = argd['year']
        edition = argd['edition']
        isbn = argd['isbn']

        borrower_id = argd['borrower_id']

        budget_code = argd['budget_code']
        period_of_interest_from = argd['period_of_interest_from']
        period_of_interest_to = argd['period_of_interest_to']
        library_notes = argd['additional_comments']
        only_edition = argd['only_edition']
        ln = argd['ln']

        book_info = (title, authors, place, publisher, year, edition, isbn)

        # Check if user is logged
        uid = getUid(req)
        if CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "%s/ill/book_request_step2" % \
                                       (CFG_SITE_URL,),
                                       navmenuid="ill")
        elif uid == -1 or isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                CFG_SITE_SECURE_URL,
                make_canonical_urlargd({
                    'referer' : "%s/ill/book_request_step2%s" % (
                        CFG_SITE_SECURE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})), norobot=True)

        _ = gettext_set_language(argd['ln'])

        user_info = collect_user_info(req)
        if not user_info['precached_useloans']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use ill."))

        book_info = {'title': title, 'authors': authors, 'place': place,
                     'publisher': publisher, 'year' : year,
                     'edition': edition, 'isbn' : isbn}

        ill_request_notes = {}
        if library_notes:
            ill_request_notes[time.strftime("%Y-%m-%d %H:%M:%S")] = str(library_notes)

        ### budget_code ###
        db.ill_register_request_on_desk(borrower_id, book_info,
                                        period_of_interest_from,
                                        period_of_interest_to,
                                        CFG_BIBCIRCULATION_ILL_STATUS_NEW,
                                        str(ill_request_notes), only_edition,
                                        'book', budget_code)

        infos = []
        infos.append('Interlibrary loan request done.')
        body = bc_templates.tmpl_infobox(infos, ln)

        return page(title       = _("Interlibrary loan request for books"),
                    body        = body,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = argd['ln'],
                    navmenuid   = "ill")

    def article_request_step1(self, req, form):
        """
        Displays all loans of a given user
        @param ln:  language
        @return the page for inbox
        """

        argd = wash_urlargd(form, {})

        # Check if user is logged
        uid = getUid(req)
        if CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "%s/ill/article_request_step1" % \
                                       (CFG_SITE_URL,),
                                       navmenuid="ill")
        elif uid == -1 or isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                CFG_SITE_SECURE_URL,
                make_canonical_urlargd({
                    'referer' : "%s/ill/article_request_step1%s" % (
                        CFG_SITE_SECURE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})), norobot=True)

        _ = gettext_set_language(argd['ln'])

        user_info = collect_user_info(req)
        if not user_info['precached_useloans']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use ill."))

        ### get borrower_id ###
        borrower_id = search_user('email', user_info['email'])
        if borrower_id == ():
            body = "Wrong user id"
        else:
            body = bc_templates.tmpl_register_ill_article_request_step1([], False, argd['ln'])

        return page(title       = _("Interlibrary loan request for articles"),
                    body        = body,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = argd['ln'],
                    navmenuid   = "ill")

    def article_request_step2(self, req, form):
        """
        Displays all loans of a given user
        @param ln:  language
        @return the page for inbox
        """

        argd = wash_urlargd(form, {'periodical_title': (str, None), 'article_title': (str, None),
            'author': (str, None), 'report_number': (str, None), 'volume': (str, None),
            'issue': (str, None), 'page': (str, None), 'year': (str, None),
            'budget_code': (str, ''), 'issn': (str, None),
            'period_of_interest_from': (str, None), 'period_of_interest_to': (str, None),
            'additional_comments': (str, None), 'key': (str, None), 'string': (str, None),
            'ln': (str, "en")})

        # Check if user is logged
        uid = getUid(req)
        if CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "%s/ill/article_request_step2" % \
                                       (CFG_SITE_URL,),
                                       navmenuid="ill")
        elif uid == -1 or isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                CFG_SITE_SECURE_URL,
                make_canonical_urlargd({
                    'referer' : "%s/ill/article_request_step2%s" % (
                        CFG_SITE_SECURE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})), norobot=True)

        _ = gettext_set_language(argd['ln'])

        user_info = collect_user_info(req)
        if not user_info['precached_useloans']:
            return page_not_authorized(req, "../", \
                                text = _("You are not authorized to use ill."))

        borrower_id = search_user('email', user_info['email'])
        if borrower_id != ():
            borrower_id = borrower_id[0][0]
            notes = argd['additional_comments']
            ill_request_notes = {}
            if notes:
                ill_request_notes[time.strftime("%Y-%m-%d %H:%M:%S")] = str(notes)

            item_info = {'periodical_title': argd['periodical_title'],
                'title': argd['article_title'], 'authors': argd['author'],
                'place': "", 'publisher': "", 'year' : argd['year'],
                'edition': "", 'issn' : argd['issn'], 'volume': argd['volume'],
                'page': argd['page'], 'issue': argd['issue'] }

            ### budget_code ###
            db.ill_register_request_on_desk(borrower_id, item_info,
                                    argd['period_of_interest_from'],
                                    argd['period_of_interest_to'],
                                    CFG_BIBCIRCULATION_ILL_STATUS_NEW,
                                    str(ill_request_notes), 'No', 'article',
                                    argd['budget_code'])

            infos = []
            infos.append('Interlibrary loan request done.')
            body = bc_templates.tmpl_infobox(infos, argd['ln'])

        else:
            body = _("Wrong user id")

        return page(title       = _("Interlibrary loan request for books"),
                    body        = body,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = argd['ln'],
                    navmenuid   = "ill")

    def purchase_request_step1(self, req, form):

        argd = wash_urlargd(form, {'type': (str, 'acq-book'), 'recid': (str, ''),
                'title': (str, ''), 'authors': (str, ''), 'place': (str, ''),
                'publisher': (str, ''), 'year': (str, ''), 'edition': (str, ''),
                'this_edition_only': (str, 'No'),
                'isbn': (str, ''), 'standard_number': (str, ''),
                'budget_code': (str, ''), 'cash': (str, 'No'),
                'period_of_interest_from': (str, ''),
                'period_of_interest_to': (str, ''),
                'additional_comments': (str, ''), 'ln': (str, 'en')})

        request_type = argd['type'].strip()
        recid = argd['recid'].strip()
        title = argd['title'].strip()
        authors = argd['authors'].strip()
        place = argd['place'].strip()
        publisher = argd['publisher'].strip()
        year = argd['year'].strip()
        edition = argd['edition'].strip()
        this_edition_only = argd['this_edition_only'].strip()
        isbn = argd['isbn'].strip()
        standard_number = argd['standard_number'].strip()
        budget_code = argd['budget_code'].strip()
        cash = argd['cash'] == 'Yes'
        period_of_interest_from = argd['period_of_interest_from'].strip()
        period_of_interest_to = argd['period_of_interest_to'].strip()
        additional_comments = argd['additional_comments'].strip()
        ln = argd['ln']

        if not recid:
            fields = (request_type, title, authors, place, publisher, year, edition,
                      this_edition_only, isbn, standard_number, budget_code,
                      cash, period_of_interest_from, period_of_interest_to,
                      additional_comments)
        else:
            fields = (request_type, recid, budget_code, cash,
                      period_of_interest_from, period_of_interest_to,
                      additional_comments)

        # Check if user is logged
        uid = getUid(req)
        if CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "%s/ill/purchase_request_step1" % \
                                       (CFG_SITE_URL,),
                                       navmenuid="ill")
        elif uid == -1 or isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                CFG_SITE_SECURE_URL,
                make_canonical_urlargd({
                    'referer' : "%s/ill/purchase_request_step1%s" % (
                        CFG_SITE_SECURE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})), norobot=True)

        _ = gettext_set_language(argd['ln'])

        user_info = collect_user_info(req)
        if not user_info['precached_useloans']:
            return page_not_authorized(req, "../", \
                                text = _("You are not authorized to use ill."))

        ### get borrower_id ###
        borrower_id = search_user('email', user_info['email'])
        if borrower_id == ():
            body = "Wrong user ID"
        else:
            (auth_code, _auth_message) = is_adminuser(req)
            body = bc_templates.tmpl_register_purchase_request_step1([], fields,
                                                      auth_code == 0, ln)

        return page(title       = _("Purchase request"),
                    body        = body,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = argd['ln'],
                    navmenuid   = "ill")

    def purchase_request_step2(self, req, form):

        argd = wash_urlargd(form, {'type': (str, 'acq-book'), 'recid': (str, ''),
                'title': (str, ''), 'authors': (str, ''), 'place': (str, ''),
                'publisher': (str, ''), 'year': (str, ''), 'edition': (str, ''),
                'this_edition_only': (str, 'No'),
                'isbn': (str, ''), 'standard_number': (str, ''),
                'budget_code': (str, ''), 'cash': (str, 'No'),
                'period_of_interest_from': (str, ''),
                'period_of_interest_to': (str, ''),
                'additional_comments': (str, ''), 'ln': (str, "en")})

        request_type = argd['type'].strip()
        recid = argd['recid'].strip()
        title = argd['title'].strip()
        authors = argd['authors'].strip()
        place = argd['place'].strip()
        publisher = argd['publisher'].strip()
        year = argd['year'].strip()
        edition = argd['edition'].strip()
        this_edition_only = argd['this_edition_only'].strip()
        isbn = argd['isbn'].strip()
        standard_number = argd['standard_number'].strip()
        budget_code = argd['budget_code'].strip()
        cash = argd['cash'] == 'Yes'
        period_of_interest_from = argd['period_of_interest_from'].strip()
        period_of_interest_to = argd['period_of_interest_to'].strip()
        additional_comments = argd['additional_comments'].strip()
        ln = argd['ln']

        if recid:
            fields = (request_type, recid, budget_code, cash,
                      period_of_interest_from, period_of_interest_to,
                      additional_comments)
        else:
            fields = (request_type, title, authors, place, publisher, year, edition,
                      this_edition_only, isbn, standard_number, budget_code,
                      cash, period_of_interest_from, period_of_interest_to,
                      additional_comments)

        # Check if user is logged
        uid = getUid(req)
        if CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "%s/ill/purchase_request_step1" % \
                                       (CFG_SITE_URL,),
                                       navmenuid="ill")
        elif uid == -1 or isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                CFG_SITE_SECURE_URL,
                make_canonical_urlargd({
                    'referer' : "%s/ill/purchase_request_step2%s" % (
                        CFG_SITE_SECURE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : ln}, {})), norobot=True)

        _ = gettext_set_language(ln)

        user_info = collect_user_info(req)
        if not user_info['precached_useloans']:
            return page_not_authorized(req, "../", \
                                text = _("You are not authorized to use ill."))

        infos = []

        if budget_code == '' and not cash:
            infos.append(_("Payment method information is mandatory. \
            Please, type your budget code or tick the 'cash' checkbox."))
            (auth_code, _auth_message) = is_adminuser(req)
            body = bc_templates.tmpl_register_purchase_request_step1(infos, fields,
                                                                 auth_code == 0, ln)
        else:
            if recid:
                item_info = "{'recid': " + str(recid) + "}"
                title = book_title_from_MARC(recid)
            else:
                item_info = {'title': title, 'authors': authors, 'place': place,
                             'publisher': publisher, 'year' : year,
                             'edition': edition, 'isbn' : isbn,
                             'standard_number': standard_number}


            ill_request_notes = {}
            if additional_comments:
                ill_request_notes[time.strftime("%Y-%m-%d %H:%M:%S")] \
                                                      = str(additional_comments)

            if cash and budget_code == '':
                budget_code = 'cash'

            borrower_email = db.get_invenio_user_email(uid)
            borrower_id = db.get_borrower_id_by_email(borrower_email)
            db.ill_register_request_on_desk(borrower_id, item_info,
                                            period_of_interest_from,
                                            period_of_interest_to,
                                            CFG_BIBCIRCULATION_ACQ_STATUS_NEW,
                                            str(ill_request_notes),
                                            this_edition_only, request_type,
                                            budget_code)

            msg_for_user = load_template('purchase_notification') % title
            send_email(fromaddr = CFG_BIBCIRCULATION_ILLS_EMAIL,
                       toaddr   = borrower_email,
                       subject  = _("Your book purchase request"),
                       header = '', footer = '',
                       content  = msg_for_user,
                       attempt_times=1,
                       attempt_sleeptime=10
                      )

            body = bc_templates.tmpl_message_purchase_request_send_ok_other(ln=ln)

        return page(title=_("Register purchase request"),
                    uid=uid,
                    req=req,
                    body=body,
                    language=ln,
                    metaheaderadd='<link rel="stylesheet" ' \
                                        'href="%s/vendors/jquery-ui/themes/redmond/jquery-ui.min.css" ' \
                                        'type="text/css" />' % CFG_SITE_URL,
                    lastupdated=__lastupdated__)


class WebInterfaceHoldingsPages(WebInterfaceDirectory):
    """Defines the set of /holdings pages."""

    _exports = ['', 'display', 'request', 'send',
                'ill_request_with_recid',
                'ill_register_request_with_recid']

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
                                   'p' : (int, 1),
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
                websearch_templates.tmpl_record_page_header_content(req,
                                                                    self.recid,
                                                                    argd['ln'])
            return page(title = title,
                        show_title_p = False,
                        body = msg,
                        description = description,
                        keywords = keywords,
                        uid = getUid(req),
                        language = argd['ln'],
                        req = req,
                        navmenuid='search')

        # Check if the record has been harvested from Amazon. If true, the control flow will be
        # that of patron driven acquisition.
        acquisition_src = get_fieldvalues(self.recid, AMZ_ACQUISITION_IDENTIFIER_TAG)
        if acquisition_src and acquisition_src[0].startswith('AMZ') and db.has_copies(self.recid) == False:
            body = perform_get_holdings_information(self.recid, req, action="proposal", ln=argd['ln'])
        else:
            body = perform_get_holdings_information(self.recid, req, action="borrowal", ln=argd['ln'])

        uid = getUid(req)

        user_info = collect_user_info(req)
        (auth_code, auth_msg) = check_user_can_view_record(user_info, self.recid)
        if auth_code and user_info['email'] == 'guest':
            cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL,
                                {'collection': guess_primary_collection_of_a_record(self.recid)})
            target = CFG_SITE_SECURE_URL + '/youraccount/login' + \
                    make_canonical_urlargd({'action': cookie, 'ln': argd['ln'],
                                'referer': CFG_SITE_SECURE_URL + user_info['uri']}, {})
            return redirect_to_url(req, target, norobot=True)
        elif auth_code:
            return page_not_authorized(req, "../", text=auth_msg)


        unordered_tabs = get_detailed_page_tabs(get_colID(\
                    guess_primary_collection_of_a_record(self.recid)),
                    self.recid, ln=argd['ln'])
        ordered_tabs_id = [(tab_id, values['order']) for (tab_id, values) in iteritems(unordered_tabs)]
        ordered_tabs_id.sort(lambda x, y: cmp(x[1], y[1]))
        link_ln = ''
        if argd['ln'] != CFG_SITE_LANG:
            link_ln = '?ln=%s' % argd['ln']
        tabs = [(unordered_tabs[tab_id]['label'], \
                 '%s/%s/%s/%s%s' % (CFG_SITE_SECURE_URL, CFG_SITE_RECORD, self.recid, tab_id, link_ln), \
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
        navtrail += ' &gt; <a class="navtrail" href="%s/%s/%s?ln=%s">'% (CFG_SITE_SECURE_URL, CFG_SITE_RECORD, self.recid, argd['ln'])
        navtrail += cgi.escape(title)
        navtrail += '</a>'

        return pageheaderonly(title=title,
                              navtrail=navtrail,
                              uid=uid,
                              verbose=1,
                              req=req,
                              metaheaderadd = "<link rel=\"stylesheet\" href=\"%s/vendors/jquery-ui/themes/redmond/jquery-ui.min.css\" type=\"text/css\" />" % CFG_SITE_SECURE_URL,
                              language=argd['ln'],
                              navmenuid='search',
                              navtrail_append_title_p=0) + \
                              websearch_templates.tmpl_search_pagestart(argd['ln']) + \
                              top + body + bottom + \
                              websearch_templates.tmpl_search_pageend(argd['ln']) + \
                              pagefooteronly(lastupdated=__lastupdated__, language=argd['ln'], req=req)

    # Return the same page wether we ask for /CFG_SITE_RECORD/123 or /CFG_SITE_RECORD/123/
    __call__ = index


    def request(self, req, form):
        """
        Show new hold request form.
        """
        argd = wash_urlargd(form, {'ln': (str, ""), 'barcode': (str, ""), 'act': (str, "")})

        _ = gettext_set_language(argd['ln'])

        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../holdings/request",
                                       navmenuid = 'yourbaskets')

        if isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                CFG_SITE_SECURE_URL,
                    make_canonical_urlargd({
                'referer' : "%s/%s/%s/holdings/request%s" % (
                    CFG_SITE_SECURE_URL,
                    CFG_SITE_RECORD,
                    self.recid,
                    make_canonical_urlargd(argd, {})),
                "ln" : argd['ln']}, {})), norobot=True)

        user_info = collect_user_info(req)
        (auth_code, auth_msg) = check_user_can_view_record(user_info, self.recid)
        if auth_code and user_info['email'] == 'guest':
            cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {'collection' : guess_primary_collection_of_a_record(self.recid)})
            target = CFG_SITE_SECURE_URL + '/youraccount/login' + \
                     make_canonical_urlargd({'action': cookie, 'ln' : argd['ln'],
                                             'referer': CFG_SITE_SECURE_URL + user_info['uri']
                                            }, {})
            return redirect_to_url(req, target, norobot=True)
        elif auth_code:
            return page_not_authorized(req, "../", \
                text = auth_msg)

        act = "borrowal"
        if argd['act'] == 'pr':
            act = "proposal"
        if argd['act'] == 'pu':
            act = "purchase"
        body = perform_new_request(recid=self.recid,
                                   barcode=argd['barcode'],
                                   action=act,
                                   ln=argd['ln'])

        unordered_tabs = get_detailed_page_tabs(get_colID(guess_primary_collection_of_a_record(self.recid)), self.recid, ln=argd['ln'])
        ordered_tabs_id = [(tab_id, values['order']) for (tab_id, values) in iteritems(unordered_tabs)]
        ordered_tabs_id.sort(lambda x, y: cmp(x[1], y[1]))
        link_ln = ''
        if argd['ln'] != CFG_SITE_LANG:
            link_ln = '?ln=%s' % argd['ln']
        tabs = [(unordered_tabs[tab_id]['label'], \
                 '%s/%s/%s/%s%s' % (CFG_SITE_SECURE_URL, CFG_SITE_RECORD, self.recid, tab_id, link_ln), \
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
        navtrail += ' &gt; <a class="navtrail" href="%s/%s/%s?ln=%s">'% (CFG_SITE_SECURE_URL, CFG_SITE_RECORD, self.recid, argd['ln'])
        navtrail += cgi.escape(title)
        navtrail += '</a>'

        return pageheaderonly(title=title,
                              navtrail=navtrail,
                              uid=uid,
                              verbose=1,
                              req=req,
                              metaheaderadd = "<link rel=\"stylesheet\" href=\"%s/vendors/jquery-ui/themes/redmond/jquery-ui.min.css\" type=\"text/css\" />" % CFG_SITE_SECURE_URL,
                              language=argd['ln'],
                              navmenuid='search',
                              navtrail_append_title_p=0) + \
                              websearch_templates.tmpl_search_pagestart(argd['ln']) + \
                              top + body + bottom + \
                              websearch_templates.tmpl_search_pageend(argd['ln']) + \
                              pagefooteronly(lastupdated=__lastupdated__, language=argd['ln'], req=req)

    def send(self, req, form):
        """
        Create a new hold request and if the 'act' parameter is "pr"(proposal),
        also send a confirmation email with the proposal.
        """
        argd = wash_urlargd(form, {'period_from': (str, ""),
                                   'period_to': (str, ""),
                                   'barcode': (str, ""),
                                   'act': (str, ""),
                                   'remarks': (str, "")
                                   })

        ln = CFG_SITE_LANG
        _ = gettext_set_language(ln)

        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../holdings/request",
                                       navmenuid = 'yourbaskets')

        if isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                CFG_SITE_SECURE_URL,
                    make_canonical_urlargd({
                'referer' : "%s/%s/%s/holdings/request%s" % (
                    CFG_SITE_SECURE_URL,
                    CFG_SITE_RECORD,
                    self.recid,
                    make_canonical_urlargd(argd, {})),
                "ln" : argd['ln']}, {})), norobot=True)

        user_info = collect_user_info(req)
        (auth_code, auth_msg) = check_user_can_view_record(user_info, self.recid)
        if auth_code and user_info['email'] == 'guest':
            cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {'collection' : guess_primary_collection_of_a_record(self.recid)})
            target = CFG_SITE_SECURE_URL + '/youraccount/login' + \
                     make_canonical_urlargd({'action': cookie, 'ln' : argd['ln'], 'referer' : \
                CFG_SITE_SECURE_URL + user_info['uri']}, {})
            return redirect_to_url(req, target)
        elif auth_code:
            return page_not_authorized(req, "../", \
                text = auth_msg)

        period_from = argd['period_from']
        period_to = argd['period_to']
        period_from = period_from.strip()
        period_to = period_to.strip()
        barcode = argd['barcode']

        if argd['act'] == 'pr':
            body = perform_book_proposal_send(uid=uid,
                                              recid=self.recid,
                                              period_from=argd['period_from'],
                                              period_to=argd['period_to'],
                                              remarks=argd['remarks'].strip())
        else:
            body = perform_new_request_send(recid=self.recid,
                                            uid=uid,
                                            period_from=argd['period_from'],
                                            period_to=argd['period_to'],
                                            barcode=barcode)

        unordered_tabs = get_detailed_page_tabs(get_colID(guess_primary_collection_of_a_record(self.recid)), self.recid, ln=ln)
        ordered_tabs_id = [(tab_id, values['order']) for (tab_id, values) in iteritems(unordered_tabs)]
        ordered_tabs_id.sort(lambda x, y: cmp(x[1], y[1]))
        link_ln = ''
        if argd['ln'] != CFG_SITE_LANG:
            link_ln = '?ln=%s' % ln
        tabs = [(unordered_tabs[tab_id]['label'], \
                 '%s/%s/%s/%s%s' % (CFG_SITE_SECURE_URL, CFG_SITE_RECORD, self.recid, tab_id, link_ln), \
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
        navtrail += ' &gt; <a class="navtrail" href="%s/%s/%s?ln=%s">'% (CFG_SITE_SECURE_URL, CFG_SITE_RECORD, self.recid, argd['ln'])
        navtrail += cgi.escape(title)
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
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                CFG_SITE_SECURE_URL,
                    make_canonical_urlargd({
                'referer' : "%s/%s/%s/holdings/ill_request_with_recid%s" % (
                    CFG_SITE_SECURE_URL,
                    CFG_SITE_RECORD,
                    self.recid,
                    make_canonical_urlargd(argd, {})),
                "ln" : argd['ln']}, {})))


        user_info = collect_user_info(req)
        (auth_code, auth_msg) = check_user_can_view_record(user_info, self.recid)
        if auth_code and user_info['email'] == 'guest':
            cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {'collection' : guess_primary_collection_of_a_record(self.recid)})
            target = CFG_SITE_SECURE_URL + '/youraccount/login' + \
                     make_canonical_urlargd({'action': cookie, 'ln' : argd['ln'], 'referer' : \
                CFG_SITE_SECURE_URL + user_info['uri']}, {})
            return redirect_to_url(req, target)
        elif auth_code:
            return page_not_authorized(req, "../", \
                text = auth_msg)



        unordered_tabs = get_detailed_page_tabs(get_colID(guess_primary_collection_of_a_record(self.recid)),
                                                    self.recid,
                                                    ln=argd['ln'])
        ordered_tabs_id = [(tab_id, values['order']) for (tab_id, values) in iteritems(unordered_tabs)]
        ordered_tabs_id.sort(lambda x, y: cmp(x[1], y[1]))
        link_ln = ''
        if argd['ln'] != CFG_SITE_LANG:
            link_ln = '?ln=%s' % argd['ln']
        tabs = [(unordered_tabs[tab_id]['label'], \
                 '%s/%s/%s/%s%s' % (CFG_SITE_SECURE_URL, CFG_SITE_RECORD, self.recid, tab_id, link_ln), \
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
        navtrail += ' &gt; <a class="navtrail" href="%s/%s/%s?ln=%s">'% (CFG_SITE_SECURE_URL, CFG_SITE_RECORD, self.recid, argd['ln'])
        navtrail += cgi.escape(title)
        navtrail += '</a>'

        return pageheaderonly(title=title,
                              navtrail=navtrail,
                              uid=uid,
                              verbose=1,
                              req=req,
                              metaheaderadd = "<link rel=\"stylesheet\" href=\"%s/vendors/jquery-ui/themes/redmond/jquery-ui.css\" type=\"text/css\" />" % CFG_SITE_SECURE_URL,
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
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                CFG_SITE_SECURE_URL,
                    make_canonical_urlargd({
                'referer' : "%s/%s/%s/holdings/ill_request_with_recid%s" % (
                    CFG_SITE_SECURE_URL,
                    CFG_SITE_RECORD,
                    self.recid,
                    make_canonical_urlargd(argd, {})),
                "ln" : argd['ln']}, {})))


        user_info = collect_user_info(req)
        (auth_code, auth_msg) = check_user_can_view_record(user_info, self.recid)
        if auth_code and user_info['email'] == 'guest':
            cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {'collection' : guess_primary_collection_of_a_record(self.recid)})
            target = CFG_SITE_SECURE_URL + '/youraccount/login' + \
                     make_canonical_urlargd({'action': cookie, 'ln' : argd['ln'], 'referer' : \
                CFG_SITE_SECURE_URL + user_info['uri']}, {})
            return redirect_to_url(req, target)
        elif auth_code:
            return page_not_authorized(req, "../", \
                text = auth_msg)



        unordered_tabs = get_detailed_page_tabs(get_colID(guess_primary_collection_of_a_record(self.recid)),
                                                    self.recid,
                                                    ln=argd['ln'])
        ordered_tabs_id = [(tab_id, values['order']) for (tab_id, values) in iteritems(unordered_tabs)]
        ordered_tabs_id.sort(lambda x, y: cmp(x[1], y[1]))
        link_ln = ''
        if argd['ln'] != CFG_SITE_LANG:
            link_ln = '?ln=%s' % argd['ln']
        tabs = [(unordered_tabs[tab_id]['label'], \
                 '%s/%s/%s/%s%s' % (CFG_SITE_SECURE_URL, CFG_SITE_RECORD, self.recid, tab_id, link_ln), \
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
        navtrail += ' &gt; <a class="navtrail" href="%s/%s/%s?ln=%s">'% (CFG_SITE_SECURE_URL, CFG_SITE_RECORD, self.recid, argd['ln'])
        navtrail += cgi.escape(title)
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
