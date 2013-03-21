## This file is part of Invenio.
## Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""BibIndex engine stopwords facility."""

__revision__ = "$Id$"

from invenio.config import CFG_BIBINDEX_PATH_TO_STOPWORDS_FILE


def create_stopwords(filename=CFG_BIBINDEX_PATH_TO_STOPWORDS_FILE):
    """Create stopword dictionary out of FILENAME."""
    try:
        file_descriptor = open(filename, 'r')
    except IOError:
        return {}
    lines = file_descriptor.readlines()
    file_descriptor.close()
    stopdict  = {}
    for line in lines:
        stopdict[line.rstrip()] = 1
    return stopdict

stopwords = create_stopwords()

def is_stopword(word, force_check=0):
    """Return true if WORD is found among stopwords, false otherwise.
       Also, return false if BibIndex wasn't configured to use
       stopwords.  However, if FORCE_CHECK is set to 1, then do not
       pay attention to whether the admin disabled stopwords
       functionality, but look up the word anyway.  This mode is
       useful for ranking.
    """
    # note: input word is assumed to be in lowercase
    if stopwords.has_key(word):
        return True
    return False
