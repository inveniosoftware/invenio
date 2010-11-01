##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import os
import re
import sys

from invenio.config import CFG_SITE_URL, CFG_TMPDIR, CFG_WEBDIR
from invenio.shellutils import run_shell_command
from invenio.textutils import encode_for_xml

def write_message(message):
    print message

def write_messages(messages):
    for message in messages:
        write_message(message)

def find_open_and_close_braces(line_index, start, brace, lines):
    '''
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
    '''

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
        write_message('unacceptable brace type!')
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
            write_message('failed to find open braces...')
            write_message('starts at ' + lines[line_index_cpy])
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
                write_message('hanging braces!  yikes!  LaTex????')
                write_message(lines[line_index_cpy])
                return (ret_open_line, ret_open_index, ret_open_line,\
                    ret_open_index)

            line = lines[line_index]
            # to not skip things that are at the beginning of the line
            close_index = line.find(close_brace)
            open_index = line.find(open_brace)

        else:
            if close_index != -1:
                close_index = line.find(close_brace, close_index+1)
            if open_index != -1:
                open_index = line.find(open_brace, open_index+1)

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
    '''
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
    '''

    # stuff we don't like
    label_head = '\\label{'

    # reassemble that sucker
    if end_line > begin_line:
        # our caption spanned multiple lines
        caption = lines[begin_line][begin_index:]

        for included_line in range(begin_line+1, end_line):
            caption = caption + ' ' + lines[included_line]

        caption = caption + lines[end_line][:end_index]
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
        caption = caption[:label_begin] + caption[label_end+1:]

    # clean out characters not allowed in MARCXML
    # not allowed: & < >
    try:
        caption = encode_for_xml(caption.encode('utf-8'), wash=True)
    except: # that damn encode thing threw an error on astro-ph/0601014
        sys.stderr.write(caption)
        sys.stderr.write(' cannot be processed\n')
        caption = caption.replace('&', '&amp;').replace('<', '&lt;')
        caption = caption.replace('>', '&gt;')

    caption = caption.strip()

    if len(caption) > 1 and caption[0] == '{' and caption[-1] == '}':
        caption = caption[1:-1]

    return caption

def remove_dups(images_and_captions_and_labels):
    '''
    So now that we spam and get loads and loads of stuff in our lists, we need
    to intelligently get rid of some of it.

    @param: images_and_captions_and_labels ([(string, string, list),
        (string, string, list),...]): the full list of images and captions and
        labels extracted from this file

    @return: images_and_captions_and_labels ([(string, string, list),
        (string, string, list),...)]: the same list, but if there are
        duplicate images contained in it, then their captions are condensed
    '''

    img_list = {}
    pared_images_and_captions_and_labels = []

    # combine relevant captions
    for (image, caption, label) in images_and_captions_and_labels:
        if image in img_list:
            if not caption in img_list[image]:
                img_list[image].append(caption)
        else:
            img_list[image] = [caption]

    # order it (we know that the order in the original is correct)
    for (image, caption, label) in images_and_captions_and_labels:
        if image in img_list:
            pared_images_and_captions_and_labels.append((image, \
                                           ' : '.join(img_list[image]), label))
            del img_list[image]
        # else we already added it to the new list

    return pared_images_and_captions_and_labels

DUMMY_IMAGE_TMP = os.path.join(CFG_TMPDIR, 'plotextractor_dummy.png')

def create_MARC(images_and_captions_and_labels, tex_file, refno, image_list,
                marc_name):
    '''
    Take the images and their captions and the name of the associated TeX
    file and build a MARCXML record for them.

    @param: images_and_captions_and_labels (([string, string, ...],
        [string, string, ...], list), ...): the images and their captions and
        labels, ordered
    @param: tex_file (string): the location of the TeX (used for finding the
        associated images; the TeX is assumed to be in the same directory
        as the converted images)
    @param: refno (string): the name for the record number field
    @param: image_list ([string, string, ...]): a list of the converted
        image file names
    @param: marc_name (string): the name of the MARC file to create/append to

    @output: a MARCXML record detailing all the arguments as appropriate
        at tarball.insert.xml and a duplicate one at tarball.correct.xml

    @return: the path to the MARCXML record, None if no plots
    '''

    marc_file = open(marc_name, 'a')
    sdir = os.path.split(tex_file)[0]

    # for building
    begin_datafield = '\t<datafield tag="FFT" ind1=" " ind2=" ">\n' +\
            '\t\t<subfield code="a">'
    plot_and_desc_datafield = '</subfield>\n\t\t<subfield code="t">Plot' +\
            '</subfield>\n\t\t<subfield code="d">'
    rename_datafield = '</subfield>\n\t\t<subfield code="n">'
    end_datafield = '</subfield>\n\t</datafield>\n'

    # fresh start
    marc_text = '<record>\n\t<controlfield tag="001">' +\
             refno + '</controlfield>\n'
    end_marc_text = '</record>\n'

    # FIXME: 001 seems to be generated badly in the output files.
    # Check this out, and better use OAI tag (like 035) for the arXiv
    # files, since matching will be done by the bibupload.

    if images_and_captions_and_labels == [['','',[]]]:
        write_message('no plots detected in ' + refno)
        return None

    image_locs_and_captions_and_labels = []

    for (image, caption, label) in images_and_captions_and_labels:
        if image == 'ERROR':
            continue
        if not image == '':
            image_loc = get_image_location(image, sdir, image_list)
            if image_loc != None and os.path.exists(image_loc):
                image_locs_and_captions_and_labels.append(
                        (image_loc, caption, label))
        else:
            image_locs_and_captions_and_labels.append((image, caption, label))

    images_and_captions_and_labels =\
            remove_dups(image_locs_and_captions_and_labels)
    index = 0

    for (image_location, caption, label) in images_and_captions_and_labels:
        if image_location == '':
            # we don't know the image, but the captions are for separate things
            for individual_caption in caption.split(' : '):
                if caption == 'No caption found' or caption == 'No caption' or\
                        caption == '':
                    continue
                marc_text = marc_text +\
                            begin_datafield +\
                            DUMMY_IMAGE_TMP +\
                            plot_and_desc_datafield +\
                            '%05d ' % index + caption +\
                            rename_datafield +\
                            'fig%05d.png' % index +\
                            end_datafield
                index = index + 1
        else:
            marc_text = marc_text +\
                       begin_datafield +\
                       image_location +\
                       plot_and_desc_datafield +\
                       '%05d %s' % (index, caption) +\
                       end_datafield

        index = index + 1

    marc_text = marc_text + end_marc_text

    marc_file.write(marc_text)
    marc_file.close()

    return marc_name

def get_image_location(image, sdir, image_list, recurred=False):
    '''
    takes a raw image name and a directory and returns the location of the
    (possibly converted) image

    @param: image (string): the name of the raw image from the TeX
    @param: sdir (string): the directory where everything was unzipped to
    @param: image_list ([string, string, ...]): the list of images that
        were extracted from the tarball and possibly converted

    @return: converted_image (string): the full path to the (possibly
        converted) image file
    '''

    if type(image) == list:
        write_message('image is ' + str(image) + ' mysteriously.')
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
        image = image[len(image.split(' ')[0])+1:]
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
    '''
    Gives the name of the image after it has been converted to png format.
    Strips off the old extension.

    @param: image (string): The fullpath of the image before conversion

    @return: converted_image (string): the fullpath of the image after convert
    '''
    png_extension = '.png'

    if image[(0-len(png_extension)):] == png_extension:
        # it already ends in png!  we're golden
        return image

    img_dir = os.path.split(image)[0]
    image = os.path.split(image)[-1]

    # cut off the old extension
    if len(image.split('.')) > 1:
        old_extension = '.' + image.split('.')[-1]
        converted_image = image[:(0-len(old_extension))] + png_extension

    else:
        #no extension... damn
        converted_image = image + png_extension

    return os.path.join(img_dir, converted_image)

def get_tex_location(new_tex_name, current_tex_name, recurred=False):
    '''
    Takes the name of a TeX file and attempts to match it to an actual file
    in the tarball.

    @param: new_tex_name (string): the name of the TeX file to find
    @param: current_tex_name (string): the location of the TeX file where we
        found the reference

    @return: tex_location (string): the location of the other TeX file on
        disk or None if it is not found
    '''

    tex_location = None

    current_dir = os.path.split(current_tex_name)[0]

    some_kind_of_tag = '\\\\\\w+ '

    new_tex_name = new_tex_name.strip()
    if new_tex_name.startswith('input'):
        new_tex_name = new_tex_name[len('input'):]
    if re.match(some_kind_of_tag, new_tex_name):
        new_tex_name = new_tex_name[len(new_tex_name.split(' ')[0])+1:]
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
        return get_tex_location(new_tex_name + '.tex', current_tex_name,\
                                recurred=True)

    return tex_location
