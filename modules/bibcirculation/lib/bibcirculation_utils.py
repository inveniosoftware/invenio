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

"""BibCirculation Utils: Auxiliary methods of BibCirculation """

__revision__ = "$Id$"

from invenio.search_engine import get_fieldvalues
from invenio.bibtask import task_low_level_submission
import invenio.bibcirculation_dblayer as db
from invenio.urlutils import create_html_link
from invenio.config import CFG_SITE_URL, CFG_TMPDIR
from invenio.bibcirculation_config import CFG_BIBCIRCULATION_AMAZON_ACCESS_KEY, \
     CFG_BIBCIRCULATION_WORKING_DAYS, \
     CFG_BIBCIRCULATION_HOLIDAYS
from invenio.messages import gettext_set_language

import datetime, time

def hold_request_mail(recid, borrower_id):
    """
    Create the mail who will be sent for each hold requests.

    @param recid: identify the record. Primary key of bibrec.
    @type recid: int

    @param borrower_id: identify the borrower. Primary key of crcBORROWER.
    @type borrower_id: int

    @return email(body)
    """

    (book_title, book_year, book_author,
    book_isbn, book_editor) = book_information_from_MARC(recid)

    ############## need some code refactoring ###############

    more_holdings_infos = db.get_holdings_details(recid)
    borrower_infos = db.get_borrower_details(borrower_id)

    #########################################################

    title_link = create_html_link(CFG_SITE_URL +
                                  '/admin/bibcirculation/bibcirculationadmin.py/get_item_details',
                                  {'recid': recid},
                                  (book_title))

    out = """

           This is an automatic email for confirming the hold request for a
           book on behalf of:

            %s (email: %s)

            title: %s
            author: %s
            location: %s
            library: %s
            publisher: %s
            year: %s
            isbn: %s

    """ % (borrower_infos[1], borrower_infos[2],
           title_link, book_author, more_holdings_infos[0][1],
           more_holdings_infos[0][2],
           book_editor, book_year, book_isbn)

    return out


def get_book_cover(isbn):
    """
    Retrieve book cover using Amazon web services.

    @param isbn: book's isbn
    @type isbn: string

    @return book cover
    """

    from xml.dom import minidom
    import urllib

    # connect to AWS
    cover_xml = urllib.urlopen('http://ecs.amazonaws.com/onca/xml' \
                               '?Service=AWSECommerceService&AWSAccessKeyId=' \
                               + CFG_BIBCIRCULATION_AMAZON_ACCESS_KEY + \
                               '&Operation=ItemSearch&Condition=All&' \
                               'ResponseGroup=Images&SearchIndex=Books&' \
                               'Keywords=' + isbn)

    # parse XML

    try:
        xml_img = minidom.parse(cover_xml)
        retrieve_book_cover = xml_img.getElementsByTagName('MediumImage')
        book_cover = retrieve_book_cover.item(0).firstChild.firstChild.data
    except AttributeError:
        book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)

    return book_cover

def book_information_from_MARC(recid):
    """
    Retrieve book's information from MARC

    @param recid: identify the record. Primary key of bibrec.
    @type recid: int

    @return tuple with title, year, author, isbn and editor.
    """

    book_title = ' '.join(get_fieldvalues(recid, "245__a") + \
                          get_fieldvalues(recid, "245__b") + \
                          get_fieldvalues(recid, "245__n") + \
                          get_fieldvalues(recid, "245__p"))

    book_year = ' '.join(get_fieldvalues(recid, "260__c"))

    book_author = '  '.join(get_fieldvalues(recid, "100__a") + \
                            get_fieldvalues(recid, "100__u"))

    book_isbn = ' '.join(get_fieldvalues(recid, "020__a"))

    book_editor = ' , '.join(get_fieldvalues(recid, "260__a") + \
                             get_fieldvalues(recid, "260__b"))


    return (book_title, book_year, book_author, book_isbn, book_editor)


def book_title_from_MARC(recid):
    """
    Retrieve book's title from MARC

    @param recid: identify the record. Primary key of bibrec.
    @type recid: int

    @return book's title
    """

    book_title = ' '.join(get_fieldvalues(recid, "245__a") + \
                          get_fieldvalues(recid, "245__b") + \
                          get_fieldvalues(recid, "245__n") + \
                          get_fieldvalues(recid, "245__p"))

    return book_title

def update_status_if_expired(loan_id):
    """
    Update the loan's status if status is 'expired'.

    @param loan_id: identify the loan. Primary key of crcLOAN.
    @type loan_id: int
    """

    loan_status = db.get_loan_status(loan_id)

    if loan_status == 'expired':
        db.update_loan_status('on loan', loan_id)

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
    next_day = datetime.datetime(*tmp_date[:3]) + more_1_day

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
        if week_day in CFG_BIBCIRCULATION_WORKING_DAYS and due_date not in CFG_BIBCIRCULATION_HOLIDAYS:
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
    Change the status of a copy for 'available' when
    an hold request was cancelled.

    @param request_id: identify the request: Primary key of crcLOANREQUEST
    @type request_id: int
    """

    barcode_requested = db.get_requested_barcode(request_id)
    db.update_item_status('available', barcode_requested)

    return

def print_new_loan_information(req, ln):
    """
    Create a printable format with the information of the last
    loan who has been registered on the table crcLOAN.
    """

    _ = gettext_set_language(ln)

    # get the last loan from crcLOAN
    (recid, borrower_id, due_date) = db.get_last_loan()

    # get book's information
    (book_title, book_year, book_author, book_isbn, book_editor) = book_information_from_MARC(recid)

    # get borrower's data/information (name, address, email)
    (borrower_name, borrower_address, borrower_email) = db.get_borrower_data(borrower_id)

    # Generate printable format
    req.content_type = "text/html"
    req.send_http_header()

    out = """<table style='width:95%; margin:auto; max-width: 600px;'>"""
    out += """
           <tr>
                     <td><img src="%s/img/CERN_CDS_logo.png"></td>
                   </tr>
                  </table><br />""" % (CFG_SITE_URL)

    out += """<table style='color: #79d; font-size: 82%; width:95%; margin:auto; max-width: 400px;'>"""

    out += """ <tr><td align="center"><h2><strong>%s</strong></h2></td></tr>""" % (_("Loan information"))

    out += """ <tr><td align="center"><strong>%s</strong></td></tr>""" % (_("This book is sent to you ..."))

    out += """</table><br />"""
    out += """<table style='color: #79d; font-size: 82%; width:95%; margin:auto; max-width: 400px;'>"""
    out += """<tr>
                        <td width="70"><strong>%s</strong></td><td style='color: black;'>%s</td>
                  </tr>
                  <tr>
                        <td width="70"><strong>%s</strong></td><td style='color: black;'>%s</td>
                  </tr>
                  <tr>
                        <td width="70"><strong>%s</strong></td><td style='color: black;'>%s</td>
                  </tr>
                  <tr>
                        <td width="70"><strong>%s</strong></td><td style='color: black;'>%s</td>
                  </tr>
                   <tr>
                        <td width="70"><strong>%s</strong></td><td style='color: black;'>%s</td>
                  </tr>
                  """ % (_("Title"), book_title,
                         _("Author"), book_author,
                         _("Editor"), book_editor,
                         _("ISBN"), book_isbn,
                         _("Year"), book_year)

    out += """</table><br />"""

    out += """<table style='color: #79d; font-size: 82%; width:95%; margin:auto; max-width: 400px;'>"""
    out += """<tr>
                        <td width="70"><strong>%s</strong></td><td style='color: black;'>%s</td>
                  </tr>
                  <tr>
                        <td width="70"><strong>%s</strong></td><td style='color: black;'>%s</td>
                  </tr>
                  <tr>
                        <td width="70"><strong>%s</strong></td><td style='color: black;'>%s</td>
                  </tr>
                  <tr>
                        <td width="70"><strong>%s</strong></td><td style='color: black;'>%s</td>
                  </tr> """ % (_("Id"), borrower_id,
                               _("Name"), borrower_name,
                               _("Address"), borrower_address,
                               _("Email"), borrower_email)
    out += """</table> <br />"""

    out += """<table style='color: #79d; font-size: 82%; width:95%; margin:auto; max-width: 400px;'>"""

    out += """ <tr><td align="center"><h2><strong>%s: %s</strong></h2></td></tr>""" % (_("Due date"), due_date)

    out += """</table>"""

    out += """<table style='color: #79d; font-size: 82%; width:95%; margin:auto; max-width: 800px;'>
                  <tr><td><input type="button" onClick='window.print()'
                  value='Print' style='color: #fff; background: #36c; font-weight: bold;'></td></tr>
                  </table>"""

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

    requests = db.get_pdf_request_data('pending')

    req.content_type = "text/html"
    req.send_http_header()

    out = """<table style='width:100%; margin:auto; max-width: 1024px;'>"""
    out += """
                   <tr>
                     <td><img src="%s/img/CERN_CDS_logo.png"></td>
                   </tr>
                  </table><br />""" % (CFG_SITE_URL)
    out += """<table style='color: #79d; font-size: 82%; width:95%; margin:auto; max-width: 1024px;'>"""

    out += """ <tr><td align="center"><h2><strong>%s</strong></h2></td></tr>""" % (_("List of pending hold requests"))

    out += """ <tr><td align="center"><strong>%s</strong></td></tr>""" % (time.ctime())

    out += """</table><br/>"""

    out += """<table style='color: #79d; font-size: 82%; width:95%; margin:auto; max-width: 1024px;'>"""

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

    for (recid, borrower_name, library_name, location, date_from, date_to, request_date) in requests:

        out += """<tr style='color: black;'>
                         <td class="bibcirccontent">%s</td>
                         <td class="bibcirccontent">%s</td>
                         <td class="bibcirccontent">%s</td>
                         <td class="bibcirccontent">%s</td>
                         <td class="bibcirccontent">%s</td>
                         <td class="bibcirccontent">%s</td>
                         <td class="bibcirccontent">%s</td>
                      </tr>
                         """ % (borrower_name, book_title_from_MARC(recid), library_name,
                                location, date_from, date_to, request_date)

    out += """</table>
              <br />
              <br />
                  <table style='color: #79d; font-size: 82%; width:95%; margin:auto; max-width: 1024px;'>
                  <tr>
                    <td>
                      <input type=button value='Back' onClick="history.go(-1)"
                      style='color: #fff; background: #36c; font-weight: bold;'>

                      <input type="button" onClick='window.print()'
                      value='Print' style='color: #fff; background: #36c; font-weight: bold;'>
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
    nb_requests = db.get_number_requests_per_copy(barcode)
    is_on_loan = db.is_item_on_loan(barcode)

    if nb_requests == 0 and is_on_loan is not None:
        db.update_item_status('on loan', barcode)
    elif nb_requests == 0 and is_on_loan is None:
        db.update_item_status('available', barcode)
    else:
        db.update_item_status('requested', barcode)

    return


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

  """ % {'isbn': isbn,
         'author': author,
         'title': title,
         'edition': edition,
         'place': place,
         'publisher': publisher,
         'year': year}

    file_path = '%s/%s_%s.xml' % (CFG_TMPDIR, 'bibcirculation_ill_book',
                                  time.strftime("%Y%m%d_%H%M%S"))

    xml_file = open(file_path, 'w')
    xml_file.write(ill_record)
    xml_file.close()

    # Pass XML file to BibUpload.
    task_low_level_submission('bibupload', 'bibcirculation', '-P', '5', '-i',
                              file_path)

    return ill_record


def wash_recid_from_ILL_request(ill_request_id):
    """
    Get dictionnary and wash recid values.

    @param ill_request_id: identify the ILL request. Primray key of crcILLREQUEST
    @type ill_request_id: int

    @return recid
    """

    book_info = db.get_ill_book_info(ill_request_id)
    book_info = eval(book_info)

    try:
        recid = int(book_info['recid'])
    except KeyError:
        recid = None

    return recid

def get_list_of_ILL_requests():
    """
    Get list with all recids related with ILL requests
    """

    list_of_recids = []
    ill_requests = db.get_ill_ids()

    for i in range(len(ill_requests)):
        recid = wash_recid_from_ILL_request(ill_requests[i][0])
        if recid:
            list_of_recids.append(recid)

    return list_of_recids

def all_copies_are_missing(recid):
    """
    Verify if all copies of an item are missing

    @param recid: identify the record. Primary key of bibrec
    @type recid: int

    @return boolean
    """

    copies_status = db.get_copies_status(recid)
    number_of_missing = 0
    for (status) in copies_status:
        if status == 'missing':
            number_of_missing += 1

    if number_of_missing == len(copies_status):
        return True
    else:
        return False

def has_copies(recid):
    """
    Verify if a recid is item (has copies)

    @param recid: identify the record. Primary key of bibrec
    @type recid: int

    @return boolean
    """

    copies_status = db.get_copies_status(recid)

    if copies_status is None:
        return False
    else:
        if len(copies_status) == 0:
            return False
        else:
            return True

def generate_email_body(template, loan_id):
    """
    Generate the body of an email for loan recalls.

    @param template: email template
    @type template: string

    @param loan_id: identify the loan. Primary key of crcLOAN.
    @type loan_id: int

    @return email(body)
    """

    recid = db.get_loan_recid(loan_id)
    (book_title, book_year, book_author,
     book_isbn, book_editor) = book_information_from_MARC(int(recid))

    out = template % (book_title, book_year, book_author,
                      book_isbn, book_editor)

    return out

def create_item_details_url(recid, ln):
    url = '/admin/bibcirculation/bibcirculationadmin.py/get_item_details?ln=%s&recid=%s' % (ln, str(recid))
    return CFG_SITE_URL+url