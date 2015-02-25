# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2005, 2006, 2007, 2008, 2010, 2011 CERN.
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

import os
import time
import calendar
import string

from six import iteritems

from invenio.legacy.dbquery import run_sql

def append_to_file(path, content):
    """print result in a file"""

    if os.path.exists(path):
        file_dest = open(path,"a")
        file_dest.write("Hit on %s reads:" % time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        file_dest.write(content)
        file_dest.write("\n")
        file_dest.close()
        return content

def get_download_weight_filtering_user(dic, keys):
    """ update the dictionnary.Without duplicates.Count maximum one hit per user per hour"""
    for k in keys:
        weight = 0
        user_ips = run_sql("select count(distinct client_host) from rnkDOWNLOADS where id_bibrec=%s group by id_bibdoc" % k)
        for ip in user_ips:
            weight = weight + ip[0]
            dic[k] = weight
    return dic

def get_download_weight_total(dic, keys):
    """ update the dictionnary.Count all the hit"""
    for k in keys:
        values = run_sql("select count(*) from rnkDOWNLOADS where id_bibrec=%s %s" % (k,";"))
        dic[k] = values[0][0]
    return dic

def uniq(alist):
    """Remove duplicate element in alist
    Fastest without order preserving"""
    set = {}
    map(set.__setitem__, alist, [])
    return set.keys()

def database_tuples_to_single_list(tuples):
    """convert a tuple extracted from the database into a list"""
    return [elem[0] for elem in tuples]


def new_downloads_to_index (last_updated):
    """id_bibrec of documents downloaded since the last run of bibrank """
    id_bibrec_list = database_tuples_to_single_list(run_sql("select id_bibrec from rnkDOWNLOADS where download_time >=\"%s\"" % last_updated))
    res = uniq(id_bibrec_list)
    return res

def filter_downloads_per_hour_with_docid (keys, last_updated):
    """filter all the duplicate downloads per user for each hour intervall"""
    for k in keys:
        id_bibdocs = run_sql("select distinct id_bibdoc from rnkDOWNLOADS where id_bibrec=%s" % k)
        for bibdoc in id_bibdocs:
            values = run_sql("""select  DATE_FORMAT(download_time,"%%Y-%%m-%%d %%H"), client_host from rnkDOWNLOADS where id_bibrec=%s and id_bibdoc=%s and download_time >=\"%s\";""" % (k, bibdoc[0], last_updated))

            for val in values:
                date_res = val[0]
                date1 = "%s:00:00" % (date_res)
                date2 = compute_next_hour(date_res)
                duplicates = (run_sql("select count(*) from rnkDOWNLOADS where id_bibrec=%s and id_bibdoc=%s and download_time>='%s' and download_time<'%s' and client_host=%s;" % (k, bibdoc[0], date1, date2, val[1]))[0][0])-1
                run_sql("delete from rnkDOWNLOADS where id_bibrec=%s and id_bibdoc=%s and download_time>='%s' and download_time<'%s' and client_host=%s limit %s;" % (k, bibdoc[0], date1, date2, val[1], duplicates))

def filter_downloads_per_hour (keys, last_updated):
    """filter all the duplicate downloads per user for each hour intervall"""
    for k in keys:
        values = run_sql("""select DATE_FORMAT(download_time,"%%Y-%%m-%%d %%H"), client_host from rnkDOWNLOADS where id_bibrec=%s and download_time >=\"%s\";""" % (k, last_updated))
        for val in values:
            date_res = val[0]
            date1 = "%s:00:00" % (date_res)
            date2 = compute_next_hour(date_res)
            duplicates = (run_sql("select count(*) from rnkDOWNLOADS where id_bibrec=%s and download_time>='%s' and download_time<'%s' and client_host=%s;" % (k, date1, date2, val[1]))[0][0])-1
            run_sql("delete from rnkDOWNLOADS where id_bibrec=%s and download_time>='%s' and download_time<'%s' and client_host=%s limit %s;" % (k, date1, date2, val[1], duplicates))

def compute_next_hour(date_res):
    """treat the change of the year, of (special)month etc.. and return the date in database format"""
    next_date = ""
    date_res, date_hour = string.split(date_res, " ")
    date_hour = string.atoi(date_hour)

    if date_hour == 23:
        date_year, date_month, date_day = string.split(date_res, "-")
        date_year = string.atoi(date_year)
        date_month = string.atoi(date_month)
        date_day = string.atoi(date_day)
        if date_month == 12 and date_day == 31:
            next_date = "%s-%s-%s 00:00:00" % (date_year + 1, 01, 01)
        elif calendar.monthrange(date_year, date_month)[1] == date_day:
            next_date = "%s-%s-%s 00:00:00" % (date_year, date_month + 1, 01)
        else :
            next_date = "%s-%s-%s 00:00:00" % (date_year, date_month, date_day + 1)

    else :
        next_hour = date_hour + 1
        next_date = "%s %s:00:00" % (date_res, next_hour)
    return next_date


def get_file_similarity_by_times_downloaded(dic, id_bibrec_list):
    """For each id_bibrec, get the client_host and see which other id_bibrec these users have also downloaded.
    Return update dictionnary of this form
    {id_bibrec:[(id_bibrec1,score),(id_bibrec2,score)],id_bibrec:[(),()]...}
    Take long time so let's see bibrank_downloads_similarity which compute in fly the similarity for
    a particular recid."""
    dic_result = {}
    if id_bibrec_list != []:
        tuple_string_id_bibrec_list = str(tuple(id_bibrec_list))
        if len(id_bibrec_list) == 1:
            tuple_string_id_bibrec_list = tuple_string_id_bibrec_list.replace(',','')
        #first compute the download similarity between the new documents
        #which have been downloadwd since the last run of bibrank
        dic_news = {}
        res = run_sql("select id_bibrec,client_host from rnkDOWNLOADS where id_bibrec in %s;" % tuple_string_id_bibrec_list)
        for res_elem in res:
            id_bibrec_key = res_elem[0]
            client_host_value = str(res_elem[1])
            if id_bibrec_key in dic_news.keys():
                tmp_list = dic_news[id_bibrec_key]
                if client_host_value not in dic_news[id_bibrec_key]:
                    tmp_list.append(client_host_value)
                    dic_news[id_bibrec_key] = tmp_list
            else :
                list_client_host_value = []
                list_client_host_value.append(client_host_value)
                dic_news[id_bibrec_key] = list_client_host_value
        #compute occurence of client_host
        for j in dic_news.keys():
            list_tuple = []
            tuple_client_host = str(tuple(dic_news[j]))
            if len(tuple(dic_news[j])) == 1:
                tuple_client_host = tuple_client_host.replace(',','')
            res2 = run_sql("select id_bibrec,count(*) from rnkDOWNLOADS where client_host in %s and id_bibrec in %s and id_bibrec != %s group by id_bibrec;" %  (tuple_client_host, tuple_string_id_bibrec_list, j)) #0.0023 par requete
            list_tuple.append(list(res2))
            dic_result[j] = list_tuple[0]
    #merge new values with old dictionnary
    return merge_with_old_dictionnary(dic, dic_result)

def merge_with_old_dictionnary(old_dic, new_dic):
    """For each key id_bibrec in new_dic add the old values contained in old_dic
    Return not ordered merged dictionnary"""
    union_dic = {}
    for (key, value) in iteritems(new_dic):
        if key in old_dic.keys():
            old_dic_value_dic = dict(old_dic[key])
            tuple_list = []
            old_dic_value_dic_keys = old_dic_value_dic.keys()
            for val in value:
                if val[0] in old_dic_value_dic_keys:
                    tuple_list.append((val[0], val[1]+ old_dic_value_dic[val[0]]))
                    del old_dic_value_dic[val[0]]
                else :
                    tuple_list.append((val[0], val[1]))
            old_dic_value_dic_items = old_dic_value_dic.items()
            if old_dic_value_dic_items != []:
                tuple_list.extend(old_dic_value_dic_items)
            union_dic[key] = tuple_list
        else :
            union_dic[key] = value

    for (key, value) in iteritems(old_dic):
        if key not in union_dic.keys():
            union_dic[key] = value
    return union_dic
