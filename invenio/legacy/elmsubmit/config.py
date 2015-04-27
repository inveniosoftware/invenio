# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2010, 2011 CERN.
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

"""ElmSubmit configuration parameters."""

from __future__ import unicode_literals

__revision__ = "$Id$"

import pkg_resources
from invenio.config import CFG_SITE_ADMIN_EMAIL, \
     CFG_SITE_URL, CFG_SITE_NAME

# elmsubmit configuration file:
CFG_ELMSUBMIT_FILES = {
         'mailprefix': 'mail',
         'test_case_1': pkg_resources.resource_filename('invenio.testsuite', 'data/elmsubmit_tests_1.mbox'),
         'test_case_2': pkg_resources.resource_filename('invenio.testsuite', 'data/elmsubmit_tests_2.mbox'),
         }
# Messages we need to send to the user, before we've identified the
# correct language to talk to them in (so we assume English!):

# pylint: disable=C0301

CFG_ELMSUBMIT_NOLANGMSGS = {'bad_email': 'Your email could not be parsed correctly to discover a submission. Please check your email client is functioning correctly.',
             'bad_submission': 'The submission data that you have provided could not be parsed correctly. Please visit <%s> for a description of the correct format.' % CFG_SITE_URL,
              'missing_type':  'The submission data that you have provided does not contain a TYPE field. This is mandatory for all submissions.',
              'unsupported_type': 'The TYPE field of your submission does not contain a recognized value.',
              'missing_fields_1': 'Your submission of type',
              'missing_fields_2': 'does not contain all the required fields:',
              'bad_field': 'This field does not validate correctly:',
              'correct_format': 'It must be formatted as follows:',
              'missing_attachment': 'We could not find the following file attached to your submission email:',
              'temp_problem': 'There is a temporary problem with %s\'s email submission interface. Please retry your submission again shortly.' % CFG_SITE_NAME}

CFG_ELMSUBMIT_SERVERS = {'smtp': 'localhost'}

CFG_ELMSUBMIT_PEOPLE = {'admin': CFG_SITE_ADMIN_EMAIL}

# fields required in the submission mail
CFG_ELMSUBMIT_REQUIRED_FIELDS = ['title',
                   'author',
                   'date',
                   'files']

# defines the mapping of metadata fields to their marc codes


# mapping code as a list means the first element is mapped to the first element
# of the list, and the rest to the second
CFG_ELMSUBMIT_MARC_MAPPING = {'author': ['100__a', '700__a'],
                'title': '245__a',
                'subtitle': '245__b',
                'photocaption': '246__b',
                'subject': '65017a',
                'secondary_subject': '65027a',
                'email': '8560_f',
                'files': ['FFT__a', 'FFT__a'],
                'affiliation': ['100__u', '700__u'],
                'language': '041__a',
                'abstract': '520__a',
                'keywords': '6531_a',
                'OAIid': '909COo',
                'PrimaryReportNumber': '037__a',
                'AdditionalReportNumber': '088__a',
                'series': ['490__a','490__v'],
                'year': '260__a',
                'note': '500__a',
                #test tags used in test cases
                'test1': '111__a',
                'test2': '111__b',
                'test3': '111__c',
                'test4': '111__d',
                'test5': '111__e'
                }

# the list of the fields determines which subfields should be joined into a
# single datafield
CFG_ELMSUBMIT_MARC_FIELDS_JOINED = {'700__': [['a', 'u']],
                      '100__': [['a', 'u']],
                      #test tags
                      '111__': [['a','c'],['b','d']]
                      }


