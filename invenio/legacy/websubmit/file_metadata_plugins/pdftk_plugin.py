# This file is part of Invenio.
# Copyright (C) 2010, 2011 CERN.
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
WebSubmit Metadata Plugin - This is the plugin to update metadata from
PDF files.

from __future__ import print_function

Dependencies: pdftk
"""

__plugin_version__ = "WebSubmit File Metadata Plugin API 1.0"

import os
import shutil
import tempfile
from invenio.utils.shell import run_shell_command
from invenio.legacy.bibdocfile.api import decompose_file
from invenio.config import CFG_PATH_PDFTK, CFG_TMPDIR
from invenio.legacy.websubmit.config import InvenioWebSubmitFileMetadataRuntimeError

if not CFG_PATH_PDFTK:
    raise ImportError, "Path to PDFTK is not set in CFG_PATH_PDFTK"

def can_read_local(inputfile):
    """
    Checks if inputfile is among metadata-readable file types

    @param inputfile: path to the image
    @type inputfile: string
    @rtype: boolean
    @return: True if file can be processed
    """

    # Check file type (0 base, 1 name, 2 ext)
    ext = decompose_file(inputfile)[2]
    return ext.lower() in ['.pdf']

def can_write_local(inputfile):
    """
    Checks if inputfile is among metadata-writable file types (pdf)

    @param inputfile: path to the image
    @type inputfile: string
    @rtype: boolean
    @return: True if file can be processed
    """
    ext = os.path.splitext(inputfile)[1]
    return ext.lower() in ['.pdf']

def read_metadata_local(inputfile, verbose):
    """
    Metadata extraction from many kind of files

    @param inputfile: path to the image
    @type inputfile: string
    @param verbose: verbosity
    @type verbose: int
    @rtype: dict
    @return: dictionary with metadata
    """
    cmd = CFG_PATH_PDFTK + ' %s dump_data'
    (exit_status, output_std, output_err) = \
                      run_shell_command(cmd, args=(inputfile,))
    metadata_dict = {}
    key = None
    value = None
    for metadata_line in output_std.splitlines():
        if metadata_line.strip().startswith("InfoKey"):
            key = metadata_line.split(':', 1)[1].strip()
        elif metadata_line.strip().startswith("InfoValue"):
            value = metadata_line.split(':', 1)[1].strip()
            if key in ["ModDate", "CreationDate"]:
                # FIXME: Interpret these dates?
                try:
                    pass
                    #value = datetime.strptime(value, "D:%Y%m%d%H%M%S%Z")
                except:
                    pass
            if key:
                metadata_dict[key] = value
                key = None
        else:
            try:
                custom_key, custom_value = metadata_line.split(':', 1)
                metadata_dict[custom_key.strip()] = custom_value.strip()
            except:
                # Most probably not relevant line
                pass

    return metadata_dict

def write_metadata_local(inputfile, outputfile, metadata_dictionary, verbose):
    """
    Metadata write method, takes the .pdf as input and creates a new
    one with the new info.

    @param inputfile: path to the pdf
    @type inputfile: string
    @param outputfile: path to the resulting pdf
    @type outputfile: string
    @param verbose: verbosity
    @type verbose: int
    @param metadata_dictionary: metadata information to update inputfile
    @type metadata_dictionary: dict
    """
    # Take the file name (0 base, 1 name, 2 ext)
    filename = decompose_file(inputfile)[1]

    # Print pdf metadata
    if verbose > 1:
        print('Metadata information in the PDF file ' + filename + ': \n')
        try:
            os.system(CFG_PATH_PDFTK + ' ' + inputfile + ' dump_data')
        except Exception:
            print('Problem with inputfile to PDFTK')

    # Info file for pdftk
    (fd, path_to_info) = tempfile.mkstemp(prefix="wsm_pdf_plugin_info_", \
                                             dir=CFG_TMPDIR)
    os.close(fd)
    file_in = open(path_to_info, 'w')
    if verbose > 5:
        print("Saving PDFTK info file to %s" % path_to_info)

    # User interaction to form the info file
    # Main Case: Dictionary received through option -d
    if not metadata_dictionary == {}:
        for tag in metadata_dictionary:
            line = 'InfoKey: ' + tag + '\nInfoValue: ' + \
                   metadata_dictionary[tag] + '\n'
            if verbose > 0:
                print(line)
            file_in.writelines(line)
    else:
        data_modified = False
        user_input = 'user_input'
        print("Entering interactive mode. Choose what you want to do:")
        while (user_input):
            if not data_modified:
                try:
                    user_input = raw_input('[w]rite / [q]uit\n')
                except:
                    print("Aborting")
                    return
            else:
                try:
                    user_input = raw_input('[w]rite / [q]uit and apply / [a]bort \n')
                except:
                    print("Aborting")
                    return
            if user_input == 'q':
                if not data_modified:
                    return
                break
            elif user_input == 'w':
                try:
                    tag = raw_input('Tag to update:\n')
                    value = raw_input('With value:\n')
                except:
                    print("Aborting")
                    return
                # Write to info file
                line = 'InfoKey: ' + tag + '\nInfoValue: ' + value + '\n'
                data_modified = True
                file_in.writelines(line)
            elif user_input == 'a':
                return
            else:
                print("Invalid option: ")
    file_in.close()

    (fd, pdf_temp_path) = tempfile.mkstemp(prefix="wsm_pdf_plugin_pdf_", \
                                              dir=CFG_TMPDIR)
    os.close(fd)

    # Now we call pdftk tool to update the info on a pdf
    #try:
    cmd_pdftk = '%s %s update_info %s output %s'
    (exit_status, output_std, output_err) = \
                  run_shell_command(cmd_pdftk,
                                    args=(CFG_PATH_PDFTK, inputfile,
                                          path_to_info, pdf_temp_path))
    if verbose > 5:
        print(output_std, output_err)

    if os.path.exists(pdf_temp_path):
        # Move to final destination if exist
        try:
            shutil.move(pdf_temp_path, outputfile)
        except Exception as err:
            raise InvenioWebSubmitFileMetadataRuntimeError("Could not move %s to %s" % \
                                                           (pdf_temp_path, outputfile))
    else:
        # Something bad happened
        raise InvenioWebSubmitFileMetadataRuntimeError("Could not update metadata " + output_err)
