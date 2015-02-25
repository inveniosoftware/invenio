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

"""Make a dummy MARC XML record and store it in the submission's working-
   directory.
"""

__revision__ = "$Id$"

import os
from invenio.ext.logging import register_exception
from invenio.utils.text import wash_for_xml
from invenio.config import \
     CFG_BINDIR, \
     CFG_WEBSUBMIT_BIBCONVERTCONFIGDIR
from invenio.legacy.websubmit.config import InvenioWebSubmitFunctionError

CFG_WEBSUBMIT_DUMMY_XML_NAME = "dummy_marcxml_rec"

def Make_Dummy_MARC_XML_Record(parameters, curdir, form, user_info=None):
    """
    Make a dummy MARC XML record and store it in a submission's working-
    directory.
    This dummy record is not intended to be inserted into the Invenio
    repository. Rather, it is intended as a way for other submission-
    related functionalities to have access to the data submitted without
    necessarily having to know the names of the files in which the
    values were stored.
    An example could be the publiline service: by using a dummy record
    in the submission's directory in would be able to access an item's
    information (e.g. title, etc) without having to know the name of the
    title file, etc.
    Another use for the dummy record could be, for example, creating a
    preview of the submitted record information with bibconvert.

    @param parameters: (dictionary) - must contain:

          + dummyrec_source_tpl: (string) - the name of the bibconvert
            source template used for the creation of the dummy record.

          + dummyrec_create_tpl: (string) - the name of the bibconvert
            create template used for the creation of the dummy record.

    @param curdir: (string) - the current submission's working
                              directory.

    @param form: (dictionary) - form fields.

    @param user_info: (dictionary) - various information about the
                                     submitting user (includes the
                                     apache req object).

    @return: (string) - empty string.

    @Exceptions raised: InvenioWebSubmitFunctionError when an
                        unexpected error is encountered.
    """
    ## Get the apache request object from user_info: (we may use it for
    ## error reporting)
    try:
        req_obj = user_info['req']
    except (KeyError, TypeError):
        req_obj = None

    ## Strip whitespace from the names of the source and creation templates:
    source_tpl = parameters['dummyrec_source_tpl'].replace(" ","")
    create_tpl = parameters['dummyrec_create_tpl'].replace(" ","")

    ## Call bibconvert to create the MARC XML record:
    cmd_bibconvert_call = "%s/bibconvert -l1 -d'%s' -Cs'%s/%s' -Ct'%s/%s' " \
                          "> %s/%s 2>/dev/null" \
                          % (CFG_BINDIR, \
                             curdir, \
                             CFG_WEBSUBMIT_BIBCONVERTCONFIGDIR, \
                             source_tpl, \
                             CFG_WEBSUBMIT_BIBCONVERTCONFIGDIR, \
                             create_tpl, \
                             curdir, \
                             CFG_WEBSUBMIT_DUMMY_XML_NAME)
    errcode_bibconvert = os.system(cmd_bibconvert_call)
    if errcode_bibconvert:
        ## There was a problem creating the dummy MARC XML record. Fail.
        err_msg = "Error: Unable to create dummy MARC XML record [%s/%s]. " \
                  "Bibconvert failed with error code [%s]." \
                  % (curdir, \
                     CFG_WEBSUBMIT_DUMMY_XML_NAME, \
                     errcode_bibconvert)
        raise InvenioWebSubmitFunctionError(err_msg)

    ## Bibconvert doesn't escape stuff for XML. Read the dummy record into
    ## memory, replace any "&" or "<" with "&amp;" and "&lt;", then re-write
    ## the dummy MARC XML record to the current dir:
    try:
        fp_dummyrec = open("%s/%s" % (curdir, \
                                      CFG_WEBSUBMIT_DUMMY_XML_NAME), "r")
        record_text = fp_dummyrec.read()
        fp_dummyrec.close()
    except IOError:
        ## Couldn't read the contents of dummy_marcxml_rec.
        err_msg = "Error: Unable to create dummy MARC XML record [%s/%s]. " \
                  "Bibconvert reported no error, but the record was " \
                  "unreadable later." % (curdir, CFG_WEBSUBMIT_DUMMY_XML_NAME)
        register_exception(req=req_obj, prefix=err_msg)
        raise InvenioWebSubmitFunctionError(err_msg)

    # Escape XML-reserved chars and clean the unsupported ones (mainly
    # control characters)
    record_text = wash_for_xml(record_text)
    ## Replace the "&":
    record_text = record_text.replace("&amp;","&")
    record_text = record_text.replace("&","&amp;")
    ## Now replace the "<":
    record_text = record_text.replace("<","&lt;")
    ## Having replaced "<" everywhere in the record, put it back in known
    ## MARC XML tags:
    record_text = record_text.replace("&lt;record","<record")
    record_text = record_text.replace("&lt;/record","</record")
    record_text = record_text.replace("&lt;datafield","<datafield")
    record_text = record_text.replace("&lt;/datafield","</datafield")
    record_text = record_text.replace("&lt;controlfield","<controlfield")
    record_text = record_text.replace("&lt;/controlfield","</controlfield")
    record_text = record_text.replace("&lt;subfield","<subfield")
    record_text = record_text.replace("&lt;/subfield","</subfield")

    ## Finally, re-write the dummy MARC XML record to the current submission's
    ## working directory:
    try:
        fp_dummyrec = open("%s/%s" % (curdir, \
                                      CFG_WEBSUBMIT_DUMMY_XML_NAME), "w")
        fp_dummyrec.write(record_text)
        fp_dummyrec.flush()
        fp_dummyrec.close()
    except IOError as err:
        ## Unable to write the dummy MARC XML record to curdir.
        err_msg = "Error: Unable to create dummy MARC XML record [%s/%s]. " \
                  "After having escaped its data contents for XML, it could " \
                  "not be written back to the submission's working directory." \
                  % (curdir, CFG_WEBSUBMIT_DUMMY_XML_NAME)
        register_exception(req=req_obj, prefix=err_msg)
        raise InvenioWebSubmitFunctionError(err_msg)
    ## Return an empty string:
    return ""
