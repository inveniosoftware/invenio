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

"""BibCirculation .........."""

__revision__ = "$Id$"

# bibcirculation imports
import invenio.bibcirculation_dblayer as db
import invenio.template
bibcirculation_templates = invenio.template.load('bibcirculation')

# others invenio imports
from invenio.config import \
     CFG_SITE_LANG, \
     CFG_CERN_SITE, \
     CFG_SITE_SUPPORT_EMAIL
from invenio.dateutils import get_datetext
import datetime
from invenio.webuser import collect_user_info
from invenio.mailutils import send_email
from invenio.bibcirculation_utils import hold_request_mail, \
     book_title_from_MARC, \
     make_copy_available, \
     create_ill_record
     #book_information_from_MARC
from invenio.bibcirculation_cern_ldap import get_user_info_from_ldap
from invenio.bibcirculation_config import CFG_BIBCIRCULATION_LIBRARIAN_EMAIL


def perform_loanshistoricaloverview(uid, ln=CFG_SITE_LANG):
    """
    Display Loans historical overview for user uid.

    @param uid: user id
    @param ln: language of the page

    @return body(html)
    """
    invenio_user_email = db.get_invenio_user_email(uid)
    is_borrower = db.is_borrower(invenio_user_email)
    result = db.get_historical_overview(is_borrower)

    body = bibcirculation_templates.tmpl_loanshistoricaloverview(result=result,
                                                                 ln=ln)

    return body


def perform_borrower_loans(uid, barcode, borrower_id,
                           request_id, ln=CFG_SITE_LANG):
    """
    Display all the loans and the requests of a given borrower.

    @param barcode: identify the item. Primary key of crcITEM.
    @type barcode: string

    @param borrower_id: identify the borrower. Primary key of crcBORROWER.
    @type borrower_id: int

    @param request_id: identify the request: Primary key of crcLOANREQUEST
    @type request_id: int

    @return body(html)
    """

    infos = []

    is_borrower = db.is_borrower(db.get_invenio_user_email(uid))
    loans = db.get_borrower_loans(is_borrower)
    requests = db.get_borrower_requests(is_borrower)

    tmp_date = datetime.date.today() + datetime.timedelta(days=30)
    new_due_date = get_datetext(tmp_date.year, tmp_date.month, tmp_date.day)

    #renew loan
    if barcode:
        recid = db.get_id_bibrec(barcode)
        queue = db.get_queue_request(recid)

        if len(queue) != 0:
            infos.append("It is not possible to renew your loan for " \
                         "<strong>" + book_title_from_MARC(recid) + "</strong>. Another user " \
                         "is waiting for this book.")
        else:
            db.update_due_date(barcode, new_due_date)
            infos.append("Your loan has been renewed with sucess.")

    #cancel request
    if request_id:
        db.cancel_request(request_id, 'cancelled')
        make_copy_available(request_id)

    #renew all loans
    elif borrower_id:
        list_of_recids = db.get_borrower_recids(borrower_id)
        for (recid) in list_of_recids:
            queue = db.get_queue_request(recid[0])

            #check if there are requests
            if len(queue) != 0:
                infos.append("It is not possible to renew your loan for " \
                             "<strong>" + book_title_from_MARC(recid) + "</strong>. Another user" \
                             " is waiting for this book.")
            else:
                db.update_due_date_borrower(borrower_id,
                                            new_due_date)
        infos.append("All loans have been renewed with success.")

    body = bibcirculation_templates.tmpl_yourloans(loans=loans,
                                                   requests=requests,
                                                   borrower_id=is_borrower,
                                                   infos=infos,
                                                   ln=ln)

    return body

def perform_get_holdings_information(recid, req, ln=CFG_SITE_LANG):
    """
    Display all the copies of an item.

    @param recid: identify the record. Primary key of bibrec.
    @type recid: int

    @return body(html)
    """

    holdings_information = db.get_holdings_information(recid)

    body = bibcirculation_templates.tmpl_holdings_information2(recid=recid,
                                                               req=req,
                                                               holdings_info=holdings_information,
                                                               ln=ln)
    return body


def perform_get_pending_request(ln=CFG_SITE_LANG):
    """
    @param ln: language of the page
    """

    status = db.get_loan_request_by_status("pending")

    body = bibcirculation_templates.tmpl_get_pending_request(status=status,
                                                                  ln=ln)

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

    body = bibcirculation_templates.tmpl_new_request2(recid=recid,
                                                      barcode=barcode,
                                                      ln=ln)

    return body


def perform_new_request_send(uid, recid,
                             period_from, period_to,
                             barcode, ln=CFG_SITE_LANG):

    """
    @param recid: recID - Invenio record identifier
    @param ln: language of the page
    """

    nb_requests = db.get_number_requests_per_copy(barcode)
    is_on_loan = db.is_item_on_loan(barcode)

    if nb_requests == 0 and is_on_loan is not None:
        status = 'waiting'
    elif nb_requests == 0 and is_on_loan is None:
        status = 'pending'
    else:
        status = 'waiting'

    user = collect_user_info(uid)
    is_borrower = db.is_borrower(user['email'])

    if is_borrower != 0:
        address = db.get_borrower_address(user['email'])
        if address != 0:

            db.new_hold_request(is_borrower, recid, barcode,
                                period_from, period_to, status)

            is_on_loan=db.is_item_on_loan(barcode)

            db.update_item_status('requested', barcode)

            if not is_on_loan:
                send_email(fromaddr=CFG_BIBCIRCULATION_LIBRARIAN_EMAIL,
                       toaddr=CFG_SITE_SUPPORT_EMAIL,
                       subject='Hold request for books confirmation',
                       content=hold_request_mail(recid, is_borrower),
                       attempt_times=1,
                       attempt_sleeptime=10
                       )
            if CFG_CERN_SITE == 1:
                message = bibcirculation_templates.tmpl_message_request_send_ok_cern()
            else:
                message = bibcirculation_templates.tmpl_message_request_send_ok_other()

        else:
            if CFG_CERN_SITE == 1:
                email=user['email']
                result = get_user_info_from_ldap(email)

                try:
                    ldap_address = result['physicalDeliveryOfficeName'][0]
                except KeyError:
                    ldap_address = None

                if ldap_address is not None:
                    db.add_borrower_address(ldap_address, email)

                    db.new_hold_request(is_borrower, recid, barcode,
                                        period_from, period_to, status)

                    db.update_item_status('requested', barcode)

                    send_email(fromaddr=CFG_BIBCIRCULATION_LIBRARIAN_EMAIL,
                               toaddr=CFG_SITE_SUPPORT_EMAIL,
                               subject='Hold request for books confirmation',
                               content=hold_request_mail(recid, is_borrower),
                               attempt_times=1,
                               attempt_sleeptime=10
                               )

                    message = bibcirculation_templates.tmpl_message_request_send_ok_cern(ln=ln)

                else:
                    message = bibcirculation_templates.tmpl_message_request_send_fail_cern(ln=ln)

            else:
                message = bibcirculation_templates.tmpl_message_request_send_fail_other(ln=ln)


    else:
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

            if address is not None:
                db.new_borrower(name, email, phone, address, mailbox, '')

                is_borrower = db.is_borrower(email)

                db.new_hold_request(is_borrower, recid, barcode,
                                    period_from, period_to, status)

                db.update_item_status('requested', barcode)

                send_email(fromaddr=CFG_BIBCIRCULATION_LIBRARIAN_EMAIL,
                           toaddr=CFG_BIBCIRCULATION_LIBRARIAN_EMAIL,
                           subject='Hold request for books confirmation',
                           content=hold_request_mail(recid, is_borrower),
                           attempt_times=1,
                           attempt_sleeptime=10
                           )
                message = bibcirculation_templates.tmpl_message_request_send_ok_cern()

            else:
                message = bibcirculation_templates.tmpl_message_request_send_fail_cern()

        else:
            message = bibcirculation_templates.tmpl_message_request_send_ok_other()

    body = bibcirculation_templates.tmpl_new_request_send(message=message, ln=ln)

    return body


def ill_request_with_recid(recid, ln=CFG_SITE_LANG):
    """
    Display ILL form.

    @param recid: identify the record. Primary key of bibrec.
    @type recid: int

    @param uid: user id
    @type: int
    """

    body = bibcirculation_templates.tmpl_ill_request_with_recid(recid=recid, infos=[], ln=ln)


    return body

 #(title, year, authors, isbn, publisher) = book_information_from_MARC(int(recid))
 #book_info = {'title': title, 'authors': authors, 'place': place, 'publisher': publisher,
 #                'year' : year,  'edition': edition, 'isbn' : isbn}

def ill_register_request_with_recid(recid, uid, period_of_interest_from,
                                    period_of_interest_to, additional_comments,
                                    conditions, only_edition, ln=CFG_SITE_LANG):
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


    # create a dictionnary
    book_info = {'recid': recid}



    user = collect_user_info(uid)
    is_borrower = db.is_borrower(user['email'])

    if is_borrower == 0:
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

            if address is not None:
                db.new_borrower(name, email, phone, address, mailbox, '')
            else:
                message = bibcirculation_templates.tmpl_message_request_send_fail_cern()
        else:
            message = bibcirculation_templates.tmpl_message_request_send_fail_other()

        return bibcirculation_templates.tmpl_ill_register_request_with_recid(message=message, ln=ln)

    address = db.get_borrower_address(user['email'])
    if address == 0:
        if CFG_CERN_SITE == 1:
            email=user['email']
            result = get_user_info_from_ldap(email)

            try:
                address = result['physicalDeliveryOfficeName'][0]
            except KeyError:
                address = None

            if address is not None:
                db.add_borrower_address(address, email)
            else:
                message = bibcirculation_templates.tmpl_message_request_send_fail_cern()
        else:
            message = bibcirculation_templates.tmpl_message_request_send_fail_other()

        return bibcirculation_templates.tmpl_ill_register_request_with_recid(message=message, ln=ln)

    if not conditions:
        infos = []
        infos.append("You didn't accept the ILL conditions.")
        return bibcirculation_templates.tmpl_ill_request_with_recid(recid, infos=infos, ln=ln)

    else:
        db.ill_register_request(book_info, is_borrower, period_of_interest_from,
                                period_of_interest_to, 'new', additional_comments,
                                only_edition or 'False','book')

        if CFG_CERN_SITE == 1:
            message = bibcirculation_templates.tmpl_message_request_send_ok_cern()
        else:
            message = bibcirculation_templates.tmpl_message_request_send_ok_other()

        #Notify librarian about new ILL request.
        send_email(fromaddr=CFG_BIBCIRCULATION_LIBRARIAN_EMAIL,
                    toaddr="piubrau@gmail.com",
                    subject='ILL request for books confirmation',
                    content=hold_request_mail(recid, is_borrower),
                    attempt_times=1,
                    attempt_sleeptime=10)

        return bibcirculation_templates.tmpl_ill_register_request_with_recid(message=message, ln=ln)


def display_ill_form(ln=CFG_SITE_LANG):
    """
    Display ILL form

    @param uid: user id
    @type: int
    """

    body = bibcirculation_templates.tmpl_display_ill_form(infos=[], ln=ln)

    return body

def ill_register_request(uid, title, authors, place, publisher, year, edition,
                         isbn, period_of_interest_from, period_of_interest_to,
                         additional_comments, conditions, only_edition, request_type, ln=CFG_SITE_LANG):
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

    item_info = (title, authors, place, publisher, year, edition, isbn)
    create_ill_record(item_info)

    book_info = {'title': title, 'authors': authors, 'place': place, 'publisher': publisher,
                 'year': year, 'edition': edition, 'isbn': isbn}

    user = collect_user_info(uid)
    is_borrower = db.is_borrower(user['email'])

    #Check if borrower is on DB.
    if is_borrower != 0:
        address = db.get_borrower_address(user['email'])

        #Check if borrower has an address.
        if address != 0:

            #Check if borrower has accepted ILL conditions.
            if conditions:

                #Register ILL request on crcILLREQUEST.
                db.ill_register_request(book_info, is_borrower, period_of_interest_from,
                                        period_of_interest_to, 'new', additional_comments,
                                        only_edition or 'False', request_type)

                #Display confirmation message.
                message = "Your ILL request has been registered and the " \
                          "document will be sent to you via internal mail."

                #Notify librarian about new ILL request.
                send_email(fromaddr=CFG_BIBCIRCULATION_LIBRARIAN_EMAIL,
                               toaddr=CFG_SITE_SUPPORT_EMAIL,
                               subject='ILL request for books confirmation',
                               content="",
                               attempt_times=1,
                               attempt_sleeptime=10
                               )

            #Borrower did not accept ILL conditions.
            else:
                infos = []
                infos.append("You didn't accept the ILL conditions.")
                body = bibcirculation_templates.tmpl_display_ill_form(infos=infos, ln=ln)

        #Borrower doesn't have an address.
        else:

            #If BibCirculation at CERN, use LDAP.
            if CFG_CERN_SITE == 1:
                email=user['email']
                result = get_user_info_from_ldap(email)

                try:
                    ldap_address = result['physicalDeliveryOfficeName'][0]
                except KeyError:
                    ldap_address = None

                # verify address
                if ldap_address is not None:
                    db.add_borrower_address(ldap_address, email)

                    db.ill_register_request(book_info, is_borrower, period_of_interest_from,
                                        period_of_interest_to, 'new', additional_comments,
                                        only_edition or 'False', request_type)

                    message = "Your ILL request has been registered and the document"\
                              " will be sent to you via internal mail."


                    send_email(fromaddr=CFG_BIBCIRCULATION_LIBRARIAN_EMAIL,
                               toaddr=CFG_SITE_SUPPORT_EMAIL,
                               subject='ILL request for books confirmation',
                               content="",
                               attempt_times=1,
                               attempt_sleeptime=10
                               )
                else:
                    message = "It is not possible to validate your request. "\
                              "Your office address is not available. "\
                              "Please contact ... "

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

            # verify address
            if address is not None:
                db.new_borrower(name, email, phone, address, mailbox, '')

                is_borrower = db.is_borrower(email)

                db.ill_register_request(book_info, is_borrower, period_of_interest_from,
                                        period_of_interest_to, 'new', additional_comments,
                                        only_edition or 'False', request_type)

                message = "Your ILL request has been registered and the document"\
                          " will be sent to you via internal mail."

                send_email(fromaddr=CFG_BIBCIRCULATION_LIBRARIAN_EMAIL,
                           toaddr=CFG_SITE_SUPPORT_EMAIL,
                           subject='ILL request for books confirmation',
                           content="",
                           attempt_times=1,
                           attempt_sleeptime=10
                           )

            else:
                message = "It is not possible to validate your request. "\
                          "Your office address is not available."\
                          " Please contact ... "

    body = bibcirculation_templates.tmpl_ill_register_request_with_recid(message=message, ln=ln)


    return body
