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

"""Unit tests for BibEncode.
* Please run conversion_for_unit_tests.py
  before you run the tests for the first time!
"""

__revision__ = "$Id$"

from invenio.base.globals import cfg
from invenio.utils.url import make_invenio_opener
from os.path import basename
import os
from six.moves.urllib.parse import urlsplit
import shutil
import urllib2

from invenio.base.wrappers import lazy_import
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase

bibencode_utils = lazy_import('invenio.modules.encoder.utils')
bibencode_encode = lazy_import('invenio.modules.encoder.encode')
bibencode_metadata = lazy_import('invenio.modules.encoder.metadata')


def url2name(url):
    return basename(urlsplit(url)[2])


class Video(object):

    def __init__(self, url):
        self.url = url
        self.name = url2name(url)

    @property
    def source(self):
        return cfg['CFG_TMPDIR'] + "/blue_sky_1080p25.y4m"

    @property
    def out01(self):
        return cfg['CFG_TMPDIR'] + "/blue_sky_1080p.mp4"

    @property
    def out02(self):
        return cfg['CFG_TMPDIR'] + "/blue_sky_1080p.ogg"

    @property
    def out03(self):
        return cfg['CFG_TMPDIR'] + "/blue_sky_1080p.webm"

    @property
    def out04(self):
        return cfg['CFG_TMPDIR'] + "/blue_sky_720p.mp4"

    @property
    def out05(self):
        return cfg['CFG_TMPDIR'] + "/blue_sky_720p.ogg"

    @property
    def out06(self):
        return cfg['CFG_TMPDIR'] + "/blue_sky_720p.webm"

    @property
    def out07(self):
        return cfg['CFG_TMPDIR'] + "/blue_sky_480p.mp4"

    @property
    def out08(self):
        return cfg['CFG_TMPDIR'] + "/blue_sky_480p.ogg"

    @property
    def out09(self):
        return cfg['CFG_TMPDIR'] + "/blue_sky_480p.webm"

    @property
    def movie_no_aspect(self):
        return cfg['CFG_TMPDIR'] + "/blue_sky_1080p_anamorphic.webm"

video01 = Video("http://media.xiph.org/video/derf/y4m/blue_sky_1080p25.y4m")


metadata = {
        "title": "Super Duper Difficult Test Metadata Video File",
        "author": "Invenio Author",
        "album_artist": "Invenio Album Artist",
        "album": "Invenio Album",
        "grouping": "Invenio Grouping",
        "composter": "Invenio Composer",
        "year": "2011",
        "track": "42",
        "comment": "Invenio Comment",
        "genre": "Invenio Genre",
        "copyright": "Invenio Copyright",
        "description": "Invenio Description",
        "synopsis": "Invenio Synopsis",
        "show": "Invenio Show",
        "episode_id": "S04x42",
        "network": "Invenio Network",
        "lyrics": "Invenio Lyrics",
        }


def download(url, localFileName = None):
    """ Downloads a file from a remote url
    """
    localName = url2name(url)
    req = urllib2.Request(url)
    r = make_invenio_opener('BibEncode').open(req)
    if 'Content-Disposition' in r.info():
        # If the response has Content-Disposition, we take file name from it
        localName = r.info()['Content-Disposition'].split('filename=')[1]
        if localName[0] == '"' or localName[0] == "'":
            localName = localName[1:-1]
    elif r.url != url:
        # if we were redirected, the real file name we take from the final URL
        localName = url2name(r.url)
    if localFileName:
        # we can force to save the file as specified name
        localName = localFileName
    f = open(localName, 'wb')
    shutil.copyfileobj(r, f)
    f.close()

def printr(message):
    """ Print with carriage return
    """
    print("\r" + message)

class SetupTester(InvenioTestCase):
    """Prepares the necessary files for the tests"""
    def test_setUp(self):
        if not os.path.exists(video01.source):
            print("Downloading sample video ... ")
            download(video01.url, video01.source)

        print("Starting encoding ... ")
        from invenio.modules.encoder.encode import encode_video
        self.assertEqual(encode_video(video01.source, video01.out01, "libfaac", "libx264", 128000, 8000000, "1920x1080", 1, "-vpre medium", metadata=metadata, update_fnc=printr), 1)
        self.assertEqual(encode_video(video01.source, video01.out02, "libvorbis", "libtheora", 128000, 8000000, "1920x1080", 1, metadata=metadata, update_fnc=printr), 1)
        self.assertEqual(encode_video(video01.source, video01.out03, "libvorbis", "libvpx", 128000, 8000000, "1920x1080", 1, "-g 320 -qmax 63",  metadata=metadata, update_fnc=printr), 1)
        self.assertEqual(encode_video(video01.source, video01.out04, "libfaac", "libx264", 128000, 4000000, "1280x720", 1, "-vpre medium", metadata=metadata, update_fnc=printr), 1)
        self.assertEqual(encode_video(video01.source, video01.out05, "libvorbis", "libtheora", 128000, 4000000, "1280x720", 1, metadata=metadata, update_fnc=printr), 1)
        self.assertEqual(encode_video(video01.source, video01.out06, "libvorbis", "libvpx", 128000, 4000000, "1280x720", 1, "-g 320 -qmax 63", metadata=metadata, update_fnc=printr), 1)
        self.assertEqual(encode_video(video01.source, video01.out07, "libfaac", "libx264", 128000, 2000000, "852x480", 1, "-vpre medium", metadata=metadata, update_fnc=printr), 1)
        self.assertEqual(encode_video(video01.source, video01.out08, "libvorbis", "libtheora", 128000, 2000000, "854x480", 1, metadata=metadata, update_fnc=printr), 1)
        self.assertEqual(encode_video(video01.source, video01.out09, "libvorbis", "libvpx", 128000, 2000000, "852x480", 1, "-g 320 -qmax 63", metadata=metadata, update_fnc=printr), 1)
        self.assertEqual(encode_video(video01.source, video01.movie_no_aspect, "libvorbis", "libvpx", 128000, 8000000, "1440x1080", 1, "-g 320 -qmax 63",  metadata=metadata, update_fnc=printr), 1)

        print("Starting frame extraction ...")
        from invenio.modules.encoder.extract import extract_frames
        self.assertEqual(extract_frames(video01.out01, output_file=cfg['CFG_TMPDIR'] + "/testframes1_", size=None, positions=None, numberof=10, extension='jpg', width=None, height=None, aspect=None, profile=None, update_fnc=printr, message_fnc=printr), 1)
        self.assertEqual(extract_frames(video01.out01, output_file=cfg['CFG_TMPDIR'] + "/testframes2_", size="640x360", positions=None, numberof=10, extension='jpg', width=None, height=None, aspect=None, profile=None, update_fnc=printr, message_fnc=printr), 1)
        self.assertEqual(extract_frames(video01.out01, output_file=cfg['CFG_TMPDIR'] + "/testframes3_", size=None, positions=None, numberof=10, extension='jpg', width=640, height=None, aspect=None, profile=None, update_fnc=printr, message_fnc=printr), 1)
        self.assertEqual(extract_frames(video01.out01, output_file=cfg['CFG_TMPDIR'] + "/testframes4_", size=None, positions=None, numberof=10, extension='jpg', width=None, height=360, aspect=None, profile=None, update_fnc=printr, message_fnc=printr), 1)
        self.assertEqual(extract_frames(video01.out01, output_file=cfg['CFG_TMPDIR'] + "/testframes5_", size=None, positions=None, numberof=10, extension='jpg', width=640, height=360, aspect=None, profile=None, update_fnc=printr, message_fnc=printr), 1)
        self.assertEqual(extract_frames(video01.out01, output_file=cfg['CFG_TMPDIR'] + "/testframes6_", size=None, positions=[1, 5, 10, 15, 20], numberof=None, extension='jpg',  width=None, height=None, aspect=None, profile=None, update_fnc=printr, message_fnc=printr), 1)
        self.assertEqual(extract_frames(video01.out01, output_file=cfg['CFG_TMPDIR'] + "/testframes7_", size=None, positions=["00:00:01.00", "00:00:02.00","00:00:03.00", "00:00:04.00", "00:00:05.00"], numberof=None, extension='jpg', width=None, height=None, aspect=None, profile=None, update_fnc=printr, message_fnc=printr), 1)
        self.assertEqual(extract_frames(video01.out01, output_file=cfg['CFG_TMPDIR'] + "/testframes8_", size=None, positions=["00:00:01.00", 5,"00:00:03.00", 10, "00:00:05.00"], numberof=None, extension='jpg',  width=None, height=None, aspect=None, profile=None, update_fnc=printr, message_fnc=printr), 1)

        print("All done")


class TestFFmpegMinInstallation(InvenioTestCase):
    """Tests if the minimum FFmpeg installation is available"""

    def test_ffmpeg(self):
        self.assertEqual(bibencode_utils.check_ffmpeg_configuration(), None)


class TestUtilsFunctions(InvenioTestCase):
    """Tests the utility functions in bibencode_utils"""

    def test_timcode_to_seconds(self):
        """Convert timecode to seconds"""
        self.assertEqual(bibencode_utils.timecode_to_seconds("00:00:00"),0.0)
        self.assertEqual(bibencode_utils.timecode_to_seconds("00:00:00.00"),0.0)
        self.assertEqual(bibencode_utils.timecode_to_seconds("00:00:00.10"),0.1)
        self.assertEqual(bibencode_utils.timecode_to_seconds("00:00:01.00"),1.0)
        self.assertEqual(bibencode_utils.timecode_to_seconds("00:00:00.01"),0.01)
        self.assertEqual(bibencode_utils.timecode_to_seconds("00:00:10"),10.0)
        self.assertEqual(bibencode_utils.timecode_to_seconds("00:10:10"),610.0)
        self.assertEqual(bibencode_utils.timecode_to_seconds("10:10:10"),36610.0)
        self.assertEqual(bibencode_utils.timecode_to_seconds("10:10:10.10"),36610.10)

    def test_seconds_to_timecode(self):
        """Convert seconds to timecode"""
        self.assertEqual(bibencode_utils.seconds_to_timecode(0.0),"00:00:00.00")
        self.assertEqual(bibencode_utils.seconds_to_timecode(0.1),"00:00:00.10")
        self.assertEqual(bibencode_utils.seconds_to_timecode(1.0),"00:00:01.00")
        self.assertEqual(bibencode_utils.seconds_to_timecode(1.1),"00:00:01.10")
        self.assertEqual(bibencode_utils.seconds_to_timecode(10.0),"00:00:10.00")
        self.assertEqual(bibencode_utils.seconds_to_timecode(610.0),"00:10:10.00")
        self.assertEqual(bibencode_utils.seconds_to_timecode(36610.0),"10:10:10.00")
        self.assertEqual(bibencode_utils.seconds_to_timecode(36610.10),"10:10:10.10")
        self.assertEqual(bibencode_utils.seconds_to_timecode(36601.10),"10:10:01.10")
        self.assertEqual(bibencode_utils.seconds_to_timecode(36600.10),"10:10:00.10")
        self.assertEqual(bibencode_utils.seconds_to_timecode("36600.10"),"10:10:00.10")

    def test_is_seconds(self):
        """Tests if given value is seconds like"""
        self.assertEqual(bibencode_utils.is_seconds(1), True)
        self.assertEqual(bibencode_utils.is_seconds(1.1), True)
        self.assertEqual(bibencode_utils.is_seconds("1"), True)
        self.assertEqual(bibencode_utils.is_seconds("1.1"), True)
        self.assertEqual(bibencode_utils.is_seconds("11.11"), True)
        self.assertEqual(bibencode_utils.is_seconds("1s"), False)
        self.assertEqual(bibencode_utils.is_seconds("1.1s"), False)
        self.assertEqual(bibencode_utils.is_seconds(""), False)

    def test_is_timecode(self):
        """Test if given value is a timecode"""
        self.assertEqual(bibencode_utils.is_timecode("00:00:00"), True)
        self.assertEqual(bibencode_utils.is_timecode("00:00:00.00"), True)
        self.assertEqual(bibencode_utils.is_timecode("00:00:00.0"), True)
        self.assertEqual(bibencode_utils.is_timecode("00:00:00.000"), True)
        self.assertEqual(bibencode_utils.is_timecode("00:00:0.0"), False)
        self.assertEqual(bibencode_utils.is_timecode("00:00"), False)
        self.assertEqual(bibencode_utils.is_timecode("00:00.00"), False)
        self.assertEqual(bibencode_utils.is_timecode("00"), False)
        self.assertEqual(bibencode_utils.is_timecode("0"), False)
        self.assertEqual(bibencode_utils.is_timecode("00.00"), False)
        self.assertEqual(bibencode_utils.is_timecode("0.0"), False)

    def test_aspect_string_to_float(self):
        """Tests if string contains an aspect ratio"""
        self.assertAlmostEqual(bibencode_utils.aspect_string_to_float("4:3"), 1.333, places=2)
        self.assertAlmostEqual(bibencode_utils.aspect_string_to_float("16:9"), 1.777, places=2)


class TestEncodeFunctions(InvenioTestCase):
    """Tests the functions of bibencode_encode"""

    def test_determine_aspect(self):
        """Tests if the aspect is correctly detected"""
        self.assertEqual(bibencode_encode.determine_aspect(video01.out02), ("16:9", 1920, 1080))
        self.assertEqual(bibencode_encode.determine_aspect(video01.out05), ("16:9", 1280, 720))
        self.assertEqual(bibencode_encode.determine_aspect(video01.out08), ("427:240", 854, 480))

    def test_determine_resolution(self):
        """Tests if the resolution is correctly calculated"""
        # The aspect is fully detectable in the video
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.out03, 1920, 1080, None), "1920x1080")
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.out03, 1280, 720, None), "1280x720")
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.out03, 854, 480, None), "854x480")
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.out03, 1920, None, None), "1920x1080")
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.out03, 1280, None, None), "1280x720")
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.out03, 854, None, None), "854x480")
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.out03, None, 1080, None), "1920x1080")
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.out03, None, 720, None), "1280x720")
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.out03, None, 480, None), "854x480")
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.out03, 1920, 1080, 1.777), "1920x1080")
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.out03, 1280, 720, 1.777), "1280x720")
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.out03, 854, 480, 1.78), "854x480")
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.out03, 1920, None, 1.777), "1920x1080")
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.out03, 1280, None, 1.777), "1280x720")
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.out03, 854, None, 1.78), "854x480")
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.out03, None, 1080, 1.777), "1920x1080")
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.out03, None, 720, 1.777), "1280x720")
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.out03, None, 480, 1.78), "854x480")
        # The aspect is not detectable in the video
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.movie_no_aspect, 1920, 1080, None), "1440x1080")
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.movie_no_aspect, 1280, 720, None), "960x720")
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.movie_no_aspect, 854, 480, None), "640x480")
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.movie_no_aspect, 1920, None, None), "1920x1440")
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.movie_no_aspect, 1280, None, None), "1280x960")
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.movie_no_aspect, 854, None, None), "854x640")
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.movie_no_aspect, None, 1080, None), "1440x1080")
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.movie_no_aspect, None, 720, None), "960x720")
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.movie_no_aspect, None, 480, None), "640x480")
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.movie_no_aspect, 1920, 1080, 1.777), "1920x1080")
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.movie_no_aspect, 1280, 720, 1.777), "1280x720")
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.movie_no_aspect, 854, 480, 1.78), "854x480")
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.movie_no_aspect, 1920, None, 1.777), "1920x1080")
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.movie_no_aspect, 1280, None, 1.777), "1280x720")
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.movie_no_aspect, 854, None, 1.78), "854x480")
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.movie_no_aspect, None, 1080, 1.777), "1920x1080")
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.movie_no_aspect, None, 720, 1.777), "1280x720")
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.movie_no_aspect, None, 480, 1.78), "854x480")
        # Alternative aspect notation
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.movie_no_aspect, 1920, 1080, "16:9"), "1920x1080")
        self.assertEqual(bibencode_encode.determine_resolution_preserving_aspect(video01.movie_no_aspect, 1920, 1080, "4:3"), "1440x1080")

    def test_assure_quality(self):
        """ Test if the quality is detected correctly"""
        self.assertEqual(bibencode_encode.assure_quality(video01.out03, None, 1920, 1080, 6000000, True, 1.0), True)
        self.assertEqual(bibencode_encode.assure_quality(video01.out03, None, 1280, 720, 6000000, True, 1.0), True)
        self.assertEqual(bibencode_encode.assure_quality(video01.out03, None, 4443, 2500, 6000000, True, 1.0), False)
        self.assertEqual(bibencode_encode.assure_quality(video01.out03, None, 1280, 720, 10000000, True, 1.0), False)
        self.assertEqual(bibencode_encode.assure_quality(video01.out03, None, 1920, 1080, 10000000, True, 1.0), False)
        self.assertEqual(bibencode_encode.assure_quality(video01.out03, None, 1920, 1080, 6000000, True, 1.0), True)
        self.assertEqual(bibencode_encode.assure_quality(video01.out03, None, None, 720, 6000000, True, 1.0), True)
        self.assertEqual(bibencode_encode.assure_quality(video01.out03, None, None, 2500, 6000000, True, 1.0), False)
        self.assertEqual(bibencode_encode.assure_quality(video01.out03, None, None, 720, 10000000, True, 1.0), False)
        self.assertEqual(bibencode_encode.assure_quality(video01.out03, None, None, 1080, 10000000, True, 1.0), False)
        self.assertEqual(bibencode_encode.assure_quality(video01.out03, None, 1920, None, None, True, 1.0), True)
        self.assertEqual(bibencode_encode.assure_quality(video01.out03, None, 1280, None, None, True, 1.0), True)
        self.assertEqual(bibencode_encode.assure_quality(video01.out03, None, 4443, None, None, True, 1.0), False)
        self.assertEqual(bibencode_encode.assure_quality(video01.out03, None, None, None, 10000000, True, 1.0), False)
        self.assertEqual(bibencode_encode.assure_quality(video01.out03, None, None, None, 6000000, True, 1.0), True)
        self.assertEqual(bibencode_encode.assure_quality(video01.out03, None, 800, 600, 6000000, True, 1.0), True)
        self.assertEqual(bibencode_encode.assure_quality(video01.out03, "4:3", 800, 600, 6000000, True, 1.0), True)
        self.assertEqual(bibencode_encode.assure_quality(video01.out03, "4:3", 1440, 1080, 6000000, True, 1.0), True)
        self.assertEqual(bibencode_encode.assure_quality(video01.out03, 1.333333333333333333, 800, 600, 6000000, True, 1.0), True)
        self.assertEqual(bibencode_encode.assure_quality(video01.out03, 1.333333333333333333, 1440, 1080, 6000000, True, 1.0), True)
        self.assertEqual(bibencode_encode.assure_quality(video01.out03, 1.333, 800, 600, 6000000, True, 0.95), True)
        self.assertEqual(bibencode_encode.assure_quality(video01.out03, 1.333, 1440, 1080, 6000000, True, 0.95), True)
        self.assertEqual(bibencode_encode.assure_quality(video01.out03, None, 800, 600, 6000000, True, 0.95), True)
        self.assertEqual(bibencode_encode.assure_quality(video01.out03, None, 1440, 1080, 6000000, True, 0.95), True)
        self.assertEqual(bibencode_encode.assure_quality(video01.out03, 1.333, 800, 600, 6000000, False, 1.0), True)
        self.assertEqual(bibencode_encode.assure_quality(video01.out03, 1.333, 1440, 1080, 6000000, False, 1.0), True)

        self.assertEqual(bibencode_encode.assure_quality(video01.movie_no_aspect, None, 800, 600, 6000000, False, 1.0), True)
        self.assertEqual(bibencode_encode.assure_quality(video01.movie_no_aspect, None, 1440, 1080, 6000000, False, 1.0), True)
        self.assertEqual(bibencode_encode.assure_quality(video01.movie_no_aspect, None, 1920, 1080, 6000000, False, 1.0), False)
        self.assertEqual(bibencode_encode.assure_quality(video01.movie_no_aspect, None, 1920, 1080, 6000000, True, 1.0), False)
        self.assertEqual(bibencode_encode.assure_quality(video01.movie_no_aspect, "16:9", 1920, 1080, 6000000, False, 1.0), False)
        self.assertEqual(bibencode_encode.assure_quality(video01.movie_no_aspect, "16:9", 1920, 1080, 6000000, True, 1.0), True)


class TestExtractFunctions(InvenioTestCase):
    """Tests the functions of bibencode_extract"""
    pass


class TestMetadataFunctions(InvenioTestCase):
    """Tests the functions of bibencode_metadata"""

    def test_ffrobe_metadata(self):
        """Test if ffprobe metadata outputs correctly"""
        metadata_check = {
            'format': {'TAG:album': '"Invenio Album"',
            'TAG:album_artist': '"Invenio Album Artist"',
            'TAG:comment': '"Invenio Comment"',
            'TAG:compatible_brands': 'isomiso2avc1mp41',
            'TAG:copyright': '"Invenio Copyright"',
            'TAG:creation_time': '1970-01-01 00:00:00',
            'TAG:description': '"Invenio Description"',
            'TAG:encoder': 'Lavf53.1.0',
            'TAG:episode_id': '"S04x42"',
            'TAG:genre': '"Invenio Genre"',
            'TAG:grouping': '"Invenio Grouping"',
            'TAG:lyrics': '"Invenio Lyrics"',
            'TAG:major_brand': 'isom',
            'TAG:minor_version': '512',
            'TAG:network': '"Invenio Network"',
            'TAG:show': '"Invenio Show"',
            'TAG:synopsis': '"Invenio Synopsis"',
            'TAG:title': '"Super Duper Difficult Test Metadata Video File"',
            'bit_rate': '7606651.000000 ',
            'duration': '10.000000 ',
            'filename': '/home/oldi/videos/park_joy_1080p.mp4',
            'format_long_name': 'QuickTime/MPEG-4/Motion JPEG 2000 format',
            'format_name': 'mov,mp4,m4a,3gp,3g2,mj2',
            'nb_streams': '1',
            'size': '9508314.000000 ',
            'start_time': '0.000000 '},
            'streams': [{'TAG:creation_time': '1970-01-01 00:00:00',
              'TAG:language': 'und',
              'avg_frame_rate': '50/1',
              'codec_long_name': 'H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10',
              'codec_name': 'h264',
              'codec_tag': '0x31637661',
              'codec_tag_string': 'avc1',
              'codec_time_base': '1/100',
              'codec_type': 'video',
              'display_aspect_ratio': '30:17',
              'duration': '10.000000 ',
              'has_b_frames': '2',
              'height': '1088',
              'index': '0',
              'nb_frames': '500',
              'pix_fmt': 'yuv420p',
              'r_frame_rate': '50/1',
              'sample_aspect_ratio': '1:1',
              'start_time': '0.000000 ',
              'time_base': '1/50',
              'width': '1920'}]}
        self.assertEqual(bibencode_metadata.ffprobe_metadata(video01.out01), metadata_check)


class TestBatchEngineFunctions(InvenioTestCase):
    """Tests the functions of bibencode_batch_engine"""
    pass


class TestDaemonFunctions(InvenioTestCase):
    """Tests the functions of bibencode_daemon"""
    pass


TEST_SUITE = make_test_suite(SetupTester,
                             TestUtilsFunctions,
                             TestEncodeFunctions,
                             TestExtractFunctions,
                             ## TestMetadataFunctions,
                             TestBatchEngineFunctions,
                             TestDaemonFunctions)

if __name__ == "__main__":
    from invenio.utils.text import wait_for_user
    wait_for_user("""
    #######################################################
    # This is the test suite for the BibEncode module     #
    #                                                     #
    # You need to have installed ffmpeg with H.264, WebM  #
    # and Theora support! Please see the manual!          #
    #                                                     #
    # Please be aware that not every aspect can be tested #
    # due to the nature of video encoding and wrapping    #
    # external libraries like ffmpeg. The results should  #
    # only be seen as an indicator and do not necessarily #
    # mean that there is something wrong.                 #
    #                                                     #
    # You should evaluate the output manually in the tmp  #
    # folder of your Invenio installation                 #
    #                                                     #
    # The test suite will download and create several     #
    # gigabytes of video material to perform the test!    #
    # The whole test might take up half an hour           #
    #                                                     #
    # Do you wich to continue? Then enter "Yes, I know!". #
    # Else press 'ctrl + c' to leave this tool.           #
    #######################################################
    """)
    run_test_suite(TEST_SUITE)
