# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

"""This is the CaseEDS module. Contains the CaseEDS WebSubmit function.
"""

__revision__ = "$Id$"

import os

from invenio.legacy.websubmit.config import \
     InvenioWebSubmitFunctionStop, \
     InvenioWebSubmitFunctionError

def CaseEDS(parameters, curdir, form, user_info=None):
    """
       This function compares the content of a file to different values and
       directly goes to a different step in the action according to the value.

       This function may be used if the treatment to be done after a
       submission depends on a field entered by the user. Typically
       this is used in an approval interface. If the referee approves
       then we do this. If he rejects, then we do other thing.  More
       specifically, the function gets the value from the file named
       [casevariable] and compares it with the values stored in
       [casevalues]. If a value matches, the function directly goes to
       the corresponding step stored in [casesteps]. If no value is
       matched, it goes to step [casedefault].

       @param parameters: (dictionary) of parameters (relating to the given
        doctype/action) that are to be passed to the function:

           + casevariable: This parameters contains the name of the
                           file in which the function will get the
                           chosen value.
                           Eg:"decision"

           + casevalues: Contains the list of recognized values to
                         match with the chosen value. Should be a
                         comma separated list of words.
                         Eg:"approve,reject"

           + casesteps: Contains the list of steps corresponding to
                        the values matched in [casevalue]. It should
                        be a comma separated list of numbers.
                        Eg:"2,3"

                        In this example, if the value stored in the
                        file named"decision" is "approved", then the
                        function launches step 2 of this action. If it
                        is "reject", then step 3 is launched.

           + casedefault: Contains the step number to go by default if
                          no match is found.
                          Eg:"4"

                          In this example, if the value stored in the
                          file named "decision" is not "approved" nor
                          "reject", then step 4 is launched.

       @return: (string) - empty string
    """
    ## Get the values of the parameters passed to this function via the
    ## parameters array:
    casevariable = parameters['casevariable']
    casevalue = parameters['casevalues']
    casestep = parameters['casesteps']
    casedefault = parameters['casedefault']

    casevalues = casevalue.split(",")
    casesteps = casestep.split(",")
    cases = {}
    for a, b in map(None, casevalues, casesteps):
        cases[a] = b
    nextstep = ""
    if not os.path.exists("%s/%s" % (curdir, casevariable)):
        nextstep = casedefault
    else:
        fp = open("%s/%s" % (curdir, casevariable), "r")
        value = fp.read()
        fp.close()
        if value in cases:
            nextstep = cases[value]
        else:
            nextstep = casedefault
    if nextstep != "":
        t = "<b>Please wait...</b>"
        t = """
<SCRIPT LANGUAGE="JavaScript1.1">
    document.forms[0].action="/submit";
    document.forms[0].step.value=%s;
    user_must_confirm_before_leaving_page = false;
    document.forms[0].submit();
</SCRIPT>""" % nextstep
        raise InvenioWebSubmitFunctionStop(t)
    else:
        raise InvenioWebSubmitFunctionError("Case function: Could not " \
                                            "determine next action step")
    return ""

