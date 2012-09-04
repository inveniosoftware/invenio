## $Id: Move_Revised_Files_to_Storage.py,v 1.20 2009/03/26 13:48:42 jerome Exp $

## This file is part of Invenio.
## Copyright (C) 2009, 2010, 2011 CERN.
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
"""WebSubmit function - Archives uploaded files

TODO:

 - Add parameter 'elementNameToFilename' so that files to revise can
   be matched by name instead of doctype.

 - Icons are created only for uploaded files, but not for related format
   created on the fly.

"""

__revision__ = "$Id$"

import time
import os

from invenio.bibdocfile import \
     InvenioWebSubmitFileError, \
     BibRecDocs
from invenio.errorlib import register_exception
from invenio.websubmit_icon_creator import \
     create_icon, InvenioWebSubmitIconCreatorError
from invenio.config import CFG_BINDIR
from invenio.dbquery import run_sql
from invenio.websubmit_functions.Shared_Functions import \
     createRelatedFormats
from invenio.websubmit_managedocfiles import get_description_and_comment

def Move_Revised_Files_to_Storage(parameters, curdir, form, user_info=None):
    """
    The function revises the files of a record with the newly uploaded
    files.

    This function can work only if you can define a mapping from the
    WebSubmit element name that uploads the file, to the doctype of
    the file. In most cases, the doctype is equivalent to the element
    name, or just map to 'Main' doctype. That is typically the case if
    you use the Move_Files_to_Storage.py function to upload the files
    at submission step. For eg. with the DEMOBOO submission of the
    Atlantis Demo site, a file is uploaded thanks to the DEMOBOO_FILE
    element/File input, which is mapped to doctype DEMOBOO_FILE.

    The function ignores files for which multiple files exist for a
    single doctype in the record, or when several files are uploaded
    with the same element name.  If the record to revise does not have
    a corresponding file, the file is inserted


    This function is similar to Move_Uploaded_Files_to_Storage.py,
    excepted that Move_Uploaded_Files_to_Storage relies on files
    uploaded from the web interface created by
    Create_Upload_Files_Interface.py, while this function relies on
    the files uploaded by a regular WebSubmit page that you have built
    from WebSubmit admin:

    Regular WebSubmit interface       --(upload file)-->  Move_Revised_Files_to_Storage.py
    Create_Upload_Files_Interface.py  --(upload file)-->  Move_Uploaded_Files_to_Storage.py

    The main advantages of this function over the functions
    Create_Upload_Files_Interface.py/Move_Uploaded_Files_to_Storage is
    that it lets you customize the display of your submission in the
    way you want, which could be simpler for your users if you usually
    only upload a few and fixed number of files per record. The
    disadvantages are that this function is not capable of : deleting
    files, adding an alternative format to a file, add a variable
    number of files, does not allow to set permissions at the level of
    file, does not support user comments, renaming, etc.

    @param parameters:(dictionary) - must contain:

      + elementNameToDoctype: maps an element/field name to a doctype.
                              Eg. the file uploaded from the
                              DEMOBOO_FILE element (input file tag)
                              should revise the file with document
                              type (doctype) "Main":
                                 DEMOBOO_FILE=Main|DEMOBOO_FILE_2=ADDITIONAL
                              ('=' separates element name and doctype
                               '|' separates each doctype/element name group)

                              In most cases, the element name == doctype:
                               DEMOBOO_FILE=DEMOBOO_FILE|DEMOBOO_FILE_2=DEMOBOO_FILE_2

      + createIconDoctypes: the list of doctypes for which an icon
                            should be created when revising the file.
                            Eg:
                                Figure|Graph
                              ('|' separated values)
                              Use '*' for all doctypes

      + iconsize: size of the icon to create (when applicable)

      + keepPreviousVersionDoctypes: the list of doctypes for which
                                     the function should keep previous
                                     versions visible when revising a
                                     file.
                                     Eg:
                                       Main|Additional
                                     ('|' separated values)
                                     Default is all

      + createRelatedFormats: if uploaded files get converted to
                              whatever format we can (1) or not (0)
    """
    # pylint: disable=E0602
    # sysno is defined in the WebSubmit functions sandbox.

    global sysno
    bibrecdocs = BibRecDocs(int(sysno))

    # Wash function parameters
    (element_name_and_doctype, create_icon_doctypes, iconsize,
     keep_previous_version_doctypes, createRelatedFormats_p) = \
     wash_function_parameters(parameters, curdir)

    for element_name, doctype in element_name_and_doctype:
        _do_log(curdir, "Processing " + element_name)
        # Check if there is a corresponding file
        file_path = os.path.join(curdir, 'files', element_name,
                                 read_file(curdir, element_name))
        if file_path and os.path.exists(file_path):
            # Now identify which file to revise
            files_in_record = bibrecdocs.list_bibdocs(doctype)
            if len(files_in_record) == 1:
                # Ok, we can revise
                bibdoc_name = files_in_record[0].get_docname()
                revise(bibrecdocs, curdir, sysno, file_path,
                       bibdoc_name, doctype, iconsize,
                       create_icon_doctypes,
                       keep_previous_version_doctypes,
                       createRelatedFormats_p)
            elif len(files_in_record) == 0:
                # We must add the file
                add(bibrecdocs, curdir, sysno, file_path,
                    doctype, iconsize, create_icon_doctypes,
                    createRelatedFormats_p)
            else:
                _do_log(curdir, "  %s ignored, because multiple files found for same doctype %s in record %s: %s" %\
                        (element_name, doctype, sysno,
                         ', '.join(files_in_record)))
        else:
            _do_log(curdir, "  No corresponding file found (%s)" % file_path)


    # Update the MARC
    bibdocfile_bin = os.path.join(CFG_BINDIR, 'bibdocfile --yes-i-know')
    os.system(bibdocfile_bin + " --fix-marc --recid=" + sysno)

    # Delete the HB BibFormat cache in the DB, so that the fulltext
    # links do not point to possible dead files
    run_sql("DELETE LOW_PRIORITY from bibfmt WHERE format='HB' AND id_bibrec=%s", (sysno,))

    # pylint: enable=E0602

def add(bibrecdocs, curdir, sysno, file_path, doctype,
        iconsize, create_icon_doctypes, createRelatedFormats_p):
    """
    Adds the file using bibdocfile
    """
    try:
        # Add file
        bibdoc = bibrecdocs.add_new_file(file_path,
                                         doctype,
                                         never_fail=True)
        _do_log(curdir, '  Added ' + bibdoc.get_docname() + ': ' + \
                file_path)

        # Add icon
        iconpath = ''
        if doctype in create_icon_doctypes or \
               '*' in create_icon_doctypes:
            iconpath = _create_icon(file_path, iconsize)
            if iconpath is not None:
                bibdoc.add_icon(iconpath)
                _do_log(curdir, '  Added icon to ' + \
                        bibdoc.get_docname() + ': ' + iconpath)

        # Automatically create additional formats when
        # possible.
        additional_formats = []
        if createRelatedFormats_p:
            additional_formats = createRelatedFormats(file_path,
                                                      overwrite=False)
        for additional_format in additional_formats:
            bibdoc.add_new_format(additional_format,
                                  bibdoc.get_docname())
            # Log
            _do_log(curdir, '  Added format ' + additional_format + \
                    ' to ' + bibdoc.get_docname() + ': ' + iconpath)


    except InvenioWebSubmitFileError, e:
        # Format already existed.  How come? We should
        # have checked this in Create_Upload_Files_Interface.py
        register_exception(prefix='Move_Revised_Files_to_Storage ' \
                           'tried to add already existing file %s ' \
                           'to record %i. %s' % \
                           (file_path, sysno, curdir),
                           alert_admin=True)

def revise(bibrecdocs, curdir, sysno, file_path, bibdoc_name, doctype,
           iconsize, create_icon_doctypes,
           keep_previous_version_doctypes, createRelatedFormats_p):
    """
    Revises the given bibdoc with a new file
    """
    try:

        # Retrieve the current description and comment, or they
        # will be lost when revising
        latest_files = bibrecdocs.list_bibdocs(doctype)[0].list_latest_files()
        prev_desc, prev_comment = get_description_and_comment(latest_files)

        if doctype in keep_previous_version_doctypes:
            # Standard procedure, keep previous version
            bibdoc = bibrecdocs.add_new_version(file_path,
                                                bibdoc_name,
                                                prev_desc,
                                                prev_comment)
            _do_log(curdir, '  Revised ' + bibdoc.get_docname() + \
                    ' with : ' + file_path)

        else:
            # Soft-delete previous versions, and add new file
            # (we need to get the doctype before deleting)
            if bibrecdocs.has_docname_p(bibdoc_name):
                # Delete only if bibdoc originally
                # existed
                bibrecdocs.delete_bibdoc(bibdoc_name)
                _do_log(curdir, '  Deleted ' + bibdoc_name)
            try:
                bibdoc = bibrecdocs.add_new_file(file_path,
                                                 doctype,
                                                 bibdoc_name,
                                                 never_fail=True,
                                                 description=prev_desc,
                                                 comment=prev_comment)
                _do_log(curdir, '  Added ' + bibdoc.get_docname() + ': ' + \
                        file_path)

            except InvenioWebSubmitFileError, e:
                _do_log(curdir, str(e))
                register_exception(prefix='Move_Uploaded_Files_to_Storage ' \
                                   'tried to revise a file %s ' \
                                   'named %s in record %i. %s' % \
                                   (file_path, bibdoc_name, sysno, curdir),
                                   alert_admin=True)

        # Add icon
        iconpath = ''
        if doctype in create_icon_doctypes or \
               '*' in create_icon_doctypes:
            iconpath = _create_icon(file_path, iconsize)
            if iconpath is not None:
                bibdoc.add_icon(iconpath)
                _do_log(curdir, 'Added icon to ' + \
                        bibdoc.get_docname() + ': ' + iconpath)

        # Automatically create additional formats when
        # possible.
        additional_formats = []
        if createRelatedFormats_p:
            additional_formats = createRelatedFormats(file_path,
                                                      overwrite=False)
        for additional_format in additional_formats:
            bibdoc.add_new_format(additional_format,
                                  bibdoc_name,
                                  prev_desc,
                                  prev_comment)
            # Log
            _do_log(curdir, '  Addeded format ' + additional_format + \
                    ' to ' + bibdoc.get_docname() + ': ' + iconpath)

    except InvenioWebSubmitFileError, e:
        # Format already existed.  How come? We should
        # have checked this in Create_Upload_Files_Interface.py
        register_exception(prefix='Move_Revised_Files_to_Storage ' \
                           'tried to revise a file %s ' \
                           'named %s in record %i. %s' % \
                           (file_path, bibdoc_name, sysno, curdir),
                           alert_admin=True)

def wash_function_parameters(parameters, curdir):
    """
    Returns the functions (admin-defined) parameters washed and
    initialized properly, as a tuple:

    Parameters:

        check Move_Revised_Files_to_Storage(..) docstring

    Returns:

        tuple (element_name_and_doctype, create_icon_doctypes, iconsize,
               keep_previous_version_doctypes, createRelatedFormats_p)
    """

    # The mapping element name -> doctype.
    # '|' is used to separate mapping groups, and '=' to separate
    # element name and doctype.
    # Eg: DEMOBOO_FILE=Main|DEMOBOO_FILEADDITIONAL=Additional File
    element_name_and_doctype = [mapping.strip().split("=") for mapping \
                                in parameters['elementNameToDoctype'].split('|') \
                                if mapping.strip() != '']

    # The list of doctypes for which we want to create an icon
    # (list of values separated by "|")
    create_icon_doctypes = [doctype.strip() for doctype \
                            in parameters['createIconDoctypes'].split('|') \
                            if doctype.strip() != '']

    # If we should create additional formats when applicable (1) or
    # not (0)
    try:
        createRelatedFormats_p = int(parameters['createRelatedFormats'])
    except ValueError, e:
        createRelatedFormats_p = False

    # Icons size
    iconsize = parameters.get('iconsize')

    # The list of doctypes for which we want to keep previous versions
    # of files visible.
    # (list of values separated by "|")
    keep_previous_version_doctypes = [doctype.strip() for doctype \
                                      in parameters['keepPreviousVersionDoctypes'].split('|') \
                                      if doctype.strip() != '']

    if not keep_previous_version_doctypes:
        # Nothing specified: keep all by default
        keep_previous_version_doctypes = [doctype for (elem, doctype) \
                                          in element_name_and_doctype]

    return (element_name_and_doctype, create_icon_doctypes, iconsize,
            keep_previous_version_doctypes, createRelatedFormats_p)

def _do_log(log_dir, msg):
    """
    Log what we have done, in case something went wrong.
    Nice to compare with bibdocactions.log

    Should be removed when the development is over.
    """
    log_file = os.path.join(log_dir, 'performed_actions.log')
    file_desc = open(log_file, "a+")
    file_desc.write("%s --> %s\n" %(time.strftime("%Y-%m-%d %H:%M:%S"), msg))
    file_desc.close()

def _create_icon(file_path, icon_size, format='gif', verbosity=9):
    """
    Creates icon of given file.

    Returns path to the icon. If creation fails, return None, and
    register exception (send email to admin).

    Parameters:

       - file_path : *str* full path to icon

       - icon_size : *int* the scaling information to be used for the
                     creation of the new icon.

       - verbosity : *int* the verbosity level under which the program
                     is to run;
    """
    icon_path = None
    try:
        filename = os.path.splitext(os.path.basename(file_path))[0]
        (icon_dir, icon_name) = create_icon(
            {'input-file':file_path,
             'icon-name': "icon-%s" % filename,
             'multipage-icon': False,
             'multipage-icon-delay': 0,
             'icon-scale': icon_size,
             'icon-file-format': format,
             'verbosity': verbosity})
        icon_path = icon_dir + os.sep + icon_name
    except InvenioWebSubmitIconCreatorError, e:
        register_exception(prefix='Icon for file %s could not be created: %s' % \
                           (file_path, str(e)),
                           alert_admin=False)
    return icon_path

def read_file(curdir, filename):
    """
    Reads a file in curdir.
    Returns None if does not exist, cannot be read, or if file is not
    really in curdir
    """
    try:
        file_path = os.path.abspath(os.path.join(curdir, filename))
        if not file_path.startswith(curdir):
            return None
        file_desc = file(file_path, 'r')
        content = file_desc.read()
        file_desc.close()
    except:
        content = None

    return content
