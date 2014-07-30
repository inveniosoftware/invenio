
__revision__ = "$Id$"

import re

from invenio.search_engine import perform_request_search
from invenio.bibformat_engine import BibFormatObject
from invenio.urlutils import create_html_link
from invenio.config import CFG_SITE_URL

def format_element(bfo, display_search_link_to_contributions='yes', volume_label="Volume "):
    """
    Prints a table of contents.

    @param display_search_link_to_contributions: display a link searching for corresponding contribution in CDS, or not.
    """

    output = ''
    record_ids = perform_request_search(p="%s" % bfo.recID, f="962__r")
    records = []
    for record_id in record_ids:
        records.append(BibFormatObject(record_id))
	
    if(len(records)<1):
	return output

    output += '<table cellspacing="2" width="100%">'
    last_volume_header = ''
    for record in records:
        recid = "%s" % record.recID
        title = "%s" % record.field("245__a")
        if title == '':
            title = "%s" % record.field("24500a")
	
	contributers = record.field("720__a")
	if contributers == '':
	    contributers = record.field("7200a")
	if contributers == '':
	    contributers = record.field("100__a")

        link = '%s/record/%s?ln=%s' % (CFG_SITE_URL, recid, bfo.lang)
        output += '''<tr><td><a href="%s">%s</a> by %s </td></tr>''' % (link, title, contributers)
        
    output += '</table>'

    return output

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
