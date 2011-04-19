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
'''
bibauthorid_realauthor_utils
    Part of the framework responsible for supplying access methods to the
    real author entities along with more advanced computational methods which
    are required in the work flow of bibauthorid.
'''
import sys
import time
import glob
import os.path as osp

import bibauthorid_utils
import bibauthorid_virtualauthor_utils
import bibauthorid_config as bconfig
import bibauthorid_structs as dat

from bibauthorid_general_functions import cmp_virtual_to_real_author
from bibauthorid_virtualauthor_utils import init_va_process_queue


def create_new_realauthor(va_id):
    """
    Create a new real author connected to the given virtual author; the trust
    value for the virtual author is obviously 1 because this virtual author is
    incompatible with every other real author and is the first
    one in this new real author.

    RETURNS: the newly created realauthorid
    """
    current_ra_id = dat.increment_tracker("raid_counter")
    dat.REALAUTHORS.append({'realauthorid': current_ra_id,
                         'virtualauthorid': va_id,
                         'p': 1})
    dat.update_log("new_ras", current_ra_id)
    update_realauthor_data_by_vid(current_ra_id, va_id)
#    update_realauthor_names(current_ra_id)

    return current_ra_id


def old_update_realauthor_names(ra_id):
    '''
    Computes a new set of realauthor names, discards the old names list
    and replaces it with the new one.

    @deprecated: The name list is no longer maintained in the process.

    @param ra_id: the id of the real author which shall be updated
    @type ra_id: int
    '''
    bconfig.LOGGER.debug("Updating RA Names for %s" % (ra_id))
#    set_realauthor_names(ra_id, compute_realauthor_names(ra_id))
    bconfig.LOGGER.debug("Done Updating RA Names for %s" % (ra_id))


def update_realauthor_va_confidence(ra_id, va_id, probability):
    '''
    Updates the confidence value for a given va in a certain ra_id

    @param ra_id: the id of the real author to be updated
    @type ra_id: int
    @param va_id: the id of the virtual author the probability shall be updated
    @type va_id: int
    @param probability: the new probability for the virtual author
    @type probability: float
    '''
    for line in [row for row in dat.REALAUTHORS
              if ((row['realauthorid'] == ra_id)
                  and (row['virtualauthorid'] == va_id))]:
        line['p'] = probability


def add_realauthor_va(ra_id, va_id, probability):
    '''
    Adds a virtualauthor to an existing realauthor

    @param ra_id: Realauthor ID
    @type ra_id: int
    @param va_id: Virtualauthor ID
    @type va_id: int
    @param probability: probability of assignment
    @type probability: float
    '''
    dat.REALAUTHORS.append({'realauthorid': ra_id,
                            'virtualauthorid': va_id,
                            'p': probability})
#    update_realauthor_names(ra_id)
    update_realauthor_data_by_vid(ra_id, va_id)


def get_realauthor_va_count_p_sum(ra_id):
    '''
    Finds the count of virtual authors and the sum of the probabilities for a
    real author
    @param ra_id: Realauthor ID
    @type ra_id: int

    @return: tuple of va_count and p_sum
    @rtype: tuple
    '''
    va_count = 0
    p_sum = 0

    for line in [row for row in dat.REALAUTHORS
              if row['realauthorid'] == ra_id]:
        va_count += 1
        p_sum += line['p']

    return (va_count, p_sum)


def get_realauthor_va_p(ra_id):
    '''
    Returns a va, p couples tuple associated to a given realauthor

    @param ra_id: the real author id to look up the information for
    @type ra_id: int

    @return: the requested va, p information
    @rtype: list of dictionaries
    '''
    retval = [row for row in dat.REALAUTHORS if row['realauthorid'] == ra_id]

    return retval


def remove_va_from_ra(ra_id, va_id):
    '''
    Removes a selected virtual author from a real author

    @param ra_id: id of the virtual author to be altered
    @type ra_id: int
    @param va_id: if of the virtual author to be removed from ra attachment
    @type va_id: int
    '''
    for remove in [row for row in dat.REALAUTHORS
               if ((row['realauthorid'] == ra_id) and
                   (row['virtualauthorid'] == va_id))]:
        dat.REALAUTHORS.remove(remove)

    bibauthorid_virtualauthor_utils.delete_virtualauthor_record(va_id,
                                                                'connected')


def get_realauthor_names_from_set(ra_id):
    '''
    Finds all authornames for a given realauthor from table
    aidREALAUTHORDATA.
    @param ra_id: the id of the real author to get the names from
    @type ra_id: int

    @return: the complete list of realauthor names, ordered by confidence
    @rtype: list
    '''
    names = [row['value'] for row in dat.REALAUTHOR_DATA
                if ((row['realauthorid'] == ra_id)
                and (row['tag'] == "orig_name_string"))]
    return names


def get_realauthors_by_virtuala_id(va_id):
    '''
    Retrieve all real authors that contain a certain virtual author

    @param va_id: Virtualauthor ID
    @return: a list of realauthors ids which are connected to a given
        virtual author
    '''
    return [row['realauthorid'] for row in dat.REALAUTHORS
            if row['virtualauthorid'] == va_id]


def update_ralist_cache(va_list, va_list_hash):
    '''
    Updates the Cache that holds information about which real authors
    potentially fit to the virtual author.

    @param va_list: The list of virtual authors
    @type va_list: list
    @param va_list_hash: a hash of the va_list
    @type va_list_hash: string
    '''

    bconfig.LOGGER.debug("Updating RA_VA_CACHE")
    ralist = []

    [ralist.append({'ra_id': ra_id, 'va_id': va_entry})
     for va_entry in va_list
     for ra_id in get_realauthors_by_virtuala_id(va_entry)]

    dat.RA_VA_CACHE[va_list_hash] = ralist

    return ralist


def add_virtualauthor(va_id, multi_va_to_ra=False):
    '''
    Adds a new virtual author to the real authors system:
    the idea is to search for possibly compatible real authors, then compare
    the compatibility of this virtual author with all the virtual authors
    connected to the selected real authors and add the new virtualauthor to
    the most compatible real author. In case we do not have a most compatible
    real author, we add the same virtual author to more then one real author
    with a lower probability; this behavior might be changed.

    @param va_id: Virtualauthor ID
    @type va_id: int
    '''
    addstart = time.time()
    adding_threshold = bconfig.REALAUTHOR_VA_ADD_THERSHOLD

    if adding_threshold == ["-1"]:
        adding_threshold = 0.7

    already_existing = get_realauthors_by_virtuala_id(va_id)
    ralist = []

    if len(already_existing) <= 0:
        start = time.time()

        va_cluster = (bibauthorid_virtualauthor_utils.
                      get_cluster_va_ids_from_va_id(va_id))
        ralist_raw = []

        va_hash = hash(str(va_cluster))

        if va_hash in dat.RA_VA_CACHE:
            ralist_raw = dat.RA_VA_CACHE[va_hash]
            bconfig.LOGGER.debug("|-> Cache Hit for va cluster")
        else:
            bconfig.LOGGER.debug("|-> Cache Fail--Generating new hash")
            ralist_raw = update_ralist_cache(va_cluster, va_hash)

        ralist = [ids['ra_id'] for ids in ralist_raw if ids['va_id'] != va_id]
        ralist = list(set(ralist))

        if len(ralist) > 0:
            min_compatibilities = []

            for i in ralist:
                compatibilities = []
                compatibilities.append(cmp_virtual_to_real_author(va_id, i))
                min_compatibilities.append(min(compatibilities))

            max_min_compatibilities = max(min_compatibilities)

            if max_min_compatibilities < adding_threshold:
                bconfig.LOGGER.log(25, "|-> Creating NEW real author for this"
                      + " virtual author (compatibility below adding threshold"
                      + " of other RAs).")
                create_new_realauthor(va_id)
                update_ralist_cache(va_cluster, va_hash)

            else:
                if min_compatibilities.count(max_min_compatibilities) == 1:
                    index = min_compatibilities.index(max_min_compatibilities)
                    add_realauthor_va(ralist[index], va_id,
                                      max_min_compatibilities)
                    bconfig.LOGGER.log(25, "|-> Adding to real author #%s"
                               " with a compatability of %.2f"
                               % (ralist[index], max_min_compatibilities))

                elif min_compatibilities.count(max_min_compatibilities) > 1:
                    if multi_va_to_ra:
                        bconfig.LOGGER.log(25, "|-> virtual author"
                                " comaptible with more than one realauthor.")
                        indexes = set()

                        for i in xrange(len(min_compatibilities)):
                            indexes.add(min_compatibilities.index(
                                                max_min_compatibilities, i))

                        bconfig.LOGGER.log(25, "|-> virtual author"
                                " will be attached to %s real authors"
                                % (len(indexes)))

                        for i in indexes:
                            add_realauthor_va(ralist[i], va_id,
                                      max_min_compatibilities)
                            bconfig.LOGGER.log(25, "|--> Adding to real author"
                               " #%s with a compatability of %.2f"
                               % (ralist[i], max_min_compatibilities))

                    else:
                        bconfig.LOGGER.log(25, "|-> virtual author"
                                " comaptible with more than one realauthor..."
                                "skipped for now.")
                        bconfig.LOGGER.log(25, "|> The (skipped) comparison "
                                  "with %s real authors took %.2fs" %
                                  (len(ralist), time.time() - start))
                        (bibauthorid_virtualauthor_utils.
                         update_virtualauthor_record(va_id, 'connected',
                                                     'False'))
                        (bibauthorid_virtualauthor_utils.
                         delete_virtualauthor_record(va_id, 'updated'))
                    return
        else:
            bconfig.LOGGER.log(25, "|-> Creating NEW real author for this"
                        " Virtual Author (currently, no real author exists)")
            create_new_realauthor(va_id)
            update_ralist_cache(va_cluster, va_hash)

    (bibauthorid_virtualauthor_utils.
     update_virtualauthor_record(va_id, 'connected', 'True'))
    (bibauthorid_virtualauthor_utils.
     delete_virtualauthor_record(va_id, 'updated'))

    bconfig.LOGGER.log(25, "|> The comparison with %s real authors took %.2fs"
                  % (len(ralist), time.time() - addstart))


def create_realauthors_from_orphans():
    '''
    Find all orphaned virtual authors and create a real author for every one.
    '''
    va_list = bibauthorid_virtualauthor_utils.get_orphan_virtualauthors()

    for va_entry in va_list:
        bconfig.LOGGER.log(25, "INSERTING VA %s Name: %s"
                           % (va_entry['virtualauthorid'],
              bibauthorid_virtualauthor_utils.
              get_virtualauthor_records(va_entry['virtualauthorid'],
                                        tag='orig_name_string')[0]['value']))
        add_virtualauthor(va_entry['virtualauthorid'])

    bconfig.LOGGER.debug("va_list lengtht: %s" % (len(va_list)))


def find_and_process_orphans(iterations=1):
    '''
    Finds and processes orphaned virtual authors.

    @param iterations: Number of rounds to do this processing
    @type iterations: int
    '''
    multi_attach = False
#    processed_orphans = set()

    for iteration in xrange(iterations):
        if dat.VIRTUALAUTHOR_PROCESS_QUEUE.empty():
            init_va_process_queue(mode="orphaned")

        while True:
            va_id = -1

            if dat.VIRTUALAUTHOR_PROCESS_QUEUE.empty():
                bconfig.LOGGER.debug("Empty Queue. Job finished."
                                     " Nothing to do.")
                break
            else:
                va_id = dat.VIRTUALAUTHOR_PROCESS_QUEUE.get()

#            if va_id not in dat.PROCESSED_ORPHANS:
            va_name = (bibauthorid_virtualauthor_utils.
                           get_virtualauthor_records(va_id,
                                            tag='orig_name_string')[0]['value'])
            bconfig.LOGGER.log(25, "|> Inserting orphaned VA: %s Name: %s"
                  % (va_id, va_name))

            if ((bconfig.ATTACH_VA_TO_MULTIPLE_RAS)
                and (iteration == iterations - 1)):
                multi_attach = True

            add_virtualauthor(va_id, multi_attach)


def find_and_process_updates(process_initials):
    '''
    Finds and processes not updated virtualauthors (which are identified by
    the 'updated' tag) and delivers the ID of this virtualauthor to the
    function responsible for assigning the virtualauthor to a realauthor.

    @param process_initials: If names with initials only shall be
        processed or not
    @type process_initials: boolean
    '''
    if dat.VIRTUALAUTHOR_PROCESS_QUEUE.empty():
        init_va_process_queue()

    while True:
        va_id = -1

        if dat.VIRTUALAUTHOR_PROCESS_QUEUE.empty():
            bconfig.LOGGER.debug("Empty Queue. Job finished. Nothing to do.")
            break
        else:
            va_id = dat.VIRTUALAUTHOR_PROCESS_QUEUE.get()

        va_name = (bibauthorid_virtualauthor_utils.
                   get_virtualauthor_records(va_id,
                                         tag='orig_name_string')[0]['value'])

        if not process_initials:
            if bibauthorid_utils.split_name_parts(va_name)[2]:
                (bibauthorid_virtualauthor_utils.
                 delete_virtualauthor_record(va_id, 'updated'))
                bconfig.LOGGER.log(25, "|> Inserting VA:"
                      + " %s Orig. name: %s" % (va_id, va_name))
                add_virtualauthor(va_id)
        else:
            (bibauthorid_virtualauthor_utils.
             delete_virtualauthor_record(va_id, 'updated'))
            bconfig.LOGGER.log(25, "|> Inserting VA: %s Orig. name: %s"
                          % (va_id, va_name))
            add_virtualauthor(va_id)


def process_updated_virtualauthors():
    '''
    First, this method calls the find_and_process_updates method
    in order to process the names which appear to have a name and not only
    initials first. This will create a more precise initial set of realauthors.
    A second run of the method will then assign initials-only names to
    real authors.
    '''
    find_and_process_updates(False)
    find_and_process_updates(True)


def update_realauthor_data_by_vid(ra_id, va_id):
    '''
    Updates the data associated with a real author.
    Scenario 1: Data for real author exists--raise virtual author count by 1.
    Scenario 2: Data for real author does currently not exist--Create data
        set for future comparisons.

    @param ra_id: Realauthor ID
    @type ra_id: int
    @param va_id: Virtualauthor ID
    @type va_id: int
    '''
    va_names_p = 0
    for row in dat.VIRTUALAUTHORS:
        if row['virtualauthorid'] == va_id:
            va_names_p = row['p']
            break

    va_p = 0
    for row in dat.REALAUTHORS:
        if ((row['realauthorid'] == ra_id)
            and (row['virtualauthorid'] == va_id)):
            va_p = row['p']
            break

    va_data = [row for row in dat.VIRTUALAUTHOR_DATA
               if row['virtualauthorid'] == va_id]

    for i in va_data:
        if (not (i['tag'] == "updated") 
            and not (i['tag'] == "connected")
            and not (i['tag'] == "authorindex")
            and not (i['tag'] == 'bibrefrecpair')):
            existant_data = [row for row in dat.REALAUTHOR_DATA
                             if ((row['realauthorid'] == ra_id)
                                 and (row['tag'] == i['tag'])
                                 and (row['value'] == i['value']))]

            if len(existant_data) > 0:
                for updated in [row for row in dat.REALAUTHOR_DATA
                                if ((row['realauthorid'] == ra_id)
                                    and (row['tag'] == i['tag'])
                                    and (row['value'] == i['value']))]:
                    updated['va_count'] += 1
                    updated['va_np'] += va_names_p
                    updated['va_p'] += va_p
            else:
                dat.REALAUTHOR_DATA.append({'realauthorid': ra_id,
                                            'tag': i['tag'],
                                            'value': i['value'],
                                            'va_count': 1,
                                            'va_np': va_names_p,
                                            'va_p': va_p})
    _start_va_harvest(ra_id, va_id)


def _start_va_harvest(ra_id, va_id):
    '''
    Starts the harvesting process add relevant data from the virtual author
    to the real author it is attached to.

    @param ra_id: id of the real author to add the data to
    @type ra_id: int
    @param va_id: id of the virtual author to read the data from
    @type va_id: int
    '''
    module_paths = glob.glob(bconfig.MODULE_PATH)
    module = None

    if not module_paths:
        bconfig.LOGGER.exception("Sorry, no modules found for comparison.")
        raise Exception('ModuleError')

    for module_path in module_paths:
        module_id = osp.splitext(osp.basename(module_path))[0]
        module = None
        module_import_name = ("bibauthorid_comparison_functions.%s"
                              % (module_id))

        try:
            __import__(module_import_name)
            module = sys.modules[module_import_name]
        except ImportError:
            bconfig.LOGGER.exception("Error while importing %s" % (module_id))

        try:
            module.get_information_from_dataset(va_id, ra_id)
        except AttributeError:
            bconfig.LOGGER.debug("No harvester in module %s."
                                 " Nothing to do." % (module_id))


def get_realauthor_ids(tag, value):
    '''
    Read realauthorids based on the value in the tag.

    @param tag: where to look for the information (ex. realauthorname)
    @type tag: string
    @param value: what to look for (ex. Ellis, J)
    @type value: string

    @return: ids that match the criteria
    @rtype: list
    '''
    return [row['realauthorid'] for row in dat.REALAUTHOR_DATA
              if ((row['tag'] == tag) and (row['value'].startswith(value)))]


def get_realauthor_data(ra_id, tag_name=""):
    '''
    Fetches the data associated to a real author entity.

    @param ra_id: Realauthor ID to receive the data from
    @type ra_id: int
    @param tag_name: OPTIONAL parameter to receive only certain tags.
                If defined, specify tag name here. E.g. "orig_name_string"
                Defaults to ""
    @type tag_name: string

    @return: the data associated with a real author
    @rtype: list of dictionaries
    '''
    ra_data = []

    if not tag_name:
        ra_data = [row for row in dat.REALAUTHOR_DATA
                   if row['realauthorid'] == ra_id]
    else:
        ra_data = [row for row in dat.REALAUTHOR_DATA
                   if ((row['realauthorid'] == ra_id) and
                       (row['tag'] == tag_name))]

    return ra_data


def set_realauthor_data(ra_id, tag_name, value):
    '''
    Sets a data entry for a virtual author entity.

    @param ra_id: ID of the real author
    @type ra_id: int
    @param tag_name: name of the tag to set (e.g. 'bibrec_id')
    @type tag_name: string
    @param value: value of the entry (e.g. '12114')
    @type value: string
    '''
    existant_data = [row for row in dat.REALAUTHOR_DATA
                     if ((row['realauthorid'] == ra_id)
                         and (row['tag'] == tag_name)
                         and (row['value'] == value))]

    if len(existant_data) > 0:
        for updated in [row for row in dat.REALAUTHOR_DATA
                        if ((row['realauthorid'] == ra_id)
                            and (row['tag'] == tag_name)
                            and (row['value'] == value))]:
            updated['va_count'] += 1

    else:
        dat.REALAUTHOR_DATA.append({'realauthorid': ra_id,
                                    'tag': tag_name,
                                    'value': value,
                                    'va_count': 1,
                                    'va_np': 0,
                                    'va_p': 0})


def del_ra_data_by_vaid(ra_id, va_id):
    '''
    Removes the data specified by a virtualauthor from the realauthor data set

    @param ra_id: Realauthor ID
    @type ra_id: int
    @param va_id: Virtualauthor ID
    @type va_id: int
    '''
    va_data = [row for row in dat.VIRTUALAUTHOR_DATA
               if row['virtualauthorid'] == va_id]

    bconfig.LOGGER.info("Processing RA data. %s " % (va_data))

    for i in va_data:
        if (not (i['tag'] == "updated") 
            and not (i['tag'] == "connected")
            and not (i['tag'] == "authorindex")
            and not (i['tag'] == "bibrec_id")
            and not (i['tag'] == 'bibrefrecpair')):
            existant_data = [row for row in dat.REALAUTHOR_DATA
                             if ((row['realauthorid'] == ra_id)
                                 and (row['tag'] == i['tag'])
                                 and (row['value'] == i['value']))]
            if existant_data[0]['va_count'] > 1:
                bconfig.LOGGER.info("|--> Updating RA Data")

                for updated in [row for row in dat.REALAUTHOR_DATA
                                if ((row['realauthorid'] == ra_id)
                                    and (row['tag'] == i['tag']))]:
                    updated['va_count'] -= 1
            else:
                bconfig.LOGGER.info("|--> Deleting RA Data")

                for deletion_candidate in [row for row in dat.REALAUTHOR_DATA
                            if ((row['realauthorid'] == ra_id)
                                and (row['tag'] == i['tag'])
                                and (row['value'] == i['value']))]:
                    dat.REALAUTHOR_DATA.remove(deletion_candidate)


def del_ra_data_by_value(ra_id, tag_name, value):
    '''
    Removes an exact data field from realauthor data set
    @deprecated: doesn't do anything yet.

    @param ra_id: Realauthor ID
    @type ra_id: int
    @param tag_name: Name of the tag to be removed
    @type tag_name: string
    @param value: specific value to be removed
    @type value: string
    '''
    bconfig.LOGGER.debug("Request to remove %u %s %s"
                         % (ra_id, tag_name, value))
