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
bibauthorid_structs
    Defines the data structures for computation in memory and acts as
    bibauthorid's memory storage facility.
'''
import Queue

# pylint: disable=W0105
AUTHOR_NAMES = []
'''
AUTHOR_NAMES
    Holds data from the aidAUTHORNAMES table.
Structure:
    [{tag: value}*]
Example:
    [{'id': '1',
    'name': 'Groom, Donald E.',
    'bibrefs': '100:1,700:9912',
    'db_name': 'Groom, Donald E.'},
    {'id': '2',
    'name': 'de Sacrobosco, Johannes',
    'bibrefs': '100:4',
    'db_name': 'de Sacrobosco, Johannes'}
    ]
'''

DOC_LIST = []
'''
DOC_LIST
    Holds data from the aidDOCLIST table.
Structure:
    [{tag: value}*]
Example:
    [{'bibrecid': 680600L,
      'authornameids': [305005L, 44341L],
      'authornameid_bibrefrec' : [(305005L, "100:133,680600")]},
     {'bibrecid': 681822L,
      'authornameids': [305005L],
      'authornameid_bibrefrec' : [(305005L, "100:133,681822")]}]
'''

REALAUTHORS = []
'''
REALAUTHORS
    Holds data from the aidREALAUTHORS table.
Structure:
    [{tag: value}*]
Example:
    [{'realauthorid': '1',
        'virtualauthorid': '1020',
        'p': '0.5453'}
    ]
'''

REALAUTHOR_DATA = []
'''
REALAUTHOR_DATA
    Holds data from the aidREALAUTHORDATA table.
Structure:
    [{tag: value}*]
Example:
    [{'realauthorid: '1',
        'tag': 'affiliation',
        'value': '2003-04;;Chen, Alex;;Fermilab',
        'va_count': '1',
        'va_np': '0',
        'va_p': '0'},
    {'realauthorid: '1',
        'tag': 'affiliation',
        'value': '2007-05;;Chen, Alex Zuxing;;Fermilab',
        'va_count': '1',
        'va_np': '0',
        'va_p': '0'},
    {'realauthorid: '1',
        'tag': 'coauthor',
        'value': 'Chen, Alex;;Chou, W.',
        'va_count': '1',
        'va_np': '0',
        'va_p': '0'}
    ]
'''

VIRTUALAUTHORS = []
'''
VIRTUALAUTHORS
    Holds data from the aidVIRTUALAUTHORS table.
Structure:
    [{tag: value}*]
Example:
    [{'virtualauthorid': '3',
        'authornamesid': '42555',
        'p': '0.9',
        'clusterid': '2'}
    ]
'''

VIRTUALAUTHOR_DATA = []
'''
VIRTUALAUTHOR_DATA
    Holds data from the aidVIRTUALAUTHORSDATA table.
Structure:
    [{tag: value}*]
Example:
    [{'virtualauthorid' : '1'
        'tag': 'authorIndex'
        'value': '0'},
    {'virtualauthorid' : '1',
        'tag': 'bibrec_id',
        'value': '680600',
    {'virtualauthorid' : '1',
        'tag': 'connected',
        'value': 'False'},
    {'virtualauthorid' : '1',
        'tag': 'orig_authorname_id',
        'value': '305005'},
    {'virtualauthorid' : '1',
        'tag': 'orig_name_string',
        'value': 'Chen, .J.'}
    ]
'''

VIRTUALAUTHOR_CLUSTERS = []
'''
VIRTUALAUTHOR_CLUSTERS
    Holds data from the aidVIRTUALAUTHORS_clusters table.
Structure:
    [{tag: value}*]
Example:
    [{'clusterid': '1',
        'clustername': 'Chen, A.'},
    {'clusterid': '2',
        'clustername': 'Chen, A. A.'}
    ]
'''

VIRTUALAUTHOR_CLUSTER_CACHE = {}
'''
VIRTUALAUTHOR_CLUSTER_CACHE
    Holds Name->ClusterID Mappings
Structure:
    {'Name': [ClusterIDs]}
Example:
    {'Ellison, J.': [2170, 2171, 2172, 2173, 2174, 2175, 2176, 2177, 2178]}
'''

VIRTUALAUTHOR_PROCESS_QUEUE = Queue.Queue()
'''
VIRTUALAUTHOR_PROCESS_QUEUE
    Holds the virtual author ids that are to be processed.
'''

ID_TRACKER = {}
'''
ID_TRACKER
    Holds information about the current/next id of virtual or real author
    entities.
Structure:
    {tracker name: value}
Example:
    {"va_id_counter": 12332L,
    "raid_counter": 122L,
    "last_updated_va": 122L,
    "cluster_id": 166}
'''

RELEVANT_RECORDS = {}
'''
RELEVANT_RECORDS
    Holds all the information about the documents referenced
    by the authors in memory
Structure:
    {bibrecid: data dict from get_record}
Example:
   {1: {'001': [([], ' ', ' ', '3', 1)],
        '035': [([('a', 'Test:1750qe'), ('9', 'SPIRESTeX')], ' ', '', '', 10)],
        '100': [([('a', 'Test, Author J.')], ' ', ' ', '', 3)],
        '245': [([('a', 'The test record')], ' ', ' ', '', 4)],
        '260': [([('c', '1750')], ' ', ' ', '', 6)],
        '269': [([('c', '1750')], ' ', ' ', '', 5)],
        '690': [([('a', 'Preprint')], 'C', ' ', '', 2)],
        '961': [([('x', '2001-11-12')], ' ', ' ', '', 7),
                ([('c', '2003-07-21')], ' ', ' ', '', 8)],
        '970': [([('a', 'SPIRES-4772695')], ' ', ' ', '', 9)],
        '980': [([('a', 'unknown')], ' ', ' ', '', 11)]}
    }
'''

RA_VA_CACHE = {}
'''
RA_VA_CACHE
    Holds information about the connection of virtual authors to real authors
    This caching allows an enormous speedup compared to assessing this
    information each time separately.
Structure:
    {hashtag of VA IDs: list of RA IDs}
'''

CITES_DICT = {}
CITED_BY_DICT = {}
'''
CITES_DICT and CITED_BY_DICT
    Hold information about citations for the job creation process.
Structure:
    {id_bibrec: [list of bibrecs that are cited by/cite the key]}
'''

UPDATES_LOG = {"deleted_vas": set(),
               "touched_vas": set(),
               "new_ras": set(),
               "new_vas": set(),
               "rec_updates": set()}
'''
UPDATES_LOG
    Keeps track of updated RAs and VAs to minimize database activities upon
    updating it from the mem cache.
Structure:
    {"tag": set of ids}
'''
# pylint: enable=W0105


def update_log(logbook, value):
    '''
    Adds a value to the set of the logbook

    @param logbook: the name of the log
    @type logbook: string
    @param value: the value to add
    @type value: int
    '''
    logbooks = ("deleted_vas", "touched_vas", "new_ras",
                "new_vas", "rec_updates")

    if not logbook in logbooks:
        raise ValueError("Valid logbooks are %s" % str(logbooks))

    if not isinstance(value, int):
        try:
            value = int(value)
        except (ValueError, TypeError):
            raise ValueError("Logbook Value must be an int.")

    if logbook in UPDATES_LOG:
        UPDATES_LOG[logbook].add(value)
    else:
        UPDATES_LOG[logbook] = set((value,))


def set_tracker(tracker_name, value):
    '''
    Sets a specified tracker to a specified value

    @param tracker_name: the name of the tracker (e.g. va_id_counter)
    @type tracker_name: string
    @param value: the value the tracker shall be updated to
    @type value: int
    '''
    if not isinstance(value, int):
        try:
            value = int(value)
        except (ValueError, TypeError):
            raise ValueError("Tracker Value is expected to be an int!")

    if tracker_name in ID_TRACKER:
        ID_TRACKER[tracker_name].add(value)
    else:
        ID_TRACKER[tracker_name] = value


def increment_tracker(tracker_name):
    '''
    Increments a specified tracker by one (1).

    @param tracker_name: the name of the tracker (e.g. va_id_counter)
    @type tracker_name: string

    @return: the new value of the tracker
    @rtype: int
    '''
    if tracker_name in ID_TRACKER:
        ID_TRACKER[tracker_name] += 1
    else:
        ID_TRACKER[tracker_name] = 1

    return ID_TRACKER[tracker_name]


def reset_mem_cache(doit=False):
    '''
    This function will reset the memory cache.

    @param doit: Tell me, if you really want to do this. Defaults to false
    @type doit: boolean
    '''

    if doit:
        AUTHOR_NAMES[:] = []
        DOC_LIST[:] = []
        REALAUTHORS[:] = []
        REALAUTHOR_DATA[:] = []
        VIRTUALAUTHORS[:] = []
        VIRTUALAUTHOR_DATA[:] = []
        VIRTUALAUTHOR_CLUSTERS[:] = []
        VIRTUALAUTHOR_CLUSTER_CACHE.clear()
        VIRTUALAUTHOR_PROCESS_QUEUE.queue.clear()
        ID_TRACKER.clear()
        RELEVANT_RECORDS.clear()
        RA_VA_CACHE.clear()

        for key in UPDATES_LOG:
            UPDATES_LOG[key] = set()
