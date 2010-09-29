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

import os
import re

from invenio.shellutils import run_shell_command
from invenio.plotextractor_output_utils import get_converted_image_name, \
                                               write_message, write_messages

def untar(tarball, sdir):
    '''
    Here we decide if our file is actually a tarball (sometimes the
    'tarballs' gotten from arXiv aren't actually tarballs.  If they
    'contain' only the TeX file, then they are just that file.), then
    we untar it if so and decide which of its constituents are the
    TeX file and which are the images.

    @param: tarball (string): the name of the tar file from arXiv
    @param: dir (string): the directory where we would like it untarred to

    @return: (image_list, tex_file) (([string, string, ...], string)):
        list of images in the tarball and the name of the TeX file in the
        tarball.
    '''

    tarball = check_for_gzip(tarball, sdir)
    dummy1, cmd_out, cmd_err = run_shell_command('file ' + tarball)

    tarball_output = 'tar archive'
    if re.search(tarball_output, cmd_out) == None:
        run_shell_command('rm ' + tarball)
        return ([], None)

    cmd = 'tar xvf ' + tarball + ' -C ' + sdir
    dummy1, cmd_out, cmd_err = run_shell_command(cmd)

    if cmd_err != '':
        return ([], None)

    run_shell_command('rm ' + tarball)
    cmd_out = cmd_out.split('\n')

    tex_output_contains = 'TeX'

    tex_file_extension = 'tex'
    image_output_contains = 'image'
    eps_output_contains = '- type eps'
    ps_output_contains = 'Postscript'

    image_list = []
    might_be_tex = []

    for extracted_file in cmd_out:
        if extracted_file == '':
            break

        # ensure we are actually looking at the right file
        extracted_file = os.path.join(sdir, extracted_file)

        dummy1, cmd_out, dummy2 = run_shell_command('file ' + extracted_file)

        # is it TeX?
        if cmd_out.find(tex_output_contains) > -1:
            might_be_tex.append(extracted_file)

        # is it an image?
        elif cmd_out.lower().find(image_output_contains) > cmd_out.find(':') \
                or \
                cmd_out.lower().find(eps_output_contains) > cmd_out.find(':')\
                or \
                cmd_out.find(ps_output_contains) > cmd_out.find(':'):
            # we have "image" in the output, and it is not in the filename
            # i.e. filename.ext: blah blah image blah blah
            image_list.append(extracted_file)

        # if neither, maybe it is TeX or an image anyway, otherwise,
        # we don't care
        else:
            if extracted_file.split('.')[-1] == tex_file_extension:
                # we might have tex source!
                might_be_tex.append(extracted_file)
            else:
                if extracted_file.split('.')[-1] in ['eps', 'png',\
                    'ps', 'jpg']:
                    # we might have an image!
                    image_list.append(extracted_file)
                #else:
                    # we don't care about it
                    #run_shell_command('rm ' + extracted_file)

    if might_be_tex == []:
        # well, that's tragic
        write_message('could not find TeX file in tar archive')
        return ([], [])

    return (image_list, might_be_tex)

def check_for_gzip(tfile, sdir):
    '''
    Was that tarball also gzipped?  Let's find out!

    @param: file (string): the name of the object (so we can gunzip, if
        that's necessary)
    @param: sdir (string): the directory to gunzip the file to if necessary

    @output: a gunzipped file in the directory of choice, if that's necessary

    @return new_file (string): The name of the file after gunzipping or the
        original name of the file if that wasn't necessary
    '''

    gzip_contains = 'gzip compressed data'
    gunzip = 'gunzip -c '

    dummy1, cmd_out, dummy2 = run_shell_command('file ' + tfile)

    if cmd_out.find(gzip_contains) > -1:
        # we have a gzip!
        # so gzip is retarded and won't accept any file that doesn't end
        # with .gz.  sad.
        cmd = 'cp ' + tfile + ' ' + tfile + '.tar.gz'
        run_shell_command(cmd)
        new_dest = os.path.join(os.path.split(tfile)[0], 'tmp.tar')
        run_shell_command('touch ' + new_dest)
        cmd = gunzip + tfile + '.tar.gz'
        dummy1, cmd_out, cmd_err = run_shell_command(cmd)
        tarfile = open(new_dest, 'w')
        tarfile.write(cmd_out)
        tarfile.close()
        cmd = 'rm ' + tfile + '.tar.gz'
        run_shell_command(cmd)
        return new_dest

    return tfile

def convert_images(image_list):
    '''
    Here we figure out the types of the images that were extracted from
    the tarball and determine how to convert them into PNG.

    @param: image_list ([string, string, ...]): the list of image files
        extracted from the tarball in step 1

    @return: image_list ([str, str, ...]): The list of image files when all
        have been converted to PNG format.
    '''

    png_output_contains = 'PNG image data'
    ps_output_contains = 'Postscript'
    eps_output_contains = 'PostScript'

    ret_list = []

    for image_file in image_list:
        if os.path.isdir(image_file):
            continue

        # FIXME: here and everywhere else in the plot extractor
        # library the run shell command statements should be (1)
        # called with timeout in order to prevent runaway imagemagick
        # conversions; (2) the arguments should be passed properly so
        # that they are escaped.

        dummy1, cmd_out, dummy2 = run_shell_command('file ' + image_file)
        if cmd_out.find(png_output_contains) > -1:
            ret_list.append(image_file)
        else:
            # we're just going to assume that ImageMagick can convert all
            # the image types that we may be faced with
            # for sure it can do EPS->PNG and JPG->PNG and PS->PNG
            # and PSTEX->PNG
            converted_image_file = get_converted_image_name(image_file)

            convert_cmd = 'convert '

            dummy1, cmd_out, cmd_err = run_shell_command(convert_cmd +\
                    image_file + ' ' + converted_image_file)
            if cmd_err == '':
                ret_list.append(converted_image_file)
            else:
                write_message('convert failed on ' + image_file)

    return ret_list
