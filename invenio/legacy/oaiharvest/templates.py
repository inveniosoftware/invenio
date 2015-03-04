# This file is part of Invenio.
# Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2014 CERN.
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
"""
OAIHarvest templates - HTML component to be used by OAI Harvest and
                       OAI Repository
"""
__revision__ = "$Id$"

import cgi
import datetime
from invenio.config import CFG_SITE_URL, CFG_SITE_LANG, CFG_CERN_SITE
from invenio.utils.html import nmtoken_from_string
from invenio.utils.url import create_html_link
from invenio.base.i18n import gettext_set_language

oai_harvest_admin_url = CFG_SITE_URL + \
                        "/admin/oaiharvest/oaiharvestadmin.py"

class Template:
    """ OAIHarvest templates"""

    def tmpl_meta_headers(self):
        """
            returning the HTML headers necessary in order to open the view holdingpen page
        """
        return """
    <script type="text/javascript" src="%s/js/jquery.min.js"></script>
    <script type="text/javascript" src="%s/js/ui.core.js"></script>
    <script type="text/javascript" src="%s/js/oaiharvester/admin.js"> </script>
    <link rel="stylesheet" href="%s/css/oaiharvester/admin.css" />
""" % tuple([CFG_SITE_URL] * 4)

    def tmpl_getnavtrail(self, previous="", ln=CFG_SITE_LANG):
        """Get the navigation trail
          - 'previous' *string* - The previous navtrail"""
        _ = gettext_set_language(ln)
        navtrail = """<a class="navtrail" href="%s/help/admin?ln=%s">Admin Area</a> """ % (CFG_SITE_URL, ln)
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

        titlebar = """ <table class="table"><tr><th>"""
        titlebar += """%s<small>[<a title="%s" href="%s/%s">?</a>]</small>""" % (title, guidetitle, CFG_SITE_URL, guideurl)
        if extraname and extraurl:
            titlebar += self.tmpl_button_link(extraname, CFG_SITE_URL + extraurl)
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

    def tmpl_button_link(self, title, url, style="btn-primary"):
        """Draws an html title bar
          - 'title' *string* - The name of the titlebar
          - 'subtitle' *string* - The header name of the subtitle
          - 'guideurl' *string* - The relative url of the guide relative to this section
        """
        return """<a href="{0}" class="btn {2}" role="button">{1}</a>""".format(
            url,
            title,
            style,
        )

    def tmpl_output_numbersources(self, ln, numbersources):
        """Get the navigation trail
          - 'number of sources' *int* - The number of sources in the database"""
        _ = gettext_set_language(ln)
        present = _("OAI sources currently present in the database")
        notpresent = _("No OAI sources currently present in the database")
        if (numbersources > 0):
            output = """&nbsp;&nbsp;&nbsp;&nbsp;<strong><span class="info">%s %s</span></strong><br /><br />""" % (numbersources, present)
            return output
        else:
            output = """&nbsp;&nbsp;&nbsp;&nbsp;<strong><span class="warning">%s</span></strong><br /><br />""" % notpresent
            return output

    def tmpl_output_schedule(self, ln, schtime, schstatus):
        _ = gettext_set_language(ln)
        msg_next = _("Next oaiharvest task")
        msg_sched = _("scheduled time:")
        msg_cur = _("current status:")
        msg_notask = _("No oaiharvest task currently scheduled.")
        if schtime and schstatus:
            output = """&nbsp;&nbsp;&nbsp;&nbsp;<strong>%s<br />
                         &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; - %s %s <br />
                         &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; - %s %s </strong><br /><br />""" % (msg_next, msg_sched, schtime, msg_cur, schstatus)
            return output
        else:
            output = """&nbsp;&nbsp;&nbsp;&nbsp;<strong><span class="warning">%s</span></strong><br /><br />""" % msg_notask
            return output

    def tmpl_admin_w200_text(self, ln, title, name, value, suffix="<br/>"):
        """Draws an html w200 text box
          - 'title' *string* - The name of the textbox
          - 'name' *string* - The name of the value in the textbox
          - 'value' *string* - The value in the textbox
          - 'suffix' *string* - A value printed after the input box (must be already escaped)
        """
        text = ("""<div class="form-group">"""
                """<label for="{0}">{2}</label>"""
                """<input type="text" class="form-control" """
                """ name="{0}" value="{1}" placeholder="{2}">"""
                """<p class="help-block">{3}</p></div>"""
                .format(cgi.escape(name, 1),
                        cgi.escape(value, 1),
                        title,
                        suffix)
                )
        return text

    def tmpl_admin_w200_text_placeholder(self, ln, placeholder, name, value, suffix="<br/>"):
        """Draws an html w200 text box
          - 'placeholder' *string* - Placeholder text for the textbox
          - 'name' *string* - The name of the value in the textbox
          - 'value' *string* - The value in the textbox
          - 'suffix' *string* - A value printed after the input box (must be already escaped)
        """
        text = ("""<div class="form-group">"""
                """<input type="text" class="form-control" """
                """ name="{0}" value="{1}" placeholder="{2}">"""
                """<p class="help-block">{3}</p></div>"""
                .format(cgi.escape(name, 1),
                        cgi.escape(value, 1),
                        cgi.escape(placeholder, 1),
                        suffix)
                )
        return text

    def tmpl_admin_checkboxes(self, ln, title, name, values, labels, states, message=""):
        """Draws a list of HTML checkboxes
          - 'title' *string* - The name of the list of checkboxes
          - 'name' *string* - The name for this group of checkboxes
          - 'values' *list* - The values of the checkboxes
          - 'labels' *list* - The labels for the checkboxes
          - 'states' *list* - The previous state of each checkbox 1|0
          - 'message' *string* - Put a message over the checkboxes. Optional.

          len(values) == len(labels) == len(states)
        """
        text = ""
        if title:
            text += """<h5>%s</h5>""" % (title,)
        text += """<table class="table"><tr><td>"""
        if message:
            text += '<small><i>(%s)</i></small><br/>' % (message,)

        for i in range(len(values)):
            value = values[i]
            label = labels[i]
            state = states[i]
            chk_box_id = value + str(i)
            text += '<div class="checkbox"><label><input type="checkbox"' \
                    'name="%s" id="%s" value="%s" ' % (name, chk_box_id, value)
            if state:
                text += 'checked="checked "'
            text += "/>"
            text += """%s</label></div>""" % label

        text += "</td></tr></table>"
        return text

    def tmpl_admin_checkbox_arguments(self, ln, title, name, values, labels, states, message="", arguments=[]):
        """Draws a list of HTML checkboxes tailored for OAI post-processes as it allows text-input
        arguments for each checkbox/post-process.

          - 'title' *string* - The name of the list of checkboxes
          - 'name' *string* - The name for this group of checkboxes
          - 'values' *list* - The values of the checkboxes
          - 'labels' *list* - The labels for the checkboxes
          - 'states' *list* - The previous state of each checkbox 1|0
          - 'message' *string* - Put a message over the checkboxes. Optional.
          - 'arguments' *list* - List of argument dictionaries (key => value mappings of argument name etc.

          len(values) == len(labels) == len(states)
          """
        text = ""
        if title:
            text += """<div><div style="float:left;"><span class="admin_label">%s</span></div>""" % (title,)
        text += """<table><tr><td>"""
        if message:
            text += '&nbsp;&nbsp; <small><i>(%s)</i></small><br/>' % (message,)

        for i in range(len(values)):
            value = values[i]
            label = labels[i]
            state = states[i]
            chk_box_id = value + str(i)
            text += '<div class="checkbox"><label><input type="checkbox"' \
                    'name="%s" id="post_input_%s" value="%s" ' % (name, chk_box_id, value)
            if state:
                text += 'checked="checked "'
            text += "/>"
            text += """%s</label></div>""" % label
            if len(arguments) > i:
                # Arguments given, let us display each argument
                args = arguments[i]
                text += """<div id="post_args_%s" class="admin_arguments">""" % (chk_box_id,)
                for arg_dict in args:
                    title = arg_dict['name'].title().replace('-', ' ')
                    if arg_dict['required']:
                        title += " *"
                    # To avoid problems with duplicate argument names we prefix with post-mode
                    arg_name = "%s_%s" % (value, arg_dict['name'])
                    # Depending on which input type the argument values are given, display it
                    if arg_dict['input'] == 'text':
                        text += self.tmpl_admin_w200_text(ln=ln, title=title, \
                                                          name=arg_name, \
                                                          value=arg_dict['value'])
                    elif arg_dict['input'] == 'checkbox':
                        text += self.tmpl_admin_checkboxes(ln=ln, title=title, name=arg_name, \
                                                           values=arg_dict['value'], \
                                                           labels=arg_dict['labels'], \
                                                           states=arg_dict['states'])
                text += """</div>"""
        text += "</td></tr></table></div>"
        return text


    def tmpl_admin_w200_select(self, ln, title, name, valuenil, values, lastval="", suffix="<br />"):
        """Draws an html w200 drop-down box
          - 'title' *string* - The name of the dd box
          - 'name' *string* - The name of the value in the dd box
          - 'value' *list* - The values in the textbox"""
        _ = gettext_set_language(ln)
        text = """<div class="form-group">"""
        if title:
            text += """<label for="{0}">{1}</label>""".format(name, title)
        text += """<select name="%s" class="form-control">""" % (name,)
        text += """<option value="">%s</option>""" % (valuenil,)
        try:
            for val in values:
                intval = int(lastval)
                if intval == int(val[0]): ## retrieve and display last value inputted into drop-down box
                    text += """<option value="%s" %s>%s</option>""" % (val[0], 'selected="selected"', str(val[1]))
                else:
                    text += """<option value="%s">%s</option>""" % (val[0], str(val[1]))
        except StandardError, e:
            for val in values:
                if lastval == val[0]:
                    text += """<option value="%s" %s>%s</option>""" % (val[0], 'selected="selected"', str(val[1]))
                else:
                    text += """<option value="%s">%s</option>""" % (val[0], str(val[1]))
        return """%s</select><p class="help-block">%s</p></div>""" % (text, suffix)

    def tmpl_admin_w200_textarea(self, ln, title, name, value, suffix="<br/>"):
        """
        Returns a textarea element with given parameters:
          - 'ln' *string* - The current language code
          - 'title' *string* - The label of the textarea
          - 'name' *string* - The name of the value in the textarea
          - 'value' *string* - The value in the textarea
          - 'suffix' *string* - Suffix to be added after the textbox element
        """
        _ = gettext_set_language(ln)
        text = ""
        if title:
            text += """<span class="admin_label">%s</span>""" % (title,)
        if value is None:
            value= ""
        text += """<textarea cols="30" rows="5" class="form-control" type="text" name="%s">%s</textarea>%s""" % \
                 (cgi.escape(name), cgi.escape(value), suffix)
        return text

    def tmpl_print_info(self, ln, infotext):
        """Outputs some info"""
        text = ("""<div class="alert alert-info">"""
                """<a class="close" data-dismiss="alert" href="#">&times;</a>"""
                """%s</div>""" % infotext)
        return text

    def tmpl_print_warning(self, ln, warntext, prefix="<br />", suffix=""):
        """Outputs some info"""
        text = ("""<div class="alert alert-warning">"""
                """<a class="close" data-dismiss="alert" href="#">&times;</a>"""
                """%s</div>""" % warntext)
        return prefix + text + suffix

    def tmpl_print_brs(self, ln, howmany):
        """Outputs some <br />s"""
        _ = gettext_set_language(ln)
        text = ""
        while howmany > 0:
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
        if outcome == 0:
            output = """<br /><span class="info">baseURL <strong>%s</strong> %s</span>""" % (base, msg_success)
            return output
        else:
            output = """<br /><span class="warning">baseURL <strong>%s</strong> %s</span>""" % (base, msg_nosuccess)
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

    def tmpl_form_vertical(self, action="", text="", button="confirm", cnfrm='', **hidden):
        """create select with hidden values and submit button

          action - name of the action to perform on submit

            text - additional text, can also be used to add non hidden input

          button - value/caption on the submit button

           cnfrm - if given, must check checkbox to confirm

        **hidden - dictionary with name=value pairs for hidden input
        """
        output  = '<form action="%s" method="post">\n' % (action, )
        output += '<table width="100%">\n<tr><td style="vertical-align: top">'
        output += text
        if cnfrm:
            output += ' <input type="checkbox" name="confirm" value="1"/>'
        for key in hidden.keys():
            if type(hidden[key]) is list:
                for value in hidden[key]:
                    output += ' <input type="hidden" name="%s" value="%s"/>\n' % (key, value)
            else:
                output += ' <input type="hidden" name="%s" value="%s"/>\n' % (key, hidden[key])
        output += '</td></tr><tr><td style="vertical-align: bottom">'
        output += ' <button type="submit" class="btn btn-primary">%s</button>\n' % (button, )
        output += '</td></tr></table>'
        output += '</form>\n'
        return output

    def tmpl_output_table(self, title_row=None, data=None, td_class="", separator_class=""):
        """
        Prints a table of given titles and data. Adds CSS class to all cells,
        if specified. Also, if a cell or row value equals "_SEPARATOR_" a simple
        separator row/column is generated.

        @param title_row: is a list of titles of columns
        @param data: is a list of rows. Each row is a list of string values
        @param td_class: specifies the CSS class for each TD.

        @return: string of generated HTML table.
        """
        output = [self.tmpl_table_begin(title_row)]
        if data is None:
            data = []
        for row in data:
            if row == "_SEPARATOR_":
                output.append(self.tmpl_table_separator_column(cssclass=separator_class))
            else:
                output.append(self.tmpl_table_row_begin())
                for item in row:
                    if item == "_SEPARATOR_":
                        output.append(self.tmpl_table_output_cell(content="", cssclass=separator_class))
                    else:
                        output.append(self.tmpl_table_output_cell(item, cssclass=td_class))
                output.append(self.tmpl_table_row_end())
        output.append(self.tmpl_table_end())
        return "".join(output)

    def tmpl_table_begin(self, title_row=None):
        result = "<table class=\"table table-striped\">"
        if title_row != None:
            result += "<tr>"
            for header in title_row:
                result += "<td><b>" + header + "</b></td>"
            result += "</tr>"
        return result

    def tmpl_table_row_begin(self):
        return "<tr>"

    def tmpl_table_output_cell(self, content, colspan=1, rowspan=1, cssclass=None):
        result = "<td"
        if colspan != 1:
            result += " colspan=\"" + str(colspan) + "\""
        if rowspan != 1:
            result += " rowspan=\"" + str(rowspan) + "\""
        if cssclass != None:
            result += " class = \"" + cssclass + "\""
        result += ">" + content + "</td>"
        return result

    def tmpl_table_separator_column(self, colspan=1, rowspan=1, cssclass=None):
        result = "<tr"
        if colspan != 1:
            result += " colspan=\"" + str(colspan) + "\""
        if rowspan != 1:
            result += " rowspan=\"" + str(rowspan) + "\""
        if cssclass != None:
            result += " class = \"" + cssclass + "\""
        result += "></tr>"
        return result

    def tmpl_table_row_end(self):
        return "</tr>\n"

    def tmpl_table_end(self):
        return "</table>\n"

    def tmpl_history_day_details_link(self, ln, date, oai_src_id):
        """Return link to detailed history for the day"""
        _ = gettext_set_language(ln)
        return create_html_link(urlbase=oai_harvest_admin_url + \
                                "/viewhistoryday",
                                urlargd={'ln':ln,
                                         'oai_src_id': str(oai_src_id),
                                         'year': str(date.year),
                                         'month': str(date.month),
                                         'day': str(date.day),
                                         'start': str(10)},
                                 link_label=_("View next entries..."))

    def tmpl_history_table_output_day_cell(self, date, number_of_records, oai_src_id, ln, show_details=False):
        inner_text = "<b>" + self.format_date(date)
        inner_text += " ( " + str(number_of_records) + " entries ) &nbsp;&nbsp;&nbsp;"
        if show_details:
            inner_text += self.tmpl_history_day_details_link(ln, date, oai_src_id)
        inner_text += "</b>"
        return self.tmpl_table_output_cell(inner_text, colspan=6)

    def tmpl_history_table_output_day_details_cell(self, ln, date, oai_src_id):
        inner_text = self.tmpl_history_day_details_link(ln, date, oai_src_id)
        return self.tmpl_table_output_cell(inner_text, colspan=7)

    def tmpl_output_checkbox(self, name, aid, value):
        return "<input type=\"checkbox\" id=\"" + aid + "\"name=\"" + name + "\" value=\"" + value + "\" />"

    def tmpl_output_preformatted(self, content):
        return "<pre style=\"background-color: #eeeeee;\">" + content + "</pre>"

    def tmpl_output_scrollable_frame(self, content):
        output = """<div class="scrollableframe" heigh="40">"""
        output += content
        output += "</div>"
        return output

    def tmpl_output_normal_frame(self, content):
        output = """<div class="normalframe" heigh="40">"""
        output += content
        output += "</div>"
        return output

    def tmpl_output_month_selection_bar(self, oai_src_id, ln, current_year=None, current_month=None):
        """constructs the month selection bar"""
        _ = gettext_set_language(ln)
        if current_month == None or current_year == None:
            current_month = datetime.datetime.today().month
            current_year = datetime.datetime.today().year
        prev_year = current_year
        prev_month = current_month
        prev_month -= 1
        if prev_month == 0:
            prev_year -= 1
            prev_month = 12
        next_year = current_year
        next_month = current_month
        next_month += 1
        if next_month == 13:
            next_year += 1
            next_month = 1
        current_date = datetime.datetime(current_year, current_month, 1)
        prevurl = create_html_link(urlbase=oai_harvest_admin_url + \
                                   "/viewhistory",
                                   urlargd={'ln':ln,
                                            'oai_src_id': str(oai_src_id),
                                            'year': str(prev_year),
                                            'month': str(prev_month)},
                                   link_label="&lt;&lt; " + _("previous month"))
        nexturl = create_html_link(urlbase=oai_harvest_admin_url + \
                                   "/viewhistory",
                                   urlargd={'ln':ln,
                                            'oai_src_id': str(oai_src_id),
                                            'year': str(next_year),
                                            'month': str(next_month)},
                                   link_label=_("next month") + " &gt;&gt;")
        result = prevurl + """&nbsp;&nbsp;&nbsp;&nbsp;"""
        result += "<b>Current month: " + self.format_ym(current_date) + "</b>"
        result += """&nbsp;&nbsp;&nbsp;&nbsp;""" + nexturl
        return result

    def tmpl_output_selection_bar(self):
        result = ""
        result += "<button class=\"adminbutton\" onClick=\"return selectAll()\">Select all</button>\n"
        result += "<button class=\"adminbutton\" onClick=\"return removeSelection()\">Remove selection</button>\n"
        result += "<button class=\"adminbutton\" onClick=\"return invertSelection()\">Invert selection</button>\n"
        return result

    def tmpl_output_history_javascript_functions(self):
        """Writes necessary javascript functions"""
        result = '<script type="text/javascript">'
        result += """
   function selectDay(day)
   {
      for (key in identifiers[day])
         document.getElementById(identifiers[day][key]).checked = true;
      return false
   }

   function selectAll()
   {
      for (day in identifiers)
      {
         for (key in identifiers[day])
            document.getElementById(identifiers[day][key]).checked = true;
      }
      return false
   }

   function removeSelection()
   {
      for (day in identifiers)
      {
         for (key in identifiers[day])
            document.getElementById(identifiers[day][key]).checked = false;
      }
      return false
   }

   function invertSelection()
   {
      for (day in identifiers)
      {
         for (key in identifiers[day])
            document.getElementById(identifiers[day][key]).checked = !(document.getElementById(identifiers[day][key]).checked);
      }
      return false
   }
   """
        result += "</script>"
        return result

    def tmpl_output_identifiers(self, identifiers):
        """
        Creates the Javascript array of identifiers.
        @param identifiers: is a dictionary containning day as a key and list of identifiers as a value
        """
        result = '<script type="text/javascript">\n'
        result += "   var identifiers = {\n"
        first = True
        for day in identifiers:
            result += "      "
            if not first:
                result += ","
            else:
                first = False
            result += str(day) + " : ["
            for id_n in range(0, len(identifiers[day])):
                result += "         "
                if id_n != 0:
                    result += ","
                result += "'" + identifiers[day][id_n] + "'\n"
            result += "        ]\n"
        result += "    }\n"
        result += '</script>'
        return result

    def tmpl_output_select_day_button(self, day):
        result = """<button class="adminbutton" onClick="return selectDay(""" + str(day) + """)">Select</button>"""
        return result

    def tmpl_output_menu(self, ln, oai_src_id, guideurl):
        """
           Function which displays menu
        """
        _ = gettext_set_language(ln)
        link_default_argd = {'ln': ln}

        main_link = create_html_link(urlbase=oai_harvest_admin_url,
                                     urlargd=link_default_argd,
                                     link_label=_("main Page"))

        link_default_argd['oai_src_id'] = str(oai_src_id)

        edit_link = create_html_link(urlbase=oai_harvest_admin_url + \
                                     "/editsource",
                                     urlargd=link_default_argd,
                                     link_label=_("edit"))
        delete_link = create_html_link(urlbase=oai_harvest_admin_url + \
                                     "/delsource",
                                     urlargd=link_default_argd,
                                     link_label=_("delete"))
        test_link = create_html_link(urlbase=oai_harvest_admin_url + \
                                     "/testsource",
                                     urlargd=link_default_argd,
                                     link_label=_("test"))
        hist_link = create_html_link(urlbase=oai_harvest_admin_url + \
                                     "/viewhistory",
                                     urlargd=link_default_argd,
                                     link_label=_("history"))
        harvest_link = create_html_link(urlbase=oai_harvest_admin_url + \
                                        "/harvest",
                                        urlargd=link_default_argd,
                                        link_label=_("harvest"))
        separator = "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        menu_header = self.tmpl_draw_titlebar(ln, title="Menu" , guideurl=guideurl)
        # Putting everything together
        result = menu_header + main_link
        if oai_src_id != None:
            result += separator + edit_link + separator + \
                      delete_link + separator + test_link + \
                      separator + hist_link + separator + \
                      harvest_link + separator

        result += self.tmpl_print_brs(ln, 2)
        return result

    # Datetime formatting functions
    def format_al_twodigits(self, number):
        """
        Converts integers to string guaranteeing that there will be at least 2 digits
        @param number: Nuber to be formatted
        @return: string representation with at least 2 digits
        """
        if number < 10:
            return "0" + str(number)
        else:
            return str(number)

    def format_ym(self, date):
        """
        formats year and month of a given date in the human-readabla format
        @param date: date containing data to be formatted
        @return: string representation
        """
        if date == None:
            return "(None)"
        return self.format_al_twodigits(date.year) + "-" + self.format_al_twodigits(date.month)

    def format_date(self, date):
        if date == None:
            return "(None)"
        return self.format_ym(date) + "-" + self.format_al_twodigits(date.day)

    def format_time(self, datetime_obj):
        if datetime_obj == None:
            return "(None)"
        return self.format_al_twodigits(datetime_obj.hour) + ":" + \
               self.format_al_twodigits(datetime_obj.minute) + ":" + \
               self.format_al_twodigits(datetime_obj.second)

    def tmpl_view_holdingpen_body(self, filter_key, content):
        return """<div>
    <form>
        <label>Show entries containing :</label>
        <input type="input" name="filter" value="%s"></input>
        <input type="submit" value="Show"></input>
    </form>
    </div>
    <ul id="holdingpencontainer"> %s</ul>
    """ % (filter_key, content,)

    def tmpl_view_holdingpen_headers(self):
        """
            returning the HTML headers necessary in order to open the view
            holdingpen page
        """
        jquery_scripts = ["vendors/jquery-ui/jquery-ui.min.js",
                          "vendors/jquery.treeview/jquery.treeview.js",
                          "vendors/jquery.treeview/jquery.treeview.async.js",
                          "js/jquery.ajaxPager.js"]
        jquery_scripts_strings = []
        for script in jquery_scripts:
            entry_str = """    <script type="text/javascript" src="%(baseurl)s/%(sname)s"></script>\n""" % {
                    "baseurl": CFG_SITE_URL,
                    "sname" : script
                }
            jquery_scripts_strings.append(entry_str)
        jquery_scripts_string = "".join(jquery_scripts_strings)

        return """ %(scriptsstring)s
    <link rel="stylesheet" href="%(baseurl)s/vendors/jquery.treeview/jquery.treeview.css" />
    <link rel="stylesheet" href="%(baseurl)s/css/jquery.ajaxPager.css" />
    <script type="text/javascript">
        var serverAddress = '%(baseurl)s';
    </script>
    <script type="text/javascript" src="%(baseurl)s/js/oaiharvester/admin.js"> </script>
    <script type="text/javascript" src="%(baseurl)s/js/oaiharvester/admin_hp.js"> </script>
""" % {
            "baseurl" : CFG_SITE_URL,
            "scriptsstring" : jquery_scripts_string
       }

    def tmpl_should_process_record_with_mode(self, marcxml, postmode, source_id):
        """
        Return True if the given C{marcxml} should be processed in the
        given C{mode}.

        Mode can take values (string):
          - p: plot extraction
          - r: reference extraction
          - a: author list parsing
          - t: file (fulltext attachement)

        @param marcxml: the record currently being processed
        @type marcxml: string
        @param postmode: processing mode currently executed
        @type postmode: string
        @param source_id: source_id
        @type source_id: integer
        @return: if record should be processed
        @rtype: boolean
        """
        if CFG_CERN_SITE:
            if not 'CERN-' in marcxml and \
                   'http://export.arxiv.org/oai2' in marcxml:
                # we skip non-CERN records when harvesting from ArXiv
                return False

        return True

    def tmpl_createhiddenform(self, action="", text="", button="confirm",
                              cnfrm='', **hidden):
        """Create select with hidden values and submit button.

          action - name of the action to perform on submit

            text - additional text, can also be used to add non hidden input

          button - value/caption on the submit button

           cnfrm - if given, must check checkbox to confirm

        **hidden - dictionary with name=value pairs for hidden input.
        """
        output = '<form action="%s" method="post">\n' % (action, )
        output += '<table class="table">\n<tr><td>'
        output += text
        if cnfrm:
            output += ' <input type="checkbox" name="confirm" value="1"/>'
        for key in hidden.keys():
            if type(hidden[key]) is list:
                for value in hidden[key]:
                    output += ' <input type="hidden" name="%s" value="%s"/>\n' % (key, value)
            else:
                output += ' <input type="hidden" name="%s" value="%s"/>\n' % (key, hidden[key])
        output += '</td><td>'
        output += ' <input class="btn btn-default" type="submit" value="%s"/>\n' % (button, )
        output += '</td></tr></table>'
        output += '</form>\n'

        return output
