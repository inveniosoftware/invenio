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

## import config variables defined from config.wml:
from invenio.config import adminemail, \
     supportemail, \
     images, \
     urlpath, \
     accessurl, \
     counters, \
     storage, \
     filedir, \
     filedirsize, \
     gfile, \
     gzip, \
     tar, \
     gunzip, \
     acroread, \
     distiller, \
     convert, \
     tmpdir, \
     bibupload, \
     bibformat, \
     bibwords, \
     bibconvert, \
     bibconvertconf, \
     htdocsurl

## test:
test = "FALSE"

## CC all action confirmation mails to administrator? (0 == NO; 1 == YES)
cfg_websubmit_copy_mails_to_admin = 0

## known compressed file extensions: 
cfg_compressed_file_extensions = ["z", "gz", "tar", "tgz", "tar", "tar.gz",
                                  "zip", "rar", "arj", "arc", "pak", "lha", "lhz",
                                  "sit", "sea", "sitx", "cpt", "hqx", "uu", "uue", 
                                  "bz", "bz2", "bzip", "tbz", "tbz2", "tar.bz", "tar.bz2"]
                                
cfg_known_file_extensions = ["lis",
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
