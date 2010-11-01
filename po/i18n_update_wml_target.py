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

"""This tool updates WML target file still containing sentences to be
translated. The sentences to translate are marked with the following
tag:

 Blah blah _(To be translated)_ blah.

These tags can span several lines. Extra whitespace is discarded.
"""

import sys
import os
import re

import gettext

lang = sys.argv[1]
files = sys.argv[2:]

charset = 'utf-8'

# a translation file is located in the source directory, along with
# this script. This makes it easy to find its path.
podir = os.path.dirname(__file__)

translation_file = os.path.join(podir, lang+'.gmo')
translation = gettext.GNUTranslations(open(translation_file))


# This matches the strings to be translated
_tag_re = re.compile(r'_\((.*?)\)_', re.DOTALL)
_ws_re = re.compile('\s+')

# we perform the substitution on the whole file at once, as they are
# not expected to be multi-gigabyte long.

def replace(match):
    """This function is called for each replacement, and fetches the
    translation from the gettext catalog.
    """
    text = match.group(1).decode(charset)
    text = _ws_re.sub(' ', text.strip())

    return translation.ugettext(text).encode('utf-8')

for filename in files:
    content = open(filename).read()
    content = _tag_re.sub(replace, content)

    open (filename,'w').write(content)
