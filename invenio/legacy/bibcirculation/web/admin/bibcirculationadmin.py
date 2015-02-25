# This file is part of Invenio.
# Copyright (C) 2008, 2009, 2010, 2011 CERN.
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

"""Invenio BibCirculation Administrator (URLs) Interface."""

__revision__ = ""

import invenio.legacy.bibcirculation.adminlib as bal
from invenio.config import CFG_SITE_LANG
from invenio.utils.url import wash_url_argument

def index(req, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py
    """
    return bal.index(req, ln)

def borrower_search(req, empty_barcode=None, redirect_to_new_request=False,
                    ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/borrowers_search
    """
    return bal.borrower_search(req, empty_barcode,
                               redirect_to_new_request=redirect_to_new_request, ln=ln)


def item_search(req, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/holdings_search
    """
    return bal.item_search(req, [], ln)


def borrower_notification(req, borrower_id=None, template=None,
                          message=None, load_msg_template=None,
                          subject=None, send_message=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/borrower_notification
    """
    return bal.borrower_notification(req, borrower_id, template,
                                     message, load_msg_template,
                                     subject, send_message, ln)


def get_pending_requests(req, request_id=None, print_data=None,
                         ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/get_pending_requests
    """
    return bal.get_pending_requests(req, request_id, print_data, ln)


def item_search_result(req, p=None, f=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/item_search_result
    """

    return bal.item_search_result(req, p, f, ln)

def loan_return(req, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/loan_return
    """
    return bal.loan_return(req, ln)

def loan_on_desk_step1(req, key=None, string=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step1
    """

    return bal.loan_on_desk_step1(req, key, string, ln)


def loan_on_desk_step2(req, user_info=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step2
    """

    user_info = user_info.split(',')


    return bal.loan_on_desk_step2(req, user_info, ln)

def loan_on_desk_step3(req, user_info=None, barcode=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step4
    """

    user_info = eval(user_info)

    return bal.loan_on_desk_step3(req, user_info, barcode, ln)

def loan_on_desk_step4(req, list_of_books=None, user_info=None, due_date=None,
                       note=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_step5
    """

    user_info = eval(user_info)

    list_of_books = eval(list_of_books)
    due_date = wash_url_argument(due_date, 'list')


    return bal.loan_on_desk_step4(req, list_of_books, user_info,
                                  due_date, note, ln)


def loan_on_desk_confirm(req, barcode=None, borrower_id=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_confirm
    """
    return bal.loan_on_desk_confirm(req, barcode, borrower_id, ln)


def register_new_loan(req, barcode=None, borrower_id=None, request_id=None,
                      new_note=None, print_data=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/register_new_loan
    """

    return bal.register_new_loan(req, barcode, borrower_id, request_id,
                                 new_note, print_data, ln)


def loan_return_confirm(req, barcode=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/loan_return_confirm
    """
    return bal.loan_return_confirm(req, barcode, ln)


def get_next_waiting_loan_request(req, recid=None, barcode=None, check_id=None,
                                  ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/get_next_waiting_loan_request
    """
    return bal.get_next_waiting_loan_request(req, recid, barcode, check_id, ln)


def make_new_loan_from_request(req, check_id=None, barcode=None,
                               ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/make_new_loan_from_request
    """
    return bal.make_new_loan_from_request(req, check_id,
                                               barcode, ln)


def all_requests(req, request_id=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/all_requests
    """
    return bal.all_requests(req, request_id, ln)

def get_item_req_historical_overview(req, recid=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/get_item_req_historical_overview
    """
    return bal.get_item_req_historical_overview(req, recid, ln)

def get_item_loans_historical_overview(req, recid=None, ln=CFG_SITE_LANG):
    """
 http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/get_item_loans_historical_overview
    """
    return bal.get_item_loans_historical_overview(req, recid, ln)

#def all_loans_test(req, ln=CFG_SITE_LANG):
#    """
#    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/all_loans
#    """
#    return bal.all_loans_test(req, ln)

def all_loans(req, msg=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/all_loans
    """

    return bal.all_loans(req, msg=msg, ln=ln)

def bor_loans_historical_overview(req, borrower_id=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/bor_loans_historical_overview
    """
    return bal.bor_loans_historical_overview(req, borrower_id, ln)

def bor_requests_historical_overview(req, borrower_id=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/bor_requests_historical_overview
    """
    return bal.bor_requests_historical_overview(req, borrower_id, ln)


def get_item_requests_details(req, recid=None, request_id=None,
                              ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/borrowers_search
    """
    return bal.get_item_requests_details(req, recid, request_id, ln)


def get_item_loans_details(req, recid=None, barcode=None, loan_id=None,
                           force=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/borrowers_search
    """
    return bal.get_item_loans_details(req, recid, barcode, loan_id, force, ln)


def get_borrower_details(req, borrower_id=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/borrowers_search
    """
    return bal.get_borrower_details(req, borrower_id, ln)

def get_item_details(req, recid=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/borrowers_search
    """
    return bal.get_item_details(req, recid, ln)

def get_library_details(req, library_id=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/get_library_details
    """
    return bal.get_library_details(req, library_id, ln)

def get_borrower_requests_details(req, borrower_id=None, request_id=None,
                                  ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/get_borrower_requests_details
    """
    return bal.get_borrower_requests_details(req, borrower_id, request_id, ln)


def get_borrower_loans_details(req, recid=None, barcode=None, borrower_id=None,
                               renewall=None, force=None, loan_id=None,
                               ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/get_borrower_loans_details
    """
    return bal.get_borrower_loans_details(req, recid, barcode, borrower_id,
                                          renewall, force, loan_id, ln)


def borrower_search_result(req, column, string, redirect_to_new_request=False,
                           ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/borrower_search_result
    """

    return bal.borrower_search_result(req, column, string,
                        redirect_to_new_request=redirect_to_new_request, ln=ln)


def associate_barcode(req, request_id=None, recid=None, borrower_id=None,
                      ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/associate_barcode
    """
    return bal.associate_barcode(req, request_id, recid, borrower_id, ln)

def get_borrower_notes(req, borrower_id=None, delete_key=None,
                       library_notes=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/get_borrower_notes
    """
    return bal.get_borrower_notes(req, borrower_id, delete_key,
                                  library_notes, ln)

def get_loans_notes(req, loan_id=None, recid=None, delete_key=None,
                    library_notes=None, back="", ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/get_loans_notes
    """
    return bal.get_loans_notes(req, loan_id, delete_key,
                               library_notes, back, ln)

def get_item_loans_notes(req, loan_id=None, recid=None,
                         add_notes=None, new_note=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/get_item_loans_notes
    """
    return bal.get_item_loans_notes(req, loan_id, recid, add_notes,
                                    new_note, ln)


def new_item(req, isbn=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/new_item
    """
    return bal.new_item(req, isbn, ln)

def add_new_borrower_step1(req, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/add_new_borrower_step1
    """
    return bal.add_new_borrower_step1(req, ln)

def add_new_borrower_step2(req, name=None, email=None, phone=None, address=None,
                           mailbox=None, notes=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/add_new_borrower_step2
    """
    return bal.add_new_borrower_step2(req, name, email, phone, address,
                                      mailbox, notes, ln)

def add_new_borrower_step3(req, tup_infos=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/add_new_borrower_step3
    """
    tup_infos = eval(tup_infos)

    return bal.add_new_borrower_step3(req, tup_infos, ln)

def update_borrower_info_step1(req, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/update_borrower_info_step1
    """
    return bal.update_borrower_info_step1(req, ln)

def update_borrower_info_step2(req, column=None, string=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/update_borrower_info_step2
    """
    return bal.update_borrower_info_step2(req, column, string, ln)

def update_borrower_info_step1(req, borrower_id=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/update_borrower_info_step1
    """
    return bal.update_borrower_info_step1(req, borrower_id, ln)

def update_borrower_info_step2(req, name=None, email=None, phone=None,
                               address=None, mailbox=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/update_borrower_info_step2
    """
    return bal.update_borrower_info_step2(req, name, email, phone, address,
                                          mailbox, ln)

def add_new_library_step1(req, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/add_new_library_step1
    """
    return bal.add_new_library_step1(req, ln)

def add_new_library_step2(req, name=None, email=None, phone=None, address=None,
                          type=None, notes=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/add_new_library_step2
    """
    return bal.add_new_library_step2(req, name, email, phone, address,
                                     type, notes, ln)

def add_new_library_step3(req, tup_infos=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/add_new_library_step3
    """
    tup_infos = eval(tup_infos)

    return bal.add_new_library_step3(req, tup_infos, ln)

def update_library_info_step1(req, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/update_library_info_step1
    """
    return bal.update_library_info_step1(req, ln)

def update_library_info_step2(req, column=None, string=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/update_library_info_step2
    """
    return bal.update_library_info_step2(req, column, string, ln)

def update_library_info_step3(req, library_id=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/update_library_info_step3
    """
    return bal.update_library_info_step3(req, library_id, ln)

def update_library_info_step4(req, name=None, email=None, phone=None,
                              address=None, library_id=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/update_library_info_step4
    """
    return bal.update_library_info_step4(req, name, email, phone, address,
                                         library_id, ln)

def update_library_info_step5(req, tup_infos, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/update_library_info_step5
    """
    tup_infos = eval(tup_infos)

    return bal.update_library_info_step5(req, tup_infos, ln)

def new_book_step1(req,ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/new_book_step1
    """
    return bal.new_book_step1(req, ln)

def new_book_step2(req,ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/new_book_step2
    """
    return bal.new_book_step2(req, ln)

def add_new_copy_step1(req, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/add_new_copy_step1
    """
    return bal.add_new_copy_step1(req)

def add_new_copy_step2(req, p=None, f=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/add_new_copy_step2
    """
    return bal.add_new_copy_step2(req, p, f, ln)

def add_new_copy_step3(req, recid=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/add_new_copy_step3
    """
    return bal.add_new_copy_step3(req, recid, ln)

def add_new_copy_step4(req, barcode=None, library=None, location=None,
                       collection=None, description=None, loan_period=None,
                       status=None, recid=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/add_new_copy_step4
    """
    return bal.add_new_copy_step4(req, barcode, library, location, collection,
                                  description, loan_period, status, recid, ln)

def add_new_copy_step5(req, tup_infos=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/add_new_copy_step5
    """
    tup_infos = eval(tup_infos)
    return bal.add_new_copy_step5(req, tup_infos, ln)

def update_item_info_step1(req, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/update_item_info_step1
    """
    return bal.update_item_info_step1(req, ln)

def update_item_info_step2(req, p, f, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/update_item_info_step2
    """
    return bal.update_item_info_step2(req, p, f, ln)

def update_item_info_step3(req, recid, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/update_item_info_step3
    """
    return bal.update_item_info_step3(req, recid, ln)

def update_item_info_step4(req, barcode, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/update_item_info_step4
    """
    return bal.update_item_info_step4(req, barcode, ln)

def update_item_info_step5(req, barcode, library, location, collection,
                           description, loan_period, status, recid,
                           ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/update_item_info_step5
    """
    return bal.update_item_info_step5(req, barcode, library, location,
                                      collection, description, loan_period,
                                      status, recid, ln)

def update_item_info_step6(req, tup_infos, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/update_item_info_step6
    """
    tup_infos = eval(tup_infos)

    return bal.update_item_info_step6(req, tup_infos, ln)

def search_library_step1(req, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/search_library_step1
    """
    return bal.search_library_step1(req=req, ln=ln)

def search_library_step2(req, column, string, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/search_library_step2
    """

    return bal.search_library_step2(req, column, string, ln)

def get_library_notes(req, library_id=None, delete_key=None, library_notes=None,
                      ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/get_library_notes
    """
    return bal.get_library_notes(req, library_id, delete_key, library_notes, ln)

def change_due_date_step1(req, loan_id=None, borrower_id=None,
                          ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/change_due_date_step1
    """
    return bal.change_due_date_step1(req, loan_id, borrower_id, ln)

def change_due_date_step2(req, due_date=None, loan_id=None, borrower_id=None,
                          ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/change_due_date_step2
    """
    return bal.change_due_date_step2(req, due_date, loan_id, borrower_id, ln)

def claim_book_return(req, borrower_id=None, recid=None, loan_id=None,
                      template=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/claim_book_return
    """
    return bal.claim_book_return(req, borrower_id, recid, loan_id, template, ln)

def all_expired_loans(req, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/all_expired_loans
    """

    return bal.all_expired_loans(req, ln)

def get_waiting_requests(req, request_id=None, print_data=None,
                         ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/get_waiting_requests
    """
    return bal.get_waiting_requests(req, request_id, print_data, ln)

def create_new_loan_step1(req, borrower_id=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/create_new_loan_step1
    """
    return bal.create_new_loan_step1(req, borrower_id, ln)

def create_new_loan_step2(req, borrower_id=None, barcode=None, notes=None,
                          ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/create_new_loan_step2
    """
    return bal.create_new_loan_step2(req, borrower_id, barcode, notes, ln)

def create_new_request_step1(req, borrower_id=None, p=None, f=None, search=None,
                             ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/create_new_request_step1
    """
    return bal.create_new_request_step1(req, borrower_id, p, f, search, ln)

def create_new_request_step2(req, recid=None, borrower_id=None,
                             ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/create_new_request_step2
    """
    return bal.create_new_request_step2(req, recid, borrower_id, ln)

def create_new_request_step3(req, borrower_id=None, barcode=None, recid=None,
                             ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/create_new_request_step3
    """
    return bal.create_new_request_step3(req, borrower_id, barcode, recid, ln)

def create_new_request_step4(req, period_from=None, period_to=None,
                             barcode=None, borrower_id=None, recid=None,
                             ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/create_new_request_step4
    """
    return bal.create_new_request_step4(req, period_from, period_to, barcode,
                                        borrower_id, recid, ln)

def place_new_request_step1(req, barcode=None, recid=None, key=None,
                            string=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/place_new_request_step1

    """
    return bal.place_new_request_step1(req, barcode, recid, key, string, ln)


def place_new_request_step2(req, barcode=None, recid=None, user_info=None,
                            ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/place_new_request_step2
    """

    if user_info is not None:
        user_info = user_info.split(',')

    return bal.place_new_request_step2(req, barcode, recid, user_info, ln)


def place_new_request_step3(req, barcode=None, recid=None, user_info=None,
                            period_from=None, period_to=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/place_new_request_step3
    """
    user_info = eval(user_info)

    return bal.place_new_request_step3(req, barcode, recid, user_info,
                                       period_from, period_to, ln)


def place_new_loan_step1(req, barcode=None, recid=None, key=None,
                         string=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/place_new_loan_step1
    """
    return bal.place_new_loan_step1(req, barcode, recid, key, string, ln)


def place_new_loan_step2(req, barcode=None, recid=None, user_info=None,
                         ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/place_new_loan_step2
    """
    return bal.place_new_loan_step2(req, barcode, recid, user_info, ln)


def place_new_loan_step3(req, barcode=None, recid=None, ccid=None, name=None,
                         email=None, phone=None, address=None, mailbox=None,
                         due_date=None, notes=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/place_new_loan_step3
    """
    return bal.place_new_loan_step3(req, barcode, recid, ccid, name, email,
                                    phone, address, mailbox, due_date, notes,
                                    ln)

def order_new_copy_step1(req, recid=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/order_new_copy_step1
    """

    return bal.order_new_copy_step1(req, recid, ln)

def order_new_copy_step2 (req, recid=None, barcode=None, vendor_id=None,
                          cost=None, currency=None, status=None,
                          order_date=None, expected_date=None,
                          library_id=None, notes=None, ln=CFG_SITE_LANG):

    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/order_new_copy_step2
    """

    return bal.order_new_copy_step2(req, recid, barcode, vendor_id, cost,
                                    currency, status, order_date, expected_date,
                                    library_id, notes, ln)

def order_new_copy_step3(req, order_info=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/order_new_copy_step3
    """

    order_info = eval(order_info)

    return bal.order_new_copy_step3(req, order_info, ln)


def ordered_books(req, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/ordered_books
    """

    return bal.list_ordered_books(req, ln)

def get_purchase_notes(req, purchase_id=None, delete_key=None,
                       library_notes=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/get_purchase_notes
    """

    return bal.get_purchase_notes(req, purchase_id, delete_key,
                                  library_notes, ln)

def register_ill_request_step0(req, recid=None, key=None, string=None,
                               ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/register_ill_request_step0
    """
    return bal.register_ill_request_step0(req, recid, key, string, ln)

def register_ill_request_step1(req, recid=None, user_info=None,
                               ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/register_ill_request_step1
    """

    return bal.register_ill_request_step1(req, recid, user_info, ln)

def register_ill_request_step2(req, recid=None, user_info=None,
                               period_of_interest_from=None,
                               period_of_interest_to=None, notes=None,
                               only_edition=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/register_ill_request_step2
    """

    return bal.register_ill_request_step2(req, recid, user_info,
                                          period_of_interest_from,
                                          period_of_interest_to,
                                          notes, only_edition, ln)

def register_ill_request_step3(req, borrower_id=None, request_info=None,
                               ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/register_ill_request_step3
    """

    request_info = eval(request_info)

    return bal.register_ill_request_step3(req, borrower_id, request_info, ln)

def list_ill_request(req, status=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/list_ill_request
    """

    return bal.list_ill_request(req, status, ln)

def ill_request_details_step1(req, delete_key=None, ill_request_id=None,
                              new_status=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/ill_request_details_step1
    """

    return bal.ill_request_details_step1(req, delete_key, ill_request_id,
                                         new_status, ln)


def ill_request_details_step2(req, delete_key=None, ill_request_id=None,
                              new_status=None, library_id=None,
                              request_date=None, expected_date=None,
                              arrival_date=None, due_date=None,
                              return_date=None, cost=None,
                              currency=None, barcode=None, library_notes=None,
                              ln=CFG_SITE_LANG):

    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/ill_request_details_step2
    """


    return bal.ill_request_details_step2(req, delete_key, ill_request_id,
                                         new_status, library_id,
                                         request_date, expected_date,
                                         arrival_date, due_date,
                                         return_date, cost, currency,
                                         barcode, library_notes, ln)

def ill_request_details_step3(req, request_info=None, ill_status=None,
                              ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/ill_request_details_step3
    """

    request_info = eval(request_info)

    return bal.ill_request_details_step3(req, request_info, ill_status, ln)


def ordered_books_details_step1(req, purchase_id=None, delete_key=None,
                                ln=CFG_SITE_LANG):
    """
    """

    return bal.ordered_books_details_step1(req, purchase_id, delete_key, ln)

def ordered_books_details_step2(req, purchase_id=None, recid=None,
                                vendor_id=None, cost=None, currency=None,
                                status=None, order_date=None,
                                expected_date=None, purchase_notes=None,
                                library_notes=None,
                                ln=CFG_SITE_LANG):

    """
    """

    return bal.ordered_books_details_step2(req, purchase_id, recid, vendor_id,
                                           cost, currency, status, order_date,
                                           expected_date,
                                           purchase_notes, library_notes, ln)

def ordered_books_details_step3(req, purchase_id=None, recid=None,
                               vendor_id=None, cost=None, currency=None,
                               status=None, order_date=None, expected_date=None,
                               purchase_notes=None, library_notes=None,
                               ln=CFG_SITE_LANG):
    """
    """

    return bal.ordered_books_details_step3(req, purchase_id, recid, vendor_id,
                                           cost, currency, status, order_date,
                                           expected_date, purchase_notes,
                                           library_notes, ln)

def add_new_vendor_step1(req, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/add_new_vendor_step1
    """
    return bal.add_new_vendor_step1(req, ln)

def add_new_vendor_step2(req, name=None, email=None, phone=None, address=None,
                         notes=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/add_new_vendor_step2
    """
    return bal.add_new_vendor_step2(req, name, email, phone, address,
                                    notes, ln)

def add_new_vendor_step3(req, tup_infos=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/add_new_vendor_step3
    """
    tup_infos = eval(tup_infos)

    return bal.add_new_vendor_step3(req, tup_infos, ln)

def update_vendor_info_step1(req, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/update_vendor_info_step1
    """
    return bal.update_vendor_info_step1(req, ln)

def update_vendor_info_step2(req, column=None, string=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/update_vendor_info_step2
    """
    return bal.update_vendor_info_step2(req, column, string, ln)

def update_vendor_info_step3(req, vendor_id=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/update_vendor_info_step3
    """
    return bal.update_vendor_info_step3(req, vendor_id, ln)

def update_vendor_info_step4(req, name=None, email=None, phone=None,
                             address=None, vendor_id=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/update_vendor_info_step4
    """
    return bal.update_vendor_info_step4(req, name, email, phone, address,
                                        vendor_id, ln)

def update_vendor_info_step5(req, tup_infos, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/update_vendor_info_step5
    """
    tup_infos = eval(tup_infos)

    return bal.update_vendor_info_step5(req, tup_infos, ln)

def search_vendor_step1(req, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/search_vendor_step1
    """
    return bal.search_vendor_step1(req, ln)

def search_vendor_step2(req, column, string, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/search_vendor_step2
    """

    return bal.search_vendor_step2(req, column, string, ln)

def get_vendor_details(req, vendor_id=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/get_vendor_details
    """
    return bal.get_vendor_details(req, vendor_id, ln)

def get_vendor_notes(req, vendor_id=None, add_notes=None, new_note=None,
                     ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/get_vendor_notes
    """
    return bal.get_vendor_notes(req, vendor_id, add_notes, new_note, ln)

def register_ill_request_with_no_recid_step1(req, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/register_ill_request_with_no_recid_step1
    """

    return bal.register_ill_request_with_no_recid_step1(req, ln)

def register_ill_request_with_no_recid_step2(req, title=None, authors=None,
                                       place=None, publisher=None, year=None,
                                       edition=None, isbn=None,
                                       period_of_interest_from=None,
                                       period_of_interest_to=None,
                                       additional_comments=None,
                                       only_edition=None, key=None, string=None,
                                       ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/register_ill_request_with_no_recid_step2
    """

    return bal.register_ill_request_with_no_recid_step2(req, title, authors,
                                          place, publisher, year, edition, isbn,
                                          period_of_interest_from,
                                          period_of_interest_to,
                                          additional_comments, only_edition,
                                          key, string, ln)

def register_ill_request_with_no_recid_step3(req, book_info=None,
                                             user_info=None,
                                             request_details=None,
                                             ln=CFG_SITE_LANG):
    """
    """

    if type(book_info) is str:
        book_info = eval(book_info)

    if type(request_details) is str:
        request_details = eval(request_details)

    if type(user_info) is str:
        user_info = user_info.split(',')

    return bal.register_ill_request_with_no_recid_step3(req, book_info,
                                                        user_info,
                                                        request_details, ln)

def register_ill_request_with_no_recid_step4(req, book_info=None,
                                             user_info=None,
                                             request_details=None,
                                             ln=CFG_SITE_LANG):
    """
    """

    if type(book_info) is str:
        book_info = eval(book_info)

    if type(request_details) is str:
        request_details = eval(request_details)

    if type(user_info) is str:
        user_info = eval(user_info)

    return bal.register_ill_request_with_no_recid_step4(req, book_info,
                                                        user_info,
                                                        request_details, ln)

def get_borrower_ill_details(req, borrower_id=None, ill_id=None,
                             ln=CFG_SITE_LANG):
    """
    """

    return bal.get_borrower_ill_details(req, borrower_id, ill_id, ln)

def get_ill_library_notes(req, ill_id=None, delete_key=None, library_notes=None,
                          ln=CFG_SITE_LANG):
    """
    """

    return bal.get_ill_library_notes(req, ill_id, delete_key, library_notes, ln)

def get_expired_loans_with_requests(req, request_id=None, ln=CFG_SITE_LANG):
    """
    """

    return bal.get_expired_loans_with_requests(req, request_id, ln)

def register_ill_book_request(req, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/holdings_search
    """
    return bal.register_ill_book_request(req, ln)

def register_ill_book_request_result(req, p=None, f=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/item_search_result
    """

    return bal.register_ill_book_request_result(req, p, f, ln)

def register_ill_book_request_from_borrower_page(req, borrower_id=None,
                                                 ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/holdings_search
    """
    return bal.register_ill_book_request_from_borrower_page(req, borrower_id,
                                                            ln)

def register_ill_book_request_from_borrower_page_result(req, borrower_id=None,
                                                        p=None, f=None,
                                                        ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/item_search_result
    """

    return bal.register_ill_book_request_from_borrower_page_result(req,
                                                        borrower_id, p, f, ln)

def register_ill_request_from_borrower_page_step1(req, borrower_id=None,
                                                  ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/register_ill_request_with_no_recid_step1
    """

    return bal.register_ill_request_from_borrower_page_step1(req, borrower_id,
                                                             ln)

def register_ill_request_from_borrower_page_step2(req, borrower_id=None,
                                        title=None, authors=None, place=None,
                                        publisher=None, year=None, edition=None,
                                        isbn=None, period_of_interest_from=None,
                                        period_of_interest_to=None,
                                        additional_comments=None,
                                        only_edition=None, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/register_ill_request_with_no_recid_step2
    """

    return bal.register_ill_request_from_borrower_page_step2(req, borrower_id,
                                                title, authors, place,
                                                publisher, year, edition, isbn,
                                                period_of_interest_from,
                                                period_of_interest_to,
                                                additional_comments,
                                                only_edition, ln)

def register_ill_article_request_step1(req, ln=CFG_SITE_LANG):
    """
    """

    return bal.register_ill_article_request_step1(req, ln)

def register_ill_article_request_step2(req, periodical_title=None,
                                       article_title=None, author=None,
                                       report_number=None, volume=None,
                                       issue=None, page=None, year=None,
                                       issn=None, period_of_interest_from=None,
                                       period_of_interest_to=None,
                                       additional_comments=None,
                                       key=None, string=None, ln=CFG_SITE_LANG):

    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/register_ill_request_with_no_recid_step2
    """

    return bal.register_ill_article_request_step2(req, periodical_title,
                                        article_title, author, report_number,
                                        volume, issue, page, year, issn,
                                        period_of_interest_from,
                                        period_of_interest_to,
                                        additional_comments, key, string, ln)

def register_ill_article_request_step3(req, book_info, user_info,
                                       request_details, ln=CFG_SITE_LANG):

    book_info = eval(book_info)

    request_details = eval(request_details)

    user_info = user_info.split(',')

    return bal.register_ill_article_request_step3(req, book_info, user_info,
                                                  request_details, ln)

def ill_search(req, ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/holdings_search
    """
    return bal.ill_search(req, ln)

def ill_search_result(req, p=None, f=None, date_from=None, date_to=None,
                      ln=CFG_SITE_LANG):
    """
    http://cds.cern.ch/admin/bibcirculation/bibcirculationadmin.py/item_search_result
    """

    return bal.ill_search_result(req, p, f, date_from, date_to, ln)
