# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2010, 2011, 2013, 2015 CERN.
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

""" Invenio bibsched task for uploading multiple documents
    or metadata files. This task can run in two different modes:
    metadata or documents.
    The parent directory from where the folders metadata and
    documents are expected to be found has to be specified
    in the invenio config file.
"""
import os.path

__revision__ = "$Id$"

import sys
import os
import time
import tempfile
import shutil
from invenio.config import (CFG_TMPSHAREDDIR,
                            CFG_BATCHUPLOADER_DAEMON_DIR,
                            CFG_BATCHUPLOADER_FILENAME_MATCHING_POLICY)
from invenio.legacy.bibsched.bibtask import (
    task_init,
    task_set_option,
    task_get_option,
    task_update_progress,
    task_low_level_submission,
    write_message,
    task_sleep_now_if_required)
from invenio.legacy.batchuploader.engine import document_upload


def task_submit_elaborate_specific_parameter(key, value, opts, args):
    """ Given the string key, checks its meaning and returns True if
        has elaborated the key.
        Possible keys:
    """
    if key in ('-d', '--documents'):
        task_set_option('documents', "documents")
        return True
    elif key in ('-m', '--metadata'):
        task_set_option('metadata', "metadata")
        return True
    return False


def task_run_core():
    """ Walks through all directories where metadata files are located
        and uploads them.
        Files are then moved to the corresponding DONE folders.
    """
    # Check if directory /batchupload exists
    if not task_get_option('documents'):
        # Metadata upload
        parent_dir = os.path.join(CFG_BATCHUPLOADER_DAEMON_DIR, "metadata/")
        progress = 0
        try:
            os.makedirs(parent_dir)
        except OSError:
            pass
        list_of_folders = ["insert",
                           "append",
                           "correct",
                           "replace",
                           "holdingpen"]
        for folder in list_of_folders:
            files_dir = os.path.join(parent_dir, folder)
            files_done_dir = os.path.join(files_dir, "DONE")
            try:
                files = os.listdir(files_dir)
            except OSError as e:
                os.mkdir(files_dir)
                files = []
                write_message(e, sys.stderr)
                write_message("Created new folder %s" % (files_dir,))
            # Create directory DONE/ if doesn't exist
            try:
                os.mkdir(files_done_dir)
            except OSError:
                # Directory exists
                pass
            for metafile in files:
                if os.path.isfile(os.path.join(files_dir, metafile)):
                    # Create temporary file to be uploaded
                    (fd, filename) = tempfile.mkstemp(prefix=metafile + "_" + time.strftime("%Y%m%d%H%M%S", time.localtime()) + "_", dir=CFG_TMPSHAREDDIR)
                    shutil.copy(os.path.join(files_dir, metafile), filename)
                    # Send bibsched task
                    mode = "--" + folder
                    jobid = str(task_low_level_submission('bibupload', 'batchupload', mode, filename))
                    # Move file to done folder
                    filename = metafile + "_" + time.strftime("%Y%m%d%H%M%S", time.localtime()) + "_" + jobid
                    os.rename(os.path.join(files_dir, metafile), os.path.join(files_done_dir, filename))
                    task_sleep_now_if_required(can_stop_too=True)
            progress += 1
            task_update_progress("Done %d out of %d." % (progress, len(list_of_folders)))
    else:
        # Documents upload
        parent_dir = daemon_dir + "/documents/"
        try:
            os.makedirs(parent_dir)
        except OSError:
            pass
        matching_order = CFG_BATCHUPLOADER_FILENAME_MATCHING_POLICY
        for folder in ["append/", "revise/"]:
            try:
                os.mkdir(parent_dir + folder)
            except:
                pass
            for matching in matching_order:
                errors = document_upload(folder=parent_dir + folder, matching=matching, mode=folder[:-1])[0]
                if not errors:
                    break  # All documents succedeed with that matching
                for error in errors:
                    write_message("File: %s - %s with matching %s" % (error[0], error[1], matching), sys.stderr)
            task_sleep_now_if_required(can_stop_too=True)
    return 1


def main():
    """ Main that constructs all the bibtask. """
    task_init(authorization_action='runbatchuploader',
              authorization_msg="Batch Uploader",
              description="""Description:
    The batch uploader has two different run modes.
    If --metadata is specified (by default) then all files in folders insert,
    append, correct and replace are uploaded using the corresponding mode.
    If mode --documents is selected all documents present in folders named
    append and revise are uploaded using the corresponding mode.
    Parent directory for batch uploader must be specified in the
    invenio configuration file.\n""",
              help_specific_usage=""" -m, --metadata\t Batch Uploader will look for metadata files in the corresponding folders
 -d, --documents\t Batch Uploader will look for documents in the corresponding folders
                                """,
              version=__revision__,
              specific_params=("md:", ["metadata", "documents"]),
              task_submit_elaborate_specific_parameter_fnc=task_submit_elaborate_specific_parameter,
              task_run_fnc=task_run_core)

if __name__ == '__main__':
    main()
