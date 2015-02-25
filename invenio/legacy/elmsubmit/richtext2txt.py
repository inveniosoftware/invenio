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
A text/richtext to text/plain converter.

Always returns a unicode string.

This is a module exporting a single function 'richtext2txt' which takes
a string of 'enriched text' and returns its conversion to 'plain
text'. 'rich text' is the text format as specified in RFC1341 for
use as an email payload with mime type text/richtext.

The code is based on the example parser given in appendix D of
RFC1341. It is a quite heavily modified version; the new code (aside
from being in Python not C):

1. Takes account of the <np> tag.

2. Deals better with soft newlines.

3. Deals better with the paragraph tag.

4. Takes account of the <iso-8859-x> tag.

The resulting code is something of a mishmash of the functional style
of programming that I prefer and the 'big while loop' proceedural
style in which the original C code is written.

With reference to point 4: Richtext is a pain because it allows
<ISO-8859-X></ISO-8859-X> markup tags to change charsets inside a
document. This means that if we get a text/richtext email payload
with 'Content-type' header specifying a charset e.g. 'us-ascii', we
can't simply decode to a unicode object; it is possible that bytes
inside the <ISO-8859-X></ISO-8859-X> will break the
unicode(str,'us-ascii') function call!

This is frustrating because:

1. Why bother to have a charset declaration outside a document only to
   go and break it inside?

This might be understandable if text/richtext was designed
independantly of MIME and its Content-Type declarations but:

2. text/richtext is specified in the SAME RFC as the Content-type:
   MIME header!

In fairness to the RFC writer(s), they were working at a time when
unicode/iso10646 was still in flux and so it was common for people
writing bilingual texts to want to use two charsets in one
document. It is interesting to note that the later text/enriched
specification (written when unicode had petrified) removes the
possibility of charset switching.

The existence of <iso-8859-x> tags makes the parser rather more
complicated.

Treatment notes:

>    Second, the command "<nl>" is used to represent  a  required
>    line  break.   (Otherwise,  CRLFs in the data are treated as
>    equivalent to  a  single  SPACE  character.)

2.

The RFC doesn't say to treat spaces as a special character; ie. that
they should be reproduced verbatim. This leads to the odd effect that
a string such as follows (where $SPACE$ in reality would be a space
character):

"<paragraph>Some text...</paragraph>$SPACE$<paragraph>More text...</paragraph>"

Is rendered as:

"Some text...

$SPACE$

More text..."

ie. The space is considered a string of text which must be separated
from the displayed paragraphs. This seems fairly odd behaviour to me,
but the RFC seems to suggest this is correct treatment.
"""

import re
import StringIO

def richtext2txt(str, charset='us-ascii', convert_iso_8859_tags=False, force_conversion=False):
    return _richtext2txt(str, charset, convert_iso_8859_tags, force_conversion)

"""
Document options somewhere here.

##### 5. Make a note that the parsers assume \n not CRLF conventions so preconvert!!!
##### -------------------------------------------------------------------------------

"""

__revision__ = "$Id$"

def _richtext2txt(string, charset='us-ascii', convert_iso_8859_tags=False, force_conversion=False,
                  recursive=False, just_closed_para=True, output_file=None):

    if type(string) == unicode and convert_iso_8859_tags:

        # Doesn't make sense to have a unicode string
        # containing mixed charsets.
        raise ValueError("function richtext2txt cannot have both unicode input string and convert_iso_8859_tags=True.")

    # f and g will be our input/output streams.

    # Create file like object from string for input file.
    f = StringIO.StringIO(string)

    # Create another file like object from string for output file,
    # unless we have been handed one by recursive call.

    if output_file is None:
        g = StringIO.StringIO(u'')
    else:
        g = output_file

    # When comparing to the RFC1341 code, substitute:
    # STDIN -> object f
    # STDOUT -> object g
    # EOF -> ''
    # ungetc -> seek(-1,1)

    # If we're not calling ourself from ISO-8859-X tag, then eat
    # leading newlines:

    if not recursive: _eat_all(f,'\n')

    c = f.read(1)

    # compile re for use in if then else. Matches 'iso-8859-XX' tags
    # where xx are digits.
    iso_re = re.compile(r'^iso-8859-([1-9][0-9]?)$', re.IGNORECASE)
    iso_close_re = re.compile(r'^/iso-8859-([1-9][0-9]?)$', re.IGNORECASE)

    while c != '':
        if c == '<':

            c, token = _read_token(f)

            if c == '': break

            if token == 'lt':
                g.write('<')

                just_closed_para = False
            elif token == 'nl':

                g.write('\n')

                # Discard all 'soft newlines' following <nl> token:
                _eat_all(f,'\n')

            elif token == 'np':

                g.write('\n\n\n')

                # Discard all 'soft newlines' following <np> token:
                _eat_all(f,'\n')

                just_closed_para = True

            elif token == 'paragraph':

                # If we haven't just closed a paragraph tag, or done
                # equivalent (eg. output an <np> tag) then produce
                # newlines to offset paragraph:

                if not just_closed_para: g.write('\n\n')

            elif token == '/paragraph':
                g.write('\n\n')

                # Discard all 'soft newlines' following </paragraph> token:
                _eat_all(f,'\n')

                just_closed_para = True

            elif token == 'comment':
                commct=1

                while commct > 0:

                    c = _throw_away_until(f,'<') # Bin characters until we get a '<'

                    if c == '': break

                    c, token = _read_token(f)

                    if c == '': break

                    if token == '/comment':
                        commct -= 1
                    elif token == 'comment':
                        commct += 1

            elif iso_re.match(token):

                if not convert_iso_8859_tags:
                    if not force_conversion:
                        raise ISO8859TagError("<iso-8859-x> tag found when convert_iso_8859_tags=False")
                    else:
                        pass
                else:
                    # Read in from the input file, stopping to look at
                    # each tag. Keep reading until we have a balanced pair
                    # of <iso-8859-x></iso-8859-x> tags. Use tag_balance
                    # to keep track of how many open iso-8859 tags we
                    # have, since nesting is legal. When tag_balance hits
                    # 0 we have found a balanced pair.

                    tag_balance = 1
                    iso_str = ''

                    while tag_balance != 0:

                        c, next_str = _read_to_next_token(f)

                        iso_str += next_str

                        if c == '': break

                        c, next_token = _read_token(f)

                        if c == '': break

                        if next_token == token:
                            tag_balance += 1
                        elif next_token == '/' + token:
                            tag_balance -= 1

                        if tag_balance != 0:
                            iso_str += ('<' + next_token + '>')

                    # We now have a complete string of text in the
                    # foreign charset in iso_str, so we call ourself
                    # to process it.  No need to consider return
                    # value, since we pass g and all the output gets
                    # written to this.

                    _richtext2txt(iso_str, charset, convert_iso_8859_tags, force_conversion,
                                  True, just_closed_para, output_file=g)
                                 #^^^^ = recursive

            elif iso_close_re.match(token):

                if force_conversion:
                    pass
                else:
                    if convert_iso_8859_tags:
                        raise ISO8859TagError("closing </iso-8859-x> tag before opening tag")
                    else:
                        raise ISO8859TagError("</iso-8859-x> tag found when convert_iso_8859_tags=False")
            else:
                # Ignore unrecognized token.
                pass

        elif c == '\n':

            # Read in contiguous string of newlines and output them as
            # single space, unless we hit EOF, in which case output
            # nothing.

            _eat_all(f,'\n')

            if _next_char(f) == '': break

            # If we have just written a newline out, soft newlines
            # should do nothing:
            if _last_char(g) != '\n': g.write(' ')

        else:
            # We have a 'normal char' so just write it out:
            _unicode_write(g, c, charset, force_conversion)

            just_closed_para = False

        c = f.read(1)

    # Only output the terminating newline if we aren't being called
    # recursively.
    if not recursive:
        g.write('\n')

    return g.getvalue()

def _read_token(f):
    """
    Read in token from inside a markup tag.
    """

    token = ""

    c = f.read(1)

    while c != '' and c!= '>':
        token += c
        c = f.read(1)

    token = token.lower()

    return c, token

def _read_to_next_token(f):

    out = ''

    c = f.read(1)
    while c != '<' and c != '':
        out += c
        c = f.read(1)

    return c, out

def _eat_all(f,d):

    """
    Discard all characters from input stream f of type d until we hit
    a character that is not of type d. Return the most recent bit read
    from the file.
    """

    got_char = False

    if _next_char(f) == d: got_char = True

    while _next_char(f) == d: f.read(1)

    if got_char:
        return d
    else:
        return None

def _throw_away_until(f,d):
    """
    Discard all characters from input stream f until we hit a
    character of type d. Discard this char also. Return the most
    recent bit read from the file (which will either be d or EOF).
    """

    c = f.read(1)
    while c != d and c != '': c = f.read(1)

    return c

def _next_char(f):
    """
    Return the next char in the file.
    """

    # Get the char:
    c = f.read(1)

    # If it wasn't an EOF, backup one, otherwise stay put:
    if c != '': f.seek(-1,1)

    return c

def _last_char(g):
    """
    Look at what the last character written to a file was.
    """

    pos = g.tell()

    if pos == 0:
        # At the start of the file.
        return None
    else:
        # Written at least one character, so step back one and read it
        # off.
        g.seek(-1,1)
        return g.read(1)

def _unicode_write(g, string, charset, force_conversion):

    strictness = { True : 'strict',
                   False: 'replace'}[force_conversion]

    # Could raise a UnicodeDecodingError!
    unicode_str = unicode(string, charset, strictness)

    g.write(unicode_str)

class RichTextConversionError(Exception):

    """
    An emtpy parent class for all errors in this module.
    """

    pass

class ISO8859TagError(RichTextConversionError):

    """
    This error is raised when we are doing a conversion with
    strict=True, the input string is unicode and we get an iso-8859-x
    tag. Unicode should not contain mixed charsets.
    """

    pass

# The original C code direct from RFC1341, appendix D
# See: http://www.faqs.org/rfcs/rfc1341.html

# #include <stdio.h>
# #include <ctype.h>
# main() {
#   int c, i;
#   char token[50];

#   while((c = getc(stdin)) != EOF) {
#     if (c == '<') {
#       for (i=0; (i<49 && (c = getc(stdin)) != '>' && c != EOF); ++i) {
#         token[i] = isupper(c) ? tolower(c) : c;
#       }
#       if (c == EOF) break;
#       if (c != '>') while ((c = getc(stdin)) != '>' && c != EOF) {;}
#       if (c == EOF) break;
#       token[i] = '\0';
#       if (!strcmp(token, "lt")) {
#         putc('<', stdout);
#       } else if (!strcmp(token, "nl")) {
#         putc('\n', stdout);
#       } else if (!strcmp(token, "/paragraph")) {
#         fputs("\n\n", stdout);
#       } else if (!strcmp(token, "comment")) {
#         int commct=1;
#         while (commct > 0) {
#           while ((c = getc(stdin)) != '<'
#                  && c != EOF) ;
#           if (c == EOF) break;
#           for (i=0; (c = getc(stdin)) != '>'
#                  && c != EOF; ++i) {
#             token[i] = isupper(c) ?
#               tolower(c) : c;
#           }
#           if (c== EOF) break;
#           token[i] = NULL;
#           if (!strcmp(token, "/comment")) --commct;
#           if (!strcmp(token, "comment")) ++commct;
#         }
#       } /* Ignore all other tokens */
#     } else if (c != '\n') putc(c, stdout);
#   }
#   putc('\n', stdout); /* for good measure */
# }

# data = open('sample.rtx','r')
# t = data.read()


