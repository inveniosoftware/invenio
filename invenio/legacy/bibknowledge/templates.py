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

"""HTML Templates for BibKnowledge administration"""

__revision__ = ""

# non Invenio imports
import os
import cgi

# Invenio imports
from invenio.base.i18n import gettext_set_language
from invenio.config import CFG_SITE_URL, CFG_WEBDIR

MAX_MAPPINGS = 100 #show max this number of mappings on one page


class Template:
    """Templating class."""

    def tmpl_admin_kbs_management(self, ln, kbs, lookup_term=""):
        """
        Returns the main management console for knowledge bases (shows a list of them).

        @param ln: language
        @param kbs: a list of dictionaries with knowledge bases attributes
        @param lookup_term: hunt for this string in kb's
        @return main management console as html
        """
        _ = gettext_set_language(ln)    # load the right message language

        #top of the page and table header
        searchforaterm_field = '<input type="text" name="search" value="%s" />' % cgi.escape(lookup_term, 1)
        searchforaterm = _("Limit display to knowledge bases matching %(keyword_field)s in their rules and descriptions") % \
                         {'keyword_field': searchforaterm_field}
        out = '''

        <!--make a search box-->
        <table class="admin_wvar" cellspacing="0">
                 <tr><td>
                 <form action="kb">
                 %(searchforaterm)s
                 <input type="hidden" name="ln" value="%(ln)s" />
                 <input type="hidden" name="descriptiontoo" value="1" />
                 <input type="submit" class="adminbutton" value="%(search_button)s">
                 </form>
                 </td></tr></table>


        <table class="admin_wvar" width="95%%" cellspacing="0">
        <tr>
        <th class="adminheaderleft" >&nbsp;</th>
        <th class="adminheaderleft" >%(name)s</th>
        <th class="adminheaderleft" >%(description)s</th>
        <th class="adminheadercenter" >%(action)s&nbsp;
          &nbsp;[<a href="%(siteurl)s/help/admin/bibknowledge-admin-guide#admin">?</a>]
        </th>
        </tr>''' % {'ln': ln,
                    'search': lookup_term,
                    'searchforaterm': searchforaterm,
                    'siteurl': CFG_SITE_URL,
                    'name': _("Name"),
                    'description': _("Description"),
                    'action': _("Action"),
                    'search_button': _("Search")}


        #table content: kb names, description and actions
        if len(kbs) == 0:
            out += '''<tr>
            <td colspan="5" class="admintd" align="center"><em>%s</em></td>
            </tr>''' % _("No Knowledge Base")
        else:
            line = 0
            for kb_attributes in kbs :
                kb_attributes['style'] = ""
                if line % 2:
                    kb_attributes['style'] = 'background-color: rgb(235, 247, 255);'
                line += 1
                kb_attributes['ln'] = ln
                kb_attributes['siteurl'] = CFG_SITE_URL
                kb_attributes['search'] = cgi.escape(lookup_term, 1)
                kb_attributes['name'] = cgi.escape(kb_attributes['name'])
                kb_attributes['description'] = cgi.escape(kb_attributes['description'])
                kb_attributes['delete'] = _("Delete")
                row_content = '''<tr>
                <td class="admintdright" style="vertical-align: middle; %(style)s">&nbsp;</td>
                <td class="admintdleft" style="vertical-align: middle; %(style)s white-space: nowrap;">
                <a href="kb?ln=%(ln)s&amp;kb=%(id)s&amp;search=%(search)s">%(name)s</a></td>
                <td class="admintdleft"style="vertical-align: middle; %(style)s">%(description)s</td>
                <td class="admintd" style="vertical-align: middle; %(style)s white-space: nowrap;">
                <form action="kb?ln=%(ln)s" type="POST">
                <input type="submit" class="adminbutton" value="%(delete)s">
                <input type="hidden" id="kb" name="kb" value="%(id)s">
                <input type="hidden" id="action" name="action" value="delete">
                </form>
                </td>
                </tr>
                ''' % kb_attributes
                out += row_content

        #table footer, buttons and bottom of the page
        out += ''' </table>
        <table align="center" width="95%">
        <tr>
        <td align="left" valign="top">&nbsp;</td>
        '''
        out += '''
        <td align="left">
        <form action="kb">
        <input type="hidden" name="action" value="new" />
        <input type="hidden" name="ln" value="%(ln)s" />
        <input class="adminbutton" type="submit" value="%(add_new)s" />

        </form>
        </td>

        <td align="right">
        <form method="post" action="kb?ln=%(ln)s&amp;action=new&amp;kbtype=dynamic">
        <input class="adminbutton" type="submit" value="%(config_dyn)s" />
        </form>
        </td>

        <td align="right">
        <form method="post" action="kb?action=new&amp;kbtype=taxonomy&amp;ln=%(ln)s">
        <input class="adminbutton" type="submit" value="%(add_tax)s" />
        </form>
        </td>

        </tr>
        </table>''' % {'ln': ln, 'add_new': _("Add New Knowledge Base"),
                       'config_dyn': _("Configure a dynamic KB"),
                       'add_tax': _("Add New Taxonomy") }

        return out

    def tmpl_kb_prevnextlink(self, ln, p_or_n, kb_id, sortby, startat):
        """
        An aux routine to make "Previous" or "Next" link
        @param ln: language
        @param p_or_n: p for previous, n for next
        @param kb_id: knowledge base id
        @param sortby: sort by to or from
        @param startat: start at this pair
        """
        _ = gettext_set_language(ln)    # load the right message language
        startat = str(startat) #to be sure
        label = _("Next")
        if p_or_n == 'p':
            label = _("Previous")
        r_url = '<a href="kb?ln=%(ln)s&amp;kb=%(kb_id)s&amp;'% {'ln':ln,
                                                                'kb_id':kb_id}
        r_url += 'sortby=%(sortby)s&amp;startat=%(start)s">' % {'sortby':sortby,
                                                                'start':startat}
        r_url += label+'</a>'
        return r_url


    def tmpl_admin_show_taxonomy(self, ln, kb_id, kb_name):
        """
        An auxiliary method used by tmpl_admin_kb_show in order to make a form to upload an ref file.
        @param ln: language
        @param kb_id: knowledge base id
        @param kb_name: knowledge base name
        @param basefilename: the file name (if already exists)
        """
        _ = gettext_set_language(ln)    # load the right message language
        #check if this kb already has a file associated with it
        #it would be named CFG_WEBDIR+"/kbfiles/"+kb_id+".rdf"
        rdfname = CFG_WEBDIR+"/kbfiles/"+str(kb_id)+".rdf"
        webname = CFG_SITE_URL+"/kb/export?kbname="+cgi.escape(kb_name, 1)
        out = ""
        if os.path.isfile(rdfname):
            out += _("This knowledge base already has a taxonomy file.")+" "
            out += _("If you upload another file, the current version will be replaced.")
            out += "<br/>"
            out += _("The current taxonomy can be accessed with this URL: %s") % \
                   ('<a href="'+webname+'">'+webname+"</a>")
        else:
            out += _("Please upload the RDF file for taxonomy %s") % cgi.escape(kb_name)
        out += """
          <br/>
          <!-- enctype="multipart/form-data"-->
          <form method="post" action="kb/upload" name="upload" enctype="multipart/form-data">
          <input style="display:none;" name="kb", value="%(kb_id)s"/>
          <input type="file" name="file"/>
          <input type="submit" name="submit" value="%(upload)s" class="adminbutton"/>
          </form>
          """ % {'kb_id': kb_id,
                 'upload': _("Upload")}
        return out


    def tmpl_admin_dynamic_kb(self, ln, kb_id, dyn_config=None, collections=None, exportstr=""):
        """
        An auxiliary method used by tmpl_admin_kb_show in order to configure a dynamic (collection based) kb.
        @param ln: language
        @param kb_id: the id of the kb
        @param kb_name: the name of the kb
        @param dyn_config: a dictionary with keys: expression
        @param collections: a list of collection names
        @param exportstr: a string to print about exporting
        """
        _ = gettext_set_language(ln)    # load the right message language
        expression = ""
        field = ""
        collection = ""

        if dyn_config.has_key('field'):
            field = dyn_config['field']

        if dyn_config.has_key('expression'):
            expression = dyn_config['expression']
        if dyn_config.has_key('collection'):
            collection = dyn_config['collection']

        pleaseconf = _("Please configure")+"<P>"
        pleaseconf += _("A dynamic knowledge base is a list of values of a \
                         given field. The list is generated dynamically by \
                         searching the records using a search expression.")
        pleaseconf += "<br/>"
        pleaseconf += _("Example: Your records contain field 270__a for \
                         the name and address of the author's institute. \
                         If you set the field to '270__a' and the expression \
                         to '270__a:*Paris*', a list of institutes in Paris \
                         will be created.")+"<br/>"
        pleaseconf += _("If the expression is empty, a list of all values \
                         in 270__a will be created.")+"<br/>"
        pleaseconf += _("If the expression contains '%', like '270__a:*%*', \
                         it will be replaced by a search string when the \
                         knowledge base is used.")+"<br/><br/>"
        pleaseconf += _("You can enter a collection name if the expression \
                         should be evaluated in a specific collection.")+"<br/><br/>"
        pleaseconf += _("Example 1: Your records contain field 270__a for \
                         the name and address of the author's institute. \
                         If you set the field to '270__a' and the expression \
                         to '270__a:*Paris*', a list of institutes in Paris \
                         will be created.")+"<br/><br/>"
        pleaseconf += _("Example 2: Return the institute's name (100__a) when the \
                         user gives its postal code (270__a): \
                         Set field to 100__a, expression to 270__a:*%*.")+"<br/><br/>"
        #create a pretty select box
        selectbox = "<select name=\"collection\"><option value=\""+ _("Any collection") +"\">"+_("Any collection")+"</option>"
        for mycoll in collections:
            selectbox += "<option value=\""+mycoll+"\""
            if mycoll == collection:
                selectbox += " selected=\"1\" "
            selectbox += ">"+mycoll+"</option>"
        selectbox += "</select>"
        pleaseconf += '''<form action="kb">
                         Field: <input name="field" value="%(field)s"/>
                         Expression: <input name="expression" value="%(expression)s"/>
                         Collection: %(selectbox)s
                         <input type="hidden" name="action" value="dynamic_update"/>
                         <input type="hidden" name="ln" value="%(ln)s"/>
                         <input type="hidden" name="kb" value="%(kb_id)s"/>
                         <input type="submit" name="submit" value="%(save)s" class="adminbutton"/>
                         </form>''' % { 'kb_id': kb_id,
                                        'expression': cgi.escape(expression, 1),
                                        'field': cgi.escape(field, 1),
                                        'collection': cgi.escape(collection, 1),
                                        'selectbox': selectbox, 'ln': ln ,
                                        'save': _("Save")}
        if field or expression:
            pleaseconf += "<p>"+_("Exporting: ")
            pleaseconf += "<a href=\""+exportstr+"\">"+exportstr+"</a><br/>"
        return pleaseconf

    def tmpl_admin_kb_show(self, ln, kb_id, kb_name, mappings,
                           sortby, startat=0, kb_type=None,
                           lookup_term="", dyn_config=None, collections=None):
        """
        Returns the content of a knowledge base.

        @param ln: language
        @param kb_id: the id of the kb
        @param kb_name: the name of the kb
        @param mappings: a list of dictionaries with mappings
        @param sortby: the sorting criteria ('from' or 'to')
        @param startat: start showing the mappings from number x. Usefull for large kb's.
        @param kb_type: None or 't' meaning taxonomy, or 'd' meaning a dynamic kb.
        @param lookup_term: focus on this left side if it is in the KB
        @param dyn_config: configuration for dynamic kb's
        @param collections: a list of collections names (will be needed by dyn kb)
        @return main management console as html
        """

        _ = gettext_set_language(ln)    # load the right message language

        #top of the page and  main table that split screen in two parts

        out = '''
        <table class="admin_wvar" cellspacing="0">
        <tr><th colspan="4" class="adminheaderleft">%(menu)s</th></tr>
        <tr>
        <td>0.&nbsp;<small><a href="kb?ln=%(ln)s&amp;\
sortby=%(sortby)s">%(close)s</a></small>&nbsp;</td>
        <td>1.&nbsp;<small>%(mappings)s</small>&nbsp;</td>
        <td>2.&nbsp;<small><a href="kb?ln=%(ln)s&amp;\
action=attributes&amp;kb=%(kb_id)s&amp;sortby=%(sortby)s">%(attributes)s</a>
        </small>&nbsp;</td>
        </tr>
        </table> ''' % {'ln':ln,
                        'kb_id':kb_id,
                        'sortby':sortby,
                        'close': _("Close Editor"),
                        'mappings': _("Knowledge Base Mappings"),
                        'attributes':_("Knowledge Base Attributes"),
                        'dependencies':_("Knowledge Base Dependencies"),
                        'menu': _("Menu")}

        #Define some constants
        try:
            startati = int(startat)
        except ValueError:
            startati = 0

        #to note about exporting..
        export = CFG_SITE_URL+"/kb/export?kbname="+cgi.escape(kb_name, 1)

        if kb_type == 'd':
            #it's a dynamic kb. Create a config form.

            return self.tmpl_admin_dynamic_kb(ln, kb_id, dyn_config, collections, export)

        if kb_type == 't':
            #it's a taxonomy (ontology). Show a dialog to upload it.
            return self.tmpl_admin_show_taxonomy(ln, kb_id, kb_name)

        hereyoucan = _("Here you can add new mappings to this base \
                        and change the base attributes.")

        out += '<p>'+hereyoucan+'<table width="100%" align="center"><tr>'

        #First column of table: add mapping form
        out += '''
        <td width="300" valign="top">

        <form name="addNewMapping"
        action="kb?ln=%(ln)s&amp;action=add_mapping&amp;kb=%(kb_id)s&amp;\
sortby=%(sortby)s&amp;forcetype=no&amp;kb_type=%(kb_type)s"
        method="post">''' % {'ln':ln, 'kb_id':kb_id,
                             'sortby':sortby, 'kb_type': kb_type}

        mapfromstring = _("Map From")
        maptostring = _("To")
        out += '''
        <table class="admin_wvar" width="100%%" cellspacing="0">
        <tr>
        <th colspan="2" class="adminheaderleft">
        Add New Mapping &nbsp;
        [<a href="%(siteurl)s/help/admin/bibknowledge-admin-guide#admin">?</a>]
        </th>
        </tr>

        <tr>
        <td class="admintdright">
        <label for="mapFrom">
        <span style="white-space: nowrap;">%(mapfrom)s</span>
        </label>:&nbsp;</td>
        <td><input tabindex="1" name="mapFrom" type="text"
                   id="mapFrom" size="25"/>
        </td>
        </tr>
        <tr>
        <td class="admintdright"><label for="mapTo">%(mapto)s</label>:&nbsp;
        </td>
        <td><input tabindex="2" name="mapTo" type="text" id="mapTo" size="25"/>
        </td>
        </tr>

        <tr>
        <td colspan="2" align="right"><input tabindex="3"
            class="adminbutton" type="submit" value="Add new Mapping"/></td>
        </tr>
        </table>
        </form>


        <!--add a search box -->
        <form name="kb">
        <table class="admin_wvar" width="100%%" cellspacing="0">
        <tr>
        <th colspan="2" class="adminheaderleft">%(searchforamapping)s</th>
        </tr>

        <tr>
        <td class="admintdright"><span style="white-space: nowrap;">%(search)s
                                 </span></label>:&nbsp;</td>
        <td><input name="search" type="text" value="%(lookup_term)s" size="25"/>
        </td>
            <input type="hidden" name="ln" value="%(ln)s" />
            <input type="hidden" name="kb" value="%(kb_id)s"/>
        </tr>

        <td colspan="2" align="right">
          <input class="adminbutton" type="submit" value="%(search)s"/>
        </td>
        </tr>
        </table>
        </form>

        </td>
        ''' % {'siteurl':CFG_SITE_URL,
               'mapfrom': mapfromstring, 'mapto': maptostring,
               'search': _("Search"), 'ln': ln, 'kb_id':kb_id,
               'lookup_term': cgi.escape(lookup_term, 1),
               'searchforamapping': _("Search for a mapping") }

        #calculate if prev/next are needed
        #add prev/next buttons if needed
        prevlink = ""
        nextlink = ""

        if startati > 0:
            newstart = startati-MAX_MAPPINGS
            if newstart < 0:
                newstart = 0
            prevlink = self.tmpl_kb_prevnextlink(ln, 'p', kb_id, sortby, newstart)

        if len(mappings) > startati+MAX_MAPPINGS:
            #all of them were not shown yet
            newstart = startati+MAX_MAPPINGS
            nextlink = self.tmpl_kb_prevnextlink(ln, 'n', kb_id, sortby, newstart)

        #Second column: mappings table
        #header and footer
        out += '''
        <td valign="top">

        <table class="admin_wvar">
        <thead>
        <!--prev/next-->
        <tr>
        <td>%(prevlink)s</td><td>%(nextlink)s</td>
        </tr>

        <tr>
        <th class="adminheaderleft" width="25">&nbsp;</th>
        <th class="adminheaderleft" width="34%%"><a href="kb?ln=%(ln)s&amp;kb=%(kb_id)s&amp;sortby=from">%(mapfrom)s</a></th>
        <th class="adminheaderleft">&nbsp;</th>
        <th class="adminheaderleft" width="34%%"><a href="kb?ln=%(ln)s&amp;kb=%(kb_id)s&amp;sortby=to">%(mapto)s</a></th>
        <th class="adminheadercenter" width="25%%">Action&nbsp;&nbsp;&nbsp;[<a href="%(siteurl)s/help/admin/bibknowledge-admin-guide#admin">?</a>]</th>
        </tr>
        </thead>
        <tfoot>
        <tr>
        <td colspan="5">&nbsp;</td>
        </tr>
        </tfoot>
        <tbody>
        ''' % {'ln':ln,
               'kb_id':kb_id,
               'siteurl':CFG_SITE_URL,
               'mapfrom': cgi.escape(mapfromstring, 1), 'mapto': cgi.escape(maptostring, 1),
               'prevlink': prevlink, 'nextlink': nextlink }

        #table content: key, value and actions
        if len(mappings) == 0:
            out += '''
            <tr>
            <td colspan="5" class="admintd" align="center"><em>%s</em></td>
            </tr></tbody>''' % _("Knowledge base is empty")
        else:
            line = 0
            tabindex_key = 6
            tabindex_value = 7
            tabindex_save_button = 8
            mnum = 0 #current iteration in mappings
            for mapping in mappings:
                #roll to startat
                mnum += 1
                if mnum > startati and mnum <= startati+MAX_MAPPINGS:
                    style = "vertical-align: middle;"
                    if line % 2:
                        style += 'background-color: rgb(235, 247, 255);'
                    line += 1
                    tabindex_key += 3
                    tabindex_value += 3
                    tabindex_save_button += 3
                    row_content = '''
                    <tr>
                    <td colspan="5">
                    <form action="kb?action=edit_mapping&amp;ln=%(ln)s&amp;kb=%(kb_id)s&amp;sortby=%(sortby)s" name="%(key)s" method="post">
                    <table>
                    <tr>
                    <td class="admintdright" style="%(style)s" width="5">
                    &nbsp;
                    <input type="hidden" name="key" value="%(key)s"/>
                    </td>
                    <td class="admintdleft" style="%(style)s">
                        <input type="text" name="mapFrom" size="30" maxlength="255" value="%(key)s" tabindex="%(tabindex_key)s"/>
                    </td>
                    <td class="admintdleft" style="%(style)s white-space: nowrap;" width="5">=&gt;</td>
                    <td class="admintdleft"style="%(style)s">
                        <input type="text" name="mapTo" size="30" value="%(value)s" tabindex="%(tabindex_value)s">
                    </td>
                    <td class="admintd" style="%(style)s white-space: nowrap;">
                        <input class="adminbutton" type="submit" name="save_mapping" value="%(save)s" tabindex="%(tabindex_save_button)s"/>
                        <input class="adminbutton" type="submit" name="delete_mapping" value="%(delete)s"/></td>
                    </tr></table></form></td></tr>
                    ''' % {'key': cgi.escape(mapping['key'], 1),
                        'value':cgi.escape(mapping['value'], 1),
                        'ln':ln,
                        'style':style,
                        'tabindex_key': tabindex_key,
                        'tabindex_value': tabindex_value,
                        'tabindex_save_button': tabindex_save_button,
                        'kb_id':kb_id,
                        'sortby':sortby,
                        'save': _("Save"),
                        'delete': _("Delete")}

                    out += row_content

        #End of table
        out += '</tbody></table>'

        out += prevlink+"&nbsp;"+nextlink

        out += '</td>'
        out += '''
        <td width="20%">&nbsp;</td>
        </tr>
        </table>
        '''
        #add a note about exporting
        out += "<p>"+_("You can get a these mappings in textual format by: ")
        out += "<a href=\""+export+"\">"+export+"</a><br/>"
        out += _("And the KBA version by:")+" "
        export = export+"&format=kba"
        out += "<a href=\""+export+"\">"+export+"</a><br/>"

        #add script that will put focus on first field of "add mapping" form
        out += '''
        <script type="text/javascript">
        self.focus();document.addNewMapping.mapFrom.focus()
        </script>
        '''

        return out

    def tmpl_admin_kb_show_attributes(self, ln, kb_id, kb_name, description, sortby, kb_type=None):
        """
        Returns the attributes of a knowledge base.

        @param ln: language
        @param kb_id: the id of the kb
        @param kb_name: the name of the kb
        @param description: the description of the kb
        @param sortby: the sorting criteria ('from' or 'to')
        @param kb_type: None or taxonomy
        @return main management console as html
        """

        _ = gettext_set_language(ln)    # load the right message language

        out = '''
        <table class="admin_wvar" cellspacing="0">
        <tr><th colspan="4" class="adminheaderleft">%(menu)s</th></tr>
        <tr>
        <td>0.&nbsp;<small><a href="kb?ln=%(ln)s&amp;sortby=%(sortby)s">%(close)s</a></small>&nbsp;</td>
        <td>1.&nbsp;<small><a href="kb?ln=%(ln)s&amp;kb=%(kb_id)s&amp;sortby=%(sortby)s">%(mappings)s</a></small>&nbsp;</td>
        <td>2.&nbsp;<small>%(attributes)s</small>&nbsp;</td>
        </tr>
        </table> ''' % {'ln':ln,
                        'kb_id':kb_id,
                        'sortby':sortby,
                        'close': _("Close Editor"),
                        'menu': _("Menu"),
                        'mappings': _("Knowledge Base Mappings"),
                        'attributes':_("Knowledge Base Attributes"),
                        'dependencies':_("Knowledge Base Dependencies")}

        out += '''
        <form name="updateAttributes"
        action="kb?ln=%(ln)s&amp;action=update_attributes&amp;kb=%(kb_id)s&amp;sortby=%(sortby)s&kb_type=%(kb_type)s" method="post">
        <table class="admin_wvar" cellspacing="0">
        <tr>

        ''' % {'ln':ln,
               'kb_id':kb_id,
               'sortby':sortby,
               'kb_type':kb_type}

        out += '''
        <th colspan="2" class="adminheaderleft">%(kb_name)s attributes&nbsp;[<a href="%(siteurl)s/help/admin/bibknowledge-admin-guide#admin">?</a>]</th>''' % {'kb_name': kb_name,
                                                                                                                                                       'siteurl': CFG_SITE_URL}

        out += '''
         </tr>
        <tr>
        <td class="admintdright">
        <input type="hidden" name="key" value="%(kb_id)s"/>
        <label for="name">Name</label>:&nbsp;</td>
        <td><input tabindex="4" name="name" type="text" id="name" size="25" value="%(kb_name)s"/></td>
        </tr>
        <tr>
        <td  class="admintdright" valign="top"><label for="description">Description</label>:&nbsp;</td>
        <td><textarea tabindex="5" name="description" id="description" rows="4" cols="25">%(kb_description)s</textarea> </td>
        </tr>
        <tr>
        <td>&nbsp;</td>
        <td align="right"><input tabindex="6" class="adminbutton" type="submit" value="%(update_base_attributes)s"/></td>
        </tr>
        </table>
        </form></td>''' % {'kb_name': cgi.escape(kb_name, 1),
                           'kb_description': cgi.escape(description, 1),
                           'kb_id':kb_id,
                           'update_base_attributes':_("Update Base Attributes")}

        return out

    def tmpl_admin_kb_show_dependencies(self, ln, kb_id, kb_name, sortby, format_elements):
        """
        Returns the attributes of a knowledge base.

        @param ln: language
        @param kb_id: the id of the kb
        @param kb_name: the name of the kb
        @param sortby: the sorting criteria ('from' or 'to')
        @param format_elements: the elements that use this kb
        """

        _ = gettext_set_language(ln)    # load the right message language

        out = '''
        <table class="admin_wvar" cellspacing="0">
        <tr><th colspan="4" class="adminheaderleft">%(menu)s</th></tr>
        <tr>
        <td>0.&nbsp;<small><a href="kb?ln=%(ln)s&amp;sortby=%(sortby)s">%(close)s</a></small>&nbsp;</td>
        <td>1.&nbsp;<small><a href="kb?ln=%(ln)s&amp;kb=%(kb_id)s&amp;sortby=%(sortby)s">%(mappings)s</a></small>&nbsp;</td>
        <td>2.&nbsp;<small><a href="kb?ln=%(ln)s&amp;action=attributes&amp;kb=%(kb_id)s&amp;sortby=%(sortby)s">%(attributes)s</a></small>&nbsp;</td>
        </tr>
        </table> <br/>''' % {'ln':ln,
                             'kb_id':kb_id,
                             'sortby':sortby,
                             'close': _("Close Editor"),
                             'menu' : _("Menu"),
                             'mappings': _("Knowledge Base Mappings"),
                             'attributes':_("Knowledge Base Attributes"),
                             'dependencies':_("Knowledge Base Dependencies")}

        out += ''' <table width="90%" class="admin_wvar" cellspacing="0"><tr>'''
        out += '''
        <th class="adminheaderleft">Format Elements used by %(name)s*</th>
        </tr>
        <tr>
        <td valign="top">&nbsp;''' % {"name": kb_name}

        if len(format_elements) == 0:
            out += '<p align="center"><i>%s</i></p>' % \
                   _("This knowledge base is not used in any format elements.")
        for format_element in format_elements:
            name = format_element['name']
            out += '''<a href="format_elements_doc?ln=%(ln)s#%(anchor)s">%(name)s</a><br/>''' % {'name':"bfe_"+name.lower(),
                                                                                                 'anchor':name.upper(),
                                                                                                 'ln':ln}
        out += '''
        </td>
        </tr>
        </table>
        <b>*Note</b>: Some knowledge base usages might not be shown. Check manually.
        '''

        return out


    def tmpl_select_rule_action(self, ln, kbid, left, right, leftorright, current, dicts):
        """
        Returns a form of actions for the user to decide what to do
        if there are overlapping rules.
        @param ln: language
        @param kbid: knowledge base id
        @param left: mapFrom side of current rule
        @param right: mapTo side of current rule
        @param leftorright: "left" or "right"
        @param current: the current item
        @param dicts: an array of mapping dictionaries with 'key', 'value', 'id'
        """
        _ = gettext_set_language(ln)    # load the right message language

        gen = _("Your rule: %s") % (' <code style="border:1px solid #999">'+cgi.escape(left)+'</code> =&gt; <code style="border:1px solid #999">'+cgi.escape(right)+"</pre><p>")
        if (leftorright=='left'):
            gen += _("The left side of the rule (%s) already appears in these knowledge bases:") % \
                   ('<code>' + cgi.escape(left) + '</code>')
        else:
            gen += _("The right side of the rule (%s) already appears in these knowledge bases:") % \
                   ('<code>' + cgi.escape(right) + '</code>')
        gen += "<br/>"
        inkbs = []
        dontdoit = False
        for d in dicts:
            kb = d['kbname']
            if kb == current and leftorright == 'left':
                dontdoit = True
                #two rules with same left side in the same kb? no.
            if inkbs.count(kb)==0:
                inkbs.append(kb)
        kbstr = ", ".join(['<b>%s</b>' % cgi.escape(inkb) for inkb in inkbs])
        gen += kbstr
        message = _("Please select action")
        optreplace = _("Replace the selected rules with this rule")
        optadd = _("Add this rule in the current knowledge base")+" ("+cgi.escape(current, 1)+")"
        optcancel = _("Cancel: do not add this rule")
        formreplace = '''<form action="kb?action=add_mapping&amp;ln=%(ln)s&amp;kb=%(kb_id)s&amp;forcetype=all"
                    method="post">
                    <input type="hidden" name="mapFrom" value="%(left)s"/>
                    <input type="hidden" name="mapTo" value="%(right)s"/>
                 ''' % {  'ln':ln, 'kb_id':kbid, 'left':cgi.escape(left, 1), 'right':cgi.escape(right, 1) }

        #make a selectable list of kb's where to push the value..
        for d in dicts:
            kb = d['kbname']
            l = d['key']
            r = d['value']
            value = cgi.escape(kb, 1)+"++++"+cgi.escape(l, 1)+"++++"+cgi.escape(r, 1)
            formreplace += '<input type="checkbox" name="replacements" value="'+value+'" />' + \
                           '<b>' + cgi.escape(kb) + '</b>: <code style="border:1px solid #999">' + \
                           cgi.escape(l) + '</code> =&gt; <code style="border:1px solid #999">' + cgi.escape(r) + "</code><br/>"

        formreplace += ''' <input class="adminbutton"
                     type="submit" value="%(opt)s"/></form>''' % { 'opt':optreplace }

        formadd = '''<form action="kb?action=add_mapping&amp;ln=%(ln)s&amp;kb=%(kb_id)s&amp;forcetype=curr" method="post">
                    <input type="hidden" name="mapFrom" value="%(left)s"/>
                    <input type="hidden" name="mapTo" value="%(right)s"/>
                    <input class="adminbutton"
                     type="submit" value="%(opt)s"/></form>''' % { 'opt':optadd, 'ln':ln,
                                                                    'kb_id':kbid,
                                                                    'left':cgi.escape(left, 1), 'right':cgi.escape(right, 1) }
        formcancel = '''<form action="kb?ln=%(ln)s&amp;kb=%(kb_id)s">
                    <input type="hidden" name="kb" value="%(kb_id)s">
                    <input  class="adminbutton"
                     type="submit" value="%(opt)s"/></form>''' % { 'ln': ln, 'kb_id':kbid, 'opt':optcancel }

        if dontdoit:
            formadd = _("It is not possible to have two rules with the same left side in the same knowledge base.")+"<p>"
        out = gen+"<p>"+message+"<p>"+formadd+formcancel+"<p><p><p>"+formreplace
        return out
