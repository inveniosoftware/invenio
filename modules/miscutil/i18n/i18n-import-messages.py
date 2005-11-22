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
This script extracts translations from messages.py and writes them in
a format suitable for gettext.
"""

import sys, time, locale, pprint, re

if len (sys.argv) == 1 or sys.argv [0] in ["-h","--help"]:
    print "Usage: i18n-import-messages.py msgfile"
    sys.exit()


msgfile = sys.argv [1]


# Parse the wml file with a custom parser

_tag_re = re.compile ('(</?[\w\s=_-]+>)')

def lexer (name):
    
    for line in open (msgfile):
        if line.startswith ('#'): continue

        line = line.strip ()
        if not line: continue

        for part in _tag_re.split (line):
            if part and part [0] == '<':
                if part [1] == '/':
                    yield ('>', part [2:-1])
                else:
                    args = part [1:-1].split ()
                    yield ('<', args)
            else:
                yield ('T', part)

    return
            
OUTSIDE, IN_MSG, IN_TEXT = range (3)

state = OUTSIDE
db    = {}

all_langs = {}

for token, value in lexer (msgfile):

    if state == OUTSIDE:
        if token == 'T': continue
        
        if token != '<' or value [0] != 'define-tag':
            raise SyntaxError ('unexpected token %s' % repr ((token, value)))

        state = IN_MSG
        msg   = value [1]
        wsd   =  'whitespace=delete' in value
        table = {}
        continue

    elif state == IN_MSG:
        if token == '>':
            assert value == 'define-tag'

            state = OUTSIDE
            db [msg] = table
            continue

        if token == '<':
            state = IN_TEXT
            ln    = value [0]
            all_langs [ln] = True
            text  = ''
            continue

    elif state == IN_TEXT:
        if token == '>':
            if value == ln:
                table [ln] = text
                state = IN_MSG
            else:
                # this is an internal token
                text += '</%s>' % value
            continue
            
        if token == 'T':
            text += value
            continue

        if token == '<':
            text += '<%s>' % ' '.join (value)
            continue
            
msgs = [ x for x in db.keys () ]
msgs.sort ()

def quote (text):
    return text.\
           replace ('\\', '\\\\').\
           replace ('\n', '\\\\n').\
           replace ('"',  '\\"')


for lang in all_langs.keys ():
    out = open ('compendium-%s.po' % lang, 'w')
    
    # Output the PO file

    out.write("""\
# Temporary Compendium file, extracted from messages.py
msgid ""
msgstr ""
"Project-Id-Version: CDSware 0.7\\n"
"POT-Creation-Date: Thu Nov  4 23:13:16 2004\\n"
"PO-Revision-Date: 2004-11-03 18:26+2\\n"
"Last-Translator: TIBERIU DONDERA <tiberiu.dondera (at) epfl.ch>\\n"
"Language-Team: LANGUAGE <LL@li.org>\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8-bit\\n"

""")


    for key in msgs:

        try:
            ref = db [key] ['en']
            trs = db [key] [lang]
        except KeyError:
            print >> sys.stderr, "warning: cannot translate %s in %s" % (key, lang)
            continue

        out.write ('#: %s\n' % key)
        out.write ('msgid "%s"\n' % quote (ref))
        out.write ('msgstr "%s"\n\n' % quote (trs))
