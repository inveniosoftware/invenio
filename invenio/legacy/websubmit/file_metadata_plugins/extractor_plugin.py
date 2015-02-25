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
WebSubmit Metadata Plugin - This is the generic metadata extraction
plugin. Contains methods to extract metadata from many kinds of files.

Dependencies: extractor
"""

__plugin_version__ = "WebSubmit File Metadata Plugin API 1.0"

import extractor
from invenio.legacy.bibdocfile.api import decompose_file

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
    return ext.lower() in ['.html', '.doc', '.ps', '.xls', '.ppt',
                           '.ps', '.sxw', '.sdw', '.dvi', '.man', '.flac',
                           '.mp3', '.nsf', '.sid', '.ogg', '.wav', '.png',
                           '.deb', '.rpm', '.tar.gz', '.zip', '.elf',
                           '.s3m', '.xm', '.it', '.flv', '.real', '.avi',
                           '.mpeg', '.qt', '.asf']

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
    # Initialization dict
    meta_info = {}

    # Extraction
    xtract = extractor.Extractor()

    # Get the keywords
    keys = xtract.extract(inputfile)

    # Loop to dump data to the dict
    for keyword_type, keyword in keys:
        meta_info[keyword_type.encode('iso-8859-1')] = \
            keyword.encode('iso-8859-1')

    # Return the dictionary
    return meta_info
