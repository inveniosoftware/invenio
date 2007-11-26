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

__revision__ = "$Id$"

"""This script updates the filesystem structure of fulltext files in order
to make it coherent with docfile implementation (docfile.py structure is backward
compatible with file.py structure, but the viceversa is not true).
"""

from invenio.dbquery import run_sql
from invenio.docfile import BibRecDocs, InvenioWebSubmitFileError

def retrieve_fulltext_recids():
    """Returns the list of all the recid number linked with at least a fulltext
    file."""
    res = run_sql('SELECT DISTINCT id_bibrec FROM bibrec_bibdoc')
    return [recid[0] for recid in res]

def fix_recid(recid):
    """Fix a given recid."""
    print "Fixing record %s ->" % recid,
    bibrec = BibRecDocs(recid)
    docnames = bibrec.get_bibdoc_names()
    try:
        for docname in docnames:
            print docname,
            new_bibdocs = bibrec.fix(docname)
            new_bibdocnames = [bibdoc.get_docname() for bibdoc in new_bibdocs]
            if new_bibdocnames:
                print "(created bibdocs: '%s')" % new_bibdocnames.join("', '"),
    except InvenioWebSubmitFileError, e:
        print "%s -> ERROR", e
    else:
        print "-> OK"

def main():
    """Core loop."""
    recids = retrieve_fulltext_recids()
    print "%s records to migrate" % len(recids)
    print "-" * 40
    for recid in recids:
        fix_recid(recid)
    print "-" * 40
    print "DONE"

if __name__ == '__main__':
    main()
