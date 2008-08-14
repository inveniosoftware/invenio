# -*- coding: utf-8 -*-
##
## $Id$
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
from invenio.urlutils import create_html_link
from invenio.config import CFG_SITE_URL, CFG_SITE_LANG
from invenio.messages import gettext_set_language
from invenio.search_engine import get_fieldvalues
import invenio.bibcirculation_dblayer as db

_MENU_ = """

       <div id="cdlhead">
       <map name="Navigation_Bar" id="cdlnav">
       <div id="bibcircmenu" class="cdsweb">
       <h2><a name="localNavLinks">Main navigation links:</a></h2>
       <ul>
        <li>
            <a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/manage_holdings">Home</a>
        </li>


     <li class="hassubmenu">
         <a href="None">Borrower</a>
         <ul class="subsubmenu" style="width:11.5em;">
          <li><a href = "%(url)s/admin/bibcirculation/bibcirculationadmin.py/borrower_search">Search</a></li>
          <li><a href = "%(url)s/admin/bibcirculation/bibcirculationadmin.py/borrower_notification">Notify</a></li>
            </ul>
        </li>

     <li class="hassubmenu">
         <a href="None">Items</a>
         <ul class="subsubmenu" style="width:11.5em;">
          <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/holdings_search">Search</a></li>
          <li><a href="None"># - Add</a></li>
             <li><a href="None"># - Remove</a></li>
             <li><a href="None"># - Update Info(?)</a></li>
            </ul>
        </li>


     <li class="hassubmenu">
         <a href="None">Loans</a>
         <ul class="subsubmenu" style="width:16.5em;">
          <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk"># - On library desk</a></li>
             <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/loan_return">Returned</a></li>
             <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/get_pending_loan_request">List of pending requests</a></li>
             <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/all_requests">List of all requests</a></li>
             <li><a href="%(url)s/admin/bibcirculation/bibcirculationadmin.py/all_loans">List of all loans</a></li>
             <li><a href="None"># - Stats</a></li>
            </ul>
        </li>

     <li class="hassubmenu">
         <a href="None">Help</a>
         <ul class="subsubmenu" style="width:12.5em;">
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


    def tmpl_index(self, ln=CFG_SITE_LANG):
        """
        @param ln=language
        """

        out = """

        <a href="%s/admin/bibcirculation/bibcirculationadmin.py/manage_holdings">Manage Holdings</a>
        <br \>
        <br \>

        """ % (CFG_SITE_URL)

        return out




    def tmpl_infobox(self, infos, ln=CFG_SITE_LANG):
        """
        Display len(infos) information fields
        @param infos: list of strings
        @param ln=language
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

    def tmpl_holdings_information(self, recid, status, barcode, hold_details,
                                  due_date, nb_requests, infos,
                                  ln=CFG_SITE_LANG):
        """
        @param recid: recID - CDS Invenio record identifier
        @param ln: language of the form
        """
        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += """
        <form name="info_form" action="%s/record/%s/holdings/request" method="get" >
        """ % (CFG_SITE_URL, recid)

        for (loan_period, location) in hold_details:
            out += """
                <table class="bibcirctable">
                     <tr>
                          <td class="bibcirctableheader" width="50">%s</td>
                          <td class="bibcirccontent" width="600"></td>
                     </tr>
                     <tr>
                          <td class="bibcirctableheader" width="50">%s</td>
                          <td class="bibcirccontent" width="600">%s</td>
                     </tr>
                     <tr>
                          <td class="bibcirctableheader" width="50">%s</td>
                          <td class="bibcirccontent" width="600">%s</td>
                     </tr>
                     <tr>
                          <td class="bibcirctableheader" width="50">%s</td>
                          <td class="bibcirccontent" width="600"> - </td>
                     </tr>
                </table>
            """ % (_("Holding details"),
                   _("Loan period"),
                   loan_period,
                   _("Location"),
                   location,
                   _("Collection"))

        out += """
                <br \>
                <table class="bibcirctable">
                     <tr>
                          <td class="bibcirctableheader" width="50">%s</td>
                          <td class="bibcirccontent" width="600"></td>
                     </tr>
                     <tr>
                          <td class="bibcirctableheader" width="50">%s</td>
                          <td class="bibcirccontent" width="600">%s</td>
                     </tr>
                      <tr>
                          <td class="bibcirctableheader" width="50">%s</td>
                          <td class="bibcirccontent" width="600">%s</td>
                     </tr>
                     <tr>
                          <td class="bibcirctableheader" width="50">%s</td>
                          <td class="bibcirccontent" width="600">%s</td>
                     </tr>
                </table>

                <input type=hidden name=due_date value=%s>
                <input type=hidden name=barcode value=%s>
        """ % (_("Loan details"),
                   _("Status"),
                   status,
                   _("No of requests"),
                   len(nb_requests),
                   _("Due date"),
                   due_date,
               due_date,
                   barcode)

        out += """
        <br \>
        <table class="bibcirctable">
             <td><input type="submit" name="request_button" value=%s class="formbutton"></td>
        </table>
        <br \>
        </form>
        """ % (_("Request"))

        return out

    def tmpl_search_result(self, result, ln=CFG_SITE_LANG):
        """
        @param result: search result
        @param ln: language of the form
        """

        _ = gettext_set_language(ln)
        out = """ """
        out += _MENU_

        out += """
        <div class="bibcircbottom">
        </form>
        <br \>
        <br \>
        <table class="bibcirctable">
        """

        for (uid, name) in result:

            borrower_link = create_html_link(CFG_SITE_URL +
                                             '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_details',
                                             {'borrower_id': uid, 'ln': ln},
                                             (name))

            out += """
            <tr align="center">
                 <td class="bibcirccontent" width="70">%s
                 <input type=hidden name=uid value=%s></td>
            </tr>
            """ % (borrower_link, uid)

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

    def tmpl_yourloans(self, result, uid, infos, ln=CFG_SITE_LANG):
        """
        @param result: loans of an user ID
        @param uid: user ID
        @param ln: language of the form
        """
        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        if len(result)==0:
            out += """
            <table class="bibcirctable_contents">
                 <td class="bibcirccontent" width="30">%s</td>
            </table>
            <br /> <br \>
            """ % (_("NO LOANS."))

        else:
            out += """<table class="bibcirctable">
                     <tr>
                     <td class="bibcirctableheader" width="500">%s</td>
                     <td class="bibcirctableheader">%s</td>
                     <td class="bibcirctableheader">%s</td>
                     </tr>
                     """ % (_("Item"), _("Loaned on"), _("Due date"))

            for(recid, barcode, loaned_on, due_date) in result:

                renew_link = create_html_link(CFG_SITE_URL +
                                         '/yourloans/display',
                                         {'barcode': barcode},
                                         (_("Renew")))

                title = ''.join(get_fieldvalues(recid, "245__a"))

                out += """
                <tr>
                <td class="bibcirccontent" width="500">%s</td>
                 <td class="bibcirccontent">%s</td>
                 <td class="bibcirccontent">%s</td>
                <td class="bibcirccontent">%s</td>
                </tr>
                """ % (title, loaned_on, due_date, renew_link)

                renew_all_link = create_html_link(CFG_SITE_URL +
                                          '/yourloans/display',
                                          {'borrower': uid},
                                          (_("Renew all loans")))

            out += """</table>
                          <br />
                          <table class="bibcirctable">
                          <tr>
                          <td class="bibcirccontent" width="70">%s</td>
                          </tr>
                          </table>
            """ % (renew_all_link)

        return out

    def tmpl_new_loan_request(self,
                              uid,
                              recid,
                              barcode,
                              ln=CFG_SITE_LANG):
        """
        @param uid: user ID
        @param recid: recID - CDS Invenio record identifier
        @param ln: language of the form
        """

        #raise repr(barcode)

        _ = gettext_set_language(ln)


        today = datetime.date.today()
        out = """
        <form name="request_form" action="%s/record/%s/holdings/send" method="get" >
        <div class="bibcirctableheader" align="center">Enter your period of interest</div>
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
               _("From"),
               _("Year"),
               _("Month"),
               _("Day"))


        out += """
        <tr>
             <td class="bibcirccontent" width="30"></td>
             <td class="bibcirccontent" width="30"><input size=4 name="from_year" value=%(from_year)s></td>
             <td class="bibcirccontent" width="30"><input size=2 name="from_month" value=%(from_month)s></td>
             <td class="bibcirccontent" width="30"> <input size=2 name="from_day" value=%(from_day)s></td>
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
             <td class="bibcirccontent" width="30"><input size=4 name="to_year" value=%(to_year)s></td>
             <td class="bibcirccontent" width="30"><input size=2 name="to_month" value=%(to_month)s></td>
             <td class="bibcirccontent" width="30"><input size=2 name="to_day" value=%(to_day)s></td>
        </tr>
        </table>
        <br /> <br \>
        """

        out += """
        <table class="bibcirctable_contents">
             <tr>
                  <td align="center">
                                <input type=button value="Back/Cancel" onClick="history.go(-1)" class="formbutton">
                       <input type="submit" name="submit_button" value="%(submit_button)s" class="formbutton">

                  </td>
                  <td width="10"><input type=hidden name=barcode value=%(barcode)s></td>
        </tr>
        </table>
        <br /> <br \>
        </form>
        """

        out = out % {'url': CFG_SITE_URL,
                     'from_year' : today.year,
                     'from_month' : today.month,
                     'from_day': today.day,
                     'to_year': today.year,
                     'to_month': today.month + 1,
                     'to_day': today.day,
                     'submit_button': ('Confirm'),
                     'recid': recid,
                     'uid': uid,
                     'barcode': barcode
                     }

        return out

    def tmpl_new_loan_request_send(self, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        out = """
        <br /> <br \>
        <table class="bibcirctable">
             <td class="bibcirccontent" width="30">%s</td>
        </table>
        <br /> <br \>
        """ % (_("Your request has been sent."))

        return out


    def tmpl_next_loan_request_done(self, ln=CFG_SITE_LANG):
        """
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
        </div>
        """ % (_("Done!."))

        return out

    def tmpl_get_pending_loan_request(self, status, ln=CFG_SITE_LANG):
        """
        @param status: all items with status = pending
        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        out = """
        """
        out += _MENU_

        if len(status)==0:
            out += """
            <div class="bibcircbottom">
            <br /> <br \>            <br /> <br \>
            <table class="bibcirctable_contents">
                 <td class="bibcirccontent" align="center">%s</td>
            </table>
            <br /> <br \>            <br />
            <table class="bibcirctable_contents">
            <td align="center">
            <input type=button value="Back" onClick="history.go(-1)" class="formbutton">
            </td>
            </table>
            <br \>
            </div>
            """ % (_("No more requests are pending."))

        else:

            out += """
            <form name="list_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/get_pending_loan_request" method="get" >
            <div class="bibcircbottom">
            <br />
            <table class="bibcirctable">
            <tr>
            <td class="bibcirctableheader" width="90">
            Show list of
            </td>
            <td width="200">
                       <select name="show"  style='border: 1px solid #cfcfcf'>
                          <option value ="all">all pending requests</option>
                          <option value ="on_loan">pending requests for holdings 'ON LOAN'</option>
                          <option value ="available">pending requests for holdings 'AVAILABLE'</option>
                    </select>
            </td>
            <td>
            <input type="submit" name="ok_button" value="OK" class="formbutton">
            </td>
            </tr>
            </table>
            <br />
            <hr>
            <br />
            </form>
            <form name="list_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/update_loan_request_status" method="get" >
             <table class="bibcirctable">
                    <tr>
                       <td class="bibcirctableheader" width="20"></td>
                                <td class="bibcirctableheader" width="100">%s</td>
                                <td class="bibcirctableheader" width="150">%s</td>

                                <td class="bibcirctableheader" width="30">%s</td>
                                <td class="bibcirctableheader" width="30">%s</td>
                    </tr>
         """% (CFG_SITE_URL,
               CFG_SITE_URL,
               _("Name"),
               _("Item"),
               _("From"),
               _("To"))

            for (id_lr, id_bibrec,  nickname, date_from, date_to) in status:

                title = ''.join(get_fieldvalues(id_bibrec, "245__a"))

                out += """
                <tr>
                 <td align="center" width="20"><input type="checkbox" name="check_id_list" value="%s"></td>
                 <td class="bibcirccontent" width="100">%s</td>
                 <td class="bibcirccontent" width="150">%s</td>

                 <td class="bibcirccontent" width="30">%s</td>
                 <td class="bibcirccontent" width="30">%s</td>
                </tr>
                """ % (id_lr, nickname, title, date_from, date_to)

            out += """</table>
                  <br />
                  <table class="bibcirctable">
                       <tr>
                            <td>
                                 <input type="submit" name="approve_button" value=%s class="formbutton">
                                 <input type="submit" name="cancel_button" value=%s class="formbutton">
                                        <input type="button" onClick="window.print()" value="Print This Page"/ class="formbutton">
                            </td>
                           </tr>
                  </table>
                  <br />
                  </div>
                  </form>
                  """ % (_("Approve"),
                         _("Cancel"))

        return out


    def tmpl_get_next_waiting_loan_request(self, status,
                                           barcode, ln=CFG_SITE_LANG):
        """
        @param status: next waiting loan
        @param barcode: item's barcode
        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        out = """
        """
        out += _MENU_


        if len(status)==0:
            out += """
            <div class="bibcircbottom">
            <br /> <br \>            <br /> <br \>
            <table class="bibcirctable_contents">
                 <td class="bibcirccontent" align="center">%s</td>
            </table>
            <br /> <br \>            <br />
            <table class="bibcirctable_contents">
            <td align="center">
            <input type=button value="Back" onClick="history.go(-1)" class="formbutton">
            </td>
            </table>
            <br \>
            </div>
            """ % (_("No more requests are waiting."))




        else:
            out += """
            <form name="list_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/update_next_loan_request_status" method="get" >
            <div class="bibcircbottom">
            <br \>
             <table class="bibcirctable">
                    <tr>
                       <td class="bibcirctableheader" width="30"></td>
                         <td class="bibcirctableheader">%s</td>
                         <td class="bibcirctableheader">%s</td>
                         <td class="bibcirctableheader">%s</td>
                         <td class="bibcirctableheader">%s</td>
                       <td width="10"><input type=hidden name=barcode value=%s></td>
                    </tr>

                    """% (CFG_SITE_URL,
                          _("Name"),
                          _("Status"),
                          _("From"),
                          _("To"),
                          barcode)

            for (id_lr, nickname, status, date_from, date_to) in status:
                out += """
                <tr>
                 <td align="left" width="30"><input type="checkbox" name="check_id" value="%s"></td>
                <td class="bibcirccontent">%s</td>
                 <td class="bibcirccontent">%s</td>
                 <td class="bibcirccontent">%s</td>
                 <td class="bibcirccontent">%s</td>
                 </tr>
                 """ % (id_lr, nickname, status, date_from, date_to)

            out += """</table>

                  <br \>
                  <table class="bibcirctable">
                       <tr>
                            <td>
                                 <input type="submit" name="approve_button" value=%s class="formbutton">
                                 <input type="submit" name="cancel_button" value=%s class="formbutton">
                            </td>
                           </tr>
                  </table>
                  </form>
                  <br \>
                  <br \>
                  <br \>
                  </div>
                  """ % (_("Approve"),
                         _("Cancel"))

        return out

    def tmpl_loan_return(self, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        out = """
        """
        out += _MENU_

        out += """
        <form name="return_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/loan_return_confirm" method="get" >
             <div class=bibcircbottom>
             <br \>
             <br \>
                <br \>
                  <table class="bibcirctable_contents">
                       <tr align="center">
                            <td class="bibcirctableheader">%s</td>
                            <td><input type="text" size=45 name="barcode" style='border: 1px solid #cfcfcf'></td>
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

    def tmpl_loan_return_confirm(self, borrower_name,
                                 id_bibrec, barcode, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
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

        title = ''.join(get_fieldvalues(id_bibrec, "245__a"))

        out += """
        <tr>
             <td class="bibcirctableheader" width="70">%s</td>
             <td class="bibcirccontent" width="600">%s</td>
        </tr>
        <tr>
             <td class="bibcirctableheader" width="70">%s</td>
             <td class="bibcirccontent" width="600">%s</td>
        </tr>

        <input type=hidden name=recID value=%s>
        <input type=hidden name=barcode value=%s>
        """ % (_("Borrower name"),
               borrower_name,
               _("Item name"),
               title,
               id_bibrec,
               barcode)


        out += """
        </table>
        <br \>
        <table class="bibcirctable_contents">
             <tr align="center">
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


    def tmpl_manage_holdings(self, pending_request, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        out = """
        """
        out += _MENU_

        out += """
        <div class=bibcircbottom>
        <br \>
        <div class="subtitle">
        Welcome to CDS Invenio Holdings Admin
        </div>
        <br \>
             <table class="bibcirctable">
                    <tr>
                         <td class="bibcirctableheader">Loans</td>
                         <td class="bibcirctableheader"></td>
                    </tr>
        """

        if pending_request == "0":
            out += """
                <tr>
                     <td class="bibcircok">You don't have any pending loans requests</td>
                     <td></td>
                </tr>
                """
        else:
            out +="""
            <tr>
                 <td class="bibcircok">You have %s pending loan(s) request(s)</td>
                 <td></td>
            </tr>

            <tr>
                 <td class="bibcircwarning"># -> section not finished!</td>
                 <td></td>
            </tr>
            """ % (pending_request)

        out += """
             <tr>
                    <td></td>
                    <td></td>
               </tr>
        </table>
        <br \><br \><br \><br \> <br \> <br \> <br \> <br \> <br \> <br \>
        </div>
        """

        return out



    def tmpl_borrower_search(self, ln=CFG_SITE_LANG):
        """
         @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        out = """
        """
        out += _MENU_

        out += """
        <div class=bibcircbottom>
        <br \><br \>         <br \>
        <form name="borrower_search" action="%s/admin/bibcirculation/bibcirculationadmin.py/search_result" method="get" >
             <table class="bibcirctable">
                  <tr align="center">
                        <td class="bibcirctableheader">%s

                    <select name="column" style='border: 1px solid #cfcfcf'>
                          <option value ="name">%s</option>
                          <option value ="email">%s</option>
                          <option value ="phone">%s</option>
                          <option value ="id">%s</option>
                    </select>

                  <input type="text" size="50" name="str" style='border: 1px solid #cfcfcf'></td>
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
        <br \><br \>        <br \><br \>
        </div>

        """ % (CFG_SITE_URL,
               _("Search borrower by"),
               _("name"),
               _("email"),
               _("phone"),
               _("id"))

        return out

    def tmpl_send_borrowers_notification(self, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        out = """
        """

        out += _MENU_

        return out

    def tmpl_holdings_search(self, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        out = """
        """

        out += _MENU_

        out += """
        <div class=bibcircbottom>
        <form name="search_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/item_search_result" method="get" >
        <br \>
        <br \>
        <br \>
        <table class="bibcirctable">
                            <tr align="center">
                                        <td class="bibcirctableheader">Search item by

                                        <select name="f" style='border: 1px solid #cfcfcf'>
                                        <option value ="">any field</option>
                                        <option value ="year">year</option>
                                        <option value ="author">author</option>
                                        <option value ="title">title</option>
                                        </select>

                                        <input type="text" size="50" name="p" style='border: 1px solid #cfcfcf'></td>
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
        <br \><br \>     <br \>  <br \>
        <form>
        </div>


        """ % (CFG_SITE_URL)

        return out

    def tmpl_item_search_result(self, result, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        out = """
        """
        out += _MENU_

        out += """
        <div class="bibcircbottom">
        <br />
        <br />
        <table class="bibcirctable">
        """

        for (recid) in result:

            title = ''.join(get_fieldvalues(recid, "245__a"))
            title_link = create_html_link(CFG_SITE_URL +
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_item_details',
                                          {'recid': recid, 'ln': ln},
                                          (title))

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

    def tmpl_loan_on_desk(self, result, borrower, barcode, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        out = """
        """
        out += _MENU_

        out += """
        <form name="return_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk" method="post" >
             <div class=bibcircbottom>
             <br \>
             <br \>
                  <table class="bibcirctable">
                       <tr>
                            <td class="bibcirctableheader" width="77">%s</td>
                            <td><input size=50 name="borrower_name" value="%s" style='border: 1px solid #cfcfcf'></td>



                                        <td class="bibcirctableheader">Search borrower by</td>
                                        <td>
                                        <select name="column"  style='border: 1px solid #cfcfcf'>
                                        <option value ="name">name</option>
                                        <option value ="email">e-mail</option>
                                        <option value ="phone">phone</option>
                                        <option value ="id">id</option>
                                        </select>
                                        </td>
                                        <td><input type="text" size="50" name="string" style='border: 1px solid #cfcfcf'></td>
                                        <td>
                                        <input type="submit" value="Search" class="formbutton">
                                        </td>

                       </tr>
        """% (CFG_SITE_URL,
              _("Borrower"),
              borrower)


        if result:

            out += """
            <table class="bibcirctable">
            <tr>

            <td ALIGN="right">
            <select name="borrower" multiple size="5"
            style='border: 1px solid #cfcfcf; width:50%' > """

            for (uid, borrower) in result:

                out += """
                      <option value ="%s">%s
                    """ % (borrower, borrower)

            out += """
                    </select>
                    </td>
                    </tr>
                    </table>
                    <table class="bibcirctable">
                    <tr>
                        <td ALIGN="right">
                        <input type="submit" value="Add user" class="formbutton">
                        </td>
                    </tr>
                    </table>
                    """

        out += """
        <table class="bibcirctable">
                     <tr>

                  <td class="bibcirctableheader" width="77">%s</td>

                        <td><textarea rows="5" cols="43" name="barcode" style='border: 1px solid #cfcfcf'></textarea></td>


                       </tr>
         </table>

        """ % (_("Barcode(s)"))


        out += """
        <br \>        <br \>
        <table class="bibcirctable">
             <tr>
                  <td>
                       <input type=button value=%s onClick="history.go(-1)" class="formbutton">
                       <input type="reset" name="reset_button" value=%s class="formbutton">
                       <input type="submit" name="confirm_button" value=%s class="formbutton">
                 </td>
                                 <td class="bibcircwarning"># - Section not finished! Testing barcode reader.</td>
             </tr>
        </table>
        <br \>
        <br \>
        </div>
        </form>
        """ % (_("Back"),
               _("Reset"),
               _("Confirm"))

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
        </div>
        """ % (_("Notification has been sent!."))

        return out

    def tmpl_register_new_loan_done(self, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        out = """
              """
        out += _MENU_

        out += """
        <div class="bibcircbottom">
        <br />
        <br />
        <br />
        <table class="bibcirctable">
             <td class="bibcirccontent" width="30">%s</td>
        </table>
        <br />
        <br />
        <br />
        </div>
        """ % (_("Done!"))

        return out

    def tmpl_loan_on_desk_confirm(self, barcode,
                                  borrower, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page0
        """

        _ = gettext_set_language(ln)

        out = """
        """
        out += _MENU_

        borrower_id = db.get_borrowerID(borrower)

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
               _("Borrower name"),
               borrower)

        for (bar) in barcode:
            recid = db.get_id_bibrec(bar)
            title = ''.join(get_fieldvalues(recid, "245__a"))

            out += """

            <tr>
                 <td class="bibcirctableheader" width="70">%s</td>
                 <td class="bibcirccontent" width="600">%s</td>
            </tr>
            <input type=hidden name=barcode value=%s>

            """ % (_("Item name"),
                   title,
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

        name_link = create_html_link(CFG_SITE_URL +
                                       '/admin/bibcirculation/bibcirculationadmin.py/all_requests',
                                       {'orderby': "name", 'ln': ln},
                                       (_("Name")))

        item_link = create_html_link(CFG_SITE_URL +
                                       '/admin/bibcirculation/bibcirculationadmin.py/all_requests',
                                       {'orderby': "item", 'ln': ln},
                                       (_("Item")))


        status_link = create_html_link(CFG_SITE_URL +
                                       '/admin/bibcirculation/bibcirculationadmin.py/all_requests',
                                       {'orderby': "status", 'ln': ln},
                                       (_("Status")))

        out += """
        <form name="all_requests_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/update_loan_request_status" method="get" >
             <div class="bibcircbottom">
             <br \>
                  <table class="bibcirctable">
                         <tr>
                              <td class="bibcirctableheader" width="70">%s</td>
                              <td class="bibcirctableheader" width="70">%s</td>
                            <td class="bibcirctableheader" width="70">%s</td>
                              <td class="bibcirctableheader" width="70">%s</td>
                              <td class="bibcirctableheader" width="70">%s</td>
                         </tr>

         """% (CFG_SITE_URL,
               name_link,
               item_link,
               status_link,
               _("From"),
               _("To"))

        for (borid, name, recid, status, date_from, date_to) in result:

            borrower_link = create_html_link(CFG_SITE_URL +
                                             '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_details',
                                             {'borrower_id': borid, 'ln': ln},
                                             (name))

            title = ''.join(get_fieldvalues(recid, "245__a"))
            title_link = create_html_link(CFG_SITE_URL +
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_item_details',
                                          {'recid': recid, 'ln': ln},
                                          (title))

            out += """
            <tr>
                 <td class="bibcirccontent" width="70">%s</td>
                <td class="bibcirccontent" width="70">%s</td>
                 <td class="bibcirccontent" width="70">%s</td>
                 <td class="bibcirccontent" width="70">%s</td>
                 <td class="bibcirccontent" width="70">%s</td>
            </tr>
            """ % (borrower_link, title_link, status, date_from, date_to)

        out += """
        </table>
        <br \>
        <table class="bibcirctable">
             <tr>
                  <td><input type=button value="Back" onClick="history.go(-1)" class="formbutton"></td>
             </tr>
        </table>
        <br \> <br \>
        </div>
        </form>
        """
        return out

    def tmpl_all_requests_for_item(self, recid, result, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        out = """
        """
        out += _MENU_

        name_link = create_html_link(CFG_SITE_URL +
                                     '/admin/bibcirculation/bibcirculationadmin.py/all_requests_for_item',
                                     {'orderby': "name",
                                      'recid': recid, 'ln': ln},
                                       (_("Name")))


        status_link = create_html_link(CFG_SITE_URL +
                                       '/admin/bibcirculation/bibcirculationadmin.py/all_requests_for_item',
                                       {'orderby': "status",
                                        'recid': recid,  'ln': ln},
                                       (_("Status")))

        out += """
        <form name="all_loans_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/update_loan_request_status" method="get" >
             <div class="bibcircbottom">
             <br \>
                  <table class="bibcirctable">
                         <tr>
                              <td class="bibcirctableheader">%s</td>
                              <td class="bibcirctableheader">%s</td>
                                                <td class="bibcirctableheader">%s</td>
                              <td class="bibcirctableheader">%s</td>
                              <td class="bibcirctableheader">%s</td>
                         </tr>
         """% (CFG_SITE_URL,
               name_link,
               _("Item"),
               status_link,
               _("From"),
               _("To"))


        for (borid, name, recid, status, date_from, date_to) in result:

            borrower_link = create_html_link(CFG_SITE_URL +
                                             '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_details',
                                             {'borrower_id': borid, 'ln': ln},
                                             (name))

            title = ''.join(get_fieldvalues(recid, "245__a"))
            title_link = create_html_link(CFG_SITE_URL +
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_item_details',
                                          {'recid': recid, 'ln': ln},
                                          (title))

            out += """
            <tr>
                 <td class="bibcirccontent">%s</td>
                 <td class="bibcirccontent">%s</td>
                 <td class="bibcirccontent">%s</td>
                 <td class="bibcirccontent">%s</td>
                 <td class="bibcirccontent">%s</td>
            </tr>
            """ % (borrower_link, title_link, status, date_from, date_to)

        out += """
        </table>
        <br \>
        <table class="bibcirctable">
             <tr>
                  <td><input type=button value="Back" onClick="history.go(-1)" class="formbutton"></td>
             </tr>
        </table>
        <br \> <br \>        <br \>
        </div>
        </form>
        """
        return out

    def tmpl_item_details(self, recid, details, nb_copies, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        out = """
        """
        out += _MENU_

        item_name = ''.join(get_fieldvalues(recid, "245__a"))
        year = ' '.join(get_fieldvalues(recid, "260__c"))
        author = ' '.join(get_fieldvalues(recid, "270__p"))
        isbn = ' '.join(get_fieldvalues(recid, "020__a"))
        editor = ' , '.join(get_fieldvalues(recid, "260__b") + \
                            get_fieldvalues(recid, "260__a"))

        out += """
           <div class="bibcircbottom">
                <form name="borrower_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/all_requests_for_item" method="get" >
                <input type=hidden name=recid value=%s>
                <br \>
                     <table class="bibcirctable">
                          <tr>
                               <td class="bibcirctableheader" width="10">%s</td>
                          </tr>
                </table>

                <table class="bibcirctable">
                     <tr>
                        <td width="100">%s</td> <td class="bibcirccontent">%s</td>
                     </tr>
                     <tr>
                        <td width="100">%s</td> <td class="bibcirccontent">%s</td>
                     </tr>
                     <tr>
                        <td width="100">%s</td> <td class="bibcirccontent">%s</td>
                         </tr>
                     <tr>
                          <td width="100">%s</td> <td class="bibcirccontent">%s</td>
                       </tr>
                       <tr>
                          <td width="100">%s</td> <td class="bibcirccontent">%s</td>
                       </tr>
           </table>
           <br \>
           <table class="bibcirctable">
                <tr>
                     <td class="bibcirctableheader">%s</td>
                </tr>
           </table>
           """  % (CFG_SITE_URL,
                   recid,
                   _("Item details"),
                  _("Name"),
                  item_name,
                  _("Author(s)"),
                  author,
                  _("Year"),
                  year,
                  _("Editor"),
                  editor,
                  _("ISBN"),
                  isbn,
                  _("Additional details"))


        for (loan_period, lib_name, libid) in details:

            library_link = create_html_link(CFG_SITE_URL +
                                            '/admin/bibcirculation/bibcirculationadmin.py/get_library_details',
                                            {'libid': libid, 'ln': ln},
                                            (lib_name))

            out += """
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


            </table>
            <br />
           <table class="bibcirctable">
                  <tr>
                     <td><input type="submit" name="details_button" value="More details about requests" class="formbutton"></td>
                  </tr>
            </table>
            """ % (_("Loan period"),
                   loan_period,
                   _("Location"),
                    library_link,
                   _("Nº of copies"),
                   nb_copies)


        out += """
           <br \>
           <table class="bibcirctable">
                <tr>
                     <td><input type=button value="Back" onClick="history.go(-1)" class="formbutton"></td>
                </tr>
           </table>
           <br \>
           <br \>
           <br \>
           </form>
           </div>
           """

        return out

    def tmpl_library_details(self, details, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        out = """
        """
        out += _MENU_

        out += """
        <div class="bibcircbottom">
        <form>

        <br \>
        """
        #raise repr(details)

        for (name, address, email, phone) in details:
            out += """
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
            </table>
            """ % (
                   _("Name"),
                   name,
                   _("Address"),
                   address,
                   _("Email"),
                    email,
                   _("Phone"),
                   phone)

        out += """
           <br \>
           <table class="bibcirctable">
                <tr>
                     <td><input type=button value="Back" onClick="history.go(-1)" class="formbutton"></td>
                </tr>
           </table>
           <br \>
           <br \>
           <br \>
           </form>
           </div>
           """

        return out


    def tmpl_borrower_details(self, borrower, request, loan, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        out = """
        """
        out += _MENU_

        for (id, name, email, phone, address) in borrower:
            out += """
            <form name="borrower_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/borrower_notification" method="get" >
            <div class="bibcircbottom">
            <input type=hidden name=borrower_id value=%s>
            <br \>
            <table class="bibcirctable">
                 <tr>
                      <td class="bibcirctableheader">%s</td>
                      <td width="740"><input type="submit" name="notify_button" value="Notify this borrower" class="formbutton"></td>
                 </tr>
             </table>
            </form>
            <table class="bibcirctable">
                 <tr>
                      <td class="bibcirctableheader" width="10">%s</td>
                      <td class="bibcirccontent">%s</td>
                 </tr>
                     <tr>
                      <td class="bibcirctableheader" width="10">%s</td>
                      <td class="bibcirccontent">%s</td>
                 </tr>
                 <tr>
                      <td class="bibcirctableheader" width="10">%s</td>
                      <td class="bibcirccontent">%s</td>
                 </tr>
                 <tr>
                      <td class="bibcirctableheader" width="10">%s</td>
                      <td class="bibcirccontent">%s</td>
                 </tr>

            """% (CFG_SITE_URL,
                  id,
                  _("Personal details"),
                  _("Name"),
                  name,
                  _("Email"),
                  email,
                  _("Phone"),
                  phone,
                  _("Address"),
                  address)

        nb_requests = len(request)
        nb_loan = len(loan)

        out += """
        </table>
        <br \>

        <table class="bibcirctable">
             <tr>
                  <td class="bibcirctableheader" width="50">%s</td>
                  <td class="bibcirctableheader" width="50"></td>
             </tr>
             <form name="borrower_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/get_borrower_requests_details" method="get" >
             <tr>
                  <td class="bibcirccontent" width="50">%s loan(s) request(s)</td>
                  <td><input type="submit" name="details_button" value="Request(s) details" class="formbutton"></td>
             </tr>

        <input type=hidden name=borrower_id value=%s>
        </form>


        <form name="borrower_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/get_borrower_loans_details" method="get" >
             <tr>
                  <td class="bibcirccontent" width="50">%s item(s) on loan</td>
                  <td><input type="submit" name="details_button" value="Loan(s) details" class="formbutton"></td>
             </tr>

        </table>
        <br \>

        <table class="bibcirctable">
             <tr>
                 <td><input type=button value="Back" onClick="history.go(-1)" class="formbutton"></td>
             </tr>
        </table>
        <br \>
        </div>
        <input type=hidden name=borrower_id value=%s>
        </form>
        """ % (_("Loan overview"),
               CFG_SITE_URL,
               nb_requests,
               id,
               CFG_SITE_URL,
               nb_loan,
               id)

        return out

    def tmpl_borrower_request_details(self, result,
                                      borrower_id, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        #raise repr(result)

        out = """
        """
        out += _MENU_
        item_link = create_html_link(CFG_SITE_URL +
                                       '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_requests_details',
                                       {'borrower_id': borrower_id,'orderby': "item", 'ln': ln},
                                       (_("Item")))

        status_link = create_html_link(CFG_SITE_URL +
                                       '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_requests_details',
                                       {'borrower_id': borrower_id,'orderby': "status", 'ln': ln},
                                       (_("Status")))

        from_link = create_html_link(CFG_SITE_URL +
                                       '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_requests_details',
                                       {'borrower_id': borrower_id,'orderby': "from", 'ln': ln},
                                       (_("From")))


        to_link = create_html_link(CFG_SITE_URL +
                                       '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_requests_details',
                                       {'borrower_id': borrower_id,'orderby': "to", 'ln': ln},
                                       (_("To")))
        out += """
        <form name="borrower_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/get_borrower_requests_details" method="get" >
        <div class="bibcircbottom">
        <br \>
             <table class="bibcirctable">
                    <tr>
                       <td class="bibcirctableheader">%s</td>
                                <td class="bibcirctableheader">%s</td>
                                <td class="bibcirctableheader">%s</td>
                       <td class="bibcirctableheader">%s</td>

               </tr>
        </form>
         """% (CFG_SITE_URL,
               item_link,
               status_link,
               from_link,
               to_link)

        for (borid, recid, status, date_from, date_to) in result:

            title = ''.join(get_fieldvalues(recid, "245__a"))
            title_link = create_html_link(CFG_SITE_URL +
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_item_details',
                                          {'recid': recid, 'ln': ln},
                                          (title))

            out += """
            <tr>
                 <td class="bibcirccontent">%s</td>
                 <td class="bibcirccontent">%s</td>
                 <td class="bibcirccontent">%s</td>
                 <td class="bibcirccontent">%s</td>
            </tr>

            """ % (title_link, status, date_from, date_to)


        out += """
        </table>
        <br \>
        <table class="bibcirctable">
             <tr>
                  <td><input type=button value="Back" onClick="history.go(-1)" class="formbutton"></td>
             </tr>
        </table>
        <br \>
        </div>

        """
        return out

    def tmpl_borrower_loans_details(self, result,
                                    borrower_id, infos, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        out = self.tmpl_infobox(infos, ln)

        out += _MENU_

        out += """
        <form name="borrower_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/get_borrower_loans_details" method="get" >
        <div class="bibcircbottom">
        <br \>
             <table class="bibcirctable">
                    <tr>
                       <td class="bibcirctableheader">%s</td>
                                <td class="bibcirctableheader">%s</td>
                                <td class="bibcirctableheader">%s</td>
                       <td class="bibcirctableheader">%s</td>
                       <td class="bibcirctableheader">%s</td>
                       <td class="bibcirctableheader">%s</td>
                       <td class="bibcirctableheader">%s</td>
                       <td class="bibcirctableheader">%s</td>
                       <td class="bibcirctableheader">%s</td>
                       <td class="bibcirctableheader">%s</td>
               </tr>
        </form>
         """% (CFG_SITE_URL,
               _("Item"),
               _("Barcode"),
               _("Loaned on"),
               _("Returned on"),
               _("Due date"),
               _("Nº of renewalls"),
               _("Nº of Overdue letters"),
               _("Date of overdue letter"),
               _("Type"),
               _("Status"))


        for (recid, barcode, loaned_on, returned_on, due_date, nb_renewall, nb_overdue, date_overdue, status, type) in result:

            title = ''.join(get_fieldvalues(recid, "245__a"))
            title_link = create_html_link(CFG_SITE_URL +
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_item_details',
                                          {'recid': recid, 'ln': ln},
                                          (title))

            prolongate_link = create_html_link(CFG_SITE_URL +
                        '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_loans_details',
                        {'borrower_id': borrower_id, 'barcode': barcode},
                        (_("Prolongate")))

            returned_link = create_html_link(CFG_SITE_URL +
                        '/admin/bibcirculation/bibcirculationadmin.py/loan_return_confirm',
                        {'barcode': barcode},
                        (_("Returned")))

            out += """
            <tr>
                 <td class="bibcirccontent">%s</td>
                 <td class="bibcirccontent">%s</td>
                 <td class="bibcirccontent">%s</td>
                 <td class="bibcirccontent">%s</td>
                 <td class="bibcirccontent">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent" align="center">%s</td>
                 <td class="bibcirccontent">%s</td>
                 <td class="bibcirccontent">%s</td>
                <td class="bibcirccontent">%s</td>
                <td class="bibcirccontent">%s</td>
            </tr>

            """ % (title_link, barcode, loaned_on,
                   returned_on, due_date, nb_renewall,
                   nb_overdue, date_overdue, status,
                   type, prolongate_link, returned_link)


        out += """
        </table>
        <br \>
        <table class="bibcirctable">
             <tr>
                  <td><input type=button value="Back" onClick="history.go(-1)" class="formbutton"></td>
             </tr>
        </table>
        <br \>
        </div>

        """
        return out

    def tmpl_all_loans(self, result, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """
        _ = gettext_set_language(ln)

        out = """
        """
        out += _MENU_

        out += """
            <form name="list_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/all_loans" method="get" >
            <div class="bibcircbottom">
            <br />
            <table class="bibcirctable">
            <tr>
            <td class="bibcirctableheader" width="90">
            Show list of
            </td>
            <td width="200">
                       <select name="show"  style="border: 1px solid #cfcfcf">
                          <option value ="all">all loans</option>
                          <option value ="expired">expired loans</option>
                          <option value ="on_loan">loans 'ON LOAN?!?!'</option>
                    </select>
            </td>
            <td>
            <input type="submit" name="ok_button" value="OK" class="formbutton">
            </td>
            </tr>
            </table>
            <br />
            <hr>
            <br />
            </form>
        """ % (CFG_SITE_URL)

        out += """
        <form name="borrower_form" action="%s/admin/bibcirculation/bibcirculationadmin.py/all_loans" method="get" >

        <br \>
             <table class="bibcirctable">
                    <tr>
                       <td class="bibcirctableheader">%s</td>
                       <td class="bibcirctableheader">%s</td>
                                <td class="bibcirctableheader">%s</td>
                                <td class="bibcirctableheader">%s</td>
                       <td class="bibcirctableheader">%s</td>
                       <td class="bibcirctableheader">%s</td>
                       <td class="bibcirctableheader">%s</td>
                       <td class="bibcirctableheader">%s</td>
                       <td class="bibcirctableheader">%s</td>
                       <td class="bibcirctableheader">%s</td>

                                </tr>

         """% (CFG_SITE_URL,
               _("Borrower"),
               _("Item"),
               _("Barcode"),
               _("Loaned on"),
               _("Returned on"),
               _("Due date"),
               _("Nº of renewalls"),
               _("Nº of Overdue letters"),
               _("Date of overdue letter"),
               _("Status"))


        for (borid, borname, recid, barcode, loaned_on, returned_on, due_date, nb_renewall, nb_overdue, date_overdue, status) in result:

            borrower_link = create_html_link(CFG_SITE_URL +
                                             '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_details',
                                             {'borrower_id': borid, 'ln': ln},
                                             (borname))

            title = ''.join(get_fieldvalues(recid, "245__a"))
            title_link = create_html_link(CFG_SITE_URL +
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_item_details',
                                          {'recid': recid, 'ln': ln},
                                          (title))

            out += """
            <tr>
                 <td class="bibcirccontent">%s</td>
                 <td class="bibcirccontent">%s</td>
                 <td class="bibcirccontent">%s</td>
                 <td class="bibcirccontent">%s</td>
                 <td class="bibcirccontent">%s</td>
                 <td class="bibcirccontent">%s</td>
                <td class="bibcirccontent" align="center">%s</td>
                <td class="bibcirccontent" align="center">%s</td>
                <td class="bibcirccontent" align="center">%s</td>
                <td class="bibcirccontent">%s</td>

             </tr>

            """ % (borrower_link, title_link, barcode,
                   loaned_on, returned_on, due_date,
                   nb_renewall, nb_overdue, date_overdue, status)

        out += """
        </table>
        <br \>
        <table class="bibcirctable">
             <tr>
                  <td><input type=button value="Back" onClick="history.go(-1)" class="formbutton"></td>
             </tr>
        </table>
        <br \>
        <br \>
        <br \>
        </div>
        </form>
        """
        return out

    def tmpl_messages_compose(self, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        out = """
        """
        out += _MENU_

        out += """

        <div class=bibcircbottom>
        <br \>
        <form>
           <table class="bibcirctable">
                    <tr>
                      <td class="bibcirctableheader" width="50">From</td>
                        <td>CERN Library</td>
             </tr>

           </table>

           <table class="bibcirctable">
                  <tr>
                       <td class="bibcirctableheader" width="50">To</td>
                       <td>
                            <input type="text" size="60" name="user">
                       </td>
                         </tr>
                </table>

            <table class="bibcirctable">
                 <tr>
                  <td class="bibcirctableheader" width="50">Subject</td>
                  <td><input type="text" size="60" name="user"></td>
               </tr>
            </table>
            <table class="bibcirctable">
             <tr>
                  <td class="bibcirctableheader" width="40">Message</td>
             </tr>
                <tr>
                  <td><textarea rows="10" cols="60" style="border: 3"></textarea></td>
             </tr>
        </table>

        <table class="bibcirctable">
             <tr>
                    <td>
                    <input type="submit" value="Cancel" class="formbutton">
                    <input type="submit" value="Send" class="formbutton">
                    </td>
                </tr>
         </table>
        <br \> <br \>
        <form>
        </div>

        """

        return out


    def tmpl_messages_inbox(self, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        out = """
        """

        out += _MENU_

        out += """

        <div class=bibcircbottom>

        </div>

        """

        return out


    def tmpl_help_contactsupport(self, ln=CFG_SITE_LANG):
        """
        """

        out = """
        """

        out += _MENU_

        out += """

        <div class=bibcircbottom>
        <br \>
          <form>
             <table class="bibcirctable">
               <tr>
                       <td class="bibcirctableheader" width="50">From</td>
                         <td>CERN Library</td>
                    </tr>
             </table>

        <table class="bibcirctable">
               <tr>
                    <td class="bibcirctableheader" width="50">To</td>
                    <td> CDS.Support</td>
               </tr>
        </table>
        <table class="bibcirctable">
             <tr>
                  <td class="bibcirctableheader" width="50">Subject</td>
                  <td><input type="text" size="60" name="user" style="border: 1px solid #cfcfcf"></td>
         </tr>
       </table>

       <table class="bibcirctable">
            <tr>
                 <td class="bibcirctableheader" width="40">Message</td>
            </tr>
            <tr>
                 <td><textarea rows="10" cols="96" style="border: 1px solid #cfcfcf"></textarea></td>
            </tr>
       </table>
       <table class="bibcirctable">
            <tr>
                    <td>
                    <input type="submit" value="Cancel" class="formbutton">
                    <input type="submit" value="Send" class="formbutton">
               </td>
               </tr>
      </table>
      <br \> <br \>
      <form>

        """

        return out

    def tmpl_borrower_search_test(self, result, send_to, ln=CFG_SITE_LANG):
        """
        @param ln: language of the page
        """

        send_to = " , ".join(send_to)

        _ = gettext_set_language(ln)

        out = """
        """

        out += _MENU_

        out += """
        <div class=bibcircbottom>
        <br \><br \>
        <form name="borrower_search" action="%s/admin/bibcirculation/bibcirculationadmin.py/borrower_search_test" method="get" >
             <table class="bibcirctable">
                  <tr>
                        <td class="bibcirctableheader">%s</td>
                  <td>
                    <select name="column">
                          <option value ="name">%s</option>
                          <option value ="email">%s</option>
                          <option value ="phone">%s</option>
                          <option value ="id">%s</option>
                    </select>
                  </td>
                  <td width="850"><input type="text" size="30" name="string"></td>
                  </tr>
             </table>
        <br \>
        <table class="bibcirctable">
             <tr>
                  <td>
                  <input type="submit" value="Search" class="formbutton">
                  </td>
             </tr>
        </table>
        <br \>
        """% (CFG_SITE_URL,
              _("Search borrower by"),
              _("name"),
              _("email"),
              _("phone"),
              _("id"))

        out += """  <table class="bibcirctable">
                    <tr>
                    <td class="bibcirctableheader">
                    To
                    </td>
                    <td width="960">
                    <input type="text" size="30" name="to_user" value="%s">
                    </td>
                    </tr>
                    </table>
                    <br \>
        """ % (send_to)

        if result:

            out += """
            <table class="bibcirctable">
            <tr>
            <td>
            <select name="user" multiple size=5"> """

            for (uid, borrower) in result:

                out += """
                      <option value ="%s">%s
                    """ % (uid, borrower)

            out += """
                    </select>
                    </td>
                    </tr>
                    </table>
                    <table class="bibcirctable">
                    <tr>
                  <td>
                        <input type="submit" value="Add user" class="formbutton">
                        </td>
                    </tr>
                    </table>
                    """


        out += """
        <form>
        <br \><br \>
        </div>

        """

        return out

    def tmpl_borrower_notification(self, email, mails, subject,
                                    result, ln=CFG_SITE_LANG):
        """
        @param result: template used for the notification
        @param ln: language of the page
        """

        if subject == None:
            subject = ""


        if type(email) is list:
            user_email = " , ".join(email)
        else:
            user_email = email

        _ = gettext_set_language(ln)

        out  = """ """

        out += _MENU_

        out += """

        <form name="borrower_notification" action="%s/admin/bibcirculation/bibcirculationadmin.py/borrower_notification" method="post" >

             <div class=bibcircbottom>
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

              _("From"),
              _("CERN Library"),
              _("To"))


        out += """

        <td>
        <input type="text" name="to_borrower" size="60" style="border: 1px solid #cfcfcf" value="%s">
       </td>


                        <td class="bibcirctableheader">Search borrower by</td>
                  <td>
                    <select name="column" style="border: 1px solid #cfcfcf">
                          <option value ="name">name</option>
                          <option value ="email">e-mail</option>
                          <option value ="phone">phone</option>
                          <option value ="id">id</option>
                    </select>
                  </td>
                  <td><input type="text" size="50" name="string" style="border: 1px solid #cfcfcf"></td>
                        <td>
                  <input type="submit" value="Search" class="formbutton">
                  </td>
             </tr>


        </tr>
        </table>
        """ % (user_email)


        if mails:

            out += """

            <br \>

            <table class="bibcirctable">
            <tr>
            <td ALIGN="right">
            <select name="borrower_id" multiple size="5" style="border: 1px solid #cfcfcf; width:50%">
            """

            for (uid, borrower) in mails:

                out += """
                      <option value ="%s">%s
                    """ % (uid, borrower)

            out += """
                    </select>
                    </td>
                    </tr>
                    </table>
                    <table class="bibcirctable">
                    <tr>
                  <td ALIGN="right">
                        <input type="submit" value="Add user" class="formbutton">
                        </td>
                    </tr>
                    </table>

                    <br \>

                    """




        out += """
        <table class="bibcirctable">
             <tr>
                  <td class="bibcirctableheader" width="50">%s</td>
                  <td><input type="text" name="subject" size="60" value="%s" style="border: 1px solid #cfcfcf"></td>
             </tr>
        </table>

        <br \>  <br \>

        <table class="bibcirctable">
             <tr>
                  <td class="bibcirctableheader" width="40">%s</td>
             </tr>
            <tr>
                  <td><textarea rows="10" cols="100" name="message" style="border: 1px solid #cfcfcf">%s</textarea></td>
                  <td></td>
        """ % (_("Subject"),
               subject,
               _("Message"),
               result)

        out += """
               <td class="bibcirctableheader" valign="top">%s<br \>
                    <select name="template" style="border: 1px solid #cfcfcf">
                         <option value ="">%s</option>
                          <option value ="overdue_letter">%s</option>
                          <option value ="reminder">%s</option>
                          <option value ="notification">%s</option>
                    </select>
                    <br \><br \>
                    <input type="submit" name="load_button" value=%s class="formbutton">
              </td>
               </tr>
        </table>
        """ % (_("Choose a letter template"),
               _("Templates"),
               _("Overdue letter"),
               _("Reminder"),
               _("Notification"),
               _("Load"))


        out += """

        <br \> <br \>
        <table class="bibcirctable">
               <tr>
                    <td>
                       <input type=button value=%s onClick="history.go(-1)" class="formbutton">
                       <input type="reset" name="reset_button" value=%s class="formbutton">
                         <input type="submit" name="send_button" value=%s class="formbutton">
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

