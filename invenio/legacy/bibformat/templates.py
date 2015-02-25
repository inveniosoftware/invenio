# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2014, 2015 CERN.
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

"""HTML Templates for BibFormat administration"""


class Template(object):
    """Templating class, refer to bibformat.py for examples of call"""

    def tmpl_admin_dialog_box(self, url, title, message, options):
        """
        Prints a dialog box with given title, message and options

        @param url: the url of the page that must process the result of the dialog box
        @param ln: language
        @param title: the title of the dialog box
        @param message: a formatted message to display inside dialog box
        @param options: a list of string options to display as button to the user
        @return: HTML markup
        """

        out = ""
        out += '''
        <div style="text-align:center;">
        <fieldset style="display:inline;margin-left:auto;margin-right:auto;">
        <legend>%(title)s:</legend>
        <p>%(message)s</p>
        <form method="post" action="%(url)s">
        ''' % {'title': title,
               'message': message,
               'url': url}

        for option in options:
            out += '''<input type="submit" class="adminbutton" name="chosen_option" value="%(value)s" />&nbsp;''' % {'value': option}

        out += '''</form></fieldset></div>'''
        return out
