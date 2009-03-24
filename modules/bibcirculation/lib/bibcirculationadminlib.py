# Administrator interface for Bibcirculation
##
## $Id: bibcirculationadminlib.py,v 1.4 2008/08/20 16:25:41 joaquim Exp $
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

__revision__ = "$Id: bibcirculationadminlib.py,v 1.4 2008/08/20 16:25:41 joaquim Exp $"

__lastupdated__ = """$Date: 2008/08/20 16:25:41 $"""

import datetime, time

# Others Invenio imports
from invenio.config import \
    CFG_SITE_LANG, \
    CFG_SITE_URL
import invenio.access_control_engine as acce
from invenio.webpage import page
from invenio.webuser import getUid, page_not_authorized
from invenio.mailutils import send_email
from invenio.search_engine import perform_request_search
from invenio.search_engine import get_fieldvalues
from invenio.urlutils import create_html_link
from invenio.messages import gettext_set_language
from invenio.bibcirculation_utils import book_information_from_MARC, \
      book_title_from_MARC, \
      update_status_if_expired, \
      renew_loan_for_X_days, \
      print_pending_hold_requests_information, \
      print_new_loan_information

# Bibcirculation imports
from invenio.bibcirculation_config import \
     CFG_BIBCIRCULATION_TEMPLATES, ACCESS_KEY, \
     USER_ON_CERN_LDAP
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
    Main page of Bibcirculation (for administrator).
    It is possible to see in this page the number of pending requests
    and other relevant informations.
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
    Page (for administrator) where is it possible to search
    for a borrower (who is on crcBORROWER table) using is name,
    email, phone or id.
    """

    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
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


def item_search_result(req, p, f, ln=CFG_SITE_LANG):
    """
    Search an item and return a list with all the possible results. To retrieve
    the information desired, we use the method 'perform_request_search' (from
    search_engine.py). In the case of BibCirculation, we are just looking for
    books (items) inside the collection 'Books'.
    """

    result = perform_request_search(cc="Books", sc="1", p=p, f=f)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_item_search_result(result=result,
                                                            ln=ln)

    return page(title="Item search result",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def borrower_search_result(req, column, string, ln=CFG_SITE_LANG):
    """
    Search a borrower and return a list with all the possible results.

    column - identify the column, of the table crcBORROWER, who will be
             considered during the search. Can be 'name', 'email' or 'id'.

    string - string used for the search process.

    @param str: string used on the search query
    """

    if column == 'name':
        result = db.search_borrower_by_name(string)
    elif column == 'email':
        result = db.search_borrower_by_email(string)
    else:
        result = db.search_borrower_by_id(string)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_borrower_search_result(result=result, ln=ln)

    return page(title="Borrower search result",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def item_search(req, ln=CFG_SITE_LANG):
    """
    Display a form where is possible to searh for an item.
    """
    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_item_search(ln=ln)

    return page(title="Item search",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def load_template(template):
    """
    Load a letter/notification template from
    bibcirculation_config.py.
    template - template who will be used in the notification.
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



def borrower_notification(req, borrower_id, template, message,
                          load_msg_template, subject, send_message,
                          ln=CFG_SITE_LANG):
    """
    Send a message/email to a borrower.

    borrower_id - identify the borrower. It is also the primary key of
                  the table crcBORROWER.

    template - identify the template who will be used in the notification.

    message - message written by the administrator.

    subject - subject of the message.

    send_message - send a message/email to a borrower.
    """

    email = db.get_borrower_email(borrower_id)

    if load_msg_template and template != None:
        show_template = load_template(template)

    elif send_message:
        send_email(fromaddr="CERN Library<library.desk@cern.ch>",
                   toaddr=email,
                   subject=subject,
                   content=message,
                   header='',
                   footer='',
                   attempt_times=1,
                   attempt_sleeptime=10
                   )
        body = bibcirculation_templates.tmpl_send_notification(ln=ln)
    else:
        show_template = load_template(template)
        body = bibcirculation_templates.tmpl_borrower_notification(email=email,
                                                                   subject=subject,
                                                                   template=show_template,
                                                                   borrower_id=borrower_id,
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


def get_next_waiting_loan_request(req, recid, barcode, check_id,
                                  ln=CFG_SITE_LANG):
    """
    Return the next loan request who is waiting or pending.

    recid - identify the record. It is also the primary key of
            the table bibrec.

    barcode - identify the item. It is the primary key of the table
              crcITEM.

    check_id - identify the hold request. It is also the primary key
               of the table crcLOANREQUEST.
    """

    if check_id:
        db.update_loan_request_status(check_id,'cancelled')
    else:
        returned_on = datetime.date.today()
        db.update_item_status('available', barcode)
        db.update_loan_info(returned_on, 'returned', barcode)


    result = db.get_next_waiting_loan_request(recid)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_get_next_waiting_loan_request(result=result,
                                                                       recid=recid,
                                                                       barcode=barcode,
                                                                       ln=ln)

    return page(title="Next requests",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def update_next_loan_request_status(req, check_id, barcode, ln=CFG_SITE_LANG):
    """
    Update the status of a loan request who is defined as 'waiting' or 'pending'.
    The new status can be 'done' or 'cancelled'.

    check_id - identify the hold request. It is also the primary key
               of the table crcLOANREQUEST.

    barcode - identify the item. It is the primary key of the table
              crcITEM.
    """

    recid = db.get_recid_from_crcLOANREQUEST(check_id)
    borrower_id = db.get_borrower_id_from_crcLOANREQUEST(check_id)

    loaned_on = datetime.date.today()
    due_date = renew_loan_for_X_days(barcode)

    db.update_loan_request_status(check_id,'done')
    db.update_barcode_on_crcloanrequest(barcode, check_id)
    db.new_loan(borrower_id, recid, barcode, loaned_on, due_date, 'on loan', 'normal','')
    db.update_item_status('on loan', barcode)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_next_loan_request_done(ln=ln)

    return page(title="New Loan",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def loan_return(req, ln=CFG_SITE_LANG):
    """
    Page where is possible to register the return of an item.
    """

    infos = []

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_loan_return(infos=infos, ln=ln)

    return page(title="Loan return",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def loan_on_desk_step1(req, key, string, ln=CFG_SITE_LANG):
    """
    Step 1 of loan procedure. Search a user/borrower and return a list with
    all the possible results.

    key - attribute who will be considered during the search. Can be 'name',
          'email' or 'ccid/id'.

    string - keyword used during the search.
    """

    list_infos = []

    if USER_ON_CERN_LDAP == 'true':
        from invenio.bibcirculation_cern_ldap import get_user_info_from_ldap

        if key =='name' and string:
            result = get_user_info_from_ldap(nickname=string)

            for i in range(len(result)):

                try:
                    name = result[i][1]['cn'][0]
                except KeyError:
                    name = ""

                try:
                    ccid = result[i][1]['employeeID'][0]
                except KeyError:
                    ccid = ""

                try:
                    email = result[i][1]['mail'][0]
                except KeyError:
                    email = ""

                try:
                    phone = result[i][1]['telephoneNumber'][0]
                except KeyError:
                    phone = ""

                try:
                    address = result[i][1]['physicalDeliveryOfficeName'][0]
                except KeyError:
                    address = ""

                try:
                    mailbox = result[i][1]['postOfficeBox'][0]
                except KeyError:
                    mailbox = ""

                tup = (ccid, name, email, phone, address, mailbox)
                list_infos.append(tup)

        elif key =='email' and string:
            result = get_user_info_from_ldap(email=string)
            try:
                name = result['cn'][0]
            except KeyError:
                name = ""

            try:
                ccid = result['employeeID'][0]
            except KeyError:
                ccid = ""

            try:
                email = result['mail'][0]
            except KeyError:
                email = ""

            try:
                phone = result['telephoneNumber'][0]
            except KeyError:
                phone = ""

            try:
                address = result['physicalDeliveryOfficeName'][0]
            except KeyError:
                address = ""

            try:
                mailbox = result['postOfficeBox'][0]
            except KeyError:
                mailbox = ""

            tup = (ccid, name, email, phone, address, mailbox)
            list_infos.append(tup)

        elif key =='ccid' and string:
            result = get_user_info_from_ldap(ccid=string)

            try:
                name = result['cn'][0]
            except KeyError:
                name = ""

            try:
                ccid = result['employeeID'][0]
            except KeyError:
                ccid = ""

            try:
                email = result['mail'][0]
            except KeyError:
                email = ""

            try:
                phone = result['telephoneNumber'][0]
            except KeyError:
                phone = ""

            try:
                address = result['physicalDeliveryOfficeName'][0]
            except KeyError:
                address = ""

            try:
                mailbox = result['postOfficeBox'][0]
            except KeyError:
                mailbox = ""

            tup = (ccid, name, email, phone, address, mailbox)
            list_infos.append(tup)

        else:
            list_infos = []

    else:
        if key =='name' and string:
            result = db.get_borrower_data_by_name(string)

        elif key =='email' and string:
            result = db.get_borrower_data_by_email(string)

        else:
            result = db.get_borrower_data_by_id(string)

        for (borrower_id, name, email, phone, address, mailbox) in result:
            tup = (borrower_id, name, email, phone, address, mailbox)
            list_infos.append(tup)


    body = bibcirculation_templates.tmpl_loan_on_desk_step1(result=list_infos,
                                                            key=key,
                                                            string=string,
                                                            ln=ln)


    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)



    return page(title="Loan on desk",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def loan_on_desk_step2(req, user_info, ln=CFG_SITE_LANG):
    """
    Return the information about the user/borower who was selected in the
    previous step.

    user_info - information of the user/borrower who was selected.
    """

    body = bibcirculation_templates.tmpl_loan_on_desk_step2(user_info=user_info,
                                                            ln=ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    return page(title="Loan on desk",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def loan_on_desk_step3(req, ccid, name, email, phone,
                       address, mailbox, ln=CFG_SITE_LANG):
    """
    Display the user/borrower's information.
    """
    user_info = (ccid, name, email, phone, address, mailbox)

    body = bibcirculation_templates.tmpl_loan_on_desk_step3(user_info=user_info,
                                                            ln=ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    return page(title="Loan on desk",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def loan_on_desk_step4(req, user_info, barcode, ln=CFG_SITE_LANG):
    """
    Display the user/borrower's information and associate a
    list of barcodes to him.
    """

    infos = []
    list_of_books = []
    list_of_barcodes = barcode.split()

    for value in list_of_barcodes:
        recid = db.get_id_bibrec(value)
        tup = (recid, value)
        list_of_books.append(tup)
        queue = db.get_queue_request(recid)

        if len(queue) != 0:
            infos.append("Another user is waiting for the book: " \
                         + book_title_from_MARC(recid) +" [barcode: "+ value +"]. " \
                         "\n\n If you want continue with this loan choose" \
                         " [Continue]. Otherwise choose [Back].")


    body = bibcirculation_templates.tmpl_loan_on_desk_step4(user_info=user_info,
                                                            list_of_books=list_of_books,
                                                            infos=infos,
                                                            ln=ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    return page(title="Loan on desk",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def loan_on_desk_step5(req, list_of_books, user_info,
                       due_date, note, ln=CFG_SITE_LANG):
    """
    Register a new loan.
    """

    (ccid, name, email, phone, address, mailbox) = user_info

    loaned_on = datetime.date.today()
    is_borrower = db.is_borrower(email)

    if is_borrower != 0:
        for i in range(len(list_of_books)):
            if note:
                date = '[' + time.ctime() + '] '
                new_line = '\n'
                note = date + note + new_line
            db.new_loan(is_borrower, list_of_books[i][0], list_of_books[i][1],
                        loaned_on, due_date[i], 'on loan', 'normal', note)
            db.update_item_status('on loan', list_of_books[i][1])
    else:
        db.new_borrower(name, email, phone, address, mailbox, '')
        is_borrower = db.is_borrower(email)
        for i in range(len(list_of_books)):
            db.new_loan(is_borrower, list_of_books[i][0], list_of_books[i][1],
                        loaned_on, due_date[i], 'on loan', 'normal', note)
            db.update_item_status('on loan', list_of_books[i][1])

    body = bibcirculation_templates.tmpl_loan_on_desk_step5(ln=ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    return page(title="Loan on desk",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def loan_on_desk_confirm(req, barcode=None, borrower_id=None, ln=CFG_SITE_LANG):
    """
    Confirm the return of an item.

    barcode - identify the item. It is the primary key of the table
              crcITEM.

    borrower_id - identify the borrower. It is also the primary key of
                  the table crcBORROWER.
    """

    result = db.loan_on_desk_confirm(barcode, borrower_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_loan_on_desk_confirm(result=result,
                                                              barcode=barcode,
                                                              borrower_id=borrower_id,
                                                              ln=ln)

    return page(title="Loan on desk confirm",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def register_new_loan(req, barcode, borrower_id,
                      request_id, new_note, print_data, ln=CFG_SITE_LANG):
    """
    Register a new loan.

    barcode - identify the item. It is the primary key of the table
              crcITEM.

    borrower_id - identify the borrower. It is also the primary key of
                  the table crcBORROWER.

    request_id - identify the hold request. It is also the primary key
               of the table crcLOANREQUEST.

    new_note - associate a note to this loan.

    print_data - print the information about this loan.
    """

    _ = gettext_set_language(ln)

    if print_data == 'true':
        return print_new_loan_information(req, ln)

    else:
        recid = db.get_id_bibrec(barcode)
        loaned_on = datetime.date.today()
        due_date = renew_loan_for_X_days(barcode)

        if new_note:
            note = '[' + time.ctime() + '] ' + new_note + '\n'
            db.new_loan(borrower_id, recid, barcode,
                            loaned_on, due_date, 'on loan', 'normal', note)
        else:
            db.new_loan(borrower_id, recid, barcode,
                        loaned_on, due_date, 'on loan', 'normal','')

        requested_barcode = db.get_requested_barcode(request_id)

        if requested_barcode == barcode:
            db.update_item_status('on loan', barcode)
        else:
            db.update_item_status('on loan', barcode)
            db.update_item_status('available', requested_barcode)

        db.update_loan_request_status(request_id, 'done')
        db.update_barcode_on_crcloanrequest(barcode, request_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    borrower_info = db.get_borrower_data(borrower_id)

    body = bibcirculation_templates.tmpl_register_new_loan(loan_information=borrower_info,
                                                           ln=ln)

    return page(title="Loan on desk",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def loan_return_confirm(req, barcode, ln=CFG_SITE_LANG):
    """
    Display a form where it is possible to register the return of an item.

    barcode - identify the item. It is the primary key of the table
              crcITEM.
    """

    infos = []

    recid = db.get_id_bibrec(barcode)

    if recid is None:
        infos.append('"%s" >  Unknown barcode. Please try again.' % barcode)
        body = bibcirculation_templates.tmpl_loan_return(infos=infos, ln=ln)
    else:
        borrower_id = db.get_borrower_id(barcode)
        borrower_name = db.get_borrower_name(borrower_id)
        body = bibcirculation_templates.tmpl_loan_return_confirm(borrower_name=borrower_name,
                                                                 recid=recid,
                                                                 barcode=barcode,
                                                                 ln=ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)


    return page(title="Loan return",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)




def get_borrower_details(req, borrower_id, ln=CFG_SITE_LANG):
    """
    Display the details of a borrower.

    borrower_id - identify the borrower. It is also the primary key of
                  the table crcBORROWER.
    """
    borrower = db.get_borrower_details(borrower_id)
    requests = db.get_borrower_request_details(borrower_id)
    loans = db.get_borrower_loan_details(borrower_id)
    notes = db.get_borrower_notes(borrower_id)

    req_hist = db.bor_requests_historical_overview(borrower_id)
    loans_hist = db.bor_loans_historical_overview(borrower_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_borrower_details(borrower=borrower,
                                                          requests=requests,
                                                          loans=loans,
                                                          notes=notes,
                                                          req_hist=req_hist,
                                                          loans_hist=loans_hist,
                                                          ln=ln)

    return page(title="Borrower details",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def get_borrower_loans_details(req, recid, barcode, borrower_id,
                               renewall, force, loan_id, ln=CFG_SITE_LANG):
    """
    Show borrower's loans details.

    recid - identify the record. It is also the primary key of
            the table bibrec.

    barcode - identify the item. It is the primary key of the table
              crcITEM.

    borrower_id - identify the borrower. It is also the primary key of
                  the table crcBORROWER.

    renewall - renew all loans.

    force - force the renew of a loan, when usually this is not possible.

    loan_id - identify a loan. It is the primery key of the table
              crcLOAN.
    """

    infos = []

    force_renew_link = create_html_link(CFG_SITE_URL +
                        '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_loans_details',
                        {'barcode': barcode, 'borrower_id': borrower_id, 'loan_id': loan_id, 'force': 'true'},
                        ("Yes"))

    no_renew_link = create_html_link(CFG_SITE_URL +
                        '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_loans_details',
                        {'borrower_id': borrower_id},
                        ("No"))

    if barcode and loan_id and recid:
        queue = db.get_queue_request(recid)
        new_due_date = renew_loan_for_X_days(barcode)

        if len(queue) != 0:
            infos.append("Another user is waiting for this book <strong>"+ book_title_from_MARC(recid) +"</strong>." \
                         " \n\n Do you want renew this loan anyway? " \
                         " \n\n [%s] [%s]" % (force_renew_link, no_renew_link))
        else:
            db.update_due_date(loan_id, new_due_date)
            update_status_if_expired(loan_id)
            infos.append("Loan renewed with sucess!")

    elif loan_id and barcode and force == 'true':
        new_due_date = renew_loan_for_X_days(barcode)
        db.update_due_date(loan_id, new_due_date)
        update_status_if_expired(loan_id)
        infos.append("Loan renewed with sucess.")

    elif borrower_id and renewall=='true':
        list_of_loans = db.get_recid_borrower_loans(borrower_id)
        for (loan_id, recid, barcode) in list_of_loans:
            queue = db.get_queue_request(recid)
            new_due_date = renew_loan_for_X_days(barcode)

            force_renewall_link = create_html_link(CFG_SITE_URL +
                                                   '/admin/bibcirculation/bibcirculationadmin.py/get_borrower_loans_details',
                                                   {'barcode': barcode, 'borrower_id': borrower_id, 'loan_id': loan_id, 'force': 'true'},
                                                   ("Yes"))

            if len(queue) != 0:
                infos.append("Another user is waiting for this book <strong>"+ book_title_from_MARC(recid) +"</strong>. " \
                             "\n\n Do you want renew this loan anyway? " \
                             "\n\n [%s] [%s]" % (force_renewall_link, no_renew_link))
            else:
                db.update_due_date(loan_id, new_due_date)
                update_status_if_expired(loan_id)

        infos.append("All loans renewed with sucess.")

    borrower_loans = db.get_borrower_loan_details(borrower_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)


    body = bibcirculation_templates.tmpl_borrower_loans_details(borrower_loans=borrower_loans,
                                                                borrower_id=borrower_id,
                                                                infos=infos,
                                                                ln=ln)

    return page(title="Loans details - %s" % (db.get_borrower_name(borrower_id)),
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def get_item_loans_details(req, recid, barcode, loan_id, force, ln=CFG_SITE_LANG):
    """
    Show all the details about all loans related with an item.

    recid - identify the record. It is also the primary key of
            the table bibrec.

    barcode - identify the item. It is the primary key of the table
              crcITEM.

    loan_id - identify a loan. It is the primery key of the table
              crcLOAN.

    force - force the renew of a loan, when usually this is not possible.
    """

    infos = []

    if loan_id and barcode and force == 'true':
        new_due_date = renew_loan_for_X_days(barcode)
        db.update_due_date(loan_id, new_due_date)
        infos.append("Loan renewed with sucess.")

    elif barcode:
        recid = db.get_id_bibrec(barcode)
        queue = db.get_queue_request(recid)
        new_due_date = renew_loan_for_X_days(barcode)


        force_renew_link = create_html_link(CFG_SITE_URL +
                        '/admin/bibcirculation/bibcirculationadmin.py/get_item_loans_details',
                        {'barcode': barcode, 'loan_id': loan_id, 'force': 'true', 'recid': recid},
                        ("Yes"))

        no_renew_link = create_html_link(CFG_SITE_URL +
                        '/admin/bibcirculation/bibcirculationadmin.py/get_item_loans_details',
                        {'recid': recid},
                        ("No"))

        if len(queue) != 0:
            infos.append("Another user is waiting for this book " \
                         "("+ book_title_from_MARC(recid) +"). \n\n Do you want renew " \
                         "this loan anyway? \n\n" \
                         " [%s] [%s]" % (force_renew_link, no_renew_link))
        else:
            db.update_due_date(loan_id, new_due_date)
            infos.append("Loan renewed with sucess.")

    result = db.get_item_loans(recid)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_get_item_loans_details(result=result,
                                                                recid=recid,
                                                                infos=infos,
                                                                ln=ln)

    return page(title="Loans details - %s" % (book_title_from_MARC(recid)),
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def get_item_details(req, recid, ln=CFG_SITE_LANG):
    """
    Display the details of an item.

    recid - identify the record. It is also the primary key of
            the table bibrec.
    """

    copies = db.get_item_copies_details(recid)
    requests = db.get_item_requests(recid)
    loans = db.get_item_loans(recid)
    req_hist_overview = db.get_item_requests_historical_overview(recid)
    loans_hist_overview = db.get_item_loans_historical_overview(recid)


    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_get_item_details(recid=recid,
                                                          copies=copies,
                                                          requests=requests,
                                                          loans=loans,
                                                          req_hist_overview = req_hist_overview,
                                                          loans_hist_overview = loans_hist_overview,
                                                          ln=ln)

    return page(title="Item details",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def get_item_req_historical_overview(req, recid, ln=CFG_SITE_LANG):
    """
    Display the requests historical overview of an item.

    recid - identify the record. It is also the primary key of
            the table bibrec.
    """

    req_hist_overview = db.get_item_requests_historical_overview(recid)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_get_item_req_historical_overview(req_hist_overview = req_hist_overview,
                                                                          ln=ln)

    return page(title="Requests - historical overview",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def get_item_loans_historical_overview(req, recid, ln=CFG_SITE_LANG):
    """
    Display the loans historical overview of an item.

    recid - identify the record. It is also the primary key of
            the table bibrec.

    """

    loans_hist_overview = db.get_item_loans_historical_overview(recid)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_get_item_loans_historical_overview(loans_hist_overview = loans_hist_overview,
                                                                        ln=ln)

    return page(title="Loans - historical overview",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def bor_loans_historical_overview(req, borrower_id, ln=CFG_SITE_LANG):
    """
    Display the loans historical overview of a borrower.

    borrower_id - identify the borrower. It is also the primary key of
                  the table crcBORROWER.
    """

    loans_hist_overview = db.bor_loans_historical_overview(borrower_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_bor_loans_historical_overview(
        loans_hist_overview = loans_hist_overview,
        ln=ln)

    return page(title="Loans - historical overview",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def bor_requests_historical_overview(req, borrower_id, ln=CFG_SITE_LANG):
    """
    Display the requests historical overview of a borrower.

    borrower_id - identify the borrower. It is also the primary key of
                  the table crcBORROWER.
    """

    req_hist_overview = db.bor_requests_historical_overview(borrower_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_bor_requests_historical_overview(
        req_hist_overview = req_hist_overview,
        ln=ln)

    return page(title="Requests - historical overview",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def get_library_details(req, library_id, ln=CFG_SITE_LANG):
    """
    Display the details of a library.

    library_id - identify the library. It is also the primary key of
                 the table crcLIBRARY.
    """

    library_details = db.get_library_details(library_id)
    library_items = db.get_library_items(library_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_library_details(library_details=library_details,
                                                         library_items=library_items,
                                                         ln=ln)

    return page(title="Library details",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def get_borrower_requests_details(req, borrower_id, id_request, ln=CFG_SITE_LANG):
    """
    Display loans details of a borrower.

    borrower_id - identify the borrower. It is also the primary key of
                  the table crcBORROWER.

    id_request - identify the hold request. It is also the primary key
                 of the table crcLOANREQUEST.
    """

    if id_request:
        status = 'cancelled'
        db.cancel_request(id_request, status)

    result = db.get_borrower_request_details(borrower_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    name = db.get_borrower_name(borrower_id)

    title = "Hold requests details - %s" % (name)
    body = bibcirculation_templates.tmpl_borrower_request_details(result=result,
                                                                  borrower_id=borrower_id,
                                                                  ln=ln)

    return page(title=title,
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def get_pending_requests(req, request_id, print_data, ln=CFG_SITE_LANG):
    """
    Get all loans requests who are pending.
    """

    _ = gettext_set_language(ln)

    if print_data == 'true':
        return print_pending_hold_requests_information(req, ln)

    elif request_id:
        db.update_loan_request_status(request_id,'cancelled')
        result = db.get_pending_loan_request('pending')

    else:
        result = db.get_pending_loan_request('pending')

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_get_pending_requests(result=result,
                                                             ln=ln)

    return page(title="List of all pending requests",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def all_requests(req, request_id, ln=CFG_SITE_LANG):
    """
    Display all requests.

    request_id - identify the hold request. It is also the primary key
               of the table crcLOANREQUEST.
    """

    if request_id:
        db.update_loan_request_status(request_id, "cancelled")
        result = db.get_all_requests()
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

    return page(title="List of hold requests",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def all_loans(req, show, loans_per_page, jloan, ln=CFG_SITE_LANG):
    """
    Display all loans.
    """

    if show == 'expired':
        result = db.get_all_expired_loans()
        title = "List of all expired loans"
    elif show == 'on_loan':
        result = db.get_all_loans_onloan()
        title = "List of all loans ON LOAN?!?!"
    else:
        result = db.get_all_loans()
        title = "List of all loans"

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_all_loans(result=result,
                                                   show=show,
                                                   loans_per_page=loans_per_page,
                                                   jloan=jloan,
                                                   ln=ln)

    return page(title=title,
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def get_item_requests_details(req, recid, request_id, ln=CFG_SITE_LANG):
    """
    Display all requests for a specific item.

    recid - identify the record. It is also the primary key of
            the table bibrec.

    request_id - identify the hold request. It is also the primary key
               of the table crcLOANREQUEST.
    """

    result = db.get_item_requests(recid)

    if request_id:
        db.cancel_request(request_id, 'cancelled')

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_get_item_requests_details(recid=recid,
                                                                   result=result,
                                                                   ln=ln)

    return page(title="Hold requests - %s" % (book_title_from_MARC(recid)),
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def associate_barcode(req, request_id, recid, borrower_id, ln=CFG_SITE_LANG):
    """
    Associate a barcode to an hold request.

    request_id - identify the hold request. It is also the primary key
                 of the table crcLOANREQUEST.

    recid - identify the record. It is also the primary key of
            the table bibrec.

    borrower_id - identify the borrower. It is also the primary key of
                  the table crcBORROWER.
    """

    borrower = db.get_borrower_details(borrower_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_associate_barcode(request_id=request_id,
                                                           recid=recid,
                                                           borrower=borrower,
                                                           ln=ln)

    return page(title="Associate barcode",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)



def get_borrower_notes(req, borrower_id, add_notes, new_note, ln=CFG_SITE_LANG):
    """
    Retrieve the notes of a borrower.

    borrower_id - identify the borrower. It is also the primary key of
                  the table crcBORROWER.

    add_notes - display the textarea where will be written a new notes.

    new_notes - note who will be added to the others library's notes.
    """

    if new_note:
        new_note = '[' + time.ctime() + '] ' + new_note + '\n'
        db.add_new_note(new_note, borrower_id)

    borrower_notes = db.get_borrower_notes(borrower_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_borrower_notes(borrower_notes=borrower_notes,
                                                        borrower_id=borrower_id,
                                                        add_notes=add_notes,
                                                        ln=ln)
    return page(title="Borrower notes",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def get_loans_notes(req, loan_id, recid, borrower_id, add_notes, new_note, ln=CFG_SITE_LANG):
    """
    Get loan's note(s).

    loan_id - identify a loan. It is the primery key of the table
              crcLOAN.

    recid - identify the record. It is also the primary key of
            the table bibrec.

    borrower_id - identify the borrower. It is also the primary key of
                  the table crcBORROWER.

    add_notes - display the textarea where will be written a new notes.

    new_notes - note who will be added to the others library's notes.
    """

    if new_note:
        new_note = '[' + time.ctime() + '] ' + new_note + '\n'
        db.add_new_loan_note(new_note, loan_id)

    loans_notes = db.get_loans_notes(loan_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_loans_notes(loans_notes=loans_notes,
                                                     loan_id=loan_id,
                                                     recid=recid,
                                                     borrower_id=borrower_id,
                                                     add_notes=add_notes,
                                                     ln=ln)
    return page(title="Loan notes",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def add_new_borrower_step1(req, ln=CFG_SITE_LANG):
    """
    Add new borrower. Step 1
    """
    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_add_new_borrower_step1(ln=ln)

    return page(title="Add new borrower - I",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def add_new_borrower_step2(req, name, email, phone, address, mailbox,
                           notes, ln=CFG_SITE_LANG):
    """
    Add new borrower. Step 2.
    """

    tup_infos = (name, email, phone, address, mailbox, notes)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_add_new_borrower_step2(tup_infos=tup_infos,
                                                                ln=ln)

    return page(title="Add new borrower - II",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def add_new_borrower_step3(req, tup_infos, ln=CFG_SITE_LANG):
    """
    Add new borrower. Step 3.
    """

    db.new_borrower(tup_infos[0], tup_infos[1], tup_infos[2],
                    tup_infos[3], tup_infos[4], tup_infos[5])

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_add_new_borrower_step3(ln=ln)

    return page(title="Add new borrower - III",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def update_borrower_info_step1(req, ln=CFG_SITE_LANG):
    """
    Update the borrower's information.
    """

    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_update_borrower_info_step1(ln=ln)

    return page(title="Update borrower information - I",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_borrower_info_step2(req, column, string, ln=CFG_SITE_LANG):
    """
    Update the borrower's information.
    """

    if column == 'name':
        result = db.search_borrower_by_name(string)
    elif column == 'phone':
        result = db.search_borrower_by_phone(string)
    elif column == 'email':
        result = db.search_borrower_by_email(string)
    else:
        result = db.search_borrower_by_id(string)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_update_borrower_info_step2(result=result, ln=ln)

    return page(title="Update borrower information - II",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_borrower_info_step3(req, borrower_id, ln=CFG_SITE_LANG):
    """
    Update the borrower's information.

    borrower_id - identify the borrower. It is also the primary key of
                  the table crcBORROWER.
    """

    result = db.get_borrower_details(borrower_id)

    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_update_borrower_info_step3(result=result,
                                                                    ln=ln)

    return page(title="Update borrower information - III",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_borrower_info_step4(req, name, email, phone, address, mailbox,
                               ln=CFG_SITE_LANG):
    """
    Update the borrower's information.
    """

    tup_infos = (name, email, phone, address, mailbox)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_update_borrower_info_step4(tup_infos=tup_infos,
                                                                    ln=ln)

    return page(title="Update borrower information - IV",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_borrower_info_step5(req, tup_infos, ln=CFG_SITE_LANG):
    """
    Update the borrower's information.
    """

    borrower_id = db.is_borrower(tup_infos[1])
    db.update_borrower_info(borrower_id, tup_infos[0], tup_infos[1],
                            tup_infos[2], tup_infos[3], tup_infos[4])

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_update_borrower_info_step5(ln=ln)

    return page(title="Update borrower information - V",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def get_item_loans_notes(req, loan_id, recid, borrower_id, add_notes, new_note, ln=CFG_SITE_LANG):
    """
    Get loan's notes.

    loan_id - identify a loan. It is the primery key of the table
              crcLOAN.

    recid - identify the record. It is also the primary key of
            the table bibrec.

    borrower_id - identify the borrower. It is also the primary key of
                  the table crcBORROWER.

    add_notes - display the textarea where will be written a new notes.

    new_notes - note who will be added to the others library's notes.
    """

    if new_note:
        date = '[' + time.ctime() + '] '
        new_line = '\n'
        new_note = date + new_note + new_line
        db.add_new_loan_note(new_note, loan_id)

    loans_notes = db.get_loans_notes(loan_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_item_loans_notes(loans_notes=loans_notes,
                                                          loan_id=loan_id,
                                                          recid=recid,
                                                          borrower_id=borrower_id,
                                                          add_notes=add_notes,
                                                          ln=ln)
    return page(title="Loan notes",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)



def new_item(req, isbn, ln=CFG_SITE_LANG):
    """
    Add a new item using the ISBN.
    """

    book_info = []
    errors = []

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    if isbn:
        from xml.dom import minidom
        import urllib
        filexml = urllib.urlopen('http://ecs.amazonaws.com/onca/xml?' \
                                 'Service=AWSECommerceService&AWSAccessKeyId=' + ACCESS_KEY + \
                                 '&Operation=ItemSearch&Condition=All&' \
                                 'ResponseGroup=ItemAttributes&SearchIndex=Books&' \
                                 'Keywords=' + isbn)

        xmldoc = minidom.parse(filexml)

        try:
            get_error_code = xmldoc.getElementsByTagName('Code')
            get_error_message = xmldoc.getElementsByTagName('Message')
            error_code = get_error_code.item(0).firstChild.data
            error_message = get_error_message.item(0).firstChild.data
            errors.append(str(error_code))
            errors.append(str(error_message))
        except AttributeError:
            errors = ""

        try:
            get_author = xmldoc.getElementsByTagName('Author')
            author = get_author.item(0).firstChild.data
            book_info.append(str(author))
        except AttributeError:
            author = ""
            book_info.append(str(author))

        try:
            get_ean = xmldoc.getElementsByTagName('EAN')
            ean = get_ean.item(0).firstChild.data
            book_info.append(int(ean))
        except AttributeError:
            ean = ""
            book_info.append(str(ean))

        try:
            get_isbn = xmldoc.getElementsByTagName('ISBN')
            short_isbn = get_isbn.item(0).firstChild.data
            book_info.append(str(short_isbn))
        except AttributeError:
            short_isbn = ""
            book_info.append(str(short_isbn))

        try:
            get_publisher = xmldoc.getElementsByTagName('Manufacturer')
            publisher = get_publisher.item(0).firstChild.data
            book_info.append(str(publisher))
        except AttributeError:
            publisher = ""
            book_info.append(str(publisher))

        try:
            get_nb_pages = xmldoc.getElementsByTagName('NumberOfPages')
            nb_pages = get_nb_pages.item(0).firstChild.data
            book_info.append(int(nb_pages))
        except AttributeError:
            nb_pages = ""
            book_info.append(str(nb_pages))

        try:
            get_pub_date = xmldoc.getElementsByTagName('PublicationDate')
            pub_date = get_pub_date.item(0).firstChild.data
            book_info.append(str(pub_date))
        except AttributeError:
            pub_date = ""
            book_info.append(str(pub_date))

        try:
            get_title = xmldoc.getElementsByTagName('Title')
            title = get_title.item(0).firstChild.data
            book_info.append(str(title))
        except AttributeError:
            title = ""
            book_info.append(str(title))

        try:
            get_edition = xmldoc.getElementsByTagName('Edition')
            edition = get_edition.item(0).firstChild.data
            book_info.append(str(edition))
        except AttributeError:
            edition = ""
            book_info.append(str(edition))

        cover_xml = urllib.urlopen('http://ecs.amazonaws.com/onca/xml' \
                                   '?Service=AWSECommerceService&AWSAccessKeyId=' + ACCESS_KEY + \
                                   '&Operation=ItemSearch&Condition=All&' \
                                   'ResponseGroup=Images&SearchIndex=Books&' \
                                   'Keywords=' + isbn)

        xml_img = minidom.parse(cover_xml)

        try:
            get_cover_link = xml_img.getElementsByTagName('MediumImage')
            cover_link = get_cover_link.item(0).firstChild.firstChild.data
            book_info.append(str(cover_link))
        except AttributeError:
            cover_link = "http://cdsweb.cern.ch/img/book_cover_placeholder.gif"
            book_info.append(str(cover_link))

        if len(errors)!=0:
            body = bibcirculation_templates.tmpl_new_item(errors=errors, ln=ln)
        else:
            body = bibcirculation_templates.tmpl_new_item(book_info=book_info, ln=ln)

    else:
        body = bibcirculation_templates.tmpl_new_item(ln=ln)

    return page(title="New Item",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)



def add_new_library_step1(req, ln=CFG_SITE_LANG):
    """
    Add a new Library.
    """
    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_add_new_library_step1(ln=ln)

    return page(title="Add new library - I",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def add_new_library_step2(req, name, email, phone, address,
                           notes, ln=CFG_SITE_LANG):

    """
    Add a new Library.
    """

    tup_infos = (name, email, phone, address, notes)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_add_new_library_step2(tup_infos=tup_infos,
                                                                ln=ln)

    return page(title="Add new library - II",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def add_new_library_step3(req, tup_infos, ln=CFG_SITE_LANG):
    """
    Add a new Library.
    """
    (name, email, phone, address, notes) = tup_infos
    db.add_new_library(name, email, phone, address, notes)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_add_new_library_step3(ln=ln)

    return page(title="Add new library - III",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_library_info_step1(req, ln=CFG_SITE_LANG):
    """
    Update the library's information.
    """

    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_update_library_info_step1(ln=ln)

    return page(title="Update library information - I",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_library_info_step2(req, column, string, ln=CFG_SITE_LANG):
    """
    Update the library's information.
    """

    if column == 'name':
        result = db.search_library_by_name(string)
    else:
        result = db.search_library_by_email(string)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_update_library_info_step2(result=result, ln=ln)

    return page(title="Update library information - II",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_library_info_step3(req, library_id, ln=CFG_SITE_LANG):
    """
    Update the library's information.

    library_id - identify the library. It is also the primary key of
                 the table crcLIBRARY.

    """
    library_info = db.get_library_details(library_id)

    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_update_library_info_step3(library_info=library_info,
                                                                   ln=ln)

    return page(title="Update library information - III",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_library_info_step4(req, name, email, phone, address,
                              library_id, ln=CFG_SITE_LANG):
    """
    Update the library's information.
    """

    tup_infos = (library_id, name, email, phone, address)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_update_library_info_step4(tup_infos=tup_infos,
                                                                   ln=ln)

    return page(title="Update library information - IV",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_library_info_step5(req, tup_infos, ln=CFG_SITE_LANG):
    """
    Update the library's information.
    """

    (library_id, name, email, phone, address) = tup_infos

    db.update_library_info(library_id, name, email, phone, address)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_update_library_info_step5(ln=ln)

    return page(title="Update library information - V",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def add_new_copy_step1(req, ln=CFG_SITE_LANG):
    """
    Add a nex copy.
    """

    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_add_new_copy_step1(ln=ln)

    return page(title="Associate copy to item",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def add_new_copy_step2(req, p, f, ln=CFG_SITE_LANG):
    """
    Add a new copy.
    """

    result = perform_request_search(cc="Books", sc="1", p=p, f=f)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_add_new_copy_step2(result=result,
                                                            ln=ln)

    return page(title="Add new copy - II",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def add_new_copy_step3(req, recid, ln=CFG_SITE_LANG):
    """
    Add a new copy.
    """
    result = db.get_item_copies_details(recid)
    libraries = db.get_libraries()

    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_add_new_copy_step3(recid=recid,
                                                            result=result,
                                                            libraries=libraries,
                                                            ln=ln)

    return page(title="Add new copy - III",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def add_new_copy_step4(req, barcode, library, location, collection, description,
                       loan_period, status, recid, ln=CFG_SITE_LANG):

    """
    Add a new copy.
    """

    library_name = db.get_library_name(library)
    tup_infos = (barcode, library, library_name, location, collection, description,
                 loan_period, status, recid)

    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_add_new_copy_step4(tup_infos=tup_infos,
                                                            ln=ln)

    return page(title="Add new copy - IV",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def add_new_copy_step5(req, tup_infos, ln=CFG_SITE_LANG):
    """
    Add a new copy.
    """
    db.add_new_copy(tup_infos[0], tup_infos[8], tup_infos[1],
                    tup_infos[4], tup_infos[3], tup_infos[5],
                    tup_infos[6], tup_infos[7])

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_add_new_copy_step5(recid=tup_infos[8],
                                                            ln=ln)

    return page(title="Add new copy - V",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_item_info_step1(req, ln=CFG_SITE_LANG):
    """
    Update the item's information.
    """

    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_update_item_info_step1(ln=ln)

    return page(title="Update item information - I",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_item_info_step2(req, p, f, ln=CFG_SITE_LANG):
    """
    Update the item's information.
    """

    result = perform_request_search(cc="Books", sc="1", p=p, f=f)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_update_item_info_step2(result=result,
                                                                ln=ln)

    return page(title="Update item information - II",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_item_info_step3(req, recid, ln=CFG_SITE_LANG):
    """
    Update the item's information.
    """

    result = db.get_item_copies_details(recid)

    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_update_item_info_step3(recid=recid,
                                                            result=result,
                                                            ln=ln)

    return page(title="Update item information - III",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_item_info_step4(req, barcode, ln=CFG_SITE_LANG):
    """
    Update the item's information.
    """

    recid = db.get_id_bibrec(barcode)
    result = db.get_item_info(barcode)
    libraries = db.get_libraries()

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_update_item_info_step4(recid=recid,
                                                                result=result,
                                                                libraries=libraries,
                                                                ln=ln)

    return page(title="Update item information - IV",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_item_info_step5(req, barcode, library, location, collection, description,
                           loan_period, status, recid, ln=CFG_SITE_LANG):

    """
    Update the item's information.
    """
    library_name = db.get_library_name(library)
    tup_infos = (barcode, library, library_name, location, collection, description,
                 loan_period, status, recid)

    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_update_item_info_step5(tup_infos=tup_infos,
                                                                ln=ln)

    return page(title="Update item information - V",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_item_info_step6(req, tup_infos, ln=CFG_SITE_LANG):
    """
    Update the item's information.
    """

    db.update_item_info(tup_infos[0], tup_infos[1],
                        tup_infos[4], tup_infos[3], tup_infos[5],
                        tup_infos[6], tup_infos[7])

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_update_item_info_step6(ln=ln)

    return page(title="Update copy information - VI",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def search_library_step1(req, ln=CFG_SITE_LANG):
    """
    Display the form where we can search a library (by name or email).
    """


    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_search_library_step1(ln=ln)

    return page(title="Search library - I",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def search_library_step2(req, column, string, ln=CFG_SITE_LANG):
    """
    Search a library and return a list with all the possible results, using the
    parameters received from the previous step.

    column - identify the column, of the table crcLIBRARY, who will be
             considered during the search. Can be 'name' or 'email'.

    str - string used for the search process.
    """

    if column == 'name':
        result = db.search_library_by_name(string)
    else:
        result = db.search_library_by_email(string)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_search_library_step2(result=result, ln=ln)

    return page(title="Search library - II",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def get_library_notes(req, library_id, add_notes, new_note, ln=CFG_SITE_LANG):
    """
    Retrieve notes related with a library.

    library_id - identify the library. It is also the primary key of
                 the table crcLIBRARY.

    add_notes - display the textarea where will be written a new notes.

    new_notes - note who will be added to the others library's notes.
    """

    if new_note:
        date = '[' + time.ctime() + '] '
        new_line = '\n'
        new_note = date + new_note + new_line
        db.add_new_library_note(new_note, library_id)

    library_notes = db.get_library_notes(library_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_library_notes(library_notes=library_notes,
                                                       library_id=library_id,
                                                       add_notes=add_notes,
                                                       ln=ln)
    return page(title="Library notes",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)
