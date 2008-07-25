## $Id$

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

__revision__ = "$Id$"

import urllib
import time
import cgi
import gettext
import traceback
import urllib
import sys

from invenio.config import \
     CFG_VERSION, \
     CFG_SITE_URL
from invenio.messages import gettext_set_language, language_list_long
from invenio.htmlutils import nmtoken_from_string

class Template:
    def tmpl_getnavtrail(self, ln, previous):
        """Get the navigation trail
          - 'previous' *string* - The previous navtrail"""
        _ = gettext_set_language(ln)
        navtrail = """<a class="navtrail" href="%s/help/admin">Admin Area</a> """ % (CFG_SITE_URL,)
        navtrail = navtrail + previous
        return navtrail

    def tmpl_draw_titlebar(self, ln, title, guideurl, extraname="", extraurl=""):
        """Draws an html title bar
          - 'title' *string* - The name of the titlebar
          - 'guideurl' *string* - The relative url of the guide relative to this section
          - 'extraname' *string* - The name of an extra function
          - 'extraurl' *string* - The relative url to an extra function
          """

        _ = gettext_set_language(ln)
        guidetitle = _("See Guide")

        titlebar = """ <table class="admin_wvar_nomargin"><tr><th class="adminheader">"""
        titlebar += """%s&nbsp;&nbsp;&nbsp;<small>[<a title="%s" href="%s/%s">?</a>]</small>""" % (title, guidetitle, CFG_SITE_URL, guideurl)
        if extraname and extraurl:
            titlebar += """&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<small>[<a href="%s/%s">%s</a>]</small>""" % (CFG_SITE_URL, extraurl, extraname)
        titlebar += """</th></tr></table>"""
        return titlebar


    def tmpl_draw_subtitle(self, ln, title, subtitle, guideurl):
        """Draws an html title bar
          - 'title' *string* - The name of the titlebar
          - 'subtitle' *string* - The header name of the subtitle
          - 'guideurl' *string* - The relative url of the guide relative to this section
          """
        _ = gettext_set_language(ln)
        guidetitle = _("See Guide")

        titlebar = """<a name="%s">""" % nmtoken_from_string(title)
        titlebar += """ </a>%s&nbsp;&nbsp;&nbsp;<small>""" % subtitle
        titlebar += """ [<a title="%s" href="%s/%s">?</a>]</small>""" % (guidetitle, CFG_SITE_URL, guideurl)
        return titlebar

    def tmpl_link_with_args(self, ln, funcurl, title, args):
        """Draws an html title bar
          - 'funcurl' *string* - The relative url to this section
          - 'title' *string* - The name of the link
          - 'args' *list* - The list of arguments to be appended to the url in the form [name, value]
          """
        _ = gettext_set_language(ln)
        initurl = '<a href="' + CFG_SITE_URL + '/' + funcurl
        endurl = '" title="' + title + '">' + title + '</a>'
        noargs = len(args)
        if noargs==0:
            # there are no arguments, close link and return
            return initurl + endurl
        else:
            # we have args. list them in the link, then close it and return it
            argsurl = '?'
            count = 1
            for arg in args:
                if count != noargs:
                    argsurl += arg[0] + '=' + arg[1] + '&amp;'
                else:
                    argsurl += arg[0] + '=' + arg[1]
                count = count + 1
            return initurl+argsurl+endurl

    def tmpl_output_numbersources(self, ln, numbersources):
        """Get the navigation trail
          - 'number of sources' *int* - The number of sources in the database"""
        _ = gettext_set_language(ln)
        present = _("OAI sources currently present in the database")
        notpresent = _("No OAI sources currently present in the database")
        if (numbersources>0):
            output  = """&nbsp;&nbsp;&nbsp;&nbsp;<strong><span class="info">%s %s</span></strong><br /><br />""" % (numbersources, present)
            return output
        else:
            output  = """&nbsp;&nbsp;&nbsp;&nbsp;<strong><span class="warning">%s</span></strong><br /><br />""" % notpresent
            return output

    def tmpl_output_schedule(self, ln, schtime, schstatus):
        _ = gettext_set_language(ln)
        msg_next = _("Next oaiharvest task")
        msg_sched = _("scheduled time:")
        msg_cur = _("current status:")
        msg_notask = _("No oaiharvest task currently scheduled.")
        if schtime and schstatus:
            output  = """&nbsp;&nbsp;&nbsp;&nbsp;<strong>%s<br />
                         &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; - %s %s <br />
                         &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; - %s %s </strong><br /><br />""" % (msg_next, msg_sched, schtime, msg_cur, schstatus)
            return output
        else:
            output  = """&nbsp;&nbsp;&nbsp;&nbsp;<strong><span class="warning">%s</span></strong><br /><br />""" % msg_notask
            return output

    def tmpl_admin_w200_text(self, ln, title, name, value):
        """Draws an html w200 text box
          - 'title' *string* - The name of the textbox
          - 'name' *string* - The name of the value in the textbox
          - 'value' *string* - The value in the textbox"""
        _ = gettext_set_language(ln)
        text = """<span class="adminlabel">%s""" % title
        text += """</span><input class="admin_w200" type="text" name="%s" value="%s" /><br />""" % (cgi.escape(name,1), cgi.escape(value, 1))
        return text

    def tmpl_admin_checkboxes(self, ln, title, name, values, labels, states):
        """Draws a list of HTML checkboxes
          - 'title' *string* - The name of the list of checkboxes
          - 'name' *string* - The name for this group of checkboxes
          - 'values' *list* - The values of the checkboxes
          - 'labels' *list* - The labels for the checkboxes
          - 'states' *list* - The previous state of each checkbox 1|0

          len(values) == len(labels) == len(states)
          """
        _ = gettext_set_language(ln)
        text = """<div><div style="float:left;"><span class="adminlabel">%s</span></div>""" % title
        text += """<table><tr><td>"""
        text += '&nbsp;&nbsp; <small><i>(Leave all unchecked for non-selective' \
                ' harvesting)</i></small><br/>'

        for i in range(len(values)):
            value = values[i]
            label = labels[i]
            state = states[i]
            chk_box_id = value + str(i)
            text += '&nbsp;&nbsp; <input type="checkbox"' \
                    'name="%s" id="%s" value="%s" ' % (name, chk_box_id, value)
            if state:
                text += 'checked="checked "'
            text += "/>"

            text += """<label for="%s">%s</label><br/>""" % (chk_box_id, label)
        text += "</td></tr></table></div>"
        return text

    def tmpl_admin_w200_select(self, ln, title, name, valuenil, values, lastval=""):
        """Draws an html w200 drop-down box
          - 'title' *string* - The name of the dd box
          - 'name' *string* - The name of the value in the dd box
          - 'value' *list* - The values in the textbox"""
        _ = gettext_set_language(ln)
        text = """<span class="adminlabel">%s""" % title
        text += """</span><select name="%s" class="admin_w200">""" % name
        text += """<option value="">%s</option>""" % valuenil
        try:
            for val in values:
                intval = int(lastval)
                if intval==int(val[0]): ## retrieve and display last value inputted into drop-down box
                    text += """<option value="%s" %s>%s</option>""" % (val[0], 'selected="selected"', str(val[1]))
                else:
                    text += """<option value="%s">%s</option>""" % (val[0], str(val[1]))
            text += """</select><br />"""
        except StandardError, e:
            for val in values:
                if lastval==val[0]:
                    text += """<option value="%s" %s>%s</option>""" % (val[0], 'selected="selected"', str(val[1]))
                else:
                    text += """<option value="%s">%s</option>""" % (val[0], str(val[1]))
            text += """</select><br />"""
        return text

    def tmpl_print_info(self, ln, infotext):
        """Outputs some info"""
        _ = gettext_set_language(ln)
        text = """<br /><b><span class="info">%s</span></b>""" % infotext
        return text

    def tmpl_print_warning(self, ln, warntext):
        """Outputs some info"""
        _ = gettext_set_language(ln)
        text = """<span class="warning">%s</span>""" % warntext
        return text

    def tmpl_print_brs(self, ln, howmany):
        """Outputs some <br />s"""
        _ = gettext_set_language(ln)
        text = ""
        while howmany>0:
            text += """<br />"""
            howmany = howmany - 1
        return text

    def tmpl_output_validate_info(self, ln, outcome, base):
        """Prints a message to say whether source was validated or not
          - 'outcome' *int* - 0=success, 1=fail
          - 'base' *string* - baseurl"""
        _ = gettext_set_language(ln)
        msg_success = _("successfully validated")
        msg_nosuccess = _("does not seem to be a OAI-compliant baseURL")
        if outcome==0:
            output = """<br /><span class="info">baseURL <strong>%s</strong> %s</span>""" % (base, msg_success)
            return output
        else:
            output = """<br /><span class="info">baseURL <strong>%s</strong> %s</span>""" % (base, msg_nosuccess)
            return output

    def tmpl_output_error_info(self, ln, base, error):
        """Prints a http error message"""
        _ = gettext_set_language(ln)
        msg_error = "returns the following HTTP error: "
        output = """<br /><span class="info">baseURL <strong>%s</strong> %s</span><br /><blockquote>%s</blockquote>""" % (base, msg_error, error)
        return output

    def tmpl_embed_document(self, url):
        output = "<iframe src=\"" + url + "\" width=\"80%\" height=\"400\"></iframe>"
        return output

    def tmpl_output_table(self, title_row = [], data = []):
        """
           Prints a table of given titles and data
           @param title_row is a list of titles of columns
           @param data is a list o rows. Each row is a list of string values
        """
        result = "<table><tr>"
        for header in title_row:
            result += "<td><b>"+ header + "</b></td>"
        result += "</tr>"
        for row in data:
            result += "<tr>"
            for item in row:
                result += "<td>" + item + "</td>"
            result += "</tr>"
        result += "</table>"
        return result
