## $Id$
## HTML parser for records.

## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002, 2003, 2004, 2005 CERN.
##
## The CDSware is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## The CDSware is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.  
##
## You should have received a copy of the GNU General Public License
## along with CDSware; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""HTML parser for records."""

## rest of the Python code goes below

__version__ = "$Id$"

from HTMLParser import HTMLParser
from string import split

from cdsware.config import *
from cdsware.search_engine import print_record
from cdsware import textwrap

WRAPWIDTH = 72

def wrap(text):
    global WRAPWIDTH
    
    lines = textwrap.wrap(text, WRAPWIDTH)
    r = ''
    for l in lines:
        r += l + '\n'
    return r

def wrap_records(text):
    global WRAPWIDTH
    
    lines = split(text, '\n')
    result = ''
    for l in lines:
        newlines = textwrap.wrap(l, WRAPWIDTH)
        for ll in newlines:
            result += ll + '\n'
    return result

class RecordHTMLParser(HTMLParser):
    """A parser for the HTML returned by cdsware.search_engine.print_record.

    The parser provides methods to transform the HTML returned by
    cdsware.search_engine.print_record into plain text, with some
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

    rec = print_record(record_id)
    htparser = RecordHTMLParser()
    try:
        htparser.feed(rec)
        return htparser.result
    except:
        #htparser.close()
        return wrap(htparser.result + 'Detailed record: <http://cdsweb.cern.ch/search.py?recid=%s>.' % record_id)


if __name__ == "__main__":
    rec = print_record(619028)
    print rec
    
    print "***"
    
    print get_as_text(619028)
