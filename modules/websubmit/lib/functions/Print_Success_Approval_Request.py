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

"""This is Print_Success_Approval_Request.  It creates a "success
   message" that is shown to the user to indicate that their approval
   request has successfully been registered.
"""

__revision__ = "$Id$"

def Print_Success_Approval_Request(parameters, curdir, form, user_info=None):
    """
    This function creates a "success message" that is to be shown to the
    user to indicate that their approval request has successfully been
    registered.

    @parameters: None.
    @return: (string) - the "success" message for the user.
    """
    text = """<br />
<div>
 The approval request for your document has successfully been
 registered and the referee has been informed.<br />
 You will be notified by email when a decision has been made.
</div>
<br />"""
    return text
