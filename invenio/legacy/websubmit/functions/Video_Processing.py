## This file is part of Invenio.
## Copyright (C) 2011 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""WebSubmit function - Video processing.

"""

__revision__ = "$Id$"

import os

from invenio.jsonutils import json_decode_file
from invenio.errorlib import register_exception
from invenio.bibencode_config import CFG_BIBENCODE_TEMPLATE_BATCH_SUBMISSION
from invenio.bibencode_utils import generate_timestamp
from invenio.bibencode_batch_engine import create_job_from_dictionary
from invenio.config import CFG_SITE_ADMIN_EMAIL

def Video_Processing(parameters, curdir, form, user_info=None):
    """
    Perform all the required processing of the video.

    Parameters are:
    * "batch_template": to specify the absolute path to a
        configuration describe which manipulation should the uploaded file
        receive. If empty, will use by default
        etc/bibencode/batch_template_submission.json
    * "aspect": to specify in which form element the aspect will be available
    * "title": to specify in which form element the title will be available
    """

    ## Read the batch template for submissions
    if parameters.get('batch_template'):
        try:
            batch_template = json_decode_file(parameters.get('batch_template'))
        except:
            register_exception(prefix="The given batch template was not readable")
            raise
    else:
        batch_template = json_decode_file(CFG_BIBENCODE_TEMPLATE_BATCH_SUBMISSION)

    ## Handle the filepath
    file_storing_path = os.path.join(curdir, "files", str(user_info['uid']), "NewFile", 'filepath')
    try:
        fp = open(file_storing_path)
        fullpath = fp.read()
        fp.close()
        batch_template['input'] = fullpath
    except:
        register_exception(prefix="The file containing the path to the video was not readable")
        raise

    ## Handle the filename
    file_storing_name = os.path.join(curdir, "files", str(user_info['uid']), "NewFile", 'filename')
    try:
        fp = open(file_storing_name)
        filename = fp.read()
        fp.close()
        batch_template['bibdoc_master_docname'] = os.path.splitext(os.path.split(filename)[1])[0]
        batch_template['bibdoc_master_extension'] = os.path.splitext(filename)[1]
        batch_template['submission_filename'] = filename
    except:
        register_exception(prefix="The file containing the original filename of the video was not readable")
        raise

    ## Handle the aspect ratio
    if parameters.get('aspect'):
        try:
            file_storing_aspect = os.path.join(curdir, parameters.get('aspect'))
            fp = open(file_storing_aspect)
            aspect = fp.read()
            fp.close()
            batch_template['aspect'] = aspect
        except:
            register_exception(prefix="The file containing the ascpect ratio of the video was not readable")
            raise
    else:
        batch_template['aspect'] = None

    ## Handle the title
    if parameters.get('title'):
        try:
            file_storing_title = os.path.join(curdir, parameters['title'])
            fp = open(file_storing_title)
            title = fp.read()
            fp.close()
        except:
            register_exception(prefix="The file containing the title of the video was not readable")
            raise
    else:
        batch_template['submission_title'] = None

    ## Set the rest
    batch_template['notify_admin'] = CFG_SITE_ADMIN_EMAIL
    batch_template['notify_user'] = user_info['email']
    batch_template['recid'] = sysno

    timestamp = generate_timestamp()
    job_filename = "submission_%d_%s.job" % (sysno, timestamp)
    create_job_from_dictionary(batch_template, job_filename)