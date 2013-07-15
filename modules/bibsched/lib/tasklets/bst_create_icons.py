# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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

"""Invenio Bibliographic Tasklet for generating subformats.
   Usange:
   $bibtasklet -N createicons -T bst_create_icons -a recid=123 -a icon_sizes=180,640,1440
   $bibtasklet -N createicons -T bst_create_icons -a "collection=ABC Photos" -a icon_sizes=180,640,1440"""

from invenio.bibdocfile import BibRecDocs
from invenio.bibdocfile_config import CFG_BIBDOCFILE_DEFAULT_ICON_SUBFORMAT
from invenio.websubmit_icon_creator import create_icon
from invenio.bibdocfilecli import cli_fix_marc
from invenio.bibtask import write_message, \
                            task_update_progress, \
                            task_sleep_now_if_required

import os
import sys

def create_icons_for_record(recid, icon_sizes):
    """Generate icons, if missing, for a record
       @param recid: the record id for which icons are being created
       @type recid: int
       @param icon_sizes: the list of icon sizes that need to be generated
       @type icon_sizes: list
    """
    exceptions = [] # keep track of all exceptions
    done = 0
    bibdocs = BibRecDocs(recid).list_bibdocs()
    for bibdoc in bibdocs:
        docname = bibdoc.get_docname()
        bibfiles = bibdoc.list_latest_files()
        bibdoc_formats = [bibfile.get_format() for bibfile in bibfiles]
        for bibfile in bibfiles:
            if bibfile.get_subformat():
                # this is a subformat, do nothing
                continue
            filepath = bibfile.get_full_path()
            #do not consider the dot in front of the format
            superformat = bibfile.get_format()[1:]
            # check if the subformat that we want to create already exists
            for icon_size in icon_sizes:
                new_format = '.%s;%s-%s' % (superformat, CFG_BIBDOCFILE_DEFAULT_ICON_SUBFORMAT, icon_size)
                if new_format in bibdoc_formats:
                    # the subformat already exists, do nothing
                    continue
                icon_properties = {
                        'input-file'      : filepath,
                        'icon-name'       : docname,
                        'multipage-icon': False,
                        'multipage-icon-delay': 0,
                        'icon-file-format': "%s" % superformat,
                        'icon-scale'      : "%s>" % icon_size,
                        'verbosity'       : 0,
                }
                try:
                    iconpath, iconname = create_icon(icon_properties)
                    bibdoc.add_file_new_format(os.path.join(iconpath, iconname), format=new_format)
                    done += 1
                except Exception, ex:
                    exceptions.append("Could not add new format to recid: %s, format: %s; exc: %s" \
                                        %(recid, new_format, ex))
    return done, exceptions


def bst_create_icons(recid, icon_sizes, collection=None):
    """BibTasklet for generating missing icons.
       @param recid: the record on which the action is being performed
       @type recid: int
       @param icon_sizes: a comma-separated list of icon sizes, ex 180,640
       @type icon_sizes: string
       @param collection: the collection name on which to run the task;
                          if recid is defined, colection will be ignored
       @type collection: string
    """
    if recid:
        recids = [int(recid)]
    elif collection:
        from invenio.search_engine import get_collection_reclist
        recids = get_collection_reclist(collection)
    else:
        write_message("Error: no recid found.", sys.stderr)
        return 1
    write_message("Generating formats for %s record%s." \
                    % (len(recids), len(recids) > 1 and 's' or ''))

    icon_sizes = icon_sizes.split(',')
    icon_sizes = [int(icon_size.strip()) for icon_size in icon_sizes]

    updated = 0
    for i, recid in enumerate(recids):
        done, exceptions =  create_icons_for_record(recid, icon_sizes)
        updated += done
        if exceptions:
            for ex in exceptions:
                write_message(ex)
        else:
            write_message("Recid %s DONE." % recid)

        task_update_progress("Done %d out of %d." % (i, len(recids)))
        task_sleep_now_if_required(can_stop_too=True)

    if updated:
        cli_fix_marc(None, explicit_recid_set=recids, interactive=False)

    return 1

