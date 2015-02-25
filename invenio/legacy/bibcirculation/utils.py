# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2008, 2009, 2010, 2011, 2012, 2013 CERN.
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

"""BibCirculation Utils: Auxiliary methods of BibCirculation """

__revision__ = "$Id$"

import datetime
import random
import re
import time

from invenio.legacy.bibrecord import get_fieldvalues
from invenio.utils.url import make_invenio_opener
from invenio.legacy.search_engine import get_field_tags
from invenio.legacy.bibsched.bibtask import task_low_level_submission
from invenio.utils.text import encode_for_xml
from invenio.base.i18n import gettext_set_language
from invenio.config import CFG_SITE_URL, CFG_TMPDIR, CFG_SITE_LANG

import invenio.legacy.bibcirculation.db_layer as db
from invenio.legacy.bibcirculation.config import \
                                CFG_BIBCIRCULATION_WORKING_DAYS, \
                                CFG_BIBCIRCULATION_HOLIDAYS, \
                                CFG_CERN_SITE, \
                                CFG_BIBCIRCULATION_ITEM_STATUS_ON_LOAN, \
                                CFG_BIBCIRCULATION_ITEM_STATUS_ON_SHELF, \
                                CFG_BIBCIRCULATION_ITEM_STATUS_IN_PROCESS, \
                                CFG_BIBCIRCULATION_REQUEST_STATUS_PENDING, \
                                CFG_BIBCIRCULATION_REQUEST_STATUS_WAITING, \
                                CFG_BIBCIRCULATION_LOAN_STATUS_ON_LOAN, \
                                CFG_BIBCIRCULATION_LOAN_STATUS_EXPIRED, \
                                CFG_BIBCIRCULATION_LOAN_STATUS_RETURNED

DICC_REGEXP = re.compile("^\{('[^']*': ?('[^']*'|\"[^\"]+\"|[0-9]*|None)(, ?'[^']*': ?('[^']*'|\"[^\"]+\"|[0-9]*|None))*)?\}$")
BIBCIRCULATION_OPENER = make_invenio_opener('BibCirculation')

def search_user(column, string):
    if string is not None:
        string = string.strip()

    if CFG_CERN_SITE == 1:
        if column == 'name':
            result = db.search_borrower_by_name(string)
        else:
            if column == 'email':
                try:
                    result = db.search_borrower_by_email(string)
                except:
                    result = ()
            else:
                try:
                    result = db.search_borrower_by_ccid(string)
                except:
                    result = ()

            if result == ():
                from invenio.legacy.bibcirculation.cern_ldap \
                     import get_user_info_from_ldap

                ldap_info = 'busy'
                while ldap_info == 'busy':
                    time.sleep(1)
                    if column == 'id' or column == 'ccid':
                        ldap_info = get_user_info_from_ldap(ccid=string)
                    elif column == 'email':
                        ldap_info = get_user_info_from_ldap(email=string)
                    else:
                        ldap_info = get_user_info_from_ldap(nickname=string)

                if len(ldap_info) == 0:
                    result = ()
                else:
                    try:
                        name = ldap_info['displayName'][0]
                    except KeyError:
                        name = ""
                    try:
                        email = ldap_info['mail'][0]
                    except KeyError:
                        email = ""
                    try:
                        phone = ldap_info['telephoneNumber'][0]
                    except KeyError:
                        phone = ""
                    try:
                        address = ldap_info['physicalDeliveryOfficeName'][0]
                    except KeyError:
                        address = ""
                    try:
                        mailbox = ldap_info['postOfficeBox'][0]
                    except KeyError:
                        mailbox = ""
                    try:
                        ccid = ldap_info['employeeID'][0]
                    except KeyError:
                        ccid = ""

                    try:
                        db.new_borrower(ccid, name, email, phone,
                                    address, mailbox, '')
                    except:
                        pass
                    result = db.search_borrower_by_ccid(int(ccid))

    else:
        if column == 'name':
            result = db.search_borrower_by_name(string)
        elif column == 'email':
            result = db.search_borrower_by_email(string)
        else:
            result = db.search_borrower_by_id(string)

    return result

def update_user_info_from_ldap(user_id):

    from invenio.legacy.bibcirculation.cern_ldap import get_user_info_from_ldap

    ccid = db.get_borrower_ccid(user_id)
    ldap_info = get_user_info_from_ldap(ccid=ccid)

    if not ldap_info:
        result = ()
    else:
        try:
            name    = ldap_info['displayName'][0]
        except KeyError:
            name    = ""
        try:
            email   = ldap_info['mail'][0]
        except KeyError:
            email   = ""
        try:
            phone   = ldap_info['telephoneNumber'][0]
        except KeyError:
            phone   = ""
        try:
            address = ldap_info['physicalDeliveryOfficeName'][0]
        except KeyError:
            address = ""
        try:
            mailbox = ldap_info['postOfficeBox'][0]
        except KeyError:
            mailbox = ""
        db.update_borrower(user_id, name, email, phone, address, mailbox)
        result = db.search_borrower_by_ccid(int(ccid))
    return result

def get_book_cover(isbn):
    """
    Retrieve book cover using Amazon web services.

    @param isbn: book's isbn
    @type isbn: string

    @return book cover
    """

    from xml.dom import minidom

    # connect to AWS
    """cover_xml = BIBCIRCULATION_OPENER.open('http://ecs.amazonaws.com/onca/xml' \
                               '?Service=AWSECommerceService&AWSAccessKeyId=' \
                               + CFG_BIBCIRCULATION_AMAZON_ACCESS_KEY + \
                               '&Operation=ItemSearch&Condition=All&' \
                               'ResponseGroup=Images&SearchIndex=Books&' \
                               'Keywords=' + isbn)"""
    cover_xml=""
    # parse XML
    try:
        xml_img = minidom.parse(cover_xml)
        retrieve_book_cover = xml_img.getElementsByTagName('MediumImage')
        book_cover = retrieve_book_cover.item(0).firstChild.firstChild.data
    except:
        book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)

    return book_cover

def book_information_from_MARC(recid):
    """
    Retrieve book's information from MARC

    @param recid: identify the record. Primary key of bibrec.
    @type recid: int

    @return tuple with title, year, author, isbn and editor.
    """
    # FIXME do the same that book_title_from_MARC

    book_title  = book_title_from_MARC(recid)

    book_year   =   ''.join(get_fieldvalues(recid, "260__c"))


    author_tags = ['100__a', '700__a', '721__a']
    book_author = ''

    for tag in author_tags:
        l = get_fieldvalues(recid, tag)
        for c in l:
            book_author += c + '; '
    book_author = book_author[:-2]

    l = get_fieldvalues(recid, "020__a")
    book_isbn = ''
    for isbn in l:
        book_isbn += isbn + ', '
    book_isbn = book_isbn[:-2]

    book_editor = ', '.join(get_fieldvalues(recid, "260__a") + \
                            get_fieldvalues(recid, "260__b"))

    return (book_title, book_year, book_author, book_isbn, book_editor)

def book_title_from_MARC(recid):
    """
    Retrieve book's title from MARC

    @param recid: identify the record. Primary key of bibrec.
    @type recid: int

    @return book's title
    """

    title_tags = get_field_tags('title')

    book_title = ''
    i = 0
    while book_title == '' and i < len(title_tags):
        l = get_fieldvalues(recid, title_tags[i])
        for candidate in l:
            book_title = book_title + candidate + ': '
        i += 1

    book_title = book_title[:-2]

    return book_title

def update_status_if_expired(loan_id):
    """
    Update the loan's status if status is 'expired'.

    @param loan_id: identify the loan. Primary key of crcLOAN.
    @type loan_id: int
    """

    loan_status = db.get_loan_status(loan_id)

    if loan_status == CFG_BIBCIRCULATION_LOAN_STATUS_EXPIRED:
        db.update_loan_status(CFG_BIBCIRCULATION_ITEM_STATUS_ON_LOAN, loan_id)

    return

def get_next_day(date_string):
    """
    Get the next day

    @param date_string: date
    @type date_string: string

    return next day
    """

    # add 1 day
    more_1_day = datetime.timedelta(days=1)

    # convert date_string to datetime format
    tmp_date = time.strptime(date_string, '%Y-%m-%d')

    # calculate the new date (next day)
    next_day = datetime.datetime(tmp_date[0], tmp_date[1], tmp_date[2]) \
                                                                + more_1_day

    return next_day

def generate_new_due_date(days):
    """
    Generate a new due date (today + X days = new due date).

    @param days: number of days
    @type days: string

    @return new due date
    """

    today = datetime.date.today()

    more_X_days = datetime.timedelta(days=days)

    tmp_date = today + more_X_days

    week_day = tmp_date.strftime('%A')
    due_date = tmp_date.strftime('%Y-%m-%d')

    due_date_validated = False

    while not due_date_validated:
        if week_day in CFG_BIBCIRCULATION_WORKING_DAYS \
           and due_date not in CFG_BIBCIRCULATION_HOLIDAYS:
            due_date_validated = True

        else:
            next_day = get_next_day(due_date)
            due_date = next_day.strftime('%Y-%m-%d')
            week_day = next_day.strftime('%A')

    return due_date

def renew_loan_for_X_days(barcode):
    """
    Renew a loan based on its loan period

    @param barcode: identify the item. Primary key of crcITEM.
    @type barcode: string

    @return new due date
    """

    loan_period = db.get_loan_period(barcode)

    if loan_period == '4 weeks':
        due_date = generate_new_due_date(30)
    else:
        due_date = generate_new_due_date(7)

    return due_date

def make_copy_available(request_id):
    """
    Change the status of a copy for
    CFG_BIBCIRCULATION_ITEM_STATUS_ON_SHELF when
    an hold request was cancelled.

    @param request_id: identify the request: Primary key of crcLOANREQUEST
    @type request_id: int
    """

    barcode_requested = db.get_requested_barcode(request_id)
    db.update_item_status(CFG_BIBCIRCULATION_ITEM_STATUS_ON_SHELF, barcode_requested)
    update_requests_statuses(barcode_requested)


def print_new_loan_information(req, ln=CFG_SITE_LANG):
    """
    Create a printable format with the information of the last
    loan who has been registered on the table crcLOAN.
    """

    _ = gettext_set_language(ln)

    # get the last loan from crcLOAN
    (recid, borrower_id, due_date) = db.get_last_loan()

    # get book's information
    (book_title, book_year, book_author,
                 book_isbn, book_editor) = book_information_from_MARC(recid)

    # get borrower's data/information (name, address, email)
    (borrower_name, borrower_address,
     borrower_mailbox, borrower_email) = db.get_borrower_data(borrower_id)

    # Generate printable format
    req.content_type = "text/html"
    req.send_http_header()

    out = """<table style='width:95%; margin:auto; max-width: 600px;'>"""
    out += """
           <tr>
                     <td><img src="%s/img/CERN_CDS_logo.png"></td>
                   </tr>
                  </table><br />""" % (CFG_SITE_URL)

    out += """<table style='color: #79d; font-size: 82%; width:95%;
                            margin:auto; max-width: 400px;'>"""

    out += """  <tr>
                    <td align="center">
                        <h2><strong>%s</strong></h2>
                    </td>
                </tr>""" % (_("Loan information"))

    out += """  <tr>
                    <td align="center"><strong>%s</strong></td>
                </tr>""" % (_("This book has been sent to you:"))

    out += """</table><br />"""
    out += """<table style='color: #79d; font-size: 82%; width:95%;
                            margin:auto; max-width: 400px;'>"""
    out += """  <tr>
                    <td width="70"><strong>%s</strong></td>
                    <td style='color: black;'>%s</td>
                </tr>
                <tr>
                    <td width="70"><strong>%s</strong></td>
                    <td style='color: black;'>%s</td>
                </tr>
                <tr>
                    <td width="70"><strong>%s</strong></td>
                    <td style='color: black;'>%s</td>
                </tr>
                <tr>
                    <td width="70"><strong>%s</strong></td>
                    <td style='color: black;'>%s</td>
                </tr>
                <tr>
                    <td width="70"><strong>%s</strong></td>
                    <td style='color: black;'>%s</td>
                </tr>
                  """ % (_("Title"),  book_title,
                         _("Author"), book_author,
                         _("Editor"), book_editor,
                         _("ISBN"),   book_isbn,
                         _("Year"),   book_year)

    out += """</table><br />"""

    out += """<table style='color: #79d; font-size: 82%; width:95%;
                            margin:auto; max-width: 400px;'>"""
    out += """  <tr>
                    <td width="70"><strong>%s</strong></td>
                    <td style='color: black;'>%s</td>
                </tr>
                <tr>
                    <td width="70"><strong>%s</strong></td>
                    <td style='color: black;'>%s</td>
                </tr>
                <tr>
                    <td width="70"><strong>%s</strong></td>
                    <td style='color: black;'>%s</td>
                </tr>
                <tr>
                    <td width="70"><strong>%s</strong></td>
                    <td style='color: black;'>%s</td>
                </tr>
           """ % (_("Name"),    borrower_name,
                  _("Mailbox"), borrower_mailbox,
                  _("Address"), borrower_address,
                  _("Email"),   borrower_email)

    out += """</table>
              <br />"""

    out += """<table style='color: #79d; font-size: 82%; width:95%;
                            margin:auto; max-width: 400px;'>"""

    out += """  <tr>
                    <td align="center"><h2><strong>%s: %s</strong></h2></td>
                </tr>""" % (_("Due date"), due_date)

    out += """</table>"""

    out += """<table style='color: #79d; font-size: 82%; width:95%;
                            margin:auto; max-width: 800px;'>
                <tr>
                    <td>
                        <input type="button" onClick='window.print()'
                               value='Print' style='color: #fff;
                               background: #36c; font-weight: bold;'>
                    </td>
                </tr>
              </table>
           """

    req.write("<html>")
    req.write(out)
    req.write("</html>")

    return "\n"

def print_pending_hold_requests_information(req, ln):
    """
    Create a printable format with all the information about all
    pending hold requests.
    """

    _ = gettext_set_language(ln)

    requests = db.get_pdf_request_data(CFG_BIBCIRCULATION_REQUEST_STATUS_PENDING)

    req.content_type = "text/html"
    req.send_http_header()

    out = """<table style='width:100%; margin:auto; max-width: 1024px;'>"""
    out += """
                   <tr>
                     <td><img src="%s/img/CERN_CDS_logo.png"></td>
                   </tr>
                  </table><br />""" % (CFG_SITE_URL)
    out += """<table style='color: #79d; font-size: 82%;
                     width:95%; margin:auto; max-width: 1024px;'>"""

    out += """  <tr>
                    <td align="center"><h2><strong>%s</strong></h2></td>
                </tr>""" % (_("List of pending hold requests"))

    out += """  <tr>
                    <td align="center"><strong>%s</strong></td>
                </tr>""" % (time.ctime())

    out += """</table><br/>"""

    out += """<table style='color: #79d; font-size: 82%;
                     width:95%; margin:auto; max-width: 1024px;'>"""

    out += """<tr>
                       <td><strong>%s</strong></td>
                       <td><strong>%s</strong></td>
                       <td><strong>%s</strong></td>
                       <td><strong>%s</strong></td>
                       <td><strong>%s</strong></td>
                       <td><strong>%s</strong></td>
                       <td><strong>%s</strong></td>
                  </tr>
                       """ % (_("Borrower"),
                              _("Item"),
                              _("Library"),
                              _("Location"),
                              _("From"),
                              _("To"),
                              _("Request date"))

    for (recid, borrower_name, library_name, location,
         date_from, date_to, request_date) in requests:

        out += """<tr style='color: black;'>
                         <td class="bibcirccontent">%s</td>
                         <td class="bibcirccontent">%s</td>
                         <td class="bibcirccontent">%s</td>
                         <td class="bibcirccontent">%s</td>
                         <td class="bibcirccontent">%s</td>
                         <td class="bibcirccontent">%s</td>
                         <td class="bibcirccontent">%s</td>
                      </tr>
                         """ % (borrower_name, book_title_from_MARC(recid),
                                library_name, location, date_from, date_to,
                                request_date)

    out += """</table>
              <br />
              <br />
                  <table style='color: #79d; font-size: 82%;
                  width:95%; margin:auto; max-width: 1024px;'>
                  <tr>
                    <td>
                      <input type=button value='Back' onClick="history.go(-1)"
                             style='color: #fff; background: #36c;
                             font-weight: bold;'>

                      <input type="button" onClick='window.print()'
                      value='Print' style='color: #fff;
                                background: #36c; font-weight: bold;'>
                    </td>
                  </tr>
                  </table>"""

    req.write("<html>")
    req.write(out)
    req.write("</html>")

    return "\n"

def get_item_info_for_search_result(recid):
    """
    Get the item's info from MARC in order to create a
    search result with more details

    @param recid: identify the record. Primary key of bibrec.
    @type recid: int

    @return book's informations (author, editor and number of copies)
    """

    book_author = '  '.join(get_fieldvalues(recid, "100__a") + \
                            get_fieldvalues(recid, "100__u"))

    book_editor = ' , '.join(get_fieldvalues(recid, "260__a") + \
                             get_fieldvalues(recid, "260__b") + \
                             get_fieldvalues(recid, "260__c"))

    book_copies = '  '.join(get_fieldvalues(recid, "964__a"))

    book_infos = (book_author, book_editor, book_copies)

    return book_infos


def update_request_data(request_id):
    """
    Update the status of a given request.

    @param request_id: identify the request: Primary key of crcLOANREQUEST
    @type request_id: int
    """

    barcode = db.get_request_barcode(request_id)
    is_on_loan = db.is_item_on_loan(barcode)

    if is_on_loan is not None:
        db.update_item_status(CFG_BIBCIRCULATION_ITEM_STATUS_ON_LOAN, barcode)
    else:
        db.update_item_status(CFG_BIBCIRCULATION_ITEM_STATUS_ON_SHELF, barcode)

    update_requests_statuses(barcode)


    return True


def compare_dates(date):
    """
    Compare given date with today

    @param date: given date
    @type date: string

    @return boolean
    """

    if date < time.strftime("%Y-%m-%d"):
        return False
    else:
        return True

def validate_date_format(date):
    """
    Verify the date format

    @param date: given date
    @type date: string

    @return boolean
    """

    try:
        if time.strptime(date, "%Y-%m-%d"):
            if compare_dates(date):
                return True
        else:
            return False
    except ValueError:
        return False

def create_ill_record(book_info):
    """
    Create a new ILL record

    @param book_info: book's information
    @type book_info: tuple

    @return MARC record
    """

    (title, author, place, publisher, year, edition, isbn) = book_info

    ill_record = """
        <record>
            <datafield tag="020" ind1=" " ind2=" ">
                <subfield code="a">%(isbn)s</subfield>
            </datafield>
            <datafield tag="100" ind1=" " ind2=" ">
                <subfield code="a">%(author)s</subfield>
            </datafield>
            <datafield tag="245" ind1=" " ind2=" ">
                <subfield code="a">%(title)s</subfield>
            </datafield>
            <datafield tag="250" ind1=" " ind2=" ">
                <subfield code="a">%(edition)s</subfield>
            </datafield>
            <datafield tag="260" ind1=" " ind2=" ">
                <subfield code="a">%(place)s</subfield>
                <subfield code="b">%(publisher)s</subfield>
                <subfield code="c">%(year)s</subfield>
            </datafield>
            <datafield tag="980" ind1=" " ind2=" ">
                <subfield code="a">ILLBOOK</subfield>
            </datafield>
        </record>
  """ % {'isbn':      encode_for_xml(isbn),
         'author':    encode_for_xml(author),
         'title':     encode_for_xml(title),
         'edition':   encode_for_xml(edition),
         'place':     encode_for_xml(place),
         'publisher': encode_for_xml(publisher),
         'year':      encode_for_xml(year)}

    file_path = '%s/%s_%s.xml' % (CFG_TMPDIR, 'bibcirculation_ill_book',
                                  time.strftime("%Y%m%d_%H%M%S"))

    xml_file = open(file_path, 'w')
    xml_file.write(ill_record)
    xml_file.close()

    # Pass XML file to BibUpload.
    task_low_level_submission('bibupload', 'bibcirculation',
                              '-P', '5', '-i', file_path)

    return ill_record


def wash_recid_from_ILL_request(ill_request_id):
    """
    Get dictionnary and wash recid values.

    @param ill_request_id: identify the ILL request. Primray key of crcILLREQUEST
    @type ill_request_id: int

    @return recid
    """

    book_info = db.get_ill_book_info(ill_request_id)
    if looks_like_dictionary(book_info):
        book_info = eval(book_info)
    else:
        book_info = None

    try:
        recid = int(book_info['recid'])
    except KeyError:
        recid = None

    return recid

def all_copies_are_missing(recid):
    """
    Verify if all copies of an item are missing

    @param recid: identify the record. Primary key of bibrec
    @type recid: int

    @return boolean
    """

    copies_status = db.get_copies_status(recid)
    number_of_missing = 0
    if copies_status == None:
        return True
    else:
        for (status) in copies_status:
            if status == 'missing':
                number_of_missing += 1

        if number_of_missing == len(copies_status):
            return True
        else:
            return False

#def has_copies(recid):
#    """
#    Verify if a recid is item (has copies)
#
#    @param recid: identify the record. Primary key of bibrec
#    @type recid: int
#
#    @return boolean
#    """
#
#    copies_status = db.get_copies_status(recid)
#
#    if copies_status is None:
#        return False
#    else:
#        if len(copies_status) == 0:
#            return False
#        else:
#            return True

def generate_email_body(template, loan_id, ill=0):
    """
    Generate the body of an email for loan recalls.

    @param template: email template
    @type template: string

    @param loan_id: identify the loan. Primary key of crcLOAN.
    @type loan_id: int

    @return email(body)
    """

    if ill:
        # Inter library loan.
        out = template
    else:
        recid = db.get_loan_recid(loan_id)
        (book_title, book_year, book_author,
         book_isbn, book_editor) = book_information_from_MARC(int(recid))

        out = template % (book_title, book_year, book_author,
                      book_isbn, book_editor)

    return out

def create_item_details_url(recid, ln):
    url = '/admin2/bibcirculation/get_item_details?ln=%s&recid=%s' % (ln,
                                                                    str(recid))
    return CFG_SITE_URL + url

def tag_all_requests_as_done(barcode, user_id):
    recid = db.get_id_bibrec(barcode)
    description = db.get_item_description(barcode)
    list_of_barcodes = db.get_barcodes(recid, description)
    for bc in list_of_barcodes:
        db.tag_requests_as_done(user_id, bc)

def update_requests_statuses(barcode):

    recid = db.get_id_bibrec(barcode)
    description = db.get_item_description(barcode)

    list_of_pending_requests = db.get_requests(recid, description,
                                    CFG_BIBCIRCULATION_REQUEST_STATUS_PENDING)
    some_copy_available = False
    copies_status = db.get_copies_status(recid, description)
    if copies_status is not None:
        for status in copies_status:
            if status in (CFG_BIBCIRCULATION_ITEM_STATUS_ON_SHELF,
                          CFG_BIBCIRCULATION_ITEM_STATUS_IN_PROCESS):
                some_copy_available = True

    if len(list_of_pending_requests) == 1:
        if not some_copy_available:
            db.update_loan_request_status(CFG_BIBCIRCULATION_REQUEST_STATUS_WAITING,
                                          list_of_pending_requests[0][0])
        else:
            return list_of_pending_requests[0][0]

    elif len(list_of_pending_requests) == 0:
        if some_copy_available:
            list_of_waiting_requests = db.get_requests(recid, description,
                                    CFG_BIBCIRCULATION_REQUEST_STATUS_WAITING)
            if len(list_of_waiting_requests) > 0:
                db.update_loan_request_status(CFG_BIBCIRCULATION_REQUEST_STATUS_PENDING,
                                              list_of_waiting_requests[0][0])
                return list_of_waiting_requests[0][0]

    elif len(list_of_pending_requests) > 1:
        for request in list_of_pending_requests:
            db.update_loan_request_status(CFG_BIBCIRCULATION_REQUEST_STATUS_WAITING,
                                          request[0])
        list_of_waiting_requests = db.get_requests(recid, description,
                                    CFG_BIBCIRCULATION_REQUEST_STATUS_WAITING)
        if some_copy_available:
            db.update_loan_request_status(CFG_BIBCIRCULATION_REQUEST_STATUS_PENDING,
                                          list_of_waiting_requests[0][0])
            return list_of_waiting_requests[0][0]

    return None

def is_periodical(recid):
    rec_type = get_fieldvalues(recid, "690C_a")
    if len(rec_type) > 0:
        for value in rec_type:
            if value == 'PERI':
                return True

    return False

def has_date_format(date):

    if type(date) is not str:
        return False

    date = date.strip()

    if len(date) is not 10:
        return False
    elif date[4] is not '-' and date[7] is not '-':
        return False
    else:
        year = date[:4]
        month = date[5:7]
        day = date[8:]

        return year.isdigit() and month.isdigit() and day.isdigit()

def generate_tmp_barcode():

    tmp_barcode = 'tmp-' + str(random.random())[-8:]

    while(db.barcode_in_use(tmp_barcode)):
        tmp_barcode = 'tmp-' + str(random.random())[-8:]

    return tmp_barcode


def check_database():

    from invenio.legacy.dbquery import run_sql

    r1 = run_sql(""" SELECT it.barcode, it.status, ln.status
                       FROM crcITEM it, crcLOAN ln
                      WHERE ln.barcode=it.barcode
                        AND it.status=%s
                        AND ln.status!=%s
                        AND ln.status!=%s
                        AND ln.status!=%s
                 """, (CFG_BIBCIRCULATION_ITEM_STATUS_ON_LOAN,
                        CFG_BIBCIRCULATION_LOAN_STATUS_ON_LOAN,
                        CFG_BIBCIRCULATION_LOAN_STATUS_EXPIRED,
                        CFG_BIBCIRCULATION_LOAN_STATUS_RETURNED))

    r2 = run_sql(""" SELECT it.barcode
                       FROM crcITEM it, crcLOAN ln
                      WHERE ln.barcode=it.barcode
                        AND it.status=%s
                        AND (ln.status=%s or ln.status=%s)
                 """, (CFG_BIBCIRCULATION_ITEM_STATUS_ON_SHELF,
                        CFG_BIBCIRCULATION_LOAN_STATUS_ON_LOAN,
                        CFG_BIBCIRCULATION_LOAN_STATUS_EXPIRED))

    r3 = run_sql(""" SELECT l1.barcode, l1.id,
                            DATE_FORMAT(l1.loaned_on,'%%Y-%%m-%%d %%H:%%i:%%s'),
                            DATE_FORMAT(l2.loaned_on,'%%Y-%%m-%%d %%H:%%i:%%s')
                       FROM crcLOAN l1,
                            crcLOAN l2
                      WHERE l1.id!=l2.id
                        AND l1.status!=%s
                        AND l1.status=l2.status
                        AND l1.barcode=l2.barcode
                   ORDER BY l1.loaned_on
                 """, (CFG_BIBCIRCULATION_LOAN_STATUS_RETURNED, ))

    r4 = run_sql(""" SELECT id, id_crcBORROWER, barcode,
                            due_date, number_of_renewals
                       FROM crcLOAN
                      WHERE status=%s
                        AND due_date>NOW()
                 """, (CFG_BIBCIRCULATION_LOAN_STATUS_EXPIRED, ))

    return (len(r1), len(r2), len(r3), len(r4))

def looks_like_dictionary(candidate_string):
    if re.match(DICC_REGEXP, candidate_string):
        return True
    else:
        return False
