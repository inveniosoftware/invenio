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

"""BibEncode metadata submodule.
Metadata insertion, extraction and processing for video files.
"""

__revision__ = "$Id$"

import subprocess
import re
from six import iteritems
from xml.dom import minidom

from invenio.utils.json import json, json_decode_file
from invenio.legacy.bibsched.bibtask import write_message
from invenio.modules.encoder.config import (
                        CFG_BIBENCODE_FFMPEG_METADATA_ARGUMENT,
                        CFG_BIBENCODE_FFMPEG_METADATA_SET_COMMAND,
                        CFG_BIBENCODE_PBCORE_MAPPINGS
                        )
from invenio.modules.encoder.utils import probe, getval, mediainfo, seconds_to_timecode

# Stores metadata for the process. Many different functions in BibEncode
# need access to video metadata regularly. Because we dont pass objects arount
# we need to call the functions of this submodule again and again. To not
# call ffprobe and mediainfo all the time, the metadata is stored in this cache.
_FFPROBE_METADATA_CACHE = {}
_MEDIAINFO_METADATA_CACHE = {}

def write_metadata(input_file, output_file, metadata):
    """Writes metadata to a copy of the given input file.
    The metadata must be a dictionary that contains valid key-value pairs.
    Valid keys are defined in CFG_BIBENCODE_FFMPEG_METADATA_TEMPLATE.
    @param input_file: The original video path
    @param outout_file: The path to the copy with the new metadata
    @param metadata: The metadata dictionary to write to the video
    """
    meta_args = []
    if type(metadata) is dict:
        ## build metadata arguments for ffmpeg
        for key, value in iteritems(metadata):
            if value is not None:
                meta_args.append(CFG_BIBENCODE_FFMPEG_METADATA_ARGUMENT % (key, value))
    else:
        write_message("metadata arg no dict")
        return 0
    ## build the command
    command = (CFG_BIBENCODE_FFMPEG_METADATA_SET_COMMAND % (input_file, output_file)).split()
    for meta_arg in meta_args:
        command.insert(-1, '-metadata')
        command.insert(-1, meta_arg)
    write_message(command)
    process = subprocess.Popen(command, stderr=subprocess.PIPE)
    stderr = []
    while process.poll() is None:
        ## We want to keep the last lines of output in case of an error
        stderr += process.communicate()[1].splitlines()
        stderr = stderr[-5:]
    if process.poll() == -15:
        write_message("terminated")
        return 0
    if process.poll() == 1:
        ## If there was an error during FFmpeg execution, write log
        write_message("There was en error with FFmpeg writing metadata")
        write_message("Below the last lines of the FFmpeg log:")
        for line in stderr:
            write_message(line)
        return 0
    if process.poll() == 0:
        write_message("went fine")
        return 1

def dump_metadata(input_file, output_file, meta_type="ffprobe"):
    """Dumps the metadata from a given video to the given file
    The output will be in JSON or XML
    @param input_file: Full path to the video
    @param output_file: Full path to the JSON dump file
    @param type: Metadata style/library to use,
                 either ffprobe, mediainfo or pbcore
    """
    metadata_dict = None
    if not meta_type in ('ffprobe', 'mediainfo', 'pbcore'):
        raise ValueError("Type must be ffprobe, pbcore or mediainfo")
    if meta_type == 'ffprobe':
        metadata_dict = ffprobe_metadata(input_file)
    elif meta_type == 'mediainfo':
        metadata_dict = mediainfo_metadata(input_file)
    if metadata_dict is not None:
        metadata_string = json.dumps(metadata_dict, sort_keys=True, indent=4)
        file = open(output_file, "w")
        file.write(metadata_string)
        file.close()
    ## Dump PBCORE
    else:
        pbcore = pbcore_metadata(input_file)
        file = open(output_file, "w")
        file.write(pbcore)
        file.close()

def ffprobe_metadata(input_file):
    """This function uses pretty and parsable ffmpeg output to
    access all the metadata of a videofile correctly
    @param input_file: fullpath to the  media file
    @type input_file: string
    @return: a dictionary containing the metadata
    @rtype: dictionary
    """
    global _FFPROBE_METADATA_CACHE
    if input_file in _FFPROBE_METADATA_CACHE:
        return _FFPROBE_METADATA_CACHE[input_file]

    ffprobe_output = probe(input_file, True)
    if ffprobe_output is None:
        return None
    meta_dict = {
                 'format': {},
                 'streams': []
                 }
    format_start = re.compile("^\[FORMAT\]$")
    format_end = re.compile("^\[\/FORMAT\]$")
    stream_start = re.compile("^\[STREAM\]$")
    stream_end = re.compile("^\[\/STREAM\]$")
    lines = ffprobe_output.splitlines()
    format_section = False
    stream_section = False
    for line in lines:
        if format_start.match(line):
            format_section = True
            continue
        if format_end.match(line):
            format_section = False
            continue
        if stream_start.match(line):
            meta_dict['streams'].append(dict())
            stream_section = True
            continue
        if stream_end.match(line):
            stream_section = False
            continue
        if format_section:
            key, value = line.split("=", 1)
            meta_dict['format'][key] = value
        if stream_section:
            key, value = line.split("=", 1)
            meta_dict['streams'][-1][key] = value
    _FFPROBE_METADATA_CACHE[input_file] = meta_dict
    return meta_dict

def mediainfo_metadata(input_file, aspect_override=None):
    """Uses the mediainfo library instead of ffprobe to access metadata
    @param input_file: fullpath to the  media file
    @type input_file: string
    @return: a list of dictionaries containing the metadata
    @rtype: list
    """

    global _MEDIAINFO_METADATA_CACHE
    if input_file in _MEDIAINFO_METADATA_CACHE:
        return _MEDIAINFO_METADATA_CACHE[input_file]

    meta_list = []
    mediainfo_output = mediainfo(input_file)
    dom = minidom.parseString(mediainfo_output)
    for track in dom.getElementsByTagName('track'):
        track_dict = {}
        last_seen_tag = ""
        for node in track.childNodes:
            try:
                if last_seen_tag != node.tagName or node.tagName == "Display_aspect_ratio":
                    track_dict[node.tagName.encode('ascii').lower()] = " ".join(t.nodeValue for t in node.childNodes if t.nodeType == t.TEXT_NODE).encode('ascii')
                last_seen_tag = node.tagName.encode('ascii')
            except:
                pass
            if 'display_aspect_ratio' in track_dict and aspect_override:
                track_dict['display_aspect_ratio'] = aspect_override
        meta_list.append(track_dict)
    _MEDIAINFO_METADATA_CACHE[input_file] = meta_list
    return meta_list

def pbcore_metadata(input_file, pbcoreIdentifier=None, pbcoreTitle=None,
                    pbcoreDescription=None, instantiationIdentifier=None,
                    instantiationPhysical=None, instantiationLocation=None,
                    instantiationGenerations=None,instantiationExtension=None,
                    instantiationPart=None, instantiationAnnotation=None,
                    instantiationRights=None, instantiationRelation=None,
                    xmlns="pbcore", aspect_override=None
                    ):
    """ Transformes parsed metadata to a pbcore representation.
    To supplement all the pbcore field, we need both ffprobe and mediainfo.
    If only ffprobe is installed, it will not fail but supplement only partially.
    @param input_file: full path to the file to extract the metadata from
    @type input_file: string
    @return: pbcore xml metadata representation
    @rtype: string
    """

    def _follow_path(path, locals_u, meta_dict, probe_dict, stream_number=None):
        """
        Trys to follow a given path and returns the value it represents.
        The path is a string that must be like this:
            local->variable_name
            ffprobe->format->param
            ffprobe->video->param
            ffprobe->audio->param
            ffprobe->stream->param
            mediainfo->general->param
            mediainfo->audio->param
            mediainfo->video->param
            mediainfo->track->param

        @param path: Path to the value
        @type: string
        @param locals_u: Local variables
        @type locals_u: dict
        @param meta_dict: Mediainfo metadata
        @type meta_dict: dict
        @param probe_dict: FFprobe metadata
        @type probe_dict: dict
        @param stream_number: To follow a path to a specific stream
        @type stream_number: int
        @return: value of the element the path points to
        @rtype: string
        """
        path_segments = path.split("->")
        ## ffprobe
        if path_segments[0] == 'ffprobe':
            ## format
            if path_segments[1] == 'format':
                return getval(probe_dict['format'], path_segments[2], 0)
            ## 1st video
            elif path_segments[1] in ('video', 'audio'):
                for stream in probe_dict['streams']:
                    if getval(stream, 'codec_type') == path_segments[1]:
                        return getval(stream, path_segments[2], 0)
            ## stream by number
            elif path_segments[1] == 'stream':
                return getval(probe_dict['streams'][stream_number],
                              path_segments[2], 0)
        ## mediainfo
        elif path_segments[0] == 'mediainfo':
            ## general, video, audio
            if path_segments[1] in ('general', 'video', 'audio'):
                for track in meta_dict:
                    if getval(track, 'kind_of_stream').lower() == path_segments[1]:
                        return getval(track, path_segments[2], 0)
            ## stream by number
            elif path_segments[1] == 'track':
                ## We rely on format being the first track in mediainfo
                ## And the order of streams in ffprobe and tracks in mediainfo being the same
                return getval(meta_dict[stream_number+1], path_segments[2], 0)
        ## local variable
        elif path_segments[0] == 'local':
            return getval(locals_u, path_segments[1], 0)
        ## direct input
        else:
            return path_segments[0]

    def _map_values(mapping, locals_u, meta_dict, probe_dict, stream_number=None):
        """ substitute a mapping dictionary an returns the substituted value.
        The dictionary must contain of a 'tag' a 'mapping' and a 'call'

        @param mapping: mapping dictionary to substitute
        @type: dict
        @param locals_u: Local variables
        @type locals_u: dict
        @param meta_dict: Mediainfo metadata
        @type meta_dict: dict
        @param probe_dict: FFprobe metadata
        @type probe_dict: dict
        @param stream_number: To follow a path to a specific stream
        @type stream_number: int
        @return: substituted mapping
        @rtype: string
        """
        items = []
        for value in mapping:
            mapping = value['mapping']
            tag = value['tag']
            call = getval(value, 'call')
            micro_mappings = mapping.split(';;')
            values = []
            foundall = True
            for micro_mapping in micro_mappings:
                value = _follow_path(micro_mapping, locals_u, meta_dict, probe_dict, stream_number)
                if value:
                    if call:
                        value = globals()[call](value)
                    values.append(value.strip())
                else:
                    foundall &= False
            try:
                if values and foundall:
                    items.append(tag % "".join(values))
            except:
                pass
        return items

    ## Get the metadata from ffprobe and mediainfo
    meta_dict = mediainfo_metadata(input_file, aspect_override)
    probe_dict = ffprobe_metadata(input_file)

    # parse the mappings
    pbcore_mappings = json_decode_file(CFG_BIBENCODE_PBCORE_MAPPINGS)

    ## INSTANTIATION ##
    # According to the PBcore standard, this strict order MUST be followed
    instantiation_mapping = pbcore_mappings['instantiation_mapping']

    ## ESSENCE TRACK ##
    # According to the PBcore standard, this strict order MUST be followed
    essencetrack_mapping = pbcore_mappings['essencetrack_mapping']

    ## The XML header for the PBcore document
    header = (
    """<?xml version="1.0" encoding="UTF-8"?><pbcoreDescriptionDocument """
    """xmlns%(xmlns)s="http://www.pbcore.org/PBCore/PBCoreNamespace.html" """
    """xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" """
    """xsi:schemaLocation="http://www.pbcore.org/PBCore/PBCoreNamespace.html">"""
    )
    if pbcoreIdentifier:
        pbcoreIdentifier ="""<pbcoreIdentifier>%s</pbcoreIdentifier>""" % pbcoreIdentifier
    else:
        pbcoreIdentifier = ""
    if pbcoreTitle:
        pbcoreTitle = """<pbcoreTitle>%s</pbcoreTitle>""" % pbcoreTitle
    else:
        pbcoreTitle = ""
    tail = """</pbcoreDescriptionDocument>"""

    ## ESSENCE TRACKS ##
    essencetracks = []
    for stream_no in range(len(probe_dict['streams'])):
        essencetracks.append(_map_values(essencetrack_mapping, locals(),
                                         meta_dict, probe_dict, stream_no))
    joinedtracks = []
    for track in essencetracks:
        track = "<instantiationEssenceTrack>" + "".join(track) + "</instantiationEssenceTrack>"
        joinedtracks.append(track)
    joinedtracks = "".join(joinedtracks)

    ## INSTANTIATION ##
    instantiation_items = _map_values(instantiation_mapping, locals(),
                                      meta_dict, probe_dict)
    joinedinstantiation = "<pbcoreInstantiation>" + "".join(instantiation_items) + "</pbcoreInstantiation>"

    joined = "%s%s%s%s%s" % (header, pbcoreIdentifier, pbcoreTitle,
                           joinedinstantiation, tail)

    if xmlns:
        joined = joined % {"xmlns" : ":%s" % xmlns}
        joined = re.sub("<(\w[^>]+)>", "<%s:\g<1>>" % xmlns, joined)
        joined = re.sub("<\/([^>]+)>", "</%s:\g<1>>" % xmlns, joined)
    else:
        joined = joined % {"xmlns" : ""}

    return joined

