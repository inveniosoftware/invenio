# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2014 CERN.
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

__revision__ = "$Id$"

import string
import os
import time
import calendar

from invenio.config import CFG_SITE_URL, CFG_SITE_LANG, CFG_BIBRANK_SHOW_DOWNLOAD_GRAPHS, CFG_BIBRANK_SHOW_DOWNLOAD_GRAPHS_CLIENT_IP_DISTRIBUTION, CFG_WEBDIR
from invenio.base.i18n import gettext_set_language
from intbitset import intbitset
from invenio.legacy.dbquery import run_sql
from invenio.legacy.bibrank.downloads_indexer import database_tuples_to_single_list
from invenio.legacy.bibrank.grapher import (write_coordinates_in_tmp_file,
                                            create_temporary_image,
                                            remove_old_img)

CFG_ID_BIBDOC_ID_BIBREC = 5

def create_download_history_graph_and_box(id_bibrec, ln=CFG_SITE_LANG):
    """Create graph with citation history for record ID_BIBREC (into a
       temporary file) and return HTML box refering to that image.
       Called by Detailed record pages.
       Notes:
        if id_bibdoc=0 : its an oustide-stored document and it has no id_bibdoc --> only one line
        if len(id_bibdocs) <= cfg_id_bibdoc_id_bibrec draw one line per id_bibdoc
        if len(id_bibdocs) > cfg_id_bibdoc_id_bibrec draw only one line which hold simultaneously the downloads for all id_bibdoc
        Each time this function is called, all the images older than 10 minutes are deleted.
    """
    _ = gettext_set_language(ln)

    out = ""

    # Prepare downloads history graph:
    if CFG_BIBRANK_SHOW_DOWNLOAD_GRAPHS:
        html_content = ""
        # remove images older than 10 minutes
        remove_old_img("download")
        # download count graph
        id_bibdocs = intbitset(run_sql("select distinct id_bibdoc from rnkDOWNLOADS where id_bibrec=%s", (id_bibrec, )))

        id_existing_bibdocs = intbitset(run_sql("SELECT id_bibdoc FROM bibrec_bibdoc JOIN bibdoc ON id_bibdoc=id WHERE id_bibrec=%s AND status<>'DELETED'", (id_bibrec, )))

        ## FIXME: when bibdocs are deleted we loose the stats. What shall we do with them?
        id_bibdocs &= id_existing_bibdocs

        history_analysis_results = ()
        if not id_bibdocs:
            pass
        elif len(id_bibdocs) <= CFG_ID_BIBDOC_ID_BIBREC and 0 not in id_bibdocs:
            history_analysis_results = draw_downloads_statistics(id_bibrec, list(id_bibdocs))
        else:
            history_analysis_results = draw_downloads_statistics(id_bibrec, [])
        if history_analysis_results and history_analysis_results[0]:
            graph_path = history_analysis_results[0][history_analysis_results[0].rfind('/')+1:]
            if CFG_BIBRANK_SHOW_DOWNLOAD_GRAPHS == 2:
                graph_file_history = CFG_WEBDIR + "/img/" + graph_path
                html_content += """<tr><td valign=center align=center>%s</td>""" % open(graph_file_history).read()
            else:  # gnuplot
                graph_file_history = CFG_SITE_URL + "/img/" + graph_path
                html_content += """<tr><td valign=center align=center><img src='%s'/></td>""" % graph_file_history
            file_to_close_history = history_analysis_results[1]
            if file_to_close_history :
                if os.path.exists(file_to_close_history):
                    os.unlink(file_to_close_history)
        if html_content != "":
            out += """<table border="0" cellspacing="1" cellpadding="1">"""
            out += html_content + "</table>"

    if CFG_BIBRANK_SHOW_DOWNLOAD_GRAPHS_CLIENT_IP_DISTRIBUTION:
        # do we show also user IP repartition?
        html_content = ""
        remove_old_img("download")
        #Users analysis graph
        ips = database_tuples_to_single_list(run_sql("select client_host from rnkDOWNLOADS where id_bibrec=%s;" % id_bibrec))
        if ips:
            users_analysis_results = create_users_analysis_graph(id_bibrec, ips)
            if users_analysis_results[0]:
                file_to_close_users = users_analysis_results[1]
                if CFG_BIBRANK_SHOW_DOWNLOAD_GRAPHS_CLIENT_IP_DISTRIBUTION == 1:
                    html_content += """<tr><td valign=center align=center><img src='%s/img/%s' align="center" alt=""></td>""" % (CFG_SITE_URL, users_analysis_results[0])
                elif CFG_BIBRANK_SHOW_DOWNLOAD_GRAPHS_CLIENT_IP_DISTRIBUTION == 2:
                    html_content += """<tr><td valign=center align=center>%s</td>""" % open(CFG_WEBDIR + "/img/"  + users_analysis_results[0]).read()
                if file_to_close_users:
                    if os.path.exists(file_to_close_users):
                        os.unlink(file_to_close_users)
        if html_content != "":
            out += """<br/><br/><table><tr><td class="blocknote">
                      %s</td></tr><tr><td>
                      <table border="0" cellspacing="1" cellpadding="1">""" % _("Download user distribution:")
            out += html_content
            out += "</table></td></tr></table>"

    # return html code used by get_file or search_engine
    return out

def draw_downloads_statistics(id_bibrec, id_bibdoc_list):
    """Create a graph of download history using a temporary file to store datas
    and a new png file for each id_bibrec to store the image of the graph which will
    be referenced by html code."""

    intervals = []
    #used to name the different curves when len(id_bibdoc_list)>1
    docfile_name_list = []
    #used to name the uniquecurve when len(id_bibdoc_list)=0 or > cfg_id_bibdoc_id_bibrec
    record_name = ""
    record_name_query = run_sql("select value from bibrec_bib24x,bib24x where id_bibrec=%s and id_bibxxx=id;" % id_bibrec)
    if record_name_query:
        record_name = record_name_query[0][0]
    #list of lists of tuples: [[("09/2004",4),..],[(..,..)]..]
    #Each list element of the list is represented by a curve
    #each elem of each list is a point on the graph
    coordinates_list = []


    #If the document is not stored in internally it has id_bibrec 0 and no creation date
    #In this case the beginning date is the first time the document has been downloaded
    local_time = time.localtime()
    local_month = local_time.tm_mon
    local_year = local_time.tm_year

    creation_date_res = run_sql("""SELECT DATE_FORMAT(creation_date,"%%Y-%%m") FROM bibrec WHERE id=%s;""" % id_bibrec)
    if creation_date_res == ():
        creation_date_res = run_sql("""SELECT DATE_FORMAT(MIN(download_time),"%%Y-%%m") FROM rnkDOWNLOADS where id_bibrec=%s;""" % id_bibrec)
    if creation_date_res == (('0000-00',),):
        creation_date_year = local_year - 1
        creation_date_month = local_month
    else :
        creation_date_year, creation_date_month = string.split(creation_date_res[0][0], "-")
        creation_date_year = int(creation_date_year)
        creation_date_month = int(creation_date_month)


    #create intervals and corresponding values
    res = create_tic_intervals(local_year, local_month, creation_date_year, creation_date_month)
    intervals = res[1]
    tic_list = res[0]

    if id_bibdoc_list == []:
        coordinates_list.append(create_list_tuple_data(intervals, id_bibrec))
        docfile_name_list = record_name
    else :
        for i in range(len(id_bibdoc_list)):
            datas = create_list_tuple_data(intervals, id_bibrec, id_bibdoc_query_addition="and id_bibdoc=%s" % id_bibdoc_list[i])
            coordinates_list.append(datas)
            docname = run_sql("select docname from bibrec_bibdoc where id_bibdoc=%s and id_bibrec=%s;" % (id_bibdoc_list[i], id_bibrec))
            docfile_name_list.append(docname[0][0])
        #In case of multiple id_bibdocs datas_max will be used to draw a line which is the total of the others lines
        if not (len(intervals)==1 or len(id_bibdoc_list)==1):
            datas_max = create_list_tuple_total(intervals, coordinates_list)
            coordinates_list.append(datas_max)
    #write coordinates_list in a temporary file
    graph_source_file, y_max = write_coordinates_in_tmp_file(coordinates_list)
    #Use create the graph from the temporary file
    graph_file = create_temporary_image(id_bibrec, 'download_history',
                                        graph_source_file, ' ',
                                        'Times downloaded', [0, 0], y_max,
                                        id_bibdoc_list, docfile_name_list,
                                        tic_list)
    return graph_file, graph_source_file

def create_list_tuple_data(intervals, id_bibrec, id_bibdoc_query_addition=""):
    """-Return a list of tuple of the form [('10/2004',3),(..)] used to plot graph
        Where 3 is the number of downloads between 01/10/2004 and 31/10/2004"""
    list_tuple = []
    for elem in intervals:
        main_date_end = string.split(elem[1], '/')
        end_of_month_end = calendar.monthrange(int(main_date_end[1]), int(main_date_end[0]))[1]
        s0 = string.split(elem[0], "/")
        s1 = string.split(elem[1], "/")
        elem0 = s0[1] + "-" + s0[0]
        elem1 = s1[1] + "-" + s1[0]
        date1 = "%s%s" % (elem0, "-01 00:00:00")
        date2 = "%s%s" % (elem1, "-%s 00:00:00" % str(end_of_month_end))
        sql_query = "select count(*) from rnkDOWNLOADS where id_bibrec=%s %s and download_time>='%s' and download_time<'%s';" % (id_bibrec, id_bibdoc_query_addition, date1, date2)
        res = run_sql(sql_query)[0][0]
        list_tuple.append((elem[0], res))
    #list_tuple = sort_list_tuple_by_date(list_tuple)
    return (list_tuple)

def sort_list_tuple_by_date(list_tuple):
    """Sort a list of tuple of the forme ("09/2004", 3)according to the
    year of the first element of the tuple"""
    list_tuple.sort(lambda x, y: (cmp(string.split(x[0], '/')[1],
                                      string.split(y[0], '/')[1])))
    return list_tuple

def create_list_tuple_total(intervals, list_data):
    """In the case of multiple id_bibdocs,  a last paragraph is added
    at the end to show the global evolution of the record"""
    list_tuple = []
    if len(intervals)==1:
        res = 0
        for j in range(len(list_data)):
            res += list_data[j][1]
        list_tuple.append((intervals[0][0], res))
    else :

        for i in range(len(intervals)):
            res = 0
            for j in range(len(list_data)):
                res += list_data[j][i][1]
            list_tuple.append((intervals[i][0], res))
        #list_tuple = sort_list_tuple_by_date(list_tuple)
    return list_tuple

def create_tic_intervals(local_year, local_month, creation_date_year, creation_date_month):
    """Create intervals since document creation date until now
       Return a list of the tics for the graph of the form ["04/2004","05/2004"), ...]
       And a list of tuple(each tuple stands for a period) of the form [("04/2004", "04/2004"),.]
       to compute the number of downloads in each period
       For the very short periods some tics and tuples are added to  make sure that
       at least two dates are returned. Useful for drawing graphs.
    """

    # okay, off we go
    tic_list = []
    interval_list = []
    original_date = (creation_date_month, creation_date_year)

    while (creation_date_year, creation_date_month) <= (local_year, local_month) and creation_date_month <= 12:
        date_elem = "%s/%s" % (creation_date_month, creation_date_year)
        tic_list.append(date_elem)
        interval_list.append((date_elem, date_elem))
        if creation_date_month != 12:
            creation_date_month = creation_date_month+1
        else :
            creation_date_year = creation_date_year+1
            creation_date_month = 1

        next_period = (creation_date_month, creation_date_year)

        #additional periods for the short period

    if len(interval_list) <= 2:
        period_before = "%s/%s" % (sub_month(original_date[0], original_date[1]))
        period_after = "%s/%s" % next_period
        interval_list.insert(0, (period_before, period_before))
        interval_list.append((period_after, period_after))
        tic_list.insert(0, period_before)
        tic_list.append(period_after)
    return (tic_list, interval_list)

def add_month(month, year):
    """Add a month and increment the year if necessary"""
    if month == 12:
        month = 1
        year += 1
    else:
        month += 1
    return (month, year)

def sub_month(month, year):
    """Add a month and decrease the year if necessary"""
    if month == 1:
        month = 12
        year = year -1
    else :
        month -= 1
    return (month, year)

def create_users_analysis_graph(id_bibrec, ips):
    """For a given id_bibrec, classify cern users and other users
    Draw a percentage graphic reprentation"""
    cern_users = 0
    other_users = 0
    coordinates_list = []
    #compute users repartition
    for ip in ips:
        if 2307522817 <= ip <= 2307588095 or 2156724481 <= ip <= 2156789759:
            cern_users += 1
        else:
            other_users += 1
    tot = float(cern_users+other_users)
    #prepare coordinates list
    coordinates_list.append((1, str(float(cern_users)/tot*100)))
    coordinates_list.append((3, str(float(other_users)/tot*100)))
    #write coordinates in a temporary file
    graph_source_file, y_max = write_coordinates_in_tmp_file([coordinates_list])
    #result2 example: [/path/to-invenio/var/www/img/tmpeC9GP5,'100.0']
    #the file contains e.g.
    #1 100.0
    #3 0.0
    #plot the graph
    graph_file = create_temporary_image(id_bibrec, 'download_users',
                                        graph_source_file, ' ',
                                        'User distribution', (0, 0), y_max,
                                        [], [], [1, 3])
    return graph_file, graph_source_file
