# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2005, 2006, 2007, 2008, 2010, 2011, 2013 CERN.
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

from __future__ import print_function

"""
   "refextract" is used to extract and process the "references"
   or "citations" made to other documents from within a document.
   A document's "references" section is usually found at the end of
   the document, and generally consists of a list of the works
   cited during the course of the document.
   "refextract" can attempt to identify a document's references
   section and extract it from the document.  It can also attempt
   to standardise the references (correct the names of journals
   etc so that they are written in a standard format), and mark them
   up so that they can be linked to the full articles on the Web by
   means of hyper-links.

   "refextract" has 4 phases of processing (passes):
    1. Convert PDF file to plaintext (UTF-8).
    2. Extract References from plaintext.
    3. Recognise and standardise citations in the extracted
       reference lines. (Periodical titles and institutional
       report numbers are standardised with the aid of
       dedicated knowledge-bases.)
    4. Markup standardised citations in MARC XML and output
       them.

    It requires providing as argument a physical fulltext file using
    [-f, --fulltext].
"""
from invenio.base.factory import with_app_context


@with_app_context()
def main():
    from invenio.legacy.refextract.cli import main as cli_main
    from invenio.legacy.refextract.cli import get_cli_options
    from invenio.legacy.refextract.cli import begin_extraction
    try:
        (options, args) = get_cli_options()
        cli_main(options, args, begin_extraction)
    except KeyboardInterrupt:
        # Exit cleanly
        print('Interrupted')
