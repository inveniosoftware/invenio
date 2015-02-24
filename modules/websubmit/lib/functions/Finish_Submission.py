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

__revision__ = "$Id$"

   ##
   ## Name:          Finish_Submission
   ## Description:   function Finish_Submission
   ##                This function sets some global variables so that even if
   ##                we are not in the last step of an action, the action stops
   ##                anyway.
   ## Author:         T.Baron
   ## PARAMETERS:    -
   ## OUTPUT: HTML
   ##

def Finish_Submission(parameters, curdir, form, user_info=None):
    """
    This function stops the data treatment process even if further
    steps exist. This is used for example in the approval action. In
    the first step, the program determines whether the user approved
    or rejected the document (see CaseEDS function description). Then
    depending on the result, it executes step 2 or step 3. If it
    executes step 2, then it should continue with step 3 if nothing
    stopped it. The Finish_Submission function plays this role.
    """
    global last_step,action_score
    last_step = 1
    action_score = -1
    return ""

