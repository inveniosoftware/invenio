# Administrator interface for Bibcirculation
#
# This file is part of Invenio.
# Copyright (C) 2008, 2009, 2010, 2011, 2012, 2013 CERN.
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

# """Invenio Bibcirculation Administrator Interface."""

from __future__ import division

"""
   Invenio Bibcirculation Administrator.
   The functions are positioned by grouping into logical
   categories('User Pages', 'Loans, Returns and Loan requests',
   'ILLs', 'Libraries', 'Vendors' ...)
   These orders should be maintained and when necessary, improved
   for readability, as and when additional methods are added.
   When applicable, methods should be renamed, refactored and
   appropriate documentation added.
"""

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

import datetime, time, types

# Other Invenio imports
from invenio.config import \
    CFG_SITE_LANG, \
    CFG_SITE_URL, \
    CFG_SITE_SECURE_URL, \
    CFG_CERN_SITE
import invenio.access_control_engine as acce
from invenio.webpage import page
from invenio.webuser import getUid, page_not_authorized
from invenio.webstat import register_customevent
from invenio.errorlib import register_exception
from invenio.mailutils import send_email
from invenio.search_engine import perform_request_search, record_exists
from invenio.urlutils import create_html_link, create_url, redirect_to_url
from invenio.messages import gettext_set_language
from invenio.webstat import register_customevent
from invenio.errorlib import register_exception
from invenio.config import \
    CFG_BIBCIRCULATION_ITEM_STATUS_ON_LOAN, \
    CFG_BIBCIRCULATION_ITEM_STATUS_ON_ORDER, \
    CFG_BIBCIRCULATION_ITEM_STATUS_ON_SHELF, \
    CFG_BIBCIRCULATION_ITEM_STATUS_IN_PROCESS, \
    CFG_BIBCIRCULATION_ITEM_STATUS_UNDER_REVIEW, \
    CFG_BIBCIRCULATION_LOAN_STATUS_ON_LOAN, \
    CFG_BIBCIRCULATION_LOAN_STATUS_RETURNED, \
    CFG_BIBCIRCULATION_REQUEST_STATUS_WAITING, \
    CFG_BIBCIRCULATION_REQUEST_STATUS_PENDING, \
    CFG_BIBCIRCULATION_REQUEST_STATUS_DONE, \
    CFG_BIBCIRCULATION_REQUEST_STATUS_CANCELLED, \
    CFG_BIBCIRCULATION_ILL_STATUS_NEW, \
    CFG_BIBCIRCULATION_ILL_STATUS_ON_LOAN, \
    CFG_BIBCIRCULATION_LIBRARY_TYPE_MAIN, \
    CFG_BIBCIRCULATION_ACQ_STATUS_NEW, \
    CFG_BIBCIRCULATION_ACQ_STATUS_RECEIVED, \
    CFG_BIBCIRCULATION_PROPOSAL_STATUS_ON_ORDER, \
    CFG_BIBCIRCULATION_PROPOSAL_STATUS_PUT_ASIDE, \
    CFG_BIBCIRCULATION_PROPOSAL_STATUS_RECEIVED

# Bibcirculation imports
from invenio.bibcirculation_config import \
     CFG_BIBCIRCULATION_TEMPLATES, CFG_BIBCIRCULATION_LIBRARIAN_EMAIL, \
     CFG_BIBCIRCULATION_LOANS_EMAIL, CFG_BIBCIRCULATION_ILLS_EMAIL, \
     CFG_BIBCIRCULATION_PROPOSAL_TYPE, CFG_BIBCIRCULATION_ACQ_STATUS
from invenio.bibcirculation_utils import book_title_from_MARC, \
      update_status_if_expired, \
      renew_loan_for_X_days, \
      print_pending_hold_requests_information, \
      print_new_loan_information, \
      validate_date_format, \
      generate_email_body, \
      book_information_from_MARC, \
      search_user, \
      tag_all_requests_as_done, \
      update_user_info_from_ldap, \
      update_request_data, \
      update_requests_statuses, \
      has_date_format, \
      generate_tmp_barcode, \
      looks_like_dictionary
import invenio.bibcirculation_dblayer as db
import invenio.template
bc_templates = invenio.template.load('bibcirculation')



def is_adminuser(req):
    """check if user is a registered administrator. """

    return acce.acc_authorize_action(req, "runbibcirculation")

def mustloginpage(req, message):
    """show a page asking the user to login."""

    navtrail_previous_links = '<a class="navtrail" href="%s/admin/">' \
        'Admin Area</a> &gt; ' \
        '<a class="navtrail" href="%s/admin/bibcirculation/">' \
        'BibCirculation Admin</a> ' % (CFG_SITE_SECURE_URL, CFG_SITE_SECURE_URL)

    return page_not_authorized(req=req, text=message,
        navtrail=navtrail_previous_links)

def load_template(template):
    """
    Load a letter/notification template from
    bibcirculation_config.py.

    @type template:  string.
    @param template: template that will be used.

    @return:         template(string)
    """

    if template == "overdue_letter":
        output = CFG_BIBCIRCULATION_TEMPLATES['OVERDUE']

    elif template == "reminder":
        output = CFG_BIBCIRCULATION_TEMPLATES['REMINDER']

    elif template == "notification":
        output = CFG_BIBCIRCULATION_TEMPLATES['NOTIFICATION']

    elif template == "ill_received":
        output = CFG_BIBCIRCULATION_TEMPLATES['ILL_RECEIVED']

    elif template == "ill_recall1":
        output = CFG_BIBCIRCULATION_TEMPLATES['ILL_RECALL1']

    elif template == "ill_recall2":
        output = CFG_BIBCIRCULATION_TEMPLATES['ILL_RECALL2']

    elif template == "ill_recall3":
        output = CFG_BIBCIRCULATION_TEMPLATES['ILL_RECALL3']

    elif template == "claim_return":
        output = CFG_BIBCIRCULATION_TEMPLATES['SEND_RECALL']

    elif template == "proposal_notification":
        output = CFG_BIBCIRCULATION_TEMPLATES['PROPOSAL_NOTIFICATION']

    elif template == "proposal_acceptance":
        output = CFG_BIBCIRCULATION_TEMPLATES['PROPOSAL_ACCEPTANCE_NOTIFICATION']

    elif template == "proposal_refusal":
        output = CFG_BIBCIRCULATION_TEMPLATES['PROPOSAL_REFUSAL_NOTIFICATION']

    elif template == "purchase_notification":
        output = CFG_BIBCIRCULATION_TEMPLATES['PURCHASE_NOTIFICATION']

    elif template == "purchase_received_tid":
        output = CFG_BIBCIRCULATION_TEMPLATES['PURCHASE_RECEIVED_TID']

    elif template == "purchase_received_cash":
        output = CFG_BIBCIRCULATION_TEMPLATES['PURCHASE_RECEIVED_CASH']

    else:
        output = CFG_BIBCIRCULATION_TEMPLATES['EMPTY']

    return output

def index(req, ln=CFG_SITE_LANG):
    """
    main function to show pages for bibcirculationadmin
    """
    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    body = bc_templates.tmpl_index(ln=ln)

    return page(title=_("BibCirculation Admin"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)



###
### Loans, Loan Requests, Loan Returns related templates.
###




def loan_on_desk_step1(req, key, string, ln=CFG_SITE_LANG):
    """
    Step 1/4 of loan procedure.
    Search a user/borrower and return a list with all the possible results.

    @type key:     string.
    @param key:    attribute that will be considered during the search. Can be 'name',
                   'email' or 'ccid/id'.

    @type string:  string.
    @param string: keyword used during the search.

    @return:       list of potential borrowers.
    """
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    infos = []
    _ = gettext_set_language(ln)

    if key and not string:
        infos.append(_('Empty string. Please, try again.'))
        body = bc_templates.tmpl_loan_on_desk_step1(result=None, key=key,
                                                    string=string, infos=infos,
                                                    ln=ln)

        navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

        return page(title=_("Loan on desk"),
                    uid=id_user,
                    req=req,
                    body=body, language=ln,
                    navtrail=navtrail_previous_links,
                    lastupdated=__lastupdated__)

    result = search_user(key, string)
    borrowers_list = []

    if len(result) == 0 and key:
        if CFG_CERN_SITE:
            infos.append(_("0 borrowers found.") + ' ' +_("Search by CCID."))
        else:
            new_borrower_link = create_html_link(CFG_SITE_SECURE_URL +
                                '/admin2/bibcirculation/add_new_borrower_step1',
                                {'ln': ln}, _("Register new borrower."))
            message = _("0 borrowers found.") + ' ' + new_borrower_link
            infos.append(message)
    elif len(result) == 1:
        return loan_on_desk_step2(req, result[0][0], ln)
    else:
        for user in result:
            borrower_data = db.get_borrower_data_by_id(user[0])
            borrowers_list.append(borrower_data)

    body = bc_templates.tmpl_loan_on_desk_step1(result=borrowers_list,
                                                key=key,
                                                string=string,
                                                infos=infos,
                                                ln=ln)


    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    return page(title=_("Circulation management"),
                uid=id_user,
                req=req,
                body=body,
                language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def loan_on_desk_step2(req, user_id, ln=CFG_SITE_LANG):
    """
    Step 2/4 of loan procedure.
    Display the user/borrower's information.

    @type user_id:  integer
    @param user_id: identify the borrower. It is also the primary key of
                    the table crcBORROWER.

    """

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    _ = gettext_set_language(ln)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    infos = []

    body = bc_templates.tmpl_loan_on_desk_step2(user_id=user_id,
                                                infos=infos,
                                                ln=ln)

    return page(title=_("Circulation management"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def loan_on_desk_step3(req, user_id, list_of_barcodes, ln=CFG_SITE_LANG):
    """
    Step 3/4 of loan procedure.
    Checks that the barcodes exist and that there are no request on these records.
    Lets the librarian change the due dates and add notes.

    @type user_id:  integer
    @param user_id: identify the borrower. It is also the primary key of
                    the table crcBORROWER.

    @type list_of_barcodes:  list
    @param list_of_barcodes: list of strings with the barcodes
                             introduced by the librarian with the barcode reader
    """

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    _ = gettext_set_language(ln)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    infos = []
    list_of_books = []

    # to avoid duplicates
    aux = []
    for bc in list_of_barcodes:
        if bc not in aux:
            aux.append(bc)
    list_of_barcodes = aux

    for value in list_of_barcodes:
        recid = db.get_id_bibrec(value)
        loan_id = db.is_item_on_loan(value)
        item_description = db.get_item_description(value)

        if recid is None:
            infos.append(_('%(x_strong_tag_open)s%(x_barcode)s%(x_strong_tag_close)s Unknown barcode.') % {'x_barcode': value, 'x_strong_tag_open': '<strong>', 'x_strong_tag_close': '</strong>'} + ' ' + _('Please, try again.'))
            body = bc_templates.tmpl_loan_on_desk_step2(user_id=user_id,
                                                        infos=infos,
                                                        ln=ln)
        elif loan_id:
            infos.append('The item with the barcode %(x_strong_tag_open)s%(x_barcode)s%(x_strong_tag_close)s is on a loan. Cannot be checked out.' % {'x_barcode': value, 'x_strong_tag_open': '<strong>', 'x_strong_tag_close': '</strong>'})
            body = bc_templates.tmpl_loan_on_desk_step2(user_id=user_id,
                                                        infos=infos,
                                                        ln=ln)
        elif user_id is None:
            infos.append(_('You must select one borrower.'))
            body = bc_templates.tmpl_loan_on_desk_step1(result=None,
                                                        key='',
                                                        string='',
                                                        infos=infos,
                                                        ln=ln)
        else:

            queue = db.get_queue_request(recid, item_description)
            (library_id, location) = db.get_lib_location(value)
            tup = (recid, value, library_id, location)
            list_of_books.append(tup)
            book_details = db.get_item_info(value)
            item_status = book_details[7]

            if item_status != CFG_BIBCIRCULATION_ITEM_STATUS_ON_SHELF:
                message = _("%(x_strong_tag_open)sWARNING:%(x_strong_tag_close)s Note that item %(x_strong_tag_open)s%(x_barcode)s%(x_strong_tag_close)s status is %(x_strong_tag_open)s%(x_status)s%(x_strong_tag_close)s") % {'x_barcode': value, 'x_strong_tag_open': '<strong>', 'x_strong_tag_close': '</strong>', 'x_status': item_status}

                infos.append(message)

            if CFG_CERN_SITE:
                library_type = db.get_library_type(library_id)
                if library_type != CFG_BIBCIRCULATION_LIBRARY_TYPE_MAIN:
                    library_name = db.get_library_name(library_id)
                    message = _("%(x_strong_tag_open)sWARNING:%(x_strong_tag_close)s Note that item %(x_strong_tag_open)s%(x_barcode)s%(x_strong_tag_close)s location is %(x_strong_tag_open)s%(x_location)s%(x_strong_tag_close)s") % {'x_barcode': value, 'x_strong_tag_open': '<strong>', 'x_strong_tag_close': '</strong>', 'x_location': library_name}
                    infos.append(message)

            if len(queue) != 0  and  queue[0][0] != user_id:
                message = _("Another user is waiting for the book: %(x_strong_tag_open)s%(x_title)s%(x_strong_tag_close)s. \n\n If you want continue with this loan choose %(x_strong_tag_open)s[Continue]%(x_strong_tag_close)s.") % {'x_title': book_title_from_MARC(recid), 'x_strong_tag_open': '<strong>', 'x_strong_tag_close': '</strong>'}
                infos.append(message)

            body = bc_templates.tmpl_loan_on_desk_step3(user_id=user_id,
                                                    list_of_books=list_of_books,
                                                    infos=infos, ln=ln)

    if list_of_barcodes == []:
        infos.append(_('Empty barcode.') + ' ' + _('Please, try again.'))
        body = bc_templates.tmpl_loan_on_desk_step2(user_id=user_id,
                                                    infos=infos,
                                                    ln=ln)

    if infos == []:
        # shortcut to simplify loan process
        due_dates = []
        for bc in list_of_barcodes:
            due_dates.append(renew_loan_for_X_days(bc))

        return loan_on_desk_step4(req, list_of_barcodes, user_id,
                       due_dates, None, ln)

    else:
        return page(title=_("Circulation management"),
                uid=id_user,
                req=req,
                body=body,
                metaheaderadd = "<link rel=\"stylesheet\" href=\"%s/img/jquery-ui.css\" type=\"text/css\" />" % CFG_SITE_SECURE_URL,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def loan_on_desk_step4(req, list_of_barcodes, user_id,
                       due_date, note, ln=CFG_SITE_LANG):
    """
    Step 4/4 of loan procedure.
    Checks that items are not on loan and that the format of
    the dates is correct and creates the loans

    @type user_id:           integer
    @param user_id:          identify the borrower. It is also the primary key of
                             the table crcBORROWER.

    @type list_of_barcodes:  list
    @param list_of_barcodes: list of strings with the barcodes
                             introduced by the librarian with the barcode reader

    @type due_date:          list.
    @param due_date:         list of due dates.

    @type note:              string.
    @param note:             note about the new loan.

    @return:                 page with the list 'Last Loans'
    """

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    _ = gettext_set_language(ln)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    infos = []

    #loaned_on = datetime.date.today()

    #Check if one of the given items is on loan.
    on_loan = []
    for barcode in list_of_barcodes:
        is_on_loan = db.is_item_on_loan(barcode)
        if is_on_loan:
            on_loan.append(barcode)

    if len(on_loan) != 0:
        message = _("The items with barcode %(x_strong_tag_open)s%(x_barcode)s%(x_strong_tag_close)s are already on loan.") % {'x_barcode': on_loan, 'x_strong_tag_open': '<strong>', 'x_strong_tag_close': '</strong>'}
        infos.append(message)

        body = bc_templates.tmpl_loan_on_desk_step1(result=None, key='',
                                                    string='', infos=infos,
                                                    ln=ln)

        return page(title=_("Loan on desk"),
                    uid=id_user,
                    req=req,
                    body=body, language=ln,
                    navtrail=navtrail_previous_links,
                    lastupdated=__lastupdated__)

    # validate the period of interest given by the admin
    for date in due_date:
        if validate_date_format(date) is False:
            infos = []
            message = _("The given due date %(x_strong_tag_open)s%(x_date)s%(x_strong_tag_close)s is not a valid date or date format") % {'x_date': date, 'x_strong_tag_open': '<strong>', 'x_strong_tag_close': '</strong>'}

            infos.append(message)

            list_of_books = []
            for bc in list_of_barcodes:
                recid = db.get_id_bibrec(bc)
                (library_id, location) = db.get_lib_location(bc)
                tup = (recid, bc, library_id, location)
                list_of_books.append(tup)

            body = bc_templates.tmpl_loan_on_desk_step3(user_id=user_id,
                                                    list_of_books=list_of_books,
                                                    infos=infos, ln=ln)

            return page(title=_("Circulation management"),
                        uid=id_user,
                        req=req,
                        body=body, language=ln,
                        navtrail=navtrail_previous_links,
                        lastupdated=__lastupdated__)

    #if borrower_id == None:
    #    db.new_borrower(ccid, name, email, phone, address, mailbox, '')
    #    borrower_id = db.get_borrower_id_by_email(email)

    for i in range(len(list_of_barcodes)):
        note_format = {}
        if note:
            note_format[time.strftime("%Y-%m-%d %H:%M:%S")] = str(note)
        barcode = list_of_barcodes[i]
        recid = db.get_id_bibrec(barcode)
        db.new_loan(user_id, recid, barcode, due_date[i],
                    CFG_BIBCIRCULATION_LOAN_STATUS_ON_LOAN,
                    'normal', note_format)

        # Duplicate requests on items belonging to a single record has been disabled.
        db.tag_requests_as_done(user_id, barcode)
        # tag_all_requests_as_done(barcode, user_id)
        db.update_item_status(CFG_BIBCIRCULATION_ITEM_STATUS_ON_LOAN, barcode)
        update_requests_statuses(barcode)

    infos.append(_("A loan for the item %(x_strong_tag_open)s%(x_title)s%(x_strong_tag_close)s, with barcode %(x_strong_tag_open)s%(x_barcode)s%(x_strong_tag_close)s, has been registered with success.") % {'x_title': book_title_from_MARC(recid), 'x_barcode': barcode, 'x_strong_tag_open': '<strong>', 'x_strong_tag_close': '</strong>'})
    infos.append(_("You could enter the barcode for this user's next loan, if any."))
    body = bc_templates.tmpl_loan_on_desk_step2(user_id=user_id,
                                                infos=infos, ln=ln)
    return page(title=_("Circulation management"),
        uid=id_user,
        req=req,
        body=body,
        metaheaderadd = "<link rel=\"stylesheet\" href=\"%s/img/jquery-ui.css\" type=\"text/css\" />" % CFG_SITE_SECURE_URL,
        navtrail=navtrail_previous_links,
        lastupdated=__lastupdated__)

def loan_on_desk_confirm(req, barcode=None, borrower_id=None, ln=CFG_SITE_LANG):
    """
    *** Obsolete and unmantained function ***
    Confirm the return of an item.

    @type barcode:       string.
    @param barcode:      identify the item. It is the primary key of the table
                         crcITEM.

    @type borrower_id:   integer.
    @param borrower_id:  identify the borrower. It is also the primary key of
                         the table crcBORROWER.
    """

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    result = db.loan_on_desk_confirm(barcode, borrower_id)

    body = bc_templates.tmpl_loan_on_desk_confirm(result=result,
                                                  barcode=barcode,
                                                  borrower_id=borrower_id,
                                                  ln=ln)

    return page(title=_("Loan on desk confirm"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def register_new_loan(req, barcode, borrower_id,
                      request_id, new_note, print_data, ln=CFG_SITE_LANG):
    """
    Register a new loan. This function is from the "Create Loan" pages.

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

    @return:            new loan
    """

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    has_recid = db.get_id_bibrec(barcode)
    loan_id = db.is_item_on_loan(barcode)

    recid = db.get_request_recid(request_id)
    req_barcode = db.get_requested_barcode(request_id)
    req_description = db.get_item_description(req_barcode)
    # Get all the items belonging to the record whose
    # description is the same.
    list_of_barcodes = db.get_barcodes(recid, req_description)

    infos = []

    if print_data == 'true':
        return print_new_loan_information(req, ln)

    else:
        if has_recid is None:
            message = _('%(x_strong_tag_open)s%(x_barcode)s%(x_strong_tag_close)s Unknown barcode.') % {'x_barcode': barcode, 'x_strong_tag_open': '<strong>', 'x_strong_tag_close': '</strong>'} + ' ' + _('Please, try again.')
            infos.append(message)
            borrower = db.get_borrower_details(borrower_id)
            title = _("Create Loan")
            body = bc_templates.tmpl_create_loan(request_id=request_id,
                                                       recid=recid,
                                                       borrower=borrower,
                                                       infos=infos,
                                                       ln=ln)

        elif loan_id:
            infos.append(_('The item with the barcode %(x_strong_tag_open)s%(x_barcode)s%(x_strong_tag_close)s is on loan.') % {'x_barcode': barcode, 'x_strong_tag_open': '<strong>', 'x_strong_tag_close': '</strong>'})
            borrower = db.get_borrower_details(borrower_id)
            title = _("Create Loan")
            body = bc_templates.tmpl_create_loan(request_id=request_id,
                                                        recid=recid,
                                                        borrower=borrower,
                                                        infos=infos,
                                                        ln=ln)

        elif barcode not in list_of_barcodes:
            infos.append(_('The given barcode "%(x_barcode)s" does not correspond to requested item.') % {'x_barcode': barcode})
            borrower = db.get_borrower_details(borrower_id)
            title = _("Create Loan")
            body = bc_templates.tmpl_create_loan(request_id=request_id,
                                                        recid=recid,
                                                        borrower=borrower,
                                                        infos=infos,
                                                        ln=ln)

        else:
            recid = db.get_id_bibrec(barcode)
            #loaned_on = datetime.date.today()
            due_date = renew_loan_for_X_days(barcode)

            if new_note:
                note_format = '[' + time.ctime() + '] ' + new_note + '\n'
            else:
                note_format = ''

            last_id = db.new_loan(borrower_id, recid, barcode,
                        due_date, CFG_BIBCIRCULATION_LOAN_STATUS_ON_LOAN,
                        'normal', note_format)
            # register event in webstat
            try:
                register_customevent("loanrequest", [request_id, last_id])
            except:
                register_exception(suffix="Do the webstat tables exists? Try with 'webstatadmin --load-config'")

            tag_all_requests_as_done(barcode, borrower_id)

            db.update_item_status(CFG_BIBCIRCULATION_ITEM_STATUS_ON_LOAN, barcode)

            db.update_loan_request_status(CFG_BIBCIRCULATION_REQUEST_STATUS_DONE,
                                          request_id)
            db.update_request_barcode(barcode, request_id)
            update_requests_statuses(barcode)

            result = db.get_all_loans(20)

            infos.append(_('A new loan has been registered with success.'))

            title = _("Current loans")
            body = bc_templates.tmpl_all_loans(result=result,
                                                       infos=infos,
                                                       ln=ln)

        navtrail_previous_links = '<a class="navtrail" ' \
                                  'href="%s/help/admin">Admin Area' \
                                  '</a>' % (CFG_SITE_SECURE_URL,)

        return page(title=title,
                    uid=id_user,
                    req=req,
                    body=body, language=ln,
                    navtrail=navtrail_previous_links,
                    lastupdated=__lastupdated__)

def create_loan(req, request_id, recid, borrower_id, ln=CFG_SITE_LANG):
    """
    Create a new loan from a hold request.

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
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    borrower = db.get_borrower_details(borrower_id)
    infos = []

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    body = bc_templates.tmpl_create_loan(request_id=request_id,
                                                           recid=recid,
                                                           borrower=borrower,
                                                           infos=infos,
                                                           ln=ln)

    return page(title=_("Create Loan"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def make_new_loan_from_request(req, check_id, barcode, ln=CFG_SITE_LANG):
    """
    Turns a request into a loan.

    @type check_id:  integer.
    @param check_id: identify the hold request. It is also the primary key
                     of the table crcLOANREQUEST.

    @type barcode:   string.
    @param barcode:  identify the item. It is the primary key of the table
                     crcITEM.
    """

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    infos = []

    recid = db.get_request_recid(check_id)
    borrower_id = db.get_request_borrower_id(check_id)
    borrower_info = db.get_borrower_details(borrower_id)

    due_date = renew_loan_for_X_days(barcode)
    if db.is_item_on_loan(barcode):
        infos.append('The item with the barcode %(x_strong_tag_open)s%(x_barcode)s%(x_strong_tag_close)s is on loan.' % {'x_barcode': barcode, 'x_strong_tag_open': '<strong>', 'x_strong_tag_close': '</strong>'})
        return redirect_to_url(req,
            '%s/admin2/bibcirculation/all_loans?ln=%s&msg=ok' % (CFG_SITE_SECURE_URL, ln))
    else:
        db.new_loan(borrower_id, recid, barcode, due_date,
                    CFG_BIBCIRCULATION_LOAN_STATUS_ON_LOAN, 'normal', '')
        infos.append(_('A new loan has been registered with success.'))
        #try:
        #    register_customevent("baskets", ["display", "", user_str])
        #except:
        #    register_exception(suffix="Do the webstat tables exists? Try with 'webstatadmin --load-config'")

    tag_all_requests_as_done(barcode, borrower_id)
    db.update_item_status(CFG_BIBCIRCULATION_ITEM_STATUS_ON_LOAN, barcode)
    update_requests_statuses(barcode)

    navtrail_previous_links = '<a class="navtrail" ' \
                    'href="%s/help/admin">Admin Area' \
                    '</a> &gt; <a class="navtrail" ' \
                    'href="%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s">' \
                    'Circulation Management' \
                    '</a> ' % (CFG_SITE_SECURE_URL, CFG_SITE_SECURE_URL, ln)

    body = bc_templates.tmpl_register_new_loan(borrower_info=borrower_info,
                                               infos=infos,
                                               recid=recid,
                                               ln=ln)

    return page(title=_("New Loan"),
                uid=id_user,
                req=req,
                body=body,
                language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def loan_return(req, ln=CFG_SITE_LANG):
    """
    Page where is possible to register the return of an item.
    """

    _ = gettext_set_language(ln)

    infos = []

    navtrail_previous_links = '<a class="navtrail" ' \
                    'href="%s/help/admin">Admin Area' \
                    '</a> &gt; <a class="navtrail" ' \
                    'href="%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s">' \
                    'Circulation Management' \
                    '</a> ' % (CFG_SITE_SECURE_URL, CFG_SITE_SECURE_URL, ln)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bc_templates.tmpl_loan_return(infos=infos, ln=ln)

    return page(title=_("Loan return"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def loan_return_confirm(req, barcode, ln=CFG_SITE_LANG):
    """
    Performs the return of a loan and displays a confirmation page.
    In case the book is requested, it is possible to select a request
    and make a loan from it (make_new_loan_from_request)

    @type barcode:   string.
    @param barcode:  identify the item. It is the primary key of the table
                     crcITEM.
    """

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    infos = []
    _ = gettext_set_language(ln)

    recid   = db.get_id_bibrec(barcode)
    loan_id = db.is_item_on_loan(barcode)

    if recid is None:
        infos.append(_('%(x_strong_tag_open)s%(x_barcode)s%(x_strong_tag_close)s Unknown barcode.') % {'x_barcode': barcode, 'x_strong_tag_open': '<strong>', 'x_strong_tag_close': '</strong>'} + ' ' + _('Please, try again.'))
        body = bc_templates.tmpl_loan_return(infos=infos, ln=ln)

    elif loan_id is None:
        message = _("The item the with barcode %(x_strong_tag_open)s%(x_barcode)s%(x_strong_tag_close)s is not on loan. Please, try again.") % {'x_barcode': barcode, 'x_strong_tag_open': '<strong>', 'x_strong_tag_close': '</strong>'}

        infos.append(message)
        body = bc_templates.tmpl_loan_return(infos=infos, ln=ln)

    else:

        library_id = db.get_item_info(barcode)[1]
        if CFG_CERN_SITE:
            library_type = db.get_library_type(library_id)
            if library_type != CFG_BIBCIRCULATION_LIBRARY_TYPE_MAIN:
                library_name = db.get_library_name(library_id)
                message = _("%(x_strong_tag_open)sWARNING:%(x_strong_tag_close)s Note that item %(x_strong_tag_open)s%(x_barcode)s%(x_strong_tag_close)s location is %(x_strong_tag_open)s%(x_location)s%(x_strong_tag_close)s") % {'x_barcode': barcode, 'x_strong_tag_open': '<strong>', 'x_strong_tag_close': '</strong>', 'x_location': library_name}
                infos.append(message)

        borrower_id = db.get_borrower_id(barcode)
        borrower_name = db.get_borrower_name(borrower_id)

        db.update_item_status(CFG_BIBCIRCULATION_ITEM_STATUS_ON_SHELF, barcode)
        db.return_loan(barcode)

        update_requests_statuses(barcode)

        description = db.get_item_description(barcode)
        result = db.get_pending_loan_request(recid, description)
        body = bc_templates.tmpl_loan_return_confirm(
                                            infos=infos,
                                            borrower_name=borrower_name,
                                            borrower_id=borrower_id,
                                            recid=recid,
                                            barcode=barcode,
                                            return_date=datetime.date.today(),
                                            result=result,
                                            ln=ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    return page(title=_("Loan return"),
                uid=id_user,
                req=req,
                body=body,
                language=ln,
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

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    email_body = generate_email_body(load_template(template), loan_id)

    email = db.get_borrower_email(borrower_id)
    subject = book_title_from_MARC(int(recid))

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    body = bc_templates.tmpl_borrower_notification(email=email,
                                                   subject=subject,
                                                   email_body=email_body,
                                                   borrower_id=borrower_id,
                                                   from_address=CFG_BIBCIRCULATION_LOANS_EMAIL,
                                                   ln=ln)


    return page(title=_("Claim return"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def change_due_date_step1(req, barcode, borrower_id, ln=CFG_SITE_LANG):
    """
    Change the due date of a loan, step1.

    loan_id: identify a loan. It is the primery key of the table
             crcLOAN.

    borrower_id: identify the borrower. It is also the primary key of
                 the table crcBORROWER.
    """
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    loan_id = db.get_current_loan_id(barcode)
    loan_details = db.get_loan_infos(loan_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    body = bc_templates.tmpl_change_due_date_step1(loan_details=loan_details,
                                                   loan_id=loan_id,
                                                   borrower_id=borrower_id,
                                                   ln=ln)
    return page(title=_("Change due date"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                #metaheaderadd = '<link rel="stylesheet" '\
                #                'href="%s/img/jquery-ui/themes/redmond/ui.theme.css" '\
                #                'type="text/css" />' % CFG_SITE_SECURE_URL,
                metaheaderadd = '<link rel="stylesheet" href="%s/img/jquery-ui.css" '\
                                'type="text/css" />' % CFG_SITE_SECURE_URL,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def change_due_date_step2(req, new_due_date, loan_id, borrower_id,
                          ln=CFG_SITE_LANG):
    """
    Change the due date of a loan, step2.

    due_date: new due date.

    loan_id: identify a loan. It is the primery key of the table
             crcLOAN.

    borrower_id: identify the borrower. It is also the primary key of
                 the table crcBORROWER.
    """
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    db.update_due_date(loan_id, new_due_date)
    update_status_if_expired(loan_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    body = bc_templates.tmpl_change_due_date_step2(new_due_date=new_due_date,
                                                   borrower_id=borrower_id,
                                                   ln=ln)
    return page(title=_("Change due date"),
                uid=id_user,
                req=req,
                body=body, language=ln,
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
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    recid = db.get_id_bibrec(barcode)
    infos = []


    navtrail_previous_links = '<a class="navtrail" ' \
                          'href="%s/help/admin">Admin Area' \
                          '</a>' % (CFG_SITE_SECURE_URL,)
    if not barcode:
        return page(title=_("Item search"),
                    req=req,
                    body=bc_templates.tmpl_item_search(infos=[], ln=ln),
                    language=ln,
                    navtrail=navtrail_previous_links,
                    lastupdated=__lastupdated__)

    if key and not string:
        infos.append(_('Empty string.') + ' ' + _('Please, try again.'))
        body = bc_templates.tmpl_place_new_request_step1(result=None,
                                                         key=key,
                                                         string=string,
                                                         barcode=barcode,
                                                         recid=recid,
                                                         infos=infos,
                                                         ln=ln)

        return page(title=_("New request"),
                    uid=id_user,
                    req=req,
                    body=body,
                    language=ln,
                    navtrail=navtrail_previous_links,
                    lastupdated=__lastupdated__)

    result = search_user(key, string)
    borrowers_list = []

    if len(result) == 0 and key:
        if CFG_CERN_SITE:
            infos.append(_("0 borrowers found.") + ' ' +_("Search by CCID."))
        else:
            new_borrower_link = create_html_link(CFG_SITE_SECURE_URL +
                                '/admin2/bibcirculation/add_new_borrower_step1',
                                {'ln': ln}, _("Register new borrower."))
            message = _("0 borrowers found.") + ' ' + new_borrower_link
            infos.append(message)
    else:
        for user in result:
            borrower_data = db.get_borrower_data_by_id(user[0])
            borrowers_list.append(borrower_data)

    if len(result) == 1:
        return place_new_request_step2(req, barcode, recid,
                                       borrowers_list[0], ln)
    else:
        body = bc_templates.tmpl_place_new_request_step1(result=borrowers_list,
                                                         key=key,
                                                         string=string,
                                                         barcode=barcode,
                                                         recid=recid,
                                                         infos=infos,
                                                         ln=ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    return page(title=_("New request"),
                uid=id_user,
                req=req,
                body=body, language=ln,
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
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    if not user_info:
        # Case someone try directly to access to step2 without passing by previous step
        if barcode:
            return page(title=_("New request"),
                        uid=id_user,
                        req=req,
                        body=bc_templates.tmpl_place_new_request_step1(result=None,
                                                                       key=None,
                                                                       string=None,
                                                                       barcode=barcode,
                                                                       recid=recid,
                                                                       infos=[],
                                                                       ln=ln),
                        language=ln,
                        navtrail=navtrail_previous_links,
                        lastupdated=__lastupdated__)
        else:
            return page(title=_("Item search"),
                        req=req,
                        body=bc_templates.tmpl_item_search(infos=[], ln=ln),
                        language=ln,
                        navtrail=navtrail_previous_links,
                        lastupdated=__lastupdated__)


    body = bc_templates.tmpl_place_new_request_step2(barcode=barcode,
                                                     recid=recid,
                                                     user_info=user_info,
                                                     infos=[],
                                                     ln=ln)

    return page(title=_("New request"),
                uid=id_user,
                req=req,
                body=body,
                metaheaderadd="<link rel=\"stylesheet\" href=\"%s/img/jquery-ui.css\" type=\"text/css\" />" % CFG_SITE_SECURE_URL,
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

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)
    if user_info:
        (_id, ccid, name, email, phone, address, mailbox) = user_info
    else:
        # Case someone try directly to access to step3 without passing by previous step
        if barcode:
            return page(title=_("New request"),
                        uid=id_user,
                        req=req,
                        body=bc_templates.tmpl_place_new_request_step1(result=None,
                                                                       key="",
                                                                       string="",
                                                                       barcode=barcode,
                                                                       recid=recid,
                                                                       infos=[],
                                                                       ln=ln),
                        language=ln,
                        navtrail=navtrail_previous_links,
                        lastupdated=__lastupdated__)
        else:

            return page(title=_("Item search"),
                        req=req,
                        body=bc_templates.tmpl_item_search(infos=[], ln=ln),
                        language=ln,
                        navtrail=navtrail_previous_links,
                        lastupdated=__lastupdated__)

    # validate the period of interest given by the admin
    if not period_from or validate_date_format(period_from) is False:
        infos = []
        infos.append(_("The period of interest %(x_strong_tag_open)sFrom: %(x_date)s%(x_strong_tag_close)s is not a valid date or date format") % {'x_date': period_from, 'x_strong_tag_open': '<strong>', 'x_strong_tag_close': '</strong>'})

        body = bc_templates.tmpl_place_new_request_step2(barcode=barcode,
                                                         recid=recid,
                                                         user_info=user_info,
                                                         infos=infos,
                                                         ln=ln)

        return page(title=_("New request"),
                    uid=id_user,
                    req=req,
                    body=body,
                    language=ln,
                    navtrail=navtrail_previous_links,
                    lastupdated=__lastupdated__)

    elif not period_to or validate_date_format(period_to) is False:
        infos = []
        infos.append(_("The period of interest %(x_strong_tag_open)sTo: %(x_date)s%(x_strong_tag_close)s is not a valid date or date format") % {'x_date': period_to, 'x_strong_tag_open': '<strong>', 'x_strong_tag_close': '</strong>'})

        body = bc_templates.tmpl_place_new_request_step2(barcode=barcode,
                                                         recid=recid,
                                                         user_info=user_info,
                                                         infos=infos,
                                                         ln=ln)

    # Register request
    borrower_id = db.get_borrower_id_by_email(email)

    if borrower_id is None:
        db.new_borrower(ccid, name, email, phone, address, mailbox, '')
        borrower_id = db.get_borrower_id_by_email(email)

    req_id = db.new_hold_request(borrower_id, recid, barcode,
                                 period_from, period_to,
                                 CFG_BIBCIRCULATION_REQUEST_STATUS_WAITING)

    pending_request = update_requests_statuses(barcode)

    if req_id == pending_request:
        (title, year, author,
         isbn, publisher) = book_information_from_MARC(int(recid))
        details = db.get_loan_request_details(req_id)
        if details:
            library  = details[3]
            location = details[4]
            request_date = details[7]
        else:
            location = ''
            library  = ''
            request_date = ''

        link_to_holdings_details = CFG_SITE_URL + \
                                   '/record/%s/holdings' % str(recid)

        subject = _('New request')
        message = load_template('notification')

        message = message % (name, ccid, email, address, mailbox, title,
                             author, publisher, year, isbn, location, library,
                             link_to_holdings_details, request_date)


        send_email(fromaddr = CFG_BIBCIRCULATION_LIBRARIAN_EMAIL,
                toaddr   = CFG_BIBCIRCULATION_LOANS_EMAIL,
                subject  = subject,
                content  = message,
                header   = '',
                footer   = '',
                attempt_times=1,
                attempt_sleeptime=10
                )
        send_email(fromaddr = CFG_BIBCIRCULATION_LIBRARIAN_EMAIL,
                toaddr   = email,
                subject  = subject,
                content  = message,
                header   = '',
                footer   = '',
                attempt_times=1,
                attempt_sleeptime=10
                )

    body = bc_templates.tmpl_place_new_request_step3(ln=ln)

    return page(title=_("New request"),
                uid=id_user,
                req=req,
                body=body, language=ln,
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
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    recid = db.get_id_bibrec(barcode)
    infos = []

    if key and not string:
        infos.append(_('Empty string.') + ' ' + _('Please, try again.'))
        body = bc_templates.tmpl_place_new_loan_step1(result=None,
                                                        key=key,
                                                        string=string,
                                                        barcode=barcode,
                                                        recid=recid,
                                                        infos=infos,
                                                        ln=ln)

        navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

        id_user = getUid(req)
        (auth_code, auth_message) = is_adminuser(req)
        if auth_code != 0:
            return mustloginpage(req, auth_message)

        return page(title=_("New loan"),
                    uid=id_user,
                    req=req,
                    body=body, language=ln,
                    navtrail=navtrail_previous_links,
                    lastupdated=__lastupdated__)

    result = search_user(key, string)
    borrowers_list = []

    if len(result) == 0 and key:
        if CFG_CERN_SITE:
            infos.append(_("0 borrowers found.") + ' ' +_("Search by CCID."))
        else:
            new_borrower_link = create_html_link(CFG_SITE_SECURE_URL +
                                '/admin2/bibcirculation/add_new_borrower_step1',
                                {'ln': ln}, _("Register new borrower."))
            message = _("0 borrowers found.") + ' ' + new_borrower_link
            infos.append(message)
    else:
        for user in result:
            borrower_data = db.get_borrower_data_by_id(user[0])
            borrowers_list.append(borrower_data)

    body = bc_templates.tmpl_place_new_loan_step1(result=borrowers_list,
                                                              key=key,
                                                              string=string,
                                                              barcode=barcode,
                                                              recid=recid,
                                                              infos=infos,
                                                              ln=ln)


    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    return page(title=_("New loan"),
                uid=id_user,
                req=req,
                body=body, language=ln,
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

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    body = bc_templates.tmpl_place_new_loan_step2(barcode=barcode,
                                                    recid=recid,
                                                    user_info=user_info,
                                                    ln=ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    return page(title=_("New loan"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def place_new_loan_step3(req, barcode, recid, ccid, name, email, phone,
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
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    infos = []

    if notes:
        notes_format = '[' + time.ctime() + '] ' +  notes +  '\n'
    else:
        notes_format = ''

    #loaned_on = datetime.date.today()

    borrower_id = db.get_borrower_id_by_email(email)
    borrower_info = db.get_borrower_data(borrower_id)

    if db.is_on_loan(barcode):
        infos.append(_("Item with barcode %(x_strong_tag_open)s%(x_barcode)s%(x_strong_tag_close)s is already on loan.") % {'x_barcode': barcode, 'x_strong_tag_open': '<strong>', 'x_strong_tag_close': '</strong>'})

        copies = db.get_item_copies_details(recid)
        requests = db.get_item_requests(recid)
        loans = db.get_item_loans(recid)
        purchases = db.get_item_purchases(CFG_BIBCIRCULATION_ACQ_STATUS_NEW, recid)

        req_hist_overview = db.get_item_requests_historical_overview(recid)
        loans_hist_overview = db.get_item_loans_historical_overview(recid)
        purchases_hist_overview = db.get_item_purchases(CFG_BIBCIRCULATION_ACQ_STATUS_RECEIVED, recid)

        title = _("Item details")
        body = bc_templates.tmpl_get_item_details(
                                        recid=recid, copies=copies,
                                        requests=requests, loans=loans,
                                        purchases=purchases,
                                        req_hist_overview=req_hist_overview,
                                        loans_hist_overview=loans_hist_overview,
                                        purchases_hist_overview=purchases_hist_overview,
                                        infos=infos, ln=ln)

    elif borrower_id != 0:
        db.new_loan(borrower_id, recid, barcode,
                    due_date, CFG_BIBCIRCULATION_LOAN_STATUS_ON_LOAN,
                    'normal', notes_format)

        tag_all_requests_as_done(barcode, borrower_id)
        db.update_item_status(CFG_BIBCIRCULATION_ITEM_STATUS_ON_LOAN, barcode)
        update_requests_statuses(barcode)

        title = _("New loan")
        body = bc_templates.tmpl_register_new_loan(borrower_info=borrower_info,
                                                   infos=infos,
                                                   recid=recid, ln=ln)

    else:
        db.new_borrower(ccid, name, email, phone, address, mailbox, '')
        borrower_id = db.get_borrower_id_by_email(email)

        db.new_loan(borrower_id, recid, barcode,
                    due_date, CFG_BIBCIRCULATION_LOAN_STATUS_ON_LOAN,
                    'normal', notes_format)
        tag_all_requests_as_done(barcode, borrower_id)
        db.update_item_status(CFG_BIBCIRCULATION_ITEM_STATUS_ON_LOAN, barcode)
        update_requests_statuses(barcode)
        title = _("New loan")
        body = bc_templates.tmpl_register_new_loan(borrower_info=borrower_info,
                                                   infos=infos,
                                                   recid=recid,
                                                   ln=ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                    'href="%s/help/admin">Admin Area' \
                    '</a> &gt; <a class="navtrail" ' \
                    'href="%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s">'\
                    'Circulation Management' \
                    '</a> ' % (CFG_SITE_SECURE_URL, CFG_SITE_SECURE_URL, ln)

    return page(title=title,
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def create_new_request_step1(req, borrower_id, p="", f="", search=None,
                             ln=CFG_SITE_LANG):
    """
    Create a new request from the borrower's page, step1.

    borrower_id: identify the borrower. It is also the primary key of
                  the table crcBORROWER.

    p: search pattern.

    f: field

    search: search an item.
    """
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    infos = []

    if borrower_id != None:
        borrower = db.get_borrower_details(borrower_id)
    else:
        message = _('Empty borrower ID.')
        return borrower_search(req, message, False, ln)

    if search and p == '':
        infos.append(_('Empty string.') + ' ' + _('Please, try again.'))
        result = ''

    elif search and f == 'barcode':
        p = p.strip('\'" \t')
        has_recid = db.get_id_bibrec(p)

        if has_recid is None:
            infos.append(_('The barcode %(x_strong_tag_open)s%(x_barcode)s%(x_strong_tag_close)s does not exist on BibCirculation database.') % {'x_barcode': p, 'x_strong_tag_open': '<strong>', 'x_strong_tag_close': '</strong>'})
            result = ''
        else:
            result = has_recid

    elif search:
        result = perform_request_search(cc="Books", sc="1", p=p, f=f)

    else:
        result = ''

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    if type(result) is types.IntType or type(result) is types.LongType:
        recid = result
        holdings_information = db.get_holdings_information(recid)
        user_info = db.get_borrower_details(borrower_id)
        body = bc_templates.tmpl_create_new_request_step2(user_info=user_info,
                                    holdings_information=holdings_information,
                                    recid=recid, ln=ln)

    else:
        body = bc_templates.tmpl_create_new_request_step1(borrower=borrower,
                                                          infos=infos,
                                                          result=result,
                                                          p=p,
                                                          f=f,
                                                          ln=ln)

    return page(title=_("New request"),
                uid=id_user,
                req=req,
                body=body, language=ln,
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
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    holdings_information = db.get_holdings_information(recid)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    user_info = db.get_borrower_details(borrower_id)

    body = bc_templates.tmpl_create_new_request_step2(user_info=user_info,
                                    holdings_information=holdings_information,
                                    recid=recid, ln=ln)

    return page(title=_("New request"),
                uid=id_user,
                req=req,
                body=body,
                language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def create_new_request_step3(req, borrower_id, barcode, recid,
                             ln=CFG_SITE_LANG):
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
                              '</a>' % (CFG_SITE_SECURE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    item_info = db.get_item_info(barcode)

    if item_info[6] == 'Reference':
        body = bc_templates.tmpl_book_not_for_loan(ln=ln)
    else:
        body = bc_templates.tmpl_create_new_request_step3(
                                                        borrower_id=borrower_id,
                                                        barcode=barcode,
                                                        recid=recid,
                                                        ln=ln)

    return page(title=_("New request"),
                uid=id_user,
                req=req,
                body=body,
                metaheaderadd = "<link rel=\"stylesheet\" href=\"%s/img/jquery-ui.css\" type=\"text/css\" />" % CFG_SITE_SECURE_URL,
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
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    db.new_hold_request(borrower_id, recid, barcode,
                        period_from, period_to,
                        CFG_BIBCIRCULATION_REQUEST_STATUS_WAITING)

    update_requests_statuses(barcode)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    body = bc_templates.tmpl_create_new_request_step4(ln=ln)

    return page(title=_("New request"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def create_new_loan_step1(req, borrower_id, ln=CFG_SITE_LANG):
    """
    Create a new loan from the borrower's page, step1.

    borrower_id: identify the borrower. It is also the primary key of
                  the table crcBORROWER.
    """

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    infos = []

    borrower = db.get_borrower_details(borrower_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    body = bc_templates.tmpl_create_new_loan_step1(borrower=borrower,
                                                   infos=infos,
                                                   ln=ln)

    return page(title=_("New loan"),
                uid=id_user,
                req=req,
                body=body, language=ln,
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
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)
    #borrower_info = db.get_borrower_data(borrower_id)

    has_recid = db.get_id_bibrec(barcode)
    loan_id = db.is_item_on_loan(barcode)

    if notes:
        notes_format = '[' + time.ctime() + '] ' + notes + '\n'
    else:
        notes_format = ''

    infos = []

    if has_recid is None:
        infos.append(_('%(x_strong_tag_open)s%(x_barcode)s%(x_strong_tag_close)s Unknown barcode.') % {'x_barcode': barcode, 'x_strong_tag_open': '<strong>', 'x_strong_tag_close': '</strong>'} + ' ' + _('Please, try again.'))
        borrower = db.get_borrower_details(borrower_id)
        title = _("New loan")
        body = bc_templates.tmpl_create_new_loan_step1(borrower=borrower,
                                                        infos=infos,
                                                        ln=ln)

    elif loan_id:
        infos.append(_('The item with the barcode %(x_strong_tag_open)s%(x_barcode)s%(x_strong_tag_close)s is on loan.') % {'x_barcode': barcode, 'x_strong_tag_open': '<strong>', 'x_strong_tag_close': '</strong>'})
        borrower = db.get_borrower_details(borrower_id)
        title = _("New loan")
        body = bc_templates.tmpl_create_new_loan_step1(borrower=borrower,
                                                        infos=infos,
                                                        ln=ln)

    else:
        #loaned_on = datetime.date.today()
        due_date = renew_loan_for_X_days(barcode)
        db.new_loan(borrower_id, has_recid, barcode,
                    due_date, CFG_BIBCIRCULATION_LOAN_STATUS_ON_LOAN,
                    'normal', notes_format)
        tag_all_requests_as_done(barcode, borrower_id)
        db.update_item_status(CFG_BIBCIRCULATION_ITEM_STATUS_ON_LOAN, barcode)
        update_requests_statuses(barcode)
        result = db.get_all_loans(20)
        title = _("Current loans")
        infos.append(_('A new loan has been registered with success.'))
        body = bc_templates.tmpl_all_loans(result=result, infos=infos, ln=ln)


    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    return page(title=title,
                uid=id_user,
                req=req,
                body=body,
                language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def all_requests(req, request_id, ln=CFG_SITE_LANG):
    """
    Display all requests.

    @type request_id:   integer.
    @param request_id:  identify the hold request. It is also the primary key
                        of the table crcLOANREQUEST.
    """
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    if request_id:
        db.update_loan_request_status(CFG_BIBCIRCULATION_REQUEST_STATUS_CANCELLED,
                                      request_id)
        result = db.get_all_requests()
    else:
        result = db.get_all_requests()

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    body = bc_templates.tmpl_all_requests(result=result, ln=ln)

    return page(title=_("List of hold requests"),
                uid=id_user,
                req=req,
                body=body, language=ln,
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
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    infos = []

    if msg == 'ok':
        infos.append(_('A new loan has been registered with success.'))

    result = db.get_all_loans(20)

    navtrail_previous_links = '<a class="navtrail" ' \
                    'href="%s/help/admin">Admin Area' \
                    '</a> &gt; <a class="navtrail" ' \
                    'href="%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s">' \
                    'Circulation Management' \
                    '</a> ' % (CFG_SITE_SECURE_URL, CFG_SITE_SECURE_URL, ln)

    body = bc_templates.tmpl_all_loans(result=result, infos=infos, ln=ln)

    return page(title=_("Current loans"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def all_expired_loans(req, ln=CFG_SITE_LANG):
    """
    Display all loans.

    @type loans_per_page:   integer.
    @param loans_per_page:  number of loans per page.

    @return:                list with all expired loans (overdue loans).
    """
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    result = db.get_all_expired_loans()

    infos = []

    navtrail_previous_links = '<a class="navtrail" ' \
                    'href="%s/help/admin">Admin Area' \
                    '</a> &gt; <a class="navtrail" ' \
                    'href="%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s">' \
                    'Circulation Management' \
                    '</a> ' % (CFG_SITE_SECURE_URL, CFG_SITE_SECURE_URL, ln)

    body = bc_templates.tmpl_all_expired_loans(result=result,
                                               infos=infos,
                                               ln=ln)

    return page(title=_('Overdue loans'),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def get_pending_requests(req, request_id, print_data, ln=CFG_SITE_LANG):
    """
    Retrun all loan requests that are pending. If request_id is not None,
    cancel the request and then, return all loan requests that are pending.

    @type request_id:   integer.
    @param request_id:  identify the hold request. It is also the primary key
                        of the table crcLOANREQUEST.

    @type print_data:   string.
    @param print_data:  print requests information.

    @return:            list of pending requests (on shelf with hold).
    """

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    if print_data == 'true':
        return print_pending_hold_requests_information(req, ln)

    elif request_id:
        # Cancel a request too.
        db.update_loan_request_status(CFG_BIBCIRCULATION_REQUEST_STATUS_CANCELLED,
                                      request_id)
        barcode = db.get_request_barcode(request_id)
        update_requests_statuses(barcode)
        result = db.get_loan_request_by_status(CFG_BIBCIRCULATION_REQUEST_STATUS_PENDING)

    else:
        result = db.get_loan_request_by_status(CFG_BIBCIRCULATION_REQUEST_STATUS_PENDING)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    body = bc_templates.tmpl_get_pending_requests(result=result, ln=ln)

    return page(title=_("Items on shelf with holds"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def get_waiting_requests(req, request_id, print_data, ln=CFG_SITE_LANG):
    """
    Get all loans requests that are waiting.

    @type request_id:   integer.
    @param request_id:  identify the hold request. It is also the primary key
                        of the table crcLOANREQUEST.

    @type print_data:   string.
    @param print_data:  print requests information.

    @return:            list of waiting requests (on loan with hold).
    """
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    if print_data == 'true':
        return print_pending_hold_requests_information(req, ln)

    elif request_id:
        db.update_loan_request_status(CFG_BIBCIRCULATION_REQUEST_STATUS_CANCELLED,
                                      request_id)

    result = db.get_loan_request_by_status(CFG_BIBCIRCULATION_REQUEST_STATUS_WAITING)
    aux    = ()

    for request in result:
        if db.get_nb_copies_on_loan(request[1]):
            aux += request,

    result = aux

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    body = bc_templates.tmpl_get_waiting_requests(result=result, ln=ln)

    return page(title=_("Items on loan with holds"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def get_expired_loans_with_waiting_requests(req, request_id, ln=CFG_SITE_LANG):

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    if request_id:
        db.update_loan_request_status(CFG_BIBCIRCULATION_REQUEST_STATUS_CANCELLED,
                                      request_id)
        result = db.get_expired_loans_with_waiting_requests()

    else:
        result = db.get_expired_loans_with_waiting_requests()

    navtrail_previous_links = '<a class="navtrail" ' \
                    'href="%s/help/admin">Admin Area' \
                    '</a> &gt; <a class="navtrail" ' \
                    'href="%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s">'\
                    'Circulation Management' \
                    '</a> ' % (CFG_SITE_SECURE_URL, CFG_SITE_SECURE_URL, ln)

    body = bc_templates.tmpl_get_expired_loans_with_waiting_requests(result=result,
                                                             ln=ln)

    return page(title=_("Overdue loans with holds"),
                uid=id_user,
                req=req,
                body=body, language=ln,
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
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    if delete_key and loan_id:
        if looks_like_dictionary(db.get_loan_notes(loan_id)):
            loans_notes = eval(db.get_loan_notes(loan_id))
            if delete_key in loans_notes.keys():
                del loans_notes[delete_key]
                db.update_loan_notes(loan_id, loans_notes)

    elif library_notes:
        if db.get_loan_notes(loan_id):
            if looks_like_dictionary(db.get_loan_notes(loan_id)):
                loans_notes = eval(db.get_loan_notes(loan_id))
            else:
                loans_notes = {}
        else:
            loans_notes = {}

        note_time = time.strftime("%Y-%m-%d %H:%M:%S")
        if note_time not in loans_notes.keys():
            loans_notes[note_time] = str(library_notes)
            db.update_loan_notes(loan_id, loans_notes)

    loans_notes = db.get_loan_notes(loan_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                    'href="%s/help/admin">Admin Area' \
                    '</a> &gt; <a class="navtrail" ' \
                    'href="%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s">' \
                    'Circulation Management' \
                    '</a> ' % (CFG_SITE_SECURE_URL, CFG_SITE_SECURE_URL, ln)

    referer = req.headers_in.get('referer')

    body = bc_templates.tmpl_get_loans_notes(loans_notes=loans_notes,
                                            loan_id=loan_id,
                                            referer=referer, back=back,
                                            ln=ln)
    return page(title=_("Loan notes"),
                uid=id_user,
                req=req,
                body=body,
                language=ln,
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

    @param new_notes:  note that will be added to the others library's notes.
    """

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    if new_note:
        date = '[' + time.ctime() + '] '
        new_line = '\n'
        new_note = date + new_note + new_line
        db.add_new_loan_note(new_note, loan_id)

    loans_notes = db.get_loan_notes(loan_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    body = bc_templates.tmpl_get_loans_notes(loans_notes=loans_notes,
                                             loan_id=loan_id,
                                             add_notes=add_notes,
                                             ln=ln)
    return page(title=_("Loan notes"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)




###
### Items and their copies' related .
###



def get_item_details(req, recid, ln=CFG_SITE_LANG):
    """
    Display the details of an item.


    @type recid:   integer.
    @param recid:  identify the record. It is also the primary key of
                   the table bibrec.

    @return:       item details.
    """

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    id_user = 1
    infos = []

    if recid == None:
        infos.append(_("Record id not valid"))

    copies = db.get_item_copies_details(recid)
    requests = db.get_item_requests(recid)
    loans = db.get_item_loans(recid)
    purchases = db.get_item_purchases(CFG_BIBCIRCULATION_ACQ_STATUS_NEW, recid)

    req_hist_overview = db.get_item_requests_historical_overview(recid)
    loans_hist_overview = db.get_item_loans_historical_overview(recid)
    purchases_hist_overview = db.get_item_purchases(CFG_BIBCIRCULATION_ACQ_STATUS_RECEIVED, recid)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    body = bc_templates.tmpl_get_item_details(recid=recid,
                                        copies=copies,
                                        requests=requests,
                                        loans=loans,
                                        purchases=purchases,
                                        req_hist_overview=req_hist_overview,
                                        loans_hist_overview=loans_hist_overview,
                                        purchases_hist_overview=purchases_hist_overview,
                                        infos=infos,
                                        ln=ln)

    return page(title=_("Item details"),
                uid=id_user,
                req=req,
                body=body, language=ln,
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
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    if request_id:
        db.cancel_request(request_id)
        update_request_data(request_id)

    result = db.get_item_requests(recid)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    body = bc_templates.tmpl_get_item_requests_details(result=result,
                                                       ln=ln)

    return page(title=_("Hold requests") + \
                        " - %s" % (book_title_from_MARC(recid)),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def get_item_loans_details(req, recid, barcode, loan_id, force,
                           ln=CFG_SITE_LANG):
    """
    Show all the details about all current loans related with a record.

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
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    infos = []

    if loan_id and barcode and force == 'true':
        new_due_date = renew_loan_for_X_days(barcode)
        #db.update_due_date(loan_id, new_due_date)
        db.renew_loan(loan_id, new_due_date)
        update_status_if_expired(loan_id)
        infos.append(_("Loan renewed with success."))

    elif barcode:
        recid = db.get_id_bibrec(barcode)
        item_description = db.get_item_description(barcode)
        queue = db.get_queue_request(recid, item_description)
        new_due_date = renew_loan_for_X_days(barcode)


        force_renew_link = create_html_link(CFG_SITE_SECURE_URL +
                        '/admin2/bibcirculation/get_item_loans_details',
                       {'barcode': barcode, 'loan_id': loan_id, 'force': 'true',
                       'recid': recid, 'ln': ln}, (_("Yes")))

        no_renew_link = create_html_link(CFG_SITE_SECURE_URL +
                        '/admin2/bibcirculation/get_item_loans_details',
                        {'recid': recid, 'ln': ln},
                        (_("No")))

        if len(queue) != 0:
            title = book_title_from_MARC(recid)
            message = _("Another user is waiting for this book %(x_strong_tag_open)s%(x_title)s%(x_strong_tag_close)s.") % {'x_title': title, 'x_strong_tag_open': '<strong>', 'x_strong_tag_close': '</strong>'}
            message += '\n\n'
            message += _("Do you want renew this loan anyway?")
            message += '\n\n'
            message += "[%s] [%s]" % (force_renew_link, no_renew_link)
            infos.append(message)
        else:
            db.renew_loan(loan_id, new_due_date)
            #db.update_due_date(loan_id, new_due_date)
            update_status_if_expired(loan_id)
            infos.append(_("Loan renewed with success."))

    result = db.get_item_loans(recid)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    body = bc_templates.tmpl_get_item_loans_details(result=result,
                                                                recid=recid,
                                                                infos=infos,
                                                                ln=ln)

    return page(title=_("Loans details") + \
                        " - %s" % (book_title_from_MARC(int(recid))),
                uid=id_user,
                req=req,
                body=body, language=ln,
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
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    req_hist_overview = db.get_item_requests_historical_overview(recid)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    body = bc_templates.tmpl_get_item_req_historical_overview(
                                            req_hist_overview=req_hist_overview,
                                            ln=ln)

    return page(title=_("Requests") + " - " + _("historical overview"),
                uid=id_user,
                req=req,
                body=body, language=ln,
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
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    loans_hist_overview = db.get_item_loans_historical_overview(recid)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    body = bc_templates.tmpl_get_item_loans_historical_overview(
                                        loans_hist_overview=loans_hist_overview,
                                        ln=ln)

    return page(title=_("Loans") + " - " + _("historical overview"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def add_new_copy_step1(req, ln=CFG_SITE_LANG):
    """
    Add a new copy.
    """

    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    body = bc_templates.tmpl_add_new_copy_step1(ln)

    return page(title=_("Add new copy") + " - I",
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def add_new_copy_step2(req, p, f, ln=CFG_SITE_LANG):
    """
    Add a new copy.
    """
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    result = perform_request_search(cc="Books", sc="1", p=p, f=f)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    body = bc_templates.tmpl_add_new_copy_step2(result=result, ln=ln)

    return page(title=_("Add new copy") + " - II",
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def add_new_copy_step3(req, recid, barcode, ln=CFG_SITE_LANG):
    """
    Add a new copy.
    """
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    infos = []
    result = db.get_item_copies_details(recid)
    libraries = db.get_internal_libraries()

    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    if barcode is not None:
        if not db.barcode_in_use(barcode):
            barcode = None

    tmp_barcode = generate_tmp_barcode()

    body = bc_templates.tmpl_add_new_copy_step3(recid=recid,
                                                result=result,
                                                libraries=libraries,
                                                original_copy_barcode=barcode,
                                                tmp_barcode=tmp_barcode,
                                                infos=infos,
                                                ln=ln)

    return page(title=_("Add new copy") + " - III",
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def add_new_copy_step4(req, barcode, library, location, collection, description,
                       loan_period, status, expected_arrival_date, recid,
                       ln=CFG_SITE_LANG):

    """
    Add a new copy.
    """
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    infos = []

    result = db.get_item_copies_details(recid)
    libraries = db.get_internal_libraries()

    if db.barcode_in_use(barcode):
        infos.append(_("The given barcode <strong>%s</strong> is already in use." % barcode))
        title = _("Add new copy") + " - III"
        body  = bc_templates.tmpl_add_new_copy_step3(recid=recid,
                                                    result=result,
                                                    libraries=libraries,
                                                    original_copy_barcode=None,
                                                    tmp_barcode=None,
                                                    infos=infos,
                                                    ln=ln)
    elif not barcode:
        infos.append(_("The given barcode is empty."))
        title = _("Add new copy") + " - III"
        body  = bc_templates.tmpl_add_new_copy_step3(recid=recid,
                                                    result=result,
                                                    libraries=libraries,
                                                    original_copy_barcode=None,
                                                    tmp_barcode=None,
                                                    infos=infos,
                                                    ln=ln)
    elif barcode[:3] == 'tmp' \
        and status in [CFG_BIBCIRCULATION_ITEM_STATUS_ON_SHELF,
                       CFG_BIBCIRCULATION_ITEM_STATUS_ON_LOAN,
                       CFG_BIBCIRCULATION_ITEM_STATUS_IN_PROCESS]:
        infos.append(_("The status selected does not accept tamporary barcodes."))
        title = _("Add new copy") + " - III"
        tmp_barcode = generate_tmp_barcode()
        body  = bc_templates.tmpl_add_new_copy_step3(recid=recid,
                                                    result=result,
                                                    libraries=libraries,
                                                    original_copy_barcode=None,
                                                    tmp_barcode=tmp_barcode,
                                                    infos=infos,
                                                    ln=ln)


    else:
        library_name = db.get_library_name(library)
        tup_infos = (barcode, library, library_name, location, collection,
                     description, loan_period, status, expected_arrival_date,
                     recid)
        title = _("Add new copy") + " - IV"
        body  = bc_templates.tmpl_add_new_copy_step4(tup_infos=tup_infos, ln=ln)

    return page(title=title,
                uid=id_user,
                req=req,
                body=body,
                metaheaderadd='<link rel="stylesheet" href="%s/img/jquery-ui.css" '\
                                'type="text/css" />' % CFG_SITE_SECURE_URL,
                language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def add_new_copy_step5(req, barcode, library, location, collection, description,
                        loan_period, status, expected_arrival_date, recid,
                        ln=CFG_SITE_LANG):
    """
    Add a new copy.
    """
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    infos = []
    if not db.barcode_in_use(barcode):
        db.add_new_copy(barcode, recid, library, collection, location, description.strip() or '-',
                        loan_period, status, expected_arrival_date)
        update_requests_statuses(barcode)
    else:
        infos.append(_("The given barcode <strong>%s</strong> is already in use.") % barcode)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    body = bc_templates.tmpl_add_new_copy_step5(infos=infos, recid=recid, ln=ln)

    return page(title=_("Add new copy") + " - V",
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def delete_copy_step1(req, barcode, ln):
    #id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    infos = []

    navtrail_previous_links = '<a class="navtrail" ' \
                                 'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    barcode = barcode.strip('\'" \t')
    recid = db.get_id_bibrec(barcode)
    if recid:
        #recid = recid[0]

        infos.append(_("Do you really want to delete this copy of the book?"))

        copies = db.get_item_copies_details(recid)

        title = _("Delete copy")
        body = bc_templates.tmpl_delete_copy_step1(barcode_to_delete=barcode,
                                                   recid=recid,
                                                   result=copies,
                                                   infos=infos,
                                                   ln=ln)

    else:
        message = _("""The barcode <strong>%s</strong> was not found""") % (barcode)
        infos.append(message)
        title = _("Item search")
        body = bc_templates.tmpl_item_search(infos=infos, ln=ln)

    return page(title=title,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def delete_copy_step2(req, barcode, ln):

    #id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    infos = []

    barcode = barcode.strip('\'" \t')
    recid = db.get_id_bibrec(barcode)

    if recid:
        #recid = recid[0]

        if db.delete_copy(barcode)==1:
            message = _("The copy with barcode <strong>%s</strong> has been deleted.") % (barcode)
        else:
            message = _('It was NOT possible to delete the copy with barcode <strong>%s</strong>') % (barcode)

        infos.append(message)

        copies = db.get_item_copies_details(recid)
        requests = db.get_item_requests(recid)
        loans = db.get_item_loans(recid)
        purchases = db.get_item_purchases(CFG_BIBCIRCULATION_ACQ_STATUS_NEW, recid)

        req_hist_overview = db.get_item_requests_historical_overview(recid)
        loans_hist_overview = db.get_item_loans_historical_overview(recid)
        purchases_hist_overview = db.get_item_purchases(CFG_BIBCIRCULATION_ACQ_STATUS_RECEIVED, recid)

        title = _("Item details")
        body = bc_templates.tmpl_get_item_details(
                                        recid=recid, copies=copies,
                                        requests=requests, loans=loans,
                                        purchases=purchases,
                                        req_hist_overview=req_hist_overview,
                                        loans_hist_overview=loans_hist_overview,
                                        purchases_hist_overview=purchases_hist_overview,
                                        infos=infos, ln=ln)

    else:
        message = _("The barcode <strong>%s</strong> was not found") % (barcode)
        infos.append(message)
        title = _("Item search")
        body = bc_templates.tmpl_item_search(infos=infos, ln=ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)
    return page(title=title,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def update_item_info_step1(req, ln=CFG_SITE_LANG):
    """
    Update the item's information.
    """

    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    body = bc_templates.tmpl_update_item_info_step1(ln=ln)

    return page(title=_("Update item information"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_item_info_step2(req, p, f, ln=CFG_SITE_LANG):
    """
    Update the item's information.
    """

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    result = perform_request_search(cc="Books", sc="1", p=p, f=f)

    body = bc_templates.tmpl_update_item_info_step2(result=result, ln=ln)

    return page(title="Update item information",
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_item_info_step3(req, recid, ln=CFG_SITE_LANG):
    """
    Update the item's information.
    """

    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    result = db.get_item_copies_details(recid)

    body = bc_templates.tmpl_update_item_info_step3(recid=recid, result=result,
                                                    ln=ln)

    return page(title=_("Update item information"),
                uid=id_user,
                req=req,
                body=body,
                language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_item_info_step4(req, barcode, ln=CFG_SITE_LANG):
    """
    Update the item's information.
    """
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    recid = db.get_id_bibrec(barcode)
    result = db.get_item_info(barcode)
    libraries = db.get_internal_libraries()
    libraries += db.get_hidden_libraries()

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    if recid == None:
        _ = gettext_set_language(ln)
        infos = []
        infos.append(_("Barcode <strong>%s</strong> not found" % barcode))
        return item_search(req, infos, ln)


    body = bc_templates.tmpl_update_item_info_step4(recid=recid,
                                                    result=result,
                                                    libraries=libraries,
                                                    ln=ln)

    return page(title=_("Update item information"),
                uid=id_user,
                req=req,
                body=body,
                language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_item_info_step5(req, barcode, old_barcode, library, location,
                           collection, description, loan_period, status,
                           expected_arrival_date, recid, ln=CFG_SITE_LANG):

    """
    Update the item's information.
    """
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    library_name = db.get_library_name(library)
    tup_infos = (barcode, old_barcode, library, library_name, location,
                 collection, description, loan_period, status,
                 expected_arrival_date, recid)

    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    body = bc_templates.tmpl_update_item_info_step5(tup_infos=tup_infos, ln=ln)

    return page(title=_("Update item information"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_item_info_step6(req, tup_infos, ln=CFG_SITE_LANG):
    """
    Update the item's information.
    """
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    infos = []

    # tuple containing information for the update process.
    (barcode, old_barcode, library_id, location, collection,
     description, loan_period, status, expected_arrival_date, recid) = tup_infos

    is_on_loan = db.is_on_loan(old_barcode)
    #is_requested = db.is_requested(old_barcode)

    # if item on loan and new status is CFG_BIBCIRCULATION_ITEM_STATUS_ON_SHELF,
    # item has to be returned.
    if is_on_loan and status == CFG_BIBCIRCULATION_ITEM_STATUS_ON_SHELF:
        db.update_item_status(CFG_BIBCIRCULATION_ITEM_STATUS_ON_SHELF, old_barcode)
        db.return_loan(old_barcode)

    if not is_on_loan and status == CFG_BIBCIRCULATION_ITEM_STATUS_ON_LOAN:
        status = db.get_copy_details(barcode)[7]
        infos.append(_("Item <strong>[%s]</strong> updated, but the <strong>status was not modified</strong>.") % (old_barcode))

    # update item information.
    db.update_item_info(old_barcode, library_id, collection, location, description.strip(),
                        loan_period, status, expected_arrival_date)
    update_requests_statuses(old_barcode)
    navtrail_previous_links = '<a class="navtrail"' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    if barcode != old_barcode:
        if db.barcode_in_use(barcode):
            infos.append(_("Item <strong>[%s]</strong> updated, but the <strong>barcode was not modified</strong> because it is already in use.") % (old_barcode))
        else:
            if db.update_barcode(old_barcode, barcode):
                infos.append(_("Item <strong>[%s]</strong> updated to <strong>[%s]</strong> with success.") % (old_barcode, barcode))
            else:
                infos.append(_("Item <strong>[%s]</strong> updated, but the <strong>barcode was not modified</strong> because it was not found (!?).") % (old_barcode))

        copies = db.get_item_copies_details(recid)
        requests = db.get_item_requests(recid)
        loans = db.get_item_loans(recid)
        purchases = db.get_item_purchases(CFG_BIBCIRCULATION_ACQ_STATUS_NEW, recid)

        req_hist_overview = db.get_item_requests_historical_overview(recid)
        loans_hist_overview = db.get_item_loans_historical_overview(recid)
        purchases_hist_overview = db.get_item_purchases(CFG_BIBCIRCULATION_ACQ_STATUS_RECEIVED, recid)

        body = bc_templates.tmpl_get_item_details(recid=recid,
                                            copies=copies,
                                            requests=requests,
                                            loans=loans,
                                            purchases=purchases,
                                            req_hist_overview=req_hist_overview,
                                            loans_hist_overview=loans_hist_overview,
                                            purchases_hist_overview=purchases_hist_overview,
                                            infos=infos,
                                            ln=ln)

        return page(title=_("Update item information"),
                    uid=id_user,
                    req=req,
                    body=body, language=ln,
                    navtrail=navtrail_previous_links,
                    lastupdated=__lastupdated__)

    else:
        return redirect_to_url(req, CFG_SITE_SECURE_URL +
                                    "/record/edit/#state=edit&recid=" + str(recid))

def item_search(req, infos=[], ln=CFG_SITE_LANG):
    """
    Display a form where is possible to searh for an item.
    """

    navtrail_previous_links = '<a class="navtrail" ' \
                    'href="%s/help/admin">Admin Area' \
                    '</a> &gt; <a class="navtrail" ' \
                    'href="%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s">' \
                    'Circulation Management' \
                    '</a> ' % (CFG_SITE_SECURE_URL, CFG_SITE_SECURE_URL, ln)

    _ = gettext_set_language(ln)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bc_templates.tmpl_item_search(infos=infos, ln=ln)

    return page(title=_("Item search"),
                uid=id_user,
                req=req,
                body=body, language=ln,
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

    """

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    infos = []

    if p == '':
        infos.append(_('Empty string.') + ' ' + _('Please, try again.'))
        return item_search(req, infos, ln)

    if f == 'barcode':
        p = p.strip('\'" \t')
        recid = db.get_id_bibrec(p)

        if recid is None:
            infos.append(_('The barcode %(x_strong_tag_open)s%(x_barcode)s%(x_strong_tag_close)s does not exist on BibCirculation database.') % {'x_barcode': p, 'x_strong_tag_open': '<strong>', 'x_strong_tag_close': '</strong>'})
            body = bc_templates.tmpl_item_search(infos=infos, ln=ln)
        else:
            return get_item_details(req, recid, ln=ln)

    elif f == 'recid':
        p = p.strip('\'" \t')
        recid = p

        if not record_exists(recid):
            infos.append(_("Requested record does not seem to exist."))
            body = bc_templates.tmpl_item_search(infos=infos, ln=ln)
        else:
            return get_item_details(req, recid, ln=ln)

    else:
        result = perform_request_search(cc="Books", sc="1", p=p, f=f)
        body = bc_templates.tmpl_item_search_result(result=result, ln=ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                    'href="%s/help/admin">Admin Area' \
                    '</a> &gt; <a class="navtrail" ' \
                    'href="%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s">' \
                    'Circulation Management' \
                    '</a> ' % (CFG_SITE_SECURE_URL, CFG_SITE_SECURE_URL, ln)

    return page(title=_("Item search result"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)




###
### "Borrower" related templates
###



def get_borrower_details(req, borrower_id, update, ln=CFG_SITE_LANG):
    """
    Display the details of a borrower.

    @type borrower_id:   integer.
    @param borrower_id:  identify the borrower. It is also the primary key of
                         the table crcBORROWER.
    """

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    if update and CFG_CERN_SITE:
        update_user_info_from_ldap(borrower_id)

    borrower = db.get_borrower_details(borrower_id)
    if borrower == None:
        info = _('Borrower not found.') + ' ' + _('Please, try again.')
        return borrower_search(req, info, False, ln)

    else:
        requests = db.get_borrower_request_details(borrower_id)
        loans = db.get_borrower_loan_details(borrower_id)
        notes = db.get_borrower_notes(borrower_id)
        ill = db.get_ill_requests_details(borrower_id)
        proposals = db.get_proposal_requests_details(borrower_id)

        req_hist = db.bor_requests_historical_overview(borrower_id)
        loans_hist = db.bor_loans_historical_overview(borrower_id)
        ill_hist = db.bor_ill_historical_overview(borrower_id)
        proposal_hist = db.bor_proposal_historical_overview(borrower_id)

        navtrail_previous_links = '<a class="navtrail" ' \
                                  'href="%s/help/admin">Admin Area' \
                                  '</a>' % (CFG_SITE_SECURE_URL,)

        body = bc_templates.tmpl_borrower_details(borrower=borrower,
                                                  requests=requests,
                                                  loans=loans,
                                                  notes=notes,
                                                  ill=ill,
                                                  proposals=proposals,
                                                  req_hist=req_hist,
                                                  loans_hist=loans_hist,
                                                  ill_hist=ill_hist,
                                                  proposal_hist=proposal_hist,
                                                  ln=ln)

        return page(title=_("Borrower details"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def add_new_borrower_step1(req, ln=CFG_SITE_LANG):
    """
    Add new borrower. Step 1
    """
    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    body = bc_templates.tmpl_add_new_borrower_step1(ln=ln)

    return page(title=_("Add new borrower") + " - I",
                uid=id_user,
                req=req,
                body=body, language=ln,
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

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    infos = []

    if name == '':
        infos.append(_("Please, insert a name"))

    if email == '':
        infos.append(_("Please, insert a valid email address"))
    else:
        borrower_id = db.get_borrower_id_by_email(email)
        if borrower_id is not None:
            infos.append(_("There is already a borrower using the following email:")
                         + " <strong>%s</strong>" % (email))

    tup_infos = (name, email, phone, address, mailbox, notes)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    if len(infos) > 0:
        body = bc_templates.tmpl_add_new_borrower_step1(tup_infos=tup_infos,
                                                        infos=infos, ln=ln)
        title = _("Add new borrower") + " - I"
    else:
        if notes != '':
            borrower_notes = {}
            note_time = time.strftime("%Y-%m-%d %H:%M:%S")
            borrower_notes[note_time] = notes
        else:
            borrower_notes = ''

        borrower_id = db.new_borrower(None, name, email, phone,
                                      address, mailbox, borrower_notes)

        return redirect_to_url(req,
            '%s/admin2/bibcirculation/get_borrower_details?ln=%s&borrower_id=%s' \
                                            % (CFG_SITE_SECURE_URL, ln, borrower_id))


        #body = bc_templates.tmpl_add_new_borrower_step2(tup_infos=tup_infos,
        #                                                infos=infos, ln=ln)
        #title = _("Add new borrower") + " - II"

    return page(title=title,
                uid=id_user,
                req=req,
                body=body,
                language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def add_new_borrower_step3(req, tup_infos, ln=CFG_SITE_LANG):
    """
    Add new borrower. Step 3.

    @type tup_infos:   tuple.
    @param tup_infos:  tuple containing borrower information.
    """
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    if tup_infos[5] != '':
        borrower_notes = {}
        note_time = time.strftime("%Y-%m-%d %H:%M:%S")
        borrower_notes[note_time] = str(tup_infos[5])
    else:
        borrower_notes = ''

    db.new_borrower(None, tup_infos[0], tup_infos[1], tup_infos[2],
                    tup_infos[3], tup_infos[4], str(borrower_notes))

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    body = bc_templates.tmpl_add_new_borrower_step3(ln=ln)

    return page(title=_("Add new borrower") + " - III",
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_borrower_info_step1(req, borrower_id, ln=CFG_SITE_LANG):
    """
    Update the borrower's information.

    @param borrower_id:  identify the borrower. It is also the primary key of
                  the table crcBORROWER.
    """

    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    borrower_details = db.get_borrower_details(borrower_id)

    tup_infos = (borrower_details[0], borrower_details[2], borrower_details[3],
                 borrower_details[4], borrower_details[5], borrower_details[6])

    body = bc_templates.tmpl_update_borrower_info_step1(tup_infos=tup_infos,
                                                        ln=ln)

    return page(title=_("Update borrower information"),
                uid=id_user,
                req=req,
                body=body,
                language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_borrower_info_step2(req, borrower_id, name, email, phone, address,
                               mailbox, ln=CFG_SITE_LANG):
    """
    Update the borrower's information.
    """

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    infos = []

    if name == '':
        infos.append(_("Please, insert a name"))

    if email == '':
        infos.append(_("Please, insert a valid email address"))
    else:
        borrower_email_id = db.get_borrower_id_by_email(email)
        if borrower_email_id is not None and borrower_id != borrower_email_id:
            infos.append(_("There is already a borrower using the following email:")
                         + " <strong>%s</strong>" % (email))

    tup_infos = (borrower_id, name, email, phone, address, mailbox)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    if len(infos) > 0:
        body = bc_templates.tmpl_update_borrower_info_step1(tup_infos=tup_infos,
                                                        infos=infos, ln=ln)
    else:
        db.update_borrower_info(borrower_id, name, email,
                                phone, address, mailbox)

        return redirect_to_url(req,
            '%s/admin2/bibcirculation/get_borrower_details?ln=%s&borrower_id=%s' \
                                            % (CFG_SITE_SECURE_URL, ln, borrower_id))

    return page(title=_("Update borrower information"),
                uid=id_user,
                req=req,
                body=body,
                language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def get_borrower_requests_details(req, borrower_id, request_id,
                                  ln=CFG_SITE_LANG):
    """
    Display loans details of a borrower.

    @type borrower_id:  integer.
    @param borrower_id: identify the borrower. It is also the primary key of
                        the table crcBORROWER.

    @type request_id:   integer.
    @param request_id:  identify the hold request to be cancelled

    @return:            borrower requests details.
    """
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    if request_id:
        db.cancel_request(request_id)
        update_request_data(request_id)

    result = db.get_borrower_request_details(borrower_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    name = db.get_borrower_name(borrower_id)

    title = _("Hold requests details") + " - %s" % (name)
    body = bc_templates.tmpl_borrower_request_details(result=result,
                                                      borrower_id=borrower_id,
                                                      ln=ln)

    return page(title=title,
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def get_borrower_loans_details(req, recid, barcode, borrower_id,
                               renewal, force, loan_id, ln=CFG_SITE_LANG):
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

    @type renewal:      string.
    @param renewal:     renew all loans.

    @type force:         string.
    @param force:        force the renew of a loan, when usually this is not possible.

    @type loan_id:       integer.
    @param loan_id:      identify a loan. It is the primery key of the table
                         crcLOAN.

    @return:             borrower loans details.
    """

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    infos = []

    force_renew_link = create_html_link(CFG_SITE_SECURE_URL +
                        '/admin2/bibcirculation/get_borrower_loans_details',
                        {'barcode': barcode, 'borrower_id': borrower_id,
                         'loan_id': loan_id, 'force': 'true', 'ln': ln},
                        (_("Yes")))

    no_renew_link = create_html_link(CFG_SITE_SECURE_URL +
                        '/admin2/bibcirculation/get_borrower_loans_details',
                        {'borrower_id': borrower_id, 'ln': ln},
                        (_("No")))

    if barcode and loan_id and recid:
        item_description = db.get_item_description(barcode)
        queue = db.get_queue_request(recid, item_description)
        new_due_date = renew_loan_for_X_days(barcode)

        if len(queue) != 0:
            title = book_title_from_MARC(recid)
            message = _("Another user is waiting for this book %(x_strong_tag_open)s%(x_title)s%(x_strong_tag_close)s.") % {'x_title': title, 'x_strong_tag_open': '<strong>', 'x_strong_tag_close': '</strong>'}
            message += '\n\n'
            message += _("Do you want renew this loan anyway?")
            message += '\n\n'
            message += "[%s] [%s]" % (force_renew_link, no_renew_link)
            infos.append(message)

        else:
            #db.update_due_date(loan_id, new_due_date)
            db.renew_loan(loan_id, new_due_date)
            #update_status_if_expired(loan_id)
            infos.append(_("Loan renewed with success."))

    elif loan_id and barcode and force == 'true':
        new_due_date = renew_loan_for_X_days(barcode)
        db.renew_loan(loan_id, new_due_date)
        update_status_if_expired(loan_id)
        infos.append(_("Loan renewed with success."))

    elif borrower_id and renewal=='true':
        list_of_loans = db.get_recid_borrower_loans(borrower_id)
        for (loan_id, recid, barcode) in list_of_loans:
            item_description = db.get_item_description(barcode)
            queue = db.get_queue_request(recid, item_description)
            new_due_date = renew_loan_for_X_days(barcode)

            force_renewall_link = create_html_link(CFG_SITE_SECURE_URL +
                            '/admin2/bibcirculation/get_borrower_loans_details',
                            {'barcode': barcode, 'borrower_id': borrower_id,
                            'loan_id': loan_id, 'force': 'true', 'ln': ln},
                            (_("Yes")))

            if len(queue) != 0:
                title = book_title_from_MARC(recid)
                message = _("Another user is waiting for this book %(x_strong_tag_open)s%(x_title)s%(x_strong_tag_close)s.") % {'x_title': title, 'x_strong_tag_open': '<strong>', 'x_strong_tag_close': '</strong>'}
                message += '\n\n'
                message += _("Do you want renew this loan anyway?")
                message += '\n\n'
                message += "[%s] [%s]" % (force_renewall_link, no_renew_link)
                infos.append(message)

            else:
                db.renew_loan(loan_id, new_due_date)
                update_status_if_expired(loan_id)

        if infos == []:
            infos.append(_("All loans renewed with success."))

    borrower_loans = db.get_borrower_loan_details(borrower_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    body = bc_templates.tmpl_borrower_loans_details(
                                                borrower_loans=borrower_loans,
                                                borrower_id=borrower_id,
                                                infos=infos, ln=ln)

    return page(title=_("Loans details") + \
                        " - %s" %(db.get_borrower_name(borrower_id)),
                uid=id_user,
                req=req,
                body=body, language=ln,
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
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    loans_hist_overview = db.bor_loans_historical_overview(borrower_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    body = bc_templates.tmpl_bor_loans_historical_overview(
        loans_hist_overview = loans_hist_overview,
        ln=ln)

    return page(title=_("Loans") + " - " + _("historical overview"),
                uid=id_user,
                req=req,
                body=body, language=ln,
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

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    req_hist_overview = db.bor_requests_historical_overview(borrower_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    body = bc_templates.tmpl_bor_requests_historical_overview(
        req_hist_overview = req_hist_overview,
        ln=ln)

    return page(title=_("Requests") + " - " + _("historical overview"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def get_borrower_ill_details(req, borrower_id, request_type='', ln=CFG_SITE_LANG):
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

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    if request_type == 'proposal-book':
        result = db.get_proposal_requests_details(borrower_id)
    else:
        result = db.get_ill_requests_details(borrower_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    name = db.get_borrower_name(borrower_id)

    title = _("ILL details") + "- %s" % (name)
    body = bc_templates.tmpl_borrower_ill_details(result=result,
                                                  borrower_id=borrower_id,
                                                  ln=ln)

    return page(title=title,
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def bor_ill_historical_overview(req, borrower_id, request_type='', ln=CFG_SITE_LANG):

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    if request_type == 'proposal-book':
        result = db.bor_proposal_historical_overview(borrower_id)
    else:
        result = db.bor_ill_historical_overview(borrower_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    name = db.get_borrower_name(borrower_id)

    title = _("ILL historical overview") + " - %s" % (name)
    body = bc_templates.tmpl_borrower_ill_details(result=result,
                                                  borrower_id=borrower_id,
                                                  ln=ln)

    return page(title=title,
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)



def borrower_notification(req, borrower_id, template, message, load_msg_template,
                          subject, send_message, from_address, ln=CFG_SITE_LANG):
    """
    Send an email to a borrower or simply load and display an editable email
    template.

    @type borrower_id:   integer.
    @param borrower_id:  identify the borrower. It is also the primary key of
                         the table crcBORROWER.

    @type borrower_email:   string.
    @param borrower_email:  The librarian can change the email manually.
                            In that case, this value will be taken instead
                            of the that in borrower details.

    @type template:      string.
    @param template:     The name of the notification template to be loaded.
                         If the @param load_msg_template holds True, the
                         template is not loaded.

    @type message:       string.
    @param message:      Message to be sent if the flag @param send_message is set.

    @type subject:       string.
    @param subject:      Subject of the message.

    @type from_address:  string.
    @param from_address: From address in the message sent.

    @return:             Display the email template or send an email to a borrower.
    """
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    email = db.get_borrower_email(borrower_id)

    if load_msg_template == 'False' and template is not None:
        # Do not load the template. It is the email body itself.
        body = bc_templates.tmpl_borrower_notification(email=email,
                                                       subject=subject,
                                                       email_body=template,
                                                       borrower_id=borrower_id,
                                                       from_address=from_address,
                                                       ln=ln)

    elif send_message:
        send_email(fromaddr = from_address,
                   toaddr   = email,
                   subject  = subject,
                   content  = message,
                   header   = '',
                   footer   = '',
                   attempt_times = 1,
                   attempt_sleeptime = 10
                   )
        body = bc_templates.tmpl_send_notification(ln=ln)

    else:
        show_template = load_template(template)
        body = bc_templates.tmpl_borrower_notification(email=email,
                                                       subject=subject,
                                                       email_body=show_template,
                                                       borrower_id=borrower_id,
                                                       from_address=from_address,
                                                       ln=ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                    'href="%s/help/admin">Admin Area' \
                    '</a> &gt; <a class="navtrail" ' \
                    'href="%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s">' \
                    'Circulation Management' \
                    '</a> ' % (CFG_SITE_SECURE_URL, CFG_SITE_SECURE_URL, ln)

    return page(title="User Notification",
                 uid=id_user,
                 req=req,
                 body=body, language=ln,
                 navtrail=navtrail_previous_links,
                 lastupdated=__lastupdated__)

def get_borrower_notes(req, borrower_id, delete_key, library_notes,
                       ln=CFG_SITE_LANG):
    """
    Retrieve the notes of a borrower.

    @type borrower_id:    integer.
    @param borrower_id:   identify the borrower. It is also the primary key of
                          the table crcBORROWER.

   """
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    if delete_key and borrower_id:
        if looks_like_dictionary(db.get_borrower_notes(borrower_id)):
            borrower_notes = eval(db.get_borrower_notes(borrower_id))
            if delete_key in borrower_notes.keys():
                del borrower_notes[delete_key]
                db.update_borrower_notes(borrower_id, borrower_notes)

    elif library_notes:
        if db.get_borrower_notes(borrower_id):
            if looks_like_dictionary(db.get_borrower_notes(borrower_id)):
                borrower_notes = eval(db.get_borrower_notes(borrower_id))
            else:
                borrower_notes = {}
        else:
            borrower_notes = {}

        note_time = time.strftime("%Y-%m-%d %H:%M:%S")
        if note_time not in borrower_notes.keys():
            borrower_notes[note_time] = str(library_notes)
            db.update_borrower_notes(borrower_id, borrower_notes)

    borrower_notes = db.get_borrower_notes(borrower_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                    'href="%s/help/admin">Admin Area' \
                    '</a> &gt; <a class="navtrail" ' \
                    'href="%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s">' \
                    'Circulation Management' \
                    '</a> ' % (CFG_SITE_SECURE_URL, CFG_SITE_SECURE_URL, ln)

    body = bc_templates.tmpl_borrower_notes(borrower_notes=borrower_notes,
                                            borrower_id=borrower_id,
                                            ln=ln)

    return page(title=_("Borrower notes"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def borrower_search(req, empty_barcode, redirect_to_new_request=False,
                    ln=CFG_SITE_LANG):
    """
    Page (for administrator) where is it possible to search
    for a borrower (who is on crcBORROWER table) using his/her name,
    email, phone or id.

    If redirect_to_new_request is False, the returned page will be "Borrower details"
    If redirect_to_new_request is True,  the returned page will be "New Request"
    """

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    infos = []

    if empty_barcode:
        infos.append(empty_barcode)

    navtrail_previous_links = '<a class="navtrail" ' \
                    'href="%s/help/admin">Admin Area' \
                    '</a> &gt; <a class="navtrail" ' \
                    'href="%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s">' \
                    'Circulation Management' \
                    '</a> ' % (CFG_SITE_SECURE_URL, CFG_SITE_SECURE_URL, ln)

    body = bc_templates.tmpl_borrower_search(infos=infos,
                                redirect_to_new_request=redirect_to_new_request,
                                ln=ln)

    if redirect_to_new_request:
        title = _("New Request")
    else:
        title = _("Borrower Search")

    return page(title=title,
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def borrower_search_result(req, column, string, redirect_to_new_request=False,
                           ln=CFG_SITE_LANG):
    """
    Search a borrower and return a list with all the possible results.

    @type column:  string
    @param column: identify the column, of the table crcBORROWER, that will be
                   considered during the search. Can be 'name', 'email' or 'id'.

    @type string:  string
    @param string: string used for the search process.

    If redirect_to_new_request is True,  the returned page will be "Borrower details"
    If redirect_to_new_request is False, the returned page will be "New Request"

    """

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    if string == '':
        message = _('Empty string.') + ' ' + _('Please, try again.')
        return borrower_search(req, message, redirect_to_new_request, ln)
    else:
        result = search_user(column, string)

    navtrail_previous_links = '<a class="navtrail" ' \
                'href="%s/help/admin">Admin Area' \
                '</a> &gt; <a class="navtrail" ' \
                'href="%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s">' \
                'Circulation Management' \
                '</a> ' % (CFG_SITE_SECURE_URL, CFG_SITE_SECURE_URL, ln)

    if len(result) == 1:
        if redirect_to_new_request:
            return create_new_request_step1(req, result[0][0])

        else:
            return get_borrower_details(req, result[0][0], False, ln)
            #return create_new_request_step1(req, borrower_id, p, f, search, ln)
    else:
        body = bc_templates.tmpl_borrower_search_result(result=result,
                                redirect_to_new_request=redirect_to_new_request,
                                ln=ln)

        return page(title=_("Borrower search result"),
                    uid=id_user,
                    req=req,
                    body=body,
                    language=ln,
                    navtrail=navtrail_previous_links,
                    lastupdated=__lastupdated__)




###
### ILL/Purchase/Acquisition related functions.
### Naming of the methods is not intuitive. Should be improved
### and appropriate documentation added, when required.
### Also, methods could be refactored.
###




def register_ill_from_proposal(req, ill_request_id, bor_id=None, ln=CFG_SITE_LANG):

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    book_info = db.get_ill_book_info(ill_request_id)

    infos = []
    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    if looks_like_dictionary(book_info):
        book_info = eval(book_info)
        if not bor_id:
            bid = db.get_ill_borrower(ill_request_id)
        else:
            bid = bor_id

        if book_info.has_key('recid') and bid:
            recid = book_info['recid']
            if not db.has_loan_request(bid, recid, ill=1):
                db.tag_requests_as_done(bid, recid=recid)
                library_notes = {}
                library_notes[time.strftime("%Y-%m-%d %H:%M:%S")] = \
                                    _("This ILL has been created from a proposal.")
                db.register_ill_from_proposal(ill_request_id,
                                              bid, library_notes)
                infos.append(_('An ILL has been created for the user.'))
            else:
                infos.append(_('An active ILL already exists for this user on this record.'))
        else:
            infos.append(_('Could not create an ILL from the proposal'))
    else:
        infos.append(_('Could not create an ILL from the proposal'))

    ill_req = db.get_ill_requests(CFG_BIBCIRCULATION_ILL_STATUS_NEW)
    body = bc_templates.tmpl_list_ill(ill_req, infos=infos, ln=ln)
    return page(title=_("ILL requests"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

    #return redirect_to_url(req,
    #                       '%s/admin2/bibcirculation/list_proposal?status=%s' % \
    #                       (CFG_SITE_SECURE_URL, CFG_BIBCIRCULATION_PROPOSAL_STATUS_PUT_ASIDE))

def register_ill_request_with_no_recid_step1(req, borrower_id,
                                             ln=CFG_SITE_LANG):

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    infos = []

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    body = bc_templates.tmpl_register_ill_request_with_no_recid_step1(
                                                        infos=infos,
                                                        borrower_id=borrower_id,
                                                        admin=True, ln=ln)

    return page(title=_("Register ILL request"),
                uid=id_user,
                req=req,
                metaheaderadd = "<link rel=\"stylesheet\" href=\"%s/img/jquery-ui.css\" type=\"text/css\" />" % CFG_SITE_SECURE_URL,
                body=body,
                language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def register_ill_request_with_no_recid_step2(req, title, authors, place,
                            publisher, year, edition, isbn, budget_code,
                            period_of_interest_from, period_of_interest_to,
                            additional_comments, only_edition, key, string,
                            borrower_id, ln=CFG_SITE_LANG):

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    infos = []
    book_info = (title, authors, place, publisher, year, edition, isbn)
    request_details = (budget_code, period_of_interest_from,
                       period_of_interest_to, additional_comments, only_edition)


    if borrower_id in (None, '', 'None'):
        body = None
        if not key:
            borrowers_list = None

        elif not string:
            infos.append(_('Empty string.') + ' ' + _('Please, try again.'))
            borrowers_list = None

        else:
            if validate_date_format(period_of_interest_from) is False:
                infos = []
                infos.append(_("The period of interest %(x_strong_tag_open)sFrom: %(x_date)s%(x_strong_tag_close)s is not a valid date or date format") % {'x_date': period_of_interest_from, 'x_strong_tag_open': '<strong>', 'x_strong_tag_close': '</strong>'})

                body = bc_templates.tmpl_register_ill_request_with_no_recid_step1(
                                                            infos=infos,
                                                            borrower_id=None,
                                                            admin=True,
                                                            ln=ln)

            elif validate_date_format(period_of_interest_to) is False:
                infos = []
                infos.append(_("The period of interest %(x_strong_tag_open)sTo: %(x_date)s%(x_strong_tag_close)s is not a valid date or date format") % {'x_date': period_of_interest_to, 'x_strong_tag_open': '<strong>', 'x_strong_tag_close': '</strong>'})

                body = bc_templates.tmpl_register_ill_request_with_no_recid_step1(
                                                                    infos=infos,
                                                                    ln=ln)

            else:
                result = search_user(key, string)

                borrowers_list = []
                if len(result) == 0:
                    infos.append(_("0 borrowers found."))
                else:
                    for user in result:
                        borrower_data = db.get_borrower_data_by_id(user[0])
                        borrowers_list.append(borrower_data)

        if body == None:
            body = bc_templates.tmpl_register_ill_request_with_no_recid_step2(
                           book_info=book_info, request_details=request_details,
                           result=borrowers_list, key=key, string=string,
                           infos=infos, ln=ln)

    else:
        user_info = db.get_borrower_data_by_id(borrower_id)


        return register_ill_request_with_no_recid_step3(req, title, authors,
                                                        place, publisher,year, edition,
                                                        isbn, user_info, budget_code,
                                                        period_of_interest_from,
                                                        period_of_interest_to,
                                                        additional_comments, only_edition,
                                                        ln)


    navtrail_previous_links = '<a class="navtrail" ' \
                    'href="%s/help/admin">Admin Area' \
                    '</a> &gt; <a class="navtrail" ' \
                    'href="%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s">'\
                    'Circulation Management' \
                    '</a> ' % (CFG_SITE_SECURE_URL, CFG_SITE_SECURE_URL, ln)



    return page(title=_("Register ILL request"),
                    uid=id_user,
                    req=req,
                    body=body, language=ln,
                    navtrail=navtrail_previous_links,
                    lastupdated=__lastupdated__)

def register_ill_request_with_no_recid_step3(req, title, authors, place,
                                                publisher, year, edition, isbn,
                                                user_info, budget_code,
                                                period_of_interest_from,
                                                period_of_interest_to,
                                                additional_comments,
                                                only_edition, ln=CFG_SITE_LANG):

    navtrail_previous_links = '<a class="navtrail" ' \
                    'href="%s/help/admin">Admin Area' \
                    '</a> &gt; <a class="navtrail" ' \
                    'href="%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s">'\
                    'Circulation Management' \
                    '</a> ' % (CFG_SITE_SECURE_URL, CFG_SITE_SECURE_URL, ln)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    request_details = (budget_code, period_of_interest_from,
                       period_of_interest_to, additional_comments, only_edition)

    book_info = (title, authors, place, publisher, year, edition, isbn)

    if user_info is None:
        return register_ill_request_with_no_recid_step2(req, title, authors,
                            place, publisher, year, edition, isbn, budget_code,
                            period_of_interest_from, period_of_interest_to,
                            additional_comments, only_edition, 'name', None,
                            None, ln)

    else:
        body = bc_templates.tmpl_register_ill_request_with_no_recid_step3(
                                                book_info=book_info,
                                                user_info=user_info,
                                                request_details=request_details,
                                                admin=True,
                                                ln=ln)

        return page(title=_("Register ILL request"),
                    uid=id_user,
                    req=req,
                    body=body, language=ln,
                    navtrail=navtrail_previous_links,
                    lastupdated=__lastupdated__)

def register_ill_request_with_no_recid_step4(req, book_info, borrower_id,
                                             request_details, ln):

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    navtrail_previous_links = '<a class="navtrail" ' \
                    'href="%s/help/admin">Admin Area' \
                    '</a> &gt; <a class="navtrail" ' \
                    'href="%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s">'\
                    'Circulation Management' \
                    '</a> ' % (CFG_SITE_SECURE_URL, CFG_SITE_SECURE_URL, ln)

    _ = gettext_set_language(ln)

    (title, authors, place, publisher, year, edition, isbn) = book_info
    #create_ill_record(book_info))

    (budget_code, period_of_interest_from,
     period_of_interest_to, library_notes, only_edition) = request_details

    ill_request_notes = {}
    if library_notes:
        ill_request_notes[time.strftime("%Y-%m-%d %H:%M:%S")] = \
                                                            str(library_notes)

### budget_code ###
    if db.get_borrower_data_by_id(borrower_id) == None:
        _ = gettext_set_language(ln)
        infos = []
        infos.append(_("<strong>Request not registered:</strong> wrong borrower id"))
        body = bc_templates.tmpl_register_ill_request_with_no_recid_step2(
                                book_info=book_info,
                                request_details=request_details, result=[],
                                key='name', string=None, infos=infos, ln=ln)

        return page(title=_("Register ILL request"),
                    uid=id_user,
                    req=req,
                    body=body, language=ln,
                    navtrail=navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        book_info = {'title': title, 'authors': authors, 'place': place,
                     'publisher': publisher,'year' : year,  'edition': edition,
                     'isbn' : isbn}
        db.ill_register_request_on_desk(borrower_id, book_info,
                                    period_of_interest_from,
                                    period_of_interest_to,
                                    CFG_BIBCIRCULATION_ILL_STATUS_NEW,
                                    str(ill_request_notes),
                                    only_edition, 'book', budget_code)

    return list_ill_request(req, CFG_BIBCIRCULATION_ILL_STATUS_NEW, ln)


def register_ill_book_request(req, borrower_id, ln=CFG_SITE_LANG):
    """
    Display a form where is possible to searh for an item.
    """
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    navtrail_previous_links = '<a class="navtrail" ' \
                    'href="%s/help/admin">Admin Area' \
                    '</a> &gt; <a class="navtrail" ' \
                    'href="%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s">'\
                    'Circulation Management' \
                    '</a> ' % (CFG_SITE_SECURE_URL, CFG_SITE_SECURE_URL, ln)

    _ = gettext_set_language(ln)

    infos = []

    body = bc_templates.tmpl_register_ill_book_request(infos=infos,
                                                       borrower_id=borrower_id,
                                                       ln=ln)

    return page(title=_("Register ILL Book request"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def register_ill_book_request_result(req, borrower_id, p, f,  ln=CFG_SITE_LANG):
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
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    infos = []
    if p == '':
        infos.append(_('Empty string.') + ' ' + _('Please, try again.'))
        body = bc_templates.tmpl_register_ill_book_request(infos=infos,
                                                        borrower_id=borrower_id,
                                                        ln=ln)
    else:
        if f == 'barcode':
            p = p.strip('\'" \t')
            recid = db.get_id_bibrec(p)

            if recid is None:
                infos.append(_('The barcode %(x_strong_tag_open)s%(x_barcode)s%(x_strong_tag_close)s does not exist on BibCirculation database.') % {'x_barcode': p, 'x_strong_tag_open': '<strong>', 'x_strong_tag_close': '</strong>'})
                body = bc_templates.tmpl_register_ill_book_request(infos=infos,
                                                        borrower_id=borrower_id,
                                                        ln=ln)
            else:
                body = bc_templates.tmpl_register_ill_book_request_result(
                                                        result=[recid],
                                                        borrower_id=borrower_id,
                                                        ln=ln)
        else:
            result = perform_request_search(cc="Books", sc="1", p=p, f=f)
            if len(result) == 0:
                return register_ill_request_with_no_recid_step1(req,
                                                                borrower_id, ln)
            else:
                body = bc_templates.tmpl_register_ill_book_request_result(
                                                        result=result,
                                                        borrower_id=borrower_id,
                                                        ln=ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                    'href="%s/help/admin">Admin Area' \
                    '</a> &gt; <a class="navtrail" ' \
                    'href="%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s">'\
                    'Circulation Management' \
                    '</a> ' % (CFG_SITE_SECURE_URL, CFG_SITE_SECURE_URL, ln)

    return page(title=_("Register ILL Book request"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def register_ill_article_request_step1(req, ln=CFG_SITE_LANG):

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    infos = []

    navtrail_previous_links = '<a class="navtrail" ' \
                   'href="%s/help/admin">Admin Area' \
                   '</a> &gt; <a class="navtrail" ' \
                   'href="%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s">' \
                   'Circulation Management' \
                   '</a> ' % (CFG_SITE_SECURE_URL, CFG_SITE_SECURE_URL, ln)

    body = bc_templates.tmpl_register_ill_article_request_step1(infos=infos,
                                                                ln=ln)

    return page(title=_("Register ILL Article request"),
                uid=id_user,
                req=req,
                body=body,
                metaheaderadd = "<link rel=\"stylesheet\" href=\"%s/img/jquery-ui.css\" type=\"text/css\" />"%(CFG_SITE_SECURE_URL),
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def register_ill_article_request_step2(req, periodical_title, article_title,
                                       author, report_number, volume, issue,
                                       pages, year, budget_code, issn,
                                       period_of_interest_from,
                                       period_of_interest_to,
                                       additional_comments, key, string,
                                       ln=CFG_SITE_LANG):

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    infos = []

    if key and not string:
        infos.append(_('Empty string.') + ' ' + _('Please, try again.'))
        article_info = (periodical_title, article_title, author, report_number,
                        volume, issue, pages, year, issn)
        request_details = (period_of_interest_from, period_of_interest_to,
                           budget_code, additional_comments)

        body = bc_templates.tmpl_register_ill_article_request_step2(
                                                article_info=article_info,
                                                request_details=request_details,
                                                result=None, key=key,
                                                string=string, infos=infos,
                                                ln=ln)

        navtrail_previous_links = '<a class="navtrail" ' \
                    'href="%s/help/admin">Admin Area' \
                    '</a> &gt; <a class="navtrail" ' \
                    'href="%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s">'\
                    'Circulation Management' \
                    '</a> ' % (CFG_SITE_SECURE_URL, CFG_SITE_SECURE_URL, ln)

        return page(title=_("Register ILL request"),
                    uid=id_user,
                    req=req,
                    body=body, language=ln,
                    navtrail=navtrail_previous_links,
                    lastupdated=__lastupdated__)

    result = search_user(key, string)
    borrowers_list = []

    if len(result) == 0 and key:
        if CFG_CERN_SITE:
            infos.append(_("0 borrowers found.") + ' ' +_("Search by CCID."))
        else:
            new_borrower_link = create_html_link(CFG_SITE_SECURE_URL +
                                '/admin2/bibcirculation/add_new_borrower_step1',
                                {'ln': ln}, _("Register new borrower."))
            message = _("0 borrowers found.") + ' ' + new_borrower_link
            infos.append(message)
    else:
        for user in result:
            borrower_data = db.get_borrower_data_by_id(user[0])
            borrowers_list.append(borrower_data)

    if validate_date_format(period_of_interest_from) is False:
        infos = []

        infos.append(_("The period of interest %(x_strong_tag_open)sFrom: %(x_date)s%(x_strong_tag_close)s is not a valid date or date format") % {'x_date': period_of_interest_from, 'x_strong_tag_open': '<strong>', 'x_strong_tag_close': '</strong>'})

        body = bc_templates.tmpl_register_ill_article_request_step1(infos=infos,
                                                                    ln=ln)

    elif validate_date_format(period_of_interest_to) is False:
        infos = []
        infos.append(_("The period of interest %(x_strong_tag_open)sTo: %(x_date)s%(x_strong_tag_close)s is not a valid date or date format") % {'x_date': period_of_interest_to, 'x_strong_tag_open': '<strong>', 'x_strong_tag_close': '</strong>'})

        body = bc_templates.tmpl_register_ill_article_request_step1(infos=infos,
                                                                    ln=ln)

    else:
        article_info = (periodical_title, article_title, author, report_number,
                        volume, issue, pages, year, issn)

        request_details = (period_of_interest_from, period_of_interest_to,
                           budget_code, additional_comments)

        body = bc_templates.tmpl_register_ill_article_request_step2(
                                                article_info=article_info,
                                                request_details=request_details,
                                                result=borrowers_list,
                                                key=key, string=string,
                                                infos=infos, ln=ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                    'href="%s/help/admin">Admin Area' \
                    '</a> &gt; <a class="navtrail" ' \
                    'href="%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s">'\
                    'Circulation Management' \
                    '</a> ' % (CFG_SITE_SECURE_URL, CFG_SITE_SECURE_URL, ln)

    return invenio.webpage.page(title=_("Register ILL request"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def register_ill_article_request_step3(req, periodical_title, title, authors,
                                       report_number, volume, issue,
                                       page_number, year, issn, user_info,
                                       request_details, ln=CFG_SITE_LANG):

    #id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    #info = (title, authors, "", "", year, "", issn)

    #create_ill_record(info)

    item_info = {'periodical_title': periodical_title, 'title': title,
                 'authors': authors, 'place': "", 'publisher': "",
                 'year' : year,  'edition': "", 'issn' : issn,
                 'volume': volume, 'issue': issue, 'page': page_number }


    (period_of_interest_from, period_of_interest_to, budget_code,
     library_notes) = request_details

    only_edition = ""

    if user_info is None:
        return register_ill_article_request_step2(req, periodical_title, title,
                                        authors, report_number, volume, issue,
                                        page_number, year, budget_code, issn,
                                        period_of_interest_from,
                                        period_of_interest_to,
                                        library_notes, 'name', None, ln)
    else:
        borrower_id = user_info[0]

        ill_request_notes = {}
        if library_notes:
            ill_request_notes[time.strftime("%Y-%m-%d %H:%M:%S")] \
                                                           = str(library_notes)

        db.ill_register_request_on_desk(borrower_id, item_info,
                                        period_of_interest_from,
                                        period_of_interest_to,
                                        CFG_BIBCIRCULATION_ILL_STATUS_NEW,
                                        str(ill_request_notes),
                                        only_edition, 'article', budget_code)


        return list_ill_request(req, CFG_BIBCIRCULATION_ILL_STATUS_NEW, ln)


def register_purchase_request_step1(req, request_type, recid, title, authors,
                        place, publisher, year, edition, this_edition_only,
                        isbn, standard_number,
                        budget_code, cash, period_of_interest_from,
                        period_of_interest_to, additional_comments,
                        ln=CFG_SITE_LANG):

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    infos = []

    navtrail_previous_links = '<a class="navtrail" ' \
                    'href="%s/help/admin">Admin Area' \
                    '</a> &gt; <a class="navtrail" ' \
                    'href="%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s">'\
                    'Circulation Management' \
                    '</a> ' % (CFG_SITE_SECURE_URL, CFG_SITE_SECURE_URL, ln)
    if recid:
        fields = (request_type, recid, budget_code, cash,
                  period_of_interest_from, period_of_interest_to,
                  additional_comments)
    else:
        fields = (request_type, title, authors, place, publisher, year, edition,
                  this_edition_only, isbn, standard_number, budget_code,
                  cash, period_of_interest_from, period_of_interest_to,
                  additional_comments)

    body = bc_templates.tmpl_register_purchase_request_step1(infos=infos,
                                         fields=fields, admin=True, ln=ln)

    return page(title=_("Register purchase request"),
                uid=id_user,
                req=req,
                body=body,
                language=ln,
                metaheaderadd='<link rel="stylesheet" ' \
                                    'href="%s/img/jquery-ui.css" ' \
                                    'type="text/css" />' % CFG_SITE_SECURE_URL,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def register_purchase_request_step2(req, request_type, recid, title, authors,
                        place, publisher, year, edition, this_edition_only,
                        isbn, standard_number,
                        budget_code, cash, period_of_interest_from,
                        period_of_interest_to, additional_comments,
                        p, f, ln=CFG_SITE_LANG):

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                    'href="%s/help/admin">Admin Area' \
                    '</a> &gt; <a class="navtrail" ' \
                    'href="%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s">'\
                    'Circulation Management' \
                    '</a> ' % (CFG_SITE_SECURE_URL, CFG_SITE_SECURE_URL, ln)

    infos = []

    if cash and budget_code == '':
        budget_code = 'cash'

    if recid:
        fields = (request_type, recid, budget_code, cash,
                  period_of_interest_from, period_of_interest_to,
                  additional_comments)
    else:
        fields = (request_type, title, authors, place, publisher, year, edition,
                  this_edition_only, isbn, standard_number, budget_code,
                  cash, period_of_interest_from, period_of_interest_to,
                  additional_comments)

    if budget_code == '' and not cash:
        infos.append(_("Payment method information is mandatory. \
                        Please, type your budget code or tick the 'cash' checkbox."))
        body = bc_templates.tmpl_register_purchase_request_step1(infos=infos,
                                                    fields=fields, admin=True, ln=ln)

    else:

########################
########################
        if p and not f:
            infos.append(_('Empty string.') + ' ' + _('Please, try again.'))

            body = bc_templates.tmpl_register_purchase_request_step2(
                                                infos=infos, fields=fields,
                                                result=None, p=p, f=f, ln=ln)

            navtrail_previous_links = '<a class="navtrail" ' \
                        'href="%s/help/admin">Admin Area' \
                        '</a> &gt; <a class="navtrail" ' \
                        'href="%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s">'\
                        'Circulation Management' \
                        '</a> ' % (CFG_SITE_SECURE_URL, CFG_SITE_SECURE_URL, ln)

            return page(title=_("Register ILL request"),
                        uid=id_user,
                        req=req,
                        body=body, language=ln,
                        navtrail=navtrail_previous_links,
                        lastupdated=__lastupdated__)

        result = search_user(f, p)
        borrowers_list = []

        if len(result) == 0 and f:
            if CFG_CERN_SITE:
                infos.append(_("0 borrowers found.") + ' ' +_("Search by CCID."))
            else:
                new_borrower_link = create_html_link(CFG_SITE_SECURE_URL +
                                '/admin2/bibcirculation/add_new_borrower_step1',
                                {'ln': ln}, _("Register new borrower."))
                message = _("0 borrowers found.") + ' ' + new_borrower_link
                infos.append(message)
        else:
            for user in result:
                borrower_data = db.get_borrower_data_by_id(user[0])
                borrowers_list.append(borrower_data)

        body = bc_templates.tmpl_register_purchase_request_step2(
                                                infos=infos, fields=fields,
                                                result=borrowers_list, p=p,
                                                f=f, ln=ln)
########################
########################

    return page(title=_("Register purchase request"),
                uid=id_user,
                req=req,
                body=body,
                language=ln,
                metaheaderadd='<link rel="stylesheet" ' \
                                    'href="%s/img/jquery-ui.css" ' \
                                    'type="text/css" />' % CFG_SITE_SECURE_URL,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def register_purchase_request_step3(req, request_type, recid, title, authors,
                        place, publisher, year, edition, this_edition_only,
                        isbn, standard_number,
                        budget_code, cash, period_of_interest_from,
                        period_of_interest_to, additional_comments,
                        borrower_id, ln=CFG_SITE_LANG):

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                    'href="%s/help/admin">Admin Area' \
                    '</a> &gt; <a class="navtrail" ' \
                    'href="%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s">'\
                    'Circulation Management' \
                    '</a> ' % (CFG_SITE_SECURE_URL, CFG_SITE_SECURE_URL, ln)

    infos = []

    if recid:
        fields = (request_type, recid, budget_code, cash,
                  period_of_interest_from, period_of_interest_to,
                  additional_comments)
    else:
        fields = (request_type, title, authors, place, publisher, year, edition,
                  this_edition_only, isbn, standard_number, budget_code,
                  cash, period_of_interest_from, period_of_interest_to,
                  additional_comments)

    if budget_code == '' and not cash:
        infos.append(_("Payment method information is mandatory. \
                        Please, type your budget code or tick the 'cash' checkbox."))
        body = bc_templates.tmpl_register_purchase_request_step1(infos=infos,
                                             fields=fields, admin=True, ln=ln)
    else:
        if recid:
            item_info = "{'recid': " + str(recid) + "}"
            title = book_title_from_MARC(recid)
        else:
            item_info = {'title': title, 'authors': authors, 'place': place,
                         'publisher': publisher, 'year' : year,  'edition': edition,
                         'isbn' : isbn, 'standard_number': standard_number}

        ill_request_notes = {}
        if additional_comments:
            ill_request_notes[time.strftime("%Y-%m-%d %H:%M:%S")] \
                                                      = str(additional_comments)

        if cash and budget_code == '':
            budget_code = 'cash'


        if borrower_id:
            borrower_email = db.get_borrower_email(borrower_id)
        else:
            borrower_email = db.get_invenio_user_email(id_user)
            borrower_id = db.get_borrower_id_by_email(borrower_email)

        db.ill_register_request_on_desk(borrower_id, item_info,
                                        period_of_interest_from,
                                        period_of_interest_to,
                                        CFG_BIBCIRCULATION_ACQ_STATUS_NEW,
                                        str(ill_request_notes),
                                        this_edition_only, request_type, budget_code)

        msg_for_user = load_template('purchase_notification') % title
        send_email(fromaddr = CFG_BIBCIRCULATION_ILLS_EMAIL,
                   toaddr   = borrower_email,
                   subject  = _("Your book purchase request"),
                   header = '', footer = '',
                   content  = msg_for_user,
                   attempt_times=1,
                   attempt_sleeptime=10
                  )

        return redirect_to_url(req,
                '%s/admin2/bibcirculation/list_purchase?ln=%s&status=%s' % \
                                            (CFG_SITE_SECURE_URL, ln,
                                             CFG_BIBCIRCULATION_ACQ_STATUS_NEW))

    return page(title=_("Register purchase request"),
                uid=id_user,
                req=req,
                body=body,
                language=ln,
                metaheaderadd='<link rel="stylesheet" ' \
                                    'href="%s/img/jquery-ui.css" ' \
                                    'type="text/css" />' % CFG_SITE_SECURE_URL,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def ill_request_details_step1(req, delete_key, ill_request_id, new_status,
                              ln=CFG_SITE_LANG):

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    infos = []

    if delete_key and ill_request_id:
        if looks_like_dictionary(db.get_ill_request_notes(ill_request_id)):
            library_notes = eval(db.get_ill_request_notes(ill_request_id))
            if delete_key in library_notes.keys():
                del library_notes[delete_key]
                db.update_ill_request_notes(ill_request_id, library_notes)

    if new_status:
        db.update_ill_request_status(ill_request_id, new_status)

    ill_request_borrower_details = \
                            db.get_ill_request_borrower_details(ill_request_id)

    if ill_request_borrower_details is None \
       or len(ill_request_borrower_details) == 0:
        infos.append(_("Borrower request details not found."))

    ill_request_details = db.get_ill_request_details(ill_request_id)
    if ill_request_details is None or len(ill_request_details) == 0:
        infos.append(_("Request not found."))


    libraries = db.get_external_libraries()

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    title = _("ILL request details")
    if infos == []:
        body = bc_templates.tmpl_ill_request_details_step1(
                                    ill_request_id=ill_request_id,
                                    ill_request_details=ill_request_details,
                                    libraries=libraries,
                      ill_request_borrower_details=ill_request_borrower_details,
                                    ln=ln)
    else:
        body = bc_templates.tmpl_display_infos(infos, ln)

    return page(title=title,
                uid=id_user,
                req=req,
                metaheaderadd='<link rel="stylesheet" ' \
                                    'href="%s/img/jquery-ui.css" ' \
                                    'type="text/css" />' % CFG_SITE_SECURE_URL,
                body=body,
                language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def ill_request_details_step2(req, delete_key, ill_request_id, new_status,
                              library_id, request_date, expected_date,
                              arrival_date, due_date, return_date,
                              cost, _currency, barcode, library_notes,
                              book_info, article_info, ln=CFG_SITE_LANG):

    #id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    if delete_key and ill_request_id:
        if looks_like_dictionary(db.get_ill_request_notes(ill_request_id)):
            library_previous_notes = eval(db.get_ill_request_notes(ill_request_id))
            if delete_key in library_previous_notes.keys():
                del library_previous_notes[delete_key]
                db.update_ill_request_notes(ill_request_id, library_previous_notes)

    if db.get_ill_request_notes(ill_request_id):
        if looks_like_dictionary(db.get_ill_request_notes(ill_request_id)):
            library_previous_notes = eval(db.get_ill_request_notes(ill_request_id))
        else:
            library_previous_notes = {}
    else:
        library_previous_notes = {}

    if library_notes:
        library_previous_notes[time.strftime("%Y-%m-%d %H:%M:%S")] = \
                                                            str(library_notes)

    if new_status == CFG_BIBCIRCULATION_LOAN_STATUS_RETURNED:
        borrower_id = db.get_ill_borrower(ill_request_id)
        barcode = db.get_ill_barcode(ill_request_id)
        db.update_ill_loan_status(borrower_id, barcode, return_date, 'ill')

    # ill recall letter issue
    try:
        from invenio.dbquery import run_sql
        _query = ('SELECT due_date from crcILLREQUEST where id = "{0}"')
        _due = run_sql(_query.format(ill_request_id))[0][0]

        # Since we don't know if the due_date is a string or datetime
        try:
            _due_date = datetime.datetime.strptime(due_date, '%Y-%m-%d')
        except TypeError:
            _due_date = due_date

        # This means that the ILL got extended, we therefore reset the 
        # overdue_letter_numer
        if _due < _due_date:
            db.update_ill_request_letter_number(ill_request_id, 0)
    except Exception:
        pass

    db.update_ill_request(ill_request_id, library_id, request_date,
                          expected_date, arrival_date, due_date, return_date,
                          new_status, cost, barcode,
                          str(library_previous_notes))

    request_type = db.get_ill_request_type(ill_request_id)
    if request_type == 'book':
        item_info = book_info
    else:
        item_info = article_info
    db.update_ill_request_item_info(ill_request_id, item_info)

    if new_status == CFG_BIBCIRCULATION_ILL_STATUS_ON_LOAN:
        # Redirect to an email template when the ILL 'book' arrives
        # (Not for articles.)
        subject = _("ILL received: ")
        book_info = db.get_ill_book_info(ill_request_id)
        if looks_like_dictionary(book_info):
            book_info = eval(book_info)
            if book_info.has_key('recid'):
                subject += "'" + book_title_from_MARC(int(book_info['recid'])) + "'"
        bid = db.get_ill_borrower(ill_request_id)
        msg = load_template("ill_received")

        return redirect_to_url(req,
                               create_url(CFG_SITE_SECURE_URL +
                                          '/admin2/bibcirculation/borrower_notification',
                                          {'borrower_id': bid,
                                           'subject': subject,
                                           'load_msg_template': False,
                                           'template': msg,
                                           'from_address': CFG_BIBCIRCULATION_ILLS_EMAIL
                                           }
                                          )
                               )

    return list_ill_request(req, new_status, ln)


def purchase_details_step1(req, delete_key, ill_request_id, new_status,
                              ln=CFG_SITE_LANG):

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    infos = []

    if delete_key and ill_request_id:
        if looks_like_dictionary(db.get_ill_request_notes(ill_request_id)):
            library_notes = eval(db.get_ill_request_notes(ill_request_id))
            if delete_key in library_notes.keys():
                del library_notes[delete_key]
                db.update_ill_request_notes(ill_request_id, library_notes)

    if new_status:
        db.update_ill_request_status(ill_request_id, new_status)

    ill_request_borrower_details = \
                            db.get_purchase_request_borrower_details(ill_request_id)

    if ill_request_borrower_details is None \
       or len(ill_request_borrower_details) == 0:
        infos.append(_("Borrower request details not found."))

    ill_request_details = db.get_ill_request_details(ill_request_id)
    if ill_request_details is None or len(ill_request_details) == 0:
        infos.append(_("Request not found."))

    vendors = db.get_all_vendors()

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    if infos == []:
        body = bc_templates.tmpl_purchase_details_step1(
                                    ill_request_id=ill_request_id,
                                    ill_request_details=ill_request_details,
                                    libraries=vendors,
                      ill_request_borrower_details=ill_request_borrower_details,
                                    ln=ln)
        title = _("Purchase details")
    else:
        body = bc_templates.tmpl_display_infos(infos, ln)

    return page(title=title,
                uid=id_user,
                req=req,
                metaheaderadd = "<link rel=\"stylesheet\" href=\"%s/img/jquery-ui.css\" type=\"text/css\" />" % CFG_SITE_SECURE_URL,
                body=body,
                language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def purchase_details_step2(req, delete_key, ill_request_id, new_status,
                              library_id, request_date, expected_date,
                              arrival_date, due_date, return_date,
                              cost, budget_code, library_notes,
                              item_info, ln=CFG_SITE_LANG):

    #id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    if delete_key and ill_request_id:
        if looks_like_dictionary(db.get_ill_request_notes(ill_request_id)):
            library_previous_notes = eval(db.get_ill_request_notes(ill_request_id))
            if delete_key in library_previous_notes.keys():
                del library_previous_notes[delete_key]
                db.update_ill_request_notes(ill_request_id, library_previous_notes)

    if db.get_ill_request_notes(ill_request_id):
        if looks_like_dictionary(db.get_ill_request_notes(ill_request_id)):
            library_previous_notes = eval(db.get_ill_request_notes(ill_request_id))
        else:
            library_previous_notes = {}
    else:
        library_previous_notes = {}

    if library_notes:
        library_previous_notes[time.strftime("%Y-%m-%d %H:%M:%S")] = \
                                                            str(library_notes)

    if new_status == CFG_BIBCIRCULATION_LOAN_STATUS_RETURNED:
        borrower_id = db.get_ill_borrower(ill_request_id)

    db.update_purchase_request(ill_request_id, library_id, request_date,
                          expected_date, arrival_date, due_date, return_date,
                          new_status, cost, budget_code,
                          str(library_previous_notes))

    request_type = db.get_ill_request_type(ill_request_id)

    if request_type not in CFG_BIBCIRCULATION_PROPOSAL_TYPE:
        db.update_ill_request_item_info(ill_request_id, item_info)

    if new_status in (CFG_BIBCIRCULATION_PROPOSAL_STATUS_ON_ORDER,
                      CFG_BIBCIRCULATION_PROPOSAL_STATUS_PUT_ASIDE):

        barcode = db.get_ill_barcode(ill_request_id)
        if new_status == CFG_BIBCIRCULATION_PROPOSAL_STATUS_ON_ORDER:
            db.update_item_status(CFG_BIBCIRCULATION_ITEM_STATUS_ON_ORDER, barcode)
            subject = _("Book suggestion accepted: ")
            template = "proposal_acceptance"
        else:
            db.update_item_status(CFG_BIBCIRCULATION_ITEM_STATUS_UNDER_REVIEW, barcode)
            subject = _("Book suggestion refused: ")
            template = "proposal_refusal"

        book_info = db.get_ill_book_info(ill_request_id)
        if looks_like_dictionary(book_info):
            book_info = eval(book_info)
            if book_info.has_key('recid'):
                bid = db.get_ill_borrower(ill_request_id)
                if db.has_loan_request(bid, book_info['recid']):
                    subject += "'" + book_title_from_MARC(int(book_info['recid'])) + "'"
                    return redirect_to_url(req,
                                           create_url(CFG_SITE_SECURE_URL +
                                           '/admin2/bibcirculation/borrower_notification',
                                           {'borrower_id': bid,
                                            'subject': subject,
                                            'template': template,
                                            'from_address': CFG_BIBCIRCULATION_ILLS_EMAIL
                                            }
                                            )
                                           )

    if new_status == CFG_BIBCIRCULATION_PROPOSAL_STATUS_RECEIVED:
        barcode = db.get_ill_barcode(ill_request_id)
        # Reset the item description to the default value.
        db.set_item_description(barcode, '-')
        #db.update_item_status(CFG_BIBCIRCULATION_ITEM_STATUS_IN_PROCESS, barcode)
        borrower_id = db.get_ill_borrower(ill_request_id)
        recid = db.get_id_bibrec(barcode)
        if db.has_loan_request(borrower_id, recid):
            #If an ILL has already been created(After the book had been put aside), there
            #would be no waiting request by the proposer.
            db.update_loan_request_status(CFG_BIBCIRCULATION_REQUEST_STATUS_WAITING,
                                      barcode=barcode,
                                      borrower_id=borrower_id)
        return redirect_to_url(req,
               '%s/admin2/bibcirculation/update_item_info_step4?barcode=%s' % \
                                                (CFG_SITE_SECURE_URL, barcode))

    if new_status == CFG_BIBCIRCULATION_ACQ_STATUS_RECEIVED:
        subject = _("Purchase received: ")
        book_info = db.get_ill_book_info(ill_request_id)
        if looks_like_dictionary(book_info):
            book_info = eval(book_info)
            if book_info.has_key('recid'):
                subject += "'" + book_title_from_MARC(int(book_info['recid'])) + "'"
        bid = db.get_ill_borrower(ill_request_id)

        if budget_code == 'cash':
            msg = load_template("purchase_received_cash") % cost
        else:
            msg = load_template("purchase_received_tid") % cost

        return redirect_to_url(req,
                               create_url(CFG_SITE_SECURE_URL +
                                          '/admin2/bibcirculation/borrower_notification',
                                          {'borrower_id': bid,
                                           'subject': subject,
                                           'load_msg_template': False,
                                           'template': msg,
                                           'from_address': CFG_BIBCIRCULATION_ILLS_EMAIL
                                           }
                                          )
                               )
    if new_status in CFG_BIBCIRCULATION_ACQ_STATUS or \
            new_status == CFG_BIBCIRCULATION_PROPOSAL_STATUS_ON_ORDER:
        # The items 'on order' whether for acquisition for the library or purchase
        # on behalf of the user are displayed in the same list.
        return redirect_to_url(req,
                '%s/admin2/bibcirculation/list_purchase?ln=%s&status=%s' % \
                              (CFG_SITE_SECURE_URL, ln, new_status))
    else:
        return redirect_to_url(req,
                '%s/admin2/bibcirculation/list_proposal?ln=%s&status=%s' % \
                              (CFG_SITE_SECURE_URL, ln, new_status))


def get_ill_library_notes(req, ill_id, delete_key, library_notes,
                          ln=CFG_SITE_LANG):

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    if delete_key and ill_id:
        if looks_like_dictionary(db.get_ill_notes(ill_id)):
            ill_notes = eval(db.get_ill_notes(ill_id))
            if delete_key in ill_notes.keys():
                del ill_notes[delete_key]
                db.update_ill_notes(ill_id, ill_notes)

    elif library_notes:
        if db.get_ill_notes(ill_id):
            if looks_like_dictionary(db.get_ill_notes(ill_id)):
                ill_notes = eval(db.get_ill_notes(ill_id))
            else:
                ill_notes = {}
        else:
            ill_notes = {}

        ill_notes[time.strftime("%Y-%m-%d %H:%M:%S")] = str(library_notes)
        db.update_ill_notes(ill_id, ill_notes)

    ill_notes = db.get_ill_notes(ill_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    body = bc_templates.tmpl_ill_notes(ill_notes=ill_notes,
                                                 ill_id=ill_id,
                                                 ln=ln)
    return page(title=_("ILL notes"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def list_ill_request(req, status, ln=CFG_SITE_LANG):

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    ill_req = db.get_ill_requests(status)

    body = bc_templates.tmpl_list_ill(ill_req=ill_req, ln=ln)

    return page(title=_("List of ILL requests"),
                uid=id_user,
                req=req,
                body=body,
                language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def list_purchase(req, status, recid=None, ln=CFG_SITE_LANG):

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    if recid:
        # Purchases of a particular item to be displayed in the item info page.
        purchase_reqs = db.get_item_purchases(status, recid)
    else:
        purchase_reqs = db.get_purchases(status)

    body = bc_templates.tmpl_list_purchase(purchase_reqs, ln=ln)

    return page(title=_("List of purchase requests"),
                uid=id_user,
                req=req,
                body=body,
                language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def list_proposal(req, status, ln=CFG_SITE_LANG):

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    if status == "requests-putaside":
        requests = db.get_requests_on_put_aside_proposals()
        body = bc_templates.tmpl_list_requests_on_put_aside_proposals(requests, ln=ln)
        title=_("List of requests on put aside proposals")
    else:
        proposals = db.get_proposals(status)
        body = bc_templates.tmpl_list_proposal(proposals, ln=ln)
        title=_("List of proposals")

    return page(title=title,
                uid=id_user,
                req=req,
                body=body,
                language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)


def ill_search(req, ln=CFG_SITE_LANG):

    infos = []

    navtrail_previous_links = '<a class="navtrail" ' \
                    'href="%s/help/admin">Admin Area' \
                    '</a> &gt; <a class="navtrail" ' \
                    'href="%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s">'\
                    'Circulation Management' \
                    '</a> ' % (CFG_SITE_SECURE_URL, CFG_SITE_SECURE_URL, ln)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    body = bc_templates.tmpl_ill_search(infos=infos, ln=ln)

    return page(title=_("ILL search"),
                uid=id_user,
                req=req,
                body=body,
                language=ln,
            metaheaderadd='<link rel="stylesheet" href="%s/img/jquery-ui.css" '\
                                'type="text/css" />' % CFG_SITE_SECURE_URL,
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
                    'href="%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s">'\
                    'Circulation Management' \
                    '</a> ' % (CFG_SITE_SECURE_URL, CFG_SITE_SECURE_URL, ln)

    #id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    if not has_date_format(date_from):
        date_from = '0000-00-00'
    if not has_date_format(date_to):
        date_to = '9999-12-31'

    if f == 'title':
        ill_req = db.search_ill_requests_title(p, date_from, date_to)
        body = bc_templates.tmpl_list_ill(ill_req=ill_req, ln=ln)

    elif f == 'ILL_request_ID':
        ill_req = db.search_ill_requests_id(p, date_from, date_to)
        body = bc_templates.tmpl_list_ill(ill_req=ill_req, ln=ln)

    elif f == 'cost':
        purchase_reqs = db.search_requests_cost(p, date_from, date_to)
        body = bc_templates.tmpl_list_purchase(purchase_reqs=purchase_reqs, ln=ln)

    elif f == 'notes':
        purchase_reqs = db.search_requests_notes(p, date_from, date_to)
        body = bc_templates.tmpl_list_purchase(purchase_reqs=purchase_reqs, ln=ln)

    return page(title=_("List of ILL requests"),
                req=req,
                body=body,
                language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)




###
### "Library" related templates ###
###




def get_library_details(req, library_id, ln=CFG_SITE_LANG):
    """
    Display the details of a library.

    @type library_id:    integer.
    @param library_id:   identify the library. It is also the primary key of
                         the table crcLIBRARY.

    @return:             library details.
    """
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    library_details = db.get_library_details(library_id)

    if library_details is None:
        _ = gettext_set_language(ln)
        infos = []
        infos.append(_('Library ID not found.'))
        return search_library_step1(req, infos, ln)

    library_items = db.get_library_items(library_id)

    body = bc_templates.tmpl_library_details(library_details=library_details,
                                             library_items=library_items,
                                             ln=ln)

    return page(title=_("Library details"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def merge_libraries_step1(req, library_id, f=None, p=None, ln=CFG_SITE_LANG):
    """
    Step 1/3 of library merging procedure

    @param library_id:  ID of the library to be deleted

    @param p: search pattern.

    @param f: field
    """

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    library_details = db.get_library_details(library_id)
    library_items = db.get_library_items(library_id)

    result = None

    if f is not None:
        if p in (None, '', '*'):
            result = db.get_all_libraries() #list of (id, name)
        elif f == 'name':
            result = db.search_library_by_name(p)
        elif f == 'email':
            result = db.search_library_by_email(p)


    body = bc_templates.tmpl_merge_libraries_step1(
                                                library_details=library_details,
                                                library_items=library_items,
                                                result=result,
                                                p=p,
                                                ln=ln)

    return page(title=_("Merge libraries"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def merge_libraries_step2(req, library_from, library_to, ln=CFG_SITE_LANG):
    """
    Step 2/3 of library merging procedure
    Confirm the libraries selected

    @param library_from:  ID of the library to be deleted

    @param library_to:    ID of the resulting library
    """

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    library_from_details = db.get_library_details(library_from)
    library_from_items   = db.get_library_items(library_from)

    library_to_details   = db.get_library_details(library_to)
    library_to_items     = db.get_library_items(library_to)

    body = bc_templates.tmpl_merge_libraries_step2(
                                    library_from_details=library_from_details,
                                    library_from_items=library_from_items,
                                    library_to_details=library_to_details,
                                    library_to_items=library_to_items,
                                    ln=ln)

    return page(title=_("Merge libraries"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def merge_libraries_step3(req, library_from, library_to, ln=CFG_SITE_LANG):
    """
    Step 3/3 of library merging procedure
    Perform the merge and display the details of the resulting library

    @param library_from:  ID of the library to be deleted

    @param library_to:    ID of the resulting library
    """

    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    db.merge_libraries(library_from, library_to)

    return get_library_details(req, library_to, ln)

def add_new_library_step1(req, ln=CFG_SITE_LANG):
    """
    Add a new Library.
    """
    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    body = bc_templates.tmpl_add_new_library_step1(ln=ln)

    return page(title=_("Add new library"),
                uid=id_user,
                req=req,
                body=body, language=ln,
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
                              '</a>' % (CFG_SITE_SECURE_URL,)

    _ = gettext_set_language(ln)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bc_templates.tmpl_add_new_library_step2(tup_infos=tup_infos, ln=ln)

    return page(title=_("Add new library"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def add_new_library_step3(req, name, email, phone, address,
                           lib_type, notes, ln=CFG_SITE_LANG):
    """
    Add a new Library.
    """

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    db.add_new_library(name, email, phone, address, lib_type, notes)

    body = bc_templates.tmpl_add_new_library_step3(ln=ln)

    return page(title=_("Add new library"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_library_info_step1(req, ln=CFG_SITE_LANG):
    """
    Update the library's information.
    """
    infos = []

    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    body = bc_templates.tmpl_update_library_info_step1(infos=infos, ln=ln)

    return page(title=_("Update library information"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_library_info_step2(req, column, string, ln=CFG_SITE_LANG):
    """
    Update the library's information.
    """
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    if not string:
        infos = []
        infos.append(_("Empty string.") + ' ' + _('Please, try again.'))
        body = bc_templates.tmpl_update_library_info_step1(infos=infos, ln=ln)
    elif string == '*':
        result = db.get_all_libraries()
        body = bc_templates.tmpl_update_library_info_step2(result=result, ln=ln)
    else:
        if column == 'name':
            result = db.search_library_by_name(string)
        else:
            result = db.search_library_by_email(string)

        body = bc_templates.tmpl_update_library_info_step2(result=result, ln=ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    return page(title=_("Update library information"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_library_info_step3(req, library_id, ln=CFG_SITE_LANG):
    """
    Update the library's information.

    library_id - identify the library. It is also the primary key of
                 the table crcLIBRARY.
    """

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    library_info = db.get_library_details(library_id)

    body = bc_templates.tmpl_update_library_info_step3(
                                                    library_info=library_info,
                                                    ln=ln)

    return page(title=_("Update library information"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_library_info_step4(req, name, email, phone, address, lib_type,
                              library_id, ln=CFG_SITE_LANG):
    """
    Update the library's information.
    """

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    tup_infos = (library_id, name, email, phone, address, lib_type)

    body = bc_templates.tmpl_update_library_info_step4(tup_infos=tup_infos,
                                                       ln=ln)

    return page(title=_("Update library information"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_library_info_step5(req, name, email, phone, address, lib_type,
                              library_id, ln=CFG_SITE_LANG):
    """
    Update the library's information.
    """

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    #(library_id, name, email, phone, address) = tup_infos

    db.update_library_info(library_id, name, email, phone, address, lib_type)

    body = bc_templates.tmpl_update_library_info_step5(ln=ln)

    return page(title=_("Update library information"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def get_library_notes(req, library_id, delete_key,
                      library_notes, ln=CFG_SITE_LANG):
    """
    Retrieve notes related with a library.

    library_id - identify the library. It is also the primary key of
                 the table crcLIBRARY.
    """
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    if delete_key and library_id:
        if looks_like_dictionary(db.get_library_notes(library_id)):
            lib_notes = eval(db.get_library_notes(library_id))
            if delete_key in lib_notes.keys():
                del lib_notes[delete_key]
                db.update_library_notes(library_id, lib_notes)

    elif library_notes:
        if db.get_library_notes(library_id):
            if looks_like_dictionary(db.get_library_notes(library_id)):
                lib_notes = eval(db.get_library_notes(library_id))
            else:
                lib_notes = {}
        else:
            lib_notes = {}

        lib_notes[time.strftime("%Y-%m-%d %H:%M:%S")] = str(library_notes)
        db.update_library_notes(library_id, lib_notes)

    lib_notes = db.get_library_notes(library_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                    'href="%s/help/admin">Admin Area' \
                    '</a> &gt; <a class="navtrail" ' \
                    'href="%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s">'\
                    'Circulation Management' \
                    '</a> ' % (CFG_SITE_SECURE_URL, CFG_SITE_SECURE_URL, ln)

    body = bc_templates.tmpl_library_notes(library_notes=lib_notes,
                                            library_id=library_id,
                                            ln=ln)
    return page(title=_("Library notes"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def search_library_step1(req, infos=[], ln=CFG_SITE_LANG):
    """
    Display the form where we can search a library (by name or email).
    """

    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    body = bc_templates.tmpl_search_library_step1(infos=infos,
                                                              ln=ln)

    return page(title=_("Search library"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def search_library_step2(req, column, string, ln=CFG_SITE_LANG):
    """
    Search a library and return a list with all the possible results, using the
    parameters received from the previous step.

    column - identify the column, of the table crcLIBRARY, that will be
             considered during the search. Can be 'name' or 'email'.

    str - string used for the search process.
    """
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    if not string:
        infos = []
        infos.append(_("Emptry string.") + ' ' + _('Please, try again.'))
        body = bc_templates.tmpl_search_library_step1(infos=infos, ln=ln)
    elif string == '*':
        result = db.get_all_libraries()
        body = bc_templates.tmpl_search_library_step2(result=result, ln=ln)
    else:
        if column == 'name':
            result = db.search_library_by_name(string)
        else:
            result = db.search_library_by_email(string)

        body = bc_templates.tmpl_search_library_step2(result=result, ln=ln)


    navtrail_previous_links = '<a class="navtrail" ' \
                    'href="%s/help/admin">Admin Area' \
                    '</a> &gt; <a class="navtrail" ' \
                    'href="%s/admin2/bibcirculation/loan_on_desk_step1?ln=%s">'\
                    'Circulation Management' \
                    '</a> ' % (CFG_SITE_SECURE_URL, CFG_SITE_SECURE_URL, ln)

    return page(title=_("Search library"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)





###
### "Vendor" related templates ###
###




def get_vendor_details(req, vendor_id, ln=CFG_SITE_LANG):
    """
    Display the details of a vendor.

    @type vendor_id:    integer.
    @param vendor_id:   identify the vendor. It is also the primary key of
                        the table crcVENDOR.

    @return:            vendor details.
    """
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    vendor_details = db.get_vendor_details(vendor_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    body = bc_templates.tmpl_vendor_details(vendor_details=vendor_details,
                                                        ln=ln)

    return page(title=_("Vendor details"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def add_new_vendor_step1(req, ln=CFG_SITE_LANG):
    """
    Add a new Vendor.
    """
    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    body = bc_templates.tmpl_add_new_vendor_step1(ln=ln)

    return page(title=_("Add new vendor"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def add_new_vendor_step2(req, name, email, phone, address,
                         notes, ln=CFG_SITE_LANG):

    """
    Add a new Vendor.
    """
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    tup_infos = (name, email, phone, address, notes)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    body = bc_templates.tmpl_add_new_vendor_step2(tup_infos=tup_infos, ln=ln)

    return page(title=_("Add new vendor"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def add_new_vendor_step3(req, name, email, phone, address,
                         notes, ln=CFG_SITE_LANG):
    """
    Add a new Vendor.
    """
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    db.add_new_vendor(name, email, phone, address, notes)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    body = bc_templates.tmpl_add_new_vendor_step3(ln=ln)

    return page(title=_("Add new vendor"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_vendor_info_step1(req, ln=CFG_SITE_LANG):
    """
    Update the vendor's information.
    """

    infos = []

    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    _ = gettext_set_language(ln)

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    body = bc_templates.tmpl_update_vendor_info_step1(infos=infos, ln=ln)

    return page(title=_("Update vendor information"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_vendor_info_step2(req, column, string, ln=CFG_SITE_LANG):
    """
    Update the vendor's information.
    """
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    if not string:
        infos = []
        infos.append(_('Empty string.') + ' ' + _('Please, try again.'))
        body = bc_templates.tmpl_update_vendor_info_step1(infos=infos, ln=ln)

    elif string == '*':
        result = db.get_all_vendors()
        body = bc_templates.tmpl_update_vendor_info_step2(result=result, ln=ln)

    else:
        if column == 'name':
            result = db.search_vendor_by_name(string)
        else:
            result = db.search_vendor_by_email(string)
        body = bc_templates.tmpl_update_vendor_info_step2(result=result, ln=ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    body = bc_templates.tmpl_update_vendor_info_step2(result=result, ln=ln)

    return page(title=_("Update vendor information"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_vendor_info_step3(req, vendor_id, ln=CFG_SITE_LANG):
    """
    Update the library's information.

    vendor_id - identify the vendor. It is also the primary key of
                 the table crcVENDOR.

    """
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    vendor_info = db.get_vendor_details(vendor_id)

    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    body = bc_templates.tmpl_update_vendor_info_step3(vendor_info=vendor_info,
                                                                  ln=ln)

    return page(title=_("Update vendor information"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_vendor_info_step4(req, name, email, phone, address,
                             vendor_id, ln=CFG_SITE_LANG):
    """
    Update the vendor's information.
    """
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    tup_infos = (vendor_id, name, email, phone, address)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    body = bc_templates.tmpl_update_vendor_info_step4(tup_infos=tup_infos,
                                                                  ln=ln)

    return page(title=_("Update vendor information"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def update_vendor_info_step5(req, name, email, phone, address,
                             vendor_id, ln=CFG_SITE_LANG):
    """
    Update the library's information.
    """
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    db.update_vendor_info(vendor_id, name, email, phone, address)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    body = bc_templates.tmpl_update_vendor_info_step5(ln=ln)

    return page(title=_("Update vendor information"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def get_vendor_notes(req, vendor_id, add_notes, new_note, ln=CFG_SITE_LANG):
    """
    Retrieve notes related with a vendor.

    vendor_id - identify the vendor. It is also the primary key of
                the table crcVENDOR.

    @param add_notes:  display the textarea where will be written a new notes.

    @param new_notes:  note that will be added to the others vendor's notes.
    """
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    if new_note:
        date = '[' + time.ctime() + '] '
        new_line = '\n'
        new_note = date + new_note + new_line
        db.add_new_vendor_note(new_note, vendor_id)

    vendor_notes = db.get_vendor_notes(vendor_id)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    body = bc_templates.tmpl_vendor_notes(vendor_notes=vendor_notes,
                                                      vendor_id=vendor_id,
                                                      add_notes=add_notes,
                                                      ln=ln)
    return page(title=_("Vendor notes"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def search_vendor_step1(req, ln=CFG_SITE_LANG):
    """
    Display the form where we can search a vendor (by name or email).
    """
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    infos = []

    navtrail_previous_links = '<a class="navtrail"' \
                              ' href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    body = bc_templates.tmpl_search_vendor_step1(infos=infos,
                                                             ln=ln)

    return page(title=_("Search vendor"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def search_vendor_step2(req, column, string, ln=CFG_SITE_LANG):
    """
    Search a vendor and return a list with all the possible results, using the
    parameters received from the previous step.

    column - identify the column, of the table crcVENDOR, that will be
             considered during the search. Can be 'name' or 'email'.

    str - string used for the search process.
    """
    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    _ = gettext_set_language(ln)

    if not string:
        infos = []
        infos.append(_('Empty string.') + ' ' + _('Please, try again.'))
        body = bc_templates.tmpl_search_vendor_step1(infos=infos,
                                                             ln=ln)
    elif string == '*':
        result = db.get_all_vendors()
        body = bc_templates.tmpl_search_vendor_step2(result=result, ln=ln)

    else:
        if column == 'name':
            result = db.search_vendor_by_name(string)
        else:
            result = db.search_vendor_by_email(string)
        body = bc_templates.tmpl_search_vendor_step2(result=result, ln=ln)

    navtrail_previous_links = '<a class="navtrail" ' \
                              'href="%s/help/admin">Admin Area' \
                              '</a>' % (CFG_SITE_SECURE_URL,)

    return page(title=_("Search vendor"),
                uid=id_user,
                req=req,
                body=body, language=ln,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)
