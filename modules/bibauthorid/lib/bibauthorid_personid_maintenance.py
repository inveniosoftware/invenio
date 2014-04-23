# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012 CERN.
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

"""
aidPersonID maintenance algorithms.
"""
from invenio.bibauthorid_name_utils import split_name_parts
from invenio.bibauthorid_name_utils import create_normalized_name
from invenio.bibauthorid_backinterface import get_name_by_bibref
from invenio.bibauthorid_backinterface import back_up_author_paper_associations  # emitting #pylint: disable-msg=W0611
from invenio.bibauthorid_backinterface import compare_personid_tables  # emitting #pylint: disable-msg=W0611
from invenio.bibauthorid_backinterface import group_personid
from invenio.bibauthorid_backinterface import check_author_paper_associations  # emitting #pylint: disable-msg=W0611
from invenio.bibauthorid_backinterface import repair_author_paper_associations  # emitting #pylint: disable-msg=W0611
from invenio.bibauthorid_backinterface import duplicated_tortoise_results_exist  # emitting #pylint: disable-msg=W0611
from invenio.bibauthorid_backinterface import merger_errors_exist  # emitting #pylint: disable-msg=W0611
from invenio.bibauthorid_backinterface import restore_author_paper_associations  # emitting #pylint: disable-msg=W0611
from invenio.bibauthorid_backinterface import get_all_author_paper_associations  # emitting #pylint: disable-msg=W0611
from invenio.bibauthorid_backinterface import get_clusters  # emitting #pylint: disable-msg=W0611
from invenio.bibauthorid_backinterface import get_papers_affected_since as get_recids_affected_since  # emitting #pylint: disable-msg=W0611


def convert_personid():
    from invenio.dbquery import run_sql  # oh come on, the whole function will be removed soon
    from itertools import repeat
    chunk = 1000

    old_personid = run_sql("SELECT `personid`, `tag`, `data`, `flag`, `lcul` FROM `aidPERSONID`")

    def flush_papers(args):
        run_sql("INSERT INTO `aidPERSONIDPAPERS` "
                "(`personid`, "
                " `bibref_table`, "
                " `bibref_value`, "
                " `bibrec`, "
                " `name`, "
                " `flag`, "
                " `lcul`) "
                "VALUES " + " , ".join(repeat("(%s, %s, %s, %s, %s, %s, %s)", len(args) / 7)), tuple(args))

    def flush_data(args):
        run_sql("INSERT INTO `aidPERSONIDDATA` "
                "(`personid`, "
                " `tag`, "
                " `data`, "
                " `opt1`, "
                " `opt2`) "
                "VALUES " + " , ".join(repeat("(%s, %s, %s, %s, %s)", len(args) / 5)), tuple(args))

    paper_args = []
    data_args = []
    for row in old_personid:
        if row[1] == 'paper':
            bibref, rec = row[2].split(',')
            tab, ref = bibref.split(':')
            try:
                name = get_name_by_bibref((int(tab), int(ref), int(rec)))
            except:
                continue
            name = split_name_parts(name)
            name = create_normalized_name(name)
            paper_args += [row[0], tab, ref, rec, name, row[3], row[4]]
            if len(paper_args) > chunk:
                flush_papers(paper_args)
                paper_args = []

        elif row[1] == 'gathered_name':
            continue
        else:
            data_args += list(row)
            if len(data_args) > chunk:
                flush_data(data_args)
                data_args = []

    if paper_args:
        flush_papers(paper_args)

    if data_args:
        flush_data(data_args)


def compare_personids(path):
    '''
    Use this function with back_up_author_paper_associations() to diff personids.
    '''
    fp = open(path, "w")
    pid1_p, pid1_d = group_personid("aidPERSONIDPAPERS_copy", "aidPERSONIDDATA_copy")
    pid2_p, pid2_d = group_personid("aidPERSONIDPAPERS", "aidPERSONIDDATA")
    compare_personid_tables(pid1_p, pid1_d, pid2_p, pid2_d, fp)
