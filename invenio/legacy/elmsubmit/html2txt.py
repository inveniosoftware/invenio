# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011 CERN.
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

__revision__ = "$Id$"

import StringIO
import formatter
import htmllib
import sgmllib
import os

from invenio.legacy.elmsubmit.misc import write_to_and_return_tempfile_name as _write_to_and_return_tempfile_name
from invenio.legacy.elmsubmit.misc import remove_tempfile as _remove_tempfile
from invenio.legacy.elmsubmit.misc import mapmany as _mapmany

# Search down to ###!!! See here !!!### for editable stuff.

# Parser classes:

class UnicodeHTMLParser(htmllib.HTMLParser):

    def unknown_charref(self, ref):
        # Take the HTML character reference and convert it to unicode.
        try:
            self.handle_data(unichr(int(ref)))
        except(OverflowError, ValueError):
            raise HTMLParsingFailed

    # htmlentitydefs.py should be found in the dir with this file:
    from .htmlentitydefs import entitydefs

class NativeParser:

    # NativeParser doesn't really need to be wrapped in a class, but
    # we need to provide the same parser_instance.parse() interface as
    # used for command line parsers.

    def parse(self, html, cols):

        file = StringIO.StringIO(u'')

        # Create HTML parser:
        writer = formatter.DumbWriter(file, maxcol=cols)
        myformatter = formatter.AbstractFormatter(writer)
        p = UnicodeHTMLParser(myformatter)

        try:
            p.feed(html)
        except sgmllib.SGMLParseError:
            raise HTMLParsingFailed

        p.close()

        return file.getvalue()

class CLParser:

    # Provide a generic interface to command line parsers.

    # We could have saved some work by avoiding writing html to a temp
    # file for those command line parsers which allow input of html
    # documents on stdin. However, not all of them do and a uniform
    # interface was simplest.

    def __init__(self, commandline_list):

        self.commandline_list = commandline_list

    def parse(self, html, cols):

        if not isinstance(html, unicode): raise UnicodeInputRequired

        utf8html = html.encode('utf8')
        tf_name = _write_to_and_return_tempfile_name(utf8html)

        # Replace cols marker:
        f = lambda x: ((x == ['cols']) and str(cols)) or x
        # Replace filename marker:
        g = lambda x: ((x == ['filename']) and tf_name) or x

        commandline_list = _mapmany([f,g], self.commandline_list)
        commandline = ''.join(commandline_list)

        # Run the process using popen3; possibly dodgy on Windows!
        # Need popen3 rather other popen function because we want to
        # grab stderr and hide it from the clients console.

        (stdin, stdout, stderr) = os.popen3(commandline, 'r')

        utf8output = stdout.read()
        exit_status = stdout.close()
        _remove_tempfile(tf_name)

        # Just in case the parser outputs bogus utf8:

        # Check the return code:
        if exit_status is not None: raise HTMLParsingFailed

        # Convert back to unicode object and return:
        try:
            output = unicode(utf8output, 'utf8')
            return output
        except (LookupError, UnicodeError):
            raise HTMLParsingFailed


###!!! See here !!!###

# Parsers:

parser_native = NativeParser()

# These can be reinstated some time down the line when command line
# parsers have worked out their charset support a little better
# (rather than the current 'if you get lynx with this patch available
# from some guys website, then recompile...'):

# It appears w3m requires patches to support utf8:
# parser_w3m = CLParser(["w3m -dump -cols ", ['cols'], " -T 'text/html' file://", ['filename']])

# It appear lynx doesn't support charsets:
# parser_lynx = CLParser(['lynx -dump -force-html -width=', ['cols'], ' file://', ['filename']])

# elinks works OK, except it appear not to support &#{unicoderef} tags, but these are rare(ish):
# Actually, trying
# parser_elinks = CLParser([ 'elinks -dump -dump-charset "utf-8" -force-html -dump-width ', ['cols'], ' file://', ['filename']])

# The version (2.1pre13) on my system of the other 'famous' command
# line browser name links doesn't seem to have a dump option!


available_parsers = [ # parser_w3m,
                      # parser_lynx,
                      # parser_elinks,
                      parser_native ]

# Key function:

def html2txt(html, use_parsers=available_parsers, cols=72):

    # Try each parser in turn (given in the list use_parsers) to see
    # if they work:

    for parser in use_parsers:
        try:
            text = parser.parse(html, cols)
        except HTMLParsingFailed:
            continue
        else:
            return text

    # None of the parsers worked.
    raise HTMLParsingFailed

# Errors:

class HTMLParsingFailed(Exception):
    """
    Raised if HTML parsing fails for any reason.
    """
    pass

class UnicodeInputRequired(Exception):
    """
    Raised if attempt is made to parse anything other than unicode.
    """


