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

"""BibEncode encoding submodule"""

from six import iteritems

from invenio.legacy.bibsched.bibtask import (
                             write_message,
                             task_update_progress,
                             )
from invenio.modules.encoder.config import (
                                     CFG_BIBENCODE_FFMPEG_ENCODING_LOG,
                                     CFG_BIBENCODE_FFMPEG_PASSLOGFILE_PREFIX,
                                     CFG_BIBENCODE_FFMPEG_METADATA_ARGUMENT,
                                     CFG_BIBENCODE_FFMPEG_ENCODE_TIME
                                     )
from invenio.modules.encoder.utils import (
                                     timecode_to_seconds,
                                     generate_timestamp,
                                     chose,
                                     getval,
                                     aspect_string_to_float
                                     )
from invenio.modules.encoder.profiles import get_encoding_profile
from invenio.modules.encoder.metadata import (
                                        ffprobe_metadata,
                                        mediainfo_metadata
                                        )
from invenio.config import CFG_PATH_FFMPEG
import time
import os
import subprocess
import uuid

def _filename_log(output_filename, nofpass=1):
    """ Constructs the filename including path for the encoding err file
    @param output_filename: name of the video file to be created
    @type output_filename: string
    @param nofpass: number of encoding passes
    @type nofpass: int
    @return: the constructed log filename
    @rtype: string
    """
    fname = os.path.split(output_filename)[1]
    fname = os.path.splitext(fname)[0]
    return CFG_BIBENCODE_FFMPEG_ENCODING_LOG % (generate_timestamp() +
                                                "_" + fname + "_%d" % nofpass)

def determine_aspect(input_file):
    """ Checks video metadata to find the display aspect ratio.
    Returns None if the DAR is not stored in the video container.

    @param input_file: full path of the video
    @type input_file: string
    """
    videoinfo = ffprobe_metadata(input_file)
    if not videoinfo:
        return None
    for stream in videoinfo['streams']:
        if stream['codec_type'] == 'video':
            fwidth = int(stream['width'])
            fheight = int(stream['height'])
            if 'display_aspect_ratio' in stream:
                return (stream['display_aspect_ratio'], fwidth, fheight)
    return (None, fwidth, fheight)

def determine_resolution_preserving_aspect(input_file, width=None,
                                           height=None, aspect=None):
    """ Determines the right resolution for a given width or height while
    preserving the aspect ratio.
    @param input_file: full path of the video
    @type input_file: string
    @param width: The proposed width for the new size.
    @type width: int
    @param height: The proposed height for the new size
    @type height: int
    @param aspect: Override aspect ratio determined from the input file
    @type aspect: float or "4:3" like string
    @return: An FFMPEG compatible size string '640x480'
    @rtype: string
    """

    def _make_even(number):
        """ Resolutions need to be even numbers for some video encoders.
        We simply increase the resulution by one pixel if it is not even.
        """
        if number % 2 != 0:
            return number+1
        else:
            return number

    if aspect:
        if type(aspect) == type(str()):
            aspect_ratio = aspect_string_to_float(aspect)
        elif type(aspect) == type(float()):
            aspect_ratio = aspect
        else:
            raise ValueError
    else:
        aspect_ratio_tuple = determine_aspect(input_file)
        if aspect_ratio_tuple[0] is None:
            aspect_ratio = float(aspect_ratio_tuple[1]) / float(aspect_ratio_tuple[2])
        else:
            aspect_ratio = aspect_string_to_float(aspect_ratio_tuple[0])

    nresolution = None
    if width and not height:
        ## The resolution hast to fit exactly the width
        nheight = int(width / aspect_ratio)
        nheight = _make_even(nheight)
        nresolution = "%dx%d" % (width, nheight)
    elif height and not width:
        ## The resolution hast to fit exactly the height
        nwidth = int(height * aspect_ratio)
        nwidth = _make_even(nwidth)
        nresolution = "%dx%d" % (nwidth, height)
    elif width and height:
        ## The resolution hast to be within both parameters, seen as a maximum
        nwidth = width
        nheight = height
        new_aspect_ratio = float(width) / float(height)
        if aspect_ratio > new_aspect_ratio:
            nheight = int(width / aspect_ratio)
        else:
            nwidth = int(height * aspect_ratio)
        nheight = _make_even(nheight)
        nwidth = _make_even(nwidth)
        nresolution = "%dx%d" % (nwidth, nheight)
    else:
        ## Return the original size in square pixels
        ## original height * aspect_ratio
        nwidth = aspect_ratio_tuple[2] * aspect_ratio
        nwidth = _make_even(nwidth)
        nresolution = "%dx%d" % (nwidth, aspect_ratio_tuple[2])
    return nresolution

def assure_quality(input_file, aspect=None, target_width=None,
                   target_height=None, target_bitrate=None,
                   accept_anamorphic=True, tolerance=0.95):
    """
    Checks if the original video material would support the target resolution
    and/or bitrate.
    @param input_file: full path of the video to check
    @type input_file: string
    @param aspect: the aspect ratio as override
    @type aspect: float
    @param target_width: width of the new video
    @type target_width: int
    @param target_height: height of the new video
    @type target_height: int
    @param target_bitrate: bitrate of the new video in bit/s.
    @type target_bitrate: int
    @param dismiss_aspect: do not care about the aspect
    @type dismiss_aspect: bool
    @return: 1 if the video supports the quality, 0 if not
    @rtype: bool
    """
    if target_bitrate:
        target_bitrate = int(target_bitrate * tolerance)
    if target_height:
        target_height = int(target_height * tolerance)
    if target_width:
        target_width = int (target_width * tolerance)

    ## First get the size and aspect using ffprobe
    ## ffprobe is more reliable in this case then mediainfo
    aspect_ratio_tuple = determine_aspect(input_file)
    fwidth = aspect_ratio_tuple[1]
    fheight = aspect_ratio_tuple[2]
    if not aspect:
        aspect = aspect_ratio_tuple[0]

    ## Get the bitrate with mediainfo now, because it is more realiable
    ## than ffprobe in this case
    fbitrate = None
    videoinfo = mediainfo_metadata(input_file)
    for track in videoinfo:
        if track['kind_of_stream'] == 'Video':
            fbitrate = getval(track, 'bit_rate')
            break
    if fbitrate:
        fbitrate = int(fbitrate)

    # This adapts anamorphic videos.
    # If it is stored anamorphic, calculate the real width from the height
    # we can use our determine_resolution function for this
    if accept_anamorphic and aspect:
        fwidth = determine_resolution_preserving_aspect(
                    input_file=input_file,
                    width=None,
                    height=fheight,
                    aspect=aspect).split('x')[0]
        fwidth = int(fwidth)
    if target_height and target_width:
        if target_width > fwidth or target_height > fheight:
            return False
    elif target_height:
        if target_height > fheight:
            return False
    elif target_width:
        if target_width > fwidth:
            return False
    if target_bitrate:
    ## If the video bitrate is unreadable, assume it is ok and our library
    ## has problems reading it out
        if fbitrate and target_bitrate > fbitrate:
            return False
    return True


def encode_video(input_file, output_file,
                 acodec=None, vcodec=None,
                 abitrate=None, vbitrate=None,
                 resolution=None,
                 passes=1,
                 special=None, specialfirst=None, specialsecond=None,
                 metadata=None,
                 width=None, height=None, aspect=None,
                 profile=None,
                 update_fnc=task_update_progress,
                 message_fnc=write_message
                 ):
    """ Starts an ffmpeg encoding process based on the given parameters.
    The encoding is run as a subprocess. The progress of the subprocess is
    continiously written to the given messaging functions. In a normale case,
    these should be the ones of BibTask.

    @param input_file: Path to the input video.
    @type input_file: string

    @param output_file: Path to the output file. If no other parameters are giv
    than input and output files, FFmpeg tries to auto-discover the right codecs
    for the given file extension. In this case, every other aspect like
    resolution and bitrates will be the same as in the input video.
    @type output_file: string

    @param acodec: The audio codec to use. This must be an available codec of
    libavcodec within FFmpeg.
    @type acodec: string

    @param vcodec: The video codec to use. This must be an available codec of
    libavcodec within FFmpeg.
    @type vcodec: string

    @param abitrate: Bitrate of the audio stream. In bit/s.
    @type abitrate: int

    @param vbitrate: Bitrate of the video stream. In bit/s.
    @type vbitrate: int

    @param resolution: Fixed size of the frames in the transcoded video.
    FFmpeg notation: 'WxH' or preset like 'vga'. See also 'width'

    @param passes: Number of encoding passes. Either 1 or 2.
    @type passes: int

    @param special: Additional FFmpeg parameters.
    @type special: string

    @param specialfirst: Additional FFmpeg parameters for the first pass.
    The 'special' parameter is ignored if this ist not 'None'
    @type specialfirst: string

    @param specialsecond: Additional FFmpeg parameters for the second pass.
    The 'special' parameter is ignored if this is not 'None'
    @type specialsecond: string

    @param metadata: Metadata that should be added to the transcoded video.
    This must be a dictionary. As with as metadata in FFmpeg, there is no
    guarantee that the metadata specified in the dictionary will really be added
    to the file, because it will largelydepend on the container format and its
    supported fields.
    @type metadata: dict

    @param width: Instead of giving a fixed resolution, you can use width and
    height as dimensional constrains. The algorithm will try to preserve the
    original aspect and fit the new frame size into the given dimensions.
    @type width: int

    @param height: see 'width'
    @type height: int

    @param aspect: A float representing the aspect ratio of the video:
    4:3 equals 1.33 and 16:9 equals 1.77.
    This is a fallback in case the algorithm fails to determine the real aspect
    ratio from the video. See also 'width'
    @type aspect: float or "4:3" like string

    @param profile: A profile to use. The priority is on the parameters
    directly given to the function.
    @type profile: string

    @param update_fnc: A function called to display or log an the encoding
    status. This function must accept a string.
    @type update_fnc: function

    @param message_fnc: A function to log important messages or errors.
    This function must accept a string.
    @type message_fnc: function

    @return: True if the encoding was successful, False if not
    @rtype: boolean
    """

    def encode(command):
        """ Subfunction to run the acutal encoding
        """
        ## Start process
        process = subprocess.Popen(command,
                                   stderr=log_file_handle,
                                   close_fds=True)
        ## While the process is running
        time.sleep(1)
        while process.poll() is None:
            # Update the status in bibsched
            update_status()
            time.sleep(4)
        ## If the process was terminated
        if process.poll() == -15:
            # Encoding was terminated by system
            message_fnc("FFMPEG was terminated")
            update_fnc("  FFMPEG was terminated")
            return 0
        ## If there was an error during encoding
        if process.poll() == 1:
            update_fnc("  An FFMPEG error has appeared, see log")
            message_fnc("An FFMPEG error has appeared encoding %s" % output_file)
            message_fnc("Command was: %s" % ' '.join(command))
            message_fnc("Last lines of the FFmpeg log:")
            ## open the logfile again an retrieve the size
            log_file_handle2 = open(log_file_name, 'rb')
            size = os.fstat(log_file_handle2.fileno())[6]
            ## Read the last lines
            log_file_handle2.seek(-min(size, 10000), 2)
            lastlines = log_file_handle2.read().splitlines()[-5:]
            for line in lastlines:
                message_fnc(line)
            return 0
        ## If everything went fine
        if process.poll() == 0:
            message_fnc("Encoding of %s done" % output_file)
            update_fnc("Encoding of %s done" % output_file)
            return 1

    def build_command(nofpass=1):
        """ Builds the ffmpeg command according to the function params
        """
        def insert(key, value):
            """ Shortcut for inserting parameters into the arg list
            """
            base_args.insert(-1, key)
            base_args.insert(-1, value)

        ## Determine base command arguments from the pass to run
        base_args = None
        if passes == 1:
            base_args = [CFG_PATH_FFMPEG, '-y', '-i', input_file, output_file]
        elif passes == 2:
            if nofpass == 1:
                base_args = [CFG_PATH_FFMPEG, '-y', '-i', input_file,
                             '-pass', '1', '-passlogfile', pass_log_file,
                             '-an', '-f', 'rawvideo', '/dev/null']
            elif nofpass == 2:
                base_args = [CFG_PATH_FFMPEG, '-y', '-i', input_file,
                             '-pass', '2', '-passlogfile',
                             pass_log_file, output_file]
        ## Insert additional arguments
        if acodec is not None:
            insert('-acodec', acodec)
        if vcodec is not None:
            insert('-vcodec', vcodec)
        if abitrate is not None:
            insert('-b:a', str(abitrate))
        if vbitrate is not None:
            insert('-b:v', str(vbitrate))

        ## If a resolution is given
        if resolution:
            insert('-s', resolution)
        ## If not, you can give width and height and generate the resolution
        else:
            ## Use our new function to get the size of the input
            nresolution = determine_resolution_preserving_aspect(input_file,
                                                                 width,
                                                                 height,
                                                                 aspect)
            insert('-s', nresolution)
        ## Metadata additions
        if type(metadata) is type(dict()):
            ## build metadata arguments for ffmpeg
            for key, value in iteritems(metadata):
                if value is not None:
                    meta_arg = (
                        CFG_BIBENCODE_FFMPEG_METADATA_ARGUMENT % (key, value)
                        )
                    insert("-metadata", meta_arg)
        ## Special argument additions
        if passes == 1:
            if passes == 1 and special is not None:
                for val in special.split():
                    base_args.insert(-1, val)
        elif passes == 2:
            if nofpass == 1:
                if specialfirst is not None:
                    for val in specialfirst.split():
                        base_args.insert(-1, val)
            if nofpass == 2:
                if specialsecond is not None:
                    for val in specialsecond.split():
                        base_args.insert(-1, val)
        return base_args

    def update_status():
        """ Parses the encoding status and updates the task in bibsched
        """

        def graphical(value):
            """ Converts a percentage value to a nice graphical representation
            """
            ## If the given value is a valid precentage
            if value >= 0 and value <= 100:
                ## This is to get nice, aligned output in bibsched
                oval = str(value).zfill(3)
                return (
                    "[" + "#"*(value/10) + " "*(10-(value/10)) +
                    "][%d/%d] %s%%" % (nofpass, passes, oval)
                    )
            else:
                ## Sometimes the parsed values from FFMPEG are totaly off.
                ## Or maybe nneeded values are not avail. for the given video.
                ## In this case there is no estimate.
                return "[  no est. ][%d/%d]     " % (nofpass, passes)

        ## init variables
        time_string = '0.0'
        percentage_done = -1
        ## try to read the encoding log
        try:
            filehandle = open(log_file_name, 'rb')
        except IOError:
            message_fnc("Error opening %s" % log_file_name)
            update_fnc("Could not open encoding log")
            return
        ## Check the size of the file before reading from the end
        size = os.path.getsize(log_file_name)
        if not size:
            return
        ## Go to the end of the log
        filehandle.seek(-min(10000, size), 2)
        chunk = filehandle.read()
        lines = chunk.splitlines()

        ## try to parse the status
        for line in reversed(lines):
            if CFG_BIBENCODE_FFMPEG_ENCODE_TIME.match(line):
                time_string = (
                    CFG_BIBENCODE_FFMPEG_ENCODE_TIME.match(line).groups()
                    )[0]
                break
        filehandle.close()
        try:
            percentage_done = int(timecode_to_seconds(time_string) / total_seconds * 100)
        except:
            precentage_done = -1
        ## Now update the bibsched progress
        opath, ofile = os.path.split(output_file)
        if len(opath) > 8:
            opath = "..." + opath[-8:]
        ohint = opath + '/' + ofile
        update_fnc(graphical(percentage_done) + " > " + ohint)

    #------------------#
    # PROFILE HANDLING #
    #------------------#

    if profile:
        profile = get_encoding_profile(profile)
        acodec = chose(acodec, 'audiocodec', profile)
        vcodec = chose(vcodec, 'videocodec', profile)
        abitrate = chose(abitrate, 'audiobitrate', profile)
        vbitrate = chose(vbitrate, 'videobitrate', profile)
        resolution = chose(resolution, 'resolution', profile)
        passes = getval(profile, 'passes', 1)
        special = chose(special, 'special', profile)
        specialfirst = chose(specialfirst, 'special_firstpass', profile)
        specialsecond = chose(specialsecond, 'special_secondpass', profile)
        metadata = chose(metadata, 'metadata', profile)
        width = chose(width, 'width', profile)
        height = chose(height, 'height', profile)
        aspect = chose(aspect, 'aspect', profile)

    #----------#
    # ENCODING #
    #----------#

    ## Mark Task as stoppable
    # task_sleep_now_if_required()

    tech_metadata = ffprobe_metadata(input_file)
    try:
        total_seconds = float(tech_metadata['format']['duration'])
    except:
        total_seconds = 0.0


    ## Run the encoding
    pass_log_file = CFG_BIBENCODE_FFMPEG_PASSLOGFILE_PREFIX % (
                    os.path.splitext(os.path.split(input_file)[1])[0],
                    str(uuid.uuid4()))
    no_error = True
    ## For every encoding pass to do
    for apass in range(0, passes):
        nofpass = apass + 1
        if no_error:
            ## Create Logfiles
            log_file_name = _filename_log(output_file, nofpass)
            try:
                log_file_handle = open(log_file_name, 'w')
            except IOError:
                message_fnc("Error creating %s" % log_file_name)
                update_fnc("Error creating logfile")
                return 0
            ## Build command for FFMPEG
            command = build_command(nofpass)
            ## Start encoding, result will define to continue or not to
            no_error = encode(command)
    ## !!! Status Update
    return no_error

def propose_resolutions(video_file, display_aspect=None, res_16_9=['1920x1080', '1280x720', '854x480', '640x360'], res_4_3=['640x480'], lq_fallback=True):
    """ Returns a list of possible resolutions that would work with the given
    video, based on its own resultion ans aspect ratio

    @ param display_aspect: Sets the display aspect ratio for videos where
    this might not be detectable
    @param res_16_9: Possible resolutions to select from for 16:9 videos
    @param res_4_3: Possible resolutions to select from for 4:3 videos
    @param lq_fallback: Return the videos own resultion if none of the given fits
    """
    def eq(a,b):
        if abs(a-b) < 0.01:
            return 1
        else:
            return 0

    def get_smaler_or_equal_res(height, avail_res):
        smaler_res = []
        for res in avail_res:
            vres = int(res.split('x')[1])
            if vres <= height:
                smaler_res.append(res)
        return smaler_res

    def get_res_for_weird_aspect(width, aspect, avail_res):
        smaler_res = []
        for res in avail_res:
            hres, vres = res.split('x')
            hres = int(hres)
            vres = int(vres)
            if hres <= width:
                height = hres * (1.0 / aspect)
                if height % 2 != 0:
                    height = height-1
                smaler_res.append(str(hres) + 'x' + str(int(height)))
        return smaler_res

    meta_dict = ffprobe_metadata(video_file)
    for stream in meta_dict['streams']:
        if stream['codec_type'] == 'video':
            width = int(stream['width'])
            height = int(stream['height'])
            # If the display aspect ratio is in the meta, we can even override
            # the ratio that was given to the function as a fallback
            # But the information in the file could be wrong ...
            # Which information is trustful?
            if 'display_aspect_ratio' in stream:
                display_aspect = stream['display_aspect_ratio']
            break
    # Calculate the aspect factors
    if display_aspect == None:
        # Assume square pixels
        display_aspect = float(width) / float(height)
    else:
        asp_w, asp_h = display_aspect.split(':')
        display_aspect = float(asp_w) / float(asp_h)
    # Check if 16:9
    if eq(display_aspect, 1.77):
        possible_res = get_smaler_or_equal_res(height, res_16_9)
    # Check if 4:3
    elif eq(display_aspect, 1.33):
        possible_res = get_smaler_or_equal_res(height, res_4_3)
    # Weird aspect
    else:
        possible_res = get_res_for_weird_aspect(width, display_aspect, res_16_9)
    # If the video is crap
    if not possible_res and lq_fallback:
        return [str(width) + 'x' + str(height)]
    else:
        return possible_res
