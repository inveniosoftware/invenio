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

"""BibEncode frame extraction module.
"""

__revision__ = "$Id$"

from invenio.modules.encoder.config import (
                            CFG_BIBENCODE_FFMPEG_EXTRACT_COMMAND,
                            )
from invenio.legacy.bibsched.bibtask import (
                             task_update_progress,
                             write_message
                             )
from invenio.modules.encoder.utils import (
                            timecode_to_seconds,
                            seconds_to_timecode,
                            is_timecode,
                            is_seconds,
                            normalize_string,
                            getval,
                            chose
                            )
from invenio.modules.encoder.metadata import (
                        ffprobe_metadata
                        )
import subprocess
import os
from invenio.modules.encoder.profiles import get_extract_profile
from invenio.modules.encoder.encode import determine_resolution_preserving_aspect
import re

# rename size to resolution
def extract_frames(input_file, output_file=None, size=None, positions=None,
                   numberof=None, extension='jpg',
                   width=None, height=None, aspect=None, profile=None,
                   update_fnc=task_update_progress,
                   message_fnc=write_message):
    """ Extracts frames from a given video using ffmpeg based on the given
    parameters. Starts a subprocess. The status of the process is continously
    written to the given messaging functions.

    @param input_file: Full path to the input video.
    @type input_file: String

    @param output_file: Full path to the output file, in case of multiple outs,
                   there will be squential numbers appended to the file's name
                   automatically. If this parameter is not given, the
                   output filename will be generated from the input file
                   The output can be substituted with information.
                   Valid substrings for substitution are:
                          %(input)s for the input filename
                          %(timecode)s for the timecode
                          %(size)s for the frame size
                          %(number)d for sequential numbers

                  Everything else that could be a python substitution substring
                  should be escaped accordingly.
                  !!! Warnning !!! FFmpeg will also try to substitude if there
                  are any '%' left. This will likely screw up the extraction.
    @type output_file: string

    @param size: The size of the frames. Format is WxH
    @type size: string

    @param positions: A list of positions within the video where the frames
                      should be shot. Percentual values between 0 and 100 or
                      HH:MM:SS.ss are accepted.
    @type positions: string

    @param numberof: In case you don't want to give positions but just a fixed
                number of frames to extract.
    @type numberof: nt

    @param extension: If no output filename is given, construct the name with
                      this extension
    @type extension: string

    @param width: The width of the extracted frame.
    @type width: int

    @param height: The height of the extracted frame
    @type height: int

    @param aspect: A float representing the aspect ratio of the video.
                   4:3 equals 1.33 and 16:9 equals 1.77. See also 'width'
    @type aspect: float or "4:3" like string

    @param profile: A profile to use. The priority is on the parameters directly
               given to the function.
    @type profile: string

    @param update_fnc: A function called to display or log an the encoding
                  status. This function must accept a string.
    @type update_fnc: function

    @param message_fnc: A function to log important messages or errors.
                   This function must accept a string.
    @type message_fnc: function

    @return: 1 if the extraction was successful, 0 if not
    @rtype: bool
    """

    #---------#
    # PROFILE #
    #---------#

    ## Takes parameters from the profile if they are not directly given
    if profile:
        profile = get_extract_profile(profile)
        size = chose(size, 'size', profile)
        positions = chose(positions, 'positions', profile)
        numberof = chose(numberof, 'numberof', profile)
        extension = chose(extension, 'extension', profile)
        width = chose(width, 'width', profile)
        height = chose(height, 'height', profile)

    #---------------#
    # Check and fix #
    #---------------#

    ## If neither positions nor a number of shots are given
    if not positions and not numberof:
        raise ValueError("Either argument \'positions\' xor argument \'numberof\' must be given")
    ## If both are given
    if positions and numberof:
        raise ValueError("Arguments \'positions\' and \'numberof\' exclude each other")
    ## If just a number of shots to take is given by 'numberof'
    if numberof and not positions:
        ## Parse the duration from the input
        info = ffprobe_metadata(input_file)
        if info is None:
            message_fnc("An error occured while receiving the video log")
            return 0
        duration = float(info['format']['duration'])
        if duration is None:
            message_fnc("Could not extract by \'numberof\' because video duration is unknown.")
            return 0
        positions = []
        for pos in range(numberof):
            ## Calculate the position for every shot and append it to the list
            position = pos * (duration / numberof)
            positions.append(position)
    ## If specific positions are given
    elif positions and not numberof:
        ## Check if correct timecodes or seconds are given
        i = 0
        for pos in positions:
            if not (is_seconds(pos) or is_timecode(pos)):
                raise ValueError("The given position \'%s\' is neither a value in seconds nor a timecode!" % str(pos))
            ## if a timecode is given, convert it to seconds
            if is_timecode(pos):
                positions[i] = timecode_to_seconds(pos)
            i += 1
    ## If no output filename is given, use input filename and append jpg
    if output_file is None:
        ipath = os.path.splitext(input_file)[0]
        if not extension.startswith("."):
            extension = "." + extension
        output_file = ipath + extension
    ## If no explizit size for the frames is given
    if not size:
        size = determine_resolution_preserving_aspect(input_file, width, height, aspect)

    #------------#
    # Extraction #
    #------------#

    counter = 1
    for position in positions:

        #---------------------------#
        # Generate output file name #
        #---------------------------#

        number_substituted = False
        if '%(number)' in  output_file:
            number_substituted = True

        ## If the output filename should be stubstituted
        try:
            output_filename = output_file % {
                                'input': os.path.splitext(os.path.split(input_file)[1])[0],
                                'timecode': seconds_to_timecode(position),
                                'size': size,
                                'number': counter
                                }
        except KeyError:
            raise
        ## In case that more than one shot is taken and you don't want to substitute
        if not number_substituted:
            if len(positions) > 1:
                path, ext = os.path.splitext(output_file)
                output_filename = path + str(counter).zfill(len(str(len(positions)))) + ext
            ## If you dont want to substitute and only one file is selected,
            ## it will just take the output or input name without altering it
            else:
                output_filename = output_file

        #-------------#
        # Run process #
        #-------------#

        ## Build the command for ffmpeg
        command = (CFG_BIBENCODE_FFMPEG_EXTRACT_COMMAND % (
            position, input_file, size, output_filename
            )).split()
        ## Start subprocess and poll the output until it finishes
        process = subprocess.Popen(command, stderr=subprocess.PIPE)
        stderr = []
        while process.poll() is None:
            ## We want to keep the last lines of output in case of an error
            stderr += process.communicate()[1].splitlines()
            stderr = stderr[-5:]
        ## If something went wrong, print the last lines of the log
        if process.poll() != 0:
            msg = ("Error while extracting frame %d of %d" % (counter, len(positions)))
            message_fnc(msg)
            update_fnc(msg)
            ## Print the end of the log
            message_fnc("Last lines of the FFmpeg log:")
            for line in stderr:
                message_fnc(line)
            return 0
        else:
            update_fnc("Frame %d of %d extracted" % (counter, len(positions)))
        counter += 1

    ## Everything should be fine if this position is reached
    message_fnc("Extraction of frames was successful")
    return 1
