# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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

"""Implement Celery tasks for generating previews."""

import os

from flask import current_app, safe_join

from invenio.base.globals import cfg

from invenio.celery import celery
from invenio.utils.shell import run_shell_command  # FIXME: subprocess.Popen

from .utils import get_pdf_path


@celery.task
def generate_preview(f):
    """Generate PNG previews of PDF pages."""
    directory = os.path.join(current_app.instance_path, "previews")
    try:
        os.mkdir(directory)
    except OSError:  # directory already exists as per docs
        pass

    directory = os.path.join(directory, str(f.get_recid()))
    try:
        os.mkdir(directory)
    except OSError:  # directory already exists as per docs, preview exists
        return directory

    cmd_pdftk = "pdftk %s burst output %s/pg_%s.pdf"
    (exit_status, output_std, output_err) = \
        run_shell_command(cmd_pdftk, args=(get_pdf_path(f), directory, '%d'))
    cmd_pdftk = '%s -flatten -density 300 %s %s/`basename %s .pdf`.png'
    for fl in os.listdir(directory):
        if fl.endswith(".pdf"):
            fn = safe_join(directory, fl)
            (exit_status, output_std, output_err) = \
                run_shell_command(cmd_pdftk, args=(
                    str(cfg["CFG_PATH_CONVERT"]), fn, directory,
                    fn))
