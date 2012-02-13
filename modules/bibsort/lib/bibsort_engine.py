## -*- mode: python; coding: utf-8; -*-
##
## This file is part of Invenio.
## Copyright (C) 2010, 2011, 2012 CERN.
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

"""BibSort Engine"""

import sys
import time
from invenio.dbquery import deserialize_via_marshal, \
serialize_via_marshal, run_sql, Error
from invenio.search_engine import get_field_tags, search_pattern
from invenio.intbitset import intbitset
from invenio.bibtask import write_message, task_update_progress, \
task_sleep_now_if_required
from invenio.config import CFG_BIBSORT_BUCKETS, CFG_CERN_SITE
from bibsort_washer import BibSortWasher, \
InvenioBibSortWasherNotImplementedError

import invenio.template
websearch_templates = invenio.template.load('websearch')

#The space distance between elements, to make inserts faster
CFG_BIBSORT_WEIGHT_DISTANCE = 8


def get_bibsort_methods_details(method_list = None):
    """Returns the id, definition, and washer for the methods in method_list.
    If no method_list is specified: we get all the data from bsrMETHOD table"""
    bibsort_methods = {}
    errors = False
    results = []
    if not method_list:
        try:
            results = run_sql("SELECT id, name, definition, washer \
                              FROM bsrMETHOD")
        except Error, err:
            write_message("The error: [%s] occured while trying to read " \
                          "the bibsort data from the database." \
                          %err, stream=sys.stderr)
            return {}, True
        if not results:
            write_message("The bsrMETHOD table is empty.")
            return {}, errors
    else:
        for method in method_list:
            try:
                res = run_sql("""SELECT id, name, definition, washer \
                              FROM bsrMETHOD where name = %s""", (method, ))
            except Error, err:
                write_message("The error: [%s] occured while trying to get " \
                              "the bibsort data from the database for method %s." \
                              %(err, method), stream=sys.stderr)
                errors = True
            if not res:
                write_message("No information for method: %s." % method)
            else:
                results.append(res[0])
    for item in results:
        bibsort_methods.setdefault(item[1], {})['id'] = item[0]
        bibsort_methods[item[1]]['definition'] = item[2]
        bibsort_methods[item[1]]['washer'] = item[3]
    return bibsort_methods, errors


def get_all_recids(including_deleted=True):#6.68s on cdsdev
    """Returns a list of all records available in the system"""
    res = run_sql("SELECT id FROM bibrec")
    if not res:
        return intbitset([])
    all_recs = intbitset(res)
    if not including_deleted: # we want to exclude deleted records
        if CFG_CERN_SITE:
            deleted = search_pattern(p='980__:"DELETED" OR 980__:"DUMMY"')
        else:
            deleted = search_pattern(p='980__:"DELETED"')
        all_recs.difference_update(deleted)
    return all_recs


def get_max_recid():
    """Returns the max id in bibrec - good approximation
    for the total number of records"""
    try:
        return run_sql("SELECT MAX(id) FROM bibrec")[0][0]
    except IndexError:
        return 0


def _get_values_from_marc_tag(tag, recids):
    '''Finds the value for a specific tag'''
    digits = tag[0:2]
    try:
        intdigits = int(digits)
        if intdigits < 0 or intdigits > 99:
            raise ValueError
    except ValueError:
        # invalid tag value asked for
        write_message('You have asked for an invalid tag value ' \
                      '[tag=%s; value=%s].' %(tag, intdigits), verbose=5)
        return []
    bx = "bib%sx" % digits
    bibx = "bibrec_bib%sx" % digits
    max_recid = get_max_recid()

    if len(recids) == 1:
        to_append = '= %s'
        query_params = [recids.tolist()[0]]

    elif len(recids) < max_recid/3:
        # if we have less then one third of the records
        # use IN
        #This realy depends on how large the repository is..
        to_append = 'IN %s'
        query_params = [tuple(recids)]

    else:
       # mysql might crush with big queries, better use BETWEEN
        to_append = 'BETWEEN %s AND %s'
        query_params = [1, max_recid]

    query = 'SELECT bibx.id_bibrec, bx.value \
                    FROM %s AS bx, %s AS bibx \
                    WHERE bibx.id_bibrec %s \
                    AND bx.id = bibx.id_bibxxx \
                    AND bx.tag LIKE %%s' % (bx, bibx, to_append)
    query_params.append(tag)
    res = run_sql(query, tuple(query_params))
    return res


def get_data_for_definition_marc(tags, recids):
    '''Having a list of tags and a list of recids, it returns a dictionary
    with the values correspondig to the tags'''
    #x = all_recids; [get_fieldvalues(recid, '037__a') for recid in x]
    #user: 140s, sys: 21s, total: 160s - cdsdev
    if isinstance(recids, (int, long)):
        recids = intbitset([recids, ])
    # for each recid we need only one value
    #on which we sort, so we can stop looking for a value
    # as soon as we find one
    tag_index = 0
    field_data_dict = {}
    while len(recids) > 0 and tag_index < len(tags):
        write_message('%s records queried for values for tags %s.' \
                      %(len(recids), tags), verbose=5)
        res = _get_values_from_marc_tag(tags[tag_index], recids)
        res_dict = dict(res)
        #field_data_dict.update(res_dict)
        #we can not use this, because res_dict might contain recids
        #that are already in field_data_dict, and we should not overwrite their value
        field_data_dict = dict(res_dict, **field_data_dict)
        #there might be keys that we do not want (ex: using 'between')
        #so we should remove them
        res_dict_keys = intbitset(res_dict.keys())
        recids_not_needed = res_dict_keys.difference(recids)
        for recid in recids_not_needed:
            del field_data_dict[recid]
        #update the recids to contain only the recid that do not have values yet
        recids.difference_update(res_dict_keys)
        tag_index += 1
    return field_data_dict


def get_data_for_definition_rnk(method_name, rnk_name):
    '''Returns the dictionary with data for method_name ranking method'''
    try:
        res = run_sql('SELECT d.relevance_data \
                          from rnkMETHODDATA d, rnkMETHOD r WHERE \
                          d.id_rnkMETHOD = r.id AND \
                          r.name = %s', (rnk_name, ))
        if res and res[0]:
            write_message('Data extracted from table rnkMETHODDATA for sorting method %s' \
                          %method_name, verbose=5)
            return deserialize_via_marshal(res[0][0])
    except Error, err:
        write_message("No data could be found for sorting method %s. " \
                      "The following errror occured: [%s]" \
                      %(method_name, err), stream=sys.stderr)
        return {}


def get_data_for_definition_bibrec(column_name, recids_copy):
    '''Having a column_name and a list of recids, it returns a dictionary
    mapping each recids with its correspondig value from the column'''
    dict_column = {}
    for recid in recids_copy:
        creation_date = run_sql('SELECT %s from bibrec WHERE id = %%s' %column_name, (recid, ))[0][0]
        dict_column[recid] = creation_date.strftime('%Y%m%d%H%M%S')
    return dict_column


def get_field_data(recids, method_name, definition):
    """Returns the data associated with the definition for recids.
    The returned dictionary will contain ONLY the recids for which
    a value has been found in the database.
    """
    recids_copy = recids.copy()
    #if we are dealing with a MARC definition
    if definition.startswith('MARC'):
        tags = definition.replace('MARC:', '').replace(' ', '').strip().split(',')
        if not tags:
            write_message('No MARC tags found for method %s.' \
                          %method_name, verbose=5)
            return {}
        write_message('The following MARC tags will be queried: %s' %tags, \
                      verbose=5)
        return get_data_for_definition_marc(tags, recids_copy)
    #if we are dealing with tags (ex: author, title)
    elif definition.startswith('FIELD'):
        tags = get_field_tags(definition.replace('FIELD:', '').strip())
        if not tags:
            write_message('No tags found for method %s.' \
                          %method_name, verbose=5)
            return {}
        write_message('The following tags will be queried: %s' %tags, verbose=5)
        return get_data_for_definition_marc(tags, recids_copy)
    # if we are dealing with ranking data
    elif definition.startswith('RNK'):
        rnk_name = definition.replace('RNK:', '').strip()
        return get_data_for_definition_rnk(method_name, rnk_name)
    # if we are looking into bibrec table
    elif definition.startswith('BIBREC'):
        column_name = definition.replace('BIBREC:', '').strip()
        return get_data_for_definition_bibrec(column_name, recids_copy)
    else:
        write_message("The definition %s for method % could not be recognized" \
                      %(definition, method_name), stream=sys.stderr)
        return {}


def apply_washer(data_dict, washer):
    '''The values are filtered using the washer function'''
    if not washer:
        return
    if washer.strip() == 'NOOP':
        return
    washer = washer.split(':')[0]#in case we have a locale defined
    try:
        method = BibSortWasher(washer)
        write_message('Washer method found: %s' %washer, verbose=5)
        for recid in data_dict:
            new_val = method.get_transformed_value(data_dict[recid])
            data_dict[recid] = new_val
    except InvenioBibSortWasherNotImplementedError, err:
        write_message("Washer %s is not implemented [%s]." \
                      %(washer, err), stream=sys.stderr)

def locale_for_sorting(washer):
    """Identifies if any specific locale should be used, and it returns it"""
    if washer.find(":") > -1:
        lang = washer[washer.index(':')+1:]
        return websearch_templates.tmpl_localemap.get(lang, websearch_templates.tmpl_default_locale)
    return None

def run_sorting_method(recids, method_name, method_id, definition, washer):
    """Does the actual sorting for the method_name
    for all the records in the database"""
    run_sorting_for_rnk = False
    if definition.startswith('RNK'):
        run_sorting_for_rnk = True
    field_data_dictionary = get_field_data(recids, method_name, definition)
    if not field_data_dictionary:
        write_message("POSSIBLE ERROR: The sorting method --%s-- has no data!" \
                      %method_name)
        return True
    apply_washer(field_data_dictionary, washer)
    #do we have any locale constraint?
    sorting_locale = locale_for_sorting(washer)
    sorted_data_list, sorted_data_dict = \
                sort_dict(field_data_dictionary, CFG_BIBSORT_WEIGHT_DISTANCE, run_sorting_for_rnk, sorting_locale)
    executed = write_to_methoddata_table(method_id, field_data_dictionary, \
                                         sorted_data_dict, sorted_data_list)
    if not executed:
        return False
    if CFG_BIBSORT_BUCKETS > 1:
        bucket_dict, bucket_last_rec_dict = split_into_buckets(sorted_data_list, len(sorted_data_list))
        for idx in bucket_dict:
            executed = write_to_buckets_table(method_id, idx, bucket_dict[idx], \
                                              sorted_data_dict[bucket_last_rec_dict[idx]])
            if not executed:
                return False
    else:
        executed = write_to_buckets_table(method_id, 1, intbitset(sorted_data_list), \
                                          sorted_data_list[-1])
        if not executed:
            return False
    return True


def write_to_methoddata_table(id_method, data_dict, data_dict_ordered, data_list_sorted, update_timestamp=True):
    """Serialize the date and write it to the bsrMETHODDATA"""
    write_message('Starting serializing the data..', verbose=5)
    serialized_data_dict = serialize_via_marshal(data_dict)
    serialized_data_dict_ordered = serialize_via_marshal(data_dict_ordered)
    serialized_data_list_sorted = serialize_via_marshal(data_list_sorted)
    write_message('Serialization completed.', verbose=5)
    date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    if not update_timestamp:
        try:
            date = run_sql('SELECT last_update from bsrMETHODDATA WHERE id_bsrMETHOD = %s', (id_method, ))[0][0]
        except IndexError:
            pass # keep the generated date
    write_message("Starting writing the data for method_id=%s " \
                  "to the database (table bsrMETHODDATA)" %id_method, verbose=5)
    try:
        write_message('Deleting old data..', verbose=5)
        run_sql("DELETE FROM bsrMETHODDATA WHERE id_bsrMETHOD = %s", (id_method, ))
        write_message('Inserting new data..', verbose=5)
        run_sql("INSERT into bsrMETHODDATA \
            (id_bsrMETHOD, data_dict, data_dict_ordered, data_list_sorted, last_updated) \
            VALUES (%s, %s, %s, %s, %s)", \
            (id_method, serialized_data_dict, serialized_data_dict_ordered, \
             serialized_data_list_sorted, date, ))
    except Error, err:
        write_message("The error [%s] occured when inserting new bibsort data "\
                      "into bsrMETHODATA table" %err, sys.stderr)
        return False
    write_message('Writing to the bsrMETHODDATA successfully completed.', \
                  verbose=5)
    return True


def write_to_buckets_table(id_method, bucket_no, bucket_data, bucket_last_value, update_timestamp=True):
    """Serialize the date and write it to the bsrMEHODDATA_BUCKETS"""
    write_message('Writing the data for bucket number %s for ' \
                  'method_id=%s to the database' \
                  %(bucket_no, id_method), verbose=5)
    write_message('Serializing data for bucket number %s' %bucket_no, verbose=5)
    serialized_bucket_data = bucket_data.fastdump()
    date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    if not update_timestamp:
        try:
            date = run_sql('SELECT last_update from bsrMETHODDATABUCKET WHERE id_bsrMETHOD = %s and bucket_no = %s', \
                           (id_method, bucket_no))[0][0]
        except IndexError:
            pass # keep the generated date
    try:
        write_message('Deleting old data.', verbose=5)
        run_sql("DELETE FROM bsrMETHODDATABUCKET \
                WHERE id_bsrMETHOD = %s AND bucket_no = %s", \
                (id_method, bucket_no, ))
        write_message('Inserting new data.', verbose=5)
        run_sql("INSERT into bsrMETHODDATABUCKET \
            (id_bsrMETHOD, bucket_no, bucket_data, bucket_last_value, last_updated) \
            VALUES (%s, %s, %s, %s, %s)", \
            (id_method, bucket_no, serialized_bucket_data, bucket_last_value, date, ))
    except Error, err:
        write_message("The error [%s] occured when inserting new bibsort data " \
                      "into bsrMETHODATA_BUCKETS table" %err, sys.stderr)
        return False
    write_message('Writing to bsrMETHODDATABUCKET for ' \
                  'bucket number %s completed.' %bucket_no, verbose=5)
    return True


def split_into_buckets(sorted_data_list, data_size):
    """The sorted_data_list is split into equal buckets.
    Returns a dictionary containing the buckets and
    a dictionary containing the last record in each bucket"""
    write_message("Starting splitting the data into %s buckets." \
                  %CFG_BIBSORT_BUCKETS, verbose=5)
    bucket_dict = {}
    bucket_last_rec_dict = {}
    step = data_size/CFG_BIBSORT_BUCKETS
    i = 0
    for i in xrange(CFG_BIBSORT_BUCKETS - 1):
        bucket_dict[i+1] = intbitset(sorted_data_list[i*step:i*step+step])
        bucket_last_rec_dict[i+1] = sorted_data_list[i*step+step-1]
        write_message("Bucket %s done." %(i+1), verbose=5)
    #last bucket contains all the remaining data
    bucket_dict[CFG_BIBSORT_BUCKETS] = intbitset(sorted_data_list[(i+1)*step:])
    bucket_last_rec_dict[CFG_BIBSORT_BUCKETS] = sorted_data_list[-1]
    write_message("Bucket %s done." %CFG_BIBSORT_BUCKETS, verbose=5)
    write_message("Splitting completed.", verbose=5)
    return bucket_dict, bucket_last_rec_dict


def sort_dict(dictionary, spacing=1, run_sorting_for_rnk=False, sorting_locale=None):
    """Sorting a dictionary. Returns a list of sorted recids
    and also a dictionary containing the recid: weight
    weight = index * spacing"""
    #10Mil records dictionary -> 36.9s
    write_message("Starting sorting the dictionary " \
                  "containing all the data..", verbose=5)
    sorted_records_dict_with_id = {}

    if sorting_locale:
        import locale
        orig_locale = locale.getlocale(locale.LC_ALL)
        try:
            locale.setlocale(locale.LC_ALL, sorting_locale)
        except locale.Error:
            try:
                locale.setlocale(locale.LC_ALL, sorting_locale + '.UTF8')
            except locale.Error:
                write_message("Setting locale to %s is not working.. ignoring locale")
        sorted_records_list = sorted(dictionary, key=dictionary.__getitem__, cmp=locale.strcoll, reverse=False)
        locale.setlocale(locale.LC_ALL, orig_locale)
    else:
        sorted_records_list = sorted(dictionary, key=dictionary.__getitem__, reverse=False)

    if run_sorting_for_rnk:
        #for ranking, we can keep the actual values associated with the recids
        return sorted_records_list, dictionary
    else:
        index = 1
        for recid in sorted_records_list:
            sorted_records_dict_with_id[recid] = index * spacing
            index += 1
    write_message("Dictionary sorted.", verbose=5)
    return sorted_records_list, sorted_records_dict_with_id


def get_modified_or_inserted_recs(method_list):
    """Returns a list of recids that have been inserted or
    modified since the last update of the bibsort methods in method_list
    method_list should already contain a list of methods that
    SHOULD be updated, if it contains new methods, an error will be thrown"""

    if not method_list: #just to be on the safe side
        return 0

    try:
        query = "SELECT min(d.last_updated) from bsrMETHODDATA d, bsrMETHOD m \
                WHERE m.name in (%s) AND d.id_bsrMETHOD = m.id" % \
                ("%s," * len(method_list))[:-1]
        last_updated = str(run_sql(query, tuple(method_list))[0][0])
    except Error, err:
        write_message("Error when trying to get the last_updated date " \
                      "from bsrMETHODDATA: [%s]" %err, sys.stderr)
        return 0
    recids = []
    try:
        results = run_sql("SELECT id from bibrec \
                          where modification_date >= %s", (last_updated, ))
        if results:
            recids = [result[0] for result in results]
    except Error, err:
        write_message("Error when trying to get the list of " \
                      "modified records: [%s]" %err, sys.stderr)
        return 0
    return recids


def get_rnk_methods(bibsort_methods):
    """Returns the list of bibsort methods (names) that are RNK methods"""
    return [method for method in bibsort_methods if \
            bibsort_methods[method]['definition'].startswith('RNK')]


def get_modified_non_rnk_methods(non_rnk_method_list):
    """Returns 2 lists of non RNK methods:
    updated_ranking_methods = non RNK methods that need to be updated
    inserted_ranking_methods = non RNK methods, that have no data yet,
    so rebalancing should run on them"""
    updated_ranking_methods = []
    inserted_ranking_methods = []
    for method in non_rnk_method_list:
        try:
            dummy = str(run_sql('SELECT d.last_updated \
                                       FROM bsrMETHODDATA d, bsrMETHOD m \
                                       WHERE m.id = d.id_bsrMETHOD \
                                       AND m.name=%s', (method, ))[0][0])
            updated_ranking_methods.append(method)
        except IndexError: #method is not in bsrMETHODDATA -> is new
            inserted_ranking_methods.append(method)
    return updated_ranking_methods, inserted_ranking_methods


def get_modified_rnk_methods(rnk_method_list, bibsort_methods):
    """Returns the list of RNK methods that have been recently modified,
    so they will need to have their bibsort data updated"""
    updated_ranking_methods = []
    deleted_ranking_methods = []
    for method in rnk_method_list:
        method_name = bibsort_methods[method]['definition'].replace('RNK:', '').strip()
        try:
            last_updated_rnk = str(run_sql('SELECT last_updated \
                                           FROM rnkMETHOD \
                                           WHERE name = %s', (method_name, ))[0][0])
        except IndexError:
            write_message("The method %s could not be found in rnkMETHOD" \
                      %(method_name), stream=sys.stderr)
            #this method does not exist in rnkMETHOD,
            #it might have been a mistype or it might have been deleted
            deleted_ranking_methods.append(method)
        if method not in deleted_ranking_methods:
            try:
                last_updated_bsr = str(run_sql('SELECT d.last_updated \
                                       FROM bsrMETHODDATA d, bsrMETHOD m \
                                       WHERE m.id = d.id_bsrMETHOD \
                                       AND m.name=%s', (method, ))[0][0])
                if last_updated_rnk >= last_updated_bsr:
                    # rnk data has been updated after bibsort ran
                    updated_ranking_methods.append(method)
                else:
                    write_message("The method %s has not been updated "\
                                  "since the last run of bibsort." %method)
            except IndexError:
                write_message("The method %s could not be found in bsrMETHODDATA" \
                      %(method))
                # that means that the bibsort never run on this method, so let's run it
                updated_ranking_methods.append(method)

    return updated_ranking_methods, deleted_ranking_methods


def delete_bibsort_data_for_method(method_id):
    """This method will delete all data asociated with a method
    from bibsort tables (except bsrMETHOD).
    Returns False in case some error occured, True otherwise"""
    try:
        run_sql("DELETE FROM bsrMETHODDATA WHERE id_bsrMETHOD = %s", (method_id, ))
        run_sql("DELETE FROM bsrMETHODDATABUCKET WHERE id_bsrMETHOD = %s", (method_id, ))
    except:
        return False
    return True

def delete_all_data_for_method(method_id):
    """This method will delete all data asociated with a method
    from bibsort tables.
    Returns False in case some error occured, True otherwise"""
    method_name = 'method name'
    try:
        run_sql("DELETE FROM bsrMETHODDATA WHERE id_bsrMETHOD = %s", (method_id, ))
        run_sql("DELETE FROM bsrMETHODDATABUCKET WHERE id_bsrMETHOD = %s", (method_id, ))
        run_sql("DELETE FROM bsrMETHODNAME WHERE id_bsrMETHOD = %s", (method_id, ))
        run_sql("DELETE FROM bsrMETHOD WHERE id = %s", (method_id, ))
        method_name = run_sql("SELECT name from bsrMETHOD WHERE id = %s", (method_id, ))[0][0]
    except Error:
        return False
    except IndexError:
        return True
    if method_name:# the method has not been deleted
        return False
    return True

def add_sorting_method(method_name, method_definition, method_treatment):
    """This method will add a new sorting method in the database
    and update the config file"""
    try:
        run_sql("INSERT INTO bsrMETHOD(name, definition, washer) \
            VALUES (%s, %s, %s)", (method_name, method_definition, method_treatment))
    except Error:
        return False
    return True

def update_bibsort_tables(recids, method, update_timestamp = True):
    """Updates the data structures for sorting method: method
    for the records in recids"""

    res = run_sql("SELECT id, definition, washer \
                  from bsrMETHOD where name = %s", (method, ))
    if res and res[0]:
        method_id = res[0][0]
        definition = res[0][1]
        washer = res[0][2]
    else:
        write_message('No sorting method called %s could be found ' \
                      'in bsrMETHOD table.' %method, sys.stderr)
        return False
    res = run_sql("SELECT data_dict, data_dict_ordered, data_list_sorted \
                  FROM bsrMETHODDATA where id_bsrMETHOD = %s", (method_id, ))
    if res and res[0]:
        data_dict = deserialize_via_marshal(res[0][0])
        data_dict_ordered = {}
        data_list_sorted = []
    else:
        write_message('No data could be found for the sorting method %s.' \
                      %method)
        return False #since this case should have been treated earlier
    #get the values for the recids that need to be recalculated
    field_data = get_field_data(recids, method, definition)
    if not field_data:
        write_message("Possible error: the method %s has no data for records %s." \
                      %(method, str(recids)))
    else:
        apply_washer(field_data, washer)

    #if a recid is not in field_data that is because no value was found for it
    #so it should be marked for deletion
    recids_to_delete = list(recids.difference(intbitset(field_data.keys())))
    recids_to_insert = []
    recids_to_modify = {}
    for recid in field_data:
        if recid in data_dict:
            if data_dict[recid] != field_data[recid]:
                #we store the old value
                recids_to_modify[recid] = data_dict[recid]
        else: # recid is new, and needs to be inserted
            recids_to_insert.append(recid)

    #remove the recids that were not previously in bibsort
    recids_to_delete = [recid for recid in recids_to_delete if recid in data_dict]

    #dicts to keep the ordered values for the recids - useful bor bucket insertion
    recids_current_ordered = {}
    recids_old_ordered = {}

    if recids_to_insert or recids_to_modify or recids_to_delete:
        data_dict_ordered = deserialize_via_marshal(res[0][1])
        data_list_sorted = deserialize_via_marshal(res[0][2])
        if recids_to_modify:
            write_message("%s records have been modified." \
                          %len(recids_to_modify), verbose=5)
            for recid in recids_to_modify:
                recids_old_ordered[recid] = data_dict_ordered[recid]
                perform_modify_record(data_dict, data_dict_ordered, \
                                data_list_sorted, field_data[recid], recid)
        if recids_to_insert:
            write_message("%s records have been inserted." \
                          %len(recids_to_insert), verbose=5)
            for recid in recids_to_insert:
                perform_insert_record(data_dict, data_dict_ordered, \
                                data_list_sorted, field_data[recid], recid)
        if recids_to_delete:
            write_message("%s records have been deleted." \
                          %len(recids_to_delete), verbose=5)
            for recid in recids_to_delete:
                perform_delete_record(data_dict, data_dict_ordered, data_list_sorted, recid)

        for recid in recids_to_modify:
            recids_current_ordered[recid] = data_dict_ordered[recid]
        for recid in recids_to_insert:
            recids_current_ordered[recid] = data_dict_ordered[recid]

        #write the modifications to db
        executed = write_to_methoddata_table(method_id, data_dict, \
                                         data_dict_ordered, data_list_sorted, update_timestamp)
        if not executed:
            return False

        #update buckets
        try:
            perform_update_buckets(recids_current_ordered, recids_to_insert, recids_old_ordered, method_id, update_timestamp)
        except Error, err:
            write_message("[%s] The bucket data for method %s has not been updated" \
                          %(method, err), sys.stderr)
            return False
    return True


def perform_update_buckets(recids_current_ordered, recids_to_insert, recids_old_ordered, method_id, update_timestamp = True):
    """Updates the buckets"""
    bucket_insert = {}
    bucket_delete = {}
    write_message("Updating the buckets for method_id = %s" %method_id, verbose=5)
    buckets = run_sql("SELECT bucket_no, bucket_last_value \
                      FROM bsrMETHODDATABUCKET \
                      WHERE id_bsrMETHOD = %s", (method_id, ))
    if not buckets:
        write_message("No bucket data found for method_id %s." \
                      %method_id, sys.stderr)
        raise Exception
    #sort the buckets to be sure we are iterating them in order(1 to max):
    buckets_dict = dict(buckets)
    for recid in recids_to_insert:
        for bucket_no in buckets_dict:
            if recids_current_ordered[recid] <= buckets_dict[bucket_no]:
                bucket_insert.setdefault(bucket_no, []).append(recid)
                break

    for recid in recids_old_ordered:
        record_inserted = 0
        record_deleted = 0
        for bucket_no in buckets_dict:
            bucket_value = int(buckets_dict[bucket_no])
            if record_inserted and record_deleted:
                #both insertion and deletion have been registered
                break
            if recids_current_ordered[recid] <= bucket_value and \
                recids_old_ordered[recid] <= bucket_value and \
                not record_inserted and \
                not record_deleted:
                #both before and after the modif,
                #recid should be in the same bucket -> nothing to do
                break
            if recids_current_ordered[recid] <= bucket_value and not record_inserted:
                #recid should be, after the modif, here, so insert
                bucket_insert.setdefault(bucket_no, []).append(recid)
                record_inserted = 1
            if recids_old_ordered[recid] <= bucket_value and not record_deleted:
                #recid was here before modif, must be removed
                bucket_delete.setdefault(bucket_no, []).append(recid)
                record_deleted = 1

    for bucket_no in buckets_dict:
        if (bucket_no in bucket_insert) or (bucket_no in bucket_delete):
            res = run_sql("SELECT bucket_data FROM bsrMETHODDATABUCKET \
                          where id_bsrMETHOD = %s AND bucket_no = %s", \
                          (method_id, bucket_no, ))
            bucket_data = intbitset(res[0][0])
            for recid in bucket_insert.get(bucket_no, []):
                bucket_data.add(recid)
            for recid in bucket_delete.get(bucket_no, []):
                bucket_data.remove(recid)
            if update_timestamp:
                date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                run_sql("UPDATE bsrMETHODDATABUCKET \
                    SET bucket_data = %s, last_updated = %s \
                    WHERE id_bsrMETHOD = %s AND bucket_no = %s", \
                    (bucket_data.fastdump(), date, method_id, bucket_no, ))
            else:
                run_sql("UPDATE bsrMETHODDATABUCKET \
                    SET bucket_data = %s \
                    WHERE id_bsrMETHOD = %s AND bucket_no = %s", \
                    (bucket_data.fastdump(), method_id, bucket_no, ))
            write_message("Updating bucket %s for method %s." %(bucket_no, method_id), verbose=5)


def perform_modify_record(data_dict, data_dict_ordered, data_list_sorted, value, recid, spacing=CFG_BIBSORT_WEIGHT_DISTANCE):
    """Modifies all the data structures with the new information
    about the record"""
    #remove the recid from the old position, to make place for the new value
    data_list_sorted.remove(recid)
    # from now on, it is the same thing as insert
    return perform_insert_record(data_dict, data_dict_ordered, data_list_sorted, value, recid, spacing)


def perform_insert_record(data_dict, data_dict_ordered, data_list_sorted, value, recid, spacing=CFG_BIBSORT_WEIGHT_DISTANCE):
    """Inserts a new record into all the data structures"""
    #data_dict
    data_dict[recid] = value
    #data_dict_ordered & data_list_sorted
    #calculate at which index the rec should be inserted in data_list_sorted
    index_for_insert = binary_search(data_list_sorted, value, data_dict)
    #we have to calculate the weight of this record in data_dict_ordered
    #and it will be the med between its neighbours in the data_list_sorted
    if index_for_insert == len(data_list_sorted):#insert at the end of the list
        #append at the end of the list
        data_list_sorted.append(recid)
        #weight = highest weight + the distance
        data_dict_ordered[recid] = data_dict_ordered[data_list_sorted[index_for_insert - 1]] + spacing
    else:
        if index_for_insert == 0: #insert at the begining of the list
            left_neighbor_weight = 0
        else:
            left_neighbor_weight = data_dict_ordered[data_list_sorted[index_for_insert - 1]]
        right_neighbor_weight = data_dict_ordered[data_list_sorted[index_for_insert]]
        #the recid's weight will be the med between left and right
        weight = (right_neighbor_weight - left_neighbor_weight)/2
        if weight < 1: #there is no more space to insert, we have to create some space
            data_list_sorted.insert(index_for_insert, recid)
            data_dict_ordered[recid] = left_neighbor_weight + spacing
            create_space_for_new_weight(index_for_insert, data_dict_ordered, data_list_sorted, spacing)
        else:
            data_list_sorted.insert(index_for_insert, recid)
            data_dict_ordered[recid] = left_neighbor_weight + weight
    write_message("Record %s done." %recid, verbose=5)
    return index_for_insert


def perform_delete_record(data_dict, data_dict_ordered, data_list_sorted, recid):
    """Delete a record from all the data structures"""
    #data_dict
    del data_dict[recid]
    #data_list_sorted
    data_list_sorted.remove(recid)
    #data_dict_ordered
    del data_dict_ordered[recid]
    write_message("Record %s done." %recid, verbose=5)
    return 1


def create_space_for_new_weight(index_for_insert, data_dict_ordered, data_list_sorted, spacing):
    """In order to keep an order of the records in data_dict_ordered, when a new
    weight is inserted, there needs to be some place for it
    (ex: recid3 needs to be inserted between recid1-with weight=10 and recid2-with weight=11)
    The scope of this function is to increease the distance between recid1 and recid2
    (and thus all the weights after recid2) so that recid3 will have an integer weight"""
    for i in range(index_for_insert+1, len(data_list_sorted)):
        data_dict_ordered[data_list_sorted[i]] += 2 * spacing


def binary_search(sorted_list, value, data_dict):
    """Binary Search O(log n)"""
    minimum = -1
    maximum = len(sorted_list)
    while maximum - minimum > 1:
        med = (maximum+minimum)/2
        recid1 = sorted_list[med]
        value1 = data_dict[recid1]
        if value1 > value:
            maximum = med
        elif value1 < value:
            minimum = med
        else:
            return med
    return minimum + 1


def run_bibsort_update(recids=None, method_list=None):
    """Updates bibsort tables for the methods in method_list
    and for the records in recids.

    If recids is None: recids = all records that have been modified
    or inserted since last update

    If method_list is None: method_list = all the methods available
    in bsrMETHOD table"""

    write_message('Initial data for run_bibsort_update method: ' \
                  'number of recids = %s; method_list=%s' \
                  %(str(len(recids)), method_list), verbose=5)
    write_message('Updating sorting data.')

    bibsort_methods, errors = get_bibsort_methods_details(method_list)
    if errors:
        return False
    method_list = bibsort_methods.keys()
    if not method_list:
        write_message('No methods found in bsrMETHOD table.. exiting.')
        return True

    #we could have 4 types of methods:
    #(i) RNK methods -> they should be rebalanced, not updated
    #(ii) RNK methods to delete -> we should delete their data
    #(iii) non RNK methods to update
    #(iv) non RNK methods that are new -> they should be rebalanced(sorted), not updated
    #check which of the methods are RNK methods (they do not need modified recids)
    rnk_methods = get_rnk_methods(bibsort_methods)
    rnk_methods_updated, rnk_methods_deleted = get_modified_rnk_methods(rnk_methods, bibsort_methods)
    #check which of the methods have no data, so they are actually new,
    #so they need balancing(sorting) instead of updating
    non_rnk_methods = [method for method in bibsort_methods.keys() if method not in rnk_methods]
    non_rnk_methods_updated, non_rnk_methods_inserted = get_modified_non_rnk_methods(non_rnk_methods)

    #(i) + (iv)
    methods_to_balance = rnk_methods_updated + non_rnk_methods_inserted
    if methods_to_balance: # several methods require rebalancing(sorting) and not updating
        return run_bibsort_rebalance(methods_to_balance)

    #(ii)
    #remove the data for the ranking methods that have been deleted
    for method in rnk_methods_deleted:
        task_sleep_now_if_required(can_stop_too=True)
        task_update_progress("Deleting data for method %s" %method)
        write_message('Starting deleting the data for RNK method %s' %method, verbose=5)
        executed_ok = delete_bibsort_data_for_method(bibsort_methods[method]['id'])
        if not executed_ok:
            write_message('Method %s could not be deleted correctly, aborting..' \
                          %method, sys.stderr)
            return False

    #(iii)
    #methods to actually update
    if non_rnk_methods_updated: # we want to update some 'normal'(not RNK) tables, so we need recids
        update_timestamp = False
        if not recids:
            recids = get_modified_or_inserted_recs(non_rnk_methods_updated)
            if recids == 0: #error signal
                return False
            if not recids:
                write_message("No records inserted or modified in bibrec table " \
                          "since the last update of bsrMETHODDATA.")
                return True
            write_message("These records have been recently modified/inserted: %s" \
                  %str(recids), verbose=5)
            update_timestamp = True
        recids_i = intbitset(recids)
        for method in non_rnk_methods_updated:
            task_sleep_now_if_required(can_stop_too=True)
            task_update_progress("Updating method %s" %method)
            write_message('Starting updating method %s' %method, verbose=5)
            executed_ok = update_bibsort_tables(recids_i, method, update_timestamp)
            if not executed_ok:
                write_message('Method %s could not be executed correctly, aborting..' \
                          %method, sys.stderr)
                return False
    return True


def run_bibsort_rebalance(method_list = None):
    """Rebalances all buckets for the methods in method_list"""
    bibsort_methods, errors = get_bibsort_methods_details(method_list)
    if errors:
        return False
    if not bibsort_methods:
        write_message('No methods found.. exiting rebalancing.')
        return True
    #check if there are only ranking methods -> no need for recids
    rnk_methods = get_rnk_methods(bibsort_methods)
    non_rnk_method = [method for method in bibsort_methods.keys() if method not in rnk_methods]

    write_message('Running rebalancing for methods: %s' %bibsort_methods.keys())

    if non_rnk_method:# we have also 'normal' (no RNK) methods, so we need the recids
        recids = get_all_recids(including_deleted=False)
        write_message('Rebalancing will run for %s records.' \
                      %str(len(recids)), verbose=5)
        task_sleep_now_if_required(can_stop_too=True)
    else:
        recids = intbitset([])
        write_message('Rebalancing will run only for RNK methods')
    for name in bibsort_methods:
        task_update_progress('Rebalancing %s method.' %name)
        write_message('Starting sorting the data for %s method ... ' \
                          %name.upper())
        executed_ok = run_sorting_method(recids, name,
                                bibsort_methods[name]['id'],
                                bibsort_methods[name]['definition'],
                                bibsort_methods[name]['washer'])
        if not executed_ok:
            write_message('Method %s could not be executed correctly.' \
                          %name, sys.stderr)
            return False
        write_message('Done.')
        task_sleep_now_if_required(can_stop_too=True)
    task_update_progress('Rebalancing done.')
    return True


def main():
    """tests"""
    #print "Running bibsort_rebalance...."
    #run_bibsort_rebalance() #rebalances everything
    #print "Running bibsort_rebalance for title and author...."
    #run_bibsort_rebalance(['title', 'author']) #rebalances only these methods
    #print "Running bibsort_update...."
    #run_bibsort_update() #update all the methods
    #print "Running bibsort_update for title and author...."
    #run_bibsort_update(method_list = ['title', 'author'])
    #print "Running bibsort_update for records 1,2,3, title author...."
    #run_bibsort_update(recids = [1, 2, 3], method_list = ['title', 'author'])

if __name__ == '__main__':
    main()
