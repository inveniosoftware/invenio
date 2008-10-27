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

__revision__ = "$Id$"

"""
This file use screen scraping techique to get informations from ALEPH.
Using sysno, this file can find information about a book.
"""

# NON INVENIO IMPORTS
import urllib
import re
import time

from invenio.search_engine import get_fieldvalues
from invenio.search_engine import perform_request_search
from invenio.dbquery import run_sql

# GLOBAL VARS
_LP_ = re.compile('<!--Loan status-->\n<td class=td1 nowrap>(.*?)</td>\n<!--Due date-->', re.DOTALL)
_LIB_ = re.compile('<!--Sub-library-->\n<td class=td1 nowrap>(.*?)</td>\n<!--Collection-->', re.DOTALL)
_LOC_ = re.compile('<!--Location-->\n<td class=td1 nowrap>(.*?)</td>\n<!--Pages-->', re.DOTALL)
_BAR_ = re.compile('<!--Barcode-->\n<td class=td1>(.*?)</td>', re.DOTALL)

def get_book_info(sysno):
    """
    Returns holding informations.

    @param sysno ALEPH system number
    """

    # GET SESSION VALUE
    session_value = urllib.urlopen('http://cdslib.cern.ch:4505/cgi-bin/session')
    session = session_value.read()

    # GET INFO FROM ALEPH USING SESSION & SYSNO
    aleph_info = urllib.urlopen("http://guest:aguest@cdslib.cern.ch:4505/ALEPH/"\
                                    +session+\
                                    "-00024/item-global?P01=CER01&P02="\
                                    +sysno+\
                                    "&P03=&P04=&P05=")
    info = aleph_info.read()
    nb_copies = re.findall('<!--Barcode-->', info)
    result = []

    for i in range(len(nb_copies)):

        lp = re.findall(_LP_, info)[i]
        #lib = re.findall(_LIB_, info)[i]
        loc = re.findall(_LOC_, info)[i]
        bar = re.findall(_BAR_, info)[i]

        # tuple with (loan period, library, location, barcode)
        tup = (bar, loc, lp)

        result.append(tup)

    return result


def holdings_info():

    # list of all recids in the collection 'Books'
    books_recids = perform_request_search(cc='Books')

    for recid in books_recids:

        t0 = time.time()

        # for each recid get the sysno number
        sysno = get_fieldvalues(recid, '970__a')
        sysno = sysno[:9]

        # get list with tuples
        #
        # e.g.  get_book_info('002651748')
        #
        # [('CM-B00036572', '004.438.Python LUT', 'Four week loan'),
        # ('CM-B00036976', '004.438.Python LUT', 'Four week loan'),
        # ('CM-B00037141', '004.438.Python LUT', 'Four week loan')]

        book_info = get_book_info(sysno)

        for (bar, loc, lp) in book_info:

            # insert into crcITEM book's values
            run_sql("""insert into crcITEM (barcode, id_bibrec,
                                            id_crcLIBRARY, location,
                                            loan_period, status,
                                            creation_date, modification_date,
                                            number_of_requests)
                                            values (%s, %s, '1', %s, %s, 'available', NOW(), NOW(), '0');
                    """, (bar, recid, loc, lp))

        t1 = time.time()
        t = t0 - t1

        output = "recid: " + recid + " >>>  Done. in " + t + " seconds."

    return output


