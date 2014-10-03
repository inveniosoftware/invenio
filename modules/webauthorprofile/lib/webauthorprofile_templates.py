# -*- coding: utf-8 -*-

## This file is part of Invenio.
## Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013 CERN.
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
WebAuthorProfile web templates
"""

# pylint: disable=C0301

__revision__ = "$Id$"

from re import compile, findall
from operator import itemgetter
from datetime import datetime
from StringIO import StringIO


import sys
if sys.hexversion < 0x2060000:
    from md5 import md5
else:
    from hashlib import md5

from invenio.webauthorprofile_publication_grapher import get_graph_code
from invenio.messages import gettext_set_language
from invenio.intbitset import intbitset
from invenio.search_engine import perform_request_search
from invenio.search_engine_summarizer import render_citation_summary
from invenio.urlutils import create_html_link
from invenio.bibauthorid_webapi import get_person_info_by_pid

import invenio.template
bibauthorid_templates = invenio.template.load('bibauthorid')
websearch_templates = invenio.template.load('websearch')

from invenio.webauthorprofile_config import CFG_WEBSEARCH_DEF_RECORDS_IN_GROUPS, \
     CFG_BIBRANK_SHOW_DOWNLOAD_STATS, CFG_SITE_NAME, CFG_SITE_URL, \
     CFG_INSPIRE_SITE, CFG_WEBSEARCH_DEFAULT_SEARCH_INTERFACE, \
     CFG_BIBINDEX_CHARS_PUNCTUATION, CFG_WEBSEARCH_WILDCARD_LIMIT, \
     CFG_WEBAUTHORPROFILE_FIELDCODE_TAG, \
     CFG_WEBAUTHORPROFILE_GENERATED_TIMESTAMP_BOTTOM_POSITION

# maximum number of collaborating authors etc shown in GUI
from invenio.webauthorprofile_config import CFG_WEBAUTHORPROFILE_MAX_COLLAB_LIST, \
    CFG_WEBAUTHORPROFILE_MAX_KEYWORD_LIST, CFG_WEBAUTHORPROFILE_MAX_FIELDCODE_LIST, \
    CFG_WEBAUTHORPROFILE_MAX_AFF_LIST, CFG_WEBAUTHORPROFILE_MAX_COAUTHOR_LIST

_RE_PUNCTUATION = compile(CFG_BIBINDEX_CHARS_PUNCTUATION)
_RE_SPACES = compile(r"\s+")


def wrap_author_name_in_quotes_if_needed(author_name):
    """
    If AUTHOR_NAME contains space, return it wrapped inside double
    quotes. Otherwise return it as it is. Useful for links like
    author:J.R.Ellis.1 versus author:"Ellis, J".
    """
    if not author_name:
        return ''

    if not isinstance(author_name, str):
        author_name = str(author_name)

    if ' ' in author_name: # and not author_name.startswith('"') and not author_name.endswith('"'):
        return '"' + author_name + '"'
    else:
        return author_name

class Template:
    # This dictionary maps Invenio language code to locale codes (ISO 639)
    tmpl_localemap = {
        'bg': 'bg_BG',
        'ar': 'ar_AR',
        'ca': 'ca_ES',
        'de': 'de_DE',
        'el': 'el_GR',
        'en': 'en_US',
        'es': 'es_ES',
        'pt': 'pt_BR',
        'fr': 'fr_FR',
        'it': 'it_IT',
        'ka': 'ka_GE',
        'lt': 'lt_LT',
        'ro': 'ro_RO',
        'ru': 'ru_RU',
        'rw': 'rw_RW',
        'sk': 'sk_SK',
        'cs': 'cs_CZ',
        'no': 'no_NO',
        'sv': 'sv_SE',
        'uk': 'uk_UA',
        'ja': 'ja_JA',
        'pl': 'pl_PL',
        'hr': 'hr_HR',
        'zh_CN': 'zh_CN',
        'zh_TW': 'zh_TW',
        'hu': 'hu_HU',
        'af': 'af_ZA',
        'gl': 'gl_ES'
        }
    tmpl_default_locale = "en_US" # which locale to use by default, useful in case of failure

    # Type of the allowed parameters for the web interface for search results
    search_results_default_urlargd = {
        'cc': (str, CFG_SITE_NAME),
        'c': (list, []),
        'p': (str, ""), 'f': (str, ""),
        'rg': (int, CFG_WEBSEARCH_DEF_RECORDS_IN_GROUPS),
        'sf': (str, ""),
        'so': (str, "d"),
        'sp': (str, ""),
        'rm': (str, ""),
        'of': (str, "hb"),
        'ot': (list, []),
        'aas': (int, CFG_WEBSEARCH_DEFAULT_SEARCH_INTERFACE),
        'as': (int, CFG_WEBSEARCH_DEFAULT_SEARCH_INTERFACE),
        'p1': (str, ""), 'f1': (str, ""), 'm1': (str, ""), 'op1':(str, ""),
        'p2': (str, ""), 'f2': (str, ""), 'm2': (str, ""), 'op2':(str, ""),
        'p3': (str, ""), 'f3': (str, ""), 'm3': (str, ""),
        'sc': (int, 0),
        'jrec': (int, 0),
        'recid': (int, -1), 'recidb': (int, -1), 'sysno': (str, ""),
        'id': (int, -1), 'idb': (int, -1), 'sysnb': (str, ""),
        'action': (str, "search"),
        'action_search': (str, ""),
        'action_browse': (str, ""),
        'd1': (str, ""),
        'd1y': (int, 0), 'd1m': (int, 0), 'd1d': (int, 0),
        'd2': (str, ""),
        'd2y': (int, 0), 'd2m': (int, 0), 'd2d': (int, 0),
        'dt': (str, ""),
        'ap': (int, 1),
        'verbose': (int, 0),
        'ec': (list, []),
        'wl': (int, CFG_WEBSEARCH_WILDCARD_LIMIT),
        }

    # ...and for search interfaces
    search_interface_default_urlargd = {
        'aas': (int, CFG_WEBSEARCH_DEFAULT_SEARCH_INTERFACE),
        'as': (int, CFG_WEBSEARCH_DEFAULT_SEARCH_INTERFACE),
        'verbose': (int, 0)}

    tmpl_opensearch_rss_url_syntax = "%(CFG_SITE_URL)s/rss?p={searchTerms}&amp;jrec={startIndex}&amp;rg={count}&amp;ln={language}" % {'CFG_SITE_URL': CFG_SITE_URL}
    tmpl_opensearch_html_url_syntax = "%(CFG_SITE_URL)s/search?p={searchTerms}&amp;jrec={startIndex}&amp;rg={count}&amp;ln={language}" % {'CFG_SITE_URL': CFG_SITE_URL}

    def loading_html(self):
        return '<img src=/img/ui-anim_basic_16x16.gif class="loadingGif" ><span> Loading...</span>'

    def tmpl_print_searchresultbox(self, bid, header, body):
        """ Print a nicely formatted box for search results. """
        #_ = gettext_set_language(ln)

        # first find total number of hits:
        out = ('<table class="searchresultsbox" ><thead><tr><th class="searchresultsboxheader">'
            + header + '</th></tr></thead><tbody><tr><td id ="%s" class="searchresultsboxbody">' % bid
            + body + '</td></tr></tbody></table>')
        return out

    def tmpl_author_name_variants_box(self, names_dict, bibauthorid_data, ln, add_box=True, loading=False):
        """
        Returns a dict consisting of: name -> frequency.
        """
        _ = gettext_set_language(ln)

        header = "<strong>" + _("Name variants") + "</strong>"
        content = []

        if loading:
            content = self.loading_html()
        else:
            if bibauthorid_data["cid"]:
                baid_query = 'exactauthor:%s' % wrap_author_name_in_quotes_if_needed(bibauthorid_data["cid"])
            elif bibauthorid_data["pid"] > -1:
                baid_query = 'exactauthor:%s' % wrap_author_name_in_quotes_if_needed(bibauthorid_data["pid"])
            else:
                baid_query = ''

            # perform_request_search function is not case sensitive, so we should agglomerate names which differ only in case
            new_names_dict = {}
            for name, papers_num in names_dict.iteritems():
                ln = name.lower()
                caps = len(findall("[A-Z]", name))
                try:
                    prev_papers_num = new_names_dict[ln][1][1]
                    new_papers_num = prev_papers_num + papers_num

                    new_caps = new_names_dict[ln][0]
                    new_name = new_names_dict[ln][1][0]
                    if new_names_dict[ln][0] < caps:
                        new_name = name
                        new_caps = caps

                    new_names_dict[ln] = [new_caps, (new_name, new_papers_num)]
                except KeyError:
                    new_names_dict[ln] = [caps, (name, papers_num)]

            filtered_list = [name[1] for name in new_names_dict.values()]
            sorted_names_list = sorted(filtered_list, key=itemgetter(0), reverse=True)

            for name, frequency in sorted_names_list:
                if not name:
                    name = ''

                prquery = baid_query + ' exactauthor:"' + name + '"'
                name_lnk = create_html_link(websearch_templates.build_search_url(p=prquery),
                                                                  {},
                                                                  str(frequency),)
                content.append("%s (%s)" % (name, name_lnk))
            content = "<br />\n".join(content)
            if not content:
                content = [_("No Name Variants")]

        if not add_box:
            return content
        names_box = self.tmpl_print_searchresultbox("name_variants", header, content)

        return names_box

    def tmpl_papers_with_self_papers_box(self, pubs, self_pubs, bibauthorid_data,
                                         num_downloads,
                                         ln, add_box=True, loading=False):
        _ = gettext_set_language(ln)
        if not loading:
            ib_pubs = intbitset(pubs)
            ib_self_pubs = intbitset(self_pubs)

            if bibauthorid_data["cid"]:
                baid_query = 'exactauthor:%s' % wrap_author_name_in_quotes_if_needed(bibauthorid_data["cid"])
            else:
                baid_query = 'exactauthor:%s' % wrap_author_name_in_quotes_if_needed(bibauthorid_data["pid"])
            baid_query = baid_query + " "

            rec_query = baid_query
            self_rec_query = baid_query + " authorcount:1 "
            descstr = ['', "<strong>" + "All papers" + "</strong>"]
            searchstr = [" All papers "]
            self_searchstr = [" Single authored "]
            if pubs:
                searchstr.append(("" +
                        create_html_link(websearch_templates.build_search_url(p=rec_query),
                        {}, str(len(pubs)) ,) + ""))
            else:
                searchstr.append(("0"))
            if self_pubs:
                self_searchstr.append(("" +
                        create_html_link(websearch_templates.build_search_url(p=self_rec_query),
                        {}, str(len(self_pubs)) ,) + ""))
            else:
                self_searchstr.append(("0"))
            psummary = searchstr
            self_psummary = self_searchstr

            if CFG_BIBRANK_SHOW_DOWNLOAD_STATS and num_downloads:
                psummary[0] += " <br> (" + _("downloaded") + " "
                psummary[0] += str(num_downloads) + " " + _("times") + ")"

            if CFG_INSPIRE_SITE:
                CFG_COLLS = ['Book',
                             'ConferencePaper',
                             'Introductory',
                             'Lectures',
                             'Published',
                             'Review',
                             'Thesis',
                             'Proceedings']
            else:
                CFG_COLLS = ['Article',
                             'Book',
                             'Preprint', ]

            collsd = {}
            self_collsd = {}

            for coll in CFG_COLLS:
                search_result = intbitset(perform_request_search(rg=0, f="collection", p=coll))
                collsd[coll] = list(ib_pubs & search_result)
                self_collsd[coll] = list(ib_self_pubs & search_result)

            for coll in CFG_COLLS:
                rec_query = baid_query + 'collection:' + wrap_author_name_in_quotes_if_needed(coll)
                self_rec_query = baid_query + 'collection:' + wrap_author_name_in_quotes_if_needed(coll) + ' authorcount:1 '
                descstr.append("%s" % coll)
                if collsd[coll]:
                    psummary.append(("" +
                             create_html_link(websearch_templates.build_search_url(p=rec_query),
                             {}, str(len(collsd[coll])),) + ''))
                else:
                    psummary.append(("0"))
                if self_collsd[coll]:
                    self_psummary.append(("" +
                             create_html_link(websearch_templates.build_search_url(p=self_rec_query),
                             {}, str(len(self_collsd[coll])),) + ''))
                else:
                    self_psummary.append(("0"))
            tp = "<tr><td> %s </td> <td align='right'> %s </td> <td align='right'> %s </td></tr>"
            line2 = "<table > %s </table>"
            line2 = line2 % ''.join(tp % (x, y, z) for x, y, z in zip(*(descstr, psummary, self_psummary)))
        else:
            line2 = self.loading_html()


        if not add_box:
            return line2
        line1 = "<strong>" + _("Papers") + "</strong>"
        papers_box = self.tmpl_print_searchresultbox("combined_papers", line1, line2)
        return papers_box

    def tmpl_keyword_box(self, kwtuples, bibauthorid_data, ln, add_box=True, loading=False):
        _ = gettext_set_language(ln)
        if not loading:
            if bibauthorid_data["cid"]:
                baid_query = 'exactauthor:%s' % wrap_author_name_in_quotes_if_needed(bibauthorid_data["cid"])
            else:
                baid_query = 'exactauthor:%s' % wrap_author_name_in_quotes_if_needed(bibauthorid_data["pid"])
            # print frequent keywords:
            keywstr = ""
            if (kwtuples):
                if CFG_WEBAUTHORPROFILE_MAX_KEYWORD_LIST > 0:
                    kwtuples = kwtuples[:CFG_WEBAUTHORPROFILE_MAX_KEYWORD_LIST]
                def print_kw(kwtuples):
                    keywstr = ""
                    for (kw, freq) in kwtuples:
                        if keywstr:
                            keywstr += '<br>'
                        rec_query = baid_query + ' keyword:"' + kw + '" '
                        searchstr = kw + ' (' + create_html_link(websearch_templates.build_search_url(p=rec_query),
                                                                           {}, str(freq),) + ')'
                        keywstr = keywstr + " " + searchstr
                    return keywstr
                keywstr = self.print_collapsable_html(print_kw, kwtuples, 'keywords', keywstr)

            else:
                keywstr += _('No Keywords')
            line2 = keywstr
        else:
            line2 = self.loading_html()
        if not add_box:
            return line2
        line1 = "<strong>" + _("Frequent keywords") + "</strong>"
        keyword_box = self.tmpl_print_searchresultbox('keywords', line1, line2)
        return keyword_box

    def tmpl_fieldcode_box(self, fieldtuples, bibauthorid_data, ln, add_box=True, loading=False):
        _ = gettext_set_language(ln)
        if not loading:
            if bibauthorid_data["cid"]:
                baid_query = 'exactauthor:%s' % wrap_author_name_in_quotes_if_needed(bibauthorid_data["cid"])
            else:
                baid_query = 'exactauthor:%s' % wrap_author_name_in_quotes_if_needed(bibauthorid_data["pid"])
            # print frequent fieldcodes:
            fieldstr = ""
            if (fieldtuples):
                if CFG_WEBAUTHORPROFILE_MAX_FIELDCODE_LIST > 0:
                    fieldtuples = fieldtuples[:CFG_WEBAUTHORPROFILE_MAX_FIELDCODE_LIST]
                def print_fieldcode(fieldtuples):
                    fieldstr = ""
                    for (field, freq) in fieldtuples:
                        if fieldstr:
                            fieldstr += '<br>'
                        rec_query = baid_query + ' ' + CFG_WEBAUTHORPROFILE_FIELDCODE_TAG + ':"' + field + '"'
                        searchstr = field + ' (' + create_html_link(websearch_templates.build_search_url(p=rec_query),
                                                                           {}, str(freq),) + ')'
                        fieldstr = fieldstr + " " + searchstr
                    return fieldstr
                fieldstr = self.print_collapsable_html(print_fieldcode, fieldtuples, 'fieldcodes', fieldstr)

            else:
                fieldstr += _('No Subject categories')

            line2 = fieldstr
        else:
            line2 = self.loading_html()
        if not add_box:
            return line2
        line1 = "<strong>" + _("Subject categories") + "</strong>"
        fieldcode_box = self.tmpl_print_searchresultbox('fieldcodes', line1, line2)
        return fieldcode_box

    def print_collapsable_html(self, print_func, data, identifier, append_to=''):
        bsize = 10
        current = 0
        maximum = len(data)
        first = data[current:bsize]
        rest = []
        while current < maximum:
            current += bsize
            bsize *= 2
            rest.append(data[current:current + bsize])
        append_to += print_func(first)
        for i, b in enumerate(rest):
            if b:
                append_to += ('<br><a href="#" class="lmore-%s-%s">'
                                '<img src="/img/aid_plus_16.png" '
                                'alt = "toggle additional information." '
                                'width="11" height="11"/> '
                                + "more" +
                                '</a></em>') % (identifier, i)

                append_to += '<div class="more-lmore-%s-%s hidden">' % (identifier, i)
                append_to += print_func(b)
        for i in range(len(rest)):
            append_to += "</div>"
        return append_to

    def tmpl_collab_box(self, collabs, bibauthorid_data, ln, add_box=True, loading=False):
        _ = gettext_set_language(ln)
        if not loading:
            if bibauthorid_data["cid"]:
                baid_query = 'exactauthor:%s' % wrap_author_name_in_quotes_if_needed(bibauthorid_data["cid"])
            else:
                baid_query = 'exactauthor:%s' % wrap_author_name_in_quotes_if_needed(bibauthorid_data["pid"])
            # print frequent keywords:
            collabstr = ""
            if (collabs):
                if CFG_WEBAUTHORPROFILE_MAX_COLLAB_LIST > 0:
                    collabs = collabs[0:CFG_WEBAUTHORPROFILE_MAX_COLLAB_LIST]

                def print_collabs(collabs):
                    collabstr = ""
                    for (cl, freq) in collabs:
                        if collabstr:
                            collabstr += '<br>'
                        rec_query = baid_query + ' collaboration:"' + cl + '"'
                        searchstr = cl + ' (' + create_html_link(websearch_templates.build_search_url(p=rec_query),
                                                                           {}, str(freq),) + ')'
                        collabstr = collabstr + " " + searchstr
                    return collabstr

                collabstr = self.print_collapsable_html(print_collabs, collabs, "collabs", collabstr)
            else:
                collabstr += _('No Collaborations')

            line2 = collabstr
        else:

            line2 = self.loading_html()
        line1 = "<strong>" + _("Collaborations") + "</strong>"
        if not add_box:
            return line2
        colla_box = self.tmpl_print_searchresultbox('collaborations', line1, line2)
        return colla_box

    def tmpl_affiliations_box(self, aff_pubdict, ln, add_box=True, loading=False):
        _ = gettext_set_language(ln)
        if not loading:
            #make a authoraff string that looks like CERN (1), Caltech (2) etc
            authoraff = ""
            aff_pubdict_keys = aff_pubdict.keys()
            aff_pubdict_keys.sort(lambda x, y: cmp(len(aff_pubdict[y]), len(aff_pubdict[x])))

            aff_pubdict = [(k, aff_pubdict[k]) for k in aff_pubdict_keys]

            if aff_pubdict:
                if CFG_WEBAUTHORPROFILE_MAX_AFF_LIST > 0:
                    aff_pubdict = aff_pubdict[:CFG_WEBAUTHORPROFILE_MAX_AFF_LIST]
                def print_aff(aff_pubdict):
                    authoraff = ""
                    for a in aff_pubdict:
                        print_a = a[0]
                        if (print_a == ' '):
                            print_a = _("unknown affiliation")
                        if authoraff:
                            authoraff += '<br>'
                        authoraff += (print_a + ' (' + create_html_link(
                                     websearch_templates.build_search_url(p=' or '.join(
                                                                    ["%s" % x for x in a[1]]),
                                                    f='recid'),
                                                    {}, str(len(a[1])),) + ')')
                    return authoraff

                authoraff = self.print_collapsable_html(print_aff, aff_pubdict, 'affiliations', authoraff)
            else:
                authoraff = _("No Affiliations")

            line2 = authoraff
        else:
            line2 = self.loading_html()
        if not add_box:
            return line2
        line1 = "<strong>" + _("Affiliations") + "</strong>"
        affiliations_box = self.tmpl_print_searchresultbox('affiliations', line1, line2)
        return affiliations_box

    def tmpl_coauthor_box(self, bibauthorid_data, authors, ln, loading=False):
        _ = gettext_set_language(ln)
        content = ""
        if not loading:
            if bibauthorid_data["cid"]:
                baid_query = 'exactauthor:%s ' % wrap_author_name_in_quotes_if_needed(bibauthorid_data["cid"])
            else:
                baid_query = 'exactauthor:%s ' % wrap_author_name_in_quotes_if_needed(bibauthorid_data["pid"])
            sorted_coauthors = sorted(sorted(authors, key=itemgetter(1)),
                                      key=itemgetter(2), reverse=True)

            if CFG_WEBAUTHORPROFILE_MAX_COAUTHOR_LIST > 0:
                sorted_coauthors = sorted_coauthors[:CFG_WEBAUTHORPROFILE_MAX_COAUTHOR_LIST]

            def print_coauthors(sorted_coauthors):
                content = []
                for canonical, name, frequency in sorted_coauthors:
                    if canonical:
                        second_author = 'exactauthor:%s' % wrap_author_name_in_quotes_if_needed(canonical)
                    else:
                        second_author = 'exactauthor:"%s"' % name
                    rec_query = baid_query + second_author + " -cn:'Collaboration' "
                    lnk = " <a href='%s/author/profile/%s'> %s </a> (" % (CFG_SITE_URL, canonical, name) + create_html_link(websearch_templates.build_search_url(p=rec_query), {}, "%s" % (frequency,),) + ')'
                    content.append("%s" % lnk)
                return "<br>\n".join(content)

            content = self.print_collapsable_html(print_coauthors, sorted_coauthors, 'coauthors', content)
        else:
            content = self.loading_html()

        if not content:
            content = _("No Frequent Co-authors")

        return content

    def tmpl_graph_box(self, pubs_per_year, ln, loading=False):
        """ Creates a graph image (if it doesn't exist) with publication history over the years for
            the specific author and returns the image tag in HTML.
        """

        _ = gettext_set_language(ln)
        graph_html = _("No Publication Graph")
        if not loading:
            if pubs_per_year:
                graph_data = []
                end = datetime.now().year+2
                start = min([min(pubs_per_year.keys())-1, end-6])
                for year in range(start, end):
                    try:
                        graph_data.append((year, pubs_per_year[year]))
                    except KeyError:
                        graph_data.append((year, 0))

                graph_file_name = '%s' % (md5(str(graph_data)).hexdigest())
                graph = get_graph_code(graph_file_name, graph_data)
                if graph:
                    graph_html = graph
        else:
            graph_html = self.loading_html()

        return graph_html
