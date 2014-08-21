
__revision__ = "$Id$"

import re

from invenio.search_engine import perform_request_search
from invenio.bibformat_engine import BibFormatObject
from invenio.config import CFG_SITE_URL

def format_element(bfo, parent_type='Conference', key_class='record-meta-key', value_class='record-meta-value'):
    """
    Prints the conference/parent of the current record

    @param parent_type: Type of parent (default "Conference")
    @param key_class: CSS class of key (Type) div wrapper (default "record-meta-key")
    @param value_class: CSS class of value div wrapper (default "record-meta-value")
    """

    output = ''
    parent_id = bfo.fields("962__r")
    if len(parent_id) == 1:
        output += '<div class="%s">%s: </div>' % (key_class, parent_type)
        parent_rec = BibFormatObject(parent_id[0])
        parent_title = "%s" % parent_rec.field("111__a")
        if parent_title == '':
            parent_title = "%s" % parent_rec.field("245__a")
        if parent_title == '':
            parent_title = "%s" % parent_rec.field("24500a")

        link = '%s/record/%s?ln=%s' % (CFG_SITE_URL, parent_id[0], bfo.lang)
        output += '<div class="%s"><a href="%s">%s</a></div>' % (value_class, link, parent_title)
    return output


def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
