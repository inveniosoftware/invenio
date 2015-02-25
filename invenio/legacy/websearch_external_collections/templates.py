# -*- coding: utf-8 -*-

# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2010, 2011 CERN.
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

"""Template for the external collections search."""

__revision__ = "$Id$"

import cgi

from invenio.config import CFG_SITE_LANG
from invenio.base.i18n import gettext_set_language
from invenio.utils.url import create_html_link

class Template:
    """Template class for the external collection search. To be loaded with template.load()"""
    def __init__(self):
        pass

    def external_collection_seealso_box(self, lang, links,
            prolog_start='<table class="externalcollectionsbox"><tr><th colspan="2" class="externalcollectionsboxheader">',
            prolog_end='</th></tr><tr><td class="externalcollectionsboxbody">',
            column_separator='</td><td class="externalcollectionsboxbody">',
            link_separator= '<br />', epilog='</td></tr></table>'):
        """Creates the box that proposes links to other useful search engines like Google.
        lang: string - The language to display in
        links: list of string - List of links to display in the box
        prolog_start, prolog_end, column_separator, link_separator, epilog': strings -
            default HTML code for the specified position in the box"""
        _ = gettext_set_language(lang)

        out = ""
        if links:
            out += '<a name="externalcollectionsbox"></a>'
            out += prolog_start
            out += _("Haven't found what you were looking for? Try your search on other servers:")
            out += prolog_end
            nb_out_links_in_one_column = len(links)/2 + len(links) % 2
            out += link_separator.join(links[:nb_out_links_in_one_column])
            out += column_separator
            out += link_separator.join(links[nb_out_links_in_one_column:])
            out += epilog
        return out

    def external_collection_overview(self, lang=CFG_SITE_LANG, engine_list=()):
        """Prints results overview box with links to particular collections below.
        lang: The language to display
        engine_list: The external engines to be used"""

        if len(engine_list) < 1:
            return ""

        _ = gettext_set_language(lang)

        out = """
  <table class="externalcollectionsresultsbox">
    <thead>
      <tr>
        <th class="externalcollectionsresultsboxheader"><strong>%s</strong></th>
      </tr>
    </thead>
      <tbody>
        <tr>
          <td class="externalcollectionsresultsboxbody"> """ % _("External collections results overview:")

        for engine in engine_list:
            internal_name = get_link_name(engine.name)
            name = _(engine.name)
            out += """<strong><a href="#%(internal_name)s">%(name)s</a></strong><br />""" % locals()
        out += """
        </td>
      </tr>
    </tbody>
  </table>
  """
        return out

def print_info_line(req,
                    html_external_engine_name_box,
                    html_external_engine_nb_results_box,
                    html_external_engine_nb_seconds_box):
    """Print on req an information line about results of an external collection search."""

    req.write('<table class="externalcollectionsresultsbox"><tr>')
    req.write('<td class="externalcollectionsresultsboxheader">')
    req.write('<big><strong>' + \
               html_external_engine_name_box + \
               '</strong></big>')
    req.write('&nbsp;&nbsp;&nbsp;')
    req.write(html_external_engine_nb_results_box)
    req.write('</td><td class="externalcollectionsresultsboxheader" width="20%" align="right">')
    req.write('<small>' + \
              html_external_engine_nb_seconds_box + \
              '</small>')
    req.write('</td></tr></table><br />')

def print_timeout(req, lang, engine, name, url):
    """Print info line for timeout."""
    _ = gettext_set_language(lang)
    req.write('<a name="%s"></a>' % get_link_name(engine.name))
    print_info_line(req,
                    create_html_link(url, {}, name, {}, False, False),
                    '',
                    _('Search timed out.'))
    message = _("The external search engine has not responded in time. You can check its results here:")
    req.write(message + ' ' + create_html_link(url, {}, name, {}, False, False) + '<br />')

def get_link_name(name):
    """Return a hash string for the string name."""
    return hex(abs(name.__hash__()))

def print_results(req, lang, pagegetter, infos, current_time, print_search_info=True, print_body=True):
    """Print results of a given search engine.
    current_time is actually the duration, expressed in seconds of execution of request.
    """
    _ = gettext_set_language(lang)
    url = infos[0]
    engine = infos[1]
    internal_name = get_link_name(engine.name)
    name = _(engine.name)
    base_url = engine.base_url

    results = engine.parser.parse_and_get_results(pagegetter.data)

    html_tit = make_url(name, base_url)

    if print_search_info:
        num = format_number(engine.parser.parse_num_results())
        if num:
            if num == '0':
                html_num = _('No results found.')
                html_sec = ''
            else:
                html_num = '<strong>' + \
                           make_url(_('%(x_res)s results found', x_res=num), url) + \
                           '</strong>'
                html_sec = '(' + _('%(x_sec)s seconds', x_sec=('%2.2f' % current_time)) + ')'
        else:
            html_num = _('No results found.')
            html_sec = ''

        req.write('<a name="%(internal_name)s"></a>' % locals())
        print_info_line(req,
                    html_tit,
                    html_num,
                    html_sec)

    if print_body:
        for result in results:
            req.write(result.html + '<br />')

        if not results:
            req.write(_('No results found.') + '<br />')

def make_url(name, url):
    if url:
        return '<a href="' + cgi.escape(url) + '">' + name + '</a>'
    else:
        return name

def format_number(num, separator=','):
    """Format a number by separating thousands with a separator (by default a comma)

    >>> format_number(10)
    '10'
    >>> format_number(10000)
    '10,000'
    >>> format_number('  000213212424249  ', '.')
    '213.212.424.249'
    """
    result = ""
    try:
        num = int(num)
    except:
        return None
    if num == 0:
        return '0'
    while num > 0:
        part = num % 1000
        num = num / 1000
        result = "%03d" % part + separator + result
    return result.strip('0').strip(separator)
