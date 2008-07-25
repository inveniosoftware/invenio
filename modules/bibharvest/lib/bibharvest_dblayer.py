## $Id$

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
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

logfile = "/opt/cds-invenio/var/cache/oaiarxiv_oaiid.dat"

class HistoryEntry:
    date = ""
    arXivId = ""
    operation = "i"
    def __init__(self, date, arXivId, operation):
        self.date = date
        self.arXivId = arXivId
        self.operation = operation


def get_history_entries(oai_src_id):
    """
    Getting the harvesting history from any database
    """
    result = []
    f = open(logfile, "r")
    lines = f.readlines()
    f.close()
    for line in lines:
#        result.append(HistoryEntry("a","a","u"))
        parts = line.split()
        if (len(parts) >= 3) and ( parts[2] == oai_src_id):
            result.append(HistoryEntry(parts[1][0:4] + "-" + parts[1][4:6] + "-" + parts[1][6:8] + " " + parts[1][8:10] + ":" + parts[1][10:12] + ":" + parts[1][12:], parts[0], "i"))
    return result
