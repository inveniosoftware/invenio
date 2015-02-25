# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014 CERN.
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

"""Invenio Bibliographic Tasklet for generating subformats.
   Usange:
   $bibtasklet -N createicons -T bst_create_icons -a recid=123 -a icon_sizes=180,640,1440
   $bibtasklet -N createicons -T bst_create_icons -a "collection=ABC Photos" -a icon_sizes=180,640,1440"""

try:
    from invenio.config import CFG_ICON_CREATION_FORMAT_MAPPINGS
except ImportError, e:
    CFG_ICON_CREATION_FORMAT_MAPPINGS = {'*': ['jpg']}
from invenio.legacy.bibdocfile.api import BibRecDocs
from invenio.legacy.bibdocfile.config import CFG_BIBDOCFILE_DEFAULT_ICON_SUBFORMAT
from invenio.legacy.websubmit.icon_creator import create_icon, CFG_ALLOWED_FILE_EXTENSIONS
from invenio.legacy.bibdocfile.cli import cli_fix_marc
from invenio.legacy.bibsched.bibtask import write_message, \
                            task_update_progress, \
                            task_sleep_now_if_required

import os
import sys

CFG_DEFAULT_ICON_EXTENSION = "gif"
CFG_DEFAULT_ICON_SIZE = '180'

def create_icons_for_record(recid, icon_sizes, icon_format_mappings=None,
                            docnames=None, add_default_icon=False, inherit_moreinfo=False):
    """Generate icons, if missing, for a record
       @param recid: the record id for which icons are being created
       @type recid: int
       @param icon_sizes: the list of icon sizes that need to be
       generated. Note that upscaled is not allowed
       @type icon_sizes: list
       @param icon_format_mappings: defines for each "master" format in
                                   which format the icons should be
                                   created. If the master format is
                                   not specified here, then its icons
                                   will be created in the same format,
                                   if possible (for eg. the icons of a
                                   TIFF file would be created as TIFF,
                                   while icons of a PDF or DOC file
                                   would be created in JPG) and unless
                                   a default mapping is not provided in
                                   C{CFG_ICON_CREATION_FORMAT_MAPPINGS}.
       @type icon_format_mappings: dict
       @param docnames: the list of docnames for which we want to create an icon.
                        If not provided, consider all docnames.
       @type docnames: list
       @param add_default_icon: if a default icon (i.e. without icon
                                size suffix, matching
                                CFG_BIBDOCFILE_DEFAULT_ICON_SUBFORMAT)
                                should be added or not.
       @type add_default_icon: bool
       @param inherit_moreinfo: if the added icons should also have
                                their description and comment set to
                                the same value as the "main" bibdoc
                                or not.
       @type inherit_moreinfo: bool
    """
    exceptions = [] # keep track of all exceptions
    done = 0
    brd = BibRecDocs(recid)
    bibdocs = brd.list_bibdocs()
    # Override default formats from CFG_ICON_CREATION_FORMAT_MAPPINGS
    # with values specified in icon_format_mappings
    if icon_format_mappings is None:
        icon_format_mappings = {}
    icon_format_mappings = dict(CFG_ICON_CREATION_FORMAT_MAPPINGS, **icon_format_mappings)
    if icon_format_mappings.has_key('*') and \
      not icon_format_mappings['*']:
        # we must override the default in order to keep the
        # "superformat"
        del icon_format_mappings['*']
    for bibdoc in bibdocs:
        docname = brd.get_docname(bibdoc.id)
        if docnames and not docname in docnames:
            # Skip this docname
            continue
        comment, description = get_comment_and_description(bibdoc, inherit_moreinfo)
        default_icon_added_p = False
        bibfiles = bibdoc.list_latest_files()
        bibdoc_formats = [bibfile.get_format() for bibfile in bibfiles]
        for bibfile in bibfiles:
            if bibfile.get_subformat():
                # this is a subformat, do nothing
                continue
            filepath = bibfile.get_full_path()
            #do not consider the dot in front of the format
            superformat = bibfile.get_format()[1:].lower()
            bibfile_icon_formats = icon_format_mappings.get(superformat, icon_format_mappings.get('*', [superformat]))
            if isinstance(bibfile_icon_formats, str):
                bibfile_icon_formats = [bibfile_icon_formats]
            bibfile_icon_formats = [bibfile_icon_format for bibfile_icon_format in bibfile_icon_formats \
                                    if bibfile_icon_format in CFG_ALLOWED_FILE_EXTENSIONS]

            if add_default_icon and not default_icon_added_p:
                # add default icon
                try:
                    iconpath, iconname = _create_icon(filepath, CFG_DEFAULT_ICON_SIZE, docname,
                                                      icon_format=CFG_DEFAULT_ICON_EXTENSION, verbosity=9)
                    bibdoc.add_file_new_format(os.path.join(iconpath, iconname),
                                               docformat=".%s;%s" % (CFG_DEFAULT_ICON_EXTENSION,
                                                                     CFG_BIBDOCFILE_DEFAULT_ICON_SUBFORMAT),
                                               comment=comment, description=description)
                    default_icon_added_p = True
                    write_message("Added default icon to recid: %s, format: %s" % (recid, CFG_DEFAULT_ICON_EXTENSION))
                except Exception, ex:
                    exceptions.append("Could not add new icon to recid: %s, format: %s; exc: %s" \
                                      % (recid, CFG_DEFAULT_ICON_EXTENSION, ex))

            # check if the subformat that we want to create already exists
            for icon_size in icon_sizes:
                washed_icon_size = icon_size.replace('>', '').replace('<', '').replace('^', '').replace('!', '')
                for icon_format in bibfile_icon_formats:
                    new_format = '.%s;%s-%s' % (icon_format, CFG_BIBDOCFILE_DEFAULT_ICON_SUBFORMAT, washed_icon_size)
                    if new_format in bibdoc_formats:
                        # the subformat already exists, do nothing
                        continue
                    # add icon
                    try:
                        iconpath, iconname = _create_icon(filepath, icon_size, docname,
                                                          icon_format=icon_format, verbosity=9)
                        bibdoc.add_file_new_format(os.path.join(iconpath, iconname), docformat=new_format,
                                                   comment=comment, description=description)
                        write_message("Added icon to recid: %s, format: %s %s %s %s" % (recid, new_format, iconpath, iconname, icon_size))
                        done += 1
                    except Exception, ex:
                        exceptions.append("Could not add new format to recid: %s, format: %s; exc: %s" \
                                            %(recid, new_format, ex))
    return done, exceptions


def bst_create_icons(recid, icon_sizes, icon_format_mappings=None,
                     collection=None, docnames=None, add_default_icon=0, inherit_moreinfo=0):
    """BibTasklet for generating missing icons.
       @param recid: the record on which the action is being performed
       @type recid: int
       @param icon_sizes: a comma-separated list of icon sizes, ex 180,640
       @type icon_sizes: string
       @param collection: the collection name on which to run the task;
                          if recid is defined, collection will be ignored
       @type collection: string
       @param icon_format_mappings: defines for each "master" format in
                                   which format the icons should be
                                   created. If the master format is
                                   not specified here, then its icons
                                   will be created in the same format,
                                   if possible (for eg. the icons of a
                                   TIFF file would be created as TIFF,
                                   while icons of a PDF or DOC file
                                   would be created in JPG) and unless
                                   a default mapping is not provided in
                                   C{CFG_ICON_CREATION_FORMAT_MAPPINGS}.
                                   Use syntax masterextension-targetextension1,targetextension2
                                   (eg. "doc->png,jpg" or "png-jpg")
                                   Use '*' to target extensions not
                                   matched by other rules (if
                                   necessary set its value to empty ''
                                   in order to override/remove the
                                   default star rule set in
                                   C{CFG_ICON_CREATION_FORMAT_MAPPINGS}.
       @type icon_format_mappings: list
       @param docnames: the list of docnames for which we want to create an icon.
                        If not provided, consider all docnames.
                        Separate docnames using "/"
       @type docnames: list
       @param add_default_icon: if a default icon (i.e. without icon
                                size suffix, matching
                                CFG_BIBDOCFILE_DEFAULT_ICON_SUBFORMAT)
                                should be added (1) or not (0)
       @type add_default_icon: int
       @param inherit_moreinfo: if the added icons should also have
                                their description and comment set to
                                the same value as the "main" bibdoc
                                (1) or not (0)
       @type inherit_moreinfo: int
    """
    if recid:
        recids = [int(recid)]
    elif collection:
        from invenio.legacy.search_engine import get_collection_reclist
        recids = get_collection_reclist(collection)
    else:
        write_message("Error: no recid found.", sys.stderr)
        return 1
    try:
        add_default_icon = int(add_default_icon) and True or False
    except:
        add_default_icon = False
    try:
        inherit_moreinfo = int(inherit_moreinfo) and True or False
    except:
        inherit_moreinfo = False
    if icon_format_mappings is None:
        icon_format_mappings = []
    if isinstance(icon_format_mappings, str):
        icon_format_mappings = [icon_format_mappings]
    try:
        icon_format_mappings = dict([map(lambda x: ',' in x and x.split(',') or x, mapping.split("-", 1)) \
                                     for mapping in icon_format_mappings])
    except Exception, e:
        write_message("Error: parameter 'icon_format_mappings' not well-formed:\n%s" % e, sys.stderr)
        return 0

    write_message("Generating formats for %s record%s." \
                    % (len(recids), len(recids) > 1 and 's' or ''))

    icon_sizes = icon_sizes.split(',')
    if isinstance(docnames, str):
        docnames = docnames.split('/')

    updated = 0
    for i, recid in enumerate(recids):
        done, exceptions = create_icons_for_record(recid, icon_sizes,
                                                   icon_format_mappings,
                                                   docnames, add_default_icon,
                                                   inherit_moreinfo)
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

def _create_icon(file_path, icon_size, docname, icon_format='gif', verbosity=9):
    """
    Creates icon of given file.

    Returns path to the icon. If creation fails, return None, and
    register exception (send email to admin).


    @param file_path: full path to icon
    @type file_path: string

    @param icon_size: the scaling information to be used for the
                      creation of the new icon.
    @type icon_size: int

    @param icon_format: format to use to create the icon
    @type icon_format: string

    @param verbosity: the verbosity level under which the program
                      is to run;
    @type verbosity: int
    """
    if icon_size.isdigit():
        # It makes sense to explicitely not upscale images
        icon_size += '>'
    icon_properties = {
        'input-file'      : file_path,
        'icon-name'       : docname,
        'multipage-icon': False,
        'multipage-icon-delay': 0,
        'icon-file-format': "%s" % icon_format,
        'icon-scale'      : "%s" % icon_size,
        'verbosity'       : verbosity,
        }
    return create_icon(icon_properties)

def get_comment_and_description(bibdoc, inherit_moreinfo):
    """
    Return the bibdoc comment and description, according to the
    model/assumption that the sames are applied to all bibdocfiles of
    the bibdoc, if inherit_moreinfo is set to True.
    """
    comment = None
    description = None
    if inherit_moreinfo:
        all_descriptions = [bibdocfile.get_description() for bibdocfile \
                            in bibdoc.list_latest_files()
                            if bibdocfile.get_description() not in ['', None]]
        if len(all_descriptions) > 0:
            description = all_descriptions[0]

        all_comments = [bibdocfile.get_comment() for bibdocfile \
                        in bibdoc.list_latest_files()
                        if bibdocfile.get_comment() not in ['', None]]
        if len(all_comments) > 0:
            comment = all_comments[0]

    return (comment, description)
