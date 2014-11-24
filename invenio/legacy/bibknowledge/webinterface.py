# This file is part of Invenio.
# Copyright (C) 2009, 2010, 2011, 2012, 2013, 2014, 2015 CERN.
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

"""BibKnowledge URL handler."""

__revision__ = "$Id$"

from invenio.config import CFG_SITE_LANG
from invenio.ext.legacy.handler import WebInterfaceDirectory, wash_urlargd
from invenio.legacy.bibknowledge import admin as bibknowledgeadmin


class WebInterfaceBibKnowledgePages(WebInterfaceDirectory):

    """Handle /kb/ etc set of pages."""

    extrapath = ""

    def __init__(self, extrapath=""):
        """Constructor."""
        self.extrapath = extrapath

    def _lookup(self, component, path):
        """The parser handle dynamic URLs.

        URL (/kb, /kb/export, /kb/upload etc).
        """
        return WebInterfaceBibKnowledgePages(component), path

    def __call__(self, req, form):
        """Serve the page in the given language."""
        argd = wash_urlargd(form, {'ln': (str, CFG_SITE_LANG),
                                   'kb': (int, -1),
                                   # what to search in the rules
                                   'search': (str, ''),
                                   # search descriptions, too
                                   'descriptiontoo': (int, 0),
                                   # delete/new/attributes/update_attributes/add_mapping/edit_mapping/dynamic_update
                                   'action': (str, ''),
                                   # for the 'really delete' dialog
                                   'chosen_option': (str, ''),
                                   # sort rules by key or value
                                   'sortby': (str, ''),
                                   # sort rules by key or value
                                   'startat': (int, 0),
                                   # name in new/rename operations
                                   'name': (str, ''),
                                   # description in new/rename operations
                                   'description': (str, ''),
                                   # mappings
                                   'mapFrom': (str, ''), 'mapTo': (str, ''),
                                   'key': (str, ''),  # key
                                   'forcetype': (str, ''),  # force mapping
                                   # needed for overlapping mappings
                                   'replacements': (str, ''),
                                   # type of edit_mapping
                                   'save_mapping': (str, ''),
                                   # type of edit_mapping
                                   'delete_mapping': (str, ''),
                                   'field': (str, ''),  # for dynamic kbs
                                   'expression': (str, ''),  # for dynamic kbs
                                   'collection': (str, ''),  # for dynamic kbs
                                   'kbname': (str, ''),  # for exporting
                                   'searchtype': (str, ''),  # for exporting
                                   'format': (str, ''),  # for exporting
                                   # for exporting to JQuery UI
                                   'term': (str, ''),
                                   # for exporting to JQuery UI
                                   'searchkey': (str, ''),
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
        key = argd['key']
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
        searchtype = argd['searchtype']
        limit = argd['limit']

        req.argd = argd  # needed by some lower level modules

        # check upload
        if self.extrapath == "upload":
            return bibknowledgeadmin.kb_upload(req, kb=kb, ln=ln)
        # check if this is "export"
        if self.extrapath == "export":
            return bibknowledgeadmin.kb_export(req, kbname=kbname,
                                               format=format, ln=ln,
                                               searchkey=searchkey,
                                               searchvalue=term,
                                               searchtype=searchtype,
                                               limit=limit)

        # first check if this is a specific action
        if action == "new":
            return bibknowledgeadmin.kb_add(req, kbtype=kbtype,
                                            sortby=sortby, ln=ln)
        if action == "attributes":
            return bibknowledgeadmin.kb_show_attributes(req, kb=kb, ln=ln)
        if action == "update_attributes":
            return bibknowledgeadmin.kb_update_attributes(
                req, kb=kb, name=name, description=description, ln=ln)
        if action == "delete":
            return bibknowledgeadmin.kb_delete(
                req, kb=kb, ln=ln, chosen_option=chosen_option)
        if action == "add_mapping":
            return bibknowledgeadmin.kb_add_mapping(
                req, kb=kb, ln=ln, mapFrom=mapFrom, mapTo=mapTo,
                forcetype=forcetype, replacements=replacements,
                kb_type=kbtype)
        if action == "edit_mapping":
            return bibknowledgeadmin.kb_edit_mapping(
                req, kb=kb, key=key, mapFrom=mapFrom, mapTo=mapTo,
                update=save_mapping, delete=delete_mapping,
                sortby=sortby, ln=ln)
        if action == "dynamic_update":
            return bibknowledgeadmin.kb_dynamic_update(
                req, kb_id=kb, ln=ln, field=field, expression=expression,
                collection=collection)
        # then, check if this is a "list all" or "show kb" request..
        if (kb > -1):
            return bibknowledgeadmin.kb_show(
                req, ln=ln, sortby=sortby, startat=startat, kb=kb,
                search=search)
        else:
            return bibknowledgeadmin.index(
                req, ln=ln, search=search, descriptiontoo=descriptiontoo)

    index = __call__
