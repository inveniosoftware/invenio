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


__revision__ = "$Id$"

# bibcirculation imports
import invenio.bibcirculation_dblayer as db
import invenio.template
bc_templates = invenio.template.load('bibcirculation')
from invenio.bibcirculationadminlib import load_template
# other invenio imports
from invenio.config import \
     CFG_SITE_LANG, \
     CFG_CERN_SITE, \
     CFG_SITE_URL
#from invenio.dateutils import get_datetext
#import datetime
#from invenio.urlutils import create_html_link
from invenio.webuser import collect_user_info
from invenio.mailutils import send_email
from invenio.messages import gettext_set_language
from invenio.bibcirculation_utils import book_title_from_MARC, \
     book_information_from_MARC, \
     create_ill_record, search_user, \
     tag_all_requests_as_done, \
     generate_new_due_date, \
     update_requests_statuses
     #make_copy_available, \
     #update_status_if_expired, \
     #book_information_from_MARC
from invenio.bibcirculation_cern_ldap import get_user_info_from_ldap
from invenio.bibcirculation_config import CFG_BIBCIRCULATION_LIBRARIAN_EMAIL, \
                                    CFG_BIBCIRCULATION_LOANS_EMAIL, \
                                    CFG_BIBCIRCULATION_REQUEST_STATUS_PENDING, \
                                    CFG_BIBCIRCULATION_REQUEST_STATUS_WAITING, \
                                    CFG_BIBCIRCULATION_ILL_STATUS_NEW


def perform_loanshistoricaloverview(uid, ln=CFG_SITE_LANG):
    """
    Display Loans historical overview for user uid.

    @param uid: user id
    @param ln: language of the page

    @return body(html)
    """
    invenio_user_email = db.get_invenio_user_email(uid)
    borrower_id = db.get_borrower_id_by_email(invenio_user_email)
    result = db.get_historical_overview(borrower_id)

    body = bc_templates.tmpl_loanshistoricaloverview(result=result, ln=ln)

    return body


def perform_borrower_loans(uid, barcode, borrower_id,
                           request_id, action, ln=CFG_SITE_LANG):
    """perofirme

    Display all the loans and the requests of a given borrower.

    @param barcode: identify the item. Primary key of crcITEM.
    @type barcode: string

    @param borrower_id: identify the borrower. Primary key of crcBORROWER.
    @type borrower_id: int

    @param request_id: identify the request: Primary key of crcLOANREQUEST
    @type request_id: int

    @return body(html)
    """

    _ = gettext_set_language(ln)

    infos = []

    borrower_id = db.get_borrower_id_by_email(db.get_invenio_user_email(uid))

    new_due_date = generate_new_due_date(30)

    #renew loan
    if action == 'renew':
        recid = db.get_id_bibrec(barcode)
        queue = db.get_queue_request(recid)

        if len(queue) != 0 and queue[0][0] != borrower_id:
            message = "It is not possible to renew your loan for %(x_strong_tag_open)s%(x_title)s%(x_strong_tag_close)s" % {'x_title': book_title_from_MARC(recid), 'x_strong_tag_open': '<strong>', 'x_strong_tag_close': '</strong>'}
            message += ' ' + _("Another user is waiting for this book.")
            infos.append(message)

        else:
            loan_id = db.get_current_loan_id(barcode)
            db.renew_loan(loan_id, new_due_date)
            #update_status_if_expired(loan_id)
            tag_all_requests_as_done(barcode, borrower_id)
            infos.append(_("Your loan has been renewed with sucess."))

    #cancel request
    elif action == 'cancel':
        db.cancel_request(request_id)
        barcode_requested = db.get_requested_barcode(request_id)
        update_requests_statuses(barcode_requested)

    #renew all loans
    elif action == 'renew_all':
        list_of_barcodes = db.get_borrower_loans_barcodes(borrower_id)
        for bc in list_of_barcodes:
            bc_recid = db.get_recid(bc)
            queue = db.get_queue_request(bc_recid)

            #check if there are requests
            if len(queue) != 0 and queue[0][0] != borrower_id:
                message = "It is not possible to renew your loan for %(x_strong_tag_open)s%(x_title)s%(x_strong_tag_close)s" % {'x_title': book_title_from_MARC(bc_recid), 'x_strong_tag_open': '<strong>', 'x_strong_tag_close': '</strong>'}
                message += ' ' + _("Another user is waiting for this book.")
                infos.append(message)
            else:
                loan_id = db.get_current_loan_id(bc)
                db.renew_loan(loan_id, new_due_date)
                #update_status_if_expired(loan_id)
                tag_all_requests_as_done(barcode, borrower_id)

        if infos == []:
            infos.append(_("All loans have been renewed with success."))

    loans = db.get_borrower_loans(borrower_id)
    requests = db.get_borrower_requests(borrower_id)

    body = bc_templates.tmpl_yourloans(loans=loans, requests=requests,
                                       borrower_id=borrower_id, infos=infos,
                                       ln=ln)
    return body

### with message ###
def perform_get_holdings_information(recid, req, ln=CFG_SITE_LANG):
    """
    Display all the copies of an item.

    @param recid: identify the record. Primary key of bibrec.
    @type recid: int

    @return body(html)
    """

    holdings_information = db.get_holdings_information(recid, False)

    body = bc_templates.tmpl_holdings_information2(recid=recid,
                                            req=req,
                                            holdings_info=holdings_information,
                                            ln=ln)

    return body

def perform_get_pending_request(ln=CFG_SITE_LANG):
    """
    @param ln: language of the page
    """

    status = db.get_loan_request_by_status(CFG_BIBCIRCULATION_REQUEST_STATUS_PENDING)

    body = bc_templates.tmpl_get_pending_request(status=status, ln=ln)

    return body


def perform_new_request(recid, barcode, ln=CFG_SITE_LANG):
    """
    Display form to be filled by the user.

    @param uid: user id
    @type: int

    @param recid: identify the record. Primary key of bibrec.
    @type recid: int

    @param barcode: identify the item. Primary key of crcITEM.
    @type barcode: string

    @return request form
    """

    body = bc_templates.tmpl_new_request(recid=recid, barcode=barcode, ln=ln)

    return body


def perform_new_request_send(uid, recid, period_from, period_to,
                             barcode, ln=CFG_SITE_LANG):

    """
    @param recid: recID - Invenio record identifier
    @param ln: language of the page
    """

    nb_requests = 0
    all_copies_on_loan = True
    copies = db.get_barcodes(recid)
    for bc in copies:
        nb_requests += db.get_number_requests_per_copy(bc)
        if db.is_item_on_loan(bc) is None:
            all_copies_on_loan = False

    if nb_requests == 0:
        if all_copies_on_loan:
            status = CFG_BIBCIRCULATION_REQUEST_STATUS_WAITING
        else:
            status = CFG_BIBCIRCULATION_REQUEST_STATUS_PENDING
    else:
        status = CFG_BIBCIRCULATION_REQUEST_STATUS_WAITING

    user = collect_user_info(uid)
    if CFG_CERN_SITE:
        try:
            borrower = search_user('ccid', user['external_hidden_personid'])
        except:
            borrower = ()
    else:
        borrower = search_user('email', user['email'])

    if borrower != ():
        borrower = borrower[0]
        borrower_id = borrower[0]
        borrower_details = db.get_borrower_details(borrower_id)
        (_id, ccid, name, email, _phone, address, mailbox) = borrower_details

        (title, year, author,
         isbn, publisher) = book_information_from_MARC(recid)

        req_id = db.new_hold_request(borrower_id, recid, barcode,
                                period_from, period_to, status)

        details = db.get_loan_request_details(req_id)
        if details:
            library = details[3]
            location = details[4]
            request_date = details[7]
        else:
            location = ''
            library = ''
            request_date = ''

        link_to_holdings_details = CFG_SITE_URL + \
                                   '/record/%s/holdings' % str(recid)

        link_to_item_request_details = CFG_SITE_URL + \
            "/admin2/bibcirculation/get_item_requests_details?ln=%s&recid=%s" \
                % (ln, str(recid))

        subject = 'New request'
        message_template = load_template('notification')

        message_for_user = message_template % (name, ccid, email, address,
                                        mailbox, title, author, publisher,
                                        year, isbn, location, library,
                                        link_to_holdings_details, request_date)

        message_for_librarian = message_template % (name, ccid, email, address,
                                        mailbox, title, author, publisher,
                                        year, isbn, location, library,
                                        link_to_item_request_details,
                                        request_date)

        if status == CFG_BIBCIRCULATION_REQUEST_STATUS_PENDING:
            send_email(fromaddr = CFG_BIBCIRCULATION_LIBRARIAN_EMAIL,
                       toaddr   = CFG_BIBCIRCULATION_LOANS_EMAIL,
                       subject  = subject,
                       content  = message_for_librarian,
                       header   = '',
                       footer   = '',
                       attempt_times=1,
                       attempt_sleeptime=10
                      )

        send_email(fromaddr = CFG_BIBCIRCULATION_LOANS_EMAIL,
                   toaddr   = email,
                   subject  = subject,
                   content  = message_for_user,
                   header   = '',
                   footer   = '',
                   attempt_times=1,
                   attempt_sleeptime=10
                  )

        if CFG_CERN_SITE:
            message = bc_templates.tmpl_message_request_send_ok_cern()
        else:
            message = bc_templates.tmpl_message_request_send_ok_other()

    else:
        if CFG_CERN_SITE:
            message = bc_templates.tmpl_message_request_send_fail_cern()
        else:
            message = bc_templates.tmpl_message_request_send_fail_other()

    body = bc_templates.tmpl_new_request_send(message=message, ln=ln)

    return body


def ill_request_with_recid(recid, ln=CFG_SITE_LANG):
    """
    Display ILL form.

    @param recid: identify the record. Primary key of bibrec.
    @type recid: int

    @param uid: user id
    @type: int
    """

    body = bc_templates.tmpl_ill_request_with_recid(recid=recid,
                                                    infos=[],
                                                    ln=ln)


    return body

 #(title, year, authors,
 # isbn, publisher) = book_information_from_MARC(int(recid))
 #book_info = {'title': title, 'authors': authors, 'place': place,
 #             'publisher': publisher, 'year' : year,  'edition': edition,
 #             'isbn' : isbn}

def ill_register_request_with_recid(recid, uid, period_of_interest_from,
                                    period_of_interest_to, additional_comments,
                                    conditions, only_edition,
                                    ln=CFG_SITE_LANG):
    """
    Register a new ILL request.

    @param recid: identify the record. Primary key of bibrec.
    @type recid: int

    @param uid: user id
    @type: int

    @param period_of_interest_from: period of interest - from(date)
    @type period_of_interest_from: string

    @param period_of_interest_to: period of interest - to(date)
    @type period_of_interest_to: string
    """

    _ = gettext_set_language(ln)

    # create a dictionnary
    book_info = {'recid': recid}

    user = collect_user_info(uid)
    borrower_id = db.get_borrower_id_by_email(user['email'])

    if borrower_id is None:
        if CFG_CERN_SITE == 1:
            result = get_user_info_from_ldap(email=user['email'])

            try:
                name = result['cn'][0]
            except KeyError:
                name = None

            try:
                email = result['mail'][0]
            except KeyError:
                email = None

            try:
                phone = result['telephoneNumber'][0]
            except KeyError:
                phone = None

            try:
                address = result['physicalDeliveryOfficeName'][0]
            except KeyError:
                address = None

            try:
                mailbox = result['postOfficeBox'][0]
            except KeyError:
                mailbox = None

            try:
                ccid = result['employeeID'][0]
            except KeyError:
                ccid = ''

            if address is not None:
                db.new_borrower(ccid, name, email, phone, address, mailbox, '')
            else:
                message = bc_templates.tmpl_message_request_send_fail_cern()
        else:
            message = bc_templates.tmpl_message_request_send_fail_other()

        return bc_templates.tmpl_ill_register_request_with_recid(
                                                            message=message,
                                                            ln=ln)

    address = db.get_borrower_address(user['email'])
    if not address:
        if CFG_CERN_SITE == 1:
            email = user['email']
            result = get_user_info_from_ldap(email)

            try:
                address = result['physicalDeliveryOfficeName'][0]
            except KeyError:
                address = None

            if address is not None:
                db.add_borrower_address(address, email)
            else:
                message = bc_templates.tmpl_message_request_send_fail_cern()
        else:
            message = bc_templates.tmpl_message_request_send_fail_other()

        return bc_templates.tmpl_ill_register_request_with_recid(
                                                               message=message,
                                                               ln=ln)

    if not conditions:
        infos = []
        infos.append(_("You didn't accept the ILL conditions."))
        return bc_templates.tmpl_ill_request_with_recid(recid,
                                                        infos=infos,
                                                        ln=ln)

    else:
        db.ill_register_request(book_info, borrower_id,
                                period_of_interest_from, period_of_interest_to,
                                CFG_BIBCIRCULATION_ILL_STATUS_NEW,
                                additional_comments,
                                only_edition or 'False','book')

        if CFG_CERN_SITE == 1:
            message = bc_templates.tmpl_message_request_send_ok_cern()
        else:
            message = bc_templates.tmpl_message_request_send_ok_other()

        #Notify librarian about new ILL request.
        send_email(fromaddr=CFG_BIBCIRCULATION_LIBRARIAN_EMAIL,
                    toaddr=CFG_BIBCIRCULATION_LOANS_EMAIL,
                    subject='ILL request for books confirmation',
                    content='',
                    #hold_request_mail(recid=recid, borrower_id=borrower_id),
                    attempt_times=1,
                    attempt_sleeptime=10)

        return bc_templates.tmpl_ill_register_request_with_recid(
                                                               message=message,
                                                               ln=ln)


def display_ill_form(ln=CFG_SITE_LANG):
    """
    Display ILL form

    @param uid: user id
    @type: int
    """

    body = bc_templates.tmpl_display_ill_form(infos=[], ln=ln)

    return body

def ill_register_request(uid, title, authors, place, publisher, year, edition,
                isbn, period_of_interest_from, period_of_interest_to,
                additional_comments, conditions, only_edition, request_type,
                ln=CFG_SITE_LANG):
    """
    Register new ILL request. Create new record (collection: ILL Books)

    @param uid: user id
    @type: int

    @param authors: book's authors
    @type authors: string

    @param place: place of publication
    @type place: string

    @param publisher: book's publisher
    @type publisher: string

    @param year: year of publication
    @type year: string

    @param edition: book's edition
    @type edition: string

    @param isbn: book's isbn
    @type isbn: string

    @param period_of_interest_from: period of interest - from(date)
    @type period_of_interest_from: string

    @param period_of_interest_to: period of interest - to(date)
    @type period_of_interest_to: string

    @param additional_comments: comments given by the user
    @type additional_comments: string

    @param conditions: ILL conditions
    @type conditions: boolean

    @param only_edition: borrower wants only the given edition
    @type only_edition: boolean
    """

    _ = gettext_set_language(ln)

    item_info = (title, authors, place, publisher, year, edition, isbn)
    create_ill_record(item_info)

    book_info = {'title': title, 'authors': authors, 'place': place,
                 'publisher': publisher, 'year': year, 'edition': edition,
                 'isbn': isbn}

    user = collect_user_info(uid)
    borrower_id = db.get_borrower_id_by_email(user['email'])

    #Check if borrower is on DB.
    if borrower_id != 0:
        address = db.get_borrower_address(user['email'])

        #Check if borrower has an address.
        if address != 0:

            #Check if borrower has accepted ILL conditions.
            if conditions:

                #Register ILL request on crcILLREQUEST.
                db.ill_register_request(book_info, borrower_id,
                                        period_of_interest_from,
                                        period_of_interest_to,
                                        CFG_BIBCIRCULATION_ILL_STATUS_NEW,
                                        additional_comments,
                                        only_edition or 'False', request_type)

                #Display confirmation message.
                message = _("Your ILL request has been registered and the " \
                          "document will be sent to you via internal mail.")

                #Notify librarian about new ILL request.
                send_email(fromaddr=CFG_BIBCIRCULATION_LIBRARIAN_EMAIL,
                               toaddr=CFG_BIBCIRCULATION_LOANS_EMAIL,
                               subject=_('ILL request for books confirmation'),
                               content="",
                               attempt_times=1,
                               attempt_sleeptime=10
                               )

            #Borrower did not accept ILL conditions.
            else:
                infos = []
                infos.append(_("You didn't accept the ILL conditions."))
                body = bc_templates.tmpl_display_ill_form(infos=infos, ln=ln)

        #Borrower doesn't have an address.
        else:

            #If BibCirculation at CERN, use LDAP.
            if CFG_CERN_SITE == 1:

                email = user['email']
                result = get_user_info_from_ldap(email)

                try:
                    ldap_address = result['physicalDeliveryOfficeName'][0]
                except KeyError:
                    ldap_address = None

                # verify address
                if ldap_address is not None:
                    db.add_borrower_address(ldap_address, email)

                    db.ill_register_request(book_info, borrower_id,
                                        period_of_interest_from,
                                        period_of_interest_to,
                                        CFG_BIBCIRCULATION_ILL_STATUS_NEW,
                                        additional_comments,
                                        only_edition or 'False',
                                        request_type)

                    message = _("Your ILL request has been registered and" \
                              " the document will be sent to you via" \
                              " internal mail.")


                    send_email(fromaddr=CFG_BIBCIRCULATION_LIBRARIAN_EMAIL,
                               toaddr=CFG_BIBCIRCULATION_LOANS_EMAIL,
                               subject=_('ILL request for books confirmation'),
                               content="",
                               attempt_times=1,
                               attempt_sleeptime=10
                               )
                else:
                    message = _("It is not possible to validate your request.")
                    message += ' ' + _("Your office address is not available.")
                    message += ' ' + _("Please contact %(contact_email)s") % \
                           {'contact_email': CFG_BIBCIRCULATION_LIBRARIAN_EMAIL}

    else:

        # Get information from CERN LDAP
        if CFG_CERN_SITE == 1:
            result = get_user_info_from_ldap(email=user['email'])

            try:
                name = result['cn'][0]
            except KeyError:
                name = None

            try:
                email = result['mail'][0]
            except KeyError:
                email = None

            try:
                phone = result['telephoneNumber'][0]
            except KeyError:
                phone = None

            try:
                address = result['physicalDeliveryOfficeName'][0]
            except KeyError:
                address = None

            try:
                mailbox = result['postOfficeBox'][0]
            except KeyError:
                mailbox = None

            try:
                ccid = result['employeeID'][0]
            except KeyError:
                ccid = ''

            # verify address
            if address is not None:
                db.new_borrower(ccid, name, email, phone, address, mailbox, '')

                borrower_id = db.get_borrower_id_by_email(email)

                db.ill_register_request(book_info, borrower_id,
                                        period_of_interest_from,
                                        period_of_interest_to,
                                        CFG_BIBCIRCULATION_ILL_STATUS_NEW,
                                        additional_comments,
                                        only_edition or 'False',
                                        request_type)

                message = _("Your ILL request has been registered and" \
                          " the document will be sent to you via" \
                          " internal mail.")

                send_email(fromaddr=CFG_BIBCIRCULATION_LIBRARIAN_EMAIL,
                           toaddr=CFG_BIBCIRCULATION_LOANS_EMAIL,
                           subject='ILL request for books confirmation',
                           content="",
                           attempt_times=1,
                           attempt_sleeptime=10
                           )

            else:
                message = _("It is not possible to validate your request.")
                message += ' ' + _("Your office address is not available.")
                message += ' ' + _("Please contact %(contact_email)s") % \
                           {'contact_email': CFG_BIBCIRCULATION_LIBRARIAN_EMAIL}

    body = bc_templates.tmpl_ill_register_request_with_recid(message=message,
                                                             ln=ln)

    return body
