# -*- coding: utf-8 -*-
## $Id$

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
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

import urllib
import time
import cgi
import gettext
import string
import locale
import sre

from invenio.config import *
from invenio.dbquery import run_sql
from invenio.messages import gettext_set_language
from invenio.search_engine_config import *

def get_fieldvalues(recID, tag):
    """Return list of field values for field TAG inside record RECID.
       FIXME: should be imported commonly for search_engine too."""
    out = []
    if tag == "001___":
        # we have asked for recID that is not stored in bibXXx tables
        out.append(str(recID))
    else:
        # we are going to look inside bibXXx tables
        digit = tag[0:2]
        bx = "bib%sx" % digit
        bibx = "bibrec_bib%sx" % digit
        query = "SELECT bx.value FROM %s AS bx, %s AS bibx WHERE bibx.id_bibrec='%s' AND bx.id=bibx.id_bibxxx AND bx.tag LIKE '%s'" \
                "ORDER BY bibx.field_number, bx.tag ASC" % (bx, bibx, recID, tag)
        res = run_sql(query)
        for row in res:
            out.append(row[0])
    return out

class Template:

    # This dictionary maps CDS Invenio language code to locale codes (ISO 639)
    tmpl_localemap = {
        'ca': 'ca_ES',
        'de': 'de_DE',
        'el': 'el_GR',
        'en': 'en_US',
        'es': 'es_ES',
        'pt': 'pt_BR',
        'fr': 'fr_FR',
        'it': 'it_IT',
        'ru': 'ru_RU',
        'sk': 'sk_SK',
        'cs': 'cs_CZ',
        'no': 'no_NO',
        'sv': 'sv_SE',
        'uk': 'uk_UA',
        'ja': 'ja_JA',
        'pl': 'pl_PL'
        }
    tmpl_default_locale = "en_US" # which locale to use by default, useful in case of failure

    def tmpl_navtrail_links(self, as, ln, weburl, separator, dads):
        """
        Creates the navigation bar at top of each search page (*Home > Root collection > subcollection > ...*)

        Parameters:

          - 'as' *bool* - Should we display an advanced search box?

          - 'ln' *string* - The language to display

          - 'weburl' *string* - The base URL for the site

          - 'separator' *string* - The separator between two consecutive collections

          - 'dads' *list* - A list of parent links, eachone being a dictionary of ('name', 'longname')
        """
        out = ""
        for url, name in dads:
            if out:
                out += separator
            out += '''<a class="navtrail" href="%(weburl)s/?c=%(qname)s&amp;as=%(as)d&amp;ln=%(ln)s">%(longname)s</a>''' % {
                'weburl'   : weburl,
                'qname'    : urllib.quote_plus (url),
                'as'       : as,
                'ln'       : ln,
                'longname' : name }
        return out

    def tmpl_webcoll_body(self, weburl, te_portalbox, searchfor, np_portalbox, narrowsearch, focuson, ne_portalbox):
        """
        Creates the body of the main search page.

        Parameters:

          - 'weburl' *string* - The base URL for the site

          - 'te_portalbox' *string* - The HTML code for the portalbox on top of search

          - 'searchfor' *string* - The HTML code for the search options

          - 'np_portalbox' *string* - The HTML code for the portalbox on bottom of search

          - 'searchfor' *string* - The HTML code for the search categories (left bottom of page)

          - 'focuson' *string* - The HTML code for the "focuson" categories (right bottom of page)

          - 'ne_portalbox' *string* - The HTML code for the bottom of the page
        """

        body = """
                <form action="%(weburl)s/search.py" method="get">
                %(searchfor)s
                %(np_portalbox)s
                <table cellspacing="0" cellpadding="0" border="0">
                  <tr>
                    <td valign="top">%(narrowsearch)s</td>
               """ % {
                 'weburl' : weburl,
                 'searchfor' : searchfor,
                 'np_portalbox' : np_portalbox,
                 'narrowsearch' : narrowsearch
               }
        if focuson:
            body += """<td valign="top">""" + focuson + """</td>"""
        body += """</tr></table>
            %(ne_portalbox)s
               </form>""" % {'ne_portalbox' : ne_portalbox}
        return body

    def tmpl_portalbox(self, title, body):
        """Creates portalboxes based on the parameters
        Parameters:

          - 'title' *string* - The title of the box

          - 'body' *string* - The HTML code for the body of the box

        """
        out = """<div class="portalbox">
                    <div class="portalboxheader">%(title)s</div>
                    <div class="portalboxbody">%(body)s</div>
                 </div>""" % {'title' : title, 'body' : body}

        return out

    def tmpl_searchfor_simple(self, ln,weburl,asearchurl, header, middle_option):
        """Produces simple *Search for* box for the current collection.

        Parameters:

          - 'ln' *string* - The language to display

          - 'weburl' *string* - The base URL for the site

          - 'asearchurl' *string* - The URL to advanced search form

          - 'header' *string* - header of search form

          - 'middle_option' *string* - HTML code for the options (any field, specific fields ...)
        """

        # load the right message language
        _ = gettext_set_language(ln)

        # print commentary start:
        out = """<!--create_searchfor_simple()-->
               <input type="hidden" name="sc" value="1">
               <input type="hidden" name="ln" value="%(ln)s">
               <table class="searchbox">
                <thead>
                 <tr align="left">
                  <th colspan="3" class="searchboxheader">%(header)s</th>
                 </tr>
                </thead>
                <tbody>
                 <tr valign="baseline">
                  <td class="searchboxbody" align="left"><input type="text" name="p" size="40" value=""></td>
                  <td class="searchboxbody" align="left">%(middle_option)s</td>
                  <td class="searchboxbody" align="left"><input class="formbutton" type="submit" name="action" value="%(msg_search)s"><input class="formbutton" type="submit" name="action" value="%(msg_browse)s"></td>
                 </tr>
                 <tr valign="baseline">
                  <td class="searchboxbody" colspan="3" align="right"
                    <small><a href="%(weburl)s/help/search/tips.%(ln)s.html">%(msg_search_tips)s</a> :: <a href="%(asearchurl)s">%(msg_advanced_search)s</a></small>
                  </td>
                 </tr>
                </tbody>
               </table>
               <!--/create_searchfor_simple()-->
                """ % {
                 'ln' : ln,
                 'weburl' : weburl,
                 'asearchurl' : asearchurl,
                 'header' : header,
                 'middle_option' : middle_option,
                 'msg_search' : _('Search'),
                 'msg_browse' : _('Browse'),
                 'msg_search_tips' : _('Search Tips'),
                 'msg_advanced_search' : _('Advanced Search'),
               }
        return out

    def tmpl_searchfor_advanced(self,
                                ln,                  # current language
                                weburl,              # base url
                                ssearchurl,          # url to simple search form
                                header,              # header of search form
                                
                                middle_option_1, middle_option_2, middle_option_3,
                                searchoptions,
                                sortoptions,
                                rankoptions,
                                displayoptions,
                                formatoptions
                                ):
        """
          Produces advanced *Search for* box for the current collection.

          Parameters:

            - 'ln' *string* - The language to display

            - 'weburl' *string* - The base URL for the site

            - 'ssearchurl' *string* - The URL to simple search form

            - 'header' *string* - header of search form

            - 'middle_option_1' *string* - HTML code for the first row of options (any field, specific fields ...)

            - 'middle_option_2' *string* - HTML code for the second row of options (any field, specific fields ...)

            - 'middle_option_3' *string* - HTML code for the third row of options (any field, specific fields ...)

            - 'searchoptions' *string* - HTML code for the search options

            - 'sortoptions' *string* - HTML code for the sort options

            - 'rankoptions' *string* - HTML code for the rank options

            - 'displayoptions' *string* - HTML code for the display options

            - 'formatoptions' *string* - HTML code for the format options

        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """<!--create_searchfor_advanced()-->
                 <input type="hidden" name="as" value="1">
                 <input type="hidden" name="ln" value="%(ln)s">
                 <table class="searchbox">
                  <thead>
                   <tr>
                    <th class="searchboxheader" colspan="3">%(header)s</th>
                   </tr>
                  </thead>
                  <tbody>
                   <tr valign="bottom">
                     <td class="searchboxbody" nowrap>%(matchbox_m1)s<input type="text" name="p1" size="40" value=""></td>
                     <td class="searchboxbody">%(middle_option_1)s</td>
                     <td class="searchboxbody">%(andornot_op1)s</td>
                   </tr>
                   <tr valign="bottom">
                     <td class="searchboxbody" nowrap>%(matchbox_m2)s<input type="text" name="p2" size="40" value=""></td>
                     <td class="searchboxbody">%(middle_option_2)s</td>
                     <td class="searchboxbody">%(andornot_op2)s</td>
                   </tr>
                   <tr valign="bottom">
                     <td class="searchboxbody" nowrap>%(matchbox_m3)s<input type="text" name="p3" size="40" value=""></td>
                     <td class="searchboxbody">%(middle_option_3)s</td>
                     <td class="searchboxbody" nowrap><input class="formbutton" type="submit" name="action" value="%(msg_search)s"><input class="formbutton" type="submit" name="action" value="%(msg_browse)s"></td>
                   </tr>
                   <tr valign="bottom">
                     <td colspan="3" class="searchboxbody" align="right">
                       <small><a href="%(weburl)s/help/search/tips.%(ln)s.html">%(msg_search_tips)s</a> :: <a href="%(ssearchurl)s">%(msg_simple_search)s</a></small>
                     </td>
                   </tr>
                  </tbody>
                 </table>
                 <!-- @todo - more imports -->
              """ % {
                 'ln' : ln,
                 'weburl' : weburl,
                 'ssearchurl' : ssearchurl,
                 'header' : header,

                 'matchbox_m1' : self.tmpl_matchtype_box('m1', ln=ln),
                 'middle_option_1' : middle_option_1,
                 'andornot_op1' : self.tmpl_andornot_box('op1', ln=ln),

                 'matchbox_m2' : self.tmpl_matchtype_box('m2', ln=ln),
                 'middle_option_2' : middle_option_2,
                 'andornot_op2' : self.tmpl_andornot_box('op2', ln=ln),

                 'matchbox_m3' : self.tmpl_matchtype_box('m3', ln=ln),
                 'middle_option_3' : middle_option_3,

                 'msg_search' : _("Search"),
                 'msg_browse' : _("Browse"),
                 'msg_search_tips' : _("Search Tips"),
                 'msg_simple_search' : _("Simple Search")
               }

        if (searchoptions):
            out += """<table class="searchbox">
                      <thead>
                       <tr>
                         <th class="searchboxheader">
                           %(searchheader)s
                         </th>
                       </tr>
                      </thead>
                      <tbody>
                       <tr valign="bottom">
                        <td class="searchboxbody">%(searchoptions)s</td>
                       </tr>
                      <tbody>
                     </table>""" % {
                       'searchheader' : _("Search options:"),
                       'searchoptions' : searchoptions
                     }

        out += """<table class="searchbox">
                   <thead>
                    <tr>
                      <th class="searchboxheader">
                        %(added)s
                      </th>
                      <th class="searchboxheader">
                        %(until)s
                      </th>
                    </tr>
                   </thead>
                   <tbody>
                    <tr valign="bottom">
                      <td class="searchboxbody">%(date_added)s</td>
                      <td class="searchboxbody">%(date_until)s</td>
                    </tr>
                   </tbody>
                  </table>
                  <table class="searchbox">
                   <thead>
                    <tr>
                      <th class="searchboxheader">
                        %(msg_sort)s
                      </th>
                      <th class="searchboxheader">
                        %(msg_display)s
                      </th>
                      <th class="searchboxheader">
                        %(msg_format)s
                      </th>
                    </tr>
                   </thead>
                   <tbody>
                    <tr valign="bottom">
                      <td class="searchboxbody">%(sortoptions)s %(rankoptions)s</td>
                      <td class="searchboxbody">%(displayoptions)s</td>
                      <td class="searchboxbody">%(formatoptions)s</td>
                    </tr>
                   </tbody>
                  </table>
                  <!--/create_searchfor_advanced()-->
              """ % {

                    'added' : _("Added since:"),
                    'until' : _("until:"),
                    'date_added' : self.tmpl_inputdate("d1", ln=ln),
                    'date_until' : self.tmpl_inputdate("d2", ln=ln),

                    'msg_sort' : _("Sort by:"),
                    'msg_display' : _("Display results:"),
                    'msg_format' : _("Output format:"),
                    'sortoptions' : sortoptions,
                    'rankoptions' : rankoptions,
                    'displayoptions' : displayoptions,
                    'formatoptions' : formatoptions
                  }
        return out

    def tmpl_matchtype_box(self, name='m', value='', ln='en'):
        """Returns HTML code for the 'match type' selection box.

          Parameters:

            - 'name' *string* - The name of the produced select

            - 'value' *string* - The selected value (if any value is already selected)

            - 'ln' *string* - the language to display
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """
        <select name="%(name)s">
        <option value="a"%(sela)s>%(opta)s
        <option value="o"%(selo)s>%(opto)s
        <option value="e"%(sele)s>%(opte)s
        <option value="p"%(selp)s>%(optp)s
        <option value="r"%(selr)s>%(optr)s
        </select>
        """ % {'name' : name,
               'sela' : self.tmpl_is_selected('a', value),
                                                           'opta' : _("All of the words:"),
               'selo' : self.tmpl_is_selected('o', value),
                                                           'opto' : _("Any of the words:"),
               'sele' : self.tmpl_is_selected('e', value),
                                                           'opte' : _("Exact phrase:"),
               'selp' : self.tmpl_is_selected('p', value),
                                                           'optp' : _("Partial phrase:"),
               'selr' : self.tmpl_is_selected('r', value),
                                                           'optr' : _("Regular expression:")
              }
        return out

    def tmpl_is_selected(self, var, fld):
        """
          Checks if *var* and *fld* are equal, and if yes, returns ' selected'.  Useful for select boxes.

          Parameters:

          - 'var' *string* - First value to compare

          - 'fld' *string* - Second value to compare
        """
        if var == fld:
            return " selected"
        else:
            return ""

    def tmpl_andornot_box(self, name='op', value='', ln='en'):
        """
          Returns HTML code for the AND/OR/NOT selection box.

          Parameters:

            - 'name' *string* - The name of the produced select

            - 'value' *string* - The selected value (if any value is already selected)

            - 'ln' *string* - the language to display
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """
        <select name="%(name)s">
        <option value="a"%(sela)s>%(opta)s
        <option value="o"%(selo)s>%(opto)s
        <option value="n"%(seln)s>%(optn)s
        </select>
        """ % {'name' : name,
               'sela' : self.tmpl_is_selected('a', value), 'opta' : _("AND"),
               'selo' : self.tmpl_is_selected('o', value), 'opto' : _("OR"),
               'seln' : self.tmpl_is_selected('n', value), 'optn' : _("AND NOT")
              }
        return out

    def tmpl_inputdate(self, name, ln, sy = 0, sm = 0, sd = 0):
        """
          Produces *From Date*, *Until Date* kind of selection box. Suitable for search options.

          Parameters:

            - 'name' *string* - The base name of the produced selects

            - 'ln' *string* - the language to display
        """
        # load the right message language
        _ = gettext_set_language(ln)

        box = """
               <select name="%(name)sd">
                 <option value=""%(sel)s>%(any)s
              """ % {
                'name' : name,
                'any' : _("any day"),
                'sel' : self.tmpl_is_selected(sd, 0)
              }
        for day in range(1,32):
            box += """<option value="%02d"%s>%02d""" % (day, self.tmpl_is_selected(sd, day), day)
        box += """</select>"""
        # month
        box += """
                <select name="%(name)sm">
                  <option value=""%(sel)s>%(any)s
               """ % {
                 'name' : name,
                 'any' : _("any month"),
                 'sel' : self.tmpl_is_selected(sm, 0)
               }
        for mm, month in [(1,_("January")), (2,_("February")), (3,_("March")), (4,_("April")), \
                          (5,_("May")), (6,_("June")), (7,_("July")), (8,_("August")), \
                          (9,_("September")), (10,_("October")), (11,_("November")), (12,_("December"))]:
            box += """<option value="%02d"%s>%s""" % (mm, self.tmpl_is_selected(sm, mm), month)
        box += """</select>"""
        # year
        box += """
                <select name="%(name)sy">
                  <option value=""%(sel)s>%(any)s
               """ % {
                 'name' : name,
                 'any' : _("any year"),
                 'sel' : self.tmpl_is_selected(sy, 0)
               }
        this_year = int(time.strftime("%Y", time.localtime()))
        for year in range(this_year-20, this_year+1):
            box += """<option value="%d"%s>%d""" % (year, self.tmpl_is_selected(sy, year), year)
        box += """</select>"""
        return box

    def tmpl_narrowsearch(self, as, ln, weburl, title, type, father, has_grandchildren, instant_browse, sons, display_grandsons, grandsons):
        """
        Creates list of collection descendants of type *type* under title *title*.
        If as==1, then links to Advanced Search interfaces; otherwise Simple Search.
        Suitable for 'Narrow search' and 'Focus on' boxes.

        Parameters:

          - 'as' *bool* - Should we display an advanced search box?

          - 'ln' *string* - The language to display

          - 'weburl' *string* - The base URL for the site

          - 'title' *string* - The title of the produced box

          - 'type' *string* - The type of the produced box (virtual collections or normal collections)

          - 'father' *collection* - The current collection

          - 'has_grandchildren' *bool* - If the current collection has grand children

          - 'sons' *list* - The list of the sub-collections (first level)

          - 'display_grandsons' *bool* - If the grand children collections should be displayed (2 level deep display)

          - 'grandsons' *list* - The list of sub-collections (second level)
        """

        # load the right message language
        _ = gettext_set_language(ln)

        if has_grandchildren:
            style_prolog = "<strong>"
            style_epilog = "</strong>"
        else:
            style_prolog = ""
            style_epilog = ""

        out = ''
        if type == 'r':
            out += """<input type="hidden" name="cc" value="%(name)s">""" % {
                     'name' : cgi.escape(father.name, 1),
                   }

        if len(sons):
            out += """<table class="narrowsearchbox">
                       <thead>
                        <tr>
                         <th colspan="2" align="left" class="narrowsearchboxheader">
                           %(title)s
                         </th>
                        </tr>
                       </thead>
                       <tbody>""" % {'title' : title}
            # iterate through sons:
            i = 0
            for son in sons:
                out += """<tr><td class="narrowsearchboxbody" valign="top">"""
                if type=='r':
                    if son.restricted_p() and son.restricted_p() != father.restricted_p():
                        out += """<input type=checkbox name="c" value="%(name)s">&nbsp;</td>""" % {'name' : son.name }
                    else:
                        out += """<input type=checkbox name="c" value="%(name)s" checked>&nbsp;</td>""" % {'name' : son.name }
                out += """<td valign="top"><a href="%(url)s/?c=%(name)s&amp;as=%(as)d&amp;ln=%(ln)s">%(prolog)s%(longname)s%(epilog)s</a>%(recs)s """ % {
                          'url' : weburl,
                          'name' : urllib.quote_plus(son.name),
                          'as' : as,
                          'ln' : ln,
                          'prolog' : style_prolog,
                          'longname' : son.get_name(ln),
                          'epilog' : style_epilog,
                          'recs' : son.create_nbrecs_info(ln)
                       }
                if son.restricted_p():
                    out += """ <small class="warning">[%(msg)s]</small>""" % { 'msg' : _("restricted") }
                if display_grandsons and len(grandsons[i]):
                    # iterate trough grandsons:
                    out += """<br>"""
                    for grandson in grandsons[i]:
                        out += """
                                <a href="%(weburl)s/?c=%(name)s&amp;as=%(as)d&amp;ln=%(ln)s">%(longname)s</a>%(nbrec)s
                               """ % {
                                 'weburl' : weburl,
                                 'name' : urllib.quote_plus(grandson.name),
                                 'as' : as,
                                 'ln' : ln,
                                 'longname' : grandson.get_name(ln),
                                 'nbrec' : grandson.create_nbrecs_info(ln)
                               }
                out += """</td></tr>"""
                i += 1
            out += "</tbody></table>"
        else:
            if type == 'r':
                # no sons, and type 'r', so print info on collection content:
                out += """<table class="narrowsearchbox">
                           <thead>
                            <tr>
                             <th class="narrowsearchboxheader">
                               %(header)s
                             </th>
                            </tr>
                           </thead>
                           <tbody>
                            <tr>
                             <td class="narrowsearchboxbody">%(body)s</td>
                            </tr>
                           <tbody>
                          </table>""" % {
                           'header' : _("Latest additions:"),
                           'body' : instant_browse
                       }

        return out

    def tmpl_nbrecs_info(self, number, prolog = None, epilog = None):
        """
        Return information on the number of records.

        Parameters:

        - 'number' *string* - The number of records

        - 'prolog' *string* (optional) - An HTML code to prefix the number (if **None**, will be
        '<small class="nbdoccoll">(')

        - 'epilog' *string* (optional) - An HTML code to append to the number (if **None**, will be
        ')</small>')
        """

        if number is None: return ''

        if prolog == None: prolog = """&nbsp;<small class="nbdoccoll">("""
        if epilog == None: epilog = """)</small>"""

        return prolog + number + epilog

    def tmpl_box_restricted_content(self, ln):
        """
          Displays a box containing a *restricted content* message

        Parameters:

          - 'ln' *string* - The language to display

        """

        # load the right message language
        _ = gettext_set_language(ln)

        return _("The contents of this collection is restricted.")

    def tmpl_box_no_records(self, ln):
        """
          Displays a box containing a *no content* message

        Parameters:

          - 'ln' *string* - The language to display

        """

        # load the right message language
        _ = gettext_set_language(ln)

        return _("This collection does not contain any document yet.")

    def tmpl_instant_browse(self, as, ln, recids, more_link = None):
        """
          Formats a list of records (given in the recids list) from the database.

        Parameters:

          - 'as' *int* - Advanced Search interface or not (0 or 1)

          - 'ln' *string* - The language to display

          - 'recids' *list* - the list of records from the database

          - 'more_link' *string* - the "More..." link for the record. If not given, will not be displayed

        """

        # load the right message language
        _ = gettext_set_language(ln)

        if not len(recids): return ""
        out = """<table class="latestadditionsbox">"""
        for recid in recids:
            out += """<tr>
                        <td class="latestadditionsboxtimebody">%(date)s</td>
                        <td class="latestadditionsboxrecordbody">%(body)s</td>
                      </tr>""" % {
                        'date': recid['date'],
                        'body': recid['body']
                      }
        out += "</table>"
        if more_link:
            out += """<div align="right"><small><a href="%(url)s&amp;ln=%(ln)s%(advanced_search_addon)s">[&gt;&gt; %(text)s]</a></small></div>""" % {
               'url'  : more_link,
               'ln'   : ln,
               'advanced_search_addon'  : as and "&amp;as=%d" % as or "",
               'text' : _("more")}
        return out

    def tmpl_searchwithin_select(self, ln, fieldname, selected, values):
        """
          Produces 'search within' selection box for the current collection.

        Parameters:

          - 'ln' *string* - The language to display

          - 'fieldname' *string* - the name of the select box produced

          - 'selected' *string* - which of the values is selected

          - 'values' *list* - the list of values in the select
        """
        out = """<select name="%(fieldname)s">""" % {
                'fieldname' : fieldname,
              }

        if values:
            for pair in values:
                out += """<option value="%(value)s"%(selected)s>%(text)s""" % {
                         'value'    : pair['value'],
                         'selected' : self.tmpl_is_selected(pair['value'], selected),
                         'text'     : pair['text']
                       }
        out += """</select>"""
        return out

    def tmpl_select(self, fieldname, values, selected = None, css_class = ''):
        """
          Produces a generic select box

        Parameters:

          - 'css_class' *string* - optional, a css class to display this select with

          - 'fieldname' *list* - the name of the select box produced

          - 'selected' *string* - which of the values is selected

          - 'values' *list* - the list of values in the select
        """
        if css_class != '':
            class_field = ' class="%s"' % css_class
        else:
            class_field = ''
        out = """<select name="%(fieldname)s"%(class)s>""" % {
                'fieldname' : fieldname,
                'class' : class_field
              }

        for pair in values:
            out += """<option value="%(value)s"%(selected)s>%(text)s""" % {
                     'value'    : pair['value'],
                     'selected' : self.tmpl_is_selected(pair['value'], selected) or
                                  (pair.has_key('selected') and self.tmpl_is_selected(pair['selected'], True)),
                     'text'     : pair['text']
                   }
        out += """</select>"""
        return out

    def tmpl_record_links(self, weburl, recid, ln):
        """
          Displays the *More info* and *Find similar* links for a record

        Parameters:

          - 'ln' *string* - The language to display

          - 'weburl' *string* - The base URL for the site

          - 'recid' *string* - the id of the displayed record
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out =  """
                <br><span class="moreinfo"><a class="moreinfo" href="%(weburl)s/search.py?recid=%(recid)s&amp;ln=%(ln)s">%(msgdetail)s</a>
                 - <a class="moreinfo" href="%(weburl)s/search.py?p=recid:%(recid)d&amp;rm=wrd&amp;ln=%(ln)s">%(msgsimilar)s</a></span>
               """ % {
                  'weburl' : weburl,
                  'recid' : recid,
                  'ln' : ln,
                  'msgdetail' : _("Detailed record"),
                  'msgsimilar' : _("Similar records")
               }
                 
        if cfg_experimental_features:
            out += """<span class="moreinfo"> - <a class="moreinfo" href="%s/search.py?p=recid:%d&amp;rm=cit&amp;ln=%s">%s</a></span>\n""" % (
                weburl, recid, ln, _("Cited by"))
                 
        return out

    def tmpl_record_body(self, weburl, titles, authors, dates, rns, abstracts, urls_u, urls_z):
        """
          Displays the "HTML basic" format of a record

        Parameters:

          - 'weburl' *string* - The base URL for the site

          - 'authors' *list* - the authors (as strings)

          - 'dates' *list* - the dates of publication

          - 'rns' *list* - the quicknotes for the record

          - 'abstracts' *list* - the abstracts for the record

          - 'urls_u' *list* - URLs to the original versions of the notice

          - 'urls_z' *list* - Not used
        """
        out = ""
        for title in titles:
            out += "<strong>%(title)s</strong> " % {
                     'title' : cgi.escape(title)
                   }
        if authors:
            out += " / "
            for i in range (0,cfg_author_et_al_threshold):
                if i < len(authors):
                    out += """<a href="%(weburl)s/search.py?p=%(name_url)s&f=author">%(name)s</a> ;""" % {
                             'weburl' : weburl,
                             'name_url' : urllib.quote(authors[i]),
                             'name' : cgi.escape(authors[i])
                           }
            if len(authors) > cfg_author_et_al_threshold:
                out += " <em>et al</em>"
        for date in dates:
            out += " %s." % cgi.escape(date)
        for rn in rns:
            out += """ <small class="quicknote">[%(rn)s]</small>""" % {'rn' : cgi.escape(rn)}
        for abstract in abstracts:
            out += "<br><small>%(abstract)s [...]</small>" % {'abstract' : cgi.escape(abstract[:1+string.find(abstract, '.')]) }
        for idx in range(0,len(urls_u)):
            out += """<br><small class="note"><a class="note" href="%(url)s">%(name)s</a></small>""" % {
                     'url' : urls_u[idx],
                     'name' : urls_u[idx]
                   }
        return out

    def tmpl_search_in_bibwords(self, p, f, ln, nearest_box):
        """
          Displays the *Words like current ones* links for a search

        Parameters:

          - 'p' *string* - Current search words

          - 'f' *string* - the fields in which the search was done

          - 'nearest_box' *string* - the HTML code for the "nearest_terms" box - most probably from a create_nearest_terms_box call
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = "<p>%(words)s <em>%(p)s</em> " % {
                 'words' : _("Words nearest to"),
                     'p' : p,
              }
        if f:
            out += "%(inside)s <em>%(f)s</em> " %{
                 'inside' : _("inside"),
                     'f' : f,
              }
        out += _("in any collection are:") + "<br>"
        out += nearest_box
        return out

    def tmpl_nearest_term_box(self, p, ln, f, weburl, terms, termargs, termhits, intro):
        """
          Displays the *Nearest search terms* box

        Parameters:

          - 'p' *string* - Current search words

          - 'f' *string* - a collection description (if the search has been completed in a collection)

          - 'ln' *string* - The language to display

          - 'weburl' *string* - The base URL for the site

          - 'terms' *array* - the broken down related terms

          - 'termargs' *array* - the URL parameters to compose the search queries for the terms

          - 'termhits' *array* - the number of hits in each query

          - 'intro' *string* - the intro HTML to prefix the box with
        """

        out = """<table class="nearesttermsbox" cellpadding="0" cellspacing="0" border="0">"""

        for i in range(0, len(terms)):
            if terms[i] == p: # print search word for orientation:
                if termhits[i] > 0:
                    out += """<tr>
                               <td class="nearesttermsboxbodyselected" align="right">%(hits)d</td>
                               <td class="nearesttermsboxbodyselected" width="15">&nbsp;</td>
                               <td class="nearesttermsboxbodyselected" align="left">
                                 <a class="nearesttermsselected" href="%(weburl)s/search.py?%(urlargs)s">%(term)s</a>
                               </td>
                              </tr>""" % {
                                 'hits' : termhits[i],
                                 'weburl' : weburl,
                                 'urlargs' : termargs[i],
                                 'term' : terms[i]
                              }
                else:
                    out += """<tr>
                               <td class="nearesttermsboxbodyselected" align="right">-</td>
                               <td class="nearesttermsboxbodyselected" width="15">&nbsp;</td>
                               <td class="nearesttermsboxbodyselected" align="left">%(term)s</td>
                              </tr>""" % {
                                'term' : terms[i]
                              }
            else:
                out += """<tr>
                           <td class="nearesttermsboxbody" align="right">%(hits)s</td>
                           <td class="nearesttermsboxbody" width="15">&nbsp;</td>
                           <td class="nearesttermsboxbody" align="left">
                             <a class="nearestterms" href="%(weburl)s/search.py?%(urlargs)s">%(term)s</a>
                           </td>
                          </tr>""" % {
                             'hits' : termhits[i],
                             'weburl' : weburl,
                             'urlargs' : termargs[i],
                             'term' : terms[i]
                          }
        out += "</table>"
        return intro + "<blockquote>" + out + "</blockquote>"

    def tmpl_browse_pattern(self, f, ln, weburl, browsed_phrases_in_colls, urlarg_colls):
        """
          Displays the *Nearest search terms* box

        Parameters:

          - 'f' *string* - a field name (i18nized)

          - 'ln' *string* - The language to display

          - 'weburl' *string* - The base URL for the site

          - 'browsed_phrases_in_colls' *array* - the phrases to display

          - 'urlargs_colls' *string* - the url parameters for the search
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """<table class="searchresultsbox">
              <thead>
               <tr>
                <th class="searchresultsboxheader" align="left">
                  %(hits)s
                </th>
                <th class="searchresultsboxheader" width="15">
                  &nbsp;
                </th>
                <th class="searchresultsboxheader" align="left">
                  %(f)s
                </th>
               </tr>
              </thead>
              <tbody>""" % {
                'hits' : _("Hits"),
                'f' : f
              }

        if len(browsed_phrases_in_colls) == 1:
            # one hit only found:
            phrase, nbhits = browsed_phrases_in_colls[0][0], browsed_phrases_in_colls[0][1]
            out += """<tr>
                       <td class="searchresultsboxbody" align="right">
                        %(nbhits)s
                       </td>
                       <td class="searchresultsboxbody" width="15">
                        &nbsp;
                       </td>
                       <td class="searchresultsboxbody" align="left">
                        <a href="%(weburl)s/search.py?p=%%22%(phrase_qt)s%%22&f=%(f)s%(urlargs)s">%(phrase)s</a>
                       </td>
                      </tr>""" % {
                        'nbhits' : nbhits,
                        'weburl' : weburl,
                        'phrase_qt' : urllib.quote(phrase),
                        'phrase' : phrase,
                        'f' : urllib.quote(f),
                        'urlargs' : urlarg_colls,
                      }
        elif len(browsed_phrases_in_colls) > 1:
            # first display what was found but the last one:
            for phrase, nbhits in browsed_phrases_in_colls[:-1]:
                out += """<tr>
                           <td class="searchresultsboxbody" align="right">
                            %(nbhits)s
                           </td>
                           <td class="searchresultsboxbody" width="15">
                            &nbsp;
                           </td>
                           <td class="searchresultsboxbody" align="left">
                            <a href="%(weburl)s/search.py?p=%%22%(phrase_qt)s%%22&f=%(f)s%(urlargs)s">%(phrase)s</a>
                           </td>
                          </tr>""" % {
                            'nbhits' : nbhits,
                            'weburl' : weburl,
                            'phrase_qt' : urllib.quote(phrase),
                            'phrase' : phrase,
                            'f' : urllib.quote(f),
                            'urlargs' : urlarg_colls,
                          }
            # now display last hit as "next term":
            phrase, nbhits = browsed_phrases_in_colls[-1]
            out += """<tr><td colspan="2" class="normal">
                            &nbsp;
                          </td>
                          <td class="normal">
                            <img src="%(weburl)s/img/sn.gif" alt="" border="0">
                            <a href="%(weburl)s/search.py?action=%(browse)s&p=%(phrase_qt)s&f=%(f)s%(urlargs)s">%(next)s</a>
                          </td>
                      </tr>""" % {
                        'weburl' : weburl,
                        'phrase_qt' : urllib.quote(phrase),
                        'browse' : _("Browse"),
                        'next' : _("next"),
                        'f' : urllib.quote(f),
                        'urlargs' : urlarg_colls,
                      }
        out += """</tbody>
            </table>"""
        return out

    def tmpl_search_box(self, ln, weburl, as, cc, cc_intl, ot, sp, action, fieldslist, f1, f2, f3, m1, m2, m3, p1, p2, p3, op1, op2, rm, p, f, coll_selects, d1y, d2y, d1m, d2m, d1d, d2d, sort_formats, sf, so, ranks, sc, rg, formats, of, pl):
        """
          Displays the *Nearest search terms* box

        Parameters:

          - 'ln' *string* - The language to display

          - 'weburl' *string* - The base URL for the site

          - 'as' *bool* - Should we display an advanced search box?

          - 'cc_intl' *string* - the i18nized current collection name

          - 'cc' *string* - the internal current collection name

          - 'ot', 'sp' *string* - hidden values

          - 'action' *string* - the action demanded by the user

          - 'fieldlist' *list* - the list of all fields available in CDSWare, for use in select within boxes in advanced search

          - 'p, f, f1, f2, f3, m1, m2, m3, p1, p2, p3, op1, op2, op3, rm' *strings* - the search parameters

          - 'coll_selects' *array* - a list of lists, each containing the collections selects to display

          - 'd1y, d2y, d1m, d2m, d1d, d2d' *int* - the search between dates

          - 'sort_formats' *array* - the select information for the sorting format

          - 'sf' *string* - the currently selected sort format

          - 'so' *string* - the currently selected sort order ("a" or "d")

          - 'ranks' *array* - ranking methods

          - 'rm' *string* - selected ranking method

          - 'sc' *string* - split by collection or not

          - 'rg' *string* - selected results/page

          - 'formats' *array* - available output formats

          - 'of' *string* - the selected output format

          - 'pl' *string* - `limit to' search pattern
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = ""
        # print search box prolog:
        out += """
                <h1 class="headline">%(ccname)s</h1>
                <form action="%(weburl)s/search.py" method="get">
                <input type="hidden" name="cc" value="%(cc)s">
                <input type="hidden" name="as" value="%(as)s">
                <input type="hidden" name="ln" value="%(ln)s">
               """ % {
                 'ccname' : cc_intl,
                 'weburl' : weburl,
                 'cc' : cgi.escape(cc, 1),
                 'as' : as,
                 'ln' : ln
               }
        if ot: out += self.tmpl_input_hidden('ot', ot)
        if sp: out += self.tmpl_input_hidden('sp', sp)

        leadingtext = _("Search")
        if action == _("Browse") :
            leadingtext = _("Browse")

        if as == 1:
            # print Advanced Search form:
            google = ''
            if cfg_google_box and (p1 or p2 or p3):
                google = """<small> :: <a href="#googlebox">%(search_smwhere)s</a></small>""" % {
                     'search_smwhere' : _("Try your search on...")
                   }

            # define search box elements:
            out += """
            <table class="searchbox">
             <thead>
              <tr>
               <th colspan="3" class="searchboxheader">
                %(leading)s:
               </th>
              </tr>
             </thead>
             <tbody>
              <tr valign="top">
                <td class="searchboxbody">%(matchbox1)s
                  <input type="text" name="p1" size="%(sizepattern)d" value="%(p1)s">
                </td>
                <td class="searchboxbody">%(searchwithin1)s</td>
                <td class="searchboxbody">%(andornot1)s</td>
              </tr>
              <tr valign="top">
                <td class="searchboxbody">%(matchbox2)s
                  <input type="text" name="p2" size="%(sizepattern)d" value="%(p2)s">
                </td>
                <td class="searchboxbody">%(searchwithin2)s</td>
                <td class="searchboxbody">%(andornot2)s</td>
              </tr>
              <tr valign="top">
                <td class="searchboxbody">%(matchbox3)s
                  <input type="text" name="p3" size="%(sizepattern)d" value="%(p3)s">
                </td>
                <td class="searchboxbody">%(searchwithin3)s</td>
                <td class="searchboxbody">
                  <input class="formbutton" type="submit" name="action" value="%(search)s"><input class="formbutton" type="submit" name="action" value="%(browse)s">&nbsp;
                </td>
              </tr>
              <tr valign="bottom">
                <td colspan="3" align="right" class="searchboxbody">
                  <small><a href="%(weburl)s/help/search/tips.%(ln)s.html">%(search_tips)s</a> ::
                         <a href="%(weburl)s/search.py?p=%(p1_qt)s&amp;f=%(f1_qt)s&amp;rm=%(rm)s&amp;cc=%(cc)s&amp;ln=%(ln)s">%(simple_search)s</a>
                  </small>
                  %(google)s
                </td>
              </tr>
             </tbody>
            </table>
            """ % {
              'leading' : leadingtext,
              'sizepattern' : cfg_advancedsearch_pattern_box_width,
              'matchbox1' : self.tmpl_matchtype_box('m1', m1, ln=ln),
              'p1' : cgi.escape(p1,1),
              'searchwithin1' : self.tmpl_searchwithin_select(
                                  ln = ln,
                                  fieldname = 'f1',
                                  selected = f1,
                                  values = self._add_mark_to_field(value = f1, fields = fieldslist, ln = ln)
                                ),
              'andornot1' : self.tmpl_andornot_box(
                                  name = 'op1',
                                  value = op1,
                                  ln = ln
                                ),
              'matchbox2' : self.tmpl_matchtype_box('m2', m2, ln=ln),
              'p2' : cgi.escape(p2,1),
              'searchwithin2' : self.tmpl_searchwithin_select(
                                  ln = ln,
                                  fieldname = 'f2',
                                  selected = f2,
                                  values = self._add_mark_to_field(value = f2, fields = fieldslist, ln = ln)
                                ),
              'andornot2' : self.tmpl_andornot_box(
                                  name = 'op2',
                                  value = op2,
                                  ln = ln
                                ),
              'matchbox3' : self.tmpl_matchtype_box('m3', m3, ln=ln),
              'p3' : cgi.escape(p3,1),
              'searchwithin3' : self.tmpl_searchwithin_select(
                                  ln = ln,
                                  fieldname = 'f3',
                                  selected = f3,
                                  values = self._add_mark_to_field(value = f3, fields = fieldslist, ln = ln)
                                ),
              'search' : _("Search"),
              'browse' : _("Browse"),
              'weburl' : weburl,
              'ln' : ln,
              'search_tips': _("Search Tips"),
              'p1_qt' : urllib.quote(p1),
              'f1_qt' : urllib.quote(f1),
              'rm' : urllib.quote(rm),
              'cc' : urllib.quote(cc),
              'simple_search' : _("Simple Search"),
              'google' : google,
            }
        else:
            # print Simple Search form:
            google = ''
            if cfg_google_box and (p1 or p2 or p3):
                google = """<small> :: <a href="#googlebox">%(search_smwhere)s</a></small>""" % {
                     'search_smwhere' : _("Try your search on...")
                   }

            out += """
            <table class="searchbox">
             <thead>
              <tr>
               <th colspan="3" class="searchboxheader">
                %(leading)s:
               </th>
              </tr>
             </thead>
             <tbody>
              <tr valign="top">
                <td class="searchboxbody"><input type="text" name="p" size="%(sizepattern)d" value="%(p)s"></td>
                <td class="searchboxbody">%(searchwithin)s</td>
                <td class="searchboxbody">
                  <input class="formbutton" type="submit" name="action" value="%(search)s">
                  <input class="formbutton" type="submit" name="action" value="%(browse)s">&nbsp;
                </td>
              </tr>
              <tr valign="bottom">
                <td colspan="3" align="right" class="searchboxbody">
                  <small><a href="%(weburl)s/help/search/tips.%(ln)s.html">%(search_tips)s</a> ::
                         <a href="%(weburl)s/search.py?p1=%(p_qt)s&amp;f1=%(f_qt)s&amp;rm=%(rm)s&amp;as=1&amp;cc=%(cc)s&amp;ln=%(ln)s">%(advanced_search)s</a>
                  </small>
                  %(google)s
                </td>
              </tr>
             </tbody>
            </table>
            """ % {
              'leading' : leadingtext,
              'sizepattern' : cfg_advancedsearch_pattern_box_width,
              'p' : cgi.escape(p, 1),
              'searchwithin' : self.tmpl_searchwithin_select(
                                  ln = ln,
                                  fieldname = 'f',
                                  selected = f,
                                  values = self._add_mark_to_field(value = f, fields = fieldslist, ln = ln)
                                ),
              'search' : _("Search"),
              'browse' : _("Browse"),
              'weburl' : weburl,
              'ln' : ln,
              'search_tips': _("Search Tips"),
              'p_qt' : urllib.quote(p),
              'f_qt' : urllib.quote(f),
              'rm' : urllib.quote(rm),
              'cc' : urllib.quote(cc),
              'advanced_search' : _("Advanced Search"),
              'google' : google,
            }
            
        ## secondly, print Collection(s) box:
        selects = ''
        for sel in coll_selects:
            selects += self.tmpl_select(fieldname = 'c', values = sel)

        out += """
            <table class="searchbox">
             <thead>
              <tr>
               <th colspan="3" class="searchboxheader">
                %(leading)s %(msg_coll)s:
               </th>
              </tr>
             </thead>
             <tbody>
              <tr valign="bottom">
               <td valign="top" class="searchboxbody">
                 %(colls)s
               </td>
              </tr>
             </tbody>
            </table>
             """ % {
               'leading' : leadingtext,
               'msg_coll' : _("collections"),
               'colls' : selects,
             }

        ## thirdly, print search limits, if applicable:
        if action != _("Browse") and pl:
            out += """<table class="searchbox">
                       <thead>
                        <tr>
                          <th class="searchboxheader">
                            %(limitto)s:
                          </th>
                        </tr>
                       </thead>
                       <tbody>
                        <tr valign="bottom">
                          <td class="searchboxbody">
                           <input type="text" name="pl" size="%(sizepattern)d" value="%(pl)s">
                          </td>
                        </tr>
                       </tbody>
                      </table>""" % {
                        'limitto' : _("Limit to"),
                        'sizepattern' : cfg_advancedsearch_pattern_box_width,
                        'pl' : cgi.escape(pl, 1),
                      }

        ## fourthly, print from/until date boxen, if applicable:
        if action == _("Browse") or (d1y==0 and d1m==0 and d1d==0 and d2y==0 and d2m==0 and d2d==0):
            pass # do not need it
        else:
            cell_6_a = self.tmpl_inputdate("d1", ln, d1y, d1m, d1d)
            cell_6_b = self.tmpl_inputdate("d2", ln, d2y, d2m, d2d)
            out += """<table class="searchbox">
                       <thead>
                        <tr>
                          <th class="searchboxheader">
                            %(added)s
                          </th>
                          <th class="searchboxheader">
                            %(until)s
                          </th>
                        </tr>
                       </thead>
                       <tbody>
                        <tr valign="bottom">
                          <td class="searchboxbody">%(date1)s</td>
                          <td class="searchboxbody">%(date2)s</td>
                        </tr>
                       </tbody>
                      </table>""" % {
                        'added' : _("Added since:"),
                        'until' : _("until:"),
                        'date1' : self.tmpl_inputdate("d1", ln, d1y, d1m, d1d),
                        'date2' : self.tmpl_inputdate("d2", ln, d2y, d2m, d2d),
                      }

        ## fifthly, print Display results box, including sort/rank, formats, etc:
        if action != _("Browse"):

            rgs = []
            for i in [10, 25, 50, 100, 250, 500]:
                rgs.append({ 'value' : i, 'text' : "%d %s" % (i, _("results"))})

            # sort by:
            out += """<table class="searchbox">
                 <thead>
                  <tr>
                   <th class="searchboxheader">
                    %(sort_by)s
                   </th>
                   <th class="searchboxheader">
                    %(display_res)s
                   </th>
                   <th class="searchboxheader">
                    %(out_format)s
                   </th>
                  </tr>
                 </thead>
                 <tbody>
                  <tr valign="bottom">
                   <td valign="top" class="searchboxbody">
                     %(select_sf)s %(select_so)s %(select_rm)s
                   </td>
                   <td valign="top" class="searchboxbody">
                     %(select_rg)s %(select_sc)s
                   </td>
                   <td valign="top" class="searchboxbody">%(select_of)s</td>
                  </tr>
                 </tbody>
                </table>""" % {
                  'sort_by' : _("Sort by:"),
                  'display_res' : _("Display results:"),
                  'out_format' : _("Output format:"),
                  'select_sf' : self.tmpl_select(fieldname = 'sf', values = sort_formats, selected = sf, css_class = 'address'),
                  'select_so' : self.tmpl_select(fieldname = 'so', values = [{
                                    'value' : 'a',
                                    'text' : _("asc.")
                                  }, {
                                    'value' : 'd',
                                    'text' : _("desc.")
                                  }], selected = so, css_class = 'address'),
                  'select_rm' : self.tmpl_select(fieldname = 'rm', values = ranks, selected = rm, css_class = 'address'),
                  'select_rg' : self.tmpl_select(fieldname = 'rg', values = rgs, selected = rg, css_class = 'address'),
                  'select_sc' : self.tmpl_select(fieldname = 'sc', values = [{
                                    'value' : '0',
                                    'text' : _("single list")
                                  }, {
                                    'value' : '1',
                                    'text' : _("split by collection")
                                  }], selected = so, css_class = 'address'),
                  'select_of' : self.tmpl_searchwithin_select(
                                  ln = ln,
                                  fieldname = 'of',
                                  selected = of,
                                  values = self._add_mark_to_field(value = of, fields = formats, chars = 3, ln = ln)
                                ),
                }

        ## last but not least, print end of search box:
        out += """</form>"""
        return out

    def tmpl_input_hidden(self, name, value):
        "Produces the HTML code for a hidden field "
        return """<input type="hidden" name="%(name)s" value="%(value)s">""" % {
                 'name' : cgi.escape(str(name), 1),
                 'value' : cgi.escape(str(value), 1),
               }

    def _add_mark_to_field(self, value, fields, ln, chars = 1):
        """Adds the current value as a MARC tag in the fields array
        Useful for advanced search"""

        # load the right message language
        _ = gettext_set_language(ln)

        out = fields
        if value and str(value[0:chars]).isdigit():
            out.append({'value' : value,
                        'text' : str(value) + " " + _("MARC tag")
                        })
        return out

    def tmpl_google_box(self, ln, cc, p, f, prolog_start, prolog_end, column_separator, link_separator, epilog):
        """Creates the box that proposes links to other useful search engines like Google.

        Parameters:

          - 'ln' *string* - The language to display in

          - 'cc' *string* - the internal current collection name

          - 'p' *string* - the search query

          - 'f' *string* - the current field

          - 'prolog_start, prolog_end, column_separator, link_separator, epilog' *strings* - default HTML code for the specified position in the box
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out_links = []
        p_quoted = urllib.quote(p)
        # Amazon
        if cfg_google_box_servers.get('Amazon', 0):
            if string.find(cc, "Book") >= 0:
                if f == "author":
                    out_links.append("""<a class="google" href="http://www.amazon.com/exec/obidos/external-search/?field-author=%s&tag=cern">%s %s Amazon</a>""" % (p_quoted, p, _('in')))
                else:
                    out_links.append("""<a class="google" href="http://www.amazon.com/exec/obidos/external-search/?keyword=%s&tag=cern">%s %s Amazon</a>""" % (p_quoted, p, _('in')))
        # CERN Intranet:
        if cfg_google_box_servers.get('CERN Intranet', 0):
            out_links.append("""<a class="google" href="http://search.cern.ch/query.html?qt=%s">%s %s CERN&nbsp;Intranet</a>""" % (urllib.quote(string.replace(p, ' ', ' +')), p, _('in')))
        # CERN Agenda:
        if cfg_google_box_servers.get('CERN Agenda', 0):
            if f == "author":
                out_links.append("""<a class="google" href="http://agenda.cern.ch/search.php?field=speaker&keywords=%s&search=Search">%s %s CERN&nbsp;Agenda</a>""" % (p_quoted, p, _('in')))
            elif f == "title":
                out_links.append("""<a class="google" href="http://agenda.cern.ch/search.php?field=title&keywords=%s&search=Search">%s %s CERN&nbsp;Agenda</a>""" % (p_quoted, p, _('in')))
        # CERN EDMS:
        if cfg_google_box_servers.get('CERN Agenda', 0):
            # FIXME: reusing CERN Agenda config variable until we can enter CERN EDMS into config.wml
            if f == "author":
                out_links.append("""<a class="google" href="https://edms.cern.ch/cedar/plsql/fullsearch.doc_search?p_search_type=ADVANCED&p_author=%s">%s %s CERN&nbsp;EDMS</a>""" % (p_quoted, p, _("in")))
            elif f == "title" or f == "abstract" or f == "keyword":
                out_links.append("""<a class="google" href="https://edms.cern.ch/cedar/plsql/fullsearch.doc_search?p_search_type=ADVANCED&p_title=%s">%s %s CERN&nbsp;EDMS</a>""" % (p_quoted, p, _("in")))
            elif f == "reportnumber":
                out_links.append("""<a class="google" href="https://edms.cern.ch/cedar/plsql/fullsearch.doc_search?p_search_type=ADVANCED&p_document_id=%s">%s %s CERN&nbsp;EDMS</a>""" % (p_quoted, p, _("in")))
            else:
                out_links.append("""<a class="google" href="https://edms.cern.ch/cedar/plsql/fullsearch.doc_search?p_search_type=BASE&p_free_text=%s">%s %s CERN&nbsp;EDMS</a>""" % (p_quoted, p, _("in")))
        # CiteSeer:
        if cfg_google_box_servers.get('CiteSeer', 0):
            out_links.append("""<a class="google" href="http://citeseer.ist.psu.edu/cs?q=%s">%s %s CiteSeer</a>""" % (p_quoted, p, _('in')))
        # Google Print:
        if cfg_google_box_servers.get('Google Scholar', 0):
            # FIXME: reusing Google Scholar config variable until we can enter Google Print into config.wml
            if string.find(cc, "Book") >= 0:
                out_links.append("""<a class="google" href="http://print.google.com/print?q=%s">%s %s Google Print</a>""" % (p_quoted, p, _("in")))
        # Google Scholar:
        if cfg_google_box_servers.get('Google Scholar', 0):
            if f == "author":
                out_links.append("""<a class="google" href="http://scholar.google.com/scholar?q=author%%3A%s">%s %s Google Scholar</a>""" % (p_quoted, p, _('in')))
            else:
                out_links.append("""<a class="google" href="http://scholar.google.com/scholar?q=%s">%s %s Google Scholar</a>""" % (p_quoted, p, _('in')))
        # Google Web:
        if cfg_google_box_servers.get('Google Web', 0):
            if f == "author":
                p_google = p
                if string.find(p, ",") >= 0 and (not p.startswith('"')) and (not p.endswith('"')):
                    p_lastname, p_firstnames = string.split(p, ",", 1)
                    p_google = '"%s %s" OR "%s %s"' % (p_lastname, p_firstnames, p_firstnames, p_lastname)
                out_links.append("""<a class="google" href="http://google.com/search?q=%s">%s %s Google Web</a>""" % (urllib.quote(p_google), p_google, _('in')))
            else:
                out_links.append("""<a class="google" href="http://google.com/search?q=%s">%s %s Google Web</a>""" % (p_quoted, p, _('in')))
        # IEC
        if cfg_google_box_servers.get('IEC', 0):
            if string.find(cc, "Standard") >= 0:
                out_links.append("""<a class="google" href="http://www.iec.ch/cgi-bin/procgi.pl/www/iecwww.p?wwwlang=E&wwwprog=sea22.p&search=text&searchfor=%s">%s %s IEC</a>""" % (p_quoted, p, _('in')))
        # IHS
        if cfg_google_box_servers.get('IHS', 0):
            if string.find(cc, "Standard") >= 0:
                out_links.append("""<a class="google" href="http://global.ihs.com/search_res.cfm?&input_doc_title=%s">%s %s IHS</a>""" % (p_quoted, p, _('in')))
        # INSPEC
        if cfg_google_box_servers.get('INSPEC', 0):
            if f == "author":
                p_inspec = sre.sub(r'(, )| ', '-', p)
                p_inspec = sre.sub(r'(-\w)\w+$', '\\1', p_inspec)
                out_links.append("""<a class="google" href="http://www.datastarweb.com/cern/?dblabel=inzz&query=%s.au.">%s %s INSPEC</a>""" % (urllib.quote(p_inspec), p_inspec, _('in')))
            elif f == "title":
                out_links.append("""<a class="google" href="http://www.datastarweb.com/cern/?dblabel=inzz&query=%s.ti.">%s %s INSPEC</a>""" % (p_quoted, p, _('in')))
            elif f == "abstract":
                out_links.append("""<a class="google" href="http://www.datastarweb.com/cern/?dblabel=inzz&query=%s.ab.">%s %s INSPEC</a>""" % (p_quoted, p, _('in')))
            elif f == "year":
                out_links.append("""<a class="google" href="http://www.datastarweb.com/cern/?dblabel=inzz&query=%s.yr.">%s %s INSPEC</a>""" % (p_quoted, p, _('in')))
        # ISO
        if cfg_google_box_servers.get('ISO', 0):
            if string.find(cc, "Standard") >= 0:
                out_links.append("""<a class="google" href="http://www.iso.org/iso/en/StandardsQueryFormHandler.StandardsQueryFormHandler?languageCode=en&keyword=%s&lastSearch=false&title=true&isoNumber=&isoPartNumber=&isoDocType=ALL&isoDocElem=ALL&ICS=&stageCode=&stagescope=Current&repost=1&stagedatepredefined=&stageDate=&committee=ALL&subcommittee=&scopecatalogue=CATALOGUE&scopeprogramme=PROGRAMME&scopewithdrawn=WITHDRAWN&scopedeleted=DELETED&sortOrder=ISO">%s %s ISO</a>""" % (p_quoted, p, _('in')))
        # KEK
        if cfg_google_box_servers.get('KEK', 0):
            kek_search_title = "KEK KISS Preprints"
            kek_search_baseurl = "http://www-lib.kek.jp/cgi-bin/kiss_prepri?"
            if string.find(cc, "Book") >= 0:
                kek_search_title = "KEK Library Books"
                kek_search_baseurl = "http://www-lib.kek.jp/cgi-bin/kiss_book?DSP=1&"
            elif string.find(cc, "Periodical") >= 0:
                kek_search_title = "KEK Library Journals"
                kek_search_baseurl = "http://www-lib.kek.jp/cgi-bin/kiss_book?DSP=2&"
            if f == "author":
                out_links.append("""<a class="google" href="%sAU=%s">%s %s %s</a>""" % \
                                 (kek_search_baseurl, p_quoted, p, _('in'), kek_search_title))
            elif f == "title":
                out_links.append("""<a class="google" href="%sTI=%s">%s %s %s</a>""" % \
                                 (kek_search_baseurl, p_quoted, p, _('in'), kek_search_title))
            elif f == "reportnumber":
                out_links.append("""<a class="google" href="%sRP=%s">%s %s %s</a>""" % \
                                 (kek_search_baseurl, p_quoted, p, _('in'), kek_search_title))
        # NEBIS
        if cfg_google_box_servers.get('NEBIS', 0):
            if string.find(cc, "Book") >= 0:
                if f == "author":
                    out_links.append("""<a class="google" href="http://opac.nebis.ch/F/?func=find-b&REQUEST=%s&find_code=WAU">%s %s NEBIS</a>""" % (p_quoted, p, _('in')))
                elif f == "title":
                    out_links.append("""<a class="google" href="http://opac.nebis.ch/F/?func=find-b&REQUEST=%s&find_code=WTI">%s %s NEBIS</a>""" % (p_quoted, p, _('in')))
                else:
                    out_links.append("""<a class="google" href="http://opac.nebis.ch/F/?func=find-b&REQUEST=%s&find_code=WRD">%s %s NEBIS</a>""" % (p_quoted, p, _('in')))
        # Scirus:
        if cfg_google_box_servers.get('Google Scholar', 0):
            # FIXME: reusing Google Scholar config variable until we can enter Scirus into config.wml
            if f == "author":
                out_links.append("""<a class="google" href="http://www.scirus.com/srsapp/search?q=author%%3A%s">%s %s Scirus</a>""" % (p_quoted, p, _("in")))
            elif f == "title":
                out_links.append("""<a class="google" href="http://www.scirus.com/srsapp/search?q=title%%3A%s">%s %s Scirus</a>""" % (p_quoted, p, _("in")))
            elif f == "keyword":
                out_links.append("""<a class="google" href="http://www.scirus.com/srsapp/search?q=keywords%%3A%s">%s %s Scirus</a>""" % (p_quoted, p, _("in")))
            else:
                out_links.append("""<a class="google" href="http://www.scirus.com/srsapp/search?q=%s">%s %s Scirus</a>""" % (p_quoted, p, _("in")))
        # SPIRES
        if cfg_google_box_servers.get('SPIRES', 0):
            spires_search_title = "SLAC SPIRES HEP"
            spires_search_baseurl = "http://www.slac.stanford.edu/spires/find/hep/"
            if string.find(cc, "Book") >= 0:
                spires_search_title = "SLAC Library Books"
                spires_search_baseurl = "http://www.slac.stanford.edu/spires/find/books/"
            elif string.find(cc, "Periodical") >= 0:
                spires_search_title = "SLAC Library Journals"
                spires_search_baseurl = "http://www.slac.stanford.edu/spires/find/tserials/"
            if f == "author":
                out_links.append("""<a class="google" href="%swww?AUTHOR=%s">%s %s %s</a>""" % \
                       (spires_search_baseurl, p_quoted, p, _('in'), spires_search_title))
            elif f == "title":
                out_links.append("""<a class="google" href="%swww?TITLE=%s">%s %s %s</a>""" % \
                       (spires_search_baseurl, p_quoted, p, _('in'), spires_search_title))
            elif f == "reportnumber":
                out_links.append("""<a class="google" href="%swww?REPORT-NUM=%s">%s %s %s</a>""" % \
                       (spires_search_baseurl, p_quoted, p, _('in'), spires_search_title))
            elif f == "keyword":
                out_links.append("""<a class="google" href="%swww?k=%s">%s %s %s</a>""" % \
                       (spires_search_baseurl, p_quoted, p, _('in'), spires_search_title))
            else: # invent a poor man's any field search since SPIRES doesn't support one
                out_links.append("""<a class="google" href="%swww?rawcmd=find+t+%s+or+a+%s+or+k+%s+or+s+%s+or+r+%s">%s %s %s</a>""" % \
                (spires_search_baseurl, p_quoted, p_quoted, p_quoted, p_quoted, p_quoted, p, _('in'), spires_search_title))
        # okay, so print the box now:
        out = ""
        if out_links:
            out += """<a name="googlebox"></a>"""
            out += prolog_start + _("Haven't found what you were looking for? Try your search on other servers:") + prolog_end
            nb_out_links_in_one_column = len(out_links)/2
            out += string.join(out_links[:nb_out_links_in_one_column], link_separator)
            out += column_separator
            out += string.join(out_links[nb_out_links_in_one_column:], link_separator)
            out += epilog
        return out

    def tmpl_search_pagestart(self, ln) :
        "page start for search page. Will display after the page header"
        return """<div class="pagebody"><div class="pagebodystripemiddle">"""

    def tmpl_search_pageend(self, ln) :
        "page end for search page. Will display just before the page footer"
        return """</div></div>"""

    def tmpl_print_warning(self, msg, type, prologue, epilogue):
        """Prints warning message and flushes output.

        Parameters:

          - 'msg' *string* - The message string

          - 'type' *string* - the warning type

          - 'prologue' *string* - HTML code to display before the warning

          - 'epilogue' *string* - HTML code to display after the warning
        """

        out = '\n%s<span class="quicknote">' % (prologue)
        if type:
            out += '%s: ' % type
        out += '%s</span>%s' % (msg, epilogue)
        return out

    def tmpl_print_search_info(self, ln, weburl, middle_only, collection, collection_name, as, sf, so, rm, rg, nb_found, of, ot, p, f, f1, f2, f3, m1, m2, m3, op1, op2, p1, p2, p3, d1y, d1m, d1d, d2y, d2m, d2d, all_fieldcodes, cpu_time, pl_in_url, jrec, sc, sp):
        """Prints stripe with the information on 'collection' and 'nb_found' results and CPU time.
           Also, prints navigation links (beg/next/prev/end) inside the results set.
           If middle_only is set to 1, it will only print the middle box information (beg/netx/prev/end/etc) links.
           This is suitable for displaying navigation links at the bottom of the search results page.

        Parameters:

          - 'ln' *string* - The language to display

          - 'weburl' *string* - The base URL for the site

          - 'middle_only' *bool* - Only display parts of the interface

          - 'collection' *string* - the collection name

          - 'collection_name' *string* - the i18nized current collection name

          - 'as' *bool* - if we display the advanced search interface

          - 'sf' *string* - the currently selected sort format

          - 'so' *string* - the currently selected sort order ("a" or "d")

          - 'rm' *string* - selected ranking method

          - 'rg' *int* - selected results/page

          - 'nb_found' *int* - number of results found

          - 'of' *string* - the selected output format

          - 'ot' *string* - hidden values

          - 'p' *string* - Current search words

          - 'f' *string* - the fields in which the search was done

          - 'f1, f2, f3, m1, m2, m3, p1, p2, p3, op1, op2' *strings* - the search parameters

          - 'jrec' *int* - number of first record on this page

          - 'd1y, d2y, d1m, d2m, d1d, d2d' *int* - the search between dates

          - 'all_fieldcodes' *array* - all the available fields

          - 'cpu_time' *float* - the time of the query in seconds
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = ""
        # left table cells: print collection name
        if not middle_only:
            out += """
                  <a name="%(collection_qt)s"></a>
                  <form action="%(weburl)s/search.py" method="get">
                  <table class="searchresultsbox"><tr><td class="searchresultsboxheader" align="left">
                  <strong><big>
                  <a href="%(weburl)s/?c=%(collection_qt_plus)s&amp;as=%(as)d&amp;ln=%(ln)s">%(collection_name)s</a></big></strong></td>
                  """ % {
                    'collection_qt' : urllib.quote(collection),
                    'collection_qt_plus' : urllib.quote_plus(collection),
                    'as' : as,
                    'ln' : ln,
                    'collection_name' : collection_name,
                    'weburl' : weburl,
                  }
        else:
            out += """
                  <form action="%(weburl)s/search.py" method="get"><div align="center">
                  """ % { 'weburl' : weburl }

        # middle table cell: print beg/next/prev/end arrows:
        if not middle_only:
            out += """<td class="searchresultsboxheader" align="center">
                      %(recs_found)s &nbsp;""" % {
                     'recs_found' : _("<strong>%s</strong> records found") % self.tmpl_nice_number(nb_found, ln)
                   }
        else:
            out += "<small>"
            if nb_found > rg:
                out += "" + collection_name + " : " + _("<strong>%s</strong> records found") % self.tmpl_nice_number(nb_found, ln) + " &nbsp; "

        if nb_found > rg: # navig.arrows are needed, since we have many hits
            if (pl_in_url):
              scbis = 1
            else:
              scbis = 0
            url = """%(weburl)s/search.py?p=%(p_qt)s&amp;cc=%(coll_qt)s&amp;f=%(f)s&amp;sf=%(sf)s&amp;so=%(so)s&amp;sp=%(sp)s&amp;rm=%(rm)s&amp;of=%(of)s&amp;ot=%(ot)s&amp;as=%(as)s&amp;ln=%(ln)s&amp;p1=%(p1)s&amp;p2=%(p2)s&amp;p3=%(p3)s&amp;f1=%(f1)s&amp;f2=%(f2)s&amp;f3=%(f3)s&amp;m1=%(m1)s&amp;m2=%(m2)s&amp;m3=%(m3)s&amp;op1=%(op1)s&amp;op2=%(op2)s&amp;sc=%(sc)d&amp;d1y=%(d1y)d&amp;d1m=%(d1m)d&amp;d1d=%(d1d)d&amp;d2y=%(d2y)d&amp;d2m=%(d2m)d&amp;d2d=%(d2d)d""" % {
                    'weburl' : weburl,
                    'p_qt' : urllib.quote(p),
                    'coll_qt' : urllib.quote(collection),
                    'f' : f,
                    'sf' : sf,
                    'so' : so,
                    'sp' : sp,
                    'rm' : rm,
                    'of' : of,
                    'ot' : ot,
                    'as' : as,
                    'ln' : ln,
                    'p1' : urllib.quote(p1),
                    'p2' : urllib.quote(p2),
                    'p3' : urllib.quote(p3),
                    'f1' : f1,
                    'f2' : f2,
                    'f3' : f3,
                    'm1' : m1,
                    'm2' : m2,
                    'm3' : m3,
                    'op1' : op1,
                    'op2' : op2,
                    'sc' : scbis,
                    'd1y' : d1y,
                    'd1m' : d1m,
                    'd1d' : d1d,
                    'd2y' : d2y,
                    'd2m' : d2m,
                    'd2d' : d2d,
                  }

            # @todo here
            if jrec-rg > 1:
                out += """<a class="img" href="%(url)s&amp;jrec=1&amp;rg=%(rg)d"><img src="%(weburl)s/img/sb.gif" alt="%(begin)s" border="0"></a>""" % {
                         'url' : url,
                         'rg' : rg,
                         'weburl' : weburl,
                         'begin' : _("begin"),
                       }
            if jrec > 1:
                out += """<a class="img" href="%(url)s&amp;jrec=%(jrec)d&amp;rg=%(rg)d"><img src="%(weburl)s/img/sp.gif" alt="%(previous)s" border="0"></a>""" % {
                         'url' : url,
                         'jrec' : max(jrec-rg, 1),
                         'rg' : rg,
                         'weburl' : weburl,
                         'previous' : _("previous")
                       }
            if jrec+rg-1 < nb_found:
                out += "%d - %d" % (jrec, jrec+rg-1)
            else:
                out += "%d - %d" % (jrec, nb_found)
            if nb_found >= jrec+rg:
                out += """<a class="img" href="%(url)s&amp;jrec=%(jrec)d&amp;rg=%(rg)d"><img src="%(weburl)s/img/sn.gif" alt="%(next)s" border="0"></a>""" % {
                         'url' : url,
                         'jrec' : jrec + rg,
                         'rg' : rg,
                         'weburl' : weburl,
                         'next' : _("next")
                       }
            if nb_found >= jrec+rg+rg:
                out += """<a class="img" href="%(url)s&amp;jrec=%(jrec)d&amp;rg=%(rg)d"><img src="%(weburl)s/img/se.gif" alt="%(end)s" border="0"></a>""" % {
                         'url' : url,
                         'jrec' : nb_found-rg+1,
                         'rg' : rg,
                         'weburl' : weburl,
                         'end' : _("end")
                       }

            # still in the navigation part
            cc = collection
            sc = 0
            for var in ['p', 'cc', 'f', 'sf', 'so', 'of', 'rg', 'as', 'ln', 'p1', 'p2', 'p3', 'f1', 'f2', 'f3', 'm1', 'm2', 'm3', 'op1', 'op2', 'sc', 'd1y', 'd1m', 'd1d', 'd2y', 'd2m', 'd2d']:
                out += self.tmpl_input_hidden(name = var, value = vars()[var])
            for var in ['ot', 'sp', 'rm']:
                if vars()[var]:
                    out += self.tmpl_input_hidden(name = var, value = vars()[var])
            if pl_in_url:
                fieldargs = cgi.parse_qs(pl_in_url)
                for fieldcode in all_fieldcodes:
                    # get_fieldcodes():
                    if fieldargs.has_key(fieldcode):
                        for val in fieldargs[fieldcode]:
                            out += self.tmpl_input_hidden(name = fieldcode, value = val)
            out += """&nbsp; %(jump)s <input type="text" name="jrec" size="4" value="%(jrec)d">""" % {
                     'jump' : _("jump to record:"),
                     'jrec' : jrec,
                   }

        if not middle_only:
            out += "</td>"
        else:
            out += "</small>"

        # right table cell: cpu time info
        if not middle_only:
            if cpu_time > -1:
                out += """<td class="searchresultsboxheader" align="right"><small>%(time)s</small>&nbsp;</td>""" % {
                         'time' : _("Search took %.2f seconds.") % cpu_time,
                       }
            out += "</tr></table>"
        else:
            out += "</div>"
        out += "</form>"
        return out

    def tmpl_nice_number(self, number, ln):
        "Returns nicely printed number NUM in language LN using the locale."
        if number is None:
            return None
        # Temporarily switch the numeric locale to the requeted one, and format the number
        # In case the system has no locale definition, use the vanilla form
        ol = locale.getlocale(locale.LC_NUMERIC)
        try:
            locale.setlocale(locale.LC_NUMERIC, self.tmpl_localemap.get(ln, self.tmpl_default_locale))
        except locale.Error:
            return str(number)
        number = locale.format('%d', number, True)
        locale.setlocale(locale.LC_NUMERIC, ol)
        return number

    def tmpl_records_format_htmlbrief(self, ln, weburl, rows, relevances_prologue, relevances_epilogue):
        """Returns the htmlbrief format of the records

        Parameters:

          - 'ln' *string* - The language to display

          - 'weburl' *string* - The base URL for the site

          - 'rows' *array* - Parts of the interface to display, in the format:

          - 'rows[number]' *int* - The order number

          - 'rows[recid]' *int* - The recID

          - 'rows[relevance]' *string* - The relevance of the record

          - 'rows[record]' *string* - The formatted record

          - 'relevances_prologue' *string* - HTML code to prepend the relevance indicator

          - 'relevances_epilogue' *string* - HTML code to append to the relevance indicator (used mostly for formatting)

        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """
              <form action="%(weburl)s/yourbaskets.py/add" method="post">
              <table>
              """ % {
                'weburl' : weburl,
              }

        for row in rows:
            out += """
                    <tr><td valign="top" align="right" nowrap><input name="recid" type="checkbox" value="%(recid)s">
                    %(number)s.
                   """ % row
            if row['relevance']:
                out += """<br><div class="rankscoreinfo"><a title="rank score">%(prologue)s%(relevance)s%(epilogue)s</a></div>""" % {
                         'prologue' : relevances_prologue,
                         'epilogue' : relevances_epilogue,
                         'relevance' : row['relevance']
                       }
            out += """</td><td valign="top">%s</td></tr>""" % row['record']
        out += """</table>
               <br><input class="formbutton" type="submit" name="action" value="%(basket)s">
               </form>""" % {
                 'basket' : _("ADD TO BASKET")
               }
        return out

    def tmpl_records_format_other(self, ln, weburl, rows, format, url_args):
        """Returns other formats of the records

        Parameters:

          - 'ln' *string* - The language to display

          - 'weburl' *string* - The base URL for the site

          - 'rows' *array* - Parts of the interface to display, in the format:

          - 'rows[record]' *string* - The formatted record

          - 'rows[number]' *int* - The order number

          - 'rows[recid]' *int* - The recID

          - 'rows[relevance]' *string* - The relevance of the record

          - 'format' *string* - The current format

          - 'url_args' *string* - The rest of the search query
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """ <p><div align="right"><small>%(format)s: """ % {
                'format' : _("Format")
              }

        if format == "hm":
            out += """<a href="%(weburl)s/search.py?%(url_args)s">HTML</a> | <a href="%(weburl)s/search.py?%(url_args)s&of=hx">BibTeX</a> | <a href="%(weburl)s/search.py?%(url_args)s&of=xd">DC</a> | MARC | <a href="%(weburl)s/search.py?%(url_args)s&of=xm">MARCXML</a>""" % vars()
        elif format == "hx":
            out += """<a href="%(weburl)s/search.py?%(url_args)s">HTML</a> | BibTeX | <a href="%(weburl)s/search.py?%(url_args)s&of=xd">DC</a> | <a href="%(weburl)s/search.py?%(url_args)s&of=hm">MARC</a> | <a href="%(weburl)s/search.py?%(url_args)s&of=xm">MARCXML</a>""" % vars()
        else:
            out += """HTML | <a href="%(weburl)s/search.py?%(url_args)s&of=hx">BibTeX</a> | <a href="%(weburl)s/search.py?%(url_args)s&of=xd">DC</a> | <a href="%(weburl)s/search.py?%(url_args)s&of=hm">MARC</a> | <a href="%(weburl)s/search.py?%(url_args)s&of=xm">MARCXML</a>""" % vars()

        out += "</small></div>"

        for row in rows:
            out += row ['record']

            if format.startswith("hd"):
                # do not print further information but for HTML detailed formats
            
                if row ['creationdate']:
                    out += """<div class="recordlastmodifiedbox">%(dates)s</div>
                              <p><span class="moreinfo"><a class="moreinfo" href="%(weburl)s/search.py?p=recid:%(recid)d&amp;rm=wrd&amp;ln=%(ln)s">%(similar)s</a></span>
                              <form action="%(weburl)s/yourbaskets.py/add" method="post">
                                <input name="recid" type="hidden" value="%(recid)s">
                                <br><input class="formbutton" type="submit" name="action" value="%(basket)s">
                              </form>
                           """ % {
                             'dates' : _("Record created %s, last modified %s") % (row['creationdate'], row['modifydate']),
                             'weburl' : weburl,
                             'recid' : row['recid'],
                             'ln' : ln,
                             'similar' : _("Similar records"),
                             'basket' : _("ADD TO BASKET")
                             }

                out += '<table>'

                if row.has_key ('citinglist'):
                    cs = row ['citinglist']

                    similar = self.tmpl_print_record_list_for_similarity_boxen (
                        _("Cited by: %s records") % len (cs), cs, ln)

                    out += '''
                    <tr><td>
                      %(similar)s&nbsp;<a href="%(weburl)s/search.py?p=recid:%(recid)d&amp;rm=cit&amp;ln=%(ln)s">%(more)s</a>
                      <br><br>
                    </td></tr>''' % { 'weburl': weburl,   'recid': row ['recid'], 'ln': ln,
                                      'similar': similar, 'more': _("more"),
                                      }

                if row.has_key ('cociting'):
                    cs = row ['cociting']

                    similar = self.tmpl_print_record_list_for_similarity_boxen (
                        _("Co-cited with: %s records") % len (cs), cs, ln)

                    out += '''
                    <tr><td>
                      %(similar)s&nbsp;<a href="%(weburl)s/search.py?p=cocitedwith:%(recid)d&amp;ln=%(ln)s">%(more)s</a>
                      <br>
                    </td></tr>''' % { 'weburl': weburl,   'recid': row ['recid'], 'ln': ln,
                                      'similar': similar, 'more': _("more"),
                                      }

                if row.has_key ('citationhistory'):
                    out += '<tr><td>%s</td></tr>' % row ['citationhistory']

                if row.has_key ('downloadsimilarity'):
                    cs = row ['downloadsimilarity']

                    similar = self.tmpl_print_record_list_for_similarity_boxen (
                        _("People who downloaded this document also downloaded:"), cs, ln)

                    out += '''
                    <tr><td>%(graph)s</td></tr>
                    <tr><td>%(similar)s</td></tr
                    >''' % { 'weburl': weburl,   'recid': row ['recid'], 'ln': ln,
                             'similar': similar, 'more': _("more"),
                             'graph': row ['downloadhistory']
                             }

                out += '</table>'

                if row.has_key ('viewsimilarity'):
                    out += '<p>&nbsp'
                    out += self.tmpl_print_record_list_for_similarity_boxen (
                        _("People who viewed this page also viewed:"), row ['viewsimilarity'], ln)

                if row.has_key ('reviews'):
                    out += '<p>&nbsp'
                    out += row['reviews']

                if row.has_key ('comments'):
                    out += row['comments']

            out += "<p>&nbsp;"
        return out

    def tmpl_print_results_overview(self, ln, weburl, results_final_nb_total, cpu_time, results_final_nb, colls, url_args):
        """Prints results overview box with links to particular collections below.

        Parameters:

          - 'ln' *string* - The language to display

          - 'weburl' *string* - The base URL for the site

          - 'results_final_nb_total' *int* - The total number of hits for the query

          - 'colls' *array* - The collections with hits, in the format:

          - 'coll[code]' *string* - The code of the collection (canonical name)

          - 'coll[name]' *string* - The display name of the collection

          - 'results_final_nb' *array* - The number of hits, indexed by the collection codes:

          - 'cpu_time' *string* - The time the query took

          - 'url_args' *string* - The rest of the search query
        """

        if len(colls) == 1:
            # if one collection only, print nothing:
            return ""

        # load the right message language
        _ = gettext_set_language(ln)

        # first find total number of hits:
        out = """<p><table class="searchresultsbox">
                <thead><tr><th class="searchresultsboxheader">%(founds)s</th></tr></thead>
                <tbody><tr><td class="searchresultsboxbody"> """ % {
                'founds' : _("<strong>Results overview:</strong> Found <strong>%s</strong> records in %.2f seconds.") % (self.tmpl_nice_number(results_final_nb_total, ln), cpu_time)
              }
        # then print hits per collection:
        for coll in colls:
            if results_final_nb.has_key(coll['code']) and results_final_nb[coll['code']] > 0:
                out += """<strong><a href="#%(coll)s">%(coll_name)s</a></strong>,
                      <a href="#%(coll)s">%(number)s</a><br>""" % {
                        'coll' : urllib.quote(coll['code']),
                        'coll_name' : coll['name'],
                        'number' : _("<strong>%s</strong> records found") % self.tmpl_nice_number(results_final_nb[coll['code']], ln)
                      }
        out += "</td></tr></tbody></table>"
        return out

    def tmpl_search_no_boolean_hits(self, ln, weburl, nearestterms):
        """No hits found, proposes alternative boolean queries

        Parameters:

          - 'ln' *string* - The language to display

          - 'weburl' *string* - The base URL for the site

          - 'nearestterms' *array* - Parts of the interface to display, in the format:

          - 'nearestterms[nbhits]' *int* - The resulting number of hits

          - 'nearestterms[url_args]' *string* - The search parameters

          - 'nearestterms[p]' *string* - The search terms

        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = _("Boolean query returned no hits. Please combine your search terms differently.")

        out += """<blockquote><table class="nearesttermsbox" cellpadding="0" cellspacing="0" border="0">"""
        for term in nearestterms:
            out += """<tr><td class="nearesttermsboxbody" align="right">%(hits)s</td>
                           <td class="nearesttermsboxbody" width="15">&nbsp;</td>
                           <td class="nearesttermsboxbody" align="left">
                            <a class="nearestterms" href="%(weburl)s/search.py?%(url_args)s">%(p)s</a>
                           </td>
                       </tr>""" % {
                      'hits' : term['nbhits'],
                      'weburl' : weburl,
                      'url_args' : term['url_args'],
                      'p' : term['p']
                    }
        out += """</table></blockquote>"""
        return out

    def tmpl_similar_author_names(self, ln, weburl, authors):
        """No hits found, proposes alternative boolean queries

        Parameters:

          - 'ln' *string* - The language to display

          - 'weburl' *string* - The base URL for the site

          - 'authors' *array* - The authors information, in the format:

          - 'authors[nb]' *int* - The resulting number of hits

          - 'authors[name]' *string* - The author

        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """<a name="googlebox"></a>
                 <table class="googlebox"><tr><th colspan="2" class="googleboxheader">%(similar)s</th></tr>""" % {
                'similar' : _("See also: similar author names")
              }
        for author in authors:
            out += """<tr>
                       <td class="googleboxbody">%(nb)d</td>
                       <td class="googleboxbody">
                          <a class="google" href="%(weburl)s/search.py?p=%(auth_qt)s&amp;f=author">%(auth)s</a>
                       </td></tr>""" % {
                     'nb' : author['nb'],
                     'weburl' : weburl,
                     'auth_qt' : urllib.quote(author['name']),
                     'auth' : author['name'],
                   }
        out += """</table>"""

        return out

    def tmpl_print_record_detailed(self, recID, ln, weburl):
        """Displays a detailed on-the-fly record

        Parameters:

          - 'ln' *string* - The language to display

          - 'weburl' *string* - The base URL for the site

          - 'recID' *int* - The record id
        """
        # okay, need to construct a simple "Detailed record" format of our own:
        out = "<p>&nbsp;"
        # secondly, title:
        titles = get_fieldvalues(recID, "245__a")
        for title in titles:
            out += "<p><p><center><big><strong>%s</strong></big></center>" % title
        # thirdly, authors:
        authors = get_fieldvalues(recID, "100__a") + get_fieldvalues(recID, "700__a")
        if authors:
            out += "<p><p><center>"
            for author in authors:
                out += """<a href="%s/search.py?p=%s&f=author">%s</a> ;""" % (weburl, urllib.quote(author), author)
            out += "</center>"
        # fourthly, date of creation:
        dates = get_fieldvalues(recID, "260__c")
        for date in dates:
            out += "<p><center><small>%s</small></center>" % date
        # fifthly, abstract:
        abstracts = get_fieldvalues(recID, "520__a")
        for abstract in abstracts:
            out += """<p style="margin-left: 15%%; width: 70%%">
                     <small><strong>Abstract:</strong> %s</small></p>""" % abstract
        # fifthly bis, keywords:
        keywords = get_fieldvalues(recID, "6531_a")
        if len(keywords):
            out += """<p style="margin-left: 15%%; width: 70%%">
                     <small><strong>Keyword(s):</strong></small>"""
            for keyword in keywords:
                out += """<small><a href="%s/search.py?p=%s&f=keyword">%s</a> ;</small> """ % (weburl, urllib.quote(keyword), keyword)
        # fifthly bis bis, published in:
        prs_p = get_fieldvalues(recID, "909C4p")
        prs_v = get_fieldvalues(recID, "909C4v")
        prs_y = get_fieldvalues(recID, "909C4y")
        prs_n = get_fieldvalues(recID, "909C4n")
        prs_c = get_fieldvalues(recID, "909C4c")
        for idx in range(0,len(prs_p)):
            out += """<p style="margin-left: 15%%; width: 70%%">
                     <small><strong>Publ. in:</strong> %s"""  % prs_p[idx]
            if prs_v and prs_v[idx]:
                out += """<strong>%s</strong>""" % prs_v[idx]
            if prs_y and prs_y[idx]:
                out += """(%s)""" % prs_y[idx]
            if prs_n and prs_n[idx]:
                out += """, no.%s""" % prs_n[idx]
            if prs_c and prs_c[idx]:
                out += """, p.%s""" % prs_c[idx]
            out += """.</small>"""
        # sixthly, fulltext link:
        urls_z = get_fieldvalues(recID, "8564_z")
        urls_u = get_fieldvalues(recID, "8564_u")
        for idx in range(0,len(urls_u)):
            link_text = "URL"
            try:
                if urls_z[idx]:
                    link_text = urls_z[idx]
            except IndexError:
                pass
            out += """<p style="margin-left: 15%%; width: 70%%">
            <small><strong>%s:</strong> <a href="%s">%s</a></small>""" % (link_text, urls_u[idx], urls_u[idx])
        # print some white space at the end:
        out += "<p><p>"
        return out

    def tmpl_print_record_list_for_similarity_boxen(self, title, score_list, ln=cdslang):
        """Print list of records in the "hs" (HTML Similarity) format for similarity boxes.
           FIXME: bad symbol names again, e.g. SCORE_LIST is *not* a list of scores.  Humph.
        """

        from invenio.search_engine import print_record

        out = '''
        <table><tr><td>
          <table><tr><td class="blocknote">%(title)s</td></tr></table>
        </td>
        <tr><td><table>
        ''' % { 'title': title }

        for recid, score in score_list [:5]:
            out += '''
            <tr><td><font class="rankscoreinfo"><a>(%(score)s)&nbsp;</a></font><small>&nbsp;%(info)s</small></td></tr>''' % {
                'score': score,
                'info' : print_record (recid, format="hs", ln=ln),
                }

        out += """</table></small></td></tr></table> """
        return out
                              

    def tmpl_print_record_brief(self, ln, recID, weburl):
        """Displays a brief record on-the-fly

        Parameters:

          - 'ln' *string* - The language to display

          - 'weburl' *string* - The base URL for the site

          - 'recID' *int* - The record id
        """
        out = ""

        # record 'recID' does not exist in format 'format', so print some default format:
        # firstly, title:
        titles = get_fieldvalues(recID, "245__a")
        # secondly, authors:
        authors = get_fieldvalues(recID, "100__a") + get_fieldvalues(recID, "700__a")
        # thirdly, date of creation:
        dates = get_fieldvalues(recID, "260__c")
        # thirdly bis, report numbers:
        rns = get_fieldvalues(recID, "037__a")
        rns = get_fieldvalues(recID, "088__a")
        # fourthly, beginning of abstract:
        abstracts = get_fieldvalues(recID, "520__a")
        # fifthly, fulltext link:
        urls_z = get_fieldvalues(recID, "8564_z")
        urls_u = get_fieldvalues(recID, "8564_u")

        return self.tmpl_record_body(
                 weburl = weburl,
                 titles = titles,
                 authors = authors,
                 dates = dates,
                 rns = rns,
                 abstracts = abstracts,
                 urls_u = urls_u,
                 urls_z = urls_z,
               )

    def tmpl_print_record_brief_links(self, ln, recID, weburl):
        """Displays links for brief record on-the-fly

        Parameters:

          - 'ln' *string* - The language to display

          - 'weburl' *string* - The base URL for the site

          - 'recID' *int* - The record id
        """
        # load the right message language
        _ = gettext_set_language(ln)

        out = ""
        if cfg_use_aleph_sysnos:
            alephsysnos = get_fieldvalues(recID, "970__a")
            if len(alephsysnos)>0:
                alephsysno = alephsysnos[0]
                out += """<br><span class="moreinfo"><a class="moreinfo" href="%s/search.py?sysno=%s&amp;ln=%s">%s</a></span>""" \
                       % (weburl, alephsysno, ln, _("Detailed record"))
            else:
                out += """<br><span class="moreinfo"><a class="moreinfo" href="%s/search.py?recid=%s&amp;ln=%s">%s</a></span>""" \
                       % (weburl, recID, ln, _("Detailed record"))
        else:
            out += """<br><span class="moreinfo"><a class="moreinfo" href="%s/search.py?recid=%s&amp;ln=%s">%s</a></span>""" \
                   % (weburl, recID, ln, _("Detailed record"))
            out += """<span class="moreinfo"> - <a class="moreinfo" href="%s/search.py?p=recid:%d&amp;rm=wrd&amp;ln=%s">%s</a></span>\n""" % \
                   (weburl, recID, ln, _("Similar records"))

        if cfg_experimental_features:
            out += """<span class="moreinfo"> - <a class="moreinfo" href="%s/search.py?p=recid:%d&amp;rm=cit&amp;ln=%s">%s</a></span>\n""" % (
                weburl, recID, ln, _("Cited by"))
                 
        return out
