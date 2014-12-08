# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

"""Implementation of sorting engine."""

from intbitset import intbitset

from invenio.base.globals import cfg
from invenio.legacy.bibrank.record_sorter import rank_records
from invenio.legacy.bibrecord import get_fieldvalues
from invenio.legacy.search_engine import get_interval_for_records_to_sort
from invenio.legacy.search_engine import slice_records
from invenio.utils.text import strip_accents
from invenio.modules.search.models import Field

from .cache import SORTING_METHODS, CACHE_SORTED_DATA


def get_tags_from_sort_fields(sort_fields):
    """Return the tags associated with sort fields.

    The second item in tuple contains the name of the field that has no tags
    associated.
    """
    tags = []
    if not sort_fields:
        return [], ''
    for sort_field in sort_fields:
        if sort_field and (
                len(sort_field) > 1 and str(sort_field[0:2]).isdigit()):
            # sort_field starts by two digits, so this is probably
            # a MARC tag already
            tags.append(sort_field)
        else:
            # let us check the 'field' table
            field_tags = Field.get_field_tags(sort_field)
            if field_tags:
                tags.extend(field_tags)
            else:
                return [], sort_field
    return tags, ''


def sort_records(recIDs, sort_field='', sort_order='a', sort_pattern='',
                 rg=None, jrec=None, sorting_methods=None):
    """Initial entry point for sorting records, acts like a dispatcher.

    1. sort_field is in the bsrMETHOD, and thus, the BibSort has sorted the
       data for this field, so we can use the cache;

    2. sort_field is not in bsrMETHOD, and thus, the cache does not contain
       any information regarding this sorting method.
    """
    sorting_methods = sorting_methods or SORTING_METHODS

    # bibsort does not handle sort_pattern for now, use bibxxx
    if sort_pattern:
        return sort_records_bibxxx(recIDs, None, sort_field, sort_order,
                                   sort_pattern, rg=rg, jrec=jrec)

    # ignore the use of buckets, use old fashion sorting
    use_sorting_buckets = cfg['CFG_BIBSORT_ENABLED']

    # Default sorting
    if not sort_field:
        if use_sorting_buckets:
            return sort_records_bibsort(
                recIDs, cfg['CFG_BIBSORT_DEFAULT_FIELD'], sort_field,
                cfg['CFG_BIBSORT_DEFAULT_FIELD_ORDER'], rg, jrec)
        else:
            if sort_order == 'd':
                recIDs.reverse()
            return slice_records(recIDs, jrec, rg)

    sort_fields = sort_field.split(",")
    if len(sort_fields) == 1:
        # we have only one sorting_field, check if it is treated by BibSort
        for sort_method in sorting_methods:
            definition = sorting_methods[sort_method]
            if use_sorting_buckets and ((
                    definition.startswith('FIELD') and definition.replace(
                        'FIELD:', '').strip().lower() == sort_fields[0].lower()
                    ) or sort_method == sort_fields[0]):
                # use BibSort
                return sort_records_bibsort(recIDs, sort_method, sort_field,
                                            sort_order, rg, jrec)
    # deduce sorting MARC tag out of the 'sort_field' argument:
    tags, error_field = get_tags_from_sort_fields(sort_fields)
    if error_field:
        if use_sorting_buckets:
            return sort_records_bibsort(
                recIDs, cfg['CFG_BIBSORT_DEFAULT_FIELD'], sort_field,
                sort_order, rg, jrec)
        else:
            return slice_records(recIDs, jrec, rg)
    elif tags:
        for sort_method in sorting_methods:
            definition = sorting_methods[sort_method]
            if definition.startswith('MARC') and \
                    definition.replace(
                        'MARC:', '').strip().split(',') == tags \
                    and use_sorting_buckets:
                # this list of tags have a designated method in BibSort
                return sort_records_bibsort(recIDs, sort_method, sort_field,
                                            sort_order, rg, jrec)
        # we do not have this sort_field in BibSort tables
        # -> do the old fashion sorting
        return sort_records_bibxxx(recIDs, tags, sort_field, sort_order,
                                   sort_pattern, rg, jrec)
    else:
        return slice_records(recIDs, jrec, rg)


def sort_records_bibsort(recIDs, sort_method, sort_field='', sort_order='d',
                         rg=None, jrec=1, sort_or_rank='s',
                         sorting_methods=SORTING_METHODS):
    """Order the list based on a sorting method using the BibSortDataCacher."""
    sorting_methods = sorting_methods or SORTING_METHODS

    if not jrec:
        jrec = 1

    # sanity check
    if sort_method not in sorting_methods:
        if sort_or_rank == 'r':
            return rank_records(rank_method_code=sort_method,
                                rank_limit_relevance=0,
                                hitset=recIDs)
        else:
            return sort_records_bibxxx(recIDs, None, sort_field, sort_order,
                                       '', rg, jrec)

    # we should return sorted records up to irec_max(exclusive)
    dummy, irec_max = get_interval_for_records_to_sort(len(recIDs), jrec, rg)
    solution = intbitset()
    input_recids = intbitset(recIDs)
    CACHE_SORTED_DATA[sort_method].recreate_cache_if_needed()
    sort_cache = CACHE_SORTED_DATA[sort_method].cache
    bucket_numbers = sort_cache['bucket_data'].keys()
    # check if all buckets have been constructed
    if len(bucket_numbers) != cfg['CFG_BIBSORT_BUCKETS']:
        if sort_or_rank == 'r':
            return rank_records(rank_method_code=sort_method,
                                rank_limit_relevance=0, hitset=recIDs)
        else:
            return sort_records_bibxxx(recIDs, None, sort_field,
                                       sort_order, rg=rg, jrec=jrec)

    if sort_order == 'd':
        bucket_numbers.reverse()
    for bucket_no in bucket_numbers:
        solution.union_update(
            input_recids & sort_cache['bucket_data'][bucket_no]
        )
        if len(solution) >= irec_max:
            break

    dict_solution = {}
    missing_records = intbitset()
    for recid in solution:
        try:
            dict_solution[recid] = sort_cache['data_dict_ordered'][recid]
        except KeyError:
            # recid is in buckets, but not in the bsrMETHODDATA,
            # maybe because the value has been deleted, but the change has not
            # yet been propagated to the buckets
            missing_records.add(recid)

    # check if there are recids that are not in any bucket -> to be added at
    # the end/top, ordered by insertion date
    if len(solution) < irec_max:
        # some records have not been yet inserted in the bibsort structures
        # or, some records have no value for the sort_method
        missing_records += input_recids - solution

    reverse = sort_order == 'd'

    if sort_method.strip().lower() == cfg['CFG_BIBSORT_DEFAULT_FIELD'] and \
            reverse:
        # If we want to sort the records on their insertion date, add the
        # missing records at the top.
        solution = sorted(missing_records, reverse=True) + \
            sorted(dict_solution, key=dict_solution.__getitem__, reverse=True)
    else:
        solution = sorted(dict_solution, key=dict_solution.__getitem__,
                          reverse=reverse) + sorted(missing_records)

    # Only keep records, we are going to display
    solution = slice_records(solution, jrec, rg)

    if sort_or_rank == 'r':
        # We need the recids, with their ranking score
        return solution, [dict_solution.get(record, 0) for record in solution]
    else:
        return solution


def sort_records_bibxxx(recIDs, tags, sort_field='', sort_order='d',
                        sort_pattern='', rg=None, jrec=None):
    """Sort record list according sort field in given order.

    If more than one instance of 'sort_field' is found for a given record, try
    to choose that that is given by 'sort pattern', for example "sort by report
    number that starts by CERN-PS".  Note that 'sort_field' can be field code
    like 'author' or MARC tag like '100__a' directly.
    """
    # check arguments:
    if not sort_field:
        return slice_records(recIDs, jrec, rg)

    if len(recIDs) > cfg['CFG_WEBSEARCH_NB_RECORDS_TO_SORT']:
        return slice_records(recIDs, jrec, rg)

    recIDs_dict = {}
    recIDs_out = []

    if not tags:
        # tags have not been camputed yet
        sort_fields = sort_field.split(',')
        tags, error_field = get_tags_from_sort_fields(sort_fields)
        if error_field:
            return slice_records(recIDs, jrec, rg)

    # check if we have sorting tag defined:
    if tags:
        # fetch the necessary field values:
        for recID in recIDs:
            val = ""  # will hold value for recID according to which sort
            vals = []  # will hold all values found in sorting tag for recID
            for tag in tags:
                if cfg['CFG_CERN_SITE'] and tag == '773__c':
                    # CERN hack: journal sorting
                    # 773__c contains page numbers, e.g. 3-13,
                    # and we want to sort by 3, and numerically:
                    vals.extend([
                        "%050s" % x.split("-", 1)[0]
                        for x in get_fieldvalues(recID, tag)])
                else:
                    vals.extend(get_fieldvalues(recID, tag))
            if sort_pattern:
                # try to pick that tag value that corresponds to sort pattern
                bingo = 0
                for v in vals:
                    if v.lower().startswith(sort_pattern.lower()):  # bingo!
                        bingo = 1
                        val = v
                        break
                if not bingo:
                    # sort_pattern not present, so add other vals after spaces
                    val = sort_pattern + "          " + ''.join(vals)
            else:
                # no sort pattern defined, so join them all together
                val = ''.join(vals)
            # sort values regardless of accents and case
            val = strip_accents(val.lower())
            if val in recIDs_dict:
                recIDs_dict[val].append(recID)
            else:
                recIDs_dict[val] = [recID]

        # create output array:
        for k in sorted(recIDs_dict.keys()):
            recIDs_out.extend(recIDs_dict[k])

        # ascending or descending?
        if sort_order == 'd':
            recIDs_out.reverse()

        recIDs = recIDs_out

    # return only up to the maximum that we need
    return slice_records(recIDs, jrec, rg)
