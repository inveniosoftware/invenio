## $Id$
## HTML parser for records.

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
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

"""HTML parser for records."""

__revision__ = "$Id$"

import sre
from HTMLParser import HTMLParser
from string import split
import textwrap

from invenio.alert_engine_config import CFG_WEBALERT_MAX_NUM_OF_CHARS_PER_LINE_IN_ALERT_EMAIL
from invenio.search_engine import print_record
from invenio.bibindex_engine import sre_html

def wrap(text):
    lines = textwrap.wrap(text, CFG_WEBALERT_MAX_NUM_OF_CHARS_PER_LINE_IN_ALERT_EMAIL)
    r = ''
    for l in lines:
        r += l + '\n'
    return r

def wrap_records(text):
    lines = split(text, '\n')
    result = ''
    for l in lines:
        newlines = textwrap.wrap(l, CFG_WEBALERT_MAX_NUM_OF_CHARS_PER_LINE_IN_ALERT_EMAIL)
        for ll in newlines:
            result += ll + '\n'
    return result

class RecordHTMLParser(HTMLParser):
    """A parser for the HTML returned by invenio.search_engine.print_record.

    The parser provides methods to transform the HTML returned by
    invenio.search_engine.print_record into plain text, with some
    minor formatting.
    """
    
    def __init__(self):
        HTMLParser.__init__(self)
        self.result = ''
        
    def handle_starttag(self, tag, attrs):
        if tag == 'strong':
            # self.result += '*'
            pass
        elif tag == 'a':
            self.printURL = 0
            self.unclosedBracket = 0
            for f in attrs:
                if f[1] == 'note':
                    self.result += 'Fulltext : <'
                    self.unclosedBracket = 1
                if f[1] == 'moreinfo':
                    self.result += 'Detailed record : '
                    self.printURL = 1
                if (self.printURL == 1) and (f[0] == 'href'):
                    self.result += '<' + f[1] + '>'
                
        elif tag == 'br':
            self.result += '\n'
        
    def handle_endtag(self, tag):
        if tag == 'strong':
            # self.result += '\n'
            pass
        elif tag == 'a':
            if self.unclosedBracket == 1:
                self.result += '>'
                self.unclosedBracket = 0

    def handle_data(self, data):
        if data == 'Detailed record':
            pass
        else:
            self.result += data

    def handle_comment(self, data):
        pass
    

def get_as_text(record_id):
    """Return the plain text from RecordHTMLParser of the record."""
    out = ""
    rec_in_hb = print_record(record_id)
    htparser = RecordHTMLParser()
    try:
        htparser.feed(rec_in_hb)
        out = htparser.result
    except:
        out = sre_html.sub(' ', rec_in_hb)
    out = sre.sub(r"[\-:]?\s*Detailed record\s*[\-:]?", "", out)
    out = sre.sub(r"[\-:]?\s*Similar records\s*[\-:]?", "", out)
    return out

if __name__ == "__main__":
    test_recID = 11
    print print_record(test_recID)
    print "***"
    print get_as_text(test_recID)
