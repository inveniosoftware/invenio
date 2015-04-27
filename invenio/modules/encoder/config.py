# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2015 CERN.
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

"""Bibencode configuration submodule."""

from __future__ import unicode_literals

import invenio.config

import pkg_resources

import re

from six import iteritems

__revision__ = "$Id$"

# -----------------------#
# General Configuration  #
# -----------------------#

# The command for probing with FFMPEG
CFG_BIBENCODE_FFMPEG_PROBE_COMMAND = invenio.config.CFG_PATH_FFPROBE + \
    " %s -loglevel verbose -show_format -show_streams"

# The command for probing with MEDIAINFO
CFG_BIBENCODE_MEDIAINFO_COMMAND = invenio.config.CFG_PATH_MEDIAINFO + \
    " %s -f --Output=XML"

# Image extraction base command
CFG_BIBENCODE_FFMPEG_EXTRACT_COMMAND = invenio.config.CFG_PATH_FFMPEG + \
    " -ss %.2f -i %s -r 1 -vframes 1 -f image2 -s %s %s"

# Commands for multipass encoding
# In the first pass, you can dump the output to /dev/null and ignore audio
# CFG_BIBENCODE_FFMPEG_COMMAND_PASS_1 = "ffmpeg -i %s -y -loglevel verbose
# -vcodec %s -pass 1 -passlogfile %s -an -f rawvideo -b %s -s %s %s /dev/null"
# CFG_BIBENCODE_FFMPEG_COMMAND_PASS_2 = "ffmpeg -i %s -y -loglevel verbose
# -vcodec %s -pass 2 -passlogfile %s -acodec %s -b %s -ab %s -s %s %s %s"
CFG_BIBENCODE_FFMPEG_PASSLOGFILE_PREFIX = invenio.config.CFG_LOGDIR + \
    "/bibencode2pass-%s-%s"

# Path to the encoding logfiles
# Filenames will later be substituted with process specific information
CFG_BIBENCODE_FFMPEG_ENCODING_LOG = invenio.config.CFG_LOGDIR + \
    "/bibencode_%s.log"

# Path to probing logiles
CFG_BIBENCODE_FFMPEG_PROBE_LOG = invenio.config.CFG_LOGDIR + \
    "/bibencode_probe_%s.log"

# The pattern for the encoding status specific string in the FFmpeg output
CFG_BIBENCODE_FFMPEG_ENCODE_TIME = re.compile(
    "^.+time=(\d\d:\d\d:\d\d.\d\d).+$")

# The pattern for the configuration string with information about compiling
# options
CFD_BIBENCODE_FFMPEG_OUT_RE_CONFIGURATION = re.compile(
    "(--enable-[a-z0-9\-]*)")

# The minimum ffmpeg compile options for BibEncode to work correctly
CFG_BIBENCODE_FFMPEG_CONFIGURATION_REQUIRED = (
    '--enable-gpl',
    '--enable-version3',
    '--enable-nonfree',
    '--enable-libfaac',
    # '--enable-libfdk-aac',
    '--enable-libtheora',
    '--enable-libvorbis',
    '--enable-libvpx',
    '--enable-libx264',
    # '--enable-funky'
)

# Path to the directory for transcoded files
CFG_BIBENCODE_TARGET_DIRECTORY = invenio.config.CFG_TMPDIR + "/"

# ------------------------#
# Metadata Configuration  #
# ------------------------#

# Template for key-value pairs that can be used with FFMPEG to set metadata.
# Not all keys are represented in every video container format.
# FFMPEG will try to write any given key-value pairs. If the container
# format does not support some pairs there wont be an error.
# You might like to verify that the attributes were really written
# by using FFPROBE.

# The FFMPEG argument structure is:
# -metadata key1="value1" -metadata key2="value2 ...
CFG_BIBENCODE_FFMPEG_METADATA_TEMPLATE = {
    'title': None,
    'author': None,
    'album_artist': None,
    'album': None,
    'grouping': None,
    'composer': None,
    'year': None,
    'track': None,
    'comment': None,
    'genre': None,
    'copyright': None,
    'description': None,
    'synopsis': None,
    'show': None,
    'episode_id': None,
    "network": None,
    'lyrics': None
}

#  Duration: 00:02:28.58, start: 0.000000, bitrate: 9439 kb/s
#                   timcode       start?              bitrate
CFG_BIBENCODE_FFMPEG_RE_VIDEOINFO_DURATION = re.compile(
    "^\s*Duration: (.*?), start: (\d+\.\d+), bitrate: (\d+?) kb\/s$")

#    Stream #0.0(eng): Video: h264 (Main), yuv420p, 1920x1056, 9338 kb/s, 23.98
#    fps, 23.98 tbr, 2997 tbn, 5994 tbc
#    Stream #0.1(eng): Video: wmv3, yuv420p, 1440x1080, 9500 kb/s, 25 tbr, 1k
#    tbn, 1k tbc
#                  number     language           codec
#    color   resolution  bitrate    fps       tbr       tbn      tbc
CFG_BIBENCODE_FFMPEG_RE_VIDEOINFO_VSTREAM = re.compile(
    "^\s*Stream #(\d+.\d+)\(?(\w+)?\)?: Video: ([a-zA-Z0-9\(\) ]*), "
    "(\w+), (\d+x\d+), (\d+) kb\/s, (.+) fps, (.+) tbr, (.+) tbn, (.+) tbc$")

#    Stream #0.0(eng): Audio: wmav2, 44100 Hz, 2 channels, s16, 320 kb/s
#    Stream #0.1(eng): Audio: aac, 44100 Hz, stereo, s16, 97 kb/s
#    number    language         codec              samplerate
#    channels      bit-depth   bitrate
CFG_BIBENCODE_FFMPEG_RE_VIDEOINFO_ASTREAM = re.compile(
    "^\s*Stream #(\d+.\d+)\(?(\w+)?\)?: Audio: ([a-zA-Z0-9\(\) ]*), "
    "(\d+) Hz, ([a-zA-Z0-9 ]+), (\w+), (\d+) kb\/s$")

# FFMPEG command for setting metadata
# This will create a copy of the master and write the metadata there
CFG_BIBENCODE_FFMPEG_METADATA_SET_COMMAND = "ffmpeg -y -i %s " + \
    "-acodec copy -vcodec copy %s"

# FFMPEG metadata argument template
# had to remove '-metadata ' in front because of issues with command splitting
CFG_BIBENCODE_FFMPEG_METADATA_ARGUMENT = "%s=\"%s\""

# File containing mappings from ffprobe and mediainfo to pbcore
CFG_BIBENCODE_PBCORE_MAPPINGS = pkg_resources.resource_filename(
    'invenio.modules.encoder', 'pbcore_mappings.json')

# XSLT Template from PBCORE to MARCXML
CFG_BIBENCODE_PBCORE_MARC_XSLT = pkg_resources.resource_filename(
    'invenio.modules.encoder', 'pbcore_to_marc_nons.xsl')

CFG_BIBENCODE_ASPECT_RATIO_MARC_FIELD = "951__x"


# Metadata Patterns for parsing
def create_metadata_re_dict():
    """Create a dictionary with Regex patterns.

    Creates a dictionary with Regex patterns from the metadata template
    dictionary.
    """
    metadata_re_dictionary = {}
    for key, value in iteritems(CFG_BIBENCODE_FFMPEG_METADATA_TEMPLATE):
        metadata_re_dictionary[key] = re.compile(
            "^\s*%s\s*:\s(((\S*)\s*(\S*))*)$" % key)
    return metadata_re_dictionary
CFG_BIBENCODE_FFMPEG_METADATA_RE_DICT = create_metadata_re_dict()

# ---------------------#
# Parameter Validation #
# ---------------------#

CFG_BIBENCODE_VALID_MODES = ['encode', 'extract', 'meta', 'batch',
                             'daemon', 'cdsmedia']

CFG_BIBENCODE_FFMPEG_VALID_SIZES = [
    'sqcif', 'qcif', 'cif', '4cif', '16cif', 'qqvga', 'qvga', 'vga', 'svga',
    'xga', 'uxga', 'qxga', 'sxga', 'qsxga', 'hsxga', 'wvga', 'wxga', 'wsxga',
    'wuxga', 'woxga', 'wqsxga', 'wquxga', 'whsxga', 'cga', 'ega',
    'hd480', 'hd720', 'hd1080'
    ]

CFG_BIBENCODE_RESOLUTIONS = {
    "ntsc": "720x480",
    "pal": "720x576",
    "qntsc": "352x240",
    "qpal": "352x288",
    "sntsc": "640x480",
    "spal": "768x576",
    "film": "352x240",
    "ntsc-film": "352x240",
    "sqcif": "128x96",
    "qcif": "176x144",
    "cif": "352x288",
    "4cif": "704x576",
    "16cif": "1408x1152",
    "qqvga": "160x120",
    "qvga": "320x240",
    "vga": "640x480",
    "svga": "800x600",
    "xga": "1024x768",
    "uxga": "1600x1200",
    "qxga": "2048x1536",
    "sxga": "1280x1024",
    "qsxga": "2560x2048",
    "hsxga": "5120x4096",
    "wvga": "852x480",
    "wxga": "1366x768",
    "wsxga": "1600x1024",
    "wuxga": "1920x1200",
    "woxga": "2560x1600",
    "wqsxga": "3200x2048",
    "wquxga": "3840x2400",
    "whsxga": "6400x4096",
    "whuxga": "7680x4800",
    "cga": "320x200",
    "ega": "640x350",
    "hd480": "852x480",
    "hd720": "1280x720",
    "hd1080": "1920x1080"
}

CFG_BIBENCODE_FFMPEG_RE_VALID_SIZE = re.compile("^\d+x\d+$")

CFG_BIBENCODE_FFMPEG_VALID_VCODECS = [
    'libx264', 'libvpx', 'libtheora', 'mpeg4', 'wmv2', 'wmv1', 'flv'
    ]

CFG_BIBENCODE_FFMPEG_VALID_ACODECS = [
    'libmp3lame', 'libvorbis', 'wma1', 'wma2', 'libfaac'
    ]

# -----------------------#
# Profiles Configuration #
# -----------------------#

CFG_BIBENCODE_PROFILES_ENCODING = pkg_resources.resource_filename(
    'invenio.modules.encoder', 'encoding_profiles.json')
CFG_BIBENCODE_PROFILES_ENCODING_LOCAL = pkg_resources.resource_filename(
    'invenio.modules.encoder', 'encoding_profiles_local.json')
CFG_BIBENCODE_PROFILES_EXTRACT = pkg_resources.resource_filename(
    'invenio.modules.encoder', 'extract_profiles.json')
CFG_BIBENCODE_PROFILES_EXTRACT_LOCAL = pkg_resources.resource_filename(
    'invenio.modules.encoder', 'extract_profiles_local.json')
CFG_BIBENCODE_TEMPLATE_BATCH_SUBMISSION = pkg_resources.resource_filename(
    'invenio.modules.encoder', 'batch_template_submission.json')

# ---------------------#
# Daemon Configuration #
# ---------------------#

CFG_BIBENCODE_DAEMON_DIR_NEWJOBS = invenio.config.CFG_TMPSHAREDDIR + \
    '/bibencode/jobs'
CFG_BIBENCODE_DAEMON_DIR_OLDJOBS = invenio.config.CFG_TMPSHAREDDIR + \
    '/bibencode/jobs/done'

# ------------------#
# WebSubmit Support #
# ------------------#

CFG_BIBENCODE_WEBSUBMIT_ASPECT_SAMPLE_FNAME = 'aspect_sample_.jpg'
CFG_BIBENCODE_WEBSUBMIT_ASPECT_SAMPLE_DIR = 'aspect_samples'
