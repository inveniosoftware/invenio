# -*- coding: utf-8 -*-

## This file is part of Invenio.
## Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

"""
Functions useful for text wrapping (in a box) and indenting.
"""

__revision__ = "$Id$"

import sys
import re
import textwrap
import invenio.template
from invenio.config import CFG_ETCDIR
try:
    import chardet
    CHARDET_AVAILABLE = True
except ImportError:
    CHARDET_AVAILABLE = False

CFG_LATEX_UNICODE_TRANSLATION_CONST = {}

CFG_WRAP_TEXT_IN_A_BOX_STYLES = {
    '__DEFAULT' : {
        'horiz_sep' : '*',
        'max_col' : 72,
        'min_col' : 40,
        'tab_str' : '    ',
        'tab_num' : 0,
        'border' : ('**', '*', '**', '** ', ' **', '**', '*', '**'),
        'prefix' : '\n',
        'suffix' : '\n',
        'break_long' : False,
        'force_horiz' : False,
    },
    'squared' : {
        'horiz_sep' : '-',
        'border' : ('+', '-', '+', '| ', ' |', '+', '-', '+')
    },
    'double_sharp' : {
        'horiz_sep' : '#',
        'border' : ('##', '#', '##', '## ', ' ##', '##', '#', '##')
    },
    'single_sharp' : {
        'horiz_sep' : '#',
        'border' : ('#', '#', '#', '# ', ' #', '#', '#', '#')
    },
    'single_star' : {
        'border' : ('*', '*', '*', '* ', ' *', '*', '*', '*',)
    },
    'double_star' : {
    },
    'no_border' : {
        'horiz_sep' : '',
        'border' : ('', '', '', '', '', '', '', ''),
        'prefix' : '',
        'suffix' : ''
    },
    'conclusion' : {
        'border' : ('', '', '', '', '', '', '', ''),
        'prefix' : '',
        'horiz_sep' : '-',
        'force_horiz' : True,
    },
    'important' : {
        'tab_num' : 1,
    },
    'ascii' : {
        'horiz_sep' : (u'├', u'─', u'┤'),
        'border' : (u'┌', u'─', u'┐', u'│ ', u' │', u'└', u'─', u'┘'),
    },
    'ascii_double' : {
        'horiz_sep' : (u'╠', u'═', u'╣'),
        'border' : (u'╔', u'═', u'╗', u'║ ', u' ║', u'╚', u'═', u'╝'),
    }

}

def indent_text(text,
                nb_tabs=0,
                tab_str="  ",
                linebreak_input="\n",
                linebreak_output="\n",
                wrap=False):
    """
    add tabs to each line of text
    @param text: the text to indent
    @param nb_tabs: number of tabs to add
    @param tab_str: type of tab (could be, for example "\t", default: 2 spaces
    @param linebreak_input: linebreak on input
    @param linebreak_output: linebreak on output
    @param wrap: wethever to apply smart text wrapping.
        (by means of wrap_text_in_a_box)
    @return: indented text as string
    """
    if not wrap:
        lines = text.split(linebreak_input)
        tabs = nb_tabs*tab_str
        output = ""
        for line in lines:
            output += tabs + line + linebreak_output
        return output
    else:
        return wrap_text_in_a_box(body=text, style='no_border',
            tab_str=tab_str, tab_num=nb_tabs)

_RE_BEGINNING_SPACES = re.compile(r'^\s*')
_RE_NEWLINES_CLEANER = re.compile(r'\n+')
_RE_LONELY_NEWLINES = re.compile(r'\b\n\b')
def wrap_text_in_a_box(body='', title='', style='double_star', **args):
    """Return a nicely formatted text box:
        e.g.
       ******************
       **  title       **
       **--------------**
       **  body        **
       ******************

    Indentation and newline are respected.
    @param body: the main text
    @param title: an optional title
    @param style: the name of one of the style in CFG_WRAP_STYLES. By default
        the double_star style is used.

    You can further tune the desired style by setting various optional
    parameters:
        @param horiz_sep: a string that is repeated in order to produce a
            separator row between the title and the body (if needed)
            or a tuple of three characters in the form (l, c, r)
        @param max_col: the maximum number of coulmns used by the box
            (including indentation)
        @param min_col: the symmetrical minimum number of columns
        @param tab_str: a string to represent indentation
        @param tab_num: the number of leveles of indentations
        @param border: a tuple of 8 element in the form
            (tl, t, tr, l, r, bl, b, br) of strings that represent the
            different corners and sides of the box
        @param prefix: a prefix string added before the box
        @param suffix: a suffix string added after the box
        @param break_long: wethever to break long words in order to respect
            max_col
        @param force_horiz: True in order to print the horizontal line even when
            there is no title

    e.g.:
    print wrap_text_in_a_box(title='prova',
        body='  123 prova.\n    Vediamo come si indenta',
        horiz_sep='-', style='no_border', max_col=20, tab_num=1)

        prova
        ----------------
        123 prova.
            Vediamo come
            si indenta

    """

    def _wrap_row(row, max_col, break_long):
        """Wrap a single row"""
        spaces = _RE_BEGINNING_SPACES.match(row).group()
        row = row[len(spaces):]
        spaces = spaces.expandtabs()
        return textwrap.wrap(row, initial_indent=spaces,
            subsequent_indent=spaces, width=max_col,
            break_long_words=break_long)

    def _clean_newlines(text):
        text = _RE_LONELY_NEWLINES.sub(' \n', text)
        return _RE_NEWLINES_CLEANER.sub(lambda x: x.group()[:-1], text)

    body = unicode(body, 'utf-8')
    title = unicode(title, 'utf-8')

    astyle = dict(CFG_WRAP_TEXT_IN_A_BOX_STYLES['__DEFAULT'])
    if CFG_WRAP_TEXT_IN_A_BOX_STYLES.has_key(style):
        astyle.update(CFG_WRAP_TEXT_IN_A_BOX_STYLES[style])
    astyle.update(args)

    horiz_sep = astyle['horiz_sep']
    border = astyle['border']
    tab_str = astyle['tab_str'] * astyle['tab_num']
    max_col = max(astyle['max_col'] \
        - len(border[3]) - len(border[4]) - len(tab_str), 1)
    min_col = astyle['min_col']
    prefix = astyle['prefix']
    suffix = astyle['suffix']
    force_horiz = astyle['force_horiz']
    break_long = astyle['break_long']

    body = _clean_newlines(body)
    tmp_rows = [_wrap_row(row, max_col, break_long)
                        for row in body.split('\n')]
    body_rows = []
    for rows in tmp_rows:
        if rows:
            body_rows += rows
        else:
            body_rows.append('')
    if not ''.join(body_rows).strip():
        # Concrete empty body
        body_rows = []

    title = _clean_newlines(title)
    tmp_rows = [_wrap_row(row, max_col, break_long)
                        for row in title.split('\n')]
    title_rows = []
    for rows in tmp_rows:
        if rows:
            title_rows += rows
        else:
            title_rows.append('')
    if not ''.join(title_rows).strip():
        # Concrete empty title
        title_rows = []

    max_col = max([len(row) for row in body_rows + title_rows] + [min_col])

    mid_top_border_len = max_col \
        + len(border[3]) + len(border[4]) - len(border[0]) - len(border[2])
    mid_bottom_border_len = max_col \
        + len(border[3]) + len(border[4]) - len(border[5]) - len(border[7])
    top_border = border[0] \
        + (border[1] * mid_top_border_len)[:mid_top_border_len] + border[2]
    bottom_border = border[5] \
        + (border[6] * mid_bottom_border_len)[:mid_bottom_border_len] \
        + border[7]
    if type(horiz_sep) is tuple and len(horiz_sep) == 3:
        horiz_line = horiz_sep[0] + (horiz_sep[1] * (max_col + 2))[:(max_col + 2)] + horiz_sep[2]
    else:
        horiz_line = border[3] + (horiz_sep * max_col)[:max_col] + border[4]

    title_rows = [tab_str + border[3] + row
        + ' ' * (max_col - len(row)) + border[4] for row in title_rows]
    body_rows = [tab_str + border[3] + row
        + ' ' * (max_col - len(row)) + border[4] for row in body_rows]

    ret = []
    if top_border:
        ret += [tab_str + top_border]
    ret += title_rows
    if title_rows or force_horiz:
        ret += [tab_str + horiz_line]
    ret += body_rows
    if bottom_border:
        ret += [tab_str + bottom_border]
    return (prefix + '\n'.join(ret) + suffix).encode('utf-8')

def wait_for_user(msg=""):
    """
    Print MSG and a confirmation prompt, waiting for user's
    confirmation, unless silent '--yes-i-know' command line option was
    used, in which case the function returns immediately without
    printing anything.
    """
    if '--yes-i-know' in sys.argv:
        return
    print msg
    try:
        answer = raw_input("Please confirm by typing 'Yes, I know!': ")
    except KeyboardInterrupt:
        print
        answer = ''
    if answer != 'Yes, I know!':
        sys.stderr.write("ERROR: Aborted.\n")
        sys.exit(1)
    return

def guess_minimum_encoding(text, charsets=('ascii', 'latin1', 'utf8')):
    """Try to guess the minimum charset that is able to represent the given
    text using the provided charsets. text is supposed to be encoded in utf8.
    Returns (encoded_text, charset) where charset is the first charset
    in the sequence being able to encode text.
    Returns (text_in_utf8, 'utf8') in case no charset is able to encode text.

    @note: If the input text is not in strict UTF-8, then replace any
        non-UTF-8 chars inside it.
    """
    text_in_unicode = text.decode('utf8', 'replace')
    for charset in charsets:
        try:
            return (text_in_unicode.encode(charset), charset)
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return (text_in_unicode.encode('utf8'), 'utf8')

def encode_for_xml(text, wash=False, xml_version='1.0', quote=False):
    """Encodes special characters in a text so that it would be
    XML-compliant.
    @param text: text to encode
    @return: an encoded text"""
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    if quote:
        text = text.replace('"', '&quot;')
    if wash:
        text = wash_for_xml(text, xml_version=xml_version)
    return text

try:
    unichr(0x100000)
    RE_ALLOWED_XML_1_0_CHARS = re.compile(u'[^\U00000009\U0000000A\U0000000D\U00000020-\U0000D7FF\U0000E000-\U0000FFFD\U00010000-\U0010FFFF]')
    RE_ALLOWED_XML_1_1_CHARS = re.compile(u'[^\U00000001-\U0000D7FF\U0000E000-\U0000FFFD\U00010000-\U0010FFFF]')
except ValueError:
    # oops, we are running on a narrow UTF/UCS Python build,
    # so we have to limit the UTF/UCS char range:
    RE_ALLOWED_XML_1_0_CHARS = re.compile(u'[^\U00000009\U0000000A\U0000000D\U00000020-\U0000D7FF\U0000E000-\U0000FFFD]')
    RE_ALLOWED_XML_1_1_CHARS = re.compile(u'[^\U00000001-\U0000D7FF\U0000E000-\U0000FFFD]')

def wash_for_xml(text, xml_version='1.0'):
    """
    Removes any character which is not in the range of allowed
    characters for XML. The allowed characters depends on the version
    of XML.

        - XML 1.0:
            <http://www.w3.org/TR/REC-xml/#charsets>
        - XML 1.1:
            <http://www.w3.org/TR/xml11/#charsets>

    @param text: input string to wash.
    @param xml_version: version of the XML for which we wash the
        input. Value for this parameter can be '1.0' or '1.1'
    """
    if xml_version == '1.0':
        return RE_ALLOWED_XML_1_0_CHARS.sub('', unicode(text, 'utf-8')).encode('utf-8')
    else:
        return RE_ALLOWED_XML_1_1_CHARS.sub('', unicode(text, 'utf-8')).encode('utf-8')

def wash_for_utf8(text, correct=True):
    """Return UTF-8 encoded binary string with incorrect characters washed away.

    @param text: input string to wash (can be either a binary string or a Unicode string)
    @param correct: whether to correct bad characters or throw exception
    """
    if isinstance(text, unicode):
        return text.encode('utf-8')

    ret = []
    while True:
        try:
            text.decode("utf-8")
        except UnicodeDecodeError, e:
            if correct:
                ret.append(text[:e.start])
                text = text[e.end:]
            else:
                raise e
        else:
            break
    ret.append(text)
    return ''.join(ret)

def nice_size(size):
    """
    @param size: the size.
    @type size: int
    @return: a nicely printed size.
    @rtype: string
    """
    websearch_templates = invenio.template.load('websearch')
    unit = 'B'
    if size > 1024:
        size /= 1024.0
        unit = 'KB'
        if size > 1024:
            size /= 1024.0
            unit = 'MB'
            if size > 1024:
                size /= 1024.0
                unit = 'GB'
    return '%s %s' % (websearch_templates.tmpl_nice_number(size, max_ndigits_after_dot=2), unit)

def remove_line_breaks(text):
    """
    Remove line breaks from input, including unicode 'line
    separator', 'paragraph separator', and 'next line' characters.
    """
    return unicode(text, 'utf-8').replace('\f', '').replace('\n', '').replace('\r', '').replace(u'\xe2\x80\xa8', '').replace(u'\xe2\x80\xa9', '').replace(u'\xc2\x85', '').encode('utf-8')

def decode_to_unicode(text, failover_encoding='utf-8'):
    """
    Decode input text into Unicode representation by first attempting to detect
    the type of encoding used in the given text. This is useful when input encoding
    is unknown.

    For optimal results, it is recommended that the chardet module is installed.
    NOTE: Beware that this might be slow for large strings.

    If chardet detection fails, it will try to decode the string using the basic
    detection function guess_minimum_encoding(). Should that fail, it will decode
    the string in the given "failover-encoding" (defaults to UTF-8).

    Also, bear in mind that it is impossible to detect the correct encoding at all
    times, other then taking educated guesses. With that said, this function will
    always return some decoded Unicode string, however the data returned may not
    be the same as original data in some cases.

    @param text: the text to decode
    @type text: string

    @param failover_encoding: the 'backup' character encoding to use. Optional.
    @type failover_encoding: string

    @return: input text as Unicode
    @rtype: string
    """
    detected_encoding = None
    if CHARDET_AVAILABLE:
        # We can use chardet to perform detection
        res = chardet.detect(text)
        if res['confidence'] >= 0.8:
            detected_encoding = res['encoding']
    if detected_encoding == None:
        # chardet unsuccessful, then try to make a basic guess
        dummy, detected_encoding = guess_minimum_encoding(text)
    try:
        return text.decode(detected_encoding)
    except (UnicodeError, LookupError):
        pass
    return text.decode(failover_encoding)

def translate_latex2unicode(text, kb_file="%s/bibconvert/KB/latex-to-unicode.kb" % \
                            (CFG_ETCDIR,)):
    """
    This function will take given text, presumably containing LaTeX symbols,
    and attempts to translate it to Unicode using the given or default KB
    translation table located under CFG_ETCDIR/bibconvert/KB/latex-to-unicode.kb.
    The translated Unicode string will then be returned.

    If the translation table and compiled regular expression object is not
    previously generated in the current session, they will be.

    @param text: a text presumably containing LaTeX symbols.
    @type text: string

    @param kb_file: full path to file containing latex2unicode translations.
                    Defaults to CFG_ETCDIR/bibconvert/KB/latex-to-unicode.kb
    @type kb_file: string

    @return: Unicode representation of translated text
    @rtype: unicode
    """
    # First decode input text to Unicode
    try:
        text = decode_to_unicode(text)
    except UnicodeDecodeError:
        text = unicode(wash_for_utf8(text))
    # Load translation table, if required
    if CFG_LATEX_UNICODE_TRANSLATION_CONST == {}:
        _load_latex2unicode_constants(kb_file)
    # Find all matches and replace text
    for match in CFG_LATEX_UNICODE_TRANSLATION_CONST['regexp_obj'].finditer(text):
        # If LaTeX style markers {, } and $ are before or after the matching text, it
        # will replace those as well
        text = re.sub("[\{\$]?%s[\}\$]?" % (re.escape(match.group()),), \
                      CFG_LATEX_UNICODE_TRANSLATION_CONST['table'][match.group()], \
                      text)
    # Return Unicode representation of translated text
    return text

def _load_latex2unicode_constants(kb_file="%s/bibconvert/KB/latex-to-unicode.kb" % \
                            (CFG_ETCDIR,)):
    """
    Load LaTeX2Unicode translation table dictionary and regular expression object
    from KB to a global dictionary.

    @param kb_file: full path to file containing latex2unicode translations.
                    Defaults to CFG_ETCDIR/bibconvert/KB/latex-to-unicode.kb
    @type kb_file: string

    @return: dict of type: {'regexp_obj': regexp match object,
                            'table': dict of LaTeX -> Unicode mappings}
    @rtype: dict
    """
    try:
        data = open(kb_file)
    except IOError:
        # File not found or similar
        sys.stderr.write("\nCould not open LaTeX to Unicode KB file. Aborting translation.\n")
        return CFG_LATEX_UNICODE_TRANSLATION_CONST
    latex_symbols = []
    translation_table = {}
    for line in data:
        # The file has form of latex|--|utf-8. First decode to Unicode.
        line = line.decode('utf-8')
        mapping = line.split('|--|')
        translation_table[mapping[0].rstrip('\n')] = mapping[1].rstrip('\n')
        latex_symbols.append(re.escape(mapping[0].rstrip('\n')))
    data.close()
    CFG_LATEX_UNICODE_TRANSLATION_CONST['regexp_obj'] = re.compile("|".join(latex_symbols))
    CFG_LATEX_UNICODE_TRANSLATION_CONST['table'] = translation_table
