# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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


def create_hp_containers(iSortCol_0=None, sSortDir_0=None,
                         sSearch=None):
    """
    Looks for related HPItems and groups them together in HPContainers

    @type hpitems: list
    @return: A list containing all the HPContainers.
    """
    from .models import BibWorkflowObject

    if iSortCol_0:
        iSortCol_0 = int(iSortCol_0)

    bwobject_list = BibWorkflowObject.query.filter(
        BibWorkflowObject.id_parent != 0).all()

    if sSearch:
        if len(sSearch) < 4:
            pass
        else:
            bwobject_list2 = []
            for bwo in bwobject_list:
                extra_data = bwo.get_extra_data()
                if bwo.id_parent == sSearch:
                    bwobject_list2.append(bwo)
                elif bwo.id_user == sSearch:
                    bwobject_list2.append(bwo)
                elif sSearch in bwo.id_workflow:
                    bwobject_list2.append(bwo)
                elif sSearch in extra_data['widget']:
                    bwobject_list2.append(bwo)
                elif sSearch in extra_data['last_task_name']:
                    bwobject_list2.append(bwo)
                try:
                    if sSearch in extra_data['redis_search']['category']:
                        bwobject_list2.append(bwo)
                    elif sSearch in extra_data['redis_search']['source']:
                        bwobject_list2.append(bwo)
                    elif sSearch in extra_data['redis_search']['title']:
                        bwobject_list2.append(bwo)
                except KeyError:
                    pass
            bwobject_list = bwobject_list2

    if iSortCol_0 == -6:
        column = 'created'
        if sSortDir_0 == 'desc':
            bwobject_list.reverse()

    return bwobject_list


bwolist = create_hp_containers()
