# -*- coding: utf-8 -*-
#
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

"""
BibCirculation daemon.
"""

__revision__ = "$Id$"

import sys
import time
from invenio.legacy.dbquery import run_sql
from invenio.legacy.bibsched.bibtask import task_init, \
                            task_sleep_now_if_required, \
                            task_update_progress, \
                            task_set_option, \
                            task_get_option, \
                            write_message
from invenio.ext.email import send_email
import invenio.legacy.bibcirculation.db_layer as db
from invenio.legacy.bibcirculation.config import CFG_BIBCIRCULATION_TEMPLATES, \
                                          CFG_BIBCIRCULATION_LOANS_EMAIL, \
                                          CFG_BIBCIRCULATION_ILLS_EMAIL, \
                                          CFG_BIBCIRCULATION_REQUEST_STATUS_WAITING, \
                                          CFG_BIBCIRCULATION_LOAN_STATUS_EXPIRED

from invenio.legacy.bibcirculation.utils import generate_email_body, \
                                         book_title_from_MARC, \
                                         update_user_info_from_ldap, \
                                         update_requests_statuses, \
                                         looks_like_dictionary
import datetime

def task_submit_elaborate_specific_parameter(key, value, opts, args):
    """ Given the string key, checks its meaning and returns True if
        has elaborated the key.
        Possible keys:
    """
    write_message(key)
    if key in ('-o', '--overdue-letters'):
        task_set_option('overdue-letters', True)
    elif key in ('-b', '--update-borrowers'):
        task_set_option('update-borrowers', True)
    elif key in ('-r', '--update-requests'):
        task_set_option('update-requests', True)
    else:
        return False
    return True

def update_expired_loan(loan_id, ill=0):
    """
    Update status, number of overdue letters and the date of overdue letter

    @param loan_id: identify the loan. Primary key of crcLOAN.
    @type loan_id: int
    """

    if ill:
        run_sql("""update crcILLREQUEST
                  set overdue_letter_number=overdue_letter_number+1,
                       overdue_letter_date=NOW()
                where id=%s
               """, (loan_id,))
    else:
        run_sql("""update crcLOAN
                  set overdue_letter_number=overdue_letter_number+1,
                       status=%s,
                       overdue_letter_date=NOW()
                where id=%s
               """, (CFG_BIBCIRCULATION_LOAN_STATUS_EXPIRED,
                     loan_id))

def send_overdue_letter(borrower_id, from_address, subject, content):
    """
    Send an overdue letter

    @param borrower_id: identify the borrower. Primary key of crcBORROWER.
    @type borrower_id: int

    @param subject: subject of the overdue letter
    @type subject: string
    """

    to_borrower = db.get_borrower_email(borrower_id)

    send_email(fromaddr=from_address,
               toaddr=to_borrower,
               subject=subject,
               content=content,
               header='',
               footer='',
               attempt_times=1,
               attempt_sleeptime=10
               )
    return 1

def must_send_second_recall(date_letters):
    """
    @param date_letters: date of the last letter.
    @type date_letters: string

    @return boolean
    """
    today = datetime.date.today()

    time_tuple = time.strptime(date_letters, "%Y-%m-%d")
    #datetime.strptime(date_letters, "%Y-%m-%d") doesn't work (only on 2.5).
    tmp_date = datetime.datetime(*time_tuple[0:3]) + datetime.timedelta(weeks=1)

    try:
        if tmp_date.strftime("%Y-%m-%d") <= today.strftime("%Y-%m-%d"):
            return True
        else:
            return False
    except ValueError:
        return False

def must_send_third_recall(date_letters):
    """
    @param date_letters: date of the last letter.
    @type date_letters: string

    @return boolean
    """
    today = datetime.date.today()

    time_tuple = time.strptime(date_letters, "%Y-%m-%d")
    #datetime.strptime(date_letters, "%Y-%m-%d") doesn't work (only on Python 2.5)
    tmp_date = datetime.datetime(*time_tuple[0:3]) + datetime.timedelta(days=3)

    try:
        if tmp_date.strftime("%Y-%m-%d") <= today.strftime("%Y-%m-%d"):
            return True
        else:
            return False
    except ValueError:
        return False

def task_run_core():
    """
    Run daemon
    """
    write_message("Starting...")
    if task_get_option("update-borrowers"):
        write_message("Started update-borrowers")
        list_of_borrowers = db.get_all_borrowers()
        total_borrowers = len(list_of_borrowers)

        for done, borrower in enumerate(list_of_borrowers):
            user_id = borrower[0]
            update_user_info_from_ldap(user_id)
            if done % 10 == 0:
                task_update_progress("Borrower: updated %d out of %d." % (done, total_borrowers))
                task_sleep_now_if_required(can_stop_too=True)
        task_update_progress("Borrower: updated %d out of %d." % (done+1, total_borrowers))
        write_message("Updated %d out of %d total borrowers" % (done+1, total_borrowers))

    if task_get_option("update-requests"):
        write_message("Started update-requests")
        list_of_reqs = db.get_loan_request_by_status(CFG_BIBCIRCULATION_REQUEST_STATUS_WAITING)

        for (_request_id, recid, bc, _name, borrower_id, _library, _location,
             _date_from, _date_to, _request_date) in list_of_reqs:
            description = db.get_item_description(bc)
            list_of_barcodes = db.get_barcodes(recid, description)
            for barcode in list_of_barcodes:
                update_requests_statuses(barcode)
                task_sleep_now_if_required(can_stop_too=True)
        task_update_progress("Requests due updated from 'waiting' to 'pending'.")
        write_message("Requests due updated from 'waiting' to 'pending'.")

    if task_get_option("overdue-letters"):
        write_message("Started overdue-letters")
        expired_loans = db.get_all_expired_loans()
        total_expired_loans = len(expired_loans)

        for done, (borrower_id, _bor_name, recid, _barcode, _loaned_on,
             _due_date, _number_of_renewals, number_of_letters,
             date_letters, _notes, loan_id) in enumerate(expired_loans):

            number_of_letters=int(number_of_letters)

            content = ''
            if number_of_letters == 0:
                content = generate_email_body(CFG_BIBCIRCULATION_TEMPLATES['RECALL1'], loan_id)
            elif number_of_letters == 1 and must_send_second_recall(date_letters):
                content = generate_email_body(CFG_BIBCIRCULATION_TEMPLATES['RECALL2'], loan_id)
            elif number_of_letters == 2 and must_send_third_recall(date_letters):
                content = generate_email_body(CFG_BIBCIRCULATION_TEMPLATES['RECALL3'], loan_id)
            elif number_of_letters >= 3 and must_send_third_recall(date_letters):
                content = generate_email_body(CFG_BIBCIRCULATION_TEMPLATES['RECALL3'], loan_id)

            if content != '':
                title = book_title_from_MARC(recid)
                subject = "LOAN RECALL: " + title

                update_expired_loan(loan_id)
                send_overdue_letter(borrower_id, CFG_BIBCIRCULATION_LOANS_EMAIL, subject, content)

            if done % 10 == 0:
                task_update_progress("Loan recall: sent %d out of %d." % (done, total_expired_loans))
                task_sleep_now_if_required(can_stop_too=True)
        task_update_progress("Loan recall: processed %d out of %d expires loans." % (done+1, total_expired_loans))
        write_message("Processed %d out of %d expired loans." % (done+1, total_expired_loans))

        # Recalls for expired ILLs
        write_message("Started overdue-letters for Inter Library Loans")
        expired_ills = db.get_all_expired_ills()
        total_expired_ills = len(expired_ills)

        for done, (ill_id, borrower_id, item_info, number_of_letters,
             date_letters) in enumerate(expired_ills):

            number_of_letters=int(number_of_letters)

            content = ''
            if number_of_letters == 0:
                content = generate_email_body(CFG_BIBCIRCULATION_TEMPLATES['ILL_RECALL1'], ill_id, ill=1)
            elif number_of_letters == 1 and must_send_second_recall(date_letters):
                content = generate_email_body(CFG_BIBCIRCULATION_TEMPLATES['ILL_RECALL2'], ill_id, ill=1)
            elif number_of_letters == 2 and must_send_third_recall(date_letters):
                content = generate_email_body(CFG_BIBCIRCULATION_TEMPLATES['ILL_RECALL3'], ill_id, ill=1)
            elif number_of_letters >= 3 and must_send_third_recall(date_letters):
                content = generate_email_body(CFG_BIBCIRCULATION_TEMPLATES['ILL_RECALL3'], ill_id, ill=1)

            if content != '' and looks_like_dictionary(item_info):
                item_info = eval(item_info)
                if 'title' in item_info:
                    book_title = item_info['title']
                    subject = "ILL RECALL: " + str(book_title)
                    update_expired_loan(loan_id=ill_id, ill=1)
                    send_overdue_letter(borrower_id, CFG_BIBCIRCULATION_ILLS_EMAIL, subject, content)
            if done % 10 == 0:
                task_update_progress("ILL recall: sent %d out of %d." % (done, total_expired_ills))
                task_sleep_now_if_required(can_stop_too=True)
        task_update_progress("ILL recall: processed %d out of %d expired ills." % (done+1, total_expired_ills))
        write_message("Processed %d out of %d expired ills." % (done+1, total_expired_ills))

    return 1

def main():

    task_init(authorization_action='runbibcircd',
              authorization_msg="BibCirculation Task Submission",
              help_specific_usage="""-o,  --overdue-letters\tCheck overdue loans and send recall emails if necessary.\n
-b,  --update-borrowers\tUpdate borrowers information from ldap.\n
-r,  --update-requests\tUpdate pending requests of users\n\n""",
              description="""Example: %s -u admin \n\n""" % (sys.argv[0]),
              specific_params=("obr", ["overdue-letters", "update-borrowers", "update-requests"]),
              task_submit_elaborate_specific_parameter_fnc=task_submit_elaborate_specific_parameter,
              version=__revision__,
              task_run_fnc = task_run_core
              )

if __name__ == '__main__':
    main()
