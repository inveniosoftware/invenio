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
import tempfile

from invenio.config import CFG_SITE_URL, CFG_WEBDIR

cfg_gnuplot_available = 1
try:
    import Gnuplot
except ImportError, e:
    cfg_gnuplot_available = 0

def write_coordinates_in_tmp_file(lists_coordinates):
    """
    Writes the graph coordinates in a temporary file for reading it later
    by the create_temporary_gnuplot_image method.
    lists_coordinates is a list of lists of this form:
    [[(1,3),(2,4),(3,5)],[(1,5),(2,5),(3,6)].
    This file is organized into one or more sets of 2 columns.
    Each set is separated from the others by two blank lines.
    Each intern list represents a set and each tuple a line in the file where fist element
    of the tuple is the element of the first column, and second element of the
    tuple is the element of the second column.
    With gnuplot, first column is used as  x coordinates, and second column as y coordinates.
    One set represents a curve in the graph.
    """
    fd, fname = tempfile.mkstemp(dir="%s/img/tmp" % CFG_WEBDIR)
    os.close(fd)
    file_dest = open(fname, 'a')
    max_y_datas = 0
    for list_elem in lists_coordinates:
        y_axe = []
        for key_value in list_elem:
            file_dest.write("%s %s\n" % (key_value[0], key_value[1]))
            y_axe.append(key_value[1])
        max_tmp = 0
        if y_axe:
            max_tmp = max(y_axe)
        if max_tmp > max_y_datas:
            max_y_datas = max_tmp
        file_dest.write("\n\n")
    file_dest.close()

    return [fname, max_y_datas]

def create_temporary_gnuplot_image(data_file, image_size, x_label, y_label, origin_tuple, y_max, intervals, graph_path):
    """ Wrapper for the Gnuplot module """
    # for different curves
    color_line_list = ['3', '4', '2', '9', '6']
    # gnuplot graph object
    g = Gnuplot.Gnuplot()
    if image_size:
        g('set terminal png tiny size %s,%s' % (image_size[0], image_size[1]))
    else:
        g('set terminal png medium')
    g('set output "%s/img/%s"' % (CFG_WEBDIR, graph_path))
    # standard options
    g('set origin %s,%s' % (origin_tuple[0], origin_tuple[1]))
    if x_label == '':
        g('unset xlabel')
    else:
        g.xlabel(s = x_label)
        if y_label == '':
            g('unset ylabel')
        else:
            g.ylabel(s = y_label)
    g('set bmargin 5')
    # let a place at the top of the graph
    g('set tmargin 1')
    g('set boxwidth 0.6 relative')
    g('set style fill solid 0.250000 border -1')
    # g('set xtics rotate')
    if len(intervals) > 1:
        g('set xrange [%s:%s]' % (str(intervals[0]), str(intervals[-1])))
    else:
        g('set xrange [%s:%s]' % (str(intervals[0]-1), str(intervals[0]+1)))
    g('set yrange [0:%s]' % str(y_max+2))
    plot_text = """plot "%s" index 0:0 using 1:2 title "" w steps lt %s lw 3"""  % (data_file, color_line_list[0])

    g('%s' % plot_text)

def create_graph_image(graph_file_name, graph_data, image_size=None):
    """
    Creates a new graph image with the given data.
    @param graph_file_name: str (graph image name)
    @param graph_data: list (data for the graph plot)
    @param image_size: list (image size)
    @return: str (path of the created graph image)
    """
    def create_dir_if_not_exists(dir_path):
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)

    create_dir_if_not_exists("%s/img/tmp" % (CFG_WEBDIR))
    create_dir_if_not_exists("%s/img/tmp/%s" % (CFG_WEBDIR, graph_file_name[0]))

    graph_coordinates_file, max_y = write_coordinates_in_tmp_file([graph_data])
    years = [tup[0] for tup in graph_data]
    graph_path = "tmp/%s/%s.png" % (graph_file_name[0], graph_file_name)
    create_temporary_gnuplot_image(graph_coordinates_file, image_size, 'Year', 'Times published', [0, 0], max_y, years, graph_path)

    if graph_coordinates_file and os.path.exists(graph_coordinates_file):
        os.unlink(graph_coordinates_file)

    return graph_path

def html_image(normal_image_path, icon_image_path):
    """
    Returns html code for showing publication graph image (with lightbox js effect)
    @param normal_image_path: str (normal sized image name)
    @param icon_image_path: str (icon sized image name)
    @return: str (html code)
    """
    html = """<a href='%s/img/%s' rel="lightbox"> <img src='%s/img/%s' alt="">
        </a>""" % (CFG_SITE_URL, normal_image_path, CFG_SITE_URL, icon_image_path)
    return html

def get_graph_code(graph_file_name, graph_data):
    """
    Creates HTML code referring to the 'publications per year' graph image.
    If the image does not exist in the filesystem, it creates a new one.
    @param graph_file_name: str (graph image name)
    @param graph_data: list (data for the graph plot)
    @return: str (html code)
    """
    def get_graph_path(graph_file_name, graph_data, image_size=None):
        graph_path = 'tmp/%s/%s.png' % (graph_file_name[0], graph_file_name)
        if os.path.exists('%s/img/%s' % (CFG_WEBDIR, graph_path)):
            return graph_path
        else:
            return create_graph_image(graph_file_name, graph_data, image_size)

    if cfg_gnuplot_available == 0 or not graph_file_name:
        return None

    normal_graph_path = get_graph_path(graph_file_name, graph_data)
    icon_graph_path = get_graph_path(graph_file_name + '_icon', graph_data, [350, 200])

    html_graph_code = html_image(normal_graph_path, icon_graph_path)
    return html_graph_code
