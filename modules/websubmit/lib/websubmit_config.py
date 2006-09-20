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

"""CDS Invenio Submission Web Interface config file."""

__revision__ = "$Id$"

# FIXME: wildcard import is bad, but it seems needed for WebSubmit the
# time being, because the MESS functions seem to have a rather funny
# usage of config variables without importing anything, but via
# execing and stuff!  WebSubmit should really get refactored one day.
from invenio.config import *

## test:
test = "FALSE"

## CC all action confirmation mails to administrator? (0 == NO; 1 == YES)
CFG_WEBSUBMIT_COPY_MAILS_TO_ADMIN = 0

## known compressed file extensions: 
CFG_COMPRESSED_FILE_EXTENSIONS = ["z", "gz", "tar", "tgz", "tar",
                                  "tar.gz", "zip", "rar", "arj",
                                  "arc", "pak", "lha", "lhz", "sit",
                                  "sea", "sitx", "cpt", "hqx", "uu",
                                  "uue", "bz", "bz2", "bzip", "tbz",
                                  "tbz2", "tar.bz", "tar.bz2"]
                                
CFG_KNOWN_FILE_EXTENSIONS = ["lis",
			     "sxi",
   		 	     "zip",
			     "kpr",
                             "xls",
                             "mov",
			     "avi",
			     "ppt",
			     "prn",
			     "pdf",
			     "tif",
			     "doc",
			     "dot",
			     "ps.gz",
			     "ps.Z",
			     "ps",
			     "eps",
			     "pps",
			     "gif",
			     "jpeg",
			     "jpg",
			     "JPG",
			     "html",
			     "htm",
			     "Download.link",
			     "link",
			     "tex",
			     "txt",
			     "ef.tif",
			     "e.tif",
			     "f.tif",
			     "ef.pdf",
			     "e.pdf",
			     "f.pdf",
			     "ef.ps.gz",
			     "e.ps.gz",
			     "f.ps.gz",
			     "ef.ps",
			     "e.ps",
			     "f.ps",
			     "e.xls",
			     "f.xls",
			     "ef.doc",
			     "e.doc",
			     "f.doc",
			     "ef.html",
			     "e.html",
			     "f.html",
			     "hpg",
			     "mpp",
			     "h",
			     "rtf",
			     "tar",
			     "tar.gz",
			     "tgz",
			     "msg",
			     "llb",
			     "ogg",
			     "mp3",
			     "wav",
			     "mpg"]
