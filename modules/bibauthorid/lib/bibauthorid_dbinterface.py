# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2013 CERN.
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
    Filename: bibauthorid_dbinterface.py

    This is the only file in bibauthorid which should
    use the database. It offers an interface for all
    the other files in the module.
'''

from invenio.config import CFG_SITE_URL, \
    CFG_BIBAUTHORID_SEARCH_ENGINE_MAX_DATACHUNK_PER_INSERT_DB_QUERY
import invenio.bibauthorid_config as bconfig

import gc
import datetime
from itertools import groupby, count, ifilter, chain, imap, repeat
from operator import itemgetter

from invenio.search_engine_utils import get_fieldvalues
from invenio.access_control_engine import acc_authorize_action
from invenio.config import CFG_SITE_URL

from invenio.bibauthorid_name_utils import split_name_parts
from invenio.bibauthorid_name_utils import create_canonical_name
from invenio.bibauthorid_name_utils import create_normalized_name

from invenio.dbquery import run_sql
from invenio import bibtask

from msgpack import packb as serialize
from msgpack import unpackb as deserialize

try:
    from collections import defaultdict
except ImportError:
    from invenio.bibauthorid_general_utils import defaultdict

from invenio.dbquery import run_sql
from invenio.htmlutils import X
from invenio.search_engine import perform_request_search, get_record
from invenio.bibrecord import record_get_field_value, \
    record_get_field_instances
from invenio.access_control_engine import acc_authorize_action
from invenio.bibauthorid_name_utils import split_name_parts, \
    create_canonical_name, create_matchable_name
from invenio.bibauthorid_general_utils import memoized
from invenio.bibauthorid_general_utils import monitored
from invenio.bibauthorid_logutils import Logger
import time


# run_sql = monitored(run_sql)

logger = Logger("db_interface")

MARC_100_700_CACHE = None


#
#
# aidPERSONIDPAPERS table                                ###
#
#
# ********** setters **********#
def add_signature(sig, name, pid, flag=0, user_level=0, m_name=None):
    '''
    Adds the given signature to the specified author.

    @param sig: signature (bibref_table, bibref_value, bibrec)
    @type sig: tuple (int, int, int)
    @param name: name to be assigned for the author
    @type name: str
    @param pid: author identifier
    @type pid: int
    @param flag: author-paper association status
    @type flag: int
    @param user_level: lcul
    @type user_level: int
    '''
    if not name:
        name = get_name_by_bibref(sig[0:2])

    if not m_name:
        m_name = create_matchable_name(name)

    run_sql('insert into aidPERSONIDPAPERS'
            '(personid, bibref_table, bibref_value, bibrec, name, m_name, flag, lcul) '
            'values (%s, %s, %s, %s, %s, %s, %s, %s)',
            (pid, str(sig[0]), sig[1], sig[2], name, m_name, flag, user_level))


def move_signature(sig, pid, force_claimed=False, set_unclaimed=False):
    '''
    Reassigns an already assigned signature to a different author.

    @param sig: signature (bibref_table, bibref_value, bibrec)
    @type sig: tuple (int, int, int)
    @param pid: author identifier
    @type pid: int
    @param force_claimed: only if signature is claimed or rejected
    @type force_claimed: bool
    @param set_unclaimed: set signature as unclaimed
    @type set_unclaimed: bool
    '''
    query = ('update aidPERSONIDPAPERS '
             'set personid=%s ')
    if set_unclaimed:
        query += ", flag=0 "
    query += ('where bibref_table like %s '
              'and bibref_value=%s '
              'and bibrec=%s ')
    if not force_claimed:
        query += " and (flag <> 2 and flag <> -2)"

    run_sql(query, (pid, sig[0], sig[1], sig[2]))


def modify_signature(old_ref, rec, new_ref, new_name):
    '''
    Modifies an already assigned signature.

    @param old_ref: old bibref (bibref_table, bibref_value)
    @type old_ref: tuple (int, int)
    @param rec: paper identifier
    @type rec: int
    @param new_ref: new bibref (bibref_table, bibref_value)
    @type new_ref: tuple (int, int)
    @param new_name: new name to be assigned for the author
    @type new_name: str
    '''
    if not new_name:
        new_name = get_name_by_bibref(new_ref)

    m_name = create_matchable_name(new_name)

    run_sql('update aidPERSONIDPAPERS '
            'set bibref_table=%s, bibref_value=%s, name=%s, m_name=%s '
            'where bibref_table like %s '
            'and bibref_value=%s '
            'and bibrec=%s',
            (str(new_ref[0]), new_ref[1], new_name, m_name,
             str(old_ref[0]), old_ref[1], rec))


def remove_signatures(sigs):  # remove_sigs
    '''
    Deletes the given signatures.

    @param sigs: signatures to be removed [(bibref_table, bibref_value, bibrec),]
    @type sigs: list [(int, int, int),]
    '''
    for sig in sigs:
        _delete_from_aidpersonidpapers_where(table=sig[0], ref=sig[1], rec=sig[2])


def remove_papers(recs):  # remove_all_bibrecs
    '''
    Deletes all data about the given papers from all authors.

    @param recs: paper identifiers
    @type recs: list [int,]
    '''
    if recs:
        recs_sqlstr = _get_sqlstr_from_set(recs)
        run_sql('delete from aidPERSONIDPAPERS '
                'where bibrec in %s' % recs_sqlstr)


def transfer_papers_to_author(papers_data, new_pid):
    '''
    It passes possesion of papers to another author.

    @param papers_data: paper relevant data [(pid, bibref_table, bibref_value, bibrec),]
    @type papers_data: list [(int, str, int, int),]
    @param new_pid: author identifier
    @type new_pid: int
    '''
    for pid, table, ref, rec, flag in papers_data:
        run_sql('update aidPERSONIDPAPERS '
                'set personid=%s, flag=%s '
                'where personid=%s '
                'and bibref_table like %s '
                'and bibref_value=%s '
                'and bibrec=%s',
                (new_pid, flag, pid, table, ref, rec))


def confirm_papers_to_author(pid, sigs_str, user_level=0):  # confirm_papers_to_person
    '''
    Confirms the relationship between the given author and the specified papers
    (from user input).

    @param pid: author identifier
    @type pid: int
    @param sigs_str: signatures to confirm (e.g. [('100:7531,9024'),] )
    @type sigs_str: list [(str),]
    @param user_level: lcul
    @type user_level: int

    @return: confirmation status and message key for each signature [(status, message_key),]
    @rtype: list [(bool, str),]
    '''
    pids_to_update = set([pid])
    statuses = list()

    for s in sigs_str:
        sig = _split_signature_string(s)
        table, ref, rec = sig

        # the paper should be present, either assigned or rejected
        papers = run_sql('select bibref_table, bibref_value, bibrec, personid, flag '
                         'from aidPERSONIDPAPERS '
                         'where bibrec=%s '
                         'and flag >= -2',
                         (rec,))

        # select bibref_table, bibref_value, bibrec
        # from aidPERSONIDPAPERS
        # where personid=pid
        # and bibrec=rec
        # and flag > -2
        author_not_rejected_papers = [p[0:3] for p in papers if p[3] == pid and p[4] > -2]

        # select bibref_table, bibref_value, bibrec
        # from aidPERSONIDPAPERS
        # where personid=pid
        # and bibrec=rec
        # and flag=-2
        author_rejected_papers = [p[0:3] for p in papers if p[3] == pid and p[4] == -2]

        # select bibref_table, bibref_value, bibrec
        # from aidPERSONIDPAPERS
        # where personid <> pid
        # and bibrec=rec
        # and flag > -2
        diff_author_not_rejected_papers = [p[0:3] for p in papers if p[3] != pid and p[4] > -2]

        # select *
        # from aidPERSONIDPAPERS "
        # where bibref_table=table
        # and bibref_value=ref
        # and bibrec=rec
        # and flag > -2
        sig_exists = [True for p in papers if p[0] == table and p[1] == ref and p[4] > -2]

        # All papers that are being claimed should be present in aidPERSONIDPAPERS, thus:
        # assert author_not_rejected_papers or author_rejected_papers or diff_author_not_rejected_papers, 'There should be at least something regarding this bibrec!'
        # assert sig_exists, 'The signature should exist'
        # should always be valid.
        # BUT, it usually happens that claims get done out of the browser/session cache which is hours/days old,
        # hence it happens that papers are claimed when they no longer exist in the system.
        # For the sake of mental sanity, instead of crashing from now on we just ignore such cases.
        if not (author_not_rejected_papers or author_rejected_papers or diff_author_not_rejected_papers) or not sig_exists:
            statuses.append({'success': False, 'operation': 'confirm'})
            continue
        statuses.append({'success': True, 'operation': 'confirm'})

        # It should not happen that a paper is assigned more than once to the same person.
        # But sometimes it happens in rare unfortunate cases of bad concurrency circumstances,
        # so we try to fix it directly instead of crashing here.
        # Once a better solution for dealing with concurrency is found, the following asserts
        # shall be reenabled to allow better control on what happens.
        # assert len(author_not_rejected_papers) < 2, "This paper should not be assigned to this person more then once! %s" % author_not_rejected_papers
        # assert len(diff_author_not_rejected_papers) < 2, "There should not be
        # more than one copy of this paper! %s" % diff_author_not_rejected_papers

        # If the bibrec is present with a different bibref, the existing one must be moved somewhere
        # else before we can claim the incoming one.
        for pap in author_not_rejected_papers:
            # move to someone else all unwanted signatures
            if pap != sig:
                new_pid = get_free_author_id()
                pids_to_update.add(new_pid)
                move_signature(pap, new_pid)

        # Make sure that the incoming claim is unique and get rid of all rejections, they are useless
        # from now on.
        remove_signatures([sig])
        add_signature(sig, None, pid)
        run_sql('update aidPERSONIDPAPERS '
                'set personid=%s, flag=%s, lcul=%s '
                'where bibref_table like %s '
                'and bibref_value=%s '
                'and bibrec=%s',
                (pid, '2', user_level, table, ref, rec))
    update_canonical_names_of_authors(pids_to_update)

    return statuses


def reject_papers_from_author(pid, sigs_str, user_level=0):  # reject_papers_from_person
    '''
    Confirms the negative relationship between the given author and the
    specified papers (from user input).

    @param pid: author identifier
    @type pid: int
    @param sigs_str: signatures to confirm (e.g. [('100:7531,9024'),] )
    @type sigs_str: list [(str),]
    @param user_level: lcul
    @type user_level: int

    @return: confirmation status and message key for each signature [(status, message_key),]
    @rtype: list [(bool, str),]
    '''
    new_pid = get_free_author_id()
    pids_to_update = set([pid])
    statuses = list()

    for s in sigs_str:
        sig = _split_signature_string(s)
        table, ref, rec = sig

        # the paper should be present, either assigned or rejected
        sig_exists = get_author_info_of_confirmed_paper(sig)

        # For the sake of mental sanity (see commentis in confirm_papers_to_author) just ignore if this paper does not longer exist.
        # assert sig_exists, 'The signature should exist'
        if not sig_exists:
            statuses.append({'success': False, 'operation': 'reject'})
            continue
        statuses.append({'success': True, 'operation': 'reject'})

        # If the record is already assigned to a different person the rejection is meaningless.
        # If not, we assign the paper to someone else (it doesn't matter who because eventually
        # it will be reassigned by tortoise) and reject it from the current person.
        current_pid, name = sig_exists[0]
        if current_pid == pid:
            move_signature(sig, new_pid, force_claimed=True, set_unclaimed=True)
            pids_to_update.add(new_pid)
            add_signature((table, ref, rec), name, pid, flag=-2, user_level=user_level)

    update_canonical_names_of_authors(pids_to_update)

    return statuses


def reset_papers_of_author(pid, sigs_str):  # reset_papers_flag
    '''
    Redefines the relationship of the given author and the specified papers as
    neutral (neither claimed nor rejected).

    @param pid: author identifier
    @type pid: int
    @param sigs_str: signatures to reset (e.g. [('100:7531,9024'),] )
    @type sigs_str: list [(str),]

    @return: confirmation status and message key for each signature [(status, message_key),]
    @rtype: list [(bool, str),]
    '''
    statuses = list()

    for s in sigs_str:
        sig = _split_signature_string(s)
        table, ref, rec = sig

        papers = _select_from_aidpersonidpapers_where(
            select=['bibref_table',
                    'bibref_value',
                    'bibrec',
                    'flag'],
            pid=pid,
            rec=rec)

        assert len(papers) < 2

        # select bibref_table, bibref_value, bibrec
        # from aidPERSONIDPAPERS
        # where personid=pid
        # and bibrec=rec
        # and flag=-2
        author_rejected_papers = [p[0:3] for p in papers if p[3] == -2]

        # select bibref_table, bibref_value, bibrec
        # from aidPERSONIDPAPERS
        # where personid=pid
        # and bibref_table=table
        # and bibref_value=ref
        # and bibrec=rec
        # and flag > -2
        sig_exists = [p[0:3] for p in papers if p[0] == table and p[1] == ref and p[3] > -2]

        # For the sake of mental sanity (see comments in confirm_papers_to_author) just ignore if this paper does not longer exist.
        # assert sig_exists, 'The signature should exist'
        if author_rejected_papers or not sig_exists:
            statuses.append({'success': False, 'operation': 'reset'})
            continue
        statuses.append({'success': True, 'operation': 'reset'})

        run_sql('delete from aidPERSONIDPAPERS '
                'where bibref_table like %s '
                'and bibref_value=%s '
                'and bibrec=%s', sig)
        add_signature(sig, None, pid)

    return statuses


def duplicated_conirmed_papers_exist(printer, repair=False):  # check_duplicated_papers
    '''
    It examines if there are records of confirmed papers in aidPERSONIDPAPERS
    table which are in an impaired state (duplicated) and repairs them if
    specified.

    @param printer: for log keeping
    @type printer: func
    @param repair: fix the duplicated records
    @type repair: bool

    @return: duplicated records are found
    @rtype: bool
    '''
    duplicated_conirmed_papers_found = False
    author_confirmed_papers = dict()
    to_reassign = list()

    confirmed_papers = run_sql('select personid, bibrec '
                               'from aidPERSONIDPAPERS '
                               'where flag <> %s', (-2,))

    for pid, rec in confirmed_papers:
        author_confirmed_papers.setdefault(pid, []).append(rec)

    for pid, recs in author_confirmed_papers.iteritems():

        if not len(recs) == len(set(recs)):
            duplicated_conirmed_papers_found = True

            duplicates = sorted(recs)
            duplicates = set([rec for i, rec in enumerate(duplicates[:-1]) if rec == duplicates[i + 1]])
            printer("Person %d has duplicated papers: %s" % (pid, duplicates))

            if repair:
                for duprec in duplicates:
                    printer("Repairing duplicated bibrec %s" % str(duprec))
                    claimed_from_involved = run_sql('select personid, bibref_table, bibref_value, bibrec, flag '
                                                    'from aidPERSONIDPAPERS '
                                                    'where personid=%s '
                                                    'and bibrec=%s '
                                                    'and flag >= 2', (pid, duprec))
                    if len(claimed_from_involved) != 1:
                        to_reassign.append(duprec)
                        _delete_from_aidpersonidpapers_where(rec=duprec, pid=pid)
                    else:
                        run_sql('delete from aidPERSONIDPAPERS '
                                'where personid=%s '
                                'and bibrec=%s '
                                'and flag < 2', (pid, duprec))

    if repair and to_reassign:
        printer("Reassigning deleted bibrecs %s" % str(to_reassign))
        from invenio.bibauthorid_rabbit import rabbit
        rabbit(to_reassign)

    return duplicated_conirmed_papers_found


def duplicated_confirmed_signatures_exist(printer, repair=False):   # check_duplicated_signatures
    '''
    It examines if there are records of confirmed signatures in
    aidPERSONIDPAPERS table which are in an impaired state (duplicated) and
    repairs them if specified.

    @param printer: for log keeping
    @type printer: func
    @param repair: fix the duplicated signatures
    @type repair: bool

    @return: duplicated signatures are found
    @rtype: bool
    '''
    duplicated_confirmed_signatures_found = False
    paper_confirmed_bibrefs = dict()
    to_reassign = list()

    confirmed_sigs = run_sql('select bibref_table, bibref_value, bibrec '
                             'from aidPERSONIDPAPERS '
                             'where flag > %s', (-2,))

    for table, ref, rec in confirmed_sigs:
        paper_confirmed_bibrefs.setdefault(rec, []).append((table, ref))

    for rec, bibrefs in paper_confirmed_bibrefs.iteritems():

        if not len(bibrefs) == len(set(bibrefs)):
            duplicated_confirmed_signatures_found = True

            duplicates = sorted(bibrefs)
            duplicates = set([bibref for i, bibref in enumerate(duplicates[:-1]) if bibref == duplicates[i + 1]])
            printer("Paper %d has duplicated signatures: %s" % (rec, duplicates))

            if repair:
                for table, ref in duplicates:
                    printer("Repairing duplicated signature %s" % str((table, ref)))
                    claimed = _select_from_aidpersonidpapers_where(
                        select=['personid',
                                'bibref_table',
                                'bibref_value',
                                'bibrec'],
                        table=table,
                        ref=ref,
                        rec=rec,
                        flag=2)

                    if len(claimed) != 1:
                        to_reassign.append(rec)
                        _delete_from_aidpersonidpapers_where(table=table, ref=ref, rec=rec)
                    else:
                        run_sql('delete from aidPERSONIDPAPERS '
                                'where bibref_table like %s '
                                'and bibref_value=%s '
                                'and bibrec=%s '
                                'and flag < 2', (table, ref, rec))

    if repair and to_reassign:
        printer("Reassigning deleted bibrecs %s" % str(to_reassign))
        from invenio.bibauthorid_rabbit import rabbit
        rabbit(to_reassign)

    return duplicated_confirmed_signatures_found


def wrong_names_exist(printer, repair=False):  # check_wrong_names
    '''
    It examines if there are records in aidPERSONIDPAPERS table which carry a
    wrong name and repairs them if specified.

    @param printer: for log keeping
    @type printer: func
    @param repair: fix the found wrong names
    @type repair: bool

    @return: wrong names are found
    @rtype: bool
    '''
    wrong_names_found = False
    wrong_names, wrong_names_count = get_wrong_names()

    if wrong_names_count > 0:
        wrong_names_found = True
        printer("%d corrupted names in aidPERSONIDPAPERS." % wrong_names_count)
        for wrong_name in wrong_names:
            if wrong_name[2]:
                printer(
                    "Outdated name, ('%s' instead of '%s' (%s:%d))." %
                    (wrong_name[3], wrong_name[2], wrong_name[0], wrong_name[1]))
            else:
                printer("Invalid id (%s:%d)." % (wrong_name[0], wrong_name[1]))

            if repair:
                printer("Fixing wrong name: %s" % str(wrong_name))
                if wrong_name[2]:
                    m_name = create_matchable_name(wrong_name[2])
                    run_sql('update aidPERSONIDPAPERS '
                            'set name=%s, m_name=%s, '
                            'where bibref_table like %s '
                            'and bibref_value=%s',
                            (wrong_name[2], m_name, wrong_name[0], wrong_name[1]))
                else:
                    _delete_from_aidpersonidpapers_where(table=wrong_name[0], ref=wrong_name[1])

    return wrong_names_found


def impaired_rejections_exist(printer, repair=False):  # check_wrong_rejection
    '''
    It examines if there are records of rejected papers in aidPERSONIDPAPERS
    table which are in an impaired state (not assigned or both confirmed and
    rejected for the same author) and repairs them if specified.

    @param printer: for log keeping
    @type printer: func
    @param repair: fix the damaged records
    @type repair: bool

    @return: damaged records are found
    @rtype: bool
    '''
    impaired_rejections_found = False
    to_reassign = list()
    to_deal_with = list()

    rejected_papers = set(_select_from_aidpersonidpapers_where(
        select=['bibref_table', 'bibref_value', 'bibrec'], flag=-2))

    confirmed_papers = set(run_sql('select bibref_table, bibref_value, bibrec '
                                   'from aidPERSONIDPAPERS '
                                   'where flag > %s', (-2,)))
    not_assigned_papers = rejected_papers - confirmed_papers

    for paper in not_assigned_papers:
        printer("Paper (%s:%s,%s) was rejected but never reassigned" % paper)
        to_reassign.append(paper)

    rejected_papers = set(
        _select_from_aidpersonidpapers_where(
            select=[
                'personid',
                'bibref_table',
                'bibref_value',
                'bibrec'],
            flag=-2))

    confirmed_papers = set(run_sql('select personid, bibref_table, bibref_value, bibrec '
                                   'from aidPERSONIDPAPERS '
                                   'where flag > %s', (-2,)))
    # papers which are both confirmed and rejected for/from the same author
    both_confirmed_and_rejected_papers = rejected_papers & confirmed_papers

    for paper in both_confirmed_and_rejected_papers:
        printer("Conflicting assignment/rejection: %s" % str(paper))
        to_deal_with.append(paper)

    if not_assigned_papers or both_confirmed_and_rejected_papers:
        impaired_rejections_found = True

    if repair and (to_reassign or to_deal_with):
        from invenio.bibauthorid_rabbit import rabbit

        if to_reassign:
            # Rabbit is not designed to reassign signatures which are rejected but not assigned:
            # All signatures should be assigned. If a rejection occurs, the signature should get
            # moved to a new place and the rejection entry added, but never exist as a rejection only.
            # Hence, to force rabbit to reassign it we have to delete the rejection.
            printer("Reassigning bibrecs with missing entries: %s" % str(to_reassign))
            for sig in to_reassign:
                table, ref, rec = sig
                _delete_from_aidpersonidpapers_where(table=table, ref=ref, rec=rec, flag=-2)

            recs = [paper[2] for paper in to_reassign]
            rabbit(recs)

        if to_deal_with:
            # We got claims and rejections on the same paper for the same person. Let's forget about
            # it and reassign it automatically, they'll make up their minds sooner or later.
            printer("Deleting and reassigning bibrefrecs with conflicts %s" % str(to_deal_with))
            for sig in to_deal_with:
                pid, table, ref, rec = sig
                _delete_from_aidpersonidpapers_where(table=table, ref=ref, rec=rec, pid=pid)

            recs = map(itemgetter(3), to_deal_with)
            rabbit(recs)

    return impaired_rejections_found


def _delete_from_aidpersonidpapers_where(pid=None, table=None, ref=None, rec=None, name=None, flag=None, lcul=None):
    '''
    Deletes the records from aidPERSONIDPAPERS table with the given attributes.
    If no parameters are given it deletes all records.

    @param pid: author identifier
    @type pid: int
    @param table: bibref_table
    @type table: int
    @param ref: bibref_value
    @type ref: int
    @param rec: paper identifier
    @type rec: int
    @param name: author name
    @type name: str
    @param flag: flag
    @type flag: int
    @param lcul: lcul
    @type lcul: int
    '''
    conditions = list()
    add_condition = conditions.append
    args = list()
    add_arg = args.append

    if pid is not None:
        add_condition('personid=%s')
        add_arg(pid)
    if table is not None:
        add_condition("bibref_table like %s")
        add_arg(str(table))
    if ref is not None:
        add_condition('bibref_value=%s')
        add_arg(ref)
    if rec is not None:
        add_condition('bibrec=%s')
        add_arg(rec)
    if name is not None:
        add_condition('name=%s')
        add_arg(name)
    if flag is not None:
        add_condition('flag=%s')
        add_arg(flag)
    if lcul is not None:
        add_condition('lcul=%s')
        add_arg(lcul)

    if not conditions:
        return

    conditions_str = " and ".join(conditions)
    query = ('delete from aidPERSONIDPAPERS '
             'where %s') % conditions_str

    run_sql(query, tuple(args))

# ********** getters **********#


def get_all_bibrecs_from_aidpersonidpapers():
    '''
    Gets all papers which are associated to some author.

    @return: paper identifiers
    @rtype: set set(int,)
    '''
    return set([i[0] for i in _select_from_aidpersonidpapers_where(select=['bibrec'])])


def get_all_paper_data_of_author(pid):
    '''
    Gets all data concerning the papers that the specified author is associated
    with.

    @param pid: author identifier
    @type pid: int

    @return: paper relevant data ((pid, bibref_table, bibref_value, bibrec),)
    @rtype: tuple ((int, str, int, int),)
    '''
    return _select_from_aidpersonidpapers_where(select=['personid', 'bibref_table', 'bibref_value', 'bibrec', 'flag'], pid=pid)


def get_papers_of_author(pid, claimed_only=False, include_rejected=False):  # get_all_paper_records
    '''
    Gets all papers for the specific author. If 'claimed_only' flag is enabled
    it takes into account only claimed papers. Additionally if
    'include_rejected' flag is enabled, it takes into account rejected
    papers as well.

    @param pid: author identifier
    @type pid: int
    @param claimed_only: include a paper only if it is claimed
    @type claimed_only: bool
    @param include_rejected: include rejected papers (only when claimed_only flag is enabled)
    @type include_rejected: bool

    @return: paper identifiers
    @rtype: set set((int),)
    '''
    query = ('select bibrec '
             'from aidPERSONIDPAPERS '
             'where personid=%s')
    if claimed_only and include_rejected:
        query += " and (flag=2 or flag=-2)"
    elif claimed_only:
        query += " and flag=2"

    return set(run_sql(query, (pid,)))


def get_confirmed_papers_of_authors(pids):  # get_all_papers_of_pids
    '''
    Gets all records for the given authors.

    @param pids: author identifiers
    @type pids: list [int,]

    @return: records ((personid, bibref_table, bibref_value, bibrec, flag),)
    @rtype: generator ((int, str, int, int, int),)
    '''
    if not pids:
        return ()
    pids_sqlstr = _get_sqlstr_from_set(pids)
    papers = run_sql('select personid, bibref_table, bibref_value, bibrec, flag '
                     'from aidPERSONIDPAPERS '
                     'where personid in %s and flag > -2' % pids_sqlstr)

    return (p for p in papers)


def get_confirmed_papers_of_author(pid):  # get_person_bibrecs
    '''
    Gets all papers which are associated (non-negatively) to the given author.

    @param pid: author identifier
    @type pid: int

    @return: paper identifiers
    @rtype: list [int,]
    '''
    papers = run_sql('select bibrec '
                     'from aidPERSONIDPAPERS '
                     'where personid=%s and flag > -2', (str(pid),))
    papers = list(set([p[0] for p in papers]))

    return papers


def get_claimed_papers_of_author(pid):  # get_claimed_papers
    '''
    Gets all signatures for the manually claimed papers of the given author.

    @param pid: author identifier
    @type pid: int

    @return: signatures ((bibref_table, bibref_value, bibrec),)
    @rtype: tuple ((str, int, int),)
    '''
    return run_sql('select bibref_table, bibref_value, bibrec '
                   'from aidPERSONIDPAPERS '
                   'where personid=%s and flag > %s', (pid, 1))


def get_claimed_papers_from_papers(recs):
    '''
    Given a set of papers it returns the subset of claimed papers.

    @param recs: paper identifiers
    @type recs: frozenset frozenset(int,)

    @return: claimed paper identifiers
    @rtype: tuple ((int),)
    '''
    recs_sqlstr = _get_sqlstr_from_set(recs)
    claimed_recs = set(run_sql('select bibrec '
                               'from aidPERSONIDPAPERS '
                               'where bibrec in %s and flag=2' % recs_sqlstr))
    return claimed_recs


def get_rec_to_signatures_mapping():
    table = _select_from_aidpersonidpapers_where(
        select=['personid',
                'bibref_table',
                'bibref_value',
                'bibrec',
                'name'])
    cache = defaultdict(list)
    for row in table:
        cache[int(row[3])].append(row)
    return cache


def get_signatures_of_paper(rec):  # get_signatures_from_rec
    '''
    Gets all records with the given paper identifier.

    @param rec: paper identifier
    @type rec: int

    @return: records with the given paper identifier ((pid, bibref_table, bibref_value, bibrec, name),)
    @rtype: tuple ((int, str, int, int, str),)
    '''
    return _select_from_aidpersonidpapers_where(select=['personid', 'bibref_table', 'bibref_value', 'bibrec', 'name'], rec=rec)


def get_status_of_signature(sig_str):  # get_bibref_modification_status
    '''
    Gets the author-paper association status for the given signature.

    @param sig_str: signature (e.g. '100:7531,9024')
    @type sig_str: str

    @return: author-paper association status (flag, lcul)
    @rtype: tuple (int, int)
    '''
    if not sig_str:
        raise ValueError("A signature identifier is expected!")

    sig = _split_signature_string(sig_str)
    table, ref, rec = sig

    flags = _select_from_aidpersonidpapers_where(select=['flag', 'lcul'], table=table, ref=ref, rec=rec)

    if flags:
        return flags[0]
    else:
        return (False, 0)


def get_author_and_status_of_signature(sig_str):  # get_papers_status
    '''
    Gets the authors and the author-paper association status (for each author)
    of the paper reffered in the given signature.

    @param sig_str: signature (e.g. '100:7531,9024')
    @type sig_str: str

    @return: author identifiers and the author-paper association status [(bibref_table, bibref_value, bibrec), personid, flag]
    @rtype: list [[(str, int, int), int, int)],]
    '''
    sig = _split_signature_string(sig_str)
    table, ref, rec = sig

    author_and_status = _select_from_aidpersonidpapers_where(select=['personid', 'flag'], table=table, ref=ref, rec=rec)

    return [[sig] + list(i) for i in author_and_status]


def get_ordered_author_and_status_of_signature(sig):  # get_signature_info
    '''
    Gets the author and the author-paper association status affiliated to the
    given signature.

    @param sig: signature (bibref_table, bibref_value, bibrec)
    @type sig: tuple (str, int, int)

    @return: author identifier and author-paper association status
    @rtype: tuple ((int, int),)
    '''
    return run_sql('select personid, flag '
                   'from aidPERSONIDPAPERS '
                   'where bibref_table like %s '
                   'and bibref_value=%s '
                   'and bibrec=%s '
                   'order by flag', sig)


def get_author_and_status_of_confirmed_paper(sig):  # personid_from_signature
    '''
    Gets the confirmed author and author-paper association status affiliated to
    the given signature.

    @param sig: signature (bibref_table, bibref_value, bibrec)
    @type sig: tuple (str, int, int)

    @return: author identifier and author-paper association status
    @rtype: tuple ((int, int),)
    '''
    conf_author_and_status = run_sql('select personid, flag '
                                     'from aidPERSONIDPAPERS '
                                     'where bibref_table like %s '
                                     'and bibref_value=%s '
                                     'and bibrec=%s '
                                     'and flag > -2', sig)

    assert len(conf_author_and_status) < 2, "More that one author hold the same signature: %s" % conf_author_and_status

    return conf_author_and_status


def get_author_info_of_confirmed_paper(sig):  # personid_name_from_signature
    '''
    Gets the confirmed author and author name affiliated to the given
    signature.

    @param sig: signature (bibref_table, bibref_value, bibrec)
    @type sig: tuple (str, int, int)

    @return: author identifier and author name
    @rtype: tuple ((int, str),)
    '''
    conf_author = run_sql('select personid, name '
                          'from aidPERSONIDPAPERS '
                          'where bibref_table like %s '
                          'and bibref_value=%s '
                          'and bibrec=%s '
                          'and flag > -2', sig)

    assert len(conf_author) < 2, "More than one author hold the same signature: %s" % str(conf_author)

    return conf_author


def get_authors_of_claimed_paper(rec):  # get_personids_from_bibrec
    '''
    Gets all the authors who are associated (non-negatively) with the given
    paper.

    @param rec: paper identifier
    @type rec: int

    @return: author identifiers
    @rtype: set set(int,)
    '''
    pids = run_sql('select personid '
                   'from aidPERSONIDPAPERS '
                   'where bibrec=%s '
                   'and flag > -2', (rec,))
    if not pids:
        return set()

    return set([pid[0] for pid in pids])


def get_personid_signature_association_for_paper(rec):
    data = run_sql("select personid, bibref_table, bibref_value from aidPERSONIDPAPERS where "
                   "bibrec = %s and flag > -2", (rec,))
    associations = defaultdict(list)
    for i in data:
        associations[str(i[1]) + ':' + str(i[2])] = int(i[0])

    return associations


def get_coauthors_of_author(pid, excluding_recs=None):  # get_coauthor_pids
    '''
    Gets the authors who are sharing papers with the given author excluding
    from the common papers the specified set.

    @param pid: author identifier
    @type pid: int
    @param excluding_recs: excluding paper identifiers
    @type excluding_recs: list [int,]
    '''
    recs = get_confirmed_papers_of_author(pid)
    if excluding_recs:
	exclude_set = set(excluding_recs)
        recs = set(recs) - exclude_set
    else:
	exclude_set = set()

    if not recs:
        return list()
    recs_sqlstr = _get_sqlstr_from_set(recs)
    pids = run_sql('select personid, bibrec '
                   'from aidPERSONIDPAPERS '
                   'where bibrec in %s '
                   'and flag > -2' % recs_sqlstr)

    pids = set([(int(p), int(r)) for p, r in pids if (int(p) != int(pid) and int(r) not in exclude_set)])
    pids = sorted([p for p, r in pids])
    pids = groupby(pids)
    pids = [(key, len(list(val))) for key, val in pids]
    pids = sorted(pids, key=itemgetter(1), reverse=True)

    return pids


def get_names_to_records_of_author(pid):  # get_person_names_count
    '''
    Returns the set of names and times each name appears from the records which
    are associated to the given author.

    @param pid: author identifier
    @type pid: int

    @return: set of names and times each name appears
    @rtype: set set((int, str),)
    '''
    author_names = run_sql('select name, bibrec '
                           'from aidPERSONIDPAPERS '
                           'where personid=%s '
                           'and flag > -2', (pid,))
    author_names = [(name[0], name[1]) for name in author_names]
    names_count = defaultdict(set)
    for name, bibrec in author_names:
        names_count[name].add(bibrec)

    return dict((x, list(y)) for x, y in names_count.items())


def get_names_count_of_author(pid):
    return dict((x, len(y)) for x, y in get_names_to_records_of_author(pid).items()).items()


def _get_external_ids_from_papers_of_author(pid, limit_to_claimed_papers=False, force_cache_tables=False):  # collect_personID_external_ids_from_papers
    '''
    Gets a mapping which associates an external system (e.g. Inspire) with the
    identifiers that the given author carries in that system (based on the
    papers he is associated with).

    @param pid: author identifier
    @type pid: int
    @param limit_to_claimed_papers: take into account only claimed papers
    @type limit_to_claimed_papers: bool

    @return: mapping
    @rtype: dict {str: set(str,)}
    '''
    external_ids = dict()

    if bconfig.COLLECT_EXTERNAL_ID_INSPIREID:

        flag = -2
        if limit_to_claimed_papers:
            flag = 1

        sigs = run_sql('select bibref_table, bibref_value, bibrec '
                       'from aidPERSONIDPAPERS '
                       'where personid=%s '
                       'and flag > %s', (pid, flag))

        records_to_cache = [x[2] for x in sigs]

       # if len(records_to_cache) >= bconfig.EXT_ID_CACHE_THRESHOLD:
        populate_partial_marc_caches(records_to_cache)

        inspire_ids = set()
        for sig in sigs:
            try:
                inspire_id = get_inspire_id_of_signature(sig)[0]
            except IndexError:
                inspire_id = None
            if inspire_id is not None:
                inspire_ids.add(inspire_id)

        external_ids[bconfig.PERSONID_EXTERNAL_IDENTIFIER_MAP['Inspire']] = inspire_ids

    return external_ids


def get_validated_request_tickets_for_author(pid, tid=None):  # get_validated_request_ticket
    '''
    Gets the request tickets for the given author after it validates that their
    entries are correct. If an entry is incorrect it discards it.

    @param pid: author identifier
    @type pid: int
    @param tid: ticket identifier
    @type tid: int

    @return: validated request tickets (e.g. [[[('assign', '100:7531,9024'), ('reject', '100:7532,9025')], 1L],])
    @rtype: list [[[(str, str),], int],]
    '''
    request_tickets = get_request_tickets_for_author(pid, tid)

    for request_ticket in list(request_tickets):
        request_ticket['operations'] = list(request_ticket['operations'])
        for operation in list(request_ticket['operations']):
            action, bibrefrec = operation
            try:
                table, ref, rec = _split_signature_string(bibrefrec)
                present = bool(_select_from_aidpersonidpapers_where(select=['*'], table=table, ref=ref, rec=rec))

                if not present:
                    request_ticket['operations'].remove(operation)
                    if not request_ticket['operations']:
                        remove_request_ticket_for_author(pid, tid=request_ticket['tid'])
            except:   # no matter what goes wrong that's an invalid entry in the ticket. We discard it!
                request_ticket['operations'].remove(operation)

    return request_tickets


def get_authors_by_name_regexp(name_regexp):  # get_all_personids_by_name
    '''
    Gets authors whose name matches the regular expression pattern.

    @param name_regexp: SQL regular expression
    @type name_regexp: str

    @return: authors whose name satisfies the regexp ((personid, name),)
    @rtype: tuple ((int, str),)
    '''
    return run_sql('select personid, name '
                   'from aidPERSONIDPAPERS '
                   'where name like %s '
                   'and flag > -2 '
                   'group by personid, name', (name_regexp,))


def get_authors_by_name(name, limit_to_recid=False, use_matchable_name=False):  # find_pids_by_exact_name
    '''
    Gets all authors who have records with the specified name.

    @param name: author name
    @type name: str

    @return: author identifiers
    @rtype: set set((int),)
    '''
    if use_matchable_name:
        name_column = 'm_name'
    else:
        name_column = 'name'

    query_string_one = "select distinct(personid) from aidPERSONIDPAPERS where %s" % name_column
    if limit_to_recid:
        pids = run_sql("".join([query_string_one, "=%s and bibrec=%s and flag>-2"]),
                      (name, limit_to_recid))
        return [pid[0] for pid in pids]
    else:
        pids = run_sql("".join([query_string_one, "=%s and flag>-2"]),
                      (name,))
        return [pid[0] for pid in pids]


def get_paper_to_author_and_status_mapping():  # get_bibrefrec_to_pid_flag_mapping
    '''
    Gets a mapping which associates signatures with author identifiers and the
    status of the author-paper association (of the paper that the signature is
    reffering to).

    @return: mapping
    @rtype: dict {(str, int, int): set((int, int),)}
    '''
    mapping = defaultdict(list)
    sigs_authors = _select_from_aidpersonidpapers_where(
        select=['bibref_table', 'bibref_value', 'bibrec', 'personid', 'flag'])

    gc.disable()

    for i in sigs_authors:
        sig = (i[0], i[1], i[2])
        pid_flag = (i[3], i[4])
        mapping[sig].append(pid_flag)

    gc.collect()
    gc.enable()

    return mapping


def get_author_to_papers_mapping(recs, limit_by_name=None):  # get_personids_and_papers_from_bibrecs
    '''
    It finds the authors of the given papers and returns a mapping which
    associates each author with the set of papers he has affiliation with.
    If 'limit_by_name' is specified it will take into account only the authors
    who carry the specific surname.

    @param recs: paper identifiers
    @type recs: list [int,]
    @param limit_by_name: author surname
    @type limit_by_name: str

    @return: mapping
    @rtype: list [(int, set(int,)),]
    '''
    pids_papers = list()
    if not recs:
        return pids_papers

    recs_sqlstr = _get_sqlstr_from_set(recs)

    surname = None
    if limit_by_name:
        try:
            surname = create_normalized_name(split_name_parts(limit_by_name)[0])
        except IndexError:
            pass

    if surname:
        pids_papers = run_sql('select personid, bibrec '
                              'from aidPERSONIDPAPERS '
                              'where bibrec in %s '
                              'and name like %s' % (recs_sqlstr, '"' + surname + '%' + '"'))
    else:
        pids_papers = run_sql('select personid, bibrec '
                              'from aidPERSONIDPAPERS '
                              'where bibrec in %s' % recs_sqlstr)

    pids_papers = sorted(pids_papers, key=itemgetter(0))
    pids_papers = groupby(pids_papers, key=itemgetter(0))
    pids_papers = [(pid, set([tup[1] for tup in pid_paps])) for pid, pid_paps in pids_papers]
    pids_papers = sorted(pids_papers, key=lambda x: len(x[1]), reverse=True)

    return pids_papers


def get_author_to_confirmed_names_mapping(since=None):  # get_all_modified_names_from_personid
    '''
    For all authors it gets the set of names from the papers each author is
    associated with. It excludes the names that come from rejected papers.
    If 'since' is specified, only authors with modified records after this date
    are taken into account.

    @param since: consider only authors with modified records after this date
    @type since: str

    @return: mapping
    @rtype: generator ((int, set([str,], int)),)
    '''
    args = list()
    add_arg = args.append

    query = ('select personid, name '
             'from aidPERSONIDPAPERS '
             'where flag > -2')
    if since:
        query += " and last_updated > %s"
        add_arg(since)

    pids_names = run_sql(query, tuple(args))

    if since:
        pids = set([pid for pid, _ in pids_names])
        pids_sqlstr = _get_sqlstr_from_set(pids)
        pids_names = run_sql('select personid, name '
                             'from aidPERSONIDPAPERS '
                             'where personid in %s '
                             'and flag > -2' % pids_sqlstr)

    res = dict()
    for pid, name in pids_names:
        try:
            res[pid][1].add(name)
            res[pid][2] += 1
        except KeyError:
            res[pid] = [pid, set([name]), 1]

    return (tuple(res[pid]) for pid in res.keys())


def get_all_modified_names_from_personid(since=None):
    if since:
        all_pids = run_sql("SELECT DISTINCT personid "
                           "FROM aidPERSONIDPAPERS "
                           "WHERE flag > -2 "
                           "AND last_updated > %s"
                           % since)
    else:
        all_pids = run_sql("SELECT DISTINCT personid "
                           "FROM aidPERSONIDPAPERS "
                           "WHERE flag > -2 ")

    return ((name[0][0], set(n[1] for n in name), len(name))
            for name in (run_sql(
                         "SELECT personid, name "
                         "FROM aidPERSONIDPAPERS "
                         "WHERE personid = %s "
                         "AND flag > -2", p)
                         for p in all_pids))


def get_author_to_name_and_occurrence_mapping():
    '''
    Gets a mapping which associates authors with the set of names they carry
    and the number of times each name occurs in their papers.

    @return: mapping
    @rtype: dict {int: {str: int},}
    '''
    cl = lambda: defaultdict(int)
    mapping = defaultdict(cl)
    authors = run_sql('select personid, name '
                      'from aidPERSONIDPAPERS '
                      'where flag > -2')

    for pid, name in authors:
        mapping[pid][name] += 1
    return mapping


def get_name_to_authors_mapping():  # get_name_string_to_pid_dictionary
    '''
    Gets a mapping which associates names with the set of authors who carry
    each name.

    @return: mapping
    @rtype: dict {str: set(int,)}
    '''
    mapping = defaultdict(set)
    authors = _select_from_aidpersonidpapers_where(select=['personid', 'name'])

    for pid, name in authors:
        mapping[name].add(pid)

    return mapping


def get_confirmed_name_to_authors_mapping():
    '''
    Gets a mapping which associates confirmed names with the set of authors who
    carry each name.

    @return: mapping
    @rtype: dict {str: set(int,)}
    '''
    mapping = defaultdict(set)
    authors = run_sql('select personid, name '
                      'from aidPERSONIDPAPERS '
                      'where flag > -2')

    for pid, name in authors:
        mapping[name].add(pid)

    return mapping


def get_all_author_paper_associations(table_name='aidPERSONIDPAPERS'):  # get_full_personid_papers
    '''
    Gets all author-paper associations (from aidPERSONIDPAPERS table or any
    other table with the same structure).

    @param table_name: name of the table with the author-paper associations
    @type table_name: str

    @return: author-paper associations ((pid, bibref_table, bibref_value, bibrec, name, flag, lcul),)
    @rtype: tuple ((int, str, int, int, str, int, int),)
    '''
    return run_sql('select personid, bibref_table, bibref_value, bibrec, name, flag, lcul '
                   'from %s' % table_name)


def get_wrong_names():
    '''
    Returns a generator with all wrong names in aidPERSONIDPAPERS table.

    @return: wrong names (table, ref, correct_name)
    @rtype: generator ((str, int, str),)
    '''
    bib100 = dict((name_id, name_value) for name_id, name_value in get_bib10x())
    bib700 = dict((name_id, name_value) for name_id, name_value in get_bib70x())

    aidpersonidpapers100 = set(_select_from_aidpersonidpapers_where(select=['bibref_value', 'name'], table='100'))
    aidpersonidpapers700 = set(_select_from_aidpersonidpapers_where(select=['bibref_value', 'name'], table='700'))

    wrong100 = set(('100', nid, bib100.get(nid, None), nvalue) for nid, nvalue in aidpersonidpapers100
                   if nvalue != bib100.get(nid, None))
    wrong700 = set(('700', nid, bib700.get(nid, None), nvalue) for nid, nvalue in aidpersonidpapers700
                   if nvalue != bib700.get(nid, None))

    total = len(wrong100) + len(wrong700)

    return chain(wrong100, wrong700), total


def get_signatures_of_paper_and_author(sig, pid):  # find_conflicts
    '''
    Gets confirmed signatures for the given signature and author.

    @param sig: signature (bibref_table, bibref_value, bibrec)
    @type sig: tuple (int, int, int)
    @param pid: author identifier
    @type pid: int

    @return: confirmed signatures
    @rtype: tuple ((bibref_table, bibref_value, bibrec, flag),)
    '''
    return run_sql('select bibref_table, bibref_value, bibrec, flag '
                   'from aidPERSONIDPAPERS '
                   'where personid=%s '
                   'and bibrec=%s '
                   'and flag <> -2', (pid, sig[2]))


def paper_affirmed_from_user_input(pid, sig_str):  # person_bibref_is_touched_old
    '''
    Examines if the given author and the specified signature association has
    been affirmed from user input.

    @param pid: author identifier
    @type pid: int
    @param sig_str: signature (e.g. '100:7531,9024')
    @type sig_str: str

    @return: author and signature association is affirmed from user input
    @rtype: bool
    '''
    sig = _split_signature_string(sig_str)
    table, ref, rec = sig

    flag = _select_from_aidpersonidpapers_where(select=['flag'], pid=pid, table=table, ref=ref, rec=rec)

    try:
        flag = flag[0][0]
    except IndexError:
        return False

    if -2 < flag < 2:
        return False

    return True


def update_external_ids_of_authors(pids=None, overwrite=False, limit_to_claimed_papers=False,  # update_personID_external_ids
                                   force_cache_tables=False):  # TODO turn to True
    '''
    Updates the external ids for the given authors. If no authors are specified
    it does the updating for all authors. The possesion of an external id is
    determined by the papers an author is associated with.

    @param pids: author identifiers
    @type pids: list [int,]
    @param overwrite: deletes all existing ext ids and recalculates them from scratch
    @type overwrite: bool
    @param limit_to_claimed_papers: take into account only claimed papers
    @type limit_to_claimed_papers: bool
    @param force_cache_tables: use a caching mechanism for the calculation
    @type force_cache_tables: bool
    '''

    if not pids:
        pids = set([i[0] for i in _select_from_aidpersonidpapers_where(select=['personid'])])

    for idx, pid in enumerate(pids):

        logger.update_status(float(idx) / float(len(pids)), "Updating external ids...")

        collected = _get_external_ids_from_papers_of_author(pid,
                                                            limit_to_claimed_papers=limit_to_claimed_papers,
                                                            force_cache_tables=True)

        collected_ids_exist = False
        for external_id in collected.values():
            if external_id:
                collected_ids_exist = True
                break

        if not collected_ids_exist and not overwrite:
            continue

        present = get_external_ids_of_author(pid)

        if overwrite:
            for ext_system_id in present.keys():
                for ext_id in present[ext_system_id]:
                    _remove_external_id_from_author(pid, ext_system_id, ext_id)
            present = dict()

        for ext_system_id in collected.keys():
            for ext_id in collected[ext_system_id]:
                if ext_system_id not in present or ext_id not in present[ext_system_id]:
                    _add_external_id_to_author(pid, ext_system_id, ext_id)

    if force_cache_tables:
        destroy_partial_marc_caches()

    logger.update_status_final("Updating external ids finished.")


def _select_from_aidpersonidpapers_where(
    select=None,
    pid=None,
    table=None,
    ref=None,
    rec=None,
    name=None,
    flag=None,
        lcul=None):
    '''
    Selects the given fields from the records of aidPERSONIDPAPERS table
    with the specified attributes. If no parameters are given it returns all
    records.

    @param select: fields to select
    @type select: list [str,]
    @param pid: author identifier
    @type pid: int
    @param table: bibref_table
    @type table: int
    @param ref: bibref_value
    @type ref: int
    @param rec: paper identifier
    @type rec: int
    @param name: author name
    @type name: str
    @param flag: author-paper association status
    @type flag: int
    @param lcul: lcul
    @type lcul: int

    @return: given fields of the records with the specified attributes
    @rtype: tuple
    '''
    if not select:
        return None

    conditions = list()
    add_condition = conditions.append
    args = list()
    add_arg = args.append

    add_condition('True')
    if pid is not None:
        add_condition('personid=%s')
        add_arg(pid)
    if table is not None:
        add_condition("bibref_table like %s")
        add_arg(str(table))
    if ref is not None:
        add_condition('bibref_value=%s')
        add_arg(ref)
    if rec is not None:
        add_condition('bibrec=%s')
        add_arg(rec)
    if name is not None:
        add_condition('name=%s')
        add_arg(name)
    if flag is not None:
        add_condition('flag=%s')
        add_arg(flag)
    if lcul is not None:
        add_condition('lcul=%s')
        add_arg(lcul)

    select_fields_str = ", ".join(select)
    conditions_str = " and ".join(conditions)
    query = ('select %s '
             'from aidPERSONIDPAPERS '
             'where %s') % (select_fields_str, conditions_str)

    return run_sql(query, tuple(args))

#
#
# aidPERSONIDDATA table                                  ###
#
#

# ********** setters **********#


def add_author_data(pid, tag, value, opt1=None, opt2=None, opt3=None):  # set_personid_row
    '''
    Adds data under the specified tag for the given author.

    @param pid: author identifier
    @type pid: int
    @param tag: data tag
    @type tag: str
    @param value: data tag value
    @type value: str
    @param opt1: opt1
    @type opt1: int
    @param opt2: opt2
    @type opt2: int
    @param opt3: opt3
    @type opt3: str
    '''
    run_sql('insert into aidPERSONIDDATA (`personid`, `tag`, `data`, `opt1`, `opt2`, `opt3`) '
            'values (%s, %s, %s, %s, %s, %s)', (pid, tag, value, opt1, opt2, opt3))


def remove_author_data(tag, pid=None, value=None):  # del_personid_row
    '''
    Deletes the data associated with the given tag. If 'pid' or 'value' are
    specified the deletion is respectively restrained.

    @param tag: data tag
    @type tag: str
    @param pid: author identifier
    @type pid: int
    @param value: data tag value
    @type value: str
    '''
    if pid:
        if value:
            _delete_from_aidpersoniddata_where(pid=pid, tag=tag, data=value)
        else:
            _delete_from_aidpersoniddata_where(pid=pid, tag=tag)
    else:
        if value:
            _delete_from_aidpersoniddata_where(tag=tag, data=value)
        else:
            _delete_from_aidpersoniddata_where(tag=tag)


def transfer_data_to_author(data, new_pid):
    '''

    @param papers_data:
    @type papers_data: list
    @param new_pid: new author identifier
    @type new_pid: int
    '''
    for pid, tag in data:
        run_sql('update aidPERSONIDDATA '
                'set personid=%s '
                'where personid=%s '
                'and tag=%s', (new_pid, pid, tag))


def add_orcid_id_to_author(pid, orcid_id):
    '''
    Adds the external identifier for ORCID system to the given author.

    @param pid: author identifier
    @type pid: int
    @param orcid_id: ORCID external identifier
    @type orcid_id: str
    '''
    _add_external_id_to_author(pid, 'ORCID', orcid_id)


def webuser_merge_user(old_uid, new_uid):
    pid = run_sql("select personid from aidPERSONIDDATA where tag='uid' and data=%s", (old_uid,))
    if pid:
        add_userid_to_author(pid[0][0], new_uid)


def add_userid_to_author(pid, uid):
    """
    Connects a userid to an author. If a userid is already present on that person, it gets flagged as old and
    the new one will replace it. If another person has the same userid, it gets stolen.
    """
    run_sql("update aidPERSONIDDATA set tag='uid_old' where tag='uid' and personid=%s", (pid,))

    pid_is_present = run_sql("select personid from aidPERSONIDDATA where tag='uid' and data=%s", (uid,))
    if not pid_is_present:
        run_sql("insert into aidPERSONIDDATA (personid, tag, data) values (%s, 'uid', %s)", (pid, uid))
    else:
        run_sql(
            "update aidPERSONIDDATA set personid=%s where personid=%s and tag='uid' and data=%s",
            (pid,
             pid_is_present[0][0],
             uid))


def add_arxiv_papers_to_author(arxiv_papers, pid):
    '''
    Adds the arxiv papers list for the specified author. If one already exists
    it compares them and in case they are different it updates it.

    @param arxiv_papers: arxiv paper identifiers
    @type arxiv_papers: list [str,]
    @param pid: author identifier
    @type pid: int
    '''
    old_arxiv_papers = get_arxiv_papers_of_author(pid)
    if old_arxiv_papers and set(old_arxiv_papers) == set(arxiv_papers):
        return

    remove_arxiv_papers_of_author(pid)

    arxiv_papers = serialize(arxiv_papers)

    run_sql('insert into aidPERSONIDDATA (`personid`, `tag`, `datablob`) '
            'values (%s, %s, %s)', (pid, 'arxiv_papers', arxiv_papers))


def remove_arxiv_papers_of_author(pid):
    '''
    Deletes the arxiv papers list of the specified author.

    @param pid: author identifier
    @type pid: int
    '''
    run_sql('delete from aidPERSONIDDATA '
            'where tag=%s and personid=%s', ('arxiv_papers', pid))


def _add_external_id_to_author(pid, ext_sys, ext_id):  # add_personID_external_id
    '''
    Adds the external identifier of the specified system to the given author.

    @param pid: author identifier
    @type pid: int
    @param ext_sys: external system
    @type ext_sys: str
    @param ext_id: external identifier
    @type ext_id: str
    '''
    run_sql('insert into aidPERSONIDDATA (personid, tag, data) '
            'values (%s, %s, %s)', (pid, 'extid:%s' % ext_sys, ext_id))


def _remove_external_id_from_author(pid, ext_sys, ext_id=None):  # remove_personID_external_id
    '''
    Removes all identifiers of the specified external system from the given
    author. If 'ext_id' is specified it removes the specific one.

    @param pid: author identifier
    @type pid: int
    @param ext_sys: external system
    @type ext_sys: str
    @param ext_id: external identifier
    @type ext_id: str
    '''
    if ext_id is None:
        _delete_from_aidpersoniddata_where(pid=pid, tag='extid:%s' % ext_sys)
    else:
        _delete_from_aidpersoniddata_where(pid=pid, tag='extid:%s' % ext_sys, data=ext_id)


def update_request_ticket_for_author(pid, ticket_dict, tid=None):  # update_request_ticket
    '''
    Creates/updates a request ticket for the given author with the specified
    ticket 'image'.

    @param pid: author identifier
    @type pid: int
    @param tag_value: ticket 'image' (e.g. (('paper', '700:316,10'),))
    @type tag_value: tuple ((str, str),)
    @param tid: ticket identifier
    @type tid: int
    '''
    request_tickets = get_request_tickets_for_author(pid)
    request_tickets_exist = bool(request_tickets)

    if tid is None:
        existing_tids = [0]
        for request_ticket in request_tickets:
            existing_tids.append(request_ticket['tid'])
        tid = max(existing_tids) + 1

        new_request_ticket = {'tid': tid}
        for tag, value in ticket_dict.iteritems():
            new_request_ticket[tag] = value
        request_tickets.append(new_request_ticket)
    else:
        for request_ticket in request_tickets:
            if request_ticket['tid'] == tid:
                for tag, value in ticket_dict.iteritems():
                    request_ticket[tag] = value
                break

    for request_ticket in list(request_tickets):
        if 'operations' not in request_ticket or not request_ticket['operations']:
            request_tickets.remove(request_ticket)

    request_tickets_num = len(request_tickets)
    request_tickets = serialize(request_tickets)

    if request_tickets_exist:
        remove_request_ticket_for_author(pid)

    run_sql("""insert into aidPERSONIDDATA
               (personid, tag, datablob, opt1)
               values (%s, %s, %s, %s)""",
           (pid, 'request_tickets', request_tickets, request_tickets_num))


def remove_request_ticket_for_author(pid, tid=None):  # delete_request_ticket
    '''
    Removes a request ticket from the given author. If ticket identifier is not
    specified it removes all the pending tickets for the given author.

    @param pid: author identifier
    @type pid: int
    @param tid: ticket identifier
    @type tid: int
    '''
    def remove_all_request_tickets_for_author(pid):
        run_sql("""delete from aidPERSONIDDATA
                   where personid=%s
                   and tag=%s""",
               (pid, 'request_tickets'))

    if tid is None:
        remove_all_request_tickets_for_author(pid)
        return

    request_tickets = get_request_tickets_for_author(pid)
    if not request_tickets:
        return

    for request_ticket in list(request_tickets):
        if request_ticket['tid'] == tid:
            request_tickets.remove(request_ticket)
            break

    remove_all_request_tickets_for_author(pid)

    if not request_tickets:
        return

    request_tickets_num = len(request_tickets)
    request_tickets = serialize(request_tickets)

    run_sql("""insert into aidPERSONIDDATA
               (personid, tag, datablob, opt1)
               values (%s, %s, %s, %s)""",
           (pid, 'request_tickets', request_tickets, request_tickets_num))


def modify_canonical_name_of_authors(pids_newcnames=None):  # change_personID_canonical_names
    '''
    Updates the existing canonical name of the given authors.

    @param pids_newcnames: author - new canonical name pairs [(personid, new_canonical_name),]
    @type pids_newcnames: list [(int, str),]
    '''
    for idx, pid_newcname in enumerate(pids_newcnames):

        pid, newcname = pid_newcname
        logger.update_status(float(idx) / float(len(pids_newcnames)), "Changing canonical names...")

        # delete the existing canonical name of the current author and the
        # current holder of the new canonical name
        run_sql("""delete from aidPERSONIDDATA
                   where tag=%s
                   and (personid=%s or data=%s)""",
               ('canonical_name', pid, newcname))

        run_sql("""insert into aidPERSONIDDATA
                   (personid, tag, data)
                   values (%s, %s, %s)""",
               (pid, 'canonical_name', newcname))

    logger.update_status_final("Changing canonical names finished.")


def _delete_from_aidpersoniddata_where(pid=None, tag=None, data=None, opt1=None, opt2=None, opt3=None):
    '''
    Deletes the records from aidPERSONIDDATA with the given attributes. If no
    parameters are given it deletes all records.

    @param pid: author identifier
    @type pid: int
    @param tag: data tag
    @type tag: str
    @param data: data tag value
    @type data: str
    @param opt1: opt1
    @type opt1: int
    @param opt2: opt2
    @type opt2: int
    @param opt3: opt3
    @type opt3: str
    '''
    conditions = list()
    add_condition = conditions.append
    args = list()
    add_arg = args.append

    if pid is not None:
        add_condition('personid=%s')
        add_arg(pid)
    if tag is not None:
        add_condition('tag=%s')
        add_arg(str(tag))
    if data is not None:
        add_condition('data=%s')
        add_arg(data)
    if opt1 is not None:
        add_condition('opt1=%s')
        add_arg(opt1)
    if opt2 is not None:
        add_condition('opt2=%s')
        add_arg(opt2)
    if opt3 is not None:
        add_condition('opt3=%s')
        add_arg(opt3)

    if not conditions:
        return

    conditions_str = " and ".join(conditions)
    query = ('delete from aidPERSONIDDATA '
             'where %s') % conditions_str

    run_sql(query, tuple(args))


# ********** getters **********#

def get_all_author_data_of_author(pid):
    '''
    @param pid: author identifier
    @type pid: int

    @return: records ((data, opt1, opt2, opt3, tag),)
    @rtype: tuple ((str, int, int, str, str),)
    '''
    return _select_from_aidpersoniddata_where(select=['personid', 'tag'], pid=pid)


def get_author_data(pid, tag):  # get_personid_row
    '''
    Gets all the records associated to the specified author and tag.

    @param pid: author identifier
    @type pid: int
    @param tag: data tag
    @type tag: str

    @return: records ((data, opt1, opt2, opt3, tag),)
    @rtype: tuple ((str, int, int, str, str),)
    '''
    return _select_from_aidpersoniddata_where(select=['data', 'opt1', 'opt2', 'opt3', 'tag'], pid=pid, tag=tag)


def get_canonical_name_of_author(pid):  # get_canonical_id_from_personid - get_canonical_names_by_pid
    '''
    Gets the canonical name of the given author.

    @param pid: author identifier
    @type pid: int

    @return: canonical name
    @rtype: tuple ((str),)
    '''
    return _select_from_aidpersoniddata_where(select=['data'], pid=pid, tag='canonical_name')


def get_pid_to_canonical_name_map():
    """
    Generate a dictionary which maps person ids to canonical names
    """
    values = run_sql("select personid, data from aidPERSONIDDATA where tag='canonical_name'")
    return dict(values)


def get_uid_of_author(pid):  # get_uid_from_personid
    '''
    Gets the user identifier associated with the specified author otherwise
    None.

    @param pid: author identifier
    @type pid: int

    @return: user identifier
    @rtype: str
    '''
    uid = _select_from_aidpersoniddata_where(select=['data'], tag='uid', pid=pid)

    if uid:
        return uid[0][0]

    return None


def get_external_ids_of_author(pid):  # get_personiID_external_ids
    '''
    Gets a mapping which associates an external system (e.g. Inspire) with the
    identifiers that the given author carries in that system.

    @param pid: author identifier
    @type pid: int

    @return: mapping {ext_system: [ext_id,]}
    @rtype: dict {str: [str,]}
    '''
    tags_extids = run_sql("""select tag, data
                             from aidPERSONIDDATA
                             where personid=%s
                             and tag like %s""",
                         (pid, 'extid:%%'))

    ext_ids = defaultdict(list)
    for tag, ext_id in tags_extids:
        ext_sys = tag.split(':')[1]
        ext_ids[ext_sys].append(ext_id)

    return ext_ids


def get_internal_user_id_of_author(pid):
    """
    Gets user id (current and eventual old ones) associated to an author.
    """
    old_ids = run_sql("select data from aidPERSONIDDATA where tag like 'uid_old' and personid=%s", (pid,))
    ids = get_user_id_of_author(pid)

    try:
        ids = int(ids[0][0])
    except IndexError:
        ids = None

    try:
        old_ids = [x[0] for x in old_ids]
    except IndexError:
        old_ids = list()

    return ids, old_ids


def get_arxiv_papers_of_author(pid):
    '''
    Gets the arxiv papers of the specified author. If no stored record is
    found, None is returned.

    @param pid: author identifier
    @type pid: int

    @return: arxiv paper identifiers
    @rtype: list [str,]
    '''
    arxiv_papers = run_sql("""select datablob
                              from aidPERSONIDDATA
                              where tag=%s
                              and personid=%s""",
                          ('arxiv_papers', pid))
    if not arxiv_papers:
        return None

    arxiv_papers = deserialize(arxiv_papers[0][0])

    return arxiv_papers


def get_request_tickets_for_author(pid, tid=None):  # get_request_ticket
    '''
    Gets the request tickets for the given author. If ticket identifier is
    specified it returns only that one.

    @param pid: author identifier
    @type pid: int
    @param tid: ticket identifier
    @type tid: int

    @returns: request tickets [[[(tag, value)], tid],]
    @rtype: list [[[(str, str)], int],]
    '''
    try:
        request_tickets = run_sql("""select datablob
                                     from aidPERSONIDDATA
                                     where personid=%s
                                     and tag=%s""",
                                 (pid, 'request_tickets'))

        request_tickets = list(deserialize(request_tickets[0][0]))
    except IndexError:
        return list()

    if tid is None:
        return request_tickets

    for request_ticket in request_tickets:
        if request_ticket['tid'] == tid:
            return [request_ticket]
    return list()


def get_authors_by_canonical_name_regexp(cname_regexp):  # get_personids_by_canonical_name
    '''
    Gets authors whose canonical name matches the regular expression pattern.

    @param cname_regexp: SQL regular expression
    @type cname_regexp: str

    @return: author identifiers and their canonical name ((pid, canonical_name),)
    @rtype: tuple ((int, str),)
    '''
    return run_sql("""select personid, data
                      from aidPERSONIDDATA
                      where tag=%s
                      and data like %s""",
                  ('canonical_name', cname_regexp))


def get_author_by_canonical_name(cname):  # get_person_id_from_canonical_id
    '''
    Gets the author who carries the given canonical name.

    @param cname: canonical name
    @type cname: str

    @return: author identifier ((pid),)
    @rtype: tuple ((int),)
    '''
    return _select_from_aidpersoniddata_where(select=['personid'], tag='canonical_name', data=cname)


def get_author_by_uid(uid):  # get_personid_from_uid
    '''
    Gets the author associated with the specified user identifier otherwise it
    returns None.

    @param uid: user identifier
    @type uid: int

    @return: author identifier
    @rtype: int
    '''
    pid = _select_from_aidpersoniddata_where(select=['personid'], tag='uid', data=str(uid))

    if not pid:
        return None

    return int(pid[0][0])


def get_author_by_external_id(ext_id, ext_sys=None):  # get_person_with_extid
    '''
    Gets the authors who carry the given external identifier. If 'ext_sys' is
    specified, it constraints the search only for that external system.

    @param ext_id: external identifier
    @type ext_id: str
    @param ext_sys: external system
    @type ext_sys: str

    @return: author identifiers set(pid,)
    @rtype: set set(int,)
    '''
    if ext_sys is None:
        pids = _select_from_aidpersoniddata_where(select=['personid'], data=ext_id)
    else:
        tag = 'extid:%s' % ext_sys
        pids = _select_from_aidpersoniddata_where(select=['personid'], data=ext_id, tag=tag)

    return set(pids)


def get_authors_with_open_tickets():  # get_persons_with_open_tickets_list
    '''
    Gets all the authors who have open tickets.

    @return: author identifiers and count of tickets ((personid, ticket_count),)
    @rtype: tuple ((int, int),)
    '''
    return run_sql("""select personid, opt1
                      from aidPERSONIDDATA
                      where tag=%s""",
                  ('request_tickets',))


def get_author_data_associations(table_name="`aidPERSONIDDATA`"):  # get_full_personid_data
    '''
    Gets all author-data associations (from aidPERSONIDDATA table or any other
    table with the same structure).

    @param table_name: name of the table with the author-data associations
    @type table_name: str

    @return: author-data associations ((pid, tag, data, opt1, opt2, opt3),)
    @rtype: tuple ((int, str, str, int, int, str),)
    '''
    return run_sql('select personid, tag, data, opt1, opt2, opt3 '
                   'from %s' % table_name)


def _get_inspire_id_of_author(pid):  # get_inspire_ids_by_pids
    '''
    Gets the external identifier of Inspire system for the given author.

    @param pid: author identifier
    @type pid: int

    @return: Inspire external identifier
    @rtype: tuple ((str),)
    '''
    return _select_from_aidpersoniddata_where(select=['data'], pid=pid, tag='extid:INSPIREID')


def get_orcid_id_of_author(pid):  # get_orcids_by_pids
    '''
    Gets the external identifier of ORCID system for the given author.

    @param pid: author identifier
    @type pid: int

    @return: ORCID external identifier
    @rtype: tuple ((str),)
    '''
    return _select_from_aidpersoniddata_where(select=['data'], pid=pid, tag='extid:ORCID')


def create_new_author_by_uid(uid=-1, uid_is_owner=False):  # create_new_person
    '''
    Creates a new author and associates him with the given user identifier. If
    the 'uid_is_owner' flag is enabled the author will hold the user identifier
    as owner, otherwise as creator.

    @param uid: user identifier
    @type uid: int
    @param uid_is_owner: the author will hold the user identifier as owner, otherwise as creator
    @type uid_is_owner: bool

    @return: author identifier
    @rtype: int
    '''
    pid_with_uid = _select_from_aidpersoniddata_where(select=['personid'], tag='uid', data=uid)

    if pid_with_uid and uid_is_owner:
        return pid_with_uid[0][0]

    pid = get_free_author_id()

    if uid_is_owner:
        add_author_data(pid, 'uid', str(uid))
    else:
        add_author_data(pid, 'user-created', str(uid))

    return pid


def user_can_modify_data_of_author(uid, pid):  # user_can_modify_data
    '''
    Examines if the specified user can modify data of the given author.

    @param uid: user identifier
    @type uid: int
    @param pid: author identifier
    @type pid: int

    @return: user can modify data
    @rtype: bool
    '''
    uid_of_author = _select_from_aidpersoniddata_where(select=['data'], tag='uid', pid=pid)

    rights = bconfig.CLAIMPAPER_CHANGE_OTHERS_DATA
    if uid_of_author and str(uid) == str(uid_of_author[0][0]):
        rights = bconfig.CLAIMPAPER_CHANGE_OWN_DATA

    return acc_authorize_action(uid, rights)[0] == 0


def _select_from_aidpersoniddata_where(select=None, pid=None, tag=None, data=None, opt1=None, opt2=None, opt3=None):
    '''
    Selects the given fields from the records of aidPERSONIDDATA table
    with the specified attributes. If no parameters are given it returns all
    records.

    @param select: fields to select
    @type select: list [str,]
    @param pid: author identifier
    @type pid: int
    @param tag: data tag
    @type tag: str
    @param data: data tag value
    @type data: str
    @param opt1: opt1
    @type opt1: int
    @param opt2: opt2
    @type opt2: int
    @param opt3: opt3
    @type opt3: str

    @return: given fields of the records with the specified attributes
    @rtype: tuple
    '''
    if not select:
        return None

    conditions = list()
    add_condition = conditions.append
    args = list()
    add_arg = args.append

    add_condition('True')
    if pid is not None:
        add_condition('personid=%s')
        add_arg(pid)
    if tag is not None:
        add_condition('tag=%s')
        add_arg(tag)
    if data is not None:
        add_condition('data=%s')
        add_arg(data)
    if opt1 is not None:
        add_condition('opt1=%s')
        add_arg(opt1)
    if opt2 is not None:
        add_condition('opt2=%s')
        add_arg(opt2)
    if opt3 is not None:
        add_condition('opt3=%s')
        add_arg(opt3)

    select_fields_str = ", ".join(select)
    conditions_str = " and ".join(conditions)
    query = """select %s
               from aidPERSONIDDATA
               where %s""" % (select_fields_str, conditions_str)

    return run_sql(query, tuple(args))

#
#
# both tables                                            ###
#
#

# ********** setters **********#


def empty_authors_exist(printer, repair=False):  # check_empty_personids
    '''
    It examines if there are empty authors (that is authors with no papers or
    other defined data) and deletes them if specified.

    @param printer: for log keeping
    @type printer: func
    @param repair: delete empty authors
    @type repair: bool

    @return: empty authors are found
    @rtype: bool
    '''
    empty_authors_found = False

    empty_pids = remove_empty_authors(remove=repair)
    if empty_pids:
        empty_authors_found = True

    for pid in empty_pids:
        printer("Personid %d has no papers and nothing else than canonical_name." % pid)

        if repair:
            printer("Deleting empty person %s." % pid)

    return empty_authors_found


def remove_empty_authors(remove=True):  # delete_empty_persons
    '''
    Gets all empty authors (that is authors with no papers or other defined
    data) and by default deletes all data associated with them, except if
    specified differently.

    @param remove: delete empty authors
    @type remove: bool

    @return: empty author identifiers set(pid,)
    @rtype: set set(int,)
    '''
    pids = run_sql("select distinct(personid) from aidPERSONIDPAPERS")
    pids_with_papers = set(pid[0] for pid in pids)
    pids_tags = _select_from_aidpersoniddata_where(select=['personid', 'tag'])
    pids_with_data = set(pid for pid, tag in pids_tags)
    not_empty_pids = set(pid for pid, tag in pids_tags if tag not in bconfig.NON_EMPTY_PERSON_TAGS)

    empty_pids = pids_with_data - (pids_with_papers | not_empty_pids)

    if empty_pids and remove:
        run_sql("""delete from aidPERSONIDDATA
                   where personid in %s"""
                % _get_sqlstr_from_set(empty_pids))

    return empty_pids


# bibauthorid_maintenance personid update private methods
def update_canonical_names_of_authors(pids=None, overwrite=False, suggested='', overwrite_not_claimed_only=False):  # update_personID_canonical_names
    '''
    Updates the canonical names for the given authors. If no authors are
    specified it does the updating for all authors. If 'overwrite' flag is
    enabled it updates even authors who carry a canonical name. If
    'overwrite_not_claimed_only' flag is enabled it updates only authors who do
    not have any claim.

    @param pids: author identifiers
    @type pids: list
    @param overwrite: update even authors who carry a canonical name
    @type overwrite: bool
    @param suggested: suggested canonical name
    @type suggested: str
    @param overwrite_not_claimed_only: update authors who do not have any claim
    @type overwrite_not_claimed_only: bool
    '''
    if pids is None:
        pids = set([pid[0] for pid in _select_from_aidpersonidpapers_where(select=['personid'])])

        if not overwrite:
            pids_with_cname = set([x[0]
                                  for x in _select_from_aidpersoniddata_where(select=['personid'], tag='canonical_name')])
            pids = pids - pids_with_cname

    for i, pid in enumerate(pids):
        logger.update_status(float(i) / float(len(pids)), "Updating canonical_names...")

        if overwrite_not_claimed_only:
            has_claims = bool(_select_from_aidpersonidpapers_where(select=['*'], pid=pid, flag=2))
            if has_claims:
                continue

        current_cname = _select_from_aidpersoniddata_where(select=['data'], pid=pid, tag='canonical_name')

        if overwrite or not current_cname:
            if current_cname:
                _delete_from_aidpersoniddata_where(pid=pid, tag='canonical_name')

            names_count = get_names_count_of_author(pid)
            names_count = sorted(names_count, key=itemgetter(1), reverse=True)

            if not names_count and not suggested:
                continue

            canonical_name = suggested
            if not suggested:
                canonical_name = create_canonical_name(names_count[0][0])

            taken_cnames = run_sql("""select data from aidPERSONIDDATA
                                      where tag=%s
                                      and data like %s""",
                                  ('canonical_name', canonical_name + '%'))
            taken_cnames = set([cname[0].lower() for cname in taken_cnames])

            for i in count(1):
                current_try = canonical_name + '.' + str(i)
                if current_try.lower() not in taken_cnames:
                    canonical_name = current_try
                    break

            run_sql("""insert into aidPERSONIDDATA
                       (personid, tag, data)
                       values (%s, %s, %s)""",
                   (pid, 'canonical_name', canonical_name))
    logger.update_status_final("Updating canonical_names finished.")

# ********** getters **********#


def get_free_author_ids():  # get_free_pids
    '''
    Gets unused author identifiers (it fills the holes).

    @return: free author identifiers
    @rtype: iterator (int, )
    '''
    all_pids = frozenset(pid[0] for pid in chain(
        _select_from_aidpersonidpapers_where(select=['personid']),
        _select_from_aidpersoniddata_where(select=['personid'])))

    return ifilter(lambda x: x not in all_pids, count(1))


def get_free_author_id():  # get_new_personid
    '''
    Gets a free author identifier.

    @return: free author identifier
    @rtype: int
    '''
    max_pids = [_select_from_aidpersonidpapers_where(select=['max(personid)']),
                _select_from_aidpersoniddata_where(select=['max(personid)'])]

    max_pids = tuple(int(pid[0][0]) for pid in max_pids if pid and pid[0][0])

    free_pid = 1
    if len(max_pids) == 2:
        free_pid = max(*max_pids) + 1
    elif len(max_pids) == 1:
        free_pid = max_pids[0] + 1

    return free_pid


def get_existing_authors(with_papers_only=False):  # get_existing_personids
    '''
    Gets existing authors (that is authors who are associated with a paper or
    withhold some other data). If 'with_papers_only' flag is enabled it gets
    only authors with papers.

    @param with_papers_only: only authors with papers
    @type with_papers_only: bool

    @return: author identifiers set(pid,)
    @rtype: set set(int,)
    '''
    pids_wih_data = set()
    if not with_papers_only:
        try:
            pids_wih_data = set(map(int, zip(*run_sql("select distinct personid from aidPERSONIDDATA"))[0]))
        except IndexError:
            pids_wih_data = set()

    try:
        pids_with_papers = set(map(int, zip(*run_sql("select distinct personid from aidPERSONIDPAPERS"))[0]))
    except IndexError:
        pids_with_papers = set()

    return pids_wih_data | pids_with_papers


def get_data_of_papers(recs, with_alt_names=False, with_all_author_papers=False):  # get_persons_from_recids
    '''
    Gets data for the specified papers. Helper for search engine indexing.

    For example: get_data_of_papers([1], True, True) returns
    ({1: [16591L]},
     {16591L: {'alternative_names': ['Wong, Yung Chow'],
               'canonical_id': 'Y.C.Wong.1',
               'person_records': [275304, 1, 51394, 128250, 311629]}})

    @param recs: paper identifiers
    @type recs: list
    @param with_alt_names: include alternative author names
    @type with_alt_names: bool
    @param with_all_author_papers: include all papers for each author
    @type with_all_author_papers: bool

    @return: data of the specified papers
    @rtype: tuple ({int: [int,]}, {int: {'str': str,}})
    '''
    paper_authors = dict()
    author_papers = dict()

    all_pids = set()

    for rec in recs:
        pids = run_sql("""select personid
                          from aidPERSONIDPAPERS
                          where bibrec=%s
                          and flag > -2""",
                      (rec,))

        pids = set(pid[0] for pid in pids)
        paper_authors[rec] = list(pids)
        all_pids |= pids

    for pid in all_pids:
        pid_data = dict()

        cname = _select_from_aidpersoniddata_where(select=['data'], pid=pid, tag='canonical_name')
        # We can suppose that this author didn't have a chance to get a canonical name yet
        # because it was not fully processed by it's creator. Anyway it's safer to try to
        # create one before failing miserably.
        if not cname:
            update_canonical_names_of_authors([pid])
        cname = _select_from_aidpersoniddata_where(select=['data'], pid=pid, tag='canonical_name')

        # assert len(canonical) == 1
        # This condition cannot hold in case claims or update daemons are run in parallel
        # with this, as it can happen that an author with papers exists and whose
        # canonical name has not been computed yet. Hence, it will be indexed next time,
        # so that it learns. Each author should have at most one canonical name, so:
        assert len(cname) <= 1, "A person cannot have more than one canonical name"

        if len(cname) == 1:
            pid_data = {'canonical_id': cname[0][0]}

        if with_alt_names:
            names = run_sql("""select name
                               from aidPERSONIDPAPERS
                               where personid=%s
                               and flag > -2""",
                           (pid,))
            names = set(name[0] for name in names)

            pid_data['alternative_names'] = list(names)

        if with_all_author_papers:
            recs = run_sql("""select bibrec
                              from aidPERSONIDPAPERS
                              where personid=%s
                              and flag > -2""",
                          (pid,))
            recs = set(rec[0] for rec in recs)

            pid_data['person_records'] = list(recs)

        author_papers[pid] = pid_data

    return (paper_authors, author_papers)


def impaired_canonical_names_exist(printer, repair=False):  # check_canonical_names
    '''
    It examines if there are authors who carry less or more than one canonical
    name and repairs them if specified.

    @param printer: for log keeping
    @type printer: func
    @param repair: fix authors with less/more than one canonical name
    @type repair: bool

    @return: authors with less/more than one canonical name exist
    @rtype: bool
    '''
    impaired_canonical_names_found = False

    authors_cnames = _select_from_aidpersoniddata_where(select=['personid', 'data'], tag='canonical_name')
    authors_cnames = sorted(authors_cnames, key=itemgetter(0))
    author_cnames_count = dict((pid, len(list(cnames))) for pid, cnames in groupby(authors_cnames, key=itemgetter(0)))

    to_update = list()

    for pid in get_existing_authors():
        cnames_count = author_cnames_count.get(pid, 0)

        if cnames_count != 1:
            if cnames_count == 0:
                papers_count = _select_from_aidpersonidpapers_where(select=['count(*)'], pid=pid)[0][0]
                if papers_count != 0:
                    impaired_canonical_names_found = True
                    printer("Personid %d does not have a canonical name, but has %d papers." % (pid, papers_count))
                    to_update.append(pid)
            else:
                impaired_canonical_names_found = True
                printer("Personid %d has %d canonical names.", (pid, cnames_count))
                to_update.append(pid)

    if repair and impaired_canonical_names_found:
        printer("Repairing canonical names for pids: %s" % str(to_update))
        update_canonical_names_of_authors(to_update, overwrite=True)

    return impaired_canonical_names_found


def user_can_modify_paper(uid, sig_str):
    '''
    Examines if the given user can modify the specified paper attribution. If
    the paper is assigned more then one time (from algorithms) consider the
    most privileged assignment.

    @param uid: user identifier
    @type: int
    @param sig_str: signature in a string form e.g. '100:7531,9024'
    @type sig_str: str

    @return: user can modify paper attribution
    @rtype: bool
    '''
    table, ref, rec = _split_signature_string(sig_str)

    pid_lcul = run_sql("""select personid, lcul
                          from aidPERSONIDPAPERS
                          where bibref_table like %s
                          and bibref_value=%s
                          and bibrec=%s
                          order by lcul
                          desc limit 0,1""",
                      (table, ref, rec))

    if not pid_lcul:
        return ((acc_authorize_action(uid, bconfig.CLAIMPAPER_CLAIM_OWN_PAPERS)[0] == 0) or
                (acc_authorize_action(uid, bconfig.CLAIMPAPER_CLAIM_OTHERS_PAPERS)[0] == 0))

    min_req_acc_n = int(pid_lcul[0][1])
    uid_of_author = run_sql("""select data
                               from aidPERSONIDDATA
                               where tag=%s
                               and personid=%s""",
                           ('uid', str(pid_lcul[0][0])))

    req_acc = get_paper_access_right(bconfig.CLAIMPAPER_CLAIM_OWN_PAPERS)
    if uid_of_author:
        if (str(uid_of_author[0][0]) != str(uid)) and min_req_acc_n > 0:
            req_acc = get_paper_access_right(bconfig.CLAIMPAPER_CLAIM_OTHERS_PAPERS)

    if min_req_acc_n < req_acc:
        min_req_acc_n = req_acc

    min_req_acc = get_paper_access_right(min_req_acc_n)

    return (acc_authorize_action(uid, min_req_acc)[0] == 0) and (get_paper_access_right(min_req_acc) >= min_req_acc_n)


#
#
# aidPERSONIDDATA or/and aidPERSONIDPAPERS table + some other table           ###
#
#

# ********** setters **********#

def back_up_author_paper_associations():  # copy_personids
    '''
    Copies/Backs-up the author-data and author-paper association tables
    (aidPERSONIDDATA, aidPERSONIDPAPERS) to the back-up tables
    (aidPERSONIDDATA_copy, aidPERSONIDPAPERS_copy) for later
    comparison/restoration.
    '''
    run_sql('drop table if exists `aidPERSONIDDATA_copy`')
    run_sql("""CREATE TABLE `aidPERSONIDDATA_copy` (
               `personid` BIGINT( 16 ) UNSIGNED NOT NULL ,
               `tag` VARCHAR( 64 ) NOT NULL ,
               `data` VARCHAR( 256 ) NULL DEFAULT NULL ,
               `datablob` LONGBLOB NULL DEFAULT NULL ,
               `opt1` MEDIUMINT( 8 ) NULL DEFAULT NULL ,
               `opt2` MEDIUMINT( 8 ) NULL DEFAULT NULL ,
               `opt3` VARCHAR( 256 ) NULL DEFAULT NULL ,
               `last_updated` TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ,
               INDEX `personid-b` (`personid`) ,
               INDEX `tag-b` (`tag`) ,
               INDEX `data-b` (`data`) ,
               INDEX `opt1` (`opt1`) ,
               INDEX `timestamp-b` ( `last_updated` )
               ) ENGINE = MYISAM  DEFAULT CHARSET = utf8""")
    run_sql("""insert into `aidPERSONIDDATA_copy`
               select *
               from `aidPERSONIDDATA`""")

    run_sql('drop table if exists `aidPERSONIDPAPERS_copy`')
    run_sql("""CREATE TABLE IF NOT EXISTS `aidPERSONIDPAPERS_copy` (
               `personid` BIGINT( 16 ) UNSIGNED NOT NULL ,
               `bibref_table` ENUM(  '100',  '700' ) NOT NULL ,
               `bibref_value` MEDIUMINT( 8 ) UNSIGNED NOT NULL ,
               `bibrec` MEDIUMINT( 8 ) UNSIGNED NOT NULL ,
               `name` VARCHAR( 256 ) NOT NULL ,
               `m_name` VARCHAR( 256 ) NOT NULL ,
               `flag` SMALLINT( 2 ) NOT NULL DEFAULT  '0' ,
               `lcul` SMALLINT( 2 ) NOT NULL DEFAULT  '0' ,
               `last_updated` TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ,
               INDEX `personid-b` (`personid`) ,
               INDEX `reftable-b` (`bibref_table`) ,
               INDEX `refvalue-b` (`bibref_value`) ,
               INDEX `rec-b` (`bibrec`) ,
               INDEX `name-b` (`name`) ,
               INDEX `pn-b` (`personid`, `name`) ,
               INDEX `timestamp-b` (`last_updated`) ,
               INDEX `flag-b` (`flag`) ,
               INDEX `personid-flag-b` (`personid`,`flag`),
               INDEX `ptvrf-b` (`personid`, `bibref_table`, `bibref_value`, `bibrec`, `flag`)
               ) ENGINE = MYISAM DEFAULT CHARSET = utf8""")
    run_sql("""insert into `aidPERSONIDPAPERS_copy`
               select *
               from `aidPERSONIDPAPERS""")

# ********** getters **********#


def get_papers_affected_since(since):  # personid_get_recids_affected_since
    '''
    Gets the set of papers which were manually changed after the specified
    timestamp.

    @param since: consider changes after the specified timestamp
    @type since: datetime.datetime

    @return: paper identifiers
    @rtype: list [int,]
    '''
    recs = set(_split_signature_string(sig[0])[2] for sig in run_sql("""select distinct value
                                                                       from aidUSERINPUTLOG
                                                                       where timestamp >= %s""",
              (since,)) if ',' in sig[0] and ':' in sig[0])

    pids = set(int(pid[0]) for pid in run_sql("""select distinct personid
                                                 from aidUSERINPUTLOG
                                                 where timestamp >= %s""",
              (since,)) if pid[0] > 0)

    if pids:
        pids_sqlstr = _get_sqlstr_from_set(pids)
        recs |= set(rec[0] for rec in run_sql("""select bibrec from aidPERSONIDPAPERS
                                                 where personid in %s"""
                                              % pids_sqlstr))

    return list(recs)


def get_papers_info_of_author(pid, flag,  # get_person_papers
                              show_author_name=False,
                              show_title=False,
                              show_rt_status=False,
                              show_affiliations=False,
                              show_date=False,
                              show_experiment=False):
    '''
    Gets information for the papers that the given author is associated with.
    The information which is included depends on the enabled flags.

    e.g. get_papers_info_of_author(16591, -2, True, True, True, True, True, True) returns
         [{'affiliation': ['Hong Kong U.'],
           'authorname': 'Wong, Yung Chow',
           'data': '100:1,1',
           'date': ('1961',),
           'experiment': [],
           'flag': 0,
           'rt_status': False,
           'title': ('Isoclinic N planes in Euclidean 2N space, Clifford parallels in elliptic (2N-1) space, and the Hurwitz matrix equations',) },
            ...]
    @param pid: author identifier
    @type pid: int
    @param flag: author-paper association status
    @type flag: int
    @param show_author_name: show author name for each paper
    @type show_author_name: bool
    @param show_title: show title of each paper
    @type show_title: bool
    @param show_rt_status: show if there are request tickets for the author
    @type show_rt_status: bool
    @param show_affiliations: show affiliations
    @type show_affiliations: bool
    @param show_date: show publication date
    @type show_date: bool
    @param show_experiment: show the experiment which the paper is associated with
    @type show_experiment: bool

    @return: information for each paper
    @rtype: list [{str: str, str: int, ...}]
    '''
    select = ['bibref_table', 'bibref_value', 'bibrec', 'flag']
    if show_author_name:
        select.append('name')

    select_fields_str = ", ".join(select)

    records = run_sql('select %s ' % select_fields_str +
                      'from aidPERSONIDPAPERS '
                      'where personid=%s '
                      'and flag >= %s', (pid, flag))

    def format_record(record):
        '''
        Gets information for the paper that the record is associated with.

        @param record: author-paper association record
        @type record: tuple

        @return: information for the paper
        @rtype: dict {str: str, str: int, ...}
        '''
        if show_author_name:
            table, ref, rec, flag, name = record
        else:
            table, ref, rec, flag = record

        sig_str = "%s:%d,%d" % (table, ref, rec)

        record_info = {'data': sig_str,
                       'flag': flag}

        recstruct = get_record(rec)

        if show_author_name:
            record_info['authorname'] = name

        if show_title:
            record_info['title'] = (record_get_field_value(recstruct, '245', '', '', 'a'),)

        if show_rt_status:
            record_info['rt_status'] = False

            for request_ticket in request_tickets:
                operations = request_ticket['operations']
                for action, bibrefrec in operations:
                    if bibrefrec == sig_str:
                        record_info['rt_status'] = True
                        break

        if show_affiliations:
            tag = '%s__u' % table
            record_info['affiliation'] = get_grouped_records((table, ref, rec), tag)[tag]

        if show_date:
            record_info['date'] = (record_get_field_value(recstruct, '269', '', '', 'c'),)

        if show_experiment:
            record_info['experiment'] = (record_get_field_value(recstruct, '693', '', '', 'e'),)

        return record_info

    request_tickets = get_request_tickets_for_author(pid)
    return [format_record(record) for record in records]


def get_names_of_author(pid, sort_by_count=True):  # get_person_db_names_count
    '''
    Gets the names associated to the given author and sorts them (by default)
    in descending order of name count.

    @param pid: author identifier
    @type pid: int
    @param sort_by_count: sort in descending order of name count
    @type sort_by_count: bool

    @return: author names and count of each name [(name, name_count),]
    @rtype: list [(str, int),]
    '''
    bibref = run_sql("""select bibref_table, bibref_value
                        from aidPERSONIDPAPERS
                        where personid=%s
                        and flag > -2""",
                    (pid,))

    bibref_values100 = [value for table, value in bibref if table == '100']
    bibref_values700 = [value for table, value in bibref if table == '700']

    bibref_values100_count = dict((key, len(list(data))) for key, data in groupby(sorted(bibref_values100)))
    bibref_values700_count = dict((key, len(list(data))) for key, data in groupby(sorted(bibref_values700)))

    ids_names100 = tuple()
    if bibref_values100:
        bibref_value100_sqlstr = _get_sqlstr_from_set(bibref_values100)
        ids_names100 = run_sql("""select id, value
                                  from bib10x
                                  where id in %s"""
                               % bibref_value100_sqlstr)

    ids_names700 = tuple()
    if bibref_values700:
        bibref_value700_sqlstr = _get_sqlstr_from_set(bibref_values700)
        ids_names700 = run_sql("""select id, value
                                  from bib70x
                                  where id in %s"""
                               % bibref_value700_sqlstr)

    names_count100 = [(name, bibref_values100_count[nid]) for nid, name in ids_names100]
    names_count700 = [(name, bibref_values700_count[nid]) for nid, name in ids_names700]

    names_count = names_count100 + names_count700

    if sort_by_count:
        names_count = sorted(names_count, key=itemgetter(1), reverse=True)

    return names_count


def merger_errors_exist():  # check_merger
    '''
    It examines if the merger introduced any error to the author-paper
    asociations (e.g. loss of claims/signatures, creation of new
    claims/signatures). It presumes that copy_personid was called before the
    merger.

    @return: merger errors are found
    @rtype: bool
    '''
    all_ok = True

    old_claims = set(run_sql("""select personid, bibref_table, bibref_value, bibrec, flag
                                from aidPERSONIDPAPERS_copy
                                where (flag=-2 or flag=2)"""))
    cur_claims = set(run_sql("""select personid, bibref_table, bibref_value, bibrec, flag
                                from aidPERSONIDPAPERS
                                where (flag=-2 or flag=2)"""))

    errors = ((old_claims - cur_claims, "Some claims were lost during the merge."),
              (cur_claims - old_claims, "Some new claims appeared after the merge."))
    action = {-2: 'Rejection', 2: 'Claim'}

    for claims, message in errors:
        if claims:
            all_ok = False
            logger.log(message)
            logger.log("".join("    %s: personid %d %d:%d,%d\n" %
                      (action[cl[4]], cl[0], int(cl[1]), cl[2], cl[3]) for cl in claims))

    old_sigs = set(run_sql("""select bibref_table, bibref_value, bibrec
                              from aidPERSONIDPAPERS_copy"""))
                              # where (flag <> -2 and flag <> 2)
    cur_sigs = set(run_sql("""select bibref_table, bibref_value, bibrec
                              from aidPERSONIDPAPERS"""))
                              # where (flag <> -2 and flag <> 2)

    errors = ((old_sigs - cur_sigs, "Some signatures were lost during the merge."),
              (cur_sigs - old_sigs, "Some new signatures appeared after the merge."))

    for sigs, message in errors:
        if sigs:
            all_ok = False
            logger.log(message)
            logger.log("".join("    %s:%d,%d\n" % sig for sig in sigs))

    return all_ok

#
#
# aidRESULTS table                                   ###
#
#

# ********** setters **********#


def save_cluster(named_cluster):
    '''
    Saves a cluster of papers (named after the author surname).

    @param named_cluster: named cluster of papers
    @type named_cluster: Cluster
    '''
    name, cluster = named_cluster
    for sig in cluster.bibs:
        table, ref, rec = sig
        run_sql("""insert into aidRESULTS
                   (personid, bibref_table, bibref_value, bibrec)
                   values (%s, %s, %s, %s)""",
               (name, str(table), ref, rec))


def remove_clusters_by_name(surname):  # remove_result_cluster
    '''
    Deletes all clusters which belong to authors who carry the specified
    surname.

    @param surname: author surname
    @type surname: str
    '''
    run_sql("""delete from aidRESULTS
               where personid like '%s.%%'"""
            % surname)


def empty_tortoise_results_table():  # empty_results_table
    '''
    Truncates the disambiguation algorithm results table.
    '''
    _truncate_table('aidRESULTS')

# ********** getters **********#


def get_clusters_by_surname(surname):  # get_lastname_results
    '''
    Gets all the disambiguation algorithm result records associated to the
    specified author surname.

    @param surname: author surname
    @type surname: str

    @return: disambiguation algorithm result records ((pid, bibref_table, bibref_value, bibrec),)
    @rtype: tuple ((str, str, int, int),)
    '''
    return run_sql("""select personid, bibref_table, bibref_value, bibrec
                      from aidRESULTS
                      where personid like %s""",
                  (surname + '.%',))


def get_cluster_names():  # get_existing_result_clusters
    '''
    Gets all cluster names.

    @return: cluster names
    @rtype: tuple ((str),)
    '''
    return set(run_sql("""select personid
                          from aidRESULTS"""))


def duplicated_tortoise_results_exist():  # check_results
    '''
    It examines if there are duplicated records in the disambiguation algorithm
    results (e.g. same signature assigned to two different authors or same
    paper assigned to same author more than once).

    @return: duplicated records in the disambiguation algorithm results exist
    @rtype: bool
    '''
    duplicated_tortoise_results_not_found = True

    disambiguation_results = run_sql("""select personid, bibref_table, bibref_value, bibrec
                                        from aidRESULTS""")
    keyfunc = lambda x: x[1:]
    disambiguation_results = sorted(disambiguation_results, key=keyfunc)
    duplicated_results = [list(sig_holders)
                          for _, sig_holders in groupby(disambiguation_results, key=keyfunc) if len(list(sig_holders)) > 1]

    for duplicates in duplicated_results:
        duplicated_tortoise_results_not_found = False
        for duplicate in duplicates:
            print "Duplicated row in aidRESULTS"
            print "%s %s %s %s" % duplicate
        print

    clusters = dict()
    for name, _, _, rec in disambiguation_results:
        clusters[name] = clusters.get(name, []) + [rec]

    faulty_clusters = dict((name, len(recs) - len(set(recs)))
                           for name, recs in clusters.items() if not len(recs) == len(set(recs)))

    if faulty_clusters:
        duplicated_tortoise_results_not_found = False
        print "Recids NOT unique in clusters!"
        print ("A total of %s clusters hold an average of %.2f duplicates" %
               (len(faulty_clusters), (sum(faulty_clusters.values()) / float(len(faulty_clusters)))))

        for name in faulty_clusters:
            print "Name: %-20s      Size: %4d      Faulty: %2d" % (name, len(clusters[name]), faulty_clusters[name])

    return duplicated_tortoise_results_not_found


#
#
# aidUSERINPUTLOG table                                    ###
#
#

# ********** setters **********#

def insert_user_log(userinfo, pid, action, tag, value, comment='', transactionid=0, timestamp=None, userid=0):
    '''
    Inserts the user log entry with the specified attributes.

    @param userinfo: user identifier and IP (e.g. 29||128.141.29.241)
    @type userinfo: str
    @param pid: author identifier
    @type pid: int
    @param action: action
    @type action: str
    @param tag: tag
    @type tag: str
    @param value: transaction value
    @type value: str
    @param comment: comment for the transaction
    @type comment: str
    @param transactionid: transaction identifier
    @type transactionid: int
    @param timestamp: entry timestamp
    @type timestamp: datetime.datetime
    @param userid: user identifier
    @type userid: int

    @return: transaction identifier
    @rtype: int
    '''
    if timestamp is None:
        run_sql("""insert into aidUSERINPUTLOG
                   (transactionid, timestamp, userinfo, userid, personid, action, tag, value, comment)
                   values (%s, now(), %s, %s, %s, %s, %s, %s, %s)""",
               (transactionid, userinfo, userid, pid, action, tag, value, comment))
    else:
        run_sql("""insert into aidUSERINPUTLOG
                   (transactionid, timestamp, userinfo, userid, personid, action, tag, value, comment)
                   values (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
               (transactionid, timestamp, userinfo, userid, pid, action, tag, value, comment))

    return transactionid

# ********** getters **********#


def get_user_logs(transactionid=None, userid=None, userinfo=None, pid=None, action=None, tag=None, value=None, comment=None, only_most_recent=False):  # get_user_log
    '''
    Gets the user log entries with the specified attributes. If no parameters
    are given it returns all log entries.

    @param transactionid: transaction identifier
    @type transactionid: int
    @param userid: user identifier
    @type userid: int
    @param userinfo: user identifier and IP (e.g. 29||128.141.29.241)
    @type userinfo: str
    @param pid: author identifier
    @type pid: int
    @param action: action
    @type action: str
    @param tag: tag
    @type tag: str
    @param value: transaction value
    @type value: str
    @param comment: comment for the transaction
    @type comment: str
    @param only_most_recent: only most recent log entry
    @type only_most_recent: bool

    @return: log entries ((id, transactionid, timestamp, userinfo, pid, action, tag, value, comment),)
    @rtype: tuple ((int, int, datetime.datetime, str, int, str, str, str, str),)
    '''
    conditions = list()
    add_condition = conditions.append
    args = list()
    add_arg = args.append

    if transactionid is not None:
        add_condition('transactionid=%s')
        add_arg(transactionid)
    if userid is not None:
        add_condition('userid=%s')
        add_arg(userid)
    if userinfo is not None:
        add_condition('userinfo=%s')
        add_arg(str(userinfo))
    if pid is not None:
        add_condition('pid=%s')
        add_arg(pid)
    if action is not None:
        add_condition('action=%s')
        add_arg(str(action))
    if tag is not None:
        add_condition('tag=%s')
        add_arg(str(tag))
    if value is not None:
        add_condition('value=%s')
        add_arg(str(value))
    if comment is not None:
        add_condition('comment=%s')
        add_arg(str(comment))

    conditions_str = " and ".join(conditions)
    query = """select id, transactionid, timestamp, userinfo, personid, action, tag, value, comment
               from aidUSERINPUTLOG
               where %s""" % (conditions_str)

    if only_most_recent:
        query += ' order by timestamp desc limit 0,1'

    return run_sql(query, tuple(args))


#
#
# other table                                      ###
#
#

# ********** setters **********#

def set_dense_index_ready():
    '''
    Sets the search engine dense index ready to use.
    '''
    run_sql("""insert into aidDENSEINDEX
               (flag)
               values (%s)""",
           (-1,))


def set_inverted_lists_ready():
    '''
    Sets the search engine inverted lists ready to use.
    '''
    run_sql("""insert into aidINVERTEDLISTS
               (qgram, inverted_list, list_cardinality)
               values (%s,%s,%s)""",
           ('!' * bconfig.QGRAM_LEN, '', 0))

# ********** getters **********#


def get_matching_bibrefs_for_paper(names, rec, always_match=False):  # get_possible_bibrecref
    '''
    Gets the bibrefs which match any of the surnames of the specified names and
    are associated with the given paper. If 'always_match' flag is enabled it
    gets all bibrefs associated to the given paper.

    @param names: author names
    @type names: list [str,]
    @param rec: paper identifier
    @type rec: int
    @param always_match: get all bibrefs associated to the given paper
    @type always_match: bool

    @return: bibrefs [[bibref_table:bibref_value, name],]
    @rtype: list [[str, str],]
    '''
    splitted_names = [split_name_parts(name) for name in names]

    bib10x_names = run_sql("""select o.id, o.value
                              from bib10x o, (select i.id_bibxxx as iid
                                              from bibrec_bib10x i
                                              where id_bibrec=%s) as dummy
                              where o.tag='100__a'
                              and o.id=dummy.iid""",
                          (rec,))
    bib70x_names = run_sql("""select o.id, o.value
                              from bib70x o, (select i.id_bibxxx as iid
                                              from bibrec_bib70x i
                                              where id_bibrec=%s) as dummy
                              where o.tag='700__a'
                              and o.id = dummy.iid""",
                          (rec,))

#    bib10x_names = run_sql("""select id, value
#                              from bib10x
#                              where tag='100__a'
#                              and id in (select id_bibxxx
#                                         from bibrec_bib10x
#                                         where id_bibrec=%s)""",
#                              (rec,) )
#    bib70x_names = run_sql("""select id, value
#                              from bib70x
#                              where tag='700__a'
#                              and id in (select id_bibxxx
#                                         from bibrec_bib70x
#                                         where id_bibrec=%s)""",
#                              (rec,) )
    bibrefs = list()

    for bib10x_id, bib10x_name in bib10x_names:
        splitted_names_bib10x = split_name_parts(bib10x_name)
        for n in splitted_names:
            if (n[0].lower() == splitted_names_bib10x[0].lower()) or always_match:
                bibref = ['100:' + str(bib10x_id), bib10x_name]
                if bibref not in bibrefs:
                    bibrefs.append(bibref)

    for bib70x_id, bib70x_name in bib70x_names:
        splitted_names_bib70x = split_name_parts(bib70x_name)
        for n in splitted_names:
            if (n[0].lower() == splitted_names_bib70x[0].lower()) or always_match:
                bibref = ['700:' + str(bib70x_id), bib70x_name]
                if bibref not in bibrefs:
                    bibrefs.append(bibref)

    return bibrefs


def get_collaborations_for_paper(rec):  # get_collaboration
    '''
    Gets the collaborations which the given paper is associated with.

    @param rec: paper identifier
    @type rec: int

    @return: collaborations
    @rtype: list [str,]
    '''
    bibxxx_ids = run_sql("""select id_bibxxx
                            from bibrec_bib71x
                            where id_bibrec=%s""",
                        (rec,))

    if not bibxxx_ids:
        return list()

    bibxxx_ids_sqlstr = _get_sqlstr_from_set(bibxxx_ids, lambda x: x[0])
    collaborations = run_sql("""select value
                                from bib71x
                                where id in %s
                                and tag like '%s'"""
                             % (bibxxx_ids_sqlstr, "710__g"))

    return [c[0] for c in collaborations]


def get_keywords_for_paper(rec):  # get_key_words
    '''
    Gets the keywords which the given paper is associated with.

    @param rec: paper identifier
    @type rec: int

    @return: keywords
    @rtype: list [str,]
    '''
    if bconfig.CFG_ADS_SITE:
        bibxxx_ids = run_sql("""select id_bibxxx
                                from bibrec_bib65x
                                where id_bibrec=%s""",
                            (rec,))
    else:
        bibxxx_ids = run_sql("""select id_bibxxx
                                from bibrec_bib69x
                                where id_bibrec=%s""",
                            (rec,))

    if not bibxxx_ids:
        return list()

    bibxxx_ids_sqlstr = _get_sqlstr_from_set(bibxxx_ids, lambda x: x[0])

    if bconfig.CFG_ADS_SITE:
        keywords = run_sql("""select value
                              from bib69x
                              where id in %s
                              and tag like '%s'"""
                           % (bibxxx_ids_sqlstr, "6531_a"))
    else:
        keywords = run_sql("""select value
                              from bib69x
                              where id in %s
                              and tag like '%s'"""
                           % (bibxxx_ids_sqlstr, "695__a"))

    return [k[0] for k in keywords]


def get_authors_of_paper(rec):  # get_all_authors
    '''
    Gets the authors (including the coauthors) whom the given paper is
    associated with.

    @param rec: paper identifier
    @type rec: int

    @return: author identifiers
    @rtype: list [int,]
    '''
    bibxxx10_ids = run_sql("""select id_bibxxx
                              from bibrec_bib10x
                              where id_bibrec=%s""",
                          (rec,))
    authors10 = tuple()
    if bibxxx10_ids:
        bibxxx10_ids_sqlstr = _get_sqlstr_from_set(bibxxx10_ids, lambda x: x[0])
        authors10 = run_sql("""select value
                               from bib10x
                               where tag='%s'
                               and id in %s"""
                            % ('100__a', bibxxx10_ids_sqlstr))

    bibxxx70_ids = run_sql("""select id_bibxxx
                              from bibrec_bib70x
                              where id_bibrec=%s""",
                          (rec,))
    authors70 = tuple()
    if bibxxx70_ids:
        bibxxx70_ids_sqlstr = _get_sqlstr_from_set(bibxxx70_ids, lambda x: x[0])
        authors70 = run_sql("""select value
                               from bib70x
                               where tag='%s'
                               and id in %s"""
                            % ('700__a', bibxxx70_ids_sqlstr))

    return [a[0] for a in chain(authors10, authors70)]


def get_title_of_paper(rec, recstruct=None):  # get_title_from_rec
    '''
    Gets the title which the specified paper carries.

    @param rec: paper identifier
    @type rec: int

    @return: title
    @rtype: str
    '''
    if not recstruct:
        try:
            title = get_fieldvalues([rec], '245__a')[0]
            return title
        except IndexError:
            return ""
    else:
        return record_get_field_value(recstruct, '245', '', '', 'a')


def _get_doi_for_paper(recid, recstruct=None):  # get_doi_from_rec
    '''
    Gets the doi which the specified paper is associated with.

    @param recid: paper identifier
    @type recid: int

    @return: doi (e.g. '10.1103/PhysRevD.1.1967')
    @rtype: str
    '''

    if not recstruct:
        recstruct = get_record(recid)

    inst = record_get_field_instances(recstruct, '024', '%')

    dois = list()
    for couple in inst:
        couple = dict(couple[0])
        try:
            if couple['2'].lower() == 'doi':
                dois.append(couple['a'])
        except:
            pass
    return dois


def get_modified_papers_since(since):  # get_recently_modified_record_ids
    '''
    Gets the papers which have modification date more recent than the specified
    one.

    @param since: consider only papers which are modified after this date
    @type since: datetime.datetime

    @return: paper identifiers
    @rtype: frozenset frozenset(int,)
    '''
    modified_recs = run_sql("""select id from bibrec
                               where modification_date >= %s""",
                           (since,))
    modified_recs = frozenset(rec[0] for rec in modified_recs)

    return modified_recs & frozenset(get_all_valid_bibrecs())


def get_modified_papers_before(recs, before):  # filter_modified_record_ids
    '''
    Gets the papers which have modification date older than the specified one
    from the given set of papers.

    @param recs: paper identifiers
    @type recs: list [(_, _, int),]
    @param before: consider only papers which are modified before this date
    @type before: datetime.datetime

    @return: paper identifiers
    @rtype: list [int,]
    '''
    if not recs:
        return list()
    recs_sqlstr = _get_sqlstr_from_set([rec[2] for rec in recs])
    modified_recs = run_sql("""select id from bibrec
                               where id in %s
                               and modification_date < '%s'"""
                            % (recs_sqlstr, before))
    modified_recs = [rec[0] for rec in modified_recs]
    modified_recs = [rec for rec in recs if rec[2] in modified_recs]

    return modified_recs


def _get_author_refs_from_db_of_paper(rec):  # _get_authors_from_paper_from_db
    '''
    Gets all author refs for the specified paper.

    @param rec: paper identifier
    @type rec: int

    @return: author refs
    @rtype: tuple ((int),)
    '''
    ref_ids100 = run_sql("""select id_bibxxx
                            from bibrec_bib10x
                            where id_bibrec=%s""",
                        (rec,))
    if not ref_ids100:
        return tuple()

    ref_ids100_sqlstr = _get_sqlstr_from_set(ref_ids100, lambda x: x[0])
    return run_sql("""select id from bib10x
                      where tag='100__a'
                      and id in %s"""
                   % ref_ids100_sqlstr)


def _get_coauthor_refs_from_db_of_paper(rec):  # _get_coauthors_from_paper_from_db
    '''
    @param rec: paper identifier
    @type rec: int

    @return: coauthor refs
    @rtype: tuple ((int),)
    '''
    ref_ids700 = run_sql("""select id_bibxxx
                         from bibrec_bib70x
                         where id_bibrec=%s""",
                         (rec,))
    if not ref_ids700:
        return tuple()

    ref_ids700_sqlstr = _get_sqlstr_from_set(ref_ids700, lambda x: x[0])
    return run_sql("""select id
                      from bib70x
                      where tag='700__a'
                      and id in %s"""
                   % ref_ids700_sqlstr)


def get_bib10x():
    '''
    Gets all existing author name identifiers and according values.

    @return: name identifiers and according values
    @rtype: tuple ((int, str),)
    '''
    return run_sql("""select id, value
                      from bib10x
                      where tag like %s""",
                  ("100__a",))


def get_bib70x():
    '''
    Gets all existing coauthor name identifiers and according values.

    @return: name identifiers and according values
    @rtype: tuple ((int, str),)
    '''
    return run_sql("""select id, value
                      from bib70x
                      where tag like %s""",
                  ("700__a",))


def get_user_id_by_email(email):
    '''
    Gets the user identifier associated with the given email.

    @param email: email
    @type email: str

    @return: user identifier
    @rtype: int
    '''
    try:
        uid = run_sql("""select id
                         from user
                         where email=%s""", (email,))[0][0]
    except IndexError:
        uid = None

    return uid


def get_name_variants_for_authors(authors):  # get_indexable_name_personids
    '''
    Gets the real author name and the author identifiers (which carry that
    name) associated to each of the specified indexable name identifiers.

    @param name_ids: indexable name identifiers
    @type name_ids: list [int,]

    @return: real author name and the author identifiers which carry that name ((name, pids),)
    @rtype: tuple ((str, bytes),)
    '''
    name_variants = run_sql("""select id, personids
                               from aidDENSEINDEX
                               where id in %s
                               and flag=1"""
                            % _get_sqlstr_from_set(authors))
    authors = list()
    author_to_name_variants_mapping = dict()
    for author, names in name_variants:
        authors.append(author)
        author_to_name_variants_mapping[author] = deserialize(names)

    assert len(authors) == len(set(authors))
    return author_to_name_variants_mapping


def get_author_groups_from_string_ids(indexable_name_ids):  # get_indexable_name_personids
    '''
    Gets the real author name and the author identifiers (which carry that
    name) associated to each of the specified indexable name identifiers.

    @param name_ids: indexable name identifiers
    @type name_ids: list [int,]

    @return: real author name and the author identifiers which carry that name ((name, pids),)
    @rtype: tuple ((str, bytes),)
    '''
    return run_sql("""select personids
                      from aidDENSEINDEX
                      where id in %s
                      and flag=0"""
                   % _get_sqlstr_from_set(indexable_name_ids))


def get_indexed_strings(string_ids):  # get_indexable_name_personids
    '''
    Gets the real author name and the author identifiers (which carry that
    name) associated to each of the specified indexable name identifiers.

    @param name_ids: indexable name identifiers
    @type name_ids: list [int,]

    @return: real author name and the author identifiers which carry that name ((name, pids),)
    @rtype: tuple ((str, bytes),)
    '''
    strings = run_sql("""select id, indexable_string, indexable_surname
                         from aidDENSEINDEX
                         where id in %s
                         and flag=0"""
                      % (_get_sqlstr_from_set(string_ids),))

    strings_to_ids_mapping = dict()
    for sid, string, surname in strings:
        strings_to_ids_mapping[string] = {'sid': sid, 'surname': surname}

    return strings_to_ids_mapping


def _get_grouped_records_from_db(sig, *args):
    '''
    Gets the records from bibmarcx table which are grouped together with the
    paper specified in the given signature and carry a tag from 'args'.

    @param sig: signature (bibref_table, bibref_value, bibrec)
    @type sig: tuple (str, str, str)
    @param args: tags
    @type args: tuple (str,)

    @return: {tag: [extracted_value,]}
    @rtype: dict {str: [str,]}
    '''
    table, ref, rec = sig

    target_table = "bib%sx" % (str(table)[:-1])
    mapping_table = "bibrec_%s" % target_table

    group_id = run_sql("""select field_number
                          from %s
                          where id_bibrec=%s
                          and id_bibxxx=%s"""
                       % (mapping_table, rec, ref))

    if not group_id:
        # the mapping is not found
        return dict((tag, list()) for tag in args)
    elif len(group_id) == 1:
        field_number = group_id[0][0]
    else:
        # ignore the error
        field_number = min(i[0] for i in group_id)

    grouped = run_sql("""select id_bibxxx
                         from %s
                         where id_bibrec=%s
                         and field_number=%s"""
                      % (mapping_table, rec, field_number))

    assert len(grouped) > 0, "There should be at most one grouped value per tag."

    grouped_sqlstr = _get_sqlstr_from_set(grouped, lambda x: str(x[0]))

    res = dict()
    for tag in args:
        values = run_sql("""select value
                            from %s
                            where tag like '%%%s%%'
                            and id in %s"""
                         % (target_table, tag, grouped_sqlstr))
        res[tag] = [value[0] for value in values]

    return res


def get_signatures_from_bibrefs(bibrefs):
    '''
    Gets all valid signatures for the given bibrefs.

    @param bibrefs: bibrefs set((bibref_table, bibref_value),)
    @type bibrefs: set set((int, int),)

    @return: signatures ((bibref_table, bibref_value, bibrec),)
    @rtype: iterator ((int, int, int),)
    '''
    sig10x = tuple()
    bib10x = filter(lambda x: x[0] == 100, bibrefs)
    if bib10x:
        bib10x_sqlstr = _get_sqlstr_from_set(bib10x, lambda x: x[1])
        sig10x = run_sql("""select 100, id_bibxxx, id_bibrec
                            from bibrec_bib10x
                            where id_bibxxx in %s"""
                         % bib10x_sqlstr)

    sig70x = tuple()
    bib70x = filter(lambda x: x[0] == 700, bibrefs)
    if bib70x:
        bib70x_sqlstr = _get_sqlstr_from_set(bib70x, lambda x: x[1])
        sig70x = run_sql("""select 700, id_bibxxx, id_bibrec
                            from bibrec_bib70x
                            where id_bibxxx in %s"""
                         % bib70x_sqlstr)

    valid_recs = set(get_all_valid_bibrecs())

    return filter(lambda x: x[2] in valid_recs, chain(set(sig10x), set(sig70x)))


def get_resolved_affiliation(ambiguous_aff):  # resolve_affiliation
    """
    This is a method available in the context of author disambiguation in ADS
    only. No other platform provides the table used by this function.

    @warning: to be used in an ADS context only

    @param ambiguous_aff_string: ambiguous affiliation
    @type ambiguous_aff_string: str

    @return: the normalized version of the affiliation
    @rtype: str
    """
    if not ambiguous_aff or not bconfig.CFG_ADS_SITE:
        return "None"

    aff_id = run_sql("""select aff_id
                        from ads_affiliations
                        where affstring=%s""",
                    (ambiguous_aff,))

    if not aff_id:
        return "None"

    return aff_id[0][0]


def _get_name_from_db_by_bibref(bibref):  # _get_name_by_bibrecref_from_db
    '''
    Gets the author name which is associated with the given bibref.

    @param bibref: bibref (bibref_table, bibref_value)
    @type bibref: tuple (int, int)

    @return: name
    @rtype: str
    '''
    table = "bib%sx" % str(bibref[0])[:-1]
    tag = "%s__a" % bibref[0]
    ref = bibref[1]

    query = """select value
               from %s
               where id=%s
               and tag='%s'""" % (table, ref, tag)

    name = run_sql(query)

    assert len(name) == 1, "A bibref must have exactly one name (%s)" % str(ref)

    return name[0][0]


def get_deleted_papers():
    '''
    Gets all deleted papers.

    @return: paper identifiers
    @rtype: tuple ((int),)
    '''
    return run_sql("""select o.id_bibrec
                      from bibrec_bib98x o, (select i.id as iid
                                             from bib98x i
                                             where value = 'DELETED'
                                             and tag like '980__a') as dummy
                      where o.id_bibxxx = dummy.iid""")


def get_inverted_lists(qgrams):
    '''
    Gets the inverted lists for the specified qgrams.

    @param qgrams: contiguous sequences of q chars
    @type qgrams: list [str,]

    @return: inverted lists and their cardinality
    @rtype: tuple ((bytes, int),)
    '''
    return run_sql("""select inverted_list, list_cardinality
                      from aidINVERTEDLISTS
                      where qgram in %s"""
                   % _get_sqlstr_from_set(qgrams, f=lambda x: "'%s'" % x))


def populate_partial_marc_caches(selected_bibrecs=None, verbose=True):
    '''
    Populates marc caches.
    '''
    global MARC_100_700_CACHE

    def br_dictionarize(maptable, md):
        gc.disable()
        maxiters = len(set(map(itemgetter(0), maptable)))
        for i, v in enumerate(groupby(maptable, itemgetter(0))):
            if i % 10000 == 0:
                logger.update_status(float(i) / maxiters, 'br_dictionarizing...')
            idx = defaultdict(list)
            fn = defaultdict(list)
            for _, k, z in v[1]:
                idx[k].append(z)
                fn[z].append(k)
            md[v[0]] = {'id': dict(idx), 'fn': dict(fn)}
        logger.update_status_final('br_dictionarizing done')
        gc.enable()
        return md

    def bib_dictionarize_in_batches(bibtable, bd):
        bd.update(((i[0], (i[1], i[2])) for i in bibtable))
        return bd

    def bib_dictionarize(bibtable):
        return dict((i[0], (i[1], i[2])) for i in bibtable)

    sl = 500

    logger.update_status(.0, 'Populating cache, 10x')

    if selected_bibrecs is None:
        bibrecs = list(set(x[0] for x in run_sql("select distinct(id_bibrec) from bibrec_bib10x")))
    else:
        bibrecs = selected_bibrecs

    # If there is nothing to cache, stop here
    if not bibrecs:
        return

    if MARC_100_700_CACHE:
        bibrecs = set(bibrecs) - MARC_100_700_CACHE['records']
        # we add to the cache only the missing records. If nothing is missing, go away.
        if not bibrecs:
            return
        MARC_100_700_CACHE['records'] |= set(bibrecs)
    else:
        MARC_100_700_CACHE = dict()
        MARC_100_700_CACHE['records'] = set(bibrecs)

    bibrecs = list(bibrecs)
    # bibrecs.sort()
    bibrecs = [bibrecs[x:x + sl] for x in range(0, len(bibrecs), sl)]

    if 'brb100' in MARC_100_700_CACHE:
        brd_b10x = MARC_100_700_CACHE['brb100']
    else:
        brd_b10x = dict()
    for i, bunch in enumerate(bibrecs):
        logger.update_status(float(i) / len(bibrecs), '10x population bunching...')
        bibrec_bib10x = run_sql("select id_bibrec, id_bibxxx, field_number"
                                " from bibrec_bib10x where id_bibrec in %s "
                                % _get_sqlstr_from_set(bunch))
        bibrec_bib10x = sorted(bibrec_bib10x, key=lambda x: x[0])
        brd_b10x = br_dictionarize(bibrec_bib10x, brd_b10x)
    del bibrec_bib10x

    logger.update_status(.25, 'Populating cache, 70x')

    if not selected_bibrecs:
        bibrecs = list(set(x[0] for x in run_sql("select distinct(id_bibrec) from bibrec_bib70x")))
        bibrecs = [bibrecs[x:x + sl] for x in range(0, len(bibrecs), sl)]

    if 'brb700' in MARC_100_700_CACHE:
        brd_b70x = MARC_100_700_CACHE['brb700']
    else:
        brd_b70x = dict()
    for i, bunch in enumerate(bibrecs):
        logger.update_status(float(i) / len(bibrecs), '70x population bunching...')
        bibrec_bib70x = run_sql("select id_bibrec, id_bibxxx, field_number"
                                " from bibrec_bib70x where id_bibrec in %s "
                                % _get_sqlstr_from_set(bunch))
        bibrec_bib70x = sorted(bibrec_bib70x, key=lambda x: x[0])
        brd_b70x = br_dictionarize(bibrec_bib70x, brd_b70x)
    del bibrec_bib70x

    logger.update_status(.5, 'Populating get_grouped_records_table_cache')

    if 'b100' in MARC_100_700_CACHE:
        bibd_10x = MARC_100_700_CACHE['b100']
    else:
        bibd_10x = dict()

    logger.update_status(.625, 'Populating get_grouped_records_table_cache')

    if selected_bibrecs:
        for i, bunch in enumerate(bibrecs):
            bib10x = (run_sql("select id, tag, value"
                              " from bib10x, bibrec_bib10x where id=id_bibxxx "
                              " and id_bibrec in %s" % _get_sqlstr_from_set(bunch)))
            bibd_10x = bib_dictionarize_in_batches(bib10x, bibd_10x)
    else:
        bib10x = (run_sql("select id, tag, value"
                          " from bib10x"))
        bibd_10x = bib_dictionarize(bib10x)
    del bib10x

    if 'b700' in MARC_100_700_CACHE:
        bibd_70x = MARC_100_700_CACHE['b700']
    else:
        bibd_70x = dict()

    logger.update_status(.75, 'Populating get_grouped_records_table_cache')

    if selected_bibrecs:
        for i, bunch in enumerate(bibrecs):
            bib70x = (run_sql("select id, tag, value"
                              " from bib70x, bibrec_bib70x where id=id_bibxxx"
                              " and id_bibrec in %s" % _get_sqlstr_from_set(bunch)))
            bibd_70x = bib_dictionarize_in_batches(bib70x, bibd_70x)
    else:
        bib70x = (run_sql("select id, tag, value"
                          " from bib70x"))
        bibd_70x = bib_dictionarize(bib70x)
    del bib70x

    logger.update_status_final('Finished populating get_grouped_records_table_cache')

    MARC_100_700_CACHE['brb100'] = brd_b10x
    MARC_100_700_CACHE['brb700'] = brd_b70x
    MARC_100_700_CACHE['b100'] = bibd_10x
    MARC_100_700_CACHE['b700'] = bibd_70x


def search_engine_is_operating():  # check_search_engine_status
    '''
    Examines if the bibauthorid search engine is operating.

    @return: bibauthorid search engine is operating
    @rtype: bool
    '''
    dense_index_exists = bool(run_sql("""select *
                                         from aidDENSEINDEX
                                         where flag=%s""",
                             (-1,)))
    inverted_lists_exists = bool(run_sql("""select *
                                            from aidINVERTEDLISTS
                                            where qgram=%s""",
                                ('!' * bconfig.QGRAM_LEN,)))

    if dense_index_exists and inverted_lists_exists:
        return True

    return False


def _truncate_table(table_name):
    '''
    Truncates the specified table.

    @param table_name: name of the table to truncate
    @type table_name: str
    '''
    run_sql('truncate %s' % table_name)


def flush_data_to_db(table_name, column_names, args):  # flush_data
    '''
    Flushes the given data in the specified table with the specified columns.

    @param table_name: name of the table
    @type table_name: str
    @param column_names: names of the columns
    @type column_names: list [str,]
    @param args: data to flush in the database
    @type args: list
    '''
    column_num = len(column_names)

    assert len(
        args) % column_num == 0, 'Trying to flush data in table %s. Wrong number of arguments passed.' % table_name

    values_sqlstr = "(%s)" % ", ".join(repeat("%s", column_num))
    multiple_values_sqlstr = ", ".join(repeat(values_sqlstr, len(args) / column_num))
    insert_query = 'insert into %s (%s) values %s' % (table_name, ", ".join(column_names), multiple_values_sqlstr)

    run_sql(insert_query, args)

#
#
# no table                                        ###
#
#


def create_new_author_by_signature(sig, name=None, m_name=None):  # new_person_from_signature
    '''
    Creates a new author and associates him with the given signature.

    @param sig: signature (bibref_table, bibref_value, bibrec)
    @type sig: tuple (int, int, int)
    @param name: author name
    @type name: str

    @return: author identifier
    @rtype: int
    '''
    pid = get_free_author_id()

    add_signature(sig, name, pid, m_name=m_name)

    return pid


def check_author_paper_associations(output_file=None):  # check_personid_papers
    '''
    It examines if there are records in aidPERSONIDPAPERS table which are in an
    impaired state. If 'output_file' is specified it writes the output in that
    file, otherwise in stdout.

    @param output_file: file to write output
    @type output_file: str

    @return: damaged records are found
    @rtype: bool
    '''
    if output_file:
        fp = open(output_file, "w")
        printer = lambda x: fp.write(x + '\n')
    else:
        printer = logger.log

    checkers = (wrong_names_exist,
                duplicated_conirmed_papers_exist,
                duplicated_confirmed_signatures_exist,
                impaired_rejections_exist,
                impaired_canonical_names_exist,
                empty_authors_exist
                # check_claim_inspireid_contradiction
                )
    # avoid writing f(a) or g(a), because one of the calls might be optimized
    return not any([check(printer) for check in checkers])


def repair_author_paper_associations(output_file=None):  # repair_personid
    '''
    It examines if there are records in aidPERSONIDPAPERS table which are in an
    impaired state and repairs them. If 'output_file' is specified it writes
    the output in that file, otherwise in stdout.

    @param output_file: file to write output
    @type output_file: str

    @return: damaged records are found even after the repairing
    @rtype: bool
    '''
    if output_file:
        fp = open(output_file, "w")
        printer = lambda x: fp.write(x + '\n')
    else:
        printer = logger.log

    checkers = (wrong_names_exist,
                duplicated_conirmed_papers_exist,
                duplicated_confirmed_signatures_exist,
                impaired_rejections_exist,
                impaired_canonical_names_exist,
                empty_authors_exist
                # check_claim_inspireid_contradiction
                )

    first_check = [check(printer) for check in checkers]
    repair_pass = [check(printer, repair=True) for check in checkers]
    last_check = [check(printer) for check in checkers]

    if any(first_check):
        assert any(repair_pass)
        assert not any(last_check)

    return not any(last_check)


def get_author_refs_of_paper(rec):  # get_authors_from_paper
    '''
    Gets all author refs for the specified paper.

    @param rec: paper identifier
    @type rec: int

    @return: author refs
    @rtype: list [(str),]
    '''
    if MARC_100_700_CACHE:
        return _get_author_refs_from_marc_caches_of_paper(rec)
    else:
        return _get_author_refs_from_db_of_paper(rec)


def _get_author_refs_from_marc_caches_of_paper(rec):  # _get_authors_from_paper_from_cache
    '''
    Gets all author refs for the specified paper (from marc caches).
    If author refs are not found in marc caches, the database is queried.

    @param rec: paper identifier
    @type rec: int

    @return: author refs
    @rtype: list [(str),]
    '''
    try:
        ids = MARC_100_700_CACHE['brb100'][rec]['id'].keys()
        refs = [i for i in ids if '100__a' in MARC_100_700_CACHE['b100'][i][0]]
    except KeyError:
        if rec in MARC_100_700_CACHE['records']:
            refs = tuple()
        else:
            refs = _get_author_refs_from_db_of_paper(rec)

    return tuple(zip(refs))


def get_coauthor_refs_of_paper(paper):  # get_coauthors_from_paper
    '''
    Gets all coauthor refs for the specified paper.

    @param rec: paper identifier
    @type rec: int

    @return: coauthor refs
    @rtype: list [(str),]
    '''
    if MARC_100_700_CACHE:
        return _get_coauthor_refs_from_marc_caches_of_paper(paper)
    else:
        return _get_coauthor_refs_from_db_of_paper(paper)


def _get_coauthor_refs_from_marc_caches_of_paper(rec):  # _get_coauthors_from_paper_from_cache
    '''
    Gets all coauthor refs for the specified paper (from marc caches).

    @param rec: paper identifier
    @type rec: int

    @return: coauthor refs
    @rtype: list [(str),]
    '''
    try:
        ids = MARC_100_700_CACHE['brb700'][rec]['id'].keys()
        refs = [i for i in ids if '700__a' in MARC_100_700_CACHE['b700'][i][0]]
    except KeyError:
        if rec in MARC_100_700_CACHE['records']:
            refs = tuple()
        else:
            refs = _get_coauthor_refs_from_db_of_paper(rec)
    return tuple(zip(refs))


def get_all_bibrefs_of_paper(rec):
    '''
    Gets all author and coauthor refs for the specified paper.

    @param rec: paper identifier
    @type rec: int

    @return: author and coauthor refs [(table, ref),]
@rtype: list [(int, str),]
    '''
    author_refs = [(100, x[0]) for x in get_author_refs_of_paper(rec)]
    coauthor_refs = [(700, x[0]) for x in get_coauthor_refs_of_paper(rec)]
    return author_refs + coauthor_refs


def get_all_signatures_of_paper(rec):
    '''
    Gets all existing signatures for the specified paper.

    @param rec: paper identifier
    @type rec: int

    @return: existing signatures {name: bibref}
    @rtype: dict {str: str}
    '''
    signatures = list()

    refs = get_all_bibrefs_of_paper(rec)
    for table, ref in refs:
        marc_tag = str(table) + '__a'
        sig = get_grouped_records((table, ref, rec), marc_tag)[marc_tag][0]
        bibref = str(table) + ':' + str(ref)
        signatures.append({"bibref": bibref, "sig": sig})

    return signatures


def _get_name_by_bibref_from_cache(ref):  # _get_name_by_bibrecref_from_cache
    '''
    Finds the author name from cache based on the given bibref.

    @param ref: bibref (bibref_table, bibref_value)
    @type ref: tuple (int, int)

    @return: name
    @rtype: str
    '''
    table = "b%s" % ref[0]
    refid = ref[1]
    tag = "%s__a" % ref[0]
    name = None

    try:
        if tag in MARC_100_700_CACHE[table][refid][0]:
            name = MARC_100_700_CACHE[table][refid][1]
    except (KeyError):
        name = _get_name_from_db_by_bibref(ref)

    return name


def get_inspire_id_of_signature(sig):  # get_inspire_id
    '''
    Gets the external identifier of Inspire system for the given signature.

    @param sig: signature (bibref_table, bibref_value, bibrec)
    @type sig: tuple (int, int, int)

    @return: Inspire external identifier
    @rtype: list [str]
    '''
    table, ref, rec = sig

    return get_grouped_records((str(table), ref, rec), str(table) + '__i').values()[0]


def get_orcid_id_of_signature(sig):
    '''
    Gets the external identifier of Inspire system for the given signature.

    @param sig: signature (bibref_table, bibref_value, bibrec)
    type sig: tuple (int, int, int)

    @return Orcid external identifier
    @rtype: list [str]
    '''

    return None


def get_author_names_from_db(pid):  # get_person_db_names_set
    '''
    Gets the set of names associated to the given author.

    @param pid: author identifier
    @type pid: int

    @return: author names
    @rtype: list [(str),]
    '''
    names = get_names_of_author(pid)

    if not names:
        return list()

    return zip(zip(*names)[0])


def get_all_valid_bibrecs():
    '''
    Gets all valid bibrecs.

    @return: paper identifiers
    @rtype: list [int,]
    '''
    return perform_request_search(c=bconfig.LIMIT_TO_COLLECTIONS, rg=0)


def get_name_by_bibref(ref):  # get_name_by_bibrecref
    '''
    Finds the author name based on the given bibref.

    @param ref: bibref (bibref_table, bibref_value)
    @type ref: tuple (int, int)

    @return: name
    @rtype: str
    '''
    if MARC_100_700_CACHE:
        return _get_name_by_bibref_from_cache(ref)
    else:
        return _get_name_from_db_by_bibref(ref)


def get_last_rabbit_runtime():  # fetch_bibauthorid_last_update
    '''
    Gets last runtime of rabbit.

    @return: last runtime of rabbit
    @rtype: datetime.datetime
    '''
    log = get_user_logs(userinfo='daemon', action='PID_UPDATE', only_most_recent=True)
    try:
        last_update = log[0][2]
    except IndexError:
        last_update = datetime.datetime(year=1, month=1, day=1)

    return last_update


def get_db_time():  # get_sql_time
    '''
    Gets the time according to the database.

    @return: db time
    @rtype: datetime.datetime
    '''
    return run_sql("select now()")[0][0]


def destroy_partial_marc_caches():
    '''
    Destroys marc caches.
    '''
    global MARC_100_700_CACHE
    MARC_100_700_CACHE = None


def _split_signature_string(sig_str):
    '''
    Splits a signature from a string form to its parts.

    @param sig_str: signature in a string form e.g. '100:7531,9024'
    @type sig_str: str

    @return: signature (bibref_table, bibref_value, bibrec)
    @rtype: tuple (int, int, int)
    '''
    bibref, rec = sig_str.split(",")
    rec = int(rec)
    table, ref = bibref.split(":")
    ref = int(ref)
    return (table, ref, rec)


def _get_sqlstr_from_set(items, f=lambda x: x):  # list_2_SQL_str
    """
    Creates a string from a set after transforming each item
    with a function.

    @param items: set of items
    @type items: X
    @param f: function to be applied to each item
    @type f: func (x->str)

    @return: "(f(x1), f(x2), ..., f(xn))" where x1,x2,...,xn elements of 'items'
    @rtype: str
    """
    strs = (str(f(x)) for x in items)
    return "(%s)" % ", ".join(strs)


def get_paper_access_right(acc):  # resolve_paper_access_right
    '''
    Given an access right key, resolves to the corresponding access right
    value. If asked for a wrong/not present key falls back to the minimum
    permission.

    @param acc: access right key
    @type acc: str or int

    @return: access right value
    @rtype: str or int
    '''
    access_dict = {bconfig.CLAIMPAPER_VIEW_PID_UNIVERSE: 0,
                   bconfig.CLAIMPAPER_CLAIM_OWN_PAPERS: 25,
                   bconfig.CLAIMPAPER_CLAIM_OTHERS_PAPERS: 50}

    if isinstance(acc, str):
        try:
            return access_dict[acc]
        except:
            return 0

    inverse_dict = dict([[v, k] for k, v in access_dict.items()])
    lower_accs = [a for a in inverse_dict.keys() if a <= acc]

    try:
        return inverse_dict[max(lower_accs)]
    except:
        return bconfig.CLAIMPAPER_VIEW_PID_UNIVERSE


def get_grouped_records(sig, *args):
    '''
    @param sig: signature (bibref_table, bibref_value, bibrec)
    @type sig: tuple (int, int, int)
    @param args: tags
    @type args: tuple (str,)
    '''
    if MARC_100_700_CACHE:
        return _get_grouped_records_using_marc_caches(sig, *args)
    else:
        return _get_grouped_records_from_db(sig, *args)


def _get_grouped_records_using_marc_caches(sig, *args):  # _get_grouped_records_using_caches
    '''
    Gets the records from marc caches which are grouped together with the paper
    specified in the given signature and carry a tag from 'args'.

    @param sig: signature (bibref_table, bibref_value, bibrec)
    @type sig: tuple (int, int, int)
    @param args: tags
    @type args: tuple (str,)

    @return: {tag: [extracted_value,]}
    @rtype: dict {str: [str,]}
    '''
    table, ref, rec = sig

    try:
        c = MARC_100_700_CACHE['brb%s' % str(table)][rec]
        fn = c['id'][ref]
    except KeyError:
        if rec in MARC_100_700_CACHE['records']:
            return dict()
        else:
            return _get_grouped_records_from_db(sig, *args)

    if not fn:  # or len(fn)>1
        # If len(fn) > 1 it's BAD: the same signature is at least twice on the same paper.
        # But after all, that's the mess we find in the database, so let's leave it there.
        return dict((tag, list()) for tag in args)

    ids = set(chain(*(c['fn'][i] for i in fn)))
    tuples = [MARC_100_700_CACHE['b%s' % str(table)][i] for i in ids]
    res = defaultdict(list)

    for t in tuples:
        present = [tag for tag in args if tag in t[0]]
        # assert len(present) <= 1

        if present:
            tag = present[0]
            res[tag].append(t[1])

    for tag in args:
        if tag not in res.keys():
            res[tag] = list()
    return dict(res)


def populate_table(table_name, column_names, values, empty_table_first=True):
    '''
    Populates the specified table which has the specified column names with the
    given list of values. If 'empty_table_first' flag is enabled it truncates
    the table before populating it.

    @param table_name: name of the table to populate
    @type table_name: str
    @param column_names: column names of the table
    @type column_names: list [str,]
    @param values: values to be inserted
    @type values: list
    @param empty_table_first: truncate the table before populating it
    @type empty_table_first: bool
    '''
    values_len = len(values)
    column_num = len(column_names)
    values_tuple_size = list()

    assert values_len % column_num == 0, 'Trying to populate table %s. Wrong number of arguments passed.' % table_name

    for i in range(int(values_len / column_num)):
        # it keeps the size for each tuple of values
        values_tuple_size.append(sum([len(str(i)) for i in values[i * column_num:i * column_num + column_num]]))

    if empty_table_first:
        _truncate_table(table_name)

    populate_table_with_limit(table_name, column_names, values, values_tuple_size)


def populate_table_with_limit(table_name, column_names, values, values_tuple_size,
                              max_insert_size=CFG_BIBAUTHORID_SEARCH_ENGINE_MAX_DATACHUNK_PER_INSERT_DB_QUERY):
    '''
    Populates the specified table which has the specified column names with the
    given list of values. It limits the datachunk size per single insert query
    according to the given threshold. Bigger threshold means better
    performance. Nevertheless if it is too big there is the risk that the mysql
    connection timeout will run out and connection with the db will be lost.

    @param table_name: name of the table to populate
    @type table_name: str
    @param column_names: column names of the table
    @type column_names: list [str,]
    @param values: values to be inserted
    @type values: list
    @param values_tuple_size: size of each tuple of values
    @type values_tuple_size: list [int,]
    @param max_insert_size: max datachunk size to be inserted to the table per single insert query
    @type max_insert_size: int
    '''
    column_num = len(column_names)
    summ = 0
    start = 0

    for i in range(len(values_tuple_size)):
        if summ + values_tuple_size[i] <= max_insert_size:
            summ += values_tuple_size[i]
            continue
        summ = values_tuple_size[i]
        flush_data_to_db(table_name, column_names, values[start:(i - 1) * column_num])
        start = (i - 1) * column_num

    flush_data_to_db(table_name, column_names, values[start:])

#
#
# other staff                                        ###
#
#


#
#
# not used functions                                        ###
#
#

def remove_not_claimed_papers_from_author(pid):  # del_person_not_manually_claimed_papers
    '''
    Deletes papers which have not been manually claimed or rejected
    from the given author.

    @param pid: author
    @type pid: int
    '''
    run_sql("""delete from aidPERSONIDPAPERS
               where (flag <> -2 and flag <> 2)
               and personid=%s""", (pid,) )


def remove_all_signatures_from_authors(pids):  # remove_personid_papers
    '''
    Deletes all signatures from the given authors.

    @param pids: authors
    @type pids: list [int,]
    '''
    if pids:
        pids_sqlstr = _get_sqlstr_from_set(pids)
        run_sql("""delete from aidPERSONIDPAPERS
                   where personid in %s"""
                % pids_sqlstr)


def get_authors_by_surname(surname):  # find_pids_by_name
    '''
    Gets all authors who carry records with the specified surname.

    @param surname: author surname
    @type surname: str

    @return: author identifier and name set((pid, name),)
    @rtype: set set((int, str),)
    '''
    return set(run_sql("""select personid, name
                          from aidPERSONIDPAPERS
                          where name like %s""",
              (surname + ',%',)))


# could be useful to optimize rabbit. Still unused and untested, Watch out!
def get_author_to_signatures_mapping():  # get_bibrecref_to_pid_dictuonary
    '''
    Gets a mapping which associates signatures with the set of authors who
    carry a record with that signature.

    @return: mapping
    @rtype: dict {(str, int, int): set(int,)}
    '''
    mapping = dict()
    authors_sigs = _select_from_aidpersonidpapers_where(select=['personid', 'bibref_table', 'bibref_value', 'bibrec'])

    for i in authors_sigs:
        mapping.setdefault(i[1:], set()).add(i[0])

    return mapping


def get_author_data_associations_for_author(pid):  # get_specific_personid_full_data
    '''
    Gets all author-data associations for the given author.

    @param pid: author identifier
    @type pid: int

    @return: author-data associations ((pid, tag, data, opt1, opt2, opt3),)
    @rtype: tuple ((int, str, str, int, int, str),)
    '''
    return _select_from_aidpersoniddata_where(select=['personid', 'tag', 'data', 'opt1', 'opt2', 'opt3'], pid=pid)


def get_user_id_of_author(pid):  # get_uids_by_pids
    '''
    Gets the user identifier for the given author.

    @param pid: author identifier
    @type pid: int

    @return: user identifier
    @rtype: tuple ((str),)
    '''
    return _select_from_aidpersoniddata_where(select=['data'], pid=pid, tag='uid')


def restore_author_paper_associations():  # restore_personids
    '''
    Restores the author-data and author-paper association tables
    (aidPERSONIDDATA, aidPERSONIDPAPERS) from the last saved copy of the
    back-up tables (aidPERSONIDDATA_copy, aidPERSONIDPAPERS_copy).
    '''
    _truncate_table('aidPERSONIDDATA')
    run_sql("""insert into `aidPERSONIDDATA`
               select *
               from `aidPERSONIDDATA_copy`""")

    _truncate_table('aidPERSONIDPAPERS')
    run_sql("""insert into `aidPERSONIDPAPERS`
               select *
               from `aidPERSONIDPAPERS_copy`""")


def check_claim_inspireid_contradiction():
    '''
    It examines if the merger introduced any error to the author-paper
    asociations (e.g. claimed papers are assigned to a differnt author,
    loss of signatures, creation of new signatures). It presumes that
    copy_personid was called before the merger.

    @return: merger errors are found
    @rtype: bool
    '''
    inspire_ids10x = run_sql("""select id
                                from bib10x
                                where tag='100__i'""")
    refs10x = set(i[0] for i in run_sql("""select id
                                           from bib10x
                                           where tag='100__a'"""))
    if inspire_ids10x:
        inspire_ids10x_sqlstr = _get_sqlstr_from_set(inspire_ids10x, lambda x: str(x[0]))

        inspire_ids10x = run_sql("""select id_bibxxx, id_bibrec, field_number
                                    from bibrec_bib10x
                                    where id_bibxxx in %s"""
                                 % inspire_ids10x_sqlstr)

        inspire_ids10x = ((row[0], [(ref, rec) for ref, rec in run_sql(
            """select id_bibxxx, id_bibrec
                                   from bibrec_bib10x
                                   where id_bibrec='%s'
                                   and field_number='%s'"""
                                    % row[1:])
                                    if ref in refs10x])
                          for row in inspire_ids10x)

    inspire_ids70x = run_sql("""select id
                                from bib70x
                                where tag='700__i'""")
    refs70x = set(i[0] for i in run_sql("""select id
                                           from bib70x
                                           where tag='700__a'"""))
    if inspire_ids70x:
        inspire_ids70x_sqlstr = _get_sqlstr_from_set(inspire_ids70x, lambda x: str(x[0]))

        inspire_ids70x = run_sql("""select id_bibxxx, id_bibrec, field_number
                                    from bibrec_bib70x
                                    where id_bibxxx in %s"""
                                 % inspire_ids70x_sqlstr)

        inspire_ids70x = ((row[0], [(ref, rec) for ref, rec in run_sql(
            """select id_bibxxx, id_bibrec
                                   from bibrec_bib70x
                                   where id_bibrec='%s'
                                   and field_number='%s'"""
                                    % (row[1:]))
                                    if ref in refs70x])
                          for row in inspire_ids70x)

    # [(iids, [bibs])]
    inspired = list(chain(((iid, list(set(('100',) + bib for bib in bibs))) for iid, bibs in inspire_ids10x),
                          ((iid, list(set(('700',) + bib for bib in bibs))) for iid, bibs in inspire_ids70x)))

    assert all(len(x[1]) == 1 for x in inspired)

    inspired = ((k, map(itemgetter(0), map(itemgetter(1), d)))
                for k, d in groupby(sorted(inspired, key=itemgetter(0)), key=itemgetter(0)))

    # [(inspireid, [bibs])]
    inspired = [([(run_sql("""select personid
                              from aidPERSONIDPAPERS
                              where bibref_table like %s
                              and bibref_value=%s
                              and bibrec=%s
                              and flag='2'""", bib), bib)
                  for bib in cluster[1]], cluster[0])
                for cluster in inspired]

    # [([([pid], bibs)], inspireid)]
    for cluster, iid in inspired:
        pids = set(chain.from_iterable(imap(itemgetter(0), cluster)))

        if len(pids) > 1:
            print "InspireID: %s links the following papers:" % iid
            print map(itemgetter(1), cluster)
            print "More than one personid claimed them:"
            print list(pids)
            print
            continue

        if len(pids) == 0:
            # not even one paper with this inspireid has been
            # claimed, screw it
            continue

        pid = list(pids)[0][0]

        # The last step is to check all non-claimed papers for being
        # claimed by the person on some different signature.
        problem = (_select_from_aidpersonidpapers_where(select=['bibref_table', 'bibref_value', 'bibrec'], pid=pid, rec=bib[2], flag=2)
                   for bib in (bib for lpid, bib in cluster if not lpid))
        problem = list(chain.from_iterable(problem))

        if problem:
            print "A personid has claimed a paper from an inspireid cluster and a contradictory paper."
            print "Personid %d" % pid
            print "Inspireid cluster %s" % str(map(itemgetter(1), cluster))
            print "Contradicting claims: %s" % str(problem)
            print


def remove_clusters_except(excl_surnames):  # remove_results_outside
    '''
    Deletes all disambiguation algorithm result records except records who are
    assoociated with the specified surnames.

    @param excl_surnames: author surnames
    @type excl_surnames: list
    '''
    excl_surnames = frozenset(excl_surnames)
    surnames = frozenset(name[0].split(".")[0] for name in run_sql("""select personid
                                                                      from aidRESULTS"""))
    for surname in surnames - excl_surnames:
        run_sql("""delete from aidRESULTS
                   where personid like %s""",
               (surname + '.%%',))


def get_clusters():  # get_full_results
    '''
    Gets all disambiguation algorithm result records.

    @return: disambiguation algorithm result records ((name, bibref_table, bibref_value, bibrec),)
    @rtype: tuple ((str, str, int, int),)
    '''
    return run_sql("""select personid, bibref_table, bibref_value, bibrec
                      from aidRESULTS""")


def get_existing_papers_and_refs(table, recs, refs):  # get_bibrefrec_subset
    '''
    From the specified papers and bibref values it gets the existing ones.

    @param table:  bibref_table
    @type table: int
    @param recs: paper identifiers
    @type recs: list [int,]
    @param refs: bibref values
    @type refs: list [int,]

    @return: paper identifiers and bibref values set((rec, bibref_value),)
    @rtype: set set((int, int),)
    '''
    table = "bibrec_bib%sx" % str(table)[:-1]
    contents = run_sql("""select id_bibrec, id_bibxxx
                          from %s"""
                       % table)
    recs = set(recs)
    refs = set(refs)

    # there are duplicates
    return set(ifilter(lambda x: x[0] in recs and x[1] in refs, contents))


#
# BibRDF utilities. To be refactored and ported to bibauthorid_bibrdfinterface                      #
#

def get_all_personids_with_orcid():
    pids = run_sql("select personid from aidPERSONIDDATA where tag='extid:ORCID'")
    pids = set(x[0] for x in pids)
    return pids


def get_records_of_authors(personids_set):
    authors = _get_sqlstr_from_set(personids_set)
    recids = run_sql("select bibrec from aidPERSONIDPAPERS where personid in %s" % authors)
    recids = set(x[0] for x in recids)
    return recids


def author_exists(personid):
    return any((bool(run_sql("select * from aidPERSONIDDATA where personid=%s limit 1", (personid,))),
                bool(run_sql("select * from aidPERSONIDPAPERS where personid=%s limit 1", (personid,)))))
