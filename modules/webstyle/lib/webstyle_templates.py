## $Id$
## CDSware WebStyle templates.

## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002, 2003, 2004, 2005 CERN.
##
## The CDSware is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## The CDSware is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDSware; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import urllib
import time
import cgi
import gettext
import traceback
import sre
import urllib
import sys

from config import *
from messages import gettext_set_language, language_list_long

class Template:
    def tmpl_navtrailbox_body(self, weburl, ln, title, previous_links, separator, prolog, epilog):
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
            out += """<a class="navtrail" href="%(weburl)s?ln=%(ln)s">%(msg_home)s</a>""" % {
                      'weburl' : weburl,
                      'ln' : ln,
                      'msg_home' : _("Home")}
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

    def tmpl_page(self, weburl, ln, headertitle, sitename = "", supportemail = "", description = "", keywords = "",
                  userinfobox = "", navtrailbox = "",
                  pageheaderadd = "", boxlefttop = "", boxlefttopadd = "",
                  boxleftbottom = "", boxleftbottomadd = "", boxrighttop = "", boxrighttopadd = "",
                  boxrightbottom = "", boxrightbottomadd = "", titleprologue = "", title = "", titleepilogue = "", body = "",
                  version = "", lastupdated = None, languagebox = "",
                  pagefooteradd = "",
                  uid = 0,
                 ):
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

          - 'version' *string* - the version number of CDSware

          - 'lastupdated' *string* - when the page was last updated

          - 'languagebox' *string* - the HTML code for the language box

          - 'pagefooteradd' *string* - additional page footer HTML code

           Output:

          - HTML code of the page
        """

        # load the right message language
        _ = gettext_set_language(ln)

        if lastupdated:
            msg_lastupdated = _("Last updated:") + " " + lastupdated
        else:
            msg_lastupdated = ""
        out = self.tmpl_pageheader(
                  weburl = weburl,
                  ln = ln,
                  headertitle = headertitle,
                  sitename = sitename,
                  supportemail = supportemail,
                  description = description,
                  keywords = keywords,
                  userinfobox = userinfobox,
                  navtrailbox = navtrailbox,
                  pageheaderadd = pageheaderadd,
                  languagebox = languagebox,
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
    <h1 class="headline">%(title)s</h1>
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

  'title' : title,
  'body' : body,

} + self.tmpl_pagefooter(
                  weburl = weburl,
                  ln = ln,
                  sitename = sitename,
                  supportemail = supportemail,
                  version = version,
                  lastupdated = lastupdated,
                  languagebox = languagebox,
                  pagefooteradd = pagefooteradd
              )
        return out

    def tmpl_pageheader(self, weburl, ln, headertitle = "", sitename = "", supportemail = "", description = "", keywords = "",
                          userinfobox = "", navtrailbox = "",
                          pageheaderadd = "", languagebox = "",
                          uid = 0,
                       ):
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

           Output:

          - HTML code of the page headers
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """
<!-- DO NOT EDIT THIS FILE! IT WAS AUTOMATICALLY GENERATED FROM CDSware SOURCES. LOOK THERE FOR THE COPYRIGHT INFO. -->
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
 <title>%(sitename)s: %(headertitle)s</title>
 <link rev="made" href="mailto:%(supportemail)s">
 <link rel="stylesheet" href="%(weburl)s/img/cds.css">
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
             <a class=header href="%(weburl)s/?ln=%(ln)s">%(msg_search)s</a>
       </td>
       <td class="headermoduleboxbodyblank">
             &nbsp;
       </td>
       <td class="headermoduleboxbody">
             <a class=header href="%(weburl)s/submit.py?ln=%(ln)s">%(msg_submit)s</a>
       </td>
       <td class="headermoduleboxbodyblank">
             &nbsp;
       </td>
       <td class="headermoduleboxbody">
             <a class=header href="%(weburl)s/youraccount.py/display?ln=%(ln)s">%(msg_personalize)s</a>
       </td>
       <td class="headermoduleboxbodyblank">
             &nbsp;
       </td>
       <td class="headermoduleboxbody">
             <a class=header href="%(weburl)s/help/index.%(ln)s.html">%(msg_help)s</a>
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
          'ln' : ln,

          'sitename' : sitename,
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
          'languagebox' : languagebox,

        }
        return out

    def tmpl_pagefooter(self, weburl, ln, sitename = "", supportemail = "",
                        version = "", lastupdated = None, languagebox = "",
                        pagefooteradd = ""
                       ):
        """Creates a page footer

           Parameters:

          - 'weburl' *string* - The base URL for the site

          - 'ln' *string* - The language to display

          - 'sitename' *string* - the first part of the page HTML title

          - 'supportemail' *string* - email of the support team

          - 'version' *string* - the version number of CDSware

          - 'lastupdated' *string* - when the page was last updated

          - 'languagebox' *string* - the HTML code for the language box

          - 'pagefooteradd' *string* - additional page footer HTML code

           Output:

          - HTML code of the page headers
        """

        # load the right message language
        _ = gettext_set_language(ln)

        if lastupdated:
            msg_lastupdated = _("Last updated:") + " " + lastupdated
        else:
            msg_lastupdated = ""

        out = """
<div class="pagefooter">
%(pagefooteradd)s
<!-- replaced page footer -->
 <div class="pagefooterstripeleft">
  %(sitename)s&nbsp;::&nbsp;<a class="footer" href="%(weburl)s/?ln=%(ln)s">%(msg_search)s</a>&nbsp;::&nbsp;<a class="footer" href="%(weburl)s/submit.py?ln=%(ln)s">%(msg_submit)s</a>&nbsp;::&nbsp;<a class="footer" href="%(weburl)s/youraccount.py/display?ln=%(ln)s">%(msg_personalize)s</a>&nbsp;::&nbsp;<a class="footer" href="%(weburl)s/help/index.%(ln)s.html">%(msg_help)s</a>
  <br>
  %(msg_poweredby)s <a class="footer" href="http://cdsware.cern.ch/">CDSware</a> v%(version)s
  <br>
  %(msg_maintainedby)s <a class="footer" href="mailto:%(supportemail)s">%(supportemail)s</a>
  <br>
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
          'ln' : ln,

          'sitename' : sitename,
          'supportemail' : supportemail,

          'msg_search' : _("Search"),
          'msg_submit' : _("Submit"),
          'msg_personalize' : _("Personalize"),
          'msg_help' : _("Help"),

          'msg_poweredby' : _("Powered by"),
          'msg_maintainedby' : _("Maintained by"),

          'msg_lastupdated' : msg_lastupdated,
          'languagebox' : languagebox,
          'version' : version,

          'pagefooteradd' : pagefooteradd,

        }
        return out

    def tmpl_language_selection_box(self, urlargs="", language="en"):
        """Take URLARGS and LANGUAGE and return textual language
           selection box for the given page.

           Parameters:

          - 'urlargs' *string* - The url args that helped produce this page

          - 'language' *string* - The selected language

        """

        # load the right message language
        _ = gettext_set_language(language)

        out = ""
        for (lang, lang_namelong) in language_list_long():
            if lang == language:
                out += """ <span class="langinfo">%s</span> &nbsp; """ % lang_namelong
            else:
                if urlargs:
                    urlargs = sre.sub(r'ln=.*?(&|$)', '', urlargs)
                if urlargs:
                    if urlargs.endswith('&'):
                        urlargs += "ln=%s" % lang
                    else:
                        urlargs += "&ln=%s" % lang
                else:
                    urlargs = "ln=%s" % lang
                out += """ <a class="langinfo" href="?%s">%s</a> &nbsp; """ % (urlargs, lang_namelong)
        return _("This site is also available in the following languages:") + "<br>" + out

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

        info_not_available = "NA"

        if title == None:
            if errors: 
                title = "Error: %s" % errors[0][1]
            else:    
                title = _("Internal Error")

        if req:
            try:
                browser_s = ''
                if req.headers_in.has_key('User-Agent'):
                    browser_s = """Browser: %s\n""" % req.headers_in['User-Agent']
                host_s = req.hostname
                page_s = req.unparsed_uri
                client_s = req.connection.remote_ip 
            except:
                pass
        else:    
            browser_s = "Browser: NA\n"
            host_s = page_s = client_s = info_not_available

        error_s = ''
        sys_error_s = ''
        traceback_s = ''
        if verbose >= 1:
            sys_error_s = """System Error: %s %s\n""" % (sys.exc_info()[0], sys.exc_info()[1])
            if errors:
                errs = ''
                for error_tuple in errors:
                    try:
                        errs += "%s%s : %s\n " % (' '*6, error_tuple[0], error_tuple[1])
                    except:
                        errs += "%s%s\n" % (' '*6, error_tuple)
                errs = errs[6:-2] # get rid of trainling ','
                error_s = "Error: %s \n" % errs
            else:
                error_s = "Error: None None\n"
        if verbose >= 9:
            traceback_s = "Traceback: \n%s" % string.join(traceback.format_tb(sys.exc_info()[2]),"\n")

        out = """
              <table class="errorbox">
               <thead>
                <tr>
                 <th class="errorboxheader">
                   <p> %(title)s %(sys1)s %(sys2)s
                 </th>
                </tr>
               </thead>
               <tbody>
                <tr>
                  <td class="errorboxbody">
                    <p>%(contact)s
                    <blockquote><pre>
URI: http://%(host)s%(page)s
Time: %(time)s
%(browser)sClient: %(client)s
%(error)s%(sys_error)s%(traceback)s
</pre></blockquote>
                  </td>
                </tr>
                <tr>
                    <td><form action="%(weburl)s/error.py/send_report" method="POST">
                            Please send an error report to the Administrator <input class="adminbutton" type="submit" value="send error report" /><br>
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
                'sys1'      : sys.exc_info()[0],
                'sys2'      : sys.exc_info()[1],
                'contact'   : _("Please contact <a href=\"mailto:%s\">%s</a> quoting the following information:")  % (urllib.quote(supportemail), supportemail),
                'host'      : host_s,
                'page'      : page_s,
                'time'      : time.strftime("%02d/%b/%Y:%H:%M:%S %z"),
                'browser'   : browser_s,
                'client'    : client_s,
                'error'     : error_s,
                'traceback' : traceback_s,
                'sys_error' : sys_error_s,
                'weburl'    : weburl,
                'referer'   : page_s!=info_not_available and ("http://" + host_s + page_s) or info_not_available
              }
 
        return out













