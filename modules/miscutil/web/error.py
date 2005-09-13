# -*- coding: utf-8 -*-
## $Id$
## Comments and reviews for records.
                                                                                                                                                                                                     
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
                                                                                                                                                                                                     
__lastupdated__ = """FIXME: last updated"""


from cdsware.webpage import page
from cdsware.errorlib import *

def send_report(req, header="NA", url="NA", time="NA", browser="NA", client="NA", error="NA", sys_error="NA", traceback="NA", referer="NA"):
    """
    Confirmation page of error report sent the admin
    parameters are the same as used for the error box. See webstyle_templates.tmpl_error_box
    """
    send_error_report_to_admin(header, url, time, browser, client, error, sys_error, traceback)
    
    out = '''
    <span class="exampleleader">The error report has been sent</span><br>
    <br>
    Many thanks for helping us make CDSware better.<br>
    <br>
    %(back)s 

    ''' % \
        {   'back'      : referer!="NA" and "<a href=\"%s\">back</a>" % (referer,) or "Use the back button of your browser to return to the previous page"
        }
    return page(title="Thanks", body=out, navtrail="", description="", keywords="",
                cdspageheaderadd="", cdspageboxlefttopadd="", cdspageboxleftbottomadd="", cdspageboxrighttopadd="",
                cdspageboxrightbottomadd="", cdspagefooteradd="", lastupdated="", urlargs="", verbose=1, titleprologue="", titleepilogue="",
                req=req)

