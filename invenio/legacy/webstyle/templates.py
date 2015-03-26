# This file is part of Invenio.
# Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014 CERN.
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
WebStyle templates. Customize the look of pages of Invenio
"""
__revision__ = \
    "$Id$"

import time
import cgi
import traceback
import urllib
import sys
import string

from bs4 import BeautifulSoup
from invenio.ext.template import render_template_to_string
from invenio.config import \
     CFG_SITE_RECORD, \
     CFG_SITE_LANG, \
     CFG_SITE_NAME, \
     CFG_SITE_NAME_INTL, \
     CFG_SITE_SUPPORT_EMAIL, \
     CFG_SITE_SECURE_URL, \
     CFG_BASE_URL, \
     CFG_SITE_URL, \
     CFG_VERSION, \
     CFG_WEBSTYLE_TEMPLATE_SKIN, \
     CFG_INSPIRE_SITE, \
     CFG_WEBLINKBACK_TRACKBACK_ENABLED

from invenio.base.i18n import gettext_set_language, language_list_long, is_language_rtl
from invenio.utils.url import make_canonical_urlargd, create_html_link, \
                             get_canonical_and_alternates_urls
from invenio.utils.date import convert_datecvs_to_datestruct, \
                              convert_datestruct_to_dategui
from invenio.modules.formatter import format_record
from invenio.utils.html import get_mathjax_header
import invenio.legacy.template
websearch_templates = invenio.legacy.template.load('websearch')


class Template:

    def tmpl_navtrailbox_body(self, ln, title, previous_links, separator,
                              prolog, epilog):
        """Bootstrap friendly-Create navigation trail box body

           Parameters:

          - 'ln' *string* - The language to display

          - 'title' *string* - page title;

          - 'previous_links' *string* - the trail content from site title until current page (both ends exclusive)

          - 'prolog' *string* - HTML code to prefix the navtrail item with

          - 'epilog' *string* - HTML code to suffix the navtrail item with

          - 'separator' *string* - HTML code that separates two navtrail items

           Output:

          - text containing the navtrail

           Note: returns empty string for Home page. (guessed by title).
        """

        # load the right message language
        _ = gettext_set_language(ln)

        if title == CFG_SITE_NAME_INTL.get(ln, CFG_SITE_NAME):
            return ""

        # Breadcrumbs
        # breadcrumb objects should provide properties 'text' and 'url'

        # First element
        breadcrumbs = [dict(text=_("Home"), url=CFG_SITE_URL), ]

        # Decode previous elements
        if previous_links:
            soup = BeautifulSoup(previous_links)
            for link in soup.find_all('a'):
                breadcrumbs.append(dict(
                    text=unicode(' '.join(link.contents)),
                    url=link.get('href')))

        # Add head
        if title:
            breadcrumbs.append(dict(text=title, url='#'))

        return render_template_to_string("breadcrumbs.html",
                                         breadcrumbs=breadcrumbs).encode('utf8')

    def tmpl_page(self, req, **kwargs):
        """Creates a complete page

           Parameters:

          - 'ln' *string* - The language to display

          - 'description' *string* - description goes to the metadata in the header of the HTML page,
                                     not yet escaped for HTML

          - 'keywords' *string* - keywords goes to the metadata in the header of the HTML page,
                                  not yet escaped for HTML

          - 'userinfobox' *string* - the HTML code for the user information box

          - 'useractivities_menu' *string* - the HTML code for the user activities menu

          - 'adminactivities_menu' *string* - the HTML code for the admin activities menu

          - 'navtrailbox' *string* - the HTML code for the navigation trail box

          - 'pageheaderadd' *string* - additional page header HTML code

          - 'boxlefttop' *string* - left-top box HTML code

          - 'boxlefttopadd' *string* - additional left-top box HTML code

          - 'boxleftbottom' *string* - left-bottom box HTML code

          - 'boxleftbottomadd' *string* - additional left-bottom box HTML code

          - 'boxrighttop' *string* - right-top box HTML code

          - 'boxrighttopadd' *string* - additional right-top box HTML code

          - 'boxrightbottom' *string* - right-bottom box HTML code

          - 'boxrightbottomadd' *string* - additional right-bottom box HTML code

          - 'title' *string* - the title of the page, not yet escaped for HTML

          - 'titleprologue' *string* - what to print before page title

          - 'titleepilogue' *string* - what to print after page title

          - 'body' *string* - the body of the page

          - 'lastupdated' *string* - when the page was last updated

          - 'uid' *int* - user ID

          - 'pagefooteradd' *string* - additional page footer HTML code

          - 'secure_page_p' *int* (0 or 1) - are we to use HTTPS friendly page elements or not?

          - 'navmenuid' *string* - the id of the navigation item to highlight for this page

          - 'metaheaderadd' *string* - list of further tags to add to the <HEAD></HEAD> part of the page

          - 'rssurl' *string* - the url of the RSS feed for this page

          - 'show_title_p' *int* (0 or 1) - do we display the page title in the body of the page?

          - 'body_css_classes' *list* - list of classes to add to the body tag

          - 'show_header' *boolean* - tells whether page header should be displayed or not

          - 'show_footer' *boolean* - tells whether page footer should be displayed or not

           Output:

          - HTML code of the page
        """
        ctx = dict(ln=CFG_SITE_LANG, description="",
                   keywords="", userinfobox="", useractivities_menu="",
                   adminactivities_menu="", navtrailbox="",
                   pageheaderadd="", boxlefttop="", boxlefttopadd="",
                   boxleftbottom="", boxleftbottomadd="",
                   boxrighttop="", boxrighttopadd="",
                   boxrightbottom="", boxrightbottomadd="",
                   titleprologue="", title="", titleepilogue="",
                   body="", lastupdated=None, pagefooteradd="", uid=0,
                   secure_page_p=0, navmenuid="", metaheaderadd="",
                   rssurl=CFG_SITE_URL+"/rss",
                   show_title_p=True, body_css_classes=None,
                   show_header=True, show_footer=True)
        ctx.update(kwargs)
        return render_template_to_string("legacy_page.html", **ctx).encode('utf8')

    def tmpl_pageheader(self, req, **kwargs):
        """Creates a page header

           Parameters:

          - 'ln' *string* - The language to display

          - 'headertitle' *string* - the title of the HTML page, not yet escaped for HTML

          - 'description' *string* - description goes to the metadata in the header of the HTML page,
                                     not yet escaped for HTML

          - 'keywords' *string* - keywords goes to the metadata in the header of the HTML page,
                                  not yet escaped for HTML

          - 'userinfobox' *string* - the HTML code for the user information box

          - 'useractivities_menu' *string* - the HTML code for the user activities menu

          - 'adminactivities_menu' *string* - the HTML code for the admin activities menu

          - 'navtrailbox' *string* - the HTML code for the navigation trail box

          - 'pageheaderadd' *string* - additional page header HTML code

          - 'uid' *int* - user ID

          - 'secure_page_p' *int* (0 or 1) - are we to use HTTPS friendly page elements or not?

          - 'navmenuid' *string* - the id of the navigation item to highlight for this page

          - 'metaheaderadd' *string* - list of further tags to add to the <HEAD></HEAD> part of the page

          - 'rssurl' *string* - the url of the RSS feed for this page

          - 'body_css_classes' *list* - list of classes to add to the body tag

           Output:

          - HTML code of the page headers
        """

        ctx = dict(ln=CFG_SITE_LANG, headertitle="",
                   description="", keywords="", userinfobox="",
                   useractivities_menu="", adminactivities_menu="",
                   navtrailbox="", pageheaderadd="", uid=0,
                   secure_page_p=0, navmenuid="admin", metaheaderadd="",
                   rssurl=CFG_SITE_URL+"/rss", body_css_classes=None)
        ctx.update(kwargs)
        if ctx['body_css_classes'] is None:
            ctx['body_css_classes'] = [ctx.get('navmenuid', '')]
        else:
            ctx['body_css_classes'].append([ctx.get('navmenuid', '')])

        return render_template_to_string(
            "legacy_page.html",
            no_pagebody=True,
            no_pagefooter=True,
            **ctx
        ).encode('utf8')

    def tmpl_pagefooter(self, req, **kwargs):
        """Creates a page footer

           Parameters:

          - 'ln' *string* - The language to display

          - 'lastupdated' *string* - when the page was last updated

          - 'pagefooteradd' *string* - additional page footer HTML code

           Output:

          - HTML code of the page headers
        """
        ctx = dict(ln=CFG_SITE_LANG, lastupdated=None, pagefooteradd=None)
        ctx.update(kwargs)
        lastupdated = ctx.get('lastupdated')
        if lastupdated and lastupdated != '$Date$':
            if lastupdated.startswith("$Date: ") or lastupdated.startswith("$Id: "):
                ctx['lastupdated'] = convert_datecvs_to_datestruct(lastupdated)

        return render_template_to_string(
            "legacy_page.html",
            no_pagebody=True,
            no_pageheader=True,
            **ctx
        ).encode('utf8')

    def tmpl_language_selection_box(self, req, language=CFG_SITE_LANG):
        """Take URLARGS and LANGUAGE and return textual language
           selection box for the given page.

           Parameters:

          - 'req' - The mod_python request object

          - 'language' *string* - The selected language

        """

        # load the right message language
        _ = gettext_set_language(language)

        # Work on a copy in order not to bork the arguments of the caller
        argd = {}
        if req and req.args:
            argd.update(cgi.parse_qs(req.args))

        parts = []

        for (lang, lang_namelong) in language_list_long():
            if lang == language:
                parts.append('<span class="langinfo">%s</span>' % lang_namelong)
            else:
                # Update the 'ln' argument in the initial request
                argd['ln'] = lang
                if req and req.uri:
                    args = urllib.quote(req.uri, '/:?') + make_canonical_urlargd(argd, {})
                else:
                    args = ""
                parts.append(create_html_link(args,
                                              {}, lang_namelong,
                                              {'class': "langinfo"}))
        if len(parts) > 1:
            return _("This site is also available in the following languages:") + \
                 "<br />" + ' &nbsp;'.join(parts)
        else:
            ## There is only one (or zero?) languages configured,
            ## so there so need to display language alternatives.
            return ""

    def tmpl_error_box(self, ln, title, verbose, req, errors):
        """Produces an error box.

           Parameters:

          - 'title' *string* - The title of the error box

          - 'ln' *string* - The selected language

          - 'verbose' *bool* - If lots of information should be displayed

          - 'req' *object* - the request object

          - 'errors' list of tuples (error_code, error_message)
        """

        # load the right message language
        _ = gettext_set_language(ln)
        info_not_available = _("N/A")

        if title is None:
            if errors:
                title = _("Error") + ': %s' % errors[0][1]
            else:
                title = _("Internal Error")

        browser_s = _("Browser")
        if req:
            try:
                if 'User-Agent' in req.headers_in:
                    browser_s += ': ' + req.headers_in['User-Agent']
                else:
                    browser_s += ': ' + info_not_available
                host_s = req.hostname
                page_s = req.unparsed_uri
                client_s = req.remote_ip
            except: # FIXME: bad except
                browser_s += ': ' + info_not_available
                host_s = page_s = client_s = info_not_available
        else:
            browser_s += ': ' + info_not_available
            host_s = page_s = client_s = info_not_available

        error_s = ''
        sys_error_s = ''
        traceback_s = ''
        if verbose >= 1:
            if sys.exc_info()[0]:
                sys_error_s = '\n' + _("System Error") + ': %s %s\n' % \
                              (sys.exc_info()[0], sys.exc_info()[1])
            if errors:
                errs = ''
                for error_tuple in errors:
                    try:
                        errs += "%s%s : %s\n " % (' '*6, error_tuple[0],
                                                  error_tuple[1])
                    except:
                        errs += "%s%s\n" % (' '*6, error_tuple)
                errs = errs[6:-2] # get rid of trainling ','
                error_s = _("Error") + ': %s")' % errs + "\n"
            else:
                error_s = _("Error") + ': ' + info_not_available
        if verbose >= 9:
            traceback_s = '\n' + _("Traceback") + ': \n%s' % \
                          string.join(traceback.format_tb(sys.exc_info()[2]),
                                      "\n")
        out = """
              <table class="errorbox">
                <thead>
                  <tr>
                    <th class="errorboxheader">
                      <p> %(title)s %(sys1)s %(sys2)s</p>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td class="errorboxbody">
                      <p>%(contact)s</p>
                        <blockquote><pre>
URI: http://%(host)s%(page)s
%(time_label)s: %(time)s
%(browser)s
%(client_label)s: %(client)s
%(error)s%(sys_error)s%(traceback)s
</pre></blockquote>
                    </td>
                  </tr>
                  <tr>
                    <td>
                      <form action="%(siteurl)s/error/send" method="post">
                        %(send_error_label)s
                        <input class="adminbutton" type="submit" value="%(send_label)s" />
                        <input type="hidden" name="header" value="%(title)s %(sys1)s %(sys2)s" />
                        <input type="hidden" name="url" value="URI: http://%(host)s%(page)s" />
                        <input type="hidden" name="time" value="Time: %(time)s" />
                        <input type="hidden" name="browser" value="%(browser)s" />
                        <input type="hidden" name="client" value="Client: %(client)s" />
                        <input type="hidden" name="error" value="%(error)s" />
                        <input type="hidden" name="sys_error" value="%(sys_error)s" />
                        <input type="hidden" name="traceback" value="%(traceback)s" />
                        <input type="hidden" name="referer" value="%(referer)s" />
                      </form>
                    </td>
                  </tr>
                </tbody>
              </table>
              """ % {
                'title'     : cgi.escape(title).replace('"', '&quot;'),
                'time_label': _("Time"),
                'client_label': _("Client"),
                'send_error_label': \
                       _("Please send an error report to the administrator."),
                'send_label': _("Send error report"),
                'sys1'  : cgi.escape(str((sys.exc_info()[0] or ''))).replace('"', '&quot;'),
                'sys2'  : cgi.escape(str((sys.exc_info()[1] or ''))).replace('"', '&quot;'),
                'contact'   : \
                    _("Please contact %(x_name)s quoting the following information:",
                      x_name=('<a href="mailto:' + urllib.quote(CFG_SITE_SUPPORT_EMAIL) +'">' + CFG_SITE_SUPPORT_EMAIL + '</a>')),
                'host'      : cgi.escape(host_s),
                'page'      : cgi.escape(page_s),
                'time'      : time.strftime("%d/%b/%Y:%H:%M:%S %z"),
                'browser'   : cgi.escape(browser_s).replace('"', '&quot;'),
                'client'    : cgi.escape(client_s).replace('"', '&quot;'),
                'error'     : cgi.escape(error_s).replace('"', '&quot;'),
                'traceback' : cgi.escape(traceback_s).replace('"', '&quot;'),
                'sys_error' : cgi.escape(sys_error_s).replace('"', '&quot;'),
                'siteurl'    : CFG_BASE_URL,
                'referer'   : page_s!=info_not_available and \
                                 ("http://" + host_s + page_s) or \
                                 info_not_available
              }
        return out

    def detailed_record_container_top(self, recid, tabs, ln=CFG_SITE_LANG,
                                      show_similar_rec_p=True,
                                      creationdate=None,
                                      modificationdate=None, show_short_rec_p=True,
                                      citationnum=-1, referencenum=-1, discussionnum=-1,
                                      include_jquery = False, include_mathjax = False):
        """Prints the box displayed in detailed records pages, with tabs at the top.

        Returns content as it is if the number of tabs for this record
        is smaller than 2

           Parameters:

        @param recid: int - the id of the displayed record
        @param tabs: ** - the tabs displayed at the top of the box.
        @param ln: *string* - the language of the page in which the box is displayed
        @param show_similar_rec_p: *bool* print 'similar records' link in the box
        @param creationdate: *string* - the creation date of the displayed record
        @param modificationdate: *string* - the last modification date of the displayed record
        @param show_short_rec_p: *boolean* - prints a very short version of the record as reminder.
        @param citationnum: show (this) number of citations in the citations tab
        @param referencenum: show (this) number of references in the references tab
        @param discussionnum: show (this) number of comments/reviews in the discussion tab
        """
        from invenio.modules.collections.cache import get_all_restricted_recids
        from invenio.modules.collections.cache import is_record_in_any_collection

        # load the right message language
        _ = gettext_set_language(ln)

        # Prepare restriction flag
        restriction_flag = ''
        if recid in get_all_restricted_recids():
            restriction_flag = '<div class="restrictedflag"><span>%s</span></div>' % _("Restricted")
        elif not is_record_in_any_collection(recid, recreate_cache_if_needed=False):
            restriction_flag = '<div class="restrictedflag restrictedflag-pending"><span>%s</span></div>' % _("Restricted (Processing Record)")

        # If no tabs, returns nothing (excepted if restricted)
        if len(tabs) <= 1:
            return restriction_flag

        # Build the tabs at the top of the page
        out_tabs = ''
        if len(tabs) > 1:
            first_tab = True
            for (label, url, selected, enabled) in tabs:
                addnum = ""
                if (citationnum > -1) and url.count("/citation") == 1:
                    addnum = "(" + str(citationnum) + ")"
                if (referencenum > -1) and url.count("/references") == 1:
                    addnum = "(" + str(referencenum) + ")"
                if (discussionnum > -1) and url.count("/comments") == 1:
                    addnum = "(" + str(discussionnum) + ")"

                css_class = []
                if selected:
                    css_class.append('on')
                if first_tab:
                    css_class.append('first')
                    first_tab = False
                if not enabled:
                    css_class.append('disabled')
                css_class = ' class="%s"' % ' '.join(css_class)
                if not enabled:
                    out_tabs += '<li%(class)s><a>%(label)s %(addnum)s</a></li>' % \
                                {'class':css_class,
                                 'label':label,
                                 'addnum':addnum}
                else:
                    out_tabs += '<li%(class)s><a href="%(url)s">%(label)s %(addnum)s </a></li>' % \
                                {'class':css_class,
                                 'url':url,
                                 'label':label,
                                 'addnum':addnum}
        if out_tabs != '':
            out_tabs = '''        <div class="detailedrecordtabs">
            <div>
                <ul class="detailedrecordtabs">%s</ul>
            <div id="tabsSpacer" style="clear:both;height:0px">&nbsp;</div></div>
        </div>''' % out_tabs


        # Add the clip icon and the brief record reminder if necessary
        record_brief = ''
        if show_short_rec_p:
            record_brief = format_record(recID=recid, of='hs', ln=ln)
            record_brief = '''<div id="detailedrecordshortreminder">
                             <div id="clip">&nbsp;</div>
                             <div id="HB">
                                 %(record_brief)s
                             </div>
                         </div>
                         <div style="clear:both;height:1px">&nbsp;</div>
                         ''' % {'record_brief': record_brief}

        additional_scripts = ""
        if include_jquery:
            additional_scripts += """<script type="text/javascript" src="%s/js/jquery.min.js">' \
            '</script>\n""" % (CFG_BASE_URL, )
        if include_mathjax:

            additional_scripts += get_mathjax_header()


        # Print the content
        out = """
        %(additional_scripts)s<div class="detailedrecordbox">
        %(tabs)s
        <div class="detailedrecordboxcontent">
            <div class="top-left-folded"></div>
            <div class="top-right-folded"></div>
            <div class="inside">
                <!--<div style="height:0.1em;">&nbsp;</div>
                <p class="notopgap">&nbsp;</p>-->
                %(record_brief)s
                """ % {'additional_scripts': additional_scripts,
                       'tabs':out_tabs,
                       'record_brief':record_brief}

        out = restriction_flag + out
        return out

    def detailed_record_container_bottom(self, recid, tabs, ln=CFG_SITE_LANG,
                                         show_similar_rec_p=True,
                                         creationdate=None,
                                         modificationdate=None, show_short_rec_p=True):
        """Prints the box displayed in detailed records pages, with tabs at the top.

        Returns content as it is if the number of tabs for this record
        is smaller than 2

           Parameters:

         - recid *int* - the id of the displayed record
         - tabs ** - the tabs displayed at the top of the box.
         - ln *string* - the language of the page in which the box is displayed
         - show_similar_rec_p *bool* print 'similar records' link in the box
         - creationdate *string* - the creation date of the displayed record
         - modificationdate *string* - the last modification date of the displayed record
         - show_short_rec_p *boolean* - prints a very short version of the record as reminder.
        """
        # If no tabs, returns nothing
        if len(tabs) <= 1:
            return ''

        # load the right message language
        _ = gettext_set_language(ln)

        similar = ""

        if show_similar_rec_p and not CFG_INSPIRE_SITE:
            similar = create_html_link(
                websearch_templates.build_search_url(p='recid:%d' % \
                                                     recid,
                                                     rm='wrd',
                                                     ln=ln),
                {}, _("Similar records"),{'class': "moreinfo"})

        out = """
            <div class="bottom-left-folded">%(dates)s</div>
            <div class="bottom-right-folded" style="text-align:right;padding-bottom:2px;">
                <span class="moreinfo" style="margin-right:10px;">%(similar)s</span></div>
          </div>
      </div>
    </div>
    <br/>
    """ % {'similar' : similar,
           'dates' : creationdate and '<div class="recordlastmodifiedbox" style="position:relative;margin-left:1px">&nbsp;%(dates)s</div>' % {
                'dates': _("Record created %(x_date_creation)s, last modified %(x_date_modification)s",
                           x_date_creation=creationdate,
                           x_date_modification=modificationdate),
                } or ''
           }

        return out


    def detailed_record_mini_panel(self, recid, ln=CFG_SITE_LANG,
                                   format='hd',
                                   files='',
                                   reviews='',
                                   actions=''):
        """Displays the actions dock at the bottom of the detailed record
           pages.

           Parameters:

         - recid *int* - the id of the displayed record
         - ln *string* - interface language code
         - format *string* - the format used to display the record
         - files *string* - the small panel representing the attached files
         - reviews *string* - the small panel representing the reviews
         - actions *string* - the small panel representing the possible user's action
        """
        # load the right message language
        _ = gettext_set_language(ln)

        out = """
        <br />
<div class="detailedrecordminipanel">
<div class="top-left"></div><div class="top-right"></div>
                <div class="inside">

        <div id="detailedrecordminipanelfile" style="width:33%%;float:left;text-align:center;margin-top:0">
             %(files)s
        </div>
        <div id="detailedrecordminipanelreview" style="width:30%%;float:left;text-align:center">
             %(reviews)s
        </div>

        <div id="detailedrecordminipanelactions" style="width:36%%;float:right;text-align:right;">
             %(actions)s
        </div>
        <div style="clear:both;margin-bottom: 0;"></div>
        </div>
        <div class="bottom-left"></div><div class="bottom-right"></div>
        </div>
        """ % {
        'siteurl': CFG_BASE_URL,
        'ln':ln,
        'recid':recid,
        'files': files,
        'reviews':reviews,
        'actions': actions,
        }
        return out

    def tmpl_error_page(self, ln=CFG_SITE_LANG, status="", admin_was_alerted=True):
        """
        Display an error page.

        - status *string* - the HTTP status.
        """
        _ = gettext_set_language(ln)
        out = """
        <p>%(message)s</p>
        <p>%(alerted)s</p>
        <p>%(doubts)s</p>""" % {
            'status' : status,
            'message' : _("The server encountered an error while dealing with your request."),
            'alerted' : admin_was_alerted and _("The system administrators have been alerted.") or '',
            'doubts' : _("In case of doubt, please contact %(x_admin_email)s.",
                         x_admin_email='<a href="mailto:%(admin)s">%(admin)s</a>' % {'admin' : CFG_SITE_SUPPORT_EMAIL})
        }
        return out

    def tmpl_warning_message(self, ln, msg):
        """
        Produces a warning message for the specified text

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'msg' *string* - The message to display
        """

        # load the right message language
        _ = gettext_set_language(ln)

        return """<center><font color="red">%s</font></center>""" % msg

    def tmpl_write_warning(self, msg, type='', prologue='', epilogue=''):
        """
        Returns formatted warning message.

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
