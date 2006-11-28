## $Id$
## CDS Invenio WebStyle templates.

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

__revision__ = \
    "$Id$"

import time
import cgi
import traceback
import urllib
import sys
import string

from invenio.config import \
     cdslang, \
     cdsnameintl, \
     supportemail, \
     sweburl, \
     weburl, \
     version
from invenio.messages import gettext_set_language, language_list_long
from invenio.urlutils import make_canonical_urlargd, create_html_link
from invenio.dateutils import convert_datecvs_to_datestruct, \
                              convert_datestruct_to_dategui

class Template:

    def tmpl_navtrailbox_body(self, ln, title, previous_links,
                              separator, prolog, epilog):
        """Create navigation trail box body

           Parameters:

          - 'weburl' *string* - The base URL for the site

          - 'ln' *string* - The language to display

          - 'title' *string* - page title;

          - 'previous_links' *string* - the trail content from site title until current page (both ends exlusive)

          - 'prolog' *string* - HTML code to prefix the navtrail item with

          - 'epilog' *string* - HTML code to suffix the navtrail item with

          - 'separator' *string* - HTML code that separates two navtrail items

           Output:

          - text containing the navtrail
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = ""
        if title != cdsnameintl[ln]:
            out += create_html_link(weburl, {'ln': ln}, 
                                    _("Home"), {'class': 'navtrail'})
        if previous_links:
            if out:
                out += separator
            out += previous_links
        if title:
            if out:
                out += separator
            if title == cdsnameintl[ln]: # hide site name, print Home instead
                out += _("Home")
            else:
                out += title
        return prolog + out + epilog

    def tmpl_page(self, req=None, ln=cdslang, description="",
                  keywords="", userinfobox="", navtrailbox="",
                  pageheaderadd="", boxlefttop="", boxlefttopadd="",
                  boxleftbottom="", boxleftbottomadd="",
                  boxrighttop="", boxrighttopadd="",
                  boxrightbottom="", boxrightbottomadd="",
                  titleprologue="", title="", titleepilogue="",
                  body="", lastupdated=None, pagefooteradd="", uid=0,
                  secure_page_p=0):
        
        """Creates a complete page

           Parameters:

          - 'weburl' *string* - The base URL for the site

          - 'ln' *string* - The language to display

          - 'sitename' *string* - the first part of the page HTML title

          - 'headertitle' *string* - the second part of the page HTML title

          - 'supportemail' *string* - email of the support team

          - 'description' *string* - description goes to the metadata in the header of the HTML page

          - 'keywords' *string* - keywords goes to the metadata in the header of the HTML page

          - 'userinfobox' *string* - the HTML code for the user information box

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

          - 'title' *string* - the title of the page

          - 'body' *string* - the body of the page

          - 'version' *string* - the version number of CDS Invenio

          - 'lastupdated' *string* - when the page was last updated

          - 'languagebox' *string* - the HTML code for the language box

          - 'pagefooteradd' *string* - additional page footer HTML code

          - 'secure_page_p' *int* (0 or 1) - are we to use HTTPS friendly page elements or not?

           Output:

          - HTML code of the page
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = self.tmpl_pageheader(req, 
                                   ln = ln,
                                   headertitle = title,
                                   description = description,
                                   keywords = keywords,
                                   userinfobox = userinfobox,
                                   navtrailbox = navtrailbox,
                                   pageheaderadd = pageheaderadd,
                                   secure_page_p = secure_page_p
                                   ) + """
<div class="pagebody">
  <div class="pagebodystripeleft">
    <div class="pageboxlefttop">%(boxlefttop)s</div>
    <div class="pageboxlefttopadd">%(boxlefttopadd)s</div>
    <div class="pageboxleftbottomadd">%(boxleftbottomadd)s</div>
    <div class="pageboxleftbottom">%(boxleftbottom)s</div>
  </div>
  <div class="pagebodystriperight">
    <div class="pageboxrighttop">%(boxrighttop)s</div>
    <div class="pageboxrighttopadd">%(boxrighttopadd)s</div>
    <div class="pageboxrightbottomadd">%(boxrightbottomadd)s</div>
    <div class="pageboxrightbottom">%(boxrightbottom)s</div>
  </div>
  <div class="pagebodystripemiddle">
    %(titleprologue)s
    <h1 class="headline">%(title)s</h1>
    %(titleepilogue)s
    %(body)s
  </div>
</div>
""" % {
  'boxlefttop' : boxlefttop,
  'boxlefttopadd' : boxlefttopadd,

  'boxleftbottom' : boxleftbottom,
  'boxleftbottomadd' : boxleftbottomadd,

  'boxrighttop' : boxrighttop,
  'boxrighttopadd' : boxrighttopadd,

  'boxrightbottom' : boxrightbottom,
  'boxrightbottomadd' : boxrightbottomadd,

  'titleprologue' : titleprologue,
  'title' : title,
  'titleepilogue' : titleepilogue,
  
  'body' : body,

  } + self.tmpl_pagefooter(req, ln = ln,
                           lastupdated = lastupdated,
                           pagefooteradd = pagefooteradd)
        return out

    def tmpl_pageheader(self, req, ln=cdslang, headertitle="",
                        description="", keywords="", userinfobox="",
                        navtrailbox="", pageheaderadd="", uid=0,
                        secure_page_p=0):

        """Creates a page header

           Parameters:

          - 'weburl' *string* - The base URL for the site

          - 'ln' *string* - The language to display

          - 'sitename' *string* - the first part of the page HTML title

          - 'headertitle' *string* - the second part of the page HTML title

          - 'supportemail' *string* - email of the support team

          - 'description' *string* - description goes to the metadata in the header of the HTML page

          - 'keywords' *string* - keywords goes to the metadata in the header of the HTML page

          - 'userinfobox' *string* - the HTML code for the user information box

          - 'navtrailbox' *string* - the HTML code for the navigation trail box

          - 'pageheaderadd' *string* - additional page header HTML code

          - 'languagebox' *string* - the HTML code for the language box

          - 'secure_page_p' *int* (0 or 1) - are we to use HTTPS friendly page elements or not?

           Output:

          - HTML code of the page headers
        """

        # load the right message language
        _ = gettext_set_language(ln)

        if headertitle == cdsnameintl[ln]:
            headertitle = _("Home")

        out = """\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
 <title>%(sitename)s: %(headertitle)s</title>
 <link rev="made" href="mailto:%(supportemail)s">
 <link rel="stylesheet" href="%(cssurl)s/img/cds.css">
 <link rel="alternate" type="application/rss+xml" title="%(sitename)s RSS" href="%(weburl)s/rss">
 <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
 <meta name="description" content="%(description)s">
 <meta name="keywords" content="%(keywords)s">
</head>
<body>
<div class="pageheader">
<!-- replaced page header -->
<div style="background-image: url(%(weburl)s/img/header_background.gif);">
<table class="headerbox">
 <tr>
  <td rowspan="2" class="headerboxbodylogo">
   %(sitename)s
  </td>
  <td align="right" class="userinfoboxbody">
   %(userinfobox)s
  </td>
 </tr>
 <tr>
  <td class="headerboxbody" valign="bottom" align="left">
   <table class="headermodulebox">
     <tr>
       <td class="headermoduleboxbodyblank">
             &nbsp;
       </td>
       <td class="headermoduleboxbodyblank">
             &nbsp;
       </td>
       <td class="headermoduleboxbody">
             <a class="header" href="%(weburl)s/?ln=%(ln)s">%(msg_search)s</a>
       </td>
       <td class="headermoduleboxbodyblank">
             &nbsp;
       </td>
       <td class="headermoduleboxbody">
             <a class="header" href="%(weburl)s/submit?ln=%(ln)s">%(msg_submit)s</a>
       </td>
       <td class="headermoduleboxbodyblank">
             &nbsp;
       </td>
       <td class="headermoduleboxbody">
             <a class="header" href="%(sweburl)s/youraccount/display?ln=%(ln)s">%(msg_personalize)s</a>
       </td>
       <td class="headermoduleboxbodyblank">
             &nbsp;
       </td>
       <td class="headermoduleboxbody">
             <a class="header" href="%(weburl)s/help/index.%(ln)s.html">%(msg_help)s</a>
       </td>
       <td class="headermoduleboxbodyblank">
             &nbsp;
       </td>
     </tr>
   </table>
  </td>
 </tr>
</table>
</div>
<table class="navtrailbox">
 <tr>
  <td class="navtrailboxbody">
   %(navtrailbox)s
  </td>
 </tr>
</table>
<!-- end replaced page header -->
%(pageheaderadd)s
</div>
        """ % {
          'weburl' : weburl,
          'sweburl' : sweburl,
          'cssurl' : secure_page_p and sweburl or weburl,
          'ln' : ln,

          'sitename' : cdsnameintl[ln],
          'headertitle' : headertitle,
          'supportemail' : supportemail,

          'description' : description,
          'keywords' : keywords,

          'userinfobox' : userinfobox,
          'navtrailbox' : navtrailbox,

          'pageheaderadd' : pageheaderadd,

          'msg_search' : _("Search"),
          'msg_submit' : _("Submit"),
          'msg_personalize' : _("Personalize"),
          'msg_help' : _("Help"),
          'languagebox' : self.tmpl_language_selection_box(req, ln),

        }
        return out

    def tmpl_pagefooter(self, req=None, ln=cdslang, lastupdated=None,
                        pagefooteradd=""):
        """Creates a page footer

           Parameters:

          - 'weburl' *string* - The base URL for the site

          - 'ln' *string* - The language to display

          - 'sitename' *string* - the first part of the page HTML title

          - 'supportemail' *string* - email of the support team

          - 'version' *string* - the version number of CDS Invenio

          - 'lastupdated' *string* - when the page was last updated

          - 'languagebox' *string* - the HTML code for the language box

          - 'pagefooteradd' *string* - additional page footer HTML code

           Output:

          - HTML code of the page headers
        """

        # load the right message language
        _ = gettext_set_language(ln)

        if lastupdated:
            if lastupdated.startswith("$Date: "):
                lastupdated = convert_datestruct_to_dategui(\
                                 convert_datecvs_to_datestruct(lastupdated),
                                 ln=ln)
            msg_lastupdated = _("Last updated") + ": " + lastupdated
        else:
            msg_lastupdated = ""

        out = """
<div class="pagefooter">
%(pagefooteradd)s
<!-- replaced page footer -->
 <div class="pagefooterstripeleft">
  %(sitename)s&nbsp;::&nbsp;<a class="footer" href="%(weburl)s/?ln=%(ln)s">%(msg_search)s</a>&nbsp;::&nbsp;<a class="footer" href="%(weburl)s/submit?ln=%(ln)s">%(msg_submit)s</a>&nbsp;::&nbsp;<a class="footer" href="%(sweburl)s/youraccount/display?ln=%(ln)s">%(msg_personalize)s</a>&nbsp;::&nbsp;<a class="footer" href="%(weburl)s/help/index.%(ln)s.html">%(msg_help)s</a>
  <br />
  %(msg_poweredby)s <a class="footer" href="http://cdsware.cern.ch/">CDS Invenio</a> v%(version)s
  <br />
  %(msg_maintainedby)s <a class="footer" href="mailto:%(supportemail)s">%(supportemail)s</a>
  <br />
  %(msg_lastupdated)s
 </div>
 <div class="pagefooterstriperight">
  %(languagebox)s
 </div>
<!-- replaced page footer -->
</div>
</body>
</html>
        """ % {
          'weburl' : weburl,
          'sweburl' : sweburl,
          'ln' : ln,

          'sitename' : cdsnameintl[ln],
          'supportemail' : supportemail,

          'msg_search' : _("Search"),
          'msg_submit' : _("Submit"),
          'msg_personalize' : _("Personalize"),
          'msg_help' : _("Help"),

          'msg_poweredby' : _("Powered by"),
          'msg_maintainedby' : _("Maintained by"),

          'msg_lastupdated' : msg_lastupdated,
          'languagebox' : self.tmpl_language_selection_box(req, ln),
          'version' : version,

          'pagefooteradd' : pagefooteradd,

        }
        return out

    def tmpl_language_selection_box(self, req, language=cdslang):
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
                    args = req.uri + make_canonical_urlargd(argd, {})
                else:
                    args = ""                
                parts.append(create_html_link(args,
                                              {}, lang_namelong,
                                              {'class': "langinfo"}))

        return _("This site is also available in the following languages:") + \
                 "<br />" + ' &nbsp;'.join(parts)

    def tmpl_error_box(self, ln, title, verbose, req, supportemail, errors):
        """Produces an error box.

           Parameters:

          - 'title' *string* - The title of the error box

          - 'ln' *string* - The selected language

          - 'verbose' *bool* - If lots of information should be displayed

          - 'req' *object* - the request object

          - 'supportemail' *string* - the supportemail for this installation 
            
          - 'errors' list of tuples (error_code, error_message)
    
          - #! todo
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
                if req.headers_in.has_key('User-Agent'):
                    browser_s += ': ' + req.headers_in['User-Agent']
                else:
                    browser_s += ': ' + info_not_available
                host_s = req.hostname
                page_s = req.unparsed_uri
                client_s = req.connection.remote_ip 
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
                sys_error_s = _("System Error") + ': %s %s\n' % \
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
            traceback_s = _("Traceback") + ': \n%s' % \
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
                      <form action="%(weburl)s/error/send" method="POST">
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
                'title'     : title,
                'time_label': _("Time"),
                'client_label': _("Client"),
                'send_error_label': \
                       _("Please send an error report to the Administrator."),
                'send_label': _("Send error report"),
                'sys1'      : sys.exc_info()[0] or '',
                'sys2'      : sys.exc_info()[1] or '',
                'contact'   : \
                   _("Please contact %s quoting the following information:") % \
                     '<a href="mailto:' + urllib.quote(supportemail) +'">' + \
                       supportemail + '</a>',
                'host'      : host_s,
                'page'      : page_s,
                'time'      : time.strftime("%d/%b/%Y:%H:%M:%S %z"),
                'browser'   : browser_s,
                'client'    : client_s,
                'error'     : error_s,
                'traceback' : traceback_s,
                'sys_error' : sys_error_s,
                'weburl'    : weburl,
                'referer'   : page_s!=info_not_available and \
                                 ("http://" + host_s + page_s) or \
                                 info_not_available
              }
 
        return out
