# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2013 CERN.
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


"""Usage: bibclassify [OPTION]... [FILE/URL]...
  or:  bibclassify [OPTION]... [DIRECTORY]...
Searches keywords in FILEs and/or files in DIRECTORY(ies). If a directory is
specified, BibClassify will generate keywords for all PDF documents contained
in the directory.

  -h, --help                display this help and exit
  -V, --version             output version information and exit
  -v, --verbose LEVEL       sets the verbose to LEVEL (=0)
  -k, --ontology FILE       sets the FILE to read the ontology from
  -o, --output-mode TYPE    changes the output format to TYPE (text, marcxml or
                              html) (=text)
  -s, --spires              outputs keywords in the SPIRES format
  -n, --keywords-number INT sets the number of keywords displayed (=20), use 0
                              to set no limit
  -m, --matching-mode TYPE  changes the search mode to TYPE (full or partial)
                              (=full)
  --detect-author-keywords  detect keywords that are explicitely written in the
                              document
  --check-ontology          checks the ontology and reports warnings and errors
  --rebuild-cache           ignores the existing cache and regenerates it
  --no-cache                don't cache the ontology

Backward compatibility (using these options is discouraged):
  -q                        equivalent to -s
  -f FILE URL               sets the file to read the keywords from

Example:
    python bibclassifycli.py -k etc/HEP.rdf http://arxiv.org/pdf/0808.1825
    python bibclassifycli.py -k etc/HEP.rdf article.pdf
    python bibclassifycli.py -k etc/HEP.rdf directory/"""

from invenio.base.factory import with_app_context


@with_app_context()
def main():
    from invenio.legacy.bibclassify.cli import main as classify_main
    return classify_main()
