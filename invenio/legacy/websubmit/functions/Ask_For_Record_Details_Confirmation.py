# This file is part of Invenio.
# Copyright (C) 2008, 2010, 2011 CERN.
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

"""Display the details of a record on which some operation is to be carried
   out and prompt for the user's confirmation that it is the correct record.
   Upon the clicking of the confirmation button, augment step by one.
"""

__revision__ = "$Id$"

import cgi
from invenio.config import CFG_SITE_ADMIN_EMAIL
from invenio.legacy.websubmit.config import \
     InvenioWebSubmitFunctionStop, \
     InvenioWebSubmitFunctionError
from invenio.legacy.search_engine import print_record, record_exists

# Details of record to display to the user for confirmation:
CFG_DOCUMENT_DETAILS_MESSAGE = """
<div>
We're about to process your request for the following document:<br /><br />
<table border="0">
 <tr>
  <td>Report Number(s):</td><td>%(report-numbers)s</td>
 </tr>
 <tr>
  <td>Title:</td><td>%(title)s</td>
 </tr>
 <tr>
  <td>Author(s):</td><td>%(author)s</td>
 </tr>
</table>
<br />
If this is correct, please CONFIRM it:<br />
<br />
<input type="submit" width="350" height="50"
 name="CONFIRM" value="CONFIRM"
 onClick="document.forms[0].step.value=%(newstep)s;">
<br />
If you think that there is a problem, please contact
 <a href="mailto:%(admin-email)s">%(admin-email)s</a>.<br />
</div>
"""

def Ask_For_Record_Details_Confirmation(parameters, \
                                        curdir, \
                                        form, \
                                        user_info=None):
    """
       Display the details of a record on which some operation is to be carried
       out and prompt for the user's confirmation that it is the correct record.
       Upon the clicking of the confirmation button, augment step by one.

       Given the "recid" (001) of a record, retrieve the basic metadata
       (title, report-number(s) and author(s)) and display them in the
       user's browser along with a prompt asking them to confirm that
       it is indeed the record that they expected to see.

       The function depends upon the presence of the "sysno" global and the
       presence of the "step" field in the "form" parameter.
       When the user clicks on the "confirm" button, step will be augmented by
       1 and the form will be submitted.
       @parameters: None.
       @return: None.
       @Exceptions raise: InvenioWebSubmitFunctionError if problems are
        encountered;
        InvenioWebSubmitFunctionStop in order to display the details of the
        record and the confirmation message.
    """
    global sysno

    ## Make sure that we know the current step:
    try:
        current_step = int(form['step'])
    except TypeError:
        ## Can't determine step.
        msg = "Unable to determine submission step. Cannot continue."
        raise InvenioWebSubmitFunctionError(msg)
    else:
        newstep = current_step + 1

    ## Make sure that the sysno is valid:
    try:
        working_recid = int(sysno)
    except TypeError:
        ## Unable to find the details of this record - cannot query the database
        msg = "Unable to retrieve details of record - record id was invalid."
        raise InvenioWebSubmitFunctionError(msg)

    if not record_exists(working_recid):
        ## Record doesn't exist.
        msg = "Unable to retrieve details of record [%s] - record does not " \
              "exist." % working_recid
        raise InvenioWebSubmitFunctionError(msg)

    ## Retrieve the details to be displayed:
    ##
    ## Author(s):
    rec_authors = ""
    rec_first_author    = print_record(int(sysno), 'tm', "100__a")
    rec_other_authors   = print_record(int(sysno), 'tm', "700__a")
    if rec_first_author != "":
        rec_authors += "".join(["%s<br />\n" % cgi.escape(author.strip()) for \
                                author in rec_first_author.split("\n")])
    if rec_other_authors != "":
        rec_authors += "".join(["%s<br />\n" % cgi.escape(author.strip()) for \
                                author in rec_other_authors.split("\n")])

    ## Title:
    rec_title = "".join(["%s<br />\n" % cgi.escape(title.strip()) for title in \
                          print_record(int(sysno), 'tm', "245__a").split("\n")])

    ## Report numbers:
    rec_reportnums = ""
    rec_reportnum        = print_record(int(sysno), 'tm', "037__a")
    rec_other_reportnums = print_record(int(sysno), 'tm', "088__a")
    if rec_reportnum != "":
        rec_reportnums += "".join(["%s<br />\n" % cgi.escape(repnum.strip()) \
                                   for repnum in rec_reportnum.split("\n")])
    if rec_other_reportnums != "":
        rec_reportnums += "".join(["%s<br />\n" % cgi.escape(repnum.strip()) \
                                   for repnum in \
                                   rec_other_reportnums.split("\n")])

    raise InvenioWebSubmitFunctionStop(CFG_DOCUMENT_DETAILS_MESSAGE % \
                                  { 'report-numbers' : rec_reportnums, \
                                    'title'          : rec_title, \
                                    'author'         : rec_authors, \
                                    'newstep'        : newstep, \
                                    'admin-email'    : CFG_SITE_ADMIN_EMAIL, \
                                  }   )
