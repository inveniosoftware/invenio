## $Id$
## BibIndex stopwords facility.

## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002 CERN.
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

import string

from bibindex_engine_config import *

def create_stopwords(filename=cfg_bibindex_path_to_stopwords_file):
    """Create stopword dictionary out of FILENAME."""
    try:
        filename = open(filename, 'r')
    except:
        return {}
    lines = filename.readlines()
    filename.close()
    stopdict  = {}
    for line in lines:
       stopdict[string.rstrip(line)] = 1
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
    if (cfg_bibindex_remove_stopwords or force_check) and stopwords.has_key(word):
        return True
    return False
