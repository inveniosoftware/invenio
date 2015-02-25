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

from __future__ import print_function

"""BibEncode module.
A multi-purpose module that wraps around FFMPEG.
It allows the execution of video transcoding, frame extraction,
metadata handling and more as BibTasks.
"""

__revision__ = "$Id$"

from pprint import pprint
import os

from invenio.legacy.bibsched.bibtask import (task_init,
                             write_message,
                             task_set_option,
                             task_get_option,
                             task_set_task_param,
                             )
from invenio.utils.json import json, json_decode_file

from . import (encode, extract, metadata, daemon, batch_engine)
from .config import (
    CFG_BIBENCODE_FFMPEG_VALID_SIZES,
    CFG_BIBENCODE_FFMPEG_VALID_ACODECS,
    CFG_BIBENCODE_FFMPEG_VALID_VCODECS,
    CFG_BIBENCODE_VALID_MODES,
    CFG_BIBENCODE_FFMPEG_RE_VALID_SIZE,
    CFG_BIBENCODE_PROFILES_ENCODING,
    CFG_BIBENCODE_PROFILES_EXTRACT,
    CFG_BIBENCODE_DAEMON_DIR_NEWJOBS,
    CFG_BIBENCODE_DAEMON_DIR_OLDJOBS,
    )
from .profiles import get_encoding_profiles, get_extract_profiles
from .utils import check_ffmpeg_configuration


def _topt(key, fallback=None):
    """ Just a shortcut
    """
    return task_get_option(key, fallback)


def task_submit_elaborate_specific_parameter(key, value, opts, args):
    """ Given the string key it checks it's meaning, eventually using the
    value. Usually it fills some key in the options dict.
    It must return True if it has elaborated the key, False, if it doesn't
    know that key.
    eg:
    if key in ('-n', '--number'):
        self.options['number'] = value
        return True
    return False
    """
    ## A dictionary used for mapping CLI parameters to task_option keys+-
    parameter_mapping = {
        '-p': 'profile_name',
        '-i': 'input',
        '--input': 'input',
        '-o': 'output',
        '--output': 'output',
        '-m': 'mode',
        '--mode': 'mode',
        '--acodec': 'acodec',
        '--vcodec': 'vcodec',
        '--abitrate': 'abitrate',
        '--vbitrate': 'vbitrate',
        '--resolution': 'size',
        '--passes': 'passes',
        '--special': 'special',
        '--specialfirst': 'specialfirst',
        '--specialsecond': 'specialsecond',
        '--width': 'width',
        '--height': 'height',
        '--aspect': 'aspect',
        '--number': 'numberof',
        '--positions': 'positions',
        '-D': 'meta_dump',
        '-W': 'meta_input',
        '--dump': 'meta_dump',
        '--write': 'meta_input',
        '--newjobfolder': 'new_job_folder',
        '--oldjobfolder': 'old_job_folder',
        '--recid': 'recid',
        '--collection': 'collection',
        '--search': 'search'
    }

    ## PASSES ##
    ## Transform 'passes' to integer
    if key in ('--passes', ):
        try:
            value = int(value)
        except ValueError:
            write_message('Value of \'--passes\' must be an integer')
            return False

    ## HEIGHT, WIDTH ##
    if key in ('--height', '--width'):
        try:
            value = int(value)
        except ValueError:
            write_message('Value of \'--height\' or \'--width\''
                          ' must be an integer')
            return False

    ## META MODE ##
    ## Transform meta mode values to boolean
    if key in ('-D', '--dump'):
        if not value in ("ffprobe", "mediainfo", "pbcore"):
            write_message("Unknown dumping format, must be 'ffprobe', 'mediainfo' or 'pbcore'")
            return False
    if key in ('--substitute', ):
        value = True
    ## Transform the 'positions' parameter into a list
    if key in ('--positions',):
        try:
            parsed = json.loads(value)
            if type(parsed) is not type(list()):
                write_message(
                    'Value of \'--positions\' must be a json list'
                )
                return False
            else:
                value = parsed
        except ValueError:
            write_message(
                    'Value of \'--positions\' must be a json list'
                )
            return False

    ## NUMBEROF ##
    ## Transform 'number' to integer
    if key in ('--number'):
        try:
            value = int(value)
        except ValueError:
            write_message('Value of \'--number\' must be an integer')
            return False
    ## ASPECT ##
    if key in ('--aspect'):
        try:
            xasp, yasp = str(value).split(':')
            xasp = float(xasp)
            yasp = float(yasp)
            value = xasp / yasp
        except:
            write_message('Value of \'--aspect\' must be in \'4:3\' format')
            return False
    ## RECID ##
    if key in ('--recid'):
        try:
            value = int(value)
        except ValueError:
            write_message('Value of \'--recid\' must be an integer')
            return False

    ## GENERAL MAPPING ##
    ## For all general or other parameters just use the mapping dictionary
    if key in parameter_mapping:
        task_set_option(parameter_mapping[key], value)
        return True
    return False


def task_run_core():
    """Runs the task by fetching arguments from the BibSched task queue.
    This is what BibSched will be invoking via daemon call.
    Return 1 in case of success and 0 in case of failure."""

    #---------------#
    # Encoding Mode #
    #---------------#

    if _topt('mode') == 'encode':
        return encode.encode_video(
                                    input_file=_topt('input'),
                                    output_file=_topt('output'),
                                    acodec=_topt('acodec'),
                                    vcodec=_topt('vcodec'),
                                    abitrate=_topt('abitrate'),
                                    vbitrate=_topt('vbitrate'),
                                    resolution=_topt('size'),
                                    passes=_topt('passes'),
                                    special=_topt('special'),
                                    specialfirst=_topt('specialfirst'),
                                    specialsecond=_topt('specialsecond'),
                                    width=_topt('width'),
                                    height=_topt('height'),
                                    aspect=_topt('aspect'),
                                    profile=_topt('profile')
                                    )

    #-----------------#
    # Extraction Mode #
    #-----------------#

    elif _topt('mode') == 'extract':
        return extract.extract_frames(
                                input_file=_topt('input'),
                                output_file=_topt('output'),
                                size=_topt('size'),
                                positions=_topt('positions'),
                                numberof=_topt('numberof'),
                                width=_topt('width'),
                                height=_topt('height'),
                                aspect=_topt('aspect'),
                                profile=_topt('profile')
                                )

    #---------------#
    # Metadata Mode #
    #---------------#
    elif _topt('mode') == 'meta':
        if _topt('meta_dump') is not None:
            metadata.dump_metadata(
                                       input_file=_topt('input'),
                                       output_file=_topt('output'),
                                       meta_type=_topt('meta_dump')
                                       )
            return True
        elif _topt('meta_input') is not None:
            if type(_topt('meta_input')) is not type(dict()):
                the_metadata = metadata.json_decode_file(
                                        filename=_topt('meta_input'))
                task_set_option('meta_input', the_metadata)
            return metadata.write_metadata(
                                       input_file=_topt('input'),
                                       output_file=_topt('output'),
                                       metadata=_topt('meta_input')
                                       )

    #------------#
    # Batch Mode #
    #------------#
    elif _topt('mode') == 'batch':
        if _topt('collection'):
            return batch_engine.create_update_jobs_by_collection(
                            batch_template_file=_topt('input'),
                            collection=_topt('collection'),
                            job_directory=_topt('new_job_dir',
                                            CFG_BIBENCODE_DAEMON_DIR_NEWJOBS))
        elif _topt('search'):
            return batch_engine.create_update_jobs_by_search(
                            pattern=_topt('search'),
                            batch_template_file=_topt('input'),
                            job_directory=_topt('new_job_dir',
                                            CFG_BIBENCODE_DAEMON_DIR_NEWJOBS))
        else:
            return batch_engine.process_batch_job(_topt('input'))

    #-------------#
    # Daemon Mode #
    #-------------#
    elif _topt('mode') == 'daemon':
        return daemon.watch_directory(
                                    _topt('new_job_dir', CFG_BIBENCODE_DAEMON_DIR_NEWJOBS),
                                    _topt('old_job_dir', CFG_BIBENCODE_DAEMON_DIR_OLDJOBS)
                                    )


def task_submit_check_options():
    """ Checks the tasks arguments for validity
    """

    #----------------#
    # General Checks #
    #----------------#

    ## FFMPEG CONFIGURATION ##
    ## The status of ffmpeg should be checked before a task is submitted
    ## There is a minimum configuration that ffmpeg must be compiled with
    ## See bibencode_utils and bibencode_config
    config = check_ffmpeg_configuration()
    if config:
        ## Prints missing configuration
        string = ''
        for item in config:
            string += ('\t' + item + '\n')
        write_message(
            "FFmpeg options are missing. Please recompile and add:\n" + string
        )
        return False

    ## MODE ##
    ## Check if the mode is a valid
    if _topt('mode') is None:
        write_message('You have to specify a mode using \'-m MODE\'')
        return False
    if _topt('mode') not in CFG_BIBENCODE_VALID_MODES:
        write_message('%s is not a valid mode. Use one of %s'
                      % (_topt('mode'), CFG_BIBENCODE_VALID_MODES))
        return False

    ## INPUT ##
    ## Check if the input file is given and if it exists
    ## You should always use an absolute path to the file
    if _topt('mode') in ('encode', 'extract', 'meta', 'batch'):
        if _topt('input') is None:
            write_message('You must specify an input file using \'-i FILE\'')
            return False
        else:
            if not os.path.exists(_topt('input')):
                print(("The file %s does not exist" % _topt('input')))
                return False

    ## OUTPUT ##
    ## Check if the output file is given and if it exists
    ## You should always use an absolute path to the file
    if _topt('mode') in ('encode', 'extract', 'meta'):
        if _topt('output') is None:
            write_message('No output file is given. Please specify with'
                          ' \'-o NAME\''
                          )
            return False

    #---------------#
    # Encoding Mode #
    #---------------#
    if _topt('mode') == 'encode':

        ## PROFILE ## Check for a valid profile if this is given
        if _topt('profile_name') is not None:
            if _topt('profile_name') not in get_encoding_profiles():
                write_message('%s not found in %s' %
                              (_topt('profile_name'),
                               CFG_BIBENCODE_PROFILES_ENCODING)
                              )
                return False
            ## If the profile exists
            else:
                pass

        ## AUDIOCODEC ##
        ## Checks if the audiocodec is one of the predefined
        if _topt('acodec') is not None:
            if _topt('acodec') not in CFG_BIBENCODE_FFMPEG_VALID_ACODECS:
                write_message(
                    '%s is not a valid audiocodec.\nAvailable codecs: %s'
                    % (_topt('acodec'), CFG_BIBENCODE_FFMPEG_VALID_ACODECS)
                )
                return False

        ## VIDEOCODEC ## Checks if the videocodec is one of the predefined
        if _topt('vcodec') is not None:
            if _topt('vcodec') not in CFG_BIBENCODE_FFMPEG_VALID_VCODECS:
                write_message(
                    '%s is not a valid videocodec.\nAvailable codecs: %s'
                    % (_topt('vcodec'), CFG_BIBENCODE_FFMPEG_VALID_VCODECS)
                )
                return False

        ## SIZE ##
        ## Checks if the size is either WxH or an FFMPEG preset
        if _topt('size') is not None:
            if not CFG_BIBENCODE_FFMPEG_RE_VALID_SIZE.match(_topt('size')):
                if _topt('size') not in CFG_BIBENCODE_FFMPEG_VALID_SIZES:
                    write_message(
                        '%s is not a valid frame size.\nEither use the'
                        ' \'WxH\' notation or one of these values:\n%s'
                        % (_topt('size'), CFG_BIBENCODE_FFMPEG_VALID_SIZES)
                    )
                    return False
        ## Check if both a size and vertical or horizontal resolution
        if (_topt('width') or _topt('height')) and _topt('size'):
            write_message('Options \'width\' and \'height\' can not be '
                          'combined with \'resolution\'')
            return False

        ## PASSES ##
        ## If a number of passes is given, it should be either 1 oder 2.
        ## You could do an infinite number of passes with ffmpeg,
        ## But it will almost never make a difference above 2 passes.
        ## So, we currently only support 2 passes.
        if _topt('passes') is not None:
            if _topt('passes') not in (1, 2):
                write_message('The number of passes must be either 1 or 2')
                return False
        else:
            task_set_option('passes', 1)

        ## BITRATE ##
        ## Check if the given bitrate is either 1000 sth. or 1000k sth.
        if _topt('abitrate') is not None:
            pass
        if _topt('vbitrate') is not None:
            pass

    #-----------------#
    # Extraction Mode #
    #-----------------#
    elif _topt('mode') == 'extract':

        ## PROFILE ##
        ## If a profile is given, check its validity
        if _topt('profile_name') is not None:
            if _topt('profile_name') not in get_extract_profiles():
                write_message('%s not found in %s' %
                              (_topt('profile_name'),
                               CFG_BIBENCODE_PROFILES_EXTRACT)
                              )
                return False
            ## If the profile exists
            else:
                pass

        ## You cannot give both a number and specific positions
        ## !!! Think about allowing both -> First extract by number,
        ## !!! then additionally the specific positions
        if (
            ((_topt('numberof') is not None) and
            (_topt('positions') is not None))
            or
            ((_topt('numberof') is None) and
            (_topt('positions') is None))
            ):
            write_message('Please specify either a number of frames to '
                          'take or specific positions')
            return False

        ## SIZE ##
        ## Checks if the size is either WxH or an FFMPEG specific value
        if _topt('size') is not None:
            if not CFG_BIBENCODE_FFMPEG_RE_VALID_SIZE.match(_topt('size')):
                if _topt('size') not in CFG_BIBENCODE_FFMPEG_VALID_SIZES:
                    write_message(
                        '%s is not a valid frame size.\nEither use the'
                        '\'WxH\' notation or one of these valus:\n%s'
                        % (_topt('size'), CFG_BIBENCODE_FFMPEG_VALID_SIZES)
                    )
                    return False

    #---------------#
    # Metadata Mode #
    #---------------#
    elif _topt('mode') == 'meta':

        ## You have to give exactly one meta suboption
        if not _xor(_topt('meta_input'),
                   _topt('meta_dump')):
            write_message("You can either dump or write metadata")
            return False

        ## METADATA INPUT ##
        if _topt('meta_input') is not None:
            ## Check if this is either a filename (that should exist)
            ## or if this a jsonic metadata notation
            if os.path.exists(_topt('meta_input')):
                pass
            else:
                try:
                    metadict = json.loads(_topt('meta_input'))
                    task_set_option('meta_input', metadict)
                except ValueError:
                    write_message('The value %s of the \'--meta\' parameter is '
                                  'neither a valid filename nor a jsonic dict'
                                  % _topt('meta_input'))
                    return False

    #------------#
    # Batch Mode #
    #------------#
    elif _topt('mode') == 'batch':
        if _topt('collection') and _topt('search'):
            write_message('You can either use \'search\' or \'collection\'')
            return False
        elif _topt('collection'):
            template = json_decode_file(_topt('input'))
            print('\n')
            print("#---------------------------------------------#")
            print("# YOU ARE ABOUT TO UPDATE A WHOLE COLLECTION  #")
            print("#---------------------------------------------#")
            print('\n')
            print('The selected template file contains:')
            pprint(template)
            print('\n')
        elif _topt('search'):
            template = json_decode_file(_topt('input'))
            message = "# YOU ARE ABOUT TO UPDATE RECORDS MATCHING '%s'  #" % _topt('search')
            print('\n')
            print(("#" + "-"*(len(message)-2) + "#"))
            print(message)
            print(("#" + "-"*(len(message)-2) + "#"))
            print('\n')
            print('The selected template file contains:')
            pprint(template)
            print('\n')


    #-------------#
    # Daemon Mode #
    #-------------#
    elif _topt('mode') == 'daemon':
        task_set_task_param('task_specific_name', 'daemon')
        ## You can either give none or both folders, but not only one
        if _xor(_topt('new_job_folder'), _topt('old_job_folder')):
            write_message('When specifying folders for the daemon mode, you '
                          'have to specify both the folder for the new jobs '
                          'and the old ones')
            return False


    ## If every check went fine
    return True


def main():
    """Main that construct all the bibtask."""
    task_init(authorization_action='runbibencode',
            authorization_msg="Bibencode Task Submission",
            help_specific_usage=(
"""
  General options:
  -m, --mode=           Selects the mode for BibEncode
                           Modes: 'meta', 'encode', 'extract', 'daemon', 'batch'
  -i, --input=          Input file
  -o, --output=         Output file


  Options for mode 'meta':
  -D, --dump=           Dumps metadata from a video to a file
                           Options: "ffprobe", "mediainfo", "pbcore"
  -W, --write=          Write metadata to a copy of the file
                            Either a filename or a serialized JSON object.

  Options for mode 'encode'
  -p                    Profile to use for encoding
  --acodec=             Audiocodec for the transcoded video
  --vcodec=             Videocodec for the transcoded video
  --abitrate=           Bitrate auf the audio stream
  --vbitrate=           Bitrate of the video stream
  --resolution=         Resolution of the transcoded video
  --passes=             Number of passes
  --special=            Pure FFmpeg options that will be appended to the command
  --specialfirst=       Pure FFmpeg options for the first pass
  --specialsecond=      Pure FFmpeg options for the second pass
  --width=              Horizontal resolution
  --height=             Vertical resolution
  --aspect=             Aspect ratio fallback if undetectable

  Options for mode 'extract':
  -p                    Profile to use for frame extraction
  --resolution=         Resolution of the extracted frame(s)
  --number=             Number of frames to extract
  --positions=          Specific positions inside the video to extract from
                            Python list notation
                            Either in seconds like '10' or '10.5'
                            Or as a timecode like '00:00:10.5'
                            Example:'[10, 10.5, 00:00:12.5, 20, 00:08:45:11.26]'
  -o, --output=         Output filename can be substituted by bibencode:
                            %(input)s for the input filename
                            %(timecode)s for the timecode
                            %(size)s for the frame size
                            %(number)d for sequential numbers
  --width=              Horizontal resolution
  --height=             Vertical resolution
  --aspect=             Aspect ratio fallback if undetectable

  Options for mode 'batch':
  --collection=         Updates the whole collection acc. to a batch template
  --search=             Updates all records matching the search query

  Options for mode 'daemon':
  --newjobdir=          Optional folder to look for new job descriptions
  --oldjobdir=          Optional folder to move the job desc. of done jobs

"""
            ),
            version=__revision__,
            specific_params=("m:i:o:p:W:D:",
                [
                 "mode=",
                 "input=",
                 "output=",
                 "write=",
                 "dump=",
                 "acodec=",
                 "vcodec=",
                 "abitrate=",
                 "vbitrate=",
                 "resolution=",
                 "passes=",
                 "special=",
                 "specialfirst=",
                 "specialsecond=",
                 "height=",
                 "width=",
                 "number=",
                 "positions=",
                 "substitute",
                 "newjobdir=",
                 "oldjobdir=",
                 "recid=",
                 "aspect=",
                 "collection=",
                 "search="
                 ]),
            task_submit_elaborate_specific_parameter_fnc= \
                            task_submit_elaborate_specific_parameter,
            task_submit_check_options_fnc=task_submit_check_options,
            task_run_fnc=task_run_core)

def _xor(*xvars):
    """ XOR Helper
    """
    xsum = bool(False)
    for xvar in xvars:
        xsum = xsum ^ bool(xvar)
    return xsum

if __name__ == '__main__':
    main()

