# -*- coding: utf-8 -*-
##
## $Id$
##
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

"""
BibExport plugin implementing 'googlescholar' exporting method.

The main function is run_export_method(jobname) defined at the end.
This is what BibExport daemon calls for all the export jobs that use
this exporting method.

The Google Scholar exporting method answers this use case: every first
of the month, please export all records modified during the last month
and matching these search criteria in an NLM format in such a way that
the output is split into files containing not more than 1000 records
and compressed via gzip and placed in this place from where Google
Scholar would fetch them. The output files would be organized like
this:

* all exportable records:

    /export/google-scholar/all-index.nlm.html   - links to parts below
    /export/google-scholar/all-part1.nlm.xml.gz - first batch of 1000 records
    /export/google-scholar/all-part2.nlm.xml.gz - second batch of 1000 records
    ...
    /export/google-scholar/all-partM.nlm.xml.gz - last batch of 1000 records

* records modified in the last month:

    /export/google-scholar/lastmonth-index.nlm.html   - links to parts below
    /export/google-scholar/lastmonth-part1.nlm.xml.gz - first batch of 1000 records
    /export/google-scholar/lastmonth-part2.nlm.xml.gz - second batch of 1000 records
    ...
    /export/google-scholar/lastmonth-partN.nlm.xml.gz - last batch of 1000 records
"""

def run_export_method(jobname):
    """Main function, reading params and running the task."""
    raise NotImplementedError
