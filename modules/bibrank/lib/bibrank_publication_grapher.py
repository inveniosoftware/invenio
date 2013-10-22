# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
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

from invenio.config import CFG_SITE_URL, CFG_WEBDIR
from invenio.bibrank_grapher import create_temporary_image, write_coordinates_in_tmp_file

def html_image(filename, width, height):
    """
    Returns html code for showing publication graph image (with lightbox js effect)
    @param filename: str (graph image name)
    @param width: int (image width)
    @param height: int (image height)
    @return: str (html code)
    """
    html = """<a href='%s/img/%s' rel="lightbox"> <img src='%s/img/%s' width="%s" height="%s"
            alt=""> </a>""" % (CFG_SITE_URL, filename, CFG_SITE_URL, filename, str(width), str(height))
    return html

def create_graph_image(graph_file_name, graph_data):
    """
    Creates a new graph image with the given data.
    @param graph_file_name: str (graph image name)
    @param graph_data: list (data for the graph plot)
    @return: str (full name of the graph image)
    """
    res = ''
    if not os.path.exists("%s/img/tmp" % (CFG_WEBDIR)):
        os.mkdir("%s/img/tmp" % (CFG_WEBDIR))
    if not os.path.exists("%s/img/tmp/%s" % (CFG_WEBDIR, graph_file_name[0])):
        os.mkdir("%s/img/tmp/%s" % (CFG_WEBDIR, graph_file_name[0]))
    datas_info = write_coordinates_in_tmp_file([graph_data])
    years = [tup[0] for tup in graph_data]
    graph = create_temporary_image(graph_file_name, 'pubs_per_year', datas_info[0], 'Year',
                                            'Times published', [0, 0], datas_info[1], [], ' ', years)
    graph_image = graph[0]
    graph_source_file = graph[1]
    if graph_image and graph_source_file and os.path.exists(graph_source_file):
        os.unlink(datas_info[0])
        res = graph_image
    return res

def get_graph_code(graph_file_name, graph_data):
    """
    Creates HTML code refering to the 'publications per year' graph image.
    If the graph image does not exist in the filesystem, it creates a new one.
    @param graph_file_name: str (graph image name)
    @param graph_data: list (data for the graph plot)
    @return: str (html code)
    """
    html_graph_code = ''
    if os.path.exists('%s/img/tmp/%s/%s.png' % (CFG_WEBDIR, graph_file_name[0], graph_file_name)):
        graph_image = 'tmp/%s/%s.png' % (graph_file_name[0], graph_file_name)
        html_graph_code = """<p>%s""" % html_image(graph_image, 350, 200)
    else:
        graph_image = create_graph_image(graph_file_name, graph_data)
        html_graph_code = """<p>%s""" % html_image(graph_image, 350, 200)
    return html_graph_code
