# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2010, 2011, 2014, 2015 CERN.
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

"""Plot extractor cli.

This programme will take a tarball from arXiv, untar it, convert all its
associated images to PNG, find the captions to the images detailed in the
included TeX document, and write MARCXML that reflects these associations.
"""

import getopt

import os

import re

import sys

import time

from tempfile import mkstemp

from invenio.config import CFG_PLOTEXTRACTOR_CONTEXT_EXTRACT_LIMIT, \
    CFG_PLOTEXTRACTOR_CONTEXT_SENTENCE_LIMIT, \
    CFG_PLOTEXTRACTOR_CONTEXT_WORD_LIMIT, CFG_PLOTEXTRACTOR_DISALLOWED_TEX, \
    CFG_SITE_URL, CFG_TMPSHAREDDIR
from invenio.legacy.bibsched.bibtask import task_low_level_submission
from invenio.utils.shell import Timeout, run_process_with_timeout, \
    run_shell_command
from invenio.utils.text import wait_for_user, wrap_text_in_a_box

from invenio_client import InvenioConnector

from .converter import convert_images, extract_text, untar
from .getter import get_list_of_all_matching_files, make_single_directory, \
    parse_and_download, tarballs_by_arXiv_id, tarballs_by_recids
from .output_utils import assemble_caption, create_MARC, create_contextfiles, \
    find_open_and_close_braces, get_image_location, get_tex_location, \
    prepare_image_data, remove_dups, write_message

assemble_caption, create_contextfiles, create_MARC, \
    find_open_and_close_braces, get_image_location, get_tex_location, \
    prepare_image_data, remove_dups, write_message


ARXIV_HEADER = 'arXiv:'
PLOTS_DIR = 'plots'

MAIN_CAPTION_OR_IMAGE = 0
SUB_CAPTION_OR_IMAGE = 1


def main():
    """The main program loop."""
    help_param = 'help'
    tarball_param = 'tarball'
    tardir_param = 'tdir'
    infile_param = 'input'
    sdir_param = 'sdir'
    extract_text_param = 'extract-text'
    force_param = 'force'
    upload_param = 'call-bibupload'
    upload_mode_param = 'upload-mode'
    yes_i_know_param = 'yes-i-know'
    recid_param = 'recid'
    with_docname_param = 'with-docname'
    with_doctype_param = 'with-doctype'
    with_docformat_param = 'with-docformat'
    arXiv_param = 'arXiv'
    squash_param = 'squash'
    refno_url_param = 'refno-url'
    refno_param = 'skip-refno'
    clean_param = 'clean'
    param_abbrs = 'h:t:d:s:i:a:l:xfuyr:qck'
    params = [help_param, tarball_param + '=', tardir_param + '=',
              sdir_param + '=', infile_param +
              '=', arXiv_param + '=', refno_url_param + '=',
              extract_text_param, force_param, upload_param, yes_i_know_param,
              recid_param + '=',
              squash_param, clean_param, refno_param, with_docname_param + '=',
              with_doctype_param + '=', with_docformat_param + '=',
              upload_mode_param + '=']
    try:
        opts, args = getopt.getopt(sys.argv[1:], param_abbrs, params)
    except getopt.GetoptError as err:
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
    squash_path = ""
    yes_i_know = False
    recids = None
    with_docname = None
    with_doctype = None
    with_docformat = None
    arXiv = None
    clean = False
    refno_url = CFG_SITE_URL
    skip_refno = False
    upload_mode = 'append'

    for opt, arg in opts:
        if opt in ['-h', '--' + help_param]:
            usage()
            sys.exit()
        elif opt in ['-t', '--' + tarball_param]:
            tarball = arg
        elif opt in ['-d', '--' + tardir_param]:
            tdir = arg
        elif opt in ['-i', '--' + infile_param]:
            infile = arg
        elif opt in ['-r', '--' + recid_param]:
            recids = arg
        elif opt in ['-a', '--' + arXiv_param]:
            arXiv = arg
        elif opt in ['--' + with_docname_param]:
            with_docname = arg
        elif opt in ['--' + with_doctype_param]:
            with_doctype = arg
        elif opt in ['--' + with_docformat_param]:
            with_docformat = arg
        elif opt in ['-s', '--' + sdir_param]:
            sdir = arg
        elif opt in ['-x', '--' + extract_text_param]:
            xtract_text = True
        elif opt in ['-f', '--' + force_param]:
            force = True
        elif opt in ['-u', '--' + upload_param]:
            upload_plots = True
        elif opt in ['--' + upload_mode_param]:
            upload_mode = arg
        elif opt in ['-q', '--' + squash_param]:
            squash = True
        elif opt in ['-y', '--' + yes_i_know_param]:
            yes_i_know = True
        elif opt in ['-c', '--' + clean_param]:
            clean = True
        elif opt in ['-l', '--' + refno_url_param]:
            refno_url = arg
        elif opt in ['-k', '--' + refno_param]:
            skip_refno = True
        else:
            usage()
            sys.exit()

    allowed_upload_modes = ('insert', 'append', 'correct', 'replace')
    if upload_mode not in allowed_upload_modes:
        write_message('Specified upload mode %s is not valid. Must be in %s' %
                      (upload_mode, ', '.join(allowed_upload_modes)))
        usage()
        sys.exit()

    if sdir is None:
        sdir = CFG_TMPSHAREDDIR
    elif not os.path.isdir(sdir):
        try:
            os.makedirs(sdir)
        except Exception:
            write_message('Error: We can\'t use this sdir.  using ' +
                          'CFG_TMPSHAREDDIR')
            sdir = CFG_TMPSHAREDDIR

    if skip_refno:
        refno_url = ""

    tars_and_gzips = []

    if tarball:
        tars_and_gzips.append(tarball)
    if tdir:
        filetypes = ['gzip compressed', 'tar archive', 'Tar archive']  # FIXME
        write_message('Currently processing any tarballs in ' + tdir)
        tars_and_gzips.extend(get_list_of_all_matching_files(tdir, filetypes))
    if infile:
        tars_and_gzips.extend(parse_and_download(infile, sdir))
    if recids:
        tars_and_gzips.extend(
            tarballs_by_recids(recids, sdir, with_docname, with_doctype,
                               with_docformat))
    if arXiv:
        tars_and_gzips.extend(tarballs_by_arXiv_id([arXiv], sdir))
    if not tars_and_gzips:
        write_message('Error: no tarballs to process!')
        sys.exit(1)

    if squash:
        squash_fd, squash_path = mkstemp(
            suffix="_" + time.strftime("%Y%m%d%H%M%S") + ".xml",
            prefix="plotextractor_", dir=sdir)
        os.write(
            squash_fd,
            '<?xml version="1.0" encoding="UTF-8"?>\n<collection>\n')
        os.close(squash_fd)

    for tarball in tars_and_gzips:
        recid = None
        if isinstance(tarball, tuple):
            tarball, recid = tarball
        process_single(tarball, sdir=sdir, xtract_text=xtract_text,
                       upload_plots=upload_plots, force=force,
                       squash=squash_path,
                       yes_i_know=yes_i_know, refno_url=refno_url,
                       clean=clean, recid=recid, upload_mode=upload_mode)
    if squash:
        squash_fd = open(squash_path, "a")
        squash_fd.write("</collection>\n")
        squash_fd.close()
        write_message("generated %s" % (squash_path,))
        if upload_plots:
            upload_to_site(squash_path, yes_i_know, upload_mode)


def process_single(tarball, sdir=CFG_TMPSHAREDDIR, xtract_text=False,
                   upload_plots=False, force=False, squash="",
                   yes_i_know=False, refno_url="",
                   clean=False, recid=None, upload_mode='append',
                   direct_xml_output=False):
    """Processe one tarball end-to-end.

    :param: tarball (string): the absolute location of the tarball we wish
        to process
    :param: sdir (string): where we should put all the intermediate files for
        the processing.  if you're uploading, this directory should be one
        of the ones specified in CFG_BIBUPLOAD_FFT_ALLOWED_LOCAL_PATHS, else
        the upload won't work
    :param: xtract_text (boolean): true iff you want to run pdftotext on the
        pdf versions of the tarfiles.  this programme assumes that the pdfs
        are named the same as the tarballs but with a .pdf extension.
    :param: upload_plots (boolean): true iff you want to bibupload the plots
        extracted by this process
    :param: force (boolean): force creation of new xml file
    :param: squash: write MARCXML output into a specified 'squash' file
        instead of single files.
    :param: yes_i_know: if True, no user interaction if upload_plots is True
    :param: refno_url: URL to the invenio-instance to query for refno.
    :param: clean: if True, everything except the original tarball, plots and
            context- files will be removed
    :param recid: the record ID linked to this tarball. Overrides C{refno_url}
    :param upload_mode: the mode in which to call bibupload
           (when C{upload_plots} is set to True.
    :return: marc_name(string): path to generated marcxml file
    """
    sub_dir, refno = get_defaults(tarball, sdir, refno_url, recid)
    if not squash:
        marc_name = os.path.join(sub_dir, '%s.xml' % (refno,))
        if force or not os.path.exists(marc_name):
            marc_fd = open(marc_name, 'w')
            marc_fd.write(
                '<?xml version="1.0" encoding="UTF-8"?>\n<collection>\n')
            marc_fd.close()
    else:
        marc_name = squash
    if xtract_text:
        extract_text(tarball)
    try:
        extracted_files_list, image_list, tex_files = untar(tarball, sub_dir)
    except Timeout:
        write_message('Timeout during tarball extraction on %s' % (tarball,))
        return None

    if tex_files == [] or tex_files is None:
        write_message('%s is not a tarball' % (os.path.split(tarball)[-1],))
        run_shell_command('rm -r %s', (sub_dir,))
        return

    converted_image_list = convert_images(image_list)
    write_message(
        'converted %d of %d images found for %s' % (len(converted_image_list),
                                                    len(image_list),
                                                    os.path.basename(tarball)))
    extracted_image_data = []

    for tex_file in tex_files:
        # Extract images, captions and labels
        partly_extracted_image_data = extract_captions(tex_file, sub_dir,
                                                       converted_image_list)
        if not partly_extracted_image_data == []:
            # Add proper filepaths and do various cleaning
            cleaned_image_data = prepare_image_data(
                partly_extracted_image_data,
                tex_file, converted_image_list)
            # Using prev. extracted info, get contexts for each image found
            extracted_image_data.extend(
                (extract_context(tex_file, cleaned_image_data)))
    extracted_image_data = remove_dups(extracted_image_data)

    marc_xml = None
    if not extracted_image_data == []:
        if refno_url == "":
            refno = None
        create_contextfiles(extracted_image_data)
        marc_xml = create_MARC(extracted_image_data, tarball, refno)
        if not squash:
            marc_xml += "\n</collection>"
        if marc_name:
            marc_fd = open(marc_name, 'a')
            marc_fd.write('%s\n' % (marc_xml,))
            marc_fd.close()
            if not squash:
                write_message('generated %s' % (marc_name,))
                if upload_plots:
                    upload_to_site(marc_name, yes_i_know, upload_mode)
    if clean:
        clean_up(extracted_files_list, image_list)

    if direct_xml_output is True:
        return marc_xml
    else:
        return marc_name


def clean_up(extracted_files_list, image_list):
    """Remove all the intermediate stuff.

    :param: extracted_files_list ([string, string, ...]): list of all
        extracted files
    :param: image_list ([string, string, ...]): list of the images to keep

    """
    for extracted_file in extracted_files_list:
        # Remove everything that is not in the image_list or is not a directory
        if extracted_file not in image_list and extracted_file[-1] != os.sep:
            run_shell_command('rm %s', (extracted_file,))


def get_defaults(tarball, sdir, refno_url, recid=None):
    """A function for parameter-checking.

    :param: tarball (string): the location of the tarball to be extracted
    :param: sdir (string): the location of the scratch directory for untarring,
        conversions, and the ultimate destination of the MARCXML
    :param: refno_url (string): server location on where to look for refno

    :param recid: (int) if set, overrides C{refno_url} and consider this record
    :return sdir, refno (string, string): the same
        arguments it was sent as is appropriate.
    """
    if not sdir or recid:
        # Missing sdir: using default directory: CFG_TMPDIR
        sdir = CFG_TMPSHAREDDIR
    else:
        sdir = os.path.split(tarball)[0]

    # make a subdir in the scratch directory for each tarball
    sdir = make_single_directory(sdir,
                                 os.path.split(tarball)[-1] + '_' + PLOTS_DIR)
    if recid:
        refno = str(recid)
    elif refno_url != "":
        refno = get_reference_number(tarball, refno_url)
        if refno is None:
            refno = os.path.basename(tarball)
            write_message('Error: can\'t find record id for %s' % (refno,))
    else:
        refno = os.path.basename(tarball)
        write_message("Skipping ref-no check")
    return sdir, refno


def get_reference_number(tarball, refno_url):
    """Attempt to determine the reference number of the file by searching.

    :param: tarball (string): the name of the tarball as downloaded from
        arXiv
    :param: refno_url (string): url of repository to check for a
        reference number for this record. If not set; returns None

    :return: refno (string): the reference number of the paper
    """
    if refno_url:
        server = InvenioConnector(refno_url)
        # we just need the name of the file
        tarball = os.path.split(tarball)[1]
        prefix = '037__a:'
        # the name right now looks like arXiv:hep-ph_9703009
        # or arXiv:0910.0476
        if tarball.startswith(ARXIV_HEADER):
            if len(tarball.split('_')) > 1:
                tarball = tarball.split(':')[1]
                arXiv_record = tarball.replace('_', '/')
            else:
                arXiv_record = tarball
            result = server.search(p=prefix + arXiv_record, of='id')
            if len(result) == 0:
                return None
            return str(result[0])
        arXiv_record = re.findall(
            '(([a-zA-Z\\-]+/\\d+)|(\\d+\\.\\d+))', tarball)
        if len(arXiv_record) > 1:
            arXiv_record = arXiv_record[0]
            result = server.search(p=prefix + arXiv_record, of='id')
            if len(result) > 0:
                return str(result[0])
        tarball_mod = tarball.replace('_', '/')
        arXiv_record = re.findall('(([a-zA-Z\\-]+/\\d+)|(\\d+\\.\\d+))',
                                  tarball_mod)
        if len(arXiv_record) > 1:
            arXiv_record = arXiv_record[0]
            result = server.search(p=prefix + arXiv_record, of='id')
            if len(result) > 0:
                return str(result[0])
    return None


def rotate_image(filename, line, sdir, image_list):
    """Rotate a image.

    Given a filename and a line, figure out what it is that the author
    wanted to do wrt changing the rotation of the image and convert the
    file so that this rotation is reflected in its presentation.

    :param: filename (string): the name of the file as specified in the TeX
    :param: line (string): the line where the rotate command was found

    :output: the image file rotated in accordance with the rotate command
    :return: True if something was rotated
    """
    file_loc = get_image_location(filename, sdir, image_list)
    degrees = re.findall('(angle=[-\\d]+|rotate=[-\\d]+)', line)

    if len(degrees) < 1:
        return False

    degrees = degrees[0].split('=')[-1].strip()

    if file_loc is None or file_loc == 'ERROR' or\
            not re.match('-*\\d+', degrees):
        return False

    degrees = str(0 - int(degrees))
    cmd_list = ['mogrify', '-rotate', degrees, file_loc]
    dummy, dummy, cmd_err = run_process_with_timeout(cmd_list)
    if cmd_err != '':
        return True
    else:
        return True


def get_context(lines, backwards=False):
    """Get context.

    Given a relevant string from a TeX file, this function will extract text
    from it as far as it is deemed contextually relevant, either backwards or
    forwards in the text.
    The level of relevance allowed is configurable. When it reaches some
    point in the text that is determined to be out of scope from the current
    context, like text that is identified as a new paragraph, a complex TeX
    structure ('/begin', '/end', etc.) etc., it will return the previously
    allocated text.

    For use when extracting text with contextual value for an figure or plot.

    :param lines (string): string to examine
    :param reversed (bool): are we searching backwards?

    :return context (string): extracted context
    """
    tex_tag = re.compile(r".*\\(\w+).*")
    sentence = re.compile(r"(?<=[.?!])[\s]+(?=[A-Z])")
    context = []

    word_list = lines.split()
    if backwards:
        word_list.reverse()

    # For each word we do the following:
    #   1. Check if we have reached word limit
    #   2. If not, see if this is a TeX tag and see if its 'illegal'
    #   3. Otherwise, add word to context
    for word in word_list:
        if len(context) >= CFG_PLOTEXTRACTOR_CONTEXT_WORD_LIMIT:
            break
        match = tex_tag.match(word)
        if match and match.group(1) in CFG_PLOTEXTRACTOR_DISALLOWED_TEX:
            # TeX Construct matched, return
            if backwards:
                # When reversed we need to go back and
                # remove unwanted data within brackets
                temp_word = ""
                while len(context):
                    temp_word = context.pop()
                    if '}' in temp_word:
                        break
            break
        context.append(word)

    if backwards:
        context.reverse()
    text = " ".join(context)
    sentence_list = sentence.split(text)

    if backwards:
        sentence_list.reverse()

    if len(sentence_list) > CFG_PLOTEXTRACTOR_CONTEXT_SENTENCE_LIMIT:
        return " ".join(
            sentence_list[:CFG_PLOTEXTRACTOR_CONTEXT_SENTENCE_LIMIT])
    else:
        return " ".join(sentence_list)


def extract_context(tex_file, extracted_image_data):
    """Extract context.

    Given a .tex file and a label name, this function will extract the text
    before and after for all the references made to this label in the text.
    The number of characters to extract before and after is configurable.

    :param tex_file (list): path to .tex file
    :param extracted_image_data ([(string, string, list), ...]):
        a list of tuples of images matched to labels and captions from
        this document.

    :return extracted_image_data ([(string, string, list, list),
        (string, string, list, list),...)]: the same list, but now containing
        extracted contexts
    """
    if os.path.isdir(tex_file) or not os.path.exists(tex_file):
        return []
    fd = open(tex_file)
    lines = fd.read()
    fd.close()

    # Generate context for each image and its assoc. labels
    new_image_data = []
    for image, caption, label in extracted_image_data:
        context_list = []

        # Generate a list of index tuples for all matches
        indicies = [match.span()
                    for match in re.finditer(r"(\\(?:fig|ref)\{%s\})" %
                                             (re.escape(label),),
                                             lines)]
        for startindex, endindex in indicies:
            # Retrive all lines before label until beginning of file
            i = startindex - CFG_PLOTEXTRACTOR_CONTEXT_EXTRACT_LIMIT
            if i < 0:
                text_before = lines[:startindex]
            else:
                text_before = lines[i:startindex]
            context_before = get_context(text_before, backwards=True)

            # Retrive all lines from label until end of file and get context
            i = endindex + CFG_PLOTEXTRACTOR_CONTEXT_EXTRACT_LIMIT
            text_after = lines[endindex:i]
            context_after = get_context(text_after)
            context_list.append(
                context_before + ' \\ref{' + label + '} ' + context_after)
        new_image_data.append((image, caption, label, context_list))
    return new_image_data


def extract_captions(tex_file, sdir, image_list, primary=True):
    """Extract captions.

    Take the TeX file and the list of images in the tarball (which all,
    presumably, are used in the TeX file) and figure out which captions
    in the text are associated with which images
    :param: lines (list): list of lines of the TeX file

    :param: tex_file (string): the name of the TeX file which mentions
        the images
    :param: sdir (string): path to current sub-directory
    :param: image_list (list): list of images in tarball
    :param: primary (bool): is this the primary call to extract_caption?

    :return: images_and_captions_and_labels ([(string, string, list),
        (string, string, list), ...]):
        a list of tuples representing the names of images and their
        corresponding figure labels from the TeX file
    """
    if os.path.isdir(tex_file) or not os.path.exists(tex_file):
        return []
    fd = open(tex_file)
    lines = fd.readlines()
    fd.close()

    # possible figure lead-ins
    figure_head = '\\begin{figure'  # also matches figure*
    figure_tail = '\\end{figure'  # also matches figure*
    picture_head = '\\begin{picture}'
    displaymath_head = '\\begin{displaymath}'
    subfloat_head = '\\subfloat'
    subfig_head = '\\subfigure'
    includegraphics_head = '\\includegraphics'
    epsfig_head = '\\epsfig'
    input_head = '\\input'
    # possible caption lead-ins
    caption_head = '\\caption'
    figcaption_head = '\\figcaption'
    label_head = '\\label'
    rotate = 'rotate='
    angle = 'angle='
    eps_tail = '.eps'
    ps_tail = '.ps'

    doc_head = '\\begin{document}'
    doc_tail = '\\end{document}'

    extracted_image_data = []
    cur_image = ''
    caption = ''
    labels = []
    active_label = ""

    # cut out shit before the doc head
    if primary:
        for line_index in range(len(lines)):
            if lines[line_index].find(doc_head) < 0:
                lines[line_index] = ''
            else:
                break

    # are we using commas in filenames here?
    commas_okay = False
    for dummy1, dummy2, filenames in \
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
            return extracted_image_data

        """
        FIGURE -
        structure of a figure:
        \begin{figure}
        \formatting...
        \includegraphics[someoptions]{FILENAME}
        \caption{CAPTION}  %caption and includegraphics may be switched!
        \end{figure}
        """

        index = line.find(figure_head)
        if index > -1:
            in_figure_tag = 1
            # some punks don't like to put things in the figure tag.  so we
            # just want to see if there is anything that is sitting outside
            # of it when we find it
            cur_image, caption, extracted_image_data = put_it_together(
                cur_image, caption,
                active_label, extracted_image_data,
                line_index, lines)

        # here, you jerks, just make it so that it's fecking impossible to
        # figure out your damn inclusion types

        index = max([line.find(eps_tail), line.find(ps_tail),
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
                filenames.extend(intelligently_find_filenames(
                    lines[line_index + 1],
                    commas_okay=commas_okay))
            if line_index < len(lines) - 2:
                filenames.extend(intelligently_find_filenames(
                    lines[line_index + 2],
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

        """
        Rotate and angle
        """
        index = max(line.find(rotate), line.find(angle))
        if index > -1:
            # which is the image associated to it?
            filenames = intelligently_find_filenames(line,
                                                     commas_okay=commas_okay)
            # try the line after and the line before
            if line_index + 1 < len(lines):
                filenames.extend(intelligently_find_filenames(
                    lines[line_index + 1],
                    commas_okay=commas_okay))
            if line_index > 1:
                filenames.extend(intelligently_find_filenames(
                    lines[line_index - 1],
                    commas_okay=commas_okay))
            already_tried = []
            for filename in filenames:
                if filename != 'ERROR' and filename not in already_tried:
                    if rotate_image(filename, line, sdir, image_list):
                        break
                    already_tried.append(filename)

        """
        INCLUDEGRAPHICS -
        structure of includegraphics:
        \includegraphics[someoptions]{FILENAME}
        """
        index = line.find(includegraphics_head)
        if index > -1:
            open_curly, open_curly_line, close_curly, dummy = \
                find_open_and_close_braces(line_index, index, '{', lines)
            filename = lines[open_curly_line][open_curly + 1:close_curly]
            if cur_image == '':
                cur_image = filename
            elif type(cur_image) == list:
                if type(cur_image[SUB_CAPTION_OR_IMAGE]) == list:
                    cur_image[SUB_CAPTION_OR_IMAGE].append(filename)
                else:
                    cur_image[SUB_CAPTION_OR_IMAGE] = [filename]
            else:
                cur_image = ['', [cur_image, filename]]

        """
        {\input{FILENAME}}
        \caption{CAPTION}

        This input is ambiguous, since input is also used for things like
        inclusion of data from other LaTeX files directly.
        """
        index = line.find(input_head)
        if index > -1:
            new_tex_names = intelligently_find_filenames(
                line, TeX=True,
                commas_okay=commas_okay)
            for new_tex_name in new_tex_names:
                if new_tex_name != 'ERROR':
                    new_tex_file = get_tex_location(new_tex_name, tex_file)
                    if new_tex_file and primary:  # to kill recursion
                        extracted_image_data.extend(extract_captions(
                                                    new_tex_file, sdir,
                                                    image_list,
                                                    primary=False))

        """PICTURE"""

        index = line.find(picture_head)
        if index > -1:
            # structure of a picture:
            # \begin{picture}
            # ....not worrying about this now
            # write_message('found picture tag')
            # FIXME
            pass

        """DISPLAYMATH"""

        index = line.find(displaymath_head)
        if index > -1:
            # structure of a displaymath:
            # \begin{displaymath}
            # ....not worrying about this now
            # write_message('found displaymath tag')
            # FIXME
            pass

        """
        CAPTIONS -
        structure of a caption:
        \caption[someoptions]{CAPTION}
        or
        \caption{CAPTION}
        or
        \caption{{options}{CAPTION}}
        """

        index = max([line.find(caption_head), line.find(figcaption_head)])
        if index > -1:
            open_curly, open_curly_line, close_curly, close_curly_line = \
                find_open_and_close_braces(line_index, index, '{', lines)

            cap_begin = open_curly + 1

            cur_caption = assemble_caption(
                open_curly_line, cap_begin,
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

        """
        SUBFLOATS -
        structure of a subfloat (inside of a figure tag):
        \subfloat[CAPTION]{options{FILENAME}}

        also associated with the overall caption of the enclosing figure
        """

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

            sub_caption = assemble_caption(
                open_square_line,
                cap_begin, close_square_line, close_square, lines)
            caption[SUB_CAPTION_OR_IMAGE].append(sub_caption)

            open_curly, open_curly_line, close_curly, dummy = \
                find_open_and_close_braces(close_square_line,
                                           close_square, '{', lines)
            sub_image = lines[open_curly_line][open_curly + 1:close_curly]

            cur_image[SUB_CAPTION_OR_IMAGE].append(sub_image)

        """
        SUBFIGURES -
        structure of a subfigure (inside a figure tag):
        \subfigure[CAPTION]{
        \includegraphics[options]{FILENAME}}

        also associated with the overall caption of the enclosing figure
        """

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

            sub_caption = assemble_caption(open_square_line,
                                           cap_begin, close_square_line,
                                           close_square, lines)
            caption[SUB_CAPTION_OR_IMAGE].append(sub_caption)

            index_cpy = index

            # find the graphics tag to get the filename
            # it is okay if we eat lines here
            index = line.find(includegraphics_head)
            while index == -1 and (line_index + 1) < len(lines):
                line_index += 1
                line = lines[line_index]
                index = line.find(includegraphics_head)
            if line_index == len(lines):
                # didn't find the image name on line
                line_index = index_cpy

            open_curly, open_curly_line, close_curly, dummy = \
                find_open_and_close_braces(line_index,
                                           index, '{', lines)
            sub_image = lines[open_curly_line][open_curly + 1:close_curly]

            cur_image[SUB_CAPTION_OR_IMAGE].append(sub_image)

        """
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
        """
        index = line.find(label_head)
        if index > -1 and in_figure_tag:
            open_curly, open_curly_line, close_curly, dummy =\
                find_open_and_close_braces(line_index,
                                           index, '{', lines)
            label = lines[open_curly_line][open_curly + 1:close_curly]
            if label not in labels:
                active_label = label
            labels.append(label)

        """
        FIGURE

        important: we put the check for the end of the figure at the end
        of the loop in case some pathological person puts everything in one
        line
        """
        index = max([line.find(figure_tail), line.find(doc_tail)])
        if index > -1:
            in_figure_tag = 0
            cur_image, caption, extracted_image_data = \
                put_it_together(cur_image, caption, active_label,
                                extracted_image_data,
                                line_index, lines)
        """
        END DOCUMENT

        we shouldn't look at anything after the end document tag is found
        """

        index = line.find(doc_tail)
        if index > -1:
            break

    return extracted_image_data


def put_it_together(cur_image, caption, context, extracted_image_data,
                    line_index, lines):
    """Put it together.

    Takes the current image(s) and caption(s) and assembles them into
    something useful in the extracted_image_data list.

    :param: cur_image (string || list): the image currently being dealt with,
        or the list of images, in the case of subimages
    :param: caption (string || list): the caption or captions currently in
        scope
    :param: extracted_image_data ([(string, string), (string, string), ...]):
        a list of tuples of images matched to captions from this document.
    :param: line_index (int): the index where we are in the lines (for
        searchback and searchforward purposes)
    :param: lines ([string, string, ...]): the lines in the TeX

    :return: (cur_image, caption, extracted_image_data): the same arguments it
        was sent, processed appropriately
    """
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
                extracted_image_data.append(
                    (cur_image[MAIN_CAPTION_OR_IMAGE],
                     caption[MAIN_CAPTION_OR_IMAGE],
                     context))
            if type(cur_image[MAIN_CAPTION_OR_IMAGE]) == list:
                # why is the main image a list?
                # it's a good idea to attach the main caption to other
                # things, but the main image can only be used once
                cur_image[MAIN_CAPTION_OR_IMAGE] = ''

            if type(cur_image[SUB_CAPTION_OR_IMAGE]) == list:
                if type(caption[SUB_CAPTION_OR_IMAGE]) == list:
                    for index in \
                            range(len(cur_image[SUB_CAPTION_OR_IMAGE])):
                        if index < len(caption[SUB_CAPTION_OR_IMAGE]):
                            long_caption = \
                                caption[MAIN_CAPTION_OR_IMAGE] + ' : ' + \
                                caption[SUB_CAPTION_OR_IMAGE][index]
                        else:
                            long_caption = \
                                caption[MAIN_CAPTION_OR_IMAGE] + ' : ' + \
                                'Caption not extracted'
                        extracted_image_data.append(
                            (cur_image[SUB_CAPTION_OR_IMAGE][index],
                             long_caption, context))

                else:
                    long_caption = caption[MAIN_CAPTION_OR_IMAGE] + \
                        ' : ' + caption[SUB_CAPTION_OR_IMAGE]
                    for sub_image in cur_image[SUB_CAPTION_OR_IMAGE]:
                        extracted_image_data.append(
                            (sub_image, long_caption, context))

            else:
                if type(caption[SUB_CAPTION_OR_IMAGE]) == list:
                    long_caption = caption[MAIN_CAPTION_OR_IMAGE]
                    for sub_cap in caption[SUB_CAPTION_OR_IMAGE]:
                        long_caption = long_caption + ' : ' + sub_cap
                    extracted_image_data.append(
                        (cur_image[SUB_CAPTION_OR_IMAGE], long_caption,
                         context))
                else:
                    # wtf are they lists for?
                    extracted_image_data.append(
                        (cur_image[SUB_CAPTION_OR_IMAGE],
                         caption[SUB_CAPTION_OR_IMAGE], context))

        elif type(cur_image) == list:
            if cur_image[MAIN_CAPTION_OR_IMAGE] != '':
                extracted_image_data.append(
                    (cur_image[MAIN_CAPTION_OR_IMAGE], caption, context))
            if type(cur_image[SUB_CAPTION_OR_IMAGE]) == list:
                for image in cur_image[SUB_CAPTION_OR_IMAGE]:
                    extracted_image_data.append((image, caption, context))
            else:
                extracted_image_data.append(
                    (cur_image[SUB_CAPTION_OR_IMAGE], caption, context))

        elif type(caption) == list:
            if caption[MAIN_CAPTION_OR_IMAGE] != '':
                extracted_image_data.append(
                    (cur_image, caption[MAIN_CAPTION_OR_IMAGE], context))
            if type(caption[SUB_CAPTION_OR_IMAGE]) == list:
                # multiple caps for one image:
                long_caption = caption[MAIN_CAPTION_OR_IMAGE]
                for subcap in caption[SUB_CAPTION_OR_IMAGE]:
                    if long_caption != '':
                        long_caption += ' : '
                    long_caption += subcap
                extracted_image_data.append((cur_image, long_caption, context))
            else:
                extracted_image_data.append(
                    (cur_image, caption[SUB_CAPTION_OR_IMAGE]. context))

        else:
            extracted_image_data.append((cur_image, caption, context))

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
            if m:
                open_curly = m.start()
                open_curly, open_curly_line, close_curly, \
                    close_curly_line = find_open_and_close_braces(
                        line_index - searchback, open_curly, '{', lines)

                cap_begin = open_curly + 1

                caption = assemble_caption(open_curly_line, cap_begin,
                                           close_curly_line, close_curly,
                                           lines)

                if type(cur_image) == list:
                    extracted_image_data.append(
                        (cur_image[MAIN_CAPTION_OR_IMAGE], caption, context))
                    for sub_img in cur_image[SUB_CAPTION_OR_IMAGE]:
                        extracted_image_data.append(
                            (sub_img, caption, context))
                else:
                    extracted_image_data.append((cur_image, caption, context))
                    break

        if caption == '':
            for searchforward in range(REASONABLE_SEARCHFORWARD):
                if line_index + searchforward >= len(lines):
                    break

                fwd_line = lines[line_index + searchforward]
                m = re.search(curly_no_tag_preceding, fwd_line)

                if m:
                    open_curly = m.start()
                    open_curly, open_curly_line, close_curly,\
                        close_curly_line = find_open_and_close_braces(
                            line_index + searchforward, open_curly, '{', lines)

                    cap_begin = open_curly + 1

                    caption = assemble_caption(open_curly_line,
                                               cap_begin, close_curly_line,
                                               close_curly, lines)

                    if type(cur_image) == list:
                        extracted_image_data.append(
                            (cur_image[MAIN_CAPTION_OR_IMAGE],
                             caption, context))
                        for sub_img in cur_image[SUB_CAPTION_OR_IMAGE]:
                            extracted_image_data.append(
                                (sub_img, caption, context))
                    else:
                        extracted_image_data.append(
                            (cur_image, caption, context))
                    break

        if caption == '':
            if type(cur_image) == list:
                extracted_image_data.append(
                    (cur_image[MAIN_CAPTION_OR_IMAGE], 'No caption found',
                     context))
                for sub_img in cur_image[SUB_CAPTION_OR_IMAGE]:
                    extracted_image_data.append(
                        (sub_img, 'No caption', context))
            else:
                extracted_image_data.append(
                    (cur_image, 'No caption found', context))

    elif caption != '' and cur_image == '':
        if type(caption) == list:
            long_caption = caption[MAIN_CAPTION_OR_IMAGE]
            for subcap in caption[SUB_CAPTION_OR_IMAGE]:
                long_caption = long_caption + ': ' + subcap
        else:
            long_caption = caption
        extracted_image_data.append(('', 'noimg' + long_caption, context))

    # if we're leaving the figure, no sense keeping the data
    cur_image = ''
    caption = ''

    return cur_image, caption, extracted_image_data


def intelligently_find_filenames(line, TeX=False, ext=False,
                                 commas_okay=False):
    """Intelligently find filenames.

    Find the filename in the line.  We don't support all filenames!  Just eps
    and ps for now.

    :param: line (string): the line we want to get a filename out of

    :return: filename ([string, ...]): what is probably the name of the file(s)
    """
    files_included = ['ERROR']

    if commas_okay:
        valid_for_filename = '\\s*[A-Za-z0-9\\-\\=\\+/\\\\_\\.,%#]+'
    else:
        valid_for_filename = '\\s*[A-Za-z0-9\\-\\=\\+/\\\\_\\.%#]+'

    if ext:
        valid_for_filename += '\.e*ps[texfi2]*'

    if TeX:
        valid_for_filename += '[\.latex]*'

    file_inclusion = re.findall('=' + valid_for_filename + '[ ,]', line)

    if len(file_inclusion) > 0:
        # right now it looks like '=FILENAME,' or '=FILENAME '
        for file_included in file_inclusion:
            files_included.append(file_included[1:-1])

    file_inclusion = re.findall('(?:[ps]*file=|figure=)' +
                                valid_for_filename + '[,\\]} ]*', line)

    if len(file_inclusion) > 0:
        # still has the =
        for file_included in file_inclusion:
            part_before_equals = file_included.split('=')[0]
            if len(part_before_equals) != file_included:
                file_included = file_included[
                    len(part_before_equals) + 1:].strip()
            if file_included not in files_included:
                files_included.append(file_included)

    file_inclusion = re.findall(
        '["\'{\\[]' + valid_for_filename + '[}\\],"\']',
        line)

    if len(file_inclusion) > 0:
        # right now it's got the {} or [] or "" or '' around it still
        for file_included in file_inclusion:
            file_included = file_included[1:-1]
            file_included = file_included.strip()
            if file_included not in files_included:
                files_included.append(file_included)

    file_inclusion = re.findall('^' + valid_for_filename + '$', line)

    if len(file_inclusion) > 0:
        for file_included in file_inclusion:
            file_included = file_included.strip()
            if file_included not in files_included:
                files_included.append(file_included)

    file_inclusion = re.findall('^' + valid_for_filename + '[,\\} $]', line)

    if len(file_inclusion) > 0:
        for file_included in file_inclusion:
            file_included = file_included.strip()
            if file_included not in files_included:
                files_included.append(file_included)

    file_inclusion = re.findall('\\s*' + valid_for_filename + '\\s*$', line)

    if len(file_inclusion) > 0:
        for file_included in file_inclusion:
            file_included = file_included.strip()
            if file_included not in files_included:
                files_included.append(file_included)

    if files_included != ['ERROR']:
        files_included = files_included[1:]  # cut off the dummy

    for file_included in files_included:
        if file_included == '':
            files_included.remove(file_included)
        if ' ' in file_included:
            for subfile in file_included.split(' '):
                if subfile not in files_included:
                    files_included.append(subfile)
        if ',' in file_included:
            for subfile in file_included.split(' '):
                if subfile not in files_included:
                    files_included.append(subfile)

    return files_included


def upload_to_site(marcxml, yes_i_know, upload_mode="append"):
    """Upload to site.

    makes the appropriate calls to bibupload to get the MARCXML record onto
    the site. Uploads in "correct" mode.

    :param: marcxml (string): the absolute location of the MARCXML that was
        generated by this programme
    :param: yes_i_know (boolean): if true, no confirmation.  if false, prompt.

    :output: a new record on the invenio site

    :return: None
    """
    if not yes_i_know:
        wait_for_user(wrap_text_in_a_box('You are going to upload new ' +
                                         'plots to the server.'))
    task_low_level_submission(
        'bibupload', 'admin',
        upload_mode and '--' + upload_mode or '', marcxml)

help_string = """
    name: plotextractor
    usage:
            plotextractor -d tar/dir -s scratch/dir
            plotextractor -i inputfile -u
            plotextractor --arXiv=arXiv_id
            plotextractor --recid=recids

    example:
            plotextractor -d /some/path/with/tarballs
            plotextractor -i input.txt --no-sdir --extract-text
            plotextractor --arXiv=hep-ex/0101001
            plotextractor --recid=13-20,29

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

        -c, --clean
            if you wish to do delete all non-essential files that were
            extracted.

        -u, --call-bibupload, --yes-i-know
            if you want to upload the plots, ask to call bibupload.  appending
            the --yes-i-know flag bypasses bibupload's prompt to upload

        --upload-mode=
            if you use --call-bibupload option, allows to specify in which
            mode BibUpload should process the input. Can take values:
            'insert', 'append', 'correct' or 'replace'

        -l, --refno-url
            Specify an URL to the invenio-instance to query for refno.
            Defaults to CFG_SITE_URL.

        -k, --skip-refno
            allows you to skip any refno check

        -r, --recid=
            if you want to process the tarball of one recid, use this tag.  it
            will also accept ranges (i.e. --recid=13-20)

        --with-docname=
            allow to choose files to process on the basis of their docname,
            when used with --recid option

        --with-doctype=
            allow to choose files to process on the basis of their doctype,
            when used with --recid option

        --with-docformat=
            allow to choose files to process on the basis of their format,
            when used with --recid option

        -a, --arXiv=
            if you want to process the tarball of one arXiv id, use this tag.

        -t, --tarball=
            for processing one tarball.

        -q, --squash
            if you want to squash all MARC into a single MARC file (for easier
            and faster bibuploading)

        -h, --help
            Print this help and exit.

    description: extracts plots from a tarfile from arXiv and generates
        MARCXML that links figures and their captions.  converts all
        images to PNG format.
"""


def usage():
    """Print usage."""
    write_message(help_string)
