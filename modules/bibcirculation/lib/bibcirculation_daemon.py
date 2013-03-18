# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2008, 2009, 2010, 2011, 2013 CERN.
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

"""
BibCirculation daemon.
"""

__revision__ = "$Id$"

import sys
import time
from invenio.dbquery import run_sql
from invenio.bibtask import task_init, \
                            task_sleep_now_if_required, \
                            task_update_progress, \
                            task_set_option, \
                            task_get_option
from invenio.mailutils import send_email
import invenio.bibcirculation_dblayer as db
from invenio.bibcirculation_config import CFG_BIBCIRCULATION_TEMPLATES, \
                                          CFG_BIBCIRCULATION_LOANS_EMAIL, \
                                          CFG_BIBCIRCULATION_LOAN_STATUS_ON_LOAN,\
                                          CFG_BIBCIRCULATION_LOAN_STATUS_EXPIRED

from invenio.bibcirculation_utils import generate_email_body, \
                                         book_title_from_MARC, \
                                         update_user_info_from_ldap
import datetime

def task_submit_elaborate_specific_parameter(key, value, opts, args):
    """ Given the string key, checks its meaning and returns True if
        has elaborated the key.
        Possible keys:
    """
    if key in ('-o', '--overdue-letters'):
        task_set_option('overdue-letters', True)
    elif key in ('-b', '--update-borrowers'):
        task_set_option('update-borrowers', True)
    else:
        return False
    return True

def get_expired_loan():
    """
    @return all expired loans
    """

    res = run_sql("""select id_crcBORROWER, id, id_bibrec
                       from crcLOAN
                      where (status=%s and due_date<NOW())
                         or (status=%s)
                """, (CFG_BIBCIRCULATION_LOAN_STATUS_ON_LOAN,
                       CFG_BIBCIRCULATION_LOAN_STATUS_EXPIRED))
    return res

def update_expired_loan(loan_id):
    """
    Update status, number of overdue letter and date of overdue letter

    @param loan_id: identify the loan. Primary key of crcLOAN.
    @type loan_id: int
    """

    run_sql("""update crcLOAN
                  set overdue_letter_number=overdue_letter_number+1,
                       status=%s,
                       overdue_letter_date=NOW()
                where id=%s
               """, (CFG_BIBCIRCULATION_LOAN_STATUS_EXPIRED,
                     loan_id))

def get_overdue_letters_info(loan_id):
    """
    Get the number of letters and the date of the last letter
    sent for a given loan_id.

    @param loan_id: identify the loan. Primary of crcLOAN.
    @type loan_id: int

    @return number_of_letters and date of the last letter
    """

    res = run_sql("""select overdue_letter_number,
                            DATE_FORMAT(overdue_letter_date,'%%Y-%%m-%%d')
                       from crcLOAN
                      where id=%s""",
                  (loan_id, ))

    return res[0]



def send_overdue_letter(borrower_id, subject, content):
    """
    Send an overdue letter

    @param borrower_id: identify the borrower. Primary key of crcBORROWER.
    @type borrower_id: int

    @param subject: subject of the overdue letter
    @type subject: string
    """

    to_borrower = db.get_borrower_email(borrower_id)

    send_email(fromaddr=CFG_BIBCIRCULATION_LOANS_EMAIL,
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

def update_borrowers_information():
    list_of_borrowers = db.get_all_borrowers()

    for borrower in list_of_borrowers:
        user_id = borrower[0]
        update_user_info_from_ldap(user_id)


def task_run_core():
    """
    run daemon
    """

    if task_get_option("update-borrowers"):
        list_of_borrowers = db.get_all_borrowers()

        total_borrowers = len(list_of_borrowers)

        for done, borrower in enumerate(list_of_borrowers):
            user_id = borrower[0]
            update_user_info_from_ldap(user_id)
            if done % 10 == 0:
                task_update_progress("Borrower: updated %d out of %d." % (done, total_borrowers))
                task_sleep_now_if_required(can_stop_too=True)

    if task_get_option("overdue-letters"):
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
                send_overdue_letter(borrower_id, subject, content)

            if done % 10 == 0:
                task_update_progress("Recall: sent %d out of %d." % (done, total_expired_loans))
                task_sleep_now_if_required(can_stop_too=True)

    return 1

def main():
    """
    main()
    """
    task_init(authorization_action='runbibcircd',
              authorization_msg="BibCirculation Task Submission",
              help_specific_usage="""-o,  --overdue-letters\tCheck overdue loans and send recall emails if necessary.\n-b,  --update-borrowers\tUpdate borrowers information from ldap.\n""",
              description="""Examples:
              %s -u admin
              """ % (sys.argv[0]),
              specific_params=("ob", ["overdue-letters", "update-borrowers"]),
                task_submit_elaborate_specific_parameter_fnc=task_submit_elaborate_specific_parameter,
                version=__revision__,
                task_run_fnc = task_run_core)

if __name__ == '__main__':
    main()
