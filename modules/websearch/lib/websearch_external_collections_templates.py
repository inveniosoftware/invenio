# -*- coding: utf-8 -*-
## $Id$

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Template for the external collections search."""

__revision__ = "$Id$"

from invenio.config import cdslang
from invenio.messages import gettext_set_language

class Template:
    """Template class for the external collection search. To be loaded with template.load()"""
    def __init__(self):
        pass

    def external_collection_seealso_box(self, lang, links, 
            prolog_start='<table class="externalcollectionsbox"><tr><th colspan="2" class="externalcollectionsboxheader">',
            prolog_end='</th></tr><tr><td class="externalcollectionsboxbody">',
            column_separator='</td><td class="externalcollectionsboxbody">',
            link_separator= '<br>', epilog='</td></tr></table>'):
        """Creates the box that proposes links to other useful search engines like Google.
        lang: string - The language to display in
        links: list of string - List of links to display in the box
        prolog_start, prolog_end, column_separator, link_separator, epilog': strings - 
            default HTML code for the specified position in the box"""
        _ = gettext_set_language(lang)

        out = ""
        if links:
            out += """<a name="externalcollectionsbox"></a>"""
            out += prolog_start + _("Haven't found what you were looking for? Try your search on other servers:") + prolog_end
            nb_out_links_in_one_column = len(links)/2 + len(links) % 2
            out += link_separator.join(links[:nb_out_links_in_one_column])
            out += column_separator
            out += link_separator.join(links[nb_out_links_in_one_column:])
            out += epilog
        return out

    def external_collection_overview(self, lang=cdslang, engine_list=()):
        """Prints results overview box with links to particular collections below.
        lang: The language to display
        engine_list: The external engines to be used"""

        if len(engine_list) <= 1:
            return ""

        _ = gettext_set_language(lang)

        out = """<p><table class="externalcollectionsresultsbox">
            <thead><tr><th class="externalcollectionsresultsboxheader"><strong>%(overview_title)s</strong></th></tr></thead>
            <tbody><tr><td class="externalcollectionsresultsboxbody"> """ % {
            'overview_title' : _("Results from external collections overview:") }

        for engine in engine_list:
            internal_name = get_link_name(engine.name)
            name = _(engine.name)
            out += '''<strong><a href="#%(internal_name)s">%(name)s</a></strong><br>''' % locals()
        out += "</td></tr></tbody></table>"
        return out

def print_info_line(req, html1, html2):
    """Print an information line on req."""
    req.write('<table class="externalcollectionsresultsbox"><tr><td class="externalcollectionsresultsboxheader" align="left" width=50%><strong><big>')
    req.write(html1)
    req.write('</big></strong></td><td class="externalcollectionsresultsboxheader" align="center">')
    req.write(html2)
    req.write('</td></tr></table><br>')

def print_timeout(req, lang, engine, name, url):
    """Print info line for timeout."""
    _ = gettext_set_language(lang)
    req.write('<a name="%s">' % get_link_name(engine.name))
    print_info_line(req, '<a href="%(url)s">%(name)s</a>' % {'url': url, 'name': name}, _('Timeout'))
    req.write(_('The external search engine has not responded in time. You can check results here : <a href="%(url)s">%(name)s</a>') % locals() + '<br>')

def get_link_name(name):
    """Return a hash string for the string name."""
    return hex(abs(name.__hash__()))

def print_results(req, lang, pagegetter, infos, current_time):
    """Print results of a given search engine."""
    _ = gettext_set_language(lang)
    url = infos[0]
    engine = infos[1]    

    results = engine.parser.parse_and_get_results(pagegetter.data)
    num = format_number(engine.parser.parse_num_results())

    html2 = _("Time : %2.3f") % current_time
    if num:
        num = _('%(num)s results found') % {'num': num}
    else:
        num = _('See results')
    if num == '0':
        num = _('No result found')
    #if num:
    #    html2 += ", "
    #    html2 += _("Number of results : %(num_results)s") % {'num_results': num}

    internal_name = get_link_name(engine.name)
    name = _(engine.name)
    base_url = engine.base_url
    req.write('<a name="%(internal_name)s"></a>' % locals())
    print_info_line(req, make_url(name, base_url) + ', ' + make_url(num, url) , html2)

    for result in results:
        req.write(result.html + '<br>')

    if not results:
        req.write(_('No results found.') + '<br>')

def make_url(name, url):
    if url:
        return '<a href="' + url + '">' + name + '</a>'
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

