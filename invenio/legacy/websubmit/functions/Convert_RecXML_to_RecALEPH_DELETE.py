# This file is part of Invenio.
# Copyright (C) 2008, 2009, 2010, 2011 CERN.
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

"""This is the Convert_RecXML_to_RecALEPH module. It contains the
   Convert_RecXML_to_RecALEPH WebSubmit function.
"""

__revision__ = "$Id$"

import os
from os import access, R_OK, W_OK
from invenio.config import CFG_BINDIR
from invenio.legacy.websubmit.config import InvenioWebSubmitFunctionError
from invenio.utils.text import wash_for_xml

def Convert_RecXML_to_RecALEPH_DELETE(parameters, curdir, form, user_info=None):
    """
       Function to create an ALEPH 500 MARC DELETE record from a MARC XML
       record.

       This function depends upon the following:

         * "recmysql" is a file that already exists in the working
            submission directory. I.e. "Make_Record" has already been called and
            the MARC XML record created.

         * "recmysql" must contain an ALEPH 500 SYS in the field "970__a". That
            is to say, the function "Allocate_ALEPH_SYS" should have been called
            and an ALEPH 500 SYS allocated to this record.
            *** NOTE: "xmlmarc2textmarc" is left to check for this in the record
                      It is run in --aleph-marc=d mode, which creates an ALEPH
                      "delete" record.

       Given the valid "recmysql" in the working submission directory, this
       function will use the "xmlmarc2textmarc" tool to convert that record into
       the ALEPH MARC record. The record will then be written into the file
       "recaleph500" in the current working submission directory.

       @parameters: None
       @return: (string) - Empty string.
    """
    ## If recmysql does not exist in the current working submission directory,
    ## or it is not readable, fail by raising a InvenioWebSubmitFunctionError:
    if not access("%s/recmysql" % curdir, R_OK|W_OK):
        ## FAIL - recmysql cannot be accessed:
        msg = """No recmysql in submission dir %s - """ \
              """Cannot create recaleph500!""" % curdir
        raise InvenioWebSubmitFunctionError(msg)

    ## Wash possible xml-invalid characters in recmysql
    recmysql_fd = file(os.path.join(curdir, 'recmysql'), 'r')
    recmysql = recmysql_fd.read()
    recmysql_fd.close()

    recmysql = wash_for_xml(recmysql)

    recmysql_fd = file(os.path.join(curdir, 'recmysql'), 'w')
    recmysql_fd.write(recmysql)
    recmysql_fd.close()

    ## Command to perform conversion of recmysql -> recaleph500:
    convert_cmd = \
     """%(bindir)s/xmlmarc2textmarc --aleph-marc=d %(curdir)s/recmysql > """ \
     """%(curdir)s/recaleph500""" \
     % { 'bindir' : CFG_BINDIR,
         'curdir' : curdir,
       }
    ## Perform the conversion of MARC XML record to ALEPH500 record:
    pipe_in, pipe_out, pipe_err = os.popen3("%s" % convert_cmd)
    pipe_in.close()
    pipe_out.close()
    conversion_errors = pipe_err.readlines()
    pipe_err.close()

    ## Check that the conversion was performed without error:
    if conversion_errors != []:
        ## It was not possible to successfully create the ALEPH500
        ## record, quit:
        msg = """An error was encountered when attempting to """ \
              """convert %s/recmysql into recaleph500 - stopping [%s]""" \
              % (curdir, "".join(conversion_errors))
        raise InvenioWebSubmitFunctionError(msg)

    ## Check for presence of recaleph500 in the current
    ## working submission directory:
    if not access("%s/recaleph500" % curdir, R_OK|W_OK):
        ## Either not present, or not readable - ERROR
        msg = """An error was encountered when attempting to convert """ \
              """%s/recmysql into recaleph500. After the conversion, """ \
              """recaleph500 could not be accessed.""" % curdir
        raise InvenioWebSubmitFunctionError(msg)

    ## Everything went OK:
    return ""
