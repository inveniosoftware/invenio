# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002, 2003, 2004, 2005 CERN.
##
## The CDSware is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## The CDSware is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDSware; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import cdsware.elmsubmit as elmsubmit
import cdsware.websubmit_engine as websubmit_engine
from cdsware.elmsubmit_misc import dict2file as _dict2file
import os.path

required_fields = ['title',
                   'author',
                   'date',
                   'files']

doctype = 'TEST'

def handler(msg, submission_dict, elmconf):

    # Process the files list:

    elmsubmit.process_files(msg, submission_dict)

    # Get a submission directory:

    storage_dir = elmsubmit.get_storage_dir(msg, doctype)
    access = os.path.basename(storage_dir)

    # Write the neccessary data format out to submission directory:

    try:
        _dict2file(submission_dict, storage_dir)
    except EnvironmentError:
        response_email = elmconf.nolangmsgs.temp_problem
        admin_response_email = "There was a problem writing data to directory %s." % (storage_dir)
        error = elmsubmit.elmsubmitError("There was a problem writing data to directory %s." % (storage_dir))
        return (response_email, admin_response_email, error)
    
    # Pass the submission to CDSware proper:
    
    try:    
        websubmit_engine.simpleendaction(doctype=doctype, act="SBI", startPg=1,
                                         indir=os.path.basename(elmconf.files.maildir),
                                         access=access)
    except websubmit_engine.functionError, e:
        response_email = elmconf.nolangmsgs.temp_problem
        admin_response_email = None
        error = elmsubmit.elmsubmitError("elmsubmit encountered websubmit functionError error: " + e.value)
        return (response_email, admin_response_email, error)
        
    except websubmit_engine.functionStop, e:
        response_email = elmconf.nolangmsgs.temp_problem
        admin_response_email = "elmsubmit encountered websubmit error: " + e.value
        error = elmsubmit.elmsubmitError("elmsubmit encountered websubmit functionStop error: " + e.value)
        return (response_email, admin_response_email, error)

    # CDSWare proper will now email the user for us.
    return (None, None, None)


