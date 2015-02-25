# This file is part of Invenio.
# Copyright (C) 2011 CERN.
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

"""WebSubmit function - Video processing.

"""

from invenio.modules.encoder.utils import probe
from invenio.legacy.websubmit.config import InvenioWebSubmitFunctionStop
import os

__revision__ = "$Id$"

def DEMOVID_Validation(parameters, curdir, form, user_info=None):
    """
    """
    messages = []
    malformed = False

    file_storing_path = os.path.join(curdir, "files", str(user_info['uid']), "NewFile", 'filepath')
    file_storing_name = os.path.join(curdir, "files", str(user_info['uid']), "NewFile", 'filename')
    file_storing_aspect = os.path.join(curdir, "DEMOVID_ASPECT")
    file_storing_title = os.path.join(curdir, "DEMOVID_TITLE")
    file_storing_description = os.path.join(curdir, "DEMOVID_DESCR")
    file_storing_author = os.path.join(curdir, "DEMOVID_AU")
    file_storing_year = os.path.join(curdir, "DEMOVID_YEAR")

    ## Validate the uploaded video
    try:
        fp = open(file_storing_path)
        fullpath = fp.read()
        fp.close()
        fp = open(file_storing_name)
        filename = fp.read()
        fp.close()
        if not probe(fullpath) or os.path.splitext(filename)[1] in ['jpg', 'jpeg', 'gif', 'tiff', 'bmp', 'png', 'tga']:
            malformed = True
            messages.append("The uploaded file is not a supported video format.")
    except:
        malformed = True
        messages.append("Please upload a video.")

    ## Validate the title
    try:
        fp = open(file_storing_title)
        title = fp.read()
        fp.close()
        if len(title) < 2 or len(title) > 50:
            malformed = True
            messages.append("The title is too short, please enter at least 2 characters.")
    except:
        malformed = True
        messages.append("Please enter a title.")


    ## Validate the description
    try:
        fp = open(file_storing_description)
        description = fp.read()
        fp.close()
        if len(description) < 10:
            malformed = True
            messages.append("The description must be at least 10 characters long.")
    except:
        malformed = True
        messages.append("Please enter a description.")

    ## Validate author
    try:
        fp = open(file_storing_author)
        author = fp.read()
        fp.close()
    except:
        malformed = True
        messages.append("Please enter at least one author.")

    ## Validate year
    try:
        fp = open(file_storing_year)
        year = fp.read()
        fp.close()
    except:
        malformed = True
        messages.append("Please enter a year.")
    try:
        if int(year) < 1000 or int(year) > 9999:
            malformed = True
            messages.append("Please enter a valid year. It must consist of 4 digits.")
    except:
        malformed = True
        messages.append("Please enter a valid year. It must consist of 4 digits.")

    ## Validate the aspect ratio
    try:
        fp = open(file_storing_aspect)
        aspect = fp.read()
        fp.close()
        try:
            aspectx, aspecty = aspect.split(':')
            aspectx = int(aspectx)
            aspecty = int(aspecty)
        except:
            malformed = True
            messages.append("Aspect ratio was not provided as 'Number:Number' format")
    except:
        malformed = True
        messages.append("Please enter an aspect ratio.")

    if malformed:
        raise InvenioWebSubmitFunctionStop("""
        <SCRIPT>
           document.forms[0].action="/submit";
           document.forms[0].curpage.value = 1;
           document.forms[0].step.value = 0;
           user_must_confirm_before_leaving_page = false;
           alert('%s');
           document.forms[0].submit();
        </SCRIPT>""" % "\\n".join(messages)
        )

    else:
        return
