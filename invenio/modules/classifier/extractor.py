# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2008, 2009, 2010, 2011, 2013, 2014, 2015 CERN.
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

"""Classifier text extraction from documents like PDF and text.

This module also provides the utility 'is_pdf' that uses GNU file in order to
determine if a local file is a PDF file.
"""

import os
import re

from flask import current_app

from .errors import IncompatiblePDF2Text

_ONE_WORD = re.compile("[A-Za-z]{2,}")


def is_pdf(document):
    """Check if a document is a PDF file and return True if is is."""
    if not executable_exists('pdftotext'):
        current_app.logger.warning(
            "GNU file was not found on the system. "
            "Switching to a weak file extension test."
        )
        if document.lower().endswith(".pdf"):
            return True
        return False

    # Tested with file version >= 4.10. First test is secure and works
    # with file version 4.25. Second condition is tested for file
    # version 4.10.
    file_output = os.popen('file ' + re.escape(document)).read()
    try:
        filetype = file_output.split(":")[-1]
    except IndexError:
        current_app.logger.error(
            "Your version of the 'file' utility seems to be unsupported."
        )
        raise IncompatiblePDF2Text('Incompatible pdftotext')

    pdf = filetype.find("PDF") > -1
    # This is how it should be done however this is incompatible with
    # file version 4.10.
    # os.popen('file -bi ' + document).read().find("application/pdf")
    return pdf


def text_lines_from_local_file(document, remote=False):
    """Return the fulltext of the local file.

    @param document: fullpath to the file that should be read
    @param remote: boolean, if True does not count lines

    @return: list of lines if st was read or an empty list
    """
    try:
        if is_pdf(document):
            if not executable_exists("pdftotext"):
                current_app.logger.error(
                    "pdftotext is not available on the system."
                )
            cmd = "pdftotext -q -enc UTF-8 %s -" % re.escape(document)
            filestream = os.popen(cmd)
        else:
            filestream = open(document, "r")
    except IOError as ex1:
        current_app.logger.error("Unable to read from file %s. (%s)"
                                 % (document, ex1.strerror))
        return []

    # FIXME - we assume it is utf-8 encoded / that is not good
    lines = [line.decode("utf-8", 'replace') for line in filestream]
    filestream.close()

    # Discard lines that do not contain at least one word.
    return [line for line in lines if _ONE_WORD.search(line) is not None]


def executable_exists(executable):
    """Test if an executable is available on the system."""
    for directory in os.getenv("PATH").split(":"):
        if os.path.exists(os.path.join(directory, executable)):
            return True
    return False
