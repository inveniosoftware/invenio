# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011, 2012 CERN.
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

from operator import itemgetter
from itertools import groupby

from bibauthorid_cluster_set import Cluster_set
from bibauthorid_cluster_set import cluster_sets_from_marktables
from bibauthorid_wedge import wedge
from bibauthorid_name_utils import generate_last_name_cluster_str
from bibauthorid_backinterface import get_all_names_from_personid
from bibauthorid_backinterface import in_results
from bibauthorid_general_utils import bibauthor_print
from bibauthorid_scheduler import schedule

def tortoise_from_scratch():
    cluster_sets = ((cs, sum(len(c.bibs) for c in cs.clusters))
        for cs in cluster_sets_from_marktables())
    cluster_sets = sorted(cluster_sets, key=itemgetter(1))
    args = [(x[0], ) for x in cluster_sets]
    sizs = map(itemgetter(1), cluster_sets)

    schedule(disambiguate, args, sizs)


def tortoise(pure=False, only_missing=False):
    names = create_lastname_list_from_personid()
    names = sorted(names, key=itemgetter(2))
    args = [(x[1], x[0], pure, only_missing) for x in names]
    sizs = map(itemgetter(2), names)

    schedule(disambiguate_last_name, args, sizs)


def tortoise_last_name(name, pure=False):
    lname = generate_last_name_cluster_str(name)

    names = create_lastname_list_from_personid()
    names = filter(lambda x: x[0] == name, names)

    if names:
        pids = names[0][1]
        bibauthor_print("Found %s(%s), %d pids" % (name, lname, len(pids)))
        disambiguate_last_name(pids, lname, pure, False)
    else:
        bibauthor_print("Sorry, %s(%s) not found in the last name clusters" % (name, lname))


def create_lastname_list_from_personid():
    '''
    This function generates a dictionary from a last name
    to list of personids which have this lastname.
    '''
    # ((personid, [full Name1], Nbibs) ... )
    all_names = get_all_names_from_personid()

    # ((personid, last_name, Nbibs) ... )
    all_names = ((row[0], generate_last_name_cluster_str(iter(row[1]).next()), row[2])
                  for row in all_names)

    # { (last_name, [(personid)... ], Nbibs) ... }
    all_names = groupby(sorted(all_names, key=itemgetter(1)), key=itemgetter(1))
    all_names = ((key, list(data)) for key, data in all_names)
    all_names = ((key, map(itemgetter(0), data), sum(x[2] for x in data)) for key, data in all_names)

    return all_names


def disambiguate_last_name(personids, last_name, pure, only_missing):
    '''
    Creates a cluster_set from personid and calls disambiguate.
    '''
    if only_missing and in_results(last_name):
        return

    cs = Cluster_set()
    if pure:
        cs.create_pure(personids, last_name)
    else:
        cs.create_skeleton(personids, last_name)
    disambiguate(cs)


def disambiguate(cluster_set):
    '''
    Updates personid from a list of personids, sharing common
    last name, and this last name.
    '''
    bibs = sum(len(c.bibs) for c in cluster_set.clusters)
    expected = bibs * (bibs - 1) / 2
    bibauthor_print("Start working on %s. Total number of bibs: %d, "
                    "maximum number of comparisons: %d"
                     % (cluster_set.last_name, bibs, expected))

    wedge(cluster_set)
    cluster_set.store()

