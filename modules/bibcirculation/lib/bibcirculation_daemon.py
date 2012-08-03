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

"""
BibCirculation daemon.
"""

__revision__ = "$Id$"

import sys
import time
from invenio.dbquery import run_sql
from invenio.bibtask import task_init
from invenio.mailutils import send_email
import invenio.bibcirculation_dblayer as db
from invenio.bibcirculation_config import CFG_BIBCIRCULATION_TEMPLATES, \
     CFG_BIBCIRCULATION_LIBRARIAN_EMAIL
from invenio.search_engine_utils import get_fieldvalues
from invenio.bibcirculation_utils import generate_email_body
import datetime


def get_expired_loan():
    """
    @return all expired loans
    """

    res = run_sql("""select id_crcBORROWER, id, id_bibrec
                     from crcLOAN
                     where status = 'on loan' and due_date < NOW()
                     """)
    return res

def update_expired_loan(loan_id):
    """
    Update status, number of overdue letter and date of overdue letter

    @param loan_id: identify the loan. Primary key of crcLOAN.
    @type loan_id: int
    """

    run_sql("""update crcLOAN
               set    overdue_letter_number = overdue_letter_number + 1,
                      status = 'expired',
                      overdue_letter_date = NOW()
               where id = %s
               """, (loan_id, ))

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

    send_email(fromaddr=CFG_BIBCIRCULATION_LIBRARIAN_EMAIL,
               toaddr=to_borrower,
               subject=subject,
               content=content,
               header='',
               footer='',
               attempt_times=1,
               attempt_sleeptime=10
               )
    return 1

def send_second_recall(date_letters):
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
        if tmp_date.strftime("%Y-%m-%d") == today.strftime("%Y-%m-%d"):
            return True
        else:
            return False
    except ValueError:
        return False

def send_third_recall(date_letters):
    """
    @param date_letters: date of the last letter.
    @type date_letters: string

    @return boolean
    """
    today = datetime.date.today()

    time_tuple = time.strptime(date_letters, "%Y-%m-%d")
    #datetime.strptime(date_letters, "%Y-%m-%d") doesn't work (only on 2.5).
    tmp_date = datetime.datetime(*time_tuple[0:3]) + datetime.timedelta(days=3)

    try:
        if tmp_date.strftime("%Y-%m-%d") == today.strftime("%Y-%m-%d"):
            return True
        else:
            return False
    except ValueError:
        return False

def task_run_core():
    """
    run daemon
    """

    #write_message("Getting expired loans ...", verbose=9)
    expired_loans = get_expired_loan()

    for (borrower_id, loan_id, recid) in expired_loans:
        (number_of_letters, date_letters) = get_overdue_letters_info(loan_id)

        if number_of_letters == 0:
            content = generate_email_body(CFG_BIBCIRCULATION_TEMPLATES['RECALL1'], loan_id)
        elif number_of_letters == 1 and send_second_recall(date_letters):
            content = generate_email_body(CFG_BIBCIRCULATION_TEMPLATES['RECALL2'], loan_id)
        elif number_of_letters == 2 and send_third_recall(date_letters):
            content = generate_email_body(CFG_BIBCIRCULATION_TEMPLATES['RECALL3'], loan_id)
        else:
            content = generate_email_body(CFG_BIBCIRCULATION_TEMPLATES['RECALL3'], loan_id)

        title = ''.join(get_fieldvalues(recid, "245__a"))
        subject = "LOAN RECALL: " + title
        update_expired_loan(loan_id)
        #write_message("Updating information about expired loans")
        send_overdue_letter(borrower_id, subject, content)
        #write_message("Sending overdue letter")

    #write_message("Done!!")

    return 1

def main():
    """
    main()
    """
    task_init(authorization_action='runbibcirculation',
              authorization_msg="BibCirculation Task Submission",
              description="""Examples:
              %s -u admin
              """ % (sys.argv[0],),
              version=__revision__,
              task_run_fnc = task_run_core)

if __name__ == '__main__':
    main()
