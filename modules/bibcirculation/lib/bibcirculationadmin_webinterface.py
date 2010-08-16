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

"""CDS Invenio BibCirculation Administrator (URLs) Interface."""

__revision__ = ""

import invenio.bibcirculationadminlib as bal
from invenio.config import CFG_SITE_URL
from invenio.urlutils import wash_url_argument, redirect_to_url
#from cgi import escape

from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory

class WebInterfaceBibCirculationAdminPages(WebInterfaceDirectory):
    """Defines the set of /admin2/bibcirculation pages."""

    _exports = ['', 'index', 'borrower_search', 'item_search', 'borrower_notification', 'get_pending_requests', 'item_search_result', 'loan_return', 'loan_on_desk_step1', 'loan_on_desk_step2', 'loan_on_desk_step3', 'loan_on_desk_step4', 'loan_on_desk_confirm', 'register_new_loan', 'loan_return_confirm', 'get_next_waiting_loan_request', 'update_next_loan_request_status', 'all_requests', 'get_item_req_historical_overview', 'get_item_loans_historical_overview', 'all_loans_test', 'all_loans', 'bor_loans_historical_overview', 'bor_requests_historical_overview', 'get_item_requests_details', 'get_item_loans_details', 'get_borrower_details', 'get_item_details', 'get_library_details', 'get_borrower_requests_details', 'get_borrower_loans_details', 'borrower_search_result', 'associate_barcode', 'get_borrower_notes', 'get_loans_notes', 'get_item_loans_notes', 'new_item', 'add_new_borrower_step1', 'add_new_borrower_step2', 'add_new_borrower_step3', 'update_borrower_info_step1', 'update_borrower_info_step2', 'update_borrower_info_step3', 'update_borrower_info_step4', 'update_borrower_info_step5', 'add_new_library_step1', 'add_new_library_step2', 'add_new_library_step3', 'update_library_info_step1', 'update_library_info_step2', 'update_library_info_step3', 'update_library_info_step4', 'update_library_info_step5', 'new_book_step1', 'new_book_step2', 'add_new_copy_step1', 'add_new_copy_step2', 'add_new_copy_step3', 'add_new_copy_step4', 'add_new_copy_step5', 'update_item_info_step1', 'update_item_info_step2', 'update_item_info_step3', 'update_item_info_step4', 'update_item_info_step5', 'update_item_info_step6', 'search_library_step1', 'search_library_step2', 'get_library_notes', 'change_due_date_step1', 'change_due_date_step2', 'claim_book_return', 'all_expired_loans', 'get_waiting_requests', 'create_new_loan_step1', 'create_new_loan_step2', 'create_new_request_step1', 'create_new_request_step2', 'create_new_request_step3', 'create_new_request_step4', 'place_new_request_step1', 'place_new_request_step2', 'place_new_request_step3', 'place_new_loan_step1', 'place_new_loan_step2', 'place_new_loan_step3', 'order_new_copy_step1', 'order_new_copy_step3', 'ordered_books', 'get_purchase_notes', 'register_ill_request_step0', 'register_ill_request_step1', 'register_ill_request_step2', 'register_ill_request_step3', 'list_ill_request', 'ill_request_details_step1', 'ill_request_details_step2', 'ill_request_details_step3', 'ordered_books_details_step1', 'ordered_books_details_step2', 'ordered_books_details_step3', 'add_new_vendor_step1', 'add_new_vendor_step2', 'add_new_vendor_step3', 'update_vendor_info_step1', 'update_vendor_info_step2', 'update_vendor_info_step3', 'update_vendor_info_step4', 'update_vendor_info_step5', 'search_vendor_step1', 'search_vendor_step2', 'get_vendor_details', 'get_vendor_notes', 'register_ill_request_with_no_recid_step1', 'register_ill_request_with_no_recid_step2', 'register_ill_request_with_no_recid_step3', 'register_ill_request_with_no_recid_step4', 'get_borrower_ill_details', 'get_ill_library_notes', 'get_expired_loans_with_requests', 'register_ill_book_request', 'register_ill_book_request_result', 'register_ill_book_request_from_borrower_page', 'register_ill_book_request_from_borrower_page_result', 'register_ill_request_from_borrower_page_step1', 'register_ill_request_from_borrower_page_step2', 'register_ill_article_request_step1', 'register_ill_article_request_step2', 'register_ill_article_request_step3', 'ill_search', 'ill_search_result', 'bor_ill_historical_overview', 'delete_copy_step1', 'delete_copy_step2']

    def index(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation"""
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']
        return bal.index(req, ln)


    def borrower_search(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/borrowers_search"""
        argd = wash_urlargd(form, {'empty_barcode': (str, None), 'redirect': (str, "no"), 'ln': (str, "en")})
        empty_barcode = argd['empty_barcode']
        redirect = argd['redirect']
        ln = argd['ln']
        return bal.borrower_search(req, empty_barcode, redirect=redirect, ln=ln)


    def item_search(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/holdings_search"""
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']
        return bal.item_search(req, [], ln)


    def borrower_notification(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/borrower_notification"""
        argd = wash_urlargd(form, {'borrower_id': (str, None), 'borrower_email': (str,None), 'template': (str, None), 'message': (str, None), 'load_msg_template': (str, None), 'subject': (str, None), 'send_message': (str, None), 'ln': (str, "en")})
        borrower_id = argd['borrower_id']
        borrower_email = argd['borrower_email']
        template = argd['template']
        message = argd['message']
        load_msg_template = argd['load_msg_template']
        subject = argd['subject']
        send_message = argd['send_message']
        ln = argd['ln']
        return bal.borrower_notification(req, borrower_id, borrower_email, template,
                                         message, load_msg_template,
                                         subject, send_message, ln)


    def get_pending_requests(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/get_pending_requests"""
        argd = wash_urlargd(form, {'request_id': (str, None), 'print_data': (str, None), 'ln': (str, "en")})
        request_id = argd['request_id']
        print_data = argd['print_data']
        ln = argd['ln']
        return bal.get_pending_requests(req, request_id, print_data, ln)


    def item_search_result(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/item_search_result"""
        argd = wash_urlargd(form, {'p': (str, None), 'f': (str, None), 'ln': (str, "en")})
        p  = argd['p']
        f  = argd['f']
        ln = argd['ln']

        return bal.item_search_result(req, p, f, ln)

    def delete_copy_step1(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/delete_copy_step1"""
        argd = wash_urlargd(form, {'barcode': (str, ''), 'ln': (str, "en")})

        barcode = argd['barcode']
        ln = argd['ln']

        return bal.delete_copy_step1(req, barcode, ln)

    def delete_copy_step2(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/delete_copy_step2"""
        argd = wash_urlargd(form, {'barcode': (str, ''), 'ln': (str, "en")})

        barcode = argd['barcode']
        ln = argd['ln']

        return bal.delete_copy_step2(req, barcode, ln)

    def loan_return(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/loan_return"""
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']
        return bal.loan_return(req, ln)


    def loan_on_desk_step1(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/loan_on_desk_step1"""
        argd = wash_urlargd(form, {'key': (str, None), 'string': (str, None), 'ln': (str, "en")})
        key = argd['key']
        string = argd['string']
        ln = argd['ln']

        return bal.loan_on_desk_step1(req, key, string, ln)


    def loan_on_desk_step2(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/loan_on_desk_step2"""
        argd = wash_urlargd(form, {'user_info': (str, None), 'ln': (str, "en")})
        user_info = argd['user_info']
        ln = argd['ln']

        user_info = user_info.split(',')


        return bal.loan_on_desk_step2(req, user_info, ln)


    def loan_on_desk_step3(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/loan_on_desk_step4"""
        argd = wash_urlargd(form, {'user_info': (str, None), 'barcode': (str, None), 'ln': (str, "en")})
        user_info = argd['user_info']
        barcode = argd['barcode']
        ln = argd['ln']

        user_info = eval(user_info)

        return bal.loan_on_desk_step3(req, user_info, barcode, ln)


    def loan_on_desk_step4(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/loan_on_desk_step5"""
        argd = wash_urlargd(form, {'list_of_books': (str, None), 'user_info': (str, None), 'due_date': (str, None), 'note': (str, None), 'ln': (str, "en")})
        list_of_books = argd['list_of_books']
        user_info = argd['user_info']
        due_date = argd['due_date']
        note = argd['note']
        ln = argd['ln']

        user_info = eval(user_info)

        list_of_books = eval(list_of_books)
        due_date = wash_url_argument(due_date, 'list')


        return bal.loan_on_desk_step4(req, list_of_books, user_info,
                                      due_date, note, ln)


    def loan_on_desk_confirm(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/loan_on_desk_confirm"""
        argd = wash_urlargd(form, {'barcode': (str, None), 'borrower_id': (str, None), 'ln': (str, "en")})
        barcode = argd['barcode']
        borrower_id = argd['borrower_id']
        ln = argd['ln']
        return bal.loan_on_desk_confirm(req, barcode, borrower_id, ln)


    def register_new_loan(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/register_new_loan"""
        argd = wash_urlargd(form, {'barcode': (str, None), 'borrower_id': (str, None), 'request_id': (str, None), 'new_note': (str, None), 'print_data': (str, None), 'ln': (str, "en")})
        barcode = argd['barcode']
        borrower_id = argd['borrower_id']
        request_id = argd['request_id']
        new_note = argd['new_note']
        print_data = argd['print_data']
        ln = argd['ln']

        return bal.register_new_loan(req, barcode, borrower_id, request_id,
                                     new_note, print_data, ln)


    def loan_return_confirm(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/loan_return_confirm"""
        argd = wash_urlargd(form, {'barcode': (str, None), 'ln': (str, "en")})
        barcode = argd['barcode']
        ln = argd['ln']
        return bal.loan_return_confirm(req, barcode, ln)


    def get_next_waiting_loan_request(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/get_next_waiting_loan_request"""
        argd = wash_urlargd(form, {'recid': (str, None), 'barcode': (str, None), 'check_id': (str, None), 'ln': (str, "en")})
        recid = argd['recid']
        barcode = argd['barcode']
        check_id = argd['check_id']
        ln = argd['ln']
        return bal.get_next_waiting_loan_request(req, recid, barcode, check_id, ln)


    def update_next_loan_request_status(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/update_next_loan_request_status"""
        argd = wash_urlargd(form, {'check_id': (str, None), 'barcode': (str, None), 'ln': (str, "en")})
        check_id = argd['check_id']
        barcode = argd['barcode']
        ln = argd['ln']
        return bal.update_next_loan_request_status(req, check_id,
                                                   barcode, ln)


    def all_requests(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/all_requests"""
        argd = wash_urlargd(form, {'request_id': (str, None), 'ln': (str, "en")})
        request_id = argd['request_id']
        ln = argd['ln']
        return bal.all_requests(req, request_id, ln)


    def get_item_req_historical_overview(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/get_item_req_historical_overview"""
        argd = wash_urlargd(form, {'recid': (str, None), 'ln': (str, "en")})
        recid = argd['recid']
        ln = argd['ln']
        return bal.get_item_req_historical_overview(req, recid, ln)


    def get_item_loans_historical_overview(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/get_item_loans_historical_overview"""
        argd = wash_urlargd(form, {'recid': (str, None), 'ln': (str, "en")})
        recid = argd['recid']
        ln = argd['ln']
        return bal.get_item_loans_historical_overview(req, recid, ln)


    def all_loans_test(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/all_loans"""
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']
        return bal.all_loans_test(req, ln)


    def all_loans(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/all_loans"""
        argd = wash_urlargd(form, {'msg': (str, None), 'ln': (str, "en")})
        msg = argd['msg']
        ln = argd['ln']

        return bal.all_loans(req, msg=msg, ln=ln)


    def bor_loans_historical_overview(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/bor_loans_historical_overview"""
        argd = wash_urlargd(form, {'borrower_id': (str, None), 'ln': (str, "en")})
        borrower_id = argd['borrower_id']
        ln = argd['ln']
        return bal.bor_loans_historical_overview(req, borrower_id, ln)


    def bor_requests_historical_overview(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/bor_requests_historical_overview"""
        argd = wash_urlargd(form, {'borrower_id': (str, None), 'ln': (str, "en")})
        borrower_id = argd['borrower_id']
        ln = argd['ln']
        return bal.bor_requests_historical_overview(req, borrower_id, ln)


    def get_item_requests_details(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/borrowers_search"""
        argd = wash_urlargd(form, {'recid': (str, None), 'request_id': (str, None), 'ln': (str, "en")})
        recid = argd['recid']
        request_id = argd['request_id']
        ln = argd['ln']
        return bal.get_item_requests_details(req, recid, request_id, ln)


    def get_item_loans_details(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/borrowers_search"""
        argd = wash_urlargd(form, {'recid': (str, None), 'barcode': (str, None), 'loan_id': (str, None), 'force': (str, None), 'ln': (str, "en")})
        recid = argd['recid']
        barcode = argd['barcode']
        loan_id = argd['loan_id']
        force = argd['force']
        ln = argd['ln']
        return bal.get_item_loans_details(req, recid, barcode, loan_id, force, ln)


    def get_borrower_details(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/borrowers_search"""
        argd = wash_urlargd(form, {'borrower_id': (str, None), 'ln': (str, "en")})
        borrower_id = argd['borrower_id']
        ln = argd['ln']
        return bal.get_borrower_details(req, borrower_id, ln)


    def get_item_details(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/borrowers_search"""
        argd = wash_urlargd(form, {'recid': (str, None), 'ln': (str, "en")})
        recid = argd['recid']
        ln = argd['ln']
        return bal.get_item_details(req, recid, ln)


    def get_library_details(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/get_library_details"""
        argd = wash_urlargd(form, {'library_id': (str, None), 'ln': (str, "en")})
        library_id = argd['library_id']
        ln = argd['ln']
        return bal.get_library_details(req, library_id, ln)


    def get_borrower_requests_details(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/get_borrower_requests_details"""
        argd = wash_urlargd(form, {'borrower_id': (str, None), 'request_id': (str, None), 'ln': (str, "en")})
        borrower_id = argd['borrower_id']
        request_id = argd['request_id']
        ln = argd['ln']
        return bal.get_borrower_requests_details(req, borrower_id, request_id, ln)


    def get_borrower_loans_details(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/get_borrower_loans_details"""
        argd = wash_urlargd(form, {'recid': (str, None), 'barcode': (str, None), 'borrower_id': (str, None), 'renewall': (str, None), 'force': (str, None), 'loan_id': (str, None), 'ln': (str, "en")})
        recid = argd['recid']
        barcode = argd['barcode']
        borrower_id = argd['borrower_id']
        renewall = argd['renewall']
        force = argd['force']
        loan_id = argd['loan_id']
        ln = argd['ln']
        return bal.get_borrower_loans_details(req, recid, barcode, borrower_id,
                                              renewall, force, loan_id, ln)


    def borrower_search_result(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/borrower_search_result"""
        argd = wash_urlargd(form, {'column': (str, "name"), 'string': (str, ""), 'redirect': (str, "no"), 'ln': (str, "en")})
        column = argd['column']
        string = argd['string']
        redirect = argd['redirect']
        ln = argd['ln']

        return bal.borrower_search_result(req, column, string, redirect=redirect, ln=ln)


    def associate_barcode(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/associate_barcode"""
        argd = wash_urlargd(form, {'request_id': (str, None), 'recid': (str, None), 'borrower_id': (str, None), 'ln': (str, "en")})
        request_id = argd['request_id']
        recid = argd['recid']
        borrower_id = argd['borrower_id']
        ln = argd['ln']
        return bal.associate_barcode(req, request_id, recid, borrower_id, ln)


    def get_borrower_notes(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/get_borrower_notes"""
        argd = wash_urlargd(form, {'borrower_id': (str, None), 'delete_key': (str, None), 'library_notes': (str, None), 'ln': (str, "en")})
        borrower_id = argd['borrower_id']
        delete_key = argd['delete_key']
        library_notes = argd['library_notes']
        ln = argd['ln']
        return bal.get_borrower_notes(req, borrower_id, delete_key,
                                      library_notes, ln)


    def get_loans_notes(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/get_loans_notes"""
        argd = wash_urlargd(form, {'loan_id': (str, None), 'recid': (str, None), 'delete_key': (str, None), 'library_notes': (str, None), 'back': (str, ""), 'ln': (str, "en")})
        loan_id = argd['loan_id']
        #recid = argd['recid']
        delete_key = argd['delete_key']
        library_notes = argd['library_notes']
        back = argd['back']
        ln = argd['ln']
        return bal.get_loans_notes(req, loan_id, delete_key,
                                   library_notes, back, ln)


    def get_item_loans_notes(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/get_item_loans_notes"""
        argd = wash_urlargd(form, {'loan_id': (str, None), 'add_notes': (str, None), 'new_note': (str, None), 'ln': (str, "en")})
        loan_id = argd['loan_id']
        #recid = argd['recid']
        add_notes = argd['add_notes']
        new_note = argd['new_note']
        ln = argd['ln']
        return bal.get_item_loans_notes(req, loan_id, add_notes,
                                        new_note, ln)


    def new_item(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/new_item"""
        argd = wash_urlargd(form, {'isbn': (str, None), 'ln': (str, "en")})
        isbn = argd['isbn']
        ln = argd['ln']
        return bal.new_item(req, isbn, ln)


    def add_new_borrower_step1(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/add_new_borrower_step1"""
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']
        return bal.add_new_borrower_step1(req, ln)


    def add_new_borrower_step2(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/add_new_borrower_step2"""
        argd = wash_urlargd(form, {'name': (str, None), 'email': (str, None), 'phone': (str, None), 'address': (str, None), 'mailbox': (str, None), 'notes': (str, None), 'ln': (str, "en")})
        name = argd['name']
        email = argd['email']
        phone = argd['phone']
        address = argd['address']
        mailbox = argd['mailbox']
        notes = argd['notes']
        ln = argd['ln']
        return bal.add_new_borrower_step2(req, name, email, phone, address,
                                          mailbox, notes, ln)


    def add_new_borrower_step3(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/add_new_borrower_step3"""
        argd = wash_urlargd(form, {'tup_infos': (str, None), 'ln': (str, "en")})
        tup_infos = argd['tup_infos']
        ln = argd['ln']
        tup_infos = eval(tup_infos)

        return bal.add_new_borrower_step3(req, tup_infos, ln)


    def update_borrower_info_step1(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/update_borrower_info_step1"""
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']
        return bal.update_borrower_info_step1(req, ln)


    def update_borrower_info_step2(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/update_borrower_info_step2"""
        argd = wash_urlargd(form, {'column': (str, None), 'string': (str, None), 'ln': (str, "en")})
        column = argd['column']
        string = argd['string']
        ln = argd['ln']
        return bal.update_borrower_info_step2(req, column, string, ln)


    def update_borrower_info_step3(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/update_borrower_info_step3"""
        argd = wash_urlargd(form, {'borrower_id': (str, None), 'ln': (str, "en")})
        borrower_id = argd['borrower_id']
        ln = argd['ln']
        return bal.update_borrower_info_step3(req, borrower_id, ln)


    def update_borrower_info_step4(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/update_borrower_info_step4"""
        argd = wash_urlargd(form, {'name': (str, None), 'email': (str, None), 'phone': (str, None), 'address': (str, None), 'mailbox': (str, None), 'ln': (str, "en")})
        name = argd['name']
        email = argd['email']
        phone = argd['phone']
        address = argd['address']
        mailbox = argd['mailbox']
        ln = argd['ln']
        return bal.update_borrower_info_step4(req, name, email, phone, address,
                                              mailbox, ln)


    def update_borrower_info_step5(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/update_borrower_info_step5"""
        argd = wash_urlargd(form, {'tup_infos': (str, '()'), 'ln': (str, "en")})
        tup_infos = argd['tup_infos']
        ln = argd['ln']
        tup_infos = eval(tup_infos)

        return bal.update_borrower_info_step5(req, tup_infos, ln)


    def add_new_library_step1(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/add_new_library_step1"""
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']
        return bal.add_new_library_step1(req, ln)


    def add_new_library_step2(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/add_new_library_step2"""
        argd = wash_urlargd(form, {'name': (str, None), 'email': (str, None), 'phone': (str, None), 'address': (str, None), 'type': (str, None), 'notes': (str, None), 'ln': (str, "en")})
        name = argd['name']
        email = argd['email']
        phone = argd['phone']
        address = argd['address']
        library_type = argd['type']
        notes = argd['notes']
        ln = argd['ln']
        return bal.add_new_library_step2(req, name, email, phone, address,
                                         library_type, notes, ln)


    def add_new_library_step3(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/add_new_library_step3"""
        argd = wash_urlargd(form, {'tup_infos': (str, None), 'ln': (str, "en")})
        tup_infos = argd['tup_infos']
        ln = argd['ln']
        tup_infos = eval(tup_infos)

        return bal.add_new_library_step3(req, tup_infos, ln)


    def update_library_info_step1(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/update_library_info_step1"""
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']
        return bal.update_library_info_step1(req, ln)


    def update_library_info_step2(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/update_library_info_step2"""
        argd = wash_urlargd(form, {'column': (str, None), 'string': (str, None), 'ln': (str, "en")})
        column = argd['column']
        string = argd['string']
        ln = argd['ln']
        return bal.update_library_info_step2(req, column, string, ln)


    def update_library_info_step3(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/update_library_info_step3"""
        argd = wash_urlargd(form, {'library_id': (str, None), 'ln': (str, "en")})
        library_id = argd['library_id']
        ln = argd['ln']
        return bal.update_library_info_step3(req, library_id, ln)


    def update_library_info_step4(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/update_library_info_step4"""
        argd = wash_urlargd(form, {'name': (str, None), 'email': (str, None), 'phone': (str, None), 'address': (str, None), 'library_id': (str, None), 'ln': (str, "en")})
        name = argd['name']
        email = argd['email']
        phone = argd['phone']
        address = argd['address']
        library_id = argd['library_id']
        ln = argd['ln']
        return bal.update_library_info_step4(req, name, email, phone, address,
                                             library_id, ln)


    def update_library_info_step5(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/update_library_info_step5"""
        argd = wash_urlargd(form, {'tup_infos': (str, '()'), 'ln': (str, "en")})
        tup_infos = argd['tup_infos']
        ln = argd['ln']
        tup_infos = eval(tup_infos)

        return bal.update_library_info_step5(req, tup_infos, ln)


    def new_book_step1(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/new_book_step1"""
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']
        return bal.new_book_step1(req, ln)


    def new_book_step2(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/new_book_step2"""
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']
        return bal.new_book_step2(req, ln)


    def add_new_copy_step1(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/add_new_copy_step1"""
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']
        return bal.add_new_copy_step1(req, ln)


    def add_new_copy_step2(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/add_new_copy_step2"""
        argd = wash_urlargd(form, {'p': (str, None), 'f': (str, None), 'ln': (str, "en")})
        p = argd['p']
        f = argd['f']
        ln = argd['ln']
        return bal.add_new_copy_step2(req, p, f, ln)


    def add_new_copy_step3(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/add_new_copy_step3"""
        argd = wash_urlargd(form, {'recid': (str, None), 'ln': (str, "en")})
        recid = argd['recid']
        ln = argd['ln']
        return bal.add_new_copy_step3(req, recid, ln)


    def add_new_copy_step4(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/add_new_copy_step4"""
        argd = wash_urlargd(form, {'barcode': (str, None), 'library': (str, None), 'location': (str, None), 'collection': (str, None), 'description': (str, None), 'loan_period': (str, None), 'status': (str, None), 'recid': (str, None), 'ln': (str, "en")})
        barcode = argd['barcode']
        library = argd['library']
        location = argd['location']
        collection = argd['collection']
        description = argd['description']
        loan_period = argd['loan_period']
        status = argd['status']
        recid = argd['recid']
        ln = argd['ln']
        return bal.add_new_copy_step4(req, barcode, library, location, collection,
                                      description, loan_period, status, recid, ln)


    def add_new_copy_step5(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/add_new_copy_step5"""
        argd = wash_urlargd(form, {'tup_infos': (str, None), 'ln': (str, "en")})
        tup_infos = argd['tup_infos']
        ln = argd['ln']
        tup_infos = eval(tup_infos)
        return bal.add_new_copy_step5(req, tup_infos, ln)


    def update_item_info_step1(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/update_item_info_step1"""
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']
        return bal.update_item_info_step1(req, ln)


    def update_item_info_step2(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/update_item_info_step2"""
        argd = wash_urlargd(form, {'p': (str, '()'), 'f': (str, '()'), 'ln': (str, "en")})
        p = argd['p']
        f = argd['f']
        ln = argd['ln']
        return bal.update_item_info_step2(req, p, f, ln)


    def update_item_info_step3(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/update_item_info_step3"""
        argd = wash_urlargd(form, {'recid': (int, 0), 'ln': (str, "en")})
        recid = argd['recid']
        ln = argd['ln']
        return bal.update_item_info_step3(req, recid, ln)


    def update_item_info_step4(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/update_item_info_step4"""
        argd = wash_urlargd(form, {'barcode': (str, '()'), 'ln': (str, "en")})
        barcode = argd['barcode']
        ln = argd['ln']
        return bal.update_item_info_step4(req, barcode, ln)


    def update_item_info_step5(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/update_item_info_step5"""
        argd = wash_urlargd(form, {'barcode': (str, '-'), 'library': (int, 0), 'location': (str, 'Unknown'), 'collection': (str, 'Unknown'), 'description': (str, ''), 'loan_period': (str, '4 weeks'), 'status': (str, 'available'), 'recid': (int, 0), 'ln': (str, "en")})
        barcode = argd['barcode']
        library = argd['library']
        location = argd['location']
        collection = argd['collection']
        description = argd['description']
        loan_period = argd['loan_period']
        status = argd['status']
        recid = argd['recid']
        ln = argd['ln']
        return bal.update_item_info_step5(req, barcode, library, location,
                                          collection, description, loan_period,
                                          status, recid, ln)


    def update_item_info_step6(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/update_item_info_step6"""
        argd = wash_urlargd(form, {'tup_infos': (str, ''), 'ln': (str, "en")})
        tup_infos = argd['tup_infos']
        ln = argd['ln']
        tup_infos = eval(tup_infos)

        return bal.update_item_info_step6(req, tup_infos, ln)


    def search_library_step1(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/search_library_step1"""
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']
        return bal.search_library_step1(req, ln)


    def search_library_step2(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/search_library_step2"""
        argd = wash_urlargd(form, {'column': (str, ''), 'string': (str, ''), 'ln': (str, "en")})
        column = argd['column']
        string = argd['string']
        ln = argd['ln']

        return bal.search_library_step2(req, column, string, ln)


    def get_library_notes(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/get_library_notes"""
        argd = wash_urlargd(form, {'library_id': (str, None), 'delete_key': (str, None), 'library_notes': (str, None), 'ln': (str, "en")})
        library_id = argd['library_id']
        delete_key = argd['delete_key']
        library_notes = argd['library_notes']
        ln = argd['ln']
        return bal.get_library_notes(req, library_id, delete_key, library_notes, ln)


    def change_due_date_step1(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/change_due_date_step1"""
        argd = wash_urlargd(form, {'loan_id': (str, None), 'borrower_id': (str, None), 'ln': (str, "en")})
        loan_id = argd['loan_id']
        borrower_id = argd['borrower_id']
        ln = argd['ln']
        return bal.change_due_date_step1(req, loan_id, borrower_id, ln)


    def change_due_date_step2(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/change_due_date_step2"""
        argd = wash_urlargd(form, {'new_due_date': (str, None), 'loan_id': (str, None), 'borrower_id': (str, None), 'ln': (str, "en")})
        new_due_date = argd['new_due_date']
        loan_id = argd['loan_id']
        borrower_id = argd['borrower_id']
        ln = argd['ln']
        return bal.change_due_date_step2(req, new_due_date, loan_id, borrower_id, ln)


    def claim_book_return(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/claim_book_return"""
        argd = wash_urlargd(form, {'borrower_id': (str, None), 'recid': (str, None), 'loan_id': (str, None), 'template': (str, None), 'ln': (str, "en")})
        borrower_id = argd['borrower_id']
        recid = argd['recid']
        loan_id = argd['loan_id']
        template = argd['template']
        ln = argd['ln']
        return bal.claim_book_return(req, borrower_id, recid, loan_id, template, ln)


    def all_expired_loans(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/all_expired_loans"""
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']

        return bal.all_expired_loans(req, ln)


    def get_waiting_requests(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/get_waiting_requests"""
        argd = wash_urlargd(form, {'request_id': (str, None), 'print_data': (str, None), 'ln': (str, "en")})
        request_id = argd['request_id']
        print_data = argd['print_data']
        ln = argd['ln']
        return bal.get_waiting_requests(req, request_id, print_data, ln)


    def create_new_loan_step1(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/create_new_loan_step1"""
        argd = wash_urlargd(form, {'borrower_id': (str, None), 'ln': (str, "en")})
        borrower_id = argd['borrower_id']
        ln = argd['ln']
        return bal.create_new_loan_step1(req, borrower_id, ln)


    def create_new_loan_step2(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/create_new_loan_step2"""
        argd = wash_urlargd(form, {'borrower_id': (str, None), 'barcode': (str, None), 'notes': (str, None), 'ln': (str, "en")})
        borrower_id = argd['borrower_id']
        barcode = argd['barcode']
        notes = argd['notes']
        ln = argd['ln']
        return bal.create_new_loan_step2(req, borrower_id, barcode, notes, ln)


    def create_new_request_step1(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/create_new_request_step1"""
        argd = wash_urlargd(form, {'borrower_id': (str, None), 'p': (str, None), 'f': (str, None), 'search': (str, None), 'ln': (str, "en")})
        borrower_id = argd['borrower_id']
        p = argd['p']
        f = argd['f']
        search = argd['search']
        ln = argd['ln']
        return bal.create_new_request_step1(req, borrower_id, p, f, search, ln)


    def create_new_request_step2(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/create_new_request_step2"""
        argd = wash_urlargd(form, {'recid': (str, None), 'borrower_id': (str, None), 'ln': (str, "en")})
        recid = argd['recid']
        borrower_id = argd['borrower_id']
        ln = argd['ln']
        return bal.create_new_request_step2(req, recid, borrower_id, ln)


    def create_new_request_step3(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/create_new_request_step3"""
        argd = wash_urlargd(form, {'borrower_id': (str, None), 'barcode': (str, None), 'recid': (str, None), 'ln': (str, "en")})
        borrower_id = argd['borrower_id']
        barcode = argd['barcode']
        recid = argd['recid']
        ln = argd['ln']
        return bal.create_new_request_step3(req, borrower_id, barcode, recid, ln)


    def create_new_request_step4(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/create_new_request_step4"""
        argd = wash_urlargd(form, {'period_from': (str, None), 'period_to': (str, None), 'barcode': (str, None), 'borrower_id': (str, None), 'recid': (str, None), 'ln': (str, "en")})
        period_from = argd['period_from']
        period_to = argd['period_to']
        barcode = argd['barcode']
        borrower_id = argd['borrower_id']
        recid = argd['recid']
        ln = argd['ln']
        return bal.create_new_request_step4(req, period_from, period_to, barcode,
                                            borrower_id, recid, ln)


    def place_new_request_step1(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/place_new_request_step1"""
        argd = wash_urlargd(form, {'barcode': (str, None), 'recid': (str, None), 'key': (str, None), 'string': (str, None), 'ln': (str, "en")})
        barcode = argd['barcode']
        recid = argd['recid']
        key = argd['key']
        string = argd['string']
        ln = argd['ln']
        return bal.place_new_request_step1(req, barcode, recid, key, string, ln)


    def place_new_request_step2(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/place_new_request_step2"""
        argd = wash_urlargd(form, {'barcode': (str, None), 'recid': (str, None), 'user_info': (str, None), 'ln': (str, "en")})
        barcode = argd['barcode']
        recid = argd['recid']
        user_info = argd['user_info']
        ln = argd['ln']

        if user_info is not None:
            user_info = user_info.split(',')

        return bal.place_new_request_step2(req, barcode, recid, user_info, ln)


    def place_new_request_step3(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/place_new_request_step3"""
        argd = wash_urlargd(form, {'barcode': (str, None), 'recid': (str, None), 'user_info': (str, None), 'period_from': (str, None), 'period_to': (str, None), 'ln': (str, "en")})
        barcode = argd['barcode']
        recid = argd['recid']
        user_info = argd['user_info']
        period_from = argd['period_from']
        period_to = argd['period_to']
        ln = argd['ln']
        user_info = eval(user_info)

        return bal.place_new_request_step3(req, barcode, recid, user_info, period_from,
                                           period_to, ln)


    def place_new_loan_step1(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/place_new_loan_step1"""
        argd = wash_urlargd(form, {'barcode': (str, None), 'recid': (str, None), 'key': (str, None), 'string': (str, None), 'ln': (str, "en")})
        barcode = argd['barcode']
        recid = argd['recid']
        key = argd['key']
        string = argd['string']
        ln = argd['ln']
        return bal.place_new_loan_step1(req, barcode, recid, key, string, ln)


    def place_new_loan_step2(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/place_new_loan_step2"""
        argd = wash_urlargd(form, {'barcode': (str, None), 'recid': (str, None), 'user_info': (str, None), 'ln': (str, "en")})
        barcode = argd['barcode']
        recid = argd['recid']
        user_info = argd['user_info']
        ln = argd['ln']
        return bal.place_new_loan_step2(req, barcode, recid, user_info, ln)


    def place_new_loan_step3(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/place_new_loan_step3"""
        argd = wash_urlargd(form, {'barcode': (str, None), 'recid': (str, None), 'ccid': (str, None), 'name': (str, None), 'email': (str, None), 'phone': (str, None), 'address': (str, None), 'mailbox': (str, None), 'due_date': (str, None), 'notes': (str, None), 'ln': (str, "en")})
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


    def order_new_copy_step1(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/order_new_copy_step1"""
        argd = wash_urlargd(form, {'recid': (str, None), 'ln': (str, "en")})
        recid = argd['recid']
        ln = argd['ln']

        return bal.order_new_copy_step1(req, recid, ln)


    def order_new_copy_step3(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/order_new_copy_step3"""
        argd = wash_urlargd(form, {'order_info': (str, None), 'ln': (str, "en")})
        order_info = argd['order_info']
        ln = argd['ln']

        order_info = eval(order_info)

        return bal.order_new_copy_step3(req, order_info, ln)


    def ordered_books(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/ordered_books"""
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']

        return bal.list_ordered_books(req, ln)


    def get_purchase_notes(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/get_purchase_notes"""
        argd = wash_urlargd(form, {'purchase_id': (str, None), 'delete_key': (str, None), 'library_notes': (str, None), 'ln': (str, "en")})
        purchase_id = argd['purchase_id']
        delete_key = argd['delete_key']
        library_notes = argd['library_notes']
        ln = argd['ln']

        return bal.get_purchase_notes(req, purchase_id, delete_key, library_notes, ln)


    def register_ill_request_step0(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/register_ill_request_step0"""
        argd = wash_urlargd(form, {'recid': (str, None), 'key': (str, None), 'string': (str, None), 'ln': (str, "en")})
        recid = argd['recid']
        key = argd['key']
        string = argd['string']
        ln = argd['ln']
        return bal.register_ill_request_step0(req, recid, key, string, ln)


    def register_ill_request_step1(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/register_ill_request_step1"""
        argd = wash_urlargd(form, {'recid': (str, None), 'user_info': (str, None), 'ln': (str, "en")})
        recid = argd['recid']
        user_info = argd['user_info']
        ln = argd['ln']

        return bal.register_ill_request_step1(req, recid, user_info, ln)


    def register_ill_request_step2(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/register_ill_request_step2"""
        argd = wash_urlargd(form, {'recid': (str, None), 'user_info': (str, None), 'period_of_interest_from': (str, None), 'period_of_interest_to': (str, None), 'notes': (str, None), 'only_edition': (str, None), 'ln': (str, "en")})
        recid = argd['recid']
        user_info = argd['user_info']
        period_of_interest_from = argd['period_of_interest_from']
        period_of_interest_to = argd['period_of_interest_to']
        notes = argd['notes']
        only_edition = argd['only_edition']
        ln = argd['ln']

        return bal.register_ill_request_step2(req, recid, user_info, period_of_interest_from, period_of_interest_to,
                                              notes, only_edition, ln)


    def register_ill_request_step3(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/register_ill_request_step3"""
        argd = wash_urlargd(form, {'borrower_id': (str, None), 'request_info': (str, None), 'ln': (str, "en")})
        borrower_id = argd['borrower_id']
        request_info = argd['request_info']
        ln = argd['ln']

        request_info = eval(request_info)

        return bal.register_ill_request_step3(req, borrower_id, request_info, ln)


    def list_ill_request(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/list_ill_request"""
        argd = wash_urlargd(form, {'status': (str, None), 'ln': (str, "en")})
        status = argd['status']
        ln = argd['ln']

        return bal.list_ill_request(req, status, ln)


    def ill_request_details_step1(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/ill_request_details_step1"""
        argd = wash_urlargd(form, {'delete_key': (str, None), 'ill_request_id': (str, None), 'new_status': (str, None), 'ln': (str, "en")})
        delete_key = argd['delete_key']
        ill_request_id = argd['ill_request_id']
        new_status = argd['new_status']
        ln = argd['ln']

        return bal.ill_request_details_step1(req, delete_key, ill_request_id, new_status, ln)


    def ill_request_details_step2(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/ill_request_details_step2"""
        argd = wash_urlargd(form, {'delete_key': (str, None), 'ill_request_id': (str, None), 'new_status': (str, None), 'library_id': (str, None), 'request_date': (str, None), 'expected_date': (str, None), 'arrival_date': (str, None), 'due_date': (str, None), 'return_date': (str, None), 'cost': (str, None), 'currency': (str, None), 'barcode': (str, None), 'library_notes': (str, None), 'ln': (str, "en")})
        delete_key = argd['delete_key']
        ill_request_id = argd['ill_request_id']
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
        ln = argd['ln']


        return bal.ill_request_details_step2(req, delete_key, ill_request_id, new_status, library_id,
                                             request_date, expected_date, arrival_date, due_date,
                                             return_date, cost, currency,
                                             barcode, library_notes, ln)


    #def ill_request_details_step3(self, req, form):
    #    """http://cdsweb.cern.ch/admin2/bibcirculation/ill_request_details_step3"""
    #    argd = wash_urlargd(form, {'request_info': (str, None), 'ill_status': (str, None), 'ln': (str, "en")})
    #    request_info = argd['request_info']
    #    ill_status = argd['ill_status']
    #    ln = argd['ln']
    #
    #    request_info = eval(request_info)
    #
    #    return bal.ill_request_details_step3(req, request_info, ill_status, ln)


    def ordered_books_details_step1(self, req, form):
        """    """
        argd = wash_urlargd(form, {'purchase_id': (str, None), 'delete_key': (str, None), 'ln': (str, "en")})
        purchase_id = argd['purchase_id']
        delete_key = argd['delete_key']
        ln = argd['ln']

        return bal.ordered_books_details_step1(req, purchase_id, delete_key, ln)


    def ordered_books_details_step2(self, req, form):
        """    """
        argd = wash_urlargd(form, {'purchase_id': (str, None), 'recid': (str, None), 'vendor_id': (str, None), 'cost': (str, None), 'currency': (str, None), 'status': (str, None), 'order_date': (str, None), 'expected_date': (str, None), 'purchase_notes': (str, None), 'library_notes': (str, None), 'ln': (str, "en")})
        purchase_id = argd['purchase_id']
        recid = argd['recid']
        vendor_id = argd['vendor_id']
        cost = argd['cost']
        currency = argd['currency']
        status = argd['status']
        order_date = argd['order_date']
        expected_date = argd['expected_date']
        purchase_notes = argd['purchase_notes']
        library_notes = argd['library_notes']
        ln = argd['ln']

        return bal.ordered_books_details_step2(req, purchase_id, recid, vendor_id,
                                               cost, currency, status, order_date, expected_date,
                                               purchase_notes, library_notes, ln)


    def ordered_books_details_step3(self, req, form):
        """    """
        argd = wash_urlargd(form, {'purchase_id': (str, None), 'recid': (str, None), 'vendor_id': (str, None), 'cost': (str, None), 'currency': (str, None), 'status': (str, None), 'order_date': (str, None), 'expected_date': (str, None), 'purchase_notes': (str, None), 'library_notes': (str, None), 'ln': (str, "en")})
        purchase_id = argd['purchase_id']
        recid = argd['recid']
        vendor_id = argd['vendor_id']
        cost = argd['cost']
        currency = argd['currency']
        status = argd['status']
        order_date = argd['order_date']
        expected_date = argd['expected_date']
        purchase_notes = argd['purchase_notes']
        library_notes = argd['library_notes']
        ln = argd['ln']

        return bal.ordered_books_details_step3(req, purchase_id, recid, vendor_id,
                                               cost, currency, status, order_date, expected_date,
                                               purchase_notes, library_notes, ln)


    def add_new_vendor_step1(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/add_new_vendor_step1"""
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']
        return bal.add_new_vendor_step1(req, ln)


    def add_new_vendor_step2(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/add_new_vendor_step2"""
        argd = wash_urlargd(form, {'name': (str, None), 'email': (str, None), 'phone': (str, None), 'address': (str, None), 'notes': (str, None), 'ln': (str, "en")})
        name = argd['name']
        email = argd['email']
        phone = argd['phone']
        address = argd['address']
        notes = argd['notes']
        ln = argd['ln']
        return bal.add_new_vendor_step2(req, name, email, phone, address,
                                        notes, ln)


    def add_new_vendor_step3(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/add_new_vendor_step3"""
        argd = wash_urlargd(form, {'tup_infos': (str, None), 'ln': (str, "en")})
        tup_infos = argd['tup_infos']
        ln = argd['ln']
        tup_infos = eval(tup_infos)

        return bal.add_new_vendor_step3(req, tup_infos, ln)


    def update_vendor_info_step1(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/update_vendor_info_step1"""
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']
        return bal.update_vendor_info_step1(req, ln)


    def update_vendor_info_step2(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/update_vendor_info_step2"""
        argd = wash_urlargd(form, {'column': (str, None), 'string': (str, None), 'ln': (str, "en")})
        column = argd['column']
        string = argd['string']
        ln = argd['ln']
        return bal.update_vendor_info_step2(req, column, string, ln)


    def update_vendor_info_step3(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/update_vendor_info_step3"""
        argd = wash_urlargd(form, {'vendor_id': (str, None), 'ln': (str, "en")})
        vendor_id = argd['vendor_id']
        ln = argd['ln']
        return bal.update_vendor_info_step3(req, vendor_id, ln)


    def update_vendor_info_step4(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/update_vendor_info_step4"""
        argd = wash_urlargd(form, {'name': (str, None), 'email': (str, None), 'phone': (str, None), 'address': (str, None), 'vendor_id': (str, None), 'ln': (str, "en")})
        name = argd['name']
        email = argd['email']
        phone = argd['phone']
        address = argd['address']
        vendor_id = argd['vendor_id']
        ln = argd['ln']
        return bal.update_vendor_info_step4(req, name, email, phone, address,
                                            vendor_id, ln)


    def update_vendor_info_step5(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/update_vendor_info_step5"""
        argd = wash_urlargd(form, {'tup_infos': (str, '()'), 'ln': (str, "en")})
        tup_infos = argd['tup_infos']
        ln = argd['ln']
        tup_infos = eval(tup_infos)

        return bal.update_vendor_info_step5(req, tup_infos, ln)


    def search_vendor_step1(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/search_vendor_step1"""
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']
        return bal.search_vendor_step1(req, ln)


    def search_vendor_step2(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/search_vendor_step2"""
        argd = wash_urlargd(form, {'column': (str, ''), 'string': (str, ''), 'ln': (str, "en")})
        column = argd['column']
        string = argd['string']
        ln = argd['ln']

        return bal.search_vendor_step2(req, column, string, ln)


    def get_vendor_details(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/get_vendor_details"""
        argd = wash_urlargd(form, {'vendor_id': (str, None), 'ln': (str, "en")})
        vendor_id = argd['vendor_id']
        ln = argd['ln']
        return bal.get_vendor_details(req, vendor_id, ln)


    def get_vendor_notes(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/get_vendor_notes"""
        argd = wash_urlargd(form, {'vendor_id': (str, None), 'add_notes': (str, None), 'new_note': (str, None), 'ln': (str, "en")})
        vendor_id = argd['vendor_id']
        add_notes = argd['add_notes']
        new_note = argd['new_note']
        ln = argd['ln']
        return bal.get_vendor_notes(req, vendor_id, add_notes, new_note, ln)


    def register_ill_request_with_no_recid_step1(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/register_ill_request_with_no_recid_step1"""
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']

        return bal.register_ill_request_with_no_recid_step1(req, ln)


    def register_ill_request_with_no_recid_step2(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/register_ill_request_with_no_recid_step2"""
        argd = wash_urlargd(form, {'title': (str, None), 'authors': (str, None), 'place': (str, None), 'publisher': (str, None), 'year': (str, None), 'edition': (str, None), 'isbn': (str, None), 'period_of_interest_from': (str, None), 'period_of_interest_to': (str, None), 'additional_comments': (str, None), 'only_edition': (str, None), 'key': (str, None), 'string': (str, None), 'ln': (str, "en")})
        title = argd['title']
        authors = argd['authors']
        place = argd['place']
        publisher = argd['publisher']
        year = argd['year']
        edition = argd['edition']
        isbn = argd['isbn']
        period_of_interest_from = argd['period_of_interest_from']
        period_of_interest_to = argd['period_of_interest_to']
        additional_comments = argd['additional_comments']
        only_edition = argd['only_edition']
        key = argd['key']
        string = argd['string']
        ln = argd['ln']

        return bal.register_ill_request_with_no_recid_step2(req, title, authors, place,
                                                            publisher, year, edition, isbn, period_of_interest_from,
                                                            period_of_interest_to, additional_comments,
                                                            only_edition, key, string, ln)


    def register_ill_request_with_no_recid_step3(self, req, form):
        """    """
        argd = wash_urlargd(form, {'book_info': (str, None), 'user_info': (str, None), 'request_details': (str, None), 'ln': (str, "en")})
        book_info = argd['book_info']
        user_info = argd['user_info']
        request_details = argd['request_details']
        ln = argd['ln']

        if type(book_info) is str:
            book_info = eval(book_info)

        if type(request_details) is str:
            request_details = eval(request_details)

        if type(user_info) is str:
            user_info = user_info.split(',')

        return bal.register_ill_request_with_no_recid_step3(req, book_info, user_info, request_details, ln)


    def register_ill_request_with_no_recid_step4(self, req, form):
        """    """
        argd = wash_urlargd(form, {'book_info': (str, None), 'user_info': (str, None), 'request_details': (str, None), 'ln': (str, "en")})
        book_info = argd['book_info']
        user_info = argd['user_info']
        request_details = argd['request_details']
        ln = argd['ln']

        if type(book_info) is str:
            book_info = eval(book_info)

        if type(request_details) is str:
            request_details = eval(request_details)

        if type(user_info) is str:
            user_info = eval(user_info)

        return bal.register_ill_request_with_no_recid_step4(req, book_info, user_info, request_details, ln)


    def get_borrower_ill_details(self, req, form):
        """    """
        argd = wash_urlargd(form, {'borrower_id': (str, None),'ln': (str, "en")})
        borrower_id = argd['borrower_id']
        ln = argd['ln']

        return bal.get_borrower_ill_details(req, borrower_id, ln)


    def bor_ill_historical_overview(self, req, form):
        """    """
        argd = wash_urlargd(form, {'borrower_id': (str, None), 'ln': (str, "en")})
        borrower_id = argd['borrower_id']
        ln = argd['ln']

        return bal.bor_ill_historical_overview(req, borrower_id, ln)


    def get_ill_library_notes(self, req, form):
        """    """
        argd = wash_urlargd(form, {'ill_id': (str, None), 'delete_key': (str, None), 'library_notes': (str, None), 'ln': (str, "en")})
        ill_id = argd['ill_id']
        delete_key = argd['delete_key']
        library_notes = argd['library_notes']
        ln = argd['ln']

        return bal.get_ill_library_notes(req, ill_id, delete_key, library_notes, ln)


    def get_expired_loans_with_requests(self, req, form):
        """    """
        argd = wash_urlargd(form, {'request_id': (str, None), 'ln': (str, "en")})
        request_id = argd['request_id']
        ln = argd['ln']

        return bal.get_expired_loans_with_requests(req, request_id, ln)


    def register_ill_book_request(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/holdings_search"""
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']
        return bal.register_ill_book_request(req, ln)


    def register_ill_book_request_result(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/item_search_result"""
        argd = wash_urlargd(form, {'p': (str, None), 'f': (str, None), 'ln': (str, "en")})
        p = argd['p']
        f = argd['f']
        ln = argd['ln']

        return bal.register_ill_book_request_result(req, p, f, ln)


    def register_ill_book_request_from_borrower_page(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/holdings_search"""
        argd = wash_urlargd(form, {'borrower_id': (str, None), 'ln': (str, "en")})
        borrower_id = argd['borrower_id']
        ln = argd['ln']
        return bal.register_ill_book_request_from_borrower_page(req, borrower_id, ln)


    def register_ill_book_request_from_borrower_page_result(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/item_search_result"""
        argd = wash_urlargd(form, {'borrower_id': (str, None), 'p': (str, None), 'f': (str, None), 'ln': (str, "en")})
        borrower_id = argd['borrower_id']
        p = argd['p']
        f = argd['f']
        ln = argd['ln']

        return bal.register_ill_book_request_from_borrower_page_result(req, borrower_id, p, f, ln)


    def register_ill_request_from_borrower_page_step1(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/register_ill_request_with_no_recid_step1"""
        argd = wash_urlargd(form, {'borrower_id': (str, None), 'ln': (str, "en")})
        borrower_id = argd['borrower_id']
        ln = argd['ln']

        return bal.register_ill_request_from_borrower_page_step1(req, borrower_id, ln)


    def register_ill_request_from_borrower_page_step2(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/register_ill_request_with_no_recid_step2"""
        argd = wash_urlargd(form, {'borrower_id': (str, None), 'title': (str, None), 'authors': (str, None), 'place': (str, None), 'publisher': (str, None), 'year': (str, None), 'edition': (str, None), 'isbn': (str, None), 'period_of_interest_from': (str, None), 'period_of_interest_to': (str, None), 'additional_comments': (str, None), 'only_edition': (str, None), 'ln': (str, "en")})
        borrower_id = argd['borrower_id']
        title = argd['title']
        authors = argd['authors']
        place = argd['place']
        publisher = argd['publisher']
        year = argd['year']
        edition = argd['edition']
        isbn = argd['isbn']
        period_of_interest_from = argd['period_of_interest_from']
        period_of_interest_to = argd['period_of_interest_to']
        additional_comments = argd['additional_comments']
        only_edition = argd['only_edition']
        ln = argd['ln']

        return bal.register_ill_request_from_borrower_page_step2(req, borrower_id, title, authors, place,
                                                                 publisher, year, edition, isbn, period_of_interest_from,
                                                                 period_of_interest_to, additional_comments,
                                                                 only_edition, ln)


    def register_ill_article_request_step1(self, req, form):
        """    """
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']

        return bal.register_ill_article_request_step1(req, ln)


    def register_ill_article_request_step2(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/register_ill_request_with_no_recid_step2"""
        argd = wash_urlargd(form, {'periodical_title': (str, None), 'article_title': (str, None), 'author': (str, None), 'report_number': (str, None), 'volume': (str, None), 'issue': (str, None), 'page': (str, None), 'year': (str, None), 'issn': (str, None), 'period_of_interest_from': (str, None), 'period_of_interest_to': (str, None), 'additional_comments': (str, None), 'key': (str, None), 'string': (str, None), 'ln': (str, "en")})
        periodical_title = argd['periodical_title']
        article_title = argd['article_title']
        author = argd['author']
        report_number = argd['report_number']
        volume = argd['volume']
        issue = argd['issue']
        page = argd['page']
        year = argd['year']
        issn = argd['issn']
        period_of_interest_from = argd['period_of_interest_from']
        period_of_interest_to = argd['period_of_interest_to']
        additional_comments = argd['additional_comments']
        key = argd['key']
        string = argd['string']
        ln = argd['ln']

        return bal.register_ill_article_request_step2(req, periodical_title, article_title, author, report_number,
                                                      volume, issue, page, year, issn,
                                                      period_of_interest_from, period_of_interest_to,
                                                      additional_comments, key, string, ln)


    def register_ill_article_request_step3(self, req, form):
        argd = wash_urlargd(form, {'book_info': (str, '()'), 'user_info': (str, 'new_cpoy'), 'request_details': (str, '()'), 'ln': (str, "en")})
        book_info = argd['book_info']
        user_info = argd['user_info']
        request_details = argd['request_details']
        ln = argd['ln']


        book_info = eval(book_info)

        request_details = eval(request_details)

        user_info = user_info.split(',')

        return bal.register_ill_article_request_step3(req, book_info, user_info, request_details, ln)


    def ill_search(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/holdings_search"""
        argd = wash_urlargd(form, {'ln': (str, "en")})
        ln = argd['ln']
        return bal.ill_search(req, ln)


    def ill_search_result(self, req, form):
        """http://cdsweb.cern.ch/admin2/bibcirculation/item_search_result"""
        argd = wash_urlargd(form, {'p': (str, None), 'f': (str, None), 'date_from': (str, None), 'date_to': (str, None), 'ln': (str, "en")})
        p = argd['p']
        f = argd['f']
        date_from = argd['date_from']
        date_to = argd['date_to']
        ln = argd['ln']

        return bal.ill_search_result(req, p, f, date_from, date_to, ln)

    def __call__(self, req, form):
        """Redirect calls without final slash."""
        redirect_to_url(req, '%s/admin2/bibcirculation/' % CFG_SITE_URL)
