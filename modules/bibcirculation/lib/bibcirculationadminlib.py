# Administrator interface for Bibcirculation
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

from __future__ import division

"""CDS Invenio Bibcirculation Administrator Interface."""

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

import datetime, time

# Others Invenio imports
from invenio.config import \
    CFG_SITE_LANG, \
    CFG_SITE_URL, \
    CFG_CERN_SITE
import invenio.access_control_engine as acce
from invenio.webpage import page
from invenio.webuser import getUid, page_not_authorized
from invenio.mailutils import send_email
from invenio.search_engine import perform_request_search
from invenio.urlutils import create_html_link, redirect_to_url
from invenio.messages import gettext_set_language
from invenio.bibcirculation_utils import book_title_from_MARC, \
      update_status_if_expired, \
      renew_loan_for_X_days, \
      print_pending_hold_requests_information, \
      print_new_loan_information, \
      update_request_data, \
      validate_date_format, \
      create_ill_record, \
      generate_email_body
      #get_list_of_ILL_requests, \
      #create_item_details_url

# Bibcirculation imports
from invenio.bibcirculation_config import \
     CFG_BIBCIRCULATION_TEMPLATES, CFG_BIBCIRCULATION_AMAZON_ACCESS_KEY, \
     CFG_BIBCIRCULATION_LIBRARIAN_EMAIL
import invenio.bibcirculation_dblayer as db
import invenio.template
bibcirculation_templates = invenio.template.load('bibcirculation')

def is_adminuser(req):
    """check if user is a registered administrator. """

    return acce.acc_authorize_action(req, "runbibcirculation")

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


def borrower_search(req, empty_barcode, redirect='no', ln=CFG_SITE_LANG):
    """
    Page (for administrator) where is it possible to search
    for a borrower (who is on crcBORROWER table) using is name,
    email, phone or id.
    """

    infos = []

    if empty_barcode:
        infos.append(empty_barcode)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a> &gt; <a class="navtrail" ' \
                              'href="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1">Circulation Management' \
                              '</a> ' % (CFG_SITE_URL, CFG_SITE_URL)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_borrower_search(infos=infos, redirect=redirect, ln=ln)

    if redirect == 'yes':
        title="New Request"
    else:
        title="Borrower Search"

    return page(title=title,
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

    @type p:   string
    @param p:  search pattern

    @type f:   string
    @param f:  search field

    @return:   list of recids
    """

    if f == 'barcode':
        has_recid = db.get_recid(p)
        infos = []

        if has_recid is None:
            infos.append('The barcode <strong>%s</strong> does not exist on BibCirculation database.' % p)
            body = bibcirculation_templates.tmpl_item_search(infos=infos, ln=ln)
        else:
            body = bibcirculation_templates.tmpl_item_search_result(result=has_recid, ln=ln)
    else:
        result = perform_request_search(cc="Books", sc="1", p=p, f=f)
        body = bibcirculation_templates.tmpl_item_search_result(result=result, ln=ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a> &gt; <a class="navtrail" ' \
                              'href="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1">Circulation Management' \
                              '</a> ' % (CFG_SITE_URL, CFG_SITE_URL)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    return page(title="Item search result",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def borrower_search_result(req, column, string, redirect='no', ln=CFG_SITE_LANG):
    """
    Search a borrower and return a list with all the possible results.

    @type column:  string
    @param column: identify the column, of the table crcBORROWER, who will be
                   considered during the search. Can be 'name', 'email' or 'id'.

    @type string:  string
    @param string: string used for the search process.

    @return:       list of borrowers.
    """

    if string == '':
        empty_barcode = 'Empty string. Please, try again.'
        return borrower_search(req, empty_barcode, ln)

    if CFG_CERN_SITE == 1:
        if column == 'name':
            result = db.search_borrower_by_name(string)
        elif column == 'email':
            result = db.search_borrower_by_email(string)
        else:
            from invenio.bibcirculation_cern_ldap import get_user_info_from_ldap
            ldap_info = get_user_info_from_ldap(ccid=string)

            try:
                mail = ldap_info['mail'][0]
            except KeyError:
                mail = None

            if mail:
                result = db.search_borrower_by_email(mail)
            else:
                result = ()

    else:
        if column == 'name':
            result = db.search_borrower_by_name(string)
        elif column == 'email':
            result = db.search_borrower_by_email(string)
        else:
            result = db.search_borrower_by_id(string)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a> &gt; <a class="navtrail" ' \
                              'href="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1">Circulation Management' \
                              '</a> ' % (CFG_SITE_URL, CFG_SITE_URL)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    if len(result) == 1:
        if redirect=='no':
            return get_borrower_details(req, result[0][0], ln)
        else:
            return create_new_request_step1(req, result[0][0])
    else:
        body = bibcirculation_templates.tmpl_borrower_search_result(result=result, redirect=redirect, ln=ln)

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
    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a> &gt; <a class="navtrail" ' \
                              'href="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1">Circulation Management' \
                              '</a> ' % (CFG_SITE_URL, CFG_SITE_URL)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    infos = []

    body = bibcirculation_templates.tmpl_item_search(infos=infos, ln=ln)

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

    @type template:  string.
    @param template: template who will be used in the notification.

    @return:         template(string)
    """

    if template == "overdue_letter":
        output = CFG_BIBCIRCULATION_TEMPLATES['OVERDUE']

    elif template == "reminder":
        output = CFG_BIBCIRCULATION_TEMPLATES['REMINDER']

    elif template == "notification":
        output = CFG_BIBCIRCULATION_TEMPLATES['NOTIFICATION']

    elif template == "claim_return":
        output = CFG_BIBCIRCULATION_TEMPLATES['SEND_RECALL']

    else:
        output = CFG_BIBCIRCULATION_TEMPLATES['EMPTY']

    return output



def borrower_notification(req, borrower_id, template, message,
                          load_msg_template, subject, send_message,
                          ln=CFG_SITE_LANG):
    """
    Send a message/email to a borrower.

    @type borrower_id:   integer.
    @param borrower_id:  identify the borrower. It is also the primary key of
                         the table crcBORROWER.

    @type template:      string.
    @param template:     identify the template who will be used in the notification.

    @type message:       string.
    @param message:      message written by the administrator.

    @type subject:       string.
    @param subject:      subject of the message.

    @return:             send a message/email to a borrower.
    """

    email = db.get_borrower_email(borrower_id)

    if load_msg_template and template is not None:
        show_template = load_template(template)

    elif send_message:
        send_email(fromaddr=CFG_BIBCIRCULATION_LIBRARIAN_EMAIL,
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
                              'href="%s/help/admin">Admin Area' \
                              '</a> &gt; <a class="navtrail" ' \
                              'href="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1">Circulation Management' \
                              '</a> ' % (CFG_SITE_URL, CFG_SITE_URL)

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

    @type recid:     integer.
    @param recid:    identify the record. It is also the primary key of
                     the table bibrec.

    @type barcode:   string.
    @param barcode:  identify the item. It is the primary key of the table
                     crcITEM.

    @type check_id:  integer.
    @param check_id: identify the hold request. It is also the primary key
                     of the table crcLOANREQUEST.

    @return:         list of waiting requests with the same recid.
    """

    if check_id:
        db.update_loan_request_status(check_id,'cancelled')
        update_request_data(check_id)
    else:
        returned_on = datetime.date.today()
        db.update_item_status('available', barcode)
        db.update_loan_info(returned_on, 'returned', barcode)

    result = db.get_next_waiting_loan_request(recid)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a> &gt; <a class="navtrail" ' \
                              'href="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1">Circulation Management' \
                              '</a> ' % (CFG_SITE_URL, CFG_SITE_URL)

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

    @type check_id:  integer.
    @param check_id: identify the hold request. It is also the primary key
                     of the table crcLOANREQUEST.

    @type barcode:   string.
    @param barcode:  identify the item. It is the primary key of the table
                     crcITEM.
    """

    recid = db.get_request_recid(check_id)
    borrower_id = db.get_request_borrower_id(check_id)
    borrower_info = db.get_borrower_details(borrower_id)

    loaned_on = datetime.date.today()
    due_date = renew_loan_for_X_days(barcode)

    db.update_loan_request_status(check_id,'done')
    db.update_request_barcode(barcode, check_id)
    db.new_loan(borrower_id, recid, barcode, loaned_on, due_date, 'on loan', 'normal','')
    db.update_item_status('on loan', barcode)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a> &gt; <a class="navtrail" ' \
                              'href="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1">Circulation Management' \
                              '</a> ' % (CFG_SITE_URL, CFG_SITE_URL)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_register_new_loan(borrower_info=borrower_info, recid=recid, ln=ln)

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
                              '</a> &gt; <a class="navtrail" ' \
                              'href="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1">Circulation Management' \
                              '</a> ' % (CFG_SITE_URL, CFG_SITE_URL)

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

    @type key:     string.
    @param key:    attribute who will be considered during the search. Can be 'name',
                   'email' or 'ccid/id'.

    @type string:  string.
    @param string: keyword used during the search.

    @return:       list of potential borrowers.
    """

    infos = []

    if key and not string:
        infos.append('Empty string. Please, try again.')
        body = bibcirculation_templates.tmpl_loan_on_desk_step1(result=None,
                                                                key=key,
                                                                string=string,
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


    list_infos = []

    if CFG_CERN_SITE == 1:

        if key =='ccid' and string:
            from invenio.bibcirculation_cern_ldap import get_user_info_from_ldap
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

        elif key =='name' and string:
            result = db.get_borrower_data_by_name(string)

            for (borrower_id, name, email, phone, address, mailbox) in result:
                tup = (borrower_id, name, email, phone, address, mailbox)
                list_infos.append(tup)

        elif key =='email' and string:
            result = db.get_borrower_data_by_email(string)

            for (borrower_id, name, email, phone, address, mailbox) in result:
                tup = (borrower_id, name, email, phone, address, mailbox)
                list_infos.append(tup)
        else:
            result = list_infos

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

    if len(result) == 0 and key:
        infos.append("0 borrowers found.")

    elif len(list_infos) == 1:
        return loan_on_desk_step2(req, tup, ln)

    body = bibcirculation_templates.tmpl_loan_on_desk_step1(result=list_infos,
                                                                key=key,
                                                                string=string,
                                                                infos=infos,
                                                                ln=ln)


    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    return page(title="Circulation management",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def loan_on_desk_step2(req, user_info, ln=CFG_SITE_LANG):
    """
    Display the user/borrower's information.

    @type ccid:     integer.
    @type name:     string.
    @type email:    string.
    @type phone:    string.
    @type address:  string.
    @type mailbox:  string.
    """

    infos = []

    body = bibcirculation_templates.tmpl_loan_on_desk_step2(user_info=user_info,
                                                            infos=infos,
                                                            ln=ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    return page(title="Circulation management",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def loan_on_desk_step3(req, user_info, barcode, ln=CFG_SITE_LANG):
    """
    Display the user/borrower's information and associate a
    list of barcodes to him.

    @type user_info:   list.
    @param user_info:  information of the user/borrower who was selected.

    @type barcode:  string.
    @param barcode: identify the item. It is the primary key of the table
                    crcITEM.
    """
    infos = []
    list_of_books = []
    list_of_barcodes = barcode.split()

    #user_info = [ccid, name, email, phone, address, mailbox]

    for value in list_of_barcodes:

        recid = db.get_id_bibrec(value)
        loan_id = db.is_item_on_loan(value)
        queue = db.get_queue_request(recid)

        if recid is None:
            infos.append('"%s" > Unknown barcode. Please, try again.' % value)
            body = bibcirculation_templates.tmpl_loan_on_desk_step2(user_info=user_info,
                                                                    infos=infos,
                                                                    ln=ln)
        elif loan_id:
            infos.append('The item with the barcode "%s" is on loan.' % value)
            body = bibcirculation_templates.tmpl_loan_on_desk_step2(user_info=user_info,
                                                                    infos=infos,
                                                                    ln=ln)
        else:
            (library_id, location) = db.get_lib_location(value)
            tup = (recid, value, library_id, location)
            list_of_books.append(tup)

            if len(queue) != 0:
                infos.append("Another user is waiting for the book:<strong> " \
                             + book_title_from_MARC(recid) +" ["+ value +"]</strong>. " \
                             "\n\n If you want continue with this loan choose" \
                             " <strong>[Continue]</strong>.")

            body = bibcirculation_templates.tmpl_loan_on_desk_step3(user_info=user_info,
                                                                    list_of_books=list_of_books,
                                                                    infos=infos,
                                                                    ln=ln)

    if list_of_barcodes == []:
        infos.append('Empty barcode. Please, try again.')
        body = bibcirculation_templates.tmpl_loan_on_desk_step2(user_info=user_info,
                                                                infos=infos,
                                                                ln=ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    return page(title="Circulation management",
                uid=id_user,
                req=req,
                body=body,
                metaheaderadd = "<link rel=\"stylesheet\" href=\"%s/img/jquery-ui.css\" type=\"text/css\" />" % CFG_SITE_URL,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def loan_on_desk_step4(req, list_of_books, user_info,
                       due_date, note, ln=CFG_SITE_LANG):
    """
    Register a new loan.

    @type list_of_books:  list.
    @param list_of_books: list of books who will on loan.

    @type user_info:      list.
    @param user_info:     information of the user/borrower who was selected.

    @type due_date:       list.
    @param due_date:      list of due dates.

    @type note:           string.
    @param note:          note about the new loan.

    @return:              new loan.
    """

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    infos = []

    (_ccid, name, email, phone, address, mailbox) = user_info

    loaned_on = datetime.date.today()
    is_borrower = db.is_borrower(email)

    #Check if one of the given items is on loan.
    on_loan = []

    for i in range(len(list_of_books)):
        is_on_loan = db.is_on_loan(list_of_books[i][1])
        if is_on_loan:
            on_loan.append(list_of_books[i][1])

    if len(on_loan) != 0:
        infos.append("The item(s) with barcode(s) <strong>%s</strong> is(are) already on loan." % on_loan)

        body = bibcirculation_templates.tmpl_loan_on_desk_step1(result=None,
                                                                key='',
                                                                string='',
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

    # validate the period of interest given by the admin
    for date in due_date:
        if validate_date_format(date) is False:
            infos = []
            infos.append("The given due date <strong>%s</strong>" \
                         " is not a valid date or date format" % date)

            body = bibcirculation_templates.tmpl_loan_on_desk_step3(user_info=user_info,
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

            return page(title="Circulation management",
                        uid=id_user,
                        req=req,
                        body=body,
                        navtrail=navtrail_previous_links,
                        lastupdated=__lastupdated__)

    if is_borrower == 0:
        db.new_borrower(name, email, phone, address, mailbox, '')
        is_borrower = db.is_borrower(email)

    for i in range(len(list_of_books)):
        note_format = {}
        if note:
            note_format[time.strftime("%Y-%m-%d %H:%M:%S")] = str(note)

        db.new_loan(is_borrower, list_of_books[i][0], list_of_books[i][1],
                    loaned_on, due_date[i], 'on loan', 'normal', note_format)
        db.update_item_status('on loan', list_of_books[i][1])

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    return redirect_to_url(req, '%s/admin/bibcirculation/bibcirculationadmin.py/all_loans?msg=ok' % CFG_SITE_URL)


def loan_on_desk_confirm(req, barcode=None, borrower_id=None, ln=CFG_SITE_LANG):
    """
    Confirm the return of an item.

    @type barcode:       string.
    @param barcode:      identify the item. It is the primary key of the table
                         crcITEM.

    @type borrower_id:   integer.
    @param borrower_id:  identify the borrower. It is also the primary key of
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

    @type barcode:       string.
    @param barcode:      identify the item. It is the primary key of the table
                         crcITEM.

    @type borrower_id:   integer.
    @param borrower_id:  identify the borrower. It is also the primary key of
                         the table crcBORROWER.

    @type request_id:    integer.
    @param request_id:   identify the hold request. It is also the primary key
                         of the table crcLOANREQUEST.

    @type new_note:     string.
    @param new_note:    associate a note to this loan.

    @type print_data:   string.
    @param print_data:  print the information about this loan.

    @return:            new loan.
    """

    _ = gettext_set_language(ln)

    has_recid = db.get_id_bibrec(barcode)
    loan_id = db.is_item_on_loan(barcode)

    recid = db.get_request_recid(request_id)
    list_of_barcodes = db.get_barcodes(recid)

    infos = []


    if print_data == 'true':
        return print_new_loan_information(req, ln)

    if has_recid is None:
        infos.append('"%s" > Unknown barcode. Please try again.' % barcode)
        borrower = db.get_borrower_details(borrower_id)
        title="Associate barcode"
        body = bibcirculation_templates.tmpl_associate_barcode(request_id=request_id,
                                                               recid=recid,
                                                               borrower=borrower,
                                                               infos=infos,
                                                               ln=ln)

    elif loan_id:
        infos.append('The item with the barcode "%s" is on loan.' % barcode)
        borrower = db.get_borrower_details(borrower_id)
        title="Associate barcode"
        body = bibcirculation_templates.tmpl_associate_barcode(request_id=request_id,
                                                               recid=recid,
                                                               borrower=borrower,
                                                               infos=infos,
                                                               ln=ln)

    elif barcode not in list_of_barcodes:
        infos.append('The given barcode "%s" does not correspond to requested item.' % barcode)
        borrower = db.get_borrower_details(borrower_id)
        title="Associate barcode"
        body = bibcirculation_templates.tmpl_associate_barcode(request_id=request_id,
                                                               recid=recid,
                                                               borrower=borrower,
                                                               infos=infos,
                                                               ln=ln)

    else:
        recid = db.get_id_bibrec(barcode)
        loaned_on = datetime.date.today()
        due_date = renew_loan_for_X_days(barcode)

        if new_note:
            note_format = '[' + time.ctime() + '] ' + new_note + '\n'
        else:
            note_format = ''

        db.new_loan(borrower_id, recid, barcode,
                    loaned_on, due_date, 'on loan', 'normal', note_format)

        requested_barcode = db.get_requested_barcode(request_id)

        if requested_barcode == barcode:
            db.update_item_status('on loan', barcode)
        else:
            db.update_item_status('on loan', barcode)
            db.update_item_status('available', requested_barcode)

        db.update_loan_request_status(request_id, 'done')
        db.update_request_barcode(barcode, request_id)

        #borrower_info = db.get_borrower_data(borrower_id)

        result = db.get_all_loans(20)

        infos.append('A new loan has been registered with success.')

        title="Current loans"
        body = bibcirculation_templates.tmpl_all_loans(result=result,
                                                   infos=infos,
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

def loan_return_confirm(req, barcode, ln=CFG_SITE_LANG):
    """
    Display a form where it is possible to register the return of an item.

    @type barcode:   string.
    @param barcode:  identify the item. It is the primary key of the table
                     crcITEM.
    """

    infos = []

    recid = db.get_id_bibrec(barcode)
    loan_id = db.is_item_on_loan(barcode)

    if recid is None:
        infos.append('"%s" >  Unknown barcode. Please try again.' % barcode)
        body = bibcirculation_templates.tmpl_loan_return(infos=infos, ln=ln)
    elif loan_id is None:
        infos.append('The item with the barcode <strong>%s</strong> is not on loan. Please try again.' % barcode)
        body = bibcirculation_templates.tmpl_loan_return(infos=infos, ln=ln)
    else:
        borrower_id = db.get_borrower_id(barcode)
        borrower_name = db.get_borrower_name(borrower_id)

        db.update_item_status('available', barcode)
        db.update_loan_info(datetime.date.today(), 'returned', barcode)

        result = db.get_next_waiting_loan_request(recid)
        body = bibcirculation_templates.tmpl_loan_return_confirm(borrower_name=borrower_name,
                                                                 borrower_id=borrower_id,
                                                                 recid=recid,
                                                                 barcode=barcode,
                                                                 return_date=datetime.date.today(),
                                                                 result=result,
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

    @type borrower_id:   integer.
    @param borrower_id:  identify the borrower. It is also the primary key of
                         the table crcBORROWER.
    """

    borrower = db.get_borrower_details(borrower_id)
    requests = db.get_borrower_request_details(borrower_id)
    loans = db.get_borrower_loan_details(borrower_id)
    notes = db.get_borrower_notes(borrower_id)
    ill = db.get_ill_requests_details(borrower_id)

    req_hist = db.bor_requests_historical_overview(borrower_id)
    loans_hist = db.bor_loans_historical_overview(borrower_id)
    ill_hist = db.bor_ill_historical_overview(borrower_id)

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
                                                          ill=ill,
                                                          req_hist=req_hist,
                                                          loans_hist=loans_hist,
                                                          ill_hist=ill_hist,
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

    @type recid:         integer.
    @param recid:        identify the record. It is also the primary key of
                         the table bibrec.

    @type barcode:       string.
    @param barcode:      identify the item. It is the primary key of the table
                         crcITEM.

    @type borrower_id:   integer.
    @param borrower_id:  identify the borrower. It is also the primary key of
                         the table crcBORROWER.

    @type renewall:      string.
    @param renewall:     renew all loans.

    @type force:         string.
    @param force:        force the renew of a loan, when usually this is not possible.

    @type loan_id:       integer.
    @param loan_id:      identify a loan. It is the primery key of the table
                         crcLOAN.

    @return:             borrower loans details.
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
            infos.append("Loan renewed with success!")

    elif loan_id and barcode and force == 'true':
        new_due_date = renew_loan_for_X_days(barcode)
        db.update_due_date(loan_id, new_due_date)
        update_status_if_expired(loan_id)
        infos.append("Loan renewed with success.")

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

        infos.append("All loans renewed with success.")

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

    @type recid:      integer.
    @param recid:     identify the record. It is also the primary key of
                      the table bibrec.

    @type barcode:    string.
    @param barcode:   identify the item. It is the primary key of the table
                      crcITEM.

    @type loan_id:    integer.
    @param loan_id:   identify a loan. It is the primery key of the table
                      crcLOAN.

    @type force:      string.
    @param force:     force the renew of a loan, when usually this is not possible.

    @return:          item loans details.
    """

    infos = []

    if loan_id and barcode and force == 'true':
        new_due_date = renew_loan_for_X_days(barcode)
        db.update_due_date(loan_id, new_due_date)
        infos.append("Loan renewed with success.")

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
            infos.append("Loan renewed with success.")

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

    return page(title="Loans details - %s" % (book_title_from_MARC(int(recid))),
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def get_item_details(req, recid, ln=CFG_SITE_LANG):
    """
    Display the details of an item.


    @type recid:   integer.
    @param recid:  identify the record. It is also the primary key of
                   the table bibrec.

    @return:       item details.
    """
    infos = []

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
                                                          infos=infos,
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

    @type recid:   integer.
    @param recid:  identify the record. It is also the primary key of
                   the table bibrec.

    @return:       Item requests - historical overview.
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

    @type recid:   integer.
    @param recid:  identify the record. It is also the primary key of
                   the table bibrec.

    @return:       Item loans - historical overview.
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

    @type borrower_id:   integer.
    @param borrower_id:  identify the borrower. It is also the primary key of
                         the table crcBORROWER.

    @return:             borrower loans - historical overview.
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

    @type borrower_id:   integer.
    @param borrower_id:  identify the borrower. It is also the primary key of
                         the table crcBORROWER.

    @return:             borrower requests - historical overview.
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

    @type library_id:    integer.
    @param library_id:   identify the library. It is also the primary key of
                         the table crcLIBRARY.

    @return:             library details.
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

def get_borrower_requests_details(req, borrower_id, request_id, ln=CFG_SITE_LANG):
    """
    Display loans details of a borrower.

    @type borrower_id:  integer.
    @param borrower_id: identify the borrower. It is also the primary key of
                        the table crcBORROWER.

    @type request_id:   integer.
    @param request_id:  identify the hold request. It is also the primary key
                        of the table crcLOANREQUEST.

    @return:            borrower requests details.
    """

    if request_id:
        db.cancel_request(request_id, 'cancelled')
        update_request_data(request_id)

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

    @type request_id:   integer.
    @param request_id:  identify the hold request. It is also the primary key
                        of the table crcLOANREQUEST.

    @type print_data:   string.
    @param print_data:  print requests information.

    @return:            list of pending requests (on shelf with hold).
    """

    _ = gettext_set_language(ln)

    if print_data == 'true':
        return print_pending_hold_requests_information(req, ln)

    elif request_id:
        db.update_loan_request_status(request_id,'cancelled')
        update_request_data(request_id)
        result = db.get_loan_request_by_status('pending')

    else:
        result = db.get_loan_request_by_status('pending')

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_get_pending_requests(result=result, ln=ln)

    return page(title="Items on shelf with holds",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def get_waiting_requests(req, request_id, print_data, ln=CFG_SITE_LANG):
    """
    Get all loans requests who are waiting.

    @type request_id:   integer.
    @param request_id:  identify the hold request. It is also the primary key
                        of the table crcLOANREQUEST.

    @type print_data:   string.
    @param print_data:  print requests information.

    @return:            list of waiting requests (on loan with hold).
    """

    _ = gettext_set_language(ln)

    if print_data == 'true':
        return print_pending_hold_requests_information(req, ln)

    elif request_id:
        db.update_loan_request_status(request_id,'cancelled')
        update_request_data(request_id)
        result = db.get_loan_request_by_status('waiting')

    else:
        result = db.get_loan_request_by_status('waiting')

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_get_waiting_requests(result=result,
                                                             ln=ln)

    return page(title="Items on loan with holds",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def all_requests(req, request_id, ln=CFG_SITE_LANG):
    """
    Display all requests.

    @type request_id:   integer.
    @param request_id:  identify the hold request. It is also the primary key
                        of the table crcLOANREQUEST.
    """

    if request_id:
        db.update_loan_request_status(request_id, "cancelled")
        update_request_data(request_id)
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


def all_loans(req, msg=None, ln=CFG_SITE_LANG):
    """
    Display all loans.

    @type loans_per_page:   integer.
    @param loans_per_page:  number of loans per page.

    @type jloan:            integer.
    @param jloan:           jump to next loan.

    @return:                list with all loans (current loans).
    """

    infos = []

    if msg=='ok':
        infos.append('A new loan has been registered with success.')

    result = db.get_all_loans(20)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a> &gt; <a class="navtrail" ' \
                              'href="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1">Circulation Management' \
                              '</a> ' % (CFG_SITE_URL, CFG_SITE_URL)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_all_loans(result=result, infos=infos, ln=ln)

    return page(title="Current loans",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def all_loans_test(req, ln=CFG_SITE_LANG):
    """
    Display all loans.

    @return: list with all loans (current loans).
    """

    result = db.get_all_loans(20)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_all_loans_test(result=result,
                                                        ln=ln)

    return page(title="TEST loans",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def all_expired_loans(req, ln=CFG_SITE_LANG):
    """
    Display all loans.

    @type loans_per_page:   integer.
    @param loans_per_page:  number of loans per page.

    @type jloan:            integer.
    @param jloan:           jump to next loan.

    @return:                list with all expired loans (overdue loans).
    """
    result = db.get_all_expired_loans()

    infos = []

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a> &gt; <a class="navtrail" ' \
                              'href="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1">Circulation Management' \
                              '</a> ' % (CFG_SITE_URL, CFG_SITE_URL)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_all_expired_loans(result=result, infos=infos, ln=ln)

    return page(title='Overdue loans',
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def get_item_requests_details(req, recid, request_id, ln=CFG_SITE_LANG):
    """
    Display all requests for a specific item.

    @type recid:         integer.
    @param recid:        identify the record. It is also the primary key of
                         the table bibrec.

    @type request_id:    integer.
    @param request_id:   identify the hold request. It is also the primary key
                         of the table crcLOANREQUEST.

    @return:             Item requests details.
    """


    if request_id:
        db.cancel_request(request_id, 'cancelled')
        update_request_data(request_id)

    result = db.get_item_requests(recid)

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

    @type request_id:     integer.
    @param request_id:    identify the hold request. It is also the primary key
                          of the table crcLOANREQUEST.

    @type recid:          integer.
    @param recid:         identify the record. It is also the primary key of
                          the table bibrec.

    @type borrower_id:    integer.
    @param borrower_id:   identify the borrower. It is also the primary key of
                          the table crcBORROWER.
    """

    borrower = db.get_borrower_details(borrower_id)
    infos = []

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
                                                           infos=infos,
                                                           ln=ln)

    return page(title="Associate barcode",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)



def get_borrower_notes(req, borrower_id, delete_key, library_notes, ln=CFG_SITE_LANG):
    """
    Retrieve the notes of a borrower.

    @type borrower_id:    integer.
    @param borrower_id:   identify the borrower. It is also the primary key of
                          the table crcBORROWER.

   """

    if delete_key and borrower_id:
        borrower_notes = eval(db.get_borrower_notes(borrower_id))
        del borrower_notes[delete_key]
        db.update_borrower_notes(borrower_id, borrower_notes)

    elif library_notes:
        if db.get_borrower_notes(borrower_id):
            borrower_notes = eval(db.get_borrower_notes(borrower_id))
        else:
            borrower_notes = {}

        borrower_notes[time.strftime("%Y-%m-%d %H:%M:%S")] = str(library_notes)
        db.update_borrower_notes(borrower_id, borrower_notes)

    borrower_notes = db.get_borrower_notes(borrower_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a> &gt; <a class="navtrail" ' \
                              'href="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1">Circulation Management' \
                              '</a> ' % (CFG_SITE_URL, CFG_SITE_URL)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_borrower_notes(borrower_notes=borrower_notes,
                                                        borrower_id=borrower_id,
                                                        ln=ln)

    return page(title="Borrower notes",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def get_loans_notes(req, loan_id, delete_key,
                    library_notes, back, ln=CFG_SITE_LANG):
    """
    Get loan's note(s).

    @type loan_id:       integer.
    @param loan_id:      identify a loan. It is the primery key of the table
                         crcLOAN.

    """

    if delete_key and loan_id:
        loans_notes = eval(db.get_loan_notes(loan_id))
        del loans_notes[delete_key]
        db.update_loan_notes(loan_id, loans_notes)

    elif library_notes:
        if db.get_loan_notes(loan_id):
            loans_notes = eval(db.get_loan_notes(loan_id))
        else:
            loans_notes = {}

        loans_notes[time.strftime("%Y-%m-%d %H:%M:%S")] = str(library_notes)
        db.update_loan_notes(loan_id, loans_notes)

    loans_notes = db.get_loan_notes(loan_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a> &gt; <a class="navtrail" ' \
                              'href="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1">Circulation Management' \
                              '</a> ' % (CFG_SITE_URL, CFG_SITE_URL)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    referer = req.headers_in.get('referer')

    body = bibcirculation_templates.tmpl_get_loans_notes(loans_notes=loans_notes,
                                                         loan_id=loan_id,
                                                         referer=referer, back=back,
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

    @type name:     string.
    @type email:    string.
    @type phone:    string.
    @type address:  string.
    @type mailbox:  string.
    @type notes:    string.
    """

    infos = []

    is_borrower = db.is_borrower(email)

    if is_borrower != 0:
        infos.append("There is already a borrower using "\
                     "the following email: \n\n <strong>%s</strong> \n\n"\
                     "Please go back to previous page and give a different email. " % email)

    tup_infos = (name, email, phone, address, mailbox, notes)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_add_new_borrower_step2(tup_infos=tup_infos,
                                                                infos=infos,
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

    @type tup_infos:   tuple.
    @param tup_infos:  tuple containing borrower information.
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

    @param borrower_id:  identify the borrower. It is also the primary key of
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


def get_item_loans_notes(req, loan_id, add_notes, new_note, ln=CFG_SITE_LANG):
    """
    Get loan's notes.

    @param loan_id:  identify a loan. It is the primery key of the table
              crcLOAN.

    @param recid:  identify the record. It is also the primary key of
            the table bibrec.

    @param borrower_id:  identify the borrower. It is also the primary key of
                  the table crcBORROWER.

    @param add_notes:  display the textarea where will be written a new notes.

    @param new_notes:  note who will be added to the others library's notes.
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

    body = bibcirculation_templates.tmpl_get_loans_notes(loans_notes=loans_notes,
                                                         loan_id=loan_id,
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
                                 'Service=AWSECommerceService&AWSAccessKeyId=' \
                                 + CFG_BIBCIRCULATION_AMAZON_ACCESS_KEY + \
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
                                   '?Service=AWSECommerceService&AWSAccessKeyId=' \
                                   + CFG_BIBCIRCULATION_AMAZON_ACCESS_KEY + \
                                   '&Operation=ItemSearch&Condition=All&' \
                                   'ResponseGroup=Images&SearchIndex=Books&' \
                                   'Keywords=' + isbn)

        xml_img = minidom.parse(cover_xml)

        try:
            get_cover_link = xml_img.getElementsByTagName('MediumImage')
            cover_link = get_cover_link.item(0).firstChild.firstChild.data
            book_info.append(str(cover_link))
        except AttributeError:
            cover_link = CFG_SITE_URL + "/img/book_cover_placeholder.gif"
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

    return page(title="Add new library",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def add_new_library_step2(req, name, email, phone, address,
                           lib_type, notes, ln=CFG_SITE_LANG):

    """
    Add a new Library.
    """

    tup_infos = (name, email, phone, address, lib_type, notes)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_add_new_library_step2(tup_infos=tup_infos,
                                                                ln=ln)

    return page(title="Add new library",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def add_new_library_step3(req, tup_infos, ln=CFG_SITE_LANG):
    """
    Add a new Library.
    """
    (name, email, phone, address, lib_type, notes) = tup_infos
    db.add_new_library(name, email, phone, address, lib_type, notes)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_add_new_library_step3(ln=ln)

    return page(title="Add new library",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_library_info_step1(req, ln=CFG_SITE_LANG):
    """
    Update the library's information.
    """
    infos = []

    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_update_library_info_step1(infos=infos,
                                                                   ln=ln)

    return page(title="Update library information",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_library_info_step2(req, column, string, ln=CFG_SITE_LANG):
    """
    Update the library's information.
    """
    if not string:
        infos = []
        infos.append("Empty string. Please try again.")
        body = bibcirculation_templates.tmpl_update_library_info_step1(infos=infos,
                                                                       ln=ln)
    elif string == '*':
        result = db.get_all_libraries()
        body = bibcirculation_templates.tmpl_update_library_info_step2(result=result,
                                                                       ln=ln)
    else:
        if column == 'name':
            result = db.search_library_by_name(string)
        else:
            result = db.search_library_by_email(string)

        body = bibcirculation_templates.tmpl_update_library_info_step2(result=result, ln=ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)


    return page(title="Update library information",
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

    return page(title="Update library information",
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

    return page(title="Update library information",
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

    return page(title="Update library information",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def new_book_step1(req,ln):
    """
    Add a new book.
    """
    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_new_book_step1(ln)

    return page(title="Order New Book",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def new_book_step2(req,ln):
    """
    Add a new book.
    """
    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_new_book_step2(ln)

    return page(title="Order New Book",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def add_new_copy_step1(req):
    """
    Add a new copy.
    """

    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_add_new_copy_step1()

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

    infos = []
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
                                                            infos=infos,
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

    infos = []

    if db.barcode_in_use(barcode):
        infos.append("The given barcode <strong>%s</strong> is already in use." % barcode)
        result = db.get_item_copies_details(recid)
        libraries = db.get_libraries()
        title="Add new copy - III"
        body = bibcirculation_templates.tmpl_add_new_copy_step3(recid=recid,
                                                                result=result,
                                                                libraries=libraries,
                                                                infos=infos,
                                                                ln=ln)
    elif not barcode:
        infos.append("The given barcode is empty.")
        result = db.get_item_copies_details(recid)
        libraries = db.get_libraries()
        title="Add new copy - III"
        body = bibcirculation_templates.tmpl_add_new_copy_step3(recid=recid,
                                                                result=result,
                                                                libraries=libraries,
                                                                infos=infos,
                                                                ln=ln)


    else:
        library_name = db.get_library_name(library)
        tup_infos = (barcode, library, library_name, location, collection, description,
                     loan_period, status, recid)
        title="Add new copy - IV"
        body = bibcirculation_templates.tmpl_add_new_copy_step4(tup_infos=tup_infos,
                                                                ln=ln)

    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
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

    return page(title="Update item information",
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

    return page(title="Update item information",
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

    return page(title="Update item information",
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

    f = open("/tmp/lib","w")
    f.write(str(libraries)+'\n')
    f.close()

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

    return page(title="Update item information",
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

    return page(title="Update item information",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_item_info_step6(req, tup_infos, ln=CFG_SITE_LANG):
    """
    Update the item's information.
    """

    infos = []

    # tuple containing information for the update process.
    (barcode, library_id, _library_name, location, collection,
     description, loan_period, status, recid) = tup_infos

    is_on_loan = db.is_on_loan(barcode)
    is_requested = db.is_requested(barcode)

    # if item on loan and new status is available,
    # item has to be returned.
    if is_on_loan and status == 'available':
        #borrower_id = db.get_borrower_id(barcode)
        #borrower_name = db.get_borrower_name(borrower_id)

        db.update_item_status('available', barcode)
        db.update_loan_info(datetime.date.today(), 'returned', barcode)

    # if item requested and new status is available
    # request has to be cancelled.
    elif is_requested and status == 'available':
        for i in range(len(is_requested)):
            db.update_loan_request_status(is_requested[i][0],'cancelled')

    # update item information.
    db.update_item_info(barcode, library_id,
                        collection, location, description,
                        loan_period, status)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    infos.append("Item <strong>[%s]</strong> updated with success." % barcode)
    copies = db.get_item_copies_details(recid)
    requests = db.get_item_requests(recid)
    loans = db.get_item_loans(recid)
    req_hist_overview = db.get_item_requests_historical_overview(recid)
    loans_hist_overview = db.get_item_loans_historical_overview(recid)


    body = bibcirculation_templates.tmpl_get_item_details(recid=recid,
                                                          copies=copies,
                                                          requests=requests,
                                                          loans=loans,
                                                          req_hist_overview = req_hist_overview,
                                                          loans_hist_overview = loans_hist_overview,
                                                          infos=infos,
                                                          ln=ln)

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

    infos = []

    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_search_library_step1(infos=infos,
                                                              ln=ln)

    return page(title="Search library",
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

    if not string:
        infos = []
        infos.append("Emptry string. Please try again.")
        body = bibcirculation_templates.tmpl_search_library_step1(infos=infos,
                                                                  ln=ln)
    elif string == '*':
        result = db.get_all_libraries()
        body = bibcirculation_templates.tmpl_search_library_step2(result=result,
                                                                  ln=ln)
    else:
        if column == 'name':
            result = db.search_library_by_name(string)
        else:
            result = db.search_library_by_email(string)

        body = bibcirculation_templates.tmpl_search_library_step2(result=result,
                                                                  ln=ln)


    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a> &gt; <a class="navtrail" ' \
                              'href="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1">Circulation Management' \
                              '</a> ' % (CFG_SITE_URL, CFG_SITE_URL)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    return page(title="Search library",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def get_library_notes(req, library_id, delete_key,
                      library_notes, ln=CFG_SITE_LANG):
    """
    Retrieve notes related with a library.

    library_id - identify the library. It is also the primary key of
                 the table crcLIBRARY.
    """

    if delete_key and library_id:
        lib_notes = eval(db.get_library_notes(library_id))
        del lib_notes[delete_key]
        db.update_library_notes(library_id, lib_notes)

    elif library_notes:
        if db.get_library_notes(library_id):
            lib_notes = eval(db.get_library_notes(library_id))
        else:
            lib_notes = {}

        lib_notes[time.strftime("%Y-%m-%d %H:%M:%S")] = str(library_notes)
        db.update_library_notes(library_id, lib_notes)

    lib_notes = db.get_library_notes(library_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a> &gt; <a class="navtrail" ' \
                              'href="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1">Circulation Management' \
                              '</a> ' % (CFG_SITE_URL, CFG_SITE_URL)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_library_notes(library_notes=lib_notes,
                                                       library_id=library_id,
                                                       ln=ln)
    return page(title="Library notes",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def change_due_date_step1(req, loan_id, borrower_id, ln=CFG_SITE_LANG):
    """
    Change the due date of a loan, step1.

    loan_id: identify a loan. It is the primery key of the table
             crcLOAN.

    borrower_id: identify the borrower. It is also the primary key of
                 the table crcBORROWER.
    """

    loan_details = db.get_loan_infos(loan_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_change_due_date_step1(loan_details=loan_details,
                                                               loan_id=loan_id,
                                                               borrower_id=borrower_id,
                                                               ln=ln)
    return page(title="Change due date",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def change_due_date_step2(req, due_date, loan_id, borrower_id, ln=CFG_SITE_LANG):
    """
    Change the due date of a loan, step2.

    due_date: new due date.

    loan_id: identify a loan. It is the primery key of the table
             crcLOAN.

    borrower_id: identify the borrower. It is also the primary key of
                 the table crcBORROWER.
    """

    db.update_due_date(loan_id, due_date)
    due_date = db.get_loan_due_date(loan_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_change_due_date_step2(due_date=due_date,
                                                               borrower_id=borrower_id,
                                                               ln=ln)
    return page(title="Change due date",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def claim_book_return(req, borrower_id, recid, loan_id,
                      template, ln=CFG_SITE_LANG):
    """
    Claim the return of an item.

    borrower_id: identify the borrower. It is also the primary key of
                  the table crcBORROWER.

    recid: identify the record. It is also the primary key of
           the table bibrec.

    template: letter template.
    """

    body = generate_email_body(load_template(template), loan_id)

    email = db.get_borrower_email(borrower_id)
    subject = "%s" % (book_title_from_MARC(int(recid)))

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_borrower_notification(email=email,
                                                               subject=subject,
                                                               template=body,
                                                               borrower_id=borrower_id,
                                                               ln=ln)

    return page(title="Claim return",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def create_new_loan_step1(req, borrower_id, ln=CFG_SITE_LANG):
    """
    Create a new loan from the borrower's page, step1.

    borrower_id: identify the borrower. It is also the primary key of
                  the table crcBORROWER.
    """

    infos = []

    borrower = db.get_borrower_details(borrower_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)


    body = bibcirculation_templates.tmpl_create_new_loan_step1(borrower=borrower,
                                                               infos=infos,
                                                               ln=ln)

    return page(title="New loan",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def create_new_loan_step2(req, borrower_id, barcode, notes, ln=CFG_SITE_LANG):
    """
    Create a new loan from the borrower's page, step2.

    borrower_id: identify the borrower. It is also the primary key of
                  the table crcBORROWER.

    barcode: identify the item. It is the primary key of the table
             crcITEM.

    notes: notes about the new loan.
    """
    #borrower_info = db.get_borrower_data(borrower_id)

    has_recid = db.get_id_bibrec(barcode)
    loan_id = db.is_item_on_loan(barcode)

    if notes:
        notes_format = '[' + time.ctime() + '] ' + notes + '\n'
    else:
        notes_format = ''

    infos = []

    if has_recid is None:
        infos.append('"%s" > Unknown barcode. Please try again.' % barcode)
        borrower = db.get_borrower_details(borrower_id)
        title="New loan"
        body = bibcirculation_templates.tmpl_create_new_loan_step1(borrower=borrower,
                                                                   infos=infos,
                                                                   ln=ln)

    elif loan_id:
        infos.append('The item with the barcode "%s" is on loan.' % barcode)
        borrower = db.get_borrower_details(borrower_id)
        title="New loan"
        body = bibcirculation_templates.tmpl_create_new_loan_step1(borrower=borrower,
                                                                   infos=infos,
                                                                   ln=ln)

    else:
        loaned_on = datetime.date.today()
        due_date = renew_loan_for_X_days(barcode)
        db.new_loan(borrower_id, has_recid, barcode,
                    loaned_on, due_date, 'on loan', 'normal', notes_format)

        result = db.get_all_loans(20)
        title = "Current loans"
        infos.append('A new loan has been registered with success.')
        body = bibcirculation_templates.tmpl_all_loans(result=result,
                                                       infos=infos,
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

def create_new_request_step1(req, borrower_id, p="", f="", search=None, ln=CFG_SITE_LANG):
    """
    Create a new request from the borrower's page, step1.

    borrower_id: identify the borrower. It is also the primary key of
                  the table crcBORROWER.

    p: search pattern.

    f: field

    search: search an item.
    """
    infos = []
    borrower = db.get_borrower_details(borrower_id)

    if search and f == 'barcode':
        has_recid = db.get_recid(p)

        if has_recid is None:
            infos.append('The barcode <strong>%s</strong> does not exist on BibCirculation database.' % p)
            result = ''
        else:
            result = has_recid

    elif search:
        result = perform_request_search(cc="Books", sc="1", p=p, f=f)

    else:
        result = ''

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_create_new_request_step1(borrower=borrower,
                                                                  infos=infos,
                                                                  result=result,
                                                                  p=p,
                                                                  f=f,
                                                                  ln=ln)

    return page(title="New request",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def create_new_request_step2(req, recid, borrower_id, ln=CFG_SITE_LANG):
    """
    Create a new request from the borrower's page, step2.

    recid: identify the record. It is also the primary key of
           the table bibrec.

    borrower_id: identify the borrower. It is also the primary key of
            the table crcBORROWER.
    """

    holdings_information = db.get_holdings_information(recid)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    user_info = db.get_borrower_details(borrower_id)

    body = bibcirculation_templates.tmpl_create_new_request_step2(user_info = user_info,
                                                                  holdings_information = holdings_information,
                                                                  recid=recid,
                                                                  ln=ln)

    return page(title="New request",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def create_new_request_step3(req, borrower_id, barcode, recid, ln=CFG_SITE_LANG):
    """
    Create a new request from the borrower's page, step3.

    borrower_id: identify the borrower. It is also the primary key of
                  the table crcBORROWER.

    barcode: identify the item. It is the primary key of the table
             crcITEM.

    recid: identify the record. It is also the primary key of
           the table bibrec.
    """

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    item_info = db.get_item_info(barcode)

    if item_info[6] == 'Not for loan':
        body = bibcirculation_templates.tmpl_book_not_for_loan(ln=ln)
    else:
        body = bibcirculation_templates.tmpl_create_new_request_step3(borrower_id=borrower_id,
                                                                  barcode=barcode,
                                                                  recid=recid,
                                                                  ln=ln)

    return page(title="New request",
                uid=id_user,
                req=req,
                body=body,
                metaheaderadd = "<link rel=\"stylesheet\" href=\"%s/img/jquery-ui.css\" type=\"text/css\" />" % CFG_SITE_URL,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def create_new_request_step4(req, period_from, period_to, barcode,
                             borrower_id, recid, ln=CFG_SITE_LANG):
    """
    Create a new request from the borrower's page, step4.

    period_from: begining of the period of interest.

    period_to: end of the period of interest.

    barcode: identify the item. It is the primary key of the table
             crcITEM.

    borrower_id: identify the borrower. It is also the primary key of
                  the table crcBORROWER.

    recid: identify the record. It is also the primary key of
           the table bibrec.
    """

    nb_requests = db.get_number_requests_per_copy(barcode)
    is_on_loan = db.is_item_on_loan(barcode)

    if nb_requests == 0 and is_on_loan is not None:
        status = 'waiting'
    elif nb_requests == 0 and is_on_loan is None:
        status = 'pending'
    else:
        status = 'waiting'

    db.new_hold_request(borrower_id, recid, barcode,
                        period_from, period_to,
                        status)

    db.update_item_status('requested', barcode)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)


    body = bibcirculation_templates.tmpl_create_new_request_step4(ln=ln)

    return page(title="New request",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def place_new_request_step1(req, barcode, recid, key, string, ln=CFG_SITE_LANG):
    """
    Place a new request from the item's page, step1.

    barcode: identify the item. It is the primary key of the table
             crcITEM.

    recid: identify the record. It is also the primary key of
           the table bibrec.

    key: search field.

    string: search pattern.
    """

    recid = db.get_id_bibrec(barcode)
    infos = []

    if key and not string:
        infos.append('Empty string. Please, try again.')
        body = bibcirculation_templates.tmpl_place_new_request_step1(result=None,
                                                                     key=key,
                                                                     string=string,
                                                                     barcode=barcode,
                                                                     recid=recid,
                                                                     infos=infos,
                                                                     ln=ln)

        navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

        id_user = getUid(req)
        (auth_code, auth_message) = is_adminuser(req)
        if auth_code != 0:
            return mustloginpage(req, auth_message)

        return page(title="New request",
                    uid=id_user,
                    req=req,
                    body=body,
                    navtrail=navtrail_previous_links,
                    lastupdated=__lastupdated__)


    list_infos = []

    if CFG_CERN_SITE == 1:
        if key =='ccid' and string:
            from invenio.bibcirculation_cern_ldap import get_user_info_from_ldap
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

        elif key =='name' and string:
            result = db.get_borrower_data_by_name(string)

            for (borrower_id, name, email, phone, address, mailbox) in result:
                tup = (borrower_id, name, email, phone, address, mailbox)
                list_infos.append(tup)

        elif key =='email' and string:
            result = db.get_borrower_data_by_email(string)

            for (borrower_id, name, email, phone, address, mailbox) in result:
                tup = (borrower_id, name, email, phone, address, mailbox)
                list_infos.append(tup)
        else:
            result = list_infos

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

    if len(result) == 1:
        return place_new_request_step2(req, barcode, recid, tup, ln)
    else:
        body = bibcirculation_templates.tmpl_place_new_request_step1(result=list_infos,
                                                                     key=key,
                                                                     string=string,
                                                                     barcode=barcode,
                                                                     recid=recid,
                                                                     infos=infos,
                                                                     ln=ln)


    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)



    return page(title="New request",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)




def place_new_request_step2(req, barcode, recid, user_info, ln=CFG_SITE_LANG):
    """
    Place a new request from the item's page, step2.

    @type barcode:     string.
    @param barcode:    identify the item. It is the primary key of the table
                       crcITEM.

    @type recid:       integer.
    @param recid:      identify the record. It is also the primary key of
                       the table bibrec.

    @type user_info:   list.
    @param user_info:  information of the user/borrower who was selected.

    """

    infos = []

    body = bibcirculation_templates.tmpl_place_new_request_step2(barcode=barcode,
                                                                 recid=recid,
                                                                 user_info=user_info,
                                                                 infos=infos,
                                                                 ln=ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    return page(title="New request",
                uid=id_user,
                req=req,
                body=body,
                metaheaderadd = "<link rel=\"stylesheet\" href=\"%s/img/jquery-ui.css\" type=\"text/css\" />" % CFG_SITE_URL,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def place_new_request_step3(req, barcode, recid, user_info,
                            period_from, period_to, ln=CFG_SITE_LANG):
    """
    Place a new request from the item's page, step3.

    @type barcode:  string.
    @param barcode: identify the item. It is the primary key of the table
                    crcITEM.

    @type recid:    integer.
    @param recid:   identify the record. It is also the primary key of
                    the table bibrec.

    @return:        new request.
    """

    (_ccid, name, email, phone, address, mailbox) = user_info

    # validate the period of interest given by the admin
    if validate_date_format(period_from) is False:
        infos = []
        infos.append("The period of interest <strong>'From': %s</strong>" \
                     " is not a valid date or date format" % period_from)

        body = bibcirculation_templates.tmpl_place_new_request_step2(barcode=barcode,
                                                                     recid=recid,
                                                                     user_info=user_info,
                                                                     infos=infos,
                                                                     ln=ln)

        navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

        id_user = getUid(req)
        (auth_code, auth_message) = is_adminuser(req)
        if auth_code != 0:
            return mustloginpage(req, auth_message)

        return page(title="New request",
                    uid=id_user,
                    req=req,
                    body=body,
                    navtrail=navtrail_previous_links,
                    lastupdated=__lastupdated__)

    elif validate_date_format(period_to) is False:
        infos = []
        infos.append("The period of interest <strong>'To': %s</strong>" \
                     " is not a valid date or date format" % period_to)

        body = bibcirculation_templates.tmpl_place_new_request_step2(barcode=barcode,
                                                                     recid=recid,
                                                                     user_info=user_info,
                                                                     infos=infos,
                                                                     ln=ln)

        navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

        id_user = getUid(req)
        (auth_code, auth_message) = is_adminuser(req)
        if auth_code != 0:
            return mustloginpage(req, auth_message)

        return page(title="New request",
                    uid=id_user,
                    req=req,
                    body=body,
                    navtrail=navtrail_previous_links,
                    lastupdated=__lastupdated__)


    # Register request
    nb_requests = db.get_number_requests_per_copy(barcode)
    is_on_loan = db.is_item_on_loan(barcode)

    if nb_requests == 0 and is_on_loan is not None:
        status = 'waiting'
    elif nb_requests == 0 and is_on_loan is None:
        status = 'pending'
    else:
        status = 'waiting'

    is_borrower = db.is_borrower(email)

    if is_borrower != 0:
        db.new_hold_request(is_borrower, recid, barcode,
                            period_from, period_to, status)
        db.update_item_status('requested', barcode)

    else:
        db.new_borrower(name, email, phone, address, mailbox, '')
        is_borrower = db.is_borrower(email)

        db.new_hold_request(is_borrower, recid, barcode,
                            period_from, period_to, status)
        db.update_item_status('requested', barcode)


    body = bibcirculation_templates.tmpl_place_new_request_step3(ln=ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    return page(title="New request",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def place_new_loan_step1(req, barcode, recid, key, string, ln=CFG_SITE_LANG):
    """
    Place a new loan from the item's page, step1.

    @type barcode:  string.
    @param barcode: identify the item. It is the primary key of the table
                    crcITEM.

    @type recid:    integer.
    @param recid:   identify the record. It is also the primary key of
                    the table bibrec.

    @type key:      string.
    @param key:     search field.

    @type string:   string.
    @param string:  search pattern.

    @return:        list of users/borrowers.
    """

    recid = db.get_id_bibrec(barcode)
    infos = []

    if key and not string:
        infos.append('Empty string. Please, try again.')
        body = bibcirculation_templates.tmpl_place_new_loan_step1(result=None,
                                                                  key=key,
                                                                  string=string,
                                                                  barcode=barcode,
                                                                  recid=recid,
                                                                  infos=infos,
                                                                  ln=ln)

        navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

        id_user = getUid(req)
        (auth_code, auth_message) = is_adminuser(req)
        if auth_code != 0:
            return mustloginpage(req, auth_message)

        return page(title="New loan",
                    uid=id_user,
                    req=req,
                    body=body,
                    navtrail=navtrail_previous_links,
                    lastupdated=__lastupdated__)
    list_infos = []

    if CFG_CERN_SITE == 1:
        if key =='ccid' and string:
            from invenio.bibcirculation_cern_ldap import get_user_info_from_ldap
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

        elif key =='name' and string:
            result = db.get_borrower_data_by_name(string)

            for (borrower_id, name, email, phone, address, mailbox) in result:
                tup = (borrower_id, name, email, phone, address, mailbox)
                list_infos.append(tup)

        elif key =='email' and string:
            result = db.get_borrower_data_by_email(string)

            for (borrower_id, name, email, phone, address, mailbox) in result:
                tup = (borrower_id, name, email, phone, address, mailbox)
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

    body = bibcirculation_templates.tmpl_place_new_loan_step1(result=list_infos,
                                                              key=key,
                                                              string=string,
                                                              barcode=barcode,
                                                              recid=recid,
                                                              infos=infos,
                                                              ln=ln)


    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)



    return page(title="New loan",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def place_new_loan_step2(req, barcode, recid, user_info, ln=CFG_SITE_LANG):
    """
    Place a new loan from the item's page, step2.

    @type barcode:    string.
    @param barcode:   identify the item. It is the primary key of the table
                      crcITEM.

    @type recid:      integer.
    @param recid:     identify the record. It is also the primary key of
                      the table bibrec.

    @type user_info:  list.
    @param user_info: information of the user/borrower who was selected.
    """

    body = bibcirculation_templates.tmpl_place_new_loan_step2(barcode=barcode,
                                                              recid=recid,
                                                              user_info=user_info,
                                                              ln=ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    return page(title="New loan",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def place_new_loan_step3(req, barcode, recid, _ccid, name, email, phone,
                         address, mailbox, due_date, notes, ln=CFG_SITE_LANG):
    """
    Place a new loan from the item's page, step3.

    @type barcode:  string.
    @param barcode: identify the item. It is the primary key of the table
                    crcITEM.

    @type recid:    integer.
    @param recid:   identify the record. It is also the primary key of
                    the table bibrec.

    @type name:     string.
    @type email:    string.
    @type phone:    string.
    @type address:  string.
    @type mailbos:  string.
    @type due_date: string.
    @type notes:    string.

    @return:        new loan.
    """

    infos = []

    if notes:
        notes_format = '[' + time.ctime() + '] ' +  notes +  '\n'
    else:
        notes_format = ''

    loaned_on = datetime.date.today()
    is_borrower = db.is_borrower(email)
    borrower_info = db.get_borrower_data(is_borrower)

    if db.is_on_loan(barcode):
        infos.append("Item with barcode <strong>%s</strong> is already on loan." % barcode)

        copies = db.get_item_copies_details(recid)
        requests = db.get_item_requests(recid)
        loans = db.get_item_loans(recid)

        req_hist_overview = db.get_item_requests_historical_overview(recid)
        loans_hist_overview = db.get_item_loans_historical_overview(recid)

        title = "Item details"
        body = bibcirculation_templates.tmpl_get_item_details(recid=recid,
                                                              copies=copies,
                                                              requests=requests,
                                                              loans=loans,
                                                              req_hist_overview = req_hist_overview,
                                                              loans_hist_overview = loans_hist_overview,
                                                              infos=infos,
                                                              ln=ln)

    elif is_borrower != 0:
        db.new_loan(is_borrower, recid, barcode,
                    loaned_on, due_date, 'on loan',
                    'normal', notes_format)

        db.update_item_status('on loan', barcode)

        title = "New loan"
        body = bibcirculation_templates.tmpl_register_new_loan(borrower_info=borrower_info,
                                                               recid=recid,
                                                               ln=ln)

    else:
        db.new_borrower(name, email, phone, address, mailbox, '')
        is_borrower = db.is_borrower(email)

        db.new_loan(is_borrower, recid, barcode,
                    loaned_on, due_date, 'on loan',
                    'normal', notes_format)

        db.update_item_status('on loan', barcode)

        title = "New loan"
        body = bibcirculation_templates.tmpl_register_new_loan(borrower_info=borrower_info,
                                                               recid=recid,
                                                               ln=ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a> &gt; <a class="navtrail" ' \
                              'href="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1">Circulation Management' \
                              '</a> ' % (CFG_SITE_URL, CFG_SITE_URL)

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


def order_new_copy_step1(req, recid, ln):
    """
    Order a new copy. Step 1.
    """

    list_of_vendors = db.get_list_of_vendors()
    libraries = db.get_libraries()

    body = bibcirculation_templates.tmpl_order_new_copy_step1(recid=recid,
                                                              list_of_vendors=list_of_vendors,
                                                              libraries=libraries,
                                                              ln=ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    return page(title="Order new copy",
                uid=id_user,
                req=req,
                metaheaderadd = "<link rel=\"stylesheet\" href=\"%s/img/jquery-ui.css\" type=\"text/css\" />" % CFG_SITE_URL,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def order_new_copy_step2 (req, recid, barcode, vendor_id, cost, currency,
                          status, order_date, expected_date, library_id,
                          notes, ln):
    """
    Order a new copy. Step 2.
    """

    order_info = (recid, barcode, vendor_id, cost, currency,
                  status, order_date, expected_date, library_id,
                  notes)

    body = bibcirculation_templates.tmpl_order_new_copy_step2(order_info=order_info, ln=ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    return page(title="Order new copy",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def order_new_copy_step3(req, order_info, ln):
    """
    Order a new copy. Step 3.
    """

    (recid, _barcode, vendor_id, cost, currency, status,
     order_date, expected_date, _library_id, notes) = order_info

    cost_format = cost + ' ' + currency

    purchase_notes = {time.strftime("%Y-%m-%d %H:%M:%S"): notes}


    db.order_new_copy(recid, vendor_id, order_date, cost_format,
                      status, str(purchase_notes), expected_date)

    #db.add_new_copy(barcode, recid, library_id, '', '',
    #                'expected: %s' % expected_date, '', status)

    #body = list_ordered_books(req,ln) #bibcirculation_templates.tmpl_order_new_copy_step3(ln=ln)

    #navtrail_previous_links = '<a class="navtrail" ' \
    #                          'href="%s/help/admin">Admin Area' \
    #                          '</a>' % (CFG_SITE_URL,)

    #id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    #return page(title="Order new copy",
    #            uid=id_user,
    #            req=req,
    #            body=body,
    #            navtrail=navtrail_previous_links,
    #            lastupdated=__lastupdated__)

    return get_item_details(req, recid, ln)


def list_ordered_books(req, ln):
    """
    Return the list with all ordered books.
    """

    ordered_books = db.get_ordered_books()

    body = bibcirculation_templates.tmpl_ordered_books(ordered_books=ordered_books, ln=ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    return page(title="List of ordered books",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def get_purchase_notes(req, purchase_id, delete_key, library_notes, ln=CFG_SITE_LANG):
    """
    Retrieve notes related with a library.

    purchase_id - identify the purchase. It is also the primary key of
                 the table crcPURCHASE.

    @param add_notes:  display the textarea where will be written a new notes.

    @param new_notes:  note who will be added to the others library's notes.
    """

    if delete_key and purchase_id:
        purchase_notes = eval(db.get_purchase_notes(purchase_id))
        del purchase_notes[delete_key]
        db.update_purchase_notes(purchase_id, purchase_notes)

    elif library_notes:
        if db.get_purchase_notes(purchase_id):
            purchase_notes = eval(db.get_purchase_notes(purchase_id))
        else:
            purchase_notes = {}

        purchase_notes[time.strftime("%Y-%m-%d %H:%M:%S")] = str(library_notes)
        db.update_purchase_notes(purchase_id, purchase_notes)

    purchase_notes = db.get_purchase_notes(purchase_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_purchase_notes(purchase_notes=purchase_notes,
                                                        purchase_id=purchase_id,
                                                        ln=ln)
    return page(title="Purchase notes",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def register_ill_request_step0(req, recid, key, string, ln=CFG_SITE_LANG):
    """
    Place a new request from the item's page, step1.

    barcode: identify the item. It is the primary key of the table
             crcITEM.

    recid: identify the record. It is also the primary key of
           the table bibrec.

    key: search field.

    string: search pattern.
    """
    infos = []

    if key and not string:
        infos.append("Empty string. Please try again.")
        body = bibcirculation_templates.tmpl_register_ill_request_step0(result=None,
                                                                        infos=infos,
                                                                        key=key,
                                                                        string=string,
                                                                        recid=recid,
                                                                        ln=ln)


        navtrail_previous_links = '<a class="navtrail" ' \
                                  'href="%s/help/admin">Admin Area' \
                                  '</a>' % (CFG_SITE_URL,)

        id_user = getUid(req)
        (auth_code, auth_message) = is_adminuser(req)
        if auth_code != 0:
            return mustloginpage(req, auth_message)


        return page(title="Register ILL request",
                    uid=id_user,
                    req=req,
                    body=body,
                    navtrail=navtrail_previous_links,
                    lastupdated=__lastupdated__)

    list_infos = []

    if CFG_CERN_SITE == 1:
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


    body = bibcirculation_templates.tmpl_register_ill_request_step0(result=list_infos,
                                                                    infos=infos,
                                                                    key=key,
                                                                    string=string,
                                                                    recid=recid,
                                                                    ln=ln)


    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)


    return page(title="Register ILL request",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def register_ill_request_step1(req, recid, user_info, ln=CFG_SITE_LANG):
    """
    Register a new ILL request. Step 1.
    """

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_register_ill_request_step1(recid=recid,
                                                                    user_info=user_info,
                                                                    ln=ln)


    return page(title="Register ILL request",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def register_ill_request_step2(req, recid, user_info, period_of_interest_from,
                               period_of_interest_to, notes, only_edition,
                               ln=CFG_SITE_LANG):
    """
    """

    request_info = (recid, period_of_interest_from, period_of_interest_to,
                    notes, only_edition)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_register_ill_request_step2(user_info=user_info,
                                                                    request_info=request_info,
                                                                    ln=ln)


    return page(title="Register ILL request",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def register_ill_request_step3(req, borrower_id, request_info, ln=CFG_SITE_LANG):
    """
    """

    (recid, period_of_interest_from, period_of_interest_to,
     notes, only_edition) = request_info

    book_info = {'recid': recid}

    if notes:
        library_notes = {}
        library_notes[time.strftime("%Y-%m-%d %H:%M:%S")] = str(notes)
    else:
        library_notes = {}

    db.ill_register_request_on_desk(borrower_id, book_info, period_of_interest_from,
                                    period_of_interest_to, 'pending', str(library_notes),
                                    only_edition or 'No', 'book')


    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_register_ill_request_step3(ln=ln)


    return page(title="Register ILL request",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def list_ill_request(req, status, ln=CFG_SITE_LANG):
    """
    """

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    ill_req = db.get_ill_requests(status)

    body = bibcirculation_templates.tmpl_list_ill_request(ill_req=ill_req, ln=ln)


    return page(title="List of ILL requests",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def ill_request_details_step1(req, delete_key, ill_request_id, new_status, ln=CFG_SITE_LANG):
    """
    """

    if delete_key and ill_request_id:
        library_notes = eval(db.get_ill_request_notes(ill_request_id))
        del library_notes[delete_key]
        db.update_ill_request_notes(ill_request_id, library_notes)

    if new_status:
        db.update_ill_request_status(ill_request_id,new_status)

    ill_request_borrower_details = db.get_ill_request_borrower_details(ill_request_id)

    ill_request_details=db.get_ill_request_details(ill_request_id)

    libraries = db.get_external_libraries()

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_ill_request_details_step1(ill_request_id=ill_request_id,
                                                                   ill_request_details=ill_request_details,
                                                                   libraries=libraries,
                                                                   ill_request_borrower_details=ill_request_borrower_details,
                                                                   ln=ln)

    return page(title="ILL request details",
                uid=id_user,
                req=req,
                metaheaderadd = "<link rel=\"stylesheet\" href=\"%s/img/jquery-ui.css\" type=\"text/css\" />" % CFG_SITE_URL,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def ill_request_details_step2(req, delete_key, ill_request_id, new_status, library_id, request_date, expected_date, arrival_date,
                              due_date, return_date, cost, currency, barcode, library_notes, ln=CFG_SITE_LANG):
    """
    """

    #id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    if delete_key and ill_request_id:
        library_previous_notes = eval(db.get_ill_request_notes(ill_request_id))
        del library_previous_notes[delete_key]
        db.update_ill_request_notes(ill_request_id, library_previous_notes)

    #navtrail_previous_links = '<a class="navtrail" ' \
    #                          'href="%s/help/admin">Admin Area' \
    #                          '</a>' % (CFG_SITE_URL,)

    cost_format = None
    if cost:
        cost_format = cost + ' ' + currency

    if db.get_ill_request_notes(ill_request_id):
        library_previous_notes = eval(db.get_ill_request_notes(ill_request_id))
    else:
        library_previous_notes = {}

    if library_notes:
        library_previous_notes[time.strftime("%Y-%m-%d %H:%M:%S")] = str(library_notes)

    if new_status == 'on loan':
        borrower_id = db.get_ill_borrower(ill_request_id)
        loaned_on = datetime.date.today()
        db.new_loan(borrower_id, '0', barcode, loaned_on, due_date, 'on loan', 'ill','')

    elif new_status == 'returned':
        borrower_id = db.get_ill_borrower(ill_request_id)
        barcode = db.get_ill_barcode(ill_request_id)
        db.update_ill_loan_status(borrower_id, barcode, return_date, 'ill')

    db.update_ill_request(ill_request_id, library_id, request_date, expected_date,
                          arrival_date, due_date, return_date, new_status, cost_format, barcode,
                          str(library_previous_notes))

    return list_ill_request(req,new_status,ln)

    #body = bibcirculation_templates.tmpl_ill_request_details_step3(ln=ln)
    #return page(title="ILL request details",
    #            uid=id_user,
    #            req=req,
    #            body=body,
    #            navtrail=navtrail_previous_links,
    #            lastupdated=__lastupdated__)


def ordered_books_details_step1(req, purchase_id, delete_key, ln=CFG_SITE_LANG):
    """
    """

    if delete_key and purchase_id:
        purchase_notes = eval(db.get_purchase_notes(purchase_id))
        del purchase_notes[delete_key]
        db.update_purchase_notes(purchase_id, purchase_notes)

    list_of_vendors = db.get_list_of_vendors()
    order_details = db.get_order_details(purchase_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_ordered_book_details_step1(order_details=order_details,
                                                                    list_of_vendors=list_of_vendors,
                                                                    ln=ln)


    return page(title="Ordered book details",
                uid=id_user,
                req=req,
                metaheaderadd = "<link rel=\"stylesheet\" href=\"%s/img/jquery-ui.css\" type=\"text/css\" />" % CFG_SITE_URL,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def ordered_books_details_step2(req, purchase_id, recid, vendor_id,
                                cost, currency, status, order_date, expected_date,
                                purchase_notes, library_notes, ln=CFG_SITE_LANG):

    """
    """

    order_details = (purchase_id, recid, vendor_id,
                     cost, currency, status, order_date,
                     expected_date, purchase_notes,
                     library_notes)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_ordered_book_details_step2(order_details=order_details,
                                                                     ln=ln)


    return page(title="Ordered book details",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def ordered_books_details_step3(req, purchase_id, recid, vendor_id,
                                cost, currency, status, order_date, expected_date,
                                purchase_notes, library_notes, ln=CFG_SITE_LANG):
    """
    """

    purchase_notes = eval(purchase_notes)
    library_notes = library_notes.strip(' \n\t')
    if (len(library_notes)) is not 0:
        purchase_notes[time.strftime("%Y-%m-%d %H:%M:%S")] = str(library_notes)

    cost_format = cost + ' ' + currency

    db.uptade_purchase(purchase_id, recid, vendor_id, cost_format,
                       status, order_date, expected_date, str(purchase_notes))

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    #body = bibcirculation_templates.tmpl_ordered_book_details_step3(ln=ln)
    body = list_ordered_books(req,ln)


    return page(title="Ordered book details",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def add_new_vendor_step1(req, ln=CFG_SITE_LANG):
    """
    Add a new Vendor.
    """
    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_add_new_vendor_step1(ln=ln)

    return page(title="Add new vendor",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def add_new_vendor_step2(req, name, email, phone, address,
                         notes, ln=CFG_SITE_LANG):

    """
    Add a new Vendor.
    """

    tup_infos = (name, email, phone, address, notes)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_add_new_vendor_step2(tup_infos=tup_infos,
                                                              ln=ln)

    return page(title="Add new vendor",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def add_new_vendor_step3(req, tup_infos, ln=CFG_SITE_LANG):
    """
    Add a new Vendor.
    """
    (name, email, phone, address, notes) = tup_infos
    db.add_new_vendor(name, email, phone, address, notes)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_add_new_vendor_step3(ln=ln)

    return page(title="Add new vendor",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_vendor_info_step1(req, ln=CFG_SITE_LANG):
    """
    Update the vendor's information.
    """

    infos = []

    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_update_vendor_info_step1(infos=infos,
                                                                  ln=ln)

    return page(title="Update vendor information",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_vendor_info_step2(req, column, string, ln=CFG_SITE_LANG):
    """
    Update the vendor's information.
    """

    if not string:
        infos = []
        infos.append("Empty string. Please try again.")
        body = bibcirculation_templates.tmpl_update_vendor_info_step1(infos=infos, ln=ln)

    elif string == '*':
        result = db.get_all_vendors()
        body = bibcirculation_templates.tmpl_update_vendor_info_step2(result=result, ln=ln)

    else:
        if column == 'name':
            result = db.search_vendor_by_name(string)
        else:
            result = db.search_vendor_by_email(string)
        body = bibcirculation_templates.tmpl_update_vendor_info_step2(result=result, ln=ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_update_vendor_info_step2(result=result, ln=ln)

    return page(title="Update vendor information",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_vendor_info_step3(req, vendor_id, ln=CFG_SITE_LANG):
    """
    Update the library's information.

    vendor_id - identify the vendor. It is also the primary key of
                 the table crcVENDOR.

    """
    vendor_info = db.get_vendor_details(vendor_id)

    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_update_vendor_info_step3(vendor_info=vendor_info,
                                                                  ln=ln)

    return page(title="Update vendor information",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_vendor_info_step4(req, name, email, phone, address,
                             vendor_id, ln=CFG_SITE_LANG):
    """
    Update the vendor's information.
    """

    tup_infos = (vendor_id, name, email, phone, address)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_update_vendor_info_step4(tup_infos=tup_infos,
                                                                  ln=ln)

    return page(title="Update vendor information",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_vendor_info_step5(req, tup_infos, ln=CFG_SITE_LANG):
    """
    Update the library's information.
    """

    (vendor_id, name, email, phone, address) = tup_infos

    db.update_vendor_info(vendor_id, name, email, phone, address)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_update_vendor_info_step5(ln=ln)

    return page(title="Update library information - V",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def search_vendor_step1(req, ln=CFG_SITE_LANG):
    """
    Display the form where we can search a vendor (by name or email).
    """

    infos = []

    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_search_vendor_step1(infos=infos,
                                                             ln=ln)

    return page(title="Search vendor",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def search_vendor_step2(req, column, string, ln=CFG_SITE_LANG):
    """
    Search a vendor and return a list with all the possible results, using the
    parameters received from the previous step.

    column - identify the column, of the table crcVENDOR, who will be
             considered during the search. Can be 'name' or 'email'.

    str - string used for the search process.
    """

    if not string:
        infos = []
        infos.append("Empty string. Please try again.")
        body = bibcirculation_templates.tmpl_search_vendor_step1(infos=infos,
                                                             ln=ln)
    elif string == '*':
        result = db.get_all_vendors()
        body = bibcirculation_templates.tmpl_search_vendor_step2(result=result, ln=ln)

    else:
        if column == 'name':
            result = db.search_vendor_by_name(string)
        else:
            result = db.search_vendor_by_email(string)
        body = bibcirculation_templates.tmpl_search_vendor_step2(result=result, ln=ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    return page(title="Search vendor",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def get_vendor_details(req, vendor_id, ln=CFG_SITE_LANG):
    """
    Display the details of a vendor.

    @type vendor_id:    integer.
    @param vendor_id:   identify the vendor. It is also the primary key of
                        the table crcVENDOR.

    @return:            vendor details.
    """

    vendor_details = db.get_vendor_details(vendor_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_vendor_details(vendor_details=vendor_details,
                                                        ln=ln)

    return page(title="Vendor details",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def get_vendor_notes(req, vendor_id, add_notes, new_note, ln=CFG_SITE_LANG):
    """
    Retrieve notes related with a vendor.

    vendor_id - identify the vendor. It is also the primary key of
                the table crcVENDOR.

    @param add_notes:  display the textarea where will be written a new notes.

    @param new_notes:  note who will be added to the others vendor's notes.
    """

    if new_note:
        date = '[' + time.ctime() + '] '
        new_line = '\n'
        new_note = date + new_note + new_line
        db.add_new_vendor_note(new_note, vendor_id)

    vendor_notes = db.get_vendor_notes(vendor_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_vendor_notes(vendor_notes=vendor_notes,
                                                      vendor_id=vendor_id,
                                                      add_notes=add_notes,
                                                      ln=ln)
    return page(title="Vendor notes",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def register_ill_request_with_no_recid_step1(req, ln=CFG_SITE_LANG):
    """
    """
    infos = []

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_register_ill_request_with_no_recid_step1(infos=infos,ln=ln)

    return page(title="Register ILL request",
                uid=id_user,
                req=req,
                metaheaderadd = "<link rel=\"stylesheet\" href=\"%s/img/jquery-ui.css\" type=\"text/css\" />" % CFG_SITE_URL,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def register_ill_request_with_no_recid_step2(req, title, authors, place,
                                             publisher, year, edition, isbn, period_of_interest_from,
                                             period_of_interest_to, additional_comments,
                                             only_edition, key, string, ln=CFG_SITE_LANG):
    """
    """
    infos = []
    book_info = (title, authors, place, publisher, year, edition, isbn)
    request_details = (period_of_interest_from, period_of_interest_to,
                           additional_comments, only_edition)
    if key and not string:
        infos.append('Empty string. Please, try again.')
        book_info = (title, authors, place, publisher, year, edition, isbn)
        request_details = (period_of_interest_from, period_of_interest_to,
                           additional_comments, only_edition)

        body = bibcirculation_templates.tmpl_register_ill_request_with_no_recid_step2(book_info=book_info,
                                                                                      request_details=request_details,
                                                                                      result=None,
                                                                                      key=key,
                                                                                      string=string,
                                                                                      infos=infos,
                                                                                      ln=ln)

        navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a> &gt; <a class="navtrail" ' \
                              'href="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1">Circulation Management' \
                              '</a> ' % (CFG_SITE_URL, CFG_SITE_URL)

        id_user = getUid(req)
        (auth_code, auth_message) = is_adminuser(req)
        if auth_code != 0:
            return mustloginpage(req, auth_message)

        return page(title="Register ILL request",
                    uid=id_user,
                    req=req,
                    body=body,
                    navtrail=navtrail_previous_links,
                    lastupdated=__lastupdated__)

    list_infos = []

    if CFG_CERN_SITE == 1:
        if key =='ccid' and string:
            from invenio.bibcirculation_cern_ldap import get_user_info_from_ldap
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

        elif key =='name' and string:
            result = db.get_borrower_data_by_name(string)

            for (borrower_id, name, email, phone, address, mailbox) in result:
                tup = (borrower_id, name, email, phone, address, mailbox)
                list_infos.append(tup)

        elif key =='email' and string:
            result = db.get_borrower_data_by_email(string)

            for (borrower_id, name, email, phone, address, mailbox) in result:
                tup = (borrower_id, name, email, phone, address, mailbox)
                list_infos.append(tup)
        else:
            result = list_infos

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


    if validate_date_format(period_of_interest_from) is False:
        infos = []
        infos.append("The given 'period_of_interest_from' <strong>%s</strong>" \
                     " is not a valid date or date format" % period_of_interest_from)

        body = bibcirculation_templates.tmpl_register_ill_request_with_no_recid_step1(infos=infos,
                                                                                      ln=ln)

    elif validate_date_format(period_of_interest_to) is False:
        infos = []
        infos.append("The given 'period_of_interest_to' <strong>%s</strong>" \
                     " is not a valid date or date format" % period_of_interest_to)

        body = bibcirculation_templates.tmpl_register_ill_request_with_no_recid_step1(infos=infos,
                                                                                      ln=ln)

    else:
        book_info = (title, authors, place, publisher, year, edition, isbn)

        request_details = (period_of_interest_from, period_of_interest_to,
                           additional_comments, only_edition)

        body = bibcirculation_templates.tmpl_register_ill_request_with_no_recid_step2(book_info=book_info,
                                                                                      request_details=request_details,
                                                                                      result=list_infos,
                                                                                      key=key,
                                                                                      string=string,
                                                                                      infos=infos,
                                                                                      ln=ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a> &gt; <a class="navtrail" ' \
                              'href="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1">Circulation Management' \
                              '</a> ' % (CFG_SITE_URL, CFG_SITE_URL)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    return page(title="Register ILL request",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def register_ill_request_with_no_recid_step3(req, book_info, user_info, request_details, ln):

    """
    """

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a> &gt; <a class="navtrail" ' \
                              'href="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1">Circulation Management' \
                              '</a> ' % (CFG_SITE_URL, CFG_SITE_URL)


    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_register_ill_request_with_no_recid_step3(book_info=book_info,
                                                                                  user_info=user_info,
                                                                                  request_details=request_details,
                                                                                  ln=ln)

    return page(title="Register ILL request",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def register_ill_request_with_no_recid_step4(req, book_info, user_info, request_details, ln):

    """
    """
    #id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    (title, authors, place, publisher, year, edition, isbn) = book_info
    create_ill_record(book_info)

    book_info = {'title': title, 'authors': authors, 'place': place, 'publisher': publisher,
                 'year' : year,  'edition': edition, 'isbn' : isbn}

    (period_of_interest_from, period_of_interest_to,
     library_notes, only_edition) = request_details

    (borrower_id, _name, _email, _phone, _address, _mailbox) = user_info

    ill_request_notes = {}
    if library_notes:
        ill_request_notes[time.strftime("%Y-%m-%d %H:%M:%S")] = str(library_notes)

    db.ill_register_request_on_desk(borrower_id, book_info, period_of_interest_from,
                                    period_of_interest_to, 'new',
                                    str(ill_request_notes), only_edition, 'book')

    #navtrail_previous_links = '<a class="navtrail" ' \
    #                          'href="%s/help/admin">Admin Area' \
    #                          '</a>' % (CFG_SITE_URL,)

    return list_ill_request(req, "new", ln)

def get_borrower_ill_details(req, borrower_id, ill_id, ln=CFG_SITE_LANG):
    """
    Display ILL details of a borrower.

    @type  borrower_id: integer.
    @param borrower_id: identify the borrower. It is also the primary key of
                        the table crcBORROWER.

    @type  ill_id:  integer.
    @param ill_id:  identify the ILL request. It is also the primary key
                    of the table crcILLREQUEST.

    @return:        borrower ILL details.
    """

    result = db.get_ill_requests_details(borrower_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    name = db.get_borrower_name(borrower_id)

    title = "ILL details - %s" % (name)
    body = bibcirculation_templates.tmpl_borrower_ill_details(result=result,
                                                              borrower_id=borrower_id,
                                                              ill_id=ill_id,
                                                              ln=ln)

    return page(title=title,
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def get_ill_library_notes(req, ill_id, delete_key, library_notes, ln=CFG_SITE_LANG):
    """
    """

    if delete_key and ill_id:
        ill_notes = eval(db.get_ill_notes(ill_id))
        del ill_notes[delete_key]
        db.update_ill_notes(ill_id, ill_notes)

    elif library_notes:
        if db.get_ill_notes(ill_id):
            ill_notes = eval(db.get_ill_notes(ill_id))
        else:
            ill_notes = {}

        ill_notes[time.strftime("%Y-%m-%d %H:%M:%S")] = str(library_notes)
        db.update_ill_notes(ill_id, ill_notes)

    ill_notes = db.get_ill_notes(ill_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_ill_notes(ill_notes=ill_notes,
                                                   ill_id=ill_id,
                                                   ln=ln)
    return page(title="ILL notes",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def get_expired_loans_with_requests(req, request_id, ln=CFG_SITE_LANG):
    """
    """

    if request_id:
        db.update_loan_request_status(request_id,'cancelled')
        update_request_data(request_id)
        result = db.get_expired_loans_with_requests()

    else:
        result = db.get_expired_loans_with_requests()

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a> &gt; <a class="navtrail" ' \
                              'href="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1">Circulation Management' \
                              '</a> ' % (CFG_SITE_URL, CFG_SITE_URL)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_get_expired_loans_with_requests(result=result,
                                                                         ln=ln)

    return page(title="Overdue loans with holds",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def register_ill_book_request(req, ln=CFG_SITE_LANG):
    """
    Display a form where is possible to searh for an item.
    """
    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a> &gt; <a class="navtrail" ' \
                              'href="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1">Circulation Management' \
                              '</a> ' % (CFG_SITE_URL, CFG_SITE_URL)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    infos = []

    body = bibcirculation_templates.tmpl_register_ill_book_request(infos=infos,
                                                                   ln=ln)

    return page(title="Register ILL Book request",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def register_ill_book_request_result(req, p, f, ln=CFG_SITE_LANG):
    """
    Search an item and return a list with all the possible results. To retrieve
    the information desired, we use the method 'perform_request_search' (from
    search_engine.py). In the case of BibCirculation, we are just looking for
    books (items) inside the collection 'Books'.

    @type p:   string
    @param p:  search pattern

    @type f:   string
    @param f:  search field

    @return:   list of recids
    """

    if f == 'barcode':
        has_recid = db.get_recid(p)
        infos = []

        if has_recid is None:
            infos.append('The barcode <strong>%s</strong> does not exist on BibCirculation database.' % p)
            body = bibcirculation_templates.tmpl_register_ill_book_request(infos=infos, ln=ln)
        else:
            body = bibcirculation_templates.tmpl_register_ill_book_request_result(result=has_recid, ln=ln)
    else:
        result = perform_request_search(cc="Books", sc="1", p=p, f=f)
        if len(result) == 0:
            return register_ill_request_with_no_recid_step1(req, ln)
        else:
            body = bibcirculation_templates.tmpl_register_ill_book_request_result(result=result, ln=ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a> &gt; <a class="navtrail" ' \
                              'href="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1">Circulation Management' \
                              '</a> ' % (CFG_SITE_URL, CFG_SITE_URL)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    return page(title="Register ILL Book request",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def register_ill_book_request_from_borrower_page(req, borrower_id, ln=CFG_SITE_LANG):
    """
    Display a form where is possible to searh for an item.
    """
    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a> &gt; <a class="navtrail" ' \
                              'href="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1">Circulation Management' \
                              '</a> ' % (CFG_SITE_URL, CFG_SITE_URL)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    infos = []

    body = bibcirculation_templates.tmpl_register_ill_book_request_from_borrower_page(infos=infos,
                                                                                      borrower_id=borrower_id,
                                                                                      ln=ln)

    return page(title="Register ILL Book request",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def register_ill_book_request_from_borrower_page_result(req, borrower_id, p, f, ln=CFG_SITE_LANG):
    """
    Search an item and return a list with all the possible results. To retrieve
    the information desired, we use the method 'perform_request_search' (from
    search_engine.py). In the case of BibCirculation, we are just looking for
    books (items) inside the collection 'Books'.

    @type p:   string
    @param p:  search pattern

    @type f:   string
    @param f:  search field

    @return:   list of recids
    """

    if f == 'barcode':
        has_recid = db.get_recid(p)
        infos = []

        if has_recid is None:
            infos.append('The barcode <strong>%s</strong> does not exist on BibCirculation database.' % p)
            body = bibcirculation_templates.tmpl_register_ill_book_request_from_borrower_page(infos=infos, ln=ln)
        else:
            body = bibcirculation_templates.tmpl_register_ill_book_request_from_borrower_page_result(result=has_recid,
                                                                                                     borrower_id=borrower_id,
                                                                                                     ln=ln)
    else:
        result = perform_request_search(cc="Books", sc="1", p=p, f=f)
        if len(result) == 0:
            return register_ill_request_from_borrower_page_step1(req, borrower_id, ln)
        else:
            body = bibcirculation_templates.tmpl_register_ill_book_request_from_borrower_page_result(result=result,
                                                                                                     borrower_id=borrower_id,
                                                                                                     ln=ln)
    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a> &gt; <a class="navtrail" ' \
                              'href="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1">Circulation Management' \
                              '</a> ' % (CFG_SITE_URL, CFG_SITE_URL)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    return page(title="Register ILL Book request",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def register_ill_request_from_borrower_page_step1(req, borrower_id, ln=CFG_SITE_LANG):
    """
    """
    infos = []

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_register_ill_request_from_borrower_page_step1(infos=infos,
                                                                                       borrower_id=borrower_id,
                                                                                       ln=ln)

    return page(title="Register ILL request",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def register_ill_request_from_borrower_page_step2(req, borrower_id, title, authors, place,
                                                  publisher, year, edition, isbn, period_of_interest_from,
                                                  period_of_interest_to, additional_comments,
                                                  only_edition, ln=CFG_SITE_LANG):

    """
    """

    infos = []

    if validate_date_format(period_of_interest_from) is False:
        infos.append("The given 'period_of_interest_from' <strong>%s</strong>" \
                     " is not a valid date or date format" % period_of_interest_from)

        body = bibcirculation_templates.tmpl_register_ill_request_from_borrower_page_step1(infos=infos,
                                                                                           borrower_id=borrower_id,
                                                                                           ln=ln)

    elif validate_date_format(period_of_interest_to) is False:
        infos.append("The given 'period_of_interest_to' <strong>%s</strong>" \
                     " is not a valid date or date format" % period_of_interest_to)

        body = bibcirculation_templates.tmpl_register_ill_request_from_borrower_page_step1(infos=infos,
                                                                                           borrower_id=borrower_id,
                                                                                           ln=ln)
    else:
        book_info = (title, authors, place, publisher, year, edition, isbn)
        user_info = db.get_borrower_details(borrower_id)
        request_details = (period_of_interest_from, period_of_interest_to,
                           additional_comments, only_edition)

        body = bibcirculation_templates.tmpl_register_ill_request_with_no_recid_step3(book_info=book_info,
                                                                                  user_info=user_info,
                                                                                  request_details=request_details,
                                                                                  ln=ln)


    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a> &gt; <a class="navtrail" ' \
                              'href="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1">Circulation Management' \
                              '</a> ' % (CFG_SITE_URL, CFG_SITE_URL)


    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    return page(title="Register ILL request",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def register_ill_article_request_step1(req, ln=CFG_SITE_LANG):
    """
    """

    infos = []

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a> &gt; <a class="navtrail" ' \
                              'href="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1">Circulation Management' \
                              '</a> ' % (CFG_SITE_URL, CFG_SITE_URL)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_register_ill_article_request_step1(infos=infos, ln=ln)

    return page(title="Register ILL Article request",
                uid=id_user,
                req=req,
                body=body,
                metaheaderadd = "<link rel=\"stylesheet\" href=\"%s/img/jquery-ui.css\" type=\"text/css\" />"%(CFG_SITE_URL),
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def register_ill_article_request_step2(req, periodical_title, article_title, author, report_number,
                                       volume, issue, pages, year, issn,
                                       period_of_interest_from, period_of_interest_to,
                                       additional_comments, key, string, ln=CFG_SITE_LANG):


    infos = []

    if key and not string:
        infos.append('Empty string. Please, try again.')
        article_info = (periodical_title, article_title, author, report_number,
                        volume, issue, pages, year, issn)
        request_details = (period_of_interest_from, period_of_interest_to,
                           additional_comments)

        body = bibcirculation_templates.tmpl_register_ill_article_request_step2(article_info=article_info,
                                                                                request_details=request_details,
                                                                                result=None,
                                                                                key=key,
                                                                                string=string,
                                                                                infos=infos,
                                                                                ln=ln)


        navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a> &gt; <a class="navtrail" ' \
                              'href="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1">Circulation Management' \
                              '</a> ' % (CFG_SITE_URL, CFG_SITE_URL)

        id_user = getUid(req)
        (auth_code, auth_message) = is_adminuser(req)
        if auth_code != 0:
            return mustloginpage(req, auth_message)

        return page(title="Register ILL request",
                    uid=id_user,
                    req=req,
                    body=body,
                    navtrail=navtrail_previous_links,
                    lastupdated=__lastupdated__)

    list_infos = []

    if CFG_CERN_SITE == 1:
        if key =='ccid' and string:
            from invenio.bibcirculation_cern_ldap import get_user_info_from_ldap
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

        elif key =='name' and string:
            result = db.get_borrower_data_by_name(string)

            for (borrower_id, name, email, phone, address, mailbox) in result:
                tup = (borrower_id, name, email, phone, address, mailbox)
                list_infos.append(tup)

        elif key =='email' and string:
            result = db.get_borrower_data_by_email(string)

            for (borrower_id, name, email, phone, address, mailbox) in result:
                tup = (borrower_id, name, email, phone, address, mailbox)
                list_infos.append(tup)
        else:
            result = list_infos

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


    if validate_date_format(period_of_interest_from) is False:
        infos = []
        infos.append("The given 'period_of_interest_from' <strong>%s</strong>" \
                     " is not a valid date or date format" % period_of_interest_from)

        body = bibcirculation_templates.tmpl_register_ill_article_request_step1(infos=infos,
                                                                                ln=ln)

    elif validate_date_format(period_of_interest_to) is False:
        infos = []
        infos.append("The given 'period_of_interest_to' <strong>%s</strong>" \
                     " is not a valid date or date format" % period_of_interest_to)

        body = bibcirculation_templates.tmpl_register_ill_article_request_step1(infos=infos,
                                                                                ln=ln)

    else:
        article_info = (periodical_title, article_title, author, report_number,
                        volume, issue, pages, year, issn)

        request_details = (period_of_interest_from, period_of_interest_to,
                           additional_comments)

        body = bibcirculation_templates.tmpl_register_ill_article_request_step2(article_info=article_info,
                                                                                request_details=request_details,
                                                                                result=list_infos,
                                                                                key=key,
                                                                                string=string,
                                                                                infos=infos,
                                                                                ln=ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a> &gt; <a class="navtrail" ' \
                              'href="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1">Circulation Management' \
                              '</a> ' % (CFG_SITE_URL, CFG_SITE_URL)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    return invenio.webpage.page(title="Register ILL request",
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def register_ill_article_request_step3(req, item_info, user_info, request_details, ln):

    """
    """

    #id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    (periodical_title, title, authors, _report_number, volume, issue, page_number, year, issn) = item_info
    volume = volume + ', '+ issue + ', '+ page_number

    info = (title, authors, "", "", year, "", issn)

    create_ill_record(info)

    item_info = {'periodical_title': periodical_title, 'title': title, 'authors': authors, 'place': "", 'publisher': "",
                 'year' : year,  'edition': "", 'issn' : issn, 'volume': volume }


    (period_of_interest_from, period_of_interest_to,
     library_notes) = request_details

    only_edition = ""

    (borrower_id, _name, _email, _phone, _address, _mailbox) = user_info

    ill_request_notes = {}
    if library_notes:
        ill_request_notes[time.strftime("%Y-%m-%d %H:%M:%S")] = str(library_notes)

    db.ill_register_request_on_desk(borrower_id, item_info, period_of_interest_from,
                                    period_of_interest_to, 'new',
                                    str(ill_request_notes), only_edition, 'article')

    #navtrail_previous_links = '<a class="navtrail" ' \
    #                          'href="%s/help/admin">Admin Area' \
    #                          '</a>' % (CFG_SITE_URL,)

    return list_ill_request(req, 'new', ln)

def ill_search(req, ln=CFG_SITE_LANG):
    """
    """
    infos = []

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a> &gt; <a class="navtrail" ' \
                              'href="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1">Circulation Management' \
                              '</a> ' % (CFG_SITE_URL, CFG_SITE_URL)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bibcirculation_templates.tmpl_ill_search(infos=infos, ln=ln)

    return page(title="ILL search",
                uid=id_user,
                req=req,
                body=body,
                 metaheaderadd = "<link rel=\"stylesheet\" href=\"%s/img/jquery-ui.css\" type=\"text/css\" />" % CFG_SITE_URL,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def ill_search_result(req, p, f, date_from, date_to, ln):
    """
    Search an item and return a list with all the possible results. To retrieve
    the information desired, we use the method 'perform_request_search' (from
    search_engine.py). In the case of BibCirculation, we are just looking for
    books (items) inside the collection 'Books'.

    @type p:   string
    @param p:  search pattern

    @type f:   string
    @param f:  search field

    @return:   list of recids
    """
    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a> &gt; <a class="navtrail" ' \
                              'href="%s/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1">Circulation Management' \
                              '</a> ' % (CFG_SITE_URL, CFG_SITE_URL)

    if date_from == 'the beginning':
        date_from = '0000-00-00'
    if date_to == 'now':
        date_to = '9999-12-31'

    if f=='title':
        ill_req = db.search_ill_requests_title(p, date_from, date_to)
    elif f=='ILL_request_ID':
        ill_req = db.search_ill_requests_id(p, date_from, date_to)

    body = bibcirculation_templates.tmpl_list_ill_request(ill_req=ill_req, ln=ln)


    return page(title="List of ILL requests",
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

    #if f == 'title':
        #from invenio.intbitset import intbitset
        #
        #ill_cds = get_list_of_ILL_requests()
        #ill_books = perform_request_search(cc="ILL Books")
        #
        #tmp = intbitset(ill_cds + ill_books)
        #ill_pattern = intbitset(perform_request_search(c=["Books", "ILL Books"], p=p))
        #
        #result = list(ill_pattern & tmp)