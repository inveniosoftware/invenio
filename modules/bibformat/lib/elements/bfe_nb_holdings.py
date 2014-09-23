__revision__ = "$Id$"

from invenio.bibcirculation_dblayer import get_number_copies
from invenio.bibcirculation_dblayer import has_copies
from invenio.bibformat_engine import BibFormatObject
from invenio.config import CFG_SITE_SECURE_URL


def format_element(bfo, title='Paper collection(s)',
                   link_text='List Issues',
                   key_class='record-meta-key',
                   value_class='record-meta-value'):
    """
    Shows a link to the holdings of the current journal. Will not show unless
    690C_a = 'PERI' and there are registered copies of the record in the library.

    @param title: Title of entry (default "Paper collection(s)")
    @param link_text: Text for the link (default "List Issues")
    @param key_class: CSS class of key (Type) div wrapper (default "record-meta-key")
    @param value_class: CSS class of value div wrapper (default "record-meta-value")
    """
    output = ''
    book_type = bfo.field('690C_a')

    if book_type == 'PERI' and has_copies(bfo.recID):
        nb_copies = get_number_copies(bfo.recID);
        output += "<div class='%(key_class)s'>%(title)s</div>" \
                  "<div class='%(value_class)s'>" \
                  "    <a href='%(sitesecureurl)s/record/%(recid)s/holdings?ln=%(ln)s'>%(link_text)s (%(nb_copies)d)</a>" \
                  "</div>" % {
            'key_class': key_class,
            'title': title,
            'value_class': value_class,
            'sitesecureurl': CFG_SITE_SECURE_URL,
            'recid': bfo.recID,
            'ln': bfo.lang,
            'link_text': link_text,
            'nb_copies': nb_copies
        }

    return output


def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0