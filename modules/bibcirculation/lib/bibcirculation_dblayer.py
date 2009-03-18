# -*- coding: utf-8 -*-
##
## $Id: bibcirculation_dblayer.py,v 1.3 2008/08/20 16:23:41 joaquim Exp $
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

"""Every db-related function of module bibcirculation"""

__revision__ = "$Id: bibcirculation_dblayer.py,v 1.3 2008/08/20 16:23:41 joaquim Exp $"

from invenio.dbquery import run_sql


def verify_office_reference(uid):
    """
    Verify is there a reference for user's office
    @param uid: user ID
    """

    query = """SELECT office
               FROM   crcborrower
               WHERE  id=%(user_id)i
            """

    uid = int(uid)

    res = run_sql(query%uid)

    return res

def get_holdings_info(recid):
    """
    Get information about holding, using recid.
    recid: CDS Invenio record identifier.
    """
    res = run_sql("""
                  select count(lr.id_bibrec),
                         it.loan_period,
                         DATE_FORMAT(max(lr.period_of_interest_to),'%%Y-%%m-%%d'),
                         lib.name
                  from crcLOANREQUEST lr, crcITEM it, crcLIBRARY lib
                  where lib.id = it.id_crcLIBRARY and
                        lr.id_bibrec=it.id_bibrec and
                        it.id_bibrec=%s and
                        lr.status = 'waiting' GROUP BY (lr.id_bibrec)
                  """, (recid, ))
    return res


def get_holdings_information(recid):
    """
    """

    res = run_sql("""select it.barcode,
                            lib.name,
                            it.collection,
                            it.location,
                            it.description,
                            it.loan_period,
                            it.status,
                            DATE_FORMAT(ln.due_date, '%%Y-%%m-%%d')
                       from crcITEM it
                            left join crcLOAN ln
                            on it.barcode = ln.barcode and ln.status != 'returned'
                            left join crcLIBRARY lib
                            on lib.id = it.id_crcLIBRARY
                     where it.id_bibrec=%s""",
                  (recid, ))

    return res

def get_holdings_details(recid):
    """
    Get details about holdings (loan period, location and library).
    recid: CDS Invenio record identifier.
    """

    res = run_sql(""" select it.loan_period, lib.name, it.location
                      from crcITEM it, crcLIBRARY lib
                      where id_bibrec=%s limit 1""",
                  (recid, ))

    return res

def get_loan_details(recid):
    """
    Get details about loans (barcode and status).
    recid: CDS Invenio record identifier
    """

    res = run_sql("""select barcode, status
                     from crcITEM
                     where id_bibrec=%s and status = "available" limit 1;
                  """, (recid, ))


    return res

def get_due_date_loan(recid):
    """
    Get the due date of a loan.
    recid: CDS Invenio record identifier.
    """

    res = run_sql("""select DATE_FORMAT(max(due_date),'%%Y-%%m-%%d')
                     from crcLOAN
                     where id_bibrec=%s and status != 'returned'
                  """, (recid, ))

    return res [0][0]


def get_holdings_info_no_requests(recid):
    """
    recid: CDS Invenio record identifier
    """

    res = run_sql(""" select it.loan_period, lib.name
                      from crcITEM it, crcLIBRARY lib
                      where it.id_crcLIBRARY=lib.id and it.id_bibrec=%s
                      """, (recid, ))

    return res

def get_recid_from_crcLOANREQUEST(loan_request_id):
    """
    @param loan_request_id: primary key of crcLOANREQUEST
    """

    res = run_sql(""" select id_bibrec
                      from crcLOANREQUEST
                      where id=%s
                  """, (loan_request_id, ))

    return res[0][0]

def get_borrower_id_from_crcLOANREQUEST(loan_request_id):
    """
    @param loan_request_id: primary key of crcLOANREQUEST
    """

    res = run_sql(""" select id_crcBORROWER
                      from crcLOANREQUEST
                      where id=%s
                  """, (loan_request_id, ))

    return res[0][0]


def get_barcode_from_crcLOANREQUEST(loan_request_id):
    """
    @param loan_request_id: primary key of crcLOANREQUEST
    """

    res = run_sql(""" select barcode
                      from crcLOANREQUEST
                      where id=%s
                  """, (loan_request_id, ))

    return res[0][0]

def get_request_date_to_from_crcLOANREQUEST(loan_request_id):
    """
    @param loan_request_id: primary key of crcLOANREQUEST
    """

    res = run_sql(""" select period_of_interest_to
                      from crcLOANREQUEST
                      where id=%s
                  """, (loan_request_id, ))

    return res[0][0]

def get_id_bibrec(barcode):
    """
    @param barcode: primary key of crcITEM
    """

    res = run_sql("""select id_bibrec
                     from crcITEM
                     where barcode=%s""",
                  (barcode, ))

    try:
        return res[0][0]
    except IndexError:
        return None

def update_item_status(status, barcode):
    """
    @param status: new item's status
    @param barcode: primary key of crcITEM
    """
    if status == 'on loan':
        return int(run_sql("""UPDATE  crcITEM
                             SET  status=%s,
                                  number_of_requests = number_of_requests + 1
                           WHERE  barcode=%s""",
                       (status, barcode)))
    else:
        return int(run_sql("""UPDATE  crcITEM
                             SET  status=%s
                           WHERE  barcode=%s""",
                           (status, barcode)))


def new_hold_request(borrower_id, recid, barcode, date_from, date_to, status):
    """
    @param uid: user ID
    @param recid: recID - CDS Invenio record identifier
    @param barcode: primary key of crcITEM
    """
    res = run_sql("""INSERT INTO crcLOANREQUEST(id_crcBORROWER,
                                                id_bibrec,
                                                barcode,
                                                period_of_interest_from,
                                                period_of_interest_to,
                                                status,
                                                request_date)
                                                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                                                """, (borrower_id, recid, barcode,
                                                      date_from, date_to,
                                                      status))

    return res

def get_barcode(recid):
    """
    @param recid: recID - CDS Invenio record identifier
    """

    res = run_sql("""select barcode
                     from crcITEM
                     where id_bibrec=%s
                  """, (recid, ))

    return res [0][0]

def get_due_date(barcode):
    """
    @param barcode: primary key of crcITEM
    """

    res = run_sql("""select period_of_interest_to
                     from crcLOANREQUEST
                     where barcode=%s
                  """, (barcode, ))

    return res [0][0]

def get_number_requests(recid):
    """
    @param recid: recID - CDS Invenio record identifier
    """
    res =  run_sql("""
                      select id_bibrec
                      from crcLOANREQUEST
                      where id_bibrec=%s and status != 'done' and status != 'cancelled';
                   """, (recid, ))

    return res

def get_number_requests2(barcode, checkid):
    """
    @param barcode: primary key of crcITEM
    @param checkid: id of crcLOANREQUEST
    """

    res =  run_sql("""select id_bibrec
                      from crcLOANREQUEST
                      where id < %s and barcode=%s and status != 'done'
                   """, (checkid, barcode))

    return res


def loan_return_confirm(uid, recid):
    """
    @param uid: user ID
    @param recid: recID - CDS Invenio record identifier
    """
    res = run_sql("""select bor.name, it.id_bibrec
                     from crcBORROWER bor, crcITEM it
                     where bor.id=%s and it.id_bibrec=%s
                     """, (uid, recid))

    return res

def get_borrower_id(barcode):
    """
    @param barcode: primary key of crcITEM
    """

    res = run_sql(""" select id_crcBORROWER
                      from crcLOAN
                      where barcode=%s and status='on loan'""",
                  (barcode, ))
    try:
        return res[0][0]
    except IndexError:
        return None

def get_borrower_email(uid):
    """
    @param uid: user ID
    """

    res = run_sql("""select email
                     from crcBORROWER
                     where id=%s""", (uid, ))

    return res[0][0]

def get_next_waiting_loan_request(recid):
    """
    @param recid: recID - CDS Invenio record identifier
    """
    res = run_sql("""SELECT lr.id,
                            bor.name,
                            lr.id_bibrec,
                            lr.status,
                            DATE_FORMAT(lr.period_of_interest_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.period_of_interest_to,'%%Y-%%m-%%d'),
                            lr.request_date
                     FROM   crcLOANREQUEST lr,
                            crcBORROWER bor
                     WHERE  lr.id_crcBORROWER=bor.id AND
                            (lr.status='waiting' OR lr.status='pending') AND lr.id_bibrec=%s
                            ORDER BY lr.request_date""",
                  (recid, ))

    return res

def update_loan_info(returned_on, status, barcode):
    """
    @param barcode: primary key of crcITEM
    """


    return int(run_sql("""update crcLOAN
                          set returned_on=%s, status=%s
                          where barcode=%s
                      """, (returned_on, status, barcode)))



def get_item_addicional_details(recid):
    """
    @param recid: recID - CDS Invenio record identifier
    """
    res = run_sql("""select it.barcode, it.loan_period, lib.name,
                            lib.id, it.location, it.number_of_requests,
                            it.status, it.collection, it.description
                     from crcITEM it, crcLIBRARY lib
                     where it.id_bibrec=%s and it.id_crcLIBRARY = lib.id
                     order by it.creation_date
                  """, (recid, ))

    return res

def get_number_copies(recid):
    """
    @param recid: recID - CDS Invenio record identifier
    """

    res = run_sql("""select count(barcode)
                     from crcITEM
                     where id_bibrec=%s
                  """, (recid, ))

    return res[0][0]


def bor_loans_historical_overview(borrower_id):
    """
    """
    res = run_sql("""
                     select l.id_bibrec,
                            l.barcode,
                            DATE_FORMAT(l.loaned_on,'%%Y-%%m-%%d'),
                            DATE_FORMAT(l.due_date,'%%Y-%%m-%%d'),
                            l.returned_on,
                            l.number_of_renewals,
                            l.overdue_letter_number
                     from crcLOAN l
                     where l.id_crcBORROWER=%s and l.status = 'returned' """,
                   (borrower_id, ))
    return res

def bor_requests_historical_overview(borrower_id):
    """
    """

    res = run_sql("""select lr.id_bibrec,
                            lr.barcode,
                            DATE_FORMAT(lr.period_of_interest_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.period_of_interest_to,'%%Y-%%m-%%d'),
                            lr.request_date
                     from crcLOANREQUEST lr
                     where lr.id_crcBORROWER=%s and lr.status ='done' """
                  , (borrower_id, ))
    return res

def item_loans_historical_overview(recid):
    """
    """
    res = run_sql("""select bor.name,
                            bor.id,
                            l.barcode,
                            DATE_FORMAT(l.loaned_on,'%%Y-%%m-%%d'),
                            DATE_FORMAT(l.due_date,'%%Y-%%m-%%d'),
                            l.returned_on,
                            l.number_of_renewals,
                            l.overdue_letter_number
                     from crcLOAN l, crcBORROWER bor
                     where l.id_crcBORROWER=bor.id and l.id_bibrec = %s
                           and l.status = 'returned' """
                  , (recid, ))

    return res


def item_requests_historical_overview(recid):
    """
    """

    res = run_sql("""
                  select bor.name,
                         bor.id,
                         lr.barcode,
                         DATE_FORMAT(lr.period_of_interest_from,'%%Y-%%m-%%d'),
                         DATE_FORMAT(lr.period_of_interest_to,'%%Y-%%m-%%d'),
                         lr.request_date
                  from crcLOANREQUEST lr, crcBORROWER bor
                  where lr.id_crcBORROWER=bor.id and lr.id_bibrec = %s
                                                 and status = 'done'
                  """, (recid, ))

    return res


def get_library_details(library_id):
    """
    @param libid: primary key of crcLIBRARY
    """

    res = run_sql("""select id, name, address, email, phone, notes
                     from crcLIBRARY
                     where id=%s;
                     """, (library_id, ))

    return res

def get_pending_loan_request(status):
    """
    @param status: status=pending
    """
    res = run_sql("""SELECT DISTINCT
                            lr.id,
                            lr.id_bibrec,
                            bor.name,
                            bor.id,
                            lib.name,
                            it.location,
                            DATE_FORMAT(lr.period_of_interest_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.period_of_interest_to,'%%Y-%%m-%%d'),
                            lr.request_date
                            FROM   crcLOANREQUEST lr,
                            crcBORROWER bor,
                            crcITEM it,
                            crcLIBRARY lib
                     WHERE  lr.id_crcBORROWER=bor.id AND it.barcode=lr.barcode AND
                            lib.id = it.id_crcLIBRARY AND lr.status=%s
                            ORDER BY lr.request_date;
                  """ ,
                     (status, ))
    return res

def get_pending_loan_request_on_loan(status):
    """
    @param status: status=pending
    """
    res = run_sql("""SELECT lr.id,
                            lr.id_bibrec,
                            bor.name,
                            bor.id,
                            it.location,
                            DATE_FORMAT(lr.period_of_interest_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.period_of_interest_to,'%%Y-%%m-%%d')
                     FROM   crcLOANREQUEST lr,
                            crcBORROWER bor,
			    crcITEM it
                     WHERE  lr.id_crcBORROWER=bor.id AND it.id_bibrec=lr.id_bibrec AND
                            lr.status=%s AND lr.barcode='' """,
                     (status, ))
    return res

def get_pending_loan_request_available(status):
    """
    @param status: status=pending
    """
    res = run_sql("""SELECT lr.id,
                            lr.id_bibrec,
                            bor.name,
                            bor.id,
                            it.location,
                            DATE_FORMAT(lr.period_of_interest_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.period_of_interest_to,'%%Y-%%m-%%d')
                     FROM   crcLOANREQUEST lr,
                            crcBORROWER bor,
			    crcITEM it
                     WHERE  lr.id_crcBORROWER=bor.id AND it.id_bibrec=lr.id_bibrec AND
                            lr.status=%s AND lr.barcode!='' """,
                     (status, ))
    return res


def update_loan_request_status(request_id, status):
    """
    @param request_id: primary key of crcLOANREQUEST
    @param status: new status
    """

    return int(run_sql("""UPDATE  crcLOANREQUEST
                             SET  status=%s
                           WHERE  id=%s""",
                       (status, request_id)))



def get_all_requests():
    """
    """
    res = run_sql("""SELECT lr.id,
                            bor.id,
                            bor.name,
                            lr.id_bibrec,
                            lr.status,
                            DATE_FORMAT(lr.period_of_interest_from,'%Y-%m-%d'),
                            DATE_FORMAT(lr.period_of_interest_to,'%Y-%m-%d'),
                            lr.request_date
                     FROM   crcLOANREQUEST lr,
                            crcBORROWER bor
                     WHERE  bor.id = lr.id_crcBORROWER and (lr.status='waiting' or lr.status='pending') ORDER BY lr.request_date
                            """)

    return res



def get_all_requests_for_item(recid):
    """
    @param recid: recID - CDS Invenio record identifier
    """
    res = run_sql("""SELECT bor.id,
                            bor.name,
                            lr.id_bibrec,
                            lr.status,
                            DATE_FORMAT(lr.period_of_interest_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.period_of_interest_to,'%%Y-%%m-%%d'),
                            lr.id,
                            lr.request_date
                     FROM   crcLOANREQUEST lr,
                            crcBORROWER bor
                     WHERE  bor.id = lr.id_crcBORROWER and lr.id_bibrec=%s and lr.status!='done'
                            and lr.status!='cancelled'

                     """, (recid, ))

    return res


def get_all_requests_for_item_order_by_status(recid):
    """
    @param recid: recID - CDS Invenio record identifier
    """
    res = run_sql("""SELECT bor.id,
                            bor.name,
                            lr.id_bibrec,
                            lr.status,
                            DATE_FORMAT(lr.period_of_interest_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.period_of_interest_to,'%%Y-%%m-%%d')
                     FROM   crcLOANREQUEST lr,
                            crcBORROWER bor
                     WHERE  bor.id = lr.id_crcBORROWER and lr.id_bibrec=%s and lr.status!='done' ORDER BY status
                     """, (recid, ))

    return res

def get_all_requests_for_item_order_by_name(recid):
    """
    @param recid: recID - CDS Invenio record identifier
    """
    res = run_sql("""SELECT bor.id,
                            bor.name,
                            lr.id_bibrec,
                            lr.status,
                            DATE_FORMAT(lr.period_of_interest_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.period_of_interest_to,'%%Y-%%m-%%d')
                     FROM   crcLOANREQUEST lr,
                            crcBORROWER bor
                     WHERE  bor.id = lr.id_crcBORROWER and lr.id_bibrec=%s and lr.status!='done' ORDER BY name
                     """, (recid, ))

    return res

def get_all_requests_order_by_status():
    """

    """
    res = run_sql("""SELECT bor.id,
                            bor.name,
                            lr.id_bibrec,
                            lr.status,
                            DATE_FORMAT(lr.period_of_interest_from,'%Y-%m-%d'),
                            DATE_FORMAT(lr.period_of_interest_to,'%Y-%m-%d')
                     FROM   crcLOANREQUEST lr,
                            crcBORROWER bor
                     WHERE  bor.id = lr.id_crcBORROWER and lr.status!='done' ORDER BY status
                            """)

    return res

def get_all_requests_order_by_name():
    """
    """
    res = run_sql("""SELECT bor.id,
                            bor.name,
                            lr.id_bibrec,
                            lr.status,
                            DATE_FORMAT(lr.period_of_interest_from,'%Y-%m-%d'),
                            DATE_FORMAT(lr.period_of_interest_to,'%Y-%m-%d')
                     FROM   crcLOANREQUEST lr,
                            crcBORROWER bor
                     WHERE  bor.id = lr.id_crcBORROWER and lr.status!='done' ORDER BY name
                            """)

    return res



def get_all_requests_order_by_item():
    """
    """
    res = run_sql("""SELECT bor.id,
                            bor.name,
                            lr.id_bibrec,
                            lr.status,
                            DATE_FORMAT(lr.period_of_interest_from,'%Y-%m-%d'),
                            DATE_FORMAT(lr.period_of_interest_to,'%Y-%m-%d')
                     FROM   crcLOANREQUEST lr,
                            crcBORROWER bor
                     WHERE  bor.id = lr.id_crcBORROWER and lr.status!='done' ORDER BY id_bibrec
                            """)

    return res

def get_borrower_details(borrower_id):
    """
    @param uid: user ID
    """
    res =  run_sql("""select id, name, email, phone, address, mailbox
                      from crcBORROWER
                      where id=%s""", (borrower_id, ))
    return res


def get_borrower_name(uid):
    """
    @param uid: user ID
    """
    res = run_sql("""select name
                     from crcBORROWER
                     where id=%s""", (uid, ))

    return res[0][0]

def loan_on_desk_confirm(barcode, borrower_id):
    """
    """

    res = run_sql("""select it.id_bibrec, bor.name
                     from crcITEM it, crcBORROWER bor
                     where it.barcode=%s and bor.id=%s
                  """, (barcode, borrower_id))

    return res

def search_borrower_by_name(string):
    """
    @param str: parameter used by regexp
    """

    res = run_sql("""select id, name
                     from crcBORROWER
                     where name regexp %s
                     """, (string, ))

    return res

def search_borrower_by_email(string):
    """
    @param str: parameter used by regexp
    """

    res = run_sql("""select id, name
                     from crcBORROWER
                     where email regexp %s
                     """, (string, ))

    return res

def search_borrower_by_phone(string):
    """
    """

    res = run_sql("""select id, name
                     from crcBORROWER
                     where phone regexp %s
                     """, (string, ))

    return res


def search_borrower_by_id(string):
    """
    @param str: parameter used by regexp
    """

    res = run_sql("""select id, name
                     from crcBORROWER
                     where id regexp %s
                     """, (string, ))

    return res

def search_user_by_email(str):
    """
    """

    res = run_sql("""
                  select id, email
                  from user
                  where email regexp %s
                  """, (str, ))

    return res


def get_borrower_loan_details(uid):
    """
    @param uid: user ID
    """

    res = run_sql("""
                  select it.id_bibrec,
                         l.barcode,
                         DATE_FORMAT(l.loaned_on,'%%Y-%%m-%%d'),
                         DATE_FORMAT(l.due_date,'%%Y-%%m-%%d'),
                         l.number_of_renewals,
                         l.overdue_letter_number,
                         DATE_FORMAT(l.overdue_letter_date,'%%Y-%%m-%%d'),
                         l.type,
                         l.notes,
                         l.id
                  from crcLOAN l, crcITEM it
                  where l.barcode=it.barcode and id_crcBORROWER=%s and l.status!='returned'
    """, (uid, ))

    return res


def get_borrower_request_details(uid):
    """
    @param uid: user ID
    """

    res = run_sql("""SELECT lr.id_crcBORROWER,
                            lr.id_bibrec,
                            lr.status,
                            DATE_FORMAT(lr.period_of_interest_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.period_of_interest_to,'%%Y-%%m-%%d'),
                            lr.request_date,
                            lr.id
                     FROM   crcLOANREQUEST lr
                     WHERE  lr.id_crcBORROWER =%s and (lr.status='waiting' or lr.status='pending')
                            """, (uid, ))

    return res

def get_borrower_request_details_order_by_item(uid):
    """
    @param uid: user ID
    """

    res = run_sql("""SELECT lr.id_crcBORROWER,
                            lr.id_bibrec,
                            lr.status,
                            DATE_FORMAT(lr.period_of_interest_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.period_of_interest_to,'%%Y-%%m-%%d')
                     FROM   crcLOANREQUEST lr
                     WHERE  lr.id_crcBORROWER =%s and lr.status!='done' ORDER BY id_bibrec
                            """, (uid, ))

    return res


def get_borrower_request_details_order_by_status(uid):
    """
    @param uid: user ID
    """

    res = run_sql("""SELECT lr.id_crcBORROWER,
                            lr.id_bibrec,
                            lr.status,
                            DATE_FORMAT(lr.period_of_interest_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.period_of_interest_to,'%%Y-%%m-%%d')
                     FROM   crcLOANREQUEST lr
                     WHERE  lr.id_crcBORROWER =%s and lr.status!='done' ORDER BY status
                            """, (uid, ))

    return res


def get_borrower_request_details_order_by_from(uid):
    """
    @param uid: user ID
    """

    res = run_sql("""SELECT lr.id_crcBORROWER,
                            lr.id_bibrec,
                            lr.status,
                            DATE_FORMAT(lr.period_of_interest_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.period_of_interest_to,'%%Y-%%m-%%d')
                     FROM   crcLOANREQUEST lr
                     WHERE  lr.id_crcBORROWER =%s and lr.status!='done' ORDER BY period_of_interest_from
                            """, (uid, ))

    return res


def get_borrower_request_details_order_by_to(uid):
    """
    @param uid: user ID
    """

    res = run_sql("""SELECT lr.id_crcBORROWER,
                            lr.id_bibrec,
                            lr.status,
                            DATE_FORMAT(lr.period_of_interest_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.period_of_interest_to,'%%Y-%%m-%%d')
                     FROM   crcLOANREQUEST lr
                     WHERE  lr.id_crcBORROWER =%s and lr.status!='done' ORDER BY period_of_interest_to
                            """, (uid, ))

    return res

def new_loan(borrower_id, id_bibrec, barcode,
             loaned_on, due_date, status, type, notes):
    """
    @param barcode: primary of crcITEM
    """
    res = run_sql(""" insert into crcLOAN (id_crcBORROWER, id_bibrec,
                                           barcode, loaned_on, due_date,
                                           status, type, notes)
                      values(%s, %s, %s, %s, %s, %s ,%s, %s)
                  """, (borrower_id, id_bibrec, barcode, loaned_on,
                        due_date, status, type, notes))

    return res

def get_all_loans_for_item(recid):
    """
    @param recid: recID - CDS Invenio record identifier
    """

    res = run_sql(
    """
    select bor.id,
           bor.name,
           l.barcode,
           DATE_FORMAT(l.loaned_on,'%%Y-%%m-%%d'),
           DATE_FORMAT(l.due_date,'%%Y-%%m-%%d'),
           l.number_of_renewals,
           l.overdue_letter_number,
           DATE_FORMAT(l.overdue_letter_date,'%%Y-%%m-%%d'),
           l.status,
           l.notes,
           l.id
    from crcLOAN l, crcBORROWER bor, crcITEM it
    where l.id_crcBORROWER = bor.id
          and l.barcode=it.barcode
          and l.id_bibrec=%s
          and l.status!='returned'
    """, (recid, ))

    return res

def get_all_loans():
    """
    """

    res = run_sql(
    """
    select bor.id,
           bor.name,
           it.id_bibrec,
           l.barcode,
           DATE_FORMAT(l.loaned_on,'%Y-%m-%d'),
           DATE_FORMAT(l.due_date,'%Y-%m-%d'),
           l.number_of_renewals,
           l.overdue_letter_number,
           DATE_FORMAT(l.overdue_letter_date,'%Y-%m-%d'),
           l.status,
           l.notes,
           l.id
    from crcLOAN l, crcBORROWER bor, crcITEM it
    where l.id_crcBORROWER = bor.id
          and l.barcode=it.barcode
          and l.status!='returned' ORDER BY l.id
    """)

    return res

def get_all_expired_loans():
    """
    """
    res = run_sql(
    """
    select bor.id,
           bor.name,
           it.id_bibrec,
           l.barcode,
           DATE_FORMAT(l.loaned_on,'%Y-%m-%d'),
           DATE_FORMAT(l.due_date,'%Y-%m-%d'),
           l.number_of_renewals,
           l.overdue_letter_number,
           DATE_FORMAT(l.overdue_letter_date,'%Y-%m-%d'),
           l.status,
           l.notes,
           l.id
    from crcLOAN l, crcBORROWER bor, crcITEM it
    where l.id_crcBORROWER = bor.id and
          l.barcode=it.barcode and l.status='expired' ;
    """)

    return res


def get_all_loans_onloan():
    """
    """
    res = run_sql(
    """
    select bor.id,
           bor.name,
           it.id_bibrec,
           l.barcode,
           DATE_FORMAT(l.loaned_on,'%Y-%m-%d'),
           DATE_FORMAT(l.returned_on,'%Y-%m-%d'),
           DATE_FORMAT(l.due_date,'%Y-%m-%d'),
           l.number_of_renewals,
           l.overdue_letter_number,
           DATE_FORMAT(l.overdue_letter_date,'%Y-%m-%d'),
           l.status
    from crcLOAN l, crcBORROWER bor, crcITEM it
    where l.id_crcBORROWER = bor.id and
          l.barcode=it.barcode and l.status='on loan';
    """)

    return res




def get_borrower_loans(uid):
    """
    @param uid: user ID
    """

    res = run_sql(""" select id_bibrec,
                             barcode,
                             DATE_FORMAT(loaned_on,'%%Y-%%m-%%d'),
                             DATE_FORMAT(due_date,'%%Y-%%m-%%d')
                      from crcLOAN
                      where id_crcBORROWER=%s and status != 'returned'
                  """, (uid, ))

    return res


def update_due_date(loan_id, new_due_date):
    """
    @param barcode: primary key of crcITEM
    """
    return int(run_sql("""UPDATE  crcLOAN
                             SET  due_date=%s,
                                  number_of_renewals = number_of_renewals + 1
                           WHERE  id=%s""",
                       (new_due_date, loan_id)))

def update_due_date_borrower(borrower, new_due_date):
    """
    """
    return int(run_sql("""UPDATE  crcLOAN
                             SET  due_date=%s
                           WHERE  id_crcBORROWER=%s and status='on loan'
                           """, (new_due_date, borrower)))

def update_recid_due_date_borrower(borrower, new_due_date, recid):
    """
    @param recid: recID - CDS Invenio record identifier
    """

    return int(run_sql("""UPDATE  crcLOAN
                             SET  due_date=%s,
                                  number_of_renewals = number_of_renewals + 1
                           WHERE  id_crcBORROWER=%s and id_bibrec=%s and status='on loan'
                           """, (new_due_date, borrower, recid)))


def get_queue_request(recid):
    """
    @param recid: recID - CDS Invenio record identifier
    """
    res = run_sql(""" select id
                      from crcLOANREQUEST
                      where id_bibrec=%s and (status='pending' or status='waiting')
                  """, (recid, ))

    return res

def get_recid_borrower_loans(uid):
    """
    @param uid: user ID
    """

    res = run_sql(""" select id, id_bibrec, barcode
                      from crcLOAN
                      where id_crcBORROWER=%s and status = 'on loan'
                  """, (uid, ))


    return res

def get_borrowerID(name):
    """
    """

    res = run_sql(""" select id
                      from crcBORROWER
                      where name=%s """, (name, ))

    return res [0][0]

def update_barcode_on_crcloanrequest(barcode, request_id):
    """
    Update the barcode of an hold request.
    barcode: new barcode (after update). It is also the
             primary key of the crcITEM table.
    request_id: identify the hold request who will be
                cancelled. It is also the primary key of
                the crcLOANREQUEST table.
    """

    run_sql("""update crcLOANREQUEST
               set barcode = %s
               where id = %s
            """, (barcode, request_id))

def get_historical_overview(borrower_id):
    """
    Get historical information overview (recid, loan date, return date
    and number of renewals).
    borrower_id: identify the borrower. All the old (returned) loans
                 associate to this borrower will be retrieved.
                 It is also the primary key of the crcBORROWER table.
    """

    res = run_sql("""select id_bibrec,
                            DATE_FORMAT(loaned_on,'%%Y-%%m-%%d'),
                            returned_on,
                            number_of_renewals
                     from crcLOAN
                     where id_crcBORROWER = %s and status = "returned";
                  """, (borrower_id, ))

    return res

def get_borrower_requests(borrower_id):
    """
    Get the hold requests of a borrower.
    borrower_id: identify the borrower. All the hold requests
                 associate to this borrower will be retrieved.
                 It is also the primary key of the crcBORROWER table.
    """
    res = run_sql("""
                  select id, id_bibrec,
                         DATE_FORMAT(request_date,'%%Y-%%m-%%d'), status
                  from   crcLOANREQUEST
                  where  id_crcBORROWER=%s and
                         (status='pending' or status='waiting')""",
                  (borrower_id, ))

    return res

def cancel_request(request_id, status):
    """
    Cancel an hold request.
    request_id: identify the hold request who will be
                cancelled. It is also the primary key of
                the crcLOANREQUEST table.
    status: The new status of the hold request. In this case
            it will be 'cancelled'.
    """
    run_sql("""update crcLOANREQUEST set status=%s
               where id=%s
            """, (status, request_id))

def get_nb_copies_on_loan(recid):
    """
    Get the number of copies on loan for a recid.
    recid: CDS Invenio record identifier. The number of copies
           of this record will be retrieved.
    """

    res = run_sql("""select id_bibrec
                     from crcLOAN
                     where id_bibrec=%s and status='on loan';
                     """, (recid, ))

    return res


def get_loans_notes(loan_id):
    """
    Get loan's notes.
    loan_id: identify the loan. The notes of
             this loan will be retrieved. It is
             also the primary key of the table
             crcLOAN.
    """

    res = run_sql("""select notes
                     from crcLOAN
                     where id=%s
                     """, (loan_id, ))

    return res[0][0]

def add_new_note(new_note, borrower_id):
    """
    Add a new borrower's note.
    new_note: note who will be added.
    borrower_id: identify the borrower. A new note will be
                 associate to this borrower. It is also
                 the primary key of the crcBORROWER table.
    """
    run_sql("""update crcBORROWER
               set notes=concat(notes,%s)
               where id=%s;
                """, (new_note, borrower_id))

def add_new_loan_note(new_note, loan_id):
    """
    Add a new loan's note.
    new_note: note who will be added.
    loan_id: identify the loan. A new note will
             added to this loan. It is also the
             primary key of the table crcLOAN.
    """
    run_sql("""update crcLOAN
               set notes=concat(notes,%s)
               where id=%s;
                """, (new_note, loan_id))


def is_borrower(email):
    """
    Verify if someone is a borrower, using the email.
    email: borrower's email.
    """
    res = run_sql("""select id
                     from crcBORROWER
                     where email=%s""",
                  (email, ))
    if res:
        return res[0][0]
    else:
        return 0

def new_borrower(name, email, phone, address, mailbox, notes):
    """
    Add/Register a new borrower on the crcBORROWER table.
    name: borrower's name.
    email: borrower's email.
    phone: borrower's phone.
    address: borrower's address.
    """

    res = run_sql("""insert into crcBORROWER (name,
                                              email,
                                              phone,
                                              address,
                                              mailbox,
                                              borrower_since,
                                              borrower_until,
                                              notes)
                      values(%s, %s, %s, %s, %s, NOW(), '0000-00-00 00:00:00', %s)""",
                      (name, email, phone, address, mailbox, notes))

def get_borrower_address(email):
    """
    Get the address of a borrower using the email.
    email: borrower's email.
    """

    res = run_sql("""select address
                     from crcBORROWER
                     where email=%s""", (email, ))

    if len(res[0][0]) > 0:
        return res[0][0]
    else:
        return 0

def add_borrower_address(address, email):
    """
    Add the email and the address of a borrower.
    address: borrower's address.
    email: borrower's email.
    """

    run_sql("""update crcBORROWER
               set address=%s
               where email=%s""", (address, email))


def get_invenio_user_email(uid):
    """
    Get the email of an invenio's user.
    uid: identify an invenio's user.
    """

    res = run_sql("""select email
                     from user
                     where id=%s""",
                  (uid, ))

    return res[0][0]

def get_borrower_notes(borrower_id):
    """
    Get the notes of a borrower.
    borrower_id: identify the borrower. The data associate
                 to this borrower will be retrieved. It is also
                 the primary key of the crcBORROWER table.
    """

    res = run_sql("""select notes
                     from   crcBORROWER
                     where id=%s""",
                  (borrower_id, ))

    return res[0][0]

def update_loan_status(status, loan_id):
    """
    Update the status of a loan.
    status: new status (after update)
    loan_id: identify the loan who will be updated.
             It is also the primary key of the table
             crcLOAN.
    """
    run_sql("""update crcLOAN
               set status = %s
               where id = %s""",
            (status, loan_id))

def get_loan_due_date(loan_id):
    """
    Get the due date of a loan.
    loan_id: identify the loan. The due date of
             this loan will be retrieved. It is
             also the primary key of the table
             crcLOAN.
    """

    res = run_sql("""select DATE_FORMAT(due_date, '%%Y-%%m-%%d')
                     from crcLOAN
                     where id = %s""",
                  (loan_id, ))

    return res[0][0]

def get_pdf_request_data(status):
    """
    @param status: status=pending
    """
    res = run_sql("""SELECT DISTINCT
                            lr.id_bibrec,
                            bor.name,
	                    it.location,
                            DATE_FORMAT(lr.period_of_interest_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.period_of_interest_to,'%%Y-%%m-%%d'),
                            lr.request_date
                     FROM   crcLOANREQUEST lr,
                            crcBORROWER bor,
			    crcITEM it
                     WHERE  lr.id_crcBORROWER=bor.id AND it.id_bibrec=lr.id_bibrec AND
                            lr.status=%s;
                  """ ,
                     (status, ))
    return res

def get_last_loan():
    """
    Get the recid, the borrower_id and the due date of
    the last loan who was registered on the crcLOAN table.
    """

    res = run_sql("""select id_bibrec,
                            id_crcBORROWER,
                            DATE_FORMAT(due_date, '%Y-%m-%d')
                     from   crcLOAN ORDER BY id DESC LIMIT 1""")

    return res[0]

def get_borrower_data(borrower_id):
    """
    Get the borrower's information (name, address and email).
    borrower_id: identify the borrower. The data associate
                 to this borrower will be retrieved. It is also
                 the primary key of the crcBORROWER table.
    """

    res = run_sql("""select name,
                            address,
                            email
                     from   crcBORROWER
                     where  id=%s""",
                  (borrower_id, ))

    return res[0]

def update_borrower_info(borrower_id, name, email, phone, address, mailbox):
    """
    Update borrower info.
    """
    return int(run_sql("""update crcBORROWER
                             set name=%s,
                                 email=%s,
                                 phone=%s,
                                 address=%s,
                                 mailbox=%s
                          where  id=%s""",
                       (name, email, phone, address, mailbox, borrower_id)))

def add_new_library(name, email, phone, address, notes):
    """
    Add a new Library.
    """

    run_sql("""insert into crcLIBRARY (name, email, phone,
                                       address, notes)
                           values (%s, %s, %s, %s, %s)""",
            (name, email, phone, address, notes))

def search_library_by_name(string):
    """
    @param str: parameter used by regexp
    """

    res = run_sql("""select id, name
                     from crcLIBRARY
                     where name regexp %s
                     """, (string, ))

    return res

def search_library_by_email(string):
    """
    @param str: parameter used by regexp
    """

    res = run_sql("""select id, name
                     from crcLIBRARY
                     where email regexp %s
                     """, (string, ))

    return res

def update_library_info(library_id, name, email, phone, address):
    """
    Update library info.
    """
    return int(run_sql("""update crcLIBRARY
                             set name=%s,
                                 email=%s,
                                 phone=%s,
                                 address=%s
                          where  id=%s""",
                       (name, email, phone, address, library_id)))

def get_libraries():
    """
    Get Libraries
    """

    res = run_sql("""select id, name
                     from   crcLIBRARY""")

    return res

def get_library_name(library_id):
    """
    Get Library's name.
    """

    res = run_sql("""select name
                     from   crcLIBRARY
                     where  id=%s""",
                  (library_id, ))

    return res[0][0]

def add_new_copy(barcode, recid, library_id, collection, location, description,
                 loan_period, status):

    """
    Add a new copy
    """

    run_sql("""insert into crcITEM (barcode, id_bibrec, id_crcLIBRARY,
                                    collection, location, description, loan_period,
                                    status, creation_date, modification_date)
                             values (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())""",
            (barcode, recid, library_id, collection, location, description,
             loan_period, status))

def get_item_info(barcode):
    """
    Get item's information.
    """

    res = run_sql("""select it.barcode,
                            it.id_crcLIBRARY,
                            lib.name,
                            it.collection,
                            it.location,
                            it.description,
                            it.loan_period,
                            it.status
                      from  crcITEM it,
                            crcLIBRARY lib
                     where  it.barcode=%s and it.id_crcLIBRARY = lib.id""",
                  (barcode, ))

    return res[0]

def update_item_info(barcode, library_id, collection, location, description,
                 loan_period, status):
    """
    Update item's information.
    """

    int(run_sql("""update crcITEM
                      set barcode=%s,
                          id_crcLIBRARY=%s,
                          collection=%s,
                          location=%s,
                          description=%s,
                          loan_period=%s,
                          status=%s,
                          modification_date=NOW()
                   where  barcode=%s""",
                (barcode, library_id, collection, location, description,
                 loan_period, status, barcode)))

def get_library_items(library_id):
    """
    Get all items who belong to a library.
    """
    res = run_sql("""select barcode, id_bibrec, collection,
                            location, description, loan_period, status, number_of_requests
                      from  crcITEM
                     where  id_crcLIBRARY=%s""",
                  (library_id, ))

    return res

def get_library_notes(library_id):
    """
    Get the notes of a library.
    borrower_id: identify the library. The data associate
                 to this library will be retrieved. It is also
                 the primary key of the crcLIBRARY table.
    """

    res = run_sql("""select notes
                     from   crcLIBRARY
                     where  id=%s""",
                  (library_id, ))

    return res[0][0]

def add_new_library_note(new_note, library_id):
    """
    Add a new borrower's note.
    new_note: note who will be added.
    borrower_id: identify the borrower. A new note will be
                 associate to this borrower. It is also
                 the primary key of the crcBORROWER table.
    """
    run_sql("""update crcLIBRARY
               set notes=concat(notes,%s)
               where id=%s;
                """, (new_note, library_id))

def get_borrower_data_by_name(name):
    """

    """

    res = run_sql("""select id, name, email, phone,
                            address, mailbox
                       from crcBORROWER
                      where name regexp %s""",
                  (name, ))

    return res


def get_borrower_data_by_email(email):
    """

    """

    res = run_sql("""select id, name, email, phone,
                            address, mailbox
                       from crcBORROWER
                      where email regexp %s""",
                  (email, ))

    return res

def get_borrower_data_by_id(borrower_id):
    """

    """

    res = run_sql("""select id, name, email, phone,
                            address, mailbox
                       from crcBORROWER
                      where id regexp %s""",
                  (borrower_id, ))

    return res

def get_number_requests_per_copy(barcode):
    """
    """

    res = run_sql("""select count(barcode)
                       from crcLOANREQUEST
                      where barcode=%s and status != 'done'""",
                  (barcode, ))

    return res[0][0]


def get_requested_barcode(request_id):
    """
    """

    res = run_sql("""select barcode
                       from crcLOANREQUEST
                      where id=%s""",
                  (request_id, ))

    return res[0][0]

def get_borrower_recids(borrower_id):
    """
    """

    res = run_sql("""select id_bibrec
                       from crcLOAN
                      where id_crcBORROWER=%s""",
                  (borrower_id,))

    return res
