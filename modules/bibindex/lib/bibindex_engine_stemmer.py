## $Id$

## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
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

from cdsware.bibindex_engine_config import *

def create_stemmers():
    """Create stemmers dictionary for all possible languages."""
    languages = {'fr': 'french', 'en': 'english', 'no':'norwegian', 'sv':'swedish', 'de': 'german', 'it':'italian', 'pt':'portuguese'}
    stemmers = {}
    try:
        import Stemmer
        for (key, value) in languages.iteritems():
            stemmers[key] = Stemmer.Stemmer(value)

    except ImportError:
        pass # PyStemmer isn't available
    return stemmers

stemmers = create_stemmers()

def is_stemmer_available_for_language(lang):
    """Return true if stemmer for language LANG is available.
       Return false otherwise.
    """
    return stemmers.has_key(lang)
    
def stem(word, lang=cfg_bibindex_stemmer_default_language):
    """Return WORD stemmed according to language LANG (e.g. 'en')."""
    if lang and is_stemmer_available_for_language(lang):
        return stemmers[lang].stem(word)
    else:
        return word

