## $Id$
##
## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002, 2003, 2004, 2005 CERN.
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

"""CDSware Submission Web Interface config file."""

## import config variables defined from config.wml:
from config import adminemail, \
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

## known compressed file extensions: 
cfg_compressed_file_extensions = ["z", "gz", "tar", "tgz", "tar", "tar.gz",
                                  "zip", "rar", "arj", "arc", "pak", "lha", "lhz",
                                  "sit", "sea", "sitx", "cpt", "hqx", "uu", "uue", 
                                  "bz", "bz2", "bzip", "tbz", "tbz2", "tar.bz", "tar.bz2"]
