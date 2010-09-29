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

import sys
import os
import getopt
import re
import time
import urllib

from invenio.shellutils import run_shell_command
from invenio.textutils import encode_for_xml, wrap_text_in_a_box, \
                              wait_for_user
from invenio.config import CFG_TMPDIR, CFG_BINDIR, CFG_BIBSCHED_PROCESS_USER
from invenio.search_engine import perform_request_search
from invenio.bibtask import task_low_level_submission
from invenio.plotextractor_getter import get_list_of_all_matching_files, \
                                         parse_and_download, \
                                         make_single_directory, \
                                         tarballs_by_recids, \
                                         tarballs_by_arXiv_id
from invenio.plotextractor_converter import untar, check_for_gzip, \
                                            convert_images
from invenio.plotextractor_output_utils import assemble_caption, \
                                               find_open_and_close_braces, \
                                               create_MARC, get_tex_location, \
                                               get_image_location, \
                                               get_converted_image_name, \
                                               write_message, write_messages

'''
This programme will take a tarball from arXiv, untar it, convert all its
associated images to PNG, find the captions to the images detailed in the
included TeX document, and write MARCXML that reflects these associations.
'''

ARXIV_HEADER = 'arXiv:'
SQUASHED_FILE = 'plotdata.xml'
PLOTS_DIR = 'plots'

help_param = 'help'
tarball_param = 'tarball'
tardir_param = 'tdir'
infile_param = 'input'
sdir_param = 'sdir'
extract_text_param = 'extract-text'
force_param = 'force'
upload_param = 'call-bibupload'
yes_i_know_param = 'yes-i-know'
recid_param = 'recid'
arXiv_param = 'arXiv'
squash_param = 'squash'
param_abbrs = 'ht:d:s:i:a:xfuyrq'
params = [help_param, tarball_param+'=', tardir_param+'=', sdir_param+'=', \
          infile_param+'=', arXiv_param, extract_text_param, force_param, \
          upload_param, yes_i_know_param, recid_param, squash_param]

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], param_abbrs, params)
    except getopt.GetoptError, err:
        write_message(str(err))
        usage()
        sys.exit(2)

    tarball = None
    sdir = None
    infile = None
    tdir = None
    xtract_text = False
    upload_plots = False
    force = False
    squash = False
    yes_i_know = False
    recids = None
    arXiv = None

    for opt, arg in opts:
        if opt in ['-h', help_param]:
            usage()
            sys.exit()
        elif opt in ['-t', tarball_param]:
            tarball = arg
        elif opt in ['-d', tardir_param]:
            tdir = arg
        elif opt in ['-i', infile_param]:
            infile = arg
        elif opt in ['-r', recid_param]:
            recid = arg
        elif opt in ['-a', arXiv_param]:
            arXiv = arg
        elif opt in ['-s', sdir_param]:
            sdir = arg
        elif opt in ['-x', extract_text_param]:
            xtract_text = True
        elif opt in ['-f', force_param]:
            force = True
        elif opt in ['-u', upload_param]:
            upload_plots = True
        elif opt in ['-q', squash_param]:
            squash = True
        elif opt in ['-y', yes_i_know_param]:
            yes_i_know = True
        else:
            usage()
            sys.exit()

    if sdir == None:
        sdir = CFG_TMPDIR

    if not os.path.isdir(sdir):
        try:
            os.makedirs(sdir)
        except:
            write_message('oopsie, we can\'t use this sdir.  using '+\
                      'CFG_TMPDIR')
            sdir = CFG_TMPDIR

    tars_and_gzips = []

    if tarball != None:
        tars_and_gzips.append(tarball)
    if tdir != None:
        filetypes = ['gzip compressed', 'ar archive'] # that catches [t,T]ar # FIXME
        write_message('processing any tarballs in ' + tdir)
        tars_and_gzips.extend(get_list_of_all_matching_files(tdir, filetypes))
    if infile != None:
        tars_and_gzips.extend(parse_and_download(infile, sdir))
    if recids != None:
        tars_and_gzips.extend(tarballs_by_recids(recids, sdir))
    if arXiv != None:
        tars_and_gzips.extend(tarballs_by_arXiv_id(arXiv, sdir))
    if tars_and_gzips == []:
        write_message('what?  no tarballs to process!')
        sys.exit(1)

    if squash:
        marc_file = os.path.join(sdir, SQUASHED_FILE)
        open(marc_file, 'w').close()

    for tarball in tars_and_gzips:
        process_single(tarball, sdir=sdir, xtract_text=xtract_text,\
                       upload_plots=upload_plots, force=force, squash=squash)

    if squash and upload_plots:
        upload_to_site(marc_file, yes_i_know)

def process_single(tarball, sdir=CFG_TMPDIR, xtract_text=False, \
                   upload_plots=True, force=False, squash=False):
    '''
    Processes one tarball end-to-end.

    @param: tarball (string): the absolute location of the tarball we wish
        to process
    @param: sdir (string): where we should put all the intermediate files for
        the processing.  if you're uploading, this directory should be one
        of the ones specified in CFG_BIBUPLOAD_FFT_ALLOWED_LOCAL_PATHS, else
        the upload won't work
    @param: xtract_text (boolean): true iff you want to run pdftotext on the
        pdf versions of the tarfiles.  this programme assumes that the pdfs
        are named the same as the tarballs but with a .pdf extension.
    @param: upload_plots (boolean): true iff you want to bibupload the plots
        extracted by this process

    @return: None
    '''

    sub_dir, refno = get_defaults(tarball, sdir)

    if not squash:
        marc_name = os.path.join(sub_dir, refno + '.xml')
    else:
        marc_name = os.path.join(sdir, SQUASHED_FILE)

    if (force or not os.path.exists(marc_name)) and not squash:
        open(marc_name, 'w').close()

    if xtract_text:
        extract_text(tarball)

    image_list, tex_files = untar(tarball, sub_dir)
    if tex_files == [] or tex_files == None:
        write_message(os.path.split(tarball)[-1] + ' is not a tarball')
        run_shell_command('rm -r ' + sub_dir)
        return

    converted_image_list = convert_images(image_list)

    images_and_captions_and_labels = [['','', []]]
    for tex_file in tex_files:
        images_and_captions_and_labels.extend(extract_captions(tex_file,
                                               sub_dir, converted_image_list))

    marc_name = create_MARC(images_and_captions_and_labels, tex_files[0],
                            refno, converted_image_list, marc_name)
    if marc_name != None and not squash:
        write_message('generated ' + marc_name)
        if upload_plots:
            upload_to_site(marc_name)

    clean_up(image_list)

    write_message('work complete on ' + os.path.split(tarball)[-1])

def clean_up(image_list):
    '''
    Removes all the intermediate stuff.

    @param: image_list ([string, string, ...]): the images to remove

    NOTE: when running this for later upload, it's not a good idea to
        remove the converted images!
    '''
    return # FIXME do not delete image files before upload
    for image_file in image_list:
        run_shell_command('rm ' + image_file)

def get_defaults(tarball, sdir):
    '''
    A function for parameter-checking.

    @param: tarball (string): the location of the tarball to be extracted
    @param: sdir (string): the location of the scratch directory for untarring,
        conversions, and the ultimate destination of the MARCXML

    @return sdir, refno (string, string): the same
        arguments it was sent as is appropriate.
    '''

    if sdir == None:
        write_message('using default directory: ' + CFG_TMPDIR +\
             ' for scratchwork')
        sdir = CFG_TMPDIR

    else:
        sdir = os.path.split(tarball)[0]

    # make a subdir in the scratch directory for each tarball
    sdir = make_single_directory(sdir, \
                                 os.path.split(tarball)[-1] + '_' + PLOTS_DIR)

    arXiv_id = os.path.split(tarball)[-1]

    refno = get_reference_number(tarball)
    if refno == tarball:
        write_message('can\'t find record id for ' + arXiv_id)

    return sdir, refno

def get_reference_number(tarball):
    '''
    Attempts to determine the reference number of the file by searching.

    @param: tarball (string): the name of the tarball as downloaded from
        arXiv

    @return: refno (string): the reference number of the paper
    '''

    # we just need the name of the file
    tarball = os.path.split(tarball)[1]

    # the name right now looks like arXiv:hep-ph_9703009
    # or arXiv:0910.0476
    if tarball.startswith(ARXIV_HEADER):
        tarball = tarball.split(':')[1]
        if len(tarball.split('_')) > 1:
            arXiv_record = tarball.replace('_', '/')
        else:
            arXiv_record = tarball

        result = perform_request_search(p=arXiv_record, f='reportnumber')

        if len(result) == 0:
            return tarball

        return str(result[0])

    arXiv_record = re.findall('(([a-zA-Z\\-]+/\\d+)|(\\d+\\.\\d+))', tarball)
    if len(arXiv_record) > 1:
        arXiv_record = arXiv_record[0]
        result = perform_request_search(p=arXiv_record, f='reportnumber')

        if len(result) > 0:
            return str(result[0])

    tarball_mod = tarball.replace('_', '/')
    arXiv_record = re.findall('(([a-zA-Z\\-]+/\\d+)|(\\d+\\.\\d+))',\
                              tarball_mod)
    if len(arXiv_record) > 1:
        arXiv_record = arXiv_record[0]
        result = perform_request_search(p=arXiv_record, f='reportnumber')

        if len(result) > 0:
            return str(result[0])

    return tarball

def rotate_image(filename, line, sdir, image_list):
    '''
    Given a filename and a line, figure out what it is that the author
    wanted to do wrt changing the rotation of the image and convert the
    file so that this rotation is reflected in its presentation.

    @param: filename (string): the name of the file as specified in the TeX
    @param: line (string): the line where the rotate command was found

    @output: the image file rotated in accordance with the rotate command
    @return: True if something was rotated
    '''

    file_loc = get_image_location(filename, sdir, image_list)
    degrees = re.findall('(angle=[-\\d]+|rotate=[-\\d]+)', line)

    if len(degrees) < 1:
        return False

    degrees = degrees[0].split('=')[-1].strip()

    if file_loc == None or file_loc == 'ERROR' or\
            not re.match('-*\\d+', degrees):
        return False

    degrees = str(0-int(degrees))

    cmd = 'mogrify -rotate ' + degrees + ' ' + file_loc
    dummy, dummy, cmd_err = run_shell_command(cmd)

    if cmd_err != '':
        return True
    else:
        return True

MAIN_CAPTION_OR_IMAGE = 0
SUB_CAPTION_OR_IMAGE = 1

def extract_captions(tex_file, sdir, image_list, main=True):
    '''
    Take the TeX file and the list of images in the tarball (which all,
    presumably, are used in the TeX file) and figure out which captions
    in the text are associated with which images

    @param: tex_file (string): the name of the TeX file which mentions
        the images

    @return: images_and_captions_and_labels ([(string, string, string),
        (string, string, string), ...]):
        a list of tuples representing the names of images and their
        corresponding figure labels from the TeX file
    '''

    if os.path.isdir(tex_file):
        return []

    tex = open(tex_file)
    # possible figure lead-ins
    figure_head = '\\begin{figure'  # also matches figure*
    figure_tail = '\\end{figure'  # also matches figure*
    picture_head = '\\begin{picture}'
    displaymath_head = '\\begin{displaymath}'
    subfloat_head = '\\subfloat'
    subfig_head = '\\subfigure'
    includegraphics_head = '\\includegraphics'
    special_head = '\\special'
    epsfig_head = '\\epsfig'
    input_head = '\\input'
    # possible caption lead-ins
    caption_head = '\\caption'
    figcaption_head = '\\figcaption'

    label_head = '\\label'
    ref_head = '\\ref{'

    rotate = 'rotate='
    angle = 'angle='

    eps_tail = '.eps'
    ps_tail = '.ps'

    doc_head = '\\begin{document}'
    doc_tail = '\\end{document}'

    images_and_captions_and_labels = []
    cur_image = ''
    caption = ''
    label = []

    lines = tex.readlines()
    tex.close()

    # cut out shit before the doc head
    if main:
        for line_index in range(len(lines)):
            if lines[line_index].find(doc_head) < 0:
                lines[line_index] = ''
            else:
                break

    # are we using commas in filenames here?
    commas_okay = False
    for dirpath, dummy0, filenames in \
            os.walk(os.path.split(os.path.split(tex_file)[0])[0]):
        for filename in filenames:
            if filename.find(',') > -1:
                commas_okay = True
                break

    # a comment is a % not preceded by a \
    comment = re.compile("(?<!\\\\)%")

    for line_index in range(len(lines)):
        # get rid of pesky comments by splitting where the comment is
        # and keeping only the part before the %
        line = comment.split(lines[line_index])[0]
        line = line.strip()
        lines[line_index] = line

    in_figure_tag = 0

    for line_index in range(len(lines)):
        line = lines[line_index]

        if line == '':
            continue
        if line.find(doc_tail) > -1:
           return images_and_captions_and_labels

        '''
        FIGURE -
        structure of a figure:
        \begin{figure}
        \formatting...
        \includegraphics[someoptions]{FILENAME}
        \caption{CAPTION}  %caption and includegraphics may be switched!
        \end{figure}
        '''

        index = line.find(figure_head)
        if index > -1:
            in_figure_tag = 1
            # some punks don't like to put things in the figure tag.  so we
            # just want to see if there is anything that is sitting outside
            # of it when we find it
            cur_image, caption, label, images_and_captions_and_labels =\
                    put_it_together(cur_image, caption, label,\
                                    images_and_captions_and_labels,\
                                    line_index, lines, tex_file)

        # here, you jerks, just make it so that it's fecking impossible to
        # figure out your damn inclusion types

        index = max([line.find(eps_tail), line.find(ps_tail),\
                     line.find(epsfig_head)])
        if index > -1:
            if line.find(eps_tail) > -1 or line.find(ps_tail) > -1:
                ext = True
            else:
                ext = False
            filenames = intelligently_find_filenames(line, ext=ext,
                                                     commas_okay=commas_okay)

            # try to look ahead!  sometimes there are better matches after
            if line_index < len(lines) - 1:
                filenames.extend(\
                          intelligently_find_filenames(lines[line_index + 1],
                                                      commas_okay=commas_okay))
            if line_index < len(lines) - 2:
                filenames.extend(\
                          intelligently_find_filenames(lines[line_index + 2],
                                                      commas_okay=commas_okay))

            for filename in filenames:
                filename = str(filename)
                if cur_image == '':
                    cur_image = filename
                elif type(cur_image) == list:
                    if type(cur_image[SUB_CAPTION_OR_IMAGE]) == list:
                        cur_image[SUB_CAPTION_OR_IMAGE].append(filename)
                    else:
                        cur_image[SUB_CAPTION_OR_IMAGE] = [filename]
                else:
                    cur_image = ['', [cur_image, filename]]

        '''
        Rotate and angle
        '''
        index = max(line.find(rotate), line.find(angle))
        if index > -1:
            # which is the image associated to it?
            filenames = intelligently_find_filenames(line,
                                                     commas_okay=commas_okay)
            # try the line after and the line before
            filenames.extend(intelligently_find_filenames(lines[line_index+1],
                                                      commas_okay=commas_okay))
            filenames.extend(intelligently_find_filenames(lines[line_index-1],
                                                      commas_okay=commas_okay))

            already_tried = []
            for filename in filenames:
                if filename != 'ERROR' and not filename in already_tried:
                    if rotate_image(filename, line, sdir, image_list):
                        break
                    already_tried.append(filename)

        '''
        INCLUDEGRAPHICS -
        structure of includegraphics:
        \includegraphics[someoptions]{FILENAME}
        '''
        index = line.find(includegraphics_head)
        if index > -1:
            open_curly, open_curly_line, close_curly, dummy = \
                    find_open_and_close_braces(line_index, index, '{', lines)

            filename = lines[open_curly_line][open_curly+1:close_curly]

            if cur_image == '':
                cur_image = filename
            elif type(cur_image) == list:
                if type(cur_image[SUB_CAPTION_OR_IMAGE]) == list:
                    cur_image[SUB_CAPTION_OR_IMAGE].append(filename)
                else:
                    cur_image[SUB_CAPTION_OR_IMAGE] = [filename]
            else:
                cur_image = ['', [cur_image, filename]]

        '''
        {\input{FILENAME}}
        \caption{CAPTION}

        This input is ambiguous, since input is also used for things like
        inclusion of data from other LaTeX files directly.
        '''
        index = line.find(input_head)
        if index > -1:
            #write_message('found input tag')
            new_tex_names = intelligently_find_filenames(line, TeX=True,
                                                        commas_okay=commas_okay)

            for new_tex_name in new_tex_names:
                if new_tex_name != 'ERROR':
                    #write_message('input TeX: ' + new_tex_name)
                    new_tex_file = get_tex_location(new_tex_name, tex_file)
                    if new_tex_file != None:
                        images_and_captions_and_labels.extend(extract_captions(\
                                                      new_tex_file, sdir,\
                                                      image_list,
                                                      main=False))

        '''PICTURE'''

        index = line.find(picture_head)
        if index > -1:
            # structure of a picture:
            # \begin{picture}
            # ....not worrying about this now
            write_message('found picture tag')

        '''DISPLAYMATH'''

        index = line.find(displaymath_head)
        if index > -1:
            # structure of a displaymath:
            # \begin{displaymath}
            # ....not worrying about this now
            write_message('found displaymath tag')

        '''
        LABELS -
        structure of a label:
        \label{somelabelnamewhichprobablyincludesacolon}

        Labels are used to tag images and will later be used in ref tags
        to reference them.  This is interesting because in effect the refs
        to a plot are additional caption for it.

        Notes: labels can be used for many more things than just plots.
        We'll have to experiment with how to best associate a label with an
        image.. if it's in the caption, it's easy.  If it's in a figure, it's
        still okay... but the images that aren't in figure tags are numerous.
        '''

        index = line.find(label_head)
        if index > -1:
            if in_figure_tag:
                # well then this clearly belongs to the current image
                open_curly, open_curly_line, close_curly, dummy = \
                    find_open_and_close_braces(line_index, index, '{', lines)
                cur_label = lines[open_curly_line][open_curly+1:close_curly]
                cur_label = cur_label.strip()
                label.append(cur_label)
                # write_message('found label ' + cur_label)

        '''
        CAPTIONS -
        structure of a caption:
        \caption[someoptions]{CAPTION}
        or
        \caption{CAPTION}
        or
        \caption{{options}{CAPTION}}
        '''

        index = max([line.find(caption_head), line.find(figcaption_head)])
        if index > -1:
            open_curly, open_curly_line, close_curly, close_curly_line = \
                    find_open_and_close_braces(line_index, index, '{', lines)

            cap_begin = open_curly + 1

            cur_caption = assemble_caption(open_curly_line, cap_begin, \
                        close_curly_line, close_curly, lines)

            if caption == '':
                caption = cur_caption
            elif type(caption) == list:
                if type(caption[SUB_CAPTION_OR_IMAGE]) == list:
                    caption[SUB_CAPTION_OR_IMAGE].append(cur_caption)
                else:
                    caption[SUB_CAPTION_OR_IMAGE] = [cur_caption]
            elif caption != cur_caption:
                caption = ['', [caption, cur_caption]]

        '''
        SUBFLOATS -
        structure of a subfloat (inside of a figure tag):
        \subfloat[CAPTION]{options{FILENAME}}

        also associated with the overall caption of the enclosing figure
        '''

        index = line.find(subfloat_head)
        if index > -1:
            # if we are dealing with subfloats, we need a different
            # sort of structure to keep track of captions and subcaptions
            if type(cur_image) != list:
                cur_image = [cur_image, []]
            if type(caption) != list:
                caption = [caption, []]

            open_square, open_square_line, close_square, close_square_line = \
                    find_open_and_close_braces(line_index, index, '[', lines)
            cap_begin = open_square + 1

            sub_caption = assemble_caption(open_square_line, \
                    cap_begin, close_square_line, close_square, lines)
            caption[SUB_CAPTION_OR_IMAGE].append(sub_caption)

            open_curly, open_curly_line, close_curly, dummy = \
                    find_open_and_close_braces(close_square_line, \
                    close_square, '{', lines)
            sub_image = lines[open_curly_line][open_curly+1:close_curly]

            cur_image[SUB_CAPTION_OR_IMAGE].append(sub_image)

        '''
        SUBFIGURES -
        structure of a subfigure (inside a figure tag):
        \subfigure[CAPTION]{
        \includegraphics[options]{FILENAME}}

        also associated with the overall caption of the enclosing figure
        '''

        index = line.find(subfig_head)
        if index > -1:
            # like with subfloats, we need a different structure for keepin
            # track of this stuff
            if type(cur_image) != list:
                cur_image = [cur_image, []]
            if type(caption) != list:
                caption = [caption, []]

            open_square, open_square_line, close_square, close_square_line = \
                    find_open_and_close_braces(line_index, index, '[', lines)
            cap_begin = open_square + 1

            sub_caption = assemble_caption(open_square_line, \
                    cap_begin, close_square_line, close_square, lines)
            caption[SUB_CAPTION_OR_IMAGE].append(sub_caption)

            index_cpy = index

            # find the graphics tag to get the filename
            # it is okay if we eat lines here
            index = line.find(includegraphics_head)
            while index == -1 and (line_index + 1) < len(lines):
                line_index = line_index + 1
                line = lines[line_index]
                index = line.find(includegraphics_head)

            if line_index == len(lines):
                line_index = index_cpy
                write_message('didn\'t find the image name on line ' +\
                                   line_index)

            else:
                open_curly, open_curly_line, close_curly, dummy = \
                        find_open_and_close_braces(line_index, \
                        index, '{', lines)
                sub_image = lines[open_curly_line][open_curly+1:close_curly]

                cur_image[SUB_CAPTION_OR_IMAGE].append(sub_image)

        '''
        FIGURE

        important: we put the check for the end of the figure at the end
        of the loop in case some pathological person puts everything in one
        line
        '''

        index = max([line.find(figure_tail), line.find(doc_tail)])
        if index > -1:
            in_figure_tag = 0

            cur_image, caption, label, images_and_captions_and_labels =\
                    put_it_together(cur_image, caption, label,\
                                    images_and_captions_and_labels,\
                                    line_index, lines, tex_file)

        '''
        END DOCUMENT

        we shouldn't look at anything after the end document tag is found
        '''

        index = line.find(doc_tail)
        if index > -1:
            break

    return images_and_captions_and_labels

def put_it_together(cur_image, caption, label, images_and_captions_and_labels,
                    line_index, lines, tex_file):
    '''
    Takes the current image(s) and caption(s) and label(s) and assembles them
    into something useful in the images_and_captions_and_labels list.

    @param: cur_image (string || list): the image currently being dealt with, or
        the list of images, in the case of subimages
    @param: caption (string || list): the caption or captions currently in scope
    @param: label (list): the labels associated to this image/these images
    @param: images_and_captions_and_labels ([(string, string, list),
        (string, string, list), ...]): a list of tuples of images matched to
        captions and labels from this document.
    @param: line_index (int): the index where we are in the lines (for
        searchback and searchforward purposes)
    @param: lines ([string, string, ...]): the lines in the TeX
    @oaram: tex_file (string): the name of the TeX file we're dealing with

    @return: (cur_image, caption, images_and_captions_labels): the same
        arguments it was sent, processed appropriately
    '''

    if type(cur_image) == list:
        if cur_image[MAIN_CAPTION_OR_IMAGE] == 'ERROR':
            cur_image[MAIN_CAPTION_OR_IMAGE] = ''
        for image in cur_image[SUB_CAPTION_OR_IMAGE]:
            if image == 'ERROR':
                cur_image[SUB_CAPTION_OR_IMAGE].remove(image)

    if cur_image != '' and caption != '':

        if type(cur_image) == list and type(caption) == list:

            if cur_image[MAIN_CAPTION_OR_IMAGE] != '' and\
                    caption[MAIN_CAPTION_OR_IMAGE] != '':
                images_and_captions_and_labels.append(
                    (cur_image[MAIN_CAPTION_OR_IMAGE],
                     caption[MAIN_CAPTION_OR_IMAGE], label))
            if type(cur_image[MAIN_CAPTION_OR_IMAGE]) == list:
                write_message('why is the main image a list?')
                # it's a good idea to attach the main caption to other
                # things, but the main image can only be used once
                cur_image[MAIN_CAPTION_OR_IMAGE] = ''

            if type(cur_image[SUB_CAPTION_OR_IMAGE]) == list:
                if type(caption[SUB_CAPTION_OR_IMAGE]) == list:
                    for index in \
                            range(len(cur_image[SUB_CAPTION_OR_IMAGE])):
                        if index < len(caption[SUB_CAPTION_OR_IMAGE]):
                            long_caption =\
                                caption[MAIN_CAPTION_OR_IMAGE] +' : '+\
                                caption[SUB_CAPTION_OR_IMAGE][index]
                        else:
                            long_caption =\
                                caption[MAIN_CAPTION_OR_IMAGE] +' : '+\
                                'caption not extracted'
                        images_and_captions_and_labels.append(
                            (cur_image[SUB_CAPTION_OR_IMAGE][index],
                             long_caption, label))

                else:
                    long_caption = caption[MAIN_CAPTION_OR_IMAGE] +\
                        ' : ' + caption[SUB_CAPTION_OR_IMAGE]
                    for sub_image in cur_image[SUB_CAPTION_OR_IMAGE]:
                        images_and_captions_and_labels.append(
                            (sub_image, long_caption, label))

            else:
                if type(caption[SUB_CAPTION_OR_IMAGE]) == list:
                    long_caption = caption[MAIN_CAPTION_OR_IMAGE]
                    for sub_cap in caption[SUB_CAPTION_OR_IMAGE]:
                        long_caption = long_caption + ' : ' + sub_cap
                    images_and_captions_and_labels.append(
                       (cur_image[SUB_CAPTION_OR_IMAGE], long_caption, label))
                else:
                    #wtf are they lists for?
                    images_and_captions_and_labels.append(
                        (cur_image[SUB_CAPTION_OR_IMAGE],
                         caption[SUB_CAPTION_OR_IMAGE], label))

        elif type(cur_image) == list:
            if cur_image[MAIN_CAPTION_OR_IMAGE] != '':
                images_and_captions_and_labels.append(
                    (cur_image[MAIN_CAPTION_OR_IMAGE], caption, label))
            if type(cur_image[SUB_CAPTION_OR_IMAGE]) == list:
                for image in cur_image[SUB_CAPTION_OR_IMAGE]:
                   images_and_captions_and_labels.append((image, caption,
                                                          label))
            else:
                images_and_captions_and_labels.append(
                    (cur_image[SUB_CAPTION_OR_IMAGE], caption, label))

        elif type(caption) == list:
            if caption[MAIN_CAPTION_OR_IMAGE] != '':
                images_and_captions_and_labels.append(
                    (cur_image, caption[MAIN_CAPTION_OR_IMAGE], label))
            if type(caption[SUB_CAPTION_OR_IMAGE]) == list:
                write_message('multiple caps for one image: ')
                long_caption = caption[MAIN_CAPTION_OR_IMAGE]
                for subcap in caption[SUB_CAPTION_OR_IMAGE]:
                    long_caption = long_caption + ' : ' + subcap
                write_message(long_caption)
                images_and_captions_and_labels.append((cur_image, long_caption,
                                                       label))
            else:
                images_and_captions_and_labels.append(
                    (cur_image, caption[SUB_CAPTION_OR_IMAGE], label))

        else:
            images_and_captions_and_labels.append((cur_image, caption, label))

    elif cur_image != '' and caption == '':
        # we may have missed the caption somewhere.
        REASONABLE_SEARCHBACK = 25
        REASONABLE_SEARCHFORWARD = 5
        curly_no_tag_preceding = '(?<!\\w){'

        for searchback in range(REASONABLE_SEARCHBACK):
            if line_index - searchback < 0:
                continue

            back_line = lines[line_index - searchback]
            m = re.search(curly_no_tag_preceding, back_line)
            if m != None:
                open_curly = m.start()
                open_curly, open_curly_line, close_curly, \
                close_curly_line = find_open_and_close_braces(\
                line_index - searchback, open_curly, '{', lines)

                cap_begin = open_curly + 1

                caption = assemble_caption(open_curly_line, cap_begin, \
                    close_curly_line, close_curly, lines)

                if type(cur_image) == list:
                    images_and_captions_and_labels.append(
                            (cur_image[MAIN_CAPTION_OR_IMAGE], caption, label))

                    for sub_img in cur_image[SUB_CAPTION_OR_IMAGE]:
                        images_and_captions_and_labels.append((sub_img, caption,
                                                           label))
                else:
                    images_and_captions_and_labels.append((cur_image, caption,
                                                       label))
                    break

        if caption == '':
            for searchforward in range(REASONABLE_SEARCHFORWARD):
                if line_index + searchforward >= len(lines):
                    break

                fwd_line = lines[line_index + searchforward]
                m = re.search(curly_no_tag_preceding, fwd_line)

                if m != None:
                    open_curly = m.start()
                    open_curly, open_curly_line, close_curly, \
                    close_curly_line = find_open_and_close_braces(\
                    line_index + searchforward, open_curly, '{', lines)

                    cap_begin = open_curly + 1

                    caption = assemble_caption(open_curly_line, \
                              cap_begin, close_curly_line, close_curly, lines)

                    if type(cur_image) == list:
                        images_and_captions_and_labels.append(
                            (cur_image[MAIN_CAPTION_OR_IMAGE], caption, label))
                        for sub_img in cur_image[SUB_CAPTION_OR_IMAGE]:
                            images_and_captions_and_labels.append(
                                                (sub_img, caption, label))
                    else:
                        images_and_captions_and_labels.append((cur_image,
                                                           caption, label))
                    break

        if caption == '':
            if type(cur_image) == list:
                images_and_captions_and_labels.append(
                    (cur_image[MAIN_CAPTION_OR_IMAGE], 'No caption found',\
                     label))
                for sub_img in cur_image[SUB_CAPTION_OR_IMAGE]:
                    images_and_captions_and_labels.append((sub_img,
                                                           'No caption', label))
            else:
                images_and_captions_and_labels.append(
                   (cur_image, 'No caption found', label))

    elif caption != '' and cur_image == '':
        if type(caption) == list:
            long_caption = caption[MAIN_CAPTION_OR_IMAGE]
            for subcap in caption[SUB_CAPTION_OR_IMAGE]:
                long_caption = long_caption + ': ' + subcap
        else:
            long_caption = caption

        images_and_captions_and_labels.append(('', long_caption, label))

    # if we're leaving the figure, no sense keeping the data
    cur_image = ''
    caption = ''
    label = []

    return (cur_image, caption, label, images_and_captions_and_labels)

def intelligently_find_filenames(line, TeX=False, ext=False, commas_okay=False):
    '''
    Find the filename in the line.  We don't support all filenames!  Just eps
    and ps for now.

    @param: line (string): the line we want to get a filename out of

    @return: filename ([string, ...]): what is probably the name of the file(s)
    '''

    files_included = ['ERROR']

    if commas_okay:
        valid_for_filename = '\\s*[A-Za-z0-9\\-\\=\\+/\\\\ _\\.,%#]+'
    else:
        valid_for_filename = '\\s*[A-Za-z0-9\\-\\=\\+/\\\\ _\\.%#]+'

    if ext:
        valid_for_filename = valid_for_filename + '.e*ps[texfi2]*'

    if TeX:
        valid_for_filename = valid_for_filename + '[.latex]*'

    file_inclusion = re.findall('=' + valid_for_filename + '[ ,]', line)

    if len(file_inclusion) > 0:
        # right now it looks like '=FILENAME,' or '=FILENAME '
        for file_included in file_inclusion:
            files_included.append(file_included[1:-1])

    file_inclusion = re.findall('([ps]*file=\\s*|figure=\\s*)' +\
                                valid_for_filename + '[,\\]} ]*', line)

    if len(file_inclusion) > 0:
        # still has the =
        for file_included in file_inclusion:
            part_before_equals = file_included.split('=')[0]
            file_included = file_included[len(part_before_equals):].strip()
            if not file_included in files_included:
                files_included.append(file_included)

    file_inclusion = re.findall('["\'{\\[]'+ valid_for_filename + '[}\\],"\']',\
                line)

    if len(file_inclusion) > 0:
        # right now it's got the {} or [] or "" or '' around it still
        for file_included in file_inclusion:
            file_included = file_included[1:-1]
            file_included = file_included.strip()
            if not file_included in files_included:
                files_included.append(file_included)

    file_inclusion = re.findall('^' + valid_for_filename + '$', line)

    if len(file_inclusion) > 0:
        for file_included in file_inclusion:
            file_included = file_included.strip()
            if not file_included in files_included:
                files_included.append(file_included)

    file_inclusion = re.findall('^' + valid_for_filename + '[,\\} $]', line)

    if len(file_inclusion) > 0:
        for file_included in file_inclusion:
            file_included = file_included.strip()
            if not file_included in files_included:
                files_included.append(file_included)

    file_inclusion = re.findall('\\s*' + valid_for_filename + '\\s*$', line)

    if len(file_inclusion) > 0:
        for file_included in file_inclusion:
            file_included = file_included.strip()
            if not file_included in files_included:
                files_included.append(file_included)

    if files_included != ['ERROR']:
        files_included = files_included[1:] # cut off the dummy
    #    write_message(line)
    #    write_message('can\'t match this for some reason')
    for file_included in files_included:
        if file_included == '':
            files_included.remove(file_included)
        if ' ' in file_included:
            for subfile in file_included.split(' '):
                if not subfile in files_included:
                    files_included.append(subfile)
        if ',' in file_included:
            for subfile in file_included.split(' '):
                if not subfile in files_included:
                    files_included.append(subfile)

    return files_included

def clean_up(image_list):
    '''
    Removes all the intermediate stuff.

    @param: image_list ([string, string, ...]): the images to remove

    NOTE: when running this for later upload, it's not a good idea to
        remove the converted images!
    '''
    return # FIXME do not delete image files before upload
    for image_file in image_list:
        run_shell_command('rm ' + image_file)

def upload_to_site(marcxml, yes_i_know):
    '''
    makes the appropriate calls to bibupload to get the MARCXML record onto
    the site.

    @param: marcxml (string): the absolute location of the MARCXML that was
        generated by this programme
    @param: yes_i_know (boolean): if true, no confirmation.  if false, prompt.

    @output: a new record on the invenio site

    @return: None
    '''
    if not yes_i_know:
        wait_for_user(wrap_text_in_a_box('You are going to upload new ' +\
                                         'plots to the server.'))
    task_low_level_submission('bibupload', 'admin', '-a', marcxml)

help_string = '''
    name: plotextractor
    usage:
            python plotextractor.py -d tar/dir -s scratch/dir
            python plotextractor.py -i inputfile -u
            python plotextractor.py --arXiv=arXiv_id
            python plotextractor.py --recid=recids

    example:
            python extract_plots.py -d /some/path/with/tarballs
            python extract_plots.py -i input.txt --no-sdir --extract-text
            python plotextractor.py --arXiv=hep-ex/0101001
            python plotextractor.py --recid=13-20,29

    options:
        -d, --tardir=
            if you wish to do a batch of tarballs, search the tree
            rooted at this directory for them

        -s, --scratchdir=
            the directory for scratchwork (untarring, conversion, etc.).
            make sure that this directory is one of the allowed dirs in
            CFG_BIBUPLOAD_FFT_ALLOWED_LOCAL_PATHS to avoid errors.  with an
            sdir selected, one xml file will be generated for the whole
            batch of files processed, and it will live in this sdir.

        -i, --input=
            if you wish to give an input file for downloading files from
            arXiv (or wherever), this is the pointer to that file, which
            should contain urls to download, no more than 1 per line.  each
            line should be the url of a tarball or gzipped tarball, and
            each downloaded item will then be processed.

        -x, --extract-text
            if there is a pdf with the same base name as the tarball for each
            tarball this is being run on, running with the -x parameter will
            run pdftotext on each of these pdfs and store the result in the
            folder

        -f, --force
            if you want to overwrite everything that was done before, just
            force the script to overwrite it.  otherwise it will only run on
            things that haven't been run on yet (for use with tardir).

        -u, --call-bibupload, --yes-i-know
            if you want to upload the plots, ask to call bibupload.  appending
            the --yes-i-know flag bypasses bibupload's prompt to upload

        -r, --recid=
            if you want to process the tarball of one recid, use this tag.  it
            will also accept ranges (i.e. --recid=13-20)

        -t, --tarball=
            for processing one tarball.

        -q, --squash
            if you want to squash all MARC into a single MARC file (for easier
            and faster bibuploading)

    description: extracts plots from a tarfile from arXiv and generates
        MARCXML that links figures and their captions.  converts all
        images to PNG format.
'''

def usage():
    write_message(help_string)

if __name__ == '__main__':
    main()
