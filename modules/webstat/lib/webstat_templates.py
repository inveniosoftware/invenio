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

__revision__ = "$Id$"
__lastupdated__ = "$Date$"

from invenio.config import bindir, webdir, weburl

class Template:

    def tmpl_welcome(self, ):
        """
        Generates a welcome page for the Webstat module.
        """
        return """<p>On these pages, you can review measurements of CDS Invenio usage
                     and performance. Output is available in several formats, and its
                     raw data can be exported for offline processing. Further on, a general
                     overview is presented below under the label Current System Health.</p>"""

    def tmpl_system_health(self, health_statistics): 
        """
        Generates a box with current information from the system providing the administrator
        an easy way of overlooking the 'health', i.e. the current performance/efficency, of
        the system.
        """
        out =  """<h3>Current system health</h3>"""

        temp_out = ""
        for statistic in health_statistics:
            if statistic is None:
                temp_out += '\n'
            elif statistic[1] is None:
                temp_out += statistic[0] + '\n'
            else:            
                temp_out += statistic[0] + \
                            '.'*(85 - len(str(statistic[0])) - len(str(statistic[1]))) + \
                            str(statistic[1]) + '\n'
        
        out += "<pre>" + temp_out + "</pre>"

        return out

    def tmpl_keyevent_list(self):
        """
        Generates a list of available key statistics.
        """
        return """<h3>Key statistics</h3>
                  <p>Please choose a statistic from below to review it in detail.</p>
                  <ul>
                    <li><a href="%s/stats/collection_population">Collection population</a></li>
                    <li><a href="%s/stats/search_frequency">Search frequency</a></li>
                    <li><a href="%s/stats/search_type_distribution">Search type distribution</a></li>
                    <li><a href="%s/stats/download_frequency">Download frequency</a></li>
                  </ul>""" % ((weburl,)*4)

    def tmpl_customevent_list(self, customevents):
        """
        Generates a list of available custom statistics.
        """
        out = """<h3>Custom events</h3>
                 <p>The Webstat module supplies a mean for the administrators of CDS Invenio
                 to define their own custom events, more abstract than the Key Statistics above. 
                 A technical walk-through how to create these, is available <a href="%s/stats/customevent_help">here</a>.
                 When a custom event has been made available, it is displayed below.</p>
                 """ % weburl


        temp_out = ""
        for event in customevents:
            temp_out += """<li><a href="%s/stats/customevent?ids=%s">%s</a></li>""" \
                        % (weburl, event[0], (event[1] is None) and event[0] or event[1])
        if len(customevents) == 0:
            out += self.tmpl_error("There are currently no custom events available.")
        else:
            out += "<ul>" + temp_out + "</ul>"

        return out

    def tmpl_customevent_help(self):
        """
        Display help for custom events.
        """
        return """<h3>General overview</h3>

                  <p>A custom event is a measure indicating the frequency of some kind of
                  "action", such as e.g. the number of advanced searches carried out using
                  the Swedish language interface. The custom event functionality is intended
                  to give administrators a mean to log abstract activity, as opposed to
                  trivial measurements like "collection population" and "search frequency".
                  Thus, a custom event is fully customizable and defined by an administrator
                  but it is important to understand that the Webstat module merely supplies
                  the mean to register an action and associate it with a predefined custom event,
                  while the actual use case leading up to the very registration of the action
                  is left to the user.</p>

                  <p>After a custom event has been created and the process of collecting data
                  has started, the event is accessible for review through the Webstat webpage.</p>

                  <h3>How to create a new custom event</h3>

                  <p>The listing below reflects the most basic usage. See
                     <strong>%(bindir)s/webstatadmin --help</strong> for more options.</p>

                  <ol>
                    <li>Execute the following command, where ID is the unique name you want to use
                        when referring to the event:
                        <pre>%(bindir)s/webstatadmin -n ID</pre>
                    </li>
                    <li>If the command completed succesfully, output similar to the following
                        is generated:
                        <pre>$ %(bindir)s/webstatadmin -n test
Event table [staEVENT01] succesfully created.
Please use event id [test] when registering an event.</pre>
                    </li>
                    <li>You can now use the code snippet:
                        <pre>from invenio.webstat import register_customevent
register_customevent('test') </pre>
                        from anywhere in your CDS Invenio sources in order to start logging
                        the custom event 'test' using the use case logic of your choice!
                    </li>
                  </ol>""" % { "bindir": bindir, }


    def tmpl_error(self, msg):
        """
        Provides a common way of outputting error messages.
        """
        return """<div class="important">%s</div>""" % msg

    def tmpl_event_box(self, options, order, choosed):
        """
        Generates a FORM box with dropdowns for events.

        @param options: { parameter name: [(argument internal, argument full)]}
        @type options: { str: [(str, str)]}

        @param order: A permutation of the keys in options, for design purpose.
        @type order: [str]

        @param options: The selected parameters, and its values. 
        @type options: { str: str }
        """
        # Create the FORM's header
        formheader = """<form method="get">"""

        # Create the headers using the options permutation
        headers = [options[param][0] for param in order]

        # Create all SELECT boxes
        sels = [self._tmpl_select_box(options[param][1],                # SELECT box data
                                      " - select " + options[param][0], # first item info
                                      param,                            # name
                                      choosed[param],                   # selected value (perhaps several)
                                      type(choosed[param]) is list)     # multiple box?
                for param in order]

        # Create all buttons
        buttons = []
        buttons.append("""<input class="formbutton" type="submit" name="action_gen" value="Generate">""")

        return self._tmpl_box(formheader, headers, sels, buttons)

    def tmpl_display_event_trend_ascii(self, title, filename):
        """Displays an image graph representing a trend"""
        return self.tmpl_display_trend(title, "<div><pre>%s</pre></div>" % open(filename, 'r').read())

    def tmpl_display_event_trend_image(self, title, filename):
        """Displays a ASCII graph represnting a trend"""
        return self.tmpl_display_trend(title, """<div><img src="%s" /></div>""" % filename.replace(webdir, weburl))

    # INTERNALS

    def tmpl_display_trend(self, title, html):
        """
        Generates a generic display box for showing graphs (ASCII and IMGs)
        alongside to some metainformational boxes.
        """
        return """<table class="narrowsearchbox">
                   <thead><tr><th colspan="2" class="narrowsearchboxheader" align="left">%s</th></tr></thead>
                   <tbody><tr><td class="narrowsearchboxbody" valign="top">%s</td></tr></tbody>
                  </table> """ % (title, html)

    def _tmpl_box(self, formheader, headers, selectboxes, buttons):
        """
        Aggregates together the parameters in order to generate the
        corresponding box.
 
        @param formheader: Start tag for the FORM element.
        @type formheader: str

        @param headers: Headers for the SELECT boxes
        @type headers: list<str>

        @param selectboxes: The actual HTML drop-down boxes, with appropriate content.
        @type selectboxes: list<str>

        @param buttons: Buttons to attach to the FORM.
        @type buttons: list<str>

        @return: HTML describing a particular FORM box.
        @type: str
        """
        out = formheader + """<table class="searchbox"><thead><tr>"""
 
        # Zip together the lists to achieve symmetry (some items might be discarded!)
        combined = zip(headers, selectboxes)

        # Append the headers
        for header in [x[0] for x in combined]:
            if header == combined[-1][0]:
                colspan = ("""colspan="%i" """ % (len(buttons)+1)).strip()
            else:
                colspan = ""
            out += """<th %s class="searchboxheader">%s</th>""" % (colspan, header)
            
        out += """</tr></thead><tbody><tr valign="bottom">"""
 
        # Append the SELECT boxes
        for selectbox in [x[1] for x in combined]:
            out += """<td class="searchboxbody" valign="top">%s</td>""" % selectbox 

        # Append all the buttons in a row
        out += """<td class="searchboxbody" valign="top" align="left">""" + "".join(buttons)
        out += "</td></tr></tbody></table></form>"

        return out

    def _tmpl_select_box(self, iterable, explaination, name, preselected, multiple=False):
        """
        Generates a HTML SELECT drop-down menu.

        @param iterable: A list of values and tag content to be used in the SELECT list
        @type iterable: [(str, str)]

        @param explaination: An explainatory string put as the tag content for the first OPTION.
        @type explaination: str

        @param name: The name of the SELECT tag. Important for FORM-parsing.
        @type name: str

        @param preselected: The value, or list of values, of the OPTION that should be
                            preselected. Blank or empty list for none.
        @type preselected: str | [] 
    
        @param multiple: Optionally sets the SELECT box to accept multiple entries.
        @type multiple: bool
        """
        sel = """<select name="%s">""" % name

        if multiple is True:
            sel = sel.replace("<select ", """<select multiple="multiple" size="5" """)
        else:
            sel += """<option value="">%s</option>""" % explaination

        for realname, printname in [(x[0], x[1]) for x in iterable]:
            if printname is None:
                printname = realname
            option = """<option value="%s">%s</option>""" % (realname, printname)
            if realname == preselected or (type(preselected) is list and realname in preselected):
                option = option.replace('">', '" selected="selected">')
            sel += option
        return sel + "</select>"

