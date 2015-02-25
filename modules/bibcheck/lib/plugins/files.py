# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013 CERN.
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

""" Plugin to validate the checksum of a record's files """

from invenio.legacy.bibdocfile.api import BibRecDocs
import os

try:
    import magic
    if hasattr(magic, "from_file"):
        HAS_MAGIC = 1
    else:
        HAS_MAGIC = 2
        magic_object = magic.open(magic.MAGIC_MIME_TYPE)
        magic_object.load()
except ImportError:
    HAS_MAGIC = 0

def check_record(record):
    """
    Validates the checksum of all the BibDocFile's in the record
    """
    record_id = record["001"][0][3]
    docs = BibRecDocs(record_id).list_bibdocs()
    for doc in docs:
        for bibfile in doc.list_latest_files():
            if not os.path.exists(bibfile.fullpath):
                record.set_invalid("File doesn't exists %s" % bibfile.fullpath)
                continue

            if not bibfile.check():
                record.set_invalid("Invalid checksum for file %s" % bibfile.fullpath)


            if HAS_MAGIC:
                if HAS_MAGIC == 1:
                    magic_mime = magic.from_file(bibfile.fullpath, mime=True)
                else:
                    magic_mime = magic_object.file(bibfile.fullpath)

                if bibfile.mime != magic_mime:
                    record.set_invalid(
                        ("Guessed mime type from extension (%s) is different" +
                         "from guessed mime type from headers (%s)") %
                        (bibfile.mime, magic_mime)
                    )


