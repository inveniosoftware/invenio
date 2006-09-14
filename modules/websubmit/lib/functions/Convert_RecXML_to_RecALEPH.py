## $Id$

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

__revision__ = "$Id$"

from os import system, access, R_OK

def Convert_RecXML_to_RecALEPH(parameters, curdir, form):
    """Call "xmlmarc2textmarc" to convert an XML MARC record to an ALEPH MARC record, saving the ALEPH record
       in the running directory for the submission.
    """
    ## attempt to create ALEPH record:
    call_xmlmarc2textmarc_text = """%(xmlmarc2textmarc)s --aleph-marc=r %(curdir)s/recmysql > %(curdir)s/recaleph"""\
                                 % { 'xmlmarc2textmarc' : xmlmarc2textmarc, 'curdir' : curdir }
    system(call_xmlmarc2textmarc_text)
    ## test for ALEPH record:
    rec_aleph_exists = access("%(curdir)s/recaleph" % { 'curdir' : curdir }, R_OK)
    if not rec_aleph_exists:
        ## recaleph doesn't exist!
        raise functionError("Cannot create ALEPH record!")
    return ""
