# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2009, 2010, 2011 CERN.
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
"""Function for archiving files"""

__revision__ = "$Id$"

from invenio.legacy.bibdocfile.api import \
     BibRecDocs, \
     decompose_file, \
     InvenioBibDocFileError, \
     CFG_BIBDOCFILE_DEFAULT_ICON_SUBFORMAT
import os
import re
from invenio.legacy.websubmit.icon_creator import create_icon
from invenio.legacy.websubmit.config import InvenioWebSubmitFunctionWarning
from invenio.legacy.websubmit.functions.Shared_Functions import get_dictionary_from_string, \
     createRelatedFormats
from invenio.ext.logging import register_exception
from invenio.config import CFG_BINDIR
from invenio.legacy.dbquery import run_sql
from invenio.utils.shell import run_shell_command

def Move_Files_to_Storage(parameters, curdir, form, user_info=None):
    """
    The function moves files received from the standard submission's
    form through file input element(s). The document are assigned a
    'doctype' (or category) corresponding to the file input element
    (eg. a file uploaded throught 'DEMOPIC_FILE' will go to
    'DEMOPIC_FILE' doctype/category).

    Websubmit engine builds the following file organization in the
    directory curdir/files:

                  curdir/files
                        |
      _____________________________________________________________________
            |                                   |                          |
      ./file input 1 element's name      ./file input 2 element's name    ....
         (for eg. 'DEMOART_MAILFILE')       (for eg. 'DEMOART_APPENDIX')
         |                                     |
      test1.pdf                             test2.pdf


    There is only one instance of all possible extension(pdf, gz...) in each part
    otherwise we may encounter problems when renaming files.

    + parameters['rename']: if given, all the files in curdir/files
      are renamed.  parameters['rename'] is of the form:
      <PA>elemfilename[re]</PA>* where re is an regexp to select(using
      re.sub) what part of the elem file has to be selected.
      e.g: <PA>file:TEST_FILE_RN</PA>

    + parameters['documenttype']: if given, other formats are created.
      It has 2 possible values: - if "picture" icon in gif format is created
                                - if "fulltext" ps, gz .... formats are created

    + parameters['paths_and_suffixes']: directories to look into and
      corresponding suffix to add to every file inside. It must have
      the same structure as a Python dictionnary of the following form
      {'FrenchAbstract':'french', 'EnglishAbstract':''}

      The keys are the file input element name from the form <=>
      directories in curdir/files The values associated are the
      suffixes which will be added to all the files in
      e.g. curdir/files/FrenchAbstract

    + parameters['iconsize'] need only if 'icon' is selected in
      parameters['documenttype']

    + parameters['paths_and_restrictions']: the restrictions to apply
      to each uploaded file. The parameter must have the same
      structure as a Python dictionnary of the following form:
      {'DEMOART_APPENDIX':'restricted'}
      Files not specified in this parameter are not restricted.
      The specified restrictions can include a variable that can be
      replaced at runtime, for eg:
      {'DEMOART_APPENDIX':'restricted to <PA>file:SuE</PA>'}

    + parameters['paths_and_doctypes']: if a doctype is specified,
      the file will be saved under the 'doctype/collection' instead
      of under the default doctype/collection given by the name
      of the upload element that was used on the websubmit interface.
      to configure the doctype in websubmit, enter the value as in a
      dictionnary, for eg:
      {'PATHS_SWORD_UPL' : 'PUSHED_TO_ARXIV'} -> from
      Demo_Export_Via_Sword [DEMOSWR] Document Types
    """

    global sysno
    paths_and_suffixes = parameters['paths_and_suffixes']
    paths_and_restrictions = parameters['paths_and_restrictions']
    rename = parameters['rename']
    documenttype = parameters['documenttype']
    iconsizes = parameters['iconsize'].split(',')
    paths_and_doctypes = parameters['paths_and_doctypes']

    ## Create an instance of BibRecDocs for the current recid(sysno)
    bibrecdocs = BibRecDocs(sysno)

    paths_and_suffixes = get_dictionary_from_string(paths_and_suffixes)

    paths_and_restrictions = get_dictionary_from_string(paths_and_restrictions)

    paths_and_doctypes = get_dictionary_from_string(paths_and_doctypes)

    ## Go through all the directories specified in the keys
    ## of parameters['paths_and_suffixes']
    for path in paths_and_suffixes.keys():
        ## Check if there is a directory for the current path
        if os.path.exists("%s/files/%s" % (curdir, path)):
            ## Retrieve the restriction to apply to files in this
            ## directory
            restriction = paths_and_restrictions.get(path, '')
            restriction = re.sub('<PA>(?P<content>[^<]*)</PA>',
                                 get_pa_tag_content,
                                 restriction)

            ## Go through all the files in curdir/files/path
            for current_file in os.listdir("%s/files/%s" % (curdir, path)):
                ## retrieve filename and extension
                dummy, filename, extension = decompose_file(current_file)
                if extension and extension[0] != ".":
                    extension = '.' + extension
                if len(paths_and_suffixes[path]) != 0:
                    extension = "_%s%s" % (paths_and_suffixes[path], extension)
                ## Build the new file name if rename parameter has been given
                if rename:
                    filename = re.sub('<PA>(?P<content>[^<]*)</PA>', \
                                      get_pa_tag_content, \
                                      parameters['rename'])

                if rename or len(paths_and_suffixes[path]) != 0 :
                    ## Rename the file
                    try:
                        # Write the log rename_cmd
                        fd = open("%s/rename_cmd" % curdir, "a+")
                        fd.write("%s/files/%s/%s" % (curdir, path, current_file) + " to " +\
                                  "%s/files/%s/%s%s" % (curdir, path, filename, extension) + "\n\n")
                        ## Rename
                        os.rename("%s/files/%s/%s" % (curdir, path, current_file), \
                                  "%s/files/%s/%s%s" % (curdir, path, filename, extension))

                        fd.close()
                        ## Save the new name in a text file in curdir so that
                        ## the new filename can be used by templates to created the recmysl
                        fd = open("%s/%s_RENAMED" % (curdir, path), "w")
                        fd.write("%s%s" % (filename, extension))
                        fd.close()
                    except OSError as err:
                        msg = "Cannot rename the file.[%s]"
                        msg %= str(err)
                        raise InvenioWebSubmitFunctionWarning(msg)
                fullpath = "%s/files/%s/%s%s" % (curdir, path, filename, extension)
                ## Check if there is any existing similar file
                if not bibrecdocs.check_file_exists(fullpath, extension):
                    bibdoc = bibrecdocs.add_new_file(fullpath, doctype=paths_and_doctypes.get(path, path), never_fail=True)
                    bibdoc.set_status(restriction)
                    ## Fulltext
                    if documenttype == "fulltext":
                        additionalformats = createRelatedFormats(fullpath)
                        if len(additionalformats) > 0:
                            for additionalformat in additionalformats:
                                try:
                                    bibrecdocs.add_new_format(additionalformat)
                                except InvenioBibDocFileError:
                                    pass
                    ## Icon
                    elif documenttype == "picture":
                        has_added_default_icon_subformat_p = False
                        for iconsize in iconsizes:
                            try:
                                iconpath, iconname = create_icon({
                                    'input-file' : fullpath,
                                    'icon-scale' : iconsize,
                                    'icon-name' : None,
                                    'icon-file-format' : None,
                                    'multipage-icon' : False,
                                    'multipage-icon-delay' : 100,
                                    'verbosity' : 0,
                                })
                            except Exception as e:
                                register_exception(prefix='Impossible to create icon for %s (record %s)' % (fullpath, sysno), alert_admin=True)
                                continue
                            iconpath = os.path.join(iconpath, iconname)
                            docname = decompose_file(fullpath)[1]
                            try:
                                mybibdoc = bibrecdocs.get_bibdoc(docname)
                            except InvenioBibDocFileError:
                                mybibdoc = None
                            if iconpath is not None and mybibdoc is not None:
                                try:
                                    icon_suffix = iconsize.replace('>', '').replace('<', '').replace('^', '').replace('!', '')
                                    if not has_added_default_icon_subformat_p:
                                        mybibdoc.add_icon(iconpath)
                                        has_added_default_icon_subformat_p = True
                                    else:
                                        mybibdoc.add_icon(iconpath, subformat=CFG_BIBDOCFILE_DEFAULT_ICON_SUBFORMAT + "-" + icon_suffix)
                                    ## Save the new icon filename in a text file in curdir so that
                                    ## it can be used by templates to created the recmysl
                                    try:
                                        if not has_added_default_icon_subformat_p:
                                            fd = open("%s/%s_ICON" % (curdir, path), "w")
                                        else:
                                            fd = open("%s/%s_ICON_%s" % (curdir, path, iconsize + '_' + icon_suffix), "w")
                                        fd.write(os.path.basename(iconpath))
                                        fd.close()
                                    except OSError as err:
                                        msg = "Cannot store icon filename.[%s]"
                                        msg %= str(err)
                                        raise InvenioWebSubmitFunctionWarning(msg)
                                except InvenioBibDocFileError as e:
                                    # Most probably icon already existed.
                                    pass
                            elif mybibdoc is not None:
                                mybibdoc.delete_icon()

    # Update the MARC
    bibdocfile_bin = os.path.join(CFG_BINDIR, 'bibdocfile --yes-i-know')
    run_shell_command(bibdocfile_bin + " --fix-marc --recid=%s", (str(sysno),))

    # Delete the HB BibFormat cache in the DB, so that the fulltext
    # links do not point to possible dead files
    run_sql("DELETE LOW_PRIORITY from bibfmt WHERE format='HB' AND id_bibrec=%s", (sysno,))

    return ""

def get_pa_tag_content(pa_content):
    """Get content for <PA>XXX</PA>.
    @param pa_content: MatchObject for <PA>(.*)</PA>.
    return: the content of the file possibly filtered by an regular expression
    if pa_content=file[re]:a_file => first line of file a_file matching re
    if pa_content=file*p[re]:a_file => all lines of file a_file, matching re,
    separated by - (dash) char.
    """
    pa_content = pa_content.groupdict()['content']
    sep = '-'
    out = ''
    if pa_content.startswith('file'):
        filename = ""
        regexp = ""
        if "[" in pa_content:
            split_index_start = pa_content.find("[")
            split_index_stop =  pa_content.rfind("]")
            regexp = pa_content[split_index_start+1:split_index_stop]
            filename = pa_content[split_index_stop+2:]## ]:
        else :
            filename = pa_content.split(":")[1]
        if os.path.exists(os.path.join(curdir, filename)):
            fp = open(os.path.join(curdir, filename), 'r')
            if pa_content[:5] == "file*":
                out = sep.join(map(lambda x: re.split(regexp, x.strip())[-1], fp.readlines()))
            else:
                out = re.split(regexp, fp.readline().strip())[-1]
            fp.close()
    return out

