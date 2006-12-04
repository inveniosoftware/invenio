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

__revision__ = "$Id$"

import time
import smtplib
    
def send_email(fromaddr, toaddr, body, attempt=0):
    if toaddr != "":
        if attempt > 2:
            raise functionError('error sending email to %s: SMTP error; gave up after 3 attempts' % toaddr)
        try:
            server = smtplib.SMTP('localhost')
            server.sendmail(fromaddr, toaddr, body)
            server.quit()
        except:
            time.sleep(10)
            send_email(fromaddr, toaddr, body, attempt+1)
            return
        
def forge_email(fromaddr, toaddr, bcc, subject, content):
    body = 'From: %s\nTo: %s\nContent-Type: text/plain; charset=utf-8\nSubject: %s\n%s' % (fromaddr, toaddr,subject, content)
    return body
