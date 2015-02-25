# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2015 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA

"""BibConvert command line tool.

Usage: [options] < input.dat
Examples:
       bibconvert -ctemplate.cfg < input.dat
       bibconvert -ctemplate.xsl < input.xml

 XSL options:
 -c,  --config             transformation stylesheet file

 Plain text-oriented options:
 -c,  --config             configuration template file
 -d,  --directory          source_data fields are located in separated files in 'directory'
 -h,  --help               print this help
 -V,  --version            print version number
 -l,  --length             minimum line length (default = 1)
 -o,  --oai                OAI identifier starts with specified value (default = 1)
 -b,  --header             insert file header
 -e,  --footer             insert file footer
 -B,  --record-header      insert record header
 -E,  --record-footer      insert record footer
 -s,  --separator          record separator, default empty line (EOLEOL)
 -t,  --output_separator

 -m0,  		           match records using query string, output *unmatched*
 -m1,                      match records using query string, output *matched*
 -m2,                      match records using query string, output *ambiguous*

 -Cx,                      alternative to -c when config split to several files, *extraction*
 -Cs,                      alternative to -c when config split to several files, *source*
 -Ct,                      alternative to -c when config split to several files, *target*

 BibConvert can convert:
  - XML data using XSL templates.
  - Plain text data using cfg templates files.

 Plain text-oriented options are not available with .xsl configuration files
"""
from invenio.base.factory import with_app_context


@with_app_context()
def main():
    """Execute bibconvert cli."""
    from invenio.legacy.bibconvert.cli import main as bibconvert_main
    return bibconvert_main()
