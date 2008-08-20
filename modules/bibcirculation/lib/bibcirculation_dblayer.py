# -*- coding: utf-8 -*-
##
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

"""Every db-related function of module bibcirculation"""

__revision__ = "$Id$"

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
    Get information about holding, using recid
    @param recid: recID - CDS Invenio record identifier
    """
    res = run_sql("""
                  select count(lr.id_bibrec), it.loan_period, DATE_FORMAT(max(lr.request_date_to), '%%Y-%%m-%%d'), lib.name
                  from crcLOANREQUEST lr, crcITEM it, crcLIBRARY lib
                  where lib.id = it.id_crcLIBRARY and lr.id_bibrec=it.id_bibrec and it.id_bibrec=%s and lr.status = 'waiting' GROUP BY (lr.id_bibrec)
                  """, (recid, ))
    return res


def get_holdings_details(recid):
    """
    @param recid: recID - CDS Invenio record identifier
    """

    res = run_sql(""" select it.loan_period, lib.name
                      from crcITEM it, crcLIBRARY lib
                      where id_bibrec=%s limit 1""", (recid, ))

    return res

def get_loan_details(recid):
    """
    @param recid: recID - CDS Invenio record identifier
    """

    res = run_sql("""select barcode, status
                     from crcITEM
                     where id_bibrec=%s and status = "available" limit 1;
                  """, (recid, ))


    return res


def get_due_date_loan(recid):
    """
    @param recid: recID - CDS Invenio record identifier
    """

    res = run_sql("""select DATE_FORMAT(max(request_date_to),'%%Y-%%m-%%d')
                     from crcLOANREQUEST
                     where id_bibrec=%s
                  """, (recid, ))

    return res [0][0]


def get_holdings_info_no_requests(recid):
    """
    @param recid: recID - CDS Invenio record identifier
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

    res = run_sql(""" select request_date_to
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
                     where barcode=%s
                  """, (barcode, ))

    return res [0][0]

def update_item_status(status, barcode):
    """
    @param status: new item's status
    @param barcode: primary key of crcITEM
    """

    return int(run_sql("""UPDATE  crcITEM
                             SET  status=%s
                           WHERE  barcode=%s""",
                       (status, barcode)))

def new_loan_request(uid,
                     recid,
                     barcode,
                     date_from,
                     date_to,
                     status,
                     notes=None):
    """
    @param uid: user ID
    @param recid: recID - CDS Invenio record identifier
    @param barcode: primary key of crcITEM
    """

    res = run_sql("""INSERT INTO crcLOANREQUEST(id_crcborrower,
                                                id_bibrec,
                                                barcode,
                                                request_date_from,
                                                request_date_to,
                                                status,
                                                notes)
                                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                                                """, (uid, recid, barcode,
                                                      date_from, date_to,
                                                      status, notes))

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

    res = run_sql("""select request_date_to
                     from crcLOANREQUEST
                     where barcode=%s
                  """, (barcode, ))

    return res [0][0]

def get_number_requests(recid):
    """
    @param recid: recID - CDS Invenio record identifier
    """
    res =  run_sql("""select id_bibrec
                      from crcLOANREQUEST
                      where id_bibrec=%s and status != 'done'
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
                      where barcode=%s
                  """, (barcode, ))

    return res [0][0]

def get_borrower_email(uid):
    """
    @param uid: user ID
    """

    res = run_sql("""select email
                     from crcBORROWER
                     where id=%s""", (uid, ))

    return res[0][0]

def get_next_waiting_loan_request(status, recid):
    """
    @param recid: recID - CDS Invenio record identifier
    """
    res = run_sql("""SELECT lr.id,
                            bor.name,
                            lr.status,
                            DATE_FORMAT(lr.request_date_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.request_date_to,'%%Y-%%m-%%d')
                     FROM   crcLOANREQUEST lr,
                            crcBORROWER bor
                     WHERE  lr.id_crcBORROWER=bor.id AND
                            lr.status=%s AND lr.id_bibrec=%s LIMIT 1""",
                  (status, recid))

    return res

def update_loan_info(returned_on, status, barcode):
    """
    @param barcode: primary key of crcITEM
    """


    res = int(run_sql("""update crcLOAN
                         set returned_on=%s, status=%s
                         where barcode=%s
                      """, (returned_on, status, barcode)))



def get_item_addicional_details(recid):
    """
    @param recid: recID - CDS Invenio record identifier
    """
    res = run_sql("""select it.loan_period, lib.name, lib.id
                     from crcITEM it, crcLIBRARY lib
                     where it.id_bibrec=%s LIMIT 1;
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


def item_loans_historical_overview(recid):
    """
    """

    res = run_sql("""select bor.name,
                            bor.id,
                            l.barcode,
                            DATE_FORMAT(l.loaned_on,'%%Y-%%m-%%d'),
                            l.returned_on,
                            l.number_of_renewals,
                            l.overdue_letter_number
                     from crcLOAN l, crcBORROWER bor
                     where l.id_crcBORROWER=bor.id and l.id_bibrec = %s
                                                   and status = 'returned' """
                  , (recid, ))

    return res


def item_requests_historical_overview(recid):
    """
    """

    res = run_sql("""
                  select bor.name,
                         bor.id,
                         DATE_FORMAT(lr.request_date_from,'%%Y-%%m-%%d'),
                         DATE_FORMAT(lr.request_date_to,'%%Y-%%m-%%d')
                  from crcLOANREQUEST lr, crcBORROWER bor
                  where lr.id_crcBORROWER=bor.id and lr.id_bibrec = %s
                                                 and status = 'done'
                  """, (recid, ))

    return res


def get_library_details(libid):
    """
    @param libid: primary key of crcLIBRARY
    """

    res = run_sql("""select name, address, email, phone
                     from crcLIBRARY
                     where id=%s;
                     """, (libid, ))

    return res

def get_pending_loan_request(status):
    """
    @param status: status=pending
    """
    res = run_sql("""SELECT lr.id,
                            lr.id_bibrec,
                            bor.name,

                            DATE_FORMAT(lr.request_date_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.request_date_to,'%%Y-%%m-%%d')
                     FROM   crcLOANREQUEST lr,
                            crcBORROWER bor
                     WHERE  lr.id_crcBORROWER=bor.id AND
                            lr.status=%s""",
                     (status, ))
    return res

def get_pending_loan_request_on_loan(status):
    """
    @param status: status=pending
    """
    res = run_sql("""SELECT lr.id,
                            lr.id_bibrec,
                            bor.name,
                            DATE_FORMAT(lr.request_date_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.request_date_to,'%%Y-%%m-%%d')
                     FROM   crcLOANREQUEST lr,
                            crcBORROWER bor
                     WHERE  lr.id_crcBORROWER=bor.id AND
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

                            DATE_FORMAT(lr.request_date_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.request_date_to,'%%Y-%%m-%%d')
                     FROM   crcLOANREQUEST lr,
                            crcBORROWER bor
                     WHERE  lr.id_crcBORROWER=bor.id AND
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
    res = run_sql("""SELECT bor.id,
                            bor.name,
                            lr.id_bibrec,
                            lr.status,
                            DATE_FORMAT(lr.request_date_from,'%Y-%m-%d'),
                            DATE_FORMAT(lr.request_date_to,'%Y-%m-%d')
                     FROM   crcLOANREQUEST lr,
                            crcBORROWER bor
                     WHERE  bor.id = lr.id_crcBORROWER and lr.status!='done'
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
                            DATE_FORMAT(lr.request_date_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.request_date_to,'%%Y-%%m-%%d')
                     FROM   crcLOANREQUEST lr,
                            crcBORROWER bor
                     WHERE  bor.id = lr.id_crcBORROWER and lr.id_bibrec=%s and lr.status!='done'
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
                            DATE_FORMAT(lr.request_date_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.request_date_to,'%%Y-%%m-%%d')
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
                            DATE_FORMAT(lr.request_date_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.request_date_to,'%%Y-%%m-%%d')
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
                            DATE_FORMAT(lr.request_date_from,'%Y-%m-%d'),
                            DATE_FORMAT(lr.request_date_to,'%Y-%m-%d')
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
                            DATE_FORMAT(lr.request_date_from,'%Y-%m-%d'),
                            DATE_FORMAT(lr.request_date_to,'%Y-%m-%d')
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
                            DATE_FORMAT(lr.request_date_from,'%Y-%m-%d'),
                            DATE_FORMAT(lr.request_date_to,'%Y-%m-%d')
                     FROM   crcLOANREQUEST lr,
                            crcBORROWER bor
                     WHERE  bor.id = lr.id_crcBORROWER and lr.status!='done' ORDER BY id_bibrec
                            """)

    return res
def get_borrower_details(uid):
    """
    @param uid: user ID
    """
    res =  run_sql("""select id, name, email, phone, adress
                      from crcBORROWER
                      where id=%s""", (uid, ))
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

#def search_borrower(column,str):
#    """
#    """
#
#    res = run_sql("""select id, name
#                     from crcBORROWER
#                     where %s regexp %s
#                     """, (column, str))
#
#    return res
#

def search_borrower_by_name(str):
    """
    @param str: parameter used by regexp
    """

    res = run_sql("""select id, name
                     from crcBORROWER
                     where name regexp %s
                     """, (str, ))

    return res

def search_borrower_by_email(str):
    """
    @param str: parameter used by regexp
    """

    res = run_sql("""select id, name
                     from crcBORROWER
                     where email regexp %s
                     """, (str, ))

    return res

def search_borrower_by_phone(str):
    """
    """

    res = run_sql("""select id, name
                     from crcBORROWER
                     where phone regexp %s
                     """, (str, ))

    return res


def search_borrower_by_id(str):
    """
    @param str: parameter used by regexp
    """

    res = run_sql("""select id, name
                     from crcBORROWER
                     where id regexp %s
                     """, (str, ))

    return res



def  get_borrower_loan_details(uid):
    """
    @param uid: user ID
    """

    res = run_sql("""
                  select it.id_bibrec,
                         l.barcode,
                         DATE_FORMAT(l.loaned_on,'%%Y-%%m-%%d'),
                         DATE_FORMAT(l.returned_on,'%%Y-%%m-%%d'),
                         DATE_FORMAT(l.due_date,'%%Y-%%m-%%d'),
                         l.number_of_renewals,
                         l.overdue_letter_number,
                         l.overdue_letter_date,
                         l.status,
                         l.type
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
                            DATE_FORMAT(lr.request_date_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.request_date_to,'%%Y-%%m-%%d')
                     FROM   crcLOANREQUEST lr
                     WHERE  lr.id_crcBORROWER =%s and lr.status!='done'
                            """, (uid, ))

    return res

def get_borrower_request_details_order_by_item(uid):
    """
    @param uid: user ID
    """

    res = run_sql("""SELECT lr.id_crcBORROWER,
                            lr.id_bibrec,
                            lr.status,
                            DATE_FORMAT(lr.request_date_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.request_date_to,'%%Y-%%m-%%d')
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
                            DATE_FORMAT(lr.request_date_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.request_date_to,'%%Y-%%m-%%d')
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
                            DATE_FORMAT(lr.request_date_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.request_date_to,'%%Y-%%m-%%d')
                     FROM   crcLOANREQUEST lr
                     WHERE  lr.id_crcBORROWER =%s and lr.status!='done' ORDER BY request_date_from
                            """, (uid, ))

    return res


def get_borrower_request_details_order_by_to(uid):
    """
    @param uid: user ID
    """

    res = run_sql("""SELECT lr.id_crcBORROWER,
                            lr.id_bibrec,
                            lr.status,
                            DATE_FORMAT(lr.request_date_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.request_date_to,'%%Y-%%m-%%d')
                     FROM   crcLOANREQUEST lr
                     WHERE  lr.id_crcBORROWER =%s and lr.status!='done' ORDER BY request_date_to
                            """, (uid, ))

    return res

def new_loan(borrower_id, id_bibrec, barcode,
             loaned_on, due_date, status, type, notes):
    """
    @param barcode: primary of crcITEM
    """

    #barcode = barcode[0]

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
           it.id_bibrec,
           l.barcode,
           DATE_FORMAT(l.loaned_on,'%%Y-%%m-%%d'),
           DATE_FORMAT(l.returned_on,'%%Y-%%m-%%d'),
           DATE_FORMAT(l.due_date,'%%Y-%%m-%%d'),
           l.number_of_renewals,
           l.overdue_letter_number,
           l.overdue_letter_date,
           l.status
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
           DATE_FORMAT(l.returned_on,'%Y-%m-%d'),
           DATE_FORMAT(l.due_date,'%Y-%m-%d'),
           l.number_of_renewals,
           l.overdue_letter_number,
           l.overdue_letter_date,
           l.status
    from crcLOAN l, crcBORROWER bor, crcITEM it
    where l.id_crcBORROWER = bor.id
          and l.barcode=it.barcode
          and l.status!='returned'
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
           DATE_FORMAT(l.returned_on,'%Y-%m-%d'),
           DATE_FORMAT(l.due_date,'%Y-%m-%d'),
           l.number_of_renewals,
           l.overdue_letter_number,
           l.overdue_letter_date,
           l.status
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
           l.overdue_letter_date,
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


def update_due_date(barcode, new_due_date):
    """
    @param barcode: primary key of crcITEM
    """
    return int(run_sql("""UPDATE  crcLOAN
                             SET  due_date=%s,
                                  number_of_renewals = number_of_renewals + 1
                           WHERE  barcode=%s""",
                       (new_due_date, barcode)))

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
    #raise repr(recid)

    res = run_sql(""" select id
                      from crcLOANREQUEST
                      where id_bibrec=%s and status != 'done'
                  """, (recid, ))

    return res

def get_recid_borrower_loans(uid):
    """
    @param uid: user ID
    """

    res = run_sql(""" select id_bibrec
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

def update_barcode_on_crcloanrequest(barcode, check_id):
    """
    """

    run_sql("""update crcLOANREQUEST
               set barcode = %s
               where id = %s
            """, (barcode, check_id))

def get_historical_overview(uid):
    """
    """

    res = run_sql("""select id_bibrec,
                            DATE_FORMAT(loaned_on,'%%Y-%%m-%%d'),
                            returned_on,
                            number_of_renewals
                     from crcLOAN
                     where id_crcBORROWER = %s and status = "returned";
                  """, (uid, ))

    return res
