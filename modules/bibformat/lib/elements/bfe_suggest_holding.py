__revision__ = "$Id$"

from invenio.bibcirculation_dblayer import has_copies
from invenio.bibformat_engine import BibFormatObject
from invenio.config import CFG_SITE_SECURE_URL


def format_element(bfo, linktext='Suggest for library'):
    """
    Shows a link to the form for suggesting this record for the library.
    Will only show for records with any value for 690C_a and who has no
    registered copies in the library. 

    @param linktext: Text for the link (default "Suggest for library")
    """
    output = ''
    book_type = bfo.field('690C_a')

    if book_type != '' and not has_copies(bfo.recID):
        output += "<a href='%(sitesecureurl)s/record/%(recid)s/holdings/request?act=pr&ln=%(ln)s'>%(text)s</a>" % {
            'sitesecureurl': CFG_SITE_SECURE_URL,
            'recid': bfo.recID,
            'ln': bfo.lang,
            'text': linktext
        }

    return output


def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0