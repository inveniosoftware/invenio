 # $Id$
## Bibindex stemmer class

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

## read config variables:
#include "config.wml"
#include "configbis.wml"
#include "cdswmllib.wml"

try:
    import sre
    import Stemmer
    stem_avail = True
except ImportError, e:
    stem_avail = False
    pass

from bibindex_engine_config import *

def getStemmer():
    languages = {'fr': 'french', 'en': 'english', 'no':'norwegian', 'se':'swedish', 'de': 'german', 'it':'italian', 'pt':'portuguese'}
    stemmer = {}
    if stem_avail:
        for (key, value) in languages.iteritems():
            stemmer[key] = Stemmer.Stemmer(value)
        return stemmer
    else:
        return {}

def stem(word):
    if cfg_use_stemmer_lang:
        return stemmer[cfg_use_stemmer_lang].stem(word)
    return word

def stem_by_lang(word, lang):
    return stemmer[lang].stem(word)

def lang_available(lang):
    return stemmer.has_key(lang)

"Creates the stemmers."
stemmer = getStemmer()
