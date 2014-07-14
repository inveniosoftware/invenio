from operator import itemgetter
from itertools import cycle, imap, chain, izip
from invenio.bibauthorid_name_utils import compare_names as comp_names, \
    create_matchable_name
from invenio import bibauthorid_config as bconfig
from invenio.bibauthorid_backinterface import get_authors_by_name, \
    add_signature, get_signatures_of_paper, \
    remove_signatures, modify_signature, filter_bibrecs_outside, get_deleted_papers, \
    create_new_author_by_signature as new_person_from_signature, get_all_valid_bibrecs, \
    remove_papers, get_author_refs_of_paper,\
    get_coauthor_refs_of_paper, get_name_by_bibref,  \
    get_author_by_external_id, update_canonical_names_of_authors, \
    update_external_ids_of_authors, remove_empty_authors
from invenio.bibauthorid_matrix_optimization import maximized_mapping
from invenio.bibauthorid_dbinterface import populate_partial_marc_caches
from invenio.bibauthorid_dbinterface import destroy_partial_marc_caches
from invenio.bibauthorid_general_utils import memoized

from invenio.bibtask import task_update_progress
from datetime import datetime
from invenio.dbquery import run_sql
from invenio.bibauthorid_logutils import Logger


now = datetime.now

USE_EXT_IDS = bconfig.RABBIT_USE_EXTERNAL_IDS
EXT_IDS_TO_USE = bconfig.RABBIT_EXTERNAL_IDS_TO_USE
if USE_EXT_IDS:
    external_id_getters = list()
    if 'InspireID' in EXT_IDS_TO_USE:
        from invenio.bibauthorid_backinterface import get_inspire_id_of_signature
        external_id_getters.append(get_inspire_id_of_signature)
    if 'OrcidID' in EXT_IDS_TO_USE:
        from invenio.bibauthorid_backinterface import get_orcid_id_of_signature
        external_id_getters.append(get_orcid_id_of_signature)


M_NAME_PIDS_CACHE = None

# The first element of this list is the master function
M_NAME_FUNCTIONS = [create_matchable_name]


def populate_mnames_pids_cache():
    global M_NAME_PIDS_CACHE
    mnames_pids = run_sql("select distinct(m_name), personid from aidPERSONIDPAPERS")
    M_NAME_PIDS_CACHE = dict(mnames_pids)


def destroy_mnames_pids_cache():
    global M_NAME_PIDS_CACHE
    M_NAME_PIDS_CACHE = None


def rabbit(bibrecs=None, check_invalid_papers=False,
           personids_to_update_extids=None, verbose=False):

    logger = Logger("Rabbit")

    if verbose:
        logger.verbose = True

    if not bibrecs:
        logger.log("Running on all records")
    else:
        logger.log("Running on %s " % (str(bibrecs)))

    populate_mnames_pids_cache()

    global M_NAME_PIDS_CACHE

    memoized_compare_names = memoized(comp_names)
    compare_names = lambda x, y: memoized_compare_names(*sorted((x, y)))

    def find_pids_by_matchable_name_with_cache(matchable_name):
        try:
            matched_pids = [M_NAME_PIDS_CACHE[matchable_name]]
        except KeyError:
            matched_pids = get_authors_by_name(matchable_name,
                                               use_matchable_name=True)
            if matched_pids:
                M_NAME_PIDS_CACHE[matchable_name] = matched_pids[0]
        return matched_pids

    if USE_EXT_IDS:

        def get_matched_pids_by_external_ids(sig, rec, pids_having_rec):
            '''
            This function returns all the matched pids after iterating
            through all available external IDs of the system.
            '''
            for get_external_id_of_signature in external_id_getters:
                external_id = get_external_id_of_signature(sig + (rec,))
                if external_id:
                    matched_pids = list(get_author_by_external_id(external_id[0]))
                    if matched_pids and int(matched_pids[0][0]) in pids_having_rec:
                        matched_pids = list()
                    return matched_pids

    threshold = 0.8

    if not bibrecs or check_invalid_papers:
        all_bibrecs = get_all_valid_bibrecs()

        if not bibrecs:
            bibrecs = all_bibrecs

        if check_invalid_papers:
            filter_bibrecs_outside(all_bibrecs)

    updated_pids = set()
    deleted = frozenset(p[0] for p in get_deleted_papers())

    bibrecs = list(bibrecs)
    for idx, rec in enumerate(bibrecs):

        logger.log("Considering %s" % str(rec))

        if idx % 100 == 0:
            task_update_progress("%d/%d current: %d" % (idx, len(bibrecs), rec))

        if idx % 1000 == 0:
            destroy_partial_marc_caches()
            populate_partial_marc_caches(bibrecs[idx: idx + 1000])

            logger.log(float(idx) / len(bibrecs), "%d/%d" % (idx, len(bibrecs)))

        if rec in deleted:
            remove_papers([rec])
            continue

        author_refs = get_author_refs_of_paper(rec)
        coauthor_refs = get_coauthor_refs_of_paper(rec)

        markrefs = frozenset(chain(izip(cycle([100]), imap(itemgetter(0),
                                                           author_refs)),
                                   izip(cycle([700]), imap(itemgetter(0),
                                                           coauthor_refs))))

        personid_rows = [map(int, row[:3]) + [row[4]]
                         for row in get_signatures_of_paper(rec)]
        personidrefs_names = dict(((row[1], row[2]), row[3])
                                  for row in personid_rows)

        personidrefs = frozenset(personidrefs_names.keys())
        new_signatures = list(markrefs - personidrefs)
        old_signatures = list(personidrefs - markrefs)

        new_signatures_names = dict((new, get_name_by_bibref(new))
                                    for new in new_signatures)

        # matrix |new_signatures| X |old_signatures|
        matrix = [[compare_names(new_signatures_names[new],
                                 personidrefs_names[old])
                   for old in old_signatures] for new in new_signatures]

        logger.log(" - Deleted signatures: %s" % str(old_signatures))
        logger.log(" - Added signatures: %s" % str(new_signatures))
        logger.log(" - Matrix: %s" % str(matrix))

        #[new_signatures, old_signatures]
        best_match = [(new_signatures[new], old_signatures[old])
                      for new, old, score in maximized_mapping(matrix)
                      if score > threshold]

        logger.log(" - Best match: %s " % str(best_match))

        for new, old in best_match:
            logger.log("  -  -  Moving signature: %s on %s to %s as %s" %
                      (old, rec, new, new_signatures_names[new]))
            modify_signature(old, rec, new, new_signatures_names[new])

        remove_signatures(tuple(list(old) + [rec]) for old in old_signatures)
        not_matched = frozenset(new_signatures) - frozenset(map(itemgetter(0),
                                                                best_match))

        remaining_personid_rows = ([x for x in personid_rows
                                    if x[1:3] in old_signatures])

        pids_having_rec = set([int(row[0]) for row in remaining_personid_rows])
        logger.log(" - Not matched: %s" % str(not_matched))

        if not_matched:
            used_pids = set(r[0] for r in personid_rows)

        for sig in not_matched:
            name = new_signatures_names[sig]
            matchable_name = create_matchable_name(name)
            matched_pids = list()
            if USE_EXT_IDS:
                matched_pids = get_matched_pids_by_external_ids(sig, rec, pids_having_rec)

                if matched_pids:
                    add_signature(list(sig) + [rec], name,
                                  matched_pids[0][0], m_name=matchable_name)
                    M_NAME_PIDS_CACHE[matchable_name] = matched_pids[0][0]
                    updated_pids.add(matched_pids[0][0])
                    pids_having_rec.add(matched_pids[0][0])
                    continue

            matched_pids = find_pids_by_matchable_name_with_cache(matchable_name)
            if not matched_pids:
                for matching_function in M_NAME_FUNCTIONS[1:]:
                    matchable_name = matching_function(name)
                    matched_pids = find_pids_by_matchable_name_with_cache(matchable_name)
                    if matched_pids:
                        break

            matched_pids = [p for p in matched_pids if int(p) not in used_pids]

            if not matched_pids or int(matched_pids[0]) in pids_having_rec:
                new_pid = new_person_from_signature(list(sig) + [rec],
                                                    name, matchable_name)
                M_NAME_PIDS_CACHE[matchable_name] = new_pid
                used_pids.add(new_pid)
                updated_pids.add(new_pid)
            else:
                add_signature(list(sig) + [rec], name,
                              matched_pids[0], m_name=matchable_name)
                M_NAME_PIDS_CACHE[matchable_name] = matched_pids[0]
                used_pids.add(matched_pids[0])
                updated_pids.add(matched_pids[0])
                pids_having_rec.add(matched_pids[0])

        logger.log('Finished with %s' % str(rec))

    logger.update_status_final()

    destroy_partial_marc_caches()

    if personids_to_update_extids:
        updated_pids |= set(personids_to_update_extids)
    if updated_pids:  # an empty set will update all canonical_names
        update_canonical_names_of_authors(updated_pids)
        update_external_ids_of_authors(updated_pids,
                                       limit_to_claimed_papers=bconfig.LIMIT_EXTERNAL_IDS_COLLECTION_TO_CLAIMED_PAPERS,
                                       force_cache_tables=True)

    destroy_partial_marc_caches()
    destroy_mnames_pids_cache()

    remove_empty_authors()

    task_update_progress("Done!")

