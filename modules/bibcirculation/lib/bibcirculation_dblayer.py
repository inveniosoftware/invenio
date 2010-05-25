# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
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
    Get information about holding, using recid.

    @param recid: identify the record. Primary key of bibrec.
    @type recid: int

    @return holdings information
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
    Get information about holding, using recid.

    @param recid: identify the record. Primary key of bibrec.
    @type recid: int

    @return holdings information
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

    @param recid: identify the record. Primary key of bibrec.
    @type recid: int

    @return list with loan period, location and library.
    """

    res = run_sql(""" select it.loan_period, lib.name, it.location
                      from crcITEM it, crcLIBRARY lib
                      where id_bibrec=%s limit 1""",
                  (recid, ))

    return res

def get_loan_details(recid):
    """
    Get details about a loan (barcode and status).

    @param recid: identify the record. Primary key of bibrec.
    @type recid: int

    @return loan details
    """

    res = run_sql("""select barcode, status
                     from crcITEM
                     where id_bibrec=%s and status = "available" limit 1;
                  """, (recid, ))


    return res

def get_due_date_loan(recid):
    """
    Get the due date of a loan.

    @param recid: identify the record. Primary key of bibrec.
    @type recid: int

    @return due date
    """

    res = run_sql("""select DATE_FORMAT(max(due_date),'%%Y-%%m-%%d')
                     from crcLOAN
                     where id_bibrec=%s and status != 'returned'
                  """, (recid, ))

    if res:
        return res[0][0]
    else:
        return None


def get_holdings_info_no_requests(recid):
    """
    @param recid: identify the record. Primary key bibrec.
    @type recid: int
    """

    res = run_sql(""" select it.loan_period, lib.name
                      from crcITEM it, crcLIBRARY lib
                      where it.id_crcLIBRARY=lib.id and it.id_bibrec=%s
                      """, (recid, ))

    return res

def get_request_recid(request_id):
    """
    Get recid of a given request_id

    @param request_id: identify the (hold) request. Primary key of crcLOANREQUEST.
    @type request_id: int

    @return recid
    """
    res = run_sql(""" select id_bibrec
                      from crcLOANREQUEST
                      where id=%s
                  """, (request_id, ))

    if res:
        return res[0][0]
    else:
        return None

def get_request_borrower_id(request_id):
    """
    Get borrower_id of a given request_id

    @param request_id: identify the (hold) request. Primary key of crcLOANREQUEST.
    @type request_id: int

    @return borrower_id
    """

    res = run_sql(""" select id_crcBORROWER
                      from crcLOANREQUEST
                      where id=%s
                  """, (request_id, ))

    if res:
        return res[0][0]
    else:
        return None


def get_request_barcode(request_id):
    """
    Get the barcode associate to a request_id.

    @param request_id: identify the (hold) request. Primary key of crcLOANREQUEST.
    @type request_id: int

    @return barcode
    """
    res = run_sql(""" select barcode
                      from crcLOANREQUEST
                      where id=%s
                  """, (request_id, ))

    if res:
        return res[0][0]
    else:
        return None

def get_id_bibrec(barcode):
    """
    Get the id bibrec (or recid).

    @param barcode: identify the item. Primary key of crcITEM.
    @type barcode: string

    @return recid or None
    """

    res = run_sql("""select id_bibrec
                     from crcITEM
                     where barcode=%s
                  """, (barcode, ))

    if res:
        return res[0][0]
    else:
        return None

def update_item_status(status, barcode):
    """
    Update the status of an item (using the barcode).

    @param status: status of the item.
    @type status: string

    @param barcode: identify the item. Primary key of crcITEM.
    @type barcode: string

    @return
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
    Create a new hold request.

    @param borrower_id: identify the borrower. Primary key of crcBORROWER.
    @type borrower_id: int

    @param recid: identify the record. Primary key of bibrec.
    @type recid: int

    @param barcode: identify the item. Primary key of crcITEM.
    @type barcode: string

    @param date_from: begining of the period of interest.
    @type date_from: string

    @param date_to: end of the period of interest.
    @type date_to: string

    @param status: hold request status.
    @type status: string

    @return
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
    Get all the barcodes(copies) of a record(item).

    @param recid: identify the record. Primary key of bibrec.
    @type recid: int

    @return list with barcode(s).
    """

    res = run_sql("""select barcode
                     from crcITEM
                     where id_bibrec=%s
                  """, (recid, ))

    if res:
        return res[0][0]
    else:
        return None

def get_due_date(barcode):
    """
    Get the due date of a given barcode.

    @param barcode: identify the item. Primary key of crcITEM.
    @type barcode: string

    @return due_date
    """

    res = run_sql("""select period_of_interest_to
                     from crcLOANREQUEST
                     where barcode=%s
                  """, (barcode, ))

    if res:
        return res[0][0]
    else:
        return None

def get_number_requests(recid):
    """
    Get the number of requests of a record.

    @param recid: identify the record. Primary key of bibrec.
    @type recid: int

    @return number of request (int)
    """
    res =  run_sql("""
                      select id_bibrec
                      from crcLOANREQUEST
                      where id_bibrec=%s and status != 'done' and status != 'cancelled';
                   """, (recid, ))

    return res

def get_number_requests2(barcode, request_id):
    """
    @param barcode: identify the item. Primary key of crcITEM.
    @type barcode: string

    @param request_id: identify the (hold) request. Primary key of crcLOANREQUEST.
    @type request_id: int

    """

    res =  run_sql("""select id_bibrec
                      from crcLOANREQUEST
                      where id < %s and barcode=%s and status != 'done'
                   """, (request_id, barcode))

    return res


def loan_return_confirm(borrower_id, recid):
    """
    @param borrower_id: identify the borrower. Primary key of crcBORROWER.
    @type borrower_id: int

    @param recid: identify the record. Primary key of bibrec.
    @type recid: int
    """
    res = run_sql("""select bor.name, it.id_bibrec
                     from crcBORROWER bor, crcITEM it
                     where bor.id=%s and it.id_bibrec=%s
                     """, (borrower_id, recid))

    return res

def get_borrower_id(barcode):
    """
    Get the borrower id who is associate to a loan.

    @param barcode: identify the item. Primary key of crcITEM.
    @type barcode: string

    @return borrower_id or None
    """
    res = run_sql(""" select id_crcBORROWER
                      from crcLOAN
                      where barcode=%s and
                            (status='on loan' or status='expired')""",
                  (barcode, ))
    try:
        return res[0][0]
    except IndexError:
        return None

def get_borrower_email(borrower_id):
    """
    Get the email of a borrower.

    @param borrower_id: identify the borrower. Primary key of crcBORROWER.
    @type borrower_id: int

    @return borrower's email (string).
    """
    res = run_sql("""select email
                     from crcBORROWER
                     where id=%s""", (borrower_id, ))

    if res:
        return res[0][0]
    else:
        return None

def get_next_waiting_loan_request(recid):
    """
    Get the next waiting (loan) request for a given recid.

    @param recid: identify the record. Primary key of bibrec.
    @type recid: int

    @return list with request_id, borrower_name, recid, status,
            period_of_interest (from and to) and request_date.
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
    Update loan information when copy is returned.

    @param returned_on: return date.
    @type returned_on: string

    @param status: new loan status.
    @type status: string

    @param barcode: identify the item. Primary key of crcITEM.
    @type barcode: string

    @return
    """

    return int(run_sql("""update crcLOAN
                          set returned_on=%s, status=%s
                          where barcode=%s
                      """, (returned_on, status, barcode)))



def get_item_copies_details(recid):
    """
    Get copies details of a given recid.

    @param recid: identify the record. Primary key of bibrec.
    @type recid: int

    @return list with barcode, loan_period, library_name, library_id,
                      location, number_of_requests, status, collection,
                      description and due_date.
    """
    res = run_sql("""select it.barcode, it.loan_period, lib.name,
                            lib.id, it.location, it.number_of_requests,
                            it.status, it.collection, it.description,
                            DATE_FORMAT(ln.due_date,'%%Y-%%m-%%d')
                     from crcITEM it
                            left join crcLOAN ln
                            on it.barcode = ln.barcode and ln.status != 'returned'
                            left join crcLIBRARY lib
                            on lib.id = it.id_crcLIBRARY
                     where it.id_bibrec=%s
                     order by it.creation_date
                  """, (recid, ))

    return res

def get_number_copies(recid):
    """
    Get the number of copies of a given recid.

    @param recid: identify the record. Primary key of bibrec.
    @type recid: int

    @return number_of_copies
    """

    res = run_sql("""select count(barcode)
                     from crcITEM
                     where id_bibrec=%s
                  """, (recid, ))

    return res[0][0]


def has_copies(recid):
    """
    Indicate if there are any physical copies of a document described
    by the record

    @param recid: The identifier of the record
    @type recid: int

    @return True or False according to the state
    """
    return get_number_copies(recid) != 0;

def bor_loans_historical_overview(borrower_id):
    """
    Get loans historical overview of a given borrower_id.

    @param borrower_id: identify the borrower. Primary key of crcBORROWER.
    @type borrower_id: int

    @return list with loans historical overview.
    """
    res = run_sql("""
                     select l.id_bibrec,
                            l.barcode,
                            lib.name,
                            it.location,
                            DATE_FORMAT(l.loaned_on,'%%Y-%%m-%%d'),
                            DATE_FORMAT(l.due_date,'%%Y-%%m-%%d'),
                            l.returned_on,
                            l.number_of_renewals,
                            l.overdue_letter_number
                     from crcLOAN l, crcITEM it, crcLIBRARY lib
                     where l.id_crcBORROWER=%s and
                           lib.id = it.id_crcLIBRARY and
                           it.barcode = l.barcode and
                           l.status = 'returned' """,
                   (borrower_id, ))
    return res

def bor_requests_historical_overview(borrower_id):
    """
    Get requests historical overview of a given borrower_id.

    @param borrower_id: identify the borrower. Primary key of crcBORROWER.
    @type borrower_id: int

    @return list with requests historical overview.
    """
    res = run_sql("""select lr.id_bibrec,
                            lr.barcode,
                            lib.name,
                            it.location,
                            DATE_FORMAT(lr.period_of_interest_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.period_of_interest_to,'%%Y-%%m-%%d'),
                            lr.request_date
                     from crcLOANREQUEST lr, crcITEM it, crcLIBRARY lib
                     where lr.id_crcBORROWER=%s and
                           lib.id = it.id_crcLIBRARY and
                           it.barcode = lr.barcode and
                           lr.status ='done' """
                  , (borrower_id, ))
    return res

def get_item_loans_historical_overview(recid):
    """
    @param recid: identify the record. Primary key of bibrec.
    @type recid: int
    """
    res = run_sql("""select bor.name,
                            bor.id,
                            l.barcode,
                            lib.name,
                            it.location,
                            DATE_FORMAT(l.loaned_on,'%%Y-%%m-%%d'),
                            DATE_FORMAT(l.due_date,'%%Y-%%m-%%d'),
                            l.returned_on,
                            l.number_of_renewals,
                            l.overdue_letter_number
                     from crcLOAN l, crcBORROWER bor, crcITEM it, crcLIBRARY lib
                     where l.id_crcBORROWER=bor.id and
                           lib.id = it.id_crcLIBRARY and
                           it.barcode = l.barcode and
                           l.id_bibrec = %s and
                           l.status = 'returned' """
                  , (recid, ))

    return res


def get_item_requests_historical_overview(recid):
    """
    recid: identify the record. It is also the primary key of
           the table bibrec.
    """

    res = run_sql("""
                  select bor.name,
                         bor.id,
                         lr.barcode,
                         lib.name,
                         it.location,
                         DATE_FORMAT(lr.period_of_interest_from,'%%Y-%%m-%%d'),
                         DATE_FORMAT(lr.period_of_interest_to,'%%Y-%%m-%%d'),
                         lr.request_date
                  from crcLOANREQUEST lr, crcBORROWER bor, crcITEM it, crcLIBRARY lib
                  where lr.id_crcBORROWER=bor.id and
                        lib.id = it.id_crcLIBRARY and
                        it.barcode = lr.barcode and
                        lr.id_bibrec = %s and
                        lr.status = 'done'
                  """, (recid, ))

    return res


def get_library_details(library_id):
    """
    library_id: identify the library. It is also the primary key of
            the table crcLIBRARY.
    """
    res = run_sql("""select id, name, address, email, phone, notes
                     from crcLIBRARY
                     where id=%s;
                     """, (library_id, ))

    if res:
        return res[0]
    else:
        return None

def get_loan_request_by_status(status):
    """
    status: request status.
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


def update_loan_request_status(request_id, status):
    """
    request_id: identify the hold request. It is also the primary key
                of the table crcLOANREQUEST.

    status: new request status.
    """
    return int(run_sql("""UPDATE  crcLOANREQUEST
                             SET  status=%s
                           WHERE  id=%s""",
                       (status, request_id)))

def get_all_requests():
    """
    Retrieve all requests.
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
                     WHERE  bor.id = lr.id_crcBORROWER and (lr.status='waiting' or lr.status='pending')
                            ORDER BY lr.request_date
                            """)

    return res

def get_item_requests(recid):
    """
    recid: identify the record. It is also the primary key of
           the table bibrec.
    """
    res = run_sql("""SELECT bor.id,
                            bor.name,
                            lr.id_bibrec,
                            lr.status,
                            lib.name,
                            it.location,
                            DATE_FORMAT(lr.period_of_interest_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.period_of_interest_to,'%%Y-%%m-%%d'),
                            lr.id,
                            lr.request_date
                     FROM   crcLOANREQUEST lr,
                            crcBORROWER bor,
                            crcITEM it,
                            crcLIBRARY lib
                     WHERE  bor.id = lr.id_crcBORROWER and lr.id_bibrec=%s
                            and lr.status!='done' and lr.status!='cancelled'
                            and lr.barcode = it.barcode and lib.id = it.id_crcLIBRARY
                     """, (recid, ))

    return res


def get_all_requests_for_item_order_by_status(recid):
    """
    recid: identify the record. It is also the primary key of
           the table bibrec.
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
    recid: identify the record. It is also the primary key of
           the table bibrec.
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
    Get all requests order by status.
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
    Get all requests order by name.
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
    Get all requests order by item.
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
    borrower_id: identify the borrower. It is also the primary key of
                 the table crcBORROWER.
    """
    res =  run_sql("""select id, name, email, phone, address, mailbox
                      from crcBORROWER
                      where id=%s""", (borrower_id, ))
    if res:
        return res[0]
    else:
        return None


def get_borrower_name(borrower_id):
    """
    borrower_id: identify the borrower. It is also the primary key of
                 the table crcBORROWER.
    """
    res = run_sql("""select name
                     from crcBORROWER
                     where id=%s""", (borrower_id, ))

    if res:
        return res[0][0]
    else:
        return None

def loan_on_desk_confirm(barcode, borrower_id):
    """
    barcode: identify the item. It is the primary key of the table
             crcITEM.

    borrower_id: identify the borrower. It is also the primary key of
                 the table crcBORROWER.
    """
    res = run_sql("""select it.id_bibrec, bor.name
                     from crcITEM it, crcBORROWER bor
                     where it.barcode=%s and bor.id=%s
                  """, (barcode, borrower_id))

    return res

def search_borrower_by_name(string):
    """
    string: search pattern.
    """

    res = run_sql("""select id, name
                     from crcBORROWER
                     where name regexp %s order by name
                     """, (string, ))

    return res

def search_borrower_by_email(string):
    """
    string: search pattern.
    """

    res = run_sql("""select id, name
                     from crcBORROWER
                     where email regexp %s
                     """, (string, ))

    return res



def search_borrower_by_phone(string):
    """
    string: search pattern.
    """

    res = run_sql("""select id, name
                     from crcBORROWER
                     where phone regexp %s
                     """, (string, ))

    return res


def search_borrower_by_id(string):
    """
    string: search pattern.
    """

    res = run_sql("""select id, name
                     from crcBORROWER
                     where id=%s
                     """, (string, ))

    return res

def search_user_by_email(string):
    """
    string: search pattern.
    """

    res = run_sql("""
                  select id, email
                  from user
                  where email regexp %s
                  """, (string, ))

    return res


def get_borrower_loan_details(borrower_id):
    """
    borrower_id: identify the borrower. It is also the primary key of
                 the table crcBORROWER.
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
                         l.id,
                         l.status
                  from crcLOAN l, crcITEM it
                  where l.barcode=it.barcode and id_crcBORROWER=%s and l.status!='returned'
    """, (borrower_id, ))

    return res


def get_borrower_request_details(borrower_id):
    """
    borrower_id: identify the borrower. It is also the primary key of
                 the table crcBORROWER.
    """

    res = run_sql("""SELECT lr.id_bibrec,
                            lr.status,
                            lib.name,
                            it.location,
                            DATE_FORMAT(lr.period_of_interest_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.period_of_interest_to,'%%Y-%%m-%%d'),
                            lr.request_date,
                            lr.id
                     FROM   crcLOANREQUEST lr,
                            crcITEM it,
                            crcLIBRARY lib
                     WHERE  lr.id_crcBORROWER =%s and (lr.status='waiting' or lr.status='pending')
                            and lib.id = it.id_crcLIBRARY and lr.barcode = it.barcode
                            """, (borrower_id, ))

    return res

def get_borrower_request_details_order_by_item(borrower_id):
    """
    borrower_id: identify the borrower. It is also the primary key of
                 the table crcBORROWER.
    """

    res = run_sql("""SELECT lr.id_crcBORROWER,
                            lr.id_bibrec,
                            lr.status,
                            DATE_FORMAT(lr.period_of_interest_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.period_of_interest_to,'%%Y-%%m-%%d')
                     FROM   crcLOANREQUEST lr
                     WHERE  lr.id_crcBORROWER =%s and lr.status!='done' ORDER BY id_bibrec
                            """, (borrower_id, ))

    return res


def get_borrower_request_details_order_by_status(borrower_id):
    """
    borrower_id: identify the borrower. It is also the primary key of
                 the table crcBORROWER.
    """

    res = run_sql("""SELECT lr.id_crcBORROWER,
                            lr.id_bibrec,
                            lr.status,
                            DATE_FORMAT(lr.period_of_interest_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.period_of_interest_to,'%%Y-%%m-%%d')
                     FROM   crcLOANREQUEST lr
                     WHERE  lr.id_crcBORROWER =%s and lr.status!='done' ORDER BY status
                            """, (borrower_id, ))

    return res


def get_borrower_request_details_order_by_from(borrower_id):
    """
    borrower_id: identify the borrower. It is also the primary key of
                 the table crcBORROWER.
    """

    res = run_sql("""SELECT lr.id_crcBORROWER,
                            lr.id_bibrec,
                            lr.status,
                            DATE_FORMAT(lr.period_of_interest_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.period_of_interest_to,'%%Y-%%m-%%d')
                     FROM   crcLOANREQUEST lr
                     WHERE  lr.id_crcBORROWER =%s and lr.status!='done' ORDER BY period_of_interest_from
                            """, (borrower_id, ))

    return res


def get_borrower_request_details_order_by_to(borrower_id):
    """
    borrower_id: identify the borrower. It is also the primary key of
                 the table crcBORROWER.
    """

    res = run_sql("""SELECT lr.id_crcBORROWER,
                            lr.id_bibrec,
                            lr.status,
                            DATE_FORMAT(lr.period_of_interest_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.period_of_interest_to,'%%Y-%%m-%%d')
                     FROM   crcLOANREQUEST lr
                     WHERE  lr.id_crcBORROWER =%s and lr.status!='done' ORDER BY period_of_interest_to
                            """, (borrower_id, ))

    return res

def new_loan(borrower_id, recid, barcode,
             loaned_on, due_date, status, loan_type, notes):
    """
    Create a new loan.

    borrower_id: identify the borrower. It is also the primary key of
                 the table crcBORROWER.

    recid: identify the record. It is also the primary key of
           the table bibrec.

    barcode: identify the item. It is the primary key of the table
             crcITEM.

    loaned_on: loan date.

    due_date: due date.

    status: loan status.

    loan_type: loan type(normal, ILL, etc...)

    notes: loan notes.
    """



    res = run_sql(""" insert into crcLOAN (id_crcBORROWER, id_bibrec,
                                           barcode, loaned_on, due_date,
                                           status, type, notes)
                      values(%s, %s, %s, %s, %s, %s ,%s, %s)
                  """, (borrower_id, recid, barcode, loaned_on,
                        due_date, status, loan_type, str(notes)))

    return res

def get_item_loans(recid):
    """
    recid: identify the record. It is also the primary key of
           the table bibrec.
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

def get_all_loans(limit):
    """
    Get all loans.
    """

    res = run_sql(
    """
    SELECT bor.id,
           bor.name,
           it.id_bibrec,
           l.barcode,
           DATE_FORMAT(l.loaned_on,'%%Y-%%m-%%d'),
           DATE_FORMAT(l.due_date,'%%Y-%%m-%%d'),
           l.number_of_renewals,
           l.overdue_letter_number,
           DATE_FORMAT(l.overdue_letter_date,'%%Y-%%m-%%d'),
           l.notes,
           l.id
    FROM crcLOAN l, crcBORROWER bor, crcITEM it
    WHERE l.id_crcBORROWER = bor.id
          and l.barcode = it.barcode
          and l.status = 'on loan'
    ORDER BY 5 DESC
    LIMIT 0,%s
    """, (limit,))

    return res

def get_all_expired_loans():
    """
    Get all expired(overdue) loans.
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
           l.notes,
           l.id
    from crcLOAN l, crcBORROWER bor, crcITEM it
    where l.id_crcBORROWER = bor.id
          and l.barcode = it.barcode
          and ( (l.status = 'on loan' and l.due_date < CURDATE())
                  or l.status='expired' )

    """)
# l.status='expired'

    return res


def get_borrower_loans(borrower_id):
    """
    borrower_id: identify the borrower. It is also the primary key of
             the table crcBORROWER.
    """

    res = run_sql(""" select id_bibrec,
                             barcode,
                             DATE_FORMAT(loaned_on,'%%Y-%%m-%%d'),
                             DATE_FORMAT(due_date,'%%Y-%%m-%%d'),
                             type
                      from crcLOAN
                      where id_crcBORROWER=%s and status != 'returned'
                  """, (borrower_id, ))

    return res


def update_due_date(loan_id, new_due_date):
    """
    loan_id: identify a loan. It is the primery key of the table
             crcLOAN.

    new_due_date: new due date.
    """
    return int(run_sql("""UPDATE  crcLOAN
                             SET  due_date=%s,
                                  number_of_renewals = number_of_renewals + 1
                           WHERE  id=%s""",
                       (new_due_date, loan_id)))

def update_due_date_borrower(borrower_id, new_due_date):
    """
    borrower_id: identify the borrower. It is also the primary key of
             the table crcBORROWER.

    new_due_date: new due date.
    """
    return int(run_sql("""UPDATE  crcLOAN
                             SET  due_date=%s
                           WHERE  id_crcBORROWER=%s and status='on loan'
                           """, (new_due_date, borrower_id)))

def get_queue_request(recid):
    """
    recid: identify the record. It is also the primary key of
           the table bibrec.
    """
    res = run_sql(""" select id
                      from crcLOANREQUEST
                      where id_bibrec=%s and (status='pending' or status='waiting')
                  """, (recid, ))

    return res

def get_recid_borrower_loans(borrower_id):
    """
    borrower_id: identify the borrower. It is also the primary key of
                 the table crcBORROWER.
    """

    res = run_sql(""" select id, id_bibrec, barcode
                      from crcLOAN
                      where id_crcBORROWER=%s and
                            status != 'returned'and
                            type != 'ill'
                  """, (borrower_id, ))


    return res

def update_request_barcode(barcode, request_id):
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
                  select id,
                         id_bibrec,
                         DATE_FORMAT(request_date,'%%Y-%%m-%%d'),
                         status
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
    recid: Invenio record identifier. The number of copies
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

    if res:
        return res[0][0]
    else:
        return None

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

    run_sql("""insert into crcBORROWER (name,
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

    if res:
        return res[0][0]
    else:
        return None

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

    if res:
        return res[0][0]
    else:
        return None

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

    if res:
        return res[0][0]
    else:
        return None

def get_pdf_request_data(status):
    """
    status: request status.
    """
    res = run_sql("""SELECT DISTINCT
                            lr.id_bibrec,
                            bor.name,
                            lib.name,
                            it.location,
                            DATE_FORMAT(lr.period_of_interest_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.period_of_interest_to,'%%Y-%%m-%%d'),
                            lr.request_date
                     FROM   crcLOANREQUEST lr,
                            crcBORROWER bor,
                            crcITEM it,
                            crcLIBRARY lib
                     WHERE  lr.id_crcBORROWER=bor.id AND
                            it.id_bibrec=lr.id_bibrec AND
                            lib.id = it.id_crcLIBRARY AND
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

    if res:
        return res[0]
    else:
        return None

def get_borrower_data(borrower_id):
    """
    Get the borrower's information (name, address and email).
    borrower_id: identify the borrower. The data associate
                 to this borrower will be retrieved. It is also
                 the primary key of the crcBORROWER table.
    """

    res = run_sql("""select name,
                            address,
                            mailbox,
                            email
                     from   crcBORROWER
                     where  id=%s""",
                  (borrower_id, ))

    if res:
        return res[0]
    else:
        return None

def update_borrower_info(borrower_id, name, email, phone, address, mailbox):
    """
    Update borrower info.

    borrower_id: identify the borrower. It is also the primary key of
                 the table crcBORROWER.
    """
    return int(run_sql("""update crcBORROWER
                             set name=%s,
                                 email=%s,
                                 phone=%s,
                                 address=%s,
                                 mailbox=%s
                          where  id=%s""",
                       (name, email, phone, address, mailbox, borrower_id)))

def add_new_library(name, email, phone, address, lib_type, notes):
    """
    Add a new Library.
    """

    run_sql("""insert into crcLIBRARY (name, email, phone,
                                       address, type, notes)
                           values (%s, %s, %s, %s, %s, %s)""",
            (name, email, phone, address, lib_type, notes))

def search_library_by_name(string):
    """
    string: search pattern.
    """

    res = run_sql("""select id, name
                     from crcLIBRARY
                     where name regexp %s
                     """, (string, ))

    return res

def search_library_by_email(string):
    """
    string: search pattern.
    """

    res = run_sql("""select id, name
                     from crcLIBRARY
                     where email regexp %s
                     """, (string, ))
    return res

def get_all_libraries():
    """
    """
    res = run_sql("""select id, name
                       from crcLIBRARY""")

    return res

def update_library_info(library_id, name, email, phone, address):
    """
    Update library information.

    library_id: identify the library. It is also the primary key of
                the table crcLIBRARY.
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
                       from crcLIBRARY""")
                      #where type<>'external' """)

    return res

def get_library_name(library_id):
    """
    Get Library's name.

    library_id: identify the library. It is also the primary key of
                the table crcLIBRARY.
    """

    res = run_sql("""select name
                     from   crcLIBRARY
                     where  id=%s""",
                  (library_id, ))

    if res:
        return res[0][0]
    else:
        return None

def add_new_copy(barcode, recid, library_id, collection, location, description,
                 loan_period, status):

    """
    Add a new copy

    barcode: identify the item. It is the primary key of the table
             crcITEM.

    recid: identify the record. It is also the primary key of
       the table bibrec.

    library_id: identify the library. It is also the primary key of
                the table crcLIBRARY.
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

    barcode: identify the item. It is the primary key of the table
             crcITEM.
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

    if res:
        return res[0]
    else:
        return None

def update_item_info(barcode, library_id, collection, location, description,
                 loan_period, status):
    """
    Update item's information.

    barcode: identify the item. It is the primary key of the table
             crcITEM.

    library_id: identify the library. It is also the primary key of
                the table crcLIBRARY.
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

    library_id: identify the library. It is also the primary key of
                the table crcLIBRARY.
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
    library_id: identify the library. The data associate
                 to this library will be retrieved. It is also
                 the primary key of the crcLIBRARY table.
    """

    res = run_sql("""select notes
                     from   crcLIBRARY
                     where  id=%s""",
                  (library_id, ))

    if res:
        return res[0][0]
    else:
        return None

def add_new_library_note(new_note, library_id):
    """
    Add a new borrower's note.
    new_note: note who will be added.
    library_id: identify the borrower. A new note will be
                 associate to this borrower. It is also
                 the primary key of the crcBORROWER table.
    """
    run_sql("""update crcLIBRARY
               set notes=concat(notes,%s)
               where id=%s;
                """, (new_note, library_id))

def get_borrower_data_by_name(name):
    """
    Retrieve borrower's data by name.
    """

    res = run_sql("""select id, name, email, phone,
                            address, mailbox
                       from crcBORROWER
                      where name regexp %s order by name""",
                  (name, ))

    return res


def get_borrower_data_by_email(email):
    """
    Retrieve borrower's data by email.
    """

    res = run_sql("""select id, name, email, phone,
                            address, mailbox
                       from crcBORROWER
                      where email regexp %s""",
                  (email, ))

    return res

def get_borrower_data_by_id(borrower_id):
    """
    Retrieve borrower's data by borrower_id.
    """

    res = run_sql("""select id, name, email, phone,
                            address, mailbox
                       from crcBORROWER
                      where id regexp %s""",
                  (borrower_id, ))

    return res

def get_number_requests_per_copy(barcode):
    """
    barcode: identify the item. It is the primary key of the table
         crcITEM.
    """

    res = run_sql("""select count(barcode)
                       from crcLOANREQUEST
                      where barcode=%s and
                            (status != 'done' and status != 'cancelled')""",
                  (barcode, ))

    return res[0][0]


def get_requested_barcode(request_id):
    """
    request_id: identify the hold request. It is also the primary key
                of the table crcLOANREQUEST.
    """

    res = run_sql("""select barcode
                       from crcLOANREQUEST
                      where id=%s""",
                  (request_id, ))

    if res:
        return res[0][0]
    else:
        return None

def get_borrower_recids(borrower_id):
    """
    borrower_id: identify the borrower. It is also the primary key of
                 the table crcBORROWER.
    """

    res = run_sql("""select id_bibrec
                       from crcLOAN
                      where id_crcBORROWER=%s""",
                  (borrower_id,))

    return res

def get_loan_status(loan_id):
    """
    Get loan's status

    loan_id: identify a loan. It is the primery key of the table
             crcLOAN.
    """

    res = run_sql("""select status
                       from crcLOAN
                      where id=%s""",
                  (loan_id, ))

    if res:
        return res[0][0]
    else:
        return None

def get_loan_period(barcode):
    """
    Retrieve the loan period of a book.

    barcode: identify the item. It is the primary key of the table
             crcITEM.
    """

    res = run_sql("""select loan_period
                       from crcITEM
                      where barcode=%s""",
                  (barcode, ))

    if res:
        return res[0][0]
    else:
        return None

def get_loan_infos(loan_id):
    """
    loan_id: identify a loan. It is the primery key of the table
             crcLOAN.
    """

    res =  run_sql("""select l.id_bibrec,
                             l.barcode,
                             DATE_FORMAT(l.loaned_on, '%%Y-%%m-%%d'),
                             DATE_FORMAT(l.due_date, '%%Y-%%m-%%d'),
                             l.status,
                             it.loan_period,
                             it.status
                        from crcLOAN l, crcITEM it, crcLOANREQUEST lr
                        where l.barcode=it.barcode and
                              l.id=%s""",
                   (loan_id, ))

    if res:
        return res[0]
    else:
        return None

def is_item_on_loan(barcode):
    """
    Check if an item is on loan.

    barcode: identify the item. It is the primary key of the table
             crcITEM.
    """

    res = run_sql("""select id
                       from crcLOAN
                      where (status='on loan' or status='expired')
                        and barcode=%s""",
                  (barcode, ))

    try:
        return res[0][0]
    except IndexError:
        return None


def order_new_copy(recid, vendor_id, order_date, cost,
                   status, notes, expected_date):

    """
    Register a new copy that has been ordered.
    """

    run_sql("""insert into crcPURCHASE(id_bibrec, id_crcVENDOR, ordered_date, price,
                                       status, notes, expected_date)
                           values (%s, %s, %s, %s, %s, %s, %s)""",
                                    (recid, vendor_id, order_date, cost,
                                     status, notes, expected_date))

def get_ordered_books():
    """
    Get the list with all the ordered books.
    """

    res = run_sql("""select id, id_bibrec, id_crcVENDOR,
                            DATE_FORMAT(ordered_date,'%Y-%m-%d'),
                            DATE_FORMAT(expected_date, '%Y-%m-%d'),
                            price, status, notes
                       from crcPURCHASE""")

    return res

def get_purchase_notes(purchase_id):
    """
    Get the notes of a purchase.
    library_id: identify the purchase. The data associate
                 to this library will be retrieved. It is also
                 the primary key of the crcPURCHASE table.
    """

    res = run_sql("""select notes
                     from   crcPURCHASE
                     where  id=%s""",
                  (purchase_id, ))

    if res:
        return res[0][0]
    else:
        return None

def update_purchase_notes(purchase_id, purchase_notes):
    """
    """

    run_sql("""update crcPURCHASE
                  set notes=%s
                where id=%s """, (str(purchase_notes), purchase_id))

def add_new_purchase_note(new_note, purchase_id):
    """
    Add a new purchase's note.
    new_note: note who will be added.
    library_id: identify the purchase. A new note will be
                 associate to this purchase. It is also
                 the primary key of the crcPURCHASE table.
    """
    run_sql("""update crcPURCHASE
               set notes=concat(notes,%s)
               where id=%s;
                """, (new_note, purchase_id))



def ill_register_request(item_info, borrower_id, period_of_interest_from,
                         period_of_interest_to, status, additional_comments,
                         only_edition, request_type):

    """
    """

    run_sql("""insert into crcILLREQUEST(id_crcBORROWER, period_of_interest_from,
                                         period_of_interest_to, status, item_info,
                                         borrower_comments, only_this_edition, request_type)
                           values (%s, %s, %s, %s, %s, %s, %s, %s)""",
                                    (borrower_id, period_of_interest_from, period_of_interest_to,
                                     status, str(item_info), additional_comments, only_edition, request_type))


def ill_register_request_on_desk(borrower_id, item_info, period_of_interest_from,
                                 period_of_interest_to, status, notes,
                                 only_edition, request_type):

    """
    """

    run_sql("""insert into crcILLREQUEST(id_crcBORROWER, period_of_interest_from,
                                         period_of_interest_to, status, item_info,
                                         only_this_edition, library_notes, request_type )
                           values (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (borrower_id, period_of_interest_from, period_of_interest_to, status,
             str(item_info), only_edition, notes, request_type))

def get_ill_requests(status):
    """
    """

    all_of_them = """select ill.id, ill.id_crcBORROWER, bor.name,
                      ill.id_crcLIBRARY, ill.status,
                      DATE_FORMAT(ill.period_of_interest_from,'%Y-%m-%d'),
                      DATE_FORMAT(ill.period_of_interest_to,'%Y-%m-%d'),
                      ill.item_info, ill.request_type
                 from crcILLREQUEST ill, crcBORROWER bor
                where ill.id_crcBORROWER=bor.id order by ill.id desc"""


    query = """select ill.id, ill.id_crcBORROWER, bor.name,
                      ill.id_crcLIBRARY, ill.status,
                      DATE_FORMAT(ill.period_of_interest_from,'%%Y-%%m-%%d'),
                      DATE_FORMAT(ill.period_of_interest_to,'%%Y-%%m-%%d'),
                      ill.item_info, ill.request_type
                 from crcILLREQUEST ill, crcBORROWER bor
                where ill.id_crcBORROWER=bor.id and ill.status='%s'
                order by ill.id desc""" % (status)

    if status == None:
        res = run_sql(all_of_them)
    else:
        res = run_sql(query)

    return res


def search_ill_requests_title(title, date_from, date_to):

    query = """select ill.id, ill.id_crcBORROWER, bor.name,
                      ill.id_crcLIBRARY, ill.status,
                      DATE_FORMAT(ill.period_of_interest_from,'%%Y-%%m-%%d'),
                      DATE_FORMAT(ill.period_of_interest_to,'%%Y-%%m-%%d'),
                      ill.item_info, ill.request_type
                 from crcILLREQUEST ill, crcBORROWER bor
                where ill.id_crcBORROWER=bor.id
                      and ill.item_info like '%%%s%%'
                      and DATE_FORMAT(ill.request_date,'%%Y-%%m-%%d') >= '%s'
                      and DATE_FORMAT(ill.request_date,'%%Y-%%m-%%d') <= '%s'
                order by ill.id desc""" % (title, date_from, date_to)

    return run_sql(query)


def search_ill_requests_id(reqid, date_from, date_to):

    query = """select ill.id, ill.id_crcBORROWER, bor.name,
                      ill.id_crcLIBRARY, ill.status,
                      DATE_FORMAT(ill.period_of_interest_from,'%%Y-%%m-%%d'),
                      DATE_FORMAT(ill.period_of_interest_to,'%%Y-%%m-%%d'),
                      ill.item_info, ill.request_type
                 from crcILLREQUEST ill, crcBORROWER bor
                where ill.id_crcBORROWER=bor.id
                      and ill.id = %s
                      and DATE_FORMAT(ill.request_date,'%%Y-%%m-%%d') >= '%s'
                      and DATE_FORMAT(ill.request_date,'%%Y-%%m-%%d') <= '%s'
                order by ill.id desc""" % (reqid, date_from, date_to)

    return run_sql(query)

def get_ill_request_details(ill_request_id):
    """
    """

    res = run_sql("""select id_crcLIBRARY,
                            DATE_FORMAT(request_date,'%%Y-%%m-%%d'),
                            DATE_FORMAT(expected_date,'%%Y-%%m-%%d'),
                            DATE_FORMAT(arrival_date,'%%Y-%%m-%%d'),
                            DATE_FORMAT(due_date,'%%Y-%%m-%%d'),
                            DATE_FORMAT(return_date,'%%Y-%%m-%%d'),
                            cost,
                            barcode,
                            library_notes,
                            status
                       from crcILLREQUEST
                      where id=%s""", (ill_request_id, ))

    if res:
        return res[0]
    else:
        return None

#def get_ill_borrower_request(ill_request_id)
def get_ill_request_borrower_details(ill_request_id):
    """
    """

    res = run_sql("""select ill.id_crcBORROWER, bor.name, bor.email, bor.mailbox,
                            DATE_FORMAT(ill.period_of_interest_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(ill.period_of_interest_to,'%%Y-%%m-%%d'),
                            ill.item_info, ill.borrower_comments,
                            ill.only_this_edition, request_type
                       from crcILLREQUEST ill, crcBORROWER bor
                      where ill.id_crcBORROWER=bor.id and ill.id=%s""", (ill_request_id, ))

    if res:
        return res[0]
    else:
        return None

def get_ill_item_received(ill_request_id):
    """
    """

    res = run_sql("""select id_crcLIBRARY,
                            DATE_FORMAT(request_date,'%%Y-%%m-%%d'),
                            DATE_FORMAT(expected_date,'%%Y-%%m-%%d'),
                            library_notes
                       from crcILLREQUEST
                      where id=%s""", (ill_request_id, ))

    if res:
        return res[0]
    else:
        return None

def get_ill_item_returned(ill_request_id):
    """
    """

    res = run_sql("""select id_crcLIBRARY,
                            DATE_FORMAT(request_date,'%%Y-%%m-%%d'),
                            DATE_FORMAT(expected_date,'%%Y-%%m-%%d'),
                            DATE_FORMAT(arrival_date,'%%Y-%%m-%%d'),
                            DATE_FORMAT(due_date,'%%Y-%%m-%%d'),
                            barcode,
                            library_notes
                       from crcILLREQUEST
                      where id=%s""", (ill_request_id, ))

    if res:
        return res[0]
    else:
        return None

def get_ill_request_closed(ill_request_id):
    """
    """

    res = run_sql("""select id_crcLIBRARY,
                            DATE_FORMAT(request_date,'%%Y-%%m-%%d'),
                            DATE_FORMAT(expected_date,'%%Y-%%m-%%d'),
                            DATE_FORMAT(arrival_date,'%%Y-%%m-%%d'),
                            DATE_FORMAT(due_date,'%%Y-%%m-%%d'),
                            DATE_FORMAT(return_date,'%%Y-%%m-%%d'),
                            cost,
                            barcode,
                            library_notes
                       from crcILLREQUEST
                      where id=%s""", (ill_request_id, ))

    if res:
        return res[0]
    else:
        return None

def get_external_libraries():
    """
    Get Libraries
    """

    res = run_sql("""select id, name
                       from crcLIBRARY
                      where type='external'
                """)

    return res


def update_ill_request(ill_request_id, library_id, request_date, expected_date,
                          arrival_date, due_date, return_date, status, cost, barcode,
                          library_notes):
    """
    Update an ILL request.
    """

    run_sql("""update crcILLREQUEST
                  set id_crcLIBRARY=%s,
                      request_date=%s,
                      expected_date=%s,
                      arrival_date=%s,
                      due_date=%s,
                      return_date=%s,
                      status=%s,
                      cost=%s,
                      barcode=%s,
                      library_notes=%s
                where id=%s""",
            (library_id, request_date, expected_date,
             arrival_date, due_date, return_date, status, cost,
             barcode, library_notes, ill_request_id))

def update_ill_request_status(ill_request_id, new_status):

    run_sql("""update crcILLREQUEST
                  set status=%s
                where id=%s""", (new_status, ill_request_id))

def update_ill_request_sent(ill_request_id, ill_status, library_id,
                            request_date, expected_date,
                            cost_format, barcode, library_notes):
    """
    """

    run_sql("""update crcILLREQUEST
                  set status=%s,
                      id_crcLIBRARY=%s,
                      request_date=%s,
                      expected_date=%s,
                      cost=%s,
                      barcode=%s,
                      library_notes=%s
                where id=%s""", (ill_status, library_id,
                                 request_date, expected_date,
                                 cost_format, barcode, library_notes,
                                 ill_request_id))

def update_ill_request_cancelled(ill_request_id, ill_status,
                                 cost_format, barcode, library_notes):
    """
    """

    run_sql("""update crcILLREQUEST
                  set status=%s,
                      cost=%s,
                      barcode=%s,
                      library_notes=%s
                where id=%s""", (ill_status, cost_format,
                                 barcode, library_notes,
                                 ill_request_id))

def update_ill_item_received(ill_request_id, ill_status,
                             arrival_date, due_date,
                             cost_format, barcode, library_notes):
    """
    """

    run_sql("""update crcILLREQUEST
                  set status=%s,
                      arrival_date=%s,
                      due_date=%s,
                      cost=%s,
                      barcode=%s,
                      library_notes=%s
                where id=%s""", (ill_status,
                                 arrival_date, due_date,
                                 cost_format, barcode, library_notes,
                                 ill_request_id))

def update_ill_item_returned(ill_request_id, ill_status,
                             return_date, cost_format,
                             library_notes):
    """
    """

    run_sql("""update crcILLREQUEST
                  set status=%s,
                      return_date=%s,
                      cost=%s,
                      library_notes=%s
                where id=%s""", (ill_status, return_date,
                                 cost_format, library_notes,
                                 ill_request_id))

def update_ill_request_closed(ill_request_id, ill_status, library_notes):
    """
    """

    run_sql("""update crcILLREQUEST
                  set status=%s,
                      library_notes=%s
                where id=%s""", (ill_status,
                                 library_notes,
                                 ill_request_id))

def get_order_details(purchase_id):
    """
    """

    res = run_sql("""select id, id_bibrec, id_crcVENDOR,
                            DATE_FORMAT(ordered_date,'%%Y-%%m-%%d'),
                            DATE_FORMAT(expected_date,'%%Y-%%m-%%d'),
                            price, status, notes
                       from crcPURCHASE
                      where id=%s""", (purchase_id, ))

    if res:
        return res[0]
    else:
        return None

def uptade_purchase(purchase_id, recid, vendor_id, price,
                    status, order_date, expected_date, notes):

    """
    """

    run_sql("""update crcPURCHASE
                  set id_bibrec=%s,
                      id_crcVENDOR=%s,
                      ordered_date=%s,
                      expected_date=%s,
                      price=%s,
                      status=%s,
                      notes=%s
                where id=%s""",
            (recid, vendor_id, order_date, expected_date, price, status,
             notes, purchase_id))

def add_new_vendor(name, email, phone, address, notes):
    """
    Add a new vendor.
    """

    run_sql("""insert into crcVENDOR (name, email, phone,
                                      address, notes)
                           values (%s, %s, %s, %s, %s)""",
            (name, email, phone, address, notes))

def search_vendor_by_name(string):
    """
    string: search pattern.
    """

    res = run_sql("""select id, name
                     from crcVENDOR
                     where name regexp %s
                     """, (string, ))

    return res

def search_vendor_by_email(string):
    """
    string: search pattern.
    """

    res = run_sql("""select id, name
                     from crcVENDOR
                     where email regexp %s
                     """, (string, ))

    return res

def get_all_vendors():
    """
    """
    res = run_sql("""select id, name
                       from crcVENDOR""")
    return res

def update_vendor_info(vendor_id, name, email, phone, address):
    """
    Update vendor information.

    vendor_id: identify the vendor. It is also the primary key of
                the table crcVENDOR.
    """
    return int(run_sql("""update crcVENDOR
                             set name=%s,
                                 email=%s,
                                 phone=%s,
                                 address=%s
                          where  id=%s""",
                       (name, email, phone, address, vendor_id)))

def get_vendors():
    """
    Get vendors
    """

    res = run_sql("""select id, name
                       from crcVENDOR""")

    return res

def get_vendor_details(vendor_id):
    """
    vendor_id: identify the vendor. It is also the primary key of
            the table crcVENDOR.
    """
    res = run_sql("""select id, name, address, email, phone, notes
                     from crcVENDOR
                     where id=%s;
                     """, (vendor_id, ))

    if res:
        return res[0]
    else:
        return None

def get_vendor_notes(vendor_id):
    """
    Get the notes of a vendor.
    vendor_id: identify the vendor. The data associate
               to this vendor will be retrieved. It is also
               the primary key of the crcVENDOR table.
    """

    res = run_sql("""select notes
                     from   crcVENDOR
                     where  id=%s""",
                  (vendor_id, ))

    if res:
        return res[0][0]
    else:
        return None

def add_new_vendor_note(new_note, vendor_id):
    """
    Add a new vendor's note.
    new_note:  note who will be added.
    vendor_id: identify the vendor. A new note will be
               associate to this vendor. It is also
               the primary key of the crcVENDOR table.
    """
    run_sql("""update crcVENDOR
               set notes=concat(notes,%s)
               where id=%s;
                """, (new_note, vendor_id))

def get_list_of_vendors():
    """
    Get vendors
    """

    res = run_sql("""select id, name
                     from   crcVENDOR""")

    return res

def get_vendor_name(vendor_id):
    """
    Get Vendor's name.

    vendor_id: identify the vendor. It is also the primary key of
                the table crcVENDOR.
    """

    res = run_sql("""select name
                     from   crcVENDOR
                     where  id=%s""",
                  (vendor_id, ))

    if res:
        return res[0][0]
    else:
        return None

def get_ill_request_notes(ill_request_id):
    """
    """

    res = run_sql("""select library_notes
                     from   crcILLREQUEST
                     where  id=%s""",
                  (ill_request_id, ))

    if res:
        return res[0][0]
    else:
        return None

def update_ill_request_notes(ill_request_id, library_notes):
    """
    """

    run_sql("""update crcILLREQUEST
                  set library_notes=%s
                where id=%s""", (str(library_notes), ill_request_id))

def get_ill_borrower(ill_request_id):
    """
    """

    res = run_sql("""select id_crcBORROWER
                       from crcILLREQUEST
                      where id=%s""", (ill_request_id, ))

    if res:
        return res[0][0]
    else:
        return None

def get_ill_barcode(ill_request_id):
    """
    """

    res = run_sql("""select barcode
                       from crcILLREQUEST
                      where id=%s""", (ill_request_id, ))

    if res:
        return res[0][0]
    else:
        return None

def update_ill_loan_status(borrower_id, barcode, return_date, loan_type):
    """
    """

    run_sql("""update crcLOAN
               set status = 'returned',
                   returned_on = %s
               where id_crcBORROWER = %s
                 and barcode = %s
                 and type = %s""",
            (return_date, borrower_id, barcode, loan_type))

def get_recid(barcode):
    """
    Get the id bibrec.

    barcode: identify the item. It is the primary key of the table
             crcITEM.
    """

    res = run_sql("""select id_bibrec
                       from crcITEM
                      where barcode=%s""",
                  (barcode, ))

    try:
        return res[0]
    except IndexError:
        return None

def get_ill_requests_details(borrower_id):
    """
    """

    res = run_sql("""select id, item_info, id_crcLIBRARY,
                            DATE_FORMAT(request_date,'%%Y-%%m-%%d'),
                            DATE_FORMAT(expected_date,'%%Y-%%m-%%d'),
                            DATE_FORMAT(arrival_date,'%%Y-%%m-%%d'),
                            DATE_FORMAT(due_date,'%%Y-%%m-%%d'),
                            status, library_notes
                       from crcILLREQUEST
                      where id_crcBORROWER=%s and status!='document received, request closed' """, (borrower_id, ))

    return res

def bor_ill_historical_overview(borrower_id):
    """
    """

    res = run_sql("""select id, item_info, id_crcLIBRARY,
                            DATE_FORMAT(request_date,'%%Y-%%m-%%d'),
                            DATE_FORMAT(expected_date,'%%Y-%%m-%%d'),
                            DATE_FORMAT(arrival_date,'%%Y-%%m-%%d'),
                            DATE_FORMAT(due_date,'%%Y-%%m-%%d'),
                            status, library_notes
                       from crcILLREQUEST
                      where id_crcBORROWER=%s and status='document received, request closed'"""
                  , (borrower_id, ))

    return res

def get_ill_notes(ill_id):
    """
    """

    res = run_sql("""select library_notes
                     from   crcILLREQUEST
                     where  id=%s""",
                  (ill_id, ))

    if res:
        return res[0][0]
    else:
        return None

def update_ill_notes(ill_id, ill_notes):
    """
    """

    run_sql("""update crcILLREQUEST
                  set library_notes=%s
                where id=%s """, (str(ill_notes), ill_id))

def is_on_loan(barcode):
    """
    """

    res = run_sql("""select id
                       from crcLOAN
                      where barcode=%s and status='on loan'
                      """, (barcode, ))

    if res:
        return True
    else:
        return False

def is_requested(barcode):
    """
    """

    res = run_sql("""select id
                       from crcLOANREQUEST
                      where barcode=%s and
                            (status = 'pending' or status = 'waiting')
                    """, (barcode, ))

    try:
        return res
    except IndexError:
        return None

def get_lib_location(barcode):
    """
    """

    res = run_sql("""select id_crcLIBRARY, location
                       from crcITEM
                      where barcode=%s""",
                  (barcode, ))

    if res:
        return res[0]
    else:
        return None

def get_barcodes(recid):
    """
    """

    res = run_sql("""select barcode
                       from crcITEM
                      where id_bibrec=%s""",
                  (recid, ))

    barcodes = []
    for i in range(len(res)):
        barcodes.append(res[i][0])

    return barcodes

def barcode_in_use(barcode):
    """
    """

    res = run_sql("""select id_bibrec
                       from crcITEM
                      where barcode=%s""",
                  (barcode, ))

    if res:
        return True
    else:
        return False

def get_expired_loans_with_requests():
    """
    """
    res = run_sql("""SELECT DISTINCT
                            lr.id,
                            lr.id_bibrec,
                            lr.id_crcBORROWER,
                            it.id_crcLIBRARY,
                            it.location,
                            DATE_FORMAT(lr.period_of_interest_from,'%Y-%m-%d'),
                            DATE_FORMAT(lr.period_of_interest_to,'%Y-%m-%d'),
                            lr.request_date
                     FROM   crcLOANREQUEST lr,
                            crcITEM it,
                            crcLOAN l
                     WHERE  it.barcode=lr.barcode AND
                            lr.barcode=l.barcode AND
                            (lr.status='pending' or lr.status='waiting') AND
                            l.status='on loan'
                            and l.due_date < CURDATE()
                            ORDER BY lr.request_date;
                  """)
    return res

def get_total_of_loans():
    """
    """

    res = run_sql("""select count(id)
                       from crcLOAN
                      where status='on loan';""")

    return res[0][0]

def update_borrower_notes(borrower_id, borrower_notes):
    """
    """
    run_sql("""update crcBORROWER
                  set notes=%s
                where id=%s """, (str(borrower_notes), borrower_id))

def get_loan_notes(loan_id):
    """
    """

    res = run_sql("""select notes
                     from   crcLOAN
                     where  id=%s""",
                  (loan_id, ))

    if res:
        return res[0][0]
    else:
        return None

def update_loan_notes(loan_id, loan_notes):
    """
    """
    run_sql("""update crcLOAN
                  set notes=%s
                where id=%s """, (str(loan_notes), loan_id))

def update_library_notes(library_id, library_notes):
    """
    """
    run_sql("""update crcLIBRARY
                  set notes=%s
                where id=%s """, (str(library_notes), library_id))

def get_ill_book_info(ill_request_id):
    """
    """

    res = run_sql("""select item_info
                       from crcILLREQUEST
                      where id=%s""",
                  (ill_request_id, ))

    if res:
        return res[0][0]
    else:
        return None

def get_ill_ids():
    """
    """

    res = run_sql("""select id
                       from crcILLREQUEST
                      where status!='document received, request closed'""")

    return res

def get_copies_status(recid):
    """
    """

    res = run_sql("""select status
                       from crcITEM
                      where id_bibrec=%s""",
                  (recid, ))

    if res:
        return res[0]
    else:
        return None

def get_loan_recid(loan_id):
    """
    """

    res = run_sql("""select id_bibrec
                       from crcLOAN
                      where id=%s""",
                  (loan_id, ))

    if res:
        return res[0][0]
    else:
        return None

def delete_ill_req():
    run_sql(""" DELETE FROM crcILLREQUEST where 1=1""")
