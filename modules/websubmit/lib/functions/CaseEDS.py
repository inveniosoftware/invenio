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

"""This is the CaseEDS module. Contains the CaseEDS WebSubmit function.
"""

__revision__ = "$Id$"

import os

from invenio.websubmit_config import \
     InvenioWebSubmitFunctionStop, \
     InvenioWebSubmitFunctionError

def CaseEDS(parameters, curdir, form):
    """This function compares the content of a file to different values and
       directly goes to a different step in the action according to the value.
       @param parameters: (dictionary) of parameters (relating to the given
        doctype/action) that are to be passed to the function:
           + casevariable: name of the file containing the value
           + casevalues:   comma-separated list of values
           + casesteps:    comma-separated list of steps
           + casedefault:  default step if no value is mapped
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
        if cases.has_key(value):
            nextstep = cases[value]
        else:
            nextstep = casedefault
    if nextstep != "":
        t = "<b>Please wait...</b>"
        t = """    
<SCRIPT LANGUAGE="JavaScript1.1">
    document.forms[0].action="/submit";
    document.forms[0].step.value=%s;
    document.forms[0].submit();
</SCRIPT>""" % nextstep
        raise InvenioWebSubmitFunctionStop(t)
    else:
        raise InvenioWebSubmitFunctionError("Case function: Could not " \
                                            "determine next action step")
    return ""

