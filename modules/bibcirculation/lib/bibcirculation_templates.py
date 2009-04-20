# -*- coding: utf-8 -*-
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

""" Templates for bibcirculation module """

__revision__ = "$Id$"

import datetime
import time

from invenio.urlutils import create_html_link
from invenio.config import CFG_SITE_URL, CFG_SITE_LANG, CFG_CERN_SITE
from invenio.messages import gettext_set_language



import invenio.bibcirculation_dblayer as db
from invenio.bibcirculation_utils import get_book_cover, \
      book_information_from_MARC, \
      book_title_from_MARC, \
      renew_loan_for_X_days, \
      get_item_info_for_search_result


_MENU_ = """

      <div id="cdlhead">
      <map name="Navigation_Bar" id="cdlnav">
      <div id="bibcircmenu" class="cdsweb">
      <h2><a name="localNavLinks">Main navigation links:</a></h2>
      <ul>
      <li>
        <a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py">Home</a>
      </li>

      <li>
        <a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1">Loans</a>
     </li>

     <li>
        <a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/loan_return">Return</a>
     </li>

     <li>
        <a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/borrower_search">Request</a>
     </li>

     <li class="hassubmenu">
         <a href='#'>Borrowers</a>
         <ul class="subsubmenu" style="width:16.5em;">
          <li><a href = "%(url)s/admin/bibcirculation/bibcirculationadmin.py/borrower_search">Search...</a></li>
          <!-- <li><a href = "%(url)s/admin/bibcirculation/bibcirculationadmin.py/borrower_notification">Notify</a></li> -->
          <li><a href = "%(url)s/admin/bibcirculation/bibcirculationadmin.py/add_new_borrower_step1">Add new borrower</a></li>
          <li><a href = "%(url)s/admin/bibcirculation/bibcirculationadmin.py/update_borrower_info_step1">Update info</a></li>
            </ul>
        </li>

     <li>
        <a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/item_search">Items</a>
     </li>
<!--
     <li class="hassubmenu">
         <a href='#'>Items</a>
         <ul class="subsubmenu" style="width:16.5em;">
          <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/item_search">Search...</a></li>
          <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/new_item">Add new item</a></li>
          <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/add_new_copy_step1">Add new copy</a></li>
          <li><a href='#'># - Remove</a></li>
          <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/update_item_info_step1">Update info</a></li>
         </ul>
        </li>
-->

    <li class="hassubmenu">
         <a href='#'>Lists</a>
         <ul class="subsubmenu" style="width:17.5em;">
          <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/all_loans">Current loans</a></li>
             <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/all_expired_loans">Overdue loans</a></li>
             <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/get_pending_requests">On Shelve items with holds</a></li>
             <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/get_waiting_requests">On Loan items with holds</a></li>
             <!-- <li><a href='#'># - Stats</a></li> -->
            </ul>
    </li>

<!--
     <li class="hassubmenu">
         <a href='#'>Loans</a>
         <ul class="subsubmenu" style="width:16.5em;">
          <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1">On library desk</a></li>
             <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/loan_return">Return book</a></li>
             <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/all_loans">List of all loans</a></li>
             <li><a href='#'># - Stats</a></li>
            </ul>
        </li>

     <li class="hassubmenu">
         <a href='#'>Requests</a>
         <ul class="subsubmenu" style="width:16.5em;">
             <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/get_pending_requests">List of pending requests</a></li>
             <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/all_requests">List of hold requests</a></li>
             <li><a href='#'># - Stats</a></li>
            </ul>
        </li>
-->
     <li class="hassubmenu">
         <a href='#'>Libraries</a>
         <ul class="subsubmenu" style="width:16.5em;">
             <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/search_library_step1">Search...</a></li>
             <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/add_new_library_step1">Add new library</a></li>
             <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/update_library_info_step1">Update info</a></li>
             <!-- <li><a href='#'># - Stats</a></li> -->
            </ul>
        </li>

     <li class="hassubmenu">
         <a href='#'>Help</a>
         <ul class="subsubmenu" style="width:16.5em;">
          <li><a href="%(url)s/help/admin/bibcirculation-admin-guide" target="_blank">Admin guide</a></li>
             <!-- <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/help_contactsupport">Contact Support</a></li> -->
            </ul>
        </li>

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


    def tmpl_holdings_information2(self, recid, holdings_info,
                                   ln=CFG_SITE_LANG):
        """
        This template is used in the user interface. In this template
        it is possible to see all details (loan period, number of copies, location, etc)
        about a book.
        """

        _ = gettext_set_language(ln)

        if not holdings_info:
            return _("This item has no holdings.")

        out = """ """

        out += """
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

        for (barcode, library, collection, location, description, loan_period, status, due_date) in holdings_info:
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
                          <td class="bibcirccontent" align='right'>
                          <input type=button onClick="location.href='%s/record/%s/holdings/request?barcode=%s'"
                          value='%s' class="formbutton"></td>
                     </tr>

                """ % (barcode, library, collection, location,
                       description, loan_period, status, due_date,
                       CFG_SITE_URL, recid, barcode,
                       _("Request"))

        out += """
           </table>
           <br \>

           """

        return out


    def tmpl_borrower_search_result(self, result, ln=CFG_SITE_LANG):
        """
        When the admin features 'borrower_seach' is used, this template
        show the result.

        @param result: search result
        @param ln: language
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_

        out += """
        <div class="bibcircbottom">
        </form>
        <br \>
        <table class="bibcirctable">
          <tr align="center">
            <td class="bibcirccontent">
              <strong>%s borrowers found</strong>
            </td>
          </tr>
        </table>
        <br \>
        <table class="bibcirctable">

        """ % (len(result))


        for (borrower_id, name) in result:

            borrower_link = create_html_link(CFG_SITE_URL +
                                             '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_details',
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
             <br \>
             """

        out += """
        <table class="bibcirctable">
             <tr align="center">
                  <td><input type=button value=%s onClick="history.go(-1)" class="formbutton"></td>
             </tr>
        </table>
        <br />
        <br \>
        <br \>
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

        renew_all_link = create_html_link(CFG_SITE_URL +
                                          '/yourloans/display',
                                          {'borrower_id': borrower_id},
                                          (_("Renew all loans")))

        loanshistoricaloverview_link = create_html_link(CFG_SITE_URL +
                                            '/yourloans/loanshistoricaloverview',
                                            {'ln': ln},
                                            (_("Loans - historical overview")))

        out = self.tmpl_infobox(infos, ln)

        if len(loans) == 0:
            out += """
            <div class="bibcirctop_bottom">
            <br />
            <br \>
            <table class="bibcirctable_contents">
                 <td align="center" class="bibcirccontent">%s</td>
            </table>
            <br />
            <br \>
            """ % (_("You don't have any book on loan."))

        else:
            out += """<div class="bibcirctop_bottom">
                        <br />
                    <table class="bibcirctable">
                     <tr>
                     <td class="bibcirctableheader" width="220">%s</td>
                     <td class="bibcirctableheader" width="100">%s</td>
                     <td class="bibcirctableheader" width="100">%s</td>
                     <td class="bibcirccontent" width="700"></td>
                     </tr>
                     """ % (_("Item"),
                            _("Loaned on"),
                            _("Due date"))

            for(recid, barcode, loaned_on, due_date) in loans:

                renew_link = create_html_link(CFG_SITE_URL +
                                         '/yourloans/display',
                                         {'barcode': barcode},
                                         (_("Renew")))

                out += """
                <tr>
                <td class="bibcirccontent" width="220">%s</td>
                <td class="bibcirccontent" width="100">%s</td>
                <td class="bibcirccontent" width="100">%s</td>
                <td class="bibcirccontent" width="700">%s</td>
                </tr>
                """ % (book_title_from_MARC(recid),
                       loaned_on,
                       due_date,
                       renew_link)



            out += """</table>
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
                   <br /> <br \>
                   <table class="bibcirctable_contents">
                   <td align="center" class="bibcirccontent">%s</td>
                   </table>
                   <br /> <br \>
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
                   <table class="bibcirctable">
                   <tr>
                   <td class="bibcirctableheader" width="220">%s</td>
                   <td class="bibcirctableheader" width="100">%s</td>
                   <td class="bibcirctableheader" width="100">%s</td>
                   <td class="bibcirctableheader" width="700"></td>
                   </tr>
                   """ % (_("Your Requests"),
                          _("Item"),
                          _("Request date"),
                          _("Status"))

            for(request_id, recid, request_date, status) in requests:

                cancel_request_link = create_html_link(CFG_SITE_URL +
                                                       '/yourloans/display',
                                                       {'request_id': request_id},
                                                       (_("Cancel")))
                out += """
                <tr>
                <td class="bibcirccontent" width="220">%s</td>
                <td class="bibcirccontent" width="100">%s</td>
                <td class="bibcirccontent" width="100">%s</td>
                <td class="bibcirccontent" width="700">%s</td>
                </tr>
                """ % (book_title_from_MARC(recid), request_date,
                       status, cancel_request_link)

            out +="""
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
                    <br /> <br \>
                    <table class="bibcirctable">
                     <tr>
                     <td class="bibcirctableheader" width="220">%s</td>
                     <td class="bibcirctableheader" width="100">%s</td>
                     <td class="bibcirctableheader" width="100">%s</td>
                     <td class="bibcirctableheader" width="700">%s</td>
                     </tr>
                     """ % (_("Item"),
                            _("Loaned on"),
                            _("Returned on"),
                            _("No of renewalls"))

        for(recid, loaned_on, returned_on, nb_renewalls) in result:

            out += """
                <tr>
                <td class="bibcirccontent" width="220">%s</td>
                <td class="bibcirccontent" width="100">%s</td>
                <td class="bibcirccontent" width="100">%s</td>
                <td class="bibcirccontent" width="700">%s</td>
                </tr>
                """ % (book_title_from_MARC(recid), loaned_on,
                       returned_on, nb_renewalls)

        out += """</table>
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
        @param recid: recID - CDS Invenio record identifier
        @param barcode: book's barcode
        @param ln: language
        """

        _ = gettext_set_language(ln)

        today = datetime.date.today()
        out = """
        <form name="request_form" action="%s/record/%s/holdings/send" method="get" >
        <div class="bibcirctableheader" align="center">%s</div>
        <br />
             <table class="bibcirctable_contents">
                  <tr>
                       <td class="bibcirctableheader" width="30">%s</td>
                       <td class="bibcirctableheader" width="30">%s</td>
                       <td class="bibcirctableheader" width="30">%s</td>
                       <td class="bibcirctableheader" width="30">%s</td>
                  </tr>
        """ % (CFG_SITE_URL,
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
        <br /> <br \>
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
        <br /> <br \>
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

    def tmpl_new_request_send(self, message, ln=CFG_SITE_LANG):
        """
        This template is used in the user interface.

        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = """
        <br /> <br \>
        <table class="bibcirctable">
        <tr>
        <td class="bibcirccontent" width="30">%s</td>
        </tr>
        <tr>
        <td class="bibcirccontent" width="30">%s<a href="%s">%s</a>%s</td>
        </tr>
        </table>
        <br /> <br \>
        <table class="bibcirctable">
        <td><input type=button onClick="location.href='%s'" value='%s' class='formbutton'></td>
        </table>
        <br /> <br \>
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

        out = """
              """
        out += _MENU_

        out += """
        <div class="bibcircbottom">
        <br /> <br \>
             <table class="bibcirctable">
             <td class="bibcirccontent" width="30">%s</td>
             </table>
             <br /> <br \>
             <table class="bibcirctable">
             <td><input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py'" value=%s class='formbutton'></td>
             </table>
        <br /> <br \>
        </div>
        """ % (_("A new loan has been registered."),
               CFG_SITE_URL,
               _("Back to home"))

        return out

    def tmpl_get_pending_requests(self, result, ln=CFG_SITE_LANG):
        """
        Template for the admin interface. Show pending requests(all, on loan, available)

        @param result: items with status = 'pending'
        @param ln: language
        """

        _ = gettext_set_language(ln)


        out = """
        """
        out += _MENU_

        if len(result) == 0:
            out += """
            <div class="bibcircbottom">
            <br /> <br \>            <br /> <br \>
            <table class="bibcirctable_contents">
                 <td class="bibcirccontent" align="center">%s</td>
            </table>
            <br /> <br \>            <br />
            <table class="bibcirctable_contents">
            <td align="center">
            <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py'" value='%s' class='formbutton'>
            </td>
            </table>
            <br \>
            </div>
            """ % (_("No more requests are pending."),
                   CFG_SITE_URL,
                   _("Back to home"))

        else:

            out += """
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
                       <td class="bibcirctableheader" align="center">%s</td>
                    </tr>
         """% (_("Name"),
               _("Item"),
               _('Library'),
               _("Location"),
               _("From"),
               _("To"),
               _("Request date"),
               _("Options"))

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
                <tr onMouseOver="this.className='highlight'" onMouseOut="this.className='normal'">
                 <td class="bibcirccontent">%s</td>
                 <td class="bibcirccontent">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td align="center" class="bibcirccontent">
                 <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/get_pending_requests?request_id=%s'"
                 value='%s' class="formbutton">
                 <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/associate_barcode?request_id=%s&recid=%s&borrower_id=%s'"
                 value='%s' class="formbutton">
                 </td>
                </tr>
                """ % (borrower_link,
                       title_link,
                       library,
                       location,
                       date_from,
                       date_to,
                       request_date,
                       CFG_SITE_URL,
                       request_id,
                       _("Cancel"),
                       CFG_SITE_URL,
                       request_id,
                       recid,
                       borrower_id,
                       _("Associate barcode"))

            out += """</table>
                  <br />
                  <table class="bibcirctable">
                       <tr>
                            <td>
                                 <input type="button" onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/get_pending_requests?print_data=true'"
                                 value="%s" class="formbutton">
                            </td>
                           </tr>
                  </table>
                  <br />
                  </div>
                  """ % (CFG_SITE_URL,
                         _("Printable format"))


        return out

    def tmpl_get_waiting_requests(self, result, ln=CFG_SITE_LANG):
        """
        Template for the admin interface. Show pending requests(all, on loan, available)

        @param result: items with status = 'pending'
        @param ln: language
        """

        _ = gettext_set_language(ln)


        out = """
        """
        out += _MENU_

        if len(result) == 0:
            out += """
            <div class="bibcircbottom">
            <br /> <br \>            <br /> <br \>
            <table class="bibcirctable_contents">
                 <td class="bibcirccontent" align="center">%s</td>
            </table>
            <br /> <br \>            <br />
            <table class="bibcirctable_contents">
            <td align="center">
            <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py'" value='%s' class='formbutton'>
            </td>
            </table>
            <br \>
            </div>
            """ % (_("No more requests are waiting."),
                   CFG_SITE_URL,
                   _("Back to home"))

        else:

            out += """
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
                       <td class="bibcirctableheader" align="center">%s</td>
                    </tr>
         """% (_("Name"),
               _("Item"),
               _('Library'),
               _("Location"),
               _("From"),
               _("To"),
               _("Request date"),
               _("Options"))

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
                <tr onMouseOver="this.className='highlight'" onMouseOut="this.className='normal'">
                 <td class="bibcirccontent">%s</td>
                 <td class="bibcirccontent">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td align="center" class="bibcirccontent">
                 <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/get_waiting_requests?request_id=%s'"
                 value='%s' class="formbutton">
                 <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/associate_barcode?request_id=%s&recid=%s&borrower_id=%s'"
                 value='%s' class="formbutton">
                 </td>
                </tr>
                """ % (borrower_link,
                       title_link,
                       library,
                       location,
                       date_from,
                       date_to,
                       request_date,
                       CFG_SITE_URL,
                       request_id,
                       _("Cancel"),
                       CFG_SITE_URL,
                       request_id,
                       recid,
                       borrower_id,
                       _("Associate barcode"))

            out += """</table>
                  <br />
                  <table class="bibcirctable">
                       <tr>
                            <td>
                                 <input type="button" onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/get_waiting_requests?print_data=true'"
                                 value="%s" class="formbutton">
                            </td>
                           </tr>
                  </table>
                  <br />
                  </div>
                  """ % (CFG_SITE_URL,
                         _("Printable format"))


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
            <br /> <br \>            <br /> <br \>
            <table class="bibcirctable_contents">
                 <td class="bibcirccontent" align="center">%s</td>
            </table>
            <br /> <br \>            <br />
            <table class="bibcirctable_contents">
            <td align="center">
            <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py'" value="Back to home" class='formbutton'>
            </td>
            </table>
            <br \>
            </div>
            """ % (_("No hold requests waiting."), CFG_SITE_URL)




        else:
            out += """
            <form name="list_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/get_next_waiting_loan_request" method="get" >
            <div class="bibcircbottom">
            <br \>
            <br \>
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
                  <br \>
                  <br \>
                  <br \>
                  <table class="bibcirctable">
                       <tr>
                            <td>
                                 <input type=button value=%s
                                  onClick="history.go(-1)" class="formbutton">
                            </td>
                           </tr>
                  </table>
                  </form>
                  <br \>
                  <br \>
                  <br \>
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
             <div class=bibcircbottom>
             <br \>
             <br \>
                <br \>
                  <table class="bibcirctable_contents">
                       <tr align="center">
                            <td class="bibcirctableheader">%s</td>
                            <td><input type="text" size=45 id="barcode" name="barcode" style='border: 1px solid #cfcfcf'></td>
                       </tr>
                 </table>

                 """ % (CFG_SITE_URL,
                        _("Barcode"))

        out += """
        <br \><br \>
        <table class="bibcirctable_contents">
             <tr align="center">
                  <td>
                       <input type=button value=%s onClick="history.go(-1)" class="formbutton">
                       <input type="reset" name="reset_button" value=%s class="formbutton">
                       <input type="submit" name="ok_button" value=%s class="formbutton">
                  </td>
             </tr>
        </table>
        <br \><br \><br \>
        </div>
        </form>
        """ % (_("Back"),
               _("Reset"),
               _("Ok"))

        return out

    def tmpl_loan_return_confirm(self, borrower_name, recid, barcode,
                                 ln=CFG_SITE_LANG):
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

        out += """
           <form name="return_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/get_next_waiting_loan_request" method="get" >
             <div class=bibcircbottom>
             <br \>
             <br \>
             <table class="bibcirctable">
        """ % (CFG_SITE_URL)

        (book_title, book_year, book_author, book_isbn, book_editor) = book_information_from_MARC(recid)

        if book_isbn:
            book_cover = get_book_cover(book_isbn)
        else:
            book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)

        out += """
        <tr>
             <td class="bibcirctableheader" width="100">%s</td>
        </tr>
        </table>
        <table class="bibcirctable">
          <tr valign='top'>
           <td width="350">
           <table>
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
            </td>
            <td class="bibcirccontent"><img style='border: 1px solid #cfcfcf' src="%s" alt="Book Cover"/></td>
            </tr>

        <input type=hidden name=recid value=%s>
        <input type=hidden name=barcode value=%s>

        """ % (_("Loan informations"),
               _("Borrower"), borrower_name,
               _("Item"), book_title,
               _("Author"), book_author,
               _("Year"), book_year,
               _("Editor"), book_editor,
               _("ISBN"), book_isbn,
               str(book_cover),
               recid,
               barcode)

        out += """
        </table>
        <br \>
        <br \>
        <table class="bibcirctable">
             <tr>
                  <td>
                       <input type=button value=%s
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit" name="confirm_button"
                        value=%s class="formbutton">
                  </td>
             </tr>
        </table>
        <br \>
        <br \>
        <br \>
        </div>
        </form>
        """ % (_("Back"),
               _("Confirm"))


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
        <div class=bibcircbottom>
        <br \>
        <div class="subtitle">
        %s
        </div>
        <br \>
        """ % (_("Welcome to CDS Invenio BibCirculation Admin"))

        out += """
        <br \><br \>
        <br \><br \>
        <br \><br \>
        <br \><br \>
        <br \><br \>
        </div>
        """

        return out


    def tmpl_borrower_search(self, ln=CFG_SITE_LANG):
        """
        Template for the admin interface. Search borrower.

        @param ln: language
        """
        _ = gettext_set_language(ln)

        out = """  """

        out += _MENU_

        out += """
        <div class=bibcircbottom>
        <br \><br \>         <br \>
        <form name="borrower_search" action="%s/admin/bibcirculation/bibcirculationadmin.py/borrower_search_result" method="get" >
             <table class="bibcirctable">
               <tr align="center">
                 <td class="bibcirctableheader">%s
                   <input type="radio" name="column" value="id">ccid
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
        <br \>
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
        <br \>
        <br \>
        <br \>
        <br \>
        </div>

        """ % (CFG_SITE_URL,
               _("Search borrower by"),
               _("Back"), _("Search"))


        return out


    def tmpl_item_search(self, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        out = """  """

        out += _MENU_

        out += """
        <div class=bibcircbottom>
        <form name="search_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/item_search_result" method="get" >
        <br \>
        <br \>
        <br \>
        <input type=hidden name=start value="0">
        <input type=hidden name=end value="10">
        <table class="bibcirctable">
          <tr align="center">
            <td class="bibcirctableheader">Search item by
              <input type="radio" name="f" value="" checked>any field
              <input type="radio" name="f" value="year">year
              <input type="radio" name="f" value="author">author
              <input type="radio" name="f" value="title">title
              <br \>
              <br \>
            </td>
          </tr>
          <tr align="center">
          <td><input type="text" size="50" name="p" style='border: 1px solid #cfcfcf'></td>
                             </tr>
        </table>
        <br \>
        <table class="bibcirctable">
          <tr align="center">
            <td>

              <input type=button value='%s'
              onClick="history.go(-1)" class="formbutton">
              <input type="submit" value='%s' class="formbutton">

            </td>
          </tr>
        </table>
        <br \>
        <br \>
        <br \>
        <br \>
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

        out += """
        <div class="bibcircbottom">
        <br />
        <table class="bibcirctable">
          <tr align="center">
            <td class="bibcirctableheader">
               %s items found
            </td>
          </tr>
        </table>
        <br />
          <table class="bibcirctable">
            <tr>
              <td class="bibcirctableheader">%s</td>
              <td class="bibcirctableheader">%s</td>
              <td class="bibcirctableheader">%s</td>
              <td class="bibcirctableheader">%s</td>
            </tr>
        """ % (len(result), _("Title"), _("Author"), _("Editor"), _("No. Copies"))

        for recid in result:

            (book_author, book_editor, book_copies) = get_item_info_for_search_result(recid)

            title_link = create_html_link(CFG_SITE_URL +
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_item_details',
                                          {'recid': recid, 'ln': ln},
                                          (book_title_from_MARC(recid)))

            out += """
                <tr>
                <td class="contents">%s</td>
                <td class="contents">%s</td>
                <td class="contents">%s</td>
                <td class="contents">%s</td>
                </tr>
                """ % (title_link, book_author, book_editor, book_copies)

        out += """
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

    def tmpl_loan_on_desk_step1(self, result, key, string, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        if string is None:
            string = ""

        _ = gettext_set_language(ln)

        out = """
        """
        out += _MENU_

        out += """
        <div class=bibcircbottom>
        <form name="step1_form1" action="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1" method="get" >
        <br \>
        <br \>
        <br \>
          <table class="bibcirctable">

            """  % (CFG_SITE_URL)

        if CFG_CERN_SITE == 1:

            out += """
                 <tr>
                   <td width="105" class="bibcirctableheader" align="center">Search user by

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
                   <td width="105" class="bibcirctableheader" align="center">Search borrower by

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

        """ % (string)

        if result:
            out += """
            <br \>
            <form name="step1_form2" action="/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step2" method="get" >
            <table class="bibcirctable">
              <tr width="200">
                <td align="center">
                  <select name="user_info" size="8" style='border: 1px solid #cfcfcf; width:40%%'>

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
                        <td ALIGN="center">
                        <input type="submit" value='%s' class="formbutton">
                        </td>
                    </tr>
                    </table>
                    </form>
                    """ % (_("Select user"))

        out += """
              <br \>
              <br \>
              <br \>
              </div>
              """

        return out

    def tmpl_loan_on_desk_step2(self, user_info, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        (ccid, name, email, phone, address, mailbox) = user_info.split(',')

        _ = gettext_set_language(ln)

        out = """
        """
        out += _MENU_

        out += """
            <div class="bibcircbottom">
            <form name="step2_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step3" method="get" >
              <br />
              <br />
              <table class="bibcirctable">
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">
                    <input type="text" style='border: 1px solid #cfcfcf' size=45 value="%s" name="ccid" readonly>
                    </td>
                </tr>
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=45 value="%s" name="name" readonly>
                    </td>
                </tr>
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=45 value="%s" name="email">
                    </td>
                </tr>
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=45 value="%s" name="phone">
                    </td>
                 </tr>
                  <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=45 value="%s" name="address">
                    </td>
                 </tr>
                  <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=45 value="%s" name="mailbox">
                    </td>
                 </tr>
                </table>
                <br />
                <table class="bibcirctable">
                <tr>
                  <td>
                       <input type=button value=%s
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit" name="confirm_button"
                       value=%s class="formbutton">

                  </td>
                 </tr>
                </table>
                </form>
                <br />
                <br />
                </div>
                """ % (CFG_SITE_URL, _("ID"), ccid,
                       _("Name"), name,
                       _("Email"), email,
                       _("Phone"), phone,
                       _("Address"), address,
                       _("Mailbox"), mailbox,
                       _("Back"), _("Continue"))

        return out

    def tmpl_loan_on_desk_step3(self, user_info, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        (ccid, name, email, phone, address, mailbox) = user_info

        _ = gettext_set_language(ln)

        out = """  """

        out += _MENU_

        out += """
            <div class="bibcircbottom">
            <form name="step3_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step4" method="get" >
              <br />
              <br />
              <table class="bibcirctable">
                          <tr>
                               <td class="bibcirctableheader" width="70">%s</td>
                          </tr>
              </table>
              <table class="bibcirctable">
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">%s</td>
                </tr>
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">%s</td>
                </tr>
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">%s</td>
                </tr>
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">%s</td>
                </tr>
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">%s</td>
                </tr>
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">%s</td>
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

                       <input type="submit" name="confirm_button"
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
                       _("Continue"), user_info)

        return out

    def tmpl_loan_on_desk_step4(self, user_info, list_of_books, infos,
                                ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """
        (ccid, name, email, phone, address, mailbox) = user_info

        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += _MENU_

        out += """
            <div class="bibcircbottom">
            <form name="step4_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step5" method="get" >
              <br />
              <br />
              <input type=hidden name="list_of_books" value="%s">
              <table class="bibcirctable">
                          <tr>
                               <td class="bibcirctableheader" width="70">%s</td>
                          </tr>
              </table>
              <table class="bibcirctable">
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">%s</td>
                </tr>
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">%s</td>
                 </tr>
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">%s</td>
                 </tr>
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">%s</td>
                 </tr>
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">%s</td>
                 </tr>
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">%s</td>
                 </tr>
                </table>
                <br />
                <table class="bibcirctable">
                          <tr>
                               <td class="bibcirctableheader" width="70">%s</td>
                          </tr>
                </table>

                <script type="text/javascript" language='JavaScript' src="/jsCalendar/calendar.js"></script>
                <script type="text/javascript" language='JavaScript' src="/jsCalendar/calendar-setup.js"></script>
                <script type="text/javascript" language='JavaScript' src="/jsCalendar/calendar-en.js"></script>
                <style type="text/css"> @import url("/jsCalendar/calendar-blue.css"); </style>

                <table class="bibcirctable">
                 <tr>
                    <td width="100">%s</td> <td align="center" width="10">%s</td> <td width="230">%s</td>
                </tr>
                """  % (CFG_SITE_URL, list_of_books, _("User information"),
                        _("CCID"), ccid,
                        _("Name"), name,
                        _("Email"), email,
                        _("Phone"), phone,
                        _("Address"), address,
                        _("Mailbox"), mailbox,
                        _("List of borrowed books"),
                        _("Item"), _("Barcode"), _("Due date"))

        iterator = 1

        for (recid, barcode) in list_of_books:

            due_date = renew_loan_for_X_days(barcode)

            out +="""
                 <tr>
                    <td width="100" class="bibcirccontent">%s</td>
                    <td width="10" align="center" class="bibcirccontent">%s</td>
                    <td width="230" class="bibcirccontent">
                       <input type="text" size="12" id="%s" name="due_date" value="%s" style='border: 1px solid #cfcfcf'>
                       <img src="/jsCalendar/jsCalendar.gif" alt="Change due date" id="%s"
                       onmouseover="this.style.background='red';" onmouseout="this.style.background=''"
                       >
                       <script type="text/javascript" language='JavaScript'>
                       Calendar.setup({
                           inputField     :    '%s',
                           ifFormat       :    '%%Y-%%m-%%d',
                           button	  :    '%s'
                           });
                       </script>
                    </td>
                </tr>
                """ % (book_title_from_MARC(recid), barcode,
                       _("due_date_" + str(iterator)), due_date,
                       _("jsCal_" + str(iterator)), _("due_date_" + str(iterator)), _("jsCal_" + str(iterator)))

            iterator += 1

        out += """
                </table>
                <br />
                <table class="bibcirctable">
                          <tr>
                               <td class="bibcirctableheader" width="70">%s</td>
                          </tr>
                </table>
                <table class="bibcirctable">
                <tr>
                  <td><textarea name='note' rows="5" cols="40" style='border: 1px solid #cfcfcf'></textarea></td>
                </tr>
                <tr>
                  <td>This note will be associate to this new loan, not to the borrower.</td>
                </tr>
                </table>
                <br />
                <table class="bibcirctable">
                <tr>
                  <td>
                       <input type=button value=%s
                       onClick="history.go(-1)" class="formbutton">

                       <input type="submit" name="confirm_button"
                       value=%s class="formbutton">

                       <input type=hidden name="user_info" value="%s">
                  </td>
                 </tr>
                </table>
                </form>
                <br />
                <br />
                </div>
                """ % (_("Write note"), _("Back"),
                       _("Continue"), user_info)

        return out


    def tmpl_loan_on_desk_step5(self, ln=CFG_SITE_LANG):
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
                 <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py'" value="Back to home" class='formbutton'>
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
        <br \> <br \>
             <table class="bibcirctable">
                  <td class="bibcirccontent" width="30">%s</td>
             </table>
             <br \> <br \>
             <table class="bibcirctable">
             <td>
             <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py'" value='Back to home' class='formbutton'>
             </td>
             </table>
        <br \> <br \>
        </div>
        """ % (_("Notification has been sent!"),
               CFG_SITE_URL)

        return out

    def tmpl_register_new_loan(self, loan_information, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        (name, address, mailbox, email) = loan_information

        _ = gettext_set_language(ln)

        out = """  """

        out += _MENU_

        out += """
        <div class="bibcircbottom">
        <br />
        <br />
        <br />
        <table class="bibcirctable">
             <td class="bibcirccontent" width="30">%s</td>
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
        </table>
        <br />
        <br />
        <table class="bibcirctable">
             <td><input type="button" onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/register_new_loan?print_data=true'"
             value="%s" class="formbutton"></td>
        </table>
        <br />
        <br />
        </div>
        """ % (_("A new loan has been registered for:"),
               _("Name"), name,
               _("Address"), address,
               _("Mailbox"), mailbox,
               _("Email"), email,
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
             <div class=bibcircbottom>
             <input type=hidden name=borrower_id value=%s>
             <br \>
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
        <br \>
        <table class="bibcirctable_contents">
             <tr>
                  <td>
                       <input type=button value=%s onClick="history.go(-1)" class="formbutton">
                       <input type="submit" name="confirm_button" value=%s class="formbutton">
                  </td>
             </tr>
        </table>
        <br \>
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
             <br \>
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
        <br \>
        <table class="bibcirctable">
             <tr>
                  <td>
                     <input type=button value="%s" onClick="history.go(-1)" class="formbutton">
                  </td>
             </tr>
        </table>
        <br \> <br \>
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

        out += """
        <form name="all_loans_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/update_loan_request_status" method="get" >
             <div class="bibcircbottom">
             <br \>
                  <table class="bibcirctable">
                         <tr>
                              <td class="bibcirctableheader">%s</td>
                              <td class="bibcirctableheader" align="center">%s</td>
                              <td class="bibcirctableheader" align="center">%s</td>
                              <td class="bibcirctableheader" align="center">%s</td
                              <td class="bibcirctableheader" align="center">%s</td>
                              <td class="bibcirctableheader" align="center">%s</td>
                              <td class="bibcirctableheader" align="center">%s</td>
                              <td class="bibcirctableheader" align="center">%s</td>
                         </tr>
         """% (CFG_SITE_URL,
               _("Borrower"),
               _("Status"),
               _("Library"),
               _("Location"),
               _("From"),
               _("To"),
               _("Request date"),
               _("Option(s)"))


        for (borrower_id, name, id_bibrec, status, library, location, date_from, date_to, request_id, request_date) in result:

            borrower_link = create_html_link(CFG_SITE_URL +
                                             '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_details',
                                             {'borrower_id': borrower_id, 'ln': ln},
                                             (name))

            out += """
            <tr  onMouseOver="this.className='highlight'" onMouseOut="this.className='normal'">
                 <td class="bibcirccontent">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">
                   <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/get_item_requests_details?recid=%s&request_id=%s'"
                   value='%s' class='formbutton'>
                 </td>
            </tr>
            """ % (borrower_link, status, library, location, date_from, date_to, request_date, CFG_SITE_URL, id_bibrec, request_id, _("Cancel hold request"))

        out += """
        </table>
        <br \>
        <table class="bibcirctable">
             <tr>
                  <td><input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/get_item_details?recid=%s'"
                       value='%s' class='formbutton'></td>
             </tr>
        </table>
        <br \><br \><br \>
       </div>
        </form>
        """ % (CFG_SITE_URL,
               recid,
               _("Back"))

        return out

    def tmpl_get_item_details(self, recid, copies, requests, loans, req_hist_overview,
                              loans_hist_overview, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = """  """

        out += _MENU_

        req_hist_link = create_html_link(CFG_SITE_URL +
                                        '/admin/bibcirculation/bibcirculationadmin.py/get_item_req_historical_overview',
                                        {'recid': recid, 'ln': ln},
                                        (_("More details")))

        loans_hist_link = create_html_link(CFG_SITE_URL +
                                        '/admin/bibcirculation/bibcirculationadmin.py/get_item_loans_historical_overview',
                                        {'recid': recid, 'ln': ln},
                                        (_("More details")))

        req_link = create_html_link(CFG_SITE_URL +
                                        '/admin/bibcirculation/bibcirculationadmin.py/get_item_requests_details',
                                        {'recid': recid, 'ln': ln},
                                        (_("More details")))

        loans_link = create_html_link(CFG_SITE_URL +
                                        '/admin/bibcirculation/bibcirculationadmin.py/get_item_loans_details',
                                        {'recid': recid, 'ln': ln},
                                        (_("More details")))


        (book_title, book_year, book_author, book_isbn, book_editor) = book_information_from_MARC(recid)

        if book_isbn:
            book_cover = get_book_cover(book_isbn)
        else:
            book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)


        out += """
           <div class="bibcircbottom">
                <br \>
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
           <br \>
           <table class="bibcirctable">
                <tr>
                     <td class="bibcirctableheader">%s</td>
                </tr>
           </table>
           """  % (_("Item details"),
                   _("Name"), book_title,
                   _("Author(s)"), book_author,
                   _("Year"), book_year,
                   _("Editor"), book_editor,
                   _("ISBN"), book_isbn,
                   str(book_cover), _("Additional details"))

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
                      <td align="center">%s</td>
                    </tr>""" % (_("Barcode"),
                                _("Status"),
                                _("Library"),
                                _("Location"),
                                _("Loan period"),
                                _("No of loans"),
                                _("Collection"),
                                _("Description"),
                                _("Option(s)"))


        for (barcode, loan_period, library_name, library_id, location, nb_requests, status, collection, description) in copies:

            library_link = create_html_link(CFG_SITE_URL +
                                            '/admin/bibcirculation/bibcirculationadmin.py/get_library_details',
                                            {'library_id': library_id, 'ln': ln},
                                            (library_name))

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

                     """% (barcode, status, library_link, location,
                           loan_period, nb_requests, collection,
                           description)

            if status == 'on loan':
                out += """
                  <td class="bibcirccontent" align="center">
                    <SELECT style='border: 1px solid #cfcfcf' ONCHANGE="location = this.options[this.selectedIndex].value;">
                      <OPTION VALUE="">Select an option
                      <OPTION VALUE="update_item_info_step4?barcode=%s">Update
                      <OPTION VALUE="place_new_request_step1?barcode=%s">New request
                      <OPTION VALUE="" DISABLED>New loan
                    </SELECT>
                  </td>
                 </tr>
                 """ % (barcode, barcode)

            elif status == 'missing':
                out += """
                     <td class="bibcirccontent" align="center">
                       <SELECT style='border: 1px solid #cfcfcf' ONCHANGE="location = this.options[this.selectedIndex].value;">
                         <OPTION VALUE="">Select an option
                         <OPTION VALUE="update_item_info_step4?barcode=%s">Update
                         <OPTION VALUE="" DISABLED>New request
                         <OPTION VALUE="" DISABLED>New loan
                       </SELECT>
                     </td>
                 </tr>
                 """ % (barcode)
            else:
                out += """
                     <td class="bibcirccontent" align="center">
                       <SELECT style='border: 1px solid #cfcfcf' ONCHANGE="location = this.options[this.selectedIndex].value;">
                         <OPTION VALUE="">Select an option
                         <OPTION VALUE="update_item_info_step4?barcode=%s">Update
                         <OPTION VALUE="place_new_request_step1?barcode=%s">New request
                         <OPTION VALUE="place_new_loan_step1?barcode=%s">New loan
                       </SELECT>
                     </td>
                 </tr>
                 """ % (barcode, barcode, barcode)


        out += """
            </table>
            <table class="bibcirctable">
                 <tr>
                     <td>
                     <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/add_new_copy_step3?recid=%s'"
                     value='%s' class="formbutton">
                     </td>
                </tr>
            </table>
            <br />
            <table class="bibcirctable">
                 <tr>
                     <td class="bibcirctableheader">%s %s</td>
                </tr>
            </table>
            <table class="bibcirctable">
                 <tr>
                      <td width="100">%s</td>
                      <td width="50" class="bibcirccontent">%s</td>
                      <td class="bibcirccontent">%s</td>
                 </tr>

                 <tr>
                      <td width="100">%s</td>
                      <td width="50" class="bibcirccontent">%s</td>
                      <td class="bibcirccontent">%s</td>
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
                      <td width="100">%s</td>
                      <td width="50" class="bibcirccontent">%s</td>
                      <td class="bibcirccontent">%s</td>
                 </tr>

                 <tr>
                      <td width="100">%s</td>
                      <td width="50" class="bibcirccontent">%s</td>
                      <td class="bibcirccontent">%s</td>
                 </tr>

            </table>
            <br />

            """ % (CFG_SITE_URL, recid, _("Add new copy"),
                   _("Hold requests and loans overview on"), time.ctime(),
                   _("Hold requests"), len(requests), req_link,
                   _("Loans"), len(loans), loans_link,
                   _("Historical overview"),
                   _("Hold requests"), len(req_hist_overview), req_hist_link,
                   _("Loans"), len(loans_hist_overview), loans_hist_link)




        out += """
           <br \>
           <table class="bibcirctable">
                <tr>
                     <td><input type=button value='%s'
                          onClick="history.go(-1)" class="formbutton"></td>
                </tr>
           </table>
           <br \>
           <br \>
           <br \>
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

        out += """<div class="bibcircbottom">
                    <br /> <br \>
                    <table class="bibcirctable">
                     <tr>
                     <td class="bibcirctableheader">%s</td>
                     <td class="bibcirctableheader" align="center">%s</td>
                     <td class="bibcirctableheader" align="center">%s</td>
                     <td class="bibcirctableheader" align="center">%s</td>
                     <td class="bibcirctableheader" align="center">%s</td>
                     <td class="bibcirctableheader" align="center">%s</td>
                     <td class="bibcirctableheader" align="center">%s</td>
                     </tr>
                     """ % (_("Item"), _("Barcode"), _("Library"),
                            _("Location"), _("From"),
                            _("To"), _("Request date"))

        for (recid, barcode, library_name, location, req_from, req_to, req_date) in req_hist_overview:

            title_link = create_html_link(CFG_SITE_URL +
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_item_details',
                                          {'recid': recid, 'ln': ln},
                                          (book_title_from_MARC(recid)))

            out += """ <tr  onMouseOver="this.className='highlight'"
                            onMouseOut="this.className='normal'">
                       <td class="bibcirccontent">%s</td>
                       <td class="bibcirccontent" align="center">%s</td>
                       <td class="bibcirccontent" align="center">%s</td>
                       <td class="bibcirccontent" align="center">%s</td>
                       <td class="bibcirccontent" align="center">%s</td>
                       <td class="bibcirccontent" align="center">%s</td>
                       <td class="bibcirccontent" align="center">%s</td>
                       </tr>
                 """ % (title_link, barcode, library_name, location, req_from, req_to, req_date)

        out += """
           </table>
           <br \>
           <table class="bibcirctable">
                <tr>
                     <td><input type=button value='%s'
                          onClick="history.go(-1)" class="formbutton"></td>
                </tr>
           </table>
           <br \>
           <br \>
           <br \>
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

        out += """<div class="bibcircbottom">
                    <br /> <br \>
                    <table class="bibcirctable">
                     <tr>
                     <td class="bibcirctableheader">%s</td>
                     <td class="bibcirctableheader" align="center">%s</td>
                     <td class="bibcirctableheader" align="center">%s</td>
                     <td class="bibcirctableheader" align="center">%s</td>
                     <td class="bibcirctableheader" align="center">%s</td>
                     <td class="bibcirctableheader" align="center">%s</td>
                     <td class="bibcirctableheader" align="center">%s</td>
                     <td class="bibcirctableheader" align="center">%s</td>
                     <td class="bibcirctableheader" align="center">%s</td>
                     </tr>
                     """ % (_("Item"),
                            _("Barcode"),
                            _("Library"),
                            _("Location"),
                            _("Loaned on"),
                            _("Due date"),
                            _("Returned on"),
                            _("Renewals"),
                            _("Overdue letters"))

        for (recid, barcode, library_name, location, loaned_on, due_date, returned_on, nb_renew, nb_overdueletters) in loans_hist_overview:

            title_link = create_html_link(CFG_SITE_URL +
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_item_details',
                                          {'recid': recid, 'ln': ln},
                                          (book_title_from_MARC(recid)))

            out += """ <tr  onMouseOver="this.className='highlight'"
                            onMouseOut="this.className='normal'">
                       <td class="bibcirccontent">%s</td>
                       <td class="bibcirccontent" align="center">%s</td>
                       <td class="bibcirccontent" align="center">%s</td>
                       <td class="bibcirccontent" align="center">%s</td>
                       <td class="bibcirccontent" align="center">%s</td>
                       <td class="bibcirccontent" align="center">%s</td>
                       <td class="bibcirccontent" align="center">%s</td>
                       <td class="bibcirccontent" align="center">%s</td>
                       <td class="bibcirccontent" align="center">%s</td>
                       </tr>
                 """ % (title_link, barcode,
                        library_name, location,
                        loaned_on, due_date,
                        returned_on, nb_renew,
                        nb_overdueletters)

        out += """
           </table>
           <br \>
           <table class="bibcirctable">
                <tr>
                     <td><input type=button value='%s'
                          onClick="history.go(-1)" class="formbutton"></td>
                </tr>
           </table>
           <br \>
           <br \>
           <br \>
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

        out += """
             <div class="bibcircbottom">
              <br />
              <br \>
              <table class="bibcirctable">
              <tr>
               <td width="80" class="bibcirctableheader">%s</td>
               <td width="20" class="bibcirctableheader" align="center">%s</td>
               <td width="20" class="bibcirctableheader" align="center">%s</td>
               <td width="20" class="bibcirctableheader" align="center">%s</td>
               <td width="20" class="bibcirctableheader" align="center">%s</td>
               <td width="20" class="bibcirctableheader" align="center">%s</td>
               <td width="20" class="bibcirctableheader" align="center">%s</td>
              </tr>
                     """ % (_("Borrower"),
                            _("Barcode"),
                            _("Library"),
                            _("Location"),
                            _("From"),
                            _("To"),
                            _("Request date"))

        for (name, borrower_id, barcode, library_name, location, req_from, req_to, req_date) in req_hist_overview:

            borrower_link = create_html_link(CFG_SITE_URL +
                                             '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_details',
                                             {'borrower_id': borrower_id, 'ln': ln},
                                             (name))

            out += """

                  <tr  onMouseOver="this.className='highlight'"
                       onMouseOut="this.className='normal'">
                   <td width="80" class="bibcirccontent">%s</td>
                   <td width="20" class="bibcirccontent" align="center">%s</td>
                   <td width="20" class="bibcirccontent" align="center">%s</td>
                   <td width="20" class="bibcirccontent" align="center">%s</td>
                   <td width="20" class="bibcirccontent" align="center">%s</td>
                   <td width="20" class="bibcirccontent" align="center">%s</td>
                   <td width="20" class="bibcirccontent" align="center">%s</td>
                  </tr>

                 """ % (borrower_link, barcode, library_name,
                        location, req_from, req_to, req_date)

        out += """
           </table>
           <br \>
           <table class="bibcirctable">
                <tr>
                     <td><input type=button value='%s'
                          onClick="history.go(-1)" class="formbutton"></td>
                </tr>
           </table>
           <br \>
           <br \>
           <br \>
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
                    <br /> <br \>
                    <table class="bibcirctable">
                     <tr>
                     <td class="bibcirctableheader">%s</td>
                     <td class="bibcirctableheader" align="center">%s</td>
                     <td class="bibcirctableheader" align="center">%s</td>
                     <td class="bibcirctableheader" align="center">%s</td>
                     <td class="bibcirctableheader" align="center">%s</td>
                     <td class="bibcirctableheader" align="center">%s</td>
                     <td class="bibcirctableheader" align="center">%s</td>
                     <td class="bibcirctableheader" align="center">%s</td>
                     <td class="bibcirctableheader" align="center">%s</td>
                     </tr>
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

            out += """ <tr  onMouseOver="this.className='highlight'"
                            onMouseOut="this.className='normal'">
                       <td class="bibcirccontent">%s</td>
                       <td class="bibcirccontent" align="center">%s</td>
                       <td class="bibcirccontent" align="center">%s</td>
                       <td class="bibcirccontent" align="center">%s</td>
                       <td class="bibcirccontent" align="center">%s</td>
                       <td class="bibcirccontent" align="center">%s</td>
                       <td class="bibcirccontent" align="center">%s</td>
                       <td class="bibcirccontent" align="center">%s</td>
                       <td class="bibcirccontent" align="center">%s</td>
                       </tr>
                 """ % (borrower_link, barcode, library_name,
                        location, loaned_on,
                        due_date, returned_on, nb_renew,
                        nb_overdueletters)

        out += """
           </table>
           <br \>
           <table class="bibcirctable">
                <tr>
                     <td><input type=button value='%s'
                          onClick="history.go(-1)" class="formbutton"></td>
                </tr>
           </table>
           <br \>
           <br \>
           <br \>
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
        <div class="bibcircbottom">
        <br \>
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
            <table class="bibcirctable">

                 <tr>
                      <td width="80">%s</td>
                      <td class="bibcirccontent">%s</td>
                 </tr>
                 <tr>
                      <td width="80">%s</td>
                      <td class="bibcirccontent">%s</td>
                 </tr>
                 <tr>
                      <td width="80">%s</td>
                      <td class="bibcirccontent">%s</td>
                 </tr>
                 <tr>
                      <td width="80">%s</td>
                      <td class="bibcirccontent">%s</td>
                 </tr>
                 <tr>
                      <td width="80">%s</td>
                      <td class="bibcirccontent">%s</td>
                 </tr>
                  <tr>
                      <td width="80">%s</td>
                      <td class="bibcirccontent">%s</td>
                 </tr>
                 <tr>
                      <td><input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/update_library_info_step3?library_id=%s'"
                      value=%s  class="formbutton">
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
           <br \>
           <br \>
           <table class="bibcirctable">
                <tr>
                     <td><input type=button value='%s'
                          onClick="history.go(-1)" class="formbutton"></td>
                </tr>
           </table>
           <br \>
           <br \>
           <br \>
           </form>
           </div>
           """ % (_("Back"))

        return out


    def tmpl_borrower_details(self, borrower, requests, loans, notes,
                              req_hist, loans_hist, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        _ = gettext_set_language(ln)


        out = """ """

        out += _MENU_

        (borrower_id, name, email, phone, address, mailbox) = borrower

        req_link = create_html_link(CFG_SITE_URL +
                                    '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_requests_details',
                                    {'borrower_id': borrower_id},
                                    (_("More details")))

        no_notes_link = create_html_link(CFG_SITE_URL +
                                         '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_notes',
                                         {'borrower_id': borrower_id},
                                         (_("No notes")))

        see_notes_link = create_html_link(CFG_SITE_URL +
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_notes',
                                          {'borrower_id': borrower_id},
                                          (_("Notes about this borrower")))


        loans_link = create_html_link(CFG_SITE_URL +
                                      '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_loans_details',
                                      {'borrower_id': borrower_id},
                                      (_("More details")))


        req_hist_link = create_html_link(CFG_SITE_URL +
                                         '/admin/bibcirculation/bibcirculationadmin.py/bor_requests_historical_overview',
                                         {'borrower_id': borrower_id},
                                         (_("More details")))

        loans_hist_link = create_html_link(CFG_SITE_URL +
                                           '/admin/bibcirculation/bibcirculationadmin.py/bor_loans_historical_overview',
                                           {'borrower_id': borrower_id},
                                           (_("More details")))

        if notes == "":
            check_notes = no_notes_link
        else:
            check_notes = see_notes_link


        out += """
            <form name="borrower_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/borrower_notification" method="get" >
            <div class="bibcircbottom">
            <input type=hidden name=borrower_id value=%s>
            <br \>
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
        nb_req_hist = len(req_hist)
        nb_loans_hist = len(loans_hist)

        out += """
        </table>
        <!-- <table class="bibcirctable">
             <tr>
                  <td><input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/update_borrower_info_step3?borrower_id=%s'"
                       value=%s class='formbutton'></td>
             </tr>
        </table> -->
        <br \>
        <table class="bibcirctable">
             <tr>
               <td>
                 <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/create_new_loan_step1?borrower_id=%s'"
                 value='%s' class='formbutton'>

                 <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/create_new_request_step1?borrower_id=%s'"
                 value='%s' class='formbutton'>

                 <input type="submit" name="notify_button" value='%s' class="formbutton">

               </td>
             </tr>
        </table>
        <br \>

        <table class="bibcirctable">
             <tr>
                  <td class="bibcirctableheader" width="50">%s %s</td>
             </tr>
        </table>

        <table class="bibcirctable">
             <tr>
                  <td width="100">%s</td>
                  <td width="50" class="bibcirccontent">%s</td>
                  <td class="bibcirccontent">%s</td>
             </tr>

             <tr>
                  <td width="100">%s</td>
                  <td width="50" class="bibcirccontent">%s</td>
                  <td class="bibcirccontent">%s</td>
             </tr>

        </table>
        <br \>


        <table class="bibcirctable">
             <tr>
                  <td class="bibcirctableheader" width="50">%s</td>
             </tr>
        </table>

        <table class="bibcirctable">
             <tr>
                  <td width="100">%s</td>
                  <td width="50" class="bibcirccontent">%s</td>
                  <td class="bibcirccontent">%s</td>
             </tr>

             <tr>
                  <td width="100">%s</td>
                  <td width="50" class="bibcirccontent">%s</td>
                  <td class="bibcirccontent">%s</td>
             </tr>

        </table>
        <br />
        <table class="bibcirctable">
             <tr>
                 <td><input type=button value='%s'
                      onClick="history.go(-1)" class="formbutton"></td>
             </tr>
        </table>
        <br \>
        </div>
        """ % (CFG_SITE_URL, borrower_id, _("Update"),
               CFG_SITE_URL, borrower_id, _("New loan"),
               CFG_SITE_URL, borrower_id, _("New request"),
               _("Notify this borrower"),
               _("Requests and Loans overview on"), time.ctime(),
               _("Requests"), nb_requests, req_link,
               _("Loans"), nb_loans, loans_link,
               _("Historical overview"),
               _("Requests"), nb_req_hist, req_hist_link,
               _("Loans"), nb_loans_hist, loans_hist_link,
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

        out += """
        <form name="borrower_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/get_borrower_requests_details" method="get" >
        <div class="bibcircbottom">
        <br \>
             <table class="bibcirctable">
                    <tr>
                       <td class="bibcirctableheader">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
               </tr>
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
            <tr  onMouseOver="this.className='highlight'"
                 onMouseOut="this.className='normal'">
                 <td class="bibcirccontent">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">
                   <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/get_item_requests_details?request_id=%s'"
                   value='%s' class="formbutton">
                 </td>
            </tr>

            """ % (title_link, status, library, location, date_from,
                   date_to, request_date, CFG_SITE_URL,
                   request_id, _("Cancel hold request"))


        out += """
        </table>
        <br \>
        <table class="bibcirctable">
             <tr>
                  <td>
                    <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/get_borrower_details?borrower_id=%s'"
                    value='%s' class='formbutton'>
                  </td>
             </tr>
        </table>
        <br \>
        </div>
        """ % (CFG_SITE_URL,
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
        out += _MENU_

        out += """
        <form name="borrower_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/get_borrower_loans_details?submit_changes=true" method="get" >
        <input type=hidden name=borrower_id value=%s>
        <div class="bibcircbottom">
        <br \>
             <table class="bibcirctable">
                    <tr>
                       <td class="bibcirctableheader">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
               </tr>

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
                                          {'loan_id': loan_id, 'recid': recid, 'borrower_id': borrower_id, 'ln': ln},
                                          (_("No notes")))

            see_notes_link = create_html_link(CFG_SITE_URL +
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_loans_notes',
                                          {'loan_id': loan_id, 'recid': recid, 'borrower_id': borrower_id, 'ln': ln},
                                          (_("See notes")))

            if notes == "":
                check_notes = no_notes_link
            else:
                check_notes = see_notes_link


            out += """
            <tr  onMouseOver="this.className='highlight'" onMouseOut="this.className='normal'">
                 <td class="bibcirccontent">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s - %s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>

                 <td align="center">
                    <SELECT style='border: 1px solid #cfcfcf' ONCHANGE="location = this.options[this.selectedIndex].value;">
                      <OPTION VALUE="">Select an option
                      <OPTION VALUE="get_borrower_loans_details?borrower_id=%s&barcode=%s&loan_id=%s&recid=%s">Renew
                      <OPTION VALUE="loan_return_confirm?barcode=%s">Return
                      <OPTION VALUE="change_due_date_step1?loan_id=%s&borrower_id=%s">Change due date
                      <OPTION VALUE="claim_book_return?borrower_id=%s&recid=%s&template=claim_return">Claim return
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
                   borrower_id, recid,
                   barcode, loan_id)

        out += """
        </table>
        <br \>
        <table class="bibcirctable">
             <tr>
                  <td class="bibcirccontent" align="right" width="100">
                  <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/get_borrower_loans_details?borrower_id=%s&renewall=true'"
                  value='%s' class='formbutton'></td>
             </tr>
        </table>
        <table class="bibcirctable">
             <tr>
                  <td>
                    <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/get_borrower_details?borrower_id=%s'"
                    value='%s' class='formbutton'>
                  </td>
             </tr>
        </table>
        <br \>
        </div>
        </form>

        """ % (CFG_SITE_URL,
               borrower_id,
               _("Renew all loans"),
               CFG_SITE_URL,
               borrower_id,
               _("Back"))


        return out

    def tmpl_all_loans(self, result, loans_per_page, jloan, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        initial = int(jloan)
        last = int(jloan) + int(loans_per_page)
        end = len(result) - (len(result) % int(loans_per_page))


        out = """  """

        out += _MENU_

        out += """
            <form name="list_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/all_loans" method="get" >
            <div class="bibcircbottom">
            <br />
            <table class="bibcirctable">
            <tr>
            """ % (CFG_SITE_URL)

        out += """
            <td class="bibcirctableheader" width="100">
            loans per page
            </td>
            <td width="70">
                    <select name="loans_per_page" style='border: 1px solid #cfcfcf'>
            """

        if loans_per_page == '50':
            out += """
                   <option value=25>25</option>
                   <option value=50 selected>50</option>
                   <option value=100>100</option>
                   <option value=200>200</option>
                   """

        elif loans_per_page == '100':
            out += """
                   <option value=25>25</option>
                   <option value=50>50</option>
                   <option value=100 selected>100</option>
                   <option value=200>200</option>
                   """

        elif loans_per_page == '200':
            out += """
                   <option value=25>25</option>
                   <option value=50>50</option>
                   <option value=100>100</option>
                   <option value=200 selected>200</option>
                   """

        else:
            out += """
                   <option value=25 selected>25</option>
                   <option value=50>50</option>
                   <option value=100>100</option>
                   <option value=200>200</option>
                   """
        out += """
                    </select>
            </td>
            <td>
            <input type="submit" name="ok_button" value="%s" class="formbutton">
            </td>
            </tr>
            </table>
            <br />
            <hr>
            <br />
            </form>

        """ % (_("Ok"))

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
            <form name="borrower_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/all_loans" method="get" >
            <br \>
             <table class="bibcirctable">
                    <tr>
                       <td class="bibcirctableheader">%s</td>
                       <td class="bibcirctableheader">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
                    </tr>

                    """% (CFG_SITE_URL,
                          _("Borrower"),
                          _("Item"),
                          _("Barcode"),
                          _("Loaned on"),
                          _("Due date"),
                          _("Renewals"),
                          _("Overdue letters"),
                          _("Status"),
                          _("Loan Notes"))

            for (borrower_id, borrower_name, recid, barcode, loaned_on, due_date, nb_renewall, nb_overdue, date_overdue, status, notes, loan_id) in result[initial:last]:

                borrower_link = create_html_link(CFG_SITE_URL +
                                                 '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_details',
                                                 {'borrower_id': borrower_id, 'ln': ln},
                                                 (borrower_name))

                see_notes_link = create_html_link(CFG_SITE_URL +
                                                  '/admin/bibcirculation/bibcirculationadmin.py/get_loans_notes',
                                                  {'loan_id': loan_id, 'recid': recid, 'borrower_id': borrower_id, 'ln': ln},
                                                  (_("see notes")))

                no_notes_link = create_html_link(CFG_SITE_URL +
                                                 '/admin/bibcirculation/bibcirculationadmin.py/get_loans_notes',
                                                 {'loan_id': loan_id, 'recid': recid, 'borrower_id': borrower_id, 'ln': ln},
                                                 (_("no notes")))

                next_link = create_html_link(CFG_SITE_URL +
                                             '/admin/bibcirculation/bibcirculationadmin.py/all_loans',
                                             {'loans_per_page': loans_per_page, 'jloan': last, 'ln': ln},
                                             (_("next page >>>")))

                previous_link = create_html_link(CFG_SITE_URL +
                                                 '/admin/bibcirculation/bibcirculationadmin.py/all_loans',
                                                 {'loans_per_page': loans_per_page, 'jloan': initial - int(loans_per_page), 'ln': ln},
                                                 (_("<<< previous page")))

                begin_link = create_html_link(CFG_SITE_URL +
                                              '/admin/bibcirculation/bibcirculationadmin.py/all_loans',
                                              {'loans_per_page': loans_per_page, 'jloan': 0, 'ln': ln},
                                              (_("|<< first page")))

                end_link = create_html_link(CFG_SITE_URL +
                                            '/admin/bibcirculation/bibcirculationadmin.py/all_loans',
                                            {'loans_per_page': loans_per_page, 'jloan': end, 'ln': ln},
                                            (_("last page >>|")))

                if notes == "":
                    check_notes = no_notes_link
                else:
                    check_notes = see_notes_link

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
                    <td class="bibcirccontent" align="center">%s - %s</td>
                    <td class="bibcirccontent" align="center">%s</td>
                    <td class="bibcirccontent" align="center">%s</td>
                    </tr>

                    """ % (borrower_link, title_link, barcode,
                           loaned_on, due_date,
                           nb_renewall, nb_overdue, date_overdue,
                           status, check_notes)

            if int(loans_per_page) <= len(result):

                if int(jloan) == 0:
                    out += """
                    </table>
                    <br \>
                    <table class="bibcirctable">
                    <tr>
                    <td align='center'>%s - %s - %s - %s</td>
                    </tr>
                    </table>
                    <br \>
                    <table class="bibcirctable">
                    <tr>
                    <td><input type=button value='%s'
                    onClick="history.go(-1)" class="formbutton"></td>
                    </tr>
                    </table>
                    <br \>
                    <br \>
                    <br \>
                    </div>
                    </form>
                    """ % ('|<< first page', '<<< previous page',
                           next_link, end_link,
                           _("Back"))

                elif int(jloan) == end:
                    out += """
                    </table>
                    <br \>
                    <table class="bibcirctable">
                    <tr>
                    <td align='center'>%s - %s - %s - %s</td>
                    </tr>
                    </table>
                    <br \>
                    <table class="bibcirctable">
                    <tr>
                    <td><input type=button value='%s'
                    onClick="history.go(-1)" class="formbutton"></td>
                    </tr>
                    </table>
                    <br \>
                    <br \>
                    <br \>
                    </div>
                    </form>
                    """ % (begin_link, previous_link,
                           'next page >>>', 'last page >>|',
                           _("Back"))

                else:
                    out += """
                    </table>
                    <br \>
                    <table class="bibcirctable">
                    <tr>
                    <td align='center'>%s - %s - %s - %s</td>
                    </tr>
                    </table>
                    <br \>
                    <table class="bibcirctable">
                    <tr>
                    <td><input type=button value='%s'
                    onClick="history.go(-1)" class="formbutton"></td>
                    </tr>
                    </table>
                    <br \>
                    <br \>
                    <br \>
                    </div>
                    </form>
                    """ % (begin_link, previous_link,
                           next_link, end_link,
                           _("Back"))
            else:
                out += """
                    </table>
                    <br \>
                    <br \>
                    <br \>
                    <table class="bibcirctable">
                    <tr>
                    <td><input type=button value='%s'
                    onClick="history.go(-1)" class="formbutton"></td>
                    </tr>
                    </table>
                    <br \>
                    <br \>
                    <br \>
                    </div>
                    </form>
                    """ % (_("Back"))



        return out


    def tmpl_all_expired_loans(self, result, loans_per_page, jloan, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        _ = gettext_set_language(ln)


        initial = int(jloan)
        last = int(jloan) + int(loans_per_page)
        end = len(result) - (len(result) % int(loans_per_page))



        out = """  """

        out += _MENU_

        out += """
            <form name="list_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/all_expired_loans" method="get" >
            <div class="bibcircbottom">
            <br />
            <table class="bibcirctable">
            <tr>
            """ % (CFG_SITE_URL)

        out += """
            <td class="bibcirctableheader" width="100">
            loans per page
            </td>
            <td width="70">
                    <select name="loans_per_page" style='border: 1px solid #cfcfcf'>
            """

        if loans_per_page == '50':
            out += """
                   <option value=25>25</option>
                   <option value=50 selected>50</option>
                   <option value=100>100</option>
                   <option value=200>200</option>
                   """

        elif loans_per_page == '100':
            out += """
                   <option value=25>25</option>
                   <option value=50>50</option>
                   <option value=100 selected>100</option>
                   <option value=200>200</option>
                   """

        elif loans_per_page == '200':
            out += """
                   <option value=25>25</option>
                   <option value=50>50</option>
                   <option value=100>100</option>
                   <option value=200 selected>200</option>
                   """

        else:
            out += """
                   <option value=25 selected>25</option>
                   <option value=50>50</option>
                   <option value=100>100</option>
                   <option value=200>200</option>
                   """
        out += """
                    </select>
            </td>
            <td>
            <input type="submit" name="ok_button" value="%s" class="formbutton">
            </td>
            </tr>
            </table>
            <br />
            <hr>
            <br />
            </form>

        """ % (_("Ok"))

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
            <form name="borrower_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/all_loans" method="get" >
            <br \>
             <table class="bibcirctable">
                    <tr>
                       <td class="bibcirctableheader">%s</td>
                       <td class="bibcirctableheader">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
                    </tr>

                    """% (CFG_SITE_URL,
                          _("Borrower"),
                          _("Item"),
                          _("Barcode"),
                          _("Loaned on"),
                          _("Due date"),
                          _("Renewals"),
                          _("Overdue letters"),
                          _("Status"),
                          _("Loan Notes"))

            for (borrower_id, borrower_name, recid, barcode, loaned_on, due_date, nb_renewall, nb_overdue, date_overdue, status, notes, loan_id) in result[initial:last]:

                borrower_link = create_html_link(CFG_SITE_URL +
                                                 '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_details',
                                                 {'borrower_id': borrower_id, 'ln': ln},
                                                 (borrower_name))

                see_notes_link = create_html_link(CFG_SITE_URL +
                                                  '/admin/bibcirculation/bibcirculationadmin.py/get_loans_notes',
                                                  {'loan_id': loan_id, 'recid': recid, 'borrower_id': borrower_id, 'ln': ln},
                                                  (_("see notes")))

                no_notes_link = create_html_link(CFG_SITE_URL +
                                                 '/admin/bibcirculation/bibcirculationadmin.py/get_loans_notes',
                                                 {'loan_id': loan_id, 'recid': recid, 'borrower_id': borrower_id, 'ln': ln},
                                                 (_("no notes")))

                next_link = create_html_link(CFG_SITE_URL +
                                             '/admin/bibcirculation/bibcirculationadmin.py/all_loans',
                                             {'loans_per_page': loans_per_page, 'jloan': last, 'ln': ln},
                                             (_("next page >>>")))

                previous_link = create_html_link(CFG_SITE_URL +
                                                 '/admin/bibcirculation/bibcirculationadmin.py/all_loans',
                                                 {'loans_per_page': loans_per_page, 'jloan': initial - int(loans_per_page), 'ln': ln},
                                                 (_("<<< previous page")))

                begin_link = create_html_link(CFG_SITE_URL +
                                              '/admin/bibcirculation/bibcirculationadmin.py/all_loans',
                                              {'loans_per_page': loans_per_page, 'jloan': 0, 'ln': ln},
                                              (_("|<< first page")))

                end_link = create_html_link(CFG_SITE_URL +
                                            '/admin/bibcirculation/bibcirculationadmin.py/all_loans',
                                            {'loans_per_page': loans_per_page, 'jloan': end, 'ln': ln},
                                            (_("last page >>|")))

                if notes == "":
                    check_notes = no_notes_link
                else:
                    check_notes = see_notes_link

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
                    <td class="bibcirccontent" align="center">%s - %s</td>
                    <td class="bibcirccontent" align="center">%s</td>
                    <td class="bibcirccontent" align="center">%s</td>
                    </tr>

                    """ % (borrower_link, title_link, barcode,
                           loaned_on, due_date,
                           nb_renewall, nb_overdue, date_overdue,
                           status, check_notes)

            if int(loans_per_page) <= len(result):

                if int(jloan) == 0:
                    out += """
                    </table>
                    <br \>
                    <table class="bibcirctable">
                    <tr>
                    <td align='center'>%s - %s - %s - %s</td>
                    </tr>
                    </table>
                    <br \>
                    <table class="bibcirctable">
                    <tr>
                    <td><input type=button value='%s'
                    onClick="history.go(-1)" class="formbutton"></td>
                    </tr>
                    </table>
                    <br \>
                    <br \>
                    <br \>
                    </div>
                    </form>
                    """ % ('|<< first page', '<<< previous page',
                           next_link, end_link,
                           _("Back"))

                elif int(jloan) == end:
                    out += """
                    </table>
                    <br \>
                    <table class="bibcirctable">
                    <tr>
                    <td align='center'>%s - %s - %s - %s</td>
                    </tr>
                    </table>
                    <br \>
                    <table class="bibcirctable">
                    <tr>
                    <td><input type=button value='%s'
                    onClick="history.go(-1)" class="formbutton"></td>
                    </tr>
                    </table>
                    <br \>
                    <br \>
                    <br \>
                    </div>
                    </form>
                    """ % (begin_link, previous_link,
                           'next page >>>', 'last page >>|',
                           _("Back"))

                else:
                    out += """
                    </table>
                    <br \>
                    <table class="bibcirctable">
                    <tr>
                    <td align='center'>%s - %s - %s - %s</td>
                    </tr>
                    </table>
                    <br \>
                    <table class="bibcirctable">
                    <tr>
                    <td><input type=button value='%s'
                    onClick="history.go(-1)" class="formbutton"></td>
                    </tr>
                    </table>
                    <br \>
                    <br \>
                    <br \>
                    </div>
                    </form>
                    """ % (begin_link, previous_link,
                           next_link, end_link,
                           _("Back"))
            else:
                out += """
                    </table>
                    <br \>
                    <br \>
                    <br \>
                    <table class="bibcirctable">
                    <tr>
                    <td><input type=button value='%s'
                    onClick="history.go(-1)" class="formbutton"></td>
                    </tr>
                    </table>
                    <br \>
                    <br \>
                    <br \>
                    </div>
                    </form>
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

        <form name="borrower_notification" action="%s/admin/bibcirculation/bibcirculationadmin.py/borrower_notification" method="get" >
             <div class=bibcircbottom>
             <input type=hidden name=borrower_id value=%s>
             <br \>
                  <table class="bibcirctable">
                       <tr>
                            <td class="bibcirctableheader" width="50">%s</td>
                            <td>%s</td>
                       </tr>
                  </table>
                  <table class="bibcirctable">
                       <tr>
                       <td class="bibcirctableheader" width="50">%s</td>
        """% (CFG_SITE_URL,
              borrower_id,
              _("From"),
              _("CERN Library"),
              _("To"))


        out += """

        <td>
        <input type="text" name="borrower_email" size="60" style='border: 1px solid #cfcfcf' value="%s">
        </td>
        </table>
        """ % (email)



        out += """
        <table class="bibcirctable">
             <tr>
                  <td class="bibcirctableheader" width="50">%s</td>
                  <td><input type="text" name="subject" size="60" value="%s" style='border: 1px solid #cfcfcf'></td>
             </tr>
        </table>

        <br \>  <br \>

        <table class="bibcirctable">
             <tr>
                  <td class="bibcirctableheader" width="40">%s</td>
             </tr>
            <tr>
                  <td><textarea rows="10" cols="100" name="message" style='border: 1px solid #cfcfcf'>%s</textarea></td>
                  <td></td>
        """ % (_("Subject"),
               subject,
               _("Message"),
               template)

        out += """
               <td class="bibcirctableheader" valign="top">%s<br \>
                    <select name="template" style='border: 1px solid #cfcfcf'>
                         <option value ="">%s</option>
                         <option value ="overdue_letter">%s</option>
                         <option value ="reminder">%s</option>
                         <option value ="notification">%s</option>
                         <option value ="claim_return">%s</option>
                    </select>
                    <br \><br \>
                    <input type="submit" name="load_template" value=%s class="formbutton">
              </td>
               </tr>
        </table>
        """ % (_("Choose a letter template"),
               _("Templates"),
               _("Overdue letter"),
               _("Reminder"),
               _("Notification"),
               _("Claim return"),
               _("Load"))


        out += """

        <br \> <br \>
        <table class="bibcirctable">
               <tr>
                    <td>
                       <input type=button value=%s onClick="history.go(-1)" class="formbutton">
                       <input type="reset" name="reset_button" value=%s class="formbutton">
                       <input type="submit" name="send_message" value=%s class="formbutton">
                    </td>
               </tr>
        </table>
        <br \> <br \>
        </div>
        </form>
        """ % (_("Back"),
               _("Reset"),
               _("Send"))


        return out


    def tmpl_get_item_loans_details(self, result, recid, infos,
                                    ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += _MENU_

        out += """
            <div class="bibcircbottom">
            <br />
            <form name="borrower_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/get_item_loans_details" method="get" >
            <input type=hidden name=recid value=%s>
            """ % (CFG_SITE_URL,
                   recid)

        out += """
             <br \>
             <table class="bibcirctable">
                    <tr>
                       <td class="bibcirctableheader">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
                       <td class="bibcirctableheader" align="center">%s</td>
                       </tr>

         """% (_("Borrower"),
               _("Barcode"),
               _("Loaned on"),
               _("Due date"),
               _("Renewals"),
               _("Overdue letter"),
               _("Loan status"),
               _("Loan notes"),
               _("Loan options"))


        for (borrower_id, borrower_name, barcode, loaned_on, due_date, nb_renewall, nb_overdue, date_overdue, status, notes, loan_id) in result:

            borrower_link = create_html_link(CFG_SITE_URL +
                                             '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_details',
                                             {'borrower_id': borrower_id, 'ln': ln},
                                             (borrower_name))

            no_notes_link = create_html_link(CFG_SITE_URL +
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_item_loans_notes',
                                          {'loan_id': loan_id, 'recid': recid, 'borrower_id': borrower_id, 'ln': ln},
                                          (_("No notes")))

            see_notes_link = create_html_link(CFG_SITE_URL +
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_item_loans_notes',
                                          {'loan_id': loan_id, 'recid': recid, 'ln': ln},
                                          (_("See notes")))

            if notes == "":
                check_notes = no_notes_link
            else:
                check_notes = see_notes_link

            out += """
            <tr  onMouseOver="this.className='highlight'" onMouseOut="this.className='normal'">
                 <td class="bibcirccontent">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s - %s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">
                   <SELECT style='border: 1px solid #cfcfcf' ONCHANGE="location = this.options[this.selectedIndex].value;">
                      <OPTION VALUE="">Select an option
                      <OPTION VALUE="get_item_loans_details?borrower_id=%s&barcode=%s&loan_id=%s&recid=%s">Renew
                      <OPTION VALUE="loan_return_confirm?barcode=%s">Return
                      <OPTION VALUE="change_due_date_step1?loan_id=%s&borrower_id=%s">Change due date
                      <OPTION VALUE="claim_book_return?borrower_id=%s&recid=%s&template=claim_return">Claim return
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
                   barcode, loan_id, borrower_id,
                   borrower_id, recid,
                   loan_id, borrower_id)

        out += """
        </table>
        <br \>
        <table class="bibcirctable">
             <tr>
                  <td>
                       <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/get_item_details?recid=%s'"
                       value='%s' class='formbutton'>
                  </td>
             </tr>
        </table>
        <br \>
        <br \>
        <br \>
        </div>
        </form>
        """ % (CFG_SITE_URL,
               recid,
               _("Back"))

        return out


    def tmpl_associate_barcode(self, request_id, recid, borrower,
                               ln=CFG_SITE_LANG):


        _ = gettext_set_language(ln)


        (book_title, _book_year, _book_author, book_isbn, _book_editor) =  book_information_from_MARC(recid)

        if book_isbn:
            book_cover = get_book_cover(book_isbn)
        else:
            book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)


        out  = """ """

        out += _MENU_

        (borrower_id, name, email, phone, address, mailbox) = borrower

        out += """
            <form name="return_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/register_new_loan" method="get" >
            <div class="bibcircbottom">
            <input type=hidden name=borrower_id value=%s>
            <input type=hidden name=request_id value=%s>
            <br \>
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
                  request_id,
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
                     <td class="bibcirccontent">%s</td>
                  </tr>
                  <tr>
                     <td class="bibcirccontent"><img style='border: 1px solid #cfcfcf' src="%s" alt="Book Cover"/></td>
                  </tr>
                  <tr>
                     <td class="bibcirctableheader">%s</td>
                  </tr>
                  <tr>
                     <td><input type="text" size="50" name="barcode" style='border: 1px solid #cfcfcf'></td>
                  </tr>
             </table>
             """ % (_("Item"),
                    book_title,
                    str(book_cover),
                    _("Barcode"))

        out += """
              <br \>
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
                       <input type="submit" name="confirm_button" value=%s class="formbutton">
                  </td>
             </tr>
        </table>
        <br \>
        <br \>
        <br \>
        </div>
        </form>
        """ % (_("Back"),
               _("Confirm"))



        return out


    def tmpl_borrower_notes(self, borrower_notes, borrower_id, add_notes,
                            ln=CFG_SITE_LANG):

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_

        out +="""
            <div class="bibcircbottom">
            <form name="borrower_notes" action="%s/admin/bibcirculation/bibcirculationadmin.py/get_borrower_notes" method="get" >
            <br \>
            <br \>
            <table class="bibcirctable">
                  <tr>
                     <td class="bibcirctableheader">%s</td>
                  </tr>
                  """ % (CFG_SITE_URL,
                         _("Notes about borrower"))

        notes = borrower_notes.split('\n')

        for values in notes:
            out += """   <tr>
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
                      <input type=hidden name=borrower_id value=%s>
                  </td>
             </tr>
            </table>

            """ % (_("Confirm"), borrower_id)
        else:
            out += """
            </table>
            <br />
            <br />
            <table class="bibcirctable">
                <tr>
                  <td>
                       <input type='submit' name='add_notes' value='%s' class='formbutton'>
                       <input type=hidden name=borrower_id value=%s>
                  </td>
             </tr>
            </table>

            """ % (_("Add notes"), borrower_id)

        out += """
            <br \>
            <br \>
             <table class="bibcirctable">
             <tr>
                  <td>
                       <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/get_borrower_details?borrower_id=%s'"
                       value=%s class='formbutton'>
                  </td>
             </tr>
             </table>
             <br \>
             <br \>
             <br \>
             </form>
             </div>
        """ % (CFG_SITE_URL,
               borrower_id,
               _("Back"))

        return out

    def tmpl_loans_notes(self, loans_notes, loan_id, recid, borrower_id,
                         add_notes, ln=CFG_SITE_LANG):

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_

        out +="""
            <div class="bibcircbottom">
            <form name="borrower_notes" action="%s/admin/bibcirculation/bibcirculationadmin.py/get_loans_notes" method="get" >
            <br \>
            <br \>
            <table class="bibcirctable">
                  <tr>
                     <td class="bibcirctableheader">%s</td>
                  </tr>
                  """ % (CFG_SITE_URL,
                         _("Notes about loan"))

        notes = loans_notes.split('\n')

        for values in notes:
            out += """   <tr>
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
                      <input type=hidden name=loan_id value=%s>
                      <input type=hidden name=recid value=%s>
                      <input type=hidden name=borrower_id value=%s>
                  </td>
             </tr>
            </table>

            """ % (_("Confirm"), loan_id, recid, borrower_id)

        else:
            out += """
                <tr><td></td></tr>
                <tr><td></td></tr>
                <tr><td></td></tr>
                <tr>
                  <td>
                       <input type='submit' name='add_notes' value='%s' class='formbutton'>
                       <input type=hidden name=loan_id value=%s>
                       <input type=hidden name=recid value=%s>
                       <input type=hidden name=borrower_id value=%s>
                  </td>
             </tr>
            </table>
            """ % (_('Add notes'), loan_id, recid, borrower_id)

        out += """
            <br \>
            <br \>
             <table class="bibcirctable">
             <tr>
                  <td>
                       <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/get_borrower_loans_details?borrower_id=%s'"
                       value=%s class='formbutton'>
                  </td>
             </tr>
             </table>
             <br \>
             <br \>
             <br \>
             </form>
             </div>
        """ % (CFG_SITE_URL,
               borrower_id,
               _("Back"))

        return out


    def tmpl_item_loans_notes(self, loans_notes, loan_id, recid, borrower_id,
                              add_notes, ln=CFG_SITE_LANG):

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_

        out +="""
            <div class="bibcircbottom">
            <form name="borrower_notes" action="%s/admin/bibcirculation/bibcirculationadmin.py/get_item_loans_notes" method="get" >
            <br \>
            <br \>
            <table class="bibcirctable">
                  <tr>
                     <td class="bibcirctableheader">%s</td>
                  </tr>
                  """ % (CFG_SITE_URL,
                         _("Notes about loan"))

        notes = loans_notes.split('\n')

        for values in notes:
            out += """   <tr>
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
                      <input type=hidden name=loan_id value=%s>
                      <input type=hidden name=recid value=%s>
                      <input type=hidden name=borrower_id value=%s>
                  </td>
             </tr>
            </table>

        """ % (_("Confirm"), loan_id, recid, borrower_id)

        else:
            out += """
                <tr><td></td></tr>
                <tr><td></td></tr>
                <tr><td></td></tr>
                <tr>
                  <td>
                       <input type='submit' name='add_notes' value='%s' class='formbutton'>
                       <input type=hidden name=loan_id value=%s>
                       <input type=hidden name=recid value=%s>
                       <input type=hidden name=borrower_id value=%s>
                  </td>
             </tr>
            </table>

            """ % (_("Add notes"), loan_id, recid, borrower_id)

        out += """
            <br \>
            <br \>
             <table class="bibcirctable">
             <tr>
                  <td>
                       <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/get_item_loans_details?recid=%s'"
                       value=%s class='formbutton'>
                  </td>
             </tr>
             </table>
             <br \>
             <br \>
             <br \>
             </form>
             </div>
        """ % (CFG_SITE_URL,
               recid,
               _("Back"))

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
                <br \>
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
                       <input type="submit" name="confirm_button" value=%s class="formbutton">
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
                         <input type="submit" name="confirm_button" value=%s class="formbutton">
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
                       <input type=button value=%s onClick= onClick="location.href='%s'" class="formbutton">
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
        <div class=bibcircbottom>
        <br \><br \>         <br \>
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
        <br \>
        <table class="bibcirctable">
             <tr align="center">
                  <td>
                        <input type=button value="Back" onClick="history.go(-1)" class="formbutton">
                  <input type="submit" value="Search" class="formbutton">
                  </td>
             </tr>
        </table>
        <form>
        <br \><br \>
        <br \>
        <br \>
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
        <br \>
        <table class="bibcirctable">
          <tr align="center">
            <td class="bibcirccontent">
              %s borrowers found
            </td>
          </tr>
        </table>
        <br \>
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
             <br \>
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
        <br \>
        <br \>
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
                       <input type="submit" name="confirm_button" value=%s class="formbutton">
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
                       <input type="submit" name="confirm_button" value=%s class="formbutton">
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
                       <input type=button value='%s' onClick= onClick="location.href='%s/sadmin/bibcirculation/bibcirculationadmin.py'" class="formbutton">
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
            <div class="bibcircbottom">
            <form name="add_new_library_step1_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/add_new_library_step2" method="get" >
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
                       <input type="submit" name="confirm_button" value=%s class="formbutton">
                  </td>
                 </tr>
                </table>
                <br />
                <br />
                </form>
                </div>
                """ % (CFG_SITE_URL, _("New library information"), _("Name"),
                       _("Email"), _("Phone"), _("Address"), _("Notes"),
                       _("Back"), _("Continue"))


        return out

    def tmpl_add_new_library_step2(self, tup_infos, ln=CFG_SITE_LANG):

        _ = gettext_set_language(ln)

        (name, email, phone, address, notes) = tup_infos

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
                </table>
                <br />
                <table class="bibcirctable">
                <tr>
                  <td>
                       <input type=button value=%s onClick="history.go(-1)" class="formbutton">
                       <input type="submit" name="confirm_button" value=%s class="formbutton">
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
                        onClick="location.href='%s'" class="formbutton">
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

    def tmpl_update_library_info_step1(self, ln=CFG_SITE_LANG):
        """
        Template for the admin interface. Search borrower.

        @param ln: language
        """
        _ = gettext_set_language(ln)

        out = """  """

        out += _MENU_

        out += """
        <div class=bibcircbottom>
        <br \><br \>         <br \>
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
        <br \>
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
        <br \><br \>
        <br \>
        <br \>
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
        <div class="bibcircbottom">
        <br \>
        <table class="bibcirctable">
          <tr align="center">
            <td class="bibcirccontent">
              %s library found
            </td>
          </tr>
        </table>
        <br \>
        <table class="bibcirctable">

        """ % (len(result))

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
             <br \>
             """

        out += """
        <table class="bibcirctable">
             <tr align="center">
                  <td><input type=button value=%s
                       onClick="history.go(-1)" class="formbutton"></td>
             </tr>
        </table>
        <br />
        <br \>
        <br \>
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
            <div class="bibcircbottom">
            <form name="update_library_info_step3_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/update_library_info_step4" method="get" >
             <input type=hidden name=library_id value=%s>
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
                </table>
                <br />
                <table class="bibcirctable">
                <tr>
                  <td>
                       <input type=button value=%s
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit" name="confirm_button"
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
            <div class="bibcircbottom">
            <form name="update_library_info_step4_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/update_library_info_step5" method="get" >
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
                </table>
                <br />
                <table class="bibcirctable">
                <tr>
                  <td>
                       <input type=button value=%s
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit" name="confirm_button"
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
                        onClick= onClick="location.href='%s'"
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

    def tmpl_add_new_copy_step1(self, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        out = """  """

        out += _MENU_

        out += """
        <div class=bibcircbottom>
        <form name="add_new_copy_step1_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/add_new_copy_step2" method="get" >
        <br \>
        <br \>
        <br \>
        <input type=hidden name=start value="0">
        <input type=hidden name=end value="10">
        <table class="bibcirctable">
           <tr align="center">
             <td class="bibcirctableheader">Search item by
             <input type="radio" name="f" value="" checked>any field
             <input type="radio" name="f" value="name">year
             <input type="radio" name="f" value="author">author
             <input type="radio" name="f" value="title">title
             <br \>
             <br \>
            </td>
           <tr align="center">
             <td>
               <input type="text" size="50" name="p" style='border: 1px solid #cfcfcf'>
             </td>
           </tr>
        </table>
        <br \>
        <table class="bibcirctable">
             <tr align="center">
               <td>

                  <input type=button value="Back"
                   onClick="history.go(-1)" class="formbutton">
                  <input type="submit" value="Search" class="formbutton">

               </td>
             </tr>
        </table>
        <br \>
        <br \>
        <br \>
        <br \>
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
                                ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = """  """

        out += _MENU_

        (book_title, book_year, book_author, book_isbn, book_editor) = book_information_from_MARC(recid)

        if book_isbn:
            book_cover = get_book_cover(book_isbn)
        else:
            book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)


        out += """
           <form name="add_new_copy_step3_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/add_new_copy_step4" method="get" >
           <div class="bibcircbottom">
                <br \>
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

           <br \>
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
                   _("Editor"),
                   book_editor,
                   _("ISBN"),
                   book_isbn,
                   str(book_cover),
                   _("Copies of %s" % book_title))


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
                      <td width="250"></td>
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
                     <td class="bibcirccontent" width="250"></td>
                 </tr>
                 """ % (barcode, status, library_link, location, loan_period, nb_requests, collection, description)


        out += """
           </table>
           <br \>
          <table class="bibcirctable">
                <tr>
                     <td class="bibcirctableheader">%s</td>
                </tr>
           </table>
           <table class="bibcirctable">
                <tr>
                    <td width="100">%s</td>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=35 name="barcode">
                    </td>
                </tr>
                <tr>
                    <td width="100">%s</td>
                    <td class="bibcirccontent">
                      <select name="library"  style='border: 1px solid #cfcfcf'>

                """ % (_("New copy details"), _("Barcode"), _("Library"))

        for(library_id, name) in libraries:
            out +="""<option value ="%s">%s</option>""" % (library_id, name)

        out += """
                    </select>
                    </td>
                </tr>
                <tr>
                    <td width="100">%s</td>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=35 name="location">
                    </td>
                </tr>
                <tr>
                    <td width="100">%s</td>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=35 name="collection">
                    </td>
                </tr>
                <tr>
                    <td width="100">%s</td>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=35 name="description">
                    </td>
                </tr>
                <tr>
                    <td width="100">%s</td>
                    <td class="bibcirccontent">
                      <select name="loan_period"  style='border: 1px solid #cfcfcf'>
                          <option value ="4 weeks">4 weeks</option>
                          <option value ="1 week">1 week</option>
                          <option value ="reference">reference</option>
                      </select>
                    </td>
                 </tr>
                 <tr>
                    <td width="100">%s</td>
                    <td class="bibcirccontent">
                    <select name="status"  style='border: 1px solid #cfcfcf'>
                          <option value ="available">available</option>
                          <option value ="on loan">on loan</option>
                          <option value ="missing">missing</option>
                    </select>
                    </td>
                 </tr>
                </table>
           <br \>
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
           <br \>
           <br \>
           </div>
           </form>
           """ % (_("Location"), _("Collection"), _("Description"),
                  _("Loan period"), _("Status"), recid)

        return out

    def tmpl_add_new_copy_step4(self, tup_infos, ln=CFG_SITE_LANG):

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

                       <input type="submit" name="confirm_button"
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
                       onClick= onClick="location.href='%s'" class="formbutton">
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

    def tmpl_update_item_info_step1(self, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        out = """  """

        out += _MENU_

        out += """
        <div class=bibcircbottom>
        <form name="update_item_info_step1_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/update_item_info_step2" method="get" >
        <br \>
        <br \>
        <br \>
        <input type=hidden name=start value="0">
        <input type=hidden name=end value="10">
        <table class="bibcirctable">
                <tr align="center">
                  <td class="bibcirctableheader">Search item by
                    <input type="radio" name="f" value="" checked>any field
                    <input type="radio" name="f" value="name">year
                    <input type="radio" name="f" value="email">author
                    <input type="radio" name="f" value="email">title
                    <br \><br \>
                  </td>
                <tr align="center">
                  <td><input type="text" size="50" name="p" style='border: 1px solid #cfcfcf'></td>
                </tr>
        </table>
        <br \>
        <table class="bibcirctable">
               <tr align="center">
                     <td>
                         <input type=button value="Back"
                          onClick="history.go(-1)" class="formbutton">

                         <input type="submit" value="Search" class="formbutton">
                     </td>
                    </tr>
        </table>
        <br \>
        <br \>
        <br \>
        <br \>
        </div>
        <form>
        """ % (CFG_SITE_URL)

        return out

    def tmpl_update_item_info_step2(self, result, ln=CFG_SITE_LANG):
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
        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = """
        """
        out += _MENU_

        (book_title, book_year, book_author, book_isbn, book_editor) = book_information_from_MARC(recid)

        if book_isbn:
            book_cover = get_book_cover(book_isbn)
        else:
            book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)

        out += """
           <form name="update_item_info_step3_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/update_item_info_step4" method="get" >
           <div class="bibcircbottom">
                <br \>
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

           <br \>

           """  % (CFG_SITE_URL,
                   _("Item details"),
                   _("Name"),
                   book_title,
                   _("Author(s)"),
                   book_author,
                   _("Year"),
                   book_year,
                   _("Editor"),
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
           <br \>
           <table class="bibcirctable">
                <tr>
                     <td>
                        <input type=button value="%s"
                         onClick="history.go(-1)" class="formbutton">
                        <input type=hidden name=recid value=%s></td>
                </tr>
           </table>
           <br \>
           <br \>
           </div>
           """ % (_("Back"), recid)

        return out

    def tmpl_update_item_info_step4(self, recid, result, libraries, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        _ = gettext_set_language(ln)

        out = """
        """
        out += _MENU_

        (book_title, book_year, book_author, book_isbn, book_editor) = book_information_from_MARC(recid)

        if book_isbn:
            book_cover = get_book_cover(book_isbn)
        else:
            book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)

        out += """
           <form name="update_item_info_step4_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/update_item_info_step5" method="get" >
           <div class="bibcircbottom">
                <br \>
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

           <br \>

           """  % (CFG_SITE_URL,
                   _("Item details"),
                   _("Name"),
                   book_title,
                   _("Author(s)"),
                   book_author,
                   _("Year"),
                   book_year,
                   _("Editor"),
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
             <table class="bibcirctable">
                <tr>
                    <td width="100">%s</td>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=35 name="barcode" value="%s" readonly>
                    </td>
                </tr>
                <tr>
                    <td width="100">%s</td>
                    <td class="bibcirccontent">
                      <select name="library"  style='border: 1px solid #cfcfcf'>

                """ % (_("Update copy information"),
                       _("Barcode"), result[0],
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
                    <td width="100">%s</td>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=35 name="location" value="%s">
                    </td>
                </tr>
                <tr>
                    <td width="100">%s</td>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=35 name="collection" value="%s">
                    </td>
                </tr>
                <tr>
                    <td width="100">%s</td>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=35 name="description" value="%s">
                    </td>
                </tr>
                <tr>
                    <td width="100">%s</td>
                    <td class="bibcirccontent">
                    <select name="loan_period" style='border: 1px solid #cfcfcf'>
                    """ % (_("Location"), result[4],
                           _("Collection"), result[3],
                           _("Description"), result[5],
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
                    <td width="100">%s</td> <td class="bibcirccontent"><select name="status"  style='border: 1px solid #cfcfcf'>
                    """ % (_("Status"))
        if result[7] == 'available':
            out += """
                          <option value ="available" selected>available</option>
                          <option value ="on loan">on loan</option>
                          <option value ="missing">missing</option>
                          <option value ="requested">requested</option>
                          """
        elif result[7] == 'on loan':
            out += """
                          <option value ="available">available</option>
                          <option value ="on loan" selected>on loan</option>
                          <option value ="missing">missing</option>
                          <option value ="requested">requested</option>
                          """

        elif result[7] == 'requested':
            out += """
                          <option value ="available">available</option>
                          <option value ="on loan">on loan</option>
                          <option value ="missing">missing</option>
                          <option value ="requested" selected>requested</option>
                          """
        else:
            out += """
                          <option value ="available">available</option>
                          <option value ="on loan">on loan</option>
                          <option value ="missing" selected>missing</option>
                          <option value ="requested">requested</option>
                          """
        out += """  </select>
                    </td>
                 </tr>
                </table>
           <br \>
           <table class="bibcirctable">
                <tr>
                     <td>
                       <input type=button value='%s'
                        onClick="history.go(-1)" class="formbutton">
                       <input type="submit" value='%s' class="formbutton">
                       <input type=hidden name=recid value=%s></td>
                </tr>
           </table>
           <br \>
           <br \>
           </div>
           </form>
           """ % (_("Back"), _("Continue"), recid)

        return out

    def tmpl_update_item_info_step5(self, tup_infos, ln=CFG_SITE_LANG):

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_

        out += """
            <div class="bibcircbottom">
            <form name="update_item_info_step5_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/update_item_info_step6" method="get" >
              <br />
              <br />
              <table class="bibcirctable">
                <tr>
                     <td class="bibcirctableheader">%s</td>
                </tr>
             </table>
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
                       <input type="submit" name="confirm_button"
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
                        onClick="location.href='%s'" class="formbutton">
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

    def tmpl_search_library_step1(self, ln=CFG_SITE_LANG):
        """
        Template for the admin interface. Search borrower.

        @param ln: language
        """
        _ = gettext_set_language(ln)

        out = """  """

        out += _MENU_

        out += """
        <div class=bibcircbottom>
        <br \><br \>         <br \>
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
          <br \>
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
        <br \>
        <br \>
        <br \>
        <br \>
        </div>

        """ % (CFG_SITE_URL,
               _("Search library by"),
               _("Back"),
               _("Search"))


        return out

    def tmpl_search_library_step2(self, result, ln=CFG_SITE_LANG):
        """
        @param result: search result
        @param ln: language
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_

        out += """
        <div class="bibcircbottom">
        <br \>
        <table class="bibcirctable">
          <tr align="center">
            <td class="bibcirccontent">
              %s library found
            </td>
          </tr>
        </table>
        <br \>
        <table class="bibcirctable">

        """ % (len(result))

        for (library_id, name) in result:

            library_link = create_html_link(CFG_SITE_URL +
                                            '/admin/bibcirculation/bibcirculationadmin.py/get_library_details',
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
        <br \>
        <table class="bibcirctable">
             <tr align="center">
                  <td>
                    <input type=button value=%s
                     onClick="history.go(-1)" class="formbutton"></td>
             </tr>
        </table>
        <br />
        <br \>
        <br \>
        </form>
        </div>

        """ % (_("Back"))

        return out


    def tmpl_library_notes(self, library_notes, library_id, add_notes,
                           ln=CFG_SITE_LANG):

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_

        out +="""
            <div class="bibcircbottom">
            <form name="borrower_notes" action="%s/admin/bibcirculation/bibcirculationadmin.py/get_library_notes" method="get" >
            <br \>
            <br \>
            <table class="bibcirctable">
                  <tr>
                     <td class="bibcirctableheader">%s</td>
                  </tr>
                  """ % (CFG_SITE_URL,
                         _("Notes about library"))

        notes = library_notes.split('\n')


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
                      <input type=hidden name=library_id value=%s>
                  </td>
             </tr>
            </table>

            """ % (_("Confirm"), library_id)

        else:
            out += """
                <tr><td></td></tr>
                <tr><td></td></tr>
                <tr><td></td></tr>
                <tr>
                  <td>
                       <input type='submit' name='add_notes' value='%s' class='formbutton'>
                       <input type=hidden name=library_id value=%s>
                  </td>
             </tr>
            </table>

            """ % (_("Add notes"), library_id)

        out += """
            <br \>
            <br \>
             <table class="bibcirctable">
             <tr>
                  <td>
                       <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/get_library_details?library_id=%s'"
                       value=%s class='formbutton'>
                  </td>
             </tr>
             </table>
             <br \>
             <br \>
             <br \>
             </form>
             </div>
        """ % (CFG_SITE_URL,
               library_id,
               _("Back"))

        return out



    def tmpl_change_due_date_step1(self, loan_details, loan_id, borrower_id, ln=CFG_SITE_LANG):
        """
        Return the form where the due date can be changed.

        loan_details: list with all the information related with the loan.

        loan_id: identify a loan. It is the primery key of the table
                 crcLOAN.

        borrower_id: identify the borrower. It is also the primary key of
                     the table crcBORROWER.
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
            <br \>
            <br \>
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
            <br \>
             """ % (CFG_SITE_URL, _("Loan information"),
                    _("Title"), book_title_from_MARC(recid),
                    _("Barcode"), barcode,
                    _("Loan date"), loaned_on,
                    _("Due date"), due_date,
                    _("Loan status"), loan_status,
                    _("Loan period"), loan_period,
                    _("Requested ?"), request_status)

        out += """

            <script type="text/javascript" language='JavaScript' src="/jsCalendar/calendar.js"></script>
            <script type="text/javascript" language='JavaScript' src="/jsCalendar/calendar-setup.js"></script>
            <script type="text/javascript" language='JavaScript' src="/jsCalendar/calendar-en.js"></script>
            <style type="text/css"> @import url("/jsCalendar/calendar-blue.css"); </style>

            <table class="bibcirctable">
              <tr align="left">
                <td width="230" class="bibcirctableheader">%s
                  <input type="text" size="12" id="%s" name="due_date" value="%s" style='border: 1px solid #cfcfcf'>
                  <img src="/jsCalendar/jsCalendar.gif" alt="Change due date" id="%s"
                  onmouseover="this.style.background='red';" onmouseout="this.style.background=''">

                  <script type="text/javascript" language='JavaScript'>
                       Calendar.setup({
                           inputField     :    '%s',
                           ifFormat       :    '%%Y-%%m-%%d',
                           button	  :    '%s'
                           });
                  </script>
                </td>
              </tr>
            </table>
            <br \>
            """ % (_("New due date: "), _("due_date"), due_date,
                   _("jsCal"), _("due_date"), _("jsCal"))


        out += """
        <table class="bibcirctable">
             <tr>
                  <td>
                       <input type=hidden name=loan_id value=%s>
                       <input type=hidden name=borrower_id value=%s>

                       <input type=button value=%s
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit" name="confirm_button"
                        value="%s" class="formbutton">


                  </td>
             </tr>
        </table>
        <br \>
        <br \>
        </form>
        </div>
        """ % (loan_id, borrower_id,
               _("Back"), _("Submit new due date"))

        return out

    def tmpl_change_due_date_step2(self, due_date, borrower_id, ln=CFG_SITE_LANG):
        """
        Return a page with the new due date.

        borrower_id: identify the borrower. It is also the primary key of
                     the table crcBORROWER.
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


    def tmpl_create_new_loan_step1(self, borrower, ln=CFG_SITE_LANG):
        """
        Display the borrower's information and a form where it is
        possible to search for an item.

        borrower: list containing borrower's information.
        """

        _ = gettext_set_language(ln)


        out  = """ """

        out += _MENU_

        (borrower_id, name, email, phone, address, mailbox) = borrower

        out += """
            <form name="create_new_loan_form1" action="%s/admin/bibcirculation/bibcirculationadmin.py/create_new_loan_step2" method="get" >
            <div class="bibcircbottom">
            <input type=hidden name=borrower_id value=%s>
            <br \>
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
              <br \>
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
                       <input type="submit" name="confirm_button" value=%s class="formbutton">
                  </td>
             </tr>
        </table>
        <br \>
        <br \>
        <br \>
        </div>
        </form>
        """ % (_("Back"),
               _("Confirm"))



        return out


    def tmpl_create_new_request_step1(self, borrower, result, p, f, ln=CFG_SITE_LANG):
        """
        Display the borrower's information and the form where it is
        possible to search for an item.

        borrower: list with borrower's information.

        result: result of searching for an item, using p and f.

        p: pattern who will be used in the search process.

        f: field who will be used in the search process.
        """

        _ = gettext_set_language(ln)


        if p is None:
            p  = ''

        out  = """ """

        out += _MENU_

        (borrower_id, name, email, phone, address, mailbox) = borrower

        out += """
            <form name="create_new_loan_form1" action="%s/admin/bibcirculation/bibcirculationadmin.py/create_new_request_step1" method="get" >
            <div class="bibcircbottom">
            <input type=hidden name=borrower_id value=%s>
            <input type=hidden name=start value="0">
            <input type=hidden name=end value="10">
            <br \>
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


        out += """
        <table class="bibcirctable">
          <tr align="center">
            <td class="bibcirctableheader">Search item by
            """
        if f == 'year':
            out += """
              <input type="radio" name="f" value="">any field
              <input type="radio" name="f" value="year" checked>year
              <input type="radio" name="f" value="author">author
              <input type="radio" name="f" value="title">title
              """

        elif f == 'author':
            out += """
              <input type="radio" name="f" value="">any field
              <input type="radio" name="f" value="year">year
              <input type="radio" name="f" value="author" checked>author
              <input type="radio" name="f" value="title">title
              """

        elif f == 'title':
            out += """
              <input type="radio" name="f" value="">any field
              <input type="radio" name="f" value="year">year
              <input type="radio" name="f" value="author">author
              <input type="radio" name="f" value="title" checked>title
              """

        else:
            out += """
              <input type="radio" name="f" value="" checked>any field
              <input type="radio" name="f" value="year">year
              <input type="radio" name="f" value="author">author
              <input type="radio" name="f" value="title">title
              """

        out += """
              <br \>
              <br \>
            </td>
          </tr>
          <tr align="center">
          <td><input type="text" size="50" name="p" value='%s' style='border: 1px solid #cfcfcf'></td>
                             </tr>
        </table>
        <br \>
        <table class="bibcirctable">
          <tr align="center">
            <td>

              <input type=button value='%s'
              onClick="history.go(-1)" class="formbutton">
              <input type="submit" value='%s' name='search' class="formbutton">

            </td>
          </tr>
        </table>
        </form>

        """ % (p, _("Back"), _("Search"))

        if result:
            out += """
            <br \>
            <form name="form2" action="%s/admin/bibcirculation/bibcirculationadmin.py/create_new_request_step2" method="get" >
            <table class="bibcirctable">
              <tr width="200">
                <td align="center">
                  <select name="recid" size="12" style='border: 1px solid #cfcfcf; width:40%%'>

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
              <br \>
              <br \>
              <br \>
              </form>
              </div>
              """

        return out

    def tmpl_create_new_request_step2(self, borrower_id, holdings_information, recid, ln=CFG_SITE_LANG):
        """
        This template is used in the user interface. In this template
        it is possible to see all details (loan period, number of copies, location, etc)
        about a book.
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
                          <td class="bibcirccontent" align='right'>
                          <input type=button onClick="location.href='%s/admin/bibcirculation/bibcirculationadmin.py/create_new_request_step3?borrower_id=%s&barcode=%s&recid=%s'"
                          value='%s' class="formbutton"></td>
                     </tr>

                """ % (barcode, library, collection, location,
                       description, loan_period, status, due_date,
                       CFG_SITE_URL, borrower_id, barcode, recid,
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
        This template is used when an user want to request a book. Here it is
        possible to define the 'period of interest'


        @param barcode: book's barcode
        @param ln: language
        """

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_

        out += """

        <script type="text/javascript" language='JavaScript' src="/jsCalendar/calendar.js"></script>
        <script type="text/javascript" language='JavaScript' src="/jsCalendar/calendar-setup.js"></script>
        <script type="text/javascript" language='JavaScript' src="/jsCalendar/calendar-en.js"></script>
        <style type="text/css"> @import url("/jsCalendar/calendar-blue.css"); </style>


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
              <input type="text" size="12" id="%s" name="period_from" value="%s" style='border: 1px solid #cfcfcf'>
              <img src="/jsCalendar/jsCalendar.gif" alt="Change due date" id="%s"
              onmouseover="this.style.background='red';" onmouseout="this.style.background=''">
              <script type="text/javascript" language='JavaScript'>
                Calendar.setup({
                  inputField     :    '%s',
                  ifFormat       :    '%%Y-%%m-%%d',
                  button	 :    '%s'
                });
              </script>
            </td>
          </tr>
        </table>

        <table class="bibcirctable_contents">
          <tr>
            <td width="90" class="bibcirctableheader" align='right'>%s</td>
            <td align='left'>
              <input type="text" size="12" id="%s" name="period_to" value="%s" style='border: 1px solid #cfcfcf'>
              <img src="/jsCalendar/jsCalendar.gif" alt="Change due date" id="%s"
              onmouseover="this.style.background='red';" onmouseout="this.style.background=''">
              <script type="text/javascript" language='JavaScript'>
                Calendar.setup({
                  inputField     :    '%s',
                  ifFormat       :    '%%Y-%%m-%%d',
                  button	 :    '%s'
                });
              </script>
            </td>
          </tr>
        </table>
        <br />
        <br />
       """ % (CFG_SITE_URL, _("Enter the period of interest"),
              _("From:  "), _("from"), datetime.date.today().strftime('%Y-%m-%d'),
              _("jsCal_from"), _("from"), _("jsCal_from"),
              _("To:  "), _("to"), (datetime.date.today() + datetime.timedelta(days=365)).strftime('%Y-%m-%d'),
              _("jsCal_to"), _("to"), _("jsCal_to"))


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
        <br \>
        </form>
        </div>

        """ % (barcode, borrower_id, recid, _('Confirm'))

        return out

    def tmpl_create_new_request_step4(self, ln=CFG_SITE_LANG):
        """
        Last step of the request procedure.

        """

        _ = gettext_set_language(ln)

        out = """ """

        out += _MENU_


        out += """
        <div class="bibcircbottom">
        <br />
        <br \>
        <table class="bibcirctable">
        <tr>
        <td class="bibcirccontent" width="30">%s</td>
        </tr>
        </table>
        <br />
        <br \>
        <table class="bibcirctable">
        <td><input type=button onClick="location.href='%s'" value='%s' class='formbutton'></td>
        </table>
        <br />
        <br \>
        </div>

        """ % (_("A new request has been registered with success."),
               CFG_SITE_URL, _("Back to home"))

        return out

    def tmpl_place_new_request_step1(self, result, key, string, barcode, recid, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        if string is None:
            string = ""

        _ = gettext_set_language(ln)

        (book_title, book_year, book_author, book_isbn, book_editor) = book_information_from_MARC(recid)

        if book_isbn:
            book_cover = get_book_cover(book_isbn)
        else:
            book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)

        out = """
        """
        out += _MENU_

        out += """
        <div class=bibcircbottom>
        <br \>
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
           <br \>

           """  % (_("Item details"),
                   _("Name"), book_title,
                   _("Author(s)"), book_author,
                   _("Year"), book_year,
                   _("Editor"), book_editor,
                   _("ISBN"), book_isbn,
                   _("Barcode"), barcode,
                   str(book_cover))

        out += """
        <form name="step1_form1" action="%s/admin/bibcirculation/bibcirculationadmin.py/place_new_request_step1" method="get" >
        <input type=hidden name=barcode value='%s'>
        <input type=hidden name=recid value='%s'>
        <br \>
        <br \>
        <br \>
          <table class="bibcirctable">

            """  % (CFG_SITE_URL, barcode, recid)

        if CFG_CERN_SITE == 1:

            out += """
                 <tr>
                   <td width="105" class="bibcirctableheader" align="center">Search user by

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
                   <td width="105" class="bibcirctableheader" align="center">Search borrower by

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

        """ % (string)

        if result:
            out += """
            <br \>
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
              <br \>
              <br \>
              <br \>
              </div>
              """

        return out


    def tmpl_place_new_request_step2(self, barcode, recid, user_info, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        (book_title, book_year, book_author, book_isbn, book_editor) = book_information_from_MARC(recid)

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
            <div class="bibcircbottom">
            <form name="step2_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/place_new_request_step3" method="get" >
            <input type=hidden name=barcode value='%s'>
            <input type=hidden name=recid value='%s'>
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
              <br \>
              """ % (CFG_SITE_URL, barcode, recid,
                     _("Item details"),
                     _("Name"), book_title,
                     _("Author(s)"), book_author,
                     _("Year"), book_year,
                     _("Editor"), book_editor,
                     _("ISBN"), book_isbn,
                     _("Barcode"), barcode,
                     str(book_cover))

        out += """
              <br />
              <table class="bibcirctable">
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">
                    <input type="text" style='border: 1px solid #cfcfcf' size=45 value="%s" name="ccid" readonly>
                    </td>
                </tr>
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=45 value="%s" name="name" readonly>
                    </td>
                </tr>
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=45 value="%s" name="email">
                    </td>
                </tr>
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=45 value="%s" name="phone">
                    </td>
                 </tr>
                  <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=45 value="%s" name="address">
                    </td>
                 </tr>
                  <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=45 value="%s" name="mailbox">
                    </td>
                 </tr>
                </table>
                <br />
                """ % (_("CCID"), ccid,
                       _("Name"), name,
                       _("Email"), email,
                       _("Phone"), phone,
                       _("Address"), address,
                       _("Mailbox"), mailbox)

        out += """

                 <script type="text/javascript" language='JavaScript' src="/jsCalendar/calendar.js"></script>
                 <script type="text/javascript" language='JavaScript' src="/jsCalendar/calendar-setup.js"></script>
                 <script type="text/javascript" language='JavaScript' src="/jsCalendar/calendar-en.js"></script>
                 <style type="text/css"> @import url("/jsCalendar/calendar-blue.css"); </style>

                <table class="bibcirctable">
                  <tr class="bibcirctableheader">
                    <td>%s</td>
                  </tr>
                </table>
                <br />
                <table class="bibcirctable">
                  <tr>
                    <td width="40" class="bibcirctableheader" align='right'>%s</td>
                    <td align='left'>
                    <input type="text" size="12" id="%s" name="period_from" value="%s" style='border: 1px solid #cfcfcf'>
                    <img src="/jsCalendar/jsCalendar.gif" alt="Change due date" id="%s"
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
                </table>
                <table class="bibcirctable">
                  <tr>
                    <td width="40" class="bibcirctableheader" align='right'>%s</td>
                    <td align='left'>
                    <input type="text" size="12" id="%s" name="period_to" value="%s" style='border: 1px solid #cfcfcf'>
                    <img src="/jsCalendar/jsCalendar.gif" alt="Change due date" id="%s"
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
                </table>
                <br />
                <br />
                <table class="bibcirctable">
                <tr>
                  <td>
                       <input type=button value=%s
                        onClick="history.go(-1)" class="formbutton">

                       <input type="submit" name="confirm_button"
                       value=%s class="formbutton">

                  </td>
                 </tr>
                </table>
                </form>
                <br />
                <br />
                </div>
                """ % (_("Enter the period of interest"),
                       _("From:  "), _("from"), datetime.date.today().strftime('%Y-%m-%d'),
                       _("jsCal_from"), _("from"), _("jsCal_from"),
                       _("To:  "), _("to"), (datetime.date.today() + datetime.timedelta(days=365)).strftime('%Y-%m-%d'),
                       _("jsCal_to"), _("to"), _("jsCal_to"),
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
        <br \>
        <table class="bibcirctable">
        <tr>
        <td class="bibcirccontent" width="30">%s</td>
        </tr>
        </table>
        <br />
        <br \>
        <table class="bibcirctable">
        <td><input type=button onClick="location.href='%s'" value='%s' class='formbutton'></td>
        </table>
        <br />
        <br \>
        </div>

        """ % (_("A new request has been registered with success."),
               CFG_SITE_URL, _("Back to home"))

        return out

    def tmpl_place_new_loan_step1(self, result, key, string, barcode, recid, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        if string is None:
            string = ""

        _ = gettext_set_language(ln)

        (book_title, book_year, book_author, book_isbn, book_editor) = book_information_from_MARC(recid)

        if book_isbn:
            book_cover = get_book_cover(book_isbn)
        else:
            book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)

        out = """
        """
        out += _MENU_

        out += """
        <div class=bibcircbottom>
        <br \>
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
           <br \>

           """  % (_("Item details"),
                   _("Name"), book_title,
                   _("Author(s)"), book_author,
                   _("Year"), book_year,
                   _("Editor"), book_editor,
                   _("ISBN"), book_isbn,
                   _("Barcode"), barcode,
                   str(book_cover))

        out += """
        <form name="step1_form1" action="%s/admin/bibcirculation/bibcirculationadmin.py/place_new_loan_step1" method="get" >
        <input type=hidden name=barcode value='%s'>
        <input type=hidden name=recid value='%s'>
        <br \>
        <br \>
        <br \>
          <table class="bibcirctable">

            """  % (CFG_SITE_URL, barcode, recid)

        if CFG_CERN_SITE == 1:

            out += """
                 <tr>
                   <td width="105" class="bibcirctableheader" align="center">Search user by

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
                   <td width="105" class="bibcirctableheader" align="center">Search borrower by

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

        """ % (string)

        if result:
            out += """
            <br \>
            <form name="step1_form2" action="%s/admin/bibcirculation/bibcirculationadmin.py/place_new_loan_step2" method="get" >
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
              <br \>
              <br \>
              <br \>
              </div>
              """

        return out

    def tmpl_place_new_loan_step2(self, barcode, recid, user_info, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        (book_title, book_year, book_author, book_isbn, book_editor) = book_information_from_MARC(recid)

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
            <div class="bibcircbottom">
            <form name="step2_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/place_new_loan_step3" method="get" >
            <input type=hidden name=barcode value='%s'>
            <input type=hidden name=recid value='%s'>
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
              <br \>
              """ % (CFG_SITE_URL, barcode, recid,
                     _("Item details"),
                     _("Name"), book_title,
                     _("Author(s)"), book_author,
                     _("Year"), book_year,
                     _("Editor"), book_editor,
                     _("ISBN"), book_isbn,
                     _("Barcode"), barcode,
                     str(book_cover))

        out += """
              <br />
              <table class="bibcirctable">
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">
                    <input type="text" style='border: 1px solid #cfcfcf' size=45 value="%s" name="ccid" readonly>
                    </td>
                </tr>
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=45 value="%s" name="name" readonly>
                    </td>
                </tr>
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=45 value="%s" name="email">
                    </td>
                </tr>
                <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=45 value="%s" name="phone">
                    </td>
                 </tr>
                  <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=45 value="%s" name="address">
                    </td>
                 </tr>
                  <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">
                      <input type="text" style='border: 1px solid #cfcfcf' size=45 value="%s" name="mailbox">
                    </td>
                 </tr>
                </table>
                <br />
                """ % (_("CCID"), ccid,
                       _("Name"), name,
                       _("Email"), email,
                       _("Phone"), phone,
                       _("Address"), address,
                       _("Mailbox"), mailbox)

        out += """

                 <script type="text/javascript" language='JavaScript' src="/jsCalendar/calendar.js"></script>
                 <script type="text/javascript" language='JavaScript' src="/jsCalendar/calendar-setup.js"></script>
                 <script type="text/javascript" language='JavaScript' src="/jsCalendar/calendar-en.js"></script>
                 <style type="text/css"> @import url("/jsCalendar/calendar-blue.css"); </style>

                <table class="bibcirctable">
                  <tr class="bibcirctableheader">
                    <td>%s</td>
                  </tr>
                </table>
                <table class="bibcirctable">
                  <tr>
                    <td width="70">%s</td>
                    <td class="bibcirccontent">%s</td>
                  </tr>
                </table>
                <table class="bibcirctable">
                  <tr>
                    <td width="70">%s</td>
                    <td align='left'>
                    <input type="text" size="12" id="%s" name="due_date" value="%s" style='border: 1px solid #cfcfcf'>
                    <img src="/jsCalendar/jsCalendar.gif" alt="Change due date" id="%s"
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
                </table>
                <br />
                <br />
                <table class="bibcirctable">
                  <tr>
                    <td class="bibcirctableheader" width="70">%s</td>
                  </tr>
                </table>
                <table class="bibcirctable">
                  <tr>
                    <td><textarea name='notes' rows="5" cols="40" style='border: 1px solid #cfcfcf'></textarea></td>
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

                       <input type="submit" name="confirm_button"
                       value=%s class="formbutton">

                  </td>
                 </tr>
                </table>
                </form>
                <br />
                <br />
                </div>
                """ % (_("Loan information"),
                       _("Loan date"), datetime.date.today().strftime('%Y-%m-%d'),
                       _("Due date"), _("due_date"), renew_loan_for_X_days(barcode),
                       _("jsCal"), _("due_date"), _("jsCal"),
                       _("Write notes"), _("Back"), _("Continue"))

        return out
