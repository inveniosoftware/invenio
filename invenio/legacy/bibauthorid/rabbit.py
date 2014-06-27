# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011, 2012, 2014 CERN.
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

from itertools import cycle, imap, chain, izip
from operator import itemgetter


from invenio.legacy.bibsched.bibtask import task_sleep_now_if_required, write_message, task_update_progress

from invenio.legacy.bibauthorid import config as bconfig

from invenio.legacy.bibauthorid.comparison import cached_sym
from invenio.legacy.bibauthorid.name_utils import compare_names as comp_names
from invenio.legacy.bibauthorid.name_utils import split_name_parts
from invenio.legacy.bibauthorid.name_utils import create_normalized_name
from invenio.legacy.bibauthorid.general_utils import update_status \
                                    , update_status_final
from invenio.legacy.bibauthorid.matrix_optimization import maximized_mapping
from invenio.legacy.bibauthorid.backinterface import get_all_valid_papers
from invenio.legacy.bibauthorid.backinterface import filter_bibrecs_outside
from invenio.legacy.bibauthorid.backinterface import get_deleted_papers
from invenio.legacy.bibauthorid.backinterface import remove_papers
from invenio.legacy.bibauthorid.backinterface import get_author_refs_of_paper
from invenio.legacy.bibauthorid.backinterface import get_coauthor_refs_of_paper
from invenio.legacy.bibauthorid.backinterface import get_signatures_of_paper
from invenio.legacy.bibauthorid.backinterface import modify_signature
from invenio.legacy.bibauthorid.backinterface import remove_signatures
from invenio.legacy.bibauthorid.backinterface import get_authors_by_name as _find_pids_by_exact_name
from invenio.legacy.bibauthorid.backinterface import create_new_author_by_signature as _new_person_from_signature
from invenio.legacy.bibauthorid.backinterface import add_signature as _add_signature
from invenio.legacy.bibauthorid.backinterface import update_canonical_names_of_authors
from invenio.legacy.bibauthorid.backinterface import update_external_ids_of_authors
from invenio.legacy.bibauthorid.backinterface import get_name_by_bibref
from invenio.legacy.bibauthorid.backinterface import populate_partial_marc_caches
from invenio.legacy.bibauthorid.backinterface import destroy_partial_marc_caches
from invenio.legacy.bibauthorid.backinterface import get_inspire_id_of_signature
from invenio.legacy.bibauthorid.backinterface import get_author_by_external_id
from invenio.legacy.bibauthorid.backinterface import get_name_to_authors_mapping
from invenio.legacy.bibauthorid.backinterface import get_free_author_id
from invenio.legacy.bibauthorid.backinterface import remove_empty_authors
USE_EXT_IDS = bconfig.RABBIT_USE_EXTERNAL_IDS
USE_INSPIREID = bconfig.RABBIT_USE_EXTERNAL_ID_INSPIREID

from datetime import datetime
now = datetime.now

def rabbit(bibrecs, check_invalid_papers=False, personids_to_update_extids=None, verbose=False):
    '''
    @param bibrecs: an iterable full of bibrecs
    @type bibrecs: an iterable of ints
    @return: none
    '''
    logfile = open('/tmp/RABBITLOG-%s' % str(now()).replace(" ", "_"), 'w')
    logfile.write("RABBIT %s running on %s \n" % (str(now()), str(bibrecs)))

    def logwrite(msg, is_error):
        verb = 9
        if is_error or verbose:
            verb = 1
        write_message(msg, verbose=verb)

    if bconfig.RABBIT_USE_CACHED_PID:
        PID_NAMES_CACHE = get_name_to_authors_mapping()

        def find_pids_by_exact_names_cache(name):
            try:
                return zip(PID_NAMES_CACHE[name])
            except KeyError:
                return []

        def add_signature_using_names_cache(sig, name, pid):
            try:
                PID_NAMES_CACHE[name].add(pid)
            except KeyError:
                PID_NAMES_CACHE[name] = set([pid])
            _add_signature(sig, name, pid)

        def new_person_from_signature_using_names_cache(sig, name):
            pid = get_free_author_id()
            add_signature_using_names_cache(sig, name, pid)
            return pid

        add_signature = add_signature_using_names_cache
        new_person_from_signature = new_person_from_signature_using_names_cache
        find_pids_by_exact_name = find_pids_by_exact_names_cache
    else:
        add_signature = _add_signature
        new_person_from_signature = _new_person_from_signature
        find_pids_by_exact_name = _find_pids_by_exact_name

    compare_names = cached_sym(lambda x: x)(comp_names)
    # fast assign threshold
    threshold = 0.80

    if not bibrecs or check_invalid_papers:
        all_bibrecs = get_all_valid_papers()

        if not bibrecs:
            bibrecs = all_bibrecs

        if check_invalid_papers:
            filter_bibrecs_outside(all_bibrecs)

    if (bconfig.RABBIT_USE_CACHED_GET_GROUPED_RECORDS and
        len(bibrecs) > bconfig.RABBIT_USE_CACHED_GET_GROUPED_RECORDS_THRESHOLD):
        populate_partial_marc_caches()
        SWAPPED_GET_GROUPED_RECORDS = True
    else:
        SWAPPED_GET_GROUPED_RECORDS = False

    updated_pids = set()
    deleted = frozenset(p[0] for p in get_deleted_papers())

    for idx, rec in enumerate(bibrecs):

        logwrite("\nConsidering %s" % str(rec), False)

        if idx%200 == 0:
            task_sleep_now_if_required(True)

            update_status(float(idx) / len(bibrecs), "%d/%d current: %d" % (idx, len(bibrecs), rec))
            task_update_progress("%d/%d current: %d" % (idx, len(bibrecs), rec))

        if rec in deleted:
            logwrite(" - Record was deleted, removing from pid and continuing with next record", True)
            remove_papers([rec])
            continue


        markrefs = frozenset(chain(izip(cycle([100]), imap(itemgetter(0), get_author_refs_of_paper(rec))),
                                   izip(cycle([700]), imap(itemgetter(0), get_coauthor_refs_of_paper(rec)))))

        personid_rows = [map(int, row[:3]) + [row[4]] for row in get_signatures_of_paper(rec)]
        personidrefs_names = dict(((row[1], row[2]), row[3]) for row in personid_rows)

        personidrefs = frozenset(personidrefs_names.keys())
        new_signatures = list(markrefs - personidrefs)
        old_signatures = list(personidrefs - markrefs)

        new_signatures_names = dict((new, create_normalized_name(split_name_parts(get_name_by_bibref(new))))
                                    for new in new_signatures)

        # matrix |new_signatures| X |old_signatures|
        matrix = [[compare_names(new_signatures_names[new], personidrefs_names[old])
                  for old in old_signatures] for new in new_signatures]

        logwrite(" - Old signatures: %s" % str(old_signatures), bool(old_signatures))
        logwrite(" - New signatures: %s" % str(new_signatures), bool(new_signatures))
        logwrite(" - Matrix: %s" % str(matrix), bool(matrix))

        # [(new_signatures, old_signatures)]
        best_match = [(new_signatures[new], old_signatures[old])
                      for new, old, score in maximized_mapping(matrix) if score > threshold]

        logwrite(" - Best match: %s " % str(best_match), bool(best_match))

        for new, old in best_match:
            logwrite(" - - Moving signature: %s on %s to %s as %s" % (old, rec, new, new_signatures_names[new]), True)
            modify_signature(old, rec, new, new_signatures_names[new])

        remove_signatures(tuple(list(old) + [rec]) for old in old_signatures)

        not_matched = frozenset(new_signatures) - frozenset(map(itemgetter(0), best_match))

        pids_having_rec = set([int(row[0]) for row in get_signatures_of_paper(rec)])
        logwrite(" - Not matched: %s" % str(not_matched), bool(not_matched))

        if not_matched:
            used_pids = set(r[0] for r in personid_rows)

        for sig in not_matched:
            name = new_signatures_names[sig]
            matched_pids = list()
            if USE_EXT_IDS:
                if USE_INSPIREID:
                    inspire_id = get_inspire_id_of_signature(sig + (rec,))
                    if inspire_id:
                        matched_pids = list(get_author_by_external_id(inspire_id[0]))
                        if matched_pids and int(matched_pids[0][0]) in pids_having_rec:
                            matched_pids = list()
                if matched_pids:
                    add_signature(list(sig) + [rec], name, matched_pids[0][0])
                    updated_pids.add(matched_pids[0][0])
                    pids_having_rec.add(matched_pids[0][0])
                    continue

            matched_pids = find_pids_by_exact_name(name)
            matched_pids = [p for p in matched_pids if int(p[0]) not in used_pids]

            if not matched_pids or int(matched_pids[0][0]) in pids_having_rec:
                new_pid = new_person_from_signature(list(sig) + [rec], name)
                used_pids.add(new_pid)
                updated_pids.add(new_pid)

            else:
                add_signature(list(sig) + [rec], name, matched_pids[0][0])
                used_pids.add(matched_pids[0][0])
                updated_pids.add(matched_pids[0][0])
                pids_having_rec.add(matched_pids[0][0])

        logwrite('Finished with %s' % str(rec), False)

    update_status_final()

    if personids_to_update_extids:
        updated_pids |= personids_to_update_extids
    if updated_pids: # an empty set will update all canonical_names
        update_canonical_names_of_authors(updated_pids)
        update_external_ids_of_authors(updated_pids, limit_to_claimed_papers=bconfig.LIMIT_EXTERNAL_IDS_COLLECTION_TO_CLAIMED_PAPERS)

    if SWAPPED_GET_GROUPED_RECORDS:
        destroy_partial_marc_caches()

    remove_empty_authors()
