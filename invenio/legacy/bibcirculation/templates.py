# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2008, 2009, 2010, 2011, 2012, 2014 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

""" Templates for the bibcirculation module """

__revision__ = "$Id$"

import datetime
import cgi
from time import localtime
import invenio.utils.date as dateutils
from invenio.utils.url import create_html_link
from invenio.base.i18n import gettext_set_language
from invenio.legacy.search_engine import get_fieldvalues
from invenio.config import CFG_SITE_URL, CFG_SITE_LANG, \
     CFG_CERN_SITE, CFG_SITE_SECURE_URL, CFG_SITE_RECORD, \
     CFG_SITE_NAME
from invenio.base.i18n import gettext_set_language

import invenio.legacy.bibcirculation.db_layer as db
from invenio.legacy.bibcirculation.utils import get_book_cover, \
      book_information_from_MARC, \
      book_title_from_MARC, \
      renew_loan_for_X_days, \
      get_item_info_for_search_result, \
      all_copies_are_missing, \
      is_periodical, \
      looks_like_dictionary
from invenio.legacy.bibcirculation.config import \
    CFG_BIBCIRCULATION_ITEM_LOAN_PERIOD, \
    CFG_BIBCIRCULATION_COLLECTION, \
    CFG_BIBCIRCULATION_LIBRARY_TYPE, \
    CFG_BIBCIRCULATION_ITEM_STATUS_ON_LOAN, \
    CFG_BIBCIRCULATION_LIBRARIAN_EMAIL, \
    CFG_BIBCIRCULATION_LOANS_EMAIL, \
    CFG_BIBCIRCULATION_ILLS_EMAIL, \
    CFG_BIBCIRCULATION_ITEM_STATUS, \
    CFG_BIBCIRCULATION_ITEM_STATUS_ON_LOAN, \
    CFG_BIBCIRCULATION_ITEM_STATUS_ON_SHELF, \
    CFG_BIBCIRCULATION_ITEM_STATUS_ON_ORDER, \
    CFG_BIBCIRCULATION_LOAN_STATUS_EXPIRED, \
    CFG_BIBCIRCULATION_ILL_STATUS_NEW, \
    CFG_BIBCIRCULATION_ILL_STATUS_REQUESTED, \
    CFG_BIBCIRCULATION_ILL_STATUS_ON_LOAN, \
    CFG_BIBCIRCULATION_ILL_STATUS_RETURNED, \
    CFG_BIBCIRCULATION_ILL_STATUS_CANCELLED, \
    CFG_BIBCIRCULATION_ILL_STATUS_RECEIVED, \
    CFG_BIBCIRCULATION_ITEM_LOAN_PERIOD, \
    CFG_BIBCIRCULATION_ACQ_STATUS_NEW, \
    CFG_BIBCIRCULATION_ACQ_STATUS_ON_ORDER, \
    CFG_BIBCIRCULATION_ACQ_STATUS_PARTIAL_RECEIPT, \
    CFG_BIBCIRCULATION_ACQ_STATUS_RECEIVED, \
    CFG_BIBCIRCULATION_ACQ_STATUS_CANCELLED, \
    CFG_BIBCIRCULATION_ACQ_TYPE, \
    CFG_BIBCIRCULATION_ACQ_STATUS, \
    CFG_BIBCIRCULATION_PROPOSAL_STATUS_NEW, \
    CFG_BIBCIRCULATION_PROPOSAL_STATUS_ON_ORDER, \
    CFG_BIBCIRCULATION_PROPOSAL_STATUS_PUT_ASIDE, \
    CFG_BIBCIRCULATION_PROPOSAL_STATUS_RECEIVED, \
    CFG_BIBCIRCULATION_PROPOSAL_TYPE, \
    CFG_BIBCIRCULATION_PROPOSAL_STATUS


JQUERY_TABLESORTER_BASE = "vendors/jquery-tablesorter"
JQUERY_TABLESORTER = JQUERY_TABLESORTER_BASE + "/jquery.tablesorter.min.js"


def load_menu(ln=CFG_SITE_LANG):

    _ = gettext_set_language(ln)

    _MENU_ = """

      <div>
      <map name="Navigation_Bar" id="cdlnav">
      <div id="bibcircmenu" class="cdsweb">
      <!-- <h2><a name="localNavLinks">%(links)s:</a></h2> -->
      <ul>
      <!-- <li>
       <a href="%(url)s/admin2/bibcirculation">%(Home)s</a>
      </li> -->

    <li>
        <a href="%(url)s/admin2/bibcirculation/loan_on_desk_step1?ln=%(ln)s">%(Loan)s</a>
    </li>

    <li>
        <a href="%(url)s/admin2/bibcirculation/loan_return?ln=%(ln)s">%(Return)s</a>
    </li>

    <li>
        <a href="%(url)s/admin2/bibcirculation/borrower_search?redirect_to_new_request=yes&ln=%(ln)s">%(Request)s</a>
    </li>

    <li>
        <a href="%(url)s/admin2/bibcirculation/borrower_search?ln=%(ln)s">%(Borrowers)s</a>
    </li>

    <li>
        <a href="%(url)s/admin2/bibcirculation/item_search?ln=%(ln)s">%(Items)s</a>
    </li>
    """ % {'url': CFG_SITE_URL, 'links': _("Main navigation links"),
           'Home': _("Home"), 'Loan': _("Loan"), 'Return': _("Return"),
           'Request': _("Request"), 'Borrowers': _("Borrowers"),
           'Items': _("Items"), 'ln': ln}

    _MENU_ += """

    <li class="hassubmenu"> <a href="#">%(Lists)s</a>
        <ul class="submenu">
            <li><a href="%(url)s/admin2/bibcirculation/all_loans?ln=%(ln)s">%(Last_loans)s</a></li>
            <li><a href="%(url)s/admin2/bibcirculation/all_expired_loans?ln=%(ln)s">%(Overdue_loans)s</a></li>
            <li><a href="%(url)s/admin2/bibcirculation/get_pending_requests?ln=%(ln)s">%(Items_on_shelf_with_holds)s</a></li>
            <li><a href="%(url)s/admin2/bibcirculation/get_waiting_requests?ln=%(ln)s">%(Items_on_loan_with_holds)s</a></li>
            <li><a href="%(url)s/admin2/bibcirculation/get_expired_loans_with_waiting_requests?ln=%(ln)s">%(Overdue_loans_with_holds)s</a></li>
        </ul>
    </li>

    <li class="hassubmenu"> <a href="#">%(Others)s</a>
        <ul class="submenu">
            <li> <a href="#">%(Libraries)s</a>
                <ul class="subsubmenu">
                    <li><a href="%(url)s/admin2/bibcirculation/search_library_step1?ln=%(ln)s">%(Search)s...</a></li>
                    <li><a href="%(url)s/admin2/bibcirculation/add_new_library_step1?ln=%(ln)s">%(Add_new_library)s</a></li>
                    <li><a href="%(url)s/admin2/bibcirculation/update_library_info_step1?ln=%(ln)s">%(Update_info)s</a></li>
                </ul>
            </li>
            <li> <a href="#">%(Vendors)s</a>
                <ul class="subsubmenu">
                    <li><a href="%(url)s/admin2/bibcirculation/search_vendor_step1?ln=%(ln)s">%(Search)s...</a></li>
                    <li><a href="%(url)s/admin2/bibcirculation/add_new_vendor_step1?ln=%(ln)s">%(Add_new_vendor)s</a></li>
                    <li><a href="%(url)s/admin2/bibcirculation/update_vendor_info_step1?ln=%(ln)s">%(Update_info)s</a></li>
                </ul>
            </li>
        </ul>
    </li>
    """ % {'url': CFG_SITE_URL, 'Lists': _("Loan Lists"),
           'Last_loans': _("Last loans"),
           'Overdue_loans': _("Overdue loans"),
           'Items_on_shelf_with_holds': _("Items on shelf with holds"),
           'Items_on_loan_with_holds': _("Items on loan with holds"),
           'Overdue_loans_with_holds': _("Overdue loans with holds"),
           'Others': _("Others"), 'Libraries': _("Libraries"),
           'Search': _("Search"), 'Add_new_library': _("Add new library"),
           'Update_info': _("Update info"), 'Vendors': _("Vendors"),
           'Add_new_vendor': _("Add new vendor"), 'ln': ln}

    _MENU_ += """

    <li class="hassubmenu"> <a href="#">%(ILL)s<!--Inter Library Loan--></a>
        <ul class="submenu">
            <li><a href="%(url)s/admin2/bibcirculation/register_ill_book_request?ln=%(ln)s">%(Register_Book_request)s</a></li>
            <li><a href="%(url)s/admin2/bibcirculation/register_ill_article_request_step1">%(Register_Article)s request</a></li>
             <li><a href="%(url)s/admin2/bibcirculation/register_purchase_request_step1?ln=%(ln)s">%(Register_Purchase_request)s</a></li>
            <li><a href="%(url)s/admin2/bibcirculation/ill_search?ln=%(ln)s">%(Search)s...</a></li>
        </ul>
    </li>

    <li class="hassubmenu"> <a href="#">%(Lists)s</a>
        <ul class="submenu">
            <li><a href="%(url)s/admin2/bibcirculation/list_ill_request?status=new&ln=%(ln)s">%(ILL)s - %(ill-new)s</a></li>
            <li><a href="%(url)s/admin2/bibcirculation/list_ill_request?status=requested&ln=%(ln)s">%(ILL)s - %(Requested)s</a></li>
            <li><a href="%(url)s/admin2/bibcirculation/list_ill_request?status=on loan&ln=%(ln)s">%(ILL)s - %(On_loan)s</a></li>
            <li><a href="%(url)s/admin2/bibcirculation/list_purchase?status=%(acq-new)s&ln=%(ln)s">%(Purchase)s - %(acq-new)s</a></li>
            <li><a href="%(url)s/admin2/bibcirculation/list_purchase?status=%(on_order)s&ln=%(ln)s">%(Purchase)s - %(on_order)s</a></li>
            <li><a href="%(url)s/admin2/bibcirculation/list_proposal?status=%(proposal-new)s&ln=%(ln)s">%(Proposal)s - %(proposal-new)s</a></li>
            <li><a href="%(url)s/admin2/bibcirculation/list_proposal?status=%(proposal-put_aside)s&ln=%(ln)s">%(Proposal)s - %(proposal-put_aside)s</a></li>
            <li><a href="%(url)s/admin2/bibcirculation/list_proposal?status=%(requests-putaside)s&ln=%(ln)s">%(Proposal)s - %(requests-putaside)s</a></li>
        </ul>
    </li>

    <li class="hassubmenu">
         <a href="#">%(Help)s</a>
        <ul class="submenu">
          <li><a href="%(url)s/help/admin/bibcirculation-admin-guide" target="_blank">%(Admin_guide)s</a></li>
             <!-- <li><a href="%(url)s/admin2/bibcirculation/help_contactsupport">%(Contact_Support)s</a></li> -->
        </ul>
    </li>
    </ul>
    <div class="clear"></div>
    </div>
    </map>
    </div>
    """ % {'url': CFG_SITE_URL, 'ILL': _("ILL"),
           'Register_Book_request': _("Register Book request"),
           'Register_Article': _("Register Article"),
           'Register_Purchase_request': _("Register purchase request"),
           'Search': _("Search"),
           'Lists': _("ILL Lists"),
           'Purchase': _("Purchase"),
           'Proposal': _("Proposal"),
           'ill-new':  _(CFG_BIBCIRCULATION_ILL_STATUS_NEW),
           'acq-new':  _(CFG_BIBCIRCULATION_ACQ_STATUS_NEW),
           'on_order': _(CFG_BIBCIRCULATION_ACQ_STATUS_ON_ORDER),
           'Requested': _(CFG_BIBCIRCULATION_ILL_STATUS_REQUESTED),
           'On_loan':  _(CFG_BIBCIRCULATION_ILL_STATUS_ON_LOAN),
           'proposal-new':  _(CFG_BIBCIRCULATION_PROPOSAL_STATUS_NEW),
           'proposal-put_aside': _(CFG_BIBCIRCULATION_PROPOSAL_STATUS_PUT_ASIDE),
           'requests-putaside': "requests-putaside",
           'Help': _("Help"),
           'Admin_guide': _("Admin guide"),
           'Contact_Support': _("Contact Support"),
           'ln': ln}

    return _MENU_


class Template:
    """
       Templates for the BibCirculation module.
       The template methods are positioned by grouping into logical
       categories('User Pages', 'Loans, Returns and Loan requests',
       'ILLs', 'Libraries', 'Vendors' ...)
       This is also true with the calling methods in bibcirculation
       and adminlib.
       These orders should be maintained and when necessary, improved
       for readability, as and when additional methods are added.
       When applicable, methods should be renamed, refactored and
       appropriate documentation added.
    """

    def tmpl_infobox(self, infos, ln=CFG_SITE_LANG):
        """
        Display len(infos) information fields
        @param infos: list of strings
        @param ln: language
        @return html output
        """
        _ = gettext_set_language(ln)
        if not((type(infos) is list) or (type(infos) is tuple)):
            infos = [infos]
        infobox = ""
        for info in infos:
            infobox += "<div class=\"infobox\">"
            lines = info.split("\n")
            for line in lines[0:-1]:
                infobox += line + "<br />\n"
            infobox += lines[-1] + "</div><br />\n"
        return infobox

    def tmpl_display_infos(self, infos, ln=CFG_SITE_LANG):
        """
        Returns a page where the only content is infoboxes.

        @param infos: messages to be displayed
        @type infos: list

        @param ln: language
        """

        _ = gettext_set_language(ln)

        out = load_menu(ln)
        out += """ <br /> """

        if type(infos) is not list or len(infos) == 0:
            out += """<div class="infobox">"""
            out += _("No messages to be displayed")
            out += """</div> <br /> """
        else:
            for info in infos:
                out += """<div class="infobox">"""
                out += info
                out += """</div> <br /> """

        return out

    def tmpl_holdings_information(self, recid, req, holdings_info,
                                  ln=CFG_SITE_LANG):
        """
        This template is used in the user interface. In this template
        it is possible to see all details (loan period, number of copies, location, etc)
        about a book.

        @param recid: identify the record. Primary key of bibrec.
        @type recid: int

        @param holdings_info: book's information (all copies)
        @type holdings_info: list
        """
        from invenio.legacy.bibcirculation.adminlib import is_adminuser

        (auth_code, _auth_message) = is_adminuser(req)

        _ = gettext_set_language(ln)

        if not book_title_from_MARC(recid):
            out = """<div align="center"
                     <div class="bibcircinfoboxmsg">%s</div>
                  """ % (_("This record does not exist."))
            return out

        elif not db.has_copies(recid):
            message = _("This record has no copies.")


            if auth_code == 0:
                new_copy_link = create_html_link(CFG_SITE_URL +
                                    '/admin2/bibcirculation/add_new_copy_step3',
                                    {'recid': recid, 'ln': ln},
                                    _("Add a new copy"))
                message += ' ' + new_copy_link

            out = """<div align="center"
                     <div class="bibcircinfoboxmsg">%s</div>
                  """ % (message)
            return out

        # verify if all copies are missing
        elif all_copies_are_missing(recid):

            ill_link = """<a href='%(url)s/ill/book_request_step1?%(ln)s'>%(ILL_services)s</a>
                       """ % {'url': CFG_SITE_URL, 'ln': ln,
                              'ILL_services': _("ILL services")}

            out = """<div align="center"
                     <div class="bibcircinfoboxmsg">%(message)s.</div>
                    """ % {'message': _('All the copies of %(strong_tag_open)s%(title)s%(strong_tag_close)s are missing. You can request a copy using %(strong_tag_open)s%(ill_link)s%(strong_tag_close)s') % {'strong_tag_open': '<strong>', 'strong_tag_close': '</strong>', 'title': book_title_from_MARC(recid), 'ill_link': ill_link}}
            return out

        # verify if there are no copies
        elif not holdings_info:
            out = """<div align="center"
                     <div class="bibcircinfoboxmsg">%s</div>
                """ % (_("This item has no holdings."))
            return out

        out = """
            <style type="text/css"> @import url("/css/tablesorter.css"); </style>
            <script src="/{0}" type="text/javascript"></script>
            <script type="text/javascript">
            """.format(JQUERY_TABLESORTER)

        if is_periodical(recid):
            out += """
            $(document).ready(function(){
                $("#table_holdings")
                    .tablesorter({sortList: [[4,1]],
                                widthFixed: true,
                                   widgets: ['zebra']})
                    .bind("sortStart",function(){$("#overlay").show();})
                    .bind("sortEnd",function(){$("#overlay").hide()})
                    .tablesorterPager({container: $("#pager"), positionFixed: false, size: 40});
            });
            </script>
            """
        else:
            out += """
            $(document).ready(function(){
                $("#table_holdings")
                    .tablesorter({sortList: [[6,1],[1,0]],
                                widthFixed: true,
                                   widgets: ['zebra']})
                    .bind("sortStart",function(){$("#overlay").show();})
                    .bind("sortEnd",function(){$("#overlay").hide()})
                    .tablesorterPager({container: $("#pager"), positionFixed: false});
            });
            </script>
            """

        out += """
                <table id="table_holdings" class="tablesorter" border="0"
                                           cellpadding="0" cellspacing="1">
                    <thead>
                        <tr>
                            <th>%s</th>
                            <th>%s</th>
                            <th>%s</th>
                            <th>%s</th>
                            <th>%s</th>
                            <th>%s</th>
                            <th>%s</th>
                            <th>%s</th>
                            <th>%s</th>
                        </tr>
                    </thead>
                    <tbody>
                """ % (_("Options"), _("Library"), _("Collection"),
                       _("Location"), _("Description"), _("Loan period"),
                       _("Status"), _("Due date"), _("Barcode"))

        for (barcode, library, collection, location, description,
             loan_period, status, due_date) in holdings_info:

            if loan_period == 'Reference':
                request_button = '-'
            else:
                request_button = """
                <input type=button
                onClick="location.href='%s/%s/%s/holdings/request?barcode=%s&ln=%s'"
                value='%s' class="bibcircbutton" onmouseover="this.className='bibcircbuttonover'"
                onmouseout="this.className='bibcircbutton'">
                """ % (CFG_SITE_URL, CFG_SITE_RECORD, recid, barcode, ln, _("Request"))

            if status in (CFG_BIBCIRCULATION_ITEM_STATUS_ON_ORDER,
                          'claimed'):
                expected_arrival_date = db.get_expected_arrival_date(barcode)
                if expected_arrival_date != '':
                    status = status + ' - ' + expected_arrival_date

            if status != 'missing':
                out += """
                <tr>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td align='center'>%s</td>
                </tr>
                """ % (request_button, library, collection or '-', location,
                       description, loan_period, status, due_date or '-', barcode)

        if auth_code != 0:
            bibcirc_link = ''
        else:
            bibcirc_link = create_html_link(CFG_SITE_URL +
                                    '/admin2/bibcirculation/get_item_details',
                                    {'recid': recid, 'ln': ln},
                                    _("See this book on BibCirculation"))

        out += """
            </tbody>
            </table>
            <div id="pager" class="pager">
                        <form>
                            <br />
                            <img src="/img/sb.gif" class="first" />
                            <img src="/img/sp.gif" class="prev" />
                            <input type="text" class="pagedisplay" />
                            <img src="/img/sn.gif" class="next" />
                            <img src="/img/se.gif" class="last" />
            """

        if is_periodical(recid):
            out += """
                            <select class="pagesize">
                                <option value="10">10</option>
                                <option value="20">20</option>
                                <option value="30">30</option>
                                <option value="40" selected="selected">40</option>
                            </select>
                """
        else:
            out += """
                            <select class="pagesize">
                                <option value="10" selected="selected">10</option>
                                <option value="20">20</option>
                                <option value="30">30</option>
                                <option value="40">40</option>
                            </select>
                """
        out += """
                        </form>
                    </div>
           <br />
           <br />
           <table class="bibcirctable">
             <tr>
               <td class="bibcirctableheader">%s</td>
             </tr>
           </table>
           """ % (bibcirc_link)

        return out

    def tmpl_book_proposal_information(self, recid, msg, ln=CFG_SITE_LANG):
        """
        This template is used in the user interface. It is used to display the
        message regarding a 'proposal' of a book when the corresponding metadata
        record has been extracted from Amazon and noone has yet suggested the
        book for acquisition(No copies of the book exist yet).

        @param msg: information about book proposal mechanism
        @type msg: string
        """
        _ = gettext_set_language(ln)
        out = """<div align="center"
                 <div class="bibcircinfoboxmsg">%s</div>
                 <br \>
                 <br \>
              """ % (msg)
        out += """<form>
                      <input type="button" value='%s' onClick="history.go(-1)" class="formbutton">
                      <input type="button" value='%s' onClick="location.href=
                       '%s/%s/%s/holdings/request?ln=%s&act=%s'" class="formbutton">
                  </form>""" % (_("Back"),  _("Suggest"), CFG_SITE_URL, CFG_SITE_RECORD,
                                recid, ln, "pr")
        return out

    def tmpl_book_not_for_loan(self, ln=CFG_SITE_LANG):
        _ = gettext_set_language(ln)
        message = """<div align="center"
                     <div class="bibcircinfoboxmsg">%s</div>
                  """ % (_("This item is not for loan."))
        return message

    def tmpl_message_send_already_requested(self, ln=CFG_SITE_LANG):
        _ = gettext_set_language(ln)
        message = _("You already have a request on, or are in possession of this document.")
        return message

    def tmpl_message_request_send_ok_cern(self, ln=CFG_SITE_LANG):
        _ = gettext_set_language(ln)
        message = _("Your request has been registered and the document will be sent to you via internal mail.")
        return message

    def tmpl_message_request_send_ok_other(self, ln=CFG_SITE_LANG):
        _ = gettext_set_language(ln)
        message = _("Your request has been registered.")
        return message

    def tmpl_message_request_send_fail_cern(self, custom_msg='', ln=CFG_SITE_LANG):
        _ = gettext_set_language(ln)
        message = _("It is not possible to validate your request. ")
        message += custom_msg
        message += _("Please contact %(librarian_email)s") \
                    % {'librarian_email': CFG_BIBCIRCULATION_LIBRARIAN_EMAIL}
        return message

    def tmpl_message_request_send_fail_other(self, custom_msg='', ln=CFG_SITE_LANG):
        _ = gettext_set_language(ln)
        message = _("It is not possible to validate your request. ")
        message += custom_msg
        message += _("Please contact %(librarian_email)s") \
                    % {'librarian_email': CFG_BIBCIRCULATION_LIBRARIAN_EMAIL}
        return message

    def tmpl_message_proposal_send_ok_cern(self, ln=CFG_SITE_LANG):
        _ = gettext_set_language(ln)
        message = _("Thank you for your suggestion. We will get back to you shortly.")
        return message

    def tmpl_message_proposal_send_ok_other(self, ln=CFG_SITE_LANG):
        _ = gettext_set_language(ln)
        message = _("Thank you for your suggestion. We will get back to you shortly.")
        return message

    def tmpl_message_purchase_request_send_ok_other(self, ln=CFG_SITE_LANG):
        _ = gettext_set_language(ln)
        message = _("Your purchase request has been registered.")
        return message

    def tmpl_message_sever_busy(self, ln=CFG_SITE_LANG):
        _ = gettext_set_language(ln)
        message = _('Server busy. Please, try again in a few seconds.')
        return message


    ###
    ### The two template methods below correspond to the user pages of bibcirculation.
    ###


    def tmpl_yourloans(self, loans, requests, proposals, borrower_id,
                       infos, ln=CFG_SITE_LANG):
        """
        When a user is logged in, in the section 'yourloans', it is
        possible to check his loans, loan requests and book proposals.
        It is also possible to renew a single loan or all loans.

        @param infos: additional information in the infobox
        @param ln: language
        """
        _ = gettext_set_language(ln)

        renew_all_link = create_html_link(CFG_SITE_SECURE_URL +
                            '/yourloans/display',
                            {'borrower_id': borrower_id, 'action': 'renew_all'},
                            (_("Renew all loans")))

        loanshistoricaloverview_link = create_html_link(CFG_SITE_SECURE_URL +
                                        '/yourloans/loanshistoricaloverview',
                                        {'ln': ln},
                                        (_("Loans - historical overview")))

        out = self.tmpl_infobox(infos, ln)

        if len(loans) == 0:
            out += """
            <div class="bibcirctop_bottom">
            <br />
            <table class="bibcirctable_contents">
                 <td align="center" class="bibcirccontent">%s</td>
            </table>
            <br />
            """ % (_("You don't have any book on loan."))

        else:
            out += """
                      <style type="text/css"> @import url("/css/tablesorter.css"); </style>
                      <script src="/%s" type="text/javascript"></script>
                      <script type="text/javascript">
                      $(document).ready(function() {
                        $('#table_loans').tablesorter()
                      });
                      </script>

                      <table class="tablesortermedium" id="table_loans"
                             border="0" cellpadding="0" cellspacing="1">
                      <thead>
                        <tr>
                         <th>%s</th>
                         <th>%s</th>
                         <th>%s</th>
                         <th>%s</th>
                        </tr>
                      </thead>
                      <tbody>
                     """ % (JQUERY_TABLESORTER,
                            _("Item"),
                            _("Loaned on"),
                            _("Due date"),
                            _("Action(s)"))

            for(recid, barcode, loaned_on, due_date, loan_type) in loans:
                record_link = "<a href=" + CFG_SITE_URL + "/%s/%s>" % (CFG_SITE_RECORD, recid) + \
                              (book_title_from_MARC(recid)) + "</a>"

                if loan_type == 'ill':
                    renew_link = '-'
                else:
                    renew_link = create_html_link(CFG_SITE_SECURE_URL +
                                        '/yourloans/display',
                                        {'barcode': barcode, 'action': 'renew'},
                                        (_("Renew")))

                out += """
                <tr>
                  <td>%s</td>
                  <td>%s</td>
                  <td>%s</td>
                  <td>%s</td>
                </tr>
                """ % (record_link,
                       loaned_on,
                       due_date,
                       renew_link)

            out += """    </tbody>
                          </table>
                          <br />
                          <table class="bibcirctable">
                          <tr>
                          <td width="430"></td>
                          <td class="bibcirccontent" width="700">%s</td>
                          </tr>
                          </table>
                          <br />
                          """ % (renew_all_link)

        if len(requests) == 0:
            out += """
                   <h1 class="headline">%s</h1>
                   <br />
                   <table class="bibcirctable_contents">
                   <td align="center" class="bibcirccontent">%s</td>
                   </table>
                   <br />
                   """ % (_("Your Requests"),
                        _("You don't have any request (waiting or pending)."))

        else:
            out += """
                   <h1 class="headline">%s</h1>
                   <style type="text/css"> @import url("/css/tablesorter.css"); </style>
                   <script src="/%s" type="text/javascript"></script>
                   <script type="text/javascript">
                   $(document).ready(function() {
                        $('#table_requests').tablesorter()
                   });
                   </script>
                   <table class="tablesortermedium" id="table_requests"
                          border="0" cellpadding="0" cellspacing="1">
                   <thead>
                   <tr>
                     <th>%s</th>
                     <th>%s</th>
                     <th>%s</th>
                     <th>%s</th>
                   </tr>
                   </thead>
                   <tbody>
                   """ % (JQUERY_TABLESORTER,
                          _("Your Requests"),
                          _("Item"),
                          _("Request date"),
                          _("Status"),
                          _("Action(s)"))

            for(request_id, recid, request_date, status) in requests:

                record_link = "<a href=" + CFG_SITE_URL + "/%s/%s?ln=%s>" % (CFG_SITE_RECORD, recid, ln) + \
                              (book_title_from_MARC(recid)) + "</a>"

                cancel_request_link = create_html_link(CFG_SITE_URL +
                                                '/yourloans/display',
                                                {'request_id': request_id,
                                                 'action': 'cancel',
                                                 'ln': ln},
                                                 (_("Cancel")))
                out += """
                <tr>
                  <td>%s</td>
                  <td>%s</td>
                  <td>%s</td>
                  <td>%s</td>
                </tr>
                """ % (record_link, request_date,
                       status, cancel_request_link)

            out += """</tbody>
                      </table>
                      <br />"""

        if len(proposals) == 0:
            out += """
                   <h1 class="headline">%s</h1>
                   <br />
                   <table class="bibcirctable_contents">
                   <td align="center" class="bibcirccontent">%s</td>
                   </table>
                   <br /> <br />
                   <hr>
                   <br />
                   <table class="bibcirctable">
                   <tr>
                   <td class="bibcirccontent" width="70">%s</td>
                   </tr>
                   </table>
                   <br />
                   <table class="bibcirctable">
                   <tr>
                   <td>
                   <input type=button onClick="location.href='%s'" value='%s' class='formbutton'>
                   </td>
                   </tr>
                   </table>
                   <br />
                   """ % (_("Your Proposals"),
                        _("You did not propose any acquisitions."),
                        loanshistoricaloverview_link,
                        CFG_SITE_URL, _("Back to home"))

        else:
            out += """
                   <h1 class="headline">%s</h1>
                   <style type="text/css"> @import url("/css/tablesorter.css"); </style>
                   <script src="/%s" type="text/javascript"></script>
                   <script type="text/javascript">
                   $(document).ready(function() {
                        $('#table_requests').tablesorter()
                   });
                   </script>
                   <table class="tablesortermedium" id="table_requests"
                          border="0" cellpadding="0" cellspacing="1">
                   <thead>
                   <tr>
                     <th>%s</th>
                     <th>%s</th>
                   </tr>
                   </thead>
                   <tbody>
                   """ % (JQUERY_TABLESORTER,
                          _("Your Proposals under review"),
                          _("Item"),
                          _("Proposal date"))

            for(request_id, recid, request_date, status) in proposals:

                record_link = "<a href=" + CFG_SITE_URL + "/%s/%s?ln=%s>" % (CFG_SITE_RECORD, recid, ln) + \
                              (book_title_from_MARC(recid)) + "</a>"

                out += """
                <tr>
                  <td>%s</td>
                  <td>%s</td>
                </tr>
                """ % (record_link, request_date)

            out += """     </tbody>
                          </table>
                          <br />
                          <hr>
                          <table class="bibcirctable">
                          <tr>
                          <td class="bibcirccontent" width="70">%s</td>
                          </tr>
                          </table>
                          <br />
                          <table class="bibcirctable">
                          <tr>
                          <td>
                          <input type=button
                                 onClick="location.href='%s'"
                                 value='%s'
                                 class='formbutton'>
                          </td>
                          </tr>
                          </table>
                          <br />
                          <br />
                          </div>
                          """ % (loanshistoricaloverview_link,
                                 CFG_SITE_URL,
                                 _("Back to home"))

        return out

    def tmpl_loanshistoricaloverview(self, result, ln=CFG_SITE_LANG):
        """
        In the section 'yourloans' it is possible to see the historical overview of the loans
        of the user who is logged in.

        @param result: All loans whose status = CFG_BIBCIRCULATION_LOAN_STATUS_RETURNED
        @param ln: language
        """

        _ = gettext_set_language(ln)

        out = """<div class="bibcirctop_bottom">
                    <br /> <br />
                    <style type="text/css"> @import url("/css/tablesorter.css"); </style>
                    <script src="/%s" type="text/javascript"></script>
                    <script type="text/javascript">
                    $(document).ready(function(){
                        $('#table_hist').tablesorter()
                    });
                    </script>
                    <table class="tablesortermedium" id="table_hist"
                           border="0" cellpadding="0" cellspacing="1">
                    <thead>
                    <tr>
                      <th>%s</th>
                      <th>%s</th>
                      <th>%s</th>
                      <th>%s</th>
                    </tr>
                    </thead>
                    <tbody>
                    """ % (JQUERY_TABLESORTER,
                           _("Item"),
                           _("Loaned"),
                           _("Returned"),
                           _("Renewals"))

        for(recid, loaned_on, returned_on, nb_renewals) in result:

            record_link = "<a href=" + CFG_SITE_URL + "/%s/%s>" % (CFG_SITE_RECORD, recid) + \
                          (book_title_from_MARC(recid)) + "</a>"

            out += """
                <tr>
                  <td>%s</td>
                  <td>%s</td>
                  <td>%s</td>
                  <td>%s</td>
                </tr>
                """ % (record_link, loaned_on,
                       returned_on, nb_renewals)

        out += """</tbody>
                  </table>
                  <br />
                  <table class="bibcirctable">
                    <tr>
                        <td>
                            <input type=button value='%s'
                                   onClick="history.go(-1)" class="formbutton">
                        </td>
                    </tr>
                  </table>
                  <br />
                  <br />
                  </div>
                  """ % (_("Back"))

        return out


    ###
    ### Loans, Loan Requests, Loan Returns related templates.
    ###


    def tmpl_new_request(self, recid, barcode, action="borrowal", ln=CFG_SITE_LANG):
        """
        This template is used when a user wants to request a copy of a book.
        If a copy is avaliable (action is 'borrowal'), the 'period of interest' is solicited.
        If not AND the book record is put up for proposal (action is 'proposal'),
        user's comments are solicited.

        @param recid: recID - Invenio record identifier
        @param barcode: book copy's barcode
        @param action: 'borrowal'/'proposal'
        @param ln: language
        """

        _ = gettext_set_language(ln)

        today = datetime.date.today()
        gap = datetime.timedelta(days=180)
        gap_1yr = datetime.timedelta(days=360)
        more_6_months = (today + gap).strftime('%Y-%m-%d')
        more_1_year = (today + gap_1yr).strftime('%Y-%m-%d')

        out = """
        <style type="text/css"> @import url("/css/tablesorter.css"); </style>
        <link rel=\"stylesheet\" href=\"%s/vendors/jquery-ui/themes/redmond/jquery-ui.min.css\" type=\"text/css\" />
        <link rel=\"stylesheet\" href=\"%s/vendors/jquery-ui/themes/redmond/theme.css\" type=\"text/css\" />
        <script type="text/javascript" src="%s/vendors/jquery-ui/jquery-ui.min.js"></script>

            <form name="request_form" action="%s/%s/%s/holdings/send" method="post" >
            <br />
              <div align=center>
              """ % (CFG_SITE_URL, CFG_SITE_URL, CFG_SITE_URL,
                     CFG_SITE_RECORD, recid)

        if action == "proposal":
            out += """ <table class="bibcirctable_contents" align=center>
                         <tr>
                           <td class="bibcirctableheader" align=center>"""

            out += _("Why do you suggest this book for the library?")

            out += """    </td>
                         </tr>
                       </table>
                       <br />
                       <table align=center class="tablesorterborrower" width="100" border="0" cellspacing="1" align="center">
                       <tr align=center>
                         <td>
                           <textarea align=center rows="5" cols="43" name="remarks" id="remarks"
                            style='border: 1px solid #cfcfcf'></textarea>
                         </td>
                       </tr>
                       <input type=hidden size="12" name="period_from" value="%s">
                       <input type=hidden size="12" name="period_to" value="%s">
                    """ % (today, more_1_year)
            out += """<input type=hidden name="act" value="%s">""" % ("pr")

        else:
            out += """<table class="bibcirctable_contents" align=center>
                        <tr>
                          <td class="bibcirctableheader" align=center>%s</td>
                        </tr>
                      </table>
                      <br/>
                      <table align=center class="tablesorterborrower" width="100" border="0" cellspacing="1" align="center">
                        <tr align=center>
                          <th align=center>%s</th>
                          <td>
                            <script type="text/javascript">
                              $(function() {
                                  $("#date_picker1").datepicker({dateFormat: 'yy-mm-dd', showOn: 'button', buttonImage: "%s/img/calendar.gif", buttonImageOnly: true});
                                           });
                            </script>
                            <input type="text" size="12" id="date_picker1" name="period_from" value="%s"
                             style='border: 1px solid #cfcfcf'>
                          </td>
                        </tr>
                        <tr align=center>
                          <th align=center>%s</th>
                          <td>
                            <script type="text/javascript">
                              $(function() {
                                  $("#date_picker2").datepicker({dateFormat: 'yy-mm-dd', showOn: 'button', buttonImage: "%s/img/calendar.gif", buttonImageOnly: true});
                                           });
                            </script>
                            <input type="text" size="12" id="date_picker2" name="period_to" value="%s"
                            style='border: 1px solid #cfcfcf'>
                          </td>
                        </tr>""" % (_("Enter your period of interest"),
                    _("From"), CFG_SITE_URL, today, _("To"),
                    CFG_SITE_URL, more_6_months,)

        out +=  """</table>
                </div>
                <br />
                <br />
                <table class="bibcirctable_contents">
                  <input type=hidden name=barcode value='%s'>
                  <tr>
                    <td align="center">
                      <input type=button value='%s' onClick="history.go(-1)" class="formbutton">
                      <input type="submit" name="submit_button" value='%s' class="formbutton">
                    </td>
                  </tr>
                </table>
                <br />
                <br />
                </form>
        """ % (barcode, _("Back"), _("Confirm"))

        return out

    def tmpl_new_request_send(self, message, ln=CFG_SITE_LANG):
        """
        This template is used in the user interface to display a confirmation message
        when a copy of a book is requested.

        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = """
        <br />
        <br />
        <table class="bibcirctable">
            <tr>
                <td class="bibcirccontent" width="30">%s</td>
            </tr>
            <tr>
                <td class="bibcirccontent" width="30">%s</td>
            </tr>
        </table>
        <br />
        <br />
        <table class="bibcirctable">
            <td>
                <input type=button onClick="location.href='%s'" value='%s' class='formbutton'>
            </td>
        </table>
        <br />
        <br />
        """ % (message,
               _("You can see your library account %(x_url_open)shere%(x_url_close)s."
                    % {'x_url_open': '<a href="' + CFG_SITE_URL + \
                       '/yourloans/display' + '">', 'x_url_close': '</a>'}),
               CFG_SITE_URL,
               _("Back to home"))

        return out

    def tmpl_book_proposal_send(self, ln=CFG_SITE_LANG):
        """
        This template is used in the user interface to display a confirmation message
        when a book is proposed for acquisition.
        """

        _ = gettext_set_language(ln)
        message = "Thank you for your suggestion."

        out = """
        <br />
        <br />
        <table class="bibcirctable">
            <tr>
                <td class="bibcirccontent" width="30">%s</td>
            </tr>
        </table>
        <br />
        <br />
        <table class="bibcirctable">
            <td>
                <input type=button onClick="location.href='%s'" value='%s' class='formbutton'>
            </td>
        </table>
        <br />
        <br />
        """ % (message, CFG_SITE_URL, _("Back to home"))

        return out

    def tmpl_get_pending_requests(self, result, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = load_menu(ln)

        out += """
            <style type="text/css"> @import url("/%s/themes/blue/style.css"); </style>
            <style type="text/css"> @import url("/%s/addons/pager/jquery.tablesorter.pager.css"); </style>
            <script src="/%s" type="text/javascript"></script>
            <script src="/%s/addons/pager/jquery.tablesorter.pager.js" type="text/javascript"></script>
            <script type="text/javascript">

            $(document).ready(function(){
                $("#table_all_loans")
                    .tablesorter({sortList: [[4,0], [0,0]],widthFixed: true, widgets: ['zebra']})
                    .bind("sortStart",function(){$("#overlay").show();})
                    .bind("sortEnd",function(){$("#overlay").hide()})
                    .tablesorterPager({container: $("#pager"), positionFixed: false});
            });
            </script>

            <script type="text/javascript">
                function confirmation(rqid) {
                  var answer = confirm("%s")
                  if (answer){
            window.location = "%s/admin2/bibcirculation/get_pending_requests?request_id="+rqid;
                    }
                  else{
                    alert("%s")
                    }
                 }
            </script>

            <br />

            <div class="bibcircbottom">
            """ % (JQUERY_TABLESORTER_BASE,
                   JQUERY_TABLESORTER,
                   JQUERY_TABLESORTER_BASE,
                   JQUERY_TABLESORTER_BASE,
                   _("Delete this request?"), CFG_SITE_URL,
                   _("Request not deleted."))

        if len(result) == 0:
            out += """
              <br />
              <table class="bibcirctable">
                <tr>
                    <td class="bibcirccontent">%s</td>
                </tr>
                </table>
                <br />
                <table class="bibcirctable">
                <tr>
                  <td>
                    <input type=button value='%s' onClick="history.go(-1)" class="formbutton">
                  </td>
                </tr>
                </table>
                <br />
                <br />
                </div>
                """ % (_("No more requests are pending."),
                       _("Back"))

        else:
            out += """
            <form name="borrower_form" action="%s/admin2/bibcirculation/all_loans" method="get" >
            <br />
            <table id="table_all_loans" class="tablesorter"
                   border="0" cellpadding="0" cellspacing="1">
               <thead>
                    <tr>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                    </tr>
              </thead>
              <tbody>
                    """ % (CFG_SITE_URL,
                            _("Name"),
                            _("Item"),
                            _('Library'),
                            _("Location"),
                            _("Vol."),
                            _("Ed."),
                            _("From"),
                            _("To"),
                            _("Request date"),
                            _("Actions"))

            for (request_id, recid, barcode, name, borrower_id, library, location,
                 date_from, date_to, request_date) in result:

                title_link = create_html_link(CFG_SITE_URL +
                                    '/admin2/bibcirculation/get_item_details',
                                    {'recid': recid, 'ln': ln},
                                    (book_title_from_MARC(recid)))

                borrower_link = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/get_borrower_details',
                                {'borrower_id': borrower_id, 'ln': ln}, (name))

                volume = db.get_item_description(barcode)
                edition = get_fieldvalues(recid, "250__a")

                if edition == []:
                    edition = ''
                else:
                    edition = edition[0]

                out += """
                <tr>
                 <td width='150'>%s</td>
                 <td width='250'>%s</td>
                 <td>%s</td>
                 <td>%s</td>
                 <td>%s</td>
                 <td>%s</td>
                 <td>%s</td>
                 <td>%s</td>
                 <td>%s</td>
                 <td algin='center'>
                 <input type="button" value='%s' style="background: url(/img/dialog-cancel.png)
                 no-repeat #8DBDD8; width: 75px; text-align: right;"
                 onClick="confirmation(%s)"
                 onmouseover="this.className='bibcircbuttonover'"
                 onmouseout="this.className='bibcircbutton'"
                 class="bibcircbutton">

                 <input type="button" value='%s' class="bibcircbutton"
                        style="background: url(/img/dialog-yes.png) no-repeat #8DBDD8;
                        width: 150px; text-align: right;"
    onmouseover="this.className='bibcircbuttonover'"
    onmouseout="this.className='bibcircbutton'"
    onClick="location.href='%s/admin2/bibcirculation/create_loan?ln=%s&request_id=%s&recid=%s&borrower_id=%s'">
                 </td>
                </tr>
                """ % (borrower_link,
                       title_link,
                       library,
                       location,
                       volume,
                       edition,
                       date_from,
                       date_to,
                       request_date,
                       _("Delete"),
                       request_id,
                       _("Create loan"),
                       CFG_SITE_URL, ln,
                       request_id,
                       recid,
                       borrower_id)

            out += """
                    </tbody>
                    </table>
                    </form>

                    <div id="pager" class="pager">
                        <form>
                            <br />
                            <img src="/img/sb.gif" class="first" />
                            <img src="/img/sp.gif" class="prev" />
                            <input type="text" class="pagedisplay" />
                            <img src="/img/sn.gif" class="next" />
                            <img src="/img/se.gif" class="last" />
                            <select class="pagesize">
                                <option value="10" selected="selected">10</option>
                                <option value="20">20</option>
                                <option value="30">30</option>
                                <option value="40">40</option>
                            </select>
                        </form>
                    </div>
                    """
            out += """
                    <div class="back" style="position: relative; top: 5px;">
                        <br />
                        <table class="bibcirctable">
                            <tr>
                                <td>
                                    <input type=button
                                           value='%s'
                                           onClick="history.go(-1)"
                                           class="formbutton">
                                </td>
                            </tr>
                        </table>
                    <br />
                    <br />
                    </form>
                    </div>
                    </div>
                    """ % (_("Back"))

        return out

    def tmpl_get_waiting_requests(self, result, ln=CFG_SITE_LANG):
        """
        @param ln: language
        """

        _ = gettext_set_language(ln)

        out = load_menu(ln)

        out += """
            <style type="text/css"> @import url("/{0}/themes/blue/style.css"); </style>
            <style type="text/css"> @import url("/{0}/addons/pager/jquery.tablesorter.pager.css"); </style>
            <script src="/{1}" type="text/javascript"></script>
            <script src="/{0}/addons/pager/jquery.tablesorter.pager.js" type="text/javascript"></script>
            <script type="text/javascript">
            $(document).ready(function(){
                $("#table_all_loans")
                    .tablesorter({sortList: [[4,0], [0,0]],widthFixed: true, widgets: ['zebra']})
                    .bind("sortStart",function(){$("#overlay").show();})
                    .bind("sortEnd",function(){$("#overlay").hide()})
                    .tablesorterPager({container: $("#pager"), positionFixed: false});
            });
            </script>

            <br />

            <div class="bibcircbottom">
            """.format(JQUERY_TABLESORTER_BASE, JQUERY_TABLESORTER)

        if len(result) == 0:
            out += """
              <br />
              <table class="bibcirctable">
                <tr>
                    <td class="bibcirccontent">%s</td>
                </tr>
                </table>
                <br />
                <table class="bibcirctable">
                <tr>
                  <td>
                    <input type=button value='%s' onClick="history.go(-1)" class="formbutton">
                  </td>
                </tr>
                </table>
                <br />
                <br />
                </div>
                """ % (_("No more requests are pending."),
                       _("Back"))

        else:
            out += """
            <form name="borrower_form" action="%s/admin2/bibcirculation/all_loans" method="get" >
            <br />
            <table id="table_all_loans" class="tablesorter"
                    border="0" cellpadding="0" cellspacing="1">
               <thead>
                    <tr>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                    </tr>
                </thead>
                <tbody>
         """% (CFG_SITE_URL,
               _("Name"),
               _("Item"),
               _('Library'),
               _("Location"),
               _("From"),
               _("To"),
               _("Request date"),
               _("Options"))

            out += """
                <script type="text/javascript">
                    function confirmation(rqid) {
                        var answer = confirm("Delete this request?")
                        if (answer){
            window.location = "%s/admin2/bibcirculation/get_waiting_requests?request_id="+rqid;
                        }
                        else{
                            alert("%s")
                        }
                    }
                </script>
                """ % (CFG_SITE_URL, _("Request not deleted."))

            for (request_id, recid, _barcode, name, borrower_id, library, location,
                 date_from, date_to, request_date) in result:

                title_link = create_html_link(CFG_SITE_URL +
                                    '/admin2/bibcirculation/get_item_details',
                                    {'recid': recid, 'ln': ln},
                                    (book_title_from_MARC(recid)))

                borrower_link = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/get_borrower_details',
                                {'borrower_id': borrower_id, 'ln': ln}, (name))

                out += """
                <tr>
                 <td>%s</td>
                 <td>%s</td>
                 <td>%s</td>
                 <td>%s</td>
                 <td>%s</td>
                 <td>%s</td>
                 <td>%s</td>
                 <td align="center">
                 <input type="button" value='%s' style="background: url(/img/dialog-cancel.png)
                 no-repeat #8DBDD8; width: 75px; text-align: right;"
                 onClick="confirmation(%s)"
                 class="bibcircbutton">

                 <input type=button
                        style="background: url(/img/dialog-yes.png) no-repeat #8DBDD8;
                               width: 150px; text-align: right;"
onClick="location.href='%s/admin2/bibcirculation/create_loan?ln=%s&request_id=%s&recid=%s&borrower_id=%s'"
                 value='%s' class="bibcircbutton">
                 </td>
                </tr>
                """ % (borrower_link,
                       title_link,
                       library,
                       location,
                       date_from,
                       date_to,
                       request_date,
                       _("Cancel"),
                       request_id,
                       CFG_SITE_URL, ln,
                       request_id,
                       recid,
                       borrower_id,
                       _("Create Loan"))

            out += """
                    </tbody>
                    </table>
                    </form>

                    <div id="pager" class="pager">
                        <form>
                            <br />
                            <img src="/img/sb.gif" class="first" />
                            <img src="/img/sp.gif" class="prev" />
                            <input type="text" class="pagedisplay" />
                            <img src="/img/sn.gif" class="next" />
                            <img src="/img/se.gif" class="last" />
                            <select class="pagesize">
                                <option value="10" selected="selected">10</option>
                                <option value="20">20</option>
                                <option value="30">30</option>
                                <option value="40">40</option>
                            </select>
                        </form>
                    </div>
                    """
            out += """
                    <div class="back" style="position: relative; top: 5px;">
                        <br />
                        <table class="bibcirctable">
                            <tr>
                                <td>
                                <input type=button value='%s' onClick="history.go(-1)"
                                        class="formbutton"></td>
                            </tr>
                        </table>
                    <br />
                    <br />
                    </form>
                    </div>
                    </div>
                    """ % (_("Back"))

        return out

    def tmpl_loan_return(self, infos, ln=CFG_SITE_LANG):
        """
        Template for the admin interface. Used when a book return.

        @param ln: language
        """

        out = self.tmpl_infobox(infos, ln)

        _ = gettext_set_language(ln)

        out += load_menu(ln)

        out += """
        <form name="return_form"
              action="%s/admin2/bibcirculation/loan_return_confirm?ln=%s" method="post">
        <div class="bibcircbottom">
        <br />
        <br />
        <br />
        <table class="bibcirctable_contents">
          <tr align="center">
            <td class="bibcirctableheader">
            %s
            <input type="text" size=45 id="barcode" name="barcode"
                   style='border: 1px solid #cfcfcf'>
            <script language="javascript" type="text/javascript">
                document.getElementById("barcode").focus();
            </script>
            </td>

          </tr>
        </table>

        """ % (CFG_SITE_URL, ln,
               _("Barcode"))

        out += """
        <br />
        <table class="bibcirctable_contents">
          <tr align="center">
            <td>
              <input type="reset" name="reset_button" value='%s' class="formbutton">
              <input type="submit" name="ok_button" value='%s' class="formbutton">
            </td>
          </tr>
        </table>
        <br />
        <br />
        <br />
        </div>
        </form>
        """ % (_("Reset"),
               _("OK"))

        return out

    def tmpl_loan_return_confirm(self, infos, borrower_name, borrower_id, recid,
                                barcode, return_date, result, ln=CFG_SITE_LANG):
        """
        @param borrower_name: person who returned the book
        @param id_bibrec: book's recid
        @param barcode: book copy's barcode
        @param ln: language
        """

        _ = gettext_set_language(ln)

        out = load_menu(ln)

        borrower_link = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/get_borrower_details',
                                {'borrower_id': borrower_id, 'ln': ln},
                                (borrower_name))

        title_link = create_html_link(CFG_SITE_URL +
                                    '/admin2/bibcirculation/get_item_details',
                                    {'recid': recid, 'ln': ln},
                                    (book_title_from_MARC(recid)))

        if len(result) == 0 and len(infos) == 0:
            out += """
            <script type="text/javascript">
                $(window).keydown(function(event){
                    window.location.href="%(url)s/admin2/bibcirculation/loan_return?ln=%(ln)s";
                });
            </script>
            """ % {'url': CFG_SITE_URL, 'ln': ln}

        out += """
           <form name="return_form"
                 action="%s/admin2/bibcirculation/loan_return?ln=%s" method="get" >
             <br />
             <div class="infoboxsuccess">""" % (CFG_SITE_URL, ln)

        out += _("The item %(x_strong_tag_open)s%(x_title)s%(x_strong_tag_close)s, with barcode %(x_strong_tag_open)s%(x_barcode)s%(x_strong_tag_close)s, has been returned with success.") % {'x_title': book_title_from_MARC(recid), 'x_barcode': barcode, 'x_strong_tag_open': '<strong>', 'x_strong_tag_close': '</strong>'}
        out += """</div>
                  <br />"""

        for info in infos:
            out += """<div class="infobox">"""
            out += info
            out += """</div> <br /> """

        if len(result) > 0:
            out += """
             <br />
             <div class="infoboxmsg">%s</div>
             <br />
            """ % (_("The next(pending) request on the returned book is shown below."))

        (_book_title, book_year, book_author,
                    book_isbn, book_editor) = book_information_from_MARC(recid)

        if book_isbn:
            book_cover = get_book_cover(book_isbn)
        else:
            book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)

        out += """

        <table class="bibcirctable">
            <tr valign='top'>
                <td width="350">
                    <table class="bibcirctable">
                        <th class="bibcirctableheader" align='left'>%s</th>
                    </table>
                    <style type="text/css"> @import url("/css/tablesorter.css"); </style>
                    <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
                        <tr>
                            <th width="80">%s</th>
                            <td class="bibcirccontent">%s</td>
                        </tr>
                        <tr>
                            <th width="80">%s</th>
                            <td class="bibcirccontent">%s</td>
                        </tr>
                        <tr>
                            <th width="80">%s</th>
                            <td class="bibcirccontent">%s</td>
                        </tr>
                        <tr>
                            <th width="80">%s</th>
                            <td class="bibcirccontent">%s</td>
                        </tr>
                        <tr>
                            <th width="80">%s</th>
                            <td class="bibcirccontent">%s</td>
                        </tr>
                        <tr>
                            <th width="80">%s</th>
                            <td class="bibcirccontent">%s</td>
                        </tr>
                        <tr>
                            <th width="80">%s</th>
                            <td class="bibcirccontent">%s</td>
                        </tr>
                    </table>
                </td>
                <td class="bibcirccontent">
                    <img style='border: 1px solid #cfcfcf' src="%s" alt="Book Cover"/>
                </td>
            </tr>

            <input type=hidden name=recid value='%s'>
            <input type=hidden name=barcode value='%s'>
        </table>

        """ % (_("Loan informations"),
               _("Borrower"), borrower_link,
               _("Item"), title_link,
               _("Author"), book_author,
               _("Year"), book_year,
               _("Publisher"), book_editor,
               _("ISBN"), book_isbn,
               _("Return date"), return_date,
               str(book_cover),
               recid,
               barcode)


        if result:
            out += """
            <style type="text/css"> @import url("/css/tablesorter.css"); </style>
            <script src="/%s" type="text/javascript"></script>
            <script type="text/javascript">
            $(document).ready(function() {
              $('#table_requests').tablesorter({widthFixed: true, widgets: ['zebra']})
            });
            </script>
            <table class="bibcirctable">
              <tr>
                <td class="bibcirctableheader">%s</td>
              </tr>
            </table>
            <table id="table_requests" class="tablesorter" border="0"
                                       cellpadding="0" cellspacing="1">
            <thead>
              <tr>
                <th>%s</th>
                <th>%s</th>
                <th>%s</th>
                <th>%s</th>
                <th>%s</th>
                <th>%s</th>
                <th>%s</th>
              </tr>
            </thead>
            </tbody>

            """% (JQUERY_TABLESORTER,
                  _("Waiting requests"),
                  _("Name"),
                  _("Item"),
                  _("Request status"),
                  _("From"),
                  _("To"),
                  _("Request date"),
                  _("Request options"))

            for (request_id, name, recid, status, date_from,
                 date_to, request_date) in result:

                out += """
                <tr>
                  <td>%s</td>
                  <td>%s</td>
                  <td>%s</td>
                  <td>%s</td>
                  <td>%s</td>
                  <td>%s</td>
                  <td>

                 <input type=button id="bor_select" onClick="location.href='%s/admin2/bibcirculation/make_new_loan_from_request?ln=%s&check_id=%s&barcode=%s'"
                 value='%s' class="bibcircbutton" style="background: url(/img/dialog-yes.png) no-repeat #8DBDD8; width: 125px; text-align: right;"></td>
                 </td>
                 </tr>
                 """ % (
                        name, book_title_from_MARC(recid),
                        status, date_from, date_to,
                        request_date, CFG_SITE_URL, ln, request_id, barcode,
                        _('Select request'))

            out += """
                </table>
              <br />
              <br />
            </form>
            """

        else:
            out += """
            </form>
            <form name="return_form"
                  action="%s/admin2/bibcirculation/loan_return_confirm?ln=%s" method="post">
            <div class="bibcircbottom">
            <table class="bibcirctable">
              <tr>
                <td class="bibcirctableheader">
                %s
                </td>
              </tr>
              <tr>
                <td class="bibcirctableheader">
                %s
                <input type="text" size=45 id="barcode" name="barcode"
                       style='border: 1px solid #cfcfcf'>
                <script language="javascript" type="text/javascript">
                    document.getElementById("barcode").focus();
                </script>
                </td>
              </tr>
            </table>

            """ % (CFG_SITE_URL, ln,
                   _("Return another book"), _("Barcode"))

            out += """
            <br />
            <table class="bibcirctable">
              <tr>
                <td>
                  <input type="reset" name="reset_button" value='%s' class="formbutton">
                  <input type="submit" name="ok_button" value='%s' class="formbutton">
                </td>
              </tr>
            </table>
            <br />
            <br />
            <br />
            </div>
            </form>
            """ % (_("Reset"),
                   _("OK"))

        return out

    def tmpl_index(self, ln=CFG_SITE_LANG):
        """
        Main page of the Admin interface.
        """

        _ = gettext_set_language(ln)

        out = load_menu(ln)

        out += """
        <div class="bibcircbottom">
        <br />
        <div class="bibcircsubtitle">
        %s
        </div>
        <br />
        """ % (_("Welcome to Invenio BibCirculation Admin"))

        out += """
        <br /><br />
        <br /><br />
        <br /><br />
        <br /><br />
        <br /><br />
        </div>
        """

        return out

    def tmpl_borrower_search(self, infos, redirect_to_new_request=False,
                             ln=CFG_SITE_LANG):
        """
        Template for the admin interface. Search borrower.

        @param ln: language
        """
        _ = gettext_set_language(ln)


        if CFG_CERN_SITE == 1:
            id_string = 'ccid'
        else:
            id_string = _('id')

        out = self.tmpl_infobox(infos, ln)

        out += load_menu(ln)

        if redirect_to_new_request:
            redirect_to_new_request = 'yes'
        else:
            redirect_to_new_request = 'no'

        new_borrower_link = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/add_new_borrower_step1',
                                {'ln': ln}, _("register new borrower"))

        out += """
        <div class="bibcircbottom">
        <br />
        <br />
        <br />
        <form name="borrower_search"
              action="%s/admin2/bibcirculation/borrower_search_result"
              method="get" >
             <table class="bibcirctable">
               <tr align="center">
                 <td class="bibcirctableheader">%s
                   <input type="radio" name="column" value="id">%s
                   <input type="radio" name="column" value="name" checked>%s
                   <input type="radio" name="column" value="email">%s
                   <input type="hidden" name="redirect_to_new_request" value="%s">
                   <br>
                   <br>
                 </td>
               </tr>
               <tr align="center">
                 <td>
                    <input type="text" size="45" name="string" id="string"
                           style='border: 1px solid #cfcfcf'>
                    <script language="javascript" type="text/javascript">
                            document.getElementById("string").focus();
                    </script>
                 </td>
               </tr>
        """ % (CFG_SITE_URL,
               _("Search borrower by"), id_string,
               _("name"), _("email"),
               redirect_to_new_request)

        if not CFG_CERN_SITE:
            out += """
                <tr align="center">
                    <td class="bibcirctableheader">%s</td>
                </tr>
            """ % (new_borrower_link)

        out += """
         </table>
        <br />
        <table class="bibcirctable">
             <tr align="center">
               <td>
                 <input type=button value='%s'
                        onClick="history.go(-1)" class="formbutton">
                 <input type="submit" value='%s' class="formbutton">
               </td>
             </tr>
        </table>
        <form>
        <br />
        <br />
        <br />
        <br />
        </div>
        """ % (_("Back"), _("Search"))


        return out

    def tmpl_borrower_search_result(self, result, redirect_to_new_request=False,
                                          ln=CFG_SITE_LANG):
        """
        When the admin's feature 'borrower_seach' is used, this template
        shows the result.

        @param result: search result
        @type result:list

        @param ln: language
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += load_menu(ln)

        if len(result) == 0:
            if CFG_CERN_SITE:
                message = _("0 borrowers found.") + ' ' +_("Search by CCID.")
            else:
                new_borrower_link = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/add_new_borrower_step1',
                                {'ln': ln}, _("Register new borrower."))
                message = _("0 borrowers found.") + ' ' + new_borrower_link

            out += """
            <div class="bibcircbottom">
            <br />
            <div class="bibcircinfoboxmsg">%s</div>
            <br />
          """ % (message)

        else:
            out += """
        <style type="text/css"> @import url("/css/tablesorter.css"); </style>
        <div class="bibcircbottom" align="center">
        </form>
        <br />
        <table class="bibcirctable">
          <tr align="center">
            <td class="bibcirccontent">
              <strong>%s borrower(s) found</strong>
            </td>
          </tr>
        </table>
        <br />
        <table class="tablesortersmall" border="0" cellpadding="0" cellspacing="1">
          <th align="center">%s</th>
        """ % (len(result), _("Borrower(s)"))


            for (borrower_id, name) in result:
                if redirect_to_new_request:
                    borrower_link = create_html_link(CFG_SITE_URL +
                            '/admin2/bibcirculation/create_new_request_step1',
                            {'borrower_id': borrower_id, 'ln': ln}, (name))
                else:
                    borrower_link = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/get_borrower_details',
                                {'borrower_id': borrower_id, 'ln': ln}, (name))

                out += """
            <tr align="center">
                 <td width="70">%s
                 <input type=hidden name=uid value='%s'></td>
            </tr>

            """ % (borrower_link, borrower_id)

        out += """
             </table>
             <br />
             <table class="bibcirctable">
             <tr align="center">
                <td>
                    <input type=button value='%s'
                           onClick="history.go(-1)"
                           class="formbutton">
                </td>
             </tr>
        </table>
        <br />
        <br />
        <br />
        </form>
        </div>
        """ % (_("Back"))

        return out

    def tmpl_item_search(self, infos, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += load_menu(ln)

        out += """
        <div class="bibcircbottom">
        <form name="search_form"
              action="%s/admin2/bibcirculation/item_search_result"
              method="get" >
        <br />
        <br />
        <br />
        <input type=hidden value="0">
        <input type=hidden value="10">
        """ % (CFG_SITE_URL)

        out += """
        <table class="bibcirctable">
          <tr align="center">
            <td class="bibcirctableheader">%s
              <input type="radio" name="f" value="">%s
              <input type="radio" name="f" value="barcode" checked>%s
              <input type="radio" name="f" value="recid">%s
              <br />
              <br />
            </td>
          </tr>
          """ % (_("Search item by"), _("Item details"), _("barcode"), _("recid"))

        out += """
          <tr align="center">
            <td>
                <input type="text" size="50" name="p" id="p" style='border: 1px solid #cfcfcf'>
                <script language="javascript" type="text/javascript">
                    document.getElementById("p").focus();
                </script>
            </td>
          </tr>
            """

        out += """
            </td>
          </tr>
        </table>
        <br />
        <table class="bibcirctable">
          <tr align="center">
            <td>
              <input type=button   value='%s' class="formbutton" onClick="history.go(-1)">
              <input type="submit" value='%s' class="formbutton">
            </td>
          </tr>
        </table>
        <br />
        <br />
        <br />
        <br />
        </div>
        <form>
        """ % (_("Back"), _("Search"))

        return out

    def tmpl_item_search_result(self, result, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = load_menu(ln)

        try:
            number_of_results = len(result)
        except:
            number_of_results = 1

        if result == None:
            out += """
            <div class="bibcircbottom">
            <br />
            <div class="bibcircinfoboxmsg">%s</div>
            <br />
            """ % (_("0 item(s) found."))
### por aqui voy ###
        else:
            out += """
        <style type="text/css"> @import url("/css/tablesorter.css"); </style>
        <div class="bibcircbottom">
        <br />
        <table class="bibcirctable">
          <tr align="center">
            <td>
               <strong>%s</strong>
            </td>
          </tr>
        </table>
        <br />
          <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
            <thead>
              <tr>
                <th>%s</th>
                <th>%s</th>
                <th>%s</th>
                <th>%s</th>
              </tr>
            </thead>
          <tbody>
        """ % (_("%(x_num)i items found.", x_num=number_of_results), _("Title"),
               _("Author"), _("Publisher"),
               _("# copies"))

### FIXME: If one result -> go ahead ###
            for recid in result:

                (book_author, book_editor,
                 book_copies) = get_item_info_for_search_result(recid)

                title_link = create_html_link(CFG_SITE_URL +
                                    '/admin2/bibcirculation/get_item_details',
                                    {'recid': recid, 'ln': ln},
                                    (book_title_from_MARC(recid)))

                out += """
                <tr>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                </tr>
                """ % (title_link, book_author,
                       book_editor, book_copies)

        out += """
          </tbody>
          </table>
        <br />
        <table class="bibcirctable">
          <tr align="center">
            <td>
              <input type=button value='%s'
               onClick="history.go(-1)" class="formbutton">
            </td>
          </tr>
        </table>
        <br />
        <br />
        <br />
        </div>

        """ % (_("Back"))

        return out

    def tmpl_loan_on_desk_step1(self, result, key, string, infos,
                                ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)
        out += load_menu(ln)

        out += """
        <div class="bibcircbottom">
        <form name="step1_form1" action="%s/admin2/bibcirculation/loan_on_desk_step1"
              method="get" >
        <br />
        <br />
        <br />
          <table class="bibcirctable" align="center">
            """ % (CFG_SITE_URL)

        if CFG_CERN_SITE == 1:

            out += """
                <tr>
                   <td class="bibcirctableheader" align="center">%s
                   """ % (_("Search user by"))

            if key == 'email':
                out += """
                   <input type="radio" name="key" value="ccid">%s
                   <input type="radio" name="key" value="name">%s
                   <input type="radio" name="key" value="email" checked>%s
                   """ % ('ccid', _('name'), _('email'))

            elif key == 'name':
                out += """
                   <input type="radio" name="key" value="ccid">%s
                   <input type="radio" name="key" value="name" checked>%s
                   <input type="radio" name="key" value="email">%s
                   """ % ('ccid', _('name'), _('email'))

            else:
                out += """
                   <input type="radio" name="key" value="ccid" checked>%s
                   <input type="radio" name="key" value="name">%s
                   <input type="radio" name="key" value="email">%s
                   """ % ('ccid', _('name'), _('email'))

        else:
            out += """
                 <tr>
                   <td align="center" class="bibcirctableheader">%s
                   """ % (_("Search borrower by"))

            if key == 'email':
                out += """
                   <input type="radio" name="key" value="id">%s
                   <input type="radio" name="key" value="name">%s
                   <input type="radio" name="key" value="email" checked>%s
                   """ % (_('id'), _('name'), _('email'))

            elif key == 'id':
                out += """
                   <input type="radio" name="key" value="id" checked>%s
                   <input type="radio" name="key" value="name">%s
                   <input type="radio" name="key" value="email">%s
                   """ % (_('id'), _('name'), _('email'))

            else:
                out += """
                   <input type="radio" name="key" value="id">%s
                   <input type="radio" name="key" value="name" checked>%s
                   <input type="radio" name="key" value="email">%s
                   """ % (_('id'), _('name'), _('email'))

        out += """
                    <br><br>
                    </td>
                    </tr>
                    <tr>
                        <td align="center">
                            <input type="text" size="40" id="string" name="string"
                                   value='%s' style='border: 1px solid #cfcfcf'>
                            <script language="javascript" type="text/javascript">
                                document.getElementById("string").focus();
                            </script>
                        </td>
                    </tr>
                    <tr>
                        <td align="center">
                            <br>
                            <input type="submit" id="bor_search" value="%s" class="formbutton">
                        </td>
                    </tr>

                   </table>
          </form>
        """ % (string or '', _("Search"))

        if result:
            out += """
            <br />
            <form name="step1_form2"
                  action="/admin2/bibcirculation/loan_on_desk_step2"
                  method="get">
            <table class="bibcirctable">
              <tr width="200">
                <td align="center">
                  <select name="user_id" size="8" style='border: 1px solid #cfcfcf; width:200'>

              """
            for user_info in result:
                name = user_info[0]
                user_id = user_info[2]
                out += """
                       <option value='%s'>%s
                       """ % (name, user_id)

            out += """
                    </select>
                  </td>
                </tr>
              </table>
              <table class="bibcirctable">
                <tr>
                  <td align="center">
                    <input type="submit" value='%s' class="formbutton">
                  </td>
                </tr>
              </table>
            </form>
            """ % (_("Select user"))

        out += """
              <br />
              <br />
              <br />
              </div>
              """

        return out

    def tmpl_loan_on_desk_step2(self, user_id, infos, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """
        user_info = db.get_borrower_details(user_id)
        (borrower_id, ccid, name, email, phone, address, mailbox) = user_info

        _ = gettext_set_language(ln)

        display_id = borrower_id
        id_string = _("ID")
        if CFG_CERN_SITE == 1:
            display_id = ccid
            id_string = _("CCID")

        out = self.tmpl_infobox(infos, ln)

        out += load_menu(ln)

        out += """
            <div class="bibcircbottom">
            <style type="text/css"> @import url("/css/tablesorter.css"); </style>
            <form name="step2_form" action="%s/admin2/bibcirculation/loan_on_desk_step3"
                  method="get" >
              <br />
              <table class="bibcirctable">
                          <tr>
                               <td class="bibcirctableheader">%s</td>
                          </tr>
                """ % (CFG_SITE_URL, _("User information"))

        out += """
              </table>
              <table class="tablesortersmall" border="0" cellpadding="0" cellspacing="1">
                <tr>
                  <th width="70">%s</th>
                  <td>%s</td>
                </tr> """ % (id_string, display_id)

        out += """
                <tr>
                  <th width="70">%s</th>
                  <td>%s</td>
                </tr>
                <tr>
                  <th width="70">%s</th>
                  <td>%s</td>
                  </tr>
                <tr>
                  <th width="70">%s</th>
                  <td>%s</td>
                </tr>
                <tr>
                  <th width="70">%s</th>
                  <td>%s</td>
                </tr>
                <tr>
                  <th width="70">%s</th>
                  <td>%s</td>
                </tr>
                </table>
                <br />
                <table class="bibcirctable">
                  <tr>
                    <td class="bibcirctableheader" width="77">%s</td>
                    <td>
                        <input type="text" size=45 id="barcode" name="barcode"
                               style='border: 1px solid #cfcfcf'>
                        <script language="javascript" type="text/javascript">
                            document.getElementById("barcode").focus();
                        </script>
                    </td>
                  </tr>
                </table>
                <br />
                <table class="bibcirctable">
                <tr>
                  <td>
                       <input type=button value="%s"
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit" id="submit_barcode"
                       value="%s" class="formbutton">

                       <br /><br />""" % (_("Name"), name,
                                          _("Address"), address,
                                          _("Mailbox"), mailbox,
                                          _("Email"), email,
                                          _("Phone"), phone,
                                          _("Enter the barcode"), _("Back"),
                                          _("Continue"))

        out += """<input type=button value="%s"
                        onClick="location.href='%s/admin2/bibcirculation/all_loans?ln=%s'"
                        class="formbutton">""" % (_("See all loans"), CFG_SITE_SECURE_URL, ln)

        out += """<input type=hidden name="user_id" value="%s">

                  </td>
                 </tr>
                </table>
                </form>
                <br />
                <br />
                </div>
                """ % (user_id)

        return out

    def tmpl_loan_on_desk_step3(self, user_id, list_of_books, infos,
                                ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """
        out = self.tmpl_infobox(infos, ln)
        _ = gettext_set_language(ln)

        user_info = db.get_borrower_details(user_id)
        (borrower_id, ccid, name, email, phone, address, mailbox) = user_info

        list_of_barcodes = []

        for book in list_of_books:
            list_of_barcodes.append(book[1])

        display_id = borrower_id
        id_string = _("ID")
        if CFG_CERN_SITE == 1:
            display_id = ccid
            id_string = _("CCID")

        out += load_menu(ln)

        out += """
            <div class="bibcircbottom">
            <style type="text/css"> @import url("/css/tablesorter.css"); </style>
            <script type="text/javascript">
            function groupDatePicker(){
                var index = 0;
                var datepicker = null;
                var datepickerhidden = this.document.getElementById("datepickerhidden")
                    do{
                datepicker = this.document.getElementById("date_picker"+index)
                if(datepicker != null){
                    if (index != 0){
                        datepickerhidden.value += ",";
                    }
                    datepickerhidden.value += datepicker.value ;
                }
                index = index + 1;
            }while(datepicker != null);
            }
            </script>
            <form name="step3_form" action="%s/admin2/bibcirculation/loan_on_desk_step4"
                  method="post" >
              <br />
              <br />
              <input type=hidden name="list_of_barcodes" value="%s">
              <input type=hidden name="datepickerhidden" id="datepickerhidden"  value="">
              <table class="bibcirctable">
                          <tr>
                               <td class="bibcirctableheader">%s</td>
                          </tr>
              </table>
              <table class="tablesortersmall" border="0" cellpadding="0" cellspacing="1">
                <tr>
                  <th width="70">%s</th>
                  <td>%s</td>
                </tr>
                <tr>
                  <th width="70">%s</th>
                  <td>%s</td>
                </tr>
                <tr>
                  <th width="70">%s</th>
                  <td>%s</td>
                </tr>
                <tr>
                  <th width="70">%s</th>
                  <td>%s</td>
                </tr>
                <tr>
                  <th width="70">%s</th>
                  <td>%s</td>
                </tr>
                <tr>
                  <th width="70">%s</th>
                  <td>%s</td>
                </tr>
                </table>
                <br />
                <table class="bibcirctable">
                          <tr>
                               <td class="bibcirctableheader">%s</td>
                          </tr>
                </table>

                <script type="text/javascript" src="%s/vendors/jquery-ui/jquery-ui.min.js"></script>

                <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
                <thead>
                 <tr>
                    <th>%s</th>
                    <th width="65">%s</th>
                    <th width="100">%s</th>
                    <th width="80">%s</th>
                    <th width="130">%s</th>
                    <th>%s</th>
                 </tr>
                </thead>
                <tbody>
                """ % (CFG_SITE_URL, str(list_of_barcodes),
                       _("User information"),
                         id_string, display_id,
                        _("Name"), name,
                        _("Address"), address,
                        _("Mailbox"), mailbox,
                        _("Email"), email,
                        _("Phone"), phone,
                        _("List of borrowed books"),
                        CFG_SITE_URL,
                        _("Item"), _("Barcode"),
                        _("Library"), _("Location"),
                        _("Due date"), _("Write note(s)"))


        iterator = 0

        for (recid, barcode, library_id, location) in list_of_books:

            due_date = renew_loan_for_X_days(barcode)

            library_name = db.get_library_name(library_id)

            out += """
                 <tr>
                    <td>%s</td>
                    <td width="65">%s</td>
                    <td width="100">%s</td>
                    <td width="80">%s</td>
                    <td width="130" class="bibcirccontent">
                    <script type="text/javascript">
                        $(function() {
                            $("%s").datepicker({dateFormat: 'yy-mm-dd', showOn: 'button', buttonImage: "%s/img/calendar.gif", buttonImageOnly: true});
                        });
                    </script>
                    <input type="text" size="12" id="%s" name="%s"
                           value="%s" style='border: 1px solid #cfcfcf'>

                    </td>
                  <td>
                    <textarea name='note' rows="1" cols="40"
                              style='border: 1px solid #cfcfcf'></textarea>
                  </td>
                </tr>
                """ % (book_title_from_MARC(recid), barcode,
                       library_name, location, "#date_picker"+str(iterator),
                       CFG_SITE_URL, "date_picker"+str(iterator),
                       'due_date'+str(iterator), due_date)

            iterator += 1

        out += """
                </tbody>
                </table>
                <br />
                <table class="bibcirctable">
                <tr>
                  <td>
                       <input type=button value="%s"
                       onClick="history.go(-1)" class="formbutton">

                       <input type="submit" id="submit_barcode"
                       value="%s" class="formbutton" onmousedown="groupDatePicker();">

                       <input type=hidden name="user_id" value="%s">
                  </td>
                 </tr>
                </table>
                </form>
                <br />
                <br />
                </div>
                """ % (_("Back"), _("Continue"), user_id)

        return out

    def tmpl_loan_on_desk_confirm(self, barcode,
                                  borrower, infos, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page0
        """

        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += load_menu(ln)

        borrower_email = borrower.split(' [')[0]
        borrower_id = borrower.split(' [')[1]
        borrower_id = int(borrower_id[:-1])

        out += """
        <form name="return_form"
              action="%s/admin2/bibcirculation/register_new_loan"
              method="post" >
            <div class="bibcircbottom">
                <input type=hidden name=borrower_id value="%s">
                <br />
                    <table class="bibcirctable">
                        <tr>
                            <td class="bibcirctableheader" width="70">%s</td>
                            <td class="bibcirccontent" width="600">%s</td>
                        </tr>
        """ % (CFG_SITE_URL,
               borrower_id,
               _("Borrower"),
               borrower_email)

        for (bar) in barcode:
            recid = db.get_id_bibrec(bar)

            out += """
                        <tr>
                            <td class="bibcirctableheader" width="70">%s</td>
                            <td class="bibcirccontent" width="600">%s</td>
                        </tr>
                <input type=hidden name=barcode value='%s'>
            """ % (_("Item"),
                   book_title_from_MARC(recid),
                   bar)


        out += """
        </table>
        <br />
        <table class="bibcirctable_contents">
             <tr>
                  <td>
                       <input type=button value='%s' onClick="history.go(-1)" class="formbutton">
                       <input type="submit"   value="%s" class="formbutton">
                  </td>
             </tr>
        </table>
        <br />
        </div>
        </form>
        """ % (_("Back"),
               _("Confirm"))


        return out

    def tmpl_register_new_loan(self, borrower_info, infos,
                               recid, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        (borrower_id, ccid, name,
         email, phone, address, mailbox) = borrower_info
        (book_title, book_year, book_author,
         book_isbn, book_editor) = book_information_from_MARC(recid)

        _ = gettext_set_language(ln)

        display_id = borrower_id
        id_string = _("ID")
        if CFG_CERN_SITE == 1:
            display_id = ccid
            id_string = _("CCID")

        out = load_menu(ln)
        out += "<br />"
        out += self.tmpl_infobox(infos, ln)

        out += """
        <style type="text/css"> @import url("/css/tablesorter.css"); </style>
        <div class="bibcircbottom">
        <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">
            <tr>
                <th width="100">%s</th>
                <td>%s</td>
            </tr>
            <tr>
                <th width="100">%s</th>
                <td>%s</td>
            </tr>
            <tr>
                <th width="100">%s</th>
                <td>%s</td>
            </tr>
            <tr>
                <th width="100">%s</th>
                <td>%s</td>
            </tr>
            <tr>
                <th width="100">%s</th>
                <td>%s</td>
            </tr>
        </table>
        <br />
        <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">
            <tr>
                <th width="100">%s</th>
                <td>%s</td>
            </tr>
            <tr>
                <th width="100">%s</th>
                <td>%s</td>
            </tr>
            <tr>
                <th width="100">%s</th>
                <td>%s</td>
            </tr>
            <tr>
                <th width="100">%s</th>
                <td>%s</td>
            </tr>
            <tr>
                <th width="100">%s</th>
                <td>%s</td>
            </tr>
            <tr>
                <th width="100">%s</th>
                <td>%s</td>
            </tr>
        </table>
        <br />
        <table class="bibcirctable">
            <td>
                <input type="button"
                       value="%s" class="formbutton"
                    onClick="location.href='%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s'"
                >
                <input type="button"
                       value="%s" class="formbutton"
    onClick="location.href='%s/admin2/bibcirculation/register_new_loan?ln=%s&print_data=true'"
                >
            </td>
        </table>
        <br />
        <br />
        </div>
        """ % (id_string, display_id,
               _("Name"), name,
               _("Address"), address,
               _("Mailbox"), mailbox,
               _("Email"), email,
               _("Phone"), phone,
               _("Title"), book_title,
               _("Author(s)"), book_author,
               _("Year"), book_year,
               _("Publisher"), book_editor,
               _("ISBN"), book_isbn,
               _("Back to home"),
               CFG_SITE_URL, ln,
               _("Print loan information"),
               CFG_SITE_URL, ln)

        return out


    def tmpl_create_new_loan_step1(self, borrower, infos, ln=CFG_SITE_LANG):
        """
        Display the borrower's information and a form where it is
        possible to search for an item.

        @param borrower: borrower's information
        @type borrower: tuple

        @param infos: information to be displayed in the infobox
        @type infos: list

        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += load_menu(ln)

        (borrower_id, ccid, name, email, phone, address, mailbox) = borrower

        display_id = borrower_id
        id_string = _("ID")
        if CFG_CERN_SITE == 1:
            display_id = ccid
            id_string = _("CCID")

        out += """
            <form name="create_new_loan_form1"
                  action="%s/admin2/bibcirculation/create_new_loan_step2"
                  method="post" >
            <div class="bibcircbottom">
            <input type=hidden name=borrower_id value="%s">
            <br />
            <table class="bibcirctable">
                 <tr>
                      <td class="bibcirctableheader">%s</td>
                 </tr>
             </table>
            </form>
            <table class="bibcirctable">
                 <tr>
                      <td width="100">%s</td>
                      <td class="bibcirccontent">%s</td>
                 </tr>
                     <tr>
                      <td width="100">%s</td>
                      <td class="bibcirccontent">%s</td>

                 </tr>
                 <tr>
                      <td width="100">%s</td>
                      <td class="bibcirccontent">%s</td>
                 </tr>
                 <tr>
                      <td width="100">%s</td>
                      <td class="bibcirccontent">%s</td>
                 </tr>
                 <tr>
                      <td width="100">%s</td>
                      <td class="bibcirccontent">%s</td>
                 </tr>
                 <tr>
                      <td width="100">%s</td>
                      <td class="bibcirccontent">%s</td>
                 </tr>
            </table>
            """% (CFG_SITE_URL,
                  borrower_id,
                  _("Personal details"),
                  id_string, display_id,
                  _("Name"), name,
                  _("Address"), address,
                  _("Mailbox"), mailbox,
                  _("Email"), email,
                  _("Phone"), phone)


        out += """
        <br />
        <table class="bibcirctable">
                  <tr>
                     <td class="bibcirctableheader">%s</td>
                  </tr>
                  <tr>
                     <td><input type="text" size="50" name="barcode" style='border: 1px solid #cfcfcf'></td>
                  </tr>
             </table>
             """ % (_("Barcode"))

        out += """
              <br />
              <table class="bibcirctable">
                <tr>
                  <td class="bibcirctableheader">%s</td>
                </tr>
                <tr>
                  <td><textarea name='new_note' rows="4" cols="43" style='border: 1px solid #cfcfcf'></textarea></td>
                </tr>
              </table>
              <br />
              """ % (_("Write notes"))

        out += """
        <table class="bibcirctable">
             <tr>
                  <td>
                       <input type=button value="%s" onClick="history.go(-1)" class="formbutton">
                       <input type="submit"   value="%s" class="formbutton">
                  </td>
             </tr>
        </table>
        <br />
        <br />
        <br />
        </div>
        </form>
        """ % (_("Back"),
               _("Confirm"))

        return out


    def tmpl_create_new_request_step1(self, borrower, infos, result, p, f,
                                      ln=CFG_SITE_LANG):
        """
        Display the borrower's information and the form where it is
        possible to search for an item.

        @param borrower: borrower's information.
        @type borrower: tuple

        @param infos: information to be displayed in the infobox.
        @type infos: list

        @param result: result of searching for an item, using p and f.
        @type result: list

        @param p: pattern which will be used in the search process.
        @type p: string

        @param f: field which will be used in the search process.
        @type f: string

        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += load_menu(ln)

        (borrower_id, ccid, name, email, phone, address, mailbox) = borrower

        display_id = borrower_id
        id_string = _("ID")
        if CFG_CERN_SITE == 1:
            display_id = ccid
            id_string = _("CCID")

        out += """
            <style type="text/css"> @import url("/css/tablesorter.css"); </style>

            <div class="bibcircbottom">

            <br />

            <table class="bibcirctable">
            <tbody>
                <tr>
                    <td width="500" valign="top">
                        <form name="create_new_loan_form1"
                          action="%s/admin2/bibcirculation/create_new_request_step1"
                          method="get" >
                            <input type=hidden name=borrower_id value="%s">
                            <table class="bibcirctable">
                                <tr align="center">
                                    <td class="bibcirctableheader">%s
            """ % (CFG_SITE_URL, borrower_id, _("Search item by"))

        if f == 'barcode':
            out += """
                                <input type="radio" name="f" value="">%s
                                <input type="radio" name="f" value="barcode" checked>%s
                                <input type="radio" name="f" value="author">%s
                                <input type="radio" name="f" value="title">%s
              """ % (_("Any field"), _("barcode"), _("author"), _("title"))

        elif f == 'author':
            out += """
                                <input type="radio" name="f" value="">%s
                                <input type="radio" name="f" value="barcode">%s
                                <input type="radio" name="f" value="author" checked>%s
                                <input type="radio" name="f" value="title">%s
              """ % (_("Any field"), _("barcode"), _("author"), _("title"))

        elif f == 'title':
            out += """
                                <input type="radio" name="f" value="">%s
                                <input type="radio" name="f" value="barcode">%s
                                <input type="radio" name="f" value="author">%s
                                <input type="radio" name="f" value="title" checked>%s
              """ % (_("Any field"), _("barcode"), _("author"), _("title"))

        else:
            out += """
                                <input type="radio" name="f" value="" checked>%s
                                <input type="radio" name="f" value="barcode">%s
                                <input type="radio" name="f" value="author">%s
                                <input type="radio" name="f" value="title">%s
              """ % (_("Any field"), _("barcode"), _("author"), _("title"))

        out += """
                                        <br />
                                        <br />
                                    </td>
                                </tr>
                                <tr align="center">
                                    <td>
                                        <input type="text" size="50" name="p" value='%s'
                                            style='border: 1px solid #cfcfcf'>
                                    </td>
                                </tr>
                            </table>
                            <br />
                            <table class="bibcirctable">
                                <tr align="center">
                                    <td>
                                        <input type=button value='%s' onClick="history.go(-1)"
                                            class="formbutton">
                                        <input type="submit" value='%s' name='search'
                                            class="formbutton">
                                    </td>
                                </tr>
                            </table>
                        </form>
        """ % (p or '', _("Back"), _("Search"))

        if result:
            out += """
            <br />
                        <form name="form2"
                            action="%s/admin2/bibcirculation/create_new_request_step2"
                            method="get" >
                            <table class="bibcirctable">
                                <tr width="200">
                                    <td align="center">
                                        <select name="recid" size="12" style='border: 1px
                                            solid #cfcfcf; width:77%%'>

              """ % (CFG_SITE_URL)
            for recid in result:
                out += """
                       <option value ='%s'>%s

                       """ % (recid, book_title_from_MARC(recid))

            out += """
                                        </select>
                                    </td>
                                </tr>
                            </table>
                            <table class="bibcirctable">
                                <tr>
                                    <td ALIGN="center">
                                        <input type="submit" value='%s' class="formbutton">
                                    </td>
                                </tr>
                            </table>
                            <input type=hidden name=borrower_id value="%s">
                        </form>
                    """ % (_("Select item"), borrower_id)

        out += """
                    </td>
                    <td width="200" align="center" valign="top">
                    <td align="center" valign="top">
                        <table class="bibcirctable">
                            <tr>
                                <td class="bibcirctableheader">%s</td>
                            </tr>
                        </table>
                        </form>
                           <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
                             <tr>
                               <th width="100">%s</th>
                               <td>%s</td>
                             </tr>
                             <tr>
                               <th width="100">%s</th>
                               <td>%s</td>
                             </tr>
                             <tr>
                               <th width="100">%s</th>
                               <td>%s</td>
                             </tr>
                             <tr>
                               <th width="100">%s</th>
                               <td>%s</td>
                             </tr>
                             <tr>
                               <th width="100">%s</th>
                               <td>%s</td>
                             </tr>
                             <tr>
                               <th width="100">%s</th>
                               <td>%s</td>
                             </tr>
                        </table>
                    </td>
                </tr>

            <br />

            """% (_("Borrower details"),
                  id_string, display_id,
                  _("Name"), name,
                  _("Address"), address,
                  _("Mailbox"), mailbox,
                  _("Email"), email,
                  _("Phone"), phone)


        out += """
            </table>
            <br />
            <br />
            <br />
            <br />
            <br />

              </div>


              """

        return out

    def tmpl_create_new_request_step2(self, user_info, holdings_information,
                                      recid, ln=CFG_SITE_LANG):
        """
        @param borrower_id: identify the borrower. Primary key of crcBORROWER.
        @type borrower_id: int

        @param holdings_information: information about the holdings.
        @type holdings_information: list

        @param recid: identify the record. Primary key of bibrec.
        @type recid: int
        """

        _ = gettext_set_language(ln)

        if not holdings_information:
            return _("This item has no holdings.")

        out = load_menu(ln)

        out += """
                 <div class="bibcircbottom">
                 <br />
                 <br />
                 <br />
                   <table class="bibcirctable">
                   <tr>
                   <td class="bibcirctableheader">%s</td>
                   <td class="bibcirctableheader">%s</td>
                   <td class="bibcirctableheader" align="center">%s</td>
                   <td class="bibcirctableheader" align="center">%s</td>
                   <td class="bibcirctableheader" align="center">%s</td>
                   <td class="bibcirctableheader" align="center">%s</td>
                   <td class="bibcirctableheader "align="center">%s</td>
                   <td class="bibcirctableheader "align="center">%s</td>
                   <td class="bibcirctableheader"></td>
                   </tr>
                   """ % (_("Barcode"), _("Library"), _("Collection"),
                          _("Location"), _("Description"), _("Loan period"),
                          _("Status"), _("Due date"))

        for (barcode, library, collection, location, description, loan_period,
             status, due_date) in holdings_information:
            out += """
                     <tr onMouseOver="this.className='highlight'" onmouseout="this.className='normal'">
                          <td class="bibcirccontent">%s</td>
                          <td class="bibcirccontent">%s</td>
                          <td class="bibcirccontent" align="center">%s</td>
                          <td class="bibcirccontent" align="center">%s</td>
                          <td class="bibcirccontent" align="center">%s</td>
                          <td class="bibcirccontent" align="center">%s</td>
                          <td class="bibcirccontent" align="center">%s</td>
                          <td class="bibcirccontent" align="center">%s</td>
                          <td class="bibcirccontent" align="right">
                          <input type=button onClick="location.href='%s/admin2/bibcirculation/place_new_request_step2?ln=%s&barcode=%s&recid=%s&user_info=%s,%s,%s,%s,%s,%s,%s'"
                          value='%s' class="formbutton"></td>
                     </tr>

                """ % (barcode, library, collection, location,
                       description, loan_period, status, due_date,
                       CFG_SITE_URL, ln, barcode, recid, user_info[0],
                       user_info[1], user_info[2], user_info[3],
                       user_info[4], user_info[5], user_info[6],
                       _("Request"))

        out += """
           </table>
           <br />
           <br />
           <br />
           </div>
           """

        return out

    def tmpl_create_new_request_step3(self, borrower_id, barcode, recid,
                                      ln=CFG_SITE_LANG):
        """
        @param borrower_id: identify the borrower. Primary key of crcBORROWER.
        @type borrower_id: int

        @param barcode: identify the item. Primary key of crcITEM.
        @type barcode: string

        @param recid: identify the record. Primary key of bibrec.
        @type recid: int

        @param ln: language
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += load_menu(ln)

        out += """

        <script type="text/javascript" src="%s/vendors/jquery-ui/jquery-ui.min.js"></script>

        <form name="request_form" action="%s/admin2/bibcirculation/create_new_request_step4"
              method="post" >
        <div class="bibcircbottom">
        <br />
        <br />
        <br />
        <table class="bibcirctable_contents">
          <tr class="bibcirctableheader" align='center'>
            <td>%s</td>
          </tr>
        </table>
        <br />
        <table class="bibcirctable_contents">
          <tr>
            <td width="90" class="bibcirctableheader" align='right'>%s</td>
            <td align='left'>

                <script type="text/javascript">
                    $(function(){
                        $("#date_picker1").datepicker({dateFormat: 'yy-mm-dd', showOn: 'button', buttonImage: "%s/img/calendar.gif", buttonImageOnly: true});
                    });
                </script>
                <input type="text" size="12" id="date_picker1" name="period_from" value="%s" style='border: 1px solid #cfcfcf'>

            </td>
          </tr>
        </table>

        <table class="bibcirctable_contents">
          <tr>
            <td width="90" class="bibcirctableheader" align='right'>%s</td>
            <td align='left'>

                <script type="text/javascript">
                    $(function(){
                        $("#date_picker2").datepicker({dateFormat: 'yy-mm-dd', showOn: 'button', buttonImage: "%s/img/calendar.gif", buttonImageOnly: true});
                    });
                </script>
                <input type="text" size="12" id="date_picker2" name="period_to" value="%s" style='border: 1px solid #cfcfcf'>

            </td>
          </tr>
        </table>
        <br />
        <br />
       """ % (CFG_SITE_URL, CFG_SITE_URL,
              _("Enter the period of interest"),
            _("From:  "), CFG_SITE_URL,
            datetime.date.today().strftime('%Y-%m-%d'),
            _("To:  "), CFG_SITE_URL,
    (datetime.date.today() + datetime.timedelta(days=365)).strftime('%Y-%m-%d'))

        out += """
        <table class="bibcirctable_contents">
          <tr>
            <td align="center">
              <input type=hidden name=barcode value='%s'>
              <input type=hidden name=borrower_id value='%s'>
              <input type=hidden name=recid value='%s'>
              <input type=button value="%s" onClick="history.go(-1)" class="formbutton">
              <input type="submit" name="submit_button" value="%s" class="formbutton">
            </td>
          </tr>
        </table>
        <br />
        <br />
        </form>
        </div>

        """ % (barcode, borrower_id, recid, _("Back"), _('Confirm'))

        return out

    def tmpl_create_new_request_step4(self, ln=CFG_SITE_LANG):
        """
        Last step of the request procedure.

        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += load_menu(ln)


        out += """
        <div class="bibcircbottom">
        <br />
        <br />
        <table class="bibcirctable">
        <tr>
        <td class="bibcirccontent" width="30">%s</td>
        </tr>
        </table>
        <br />
        <br />
        <table class="bibcirctable">
        <td>
            <input type=button
                onClick="location.href='%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s'"
                value='%s' class='formbutton'>
        </td>
        </table>
        <br />
        <br />
        </div>

        """ % (_("A new request has been registered with success."),
               CFG_SITE_URL, ln, _("Back to home"))

        return out


    def tmpl_place_new_request_step1(self, result, key, string, barcode,
                                     recid, infos, ln=CFG_SITE_LANG):
        """
        @param result: borrower's information
        @type result: list

        @param key: field (name, email, etc...)
        @param key: string

        @param string: pattern
        @type string: string

        @param barcode: identify the item. Primary key of crcITEM.
        @type barcode: string

        @param recid: identify the record. Primary key of bibrec
        @type recid: int

        @param infos: information
        @type infos: list

        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        (book_title, book_year, book_author,
         book_isbn, book_editor) = book_information_from_MARC(recid)

        if book_isbn:
            book_cover = get_book_cover(book_isbn)
        else:
            book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)

        out = self.tmpl_infobox(infos, ln)

        out += load_menu(ln)

        out += """
        <style type="text/css"> @import url("/css/tablesorter.css"); </style>
        <div class="bibcircbottom">
        <br />
        <br />
                <table class="bibcirctable">
                  <tr>
                    <td width="500" valign='top'>
                        <table class="bibcirctable">
                            <tr>
                                <td class="bibcirctableheader" width="10">%s</td>
                            </tr>
                        </table>

                      <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td>
                        </tr>
                      </table>
                     </td>
                     <td width="200" align='center' valign='top'>
                       <table>
                         <tr>
                           <td>
                             <img style='border: 1px solid #cfcfcf' src="%s" alt="Book Cover"/>
                           </td>
                         </tr>
                       </table>
                     </td>
                     """ % (_("Item details"),
                            _("Name"), book_title,
                            _("Author(s)"), book_author,
                            _("Year"), book_year,
                            _("Publisher"), book_editor,
                            _("ISBN"), book_isbn,
                            _("Barcode"), barcode,
                            str(book_cover))

        out += """
        <td valign='top' align='center'>
        <form name="step1_form1"
              action="%s/admin2/bibcirculation/place_new_request_step1"
              method="get" >
        <input type=hidden name=barcode value='%s'>
        <input type=hidden name=recid value='%s'>
        <table>

            """ % (CFG_SITE_URL, barcode, recid)

        if CFG_CERN_SITE == 1:

            out += """
                 <tr>
                   <td class="bibcirctableheader" align="center">%s
                   """ % (_("Search user by"))

            if key == 'email':
                out += """
                   <input type="radio" name="key" value="ccid">%s
                   <input type="radio" name="key" value="name">%s
                   <input type="radio" name="key" value="email" checked>%s
                   """ % (_("ccid"), _("name"), _("email"))

            elif key == 'name':
                out += """
                   <input type="radio" name="key" value="ccid">%s
                   <input type="radio" name="key" value="name" checked>%s
                   <input type="radio" name="key" value="email">%s
                   """ % (_("ccid"), _("name"), _("email"))

            else:
                out += """
                   <input type="radio" name="key" value="ccid" checked>%s
                   <input type="radio" name="key" value="name">%s
                   <input type="radio" name="key" value="email">%s
                   """ % (_("ccid"), _("name"), _("email"))

        else:
            out += """
                 <tr>
                   <td class="bibcirctableheader" align="center">%s
                   """ % (_("Search borrower by"))

            if key == 'email':
                out += """
                   <input type="radio" name="key" value="id">%s
                   <input type="radio" name="key" value="name">%s
                   <input type="radio" name="key" value="email" checked>%s
                   """ % (_("ccid"), _("name"), _("email"))

            elif key == 'id':
                out += """
                   <input type="radio" name="key" value="id" checked>%s
                   <input type="radio" name="key" value="name">%s
                   <input type="radio" name="key" value="email">%s
                   """ % (_("ccid"), _("name"), _("email"))

            else:
                out += """
                   <input type="radio" name="key" value="id">%s
                   <input type="radio" name="key" value="name" checked>%s
                   <input type="radio" name="key" value="email">%s
                   """ % (_("ccid"), _("name"), _("email"))

        out += """
                    <br><br>
                    </td>
                    </tr>
                    <tr>
                    <td align="center">
                    <input type="text" size="40" id="string" name="string"
                           value='%s'  style='border: 1px solid #cfcfcf'>
                    </td>
                    </tr>
                    <tr>
                    <td align="center">
                    <br>
                    <input type="submit" value="%s" class="formbutton">
                    </td>
                    </tr>
                </table>
          </form>
        """ % (string or '', _("Search"))

        if result:
            out += """
            <br />
            <form name="step1_form2"
                  action="%s/admin2/bibcirculation/place_new_request_step2"
                  method="get" >
            <input type=hidden name=barcode value='%s'>
            <input type=hidden name=recid value='%s'>
            <table class="bibcirctable">
                <tr width="200">
                    <td align="center">
                        <select name="user_info"
                                size="8"
                                style='border: 1px solid #cfcfcf; width:40%%'>
            """ % (CFG_SITE_URL, barcode, recid)

            for (borrower_id, ccid, name, email,
                 phone, address, mailbox) in result:
                out += """
                       <option value ='%s,%s,%s,%s,%s,%s,%s'>%s
                       """ % (borrower_id, ccid, name, email, phone,
                              address, mailbox, name)

            out += """
                    </select>
                    </td>
                    </tr>
                    </table>
                    <table class="bibcirctable">
                    <tr>
                        <td ALIGN="center">
                        <input type="submit" value='%s' class="formbutton">
                        </td>
                    </tr>
                    </table>
                    </form>
                    """ % (_("Select user"))

        out += """
                  </td>
                </tr>
              </table>
              <br />
              <br />
              <br />
              <br />
              </div>
              """

        return out

    def tmpl_place_new_request_step2(self, barcode, recid, user_info, infos,
                                     ln=CFG_SITE_LANG):
        """
        @param barcode: identify the item. Primary key of crcITEM.
        @type barcode: string

        @param recid: identify the record. Primary key of bibrec
        @type recid: int

        @param user_info: user's information
        @type user_info: tuple

        @param infos: information
        @type infos: list

        @param ln: language of the page
        """

        (book_title, book_year, book_author,
         book_isbn, book_editor) = book_information_from_MARC(recid)

        if book_isbn:
            book_cover = get_book_cover(book_isbn)
        else:
            book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)

        (borrower_id, ccid, name, email, phone, address, mailbox) = user_info

        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += load_menu(ln)

        out += """
            <style type="text/css"> @import url("/css/tablesorter.css"); </style>
            <div class="bibcircbottom">
            <form name="step2_form" action="%s/admin2/bibcirculation/place_new_request_step3"
                  method="post" >
            <input type=hidden name=barcode value='%s'>
            <input type=hidden name=recid value='%s'>
            <input type=hidden name=user_info value="%s,%s,%s,%s,%s,%s,%s">
            <br />

                <table class="bibcirctable">
                    <tr>
                        <td width="500" valign="top">
                            <table class="bibcirctable">
                                <tr class="bibcirctableheader">
                                    <td>%s</td>
                                </tr>
                            </table>
                            <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
                                <tr>
                                   <th width="100">%s</th>
                                   <td>%s</td>
                                </tr>
                                <tr>
                                   <th width="100">%s</th>
                                   <td>%s</td>
                                </tr>
                                <tr>
                                   <th width="100">%s</th>
                                   <td>%s</td>
                                </tr>
                                <tr>
                                   <th width="100">%s</th>
                                   <td>%s</td>
                                </tr>
                                <tr>
                                   <th width="100">%s</th>
                                   <td>%s</td>
                                </tr>
                                <tr>
                                   <th width="100">%s</th>
                                   <td>%s</td>
                                </tr>
                            </table>
                        </td>
                        <td width="200" align='center' valign='top'>
                            <table>
                                <tr>
                                    <td>
                                        <img style='border: 1px solid #cfcfcf' src="%s" alt="Book Cover"/>
                                    </td>
                                </tr>
                            </table>
                        </td>


              <br />
              """ % (CFG_SITE_URL, barcode, recid,
                     borrower_id, ccid, name, email, phone, address, mailbox,
                     _("Item details"),
                     _("Name"), book_title,
                     _("Author(s)"), book_author,
                     _("Year"), book_year,
                     _("Publisher"), book_editor,
                     _("ISBN"), book_isbn,
                     _("Barcode"), barcode,
                     str(book_cover))

        out += """
              <td align='center' valign="top">
              <table class="bibcirctable">
                <tr class="bibcirctableheader">
                    <td>%s</td>
                </tr>
              </table>
              <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
                <tr>
                    <th width="100">%s</th>
                    <td>%s</td>
                </tr>
                <tr>
                    <th width="100">%s</th>
                    <td>%s</td>
                </tr>
                <tr>
                    <th width="100">%s</th>
                    <td>%s</td>
                </tr>
                <tr>
                    <th width="100">%s</th>
                    <td>%s</td>
                 </tr>
                  <tr>
                    <th width="100">%s</th>
                    <td>%s</td>
                 </tr>
                  <tr>
                    <th width="100">%s</th>
                    <td>%s</td>
                 </tr>
                </table>
                </td>
                </table>
                """ % (_("Borrower details"),
                       _("ID"), ccid,
                       _("Name"), name,
                       _("Address"), address,
                       _("Mailbox"), mailbox,
                       _("Email"), email,
                       _("Phone"), phone)

        out += """

                <script type="text/javascript" src="%s/vendors/jquery-ui/jquery-ui.min.js"></script>

                <table class="bibcirctable">
                  <tr class="bibcirctableheader">
                    <td>%s</td>
                  </tr>
                </table>
                <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">
                  <tr>
                    <th width="100">%s</th>
                    <td>

                    <script type="text/javascript">
                    $(function(){
                        $("#date_picker1").datepicker({dateFormat: 'yy-mm-dd', showOn: 'button', buttonImage: "%s/img/calendar.gif", buttonImageOnly: true});
                    });
                    </script>
                    <input type="text" size="12" id="date_picker1" name="period_from" value="%s" style='border: 1px solid #cfcfcf'>

                    </td>
                  </tr>
                  <tr>
                    <th width="100">%s</th>
                    <td>

                    <script type="text/javascript">
                    $(function(){
                        $("#date_picker2").datepicker({dateFormat: 'yy-mm-dd', showOn: 'button', buttonImage: "%s/img/calendar.gif", buttonImageOnly: true});
                    });
                    </script>
                    <input type="text" size="12" id="date_picker2" name="period_to" value="%s" style='border: 1px solid #cfcfcf'>

                    </td>
                  </tr>
                </table>
                <br />
                <br />
                <table class="bibcirctable">
                <tr>
                  <td>
                       <input type=button value="%s"
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit"
                       value="%s" class="formbutton">

                  </td>
                 </tr>
                </table>
                </form>
                <br />
                <br />
                </div>
                """ % (CFG_SITE_URL,
        _("Enter the period of interest"),
        _("From:  "), CFG_SITE_URL, datetime.date.today().strftime('%Y-%m-%d'),
        _("To:  "), CFG_SITE_URL,
    (datetime.date.today() + datetime.timedelta(days=365)).strftime('%Y-%m-%d'),
        _("Back"), _("Continue"))

        return out

    def tmpl_place_new_request_step3(self, ln=CFG_SITE_LANG):
        """
        Last step of the request procedure.
        """

        _ = gettext_set_language(ln)

        out = load_menu(ln)

        out += """
        <div class="bibcircbottom">
        <br />
        <br />
        <div class="bibcircinfoboxsuccess">%s</div>
        <br />
        <br />
        <table class="bibcirctable">
        <td>
            <input type=button
                   onClick="location.href='%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s'"
                   value='%s'
                   class='formbutton'>
        </td>
        </table>
        <br />
        <br />
        </div>

        """ % (_("A new request has been registered with success."),
               CFG_SITE_URL, ln, _("Back to home"))

        return out


    def tmpl_place_new_loan_step1(self, result, key, string, barcode,
                                  recid, infos, ln=CFG_SITE_LANG):
        """
        @param result: borrower's information
        @type result: list

        @param key: field (name, email, etc...)
        @param key: string

        @param string: pattern
        @type string: string

        @param barcode: identify the item. Primary key of crcITEM.
        @type barcode: string

        @param recid: identify the record. Primary key of bibrec
        @type recid: int

        @param infos: information
        @type infos: list

        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        (book_title, book_year, book_author,
         book_isbn, book_editor) = book_information_from_MARC(recid)

        if book_isbn:
            book_cover = get_book_cover(book_isbn)
        else:
            book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)

        out = self.tmpl_infobox(infos, ln)

        out += load_menu(ln)

        out += """
        <style type="text/css"> @import url("/css/tablesorter.css"); </style>
        <div class="bibcircbottom">
        <br />
          <table class="bibcirctable">
                  <tr>
                     <td class="bibcirctableheader" width="10">%s</td>
                  </tr>
                </table>
                <table class="bibcirctable">
                  <tr>
                    <td width="500" valign='top'>
                      <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td>
                        </tr>
                      </table>
                     </td>
                     <td width="200" align='center' valign='top'>
                       <table>
                         <tr>
                           <td>
                             <img style='border: 1px solid #cfcfcf' src="%s" alt="Book Cover"/>
                           </td>
                         </tr>
                       </table>
                     </td>
                     """ % (_("Item details"),
                            _("Name"), book_title,
                            _("Author(s)"), book_author,
                            _("Year"), book_year,
                            _("Publisher"), book_editor,
                            _("ISBN"), book_isbn,
                            _("Barcode"), barcode,
                            str(book_cover))

        out += """
        <td valign='top' align='center'>
        <form name="step1_form1"
              action="%s/admin2/bibcirculation/place_new_loan_step1"
              method="get" >
        <input type=hidden name=barcode value='%s'>
        <input type=hidden name=recid value='%s'>
        <table>

            """ % (CFG_SITE_URL, barcode, recid)

        if CFG_CERN_SITE == 1:

            out += """
                 <tr>
                   <td class="bibcirctableheader" align="center">%s
                   """ % (_("Search user by"))

            if key == 'email':
                out += """
                   <input type="radio" name="key" value="ccid">%s
                   <input type="radio" name="key" value="name">%s
                   <input type="radio" name="key" value="email" checked>%s
                   """ % (_("ccid"), _("name"), _("email"))

            elif key == 'name':
                out += """
                   <input type="radio" name="key" value="ccid">%s
                   <input type="radio" name="key" value="name" checked>%s
                   <input type="radio" name="key" value="email">%s
                   """ % (_("ccid"), _("name"), _("email"))

            else:
                out += """
                   <input type="radio" name="key" value="ccid" checked>%s
                   <input type="radio" name="key" value="name">%s
                   <input type="radio" name="key" value="email">%s
                   """ % (_("ccid"), _("name"), _("email"))

        else:
            out += """
                 <tr>
                   <td class="bibcirctableheader" align="center">%s
                   """ % (_("Search user by"))

            if key == 'email':
                out += """
                   <input type="radio" name="key" value="id">%s
                   <input type="radio" name="key" value="name">%s
                   <input type="radio" name="key" value="email" checked>%s
                   """ % (_("id"), _("name"), _("email"))

            elif key == 'id':
                out += """
                   <input type="radio" name="key" value="id" checked>%s
                   <input type="radio" name="key" value="name">%s
                   <input type="radio" name="key" value="email">%s
                   """ % (_("id"), _("name"), _("email"))

            else:
                out += """
                   <input type="radio" name="key" value="id">%s
                   <input type="radio" name="key" value="name" checked>%s
                   <input type="radio" name="key" value="email">%s
                   """ % (_("id"), _("name"), _("email"))

        out += """
                    <br><br>
                    </td>
                    </tr>
                    <tr>
                    <td align="center">
                    <input type="text" size="40" id="string" name="string"
                           value='%s'  style='border: 1px solid #cfcfcf'>
                    </td>
                    </tr>
                    <tr>
                    <td align="center">
                    <br>
                    <input type="submit" value="%s" class="formbutton">
                    </td>
                    </tr>
                </table>
          </form>
        """ % (string or '', _("Search"))

        if result:
            out += """
                <script type="text/javascript">
                    function checkform(form){
                      if (form.user_id.value == ""){
                        alert("%s");
                        return false;
                      }
                      else{
                        return true;
                      }
                    }
                </script>
                """ % (_("Please select one borrower to continue."))

            out += """
            <br />
            <form name="step1_form2" action="%s/admin2/bibcirculation/loan_on_desk_step3"
                  method="get" onsubmit="return checkform(this);">
            <input type=hidden name=barcode value='%s'>

            <table class="bibcirctable">
              <tr width="200">
                <td align="center">
                  <select name="user_id" size="8" style='border: 1px solid #cfcfcf;'>
            """ % (CFG_SITE_URL, barcode)

            for brw in result:
                borrower_id = brw[0]
                name = brw[2]
                out += """
                       <option value ="%s">%s
                       """ % (borrower_id, name)

            out += """
                    </select>
                    </td>
                    </tr>
                    </table>
                    <table class="bibcirctable">
                    <tr>
                        <td ALIGN="center">
                        <input type="submit" value='%s' class="formbutton">
                        </td>
                    </tr>
                    </table>
                    </form>
                    """ % (_("Select user"))

        out += """
                  </td>
                </tr>
              </table>
              <br />
              <br />
              <br />
              <br />
              </div>
              """

        return out

    def tmpl_place_new_loan_step2(self, barcode, recid, user_info,
                                  ln=CFG_SITE_LANG):
        """
        @param barcode: identify the item. Primary key of crcITEM.
        @type barcode: string

        @param recid: identify the record. Primary key of bibrec.
        @type recid: int

        @param user_info: user's information
        @type user_info: tuple

        @param ln: language of the page
        """

        (book_title, book_year, book_author, book_isbn,
         book_editor) = book_information_from_MARC(recid)

        if book_isbn:
            book_cover = get_book_cover(book_isbn)
        else:
            book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)

        (_borrower_id, ccid, name, email, phone,
         address, mailbox) = user_info.split(',')

        _ = gettext_set_language(ln)

        out = """
        """
        out += load_menu(ln)

        out += """
            <style type="text/css"> @import url("/css/tablesorter.css"); </style>
            <div class="bibcircbottom">
            <form name="step2_form" action="%s/admin2/bibcirculation/place_new_loan_step3"
                  method="post" >
            <input type=hidden name=barcode value='%s'>
            <input type=hidden name=recid value='%s'>
            <input type=hidden name=email value='%s'>
              <br />
              <table class="bibcirctable">
                  <tr>
                     <td class="bibcirctableheader" width="10">%s</td>
                  </tr>
                </table>

                <table class="bibcirctable">
                 <tr valign='top'>
                  <td width="400">
                    <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
                     <tr>
                       <th width="100">%s</th>
                       <td>%s</td>
                     </tr>
                     <tr>
                       <th width="100">%s</th>
                       <td>%s</td>
                     </tr>
                     <tr>
                       <th width="100">%s</th>
                       <td>%s</td>
                     </tr>
                     <tr>
                       <th width="100">%s</th>
                       <td>%s</td>
                     </tr>
                     <tr>
                       <th width="100">%s</th>
                       <td>%s</td>
                     </tr>
                     <tr>
                       <th width="100">%s</th>
                       <td>%s</td>
                     </tr>
                   </table>
                 </td>
                 <td>
                   <img style='border: 1px solid #cfcfcf' src="%s" alt="Book Cover"/>
                 </td>
               </tr>
              </table>
              <br />
              """ % (CFG_SITE_URL, barcode,
                     recid, email,
                     _("Item details"),
                     _("Name"), book_title,
                     _("Author(s)"), book_author,
                     _("Year"), book_year,
                     _("Publisher"), book_editor,
                     _("ISBN"), book_isbn,
                     _("Barcode"), barcode,
                     str(book_cover))

        out += """
              <br />
              <table class="bibcirctable">
                <tr>
                  <td class="bibcirctableheader" width="10">%s</td>
                </tr>
              </table>
              <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">
                <tr>
                    <th width="70">%s</th>
                    <td>%s</td>
                </tr>
                <tr>
                    <th width="70">%s</th>
                    <td>%s</td>
                </tr>
                <tr>
                    <th width="70">%s</th>
                    <td>%s</td>
                </tr>
                <tr>
                    <th width="70">%s</th>
                    <td>%s</td>
                 </tr>
                 <tr>
                    <th width="70">%s</th>
                    <td>%s</td>
                 </tr>
                 <tr>
                    <th width="70">%s</th>
                    <td>%s</td>
                 </tr>
                </table>
                <br />
                """ % (_("Borrower details"),
                       _("ID"), ccid,
                       _("Name"), name,
                       _("Address"), address,
                       _("Mailbox"), mailbox,
                       _("Email"), email,
                       _("Phone"), phone)

        out += """

                <script type="text/javascript" src="%s/vendors/jquery-ui/jquery-ui.min.js"></script>

                <table class="bibcirctable">
                  <tr class="bibcirctableheader">
                    <td>%s</td>
                  </tr>
                </table>
                <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">
                  <tr>
                    <th width="70">%s</th>
                    <td>%s</td>
                  </tr>
                  <tr>
                    <th width="70">%s</th>
                    <td align='left'>
                    <script type="text/javascript">
                    $(function(){
                        $("#date_picker1").datepicker({dateFormat: 'yy-mm-dd', showOn: 'button', buttonImage: "%s/img/calendar.gif", buttonImageOnly: true});
                    });
                </script>
                <input type="text" size="12" id="date_picker1"
                       name="due_date" value="%s" style='border: 1px solid #cfcfcf'>
                    </td>
                  </tr>
                </table>
                <br />
                <br />
                <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">
                  <tr>
                    <th>%s</th>
                  </tr>
                  <tr>
                    <td>
                        <textarea name='notes' rows="5" cols="57"
                                  style='border: 1px solid #cfcfcf'></textarea>
                    </td>
                  </tr>
                  <tr>
                    <td>%s</td>
                  </tr>
                </table>
                <br />
                <br />
                <table class="bibcirctable">
                <tr>
                  <td>
                       <input type=button value="%s"
                              onClick="history.go(-1)"
                              class="formbutton">
                       <input type="submit"
                              value="%s"
                              class="formbutton">
                  </td>
                 </tr>
                </table>
                </form>
                <br />
                <br />
                </div>
    """ % (CFG_SITE_URL,
        _("Loan information"),
        _("Loan date"), datetime.date.today().strftime('%Y-%m-%d'),
        _("Due date"), CFG_SITE_URL, renew_loan_for_X_days(barcode),
        _("Write notes"),
        _("This note will be associated to this new loan, not to the borrower."),
        _("Back"), _("Continue"))

        return out


    def tmpl_change_due_date_step1(self, loan_details, loan_id, borrower_id,
                                   ln=CFG_SITE_LANG):
        """
        Return the form where the due date can be changed.

        @param loan_details: the information related to the loan.
        @type loan_details: tuple

        @param loan_id: identify the loan. Primary key of crcLOAN.
        @type loan_id: int

        @param borrower_id: identify the borrower. Primary key of crcBORROWER.
        @type borrower_id: int

        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += load_menu(ln)

        (recid, barcode, loaned_on, due_date, loan_status,
                                    loan_period, _item_status) = loan_details
        number_of_requests = db.get_number_requests_per_copy(barcode)
        if number_of_requests > 0:
            request_status = 'Yes'
        else:
            request_status = 'No'

        out += """
            <div class="bibcircbottom">
            <form name="borrower_notes" action="%s/admin2/bibcirculation/change_due_date_step2" method="get" >
            <br />
            <br />
            <table class="bibcirctable">
             <tr>
               <td class="bibcirctableheader" width="100">%s</td>
             </tr>
           </table>
           <table class="bibcirctable">
            <tr>
             <td width="80">%s</td> <td class="bibcirccontent">%s</td>
            </tr>
            <tr>
            <td width="80">%s</td> <td class="bibcirccontent">%s</td>
            </tr>
            <tr>
            <td width="80">%s</td> <td class="bibcirccontent">%s</td>
            </tr>
            <tr>
            <td width="80">%s</td> <td class="bibcirccontent">%s</td>
            </tr>
            <tr>
            <td width="80">%s</td> <td class="bibcirccontent">%s</td>
            </tr>
            <tr>
            <td width="80">%s</td> <td class="bibcirccontent">%s</td>
            </tr>
            <tr>
            <td width="80">%s</td> <td class="bibcirccontent">%s</td>
            </tr>
            </table>
            <br />
             """ % (CFG_SITE_URL, _("Loan information"),
                    _("Title"), book_title_from_MARC(recid),
                    _("Barcode"), barcode,
                    _("Loan date"), loaned_on,
                    _("Due date"), due_date,
                    _("Loan status"), loan_status,
                    _("Loan period"), loan_period,
                    _("Requested ?"), request_status)

        out += """

            <script type="text/javascript" src="%s/vendors/jquery-ui/jquery-ui.min.js"></script>

            <table class="bibcirctable">
              <tr align="left">
                <td width="230" class="bibcirctableheader">%s
                    <script type="text/javascript">
                        $(function(){
                            $("#date_picker1").datepicker({dateFormat: 'yy-mm-dd', showOn: 'button', buttonImage: "%s/img/calendar.gif", buttonImageOnly: true});
                        });
                    </script>
                    <input type="text" size="12" id="date_picker1" name="new_due_date" value="%s" style='border: 1px solid #cfcfcf'>
                </td>
              </tr>
            </table>
            <br />
            """ % (CFG_SITE_URL, _("New due date: "), CFG_SITE_URL, due_date)

        out += """
        <table class="bibcirctable">
             <tr>
                  <td>
                       <input type=hidden name=loan_id value="%s">
                       <input type=hidden name=borrower_id value="%s">

                       <input type=button value="%s"
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit"
                        value="%s" class="formbutton">


                  </td>
             </tr>
        </table>
        <br />
        <br />
        </form>
        </div>
        """ % (loan_id, borrower_id,
               _("Back"), _("Submit new due date"))

        return out

    def tmpl_change_due_date_step2(self, new_due_date, borrower_id,
                                   ln=CFG_SITE_LANG):
        """
        Return a page with the new due date.

        @param due_date: new due date
        @type due_date: string

        @param borrower_id: identify the borrower. Primary key of crcBORROWER.
        @type borrower_id: int

        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += load_menu(ln)

        out += """
            <div class="bibcircbottom">
              <br />
              <br />
              <table class="bibcirctable">
                <tr>
                    <td class="bibcirccontent">%s</td>
                </tr>
                </table>
                <br />
                <table class="bibcirctable">
                <tr>
                  <td>
                    <input type=button
    onClick="location.href='%s/admin2/bibcirculation/get_borrower_loans_details?ln=%s&borrower_id=%s'"
                    value='%s' class='formbutton'>
                  </td>
                 </tr>
                </table>
                <br />
                <br />
                </div>
""" % (_("The due date has been updated. New due date: %(x_name)s", x_name=(new_due_date)),
    CFG_SITE_URL, ln, borrower_id, cgi.escape(_("Back to borrower's loans"), True))


        return out

    def tmpl_send_notification(self, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        out = """
              """
        out += load_menu(ln)

        out += """
        <div class="bibcircbottom">
        <br />
        <br />
            <table class="bibcirctable">
                <td class="bibcirccontent" width="30">%s</td>
            </table>
            <br /> <br />
            <table class="bibcirctable">
            <td>
             <input
                type=button
                onClick="location.href='%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s'"
                value='%s'
                class='formbutton'>
            </td>
            </table>
        <br />
        <br />
        </div>
        """ % (_("Notification has been sent!"),
               CFG_SITE_URL, ln, _("Back to home"))

        return out

    def tmpl_get_loans_notes(self, loans_notes, loan_id,
                             referer, back="", ln=CFG_SITE_LANG):

        _ = gettext_set_language(ln)

        if back == "":
            back = referer

        if not loans_notes:
            loans_notes = {}
        else:
            if looks_like_dictionary(loans_notes):
                loans_notes = eval(loans_notes)
            else:
                loans_notes = {}

        out = """ """

        out += load_menu(ln)

        out += """
            <div class="bibcircbottom">
            <form name="loans_notes"
                  action="%s/admin2/bibcirculation/get_loans_notes"
                  method="get" >
            <input type="hidden" name="loan_id" value="%s">
            <br />
            <br />
            <table class="bibcirctable">
              <tr>
                <td class="bibcirctableheader">%s</td>
              </tr>
            </table>
            <table class="bibcirctable">
              <tr>
                <td>
                  <table class="bibcircnotes">
            """ % (CFG_SITE_URL, loan_id,
                   _("Notes about loan"))

        key_array = loans_notes.keys()
        key_array.sort()

        for key in key_array:
            delete_note = create_html_link(CFG_SITE_URL +
                            '/admin2/bibcirculation/get_loans_notes',
                            {'delete_key': key, 'loan_id': loan_id, 'ln': ln,
                            'back': cgi.escape(back, True)}, (_("[delete]")))

            out += """<tr class="bibcirccontent">
                        <td class="bibcircnotes" width="160" valign="top"
                            align="center"><b>%s</b></td>
                        <td width="400"><i>%s</i></td>
                        <td width="65" align="center">%s</td>
                      </tr>
                      """ % (key, loans_notes[key], delete_note)

        out += """
                  </table>
                </td>
              </tr>
            </table>
            <br />
            <table class="bibcirctable">
              <tr>
                <td class="bibcirctableheader">%s</td>
              </tr>
            </table>
            <table class="bibcirctable">
              <tr>
                <td class="bibcirccontent">
                  <textarea name="library_notes" rows="5" cols="90"
                            style='border: 1px solid #cfcfcf'></textarea>
                </td>
              </tr>
            </table>
            <br />
            <table class="bibcirctable">
              <tr>
                  <td>
                    <input type=button
                           value="%s"
                           onClick="window.location='%s'"
                           class="formbutton">
                    <input type="submit" value="%s" class="formbutton">
                    <input type="hidden" name="back" value="%s">
                  </td>
             </tr>
             </table>
             <br />
             <br />
             <br />
             </form>
             </div>
        """ % (_("Write new note"),
               _("Back"),
               cgi.escape(back, True),
               _("Confirm"),
               cgi.escape(back, True))

        return out

    def tmpl_all_requests(self, result, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        out = """
        """
        out += load_menu(ln)

        out += """
        <form name="all_requests_form"
              action="%s/admin2/bibcirculation/all_requests"
              method="get" >
            <div class="bibcircbottom">
                <br />
                <table class="bibcirctable">
                    <tr>
                        <td class="bibcirctableheader">%s</td>
                        <td class="bibcirctableheader">%s</td>
                        <td class="bibcirctableheader" align="center">%s</td>
                        <td class="bibcirctableheader" align="center">%s</td>
                        <td class="bibcirctableheader" align="center">%s</td>
                        <td class="bibcirctableheader" align="center">%s</td>
                        <td class="bibcirctableheader" align="center">%s</td>
                    </tr>
        """ % (CFG_SITE_URL,
               _("Borrower"),
               _("Item"),
               _("Status"),
               _("From"),
               _("To"),
               _("Request date"),
               _("Option(s)"))

        for (id_lr, borid, name, recid, status, date_from,
             date_to, request_date) in result:

            borrower_link = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/get_borrower_details',
                                {'borrower_id': borid, 'ln': ln},(name))

            title_link = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/get_item_details',
                                {'recid': recid, 'ln': ln},
                                (book_title_from_MARC(recid)))

            out += """
            <tr onMouseOver="this.className='highlight'" onmouseout="this.className='normal'">
                 <td class="bibcirccontent">%s</td>
                 <td class="bibcirccontent">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">
                   <input type=button
                    onClick="location.href='%s/admin2/bibcirculation/all_requests?ln=%s&request_id=%s'"
                    value='%s' class="formbutton">
                 </td>
            </tr>
            """ % (borrower_link,
                   title_link,
                   status,
                   date_from,
                   date_to,
                   request_date,
                   CFG_SITE_URL, ln,
                   id_lr,
                   _("Cancel hold request"))

        out += """
        </table>
        <br />
        <table class="bibcirctable">
             <tr>
                  <td>
                     <input type=button value="%s" onClick="history.go(-1)" class="formbutton">
                  </td>
             </tr>
        </table>
        <br />
        <br />
        </div>
        </form>
        """ % (_("Back"))

        return out

    def tmpl_all_loans(self, result, infos, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += load_menu(ln)

        out += """
            <style type="text/css"> @import url("/{0}/themes/blue/style.css"); </style>
            <style type="text/css"> @import url("/{0}/addons/pager/jquery.tablesorter.pager.css"); </style>
            <script src="/{1}" type="text/javascript"></script>
            <script src="/{0}/addons/pager/jquery.tablesorter.pager.js" type="text/javascript"></script>
            <script type="text/javascript">
            $(document).ready(function(){
                $("#table_all_loans")
                    .tablesorter({sortList: [[3,1], [0,0]],widthFixed: true, widgets: ['zebra']})
                    .bind("sortStart",function(){$("#overlay").show();})
                    .bind("sortEnd",function(){$("#overlay").hide()})
                    .tablesorterPager({container: $("#pager"), positionFixed: false});
            });
            </script>

            <br />

            <div class="bibcircbottom">
            """.format(JQUERY_TABLESORTER_BASE, JQUERY_TABLESORTER)

        if len(result) == 0:
            out += """
              <br />
              <table class="bibcirctable">
                <tr>
                    <td class="bibcirccontent">%s</td>
                </tr>
                </table>
                <br />
                <table class="bibcirctable">
                <tr>
                  <td>
                    <input type=button value='%s' onClick="history.go(-1)" class="formbutton">
                  </td>
                </tr>
                </table>
                <br />
                <br />
                </div>
                """ % (_("No result for your search."),
                       _("Back"))

        else:
            out += """
            <form name="borrower_form" action="%s/admin2/bibcirculation/all_loans" method="get" >
            <br />
            <table id="table_all_loans" class="tablesorter"
                   border="0" cellpadding="0" cellspacing="1">
               <thead>
                    <tr>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th></th>
                    </tr>
               </thead>
              <tbody>
                       """% (CFG_SITE_URL,
                          _("Borrower"),
                          _("Item"),
                          _("Barcode"),
                          _("Loaned on"),
                          _("Due date"),
                          _("Renewals"),
                          _("Overdue letters"),
                          _("Loan Notes"))

            for (borrower_id, borrower_name, recid, barcode,
                 loaned_on, due_date, nb_renewal, nb_overdue,
                 date_overdue, notes, loan_id) in result:

                borrower_link = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/get_borrower_details',
                                {'borrower_id': borrower_id, 'ln': ln},
                                (borrower_name))

                see_notes_link = create_html_link(CFG_SITE_URL +
                               '/admin2/bibcirculation/get_loans_notes',
                               {'loan_id': loan_id, 'ln': ln}, (_("see notes")))

                no_notes_link = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/get_loans_notes',
                                {'loan_id': loan_id, 'ln': ln}, (_("no notes")))


                if notes == "" or str(notes) == '{}':
                    check_notes = no_notes_link
                else:
                    check_notes = see_notes_link

                title_link = create_html_link(CFG_SITE_URL +
                                    '/admin2/bibcirculation/get_item_details',
                                    {'recid': recid, 'ln': ln},
                                    (book_title_from_MARC(recid)))

                out += """
                    <tr>
                        <td>%s</td>
                        <td>%s</td>
                        <td>%s</td>
                        <td>%s</td>
                        <td>%s</td>
                        <td>%s</td>
                        <td>%s - %s</td>
                        <td>%s</td>
                        <td align="center">
                        <input type=button onClick="location.href='%s/admin2/bibcirculation/claim_book_return?borrower_id=%s&recid=%s&loan_id=%s&template=claim_return'" onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
                             value='%s' class='bibcircbutton'></td>
                    </tr>

                    """ % (borrower_link, title_link, barcode,
                           loaned_on, due_date,
                           nb_renewal, nb_overdue, date_overdue,
                           check_notes, CFG_SITE_URL,
                           borrower_id, recid, loan_id, _("Send recall"))

            out += """
                    </tbody>
                    </table>
                    </form>

                    <div id="pager" class="pager">
                        <form>
                            <br />
                            <img src="/img/sb.gif" class="first" />
                            <img src="/img/sp.gif" class="prev" />
                            <input type="text" class="pagedisplay" />
                            <img src="/img/sn.gif" class="next" />
                            <img src="/img/se.gif" class="last" />
                            <select class="pagesize">
                                <option value="10" selected="selected">10</option>
                                <option value="20">20</option>
                                <option value="30">30</option>
                                <option value="40">40</option>
                            </select>
                        </form>
                    </div>
                    """
            out += """
                    <div class="back" style="position: relative; top: 5px;">
                        <br />
                        <table class="bibcirctable">
                            <tr>
                                <td>
                                    <input type=button value='%s'
                                           onClick="history.go(-1)"
                                           class="formbutton">
                                </td>
                            </tr>
                        </table>
                    <br />
                    <br />
                    </div>
                    </div>
                    """ % (_("Back"))

        return out

    def tmpl_all_expired_loans(self, result, infos, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += load_menu(ln)

        out += """
            <style type="text/css"> @import url("/{0}/themes/blue/style.css"); </style>
            <style type="text/css"> @import url("/{0}/addons/pager/jquery.tablesorter.pager.css"); </style>
            <script src="/{1}" type="text/javascript"></script>
            <script src="/{0}/addons/pager/jquery.tablesorter.pager.js" type="text/javascript"></script>
            <script type="text/javascript">
            $(document).ready(function(){
                $("#table_all_loans")
                    .tablesorter({sortList: [[3,1], [0,0]],widthFixed: true, widgets: ['zebra']})
                    .bind("sortStart",function(){$("#overlay").show();})
                    .bind("sortEnd",function(){$("#overlay").hide()})
                    .tablesorterPager({container: $("#pager"), positionFixed: false});
            });
            </script>

            <br />

            <div class="bibcircbottom">
            """.format(JQUERY_TABLESORTER_BAES, JQUERY_TABLESORTER)

        if len(result) == 0:
            out += """
              <br />
              <table class="bibcirctable">
                <tr>
                    <td class="bibcirccontent">%s</td>
                </tr>
                </table>
                <br />
                <table class="bibcirctable">
                <tr>
                  <td>
                    <input type=button value='%s'
                           onClick="history.go(-1)" class="formbutton">
                  </td>
                </tr>
                </table>
                <br />
                <br />
                </div>
                """ % (_("No result for your search."),
                       _("Back"))

        else:
            out += """
            <form name="borrower_form"
                  action="%s/admin2/bibcirculation/all_loans"
                  method="get" >
            <br />
            <table id="table_all_loans" class="tablesorter"
                    border="0" cellpadding="0" cellspacing="1">
               <thead>
                    <tr>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th></th>
                    </tr>
               </thead>
              <tbody>
                       """% (CFG_SITE_URL,
                          _("Borrower"),
                          _("Item"),
                          _("Barcode"),
                          _("Loaned on"),
                          _("Due date"),
                          _("Renewals"),
                          _("Overdue letters"),
                          _("Loan Notes"))

            for (borrower_id, borrower_name, recid, barcode,
                 loaned_on, due_date, nb_renewal, nb_overdue,
                 date_overdue, notes, loan_id) in result:

                borrower_link = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/get_borrower_details',
                                {'borrower_id': borrower_id, 'ln': ln},
                                (borrower_name))

                see_notes_link = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/get_loans_notes',
                                {'loan_id': loan_id, 'ln': ln},
                                (_("see notes")))

                no_notes_link = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/get_loans_notes',
                                {'loan_id': loan_id, 'ln': ln},
                                 (_("no notes")))


                if notes == "" or str(notes) == '{}':
                    check_notes = no_notes_link
                else:
                    check_notes = see_notes_link

                title_link = create_html_link(CFG_SITE_URL +
                                    '/admin2/bibcirculation/get_item_details',
                                    {'recid': recid, 'ln': ln},
                                    (book_title_from_MARC(recid)))

                out += """
                    <tr>
                        <td>%s</td>
                        <td>%s</td>
                        <td>%s</td>
                        <td>%s</td>
                        <td>%s</td>
                        <td>%s</td>
                        <td>%s - %s</td>
                        <td>%s</td>
                        <td align="center">
                        <input type=button onClick="location.href='%s/admin2/bibcirculation/claim_book_return?borrower_id=%s&recid=%s&loan_id=%s&template=claim_return'" onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
                             value='%s' class='bibcircbutton'></td>
                    </tr>

                    """ % (borrower_link, title_link, barcode,
                           loaned_on, due_date,
                           nb_renewal, nb_overdue, date_overdue,
                           check_notes, CFG_SITE_URL,
                           borrower_id, recid, loan_id, _("Send recall"))


            out += """
                    </tbody>
                    </table>
                    </form>

                    <div id="pager" class="pager">
                        <form>
                            <br />
                            <img src="/img/sb.gif" class="first" />
                            <img src="/img/sp.gif" class="prev" />
                            <input type="text" class="pagedisplay" />
                            <img src="/img/sn.gif" class="next" />
                            <img src="/img/se.gif" class="last" />
                            <select class="pagesize">
                                <option value="10" selected="selected">10</option>
                                <option value="20">20</option>
                                <option value="30">30</option>
                                <option value="40">40</option>
                            </select>
                        </form>
                    </div>
                    """
            out += """
                    <div class="back" style="position: relative; top: 5px;">
                        <br />
                        <table class="bibcirctable">
                            <tr>
                                <td>
                                    <input type=button value='%s'
                                           onClick="history.go(-1)" class="formbutton">
                                </td>
                            </tr>
                        </table>
                    <br />
                    <br />
                    </form>
                    </div>
                    </div>
                    """ % (_("Back"))

        return out

    def tmpl_get_expired_loans_with_waiting_requests(self, result, ln=CFG_SITE_LANG):
        """
        @param result: loans' information
        @param result: list
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += load_menu(ln)

        if len(result) == 0:
            out += """
            <div class="bibcircbottom">
            <br /> <br />            <br /> <br />
            <table class="bibcirctable_contents">
                 <td class="bibcirccontent" align="center">%s</td>
            </table>
            <br /> <br />            <br />
            <table class="bibcirctable_contents">
            <td align="center">
            <input type=button
                   onClick="location.href='%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s'"
                   value='%s'
                   class='formbutton'>
            </td>
            </table>
            <br />
            </div>
            """ % (_("No more requests are pending or waiting."),
                   CFG_SITE_URL, ln,
                   _("Back to home"))

        else:
            out += """
            <style type="text/css"> @import url("/%s/themes/blue/style.css"); </style>
            <style type="text/css"> @import url("/%s/addons/pager/jquery.tablesorter.pager.css"); </style>
            <script src="/%s" type="text/javascript"></script>
            <script src="/%s/addons/pager/jquery.tablesorter.pager.js" type="text/javascript"></script>
            <script type="text/javascript">

            $(document).ready(function(){
                $("#table_requests")
                    .tablesorter({sortList: [[4,0], [0,0]],widthFixed: true, widgets: ['zebra']})
                    .bind("sortStart",function(){$("#overlay").show();})
                    .bind("sortEnd",function(){$("#overlay").hide()})
                    .tablesorterPager({container: $("#pager"), positionFixed: false});
            });
            </script>

            <div class="bibcircbottom">
            <br />
            <br />
            <table id="table_requests" class="tablesorter" border="0" cellpadding="0" cellspacing="1">
            <thead>
              <tr>
                <th>%s</th>
                <th>%s</th>
                <th>%s</th>
                <th>%s</th>
                <th>%s</th>
                <th>%s</th>
                <th>%s</th>
                <th>%s</th>
              </tr>
            </thead>
            <tbody>
         """% (JQUERY_TABLESORTER_BASE,
               JQUERY_TABLESORTER_BASE,
               JQUERY_TABLESORTER,
               JQUERY_TABLESORTER_BASE,
               _("Name"),
               _("Item"),
               _('Library'),
               _("Location"),
               _("From"),
               _("To"),
               _("Request date"),
               _("Actions"))

            for (request_id, recid, borrower_id, library_id, location,
                 date_from, date_to, request_date) in result:

                borrower_name = db.get_borrower_name(borrower_id)
                library_name = db.get_library_name(library_id)


                title_link = create_html_link(CFG_SITE_URL +
                                    '/admin2/bibcirculation/get_item_details',
                                    {'recid': recid, 'ln': ln},
                                    (book_title_from_MARC(recid)))

                if borrower_name:
                    borrower_link = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/get_borrower_details',
                                {'borrower_id': borrower_id, 'ln': ln},
                                (borrower_name))
                else:
                    borrower_link = str(borrower_id)


                out += """
                <script type="text/javascript">
                function confirmation(id){
                  var answer = confirm("Delete this request?")
                  if (answer){
                    window.location = "%s/admin2/bibcirculation/get_expired_loans_with_waiting_requests?request_id="+id;
                  }
                  else{
                    alert("Request not deleted.")
                  }
                }
                </script>
                <tr>
                  <td width='150'>%s</td>
                  <td width='250'>%s</td>
                  <td>%s</td>
                  <td>%s</td>
                  <td>%s</td>
                  <td>%s</td>
                  <td>%s</td>
                  <td algin='center'>
                    <input type="button" value='%s' style="background: url(/img/dialog-cancel.png)
                        no-repeat #8DBDD8; width: 75px; text-align: right;"
                        onClick="confirmation(%s)"
                        onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
                        class="bibcircbutton">
                    <input type=button style="background: url(/img/dialog-yes.png) no-repeat #8DBDD8; width: 150px; text-align: right;"
                        onClick="location.href='%s/admin2/bibcirculation/create_loan?request_id=%s&recid=%s&borrower_id=%s&ln=%s'"
                        onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
                        value='%s' class="bibcircbutton">
                  </td>
                </tr>
                """ % (CFG_SITE_URL,
                       borrower_link,
                       title_link,
                       library_name,
                       location,
                       date_from,
                       date_to,
                       request_date,
                       _("Delete"),
                        request_id,
                       CFG_SITE_URL,
                       request_id,
                       recid,
                       borrower_id,
                       ln,
                       _("Create Loan"))

            out += """
                  </tbody>
                </table>
                 <div id="pager" class="pager">
                        <form>
                            <br />
                            <img src="/img/sb.gif" class="first" />
                            <img src="/img/sp.gif" class="prev" />
                            <input type="text" class="pagedisplay" />
                            <img src="/img/sn.gif" class="next" />
                            <img src="/img/se.gif" class="last" />
                            <select class="pagesize">
                                <option value="10" selected="selected">10</option>
                                <option value="20">20</option>
                                <option value="30">30</option>
                                <option value="40">40</option>
                            </select>
                        </form>
                    </div>

                  <br />
                  <table class="bibcirctable">
                    <tr>
                      <td>
                        <input type=button style="background: url(/img/document-print.png) no-repeat #8DBDD8; width: 135px; text-align: right;"
                        onClick="location.href='%s/admin2/bibcirculation/get_pending_requests?print_data=true&ln=%s'"
                        onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
                        value='%s' class="bibcircbutton">
                      </td>
                    </tr>
                  </table>
                  <br />
                  </div>
                  """ % (CFG_SITE_URL, ln,
                         _("Printable format"))


        return out



    ###
    ### Items and their copies' related templates.
    ###



    def tmpl_get_item_details(self, recid, copies, requests, loans, purchases, req_hist_overview,
                              loans_hist_overview, purchases_hist_overview, infos, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        record_is_periodical = is_periodical(recid)

        out = self.tmpl_infobox(infos, ln)

        out += load_menu(ln)

        (book_title, book_year, book_author,
                     book_isbn, book_editor) = book_information_from_MARC(recid)

        if book_isbn:
            try:
                book_cover = get_book_cover(book_isbn)
            except KeyError:
                book_cover = """%s/img/book_cover_placeholder.gif
                            """ % (CFG_SITE_URL)
        else:
            book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)

        link_to_detailed_record = "<a href='%s/%s/%s' target='_blank'>%s</a>" % (CFG_SITE_URL, CFG_SITE_RECORD, recid, book_title)

        out += """
           <div class="bibcircbottom">
                <br />
                <table class="bibcirctable">
                  <tr>
                    <td class="bibcirctableheader">%s</td>
                  </tr>
                 <tr valign='top'>
                    <td width="400">
                    <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
                     <tr>
                        <th width="100">%s</th>
                        <td>%s</td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>%s</td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>%s</td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>%s</td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>%s</td>
                     </tr>
                     </table>
                      <input type=button onClick="window.open('%s/%s/%s/edit')"
                      value='%s' class="formbutton">
                     </td>
                     <td>
                     <img style='border: 1px solid #cfcfcf' src="%s" alt="%s"/>
                     </td>""" %  (_("Item details"), _("Name"), link_to_detailed_record,
                   _("Author(s)"), book_author, _("Year"), book_year,
                   _("Publisher"), book_editor, _("ISBN"), book_isbn,
                   CFG_SITE_URL, CFG_SITE_RECORD, recid, _("Edit this record"),
                   str(book_cover), _("Book Cover"))

        # Search another item directly from the item details page.
        out += """<td>
        <form name="search_form"
              action="%s/admin2/bibcirculation/item_search_result"
              method="get" >
        <input type=hidden value="0">
        <input type=hidden value="10">
        <table class="bibcirctable">
          <tr>
            <td class="bibcirctableheader">%s
              <input type="radio" name="f" value="">%s
              <input type="radio" name="f" value="barcode" checked>%s
              <input type="radio" name="f" value="recid">%s
              <br /><br />
            </td>
          </tr>
          """ % (CFG_SITE_URL, _("Search another item by"), _("Item details"),
                 _("barcode"), _("recid"))

        out += """
          <tr>
            <td>
                <input type="text" size="50" name="p" id="p" style='border: 1px solid #cfcfcf'>
                <script language="javascript" type="text/javascript">
                    document.getElementById("p").focus();
                </script>
            </td>
          </tr>
            """

        out += """
            </td>
          </tr>
        </table>
        <br />
        <table class="bibcirctable">
          <tr>
            <td>
              <input type=button   value='%s' class="formbutton" onClick="history.go(-1)">
              <input type="submit" value='%s' class="formbutton">
            </td>
          </tr>
        </table>
        <br />
        <br />
        <form>
        </td>
        """ % (_("Back"), _("Search"))

        out +=  """ </tr>
              </table>
           <br />
           <table class="bibcirctable">
                <tr>
                     <td class="bibcirctableheader">%s</td>
                </tr>
           </table>
           """ % (_("Additional details"))

        out += """
            <style type="text/css">
                @import url("/css/tablesorter.css");
            </style>

            <style type="text/css">
                @import url("/{1}/themes/blue/style.css");
            </style>
            <style type="text/css">
                @import url("/{1}/addons/pager/jquery.tablesorter.pager.css");
            </style>

            <script src="/{0}" type="text/javascript"></script>
            <script src="/{1}/addons/pager/jquery.tablesorter.pager.js"
                    type="text/javascript"></script>
            """.format(JQUERY_TABLESORTER, JQUERY_TABLESORTER_BASE)

        if record_is_periodical:
            out += """
            <script type="text/javascript">
                $(document).ready(function(){
                    $("#table_copies")
                      .tablesorter({sortList: [[7,1],[4,0]],widthFixed: true,widgets: ['zebra']})
                      .bind("sortStart",function(){$("#overlay").show();})
                      .bind("sortEnd",function(){$("#overlay").hide()})
                      .tablesorterPager({container: $("#pager"),
                                         positionFixed: false,
                                         size: 40
                                        });
                });
            </script>
            """
        else:
            out += """
            <script type="text/javascript">
                $(document).ready(function(){
                    $('#table_copies').tablesorter({sortList: [[1,1],[4,0]],
                                                    widthFixed: true,
                                                    widgets: ['zebra']})
                });
            </script>
            """

        out += """
                  <table class="tablesorter" id="table_copies" border="0"
                         cellpadding="0" cellspacing="1">
                  <thead>
                    <tr>
                      <th>%s</th>
                      <th>%s</th>
                      <th>%s</th>
                      <th>%s</th>
                      <th>%s</th>
               """ % (_("Barcode"),
                      _("Status"),
                      _(CFG_BIBCIRCULATION_ILL_STATUS_REQUESTED), #_("Requested"),
                      _("Due date"),
                      _("Library"))

        if not record_is_periodical:
            out += """
                      <th>%s</th>
                   """ % (_("Location"))

        out += """
                      <th>%s</th>
                      <th>%s</th>
                """ % (_("Loan period"),
                       _("No of loans"))

        if not record_is_periodical:
            out += """
                      <th>%s</th>
                   """ % (_("Collection"))

        out += """
                      <th>%s</th>
                      <th>%s</th>
                    </tr>
                  </thead>
                  <tboby>
                    """ % (_("Description"),
                           _("Actions"))

        for (barcode, loan_period, library_name, library_id,
             location, nb_requests, status, collection,
             description, due_date) in copies:

            number_of_requests = db.get_number_requests_per_copy(barcode)
            if number_of_requests > 0:
                requested = 'Yes'
            else:
                requested = 'No'

            if status in ('on order', 'claimed'):
                expected_arrival_date = db.get_expected_arrival_date(barcode)
                if expected_arrival_date != '':
                    status = status + ' - ' + expected_arrival_date

            library_link = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/get_library_details',
                                {'library_id': library_id, 'ln': ln},
                                (library_name))

            out += """
                 <tr>
                     <td>%s</td>
                     <td>%s</td>
                     <td>%s</td>
                     <td>%s</td>
                     <td>%s</td>
                     """ % (barcode, status, requested,
                            due_date or '-', library_link)

            if not record_is_periodical:
                out += """
                     <td>%s</td>
                     """ % (location)

            out += """
                     <td>%s</td>
                     <td>%s</td>
                     """ % (loan_period, nb_requests)

            if not record_is_periodical:
                out += """
                     <td>%s</td>
                     """ % (collection or '-')

            out += """
                     <td>%s</td>
                     """ % (description or '-')

            if status == CFG_BIBCIRCULATION_ITEM_STATUS_ON_LOAN:
                out += """
                  <td align="center">
                    <SELECT style='border: 1px solid #cfcfcf'
                            ONCHANGE="location = this.options[this.selectedIndex].value;">
                      <OPTION VALUE="">%s
                      <OPTION VALUE="update_item_info_step4?barcode=%s">%s
                      <OPTION VALUE="add_new_copy_step3?recid=%s&barcode=%s">%s
                      <OPTION VALUE="place_new_request_step1?barcode=%s">%s
                      <OPTION VALUE="" DISABLED>%s
                      <OPTION VALUE="" DISABLED>%s
                    </SELECT>
                  </td>
                 </tr>
                 """ % (_("Select an action"),
                        barcode, _("Update"),
                        recid, barcode, _("Add similar copy"),
                        barcode, _("New request"),
                        _("New loan"),
                        _("Delete copy"))

            elif status == 'missing':
                out += """
                     <td align="center">
                       <SELECT style='border: 1px solid #cfcfcf'
                               ONCHANGE="location = this.options[this.selectedIndex].value;">
                         <OPTION VALUE="">%s
                         <OPTION VALUE="update_item_info_step4?barcode=%s">%s
                         <OPTION VALUE="add_new_copy_step3?recid=%s&barcode=%s">%s
                         <OPTION VALUE="" DISABLED>%s
                         <OPTION VALUE="" DISABLED>%s
                         <OPTION VALUE="delete_copy_step1?barcode=%s">%s
                       </SELECT>
                     </td>
                 </tr>
                 """ % (_("Select an action"),
                        barcode, _("Update"),
                        recid, barcode, _("Add similar copy"),
                        _("New request"),
                        _("New loan"),
                        barcode, _("Delete copy"))

            elif status == 'Reference':
                out += """
                     <td align="center">
                       <SELECT style='border: 1px solid #cfcfcf'
                               ONCHANGE="location = this.options[this.selectedIndex].value;">
                         <OPTION VALUE="">%s
                         <OPTION VALUE="update_item_info_step4?barcode=%s">%s
                         <OPTION VALUE="add_new_copy_step3?recid=%s&barcode=%s">%s
                         <OPTION VALUE="place_new_request_step1?barcode=%s">%s
                         <OPTION VALUE="place_new_loan_step1?barcode=%s">%s
                         <OPTION VALUE="delete_copy_step1?barcode=%s">%s
                       </SELECT>
                     </td>
                 </tr>
                 """ % (_("Select an action"),
                        barcode, _("Update"),
                        recid, barcode, _("Add similar copy"),
                        barcode, _("New request"),
                        barcode, _("New loan"),
                        barcode, _("Delete copy"))

            else:
                out += """
                     <td align="center">
                       <SELECT style='border: 1px solid #cfcfcf'
                               ONCHANGE="location = this.options[this.selectedIndex].value;">
                         <OPTION VALUE="">%s
                         <OPTION VALUE="update_item_info_step4?barcode=%s">%s
                         <OPTION VALUE="add_new_copy_step3?recid=%s&barcode=%s">%s
                         <OPTION VALUE="place_new_request_step1?barcode=%s">%s
                         <OPTION VALUE="place_new_loan_step1?barcode=%s">%s
                         <OPTION VALUE="delete_copy_step1?barcode=%s">%s
                       </SELECT>
                     </td>
                 </tr>
                 """ % (_("Select an action"),
                        barcode, _("Update"),
                        recid, barcode, _("Add similar copy"),
                        barcode, _("New request"),
                        barcode, _("New loan"),
                        barcode, _("Delete copy"))

        out += """
             </tbody>
            </table>
            """

        if record_is_periodical:
            out += """
            <div id="pager" class="pager">
                        <form>
                            <img src="/img/sb.gif" class="first" />
                            <img src="/img/sp.gif" class="prev" />
                            <input type="text" class="pagedisplay" />
                            <img src="/img/sn.gif" class="next" />
                            <img src="/img/se.gif" class="last" />
                            <select class="pagesize">
                                <option value="10">10</option>
                                <option value="20">20</option>
                                <option value="30">30</option>
                                <option value="40" selected="selected">40</option>
                            </select>
                        </form>
            </div>
            """

        out += """
            </br>
            <table class="bibcirctable">
                <tr>
                    <td>
                    <input type=button
                onClick="location.href='%s/admin2/bibcirculation/add_new_copy_step3?ln=%s&recid=%s'"
                    value='%s' class="formbutton">
                    </td>
                </tr>
            </table>
            <br />

            <table class="bibcirctable">
                <tr>
                    <td class="bibcirctableheader">%s</td>
                </tr>
            </table>
            <table class="tablesortersmall" border="0" cellpadding="0" cellspacing="1">
                <tr>
                    <th width="100">%s</th>
                    <td width="50">%s</td>
                    <td>
                    <input type="button" value='%s'
            onClick="location.href='%s/admin2/bibcirculation/get_item_requests_details?ln=%s&recid=%s'"
            onmouseover="this.className='bibcircbuttonover'"
            onmouseout="this.className='bibcircbutton'"
                      class="bibcircbutton">
                    </td>
                </tr>

                <tr>
                    <th width="100">%s</th>
                    <td width="50">%s</td>
                    <td>
                    <input type="button" value='%s'
            onClick="location.href='%s/admin2/bibcirculation/get_item_loans_details?ln=%s&recid=%s'"
            onmouseover="this.className='bibcircbuttonover'"
            onmouseout="this.className='bibcircbutton'"
                      class="bibcircbutton">
                    </td>
                </tr>

                <tr>
                    <th width="100">%s</th>
                    <td width="50">%s</td>
                    <td>
                    <input type="button" value='%s'
            onClick="location.href='%s/admin2/bibcirculation/list_purchase?ln=%s&status=%s&recid=%s'"
            onmouseover="this.className='bibcircbuttonover'"
            onmouseout="this.className='bibcircbutton'"
                      class="bibcircbutton">
                    </td>
                </tr>

            </table>

            <br />
            <table class="bibcirctable">
                 <tr>
                     <td class="bibcirctableheader">%s</td>
                </tr>
            </table>
            <table class="tablesortersmall" border="0" cellpadding="0" cellspacing="1">
                 <tr>
                      <th width="100">%s</th>
                      <td width="50">%s</td>
                      <td>
                      <input type="button" value='%s'
    onClick="location.href='%s/admin2/bibcirculation/get_item_req_historical_overview?ln=%s&recid=%s'"
    onmouseover="this.className='bibcircbuttonover'"
    onmouseout="this.className='bibcircbutton'"
                      class="bibcircbutton">
                      </td>
                 </tr>

                 <tr>
                      <th width="100">%s</th>
                      <td width="50">%s</td>
                      <td>
                      <input type="button" value='%s'
onClick="location.href='%s/admin2/bibcirculation/get_item_loans_historical_overview?ln=%s&recid=%s'"
    onmouseover="this.className='bibcircbuttonover'"
    onmouseout="this.className='bibcircbutton'"
                      class="bibcircbutton">
                      </td>
                 </tr>

                 <tr>
                      <th width="100">%s</th>
                      <td width="50">%s</td>
                      <td>
                      <input type="button" value='%s'
onClick="location.href='%s/admin2/bibcirculation/list_purchase?ln=%s&status=%s&recid=%s'"
    onmouseover="this.className='bibcircbuttonover'"
    onmouseout="this.className='bibcircbutton'"
                      class="bibcircbutton">
                      </td>
                 </tr>
            </table>
            <br />
            """ % (CFG_SITE_URL, ln, recid, _("Add new copy"),
    _("Hold requests and loans overview on %(date)s")
    % {'date': dateutils.convert_datestruct_to_datetext(localtime())},
    _("Hold requests"), len(requests), _("More details"), CFG_SITE_URL, ln, recid,
    _("Loans"), len(loans), _("More details"), CFG_SITE_URL, ln, recid,
    _("Purchases"), len(purchases), _("More details"), CFG_SITE_URL, ln,
    CFG_BIBCIRCULATION_ACQ_STATUS_NEW, recid,
    _("Historical overview"), _("Hold requests"), len(req_hist_overview),
    _("More details"), CFG_SITE_URL, ln, recid, _("Loans"), len(loans_hist_overview),
    _("More details"), CFG_SITE_URL, ln, recid, _("Purchases"), len(purchases_hist_overview),
    _("More details"), CFG_SITE_URL, ln, CFG_BIBCIRCULATION_ACQ_STATUS_RECEIVED, recid)

        out += """
           <table class="bibcirctable">
             <tr>
               <td>
                 <input type=button value='%s'
                 onClick="history.go(-1)" class="formbutton">
               </td>
             </tr>
           </table>
           <br />
           <br />
           <br />
           </div>
           """ % (_("Back"))

        return out

    def tmpl_get_item_requests_details(self, result, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = load_menu(ln)

        if len(result) == 0:
            out += """
            <div class="bibcircbottom">
            <br />
            <div class="bibcircinfoboxmsg">%s</div>
            <br />
            """ % (_("There are no requests."))

        else:
            out += """
            <style type="text/css"> @import url("/css/tablesorter.css"); </style>
            <script src="/%s" type="text/javascript"></script>
            <script type="text/javascript">
            $(document).ready(function() {
              $('#table_requests').tablesorter({widthFixed: true, widgets: ['zebra']})
            });
            </script>
        <form name="all_loans_form"
              action="%s/admin2/bibcirculation/update_loan_request_status" method="get" >
            <div class="bibcircbottom">
            <br />
            <table id="table_requests" class="tablesorter"
                   border="0" cellpadding="0" cellspacing="1">
                <thead>
                    <tr>
                        <th>%s</th>
                        <th>%s</th>
                        <th>%s</th>
                        <th>%s</th>
                        <th>%s</th>
                        <th>%s</th>
                        <th>%s</th>
                        <th>%s</th>
                        <th>%s</th>
                        <th>%s</th>
                    </tr>
                </thead>
                <tbody>
                  """% (JQUERY_TABLESORTER,
                        CFG_SITE_URL,
                        _("Borrower"),
                        _("Status"),
                        _("Library"),
                        _("Location"),
                        _("Barcode"),
                        _("Item Desc"),
                        _("From"),
                        _("To"),
                        _("Request date"),
                        _("Option(s)"))


            for (borrower_id, name, id_bibrec, barcode, status, library,
                 location, description, date_from, date_to, request_id,
                 request_date) in result:

                borrower_link = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/get_borrower_details',
                                {'borrower_id': borrower_id, 'ln': ln}, (name))

                out += """
            <tr>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td align="center">
                   <input type=button
onClick="location.href='%s/admin2/bibcirculation/create_loan?recid=%s&request_id=%s&borrower_id=%s'" value='%s' class='formbutton'>
                   <input type=button
onClick="location.href='%s/admin2/bibcirculation/get_item_requests_details?recid=%s&request_id=%s'" value='%s' class='formbutton'>
                </td>
            </tr>
            """ % (borrower_link, status, library, location, barcode, description,
                   date_from, date_to, request_date, CFG_SITE_URL,
                   id_bibrec, request_id, borrower_id, _("Create loan"),
                   CFG_SITE_URL, id_bibrec, request_id, _("Cancel hold request"))

        out += """
        </tbody>
        </table>
        <br />
        <table class="bibcirctable">
            <tr>
                <td>
                    <input type=button
                    onClick="history.go(-1)" value='%s' class='formbutton'>
                </td>
            </tr>
        </table>
        <br />
        <br />
        <br />
       </div>
        </form>
        """ % (_("Back"))

        return out

    def tmpl_get_item_loans_details(self, result, recid, infos,
                                    ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += load_menu(ln)

        if len(result) == 0:
            out += """
            <div class="bibcircbottom">
            <br />
            <div class="bibcircinfoboxmsg">%s</div>
            <br />
            """ % (_("There are no loans."))

        else:
            out += """
            <div class="bibcircbottom">
            <style type="text/css"> @import url("/css/tablesorter.css"); </style>
            <script src="/%s" type="text/javascript"></script>
            <script type="text/javascript">
            $(document).ready(function() {
              $('#table_loans').tablesorter({widthFixed: true, widgets: ['zebra']})
            });
            </script>
            <br />
            <form name="borrower_form"
                  action="%s/admin2/bibcirculation/get_item_loans_details" method="get" >
            <input type=hidden name=recid value="%s">
            """ % (CFG_SITE_URL,
                   recid)

            out += """
             <br />
             <table id="table_loans" class="tablesorter" border="0"
                                     cellpadding="0" cellspacing="1">
               <thead>
                    <tr>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                    </tr>
                </thead>
                <tbody>
                """% (JQUERY_TABLESORTER,
                      _("Borrower"),
                      _("Barcode"),
                      _("Loaned on"),
                      _("Due date"),
                      _("Renewals"),
                      _("Overdue letter"),
                      _("Loan status"),
                      _("Loan notes"),
                      _("Loan options"))


            for (borrower_id, borrower_name, barcode, loaned_on,
                 due_date, nb_renewal, nb_overdue, date_overdue,
                 status, notes, loan_id) in result:

                borrower_link = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/get_borrower_details',
                                {'borrower_id': borrower_id, 'ln': ln},
                                (borrower_name))

                no_notes_link = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/get_loans_notes',
                                {'loan_id': loan_id, 'ln': ln}, (_("No notes")))

                see_notes_link = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/get_loans_notes',
                               {'loan_id': loan_id, 'ln': ln}, (_("See notes")))

                if notes == "" or str(notes) == '{}':
                    check_notes = no_notes_link
                else:
                    check_notes = see_notes_link

                out += """
            <tr>
                 <td>%s</td>
                 <td>%s</td>
                 <td>%s</td>
                 <td>%s</td>
                 <td>%s</td>
                 <td>%s - %s</td>
                 <td>%s</td>
                 <td>%s</td>
                 """ % (borrower_link, barcode, loaned_on, due_date,
                        nb_renewal, nb_overdue, date_overdue,
                        status, check_notes)

                out += """
                 <td align="center">
                   <SELECT style='border: 1px solid #cfcfcf'
                        ONCHANGE="location = this.options[this.selectedIndex].value;">
                      <OPTION VALUE="">%s
                      <OPTION VALUE="get_item_loans_details?barcode=%s&loan_id=%s&recid=%s">%s
                      <OPTION VALUE="loan_return_confirm?barcode=%s">%s
                """ % (_("Select an action"),
                       barcode, loan_id, recid, _("Renew"),
                       barcode, _("Return"))

                if status == CFG_BIBCIRCULATION_LOAN_STATUS_EXPIRED:
                    out += """
                      <OPTION VALUE="change_due_date_step1?barcode=%s" DISABLED>%s
                      """ % (barcode, _("Change due date"))
                else:
                    out += """
                      <OPTION VALUE="change_due_date_step1?barcode=%s">%s
                      """ % (barcode, _("Change due date"))

                out += """
    <OPTION VALUE="claim_book_return?borrower_id=%s&recid=%s&loan_id=%s&template=claim_return">%s
                    </SELECT>
                 </td>
             </tr>
             <input type=hidden name=loan_id value="%s">
             """ % (borrower_id, recid, loan_id, _("Send recall"),
                    loan_id)

        out += """
        <tbody>
        </table>
        <br />
        <table class="bibcirctable">
            <tr>
                <td>
                    <input type=button
               onClick="location.href='%s/admin2/bibcirculation/get_item_details?ln=%s&recid=%s'"
                    value='%s'
                    class='formbutton'>
                </td>
            </tr>
        </table>
        <br />
        <br />
        <br />
        </div>
        </form>
        """ % (CFG_SITE_URL, ln,
               recid,
               _("Back"))

        return out

    def tmpl_get_item_req_historical_overview(self, req_hist_overview,
                                          ln=CFG_SITE_LANG):
        """
        Return the historical requests overview of a item.

        @param req_hist_overview: list of old borrowers.
        """

        _ = gettext_set_language(ln)

        out = load_menu(ln)

        if len(req_hist_overview) == 0:
            out += """
            <div class="bibcircbottom">
            <br />
            <div class="bibcircinfoboxmsg">%s</div>
            <br />
            """ % (_("There are no requests."))

        else:
            out += """
             <div class="bibcircbottom">
             <style type="text/css"> @import url("/css/tablesorter.css"); </style>
            <script src="/%s" type="text/javascript"></script>
            <script type="text/javascript">
            $(document).ready(function() {
              $('#table_holdings').tablesorter({widthFixed: true, widgets: ['zebra']})
            });
            </script>
              <br />
              <br />
              <table id="table_holdings" class="tablesorter"
                     border="0" cellpadding="0" cellspacing="1">
              <thead>
              <tr>
               <th>%s</th>
               <th>%s</th>
               <th>%s</th>
               <th>%s</th>
               <th>%s</th>
               <th>%s</th>
               <th>%s</th>
              </tr>
              </thead>
              </tbody>
                     """ % (JQUERY_TABLESORTER,
                            _("Borrower"),
                            _("Barcode"),
                            _("Library"),
                            _("Location"),
                            _("From"),
                            _("To"),
                            _("Request date"))

            for (name, borrower_id, barcode, library_name,
                 location, req_from, req_to, req_date) in req_hist_overview:

                borrower_link = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/get_borrower_details',
                                {'borrower_id': borrower_id, 'ln': ln}, (name))

                out += """
                  <tr>
                   <td>%s</td>
                   <td>%s</td>
                   <td>%s</td>
                   <td>%s</td>
                   <td>%s</td>
                   <td>%s</td>
                   <td>%s</td>
                  </tr>

                 """ % (borrower_link, barcode, library_name,
                        location, req_from, req_to, req_date)

        out += """
           </tbody>
           </table>
           <br />
           <table class="bibcirctable">
                <tr>
                    <td>
                        <input type=button value='%s'
                               onClick="history.go(-1)"
                               class="formbutton">
                    </td>
                </tr>
           </table>
           <br />
           <br />
           <br />
           </div>

           """ % (_("Back"))

        return out

    def tmpl_get_item_loans_historical_overview(self, loans_hist_overview,
                                            ln=CFG_SITE_LANG):
        """
        Return the historical loans overview of an item.

        @param loans_hist_overview: list of old borrowers.
        """

        _ = gettext_set_language(ln)

        out = """
        """
        out += load_menu(ln)

        out += """<div class="bibcircbottom">
                  <style type="text/css"> @import url("/css/tablesorter.css"); </style>
                  <script src="/%s" type="text/javascript"></script>
                  <script type="text/javascript">
                  $(document).ready(function() {
                    $('#table_loans').tablesorter({widthFixed: true, widgets: ['zebra']})
                  });
                  </script>
                    <br />
                    <br />
                    <table id="table_loans" class="tablesorter"
                           border="0" cellpadding="0" cellspacing="1">
                    <thead>
                     <tr>
                     <th>%s</th>
                     <th>%s</th>
                     <th>%s</th>
                     <th>%s</th>
                     <th>%s</th>
                     <th>%s</th>
                     <th>%s</th>
                     <th>%s</th>
                     <th>%s</th>
                     </tr>
                     </thead>
                     <tbody>
                     """ % (JQUERY_TABLESORTER,
                            _("Borrower"),
                            _("Barcode"),
                            _("Library"),
                            _("Location"),
                            _("Loaned on"),
                            _("Due date"),
                            _("Returned on"),
                            _("Renewals"),
                            _("Overdue letters"))

        for (name, borrower_id, barcode, library_name, location, loaned_on,
             due_date, returned_on, nb_renew,
             nb_overdueletters) in loans_hist_overview:

            borrower_link = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/get_borrower_details',
                                {'borrower_id': borrower_id, 'ln': ln}, (name))

            out += """ <tr>
                       <td>%s</td>
                       <td>%s</td>
                       <td>%s</td>
                       <td>%s</td>
                       <td>%s</td>
                       <td>%s</td>
                       <td>%s</td>
                       <td>%s</td>
                       <td>%s</td>
                       </tr>
                 """ % (borrower_link, barcode, library_name,
                        location, loaned_on,
                        due_date, returned_on, nb_renew,
                        nb_overdueletters)

        out += """
           </tbody>
           </table>
           <br />
           <table class="bibcirctable">
                <tr>
                     <td><input type=button value='%s'
                          onClick="history.go(-1)" class="formbutton"></td>
                </tr>
           </table>
           <br />
           <br />
           <br />
           </div>

           """ % (_("Back"))

        return out

    def tmpl_update_item_info_step1(self, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = load_menu(ln)

        out += """
        <div class="bibcircbottom">
        <form name="update_item_info_step1_form"
              action="%s/admin2/bibcirculation/update_item_info_step2" method="get" >
              """ % (CFG_SITE_URL)
        out += """
        <br />
        <br />
        <br />
        <input type=hidden name=start value="0">
        <input type=hidden name=end value="10">
        <table class="bibcirctable">
                <tr align="center">
                  <td class="bibcirctableheader">%s
                    <input type="radio" name="f" value="" checked>%s
                    <input type="radio" name="f" value="name">%s
                    <input type="radio" name="f" value="email">%s
                    <input type="radio" name="f" value="email">%s
                    <br /><br />
                  </td>
            """ % (_("Search item by"), _("RecId/Item details"), _("year"),
                   _("author"), _("title"))

        out += """
                <tr align="center">
                  <td>
                    <input type="text" size="50" name="p" style='border: 1px solid #cfcfcf'>
                  </td>
                </tr>
        </table>
        <br />
        <table class="bibcirctable">
            <tr align="center">
                <td>
                    <input type=button
                           value="%s"
                           onClick="history.go(-1)"
                           class="formbutton">

                    <input type="submit"
                           value="%s"
                           class="formbutton">
                </td>
            </tr>
        </table>
        <br />
        <br />
        <br />
        <br />
        </div>
        <form>
        """ % (_("Back"), _("Search"))

        return out

    def tmpl_update_item_info_step2(self, result, ln=CFG_SITE_LANG):
        """
        @param result: list with recids
        @type result: list

        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = load_menu(ln)

        out += """
        <div class="bibcircbottom">
        <br />
        <br />
        <table class="bibcirctable">
          <tr align="center">
            <td class="bibcirccontent"><strong>%s</strong></td>
          </tr>
        </table>
        <table class="bibcirctable">
        </tr>
        """ % (_("%(nb_items_found)i items found")
                    % {'nb_items_found': len(result)})

        for recid in result:

            title_link = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/update_item_info_step3',
                                {'recid': recid, 'ln': ln},
                                (book_title_from_MARC(recid)))

            out += """
                <tr align="center">
                <td class="contents">%s</td>
                </tr>
                """ % (title_link)

        out += """
        </table>
        <br />
        <table class="bibcirctable">
        <tr align="center">
        <td>
        <input type=button value="%s" onClick="history.go(-1)" class="formbutton">
        </td>
        </tr>
        </table>
        <br />
        <br />
        <br />
        </div>
        """ % (_("Back"))
        return out

    def tmpl_update_item_info_step3(self, recid, result, ln=CFG_SITE_LANG):
        """
        @param recid: identify the record. Primary key of bibrec.
        @type recid: int

        @param result: book's information
        @type result: tuple

        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = """
        """
        out += load_menu(ln)

        (book_title, book_year, book_author,
                     book_isbn, book_editor) = book_information_from_MARC(recid)

        if book_isbn:
            book_cover = get_book_cover(book_isbn)
        else:
            book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)

        out += """
           <form name="update_item_info_step3_form"
                 action="%s/admin2/bibcirculation/update_item_info_step4" method="get" >
           <div class="bibcircbottom">
                <br />
                     <table class="bibcirctable">
                          <tr>
                               <td class="bibcirctableheader" width="10">%s</td>
                          </tr>
                </table>
                <table class="bibcirctable">
                 <tr valign='top'>
                    <td width="400">
                    <table>
                     <tr>
                        <td width="100">%s</td>
                        <td class="bibcirccontent">%s</td>
                     </tr>
                     <tr>
                        <td width="100">%s</td>
                        <td class="bibcirccontent">%s</td>
                     </tr>
                     <tr>
                        <td width="100">%s</td>
                        <td class="bibcirccontent">%s</td>
                         </tr>
                     <tr>
                        <td width="100">%s</td>
                        <td class="bibcirccontent">%s</td>
                     </tr>
                     <tr>
                        <td width="100">%s</td>
                        <td class="bibcirccontent">%s</td>
                     </tr>
                     </table>
                     </td>
                     <td class="bibcirccontent">
                        <img style='border: 1px solid #cfcfcf' src="%s" alt="Book Cover"/>
                     </td>
                 </tr>
                </table>

           <br />

           """ % (CFG_SITE_URL,
                   _("Item details"),
                   _("Name"),
                   book_title,
                   _("Author(s)"),
                   book_author,
                   _("Year"),
                   book_year,
                   _("Publisher"),
                   book_editor,
                   _("ISBN"),
                   book_isbn,
                   str(book_cover))


        out += """<table class="bibcirctable">
                    <tr>
                      <td>%s</td>
                      <td align="center">%s</td>
                      <td align="center">%s</td>
                      <td align="center">%s</td>
                      <td align="center">%s</td>
                      <td align="center">%s</td>
                      <td align="center">%s</td>
                      <td align="center">%s</td>
                      <td align="center"></td>
                      <td width="350"></td>
                    </tr>""" % (_("Barcode"),
                                _("Status"),
                                _("Library"),
                                _("Location"),
                                _("Loan period"),
                                _("No of loans"),
                                _("Collection"),
                                _("Description"))


        for (barcode, loan_period, lib_name, libid, location, nb_requests,
             status, collection, description) in result:

            library_link = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/get_library_details',
                                {'library_id': libid, 'ln': ln}, (lib_name))

            out += """
                 <tr>
                     <td class="bibcirccontent">%s</td>
                     <td class="bibcirccontent" align="center">%s</td>
                     <td class="bibcirccontent" align="center">%s</td>
                     <td class="bibcirccontent" align="center">%s</td>
                     <td class="bibcirccontent" align="center">%s</td>
                     <td class="bibcirccontent" align="center">%s</td>
                     <td class="bibcirccontent" align="center">%s</td>
                     <td class="bibcirccontent" align="center">%s</td>
                     <td class="bibcirccontent" align="center">
                     <input type=button
      onClick="location.href='%s/admin2/bibcirculation/update_item_info_step4?ln=%s&barcode=%s'"
                     value="%s" class="formbutton">
                     </td>
                     <td class="bibcirccontent" width="350"></td>
                 </tr>
                 """ % (barcode, status, library_link, location, loan_period,
                        nb_requests, collection, description, CFG_SITE_URL, ln,
                        barcode, _("Update"))

        out += """
           </table>
           <br />
           <table class="bibcirctable">
                <tr>
                     <td>
                        <input type=button value="%s"
                         onClick="history.go(-1)" class="formbutton">
                        <input type=hidden name=recid value="%s"></td>
                </tr>
           </table>
           <br />
           <br />
           </div>
           """ % (_("Back"), recid)

        return out

    def tmpl_update_item_info_step4(self, recid, result, libraries,
                                    ln=CFG_SITE_LANG):
        """
        @param recid: identify the record. Primary key of bibrec
        @type recid: int

        @param result: book's information
        @type result: tuple

        @param libraries: list of libraries
        @type libraries: list

        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = load_menu(ln)

        (title, year, author, isbn, editor) = book_information_from_MARC(recid)

        barcode = result[0]
        expected_arrival_date = db.get_expected_arrival_date(barcode)

        if isbn:
            book_cover = get_book_cover(isbn)
        else:
            book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)

        out += """
           <style type="text/css"> @import url("/css/tablesorter.css"); </style>
           <form name="update_item_info_step4_form"
                 action="%s/admin2/bibcirculation/update_item_info_step5" method="get" >
           <div class="bibcircbottom">
                <br />
                <table class="bibcirctable">
                    <tr>
                        <td class="bibcirctableheader" width="10">%s</td>
                    </tr>
                </table>
                <table class="bibcirctable">
                 <tr valign='top'>
                    <td width="400">
                    <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
                     <tr>
                       <th width="100">%s</th>
                       <td>%s</td>
                     </tr>
                     <tr>
                       <th width="100">%s</th>
                       <td>%s</td>
                     </tr>
                     <tr>
                       <th width="100">%s</th>
                       <td>%s</td>
                     </tr>
                     <tr>
                       <th width="100">%s</th>
                       <td>%s</td>
                     </tr>
                     <tr>
                       <th width="100">%s</th>
                       <td>%s</td>
                     </tr>
                   </table>
                 </td>
                 <td class="bibcirccontent">
                    <img style='border: 1px solid #cfcfcf' src="%s" alt="Book Cover"/>
                 </td>
               </tr>
              </table>

           <br />

           """ % (CFG_SITE_URL,
                   _("Item details"),
                   _("Name"),
                   title,
                   _("Author(s)"),
                   author,
                   _("Year"),
                   year,
                   _("Publisher"),
                   editor,
                   _("ISBN"),
                   isbn,
                   str(book_cover))

        out += """
             <table class="bibcirctable">
                <tr>
                     <td class="bibcirctableheader">%s</td>
                </tr>
             </table>
             <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">
               <tr>
                 <th width="100">%s</th>
                 <td>
                    <input type="text" style='border: 1px solid #cfcfcf'
                           size=35 name="barcode" value="%s">
                    <input type=hidden name=old_barcode value="%s">
                 </td>
               </tr>
               <tr>
                 <th width="100">%s</th>
                 <td>
                   <select name="library_id"  style='border: 1px solid #cfcfcf'>

                """ % (_("Update copy information"),
                       _("Barcode"), result[0], result[0],
                       _("Library"))

        for(library_id, name) in libraries:

            if library_id == result[1]:
                out += """<option value ="%s" selected>%s</option>
                        """ % (library_id, name)

            else:
                out += """<option value ="%s">%s</option>
                        """ % (library_id, name)

        out += """
                    </select>
                    </td>
                </tr>
                <tr>
                  <th width="100">%s</th>
                  <td>
                    <input type="text" style='border: 1px solid #cfcfcf' size=35
                           name="location" value="%s">
                  </td>
                </tr>
                <tr>
                  <th width="100">%s</th>
                  <td>
                    <select name="collection" style='border: 1px solid #cfcfcf'>
                    """ % (_("Location"), result[4],
                           _("Collection"))

        for collection in CFG_BIBCIRCULATION_COLLECTION:
            if collection == result[3]:
                out += """
                    <option value="%s" selected="selected">%s</option>
                       """ % (collection, collection)
            else:
                out += """
                    <option value="%s">%s</option>
                       """ % (collection, collection)

        out += """
                   </select>
                  </td>
                </tr>
                <tr>
                  <th width="100">%s</th>
                  <td>
                    <input type="text" style='border: 1px solid #cfcfcf' size=35
                           name="description" value="%s">
                  </td>
                </tr>
                    """ % (_("Description"), result[5] or '-')

        out += """
                <tr>
                    <th width="100">%s</th>
                    <td>
                      <select name="loan_period"  style='border: 1px solid #cfcfcf'>
                """ % (_("Loan period"))

        for loan_period in CFG_BIBCIRCULATION_ITEM_LOAN_PERIOD:
            if loan_period == result[6]:
                out += """
                          <option value="%s" selected="selected">%s</option>
                       """ % (loan_period, loan_period)
            else:
                out += """
                          <option value="%s">%s</option>
                       """ % (loan_period, loan_period)

        out += """
                      </select>
                    </td>
                </tr>
            """

        out += """
                 <tr>
                    <th width="100">%s</th>
                    <td>
                      <select name="status"  style='border: 1px solid #cfcfcf'>

                      """ % (_("Status"))


        for st in CFG_BIBCIRCULATION_ITEM_STATUS:
            if st == CFG_BIBCIRCULATION_ITEM_STATUS_ON_LOAN and result[7] != CFG_BIBCIRCULATION_ITEM_STATUS_ON_LOAN:
                pass # to avoid creting a fake loan,
                     # 'on loan' is only shown if the item was already on loan
            elif st == result[7]:
                out += """
                          <option value="%s" selected>%s</option>
                    """ % (st, st)
            else:
                out += """
                          <option value="%s">%s</option>
                    """ % (st, st)

        out += """  </select>
                    </td>
                 </tr>
                 <tr>
                  <th width="100">%s</th>
                  <td>
                    <input type="text" style='border: 1px solid #cfcfcf' size=35
                           name="expected_arrival_date" value="%s">
                  </td>
                </tr>
                </table>
           <br />
           <table class="bibcirctable">
                <tr>
                     <td>
                       <input type=button onClick="history.go(-1)"
                       value='%s' class='formbutton'>
                       <input type="submit" value='%s' class="formbutton">
                       <input type=hidden name=recid value="%s">
                     </td>
                </tr>
           </table>
           <br />
           <br />
           </div>
           </form>
           """ % (_("Expected arrival date"), expected_arrival_date,
                  _("Back"), _("Continue"), recid)

        return out

    def tmpl_update_item_info_step5(self, tup_infos, ln=CFG_SITE_LANG):
        """
        @param tup_info: item's information
        @type tup_info: tuple

        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += load_menu(ln)

        out += """
            <style type="text/css"> @import url("/css/tablesorter.css"); </style>
            <div class="bibcircbottom">
            <form name="update_item_info_step5_form"
                  action="%s/admin2/bibcirculation/update_item_info_step6" method="get" >
              <br />
              <br />
              <table class="bibcirctable">
                <tr>
                    <td class="bibcirctableheader">%s</td>
                </tr>
              </table>
              <table class="tablesortersmall" border="0" cellpadding="0" cellspacing="1">
                <tr>
                    <th width="100">%s</th> <td>%s</td>
                </tr>
                <tr>
                    <th width="100">%s</th> <td>%s</td>
                </tr>
                <tr>
                    <th width="100">%s</th> <td>%s</td>
                </tr>
                <tr>
                    <th width="100">%s</th> <td>%s</td>
                </tr>
                <tr>
                    <th width="100">%s</th> <td>%s</td>
                </tr>
                <tr>
                    <th width="100">%s</th> <td>%s</td>
                </tr>
                <tr>
                    <th width="100">%s</th> <td>%s</td>
                </tr>
                <tr>
                    <th width="100">%s</th> <td>%s</td>
                </tr>
              </table>
              <br />
              <table class="bibcirctable">
                <tr>
                  <td>
                     <input type=button value="%s"
                       onClick="history.go(-1)" class="formbutton">
                     <input type="submit"
                      value="%s" class="formbutton">
                     <input type=hidden name=barcode value="%s">
                     <input type=hidden name=old_barcode value="%s">
                     <input type=hidden name=library_id value="%s">
                     <input type=hidden name=location value="%s">
                     <input type=hidden name=collection value="%s">
                     <input type=hidden name=description value="%s">
                     <input type=hidden name=loan_period value="%s">
                     <input type=hidden name=status value="%s">
                     <input type=hidden name=expected_arrival_date value="%s">
                     <input type=hidden name=recid value="%s">
                  </td>
                </tr>
              </table>
              <br />
              <br />
            </form>
            </div>
                """ % (CFG_SITE_URL, _("New copy information"),
                    _("Barcode"), cgi.escape(tup_infos[0], True),
                    _("Library"), cgi.escape(tup_infos[3], True),
                    _("Location"), cgi.escape(tup_infos[4], True),
                    _("Collection"), cgi.escape(tup_infos[5], True),
                    _("Description"), cgi.escape(tup_infos[6], True),
                    _("Loan period"), cgi.escape(tup_infos[7], True),
                    _("Status"), cgi.escape(tup_infos[8], True),
                    _("Expected arrival date"), cgi.escape(tup_infos[9], True),
                    _("Back"), _("Confirm"),
                    cgi.escape(tup_infos[0], True),
                    cgi.escape(tup_infos[1], True),
                    tup_infos[2], cgi.escape(tup_infos[4], True),
                    cgi.escape(tup_infos[5], True),
                    cgi.escape(tup_infos[6], True),
                    cgi.escape(tup_infos[7], True),
                    cgi.escape(tup_infos[8], True),
                    cgi.escape(tup_infos[9], True), tup_infos[10])

        return out


    def tmpl_add_new_copy_step1(self, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = load_menu(ln)

        out += """
        <div class="bibcircbottom">
        <form name="add_new_copy_step1_form"
              action="%s/admin2/bibcirculation/add_new_copy_step2"
              method="get" >
        <br />
        <br />
        <br />
        <input type=hidden name=start value="0">
        <input type=hidden name=end value="10">
        <table class="bibcirctable">
           <tr align="center">
           """ % (CFG_SITE_URL)
        out += """
             <td class="bibcirctableheader">%s
             <input type="radio" name="f" value="" checked>%s
             <input type="radio" name="f" value="name">%s
             <input type="radio" name="f" value="author">%s
             <input type="radio" name="f" value="title">%s
             """ % (_("Search item by"), _("RecId/Item details"), _("year"),
                    _("author"), _("title"))

        out += """
             <br />
             <br />
            </td>
           <tr align="center">
             <td>
               <input type="text" size="50" name="p" style='border: 1px solid #cfcfcf'>
             </td>
           </tr>
        </table>
        <br />
        <table class="bibcirctable">
            <tr align="center">
                <td>
                    <input type=button
                            value="%s"
                            onClick="history.go(-1)"
                            class="formbutton">
                    <input type="submit"
                            value="%s"
                            class="formbutton">
                </td>
            </tr>
        </table>
        <br />
        <br />
        <br />
        <br />
        </div>
        <form>
        """ % (_("Back"), _("Search"))

        return out

    def tmpl_add_new_copy_step2(self, result, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = load_menu(ln)

        out += """
        <div class="bibcircbottom">
        <br />
        <br />
        <table class="bibcirctable">
          <tr align="center">
            <td class="bibcirccontent">
              <strong>%s items found</strong>
            </td>
          </tr>
        </table>
        <table class="bibcirctable">
        </tr>
        """ % (len(result))

        for recid in result:

            title_link = create_html_link(CFG_SITE_URL +
                                    '/admin2/bibcirculation/add_new_copy_step3',
                                    {'recid': recid, 'ln': ln},
                                    (book_title_from_MARC(recid)))

            out += """
                <tr align="center">
                <td class="contents">%s</td>
                </tr>
                """ % (title_link)

        out += """
        </table>
        <br />
        """

        out += """
        <table class="bibcirctable">
        <tr align="center">
        <td>
        <input type=button value="%s" onClick="history.go(-1)" class="formbutton">
        </td>
        </tr>
        </table>
        <br />
        <br />
        <br />
        </div>
        """ % (_("Back"))
        return out

    def tmpl_add_new_copy_step3(self, recid, result, libraries,
                                original_copy_barcode, tmp_barcode,
                                infos, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        record_is_periodical = is_periodical(recid)

        out = self.tmpl_infobox(infos, ln)

        out += load_menu(ln)

        (book_title, book_year, book_author,
                     book_isbn, book_editor) = book_information_from_MARC(recid)

        if book_isbn:
            book_cover = get_book_cover(book_isbn)
        else:
            book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)

        out += """
            <style type="text/css">
                @import url("/css/tablesorter.css");
            </style>

            <style type="text/css">
                @import url("/{0}/themes/blue/style.css");
            </style>
            <style type="text/css">
                @import url("/{0}/addons/pager/jquery.tablesorter.pager.css");
            </style>

            <script src="/{1}" type="text/javascript"></script>
            <script src="/{0}/addons/pager/jquery.tablesorter.pager.js"
                    type="text/javascript"></script>
            """.format(JQUERY_TABLESORTER_BASE, JQUERY_TABLESORTER)

        if record_is_periodical:
            out += """
            <script type="text/javascript">
                $(document).ready(function(){
                    $("#table_copies")
                      .tablesorter({sortList: [[6,1]],widthFixed: true, widgets: ['zebra']})
                      .bind("sortStart",function(){$("#overlay").show();})
                      .bind("sortEnd",function(){$("#overlay").hide()})
                      .tablesorterPager({container: $("#pager"), positionFixed: false});
                });
            </script>
            """
        else:
            out += """
            <script type="text/javascript">
                $(document).ready(function() {
                    $('#table_copies').tablesorter({widthFixed: true, widgets: ['zebra']})
                });
            </script>
            """

        out += """
           <form name="add_new_copy_step3_form"
                 action="%s/admin2/bibcirculation/add_new_copy_step4" method="get" >
           <div class="bibcircbottom">
                <br />
                <table class="bibcirctable">
                    <tr>
                        <td class="bibcirctableheader" width="10">%s</td>
                    </tr>
                </table>
                <table class="bibcirctable">
                 <tr valign='top'>
                    <td width="400">
                    <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
                     <tr>
                        <th width="100">%s</th>
                        <td>%s</td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>%s</td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>%s</td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>%s</td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>%s</td>
                     </tr>
                     </table>
                     </td>
                     <td class="bibcirccontent">
                        <img style='border: 1px solid #cfcfcf' src="%s" alt="Book Cover"/>
                     </td>
                     </tr>
              </table>

           <br />
           <table class="bibcirctable">
                <tr>
                     <td class="bibcirctableheader">%s</td>
                </tr>
           </table>

           """ % (CFG_SITE_URL,
                   _("Item details"),
                   _("Name"),
                   book_title,
                   _("Author(s)"),
                   book_author,
                   _("Year"),
                   book_year,
                   _("Publisher"),
                   book_editor,
                   _("ISBN"),
                   book_isbn,
                   str(book_cover),
                   _("Copies of %(x_name)s", x_name=book_title))


        out += """
                  <table class="tablesorter" id="table_copies" border="0"
                         cellpadding="0" cellspacing="1">
                  <thead>
                    <tr>
                      <th>%s</th>
                      <th>%s</th>
                      <th>%s</th>
                      <th>%s</th>
                """ % (_("Barcode"),
                       _("Status"),
                       _("Due date"),
                       _("Library"))

        if not record_is_periodical:
            out += """
                      <th>%s</th>
                   """ % (_("Location"))

        out += """
                      <th>%s</th>
                      <th>%s</th>
                """ % (_("Loan period"),
                       _("No of loans"))

        if not record_is_periodical:
            out += """
                      <th>%s</th>
                   """ % (_("Collection"))

        out += """
                      <th>%s</th>
                    </tr>
                  </thead>
                  <tboby>
                    """ % (_("Description"))

        for (barcode, loan_period, lib_name, libid, location, nb_requests,
             status, collection, description, due_date) in result:

            library_link = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/get_library_details',
                                {'library_id': libid, 'ln': ln}, (lib_name))

            out += """
                 <tr>
                     <td>%s</td>
                     <td>%s</td>
                     <td>%s</td>
                     <td>%s</td>
                     """ % (barcode, status, due_date or '-', library_link)

            if not record_is_periodical:
                out += """
                     <td>%s</td>
                     """ % (location)

            out += """
                     <td>%s</td>
                     <td>%s</td>
                     """ % (loan_period, nb_requests)

            if not record_is_periodical:
                out += """
                     <td>%s</td>
                     """ % (collection or '-')

            out += """
                     <td>%s</td>
                     """ % (description or '-')

        out += """
           </tbody>
           </table>
           """

        if record_is_periodical:
            out += """
            <div id="pager" class="pager">
                        <form>
                            <img src="/img/sb.gif" class="first" />
                            <img src="/img/sp.gif" class="prev" />
                            <input type="text" class="pagedisplay" />
                            <img src="/img/sn.gif" class="next" />
                            <img src="/img/se.gif" class="last" />
                            <select class="pagesize">
                                <option value="10" selected="selected">10</option>
                                <option value="20">20</option>
                                <option value="30">30</option>
                                <option value="40">40</option>
                            </select>
                        </form>
            </div>
            </br>
            """

        if record_is_periodical:
            colspan = 'colspan="5"'
        else:
            colspan = ''

        if original_copy_barcode is not None:
            default_details = db.get_item_info(original_copy_barcode)
            if default_details is not None:
                default_library_id = default_details[1]
                default_collection = default_details[3]
                default_location = default_details[4]
                default_description = default_details[5]
                default_loan_period = default_details[6]

        out += """
          <table class="bibcirctable">
                <tr>
                     <td class="bibcirctableheader">%s</td>
                </tr>
           </table>
           <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">
                <tr>
                    <th>%s</th>
                    <td %s>
                      <input type="text" style='border: 1px solid #cfcfcf' size=35
                             name="barcode" value='%s'>
                    </td>
                </tr>
                <tr>
                    <th>%s</th>
                    <td %s>
                      <select name="library"  style='border: 1px solid #cfcfcf'>

                """ % (_("New copy details"), _("Barcode"),
                       colspan, tmp_barcode, _("Library"), colspan)

        main_library = db.get_main_libraries()
        if main_library is not None:
            main_library = main_library[0][0] #id of the first main library

        for(library_id, name) in libraries:
            if original_copy_barcode is not None and \
               default_details is not None and \
               library_id == default_library_id:
                out += """<option value="%s" selected="selected">%s</option>
                      """ % (library_id, name)
            elif library_id == main_library:
                out += """<option value="%s" selected="selected">%s</option>
                      """ % (library_id, name)
            else:
                out += """<option value="%s">%s</option>""" % (library_id, name)

        if original_copy_barcode is not None \
            and default_location is not None:
            loc = default_location
        else:
            loc = ''

        out += """
                    </select>
                    </td>
                </tr>
            """

        if record_is_periodical:
            out += """ <input type=hidden name=collection value="%s">
                    """ % ("Periodical")
        else:
            out += """
                <tr>
                    <th width="100">%s</th>
                    <td>
                      <input type="text" style='border: 1px solid #cfcfcf' size=35
                             name="location" value="%s">
                    </td>
                </tr>
                """ % (_("Location"), loc)

            out += """
                <tr>
                    <th width="100">%s</th>
                    <td>
                      <select name="collection" style='border: 1px solid #cfcfcf'>
                   """ % (_("Collection"))

            for collection in CFG_BIBCIRCULATION_COLLECTION:
                if original_copy_barcode is not None and \
                   default_collection is not None and \
                   collection == default_collection:
                    out += """
                        <option value="%s" selected="selected">%s</option>
                           """ % (collection, collection)
                else:
                    out += """
                        <option value="%s">%s</option>
                           """ % (collection, collection)

            out += """
                      </select>
                    </td>
                </tr>
                """

        if original_copy_barcode is not None \
           and default_description is not None:
            desc = default_description
        else:
            desc = ''

        out += """
                <tr>
                    <th width="100">%s</th>
                    <td>
                      <input type="text" style='border: 1px solid #cfcfcf' size=35
                             name="description" value="%s">
                    </td>
                </tr>
                """ % (_("Description"), desc)

        out += """
                <tr>
                    <th width="100">%s</th>
                    <td %s>
                      <select name="loan_period"  style='border: 1px solid #cfcfcf'>
                """ % (_("Loan period"), colspan)

        for loan_period in CFG_BIBCIRCULATION_ITEM_LOAN_PERIOD:
            if original_copy_barcode is not None and \
                 default_loan_period is not None and \
                 loan_period == default_loan_period:
                out += """
                          <option value="%s" selected="selected">%s</option>
                       """ % (loan_period, loan_period)
            else:
                out += """
                          <option value="%s">%s</option>
                       """ % (loan_period, loan_period)

        out += """
                      </select>
                    </td>
                </tr>
            """

        out += """
                <tr>
                    <th width="100">%s</th>
                    <td %s>
                    <select name="status"  style='border: 1px solid #cfcfcf'>
                """ % (_("Status"), colspan)

        for st in CFG_BIBCIRCULATION_ITEM_STATUS:
            if st == CFG_BIBCIRCULATION_ITEM_STATUS_ON_SHELF:
                out += """
                          <option value ="%s" selected="selected">%s</option>
                    """ % (st, st)
            else:
                out += """
                          <option value ="%s">%s</option>
                    """ % (st, st)

        out += """
                    </select>
                    </td>
                 </tr>
                 <tr>
                  <th width="100">%s</th>
                  <td %s>
                    <input type="text" style='border: 1px solid #cfcfcf' size=35
                           name="expected_arrival_date" value="">
                  </td>
                 </tr>
                </table>
           <br />
           <table class="bibcirctable">
                <tr>
                     <td>
                       <input type=button value="%s"
                        onClick="history.go(-1)" class="formbutton">
                       <input type="submit" value="%s" class="formbutton">
                       <input type=hidden name=recid value="%s">
                     </td>
                </tr>
           </table>
           <br />
           <br />
           </div>
           </form>
           """ % (_("Expected arrival date"), colspan, _("Back"),
                  _("Continue"), recid)

        return out

    def tmpl_add_new_copy_step4(self, tup_infos, ln=CFG_SITE_LANG):
        """
        @param tup_info: item's information
        @type tup_info: tuple

        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        (barcode, library, _library_name, location, collection, description,
         loan_period, status, expected_arrival_date, recid) = tup_infos

        out = """ """

        out += load_menu(ln)

        out += """
            <style type="text/css"> @import url("/css/tablesorter.css"); </style>
            <div class="bibcircbottom">
            <form name="add_new_copy_step4_form"
                  action="%s/admin2/bibcirculation/add_new_copy_step5"
                  method="get" >
              <br />
              <br />
              <table class="tablesorterborrower">
                <tr>
                    <th width="90">%s</th> <td class="bibcirccontent">%s</td>
                </tr>
                <tr>
                    <th width="90">%s</th> <td class="bibcirccontent">%s</td>
                </tr>
                <tr>
                    <th width="90">%s</th> <td class="bibcirccontent">%s</td>
                </tr>
                <tr>
                    <th width="90">%s</th> <td class="bibcirccontent">%s</td>
                </tr>
                <tr>
                    <th width="90">%s</th> <td class="bibcirccontent">%s</td>
                 </tr>
                 <tr>
                    <th width="90">%s</th> <td class="bibcirccontent">%s</td>
                 </tr>
                 <tr>
                    <th width="90">%s</th> <td class="bibcirccontent">%s</td>
                 </tr>
                 <tr>
                    <th width="90">%s</th> <td class="bibcirccontent">%s</td>
                 </tr>
                </table>
                <br />
                <table class="bibcirctable">
                <tr>
                  <td>
                       <input type=button value="%s"
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit"
                       value="%s" class="formbutton">

                       <input type=hidden name=barcode value="%s">
                       <input type=hidden name=library value="%s">
                       <input type=hidden name=location value="%s">
                       <input type=hidden name=collection value="%s">
                       <input type=hidden name=description value="%s">
                       <input type=hidden name=loan_period value="%s">
                       <input type=hidden name=status value="%s">
                       <input type=hidden name=expected_arrival_date value="%s">
                       <input type=hidden name=recid value="%s">

                  </td>
                 </tr>
                </table>
                <br />
                <br />
                </form>
                </div>
                """ % (CFG_SITE_URL,
                       _("Barcode"), tup_infos[0],
                       _("Library"), tup_infos[2],
                       _("Location"), tup_infos[3],
                       _("Collection"), tup_infos[4],
                       _("Description"), tup_infos[5],
                       _("Loan period"), tup_infos[6],
                       _("Status"), tup_infos[7],
                       _("Expected arrival date"), expected_arrival_date,
                       _("Back"), _("Continue"),
                       barcode, library, location, collection, description,
                       loan_period, status, expected_arrival_date, recid)

        return out

    def tmpl_add_new_copy_step5(self, infos, recid, ln=CFG_SITE_LANG):
        """
        @param recid: identify the record. Primary key of bibrec.
        @type recid: int
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += load_menu(ln)

        if infos == []:
            out += """
            <div class="bibcircbottom">
              <br />
              <br />
              <table class="bibcirctable">
                <tr>
                    <td class="bibcirccontent">%s</td>
                </tr>
                </table>
                <br />
                <table class="bibcirctable">
                    <tr>
                        <td>
                            <input type=button value='%s'
                    onClick="location.href='%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s'"
                            class="formbutton">
                        </td>
                    </tr>
                </table>
                <br />
                <br />
                </div>
        """ % (_("A %(x_url_open)snew copy%(x_url_close)s has been added.") % {'x_url_open': '<a href="' + CFG_SITE_URL + '/admin2/bibcirculation/get_item_details?ln=%s&amp;recid=%s' %(ln, recid) + '">', 'x_url_close': '</a>'},
               _("Back to home"),
               CFG_SITE_URL, ln)

        else:
            out += """<br /> """
            out += self.tmpl_infobox(infos, ln)
            out += """
            <div class="bibcircbottom">
                <br />
                <br />

                <table class="bibcirctable">
                    <tr>
                        <td>
                            <input type=button value='%s'
            onClick="location.href='%s/admin2/bibcirculation/get_item_details?ln=%s&recid=%s'"
                            class="formbutton">
                        </td>
                    </tr>
                </table>
                <br />
                <br />
                </div>
                """ % (_("Back to the record"),
                       CFG_SITE_URL, ln, recid)

        return out

    def tmpl_delete_copy_step1(self, barcode_to_delete, recid, result,
                               infos, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        record_is_periodical = is_periodical(recid)

        out = load_menu(ln)

        (book_title, book_year, book_author,
          book_isbn, book_editor) = book_information_from_MARC(recid)

        if book_isbn:
            book_cover = get_book_cover(book_isbn)
        else:
            book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)


        out += """
            <style type="text/css">
                @import url("/css/tablesorter.css");
            </style>

            <style type="text/css">
                @import url("/{0}/themes/blue/style.css");
            </style>
            <style type="text/css">
                @import url("/{0}/addons/pager/jquery.tablesorter.pager.css");
            </style>

            <script src="/{1}" type="text/javascript"></script>
            <script src="/{0}/addons/pager/jquery.tablesorter.pager.js"
                    type="text/javascript"></script>
            """.format(JQUERY_TABLESORTER_BASE, JQUERY_TABLESORTER)

        if record_is_periodical:
            out += """
            <script type="text/javascript">
                $(document).ready(function(){
                    $("#table_copies")
                      .tablesorter({sortList: [[6,1]],widthFixed: true, widgets: ['zebra']})
                      .bind("sortStart",function(){$("#overlay").show();})
                      .bind("sortEnd",function(){$("#overlay").hide()})
                      .tablesorterPager({container: $("#pager"), positionFixed: false});
                });
            </script>
            """
        else:
            out += """
            <script type="text/javascript">
                $(document).ready(function() {
                    $('#table_copies').tablesorter({widthFixed: true, widgets: ['zebra']})
                });
            </script>
            """

        out += """
           <form name="delete_copy_step2_form"
                 action="%s/admin2/bibcirculation/delete_copy_step2"
                 method="get">
           <div class="bibcircbottom">
                <br />
                     <table class="bibcirctable">
                          <tr>
                               <td class="bibcirctableheader" width="10">%s</td>
                          </tr>
                </table>
                <table class="bibcirctable">
                 <tr valign='top'>
                    <td width="400">
                    <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
                     <tr>
                        <th width="100">%s</th>
                        <td>%s</td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>%s</td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>%s</td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>%s</td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>%s</td>
                     </tr>
                     </table>
                     </td>
                     <td class="bibcirccontent">
                        <img style='border: 1px solid #cfcfcf'
                             src="%s" alt="Book Cover"/>
                     </td>
                     </tr>
              </table>

           <br />
           <table class="bibcirctable">
                <tr>
                     <td class="bibcirctableheader">%s</td>
                </tr>
           </table>

           """ % (CFG_SITE_URL,
                   _("Item details"),
                   _("Name"),
                   book_title,
                   _("Author(s)"),
                   book_author,
                   _("Year"),
                   book_year,
                   _("Publisher"),
                   book_editor,
                   _("ISBN"),
                   book_isbn,
                   str(book_cover),
                   _("Copies of %(x_name)s", x_name=book_title))


        out += """
                  <table class="tablesorter" id="table_copies" border="0"
                         cellpadding="0" cellspacing="1">
                  <thead>
                    <tr>
                      <th>%s</th>
                      <th>%s</th>
                      <th>%s</th>
                      <th>%s</th>
                """ % (_("Barcode"),
                       _("Status"),
                       _("Due date"),
                       _("Library"))

        if not record_is_periodical:
            out += """
                      <th>%s</th>
                   """ % (_("Location"))

        out += """
                      <th>%s</th>
                      <th>%s</th>
                """ % (_("Loan period"),
                       _("No of loans"))

        if not record_is_periodical:
            out += """
                      <th>%s</th>
                   """ % (_("Collection"))

        out += """
                      <th>%s</th>
                    </tr>
                  </thead>
                  <tboby>
                    """ % (_("Description"))

        for (barcode, loan_period, lib_name, libid, location, nb_requests,
             status, collection, description, due_date) in result:

            library_link = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/get_library_details',
                                {'library_id': libid, 'ln': ln}, (lib_name))

            out += """
                 <tr>
                     <td>%s</td>
                     <td>%s</td>
                     <td>%s</td>
                     <td>%s</td>
                     """ % (barcode, status, due_date or '-', library_link)

            if not record_is_periodical:
                out += """
                     <td>%s</td>
                     """ % (location)

            out += """
                     <td>%s</td>
                     <td>%s</td>
                     """ % (loan_period, nb_requests)

            if not record_is_periodical:
                out += """
                     <td>%s</td>
                     """ % (collection or '-')

            out += """
                     <td>%s</td>
                     """ % (description or '-')


        out += """ </tbody>
                  </table>
                """

        if record_is_periodical:
            out += """
            <div id="pager" class="pager">
                        <form>
                            <img src="/img/sb.gif" class="first" />
                            <img src="/img/sp.gif" class="prev" />
                            <input type="text" class="pagedisplay" />
                            <img src="/img/sn.gif" class="next" />
                            <img src="/img/se.gif" class="last" />
                            <select class="pagesize">
                                <option value="10" selected="selected">10</option>
                                <option value="20">20</option>
                                <option value="30">30</option>
                                <option value="40">40</option>
                            </select>
                        </form>
            </div>
            </br>
            """

        out += self.tmpl_infobox(infos, ln)

        out += """<table id="table_copies" class="tablesorter"
                         border="0" cellpadding="0" cellspacing="1">
          <thead>
            <tr>
              <th>%s</th>
              <th>%s</th>
              <th>%s</th>
              <th>%s</th>
              <th>%s</th>
              <th>%s</th>
              <th>%s</th>
              <th>%s</th>
              <th>%s</th>
            </tr>
            </thead>
            <tbody>""" % (_("Barcode"),
                        _("Status"),
                        _("Due date"),
                        _("Library"),
                        _("Location"),
                        _("Loan period"),
                        _("No of loans"),
                        _("Collection"),
                        _("Description"))

        for (barcode, loan_period, lib_name, libid, location, nb_requests,
             status, collection, description, due_date) in result:
            if barcode == barcode_to_delete:
                library_link = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/get_library_details',
                                {'library_id': libid, 'ln': ln}, (lib_name))

                out += """
                     <tr>
                         <td>%s</td>
                         <td>%s</td>
                         <td>%s</td>
                         <td>%s</td>
                         <td>%s</td>
                         <td>%s</td>
                         <td>%s</td>
                         <td>%s</td>
                         <td>%s</td>
                     </tr>
                     """ % (barcode, status, due_date, library_link, location,
                            loan_period, nb_requests, collection or '-',
                            description or '-')

        out += """ </tbody>
                  </table>
                """
        out += """<input type=hidden name=barcode value="%s">
                """ % (str(barcode_to_delete))
        out += """<input type=button value="%s" onClick="history.go(-1)"
                         class="formbutton">
               """ % (_("Back"))
        out += """<input type="submit" value='%s' class="formbutton">
               """ % (_("Delete"))

        out += """</div></form>"""

        return out

    def tmpl_create_loan(self, request_id, recid, borrower,
                               infos, ln=CFG_SITE_LANG):


        _ = gettext_set_language(ln)


        (book_title, _book_year, _book_author,
         book_isbn, _book_editor) = book_information_from_MARC(recid)

        if book_isbn:
            book_cover = get_book_cover(book_isbn)
        else:
            book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)


        out = self.tmpl_infobox(infos, ln)

        out += load_menu(ln)

        (borrower_id, ccid, name, email, phone, address, mailbox) = borrower

        display_id = borrower_id
        id_string = _("ID")
        if CFG_CERN_SITE == 1:
            display_id = ccid
            id_string = _("CCID")


        out += """
            <style type="text/css"> @import url("/css/tablesorter.css"); </style>
            <form name="return_form" action="%s/admin2/bibcirculation/register_new_loan"
                  method="post" >
            <div class="bibcircbottom">
            <input type=hidden name=borrower_id value="%s">
            <input type=hidden name=request_id value="%s">
            <br />
            <table class="bibcirctable">
                <tr>
                    <td class="bibcirctableheader">%s</td>
                </tr>
            </table>
            </form>
            <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">
              <tr>
                <th width="100">%s</th>
                <td>%s</td>
              </tr>
              <tr>
                <th width="100">%s</th>
                <td>%s</td>
              </tr>
              <tr>
                <th width="100">%s</th>
                <td>%s</td>
              </tr>
              <tr>
                <th width="100">%s</th>
                <td>%s</td>
              </tr>
              <tr>
                <th width="100">%s</th>
                <td>%s</td>
              </tr>
              <tr>
                <th width="100">%s</th>
                <td>%s</td>
               </tr>
            </table>
            """% (CFG_SITE_URL,
                  borrower_id,
                  request_id,
                  _("Personal details"),
                  id_string, display_id,
                  _("Name"), name,
                  _("Address"), address,
                  _("Mailbox"), mailbox,
                  _("Email"), email,
                  _("Phone"), phone)

        out += """
        <br />
        <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">
            <tr>
                <th>%s</th>
            </tr>
            <tr>
                <td>%s</td>
            </tr>
            <tr algin='center'>
                <td>
                    <img style='border: 1px solid #cfcfcf' src="%s" alt="Book Cover"/>
                </td>
            </tr>
            <tr>
                <th>%s</th>
            </tr>
            <tr>
                <td>
                    <input type="text" size="66" name="barcode"
                           style='border: 1px solid #cfcfcf'>
                </td>
            </tr>
        </table>

        """ % (_("Item"),
               book_title,
               str(book_cover),
               _("Barcode"))

        out += """
              <br />
              <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">
                <tr>
                  <th>%s</th>
                </tr>
                <tr>
                  <td>
                    <textarea name='new_note' rows="4" cols="57"
                              style='border: 1px solid #cfcfcf'></textarea>
                  </td>
                </tr>
              </table>
              <br />
              """ % (_("Write notes"))

        out += """
        <table class="bibcirctable">
          <tr>
            <td>
              <input type=button value="%s" onClick="history.go(-1)" class="bibcircbutton"
                onmouseover="this.className='bibcircbuttonover'"
                onmouseout="this.className='bibcircbutton'">
              <input type="submit" value="%s" class="bibcircbutton"
                onmouseover="this.className='bibcircbuttonover'"
                onmouseout="this.className='bibcircbutton'">
            </td>
          </tr>
        </table>
        <br />
        <br />
        <br />
        </div>
        </form>
        """ % (_("Back"),
               _("Confirm"))

        return out


    ###
    ### "Borrower" related templates
    ###


    def tmpl_borrower_details(self, borrower, requests, loans, notes,
                              ill, proposals, req_hist, loans_hist, ill_hist,
                              proposal_hist, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = load_menu(ln)

        (borrower_id, ccid, name, email, phone, address, mailbox) = borrower

        display_id = borrower_id
        id_string = _("ID")
        if CFG_CERN_SITE == 1:
            display_id = ccid
            id_string = _("CCID")

        no_notes_link = create_html_link(CFG_SITE_URL +
                                    '/admin2/bibcirculation/get_borrower_notes',
                                    {'borrower_id': borrower_id},
                                    (_("No notes")))

        see_notes_link = create_html_link(CFG_SITE_URL +
                                    '/admin2/bibcirculation/get_borrower_notes',
                                    {'borrower_id': borrower_id},
                                    (_("Notes about this borrower")))

        if notes == "" or str(notes) == '{}':
            check_notes = no_notes_link
        else:
            check_notes = see_notes_link


        out += """
            <style type="text/css"> @import url("/css/tablesorter.css"); </style>
            <div class="bibcircbottom">

            <br />
            <table class="bibcirctable">
                 <tr>
                      <td class="bibcirctableheader">%s</td>
                 </tr>
             </table>
            </form>
            <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">
              <tr>
                <th width="100">%s</th>
                <td>%s</td>
              </tr>
              <tr>
                <th width="100">%s</th>
                <td>%s</td>
              </tr>
              <tr>
                <th width="100">%s</th>
                <td>%s</td>
              </tr>
              <tr>
                <th width="100">%s</th>
                <td>%s</td>
              </tr>
              <tr>
                <th width="100">%s</th>
                <td>%s</td>
              </tr>
              <tr>
                <th width="100">%s</th>
                <td>%s</td>
               </tr>
               <tr>
                 <th width="100">%s</th>
                 <td>%s</td>
               </tr>

            """ % (_("Personal details"),
                   id_string, display_id,
                   _("Name"), name,
                   _("Address"), address,
                   _("Mailbox"), mailbox,
                   _("Email"), email,
                   _("Phone"), phone,
                   _("Notes"), check_notes)

        nb_requests = len(requests)
        nb_loans = len(loans)
        nb_ill = len(ill)
        nb_proposals = len(proposals)
        nb_req_hist = len(req_hist)
        nb_loans_hist = len(loans_hist)
        nb_ill_hist = len(ill_hist)
        nb_proposal_hist = len(proposal_hist)

        out += """
        </table>
        <br />
        <table class="bibcirctable">
          <tr>
            <td>
            <input type=button
                onClick="location.href='%s/admin2/bibcirculation/loan_on_desk_step2?ln=%s&user_id=%s'"
                value='%s' class='formbutton'>

            <input type=button
    onClick="location.href='%s/admin2/bibcirculation/create_new_request_step1?ln=%s&borrower_id=%s'"
                value='%s' class='formbutton'>

            <input type=button
    onClick="location.href='%s/admin2/bibcirculation/register_ill_book_request?ln=%s&borrower_id=%s'"
                value='%s' class='formbutton'>

            <input type=button
    onClick="location.href='%s/admin2/bibcirculation/borrower_notification?ln=%s&borrower_id=%s&from_address=%s'"
                value='%s' class='formbutton'>
        """ % (CFG_SITE_URL, ln, borrower_id, _("New loan"),
               CFG_SITE_URL, ln, borrower_id, _("New request"),
               CFG_SITE_URL, ln, borrower_id, _("New ILL request"),
               CFG_SITE_URL, ln, borrower_id, CFG_BIBCIRCULATION_LOANS_EMAIL, _("Notify this borrower"))

        if CFG_CERN_SITE:
            out += """
            <input type=button onClick=
"location.href='%s/admin2/bibcirculation/get_borrower_details?ln=%s&borrower_id=%s&update=True'"
                value="%s" class='formbutton'>
            """ % (CFG_SITE_URL, ln, borrower_id, _("Update"))

        else:
            out += """
            <input type=button
    onClick=
       "location.href='%s/admin2/bibcirculation/update_borrower_info_step1?ln=%s&borrower_id=%s'"
                value="%s" class='formbutton'>
            """ % (CFG_SITE_URL, ln, borrower_id, _("Update"))

        out += """
            </td>

          </tr>
        </table>
        <br />
        <table class="bibcirctable">
          <tr>
            <td class="bibcirctableheader">%s %s</td>
          </tr>
        </table>
        <table class="tablesortersmall" border="0" cellpadding="0" cellspacing="1">
          <tr>
            <th width="100">%s</th>
            <td width="50">%s</td>
            <td>
              <input type="button"
              onClick="location.href='%s/admin2/bibcirculation/get_borrower_requests_details?ln=%s&borrower_id=%s'"
              onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
              value='%s' class="bibcircbutton">
            </td>
          </tr>
          <tr>
            <th width="100">%s</th>
            <td width="50">%s</td>
            <td>
              <input type="button"
              onClick="location.href='%s/admin2/bibcirculation/get_borrower_loans_details?ln=%s&borrower_id=%s'"
              onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
              value='%s' class="bibcircbutton">
            </td>
          </tr>
          <tr>
            <th width="100">%s</th>
            <td width="50">%s</td>
            <td>
              <input type="button"
              onClick="location.href='%s/admin2/bibcirculation/get_borrower_ill_details?ln=%s&borrower_id=%s'"
              onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
              value='%s' class="bibcircbutton">
            </td>
          </tr>
          <tr>
            <th width="100">%s</th>
            <td width="50">%s</td>
            <td>
              <input type="button"
              onClick="location.href='%s/admin2/bibcirculation/get_borrower_ill_details?ln=%s&borrower_id=%s&request_type=%s'"
              onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
              value='%s' class="bibcircbutton">
            </td>
          </tr>
        </table>
        <br />
        <table class="bibcirctable">
          <tr>
            <td class="bibcirctableheader">%s</td>
          </tr>
        </table>
        <table class="tablesortersmall" border="0" cellpadding="0" cellspacing="1">
          <tr>
            <th width="100">%s</th>
            <td width="50">%s</td>
            <td>
              <input type="button"
              onClick="location.href='%s/admin2/bibcirculation/bor_requests_historical_overview?ln=%s&borrower_id=%s'"
              onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
              value='%s' class="bibcircbutton">
            </td>
          </tr>
          <tr>
            <th width="100">%s</th>
            <td width="50">%s</td>
            <td>
              <input type="button"
              onClick="location.href='%s/admin2/bibcirculation/bor_loans_historical_overview?ln=%s&borrower_id=%s'"
              onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
              value='%s' class="bibcircbutton">
            </td>
          </tr>
          <tr>
            <th width="100">%s</th>
            <td width="50">%s</td>
            <td>
              <input type="button"
              onClick="location.href='%s/admin2/bibcirculation/bor_ill_historical_overview?ln=%s&borrower_id=%s'"
              onmouseover="this.className='bibcircbuttonover'"
              onmouseout="this.className='bibcircbutton'"
              value='%s' class="bibcircbutton">
            </td>
          </tr>
          <tr>
            <th width="100">%s</th>
            <td width="50">%s</td>
            <td>
              <input type="button"
              onClick="location.href='%s/admin2/bibcirculation/bor_ill_historical_overview?ln=%s&borrower_id=%s&request_type=%s'"
              onmouseover="this.className='bibcircbuttonover'"
              onmouseout="this.className='bibcircbutton'"
              value='%s' class="bibcircbutton">
            </td>
          </tr>
        </table>
        <br />
        <table class="bibcirctable">
          <tr>
            <td><input type=button value='%s'
                 onClick="history.go(-1)" class="formbutton"></td>
          </tr>
        </table>
        <br />
        </div>
        """ % (_("Requests, Loans and ILL overview on"),
               dateutils.convert_datestruct_to_datetext(localtime()),
               _("Requests"), nb_requests, CFG_SITE_URL, ln, borrower_id,
               _("More details"),
               _("Loans"), nb_loans, CFG_SITE_URL, ln, borrower_id,
               _("More details"),
               _("ILL"), nb_ill, CFG_SITE_URL, ln, borrower_id,
               _("More details"),
               _("Proposals"), nb_proposals, CFG_SITE_URL, ln, borrower_id, 'proposal-book',
               _("More details"),
               _("Historical overview"),
               _("Requests"), nb_req_hist, CFG_SITE_URL, ln, borrower_id,
               _("More details"),
               _("Loans"), nb_loans_hist, CFG_SITE_URL, ln, borrower_id,
               _("More details"),
               _("ILL"), nb_ill_hist, CFG_SITE_URL, ln, borrower_id,
               _("More details"),
               _("Proposals"), nb_proposal_hist, CFG_SITE_URL, ln, borrower_id, 'proposal-book',
               _("More details"),
               _("Back"))


        return out

    def tmpl_borrower_request_details(self, result, borrower_id,
                                      ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        out = """
        """
        out += load_menu(ln)

        if len(result) == 0:
            out += """
            <div class="bibcircbottom">
            <br />
            <div class="bibcircinfoboxmsg">%s</div>
            <br />
          """ % (_("There are no requests."))

        else:
            out += """
         <style type="text/css"> @import url("/css/tablesorter.css"); </style>
         <script src="/%s" type="text/javascript"></script>
         <script type="text/javascript">
           $(document).ready(function() {
             $('#table_requests').tablesorter({widthFixed: true, widgets: ['zebra']})
           });
         </script>
        <form name="borrower_form" action="%s/admin2/bibcirculation/get_borrower_requests_details" method="get" >
        <div class="bibcircbottom">
        <br />
             <table id="table_requests" class="tablesorter" border="0" cellpadding="0" cellspacing="1">
               <thead>
                    <tr>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                   </tr>
              </thead>
              <tbody>
        </form>
         """% (JQUERY_TABLESORTER,
               CFG_SITE_URL,
               _("Item"),
               _("Request status"),
               _("Library"),
               _("Location"),
               _("From"),
               _("To"),
               _("Request date"),
               _("Request option(s)"))

            for (recid, status, library, location, date_from,
                 date_to, request_date, request_id) in result:

                title_link = create_html_link(CFG_SITE_URL +
                                    '/admin2/bibcirculation/get_item_details',
                                    {'recid': recid, 'ln': ln},
                                    (book_title_from_MARC(recid)))

                out += """
            <tr>
                 <td>%s</td>
                 <td>%s</td>
                 <td>%s</td>
                 <td>%s</td>
                 <td>%s</td>
                 <td>%s</td>
                 <td>%s</td>
                 <td align="center">
                 <input type="button" value='%s' style="background: url(/img/dialog-cancel.png)
                 no-repeat #8DBDD8; width: 75px; text-align: right;"
    onClick="location.href='%s/admin2/bibcirculation/get_pending_requests?ln=%s&request_id=%s'"
                 onmouseover="this.className='bibcircbuttonover'"
                 onmouseout="this.className='bibcircbutton'"
                 class="bibcircbutton">
                 </td>
            </tr>

            """ % (title_link, status, library, location, date_from,
                   date_to, request_date, _("Cancel"),
                   CFG_SITE_URL, ln, request_id)


        out += """
        </tbody>
        </table>
        <br />
        <table class="bibcirctable">
             <tr>
                  <td>
                    <input type=button onClick="location.href='%s/admin2/bibcirculation/get_borrower_details?ln=%s&borrower_id=%s'"
                    value='%s' class='formbutton'>
                  </td>
             </tr>
        </table>
        <br />
        </div>
        """ % (CFG_SITE_URL, ln,
               borrower_id,
               _("Back"))

        return out

    def tmpl_borrower_loans_details(self, borrower_loans, borrower_id, infos,
                                    ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += load_menu(ln)

        if len(borrower_loans) == 0:
            out += """
            <div class="bibcircbottom">
            <br />
            <div class="bibcircinfoboxmsg">%s</div>
            <br />
          """ % (_("There are no loans."))

        else:
            out += """
        <form name="borrower_form" action="%s/admin2/bibcirculation/get_borrower_loans_details?submit_changes=true" method="get" >
        <input type=hidden name=borrower_id value="%s">
        <div class="bibcircbottom">

        <style type="text/css"> @import url("/css/tablesorter.css"); </style>
        <script src="/%s" type="text/javascript"></script>
        <script type="text/javascript">
        $(document).ready(function() {
          $('#table_loans').tablesorter({widthFixed: true, widgets: ['zebra']})
        });
        </script>

        <br />
             <table id="table_loans" class="tablesorter" border="0" cellpadding="0" cellspacing="1">
             <thead>
               <tr>
                 <th>%s</th>
                 <th>%s</th>
                 <th>%s</th>
                 <th>%s</th>
                 <th>%s</th>
                 <th>%s</th>
                 <th>%s</th>
                 <th>%s</th>
                 <th>%s</th>
                 <th>%s</th>
               </tr>
             </thead>
             <tbody>

         """% (JQUERY_TABLESORTER,
               CFG_SITE_URL,
               borrower_id,
               _("Item"),
               _("Barcode"),
               _("Loan date"),
               _("Due date"),
               _("Renewals"),
               _("Overdue letters"),
               _("Type"),
               _("Loan notes"),
               _("Loans status"),
               _("Loan options"))


            for (recid, barcode, loaned_on, due_date, nb_renewal,
                 nb_overdue, date_overdue, loan_type, notes,
                 loan_id, status) in borrower_loans:

                title_link = create_html_link(CFG_SITE_URL +
                                    '/admin2/bibcirculation/get_item_details',
                                    {'recid': recid, 'ln': ln},
                                    (book_title_from_MARC(recid)))

                no_notes_link = create_html_link(CFG_SITE_URL +
                                    '/admin2/bibcirculation/get_loans_notes',
                                    {'loan_id': loan_id, 'ln': ln},
                                    (_("No notes")))

                see_notes_link = create_html_link(CFG_SITE_URL +
                                    '/admin2/bibcirculation/get_loans_notes',
                                    {'loan_id': loan_id, 'ln': ln},
                                    (_("See notes")))

                if notes == "" or str(notes) == '{}':
                    check_notes = no_notes_link
                else:
                    check_notes = see_notes_link


                out += """
            <tr>
              <td>%s</td>
              <td>%s</td>
              <td>%s</td>
              <td>%s</td>
              <td>%s</td>
              <td>%s - %s</td>
              <td>%s</td>
              <td>%s</td>
              <td>%s</td>
              """ % (title_link, barcode, loaned_on, due_date, nb_renewal,
                     nb_overdue, date_overdue, loan_type, check_notes, status)

                out += """
              <td align="center">
                <SELECT style='border: 1px solid #cfcfcf'
                        ONCHANGE="location = this.options[this.selectedIndex].value;">
        <OPTION VALUE="">%s
        <OPTION
            VALUE="get_borrower_loans_details?borrower_id=%s&barcode=%s&loan_id=%s&recid=%s">%s
                  <OPTION VALUE="loan_return_confirm?barcode=%s">%s
                """ % (_("Select an action"),
                       borrower_id, barcode, loan_id, recid, _("Renew"),
                       barcode, _("Return"))

                if status == CFG_BIBCIRCULATION_LOAN_STATUS_EXPIRED:
                    out += """
        <OPTION VALUE="change_due_date_step1?barcode=%s&borrower_id=%s" DISABLED>%s
                  """ % (barcode, borrower_id, _("Change due date"))
                else:
                    out += """
        <OPTION VALUE="change_due_date_step1?barcode=%s&borrower_id=%s">%s
                  """ % (barcode, borrower_id, _("Change due date"))

                out += """
                <OPTION VALUE="claim_book_return?borrower_id=%s&recid=%s&loan_id=%s&template=claim_return">%s
                </SELECT>
              </td>
                <input type=hidden name=barcode value="%s">
                <input type=hidden name=loan_id value="%s">
            </tr>
            """ % (borrower_id, recid, loan_id, _("Send recall"),
                   barcode, loan_id)

            out += """
        </tbody>
        </table>
        <br />
        <table class="bibcirctable">
          <tr>
            <td class="bibcirccontent" align="right" width="100">
              <input type=button onClick="location.href='%s/admin2/bibcirculation/get_borrower_loans_details?ln=%s&borrower_id=%s&renewal=true'"
              value='%s' class='bibcircbutton'onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"></td>
          </tr>
        </table>
        """ % (CFG_SITE_URL, ln,
               borrower_id,
               _("Renew all loans"))

        out += """
        <table class="bibcirctable">
          <tr>
            <td>
              <input type=button
    onClick="location.href='%s/admin2/bibcirculation/get_borrower_details?ln=%s&borrower_id=%s'"
              value='%s' class='formbutton'></td>
          </tr>
        </table>
        <br />
        </div>
        </form>

        """ % (CFG_SITE_URL, ln,
               borrower_id,
               _("Back"))


        return out

    def tmpl_bor_requests_historical_overview(self, req_hist_overview,
                                              ln=CFG_SITE_LANG):
        """
        Return the historical requests overview of a borrower.

        @param req_hist_overview: list of old requests.
        """

        _ = gettext_set_language(ln)

        out = load_menu(ln)

        if len(req_hist_overview) == 0:
            out += """
            <div class="bibcircbottom">
            <br />
            <div class="bibcircinfoboxmsg">%s</div>
            <br />
          """ % (_("There are no requests."))

        else:
            out += """<div class="bibcircbottom">
                    <br /> <br />
                    <style type="text/css"> @import url("/css/tablesorter.css"); </style>
                    <script src="/%s" type="text/javascript"></script>
                    <script type="text/javascript">
                      $(document).ready(function() {
                        $('#table_requests').tablesorter({widthFixed: true, widgets: ['zebra']})
                      });
                    </script>
                    <table id="table_requests" class="tablesorter"
                           border="0" cellpadding="0" cellspacing="1">
                    <thead>
                     <tr>
                     <th>%s</th>
                     <th>%s</th>
                     <th>%s</th>
                     <th>%s</th>
                     <th>%s</th>
                     <th>%s</th>
                     <th>%s</th>
                     </tr>
                    <thead>
                    <tbody>
                    """ % (JQUERY_TABLESORTER,
                           _("Item"), _("Barcode"), _("Library"),
                           _("Location"), _("From"),
                           _("To"), _("Request date"))

            for (recid, barcode, library_name,
                 location, req_from, req_to, req_date) in req_hist_overview:

                title_link = create_html_link(CFG_SITE_URL +
                                    '/admin2/bibcirculation/get_item_details',
                                    {'recid': recid, 'ln': ln},
                                    (book_title_from_MARC(recid)))

                out += """ <tr>
                            <td>%s</td>
                            <td>%s</td>
                            <td>%s</td>
                            <td>%s</td>
                            <td>%s</td>
                            <td>%s</td>
                            <td>%s</td>
                           </tr>
                 """ % (title_link, barcode, library_name, location, req_from,
                        req_to, req_date)

        out += """
           </tbody>
           </table>
           <br />
           """
        out += """
           <table class="bibcirctable">
                <tr>
                     <td><input type=button value='%s'
                          onClick="history.go(-1)" class="formbutton"></td>
                </tr>
           </table>
           <br />
           <br />
           <br />
           </div>

           """ % (_("Back"))

        return out

    def tmpl_bor_loans_historical_overview(self, loans_hist_overview,
                                           ln=CFG_SITE_LANG):
        """
        Return the historical loans overview of a borrower.

        @param loans_hist_overview: list of old loans.
        """

        _ = gettext_set_language(ln)

        out = load_menu(ln)

        if len(loans_hist_overview) == 0:
            out += """
            <div class="bibcircbottom">
            <br />
            <div class="bibcircinfoboxmsg">%s</div>
            <br />
            """ % (_("There are no loans."))

        else:
            out += """<div class="bibcircbottom">
                      <style type="text/css"> @import url("/css/tablesorter.css"); </style>
                      <script src="/%s" type="text/javascript"></script>
                      <script type="text/javascript">
                        $(document).ready(function() {
                          $('#table_loans').tablesorter({widthFixed: true, widgets: ['zebra']})
                        });
                      </script>
                    <br /> <br />
                    <table id="table_loans" class="tablesorter"
                           border="0" cellpadding="0" cellspacing="1">
                    <thead>
                     <tr>
                     <th>%s</th>
                     <th>%s</th>
                     <th>%s</th>
                     <th>%s</th>
                     <th>%s</th>
                     <th>%s</th>
                     <th>%s</th>
                     <th>%s</th>
                     <th>%s</th>
                     </tr>
                   </thead>
                   <tbody>
                     """ % (JQUERY_TABLESORTER,
                            _("Item"),
                            _("Barcode"),
                            _("Library"),
                            _("Location"),
                            _("Loaned on"),
                            _("Due date"),
                            _("Returned on"),
                            _("Renewals"),
                            _("Overdue letters"))

            recid = '-'
            barcode = '-'
            library_name = '-'
            location = '-'
            loaned_on = '-'
            due_date = '-'
            returned_on = '-'
            nb_renew = '-'
            nb_overdueletters = '-'

            for (recid, barcode, library_name, location, loaned_on, due_date,
                 returned_on, nb_renew,
                 nb_overdueletters) in loans_hist_overview:

                title_link = create_html_link(CFG_SITE_URL +
                                    '/admin2/bibcirculation/get_item_details',
                                    {'recid': recid, 'ln': ln},
                                    (book_title_from_MARC(recid)))

                out += """ <tr>
                           <td>%s</td>
                           <td>%s</td>
                           <td>%s</td>
                           <td>%s</td>
                           <td>%s</td>
                           <td>%s</td>
                           <td>%s</td>
                           <td>%s</td>
                           <td>%s</td>
                           </tr>
                     """ % (title_link, barcode,
                            library_name, location,
                            loaned_on, due_date,
                            returned_on, nb_renew,
                            nb_overdueletters)

        out += """
            </table>
            <br />
            <table class="bibcirctable">
                <tr>
                    <td>
                        <input type=button value='%s'
                               onClick="history.go(-1)" class="formbutton">
                    </td>
                </tr>
           </table>
           <br />
           <br />
           <br />
           </div>

           """ % (_("Back"))

        return out

    def tmpl_borrower_notification(self, email, subject, email_body, borrower_id,
                                   from_address, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        if subject is None:
            subject = ""

        _ = gettext_set_language(ln)

        out = load_menu(ln)

        out += """
        <style type="text/css"> @import url("/css/tablesorter.css"); </style>
        <form name="borrower_notification"
              action="%s/admin2/bibcirculation/borrower_notification"
              method="get" >
            <div class="bibcircbottom">
            <input type=hidden name=borrower_id value="%s">
            <input type=hidden name=from_address value="%s">
            <br />
            <table class="tablesortermedium" border="0" cellpadding="0" cellspacing="1">
                <tr>
                    <th width="50">%s</th>
                    <td>%s</td>
                </tr>
                <tr>
                    <th width="50">%s</th>
                    <td>%s</td>
                </tr>
        """ % (CFG_SITE_URL,
               borrower_id,
               from_address,
               _("From"),
               _("CERN Library"),
               _("To"),
               email)

        out += """
            <tr>
                <th width="50">%s</th>
                <td>
                    <input type="text" name="subject" size="60"
                           value="%s" style='border: 1px solid #cfcfcf'>
                </td>
            </tr>
        </table>

        <br />

        <table class="tablesortermedium" border="0" cellpadding="0" cellspacing="1">
            <tr>
                <th width="500">%s</th>
                <th>%s</th>
            </tr>
            <tr>
                <td>
                    <textarea rows="10" cols="100" name="message"
                              style='border: 1px solid #cfcfcf'>%s</textarea>
                </td>
        """ % (_("Subject"),
               subject,
               _("Message"),
               _("Choose a template"),
               email_body)

        out += """
               <td>
                    <select name="template" style='border: 1px solid #cfcfcf'>
                         <option value ="">%s</option>
                         <option value ="overdue_letter">%s</option>
                         <option value ="reminder">%s</option>
                         <option value ="notification">%s</option>
                         <option value ="claim_return">%s</option>
                         <option value ="ill_recall1">%s</option>
                         <option value ="proposal_acceptance">%s</option>
                         <option value ="proposal_refusal">%s</option>
                         <option value ="purchase_received_cash">%s</option>
                         <option value ="purchase_received_tid">%s</option>
                    </select>
                    <br />
                    <br />
                    <button type="submit" name="load_msg_template" value="True" class="formbutton">%s</button>
               </td>
               </tr>
        </table>
        """ % (_("Templates"),
               _("Overdue letter"),
               _("Reminder"),
               _("Notification"),
               _("Loan recall"),
               _("ILL recall"),
               _("Proposal-accept"),
               _("Proposal-refuse"),
               _("Purchase-received-cash"),
               _("Purchase-received-TID"),
               _("Load"))

        out += """
        <br /> <br />
        <table class="bibcirctable">
               <tr>
                    <td>
                       <input type=button value="%s" onClick="history.go(-1)" class="formbutton">
                       <input type="reset" name="reset_button" value="%s" class="formbutton">
                       <input type="submit" name="send_message" value="%s" class="formbutton">
                    </td>
               </tr>
        </table>
        <br /> <br />
        </div>
        </form>
        """ % (_("Back"),
               _("Reset"),
               _("Send"))


        return out


    def tmpl_borrower_notes(self, borrower_notes, borrower_id,
                            ln=CFG_SITE_LANG):

        _ = gettext_set_language(ln)

        if not borrower_notes:
            borrower_notes = {}
        else:
            if looks_like_dictionary(borrower_notes):
                borrower_notes = eval(borrower_notes)
            else:
                borrower_notes = {}

        out = """ """

        out += load_menu(ln)

        out += """
            <div class="bibcircbottom">
            <form name="borrower_notes"
                  action="%s/admin2/bibcirculation/get_borrower_notes"
                  method="post" >
            <input type=hidden name=borrower_id value='%s'>
            <br />
            <br />
            <table class="bibcirctable">
              <tr>
                <td class="bibcirctableheader">%s</td>
              </tr>
            </table>
            <table class="bibcirctable">
              <tr>
                <td>
                  <table class="bibcircnotes">

            """ % (CFG_SITE_URL, borrower_id,
                   _("Notes about borrower"))

        key_array = borrower_notes.keys()
        key_array.sort()

        for key in key_array:
            delete_note = create_html_link(CFG_SITE_URL +
                            '/admin2/bibcirculation/get_borrower_notes',
                            {'delete_key': key, 'borrower_id': borrower_id,
                             'ln': ln}, (_("[delete]")))

            out += """<tr class="bibcirccontent">
                        <td class="bibcircnotes" width="160"
                            valign="top" align="center"><b>%s</b></td>
                        <td width="400"><i>%s</i></td>
                        <td width="65" align="center">%s</td>
                      </tr>

                      """ % (key, borrower_notes[key], delete_note)

        out += """
                  </table>
                </td>
              </tr>
            </table>
            <br />
            <table class="bibcirctable">
              <tr>
                <td class="bibcirctableheader">%s</td>
              </tr>
            </table>
            <table class="bibcirctable">
              <tr>
                <td class="bibcirccontent">
                  <textarea name="library_notes" rows="5" cols="90"
                            style='border: 1px solid #cfcfcf'></textarea>
                </td>
              </tr>
            </table>
            <br />
            <table class="bibcirctable">
              <tr>
                <td>
                  <input type=button
    onClick="location.href='%s/admin2/bibcirculation/get_borrower_details?ln=%s&borrower_id=%s'"
                  value="%s" class='formbutton'>
                  <input type="submit" value='%s' class="formbutton">
                </td>
              </tr>
             </table>
             <br />
             <br />
             <br />
             </form>
             </div>
        """ % (_("Write new note"),
               CFG_SITE_URL, ln,
               borrower_id,
               _("Back"),
               _("Confirm"))

        return out

    def tmpl_add_new_borrower_step1(self, tup_infos=None, infos=None, ln=CFG_SITE_LANG):

        _ = gettext_set_language(ln)

        if tup_infos:
            (name, email, phone, address, mailbox, notes) = tup_infos
        else:
            (name, email, phone, address, mailbox, notes) = ('', '', '', '', '', '')

        out = ''

        if infos:
            out += self.tmpl_infobox(infos, ln)

        out += load_menu(ln)

        out += """
            <div class="bibcircbottom">
            <form name="add_new_borrower_step1_form"
                  action="%s/admin2/bibcirculation/add_new_borrower_step2"
                  method="get">
              <br />
              <br />
              <table class="bibcirctable">
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf'
                             size=45 name="name" value="%s">
                    </td>
                </tr>
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf'
                             size=45 name="email" value="%s">
                    </td>
                </tr>
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf'
                             size=45 name="phone" value="%s">
                    </td>
                </tr>
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf'
                             size=45 name="address" value="%s">
                    </td>
                 </tr>
                  <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf'
                             size=45 name="mailbox" value="%s">
                    </td>
                 </tr>
                 <tr>
                    <td width="70" valign="top">%s</td>
                    <td class="bibcirccontent">
                        <textarea name="notes" rows="5" cols="39"
                                style='border: 1px solid #cfcfcf'>%s</textarea>
                    </td>
                 </tr>
                </table>
                <br />
                <table class="bibcirctable">
                <tr>
                  <td>
                       <input type=button value="%s" class="formbutton"
                              onClick="history.go(-1)">
                       <input type="submit" value="%s" class="formbutton">
                  </td>
                 </tr>
                </table>
                <br />
                <br />
                </form>
                </div>
                """ % (CFG_SITE_URL,
                       _("Name"), name,
                       _("Email"), email,
                       _("Phone"), phone,
                       _("Address"), address,
                       _("Mailbox"), mailbox,
                       _("Notes"), notes,
                       _("Back"), _("Continue"))

        return out

    def tmpl_add_new_borrower_step2(self, tup_infos, infos, ln=CFG_SITE_LANG):

        _ = gettext_set_language(ln)

        (name, email, phone, address, mailbox, notes) = tup_infos

        out = self.tmpl_infobox(infos, ln)

        out += load_menu(ln)

        out += """
            <div class="bibcircbottom">
            <form name="add_new_borrower_step2_form"
                  action="%s/admin2/bibcirculation/add_new_borrower_step3"
                  method="post" >
              <br />
              <br />
              <table class="bibcirctable">
                <tr>
                    <td width="70">%s</td> <td class="bibcirccontent">%s</td>
                </tr>
                <tr>
                    <td width="70">%s</td> <td class="bibcirccontent">%s</td>
                </tr>
                <tr>
                    <td width="70">%s</td> <td class="bibcirccontent">%s</td>
                </tr>
                <tr>
                    <td width="70">%s</td> <td class="bibcirccontent">%s</td>
                 </tr>
                 <tr>
                    <td width="70">%s</td> <td class="bibcirccontent">%s</td>
                 </tr>
                 <tr>
                    <td width="70">%s</td> <td class="bibcirccontent">%s</td>
                 </tr>
                </table>

                """ % (CFG_SITE_URL,
                       _("Name"), name,
                       _("Email"), email,
                       _("Phone"), phone,
                       _("Address"), address,
                       _("Mailbox"), mailbox,
                       _("Notes"), notes)


        if infos:
            out += """
                    <br />
                    <table class="bibcirctable">
                      <tr>
                        <td>
                         <input type=button value="%s"
                                onClick="history.go(-1)"
                                class="formbutton">
                       </td>
                     </tr>
                    </table>
                    <br />
                    <br />
                    </form>
                    </div>
                """ % (_("Back"))

        else:
            out += """
                    <br />
                    <table class="bibcirctable">
                      <tr>
                        <td>
                         <input type=button value="%s"
                                onClick="history.go(-1)"
                                class="formbutton">
                         <input type="submit" value="%s" class="formbutton">
                         <input type=hidden name=tup_infos value="%s">
                       </td>
                     </tr>
                   </table>
                   <br />
                   <br />
                   </form>
                   </div>
                   """ % (_("Back"), _("Continue"), tup_infos)

        return out

    def tmpl_add_new_borrower_step3(self, ln=CFG_SITE_LANG):

        _ = gettext_set_language(ln)

        out = """ """

        out += load_menu(ln)

        out += """
            <div class="bibcircbottom">
              <br />
              <br />
              <table class="bibcirctable">
                <tr>
                    <td class="bibcirccontent">%s</td>
                </tr>
                </table>
                <br />
                <table class="bibcirctable">
                <tr>
                  <td>
                       <input type=button value="%s"
                    onClick="location.href='%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s'"
                            class="formbutton">
                  </td>
                 </tr>
                </table>
                <br />
                <br />
                </div>
                """ % (_("A new borrower has been registered."),
                       _("Back to home"),
                       CFG_SITE_URL, ln)

        return out

    def tmpl_update_borrower_info_step1(self, tup_infos, infos=None,
                                        ln=CFG_SITE_LANG):

        _ = gettext_set_language(ln)

        (borrower_id, name, email, phone, address, mailbox) = tup_infos

        display_id = borrower_id
        id_string = _("ID")

        out = ''

        if infos:
            out += self.tmpl_infobox(infos, ln)

        out += load_menu(ln)

        out += """
            <div class="bibcircbottom">
            <form name="update_borrower_info_step1_form"
                  action="%s/admin2/bibcirculation/update_borrower_info_step2"
                  method="get" >
              <br />
              <br />
              <table class="bibcirctable">
                <tr>
                    <td class="bibcirctableheader">%s</td>
                </tr>
              </table>
              <table class="bibcirctable">
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">%s</td>
                </tr>
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">
                        <input type="text" style='border: 1px solid #cfcfcf'
                                size=45 name="name" value="%s">
                    </td>
                </tr>
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">
                        <input type="text" style='border: 1px solid #cfcfcf'
                                size=45 name="address" value="%s">
                    </td>
                 </tr>
                 <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">
                        <input type="text" style='border: 1px solid #cfcfcf'
                                size=45 name="mailbox" value="%s">
                    </td>
                 </tr>
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">
                        <input type="text" style='border: 1px solid #cfcfcf'
                                size=45 name="email" value="%s">
                    </td>
                </tr>
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">
                        <input type="text" style='border: 1px solid #cfcfcf'
                                size=45 name="phone" value="%s">
                        <input type=hidden name=borrower_id value="%s">
                    </td>
                </tr>

                </table>
                <br />
                <table class="bibcirctable">
                <tr>
                    <td>
                        <input type=button value="%s" onClick="history.go(-1)"
                               class="formbutton">
                        <input type="submit" value='%s' class="formbutton">
                    </td>
                </tr>
                </table>
                <br />
                <br />
                </form>
                </div>
                """ % (CFG_SITE_URL, _("Borrower information"),
                       id_string, display_id,
                       _("Name"), name,
                       _("Address"), address,
                       _("Mailbox"), mailbox,
                       _("Email"), email,
                       _("Phone"), phone,
                       borrower_id,
                       _("Back"), _("Continue"))


        return out


    ###
    ### ILL/Purchase/Acquisition related templates.
    ### Naming of the methods is not intuitive. Should be improved
    ### and appropriate documentation added, when required.
    ### Also, methods could be refactored.
    ###


    def tmpl_borrower_ill_details(self, result, borrower_id,
                                  ln=CFG_SITE_LANG):
        """
        @param result: ILL request's information
        @type result: list

        @param borrower_id: identify the borrower. Primary key of crcBORROWER.
        @type borrower_id: int

        @param ill_id: identify the ILL request. Primray key of crcILLREQUEST
        @type ill_id: int

        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        out = load_menu(ln)

        out += """
        <style type="text/css"> @import url("/css/tablesorter.css"); </style>
        <script src="/%s" type="text/javascript"></script>
        <script type="text/javascript">
        $(document).ready(function() {
          $('#table_ill').tablesorter({widthFixed: true, widgets: ['zebra']})
        });
        </script>
        <div class="bibcircbottom">
        <br />
        <table id="table_ill" class="tablesorter" border="0"
               cellpadding="0" cellspacing="1">
        <thead>
          <tr>
            <th>%s</th>
            <th>%s</th>
            <th>%s</th>
            <th>%s</th>
            <th>%s</th>
            <th>%s</th>
            <th>%s</th>
            <th>%s</th>
            <th>%s</th>
          </tr>
        </thead>
        <tbody>
         """ % (JQUERY_TABLESORTER,
                _("ILL ID"),
                _("Item"),
                _("Supplier"),
                _("Request date"),
                _("Expected date"),
                _("Arrival date"),
                _("Due date"),
                _("Status"),
                _("Library notes"))

        for (ill_id, book_info, supplier_id, request_date,
             expected_date, arrival_date, due_date, status,
             library_notes, request_type) in result:

            #get supplier name
            if supplier_id:
                if request_type in CFG_BIBCIRCULATION_ACQ_TYPE or \
                   request_type in CFG_BIBCIRCULATION_PROPOSAL_TYPE:
                    library_name = db.get_vendor_name(supplier_id)
                    library_link = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/get_vendor_details',
                                {'vendor_id': supplier_id, 'ln': ln},
                                (library_name))
                else:
                    library_name = db.get_library_name(supplier_id)
                    library_link = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/get_library_details',
                                {'library_id': supplier_id, 'ln': ln},
                                (library_name))
            else:
                library_link = '-'

            #get book title
            if looks_like_dictionary(book_info):
                book_info = eval(book_info)
            else:
                book_info = {}

            try:
                title_link = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/get_item_details',
                                {'recid': book_info['recid'], 'ln': ln},
                                (book_title_from_MARC(int(book_info['recid']))))
            except KeyError:
                title_link = book_info['title']

            if request_type in CFG_BIBCIRCULATION_ACQ_TYPE or \
               request_type in CFG_BIBCIRCULATION_PROPOSAL_TYPE:
                ill_id_link = create_html_link(CFG_SITE_URL +
                            '/admin2/bibcirculation/purchase_details_step1',
                            {'ill_request_id': str(ill_id), 'ln': ln},
                            str(ill_id))
            else:
                ill_id_link = create_html_link(CFG_SITE_URL +
                            '/admin2/bibcirculation/ill_request_details_step1',
                            {'ill_request_id': str(ill_id), 'ln': ln},
                            str(ill_id))

            # links to notes pages
            lib_no_notes_link = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/get_ill_library_notes',
                                {'ill_id': ill_id}, (_("No notes")))

            lib_see_notes_link = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/get_ill_library_notes',
                                {'ill_id': ill_id}, (_("Notes about this ILL")))

            if library_notes == "":
                notes_link = lib_no_notes_link
            else:
                notes_link = lib_see_notes_link

            out += """
            <tr>
              <td>%s</td>
              <td>%s</td>
              <td>%s</td>
              <td>%s</td>
              <td>%s</td>
              <td>%s</td>
              <td>%s</td>
              <td>%s</td>
              <td>%s</td>
            </tr>
            """ % (ill_id_link, title_link, library_link, request_date,
                   expected_date, arrival_date, due_date, status,
                   notes_link)

        out += """
        </tbody>
        </table>
        <br />
        <table class="bibcirctable">
          <tr>
            <td>
              <input type=button
    onClick="location.href='%s/admin2/bibcirculation/get_borrower_details?borrower_id=%s&ln=%s'"
              value='%s' class='formbutton'>
            </td>
          </tr>
        </table>
        <br />
        </div>
        """ % (CFG_SITE_URL,
               borrower_id, ln,
               _("Back"))

        return out

    def tmpl_ill_request_with_recid(self, recid, infos, ln=CFG_SITE_LANG):
        """
        @param recid: identify the record. Primary key of bibrec.
        @type recid: int

        @param infos: information
        @type infos: list
        """

        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        (book_title, book_year, book_author,
         book_isbn, book_editor) = book_information_from_MARC(recid)

        today = datetime.date.today()
        within_six_months = (datetime.date.today() + \
                             datetime.timedelta(days=182)).strftime('%Y-%m-%d')

        out += """
           <div align="center">
           <style type="text/css"> @import url("/css/tablesorter.css"); </style>
           <form name="update_item_info_step4_form" action="%s/record/%s/holdings/ill_register_request_with_recid" method="post" >
                <table class="bibcirctable">
                  <tr align="center">
                    <td><h1 class="headline">%s</h1></td>
                  </tr>
                </table>
                <table class="bibcirctable">
                  <tr align="center">
                    <td class="bibcirctableheader" width="10">%s</td>
                  </tr>
                </table>
                <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">
                <input type=hidden name=recid value='%s'>
                     <tr>
                        <th width="100">%s</th>
                        <td>%s</td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>%s</td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>%s</td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>%s</td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>%s</td>
                     </tr>
                     </table>
                     <br />
                     <br />

           """ % (CFG_SITE_URL, recid,
                   _('Interlibrary loan request for books'),
                   _("Item details"),
                   recid,
                   _("Name"),
                   book_title,
                   _("Author(s)"),
                   book_author,
                   _("Year"),
                   book_year,
                   _("Publisher"),
                   book_editor,
                   _("ISBN"),
                   book_isbn)

        out += """
            <style type="text/css"> @import url("/css/tablesorter.css"); </style>
            <script type="text/javascript" src="%s/vendors/jquery-ui/jquery-ui.min.js"></script>
            """% CFG_SITE_URL

        out += """
             <table class="bibcirctable">
                <tr align="center">
                     <td class="bibcirctableheader">%s</td>
                </tr>
             </table>
             <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">
               <tr>
                <th width="150">%s</th>
                <td>
                    <script type="text/javascript">
                        $(function() {
                            $("#date_picker1").datepicker({dateFormat: 'yy-mm-dd', showOn: 'button', buttonImage: "%s/img/calendar.gif", buttonImageOnly: true});
                        });
                    </script>
                    <input type="text" size="10" id="date_picker1" name="period_of_interest_from" value="%s" style='border: 1px solid #cfcfcf'>
                </td>
               </tr>
                <tr>
                <th width="150">%s</th>
                <td>
                    <script type="text/javascript">
                        $(function() {
                            $("#date_picker2").datepicker({dateFormat: 'yy-mm-dd', showOn: 'button', buttonImage: "%s/img/calendar.gif", buttonImageOnly: true});
                        });
                    </script>
                    <input type="text" size="10" id="date_picker2" name="period_of_interest_to" value="%s" style='border: 1px solid #cfcfcf'>
                </td>
                </tr>
                <tr>
                   <th valign="top" width="150">%s</th>
                   <td><textarea name='additional_comments' rows="6" cols="30"
                   style='border: 1px solid #cfcfcf'></textarea></td>
                </tr>
              </table>
              <table class="bibcirctable">
                <tr align="center">
                  <td>
                    <input name="conditions" type="checkbox" value="accepted" />%s</td>
                </tr>
                <tr align="center">
                  <td>
                    <input name="only_edition" type="checkbox" value="Yes" />%s</td>
                </tr>
             </table>
             <br />
             <table class="bibcirctable">
                <tr align="center">
                  <td>
                       <input type=button value="%s"
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit"
                       value="%s" class="formbutton">

                  </td>
                 </tr>
             </table>
             </form>
             <br />
             <br />
             </div>
             """ % (_("ILL request details"),
                    _("Period of interest - From"),
                    CFG_SITE_URL, today,
                    _("Period of interest - To"),
                    CFG_SITE_URL, within_six_months,
                    _("Additional comments"),
                    _("I accept the %(x_url_open)sconditions%(x_url_close)s of the service in particular the return of books in due time.") % {'x_url_open': '<a href="http://library.web.cern.ch/library/Library/ill_faq.html" target="_blank">', 'x_url_close': '</a>'},
                    _("I want this edition only."),
                    _("Back"), _("Continue"))

        return out

    def tmpl_ill_register_request_with_recid(self, message, ln=CFG_SITE_LANG):
        """
        @param message: information to the borrower
        @type message: string

        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = """
        <br /> <br />
        <table class="bibcirctable">
        <tr>
        <td class="bibcirccontent" width="30">%s</td>
        </tr>
        <tr>
        <td class="bibcirccontent" width="30">%s</td>
        </tr>
        </table>
        <br /> <br />
        <table class="bibcirctable">
        <td><input type=button onClick="location.href='%s'" value='%s' class='formbutton'></td>
        </table>
        <br /> <br />
        """ % (message,
               _("Check your library account %(here_link)s.") % {'here_link':
                        create_html_link(CFG_SITE_URL + '/yourloans/display',
                                    {'ln': ln}, _("here"))},
               CFG_SITE_URL,
               _("Back to home"))

        return out

    def tmpl_register_ill_request_with_no_recid_step1(self, infos, borrower_id,
                                                      admin=True,
                                                      ln=CFG_SITE_LANG):
        """
        @param infos: information
        @type infos: list
        """

        _ = gettext_set_language(ln)

        if admin:
            form_url = CFG_SITE_URL + '/admin2/bibcirculation/register_ill_request_with_no_recid_step2'
        else:
            form_url = CFG_SITE_URL+'/ill/book_request_step2'


        out = self.tmpl_infobox(infos, ln)

        if admin:
            out += load_menu(ln)

            out += """
            <br />
            <br />
              <div class="bibcircbottom" align="center">
              <div class="bibcircinfoboxmsg"><strong>%s<br />%s</strong></div>
              <br />
              <br />
            """ % (_("Book does not exist in %(CFG_SITE_NAME)s") % \
                        {'CFG_SITE_NAME': CFG_SITE_NAME},
                   _("Please fill the following form."))

        out += """
          <style type="text/css"> @import url("/css/tablesorter.css"); </style>
           <form name="display_ill_form" action="%s" method="get">
           """ % (form_url)
        out += """
             <table class="bibcirctable">
                  <tr align="center">
                    <td class="bibcirctableheader">%s</td>
                  </tr>
                </table>
            """ % (_("Item details"))

        if borrower_id not in (None, ''):
            out += """
                <input type=hidden name=borrower_id value="%s">
            """ % (borrower_id)

        out += """
                <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">
                    <tr>
                        <th width="100">%s</th>
                        <td>
                          <input type="text" size="45" name="title" style='border: 1px solid #cfcfcf'>
                        </td>
                    </tr>
                    <tr>
                        <th width="100">%s</th>
                        <td>
                          <input type="text" size="45" name="authors" style='border: 1px solid #cfcfcf'>
                        </td>
                    </tr>
                    <tr>
                        <th width="100">%s</th>
                        <td>
                          <input type="text" size="30" name="place" style='border: 1px solid #cfcfcf'>
                        </td>
                    </tr>
                    <tr>
                        <th width="100">%s</th>
                        <td>
                          <input type="text" size="30" name="publisher" style='border: 1px solid #cfcfcf'>
                        </td>
                    </tr>
                    <tr>
                        <th width="100">%s</th>
                        <td>
                          <input type="text" size="30" name="year" style='border: 1px solid #cfcfcf'>
                        </td>
                    </tr>
                    <tr>
                        <th width="100">%s</th>
                        <td>
                          <input type="text" size="30" name="edition" style='border: 1px solid #cfcfcf'>
                        </td>
                    </tr>
                    <tr>
                        <th width="100">%s</th>
                        <td>
                          <input type="text" size="30" name="isbn" style='border: 1px solid #cfcfcf'>
                        </td>
                    </tr>
                </table>


           <br />

           """ % (_("Book title"),
                   _("Author(s)"),
                   _("Place"),
                   _("Publisher"),
                   _("Year"),
                   _("Edition"),
                   _("ISBN"))

        out += """
        <script type="text/javascript" src="%s/vendors/jquery-ui/jquery-ui.min.js"></script>

             <table class="bibcirctable">
                <tr align="center">
                     <td class="bibcirctableheader">%s</td>
                </tr>
             </table>
             <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">
            <!--<tr>
                    <th width="100">%s</th>
                    <td>
                        <input type="text" size="30" name="budget_code" style='border: 1px solid #cfcfcf'>
                    </td>
                </tr>-->
                <tr>
                    <th valign="center" width="100">%s</th>
                    <td valign="center" width="250">

                        <script type="text/javascript">
                             $(function() {
                                 $("#date_picker1").datepicker({dateFormat: 'yy-mm-dd', showOn: 'button', buttonImage: "%s/img/calendar.gif", buttonImageOnly: true});
                             });
                         </script>
                         <input type="text" size="10" id="date_picker1" name="period_of_interest_from" value="%s" style='border: 1px solid #cfcfcf'>

                    </td>
                </tr>
                """% (CFG_SITE_URL,
                      _("ILL request details"), _("Budget code"),
                      _("Period of interest (From)"),
                      CFG_SITE_URL,
                    datetime.date.today().strftime('%Y-%m-%d'))

        out += """
                <tr>
                <th valign="top" width="100">%s</th>
                <td width="250">

                        <script type="text/javascript">
                             $(function() {
                                 $("#date_picker2").datepicker({dateFormat: 'yy-mm-dd', showOn: 'button', buttonImage: "%s/img/calendar.gif", buttonImageOnly: true});
                             });
                         </script>
                         <input type="text" size="10" id="date_picker2" name="period_of_interest_to" value="%s" style='border: 1px solid #cfcfcf'>

                    </td>
                </tr>
                <tr>
                   <th valign="top" width="100">%s</th>
                   <td width="250"><textarea name='additional_comments' rows="6" cols="34"
                   style='border: 1px solid #cfcfcf'></textarea></td>
                </tr>
              </table>
              <table class="bibcirctable">
              <!--<tr>
                  <td>
                    <input name="conditions" type="checkbox" value="accepted" />%s</td>
                </tr> -->
                <tr align="center">
                  <td>
                    <input name="only_edition" type="checkbox" value="Yes" />%s</td>
                </tr>
             </table>
             <br />
             <table class="bibcirctable">
                <tr align="center">
                  <td>
                       <input type=button value="%s"
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit"
                       value="%s" class="formbutton">

                  </td>
                 </tr>
             </table>
             </form>
             <br />
             <br />
             </div>
             """ % (_("Period of interest (To)"), CFG_SITE_URL,
    (datetime.date.today() + datetime.timedelta(days=365)).strftime('%Y-%m-%d'),
    _("Additional comments"),
    _("Borrower accepts the %(x_url_open)sconditions%(x_url_close)s of the service in particular the return of books in due time.") % {'x_url_open': '<a href="http://library.web.cern.ch/library/Library/ill_faq.html" target="_blank">', 'x_url_close': '</a>'},
    _("Borrower wants this edition only."), _("Back"), _("Continue"))

        return out

    def tmpl_register_ill_request_with_no_recid_step2(self, book_info,
                                                      request_details, result,
                                                      key, string, infos, ln):
        """
        @param book_info: book's information
        @type book_info: tuple

        @param request_details: details about a given request
        @type request_details: tuple

        @param result: borrower's information
        @type result: list

        @param key: field (name, email, etc...)
        @param key: string

        @param string: pattern
        @type string: string

        @param infos: information to be displayed in the infobox
        @type infos: list
        """

        (title, authors, place, publisher, year, edition, isbn) = book_info

        (budget_code, period_of_interest_from, period_of_interest_to,
         additional_comments, only_edition)= request_details

        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += load_menu(ln)

        out += """
        <style type="text/css"> @import url("/css/tablesorter.css"); </style>
        <div class="bibcircbottom">
         <form name="step1_form1" action="%s/admin2/bibcirculation/register_ill_request_with_no_recid_step2" method="get" >
        <br />

                <table class="bibcirctable">
                  <tr>
                    <td width="500" valign='top'>
                       <table class="bibcirctable">
                        <tr>
                            <td class="bibcirctableheader" width="10">%s</td>
                        </tr>
                       </table>
                      <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td><input type=hidden name=title value="%s">
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td><input type=hidden name=authors value="%s">
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td><input type=hidden name=place value="%s">
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td><input type=hidden name=year value="%s">
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td><input type=hidden name=publisher value="%s">
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td><input type=hidden name=edition value="%s">
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td><input type=hidden name=isbn value="%s">
                        </tr>
                      </table>
                      <table>
                         <tr>
                           <td class="bibcirctableheader">%s</td>
                        </tr>
                       </table>
                       <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
                       <!--
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td><input type=hidden name=budget_code value="%s">
                        </tr>
                        -->
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td><input type=hidden name=period_of_interest_from value="%s">
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td><input type=hidden name=period_of_interest_to value="%s">
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td><input type=hidden name=additional_comments value="%s">
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td><input type=hidden name=only_edition value="%s">
                        </tr>
                      </table>
                     </td>
                     <td width="200" align='center' valign='top'>
                       <table>
                         <tr>
                           <td>

                           </td>
                         </tr>
                       </table>
                     </td>
                     """ % (CFG_SITE_URL,
                _("Item details"),
                _("Name"), title, title,
                _("Author(s)"), authors, authors,
                _("Place"), place, place,
                _("Year"), year, year,
                _("Publisher"), publisher, publisher,
                _("Edition"), edition, edition,
                _("ISBN"), isbn, isbn,
                _("ILL request details"),
                _("Budget code"), budget_code, budget_code,
                _("Period of interest - From"),
                period_of_interest_from, period_of_interest_from,
                _("Period of interest - To"),
                period_of_interest_to, period_of_interest_to,
                _("Additional comments"),
                additional_comments, additional_comments,
                _("Only this edition."), only_edition, only_edition)

        out += """
        <td valign='top' align='center'>
         <table>

            """

        if CFG_CERN_SITE == 1:
            out += """
                <tr>
                   <td class="bibcirctableheader" align="center">%s
                   """ % (_("Search user by"))

            if key == 'email':
                out += """
                   <input type="radio" name="key" value="ccid">%s
                   <input type="radio" name="key" value="name">%s
                   <input type="radio" name="key" value="email" checked>%s
                   """ % ('ccid', _('name'), _('email'))

            elif key == 'name':
                out += """
                   <input type="radio" name="key" value="ccid">%s
                   <input type="radio" name="key" value="name" checked>%s
                   <input type="radio" name="key" value="email">%s
                   """ % ('ccid', _('name'), _('email'))

            else:
                out += """
                   <input type="radio" name="key" value="ccid" checked>%s
                   <input type="radio" name="key" value="name">%s
                   <input type="radio" name="key" value="email">%s
                   """ % ('ccid', _('name'), _('email'))

        else:
            out += """
                 <tr>
                   <td align="center" class="bibcirctableheader">%s
                   """ % (_("Search borrower by"))

            if key == 'email':
                out += """
                   <input type="radio" name="key" value="id">%s
                   <input type="radio" name="key" value="name">%s
                   <input type="radio" name="key" value="email" checked>%s
                   """ % (_('id'), _('name'), _('email'))

            elif key == 'id':
                out += """
                   <input type="radio" name="key" value="id" checked>%s
                   <input type="radio" name="key" value="name">%s
                   <input type="radio" name="key" value="email">%s
                   """ % (_('id'), _('name'), _('email'))

            else:
                out += """
                   <input type="radio" name="key" value="id">%s
                   <input type="radio" name="key" value="name" checked>%s
                   <input type="radio" name="key" value="email">%s
                   """ % (_('id'), _('name'), _('email'))


        out += """
                    <br><br>
                    </td>
                    </tr>
                    <tr>
                    <td align="center">
                    <input type="text" size="40" id="string" name="string"
                            value='%s' style='border: 1px solid #cfcfcf'>
                    </td>
                    </tr>
                    <tr>
                    <td align="center">
                    <br>
                    <input type="submit" value="%s" class="formbutton">
                    </td>
                    </tr>

                   </table>
          </form>

        """ % (string or '', _("Search"))

        if result:
            out += """
            <br />
            <form name="step1_form2"
                  action="%s/admin2/bibcirculation/register_ill_request_with_no_recid_step3"
                  method="get" >
            <input type=hidden name=title value="%s">
            <input type=hidden name=authors value="%s">
            <input type=hidden name=place value="%s">
            <input type=hidden name=publisher value="%s">
            <input type=hidden name=year value="%s">
            <input type=hidden name=edition value="%s">
            <input type=hidden name=isbn value="%s">

            <table class="bibcirctable">
              <tr width="200">
                <td align="center">
                  <select name="user_info" size="8"
                          style='border: 1px solid #cfcfcf; width:80%%'>

            """ % (CFG_SITE_URL, title, authors, place,
                   publisher, year, edition, isbn)

            for (borrower_id, ccid, name, email,
                 phone, address, mailbox) in result:
                out += """
                       <option value ='%s,%s,%s,%s,%s,%s,%s'>%s
                       """ % (borrower_id, ccid, name, email, phone,
                              address, mailbox, name)

            out += """
                    </select>
                    </td>
                    </tr>
                    </table>
                    <table class="bibcirctable">
                    <tr>
                        <td align="center">
                        <input type="submit" value='%s' class="formbutton">
                        </td>
                    </tr>
                    </table>
                    <!-- <input type=hidden name=budget_code value="%s"> -->
                    <input type=hidden name=period_of_interest_from value="%s">
                    <input type=hidden name=period_of_interest_to value="%s">
                    <input type=hidden name=additional_comments value="%s">
                    <input type=hidden name=only_edition value="%s">
                    </form>
                    """ % (_("Select user"), budget_code,
                                            period_of_interest_from,
                                            period_of_interest_to,
                                            additional_comments,
                                            only_edition)

        out += """
                  </td>
                </tr>
              </table>
              <br />
              <br />
              <br />
              <br />
              </div>
              """

        return out

    def tmpl_register_ill_request_with_no_recid_step3(self, book_info,
                                                    user_info, request_details,
                                                    admin=True,
                                                    ln=CFG_SITE_LANG):
        """
        @param book_info: book's information
        @type book_info: tuple

        @param user_info: user's information
        @type user_info: tuple

        @param request_details: details about a given request
        @type request_details: tuple
        """

        _ = gettext_set_language(ln)

        if admin:
            form_url = CFG_SITE_URL+'/admin2/bibcirculation/register_ill_request_with_no_recid_step4'
        else:
            form_url = CFG_SITE_URL+'/ill/book_request_step3'


        (title, authors, place, publisher, year, edition, isbn) = book_info

        (borrower_id, ccid, name, email, phone, address, mailbox) = user_info

        display_id = borrower_id
        id_string = _("ID")
        if CFG_CERN_SITE == 1:
            display_id = ccid
            id_string = _("CCID")

        (budget_code, period_of_interest_from, period_of_interest_to,
         additional_comments, only_edition)= request_details

        out = ""
        if admin:
            out += load_menu(ln)

        out += """
        <style type="text/css"> @import url("/css/tablesorter.css"); </style>
        <div class="bibcircbottom">
        <form name="step3_form1" action="%s" method="post" >
        <br />
                <table class="bibcirctable">
                  <tr>
                    <td width="200" valign='top'>
        """ % (form_url)

        out += """
                    <input type=hidden name=title value='%s'>
                    <input type=hidden name=authors value='%s'>
                    <input type=hidden name=place value='%s'>
                    <input type=hidden name=publisher value='%s'>
                    <input type=hidden name=year value='%s'>
                    <input type=hidden name=edition value='%s'>
                    <input type=hidden name=isbn value='%s'>
                """ % (title, authors, place, publisher, year, edition, isbn)

        out += """
                    <!-- <input type=hidden name=budget_code value='%s'> -->
                    <input type=hidden name=period_of_interest_from value='%s'>
                    <input type=hidden name=period_of_interest_to value='%s'>
                    <input type=hidden name=additional_comments value='%s'>
                    <input type=hidden name=only_edition value='%s'>
                """ % (budget_code, period_of_interest_from,
                    period_of_interest_to, additional_comments, only_edition)

        out += """    <table class="bibcirctable">
                        <tr>
                            <td class="bibcirctableheader" width="10">%s</td>
                        </tr>
                       </table>
                      <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td>
                        </tr>
                      </table>
                      """ % (_("Item details"),
                            _("Title"), title,
                            _("Author(s)"), authors,
                            _("Place"), place,
                            _("Year"), year,
                            _("Publisher"), publisher,
                            _("Edition"), edition,
                            _("ISBN"), isbn)

        out += """
                      <table>
                         <tr>
                           <td class="bibcirctableheader">%s</td>
                        </tr>
                       </table>
                       <table class="tablesorter" border="0"
                              cellpadding="0" cellspacing="1">
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td>
                        </tr>
                      </table>
                     </td>
                     <td width="50" valign='top'>
                       <table>
                         <tr>
                           <td>

                           </td>
                         </tr>
                       </table>
                     </td>
                """ % (_("ILL request details"),
                    _("Budget code"), budget_code,
                    _("Period of interest (From)"), period_of_interest_from,
                    _("Period of interest (To)"), period_of_interest_to,
                    _("Additional comments"), additional_comments,
                    _("Only this edition"), only_edition)

        out += """
                    <td width="200" valign='top'>

                            <table>
                                <tr align="center">
                                  <td class="bibcirctableheader">%s</td>
                                  <input type=hidden name=borrower_id value="%s">
                                </tr>
                            </table>
                            <table class="tablesorter" width="200" border="0"
                                    cellpadding="0" cellspacing="1">
                                <tr>
                                 <th width="100">%s</th>
                                 <td>%s</td>
                                </tr>
                                <tr>
                                 <th width="100">%s</th>
                                 <td>%s</td>
                                </tr>
                                <tr>
                                 <th width="100">%s</th>
                                 <td>%s</td>
                                </tr>
                                <tr>
                                 <th width="100">%s</th>
                                 <td>%s</td>
                                </tr>
                                <tr>
                                 <th width="100">%s</th>
                                 <td>%s</td>
                                </tr>
                                <tr>
                                 <th width="100">%s</th>
                                 <td>%s</td>
                                </tr>
                            </table>

                    </td>
                </tr>
            </table>
                      """ % (_("Borrower details"), borrower_id,
                             id_string, display_id,
                             _("Name"), name,
                             _("Address"), address,
                             _("Mailbox"), mailbox,
                             _("Email"), email,
                             _("Phone"), phone)

        out += """<br />
                  <table class="bibcirctable">
                    <tr align="center">
                      <td>
                        <input type=button value="%s"
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit"
                       value="%s" class="formbutton">
                      </td>
                    </tr>
                </table>""" % (_("Back"), _("Continue"))


        return out

    def tmpl_register_ill_book_request(self, infos, borrower_id,
                                       ln=CFG_SITE_LANG):
        """
        @param infos: information
        @type infos: list

        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += load_menu(ln)

        out += """
        <div class=bibcircbottom align="center">
        <form name="search_form"
              action="%s/admin2/bibcirculation/register_ill_book_request_result"
              method="get" >
        <br />
        <br />
        <div class="bibcircinfoboxmsg"><strong>%s</strong></div>
        <br />
        <input type=hidden name=start value="0">
        <input type=hidden name=end value="10">
        """ % (CFG_SITE_URL,
            _("Check if the book already exists on %(CFG_SITE_NAME)s, before sending your ILL request.") % {'CFG_SITE_NAME': CFG_SITE_NAME})

        if borrower_id is not None:
            out += """
            <input type=hidden name=borrower_id value="%s">
            """ % (borrower_id)

        out += """
        <table class="bibcirctable">
          <tr align="center">
            <td class="bibcirctableheader">%s
              <input type="radio" name="f" value="" checked>%s
              <input type="radio" name="f" value="barcode">%s
              <input type="radio" name="f" value="author">%s
              <input type="radio" name="f" value="title">%s
              <br />
              <br />
            </td>
            """ % (_("Search item by"), _("RecId/Item details"), _("barcode"),
                   _("author"), _("title"))

        out += """
          </tr>
          <tr align="center">
            <td>
                <input type="text" size="50" name="p" id='p' style='border: 1px solid #cfcfcf'>
                <script language="javascript" type="text/javascript">
                    document.getElementById("p").focus();
                </script>
            </td>
          </tr>
        </table>
        <br />
        <table class="bibcirctable">
          <tr align="center">
            <td>
              <input type=button value='%s'
                     onClick="history.go(-1)" class="formbutton">
              <input type="submit" value='%s' class="formbutton">
            </td>
          </tr>
        </table>
        <br />
        <br />
        <br />
        <br />
        </div>
        </form>

        """ % (_("Back"), _("Search"))

        return out

    def tmpl_register_ill_book_request_result(self, result, borrower_id,
                                              ln=CFG_SITE_LANG):
        """
        @param result: book's information
        @type result: list

        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = load_menu(ln)

        if len(result) == 0:
            out += """
            <div class="bibcircbottom" align="center">
            <br />
            <div class="bibcircinfoboxmsg">%s</div>
            <br />
            """ % (_("0 items found."))
            if borrower_id is not None:
                out += """
                    <input type=hidden name=borrower_id value="%s">
                """ % (borrower_id)

        else:
            out += """
        <style type="text/css"> @import url("/css/tablesorter.css"); </style>
        <div class="bibcircbottom">
        <form name="search_form"
              action="%s/admin2/bibcirculation/register_ill_request_with_no_recid_step1"
              method="get" >
        <br />
        """ % (CFG_SITE_URL)

            if borrower_id is not None and borrower_id is not '':
                out += """
        <input type=hidden name=borrower_id value="%s">
        """ % (borrower_id)

            out += """
        <table class="bibcirctable">
          <tr align="center">
            <td>
               <strong>%s item(s) found</strong>
            </td>
          </tr>
        </table>
        <br />
          <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
          <thead>
            <tr>
              <th>%s</th>
              <th>%s</th>
              <th>%s</th>
              <th>%s</th>
            </tr>
          </thead>
          <tbody>
        """ % (len(result), _("Title"),
               _("Author"), _("Publisher"),
               _("# copies"))

            for recid in result:

                (book_author, book_editor,
                 book_copies) = get_item_info_for_search_result(recid)

                title_link = create_html_link(CFG_SITE_URL +
                                    '/admin2/bibcirculation/get_item_details',
                                    {'recid': recid, 'ln': ln},
                                    (book_title_from_MARC(recid)))

                out += """
                <tr>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                </tr>
                """ % (title_link, book_author,
                       book_editor, book_copies)

        out += """
          </tbody>
          </table>
        <br />
        <table class="bibcirctable">
          <tr align="center">
            <td>
              <input type=button value='%s'
               onClick="history.go(-1)" class="formbutton">
              <input type="submit" value='%s' class="formbutton">
            </td>
          </tr>
        </table>
        <br />
        <br />
        <br />
        </form>
        </div>

        """ % (_("Back"), _("Proceed anyway"))

        return out

    def tmpl_register_ill_article_request_step1(self, infos, admin=True,
                                                ln=CFG_SITE_LANG):
        """
        @param infos: information
        @type infos: list
        """

        _ = gettext_set_language(ln)

        if admin:
            form_url = CFG_SITE_URL + \
                    '/admin2/bibcirculation/register_ill_article_request_step2'
            method = 'get'
        else:
            form_url = CFG_SITE_URL+'/ill/article_request_step2'
            method = 'post'

        out = self.tmpl_infobox(infos, ln)
        if admin:
            out += load_menu(ln)

        out += """
        <br />
        <br />
          <div class="bibcircbottom" align="center">
          <br />
          <br />
          <style type="text/css"> @import url("/css/tablesorter.css"); </style>
          """
        out += """
           <form name="display_ill_form" action="%s" method="%s">
                """ % (form_url, method)
        out += """
             <table class="bibcirctable">
                  <tr align="center">
                    <td class="bibcirctableheader" width="10">%s</td>
                  </tr>
                </table>
                <table class="tablesorterborrower" border="0"
                       cellpadding="0" cellspacing="1">
                    <tr>
                        <th width="100">%s</th>
                        <td>
                          <input type="text" size="45" name="periodical_title"
                                 id='periodical_title'
                                 style='border: 1px solid #cfcfcf'>
                          <script language="javascript" type="text/javascript">
                            document.getElementById("periodical_title").focus();
                          </script>
                        </td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>
                          <input type="text" size="45" name="article_title"
                                 style='border: 1px solid #cfcfcf'>
                        </td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>
                          <input type="text" size="45" name="author"
                                 style='border: 1px solid #cfcfcf'>
                        </td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>
                          <input type="text" size="30" name="report_number"
                                 style='border: 1px solid #cfcfcf'>
                        </td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>
                          <input type="text" size="30" name="volume"
                                 style='border: 1px solid #cfcfcf'>
                        </td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>
                          <input type="text" size="30" name="issue"
                                 style='border: 1px solid #cfcfcf'>
                        </td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>
                          <input type="text" size="30" name="page"
                                 style='border: 1px solid #cfcfcf'>
                        </td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>
                          <input type="text" size="30" name="year"
                                 style='border: 1px solid #cfcfcf'>
                        </td>
                     </tr>
                     <!-- <tr>
                        <th width="100">%s</th>
                        <td>
                          <input type="text" size="30" name="budget_code"
                                 style='border: 1px solid #cfcfcf'>
                        </td>
                     </tr> -->
                     <tr>
                        <th width="100">%s</th>
                        <td>
                          <input type="text" size="30" name="issn"
                                 style='border: 1px solid #cfcfcf'>
                        </td>
                     </tr>
                </table>
           <br />

           """ % (_("Article details"),
                   _("Periodical title"),
                   _("Article title"),
                   _("Author(s)"),
                   _("Report number"),
                   _("Volume"),
                   _("Issue"),
                   _("Page"),
                   _("Year"),
                   _("Budget code"),
                   _("ISSN"))

        out += """
            <script type="text/javascript" src="%s/vendors/jquery-ui/jquery-ui.min.js"></script>

             <table class="bibcirctable">
                <tr align="center">
                     <td class="bibcirctableheader">%s</td>
                </tr>
             </table>
             <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">
               <tr>
                <th width="150">%s</th>
                <td>
                        <script type="text/javascript">
                            $(function(){
                            $("#date_picker1").datepicker({dateFormat: 'yy-mm-dd', showOn: 'button', buttonImage: "%s/img/calendar.gif", buttonImageOnly: true});
                            });
                        </script>
                        <input type="text" size="12" id="date_picker1"
                               name="period_of_interest_from" value="%s"
                               style='border: 1px solid #cfcfcf'>
                    </td>
                </tr>
                <tr>
                    <th width="150">%s</th>
                    <td>
                        <script type="text/javascript">
                            $(function(){
                            $("#date_picker2").datepicker({dateFormat: 'yy-mm-dd', showOn: 'button', buttonImage: "%s/img/calendar.gif", buttonImageOnly: true});
                            });
                        </script>
                        <input type="text" size="12" id="date_picker2"
                               name="period_of_interest_to" value="%s"
                               style='border: 1px solid #cfcfcf'>
                    </td>
                </tr>
                <tr>
                   <th valign="top" width="150">%s</th>
                    <td>
                        <textarea name='additional_comments' rows="6" cols="30"
                                  style='border: 1px solid #cfcfcf'></textarea>
                        </td>
                </tr>
              </table>
              <br />
              <table class="bibcirctable">
                <tr align="center">
                    <td>
                        <input type=button value="%s"
                               onClick="history.go(-1)" class="formbutton">
                        <input type="submit"
                               value="%s" class="formbutton">
                    </td>
                </tr>
              </table>
              </form>
              <br />
              <br />
              </div>
    """ % (CFG_SITE_URL, _("ILL request details"),
        _("Period of interest - From"), CFG_SITE_URL,
        datetime.date.today().strftime('%Y-%m-%d'),
        _("Period of interest - To"), CFG_SITE_URL,
   (datetime.date.today() + datetime.timedelta(days=365)).strftime('%Y-%m-%d'),
        _("Additional comments"),
        _("Back"), _("Continue"))

        return out

    def tmpl_register_ill_article_request_step2(self, article_info,
                                    request_details, result, key, string,
                                    infos, ln=CFG_SITE_LANG):
        """
        @param article_info: information about the article
        @type article_info: tuple

        @param request_details: details about a given ILL request
        @type request_details: tuple

        @param result: result with borrower's information
        @param result: list

        @param key: field (name, email, etc...)
        @param key: string

        @param string: pattern
        @type string: string

        @param infos: information
        @type infos: list
        """

        (periodical_title, article_title, author, report_number,
         volume, issue, page, year, issn) = article_info

        (period_of_interest_from, period_of_interest_to, budget_code,
         additional_comments)= request_details

        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += load_menu(ln)

        out += """
        <style type="text/css"> @import url("/css/tablesorter.css"); </style>
        <div class="bibcircbottom">
         <form name="step1_form1"
               action="%s/admin2/bibcirculation/register_ill_article_request_step2"
               method="get" >
        <br />
          <table class="bibcirctable">
                  <tr>
                     <td class="bibcirctableheader" width="10">%s</td>
                  </tr>
                </table>
                <table class="bibcirctable">
                  <tr>
                    <td width="500" valign='top'>
                      <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td><input type=hidden name=periodical_title value="%s">
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td><input type=hidden name=article_title value="%s">
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td><input type=hidden name=author value="%s">
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td><input type=hidden name=report_number value="%s">
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td><input type=hidden name=volume value="%s">
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td><input type=hidden name=issue value="%s">
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td><input type=hidden name=page value="%s">
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td><input type=hidden name=year value="%s">
                        </tr>
                        <!-- <tr>
                          <th width="100">%s</th>
                          <td>%s</td><input type=hidden name=budget_code value="%s">
                        </tr> -->
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td><input type=hidden name=issn value="%s">
                        </tr>
                      </table>
                      <table>
                         <tr>
                           <td class="bibcirctableheader">%s</td>
                        </tr>
                       </table>
                       <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td><input type=hidden name=period_of_interest_from value="%s">
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td><input type=hidden name=period_of_interest_to value="%s">
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td><input type=hidden name=additional_comments value="%s">
                        </tr>
                      </table>
                     </td>
                     <td width="200" align='center' valign='top'>
                     </td>
        """ % (CFG_SITE_URL,
            _("Item details"),
            _("Periodical title"), periodical_title, periodical_title,
            _("Article title"), article_title, article_title,
            _("Author(s)"), author, author,
            _("Report number"), report_number, report_number,
            _("Volume"), volume, volume,
            _("Issue"), issue, issue,
            _("Page"), page, page,
            _("Year"), year, year,
            _("Budget code"), budget_code, budget_code,
            _("ISSN"), issn, issn,
            _("ILL request details"),
            _("Period of interest - From"),
            period_of_interest_from, period_of_interest_from,
            _("Period of interest - To"),
            period_of_interest_to, period_of_interest_to,
            _("Additional comments"),
            additional_comments, additional_comments)

        out += """
        <td valign='top' align='center'>
         <table>

            """

        if CFG_CERN_SITE == 1:
            out += """
                <tr>
                   <td class="bibcirctableheader" align="center">%s
                   """ % (_("Search user by"))

            if key == 'email':
                out += """
                   <input type="radio" name="key" value="ccid">%s
                   <input type="radio" name="key" value="name">%s
                   <input type="radio" name="key" value="email" checked>%s
                   """ % ('ccid', _('name'), _('email'))

            elif key == 'name':
                out += """
                   <input type="radio" name="key" value="ccid">%s
                   <input type="radio" name="key" value="name" checked>%s
                   <input type="radio" name="key" value="email">%s
                   """ % ('ccid', _('name'), _('email'))

            else:
                out += """
                   <input type="radio" name="key" value="ccid" checked>%s
                   <input type="radio" name="key" value="name">%s
                   <input type="radio" name="key" value="email">%s
                   """ % ('ccid', _('name'), _('email'))

        else:
            out += """
                 <tr>
                   <td align="center" class="bibcirctableheader">%s
                   """ % (_("Search borrower by"))

            if key == 'email':
                out += """
                   <input type="radio" name="key" value="id">%s
                   <input type="radio" name="key" value="name">%s
                   <input type="radio" name="key" value="email" checked>%s
                   """ % (_('id'), _('name'), _('email'))

            elif key == 'id':
                out += """
                   <input type="radio" name="key" value="id" checked>%s
                   <input type="radio" name="key" value="name">%s
                   <input type="radio" name="key" value="email">%s
                   """ % (_('id'), _('name'), _('email'))

            else:
                out += """
                   <input type="radio" name="key" value="id">%s
                   <input type="radio" name="key" value="name" checked>%s
                   <input type="radio" name="key" value="email">%s
                   """ % (_('id'), _('name'), _('email'))

        out += """
                    <br><br>
                    </td>
                    </tr>
                    <tr>
                    <td align="center">
                    <input type="text" size="40" id="string" name="string"
                           value='%s' style='border: 1px solid #cfcfcf'>
                    </td>
                    </tr>
                    <tr>
                    <td align="center">
                    <br>
                    <input type="submit" value="%s" class="formbutton">
                    </td>
                    </tr>
                   </table>
          </form>

        """ % (string or '', _("Search"))

        if result:
            out += """
            <br />
            <form name="step1_form2"
                  action="%s/admin2/bibcirculation/register_ill_article_request_step3"
                  method="post" >
            <input type=hidden name=periodical_title value="%s">
            <input type=hidden name=article_title value="%s">
            <input type=hidden name=author value="%s">
            <input type=hidden name=report_number value="%s">
            <input type=hidden name=volume value="%s">
            <input type=hidden name=issue value="%s">
            <input type=hidden name=page value="%s">
            <input type=hidden name=year value="%s">
            <input type=hidden name=issn value="%s">
            <table class="bibcirctable">
              <tr width="200">
                <td align="center">
                  <select name="user_info" size="8"
                          style='border: 1px solid #cfcfcf; width:40%%'>
            """ % (CFG_SITE_URL, periodical_title, article_title,
                   author, report_number, volume, issue, page, year, issn)

            for (borrower_id, ccid, name, email,
                 phone, address, mailbox) in result:
                out += """
                       <option value ='%s,%s,%s,%s,%s,%s,%s'>%s
                       """ % (borrower_id, ccid, name, email,
                              phone, address, mailbox, name)

            out += """
                    </select>
                    </td>
                    </tr>
                    </table>
                    <table class="bibcirctable">
                    <tr>
                        <td align="center">
                        <input type="submit" value='%s' class="formbutton">
                        </td>
                    </tr>
                    </table>
                    <input type=hidden name=period_of_interest_from value="%s">
                    <input type=hidden name=period_of_interest_to value="%s">
                    <input type=hidden name=budget_code value="%s">
                    <input type=hidden name=additional_comments value="%s">
                    </form>
                    """ % (_("Select user"),
                           period_of_interest_from, period_of_interest_to,
                           budget_code, additional_comments)

        out += """
                  </td>
                </tr>
              </table>
              <br />
              <br />
              <br />
              <br />
              </div>
              """

        return out


    def tmpl_register_purchase_request_step1(self, infos, fields, admin=False,
                                             ln=CFG_SITE_LANG):
        """
        @param infos: information
        @type infos: list
        """

        _ = gettext_set_language(ln)
        recid = ''
        #If admin, redirect to the second step(where the user is selected)
        if admin:
            form_url = CFG_SITE_URL + \
                    '/admin2/bibcirculation/register_purchase_request_step2'
        else:
            form_url = CFG_SITE_URL+'/ill/purchase_request_step2'

        if len(fields) == 7:
            (request_type, recid, _budget_code, cash,
             _period_of_interest_from, _period_of_interest_to,
             _additional_comments) = fields
            (book_title, book_year, book_author,
             book_isbn, book_editor) = book_information_from_MARC(int(recid))
        else:
            (request_type, title, authors, place, publisher, year, edition,
             this_edition_only, isbn, standard_number, _budget_code, cash,
             _period_of_interest_from, _period_of_interest_to,
             _additional_comments) = fields
            if this_edition_only == 'Yes':
                checked_edition = 'checked'
            else:
                checked_edition = ''

        if cash:
            checked_cash = 'checked'
        else:
            checked_cash = ''

        out = ''

        if admin:
            out += load_menu(ln)

        out += """<br />""" + self.tmpl_infobox(infos, ln)

        if not admin:
            out += """%s<br /><br />""" % _("We will process your order immediately and contact you \
                                        as soon as the document is received.")
            out += _("According to a decision from the Scientific Information Policy Board, \
            books purchased with budget codes other than Team accounts will be added to the Library catalogue, \
            with the indication of the purchaser.")

        out += """
          <div class="bibcircbottom" align="center">
          <br />
          <style type="text/css"> @import url("/css/tablesorter.css"); </style>
          """
        out += """
            <form name="display_ill_form" action="%s" method="post">
                <table class="bibcirctable">
                    <tr align="center">
                        <td class="bibcirctableheader" width="10">%s</td>
                    </tr>
                </table>
                <table class="tablesorterborrower" border="0"
                       cellpadding="0" cellspacing="1">
                """ % (form_url, _("Document details"))
        if recid:
            out += """<tr>
                        <th width="100">%s</th>
                        <td>%s</td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>%s</td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>%s</td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>%s</td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>%s</td>
                     </tr>
                    </table>
                    <input type=hidden name=recid value="%s">
                <br />
              """ % ( _("Title"), book_title,
                      _("Author(s)"), book_author,
                      _("Year"), book_year,
                      _("Publisher"), book_editor,
                      _("ISBN"), book_isbn,
                      recid)

        else:
            out += """<tr>
                        <th width="100">%s</th>
                        <td><SELECT name="type" style='border: 1px solid #cfcfcf'>
                   """ % _("Document type")
            for purchase_type in CFG_BIBCIRCULATION_ACQ_TYPE:
                if request_type == purchase_type or request_type == '':
                    out += """
                                    <OPTION VALUE="%s" selected="selected">%s
                    """ % (purchase_type, purchase_type)
                else:
                    out += """
                                    <OPTION VALUE="%s">%s
                    """ % (purchase_type, purchase_type)

            out += """    </SELECT></td>
                        </tr>
                        <tr>
                            <th width="100">%s</th>
                            <td>
                                <input type="text" size="45" name="title"
                                       id='title' value='%s'
                                       style='border: 1px solid #cfcfcf'>
                                <script language="javascript" type="text/javascript">
                                        document.getElementById("title").focus();
                                </script>
                            </td>
                        </tr>
                        <tr>
                            <th width="100">%s</th>
                            <td>
                                <input type="text" size="45" name="authors"
                                       value='%s'
                                       style='border: 1px solid #cfcfcf'>
                            </td>
                        </tr>
                        <tr>
                            <th width="100">%s</th>
                            <td>
                                <input type="text" size="30" name="place"
                                       value='%s'
                                       style='border: 1px solid #cfcfcf'>
                            </td>
                        </tr>
                        <tr>
                            <th width="100">%s</th>
                            <td>
                                <input type="text" size="30" name="publisher"
                                       value='%s'
                                       style='border: 1px solid #cfcfcf'>
                            </td>
                        </tr>
                        <tr>
                            <th width="100">%s</th>
                            <td>
                                <input type="text" size="30" name="year"
                                       value='%s'
                                       style='border: 1px solid #cfcfcf'>
                            </td>
                        </tr>
                        <tr>
                            <th width="100">%s</th>
                            <td>
                                <input type="text" size="30" name="edition"
                                       value='%s'
                                       style='border: 1px solid #cfcfcf'>
                                       <br />
                                <input name="this_edition_only"
                                       type="checkbox" value="Yes" %s/>%s</td>
                            </td>
                        </tr>
                        <tr>
                            <th width="100">%s</th>
                            <td>
                                <input type="text" size="30" name="isbn"
                                       value='%s'
                                       style='border: 1px solid #cfcfcf'>
                            </td>
                        </tr>
                        <tr>
                            <th width="100">%s</th>
                            <td>
                                <input type="text" size="30" name="standard_number"
                                       value='%s'
                                       style='border: 1px solid #cfcfcf'>
                            </td>
                        </tr>
                    </table>
                <br />
               """ % (_("Title"), title,
                      _("Author(s)"), authors,
                      _("Place"), place,
                      _("Publisher"), publisher,
                      _("Year"), year,
                      _("Edition"), edition,
                      checked_edition, _("This edition only"),
                      _("ISBN"), isbn,
                      _("Standard number"), standard_number)

        out += """
            <script type="text/javascript"
                    src="%s/vendors/jquery-ui/jquery-ui.min.js"></script>

             <table class="bibcirctable">
                <tr align="center">
                     <td class="bibcirctableheader">%s</td>
                </tr>
             </table>
             <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">
                <tr>
                    <th width="100">%s</th>
                    <td>
                        <input type="text" size="30" name="budget_code"
                               style='border: 1px solid #cfcfcf'>
                        <input name="cash" type="checkbox" value="Yes" %s/>%s</td>
                </tr>
                <tr>
                    <th width="150">%s</th>
                    <td>
                        <script type="text/javascript">
                            $(function(){
                            $("#date_picker1").datepicker({dateFormat: 'yy-mm-dd',
                                         showOn: 'button', buttonImage: "%s/img/calendar.gif",
                                         buttonImageOnly: true});
                            });
                        </script>
                        <input type="text" size="12" id="date_picker1"
                               name="period_of_interest_from" value="%s"
                               style='border: 1px solid #cfcfcf'>
                    </td>
                </tr>
                <tr>
                    <th width="150">%s</th>
                    <td>
                        <script type="text/javascript">
                            $(function(){
                            $("#date_picker2").datepicker({dateFormat: 'yy-mm-dd',
                                        showOn: 'button', buttonImage: "%s/img/calendar.gif",
                                        buttonImageOnly: true});
                            });
                        </script>
                        <input type="text" size="12" id="date_picker2"
                               name="period_of_interest_to" value="%s"
                               style='border: 1px solid #cfcfcf'>
                    </td>
                </tr>
                <tr>
                   <th valign="top" width="150">%s</th>
                    <td>
                        <textarea name='additional_comments' rows="6" cols="30"
                                  style='border: 1px solid #cfcfcf'></textarea>
                        </td>
                </tr>
              </table>
              <table class="bibcirctable">
                <tr align="center">
                    <td>
                        <input type=button value="%s"
                               onClick="history.go(-1)" class="formbutton">
                        <input type="submit" id="submit_request"
                               value="%s" class="formbutton">
                    </td>
                </tr>
              </table>
              </form>
              <br />
              </div>
    """ % (CFG_SITE_URL, _("Request details"),
           _("Budget code"), checked_cash, _("Cash"),
           _("Period of interest - From"), CFG_SITE_URL,
           datetime.date.today().strftime('%Y-%m-%d'),
           _("Period of interest - To"), CFG_SITE_URL,
    (datetime.date.today() + datetime.timedelta(days=365)).strftime('%Y-%m-%d'),
          _("Additional comments"), _("Back"), _("Continue"))

        return out

    def tmpl_register_purchase_request_step2(self, infos, fields, result,
                                             p, f, ln=CFG_SITE_LANG):
        recid = ''
        if len(fields) == 7:
            (request_type, recid, budget_code, cash,
             period_of_interest_from, period_of_interest_to,
             additional_comments) = fields
            (title, year, authors, isbn, publisher) = book_information_from_MARC(int(recid))
        else:
            (request_type, title, authors, place, publisher, year, edition,
             this_edition_only, isbn, standard_number, budget_code, cash,
             period_of_interest_from, period_of_interest_to,
             additional_comments) = fields

        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += load_menu(ln)

        out += """
        <style type="text/css"> @import url("/css/tablesorter.css"); </style>
        <div class="bibcircbottom">
         <form name="step2_form1"
               action="%s/admin2/bibcirculation/register_purchase_request_step2"
               method="get">
        <br />
          <table class="bibcirctable">
                  <tr>
                     <td class="bibcirctableheader" width="10">%s</td>
                  </tr>
                </table>
                <table class="bibcirctable">
                  <tr>
                    <td width="500" valign='top'>
                      <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td><input type=hidden name=type value="%s">
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td><input type=hidden name=title value="%s">
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td><input type=hidden name=authors value="%s">
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td><input type=hidden name=isbn value="%s">
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td><input type=hidden name=publisher value="%s">
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td><input type=hidden name=year value="%s">
                        </tr>""" % ( CFG_SITE_URL,
                                     _("Item details"),
                                     _("Type"), request_type, request_type,
                                     _("Title"), title, title,
                                     _("Author(s)"), authors, authors,
                                     _("ISBN"), isbn, isbn,
                                     _("Publisher"), publisher, publisher,
                                     _("Year"), year, year)

        if not recid:
            out += """<tr>
                      <th width="100">%s</th>
                      <td>%s</td><input type=hidden name=place value="%s">
                    </tr>
                    <tr>
                      <th width="100">%s</th>
                      <td>%s</td><input type=hidden name=edition value="%s">
                    </tr>
                    <tr>
                      <th width="100">%s</th>
                      <td>%s</td><input type=hidden name=standard_number value="%s">
                    </tr>""" % ( _("Place"), place, place,
                                 _("Edition"), edition, edition,
                                 _("Standard number"), standard_number, standard_number)

        out += """</table>
              <table>
                 <tr>
                   <td class="bibcirctableheader">%s</td>
                </tr>
               </table>
               <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
                <tr>
                    <th width="100">%s</th>
                    <td>%s</td><input type=hidden name=budget_code value="%s">
                </tr>

                <tr>
                  <th width="100">%s</th>
                  <td>%s</td><input type=hidden name=period_of_interest_from value="%s">
                </tr>
                <tr>
                  <th width="100">%s</th>
                  <td>%s</td><input type=hidden name=period_of_interest_to value="%s">
                </tr>
                <tr>
                  <th width="100">%s</th>
                  <td>%s</td><input type=hidden name=additional_comments value="%s">
                </tr>
              </table>
             </td>
             <td width="200" align='center' valign='top'>
             </td>
                """ % (_("Request details"),
                       _("Budget code"), budget_code, budget_code,
                       _("Period of interest - From"),
                       period_of_interest_from, period_of_interest_from,
                       _("Period of interest - To"),
                       period_of_interest_to, period_of_interest_to,
                       _("Additional comments"),
                       additional_comments, additional_comments)

        if recid:
            out += """<input type=hidden name=recid value="%s">
                   """ % recid

        out += """
        <td valign='top' align='center'>
         <table>
            """

        if CFG_CERN_SITE == 1:
            out += """
                <tr>
                   <td class="bibcirctableheader" align="center">%s
                   """ % (_("Search user by"))

            if f == 'email':
                out += """
                   <input type="radio" name="f" value="ccid">%s
                   <input type="radio" name="f" value="name">%s
                   <input type="radio" name="f" value="email" checked>%s
                   """ % ('ccid', _('name'), _('email'))

            elif f == 'name':
                out += """
                   <input type="radio" name="f" value="ccid">%s
                   <input type="radio" name="f" value="name" checked>%s
                   <input type="radio" name="f" value="email">%s
                   """ % ('ccid', _('name'), _('email'))

            else:
                out += """
                   <input type="radio" name="f" value="ccid" checked>%s
                   <input type="radio" name="f" value="name">%s
                   <input type="radio" name="f" value="email">%s
                   """ % ('ccid', _('name'), _('email'))

        else:
            out += """
                 <tr>
                   <td align="center" class="bibcirctableheader">%s
                   """ % (_("Search borrower by"))

            if f == 'email':
                out += """
                   <input type="radio" name="f" value="id">%s
                   <input type="radio" name="f" value="name">%s
                   <input type="radio" name="f" value="email" checked>%s
                   """ % (_('id'), _('name'), _('email'))

            elif f == 'id':
                out += """
                   <input type="radio" name="f" value="id" checked>%s
                   <input type="radio" name="f" value="name">%s
                   <input type="radio" name="f" value="email">%s
                   """ % (_('id'), _('name'), _('email'))

            else:
                out += """
                   <input type="radio" name="f" value="id">%s
                   <input type="radio" name="f" value="name" checked>%s
                   <input type="radio" name="f" value="email">%s
                   """ % (_('id'), _('name'), _('email'))

        out += """
                    <br><br>
                    </td>
                    </tr>
                    <tr>
                        <td align="center">
                            <input type="text" size="40" id="string" name="p"
                                   value='%s'  style='border: 1px solid #cfcfcf'>
                        </td>
                    </tr>
                    <tr>
                        <td align="center">
                            <br>
                            <input type="submit" id="search_user" value="%s" class="formbutton">
                        </td>
                    </tr>
                   </table>
          </form>

        """ % (p or '', _("Search"))

        if result:
            out += """
            <br />
            <form name="step1_form2"
                  action="%s/admin2/bibcirculation/register_purchase_request_step3"
                  method="post" >
            <input type=hidden name=type value="%s">
            <input type=hidden name=title value="%s">
            <input type=hidden name=authors value="%s">
            <input type=hidden name=publisher value="%s">
            <input type=hidden name=year value="%s">
            """ % (CFG_SITE_URL, request_type, title, authors, publisher, year)

            if recid:
                out += """<input type=hidden name=recid value="%s">
                       """ % recid
            else:
                out += """<input type=hidden name=place value="%s">
                <input type=hidden name=edition value="%s">
                <input type=hidden name=this_edition_only value="%s">
                <input type=hidden name=standard_number value="%s">
                """ % (place, edition, this_edition_only, standard_number)

            out += """<input type=hidden name=isbn value="%s">
            <input type=hidden name=budget_code value="%s">
            <input type=hidden name=cash value="%s">
            <input type=hidden name=period_of_interest_from value="%s">
            <input type=hidden name=period_of_interest_to value="%s">
            <input type=hidden name=additional_comments value="%s">
            <table class="bibcirctable">
              <tr width="200">
                <td align="center">
                    <select name="borrower_id" size="8"
                          style='border: 1px solid #cfcfcf'>
            """ % (isbn, budget_code, cash, period_of_interest_from,
                   period_of_interest_to, additional_comments)

            for borrower_info in result:
                borrower_id = borrower_info[0]
                name = borrower_info[2]
                out += """
                       <option value =%s>%s</option>
                       """ % (borrower_id, name)

            out += """
                    </select>
                </td>
              </tr>
            </table>
            <table class="bibcirctable">
                <tr>
                    <td align="center">
                        <input type="submit" id="select_user" value='%s' class="formbutton">
                    </td>
                </tr>
            </table>

            </form>
            """ % (_("Select user"))

        out += """
                  </td>
                </tr>
              </table>
              <br />
              <br />
              <br />
              <br />
              </div>
              """

        return out


    def tmpl_ill_search(self, infos, ln=CFG_SITE_LANG):
        """
        Display form for ILL search

        @param infos: information
        @type infos: list

        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += load_menu(ln)

        out += """
        <div class="bibcircbottom">
        <link rel=\"stylesheet\" href=\"%(site_url)s/vendors/jquery-ui/themes/redmond/jquery-ui.min.css\" type=\"text/css\" />
        <link rel=\"stylesheet\" href=\"%(site_url)s/vendors/jquery-ui/themes/redmond/theme.css\" type=\"text/css\" />
        <script type="text/javascript"
                src="%(site_url)s/vendors/jquery-ui/jquery-ui.min.js"></script>
        <form name="search_form"
              action="%(site_url)s/admin2/bibcirculation/ill_search_result"
              method="get" >
        <br />
        <br />
        <br />
        """ % {'site_url': CFG_SITE_URL}

        out += """
        <table class="bibcirctable">
          <tr align="center">
            <td class="bibcirctableheader">%s
              <input type="radio" name="f" value="title" checked>%s
              <input type="radio" name="f" value="ILL_request_ID">%s
              <input type="radio" name="f" value="cost">%s
              <input type="radio" name="f" value="notes">%s
            </td>
          </tr>
        </table>

        <br />
        <table class="bibcirctable">
            <tr align="center" width=10>
                <td width=10>
                    <input type="text" size="50" name="p" id='p'
                           style='border: 1px solid #cfcfcf'>
                    <script language="javascript" type="text/javascript">
                        document.getElementById("p").focus();
                    </script>
                </td>
            </tr>
        </table>
        """ % (_("Search ILL request by"), _("ILL RecId/Item details"),
               _("ILL request id"), _("cost"), _("notes"))

        out += """
        <br />
        <table align="center">

            <tr align="center">
                <td class="bibcirctableheader" align="right">%s:    </td>
                <td class="bibcirctableheader" align="right">%s</td>
                <td align="left">
                <script type="text/javascript">
                    $(function(){
                        $("#date_picker1").datepicker({dateFormat: 'yy-mm-dd',
                        showOn: 'button', buttonImage: "%s/img/calendar.gif",
                        buttonImageOnly: true});
                    });
                </script>
                <input type="text" size="12" id="date_picker1" name="date_from"
                        value="%s" style='border: 1px solid #cfcfcf'>
                </td>
            </tr>

            <tr align="center">
                <td class="bibcirctableheader" align="right"></td>
                <td class="bibcirctableheader" align="right">%s</td>
                <td align="left">
                    <script type="text/javascript">
                        $(function(){
                            $("#date_picker2").datepicker({dateFormat: 'yy-mm-dd',
                            showOn: 'button', buttonImage: "%s/img/calendar.gif",
                            buttonImageOnly: true});
                        });
                    </script>
                    <input type="text" size="12" id="date_picker2" name="date_to"
                            value="%s" style='border: 1px solid #cfcfcf'>
                </td>
            </tr>
        </table>

        """ % (_("date restriction"),
               _("From"), CFG_SITE_URL, "the beginning",
               _("To"), CFG_SITE_URL, "now")

        out += """
        <br />
        <table class="bibcirctable">
          <tr align="center">
            <td>

              <input type=button value='%s'
              onClick="history.go(-1)" class="formbutton">
              <input type="submit" value='%s' class="formbutton">

            </td>
          </tr>
        </table>
        <br />
        <br />
        <br />
        <br />
        </div>
        <form>

        """ % (_("Back"), _("Search"))

        return out

    def tmpl_ill_request_details_step1(self, ill_request_id,
                                       ill_request_details, libraries,
                                       ill_request_borrower_details,
                                       ln=CFG_SITE_LANG):

        """
        @param ill_request_id: identify the ILL request. Primary key of crcILLREQUEST
        @type ill_request_id: int

        @param ill_req_details: information about a given ILL request
        @type ill_req_details: tuple

        @param libraries: list of libraries
        @type libraries: list

        @param ill_status: status of an ILL request
        @type ill_status: string

        @param ill_request_borrower_details: borrower's information
        @type ill_request_borrower_details: tuple
        """

        book_statuses = [CFG_BIBCIRCULATION_ILL_STATUS_NEW,
                         CFG_BIBCIRCULATION_ILL_STATUS_REQUESTED,
                         CFG_BIBCIRCULATION_ILL_STATUS_ON_LOAN,
                         CFG_BIBCIRCULATION_ILL_STATUS_RETURNED,
                         CFG_BIBCIRCULATION_ILL_STATUS_CANCELLED]

        article_statuses = [CFG_BIBCIRCULATION_ILL_STATUS_NEW,
                            CFG_BIBCIRCULATION_ILL_STATUS_REQUESTED,
                            CFG_BIBCIRCULATION_ILL_STATUS_RECEIVED,
                            CFG_BIBCIRCULATION_ILL_STATUS_CANCELLED]

        _ = gettext_set_language(ln)

        out = load_menu(ln)

        out += """
            <style type="text/css"> @import url("/css/tablesorter.css"); </style>
            <script type="text/javascript"
                    src="%s/vendors/jquery-ui/jquery-ui.min.js"></script>
            """% CFG_SITE_URL

        (_borrower_id, borrower_name, borrower_email, borrower_mailbox,
         period_from, period_to, item_info, borrower_comments,
         only_this_edition, request_type) = ill_request_borrower_details

        (library_id, request_date, expected_date, arrival_date, due_date,
         return_date, cost, barcode, library_notes,
         ill_status) = ill_request_details

        if library_notes == '' or library_notes == None:
            previous_library_notes = {}
        else:
            if looks_like_dictionary(library_notes):
                previous_library_notes = eval(library_notes)
            else:
                previous_library_notes = {}

        key_array = previous_library_notes.keys()
        key_array.sort()

        if looks_like_dictionary(item_info):
            item_info = eval(item_info)
        else:
            item_info = {}

        today = datetime.date.today()
        within_a_week = (datetime.date.today()
                          + datetime.timedelta(days=7)).strftime('%Y-%m-%d')
        within_a_month = (datetime.date.today()
                          + datetime.timedelta(days=30)).strftime('%Y-%m-%d')


        notes = ''
        for key in key_array:
            delete_note = create_html_link(CFG_SITE_URL +
                        '/admin2/bibcirculation/ill_request_details_step1',
                        {'delete_key': key, 'ill_request_id': ill_request_id,
                        'ln': ln}, (_("[delete]")))

            notes += """<tr class="bibcirccontent">
                            <td class="bibcircnotes" width="160" valign="top"
                                align="center"><b>%s</b></td>
                            <td width="400"><i>%s</i></td>
                            <td width="65" align="center">%s</td>
                        </tr>

                     """ % (key, previous_library_notes[key], delete_note)

        if library_id:
            library_name = db.get_library_name(library_id)
        else:
            library_name = '-'

        try:
            (book_title, book_year, book_author, book_isbn,
              book_editor) = book_information_from_MARC(int(item_info['recid']))

            if book_isbn:
                book_cover = get_book_cover(book_isbn)
            else:
                book_cover = """%s/img/book_cover_placeholder.gif
                                """ % (CFG_SITE_URL)

            out += """
            <form name="ill_req_form"
                  action="%s/admin2/bibcirculation/ill_request_details_step2" method="get" >
            <div class="bibcircbottom">
            <input type=hidden name=ill_request_id value="%s">
                <br />
                <table class="bibcirctable">
                    <tr>
                        <td class="bibcirctableheader" width="10">%s</td>
                    </tr>
                </table>
                <table class="bibcirctable">
                 <tr valign='top'>
                   <td width="400">
                    <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
                     <tr>
                        <th width="100">%s</th>
                        <td>%s</td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>%s</td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>%s</td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>%s</td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>%s</td>
                     </tr>
                    </table>
                   </td>
                   <input type=hidden name=recid value="%s">
                   <td class="bibcirccontent">
                       <img style='border: 1px solid #cfcfcf' src="%s" alt="Book Cover"/>
                   </td>
                 </tr>
              </table>
              <br />
              """ % (CFG_SITE_URL,
                      ill_request_id,
                      _("Item details"),
                      _("Name"),
                      book_title,
                      _("Author(s)"),
                      book_author,
                      _("Year"),
                      book_year,
                      _("Publisher"),
                      book_editor,
                      _("ISBN"),
                      book_isbn,
                      item_info['recid'],
                      str(book_cover))

        except KeyError:
            try:
                book_cover = get_book_cover(item_info['isbn'])
            except KeyError:
                book_cover = """%s/img/book_cover_placeholder.gif
                            """ % (CFG_SITE_URL)

            if str(request_type) == 'book':
                out += """
                <style type="text/css"> @import url("/css/tablesorter.css"); </style>
                <form name="ill_req_form"
                      action="%s/admin2/bibcirculation/ill_request_details_step2"
                      method="get">
                   <div class="bibcircbottom">
                   <input type=hidden name=ill_request_id value="%s">
                    <br />
                    <table class="bibcirctable">
                      <tr>
                        <td class="bibcirctableheader" width="10">%s</td>
                      </tr>
                    </table>
                    <table class="bibcirctable">
                     <tr valign='top'>
                       <td width="800">
                        <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
                         <tr>
                            <th width="100">%s</th>
                            <td>
                                <textarea name='title' rows="2"
                                    style='width:98%%; border: 1px solid #cfcfcf;'>%s</textarea>
                            </td>
                         </tr>
                         <tr>
                            <th width="100">%s</th>
                            <td>
                                <textarea name='authors' rows="1"
                                    style='width:98%%; border: 1px solid #cfcfcf;'>%s</textarea>
                            </td>
                         </tr>
                         <tr>
                            <th width="100">%s</th>
                            <td>
                                <textarea name='place' rows="1"
                                    style='width:98%%; border: 1px solid #cfcfcf;'>%s</textarea>
                            </td>
                         </tr>
                         <tr>
                            <th width="100">%s</th>
                            <td>
                                <textarea name='publisher' rows="1"
                                    style='width:98%%; border: 1px solid #cfcfcf;'>%s</textarea>
                            </td>
                         </tr>
                         <tr>
                            <th width="100">%s</th>
                            <td>
                                <textarea name='year' rows="1"
                                    style='width:98%%; border: 1px solid #cfcfcf;'>%s</textarea>
                            </td>
                         </tr>
                         <tr>
                            <th width="100">%s</th>
                            <td>
                                <textarea name='edition' rows="1"
                                    style='width:98%%; border: 1px solid #cfcfcf;'>%s</textarea>
                            </td>
                         </tr>
                          <tr>
                            <th width="100">%s</th>
                            <td>
                                <textarea name='isbn' rows="1"
                                    style='width:98%%; border: 1px solid #cfcfcf;'>%s</textarea>
                            </td>
                         </tr>
                        </table>
                      </td>
                        <td class="bibcirccontent">
                            <img style='border: 1px solid #cfcfcf' src="%s" alt="Book Cover"/>
                        </td>
                      </tr>
                  </table>
                  <br />
                  """ % (CFG_SITE_URL, ill_request_id,
                          _("Item details"),
                          _("Title"), item_info['title'],
                          _("Author(s)"), item_info['authors'],
                          _("Place"), item_info['place'],
                          _("Publisher"), item_info['publisher'],
                          _("Year"), item_info['year'],
                          _("Edition"), item_info['edition'],
                          _("ISBN"), item_info['isbn'],
                          str(book_cover))

            # for articles
            elif str(request_type) == 'article':
                out += """
                <style type="text/css"> @import url("/css/tablesorter.css"); </style>
                <form name="ill_req_form"
                      action="%s/admin2/bibcirculation/ill_request_details_step2" method="get" >
                   <div class="bibcircbottom">
                   <input type=hidden name=ill_request_id value="%s">
                    <br />
                    <table class="bibcirctable">
                      <tr>
                        <td class="bibcirctableheader" width="10">%s</td>
                      </tr>
                    </table>
                    <table class="bibcirctable">
                     <tr valign='top'>
                       <td width="800">
                        <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
                         <tr>
                            <th width="100">%s</th>
                            <td colspan="5">
                                <textarea name='periodical_title' rows="2"
                                    style='width:98%%; border: 1px solid #cfcfcf;'>%s</textarea>
                            </td>
                         </tr>
                         <tr>
                            <th width="100">%s</th>
                            <td colspan="5">
                                <textarea name='title' rows="2"
                                    style='width:98%%; border: 1px solid #cfcfcf;'>%s</textarea>
                            </td>
                         </tr>
                         <tr>
                            <th width="100">%s</th>
                            <td colspan="5">
                                <textarea name='authors' rows="1"
                                    style='width:98%%; border: 1px solid #cfcfcf;'>%s</textarea>
                            </td>
                         </tr>

                         <tr>
                            <th width="100">%s</th>
                            <td>
                                <textarea name='volume' rows="1"
                                          style='width:91%%;
                                          border: 1px solid #cfcfcf;'>%s</textarea>
                            </td>
                            <th width="50" align='right'>%s</th>
                            <td>
                                <textarea name='issue' rows="1"
                                          style='width:91%%;
                                          border: 1px solid #cfcfcf;'>%s</textarea>
                            </td>
                            <th width="50" align='right'>%s</th>
                            <td>
                                <textarea name='page' rows="1"
                                          style='width:91%%;
                                          border: 1px solid #cfcfcf;'>%s</textarea>
                            </td>
                         </tr>

                         <tr>
                            <th width="100">%s</th>
                            <td colspan="3">
                                <textarea name='place' rows="1"
                                    style='width:96%%; border: 1px solid #cfcfcf;'>%s</textarea>
                            </td>
                            <th width="50" align='right'>%s</th>
                            <td>
                                <textarea name='issn' rows="1"
                                    style='width:91%%; border: 1px solid #cfcfcf;'>%s</textarea>
                            </td>
                         </tr>
                         <tr>
                            <th width="100">%s</th>
                            <td colspan="3">
                                <textarea name='publisher' rows="1"
                                    style='width:96%%; border: 1px solid #cfcfcf;'>%s</textarea>
                            </td>
                            <th width="50" align='right'>%s</th>
                            <td>
                                <textarea name='year' rows="1"
                                    style='width:91%%; border: 1px solid #cfcfcf;'>%s</textarea>
                            </td>
                         </tr>
                        </table>
                      </td>
                      <td class="bibcirccontent">
                        <img style='border: 1px solid #cfcfcf' src="%s" alt="Book Cover"/>
                      </td>
                      </tr>
                  </table>
                  <br />
                  """ % (CFG_SITE_URL,
                         ill_request_id,
                         _("Item details"),
                         _("Periodical Title"), item_info['periodical_title'],
                         _("Article Title"), item_info['title'],
                         _("Author(s)"), item_info['authors'],
                         _("Volume"), item_info['volume'],
                         _("Issue"), item_info['issue'],
                         _("Page"), item_info['page'],
                         _("Place"), item_info['place'],
                         _("ISSN"), item_info['issn'],
                         _("Publisher"), item_info['publisher'],
                         _("Year"), item_info['year'],
                         str(book_cover))

            elif str(request_type) == 'acq-book':
                out += """
                <style type="text/css"> @import url("/css/tablesorter.css"); </style>
                <form name="ill_req_form"
                      action="%s/admin2/bibcirculation/ill_request_details_step2"
                      method="get">
                   <div class="bibcircbottom">
                   <input type=hidden name=ill_request_id value="%s">
                    <br />
                    <table class="bibcirctable">
                      <tr>
                        <td class="bibcirctableheader" width="10">%s</td>
                      </tr>
                    </table>
                    <table class="bibcirctable">
                     <tr valign='top'>
                       <td width="800">
                        <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
                         <tr>
                            <th width="100">%s</th>
                            <td>
                                <textarea name='title' rows="2"
                                    style='width:98%%; border: 1px solid #cfcfcf;'>%s</textarea>
                            </td>
                         </tr>
                         <tr>
                            <th width="100">%s</th>
                            <td>
                                <textarea name='authors' rows="1"
                                    style='width:98%%; border: 1px solid #cfcfcf;'>%s</textarea>
                            </td>
                         </tr>
                         <tr>
                            <th width="100">%s</th>
                            <td>
                                <textarea name='place' rows="1"
                                    style='width:98%%; border: 1px solid #cfcfcf;'>%s</textarea>
                            </td>
                         </tr>
                         <tr>
                            <th width="100">%s</th>
                            <td>
                                <textarea name='publisher' rows="1"
                                    style='width:98%%; border: 1px solid #cfcfcf;'>%s</textarea>
                            </td>
                         </tr>
                         <tr>
                            <th width="100">%s</th>
                            <td>
                                <textarea name='year' rows="1"
                                    style='width:98%%; border: 1px solid #cfcfcf;'>%s</textarea>
                            </td>
                         </tr>
                         <tr>
                            <th width="100">%s</th>
                            <td>
                                <textarea name='edition' rows="1"
                                    style='width:98%%; border: 1px solid #cfcfcf;'>%s</textarea>
                            </td>
                         </tr>
                          <tr>
                            <th width="100">%s</th>
                            <td>
                                <textarea name='isbn' rows="1"
                                    style='width:98%%; border: 1px solid #cfcfcf;'>%s</textarea>
                            </td>
                         </tr>
                        </table>
                      </td>
                        <td class="bibcirccontent">
                            <img style='border: 1px solid #cfcfcf' src="%s" alt="Book Cover"/>
                        </td>
                      </tr>
                  </table>
                  <br />
                  """ % (CFG_SITE_URL, ill_request_id,
                          _("Item details"),
                          _("Title"), item_info['title'],
                          _("Author(s)"), item_info['authors'],
                          _("Place"), item_info['place'],
                          _("Publisher"), item_info['publisher'],
                          _("Year"), item_info['year'],
                          _("Edition"), item_info['edition'],
                          _("ISBN"), item_info['isbn'],
                          str(book_cover))

            else:
                out += """Wrong type."""

        out += """
        <table class="bibcirctable">
          <tr valign='top'>
            <td width="550">
              <table>
                <tr>
                  <td class="bibcirctableheader">%s</td>
                </tr>
              </table>
              <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
                <tr>
                  <th width="150">%s</th>
                  <td>%s</td>
                </tr>
                <tr>
                  <th width="150">%s</th>
                  <td>%s</td>
                </tr>
                <tr>
                  <th width="150">%s</th>
                  <td>%s</td>
                </tr>
                <tr>
                  <th width="150">%s</th>
                  <td>%s</td>
                </tr>
                <tr>
                  <th width="150">%s</th>
                  <td>%s</td>
                </tr>
                <tr>
                   <th width="150">%s</th>
                   <td width="350"><i>%s</i></td>
                </tr>
                <tr>
                  <th width="150">%s</th>
                  <td>%s</td>
                </tr>
              </table>
              </td>
              <td>
              <table>
                <tr>
                     <td class="bibcirctableheader">%s</td>
                </tr>
             </table>

             """ % (_("Borrower request"), _("Name"), borrower_name,
                    _("Email"), borrower_email,
                    _("Mailbox"), borrower_mailbox,
                    _("Period of interest (From)"), period_from,
                    _("Period of interest (To)"), period_to,
                    _("Borrower comments"), borrower_comments or '-',
                    _("Only this edition?"), only_this_edition or 'No',
                    _("ILL request details"))


        out += """
                        <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
                            <tr>
                                <input type=hidden name=new_status value="%s">
                              <th width="100">%s</th>
                              <td>
                                <select style='border: 1px solid #cfcfcf'
                                onchange="location = this.options[this.selectedIndex].value;">
             """ % (ill_status, _("Status"))

        statuses = []

        if request_type == 'book':
            statuses = book_statuses
        elif request_type in CFG_BIBCIRCULATION_ACQ_TYPE:
            statuses = CFG_BIBCIRCULATION_ACQ_STATUS
        elif request_type in CFG_BIBCIRCULATION_PROPOSAL_TYPE:
            statuses = CFG_BIBCIRCULATION_PROPOSAL_STATUS
        elif request_type == 'article':
            statuses = article_statuses

        for status in statuses:
            if status == ill_status:
                out += """
            <option value ="ill_request_details_step1?ill_request_id=%s&new_status=%s" selected>
                    %s
                    </option>
            """ % (ill_request_id, status, status)
            else:
                out += """
            <option value ="ill_request_details_step1?ill_request_id=%s&new_status=%s">
                    %s
                    </option>
            """ % (ill_request_id, status, status)

        out += """
                                </select>
                              </td>
                            </tr>
            """

#### NEW ####
        if ill_status == CFG_BIBCIRCULATION_ILL_STATUS_NEW \
           or ill_status == None \
           or ill_status == '':

            out += """
                            <tr>
                              <th width="150">%s</th>
                              <td>%s</td>
                            </tr>
                            <tr>
                              <th width="100" valign="top">%s</th>
                              <td>
                                <table class="bibcircnotes">
                        """ % (_("ILL request ID"), ill_request_id,
                               _("Previous notes"))

            out += notes

            out += """
                            </table>
                          </td>
                        </tr>
                        <tr>
                          <th valign="top" width="100">%s</th>
                          <td>
                            <textarea name='library_notes' rows="6" cols="74"
                                      style='border: 1px solid #cfcfcf'>
                            </textarea>
                          </td>
                        </tr>
                      </table>
                    </td>
                  </tr>
                </table>

                      """ % (_("Library notes"))

############# REQUESTED ##############
        elif ill_status ==  CFG_BIBCIRCULATION_ILL_STATUS_REQUESTED:

            out += """
                            <tr>
                              <th width="150">%s</th>
                              <td class="bibcirccontent">%s</td>
                            </tr>
                        """ % (_("ILL request ID"), ill_request_id)

            out += """
                            <tr>
                              <th width="150">%s</th>
                              <td class="bibcirccontent">
                                <select name="library_id"  style='border: 1px solid #cfcfcf'>
            """ % (_("Library/Supplier"))

            for(lib_id, name) in libraries:
                if lib_id == library_id:
                    out += """       <option value="%s" selected>%s</option>
                            """ % (lib_id, name)
                else:
                    out += """       <option value="%s">%s</option>
                            """ % (lib_id, name)

            out += """
                         </select>
                       </td>
                     </tr>
                     <tr>
                       <th width="150">%s</th>
                       <td class="bibcirccontent">

                        <script type="text/javascript">
                             $(function() {
                                 $("#date_picker1").datepicker({dateFormat: 'yy-mm-dd', showOn: 'button', buttonImage: "%s/img/calendar.gif", buttonImageOnly: true});
                             });
                        </script>
                        <input type="text" size="10" id="date_picker1"
                               name="request_date" value="%s" style='border: 1px solid #cfcfcf'>

                      </td>
                    </tr>
                    <tr>
                      <th width="150">%s</th>
                      <td class="bibcirccontent">

                        <script type="text/javascript">
                             $(function() {
                                 $("#date_picker2").datepicker({dateFormat: 'yy-mm-dd', showOn: 'button', buttonImage: "%s/img/calendar.gif", buttonImageOnly: true});
                             });
                        </script>
                        <input type="text" size="10" id="date_picker2"
                               name="expected_date" value="%s" style='border: 1px solid #cfcfcf'>

                      </td>
                    </tr>
                    <tr>
                      <th width="100">%s</th>
                      <td class="bibcirccontent">
                        <input type="text" size="12" name="cost"
                               value="%s" style='border: 1px solid #cfcfcf'>
                        """ % (_("Request date"),
                               CFG_SITE_URL, today,
                               _("Expected date"),
                               CFG_SITE_URL, within_a_week,
                               _("Cost"), cost)

            out += """
                      </td>
                    </tr>
                    <tr>
                      <th width="100">%s</th>
                      <td class="bibcirccontent"><input type="text" size="12" name="barcode"
                          value="%s" style='border: 1px solid #cfcfcf'>
                      </td>
                    </tr>
                    <tr>
                          <th width="100" valign="top">%s</th>
                          <td>
                            <table class="bibcircnotes">
                    """ % (_("Barcode"), barcode or 'No barcode associated',
                           _("Previous notes"))

            out += notes

            out += """
                            </table>
                          </td>
                        </tr>
                    <tr>
                       <th valign="top" width="150">%s</th>
                          <td>
                            <textarea name='library_notes' rows="6" cols="74"
                                      style='border: 1px solid #cfcfcf'></textarea>
                          </td>
                     </tr>
                   </table>
                 </td>
               </tr>
             </table>

                      """ % (_("Library notes"))

##### ON LOAN ##############
        elif ill_status == CFG_BIBCIRCULATION_ITEM_STATUS_ON_LOAN:

            out += """
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent">%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent">%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent">%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent">%s</td>
                        </tr>
                    """ % (_("ILL request ID"), ill_request_id, _("Library"),
                           library_name, _("Request date"), request_date,
                           _("Expected date"), expected_date)

            if str(arrival_date) == '0000-00-00':
                date1 = today
            else:
                date1 = arrival_date

            if str(due_date) == '0000-00-00':
                date2 = within_a_month
            else:
                date2 = due_date


            out += """
                    <tr>
                       <th width="150">%s</th>
                       <td class="bibcirccontent">

                        <script type="text/javascript">
                             $(function() {
                                 $("#date_picker1").datepicker({dateFormat: 'yy-mm-dd', showOn: 'button', buttonImage: "%s/img/calendar.gif", buttonImageOnly: true});
                             });
                        </script>
                        <input type="text" size="10" id="date_picker1" name="arrival_date" value="%s" style='border: 1px solid #cfcfcf'>

                      </td>
                    </tr>
                    <tr>
                      <th width="150">%s</th>
                      <td class="bibcirccontent">

                        <script type="text/javascript">
                             $(function() {
                                 $("#date_picker2").datepicker({dateFormat: 'yy-mm-dd', showOn: 'button', buttonImage: "%s/img/calendar.gif", buttonImageOnly: true});
                             });
                        </script>
                        <input type="text" size="10" id="date_picker2" name="due_date" value="%s" style='border: 1px solid #cfcfcf'>
                        <input type="hidden" name="request_date" value="%s">
                        <input type="hidden" name="expected_date" value="%s">
                        <input type="hidden" name="library_id" value="%s">
                      </td>
                    </tr>
            """ % (_("Arrival date"), CFG_SITE_URL, date1, _("Due date"),
                CFG_SITE_URL, date2, request_date, expected_date, library_id)

            out += """
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent"><input type="text" size="12" name="cost" value="%s" style='border: 1px solid #cfcfcf'>
                    """ % (_("Cost"), cost)
            out += """
                          </td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent"><input type="text" size="12" name="barcode" value="%s" style='border: 1px solid #cfcfcf'>
                        </tr>
                        <tr>
                          <th width="100" valign="top">%s</th>
                          <td>
                            <table class="bibcircnotes">
                        """ % (_("Barcode"), barcode, _("Previous notes"))

            out += notes


            out += """
                            </table>
                          </td>
                        </tr>
                        <tr>
                          <th valign="top" width="100">%s</th>
                          <td><textarea name='library_notes' rows="6" cols="74" style='border: 1px solid #cfcfcf'></textarea></td>
                        </tr>
                      </table>
                     </td>
                   </tr>
                 </table>

                      """ % (_("Library notes"))


##### RETURNED ##############
        elif ill_status == CFG_BIBCIRCULATION_ILL_STATUS_RETURNED or \
             ill_status == CFG_BIBCIRCULATION_ILL_STATUS_CANCELLED:

            date1 = return_date

            if ill_status == CFG_BIBCIRCULATION_ILL_STATUS_RETURNED and \
               str(return_date)=='0000-00-00':
                date1 = today

            out += """
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent">%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent">%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent">%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent">%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent">%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent">%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent">
                            <script type="text/javascript">
                                $(function() {
                                    $("#date_picker1").datepicker({dateFormat: 'yy-mm-dd',
                                        showOn: 'button', buttonImage: "%s/img/calendar.gif",
                                        buttonImageOnly: true});
                                });
                            </script>
                            <input type="text" size="10" id="date_picker1" name="return_date"
                                   value="%s" style='border: 1px solid #cfcfcf'>
                            <input type="hidden" name="request_date"  value="%s">
                            <input type="hidden" name="expected_date" value="%s">
                            <input type="hidden" name="arrival_date"  value="%s">
                            <input type="hidden" name="due_date"      value="%s">
                            <input type="hidden" name="library_id"    value="%s">
                          </td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent">
                            <input type="text" size="12" name="cost"
                                   value="%s" style='border: 1px solid #cfcfcf'>
        """ % (_("ILL request ID"), ill_request_id, _("Library"),
            library_name, _("Request date"), request_date, _("Expected date"),
            expected_date, _("Arrival date"), arrival_date, _("Due date"),
            due_date, _("Return date"), CFG_SITE_URL, date1, request_date,
            expected_date, arrival_date, due_date, library_id, _("Cost"), cost)

            out += """
                            </select>
                          </td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent">%s</td>
                        </tr>
                        <tr>
                          <th width="100" valign="top">%s</th>
                          <td>
                            <table class="bibcircnotes">
                    """ % (_("Barcode"), barcode, _("Previous notes"))

            out += notes

            out += """
                            </table>
                          </td>
                        </tr>
                        <tr>
                          <th valign="top" width="100">%s</th>
                          <td>
                            <textarea name='library_notes' rows="6" cols="74"
                                      style='border: 1px solid #cfcfcf'></textarea>
                          </td>
                        </tr>
                      </table>
                     </td>
                   </tr>
                 </table>

                      """ % (_("Library notes"))

##### RECEIVED ##############
        elif ill_status == CFG_BIBCIRCULATION_ILL_STATUS_RECEIVED:
            if str(arrival_date) == '0000-00-00':
                date1 = today
            else:
                date1 = arrival_date

            out += """
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent">%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent">%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent">%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent">%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent">
                            <script type="text/javascript">
                                $(function() {
                                    $("#date_picker1").datepicker({dateFormat: 'yy-mm-dd',
                                        showOn: 'button', buttonImage: "%s/img/calendar.gif",
                                        buttonImageOnly: true});
                                });
                            </script>
                            <input type="text" size="10" id="date_picker1"
                               name="arrival_date" value="%s" style='border: 1px solid #cfcfcf'>
                            <input type="hidden" name="request_date" value="%s">
                            <input type="hidden" name="expected_date" value="%s">
                            <input type="hidden" name="library_id" value="%s">
                          </td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent"><input type="text" size="12"
                              name="cost" value="%s" style='border: 1px solid #cfcfcf'>
        """ % (_("ILL request ID"), ill_request_id, _("Library"), library_name,
            _("Request date"), request_date, _("Expected date"), expected_date,
            _("Arrival date"), CFG_SITE_URL, date1, request_date, expected_date,
            library_id, _("Cost"), cost)

            out += """
                          </td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent">%s</td>
                        </tr>
                        <tr>
                          <th width="100" valign="top">%s</th>
                          <td>
                            <table class="bibcircnotes">
                """ % (_("Barcode"), barcode, _("Previous notes"))

            out += notes

            out += """
                            </table>
                          </td>
                        </tr>
                        <tr>
                          <th valign="top" width="100">%s</th>
                          <td>
                            <textarea name='library_notes' rows="6" cols="74"
                                      style='border: 1px solid #cfcfcf'></textarea>
                          </td>
                        </tr>
                      </table>
                     </td>
                   </tr>
                 </table>

                      """ % (_("Library notes"))

###### END STATUSES ######

        out += """
             <br />
             <table class="bibcirctable">
                <tr>
                  <td>
                       <input type=button value="%s"
                              onClick="history.go(-1)" class="formbutton">
                       <input type="submit"
                              value="%s" class="formbutton">
                  </td>
                 </tr>
             </table>
             </div>
             </form>
             <br />
             <br />
               """ % (_("Back"), _("Continue"))

        return out

    def tmpl_purchase_details_step1(self, ill_request_id,
                                     ill_request_details, libraries,
                                     ill_request_borrower_details,
                                     ln=CFG_SITE_LANG):

        _ = gettext_set_language(ln)

        out = load_menu(ln)

        out += """
            <style  type="text/css"> @import url("/css/tablesorter.css"); </style>
            <script type="text/javascript" src="%s/vendors/jquery-ui/jquery-ui.min.js"></script>
            """% CFG_SITE_URL

        (_borrower_id, borrower_name, borrower_email,
         borrower_mailbox, period_from, period_to,
         item_info, borrower_comments, only_this_edition,
         budget_code, request_type) = ill_request_borrower_details

        (library_id, request_date, expected_date, arrival_date, due_date,
         return_date, cost, _barcode, library_notes,
         ill_status) = ill_request_details

        if library_notes == '' or library_notes == None:
            previous_library_notes = {}
        else:
            if looks_like_dictionary(library_notes):
                previous_library_notes = eval(library_notes)
            else:
                previous_library_notes = {}

        key_array = previous_library_notes.keys()
        key_array.sort()

        if looks_like_dictionary(item_info):
            item_info = eval(item_info)
        else:
            item_info = {}

        today = datetime.date.today()
        within_a_week = (datetime.date.today()
                       + datetime.timedelta(days=7)).strftime('%Y-%m-%d')
        within_a_month = (datetime.date.today()
                        + datetime.timedelta(days=30)).strftime('%Y-%m-%d')

        notes = ''
        for key in key_array:
            delete_note = create_html_link(CFG_SITE_URL +
                        '/admin2/bibcirculation/purchase_details_step1',
                        {'delete_key': key, 'ill_request_id': ill_request_id,
                        'ln': ln}, (_("[delete]")))

            notes += """<tr class="bibcirccontent">
                            <td class="bibcircnotes" width="160" valign="top"
                                align="center"><b>%s</b></td>
                            <td width="400"><i>%s</i></td>
                            <td width="65" align="center">%s</td>
                        </tr>
                     """ % (key, previous_library_notes[key], delete_note)

        if library_id:
            library_name = db.get_vendor_name(library_id)
        else:
            library_name = '-'

        try:
            (book_title, book_year, book_author, book_isbn,
             book_editor) = book_information_from_MARC(int(item_info['recid']))

            if book_isbn:
                book_cover = get_book_cover(book_isbn)
            else:
                book_cover = """%s/img/book_cover_placeholder.gif
                                """ % (CFG_SITE_URL)

            out += """
            <form name="ill_req_form"
                  action="%s/admin2/bibcirculation/purchase_details_step2" method="get" >
            <div class="bibcircbottom">
            <input type=hidden name=ill_request_id value="%s">
                <br />
                <table class="bibcirctable">
                    <tr>
                        <td class="bibcirctableheader" width="10">%s</td>
                    </tr>
                </table>
                <table class="bibcirctable">
                 <tr valign='top'>
                   <td width="400">
                    <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
                     <tr>
                        <th width="100">%s</th>
                        <td>%s</td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>%s</td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>%s</td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>%s</td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>%s</td>
                     </tr>
                    </table>
                   </td>
                   <input type=hidden name=recid value="%s">
                   <td class="bibcirccontent">
                       <img style='border: 1px solid #cfcfcf' src="%s" alt="Book Cover"/>
                   </td>
                 </tr>
                </table>
                <br />
              """ % (CFG_SITE_URL,
                      ill_request_id,
                      _("Item details"),
                      _("Name"),
                      book_title,
                      _("Author(s)"),
                      book_author,
                      _("Year"),
                      book_year,
                      _("Publisher"),
                      book_editor,
                      _("ISBN"),
                      book_isbn,
                      item_info['recid'],
                      str(book_cover))

        except KeyError:
            try:
                book_cover = get_book_cover(item_info['isbn'])
            except KeyError:
                book_cover = """%s/img/book_cover_placeholder.gif
                            """ % (CFG_SITE_URL)

            if str(request_type) in CFG_BIBCIRCULATION_ACQ_TYPE or \
               str(request_type) in CFG_BIBCIRCULATION_PROPOSAL_TYPE:
                out += """
                <style type="text/css"> @import url("/css/tablesorter.css"); </style>
                <form name="ill_req_form"
                      action="%s/admin2/bibcirculation/purchase_details_step2"
                      method="get">
                   <div class="bibcircbottom">
                   <input type=hidden name=ill_request_id value="%s">
                    <br />
                    <table class="bibcirctable">
                      <tr>
                        <td class="bibcirctableheader" width="10">%s</td>
                      </tr>
                    </table>
                    <table class="bibcirctable">
                     <tr valign='top'>
                       <td width="800">
                        <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
                         <tr>
                            <th width="100">%s</th>
                            <td>
                                <textarea name='title' rows="2"
                                    style='width:98%%; border: 1px solid #cfcfcf;'>%s</textarea>
                            </td>
                         </tr>
                         <tr>
                            <th width="100">%s</th>
                            <td>
                                <textarea name='authors' rows="1"
                                    style='width:98%%; border: 1px solid #cfcfcf;'>%s</textarea>
                            </td>
                         </tr>
                         <tr>
                            <th width="100">%s</th>
                            <td>
                                <textarea name='place' rows="1"
                                    style='width:98%%; border: 1px solid #cfcfcf;'>%s</textarea>
                            </td>
                         </tr>
                         <tr>
                            <th width="100">%s</th>
                            <td>
                                <textarea name='publisher' rows="1"
                                    style='width:98%%; border: 1px solid #cfcfcf;'>%s</textarea>
                            </td>
                         </tr>
                         <tr>
                            <th width="100">%s</th>
                            <td>
                                <textarea name='year' rows="1"
                                    style='width:98%%; border: 1px solid #cfcfcf;'>%s</textarea>
                            </td>
                         </tr>
                         <tr>
                            <th width="100">%s</th>
                            <td>
                                <textarea name='edition' rows="1"
                                    style='width:98%%; border: 1px solid #cfcfcf;'>%s</textarea>
                            </td>
                         </tr>
                         <tr>
                            <th width="100">%s</th>
                            <td>
                                <textarea name='isbn' rows="1"
                                    style='width:98%%; border: 1px solid #cfcfcf;'>%s</textarea>
                            </td>
                         </tr>
                         <tr>
                            <th width="100">%s</th>
                            <td>
                                <textarea name='standard_number' rows="1"
                                    style='width:98%%; border: 1px solid #cfcfcf;'>%s</textarea>
                            </td>
                         </tr>
                        </table>
                      </td>
                        <td class="bibcirccontent">
                            <img style='border: 1px solid #cfcfcf' src="%s" alt="Book Cover"/>
                        </td>
                      </tr>
                  </table>
                  <br />
                  """ % (CFG_SITE_URL, ill_request_id,
                          _("Item details"),
                          _("Title"), item_info['title'],
                          _("Author(s)"), item_info['authors'],
                          _("Place"), item_info['place'],
                          _("Publisher"), item_info['publisher'],
                          _("Year"), item_info['year'],
                          _("Edition"), item_info['edition'],
                          _("ISBN"), item_info['isbn'],
                          _("Standard number"), item_info['standard_number'],
                          str(book_cover))

            else:
                out += """Wrong type."""

        out += """
        <table class="bibcirctable">
          <tr valign='top'>
            <td width="550">
              <table>
                <tr>
                  <td class="bibcirctableheader">%s</td>
                </tr>
              </table>
              <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
                <tr>
                  <th width="150">%s</th>
                  <td>%s</td>
                </tr>
                <tr>
                  <th width="150">%s</th>
                  <td>%s</td>
                </tr>
                <tr>
                  <th width="150">%s</th>
                  <td>%s</td>
                </tr>""" % (_("Borrower request"), _("Name"), borrower_name,
                            _("Email"), borrower_email,
                            _("Mailbox"), borrower_mailbox)

        if request_type not in CFG_BIBCIRCULATION_PROPOSAL_TYPE:
            out += """<tr>
                  <th width="150">%s</th>
                  <td>%s</td>
                </tr>
                <tr>
                  <th width="150">%s</th>
                  <td>%s</td>
                </tr>
                <tr>
                  <th width="150">%s</th>
                  <td>%s</td>
                </tr>""" % (_("Period of interest (From)"), period_from,
                            _("Period of interest (To)"), period_to,
                            _("Only this edition?"), only_this_edition or 'No')
        else:
            out += """<tr>
                  <th width="150">%s</th>
                  <td>%s</td>
                </tr>""" % (_("Date of request"), period_from)

        out += """<tr>
                   <th width="150">%s</th>
                   <td width="350"><i>%s</i></td>
                </tr>
              </table>
              </td>
              <td>
              <table>
                <tr>
                     <td class="bibcirctableheader">%s</td>
                </tr>
             </table> """ % (_("Borrower comments"), borrower_comments or '-',
                            _("Request details"))

        out += """
                        <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
                            <tr>
                                <input type=hidden name=new_status value="%s">
                              <th width="100">%s</th>
                              <td colspan="3">
                                <select style='border: 1px solid #cfcfcf'
                                onchange="location = this.options[this.selectedIndex].value;">
             """ % (ill_status, _("Status"))

        statuses = []
        if request_type in CFG_BIBCIRCULATION_ACQ_TYPE:
            statuses = CFG_BIBCIRCULATION_ACQ_STATUS
        elif request_type in CFG_BIBCIRCULATION_PROPOSAL_TYPE:
            statuses = CFG_BIBCIRCULATION_PROPOSAL_STATUS

        for status in statuses:
            if status == ill_status:
                out += """
            <option value ="purchase_details_step1?ill_request_id=%s&new_status=%s" selected>
                    %s
                    </option>
            """ % (ill_request_id, status, status)
            else:
                out += """
            <option value ="purchase_details_step1?ill_request_id=%s&new_status=%s">
                    %s
                    </option>
            """ % (ill_request_id, status, status)

        out += """
                                </select>
                              </td>
                            </tr>
            """

######## NEW ########
        if ill_status == CFG_BIBCIRCULATION_ACQ_STATUS_NEW \
           or ill_status == CFG_BIBCIRCULATION_PROPOSAL_STATUS_NEW \
           or ill_status == CFG_BIBCIRCULATION_PROPOSAL_STATUS_PUT_ASIDE \
           or ill_status == None \
           or ill_status == '':

            out += """
                            <tr>
                              <th width="150">%s</th>
                              <td>%s</td>
                              <th width="150">%s</th>
                              <td>%s</td>
                            </tr>
                            <tr>
                              <th width="150">%s</th>
                              <td colspan="3">
                                <input type="text" size="12"
                                       name="budget_code"
                                       value="%s"
                                       style='border: 1px solid #cfcfcf'>
                              </td>
                            </tr>
                            <tr>
                              <th width="100" valign="top">%s</th>
                              <td colspan="3">
                                <table class="bibcircnotes">
                    """ % (_("ILL request ID"), ill_request_id,
                           _("Type"), request_type,
                           _("Budget code"), budget_code,
                           _("Previous notes"))

            out += notes

            out += """
                            </table>
                          </td>
                        </tr>
                        <tr>
                          <th valign="top" width="100">%s</th>
                          <td colspan="3">
                            <textarea name='library_notes' rows="6" cols="74"
                                      style='border: 1px solid #cfcfcf'>
                            </textarea>
                          </td>
                        </tr>
                      </table>
                    </td>
                  </tr>
                </table>
                      """ % (_("Library notes"))

############# ON ORDER ##############
        elif ill_status ==  CFG_BIBCIRCULATION_ACQ_STATUS_ON_ORDER \
             or ill_status == CFG_BIBCIRCULATION_PROPOSAL_STATUS_ON_ORDER:

            out += """
                            <tr>
                              <th width="150">%s</th>
                              <td class="bibcirccontent">%s</td>
                              <th width="150">%s</th>
                              <td class="bibcirccontent">%s</td>
                            </tr>
                        """ % (_("ILL request ID"), ill_request_id,
                               _("Type"), request_type)

            out += """
                            <tr>
                              <th width="150">%s</th>
                              <td class="bibcirccontent" colspan="3">
                                <select name="library_id"  style='border: 1px solid #cfcfcf'>
                        """ % (_("Vendor"))

            for(lib_id, name) in libraries:
                if lib_id == library_id:
                    out += """       <option value="%s" selected>%s</option>
                            """ % (lib_id, name)
                else:
                    out += """       <option value="%s">%s</option>
                            """ % (lib_id, name)

            out += """
                         </select>
                       </td>
                     </tr>
                     <tr>
                       <th width="150">%s</th>
                       <td class="bibcirccontent" colspan="3">

                        <script type="text/javascript">
                             $(function(){
                                 $("#date_picker1").datepicker({dateFormat: 'yy-mm-dd',
                                   showOn: 'button', buttonImage: "%s/img/calendar.gif",
                                   buttonImageOnly: true});
                             });
                        </script>
                        <input type="text" size="10" id="date_picker1"
                               name="request_date" value="%s" style='border: 1px solid #cfcfcf'>

                      </td>
                    </tr>
                    <tr>
                      <th width="150">%s</th>
                      <td class="bibcirccontent" colspan="3">
                        <script type="text/javascript">
                             $(function() {
                                 $("#date_picker2").datepicker({dateFormat: 'yy-mm-dd',
                                        showOn: 'button', buttonImage: "%s/img/calendar.gif",
                                        buttonImageOnly: true});
                             });
                        </script>
                        <input type="text" size="10" id="date_picker2"
                               name="expected_date" value="%s" style='border: 1px solid #cfcfcf'>

                      </td>
                    </tr>
                    <tr>
                      <th width="100">%s</th>
                      <td class="bibcirccontent" colspan="3">
                        <input type="text" size="12" name="cost"
                               value="%s" style='border: 1px solid #cfcfcf'>
                        """ % (_("Request date"),
                               CFG_SITE_URL, today,
                               _("Expected date"),
                               CFG_SITE_URL, within_a_week,
                               _("Cost"), cost)

            out += """
                      </td>
                    </tr>
                    <tr>
                      <th width="100">%s</th>
                      <td class="bibcirccontent" colspan="3">
                            <input type="text" size="12" name="budget_code"
                                   value="%s" style='border: 1px solid #cfcfcf'>
                      </td>
                    </tr>
                    <tr>
                          <th width="100" valign="top">%s</th>
                          <td colspan="3">
                            <table class="bibcircnotes">
                    """ % (_("Budget code"), budget_code,
                           _("Previous notes"))

            out += notes

            out += """
                            </table>
                          </td>
                    </tr>
                    <tr>
                        <th valign="top" width="150">%s</th>
                            <td colspan="3">
                                <textarea name='library_notes' rows="6" cols="74"
                                          style='border: 1px solid #cfcfcf'></textarea>
                            </td>
                    </tr>
                   </table>
                 </td>
               </tr>
             </table>
                      """ % (_("Library notes"))

##### PARTIAL RECEIPT ##############
        elif ill_status == CFG_BIBCIRCULATION_ACQ_STATUS_PARTIAL_RECEIPT:

            out += """
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent">%s</td>
                          <th width="100">%s</th>
                          <td class="bibcirccontent">%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent" colspan="3">%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent" colspan="3">%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent" colspan="3">%s</td>
                        </tr>
                    """ % (_("ILL request ID"), ill_request_id,
                           _("Type"), request_type, _("Library"),
                           library_name, _("Request date"), request_date,
                           _("Expected date"), expected_date)

            if str(arrival_date) == '0000-00-00':
                date1 = today
            else:
                date1 = arrival_date

            if str(due_date) == '0000-00-00':
                date2 = within_a_month
            else:
                date2 = due_date


            out += """
                    <tr>
                       <th width="150">%s</th>
                       <td class="bibcirccontent" colspan="3">

                        <script type="text/javascript">
                             $(function() {
                                 $("#date_picker1").datepicker({dateFormat: 'yy-mm-dd', showOn: 'button', buttonImage: "%s/img/calendar.gif", buttonImageOnly: true});
                             });
                        </script>
                        <input type="text" size="10" id="date_picker1" name="arrival_date" value="%s" style='border: 1px solid #cfcfcf'>

                      </td>
                    </tr>
                    <tr>
                      <th width="150">%s</th>
                      <td class="bibcirccontent" colspan="3">

                        <script type="text/javascript">
                             $(function() {
                                 $("#date_picker2").datepicker({dateFormat: 'yy-mm-dd', showOn: 'button', buttonImage: "%s/img/calendar.gif", buttonImageOnly: true});
                             });
                        </script>
                        <input type="text" size="10" id="date_picker2" name="due_date" value="%s" style='border: 1px solid #cfcfcf'>
                        <input type="hidden" name="request_date" value="%s">
                        <input type="hidden" name="expected_date" value="%s">
                        <input type="hidden" name="library_id" value="%s">
                      </td>
                    </tr>
            """ % (_("Arrival date"), CFG_SITE_URL, date1, _("Due date"),
                CFG_SITE_URL, date2, request_date, expected_date, library_id)

            out += """
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent" colspan="3">
                            <input type="text" size="12" name="cost" value="%s"
                                   style='border: 1px solid #cfcfcf'>
                    """ % (_("Cost"), cost)

            out += """
                          </td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent" colspan="3">
                            <input type="text" size="12" name="budget_code"
                                   value="%s" style='border: 1px solid #cfcfcf'>
                        </tr>
                        <tr>
                          <th width="100" valign="top">%s</th>
                          <td colspan="3">
                            <table class="bibcircnotes">
                        """ % (_("Budget code"), budget_code, _("Previous notes"))

            out += notes


            out += """
                            </table>
                          </td>
                        </tr>
                        <tr>
                          <th valign="top" width="100">%s</th>
                          <td colspan="3">
                            <textarea name='library_notes' rows="6" cols="74"
                                      style='border: 1px solid #cfcfcf'></textarea>
                          </td>
                        </tr>
                      </table>
                     </td>
                   </tr>
                 </table>

                      """ % (_("Library notes"))


##### CANCELED ##############
        elif ill_status == CFG_BIBCIRCULATION_ACQ_STATUS_CANCELLED:

            date1 = return_date

            if ill_status == CFG_BIBCIRCULATION_ILL_STATUS_RETURNED and \
               str(return_date)=='0000-00-00':
                date1 = today

            out += """
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent">%s</td>
                          <th width="100">%s</th>
                          <td class="bibcirccontent">%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent" colspan="3">%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent" colspan="3">%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent" colspan="3">%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent" colspan="3">%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent" colspan="3">%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent" colspan="3">
                            <script type="text/javascript">
                                $(function() {
                                    $("#date_picker1").datepicker({dateFormat: 'yy-mm-dd',
                                        showOn: 'button', buttonImage: "%s/img/calendar.gif",
                                        buttonImageOnly: true});
                                });
                            </script>
                            <input type="text" size="10" id="date_picker1" name="return_date"
                                   value="%s" style='border: 1px solid #cfcfcf'>
                            <input type="hidden" name="request_date"  value="%s">
                            <input type="hidden" name="expected_date" value="%s">
                            <input type="hidden" name="arrival_date"  value="%s">
                            <input type="hidden" name="due_date"      value="%s">
                            <input type="hidden" name="library_id"    value="%s">
                            <input type="hidden" name="budget_code"   value="%s">
                          </td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent" colspan="3">
                            <input type="text" size="12" name="cost"
                                   value="%s" style='border: 1px solid #cfcfcf'>
        """ % (_("ILL request ID"), ill_request_id, _("Type"), request_type,
               _("Library"), library_name, _("Request date"), request_date,
               _("Expected date"), expected_date, _("Arrival date"),
               arrival_date, _("Due date"), due_date, _("Return date"),
               CFG_SITE_URL, date1, request_date, expected_date, arrival_date,
               due_date, library_id, budget_code, _("Cost"), cost)

            out += """
                          </td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent" colspan="3">%s</td>
                        </tr>
                        <tr>
                          <th width="100" valign="top">%s</th>
                          <td colspan="3">
                            <table class="bibcircnotes">
                    """ % (_("Budget code"), budget_code, _("Previous notes"))

            out += notes

            out += """
                            </table>
                          </td>
                        </tr>
                        <tr>
                          <th valign="top" width="100">%s</th>
                          <td colspan="3">
                            <textarea name='library_notes' rows="6" cols="74"
                                      style='border: 1px solid #cfcfcf'></textarea>
                          </td>
                        </tr>
                      </table>
                     </td>
                   </tr>
                 </table>

                      """ % (_("Library notes"))

##### RECEIVED ##############
        elif ill_status == CFG_BIBCIRCULATION_ACQ_STATUS_RECEIVED \
             or ill_status == CFG_BIBCIRCULATION_PROPOSAL_STATUS_RECEIVED:
            if str(arrival_date) == '0000-00-00':
                date1 = today
            else:
                date1 = arrival_date

            out += """
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent">%s</td>
                          <th width="100">%s</th>
                          <td class="bibcirccontent">%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent" colspan="3">%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent" colspan="3">%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent" colspan="3">%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent" colspan="3">
                            <script type="text/javascript">
                                $(function() {
                                    $("#date_picker1").datepicker({dateFormat: 'yy-mm-dd',
                                        showOn: 'button', buttonImage: "%s/img/calendar.gif",
                                        buttonImageOnly: true});
                                });
                            </script>
                            <input type="text" size="10" id="date_picker1"
                               name="arrival_date" value="%s" style='border: 1px solid #cfcfcf'>
                            <input type="hidden" name="request_date" value="%s">
                            <input type="hidden" name="expected_date" value="%s">
                            <input type="hidden" name="library_id" value="%s">
                          </td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent" colspan="3"><input type="text" size="12"
                              name="cost" value="%s" style='border: 1px solid #cfcfcf'>
        """ % (_("ILL request ID"), ill_request_id, _("Type"), request_type,
               _("Library"), library_name, _("Request date"), request_date,
               _("Expected date"), expected_date, _("Arrival date"),
               CFG_SITE_URL, date1, request_date, expected_date, library_id,
               _("Cost"), cost)

            out += """
                          </td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent" colspan="3"><input type="text" size="12"
                            name="budget_code" value="%s" style='border: 1px solid #cfcfcf'></td>
                        </tr>
                        <tr>
                          <th width="100" valign="top">%s</th>
                          <td colspan="3">
                            <table class="bibcircnotes">
                """ % (_("Budget code"), budget_code, _("Previous notes"))

            out += notes

            out += """
                            </table>
                          </td>
                        </tr>
                        <tr>
                          <th valign="top" width="100">%s</th>
                          <td colspan="3">
                            <textarea name='library_notes' rows="6" cols="74"
                                      style='border: 1px solid #cfcfcf'></textarea>
                          </td>
                        </tr>
                      </table>
                     </td>
                   </tr>
                 </table>

                      """ % (_("Library notes"))

###### END STATUSES ######

        out += """

             <br />
             <table class="bibcirctable">
                <tr>
                  <td>
                       <input type=button value="%s"
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit"
                       value="%s" class="formbutton">

                  </td>
                 </tr>
             </table>
             </div>
             </form>
             <br />
             <br />
               """ % (_("Back"), _("Continue"))

        return out


    def tmpl_ill_notes(self, ill_notes, ill_id, ln=CFG_SITE_LANG):
        """
        @param ill_notes: notes about an ILL request
        @type ill_notes: dictionnary

        @param ill_id: identify the ILL request. Primray key of crcILLREQUEST
        @type ill_id: int
        """

        _ = gettext_set_language(ln)

        if not ill_notes:
            ill_notes = {}
        else:
            if looks_like_dictionary(ill_notes):
                ill_notes = eval(ill_notes)
            else:
                ill_notes = {}
        out = """ """

        out += load_menu(ln)

        out += """
            <div class="bibcircbottom">
            <form name="borrower_notes"
                  action="%s/admin2/bibcirculation/get_ill_library_notes"
                  method="get" >
            <input type=hidden name=ill_id value='%s'>
            <br />
            <br />
            <table class="bibcirctable">
              <tr>
                <td class="bibcirctableheader">%s</td>
              </tr>
            </table>
            <table class="bibcirctable">
              <tr>
                <td>
                  <table class="bibcircnotes">

            """ % (CFG_SITE_URL, ill_id,
                   _("Notes about ILL"))

        key_array = ill_notes.keys()
        key_array.sort()

        for key in key_array:
            delete_note = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/get_ill_library_notes',
                                {'delete_key': key, 'ill_id': ill_id, 'ln': ln},
                                (_("[delete]")))

            out += """<tr class="bibcirccontent">
                        <td class="bibcircnotes" width="160" valign="top"
                            align="center"><b>%s</b></td>
                        <td width="400"><i>%s</i></td>
                        <td width="65" align="center">%s</td>
                      </tr>

                      """ % (key, ill_notes[key], delete_note)

        out += """
                  </table>
                  </td>
              </tr>
            </table>
            <br />
            <table class="bibcirctable">
              <tr>
                <td class="bibcirctableheader">%s</td>
              </tr>
            </table>
            <table class="bibcirctable">
              <tr>
                <td class="bibcirccontent">
                  <textarea name="library_notes" rows="5" cols="90"
                            style='border: 1px solid #cfcfcf'>
                  </textarea>
                </td>
              </tr>
            </table>
            <br />
            <table class="bibcirctable">
              <tr>
                  <td>
                    <input type=button value='%s'
                           onClick="history.go(-1)" class="formbutton">
                    <input type="submit" value='%s' class="formbutton">
                  </td>
             </tr>
             </table>
             <br />
             <br />
             <br />
             </form>
             </div>
        """ % (_("Write new note"),
               _("Back"),
               _("Confirm"))

        return out



    ####
    #### Templates for the display of "Lists" ####
    ####



    def tmpl_list_ill(self, ill_req, infos=[], ln=CFG_SITE_LANG):
        """
        @param ill_req: information about ILL requests
        @type ill_req: tuple
        """
        _ = gettext_set_language(ln)

        out = """ """

        if infos: out = self.tmpl_infobox(infos, ln)

        out += load_menu(ln)

        out += """
        <style type="text/css"> @import url("/css/tablesorter.css"); </style>
        <script src="/%s" type="text/javascript"></script>
        <script type="text/javascript">
        $(document).ready(function() {
          $('#table_ill').tablesorter({widthFixed: true, widgets: ['zebra']})
        });
        </script>
        <div class="bibcircbottom">
            <br />
            <table id="table_ill" class="tablesorter" border="0"
                                   cellpadding="0" cellspacing="1">
                <thead>
                    <tr>
                        <th>%s</th>
                        <th>%s</th>
                        <th>%s</th>
                        <th>%s</th>
                        <th>%s</th>
                        <th>%s</th>
                        <th>%s</th>
                        <th>%s</th>
                        <th>%s</th>
                    </tr>
                </thead>
                <tbody>
            """% (JQUERY_TABLESORTER,
                  _("Borrower"),
                  _("Item"),
                  _("Supplier"),
                  _("Status"),
                  _("ID"),
                  _("Interest from"),
                  _("Due date"),
                  _("Type"),
                  _("Option(s)"))

        for (ill_request_id, borrower_id, borrower_name, library_id,
             ill_status, period_from, _period_to, due_date, item_info,
             request_type) in ill_req:

            borrower_link = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/get_borrower_details',
                                {'borrower_id': borrower_id, 'ln': ln},
                                (borrower_name))

            if library_id:
                if request_type in CFG_BIBCIRCULATION_ACQ_TYPE or \
                   request_type in CFG_BIBCIRCULATION_PROPOSAL_TYPE:
                    library_name = db.get_vendor_name(library_id)
                else:
                    library_name = db.get_library_name(library_id)
            else:
                library_name = '-'

            if looks_like_dictionary(item_info):
                item_info = eval(item_info)
            else:
                item_info = {}

            try:
                title = book_title_from_MARC(int(item_info['recid']))
                title_link = create_html_link(CFG_SITE_URL +
                                    '/admin2/bibcirculation/get_item_details',
                                    {'recid': item_info['recid'], 'ln': ln}, title)
            except KeyError:
                if request_type in ['book'] + CFG_BIBCIRCULATION_ACQ_TYPE + CFG_BIBCIRCULATION_PROPOSAL_TYPE:
                    title = item_info['title']
                else:
                    title = item_info['periodical_title']
                title_link = title

            out += """
                   <tr>
                    <td class="bibcirccontent">%s</td>
                    <td class="bibcirccontent">%s</td>
                    <td class="bibcirccontent">%s</td>
                    <td class="bibcirccontent">%s</td>
                    <td class="bibcirccontent">%s</td>
                    <td class="bibcirccontent">%s</td>
                    <td class="bibcirccontent">%s</td>
                    <td class="bibcirccontent">%s</td>
                    <td align="center">
                    """ % (borrower_link, title_link, library_name, ill_status,
                           ill_request_id, period_from, due_date or '-',
                           request_type)

            if request_type in CFG_BIBCIRCULATION_ACQ_TYPE or \
               request_type in CFG_BIBCIRCULATION_PROPOSAL_TYPE:
                out += """
                       <input type=button onClick="location.href='%s/admin2/bibcirculation/purchase_details_step1?ill_request_id=%s'" onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
                       value="%s" class='bibcircbutton'>
                    </td>
                   </tr>
                    """ % (CFG_SITE_URL, ill_request_id, _('select'))
            else:
                out += """
                       <input type=button onClick="location.href='%s/admin2/bibcirculation/ill_request_details_step1?ill_request_id=%s'" onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
                       value="%s" class='bibcircbutton'>
                    """ % (CFG_SITE_URL, ill_request_id, _('select'))

                # Create a link for a manual recall.
                if ill_status == CFG_BIBCIRCULATION_ILL_STATUS_ON_LOAN:
                    subject = _("Inter library loan recall: ") + str(title)

                    out += """
                       <input type=button onClick="location.href='%s/admin2/bibcirculation/borrower_notification?borrower_id=%s&subject=%s&load_msg_template=True&template=%s&from_address=%s'"
                       onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'" value="%s" class='bibcircbutton'>
                    """ % (CFG_SITE_URL, borrower_id, subject, 'ill_recall1', CFG_BIBCIRCULATION_ILLS_EMAIL, _('Send Recall'))

                out +=   """</td>
                          </tr>
                        """
        out += """
           </tbody>
          </table>
         </div>
        """

        return out

    def tmpl_list_purchase(self, purchase_reqs, ln=CFG_SITE_LANG):
        """
        @param purchase_req: information about purchase requests
        @type purchase_req: tuple
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += load_menu(ln)

        out += """
        <style type="text/css"> @import url("/css/tablesorter.css"); </style>
        <script src="/%s" type="text/javascript"></script>
        <script type="text/javascript">
        $(document).ready(function() {
          $('#table_ill').tablesorter({widthFixed: true, widgets: ['zebra']})
        });
        </script>
         <div class="bibcircbottom">
           <br />
             <table id="table_ill" class="tablesorter" border="0"
                                   cellpadding="0" cellspacing="1">
             <thead>
                    <tr>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                    </tr>
             </thead>
             <tbody>
            """% (JQUERY_TABLESORTER,
                  _("Borrower"),
                  _("Item"),
                  _("No. purchases"),
                  _("Supplier"),
                  _("Cost"),
                  _("Status"),
                  _("ID"),
                  _("Date requested"),
                  _("Type"),
                  _("Options"))

        for (ill_request_id, borrower_id, borrower_name, vendor_id, ill_status,
             period_from, _period_to, _due_date, item_info, cost, request_type,
             no_purchases) in purchase_reqs:

            borrower_link = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/get_borrower_details',
                                {'borrower_id': borrower_id, 'ln': ln},
                                (borrower_name))

            if vendor_id:
                vendor_name = db.get_vendor_name(vendor_id)
            else:
                vendor_name = '-'

            if looks_like_dictionary(item_info):
                item_info = eval(item_info)
            else:
                item_info = {}

            try:
                title_link = create_html_link(CFG_SITE_URL +
                                    '/admin2/bibcirculation/get_item_details',
                                    {'recid': item_info['recid'], 'ln': ln},
                                (book_title_from_MARC(int(item_info['recid']))))
            except KeyError:
                title_link = item_info['title']

            out += """
                   <tr>
                    <td class="bibcirccontent">%s</td>
                    <td class="bibcirccontent">%s</td>
                    <td class="bibcirccontent">%s</td>
                    <td class="bibcirccontent">%s</td>
                    <td class="bibcirccontent">%s</td>
                    <td class="bibcirccontent">%s</td>
                    <td class="bibcirccontent">%s</td>
                    <td class="bibcirccontent">%s</td>
                    <td class="bibcirccontent">%s</td>
                    <td align="center">
                    """ % (borrower_link, title_link, no_purchases,
                           vendor_name, cost, ill_status, ill_request_id,
                           period_from, request_type)

            if request_type in CFG_BIBCIRCULATION_ACQ_TYPE or \
               request_type in CFG_BIBCIRCULATION_PROPOSAL_TYPE:
                out += """
                       <input type=button id=select_purchase onClick="location.href='%s/admin2/bibcirculation/purchase_details_step1?ill_request_id=%s'"
                        onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
                       value="%s" class='bibcircbutton'>
                     </td>
                   </tr>
                       """ % (CFG_SITE_URL, ill_request_id, _('select'))
            else:
                out += """
                       <input type=button id=select_ill onClick="location.href='%s/admin2/bibcirculation/ill_request_details_step1?ill_request_id=%s'"
                        onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
                       value="%s" class='bibcircbutton'>
                    </td>
                   </tr>
                       """ % (CFG_SITE_URL, ill_request_id, _('select'))

        out += """
           </tbody>
          </table>
         </div>
        """

        return out

    def tmpl_list_proposal(self, proposals, ln=CFG_SITE_LANG):
        """
        @param proposals: Information about proposals
        @type proposals: tuple
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += load_menu(ln)

        out += """
        <style type="text/css"> @import url("/css/tablesorter.css"); </style>
        <script src="/%s" type="text/javascript"></script>
        <script type="text/javascript">
        $(document).ready(function() {
          $('#table_ill').tablesorter({widthFixed: true, widgets: ['zebra']})
        });
        </script>
         <div class="bibcircbottom">
           <br />
             <table id="table_ill" class="tablesorter" border="0"
                                   cellpadding="0" cellspacing="1">
             <thead>
                    <tr>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                    </tr>
             </thead>
             <tbody>
            """% (JQUERY_TABLESORTER,
                  _("ID"),
                  _("Proposal date"),
                  _("Proposer"),
                  _("Requests"),
                  _("Title"),
                  _("Status"),
                  _("Supplier"),
                  _("Cost"),
                  _("Type"),
                  _("Options"))

        for (ill_request_id, borrower_id, borrower_name, vendor_id,
             ill_status, _barcode, period_from, _period_to,
             item_info, cost, request_type, number_of_requests) in proposals:

            borrower_link = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/get_borrower_details',
                                {'borrower_id': borrower_id, 'ln': ln},
                                (borrower_name))

            if vendor_id:
                vendor_name = db.get_vendor_name(vendor_id)
            else:
                vendor_name = '-'

            if looks_like_dictionary(item_info):
                item_info = eval(item_info)
            else:
                item_info = {}

            try:
                title_link = create_html_link(CFG_SITE_URL +
                                    '/admin2/bibcirculation/get_item_details',
                                    {'recid': item_info['recid'], 'ln': ln},
                                (book_title_from_MARC(int(item_info['recid']))))
            except KeyError:
                title_link = item_info['title']

            try:
                hold_requests_link = create_html_link(CFG_SITE_URL +
                                    '/admin2/bibcirculation/get_item_requests_details',
                                    {'recid': item_info['recid'], 'ln': ln},
                                    str(number_of_requests))
            except KeyError:
                hold_requests_link = str(number_of_requests)

            out += """
                   <tr>
                    <td class="bibcirccontent">%s</td>
                    <td class="bibcirccontent">%s</td>
                    <td class="bibcirccontent">%s</td>
                    <td class="bibcirccontent">%s</td>
                    <td class="bibcirccontent">%s</td>
                    <td class="bibcirccontent">%s</td>
                    <td class="bibcirccontent">%s</td>
                    <td class="bibcirccontent">%s</td>
                    <td class="bibcirccontent">%s</td>
                    <td align="center">
                    """ % (ill_request_id, period_from, borrower_link,
                           hold_requests_link, title_link, ill_status,
                           vendor_name, cost, request_type)

            out += """ <input type=button onClick="location.href='%s/admin2/bibcirculation/purchase_details_step1?ill_request_id=%s'" onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
                       value="%s" class='bibcircbutton'>""" % (CFG_SITE_URL, ill_request_id, _('select'))

            if ill_status == CFG_BIBCIRCULATION_PROPOSAL_STATUS_PUT_ASIDE:
                out += """ <input type=button onClick="location.href='%s/admin2/bibcirculation/register_ill_from_proposal?ill_request_id=%s'" onmouseover="this.className='bibcircbuttonover'"
                            onmouseout="this.className='bibcircbutton'" value="%s" class='bibcircbutton'>""" % (CFG_SITE_URL, ill_request_id, _('Create ILL req'))

            out += """</td></tr>"""

        out += """
           </tbody>
          </table>
         </div>
        """

        return out

    def tmpl_list_requests_on_put_aside_proposals(self, requests, ln=CFG_SITE_LANG):
        """
        Template for the display of additional requests on proposals which are
        'put aside'.
        @param requests: information about requests on 'put aside' proposals
        @type requests: tuple
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += load_menu(ln)

        out += """
        <style type="text/css"> @import url("/css/tablesorter.css"); </style>
        <script src="/%s" type="text/javascript"></script>
        <script type="text/javascript">
        $(document).ready(function() {
          $('#table_ill').tablesorter({widthFixed: true, widgets: ['zebra']})
        });
        </script>
         <div class="bibcircbottom">
           <br />
             <table id="table_ill" class="tablesorter" border="0"
                                   cellpadding="0" cellspacing="1">
             <thead>
                    <tr>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                    </tr>
             </thead>
             <tbody>
            """% (JQUERY_TABLESORTER,
                  _("Req.ID"),
                  _("Requester"),
                  _("Period of Interest: From"),
                  _("Period of Interest: To"),
                  _("Title"),
                  _("Cost"),
                  _("Options"))

        for (ill_id, req_id, bor_id, bor_name, period_from, period_to,
             item_info, cost) in requests:

            borrower_link = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/get_borrower_details',
                                {'borrower_id': bor_id, 'ln': ln},
                                (bor_name))

            if looks_like_dictionary(item_info):
                item_info = eval(item_info)
            else:
                item_info = {}

            try:
                title_link = create_html_link(CFG_SITE_URL +
                                    '/admin2/bibcirculation/get_item_details',
                                    {'recid': item_info['recid'], 'ln': ln},
                                (book_title_from_MARC(int(item_info['recid']))))
            except KeyError:
                title_link = item_info['title']

            out += """
                   <tr>
                    <td class="bibcirccontent">%s</td>
                    <td class="bibcirccontent">%s</td>
                    <td class="bibcirccontent">%s</td>
                    <td class="bibcirccontent">%s</td>
                    <td class="bibcirccontent">%s</td>
                    <td class="bibcirccontent">%s</td>
                    <td align="center">
                    """ % (req_id, borrower_link, period_from, period_to,
                           title_link, cost)

            out += """ <input type=button onClick="location.href='%s/admin2/bibcirculation/purchase_details_step1?ill_request_id=%s'" onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
                       value="%s" class='bibcircbutton'>""" % (CFG_SITE_URL, ill_id, _('Go to Proposal'))

            out += """ <input type=button onClick="location.href='%s/admin2/bibcirculation/register_ill_from_proposal?ill_request_id=%s&bor_id=%s'" onmouseover="this.className='bibcircbuttonover'"
                       onmouseout="this.className='bibcircbutton'" value="%s" class='bibcircbutton'>""" % (CFG_SITE_URL, ill_id, bor_id, _('Create ILL req'))

            out += """</td></tr>"""

        out += """
           </tbody>
          </table>
         </div>
        """

        return out


    ###
    ### "Library" related templates ###
    ###


    def tmpl_merge_libraries_step1(self, library_details, library_items,
                                         result, p, ln=CFG_SITE_LANG):

        _ = gettext_set_language(ln)

        out = """
        """
        out += load_menu(ln)

        out += """
        <style type="text/css"> @import url("/css/tablesorter.css"); </style>
        <div class="bibcircbottom">
        <br />
        """
        (library_id, name, address, email, phone,
         lib_type, notes) = library_details

        no_notes_link = create_html_link(CFG_SITE_URL +
                                    '/admin2/bibcirculation/get_library_notes',
                                    {'library_id': library_id},
                                    (_("No notes")))

        see_notes_link = create_html_link(CFG_SITE_URL +
                                    '/admin2/bibcirculation/get_library_notes',
                                    {'library_id': library_id},
                                    (_("Notes about this library")))

        if notes == "" or str(notes) == '{}':
            notes_link = no_notes_link
        else:
            notes_link = see_notes_link

        out += """
            <table class="bibcirctable">
                <tbody>
                    <tr>
                        <td align="left" valign="top" width="300">
                            <table class="bibcirctable">
                                <tr>
                                    <td width="200" class="bibcirctableheader">%s</td>
                                </tr>
                            </table>
                            <table class="tablesorter" border="0"
                                   cellpadding="0" cellspacing="1">
                                <tr>
                                    <th width="100">%s</th>
                                    <td>%s</td>
                                </tr>
                                <tr>
                                    <th width="100">%s</th>
                                    <td>%s</td>
                                </tr>
                                <tr>
                                    <th width="100">%s</th>
                                    <td>%s</td>
                                </tr>
                                <tr>
                                    <th width="100">%s</th>
                                    <td>%s</td>
                                </tr>
                                <tr>
                                    <th width="100">%s</th>
                                    <td>%s</td>
                                </tr>
                                <tr>
                                    <th width="100">%s</th>
                                    <td>%s</td>
                                </tr>
                                <tr>
                                    <th width="100">%s</th>
                                    <td>%s</td>
                                </tr>
                            </table>
                        </td>
                            """ % (_("Library to be deleted"),
                                   _("Name"), name,
                                   _("Address"), address,
                                   _("Email"), email,
                                   _("Phone"), phone,
                                   _("Type"), lib_type,
                                   _("Notes"), notes_link,
                                   _("No of items"), len(library_items))


        out += """
                        <td width="200" align="center" valign="top">
                        <td valign="top" align='left'>
                            <form name="search_library_step1_form"
                                    action="%s/admin2/bibcirculation/merge_libraries_step1"
                                    method="get" >
                                <input type=hidden name=library_id value="%s">
                                <table class="bibcirctable">
                                    <tr align="center">
                                        <td class="bibcirctableheader">%s
                                            <input type="radio" name="f"
                                                   value="name" checked>%s
                                            <input type="radio" name="f"
                                                   value="email">%s
                                            <br \>
                                            <br \>
                                        </td>
                                    </tr>
                                    <tr align="center">
                                        <td>
                                            <input type="text" size="45" name="p"
                                                   style='border: 1px solid #cfcfcf'
                                                   value="%s">
                                        </td>
                                    </tr>
                                </table>
                                <br />
                                <table class="bibcirctable">
                                    <tr align="center">
                                        <td>
                                            <input type="submit" value='%s' class="formbutton">
                                        </td>
                                    </tr>
                                </table>
                            </form>
            """ % (CFG_SITE_URL, library_id, _("Search library"),
                   _("name"), _("email"), p or '', _("Search"))

        if result:
            out += """
                            <br />
                            <form name="form2"
                                    action="%s/admin2/bibcirculation/merge_libraries_step2"
                                    method="get">
                                <table class="bibcirctable">
                                    <tr width="200">
                                        <td align="center">
                                            <select name="library_to" size="12"
                                                    style='border: 1px
                                                    solid #cfcfcf; width:77%%'>
                            """ % (CFG_SITE_URL)

            for (library_to, library_name) in result:
                if library_to != library_id:
                    out += """
                                                <option value ='%s'>%s

                       """ % (library_to, library_name)

            out += """
                                            </select>
                                        </td>
                                    </tr>
                                </table>
                                <table class="bibcirctable">
                                    <tr>
                                        <td ALIGN="center">
                                            <input type="submit" value='%s' class="formbutton">
                                        </td>
                                    </tr>
                                </table>
                                <input type=hidden name=library_from value="%s">
                            </form>
                    """ % (_("Select library"), library_id)

        out += """
                        </td>
                    <tr>
                </tbody>
            </table>
            <br />
            <br />
            <table class="bibcirctable">
                <tr>
                    <td>
                        <input type=button value='%s'
                          onClick="history.go(-1)" class="formbutton">
                    </td>
                </tr>
            </table>
            <br />
            <br />
            <br />
        </div>
           """ % (_("Back"))

        return out

    def tmpl_merge_libraries_step2(self, library_from_details,
                                   library_from_items, library_to_details,
                                   library_to_items, ln=CFG_SITE_LANG):

        _ = gettext_set_language(ln)

        out = load_menu(ln)

        out += """
        <style type="text/css"> @import url("/css/tablesorter.css"); </style>
        <div class="bibcircbottom">
        <br />
        """

        try:
            (library_id_1, name_1, address_1, email_1,
             phone_1, type_1, notes_1) = library_from_details
            found_1 = True
        except:
            found_1 = False

        try:
            (library_id_2, name_2, address_2, email_2,
             phone_2, type_2, notes_2) = library_to_details
            found_2 = True
        except:
            found_2 = False

        if found_1:
            no_notes_link_1 = create_html_link(CFG_SITE_URL +
                                    '/admin2/bibcirculation/get_library_notes',
                                    {'library_id': library_id_1},
                                    (_("No notes")))

            see_notes_link_1 = create_html_link(CFG_SITE_URL +
                                    '/admin2/bibcirculation/get_library_notes',
                                    {'library_id': library_id_1},
                                    (_("Notes about this library")))
            if notes_1 == "" or str(notes_1) == '{}':
                notes_link_1 = no_notes_link_1
            else:
                notes_link_1 = see_notes_link_1

        if found_2:
            no_notes_link_2 = create_html_link(CFG_SITE_URL +
                                    '/admin2/bibcirculation/get_library_notes',
                                    {'library_id': library_id_2},
                                    (_("No notes")))

            see_notes_link_2 = create_html_link(CFG_SITE_URL +
                                    '/admin2/bibcirculation/get_library_notes',
                                    {'library_id': library_id_2},
                                    (_("Notes about this library")))

            if notes_2 == "" or str(notes_2) == '{}':
                notes_link_2 = no_notes_link_2
            else:
                notes_link_2 = see_notes_link_2

        if found_1 and found_2:
            out += """
            <br />
            <div class="infoboxmsg">
                <strong>
                    %s
                </strong>
            </div>
            <br />
          """ % (_("Please, note that this action is NOT reversible"))

        out += """
            <table class="bibcirctable">
                <tbody>
                    <tr>
            """

        if found_1:
            out += """
                        <td align="left" valign="top" width="300">
                            <table class="bibcirctable">
                                <tr>
                                    <td width="200" class="bibcirctableheader">%s</td>
                                </tr>
                            </table>
                            <table class="tablesorter" border="0"
                                   cellpadding="0" cellspacing="1">
                                <tr>
                                    <th width="100">%s</th>
                                    <td>%s</td>
                                </tr>
                                <tr>
                                    <th width="100">%s</th>
                                    <td>%s</td>
                                </tr>
                                <tr>
                                    <th width="100">%s</th>
                                    <td>%s</td>
                                </tr>
                                <tr>
                                    <th width="100">%s</th>
                                    <td>%s</td>
                                </tr>
                                <tr>
                                    <th width="100">%s</th>
                                    <td>%s</td>
                                </tr>
                                <tr>
                                    <th width="100">%s</th>
                                    <td>%s</td>
                                </tr>
                                <tr>
                                    <th width="100">%s</th>
                                    <td>%s</td>
                                </tr>
                            </table>
                """ % (_("Library to be deleted"),
                   _("Name"), name_1,
                   _("Address"), address_1,
                   _("Email"), email_1,
                   _("Phone"), phone_1,
                   _("Type"), type_1,
                   _("Notes"), notes_link_1,
                   _("No of items"), len(library_from_items))
        else:
            out += """
                        <td align="left" valign="center" width="300">
                            <div class="infoboxmsg">%s</div>
                        """ % (_("Library not found"))

        out += """
                        </td>
                        <td width="200" align="center" valign="center">
                            <strong>==></strong>
                        </td>
                """

        if found_2:
            out += """
                        <td align="left" valign="top" width="300">
                            <table class="bibcirctable">
                                <tr>
                                    <td width="200" class="bibcirctableheader">%s</td>
                                </tr>
                            </table>
                            <table class="tablesorter" border="0"
                                   cellpadding="0" cellspacing="1">
                                <tr>
                                    <th width="100">%s</th>
                                    <td>%s</td>
                                </tr>
                                <tr>
                                    <th width="100">%s</th>
                                    <td>%s</td>
                                </tr>
                                <tr>
                                    <th width="100">%s</th>
                                    <td>%s</td>
                                </tr>
                                <tr>
                                    <th width="100">%s</th>
                                    <td>%s</td>
                                </tr>
                                <tr>
                                    <th width="100">%s</th>
                                    <td>%s</td>
                                </tr>
                                <tr>
                                    <th width="100">%s</th>
                                    <td>%s</td>
                                </tr>
                                <tr>
                                    <th width="100">%s</th>
                                    <td>%s</td>
                                </tr>
                            </table>

                """ % (_("Merged library"),
                   _("Name"), name_2,
                   _("Address"), address_2,
                   _("Email"), email_2,
                   _("Phone"), phone_2,
                   _("Type"), type_2,
                   _("Notes"), notes_link_2,
                   _("No of items"), len(library_to_items))
        else:
            out += """
                        <td align="left" valign="center" width="300">
                            <div class="infoboxmsg">%s</div>
                        """ % (_("Library not found"))

        out += """
                        </td>
                    <tr>
                </tbody>
            </table>
            <br />
            <br />
            <form name="form1" action="%s/admin2/bibcirculation/merge_libraries_step3"
                               method="get">
                <table class="bibcirctable">
                    <tr>
                        <td>
                            <input type=button value='%s'
                              onClick="history.go(-1)" class="formbutton">
                """ % (CFG_SITE_URL, _("Back"))

        if found_1 and found_2:
            out += """
                            <input type=hidden name=library_from value="%s">
                            <input type=hidden name=library_to value="%s">
                            <input type="submit" value='%s' class="formbutton">
                """ % (library_id_1, library_id_2, _("Confirm"))

        out += """
                        </td>
                    </tr>
                </table>
            </form>
            <br />
            <br />
            <br />
        </div>
           """

        return out

    def tmpl_add_new_library_step1(self, ln=CFG_SITE_LANG):

        _ = gettext_set_language(ln)

        out = load_menu(ln)

        out += """
            <style type="text/css"> @import url("/css/tablesorter.css"); </style>
            <div class="bibcircbottom" align="center">
            <form name="add_new_library_step1_form"
                  action="%s/admin2/bibcirculation/add_new_library_step2" method="get" >
              <br />
              <br />
               <table class="bibcirctable">
                <tr align="center">
                     <td class="bibcirctableheader">%s</td>
                </tr>
              </table>
              <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">
                <tr>
                    <th width="70">%s</th>
                    <td>
                      <input type="text" style='border: 1px solid #cfcfcf'
                             size=50 name="name" id='name'>
                      <script language="javascript" type="text/javascript">
                            document.getElementById("name").focus();
                      </script>
                    </td>
                </tr>
                <tr>
                    <th width="70">%s</th>
                    <td>
                      <input type="text" style='border: 1px solid #cfcfcf' size=50 name="email">
                    </td>
                </tr>
                <tr>
                    <th width="70">%s</th>
                    <td>
                      <input type="text" style='border: 1px solid #cfcfcf' size=50 name="phone">
                    </td>
                </tr>
                <tr>
                    <th width="70">%s</th>
                    <td>
                      <input type="text" style='border: 1px solid #cfcfcf' size=50
                             name="address">
                    </td>
                 </tr>
                 <tr>
                    <th width="70">%s</th>
                    <td>
                    <select name="type"  style='border: 1px solid #cfcfcf'>
            """ % (CFG_SITE_URL, _("New library information"), _("Name"),
                     _("Email"), _("Phone"), _("Address"), _("Type"))

        for lib in CFG_BIBCIRCULATION_LIBRARY_TYPE:
            out += """
                        <option value="%s">%s</option>
                   """ % (lib, lib)

        out += """
                      </select>
                    </td>
                 </tr>
                 <tr>
                    <th width="70" valign="top">%s</th>
                    <td>
                      <textarea name="notes" rows="5" cols="39"
                                style='border: 1px solid #cfcfcf'></textarea>
                    </td>
                 </tr>
                </table>
                <br />
                <table class="bibcirctable">
                <tr align="center">
                  <td>
                       <input type=button value="%s" onClick="history.go(-1)" class="formbutton">
                       <input type="submit"   value="%s" class="formbutton">
                  </td>
                 </tr>
                </table>
                <br />
                <br />
                </form>
                </div>
                """ % (_("Notes"), _("Back"), _("Continue"))

        return out

    def tmpl_add_new_library_step2(self, tup_infos, ln=CFG_SITE_LANG):

        _ = gettext_set_language(ln)

        (name, email, phone, address, lib_type, notes) = tup_infos

        out = """ """

        out += load_menu(ln)

        out += """
            <div class="bibcircbottom">
            <form name="add_new_library_step2_form"
                  action="%s/admin2/bibcirculation/add_new_library_step3" method="get" >
              <br />
              <br />
               <table class="bibcirctable">
                <tr>
                     <td class="bibcirctableheader">%s</td>
                </tr>
              </table>
              <table class="bibcirctable">
                <tr>
                    <td width="70">%s</td> <td class="bibcirccontent">%s</td>
                </tr>
                <tr>
                    <td width="70">%s</td> <td class="bibcirccontent">%s</td>
                </tr>
                <tr>
                    <td width="70">%s</td> <td class="bibcirccontent">%s</td>
                </tr>
                <tr>
                    <td width="70">%s</td> <td class="bibcirccontent">%s</td>
                </tr>
                <tr>
                    <td width="70">%s</td> <td class="bibcirccontent">%s</td>
                </tr>
                <tr>
                    <td width="70">%s</td> <td class="bibcirccontent">%s</td>
                </tr>
                </table>
                <br />
                <table class="bibcirctable">
                <tr>
                    <td>
                        <input type=button
                               value="%s"
                               onClick="history.go(-1)"
                               class="formbutton">
                        <input type="submit"
                               value="%s"
                               class="formbutton">
                        <input type=hidden name=name     value="%s">
                        <input type=hidden name=email    value="%s">
                        <input type=hidden name=phone    value="%s">
                        <input type=hidden name=address  value="%s">
                        <input type=hidden name=lib_type value="%s">
                        <input type=hidden name=notes    value="%s">
                    </td>
                </tr>
                </table>
                <br />
                <br />
                </form>
                </div>
                """ % (CFG_SITE_URL, _("New library information"),
                       _("Name"), name,
                       _("Email"), email,
                       _("Phone"), phone,
                       _("Address"), address,
                       _("Type"), lib_type,
                       _("Notes"), notes,
                       _("Back"), _("Confirm"),
                      name, email, phone, address, lib_type, notes)
        return out

    def tmpl_add_new_library_step3(self, ln=CFG_SITE_LANG):

        _ = gettext_set_language(ln)

        out = load_menu(ln)

        out += """
            <div class="bibcircbottom">
              <br />
              <br />
              <table class="bibcirctable">
                <tr>
                    <td class="bibcirccontent">%s</td>
                </tr>
                </table>
                <br />
                <table class="bibcirctable">
                <tr>
                  <td>
                       <input type=button value='%s'
                    onClick="location.href='%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s'"
                            class="formbutton">
                  </td>
                 </tr>
                </table>
                <br />
                <br />
                </div>
                """ % (_("A new library has been registered."),
                       _("Back to home"),
                       CFG_SITE_URL, ln)

        return out

    def tmpl_update_library_info_step1(self, infos, ln=CFG_SITE_LANG):
        """
        Template for the admin interface. Search borrower.

        @param ln: language
        """
        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += load_menu(ln)

        out += """
        <div class="bibcircbottom">
        <br />
        <br />
        <br />
        <form name="update_library_info_step1_form"
              action="%s/admin2/bibcirculation/update_library_info_step2"
              method="get" >
            <table class="bibcirctable">
                <tr align="center">
                    <td class="bibcirctableheader">%s
                        <input type="radio" name="column" value="name" checked>%s
                        <input type="radio" name="column" value="email">%s
                        <br>
                        <br>
                    </td>
                </tr>
        """ % (CFG_SITE_URL,
               _("Search library by"),
               _("name"),
               _("email"))

        out += """
                <tr align="center">
                    <td>
                        <input type="text" size="45" name="string" id='string'
                               style='border: 1px solid #cfcfcf'>
                        <script language="javascript" type="text/javascript">
                            document.getElementById("string").focus();
                        </script>
                    </td>
                </tr>
            </table>
        <br />
        <table class="bibcirctable">
             <tr align="center">
                  <td>
                        <input type=button value='%s'
                         onClick="history.go(-1)" class="formbutton">
                        <input type="submit" value="%s" class="formbutton">

                  </td>
             </tr>
        </table>
        <form>
        <br /><br />
        <br />
        <br />
        </div>
        """ % (_("Back"), _("Search"))

        return out

    def tmpl_update_library_info_step2(self, result, ln=CFG_SITE_LANG):
        """
        @param result: search result
        @param ln: language
        """

        _ = gettext_set_language(ln)

        out = load_menu(ln)

        out += """
        <style type="text/css"> @import url("/css/tablesorter.css"); </style>
        <div class="bibcircbottom" align="center">
        <br />
        <table class="bibcirctable">
          <tr align="center">
            <td class="bibcirccontent">
               <strong>%s libraries found</strong>
            </td>
          </tr>
        </table>
        <br />
        <table class="tablesortersmall" border="0"
               cellpadding="0" cellspacing="1">
         <th align="center">%s</th>

        """ % (len(result), _("Libraries"))

        for (library_id, name) in result:
            library_link = create_html_link(CFG_SITE_URL +
                            '/admin2/bibcirculation/update_library_info_step3',
                            {'library_id': library_id, 'ln': ln}, (name))

            out += """
            <tr align="center">
                 <td class="bibcirccontent" width="70">%s
                 <input type=hidden name=library_id value="%s"></td>
            </tr>
            """ % (library_link, library_id)


        out += """
             </table>
             <br />

        <table class="bibcirctable">
             <tr align="center">
                  <td><input type=button value="%s"
                       onClick="history.go(-1)" class="formbutton"></td>
             </tr>
        </table>
        <br />
        <br />
        <br />
        </form>
        </div>
        """ % (_("Back"))

        return out

    def tmpl_update_library_info_step3(self, library_info, ln=CFG_SITE_LANG):

        _ = gettext_set_language(ln)

        (library_id, name, address, email, phone,
         lib_type, _notes) = library_info

        out = """ """

        out += load_menu(ln)

        out += """
            <style type="text/css"> @import url("/css/tablesorter.css"); </style>
            <div class="bibcircbottom" align="center">
            <form name="update_library_info_step3_form"
                  action="%s/admin2/bibcirculation/update_library_info_step4" method="get" >
                <input type=hidden name=library_id value="%s">
                <br />
                <br />
                <table class="bibcirctable">
                    <tr align="center">
                         <td class="bibcirctableheader">%s</td>
                    </tr>
                </table>
                <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">
                    <tr>
                        <th width="70">%s</th>
                        <td>
                          <input type="text" style='border: 1px solid #cfcfcf' size=50
                                 name="name" value="%s">
                        </td>
                    </tr>
                    <tr>
                        <th width="70">%s</th>
                        <td>
                          <input type="text" style='border: 1px solid #cfcfcf' size=50
                                 name="email" value="%s">
                        </td>
                    </tr>
                    <tr>
                        <th width="70">%s</th>
                        <td>
                          <input type="text" style='border: 1px solid #cfcfcf' size=50
                                 name="phone" value="%s">
                        </td>
                    </tr>
                    <tr>
                        <th width="70">%s</th>
                        <td>
                          <input type="text" style='border: 1px solid #cfcfcf' size=50
                                 name="address" value="%s">
                        </td>
                    </tr>
                    <tr>
                        <th width="70">%s</th>
                        <td>
                            <select name="lib_type"  style='border: 1px solid #cfcfcf'>
                """ % (CFG_SITE_URL, library_id, _("Library information"),
                       _("Name"), name,
                       _("Email"), email,
                       _("Phone"), phone,
                       _("Address"), address,
                       _("Type"))

        for lib in CFG_BIBCIRCULATION_LIBRARY_TYPE:
            if lib == lib_type:
                out += """
                                <option value="%s" selected="selected">%s</option>
                       """ % (lib, lib)
            else:
                out += """
                                <option value="%s">%s</option>
                       """ % (lib, lib)

        out += """
                            </select>
                        </td>
                    </tr>
                </table>
                <br />
                <table class="bibcirctable">
                <tr align="center">
                  <td>
                       <input type=button value="%s" onClick="history.go(-1)" class="formbutton">
                       <input type="submit" value="%s" class="formbutton">
                  </td>
                </tr>
                </table>
                <br />
                <br />
                </form>
                </div>
                """ % (_("Back"), _("Continue"))


        return out

    def tmpl_update_library_info_step4(self, tup_infos, ln=CFG_SITE_LANG):

        (library_id, name, email, phone, address, lib_type) = tup_infos

        _ = gettext_set_language(ln)

        out = load_menu(ln)

        out += """
            <style type="text/css"> @import url("/css/tablesorter.css"); </style>
            <div class="bibcircbottom" align="center">
            <form name="update_library_info_step4_form" action="%s/admin2/bibcirculation/update_library_info_step5" method="get" >
              <br />
              <br />
              <table class="bibcirctable">
                <tr align="center">
                     <td class="bibcirctableheader">%s</td>
                </tr>
              </table>
              <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">
                <tr>
                    <th width="70">%s</th> <td>%s</td>
                </tr>
                <tr>
                    <th width="70">%s</th> <td>%s</td>
                </tr>
                <tr>
                    <th width="70">%s</th> <td>%s</td>
                </tr>
                <tr>
                    <th width="70">%s</th> <td>%s</td>
                </tr>
                <tr>
                    <th width="70">%s</th> <td>%s</td>
                </tr>
                </table>
                <br />
                <table class="bibcirctable">
                <tr align="center">
                  <td>
                       <input type=button value="%s"
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit"
                       value="%s" class="formbutton">

                       <input type=hidden name=library_id value="%s">
                       <input type=hidden name=name value="%s">
                       <input type=hidden name=email value="%s">
                       <input type=hidden name=phone value="%s">
                       <input type=hidden name=address value="%s">
                       <input type=hidden name=lib_type value="%s">
                  </td>
                 </tr>
                </table>
                <br />
                <br />
                </form>
                </div>
                """ % (CFG_SITE_URL, _("Library information"),
                       _("Name"), name,
                       _("Email"), email,
                       _("Phone"), phone,
                       _("Address"), address,
                       _("Type"), lib_type,
                       _("Back"), _("Continue"),
                       library_id, name, email, phone, address, lib_type)

        return out

    def tmpl_update_library_info_step5(self, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += load_menu(ln)

        out += """
            <div class="bibcircbottom">
              <br />
              <br />
              <table class="bibcirctable">
                <tr>
                    <td class="bibcirccontent">%s</td>
                </tr>
                </table>
                <br />
                <table class="bibcirctable">
                <tr>
                  <td>
                       <input type=button value="%s"
                    onClick="location.href='%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s'"
                        class="formbutton">
                  </td>
                 </tr>
                </table>
                <br />
                <br />
                </div>
                """ % (_("The information has been updated."),
                       _("Back to home"),
                       CFG_SITE_URL, ln)

        return out

    def tmpl_search_library_step1(self, infos, ln=CFG_SITE_LANG):
        """
        Template for the admin interface. Search borrower.

        @param infos: informations
        @type infos: list

        @param ln: language
        """
        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += load_menu(ln)

        out += """
        <div class="bibcircbottom">
        <br />
        <br />
        <br />
        <form name="search_library_step1_form"
              action="%s/admin2/bibcirculation/search_library_step2"
              method="get" >
          <table class="bibcirctable">
           <tr align="center">
             <td class="bibcirctableheader">%s
               <input type="radio" name="column" value="name" checked>%s
               <input type="radio" name="column" value="email">%s
               <br>
               <br>
             </td>
           </tr>
        """ % (CFG_SITE_URL,
               _("Search library by"),
               _("name"), _("email"))
        out += """
           <tr align="center">
             <td>
                <input type="text" size="45" name="string" id="string"
                       style='border: 1px solid #cfcfcf'>
                <script language="javascript" type="text/javascript">
                    document.getElementById("string").focus();
                </script>
             </td>
           </tr>
          </table>
          <br />
          <table class="bibcirctable">
             <tr align="center">
                  <td>
                        <input type=button value='%s'
                          onClick="history.go(-1)" class="formbutton">
                        <input type="submit" value='%s' class="formbutton">
                  </td>
             </tr>
        </table>
        <form>
        <br />
        <br />
        <br />
        <br />
        </div>

        """ % (_("Back"),
               _("Search"))


        return out

    def tmpl_search_library_step2(self, result, ln=CFG_SITE_LANG):
        """
        @param result: search result about libraries
        @type result: list

        @param ln: language
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += load_menu(ln)

        if len(result) == 0:
            out += """
            <div class="bibcircbottom">
            <br />
            <div class="bibcircinfoboxmsg">%s</div>
            <br />
            """ % (_("0 libraries found."))

        else:
            out += """
        <style type="text/css"> @import url("/css/tablesorter.css"); </style>
        <div class="bibcircbottom" align="center">
        <br />
        <table class="bibcirctable">
            <tr align="center">
                <td class="bibcirccontent">
                    <strong>%s libraries found</strong>
                </td>
            </tr>
        </table>
        <br />
        <table class="tablesortersmall" border="0" cellpadding="0" cellspacing="1">
          <th align="center">%s</th>

        """ % (len(result), _("Libraries"))

            for (library_id, name) in result:

                library_link = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/get_library_details',
                                {'library_id': library_id, 'ln': ln}, (name))

                out += """
            <tr align="center">
                <td width="70">%s
                    <input type=hidden name=library_id value="%s">
                </td>
            </tr>
            """ % (library_link, library_id)

        out += """
        </table>
        <br />
        <table class="bibcirctable">
            <tr align="center">
                <td>
                    <input type=button value="%s" onClick="history.go(-1)" class="formbutton">
                </td>
            </tr>
        </table>
        <br />
        <br />
        <br />
        </form>
        </div>

        """ % (_("Back"))

        return out

    def tmpl_library_details(self, library_details, library_items,
                             ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        out = """
        """
        out += load_menu(ln)

        out += """
        <style type="text/css"> @import url("/css/tablesorter.css"); </style>
        <div class="bibcircbottom">
        <br />
        """
        (library_id, name, address, email, phone,
         lib_type, notes) = library_details

        no_notes_link = create_html_link(CFG_SITE_URL +
                                    '/admin2/bibcirculation/get_library_notes',
                                    {'library_id': library_id},
                                    (_("No notes")))

        see_notes_link = create_html_link(CFG_SITE_URL +
                                    '/admin2/bibcirculation/get_library_notes',
                                    {'library_id': library_id},
                                    (_("Notes about this library")))

        if notes == "" or str(notes) == '{}':
            notes_link = no_notes_link
        else:
            notes_link = see_notes_link

        out += """
            <table class="bibcirctable">
                 <tr>
                      <td width="80" class="bibcirctableheader">%s</td>
                 </tr>
            </table>
            <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">

                 <tr>
                      <th width="100">%s</th>
                      <td>%s</td>
                 </tr>
                 <tr>
                      <th width="100">%s</th>
                      <td>%s</td>
                 </tr>
                 <tr>
                      <th width="100">%s</th>
                      <td>%s</td>
                 </tr>
                 <tr>
                      <th width="100">%s</th>
                      <td>%s</td>
                 </tr>
                 <tr>
                      <th width="100">%s</th>
                      <td>%s</td>
                 </tr>
                 <tr>
                      <th width="100">%s</th>
                      <td>%s</td>
                 </tr>
                  <tr>
                      <th width="100">%s</th>
                      <td>%s</td>
                 </tr>
             </table>
             <table>
                 <tr>
                   <td>
                     <input type=button
    onClick="location.href='%s/admin2/bibcirculation/update_library_info_step3?ln=%s&library_id=%s'"
                     onmouseover="this.className='bibcircbuttonover'"
                     onmouseout="this.className='bibcircbutton'"
                     value="%s"  class="bibcircbutton">
                    <a href="%s/admin2/bibcirculation/merge_libraries_step1?ln=%s&library_id=%s">%s</a>
                      </td>
                 </tr>
            </table>
            """ % (_("Library details"),
                   _("Name"), name,
                   _("Address"), address,
                   _("Email"), email,
                   _("Phone"), phone,
                   _("Type"), lib_type,
                   _("Notes"), notes_link,
                   _("No of items"), len(library_items),
                   CFG_SITE_URL, ln, library_id, _("Update"),
                   CFG_SITE_URL, ln, library_id, _("Duplicated library?"))

        out += """
           </table>
           <br />
           <br />
           <table class="bibcirctable">
                <tr>
                     <td><input type=button value='%s'
                          onClick="history.go(-1)" class="formbutton"></td>
                </tr>
           </table>
           <br />
           <br />
           <br />
           </div>
           """ % (_("Back"))

        return out

    def tmpl_library_notes(self, library_notes, library_id,
                           ln=CFG_SITE_LANG):

        """
        @param library_notes: notes about a library
        @type library_notes: dictionnary

        @param library_id: identify the library. Primary key of crcLIBRARY
        @type library_id: int

        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        if not library_notes:
            library_notes = {}
        else:
            if looks_like_dictionary(library_notes):
                library_notes = eval(library_notes)
            else:
                library_notes = {}

        out = """ """

        out += load_menu(ln)

        out += """
            <div class="bibcircbottom">
            <form name="library_notes" action="%s/admin2/bibcirculation/get_library_notes" method="get" >
            <input type=hidden name=library_id value='%s'>
            <br />
            <br />
            <table class="bibcirctable">
              <tr>
                <td class="bibcirctableheader">%s</td>
              </tr>
            </table>
            <table class="bibcirctable">
              <tr>
                <td>
                  <table class="bibcircnotes">

            """ % (CFG_SITE_URL, library_id,
                   _("Notes about library"))

        key_array = library_notes.keys()
        key_array.sort()

        for key in key_array:
            delete_note = create_html_link(CFG_SITE_URL +
                                    '/admin2/bibcirculation/get_library_notes',
                                {'delete_key': key, 'library_id': library_id,
                                 'ln': ln}, (_("[delete]")))

            out += """<tr class="bibcirccontent">
                        <td class="bibcircnotes" width="160" valign="top" align="center"><b>%s</b></td>
                        <td width="400"><i>%s</i></td>
                        <td width="65" align="center">%s</td>
                      </tr>

                      """ % (key, library_notes[key], delete_note)

        out += """
                  </table>
                </td>
              </tr>
            </table>
            <br />
            <table class="bibcirctable">
              <tr>
                <td class="bibcirctableheader">%s</td>
              </tr>
            </table>
            <table class="bibcirctable">
              <tr>
                <td class="bibcirccontent">
                  <textarea name="library_notes" rows="5" cols="90" style='border: 1px solid #cfcfcf'></textarea>
                </td>
              </tr>
            </table>
            <br />
            <table class="bibcirctable">
              <tr>
                  <td>
                      <input type=button
    onClick="location.href='%s/admin2/bibcirculation/get_library_details?ln=%s&library_id=%s'"
                       value="%s" class='formbutton'>
                       <input type="submit" value='%s' class="formbutton">
                  </td>
             </tr>
             </table>
             <br />
             <br />
             <br />
             </form>
             </div>
        """ % (_("Write new note"),
               CFG_SITE_URL, ln,
               library_id,
               _("Back"),
               _("Confirm"))

        return out


    ###
    ### "Vendor" related templates ###
    ###


    def tmpl_add_new_vendor_step1(self, ln=CFG_SITE_LANG):
        """
        @param ln: language
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += load_menu(ln)

        out += """
            <style type="text/css"> @import url("/css/tablesorter.css"); </style>
            <div class="bibcircbottom" align="center">
            <form name="add_new_vendor_step1_form" action="%s/admin2/bibcirculation/add_new_vendor_step2" method="get" >
              <br />
              <br />
               <table class="bibcirctable">
                <tr align="center">
                     <td class="bibcirctableheader">%s</td>
                </tr>
              </table>
              <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">
                <tr>
                    <th width="70">%s</th>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=45 name="name">
                    </td>
                </tr>
                <tr>
                    <th width="70">%s</th>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=45 name="email">
                    </td>
                </tr>
                <tr>
                    <th width="70">%s</th>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=45 name="phone">
                    </td>
                </tr>
                <tr>
                    <th width="70">%s</th>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=45 name="address">
                    </td>
                 </tr>
                 <tr>
                    <th width="70" valign="top">%s</th>
                    <td class="bibcirccontent">
                      <textarea name="notes" rows="5" cols="39" style='border: 1px solid #cfcfcf'></textarea>
                    </td>
                 </tr>
                </table>
                <br />
                <table class="bibcirctable">
                <tr align="center">
                  <td>
                       <input type=button value="%s" onClick="history.go(-1)" class="formbutton">
                       <input type="submit"   value="%s" class="formbutton">
                  </td>
                 </tr>
                </table>
                <br />
                <br />
                </form>
                </div>
                """ % (CFG_SITE_URL, _("New vendor information"), _("Name"),
                       _("Email"), _("Phone"), _("Address"), _("Notes"),
                       _("Back"), _("Continue"))


        return out

    def tmpl_add_new_vendor_step2(self, tup_infos, ln=CFG_SITE_LANG):
        """
        @param tup_infos: borrower's information
        @type tup_infos: tuple

        @param ln: language
        """

        _ = gettext_set_language(ln)

        (name, email, phone, address, notes) = tup_infos

        out = """ """

        out += load_menu(ln)

        out += """
            <style type="text/css"> @import url("/css/tablesorter.css"); </style>
            <div class="bibcircbottom" align="center">
            <form name="add_new_vendor_step2_form" action="%s/admin2/bibcirculation/add_new_vendor_step3" method="get" >
              <br />
              <br />
               <table class="bibcirctable">
                <tr align="center">
                     <td class="bibcirctableheader">%s</td>
                </tr>
              </table>
              <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">
                <tr>
                    <th width="70">%s</th> <td class="bibcirccontent">%s</td>
                </tr>
                <tr>
                    <th width="70">%s</th> <td class="bibcirccontent">%s</td>
                </tr>
                <tr>
                    <th width="70">%s</th> <td class="bibcirccontent">%s</td>
                </tr>
                <tr>
                    <th width="70">%s</th> <td class="bibcirccontent">%s</td>
                </tr>
                <tr>
                    <th width="70">%s</th> <td class="bibcirccontent">%s</td>
                 </tr>
                </table>
                <br />
                <table class="bibcirctable">
                <tr align="center">
                  <td>
                       <input type=button value="%s" onClick="history.go(-1)" class="formbutton">
                       <input type="submit"   value="%s" class="formbutton">
                       <input type=hidden name=name value="%s">
                       <input type=hidden name=email value="%s">
                       <input type=hidden name=phone value="%s">
                       <input type=hidden name=address value="%s">
                       <input type=hidden name=notes value="%s">
                  </td>
                 </tr>
                </table>
                <br />
                <br />
                </form>
                </div>
                """ % (CFG_SITE_URL, _("New vendor information"),
                       _("Name"), name,
                       _("Email"), email,
                       _("Phone"), phone,
                       _("Address"), address,
                       _("Notes"), notes,
                       _("Back"), _("Confirm"),
                       name, email, phone, address, notes)

        return out

    def tmpl_add_new_vendor_step3(self, ln=CFG_SITE_LANG):
        """
        @param ln: language
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += load_menu(ln)

        out += """
            <div class="bibcircbottom">
              <br />
              <br />
              <table class="bibcirctable">
                <tr>
                    <td class="bibcirccontent">%s</td>
                </tr>
                </table>
                <br />
                <table class="bibcirctable">
                <tr>
                  <td>
                       <input type=button value="%s"
                onClick="location.href='%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s'"
                        class="formbutton">
                  </td>
                 </tr>
                </table>
                <br />
                <br />
                </div>
                """ % (_("A new vendor has been registered."),
                       _("Back to home"),
                       CFG_SITE_URL, ln)

        return out

    def tmpl_update_vendor_info_step1(self, infos, ln=CFG_SITE_LANG):
        """
        @param infos: information
        @type infos: list

        @param ln: language
        """
        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += load_menu(ln)

        out += """
        <div class="bibcircbottom">
        <br />
        <br />
        <br />
        <form name="update_vendor_info_step1_form"
              action="%s/admin2/bibcirculation/update_vendor_info_step2"
              method="get" >
            <table class="bibcirctable">
                <tr align="center">
                    <td class="bibcirctableheader">%s
                        <input type="radio" name="column" value="name" checked>%s
                        <input type="radio" name="column" value="email">%s
                        <br>
                        <br>
                    </td>
                </tr>
                """ % (CFG_SITE_URL,
                       _("Search vendor by"),
                       _("name"),
                       _("email"))

        out += """
                <tr align="center">
                    <td>
                        <input type="text" size="45" name="string"
                               style='border: 1px solid #cfcfcf'>
                    </td>
                </tr>
            </table>
            <br />
            <table class="bibcirctable">
                <tr align="center">
                    <td>
                        <input type=button value='%s'
                               onClick="history.go(-1)" class="formbutton">
                        <input type="submit" value="%s" class="formbutton">
                    </td>
                </tr>
            </table>
        <form>
        <br />
        <br />
        <br />
        <br />
        </div>
        """ % (_("Back"), _("Search"))

        return out

    def tmpl_update_vendor_info_step2(self, result, ln=CFG_SITE_LANG):
        """
        @param result: search result
        @type result: list

        @param ln: language
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += load_menu(ln)

        out += """
        <style type="text/css"> @import url("/css/tablesorter.css"); </style>
        <div class="bibcircbottom" align="center">
        <br />
        <table class="bibcirctable">
          <tr align="center">
            <td class="bibcirccontent">
              <strong>%s vendor(s) found</strong>
            </td>
          </tr>
        </table>
        <br />
        <table class="tablesortersmall" border="0" cellpadding="0" cellspacing="1">
          <tr align="center">
            <th>%s</th>
          </tr>

        """ % (len(result), _("Vendor(s)"))

        for (vendor_id, name) in result:
            vendor_link = create_html_link(CFG_SITE_URL +
                            '/admin2/bibcirculation/update_vendor_info_step3',
                            {'vendor_id': vendor_id, 'ln': ln}, (name))

            out += """
            <tr align="center">
                 <td class="bibcirccontent" width="70">%s
                 <input type=hidden name=vendor_id value="%s"></td>
            </tr>
            """ % (vendor_link, vendor_id)


        out += """
             </table>
             <br />
             """

        out += """
        <table class="bibcirctable">
             <tr align="center">
                  <td><input type=button value="%s"
                       onClick="history.go(-1)" class="formbutton"></td>
             </tr>
        </table>
        <br />
        <br />
        <br />
        </form>
        </div>
        """ % (_("Back"))

        return out

    def tmpl_update_vendor_info_step3(self, vendor_info, ln=CFG_SITE_LANG):
        """
        @param vendor_infos: information about a given vendor
        @type vendor_infos: tuple
        """

        _ = gettext_set_language(ln)

        (vendor_id, name, address, email, phone, _notes) = vendor_info

        out = """ """

        out += load_menu(ln)

        out += """
            <style type="text/css"> @import url("/css/tablesorter.css"); </style>
            <div class="bibcircbottom" align="center">
            <form name="update_vendor_info_step3_form" action="%s/admin2/bibcirculation/update_vendor_info_step4" method="get" >
             <input type=hidden name=vendor_id value="%s">
              <br />
              <br />
              <table class="bibcirctable">
                <tr align="center">
                     <td class="bibcirctableheader">%s</td>
                </tr>
              </table>
              <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">
                <tr>
                    <th width="70">%s</th>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=45 name="name" value="%s">
                    </td>
                </tr>
                <tr>
                    <th width="70">%s</th>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=45 name="email" value="%s">
                    </td>
                </tr>
                <tr>
                    <th width="70">%s</th>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=45 name="phone" value="%s">
                    </td>
                </tr>
                <tr>
                    <th width="70">%s</th>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=45 name="address" value="%s">
                    </td>
                 </tr>
                </table>
                <br />
                <table class="bibcirctable">
                <tr align="center">
                  <td>
                       <input type=button value="%s"
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit"
                       value="%s" class="formbutton">

                  </td>
                 </tr>
                </table>
                <br />
                <br />
                </form>
                </div>
                """ % (CFG_SITE_URL, vendor_id, _("Vendor information"),
                       _("Name"), name,
                       _("Email"), email,
                       _("Phone"), phone,
                       _("Address"), address,
                       _("Back"), _("Continue"))


        return out

    def tmpl_update_vendor_info_step4(self, tup_infos, ln=CFG_SITE_LANG):
        """
        @param tup_infos: information about a given vendor
        @type tup_infos: tuple
        """

        (vendor_id, name, email, phone, address) = tup_infos

        _ = gettext_set_language(ln)

        out = """ """

        out += load_menu(ln)

        out += """
            <style type="text/css"> @import url("/css/tablesorter.css"); </style>
            <div class="bibcircbottom" align="center">
            <form name="update_vendor_info_step4_form" action="%s/admin2/bibcirculation/update_vendor_info_step5" method="get" >
              <br />
              <br />
              <table class="bibcirctable">
                <tr align="center">
                     <td class="bibcirctableheader">%s</td>
                </tr>
              </table>
              <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">
                <tr>
                    <th width="70">%s</th> <td class="bibcirccontent">%s</td>
                </tr>
                <tr>
                    <th width="70">%s</th> <td class="bibcirccontent">%s</td>
                </tr>
                <tr>
                    <th width="70">%s</th> <td class="bibcirccontent">%s</td>
                </tr>
                <tr>
                    <th width="70">%s</th> <td class="bibcirccontent">%s</td>
                 </tr>
                </table>
                <br />
                <table class="bibcirctable">
                <tr align="center">
                  <td>
                       <input type=button value="%s"
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit"
                       value="%s" class="formbutton">

                       <input type=hidden name=vendor_id value="%s">
                       <input type=hidden name=name value="%s">
                       <input type=hidden name=email value="%s">
                       <input type=hidden name=phone value="%s">
                       <input type=hidden name=address value="%s">
                  </td>
                 </tr>
                </table>
                <br />
                <br />
                </form>
                </div>
                """ % (CFG_SITE_URL, _("Vendor information"),
                       _("Name"), name,
                       _("Email"), email,
                       _("Phone"), phone,
                       _("Address"), address,
                       _("Back"), _("Continue"),
                       vendor_id, name, email, phone, address)

        return out

    def tmpl_update_vendor_info_step5(self, ln=CFG_SITE_LANG):
        """
        @param ln: language
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += load_menu(ln)

        out += """
            <div class="bibcircbottom">
              <br />
              <br />
              <table class="bibcirctable">
                <tr>
                    <td class="bibcirccontent">%s</td>
                </tr>
                </table>
                <br />
                <table class="bibcirctable">
                <tr>
                  <td>
                       <input type=button value="%s"
                 onClick="location.href='%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s'"
                        class="formbutton">
                  </td>
                 </tr>
                </table>
                <br />
                <br />
                </div>
                """ % (_("The information has been updated."),
                       _("Back to home"),
                       CFG_SITE_URL, ln)

        return out

    def tmpl_search_vendor_step1(self, infos, ln=CFG_SITE_LANG):
        """
        @param infos: information for the infobox.
        @type infos: list

        @param ln: language
        """
        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += load_menu(ln)

        out += """
        <div class="bibcircbottom">
        <br />
        <br />
        <br />
        <form name="search_vendor_step1_form"
              action="%s/admin2/bibcirculation/search_vendor_step2"
              method="get" >
          <table class="bibcirctable">
           <tr align="center">
             <td class="bibcirctableheader">%s
               <input type="radio" name="column" value="name" checked>%s
               <input type="radio" name="column" value="email">%s
               <br>
               <br>
             </td>
           </tr>
           """ % (CFG_SITE_URL,
                  _("Search vendor by"),
                  _("name"),
                  _("email"))

        out += """
           <tr align="center">
             <td>
                <input type="text" size="45" name="string" id='string'
                       style='border: 1px solid #cfcfcf'>
                <script language="javascript" type="text/javascript">
                    document.getElementById("string").focus();
                </script>
             </td>
           </tr>
          </table>
          <br />
          <table class="bibcirctable">
             <tr align="center">
                  <td>
                        <input type=button value='%s'
                          onClick="history.go(-1)" class="formbutton">
                        <input type="submit" value='%s' class="formbutton">
                  </td>
             </tr>
        </table>
        <form>
        <br />
        <br />
        <br />
        <br />
        </div>

        """ % (_("Back"), _("Search"))


        return out

    def tmpl_search_vendor_step2(self, result, ln=CFG_SITE_LANG):
        """
        @param result: search result
        @type result:list

        @param ln: language
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += load_menu(ln)

        out += """
        <style type="text/css"> @import url("/css/tablesorter.css"); </style>
        <div class="bibcircbottom" align="center">
        <br />
        <table class="bibcirctable">
          <tr align="center">
            <td class="bibcirccontent">
              <strong>%s vendor(s) found</strong>
            </td>
          </tr>
        </table>
        <br />
        <table class="tablesortersmall" border="0" cellpadding="0" cellspacing="1">
          <tr align="center">
             <th>%s</th>
           </tr>
        """ % (len(result), _("Vendor(s)"))

        for (vendor_id, name) in result:

            vendor_link = create_html_link(CFG_SITE_URL +
                                '/admin2/bibcirculation/get_vendor_details',
                                {'vendor_id': vendor_id, 'ln': ln}, (name))

            out += """
            <tr align="center">
                 <td class="bibcirccontent" width="70">%s
                 <input type=hidden name=library_id value="%s"></td>
            </tr>
            """ % (vendor_link, vendor_id)

        out += """
        </table>
        <br />
        <table class="bibcirctable">
             <tr align="center">
                  <td>
                    <input type=button value="%s"
                     onClick="history.go(-1)" class="formbutton"></td>
             </tr>
        </table>
        <br />
        <br />
        <br />
        </form>
        </div>

        """ % (_("Back"))

        return out

    def tmpl_vendor_details(self, vendor_details, ln=CFG_SITE_LANG):
        """
        @param vendor_details: details about a given vendor
        @type vendor_details: tuple

        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        out = """
        """
        out += load_menu(ln)

        out += """
        <div class="bibcircbottom" align="center">
        <br />
        <style type="text/css"> @import url("/css/tablesorter.css"); </style>
        """
        (vendor_id, name, address, email, phone, notes) = vendor_details

        no_notes_link = create_html_link(CFG_SITE_URL +
                                    '/admin2/bibcirculation/get_vendor_notes',
                                    {'vendor_id': vendor_id},
                                    (_("No notes")))

        see_notes_link = create_html_link(CFG_SITE_URL +
                                    '/admin2/bibcirculation/get_vendor_notes',
                                    {'vendor_id': vendor_id},
                                    (_("Notes about this vendor")))

        if notes == "" or str(notes) == '{}':
            notes_link = no_notes_link
        else:
            notes_link = see_notes_link

        out += """
            <table class="bibcirctable">
                 <tr align="center">
                      <td width="80" class="bibcirctableheader">%s</td>
                 </tr>
            </table>
            <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">

                 <tr>
                      <th width="80">%s</th>
                      <td class="bibcirccontent">%s</td>
                 </tr>
                 <tr>
                      <th width="80">%s</th>
                      <td class="bibcirccontent">%s</td>
                 </tr>
                 <tr>
                      <th width="80">%s</th>
                      <td class="bibcirccontent">%s</td>
                 </tr>
                 <tr>
                      <th width="80">%s</th>
                      <td class="bibcirccontent">%s</td>
                 </tr>
                 <tr>
                      <th width="80">%s</th>
                      <td class="bibcirccontent">%s</td>
                 </tr>
                 </table>
                 <table>
                 <tr>
                      <td><input type=button onClick="location.href='%s/admin2/bibcirculation/update_vendor_info_step3?vendor_id=%s'" onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
                      value="%s"  class="bibcircbutton">
                      </td>
                 </tr>
            </table>
            """ % (_("Vendor details"),
                   _("Name"), name,
                   _("Address"), address,
                   _("Email"), email,
                   _("Phone"), phone,
                   _("Notes"), notes_link,
                   CFG_SITE_URL, vendor_id, _("Update"))

        out += """
           </table>
           <br />
           <br />
           <table class="bibcirctable">
                <tr align="center">
                     <td><input type=button value='%s'
                          onClick="history.go(-1)" class="formbutton"></td>
                </tr>
           </table>
           <br />
           <br />
           <br />
           </form>
           </div>
           """ % (_("Back"))

        return out

    def tmpl_vendor_notes(self, vendor_notes, vendor_id, add_notes,
                          ln=CFG_SITE_LANG):

        _ = gettext_set_language(ln)

        out = """ """

        out += load_menu(ln)

        out += """
            <div class="bibcircbottom">
            <form name="vendor_notes" action="%s/admin2/bibcirculation/get_vendor_notes" method="get" >
            <br />
            <br />
            <table class="bibcirctable">
                  <tr>
                     <td class="bibcirctableheader">%s</td>
                  </tr>
                  """ % (CFG_SITE_URL,
                         _("Notes about this vendor"))

        notes = vendor_notes.split('\n')


        for values in notes:
            out += """ <tr>
                        <td class="bibcirccontent">%s</td>
                       </tr>
                       """ % (values)

        if add_notes:
            out += """
                <tr>
                  <td><textarea name='new_note' rows="10" cols="60" style='border: 1px solid #cfcfcf'></textarea></td>
                  </tr>
                   <tr>
                  <td>
                      <input type='submit' name='confirm_note' value='%s' class='formbutton'>
                      <input type=hidden name=vendor_id value="%s">
                  </td>
             </tr>
            </table>

            """ % (_("Confirm"), vendor_id)

        else:
            out += """
                <tr><td></td></tr>
                <tr><td></td></tr>
                <tr><td></td></tr>
                <tr>
                  <td>
                       <input type='submit' name='add_notes' value='%s' class='formbutton'>
                       <input type=hidden name=vendor_id value="%s">
                  </td>
             </tr>
            </table>

            """ % (_("Add notes"), vendor_id)

        out += """
            <br />
            <br />
             <table class="bibcirctable">
             <tr>
                  <td>
                       <input type=button
        onClick="location.href='%s/admin2/bibcirculation/get_vendor_details?vendor_id=%s&ln=%s'"
                       value="%s" class='formbutton'>
                  </td>
             </tr>
             </table>
             <br />
             <br />
             <br />
             </form>
             </div>
        """ % (CFG_SITE_URL,
               vendor_id, ln,
               _("Back"))

        return out
