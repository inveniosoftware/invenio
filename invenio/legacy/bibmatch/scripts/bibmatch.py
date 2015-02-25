# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2010, 2011, 2013 CERN.
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
Match bibliographic data in a MARCXML file against database content.

 Usage: bibmatch [options] < input.xml > output.xml

 Examples:

 $ bibmatch -b -n < input.xml
 $ bibmatch --field=title < input.xml >  unmatched.xml
 $ bibmatch --field=245__a --mode=a < input.xml > unmatched.xml
 $ bibmatch --print-ambiguous --query-string="245__a||100__a" < input.xml > unmatched.xml

 $ bibmatch [options] < input.xml > unmatched.xml

 Options:


 Output:

 -0 --print-new (default) print unmatched in stdout
 -1 --print-match print matched records in stdout
 -2 --print-ambiguous print records that match more than 1 existing records
 -3 --print-fuzzy print records that match the longest words in existing records

 -b --batch-output=(filename). filename.0 will be new records, filename.1 will be matched,
      filename.2 will be ambiguous, filename.3 will be fuzzy match

 Simple query:

 -f --field=(field)

 Advanced query:

 -c --config=(config-filename)
 -q --query-string=(uploader_querystring)
 -m --mode=(a|e|o|p|r)
 -o --operator=(a|o)

 Where mode is:
  "a" all of the words,
  "o" any of the words,
  "e" exact phrase,
  "p" partial phrase,
  "r" regular expression.

 Operator is:
  "a" and,
  "o" or.

 General options:

 -n   --noprocess          Do not print records in stdout.
 -i,  --input              use a named file instead of stdin for input
 -h,  --help               print this help and exit
 -V,  --version            print version information and exit
 -v,  --verbose=LEVEL      verbose level (from 0 to 9, default 1)

"""

from invenio.base.factory import with_app_context


@with_app_context()
def main():
    from invenio.legacy.bibmatch.engine import main as engine_main
    return engine_main()
