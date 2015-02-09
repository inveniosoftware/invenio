# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2015 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Module provides helper functions for communities views."""

import os

from invenio.base.globals import cfg


def save_and_validate_logo(logo, filename, prev_ext=None):
    """Validate if communities logo is in limit size and save it."""
    base_path = os.path.join(cfg['COLLECT_STATIC_ROOT'], 'user')
    ext = os.path.splitext(logo.filename)[1]
    new_logo_path = os.path.join(base_path, filename + ext)
    prev_logo_path = None
    backup = None
    CHUNK = 250 * 1024  # 250KB
    CHUNKS_AMOUNT = 6  # 6 * 250KB = 1.5MB

    if ext in cfg['COMMUNITIES_LOGO_EXTENSIONS']:

        if not os.path.exists(base_path):
            os.mkdir(base_path, 0755)

        if prev_ext:
            prev_logo_path = os.path.join(base_path, filename + prev_ext)
            if os.path.exists(prev_logo_path):
                with open(prev_logo_path, 'rb') as fp:
                    backup = fp.read()

        with open(new_logo_path, 'wb') as fp:
            for i in range(CHUNKS_AMOUNT):
                chunk = logo.stream.read(CHUNK)
                if not chunk:
                    break
                fp.write(chunk)
        if logo.stream.read(CHUNK):
            # File size exceeded
            os.remove(new_logo_path)
            if backup and prev_logo_path:
                with open(prev_logo_path, 'wb') as fp:
                        fp.write(backup)
            return None
        else:
            # Success
            if prev_ext != ext and backup:
                os.remove(prev_logo_path)
            return ext
    else:
        return None
