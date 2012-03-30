# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011 CERN.
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

from bibtask import task_sleep_now_if_required

from bibauthorid_comparison import cached_sym
from bibauthorid_name_utils import compare_names as comp_names
from bibauthorid_name_utils import split_name_parts
from bibauthorid_name_utils import create_normalized_name
from bibauthorid_general_utils import update_status
from bibauthorid_matrix_optimization import maximized_mapping
from bibauthorid_backinterface import get_all_valid_bibrecs
from bibauthorid_backinterface import filter_bibrecs_outside
from bibauthorid_backinterface import get_deleted_papers
from bibauthorid_backinterface import delete_paper_from_personid
from bibauthorid_backinterface import get_authors_from_paper
from bibauthorid_backinterface import get_coauthors_from_paper
from bibauthorid_backinterface import get_signatures_from_rec
from bibauthorid_backinterface import modify_signature
from bibauthorid_backinterface import remove_sigs
from bibauthorid_backinterface import find_pids_by_name
from bibauthorid_backinterface import new_person_from_signature
from bibauthorid_backinterface import add_signature
from bibauthorid_backinterface import update_personID_canonical_names
from bibauthorid_backinterface import get_name_by_bibrecref

def rabbit(bibrecs, check_invalid_papers=False):
    '''
    @param bibrecs: an iterable full of bibrecs
    @type bibrecs: an iterable of ints
    @return: none
    '''

    compare_names = cached_sym(lambda x: x)(comp_names)
    # fast assign threshold
    threshold = 0.80

    if not bibrecs or check_invalid_papers:
        all_bibrecs = get_all_valid_bibrecs()

        if not bibrecs:
            bibrecs = all_bibrecs

        if check_invalid_papers:
            filter_bibrecs_outside(all_bibrecs)

    updated_pids = set()
    deleted = frozenset(p[0] for p in get_deleted_papers())

    for idx, rec in enumerate(bibrecs):
        task_sleep_now_if_required(True)
        update_status(float(idx) / len(bibrecs), "%d/%d current: %d" % (idx, len(bibrecs), rec))
        if rec in deleted:
            delete_paper_from_personid(rec)
            continue

        markrefs = frozenset(chain(izip(cycle([100]), imap(itemgetter(0), get_authors_from_paper(rec))),
                                   izip(cycle([700]), imap(itemgetter(0), get_coauthors_from_paper(rec)))))

        personid_rows = [map(int, row[:4]) + [row[4]] for row in get_signatures_from_rec(rec)]
        personidrefs_names = dict(((row[1], row[2]), row[4]) for row in personid_rows)

        personidrefs = frozenset(personidrefs_names.keys())
        new_signatures = list(markrefs - personidrefs)
        old_signatures = list(personidrefs - markrefs)

        new_signatures_names = dict((new, create_normalized_name(split_name_parts(get_name_by_bibrecref(new))))
                                    for new in new_signatures)

        # matrix |new_signatures| X |old_signatures|
        matrix = [[compare_names(new_signatures_names[new], personidrefs_names[old])
                  for old in old_signatures] for new in new_signatures]

        # [(new_signatures, old_signatures)]
        best_match = [(new_signatures[new], old_signatures[old])
                      for new, old, score in maximized_mapping(matrix) if score > threshold]
        for new, old in best_match:
            modify_signature(old, rec, new, new_signatures_names[new])

        remove_sigs(tuple(list(old) + [rec]) for old in old_signatures)

        not_matched = frozenset(new_signatures) - frozenset(map(itemgetter(0), best_match))

        if not_matched:
            used_pids = set(r[0] for r in personid_rows)

        for sig in not_matched:
            name = new_signatures_names[sig]
            family = split_name_parts(name)[0]
            possible_pids = find_pids_by_name(family)
            possible_pids = [p for p in possible_pids if int(p[0]) not in used_pids]

            if not possible_pids:
                new_pid = new_person_from_signature(list(sig) + [rec], name)
                used_pids.add(new_pid)
                updated_pids.add(new_pid)
                continue

            # python 2.4 doesn't support key argument on max
            winner = possible_pids[0]
            win_score = compare_names(name, winner[1])
            for cur in possible_pids[1:]:
                score = compare_names(name, cur[1])
                if win_score < score:
                    winner = cur
                    win_score = score

            if win_score >= threshold:
                add_signature(list(sig) + [rec], name, winner[0])
                used_pids.add(winner[0])
                updated_pids.add(winner[0])
            else:
                new_pid = new_person_from_signature(list(sig) + [rec], name)
                used_pids.add(new_pid)
                updated_pids.add(new_pid)

    if updated_pids: # an empty set will update all canonical_names
        update_personID_canonical_names(updated_pids)
    update_status(1)
    print

