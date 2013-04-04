# This file is part of Invenio.
# Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
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

"""BibClassify's web interface."""

#FIXME: some links are not fully functional.
#FIXME: the display panel should be prettified.
#FIXME: the business logic and the display should be separated into
#       dedicated engine and HTML template layers.
#FIXME: the output strings should be I18N-ized.

import os
from cgi import escape
from urllib import quote
import time

from invenio.bibrecord import record_xml_output
from invenio.config import CFG_SITE_URL
from invenio.webinterface_handler import wash_urlargd
from invenio.search_engine import perform_request_search, get_record
from invenio.htmlutils import escape_html
from invenio.bibclassify_text_extractor import is_pdf
from invenio.bibdocfile import BibRecDocs
from invenio.bibclassify_engine import output_marc
from invenio.config import CFG_TMPDIR

DEFAULT_OPTS = {
    'type': 'tagcloud',
    'sort': 'occurrences',
    'numbering': 'off',
    'generate': 'no',
    }

def extend_argd(argd):
    for type, value in DEFAULT_OPTS.items():
        if type not in argd:
            argd[type] = value
    return argd

def _http_get_argument_string(argd, *options):
    """Returns the string of HTTP GET options. Only non-default
    options are considered."""
    get_options = {}
    # First get the current options.
    for option, value in argd.items():
        if option not in DEFAULT_OPTS:
            get_options[option] = value
        elif option not in zip(*options)[0] and \
            value != DEFAULT_OPTS[option]:
            get_options[option] = value
    # Then add the new options.
    for option, value in options:
        if value != DEFAULT_OPTS[option]:
            get_options[option] = value

    if 'generate' in get_options:
        del get_options['generate']

    if not get_options:
        return ""
    else:
        return '?' + '&'.join(['%s=%s' % (option, value)
            for option, value in get_options.items()])

def get_keywords_body(keywords, req, recid, argd):
    """Returns the body associated with the keywords."""
    body = []
    rec = get_record(recid)

    extend_argd(argd)

    if keywords:
        weights_available = 0 not in zip(*keywords)[1]
    else:
        req.write('There are no keywords associated with this document.<br>' \
            '<form action="" method="get">' \
            '  <input type="hidden" name="generate" value="yes">' \
            '  <input type="submit" value="Generate keywords">' \
            '</form>')
        return

    if argd['type'] == 'tagcloud' and not weights_available:
        # No weight is specified for at least one of the keywords.
        # Display the keywords as a list.
        argd['type'] = 'list'

    if argd['type'] == 'tagcloud':
        body.append('<div style="text-align: center; color: red; '
            'font-size: 80%; margin-top: 15px">Single keywords in grey, '
            'composite keywords in blue.</div>')

    if argd['type'] == 'list':
        # Display keywords as a list.
        body.append(_get_keywords_list(keywords, argd))
    elif argd['type'] == 'tagcloud':
        if argd['sort'] == 'related' and not keywords:
            print 'No similar document was found.'

        # Separate single and composite keywords.
        single_keywords, composite_keywords = [], []
        for keyword in keywords:
            if ': ' in keyword[0]:
                composite_keywords.append(keyword)
            else:
                single_keywords.append(keyword)

        # Display keywords as a tag cloud.
        single_levels = _get_font_levels(single_keywords)
        composite_levels = _get_font_levels(composite_keywords)

        body.append(_get_html_tag_cloud(single_levels +
            composite_levels, argd))
    elif argd['type'] == 'xml':
        body.append('<pre><code>%s</code></pre>' %
            escape_html(record_xml_output(rec, ['653'])))
    else:
        body = 'Unknown type: ' + argd['type']

    out = ''
    for element in body:
        out += '<br>' + element.encode('utf-8')
    req.write(out)
    return

def _get_font_levels(keywords):
    """Takes keywords (a list of tuple (item, weight)) and
    returns (item, weight, fontlevel)."""
    # Extract the weights from the keywords.
    try:
        weights = zip(*keywords)[1]
    except IndexError:
        return keywords

    # Define the range of fonts.
    f_number = 8

    # Get some necessary values.
    w_min = float(min(weights))
    w_max = float(max(weights))

    # Compute the distribution function.
    if w_max == w_min:
        level = 1
    else:
        slope = f_number / (w_max - w_min)
        y_intercept = - w_min * slope
        level = lambda weight: int(slope * weight + y_intercept)

    # Compute the font level for each weight.
    for keyword in keywords:
        if keyword[1] == w_max:
            keyword.append(f_number - 1)
        else:
            keyword.append(level(keyword[1]))

    return keywords

def _get_keywords_list(keywords, argd):
    """Returns a list output of the keywords."""
    # Separate keywords with and without weight, and single and
    # composite keywords.
    sorted_keywords = {
        'unweighted': {'single': [], 'composite': []},
        'weighted': {'single': [], 'composite': []}
        }

    for keyword, weight in keywords:
        state = 'single'
        weighted = 'weighted'
        if ': ' in keyword:
            state = 'composite'
        if weight == 0:
            weighted = 'unweighted'
        sorted_keywords[weighted][state].append((escape(keyword), weight))

    out = []

    if sorted_keywords['unweighted']['composite']:
        out.append('<b>Unweighted composite keywords:</b>')
        sorted_keywords['unweighted']['composite'].sort(lambda x, y:
            cmp(x[0].lower(), y[0].lower()))
        for keyword, _ in sorted_keywords['unweighted']['composite']:
            out.append(keyword)

    if sorted_keywords['unweighted']['single']:
        out.append('<b>Unweighted single keywords:</b>')
        sorted_keywords['unweighted']['single'].sort(lambda x, y:
            cmp(x[0].lower(), y[0].lower()))
        for keyword, _ in sorted_keywords['unweighted']['single']:
            out.append(keyword)

    if sorted_keywords['weighted']['composite']:
        out.append('<b>Weighted composite keywords:</b>')
        sorted_keywords['weighted']['composite'].sort(lambda x, y:
            cmp(y[1], x[1]) or cmp(x[0].lower(), y[0].lower()))
        for keyword, weight in sorted_keywords['weighted']['composite']:
            if argd['numbering'] == 'on':
                out.append("%s (%d)" % (keyword, weight))
            else:
                out.append(keyword)

    if sorted_keywords['weighted']['single']:
        out.append('<b>Weighted single keywords:</b>')
        sorted_keywords['weighted']['single'].sort(lambda x, y:
            cmp(y[1], x[1]) or cmp(x[0].lower(), y[0].lower()))
        for keyword, weight in sorted_keywords['weighted']['single']:
            if argd['numbering'] == 'on':
                out.append("%s (%d)" % (keyword, weight))
            else:
                out.append(keyword)

    return '<div style="width: 60%; float: top; margin-left: 20%; ' \
        'margin-top: 20px; margin-bottom: 20px; font-family: Arial, ' \
        'Helvetica, sans-serif; ">' + '<br>'.join(out) + \
        '</div>'

def _get_html_tag_cloud(information, argd):
    """Returns a formatted tag cloud."""
    sort_method = lambda x, y: cmp(x[0].lower(), y[0].lower()) or \
                               cmp(y[1], x[1])
    information.sort(sort_method)

    # Define the range of fonts.
    f_min = 12
    f_increment = 3
    f_number = 8
    fonts = [f_min + i * f_increment for i in range(f_number)]

    cloud = []

    cloud.append('<div class="tagCloud" '
                     'style="width: 60%; '
                            'float: top; '
                            'margin-left: 20%; '
                            'margin-top: 20px; '
                            'margin-bottom: 20px; '
                            '">')

    for keyword, weight, level in information:
        if argd['numbering'] == 'off':
            cloud.append('<span style="font-size: %spx; '
                '">\n\t<a style="color: #%s; " href="%s">%s</a>\n</span>' %
                (fonts[level],
                 ': ' in keyword and '3366CC' or '666666',
                 _kw_search_link(keyword, argd),
                 escape(keyword).replace(' ', '&nbsp;')))
        elif argd['numbering'] == 'on':
            cloud.append('<span><a style="font-size: %spx; color: #%s; " '
                'href="%s">%s&nbsp;(%d)</a></span>' %
                (fonts[level],
                 ': ' in keyword and '3366CC' or '666666',
                 _kw_search_link(keyword, argd),
                 escape(keyword).replace(' ', '&nbsp;'), weight))

    cloud.append('</div>')

    return '\n'.join(cloud)

def _kw_search_link(keyword, argd):
    """Returns a link that searches for a keyword."""
    return """%s/search?f=keyword&amp;p=%s&amp;ln=%s""" % (
        CFG_SITE_URL,
        quote('"%s"' % keyword),
        argd['ln'])

def get_sorting_options(argd, keywords):
    """Returns the HTML view of the sorting options. Takes care of
    enabling only some options based on the page shown."""

    argd = wash_urlargd(argd, {
        'type': (str, DEFAULT_OPTS['type']),
        'sort': (str, DEFAULT_OPTS['sort']),
        'numbering': (str, DEFAULT_OPTS['numbering']),
        'generate': (str, 'no')})

    if keywords:
        weights_available = 0 not in zip(*keywords)[1]
    else:
        weights_available = False

    options = []
    options.append('<div style="text-align: left; margin-left: 10px; font-size: small;">')

    options_str = '<b>Display keywords:</b> '
    if argd['type'] == 'tagcloud':
        options_str += '[tag cloud] '
    else:
        # If type is set to occurrences and there are no weights
        # available, then disable this option.
        if argd['sort'] == 'occurrences' and not weights_available:
            options_str += '[tag cloud] '
        else:
            options_str += '[<a href="%s">tag cloud</a>] ' % \
                _http_get_argument_string(argd, ('type', 'tagcloud'))
    if argd['type'] == 'list':
        options_str += '[list] '
    else:
        options_str += '[<a href="%s">list</a>] ' % \
            _http_get_argument_string(argd, ('type', 'list'))
    if argd['type'] == 'xml':
        options_str += '[XML] '
    else:
        options_str += '[<a href="%s">XML</a>] ' % \
            _http_get_argument_string(argd, ('type', 'xml'))

    options_str += ' <br>  '

    options_str += '<b>Sort keywords:</b> '
    if argd['sort'] == 'occurrences' or argd['type'] == 'xml':
        options_str += '[by occurrences] '
    else:
        options_str += '[<a href="%s">by occurrences</a>] ' % \
            _http_get_argument_string(argd, ('sort', 'occurrences'))
    if argd['sort'] == 'related' or argd['type'] == 'xml':
        options_str += '[by related documents] '
    else:
        options_str += '[<a href="%s">by related documents</a>] ' % \
            _http_get_argument_string(argd, ('sort', 'related'))

    options.append(options_str)
    options.append('</div>')
    return '\n'.join(options)

def record_get_keywords(recid, argd):
    """Returns a list of pairs [keyword, weight] contained in the
    record. Weight is set to 0 if no weight can be found."""
    keywords = []

    rec = get_record(recid)

    for field in rec.get('653', []):
        keyword = ''
        weight = 0
        for subfield in field[0]:
            if subfield[0] == 'a':
                keyword = subfield[1]
            elif subfield[0] == 'n':
                weight = int(subfield[1])
        if argd['sort'] == 'related':
            # Number of related documents minus 1 in order to not
            # consider the source document.
            weight = len(perform_request_search(p='"%s"' % keyword,
                f='keyword'))
            if weight:
                keywords.append([keyword, weight])
        else:
            keywords.append([keyword, weight])

    return keywords

def generate_keywords(req, recid, store_keywords=True):
    req.write("Please be patient while the keywords classification is running...")

    bibdocfiles = BibRecDocs(recid).list_latest_files()

    keywords = []
    for doc in bibdocfiles:
        # Get the keywords for each PDF document contained in the record.
        if is_pdf(doc.get_full_path()):
            fulltext = doc.get_full_path()
            from invenio.bibclassify_engine import get_keywords_from_local_file
            single_keywords, composite_keywords = get_keywords_from_local_file(fulltext,
                taxonomy='HEP', with_author_keywords=True)

            for keyword, spans in single_keywords.items():
                keywords.append([keyword.concept, len(spans)])
            for keyword, num, components in composite_keywords:
                keywords.append([keyword.concept, num])

    if keywords and store_keywords:
        output = ['<collection><record>\n'
                  '<controlfield tag="001">%s</controlfield>' % recid]

        output.append(output_marc(single_keywords, composite_keywords,
        spires=False, taxonomy='HEP'))

        output.append('</record></collection>')

        tmp_directory = "%s/bibclassify" % CFG_TMPDIR
        filename = "bibclassifyd_%s.xml" % time.strftime("%Y%m%d%H%M%S",
            time.localtime())
        abs_path = os.path.join(tmp_directory, filename)

        if not os.path.isdir(tmp_directory):
            os.mkdir(tmp_directory)

        file_desc = open(abs_path, "w")
        file_desc.write('\n'.join(output))
        file_desc.close()

        #cmd = "%s/bibupload -n -c '%s' " % (CFG_BINDIR, abs_path)
        #os.system(cmd)

    return keywords
