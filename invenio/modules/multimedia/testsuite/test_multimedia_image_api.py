# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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

"""Multimedia Image API Tests."""

from six import StringIO
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase


class TestMultimediaAPI(InvenioTestCase):

    """Multimedia Image API test case."""

    def setUp(self):
        """Run before the test."""
        # Create an image in memory
        from PIL import Image
        from invenio.modules.multimedia.api import MultimediaImage
        tmp_file = StringIO()
        # create a new image
        image = Image.new("RGBA", (1280, 1024), (255, 0, 0, 0))
        image.save(tmp_file, 'png')

        # Initialize it for our object and create and instance for
        # each test
        tmp_file.seek(0)
        self.image_resize = MultimediaImage.from_string(tmp_file)
        tmp_file.seek(0)
        self.image_crop = MultimediaImage.from_string(tmp_file)
        tmp_file.seek(0)
        self.image_rotate = MultimediaImage.from_string(tmp_file)

    def tearDown(self):
        """Run after the test."""

    def test_image_resize(self):
        """Test image resize function."""
        # Test image size before
        self.assertEqual(str(self.image_resize.size()), str((1280, 1024)))

        # Resize.image_resize to 720,680
        self.image_resize.resize('720,680')
        self.assertEqual(str(self.image_resize.size()), str((720, 680)))

        # Resize.image_resize to 300,
        self.image_resize.resize('300,')
        self.assertEqual(str(self.image_resize.size()), str((300, 283)))

        # Resize.image_resize to ,300
        self.image_resize.resize(',300')
        self.assertEqual(str(self.image_resize.size()), str((318, 300)))

        # Resize.image_resize to pct:90
        self.image_resize.resize('pct:90')
        self.assertEqual(str(self.image_resize.size()), str((286, 270)))

    def test_image_crop(self):
        """Test the crop function."""
        # Crop image x,y,w,h
        self.image_crop.crop('20,20,400,300')
        self.assertEqual(str(self.image_crop.size()), str((400, 300)))

        # Crop image pct:x,y,w,h
        self.image_crop.crop('pct:20,20,40,30')
        self.assertEqual(str(self.image_crop.size()), str((160, 90)))

    def test_image_rotate(self):
        """Test image rotate function."""
        self.image_rotate.rotate(90)
        self.assertEqual(str(self.image_rotate.size()), str((1024, 1280)))

TEST_SUITE = make_test_suite(TestMultimediaAPI)

if __name__ == '__main__':
    run_test_suite(TEST_SUITE)
