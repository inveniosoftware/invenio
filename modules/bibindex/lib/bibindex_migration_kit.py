## $Id$

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
This script will update idxPHRASE dynamically created by the user.
"""

from invenio.dbquery import run_sql

def migrate():
    """Core."""
    index_ids = [x[0] for x in run_sql('select id from idxINDEX')]
    for index_id in index_ids:
        print "Updating index %i" % index_id
        run_sql('ALTER TABLE `idxPHRASE%02dF` CHANGE `term` `term` TEXT NULL DEFAULT NULL, DROP INDEX `term`, ADD UNIQUE `term` (`term` (50))' % index_id)
    print "Done!"

if __name__ == "__main__":
    migrate()