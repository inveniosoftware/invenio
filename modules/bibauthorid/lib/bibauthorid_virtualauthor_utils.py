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
"""
bibauthorid_virtualauthor_utils
    Part of the framework responsible for supplying access methods to the
    virtual author entities along with more advanced computational methods,
    which are required in the work flow of bibauthorid.
"""
from operator import itemgetter
from bibauthorid_utils import split_name_parts
from bibauthorid_utils import clean_name_string
from bibauthorid_utils import create_unified_name
from bibauthorid_utils import get_field_values_on_condition

import bibauthorid_structs as dat
import bibauthorid_config as bconfig


def add_minimum_virtualauthor(orig_authornames_id,
                                       orig_name_string,
                                       bibrec_id,
                                       author_index,
                                       authorname_p_list,
                                       refrec=""):
    '''
    Adds a complete virtual author to the virtual authors table.

    @param orig_authornames_id: ID of the name in authornames table
    @type orig_authornames_id: int
    @param orig_name_string: String of the author name
    @type orig_name_string: string
    @param bibrec_id: ID of the record
    @type bibrec_id: int
    @param author_index: number of the author
    @type author_index: int
    @param authorname_p_list: list of authornamesID with confidence index
        associated [[id1,p], [id2,p], .., [idn,p]]
    @type authorname_p_list: list of lists
    @param refrec: The bibref-bibrec pair of this author on a paper in format
        "100:14424,12441"
    @type refrec: string
    '''
    current_va = create_new_virtualauthor(orig_authornames_id,
                                         orig_name_string)

    add_virtualauthor_record(current_va, 'bibrec_id', bibrec_id)
    add_virtualauthor_record(current_va, 'author_index', author_index)

    if refrec:
        pair = "%s,%s" % (refrec, bibrec_id)
        add_virtualauthor_record(current_va, 'bibrefrecpair', pair)

    dat.update_log("new_vas", current_va)
    update_virtualauthor_cluster(current_va)


def create_new_virtualauthor(orig_authornames_id, orig_name_string):
    '''
    Adds a new virtualauthor to the virtualauthors table;
    Adds original author name and original name string info to the
    virtualauthors_data table

    @param orig_authornames_id: authornames id of the virtual author
    @type orig_authornames_id: int
    @param orig_name_string: name string in authornames of the virtual author
    @type orig_name_string: string

    @return: the va_id of the first found virtual authors
    @rtype: int
    '''
    current_va_id = dat.increment_tracker("va_id_counter")
    dat.VIRTUALAUTHORS.append({'virtualauthorid': current_va_id,
                               'authornamesid': orig_authornames_id,
                               'p': 1,
                               'clusterid':-1})
    add_virtualauthor_record(current_va_id, 'orig_authorname_id',
                             orig_authornames_id)
    add_virtualauthor_record(current_va_id, 'orig_name_string',
                             orig_name_string)
    update_virtualauthor_record(current_va_id, 'updated', 'True')
    add_virtualauthor_record(current_va_id, 'connected', 'False')

    return current_va_id


def update_virtualauthor_cluster(va_id):
    """
    Computes the clusterID for the virtualauthor.
    The clustering at this level is done accumulating all the compatible
    surnames, but there is
    still space for a smarter choice.
    @note: The clustering number is used as a speed up tool, and it is meant to
        accumulate all the possible compatible virtualauthors so we do not have
        to search anywhere else. This means that a worst case cluster is no
        clustering at all (only one cluster for the whole virtualauthors set)
        and a best case cluster is a clusterID for the minimum set of
        virtualauthors representing a real author. It is important
        _NOT to loose_ virtualauthors! It is better to have a bigger cluster
        than loosing possibly precious information later.

    @param va_id: ID of the virtual author the cluster shall be updated for
    @type va_id: int
    """
    ori_name = get_virtualauthor_records(va_id, 'orig_name_string')[0]['value']

    ori_name = clean_name_string(ori_name)
    current_cluster_ids = get_clusterids_from_name(ori_name, True)

    for va_item in [row for row in dat.VIRTUALAUTHORS
               if row['virtualauthorid'] == va_id]:
        va_item['clusterid'] = current_cluster_ids[1]

    bconfig.LOGGER.debug("| Found %s cluster for %s. Now set to %s." %
          (len(current_cluster_ids[0]), ori_name, current_cluster_ids[1]))

    update_virtualauthor_record(va_id, 'updated', 'True')


def add_virtualauthor_record(va_id, tag, value):
    '''
    Adds a record to the virtualauthor_data table

    @param va_id: id of the virtual author to attach the attribute to
    @type va_id: int
    @param tag: tag to alter the value of
    @type tag: string
    @param value: the new value of the tag
    @type value: string
    '''
    dat.VIRTUALAUTHOR_DATA.append({'virtualauthorid': va_id,
                                   'tag': tag,
                                   'value': value})

    if not tag == "updated":
        update_virtualauthor_record(va_id, 'updated', 'True')

    dat.update_log("touched_vas", va_id)


def get_virtualauthor_records(va_id, tag=False):
    '''
    Returns all the records associated to a virtual author.
    If tag != False returns only the selected tag

    @param va_id: id of the virtual author to read the attribute from
    @type va_id: int
    @param tag: the tag to read. Optional. Default: False
    @type tag: string
    '''
    rows = []

    if tag:
        rows = [row for row in dat.VIRTUALAUTHOR_DATA
                if ((row['virtualauthorid'] == va_id)
                    and (row['tag'] == tag))]
    else:
        rows = [row for row in dat.VIRTUALAUTHOR_DATA
                if row['virtualauthorid'] == va_id]

    return rows


def get_virtualauthor_record_tags():
    '''
    Returns the tags found in the virtual author data storage.

    @return: list of tags found
    @rtype: list of strings
    '''
    tags = set()

    for row in dat.VIRTUALAUTHOR_DATA:
        tags.add(row['tag'])

    return list(tags)


def update_virtualauthor_record(va_id, tag, value):
    '''
    Change the value associated to the given tag for a certain virtual author

    @param va_id: ID of the virtual author
    @type va_id: int
    @param tag: tag to be updated
    @type tag: string
    @param value: value to be written for the tag
    @type value: string
    '''
    current_tag_value = [row for row in dat.VIRTUALAUTHOR_DATA
                         if ((row['virtualauthorid'] == va_id)
                             and (row['tag'] == tag))]

    if len(current_tag_value) > 0:
        for tagupdate in [row for row in dat.VIRTUALAUTHOR_DATA
                          if ((row['virtualauthorid'] == va_id)
                              and (row['tag'] == tag))]:
            tagupdate['tag'] = tag
            tagupdate['value'] = value

        dat.update_log("touched_vas", va_id)
    else:
        add_virtualauthor_record(va_id, tag, value)


def delete_virtualauthor_record(va_id, tag):
    '''
    Remove a tag field from the virtualauthor_data table

    @param va_id: ID of the virtual author
    @type va_id: int
    @param tag: tag of the record to be deleted
    @type tag: string
    '''
    for tagupdate in list([row for row in dat.VIRTUALAUTHOR_DATA
                      if ((row['virtualauthorid'] == va_id)
                          and (row['tag'] == tag))]):
        dat.VIRTUALAUTHOR_DATA.remove(tagupdate)

    dat.update_log("touched_vas", va_id)


def get_whole_va_cluster(cluster_id):
    '''
    Returns each virtual author that belongs to a given cluster

    @param cluster_id: numerical ID of a cluster
    @type cluster_id: int

    @return: Each dictionary in the list holds all information about a virtual
        author that belongs to a certain cluster.
    @rtype: a list of dictionaries
    '''
    return [row for row in dat.VIRTUALAUTHORS if row['clusterid'] == cluster_id]


def get_cluster_va_ids(cluster_id):
    '''
    Returns a list of virtual author IDs as representation of which virtual
    author entities are associated with a given cluster

    @param cluster_id: numerical ID of a cluster
    @type cluster_id: int

    @return: A list of virtual author IDs
    @rtype: list of int
    '''
    matches = set()

    for row in sorted(dat.VIRTUALAUTHORS, key=itemgetter('clusterid')):
        if row['clusterid'] == cluster_id:
            matches.add(row['virtualauthorid'])
        elif row['clusterid'] > cluster_id:
            break
        else:
            continue

    return list(matches)


def get_cluster_va_ids_from_va_id(va_id):
    '''
    Starting from a given virtual author (represented by its ID), all other
    compatible virtual authors (i.e. member of the same cluster or member of
    the parent cluster as the referenced virtual author) will be found.

    @param va_id: ID of the referenced virtual author
    @type va_id: int

    @return: all matching virtual authors
    @rtype: list of int
    '''
    name = get_virtualauthor_records(va_id, 'orig_name_string')[0]['value']

    if name in dat.VIRTUALAUTHOR_CLUSTER_CACHE:
        return dat.VIRTUALAUTHOR_CLUSTER_CACHE[name]
    else:
        va_ids = []
        clusters = get_clusterids_from_name(name)

        for cluster in clusters:
            for cluster_va_id in get_cluster_va_ids(cluster):
                va_ids.append(cluster_va_id)

        final_ids = list(set(va_ids))

        dat.VIRTUALAUTHOR_CLUSTER_CACHE[name] = final_ids

        return final_ids


def get_clusterids_from_name(name, return_matching=False):
    '''
    Returns a list of cluster IDs, which are fitting for the parameter 'name'.
    First checks if, in general, a cluster for this name exists. If not,
    create one. If there is a cluster, try to find all other fitting clusters
    and add the found cluster IDs to the list to be returned

    @param name: The name to be on the lookout for.
    @type name: string
    @param return_matching: also return the reference name's matching cluster
    @type return_matching: boolean

    @return:
        if return_matching: list of 1) list of cluster IDs 2) the cluster ID
            matching the name
        if not return_matching: list of cluster IDs
    @rtype:
        if return_matching: list of (list of int, int)
        if not return_matching: list of int
    '''
    search_string = create_unified_name(name)
    search_string = clean_name_string(search_string)

    if len(search_string) > 150:
        search_string = search_string[:150]

    clusterids = set()
    matching_cluster = -1
    initials = ""
    split_string = ""

    if search_string[:-1].count(",") > 0:
        split_string = search_string[:-1].replace(' ', '').split(',')

        if split_string[1]:
            initials = split_string[1].split('.')

    if len(initials) > 2 and len(initials) <= 5:
        permutation_list = initials

        permutation_base = ("%s, %s." %
                            (search_string.split(',')[0], permutation_list[0]))

        for permutation in permutations(permutation_list[1:]):
            name_string = "%s %s." % (permutation_base, ". ".join(permutation))
            clusters = _get_clusterids_from_name(name_string, return_matching)
            if return_matching:
                matching_cluster = clusters[1]
                for clusterid in clusters[0]:
                    clusterids.add(clusterid)
            else:
                for clusterid in clusters:
                    clusterids.add(clusterid)
    else:
        clusters = _get_clusterids_from_name(search_string, return_matching)
        if return_matching:
            matching_cluster = clusters[1]
            clusterids = clusters[0]
        else:
            clusterids = clusters

    if return_matching:
        return [clusterids, matching_cluster]
    else:
        return clusterids


def _get_clusterids_from_name(search_string, return_matching=False):
    '''
    Returns a list of cluster IDs, which are fitting for the parameter 'name'.
    First checks if, in general, a cluster for this name exists. If not,
    create one. If there is a cluster, try to find all other fitting clusters
    and add the found cluster IDs to the list to be returned

    @param name: The name to be on the lookout for.
    @type name: string
    @param return_matching: also return the reference name's matching cluster
    @type return_matching: boolean

    @return:
        if return_matching: list of 1) list of cluster IDs 2) the cluster ID
            matching the name
        if not return_matching: list of cluster IDs
    @rtype:
        if return_matching: list of (list of int, int)
        if not return_matching: list of int
    '''
    clusterids = set()
    newly_created_cluster_id = -1
    existing_initial_cluster_id = -1

    for row in dat.VIRTUALAUTHOR_CLUSTERS:
        if row['clustername'] == search_string:
            existing_initial_cluster_id = row['clusterid']
            break

    if existing_initial_cluster_id > -1:
        clusterids.add(existing_initial_cluster_id)
    else:
        newly_created_cluster_id = dat.increment_tracker('cluster_id')
        dat.VIRTUALAUTHOR_CLUSTERS.append(
                                        {"clusterid": newly_created_cluster_id,
                                         "clustername": search_string})
        clusterids.add(newly_created_cluster_id)

    name_matching_cluster = -1

    if (newly_created_cluster_id > -1):
        name_matching_cluster = newly_created_cluster_id
    else:
        name_matching_cluster = existing_initial_cluster_id

#    The follwing snippet finds every cluster matching the name
#        and any addition
#    as well as the parents.
#    E.g.(Additions): Ellis, John will find clusters for
#        Ellis, J; Ellis, J. R. and Ellis J. E.
#    E.g.(Parents): Ellis, John R. will find clusters for
#        Ellis, J. R. and Ellis, J.

    matching_ids = [row['clusterid'] for row in dat.VIRTUALAUTHOR_CLUSTERS
               if ((row['clustername'].startswith(search_string))
                   or (search_string.startswith(row['clustername'])))]

    for matching_id in matching_ids:
        clusterids.add(matching_id)

    clusterids = list(clusterids)

    if return_matching:
        return [clusterids, name_matching_cluster]
    else:
        return clusterids


def permutations (orig_list):
    '''
    Generator function for building permutations of a given list.
    Used for the permutation of initials during the cluster finding process.
    O(n^2) is acceptable, hence the low number of items.

    @param orig_list: the list to permute
    @type orig_list: list

    @return: The generator for the permutations
    @rtype: generator
    '''
    if not isinstance(orig_list, list):
        orig_list = list(orig_list)

    yield orig_list

    if len(orig_list) == 1:
        return

    for item in sorted(orig_list):
        new_list = orig_list[:]
        position = new_list.index(item)

        try:
            del(new_list[position])
        except IndexError:
            pass

        new_list.insert(0, item)
        for resto in permutations(new_list[1:]):
            if new_list[:1] + resto != orig_list:
                yield new_list[:1] + resto


def get_orphan_virtualauthors():
    '''
    Returns a list of all IDs of Orphans. Orphans are virtual authors that are
    not connected to a real author entity.

    @return: a list of all the virtual author IDs tagged as orphans.
    @rtype: list of int
    '''
    valist = [row['virtualauthorid'] for row in dat.VIRTUALAUTHOR_DATA
              if ((row['tag'] == 'connected')
                  and (row['value'] == 'False'))]
    return valist


def get_next_updated_virtualauthor():
    """
    Returns one of the virtualauthorsIDs tagged as updated

    @deprecated: Newly created queue model is more efficient and cleaner.

    @return: Next updated virtual author.
    @rtype: int
    """
    while(True):
        valist = [row['virtualauthorid'] for row in dat.VIRTUALAUTHOR_DATA
                  if ((row['tag'] == 'updated')
                      and (row['value'] == 'True'))]

        if len(valist) > 0:
            last_valist_str = ''
            if last_valist_str != str(valist[0][0]):
                return valist
        else:
            return - 1


def init_va_process_queue(mode="updated"):
    '''
    Initializes the virtual author process queue with all virtual authors
    that are not connected (orphaned) or updated.

    @param mode: Specifies the mode of operation regarding which data to use.
        Modes are: 'orphaned' or 'updated' (default)
    @type mode: string
    '''
    bconfig.LOGGER.log(25, "Initializing processing queue")

    if not dat.VIRTUALAUTHOR_PROCESS_QUEUE.empty():
        bconfig.LOGGER.info("Clearing VA Process Queue")
        dat.VIRTUALAUTHOR_PROCESS_QUEUE.queue.clear()

    va_nosort = {}

    if mode == "updated":
        for va_entry in [row['virtualauthorid'] for row in
                         dat.VIRTUALAUTHOR_DATA
                         if ((row['tag'] == 'updated')
                             and (row['value'] == 'True'))]:
            va_nosort[va_entry] = 0
    elif mode == "orphaned":
        for va_entry in [row['virtualauthorid'] for row in
                         dat.VIRTUALAUTHOR_DATA
                         if ((row['tag'] == 'connected')
                             and (row['value'] == 'False'))]:
            va_nosort[va_entry] = 0

    for va_id in va_nosort:
        va_data = get_virtualauthor_records(va_id)
        authorname_string = ""
        bibrec_id = ""

        for va_data_item in va_data:
            if va_data_item['tag'] == "bibrec_id":
                bibrec_id = va_data_item['value']
            elif va_data_item['tag'] == "orig_name_string":
                authorname_string = va_data_item['value']

        else:
            affiliations = get_field_values_on_condition(bibrec_id,
                            ['100', '700'], 'u', 'a', authorname_string)
            coauthors = get_field_values_on_condition(bibrec_id,
                            ['100', '700'], 'a', 'a', authorname_string, "!=")
            collaboration = get_field_values_on_condition(bibrec_id, "710", "g")

            if affiliations:
                va_nosort[va_id] += 1

            if coauthors:
                va_nosort[va_id] += 1

            if collaboration:
                va_nosort[va_id] += 1

    for va_entry in sorted(va_nosort.items(), key=itemgetter(1), reverse=True):
        dat.VIRTUALAUTHOR_PROCESS_QUEUE.put(va_entry[0])

    bconfig.LOGGER.log(25, "Done with queue initialization.")


def get_updated_virtualauthors():
    """
    Returns a list of all the virtual authors IDs tagged as updated

    @return: list of updated virtual authors
    @rtype: list of int
    """
    return [row['virtualauthorid'] for row in dat.VIRTUALAUTHOR_DATA
                  if ((row['tag'] == 'updated')
                      and (row['value'] == 'True'))]


def get_va_id_from_recid_and_nameid(bibrec, authornamesid):
    '''
    Finds all the virtual author ids that belong to a certain name on a record

    @param bibrec: bibrec id of a record
    @type bibrec: int
    @param authornamesid: id in author names of a certain name string
    @type authornamesid: int

    @return: list of virtual author ids
    @rtype: list of int
    '''
    va_ids = set()

    for possible_va_id in [row['virtualauthorid'] for row in dat.VIRTUALAUTHORS
                              if row['authornamesid'] == authornamesid]:
        for va_id in [row['virtualauthorid'] for row in dat.VIRTUALAUTHOR_DATA
                      if ((row['virtualauthorid'] == possible_va_id) and
                          (row['tag'] == 'bibrec_id') and
                          (row['value'] == bibrec))]:
            va_ids.add(va_id)

    return list(va_ids)


def get_va_ids_from_recid(bibrec):
    '''
    Finds all the virtual author ids that belong to a certain record

    @param bibrec: bibrec id of a record
    @type bibrec: int

    @return: list of virtual author ids
    @rtype: list of int
    '''
    va_ids = set()

    for va_id in [row['virtualauthorid'] for row in dat.VIRTUALAUTHOR_DATA
                  if ((row['tag'] == 'bibrec_id') and
                      (row['value'] == str(bibrec)))]:
        va_ids.add(va_id)

    return list(va_ids)


def get_va_ids_by_recid_lname(bibrec, lastname):
    '''
    Finds all the virtual author ids that belong to a certain record
    and hold a certain last name

    @param bibrec: bibrec id of a record
    @type bibrec: int
    @param lastname: The last name of a person
    @type lastname: string

    @return: list of virtual author ids
    @rtype: list of int
    '''
    va_ids = set()
    pot_va_ids = [row['virtualauthorid'] for row in dat.VIRTUALAUTHOR_DATA
                  if ((row['tag'] == 'bibrec_id') and
                      (row['value'] == str(bibrec)))]
    for va_id in [row['virtualauthorid'] for row in dat.VIRTUALAUTHOR_DATA
                      if ((row['virtualauthorid'] in pot_va_ids) and
                          (row['tag'] == 'orig_name_string') and
                          (split_name_parts(row['value'])[0] == lastname))]:
        va_ids.add(va_id)

    return list(va_ids)


def delete_virtual_author(va_id):
    '''
    This will delete a virtual author while cascading the change through the
    different storages and instances: ra_data, ras, va_data and vas

    @param va_id: the virtual author to be deleted
    @type va_id: int

    @return: success or failure of the process
    @rtype: boolean
    '''
    if not isinstance(va_id, int):
        try:
            va_id = int(va_id)
        except (ValueError, TypeError):
            raise ValueError("Expecting the va id to be an int.")

    tags = get_virtualauthor_record_tags()

    for tag in tags:
        delete_virtualauthor_record(va_id, tag)

    for deletion_candidate in list([row for row in dat.VIRTUALAUTHORS
                               if row['virtualauthorid'] == va_id]):
        dat.VIRTUALAUTHORS.remove(deletion_candidate)

    dat.update_log("deleted_vas", va_id)

    return True
