# -*- coding: utf-8 -*-
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Unit tests for the plotextract script."""

__revision__ = "$Id$"

import os
import unittest

from invenio.plotextractor import get_defaults, \
     put_it_together, \
     find_open_and_close_braces, \
     intelligently_find_filenames, \
     assemble_caption, \
     get_converted_image_name
from invenio.plotextractor_output_utils import remove_dups

from invenio.config import CFG_TMPDIR
from invenio.testutils import make_test_suite, run_test_suite

class GetDefaultsTest(unittest.TestCase):
    """Test functions related to get_defaults function."""
    def xtest_get_defaults(self): # FIXME
        tarball = '/tmp/somethingtar'
        sdir = None
        sdir_should_be = os.path.join(CFG_TMPDIR, 'somethingtar_plots')

        sdir, refno = get_defaults(tarball, sdir)
        assert sdir==sdir_should_be, 'didn\'t get correct default scratch dir'
        assert refno==tarball, 'didn\'t get correct default reference number'
        os.system('rm -r %s' % sdir)

        sdir = 'anything else'
        sdir_should_be = '/tmp/somethingtar_plots'

        sdir, refno = get_defaults(tarball, sdir)
        assert sdir==sdir_should_be, 'didn\'t get correct scratch dir'
        assert refno==tarball, 'didn\'t get correct default reference number'
        os.system('rm -r %s' % sdir)

class PutItTogetherTest(unittest.TestCase):
    """Test functions related to the put_it_together function."""

    empty_images_and_captions = []
    dummy_line_index = -1
    empty_lines = []
    tex_file = 'unimportant'

    def test_with_singles(self):
        single_image = 'singleimage'
        single_caption = 'singlecaption'

        cur_image, caption, images_and_captions =\
                put_it_together(single_image, single_caption,
                                empty_images_and_captions, dummy_line_index,
                                empty_lines, tex_file)
        assert images_and_captions==[('singleimage', 'singlecaption')],\
               'failed to zip captions correctly'

    def test_with_multiples_0(self):
        no_main_two_subs = ['', ['img1', 'img2']]
        single_caption = 'singlecaption'

        cur_image, caption, images_and_captions =\
                put_it_together(no_main_two_subs, single_caption,
                                empty_images_and_captions, dummy_line_index,
                                empty_lines, tex_file)
        assert images_and_captions==[('img1', 'singlecaption'),\
                                     ('img2', 'singlecaption')],\
               'didn\'t zip multiple images to one caption correctly'

    def test_with_multiples_1(self):
        no_main_two_subs = ['', ['sub1', 'sub2']]
        main_and_two_sub_captions = ['main caption', ['subcap1', 'subcap2']]

        cur_image, caption, images_and_captions =\
                put_it_together(no_main_two_subs, main_and_two_sub_captions,
                                empty_images_and_captions, dummy_line_index,
                                empty_lines, tex_file)
        assert images_and_captions == [('sub1', 'main caption : subcap1'),\
                                       ('sub2', 'main caption : subcap2')],\
                'didn\'t zip multiple images to main and subcaps correctly'

    def test_with_multiples_2(self):
        main_and_two_sub_images = ['main', ['sub1', 'sub2']]
        main_and_two_sub_captions = ['main caption', ['subcap1', 'subcap2']]

        cur_image, caption, images_and_captions =\
                put_it_together(main_and_two_sub_images,
                                main_and_two_sub_captions,
                                empty_images_and_captions, dummy_line_index,
                                empty_lines, tex_file)
        assert images_and_captions==[('main', 'main caption'),
                                     ('sub1', 'main caption : subcap1'),\
                                     ('sub2', 'main caption : subcap2')],\
                'didn\'t zip {main,sub}{images,captions} together properly'

    def test_with_multiples_3(self):
        single_image = 'singleimage'
        no_main_two_subcaptions = ['', ['subcap1', 'subcap2']]

        cur_image, caption, images_and_captions =\
                put_it_together(single_image, no_two_sub_captions,
                                empty_images_and_captions, dummy_line_index,
                                empty_lines, tex_file)
        assert images_and_captions==[('singleimage', 'subcap1 : subcap2')],\
                'didn\'t zip a single image to multiple subcaps correctly'

    def test_extract_caption(self):
        example_lines = ['{some caption}', '[something else]', 'unrelated']
        single_image = 'singleimage'
        no_caption = ''

        cur_image, caption, images_and_captions =\
                put_it_together(single_image, no_caption,
                                empty_images_and_captions, 1,
                                example_lines, tex_file)
        assert images_and_captions==[('singleimage', 'some caption')],\
                'didn\'t correctly extract the caption for zipping'

class TestFindOpenAndCloseBraces(unittest.TestCase):

    def simple_test(self):
        simple_test_lines = ['{simple}']

        start, start_line, end, end_line = find_open_and_close_braces(
                                               0, 0, '{', simple_test_lines)
        assert start==0, 'didn\'t identify start index'
        assert start_line==0, 'didn\'t identify start line'
        assert end==8, 'didn\'t identify end index'
        assert end_line==0, 'didn\'t identify end line'

    def braces_start_on_next_line_test(self):
        start_on_next_line_lines = ['nothing here', 'chars{morestuff', 'last}']

        start, start_line, end, end_line = find_open_and_close_braces(
                                               0, 0, '{',
                                               start_on_next_line_lines)
        assert start==5, 'didn\'t identify start index'
        assert start_line==1, 'didn\'t identify start line'
        assert end==4, 'didn\'t identify end index'
        assert end_line==2, 'didn\'t identify end line'

    def confounding_braces(self):
        confounding_braces_lines = ['{brace{bracebrace}{}', 'brace{{brace}',
                                   'brace}', '}']

        start, start_line, end, end_line = find_open_and_close_braces(
                                               0, 0, '{',
                                               confounding_braces_lines)
        assert start==0, 'didn\'t identify start index'
        assert start_line==0, 'didn\'t identify start line'
        assert end==0, 'didn\'t identify end index'
        assert end_line==3, 'didn\'t identify end line'

    def square_braces(self):
        square_brace_lines = ['[squaaaaaaare braces]']

        start, start_line, end, end_line = find_open_and_close_braces(
                                               0, 0, '[',
                                               square_brace_lines)
        assert start==0, 'didn\'t identify start index'
        assert start_line==0, 'didn\'t identify start line'
        assert end==20, 'didn\'t identify end index'
        assert end_line==0, 'didn\'t identify end line'

    def hanging_braces(self):
        hanging_braces_lines = ['line{and stuff', 'and more stuff', 'and more']

        start, start_line, end, end_line = find_open_and_close_braces(
                                               0, 0, '{',
                                               hanging_braces_lines)
        assert start==4, 'didn\'t identify start index'
        assert start_line==0, 'didn\'t identify start line'
        assert end==4, 'didn\'t identify end index'
        assert end_line==0, 'didn\'t identify end line'

    def unacceptable_braces(self):
        empty_lines = []

        start, start_line, end, end_line = find_open_and_close_braces(
                                               0, 0, '?',
                                               empty_lines)
        assert start==-1, 'didn\'t identify non-brace'
        assert start_line==-1, 'didn\'t identify non-brace'
        assert end==-1, 'didn\'t identify non-brace'
        assert end_line==-1, 'didn\'t identify non-brace'

class TestIntelligentlyFindFilenames(unittest.TestCase):
    def simple_test(self):
        line = 'file.eps'

        filenames = intelligently_find_filenames(line)
        assert filenames==['file.eps'], 'didn\'t find correct filenames'

    def ext_test(self):
        line = 'file.eps file2'

        filenames = intelligently_find_filenames(line, ext=True)
        assert filenames==['file.eps'], 'didn\'t look for extension'

    def tex_test(self):
        line = 'file.eps file2.tex'

        filenames = intelligently_find_filenames(line, TeX=True)
        assert filenames==['file2.tex'], 'not looking for TeX ext'

    def file_equals_test(self):
        line = 'file=something.eps'

        filenames = intelligently_find_filenames(line)
        assert filenames==['something.eps'], 'didn\'t catch file='

    def in_brackets_test(self):
        line='[file.eps]{anotherfile.ps}'

        filenames = intelligently_find_filenames(line)
        assert filenames==['file.eps', 'anotherfile.ps'], 'didn\'t sort ' +\
                'out brackets properly'

    def lots_of_filenames(self):
        line='[file.pstex]figure=something.eps,haha,anotherthing.ps'

        filenames = intelligently_find_filenames(line, ext=True)
        assert 'file.pstex' in filenames, 'didn\'t look in brackets'
        assert 'something.eps' in filenames, 'didn\'t find figure='
        assert 'anotherthing.ps' in filenames, 'didn\'t find filename'

class TestAssembleCaption(unittest.TestCase):
    def simple_test(self):
        lines = ['some', 'simple ', 'caption!']

        caption = assemble_caption(0, 0, 2, 7, lines)
        assert caption=='some simple caption!', 'didn\'t correctly assemble ' +\
                        'caption'

    def clean_out_label_test(self):
        lines = ['some', '\label{aghhhh}simple ', 'caption!']

        caption = assemble_caption(0, 0, 2, 7, lines)
        assert caption=='some simple caption!', 'didn\'t correctly assemble ' +\
                        'caption'

class TestRemoveDups(unittest.TestCase):
    def test_no_dups(self):
        images_and_captions = [('img1', 'caption1'), ('img2', 'caption2')]

        pared_images_and_captions = remove_dups(images_and_captions)
        assert pared_images_and_captions==images_and_captions, 'removed nondup'

    def test_dup_images(self):
        images_and_captions = [('img1', 'caption1'), ('img1', 'caption2')]

        pared_images_and_captions = remove_dups(images_and_captions)
        assert pared_images_and_captions==[('img1', 'caption1 : caption2')],\
                'didn\'t merge captions correctly'

    def test_dup_captions(self):
        images_and_captions = [('img1', 'caption1'), ('img1', 'caption1'),\
                               ('img1', 'caption2')]

        pared_images_and_captions = remove_dups(images_and_captions)
        assert pared_images_and_captions==[('img1', 'caption1 : caption2')],\
                'didn\'t merge captions correctly'

class TestGetConvertedImageName(unittest.TestCase):
    def no_change_test(self):
        image = '/path/to/image.png'

        converted_image = get_converted_image_name(image)
        assert converted_image==image, 'didn\'t notice image was already '+\
                                       'converted'

    def dot_in_dir_name_no_ext_test(self):
        image = '/path.to/the/image'

        converted_image = get_converted_image_name(image)
        assert converted_image==image+'.png', 'didn\'t add extension'

    def change_extension_test(self):
        image = '/path/to/image.eps'

        converted_image = get_converted_image_name(image)
        assert converted_image=='/path/to/image.png', 'didn\'t change extension'

TEST_SUITE = make_test_suite(GetDefaultsTest,) # FIXME

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
