# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2010, 2011, 2012, 2013, 2014 CERN.
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

"""Unit tests for the plotextract script."""

__revision__ = "$Id$"


from invenio.base.wrappers import lazy_import
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase

assemble_caption = lazy_import('invenio.utils.plotextractor.cli:assemble_caption')
find_open_and_close_braces = lazy_import('invenio.utils.plotextractor.cli:find_open_and_close_braces')
intelligently_find_filenames = lazy_import('invenio.utils.plotextractor.cli:intelligently_find_filenames')
put_it_together = lazy_import('invenio.utils.plotextractor.cli:put_it_together')
get_converted_image_name = lazy_import('invenio.utils.plotextractor.output_utils:get_converted_image_name')
remove_dups = lazy_import('invenio.utils.plotextractor.output_utils:remove_dups')


class PutItTogetherTest(InvenioTestCase):
    """Test functions related to the put_it_together function."""

    def setUp(self):
        self.empty_images_and_captions = []
        self.dummy_line_index = -1
        self.empty_lines = []
        self.tex_file = 'unimportant'

    def test_with_singles(self):
        """plotextractor - put_it_together with singles"""
        single_image = 'singleimage'
        single_caption = 'singlecaption'
        single_label = 'singlelabel'

        dummy1, dummy2, images_and_captions = \
                put_it_together(single_image, single_caption, single_label,
                                self.empty_images_and_captions, self.dummy_line_index,
                                self.empty_lines)
        self.assertTrue(images_and_captions == [('singleimage',
                                                 'singlecaption',
                                                 'singlelabel')],
                                            'failed to zip captions correctly')

    def test_with_multiples_0(self):
        """plotextractor - put_it_together with multiples"""
        no_main_two_subs = ['', ['img1', 'img2']]
        single_caption = 'singlecaption'
        single_label = 'singlelabel'
        dummy1, dummy2, images_and_captions = \
                put_it_together(no_main_two_subs, single_caption, single_label,
                                self.empty_images_and_captions, self.dummy_line_index,
                                self.empty_lines)
        self.assertTrue(images_and_captions == [('img1',
                                                 'singlecaption',
                                                 'singlelabel'),
                                                ('img2',
                                                 'singlecaption',
                                                 'singlelabel')],
               "didn't zip multiple images to one caption correctly")

    def test_with_multiples_1(self):
        """plotextractor - put_it_together with multiples 1"""
        no_main_two_subs = ['', ['sub1', 'sub2']]
        main_and_two_sub_captions = ['main caption', ['subcap1', 'subcap2']]
        single_label = 'singlelabel'
        dummy1, dummy2, images_and_captions = \
                put_it_together(no_main_two_subs, main_and_two_sub_captions, single_label,
                                self.empty_images_and_captions, self.dummy_line_index,
                                self.empty_lines)
        self.assertTrue(images_and_captions == [('sub1',
                                                 'main caption : subcap1',
                                                 'singlelabel'),
                                                ('sub2',
                                                 'main caption : subcap2',
                                                 'singlelabel')],
                "didn't zip multiple images to main and subcaps correctly")

    def test_with_multiples_2(self):
        """plotextractor - put_it_together with multiples 2"""
        main_and_two_sub_images = ['main', ['sub1', 'sub2']]
        main_and_two_sub_captions = ['main caption', ['subcap1', 'subcap2']]
        single_label = 'singlelabel'
        dummy1, dummy2, images_and_captions = \
                put_it_together(main_and_two_sub_images,
                                main_and_two_sub_captions,
                                single_label,
                                self.empty_images_and_captions, self.dummy_line_index,
                                self.empty_lines)
        self.assertTrue(images_and_captions == [('main',
                                                 'main caption',
                                                 'singlelabel'),
                                                ('sub1',
                                                 'main caption : subcap1',
                                                 'singlelabel'),
                                                ('sub2',
                                                 'main caption : subcap2',
                                                 'singlelabel')],
                "didn't zip {main,sub}{images,captions} together properly")

    def test_with_multiples_3(self):
        """plotextractor - put_it_together with multiples 3"""
        single_image = 'singleimage'
        no_main_two_subcaptions = ['', ['subcap1', 'subcap2']]
        single_label = 'singlelabel'
        dummy1, dummy2, images_and_captions = \
                put_it_together(single_image, no_main_two_subcaptions, single_label,
                                self.empty_images_and_captions, self.dummy_line_index,
                                self.empty_lines)
        self.assertTrue(images_and_captions == [('singleimage',
                                                 'subcap1 : subcap2',
                                                 'singlelabel')],
                "didn't zip a single image to multiple subcaps correctly")

    def test_extract_caption(self):
        """plotextractor - put_it_together with extract caption"""
        example_lines = ['{some caption}', '[something else]', 'unrelated']
        single_image = 'singleimage'
        no_caption = ''
        single_label = 'singlelabel'
        dummy1, dummy2, images_and_captions = \
                put_it_together(single_image, no_caption, single_label,
                                self.empty_images_and_captions, 1,
                                example_lines)
        self.assertTrue(images_and_captions == [('singleimage',
                                                 'some caption',
                                                 'singlelabel')],
                "didn't correctly extract the caption for zipping")

class TestFindOpenAndCloseBraces(InvenioTestCase):

    def test_simple_test(self):
        """plotextractor - find_open_and_close_braces simple"""
        simple_test_lines = ['{simple}']

        start, start_line, end, end_line = find_open_and_close_braces(
                                               0, 0, '{', simple_test_lines)
        self.assertTrue(start == 0, "didn't identify start index")
        self.assertTrue(start_line == 0, "didn't identify start line")
        self.assertTrue(end == 7, "didn't identify end index")
        self.assertTrue(end_line == 0, "didn't identify end line")

    def test_braces_start_on_next_line_test(self):
        """plotextractor - find_open_and_close_braces next line"""
        start_on_next_line_lines = ['nothing here', 'chars{morestuff', 'last}']

        start, start_line, end, end_line = find_open_and_close_braces(
                                               0, 0, '{',
                                               start_on_next_line_lines)
        self.assertTrue(start == 5, "didn't identify start index")
        self.assertTrue(start_line == 1, "didn't identify start line")
        self.assertTrue(end == 4, "didn't identify end index")
        self.assertTrue(end_line == 2, "didn't identify end line")

    def test_confounding_braces(self):
        """plotextractor - find_open_and_close_braces confounding"""
        confounding_braces_lines = ['{brace{bracebrace}{}', 'brace{{brace}',
                                   'brace}', '}']

        start, start_line, end, end_line = find_open_and_close_braces(
                                               0, 0, '{',
                                               confounding_braces_lines)
        self.assertTrue(start == 0, "didn't identify start index")
        self.assertTrue(start_line == 0, "didn't identify start line")
        self.assertTrue(end == 0, "didn't identify end index")
        self.assertTrue(end_line == 3, "didn't identify end line")

    def test_square_braces(self):
        """plotextractor - find_open_and_close_braces square braces"""
        square_brace_lines = ['[squaaaaaaare braces]']

        start, start_line, end, end_line = find_open_and_close_braces(
                                               0, 0, '[',
                                               square_brace_lines)
        self.assertTrue(start == 0, "didn't identify start index")
        self.assertTrue(start_line == 0, "didn't identify start line")
        self.assertTrue(end == 20, "didn't identify end index")
        self.assertTrue(end_line == 0, "didn't identify end line")

    def test_hanging_braces(self):
        """plotextractor - find_open_and_close_braces hanging braces"""
        hanging_braces_lines = ['line{and stuff', 'and more stuff', 'and more']

        start, start_line, end, end_line = find_open_and_close_braces(
                                               0, 0, '{',
                                               hanging_braces_lines)
        self.assertTrue(start == 4, "didn't identify start index")
        self.assertTrue(start_line == 0, "didn't identify start line")
        self.assertTrue(end == 4, "didn't identify end index")
        self.assertTrue(end_line == 0, "didn't identify end line")

    def test_unacceptable_braces(self):
        """plotextractor - find_open_and_close_braces unacceptable braces"""
        empty_lines = []

        start, start_line, end, end_line = find_open_and_close_braces(
                                               0, 0, '?',
                                               empty_lines)
        self.assertTrue(start == -1, "didn't identify non-brace")
        self.assertTrue(start_line == -1, "didn't identify non-brace")
        self.assertTrue(end == -1, "didn't identify non-brace")
        self.assertTrue(end_line == -1, "didn't identify non-brace")

class TestIntelligentlyFindFilenames(InvenioTestCase):

    def test_simple_test(self):
        """plotextractor - intelligently_find_filenames simple"""
        line = 'file.eps'

        filenames = intelligently_find_filenames(line, ext=True)
        self.assertTrue(filenames == ['file.eps'],
                        "didn't find correct filenames")

    def test_ext_test(self):
        """plotextractor - intelligently_find_filenames extension"""
        line = 'file.eps file2'

        filenames = intelligently_find_filenames(line, ext=True)
        self.assertTrue(filenames == ['file.eps'],
                        "didn't look for extension")

    def test_tex_test(self):
        """plotextractor - intelligently_find_filenames TeX extension"""
        line = 'file.eps file2.tex'

        filenames = intelligently_find_filenames(line, TeX=True)
        self.assertTrue(filenames == ['file.eps', 'file2.tex'],
                        'not looking for TeX ext')

    def test_file_equals_test(self):
        """plotextractor - intelligently_find_filenames equals"""
        line = 'file=something.eps'

        filenames = intelligently_find_filenames(line, ext=True)
        self.assertTrue(filenames == ['something.eps', 'file=something.eps'],
                        "didn't catch file=")

    def test_in_brackets_test(self):
        """plotextractor - intelligently_find_filenames brackets"""
        line = '[file.eps]{anotherfile.ps}'

        filenames = intelligently_find_filenames(line)
        self.assertTrue(filenames == ['file.eps', 'anotherfile.ps'],
                        "didn't sort out brackets properly")

    def test_lots_of_filenames(self):
        """plotextractor - intelligently_find_filenames lots of filenames"""
        line = '[file.pstex]figure=something.eps,haha,anotherthing.ps'

        filenames = intelligently_find_filenames(line, ext=True)
        self.assertTrue('file.pstex' in filenames, "didn't look in brackets")
        self.assertTrue('something.eps' in filenames, "didn't find figure=")
        self.assertTrue('anotherthing.ps' in filenames, "didn't find filename")

class TestAssembleCaption(InvenioTestCase):

    def test_simple_test(self):
        """plotextractor - assemble caption simple"""
        lines = ['some', 'simple ', 'caption!']

        caption = assemble_caption(0, 0, 2, 8, lines)
        self.assertTrue(caption == 'some simple caption!',
                        "didn't correctly assemble caption")

    def test_clean_out_label_test(self):
        """plotextractor - assemble caption clean out label"""
        lines = ['some', '\\label{aghhhh}simple ', 'caption!']

        caption = assemble_caption(0, 0, 2, 8, lines)
        self.assertTrue(caption == 'some simple caption!',
                        "didn't correctly assemble caption")

class TestRemoveDups(InvenioTestCase):

    def test_no_dups(self):
        """plotextractor - remove_dups no dupes"""
        images_and_captions = [('img1', 'caption1', 'label1', 'FIXME1'),
                               ('img2', 'caption2', 'label1', 'FIXME1')]

        pared_images_and_captions = remove_dups(images_and_captions)
        self.assertTrue(pared_images_and_captions == images_and_captions, 'removed nondup')

    def test_dup_images(self):
        """plotextractor - remove_dups images"""
        images_and_captions = [('img1', 'caption1', 'label1', 'FIXME1'),
                               ('img1', 'caption2', 'label1', 'FIXME1')]

        pared_images_and_captions = remove_dups(images_and_captions)
        self.assertTrue(pared_images_and_captions == [('img1',
                                                       'caption1 : caption2',
                                                       'label1', 'FIXME1')],
                "didn't merge captions correctly")

    def test_dup_captions(self):
        """plotextractor - remove_dups captions"""
        images_and_captions = [('img1', 'caption1', 'label1', 'FIXME1'),
                               ('img1', 'caption1', 'label1', 'FIXME1'),
                               ('img1', 'caption2', 'label1', 'FIXME1')]

        pared_images_and_captions = remove_dups(images_and_captions)
        self.assertTrue(pared_images_and_captions == [('img1',
                                                       'caption1 : caption2',
                                                       'label1', 'FIXME1')],
                "didn't merge captions correctly")

class TestGetConvertedImageName(InvenioTestCase):

    def test_no_change_test(self):
        """plotextractor - get_converted_image_name no change"""
        image = '/path/to/image.png'

        converted_image = get_converted_image_name(image)
        self.assertTrue(converted_image == image,
                        "didn't notice image was already converted")

    def test_dot_in_dir_name_no_ext_test(self):
        """plotextractor - get_converted_image_name dot in dir name"""
        image = '/path.to/the/image'

        converted_image = get_converted_image_name(image)
        self.assertTrue(converted_image == image + '.png',
                        "didn't add extension")

    def test_change_extension_test(self):
        """plotextractor - get_converted_image_name extension"""
        image = '/path/to/image.eps'

        converted_image = get_converted_image_name(image)
        self.assertTrue(converted_image == '/path/to/image.png',
                        "didn't change extension")


TEST_SUITE = make_test_suite(PutItTogetherTest, TestFindOpenAndCloseBraces,
                             TestIntelligentlyFindFilenames,
                             TestAssembleCaption, TestRemoveDups,
                             TestGetConvertedImageName)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
