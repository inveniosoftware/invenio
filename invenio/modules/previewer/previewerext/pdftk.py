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

"""Implemenent PDFTk previewer plugin."""

from flask import abort, current_app, jsonify, request, safe_join

from invenio.base.globals import cfg
from invenio.utils.shell import run_shell_command  # FIXME: subprocess.Popen

from ..tasks import generate_preview
from ..utils import get_pdf_path


def can_preview(f):
    """Return True for PDFs, False for others."""
    if f.superformat == ".pdf":
        return True
    return False


def preview(f):
    """Generate preview for a file."""
    generate_preview(f)  # FIXME: call as Celery task at record upload time?
    return send_pdf_image_data(current_app.instance_path + "/previews/" +
                               str(f.get_recid()))


def send_pdf_image_data(directory):
    """Send encoded raw PNG preview of a PDF page."""
    try:
        raw_file = open(safe_join(directory, "pg_" +
                                  request.args.get("page", default="1",
                                                   type=str) +
                                  ".png"), "r")
        # FIXME: use Documents to store previews
        import base64
        return base64.b64encode(raw_file.read())
    except IOError:
        current_app.logger.exception("PDF page not found")
        abort(404)


def maxpage(f):
    """Return number of pages for PDF records via AJAX."""
    cmd_pdftk = "%s %s dump_data output | grep NumberOfPages"
    pdf = get_pdf_path(f)
    if pdf is not None:
        (exit_status, output_std, output_err) = \
            run_shell_command(cmd_pdftk, args=(str(cfg["CFG_PATH_PDFTK"]), pdf))
        if int(exit_status) == 0 and len(output_err) == 0:
            return jsonify(maxpage=int(output_std.strip().split(" ")[1]))
    return jsonify(maxpage=-1)
