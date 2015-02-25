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

import os
import time


from invenio.config import (CFG_SITE_URL,
                            CFG_SITE_LANG,
                            CFG_WEBDIR,
                            CFG_BIBRANK_SHOW_CITATION_GRAPHS)
from invenio.base.i18n import gettext_set_language
from invenio.legacy.bibrank.grapher import (create_temporary_image,
                                     write_coordinates_in_tmp_file)
from invenio.legacy.bibrank.citation_searcher import get_cited_by
from invenio.legacy.search_engine.utils import get_fieldvalues
from invenio.utils.date import strptime


CFG_BIBRANK_PRINT_CITATION_HISTORY = 1
# Do not generate graphs that have less than three points
CFG_BIBRANK_CITATION_HISTORY_MIN_X_POINTS = 2

REL_PATH = 'img/citation-graphs'
BASE_DIR = os.path.join(CFG_WEBDIR, os.path.join(*REL_PATH.split('/')))

DATE_TAGS = ('269__c', '773__y', '260__c', '111__x', '502__d')


def get_record_year(recid):
    record_date = []
    for tag in DATE_TAGS:
        record_date = get_fieldvalues(recid, tag)
        if record_date:
            break
    return record_date


def calculate_citation_graphe_x_coordinates(recid):
    """Return a range of year from the publication year of record RECID
       until the current year."""
    record_date = get_record_year(recid)
    currentyear = time.localtime()[0]

    recordyear = None
    if record_date:
        recordyear = find_year(record_date[0])
    if not recordyear:
        recordyear = currentyear

    return range(recordyear, currentyear+1)


def calculate_citation_history_coordinates(recid):
    """Return a list of citation graph coordinates for RECID, sorted by year."""
    result = {}
    for year in calculate_citation_graphe_x_coordinates(recid):
        result[year] = 0

    if len(result) < CFG_BIBRANK_CITATION_HISTORY_MIN_X_POINTS:
        # do not generate graphs that have less than X points
        return []

    for recid in get_cited_by(recid):
        rec_date = get_record_year(recid)
        # Some records simlpy do not have these fields
        if rec_date:
            # Maybe rec_date[0][0:4] has a typo and cannot
            # be converted to an int
            try:
                d = strptime(rec_date[0][:4], '%Y')
            except ValueError:
                pass
            else:
                if d.year in result:
                    result[d.year] += 1

    return sorted(result.iteritems())


def find_year(recordyear):
    """find the year in the string as a suite of 4 int"""
    year = None
    for i in range(len(recordyear)-3):
        s = recordyear[i:i+4]
        if s.isalnum():
            year = int(s)
            break
    return year


def html_command(filename):
    """return html code for showing citation graph image
    """
    t = ''
    if CFG_BIBRANK_SHOW_CITATION_GRAPHS == 1:
        t = '<img src="%s/%s/%s" align="center" alt="Citation Graph">' \
                                           % (CFG_SITE_URL, REL_PATH, filename)
    elif CFG_BIBRANK_SHOW_CITATION_GRAPHS == 2:
        t = open(os.path.join(BASE_DIR, filename)).read()
    return t


def remove_old_graph_if_needed(filename):
    """Delete graph if it is older than x seconds"""
    if not os.path.isfile(filename):
        return True

    try:
        mtime = os.stat(filename).st_mtime
    except OSError, e:
        # File does not exist is ok
        if e.errno != 2:
            raise
        return True

    time_diff = time.time() - mtime
    if time_diff > 3600*24:
        try:
            os.unlink(filename)
        except OSError, e:
            # File does not exist is ok
            if e.errno != 2:
                raise
        return True

    return False


def safe_create_citation_graph(recid, dest):
    # Create destination dir
    dest_dir = os.path.dirname(dest)
    try:
        os.makedirs(dest_dir)
    except OSError, e:
        # If directory already exists, ignore error
        if e.errno != 17:
            raise

    graph_source_file = create_citation_graph(recid, dest_dir)

    if graph_source_file:
        try:
            os.rename(graph_source_file, dest)
        except OSError:
            os.unlink(graph_source_file)


def create_citation_graph(recid, dest_dir):
    coordinates = calculate_citation_history_coordinates(recid)
    if coordinates:
        years = calculate_citation_graphe_x_coordinates(recid)

        coordinates_file, max_y = write_coordinates_in_tmp_file([coordinates])
        try:
            graph_file = create_temporary_image(recid,
                    'citation', coordinates_file, 'Year', 'Times cited',
                    [0, 0], max_y, [], ' ', years, dest_dir=dest_dir)
        finally:
            # Always delete the coordinates file
            if coordinates_file:
                os.unlink(coordinates_file)

        if graph_file and os.path.exists(graph_file):
            return graph_file


def create_citation_history_graph_and_box(recid, ln=CFG_SITE_LANG):
    """Create graph with citation history for record RECID (into a
       temporary file) and return HTML box refering to that image.
       Called by Detailed record pages.
    """

    _ = gettext_set_language(ln)

    html_result = ""

    if CFG_BIBRANK_PRINT_CITATION_HISTORY:
        graph_file_name = 'citation_%s_stats.png' % recid
        # We need to store graphs in subdirectories because
        # of max files per directory limit on AFS
        sub_dir = str(recid / 10000)
        graph_file = os.path.join(BASE_DIR, sub_dir, graph_file_name)

        if remove_old_graph_if_needed(graph_file):
            safe_create_citation_graph(recid, graph_file)

        if os.path.exists(graph_file):
            html_head = '<br /><table><tr><td class="blocknote">%s</td></tr></table>' % _("Citation history:")
            html_graph_code = """<p>%s</p>""" % html_command('%s/%s' % (sub_dir, graph_file_name))
            html_result = html_head + html_graph_code

    return html_result
