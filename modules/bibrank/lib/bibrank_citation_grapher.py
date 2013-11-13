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

__revision__ = "$Id$"

import os
import time

from invenio.config import CFG_SITE_URL, CFG_SITE_LANG, CFG_WEBDIR, CFG_BIBRANK_SHOW_CITATION_GRAPHS
from invenio.legacy.dbquery import run_sql
from invenio.base.i18n import gettext_set_language
from invenio.bibrank_grapher import create_temporary_image, write_coordinates_in_tmp_file, remove_old_img
from invenio.bibrank_citation_searcher import calculate_cited_by_list

cfg_bibrank_print_citation_history = 1
color_line_list = ['9', '19', '10', '15', '21', '18']
cfg_bibrank_citation_history_min_x_points = 3 # do not generate graphs that have less than three points

def get_field_values(recID, tag):
    """Return list of field values for field tag inside record RECID."""
    out = []
    if tag == "001___":
        out.append(str(recID))
    else:
        digit = tag[0:2]
        bx = "bib%sx" % digit
        bibx = "bibrec_bib%sx" % digit
        query = "SELECT bx.value FROM %s AS bx, %s AS bibx WHERE bibx.id_bibrec='%s' AND bx.id=bibx.id_bibxxx AND bx.tag LIKE '%s'" "ORDER BY bibx.field_number, bx.tag ASC" % (bx, bibx, recID, tag)
        res = run_sql(query)
        for row in res:
            out.append(row[0])
    return out

def calculate_citation_history_coordinates(recid):
    """Return a list of citation graph coordinates for RECID, sorted by year."""
    result = []
    dbg = ""
    initial_result= get_initial_result(calculate_citation_graphe_x_coordinates(recid))
    citlist = calculate_cited_by_list(recid)
    for rec_id, cit_weight in citlist:
        cit_year = get_field_values(rec_id,'773__y')
        if not cit_year:
            cit_year = get_field_values(rec_id, '260__c')
            if not cit_year:
                cit_year = get_field_values(rec_id, '269__c')
        #some records simlpy do not have these fields
        if cit_year:
            #maybe cit_year[0][0:4] has a typo and cannot
            #be converted to an int
            numeric=1
            try:
                tmpval = int(cit_year[0][0:4])
            except ValueError:
                numeric=0
            if numeric and initial_result.has_key(int(cit_year[0][0:4])):
                initial_result[int(cit_year[0][0:4])] += 1
    for key, value in initial_result.items():
        result.append((key, value))
    result.sort()
    if len(result) < cfg_bibrank_citation_history_min_x_points:
        # do not generate graphs that have less than X points
        return []
    return result

def calculate_citation_graphe_x_coordinates(recid):
    """Return a range of year from the publication year of record RECID
       until the current year."""
    rec_years = []
    recordyear = get_field_values(recid, '773__y')
    if not recordyear:
        recordyear = get_field_values(recid, '260__c')
        if not recordyear:
            recordyear = get_field_values(recid, '269__c')
    currentyear = time.localtime()[0]
    if recordyear == []:
        recordyear = currentyear
    else:
        recordyear = find_year(recordyear[0])
    interval = range(int(recordyear), currentyear+1)
    return interval

def find_year(recordyear):
    """find the year in the string as a suite of 4 int"""
    s = ""
    for i in range(len(recordyear)-3):
        s = recordyear[i:i+4]
        if s.isalnum():
            break
    return s

def get_initial_result(rec_years):
    """return an initial dictionary with year of record publication as key
       and zero as value
    """
    result = {}
    for year in rec_years :
        result[year] = 0
    return result

def html_command(file):
    t = ''
    if CFG_BIBRANK_SHOW_CITATION_GRAPHS == 1:
        t = """<img src='%s/img/%s' align="center" alt="">""" % (CFG_SITE_URL, file)
    elif CFG_BIBRANK_SHOW_CITATION_GRAPHS == 2:
        t = open(CFG_WEBDIR + "/img/" + file).read()
    #t += "</table></td></tr></table>"
    return t

def create_citation_history_graph_and_box(recid, ln=CFG_SITE_LANG):
    """Create graph with citation history for record RECID (into a
       temporary file) and return HTML box refering to that image.
       Called by Detailed record pages.
    """

    _ = gettext_set_language(ln)

    html_result = ""
    if cfg_bibrank_print_citation_history:
        coordinates = calculate_citation_history_coordinates(recid)
        if coordinates:
            html_head = """<br /><table><tr><td class="blocknote">%s</td></tr></table>"""% _("Citation history:")
            graphe_file_name = 'citation_%s_stats.png' % str(recid)
            remove_old_img(graphe_file_name)
            years = calculate_citation_graphe_x_coordinates(recid)
            years.sort()
            datas_info = write_coordinates_in_tmp_file([coordinates])
            graphe = create_temporary_image(recid, 'citation', datas_info[0], 'Year', 'Times cited', [0,0], datas_info[1], [], ' ', years)
            graphe_image = graphe[0]
            graphe_source_file = graphe[1]
            if graphe_image and graphe_source_file:
                if os.path.exists(graphe_source_file):
                    os.unlink(datas_info[0])
                    html_graphe_code = """<p>%s"""% html_command(graphe_image)
                html_result = html_head + html_graphe_code
    return html_result
