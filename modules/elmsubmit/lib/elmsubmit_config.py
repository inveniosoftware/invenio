## $Id$</protect>

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

# elmsubmit configuration file:
files = {
         'mailprefix': 'mail',
         'testcaseprefix': 'elmsubmit_testmails'}
# Messages we need to send to the user, before we've identified the
# correct language to talk to them in (so we assume English!):

nolangmsgs = {'bad_email': 'Your email could not be parsed correctly to discover a submission. Please check your email client is functioning correctly.',
             'bad_submission': 'The submission data that you have provided could not be parsed correctly. Please visit <http://pcdh23.cern.ch> for a description of the correct format.',
              'missing_type':  'The submission data that you have provided does not contain a TYPE field. This is mandatory for all submissions.',
              'unsupported_type': 'The TYPE field of your submission does not contain a recognized value.',
              'missing_fields_1': 'Your submission of type',
              'missing_fields_2': 'does not contain all the required fields:',
              'bad_field': 'This field does not validate correctly:',
              'correct_format': 'It must be formatted as follows:',
              'missing_attachment': 'We could not find the following file attached to your submission email:',
              'temp_problem': 'There is a temporary problem with CDS Invenio\'s email submission interface. Please retry your submission again shortly.'}

servers = {'smtp': 'localhost'}

people = {'admin': 'cds.support@cern.ch'}

# fields required in the submission mail
required_fields = ['title',
                   'author',
                   'date',
                   'files']

# defines the mapping of metadata fields to their marc codes


# mapping code as a list means the first element is mapped to the first element
# of the list, and the rest to the second

marc_mapping = {'author': ['100__a','700__a'],
                'title': '245__a',
                'subtitle': '245__b',
                'photocaption': '246__b',
                'subject': '65017a',
                'secondary_subject': '65027a',
                'email': '8560_f',
                'files': ['FFT__a','FFT__a'],    
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

marc_fields_joined = {'700__': [['a', 'u']],
                      '100__': [['a', 'u']],
                      #test tags
                      '111__': [['a','c'],['b','d']]
                      }


