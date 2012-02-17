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

""" Templates for bibcirculation module """

__revision__ = "$Id$"

import datetime
import time
import cgi

from invenio.urlutils import create_html_link
from invenio.config import CFG_SITE_URL, CFG_SITE_LANG, \
     CFG_CERN_SITE, CFG_SITE_SECURE_URL, CFG_SITE_RECORD
from invenio.bibcirculation_config import CFG_BIBCIRCULATION_LIBRARIAN_EMAIL
from invenio.messages import gettext_set_language

import invenio.bibcirculation_dblayer as db
from invenio.bibcirculation_utils import get_book_cover, \
      book_information_from_MARC, \
      book_title_from_MARC, \
      renew_loan_for_X_days, \
      get_item_info_for_search_result, \
      all_copies_are_missing, \
      has_copies, \
      looks_like_dictionary


_MENU_ = """

      <div id="cdlhead">
      <map name="Navigation_Bar" id="cdlnav">
      <div id="bibcircmenu" class="cdsweb">
      <h2><a name="localNavLinks">Main navigation links:</a></h2>
      <ul>
      <!-- <li>
       <a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py">Home</a>
      </li> -->

    <li>
        <a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1">Loan</a>
    </li>

    <li>
        <a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/loan_return">Return</a>
    </li>

    <li>
        <a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/borrower_search?redirect='yes'">Request</a>
    </li>

    <li>
        <a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/borrower_search">Borrowers</a>
    </li>

<!--
     <li class="hassubmenu">
         <a href="#">Borrowers</a>
         <ul class="subsubmenu">
          <li><a href = "%(url)s/admin/bibcirculation/bibcirculationadmin.py/borrower_search">Search...</a></li>
          <li><a href = "%(url)s/admin/bibcirculation/bibcirculationadmin.py/borrower_notification">Notify</a></li>
          <li><a href = "%(url)s/admin/bibcirculation/bibcirculationadmin.py/add_new_borrower_step1">Add new borrower</a></li>
          <li><a href = "%(url)s/admin/bibcirculation/bibcirculationadmin.py/update_borrower_info_step1">Update info</a></li>
         </ul>
        </li>
-->
    <li>
        <a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/item_search">Items</a>
    </li>
<!--
     <li class="hassubmenu">
         <a href="#">Items</a>
        <ul class="subsubmenu">
          <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/item_search">Search...</a></li>
          <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/new_item">Add new item</a></li>
          <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/add_new_copy_step1">Add new copy</a></li>
          <li><a href="#"># - Remove</a></li>
          <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/update_item_info_step1">Update info</a></li>
        </ul>
        </li>
-->

    <li class="hassubmenu">
         <a href="#">Lists</a>
        <ul class="subsubmenu">
          <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/all_loans">Last loans</a></li>
          <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/all_expired_loans">Overdue loans</a></li>
          <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/get_pending_requests">Items on shelf with holds</a></li>
          <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/get_waiting_requests">Items on loan with holds</a></li>
          <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/get_expired_loans_with_requests">Overdue loans with holds</a></li>
          <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/ordered_books">Ordered books</a></li>
     <!-- <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/all_loans_test">TEST loans</a></li>
          <li><a href="#"># - Stats</a></li> -->
        </ul>
    </li>

<!--
     <li class="hassubmenu">
         <a href="#">Loans</a>
         <ul class="subsubmenu">
         <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1">On library desk</a></li>
             <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/loan_return">Return book</a></li>
             <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/all_loans">List of all loans</a></li>
             <li><a href="#"># - Stats</a></li>
            </ul>
        </li>

     <li class="hassubmenu">
         <a href="#">Requests</a>
         <ul class="subsubmenu">
             <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/get_pending_requests">List of pending requests</a></li>
             <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/all_requests">List of hold requests</a></li>
             <li><a href="#"># - Stats</a></li>
            </ul>
        </li>
-->

    <li class="hassubmenu">
         <a href="#">Libraries</a>
         <ul class="subsubmenu">
             <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/search_library_step1">Search...</a></li>
             <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/add_new_library_step1">Add new library</a></li>
             <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/update_library_info_step1">Update info</a></li>
          </ul>
    </li>

    <li class="hassubmenu">
         <a href="#">Vendors</a>
        <ul class="subsubmenu">
             <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/search_vendor_step1">Search...</a></li>
             <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/add_new_vendor_step1">Add new vendor</a></li>
             <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/update_vendor_info_step1">Update info</a></li>
        </ul>
    </li>

    <li class="hassubmenu">
         <a href="#">Acquisitions</a>
        <ul class="subsubmenu">
             <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/ordered_books">List of ordered books</a></li>
             <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/new_book_step1">Order new book</a></li>
        </ul>
    </li>

    <li class="hassubmenu">
         <a href="#">ILL</a>
        <ul class="subsubmenu">
            <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/ill_search">Search...</a></li>
            <!--<li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/list_ill_request">All requests</a></li>-->
            <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/list_ill_request?status=new">New</a></li>
            <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/list_ill_request?status=requested">Requested</a></li>
            <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/list_ill_request?status=on loan">On loan</a></li>

            <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/register_ill_book_request">Register Book request</a></li>
            <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/register_ill_article_request_step1">Register Article request</a></li>
        </ul>
    </li>

    <li class="hassubmenu">
         <a href="#">Help</a>
        <ul class="subsubmenu">
          <li><a href="%(url)s/help/admin/bibcirculation-admin-guide" target="_blank">Admin guide</a></li>
             <!-- <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/help_contactsupport">Contact Support</a></li> -->
        </ul>
    </li>
    </ul>
    <div class="clear"></div>
    </div>
    </map>
    </div>

        """ % {'url': CFG_SITE_URL}


class Template:
    """Templates for BibCirculation module"""

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


    def tmpl_holdings_information2(self, recid, req, holdings_info,
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

        _ = gettext_set_language(ln)

        if not book_title_from_MARC(recid):
            out = """<div align="center"
                     <div class="infoboxmsg">
                      This record does not exist.
                      </div>"""
            return out

        elif not has_copies(recid):
            out = """<div align="center"
                     <div class="infoboxmsg">
                      This record has no copies.
                      </div>"""
            return out

        # verify if all copies are missing
        elif all_copies_are_missing(recid):

            ill_link = """<a href='%s/%s/%s/holdings/ill_request_with_recid'>ILL services</a>""" % (CFG_SITE_URL, CFG_SITE_RECORD, recid)

            out = """<div align="center"
                     <div class="infoboxmsg">
                      All the copies of <strong>%s</strong> are missing.You can request a copy using <strong>%s</strong>.
                      </div>""" % (book_title_from_MARC(recid), ill_link)

            return out

        # verify if there are no copies
        elif not holdings_info:
            out = """<div align="center"
                     <div class="infoboxmsg">
                      This item has no holdings.
                      </div>"""
            return out

        out = """
            <style type="text/css"> @import url("/img/tablesorter.css"); </style>
            <script src="/js/jquery.js" type="text/javascript"></script>
            <script src="/js/jquery.tablesorter.js" type="text/javascript"></script>
            <script type="text/javascript">
            $(document).ready(function() {
              $('#table_holdings').tablesorter({widthFixed: true, widgets: ['zebra']})
            });
            </script>
        """

        out += """
                   <table id="table_holdings" class="tablesorter" border="0" cellpadding="0" cellspacing="1">
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
                   """ % (_("Barcode"), _("Library"), _("Collection"),
                          _("Location"), _("Description"), _("Loan period"),
                          _("Status"), _("Due date"), _("Option(s)"))

        for (barcode, library, collection, location, description,
             loan_period, status, due_date) in holdings_info:

            if status == 'Not for loan':
                request_button = '-'
            else:
                request_button = """<input type=button onClick="location.href='%s/%s/%s/holdings/request?barcode=%s'"
                                    value='%s' class="bibcircbutton" onmouseover="this.className='bibcircbuttonover'"
                                    onmouseout="this.className='bibcircbutton'">""" % (CFG_SITE_URL, CFG_SITE_RECORD, recid,
                                                                                       barcode, _("Request"))
            if status == 'missing':
                out += """ """
            else:
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

                """ % (barcode, library, collection or '-', location,
                       description or '-', loan_period, status,
                       due_date or '-', request_button)

        from invenio.bibcirculationadminlib import is_adminuser
        (auth_code, _auth_message) = is_adminuser(req)

        if auth_code != 0:
            bibcirc_link = ''
        else:
            bibcirc_link = create_html_link(CFG_SITE_URL +
                                            '/admin/bibcirculation/bibcirculationadmin.py/get_item_details',
                                            {'recid': recid, 'ln': ln},
                                            _("See this book on BibCirculation"))

        out += """
            </tbody>
           </table>
           <br />
           <br />
           <table class="bibcirctable">
             <tr>
               <td class="bibcirctableheader">%s</td>
             </tr>
           </table>
           """ % (bibcirc_link)

        return out

    def tmpl_book_not_for_loan(self):
        message = """<div align="center"
                     <div class="infoboxmsg">
                      This item is not for loan.
                      </div>"""
        return message

    def tmpl_message_request_send_ok_cern(self):

        message =  "Your request has been registered and the document"\
                              " will be sent to you via internal mail."

        return message

    def tmpl_message_request_send_ok_other(self):

        message = "Your request has been registered."

        return message

    def tmpl_message_request_send_fail_cern(self):

        message = "It is not possible to validate your request. "\
                              "Your office address is not available. "\
                              "Please contact " + CFG_BIBCIRCULATION_LIBRARIAN_EMAIL

        return message

    def tmpl_message_request_send_fail_other(self):

        message = "It is not possible to validate your request. "\
                              "Your office address is not available. "\
                              "Please contact " + CFG_BIBCIRCULATION_LIBRARIAN_EMAIL

        return message

    def tmpl_borrower_search_result(self, result, redirect='no', ln=CFG_SITE_LANG):
        """
        When the admin features 'borrower_seach' is used, this template
        show the result.

        @param result: search result
        @type result:list

        @param ln: language
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_

        if len(result) == 0:
            out += """
            <div class="bibcircbottom">
            <br />
            <div class="infoboxmsg">%s</div>
            <br />
          """ % (_("0 borrower(s) found."))

        else:
            out += """
        <style type="text/css"> @import url("/img/tablesorter.css"); </style>
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
                if redirect == 'no':
                    borrower_link = create_html_link(CFG_SITE_URL +
                                             '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_details',
                                             {'borrower_id': borrower_id, 'ln': ln},
                                             (name))
                else:
                    borrower_link = create_html_link(CFG_SITE_URL +
                                             '/admin/bibcirculation/bibcirculationadmin.py/create_new_request_step1',
                                             {'borrower_id': borrower_id, 'ln': ln},
                                             (name))

                out += """
            <tr align="center">
                 <td width="70">%s
                 <input type=hidden name=uid value=%s></td>
            </tr>

            """ % (borrower_link, borrower_id)

        out += """
             </table>
             <br />
             <table class="bibcirctable">
             <tr align="center">
                  <td><input type=button value=%s onClick="history.go(-1)" class="formbutton"></td>
             </tr>
        </table>
        <br />
        <br />
        <br />
        </form>
        </div>
        """ % (_("Back"))

        return out


    def tmpl_yourloans(self, loans, requests, borrower_id,
                       infos, ln=CFG_SITE_LANG):
        """
        When an user is logged in, it is possible to check his loans.
        In the section 'yourloans', it is also possible to renew a single
        loan or all loans.

        @param result: show all loans of an user who is logged in
        @param uid: user ID
        @param infos: display information about holdings
        @param ln: language
        """
        _ = gettext_set_language(ln)

        renew_all_link = create_html_link(CFG_SITE_SECURE_URL +
                                          '/yourloans/display',
                                          {'borrower_id': borrower_id},
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
            <br />
            <table class="bibcirctable_contents">
                 <td align="center" class="bibcirccontent">%s</td>
            </table>
            <br />
            <br />
            """ % (_("You don't have any book on loan."))

        else:
            out += """<br />
                      <style type="text/css"> @import url("/img/tablesorter.css"); </style>
                      <script src="/js/jquery.js" type="text/javascript"></script>
                      <script src="/js/jquery.tablesorter.js" type="text/javascript"></script>
                      <script type="text/javascript">
                      $(document).ready(function() {
                        $('#table_loans').tablesorter()
                      });
                      </script>

                      <table class="tablesortermedium" id="table_loans" border="0" cellpadding="0" cellspacing="1">
                      <thead>
                        <tr>
                         <th>%s</th>
                         <th>%s</th>
                         <th>%s</th>
                         <th>%s</th>
                        </tr>
                      </thead>
                      <tbody>
                     """ % (_("Item"),
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
                                                  {'barcode': barcode},
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
                          <br />
                          <br />
                          """ % (renew_all_link)


        if len(requests) == 0:
            out += """
                   <h1 class="headline">%s</h1>
                   <div class="bibcirctop">
                   <br /> <br />
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
                   """  % (_("Your Requests"),
                           _("You don't have any request (waiting or pending)."),
                           loanshistoricaloverview_link,
                           CFG_SITE_URL,
                           _("Back to home"))


        else:
            out +="""
                   <h1 class="headline">%s</h1>
                   <div class="bibcirctop">
                   <br />
                   <style type="text/css"> @import url("/img/tablesorter.css"); </style>
                   <script src="/js/jquery.js" type="text/javascript"></script>
                   <script src="/js/jquery.tablesorter.js" type="text/javascript"></script>
                   <script type="text/javascript">
                   $(document).ready(function() {
                        $('#table_requests').tablesorter()
                   });
                   </script>
                   <table class="tablesortermedium" id="table_requests" border="0" cellpadding="0" cellspacing="1">
                   <thead>
                   <tr>
                     <th>%s</th>
                     <th>%s</th>
                     <th>%s</th>
                     <th>%s</th>
                   </tr>
                   </thead>
                   <tbody>
                   """ % (_("Your Requests"),
                          _("Item"),
                          _("Request date"),
                          _("Status"),
                          _("Action(s)"))

            for(request_id, recid, request_date, status) in requests:

                record_link = "<a href=" + CFG_SITE_URL + "/%s/%s>" % (CFG_SITE_RECORD, recid) + \
                              (book_title_from_MARC(recid)) + "</a>"

                cancel_request_link = create_html_link(CFG_SITE_URL +
                                                       '/yourloans/display',
                                                       {'request_id': request_id},
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

            out +="""     </tbody>
                          </table>
                          <br />
                          <br />
                          <br />
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
                          <br />
                          </div>
                          """ % (loanshistoricaloverview_link,
                                 CFG_SITE_URL,
                                 _("Back to home"))

        return out


    def tmpl_loanshistoricaloverview(self, result, ln):
        """
        In the section 'yourloans' it is possible to see the loans historical overview
        of the user who is logged in. Bibcirculation display all loans where the status is
        'returned'.

        @param result: show all loans where status = 'returned'
        @param ln: language
        """

        _ = gettext_set_language(ln)

        out = """<div class="bibcirctop_bottom">
                    <br /> <br />
                    <style type="text/css"> @import url("/img/tablesorter.css"); </style>
                    <script src="/js/jquery.js" type="text/javascript"></script>
                    <script src="/js/jquery.tablesorter.js" type="text/javascript"></script>
                    <script type="text/javascript">
                    $(document).ready(function() {
                        $('#table_hist').tablesorter()
                    });
                    </script>
                    <table class="tablesortermedium" id="table_hist" border="0" cellpadding="0" cellspacing="1">
                    <thead>
                    <tr>
                      <th>%s</th>
                      <th>%s</th>
                      <th>%s</th>
                      <th>%s</th>
                    </tr>
                    </thead>
                    <tbody>
                    """ % (_("Item"),
                           _("Loaned"),
                           _("Returned"),
                           _("Renewalls"))

        for(recid, loaned_on, returned_on, nb_renewalls) in result:

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
                       returned_on, nb_renewalls)

        out += """</tbody>
                  </table>
                  <br />
                  <table class="bibcirctable">
                  <tr>
                  <td>
                  <input type=button value=%s onClick="history.go(-1)" class="formbutton">
                  </td>
                  </tr>
                  </table>
                  <br />
                  <br />
                  </div>
                  """ % (_("Back"))

        return out


    def tmpl_new_request(self, uid, recid, barcode, ln=CFG_SITE_LANG):
        """
        This template is used when an user want to request a book. Here it is
        possible to define the 'period of interest'

        @param uid: user ID
        @param recid: recID - Invenio record identifier
        @param barcode: book barcode
        @param ln: language
        """

        _ = gettext_set_language(ln)

        today = datetime.date.today()
        out = """
        <form name="request_form" action="%s/%s/%s/holdings/send" method="get" >
        <div class="bibcirctableheader" align="center">%s</div>
        <br />
             <table class="bibcirctable_contents">
                  <tr>
                       <td class="bibcirctableheader">%s</td>
                       <td class="bibcirctableheader">%s</td>
                       <td class="bibcirctableheader">%s</td>
                       <td class="bibcirctableheader">%s</td>
                  </tr>
        """ % (CFG_SITE_URL,
               CFG_SITE_RECORD,
               recid,
               _("Enter your period of interest"),
               _("From"),
               _("Year"),
               _("Month"),
               _("Day"))


        out += """
        <tr>
             <td class="bibcirccontent" width="30"></td>
             <td class="bibcirccontent" width="30"><input size=4 style='border: 1px solid #cfcfcf' name="from_year" value=%(from_year)s></td>
             <td class="bibcirccontent" width="30"><input size=2 style='border: 1px solid #cfcfcf' name="from_month" value=%(from_month)s></td>
             <td class="bibcirccontent" width="30"><input size=2 style='border: 1px solid #cfcfcf' name="from_day" value=%(from_day)s></td>
        </tr>
        """

        out += """
        <tr>
             <td class="bibcirctableheader" width="30">%s</td>
             <td class="bibcirctableheader" width="30">%s</td>
             <td class="bibcirctableheader" width="30">%s</td>
             <td class="bibcirctableheader" width="30">%s</td>
        </tr>
        """ % (_("To"),
               _("Year"),
               _("Month"),
               _("Day"))


        out +=  """
        <tr>
             <td class="bibcirccontent" width="30"></td>
             <td class="bibcirccontent" width="30"><input size=4 style='border: 1px solid #cfcfcf' name="to_year" value=%(to_year)s></td>
             <td class="bibcirccontent" width="30"><input size=2 style='border: 1px solid #cfcfcf' name="to_month" value=%(to_month)s></td>
             <td class="bibcirccontent" width="30"><input size=2 style='border: 1px solid #cfcfcf' name="to_day" value=%(to_day)s></td>
        </tr>
        </table>
        <br /> <br />
        """

        out += """
        <table class="bibcirctable_contents">
             <tr>
                  <td align="center">
                     <input type=button value="Back" onClick="history.go(-1)" class="formbutton">
                     <input type="submit" name="submit_button" value="%(submit_button)s" class="formbutton">
                     <input type=hidden name=barcode value='%(barcode)s'>
                  </td>

        </tr>
        </table>
        <br /> <br />
        </form>
        """

        out = out % {'url': CFG_SITE_URL,
                     'from_year' : today.year,
                     'from_month' : today.month,
                     'from_day': today.day,
                     'to_year': today.year + 1,
                     'to_month': today.month,
                     'to_day': today.day,
                     'submit_button': ('Confirm'),
                     'recid': recid,
                     'uid': uid,
                     'barcode': barcode
                     }

        return out

    def tmpl_new_request2(self, recid, barcode, ln=CFG_SITE_LANG):
        """
        This template is used when an user want to request a book. Here it is
        possible to define the 'period of interest'

        @param uid: user ID
        @param recid: recID - Invenio record identifier
        @param barcode: book's barcode
        @param ln: language
        """

        _ = gettext_set_language(ln)

        today = datetime.date.today()
        gap = datetime.timedelta(days=180)
        more_6_months = (today + gap).strftime('%Y-%m-%d')

        out = """
        <style type="text/css"> @import url("/img/tablesorter.css"); </style>
        <link rel=\"stylesheet\" href=\"%s/img/jquery-ui.css\" type=\"text/css\" />
        <script type="text/javascript" language='JavaScript' src="%s/js/jquery-ui.min.js"></script>

        <form name="request_form" action="%s/%s/%s/holdings/send" method="get" >
        <br />
        <div align=center>
          <table class="bibcirctable_contents" align=center>
            <tr>
              <td class="bibcirctableheader" align=center>%s</td>
            </tr>
          </table>
          <br />

          <table align=center class="tablesorterborrower" width="100" border="0" cellspacing="1" align="center">

            <tr align=center>
              <th align=center>%s</th>
              <td>

                <script type="text/javascript">
                    $(function(){
                        $("#date_picker1").datepicker({dateFormat: 'yy-mm-dd', showOn: 'button', buttonImage: "%s/img/calendar.gif", buttonImageOnly: true});
                    });
                </script>
                <input type="text" size="12" id="date_picker1" name="period_from" value="%s" style='border: 1px solid #cfcfcf'>

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
                <input type="text" size="12" id="date_picker2" name="period_to" value="%s" style='border: 1px solid #cfcfcf'>

              </td>
            </tr>
          </table>
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
        """ % (CFG_SITE_URL, CFG_SITE_URL,
               CFG_SITE_URL, CFG_SITE_RECORD, recid,
               _("Enter your period of interest"),
               _("From"),CFG_SITE_URL, today, _("To"), CFG_SITE_URL, more_6_months,
               barcode, _("Back"), _("Confirm"))

        return out

    def tmpl_new_request_send(self, message, ln=CFG_SITE_LANG):
        """
        This template is used in the user interface.

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
        <td class="bibcirccontent" width="30">%s<a href="%s">%s</a>%s</td>
        </tr>
        </table>
        <br /> <br />
        <table class="bibcirctable">
        <td><input type=button onClick="location.href='%s'" value='%s' class='formbutton'></td>
        </table>
        <br /> <br />
        """ % (message,
               _("You can see your loans "),
               CFG_SITE_URL + '/yourloans/display',
               _("here"),
               _("."),
               CFG_SITE_URL,
               _("Back to home"))

        return out


    def tmpl_next_loan_request_done(self, ln=CFG_SITE_LANG):
        """
        This template is used in the admin interface, when a request is
        'waiting' in the queue.

        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        out = _MENU_

        out += """
        <div class="bibcircbottom">
            <br /> <br />
            <table class="bibcirctable">
            <td class="bibcirccontent" width="30">%s</td>
            </table>
            <br /> <br />
            <table class="bibcirctable">
            <td><input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1'"
            value=%s class='formbutton'></td>
            </table>
            <br /> <br />
        </div>
        """ % (_("A new loan has been registered."),
               CFG_SITE_URL,
               _("Back to home"))

        return out

    def tmpl_get_pending_requests(self, result, ln=CFG_SITE_LANG):

        """
        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = _MENU_

        out += """
            <style type="text/css"> @import url("/js/tablesorter/themes/blue/style.css"); </style>
            <style type="text/css"> @import url("/js/tablesorter/addons/pager/jquery.tablesorter.pager.css"); </style>

            <script src="/js/tablesorter/jquery.tablesorter.js" type="text/javascript"></script>
            <script src="/js/tablesorter/addons/pager/jquery.tablesorter.pager.js" type="text/javascript"></script>
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
            """

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
            <form name="borrower_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/all_loans" method="get" >
            <br />
            <table id="table_all_loans" class="tablesorter" border="0" cellpadding="0" cellspacing="1">
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
                       """%  (CFG_SITE_URL,
                              _("Name"),
                              _("Item"),
                              _('Library'),
                              _("Location"),
                              _("From"),
                              _("To"),
                              _("Request date"),
                              _("Actions"))

            for (request_id, recid, name, borrower_id, library, location, date_from, date_to, request_date) in result:

                title_link = create_html_link(CFG_SITE_URL +
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_item_details',
                                          {'recid': recid, 'ln': ln},
                                          (book_title_from_MARC(recid)))

                borrower_link = create_html_link(CFG_SITE_URL +
                                             '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_details',
                                             {'borrower_id': borrower_id, 'ln': ln},
                                             (name))

                out += """
                <script type="text/javascript">
                function confirmation() {
                  var answer = confirm("Delete this request?")
                  if (answer){
                    window.location = "%s/admin/bibcirculation/bibcirculationadmin.py/get_pending_requests?request_id=%s";
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
                 no-repeat; width: 75px; text-align: right;"
                 onClick="confirmation()"
                 onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
                 class="bibcircbutton">


                 <input type=button style="background: url(/img/dialog-yes.png) no-repeat; width: 150px; text-align: right;"
                 onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/associate_barcode?request_id=%s&recid=%s&borrower_id=%s'"
                 onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
                 value='%s' class="bibcircbutton">
                 </td>
                </tr>
                """ % (CFG_SITE_URL,
                       request_id,
                       borrower_link,
                       title_link,
                       library,
                       location,
                       date_from,
                       date_to,
                       request_date,
                       _("Delete"),
                       CFG_SITE_URL,
                       request_id,
                       recid,
                       borrower_id,
                       _("Associate barcode"))

            out+= """
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
                                <td><input type=button value='%s' onClick="history.go(-1)" class="formbutton"></td>
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
        Template for the admin interface. Show pending requests(all, on loan, available)

        @param result: items with status = 'pending'
        @param ln: language
        """

        _ = gettext_set_language(ln)

        out = _MENU_

        out += """
            <style type="text/css"> @import url("/js/tablesorter/themes/blue/style.css"); </style>
            <style type="text/css"> @import url("/js/tablesorter/addons/pager/jquery.tablesorter.pager.css"); </style>

            <script src="/js/tablesorter/jquery.tablesorter.js" type="text/javascript"></script>
            <script src="/js/tablesorter/addons/pager/jquery.tablesorter.pager.js" type="text/javascript"></script>
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
            """

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
            <form name="borrower_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/all_loans" method="get" >
            <br />
            <table id="table_all_loans" class="tablesorter" border="0" cellpadding="0" cellspacing="1">
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

            for (request_id, recid, name, borrower_id, library, location,
                 date_from, date_to, request_date) in result:

                title_link = create_html_link(CFG_SITE_URL +
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_item_details',
                                          {'recid': recid, 'ln': ln},
                                          (book_title_from_MARC(recid)))

                borrower_link = create_html_link(CFG_SITE_URL +
                                             '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_details',
                                             {'borrower_id': borrower_id, 'ln': ln},
                                             (name))

                out += """
                <script type="text/javascript">
                function confirmation() {
                  var answer = confirm("Delete this request?")
                  if (answer){
                    window.location = "%s/admin/bibcirculation/bibcirculationadmin.py/get_pending_requests?request_id=%s";
                    }
                  else{
                    alert("Request not deleted.")
                    }
                 }
                </script>
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
                 no-repeat; width: 75px; text-align: right;"
                 onClick="confirmation()"
                 class="bibcircbutton">

                 <input type=button type=button style="background: url(/img/dialog-yes.png) no-repeat; width: 150px; text-align: right;" onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/associate_barcode?request_id=%s&recid=%s&borrower_id=%s'"
                 value='%s' class="bibcircbutton">
                 </td>
                </tr>
                """ % (CFG_SITE_URL,
                       request_id,
                       borrower_link,
                       title_link,
                       library,
                       location,
                       date_from,
                       date_to,
                       request_date,
                       _("Cancel"),
                       CFG_SITE_URL,
                       request_id,
                       recid,
                       borrower_id,
                       _("Associate barcode"))

            out+= """
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
                                <td><input type=button value='%s' onClick="history.go(-1)" class="formbutton"></td>
                            </tr>
                        </table>
                    <br />
                    <br />
                    </form>
                    </div>
                    </div>
                    """ % (_("Back"))

        return out


    def tmpl_get_next_waiting_loan_request(self, result, recid, barcode, ln=CFG_SITE_LANG):
        """
        Template for the admin interface. Show the next request in the queue.

        @param result: next request with status = 'waiting'
        @param barcode: book's barcode
        @param ln: language
        """

        _ = gettext_set_language(ln)

        out = """
        """
        out += _MENU_


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
            <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1'"
            value="Back to home" class='formbutton'>
            </td>
            </table>
            <br />
            </div>
            """ % (_("No hold requests waiting."), CFG_SITE_URL)




        else:
            out += """
            <form name="list_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/get_next_waiting_loan_request" method="get" >
            <div class="bibcircbottom">
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
                       <td class="bibcirctableheader" align="center">%s</td>
                       <td width="10"><input type=hidden name=barcode value=%s></td>
                       <td width="10"><input type=hidden name=recid value=%s></td>
                    </tr>

                    """% (CFG_SITE_URL,
                          _("Name"),
                          _("Item"),
                          _("Request status"),
                          _("From"),
                          _("To"),
                          _("Request date"),
                          _("Request options"),
                          barcode,
                          recid)

            for (id_lr, name, recid, status, date_from, date_to, request_date) in result:

                out += """
                <tr  onMouseOver="this.className='highlight'" onMouseOut="this.className='normal'">
                 <td class="bibcirccontent">%s</td>
                 <td class="bibcirccontent">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">
                 <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/get_next_waiting_loan_request?check_id=%s&recid=%s&barcode=%s'"
                 value='%s' class="formbutton">
                 <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/update_next_loan_request_status?check_id=%s&barcode=%s'"
                 value='%s' class="formbutton"></td>
                 </td>
                 </tr>
                 """ % (
                        name, book_title_from_MARC(recid),
                        status, date_from, date_to,
                        request_date, CFG_SITE_URL,
                        id_lr, recid, barcode,
                        _("Cancel"), CFG_SITE_URL,
                        id_lr, barcode,
                        _('Select hold request'))

            out += """</table>
                  <br />
                  <br />
                  <br />
                  <table class="bibcirctable">
                       <tr>
                            <td>
                                 <input type=button value=%s
                                  onClick="history.go(-1)" class="formbutton">
                            </td>
                           </tr>
                  </table>
                  </form>
                  <br />
                  <br />
                  <br />
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

        out += _MENU_

        out += """
        <form name="return_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/loan_return_confirm" method="get">
        <div class="bibcircbottom">
        <br />
        <br />
        <br />
        <table class="bibcirctable_contents">
          <tr align="center">
            <td class="bibcirctableheader">
            %s
            <input type="text" size=45 id="barcode" name="barcode" style='border: 1px solid #cfcfcf'>
            </td>

          </tr>
        </table>

        """ % (CFG_SITE_URL,
               _("Barcode"))

        out += """
        <br />
        <table class="bibcirctable_contents">
          <tr align="center">
            <td>
              <input type="reset" name="reset_button" value=%s class="formbutton">
              <input type="submit" name="ok_button" value=%s class="formbutton">
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

    def tmpl_loan_return_confirm(self, borrower_name, borrower_id, recid,
                                 barcode, return_date, result, ln=CFG_SITE_LANG):
        """
        @param borrower_name: person who returned the book
        @param id_bibrec: book's recid
        @param barcode: book's barcode
        @param ln: language
        """
        _ = gettext_set_language(ln)

        out = """
        """
        out += _MENU_


        borrower_link = create_html_link(CFG_SITE_URL +
                                         '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_details',
                                         {'borrower_id': borrower_id, 'ln': ln},
                                         (borrower_name))

        title_link = create_html_link(CFG_SITE_URL +
                                      '/admin/bibcirculation/bibcirculationadmin.py/get_item_details',
                                      {'recid': recid, 'ln': ln},
                                      (book_title_from_MARC(recid)))

        out += """
           <form name="return_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/get_next_waiting_loan_request" method="get" >
             <div class="bibcircbottom">
             <br />
             <div class="infoboxsuccess">%s</div>
             <br />
             <table class="bibcirctable">
        """ % (CFG_SITE_URL, _("The item %(x_title)s with barcode %(x_barcode)s has been returned with success." % \
                             {'x_title': book_title_from_MARC(recid), 'x_barcode': barcode}))

        (_book_title, book_year, book_author, book_isbn, book_editor) = book_information_from_MARC(int(recid))

        if book_isbn:
            book_cover = get_book_cover(book_isbn)
        else:
            book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)

        out += """
        <tr>
             <td class="bibcirctableheader">%s</td>
        </tr>
        </table>
        <table class="bibcirctable">
          <tr valign='top'>
            <td width="350">
            <style type="text/css"> @import url("/img/tablesorter.css"); </style>
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
            <td class="bibcirccontent"><img style='border: 1px solid #cfcfcf' src="%s" alt="Book Cover"/></td>
            </tr>

        <input type=hidden name=recid value=%s>
        <input type=hidden name=barcode value=%s>

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
            </table>
            <div class="infoboxmsg">%s</div>
            <br />
            <style type="text/css"> @import url("/img/tablesorter.css"); </style>
            <script src="/js/jquery.js" type="text/javascript"></script>
            <script src="/js/jquery.tablesorter.js" type="text/javascript"></script>
            <script type="text/javascript">
            $(document).ready(function() {
              $('#table_requests').tablesorter({widthFixed: true, widgets: ['zebra']})
            });
            </script>
            <table class="bibcirctable">
              <tr>
                <td class="bibcirctableheader" width="100">%s</td>
              </tr>
            </table>
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
              </tr>
            </thead>
            </tbody>

            """% (_("There %s request(s) on the book who has been returned." % len(result)),
                  _("Waiting requests"),
                  _("Name"),
                  _("Item"),
                  _("Request status"),
                  _("From"),
                  _("To"),
                  _("Request date"),
                  _("Request options"))

            for (request_id, name, recid, status, date_from, date_to, request_date) in result:

                out += """
               <script type="text/javascript">
               function confirmation() {
                 var answer = confirm("Delete this request?")
                 if (answer){
                   window.location = "%s/admin/bibcirculation/bibcirculationadmin.py/get_next_waiting_loan_request?check_id=%s&recid=%s&barcode=%s";
                   }
                 }
               </script>

               """ % (CFG_SITE_URL, request_id, recid, barcode)

                out += """
                <tr>
                  <td>%s</td>
                  <td>%s</td>
                  <td>%s</td>
                  <td>%s</td>
                  <td>%s</td>
                  <td>%s</td>
                  <td>
                    <input type=button onClick="confirmation()" value='%s' class="bibcircbutton"
                    style="background: url(/img/dialog-cancel.png) no-repeat; width: 75px; text-align: right;">

                 <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/update_next_loan_request_status?check_id=%s&barcode=%s'"
                 value='%s' class="bibcircbutton" style="background: url(/img/dialog-yes.png) no-repeat; width: 125px; text-align: right;"></td>
                 </td>
                 </tr>
                 """ % (
                        name, book_title_from_MARC(recid),
                        status, date_from, date_to,
                        request_date, _("Delete"),
                        CFG_SITE_URL, request_id, barcode,
                        _('Select request'))

            out += """
            </table>
            """

        else:
            out += """
              </table>
              <div class="infoboxmsg">%s</div>""" % (_("There are no requests waiting on the item <strong>%s</strong>." % book_title_from_MARC(recid)))

            out += """
            <br />
            <br />
            <br />
            </div>
            </form>
            """

        return out


    def tmpl_index(self, ln=CFG_SITE_LANG):
        """
        Main page of the Admin interface.

        @param pending_request: display the number of pending requests
        @param ln: language
        """

        _ = gettext_set_language(ln)

        out = """  """

        out += _MENU_

        out += """
        <div class="bibcircbottom">
        <br />
        <div class="subtitle">
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


    def tmpl_borrower_search(self, infos, redirect='no', ln=CFG_SITE_LANG):
        """
        Template for the admin interface. Search borrower.

        @param ln: language
        """
        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += _MENU_

        out += """
        <div class="bibcircbottom">
        <br /><br />         <br />
        <form name="borrower_search" action="%s/admin/bibcirculation/bibcirculationadmin.py/borrower_search_result" method="get" >
             <table class="bibcirctable">
               <tr align="center">
                 <td class="bibcirctableheader">%s
                   <input type="radio" name="column" value="id">ccid
                   <input type="radio" name="column" value="name" checked>name
                   <input type="radio" name="column" value="email">email
                   <input type="hidden" name="redirect" value="%s">
                   <br>
                   <br>
                 </td>
               </tr>
               <tr align="center">
                 <td><input type="text" size="45" name="string" style='border: 1px solid #cfcfcf'></td>
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

        """ % (CFG_SITE_URL,
               _("Search borrower by"),redirect,
               _("Back"), _("Search"))


        return out


    def tmpl_item_search(self, infos, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += _MENU_

        out += """
        <div class="bibcircbottom">
        <form name="search_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/item_search_result" method="get" >
        <br />
        <br />
        <br />
        <input type=hidden value="0">
        <input type=hidden value="10">
        <table class="bibcirctable">
          <tr align="center">
            <td class="bibcirctableheader">Search item by
              <input type="radio" name="f" value="" checked>any field
              <input type="radio" name="f" value="barcode">barcode
              <input type="radio" name="f" value="author">author
              <input type="radio" name="f" value="title">title
              <br />
              <br />
            </td>
          </tr>
          <tr align="center">
          <td><input type="text" size="50" name="p" style='border: 1px solid #cfcfcf'></td>
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
        <form>

        """ % (CFG_SITE_URL, _("Back"), _("Search"))

        return out


    def tmpl_item_search_result(self, result, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = """  """

        out += _MENU_

        if result == None:
            out += """
            <div class="bibcircbottom">
            <br />
            <div class="infoboxmsg">%s</div>
            <br />
            """ % (_("0 item(s) found."))

        else:
            out += """
        <style type="text/css"> @import url("/img/tablesorter.css"); </style>
        <div class="bibcircbottom">
        <br />
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
               _("No. Copies"))

### FIXME: If one result -> go ahead ###
            for recid in result:

                (book_author, book_editor, book_copies) = get_item_info_for_search_result(recid)

                title_link = create_html_link(CFG_SITE_URL +
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_item_details',
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

    def tmpl_loan_on_desk_step1(self, result, key, string, infos, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += _MENU_

        out += """
        <div class="bibcircbottom">
        <form name="step1_form1" action="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1" method="get" >
        <br />
        <br />
        <br />
          <table class="bibcirctable" align="center">

            """  % (CFG_SITE_URL)

        if CFG_CERN_SITE == 1:

            out += """
                 <tr>
                   <td class="bibcirctableheader" align="center">Search user by
                   """

            if key == 'email':
                out += """
                   <input type="radio" name="key" value="ccid">ccid
                   <input type="radio" name="key" value="name">name
                   <input type="radio" name="key" value="email" checked>email
                   """

            elif key == 'name':
                out += """
                   <input type="radio" name="key" value="ccid">ccid
                   <input type="radio" name="key" value="name" checked>name
                   <input type="radio" name="key" value="email">email
                   """

            else:
                out += """
                   <input type="radio" name="key" value="ccid" checked>ccid
                   <input type="radio" name="key" value="name">name
                   <input type="radio" name="key" value="email">email
                   """

        else:
            out += """
                 <tr>
                   <td align="center" class="bibcirctableheader">Search borrower by
                   """

            if key == 'email':
                out += """
                   <input type="radio" name="key" value="id">id
                   <input type="radio" name="key" value="name">name
                   <input type="radio" name="key" value="email" checked>email
                   """

            elif key == 'id':
                out += """
                   <input type="radio" name="key" value="id" checked>id
                   <input type="radio" name="key" value="name">name
                   <input type="radio" name="key" value="email">email
                   """

            else:
                out += """
                   <input type="radio" name="key" value="id">id
                   <input type="radio" name="key" value="name" checked>name
                   <input type="radio" name="key" value="email">email
                   """

        out += """
                    <br><br>
                    </td>
                    </tr>
                    <tr>
                    <td align="center">
                    <input type="text" size="40" id="string" name="string"  value='%s' style='border: 1px solid #cfcfcf'>
                    </td>
                    </tr>
                    <tr>
                    <td align="center">
                    <br>
                    <input type="submit" value="Search" class="formbutton">
                    </td>
                    </tr>

                   </table>
          </form>
        """ % (string or '')

        if result:
            out += """
            <br />
            <form name="step1_form2" action="/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step2" method="get">
            <table class="bibcirctable">
              <tr width="200">
                <td align="center">
                  <select name="user_info" size="8" style='border: 1px solid #cfcfcf; width:200'>

              """
            for (ccid, name, email, phone, address, mailbox) in result:
                out += """
                       <option value ='%s,%s,%s,%s,%s,%s'>%s
                       """ % (ccid, name, email, phone, address, mailbox, name)

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


    def tmpl_loan_on_desk_step2(self, user_info, infos, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """
        (ccid, name, email, phone, address, mailbox) = user_info

        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += _MENU_

        out += """
            <div class="bibcircbottom">
            <style type="text/css"> @import url("/img/tablesorter.css"); </style>
            <form name="step2_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step3" method="get" >
              <br />
              <br />
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
                    <td class="bibcirctableheader" width="77">%s</td>
                  </tr>
                  <tr>
                    <td><textarea rows="5" cols="43" name="barcode" style='border: 1px solid #cfcfcf'></textarea></td>
                  </tr>
                </table>
                <br />
                <table class="bibcirctable">
                <tr>
                  <td>
                       <input type=button value=%s
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit"
                       value=%s class="formbutton">

                      <input type=hidden name="user_info" value="%s">

                  </td>
                 </tr>
                </table>
                </form>
                <br />
                <br />
                </div>
                """ % (CFG_SITE_URL, _("User information"),
                       _("ID"), ccid,
                       _("Name"), name,
                       _("Email"), email,
                       _("Phone"), phone,
                       _("Address"), address,
                       _("Mailbox"), mailbox,
                       _("Barcode(s)"), _("Back"),
                       _("Continue"),user_info)

        return out

    def tmpl_loan_on_desk_step3(self, user_info, list_of_books, infos,
                                ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """
        (ccid, name, email, phone, address, mailbox) = user_info
        #user_info = [str(ccid), str(name), str(email), str(phone), str(address), str(mailbox)]

        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += _MENU_

        out += """
            <div class="bibcircbottom">
            <style type="text/css"> @import url("/img/tablesorter.css"); </style>
            <form name="step3_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step4" method="get" >
              <br />
              <br />
              <input type=hidden name="list_of_books" value="%s">
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

                <script type="text/javascript" language='JavaScript' src="%s/js/jquery-ui.min.js"></script>

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
                """  % (CFG_SITE_URL, list_of_books, _("User information"),
                        _("ID"), ccid,
                        _("Name"), name,
                        _("Email"), email,
                        _("Phone"), phone,
                        _("Address"), address,
                        _("Mailbox"), mailbox,
                        _("List of borrowed books"),
                        CFG_SITE_URL,
                        _("Item"), _("Barcode"),
                        _("Library"), _("Location"),
                        _("Due date"), _("Write note(s)"))


        iterator = 1

        for (recid, barcode, library_id, location) in list_of_books:

            due_date = renew_loan_for_X_days(barcode)

            library_name = db.get_library_name(library_id)

            out +="""
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
                    <input type="text" size="12" id="%s" name="due_date" value="%s" style='border: 1px solid #cfcfcf'>

                    </td>
                  <td ><textarea name='note' rows="1" cols="40" style='border: 1px solid #cfcfcf'></textarea></td>
                </tr>
                """ % (book_title_from_MARC(recid), barcode,
                       library_name, location,
                        "#date_picker" + str(iterator), CFG_SITE_URL ,"date_picker" + str(iterator),due_date)


            iterator += 1

        out += """
                </tbody>
                </table>
                <br />
                <table class="bibcirctable">
                <tr>
                  <td>
                       <input type=button value=%s
                       onClick="history.go(-1)" class="formbutton">

                       <input type="submit"
                       value=%s class="formbutton">

                       <input type=hidden name="user_info" value="%s">
                  </td>
                 </tr>
                </table>
                </form>
                <br />
                <br />
                </div>
                """ % ( _("Back"), _("Continue"), str(user_info))

        return out


    def tmpl_loan_on_desk_step4(self, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = """
        """
        out += _MENU_

        out +="""<div class="bibcircbottom">
                 <br />
                 <br />
                 <br />
                 <br />
                 A new loan has been registered.
                 <br />
                 <br />
                 <br />
                 <br />
                 <table class="bibcirctable_contents">
                 <td align="center">
                 <input type=button onClick="location.href='%s'" value="Back to home" class='formbutton'>
                 </td>
                 </table>
                 <br />
                 </div>
                 """ % (CFG_SITE_URL)

        return out

    def tmpl_send_notification(self, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        out = """
              """
        out += _MENU_

        out += """
        <div class="bibcircbottom">
        <br /> <br />
             <table class="bibcirctable">
                  <td class="bibcirccontent" width="30">%s</td>
             </table>
             <br /> <br />
             <table class="bibcirctable">
             <td>
             <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1'"
             value='Back to home' class='formbutton'>
             </td>
             </table>
        <br /> <br />
        </div>
        """ % (_("Notification has been sent!"),
               CFG_SITE_URL)

        return out

    def tmpl_register_new_loan(self, borrower_info, recid, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        (_id, name, email, phone, address, mailbox) = borrower_info
        (book_title, book_year, book_author, book_isbn, book_editor) = book_information_from_MARC(int(recid))

        _ = gettext_set_language(ln)

        out = """  """

        out += _MENU_

        out += """
        <br />
        <div class="infoboxsuccess">%s</div>
        <style type="text/css"> @import url("/img/tablesorter.css"); </style>
        <div class="bibcircbottom">
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
        </table>
        <br />
        <table class="bibcirctable">
             <td><input type="button" onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/register_new_loan?print_data=true'"
             value="%s" class="formbutton"></td>
        </table>
        <br />
        <br />
        </div>
        """ % (_("A new loan has been registered."),
               _("Name"), name,
               _("Email"), email,
               _("Phone"), phone,
               _("Address"), address,
               _("Mailbox"), mailbox,
               _("Name"), book_title,
               _("Author(s)"), book_author,
               _("Year"), book_year,
               _("Publisher"), book_editor,
               _("ISBN"), book_isbn,
               CFG_SITE_URL,
               _("Print loan information"))

        return out

    def tmpl_loan_on_desk_confirm(self, barcode,
                                  borrower, infos, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page0
        """

        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += _MENU_

        borrower_email = borrower.split(' [')[0]
        borrower_id = borrower.split(' [')[1]
        borrower_id = int(borrower_id[:-1])

        out += """
        <form name="return_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/register_new_loan" method="get" >
             <div class="bibcircbottom">
             <input type=hidden name=borrower_id value=%s>
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
            <input type=hidden name=barcode value=%s>

            """ % (_("Item"),
                   book_title_from_MARC(recid),
                   bar)



        out += """
        </table>
        <br />
        <table class="bibcirctable_contents">
             <tr>
                  <td>
                       <input type=button value=%s onClick="history.go(-1)" class="formbutton">
                       <input type="submit"   value=%s class="formbutton">
                  </td>
             </tr>
        </table>
        <br />
        </div>
        </form>
        """ % (_("Back"),
               _("Confirm"))


        return out

    def tmpl_all_requests(self, result, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        out = """
        """
        out += _MENU_

        out += """
        <form name="all_requests_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/all_requests" method="get" >
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

        """% (CFG_SITE_URL,
               _("Borrower"),
               _("Item"),
               _("Status"),
               _("From"),
               _("To"),
               _("Request date"),
               _("Option(s)"))

        for (id_lr, borid, name, recid, status, date_from, date_to, request_date) in result:

            borrower_link = create_html_link(CFG_SITE_URL +
                                             '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_details',
                                             {'borrower_id': borid, 'ln': ln},
                                             (name))

            title_link = create_html_link(CFG_SITE_URL +
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_item_details',
                                          {'recid': recid, 'ln': ln},
                                          (book_title_from_MARC(recid)))

            out += """
            <tr onMouseOver="this.className='highlight'" onMouseOut="this.className='normal'">
                 <td class="bibcirccontent">%s</td>
                 <td class="bibcirccontent">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">
                   <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/all_requests?request_id=%s'"
                   value='%s' class="formbutton">
                 </td>
            </tr>
            """ % (borrower_link,
                   title_link,
                   status,
                   date_from,
                   date_to,
                   request_date,
                   CFG_SITE_URL,
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
        <br /> <br />
        </div>
        </form>
        """ % (_("Back"))



        return out

    def tmpl_get_item_requests_details(self, recid, result, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = """
        """
        out += _MENU_

        if len(result) == 0:
            out += """
            <div class="bibcircbottom">
            <br />
            <div class="infoboxmsg">%s</div>
            <br />
            """ % (_("There are no requests."))

        else:
            out += """
            <style type="text/css"> @import url("/img/tablesorter.css"); </style>
            <script src="/js/jquery.js" type="text/javascript"></script>
            <script src="/js/jquery.tablesorter.js" type="text/javascript"></script>
            <script type="text/javascript">
            $(document).ready(function() {
              $('#table_requests').tablesorter({widthFixed: true, widgets: ['zebra']})
            });
            </script>
        <form name="all_loans_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/update_loan_request_status" method="get" >
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
                  """% (CFG_SITE_URL,
                        _("Borrower"),
                        _("Status"),
                        _("Library"),
                        _("Location"),
                        _("From"),
                        _("To"),
                        _("Request date"),
                        _("Option(s)"))


            for (borrower_id, name, id_bibrec, status, library,
                 location, date_from, date_to, request_id,
                 request_date) in result:

                borrower_link = create_html_link(CFG_SITE_URL +
                                             '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_details',
                                             {'borrower_id': borrower_id, 'ln': ln},
                                             (name))

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
                   <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/get_item_requests_details?recid=%s&request_id=%s'"
                   value='%s' class='formbutton'>
                 </td>
            </tr>
            """ % (borrower_link, status, library, location,
                   date_from, date_to, request_date, CFG_SITE_URL,
                   id_bibrec, request_id, _("Cancel hold request"))

        out += """
        </tbody>
        </table>
        <br />
        <table class="bibcirctable">
             <tr>
                  <td><input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/get_item_details?recid=%s'"
                       value='%s' class='formbutton'></td>
             </tr>
        </table>
        <br /><br /><br />
       </div>
        </form>
        """ % (CFG_SITE_URL,
               recid,
               _("Back"))

        return out

    def tmpl_get_item_details(self, recid, copies, requests, loans, req_hist_overview,
                              loans_hist_overview, infos, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += _MENU_

        (book_title, book_year, book_author, book_isbn, book_editor) = book_information_from_MARC(int(recid))

        if book_isbn:
            try:
                book_cover = get_book_cover(book_isbn)
            except KeyError:
                book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)
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
                      <input type=button onClick="window.open('%s/%s/%s/edit')"
                      value='%s' class="formbutton">
                     </td>
                     <td>
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
           """  % (_("Item details"),
                   _("Name"), link_to_detailed_record,
                   _("Author(s)"), book_author,
                   _("Year"), book_year,
                   _("Publisher"), book_editor,
                   _("ISBN"), book_isbn,
                   CFG_SITE_URL, CFG_SITE_RECORD, recid,
                   _("Edit this record"),
                   str(book_cover),
                   _("Additional details"))

        out += """
            <style type="text/css"> @import url("/img/tablesorter.css"); </style>
            <script src="/js/jquery.js" type="text/javascript"></script>
            <script src="/js/jquery.tablesorter.js" type="text/javascript"></script>
            <script type="text/javascript">
            $(document).ready(function() {
              $('#table_copies').tablesorter({widthFixed: true, widgets: ['zebra']})
            });
            </script>

                  <table class="tablesorter" id="table_copies" border="0" cellpadding="0" cellspacing="1">
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
                  <tboby>
                    """ % (_("Barcode"),
                           _("Status"),
                           _("Due date"),
                           _("Library"),
                           _("Location"),
                           _("Loan period"),
                           _("No of loans"),
                           _("Collection"),
                           _("Description"),
                           _("Action(s)"))


        for (barcode, loan_period, library_name, library_id,
             location, nb_requests, status, collection,
             description, due_date) in copies:

            library_link = create_html_link(CFG_SITE_URL +
                                            '/admin/bibcirculation/bibcirculationadmin.py/get_library_details',
                                            {'library_id': library_id, 'ln': ln},
                                            (library_name))

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
                     """% (barcode, status, due_date or '-', library_link, location,
                           loan_period, nb_requests, collection or '-',
                           description or '-')

            if status == 'on loan':
                out += """
                  <td align="center">
                    <SELECT style='border: 1px solid #cfcfcf' ONCHANGE="location = this.options[this.selectedIndex].value;">
                      <OPTION VALUE="">Select an action
                      <OPTION VALUE="update_item_info_step4?barcode=%s">Update
                      <OPTION VALUE="place_new_request_step1?barcode=%s">New request
                      <OPTION VALUE="" DISABLED>New loan
                    </SELECT>
                  </td>
                 </tr>
                 """ % (barcode, barcode)

            elif status == 'missing':
                out += """
                     <td align="center">
                       <SELECT style='border: 1px solid #cfcfcf' ONCHANGE="location = this.options[this.selectedIndex].value;">
                         <OPTION VALUE="">Select an action
                         <OPTION VALUE="update_item_info_step4?barcode=%s">Update
                         <OPTION VALUE="" DISABLED>New request
                         <OPTION VALUE="" DISABLED>New loan
                       </SELECT>
                     </td>
                 </tr>
                 """ % (barcode)

            elif status == 'Not for loan':
                out += """
                     <td align="center">
                       <SELECT style='border: 1px solid #cfcfcf' ONCHANGE="location = this.options[this.selectedIndex].value;">
                         <OPTION VALUE="">Select an action
                         <OPTION VALUE="update_item_info_step4?barcode=%s">Update
                         <OPTION VALUE="place_new_request_step1?barcode=%s">New request
                         <OPTION VALUE="place_new_loan_step1?barcode=%s">New loan
                       </SELECT>
                     </td>
                 </tr>
                 """ % (barcode, barcode, barcode)

            else:
                out += """
                     <td align="center">
                       <SELECT style='border: 1px solid #cfcfcf' ONCHANGE="location = this.options[this.selectedIndex].value;">
                         <OPTION VALUE="">Select an action
                         <OPTION VALUE="update_item_info_step4?barcode=%s">Update
                         <OPTION VALUE="place_new_request_step1?barcode=%s">New request
                         <OPTION VALUE="place_new_loan_step1?barcode=%s">New loan
                       </SELECT>
                     </td>
                 </tr>
                 """ % (barcode, barcode, barcode)


        out += """
             </tbody>
            </table>
            <table class="bibcirctable">
                 <tr>
                     <td>
                     <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/add_new_copy_step3?recid=%s'"
                     value='%s' class="formbutton">

                     <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/order_new_copy_step1?recid=%s'"
                     value='%s' class="formbutton">

                     <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/register_ill_request_step0?recid=%s'"
                     value='%s'class="formbutton">
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
                      <input type="button" value='%s'
                      onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/get_item_requests_details?recid=%s'"
                      onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
                      class="bibcircbutton">
                      </td>
                 </tr>

                 <tr>
                      <th width="100">%s</th>
                      <td width="50">%s</td>
                      <td>
                      <input type="button" value='%s'
                      onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/get_item_loans_details?recid=%s'"
                      onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
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
                      onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/get_item_req_historical_overview?recid=%s'"
                      onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
                      class="bibcircbutton">
                      </td>
                 </tr>

                 <tr>
                      <th width="100">%s</th>
                      <td width="50">%s</td>
                      <td>
                      <input type="button" value='%s'
                      onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/get_item_loans_historical_overview?recid=%s'"
                      onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
                      class="bibcircbutton">
                      </td>
                 </tr>

            </table>
            <br />

            """ % (CFG_SITE_URL, recid, _("Add new copy"),
                   CFG_SITE_URL, recid, _("Order new copy"),
                    CFG_SITE_URL, recid, _("ILL request"),
                   _("Hold requests and loans overview on"), time.ctime(),
                   _("Hold requests"), len(requests), _("More details"), CFG_SITE_URL, recid,
                   _("Loans"), len(loans), _("More details"), CFG_SITE_URL, recid,
                   _("Historical overview"),
                   _("Hold requests"), len(req_hist_overview), _("More details"), CFG_SITE_URL, recid,
                   _("Loans"), len(loans_hist_overview), _("More details"), CFG_SITE_URL, recid)




        out += """
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

    def tmpl_bor_requests_historical_overview(self, req_hist_overview, ln=CFG_SITE_LANG):
        """
        Return the historical requests overview of a borrower.

        req_hist_overview: list of old requests.
        """

        _ = gettext_set_language(ln)

        out = """
        """
        out += _MENU_

        if len(req_hist_overview) == 0:
            out += """
            <div class="bibcircbottom">
            <br />
            <div class="infoboxmsg">%s</div>
            <br />
          """ % (_("There are no requests."))

        else:
            out += """<div class="bibcircbottom">
                    <br /> <br />
                    <style type="text/css"> @import url("/img/tablesorter.css"); </style>
                    <script src="/js/jquery.js" type="text/javascript"></script>
                    <script src="/js/jquery.tablesorter.js" type="text/javascript"></script>
                    <script type="text/javascript">
                      $(document).ready(function() {
                        $('#table_requests').tablesorter({widthFixed: true, widgets: ['zebra']})
                      });
                    </script>
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
                     </tr>
                    <thead>
                    <tbody>
                    """ % (_("Item"), _("Barcode"), _("Library"),
                           _("Location"), _("From"),
                           _("To"), _("Request date"))

            for (recid, barcode, library_name, location, req_from, req_to, req_date) in req_hist_overview:

                title_link = create_html_link(CFG_SITE_URL +
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_item_details',
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
                 """ % (title_link, barcode, library_name, location, req_from, req_to, req_date)

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

    def tmpl_bor_loans_historical_overview(self, loans_hist_overview, ln=CFG_SITE_LANG):
        """
        Return the historical loans overview of a borrower.

        loans_hist_overview: list of old loans.
        """

        _ = gettext_set_language(ln)

        out = """   """

        out += _MENU_

        if len(loans_hist_overview) == 0:
            out += """
            <div class="bibcircbottom">
            <br />
            <div class="infoboxmsg">%s</div>
            <br />
            """ % (_("There are no loans."))

        else:
            out += """<div class="bibcircbottom">
                      <style type="text/css"> @import url("/img/tablesorter.css"); </style>
                      <script src="/js/jquery.js" type="text/javascript"></script>
                      <script src="/js/jquery.tablesorter.js" type="text/javascript"></script>
                      <script type="text/javascript">
                        $(document).ready(function() {
                          $('#table_loans').tablesorter({widthFixed: true, widgets: ['zebra']})
                        });
                      </script>
                    <br /> <br />
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
                     </tr>
                   </thead>
                   <tbody>
                     """ % (_("Item"),
                            _("Barcode"),
                            _("Library"),
                            _("Location"),
                            _("Loaned on"),
                            _("Due date"),
                            _("Returned on"),
                            _("Renewals"),
                            _("Overdue letters"))
            (recid, barcode, library_name, location, loaned_on, due_date,
                 returned_on, nb_renew, nb_overdueletters) = None

            for (recid, barcode, library_name, location, loaned_on, due_date,
                 returned_on, nb_renew, nb_overdueletters) in loans_hist_overview:

                title_link = create_html_link(CFG_SITE_URL +
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_item_details',
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
                     <td><input type=button value='%s'
                          onClick="history.go(-1)" class="formbutton"></td>
                </tr>
           </table>
           <br />
           <br />
           <br />
           </div>

           """ % ("Back")

        return out


    def tmpl_get_item_req_historical_overview(self, req_hist_overview,
                                          ln=CFG_SITE_LANG):
        """
        Return the historical requests overview of a item.

        req_hist_overview: list of old borrowers.
        """

        _ = gettext_set_language(ln)

        out = """  """

        out += _MENU_

        if len(req_hist_overview) == 0:
            out += """
            <div class="bibcircbottom">
            <br />
            <div class="infoboxmsg">%s</div>
            <br />
            """ % (_("There are no requests."))

        else:
            out += """
             <div class="bibcircbottom">
             <style type="text/css"> @import url("/img/tablesorter.css"); </style>
            <script src="/js/jquery.js" type="text/javascript"></script>
            <script src="/js/jquery.tablesorter.js" type="text/javascript"></script>
            <script type="text/javascript">
            $(document).ready(function() {
              $('#table_holdings').tablesorter({widthFixed: true, widgets: ['zebra']})
            });
            </script>
              <br />
              <br />
              <table id="table_holdings" class="tablesorter" border="0" cellpadding="0" cellspacing="1">
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
                     """ % (_("Borrower"),
                            _("Barcode"),
                            _("Library"),
                            _("Location"),
                            _("From"),
                            _("To"),
                            _("Request date"))

            for (name, borrower_id, barcode, library_name,
                 location, req_from, req_to, req_date) in req_hist_overview:

                borrower_link = create_html_link(CFG_SITE_URL +
                                             '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_details',
                                             {'borrower_id': borrower_id, 'ln': ln},
                                             (name))

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


    def tmpl_get_item_loans_historical_overview(self, loans_hist_overview,
                                            ln=CFG_SITE_LANG):
        """
        Return the historical loans overview of a item.

        loans_hist_overview: list of old borrowers.
        """

        _ = gettext_set_language(ln)

        out = """
        """
        out += _MENU_

        out += """<div class="bibcircbottom">
                  <style type="text/css"> @import url("/img/tablesorter.css"); </style>
                  <script src="/js/jquery.js" type="text/javascript"></script>
                  <script src="/js/jquery.tablesorter.js" type="text/javascript"></script>
                  <script type="text/javascript">
                  $(document).ready(function() {
                    $('#table_loans').tablesorter({widthFixed: true, widgets: ['zebra']})
                  });
                  </script>
                    <br />
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
                     </tr>
                     </thead>
                     <tbody>
                     """ % (_("Borrower"),
                            _("Barcode"),
                            _("Library"),
                            _("Location"),
                            _("Loaned on"),
                            _("Due date"),
                            _("Returned on"),
                            _("Renewals"),
                            _("Overdue letters"))

        for (name, borrower_id, barcode, library_name, location, loaned_on, due_date, returned_on, nb_renew, nb_overdueletters) in loans_hist_overview:

            borrower_link = create_html_link(CFG_SITE_URL +
                                             '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_details',
                                             {'borrower_id': borrower_id, 'ln': ln},
                                             (name))

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

    def tmpl_library_details(self, library_details, library_items,
                             ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        out = """
        """
        out += _MENU_

        out += """
        <style type="text/css"> @import url("/img/tablesorter.css"); </style>
        <div class="bibcircbottom">
        <br />
        """
        (library_id, name, address, email, phone, notes) = library_details

        no_notes_link = create_html_link(CFG_SITE_URL +
                                         '/admin/bibcirculation/bibcirculationadmin.py/get_library_notes',
                                         {'library_id': library_id},
                                         (_("No notes")))

        see_notes_link = create_html_link(CFG_SITE_URL +
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_library_notes',
                                          {'library_id': library_id},
                                          (_("Notes about this library")))

        if notes == "":
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
             </table>
             <table>
                 <tr>
                   <td>
                     <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/update_library_info_step3?library_id=%s'" onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
                     value=%s  class="bibcircbutton">
                      </td>
                 </tr>
            </table>
            """ % (_("Library details"),
                   _("Name"), name,
                   _("Address"), address,
                   _("Email"), email,
                   _("Phone"), phone,
                   _("Notes"), notes_link,
                   _("No of items"), len(library_items),
                   CFG_SITE_URL, library_id, _("Update"))

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


    def tmpl_borrower_details(self, borrower, requests, loans, notes,
                              ill, req_hist, loans_hist, ill_hist,
                              ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_

        (borrower_id, name, email, phone, address, mailbox) = borrower

        #req_link = create_html_link(CFG_SITE_URL +
        #                            '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_requests_details',
        #                            {'borrower_id': borrower_id},
        #                            (_("More details")))

        no_notes_link = create_html_link(CFG_SITE_URL +
                                         '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_notes',
                                         {'borrower_id': borrower_id},
                                         (_("No notes")))

        see_notes_link = create_html_link(CFG_SITE_URL +
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_notes',
                                          {'borrower_id': borrower_id},
                                          (_("Notes about this borrower")))

        #loans_link = create_html_link(CFG_SITE_URL +
        #                              '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_loans_details',
        #                              {'borrower_id': borrower_id},
        #                              (_("More details")))
        #
        #ill_link = create_html_link(CFG_SITE_URL +
        #                            '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_ill_details',
        #                            {'borrower_id': borrower_id},
        #                            (_("More details")))
        #
        #req_hist_link = create_html_link(CFG_SITE_URL +
        #                                 '/admin/bibcirculation/bibcirculationadmin.py/bor_requests_historical_overview',
        #                                 {'borrower_id': borrower_id},
        #                                 (_("More details")))
        #
        #loans_hist_link = create_html_link(CFG_SITE_URL +
        #                                   '/admin/bibcirculation/bibcirculationadmin.py/bor_loans_historical_overview',
        #                                   {'borrower_id': borrower_id},
        #                                   (_("More details")))
        #
        #ill_hist_link = create_html_link(CFG_SITE_URL +
        #                                 '/admin/bibcirculation/bibcirculationadmin.py/bor_ill_historical_overview',
        #                                 {'borrower_id': borrower_id},
        #                                 (_("More details")))

        if notes == "" or str(notes) == '{}':
            check_notes = no_notes_link
        else:
            check_notes = see_notes_link


        out += """
            <style type="text/css"> @import url("/img/tablesorter.css"); </style>
            <form name="borrower_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/borrower_notification" method="get" >
            <div class="bibcircbottom">
            <input type=hidden name=borrower_id value=%s>
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

            """ % (CFG_SITE_URL,
                   borrower_id,
                   _("Personal details"),
                   _("Name"), name,
                   _("Email"), email,
                   _("Phone"), phone,
                   _("Address"), address,
                   _("Mailbox"), mailbox,
                   _("Notes"), check_notes)

        nb_requests = len(requests)
        nb_loans = len(loans)
        nb_ill = len(ill)
        nb_req_hist = len(req_hist)
        nb_loans_hist = len(loans_hist)
        nb_ill_hist = len(ill_hist)

        out += """
        </table>
        <!-- <table class="bibcirctable">
             <tr>
                  <td><input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/update_borrower_info_step3?borrower_id=%s'"
                       value=%s class='formbutton'></td>
             </tr>
        </table> -->
        <br />
        <table class="bibcirctable">
          <tr>
            <td>
            <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step2?user_info=%s,%s,%s,%s,%s,%s'"
            value='%s' class='formbutton'>
            <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/create_new_request_step1?borrower_id=%s'"
            value='%s' class='formbutton'>
            <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/register_ill_book_request_from_borrower_page?borrower_id=%s'"
            value='%s' class='formbutton'>
            <input type='submit' name='notify_button' value='%s' class='formbutton'>
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
              onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/get_borrower_requests_details?borrower_id=%s'"
              onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
              value='%s' class="bibcircbutton">
            </td>
          </tr>
          <tr>
            <th width="100">%s</th>
            <td width="50">%s</td>
            <td>
              <input type="button"
              onClick="location.href='%s//admin/bibcirculation/bibcirculationadmin.py/get_borrower_loans_details?borrower_id=%s'"
              onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
              value='%s' class="bibcircbutton">
            </td>
          </tr>
          <tr>
            <th width="100">%s</th>
            <td width="50">%s</td>
            <td>
              <input type="button"
              onClick="location.href='%s//admin/bibcirculation/bibcirculationadmin.py/get_borrower_ill_details?borrower_id=%s'"
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
              onClick="location.href='%s//admin/bibcirculation/bibcirculationadmin.py/bor_requests_historical_overview?borrower_id=%s'"
              onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
              value='%s' class="bibcircbutton">
            </td>
          </tr>
          <tr>
            <th width="100">%s</th>
            <td width="50">%s</td>
            <td>
              <input type="button"
              onClick="location.href='%s//admin/bibcirculation/bibcirculationadmin.py/bor_loans_historical_overview?borrower_id=%s'"
              onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
              value='%s' class="bibcircbutton">
            </td>
          </tr>
          <tr>
            <th width="100">%s</th>
            <td width="50">%s</td>
            <td>
              <input type="button"
              onClick="location.href='%s//admin/bibcirculation/bibcirculationadmin.py/bor_ill_historical_overview?borrower_id=%s'"
              onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
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
        """ % (CFG_SITE_URL, borrower_id, _("Update"),
               CFG_SITE_URL, borrower_id, name, email, phone, address, mailbox, _("New loan"),
               CFG_SITE_URL, borrower_id, _("New request"),
               CFG_SITE_URL, borrower_id, _("New ILL request"),
               _("Notify this borrower"),
               _("Requests, Loans and ILL overview on"), time.ctime(),
               _("Requests"), nb_requests, CFG_SITE_URL, borrower_id, _("More details"),
               _("Loans"), nb_loans, CFG_SITE_URL, borrower_id, _("More details"),
               _("ILL"), nb_ill, CFG_SITE_URL, borrower_id, _("More details"),
               _("Historical overview"),
               _("Requests"), nb_req_hist, CFG_SITE_URL, borrower_id, _("More details"),
               _("Loans"), nb_loans_hist, CFG_SITE_URL, borrower_id, _("More details"),
               _("ILL"), nb_ill_hist, CFG_SITE_URL, borrower_id, _("More details"),
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
        out += _MENU_

        if len(result) == 0:
            out += """
            <div class="bibcircbottom">
            <br />
            <div class="infoboxmsg">%s</div>
            <br />
          """ % (_("There are no requests."))

        else:
            out += """
         <style type="text/css"> @import url("/img/tablesorter.css"); </style>
         <script src="/js/jquery.js" type="text/javascript"></script>
         <script src="/js/jquery.tablesorter.js" type="text/javascript"></script>
         <script type="text/javascript">
           $(document).ready(function() {
             $('#table_requests').tablesorter({widthFixed: true, widgets: ['zebra']})
           });
         </script>
        <form name="borrower_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/get_borrower_requests_details" method="get" >
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
         """% (CFG_SITE_URL,
               _("Item"),
               _("Request status"),
               _("Library"),
               _("Location"),
               _("From"),
               _("To"),
               _("Request date"),
               _("Request option(s)"))

            for (recid, status, library, location, date_from, date_to, request_date, request_id) in result:
                title_link = create_html_link(CFG_SITE_URL +
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_item_details',
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
                 no-repeat; width: 75px; text-align: right;"
                 onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/get_pending_requests?request_id=%s'"
                 onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
                 class="bibcircbutton">
                 </td>
            </tr>

            """ % (title_link, status, library, location, date_from,
                   date_to, request_date, _("Cancel"),
                   CFG_SITE_URL, request_id)


        out += """
        </tbody>
        </table>
        <br />
        <table class="bibcirctable">
             <tr>
                  <td>
                    <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/get_borrower_details?borrower_id=%s'"
                    value='%s' class='formbutton'>
                  </td>
             </tr>
        </table>
        <br />
        </div>
        """ % (CFG_SITE_URL,
               borrower_id,
               _("Back"))

        return out

    def tmpl_borrower_loans_details(self, borrower_loans, borrower_id, infos, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += _MENU_

        if len(borrower_loans) == 0:
            out += """
            <div class="bibcircbottom">
            <br />
            <div class="infoboxmsg">%s</div>
            <br />
          """ % (_("There are no loans."))

        else:
            out += """
        <form name="borrower_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/get_borrower_loans_details?submit_changes=true" method="get" >
        <input type=hidden name=borrower_id value=%s>
        <div class="bibcircbottom">

        <style type="text/css"> @import url("/img/tablesorter.css"); </style>
        <script src="/js/jquery.js" type="text/javascript"></script>
        <script src="/js/jquery.tablesorter.js" type="text/javascript"></script>
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

         """% (CFG_SITE_URL,
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


            for (recid, barcode, loaned_on, due_date, nb_renewall, nb_overdue, date_overdue, loan_type, notes, loan_id, status) in borrower_loans:

                title_link = create_html_link(CFG_SITE_URL +
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_item_details',
                                          {'recid': recid, 'ln': ln},
                                          (book_title_from_MARC(recid)))

                no_notes_link = create_html_link(CFG_SITE_URL +
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_loans_notes',
                                          {'loan_id': loan_id, 'recid': recid, 'ln': ln},
                                          (_("No notes")))

                see_notes_link = create_html_link(CFG_SITE_URL +
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_loans_notes',
                                          {'loan_id': loan_id, 'recid': recid, 'ln': ln},
                                          (_("See notes")))

                if notes == "":
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
              <td align="center">
                <SELECT style='border: 1px solid #cfcfcf' ONCHANGE="location = this.options[this.selectedIndex].value;">
                  <OPTION VALUE="">Select an action
                  <OPTION VALUE="get_borrower_loans_details?borrower_id=%s&barcode=%s&loan_id=%s&recid=%s">Renew
                  <OPTION VALUE="loan_return_confirm?barcode=%s">Return
                  <OPTION VALUE="change_due_date_step1?loan_id=%s&borrower_id=%s">Change due date
                  <OPTION VALUE="claim_book_return?borrower_id=%s&recid=%s&loan_id=%s&template=claim_return">Send recall
                </SELECT>
              </td>
                <input type=hidden name=barcode value=%s>
                <input type=hidden name=loan_id value=%s>
            </tr>

            """ % (title_link, barcode, loaned_on,
                   due_date, nb_renewall,
                   nb_overdue, date_overdue, loan_type,
                   check_notes, status,
                   borrower_id, barcode,
                   loan_id, recid,
                   barcode, loan_id, borrower_id,
                   borrower_id, recid, loan_id,
                   barcode, loan_id)

            out += """
        </tbody>
        </table>
        <br />
        <table class="bibcirctable">
          <tr>
            <td class="bibcirccontent" align="right" width="100">
              <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/get_borrower_loans_details?borrower_id=%s&renewall=true'"
              value='%s' class='bibcircbutton'onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"></td>
          </tr>
        </table>
        """ % (CFG_SITE_URL,
               borrower_id,
               _("Renew all loans"))

        out += """
        <table class="bibcirctable">
          <tr>
            <td>
              <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/get_borrower_details?borrower_id=%s'"
              value='%s' class='formbutton'></td>
          </tr>
        </table>
        <br />
        </div>
        </form>

        """ % (CFG_SITE_URL,
               borrower_id,
               _("Back"))


        return out

    def tmpl_all_loans(self, result, infos, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += _MENU_

        out += """
            <style type="text/css"> @import url("/js/tablesorter/themes/blue/style.css"); </style>
            <style type="text/css"> @import url("/js/tablesorter/addons/pager/jquery.tablesorter.pager.css"); </style>

            <script src="/js/tablesorter/jquery.tablesorter.js" type="text/javascript"></script>
            <script src="/js/tablesorter/addons/pager/jquery.tablesorter.pager.js" type="text/javascript"></script>
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
            """

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
            <form name="borrower_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/all_loans" method="get" >
            <br />
            <table id="table_all_loans" class="tablesorter" border="0" cellpadding="0" cellspacing="1">
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
                 loaned_on, due_date, nb_renewall, nb_overdue,
                 date_overdue, notes, loan_id) in result:

                borrower_link = create_html_link(CFG_SITE_URL +
                                                 '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_details',
                                                 {'borrower_id': borrower_id, 'ln': ln},
                                                 (borrower_name))

                see_notes_link = create_html_link(CFG_SITE_URL +
                                                  '/admin/bibcirculation/bibcirculationadmin.py/get_loans_notes',
                                                  {'loan_id': loan_id, 'recid': recid, 'ln': ln},
                                                  (_("see notes")))

                no_notes_link = create_html_link(CFG_SITE_URL +
                                                 '/admin/bibcirculation/bibcirculationadmin.py/get_loans_notes',
                                                 {'loan_id': loan_id, 'recid': recid, 'ln': ln},
                                                 (_("no notes")))


                if notes == "":
                    check_notes = no_notes_link
                elif str(notes) == '{}':
                    check_notes = no_notes_link
                else:
                    check_notes = see_notes_link

                title_link = create_html_link(CFG_SITE_URL +
                                              '/admin/bibcirculation/bibcirculationadmin.py/get_item_details',
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
                        <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/claim_book_return?borrower_id=%s&recid=%s&loan_id=%s&template=claim_return'" onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
                             value='%s' class='bibcircbutton'></td>
                    </tr>

                    """ % (borrower_link, title_link, barcode,
                           loaned_on, due_date,
                           nb_renewall, nb_overdue, date_overdue,
                           check_notes, CFG_SITE_URL,
                           borrower_id, recid, loan_id, _("Send recall"))





            out+= """
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
                                <td><input type=button value='%s' onClick="history.go(-1)" class="formbutton"></td>
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

        out += _MENU_

        out += """
            <style type="text/css"> @import url("/js/tablesorter/themes/blue/style.css"); </style>
            <style type="text/css"> @import url("/js/tablesorter/addons/pager/jquery.tablesorter.pager.css"); </style>

            <script src="/js/tablesorter/jquery.tablesorter.js" type="text/javascript"></script>
            <script src="/js/tablesorter/addons/pager/jquery.tablesorter.pager.js" type="text/javascript"></script>
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
            """

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
            <form name="borrower_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/all_loans" method="get" >
            <br />
            <table id="table_all_loans" class="tablesorter" border="0" cellpadding="0" cellspacing="1">
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
                 loaned_on, due_date, nb_renewall, nb_overdue,
                 date_overdue, notes, loan_id) in result:

                borrower_link = create_html_link(CFG_SITE_URL +
                                                 '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_details',
                                                 {'borrower_id': borrower_id, 'ln': ln},
                                                 (borrower_name))

                see_notes_link = create_html_link(CFG_SITE_URL +
                                                  '/admin/bibcirculation/bibcirculationadmin.py/get_loans_notes',
                                                  {'loan_id': loan_id, 'recid': recid, 'ln': ln},
                                                  (_("see notes")))

                no_notes_link = create_html_link(CFG_SITE_URL +
                                                 '/admin/bibcirculation/bibcirculationadmin.py/get_loans_notes',
                                                 {'loan_id': loan_id, 'recid': recid, 'ln': ln},
                                                 (_("no notes")))


                if notes == "":
                    check_notes = no_notes_link
                elif str(notes) == '{}':
                    check_notes = no_notes_link
                else:
                    check_notes = see_notes_link

                title_link = create_html_link(CFG_SITE_URL +
                                              '/admin/bibcirculation/bibcirculationadmin.py/get_item_details',
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
                        <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/claim_book_return?borrower_id=%s&recid=%s&loan_id=%s&template=claim_return'" onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
                             value='%s' class='bibcircbutton'></td>
                    </tr>

                    """ % (borrower_link, title_link, barcode,
                           loaned_on, due_date,
                           nb_renewall, nb_overdue, date_overdue,
                           check_notes, CFG_SITE_URL,
                           borrower_id, recid, loan_id, _("Send recall"))


            out+= """
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
                                <td><input type=button value='%s' onClick="history.go(-1)" class="formbutton"></td>
                            </tr>
                        </table>
                    <br />
                    <br />
                    </form>
                    </div>
                    </div>
                    """ % (_("Back"))

        return out

    def tmpl_borrower_notification(self, email, subject, template, borrower_id,
                                   ln=CFG_SITE_LANG):
        """
        @param result: template used for the notification
        @param ln: language of the page
        """

        if subject is None:
            subject = ""

        _ = gettext_set_language(ln)

        out  = """ """

        out += _MENU_

        out += """
        <style type="text/css"> @import url("/img/tablesorter.css"); </style>
        <form name="borrower_notification" action="%s/admin/bibcirculation/bibcirculationadmin.py/borrower_notification" method="get" >
             <div class="bibcircbottom">
             <input type=hidden name=borrower_id value=%s>
             <br />
               <table class="tablesortermedium" border="0" cellpadding="0" cellspacing="1">
                 <tr>
                   <th width="50">%s</th>
                   <td>%s</td>
                </tr>
                <tr>
                  <th width="50">%s</th>
        """% (CFG_SITE_URL,
              borrower_id,
              _("From"),
              _("CERN Library"),
              _("To"))


        out += """
        <td>
        <input type="text" name="borrower_email" size="60" style='border: 1px solid #cfcfcf' value="%s">
        </td>
        </tr>
        """ % (email)



        out += """
             <tr>
               <th width="50">%s</th>
               <td><input type="text" name="subject" size="60" value="%s" style='border: 1px solid #cfcfcf'></td>
             </tr>
        </table>

        <br />

        <table class="tablesortermedium" border="0" cellpadding="0" cellspacing="1">
          <tr>
            <th width="500">%s</th>
            <th>%s</th>
          </tr>
          <tr>
            <td><textarea rows="10" cols="100" name="message" style='border: 1px solid #cfcfcf'>%s</textarea></td>
        """ % (_("Subject"),
               subject,
               _("Message"),
               _("Choose a template"),
               template)

        out += """
               <td>
                    <select name="template" style='border: 1px solid #cfcfcf'>
                         <option value ="">%s</option>
                         <option value ="overdue_letter">%s</option>
                         <option value ="reminder">%s</option>
                         <option value ="notification">%s</option>
                         <option value ="claim_return">%s</option>
                    </select>
                    <br /><br />
                    <input type="submit" name="load_template" value=%s class="formbutton">
               </td>
               </tr>
        </table>
        """ % (_("Templates"),
               _("Overdue letter"),
               _("Reminder"),
               _("Notification"),
               _("Send recall"),
               _("Load"))


        out += """

        <br /> <br />
        <table class="bibcirctable">
               <tr>
                    <td>
                       <input type=button value=%s onClick="history.go(-1)" class="formbutton">
                       <input type="reset" name="reset_button" value=%s class="formbutton">
                       <input type="submit" name="send_message" value=%s class="formbutton">
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

    def tmpl_all_loans_test(self, result, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_

        out += """
            <br />
            <style type="text/css"> @import url("/img/tablesorter.css"); </style>
            <script src="/js/jquery.js" type="text/javascript"></script>
            <script src="/js/jquery.tablesorter.js" type="text/javascript"></script>
            <script src="/js/jquery.tablesorter.pager.js" type="text/javascript"></script>
            <script type="text/javascript">
            $(document).ready(function() {
              $('#tablesorter-loans')
                .tablesorter({widthFixed: true, widgets: ['zebra']})
                .tablesorterPager({container: $('#pager')});
            });
            </script>

              <table id="tablesorter-loans" class="tablesorter" border="0" cellpadding="0" cellspacing="1">
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
                """% (_("Borrower"),
                      _("Item"),
                      _("Barcode"),
                      _("Loaned on"),
                      _("Due date"),
                      _("Renewals"),
                      _("Overdue letters"),
                      _("Loan Notes"))

        for (borrower_id, borrower_name, recid, barcode,
             loaned_on, due_date, nb_renewall, nb_overdue,
             date_overdue, notes, loan_id) in result:

            borrower_link = create_html_link(CFG_SITE_URL +
                                             '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_details',
                                             {'borrower_id': borrower_id, 'ln': ln},
                                             (borrower_name))

            see_notes_link = create_html_link(CFG_SITE_URL +
                                              '/admin/bibcirculation/bibcirculationadmin.py/get_loans_notes',
                                              {'loan_id': loan_id, 'recid': recid, 'ln': ln},
                                              (_("see notes")))

            no_notes_link = create_html_link(CFG_SITE_URL +
                                             '/admin/bibcirculation/bibcirculationadmin.py/get_loans_notes',
                                            {'loan_id': loan_id, 'recid': recid, 'ln': ln},
                                             (_("no notes")))

            if notes == "":
                check_notes = no_notes_link
            else:
                check_notes = see_notes_link

            title_link = create_html_link(CFG_SITE_URL +
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_item_details',
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
                  </tr>
                  """ % (borrower_link, title_link,
                         barcode, loaned_on, due_date,
                         nb_renewall, nb_overdue,
                         date_overdue, check_notes)


        out += """ </tbody>
                 </table>
                 <div id="pager" class="pager">
                   <form>
                   <img src="/js/first.png" class="first"/>
                   <img src="/js/prev.png" class="prev"/>
                   <input type="text" class="pagedisplay"/>
                   <img src="/js/next.png" class="next"/>
                   <img src="/js/last.png" class="last"/>
                   <select class="pagesize">
                     <option selected="selected" value="25">25</option>
                     <option value="40">40</option>
                     <option value="60">60</option>
                 </select>
                 </form>
               </div>
                 """

        return out

    def tmpl_get_item_loans_details(self, result, recid, infos,
                                    ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += _MENU_

        if len(result) == 0:
            out += """
            <div class="bibcircbottom">
            <br />
            <div class="infoboxmsg">%s</div>
            <br />
            """ % (_("There are no loans."))

        else:
            out += """
            <div class="bibcircbottom">
            <style type="text/css"> @import url("/img/tablesorter.css"); </style>
            <script src="/js/jquery.js" type="text/javascript"></script>
            <script src="/js/jquery.tablesorter.js" type="text/javascript"></script>
            <script type="text/javascript">
            $(document).ready(function() {
              $('#table_loans').tablesorter({widthFixed: true, widgets: ['zebra']})
            });
            </script>
            <br />
            <form name="borrower_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/get_item_loans_details" method="get" >
            <input type=hidden name=recid value=%s>
            """ % (CFG_SITE_URL,
                   recid)

            out += """
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
                    </tr>
                </thead>
                <tbody>
                """% (_("Borrower"),
                      _("Barcode"),
                      _("Loaned on"),
                      _("Due date"),
                      _("Renewals"),
                      _("Overdue letter"),
                      _("Loan status"),
                      _("Loan notes"),
                      _("Loan options"))


            for (borrower_id, borrower_name, barcode, loaned_on,
                 due_date, nb_renewall, nb_overdue, date_overdue,
                 status, notes, loan_id) in result:

                borrower_link = create_html_link(CFG_SITE_URL +
                                             '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_details',
                                             {'borrower_id': borrower_id, 'ln': ln},
                                             (borrower_name))

                no_notes_link = create_html_link(CFG_SITE_URL +
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_loans_notes',
                                          {'loan_id': loan_id, 'recid': recid, 'ln': ln},
                                          (_("No notes")))

                see_notes_link = create_html_link(CFG_SITE_URL +
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_loans_notes',
                                          {'loan_id': loan_id, 'recid': recid, 'ln': ln},
                                          (_("See notes")))

                if notes == "":
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
                 <td align="center">
                   <SELECT style='border: 1px solid #cfcfcf' ONCHANGE="location = this.options[this.selectedIndex].value;">
                      <OPTION VALUE="">Select an action
                      <OPTION VALUE="get_item_loans_details?barcode=%s&loan_id=%s&recid=%s">Renew
                      <OPTION VALUE="loan_return_confirm?barcode=%s">Return
                      <OPTION VALUE="change_due_date_step1?loan_id=%s">Change due date
                      <OPTION VALUE="claim_book_return?recid=%s&template=claim_return">Send recall
                    </SELECT>
                 </td>
             </tr>
             <input type=hidden name=loan_id value=%s>
             <input type=hidden name=loan_id value=%s>

            """ % (borrower_link, barcode,
                   loaned_on, due_date,
                   nb_renewall, nb_overdue,
                   date_overdue, status, check_notes,
                   borrower_id, barcode, loan_id, recid,
                   barcode, loan_id, recid,
                   loan_id)

        out += """
        <tbody>
        </table>
        <br />
        <table class="bibcirctable">
             <tr>
                  <td>
                       <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/get_item_details?recid=%s'"
                       value='%s' class='formbutton'>
                  </td>
             </tr>
        </table>
        <br />
        <br />
        <br />
        </div>
        </form>
        """ % (CFG_SITE_URL,
               recid,
               _("Back"))

        return out


    def tmpl_associate_barcode(self, request_id, recid, borrower,
                               infos, ln=CFG_SITE_LANG):


        _ = gettext_set_language(ln)


        (book_title, _book_year, _book_author, book_isbn, _book_editor) =  book_information_from_MARC(int(recid))

        if book_isbn:
            book_cover  = get_book_cover(book_isbn)
        else:
            book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)


        out = self.tmpl_infobox(infos, ln)

        out += _MENU_

        (borrower_id, name, email, phone, address, mailbox) = borrower

        out += """
            <style type="text/css"> @import url("/img/tablesorter.css"); </style>
            <form name="return_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/register_new_loan" method="get" >
            <div class="bibcircbottom">
            <input type=hidden name=borrower_id value=%s>
            <input type=hidden name=request_id value=%s>
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
            </table>
            """% (CFG_SITE_URL,
                  borrower_id,
                  request_id,
                  _("Personal details"),
                  _("Name"), name,
                  _("Email"), email,
                  _("Phone"), phone,
                  _("Address"), address,
                  _("Mailbox"), mailbox)


        out +="""
        <br />
        <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">
          <tr>
            <th>%s</th>
          </tr>
          <tr>
            <td>%s</td>
          </tr>
          <tr algin='center'>
            <td><img style='border: 1px solid #cfcfcf' src="%s" alt="Book Cover"/></td>
          </tr>
          <tr>
            <th>%s</th>
          </tr>
          <tr>
            <td><input type="text" size="66" name="barcode" style='border: 1px solid #cfcfcf'></td>
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
                  <td><textarea name='new_note' rows="4" cols="57" style='border: 1px solid #cfcfcf'></textarea></td>
                </tr>
              </table>
              <br />
              """ % (_("Write notes"))

        out += """
        <table class="bibcirctable">
          <tr>
            <td>
              <input type=button value=%s onClick="history.go(-1)" class="bibcircbutton"
              onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'">
              <input type="submit"   value=%s class="bibcircbutton"
              onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'">
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

        out += _MENU_

        out +="""
            <div class="bibcircbottom">
            <form name="borrower_notes" action="%s/admin/bibcirculation/bibcirculationadmin.py/get_borrower_notes" method="get" >
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
                                           '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_notes',
                                           {'delete_key': key, 'borrower_id': borrower_id, 'ln': ln},
                                           (_("[delete]")))

            out += """<tr class="bibcirccontent">
                        <td class="bibcircnotes" width="160" valign="top" align="center"><b>%s</b></td>
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
                  <textarea name="library_notes" rows="5" cols="90" style='border: 1px solid #cfcfcf'></textarea>
                </td>
              </tr>
            </table>
            <br />
            <table class="bibcirctable">
              <tr>
                <td>
                  <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/get_borrower_details?borrower_id=%s'"
                  value=%s class='formbutton'>
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
               CFG_SITE_URL,
               borrower_id,
               _("Back"),
               _("Confirm"))

        return out


    def tmpl_get_loans_notes(self, loans_notes, loan_id,
                             referer, back="", ln=CFG_SITE_LANG):

        _ = gettext_set_language(ln)

        if back == "":
            back=referer

        if not loans_notes:
            loans_notes = {}
        else:
            if looks_like_dictionary(loans_notes):
                loans_notes = eval(loans_notes)
            else:
                loans_notes = {}

        out = """ """

        out += _MENU_

        out +="""
            <div class="bibcircbottom">
            <form name="loans_notes" action="%s/admin/bibcirculation/bibcirculationadmin.py/get_loans_notes" method="get" >
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
                                           '/admin/bibcirculation/bibcirculationadmin.py/get_loans_notes',
                                           {'delete_key': key, 'loan_id': loan_id, 'ln': ln, 'back': cgi.escape(back, True)},
                                           (_("[delete]")))

            out += """<tr class="bibcirccontent">
                        <td class="bibcircnotes" width="160" valign="top" align="center"><b>%s</b></td>
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
                  <textarea name="library_notes" rows="5" cols="90" style='border: 1px solid #cfcfcf'></textarea>
                </td>
              </tr>
            </table>
            <br />
            <table class="bibcirctable">
              <tr>
                  <td>
                    <input type=button value="%s" onClick="window.location='%s'" class="formbutton">
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
               cgi.escape(back,True),
               _("Confirm"),
               cgi.escape(back, True))

        return out



    def tmpl_new_item(self, book_info=None, errors=None, ln=CFG_SITE_LANG):
        """
        No more in use.
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_

        if book_info:
            out += """
              <div class="bibcircbottom">
                <br />
                <table class="bibcirctable">
                <tr>
                <td class="bibcirctableheader" width="10">%s</td>
                </tr>
                </table>
                <table class="bibcirctable">
                     <tr>
                     <td width="110" valign="top">%s</td>
                     <td class="bibcirccontent">
                       <textarea style='border: 1px solid #cfcfcf' rows="3" cols="43" name="title">%s</textarea>
                     </td>
                     </tr>
                     <tr>
                     <td width="110"></td>
                     <td class="bibcirccontent"></td>
                     </tr>
                     <tr>
                     <td width="110"></td>
                     <td class="bibcirccontent">
                      <img style='border: 1px solid #cfcfcf' src="%s" alt="Book Cover"/>
                     </td>
                     </tr>
                     <tr>
                     <td width="110"></td>
                     <td class="bibcirccontent"></td>
                     </tr>
                     <tr>
                     <td width="110">%s</td>
                     <td class="bibcirccontent">
                       <input type="text" style='border: 1px solid #cfcfcf' size=45 value="%s" name="author">
                     </td>
                     </tr>
                     <tr>
                     <td width="110">%s</td>
                     <td class="bibcirccontent">
                       <input type="text" style='border: 1px solid #cfcfcf' size=45 value="%s" name="ean">
                     </td>
                     </tr>
                     <tr>
                     <td width="110">%s</td>
                     <td class="bibcirccontent">
                       <input type="text" style='border: 1px solid #cfcfcf' size=45 value="%s" name="isbn">
                     </td>
                     </tr>
                     <tr>
                     <td width="110">%s</td>
                     <td class="bibcirccontent">
                       <input type="text" size=45 style='border: 1px solid #cfcfcf' value="%s" name="publisher">
                     </td>
                     </tr>
                     <tr>
                     <td width="110">%s</td>
                     <td class="bibcirccontent">
                       <input type="text" size=45 style='border: 1px solid #cfcfcf' value="%s" name="pub_date">
                     </td>
                     </tr>
                     <tr>
                     <td width="110">%s</td>
                     <td class="bibcirccontent">
                       <input type="text" style='border: 1px solid #cfcfcf' size=45 value="" name="pub_place">
                     </td>
                     </tr>
                     <tr>
                     <td width="110">%s</td>
                     <td class="bibcirccontent">
                       <input type="text" style='border: 1px solid #cfcfcf' size=45 value="%s" name="edition">
                     </td>
                     </tr>
                     <tr>
                     <td width="110">%s</td>
                     <td class="bibcirccontent">
                       <input type="text" style='border: 1px solid #cfcfcf' size=45 value="%s" name="nb_pages">
                     </td>
                     </tr>
                     <tr>
                     <td width="110">%s</td>
                     <td class="bibcirccontent">
                       <input type="text" style='border: 1px solid #cfcfcf' size=45 value="%s" name="sub_library">
                     </td>
                     </tr>
                     <tr>
                     <td width="110">%s</td>
                     <td class="bibcirccontent">
                       <input type="text" style='border: 1px solid #cfcfcf' size=45 value="" name="location">
                     </td>
                     </tr>
                     <tr>
                     <td width="110">%s</td>
                     <td class="bibcirccontent">
                     <select name="loan_period" style='border: 1px solid #cfcfcf'>
                             <option value ="Not for loan">Not for loan</option>
                             <option value ="4 weeks loan">4 weeks loan</option>
                     </select></td>
                     </tr>
                     <tr>
                     <td width="110">%s</td>
                     <td class="bibcirccontent">
                       <input type="text" style='border: 1px solid #cfcfcf' size=45 value="" name="barcode">
                     </td>
                     </tr>
                     <tr>
                     <td width="110">%s</td>
                     <td class="bibcirccontent">
                       <input type="text" style='border: 1px solid #cfcfcf' size=45 value="" name="collection">
                     </td>
                     </tr>
                     <tr>
                     <td width="110">%s</td>
                     <td class="bibcirccontent">
                       <input type="text" style='border: 1px solid #cfcfcf' size=45 value="" name="description">
                     </td>
                     </tr>
           </table>
           <br />
           <br />
           """ % (_("Book Information"),
                  _("Title"), book_info[6],
                  book_info[8],
                  _("Author"), book_info[0],
                  _("EAN"), book_info[1],
                  _("ISBN"), book_info[2],
                  _("Publisher"), book_info[3],
                  _("Publication date"), book_info[5],
                  _("Publication place"),
                  _("Edition"), book_info[7],
                  _("Number of pages"), book_info[4],
                  _("Sub-library"),
                  _("CERN Central Library"),
                  _("Location"),
                  _("Loan period"),
                  _("Barcode"),
                  _("Collection"),
                  _("Description"))

        elif errors:
            out += """
            <div class="bibcircbottom">
            <form name="list_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/new_item" method="get" >
            <br />
            <br />
            <br />
            <table class="bibcirctable_contents">
            <tr align="center">
            <td>ERROR: %s. %s</td>
            </tr>
            </table>
            <br />
            <br />
            <br />
            <br />
            </form>
            </div>
            """ % (CFG_SITE_URL, errors[0], errors[1])

        else:
            out += """
            <div class="bibcircbottom">
            <form name="list_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/new_item" method="get" >
            <br />
            <br />
            <br />
            <table class="bibcirctable_contents">
            <tr align="center">
            <td class="bibcirctableheader">'%s'
              <input type="text" style='border: 1px solid #cfcfcf' size=25  name="isbn">
            </td>
            </tr>
            </table>
            <br />
            <table class="bibcirctable_contents">
            <tr align="center">
            <td><input type="submit" value="Retrieve book information" class="formbutton"></td>
            </tr>
            </table>
            <br />
            <br />
            <br />
            </form>
            </div>
            """ % (CFG_SITE_URL, _("ISBN"))

        return out


    def tmpl_add_new_borrower_step1(self, ln=CFG_SITE_LANG):

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_

        out += """
            <div class="bibcircbottom">
            <form name="add_new_borrower_step1_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/add_new_borrower_step2" method="get" >
              <br />
              <br />
              <table class="bibcirctable">
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=45 name="name">
                    </td>
                </tr>
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=45 name="email">
                    </td>
                </tr>
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=45 name="phone">
                    </td>
                </tr>
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=45 name="address">
                    </td>
                 </tr>
                  <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=45 name="mailbox">
                    </td>
                 </tr>
                 <tr>
                    <td width="70" valign="top">%s</td>
                    <td class="bibcirccontent">
                      <textarea name="notes" rows="5" cols="39" style='border: 1px solid #cfcfcf'></textarea>
                    </td>
                 </tr>
                </table>
                <br />
                <table class="bibcirctable">
                <tr>
                  <td>
                       <input type=button value=%s onClick="history.go(-1)" class="formbutton">
                       <input type="submit"   value=%s class="formbutton">
                  </td>
                 </tr>
                </table>
                <br />
                <br />
                </form>
                </div>
                """ % (CFG_SITE_URL, _("Name"), _("Email"),
                       _("Phone"), _("Address"), _("Mailbox"), _("Notes"),
                       _("Back"), _("Continue"))

        return out


    def tmpl_add_new_borrower_step2(self, tup_infos, infos, ln=CFG_SITE_LANG):

        _ = gettext_set_language(ln)

        (name, email, phone, address, mailbox, notes) = tup_infos

        out = self.tmpl_infobox(infos, ln)

        out += _MENU_

        out += """
            <div class="bibcircbottom">
            <form name="add_new_borrower_step2_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/add_new_borrower_step3" method="get" >
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
                         <input type=button value=%s onClick="history.go(-1)" class="formbutton">
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
                         <input type=button value=%s onClick="history.go(-1)" class="formbutton">
                         <input type="submit"   value=%s class="formbutton">
                         <input type=hidden name=tup_infos value="%s">
                       </td>
                     </tr>
                   </table>
                   <br />
                   <br />
                   </form>
                   </div>
                   """ % (_("Back"), _("Continue"),
                          tup_infos)

        return out

    def tmpl_add_new_borrower_step3(self, ln=CFG_SITE_LANG):

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_

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
                       <input type=button value=%s onClick= onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1'"
                       class="formbutton">
                  </td>
                 </tr>
                </table>
                <br />
                <br />
                </div>
                """ % (_("A new borrower has been registered."),
                       _("Back to home"),
                       CFG_SITE_URL)

        return out

    def tmpl_update_borrower_info_step1(self, ln=CFG_SITE_LANG):
        """
        Template for the admin interface. Search borrower.

        @param ln: language
        """
        _ = gettext_set_language(ln)

        out = """  """

        out += _MENU_

        out += """
        <div class="bibcircbottom">
        <br /><br />         <br />
        <form name="update_borrower_info_step1_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/update_borrower_info_step2" method="get" >
             <table class="bibcirctable">
                  <tr align="center">
                        <td class="bibcirctableheader">%s
                        <input type="radio" name="column" value="id">ccid
                        <input type="radio" name="column" value="name" checked>name
                        <input type="radio" name="column" value="email">email
                         <br><br>
                        </td>
                  </tr>
                  <tr align="center">
                        <td><input type="text" size="45" name="string" style='border: 1px solid #cfcfcf'></td>
                  </tr>
             </table>
        <br />
        <table class="bibcirctable">
             <tr align="center">
                  <td>
                        <input type=button value="Back" onClick="history.go(-1)" class="formbutton">
                  <input type="submit" value="Search" class="formbutton">
                  </td>
             </tr>
        </table>
        <form>
        <br /><br />
        <br />
        <br />
        </div>

        """ % (CFG_SITE_URL,
               _("Search borrower by"))


        return out

    def tmpl_update_borrower_info_step2(self, result, ln=CFG_SITE_LANG):
        """
        @param result: search result
        @param ln: language
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_

        out += """
        <div class="bibcircbottom">
        <br />
        <table class="bibcirctable">
          <tr align="center">
            <td class="bibcirccontent">
              %s borrowers found
            </td>
          </tr>
        </table>
        <br />
        <table class="bibcirctable">
        """ % (len(result))

        for (borrower_id, name) in result:
            borrower_link = create_html_link(CFG_SITE_URL +
                                             '/admin/bibcirculation/bibcirculationadmin.py/update_borrower_info_step3',
                                             {'borrower_id': borrower_id, 'ln': ln},
                                             (name))

            out += """
            <tr align="center">
                 <td class="bibcirccontent" width="70">%s
                 <input type=hidden name=uid value=%s></td>
            </tr>
            """ % (borrower_link, borrower_id)


        out += """
             </table>
             <br />
             """

        out += """
        <table class="bibcirctable">
             <tr align="center">
                  <td>
                    <input type=button value=%s
                     onClick="history.go(-1)" class="formbutton">
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


    def tmpl_update_borrower_info_step3(self, result, ln=CFG_SITE_LANG):

        _ = gettext_set_language(ln)

        (_borrower_id, name, email, phone, address, mailbox) = result

        out = """ """

        out += _MENU_

        out += """
            <div class="bibcircbottom">
            <form name="update_borrower_info_step3_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/update_borrower_info_step4" method="get" >
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
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=45 name="name" value="%s">
                    </td>
                </tr>
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=45 name="email" value="%s">
                    </td>
                </tr>
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=45 name="phone" value="%s">
                    </td>
                </tr>
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=45 name="address" value="%s">
                    </td>
                 </tr>
                 <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=45 name="mailbox" value="%s">
                    </td>
                 </tr>
                </table>
                <br />
                <table class="bibcirctable">
                <tr>
                  <td>
                       <input type=button value=%s onClick="history.go(-1)" class="formbutton">
                       <input type="submit"   value=%s class="formbutton">
                  </td>
                 </tr>
                </table>
                <br />
                <br />
                </form>
                </div>
                """ % (CFG_SITE_URL, _("Borrower information"),
                       _("Name"), name,
                       _("Email"), email,
                       _("Phone"), phone,
                       _("Address"), address,
                       _("Mailbox"), mailbox,
                       _("Back"), _("Continue"))


        return out

    def tmpl_update_borrower_info_step4(self, tup_infos, ln=CFG_SITE_LANG):

        _ = gettext_set_language(ln)

        (name, email, phone, address, mailbox) = tup_infos

        out = """ """

        out += _MENU_

        out += """
            <div class="bibcircbottom">
            <form name="update_borrower_info_step4_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/update_borrower_info_step5" method="get" >
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
                </table>
                <br />
                <table class="bibcirctable">
                <tr>
                  <td>
                       <input type=button value=%s onClick="history.go(-1)" class="formbutton">
                       <input type="submit"   value=%s class="formbutton">
                       <input type=hidden name=tup_infos value="%s">
                  </td>
                 </tr>
                </table>
                <br />
                <br />
                </form>
                </div>
                """ % (CFG_SITE_URL, _("Borrower information"),
                       _("Name"), name,
                       _("Email"), email,
                       _("Phone"), phone,
                       _("Address"), address,
                       _("Mailbox"), mailbox,
                       _("Back"), _("Confirm"),
                       tup_infos)

        return out

    def tmpl_update_borrower_info_step5(self, ln=CFG_SITE_LANG):

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_

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
                       <input type=button value='%s' onClick= onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1'"
                       class="formbutton">
                  </td>
                 </tr>
                </table>
                <br />
                <br />
                </div>
                """ % (_("The information has been updated."),
                       _("Back to home"),
                       CFG_SITE_URL)

        return out

    def tmpl_add_new_library_step1(self, ln=CFG_SITE_LANG):

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_

        out += """
            <style type="text/css"> @import url("/img/tablesorter.css"); </style>
            <div class="bibcircbottom" align="center">
            <form name="add_new_library_step1_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/add_new_library_step2" method="get" >
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
                      <input type="text" style='border: 1px solid #cfcfcf' size=50 name="name">
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
                      <input type="text" style='border: 1px solid #cfcfcf' size=50 name="address">
                    </td>
                 </tr>
                 <tr>
                    <th width="70">%s</th>
                    <td>
                    <select name="type"  style='border: 1px solid #cfcfcf'>
                          <option value ="internal">internal</option>
                          <option value ="external">external</option>
                      </select>
                    </td>
                 </tr>
                 <tr>
                    <th width="70" valign="top">%s</th>
                    <td>
                      <textarea name="notes" rows="5" cols="39" style='border: 1px solid #cfcfcf'></textarea>
                    </td>
                 </tr>
                </table>
                <br />
                <table class="bibcirctable">
                <tr align="center">
                  <td>
                       <input type=button value=%s onClick="history.go(-1)" class="formbutton">
                       <input type="submit"   value=%s class="formbutton">
                  </td>
                 </tr>
                </table>
                <br />
                <br />
                </form>
                </div>
                """ % (CFG_SITE_URL, _("New library information"), _("Name"),
                       _("Email"), _("Phone"), _("Address"), _("Type"), _("Notes"),
                       _("Back"), _("Continue"))


        return out

    def tmpl_add_new_library_step2(self, tup_infos, ln=CFG_SITE_LANG):

        _ = gettext_set_language(ln)

        (name, email, phone, address, lib_type, notes) = tup_infos

        out = """ """

        out += _MENU_

        out += """
            <div class="bibcircbottom">
            <form name="add_new_library_step2_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/add_new_library_step3" method="get" >
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
                       <input type=button value=%s onClick="history.go(-1)" class="formbutton">
                       <input type="submit"   value=%s class="formbutton">
                       <input type=hidden name=tup_infos value="%s">
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
                       tup_infos)

        return out


    def tmpl_add_new_library_step3(self, ln=CFG_SITE_LANG):

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_

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
                       <input type=button value=%s
                        onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1'"
                        class="formbutton">
                  </td>
                 </tr>
                </table>
                <br />
                <br />
                </div>
                """ % (_("A new library has been registered."),
                       _("Back to home"),
                       CFG_SITE_URL)

        return out

    def tmpl_update_library_info_step1(self, infos, ln=CFG_SITE_LANG):
        """
        Template for the admin interface. Search borrower.

        @param ln: language
        """
        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += _MENU_

        out += """
        <div class="bibcircbottom">
        <br /><br />         <br />
        <form name="update_library_info_step1_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/update_library_info_step2" method="get" >
             <table class="bibcirctable">
                  <tr align="center">
                    <td class="bibcirctableheader">%s
                     <input type="radio" name="column" value="name" checked>name
                     <input type="radio" name="column" value="email">email
                     <br>
                     <br>
                     </td>
                  </tr>
                  <tr align="center">
                        <td><input type="text" size="45" name="string" style='border: 1px solid #cfcfcf'></td>
                  </tr>
             </table>
        <br />
        <table class="bibcirctable">
             <tr align="center">
                  <td>
                        <input type=button value='%s'
                         onClick="history.go(-1)" class="formbutton">
                        <input type="submit" value="Search" class="formbutton">

                  </td>
             </tr>
        </table>
        <form>
        <br /><br />
        <br />
        <br />
        </div>

        """ % (CFG_SITE_URL,
               _("Search library by"),
               _("Back"))

        return out


    def tmpl_update_library_info_step2(self, result, ln=CFG_SITE_LANG):
        """
        @param result: search result
        @param ln: language
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_

        out += """
        <style type="text/css"> @import url("/img/tablesorter.css"); </style>
        <div class="bibcircbottom" align="center">
        <br />
        <table class="bibcirctable">
          <tr align="center">
            <td class="bibcirccontent">
               <strong>%s library(ies) found</strong>
            </td>
          </tr>
        </table>
        <br />
        <table class="tablesortersmall" border="0" cellpadding="0" cellspacing="1">
         <th align="center">%s</th>

        """ % (len(result), _("Library(ies)"))

        for (library_id, name) in result:
            library_link = create_html_link(CFG_SITE_URL +
                                            '/admin/bibcirculation/bibcirculationadmin.py/update_library_info_step3',
                                            {'library_id': library_id, 'ln': ln},
                                            (name))

            out += """
            <tr align="center">
                 <td class="bibcirccontent" width="70">%s
                 <input type=hidden name=library_id value=%s></td>
            </tr>
            """ % (library_link, library_id)


        out += """
             </table>
             <br />
             """

        out += """
        <table class="bibcirctable">
             <tr align="center">
                  <td><input type=button value=%s
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

        (library_id, name, address, email, phone, _notes) = library_info

        out = """ """

        out += _MENU_

        out += """
            <style type="text/css"> @import url("/img/tablesorter.css"); </style>
            <div class="bibcircbottom" align="center">
            <form name="update_library_info_step3_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/update_library_info_step4" method="get" >
             <input type=hidden name=library_id value=%s>
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
                      <input type="text" style='border: 1px solid #cfcfcf' size=50 name="name" value="%s">
                    </td>
                </tr>
                <tr>
                    <th width="70">%s</th>
                    <td>
                      <input type="text" style='border: 1px solid #cfcfcf' size=50 name="email" value="%s">
                    </td>
                </tr>
                <tr>
                    <th width="70">%s</th>
                    <td>
                      <input type="text" style='border: 1px solid #cfcfcf' size=50 name="phone" value="%s">
                    </td>
                </tr>
                <tr>
                    <th width="70">%s</th>
                    <td>
                      <input type="text" style='border: 1px solid #cfcfcf' size=50 name="address" value="%s">
                    </td>
                 </tr>
                </table>
                <br />
                <table class="bibcirctable">
                <tr align="center">
                  <td>
                       <input type=button value=%s
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit"
                       value=%s class="formbutton">

                  </td>
                 </tr>
                </table>
                <br />
                <br />
                </form>
                </div>
                """ % (CFG_SITE_URL, library_id, _("Library information"),
                       _("Name"), name,
                       _("Email"), email,
                       _("Phone"), phone,
                       _("Address"), address,
                       _("Back"), _("Continue"))


        return out

    def tmpl_update_library_info_step4(self, tup_infos, ln=CFG_SITE_LANG):

        (_library_id, name, email, phone, address) = tup_infos

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_

        out += """
            <style type="text/css"> @import url("/img/tablesorter.css"); </style>
            <div class="bibcircbottom" align="center">
            <form name="update_library_info_step4_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/update_library_info_step5" method="get" >
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
                </table>
                <br />
                <table class="bibcirctable">
                <tr align="center">
                  <td>
                       <input type=button value=%s
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit"
                       value=%s class="formbutton">

                       <input type=hidden name=tup_infos value="%s">
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
                       _("Back"), _("Continue"),
                       tup_infos)

        return out

    def tmpl_update_library_info_step5(self, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_

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
                       <input type=button value=%s
                        onClick= onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1'"
                        class="formbutton">
                  </td>
                 </tr>
                </table>
                <br />
                <br />
                </div>
                """ % (_("The information has been updated."),
                       _("Back to home"),
                       CFG_SITE_URL)

        return out

    def tmpl_new_book_step1(self, ln=CFG_SITE_LANG):

        _ = gettext_set_language(ln)

        out = _MENU_

        out += """
        <br />
        <br />
          <div class="bibcircbottom" align="center">
          <br />
          <br />
          <style type="text/css"> @import url("/img/tablesorter.css"); </style>
           <form name="display_ill_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/new_book_step2" method="get">
             <table class="bibcirctable">
                  <tr align="center">
                    <td class="bibcirctableheader">%s</td>
                  </tr>
                </table>
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

           """  % (CFG_SITE_URL,
                   _("Item details"),
                   _("Book title"),
                   _("Author(s)"),
                   _("Place"),
                   _("Publisher"),
                   _("Year"),
                   _("Edition"),
                   _("ISBN"))



        #conditions_link = """<a href="http://library.web.cern.ch/library/Library/ill_faq.html" target="_blank">conditions</a>"""

        out += """
             <table class="bibcirctable">
                <tr align="center">
                  <td>
                       <input type=button value=%s
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit"
                       value=%s class="formbutton">

                  </td>
                 </tr>
             </table>
             </form>
             <br />
             <br />
             </div>
             """ % (_("Back"), _("Continue"))

        return out

    def tmpl_new_book_step2(self, ln=CFG_SITE_LANG):
        ### FIXME ###
        return "Y aquí se hace algo..."

    def tmpl_add_new_copy_step1(self):
        """
        @param ln: language of the page
        """

        out = _MENU_

        out += """
        <div class="bibcircbottom">
        <form name="add_new_copy_step1_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/add_new_copy_step2" method="get" >
        <br />
        <br />
        <br />
        <input type=hidden name=start value="0">
        <input type=hidden name=end value="10">
        <table class="bibcirctable">
           <tr align="center">
             <td class="bibcirctableheader">Search item by
             <input type="radio" name="f" value="" checked>any field
             <input type="radio" name="f" value="name">year
             <input type="radio" name="f" value="author">author
             <input type="radio" name="f" value="title">title
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

                  <input type=button value="Back"
                   onClick="history.go(-1)" class="formbutton">
                  <input type="submit" value="Search" class="formbutton">

               </td>
             </tr>
        </table>
        <br />
        <br />
        <br />
        <br />
        </div>
        <form>

        """ % (CFG_SITE_URL)

        return out


    def tmpl_add_new_copy_step2(self, result, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = """  """

        out += _MENU_

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
                                          '/admin/bibcirculation/bibcirculationadmin.py/add_new_copy_step3',
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
        <input type=button value="Back" onClick="history.go(-1)" class="formbutton">
        </td>
        </tr>
        </table>
        <br />
       <br />
        <br />
        </div>
        """
        return out


    def tmpl_add_new_copy_step3(self, recid, result, libraries,
                                infos, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += _MENU_

        (book_title, book_year, book_author, book_isbn, book_editor) = book_information_from_MARC(int(recid))

        if book_isbn:
            book_cover = get_book_cover(book_isbn)
        else:
            book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)


        out += """
           <style type="text/css"> @import url("/img/tablesorter.css"); </style>
           <script src="/js/jquery.js" type="text/javascript"></script>
            <script src="/js/jquery.tablesorter.js" type="text/javascript"></script>
            <script type="text/javascript">
            $(document).ready(function() {
              $('#table_copies').tablesorter({widthFixed: true, widgets: ['zebra']})
            });
            </script>
           <form name="add_new_copy_step3_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/add_new_copy_step4" method="get" >
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
                     <td class="bibcirccontent"><img style='border: 1px solid #cfcfcf' src="%s" alt="Book Cover"/></td>
                     </tr>
              </table>

           <br />
           <table class="bibcirctable">
                <tr>
                     <td class="bibcirctableheader">%s</td>
                </tr>
           </table>

           """  % (CFG_SITE_URL,
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
                   _("Copies of %s" % book_title))


        out += """<table id="table_copies" class="tablesorter" border="0" cellpadding="0" cellspacing="1">
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

            library_link = create_html_link(CFG_SITE_URL +
                                            '/admin/bibcirculation/bibcirculationadmin.py/get_library_details',
                                            {'library_id': libid, 'ln': ln},
                                            (lib_name))

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


        out += """
           </tbody>
           </table>
           <br />
          <table class="bibcirctable">
                <tr>
                     <td class="bibcirctableheader">%s</td>
                </tr>
           </table>
           <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">
                <tr>
                    <th width="100">%s</th>
                    <td>
                      <input type="text" style='border: 1px solid #cfcfcf' size=35 name="barcode">
                    </td>
                </tr>
                <tr>
                    <th width="100">%s</th>
                    <td>
                      <select name="library"  style='border: 1px solid #cfcfcf'>

                """ % (_("New copy details"), _("Barcode"), _("Library"))

        for(library_id, name) in libraries:
            out +="""<option value ="%s">%s</option>""" % (library_id, name)

        out += """
                    </select>
                    </td>
                </tr>
                <tr>
                    <th width="100">%s</th>
                    <td>
                      <input type="text" style='border: 1px solid #cfcfcf' size=35 name="location">
                    </td>
                </tr>
                <tr>
                    <th width="100">%s</th>
                    <td>
                      <select name="collection" style='border: 1px solid #cfcfcf'>
                        <option value = "Monography">Monography</option>
                        <option value = "Reference">Reference</option>
                        <option value = "Archives">Archives</option>
                        <option value = "Library">Library</option>
                        <option value = "Conference">Conference</option>
                        <option value = "LSL Depot">LSL Depot</option>
                        <option value = "Oversize">Oversize</option>
                        <option value = "Official">Official</option>
                        <option value = "Pamphlet">Pamphlet</option>
                        <option value = "CDROM">CDROM</option>
                        <option value = "Standards">Standards</option>
                        <option value = "Video & Trainings">Video & Trainings</option>
                      </select>
                    </td>
                </tr>
                <tr>
                    <th width="100">%s</th>
                    <td>
                      <input type="text" style='border: 1px solid #cfcfcf' size=35 name="description">
                    </td>
                </tr>
                <tr>
                    <th width="100">%s</th>
                    <td>
                      <select name="loan_period"  style='border: 1px solid #cfcfcf'>
                          <option value ="4 weeks">4 weeks</option>
                          <option value ="1 week">1 week</option>
                          <option value ="reference">reference</option>
                      </select>
                    </td>
                 </tr>
                 <tr>
                    <th width="100">%s</th>
                    <td>
                    <select name="status"  style='border: 1px solid #cfcfcf'>
                          <option value ="available">available</option>
                          <option value ="missing">missing</option>
                    </select>
                    </td>
                 </tr>
                </table>
           <br />
           <table class="bibcirctable">
                <tr>
                     <td>
                       <input type=button value="Back"
                        onClick="history.go(-1)" class="formbutton">
                       <input type="submit" value="Continue" class="formbutton">
                       <input type=hidden name=recid value=%s>
                     </td>
                </tr>
           </table>
           <br />
           <br />
           </div>
           </form>
           """ % (_("Location"), _("Collection"), _("Description"),
                  _("Loan period"), _("Status"), recid)

        return out

    def tmpl_add_new_copy_step4(self, tup_infos, ln=CFG_SITE_LANG):
        """
        @param tup_info: item's informations
        @type tup_info: tuple

        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_

        out += """
            <div class="bibcircbottom">
            <form name="add_new_copy_step4_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/add_new_copy_step5" method="get" >
              <br />
              <br />
              <table class="bibcirctable">
                <tr>
                    <td width="90">%s</td> <td class="bibcirccontent">%s</td>
                </tr>
                <tr>
                    <td width="90">%s</td> <td class="bibcirccontent">%s</td>
                </tr>
                <tr>
                    <td width="90">%s</td> <td class="bibcirccontent">%s</td>
                </tr>
                <tr>
                    <td width="90">%s</td> <td class="bibcirccontent">%s</td>
                 </tr>
                 <tr>
                    <td width="90">%s</td> <td class="bibcirccontent">%s</td>
                 </tr>
                 <tr>
                    <td width="90">%s</td> <td class="bibcirccontent">%s</td>
                 </tr>
                 <tr>
                    <td width="90">%s</td> <td class="bibcirccontent">%s</td>
                 </tr>
                </table>
                <br />
                <table class="bibcirctable">
                <tr>
                  <td>
                       <input type=button value=%s
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit"
                       value=%s class="formbutton">

                       <input type=hidden name=tup_infos value="%s">

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
                       _("Back"), _("Continue"), tup_infos)

        return out

    def tmpl_add_new_copy_step5(self, recid, ln=CFG_SITE_LANG):
        """
        @param recid: identify the record. Primary key of bibrec.
        @type recid: int
        """

        _ = gettext_set_language(ln)

        item_link = create_html_link(CFG_SITE_URL +
                                     '/admin/bibcirculation/bibcirculationadmin.py/get_item_details',
                                     {'recid': recid, 'ln': ln},
                                     (_("new copy")))

        out = """ """

        out += _MENU_

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
                       onClick= onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1'" class="formbutton">
                  </td>
                 </tr>
                </table>
                <br />
                <br />
                </div>
                """ % (_("A %s has been added." % (item_link)),
                       _("Back to home"),
                       CFG_SITE_URL)

        return out

    def tmpl_update_item_info_step1(self):
        """
        @param ln: language of the page
        """

        out = """  """

        out += _MENU_

        out += """
        <div class="bibcircbottom">
        <form name="update_item_info_step1_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/update_item_info_step2" method="get" >
        <br />
        <br />
        <br />
        <input type=hidden name=start value="0">
        <input type=hidden name=end value="10">
        <table class="bibcirctable">
                <tr align="center">
                  <td class="bibcirctableheader">Search item by
                    <input type="radio" name="f" value="" checked>any field
                    <input type="radio" name="f" value="name">year
                    <input type="radio" name="f" value="email">author
                    <input type="radio" name="f" value="email">title
                    <br /><br />
                  </td>
                <tr align="center">
                  <td><input type="text" size="50" name="p" style='border: 1px solid #cfcfcf'></td>
                </tr>
        </table>
        <br />
        <table class="bibcirctable">
               <tr align="center">
                     <td>
                         <input type=button value="Back"
                          onClick="history.go(-1)" class="formbutton">

                         <input type="submit" value="Search" class="formbutton">
                     </td>
                    </tr>
        </table>
        <br />
        <br />
        <br />
        <br />
        </div>
        <form>
        """ % (CFG_SITE_URL)

        return out

    def tmpl_update_item_info_step2(self, result, ln=CFG_SITE_LANG):
        """
        @param result: list with recids
        @type result: list

        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = """  """

        out += _MENU_

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
                                          '/admin/bibcirculation/bibcirculationadmin.py/update_item_info_step3',
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
        <input type=button value="Back" onClick="history.go(-1)" class="formbutton">
        </td>
        </tr>
        </table>
        <br />
        <br />
        <br />
        </div>
        """
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
        out += _MENU_

        (book_title, book_year, book_author, book_isbn, book_editor) = book_information_from_MARC(int(recid))

        if book_isbn:
            book_cover = get_book_cover(book_isbn)
        else:
            book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)

        out += """
           <form name="update_item_info_step3_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/update_item_info_step4" method="get" >
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
                     <td class="bibcirccontent"><img style='border: 1px solid #cfcfcf' src="%s" alt="Book Cover"/></td>
                     </tr>
              </table>

           <br />

           """  % (CFG_SITE_URL,
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


        for (barcode, loan_period, lib_name, libid, location, nb_requests, status, collection, description) in result:

            library_link = create_html_link(CFG_SITE_URL +
                                            '/admin/bibcirculation/bibcirculationadmin.py/get_library_details',
                                            {'library_id': libid, 'ln': ln},
                                            (lib_name))

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
                     <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/update_item_info_step4?barcode=%s'"
                     value=%s class="formbutton">
                     </td>
                     <td class="bibcirccontent" width="350"></td>
                 </tr>
                 """ % (barcode, status, library_link, location, loan_period,
                        nb_requests, collection, description, CFG_SITE_URL,
                        barcode, _("Update"))

        out += """
           </table>
           <br />
           <table class="bibcirctable">
                <tr>
                     <td>
                        <input type=button value="%s"
                         onClick="history.go(-1)" class="formbutton">
                        <input type=hidden name=recid value=%s></td>
                </tr>
           </table>
           <br />
           <br />
           </div>
           """ % (_("Back"), recid)

        return out

    def tmpl_update_item_info_step4(self, recid, result, libraries, ln=CFG_SITE_LANG):
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

        out = """
        """
        out += _MENU_

        (book_title, book_year, book_author, book_isbn, book_editor) = book_information_from_MARC(int(recid))

        if book_isbn:
            book_cover = get_book_cover(book_isbn)
        else:
            book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)

        out += """
           <style type="text/css"> @import url("/img/tablesorter.css"); </style>
           <form name="update_item_info_step4_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/update_item_info_step6" method="get" >
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
                 <td class="bibcirccontent"><img style='border: 1px solid #cfcfcf' src="%s" alt="Book Cover"/></td>
               </tr>
              </table>

           <br />

           """  % (CFG_SITE_URL,
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

        out += """
             <table class="bibcirctable">
                <tr>
                     <td class="bibcirctableheader">%s</td>
                </tr>
             </table>
             <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">
               <tr>
                 <th width="100">%s</th>
                 <td>%s</td><input type=hidden name=barcode value=%s>
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
                out +="""<option value ="%s" selected>%s</option>""" % (library_id, name)

            else:
                out +="""<option value ="%s">%s</option>""" % (library_id, name)

        out += """
                    </select>
                    </td>
                </tr>
                <tr>
                  <th width="100">%s</th>
                  <td><input type="text" style='border: 1px solid #cfcfcf' size=35 name="location" value="%s"></td>
                </tr>
                <tr>
                  <th width="100">%s</th>
                  <td>
                    <select name="collection" style='border: 1px solid #cfcfcf'>
                    """ % (_("Location"), result[4],
                           _("Collection"))

        if result[3] == 'Monography':
            out += """
                      <option value = "Monography" selected>Monography</option>
                      <option value = "Reference">Reference</option>
                      <option value = "Archives">Archives</option>
                      <option value = "Library">Library</option>
                      <option value = "Conference">Conference</option>
                      <option value = "LSL Depot">LSL Depot</option>
                      <option value = "Oversize">Oversize</option>
                      <option value = "Official">Official</option>
                      <option value = "Pamphlet">Pamphlet</option>
                      <option value = "CDROM">CDROM</option>
                      <option value = "Standards">Standards</option>
                      <option value = "Video & Trainings">Video & Trainings</option>
                   """
        elif result[3] == 'Reference':
            out += """
                      <option value = "Monography">Monography</option>
                      <option value = "Reference" selected>Reference</option>
                      <option value = "Archives">Archives</option>
                      <option value = "Library">Library</option>
                      <option value = "Conference">Conference</option>
                      <option value = "LSL Depot">LSL Depot</option>
                      <option value = "Oversize">Oversize</option>
                      <option value = "Official">Official</option>
                      <option value = "Pamphlet">Pamphlet</option>
                      <option value = "CDROM">CDROM</option>
                      <option value = "Standards">Standards</option>
                      <option value = "Video & Trainings">Video & Trainings</option>
                   """

        elif result[3] == 'Archives':
            out += """
                      <option value = "Monography">Monography</option>
                      <option value = "Reference">Reference</option>
                      <option value = "Archives" selected>Archives</option>
                      <option value = "Library">Library</option>
                      <option value = "Conference">Conference</option>
                      <option value = "LSL Depot">LSL Depot</option>
                      <option value = "Oversize">Oversize</option>
                      <option value = "Official">Official</option>
                      <option value = "Pamphlet">Pamphlet</option>
                      <option value = "CDROM">CDROM</option>
                      <option value = "Standards">Standards</option>
                      <option value = "Video & Trainings">Video & Trainings</option>
                   """

        elif result[3] == 'Library':
            out += """
                      <option value = "Monography">Monography</option>
                      <option value = "Reference">Reference</option>
                      <option value = "Archives">Archives</option>
                      <option value = "Library" selected>Library</option>
                      <option value = "Conference">Conference</option>
                      <option value = "LSL Depot">LSL Depot</option>
                      <option value = "Oversize">Oversize</option>
                      <option value = "Official">Official</option>
                      <option value = "Pamphlet">Pamphlet</option>
                      <option value = "CDROM">CDROM</option>
                      <option value = "Standards">Standards</option>
                      <option value = "Video & Trainings">Video & Trainings</option>
                   """

        elif result[3] == 'Conference':
            out += """
                      <option value = "Monography">Monography</option>
                      <option value = "Reference">Reference</option>
                      <option value = "Archives">Archives</option>
                      <option value = "Library">Library</option>
                      <option value = "Conference" selected>Conference</option>
                      <option value = "LSL Depot">LSL Depot</option>
                      <option value = "Oversize">Oversize</option>
                      <option value = "Official">Official</option>
                      <option value = "Pamphlet">Pamphlet</option>
                      <option value = "CDROM">CDROM</option>
                      <option value = "Standards">Standards</option>
                      <option value = "Video & Trainings">Video & Trainings</option>
                   """

        elif result[3] == 'LSL Depot':
            out += """
                      <option value = "Monography">Monography</option>
                      <option value = "Reference">Reference</option>
                      <option value = "Archives">Archives</option>
                      <option value = "Library">Library</option>
                      <option value = "Conference">Conference</option>
                      <option value = "LSL Depot" selected>LSL Depot</option>
                      <option value = "Oversize">Oversize</option>
                      <option value = "Official">Official</option>
                      <option value = "Pamphlet">Pamphlet</option>
                      <option value = "CDROM">CDROM</option>
                      <option value = "Standards">Standards</option>
                      <option value = "Video & Trainings">Video & Trainings</option>
                   """

        elif result[3] == 'Oversize':
            out += """
                      <option value = "Monography">Monography</option>
                      <option value = "Reference">Reference</option>
                      <option value = "Archives">Archives</option>
                      <option value = "Library">Library</option>
                      <option value = "Conference">Conference</option>
                      <option value = "LSL Depot">LSL Depot</option>
                      <option value = "Oversize" selected>Oversize</option>
                      <option value = "Official">Official</option>
                      <option value = "Pamphlet">Pamphlet</option>
                      <option value = "CDROM">CDROM</option>
                      <option value = "Standards">Standards</option>
                      <option value = "Video & Trainings">Video & Trainings</option>
                   """

        elif result[3] == 'Official':
            out += """
                      <option value = "Monography">Monography</option>
                      <option value = "Reference">Reference</option>
                      <option value = "Archives">Archives</option>
                      <option value = "Library">Library</option>
                      <option value = "Conference">Conference</option>
                      <option value = "LSL Depot">LSL Depot</option>
                      <option value = "Oversize">Oversize</option>
                      <option value = "Official" selected>Official</option>
                      <option value = "Pamphlet">Pamphlet</option>
                      <option value = "CDROM">CDROM</option>
                      <option value = "Standards">Standards</option>
                      <option value = "Video & Trainings">Video & Trainings</option>
                   """

        elif result[3] == 'Pamphlet':
            out += """
                      <option value = "Monography">Monography</option>
                      <option value = "Reference">Reference</option>
                      <option value = "Archives">Archives</option>
                      <option value = "Library">Library</option>
                      <option value = "Conference">Conference</option>
                      <option value = "LSL Depot">LSL Depot</option>
                      <option value = "Oversize">Oversize</option>
                      <option value = "Official">Official</option>
                      <option value = "Pamphlet" select>Pamphlet</option>
                      <option value = "CDROM">CDROM</option>
                      <option value = "Standards">Standards</option>
                      <option value = "Video & Trainings">Video & Trainings</option>
                   """

        elif result[3] == 'CDROM':
            out += """
                      <option value = "Monography">Monography</option>
                      <option value = "Reference">Reference</option>
                      <option value = "Archives">Archives</option>
                      <option value = "Library">Library</option>
                      <option value = "Conference">Conference</option>
                      <option value = "LSL Depot">LSL Depot</option>
                      <option value = "Oversize">Oversize</option>
                      <option value = "Official">Official</option>
                      <option value = "Pamphlet">Pamphlet</option>
                      <option value = "CDROM" selected>CDROM</option>
                      <option value = "Standards">Standards</option>
                      <option value = "Video & Trainings">Video & Trainings</option>
                   """

        elif result[3] == 'Standards':
            out += """
                      <option value = "Monography">Monography</option>
                      <option value = "Reference">Reference</option>
                      <option value = "Archives">Archives</option>
                      <option value = "Library">Library</option>
                      <option value = "Conference">Conference</option>
                      <option value = "LSL Depot">LSL Depot</option>
                      <option value = "Oversize">Oversize</option>
                      <option value = "Official">Official</option>
                      <option value = "Pamphlet">Pamphlet</option>
                      <option value = "CDROM">CDROM</option>
                      <option value = "Standards" selected>Standards</option>
                      <option value = "Video & Trainings">Video & Trainings</option>
                   """

        elif result[3] == 'Video & Trainings':
            out += """
                      <option value = "Monography">Monography</option>
                      <option value = "Reference">Reference</option>
                      <option value = "Archives">Archives</option>
                      <option value = "Library">Library</option>
                      <option value = "Conference">Conference</option>
                      <option value = "LSL Depot">LSL Depot</option>
                      <option value = "Oversize">Oversize</option>
                      <option value = "Official">Official</option>
                      <option value = "Pamphlet">Pamphlet</option>
                      <option value = "CDROM">CDROM</option>
                      <option value = "Standards">Standards</option>
                      <option value = "Video & Trainings" selected>Video & Trainings</option>
                   """

        else:
            out += """
                      <option value = "">-</option>
                      <option value = "Monography">Monography</option>
                      <option value = "Reference">Reference</option>
                      <option value = "Archives">Archives</option>
                      <option value = "Library">Library</option>
                      <option value = "Conference">Conference</option>
                      <option value = "LSL Depot">LSL Depot</option>
                      <option value = "Oversize">Oversize</option>
                      <option value = "Official">Official</option>
                      <option value = "Pamphlet">Pamphlet</option>
                      <option value = "CDROM">CDROM</option>
                      <option value = "Standards">Standards</option>
                      <option value = "Video & Trainings">Video & Trainings</option>
                   """

        out += """
                   </select>
                  </td>
                </tr>
                <tr>
                  <th width="100">%s</th>
                  <td><input type="text" style='border: 1px solid #cfcfcf' size=35 name="description" value="%s"></td>
                </tr>
                <tr>
                    <th width="100">%s</th>
                    <td>
                    <select name="loan_period" style='border: 1px solid #cfcfcf'>
                    """ % (_("Description"), result[5] or '-',
                           _("Loan period"))

        if result[6] == '4 weeks':
            out += """
                    <option value ="4 weeks" selected>4 weeks</option>
                    <option value ="1 week">1 week</option>
                    <option value ="reference">reference</option>
                    """
        elif result[6] == '1 week':
            out += """
                    <option value ="4 weeks">4 weeks</option>
                    <option value ="1 week" selected>1 week</option>
                    <option value ="reference">reference</option>
                    """
        else:
            out += """
                    <option value ="4 weeks">4 weeks</option>
                    <option value ="1 week">1 week</option>
                    <option value ="reference" selected>reference</option>
                    """

        out += """</select>
                    </td>
                 </tr>
                 <tr>
                    <th width="100">%s</th>
                    <td>
                      <select name="status"  style='border: 1px solid #cfcfcf'>

                      """ % (_("Status"))

        if result[7] == 'available':
            out += """
                          <option value ="available" selected>available</option>
                          <option value ="missing">missing</option>
                          """
        elif result[7] == 'on loan':
            out += """
                          <option value ="available">available</option>
                          <option value ="on loan" selected>on loan</option>
                          <option value ="missing">missing</option>
                          """

        elif result[7] == 'requested':
            out += """
                          <option value ="available">available</option>
                          <option value ="missing">missing</option>
                          <option value ="requested" selected>requested</option>
                          """
        else:
            out += """
                          <option value ="available">available</option>
                          <option value ="missing" selected>missing</option>
                          """
        out += """  </select>
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
                       <input type=hidden name=recid value=%s>
                     </td>
                </tr>
           </table>
           <br />
           <br />
           </div>
           </form>
           """ % (_("Back"), _("Continue"), recid)

        return out

    def tmpl_update_item_info_step5(self, tup_infos, ln=CFG_SITE_LANG):
        """
        @param tup_info: item's informations
        @type tup_info: tuple

        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_

        out += """
            <style type="text/css"> @import url("/img/tablesorter.css"); </style>
            <div class="bibcircbottom">
            <form name="update_item_info_step5_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/update_item_info_step6" method="get" >
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
                </table>
                <br />
                <table class="bibcirctable">
                <tr>
                  <td>
                       <input type=button value=%s
                         onClick="history.go(-1)" class="formbutton">
                       <input type="submit"
                        value=%s class="formbutton">
                       <input type=hidden name=tup_infos value="%s">

                  </td>
                 </tr>
                </table>
                <br />
                <br />
                </form>
                </div>
                """ % (CFG_SITE_URL, _("New copy information"),
                       _("Barcode"), tup_infos[0],
                       _("Library"), tup_infos[2],
                       _("Location"), tup_infos[3],
                       _("Collection"), tup_infos[4],
                       _("Description"), tup_infos[5],
                       _("Loan period"), tup_infos[6],
                       _("Status"), tup_infos[7],
                       _("Back"), _("Confirm"), tup_infos)

        return out

    def tmpl_update_item_info_step6(self, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_

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
                        onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1'" class="formbutton">
                  </td>
                 </tr>
                </table>
                <br />
                <br />
                </div>
                """ % (_("This item has been updated."),
                       _("Back to home"),
                       CFG_SITE_URL)

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

        out += _MENU_

        out += """
        <div class="bibcircbottom">
        <br /><br />         <br />
        <form name="search_library_step1_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/search_library_step2" method="get" >
          <table class="bibcirctable">
           <tr align="center">
             <td class="bibcirctableheader">%s
               <input type="radio" name="column" value="name" checked>name
               <input type="radio" name="column" value="email">email
               <br>
               <br>
             </td>
           </tr>
           <tr align="center">
             <td><input type="text" size="45" name="string" style='border: 1px solid #cfcfcf'></td>
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

        """ % (CFG_SITE_URL,
               _("Search library by"),
               _("Back"),
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

        out += _MENU_

        if len(result) == 0:
            out += """
            <div class="bibcircbottom">
            <br />
            <div class="infoboxmsg">%s</div>
            <br />
            """ % (_("0 library(ies) found."))

        else:
            out += """
        <style type="text/css"> @import url("/img/tablesorter.css"); </style>
        <div class="bibcircbottom" align="center">
        <br />
        <table class="bibcirctable">
          <tr align="center">
            <td class="bibcirccontent">
              <strong>%s library(ies) found</strong>
            </td>
          </tr>
        </table>
        <br />
        <table class="tablesortersmall" border="0" cellpadding="0" cellspacing="1">
          <th align="center">%s</th>

        """ % (len(result), _("Library(ies)"))

            for (library_id, name) in result:

                library_link = create_html_link(CFG_SITE_URL +
                                            '/admin/bibcirculation/bibcirculationadmin.py/get_library_details',
                                            {'library_id': library_id, 'ln': ln},
                                            (name))

                out += """
            <tr align="center">
                 <td width="70">%s
                 <input type=hidden name=library_id value=%s></td>
            </tr>
            """ % (library_link, library_id)

        out += """
        </table>
        <br />
        <table class="bibcirctable">
             <tr align="center">
                  <td>
                    <input type=button value=%s
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

        out += _MENU_

        out +="""
            <div class="bibcircbottom">
            <form name="library_notes" action="%s/admin/bibcirculation/bibcirculationadmin.py/get_library_notes" method="get" >
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
                                           '/admin/bibcirculation/bibcirculationadmin.py/get_library_notes',
                                           {'delete_key': key, 'library_id': library_id, 'ln': ln},
                                           (_("[delete]")))

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
                      <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/get_library_details?library_id=%s'"
                       value=%s class='formbutton'>
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
               CFG_SITE_URL,
               library_id,
               _("Back"),
               _("Confirm"))

        return out



    def tmpl_change_due_date_step1(self, loan_details, loan_id, borrower_id, ln=CFG_SITE_LANG):
        """
        Return the form where the due date can be changed.

        @param loan_details: the information related with the loan.
        @type loan_details: tuple

        @param loan_id: identify the loan. Primary key of crcLOAN.
        @type loan_id: int

        @param borrower_id: identify the borrower. Primary key of crcBORROWER.
        @type borrower_id: int

        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_

        (recid, barcode, loaned_on, due_date, loan_status, loan_period, item_status) = loan_details

        if item_status == 'requested':
            request_status = 'Yes'
        else:
            request_status = 'No'

        out +="""
            <div class="bibcircbottom">
            <form name="borrower_notes" action="%s/admin/bibcirculation/bibcirculationadmin.py/change_due_date_step2" method="get" >
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

            <script type="text/javascript" language='JavaScript' src="%s/js/jquery-ui.min.js"></script>

            <table class="bibcirctable">
              <tr align="left">
                <td width="230" class="bibcirctableheader">%s
                    <script type="text/javascript">
                        $(function(){
                            $("#date_picker1").datepicker({dateFormat: 'yy-mm-dd', showOn: 'button', buttonImage: "%s/img/calendar.gif", buttonImageOnly: true});
                        });
                    </script>
                    <input type="text" size="12" id="date_picker1" name="period_from" value="%s" style='border: 1px solid #cfcfcf'>
                </td>
              </tr>
            </table>
            <br />
            """ % (CFG_SITE_URL,
                    _("New due date: "), CFG_SITE_URL, due_date)


        out += """
        <table class="bibcirctable">
             <tr>
                  <td>
                       <input type=hidden name=loan_id value=%s>
                       <input type=hidden name=borrower_id value=%s>

                       <input type=button value=%s
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

    def tmpl_change_due_date_step2(self, due_date, borrower_id, ln=CFG_SITE_LANG):
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

        out += _MENU_

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
                    <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/get_borrower_loans_details?borrower_id=%s'"
                    value=%s class='formbutton'>
                  </td>
                 </tr>
                </table>
                <br />
                <br />
                </div>
                """ % (_("The due date has been updated. New due date: %s" % (due_date)),
                       CFG_SITE_URL, borrower_id, _("Back borrower's loans"))


        return out


    def tmpl_create_new_loan_step1(self, borrower, infos, ln=CFG_SITE_LANG):
        """
        Display the borrower's information and a form where it is
        possible to search for an item.

        @param borrower: borrower's information.
        @type borrower: tuple

        @param infos: informations
        @type infos: list

        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += _MENU_

        (borrower_id, name, email, phone, address, mailbox) = borrower

        out += """
            <form name="create_new_loan_form1" action="%s/admin/bibcirculation/bibcirculationadmin.py/create_new_loan_step2" method="get" >
            <div class="bibcircbottom">
            <input type=hidden name=borrower_id value=%s>
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
            </table>
            """% (CFG_SITE_URL,
                  borrower_id,
                  _("Personal details"),
                  _("Name"), name,
                  _("Email"), email,
                  _("Phone"), phone,
                  _("Address"), address,
                  _("Mailbox"), mailbox)


        out +="""
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
                       <input type=button value=%s onClick="history.go(-1)" class="formbutton">
                       <input type="submit"   value=%s class="formbutton">
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


    def tmpl_create_new_request_step1(self, borrower, infos, result, p, f, ln=CFG_SITE_LANG):
        """
        Display the borrower's information and the form where it is
        possible to search for an item.

        @param borrower: borrower's information.
        @type borrower: tuple

        @param infos: informations
        @type infos: list

        @param result: result of searching for an item, using p and f.
        @type result: list

        @param p: pattern who will be used in the search process.
        @type p: string

        @param f: field who will be used in the search process.
        @type f: string

        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += _MENU_

        (borrower_id, name, email, phone, address, mailbox) = borrower

        out += """
            <style type="text/css"> @import url("/img/tablesorter.css"); </style>

            <div class="bibcircbottom">

            <br />

            <table class="bibcirctable">
            <tbody>
                <tr>
                    <td width="500" valign="top">

                    <form name="create_new_loan_form1" action="%s/admin/bibcirculation/bibcirculationadmin.py/create_new_request_step1" method="get" >
                    <input type=hidden name=borrower_id value=%s>
                    <table class="bibcirctable">
                        <tr align="center">
                            <td class="bibcirctableheader">Search item by
            """%(CFG_SITE_URL, borrower_id)

        if f == 'barcode':
            out += """
                                <input type="radio" name="f" value="">any field
                                <input type="radio" name="f" value="barcode" checked>barcode
                                <input type="radio" name="f" value="author">author
                                <input type="radio" name="f" value="title">title
              """

        elif f == 'author':
            out += """
                                <input type="radio" name="f" value="">any field
                                <input type="radio" name="f" value="barcode">barcode
                                <input type="radio" name="f" value="author" checked>author
                                <input type="radio" name="f" value="title">title
              """

        elif f == 'title':
            out += """
                                <input type="radio" name="f" value="">any field
                                <input type="radio" name="f" value="barcode">barcode
                                <input type="radio" name="f" value="author">author
                                <input type="radio" name="f" value="title" checked>title
              """

        else:
            out += """
                                <input type="radio" name="f" value="" checked>any field
                                <input type="radio" name="f" value="barcode">barcode
                                <input type="radio" name="f" value="author">author
                                <input type="radio" name="f" value="title">title
              """

        out += """
                                <br />
                                <br />
                            </td>
                        </tr>
                        <tr align="center">
                            <td><input type="text" size="50" name="p" value='%s' style='border: 1px solid #cfcfcf'></td>
                        </tr>
                    </table>
                    <br />
                    <table class="bibcirctable">
                        <tr align="center">
                            <td>
                                <input type=button value='%s' onClick="history.go(-1)" class="formbutton">
                                <input type="submit" value='%s' name='search' class="formbutton">
                            </td>
                        </tr>
                    </table>
                    </form>
        """ % (p or '', _("Back"), _("Search"))


        if result:
            out += """
            <br />
            <form name="form2" action="%s/admin/bibcirculation/bibcirculationadmin.py/create_new_request_step2" method="get" >
            <table class="bibcirctable">
              <tr width="200">
                <td align="center">
                    <select name="recid" size="12" style='border: 1px solid #cfcfcf; width:77%%'>

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
            <input type=hidden name=borrower_id value=%s>
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
                        </table>
                    </td>
                </tr>

            <br />

            """% (_("Borrower details"),
                  _("Name"), name,
                  _("Email"), email,
                  _("Phone"), phone,
                  _("Address"), address,
                  _("Mailbox"), mailbox)


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

    def tmpl_create_new_request_step2(self, user_info, holdings_information, recid, ln=CFG_SITE_LANG):
        """
        @param borrower_id: identify the borrower. Primary key of crcBORROWER.
        @type borrower_id: int

        @param holdings_information: information about holdings
        @type holdings_information: list

        @param recid: identify the record. Primary key of bibrec.
        @type recid: int
        """

        _ = gettext_set_language(ln)

        if not holdings_information:
            return _("This item has no holdings.")

        out = """ """

        out += _MENU_

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

        for (barcode, library, collection, location, description, loan_period, status, due_date) in holdings_information:
            out += """
                     <tr onMouseOver="this.className='highlight'" onMouseOut="this.className='normal'">
                          <td class="bibcirccontent">%s</td>
                          <td class="bibcirccontent">%s</td>
                          <td class="bibcirccontent" align="center">%s</td>
                          <td class="bibcirccontent" align="center">%s</td>
                          <td class="bibcirccontent" align="center">%s</td>
                          <td class="bibcirccontent" align="center">%s</td>
                          <td class="bibcirccontent" align="center">%s</td>
                          <td class="bibcirccontent" align="center">%s</td>
                          <td class="bibcirccontent" align="right">
                          <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/place_new_request_step2?barcode=%s&recid=%s&user_info=%s,%s,%s,%s,%s,%s'"
                          value='%s' class="formbutton"></td>
                     </tr>

                """ % (barcode, library, collection, location,
                       description, loan_period, status, due_date,
                       CFG_SITE_URL, barcode, recid, user_info[0],user_info[1],user_info[2],user_info[3],user_info[4],user_info[5],
                       _("Request"))

        out += """
           </table>
           <br />
           <br />
           <br />
           </div>
           """

        return out

    def tmpl_create_new_request_step3(self, borrower_id, barcode, recid, ln=CFG_SITE_LANG):
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

        out += _MENU_

        out += """

        <script type="text/javascript" language='JavaScript' src="%s/js/jquery-ui.min.js"></script>

        <form name="request_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/create_new_request_step4" method="get" >
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
              _("From:  "), CFG_SITE_URL, datetime.date.today().strftime('%Y-%m-%d'),
              _("To:  "), CFG_SITE_URL, (datetime.date.today() + datetime.timedelta(days=365)).strftime('%Y-%m-%d'))



        out += """
        <table class="bibcirctable_contents">
          <tr>
            <td align="center">
              <input type=hidden name=barcode value='%s'>
              <input type=hidden name=borrower_id value='%s'>
              <input type=hidden name=recid value='%s'>
              <input type=button value="Back" onClick="history.go(-1)" class="formbutton">
              <input type="submit" name="submit_button" value="%s" class="formbutton">
            </td>
          </tr>
        </table>
        <br />
        <br />
        </form>
        </div>

        """ % (barcode, borrower_id, recid, _('Confirm'))

        return out

    def tmpl_create_new_request_step4(self, ln=CFG_SITE_LANG):
        """
        Last step of the request procedure.

        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_


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
        <td><input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1'"
        value='%s' class='formbutton'></td>
        </table>
        <br />
        <br />
        </div>

        """ % (_("A new request has been registered with success."),
               CFG_SITE_URL, _("Back to home"))

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

        @param infos: informations
        @type infos: list

        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        (book_title, book_year, book_author, book_isbn, book_editor) = book_information_from_MARC(int(recid))

        if book_isbn:
            book_cover = get_book_cover(book_isbn)
        else:
            book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)

        out = self.tmpl_infobox(infos, ln)

        out += _MENU_

        out += """
        <style type="text/css"> @import url("/img/tablesorter.css"); </style>
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
        <form name="step1_form1" action="%s/admin/bibcirculation/bibcirculationadmin.py/place_new_request_step1" method="get" >
        <input type=hidden name=barcode value='%s'>
        <input type=hidden name=recid value='%s'>
        <table>

            """  % (CFG_SITE_URL, barcode, recid)

        if CFG_CERN_SITE == 1:

            out += """
                 <tr>
                   <td class="bibcirctableheader" align="center">Search user by

                   """

            if key == 'email':
                out += """
                   <input type="radio" name="key" value="ccid">ccid
                   <input type="radio" name="key" value="name">name
                   <input type="radio" name="key" value="email" checked>email
                   """

            elif key == 'name':
                out += """
                   <input type="radio" name="key" value="ccid">ccid
                   <input type="radio" name="key" value="name" checked>name
                   <input type="radio" name="key" value="email">email
                   """

            else:
                out += """
                   <input type="radio" name="key" value="ccid" checked>ccid
                   <input type="radio" name="key" value="name">name
                   <input type="radio" name="key" value="email">email
                   """

        else:
            out += """
                 <tr>
                   <td class="bibcirctableheader" align="center">Search borrower by

                   """

            if key == 'email':
                out += """
                   <input type="radio" name="key" value="id">id
                   <input type="radio" name="key" value="name">name
                   <input type="radio" name="key" value="email" checked>email
                   """

            elif key == 'id':
                out += """
                   <input type="radio" name="key" value="id" checked>id
                   <input type="radio" name="key" value="name">name
                   <input type="radio" name="key" value="email">email
                   """

            else:
                out += """
                   <input type="radio" name="key" value="id">id
                   <input type="radio" name="key" value="name" checked>name
                   <input type="radio" name="key" value="email">email
                   """

        out += """
                    <br><br>
                    </td>
                    </tr>
                    <tr>
                    <td align="center">
                    <input type="text" size="40" id="string" name="string"  value='%s' style='border: 1px solid #cfcfcf'>
                    </td>
                    </tr>
                    <tr>
                    <td align="center">
                    <br>
                    <input type="submit" value="Search" class="formbutton">
                    </td>
                    </tr>

                   </table>
          </form>

        """ % (string or '')

        if result:
            out += """
            <br />
            <form name="step1_form2" action="%s/admin/bibcirculation/bibcirculationadmin.py/place_new_request_step2" method="get" >
            <input type=hidden name=barcode value='%s'>
            <input type=hidden name=recid value='%s'>
            <table class="bibcirctable">
              <tr width="200">
                <td align="center">
                  <select name="user_info" size="8" style='border: 1px solid #cfcfcf; width:40%%'>

            """ % (CFG_SITE_URL, barcode, recid)

            for (ccid, name, email, phone, address, mailbox) in result:
                out += """
                       <option value ='%s,%s,%s,%s,%s,%s'>%s

                       """ % (ccid, name, email, phone, address, mailbox, name)

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

    def tmpl_place_new_request_step2(self, barcode, recid, user_info, infos, ln=CFG_SITE_LANG):
        """
        @param barcode: identify the item. Primary key of crcITEM.
        @type barcode: string

        @param recid: identify the record. Primary key of bibrec
        @type recid: int

        @param user_info: user's informations
        @type user_info: tuple

        @param infos: informations
        @type infos: list

        @param ln: language of the page
        """

        (book_title, book_year, book_author, book_isbn, book_editor) = book_information_from_MARC(int(recid))

        if book_isbn:
            book_cover = get_book_cover(book_isbn)
        else:
            book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)

        (ccid, name, email, phone, address, mailbox) = user_info

        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += _MENU_

        out += """
            <style type="text/css"> @import url("/img/tablesorter.css"); </style>
            <div class="bibcircbottom">
            <form name="step2_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/place_new_request_step3" method="get" >
            <input type=hidden name=barcode value='%s'>
            <input type=hidden name=recid value='%s'>
            <input type=hidden name=user_info value="%s">
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
              """ % (CFG_SITE_URL, barcode,
                     recid, user_info,
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
                       _("Email"), email,
                       _("Phone"), phone,
                       _("Address"), address,
                       _("Mailbox"), mailbox)

        out += """

                <script type="text/javascript" language='JavaScript' src="%s/js/jquery-ui.min.js"></script>


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
                       <input type=button value=%s
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit"
                       value=%s class="formbutton">

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
                        _("To:  "),  CFG_SITE_URL, (datetime.date.today() + datetime.timedelta(days=365)).strftime('%Y-%m-%d'),
                        _("Back"), _("Continue"))

        return out

    def tmpl_place_new_request_step3(self, ln=CFG_SITE_LANG):
        """
        Last step of the request procedure.
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_


        out += """
        <div class="bibcircbottom">
        <br />
        <br />
        <div class="infoboxsuccess">%s</div>
        <br />
        <br />
        <table class="bibcirctable">
        <td><input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1'"
        value='%s' class='formbutton'></td>
        </table>
        <br />
        <br />
        </div>

        """ % (_("A new request has been registered with success."),
               CFG_SITE_URL, _("Back to home"))

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

        @param infos: informations
        @type infos: list

        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        (book_title, book_year, book_author, book_isbn, book_editor) = book_information_from_MARC(int(recid))

        if book_isbn:
            book_cover = get_book_cover(book_isbn)
        else:
            book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)

        out = self.tmpl_infobox(infos, ln)

        out += _MENU_

        out += """
        <style type="text/css"> @import url("/img/tablesorter.css"); </style>
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
        <form name="step1_form1" action="%s/admin/bibcirculation/bibcirculationadmin.py/place_new_loan_step1" method="get" >
        <input type=hidden name=barcode value='%s'>
        <input type=hidden name=recid value='%s'>
        <table>

            """  % (CFG_SITE_URL, barcode, recid)

        if CFG_CERN_SITE == 1:

            out += """
                 <tr>
                   <td class="bibcirctableheader" align="center">Search user by

                   """

            if key == 'email':
                out += """
                   <input type="radio" name="key" value="ccid">ccid
                   <input type="radio" name="key" value="name">name
                   <input type="radio" name="key" value="email" checked>email
                   """

            elif key == 'name':
                out += """
                   <input type="radio" name="key" value="ccid">ccid
                   <input type="radio" name="key" value="name" checked>name
                   <input type="radio" name="key" value="email">email
                   """

            else:
                out += """
                   <input type="radio" name="key" value="ccid" checked>ccid
                   <input type="radio" name="key" value="name">name
                   <input type="radio" name="key" value="email">email
                   """

        else:
            out += """
                 <tr>
                   <td class="bibcirctableheader" align="center">Search borrower by

                   """

            if key == 'email':
                out += """
                   <input type="radio" name="key" value="id">id
                   <input type="radio" name="key" value="name">name
                   <input type="radio" name="key" value="email" checked>email
                   """

            elif key == 'id':
                out += """
                   <input type="radio" name="key" value="id" checked>id
                   <input type="radio" name="key" value="name">name
                   <input type="radio" name="key" value="email">email
                   """

            else:
                out += """
                   <input type="radio" name="key" value="id">id
                   <input type="radio" name="key" value="name" checked>name
                   <input type="radio" name="key" value="email">email
                   """

        out += """
                    <br><br>
                    </td>
                    </tr>
                    <tr>
                    <td align="center">
                    <input type="text" size="40" id="string" name="string"  value='%s' style='border: 1px solid #cfcfcf'>
                    </td>
                    </tr>
                    <tr>
                    <td align="center">
                    <br>
                    <input type="submit" value="Search" class="formbutton">
                    </td>
                    </tr>

                   </table>
          </form>

        """ % (string or '')
#<input type=hidden name=recid value='%s'>
        if result:
            out += """
            <br />
            <form name="step1_form2" action="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step3" method="get" >
            <input type=hidden name=barcode value='%s'>

            <table class="bibcirctable">
              <tr width="200">
                <td align="center">
                  <select name="user_info" size="8" style='border: 1px solid #cfcfcf; width:40%%'>

            """ % (CFG_SITE_URL, barcode)

            for (ccid, name, email, phone, address, mailbox) in result:
                out += """
                       <option value ="[\'%s\',\'%s\',\'%s\',\'%s\',\'%s\',\'%s\']">%s

                       """ % (ccid, name, email, phone, address, mailbox, name)

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

    def tmpl_place_new_loan_step2(self, barcode, recid, user_info, ln=CFG_SITE_LANG):
        """
        @param barcode: identify the item. Primary key of crcITEM.
        @type barcode: string

        @param recid: identify the record. Primary key of bibrec.
        @type recid: int

        @param user_info: user's informations
        @type user_info: tuple

        @param ln: language of the page
        """

        (book_title, book_year, book_author, book_isbn,
         book_editor) = book_information_from_MARC(int(recid))

        if book_isbn:
            book_cover = get_book_cover(book_isbn)
        else:
            book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)

        (ccid, name, email, phone, address, mailbox) = user_info.split(',')

        _ = gettext_set_language(ln)

        out = """
        """
        out += _MENU_

        out += """
            <style type="text/css"> @import url("/img/tablesorter.css"); </style>
            <div class="bibcircbottom">
            <form name="step2_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/place_new_loan_step3" method="get" >
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
                       _("Email"), email,
                       _("Phone"), phone,
                       _("Address"), address,
                       _("Mailbox"), mailbox)

        out += """

                <script type="text/javascript" language='JavaScript' src="%s/js/jquery-ui.min.js"></script>

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
                <input type="text" size="12" id="date_picker1" name="due_date" value="%s" style='border: 1px solid #cfcfcf'>
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
                    <td><textarea name='notes' rows="5" cols="57" style='border: 1px solid #cfcfcf'></textarea></td>
                  </tr>
                  <tr>
                    <td>This note will be associate to this new loan, not to the borrower.</td>
                  </tr>
                </table>
                <br />
                <br />
                <table class="bibcirctable">
                <tr>
                  <td>
                       <input type=button value=%s
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit"
                       value=%s class="formbutton">

                  </td>
                 </tr>
                </table>
                </form>
                <br />
                <br />
                </div>
                """ % (CFG_SITE_URL,
                       _("Loan information"),
                       _("Loan date"),  datetime.date.today().strftime('%Y-%m-%d'),
                       _("Due date"), CFG_SITE_URL, renew_loan_for_X_days(barcode),
                       _("Write notes"), _("Back"), _("Continue"))

        return out


    def tmpl_order_new_copy_step1(self, recid, list_of_vendors,
                                  libraries, ln=CFG_SITE_LANG):
        """
        @param recid: identify the record. Primary key of bibrec.
        @type recid: int

        @param list_of_vendors: list with all the vendores
        @type list_of_vendors: list

        @param libraries: all libraries
        @type libraries: list

        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = """
        """
        out += _MENU_

        (book_title, book_year, book_author, book_isbn, book_editor) = book_information_from_MARC(int(recid))

        if book_isbn:
            book_cover = get_book_cover(book_isbn)
        else:
            book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)

        out += """
           <style type="text/css"> @import url("/img/tablesorter.css"); </style>
           <script type="text/javascript" src="/js/jquery.validate.js"></script>
           <script>
             $(document).ready(function(){
               $('#order_new_copy_step1_form').validate();
             });
           </script>
           <style type="text/css">
           label { width: 10em; float: left; }
           label.error { float: none; color: red; padding-left: .5em; vertical-align: top; }
           p { clear: both; }
           .submit { margin-left: 12em; }
           em { font-weight: bold; padding-right: 1em; vertical-align: top; }
           </style>
           <form name="order_new_copy_step1_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/order_new_copy_step2" method="get" >
           <div class="bibcircbottom">
             <br />
             <table class="bibcirctable">
               <tr>
                 <td class="bibcirctableheader" width="10">%s</td>
               </tr>
               </table>
               <table class="bibcirctable">
                 <tr valign='top'>
                   <td width="400"><input type=hidden name=recid value='%s'>
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
                     <td class="bibcirccontent"><img style='border: 1px solid #cfcfcf' src="%s" alt="Book Cover"/></td>
                     </tr>
              </table>

           <br />

           """  % (CFG_SITE_URL,
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
                   book_isbn,
                   str(book_cover))

        out += """

        <script type="text/javascript" language='JavaScript' src="%s/js/jquery-ui.min.js"></script>

             <table class="bibcirctable">
                <tr>
                     <td class="bibcirctableheader">%s</td>
                </tr>
             </table>
             <table class="tablesortermedium" border="0" cellpadding="0" cellspacing="1">
             <tr>
               <th width="100">%s</th>
               <td>
                 <input class="required" type="text" size="20" name="barcode" style='border: 1px solid #cfcfcf' />
                 <em>*</em>
               </td>
             </tr>
             <tr>
               <th width="100">%s</th>
                 <td>
                   <select name="vendor_id"  style='border: 1px solid #cfcfcf'>

                """ % (CFG_SITE_URL,
                       _("Order details"), _("Barcode"),  _("Vendor"))

        for(vendor_id, name) in list_of_vendors:
            out +="""<option value ="%s">%s</option>""" % (vendor_id, name)

        today = datetime.date.today()
        gap = datetime.timedelta(days=14)
        more_2_weeks = (today + gap).strftime('%Y-%m-%d')

        out += """
                    </select>
                    </td>
                </tr>
                <tr>
                    <th width="100">%s</th>
                    <td>
                    <input type="text" style='border: 1px solid #cfcfcf' size=12 name="cost">
                      <select name="currency"  style='border: 1px solid #cfcfcf'>
                        <option value ="EUR">EUR</option>
                        <option value ="CHF">CHF</option>
                        <option value ="USD">USD</option>
                      </select>
                    </td>
                </tr>
                <tr>
                    <th width="100">%s</th>
                    <td>
                      <select name="status" style='border: 1px solid #cfcfcf'>
                          <option value ="ordered">ordered</option>
                          <option value ="cancelled">cancelled</option>
                          <option value ="not arrived">arrived</option>
                      </select>
                    </td>
                </tr>
                <tr>
                <th width="100">%s</th>
                    <td>
                        <script type="text/javascript">
                        $(function(){
                            $("#date_picker1").datepicker({dateFormat: 'yy-mm-dd', showOn: 'button', buttonImage: "%s/img/calendar.gif", buttonImageOnly: true});
                        });
                        </script>
                        <input type="text" size="12" id="date_picker1" name="order_date" value="%s" style='border: 1px solid #cfcfcf'>
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
                        <input type="text" size="12" id="date_picker2" name="expected_date" value="%s" style='border: 1px solid #cfcfcf'>

                    </td>
                </tr>
                <tr>
                  <th width="100">%s</th>
                  <td>
                    <select name="library_id" style='border: 1px solid #cfcfcf'>

                """ % (_("Price"), _("Status"),
                       _("Order date"), CFG_SITE_URL, today,
                       _("Expected date"), CFG_SITE_URL, more_2_weeks,
                       _("Library"))

        for(library_id, name) in libraries:
            out +="""<option value ="%s">%s</option>""" % (library_id, name)

        out += """
                    </select>
                    </td>
                </tr>
                <tr>
                   <th valign="top" width="100">%s</th>
                   <td><textarea name='notes' rows="6" cols="30" style='border: 1px solid #cfcfcf'></textarea></td>
                </tr>
             </table>
             <br />
             <table class="bibcirctable">
                <tr>
                  <td>
                       <input type=button value=%s
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit"
                       value=%s class="formbutton">

                  </td>
                 </tr>
             </table>
             </form>
             <br />
             <br />
             </div>
             """ % (_("Notes"), _("Back"), _("Continue"))

        return out



    def tmpl_order_new_copy_step2(self, order_info, ln=CFG_SITE_LANG):
        """
        @param order_info: order's informations
        @type order_info: tuple

        @param ln: language of the page
        """

        (recid, barcode, vendor_id, cost, currency, status,
         order_date, expected_date, library_id, notes) = order_info

        (book_title, book_year, book_author,
         book_isbn, book_editor) = book_information_from_MARC(int(recid))

        vendor_name = db.get_vendor_name(vendor_id)
        library_name = db.get_library_name(library_id)

        if book_isbn:
            book_cover = get_book_cover(book_isbn)
        else:
            book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)

        _ = gettext_set_language(ln)

        out = """
        """
        out += _MENU_

        out += """
            <div class="bibcircbottom">
            <style type="text/css"> @import url("/img/tablesorter.css"); </style>
            <form name="step2_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/order_new_copy_step3" method="get" >
                <input type=hidden name=order_info value="%s">
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
                     order_info,
                     _("Item details"),
                     _("Name"), book_title,
                     _("Author(s)"), book_author,
                     _("Year"), book_year,
                     _("Publisher"), book_editor,
                     _("ISBN"), book_isbn,
                     str(book_cover))

        out += """
              <br />
              <table class="bibcirctable">
                  <tr>
                     <td class="bibcirctableheader">%s</td>
                  </tr>
                </table>
              <table class="tablesortersmall" border="0" cellpadding="0" cellspacing="1">
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
                    <td>%s %s</td>
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
                    <td><i>%s</i></td>
                 </tr>
                </table>
                <br />
                <table class="bibcirctable">
                   <tr>
                    <td>
                       <input type=button value=%s
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit"
                       value=%s class="formbutton">

                    </td>
                   </tr>
                 </table>
               </form>
               <br />
               <br />
               </div>
               """ % (_("Order details"),
                      _("Barcode"), barcode,
                      _("Vendor"), vendor_name,
                      _("Price"), cost, currency,
                      _("Status"), status,
                      _("Order date"), order_date,
                      _("Expected date"), expected_date,
                      _("Library"), library_name,
                      _("Notes"), notes,
                      _("Back"), _("Continue"))


        return out


    def tmpl_order_new_copy_step3(self, ln=CFG_SITE_LANG):
        """
        Last step of the request procedure.

        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_


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
        <td><input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1'"
        value='%s' class='formbutton'></td>
        </table>
        <br />
        <br />
        </div>

        """ % (_("A new purchase has been registered with success."),
               CFG_SITE_URL, _("Back to home"))


        return out

    def tmpl_ordered_books(self, ordered_books, ln=CFG_SITE_LANG):
        """
        Display list with all ordered books.

        @param ordered_books: list with all the ordered books
        @type ordered_books: list
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_


        out += """
        <style type="text/css"> @import url("/img/tablesorter.css"); </style>
        <script src="/js/jquery.js" type="text/javascript"></script>
        <script src="/js/jquery.tablesorter.js" type="text/javascript"></script>
        <script type="text/javascript">
           $(document).ready(function() {
              $('#table_orders').tablesorter({widthFixed: true, widgets: ['zebra']})
            });
        </script>
        <div class="bibcircbottom">
        <br />
             <table id="table_orders" class="tablesorter" border="0" cellpadding="0" cellspacing="1">
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

         """% (_("Item"),
               _("Vendor"),
               _("Ordered date"),
               _("Price"),
               _("Status"),
               _("Expected date"),
               _("Notes"),
               _("Option(s)"))

        for (purchase_id, recid, vendor_id, ordered_date, expected_date, price, status, notes) in ordered_books:

            vendor_name = db.get_vendor_name(vendor_id)

            title_link = create_html_link(CFG_SITE_URL +
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_item_details',
                                          {'recid': recid, 'ln': ln},
                                          (book_title_from_MARC(recid)))


            no_notes_link = create_html_link(CFG_SITE_URL +
                                         '/admin/bibcirculation/bibcirculationadmin.py/get_purchase_notes',
                                         {'purchase_id': purchase_id},
                                         (_("No notes")))

            see_notes_link = create_html_link(CFG_SITE_URL +
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_purchase_notes',
                                          {'purchase_id': purchase_id},
                                          (_("See notes")))

            if notes == "":
                notes_link = no_notes_link
            else:
                notes_link = see_notes_link

            out += """
            <tr  onMouseOver="this.className='highlight'" onMouseOut="this.className='normal'">
                 <td class="bibcirccontent">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td align="center">
                   <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/ordered_books_details_step1?purchase_id=%s'" onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
                       value=%s class='bibcircbutton'>
                    </td>
            </tr>

            """ % (title_link, vendor_name, ordered_date,
                   price, status, expected_date, notes_link,
                   CFG_SITE_URL, purchase_id, _("select"))

        out += """
           </tbody>
           </table>
           <br />
           <br />
           </div>
        """

        return out

    def tmpl_purchase_notes(self, purchase_notes, purchase_id, ln=CFG_SITE_LANG):
        """
        @param purchase_notes: notes about a given purchase
        @type purchase_notes: dictionnary

        @param purchase_id: identify the purchase. Primary key of crcPURCHASE
        @type purchase_id: int
        """

        _ = gettext_set_language(ln)

        if not purchase_notes:
            purchase_notes = {}
        else:
            if looks_like_dictionary(purchase_notes):
                purchase_notes = eval(purchase_notes)
            else:
                purchase_notes = {}

        out = """ """

        out += _MENU_

        out +="""
            <div class="bibcircbottom">
            <form name="borrower_notes" action="%s/admin/bibcirculation/bibcirculationadmin.py/get_purchase_notes" method="get" >
            <input type=hidden name=purchase_id value='%s'>
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

            """ % (CFG_SITE_URL, purchase_id,
                   _("Notes about acquisition"))

        key_array = purchase_notes.keys()
        key_array.sort()

        for key in key_array:
            delete_note = create_html_link(CFG_SITE_URL +
                                           '/admin/bibcirculation/bibcirculationadmin.py/get_purchase_notes',
                                           {'delete_key': key, 'purchase_id': purchase_id, 'ln': ln},
                                           (_("[delete]")))

            out += """<tr class="bibcirccontent">
                        <td class="bibcircnotes" width="160" valign="top" align="center"><b>%s</b></td>
                        <td width="400"><i>%s</i></td>
                        <td width="65" align="center">%s</td>
                      </tr>

                      """ % (key, purchase_notes[key], delete_note)

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
                       <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/ordered_books'"
                       value=%s class='formbutton'>
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
               CFG_SITE_URL,
               _("Back"),
               _("Confirm"))

        return out

    def tmpl_register_ill_request_step0(self, result, infos, key, string, recid, ln=CFG_SITE_LANG):
        """
        @param result: borrower's information
        @type result: list

        @param infos: informations
        @type infos: list

        @param key: field (name, email, etc...)
        @param key: string

        @param string: pattern
        @type string: string

        @param recid: identify the record. Primary key of bibrec.
        @type recid: int

        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        (book_title, book_year, book_author, book_isbn, book_editor) = book_information_from_MARC(int(recid))

        if book_isbn:
            book_cover = get_book_cover(book_isbn)
        else:
            book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)

        out = self.tmpl_infobox(infos, ln)

        out += _MENU_

        out += """
        <style type="text/css"> @import url("/img/tablesorter.css"); </style>
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
                            str(book_cover))

        out += """
        <td valign='top' align='center'>
        <form name="step1_form1" action="%s/admin/bibcirculation/bibcirculationadmin.py/register_ill_request_step0" method="get" >
        <input type=hidden name=recid value='%s'>
        <table>

            """  % (CFG_SITE_URL, recid)

        if CFG_CERN_SITE == 1:

            out += """
                 <tr>
                   <td class="bibcirctableheader" align="center">Search user by

                   """

            if key == 'email':
                out += """
                   <input type="radio" name="key" value="ccid">ccid
                   <input type="radio" name="key" value="name">name
                   <input type="radio" name="key" value="email" checked>email
                   """

            elif key == 'name':
                out += """
                   <input type="radio" name="key" value="ccid">ccid
                   <input type="radio" name="key" value="name" checked>name
                   <input type="radio" name="key" value="email">email
                   """

            else:
                out += """
                   <input type="radio" name="key" value="ccid" checked>ccid
                   <input type="radio" name="key" value="name">name
                   <input type="radio" name="key" value="email">email
                   """

        else:
            out += """
                 <tr>
                   <td class="bibcirctableheader" align="center">Search borrower by

                   """

            if key == 'email':
                out += """
                   <input type="radio" name="key" value="id">id
                   <input type="radio" name="key" value="name">name
                   <input type="radio" name="key" value="email" checked>email
                   """

            elif key == 'id':
                out += """
                   <input type="radio" name="key" value="id" checked>id
                   <input type="radio" name="key" value="name">name
                   <input type="radio" name="key" value="email">email
                   """

            else:
                out += """
                   <input type="radio" name="key" value="id">id
                   <input type="radio" name="key" value="name" checked>name
                   <input type="radio" name="key" value="email">email
                   """

        out += """
                    <br><br>
                    </td>
                    </tr>
                    <tr>
                    <td align="center">
                    <input type="text" size="40" id="string" name="string"  value='%s' style='border: 1px solid #cfcfcf'>
                    </td>
                    </tr>
                    <tr>
                    <td align="center">
                    <br>
                    <input type="submit" value="Search" class="formbutton">
                    </td>
                    </tr>

                   </table>
          </form>

        """ % (string or '')

        if result:
            out += """
            <br />
            <form name="step1_form2" action="%s/admin/bibcirculation/bibcirculationadmin.py/register_ill_request_step1" method="get" >
            <input type=hidden name=recid value='%s'>
            <table class="bibcirctable">
              <tr width="200">
                <td align="center">
                  <select name="user_info" size="8" style='border: 1px solid #cfcfcf; width:40%%'>

            """ % (CFG_SITE_URL, recid)

            for (ccid, name, email, phone, address, mailbox) in result:
                out += """
                       <option value ='%s,%s,%s,%s,%s,%s'>%s

                       """ % (ccid, name, email, phone, address, mailbox, name)

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

    def tmpl_register_ill_request_step1(self, recid, user_info, ln=CFG_SITE_LANG):
        """
        @param recid: identify the record. Primary key of bibrec.
        @type recid: int

        @param user_info: user's informations
        @type user_info: tuple
        """

        (ccid, name, email, phone, address, mailbox) = user_info.split(',')

        _ = gettext_set_language(ln)

        out = """  """

        out += _MENU_

        (book_title, book_year, book_author, book_isbn, book_editor) = book_information_from_MARC(int(recid))

        out += """
           <style type="text/css"> @import url("/img/tablesorter.css"); </style>
           <form name="update_item_info_step4_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/register_ill_request_step2" method="get" >
           <div class="bibcircbottom" align="center">
                <br />
                     <table class="bibcirctable">
                          <tr align="center">
                               <td class="bibcirctableheader" width="10">%s</td>
                          </tr>
                </table>
                    <input type=hidden name=recid value='%s'>
                    <input type=hidden name=user_info value="%s">
                    <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">
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
                     </table>
           <br />

           """  % (CFG_SITE_URL,
                   _("Item details"),
                   recid, user_info,
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
                <script type="text/javascript" language='JavaScript' src="/jsCalendar/calendar.js"></script>
                <script type="text/javascript" language='JavaScript' src="/jsCalendar/calendar-setup.js"></script>
                <script type="text/javascript" language='JavaScript' src="/jsCalendar/calendar-en.js"></script>
                <style type="text/css"> @import url("/jsCalendar/calendar-blue.css"); </style>


              <br />
              <table>
                <tr>
                  <td class="bibcirctableheader">%s</td>
                </tr>
              </table>
              <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">
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
                </table>
                <br />
                <table>
                <tr>
                  <td class="bibcirctableheader">%s</td>
                </tr>
              </table>
                <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">
                <tr>
                <th width="150">%s</th>
                <td class="bibcirccontent">
                       <input type="text" size="12" id="%s" name="period_of_interest_from" value="" style='border: 1px solid #cfcfcf'>
                       <img src="/jsCalendar/jsCalendar.gif" alt="select period of interest" id="%s"
                       onmouseover="this.style.background='red';" onmouseout="this.style.background=''">
                       <script type="text/javascript" language='JavaScript'>
                       Calendar.setup({
                           inputField     :    '%s',
                           ifFormat       :    '%%Y-%%m-%%d',
                           button         :    '%s'
                           });
                       </script>
                    </td>
                </tr>
                <tr>
                <th width="150">%s</th>
                <td class="bibcirccontent">
                       <input type="text" size="12" id="%s" name="period_of_interest_to" value="" style='border: 1px solid #cfcfcf'>
                       <img src="/jsCalendar/jsCalendar.gif" alt="select period of interest" id="%s"
                       onmouseover="this.style.background='red';" onmouseout="this.style.background=''">
                       <script type="text/javascript" language='JavaScript'>
                       Calendar.setup({
                           inputField     :    '%s',
                           ifFormat       :    '%%Y-%%m-%%d',
                           button         :    '%s'
                           });
                       </script>
                    </td>
                </tr>
                <tr>
                   <th valign="top" width="150">%s</th>
                   <td><textarea name='notes' rows="6" cols="30"
                   style='border: 1px solid #cfcfcf'></textarea></td>
                </tr>
                </table>
                <table class="bibcirctable">
                  <tr align="center">
                    <td>
                    <input name="only_edition" type="checkbox" value="Yes" />%s</td>
                  </tr>
                </table>
                </td>
                <td>
                """ % (_("Borrower details"),
                       _("ID"), ccid,
                       _("Name"), name,
                       _("Email"), email,
                       _("Phone"), phone,
                       _("Address"), address,
                       _("Mailbox"), mailbox,
                       _("ILL request details"),
                       _("Period of interest - From"), "period_of_interest_from",
                       "jsCal3", "period_of_interest_from", "jsCal3",
                       _("Period of interest - To"), "period_of_interest_to",
                       "jsCal4", "period_of_interest_to", "jsCal4",
                       _("Additional comments"),
                       _("Borrower wants only this edition?"))

        out += """

             <table>
             <br />
             <table class="bibcirctable">
                <tr align="center">
                  <td>
                       <input type=button value=%s
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit"
                       value=%s class="formbutton">

                  </td>
                 </tr>
             </table>
             </form>
             <br />
             <br />
             </div>
             """ % (_("Back"), _("Continue"))

        return out

    def tmpl_register_ill_request_step2(self, user_info, request_info, ln=CFG_SITE_LANG):
        """
        @param user_info: user's informations
        @type user_info: tuple

        @param request_info: request's informations
        @type request_info: tuple

        @param ln: language of the page
        """

        (recid, period_of_interest_from, period_of_interest_to,
         notes, only_edition) = request_info

        (book_title, book_year, book_author,
         book_isbn, book_editor) = book_information_from_MARC(int(recid))

        (borrower_id, name, email, phone, address, mailbox) = user_info

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_

        out += """
        <style type="text/css"> @import url("/img/tablesorter.css"); </style>
        <div class=bibcircbottom align="center">
        <br />
        <br />
         <form name="step1_form1" action="%s/admin/bibcirculation/bibcirculationadmin.py/register_ill_request_step3" method="get" >
                 <table>
                   <tr align="center">
                     <td class="bibcirctableheader">%s</td>
                     <input type=hidden name=borrower_id value="%s">
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
                      </table>
                      <table>
                         <tr align="center">
                           <td class="bibcirctableheader">%s</td>
                           <input type=hidden name=request_info value="%s">
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
                      </table>
                      <table>
                         <tr align="center">
                           <td class="bibcirctableheader">%s</td>
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
                      </table>

                      """ % (CFG_SITE_URL,
                             _("Item details"), borrower_id,
                             _("Name"), book_title,
                             _("Author(s)"), book_author,
                             _("Year"), book_year,
                             _("Publisher"), book_editor,
                             _("ISBN"), book_isbn,
                             _("ILL request details"), request_info,
                             _("Period of interest - From"), period_of_interest_from,
                             _("Period of interest - To"), period_of_interest_to,
                             _("Additional comments"), notes,
                             _("Only this edition"), only_edition,
                             _("Borrower details"),
                             _("ID"), borrower_id,
                             _("Name"), name,
                             _("Email"), email,
                             _("Phone"), phone,
                             _("Address"), address,
                             _("Mailbox"), mailbox)

        out += """<br />
                  <table class="bibcirctable">
                    <tr align="center">
                      <td>
                        <input type=button value=%s
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit"
                       value=%s class="formbutton">
                      </td>
                    </tr>
                </table>""" % (_("Back"), _("Continue"))


        return out

        (_ccid, name, email, phone, address, mailbox) = user_info.split(',')



        return out

    def tmpl_register_ill_request_step3(self, ln=CFG_SITE_LANG):
        """
        Last step of the request procedure.

        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_


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
        <td><input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1'"
        value='%s' class='formbutton'></td>
        </table>
        <br />
        <br />
        </div>

        """ % (_("A new ILL request has been registered with success."),
               CFG_SITE_URL, _("Back to home"))


        return out


    def tmpl_ill_request_with_recid(self, recid, infos, ln=CFG_SITE_LANG):
        """
        @param recid: identify the record. Primary key of bibrec.
        @type recid: int

        @param infos: informations
        @type infos: list
        """

        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        (book_title, book_year, book_author, book_isbn, book_editor) = book_information_from_MARC(int(recid))

        today = datetime.date.today()
        within_six_months = (datetime.date.today() + datetime.timedelta(days=182)).strftime('%Y-%m-%d')

        out += """
           <div align="center">
           <style type="text/css"> @import url("/img/tablesorter.css"); </style>
           <form name="update_item_info_step4_form" action="%s/%s/%s/holdings/ill_register_request_with_recid" method="get" >
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

           """  % (CFG_SITE_URL, CFG_SITE_RECORD, recid,
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

        conditions_link = """<a href="http://library.web.cern.ch/library/Library/ill_faq.html" target="_blank">conditions</a>"""

        out += """
            <style type="text/css"> @import url("/img/tablesorter.css"); </style>
            <script type="text/javascript" language='JavaScript' src="%s/js/jquery-ui.min.js"></script>
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
                       <input type=button value=%s
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit"
                       value=%s class="formbutton">

                  </td>
                 </tr>
             </table>
             </form>
             <br />
             <br />
             </div>
             """ % (_("ILL request details"),
                    _("Period of interest - From"), CFG_SITE_URL, today,
                    _("Period of interest - To"),   CFG_SITE_URL, within_six_months,
                    _("Additional comments"),
                    _("I accept the %s of the service in particular the return of books in due time." % (conditions_link)),
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
        <td class="bibcirccontent" width="30">%s<a href="%s">%s</a>%s</td>
        </tr>
        </table>
        <br /> <br />
        <table class="bibcirctable">
        <td><input type=button onClick="location.href='%s'" value='%s' class='formbutton'></td>
        </table>
        <br /> <br />
        """ % (message,
               _("You can see your loans "),
               CFG_SITE_URL + '/yourloans/display',
               _("here"),
               _("."),
               CFG_SITE_URL,
               _("Back to home"))

        return out


    def tmpl_display_ill_form(self, infos, ln=CFG_SITE_LANG):
        """
        @param infos: informations
        @type infos: list
        """

        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)


        out += """
           <div align="center">
           <style type="text/css"> @import url("/img/tablesorter.css"); </style>
           <form name="display_ill_form" action="%s/ill/register_request" method="get">
                <table class="bibcirctable">
                  <tr align="center">
                    <td class="bibcirctableheader" width="10">%s</td>
                  </tr>
                </table>
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

           """  % (CFG_SITE_URL,
                   _("Item details"),
                   _("Title"),
                   _("Author(s)"),
                   _("Place"),
                   _("Publisher"),
                   _("Year"),
                   _("Edition"),
                   _("ISBN"))



        conditions_link = """<a href="http://library.web.cern.ch/library/Library/ill_faq.html" target="_blank">conditions</a>"""

        out += """
        <script type="text/javascript" language='JavaScript' src="/jsCalendar/calendar.js"></script>
        <script type="text/javascript" language='JavaScript' src="/jsCalendar/calendar-setup.js"></script>
        <script type="text/javascript" language='JavaScript' src="/jsCalendar/calendar-en.js"></script>
        <style type="text/css"> @import url("/jsCalendar/calendar-blue.css"); </style>

             <table class="bibcirctable">
                <tr align="center">
                     <td class="bibcirctableheader">%s</td>
                </tr>
             </table>
             <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">
               <tr>
                <th width="150">%s</th>
                <td>
                       <input type="text" size="12" id="%s" name="period_of_interest_from"
                       value="" style='border: 1px solid #cfcfcf'>
                       <img src="/jsCalendar/jsCalendar.gif" alt="select period of interest" id="%s"
                       onmouseover="this.style.background='red';" onmouseout="this.style.background=''"
                       >
                       <script type="text/javascript" language='JavaScript'>
                       Calendar.setup({
                           inputField     :    '%s',
                           ifFormat       :    '%%Y-%%m-%%d',
                           button         :    '%s'
                           });
                       </script>
                    </td>
                </tr>
                <tr>
                <th width="150">%s</th>
                <td>
                       <input type="text" size="12" id="%s" name="period_of_interest_to"
                       value="" style='border: 1px solid #cfcfcf'>
                       <img src="/jsCalendar/jsCalendar.gif" alt="select period of interest" id="%s"
                       onmouseover="this.style.background='red';" onmouseout="this.style.background=''"
                       >
                       <script type="text/javascript" language='JavaScript'>
                       Calendar.setup({
                           inputField     :    '%s',
                           ifFormat       :    '%%Y-%%m-%%d',
                           button         :    '%s'
                           });
                       </script>
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
                    <input name="only_edition" type="checkbox" value="True" />%s</td>
                </tr>
             </table>
             <br />
             <table class="bibcirctable">
                <tr align="center">
                  <td>
                       <input type=button value=%s
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit"
                       value=%s class="formbutton">

                  </td>
                 </tr>
             </table>
             </form>
             <br />
             <br />
             </div>
             """ % (_("ILL request details"), _("Period of interest - From"), "period_of_interest_from",
                    "jsCal1", "period_of_interest_from", "jsCal1",
                    _("Period of interest - To"), "period_of_interest_to", "jsCal2", "period_of_interest_to", "jsCal2",
                    _("Additional comments"),
                    _("I accept the %s of the service in particular the return of books in due time." % (conditions_link)),
                    _("I want this edition only."),
                    _("Back"), _("Continue"))

        return out

    def tmpl_list_ill_request(self, ill_req, ln=CFG_SITE_LANG):
        """
        @param ill_req: informations about a given ILL request
        @type ill_req: tuple
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_

        out += """
        <style type="text/css"> @import url("/img/tablesorter.css"); </style>
        <script src="/js/jquery.js" type="text/javascript"></script>
        <script src="/js/jquery.tablesorter.js" type="text/javascript"></script>
        <script type="text/javascript">
        $(document).ready(function() {
          $('#table_ill').tablesorter({widthFixed: true, widgets: ['zebra']})
        });
        </script>
         <div class="bibcircbottom">
           <br />
             <table id="table_ill" class="tablesorter" border="0" cellpadding="0" cellspacing="1">
             <thead>
                    <tr>
                       <th width="200">%s</th>
                       <th width="300">%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                       <th>%s</th>
                    </tr>
             </thead>
             <tbody>
            """% (_("Borrower"),
                  _("Item"),
                  _("Supplier"),
                  _("Status"),
                  _("ID"),
                  _("Interest from"),
                  _("Type"),
                  _("Option(s)"))



        for (ill_request_id, borrower_id, borrower_name, library_id,
             ill_status, period_from, _period_to, item_info, request_type) in ill_req:

            borrower_link = create_html_link(CFG_SITE_URL +
                                             '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_details',
                                             {'borrower_id': borrower_id, 'ln': ln},
                                             (borrower_name))

            if library_id:
                library_name = db.get_library_name(library_id)
            else:
                library_name = '-'

            if looks_like_dictionary(item_info):
                item_info = eval(item_info)
            else:
                item_info = {}

            try:
                title_link = create_html_link(CFG_SITE_URL +
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_item_details',
                                          {'recid': item_info['recid'], 'ln': ln},
                                          (book_title_from_MARC(int(item_info['recid']))))
            except KeyError:
                if request_type == 'book':
                    title_link = item_info['title']
                else:
                    title_link = item_info['periodical_title']


            out += """
                   <tr>
                    <td class="bibcirccontent">%s</td>
                    <td class="bibcirccontent">%s</td>
                    <td class="bibcirccontent">%s</td>
                    <td class="bibcirccontent">%s</td>
                    <td class="bibcirccontent">%s</td>
                    <td class="bibcirccontent">%s</td>
                    <td class="bibcirccontent">%s</td>
                    <td align="center">
                       <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/ill_request_details_step1?ill_request_id=%s'" onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
                       value=%s class='bibcircbutton'>
                    </td>
                   </tr>

                    """ % (borrower_link, title_link, library_name, ill_status,ill_request_id,
                           period_from, request_type, CFG_SITE_URL, ill_request_id, _('select'))


        out += """
           </tbody>
          </table>
         </div>
        """

        return out

    def tmpl_ill_request_details_step1(self, ill_request_id, ill_request_details, libraries, ill_request_borrower_details,ln=CFG_SITE_LANG):

        """
        @param ill_request_id: identify the ILL request. Primary key of crcILLREQUEST
        @type ill_request_id: int

        @param ill_req_details: informations about a given ILL request
        @type ill_req_details: tuple

        @param libraries: list of libraries
        @type libraries: list

        @param ill_status: status of an ILL request
        @type ill_status: string

        @param ill_request_borrower_details: borrower's informations
        @type ill_request_borrower_details: tuple
        """

        _ = gettext_set_language(ln)

        out = _MENU_

        out += """
            <style type="text/css"> @import url("/img/tablesorter.css"); </style>
            <script type="text/javascript" language='JavaScript' src="%s/js/jquery-ui.min.js"></script>
            """% (CFG_SITE_URL)

        (_borrower_id, borrower_name, borrower_email, borrower_mailbox,
         period_from, period_to, item_info, borrower_comments, only_this_edition, request_type) = ill_request_borrower_details

        (library_id, request_date, expected_date, arrival_date, due_date, return_date,
         cost, barcode, library_notes, ill_status) = ill_request_details

        if cost:
            (value, currency) = cost.split()
        else:
            (value, currency) = (0, 'EUR')

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
        within_a_week  = (datetime.date.today() + datetime.timedelta(days=7)).strftime('%Y-%m-%d')
        within_a_month = (datetime.date.today() + datetime.timedelta(days=30)).strftime('%Y-%m-%d')


        notes=''
        for key in key_array:
            delete_note = create_html_link(CFG_SITE_URL +
                                           '/admin/bibcirculation/bibcirculationadmin.py/ill_request_details_step1',
                                           {'delete_key': key, 'ill_request_id': ill_request_id, 'ln': ln},
                                           (_("[delete]")))

            notes += """<tr class="bibcirccontent">
                            <td class="bibcircnotes" width="160" valign="top" align="center"><b>%s</b></td>
                            <td width="400"><i>%s</i></td>
                            <td width="65" align="center">%s</td>
                        </tr>

                     """ % (key, previous_library_notes[key], delete_note)

        if library_id:
            library_name = db.get_library_name(library_id)
        else:
            library_name = '-'

        try:
            (book_title, book_year, book_author, book_isbn, book_editor) = book_information_from_MARC(int(item_info['recid']))

            if book_isbn:
                book_cover = get_book_cover(book_isbn)
            else:
                book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)

            out += """
            <form name="ill_req_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/ill_request_details_step2" method="get" >
            <div class="bibcircbottom">
            <input type=hidden name=ill_request_id value=%s>
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
                   <td class="bibcirccontent"><img style='border: 1px solid #cfcfcf' src="%s" alt="Book Cover"/></td>
                 </tr>
              </table>
              <br />
              """  % (CFG_SITE_URL,
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
                      str(book_cover))

        except KeyError:
            try:
                book_cover = get_book_cover(item_info['isbn'])
            except KeyError:
                book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)

            f=open("/tmp/item_info",'w')
            f.write(str(item_info)+'\n')
            f.close()
            if str(request_type) == 'book':
                out += """
                <style type="text/css"> @import url("/img/tablesorter.css"); </style>
                <form name="ill_req_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/ill_request_details_step2" method="get" >
                   <div class="bibcircbottom">
                   <input type=hidden name=ill_request_id value=%s>
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
                         <tr>
                            <th width="100">%s</th>
                            <td>%s</td>
                         </tr>
                        </table>
                      </td>
                        <td class="bibcirccontent"><img style='border: 1px solid #cfcfcf' src="%s" alt="Book Cover"/></td>
                      </tr>
                  </table>
                  <br />

                  """  % (CFG_SITE_URL,
                          ill_request_id,
                          _("Item details"),
                          _("Title"),
                          item_info['title'],
                          _("Author(s)"),
                          item_info['authors'],
                          _("Place"),
                          item_info['place'],
                          _("Publisher"),
                          item_info['publisher'],
                          _("Year"),
                          item_info['year'],
                          _("Edition"),
                          item_info['edition'],
                          _("ISBN"),
                          item_info['isbn'],
                          str(book_cover))

            # for articles
            elif str(request_type) == 'article':

                out += """
                <style type="text/css"> @import url("/img/tablesorter.css"); </style>
                <form name="ill_req_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/ill_request_details_step2" method="get" >
                   <div class="bibcircbottom">
                   <input type=hidden name=ill_request_id value=%s>
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
                        <td class="bibcirccontent"><img style='border: 1px solid #cfcfcf' src="%s" alt="Book Cover"/></td>
                      </tr>
                  </table>
                  <br />

                  """  % (CFG_SITE_URL,
                          ill_request_id,
                          _("Item details"),
                          _("Periodical Title"),
                          item_info['periodical_title'],
                          _("Article Title"),
                          item_info['title'],
                          _("Author(s)"),
                          item_info['authors'],
                          _("Volume, Issue, Page"),
                          item_info['volume'],
                          _("ISSN"),
                          item_info['issn'],
                          _("Place"),
                          item_info['place'],
                          _("Publisher"),
                          item_info['publisher'],
                          _("Year"),
                          item_info['year'],
                          str(book_cover))
            else:
                out+= """aqui falta algo, no?"""

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


#### NEW ####
        if ill_status == 'new' or ill_status == None or ill_status == '':
            if request_type == 'book':
                out += """
                          <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
                            <tr>
                                <input type=hidden name=new_status value="new">
                              <th width="100">%s</th>
                              <td>
                                <select style='border: 1px solid #cfcfcf' onchange="location = this.options[this.selectedIndex].value;">
                                  <option value ="ill_request_details_step1?ill_request_id=%s&new_status=new" selected>
                                    New
                                  </option>
                                  <option value ="ill_request_details_step1?ill_request_id=%s&new_status=requested">
                                    Requested
                                  </option>
                                  <option value ="ill_request_details_step1?ill_request_id=%s&new_status=on loan">
                                    On loan
                                  </option>
                                  <option value ="ill_request_details_step1?ill_request_id=%s&new_status=returned">
                                    Returned
                                  </option>
                                </select>
                              </td>
                            </tr>
                            <tr>
                              <th width="150">%s</th>
                              <td>%s</td>
                            </tr>
                            <tr>
                              <th width="100" valign="top">%s</th>
                              <td>
                                <table class="bibcircnotes"> """ % (_("Status"), ill_request_id, ill_request_id,
                                                                    ill_request_id, ill_request_id, _("ILL request ID"), ill_request_id, _("Previous notes"))
            if request_type == 'article':
                out += """
                      <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
                        <tr>
                            <input type=hidden name=new_status value="new">
                          <th width="100">%s</th>
                          <td>
                            <select style='border: 1px solid #cfcfcf' onchange="location = this.options[this.selectedIndex].value;">
                              <option value ="ill_request_details_step1?ill_request_id=%s&new_status=new" selected>
                                New
                              </option>
                              <option value ="ill_request_details_step1?ill_request_id=%s&new_status=requested">
                                Requested
                              </option>
                              <option value ="ill_request_details_step1?ill_request_id=%s&new_status=received">
                                Received
                              </option>
                            </select>
                          </td>
                        </tr>
                        <tr>
                          <th width="150">%s</th>
                          <td>%s</td>
                        </tr>
                        <tr>
                          <th width="100" valign="top">%s</th>
                          <td>
                            <table class="bibcircnotes"> """ % (_("Status"), ill_request_id, ill_request_id,
                                                                ill_request_id, _("ILL request ID"), ill_request_id, _("Previous notes"))


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

############# REQUESTED ##############
        elif ill_status == 'requested':

            if request_type == 'book':
                out += """
                          <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
                            <tr>
                            <input type=hidden name=new_status value="requested">
                              <th width="150">%s</th>
                              <td class="bibcirccontent">
                                <select style='border: 1px solid #cfcfcf' onchange="location = this.options[this.selectedIndex].value;">
                                  <option value ="ill_request_details_step1?ill_request_id=%s&new_status=new">
                                    New
                                  </option>
                                  <option value ="ill_request_details_step1?ill_request_id=%s&new_status=requested" selected>
                                    Requested
                                  </option>
                                  <option value ="ill_request_details_step1?ill_request_id=%s&new_status=on loan">
                                    On loan
                                  </option>
                                  <option value ="ill_request_details_step1?ill_request_id=%s&new_status=returned">
                                    Returned
                                  </option>
                                </select>
                              </td>
                            </tr>
                            <tr>
                              <th width="150">%s</th>
                              <td class="bibcirccontent">%s</td>
                            </tr>
                            <tr>
                              <th width="150">%s</th>
                              <td class="bibcirccontent">
                                <select name="library_id"  style='border: 1px solid #cfcfcf'>

                            """ % (_("Status"), ill_request_id, ill_request_id,
                                   ill_request_id, ill_request_id, _("ILL request ID"), ill_request_id,
                                   _("Library/Supplier"))
            if request_type == 'article':
                out += """
                          <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
                            <tr>
                            <input type=hidden name=new_status value="requested">
                              <th width="150">%s</th>
                              <td class="bibcirccontent">
                                <select style='border: 1px solid #cfcfcf' onchange="location = this.options[this.selectedIndex].value;">
                                  <option value ="ill_request_details_step1?ill_request_id=%s&new_status=new">
                                    New
                                  </option>
                                  <option value ="ill_request_details_step1?ill_request_id=%s&new_status=requested" selected>
                                    Requested
                                  </option>
                                  <option value ="ill_request_details_step1?ill_request_id=%s&new_status=received">
                                    Received
                                  </option>
                                </select>
                              </td>
                            </tr>
                            <tr>
                              <th width="150">%s</th>
                              <td class="bibcirccontent">%s</td>
                            </tr>
                            <tr>
                              <th width="150">%s</th>
                              <td class="bibcirccontent">
                                <select name="library_id"  style='border: 1px solid #cfcfcf'>

                            """ % (_("Status"), ill_request_id, ill_request_id,
                                   ill_request_id, _("ILL request ID"), ill_request_id,
                                   _("Library/Supplier"))

            for(library_id, name) in libraries:
                out += """<option value ="%s">%s</option>""" % (library_id, name)

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
                        <input type="text" size="10" id="date_picker1" name="request_date" value="%s" style='border: 1px solid #cfcfcf'>

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
                        <input type="text" size="10" id="date_picker2" name="expected_date" value="%s" style='border: 1px solid #cfcfcf'>

                      </td>
                    </tr>
                    <tr>
                      <th width="100">%s</th>
                      <td class="bibcirccontent">
                        <input type="text" size="12" name="cost" value="%s" style='border: 1px solid #cfcfcf'>
                        <select name="currency"  style='border: 1px solid #cfcfcf'>

                        """ % (_("Request date"),
                               CFG_SITE_URL, today,
                               _("Expected date"),
                               CFG_SITE_URL, within_a_week,
                               _("Cost"), value)


            if currency == 'EUR':
                out += """
                <option value="EUR" selected>EUR</option>
                <option value="CHF">CHF</option>
                <option value="USD">USD</option> """

            elif currency == 'CHF':
                out += """
                <option value="EUR">EUR</option>
                <option value="CHF" selected>CHF</option>
                <option value="USD">USD</option> """

            else:
                out +="""
                <option value="EUR">EUR</option>
                <option value="CHF">CHF</option>
                <option value="USD" selected>USD</option> """

            out += """
                        </select>
                      </td>
                    </tr>
                    <tr>
                      <th width="100">%s</th>
                      <td class="bibcirccontent"><input type="text" size="12" name="barcode" value="%s" style='border: 1px solid #cfcfcf'>
                      </td>
                    </tr>
                    <tr>
                          <th width="100" valign="top">%s</th>
                          <td>
                            <table class="bibcircnotes"> """  %(_("Barcode"), barcode or 'No barcode asociated',
                                                                _("Previous notes"))

            out += notes

            out += """
                            </table>
                          </td>
                        </tr>
                    <tr>
                       <th valign="top" width="150">%s</th>
                       <td><textarea name='library_notes' rows="6" cols="74" style='border: 1px solid #cfcfcf'></textarea></td>
                     </tr>
                   </table>
                 </td>
               </tr>
             </table>

                      """ % (_("Library notes"))

##### ON LOAN ##############
        elif ill_status == 'on loan':

            out += """
                      <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
                        <tr>
                        <input type=hidden name=new_status value="on loan">
                          <th width="100">%s</th>
                          <td class="bibcirccontent">
                            <select style='border: 1px solid #cfcfcf' onchange="location = this.options[this.selectedIndex].value;">
                              <option value ="ill_request_details_step1?ill_request_id=%s&new_status=new">
                                New
                              </option>
                              <option value ="ill_request_details_step1?ill_request_id=%s&new_status=requested">
                                Requested
                              </option>
                              <option value ="ill_request_details_step1?ill_request_id=%s&new_status=on loan" selected>
                                On loan
                              </option>
                              <option value ="ill_request_details_step1?ill_request_id=%s&new_status=returned">
                                Returned
                              </option>
                            </select>
                          </td>
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

                    """ % (_("Status"), ill_request_id, ill_request_id,
                            ill_request_id, ill_request_id, _("ILL request ID"), ill_request_id,
                            _("Library"), library_name,
                            _("Request date"), request_date, _("Expected date"),
                            expected_date)

            if str(arrival_date)=='0000-00-00':
                date1=today
            else:
                date1=arrival_date

            if str(due_date)=='0000-00-00':
                date2=within_a_month
            else:
                date2=due_date


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
                      </td>
                    </tr>
                """ % (_("Arrival date"), CFG_SITE_URL, date1, _("Due date"), CFG_SITE_URL, date2, request_date, expected_date)

            out += """
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent"><input type="text" size="12" name="cost" value="%s" style='border: 1px solid #cfcfcf'>
                            <select name="currency"  style='border: 1px solid #cfcfcf'>

                    """  % (_("Cost"), value)

            if currency == 'EUR':
                out += """
                <option value="EUR" selected>EUR</option>
                <option value="CHF">CHF</option>
                <option value="USD">USD</option> """

            elif currency == 'CHF':
                out += """
                <option value="EUR">EUR</option>
                <option value="CHF" selected>CHF</option>
                <option value="USD">USD</option> """

            else:
                out +="""
                <option value="EUR">EUR</option>
                <option value="CHF">CHF</option>
                <option value="USD" selected>USD</option> """

            out += """
                            </select>
                          </td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent"><input type="text" size="12" name="barcode" value="%s" style='border: 1px solid #cfcfcf'>
                        </tr>
                        <tr>
                          <th width="100" valign="top">%s</th>
                          <td>
                            <table class="bibcircnotes"> """ % (_("Barcoce"), barcode, _("Previous notes"))

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
        elif ill_status == 'returned':

            out += """
                      <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
                        <tr>
                        <input type=hidden name=new_status value="returned">
                          <th width="100">%s</th>
                          <td class="bibcirccontent">
                            <select style='border: 1px solid #cfcfcf' onchange="location = this.options[this.selectedIndex].value;">
                              <option value ="ill_request_details_step1?ill_request_id=%s&new_status=new">
                                New
                              </option>
                              <option value ="ill_request_details_step1?ill_request_id=%s&new_status=requested">
                                Requested
                              </option>
                              <option value ="ill_request_details_step1?ill_request_id=%s&new_status=on loan">
                                On loan
                              </option>
                              <option value ="ill_request_details_step1?ill_request_id=%s&new_status=returned" selected>
                                Returned
                              </option>
                            </select>
                          </td>
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
                          <td class="bibcirccontent">%s</td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent">
                            <script type="text/javascript">
                                $(function() {
                                    $("#date_picker1").datepicker({dateFormat: 'yy-mm-dd', showOn: 'button', buttonImage: "%s/img/calendar.gif", buttonImageOnly: true});
                                });
                            </script>
                            <input type="text" size="10" id="date_picker1" name="return_date" value="%s" style='border: 1px solid #cfcfcf'>
                            <input type="hidden" name="request_date" value="%s">
                            <input type="hidden" name="expected_date" value="%s">
                            <input type="hidden" name="arrival_date" value="%s">
                            <input type="hidden" name="due_date" value="%s">
                          </td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent"><input type="text" size="12" name="cost" value="%s" style='border: 1px solid #cfcfcf'>
                            <select name="currency"  style='border: 1px solid #cfcfcf'>

                            """  % ( _("Status"), ill_request_id,ill_request_id,ill_request_id,ill_request_id, _("ILL request ID"), ill_request_id,
                                    _("Library"), library_name,
                                    _("Request date"), request_date, _("Expected date"), expected_date,
                                    _("Arrival date"), arrival_date, _("Due date"), due_date,
                                    _("Return date"), CFG_SITE_URL, return_date,
                                    request_date, expected_date,arrival_date,due_date,
                                    _("Cost"), value)


            if currency == 'EUR':
                out += """
                <option value="EUR" selected>EUR</option>
                <option value="CHF">CHF</option>
                <option value="USD">USD</option> """

            elif currency == 'CHF':
                out += """
                <option value="EUR">EUR</option>
                <option value="CHF" selected>CHF</option>
                <option value="USD">USD</option> """

            else:
                out +="""
                <option value="EUR">EUR</option>
                <option value="CHF">CHF</option>
                <option value="USD" selected>USD</option> """

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
                            <table class="bibcircnotes"> """ % (_("Barcode"), barcode, _("Previous notes"))

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

##### RECEIVED ##############
        elif ill_status == 'received':
            if str(arrival_date)=='0000-00-00':
                date1=today
            else:
                date1=arrival_date
            out += """
                      <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
                        <tr>
                        <input type=hidden name=new_status value="received">
                          <th width="100">%s</th>
                          <td class="bibcirccontent">
                            <select style='border: 1px solid #cfcfcf' onchange="location = this.options[this.selectedIndex].value;">
                              <option value ="ill_request_details_step1?ill_request_id=%s&new_status=new">
                                New
                              </option>
                              <option value ="ill_request_details_step1?ill_request_id=%s&new_status=requested">
                                Requested
                              </option>
                              <option value ="ill_request_details_step1?ill_request_id=%s&new_status=received" selected>
                                Received
                              </option>
                            </select>
                          </td>
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
                                    $("#date_picker1").datepicker({dateFormat: 'yy-mm-dd', showOn: 'button', buttonImage: "%s/img/calendar.gif", buttonImageOnly: true});
                                });
                            </script>
                            <input type="text" size="10" id="date_picker1" name="arrival_date" value="%s" style='border: 1px solid #cfcfcf'>
                            <input type="hidden" name="request_date" value="%s">
                            <input type="hidden" name="expected_date" value="%s">
                          </td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent"><input type="text" size="12" name="cost" value="%s" style='border: 1px solid #cfcfcf'>
                            <select name="currency"  style='border: 1px solid #cfcfcf'>

                            """  % ( _("Status"), ill_request_id,ill_request_id,ill_request_id, _("ILL request ID"), ill_request_id,
                                    _("Library"), library_name,
                                    _("Request date"), request_date, _("Expected date"), expected_date,
                                    _("Arrival date"), CFG_SITE_URL, date1,
                                    request_date, expected_date,
                                    _("Cost"), value)


            if currency == 'EUR':
                out += """
                <option value="EUR" selected>EUR</option>
                <option value="CHF">CHF</option>
                <option value="USD">USD</option> """

            elif currency == 'CHF':
                out += """
                <option value="EUR">EUR</option>
                <option value="CHF" selected>CHF</option>
                <option value="USD">USD</option> """

            else:
                out +="""
                <option value="EUR">EUR</option>
                <option value="CHF">CHF</option>
                <option value="USD" selected>USD</option> """

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
                            <table class="bibcircnotes"> """ % (_("Barcode"), barcode, _("Previous notes"))

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
###### END STATUSES ######


        out += """

             <br />
             <table class="bibcirctable">
                <tr>
                  <td>
                       <input type=button value=%s
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit"
                       value=%s class="formbutton">

                  </td>
                 </tr>
             </table>
             </div>
             </form>
             <br />
             <br />
               """ % (_("Back"), _("Continue"))


        return out


    def tmpl_ill_request_details_step2(self, ill_req_details, request_info, ill_status, ill_request_borrower_details, ln=CFG_SITE_LANG):
        """
        @param ill_req_details: informations about a given ILL request
        @type ill_req_details: tuple

        @param request_info:
        @type request_info: tuple

        @param ill_status: status of an ILL request
        @type ill_status: string

        @param ill_request_borrower_details: borrower's informations
        @type ill_request_borrower_details: tuple
        """

        _ = gettext_set_language(ln)

        out = _MENU_

        (_borrower_id, borrower_name, borrower_email, borrower_mailbox,
         period_from, period_to, book_info, borrower_comments, only_this_edition) = ill_request_borrower_details

        if looks_like_dictionary(book_info):
            book_info = eval(book_info)
        else:
            book_info = {}

        try:
            (book_title, book_year, book_author, book_isbn, book_editor) = book_information_from_MARC(int(book_info['recid']))

            if book_isbn:
                book_cover = get_book_cover(book_isbn)
            else:
                book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)

            out += """
            <style type="text/css"> @import url("/img/tablesorter.css"); </style>
            <form name="ill_req_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/ill_request_details_step3" method="get" >
            <div class="bibcircbottom">
            <input type=hidden name=request_info value="%s">
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
                     </table>
                     </td>
                     <td class="bibcirccontent"><img style='border: 1px solid #cfcfcf' src="%s" alt="Book Cover"/></td>
                     </tr>
              </table>
              <br />

              """  % (CFG_SITE_URL,
                      request_info,
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

        except KeyError:

            try:
                book_cover = get_book_cover(book_info['isbn'])
            except KeyError:
                book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)

            out += """
            <style type="text/css"> @import url("/img/tablesorter.css"); </style>
            <form name="ill_req_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/ill_request_details_step3" method="get" >
            <div class="bibcircbottom">
            <input type=hidden name=request_info value="%s">
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
                        <td class="bibcirccontent">%s</td>
                     </tr>
                </table>
                  </td>
                    <td class="bibcirccontent"><img style='border: 1px solid #cfcfcf' src="%s" alt="Book Cover"/></td>
                  </tr>
              </table>
              <br />

              """  % (CFG_SITE_URL,
                      request_info,
                      _("Item details"),
                      _("Name"),
                      book_info['title'],
                      _("Author(s)"),
                      book_info['authors'],
                      _("Place"),
                      book_info['place'],
                      _("Publisher"),
                      book_info['publisher'],
                      _("Year"),
                      book_info['year'],
                      _("Edition"),
                      book_info['edition'],
                      _("ISBN"),
                      book_info['isbn'],
                      str(book_cover))



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
                  <td class="bibcirccontent">%s</td>
                </tr>
                <tr>
                  <th width="150">%s</th>
                  <td class="bibcirccontent">%s</td>
                </tr>
                <tr>
                  <th width="150">%s</th>
                  <td class="bibcirccontent">%s</td>
                </tr>
                <tr>
                  <th width="150">%s</th>
                  <td class="bibcirccontent">%s</td>
                </tr>
                <tr>
                  <th width="150">%s</th>
                  <td class="bibcirccontent">%s</td>
                </tr>
                <tr>
                   <th width="150">%s</th>
                   <td width="350" class="bibcirccontent"><i>%s</i></td>
                </tr>
                <tr>
                  <th width="150">%s</th>
                  <td class="bibcirccontent">%s</td>
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
                    _("Period of interest - From"), period_from,
                    _("Period of interest - To"), period_to,
                    _("Borrower comments"), borrower_comments or '-',
                    _("Only this edition?"), only_this_edition,
                    _("ILL request details"))

        if ill_status == 'new':

            if not ill_req_details:
                previous_library_notes = {}
            else:
                if looks_like_dictionary(ill_req_details[8]):
                    previous_library_notes = eval(ill_req_details[8])
                else:
                    previous_library_notes = {}

            (ill_request_id, library_notes) = request_info

            out += """
            <input type=hidden name=ill_status value="%s">
            <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
               <tr>
                 <th width="100">%s</th>
                 <td class="bibcirccontent"><b>%s</b></td>
               </tr>
               <tr>
                 <th width="100">%s</th>
                 <td class="bibcirccontent">%s</td>
               </tr>
               <tr>
                 <th width="100" valign="top">%s</th>
                 <td>
                   <table class="bibcircnotes"> """ % (ill_status, _("Status"), ill_status,
                                                       _("ILL request ID"), ill_request_id,
                                                       _("Previous notes"))

            key_array = previous_library_notes.keys()
            key_array.sort()

            for key in key_array:
                delete_note = create_html_link(CFG_SITE_URL +
                                           '/admin/bibcirculation/bibcirculationadmin.py/ill_request_details_step2',
                                           {'delete_key': key, 'ill_request_id': ill_request_id, 'ill_status': ill_status,
                                            'library_notes': library_notes, 'ln': ln},
                                           (_("[delete]")))

                out += """<tr class="bibcirccontent">
                            <td class="bibcircnotes" width="160" valign="top" align="center"><b>%s</b></td>
                            <td width="400"><i>%s</i></td>
                            <td width="65" align="center">%s</td>
                          </tr>

                      """ % (key, previous_library_notes[key], delete_note)


            out += """
                            </table>
                          </td>
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td class="bibcirccontent"><i>%s</i></td>
                        </tr>
                      </table>
                    </td>
                  </tr>
                </table>

                     """ % (_("Library notes"), library_notes or '-')

        elif ill_status == 'requested':

            if not ill_req_details:
                previous_library_notes = {}
            else:
                if looks_like_dictionary(ill_req_details[8]):
                    previous_library_notes = eval(ill_req_details[8])
                else:
                    previous_library_notes = {}

            (ill_request_id, library_id, request_date, expected_date,
             cost, currency, barcode, library_notes) =  request_info

            if library_id:
                library_name = db.get_library_name(library_id)
            else:
                library_name = '-'

            out += """
            <input type=hidden name=ill_status value="%s">
            <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
               <tr>
                 <th width="100">%s</th>
                 <td class="bibcirccontent"><b>%s</b></td>
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
                 <td class="bibcirccontent">%s %s</td>
               </tr>
               <tr>
                 <th width="100">%s</th>
                 <td class="bibcirccontent">%s</td>
               </tr>
               <tr>
                 <th width="100" valign="top">%s</th>
                 <td>
                   <table class="bibcircnotes"> """ % (ill_status, _("Status"), ill_status,
                                                       _("ILL request ID"), ill_request_id,
                                                       _("Library/Supplier"), library_name,
                                                       _("Request date"), request_date,
                                                       _("Expected date"),expected_date,
                                                       _("Cost"), cost, currency,
                                                       _("Barcode"), barcode,
                                                       _("Previous notes"))

            key_array = previous_library_notes.keys()
            key_array.sort()

            for key in key_array:
                delete_note = create_html_link(CFG_SITE_URL +
                                           '/admin/bibcirculation/bibcirculationadmin.py/ill_request_details_step2',
                                           {'delete_key': key, 'ill_request_id': ill_request_id, 'ill_status': ill_status,
                                            'library_notes': library_notes, 'ln': ln},
                                           (_("[delete]")))

                out += """<tr class="bibcirccontent">
                            <td class="bibcircnotes" width="160" valign="top" align="center"><b>%s</b></td>
                            <td width="400"><i>%s</i></td>
                            <td width="65" align="center">%s</td>
                          </tr>

                      """ % (key, previous_library_notes[key], delete_note)


            out += """
                            </table>
                          </td>
                        </tr>
               <tr>
                   <th width="100">%s</th>
                   <td class="bibcirccontent"><i>%s</i></td>
               </tr>
              </table>
              </td>
              </tr>
              </table>
              """ % (_("Library notes"), library_notes or '-')

        elif ill_status == 'request cancelled':
            (library_id, request_date, expected_date, previous_library_notes) = ill_req_details

            if not previous_library_notes:
                previous_library_notes = {}
            else:
                if looks_like_dictionary(previous_library_notes):
                    previous_library_notes = eval(previous_library_notes)
                else:
                    previous_library_notes = {}

            (ill_request_id, cost, currency, barcode, library_notes) =  request_info

            if library_id:
                library_name = db.get_library_name(library_id)
            else:
                library_name = '-'

            out += """
            <input type=hidden name=ill_status value="%s">
            <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
               <tr>
                 <th width="100">%s</th>
                 <td class="bibcirccontent"><b>%s</b></td>
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
                 <td class="bibcirccontent">%s %s</td>
               </tr>
               <tr>
                 <th width="100">%s</th>
                 <td class="bibcirccontent">%s</td>
               </tr>
               <tr>
                 <th width="100" valign="top">%s</th>
                 <td>
                   <table class="bibcircnotes"> """ % (ill_status, _("Status"), ill_status,
                                                       _("ILL request ID"), ill_request_id,
                                                       _("Library/Supplier"), library_name,
                                                       _("Request date"), request_date,
                                                       _("Expected date"),expected_date,
                                                       _("Cost"), cost, currency,
                                                       _("Barcode"), barcode,
                                                       _("Previous notes"))

            key_array = previous_library_notes.keys()
            key_array.sort()

            for key in key_array:
                delete_note = create_html_link(CFG_SITE_URL +
                                           '/admin/bibcirculation/bibcirculationadmin.py/ill_request_details_step2',
                                           {'delete_key': key, 'ill_request_id': ill_request_id, 'ill_status': ill_status,
                                            'library_notes': library_notes, 'ln': ln},
                                           (_("[delete]")))

                out += """<tr class="bibcirccontent">
                            <td class="bibcircnotes" width="160" valign="top" align="center"><b>%s</b></td>
                            <td width="400"><i>%s</i></td>
                            <td width="65" align="center">%s</td>
                          </tr>

                      """ % (key, previous_library_notes[key], delete_note)


            out += """
                            </table>
                          </td>
                        </tr>
               <tr>
                   <th width="100">%s</th>
                   <td class="bibcirccontent"><i>%s</i></td>
               </tr>
              </table>
              </td>
              </tr>
              </table>
              """ % (_("Library notes"), library_notes or '-')

        elif ill_status == 'item received, due date defined':

            (library_id, request_date, expected_date, previous_library_notes) = ill_req_details

            if not previous_library_notes:
                previous_library_notes = {}
            else:
                if looks_like_dictionary(previous_library_notes):
                    previous_library_notes = eval(previous_library_notes)
                else:
                    previous_library_notes = {}

            (ill_request_id, arrival_date, due_date, cost, currency, barcode, library_notes) =  request_info

            if library_id:
                library_name = db.get_library_name(library_id)
            else:
                library_name = '-'

            out += """
            <input type=hidden name=ill_status value="%s">
            <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
               <tr>
                 <th width="100">%s</th>
                 <td class="bibcirccontent"><b>%s</b></td>
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
                 <td class="bibcirccontent">%s</td>
               </tr>
               <tr>
                 <th width="100">%s</th>
                 <td class="bibcirccontent">%s %s</td>
               </tr>
               <tr>
                 <th width="100">%s</th>
                 <td class="bibcirccontent">%s</td>
               </tr>
               <tr>
                 <th width="100" valign="top">%s</th>
                 <td>
                   <table class="bibcircnotes"> """ % (ill_status, _("Status"), ill_status,
                                                       _("ILL request ID"), ill_request_id,
                                                       _("Library/Supplier"), library_name,
                                                       _("Request date"), request_date,
                                                       _("Expected date"), expected_date,
                                                       _("Arrival date"), arrival_date,
                                                       _("Due date"), due_date,
                                                       _("Cost"), cost, currency,
                                                       _("Barcode"), barcode,
                                                       _("Previous notes"))

            key_array = previous_library_notes.keys()
            key_array.sort()

            for key in key_array:
                delete_note = create_html_link(CFG_SITE_URL +
                                           '/admin/bibcirculation/bibcirculationadmin.py/ill_request_details_step2',
                                           {'delete_key': key, 'ill_request_id': ill_request_id, 'ill_status': ill_status,
                                            'library_notes': library_notes, 'ln': ln},
                                           (_("[delete]")))

                out += """<tr class="bibcirccontent">
                            <td class="bibcircnotes" width="160" valign="top" align="center"><b>%s</b></td>
                            <td width="400"><i>%s</i></td>
                            <td width="65" align="center">%s</td>
                          </tr>

                      """ % (key, previous_library_notes[key], delete_note)


            out += """
                            </table>
                          </td>
                        </tr>
               <tr>
                   <th width="100">%s</th>
                   <td class="bibcirccontent"><i>%s</i></td>
               </tr>
              </table>
              </td>
              </tr>
              </table>
              """ % (_("Library notes"), library_notes or '-')

        elif ill_status == 'item returned':

            (library_id, request_date, expected_date, arrival_date, due_date, barcode, previous_library_notes) = ill_req_details

            if looks_like_dictionary(previous_library_notes):
                previous_library_notes = eval(previous_library_notes)
            else:
                previous_library_notes = {}

            (ill_request_id, return_date, cost, currency, library_notes) =  request_info

            library_name = db.get_library_name(library_id)

            out += """
            <input type=hidden name=ill_status value="%s">
            <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
               <tr>
                 <th width="100">%s</th>
                 <td class="bibcirccontent"><b>%s</b></td>
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
                 <td class="bibcirccontent">%s</td>
               </tr>
               <tr>
                 <th width="100">%s</th>
                 <td class="bibcirccontent">%s</td>
               </tr>
               <tr>
                 <th width="100">%s</th>
                 <td class="bibcirccontent">%s %s</td>
               </tr>
               <tr>
                 <th width="100">%s</th>
                 <td class="bibcirccontent">%s</td>
               </tr>
               <tr>
                 <th width="100" valign="top">%s</th>
                 <td>
                   <table class="bibcircnotes"> """ % (ill_status, _("Status"), ill_status,
                                                       _("ILL request ID"), ill_request_id,
                                                       _("Library/Supplier"), library_name,
                                                       _("Request date"), request_date,
                                                       _("Expected date"), expected_date,
                                                       _("Arrival date"), arrival_date,
                                                       _("Due date"), due_date,
                                                       _("Return date"), return_date,
                                                       _("Cost"), cost, currency,
                                                       _("Barcode"), barcode,
                                                       _("Previous notes"))

            key_array = previous_library_notes.keys()
            key_array.sort()

            for key in key_array:
                delete_note = create_html_link(CFG_SITE_URL +
                                           '/admin/bibcirculation/bibcirculationadmin.py/ill_request_details_step2',
                                           {'delete_key': key, 'ill_request_id': ill_request_id, 'ill_status': ill_status,
                                            'library_notes': library_notes, 'ln': ln},
                                           (_("[delete]")))

                out += """<tr class="bibcirccontent">
                            <td class="bibcircnotes" width="160" valign="top" align="center"><b>%s</b></td>
                            <td width="400"><i>%s</i></td>
                            <td width="65" align="center">%s</td>
                          </tr>

                      """ % (key, previous_library_notes[key], delete_note)


            out += """
                            </table>
                          </td>
                        </tr>
               <tr>
                   <th width="100">%s</th>
                   <td class="bibcirccontent"><i>%s</i></td>
               </tr>
              </table>
              </td>
              </tr>
              </table>
              """ % (_("Library notes"), library_notes or '-')

        else:

            (library_id, request_date, expected_date, arrival_date, due_date, return_date, cost, barcode, previous_library_notes) = ill_req_details

            if looks_like_dictionary(previous_library_notes):
                previous_library_notes = eval(previous_library_notes)
            else:
                previous_library_notes = {}

            (value, currency) = cost.split()

            (ill_request_id, library_notes) =  request_info

            library_name = db.get_library_name(library_id)

            out += """
            <input type=hidden name=ill_status value="%s">
            <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
               <tr>
                 <th width="100">%s</th>
                 <td class="bibcirccontent"><b>%s</b></td>
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
                 <td class="bibcirccontent">%s</td>
               </tr>
               <tr>
                 <th width="100">%s</th>
                 <td class="bibcirccontent">%s</td>
               </tr>
               <tr>
                 <th width="100">%s</th>
                 <td class="bibcirccontent">%s %s</td>
               </tr>
               <tr>
                 <th width="100">%s</th>
                 <td class="bibcirccontent">%s</td>
               </tr>
               <tr>
                 <th width="100" valign="top">%s</th>
                 <td>
                   <table class="bibcircnotes"> """ % (ill_status, _("Status"), ill_status,
                                                       _("ILL request ID"), ill_request_id,
                                                       _("Library/Supplier"), library_name,
                                                       _("Request date"), request_date,
                                                       _("Expected date"), expected_date,
                                                       _("Arrival date"), arrival_date,
                                                       _("Due date"), due_date,
                                                       _("Return date"), return_date,
                                                       _("Cost"), value, currency,
                                                       _("Barcode"), barcode,
                                                       _("Previous notes"))

            key_array = previous_library_notes.keys()
            key_array.sort()

            for key in key_array:
                delete_note = create_html_link(CFG_SITE_URL +
                                           '/admin/bibcirculation/bibcirculationadmin.py/ill_request_details_step2',
                                           {'delete_key': key, 'ill_request_id': ill_request_id, 'ill_status': ill_status,
                                            'library_notes': library_notes, 'ln': ln},
                                           (_("[delete]")))

                out += """<tr class="bibcirccontent">
                            <td class="bibcircnotes" width="160" valign="top" align="center"><b>%s</b></td>
                            <td width="400"><i>%s</i></td>
                            <td width="65" align="center">%s</td>
                          </tr>

                      """ % (key, previous_library_notes[key], delete_note)


            out += """
                            </table>
                          </td>
                        </tr>
               <tr>
                   <th width="100">%s</th>
                   <td class="bibcirccontent"><i>%s</i></td>
               </tr>
              </table>
              </td>
              </tr>
              </table>
              """ % (_("Library notes"), library_notes or '-')



        out += """
             <br />
             <table class="bibcirctable">
                <tr>
                  <td>
                       <input type=button value=%s
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit"
                       value=%s class="formbutton">

                  </td>
                 </tr>
             </table>
             </div>
             </form>
             <br />
             <br />
               """ % (_("Back"), _("Continue"))

        return out


    def tmpl_ill_request_details_step3(self, ln=CFG_SITE_LANG):
        """
        Last step of the request procedure.

        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_


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
        <td><input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1'"
        value='%s' class='formbutton'></td>
        </table>
        <br />
        <br />
        </div>

        """ % (_("An ILL request has been updated with success."),
               CFG_SITE_URL, _("Back to home"))


        return out

    def tmpl_ordered_book_details_step1(self, order_details, list_of_vendors, ln=CFG_SITE_LANG):
        """
        @param order_details: informations about a given order.
        @type order_details: tuple

        @param list_of_vendors: list with all the vendors
        @type list_of_vendors: list
        """

        _ = gettext_set_language(ln)

        out = """
        """
        out += _MENU_

        (purchase_id, recid, vendor, order_date, expected_date, price, status, notes) = order_details

        if looks_like_dictionary(notes):
            purchase_notes = eval(notes)
        else:
            purchase_notes = {}

        (book_title, book_year, book_author, book_isbn, book_editor) = book_information_from_MARC(int(recid))

        (value, currency) = price.split()

        if book_isbn:
            book_cover = get_book_cover(book_isbn)
        else:
            book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)

        out += """
           <style type="text/css"> @import url("/img/tablesorter.css"); </style>
           <form name="update_item_info_step4_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/ordered_books_details_step2" method="get" >
           <div class="bibcircbottom">
           <input type=hidden name=purchase_id value="%s">
                <br />
                     <table class="bibcirctable">
                          <tr>
                               <td class="bibcirctableheader" width="10">%s</td>
                          </tr>
                </table>
                <table class="bibcirctable">
                 <tr valign='top'>
                    <td width="400"><input type=hidden name=recid value='%s'>
                    <table class="tablesorter" border="0" cellpadding="0" cellspacing="1">
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
                     </table>
                     </td>
                     <td class="bibcirccontent"><img style='border: 1px solid #cfcfcf' src="%s" alt="Book Cover"/></td>
                     </tr>
              </table>

           <br />

           """  % (CFG_SITE_URL,
                   purchase_id,
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
                   book_isbn,
                   str(book_cover))

        out += """

        <script type="text/javascript" language='JavaScript' src="%s/js/jquery-ui.min.js"></script>

             <table class="bibcirctable">
                <tr>
                     <td class="bibcirctableheader">%s</td>
                </tr>
             </table>
             <table class="tablesortermedium" border="0" cellpadding="0" cellspacing="1">
                <tr>
                    <th width="100">%s</th>
                    <td class="bibcirccontent">
                    <select name="vendor_id"  style='border: 1px solid #cfcfcf'>

                    """ % (CFG_SITE_URL, _("Order details"), _("Vendor"))

        for(vendor_id, name) in list_of_vendors:
            if vendor_id == vendor:
                out +="""<option value="%s" selected>%s</option>""" % (vendor_id, name)
            else:
                out +="""<option value="%s">%s</option>""" % (vendor_id, name)

        out += """
                    </select>
                    </td>
                </tr>
                <tr>
                    <th width="100">%s</th>
                    <td class="bibcirccontent">
                    <input type="text" size="12" name="cost" value="%s" style='border: 1px solid #cfcfcf'>
                    <select name="currency"  style='border: 1px solid #cfcfcf'>

                """ % (_("Cost"), value,)

        if currency == 'EUR':
            out += """
             <option value="EUR" selected>EUR</option>
             <option value="CHF">CHF</option>
             <option value="USD">USD</option> """

        elif currency == 'CHF':
            out += """
             <option value="EUR">EUR</option>
             <option value="CHF" selected>CHF</option>
             <option value="USD">USD</option> """

        else:
            out +="""
            <option value="EUR">EUR</option>
            <option value="CHF">CHF</option>
            <option value="USD" selected>USD</option> """


        out += """
                    </select>
                    </td>
                </tr>
                <tr>
                    <th width="100">%s</th>
                    <td class="bibcirccontent">
                      <select name="status" style='border: 1px solid #cfcfcf'>

                      """ % (_("Status"))

        if status == 'ordered':
            out += """
                     <option value ="ordered" selected>ordered</option>
                     <option value ="cancelled">cancelled</option>
                     <option value ="not arrived">not arrived</option>
                   """

        elif status == 'cancelled':
            out += """
                     <option value ="ordered">ordered</option>
                     <option value ="cancelled" selected>cancelled</option>
                     <option value ="not arrived">not arrived</option>

                    """

        else:
            out += """
                     <option value ="ordered">ordered</option>
                     <option value ="cancelled">cancelled</option>
                     <option value ="not arrived" selected>not arrived</option>

                      """
        out += """
                      </select>
                    </td>
                </tr>
                <tr>
                <th width="100">%s</th>
                <td class="bibcirccontent">

                        <script type="text/javascript">
                             $(function() {
                                 $("#date_picker1").datepicker({dateFormat: 'yy-mm-dd', showOn: 'button', buttonImage: "%s/img/calendar.gif", buttonImageOnly: true});
                             });
                        </script>
                        <input type="text" size="10" id="date_picker1" name="order_date" value="%s" style='border: 1px solid #cfcfcf'>

                    </td>
                </tr>
                <tr>
                <th width="100">%s</th>
                <td class="bibcirccontent">
                        <script type="text/javascript">
                             $(function() {
                                 $("#date_picker2").datepicker({dateFormat: 'yy-mm-dd', showOn: 'button', buttonImage: "%s/img/calendar.gif", buttonImageOnly: true});
                             });
                        </script>
                        <input type="text" size="10" id="date_picker2" name="expected_date" value="%s" style='border: 1px solid #cfcfcf'>

                    </td>
                </tr>
                <tr>
                    <th width="100" valign="top">%s</th>
                    <td>
                      <table class="bibcircnotes">

                    """ % (_("Order date"), CFG_SITE_URL, order_date,
                           _("Expected date"), CFG_SITE_URL, expected_date,
                           _("Previous notes"))

        key_array = purchase_notes.keys()
        key_array.sort()

        for key in key_array:

            delete_note = create_html_link(CFG_SITE_URL +
                                           '/admin/bibcirculation/bibcirculationadmin.py/ordered_books_details_step1',
                                           {'delete_key': key, 'purchase_id': purchase_id, 'ln': ln},
                                           (_("[delete]")))

            out += """<tr class="bibcirccontent">
                        <td class="bibcircnotes" width="160" valign="top" align="center"><b>%s</b></td>
                        <td width="400"><i>%s</i></td>
                        <td width="65" align="center">%s</td>
                      </tr>

                      """ % (key, purchase_notes[key], delete_note)


        out += """
                   </table></td>
               </tr>
               <input type=hidden name="purchase_notes" value="%s">
               <tr>
                 <th width="100" valign="top">%s</th>
                 <td class="bibcirccontent">
                   <textarea name="library_notes" rows="5" cols="90" style='border: 1px solid #cfcfcf'></textarea>
                 </td>
               </tr>
             </table>
             <br />
             <table class="bibcirctable">
                <tr>
                  <td>
                       <input type=button value=%s
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit"
                       value=%s class="formbutton">

                  </td>
                 </tr>
             </table>
             </form>
             <br />
             <br />
             </div>
             """ % (purchase_notes, _("Notes"), _("Back"), _("Continue"))

        return out


    def tmpl_ordered_book_details_step2(self, order_details, ln=CFG_SITE_LANG):
        """
        @param order_details: informations about a given order.
        @type order_details: tuple

        @param ln: language of the page
        """

        (purchase_id, recid, vendor_id, cost, currency, status,
         order_date, expected_date, purchase_notes, library_notes) = order_details

        vendor_name = db.get_vendor_name(vendor_id)

        (book_title, book_year, book_author, book_isbn, book_editor) = book_information_from_MARC(int(recid))

        if book_isbn:
            book_cover = get_book_cover(book_isbn)
        else:
            book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)

        _ = gettext_set_language(ln)

        out = """
        """
        out += _MENU_

        out += """
            <div class="bibcircbottom">
            <form name="step2_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/ordered_books_details_step3" method="get" >
                <input type=hidden name=purchase_id value="%s">
                <input type=hidden name=recid value="%s">
                <input type=hidden name=vendor_id value="%s">
                <input type=hidden name=cost value="%s">
                <input type=hidden name=currency value="%s">
                <input type=hidden name=status value="%s">
                <input type=hidden name=order_date value="%s">
                <input type=hidden name=expected_date value="%s">
                <input type=hidden name=purchase_notes value="%s">
                <input type=hidden name=library_notes value="%s">
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
                     purchase_id, recid,
                     vendor_id, cost,
                     currency, status,
                     order_date,
                     expected_date,
                     purchase_notes,
                     library_notes,
                     _("Item details"),
                     _("Name"), book_title,
                     _("Author(s)"), book_author,
                     _("Year"), book_year,
                     _("Publisher"), book_editor,
                     _("ISBN"), book_isbn,
                     str(book_cover))

        out += """
              <br />
              <table class="bibcirctable">
                  <tr>
                     <td class="bibcirctableheader">%s</td>
                  </tr>
                </table>
              <table class="bibcirctable">
                <tr>
                    <td width="100">%s</td>
                    <td class="bibcirccontent">%s</td>
                </tr>
                <tr>
                    <td width="100">%s</td>
                    <td class="bibcirccontent">%s %s</td>
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
                    <td width="100" valign="top">%s</td>
                    <td><table class="bibcircnotes">

                    """ % (_("Order details"),
                           _("Vendor"), vendor_name,
                           _("Price"), cost, currency,
                           _("Status"), status,
                           _("Order date"), order_date,
                           _("Expected date"), expected_date,
                           _("Previous notes"))

        if looks_like_dictionary(purchase_notes):
            purchase_notes = eval(purchase_notes)
        else:
            purchase_notes = {}

        key_array = purchase_notes.keys()
        key_array.sort()

        for key in key_array:
            out += """<tr class="bibcirccontent">
                        <td class="bibcircnotes" width="160" valign="top" align="center"><b>[%s]</b></td>
                        <td width="400"><i>%s</i></td>
                      </tr>

                      """ % (key, purchase_notes[key])

        out += """
                   </table>
                  </td>
                 </tr>
                  <tr>
                    <td width="100">%s</td>
                    <td class="bibcirccontent">%s</td>
                 </tr>
                </table>
                <br />
                <table class="bibcirctable">
                   <tr>
                    <td>
                       <input type=button value=%s
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit"
                       value=%s class="formbutton">

                    </td>
                   </tr>
                 </table>
               </form>
               <br />
               <br />
               </div>
               """ % (_("Notes"), library_notes,
                      _("Back"), _("Continue"))

        return out

    def tmpl_ordered_book_details_step3(self, ln=CFG_SITE_LANG):
        """
        Last step of the request procedure.

        @param ln: language
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_


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
        <td><input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1'"
        value='%s' class='formbutton'></td>
        </table>
        <br />
        <br />
        </div>

        """ % (_("Purchase information updated with success."),
               CFG_SITE_URL, _("Back to home"))


        return out


    def tmpl_add_new_vendor_step1(self, ln=CFG_SITE_LANG):
        """
        @param ln: language
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_

        out += """
            <style type="text/css"> @import url("/img/tablesorter.css"); </style>
            <div class="bibcircbottom" align="center">
            <form name="add_new_vendor_step1_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/add_new_vendor_step2" method="get" >
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
                       <input type=button value=%s onClick="history.go(-1)" class="formbutton">
                       <input type="submit"   value=%s class="formbutton">
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
        @param tup_infos: borrower's informations
        @type tup_infos: tuple

        @param ln: language
        """

        _ = gettext_set_language(ln)

        (name, email, phone, address, notes) = tup_infos

        out = """ """

        out += _MENU_

        out += """
            <style type="text/css"> @import url("/img/tablesorter.css"); </style>
            <div class="bibcircbottom" align="center">
            <form name="add_new_vendor_step2_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/add_new_vendor_step3" method="get" >
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
                       <input type=button value=%s onClick="history.go(-1)" class="formbutton">
                       <input type="submit"   value=%s class="formbutton">
                       <input type=hidden name=tup_infos value="%s">
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
                       tup_infos)

        return out


    def tmpl_add_new_vendor_step3(self, ln=CFG_SITE_LANG):
        """
        @param ln: language
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_

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
                       <input type=button value=%s
                        onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1'"
                        class="formbutton">
                  </td>
                 </tr>
                </table>
                <br />
                <br />
                </div>
                """ % (_("A new vendor has been registered."),
                       _("Back to home"),
                       CFG_SITE_URL)

        return out

    def tmpl_update_vendor_info_step1(self, infos, ln=CFG_SITE_LANG):
        """
        @param infos: informations
        @type infos: list

        @param ln: language
        """
        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += _MENU_

        out += """
        <div class="bibcircbottom">
        <br /><br />         <br />
        <form name="update_vendor_info_step1_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/update_vendor_info_step2" method="get" >
             <table class="bibcirctable">
                  <tr align="center">
                    <td class="bibcirctableheader">%s
                     <input type="radio" name="column" value="name" checked>name
                     <input type="radio" name="column" value="email">email
                     <br>
                     <br>
                     </td>
                  </tr>
                  <tr align="center">
                        <td><input type="text" size="45" name="string" style='border: 1px solid #cfcfcf'></td>
                  </tr>
             </table>
        <br />
        <table class="bibcirctable">
             <tr align="center">
                  <td>
                        <input type=button value='%s'
                         onClick="history.go(-1)" class="formbutton">
                        <input type="submit" value="Search" class="formbutton">

                  </td>
             </tr>
        </table>
        <form>
        <br /><br />
        <br />
        <br />
        </div>

        """ % (CFG_SITE_URL,
               _("Search vendor by"),
               _("Back"))

        return out


    def tmpl_update_vendor_info_step2(self, result, ln=CFG_SITE_LANG):
        """
        @param result: search result
        @type result: list

        @param ln: language
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_

        out += """
        <style type="text/css"> @import url("/img/tablesorter.css"); </style>
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
                                           '/admin/bibcirculation/bibcirculationadmin.py/update_vendor_info_step3',
                                           {'vendor_id': vendor_id, 'ln': ln},
                                           (name))

            out += """
            <tr align="center">
                 <td class="bibcirccontent" width="70">%s
                 <input type=hidden name=vendor_id value=%s></td>
            </tr>
            """ % (vendor_link, vendor_id)


        out += """
             </table>
             <br />
             """

        out += """
        <table class="bibcirctable">
             <tr align="center">
                  <td><input type=button value=%s
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

        out += _MENU_

        out += """
            <style type="text/css"> @import url("/img/tablesorter.css"); </style>
            <div class="bibcircbottom" align="center">
            <form name="update_vendor_info_step3_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/update_vendor_info_step4" method="get" >
             <input type=hidden name=vendor_id value=%s>
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
                       <input type=button value=%s
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit"
                       value=%s class="formbutton">

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

        (_vendor_id, name, email, phone, address) = tup_infos

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_

        out += """
            <style type="text/css"> @import url("/img/tablesorter.css"); </style>
            <div class="bibcircbottom" align="center">
            <form name="update_vendor_info_step4_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/update_vendor_info_step5" method="get" >
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
                       <input type=button value=%s
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit"
                       value=%s class="formbutton">

                       <input type=hidden name=tup_infos value="%s">
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
                       tup_infos)

        return out

    def tmpl_update_vendor_info_step5(self, ln=CFG_SITE_LANG):
        """
        @param ln: language
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_

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
                       <input type=button value=%s
                        onClick= onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1'"
                        class="formbutton">
                  </td>
                 </tr>
                </table>
                <br />
                <br />
                </div>
                """ % (_("The information has been updated."),
                       _("Back to home"),
                       CFG_SITE_URL)

        return out

    def tmpl_search_vendor_step1(self, infos, ln=CFG_SITE_LANG):
        """
        @param infos: informations
        @type infos: list

        @param ln: language
        """
        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += _MENU_

        out += """
        <div class="bibcircbottom">
        <br /><br />         <br />
        <form name="search_vendor_step1_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/search_vendor_step2" method="get" >
          <table class="bibcirctable">
           <tr align="center">
             <td class="bibcirctableheader">%s
               <input type="radio" name="column" value="name" checked>name
               <input type="radio" name="column" value="email">email
               <br>
               <br>
             </td>
           </tr>
           <tr align="center">
             <td><input type="text" size="45" name="string" style='border: 1px solid #cfcfcf'></td>
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

        """ % (CFG_SITE_URL,
               _("Search vendor by"),
               _("Back"),
               _("Search"))


        return out

    def tmpl_search_vendor_step2(self, result, ln=CFG_SITE_LANG):
        """
        @param result: search result
        @type result:list

        @param ln: language
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_

        out += """
        <style type="text/css"> @import url("/img/tablesorter.css"); </style>
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
                                           '/admin/bibcirculation/bibcirculationadmin.py/get_vendor_details',
                                           {'vendor_id': vendor_id, 'ln': ln},
                                           (name))

            out += """
            <tr align="center">
                 <td class="bibcirccontent" width="70">%s
                 <input type=hidden name=library_id value=%s></td>
            </tr>
            """ % (vendor_link, vendor_id)

        out += """
        </table>
        <br />
        <table class="bibcirctable">
             <tr align="center">
                  <td>
                    <input type=button value=%s
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
        out += _MENU_

        out += """
        <div class="bibcircbottom" align="center">
        <br />
        <style type="text/css"> @import url("/img/tablesorter.css"); </style>
        """
        (vendor_id, name, address, email, phone, notes) = vendor_details

        no_notes_link = create_html_link(CFG_SITE_URL +
                                         '/admin/bibcirculation/bibcirculationadmin.py/get_vendor_notes',
                                         {'vendor_id': vendor_id},
                                         (_("No notes")))

        see_notes_link = create_html_link(CFG_SITE_URL +
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_vendor_notes',
                                          {'vendor_id': vendor_id},
                                          (_("Notes about this vendor")))

        if notes == "":
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
                      <td><input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/update_vendor_info_step3?vendor_id=%s'" onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
                      value=%s  class="bibcircbutton">
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

        out += _MENU_

        out +="""
            <div class="bibcircbottom">
            <form name="vendor_notes" action="%s/admin/bibcirculation/bibcirculationadmin.py/get_vendor_notes" method="get" >
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
                      <input type=hidden name=vendor_id value=%s>
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
                       <input type=hidden name=vendor_id value=%s>
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
                       <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/get_vendor_details?vendor_id=%s'"
                       value=%s class='formbutton'>
                  </td>
             </tr>
             </table>
             <br />
             <br />
             <br />
             </form>
             </div>
        """ % (CFG_SITE_URL,
               vendor_id,
               _("Back"))

        return out

    def tmpl_register_ill_request_with_no_recid_step1(self, infos, ln=CFG_SITE_LANG):
        """
        @param infos: informations
        @type infos: list
        """

        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += _MENU_

        out += """
        <br />
        <br />
          <div class="bibcircbottom" align="center">
          <div class="infoboxmsg"><strong>%s<br />%s</strong></div>
          <br />
          <br />
          <style type="text/css"> @import url("/img/tablesorter.css"); </style>
           <form name="display_ill_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/register_ill_request_with_no_recid_step2" method="get">
             <table class="bibcirctable">
                  <tr align="center">
                    <td class="bibcirctableheader">%s</td>
                  </tr>
                </table>
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

           """  % (_("Book does not exists on Invenio."),_("Please fill the following form."),
                   CFG_SITE_URL,
                   _("Item details"),
                   _("Book title"),
                   _("Author(s)"),
                   _("Place"),
                   _("Publisher"),
                   _("Year"),
                   _("Edition"),
                   _("ISBN"))



        conditions_link = """<a href="http://library.web.cern.ch/library/Library/ill_faq.html" target="_blank">conditions</a>"""

        out += """
        <script type="text/javascript" language='JavaScript' src="%s/js/jquery-ui.min.js"></script>

             <table class="bibcirctable">
                <tr align="center">
                     <td class="bibcirctableheader">%s</td>
                </tr>
             </table>
             <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">
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
                      _("ILL request details"),
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
                       <input type=button value=%s
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit"
                       value=%s class="formbutton">

                  </td>
                 </tr>
             </table>
             </form>
             <br />
             <br />
             </div>
             """ % (_("Period of interest (To)"),  CFG_SITE_URL, (datetime.date.today() + datetime.timedelta(days=365)).strftime('%Y-%m-%d'),
                    _("Additional comments"),
                    _("Borrower accepts the %s of the service in particular the return of books in due time." % (conditions_link)),
                    _("Borrower wants this edition only."),
                    _("Back"), _("Continue"))

        return out

    def tmpl_register_ill_request_with_no_recid_step2(self, book_info, request_details,
                                                      result, key, string, infos, ln):
        """
        @param book_info: book's informations
        @type book_info: tuple

        @param request_details: details about a given request
        @type request_details: tuple

        @param result: borrower's informations
        @type result: list

        @param key: field (name, email, etc...)
        @param key: string

        @param string: pattern
        @type string: string

        @param infos: informations
        @type infos: list
        """

        (title, authors, place, publisher, year, edition, isbn) = book_info

        (period_of_interest_from, period_of_interest_to,
         additional_comments, only_edition)= request_details

        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += _MENU_

        #if isbn:
        #    book_cover = get_book_cover(isbn)
        #else:
        #    book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)

        out += """
        <style type="text/css"> @import url("/img/tablesorter.css"); </style>
        <div class="bibcircbottom">
         <form name="step1_form1" action="%s/admin/bibcirculation/bibcirculationadmin.py/register_ill_request_with_no_recid_step2" method="get" >
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
                          <td>%s</td><input type=hidden name=publisher value="%s">
                        </tr>
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td><input type=hidden name=year value="%s">
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
                            _("Period of interest - From"), period_of_interest_from, period_of_interest_from,
                            _("Period of interest - To"), period_of_interest_to, period_of_interest_to,
                            _("Additional comments"), additional_comments, additional_comments,
                            _("Only this edition."), only_edition, only_edition)

#<img style='border: 1px solid #cfcfcf' src="%s" alt="Book Cover"/> ,
                         #   str(book_cover)
        out += """
        <td valign='top' align='center'>
         <table>

            """

        if CFG_CERN_SITE == 1:

            out += """
                 <tr>
                   <td class="bibcirctableheader" align="center">Search user by

                   """

            if key == 'email':
                out += """
                   <input type="radio" name="key" value="ccid">ccid
                   <input type="radio" name="key" value="name">name
                   <input type="radio" name="key" value="email" checked>email
                   """

            elif key == 'name':
                out += """
                   <input type="radio" name="key" value="ccid">ccid
                   <input type="radio" name="key" value="name" checked>name
                   <input type="radio" name="key" value="email">email
                   """

            else:
                out += """
                   <input type="radio" name="key" value="ccid" checked>ccid
                   <input type="radio" name="key" value="name">name
                   <input type="radio" name="key" value="email">email
                   """

        else:
            out += """
                 <tr>
                   <td class="bibcirctableheader" align="center">Search borrower by

                   """

            if key == 'email':
                out += """
                   <input type="radio" name="key" value="id">id
                   <input type="radio" name="key" value="name">name
                   <input type="radio" name="key" value="email" checked>email
                   """

            elif key == 'id':
                out += """
                   <input type="radio" name="key" value="id" checked>id
                   <input type="radio" name="key" value="name">name
                   <input type="radio" name="key" value="email">email
                   """

            else:
                out += """
                   <input type="radio" name="key" value="id">id
                   <input type="radio" name="key" value="name" checked>name
                   <input type="radio" name="key" value="email">email
                   """

        out += """
                    <br><br>
                    </td>
                    </tr>
                    <tr>
                    <td align="center">
                    <input type="text" size="40" id="string" name="string"  value='%s' style='border: 1px solid #cfcfcf'>
                    </td>
                    </tr>
                    <tr>
                    <td align="center">
                    <br>
                    <input type="submit" value="Search" class="formbutton">
                    </td>
                    </tr>

                   </table>
          </form>

        """ % (string or '')

        if result:
            out += """
            <br />
            <form name="step1_form2" action="%s/admin/bibcirculation/bibcirculationadmin.py/register_ill_request_with_no_recid_step3" method="get" >
            <input type=hidden name=book_info value="%s">
            <table class="bibcirctable">
              <tr width="200">
                <td align="center">
                  <select name="user_info" size="8" style='border: 1px solid #cfcfcf; width:80%%'>

            """ % (CFG_SITE_URL, book_info)

            for (ccid, name, email, phone, address, mailbox) in result:
                out += """
                       <option value ='%s,%s,%s,%s,%s,%s'>%s

                       """ % (ccid, name, email, phone, address, mailbox, name)

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
                    <input type=hidden name=request_details value="%s">
                    </form>
                    """ % (_("Select user"), request_details)

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

    def tmpl_register_ill_request_with_no_recid_step3(self, book_info, user_info, request_details, ln):
        """
        @param book_info: book's informations
        @type book_info: tuple

        @param user_info: user's informations
        @type user_info: tuple

        @param request_details: details about a given request
        @type request_details: tuple
        """

        (title, authors, place, publisher, year, edition, isbn) = book_info

        (_borrower_id, name, email, phone, address, mailbox) = user_info

        (period_of_interest_from, period_of_interest_to,
         additional_comments, only_edition)= request_details

        _ = gettext_set_language(ln)

        out = _MENU_

        out += """
        <style type="text/css"> @import url("/img/tablesorter.css"); </style>
        <div class="bibcircbottom">
        <form name="step3_form1" action="%s/admin/bibcirculation/bibcirculationadmin.py/register_ill_request_with_no_recid_step4" method="get" >
        <br />
                <table class="bibcirctable">
                  <tr>
                    <td width="200" valign='top'>
                    <input type=hidden name=book_info value="%s">
                    <input type=hidden name=request_details value="%s">
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
                        <tr>
                          <th width="100">%s</th>
                          <td>%s</td>
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
                     """ % (CFG_SITE_URL, book_info, request_details,
                            _("Item details"),
                            _("Name"), title,
                            _("Author(s)"), authors,
                            _("Place"), place,
                            _("Year"), year,
                            _("Publisher"), publisher,
                            _("Edition"), edition,
                            _("ISBN"), isbn,
                            _("ILL request details"),
                            _("Period of interest (From)"), period_of_interest_from,
                            _("Period of interest (To)"), period_of_interest_to,
                            _("Additional comments"), additional_comments,
                            _("Only this edition"), only_edition)

        out += """
                    <td width="200" valign='top'>

                            <table>
                                <tr align="center">
                                  <td class="bibcirctableheader">%s</td>
                                  <input type=hidden name=user_info value="%s">
                                </tr>
                            </table>
                            <table class="tablesorter" width="200" border="0" cellpadding="0" cellspacing="1">
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
                      """ % (_("Borrower details"), user_info,
                             _("Name"), name,
                             _("Email"), email,
                             _("Phone"), phone,
                             _("Address"), address,
                             _("Mailbox"), mailbox)


        #out += """
        #<style type="text/css"> @import url("/img/tablesorter.css"); </style>
        #<div class=bibcircbottom align="center">
        # <form name="step1_form1" action="%s/admin/bibcirculation/bibcirculationadmin.py/register_ill_request_with_no_recid_step4" method="get" >
        # <br />
        #    <table class="bibcirctable">
        #        <tr>
        #            <td width="500" valign='top'>
        #                <table>
        #                  <tr align="center">
        #                    <td class="bibcirctableheader">%s</td>
        #                    <input type=hidden name=book_info value="%s">
        #                  </tr>
        #                </table>
        #                <table class="tablesorterborrower" width:100%% border="0" cellpadding="0" cellspacing="1">
        #                    <tr width:100%%>
        #                      <th>%s</th>
        #                      <td>%s</td>
        #                    </tr>
        #                    <tr>
        #                      <th width="300">%s</th>
        #                      <td>%s</td>
        #                    </tr>
        #                    <tr>
        #                      <th width="300">%s</th>
        #                      <td width="300">%s</td>
        #                    </tr>
        #                    <tr>
        #                      <th width="100">%s</th>
        #                      <td>%s</td>
        #                    </tr>
        #                    <tr>
        #                      <th width="100">%s</th>
        #                      <td>%s</td>
        #                    </tr>
        #                    <tr>
        #                      <th width="100">%s</th>
        #                      <td>%s</td>
        #                    </tr>
        #                    <tr>
        #                      <th width="100">%s</th>
        #                      <td>%s</td>
        #                    </tr>
        #                </table>
        #    """ %(CFG_SITE_URL,
        #                     _("Item details"), book_info,
        #                     _("Name"), title,
        #                     _("Author(s)"), authors,
        #                     _("Place"), place,
        #                     _("Year"), year,
        #                     _("Publisher"), publisher,
        #                     _("Edition"), edition,
        #                     _("ISBN"), isbn,)
        #out += """
        #                <table>
        #                    <tr align="center">
        #                        <td class="bibcirctableheader">%s</td>
        #                            <input type=hidden name=request_details value="%s">
        #                    </tr>
        #                </table>
        #                <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">
        #                    <tr>
        #                      <th width="100">%s</th>
        #                      <td>%s</td>
        #                    </tr>
        #                    <tr>
        #                      <th width="100">%s</th>
        #                      <td>%s</td>
        #                    </tr>
        #                    <tr>
        #                      <th width="100">%s</th>
        #                      <td>%s</td>
        #                    </tr>
        #                    <tr>
        #                      <th width="100">%s</th>
        #                      <td>%s</td>
        #                    </tr>
        #                </table>
        #            </td>
        #            <td width="200" align='center' valign='top'>
        #               <table>
        #                 <tr>
        #                   <td>
        #
        #                   </td>
        #                 </tr>
        #               </table>
        #             </td>
        #            <td valign='top' align='center'>
        #
        #                    <table>
        #                        <tr align="center">
        #                          <td class="bibcirctableheader">%s</td>
        #                          <input type=hidden name=user_info value="%s">
        #                        </tr>
        #                    </table>
        #                    <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">
        #                        <tr>
        #                         <th width="100">%s</th>
        #                         <td>%s</td>
        #                        </tr>
        #                        <tr>
        #                         <th width="100">%s</th>
        #                         <td>%s</td>
        #                        </tr>
        #                        <tr>
        #                         <th width="100">%s</th>
        #                         <td>%s</td>
        #                        </tr>
        #                        <tr>
        #                         <th width="100">%s</th>
        #                         <td>%s</td>
        #                        </tr>
        #                        <tr>
        #                         <th width="100">%s</th>
        #                         <td>%s</td>
        #                        </tr>
        #                    </table>
        #
        #            </td>
        #        </tr>
        #    </table>
        #              """ % (
        #                     _("ILL request details"), request_details,
        #                     _("Period of interest - From"), period_of_interest_from,
        #                     _("Period of interest - To"), period_of_interest_to,
        #                     _("Additional comments"), additional_comments,
        #                     _("Only this edition"), only_edition,
        #                     _("Borrower details"), user_info,
        #                     _("Name"), name,
        #                     _("Email"), email,
        #                     _("Phone"), phone,
        #                     _("Address"), address,
        #                     _("Mailbox"), mailbox)

        out += """<br />
                  <table class="bibcirctable">
                    <tr align="center">
                      <td>
                        <input type=button value=%s
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit"
                       value=%s class="formbutton">
                      </td>
                    </tr>
                </table>""" % (_("Back"), _("Continue"))


        return out

    def tmpl_borrower_ill_details(self, result, borrower_id,
                                  ill_id, ln=CFG_SITE_LANG):
        """
        @param result: ILL request's informations:
        @type result: list

        @param borrower_id: identify the borrower. Primary key of crcBORROWER.
        @type borrower_id: int

        @param ill_id: identify the ILL request. Primray key of crcILLREQUEST
        @type ill_id: int

        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        out = """
        """
        out += _MENU_

        out += """
        <style type="text/css"> @import url("/img/tablesorter.css"); </style>
        <script src="/js/jquery.js" type="text/javascript"></script>
        <script src="/js/jquery.tablesorter.js" type="text/javascript"></script>
        <script type="text/javascript">
        $(document).ready(function() {
          $('#table_ill').tablesorter({widthFixed: true, widgets: ['zebra']})
        });
        </script>
        <div class="bibcircbottom">
        <br />
        <table id="table_ill" class="tablesorter" border="0" cellpadding="0" cellspacing="1">
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
         """% (_("Item"),
               _("Supplier"),
               _("Request date"),
               _("Expected date"),
               _("Arrival date"),
               _("Due date"),
               _("Status"),
               _("Library notes"))

        for (ill_id, book_info, supplier_id, request_date,
             expected_date, arrival_date, due_date, status,
             library_notes) in result:

            #get supplier name
            if supplier_id:
                library_name = db.get_library_name(supplier_id)
                library_link = create_html_link(CFG_SITE_URL +
                                                '/admin/bibcirculation/bibcirculationadmin.py/get_library_details',
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
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_item_details',
                                          {'recid': book_info['recid'], 'ln': ln},
                                          (book_title_from_MARC(int(book_info['recid']))))
            except KeyError:
                title_link = book_info['title']

            # links to notes pages
            lib_no_notes_link = create_html_link(CFG_SITE_URL +
                                                 '/admin/bibcirculation/bibcirculationadmin.py/get_ill_library_notes',
                                                 {'ill_id': ill_id},
                                                 (_("No notes")))

            lib_see_notes_link = create_html_link(CFG_SITE_URL +
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_ill_library_notes',
                                          {'ill_id': ill_id},
                                          (_("Notes about this ILL")))

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
            </tr>

            """ % (title_link, library_link, request_date,
                   expected_date, arrival_date, due_date, status,
                   notes_link)


        out += """
        </tbody>
        </table>
        <br />
        <table class="bibcirctable">
          <tr>
            <td>
              <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/get_borrower_details?borrower_id=%s'"
              value='%s' class='formbutton'>
            </td>
          </tr>
        </table>
        <br />
        </div>
        """ % (CFG_SITE_URL,
               borrower_id,
               _("Back"))

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

        out = """ """

        out += _MENU_

        out +="""
            <div class="bibcircbottom">
            <form name="borrower_notes" action="%s/admin/bibcirculation/bibcirculationadmin.py/get_ill_library_notes" method="get" >
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
                   _("Notes about acquisition"))

        key_array = ill_notes.keys()
        key_array.sort()

        for key in key_array:
            delete_note = create_html_link(CFG_SITE_URL +
                                           '/admin/bibcirculation/bibcirculationadmin.py/get_ill_library_notes',
                                           {'delete_key': key, 'ill_id': ill_id, 'ln': ln},
                                           (_("[delete]")))

            out += """<tr class="bibcirccontent">
                        <td class="bibcircnotes" width="160" valign="top" align="center"><b>%s</b></td>
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
                  <textarea name="library_notes" rows="5" cols="90" style='border: 1px solid #cfcfcf'></textarea>
                </td>
              </tr>
            </table>
            <br />
            <table class="bibcirctable">
              <tr>
                  <td>
                       <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/ordered_books'"
                       value=%s class='formbutton'>
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
               CFG_SITE_URL,
               _("Back"),
               _("Confirm"))

        return out

    def tmpl_get_expired_loans_with_requests(self, result, ln=CFG_SITE_LANG):
        """
        @param result: loans' informations:
        @param result: list

        """

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_

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
            <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1'"
            value='%s' class='formbutton'>
            </td>
            </table>
            <br />
            </div>
            """ % (_("No more requests are pending or waiting."),
                   CFG_SITE_URL,
                   _("Back to home"))

        else:

            out += """
            <style type="text/css"> @import url("/js/tablesorter/themes/blue/style.css"); </style>
            <style type="text/css"> @import url("/js/tablesorter/addons/pager/jquery.tablesorter.pager.css"); </style>

            <script src="/js/tablesorter/jquery.tablesorter.js" type="text/javascript"></script>
            <script src="/js/tablesorter/addons/pager/jquery.tablesorter.pager.js" type="text/javascript"></script>
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
         """% (_("Name"),
               _("Item"),
               _('Library'),
               _("Location"),
               _("From"),
               _("To"),
               _("Request date"),
               _("Actions"))

            for (request_id, recid, borrower_id, library_id, location, date_from, date_to, request_date) in result:

                borrower_name = db.get_borrower_name(borrower_id)
                library_name = db.get_library_name(library_id)


                title_link = create_html_link(CFG_SITE_URL +
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_item_details',
                                          {'recid': recid, 'ln': ln},
                                          (book_title_from_MARC(recid)))

                if borrower_name:
                    borrower_link = create_html_link(CFG_SITE_URL +
                                             '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_details',
                                             {'borrower_id': borrower_id, 'ln': ln},
                                             (borrower_name))
                else:
                    borrower_link = str(borrower_id)


                out += """
                <script type="text/javascript">
                function confirmation(id){
                  var answer = confirm("Delete this request?")
                  if (answer){
                    window.location = "%s/admin/bibcirculation/bibcirculationadmin.py/get_expired_loans_with_requests?request_id="+id;
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
                        no-repeat; width: 75px; text-align: right;"
                        onClick="confirmation(%s)"
                        onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
                        class="bibcircbutton">
                    <input type=button style="background: url(/img/dialog-yes.png) no-repeat; width: 150px; text-align: right;"
                        onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/associate_barcode?request_id=%s&recid=%s&borrower_id=%s'"
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
                       _("Associate barcode"))

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
                        <input type=button style="background: url(/img/document-print.png) no-repeat; width: 135px; text-align: right;"
                        onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/get_pending_requests?print_data=true'"
                        onmouseover="this.className='bibcircbuttonover'" onmouseout="this.className='bibcircbutton'"
                        value='%s' class="bibcircbutton">
                      </td>
                    </tr>
                  </table>
                  <br />
                  </div>
                  """ % (CFG_SITE_URL,
                         _("Printable format"))


        return out

    def tmpl_register_ill_book_request(self, infos, ln=CFG_SITE_LANG):
        """
        @param infos: informations
        @type infos: list

        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += _MENU_

        out += """
        <div class=bibcircbottom align="center">
        <form name="search_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/register_ill_book_request_result"
        method="get" >
        <br />
        <br />
        <div class="infoboxmsg"><strong>%s</strong></div>
        <br />
        <input type=hidden name=start value="0">
        <input type=hidden name=end value="10">
        <table class="bibcirctable">
          <tr align="center">
            <td class="bibcirctableheader">Search item by
              <input type="radio" name="f" value="" checked>any field
              <input type="radio" name="f" value="barcode">barcode
              <input type="radio" name="f" value="author">author
              <input type="radio" name="f" value="title">title
              <br />
              <br />
            </td>
          </tr>
          <tr align="center">
            <td><input type="text" size="50" name="p" style='border: 1px solid #cfcfcf'></td>
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

        """ % (CFG_SITE_URL, _("Check if the book already exists on Invenio,"\
                               + " before to send your ILL request."),
               _("Back"), _("Search"))

        return out

    def tmpl_register_ill_book_request_result(self, result, ln=CFG_SITE_LANG):
        """
        @param result: book's information
        @type result: list

        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = _MENU_

        if len(result) == 0:
            out += """
            <div class="bibcircbottom" align="center">
            <br />
            <div class="infoboxmsg">%s</div>
            <br />
            """ % (_("0 items found."))

        else:
            out += """
        <style type="text/css"> @import url("/img/tablesorter.css"); </style>
        <div class="bibcircbottom">
        <form name="search_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/register_ill_request_with_no_recid_step1" method="get" >
        <br />
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
        """ % (CFG_SITE_URL,len(result), _("Title"),
               _("Author"), _("Publisher"),
               _("No. Copies"))

            for recid in result:

                (book_author, book_editor, book_copies) = get_item_info_for_search_result(recid)

                title_link = create_html_link(CFG_SITE_URL +
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_item_details',
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

    def tmpl_register_ill_book_request_from_borrower_page(self, infos, borrower_id, ln=CFG_SITE_LANG):
        """
        @param infos: informations
        @type infos: list

        @param borrower_id: identify the borrower. Primary key of crcBORROWER.
        @type borrower_id: int

        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += _MENU_

        out += """
        <div class=bibcircbottom align="center">
        <form name="search_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/register_ill_book_request_from_borrower_page_result"
        method="get" >
        <input type=hidden name=borrower_id value=%s>
        <br />
        <br />
        <div class="infoboxmsg"><strong>%s</strong></div>
        <br />
        <input type=hidden name=start value="0">
        <input type=hidden name=end value="10">
        <table class="bibcirctable">
          <tr align="center">
            <td class="bibcirctableheader">Search item by
              <input type="radio" name="f" value="" checked>any field
              <input type="radio" name="f" value="barcode">barcode
              <input type="radio" name="f" value="author">author
              <input type="radio" name="f" value="title">title
              <br />
              <br />
            </td>
          </tr>
          <tr align="center">
          <td><input type="text" size="50" name="p" style='border: 1px solid #cfcfcf'></td>
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
        <form>

        """ % (CFG_SITE_URL, borrower_id,
               _("Check if the book already exists on Invenio,"\
                 " before to send your ILL request."),
               _("Back"), _("Search"))

        return out

    def tmpl_register_ill_book_request_from_borrower_page_result(self, result, ln=CFG_SITE_LANG):
        """
        @param result: book's information
        @type result: list

        @param borrower_id: identify the borrower. Primary key of crcBORROWER.
        @type borrower_id: int

        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = """  """

        out += _MENU_

        if len(result) == 0:
            out += """
            <div class="bibcircbottom" align="center">
            <br />
            <div class="infoboxmsg">%s</div>
            <br />
            """ % (_("0 items found."))

        else:
            out += """
        <style type="text/css"> @import url("/img/tablesorter.css"); </style>
        <div class="bibcircbottom">
        <br />
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
               _("No. Copies"))

            for recid in result:

                (book_author, book_editor, book_copies) = get_item_info_for_search_result(recid)

                title_link = create_html_link(CFG_SITE_URL +
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_item_details',
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

    def tmpl_register_ill_request_from_borrower_page_step1(self, infos, borrower_id, ln=CFG_SITE_LANG):
        """
        @param infos: informations
        @type infos: list

        @param borrower_id: identify the borrower. Primary key of crcBORROWER.
        @type borrower_id: int
        """

        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += _MENU_


        out += """
        <br />
        <br />
          <div class="bibcircbottom" align="center">
          <div class="infoboxmsg"><strong>%s</strong></div>
          <br />
          <br />
          <style type="text/css"> @import url("/img/tablesorter.css"); </style>
           <form name="display_ill_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/register_ill_request_from_borrower_page_step2" method="get">
           <input type=hidden name=borrower_id value=%s>
             <table class="bibcirctable">
                  <tr align="center">
                    <td class="bibcirctableheader" width="10">%s</td>
                  </tr>
                </table>
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

           """  % (_("Book does not exists on Invenio. Please fill the following form."),
                   CFG_SITE_URL, borrower_id,
                   _("Item details"),
                   _("Book title"),
                   _("Author(s)"),
                   _("Place"),
                   _("Publisher"),
                   _("Year"),
                   _("Edition"),
                   _("ISBN"))



        conditions_link = """<a href="http://library.web.cern.ch/library/Library/ill_faq.html" target="_blank">conditions</a>"""

        out += """
        <script type="text/javascript" language='JavaScript' src="/jsCalendar/calendar.js"></script>
        <script type="text/javascript" language='JavaScript' src="/jsCalendar/calendar-setup.js"></script>
        <script type="text/javascript" language='JavaScript' src="/jsCalendar/calendar-en.js"></script>
        <style type="text/css"> @import url("/jsCalendar/calendar-blue.css"); </style>

             <table class="bibcirctable">
                <tr align="center">
                     <td class="bibcirctableheader">%s</td>
                </tr>
             </table>
             <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">
               <tr>
                <th width="150">%s</th>
                <td>
                       <input type="text" size="12" id="%s" name="period_of_interest_from" value="" style='border: 1px solid #cfcfcf'>
                       <img src="/jsCalendar/jsCalendar.gif" alt="select period of interest" id="%s"
                       onmouseover="this.style.background='red';" onmouseout="this.style.background=''"
                       >
                       <script type="text/javascript" language='JavaScript'>
                       Calendar.setup({
                           inputField     :    '%s',
                           ifFormat       :    '%%Y-%%m-%%d',
                           button         :    '%s'
                           });
                       </script>
                    </td>
                </tr>
                <tr>
                <th width="150">%s</th>
                <td>
                       <input type="text" size="12" id="%s" name="period_of_interest_to" value="" style='border: 1px solid #cfcfcf'>
                       <img src="/jsCalendar/jsCalendar.gif" alt="select period of interest" id="%s"
                       onmouseover="this.style.background='red';" onmouseout="this.style.background=''"
                       >
                       <script type="text/javascript" language='JavaScript'>
                       Calendar.setup({
                           inputField     :    '%s',
                           ifFormat       :    '%%Y-%%m-%%d',
                           button         :    '%s'
                           });
                       </script>
                    </td>
                </tr>
                <tr>
                   <th valign="top" width="150">%s</th>
                   <td><textarea name='additional_comments' rows="6" cols="30"
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
                       <input type=button value=%s
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit"
                       value=%s class="formbutton">

                  </td>
                 </tr>
             </table>
             </form>
             <br />
             <br />
             </div>
             """ % (_("ILL request details"), _("Period of interest - From"),
                    "period_of_interest_from",
                    "jsCal1", "period_of_interest_from", "jsCal1",
                    _("Period of interest - To"), "period_of_interest_to",
                    "jsCal2", "period_of_interest_to", "jsCal2",
                    _("Additional comments"),
                    _("Borrower accepts the %s of the service in particular the return of books in due time." % (conditions_link)),
                    _("Borrower wants this edition only."),
                    _("Back"), _("Continue"))


        return out

    def tmpl_register_ill_request_from_borrower_page_step3(self, book_info, user_info, request_details, ln):
        """
        @param book_info: book's informations
        @type book_info: tuple

        @param user_info: user's informations
        @type user_info: tuple

        @param request_details: details about a given request
        @type request_details: tuple
        """

        (title, authors, place, publisher, year, edition, isbn) = book_info

        (_borrower_id, name, email, phone, address, mailbox) = user_info

        (period_of_interest_from, period_of_interest_to,
         additional_comments, only_edition)= request_details

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_

        out += """
        <style type="text/css"> @import url("/img/tablesorter.css"); </style>
        <div class=bibcircbottom align="center">
        <br />
        <br />
         <form name="step1_form1" action="%s/admin/bibcirculation/bibcirculationadmin.py/register_ill_request_from_borrower_page_step4" method="get" >
                 <table>
                   <tr align="center">
                     <td class="bibcirctableheader">%s</td>
                     <input type=hidden name=book_info value="%s">
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
                         <tr align="center">
                           <td class="bibcirctableheader">%s</td>
                           <input type=hidden name=request_details value="%s">
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
                      </table>
                      <table>
                         <tr align="center">
                           <td class="bibcirctableheader">%s</td>
                           <input type=hidden name=user_info value="%s">
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
                      </table>

                      """ % (CFG_SITE_URL,
                             _("Item details"), book_info,
                             _("Name"), title,
                             _("Author(s)"), authors,
                             _("Place"), place,
                             _("Year"), year,
                             _("Publisher"), publisher,
                             _("Edition"), edition,
                             _("ISBN"), isbn,
                             _("ILL request details"), request_details,
                             _("Period of interest - From"), period_of_interest_from,
                             _("Period of interest - To"), period_of_interest_to,
                             _("Additional comments"), additional_comments,
                             _("Only this edition"), only_edition or 'No',
                             _("Borrower details"), user_info,
                             _("Name"), name,
                             _("Email"), email,
                             _("Phone"), phone,
                             _("Address"), address,
                             _("Mailbox"), mailbox)

        out += """<br />
                  <table class="bibcirctable">
                    <tr align="center">
                      <td>
                        <input type=button value=%s
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit"
                       value=%s class="formbutton">
                      </td>
                    </tr>
                </table>""" % (_("Back"), _("Continue"))


        return out

    def tmpl_register_ill_article_request_step1(self, infos, ln=CFG_SITE_LANG):
        """
        @param infos: informations
        @type infos: list
        """

        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += _MENU_


        out += """
        <br />
        <br />
          <div class="bibcircbottom" align="center">
          <br />
          <br />
          <style type="text/css"> @import url("/img/tablesorter.css"); </style>
           <form name="display_ill_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/register_ill_article_request_step2" method="get">
             <table class="bibcirctable">
                  <tr align="center">
                    <td class="bibcirctableheader" width="10">%s</td>
                  </tr>
                </table>
                <table class="tablesorterborrower" border="0" cellpadding="0" cellspacing="1">
                    <tr>
                        <th width="100">%s</th>
                        <td>
                          <input type="text" size="45" name="periodical_title" style='border: 1px solid #cfcfcf'>
                        </td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>
                          <input type="text" size="45" name="article_title" style='border: 1px solid #cfcfcf'>
                        </td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>
                          <input type="text" size="45" name="author" style='border: 1px solid #cfcfcf'>
                        </td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>
                          <input type="text" size="30" name="report_number" style='border: 1px solid #cfcfcf'>
                        </td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>
                          <input type="text" size="30" name="volume" style='border: 1px solid #cfcfcf'>
                        </td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>
                          <input type="text" size="30" name="issue" style='border: 1px solid #cfcfcf'>
                        </td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>
                          <input type="text" size="30" name="page" style='border: 1px solid #cfcfcf'>
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
                          <input type="text" size="30" name="budget_code" style='border: 1px solid #cfcfcf'>
                        </td>
                     </tr>
                     <tr>
                        <th width="100">%s</th>
                        <td>
                          <input type="text" size="30" name="issn" style='border: 1px solid #cfcfcf'>
                        </td>
                     </tr>
                </table>


           <br />

           """  % (CFG_SITE_URL,
                   _("Article details"),
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


        #conditions_link = """<a href="http://library.web.cern.ch/library/Library/ill_faq.html" target="_blank">conditions</a>"""

        out += """
            <script type="text/javascript" language='JavaScript' src="%s/js/jquery-ui.min.js"></script>

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
                        <input type="text" size="12" id="date_picker1" name="period_of_interest_from" value="%s" style='border: 1px solid #cfcfcf'>
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
                        <input type="text" size="12" id="date_picker2" name="period_of_interest_to" value="%s" style='border: 1px solid #cfcfcf'>
                    </td>
                </tr>
                <tr>
                   <th valign="top" width="150">%s</th>
                   <td><textarea name='additional_comments' rows="6" cols="30"
                   style='border: 1px solid #cfcfcf'></textarea></td>
                </tr>
              </table>
              <br />
              <table class="bibcirctable">
                <tr align="center">
                  <td>
                       <input type=button value=%s
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit"
                       value=%s class="formbutton">

                  </td>
                 </tr>
             </table>
             </form>
             <br />
             <br />
             </div>
             """ % (CFG_SITE_URL,_("ILL request details"),
                    _("Period of interest - From"), CFG_SITE_URL, datetime.date.today().strftime('%Y-%m-%d'),
                    _("Period of interest - To"), CFG_SITE_URL, (datetime.date.today() + datetime.timedelta(days=365)).strftime('%Y-%m-%d'),
                    _("Additional comments"),
                    _("Back"), _("Continue"))

        return out


    def tmpl_register_ill_article_request_step2(self, article_info, request_details,
                                                result, key, string, infos, ln):
        """
        @param article_info: information about article
        @type article_info: tuple

        @param request_details: details about a given ILL request
        @type request_details: tuple

        @param result: result with borrower's information
        @param result: list

        @param key: field (name, email, etc...)
        @param key: string

        @param string: pattern
        @type string: string

        @param infos: informations
        @type infos: list
        """

        (periodical_title, article_title, author, report_number,
         volume, issue, page, year, issn) = article_info

        (period_of_interest_from, period_of_interest_to,
         additional_comments)= request_details

        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += _MENU_

        out += """
        <style type="text/css"> @import url("/img/tablesorter.css"); </style>
        <div class="bibcircbottom">
         <form name="step1_form1" action="%s/admin/bibcirculation/bibcirculationadmin.py/register_ill_article_request_step2" method="get" >
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
                            _("ISSN"), issn, issn,
                            _("ILL request details"),
                            _("Period of interest - From"), period_of_interest_from, period_of_interest_from,
                            _("Period of interest - To"), period_of_interest_to, period_of_interest_to,
                            _("Additional comments"), additional_comments, additional_comments)

        out += """
        <td valign='top' align='center'>
         <table>

            """

        if CFG_CERN_SITE == 1:

            out += """
                 <tr>
                   <td class="bibcirctableheader" align="center">Search user by

                   """

            if key == 'email':
                out += """
                   <input type="radio" name="key" value="ccid">ccid
                   <input type="radio" name="key" value="name">name
                   <input type="radio" name="key" value="email" checked>email
                   """

            elif key == 'name':
                out += """
                   <input type="radio" name="key" value="ccid">ccid
                   <input type="radio" name="key" value="name" checked>name
                   <input type="radio" name="key" value="email">email
                   """

            else:
                out += """
                   <input type="radio" name="key" value="ccid" checked>ccid
                   <input type="radio" name="key" value="name">name
                   <input type="radio" name="key" value="email">email
                   """

        else:
            out += """
                 <tr>
                   <td class="bibcirctableheader" align="center">Search borrower by

                   """

            if key == 'email':
                out += """
                   <input type="radio" name="key" value="id">id
                   <input type="radio" name="key" value="name">name
                   <input type="radio" name="key" value="email" checked>email
                   """

            elif key == 'id':
                out += """
                   <input type="radio" name="key" value="id" checked>id
                   <input type="radio" name="key" value="name">name
                   <input type="radio" name="key" value="email">email
                   """

            else:
                out += """
                   <input type="radio" name="key" value="id">id
                   <input type="radio" name="key" value="name" checked>name
                   <input type="radio" name="key" value="email">email
                   """

        out += """
                    <br><br>
                    </td>
                    </tr>
                    <tr>
                    <td align="center">
                    <input type="text" size="40" id="string" name="string"  value='%s' style='border: 1px solid #cfcfcf'>
                    </td>
                    </tr>
                    <tr>
                    <td align="center">
                    <br>
                    <input type="submit" value="Search" class="formbutton">
                    </td>
                    </tr>

                   </table>
          </form>

        """ % (string or '')

        if result:
            out += """
            <br />
            <form name="step1_form2" action="%s/admin/bibcirculation/bibcirculationadmin.py/register_ill_article_request_step3" method="get" >
            <input type=hidden name=book_info value="%s">
            <table class="bibcirctable">
              <tr width="200">
                <td align="center">
                  <select name="user_info" size="8" style='border: 1px solid #cfcfcf; width:40%%'>

            """ % (CFG_SITE_URL, article_info)

            for (ccid, name, email, phone, address, mailbox) in result:
                out += """
                       <option value ='%s,%s,%s,%s,%s,%s'>%s

                       """ % (ccid, name, email, phone, address, mailbox, name)

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
                    <input type=hidden name=request_details value="%s">
                    </form>
                    """ % (_("Select user"), request_details)

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

        @param infos: informations
        @type infos: list

        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += _MENU_

#<input type=hidden name=start value="0">
#<input type=hidden name=end value="10">

        out += """
        <div class="bibcircbottom">
        <link rel=\"stylesheet\" href=\"%s/img/jquery-ui.css\" type=\"text/css\" />
        <script type="text/javascript" language='JavaScript' src="%s/js/jquery-ui.min.js"></script>
        <form name="search_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/ill_search_result" method="get" >
        <br />
        <br />
        <br />

        <table class="bibcirctable">
          <tr align="center">
            <td class="bibcirctableheader">Search ILL request by
              <input type="radio" name="f" value="title" checked>title
              <input type="radio" name="f" value="ILL_request_ID">ill_request_id
            </td>
          </tr>
        </table>

        <br />
        <table class="bibcirctable">
            <tr align="center" width=10>
                <td width=10><input type="text" size="50" name="p" style='border: 1px solid #cfcfcf'></td>
            </tr>
        </table>
        """ % (CFG_SITE_URL,CFG_SITE_URL,CFG_SITE_URL)

        out += """
        <br />
        <table align="center">

            <tr align="center">
                <td class="bibcirctableheader" align="right">date restriction:    </td>
                <td class="bibcirctableheader" align="right">From</td>
                <td align="left">
                <script type="text/javascript">
                    $(function(){
                        $("#date_picker1").datepicker({dateFormat: 'yy-mm-dd', showOn: 'button', buttonImage: "%s/img/calendar.gif", buttonImageOnly: true});
                    });
                </script>
                <input type="text" size="12" id="date_picker1" name="date_from" value="%s" style='border: 1px solid #cfcfcf'>
                </td>
            </tr>

            <tr align="center">
                <td class="bibcirctableheader" align="right"></td>
                <td class="bibcirctableheader" align="right">To</td>
                <td align="left">
                    <script type="text/javascript">
                        $(function(){
                            $("#date_picker2").datepicker({dateFormat: 'yy-mm-dd', showOn: 'button', buttonImage: "%s/img/calendar.gif", buttonImageOnly: true});
                        });
                    </script>
                    <input type="text" size="12" id="date_picker2" name="date_to" value="%s" style='border: 1px solid #cfcfcf'>
                </td>
            </tr>
        </table>

        """ % (CFG_SITE_URL, "the beginning", CFG_SITE_URL, "now")

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
