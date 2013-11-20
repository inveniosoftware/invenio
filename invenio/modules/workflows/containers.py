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

from .config import CFG_OBJECT_VERSION
from .loader import widgets


def create_hp_containers(iSortCol_0=None, sSortDir_0=None,
                         sSearch=None, version_showing=[CFG_OBJECT_VERSION.HALTED]):
    """
    Looks for related HPItems and groups them together in HPContainers

    @type hpitems: list
    @return: A list containing all the HPContainers.
    """
    from .models import BibWorkflowObject

    if iSortCol_0:
        iSortCol_0 = int(iSortCol_0)

    print '************************version_showing', version_showing

    bwobject_list = BibWorkflowObject.query.filter(
        BibWorkflowObject.id_parent != 0 and \
        BibWorkflowObject.version.in_(version_showing)).all()

    print 'GOT THAT MANY RECORDS HERE:', len(bwobject_list)
    if sSearch:
        print sSearch
        if len(sSearch) < 4:
            pass
        else:
            bwobject_list_tmp = []
            for bwo in bwobject_list:
                extra_data = bwo.get_extra_data()
                if bwo.id_parent == sSearch:
                    bwobject_list_tmp.append(bwo)
                elif bwo.id_user == sSearch:
                    bwobject_list_tmp.append(bwo)
                elif bwo.id_workflow == sSearch:
                    bwobject_list_tmp.append(bwo)
                elif extra_data['last_task_name'] == sSearch:
                    bwobject_list_tmp.append(bwo)
                else:
                    try:
                        widget = widgets[extra_data['widget']]
                        if sSearch in widget.__title__ or sSearch in extra_data['widget']:
                            bwobject_list_tmp.append(bwo)
                    except:
                        pass
                try:
                    if sSearch in extra_data['redis_search']['category']:
                        bwobject_list_tmp.append(bwo)
                    elif sSearch in extra_data['redis_search']['source']:
                        bwobject_list_tmp.append(bwo)
                    elif sSearch in extra_data['redis_search']['title']:
                        bwobject_list_tmp.append(bwo)
                except KeyError:
                    pass
            bwobject_list = bwobject_list_tmp

    if iSortCol_0 == -6:
        if sSortDir_0 == 'desc':
            bwobject_list.reverse()
    
    return bwobject_list

try:
    bwolist = create_hp_containers(version_showing=current_app.config['VERSION_SHOWING'])
    print "try succeded"
except:    
    print "try failed"
    bwolist = create_hp_containers()
