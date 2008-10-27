# -*- coding: utf-8 -*-
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

"""BibCirculation .........."""

__revision__ = "$Id$"

# bibcirculation imports
import invenio.bibcirculation_dblayer as db
import invenio.template
bibcirculation_templates = invenio.template.load('bibcirculation')

# others invenio imports
from invenio.config import \
     CFG_SITE_LANG
from invenio.dateutils import get_datetext
import datetime
from invenio.search_engine import get_fieldvalues


def perform_loanshistoricaloverview(uid, ln=CFG_SITE_LANG):
    """
    @param ln: language of the page
    """

    result = db.get_historical_overview(uid)

    body = bibcirculation_templates.tmpl_loanshistoricaloverview(result=result, ln=ln)

    return body


def perform_borrower_loans(uid, barcode, borrower, ln=CFG_SITE_LANG):
    """
    @param ln: language of the page
    """

    infos = []

    now = datetime.date.today()
    year = now.year
    month = now.month + 1
    day = now.day
    new_due_date = get_datetext(year, month, day)

    if barcode:
        recid = db.get_id_bibrec(barcode)
        queue = db.get_queue_request(recid)
        title = ''.join(get_fieldvalues(recid, "245__a"))

        if len(queue) != 0:
            infos.append("Sorry. It is not possible to renew your loan for "+title+". Another user is waiting for this book.")
        else:
            db.update_due_date(barcode, new_due_date)
            infos.append("Done!!!")

    elif borrower:
        list_of_recids = db.get_recid_borrower_loans(borrower)


        for (recid) in list_of_recids:
            recid = recid[0]
            queue = db.get_queue_request(recid)
            title = ''.join(get_fieldvalues(recid, "245__a"))

            if len(queue) != 0:
                infos.append("Sorry. It is not possible to renew your loan for "+title+". Another user is waiting for this book.")
            else:
                db.update_recid_due_date_borrower(borrower, new_due_date, recid)
                infos.append("Done :-) ")

    result = db.get_borrower_loans(uid)
    #name = db.get_borrower_name(uid)

    body = bibcirculation_templates.tmpl_yourloans(result=result, uid=uid, infos=infos, ln=ln)

    return body

def perform_get_holdings_information(recid, ln=CFG_SITE_LANG):
    """
    @param recid: recID - CDS Invenio record identifier
    @param ln: language of the page
    """
    infos = []

    nb_requests = db.get_number_requests(recid)

    nb_copies = db.get_number_copies(recid)

    hold_details = db.get_holdings_details(recid)
    loan_details = db.get_loan_details(recid)

    if len(loan_details) != 0:
        for(barcod, stat) in loan_details:
            barcode = barcod
            status = stat
        due_date = " - "
        nb_requests = ""
    else:
        barcode = ""
        status = "On loan"
        title = ''.join(get_fieldvalues(recid, "245__a"))
        due_date = db.get_due_date_loan(recid)
        infos.append('Sorry. Actually, all copies of "' + title + '" are on loan. One copy should be available on ' + due_date + '.')
        nb_requests = db.get_number_requests(recid)

    body = bibcirculation_templates.tmpl_holdings_information(recid=recid,
                                                              status=status,
                                                              barcode=barcode,
                                                              hold_details=hold_details,
                                                              nb_requests=nb_requests,
                                                              nb_copies=nb_copies,
                                                              due_date=due_date,
                                                              infos=infos,
                                                              ln=ln)

    return body


def perform_get_pending_loan_request(ln=CFG_SITE_LANG):
    """
    @param ln: language of the page
    """

    status = db.get_pending_loan_request("pending")

    body = bibcirculation_templates.tmpl_get_pending_loan_request(status=status,
                                                                  ln=ln)

    return body


def perform_new_loan_request(uid,
                             recid,
                             due_date,
                             barcode,
                             from_year=0,
                             from_month=0,
                             from_day=0,
                             to_year=0,
                             to_month=0,
                             to_day=0,
                             ln=CFG_SITE_LANG):
    """
    @param recid: recID - CDS Invenio record identifier
    """

    body = bibcirculation_templates.tmpl_new_loan_request(uid=uid,
                                                          recid=recid,
                                                          barcode=barcode,
                                                          ln=ln)

    return body


def perform_new_loan_request_send(uid,
                                  recid,
                                  barcode,
                                  from_year=0,
                                  from_month=0,
                                  from_day=0,
                                  to_year=0,
                                  to_month=0,
                                  to_day=0,
                                  ln=CFG_SITE_LANG):

    """
    @param recid: recID - CDS Invenio record identifier
    @param ln: language of the page
    """

    request_from = get_datetext(from_year, from_month, from_day)
    request_to = get_datetext(to_year, to_month, to_day)

    body = bibcirculation_templates.tmpl_new_loan_request_send(ln=ln)

    db.new_loan_request(uid=uid,
                        recid=recid,
                        barcode=barcode,
                        date_from=request_from,
                        date_to=request_to,
                        status='pending',
                        notes='')

    if barcode !="":
        db.update_item_status('requested', barcode)

    return body

