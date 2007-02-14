# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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
BibIndex indexing engine configuration parameters.  
"""

__revision__ = \
    "$Id$"

## configuration parameters read from the general config file:
from invenio.config import \
     version, \
     CFG_PATH_PDFTOTEXT, \
     CFG_PATH_PSTOTEXT, \
     CFG_PATH_PSTOASCII, \
     CFG_PATH_ANTIWORD, \
     CFG_PATH_CATDOC, \
     CFG_PATH_WVTEXT, \
     CFG_PATH_PPTHTML, \
     CFG_PATH_XLHTML, \
     CFG_PATH_HTMLTOTEXT, \
     CFG_PATH_GZIP

## version number:
BIBINDEX_ENGINE_VERSION = "CDS Invenio/%s bibindex/%s" % (version, version)

## programs used to convert fulltext files to text:
CONV_PROGRAMS = { ### PS switched off at the moment, since PDF is faster
    #"ps": [CFG_PATH_PSTOTEXT, CFG_PATH_PSTOASCII],  
    #"ps.gz": [CFG_PATH_PSTOTEXT, CFG_PATH_PSTOASCII],               
    "pdf": [CFG_PATH_PDFTOTEXT, CFG_PATH_PSTOTEXT, CFG_PATH_PSTOASCII],
    "doc": [CFG_PATH_ANTIWORD, CFG_PATH_CATDOC, CFG_PATH_WVTEXT],
    "ppt": [CFG_PATH_PPTHTML],
    "xls": [CFG_PATH_XLHTML]}

## helper programs used if the above programs convert only to html or
## other intermediate file formats:
CONV_PROGRAMS_HELPERS =  {"html": CFG_PATH_HTMLTOTEXT,
                          "gz": CFG_PATH_GZIP}

## safety parameters concerning DB thread-multiplication problem:
CFG_CHECK_MYSQL_THREADS = 0 # to check or not to check the problem? 
CFG_MAX_MYSQL_THREADS = 50 # how many threads (connections) we
                           # consider as still safe
CFG_MYSQL_THREAD_TIMEOUT = 20 # we'll kill threads that were sleeping
                              # for more than X seconds
