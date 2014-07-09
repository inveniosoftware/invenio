# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2009, 2010, 2011 CERN.
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
Handle requests from the web interface for Knowledge Base related
(admin) functions.
"""

from invenio.config import CFG_SITE_LANG
from invenio.modules.knowledge import dblayer as bibknowledge_dblayer
from invenio.modules.knowledge import api as bibknowledge

import invenio.legacy.template
bibknowledge_templates = invenio.legacy.template.load('bibknowledge')


def perform_request_knowledge_bases_management(ln=CFG_SITE_LANG, search="",
                                               descriptiontoo=""):
    """
    Returns the main page for knowledge bases management.

    @param ln language
    @param search search for this string in kb's
    @param descriptiontoo search in descriptions too
    @return the main page for knowledge bases management
    """
    kbs = bibknowledge.get_kbs_info()
    #if search is nonempty, filter out kb's that do not have the
    #the string that we search
    newkbs = []
    if search:
        for kb in kbs:
            skip = 0 #do-we-need-to-scan-more control
            kbname = kb['name']
            #get description if needed
            if descriptiontoo and kb['description'].count(search) > 0:
                #add and skip
                newkbs.append(kb)
                skip = 1
            #likewise: check if name matches
            if descriptiontoo and kbname.count(search) > 0:
                #add and skip
                newkbs.append(kb)
                skip = 1
            #get mappings
            mappings = bibknowledge_dblayer.get_kb_mappings(kbname)
            for mapping in mappings:
                if skip == 0:
                    key =  mapping['key']
                    value = mapping['value']
                    if key.count(search)> 0 or value.count(search)> 0:
                        #add this in newkbs
                        newkbs.append(kb)
                        #skip the rest, we know there's ok stuff in this kb
                        skip = 1
        kbs = newkbs

    return bibknowledge_templates.tmpl_admin_kbs_management(ln, kbs, search)

def perform_request_knowledge_base_show(kb_id, ln=CFG_SITE_LANG, sortby="to",
                                        startat=0, search_term=""):
    """
    Show the content of a knowledge base

    @param ln language
    @param kb a knowledge base id
    @param sortby the sorting criteria ('from' or 'to')
    @param startat start showing mapping rules at what number
    @param search_term search for this string in kb
    @return the content of the given knowledge base
    """
    name = bibknowledge_dblayer.get_kb_name(kb_id)
    mappings = bibknowledge_dblayer.get_kb_mappings(name, sortby)

    kb_type = bibknowledge_dblayer.get_kb_type(kb_id)
    #filter in only the requested rules if the user is searching..
    if search_term:
        newmappings = []
        for mapping in mappings:
            key =  mapping['key']
            value = mapping['value']
            if key.count(search_term)> 0 or value.count(search_term)> 0:
                newmappings.append(mapping)
        #we were searching, so replace
        mappings = newmappings
    #if this bk is dynamic, get the configuration from the DB, and a list of
    #collections as a bonus
    dyn_config = None
    collections = None
    if kb_type == 'd':
        from invenio.legacy.search_engine import get_alphabetically_ordered_collection_list
        dyn_config = bibknowledge_dblayer.get_kb_dyn_config(kb_id)
        collections = []
        collitems = get_alphabetically_ordered_collection_list()
        for collitem in collitems:
            collections.append(collitem[0])
    return bibknowledge_templates.tmpl_admin_kb_show(ln, kb_id, name,
                                                     mappings, sortby, startat,
                                                     kb_type, search_term,
                                                     dyn_config, collections)


def perform_request_knowledge_base_show_attributes(kb_id, ln=CFG_SITE_LANG,
                                                   sortby="to"):
    """
    Show the attributes of a knowledge base

    @param ln language
    @param kb a knowledge base id
    @param sortby the sorting criteria ('from' or 'to')
    @return the content of the given knowledge base
    """
    name = bibknowledge_dblayer.get_kb_name(kb_id)
    description = bibknowledge_dblayer.get_kb_description(name)
    kb_type =  bibknowledge_dblayer.get_kb_type(name)
    return bibknowledge_templates.tmpl_admin_kb_show_attributes(ln, kb_id, name,
                                                                description,
                                                                sortby, kb_type)


def perform_request_knowledge_base_show_dependencies(kb_id, ln=CFG_SITE_LANG,
                                                     sortby="to"):
    """
    Show the dependencies of a kb

    @param ln language
    @param kb a knowledge base id
    @param sortby the sorting criteria ('from' or 'to')
    @return the dependencies of the given knowledge base
    """
    name = bibknowledge_dblayer.get_kb_name(kb_id)
    format_elements = bibknowledge.get_elements_that_use_kb(name)

    return bibknowledge_templates.tmpl_admin_kb_show_dependencies(ln, kb_id, name, sortby, format_elements)

def perform_request_verify_rule(ln, kbid, left, right, leftorright, currentname, tuples):
    """
    Returns a page element by which the user chooses an action:
    What to do if a rule already exists in some kb.
    Parameters:
    @param ln language
    @param kbid current kb id
    @param left left side of rule
    @param right right side of rule
    @param leftorright "left" or "right" checking
    @param currentname the name of the current kb
    @param tuples a list containing "kb - rule" tuples
    """
    return bibknowledge_templates.tmpl_select_rule_action(ln, kbid, left, right, leftorright, currentname, tuples)

def perform_update_kb_config(kb_id, field, expression, collection):
    """
    Updates config by calling a db function.
    Parameters:
    @param kb_id knowledge base id
    @param field field configured to be used
    @param expression search expression
    @param collection search in this collection
    """
    #this will complain if the collection does not exist
    return bibknowledge_dblayer.save_kb_dyn_config(kb_id, field, expression, collection)

