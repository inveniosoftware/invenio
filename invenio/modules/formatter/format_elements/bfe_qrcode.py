# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2014 CERN.
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

"""BibFormat element - QR code generator """

from invenio.config import CFG_SITE_SECURE_URL, CFG_WEBDIR, CFG_SITE_RECORD
from invenio.utils.hash import md5
import os
try:
    import qrcode
    from PIL import Image
    HAS_QR = True
except ImportError:
    HAS_QR = False

if not HAS_QR:
    from warnings import warn
    warn("Please install qrcode <https://pypi.python.org/pypi/qrcode> and "
         "Pillow (Python Imaging Library) "
         "<https://pypi.python.org/pypi/Pillow/>.")


def _get_record_hash(link):
    """
    Generate a record hash including CFG_SITE_URL so that
    if CFG_SITE_URL is updated, the QR-code image is invalidated.
    """
    return md5(link).hexdigest()[:8].lower()


def format_element(bfo, width="100"):
    """
    Generate a QR-code image linking to the current record.

    @param width: Width of QR-code image.
    """
    if not HAS_QR:
        return ""

    width = int(width)

    bibrec_id = bfo.control_field("001")
    link = "%s/%s/%s" % (CFG_SITE_SECURE_URL, CFG_SITE_RECORD, bibrec_id)
    hash_val = _get_record_hash(link)

    filename = "%s_%s.png" % (bibrec_id, hash_val)
    filename_url = "/img/qrcodes/%s" % filename
    filename_path = os.path.join(CFG_WEBDIR, "img/qrcodes/%s" % filename)

    if not os.path.exists(filename_path):
        if not os.path.exists(os.path.dirname(filename_path)):
            os.makedirs(os.path.dirname(filename_path))

        img = qrcode.make(link)
        img._img = img._img.convert("RGBA")
        img._img = img._img.resize((width, width), Image.ANTIALIAS)
        img.save(filename_path, "PNG")

    return """<img src="%s" width="%s" />""" % (filename_url, width)


def escape_values(dummy_bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
