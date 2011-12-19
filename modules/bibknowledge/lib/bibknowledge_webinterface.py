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

"""BibKnowledge URL handler."""

__revision__ = "$Id$"

from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory
from invenio import bibknowledgeadmin
from invenio.config import CFG_SITE_LANG

class WebInterfaceBibKnowledgePages(WebInterfaceDirectory):
    """ Handle /kb/ etc set of pages."""
    extrapath = ""

    def __init__(self, extrapath=""):
        """Constructor."""
        self.extrapath = extrapath

    def _lookup(self, component, path):
        """This handler parses dynamic URLs (/kb, /kb/export, /kb/upload etc)."""
        return WebInterfaceBibKnowledgePages(component), path


    def __call__(self, req, form):
        """Serve the page in the given language."""
        argd = wash_urlargd(form, {'ln': (str, CFG_SITE_LANG),
                                   'kb': (int, -1),
                                   'search': (str, ''), #what to search in the rules
                                   'descriptiontoo': (int, 0), #search descriptions, too
                                   'action': (str, ''),  #delete/new/attributes/update_attributes/add_mapping/edit_mapping/dynamic_update
                                   'chosen_option': (str, ''),  #for the 'really delete' dialog
                                   'sortby': (str, ''),  #sort rules by key or value
                                   'startat': (int, 0),  #sort rules by key or value
                                   'name': (str, ''), #name in new/rename operations
                                   'description': (str, ''), #description in new/rename operations
                                   'mapFrom': (str, ''), 'mapTo': (str, ''), #mappings
                                   'forcetype': (str, ''), #force mapping
                                   'replacements':  (str, ''), #needed for overlapping mappings
                                   'save_mapping':  (str, ''), #type of edit_mapping
                                   'delete_mapping':  (str, ''), #type of edit_mapping
                                   'field':  (str, ''), #for dynamic kbs
                                   'expression':  (str, ''), #for dynamic kbs
                                   'collection':  (str, ''), #for dynamic kbs
                                   'kbname':  (str, ''), #for exporting
                                   'format':  (str, ''), #for exporting
                                   'term': (str, ''), #for exporting to JQuery UI
                                   'searchkey': (str, ''), #for exporting to JQuery UI
                                   'kbtype': (str, ''),
                                   'limit': (int, None)})
        ln = argd['ln']
        kb = argd['kb']
        search = argd['search']
        term = argd['term']
        searchkey = argd['searchkey']
        descriptiontoo = argd['descriptiontoo']
        action = argd['action']
        chosen_option = argd['chosen_option']
        name = argd['name']
        description = argd['description']
        sortby = argd['sortby']
        startat = argd['startat']
        mapFrom = argd['mapFrom']
        mapTo = argd['mapTo']
        kbtype = argd['kbtype']
        field = argd['field']
        expression = argd['expression']
        collection = argd['collection']
        forcetype = argd['forcetype']
        replacements = argd['replacements']
        save_mapping = argd['save_mapping']
        delete_mapping = argd['delete_mapping']
        kbname = argd['kbname']
        format = argd['format']
        limit = argd['limit']

        req.argd = argd #needed by some lower level modules

        #check upload
        if self.extrapath == "upload":
            return bibknowledgeadmin.kb_upload(req, kb=kb, ln=ln)
        #check if this is "export"
        if self.extrapath == "export":
            return bibknowledgeadmin.kb_export(req, kbname=kbname, format=format, ln=ln, searchkey=searchkey, searchvalue=term, limit=limit)

        #first check if this is a specific action
        if action == "new":
            return bibknowledgeadmin.kb_add(req, kbtype=kbtype, sortby=sortby, ln=ln)
        if action == "attributes":
            return bibknowledgeadmin.kb_show_attributes(req, kb=kb, ln=ln)
        if action == "update_attributes":
            return bibknowledgeadmin.kb_update_attributes(req, kb=kb, name=name, description=description, ln=ln)
        if action == "delete":
            return bibknowledgeadmin.kb_delete(req, kb=kb, ln=ln, chosen_option=chosen_option)
        if action == "add_mapping":
            return bibknowledgeadmin.kb_add_mapping(req, kb=kb, ln=ln, mapFrom=mapFrom, mapTo=mapTo, forcetype=forcetype, replacements=replacements, kb_type=kbtype)
        if action == "edit_mapping":
            return bibknowledgeadmin.kb_edit_mapping(req, kb=kb, key=mapFrom, mapFrom=mapFrom, mapTo=mapTo, update=save_mapping, delete=delete_mapping, sortby=sortby, ln=ln)
        if action == "dynamic_update":
            return bibknowledgeadmin.kb_dynamic_update(req, kb_id=kb, ln=ln, field=field, expression=expression, collection=collection)
        #then, check if this is a "list all" or "show kb" request..
        if (kb > -1):
            return bibknowledgeadmin.kb_show(req, ln=ln, sortby=sortby, startat=startat, kb=kb, search=search)
        else:
            return bibknowledgeadmin.index(req, ln=ln, search=search, descriptiontoo=descriptiontoo)

    index = __call__

