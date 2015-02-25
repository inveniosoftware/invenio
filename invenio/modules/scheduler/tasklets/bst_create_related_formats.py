# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012 CERN.
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

"""
Invenio Tasklet.

Create related formats
"""

from invenio.legacy.bibdocfile.api import BibRecDocs
from invenio.legacy.bibsched.bibtask import write_message, \
     task_sleep_now_if_required, \
     task_update_progress
from invenio.legacy.bibdocfile.managedocfiles import get_description_and_comment
from invenio.legacy.websubmit.functions.Shared_Functions import \
     createRelatedFormats
from invenio.legacy.bibdocfile.cli import cli_fix_marc

def bst_create_related_formats(recid, docnames=None, force=0):
    """
    Create the related formats for the given record and docnames.

    @param recid: the record ID to consider
    @type recid: int
    @param docnames: the list of docnames for which we want to create
                     related formats. Separate docnames using '/' character.
    @type docnames: list
    @param force: do we force the creation even if the format already exists (1) or not (0)?
    @type force: int
    """
    force = int(force) and True or False
    recid = int(recid)
    if isinstance(docnames, str):
        docnames = docnames.split('/')
    elif docnames is None:
        docnames = []

    try:
        bibarchive = BibRecDocs(recid)
    except Exception, e:
        write_message("Could not instantiate record #%s: %s" % (recid, e))
        return 0

    write_message("Going to create related file formats for record #%s" % recid)

    i = 0
    for docname in docnames:
        i += 1
        task_sleep_now_if_required()
        msg = "Processing %s (%i/%i)" % (docname, i, len(docnames))
        write_message(msg)
        task_update_progress(msg)
        try:
            bibdoc = bibarchive.get_bibdoc(docname)
        except Exception, e:
            write_message("Could not process docname %s: %s" % (docname, e))
            continue

        (prev_desc, prev_comment) = \
                    get_description_and_comment(bibarchive.get_bibdoc(docname).list_latest_files())

        # List all files that are not icons or subformats
        current_files = [bibdocfile.get_path() for bibdocfile in bibdoc.list_latest_files() if \
                         not bibdocfile.get_subformat() and not bibdocfile.is_icon()]

        ## current_files = []
        ## if not force:
        ##     current_files = [bibdocfile.get_path() for bibdocfile bibdoc.list_latest_files()]
        for current_filepath in current_files:
            # Convert
            new_files = createRelatedFormats(fullpath=current_filepath,
                                             overwrite=force,
                                             consider_version=True)
            # Append
            for new_file in new_files:
                try:
                    bibdoc = bibarchive.add_new_format(new_file,
                                                       docname,
                                                       prev_desc,
                                                       prev_comment)
                except Exception, e:
                    write_message("Could not add format to BibDoc with docname %s: %s" % (docname, e))
                    continue

    write_message("All files successfully processed and attached")
    cli_fix_marc(None, [recid], interactive=False)

    return 1
