# -*- coding: utf-8 -*-
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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

"""
BibCirculation daemon.
"""

__revision__ = "$Id: bibcirculation_daemon.py"

import sys
from invenio.dbquery import run_sql
from invenio.bibtask import task_init, write_message
from invenio.mailutils import send_email
import invenio.bibcirculation_dblayer as db
from invenio.bibcirculation_config import CFG_BIBCIRCULATION_TEMPLATES
from invenio.search_engine import get_fieldvalues


def get_expired_loan():
    """
    @return all expired loans
    """

    res = run_sql("""select id_crcBORROWER, id, id_bibrec
                     from crcLOAN
                     where status = 'on loan' and due_date < NOW()
                     """)
    return res

def update_expired_loan(id):
    """
    Update status, number of overdue letter and date of overdue letter
    @param id: id of crcLOAN
    """

    run_sql("""update crcLOAN
               set    overdue_letter_number = overdue_letter_number + 1,
                      status = 'expired',
                      overdue_letter_date = NOW()
               where id = %s
               """, (id, ))


def send_overdue_letter(borrower_id, subject):
    """
    send an overdue letter
    @param borrower_id: id of crcBORROWER
    @param subject: subject of the overdue letter
    """

    to_borrower = db.get_borrower_email(borrower_id)

    send_email(fromaddr="library.desk@cern.ch",
               toaddr=to_borrower,
               subject=subject,
               content=CFG_BIBCIRCULATION_TEMPLATES['OVERDUE'],
               header='',
               footer='',
               attempt_times=1,
               attempt_sleeptime=10
               )
    return 1

def task_run_core():
    """
    run daemon
    """

    write_message("Getting expired loans ...", verbose=9)
    expired_loans = get_expired_loan()

    for (borrower_id, id_loan, recid) in expired_loans:
        title = ''.join(get_fieldvalues(recid, "245__a"))
        subject = "OVERDUE LETTER - " + title
        update_expired_loan(id_loan)
        write_message("Updating information about expired loans")
        send_overdue_letter(borrower_id, subject)
        write_message("Sending overdue letter")

    write_message("Done!!")

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


