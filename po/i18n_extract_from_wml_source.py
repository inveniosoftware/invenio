## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2010, 2011 CERN.
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

from __future__ import print_function

"""
This tool extracts sentences to be translated from HTML / WML source
files.

The sentences to translate are marked with the following tag:

 Blah blah _(To be translated)_ blah.

These tags can span several lines. Extra whitespace is discarded.
"""

import sys, re, os

_tag_re = re.compile(r'_\((.*?)\)_', re.M)
_nl_re = re.compile('\n')
_ws_re = re.compile('\s+')

def print_usage():
    """Print usage info."""
    print("""Usage: %s <dirname> <potfiles-filename>
Description: Extract translatable strings from the list of files read
             from potfiles-filename.  The files specified there are
             relative to dirname.  Print results on stdout.
""")
    return

def quote(text):
    """Normalize and quote a string for inclusion in the po file."""
    return text.\
           replace('\\', '\\\\').\
           replace('\n', '\\\\n').\
           replace('\t', '\\\\t').\
           replace('"',  '\\"')


def extract_from_wml_files(dirname, potfiles_filename):
    """Extract translatable strings from the list of files read from
    potfiles_filename.  The files specified there are relative to
    dirname.  Print results on stdout.
    """

    ## extract messages and fill db:
    db = {}
    for f in [ f.strip() for f in open(potfiles_filename) ]:
        if not f or f.startswith('#'):
            continue

        f = f.rstrip(' \\')
        data = open(dirname + "/" + f).read()

        lines = [0]
        for m in _nl_re.finditer(data):
            lines.append(m.end())

        for m in _tag_re.finditer(data.replace('\n', ' ')):
            word = m.group(1)
            pos  = m.start()

            line = len([x for x in lines if x < pos])

            ref = '%s:%d' % (f, line)

            # normalize the word a bit, as it comes from a file where
            # whitespace is not too significant.
            word = _ws_re.sub(' ', word.strip())

            db.setdefault(word, []).append(ref)

    ## print po header:
    print(r'''
    # # This file is part of Invenio.
    # # Copyright (C) 2006, 2007, 2008, 2010, 2011 CERN.
    # #
    # # Invenio is free software; you can redistribute it and/or
    # # modify it under the terms of the GNU General Public License as
    # # published by the Free Software Foundation; either version 2 of the
    # # License, or (at your option) any later version.
    # #
    # # Invenio is distributed in the hope that it will be useful, but
    # # WITHOUT ANY WARRANTY; without even the implied warranty of
    # # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    # # General Public License for more details.
    # #
    # # You should have received a copy of the GNU General Public License
    # # along with Invenio; if not, write to the Free Software Foundation, Inc.,
    # # 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
    msgid ""
    msgstr ""
    "Project-Id-Version: Invenio 0.7\n"
    "POT-Creation-Date: Tue Nov 22 16:44:03 2005\n"
    "PO-Revision-Date: 2005-11-22 11:20+0100\n"
    "Last-Translator: FULL NAME <EMAIL@ADDRESS>\n"
    "Language-Team: LANGUAGE <LL@li.org>\n"
    "MIME-Version: 1.0\n"
    "Content-Type: text/plain; charset=UTF-8\n"
    "Content-Transfer-Encoding: 8bit\n"
    "Generated-By: pygettext.py 1.5\n"

    ''')

    ## print po content from db:
    for original, refs in db.items():

        for ref in refs:
            print("#: %s" % ref)

        print('msgid "%s"' % quote(original))
        print('msgstr ""')
        print()

    return

if __name__ == "__main__":
    if len(sys.argv) == 3:
        dirname = sys.argv[1]
        potfiles_filename = sys.argv[2]
        if not os.path.isdir(dirname):
            print("ERROR: %s is not a directory." % dirname)
            print_usage()
            sys.exit(1)
        elif not os.path.isfile(potfiles_filename):
            print("ERROR: %s is not a file." % potfiles_filename)
            print_usage()
            sys.exit(1)
        else:
            extract_from_wml_files(sys.argv[1], sys.argv[2])
    else:
        print_usage()


