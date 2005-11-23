# -*- coding: utf-8 -*-
##
## $Id$
## 
## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002 CERN.
##
## The CDSware is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## The CDSware is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDSware; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import string  
import os
import sys
import time
import tempfile
import calendar
from config import weburl, cdslang
from messages import msg_downloads_history
from dbquery import run_sql
from bibrank_downloads_indexer import database_tuples_to_single_list
from bibrank_grapher import *

color_line_list = ['9', '19', '10', '15', '21', '18']
cfg_id_bibdoc_id_bibrec = 5
cfg_bibrank_print_download_history = 1
cfg_bibrank_print_download_split_by_id = 1

def create_download_history_graph_and_box(id_bibrec, ln=cdslang):
    """Create graph with citation history for record ID_BIBREC (into a
       temporary file) and return HTML box refering to that image.
       Called by Detailed record pages.
       Notes:
        if id_bibdoc=0 : its an oustide-stored document and it has no id_bibdoc --> only one line
        if nb_id_bibdoc <= cfg_id_bibdoc_id_bibrec draw one line per id_bibdoc
        if nb_id_bibdoc > cfg_id_bibdoc_id_bibrec draw only one line which hold simultaneously the downloads per id_bibdoc
        Each time this function is called, all the images older than 10 minutes are deleted.
    """
    html_code = ""
    html_content = ""
    users_analysis_text = ""
    if cfg_bibrank_print_download_split_by_id:
        users_analysis_text = "and Users repartition"
        #remove images older than 10 minutes
        remove_old_img("download")
        #Users analysis graph
        ips = database_tuples_to_single_list(run_sql("select client_host from rnkDOWNLOADS where id_bibrec=%s;" % id_bibrec))
        if ips == []:
            pass
        else :
            users_analysis_results = create_users_analysis_graph(id_bibrec, ips)
            graph_file_users = weburl + "/img/"  + users_analysis_results[0]
            file_to_close_users = users_analysis_results[1]      
            html_content += """<tr><td valign=center align=center><img src='%s'/></td>""" % graph_file_users
            if file_to_close_users:
                if os.path.exists(file_to_close_users):
                    os.unlink(file_to_close_users)
    
    #Downloads history graph and return html code used by get_file or search_engine
    if cfg_bibrank_print_download_history:
        remove_old_img("download")
        nb_id_bibdoc = run_sql("select distinct id_bibdoc from rnkDOWNLOADS where id_bibrec=%s;" % id_bibrec)
        history_analysis_results = ()
        if nb_id_bibdoc == ():
            pass
        elif nb_id_bibdoc[0][0] <= cfg_id_bibdoc_id_bibrec and (0, ) not in nb_id_bibdoc:
            history_analysis_results = draw_downloads_statistics(id_bibrec, list(nb_id_bibdoc))
        else:
            history_analysis_results = draw_downloads_statistics(id_bibrec, [])
        if history_analysis_results:
            graph_file_history = weburl + "/img/" + history_analysis_results[0]
            file_to_close_history = history_analysis_results[1]
            html_content += """<tr><td valign=center align=center><img src='%s'/></td>""" % graph_file_history
            if file_to_close_history :
                if os.path.exists(file_to_close_history):
                    os.unlink(file_to_close_history)
                    
    out = ""
    if html_content != "":
        out += """<br/><br/><table><tr><td class="blocknote">
                  %s %s</td></tr><tr><td>
                  <table border="0" cellspacing="1" cellpadding="1">""" %  (msg_downloads_history[ln], users_analysis_text)
        out += html_content
        out += "</table></td></tr></table>"
    return out
    
def draw_downloads_statistics(id_bibrec, id_bibdoc_list):
    """Create a graph about download history using a temporary file to store datas 
    and a new png file for each id_bibrec to store the image of the graph which will
    be referenced by html code."""    

    intervals = []
    #used to name the different curves when len(id_bibdoc_list)>1
    docfile_name_list = []
    #used to name the uniquecurve when len(id_bibdoc_list)=0 or > cfg_id_bibdoc_id_bibrec 
    record_name = run_sql("select value from bibrec_bib24x,bib24x where id_bibrec=%s and id_bibxxx=id;" % id_bibrec)[0][0]
    #list of lists of tuples: [[("09/2004",4),..],[(..,..)]..]
    #Each list element of the list is represented by a curve
    #each elem of each list is a point on the graph
    coordinates_list = []
    
    #If the document is not stored in CdsWare it has id_bibrec 0 and no creation date
    #In this case the beginning date is the first time the document has been downloaded
    creation_date_res = run_sql("""SELECT DATE_FORMAT(creation_date,"%%Y-%%m-%%d-%%H:%%i:%%s") FROM bibrec WHERE id=%s;""" % id_bibrec)
    if creation_date_res == ():
        creation_date_res = run_sql("""SELECT DATE_FORMAT(MIN(download_time),"%%Y-%%m-%%d-%%H:%%i:%%s") FROM rnkDOWNLOADS where id_bibrec=%s;""" % id_bibrec)
    creation_date_year, creation_date_month, creation_date_day, creation_date_time = string.split(creation_date_res[0][0], "-")
    creation_date_year = string.atoi(creation_date_year)
    creation_date_month = string.atoi(creation_date_month)
    creation_date_day = string.atoi(creation_date_day)
    creation_date_time = str(creation_date_time)
        
    #create intervals and corresponding values
    local_time = time.localtime()
    res = create_tic_intervals(local_time, creation_date_year, creation_date_month)
    intervals = res[1]
    tic_list = res[0]

    if id_bibdoc_list == []:
        coordinates_list.append(create_list_tuple_data(intervals, id_bibrec))
        docfile_name_list = record_name
    else :
        for i in range(len(id_bibdoc_list)):
            datas = create_list_tuple_data(intervals, id_bibrec, id_bibdoc_query_addition="and id_bibdoc=%s" % id_bibdoc_list[i][0])
            coordinates_list.append(datas)
            docfile_name_list.append(run_sql("select docname from bibdoc where id=%s;" % id_bibdoc_list[i][0])[0][0])
        #In case of multiple id_bibdocs datas_max will be used to draw a line which is the total of the others lines 
        if not (len(intervals)==1 or len(id_bibdoc_list)==1):
            datas_max = create_list_tuple_total(intervals, coordinates_list)
            coordinates_list.append(datas_max)
    #write coordinates_list in a temporary file   
    result2 = write_coordinates_in_tmp_file(coordinates_list)
    
    fname = result2[0]
    y_max = result2[1]
    #Use create the graph from the temporary file
    return create_temporary_image(id_bibrec, 'download_history', fname, '', 'Downloads/month', (0, 0), y_max, id_bibdoc_list, docfile_name_list, tic_list)
    
def create_list_tuple_data(intervals, id_bibrec, id_bibdoc_query_addition=""):
    """-Return a list of tuple of the form [('10/2004',3),(..)] used to plot graph
        Where 3 is the number of downloads between 01/10/2004 and 31/10/2004"""    
    list_tuple = []
    for elem in intervals:
        main_date_end = string.split(elem[1], '/')
        end_of_month_end = calendar.monthrange(string.atoi(main_date_end[1]), string.atoi(main_date_end[0]))[1]
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

def create_tic_intervals(local_time, creation_date_year, creation_date_month):
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
    local_month = local_time.tm_mon
    local_year = local_time.tm_year
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
    else  :
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
    for i in range(len(ips)):
        if 2307522817 <= ips[i] <= 2307588095 or 2156724481 <= ips[i] <= 2156789759:
            cern_users += 1
        else :
            other_users += 1
    tot = float(cern_users+other_users)
    #prepare coordinates list
    coordinates_list.append((1, str(float(cern_users)/tot*100)))
    coordinates_list.append((3, str(float(other_users)/tot*100)))
    #write coordinates in a temporary file 
    result2 = write_coordinates_in_tmp_file([coordinates_list])
    #plot the graph
    return create_temporary_image(id_bibrec, 'download_users', result2[0], '', '', (0, 0), result2[1], [], [], [1, 3])


