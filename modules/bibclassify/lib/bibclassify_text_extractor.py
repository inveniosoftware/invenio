# -*- coding: utf-8 -*-
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

"""
BibClassify Text Extractor.
"""

__revision__ = "$Id$"

import os
import re
import sys
import tempfile
import urllib2

def executable_exists(executable):
    """Tests if an executable is available on the system."""
    for directory in os.getenv("PATH").split(":"):
        if os.path.exists(os.path.join(directory, executable)):
            return True
    return False

def is_pdf(document):
    """Checks if a document is a PDF file. Returns True if is is."""
    if not executable_exists:
        print >> sys.stderr, ("Warning: GNU file was not found on the system. "
            "Weak test.")
        if document.lower().endswith(".pdf"):
            return True
        return False
    # Tested with file version >= 4.10. First test is secure and works
    # with file version 4.25. Second condition is tested for file
    # version 4.10.
    file_output = os.popen('file ' + document).read()
    try:
        filetype = file_output.split(":")[1]
    except IndexError:
        print >> sys.stderr, ("Your version of the 'file' utility seems "
            "to be unsupported. Please report this cds.support@cern.ch.")
        sys.exit(1)

    pdf = filetype.find("PDF") > -1
    # This is how it should be done however this is incompatible with
    # file version 4.10.
    #os.popen('file -bi ' + document).read().find("application/pdf")
    return pdf

def text_lines_from_url(url, user_agent=""):
    """Returns the fulltext of the file found at the URL."""
    request = urllib2.Request(url)
    if user_agent:
        request.add_header("User-Agent", user_agent)
    try:
        distant_stream = urllib2.urlopen(request)
        # Write the URL content to a temporary file.
        local_file = tempfile.mkstemp(prefix="bibclassify.")[1]
        local_stream = open(local_file, "w")
        local_stream.write(distant_stream.read())
        local_stream.close()
        # Read lines from the temporary file.
        lines = text_lines_from_local_file(local_file)
        os.remove(local_file)
        return lines
    except:
        print >> sys.stderr, "Unable to read from URL '%s'." % url
        return None

_ONE_WORD = re.compile("[A-Za-z]{2,}")

def text_lines_from_local_file(document):
    """Returns the fulltext of the local file."""
    try:
        if is_pdf(document):
            if not executable_exists("pdftotext"):
                print >> sys.stderr, ("Error: pdftotext is not available on "
                    "the system.")
            cmd = "pdftotext -q -enc UTF-8 %s -" % document
            filestream = os.popen(cmd)
        else:
            filestream = open(document, "r")
    except:
        print >> sys.stderr, "Unable to read from file '%s'." % document
        return None

    lines = [line.decode("utf-8") for line in filestream]
    filestream.close()

    # Discard lines that do not contain at least one word.
    lines = [line for line in lines if _ONE_WORD.search(line) is not None]

    return lines
