# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2013 CERN.
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

__revision__ = "$Id$"

import os
import tempfile

from invenio.config import CFG_TMPDIR, CFG_WEBDIR
from invenio.websubmit_config import *

## test gnuplot presence:
cfg_gnuplot_available = 1
try:
    import Gnuplot
except ImportError, e:
    cfg_gnuplot_available = 0

def write_coordinates_in_tmp_file(lists_coordinates):
    """write the graph coordinates in a temporary file for reading it later
    by the create_temporary_image method
    lists_coordinates is a list of list of this form:
    [[(1,3),(2,4),(3,5)],[(1,5),(2,5),(3,6)]
    This file is organized into one or more sets of 2 columns.
    Each set is separated from the others by two blank lines.
    Each intern list represents a set and each tuple a line in the file where fist element
    of the tuple is the element of the first column, and second element of the
    tuple is the element of the second column.
    With gnuplot, first column is used as  x coordinates, and second column as y coordinates.
    One set represents a curve in the graph.
    """
    max_y_datas = 0
    (fd, fname) = tempfile.mkstemp(prefix='bibrank_grapher_', dir=CFG_TMPDIR)
    file_dest = os.fdopen(fd, 'a')
    for list_elem in lists_coordinates:
        y_axe = []
        #prepare data and store them in a file
        for key_value in list_elem:
            file_dest.write("%s %s\n"%(key_value[0], key_value[1]))
            y_axe.append(key_value[1])
        max_tmp = 0
        if y_axe:
            max_tmp = max(y_axe)
        if max_tmp > max_y_datas:
            max_y_datas = max_tmp
        file_dest.write("\n\n")
    file_dest.close()

    return [fname, max_y_datas]

def create_temporary_image(recid, kind_of_graphe, data_file, x_label, y_label, origin_tuple, y_max, docid_list, graphe_titles, intervals):
    """From a temporary file, draw a gnuplot graph
    The arguments are as follows:
    recid          - record ID
    kind_of_graph  - takes one of these values : "citation" ,"download_history", "download_users"
                     All the commons gnuplot commands for these cases, are written at the beginning
                     After the particular commands dependaing of each case are written.
    data_file      - Name of the temporary file which contains the gnuplot datas used to plot the graph.
                     This file is organized into one or more sets of 2 columns.
                     First column contains x coordinates, and second column contains y coordinates.
                     Each set is separated from the others by two blank lines.
    x_label        - Name of the x axe.
    y_label        - Name of the y axe.
    origin_tuple   - Reference coordinates for positionning the graph.
    y_max          - Max value of y. Used to set y range.
    docid_list     - In download_history case, docid_list is used to plot multiple curves.
    graphe_titles  - List of graph titles. It's used to name the curve in the legend.
    intervals      - x tics location and xrange specification"""

    if cfg_gnuplot_available == 0:
        return (None, None)
    #For different curves
    color_line_list = ['4', '3', '2', '9', '6']
    #Gnuplot graphe object
    g = Gnuplot.Gnuplot()
    #Graphe name: file to store graph
    graphe_name = "tmp_%s_%s_stats.png" % (kind_of_graphe, recid)
    g('set terminal png small')
    g('set output "%s/img/%s"' % (CFG_WEBDIR, graphe_name))
    len_intervals = len(intervals)
    len_docid_list = len(docid_list)
    # Standard options
    g('set size 0.5,0.5')
    g('set origin %s,%s'% (origin_tuple[0], origin_tuple[1]))
    if x_label == '':
        g('unset xlabel')
    else:
        g.xlabel(s = x_label)
    if x_label == '':
        g('unset ylabel')
    else:
        g.ylabel(s = y_label)
    g('set bmargin 5')
    #let a place at the top of the graph
    g('set tmargin 1')

    #Will be passed to g at the end to plot the graphe
    plot_text = ""

    if kind_of_graphe == 'download_history':
        g('set xdata time') #Set x scale as date
        g('set timefmt "%m/%Y"') #Inform about format in file .dat
        g('set format x "%b %y"') #Format displaying
        if len(intervals) > 1 :
            g('set xrange ["%s":"%s"]' % (intervals[0], intervals[len_intervals-1]))
        y_offset = max(3, float(y_max)/60)
        g('set yrange [0:%s]' %str(y_max + y_offset))
        if len_intervals > 1 and len_intervals <= 12:
            g('set xtics rotate %s' % str(tuple(intervals)))#to prevent duplicate tics
        elif len_intervals > 12 and len_intervals <= 24:
            g('set xtics rotate "%s", 7776000, "%s"' % (intervals[0], intervals[len_intervals-1]))            #3 months intervalls
        else :
            g('set xtics rotate "%s",15552000, "%s"' % (intervals[0], intervals[len_intervals-1]))            #6 months intervalls

        if len_docid_list <= 1: #Only one curve
            #g('set style fill solid 0.25')
            if len(intervals)<=4:
                plot_text = plot_command(1, data_file, (0, 0), "", "imp", color_line_list[0], 20)
            else:
                plot_text = plot_command(1, data_file, (0, 0), "", "linespoint", color_line_list[0], 1, "pt 26", "ps 0.5")
        elif len_docid_list > 1: #Multiple curves
            if len(intervals)<=4:
                plot_text = plot_command(1, data_file, (0, 0), graphe_titles[0], "imp", color_line_list[0], 20)
            else:
                plot_text = plot_command(1, data_file, (0, 0), graphe_titles[0], "linespoint", color_line_list[0], 1, "pt 26", "ps 0.5")
            for d in range(1, len_docid_list):
                if len(intervals)<=4:
                    plot_text += plot_command(0, data_file, (d, d) , graphe_titles[d], "imp", color_line_list[d], 20)
                else :
                    plot_text += plot_command(0, data_file, (d, d) , graphe_titles[d], "linespoint", color_line_list[d], 1, "pt 26", "ps 0.5")
            if len(intervals)>2:
                plot_text += plot_command(0, data_file, (len_docid_list, len_docid_list), "", "impulses", 0, 2 )
                plot_text += plot_command(0, data_file, (len_docid_list, len_docid_list), "TOTAL", "lines", 0, 5)

    elif kind_of_graphe == 'download_users':
        g('set size 0.25,0.5')
        g('set xrange [0:4]')
        g('set yrange [0:100]')
        g('set format y "%g %%"')
        g("""set xtics ("" 0, "CERN\\n Users" 1, "Other\\n Users" 3, "" 4)""")
        g('set ytics 0,10,100')
        g('set boxwidth 0.7 relative')
        g('set style fill solid 0.25')
        plot_text = 'plot "%s" using 1:2 title "" with boxes lt 7 lw 2' % data_file

    else: #citation
        g('set boxwidth 0.6 relative')
        g('set style fill solid 0.250000 border -1')
        g('set xtics rotate')
        g('set xrange [%s:%s]' % (str(intervals[0]), str(intervals[len_intervals-1])))
        g('set yrange [0:%s]' %str(y_max+2))
        plot_text = """plot "% s" index 0:0 using 1:2 title "" w steps lt %s lw 3"""  % (data_file, color_line_list[1])

    g('%s' % plot_text)
    return (graphe_name, data_file)

def remove_old_img(prefix_file_name):
    """Detele all the images older than 10 minutes to prevent to much storage
    Takes 0.0 seconds for 50 files to delete"""

    command = "find %s/img/ -name tmp_%s*.png -amin +10 -exec rm -f {} \;" % (CFG_WEBDIR, prefix_file_name)
    return os.system(command)

def plot_command(first_line, file_source, indexes, title, style, line_type, line_width, point_type="", point_size=""):
    """Return a string of a gnuplot plot command.Particularly useful when multiple curves
    From a temporary file, draw a gnuplot graph
    Return a plot command string as follows:
    plot datafile <first curve parameters>, datafile <second curve parameters>,...
    The arguments are as follows:
    first_line   - only the drawing command of the first curve contains the word plot
    file_source  - data file source which containes coordinates
    indexes      - points out set number in data file source
    title        - title of the curve in the legend box
    style        - respresentation of the curve ex: linespoints, lines ...
    line_type    - color of the line
    line_width   - width of the line
    point_type   - optionnal parameter: if not mentionned it's a wide string.
                   Using in the case of style = linespoints to set point style"""
    if first_line:
        plot_text = """plot "%s" index %s:%s using 1:2 title "%s" with %s lt %s lw %s %s %s"""  % (file_source, indexes[0], indexes[1], title, style, line_type, line_width, point_type, point_size)
    else:
        plot_text = """, "%s" index %s:%s using 1:2 title "%s" with %s lt %s lw %s %s %s"""  % (file_source, indexes[0], indexes[1], title, style, line_type, line_width, point_type, point_size)
    return plot_text
