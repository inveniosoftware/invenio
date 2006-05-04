# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
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

## configuration parameters read from the general config file:
from invenio.config import cfg_bibindex_fulltext_index_local_files_only, \
     cfg_bibindex_stemmer_default_language, \
     cfg_bibindex_remove_stopwords, \
     cfg_bibindex_path_to_stopwords_file, \
     cfg_bibindex_chars_alphanumeric_separators, \
     cfg_bibindex_chars_punctuation, \
     cfg_bibindex_remove_html_markup, \
     cfg_bibindex_min_word_length, \
     cfg_bibindex_urlopener_username, \
     cfg_bibindex_urlopener_password, \
     version, \
     pdftotext, \
     pstotext, \
     pstoascii, \
     antiword, \
     catdoc, \
     wvtext, \
     ppthtml, \
     xlhtml, \
     htmltotext, \
     gzip

## version number:
bibindex_engine_version = "CDS Invenio/%s bibindex/%s" % (version, version)

## programs used to convert fulltext files to text:
conv_programs = {#"ps": [pstotext,pstoascii],  # switched off at the moment, since PDF is faster
                 #"ps.gz": [pstotext,pstoascii],
                 "pdf": [pdftotext,pstotext,pstoascii],
                 "doc": [antiword,catdoc,wvtext],
                 "ppt": [ppthtml],
                 "xls": [xlhtml]}
## helper programs used if the above programs convert only to html or other intermediate file formats:
conv_programs_helpers =  {"html": htmltotext,
                          "gz": gzip}

## safety parameters concerning MySQL thread-multiplication problem:
cfg_check_mysql_threads = 0 # to check or not to check the problem? 
cfg_max_mysql_threads = 50 # how many threads (connections) we consider as still safe
cfg_mysql_thread_timeout = 20 # we'll kill threads that were sleeping for more than X seconds
