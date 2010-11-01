# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
bibcirculation config file
"""

__revision__ = "$Id$"

from invenio.config import CFG_CERN_SITE, \
                           CFG_SITE_URL


# templates used to notify borrowers
if CFG_CERN_SITE == 1:
    CFG_BIBCIRCULATION_TEMPLATES = {
    'OVERDUE': 'Overdue letter template (write some text)',
    'REMINDER': 'Reminder letter template (write some text)',
    'NOTIFICATION': 'Notification letter template (write some text)',
    'RECALL1': 'Dear Colleague,\n\n'\
               'The loan period has now expired for the following Library item which you'\
               ' borrowed. Please return it to the Library (either personally or by'\
               ' internal mail) or extend the loan at:\n\n'\
               '%s/yourloans/display \n\n' % CFG_SITE_URL +
               'If you have already done so, please ignore this message.\n\n'\
               'Item information:\n\n'\
               '%s \n'\
               '%s \n'\
               '%s \n'\
               '%s \n'\
               '%s \n\n'\
               'Thank you for using our services, Library Staff \n\n\n\n'\
               'If you are not able to update your loans via WWW or for any other'\
               ' matter concerning circulation of library material, please simply'\
               ' reply to this mail.',
    'RECALL2': 'Dear Colleague\n\n'\
               'The return date for the following Library item which you borrowed is now'\
               'well past. According to our records you have not responded to our first'\
               'recall message, so we now ask you to return the item to the Library'\
               'without delay (either personally or by internal mail). If you have already'\
               'done so, please ignore this message. To send any comments, reply to this'\
               'mail.\n\n' \
               'Item information:\n\n'\
               '%s \n'\
               '%s \n'\
               '%s \n'\
               '%s \n'\
               '%s \n\n'\
               'Thank you in advance for your cooperation, CERN Library Staff',
    'RECALL3': 'Dear Colleague,\n\n'\
               'We have already sent you two messages about the following Library item,'\
               'which should have been returned a long time ago. According to our records,'\
               'you have not responded to either of them. Please return the item to the'\
               'Library without delay (either personally or by internal mail) or reply to'\
               'this mail giving any comments. If we do not hear from you within one week,'\
               'I will feel free to take up the matter with your supervisor. If you have'\
               'already returned the item, please ignore this message.\n\n'\
               'Item information:\n\n'\
               '%s \n'\
               '%s \n'\
               '%s \n'\
               '%s \n'\
               '%s \n\n'\
               'Thank you in advance for your cooperation, CERN Library Staff',
    'EMPTY': 'Please choose one template'
    }

else:
    CFG_BIBCIRCULATION_TEMPLATES = {
        'OVERDUE': 'Overdue letter template (write some text)',
        'REMINDER': 'Reminder letter template (write some text)',
        'NOTIFICATION': 'Notification letter template (write some text)',
        'SEND_RECALL': 'Dear Colleague,\n\n'\
                       'The loan for the document(s)\n\n'\
                       'Item information:\n\n'\
                       '\t title: %s \n'\
                       '\t year: %s \n'\
                       '\t author(s): %s \n'\
                       '\t isbn: %s \n'\
                       '\t publisher: %s \n\n'\
                       'is overdue and another reader(s) is/are waiting for the document(s).'\
                       'Please return them to the Library as soon as possible.'\
                       '\n\nBest regards',
        'RECALL1': 'Dear Colleague,\n\n'\
                   'The loan period has now expired for the following Library item which you'\
                   ' borrowed. Please return it to the Library (either personally or by'\
                   ' internal mail) or extend the loan at:\n\n'\
                   '%s/yourloans/display \n\n' % CFG_SITE_URL +
                   'If you have already done so, please ignore this message.\n\n'\
                   'Item information:\n\n'\
                   '\t title: %s \n'\
                   '\t year: %s \n'\
                   '\t author(s): %s \n'\
                   '\t isbn: %s \n'\
                   '\t publisher: %s \n\n'\
                   'Thank you for using our services, Library Staff \n\n\n\n'\
                   'If you are not able to update your loans via WWW or for any other'\
                   'matter concerning circulation of library material, please simply'\
                   'reply to this mail.',
        'RECALL2': 'Dear Colleague\n\n'\
                   'The return date for the following Library item which you borrowed is now'\
                   'well past. According to our records you have not responded to our first'\
                   'recall message, so we now ask you to return the item to the Library'\
                   'without delay (either personally or by internal mail). If you have already'\
                   'done so, please ignore this message. To send any comments, reply to this'\
                   'mail.' \
                   'Item information:\n\n'\
                   '%s \n'\
                   '%s \n'\
                   '%s \n'\
                   '%s \n'\
                   '%s \n\n'\
                   'Thank you in advance for your cooperation, Library Staff',
        'RECALL3': 'Dear Colleague,\n\n'\
               'We have already sent you two messages about the following Library item,'\
               'which should have been returned a long time ago. According to our records,'\
               'you have not responded to either of them. Please return the item to the'\
               'Library without delay (either personally or by internal mail) or reply to'\
               'this mail giving any comments. If we do not hear from you within one week,'\
               'I will feel free to take up the matter with your supervisor. If you have'\
               'already returned the item, please ignore this message.\n\n'\
               'Item information:\n\n'\
               '%s \n'\
               '%s \n'\
               '%s \n'\
               '%s \n'\
               '%s \n\n'\
               'Thank you in advance for your cooperation, CERN Library Staff',
        'EMPTY': 'Please choose one template'
        }

CFG_BIBCIRCULATION_AMAZON_ACCESS_KEY = '1T6P3M3TDMW9HWJ212R2'

if CFG_CERN_SITE == 1:
    CFG_BIBCIRCULATION_OVERDUE_LETTER_SENDER = 'CERN Library<library.desk@cern.ch>'
    CFG_BIBCIRCULATION_LIBRARIAN_EMAIL = 'CERN Library<library.desk@cern.ch>'
else:
    CFG_BIBCIRCULATION_OVERDUE_LETTER_SENDER = 'Atlantis Library<balthasar.montague@cds.cern.ch>'
    CFG_BIBCIRCULATION_LIBRARIAN_EMAIL = 'Atlantis Library<balthasar.montague@cds.cern.ch>'

CFG_BIBCIRCULATION_HOLIDAYS = ['2009-07-09']

CFG_BIBCIRCULATION_WORKING_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
