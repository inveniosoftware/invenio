##
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import sys
from time import time
from invenio.search_engine import get_record, \
    perform_request_search, search_unit_in_bibxxx

from invenio.bibauthorid_logutils import Logger

from invenio.dbquery import run_sql
from invenio.bibauthorid_dbinterface import get_existing_authors, \
    get_canonical_name_of_author, get_papers_of_author, \
    get_all_paper_data_of_author, \
    get_signatures_of_paper, get_author_info_of_confirmed_paper, \
    _get_external_ids_from_papers_of_author, get_claimed_papers_of_author, \
    get_inspire_id_of_signature, populate_partial_marc_caches, move_signature, \
    add_external_id_to_author, get_free_author_id, get_inspire_id_of_author, \
    get_orcid_id_of_author, destroy_partial_marc_caches, get_name_by_bibref
from invenio.bibauthorid_general_utils import memoized
import invenio.bibauthorid_dbinterface as db
import invenio.bibauthorid_config as bconfig
from invenio.bibauthorid_webapi import get_hepnames, add_cname_to_hepname_record
from invenio.bibcatalog import BIBCATALOG_SYSTEM
from invenio.bibtask import write_message
from invenio.bibauthorid_hoover_exceptions import *


try:
    from collections import defaultdict
except ImportError:
    from invenio.bibauthorid_general_utils import defaultdict

class HooverStats(object):
    tickets_raised = 0
    new_ids_found = 0
    connections_to_hepnames = 0
    move_signature_calls = 0

    @classmethod
    def report_results(cls):
        log = ("Tickets raised: {0} "
               "New identifiers found: {1} "
               "Connections to hepnames performed: {2} "
               "Signatures attempted to move: {3}").format(cls.tickets_raised, 
                       cls.new_ids_found, cls.connections_to_hepnames, cls.move_signature_calls)
        write_message(log, verbose=4)
        return (cls.tickets_raised, cls.new_ids_found, cls.connections_to_hepnames, cls.move_signature_calls)

def open_rt_ticket(e, debug_log=False, queue='Test'):
    """Take an exception e and, if allowed by the configuration,
    open a ticket for that exception.

    Arguments:
    e -- the exception to be reported
    """
    global ticket_hashes
    ticket_hash = e.hash()
    subject = e.get_message_subject() + ' ' + ticket_hash
    body = e.get_message_body()
    if debug_log:
        debug = e.__repr__() + '\n' + \
            '\n'.join([
                str(key) + " " +
                str(value) for key, value in vars(e).iteritems()])
    else:
        debug = ''
    if rt_ticket_report:
        if ticket_hash not in ticket_hashes.iterkeys():
            ticket_id = BIBCATALOG_SYSTEM.ticket_submit(uid=None,
                                                        subject=subject,
                                                        recordid=e.recid,
                                                        text=body +
                                                        '\n Debugging\
                                                        information: \n' +
                                                        debug,
                                                        queue=queue,
                                                        priority="",
                                                        owner="",
                                                        requestor="")
            HooverStats.tickets_raised += 1
            ticket_data = BIBCATALOG_SYSTEM.ticket_get_info(None, ticket_id)
            ticket_hashes[ticket_hash] = ticket_data, ticket_id, True
        else:
            ticket_hashes[ticket_hash] = ticket_hashes[ticket_hash][:2] + \
                (True,)
            # If the ticket is already there check its status.  In case it is
            # marked as somehow solved -- i.e. resolved, deleted or rejected --
            # reopen it.
            if ticket_hashes[ticket_hash][0]['status'] in ['resolved',
                                                           'deleted',
                                                           'rejected']:
                BIBCATALOG_SYSTEM.ticket_set_attribute(
                    None, ticket_hashes[ticket_hash][1], 'status', 'open')
                HooverStats.tickets_raised += 1
    else:
        write_message('sub: ' + subject + '\nbody:\n' + body + '\ndbg:\n' + debug, verbose=9)

def get_signatures_with_inspireID_sql(inspireid):
    """Signatures of specific inspireID using an Sql query"""
    signatures = run_sql("SELECT 100, secondbib.id, firstbibrec.id_bibrec \
                            FROM bib10x AS firstbib \
                            INNER JOIN bibrec_bib10x AS firstbibrec ON firstbib.id=firstbibrec.id_bibxxx \
                            INNER JOIN bibrec_bib10x AS secondbibrec ON firstbibrec.field_number=secondbibrec.field_number \
                                                        AND secondbibrec.id_bibrec=firstbibrec.id_bibrec \
                            INNER JOIN bib10x AS secondbib ON secondbibrec.id_bibxxx=secondbib.id \
                            WHERE firstbib.value=%s AND secondbib.tag='100__a'", (inspireid,)) + \
        run_sql("SELECT 700, secondbib.id, firstbibrec.id_bibrec \
                            FROM bib70x AS firstbib \
                            INNER JOIN bibrec_bib70x AS firstbibrec ON firstbib.id=firstbibrec.id_bibxxx \
                            INNER JOIN bibrec_bib70x AS secondbibrec ON firstbibrec.field_number=secondbibrec.field_number \
                                                        AND secondbibrec.id_bibrec=firstbibrec.id_bibrec \
                            INNER JOIN bib70x AS secondbib ON secondbibrec.id_bibxxx=secondbib.id \
                            WHERE firstbib.value=%s AND secondbib.tag='700__a'", (inspireid,))

    return signatures


def _get_signatures_with_tag_value_cache(value, tag_ending):
    """Signatures of specific inspireID using CACHE"""
    signatures = []
    LC = db.MARC_100_700_CACHE
    if ('100' + tag_ending, value) in LC['inverted_b100']:
        for rec in LC['b100_id_recid_lookup_table'][
                LC['inverted_b100'][('100' + tag_ending), value]]:
            if LC['inverted_b100'][
                    ('100' + tag_ending, value)] in LC['brb100'][rec]['id']:
                for field_number in LC['brb100'][rec]['id'][
                        LC['inverted_b100'][('100' + tag_ending, value)]]:
                    for key in LC['brb100'][rec]['fn'][field_number]:
                        if LC['b100'][key][0] == '100__a':
                            signatures.append((str(100), key, rec))

    if ('700' + tag_ending, value) in LC['inverted_b700']:
        for rec in LC['b700_id_recid_lookup_table'][
                LC['inverted_b700'][('700' + tag_ending), value]]:
            if LC['inverted_b700'][
                    ('700' + tag_ending, value)] in LC['brb700'][rec]['id']:
                for field_number in LC['brb700'][rec]['id'][
                        LC['inverted_b700'][('700' + tag_ending, value)]]:
                    for key in LC['brb700'][rec]['fn'][field_number]:
                        if LC['b700'][key][0] == '700__a':
                            signatures.append((str(700), key, rec))
    return tuple(signatures)


def get_signatures_with_inspireID_cache(inspireid):
    return _get_signatures_with_tag_value_cache(inspireid, '__i')


def get_signatures_with_orcid_cache(orcid):
    return _get_signatures_with_tag_value_cache(orcid, '__j')


def get_all_recids_in_hepnames():
    return set(perform_request_search(p='', cc='HepNames', rg=0))

get_all_recids_in_hepnames = memoized(get_all_recids_in_hepnames)


def get_inspireID_from_hepnames(pid):
    """return inspireID of a pid by searching the hepnames

    Arguments:
    pid -- the pid of the author to search in the hepnames dataset
    """
    author_canonical_name = get_canonical_name_of_author(pid)
    hepnames_recids = get_all_recids_in_hepnames()
    try:
        #recid = perform_request_search(p="035:" + author_canonical_name[0][0], cc="HepNames")
        recid = set(search_unit_in_bibxxx(
            p=author_canonical_name[0][0], f='035__', type='='))
        recid = list(recid & hepnames_recids)

        if len(recid) > 1:
            raise MultipleHepnamesRecordsWithSameIdException(
                "More than one hepnames record found with the same inspire id",
                recid,
                'INSPIREID')

        hepname_record = get_record(recid[0])
        fields_dict = [dict(x[0]) for x in hepname_record['035']]
        inspire_ids = []
        for d in fields_dict:
            if '9' in d and d['9'] == 'INSPIRE':
                try:
                    inspire_ids.append(d['a'])
                except KeyError:
                    raise BrokenHepNamesRecordException(
                        "There is no inspire id present, althought there is a MARC tag.",
                        recid[0],
                        'INSPIREID')
        if len(inspire_ids) > 1:
            raise BrokenHepNamesRecordException(
                "Multiple inspire ids found in the record.",
                recid[0],
                'INSPIREID')
        else:
            return inspire_ids[0]
    except IndexError:
        return None
    except KeyError:
        return None


class HepnamesConnector(object):

    """A class to handle the connections that are to be performed.
    This is needed to avoid the creation of too many bibupload tasks.

    Arguments:
    produce_connection_entry -- the function that returns the correspondance
                                between canonical name and record id

    Attributes:
    cname_dict -- the dictionary that holds the connections that need to be done
    """

    def __init__(self, produce_connection_entry=None,
                 packet_size=1000, dry_hepnames_run=False):
        self.cname_dict = dict()
        self.produce_connection_entry = produce_connection_entry
        self.packet_size = packet_size
        if dry_hepnames_run:
            def _null_func():
                pass
            self.execute_connection = _null_func
        else:
            self.execute_connection = self._execute_connection

    def add_connection(self, pid, inspireid):
        """add connection to the connector indicating that there should be a
        connection created between the pid an the HepNames record with the
        inspireID"""
        try:
            coll_id = get_inspireID_from_hepnames(pid)
        except BrokenHepNamesRecordException:
            coll_id = None
        if not coll_id:
            tmp = dict_entry_for_hepnames_connector(pid, inspireid)
            if tmp:
                self.cname_dict.update(tmp)
            if len(self.cname_dict.keys()) >= self.packet_size:
                self.execute_connection()

    def _execute_connection(self):
        """Execute the connection between the canonical name and the hepnames
        record. In case the dry_hepnames_run option is true this functions is
        substituted with the _null_func(), a function that has no effect.
        """
        add_cname_to_hepname_record(self.cname_dict)
        HooverStats.connections_to_hepnames += len(self.cname_dict)
        self.cname_dict.clear()


def dict_entry_for_hepnames_connector(pid, inspireid):
    """Produce the correct dictonary entry for the connector to use.

    Arguments:
    pid -- the pid of the author that has the inspireID
    inspireID -- the inspireID of the author
    """
    author_canonical_name = get_canonical_name_of_author(pid)

    if not author_canonical_name:
        return None

    recid = perform_request_search(p="035:" + inspireid, cc="HepNames")
    if recid:
        if len(recid) > 1:
            raise MultipleHepnamesRecordsWithSameIdException(
                "More than one hepnames record found with the same inspire id",
                recid,
                'INSPIREID')
        write_message("Connecting pid {0} canonical_name %s inspireID {1}".format(pid, author_canonical_name, inspireid), verbose=3)
        return {author_canonical_name[0][0]: recid[0]}


class Vacuumer(object):

    """Class responsible for vacuuming the signatures to the right profile

    Constructor arguments:
    pid -- the pid of the author
    """

    def __init__(self, pid):
        self.claimed_paper_signatures = set(
            sig[1:4] for sig in get_papers_of_author(pid, include_unclaimed=False))
        self.unclaimed_paper_signatures = set(
            sig[1:4] for sig in get_papers_of_author(pid, include_claimed=False))
        self.claimed_paper_records = set(
            rec[2] for rec in self.claimed_paper_signatures)
        self.unclaimed_paper_records = set(
            rec[2] for rec in self.unclaimed_paper_signatures)
        self.pid = pid

    def vacuum_signature(self, signature):
        if signature not in self.unclaimed_paper_signatures and signature not in self.claimed_paper_signatures:
            if signature[2] in self.claimed_paper_records:
                raise DuplicateClaimedPaperException(
                    "Vacuum a duplicated claimed paper",
                    self.pid,
                    signature,
                    filter(
                        lambda x: x[2] == signature[2],
                        self.claimed_paper_signatures))

            duplicated_signatures = filter(
                lambda x: signature[2] == x[2],
                self.unclaimed_paper_signatures)

            if duplicated_signatures:
                write_message(("Conflict in pid {0}"
                              " with signature {1}".format(signature, self.pid)),
                              verbose=4)
                new_pid = get_free_author_id()
                write_message(
                    ("Moving  conflicting signature {0} from pid {1}"
                    " to pid {2}".format(duplicated_signatures[0], 
                        self.pid,new_pid)),
                    verbose=3)
                HooverStats.move_signature_calls += 1
                move_signature(duplicated_signatures[0], new_pid)
                HooverStats.move_signature_calls += 1
                move_signature(signature, self.pid)
                after_vacuum = (sig[1:4]
                                for sig in get_papers_of_author(self.pid))

                if signature not in after_vacuum:
                    HooverStats.move_signature_calls += 1
                    move_signature(duplicated_signatures[0], self.pid)

                raise DuplicateUnclaimedPaperException(
                    "Vacuum a duplicated unclaimed paper",
                    new_pid,
                    signature,
                    duplicated_signatures)

            write_message("Hoovering {0} to pid {1}".format(signature, self.pid), verbose=3)
            HooverStats.move_signature_calls += 1
            move_signature(signature, self.pid)


def get_signatures_with_inspireID(inspireid):
    """get and vacuum of the signatures that belong to this inspireID

    Arguments:
    inspireID -- the string containing the inspireID
    """
    return get_signatures_with_inspireID_cache(inspireid)


def get_records_with_tag(tag):
    """return all the records with a specific tag

    Arguments:
    tag -- the tag to search for
    """
    assert tag in ['100__i', '100__j', '700__i', '700__j']
    if tag.startswith("100"):
        return run_sql(
            "select id_bibrec from bibrec_bib10x where id_bibxxx in (select id from bib10x where tag=%s)",
            (tag,
             ))
    if tag.startswith("700"):
        return run_sql(
            "select id_bibrec from bibrec_bib70x where id_bibxxx in (select id from bib70x where tag=%s)",
            (tag,
             ))


def get_inspireID_from_claimed_papers(pid, intersection_set=None):
    """returns the inspireID found inside the claimed papers of the author.
    This happens only in case all the inspireIDs are the same,
    if there is  a conflict in the inspireIDs of the papers the
    ConflictingIdsFromReliableSource exception is raised

    Arguments:
    pid -- the pid of the author
    intersection_set -- a set of paper signatures. The unclaimed paper
                        signatures are then intersected with this set.
                        the result is used for the inspireID search.
    """
    claimed_papers = get_papers_of_author(pid, include_unclaimed=False)
    if intersection_set:
        claimed_papers = filter(
            lambda x: x[3] in intersection_set, claimed_papers)
        # claimed_papers = [x for x in claimed_paper_signatures if x[3] in intersection_set]
    claimed_paper_signatures = (x[1:4] for x in claimed_papers)

    inspireid_list = []
    for sig in claimed_paper_signatures:
        inspireid = get_inspire_id_of_signature(sig)
        if inspireid:
            if len(inspireid) > 1:
                open_rt_ticket(ConflictingIdsOnRecordException(
                    'Conflicting ids found', pid, 'INSPIREID', inspireid, sig))
                return None

            inspireid_list.append(inspireid[0])

    try:
        if inspireid_list[1:] == inspireid_list[:-1]:
            return inspireid_list[0]
    except IndexError:
        return None
    else:
        raise MultipleIdsOnSingleAuthorException(
            'Signatures conflicting:' +
            ','.join(claimed_paper_signatures),
            pid,
            'INSPIREID',
            inspireid_list)


def get_inspireID_from_unclaimed_papers(pid, intersection_set=None):
    """returns the inspireID found inside the unclaimed papers of the author.
    This happens only in case all the inspireIDs are the same,
    if there is  a conflict in the inspireIDs of the papers the
    ConflictingIdsOnRecordException exception is reported.
    It is not raised, due to the fact that this is an unreliable source.

    Arguments:
    pid -- the pid of the author
    intersection_set -- a set of paper signatures. The unclaimed paper
                        signatures are then intersected with this set.
                        the result is used for the inspireID search.
    """
    unclaimed_papers = get_papers_of_author(pid, include_claimed=False)
    if intersection_set:
        unclaimed_papers = filter(
            lambda x: x[3] in intersection_set, unclaimed_papers)
    unclaimed_paper_signatures = (x[1:4] for x in unclaimed_papers)

    inspireid_list = []
    for sig in unclaimed_paper_signatures:
        inspireid = get_inspire_id_of_signature(sig)
        if inspireid:
            if len(inspireid) > 1:
                open_rt_ticket(ConflictingIdsOnRecordException(
                    'Conflicting ids found', pid, 'INSPIREID', inspireid, sig))
                return None

            inspireid_list.append(inspireid[0])

    try:
        if inspireid_list[1:] == inspireid_list[:-1]:
            return inspireid_list[0]
    except IndexError:
        return None
    else:
        raise MultipleIdsOnSingleAuthorException(
            'Signatures conflicting:' +
            ','.join(unclaimed_paper_signatures),
            pid,
            'INSPIREID',
            inspireid_list)

ticket_hashes = dict()
rt_ticket_report=False

def hoover(authors=None, check_db_consistency=False, dry_run=False,
           packet_size=1000, dry_hepnames_run=False, open_tickets=False, queue='Test'):
    """The actions that hoover performs are the following:
    1. Find out the identifiers that belong to the authors(pids) in the database
    2. Find and pull all the signatures that have the same identifier as the author to the author
    3. Connect the profile of the author with the hepnames collection entry
    (optional) check the database to see if it is in a consistent state

    Keyword arguments:
    authors -- an iterable of authors to be hoovered
    check_db_consistency -- perform checks for the consistency of the database
    dry_run -- do not alter the database tables
    packet_size -- squeeze together the marcxml. This there are fewer bibupload
                   processes for the bibsched to run.
    dry_hepnames_run -- do not alter the hepnames collection
    queue -- the name of the queue to be used in the rt system for the tickets
    """
    global rt_ticket_report
    rt_ticket_report = open_tickets
    write_message("Packet size {0}".format(packet_size), verbose=1)
    write_message("Initializing hoover", verbose=1)
    write_message("Selecting records with identifiers...", verbose=1)
    recs = get_records_with_tag('100__i')
    recs += get_records_with_tag('100__j')
    recs += get_records_with_tag('700__i')
    recs += get_records_with_tag('700__j')
    write_message("Found {0} records".format(len(set(recs))), verbose=2)
    recs = set(recs) & set(
        run_sql("select DISTINCT(bibrec) from aidPERSONIDPAPERS"))
    write_message("   out of which {0} are in BibAuthorID".format(len(recs)), verbose=2)

    records_with_id = set(rec[0] for rec in recs)

    destroy_partial_marc_caches()
    populate_partial_marc_caches(records_with_id, create_inverted_dicts=True)

    if rt_ticket_report:
        global ticket_hashes
        write_message("Ticketing system rt is used", verbose=9)
        write_message("Building hash cache for tickets", verbose=9)
        ticket_ids = BIBCATALOG_SYSTEM.ticket_search(None, subject='[Hoover]')
        for ticket_id in ticket_ids:
            try:
                ticket_data = BIBCATALOG_SYSTEM.ticket_get_info(
                    None, ticket_id)
                ticket_hashes[
                    ticket_data['subject'].split()[-1]] = ticket_data, ticket_id, False
            except IndexError:
                write_message("Problem in subject of ticket {0}".format(ticket_id), verbose=5)
        write_message("Found {0} tickets".format(len(ticket_hashes)), verbose=2)

    fdict_id_getters = {
        "INSPIREID": {
            'reliable': [get_inspire_id_of_author,
                         get_inspireID_from_hepnames,
                         lambda pid: get_inspireID_from_claimed_papers(
                             pid, intersection_set=records_with_id)],

            'unreliable': [lambda pid: get_inspireID_from_unclaimed_papers(
                           pid, intersection_set=records_with_id)],
            'signatures_getter': get_signatures_with_inspireID,
            'connection': dict_entry_for_hepnames_connector,
            'data_dicts': {
                'pid_mapping': defaultdict(set),
                'id_mapping': defaultdict(set)
            }
        },

        "ORCID": {
            'reliable': [  # get_orcid_id_of_author,
                # get_inspireID_from_hepnames,
                # lambda pid: get_inspireID_from_claimed_papers(pid,
                # intersection_set=records_with_id)]
            ],

            'unreliable': [
                # get_inspireID_from_hepnames,
                # lambda pid: get_inspireID_from_claimed_papers(pid,
                # intersection_set=records_with_id)]
            ],
            'signatures_getter': lambda x: list(),
            'connection': lambda pid, _id: None,
            'data_dicts': {
                'pid_mapping': defaultdict(set),
                'id_mapping': defaultdict(set)
            }
        }
    }

    if not authors:
        authors = get_existing_authors()

    write_message("Running on {0}".format(len(authors)), verbose=2)

    unclaimed_authors = defaultdict(set)
    hep_connector = HepnamesConnector(
        packet_size=packet_size, dry_hepnames_run=dry_hepnames_run)

    for index, pid in enumerate(authors):
        write_message("Searching for reliable ids of person {0}".format(pid), verbose=2)
        for identifier_type, functions in fdict_id_getters.iteritems():
            write_message("    Type: {0}".format(identifier_type,), verbose=9)

            try:
                G = (func(pid) for func in functions['reliable'])
                if check_db_consistency:
                    results = filter(None, (func for func in G if func))
                    try:
                        # check if this is reduntant
                        if len(results) == 1:
                            consistent_db = True
                        else:
                            consistent_db = len(set(results)) <= 1
                        res = results[0]
                    except IndexError:
                        res = None
                    else:
                        if not consistent_db:
                            res = None
                            raise InconsistentIdentifiersException(
                                'Inconsistent database',
                                pid,
                                identifier_type,
                                set(results))
                else:
                    res = next((func for func in G if func), None)
            except MultipleIdsOnSingleAuthorException as e:
                open_rt_ticket(e, queue=queue)
            except BrokenHepNamesRecordException as e:
                continue
            except InconsistentIdentifiersException as e:
                open_rt_ticket(e, queue=queue)
            except MultipleHepnamesRecordsWithSameIdException as e:
                open_rt_ticket(e, queue=queue)
            else:
                if res:
                    HooverStats.new_ids_found += 1
                    write_message("   Found reliable id {0}".format(res, ), verbose=9)
                    fdict_id_getters[identifier_type][
                        'data_dicts']['pid_mapping'][pid].add(res)
                    fdict_id_getters[identifier_type][
                        'data_dicts']['id_mapping'][res].add(pid)
                else:
                    write_message("   No reliable id found", verbose=9)
                    unclaimed_authors[identifier_type].add(pid)

    write_message("Vacuuming reliable ids...", verbose=2)

    for identifier_type, data in fdict_id_getters.iteritems():
        hep_connector.produce_connection_entry = fdict_id_getters[
            identifier_type]['connection']
        for pid, identifiers in data['data_dicts']['pid_mapping'].iteritems():
            write_message("   Person {0} has reliable identifier(s) {1} ".format(
                       str(pid), str(identifiers)), verbose=9)
            try:
                if len(identifiers) == 1:
                    identifier = list(identifiers)[0]
                    write_message("        Considering  {0}".format(identifier), verbose=9)

                    if len(data['data_dicts']['id_mapping'][identifier]) == 1:
                        if not dry_run:
                            rowenta = Vacuumer(pid)
                            signatures = data['signatures_getter'](identifier)
                            write_message(
                                "        Vacuuming {0} signatures! ".format(str(
                                    len(signatures))), verbose=4)
                            for sig in signatures:
                                try:
                                    rowenta.vacuum_signature(sig)
                                except DuplicateClaimedPaperException as e:
                                    open_rt_ticket(e, queue=queue)
                                except DuplicateUnclaimedPaperException as e:
                                    unclaimed_authors[
                                        identifier_type].add(e.pid)
                            write_message(
                                "        Adding inspireid {0} to pid {1}".format(
                                    identifier, pid), verbose=3)
                            add_external_id_to_author(
                                pid, identifier_type, identifier)
                            hep_connector.add_connection(pid, identifier)

                    else:
                        raise MultipleAuthorsWithSameIdException(
                            "More than one authors with the same identifier",
                            data['data_dicts']['id_mapping'][identifier],
                            identifier)
                else:
                    raise MultipleIdsOnSingleAuthorException(
                        "More than one identifier on a single author ",
                        pid,
                        'INSPIREID',
                        identifiers)

            except MultipleAuthorsWithSameIdException as e:
                open_rt_ticket(e, queue=queue)
            except MultipleIdsOnSingleAuthorException as e:
                open_rt_ticket(e, queue=queue)
            except MultipleHepnamesRecordsWithSameIdException as e:
                open_rt_ticket(e, queue=queue)
            write_message("   Done with {0}".format(pid,), verbose=3)

    write_message("Vacuuming unreliable ids...", verbose=2)

    for identifier_type, functions in fdict_id_getters.iteritems():
        hep_connector.produce_connection_entry = fdict_id_getters[
            identifier_type]['connection']
        for index, pid in enumerate(unclaimed_authors[identifier_type]):
            write_message("Searching for unreliable ids of person {0}".format(pid), verbose=9)
            try:
                G = (func(pid) for func in functions['unreliable'])
                res = next((func for func in G if func), None)
                if res is None:
                    continue
            except MultipleIdsOnSingleAuthorException as e:
                continue
            except BrokenHepNamesRecordException as e:
                continue
            except MultipleHepnamesRecordsWithSameIdException as e:
                open_rt_ticket(e, queue=queue)

            HooverStats.new_ids_found += 1
            write_message("   Person {0} has unreliable identifier {1} ".format(
                       str(pid), str(res)), verbose=9)

            if res in fdict_id_getters[identifier_type]['data_dicts']['id_mapping']:
                write_message(
                    "        Id {0} is already assigned to another person, skipping person {1} ".format(
                    str(res), pid))
                continue

            if not dry_run:
                rowenta = Vacuumer(pid)
                signatures = functions['signatures_getter'](res)
                for sig in signatures:
                    try:
                        rowenta.vacuum_signature(sig)
                    except DuplicateClaimedPaperException as e:
                        open_rt_ticket(e, queue=queue)
                    except DuplicateUnclaimedPaperException as e:
                        pass

                write_message("     Adding inspireid {0} to pid {1}".format(res, pid), verbose=3)
                add_external_id_to_author(pid, identifier_type, res)
                hep_connector.add_connection(pid, res)
            write_message("   Done with {0}".format(pid), verbose=3)
    hep_connector.execute_connection()
    for ticket in ticket_hashes:
        if ticket[2] == False:
            BIBCATALOG_SYSTEM.ticket_set_attribute(
                None, ticket[1], 'status', 'resolved')

    HooverStats.report_results()
    write_message("Terminating hoover", verbose=1)

if __name__ == "__main__":
    hoover(check_db_consistency=True)
