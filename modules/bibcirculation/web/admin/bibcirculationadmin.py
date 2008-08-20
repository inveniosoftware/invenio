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


def borrower_search_test(req, column=None, string=None,
                         user=None, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/borrowers_search_test

    """
    return bal.borrower_search_test(req, column, string, user, ln)


def holdings_search(req, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/holdings_search

    """
    return bal.holdings_search(req, ln)


def borrower_notification(req, borrower_id=None,
                          template=None, to_borrower=None,
                          message=None, search_button=None,
                          load_button=None, string=None,
                          column=None, subject=None,
                          send_button=None, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/borrower_notification

    """
    return bal.borrower_notification(req, borrower_id, template,
                                     to_borrower, message, search_button,
                                     load_button, string, column, subject,
                                     send_button, ln)


def get_pending_loan_request(req, show=None, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/get_pending_loan_request

    """
    return bal.get_pending_loan_request(req, show, ln)


def item_search_result(req, p=None, f=None, start=None, end=None, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/item_search_result
    """

    return bal.item_search_result(req, p, f, start, end, ln)

def loan_return(req, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/loan_return

    """
    return bal.loan_return(req, ln)

def loan_on_desk(req, column=None, string=None,
                 borrower="", confirm_button=None,
                 barcode="", borrower_name=None, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk

    """

    return bal.loan_on_desk(req, column, string,
                            borrower, confirm_button,
                            barcode, borrower_name, ln)


def loan_on_desk_confirm(req, barcode=None, borrower_id=None, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/loan_on_desk_confirm

    """
    return bal.loan_on_desk_confirm(req, barcode, borrower_id, ln)


def register_new_loan(req, barcode=None, borrower_id=None, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/register_new_loan

    """
    barcode = wash_url_argument(barcode, 'list')

    return bal.register_new_loan(req, barcode, borrower_id, ln)


def loan_return_confirm(req, barcode=None, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/loan_return_confirm

    """
    return bal.loan_return_confirm(req, barcode, ln)


def get_next_waiting_loan_request(req, recID=None, barcode=None,
                                  ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/get_next_waiting_loan_request

    """
    return bal.get_next_waiting_loan_request(req, recID, barcode, ln)


def update_loan_request_status(req, check_id_list=None, approve_button=None,
                               cancel_button=None, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/update_loan_request_status

    """

    check_id_list = wash_url_argument(check_id_list, 'list')

    return bal.update_loan_request_status(req, check_id_list,
                                          approve_button, cancel_button, ln)


def update_next_loan_request_status(req, check_id=None, approve_button=None,
                                    cancel_button=None, barcode=None,
                                    ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/update_next_loan_request_status

    """
    return bal.update_next_loan_request_status(req, check_id,
                                               approve_button,
                                               cancel_button,
                                               barcode, ln)


def all_requests(req, orderby=None, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/all_requests

    """
    return bal.all_requests(req, orderby, ln)


def item_req_historical_overview(req, recid=None, ln=CFG_SITE_LANG):
    """
    """
    return bal.item_req_historical_overview(req, recid, ln)

def item_loans_historical_overview(req, recid=None, ln=CFG_SITE_LANG):
    """
    """
    return bal.item_loans_historical_overview(req, recid, ln)

def all_loans(req, show=None, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/all_loans

    """
    return bal.all_loans(req, show, ln)


def all_requests_for_item(req, recid=None, orderby=None, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/borrowers_search

    """
    return bal.get_all_requests_for_item(req, recid, orderby, ln)


def all_loans_for_item(req, recid=None, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/borrowers_search

    """
    return bal.all_loans_for_item(req, recid, ln)


def get_borrower_details(req, ln=CFG_SITE_LANG, borrower_id=None):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/borrowers_search

    """
    return bal.get_borrower_details(req, ln, borrower_id)

def get_item_details(req, ln=CFG_SITE_LANG, recid=None):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/borrowers_search

    """
    return bal.get_item_details(req, ln, recid)

def get_library_details(req, ln=CFG_SITE_LANG, libid=None):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/borrowers_search

    """
    return bal.get_library_details(req, ln, libid)

def get_borrower_requests_details(req, orderby=None, ln=CFG_SITE_LANG,
                                  notify_button=None, borrower_id=None):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/borrowers_search

    """
    return bal.get_borrower_requests_details(req, orderby, ln,
                                             notify_button, borrower_id)


def get_borrower_loans_details(req, orderby=None, ln=CFG_SITE_LANG,
                               notify_button=None, barcode=None,
                               borrower_id=None):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/borrowers_search

    """
    return bal.get_borrower_loans_details(req, orderby, ln,
                                          notify_button, barcode, borrower_id)


def search_result(req, column, str, ln=CFG_SITE_LANG):
    """
    """
    return bal.search_result(req, column, str, ln)


def help_contactsupport(req, ln=CFG_SITE_LANG):
    """
    http://cdsweb.cern.ch/admin/bibcirculation/bibcirculationadmin.py/borrowers_search

    """
    return bal.help_contactsupport(req, ln)

