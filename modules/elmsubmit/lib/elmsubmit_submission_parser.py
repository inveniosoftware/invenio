# -*- coding: utf-8 -*-
##
## $Id$
##
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



import re

tokens = (
    'CDSON',
    'CDSOFF',
    'KEY',
    'VALUE',
    )

# Tokens
def t_CDSON(t):
    r'\s*cdson:::\n+'
    return t

def t_KEY(t):
    r'(?<=\n)[\ \t]*_+\w+?_+\s*\n+'
    t.value = re.search(r'_+(\w+?)_+', t.value).group(1)
    t.value = t.value.lower()
    return t

def t_VALUE(t):
    r'.+?\S+.*?(?=([\ \t]*_+\w+?_+\s*\n|\n\s*cdsoff:::))'
    t.value = t.value.strip()
    return t

def t_CDSOFF(t):
    r'(?s)\n\s*cdsoff:::(\n.*)?'
    match = re.search(r'(?s)\n\s*cdsoff:::(\n.*)?', t.value)
    global trailing_text
    if match.group(1) is not None:
        # [1:] kills the extra newline we matched:
        trailing_text = match.group(1)[1:]
    else:
        trailing_text = ''
    return t

def t_error(t):
    print "Illegal character '%s'" % t.value[0]
    raise ValueError('bad parsing')
    
# Build the lexer
import lex
lex.lex(optimize=1)

# Parsing rules

# Dictionary:
data = {}

def p_submission(p):
    """submission : CDSON assignmentList CDSOFF"""
    
def p_assignmentList(p):
    """assignmentList : assignment
                      | assignment assignmentList"""

def p_assignment(p):
    """assignment : KEY VALUE"""
    data[p[1]] = p[2]

def p_error(p):
    print "Syntax error at '%s'" % p.value
    raise ValueError('syntax error')

import yacc
yacc.yacc()

def parse_submission(string):
    global data
    global trailing_text
    try:
        try:
            yacc.parse(string)
            return (data, trailing_text)
        except:
            raise SubmissionParserError()
    finally:
        data = {}
        trailing_text = ''

class SubmissionParserError(Exception):
    pass

