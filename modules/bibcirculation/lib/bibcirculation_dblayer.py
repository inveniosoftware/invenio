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
   Every db-related function of the bibcirculation module.
   The methods are positioned by grouping into logical
   categories ('Loans', 'Returns', 'Loan requests', 'ILLs',
   'Libraries', 'Vendors' ...)
   This positioning should be maintained and when necessary,
   improved for readability, as and when additional methods are
   added. When applicable, methods should be renamed, refactored
   and appropriate documentation added.

   Currently, the same table 'crcILLREQUEST' is used for the ILLs,
   purchases as well as proposals.

"""

__revision__ = "$Id$"

from invenio.dbquery import run_sql
from invenio.bibcirculation_config import \
    CFG_BIBCIRCULATION_ITEM_STATUS_ON_LOAN, \
    CFG_BIBCIRCULATION_LOAN_STATUS_ON_LOAN, \
    CFG_BIBCIRCULATION_LOAN_STATUS_EXPIRED, \
    CFG_BIBCIRCULATION_LOAN_STATUS_RETURNED, \
    CFG_BIBCIRCULATION_REQUEST_STATUS_WAITING, \
    CFG_BIBCIRCULATION_REQUEST_STATUS_PENDING, \
    CFG_BIBCIRCULATION_REQUEST_STATUS_PROPOSED, \
    CFG_BIBCIRCULATION_REQUEST_STATUS_DONE, \
    CFG_BIBCIRCULATION_REQUEST_STATUS_CANCELLED, \
    CFG_BIBCIRCULATION_ILL_STATUS_NEW, \
    CFG_BIBCIRCULATION_ILL_STATUS_REQUESTED, \
    CFG_BIBCIRCULATION_ILL_STATUS_ON_LOAN, \
    CFG_BIBCIRCULATION_ILL_STATUS_RETURNED, \
    CFG_BIBCIRCULATION_ILL_STATUS_RECEIVED, \
    CFG_BIBCIRCULATION_ACQ_STATUS_NEW, \
    CFG_BIBCIRCULATION_ACQ_STATUS_ON_ORDER, \
    CFG_BIBCIRCULATION_ACQ_STATUS_PARTIAL_RECEIPT, \
    CFG_BIBCIRCULATION_ACQ_STATUS_RECEIVED, \
    CFG_BIBCIRCULATION_ACQ_STATUS_CANCELLED, \
    CFG_BIBCIRCULATION_PROPOSAL_STATUS_NEW, \
    CFG_BIBCIRCULATION_PROPOSAL_STATUS_ON_ORDER, \
    CFG_BIBCIRCULATION_PROPOSAL_STATUS_RECEIVED, \
    CFG_BIBCIRCULATION_PROPOSAL_STATUS_PUT_ASIDE, \
    CFG_BIBCIRCULATION_LIBRARY_TYPE_INTERNAL, \
    CFG_BIBCIRCULATION_LIBRARY_TYPE_EXTERNAL, \
    CFG_BIBCIRCULATION_LIBRARY_TYPE_MAIN, \
    CFG_BIBCIRCULATION_LIBRARY_TYPE_HIDDEN




###
### Loan Requests related functions ###
###




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
    """
    res = run_sql("""INSERT INTO crcLOANREQUEST(id_crcBORROWER,
                                                id_bibrec,
                                                barcode,
                                                period_of_interest_from,
                                                period_of_interest_to,
                                                status,
                                                request_date)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    """, (borrower_id, recid, barcode, date_from,
                          date_to, status))

    return res

def has_loan_request(borrower_id, recid, ill=0):

    from invenio.bibcirculation_utils import looks_like_dictionary

    if ill == 0:
        return run_sql("""
                      SELECT id
                      FROM   crcLOANREQUEST
                      WHERE  id_crcBORROWER=%s and
                             id_bibrec=%s and
                             status in (%s, %s, %s)""",
                       (borrower_id, recid,
                        CFG_BIBCIRCULATION_REQUEST_STATUS_PENDING,
                        CFG_BIBCIRCULATION_REQUEST_STATUS_WAITING,
                        CFG_BIBCIRCULATION_REQUEST_STATUS_PROPOSED
                        )) != ()
    else:
        res = run_sql("""
              SELECT item_info
              FROM   crcILLREQUEST
              WHERE  id_crcBORROWER=%s and
                     request_type=%s and
                     status in (%s, %s, %s)""",
               (borrower_id, 'book',
                CFG_BIBCIRCULATION_ILL_STATUS_NEW,
                CFG_BIBCIRCULATION_ILL_STATUS_REQUESTED,
                CFG_BIBCIRCULATION_ILL_STATUS_ON_LOAN
                ))
        for record in res:
            if looks_like_dictionary(record[0]):
                item_info = eval(record[0])
                try:
                    if str(recid) == str(item_info['recid']): return True
                except KeyError:
                    continue
        return False

def is_requested(barcode):

    res = run_sql("""SELECT id
                       FROM crcLOANREQUEST
                      WHERE barcode=%s
                        AND (status = %s or status = %s)
                    """, (barcode,
                          CFG_BIBCIRCULATION_REQUEST_STATUS_PENDING,
                          CFG_BIBCIRCULATION_REQUEST_STATUS_WAITING))

    try:
        return res
    except IndexError:
        return None

def is_doc_already_requested(recid, barcode, borrower_id):
    """
    Check if the borrower already has a waiting/pending loan request or
    a proposal, or a loan on some item of the record.
    """
    multi_volume_book = False
    if get_item_description(barcode).strip() not in ('', '-'):
        multi_volume_book = True

    reqs_on_rec = run_sql("""SELECT id, barcode
                       FROM crcLOANREQUEST
                      WHERE id_bibrec=%s
                        AND id_crcBORROWER = %s
                        AND status in (%s, %s, %s)
                    """, (recid, borrower_id,
                          CFG_BIBCIRCULATION_REQUEST_STATUS_PENDING,
                          CFG_BIBCIRCULATION_REQUEST_STATUS_WAITING,
                          CFG_BIBCIRCULATION_REQUEST_STATUS_PROPOSED,
                          ))
    if reqs_on_rec != () and not multi_volume_book: return True
    for req in reqs_on_rec:
        if req[1] == barcode: return True

    loans_on_rec = run_sql("""SELECT id, barcode
                       FROM crcLOAN
                      WHERE id_bibrec=%s
                        AND id_crcBORROWER = %s
                        AND status in (%s, %s)
                    """, (recid, borrower_id,
                          CFG_BIBCIRCULATION_LOAN_STATUS_ON_LOAN,
                          CFG_BIBCIRCULATION_LOAN_STATUS_EXPIRED
                          ))
    if loans_on_rec != () and not multi_volume_book: return True
    for loan in loans_on_rec:
        if loan[1] == barcode: return True

    return False

def cancel_request(request_id, borrower_id=None, recid=None):
    """
    Cancel a hold request identified with the request_id. If it is None,
    cancel the hold request identified with (borrower_id, recid), if both
    are not None.
    """
    if request_id:
        run_sql("""UPDATE crcLOANREQUEST
                      SET status=%s
                    WHERE id=%s
                """, (CFG_BIBCIRCULATION_REQUEST_STATUS_CANCELLED, request_id))

    elif borrower_id and recid:
        run_sql("""UPDATE crcLOANREQUEST
                      SET status=%s
                    WHERE id_crcBORROWER=%s and
                          id_bibrec=%s and
                          status in (%s, %s, %s)""",
                    (CFG_BIBCIRCULATION_REQUEST_STATUS_CANCELLED,
                     borrower_id, recid,
                     CFG_BIBCIRCULATION_REQUEST_STATUS_PENDING,
                     CFG_BIBCIRCULATION_REQUEST_STATUS_PROPOSED,
                     CFG_BIBCIRCULATION_REQUEST_STATUS_WAITING
                     ))

def tag_requests_as_done(user_id, barcode=None, recid=None):

    if barcode:
        run_sql("""UPDATE crcLOANREQUEST
                  SET status=%s
                WHERE barcode=%s
                  and id_crcBORROWER=%s
                """, (CFG_BIBCIRCULATION_REQUEST_STATUS_DONE,
                      barcode, user_id))

    elif recid:
        run_sql("""UPDATE crcLOANREQUEST
                  SET status=%s
                WHERE id_bibrec=%s
                  and id_crcBORROWER=%s
                """, (CFG_BIBCIRCULATION_REQUEST_STATUS_DONE,
                      recid, user_id))


def get_requests(recid, description, status):
    """
    Get the number of requests of a record.

    @param recid: identify the record. Primary key of bibrec.
    @type recid: int

    @param status: identify the status.
    @type status: string

    @return number of requests (int)
    """
    # Get all the barcodes of the items belonging to the same record and with the same description.
    barcodes = tuple(rec[0] for rec in run_sql("""SELECT barcode FROM crcITEM WHERE description=%s
                                                  AND id_bibrec=%s""", (description, recid)))

    query = """SELECT  id, DATE_FORMAT(period_of_interest_from,'%%Y-%%m-%%d'),
                             DATE_FORMAT(period_of_interest_to,'%%Y-%%m-%%d'),
                             DATE_FORMAT(request_date,'%%Y-%%m-%%d')
                        FROM crcLOANREQUEST
                       WHERE period_of_interest_from <= NOW()
                         AND period_of_interest_to >= NOW()
                         AND id_bibrec=%s
                         AND status='%s' """% (recid, status)


    if len(barcodes) == 1:
        query += """AND barcode='%s' ORDER BY request_date""" % barcodes[0]
    elif len(barcodes) > 1:
        query += """AND barcode in %s ORDER BY request_date""" % (barcodes,)
    else:
        query += """ORDER BY request_date"""

    return run_sql(query)

def get_all_requests():
    """
    Retrieve all requests.
    """
    res = run_sql("""SELECT lr.id,
                            bor.id,
                            bor.name,
                            lr.id_bibrec,
                            lr.status,
                            DATE_FORMAT(lr.period_of_interest_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.period_of_interest_to,'%%Y-%%m-%%d'),
                            lr.request_date
                     FROM   crcLOANREQUEST lr,
                            crcBORROWER bor
                     WHERE  bor.id = lr.id_crcBORROWER
                       AND  (lr.status=%s OR lr.status=%s)
                       AND  lr.period_of_interest_to >= CURDATE()
                  ORDER BY  lr.request_date
                    """, (CFG_BIBCIRCULATION_REQUEST_STATUS_WAITING,
                          CFG_BIBCIRCULATION_REQUEST_STATUS_PENDING))

    return res

def get_loan_request_details(req_id):

    res = run_sql("""SELECT lr.id_bibrec,
                            bor.name,
                            bor.id,
                            lib.name,
                            it.location,
                            DATE_FORMAT(lr.period_of_interest_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.period_of_interest_to,'%%Y-%%m-%%d'),
                            lr.request_date
                       FROM crcLOANREQUEST lr,
                            crcBORROWER bor,
                            crcITEM it,
                            crcLIBRARY lib
                      WHERE lr.id_crcBORROWER=bor.id AND it.barcode=lr.barcode
                        AND lib.id = it.id_crcLIBRARY
                        AND lr.id=%s
                   """, (req_id, ))

    if res:
        return res[0]
    else:
        return None

def get_loan_request_by_status(status):

    query = """SELECT DISTINCT
                        lr.id,
                        lr.id_bibrec,
                        lr.barcode,
                        bor.name,
                        bor.id,
                        lib.name,
                        it.location,
                        DATE_FORMAT(lr.period_of_interest_from,'%%Y-%%m-%%d'),
                        DATE_FORMAT(lr.period_of_interest_to,'%%Y-%%m-%%d'),
                        lr.request_date
                   FROM crcLOANREQUEST lr,
                        crcBORROWER bor,
                        crcITEM it,
                        crcLIBRARY lib
                  WHERE lr.id_crcBORROWER=bor.id AND it.barcode=lr.barcode AND
                        lib.id = it.id_crcLIBRARY AND lr.status=%s
                        AND lr.period_of_interest_from <= NOW()
                        AND lr.period_of_interest_to >= NOW()
               ORDER BY lr.request_date"""

    res = run_sql(query , (status, ))
    return res

def get_requested_barcode(request_id):
    """
    request_id: identify the hold request. It is also the primary key
                of the table crcLOANREQUEST.
    """

    res = run_sql("""SELECT barcode
                       FROM crcLOANREQUEST
                      WHERE id=%s""",
                  (request_id, ))

    if res:
        return res[0][0]
    else:
        return None

def update_loan_request_status(new_status, request_id=None,
                               barcode=None, borrower_id=None):
    """
    Update the hold request(s) status(es) for an item with the request_id/barcode.
    If the status of the hold request on an item with a particular barcode and
    by a particular borrrower is to be modified, specify the borrower_id too.
    """

    if request_id:
        return int(run_sql("""UPDATE  crcLOANREQUEST
                                 SET  status=%s
                               WHERE  id=%s""",
                       (new_status, request_id)))

    elif barcode and borrower_id:
        return int(run_sql("""UPDATE  crcLOANREQUEST
                                 SET  status=%s
                               WHERE  barcode=%s
                                 AND  id_crcBORROWER=%s""",
                           (new_status, barcode, borrower_id)))

    elif barcode:
        return int(run_sql("""UPDATE  crcLOANREQUEST
                                 SET  status=%s
                               WHERE  barcode=%s""",
                           (new_status, barcode)))

def update_request_barcode(barcode, request_id):
    """
    Update the barcode of a hold request.
    barcode: new barcode (after update). It is also the
             primary key of the crcITEM table.
    request_id: identify the hold request who will be
                cancelled. It is also the primary key of
                the crcLOANREQUEST table.
    """

    run_sql("""UPDATE crcLOANREQUEST
               set barcode = %s
               WHERE id = %s
            """, (barcode, request_id))

def get_pending_loan_request(recid, description):
    """
    Get the pending request for a given recid.

    @param recid: identify the record. Primary key of bibrec.
    @type recid: int

    @param description: Gives the details like volume(if any), etc... of a particular
                        item in the record.
    @type description:  string

    @return list with request_id, borrower_name, recid, status,
            period_of_interest (FROM and to) and request_date.
    """

    # Get all the barcodes of the items belonging to the same record and with the same description.
    barcodes = tuple(rec[0] for rec in run_sql("""SELECT barcode FROM crcITEM WHERE description=%s
                                                  AND id_bibrec=%s""", (description, recid)))

    query = """SELECT lr.id,
                            bor.name,
                            lr.id_bibrec,
                            lr.status,
                            DATE_FORMAT(lr.period_of_interest_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.period_of_interest_to,'%%Y-%%m-%%d'),
                            lr.request_date
                       FROM crcLOANREQUEST lr,
                            crcBORROWER bor
                      WHERE lr.id_crcBORROWER=bor.id
                        AND lr.status='%s'
                        AND lr.id_bibrec=%s
                        AND lr.period_of_interest_from <= NOW()
                        AND lr.period_of_interest_to >= NOW() """% \
                        (CFG_BIBCIRCULATION_REQUEST_STATUS_PENDING, recid)


    if len(barcodes) == 1:
        query += """AND lr.barcode='%s' ORDER BY lr.request_date""" % barcodes[0]
    elif len(barcodes) > 1:
        query += """AND lr.barcode in %s ORDER BY lr.request_date""" % (barcodes,)
    else:
        query += """ORDER BY lr.request_date"""

    return run_sql(query)

def get_queue_request(recid, item_description):
    """
    recid: identify the record. It is also the primary key of
           the table bibrec.
    item_description: Gives the details like volume(if any), etc... of a particular
                      item in the record.
    """

     # Get all the barcodes of the items belonging to the same record and with the same description.
    barcodes = tuple(rec[0] for rec in run_sql("""SELECT barcode FROM crcITEM WHERE description=%s
                                                  AND id_bibrec=%s""", (item_description, recid)))

    query = """SELECT id_crcBORROWER,
                            status,
                            DATE_FORMAT(request_date,'%%Y-%%m-%%d')
                       FROM crcLOANREQUEST
                      WHERE id_bibrec=%s
                        AND (status='%s' or status='%s')
                        AND period_of_interest_from <= NOW()
                        AND period_of_interest_to >= NOW() """% \
                        (recid, CFG_BIBCIRCULATION_REQUEST_STATUS_PENDING,\
                                CFG_BIBCIRCULATION_REQUEST_STATUS_WAITING)


    if len(barcodes) == 1:
        query += """AND barcode='%s' ORDER BY request_date""" % barcodes[0]
    elif len(barcodes) > 1:
        query += """AND barcode in %s ORDER BY request_date""" % (barcodes,)
    else:
        query += """ORDER BY request_date"""

    return run_sql(query)

def get_request_recid(request_id):
    """
    Get the recid of a given request_id

    @param request_id: identify the (hold) request. Primary key of crcLOANREQUEST.
    @type request_id: int

    @return recid
    """
    res = run_sql(""" SELECT id_bibrec
                      FROM crcLOANREQUEST
                      WHERE id=%s
                  """, (request_id, ))

    if res:
        return res[0][0]
    else:
        return None

def get_request_barcode(request_id):
    """
    Get the barcode of a given request_id

    @param request_id: identify the (hold) request. Primary key of crcLOANREQUEST.
    @type request_id: int

    @return barcode
    """
    res = run_sql(""" SELECT barcode
                      FROM crcLOANREQUEST
                      WHERE id=%s
                  """, (request_id, ))

    if res:
        return res[0][0]
    else:
        return None

def get_request_borrower_id(request_id):
    """
    Get the borrower_id of a given request_id

    @param request_id: identify the (hold) request. Primary key of crcLOANREQUEST.
    @type request_id: int

    @return borrower_id
    """

    res = run_sql(""" SELECT id_crcBORROWER
                      FROM crcLOANREQUEST
                      WHERE id=%s
                  """, (request_id, ))

    if res:
        return res[0][0]
    else:
        return None

def get_number_requests_per_copy(barcode):
    """
    barcode: identify the item. It is the primary key of the table
         crcITEM.
    """

    res = run_sql("""SELECT count(barcode)
                       FROM crcLOANREQUEST
                      WHERE barcode=%s and
                            (status != %s and status != %s)""",
                  (barcode, CFG_BIBCIRCULATION_REQUEST_STATUS_DONE,
                   CFG_BIBCIRCULATION_REQUEST_STATUS_CANCELLED))

    return res[0][0]

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
                  """, (status,))
    return res




###
### Loans related functions ###
###




def loan_on_desk_confirm(barcode, borrower_id):
    """
    barcode: identify the item. It is the primary key of the table
             crcITEM.

    borrower_id: identify the borrower. It is also the primary key of
                 the table crcBORROWER.
    """
    res = run_sql("""SELECT it.id_bibrec, bor.name
                       FROM crcITEM it, crcBORROWER bor
                      WHERE it.barcode=%s and bor.id=%s
                  """, (barcode, borrower_id))

    return res

def is_on_loan(barcode):

    res = run_sql("""SELECT id
                       FROM crcLOAN
                      WHERE barcode=%s
                        AND (status=%s or status=%s)
                      """, (barcode,
                            CFG_BIBCIRCULATION_LOAN_STATUS_ON_LOAN,
                            CFG_BIBCIRCULATION_LOAN_STATUS_EXPIRED))

    if res:
        return True
    else:
        return False

def is_item_on_loan(barcode):
    """
    Check if an item is on loan.

    @param barcode: identify the item. It is the primary key of the table crcITEM.
    """

    res = run_sql("""SELECT id
                       FROM crcLOAN
                      WHERE (status=%s or status=%s)
                        and barcode=%s""",
                  (CFG_BIBCIRCULATION_LOAN_STATUS_ON_LOAN,
                   CFG_BIBCIRCULATION_LOAN_STATUS_EXPIRED, barcode))

    try:
        return res[0][0]
    except IndexError:
        return None

def get_loan_infos(loan_id):
    """
    loan_id: identify a loan. It is the primery key of the table
             crcLOAN.
    """

    res =  run_sql("""SELECT l.id_bibrec,
                             l.barcode,
                             DATE_FORMAT(l.loaned_on, '%%Y-%%m-%%d'),
                             DATE_FORMAT(l.due_date, '%%Y-%%m-%%d'),
                             l.status,
                             it.loan_period,
                             it.status
                        FROM crcLOAN l, crcITEM it, crcLOANREQUEST lr
                       WHERE l.barcode=it.barcode and
                             l.id=%s""",
                   (loan_id, ))

    if res:
        return res[0]
    else:
        return None

def get_borrower_id(barcode):
    """
    Get the borrower id who is associated to a loan.

    @param barcode: identify the item. Primary key of crcITEM.
    @type barcode: string

    @return borrower_id or None
    """
    res = run_sql(""" SELECT id_crcBORROWER
                        FROM crcLOAN
                       WHERE barcode=%s and
                             (status=%s or status=%s)""",
                  (barcode, CFG_BIBCIRCULATION_LOAN_STATUS_ON_LOAN,
                   CFG_BIBCIRCULATION_LOAN_STATUS_EXPIRED))
    try:
        return res[0][0]
    except IndexError:
        return None

def get_borrower_loans_barcodes(borrower_id):
    """
    borrower_id: identify the borrower. It is also the primary key of
                 the table crcBORROWER.
    """

    res = run_sql("""SELECT barcode
                       FROM crcLOAN
                      WHERE id_crcBORROWER=%s
                        AND (status=%s OR status=%s)
                         """,
                  (borrower_id, CFG_BIBCIRCULATION_LOAN_STATUS_ON_LOAN,
                   CFG_BIBCIRCULATION_LOAN_STATUS_EXPIRED))

    list_of_barcodes = []
    for bc in res:
        list_of_barcodes.append(bc[0])

    return list_of_barcodes

def new_loan(borrower_id, recid, barcode,
             due_date, status, loan_type, notes):
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
                      values(%s, %s, %s, NOW(), %s, %s ,%s, %s)
                  """, (borrower_id, recid, barcode, due_date,
                        status, loan_type, str(notes)))

    res = run_sql(""" UPDATE crcITEM
                         SET status=%s
                       WHERE barcode=%s""", (status, barcode))

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

def update_loan_status(status, loan_id):
    """
    Update the status of a loan.
    status: new status (after update)
    loan_id: identify the loan who will be updated.
             It is also the primary key of the table
             crcLOAN.
    """
    run_sql("""UPDATE crcLOAN
               set status = %s
               WHERE id = %s""",
            (status, loan_id))

def get_loan_status(loan_id):
    """
    Get loan's status

    loan_id: identify a loan. It is the primery key of the table
             crcLOAN.
    """

    res = run_sql("""SELECT status
                       FROM crcLOAN
                      WHERE id=%s""",
                  (loan_id, ))

    if res:
        return res[0][0]
    else:
        return None

def get_all_loans(limit):
    """
    Get all loans.
    """

    res = run_sql("""
        SELECT bor.id,
               bor.name,
               it.id_bibrec,
               l.barcode,
               DATE_FORMAT(l.loaned_on,'%%Y-%%m-%%d %%T'),
               DATE_FORMAT(l.due_date,'%%Y-%%m-%%d'),
               l.number_of_renewals,
               l.overdue_letter_number,
               DATE_FORMAT(l.overdue_letter_date,'%%Y-%%m-%%d'),
               l.notes,
               l.id
          FROM crcLOAN l, crcBORROWER bor, crcITEM it
         WHERE l.id_crcBORROWER = bor.id
           AND l.barcode = it.barcode
           AND l.status = %s
      ORDER BY 5 DESC
         LIMIT 0,%s
    """, (CFG_BIBCIRCULATION_LOAN_STATUS_ON_LOAN, limit))

    return res

def get_all_expired_loans():
    """
    Get all expired(overdue) loans.
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
          and ((l.status = %s and l.due_date < CURDATE())
                  or l.status = %s )
    """, (CFG_BIBCIRCULATION_LOAN_STATUS_ON_LOAN,
          CFG_BIBCIRCULATION_LOAN_STATUS_EXPIRED))

    return res

def get_expired_loans_with_waiting_requests():

    res = run_sql("""SELECT DISTINCT
                            lr.id,
                            lr.id_bibrec,
                            lr.id_crcBORROWER,
                            it.id_crcLIBRARY,
                            it.location,
                            DATE_FORMAT(lr.period_of_interest_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.period_of_interest_to,'%%Y-%%m-%%d'),
                            lr.request_date
                       FROM crcLOANREQUEST lr,
                            crcITEM it,
                            crcLOAN l
                      WHERE it.barcode=l.barcode
                        AND lr.id_bibrec=it.id_bibrec
                        AND (lr.status=%s or lr.status=%s)
                        AND (l.status=%s or (l.status=%s
                        AND l.due_date < CURDATE()))
                        AND lr.period_of_interest_from <= NOW()
                        AND lr.period_of_interest_to >= NOW()
                   ORDER BY lr.request_date;
                  """, ( CFG_BIBCIRCULATION_REQUEST_STATUS_PENDING,
                         CFG_BIBCIRCULATION_REQUEST_STATUS_WAITING,
                         CFG_BIBCIRCULATION_LOAN_STATUS_EXPIRED,
                         CFG_BIBCIRCULATION_LOAN_STATUS_ON_LOAN))
    return res

def get_current_loan_id(barcode):
    res = run_sql(""" SELECT id
                        FROM crcLOAN
                       WHERE barcode=%s
                         AND (status=%s OR status=%s)
                  """, (barcode, CFG_BIBCIRCULATION_LOAN_STATUS_ON_LOAN,
                        CFG_BIBCIRCULATION_LOAN_STATUS_EXPIRED))

    if res:
        return res[0][0]

def get_last_loan():
    """
    Get the recid, the borrower_id and the due date of
    the last loan who was registered on the crcLOAN table.
    """

    res = run_sql("""SELECT id_bibrec,
                            id_crcBORROWER,
                            DATE_FORMAT(due_date, '%Y-%m-%d')
                     FROM   crcLOAN ORDER BY id DESC LIMIT 1""")

    if res:
        return res[0]
    else:
        return None

def get_loan_recid(loan_id):

    res = run_sql("""SELECT id_bibrec
                       FROM crcLOAN
                      WHERE id=%s""",
                  (loan_id, ))

    if res:
        return res[0][0]
    else:
        return None

def get_loan_notes(loan_id):

    res = run_sql("""SELECT notes
                       FROM crcLOAN
                      WHERE id=%s""",
                      (loan_id, ))

    if res:
        return res[0][0]
    else:
        return None

def update_loan_notes(loan_id, loan_notes):
    """
    """
    run_sql("""UPDATE crcLOAN
                  SET notes=%s
                WHERE id=%s """, (str(loan_notes), loan_id))

def add_new_loan_note(new_note, loan_id):
    """
    Add a new loan's note.
    new_note: note who will be added.
    loan_id: identify the loan. A new note will
             added to this loan. It is also the
             primary key of the table crcLOAN.
    """
    run_sql("""UPDATE crcLOAN
               set notes=concat(notes,%s)
               WHERE id=%s;
                """, (new_note, loan_id))

def renew_loan(loan_id, new_due_date):
    run_sql("""UPDATE  crcLOAN
                  SET  due_date=%s,
                       number_of_renewals=number_of_renewals+1,
                       overdue_letter_number=0,
                       status=%s
                WHERE  id=%s""", (new_due_date,
                                  CFG_BIBCIRCULATION_LOAN_STATUS_ON_LOAN,
                                  loan_id))

###
### Loan Returns related functions ###
###



def return_loan(barcode):
    """
    Update loan information when a copy is returned.

    @param returned_on: return date.
    @type returned_on: string

    @param status: new loan status.
    @type status: string

    @param barcode: identify the item. Primary key of crcITEM.
    @type barcode: string
    """

    return int(run_sql("""UPDATE crcLOAN
                             SET returned_on=NOW(), status=%s, due_date=NULL
                           WHERE barcode=%s and (status=%s or status=%s)
                      """, (CFG_BIBCIRCULATION_LOAN_STATUS_RETURNED,
                            barcode,
                            CFG_BIBCIRCULATION_LOAN_STATUS_ON_LOAN,
                            CFG_BIBCIRCULATION_LOAN_STATUS_EXPIRED)))



###
### 'Item' related functions ###
###



def get_id_bibrec(barcode):
    """
    Get the id of the bibrec (recid).

    @param barcode: identify the item. Primary key of crcITEM.
    @type barcode: string

    @return recid or None
    """

    res = run_sql("""SELECT id_bibrec
                     FROM crcITEM
                     WHERE barcode=%s
                  """, (barcode, ))

    if res:
        return res[0][0]
    else:
        return None

def get_item_info(barcode):
    """
    Get item's information.

    barcode: identify the item. It is the primary key of the table
             crcITEM.
    """

    res = run_sql("""SELECT it.barcode,
                            it.id_crcLIBRARY,
                            lib.name,
                            it.collection,
                            it.location,
                            it.description,
                            it.loan_period,
                            it.status
                       FROM crcITEM it,
                            crcLIBRARY lib
                      WHERE it.barcode=%s and it.id_crcLIBRARY = lib.id""",
                  (barcode, ))

    if res:
        return res[0]
    else:
        return None

def get_loan_period(barcode):
    """
    Retrieve the loan period of a book.

    barcode: identify the item. It is the primary key of the table
             crcITEM.
    """

    res = run_sql("""SELECT loan_period
                       FROM crcITEM
                      WHERE barcode=%s""",
                  (barcode, ))

    if res:
        return res[0][0]
    else:
        return None

def update_item_info(barcode, library_id, collection, location, description,
                 loan_period, status, expected_arrival_date):
    """
    Update item's information.

    barcode: identify the item. It is the primary key of the table
             crcITEM.

    library_id: identify the library. It is also the primary key of
                the table crcLIBRARY.
    """

    int(run_sql("""UPDATE crcITEM
                      set barcode=%s,
                          id_crcLIBRARY=%s,
                          collection=%s,
                          location=%s,
                          description=%s,
                          loan_period=%s,
                          status=%s,
                          expected_arrival_date=%s,
                          modification_date=NOW()
                   WHERE  barcode=%s""",
                (barcode, library_id, collection, location, description,
                 loan_period, status, expected_arrival_date, barcode)))

def update_barcode(old_barcode, barcode):

    res = run_sql("""UPDATE crcITEM
                        SET barcode=%s
                      WHERE barcode=%s
                """, (barcode, old_barcode))

    run_sql("""UPDATE crcLOAN
                  SET barcode=%s
                WHERE barcode=%s
                """, (barcode, old_barcode))

    run_sql("""UPDATE crcLOANREQUEST
                  SET barcode=%s
                WHERE barcode=%s
                """, (barcode, old_barcode))

    run_sql("""UPDATE crcILLREQUEST
                  SET barcode=%s
                WHERE barcode=%s
                """, (barcode, old_barcode))

    return res > 0

def get_item_loans(recid):
    """
    recid: identify the record. It is also the primary key of
           the table bibrec.
    """

    res = run_sql(
    """
    SELECT bor.id,
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
    FROM crcLOAN l, crcBORROWER bor, crcITEM it
    WHERE l.id_crcBORROWER = bor.id
          and l.barcode=it.barcode
          and l.id_bibrec=%s
          and l.status!=%s
    """, (recid, CFG_BIBCIRCULATION_LOAN_STATUS_RETURNED))

    return res

def get_item_requests(recid):
    """
    recid: identify the record. It is also the primary key of
           the table bibrec.
    """
    res = run_sql("""SELECT bor.id,
                            bor.name,
                            lr.id_bibrec,
                            lr.barcode,
                            lr.status,
                            lib.name,
                            it.location,
                            it.description,
                            DATE_FORMAT(lr.period_of_interest_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.period_of_interest_to,'%%Y-%%m-%%d'),
                            lr.id,
                            lr.request_date
                     FROM   crcLOANREQUEST lr,
                            crcBORROWER bor,
                            crcITEM it,
                            crcLIBRARY lib
                     WHERE  bor.id = lr.id_crcBORROWER and lr.id_bibrec=%s
                            and lr.status!=%s and lr.status!=%s and lr.status!=%s
                            and lr.barcode = it.barcode and lib.id = it.id_crcLIBRARY
                     """, (recid,
                           CFG_BIBCIRCULATION_REQUEST_STATUS_DONE,
                           CFG_BIBCIRCULATION_REQUEST_STATUS_CANCELLED,
                           CFG_BIBCIRCULATION_REQUEST_STATUS_PROPOSED))

    return res

def get_item_purchases(status, recid):
    """
    Purchases of a particular item to be displayed in the item info page.
    """

    from invenio.bibcirculation_utils import looks_like_dictionary

    status1 = ''
    status2 = ''

    if status == CFG_BIBCIRCULATION_ACQ_STATUS_NEW:
        status1 = CFG_BIBCIRCULATION_ACQ_STATUS_ON_ORDER
        status2 = CFG_BIBCIRCULATION_PROPOSAL_STATUS_ON_ORDER
    elif status == CFG_BIBCIRCULATION_ACQ_STATUS_RECEIVED:
        status1 = CFG_BIBCIRCULATION_ACQ_STATUS_PARTIAL_RECEIPT
        status2 = CFG_BIBCIRCULATION_PROPOSAL_STATUS_RECEIVED

    res = run_sql("""SELECT ill.id, ill.id_crcBORROWER, bor.name,
                       ill.id_crcLIBRARY, ill.status,
                       DATE_FORMAT(ill.period_of_interest_from,'%%Y-%%m-%%d'),
                       DATE_FORMAT(ill.period_of_interest_to,'%%Y-%%m-%%d'),
                       DATE_FORMAT(ill.due_date,'%%Y-%%m-%%d'),
                       ill.item_info, ill.cost, ill.request_type, ''
                  FROM crcILLREQUEST ill, crcBORROWER bor
                 WHERE ill.id_crcBORROWER=bor.id
                   AND ill.request_type in (%s, %s, %s)
                   AND ill.status in (%s, %s, %s)
              ORDER BY ill.id desc""", ('acq-book', 'acq-standard',
                                        'proposal-book', status, status1, status2))

    purchases = []
    for record in res:
        if looks_like_dictionary(record[8]):
            item_info = eval(record[8])
            try:
                if str(recid) == str(item_info['recid']): purchases.append(record)
            except KeyError:
                continue
    return tuple(purchases)

def get_item_loans_historical_overview(recid):
    """
    @param recid: identify the record. Primary key of bibrec.
    @type recid: int
    """
    res = run_sql("""SELECT bor.name,
                            bor.id,
                            l.barcode,
                            lib.name,
                            it.location,
                            DATE_FORMAT(l.loaned_on,'%%Y-%%m-%%d'),
                            DATE_FORMAT(l.due_date,'%%Y-%%m-%%d'),
                            l.returned_on,
                            l.number_of_renewals,
                            l.overdue_letter_number
                     FROM crcLOAN l, crcBORROWER bor, crcITEM it, crcLIBRARY lib
                     WHERE l.id_crcBORROWER=bor.id and
                           lib.id = it.id_crcLIBRARY and
                           it.barcode = l.barcode and
                           l.id_bibrec = %s and
                           l.status = %s """
                  , (recid, CFG_BIBCIRCULATION_LOAN_STATUS_RETURNED))

    return res

def get_item_requests_historical_overview(recid):
    """
    recid: identify the record. It is also the primary key of
           the table bibrec.
    """

    res = run_sql("""
                  SELECT bor.name,
                         bor.id,
                         lr.barcode,
                         lib.name,
                         it.location,
                         DATE_FORMAT(lr.period_of_interest_from,'%%Y-%%m-%%d'),
                         DATE_FORMAT(lr.period_of_interest_to,'%%Y-%%m-%%d'),
                         lr.request_date
                  FROM crcLOANREQUEST lr, crcBORROWER bor, crcITEM it, crcLIBRARY lib
                  WHERE lr.id_crcBORROWER=bor.id and
                        lib.id = it.id_crcLIBRARY and
                        it.barcode = lr.barcode and
                        lr.id_bibrec = %s and
                        lr.status = %s
                  """, (recid, CFG_BIBCIRCULATION_REQUEST_STATUS_DONE))

    return res

def get_nb_copies_on_loan(recid):
    """
    Get the number of copies on loan for a recid.
    recid: Invenio record identifier. The number of copies
           of this record will be retrieved.
    """

    res = run_sql("""SELECT count(barcode)
                     FROM crcITEM
                     WHERE id_bibrec=%s and status=%s;
                     """, (recid, CFG_BIBCIRCULATION_LOAN_STATUS_ON_LOAN))

    return res[0][0]

def get_item_copies_details(recid):
    """
    Get copies details of a given recid.

    @param recid: identify the record. Primary key of bibrec.
    @type recid: int

    @return list with barcode, loan_period, library_name, library_id,
                      location, number_of_requests, status, collection,
                      description and due_date.
    """
    res = run_sql("""SELECT it.barcode, it.loan_period, lib.name,
                            lib.id, it.location, it.number_of_requests,
                            it.status, it.collection, it.description,
                            DATE_FORMAT(ln.due_date,'%%Y-%%m-%%d')
                     FROM crcITEM it
                            left join crcLOAN ln
                            on it.barcode = ln.barcode and ln.status != %s
                            left join crcLIBRARY lib
                            on lib.id = it.id_crcLIBRARY
                     WHERE it.id_bibrec=%s
                     ORDER BY it.creation_date
                  """, (CFG_BIBCIRCULATION_LOAN_STATUS_RETURNED, recid))

    return res

def get_copy_details(barcode):

    res = run_sql(""" SELECT *
                        FROM crcITEM it
                       WHERE barcode=%s""",
                  (barcode, ))

    if res is not None:
        return res[0]
    else:
        return None

def get_copies_status(recid, description='-'):
    """
    @param description: Gives the details like volume(if any), etc... of a particular
                        item in the record.
    """
    if description.strip() in ('', '-'):
        res = run_sql("""SELECT status
                           FROM crcITEM
                          WHERE id_bibrec=%s""", (recid, ))
    else:
        res = run_sql("""SELECT status
                           FROM crcITEM
                          WHERE id_bibrec=%s
                            AND description=%s
                      """, (recid, description))

    list_of_statuses = []
    for status in res:
        list_of_statuses.append(status[0])

    if list_of_statuses == []:
        return None
    else:
        return list_of_statuses

def update_item_status(status, barcode):
    """
    Update the status of an item (using the barcode).

    @param status: status of the item.
    @type status: string

    @param barcode: identify the item. Primary key of crcITEM.
    @type barcode: string

    @return
    """
    if status == CFG_BIBCIRCULATION_ITEM_STATUS_ON_LOAN:
        return int(run_sql("""UPDATE  crcITEM
                                 SET  status=%s,
                                      number_of_requests = number_of_requests + 1
                               WHERE  barcode=%s""", (status, barcode)))
    else:
        return int(run_sql("""UPDATE  crcITEM
                                 SET  status=%s
                               WHERE  barcode=%s""", (status, barcode)))

def get_item_description(barcode):
    res = run_sql(""" SELECT description
                      FROM crcITEM
                      WHERE barcode=%s
                  """, (barcode, ))

    #When no description:
    #Don't return NULL, in order not to pose problems if checked for equality.
    if res and res[0][0]:
        return res[0][0]
    else:
        return ''

def set_item_description(barcode, description):
    return int(run_sql("""UPDATE  crcITEM
                                 SET  description=%s
                               WHERE  barcode=%s""", (description or '-', barcode)))

def get_holdings_information(recid, include_hidden_libraries=True):
    """
    Get information about holdings, using recid.

    @param recid: identify the record. Primary key of bibrec.
    @type recid:  int

    @return holdings information
    """

    if include_hidden_libraries:
        res = run_sql("""SELECT it.barcode,
                                lib.name,
                                it.collection,
                                it.location,
                                it.description,
                                it.loan_period,
                                it.status,
                                DATE_FORMAT(ln.due_date, '%%Y-%%m-%%d')
                           FROM crcITEM it
                                left join crcLOAN ln
                                on it.barcode = ln.barcode and ln.status != %s
                                left join crcLIBRARY lib
                                on lib.id = it.id_crcLIBRARY
                          WHERE it.id_bibrec=%s
                    """, (CFG_BIBCIRCULATION_LOAN_STATUS_RETURNED, recid))

    else:
        res = run_sql("""SELECT it.barcode,
                                lib.name,
                                it.collection,
                                it.location,
                                it.description,
                                it.loan_period,
                                it.status,
                                DATE_FORMAT(ln.due_date, '%%Y-%%m-%%d')
                           FROM crcITEM it
                                left join crcLOAN ln
                                on it.barcode = ln.barcode and ln.status != %s
                                left join crcLIBRARY lib
                                on lib.id = it.id_crcLIBRARY
                          WHERE it.id_bibrec=%s
                            AND lib.type<>%s
                    """, (CFG_BIBCIRCULATION_LOAN_STATUS_RETURNED, recid,
                          CFG_BIBCIRCULATION_LIBRARY_TYPE_HIDDEN))

    return res

def get_number_copies(recid):
    """
    Get the number of copies of a given recid.
    This function is used by the 'BibEdit' module to display the
    number of copies for the record being edited.
    @param recid: identify the record. Primary key of bibrec.
    @type recid: int

    @return number_of_copies
    """
    try:
        recid = int(recid)
    except ValueError:
        return 0

    res = run_sql("""SELECT count(barcode)
                     FROM crcITEM
                     WHERE id_bibrec=%s
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
    return (get_number_copies(recid) != 0)

def add_new_copy(barcode, recid, library_id, collection, location, description,
                 loan_period, status, expected_arrival_date):

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
                                status, expected_arrival_date, creation_date,
                                modification_date)
                values (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())""",
            (barcode, recid, library_id, collection, location, description or '-',
             loan_period, status, expected_arrival_date))

def delete_copy(barcode):
    res = run_sql("""delete FROM crcITEM WHERE barcode=%s""", (barcode, ))
    return res

def get_expected_arrival_date(barcode):
    res = run_sql("""SELECT expected_arrival_date
                       FROM crcITEM
                      WHERE barcode=%s """, (barcode,))
    if res:
        return res[0][0]
    else:
        return ''

def get_barcodes(recid, description='-'):
    """
    @param description: Gives the details like volume(if any), etc... of a particular
                        item in the record.
    """

    if description.strip() in ('', '-'):
        res = run_sql("""SELECT barcode
                           FROM crcITEM
                          WHERE id_bibrec=%s""",
                      (recid, ))
    else:
        res = run_sql("""SELECT barcode
                           FROM crcITEM
                          WHERE id_bibrec=%s
                            AND description=%s""",
                      (recid, description))

    barcodes = []
    for i in range(len(res)):
        barcodes.append(res[i][0])

    return barcodes

def barcode_in_use(barcode):

    res = run_sql("""SELECT id_bibrec
                       FROM crcITEM
                      WHERE barcode=%s""",
                  (barcode, ))

    if len(res)>0:
        return True
    else:
        return False




###
### "Borrower" related functions ###
###




def new_borrower(ccid, name, email, phone, address, mailbox, notes):
    """
    Add/Register a new borrower on the crcBORROWER table.
    name: borrower's name.
    email: borrower's email.
    phone: borrower's phone.
    address: borrower's address.
    """

    return run_sql("""insert into crcBORROWER ( ccid,
                                                name,
                                                email,
                                                phone,
                                                address,
                                                mailbox,
                                                borrower_since,
                                                borrower_until,
                                                notes)
        values(%s, %s, %s, %s, %s, %s, NOW(), '0000-00-00 00:00:00', %s)""",
        (ccid, name, email, phone, address, mailbox, str(notes)))
    # IntegrityError: (1062, "Duplicate entry '665119' for key 2")

def get_borrower_details(borrower_id):
    """
    borrower_id: identify the borrower. It is also the primary key of
                 the table crcBORROWER.
    """
    res = run_sql("""SELECT id, ccid, name, email, phone, address, mailbox
                  FROM crcBORROWER WHERE id=%s""", (borrower_id, ))
    if res:
        return clean_data(res[0])
    else:
        return None


def clean_data(data):
    final_res = list(data)
    for i in range(0, len(final_res)):
        if isinstance(final_res[i], str):
            final_res[i] = final_res[i].replace(",", " ")
    return final_res


def update_borrower_info(borrower_id, name, email, phone, address, mailbox):
    """
    Update borrower info.

    borrower_id: identify the borrower. It is also the primary key of
                 the table crcBORROWER.
    """
    return int(run_sql("""UPDATE crcBORROWER
                             set name=%s,
                                 email=%s,
                                 phone=%s,
                                 address=%s,
                                 mailbox=%s
                          WHERE  id=%s""",
                       (name, email, phone, address, mailbox, borrower_id)))

def get_borrower_data(borrower_id):
    """
    Get the borrower's information (name, address and email).
    borrower_id: identify the borrower. The data associate
                 to this borrower will be retrieved. It is also
                 the primary key of the crcBORROWER table.
    """

    res = run_sql("""SELECT name,
                            address,
                            mailbox,
                            email
                     FROM   crcBORROWER
                     WHERE  id=%s""",
                  (borrower_id, ))

    if res:
        return clean_data(res[0])
    else:
        return None

def get_borrower_data_by_id(borrower_id):
    """
    Retrieve borrower's data by borrower_id.
    """

    res = run_sql("""SELECT id, ccid, name, email, phone,
                            address, mailbox
                       FROM crcBORROWER
                      WHERE id=%s""", (borrower_id, ))

    if res:
        return clean_data(res[0])
    else:
        return None

def get_borrower_ccid(user_id):

    res = run_sql("""SELECT ccid
                       FROM crcBORROWER
                      WHERE id=%s""", (user_id, ))

    if res:
        return res[0][0]
    else:
        return None

def get_all_borrowers():
    res = run_sql("""SELECT id, ccid
                       FROM crcBORROWER""")

    return res

def get_borrower_name(borrower_id):
    """
    borrower_id: identify the borrower. It is also the primary key of
                 the table crcBORROWER.
    """
    res = run_sql("""SELECT name
                       FROM crcBORROWER
                      WHERE id=%s
                  """, (borrower_id, ))

    if res:
        return res[0][0]
    else:
        return None

def get_borrower_email(borrower_id):
    """
    Get the email of a borrower.

    @param borrower_id: identify the borrower. Primary key of crcBORROWER.
    @type borrower_id: int

    @return borrower's email (string).
    """
    res = run_sql("""SELECT email
                       FROM crcBORROWER
                      WHERE id=%s""", (borrower_id, ))

    if res:
        return res[0][0]
    else:
        return None

def get_borrower_id_by_email(email):
    """
    Retrieve borrower's id by email.
    """

    res = run_sql("""SELECT id
                       FROM crcBORROWER
                      WHERE email=%s""",
                  (email, ))

    if res:
        return res[0][0]
    else:
        return None

def get_borrower_address(email):
    """
    Get the address of a borrower using the email.
    email: borrower's email.
    """

    res = run_sql("""SELECT address
                     FROM crcBORROWER
                     WHERE email=%s""", (email, ))

    if len(res[0][0]) > 0:
        return res[0][0].replace(",", " ")
    else:
        return 0

def add_borrower_address(address, email):
    """
    Add the email and the address of a borrower.
    address: borrower's address.
    email: borrower's email.
    """

    run_sql("""UPDATE crcBORROWER
               set address=%s
               WHERE email=%s""", (address, email))

def get_invenio_user_email(uid):
    """
    Get the email of an invenio's user.
    uid: identify an invenio's user.
    """

    res = run_sql("""SELECT email
                     FROM user
                     WHERE id=%s""",
                  (uid, ))

    if res:
        return res[0][0]
    else:
        return None

def search_borrower_by_name(string):
    """
    string: search pattern.
    """
    string = string.replace("'", "\\'")

    res = run_sql("""SELECT id, name
                       FROM crcBORROWER
                      WHERE upper(name) like upper('%%%s%%')
                   ORDER BY name
                  """ % (string))

    return res

def search_borrower_by_email(string):
    """
    string: search pattern.
    """

    res = run_sql("""SELECT id, name
                       FROM crcBORROWER
                      WHERE email regexp %s
                     """, (string, ))

    return res

def search_borrower_by_id(string):
    """
    string: search pattern.
    """

    res = run_sql("""SELECT id, name
                       FROM crcBORROWER
                      WHERE id=%s
                     """, (string, ))

    return res

def search_borrower_by_ccid(string):
    """
    string: search pattern.
    """

    res = run_sql("""SELECT id, name
                       FROM crcBORROWER
                      WHERE ccid regexp %s
                     """, (string, ))

    return res

def update_borrower(user_id, name, email, phone, address, mailbox):
    return run_sql(""" UPDATE crcBORROWER
                          SET name=%s,
                              email=%s,
                              phone=%s,
                              address=%s,
                              mailbox=%s
                        WHERE id=%s
            """, (name, email, phone, address, mailbox, user_id))

def get_borrower_loans(borrower_id):
    """
    borrower_id: identify the borrower. It is also the primary key of
             the table crcBORROWER.
    """

    res = run_sql(""" SELECT id_bibrec,
                             barcode,
                             DATE_FORMAT(loaned_on,'%%Y-%%m-%%d'),
                             DATE_FORMAT(due_date,'%%Y-%%m-%%d'),
                             type
                      FROM crcLOAN
                      WHERE id_crcBORROWER=%s and status != %s
                  """, (borrower_id, CFG_BIBCIRCULATION_LOAN_STATUS_RETURNED))

    return res

def get_recid_borrower_loans(borrower_id):
    """
    borrower_id: identify the borrower. It is also the primary key of
                 the table crcBORROWER.
    """

    res = run_sql(""" SELECT id, id_bibrec, barcode
                      FROM crcLOAN
                      WHERE id_crcBORROWER=%s
                        AND status != %s
                        AND type != 'ill'
                  """, (borrower_id, CFG_BIBCIRCULATION_ILL_STATUS_RETURNED))


    return res

def get_borrower_loan_details(borrower_id):
    """
    borrower_id: identify the borrower. It is also the primary key of
                 the table crcBORROWER.

    This function is also used by the Aleph Service for the display of loans
    of the user for the termination sheet.
    """

    res = run_sql("""
                  SELECT it.id_bibrec,
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
                    FROM crcLOAN l, crcITEM it
                   WHERE l.barcode=it.barcode
                     AND id_crcBORROWER=%s
                     AND l.status!=%s
    """, (borrower_id, CFG_BIBCIRCULATION_LOAN_STATUS_RETURNED))

    return res

def get_borrower_request_details(borrower_id):
    """
    borrower_id: identify the borrower. It is also the primary key of
                 the table crcBORROWER.

    This function is also used by the Aleph Service for the display of loan
    requests of the user for the termination sheet.
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
                     WHERE  lr.id_crcBORROWER=%s
                       AND  (lr.status=%s OR lr.status=%s)
                            and lib.id = it.id_crcLIBRARY and lr.barcode = it.barcode
                            """, (borrower_id,
                                  CFG_BIBCIRCULATION_REQUEST_STATUS_WAITING,
                                  CFG_BIBCIRCULATION_REQUEST_STATUS_PENDING))

    return res

def get_borrower_requests(borrower_id):
    """
    Get the hold requests of a borrower.
    borrower_id: identify the borrower. All the hold requests
                 associate to this borrower will be retrieved.
                 It is also the primary key of the crcBORROWER table.
    """
    res = run_sql("""
                  SELECT id,
                         id_bibrec,
                         DATE_FORMAT(request_date,'%%Y-%%m-%%d'),
                         status
                  FROM   crcLOANREQUEST
                  WHERE  id_crcBORROWER=%s and
                         (status=%s or status=%s)""",
                  (borrower_id, CFG_BIBCIRCULATION_REQUEST_STATUS_PENDING,
                   CFG_BIBCIRCULATION_REQUEST_STATUS_WAITING))

    return res

def get_borrower_proposals(borrower_id):
    """
    Get the proposals of a borrower.
    borrower_id: identify the borrower. All the proposals
                 associated to this borrower will be retrieved.
                 It is also the primary key of the crcBORROWER table.
    """
    res = run_sql("""
                  SELECT id,
                         id_bibrec,
                         DATE_FORMAT(request_date,'%%Y-%%m-%%d'),
                         status
                  FROM   crcLOANREQUEST
                  WHERE  id_crcBORROWER=%s and
                         status=%s""",
                  (borrower_id, CFG_BIBCIRCULATION_REQUEST_STATUS_PROPOSED))
    return res

def bor_loans_historical_overview(borrower_id):
    """
    Get loans historical overview of a given borrower_id.

    @param borrower_id: identify the borrower. Primary key of crcBORROWER.
    @type borrower_id: int

    @return list with loans historical overview.
    """
    res = run_sql("""SELECT l.id_bibrec,
                            l.barcode,
                            lib.name,
                            it.location,
                            DATE_FORMAT(l.loaned_on,'%%Y-%%m-%%d'),
                            DATE_FORMAT(l.due_date,'%%Y-%%m-%%d'),
                            l.returned_on,
                            l.number_of_renewals,
                            l.overdue_letter_number
                     FROM crcLOAN l, crcITEM it, crcLIBRARY lib
                     WHERE l.id_crcBORROWER=%s and
                           lib.id = it.id_crcLIBRARY and
                           it.barcode = l.barcode and
                           l.status = %s
                """, (borrower_id, CFG_BIBCIRCULATION_LOAN_STATUS_RETURNED))
    return res

def bor_requests_historical_overview(borrower_id):
    """
    Get requests historical overview of a given borrower_id.

    @param borrower_id: identify the borrower. Primary key of crcBORROWER.
    @type borrower_id: int

    @return list with requests historical overview.
    """
    res = run_sql("""SELECT lr.id_bibrec,
                            lr.barcode,
                            lib.name,
                            it.location,
                            DATE_FORMAT(lr.period_of_interest_from,'%%Y-%%m-%%d'),
                            DATE_FORMAT(lr.period_of_interest_to,'%%Y-%%m-%%d'),
                            lr.request_date
                       FROM crcLOANREQUEST lr, crcITEM it, crcLIBRARY lib
                      WHERE lr.id_crcBORROWER=%s and
                            lib.id = it.id_crcLIBRARY and
                            it.barcode = lr.barcode and
                            lr.status =%s
                """, (borrower_id, CFG_BIBCIRCULATION_REQUEST_STATUS_DONE))
    return res

def get_historical_overview(borrower_id):
    """
    Get historical information overview (recid, loan date, return date
    and number of renewals).
    borrower_id: identify the borrower. All the old (returned) loans
                 associated to this borrower will be retrieved.
                 It is also the primary key of the crcBORROWER table.
    """

    res = run_sql("""SELECT id_bibrec,
                            DATE_FORMAT(loaned_on,'%%Y-%%m-%%d'),
                            returned_on,
                            number_of_renewals
                     FROM crcLOAN
                     WHERE id_crcBORROWER=%s and status=%s;
                  """, (borrower_id,
                        CFG_BIBCIRCULATION_LOAN_STATUS_RETURNED))

    return res

def get_borrower_notes(borrower_id):
    """The data associated to this borrower will be retrieved."""

    res = run_sql("""SELECT notes
                     FROM   crcBORROWER
                     WHERE id=%s""",
                  (borrower_id, ))

    if res:
        return res[0][0]
    else:
        return None

def update_borrower_notes(borrower_id, borrower_notes):

    run_sql("""UPDATE crcBORROWER
                  SET notes=%s
                WHERE id=%s """, (str(borrower_notes), borrower_id))




###
### "Library" related functions ###
###




def get_all_libraries():

    res = run_sql("""SELECT id, name
                       FROM crcLIBRARY
                       ORDER BY name""")

    return res

def get_main_libraries():

    res = run_sql("""SELECT id, name
                     FROM crcLIBRARY
                     WHERE type=%s
                     """, (CFG_BIBCIRCULATION_LIBRARY_TYPE_MAIN, ))

    if res:
        return res
    else:
        return None

def get_internal_libraries():

    res = run_sql("""SELECT id, name
                       FROM crcLIBRARY
                       WHERE (type=%s OR type=%s)
                       ORDER BY name
                  """, (CFG_BIBCIRCULATION_LIBRARY_TYPE_INTERNAL,
                        CFG_BIBCIRCULATION_LIBRARY_TYPE_MAIN))

    return res

def get_external_libraries():

    res = run_sql("""SELECT id, name
                       FROM crcLIBRARY
                      WHERE type=%s
                """, (CFG_BIBCIRCULATION_LIBRARY_TYPE_EXTERNAL, ))

    return res

def get_hidden_libraries():

    res = run_sql("""SELECT id, name
                       FROM crcLIBRARY
                       WHERE type=%s
                       ORDER BY name
                  """, (CFG_BIBCIRCULATION_LIBRARY_TYPE_HIDDEN, ))

    return res

def merge_libraries(library_from, library_to):

    run_sql("""UPDATE crcITEM
                  SET id_crcLIBRARY=%s
                WHERE id_crcLIBRARY=%s
                  """, (library_to, library_from))

    run_sql("""UPDATE crcILLREQUEST
                  SET id_crcLIBRARY=%s
                WHERE id_crcLIBRARY=%s
                  """, (library_to, library_from))

    run_sql("""DELETE FROM crcLIBRARY
                WHERE id=%s
                  """, (library_from,))

def get_library_items(library_id):
    """
    Get all items which belong to a library.

    library_id: identify the library. It is also the primary key of
                the table crcLIBRARY.
    """
    res = run_sql("""SELECT barcode, id_bibrec, collection,
                            location, description, loan_period, status, number_of_requests
                       FROM crcITEM
                      WHERE id_crcLIBRARY=%s""",
                  (library_id, ))

    return res

def get_library_details(library_id):
    """
    library_id: identify the library. It is also the primary key of
                the table crcLIBRARY.
    """
    res = run_sql("""SELECT id, name, address, email, phone, type, notes
                     FROM crcLIBRARY
                     WHERE id=%s;
                     """, (library_id, ))

    if res:
        return res[0]
    else:
        return None

def get_library_type(library_id):
    """
    library_id: identify the library. It is also the primary key of
                the table crcLIBRARY.
    """

    res = run_sql("""SELECT type
                     FROM   crcLIBRARY
                     WHERE  id=%s""",
                  (library_id, ))

    if res:
        return res[0][0]
    else:
        return None

def get_library_name(library_id):
    """
    library_id: identify the library. It is also the primary key of
                the table crcLIBRARY.
    """

    res = run_sql("""SELECT name
                     FROM   crcLIBRARY
                     WHERE  id=%s""",
                  (library_id, ))

    if res:
        return res[0][0]
    else:
        return None

def get_lib_location(barcode):

    res = run_sql("""SELECT id_crcLIBRARY, location
                       FROM crcITEM
                      WHERE barcode=%s""",
                  (barcode, ))

    if res:
        return res[0]
    else:
        return None

def get_library_notes(library_id):
    """ The data associated to this library will be retrieved."""
    res = run_sql("""SELECT notes
                       FROM crcLIBRARY
                      WHERE id=%s""",
                  (library_id, ))

    if res:
        return res[0][0]
    else:
        return None

def update_library_notes(library_id, library_notes):

    run_sql("""UPDATE crcLIBRARY
                  SET notes=%s
                WHERE id=%s """, (str(library_notes), library_id))

def add_new_library(name, email, phone, address, lib_type, notes):

    run_sql("""insert into crcLIBRARY (name, email, phone,
                                       address, type, notes)
                           values (%s, %s, %s, %s, %s, %s)""",
            (name, email, phone, address, lib_type, notes))

def update_library_info(library_id, name, email, phone, address, lib_type):
    """
    library_id: identify the library. It is also the primary key of
                the table crcLIBRARY.
    """

    return int(run_sql("""UPDATE crcLIBRARY
                             set name=%s,
                                 email=%s,
                                 phone=%s,
                                 address=%s,
                                 type=%s
                           WHERE id=%s""",
                       (name, email, phone, address, lib_type, library_id)))

def search_library_by_name(string):

    string = string.replace("'", "\\'")

    res = run_sql("""SELECT id, name
                     FROM crcLIBRARY
                     WHERE upper(name) like upper('%%%s%%')
                     ORDER BY name
                     """ % (string))

    return res

def search_library_by_email(string):

    res = run_sql("""SELECT id, name
                     FROM crcLIBRARY
                     WHERE email regexp %s
                     ORDER BY name
                     """, (string, ))
    return res




###
### "Vendor" related functions ###
###




def get_all_vendors():

    res = run_sql("""SELECT id, name
                       FROM crcVENDOR""")
    return res

def get_vendor_details(vendor_id):
    """
    vendor_id: identify the vendor. It is also the primary key of
               the table crcVENDOR.
    """
    res = run_sql("""SELECT id, name, address, email, phone, notes
                       FROM crcVENDOR
                      WHERE id=%s;
                     """, (vendor_id, ))

    if res:
        return res[0]
    else:
        return None

def get_vendor_name(vendor_id):
    """
    vendor_id: identify the vendor. It is also the primary key of
               the table crcVENDOR.
    """
    res = run_sql("""SELECT name
                       FROM crcVENDOR
                      WHERE id=%s""",
                  (vendor_id, ))

    if res:
        return res[0][0]
    else:
        return None

def get_vendor_notes(vendor_id):
    """ The data associated to this vendor will be retrieved."""

    res = run_sql("""SELECT notes
                       FROM crcVENDOR
                      WHERE id=%s""",
                  (vendor_id, ))

    if res:
        return res[0][0]
    else:
        return None

def add_new_vendor_note(new_note, vendor_id):

    run_sql("""UPDATE crcVENDOR
                  SET notes=concat(notes,%s)
                WHERE id=%s;
                """, (new_note, vendor_id))

def add_new_vendor(name, email, phone, address, notes):

    run_sql("""insert into crcVENDOR (name, email, phone,
                                      address, notes)
                           values (%s, %s, %s, %s, %s)""",
            (name, email, phone, address, notes))

def update_vendor_info(vendor_id, name, email, phone, address):
    """
    vendor_id: identify the vendor. It is also the primary key of
               the table crcVENDOR.
    """
    return int(run_sql("""UPDATE crcVENDOR
                             SET name=%s,
                                 email=%s,
                                 phone=%s,
                                 address=%s
                          WHERE  id=%s""",
                       (name, email, phone, address, vendor_id)))

def search_vendor_by_name(string):

    res = run_sql("""SELECT id, name
                       FROM crcVENDOR
                      WHERE name regexp %s
                     """, (string, ))

    return res

def search_vendor_by_email(string):

    res = run_sql("""SELECT id, name
                       FROM crcVENDOR
                      WHERE email regexp %s
                     """, (string, ))

    return res




###
### ILL/Proposals/Purchases related functions ###
###




def get_ill_request_type(ill_request_id):

    res = run_sql("""SELECT request_type
                       FROM crcILLREQUEST
                      WHERE id=%s""", (ill_request_id, ))

    if res:
        return res[0][0]
    else:
        return None

def ill_register_request(item_info, borrower_id, period_of_interest_from,
                         period_of_interest_to, status, additional_comments,
                         only_edition, request_type, budget_code='', barcode=''):

    run_sql("""insert into crcILLREQUEST(id_crcBORROWER, barcode,
                                period_of_interest_from,
                                period_of_interest_to, status, item_info,
                                borrower_comments, only_this_edition,
                                request_type, budget_code)
                    values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (borrower_id, barcode, period_of_interest_from,
                         period_of_interest_to, status, str(item_info),
                         additional_comments, only_edition,
                         request_type, budget_code))

def ill_register_request_on_desk(borrower_id, item_info,
                                 period_of_interest_from,
                                 period_of_interest_to,
                                 status, notes, only_edition, request_type,
                                 budget_code=''):

    run_sql("""insert into crcILLREQUEST(id_crcBORROWER,
                                period_of_interest_from, period_of_interest_to,
                                status, item_info, only_this_edition,
                                library_notes, request_type, budget_code)
                           values (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (borrower_id, period_of_interest_from, period_of_interest_to,
             status, str(item_info), only_edition, notes, request_type,
             budget_code))

def get_ill_request_details(ill_request_id):

    res = run_sql("""SELECT id_crcLIBRARY,
                            DATE_FORMAT(request_date,'%%Y-%%m-%%d'),
                            DATE_FORMAT(expected_date,'%%Y-%%m-%%d'),
                            DATE_FORMAT(arrival_date,'%%Y-%%m-%%d'),
                            DATE_FORMAT(due_date,'%%Y-%%m-%%d'),
                            DATE_FORMAT(return_date,'%%Y-%%m-%%d'),
                            cost,
                            barcode,
                            library_notes,
                            status
                       FROM crcILLREQUEST
                      WHERE id=%s""", (ill_request_id, ))

    if res:
        return res[0]
    else:
        return None

def register_ill_from_proposal(ill_request_id, bid=None, library_notes=''):
    """
    Register an ILL request created from an existing proposal.
    (Used in cases where proposals are 'put aside')
    """

    if not bid:
        bid = run_sql("""SELECT id_crcBORROWER
                           FROM crcILLREQUEST
                          WHERE id = %s
                      """, (ill_request_id))[0][0]

    run_sql("""insert into crcILLREQUEST(id_crcBORROWER,
                                period_of_interest_from, period_of_interest_to,
                                status, item_info, only_this_edition,
                                request_type, budget_code, library_notes)
                    SELECT %s, period_of_interest_from, period_of_interest_to,
                                %s, item_info, only_this_edition,
                                %s, budget_code, %s
                      FROM crcILLREQUEST
                     WHERE id = %s
            """,(bid, CFG_BIBCIRCULATION_ILL_STATUS_NEW, 'book',
                 str(library_notes), ill_request_id))

def get_ill_requests(status):

    if status == None:
        res = run_sql("""
                SELECT ill.id, ill.id_crcBORROWER, bor.name,
                       ill.id_crcLIBRARY, ill.status,
                       DATE_FORMAT(ill.period_of_interest_from,'%%Y-%%m-%%d'),
                       DATE_FORMAT(ill.period_of_interest_to,'%%Y-%%m-%%d'),
                       DATE_FORMAT(ill.due_date,'%%Y-%%m-%%d'),
                       ill.item_info, ill.request_type
                  FROM crcILLREQUEST ill, crcBORROWER bor
                 WHERE ill.id_crcBORROWER=bor.id
                   AND (ill.request_type=%s OR ill.request_type=%s)
              ORDER BY ill.id desc
              """, ('article', 'book'))
    else:
        res = run_sql("""
                SELECT ill.id, ill.id_crcBORROWER, bor.name,
                       ill.id_crcLIBRARY, ill.status,
                       DATE_FORMAT(ill.period_of_interest_from,'%%Y-%%m-%%d'),
                       DATE_FORMAT(ill.period_of_interest_to,'%%Y-%%m-%%d'),
                       DATE_FORMAT(ill.due_date,'%%Y-%%m-%%d'),
                       ill.item_info, ill.request_type
                  FROM crcILLREQUEST ill, crcBORROWER bor
                 WHERE ill.id_crcBORROWER=bor.id
                   AND (ill.request_type=%s OR ill.request_type=%s)
                   AND ill.status=%s
              ORDER BY ill.id desc
              """, ('article', 'book', status))

    return res

def get_all_expired_ills():
    """
    Get all expired(overdue) ills.
    """
    res = run_sql(
          """
          SELECT id,
                 id_crcBORROWER,
                 item_info,
                 overdue_letter_number,
                 DATE_FORMAT(overdue_letter_date,'%%Y-%%m-%%d')
           FROM  crcILLREQUEST
          WHERE  status = %s and due_date < CURDATE()
            AND  request_type in (%s, %s)
          """, (CFG_BIBCIRCULATION_ILL_STATUS_ON_LOAN,
                'article', 'book'))

    return res

def get_proposals(proposal_status):

    res = run_sql("""SELECT temp.*, count(req.barcode)
              FROM (SELECT ill.id, ill.id_crcBORROWER, bor.name, ill.id_crcLIBRARY,
                           ill.status, ill.barcode,
                           ill.period_of_interest_from,
                           ill.period_of_interest_to,
                           ill.item_info, ill.cost, ill.request_type
                      FROM crcILLREQUEST as ill, crcBORROWER as bor
                     WHERE ill.request_type=%s
                       AND ill.status=%s
                       AND ill.barcode!=''
                       AND ill.id_crcBORROWER=bor.id) AS temp
         LEFT JOIN (SELECT barcode
                      FROM crcLOANREQUEST
                     WHERE barcode!=''
                       AND status in (%s, %s, %s, %s)) AS req
                ON temp.barcode=req.barcode
          GROUP BY req.barcode
          ORDER BY temp.id desc""", ('proposal-book', proposal_status,
                                    CFG_BIBCIRCULATION_REQUEST_STATUS_PROPOSED,
                                    CFG_BIBCIRCULATION_REQUEST_STATUS_PENDING,
                                    CFG_BIBCIRCULATION_REQUEST_STATUS_WAITING,
                                    CFG_BIBCIRCULATION_REQUEST_STATUS_DONE))
    return res

def get_requests_on_put_aside_proposals():
    """
    @return Requests on proposed books that are 'put aside'.
    """

    res = run_sql("""SELECT ill.id, req.id, bor.id, bor.name, req.period_of_interest_from,
                           req.period_of_interest_to, ill.item_info, ill.cost
                      FROM crcILLREQUEST as ill, crcLOANREQUEST as req, crcBORROWER as bor
                     WHERE ill.barcode!='' AND req.barcode!=''
                       AND ill.barcode=req.barcode
                       AND req.id_crcBORROWER = bor.id
                       AND ill.request_type=%s
                       AND ill.status=%s
                       AND req.status=%s
           ORDER BY req.id desc""", ('proposal-book', CFG_BIBCIRCULATION_PROPOSAL_STATUS_PUT_ASIDE,
                                    CFG_BIBCIRCULATION_REQUEST_STATUS_WAITING))
    return res

def get_purchases(status):

    if status in (CFG_BIBCIRCULATION_ACQ_STATUS_ON_ORDER,
                  CFG_BIBCIRCULATION_PROPOSAL_STATUS_ON_ORDER):
        #Include proposals with status 'on order' since they are
        #purchases too and thus, is helpful if both the categories are
        #displayed in the same 'purchase-on order' list in the menu.
        res = run_sql("""SELECT ill_data.*, ill_cnt.cnt FROM
               (SELECT ill.id, ill.id_crcBORROWER, bor.name,
                       ill.id_crcLIBRARY, ill.status,
                       DATE_FORMAT(ill.period_of_interest_from,'%%Y-%%m-%%d'),
                       DATE_FORMAT(ill.period_of_interest_to,'%%Y-%%m-%%d'),
                       DATE_FORMAT(ill.due_date,'%%Y-%%m-%%d'),
                       ill.item_info, ill.cost, ill.request_type
                  FROM crcILLREQUEST ill, crcBORROWER bor
                 WHERE ill.id_crcBORROWER=bor.id
                   AND ill.request_type in (%s, %s, %s)
                   AND ill.status in (%s, %s)) AS ill_data
             LEFT JOIN (SELECT item_info, count(item_info) AS cnt
                        FROM crcILLREQUEST
                        WHERE request_type in (%s, %s, %s)
                          AND status not in (%s, %s, %s)
                        GROUP BY item_info) AS ill_cnt
                    ON ill_data.item_info = ill_cnt.item_info
              ORDER BY ill_data.id desc""", ('acq-standard', 'acq-book',
                                             'proposal-book',
                                             CFG_BIBCIRCULATION_ACQ_STATUS_ON_ORDER,
                                             CFG_BIBCIRCULATION_PROPOSAL_STATUS_ON_ORDER,
                                             'acq-standard', 'acq-book',
                                             'proposal-book',
                                             CFG_BIBCIRCULATION_ACQ_STATUS_CANCELLED,
                                             CFG_BIBCIRCULATION_PROPOSAL_STATUS_NEW,
                                             CFG_BIBCIRCULATION_PROPOSAL_STATUS_PUT_ASIDE))

    else:
        res = run_sql("""SELECT ill_data.*, ill_cnt.cnt FROM
               (SELECT ill.id, ill.id_crcBORROWER, bor.name,
                       ill.id_crcLIBRARY, ill.status,
                       DATE_FORMAT(ill.period_of_interest_from,'%%Y-%%m-%%d'),
                       DATE_FORMAT(ill.period_of_interest_to,'%%Y-%%m-%%d'),
                       DATE_FORMAT(ill.due_date,'%%Y-%%m-%%d'),
                       ill.item_info, ill.cost, ill.request_type
                  FROM crcILLREQUEST ill, crcBORROWER bor
                 WHERE ill.id_crcBORROWER=bor.id
                   AND ill.request_type in (%s, %s)
                   AND ill.status=%s) AS ill_data
             LEFT JOIN (SELECT item_info, count(item_info) AS cnt
                        FROM crcILLREQUEST
                        WHERE request_type in (%s, %s)
                          AND status!=%s
                        GROUP BY item_info) AS ill_cnt
                    ON ill_data.item_info = ill_cnt.item_info
              ORDER BY ill_data.id desc""", ('acq-standard', 'acq-book', status,
                                             'acq-standard', 'acq-book',
                                             CFG_BIBCIRCULATION_ACQ_STATUS_CANCELLED))

    return res

def search_ill_requests_title(title, date_from, date_to):

    title     = title.replace("'", "\\'")
    date_from = date_from.replace("'", "\\'")
    date_to   = date_to.replace("'", "\\'")

    tokens = title.split()
    tokens_query = ""
    for token in tokens:
        tokens_query += " AND ill.item_info like '%%%s%%' " % token


    query = """SELECT ill.id, ill.id_crcBORROWER, bor.name,
                      ill.id_crcLIBRARY, ill.status,
                      DATE_FORMAT(ill.period_of_interest_from,'%Y-%m-%d'),
                      DATE_FORMAT(ill.period_of_interest_to,'%Y-%m-%d'),
                      DATE_FORMAT(ill.due_date,'%Y-%m-%d'),
                      ill.item_info, ill.request_type
                 FROM crcILLREQUEST ill, crcBORROWER bor
                WHERE ill.id_crcBORROWER=bor.id """
    query += tokens_query
    query += """  AND DATE_FORMAT(ill.request_date,'%%Y-%%m-%%d') >= '%s'
                  AND DATE_FORMAT(ill.request_date,'%%Y-%%m-%%d') <= '%s'
             ORDER BY ill.id desc""" % (date_from, date_to)

    return run_sql(query)

def search_ill_requests_id(reqid, date_from, date_to):

    res = run_sql("""
                SELECT ill.id, ill.id_crcBORROWER, bor.name,
                       ill.id_crcLIBRARY, ill.status,
                       DATE_FORMAT(ill.period_of_interest_from,'%%Y-%%m-%%d'),
                       DATE_FORMAT(ill.period_of_interest_to,'%%Y-%%m-%%d'),
                       DATE_FORMAT(ill.due_date,'%%Y-%%m-%%d'),
                       ill.item_info, ill.request_type
                  FROM crcILLREQUEST ill, crcBORROWER bor
                 WHERE ill.id_crcBORROWER=bor.id
                   AND ill.id = %s
                   AND DATE_FORMAT(ill.request_date,'%%Y-%%m-%%d') >=%s
                   AND DATE_FORMAT(ill.request_date,'%%Y-%%m-%%d') <=%s
              ORDER BY ill.id desc""", (reqid, date_from, date_to))

    return res

def search_requests_cost(cost, date_from, date_to):

    cost = cost.replace("'", "\\'")

    res = run_sql("""
                SELECT ill.id, ill.id_crcBORROWER, bor.name,
                       ill.id_crcLIBRARY, ill.status,
                       DATE_FORMAT(ill.period_of_interest_from,'%%Y-%%m-%%d'),
                       DATE_FORMAT(ill.period_of_interest_to,'%%Y-%%m-%%d'),
                       DATE_FORMAT(ill.due_date,'%%Y-%%m-%%d'),
                       ill.item_info, ill.cost, ill.request_type, ''
                  FROM crcILLREQUEST ill, crcBORROWER bor
                 WHERE ill.id_crcBORROWER=bor.id
                   AND ill.cost like upper('%%%s%%')
                   AND DATE_FORMAT(ill.request_date,'%%Y-%%m-%%d') >= %s
                   AND DATE_FORMAT(ill.request_date,'%%Y-%%m-%%d') <= %s
              ORDER BY ill.id desc
                  """ % (cost.upper(), date_from, date_to))

    return res

def search_requests_notes(notes, date_from, date_to):

    notes = notes.replace("'", "\\'")
    date_from = date_from.replace("'", "\\'")
    date_to   = date_to.replace("'", "\\'")

    tokens = notes.split()
    tokens_query = ""
    for token in tokens:
        tokens_query += " AND library_notes like '%%%s%%' " % token

    query =  """
                SELECT ill.id, ill.id_crcBORROWER, bor.name,
                       ill.id_crcLIBRARY, ill.status,
                       DATE_FORMAT(ill.period_of_interest_from,'%Y-%m-%d'),
                       DATE_FORMAT(ill.period_of_interest_to,'%Y-%m-%d'),
                       DATE_FORMAT(ill.due_date,'%Y-%m-%d'),
                       ill.item_info, ill.cost, ill.request_type, ''
                  FROM crcILLREQUEST ill, crcBORROWER bor
                 WHERE ill.id_crcBORROWER=bor.id """
    query += tokens_query
    query += """   AND DATE_FORMAT(ill.request_date,'%%Y-%%m-%%d') >= %s
                   AND DATE_FORMAT(ill.request_date,'%%Y-%%m-%%d') <= %s
              ORDER BY ill.id desc
                  """ % (date_from, date_to)

    return run_sql(query)

def get_ill_request_borrower_details(ill_request_id):

    res = run_sql("""
        SELECT ill.id_crcBORROWER, bor.name, bor.email, bor.mailbox,
               DATE_FORMAT(ill.period_of_interest_from,'%%Y-%%m-%%d'),
               DATE_FORMAT(ill.period_of_interest_to,'%%Y-%%m-%%d'),
               ill.item_info, ill.borrower_comments,
               ill.only_this_edition, ill.request_type
          FROM crcILLREQUEST ill, crcBORROWER bor
         WHERE ill.id_crcBORROWER=bor.id and ill.id=%s""", (ill_request_id, ))

    if res:
        return res[0]
    else:
        return None

def get_purchase_request_borrower_details(ill_request_id):

    res = run_sql("""
        SELECT ill.id_crcBORROWER, bor.name, bor.email, bor.mailbox,
               DATE_FORMAT(ill.period_of_interest_from,'%%Y-%%m-%%d'),
               DATE_FORMAT(ill.period_of_interest_to,'%%Y-%%m-%%d'),
               ill.item_info, ill.borrower_comments,
               ill.only_this_edition, ill.budget_code, ill.request_type
          FROM crcILLREQUEST ill, crcBORROWER bor
         WHERE ill.id_crcBORROWER=bor.id and ill.id=%s""", (ill_request_id, ))

    if res:
        return res[0]
    else:
        return None

def update_ill_request_letter_number(ill_request_id, overdue_letter_number):
    query = ('UPDATE crcILLREQUEST set overdue_letter_number={0} '
             'where id="{1}"')
    run_sql(query.format(overdue_letter_number, ill_request_id))

def update_ill_request(ill_request_id, library_id, request_date,
                       expected_date, arrival_date, due_date, return_date,
                       status, cost, barcode, library_notes):

    run_sql("""UPDATE crcILLREQUEST
                  SET id_crcLIBRARY=%s,
                      request_date=%s,
                      expected_date=%s,
                      arrival_date=%s,
                      due_date=%s,
                      return_date=%s,
                      status=%s,
                      cost=%s,
                      barcode=%s,
                      library_notes=%s
                WHERE id=%s""",
            (library_id, request_date, expected_date,
             arrival_date, due_date, return_date, status, cost,
             barcode, library_notes, ill_request_id))

def update_purchase_request(ill_request_id, library_id, request_date,
                       expected_date, arrival_date, due_date, return_date,
                       status, cost, budget_code, library_notes):

    run_sql("""UPDATE crcILLREQUEST
                  SET id_crcLIBRARY=%s,
                      request_date=%s,
                      expected_date=%s,
                      arrival_date=%s,
                      due_date=%s,
                      return_date=%s,
                      status=%s,
                      cost=%s,
                      budget_code=%s,
                      library_notes=%s
                WHERE id=%s""",
            (library_id, request_date, expected_date,
             arrival_date, due_date, return_date, status, cost,
             budget_code, library_notes, ill_request_id))

def update_ill_request_status(ill_request_id, new_status):

    run_sql("""UPDATE crcILLREQUEST
                  SET status=%s
                WHERE id=%s""", (new_status, ill_request_id))

def get_ill_request_notes(ill_request_id):

    res = run_sql("""SELECT library_notes
                       FROM crcILLREQUEST
                      WHERE id=%s""",
                  (ill_request_id, ))

    if res:
        return res[0][0]
    else:
        return None

def update_ill_request_notes(ill_request_id, library_notes):

    run_sql("""UPDATE crcILLREQUEST
                  SET library_notes=%s
                WHERE id=%s""", (str(library_notes), ill_request_id))

def update_ill_request_item_info(ill_request_id, item_info):

    run_sql("""UPDATE crcILLREQUEST
                  SET item_info=%s
                WHERE id=%s""", (str(item_info), ill_request_id))

def get_ill_borrower(ill_request_id):

    res = run_sql("""SELECT id_crcBORROWER
                       FROM crcILLREQUEST
                      WHERE id=%s""", (ill_request_id, ))

    if res:
        return res[0][0]
    else:
        return None

def get_ill_barcode(ill_request_id):

    res = run_sql("""SELECT barcode
                       FROM crcILLREQUEST
                      WHERE id=%s""", (ill_request_id, ))

    if res:
        return res[0][0]
    else:
        return None

def update_ill_loan_status(borrower_id, barcode, return_date, loan_type):

    run_sql("""UPDATE crcLOAN
                  SET status = %s,
                      returned_on = %s
                WHERE id_crcBORROWER = %s
                  AND barcode = %s
                  AND type = %s """,
            (CFG_BIBCIRCULATION_LOAN_STATUS_RETURNED,
             return_date, borrower_id, barcode, loan_type))

def get_ill_requests_details(borrower_id):
    """
    This function is also used by the Aleph Service for the display of ILLs
    of the user for termination sheet.
    """

    res = run_sql("""SELECT id, item_info, id_crcLIBRARY,
                            DATE_FORMAT(request_date,'%%Y-%%m-%%d'),
                            DATE_FORMAT(expected_date,'%%Y-%%m-%%d'),
                            DATE_FORMAT(arrival_date,'%%Y-%%m-%%d'),
                            DATE_FORMAT(due_date,'%%Y-%%m-%%d'),
                            status, library_notes, request_type
                       FROM crcILLREQUEST
                      WHERE id_crcBORROWER=%s
                        AND status in (%s, %s, %s)
                        AND request_type in (%s, %s)
                   ORDER BY FIELD(status, %s, %s, %s)
                  """, (borrower_id, CFG_BIBCIRCULATION_ILL_STATUS_NEW,
                        CFG_BIBCIRCULATION_ILL_STATUS_REQUESTED,
                        CFG_BIBCIRCULATION_ILL_STATUS_ON_LOAN,
                        'article', 'book',
                        CFG_BIBCIRCULATION_ILL_STATUS_ON_LOAN,
                        CFG_BIBCIRCULATION_ILL_STATUS_NEW,
                        CFG_BIBCIRCULATION_ILL_STATUS_REQUESTED))

    return res

def get_proposal_requests_details(borrower_id):

    res = run_sql("""SELECT id, item_info, id_crcLIBRARY,
                            DATE_FORMAT(request_date,'%%Y-%%m-%%d'),
                            DATE_FORMAT(expected_date,'%%Y-%%m-%%d'),
                            DATE_FORMAT(arrival_date,'%%Y-%%m-%%d'),
                            DATE_FORMAT(due_date,'%%Y-%%m-%%d'),
                            status, library_notes, request_type
                       FROM crcILLREQUEST
                      WHERE id_crcBORROWER=%s
                        AND status in (%s, %s)
                        AND request_type = %s
                  """, (borrower_id, CFG_BIBCIRCULATION_PROPOSAL_STATUS_NEW,
                        CFG_BIBCIRCULATION_PROPOSAL_STATUS_PUT_ASIDE,
                        'proposal-book'))

    return res

def bor_ill_historical_overview(borrower_id):

    res = run_sql("""SELECT id, item_info, id_crcLIBRARY,
                            DATE_FORMAT(request_date,'%%Y-%%m-%%d'),
                            DATE_FORMAT(expected_date,'%%Y-%%m-%%d'),
                            DATE_FORMAT(arrival_date,'%%Y-%%m-%%d'),
                            DATE_FORMAT(due_date,'%%Y-%%m-%%d'),
                            status, library_notes, request_type
                       FROM crcILLREQUEST
                      WHERE id_crcBORROWER=%s
                        AND (status=%s OR status=%s)
                        AND request_type in (%s, %s)
                        """, (borrower_id, CFG_BIBCIRCULATION_ILL_STATUS_RETURNED,
                              CFG_BIBCIRCULATION_ILL_STATUS_RECEIVED,
                              'article', 'book'))

    return res

def bor_proposal_historical_overview(borrower_id):

    res = run_sql("""SELECT id, item_info, id_crcLIBRARY,
                            DATE_FORMAT(request_date,'%%Y-%%m-%%d'),
                            DATE_FORMAT(expected_date,'%%Y-%%m-%%d'),
                            DATE_FORMAT(arrival_date,'%%Y-%%m-%%d'),
                            DATE_FORMAT(due_date,'%%Y-%%m-%%d'),
                            status, library_notes, request_type
                       FROM crcILLREQUEST
                      WHERE id_crcBORROWER=%s
                        AND (status=%s OR status=%s)
                        AND request_type = %s
                        """, (borrower_id, CFG_BIBCIRCULATION_PROPOSAL_STATUS_ON_ORDER,
                              CFG_BIBCIRCULATION_PROPOSAL_STATUS_RECEIVED,
                              'proposal-book'))

    return res

def get_ill_notes(ill_id):

    res = run_sql("""SELECT library_notes
                       FROM crcILLREQUEST
                      WHERE id=%s""",
                  (ill_id, ))

    if res:
        return res[0][0]
    else:
        return None

def update_ill_notes(ill_id, ill_notes):

    run_sql("""UPDATE crcILLREQUEST
                  SET library_notes=%s
                WHERE id=%s """, (str(ill_notes), ill_id))

def get_ill_book_info(ill_request_id):

    res = run_sql("""SELECT item_info
                       FROM crcILLREQUEST
                      WHERE id=%s""",
                  (ill_request_id, ))

    if res:
        return res[0][0]
    else:
        return None

def delete_brief_format_cache(recid):

    run_sql("""DELETE FROM bibfmt
                WHERE format='HB'
                  AND id_bibrec=%s""", (recid,))
