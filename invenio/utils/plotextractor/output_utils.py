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

from __future__ import print_function

import os
import re
import sys

from invenio.utils.text import encode_for_xml, wash_for_utf8
from invenio.legacy.bibrecord import field_xml_output


def write_message(message):
    print(message)

def write_messages(messages):
    for message in messages:
        write_message(message)



def find_open_and_close_braces(line_index, start, brace, lines):
    """
    Take the line where we want to start and the index where we want to start
    and find the first instance of matched open and close braces of the same
    type as brace in file file.

    @param: line (int): the index of the line we want to start searching at
    @param: start (int): the index in the line we want to start searching at
    @param: brace (string): one of the type of brace we are looking for ({, },
        [, or ])
    @param lines ([string, string, ...]): the array of lines in the file we
        are looking in.

    @return: (start, start_line, end, end_line): (int, int, int): the index
        of the start and end of whatever braces we are looking for, and the
        line number that the end is on (since it may be different than the line
        we started on)
    """

    if brace in ['[', ']']:
        open_brace = '['
        close_brace = ']'
    elif brace in ['{', '}']:
        open_brace = '{'
        close_brace = '}'
    elif brace in ['(', ')']:
        open_brace = '('
        close_brace = ')'
    else:
        # unacceptable brace type!
        return (-1, -1, -1, -1)

    open_braces = []
    line = lines[line_index]

    ret_open_index = line.find(open_brace, start)
    line_index_cpy = line_index
    # sometimes people don't put the braces on the same line
    # as the tag
    while ret_open_index == -1:
        line_index = line_index + 1
        if line_index >= len(lines):
            # failed to find open braces...
            return (0, line_index_cpy, 0, line_index_cpy)
        line = lines[line_index]
        ret_open_index = line.find(open_brace)

    open_braces.append(open_brace)

    ret_open_line = line_index

    open_index = ret_open_index
    close_index = ret_open_index

    while len(open_braces) > 0:
        if open_index == -1 and close_index == -1:
            # we hit the end of the line!  oh, noez!
            line_index = line_index + 1

            if line_index >= len(lines):
                # hanging braces!
                return (ret_open_index, ret_open_line, ret_open_index, \
                    ret_open_line)

            line = lines[line_index]
            # to not skip things that are at the beginning of the line
            close_index = line.find(close_brace)
            open_index = line.find(open_brace)

        else:
            if close_index != -1:
                close_index = line.find(close_brace, close_index + 1)
            if open_index != -1:
                open_index = line.find(open_brace, open_index + 1)

        if close_index != -1:
            open_braces.pop()
            if len(open_braces) == 0 and \
                    (open_index > close_index or open_index == -1):
                break
        if open_index != -1:
            open_braces.append(open_brace)

    ret_close_index = close_index

    return (ret_open_index, ret_open_line, ret_close_index, line_index)

def assemble_caption(begin_line, begin_index, end_line, end_index, lines):
    """
    Take write_messageation about the caption of a picture and put it all together
    in a nice way.  If it spans multiple lines, put it on one line.  If it
    contains controlled characters, strip them out.  If it has tags we don't
    want to worry about, get rid of them, etc.

    @param: begin_line (int): the index of the line where the caption begins
    @param: begin_index (int): the index within the line where the caption
        begins
    @param: end_line (int): the index of the line where the caption ends
    @param: end_index (int): the index within the line where the caption ends
    @param: lines ([string, string, ...]): the line strings of the text

    @return: caption (string): the caption, nicely formatted and pieced together
    """

    # stuff we don't like
    label_head = '\\label{'

    # reassemble that sucker
    if end_line > begin_line:
        # our caption spanned multiple lines
        caption = lines[begin_line][begin_index:]

        for included_line_index in range(begin_line + 1, end_line):
            caption = caption + ' ' + lines[included_line_index]

        caption = caption + ' ' + lines[end_line][:end_index]
        caption = caption.replace('\n', ' ')
        caption = caption.replace('  ', ' ')
    else:
        # it fit on one line
        caption = lines[begin_line][begin_index:end_index]

    # clean out a label tag, if there is one
    label_begin = caption.find(label_head)
    if label_begin > -1:
        # we know that our caption is only one line, so if there's a label
        # tag in it, it will be all on one line.  so we make up some args
        dummy_start, dummy_start_line, label_end, dummy_end = \
                find_open_and_close_braces(0, label_begin, '{', [caption])
        caption = caption[:label_begin] + caption[label_end + 1:]

    # clean out characters not allowed in MARCXML
    # not allowed: & < >
    try:
        caption = wash_for_utf8(caption)
        caption = encode_for_xml(caption.encode('utf-8', 'xmlcharrefreplace'), wash=True)
    except: # that damn encode thing threw an error on astro-ph/0601014
        sys.stderr.write(caption)
        sys.stderr.write(' cannot be processed\n')
        caption = caption.replace('&', '&amp;').replace('<', '&lt;')
        caption = caption.replace('>', '&gt;')

    caption = caption.strip()

    if len(caption) > 1 and caption[0] == '{' and caption[-1] == '}':
        caption = caption[1:-1]

    return caption

def prepare_image_data(extracted_image_data, tex_file, image_list):
    """
    Prepare and clean image-data from duplicates and other garbage.

    @param: extracted_image_data ([(string, string, list, list) ...],
        ...])): the images and their captions + contexts, ordered
    @param: tex_file (string): the location of the TeX (used for finding the
        associated images; the TeX is assumed to be in the same directory
        as the converted images)
    @param: image_list ([string, string, ...]): a list of the converted
        image file names
    @return extracted_image_data ([(string, string, list, list) ...],
        ...])) again the list of image data cleaned for output
    """
    sdir = os.path.split(tex_file)[0]
    image_locs_and_captions_and_labels = []
    for (image, caption, label) in extracted_image_data:
        if image == 'ERROR':
            continue
        if not image == '':
            image_loc = get_image_location(image, sdir, image_list)
            if image_loc != None and os.path.exists(image_loc):
                image_locs_and_captions_and_labels.append(
                        (image_loc, caption, label))
        else:
            image_locs_and_captions_and_labels.append((image, caption, label))
    return image_locs_and_captions_and_labels

def remove_dups(extracted_image_data):
    """
    So now that we spam and get loads and loads of stuff in our lists, we need
    to intelligently get rid of some of it.

    @param: extracted_image_data ([(string, string, list, list),
        (string, string, list, list),...]): the full list of images, captions,
        labels and contexts extracted from this file

    @return: extracted_image_data ([(string, string, list, list),
        (string, string, list, list),...)]: the same list, but if there are
        duplicate images contained in it, then their captions are condensed
    """

    img_list = {}
    pared_image_data = []

    # combine relevant captions
    for (image, caption, label, contexts) in extracted_image_data:
        if image in img_list:
            if not caption in img_list[image]:
                img_list[image].append(caption)
        else:
            img_list[image] = [caption]

    # order it (we know that the order in the original is correct)
    for (image, caption, label, contexts) in extracted_image_data:
        if image in img_list:
            pared_image_data.append((image, \
                                           ' : '.join(img_list[image]), label, contexts))
            del img_list[image]
        # else we already added it to the new list

    return pared_image_data

def create_contextfiles(extracted_image_data):
    """
    Saves the context for each image to a file in the current sub-directory,
    returning a list of tuples per file saved in this form: [(image, filename), ..]

    @param extracted_image_data ([(string, string, list, list), ...]):
        a list of tuples of images matched to labels, captions and contexts from
        this document.
    """
    for image, dummy2, dummy3, contexts in extracted_image_data:
        if len(contexts) > 0 and image != "":
            context_filepath = image + '.context'
            fd = open(context_filepath, 'w')
            for context_line in contexts:
                fd.write(wash_for_utf8(context_line) + '\n\n')
            fd.close()
            #write_message(context_filepath + ' written.')

def create_MARC(extracted_image_data, tarball, refno):
    """
    Take the images and their captions and the name of the associated TeX
    file and build a MARCXML record for them.

    @param: extracted_image_data ([(string, string, list, list), ...]):
        a list of tuples of images matched to labels, captions and contexts from
        this document.
    @param: refno (string): the name for the record number field, or None

    @output: a MARCXML record detailing all the arguments as appropriate
        at tarball.insert.xml and a duplicate one at tarball.correct.xml

    @return: the path to the MARCXML record, None if no plots
    """
    root_dir = os.path.dirname(tarball) + os.sep + os.path.basename(tarball) + \
                 '_plots' + os.sep

    marcxml_fft = []
    index = 0
    for (image_location, caption, dummy, contexts) in extracted_image_data:
        if len(image_location) < 3:
            # If not useful URL -> move on to next
            continue

        # Merge subfolder into docname, until root directory
        relative_image_path = image_location.replace(root_dir, '')
        docname = "_".join(relative_image_path.split('.')[:-1]).replace('/', '_').replace(';', '').replace(':', '')

        if type(caption) == list:
            caption = " ".join(caption)

        if len(caption) < 3:
            subfields = []
            subfields.append(('a', image_location))
            subfields.append(('t', "PlotMisc"))
            subfields.append(('d', "%05d %s" % (index, caption.replace(' : ', ''))))
            subfields.append(('n', docname))
            subfields.append(('o', "HIDDEN"))
            marcxml_fft.append(field_xml_output((subfields, ' ', ' ', None), "FFT"))
        else:
            # Add PLOT MARCXML
            subfields = []
            subfields.append(('a', image_location))
            subfields.append(('t', "Plot"))
            subfields.append(('d', "%05d %s" % (index, caption.replace(' : ', ''))))
            subfields.append(('n', docname))
            marcxml_fft.append(field_xml_output((subfields, ' ', ' ', None), "FFT"))
            if contexts:
                # Add CONTEXT MARCXML
                subfields = []
                subfields.append(('a', "%s.context" % (image_location,)))
                subfields.append(('t', "Plot"))
                subfields.append(('f', ".png;context"))
                subfields.append(('n', docname))
                subfields.append(('o', "HIDDEN"))
                marcxml_fft.append(field_xml_output((subfields, ' ', ' ', None), "FFT"))
        index += 1

    if marcxml_fft:
        # For building result MARCXML
        marcxml_header = ['<record>']

        # Datafield := (subfields, ind1, ind2, controlfield)
        # Subfield := (code, value)

        #FIXME: Determine what to do without refno
        if refno and refno.isdigit():
            field = (None, ' ', ' ', refno)
            marcxml_header.append(field_xml_output(field, '001'))
        marcxml = marcxml_header + marcxml_fft
        marcxml.append('</record>')
        return '\n'.join(marcxml)
    return ""

def get_image_location(image, sdir, image_list, recurred=False):
    """
    This function takes a raw image name and a directory and returns the location of the
    (possibly converted) image

    @param: image (string): the name of the raw image from the TeX
    @param: sdir (string): the directory where everything was unzipped to
    @param: image_list ([string, string, ...]): the list of images that
        were extracted from the tarball and possibly converted

    @return: converted_image (string): the full path to the (possibly
        converted) image file
    """

    if type(image) == list:
        # image is a list, not good
        return None

    image = str(image)

    image = image.strip()

    figure_or_file = '(figure=|file=)'
    figure_or_file_in_image = re.findall(figure_or_file, image)
    if len(figure_or_file_in_image) > 0:
        image.replace(figure_or_file_in_image[0], '')
    includegraphics = '\\includegraphics{'
    includegraphics_in_image = re.findall(includegraphics, image)
    if len(includegraphics_in_image) > 0:
        image.replace(includegraphics_in_image[0], '')

    image = image.strip()

    some_kind_of_tag = '\\\\\\w+ '

    if image.startswith('./'):
        image = image[2:]
    if re.match(some_kind_of_tag, image):
        image = image[len(image.split(' ')[0]) + 1:]
    if image.startswith('='):
        image = image[1:]

    if len(image) == 1:
        return None

    image = image.strip()

    image_path = os.path.join(sdir, image)
    converted_image_should_be = get_converted_image_name(image_path)

    if image_list == None:
        image_list = os.listdir(sdir)

    for png_image in image_list:
        if converted_image_should_be == png_image:
            return png_image

    # maybe it's in a subfolder called eps (TeX just understands that)
    if os.path.isdir(os.path.join(sdir, 'eps')):
        image_list = os.listdir(os.path.join(sdir, 'eps'))
        for png_image in image_list:
            if converted_image_should_be == png_image:
                return os.path.join('eps', png_image)

    if os.path.isdir(os.path.join(sdir, 'fig')):
        image_list = os.listdir(os.path.join(sdir, 'fig'))
        for png_image in image_list:
            if converted_image_should_be == png_image:
                return os.path.join('fig', png_image)

    if os.path.isdir(os.path.join(sdir, 'figs')):
        image_list = os.listdir(os.path.join(sdir, 'figs'))
        for png_image in image_list:
            if converted_image_should_be == png_image:
                return os.path.join('figs', png_image)

    if os.path.isdir(os.path.join(sdir, 'Figures')):
        image_list = os.listdir(os.path.join(sdir, 'Figures'))
        for png_image in image_list:
            if converted_image_should_be == png_image:
                return os.path.join('Figures', png_image)

    if os.path.isdir(os.path.join(sdir, 'Figs')):
        image_list = os.listdir(os.path.join(sdir, 'Figs'))
        for png_image in image_list:
            if converted_image_should_be == png_image:
                return os.path.join('Figs', png_image)

    # maybe it is actually just loose.
    for png_image in os.listdir(sdir):
        if os.path.split(converted_image_should_be)[-1] == png_image:
            return converted_image_should_be
        if os.path.isdir(os.path.join(sdir, png_image)):
            # try that, too!  we just do two levels, because that's all that's
            # reasonable..
            sub_dir = os.path.join(sdir, png_image)
            for sub_dir_file in os.listdir(sub_dir):
                if os.path.split(converted_image_should_be)[-1] == sub_dir_file:
                    return converted_image_should_be

    # maybe it's actually up a directory or two: this happens in nested
    # tarballs where the TeX is stored in a different directory from the images
    for png_image in os.listdir(os.path.split(sdir)[0]):
        if os.path.split(converted_image_should_be)[-1] == png_image:
            return converted_image_should_be
    for png_image in os.listdir(os.path.split(os.path.split(sdir)[0])[0]):
        if os.path.split(converted_image_should_be)[-1] == png_image:
            return converted_image_should_be

    if recurred:
        return None

    # agh, this calls for drastic measures
    for piece in image.split(' '):
        res = get_image_location(piece, sdir, image_list, recurred=True)
        if res != None:
            return res

    for piece in image.split(','):
        res = get_image_location(piece, sdir, image_list, recurred=True)
        if res != None:
            return res

    for piece in image.split('='):
        res = get_image_location(piece, sdir, image_list, recurred=True)
        if res != None:
            return res

    #write_message('Unknown image ' + image)
    return None

def get_converted_image_name(image):
    """
    Gives the name of the image after it has been converted to png format.
    Strips off the old extension.

    @param: image (string): The fullpath of the image before conversion

    @return: converted_image (string): the fullpath of the image after convert
    """
    png_extension = '.png'

    if image[(0 - len(png_extension)):] == png_extension:
        # it already ends in png!  we're golden
        return image

    img_dir = os.path.split(image)[0]
    image = os.path.split(image)[-1]

    # cut off the old extension
    if len(image.split('.')) > 1:
        old_extension = '.' + image.split('.')[-1]
        converted_image = image[:(0 - len(old_extension))] + png_extension

    else:
        #no extension... damn
        converted_image = image + png_extension

    return os.path.join(img_dir, converted_image)

def get_tex_location(new_tex_name, current_tex_name, recurred=False):
    """
    Takes the name of a TeX file and attempts to match it to an actual file
    in the tarball.

    @param: new_tex_name (string): the name of the TeX file to find
    @param: current_tex_name (string): the location of the TeX file where we
        found the reference

    @return: tex_location (string): the location of the other TeX file on
        disk or None if it is not found
    """

    tex_location = None

    current_dir = os.path.split(current_tex_name)[0]

    some_kind_of_tag = '\\\\\\w+ '

    new_tex_name = new_tex_name.strip()
    if new_tex_name.startswith('input'):
        new_tex_name = new_tex_name[len('input'):]
    if re.match(some_kind_of_tag, new_tex_name):
        new_tex_name = new_tex_name[len(new_tex_name.split(' ')[0]) + 1:]
    if new_tex_name.startswith('./'):
        new_tex_name = new_tex_name[2:]
    if len(new_tex_name) == 0:
        #write_message('TeX has been stripped down to nothing.')
        return None
    new_tex_name = new_tex_name.strip()

    new_tex_file = os.path.split(new_tex_name)[-1]
    new_tex_folder = os.path.split(new_tex_name)[0]
    if new_tex_folder == new_tex_file:
        new_tex_folder = ''

    # could be in the current directory
    for any_file in os.listdir(current_dir):
        if any_file == new_tex_file:
            return os.path.join(current_dir, new_tex_file)

    # could be in a subfolder of the current directory
    if os.path.isdir(os.path.join(current_dir, new_tex_folder)):
        for any_file in os.listdir(os.path.join(current_dir, new_tex_folder)):
            if any_file == new_tex_file:
                return os.path.join(os.path.join(current_dir, new_tex_folder),
                                    new_tex_file)

    # could be in a subfolder of a higher directory
    one_dir_up = os.path.join(os.path.split(current_dir)[0], new_tex_folder)
    if os.path.isdir(one_dir_up):
        for any_file in os.listdir(one_dir_up):
            if any_file == new_tex_file:
                return os.path.join(one_dir_up, new_tex_file)

    two_dirs_up = os.path.join(os.path.split(os.path.split(current_dir)[0])[0],
                               new_tex_folder)
    if os.path.isdir(two_dirs_up):
        for any_file in os.listdir(two_dirs_up):
            if any_file == new_tex_file:
                return os.path.join(two_dirs_up, new_tex_file)

    if tex_location == None and not recurred:
        return get_tex_location(new_tex_name + '.tex', current_tex_name, \
                                recurred=True)

    return tex_location
