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

"""BibEncode helper functions.

Functions that are used throughout the BibEncode module

"""
import os
import subprocess
import unicodedata
import re
import six
import sys
import time
try:
    from uuid import uuid4
except ImportError:
    import random
    def uuid4():
        return "%x" % random.getrandbits(16*8)

from .config import (
                    CFG_BIBENCODE_FFMPEG_PROBE_LOG,
                    CFG_BIBENCODE_FFMPEG_PROBE_COMMAND,
                    CFD_BIBENCODE_FFMPEG_OUT_RE_CONFIGURATION,
                    CFG_BIBENCODE_FFMPEG_CONFIGURATION_REQUIRED,
                    CFG_BIBENCODE_MEDIAINFO_COMMAND
                    )
from invenio.config import CFG_PATH_FFPROBE

# The timestamp for the process. Used to identify Logfiles.
def generate_timestamp():
    """ Generates a timestamp for the logfile to make it unique
    """
    return "%s-%s" % (time.strftime("%Y%m%d%H%M%S", time.gmtime()), str(uuid4()))

# The following functions are for ffmpeg specific timecodes
# The format is HH:MM:SS.ss
def timecode_to_seconds(timecode):
    """ Converts a timecode to a total duration in seconds
    """
    if type(timecode) == type(str()):
        try:
            hours, minutes, seconds = timecode.split(':')
            total_seconds = int(hours)*3600+int(minutes)*60+float(seconds)
        except ValueError:
            raise ValueError(timecode + " is not a valid timecode, the format is hh:mm:ss.ss or hh:mm:ss")
    else:
        raise ValueError(timecode + " is not a valid timecode, the format is hh:mm:ss.ss or hh:mm:ss")
    return total_seconds

def seconds_to_timecode(total_seconds):
    """ Converts seconds to a timecode
    """
    ## Cast to float
    if (type(total_seconds) == type(int())
        or type(total_seconds) == type(float())
        or type(total_seconds) == type(str())
        ):
        try:
            total_seconds = float(total_seconds)
        except ValueError:
            ValueError("string must be of format '1.1' or '1'")
        hours = int(total_seconds / 3600)
        minutes = int(total_seconds / 60) - hours * 60
        seconds = total_seconds % 60
    else:
        raise TypeError("seconds must be given as integer or float or string values")
    return "%02d:%02d:%05.2f" % (hours, minutes, seconds)

def is_timecode(value):
    """ Checks if the given string is a timecode
    """
    if type(value) == type(str()) or type(value) == type(unicode()):
        pattern = re.compile("^\d\d:\d\d:\d\d(\.\d+)?$")
        if pattern.match(value):
            return True
        else:
            return False
    else:
        return False

def is_seconds(value):
    """ Checks if the given value represents seconds
    Integer, Floats and Strings of the right format are valid
    """
    if type(value) == type(float()) or type(value) == type(int()):
        return True
    elif type(value) == type(str()):
        pattern = re.compile("^\d+(\.\d+)?$")
        if pattern.match(value):
            return True
        else:
            return False
    else:
        return False

# Try to parse anything to unicode
# http://www.codigomanso.com/en/2010/05/una-de-python-force_unicode/
def force_unicode(seq, encoding='utf-8', errors='ignore'):
    """
    Returns a unicode object representing 'seq'. Treats bytestrings using the
    'encoding' codec.
    """
    import codecs
    if seq is None:
        return ''

    try:
        if not isinstance(seq, six.string_types,):
            if hasattr(seq, '__unicode__'):
                seq = unicode(seq)
            else:
                try:
                    seq = unicode(str(seq), encoding, errors)
                except UnicodeEncodeError:
                    if not isinstance(seq, Exception):
                        raise
                    # If we get to here, the caller has passed in an Exception
                    # subclass populated with non-ASCII data without special
                    # handling to display as a string. We need to handle this
                    # without raising a further exception. We do an
                    # approximation to what the Exception's standard str()
                    # output should be.
                    seq = ' '.join([force_unicode(arg, encoding, errors) for arg in seq])
        elif not isinstance(seq, unicode):
            # Note: We use .decode() here, instead of unicode(seq, encoding,
            # errors), so that if seq is a SafeString, it ends up being a
            # SafeUnicode at the end.
            seq = seq.decode(encoding, errors)
    except UnicodeDecodeError as e:
        if not isinstance(seq, Exception):
            raise UnicodeDecodeError (seq, *e.args)
        else:
            # If we get to here, the caller has passed in an Exception
            # subclass populated with non-ASCII bytestring data without a
            # working unicode method. Try to handle this without raising a
            # further exception by individually forcing the exception args
            # to unicode.
            seq = ' '.join([force_unicode(arg, encoding, errors) for arg in seq])
    return seq

def normalize_string(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.

    Returns a unicode object
    """
    value = force_unicode(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    return re.sub('[-\s]+', '-', value)

def filename_convert(input_file):
    """ Converts /foo/bar/Example.mp4 to Example_mp4
    Used for the generation of log filenames
    """
    path, filename = os.path.split(input_file)
    fname, ext = os.path.splitext(filename)
    return fname + "_" + ext[1:]

def get_probe_log_filename(input_file):
    """ generates the filename for the ffprobe logfile
    """
    return CFG_BIBENCODE_FFMPEG_PROBE_LOG % (filename_convert(input_file))

def get_lines_from_probe_log(input_file):
    """ Probes the file using FFprobe and returns the lines of the probe log
        This will create a log file.
    """
    ## Create Log file
    log_file = open(get_probe_log_filename(input_file), 'w')
    ## Build command for ffprobe execution
    command = (CFG_BIBENCODE_FFMPEG_PROBE_COMMAND % input_file).split()
    ## Start process and wait until it finishes
    process = subprocess.Popen(command, stderr=log_file)
    returncode = process.wait()
    ## If the process ends normal parse log file
    if returncode == 0:
        ## Read the Log
        log_file = open(get_probe_log_filename(input_file))
        finput = log_file.read()
        lines = finput.splitlines()
        log_file.close()
        return lines
    ## If there was a problem during execution
    if returncode == -15 or returncode == 1:
        return None
    else:
        return None

# Simple function to receive ffprobe results
def probe(input_file, parsable=False):
    """ Probes the file using FFprobe and returns the output as a string
    """
    command = (CFG_BIBENCODE_FFMPEG_PROBE_COMMAND % input_file).split()
    process = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    returncode = process.wait()
    if returncode == 0:
        if not parsable:
            return process.communicate()[1]
        else:
            return process.communicate()[0]
    else:
        return None

def mediainfo(input_file):
    """ Receives XML output from mediainfo CLI
    """
    command = (CFG_BIBENCODE_MEDIAINFO_COMMAND % input_file).split()
    process = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    returncode = process.wait()
    if returncode == 0:
        return process.communicate()[0]
    else:
        return None

def check_ffmpeg_configuration():
    """ Uses ffprobe to check if ffmpeg is compiled with the right
    options to integrate in BibEncode

    @return: Returns a list of missing options
    @rtype: set
    """
    ## Use ffprobe to get the current ffmpeg configuration
    try:
        process = subprocess.Popen(CFG_PATH_FFPROBE, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    except OSError:
        return ["FFMPEG/FFPROBE does not seem to be installed!"]
    returncode = process.wait()
    ## This reads the stream from PIPE
    output = process.communicate()[1]
    ## find the configuration text inside ffprobes output
    ## and parse all the configuration arguments
    ## 'options' is a list configuration flags
    options = CFD_BIBENCODE_FFMPEG_OUT_RE_CONFIGURATION.findall(output)
    ## check if the neccessary configuration is availables
    ## This should be at least --enable-libvpx, ...libtheora, ...libvorbis
    ## ...gpl, ..version3, ...nonfree,
    ## libx264 and libfaac should be recommended in the manual but with
    ## regards about the licensing and patenting issues

    ## !!! Warn: For old Python versions, there is the sets module
    ## For newer ones, this is deprecated, set is a build in type now
    if sys.version_info < (2, 6):
        import sets
        o = sets.Set(options)
        s = sets.Set(CFG_BIBENCODE_FFMPEG_CONFIGURATION_REQUIRED)
        if not s.issubset(o):
            return o.difference(s)
    else:
        if not set(CFG_BIBENCODE_FFMPEG_CONFIGURATION_REQUIRED).issubset(options):
            return set(CFG_BIBENCODE_FFMPEG_CONFIGURATION_REQUIRED).difference(options)

def check_mediainfo_configuration():
    """ Checks if mediainfo lib is installed

    @return: Returns a list of missing options or simply False if no missings
    @rtype: set
    """
    try:
        process = subprocess.Popen('mediainfo', stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    except OSError:
        return ["MEDIAINFO does not seem to be installed!"]
    return False

def getval(dictionary, key, fallback=None):
    """ Returns a value from a dict. If the key doesn't exist, returns fallback

    @param dictionary: a dictionary with the value to access
    @type dictionary: dict
    @param key: key of the value to access
    @type key: object
    @param fallback: a fallback value if the key does not exist
    @type fallback: object
    @return: the value of the key or the fallback
    @rtype: object
    """
    if type(dictionary) == type(dict()) and key in dictionary:
        return dictionary[key]
    else:
        return fallback

def chose(primary, fallback_key, fallback_dict):
    """ Returns a fallback from a dictionary if the primary is not available

    @param primary: value to take first
    @type primary: object
    @param fallback_key: key of the fallback
    @type fallback_key: object
    @param fallback_dict: the dictinary where the fallback key is stored
    @type fallback_dict: dict
    @return: primary, fallback value or None
    @rtype: object
    """
    if not primary:
        return getval(fallback_dict, fallback_key)
    else:
        return primary

def chose2(key, primary_dict, fallback_dict):
    """ Tries to receive a key from one dictionary and falls back to another
    """
    return getval(primary_dict, key,
                  getval(fallback_dict, key))

def aspect_string_to_float(aspect_as_string):
    """
    Transforms a string containing an aspect ratio to a float

    @param aspect_as_string: Aspect ratio as a String eg '16:9'
    @type aspect_as_string: string
    @return: Aspect ratio as a float eg '1.77777'
    @rtype: float
    """
    try:
        aspect_x, aspect_y = aspect_as_string.split(':')
        aspect_x = float(aspect_x)
        aspect_y = float(aspect_y)
    except:
        raise
    return aspect_x / aspect_y
