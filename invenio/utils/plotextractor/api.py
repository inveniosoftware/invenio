# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""API for plotextractor utility."""

import os

from invenio.base.globals import cfg
from invenio.utils.shell import run_shell_command

from .cli import (
    extract_captions,
    extract_context,
    get_defaults,
)
from .converter import convert_images, untar
from .getter import harvest_single
from .output_utils import (
    create_MARC,
    create_contextfiles,
    prepare_image_data,
    remove_dups
)


def get_plots(tarball):
    """Return a list of found and converted plots given a tarball."""
    sub_dir, dummy = get_defaults(tarball, cfg['CFG_TMPDIR'], "")

    tex_files = None
    image_list = None

    dummy, image_list, tex_files = untar(
        tarball,
        sub_dir
    )

    converted_image_list = convert_images(image_list)
    extracted_image_data = []
    if tex_files == [] or tex_files is None:
        # Its not a tarball
        run_shell_command('rm -r %s', (sub_dir,))
    else:
        for tex_file in tex_files:
            # Extract images, captions and labels
            partly_extracted_image_data = extract_captions(tex_file,
                                                           sub_dir,
                                                           converted_image_list)
            if partly_extracted_image_data:
                # Add proper filepaths and do various cleaning
                cleaned_image_data = prepare_image_data(
                    partly_extracted_image_data,
                    tex_file, converted_image_list)
                # Using prev. extracted info, get contexts for each
                # image found
                extracted_image_data.extend(
                    (extract_context(tex_file, cleaned_image_data)))
    return extracted_image_data


def get_marcxml_plots_from_tarball(tarball):
    """Given a path to a tar archive, return MARCXML of plots."""
    extracted_image_data = get_plots(str(tarball))
    if extracted_image_data:
        extracted_image_data = remove_dups(extracted_image_data)
        image_marc_xml = create_MARC(extracted_image_data, tarball, None)
        if image_marc_xml:
            create_contextfiles(extracted_image_data)
            return ('<?xml version="1.0" encoding="UTF-8"?>\n<collection>\n'
                    '{0}\n</collection>'.format(image_marc_xml))


def get_tarball_from_arxiv(arxiv_id, save_to_folder):
    """Download and return path to arXiv tarball for given article."""
    if not os.path.exists(save_to_folder):
        os.makedirs(save_to_folder)
    tarball, dummy = harvest_single(
        arxiv_id,
        save_to_folder,
        ["tarball"]
    )
    return tarball


def get_pdf_from_arxiv(arxiv_id, save_to_folder):
    """Download and return path to arXiv tarball for given article."""
    if not os.path.exists(save_to_folder):
        os.makedirs(save_to_folder)
    dummy, pdf = harvest_single(
        arxiv_id,
        save_to_folder,
        ["pdf"]
    )
    return pdf
