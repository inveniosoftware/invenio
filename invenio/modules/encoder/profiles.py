# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011 CERN.
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

""" BibEncode profile submodule """

import os
import shutil

from invenio.utils.json import json_decode_file
from invenio.modules.encoder.config import (
                                      CFG_BIBENCODE_PROFILES_ENCODING,
                                      CFG_BIBENCODE_PROFILES_EXTRACT,
                                      CFG_BIBENCODE_PROFILES_ENCODING_LOCAL,
                                      CFG_BIBENCODE_PROFILES_EXTRACT_LOCAL
                                      )
from invenio.modules.encoder.utils import getval
from invenio.ext.logging import register_exception

#-------------------#
# Encoding profiles #
#-------------------#

def get_encoding_profiles():
    """ Returns a dictionary representation of the encoding profiles
    """
    if not os.path.exists(CFG_BIBENCODE_PROFILES_ENCODING_LOCAL):
        shutil.copy(CFG_BIBENCODE_PROFILES_ENCODING, CFG_BIBENCODE_PROFILES_ENCODING_LOCAL)
    default_profiles = json_decode_file(CFG_BIBENCODE_PROFILES_ENCODING)
    local_profiles = json_decode_file(CFG_BIBENCODE_PROFILES_ENCODING_LOCAL)
    default_profiles.update(local_profiles)
    return default_profiles

def get_encoding_profile(key):
    """ Returns a dictionary representation of an encoding profile by key
    """
    profile = get_encoding_profiles()[key]

    def san_bitrate(bitrate):
        """ Sanitizes bitrates
        """
        if type(str()) == type(bitrate):
            if bitrate.endswith('k'):
                try:
                    bitrate = int(bitrate[:-1])
                    bitrate *= 1000
                    return int(bitrate)
                except ValueError:
                    register_exception(alert_admin=True)
                    raise
        elif type(int) == type(bitrate):
            return bitrate
        else:
            register_exception(alert_admin=True)
            raise

    if getval(profile, 'videobitrate'):
        profile['videobitrate'] = san_bitrate(getval(profile, 'videobitrate'))

    if getval(profile, 'audiobitrate'):
        profile['audiobitrate'] = san_bitrate(getval(profile, 'audiobitrate'))

    return profile

#---------------------#
# Extraction profiles #
#---------------------#

def get_extract_profiles():
    """ Returns a dictionary representation of the frame extraction profiles
    """
    if not os.path.exists(CFG_BIBENCODE_PROFILES_EXTRACT_LOCAL):
        shutil.copy(CFG_BIBENCODE_PROFILES_EXTRACT, CFG_BIBENCODE_PROFILES_EXTRACT_LOCAL)
    default_profiles = json_decode_file(CFG_BIBENCODE_PROFILES_EXTRACT)
    local_profiles = json_decode_file(CFG_BIBENCODE_PROFILES_EXTRACT_LOCAL)
    default_profiles.update(local_profiles)
    return default_profiles

def get_extract_profile(key):
    """ Returns a dictionary representation of an extrtaction profile by key
    """
    return get_extract_profiles()[key]

