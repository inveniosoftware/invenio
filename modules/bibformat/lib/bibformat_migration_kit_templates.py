# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.  
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""HTML Templates for BibFormat migration kit"""                             

__revision__ = "$Id$"

# Invenio imports                  
from invenio.messages import gettext_set_language
from invenio.textutils import indent_text
from invenio.config import weburl
class Template:
    """Templating class, refer to bibformat_migration_kit_assistant_lib.py for examples of call"""

    def tmpl_admin_migration_status(self, ln, steps):
        """
        Prints the status of the migration, some help and actions to perform the migration
        """
        
        _ = gettext_set_language(ln)    # load the right message language
        
        out = """<p>You can see below the remaining steps to complete the migration of your BibFormat settings.</p>
        <p>Note that it is not recommended to process a step more than once (or it might create duplicates).</p>"""

        out += '''
        <table class="admin_wvar" width="60%">
        <tr>
        <th class="adminheaderleft">Steps (in suggested order)</th>
        <th class="adminheadercenter">Status</th>
        </tr>'''
        i = 0
        for step in steps:
            i += 1
            out += '''
            <tr>
            <td class="admintdleft">%(order)s. <a href="%(action_link)s?ln=%(ln)s">%(action_label)s</a></td>
            <td class="admintd">%(status)s&nbsp;</td>
            </tr>''' % {'ln': ln,
                        'action_link': step['link'],
                        'action_label': step['label'],
                        'status': step['status'],
                        'order': i}
            
        out += '</table>'

        return indent_text(out)
    
    def tmpl_admin_cannot_migrate(self, warnings):
        """
        Prints an error message warning that migration cannot be done because of some error(s)

        @param warnings a list of strings warnings
        """

        out = '''
        <table width="66%%" class="errorbox" style="margin-left: auto; margin-right: auto;">
        <tr>
        <th class="errorboxheader">
        %(warnings)s
        </th>
        </tr>
        </table>
        ''' % {'warnings': '<br/>'.join(warnings)}

        return out

    def tmpl_admin_migrate_knowledge_bases(self, ln):
        """
        Basic page to report the status of the migration of knowledge bases
        """
        
        _ = gettext_set_language(ln) # load the right message language
        
        out = '''
        <p>The migration of your knowledge bases has been done.</p>
        <p>You can go back to the main <a href="%s/admin/bibformat/bibformatadmin.py?ln=%s">BibFormat administration page</a> or 
        continue with the <a href="%s/admin/bibformat/bibformat_migration_kit_assistant.py/migrate_behaviours?ln=%s">
        next step (Migration of behaviours) >>></a></p>''' % (weburl, ln, weburl, ln)

        return indent_text(out)


    def tmpl_admin_migrate_behaviours(self, ln, status):
        """
        Basic page to report the status of the migration of behaviours to output formats
        """
        _ = gettext_set_language(ln)    # load the right message language

        if status == '<span style="color: green;">Migrated</span>':
            out = '''<p>The migration of your behaviours has been done.</p>'''
        else:
            out = '''<p>The result of the migration is: %s</p>''' % status
            
        out += '''
        <p>The behaviours have been moved to a new kind
        of configuration file, called "<i>Output Format</i>". If you
        have not used particular syntax in your behaviours, the output
        formats should behave the same way. We advice you to check
        this point and modify the output formats if necessary.</p>'''

        out += '''
        <p>You can go back to the main <a href="%s/admin/bibformat/bibformatadmin.py?ln=%s">BibFormat administration page</a> or 
        proceed with the  <a href="%s/admin/bibformat/bibformat_migration_kit_assistant.py/migrate_formats?ln=%s">
        next step (Migration of formats) >>></a></p>''' % (weburl, ln, weburl, ln)

        return indent_text(out)


    def tmpl_admin_migrate_formats(self, ln):
        """
        Basic page to warn user that migration of formats to format templates
        is not straightforward
        """
        _ = gettext_set_language(ln)    # load the right message language
        
        out = '''<p>The migration of format is not completely
        staightforward. Here are some advice for the migration:</p>
        <ol>
        <li>If you do not have modified original formats provided by
        default in CDS Invenio (formerly CDSware), then you should not
        proceed with this step.</li>
        <li>If you have only made small
        changes to the original formats provided by default in CDS
        Invenio (formerly CDSware), then you should not proceed with
        this step, but compare your modified files with the new
        provided files and make changes manually.</li>
        <li>If you have
        created totally new formats or made large modifications to the
        provided one, we still advice you not to use this tool and
        make changes by yourself. However, you can try to run this
        translation tool as a starting point. If you have made HTML
        prototypes of the formats, then you would better start from
        the prototypes.</li>
        </ol>
        <p>In any case you should fill the
        table that maps text labels to a Marc codes BEFORE doing this migration, which should help
        you to write new formats (and also help you manage fields of
        the system).<br/> Here are some explanations that can help you
        understand why we advice you to rewrite format manually:</p>
        <p>The new BibFormat now uses format files that separate the presentation
        from the business logic, which is something that cannot be
        completely automated. The formats will be moved to new kinds
        of configuration files, called "<i>Format templates</i> (for
        the presentation) and "<i>Format elements</i> (for the part
        that binds the record in database to the format
        template). Format templates are written in HTML. Format
        elements are written in Python. However basic format elements
        do not even need to be written, as BibFormat can guess which
        field of a record it has to retrieve by looking at an internal
        mapping table (maps a label to a marc code). It is why it is
        important that you fill this table correctly BEFORE running
        the translation of the formats. </p>
        <p>This migration tool will do as much as possible to translate your formats in these new
        kind of files. It will create format templates files
        corresponding to your formats, and will include an attempt of
        translation + the original code as comment. Empty format
        elements files will be created whenever necessary.</p>'''

        out += '''
        <p><a href="%s/admin/bibformat/bibformat_migration_kit_assistant.py/migrate_formats_do?ln=%s">Click here to migrate your format automatically</a>, despite the above recommendations.</p>
        ''' % (weburl, ln)
        
        return indent_text(out)

    
    def tmpl_admin_migrate_formats_do(self, ln):
        """
        Basic page to report the status of the migration of formats to format templates
        """
        _ = gettext_set_language(ln)    # load the right message language
        
        out = '''<p>Migration of formats has been done.</p>'''
        out += '''<p>To check and edit format templates,
        use the <a href="%s/admin/bibformat/bibformatadmin.py/format_templates_manage">Format template management console</a> or edit files directly in directory etc/bibformat/templates/ of your CDS Invenio installation base.</p>''' % weburl
        out += '''<p>To check and edit your format elements, open files in lib/python/invenio/bibformat_elements directory of your CDS Invenio installation base</p>'''

        out += '''<a href="%s/admin/bibformat/bibformatadmin.py">Click here to go back to main BibFormat administration page</a>''' % weburl
        return indent_text(out)
