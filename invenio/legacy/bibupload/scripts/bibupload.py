# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2010, 2011, 2013 CERN.
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
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
BibUpload: Receive MARC XML file and update the appropriate database tables according to options.

    Usage: bibupload [options] input.xml
    Examples:
      $ bibupload -i input.xml

    Options:
     -a, --append            new fields are appended to the existing record
     -c, --correct           fields are replaced by the new ones in the existing record
     -f, --format            takes only the FMT fields into account. Does not update
     -i, --insert            insert the new record in the database
     -r, --replace           the existing record is entirely replaced by the new one
     -z, --reference         update references (update only 999 fields)
     -s, --stage=STAGE       stage to start from in the algorithm (0: always done; 1: FMT tags;
                             2: FFT tags; 3: BibFmt; 4: Metadata update; 5: time update)
     -n,  --notimechange     do not change record last modification date when updating

    Scheduling options:
     -u, --user=USER         user name to store task, password needed

    General options:
     -h, --help              print this help and exit
     -v, --verbose=LEVEL     verbose level (from 0 to 9, default 1)
     -V  --version           print the script version
"""


from invenio.base.factory import with_app_context


@with_app_context()
def main():
    from invenio.legacy.bibupload.engine import main as bibupload_main
    return bibupload_main()
