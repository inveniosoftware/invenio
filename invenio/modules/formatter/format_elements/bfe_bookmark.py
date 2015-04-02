# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2014, 2015 CERN.
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

"""BibFormat element - bookmark toolbar.

See <http://keith-wood.name/bookmark.html>.
"""

from invenio.config import CFG_SITE_URL, CFG_BASE_URL, CFG_SITE_RECORD, CFG_CERN_SITE
from invenio.legacy.search_engine import get_all_restricted_recids
from invenio.utils.html import escape_javascript_string
from invenio.modules.formatter.format_elements.bfe_sciencewise import create_sciencewise_url, \
    get_arxiv_reportnumber
from invenio.legacy.webjournal.utils import \
    parse_url_string, \
    make_journal_url, \
    get_journals_ids_and_names


def format_element(
        bfo, only_public_records=1,
        sites="linkedin,twitter,facebook,google,delicious,sciencewise"):
    """Return a snippet of JavaScript needed for displaying a bookmark toolbar.

    :param only_public_records: if set to 1 (the default), prints the box only
        if the record is public (i.e. if it belongs to the root colletion and
        is accessible to the world).

    :param sites: which sites to enable (default is
        'linkedin,twitter,facebook,google,delicious,sciencewise').
        This should be a comma separated list of strings.
        Valid values are available on:
            <http://keith-wood.name/bookmark.html#sites>
        Note that 'sciencewise' is an ad-hoc service that will be displayed
        only in case the record has an arXiv reportnumber and will always
        be displayed last.
    """
    if int(only_public_records) and \
            bfo.recID not in get_all_restricted_recids():
        return ""

    sitelist = sites.split(',')
    sitelist = [site.strip().lower() for site in sitelist]

    sciencewise = False
    if 'sciencewise' in sitelist:
        sciencewise = True
        sitelist.remove('sciencewise')

    sites_js = ", ".join("'%s'" % site for site in sitelist)

    title = bfo.field('245__a')
    description = bfo.field('520__a')

    sciencewise_script = ""
    if sciencewise:
        reportnumber = get_arxiv_reportnumber(bfo)
        sciencewise_url = ""
        if reportnumber:
            sciencewise_url = create_sciencewise_url(reportnumber)
        if not sciencewise_url and CFG_CERN_SITE:
            sciencewise_url = create_sciencewise_url(bfo.recID, cds=True)
        if sciencewise_url:
            sciencewise_script = """\
$.bookmark.addSite('sciencewise', 'ScienceWise.info', '%(siteurl)s/img/sciencewise.png', 'en', 'bookmark', '%(url)s');
$('#bookmark_sciencewise').bookmark({sites: ['sciencewise']});
""" % {
                'siteurl': CFG_SITE_URL,
                'url': sciencewise_url.replace("'", r"\'"),
            }

    url = '%(siteurl)s/%(record)s/%(recid)s' % \
          {'recid': bfo.recID,
           'record': CFG_SITE_RECORD,
           'siteurl': CFG_BASE_URL}

    args = parse_url_string(bfo.user_info['uri'])
    journal_name = args["journal_name"]
    if journal_name and \
       (journal_name in [info.get('journal_name', '') for info in get_journals_ids_and_names()]):
        # We are displaying a WebJournal article: URL is slightly different
        url = make_journal_url(bfo.user_info['uri'])

    return """\
<!-- JQuery Bookmark Button BEGIN -->
<div id="bookmark"></div><div id="bookmark_sciencewise"></div>
<style type="text/css">
    #bookmark_sciencewise, #bookmark { float: left; }
    #bookmark_sciencewise li { padding: 2px; width: 25px}
    #bookmark_sciencewise ul, #bookmark ul { list-style-image: none; }
</style>
<script type="text/javascript" src="%(siteurl)s/vendors/jquery.bookmark/jquery.bookmark.min.js"></script>
<style type="text/css">@import "%(siteurl)s/vendors/jquery.bookmark/jquery.bookmark.css";</style>
<script type="text/javascript">// <![CDATA[
    %(sciencewise)s
    $('#bookmark').bookmark({
        sites: [%(sites_js)s],
        icons: '%(siteurl)s/vendors/jquery.bookmark/bookmarks.png',
        url: '%(url)s',
        addEmail: true,
        title: "%(title)s",
        description: "%(description)s"
    });
// ]]>
</script>
<!-- JQuery Bookmark Button END -->
""" % {
        'siteurl': CFG_BASE_URL,
        'sciencewise': sciencewise_script,
        'title': escape_javascript_string(title,
                                          escape_for_html=False,
                                          escape_CDATA=True),
        'description': escape_javascript_string(description,
                                                escape_for_html=False,
                                                escape_CDATA=True),
        'sites_js': sites_js,
        'url': url,
    }


def escape_values(bfo):
    """Check if output of this element should be escaped."""
    return 0
