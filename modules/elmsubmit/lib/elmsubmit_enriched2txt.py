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
A text/enriched to text/plain converter.

This is a module exporting a single function enriched2txt which
takes as its argument a string of 'enriched text' and returns its
conversion to 'plain text'. 'enriched text' is the text format as
specified in RFC1896 for use as an email payload with mime type
text/enriched.

Note that it is somewhat simpler than the text/richtext converter (see
elmsubmit_richtext2txt.py); this is largely thanks to the enriched
text specification attempting to remove many of the complexities found
in text/richtext; eg. superscript tags, iso-8859-x tags.

If you hand enriched2txt a regular string, the algorithm assumes
7-bit ascii. If you wish to parse internationalized text, make sure
you either:

1. Use an encoding that can be treated safely as if it were 7-bit
   ascii (eg. utf-8)

or better:

2. Pass in a unicode object.

This function is a direct conversion of the C code from the appendix
of RFC1896 which gives a sample enriched text to plain text
converter. This is a quick conversion job, since text/enriched email
payload is fairly rare these days and so not worth too much time
considering. I haven't paid much thought as to the quality of the
original algorithm --- hopefully the RFC writer had his thinking cap
on straight; it seems to produce fairly reasonable output on test
documents.

Note that one difference in the python version of the parser is that
it allows markup tokens of unlimited size.

Unlike the specification for text/richtext (see RFC1341), only one
charset is allowed in any text/enriched file. Quoting RFC1896:

> 1 For cases where the different types of non-ASCII text can be
> limited to their own paragraphs with distinct formatting, a
> multipart message can be used with each part having a Content-Type
> of text/enriched and a different charset parameter. The one caveat
> to using this method is that each new part must start in the initial
> state for a text/enriched document. That means that all of the
> text/enriched commands in the preceding part must be properly
> balanced with ending commands before the next text/enriched part
> begins. Also, each text/enriched part must begin a new paragraph.

> 2 If different types of non-ASCII text are to appear in the same
> line or paragraph, or if text/enriched formatting (e.g. margins,
> typeface, justification) is required across several different types
> of non-ASCII text, a single text/enriched body part should be used
> with a character set specified that contains all of the required
> characters. For example, a charset parameter of "UNICODE-1-1-UTF-7"
> as specified in [RFC-1642] could be used for such purposes. Not only
> does UNICODE contain all of the characters that can be represented
> in all of the other registered ISO 8859 MIME character sets, but
> UTF-7 is fully compatible with other aspects of the text/enriched
> standard, including the use of the "<" character referred to
> below. Any other character sets that are specified for use in MIME
> which contain different types of non-ASCII text can also be used in
> these instances.
"""

__revision__ = "$Id$"

def enriched2txt(string):

    # f and g will be our input/output streams.

    # We instantiate them as cStringIO objects for speed if the input
    # string is not unicode (ie. its a normal string type). Otherwise
    # we make them StringIO objects.

    if type(string) != unicode:

        import cStringIO

        # Create file like object from string for input file.
        f = cStringIO.StringIO(string)

        # Create another file like object from string for output file.
        g = cStringIO.StringIO()

    else:

        import StringIO

        # Create file like object from string for input file.
        f = StringIO.StringIO(string)

        # Create another file like object from string for output file.
        g = StringIO.StringIO(u'')

    # From here on in we are almost identical to the RFC1896 code, except substitute:
    # STDIN -> object f
    # STDOUT -> object g
    # EOF -> ''
    # ungetc -> seek(-1,1)

    paramct = 0
    newlinect = 0
    nofill = 0

    c = f.read(1)

    while c != '':
        if (c == '<'):
            if newlinect == 1: g.write(' ')
            newlinect = 0;
            c = f.read(1)
            if (c == '<'):
                if paramct <= 0: g.write(c)
            else:
                f.seek(-1,1)
                token = ""
                c = f.read(1)

                while c != '' and c!= '>':
                    token += c
                    c = f.read(1)

                if c == '': break

                token = token.lower()

                if token == 'param':
                    paramct += 1
                elif token == 'nofill':
                    nofill += 1
                elif token == '/param':
                    paramct -= 1
                elif token == '/nofill':
                    nofill -= 1

        else:
            if paramct > 0:
                pass # ignore params
            elif c == '\n' and nofill <= 0:
                newlinect += 1
                if newlinect > 1: g.write(c)
            else:
                if newlinect == 1: g.write(' ')
                newlinect = 0
                g.write(c)

        c = f.read(1)

    g.write('\n')

    return g.getvalue()

# The original C code direct from RFC1896 appendix.
# See: http://people.qualcomm.com/presnick/textenriched.html

# #include <ctype.h>
# #include <stdio.h>
# #include <stdlib.h>
# #include <string.h>

# main() {
#         int c, i, paramct=0, newlinect=0, nofill=0;
#         char token[62], *p;

#         while ((c=getc(stdin)) != EOF) {
#                 if (c == '<') {
#                         if (newlinect == 1) putc(' ', stdout);
#                         newlinect = 0;
#                         c = getc(stdin);
#                         if (c == '<') {
#                                 if (paramct <= 0) putc(c, stdout);
#                         } else {
#                                  ungetc(c, stdin);
#                                  for (i=0, p=token; (c=getc(stdin)) != EOF && c != '>'; i++) {
#                                         if (i < sizeof(token)-1)
#                                                 *p++ = isupper(c) ? tolower(c) : c;
#                                  }
#                                  *p = '\0';
#                                  if (c == EOF) break;
#                                  if (strcmp(token, "param") == 0)
#                                          paramct++;
#                                  else if (strcmp(token, "nofill") == 0)
#                                          nofill++;
#                                  else if (strcmp(token, "/param") == 0)
#                                          paramct--;
#                                  else if (strcmp(token, "/nofill") == 0)
#                                          nofill--;
#                          }
#                 } else {
#                         if (paramct > 0)
#                                 ; /* ignore params */
#                         else if (c == '\n' && nofill <= 0) {
#                                 if (++newlinect > 1) putc(c, stdout);
#                         } else {
#                                 if (newlinect == 1) putc(' ', stdout);
#                                 newlinect = 0;
#                                 putc(c, stdout);
#                         }
#                 }
#         }
#         /* The following line is only needed with line-buffering */
#         putc('\n', stdout);
#         exit(0);
# }


