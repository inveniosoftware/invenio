 # $Id$
## Bibindex stopword class

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
    import string
    import os
    import sys
except ImportError, e:
    import sys

from bibindex_engine_config import *

stopwords = {}
def get_stopwords(file=cfg_path_stopwordlist):
    """Get stopword list"""
    try:
        file = open(file, 'r')
    except:
        return {}
    lines = file.readlines()
    file.close()
    stopdict  = {}
    for line in lines:
       stopdict[string.rstrip(line)] = 1
    return stopdict

def is_stopword(word): 
    """returns False if not stopword, True if stopword"""

    #inputword must be lowercase
    if cfg_remove_stopwords and stopwords.has_key(word):
        return True
    return False

def is_stopword_force(word): 
    """returns False if not stopword, True if stopword"""

    #inputword must be lowercase
    if stopwords.has_key(word):
        return True
    return False

stopwords = get_stopwords()
