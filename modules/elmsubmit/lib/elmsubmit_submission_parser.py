# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011 CERN.
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
parse_submission takes text like this:

--------------
cdson:::

_language_
eng

_type_
test

_title_
Blathering on About More Scientific Crap

_author_
Owen, R

_num_
69

_date_
01/01/2004

_keywords_
science forgery vitriol

_abstract_
This is possibly the best document to come out of space in a long
time. Aliens have really improved their scientific writing abilites.

Brillig things about this document:
One: I wrote it.
Two: It smells of cheese.
Three: Fnah!

_note_
Not musical, but informative.

_refnums_
AA11x-madeup_ref

_files_
info.pdf
foo.txt

cdsoff:::

Dear Sir,

Here is the rest of the email.

Sincerely,
Jonathon Bloggs.

--
Tel: 555 111 234567
IT-UDS CERN
--------------

This is turned into a 2-tuple. The first entry in the tuple is a
Python dictionary containing the submission info. The second entry is
the trailing text that follows the submission (the submission MUST be
at the top of the text).

({'abstract': 'This is possibly the best document to come out of space in a long\ntime. Aliens have really improved their scientific writing abilites.\n\nBrillig things about this document:\nOne: I wrote it.\nTwo: It smells of cheese.\nThree: Fnah!',
  'author': 'Owen, R',
  'date': '01/01/2004',
  'files': 'info.pdf\nfoo.txt',
  'keywords': 'science forgery vitriol',
  'language': 'eng',
  'note': 'Not musical, but informative.',
  'num': '69',
  'refnums': 'AA11x-madeup_ref',
  'title': 'Blathering on About More Scientific Crap',
  'type': 'test'},
 '\nDear Sir,\n\nHere is the rest of the email.\n\nSincerely, \nJonathon Bloggs.\n\n--\nTel: 555 111 234567\nIT-UDS CERN')

It is fairly robust when treating misformatted submissions, so should
hopefully protect against misformatting due to evil smtp servers /
conversion from HTML email producing clients, etc. For example, we can
process the following OK:

----------------
 cdson:::

         _language_
                eng

                                                _type_



        test

_title_
                Blathering on About More Scientific Crap

__author__
                Owen, R

                                       _num_
        69

    _date_





        01/01/2004

     _keywords_
                                        science forgery vitriol
    cdsoff:::

---------------------
"""

__revision__ = "$Id$"

# text values determining begin and end of submission

submission_frame_values = ['cdson:::', 'cdsoff:::']

def parse_submission(string):
    # function extracts the metadata from the string representing the mail content

    # split the mail into lines

    list_of_lines = string.splitlines()

    # strip the lines from trailing whitespaces

    list_of_lines =  map(lambda x: x.strip(), list_of_lines)

    # throw out the empty lines

    list_of_lines = filter(None, list_of_lines)

    submission_dict = {}

    # indicator that the submission content has begun
    submission_start = 0

    # indicator that the submission content has ended
    submission_end = 0

    # current keyword
    current_keyword = ''


    for line in list_of_lines:

        # end of submission
        if (submission_end == 1):
            break

        # submission in progress
        if (submission_start == 1):

            # found a keyword
            if (line[0] == '_' and line[-1] == '_'):
                current_keyword = line[1:-1]

            # found end of submission
            elif (line == submission_frame_values[1]):
                submission_end = 1

            # adding content to dictionary
            elif (current_keyword <> ''):
                submission_dict.setdefault(current_keyword, []).append(line)
        else:

            # found beginning of submission
            if (line == submission_frame_values[0]):
                submission_start = 1

    return submission_dict

class SubmissionParserError(Exception):
    pass
