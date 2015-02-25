# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011 CERN.
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

"""Return a message to the user's browser saying that their decision was taken
   into account. Intended for use in an approval submission (the referee should
   be the recipient of any message created by this function.)
"""

__revision__ = "$Id$"

import os
import cgi
from invenio.ext.logging import register_exception

def Print_Success_APP(parameters, curdir, form, user_info=None):
    """Return a message to be displayed by the referee's browser after (s)he
       has refereed an item.

       @param parameters: (dictionary) - parameters needed by this function.

        Contains:

          + decision_file: (string) - the name of the file in which the
                           referee's decision is stored.

          + newrnin: (string) - the name of the file in which the
                                new report number is stored.

       @param curdir: (string) - the current submission's working directory.

       @param form: (dictionary) - submitted form values.

       @param user_info: (dictionary) - information about the user.

       @return: (string) - a message to be displayed by the user's browser.
    """
    global rn  ## Unfortunately, it's necessary to use the magic "rn" global:
    ## Get the name of the decision file:
    try:
        decision_filename = parameters['decision_file']
    except KeyError:
        decision_filename = ""

    ## If a new report number has been generated, retrieve it:
    try:
        newrnpath = parameters['newrnin']
    except KeyError:
        register_exception()
        newrnpath = ""
    else:
        if newrnpath in (None, "None"):
            newrnpath = ""
    newrnpath = os.path.basename(newrnpath)
    newrn = ""
    if newrnpath != ""  and os.path.exists("%s/%s" % (curdir, newrnpath)):
        try:
            fp = open("%s/%s" % (curdir, newrnpath) , "r")
            newrn = fp.read()
            fp.close()
        except IOError:
            register_exception()
            newrn = ""
    else:
        newrn = ""

    ## Now try to read the decision from the decision_filename:
    if decision_filename in (None, "", "NULL"):
        ## We don't have a name for the decision file.
        ## For backward compatibility reasons, try to read the decision from
        ## a file called 'decision' in curdir:
        if os.path.exists("%s/decision" % curdir):
            try:
                fh_decision = open("%s/decision" % curdir, "r")
                decision = fh_decision.read()
                fh_decision.close()
            except IOError:
                ## Unable to open the decision file
                exception_prefix = "Error in WebSubmit function " \
                                   "Print_Success_APP. Tried to open " \
                                   "decision file [%s/decision] but was " \
                                   "unable to." % curdir
                register_exception(prefix=exception_prefix)
                decision = ""
            else:
                decision = decision.strip()
        else:
            decision = ""
    else:
        ## Try to read the decision from the decision file:
        try:
            fh_decision = open("%s/%s" % (curdir, decision_filename), "r")
            decision = fh_decision.read()
            fh_decision.close()
        except IOError:
            ## Oops, unable to open the decision file.
            decision = ""
            exception_prefix = "Error in WebSubmit function " \
                               "Print_Success_APP. Tried to open decision " \
                               "file [%s/%s] but was unable to." \
                               % (curdir, decision_filename)
            register_exception(prefix=exception_prefix)
        else:
            decision = decision.strip()

    ## Create the message:
    if decision != "":
        additional_info_approve = "The item will now be integrated into " \
                                  "the relevant collection with the " \
                                  "reference number <b>%s</b>." \
                                  % ((newrn == "" and cgi.escape(rn)) or \
                                     cgi.escape(newrn))
        msg = "<br /><div>Your decision was: <b>%(decision)s</b>.<br />\n" \
              "It has been taken into account.<br />\n" \
              "%(additional-info)s</div><br />\n" \
              % { 'decision'        : cgi.escape(decision),
                  'additional-info' : ((decision == "approve" and \
                                        additional_info_approve) \
                                       or ""),
                }
    else:
        ## Since the decision could not be read from the decision file, we will
        ## just display a generic "thank you for your decision" message.
        ## FIXME: We should really report this to WebSubmit core.
        msg = "<br /><div>Thank you for your decision.</div><br />\n"
    ## Return the message to WebSubmit core.
    return msg
