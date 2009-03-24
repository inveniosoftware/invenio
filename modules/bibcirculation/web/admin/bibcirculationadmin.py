## $Id: bibcirculationadmin.py,v 1.4 2008/08/20 16:26:39 joaquim Exp $
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

"""CDS Invenio BibCirculation Administrator Interface."""

__revision__ = ""

import sys
import invenio.bibcirculationadminlib as bal
from invenio.config import CFG_SITE_LANG
from invenio.urlutils import wash_url_argument
"""
http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py
"""

def index(req, ln=CFG_SITE_LANG):
    """
    """
    return bal.index(req, ln)

def manage_holdings(req, ln=CFG_SITE_LANG):
    """
    """
    return bal.manage_holdings(req, ln)


def borrower_search(req, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/borrowers_search

    """
    return bal.borrower_search(req, ln)


def item_search(req, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/holdings_search

    """
    return bal.item_search(req, ln)


def borrower_notification(req, borrower_id=None, template=None,
                          message=None, load_msg_template=None, subject=None,
                          send_message=None, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/borrower_notification

    """
    return bal.borrower_notification(req, borrower_id, template,
                                     message, load_msg_template, subject,
                                     send_message, ln)


def get_pending_requests(req, request_id=None, print_data=None, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/get_pending_requests

    """
    return bal.get_pending_requests(req, request_id, print_data, ln)


def item_search_result(req, p=None, f=None, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/item_search_result
    """

    return bal.item_search_result(req, p, f, ln)

def loan_return(req, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/loan_return

    """
    return bal.loan_return(req, ln)

def loan_on_desk_step1(req, key=None, string=None, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk

    """

    return bal.loan_on_desk_step1(req, key, string, ln)


def loan_on_desk_step2(req, user_info=None, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk

    """
    return bal.loan_on_desk_step2(req, user_info, ln)

def loan_on_desk_step3(req, ccid=None, name=None, email=None, phone=None, address=None, mailbox=None, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk

    """
    return bal.loan_on_desk_step3(req, ccid, name, email, phone, address, mailbox, ln)

def loan_on_desk_step4(req, user_info=None, barcode=None, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk

    """

    user_info = eval(user_info)

    return bal.loan_on_desk_step4(req, user_info, barcode, ln)

def loan_on_desk_step5(req, list_of_books=None, user_info=None, due_date=None, note=None, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk

    """

    list_of_books = eval(list_of_books)
    user_info = eval(user_info)
    due_date = wash_url_argument(due_date, 'list')

    return bal.loan_on_desk_step5(req, list_of_books, user_info, due_date, note, ln)


def loan_on_desk_confirm(req, barcode=None, borrower_id=None, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_confirm

    """
    return bal.loan_on_desk_confirm(req, barcode, borrower_id, ln)


def register_new_loan(req, barcode=None, borrower_id=None, request_id=None, new_note=None, print_data=None, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/register_new_loan

    """

    return bal.register_new_loan(req, barcode, borrower_id, request_id, new_note, print_data, ln)


def loan_return_confirm(req, barcode=None, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/loan_return_confirm

    """
    return bal.loan_return_confirm(req, barcode, ln)


def get_next_waiting_loan_request(req, recid=None, barcode=None, check_id=None,
                                  ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/get_next_waiting_loan_request

    """
    return bal.get_next_waiting_loan_request(req, recid, barcode, check_id, ln)


def update_loan_request_status(req, check_id_list=None, barcode=None, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/update_loan_request_status

    """

    check_id_list = wash_url_argument(check_id_list, 'list')

    return bal.update_loan_request_status(req, check_id_list, barcode, ln)


def update_next_loan_request_status(req, check_id=None, barcode=None,
                                    ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/update_next_loan_request_status

    """
    return bal.update_next_loan_request_status(req, check_id,
                                               barcode, ln)


def all_requests(req, request_id=None, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/all_requests

    """

    return bal.all_requests(req, request_id, ln)


def get_item_req_historical_overview(req, recid=None, ln=CFG_SITE_LANG):
    """
    """
    return bal.get_item_req_historical_overview(req, recid, ln)

def get_item_loans_historical_overview(req, recid=None, ln=CFG_SITE_LANG):
    """
    """
    return bal.get_item_loans_historical_overview(req, recid, ln)

def all_loans(req, show=None, loans_per_page=25, jloan=0, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/all_loans

    """
    return bal.all_loans(req, show, loans_per_page, jloan, ln)

def bor_loans_historical_overview(req, borrower_id=None, ln=CFG_SITE_LANG):
    """
    """
    return bal.bor_loans_historical_overview(req, borrower_id, ln)

def bor_requests_historical_overview(req, borrower_id=None, ln=CFG_SITE_LANG):
    """
    """
    return bal.bor_requests_historical_overview(req, borrower_id, ln)


def get_item_requests_details(req, recid=None, request_id=None, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/borrowers_search

    """
    return bal.get_item_requests_details(req, recid, request_id, ln)


def get_item_loans_details(req, recid=None, barcode=None, loan_id=None, force=None, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/borrowers_search

    """
    return bal.get_item_loans_details(req, recid, barcode, loan_id, force, ln)


def get_borrower_details(req, borrower_id=None, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/borrowers_search

    """
    return bal.get_borrower_details(req, borrower_id, ln)

def get_item_details(req, recid=None, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/borrowers_search

    """
    return bal.get_item_details(req, recid, ln)

def get_library_details(req, library_id=None, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/borrowers_search

    """
    return bal.get_library_details(req, library_id, ln)

def get_borrower_requests_details(req, borrower_id=None, id_request=None, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/borrowers_search

    """
    return bal.get_borrower_requests_details(req, borrower_id, id_request, ln)


def get_borrower_loans_details(req, recid=None, barcode=None, borrower_id=None, renewall=None,
                               force=None, loan_id=None, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/borrowers_search

    """

    return bal.get_borrower_loans_details(req, recid, barcode, borrower_id, renewall,
                                          force, loan_id, ln)


def borrower_search_result(req, column, string, ln=CFG_SITE_LANG):
    """
    """
    return bal.borrower_search_result(req, column, string, ln)


def help_contactsupport(req, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/borrowers_search

    """
    return bal.help_contactsupport(req, ln)

def associate_barcode(req, request_id=None, recid=None, borrower_id=None, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/borrowers_search

    """
    return bal.associate_barcode(req, request_id, recid, borrower_id, ln)

def get_borrower_notes(req, borrower_id=None, add_notes=None, new_note=None, ln=CFG_SITE_LANG):
    """
    """
    return bal.get_borrower_notes(req, borrower_id, add_notes, new_note, ln)

def get_loans_notes(req, loan_id=None, recid=None, borrower_id=None, add_notes=None, new_note=None, ln=CFG_SITE_LANG):
    """
    """
    return bal.get_loans_notes(req, loan_id, recid, borrower_id, add_notes, new_note, ln)

def get_item_loans_notes(req, loan_id=None, recid=None, borrower_id=None, add_notes=None, new_note=None, ln=CFG_SITE_LANG):
    """
    """
    return bal.get_item_loans_notes(req, loan_id, recid, borrower_id, add_notes, new_note, ln)


def new_item(req, isbn=None, ln=CFG_SITE_LANG):
    """
    """
    return bal.new_item(req, isbn, ln)

def add_new_borrower_step1(req, ln=CFG_SITE_LANG):
    """
    """
    return bal.add_new_borrower_step1(req, ln)

def add_new_borrower_step2(req, name=None, email=None, phone=None, address=None, mailbox=None, notes=None, ln=CFG_SITE_LANG):
    """
    """
    return bal.add_new_borrower_step2(req, name, email, phone, address, mailbox, notes, ln)

def add_new_borrower_step3(req, tup_infos=None, ln=CFG_SITE_LANG):
    """
    """
    tup_infos = eval(tup_infos)

    return bal.add_new_borrower_step3(req, tup_infos, ln)

def update_borrower_info_step1(req, ln=CFG_SITE_LANG):
    """
    """
    return bal.update_borrower_info_step1(req, ln)

def update_borrower_info_step2(req, column=None, string=None, ln=CFG_SITE_LANG):
    """
    """
    return bal.update_borrower_info_step2(req, column, string, ln)

def update_borrower_info_step3(req, borrower_id=None, ln=CFG_SITE_LANG):
    """
    """
    return bal.update_borrower_info_step3(req, borrower_id, ln)

def update_borrower_info_step4(req, name=None, email=None, phone=None, address=None, mailbox=None,
                               ln=CFG_SITE_LANG):
    """
    """
    return bal.update_borrower_info_step4(req, name, email, phone, address, mailbox, ln)

def update_borrower_info_step5(req, tup_infos, ln=CFG_SITE_LANG):
    """
    """
    tup_infos = eval(tup_infos)

    return bal.update_borrower_info_step5(req, tup_infos, ln)

def add_new_library_step1(req, ln=CFG_SITE_LANG):
    """
    """
    return bal.add_new_library_step1(req, ln)

def add_new_library_step2(req, name=None, email=None, phone=None, address=None, notes=None, ln=CFG_SITE_LANG):
    """
    """
    return bal.add_new_library_step2(req, name, email, phone, address, notes, ln)

def add_new_library_step3(req, tup_infos=None, ln=CFG_SITE_LANG):
    """
    """
    tup_infos = eval(tup_infos)

    return bal.add_new_library_step3(req, tup_infos, ln)

def update_library_info_step1(req, ln=CFG_SITE_LANG):
    """
    """
    return bal.update_library_info_step1(req, ln)

def update_library_info_step2(req, column=None, string=None, ln=CFG_SITE_LANG):
    """
    """
    return bal.update_library_info_step2(req, column, string, ln)

def update_library_info_step3(req, library_id=None, ln=CFG_SITE_LANG):
    """
    """
    return bal.update_library_info_step3(req, library_id, ln)

def update_library_info_step4(req, name=None, email=None, phone=None, address=None,
                              library_id=None, ln=CFG_SITE_LANG):
    """
    """
    return bal.update_library_info_step4(req, name, email, phone, address, library_id, ln)

def update_library_info_step5(req, tup_infos, ln=CFG_SITE_LANG):
    """
    """
    tup_infos = eval(tup_infos)

    return bal.update_library_info_step5(req, tup_infos, ln)

def add_new_copy_step1(req, ln=CFG_SITE_LANG):
    """
    """

    return bal.add_new_copy_step1(req, ln)

def add_new_copy_step2(req, p=None, f=None, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/item_search_result
    """

    return bal.add_new_copy_step2(req, p, f, ln)

def add_new_copy_step3(req, recid=None, ln=CFG_SITE_LANG):
    """
    """
    return bal.add_new_copy_step3(req, recid, ln)

def add_new_copy_step4(req, barcode=None, library=None, location=None, collection=None,
                       description=None, loan_period=None, status=None, recid=None, ln=CFG_SITE_LANG):
    """
    """

    return bal.add_new_copy_step4(req, barcode, library, location, collection, description,
                       loan_period, status, recid, ln)

def add_new_copy_step5(req, tup_infos=None, ln=CFG_SITE_LANG):
    """
    """
    tup_infos = eval(tup_infos)

    return bal.add_new_copy_step5(req, tup_infos, ln)

def update_item_info_step1(req, ln=CFG_SITE_LANG):
    """
    """
    return bal.update_item_info_step1(req, ln)

def update_item_info_step2(req, p, f, ln=CFG_SITE_LANG):
    """
    """
    return bal.update_item_info_step2(req, p, f, ln)

def update_item_info_step3(req, recid, ln=CFG_SITE_LANG):
    """
    """
    return bal.update_item_info_step3(req, recid, ln)

def update_item_info_step4(req, barcode, ln=CFG_SITE_LANG):
    """
    """
    return bal.update_item_info_step4(req, barcode, ln)

def update_item_info_step5(req, barcode, library, location, collection, description,
                           loan_period, status, recid, ln=CFG_SITE_LANG):
    """
    """
    return bal.update_item_info_step5(req, barcode, library, location, collection, description,
                                      loan_period, status, recid, ln)

def update_item_info_step6(req, tup_infos, ln=CFG_SITE_LANG):
    """
    """
    tup_infos = eval(tup_infos)

    return bal.update_item_info_step6(req, tup_infos, ln)

def search_library_step1(req, ln=CFG_SITE_LANG):
    """
    """
    return bal.search_library_step1(req, ln)

def search_library_step2(req, column, string, ln=CFG_SITE_LANG):
    """
    """

    return bal.search_library_step2(req, column, string, ln)

def get_library_notes(req, library_id=None, add_notes=None, new_note=None, ln=CFG_SITE_LANG):
    """
    """
    return bal.get_library_notes(req, library_id, add_notes, new_note, ln)
