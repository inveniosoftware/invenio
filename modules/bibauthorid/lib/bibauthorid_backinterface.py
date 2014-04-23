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
'''
    bibauthorid_frontinterface
    This file aims to filter and modify the interface given by
    bibauthorid_bdinterface in order to make it usable by the
    backend so to keep it as clean as possible.
'''

from itertools import groupby
from operator import itemgetter

# Well this is bad, BUT otherwise there must 100+ lines
# of the form from dbinterface import ...  # emitting
from invenio.bibauthorid_dbinterface import *  # pylint:  disable-msg=W0614

import invenio.bibauthorid_dbinterface as dbinter


def group_personid(papers_table="aidPERSONID_PAPERS", data_table="aidPERSONID_DATA"):
    '''
    Extracts, groups and returns the whole personid.
    '''
    papers = dbinter.get_all_author_paper_associations(papers_table)
    data = dbinter.get_author_data_associations(data_table)

    group = lambda x: groupby(sorted(x, key=itemgetter(0)), key=itemgetter(0))
    to_dict = lambda x: dict((pid, map(itemgetter(slice(1, None)), data)) for pid, data in x)

    return (to_dict(group(papers)), to_dict(group(data)))


def compare_personid_tables(personIDold_papers, personIDold_data,
                            personIDnew_papers, personIDnew_data, fp):
    """
    Compares how personIDnew is different to personIDold.
    The two arguments must be generated with group_personid.
    fp must be a valid file object.
    """
    header_new = "+++ "
#    header_old = "    "
    header_removed = "--- "

    def write_new_personid(pid):
        fp.write("            Personid %d\n" % pid)

    def write_end_personid():
        fp.write("\n")

    def write_paper(row, header):
        fp.write(
            "%s[PAPER] %s, signature %s %d %d, flag: %d, lcul: %d\n" %
            (header, row[3], row[0], row[1], row[2], row[4], row[5]))

    def write_data(row, header):
        tag = "[%s]" % row[0].upper()
        fp.write("%s%s %s, opt: (%s %s %s)\n" % (header, tag, row[1], row[2], row[3], row[4]))

    all_pids = (frozenset(personIDold_data.keys())
                | frozenset(personIDnew_data.keys())
                | frozenset(personIDold_papers.keys())
                | frozenset(personIDnew_papers.keys()))

    for pid in all_pids:
        data_old = frozenset(personIDold_data.get(pid, frozenset()))
        data_new = frozenset(personIDnew_data.get(pid, frozenset()))
#        old_data = data_new & data_old
        new_data = data_new - data_old
        del_data = data_old - data_new

        papers_old = frozenset(personIDold_papers.get(pid, frozenset()))
        papers_new = frozenset(personIDnew_papers.get(pid, frozenset()))
#        old_papers = papers_new & papers_old
        new_papers = papers_new - papers_old
        del_papers = papers_old - papers_new

        if new_data or del_data or new_papers or del_papers:
            write_new_personid(pid)

            for arr, header in zip([new_data, del_data],
                                   [header_new, header_removed]):
                for row in arr:
                    write_data(row, header)

            for arr, header in zip([new_papers, del_papers],
                                   [header_new, header_removed]):
                for row in arr:
                    write_paper(row, header)

            write_end_personid()


def compare_personid_tables_easy(suffix='_copy', filename='/tmp/pid_comparison'):
    f = open(filename, 'w')
    oldPap, oldDat = group_personid('aidPERSONIDPAPERS' + suffix, 'aidPERSONIDDATA' + suffix)
    pap, dat = group_personid('aidPERSONIDPAPERS', 'aidPERSONIDDATA')
    compare_personid_tables(oldPap, oldDat, pap, dat, f)
    f.close()


def filter_bibrecs_outside(all_papers):
    all_bibrecs = get_all_bibrecs_from_aidpersonidpapers()

    to_remove = list(frozenset(all_bibrecs) - frozenset(all_papers))
    chunk = 1000
    separated = [to_remove[i: i + chunk] for i in range(0, len(to_remove), chunk)]

    for sep in separated:
        remove_papers(sep)
