## Administrator interface for Bibcirculation
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

"""CDS Invenio Bibcirculation Administrator Interface."""

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

import datetime, time

# Others Invenio imports
from invenio.config import \
    CFG_SITE_LANG, \
    CFG_SITE_URL
import invenio.access_control_engine as acce
from invenio.webpage import page
from invenio.webuser import getUid, page_not_authorized
from invenio.dateutils import get_datetext
from invenio.mailutils import send_email
from invenio.search_engine import perform_request_search


# Bibcirculation imports
from invenio.bibcirculation_config import CFG_BIBCIRCULATION_TEMPLATES
import invenio.bibcirculation_dblayer as db
import invenio.template
bibcirculation_templates = invenio.template.load('bibcirculation')

def is_adminuser(req):
    """check if user is a registered administrator. """

    return acce.acc_authorize_action(req, "cfgbibformat")

def mustloginpage(req, message):
    """show a page asking the user to login."""

    navtrail_previous_links = '<a class="navtrail" href="%s/admin/">' \
        'Admin Area</a> &gt; ' \
        '<a class="navtrail" href="%s/admin/bibcirculation/">' \
        'BibCirculation Admin</a> ' % (CFG_SITE_URL, CFG_SITE_URL)

    return page_not_authorized(req=req, text=message,
        navtrail=navtrail_previous_links)

def index(req, ln=CFG_SITE_LANG):
    """main function to show pages for bibcirculationadmin
    """
    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_index(ln=ln)

    return page(title="BibCirculation Admin",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)




def manage_holdings(req, ln=CFG_SITE_LANG):
    """
    Main admin page of Bibcirculation.
    Display the number of pending loans requests.
    """

    result = db.get_pending_loan_request("pending")
    result = len(result)

    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_manage_holdings(pending_request=result,
                                                         ln=ln)

    return page(title="Manage Holdings",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def borrower_search(req, ln=CFG_SITE_LANG):
    """
    Page where we can search a borrower using a name.
    """
    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_borrower_search(ln=ln)

    return page(title="Borrower Search",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def item_search_result(req, p, f, start, end, ln=CFG_SITE_LANG):
    """
    """

    result = perform_request_search(cc="Books", sc="1", p=p, f=f)
    #raise repr(start)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)


    body = bibcirculation_templates.tmpl_item_search_result(result=result,
                                                            start=start,
                                                            end=end,
                                                            ln=ln)

    return page(title="Search result",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)




def borrower_search_test(req, column, string, user, ln=CFG_SITE_LANG):
    """
    Page where we can search a borrower using a name.
    """



    if string:
        if column == 'name':
            result = db.search_borrower_by_name(string)
        elif column == 'phone':
            result = db.search_borrower_by_phone(string)
        elif column == 'email':
            result = db.search_borrower_by_email(string)
        else:
            result = db.search_borrower_by_id(string)
    else:
        result = ""


    if user:

        send_to = []

        for (uid) in user:
            user_mail = db.get_borrower_email(uid)
            send_to.append(user_mail)
    else:
        send_to = ""


#    raise repr(result)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_borrower_search_test(result=result, send_to=send_to, ln=ln)

    return page(title="Borrower Search",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def search_result(req, column, str, ln=CFG_SITE_LANG):
    """
    Display the result when we use a search method (e.g. borrower_search)
    @param str: string used on the search query
    """

    if column == 'name':
        result = db.search_borrower_by_name(str)
    elif column == 'phone':
        result = db.search_borrower_by_phone(str)
    elif column == 'email':
        result = db.search_borrower_by_email(str)
    else:
        result = db.search_borrower_by_id(str)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_search_result(result=result, ln=ln)

    return page(title="Search result",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)



def holdings_search(req, ln=CFG_SITE_LANG):
    """
    """
    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_holdings_search(ln=ln)

    return page(title="Items Search",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def load_template(template):
    """
    Load a letter/notification template from
    bibcirculation_config.py.
    @param template: template who will be used in the notification.
    """
    if template == "overdue_letter":
        output = CFG_BIBCIRCULATION_TEMPLATES['OVERDUE']

    elif template == "reminder":
        output = CFG_BIBCIRCULATION_TEMPLATES['REMINDER']

    elif template == "notification":
        output = CFG_BIBCIRCULATION_TEMPLATES['NOTIFICATION']

    else:
        output = CFG_BIBCIRCULATION_TEMPLATES['EMPTY']

    return output



def borrower_notification(req, borrower_id=None, template=None,
                          to_borrower=None, message=None,
                          search_button=None, load_button=None, string=None,
                          column=None, subject=None, send_button=None, ln=CFG_SITE_LANG):
    """
    Send a message/email to a borrower
    """

    if string:
        if column == 'name':
            mails = db.search_borrower_by_name(string)
        elif column == 'phone':
            mails = db.search_borrower_by_phone(string)
        elif column == 'email':
            mails = db.search_borrower_by_email(string)
        else:
            mails = db.search_borrower_by_id(string)
    else:
        mails = ""


    if borrower_id:
        email = []

        for (uid) in borrower_id:
            user_mail = db.get_borrower_email(uid)
            email.append(user_mail)
    else:
        email = ""


    if to_borrower:
        email = to_borrower


    if load_button == "Load" and template != None:
        result = load_template(template)
        body = bibcirculation_templates.tmpl_borrower_notification(email=email,
                                                                   mails=mails,
                                                                   subject=subject,
                                                                   result=result,
                                                                   ln=ln)


    elif send_button == "Send":
        send_email(fromaddr="library.desk@cern.ch",
                   toaddr=to_borrower,
                   subject=subject,
                   content=message,
                   header='',
                   footer='',
                   attempt_times=1,
                   attempt_sleeptime=10
                   )

      #  raise repr(send_email)
        body = bibcirculation_templates.tmpl_send_notification(ln=ln)




    else:
        result = load_template(template)
        body = bibcirculation_templates.tmpl_borrower_notification(email=email,
                                                                   mails=mails,
                                                                   subject=subject,
                                                                   result=result,
                                                                   ln=ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                              '  href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    return page(title="Borrower Notification",
                 uid=id_user,
                 req=req,
                 body=body,
                 navtrail=navtrail_previous_links,
                 lastupdated=__lastupdated__)



def get_next_waiting_loan_request(req, recID=None, barcode=None,
                                  submit_button=None, ln=CFG_SITE_LANG):
    """
    Display the next loan request who is waiting.
    """



    returned_on = datetime.date.today()
    db.update_item_status('available', barcode)
    db.update_loan_info(returned_on, 'returned', barcode)
    result = db.get_next_waiting_loan_request("waiting", recID)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_get_next_waiting_loan_request(status=result,
                                                                       barcode=barcode,
                                                                       ln=ln)

    return page(title="Waiting loans requests",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def update_next_loan_request_status(req, check_id=None,
                                    approve_button=None, cancel_button=None,
                                    barcode=None, ln=CFG_SITE_LANG):
    """
    Update the status of a loan request who is defined as 'waiting'.
    The new status can be 'done' or 'cancelled'.
    """

    recid = db.get_recid_from_crcLOANREQUEST(check_id)
    borrower_id = db.get_borrower_id_from_crcLOANREQUEST(check_id)
    loaned_on = datetime.date.today()
    due_date = get_datetext(loaned_on.year, loaned_on.month + 1, loaned_on.day)

    if check_id != None and approve_button == "Approve":
        db.update_loan_request_status(check_id,'done')
        db.update_barcode_on_crcloanrequest(barcode, check_id)
        db.new_loan(borrower_id, recid, barcode, loaned_on, due_date, 'on loan', 'normal','')
        db.update_item_status('on loan', barcode)

    elif check_id != None and cancel_button == "Cancel":
        for(id) in check_id:
            db.update_loan_request_status(check_id,'cancelled')

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_next_loan_request_done(ln=ln)

    return page(title="Title",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def loan_return(req, ln=CFG_SITE_LANG):
    """
    Page where is possible to register the return of an item.
    """

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_loan_return(ln=ln)

    return page(title="Loan return",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def loan_on_desk(req, column, string, borrower, confirm_button, barcode, borrower_name, ln=CFG_SITE_LANG):
    """
    @param ln: language of the page
    """
    if confirm_button == "Confirm":
        title="Loan on desk confirm"
        barcode = barcode.split()
        body = bibcirculation_templates.tmpl_loan_on_desk_confirm(barcode=barcode,
                                                                  borrower=borrower_name,
                                                                  ln=ln)

    elif string:
        title="Loan on desk"
        if column == 'name':
            result = db.search_borrower_by_name(string)
        elif column == 'phone':
            result = db.search_borrower_by_phone(string)
        elif column == 'email':
            result = db.search_borrower_by_email(string)
        else:
            result = db.search_borrower_by_id(string)

        body = bibcirculation_templates.tmpl_loan_on_desk(result=result,
                                                          borrower=borrower,
                                                          barcode=barcode,
                                                          ln=ln)
    else:
        title="Loan on desk"
        result = ""
        body = bibcirculation_templates.tmpl_loan_on_desk(result=result,
                                                          borrower=borrower,
                                                          barcode=barcode,
                                                          ln=ln)


    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)



    return page(title=title,
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def loan_on_desk_confirm(req, barcode=None, borrower_id=None, ln=CFG_SITE_LANG):
    """

    """

    result = db.loan_on_desk_confirm(barcode, borrower_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_loan_on_desk_confirm(result=result, barcode=barcode, borrower_id=borrower_id, ln=ln)

    return page(title="Loan on desk confirm",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def register_new_loan(req, barcode, borrower_id, ln=CFG_SITE_LANG):
    """
    @param ln: language of the page
    """

    loaned_on = datetime.date.today()

    for(bar) in barcode:
        id_bibrec = db.get_id_bibrec(bar)
        due_date = get_datetext(loaned_on.year, loaned_on.month + 1, loaned_on.day)

        db.new_loan(borrower_id, id_bibrec, bar, loaned_on, due_date, 'on loan', 'normal','')
        db.update_item_status('on loan', bar)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_register_new_loan_done(ln=ln)

    return page(title="Loan on desk",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def loan_return_confirm(req, barcode, ln=CFG_SITE_LANG):
    """

    """
    result = []

    id_bibrec = db.get_id_bibrec(barcode)
    borrower_id = db.get_borrower_id(barcode)
    borrower_name = db.get_borrower_name(borrower_id)

    result.append(borrower_id)
    result.append(id_bibrec)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_loan_return_confirm(borrower_name=borrower_name,
                                                             id_bibrec=id_bibrec,
                                                             barcode=barcode,
                                                             ln=ln)

    return page(title="Loan return confirm",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)




def get_borrower_details(req, ln=CFG_SITE_LANG, borrower_id=None):
    """
    Display the details of a borrower.
    @param borrower_id: ID of a borrower who will used to get is details.
    """
    borrower = db.get_borrower_details(borrower_id)
    request = db.get_borrower_request_details(borrower_id)
    loan = db.get_borrower_loan_details(borrower_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_borrower_details(borrower=borrower,
                                                          request=request,
                                                          loan=loan,
                                                          ln=ln)

    return page(title="Borrower details",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def get_borrower_loans_details(req, orderby=None, ln=CFG_SITE_LANG, notify_button=None, barcode=None, borrower_id=None):
    """

    """

    infos = []

    now = datetime.date.today()
    year = now.year
    month = now.month + 1
    day = now.day
    new_due_date = get_datetext(year, month, day)

    if barcode:
        recid = db.get_id_bibrec(barcode)
        queue = db.get_queue_request(recid)

        if len(queue) != 0:
            infos.append("Sorry! It is not possible to prolongate this loan. Another user is waiting for this book.")
        else:
            db.update_due_date(barcode, new_due_date)
            infos.append("Done!!!")



    result = db.get_borrower_loan_details(borrower_id)


    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_borrower_loans_details(result=result,
                                                                borrower_id=borrower_id,
                                                                infos=infos,
                                                                ln=ln)
    name = db.get_borrower_name(borrower_id)
    title = "Loans details for %s" % (name)

    return page(title=title,
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def all_loans_for_item(req, recid, ln=CFG_SITE_LANG):
    """
    """
    #raise repr(recid)

    result = db.get_all_loans_for_item(recid)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_all_loans_for_item(result=result,
                                                            ln=ln)

    return page(title="All loans",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def get_item_details(req, ln=CFG_SITE_LANG, recid=None):
    """
    Display the details of an item.
    @param recid: CDS Invenio record identifier
    """
    result = db.get_item_addicional_details(recid)
    nb_copies = db.get_number_copies(recid)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_item_details(recid=recid,
                                                      details=result,
                                                      nb_copies=nb_copies,
                                                      ln=ln)

    return page(title="Item details",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def get_library_details(req, ln=CFG_SITE_LANG, libid=None):
    """
    Display the details of a library.
    @param libid: Library identifier
    """
    result = db.get_library_details(libid)

    navtrail_previous_links = '<a class="navtrail" ' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_library_details(details=result,
                                                         ln=ln)

    return page(title="Library details",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def get_borrower_requests_details(req, orderby=None, ln=CFG_SITE_LANG,
                              notify_button=None, borrower_id=None):
    """
    Display loans details of a borrower.
    @param borrower_id: borrower identifier.
    @param orderby: define the order who will displayed all details.
    """

    if orderby == "status":
        result = db.get_borrower_request_details_order_by_status(borrower_id)
    elif orderby == "from":
        result = db.get_borrower_request_details_order_by_from(borrower_id)
    elif orderby == "item":
        result = db.get_borrower_request_details_order_by_item(borrower_id)
    elif orderby == "to":
        result = db.get_borrower_request_details_order_by_to(borrower_id)
    else:
        result = db.get_borrower_request_details(borrower_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    name = db.get_borrower_name(borrower_id)

    title = "Requests details for %s" % (name)
    body = bibcirculation_templates.tmpl_borrower_request_details(result=result,
                                                               borrower_id=borrower_id,
                                                               ln=ln)

    return page(title=title,
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def get_pending_loan_request(req, show, ln=CFG_SITE_LANG):
    """
    Get all loans requests who are pending.
    """

    if show =='on_loan':
        status = db.get_pending_loan_request_on_loan('pending')
        title = "List of pending requests for holdings 'ON LOAN'"
    elif show =='available':
        status = db.get_pending_loan_request_available('pending')
        title = "List of pending requests for holdings 'AVAILABLE'"
    else:
        status = db.get_pending_loan_request("pending")
        title = "List of all pending requests"

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_get_pending_loan_request(status=status,
                                                                   ln=ln)

    return page(title=title,
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def update_loan_request_status(req, check_id_list=None, approve_button=None,
                               cancel_button=None, ln=CFG_SITE_LANG):
    """
    Update the loan request status from 'pending' to 'waiting' or
    'done' or 'cancelled'.
    """

    if check_id_list != None and approve_button == "Approve":

        for (check_id) in check_id_list:
            recid = db.get_recid_from_crcLOANREQUEST(check_id)
            borrower_id = db.get_borrower_id_from_crcLOANREQUEST(check_id)
            barcode = db.get_barcode_from_crcLOANREQUEST(check_id)

            if barcode =="":
                db.update_loan_request_status(check_id,'waiting')

            else:
                loaned_on = datetime.date.today()
                due_date = get_datetext(loaned_on.year, loaned_on.month + 1, loaned_on.day)
                nb_request = db.get_number_requests2(barcode, check_id)

                if len(nb_request) != 0:
                    db.update_loan_request_status(check_id,'waiting')

                else:
                    db.update_loan_request_status(check_id,'done')
                    db.update_item_status('on loan', barcode)
                    db.new_loan(borrower_id, recid, barcode, loaned_on, due_date, 'on loan', 'normal','')


    elif check_id_list != None and cancel_button == "Cancel":

        for(check_id) in check_id_list:
            db.update_loan_request_status(check,'cancelled')

    status = db.get_pending_loan_request("pending")
    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_get_pending_loan_request(status=status,
                                                                  ln=ln)

    return page(title="Pending Loans Requests",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def all_requests(req, orderby=None, ln=CFG_SITE_LANG):
    """
    Display all loans.
    """

    if orderby == "status":
        result = db.get_all_requests_order_by_status()
    elif orderby == "name":
        result = db.get_all_requests_order_by_name()
    elif orderby == "item":
        result = db.get_all_requests_order_by_item()
    else:
        result = db.get_all_requests()

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_all_requests(result=result, ln=ln)

    return page(title="List of all requests",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def all_loans(req, show, ln=CFG_SITE_LANG):
    """
    """

    if show == 'expired':
        result = db.get_all_expired_loans()
        title="List of all expired loans"
    elif show == 'on_loan':
        result = db.get_all_loans_onloan()
        title="List of all loans ON LOAN?!?!"
    else:
        result = db.get_all_loans()
        title="List of all loans"

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_all_loans(result=result, ln=ln)

    return page(title=title,
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)



def get_all_requests_for_item(req, recid=None, orderby=None, ln=CFG_SITE_LANG):
    """
    Display all requests for a specific item.
    """

    if orderby == "status":
        result = db.get_all_requests_for_item_order_by_status(recid)
    elif orderby == "name":
        result = db.get_all_requests_for_item_order_by_name(recid)
    else:
        result = db.get_all_requests_for_item(recid)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_all_requests_for_item(recid=recid,
                                                            result=result,
                                                            ln=ln)

    return page(title="All requests",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def messages_compose(req, ln=CFG_SITE_LANG):
    """
    """
    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_messages_compose(ln=ln)

    return page(title="Messages Compose",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def messages_inbox(req, ln=CFG_SITE_LANG):
    """
    """
    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_messages_inbox(ln=ln)

    return page(title="Messages Inbox",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def help_contactsupport(req, ln=CFG_SITE_LANG):
    """
    """
    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_help_contactsupport(ln=ln)

    return page(title="Contact Support",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


