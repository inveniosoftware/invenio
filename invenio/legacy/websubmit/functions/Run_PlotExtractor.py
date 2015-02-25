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

"""WebSubmit function - Run PlotExtractor on given record."""

import os
from invenio.config import CFG_BINDIR
from invenio.utils.shell import run_shell_command
from invenio.legacy.websubmit.functions.Shared_Functions import ParamFromFile

def Run_PlotExtractor(parameters, curdir, form, user_info=None):
    """
    Run the plot extraction on the current record.

    The record ID (sysno) must be defined and known already, and the
    files attached already (so the function must be run after
    'Move_Uploaded_Files_To_Storage' & co., not after a FFT that could
    be scheduled later).

    @param parameters:(dictionary) - contains:

      + with_docname: run plot extraction only on files matching this
                    docname only. If the value starts with "file:", read
                    the docname value from the specified file.

      + with_doctype: run plot extraction only on files matching this
                    doctype only. If the value starts with "file:", read
                    the doctype value from the specified file.

      + with_docformat: run plot extraction only on files matching this
                      format only. If the value starts with "file:", read
                      the doctype value from the specified file.

      + extract_plots_switch_file: run plot extraction only if the filename
                                  exists in curdir. Typically one would set
                                  'files' to extract plots only if some files
                                  have been uploaded.

    If none of the with_* parameters is provided, the current plot
    extractor behaviour will not lead to extracting the plots from all
    the files, but will fall back on 'arXiv' source extraction (see
    plotextractor for details).

    """
    global sysno

    extract_plots_switch_file = parameters["extract_plots_switch_file"]
    if extract_plots_switch_file and \
           not os.path.exists(os.path.join(curdir, extract_plots_switch_file)):
        return ""

    if sysno:
        cmd = os.path.join(CFG_BINDIR, 'plotextractor') + ' -u --upload-mode=correct -r %s --yes-i-know'
        arguments = [str(sysno),]

        if parameters["with_docname"]:
            with_docname = parameters["with_docname"]
            if with_docname.startswith('file:'):
                with_docname = ParamFromFile(os.path.join(curdir, with_docname[5:]))
            cmd += ' --with-docname=%s'
            arguments.append(with_docname)

        if parameters["with_doctype"]:
            with_doctype = parameters["with_doctype"]
            if with_doctype.startswith('file:'):
                with_doctype = ParamFromFile(os.path.join(curdir, with_doctype[5:]))
            cmd += ' --with-doctype=%s'
            arguments.append(with_doctype)

        if parameters["with_docformat"]:
            with_docformat = parameters["with_docformat"]
            if with_docformat.startswith('file:'):
                with_docformat = ParamFromFile(os.path.join(curdir, with_docformat[5:]))
            cmd += ' --with-docformat=%s'
            arguments.append(with_docformat)

        cmd += ' &'
        run_shell_command(cmd, args=arguments)

    return ""
