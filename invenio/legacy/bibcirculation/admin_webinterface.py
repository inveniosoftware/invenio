# This file is part of Invenio.
# Copyright (C) 2008, 2009, 2010, 2011, 2013 CERN.
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

"""Invenio BibCirculation Administrator (URLs) Interface.
   The functions are positioned by grouping into logical
   categories('User Pages', 'Loans, Returns and Loan requests',
   'ILLs', 'Libraries', 'Vendors' ...)
   These orders should be maintained and when necessary, improved
   for readability, as and when additional methods are added.
   When applicable, methods should be renamed, refactored and
   appropriate documentation added.
"""

__revision__ = ""

from invenio.utils.url import redirect_to_url
from invenio.config import CFG_SITE_URL, CFG_BIBCIRCULATION_ITEM_STATUS_ON_SHELF
from invenio.ext.legacy.handler import wash_urlargd, WebInterfaceDirectory

import invenio.legacy.bibcirculation.adminlib as bal

class WebInterfaceBibCirculationAdminPages(WebInterfaceDirectory):
    """Defines the set of /admin2/bibcirculation pages."""

    _exports = ['', 'index',

                # Loans, Loan Requests, Loan Returns related pages
                'loan_on_desk_step1', 'loan_on_desk_step2', 'loan_on_desk_step3',
                'loan_on_desk_step4', 'loan_on_desk_confirm', 'register_new_loan',
                'create_loan', 'make_new_loan_from_request', 'loan_return',
                'loan_return_confirm', 'claim_book_return',
                'change_due_date_step1', 'change_due_date_step2',
                'place_new_request_step1', 'place_new_request_step2',
                'place_new_request_step3', 'place_new_loan_step1',
                'place_new_loan_step2', 'place_new_loan_step3',
                'create_new_request_step1', 'create_new_request_step2',
                'create_new_request_step3', 'create_new_request_step4',
                'create_new_loan_step1', 'create_new_loan_step2',
                'all_requests', 'all_loans', 'all_expired_loans',
                'get_pending_requests', 'get_waiting_requests',
                'get_expired_loans_with_waiting_requests',
                'get_loans_notes', 'get_item_loans_notes',

                # "Item" related pages
                'get_item_details', 'get_item_requests_details', 'get_item_loans_details',
                'get_item_req_historical_overview', 'get_item_loans_historical_overview',
                'add_new_copy_step1', 'add_new_copy_step2', 'add_new_copy_step3',
                'add_new_copy_step4', 'add_new_copy_step5',
                'delete_copy_step1', 'delete_copy_step2',
                'update_item_info_step1', 'update_item_info_step2', 'update_item_info_step3',
                'update_item_info_step4', 'update_item_info_step5', 'update_item_info_step6',
                'item_search', 'item_search_result',

                # "Borrower" related pages
                'get_borrower_details', 'add_new_borrower_step1',
                'add_new_borrower_step2', 'add_new_borrower_step3',
                'update_borrower_info_step1', 'update_borrower_info_step2',
                'get_borrower_requests_details', 'get_borrower_loans_details',
                'bor_loans_historical_overview', 'bor_requests_historical_overview',
                'get_borrower_ill_details', 'bor_ill_historical_overview',
                'borrower_notification', 'get_borrower_notes',
                'borrower_search', 'borrower_search_result',

                # ILL/Purchase/Acquisition related pages
                'register_ill_from_proposal', 'register_ill_request_with_no_recid_step1',
                'register_ill_request_with_no_recid_step2', 'register_ill_request_with_no_recid_step3',
                'register_ill_request_with_no_recid_step4',
                'register_ill_book_request', 'register_ill_book_request_result',
                'register_ill_article_request_step1', 'register_ill_article_request_step2',
                'register_ill_article_request_step3',
                'register_purchase_request_step1', 'register_purchase_request_step2',
                'register_purchase_request_step3',
                'ill_request_details_step1', 'ill_request_details_step2',
                'purchase_details_step1', 'purchase_details_step2', 'get_ill_library_notes',
                'list_ill_request', 'list_purchase', 'list_proposal',
                'ill_search', 'ill_search_result',

                # "Library" related pages
                'get_library_details', 'merge_libraries_step1', 'merge_libraries_step2',
                'merge_libraries_step3', 'add_new_library_step1', 'add_new_library_step2',
                'add_new_library_step3', 'update_library_info_step1', 'update_library_info_step2',
                'update_library_info_step3', 'update_library_info_step4', 'update_library_info_step5',
                'get_library_notes', 'search_library_step1', 'search_library_step2',

                # "Vendor related pages
                'get_vendor_details', 'add_new_vendor_step1', 'add_new_vendor_step2',
                'add_new_vendor_step3', 'update_vendor_info_step1', 'update_vendor_info_step2',
                'update_vendor_info_step3', 'update_vendor_info_step4', 'update_vendor_info_step5',
                'get_vendor_notes', 'search_vendor_step1', 'search_vendor_step2'
                ]



    def index(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation"""
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']
        return bal.index(req, ln)



# Loans, Loan Requests, Loan Returns related pages



    def loan_on_desk_step1(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/loan_on_desk_step1"""
        argd = wash_urlargd(form, {'key': (str, None), 'string': (str, None), 'ln': (str, "en")})
        key = argd['key']
        string = argd['string']
        ln = argd['ln']

        if string is not None:
            string = string.strip()

        return bal.loan_on_desk_step1(req, key, string, ln)

    def loan_on_desk_step2(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/loan_on_desk_step2"""
        argd = wash_urlargd(form, {'user_id': (int, None), 'ln': (str, "en")})
        user_id = argd['user_id']
        ln = argd['ln']

        return bal.loan_on_desk_step2(req, user_id, ln)

    def loan_on_desk_step3(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/loan_on_desk_step4"""
        argd = wash_urlargd(form, {'user_id': (int, None), 'barcode': (str, None),
                                    'ln': (str, "en")})
        user_id = argd['user_id']
        list_of_barcodes = argd['barcode']
        ln = argd['ln']

        if list_of_barcodes is not None:
            list_of_barcodes = list_of_barcodes.split()
        else:
            list_of_barcodes = []

        return bal.loan_on_desk_step3(req, user_id, list_of_barcodes, ln)

    def loan_on_desk_step4(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/loan_on_desk_step5"""
        argd = wash_urlargd(form, {'list_of_barcodes': (str, None), 'user_id': (int, None),
                        'datepickerhidden': (str, None), 'note': (str, None), 'ln': (str, "en")})
        list_of_barcodes = argd['list_of_barcodes']
        user_id = argd['user_id']
        due_date = argd['datepickerhidden']
        note = argd['note']
        ln = argd['ln']

        list_of_barcodes = list_of_barcodes.strip('[]')
        list_of_barcodes = list_of_barcodes.split(',')

        for i in range(len(list_of_barcodes)):
            list_of_barcodes[i] = list_of_barcodes[i].strip('\' ')

        due_date = due_date.split(',')


        return bal.loan_on_desk_step4(req, list_of_barcodes, user_id, due_date, note, ln)

    def loan_on_desk_confirm(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/loan_on_desk_confirm"""
        argd = wash_urlargd(form, {'barcode': (str, None), 'borrower_id': (str, None),
                                    'ln': (str, "en")})
        barcode = argd['barcode']
        borrower_id = argd['borrower_id']
        ln = argd['ln']
        return bal.loan_on_desk_confirm(req, barcode, borrower_id, ln)

    def register_new_loan(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/register_new_loan"""
        argd = wash_urlargd(form, {'barcode': (str, None), 'borrower_id': (str, None),
                                   'request_id': (str, None), 'new_note': (str, None),
                                   'print_data': (str, None), 'ln': (str, "en")})
        barcode     = argd['barcode']
        borrower_id = argd['borrower_id']
        request_id  = argd['request_id']
        new_note    = argd['new_note']
        print_data  = argd['print_data']
        ln          = argd['ln']

        if barcode is not None:
            barcode = barcode.strip()

        return bal.register_new_loan(req, barcode, borrower_id, request_id,
                                     new_note, print_data, ln)

    def create_loan(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/create_loan"""
        argd = wash_urlargd(form, {'request_id': (str, None), 'recid': (str, None),
                                    'borrower_id': (str, None), 'ln': (str, "en")})
        request_id = argd['request_id']
        recid = argd['recid']
        borrower_id = argd['borrower_id']
        ln = argd['ln']
        return bal.create_loan(req, request_id, recid, borrower_id, ln)

    def make_new_loan_from_request(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/make_new_loan_from_request"""
        argd = wash_urlargd(form, {'check_id': (str, None), 'barcode': (str, None),
                                    'ln': (str, "en")})
        check_id = argd['check_id']
        barcode  = argd['barcode']
        ln       = argd['ln']

        return bal.make_new_loan_from_request(req, check_id, barcode, ln)

    def loan_return(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/loan_return"""
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']
        return bal.loan_return(req, ln)

    def loan_return_confirm(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/loan_return_confirm"""
        argd = wash_urlargd(form, {'barcode': (str, None), 'ln': (str, "en")})
        barcode = argd['barcode']
        ln = argd['ln']
        if barcode is not None:
            barcode = barcode.strip()

        return bal.loan_return_confirm(req, barcode, ln)

    def claim_book_return(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/claim_book_return"""
        argd = wash_urlargd(form, {'borrower_id': (str, None), 'recid': (str, None),
                            'loan_id': (str, None), 'template': (str, None), 'ln': (str, "en")})
        borrower_id = argd['borrower_id']
        recid = argd['recid']
        loan_id = argd['loan_id']
        template = argd['template']
        ln = argd['ln']
        return bal.claim_book_return(req, borrower_id, recid, loan_id, template, ln)


    def change_due_date_step1(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/change_due_date_step1"""
        argd = wash_urlargd(form, {'barcode': (str, None), 'borrower_id': (str, None),
                                    'ln': (str, "en")})
        barcode = argd['barcode']
        borrower_id = argd['borrower_id']
        ln = argd['ln']
        return bal.change_due_date_step1(req, barcode, borrower_id, ln)

    def change_due_date_step2(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/change_due_date_step2"""
        argd = wash_urlargd(form, {'new_due_date': (str, None), 'loan_id': (str, None),
                                    'borrower_id': (str, None), 'ln': (str, "en")})
        new_due_date = argd['new_due_date']
        loan_id = argd['loan_id']
        borrower_id = argd['borrower_id']
        ln = argd['ln']
        return bal.change_due_date_step2(req, new_due_date, loan_id, borrower_id, ln)


    def place_new_request_step1(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/place_new_request_step1"""
        argd = wash_urlargd(form, {'barcode': (str, None), 'recid': (str, None),
                            'key': (str, None), 'string': (str, None), 'ln': (str, "en")})
        barcode = argd['barcode']
        recid = argd['recid']
        key = argd['key']
        string = argd['string']
        ln = argd['ln']

        if barcode is not None:
            barcode = barcode.strip()
        if recid is not None:
            recid = recid.strip()
        if string is not None:
            string = string.strip()

        return bal.place_new_request_step1(req, barcode, recid, key, string, ln)

    def place_new_request_step2(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/place_new_request_step2"""
        argd = wash_urlargd(form, {'barcode': (str, None), 'recid': (str, None),
                                    'user_info': (str, None), 'ln': (str, "en")})
        barcode = argd['barcode']
        recid = argd['recid']
        user_info = argd['user_info']
        ln = argd['ln']

        if user_info is not None:
            user_info = user_info.split(',')

        return bal.place_new_request_step2(req, barcode, recid, user_info, ln)

    def place_new_request_step3(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/place_new_request_step3"""
        argd = wash_urlargd(form, {'barcode': (str, None), 'recid': (str, None),
                    'user_info': (str, None), 'period_from': (str, None),
                    'period_to': (str, None), 'ln': (str, "en")})
        barcode = argd['barcode']
        recid = argd['recid']
        user_info = argd['user_info']
        period_from = argd['period_from']
        period_to = argd['period_to']
        ln = argd['ln']

        if user_info is not None:
            user_info = user_info.split(',')

        return bal.place_new_request_step3(req, barcode, recid, user_info, period_from,
                                           period_to, ln)


    def place_new_loan_step1(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/place_new_loan_step1"""
        argd = wash_urlargd(form, {'barcode': (str, None), 'recid': (str, None),
                            'key': (str, None), 'string': (str, None), 'ln': (str, "en")})
        barcode = argd['barcode']
        recid = argd['recid']
        key = argd['key']
        string = argd['string']
        ln = argd['ln']

        if barcode is not None:
            barcode = barcode.strip()
        if recid is not None:
            recid = recid.strip()
        if string is not None:
            string = string.strip()

        return bal.place_new_loan_step1(req, barcode, recid, key, string, ln)

    def place_new_loan_step2(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/place_new_loan_step2"""
        argd = wash_urlargd(form, {'barcode': (str, None), 'recid': (str, None),
                                    'user_info': (str, None), 'ln': (str, "en")})
        barcode = argd['barcode']
        recid = argd['recid']
        user_info = argd['user_info']
        ln = argd['ln']
        return bal.place_new_loan_step2(req, barcode, recid, user_info, ln)

    def place_new_loan_step3(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/place_new_loan_step3"""
        argd = wash_urlargd(form, {'barcode': (str, None), 'recid': (str, None),
            'ccid': (str, None), 'name': (str, None), 'email': (str, None),
            'phone': (str, None), 'address': (str, None), 'mailbox': (str, None),
            'due_date': (str, None), 'notes': (str, None), 'ln': (str, "en")})
        barcode = argd['barcode']
        recid = argd['recid']
        ccid = argd['ccid']
        name = argd['name']
        email = argd['email']
        phone = argd['phone']
        address = argd['address']
        mailbox = argd['mailbox']
        due_date = argd['due_date']
        notes = argd['notes']
        ln = argd['ln']
        return bal.place_new_loan_step3(req, barcode, recid, ccid, name, email,
                                        phone, address, mailbox, due_date, notes,
                                        ln)


    def create_new_request_step1(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/create_new_request_step1"""
        argd = wash_urlargd(form, {'borrower_id': (str, None), 'p': (str, None),
                            'f': (str, None), 'search': (str, None), 'ln': (str, "en")})

        borrower_id = argd['borrower_id']
        p = argd['p']
        f = argd['f']
        search = argd['search']
        ln = argd['ln']

        if borrower_id is not None:
            borrower_id = borrower_id.strip()
        if p is not None:
            p = p.strip()

        return bal.create_new_request_step1(req, borrower_id, p, f, search, ln)

    def create_new_request_step2(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/create_new_request_step2"""
        argd = wash_urlargd(form, {'recid': (str, None), 'borrower_id': (str, None),
                            'ln': (str, "en")})
        recid = argd['recid']
        borrower_id = argd['borrower_id']
        ln = argd['ln']
        return bal.create_new_request_step2(req, recid, borrower_id, ln)

    def create_new_request_step3(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/create_new_request_step3"""
        argd = wash_urlargd(form, {'borrower_id': (str, None), 'barcode': (str, None),
                                    'recid': (str, None), 'ln': (str, "en")})
        borrower_id = argd['borrower_id']
        barcode = argd['barcode']
        recid = argd['recid']
        ln = argd['ln']
        return bal.create_new_request_step3(req, borrower_id, barcode, recid, ln)

    def create_new_request_step4(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/create_new_request_step4"""
        argd = wash_urlargd(form, {'period_from': (str, None), 'period_to': (str, None),
                    'barcode': (str, None), 'borrower_id': (str, None), 'recid': (str, None),
                    'ln': (str, "en")})
        period_from = argd['period_from']
        period_to = argd['period_to']
        barcode = argd['barcode']
        borrower_id = argd['borrower_id']
        recid = argd['recid']
        ln = argd['ln']
        return bal.create_new_request_step4(req, period_from, period_to, barcode,
                                            borrower_id, recid, ln)


    def create_new_loan_step1(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/create_new_loan_step1"""
        argd = wash_urlargd(form, {'borrower_id': (str, None), 'ln': (str, "en")})
        borrower_id = argd['borrower_id']
        ln = argd['ln']
        return bal.create_new_loan_step1(req, borrower_id, ln)

    def create_new_loan_step2(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/create_new_loan_step2"""
        argd = wash_urlargd(form, {'borrower_id': (str, None), 'barcode': (str, None),
                                    'notes': (str, None), 'ln': (str, "en")})
        borrower_id = argd['borrower_id']
        barcode = argd['barcode']
        notes = argd['notes']
        ln = argd['ln']
        return bal.create_new_loan_step2(req, borrower_id, barcode, notes, ln)


    def all_requests(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/all_requests"""
        argd = wash_urlargd(form, {'request_id': (str, None), 'ln': (str, "en")})
        request_id = argd['request_id']
        ln = argd['ln']
        return bal.all_requests(req, request_id, ln)

    def all_loans(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/all_loans"""
        argd = wash_urlargd(form, {'msg': (str, None), 'ln': (str, "en")})
        msg = argd['msg']
        ln = argd['ln']

        return bal.all_loans(req, msg=msg, ln=ln)

    def all_expired_loans(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/all_expired_loans"""
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']

        return bal.all_expired_loans(req, ln)

    def get_pending_requests(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/get_pending_requests"""
        argd = wash_urlargd(form, {'request_id': (str, None), 'print_data': (str, None),
                                   'ln': (str, "en")})
        request_id = argd['request_id']
        print_data = argd['print_data']
        ln = argd['ln']
        return bal.get_pending_requests(req, request_id, print_data, ln)

    def get_waiting_requests(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/get_waiting_requests"""
        argd = wash_urlargd(form, {'request_id': (str, None), 'print_data': (str, None),
                                    'ln': (str, "en")})
        request_id = argd['request_id']
        print_data = argd['print_data']
        ln = argd['ln']
        return bal.get_waiting_requests(req, request_id, print_data, ln)

    def get_expired_loans_with_waiting_requests(self, req, form):
        """    """
        argd = wash_urlargd(form, {'request_id': (str, None), 'ln': (str, "en")})
        request_id = argd['request_id']
        ln = argd['ln']

        return bal.get_expired_loans_with_waiting_requests(req, request_id, ln)


    def get_loans_notes(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/get_loans_notes"""
        argd = wash_urlargd(form, {'loan_id': (str, None), 'recid': (str, None),
                                    'delete_key': (str, None), 'library_notes': (str, None),
                                    'back': (str, ""), 'ln': (str, "en")})
        loan_id = argd['loan_id']
        delete_key = argd['delete_key']
        library_notes = argd['library_notes']
        back = argd['back']
        ln = argd['ln']
        return bal.get_loans_notes(req, loan_id, delete_key,
                                   library_notes, back, ln)

    def get_item_loans_notes(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/get_item_loans_notes"""
        argd = wash_urlargd(form, {'loan_id': (str, None), 'add_notes': (str, None),
                                    'new_note': (str, None), 'ln': (str, "en")})
        loan_id = argd['loan_id']
        add_notes = argd['add_notes']
        new_note = argd['new_note']
        ln = argd['ln']
        return bal.get_item_loans_notes(req, loan_id, add_notes,
                                        new_note, ln)



# "Item" related pages




    def get_item_details(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/"""
        argd = wash_urlargd(form, {'recid': (str, None), 'ln': (str, "en")})
        recid = argd['recid']
        ln = argd['ln']

        try:
            recid = int(recid)
        except:
            recid = None

        return bal.get_item_details(req, recid, ln)

    def get_item_requests_details(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/borrowers_search"""
        argd = wash_urlargd(form, {'recid': (str, None), 'request_id': (str, None),
                                    'ln': (str, "en")})
        recid = argd['recid']
        request_id = argd['request_id']
        ln = argd['ln']
        return bal.get_item_requests_details(req, recid, request_id, ln)

    def get_item_loans_details(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/borrowers_search"""
        argd = wash_urlargd(form, {'recid': (str, None), 'barcode': (str, None),
                            'loan_id': (str, None), 'force': (str, None), 'ln': (str, "en")})
        recid = argd['recid']
        barcode = argd['barcode']
        loan_id = argd['loan_id']
        force = argd['force']
        ln = argd['ln']
        return bal.get_item_loans_details(req, recid, barcode, loan_id, force, ln)

    def get_item_req_historical_overview(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/get_item_req_historical_overview"""
        argd = wash_urlargd(form, {'recid': (str, None), 'ln': (str, "en")})
        recid = argd['recid']
        ln = argd['ln']
        return bal.get_item_req_historical_overview(req, recid, ln)

    def get_item_loans_historical_overview(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/get_item_loans_historical_overview"""
        argd = wash_urlargd(form, {'recid': (str, None), 'ln': (str, "en")})
        recid = argd['recid']
        ln = argd['ln']
        return bal.get_item_loans_historical_overview(req, recid, ln)


    def add_new_copy_step1(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/add_new_copy_step1"""
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']
        return bal.add_new_copy_step1(req, ln)

    def add_new_copy_step2(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/add_new_copy_step2"""
        argd = wash_urlargd(form, {'p': (str, None), 'f': (str, None), 'ln': (str, "en")})
        p  = argd['p']
        f  = argd['f']
        ln = argd['ln']

        if p is not None:
            p = p.strip()

        return bal.add_new_copy_step2(req, p, f, ln)

    def add_new_copy_step3(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/add_new_copy_step3"""
        argd = wash_urlargd(form, {'recid': (str, None), 'barcode': (str, None),
                                   'ln': (str, "en")})
        recid   = argd['recid']
        barcode = argd['barcode']
        ln      = argd['ln']
        return bal.add_new_copy_step3(req, recid, barcode, ln)

    def add_new_copy_step4(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/add_new_copy_step4"""
        argd = wash_urlargd(form, {'barcode': (str, None), 'library': (str, ''),
            'location': (str, ''), 'collection': (str, ''), 'description': (str, '-'),
            'loan_period': (str, ''), 'status': (str, ''),
            'expected_arrival_date': (str, ''), 'recid': (str, None), 'ln': (str, "en")})

        barcode     = argd['barcode']
        library     = argd['library']
        location    = argd['location']
        collection  = argd['collection']
        description = argd['description']
        loan_period = argd['loan_period']
        status      = argd['status']
        expected_arrival_date = argd['expected_arrival_date']
        recid       = argd['recid']
        ln          = argd['ln']

        if barcode is not None:
            barcode = barcode.strip()

        library     = library.strip()
        location    = location.strip()
        collection  = collection.strip()
        description = description.strip()

        loan_period = loan_period.strip()
        status      = status.strip()
        expected_arrival_date = expected_arrival_date.strip()

        if recid is not None:
            recid = recid.strip()

        return bal.add_new_copy_step4(req, barcode, library, location, collection,
                                      description, loan_period, status,
                                      expected_arrival_date, recid, ln)

    def add_new_copy_step5(self, req, form):

        argd = wash_urlargd(form, {'barcode': (str, None), 'library': (str, None),
            'location': (str, None), 'collection': (str, None), 'description': (str, '-'),
            'loan_period': (str, None), 'status': (str, None),
            'expected_arrival_date': (str, None), 'recid': (str, None), 'ln': (str, "en")})

        barcode = argd['barcode']
        library = argd['library']
        location = argd['location']
        collection = argd['collection']
        description = argd['description']
        loan_period = argd['loan_period']
        status = argd['status']
        expected_arrival_date = argd['expected_arrival_date']
        recid = argd['recid']
        ln = argd['ln']
        return bal.add_new_copy_step5(req, barcode, library, location, collection,
                            description, loan_period, status, expected_arrival_date, recid, ln)


    def delete_copy_step1(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/delete_copy_step1"""
        argd = wash_urlargd(form, {'barcode': (str, ''), 'ln': (str, "en")})

        barcode = argd['barcode']
        ln = argd['ln']

        return bal.delete_copy_step1(req, barcode, ln)

    def delete_copy_step2(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/delete_copy_step2"""
        argd = wash_urlargd(form, {'barcode': (str, ''), 'ln': (str, "en")})

        barcode = argd['barcode']
        ln = argd['ln']

        return bal.delete_copy_step2(req, barcode, ln)


    def update_item_info_step1(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/update_item_info_step1"""
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']
        return bal.update_item_info_step1(req, ln)

    def update_item_info_step2(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/update_item_info_step2"""
        argd = wash_urlargd(form, {'p': (str, '()'), 'f': (str, '()'), 'ln': (str, "en")})
        p = argd['p']
        f = argd['f']
        ln = argd['ln']

        p = p.strip()

        return bal.update_item_info_step2(req, p, f, ln)

    def update_item_info_step3(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/update_item_info_step3"""
        argd = wash_urlargd(form, {'recid': (int, 0), 'ln': (str, "en")})
        recid = argd['recid']
        ln = argd['ln']
        return bal.update_item_info_step3(req, recid, ln)

    def update_item_info_step4(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/update_item_info_step4"""
        argd = wash_urlargd(form, {'barcode': (str, '()'), 'ln': (str, "en")})
        barcode = argd['barcode']
        ln = argd['ln']
        return bal.update_item_info_step4(req, barcode, ln)

    def update_item_info_step5(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/update_item_info_step5"""
        argd = wash_urlargd(form, {'barcode': (str, ''), 'old_barcode': (str, ''),
            'library_id': (int, 0), 'location': (str, 'Unknown'), 'collection': (str, 'Unknown'),
            'description': (str, '-'), 'loan_period': (str, '4 weeks'),
            'status': (str, CFG_BIBCIRCULATION_ITEM_STATUS_ON_SHELF), 'expected_arrival_date': (str, ''),
            'recid': (int, 0), 'ln': (str, "en")})

        barcode = argd['barcode']
        old_barcode = argd['old_barcode']
        library = argd['library_id']
        location = argd['location']
        collection = argd['collection']
        description = argd['description']
        loan_period = argd['loan_period']
        status = argd['status']
        expected_arrival_date = argd['expected_arrival_date']
        recid = argd['recid']
        ln = argd['ln']

        barcode = barcode.strip()
        old_barcode = old_barcode.strip()
        location = location.strip()
        collection = collection.strip()
        description = description.strip()
        loan_period = loan_period.strip()
        status = status.strip()
        expected_arrival_date = expected_arrival_date.strip()

        return bal.update_item_info_step5(req, barcode, old_barcode, library, location,
                                          collection, description, loan_period,
                                          status, expected_arrival_date, recid, ln)

    def update_item_info_step6(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/update_item_info_step6"""
        argd = wash_urlargd(form, {'barcode': (str, '-'), 'old_barcode': (str, '-'),
            'library_id': (int, 0), 'location': (str, 'Unknown'), 'collection': (str, 'Unknown'),
            'description': (str, '-'), 'loan_period': (str, '4 weeks'),
            'status': (str, CFG_BIBCIRCULATION_ITEM_STATUS_ON_SHELF), 'expected_arrival_date': (str, ''),
            'recid': (int, 0), 'ln': (str, "en")})

        barcode = argd['barcode']
        old_barcode = argd['old_barcode']
        library_id = argd['library_id']
        location = argd['location']
        collection = argd['collection']
        description = argd['description']
        loan_period = argd['loan_period']
        status = argd['status']
        expected_arrival_date = argd['expected_arrival_date']
        recid = argd['recid']

        ln = argd['ln']

        tup_infos = (barcode, old_barcode, library_id, location, collection,
                    description, loan_period, status, expected_arrival_date, recid)

        return bal.update_item_info_step6(req, tup_infos, ln)


    def item_search(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/holdings_search"""
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']
        return bal.item_search(req, [], ln)

    def item_search_result(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/item_search_result"""
        argd = wash_urlargd(form, {'p': (str, ''), 'f': (str, ''),
                                   'ln': (str, "en")})
        p  = argd['p']
        f  = argd['f']
        ln = argd['ln']

        if p is not None:
            p = p.strip()

        return bal.item_search_result(req, p, f, ln)




# "Borrower" related pages




    def get_borrower_details(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/borrowers_search"""
        argd = wash_urlargd(form, {'borrower_id': (str, None), 'update': (str, 'False'),
                                   'ln': (str, "en")})
        borrower_id = argd['borrower_id']
        update = argd['update']
        ln = argd['ln']

        if update == 'True':
            update = True
        else:
            update = False

        return bal.get_borrower_details(req, borrower_id, update, ln)

    def add_new_borrower_step1(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/add_new_borrower_step1"""
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']
        return bal.add_new_borrower_step1(req, ln)

    def add_new_borrower_step2(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/add_new_borrower_step2"""
        argd = wash_urlargd(form, {'name': (str, ''), 'email': (str, ''),
            'phone': (str, ''), 'address': (str, ''), 'mailbox': (str, ''),
            'notes': (str, ''), 'ln': (str, "en")})
        name = argd['name']
        email = argd['email']
        phone = argd['phone']
        address = argd['address']
        mailbox = argd['mailbox']
        notes = argd['notes']
        ln = argd['ln']

        name = name.strip()
        email = email.strip()
        phone = phone.strip()
        address = address.strip()
        mailbox = mailbox.strip()
        notes = notes.strip()

        return bal.add_new_borrower_step2(req, name, email, phone, address,
                                          mailbox, notes, ln)

    def update_borrower_info_step1(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/update_borrower_info_step1"""
        argd = wash_urlargd(form, {'borrower_id': (str, None), 'ln': (str, "en")})
        borrower_id = argd['borrower_id']
        ln = argd['ln']
        return bal.update_borrower_info_step1(req, borrower_id, ln)

    def update_borrower_info_step2(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/update_borrower_info_step2"""
        argd = wash_urlargd(form, {'borrower_id': (int, None), 'name': (str, ''),
            'email': (str, ''), 'phone': (str, ''), 'address': (str, ''),
            'mailbox': (str, ''), 'ln': (str, "en")})

        name = argd['name']
        email = argd['email']
        phone = argd['phone']
        address = argd['address']
        mailbox = argd['mailbox']
        borrower_id = argd['borrower_id']
        ln = argd['ln']

        name = name.strip()
        email = email.strip()
        phone = phone.strip()
        address = address.strip()
        mailbox = mailbox.strip()

        return bal.update_borrower_info_step2(req, borrower_id, name, email, phone, address,
                                              mailbox, ln)


    def get_borrower_requests_details(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/get_borrower_requests_details"""
        argd = wash_urlargd(form, {'borrower_id': (str, None), 'request_id': (str, None),
                                    'ln': (str, "en")})
        borrower_id = argd['borrower_id']
        request_id = argd['request_id']
        ln = argd['ln']
        return bal.get_borrower_requests_details(req, borrower_id, request_id, ln)

    def get_borrower_loans_details(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/get_borrower_loans_details"""
        argd = wash_urlargd(form, {'recid': (str, None), 'barcode': (str, None),
                                    'borrower_id': (str, None), 'renewal': (str, None),
                                    'force': (str, None), 'loan_id': (str, None),
                                    'ln': (str, "en")})
        recid = argd['recid']
        barcode = argd['barcode']
        borrower_id = argd['borrower_id']
        renewal = argd['renewal']
        force = argd['force']
        loan_id = argd['loan_id']
        ln = argd['ln']
        return bal.get_borrower_loans_details(req, recid, barcode, borrower_id,
                                              renewal, force, loan_id, ln)

    def bor_loans_historical_overview(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/bor_loans_historical_overview"""
        argd = wash_urlargd(form, {'borrower_id': (str, None), 'ln': (str, "en")})
        borrower_id = argd['borrower_id']
        ln = argd['ln']
        return bal.bor_loans_historical_overview(req, borrower_id, ln)

    def bor_requests_historical_overview(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/bor_requests_historical_overview"""
        argd = wash_urlargd(form, {'borrower_id': (str, None), 'ln': (str, "en")})
        borrower_id = argd['borrower_id']
        ln = argd['ln']
        return bal.bor_requests_historical_overview(req, borrower_id, ln)

    def get_borrower_ill_details(self, req, form):
        """    """
        argd = wash_urlargd(form, {'borrower_id': (str, None),
                                   'request_type': (str, ''), 'ln': (str, "en")})
        borrower_id = argd['borrower_id']
        request_type = argd['request_type']
        ln = argd['ln']

        return bal.get_borrower_ill_details(req, borrower_id, request_type, ln)

    def bor_ill_historical_overview(self, req, form):
        """    """
        argd = wash_urlargd(form, {'borrower_id': (str, None),
                                   'request_type': (str, ''), 'ln': (str, "en")})
        borrower_id = argd['borrower_id']
        request_type = argd['request_type']
        ln = argd['ln']

        return bal.bor_ill_historical_overview(req, borrower_id, request_type, ln)


    def borrower_notification(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/borrower_notification"""
        argd = wash_urlargd(form, {'borrower_id': (str, None), 'template': (str, None),
            'message': (str, None), 'load_msg_template': (str, 'True'), 'subject': (str, None),
            'send_message': (str, None), 'from_address': (str, None), 'ln': (str, "en")})

        borrower_id = argd['borrower_id']
        template = argd['template']
        message = argd['message']
        load_msg_template = argd['load_msg_template']
        subject = argd['subject']
        send_message = argd['send_message']
        from_address = argd['from_address']
        ln = argd['ln']

        return bal.borrower_notification(req, borrower_id, template, message,
                                         load_msg_template, subject, send_message, 
                                         from_address, ln)

    def get_borrower_notes(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/get_borrower_notes"""
        argd = wash_urlargd(form, {'borrower_id': (str, None), 'delete_key': (str, None),
                                    'library_notes': (str, None), 'ln': (str, "en")})
        borrower_id = argd['borrower_id']
        delete_key = argd['delete_key']
        library_notes = argd['library_notes']
        ln = argd['ln']
        return bal.get_borrower_notes(req, borrower_id, delete_key,
                                      library_notes, ln)

    def borrower_search(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/borrowers_search"""
        argd = wash_urlargd(form, {'empty_barcode': (str, None),
                                   'redirect_to_new_request': (str, "no"),
                                    'ln': (str, "en")})
        empty_barcode = argd['empty_barcode']
        redirect_to_new_request = argd['redirect_to_new_request']
        ln = argd['ln']

        if redirect_to_new_request == 'yes':
            redirect_to_new_request = True
        else:
            redirect_to_new_request = False

        return bal.borrower_search(req, empty_barcode,
                                   redirect_to_new_request=redirect_to_new_request, ln=ln)

    def borrower_search_result(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/borrower_search_result"""
        argd = wash_urlargd(form, {'column': (str, "name"), 'string': (str, ''),
                                   'redirect_to_new_request': (str, "no"), 'ln': (str, "en")})
        column = argd['column']
        string = argd['string']
        redirect_to_new_request = argd['redirect_to_new_request']
        ln = argd['ln']

        string = string.strip()
        if redirect_to_new_request == 'yes':
            redirect_to_new_request = True
        else:
            redirect_to_new_request = False

        return bal.borrower_search_result(req, column, string,
                                redirect_to_new_request=redirect_to_new_request,
                                ln=ln)




# ILL/Purchase/Acquisition related pages


    def register_ill_from_proposal(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/register_ill_from_proposal"""
        argd = wash_urlargd(form, {'ill_request_id': (str, None), 'bor_id': (str, None), 'ln': (str, "en")})
        ill_request_id = argd['ill_request_id']
        ln = argd['ln']
        bor_id = argd['bor_id']

        return bal.register_ill_from_proposal(req, ill_request_id, bor_id, ln)

    def register_ill_request_with_no_recid_step1(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/register_ill_request_with_no_recid_step1"""
        argd = wash_urlargd(form, {'ln': (str, "en"), 'borrower_id': (str, None)})
        ln = argd['ln']
        borrower_id = argd['borrower_id']
        if borrower_id == 'None':
            borrower_id = None

        return bal.register_ill_request_with_no_recid_step1(req, borrower_id, ln)

    def register_ill_request_with_no_recid_step2(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/register_ill_request_with_no_recid_step2"""

        argd = wash_urlargd(form, {'title': (str, ''), 'authors': (str, ''),
            'place': (str, ''), 'publisher': (str, ''), 'year': (str, ''),
            'edition': (str, ''), 'isbn': (str, ''), 'budget_code': (str, ''),
            'period_of_interest_from': (str, ''), 'period_of_interest_to': (str, ''),
            'additional_comments': (str, ''), 'only_edition': (str, 'No'), 'key': (str, None),
            'string': (str, ''), 'borrower_id': (str, None), 'ln': (str, "en")})

        title = argd['title']
        authors = argd['authors']
        place = argd['place']
        publisher = argd['publisher']
        year = argd['year']
        edition = argd['edition']
        isbn = argd['isbn']
        budget_code = argd['budget_code']
        period_of_interest_from = argd['period_of_interest_from']
        period_of_interest_to = argd['period_of_interest_to']
        additional_comments = argd['additional_comments']
        only_edition = argd['only_edition']
        key = argd['key']
        string = argd['string']
        borrower_id = argd['borrower_id']
        ln = argd['ln']

        if borrower_id is not None:
            borrower_id = borrower_id.strip()
        if borrower_id == 'None':
            borrower_id = None

        title = title.strip()
        authors = authors.strip()
        place = place.strip()
        publisher = publisher.strip()
        year = year.strip()
        edition =  edition.strip()
        isbn = isbn.strip()
        budget_code = budget_code.strip()
        period_of_interest_from = period_of_interest_from.strip()
        period_of_interest_to = period_of_interest_to.strip()
        string = string.strip()

        return bal.register_ill_request_with_no_recid_step2(req, title, authors, place,
                            publisher, year, edition, isbn, budget_code, period_of_interest_from,
                            period_of_interest_to, additional_comments,
                            only_edition, key, string, borrower_id, ln)

    def register_ill_request_with_no_recid_step3(self, req, form):
        """    """
        argd = wash_urlargd(form, {'title': (str, None), 'authors': (str, None),
            'place': (str, None), 'publisher': (str, None), 'year': (str, None),
            'edition': (str, None), 'isbn': (str, None), 'user_info': (str, None),
            'budget_code': (str, ''), 'period_of_interest_from': (str, None),
            'period_of_interest_to': (str, None), 'additional_comments': (str, None),
            'only_edition': (str, 'No'), 'ln': (str, "en")})

        title = argd['title']
        authors = argd['authors']
        place = argd['place']
        publisher = argd['publisher']
        year = argd['year']
        edition = argd['edition']
        isbn = argd['isbn']

        user_info = argd['user_info']

        budget_code = argd['budget_code']
        period_of_interest_from = argd['period_of_interest_from']
        period_of_interest_to = argd['period_of_interest_to']
        additional_comments = argd['additional_comments']
        only_edition = argd['only_edition']

        ln = argd['ln']

        if user_info is not None:
            user_info = user_info.split(',')

        return bal.register_ill_request_with_no_recid_step3(req, title, authors, place,
                                                            publisher, year, edition, isbn,
                                                            user_info, budget_code,
                                                            period_of_interest_from,
                                                            period_of_interest_to,
                                                            additional_comments,
                                                            only_edition, ln)

    def register_ill_request_with_no_recid_step4(self, req, form):
        """    """

        argd = wash_urlargd(form, {'title': (str, None), 'authors': (str, None),
            'place': (str, None), 'publisher': (str, None), 'year': (str, None),
            'edition': (str, None), 'isbn': (str, None), 'borrower_id': (str, None),
            'budget_code': (str, ''), 'period_of_interest_from': (str, None),
            'period_of_interest_to': (str, None), 'additional_comments': (str, None),
            'only_edition': (str, None), 'ln': (str, "en")})

        title = argd['title']
        authors = argd['authors']
        place = argd['place']
        publisher = argd['publisher']
        year = argd['year']
        edition = argd['edition']
        isbn = argd['isbn']

        borrower_id = argd['borrower_id']

        budget_code = argd['budget_code']
        period_of_interest_from = argd['period_of_interest_from']
        period_of_interest_to = argd['period_of_interest_to']
        additional_comments = argd['additional_comments']
        only_edition = argd['only_edition']

        ln = argd['ln']

        book_info = (title, authors, place, publisher, year, edition, isbn)

        request_details = (budget_code, period_of_interest_from, period_of_interest_to,
                            additional_comments, only_edition)

        return bal.register_ill_request_with_no_recid_step4(req, book_info, borrower_id,
                                                            request_details, ln)


    def register_ill_book_request(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/holdings_search"""
        argd = wash_urlargd(form, {'borrower_id': (str, None), 'ln': (str, "en")})
        ln = argd['ln']
        borrower_id = argd['borrower_id']
        return bal.register_ill_book_request(req, borrower_id, ln)

    def register_ill_book_request_result(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/item_search_result"""
        argd = wash_urlargd(form, {'borrower_id': (str, None),'p': (str, None),
                                    'f': (str, None), 'ln': (str, "en")})
        p = argd['p']
        f = argd['f']
        ln = argd['ln']
        borrower_id = argd['borrower_id']
        return bal.register_ill_book_request_result(req, borrower_id, p, f, ln)


    def register_ill_article_request_step1(self, req, form):
        """    """
        argd = wash_urlargd(form, {'ln': (str, "en")})

        ln = argd['ln']

        return bal.register_ill_article_request_step1(req, ln)

    def register_ill_article_request_step2(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/register_ill_request_with_no_recid_step2"""

        argd = wash_urlargd(form, {'periodical_title': (str, None),
            'article_title': (str, None), 'author': (str, None),
            'report_number': (str, None), 'volume': (str, None),
            'issue': (str, None), 'page': (str, None), 'year': (str, None),
            'budget_code': (str, ''), 'issn': (str, None),
            'period_of_interest_from': (str, None),
            'period_of_interest_to': (str, None),
            'additional_comments': (str, None), 'key': (str, None),
            'string': (str, None), 'ln': (str, "en")})

        periodical_title = argd['periodical_title']
        article_title = argd['article_title']
        author = argd['author']
        report_number = argd['report_number']
        volume = argd['volume']
        issue = argd['issue']
        page = argd['page']
        year = argd['year']
        budget_code = argd['budget_code']
        issn = argd['issn']
        period_of_interest_from = argd['period_of_interest_from']
        period_of_interest_to = argd['period_of_interest_to']
        additional_comments = argd['additional_comments']
        key = argd['key']
        string = argd['string']
        ln = argd['ln']

        return bal.register_ill_article_request_step2(req, periodical_title, article_title,
                                                      author, report_number,
                                                      volume, issue, page, year, budget_code,
                                                      issn, period_of_interest_from,
                                                      period_of_interest_to,
                                                      additional_comments, key, string, ln)

    def register_ill_article_request_step3(self, req, form):

        argd = wash_urlargd(form, {'periodical_title': (str, ''), 'article_title': (str, ''),
                'author': (str, ''), 'report_number': (str, ''), 'volume': (str, ''),
                'issue': (str, ''), 'page': (str, ''), 'year': (str, ''), 'issn': (str, ''),
                'user_info': (str, None), 'request_details': (str, '()'),
                'ln': (str, "en"), 'period_of_interest_from': (str, ''),
                'period_of_interest_to': (str, ''), 'budget_code': (str, ''),
                'additional_comments': (str, '')})

        periodical_title = argd['periodical_title']
        article_title = argd['article_title']
        author = argd['author']
        report_number = argd['report_number']
        volume = argd['volume']
        issue = argd['issue']
        page = argd['page']
        year = argd['year']
        issn = argd['issn']
        user_info = argd['user_info']
        request_details = argd['request_details']
        ln = argd['ln']
        period_of_interest_from = argd['period_of_interest_from']
        period_of_interest_to = argd['period_of_interest_to']
        budget_code = argd['budget_code']
        additional_comments = argd['additional_comments']

        request_details = (period_of_interest_from, period_of_interest_to,
                           budget_code, additional_comments)

        if user_info is not None:
            user_info = user_info.split(',')

        return bal.register_ill_article_request_step3(req, periodical_title, article_title,
                                        author, report_number, volume, issue, page, year, issn,
                                        user_info, request_details, ln)


    def register_purchase_request_step1(self, req, form):
        """    """
        argd = wash_urlargd(form, {'type': (str, 'acq-book'),
                'title': (str, ''), 'authors': (str, ''), 'place': (str, ''),
                'publisher': (str, ''), 'year': (str, ''), 'edition': (str, ''),
                'this_edition_only': (str, 'No'),
                'isbn': (str, ''), 'standard_number': (str, ''),
                'budget_code': (str, ''), 'cash': (str, 'No'),
                'period_of_interest_from': (str, ''),
                'period_of_interest_to': (str, ''),
                'additional_comments': (str, ''), 'ln': (str, "en")})

        request_type = argd['type'].strip()
        title = argd['title'].strip()
        authors = argd['authors'].strip()
        place = argd['place'].strip()
        publisher = argd['publisher'].strip()
        year = argd['year'].strip()
        edition = argd['edition'].strip()
        this_edition_only = argd['this_edition_only'].strip()
        isbn = argd['isbn'].strip()
        standard_number = argd['standard_number'].strip()
        budget_code = argd['budget_code'].strip()
        cash = argd['cash'] == 'Yes'
        period_of_interest_from = argd['period_of_interest_from'].strip()
        period_of_interest_to = argd['period_of_interest_to'].strip()
        additional_comments = argd['additional_comments'].strip()
        ln = argd['ln']

        return bal.register_purchase_request_step1(req, request_type, title,
                                authors, place, publisher, year, edition,
                                this_edition_only, isbn, standard_number,
                                budget_code, cash, period_of_interest_from,
                                period_of_interest_to, additional_comments, ln)

    def register_purchase_request_step2(self, req, form):
        """    """
        argd = wash_urlargd(form, {'type': (str, 'acq-book'), 'recid': (str, ''),
                'title': (str, ''), 'authors': (str, ''), 'place': (str, ''),
                'publisher': (str, ''), 'year': (str, ''), 'edition': (str, ''),
                'this_edition_only': (str, 'No'),
                'isbn': (str, ''), 'standard_number': (str, ''),
                'budget_code': (str, ''), 'cash': (str, 'No'),
                'period_of_interest_from': (str, ''),
                'period_of_interest_to': (str, ''),
                'additional_comments': (str, ''), 'p': (str, ''),
                'f': (str, ''), 'ln': (str, "en")})

        request_type = argd['type'].strip()
        recid = argd['recid'].strip()
        title = argd['title'].strip()
        authors = argd['authors'].strip()
        place = argd['place'].strip()
        publisher = argd['publisher'].strip()
        year = argd['year'].strip()
        edition = argd['edition'].strip()
        this_edition_only = argd['this_edition_only'].strip()
        isbn = argd['isbn'].strip()
        standard_number = argd['standard_number'].strip()
        budget_code = argd['budget_code'].strip()
        cash = (argd['cash'] == 'Yes')
        period_of_interest_from = argd['period_of_interest_from'].strip()
        period_of_interest_to = argd['period_of_interest_to'].strip()
        additional_comments = argd['additional_comments'].strip()
        p = argd['p'].strip()
        f = argd['f'].strip()
        ln = argd['ln']

        return bal.register_purchase_request_step2(req, request_type, recid, title, authors,
                        place, publisher, year, edition, this_edition_only,
                        isbn, standard_number, budget_code, cash,
                        period_of_interest_from, period_of_interest_to,
                        additional_comments, p, f, ln)

    def register_purchase_request_step3(self, req, form):
        """    """
        argd = wash_urlargd(form, {'type': (str, 'acq-book'), 'recid': (str, ''),
                'title': (str, ''), 'authors': (str, ''), 'place': (str, ''),
                'publisher': (str, ''), 'year': (str, ''), 'edition': (str, ''),
                'this_edition_only': (str, 'No'),
                'isbn': (str, ''), 'standard_number': (str, ''),
                'budget_code': (str, ''), 'cash': (str, 'No'),
                'period_of_interest_from': (str, ''),
                'period_of_interest_to': (str, ''),
                'additional_comments': (str, ''),
                'borrower_id': (str, ''), 'ln': (str, "en")})

        request_type = argd['type'].strip()
        recid = argd['recid'].strip()
        title = argd['title'].strip()
        authors = argd['authors'].strip()
        place = argd['place'].strip()
        publisher = argd['publisher'].strip()
        year = argd['year'].strip()
        edition = argd['edition'].strip()
        this_edition_only = argd['this_edition_only'].strip()
        isbn = argd['isbn'].strip()
        standard_number = argd['standard_number'].strip()
        budget_code = argd['budget_code'].strip()
        cash = (argd['cash'] == 'Yes')
        period_of_interest_from = argd['period_of_interest_from'].strip()
        period_of_interest_to = argd['period_of_interest_to'].strip()
        additional_comments = argd['additional_comments'].strip()
        borrower_id = argd['borrower_id'].strip()
        ln = argd['ln']

        return bal.register_purchase_request_step3(req, request_type, recid, title, authors,
                        place, publisher, year, edition, this_edition_only,
                        isbn, standard_number,
                        budget_code, cash, period_of_interest_from,
                        period_of_interest_to, additional_comments,
                        borrower_id, ln)


    def ill_request_details_step1(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/ill_request_details_step1"""

        argd = wash_urlargd(form, {'delete_key': (str, None), 'ill_request_id': (str, None),
                                   'new_status': (str, None), 'ln': (str, "en")})

        delete_key = argd['delete_key']
        ill_request_id = argd['ill_request_id']
        new_status = argd['new_status']
        ln = argd['ln']

        return bal.ill_request_details_step1(req, delete_key, ill_request_id, new_status, ln)

    def ill_request_details_step2(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/ill_request_details_step2"""

        argd = wash_urlargd(form, {'delete_key': (str, None),
            'ill_request_id': (str, None), 'recid': (str, ''), 'new_status': (str, None),
            'library_id': (str, None), 'request_date': (str, None),
            'expected_date': (str, None), 'arrival_date': (str, None),
            'due_date': (str, None), 'return_date': (str, None),
            'cost': (str, None), 'currency': (str, None),
            'barcode': (str, None), 'library_notes': (str, None),
            'title': (str, None), 'authors': (str, None), 'place': (str, None),
            'publisher': (str, None), 'year': (str, None),
            'edition': (str, None), 'isbn': (str, None),
            'periodical_title': (str,None), 'volume': (str,''),
            'issue': (str,''), 'page': (str,''), 'issn': (str,None),
            'ln': (str, "en")})

        delete_key = argd['delete_key']
        ill_request_id = argd['ill_request_id']
        recid = argd['recid']
        new_status = argd['new_status']
        library_id = argd['library_id']
        request_date = argd['request_date']
        expected_date = argd['expected_date']
        arrival_date = argd['arrival_date']
        due_date = argd['due_date']
        return_date = argd['return_date']
        cost = argd['cost']
        currency = argd['currency']
        barcode = argd['barcode']
        library_notes = argd['library_notes']

        title = argd['title']
        authors = argd['authors']
        place = argd['place']
        publisher = argd['publisher']
        year = argd['year']
        edition = argd['edition']
        isbn = argd['isbn']

        periodical_title = argd['periodical_title']
        volume = argd['volume']
        issue = argd['issue']
        page = argd['page']
        issn = argd['issn']

        ln = argd['ln']

        if library_notes is not None:
            library_notes = library_notes.strip()
        if delete_key is not None:
            delete_key = delete_key.strip()
        if ill_request_id is not None:
            ill_request_id = ill_request_id.strip()
        if recid is not None:
            recid = recid.strip()
        if new_status is not None:
            new_status = new_status.strip()
        if library_id is not None:
            library_id = library_id.strip()
        if return_date is not None:
            return_date = return_date.strip()
        if expected_date is not None:
            expected_date = expected_date.strip()
        if arrival_date is not None:
            arrival_date = arrival_date.strip()
        if due_date is not None:
            due_date = due_date.strip()
        if return_date is not None:
            return_date = return_date.strip()
        if cost is not None:
            cost = cost.strip()
        if currency is not None:
            currency = currency.strip()
        if barcode is not None:
            barcode = barcode.strip()

        if title is not None:
            title = title.strip()
        if authors is not None:
            authors = authors.strip()
        if place is not None:
            place = place.strip()
        if publisher is not None:
            publisher = publisher.strip()
        if year is not None:
            year = year.strip()
        if edition is not None:
            edition =  edition.strip()
        if isbn is not None:
            isbn = isbn.strip()


        if periodical_title is not None:
            periodical_title = periodical_title.strip()
        if volume is not None:
            volume = volume.strip()
        if issue is not None:
            issue = issue.strip()
        if page is not None:
            page = page.strip()
        if issn is not None:
            issn = issn.strip()

        article_info = {'periodical_title': periodical_title, 'title': title, 'authors': authors,
            'place': place, 'publisher': publisher, 'year' : year,  'edition': "", 'issn' : issn,
            'volume': volume, 'issue': issue, 'page': page }

        if recid:
            book_info = "{'recid': " + str(recid) + "}"
        else:
            book_info = {'title': title, 'authors': authors, 'place': place, 'publisher': publisher,
                     'year': year, 'edition': edition, 'isbn': isbn}

        return bal.ill_request_details_step2(req, delete_key, ill_request_id, new_status,
                                        library_id, request_date, expected_date, arrival_date,
                                        due_date, return_date, cost, currency, barcode,
                                        library_notes, book_info, article_info, ln)

    def purchase_details_step1(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/purchase_details_step1"""

        argd = wash_urlargd(form, {'delete_key': (str, None), 'ill_request_id': (str, None),
                                   'new_status': (str, None), 'ln': (str, "en")})

        delete_key = argd['delete_key']
        ill_request_id = argd['ill_request_id']
        new_status = argd['new_status']
        ln = argd['ln']

        return bal.purchase_details_step1(req, delete_key, ill_request_id, new_status, ln)

    def purchase_details_step2(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/purchase_details_step2"""

        argd = wash_urlargd(form, {'ill_request_id': (str, None), 'recid': (str, ''),
            'new_status': (str, None), 'library_id': (str, None),
            'request_date': (str, None), 'expected_date': (str, None),
            'arrival_date': (str, None), 'due_date': (str, None),
            'return_date': (str, None), 'cost': (str, ''), 'authors': (str, ''),
            'library_notes': (str, ''), 'title': (str, ''), 'place': (str, ''),
            'publisher': (str, ''), 'year': (str, ''), 'edition': (str, ''),
            'isbn': (str, ''), 'budget_code': (str, ''),
            'standard_number': (str, ''), 'ln': (str, "en")})

        ill_request_id = argd['ill_request_id']
        new_status = argd['new_status']
        library_id = argd['library_id']
        request_date = argd['request_date']
        expected_date = argd['expected_date']
        arrival_date = argd['arrival_date']
        due_date = argd['due_date']
        return_date = argd['return_date']
        cost = argd['cost'].strip()
        budget_code = argd['budget_code'].strip()
        library_notes = argd['library_notes'].strip()
        standard_number = argd['standard_number'].strip()

        recid = argd['recid'].strip()
        title = argd['title'].strip()
        authors = argd['authors'].strip()
        place = argd['place'].strip()
        publisher = argd['publisher'].strip()
        year = argd['year'].strip()
        edition = argd['edition'].strip()
        isbn = argd['isbn'].strip()
        ln = argd['ln'].strip()

        if ill_request_id is not None:
            ill_request_id = ill_request_id.strip()
        if new_status is not None:
            new_status = new_status.strip()
        if library_id is not None:
            library_id = library_id.strip()
        if return_date is not None:
            return_date = return_date.strip()
        if expected_date is not None:
            expected_date = expected_date.strip()
        if arrival_date is not None:
            arrival_date = arrival_date.strip()
        if due_date is not None:
            due_date = due_date.strip()
        if return_date is not None:
            return_date = return_date.strip()

        if recid:
            item_info = "{'recid': " + str(recid) + "}"
        else:
            item_info = {'title': title, 'authors': authors,
                         'place': place, 'publisher': publisher,
                         'year': year, 'edition': edition, 'isbn': isbn,
                         'standard_number': standard_number}

        return bal.purchase_details_step2(req, None, ill_request_id,
                                    new_status, library_id, request_date,
                                    expected_date, arrival_date, due_date,
                                    return_date, cost, budget_code,
                                    library_notes, item_info, ln)

    def get_ill_library_notes(self, req, form):
        """    """
        argd = wash_urlargd(form, {'ill_id': (str, None), 'delete_key': (str, None),
                                        'library_notes': (str, None), 'ln': (str, "en")})
        ill_id = argd['ill_id']
        delete_key = argd['delete_key']
        library_notes = argd['library_notes']
        ln = argd['ln']

        return bal.get_ill_library_notes(req, ill_id, delete_key, library_notes, ln)


    def list_ill_request(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/list_ill_request"""
        argd = wash_urlargd(form, {'status': (str, None), 'ln': (str, "en")})
        status = argd['status']
        ln = argd['ln']

        return bal.list_ill_request(req, status, ln)

    def list_purchase(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/list_purchase"""
        argd = wash_urlargd(form, {'status': (str, None), 'recid': (str, None), 'ln': (str, "en")})
        status = argd['status']
        recid = argd['recid']
        ln = argd['ln']

        return bal.list_purchase(req, status, recid, ln)

    def list_proposal(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/list_proposal"""
        argd = wash_urlargd(form, {'status': (str, None), 'ln': (str, "en")})
        status = argd['status']
        ln = argd['ln']

        return bal.list_proposal(req, status, ln)


    def ill_search(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/holdings_search"""
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']
        return bal.ill_search(req, ln)

    def ill_search_result(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/item_search_result"""
        argd = wash_urlargd(form, {'p': (str, None), 'f': (str, None), 'date_from': (str, None),
                                        'date_to': (str, None), 'ln': (str, "en")})
        p = argd['p']
        f = argd['f']
        date_from = argd['date_from']
        date_to = argd['date_to']
        ln = argd['ln']

        if p is not None:
            p = p.strip()
        if date_from is not None:
            date_from = date_from.strip()
        if date_to is not None:
            date_to = date_to.strip()

        return bal.ill_search_result(req, p, f, date_from, date_to, ln)




# "Library" related pages




    def get_library_details(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/get_library_details"""
        argd = wash_urlargd(form, {'library_id': (str, None), 'ln': (str, "en")})
        library_id = argd['library_id']
        ln = argd['ln']
        return bal.get_library_details(req, library_id, ln)

    def merge_libraries_step1(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/merge_libraries_step1"""
        argd = wash_urlargd(form, {'library_id': (int, None), 'p': (str, None),
                                    'f': (str, None), 'ln': (str, None)})

        library_id = argd['library_id']
        p  = argd['p']
        f  = argd['f']
        ln = argd['ln']

        if p is not None:
            p = p.strip()

        return bal.merge_libraries_step1(req, library_id, f, p, ln)

    def merge_libraries_step2(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/merge_libraries_step2"""
        argd = wash_urlargd(form, {'library_from': (int, None), 'library_to': (int, None),
                                             'ln': (str, "en")})

        library_from = argd['library_from']
        library_to   = argd['library_to']
        ln = argd['ln']

        return bal.merge_libraries_step2(req, library_from, library_to, ln)

    def merge_libraries_step3(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/merge_libraries_step2"""
        argd = wash_urlargd(form, {'library_from': (int, None), 'library_to': (int, None),
                                             'ln': (str, "en")})

        library_from = argd['library_from']
        library_to   = argd['library_to']
        ln = argd['ln']

        return bal.merge_libraries_step3(req, library_from, library_to, ln)


    def add_new_library_step1(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/add_new_library_step1"""
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']
        return bal.add_new_library_step1(req, ln)

    def add_new_library_step2(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/add_new_library_step2"""
        argd = wash_urlargd(form, {'name': (str, ''), 'email': (str, ''),
            'phone': (str, ''), 'address': (str, ''), 'type': (str, ''),
            'notes': (str, None), 'ln': (str, "en")})
        name = argd['name']
        email = argd['email']
        phone = argd['phone']
        address = argd['address']
        library_type = argd['type']
        notes = argd['notes']
        ln = argd['ln']

        name = name.strip()
        email = email.strip()
        phone = phone.strip()
        address = address.strip()
        library_type = library_type.strip()

        return bal.add_new_library_step2(req, name, email, phone, address,
                                         library_type, notes, ln)

    def add_new_library_step3(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/add_new_library_step3"""
        argd = wash_urlargd(form, {'name': (str, None), 'email': (str, None),
            'phone': (str, None), 'address': (str, None), 'lib_type': (str, None),
            'notes': (str, None), 'ln': (str, "en")})
        name = argd['name']
        email = argd['email']
        phone = argd['phone']
        address = argd['address']
        library_type = argd['lib_type']
        notes = argd['notes']
        ln = argd['ln']

        return bal.add_new_library_step3(req,name, email, phone, address, library_type, notes, ln)


    def update_library_info_step1(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/update_library_info_step1"""
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']
        return bal.update_library_info_step1(req, ln)

    def update_library_info_step2(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/update_library_info_step2"""
        argd = wash_urlargd(form, {'column': (str, None), 'string': (str, None),
                                    'ln': (str, "en")})
        column = argd['column']
        string = argd['string']
        ln = argd['ln']

        if string is not None:
            string = string.strip()

        return bal.update_library_info_step2(req, column, string, ln)

    def update_library_info_step3(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/update_library_info_step3"""
        argd = wash_urlargd(form, {'library_id': (str, None), 'ln': (str, "en")})
        library_id = argd['library_id']
        ln = argd['ln']
        return bal.update_library_info_step3(req, library_id, ln)

    def update_library_info_step4(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/update_library_info_step4"""
        argd = wash_urlargd(form, {'name': (str, ''), 'email': (str, ''),
            'phone': (str, ''), 'address': (str, ''), 'library_id': (str, ''),
            'lib_type': (str, ''), 'ln': (str, "en")})

        name = argd['name']
        email = argd['email']
        phone = argd['phone']
        address = argd['address']
        lib_type = argd['lib_type']
        library_id = argd['library_id']
        ln = argd['ln']

        name = name.strip()
        email = email.strip()
        phone = phone.strip()
        address = address.strip()
        lib_type = lib_type.strip()

        return bal.update_library_info_step4(req, name, email, phone, address, lib_type,
                                             library_id, ln)

    def update_library_info_step5(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/update_library_info_step5"""
        argd = wash_urlargd(form, {'name': (str, None), 'email': (str, None),
                        'phone': (str, None), 'address': (str, None), 'library_id': (str, None),
                        'lib_type': (str, None), 'ln': (str, "en")})

        name = argd['name']
        email = argd['email']
        phone = argd['phone']
        address = argd['address']
        lib_type = argd['lib_type']
        library_id = argd['library_id']
        ln = argd['ln']

        return bal.update_library_info_step5(req, name, email, phone, address, lib_type,
                                             library_id, ln)


    def get_library_notes(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/get_library_notes"""
        argd = wash_urlargd(form, {'library_id': (str, None), 'delete_key': (str, None),
                                    'library_notes': (str, None), 'ln': (str, "en")})
        library_id = argd['library_id']
        delete_key = argd['delete_key']
        library_notes = argd['library_notes']
        ln = argd['ln']
        return bal.get_library_notes(req, library_id, delete_key, library_notes, ln)

    def search_library_step1(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/search_library_step1"""
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']
        return bal.search_library_step1(req=req, ln=ln)

    def search_library_step2(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/search_library_step2"""
        argd = wash_urlargd(form, {'column': (str, ''), 'string': (str, ''), 'ln': (str, "en")})
        column = argd['column']
        string = argd['string']
        ln = argd['ln']

        string = string.strip()

        return bal.search_library_step2(req, column, string, ln)



# "Vendor related pages



    def get_vendor_details(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/get_vendor_details"""
        argd = wash_urlargd(form, {'vendor_id': (str, None), 'ln': (str, "en")})
        vendor_id = argd['vendor_id']
        ln = argd['ln']
        return bal.get_vendor_details(req, vendor_id, ln)

    def add_new_vendor_step1(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/add_new_vendor_step1"""
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']
        return bal.add_new_vendor_step1(req, ln)

    def add_new_vendor_step2(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/add_new_vendor_step2"""
        argd = wash_urlargd(form, {'name': (str, None), 'email': (str, None),
        'phone': (str, None), 'address': (str, None), 'notes': (str, None), 'ln': (str, "en")})

        name = argd['name']
        email = argd['email']
        phone = argd['phone']
        address = argd['address']
        notes = argd['notes']
        ln = argd['ln']

        if name is not None:
            name = name.strip()
        if email is not None:
            email = email.strip()
        if phone is not None:
            phone = phone.strip()
        if address is not None:
            address = address.strip()

        return bal.add_new_vendor_step2(req, name, email, phone, address,
                                        notes, ln)

    def add_new_vendor_step3(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/add_new_vendor_step3"""
        argd = wash_urlargd(form, {'name': (str, None), 'email': (str, None),
            'phone': (str, None), 'address': (str, None), 'notes': (str, None),
            'ln': (str, "en")})

        name = argd['name']
        email = argd['email']
        phone = argd['phone']
        address = argd['address']
        notes = argd['notes']
        ln = argd['ln']
        return bal.add_new_vendor_step3(req, name, email, phone, address,
                                        notes, ln)


    def update_vendor_info_step1(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/update_vendor_info_step1"""
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']
        return bal.update_vendor_info_step1(req, ln)

    def update_vendor_info_step2(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/update_vendor_info_step2"""
        argd = wash_urlargd(form, {'column': (str, None), 'string': (str, None),
            'ln': (str, "en")})

        column = argd['column']
        string = argd['string']
        ln = argd['ln']

        if string is not None:
            string = string.strip()

        return bal.update_vendor_info_step2(req, column, string, ln)

    def update_vendor_info_step3(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/update_vendor_info_step3"""
        argd = wash_urlargd(form, {'vendor_id': (str, None), 'ln': (str, "en")})
        vendor_id = argd['vendor_id']
        ln = argd['ln']
        return bal.update_vendor_info_step3(req, vendor_id, ln)

    def update_vendor_info_step4(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/update_vendor_info_step4"""
        argd = wash_urlargd(form, {'name': (str, None), 'email': (str, None),
            'phone': (str, None), 'address': (str, None), 'vendor_id': (str, None),
            'ln': (str, "en")})

        name = argd['name']
        email = argd['email']
        phone = argd['phone']
        address = argd['address']
        vendor_id = argd['vendor_id']
        ln = argd['ln']

        if name is not None:
            name = name.strip()
        if email is not None:
            email = email.strip()
        if phone is not None:
            phone = phone.strip()
        if address is not None:
            address = address.strip()

        return bal.update_vendor_info_step4(req, name, email, phone, address,
                                            vendor_id, ln)

    def update_vendor_info_step5(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/update_vendor_info_step5"""
        argd = wash_urlargd(form, {'name': (str, None), 'email': (str, None),
            'phone': (str, None), 'address': (str, None), 'vendor_id': (str, None),
            'ln': (str, "en")})

        name = argd['name']
        email = argd['email']
        phone = argd['phone']
        address = argd['address']
        vendor_id = argd['vendor_id']
        ln = argd['ln']
        return bal.update_vendor_info_step5(req, name, email, phone, address,
                                            vendor_id, ln)


    def get_vendor_notes(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/get_vendor_notes"""
        argd = wash_urlargd(form, {'vendor_id': (str, None), 'add_notes': (str, None),
                                    'new_note': (str, None), 'ln': (str, "en")})
        vendor_id = argd['vendor_id']
        add_notes = argd['add_notes']
        new_note = argd['new_note']
        ln = argd['ln']
        return bal.get_vendor_notes(req, vendor_id, add_notes, new_note, ln)

    def search_vendor_step1(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/search_vendor_step1"""
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']
        return bal.search_vendor_step1(req, ln)

    def search_vendor_step2(self, req, form):
        """http://cds.cern.ch/admin2/bibcirculation/search_vendor_step2"""
        argd = wash_urlargd(form, {'column': (str, ''), 'string': (str, ''), 'ln': (str, "en")})
        column = argd['column']
        string = argd['string']
        ln = argd['ln']

        if string is not None:
            string = string.strip()

        return bal.search_vendor_step2(req, column, string, ln)


    def __call__(self, req, form):
        """Redirect calls without final slash."""
        redirect_to_url(req, '%s/admin2/bibcirculation/' % CFG_SITE_URL)
