# -*- coding: utf-8 -*-
##
## $Id: bibcirculation_utils.py,v 1.1 2008/08/25 12:44:35 joaquim Exp $
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

"""BibCirculation Utils: Auxiliary methods of BibCirculation """

__revision__ = "$Id: bibcirculation_utils.py,v 1.1 2008/08/25 12:44:35 joaquim Exp $"

from invenio.search_engine import get_fieldvalues
import invenio.bibcirculation_dblayer as db
from invenio.urlutils import create_html_link
from invenio.config import CFG_SITE_URL
from invenio.bibcirculation_config import ACCESS_KEY

def hold_request_mail(recid, borrower_id):
    """
    Create the mail who will be sent for each hold requests.
    """

    (book_title, book_year, book_author, book_isbn, book_editor) = book_information_from_MARC(recid)
    more_holdings_infos = db.get_holdings_details(recid)
    borrower_infos = db.get_borrower_details(borrower_id)

    title_link = create_html_link(CFG_SITE_URL +
                                          '/admin/bibcirculation/bibcirculationadmin.py/get_item_details',
                                          {'recid': recid},
                                          (book_title))
    out = """
    Hello,

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


        Best regards
        --
        CERN Document Server <http://cdsweb.cern.ch>
        Need human intervention?  Contact <cds.support@cern.ch>

    """ % (borrower_infos[0][1], borrower_infos[0][2],
           title_link, book_author, more_holdings_infos[0][1],
           more_holdings_infos[0][2],
           book_editor, book_year, book_isbn)

    return out


def get_book_cover(isbn):
    """
    Retrieve book cover using Amazon web services.
    """

    from xml.dom import minidom
    import urllib

    cover_xml = urllib.urlopen('http://ecs.amazonaws.com/onca/xml' \
                               '?Service=AWSECommerceService&AWSAccessKeyId=' + ACCESS_KEY + \
                               '&Operation=ItemSearch&Condition=All&' \
                               'ResponseGroup=Images&SearchIndex=Books&' \
                               'Keywords=' + isbn)

    xml_img = minidom.parse(cover_xml)

    try:
        retrieve_book_cover = xml_img.getElementsByTagName('MediumImage')
        book_cover = retrieve_book_cover.item(0).firstChild.firstChild.data
    except AttributeError:
        book_cover = "%s/img/book_cover_placeholder.gif" % (CFG_SITE_URL)

    return book_cover

def book_information_from_MARC(recid):
    """
    Retrieve book information from MARC
    """

    book_title = ' '.join(get_fieldvalues(recid, "245__a") + \
                          get_fieldvalues(recid, "245__b") + \
                          get_fieldvalues(recid, "245__n") + \
                          get_fieldvalues(recid, "245__p"))

    book_year = ' '.join(get_fieldvalues(recid, "260__c"))

    book_author = '  '.join(get_fieldvalues(recid, "270__p") + \
                            get_fieldvalues(recid, "100__a") +
                            get_fieldvalues(recid, "100__u"))

    book_isbn = ' '.join(get_fieldvalues(recid, "020__a"))

    book_editor = ' , '.join(get_fieldvalues(recid, "260__b") + \
                             get_fieldvalues(recid, "260__a"))


    return (book_title, book_year, book_author, book_isbn, book_editor)


def book_title_from_MARC(recid):
    """
    Retrieve book's title from MARC
    """
    book_title = ' '.join(get_fieldvalues(recid, "245__a") + \
                          get_fieldvalues(recid, "245__b") + \
                          get_fieldvalues(recid, "245__n") + \
                          get_fieldvalues(recid, "245__p"))

    return book_title

