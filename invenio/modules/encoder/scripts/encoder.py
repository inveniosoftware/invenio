# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2013 CERN.
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
Bibencode: Encode a given video and profile using FFmpeg.

    Usage: bibencode -i INPUT -p PROFILE
    Examples:
      $ bibencode -i myvideo.mov -p THEORA_480P

    Options:
     -i, --input             the file that will be transcoded
     -p, --profile           the profile that will be used for transcoding

    General options:
     -h, --help              print this help and exit
     -v, --verbose=LEVEL     verbose level (from 0 to 9, default 1)
     -V  --version           print the script version
"""

from invenio.base.factory import with_app_context


@with_app_context()
def main():
    from invenio.modules.encoder.tasks import main as encoder_main
    return encoder_main()
