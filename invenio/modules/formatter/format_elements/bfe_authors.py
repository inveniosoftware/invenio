# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2013, 2014, 2015 CERN.
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

"""BibFormat element - Print authors."""

import re
from urllib import quote
from cgi import escape
from invenio.base.i18n import gettext_set_language
from invenio.base.globals import cfg
from invenio.legacy.bibauthority.engine import \
    get_low_level_recIDs_from_control_no
from invenio.ext.logging import register_exception


def format_element(bfo, limit, separator=' ; ',
                   extension='[...]',
                   print_links="yes",
                   print_affiliations='no',
                   affiliation_prefix=' (',
                   affiliation_suffix=')',
                   interactive="no",
                   highlight="no",
                   link_author_pages="no",
                   link_mobile_pages="no",
                   relator_code_pattern=None,
                   multiple_affiliations="no",
                   print_orcid="no",
                   orcid_type="text",
                   orcid_text="no",
                   orcid_prefix="[",
                   orcid_postfix="]"):
    """
    Print the list of authors of a record.

    @param limit: the maximum number of authors to display
    @param separator: the separator between authors.
    @param extension: a text printed if more authors than 'limit' exist
    @param print_links: if yes, prints the authors as HTML link to their publications
    @param print_affiliations: if yes, make each author name followed by its affiliation
    @param affiliation_prefix: prefix printed before each affiliation
    @param affiliation_suffix: suffix printed after each affiliation
    @param interactive: if yes, enable user to show/hide authors when there are too many (html + javascript)
    @param highlight: highlights authors corresponding to search query if set to 'yes'
    @param link_author_pages: should we link to author pages if print_links in on?
    @param link_mobile_pages: should we link to mobile app pages if print_links in on?
    @param relator_code_pattern: a regular expression to filter authors based on subfield $4 (relator code)
    @param multiple_affiliations: whether all affiliations should be displayed
    @param print_orcid: if yes, make each author name followed by its ORCID
    @param orcid_type: the type of ORCID to be displayed. Accepted values: logo link, text
    @param orcid_text: text to put in a link, if left blank it will use an ORCID
    @param orcid_prefix: prefix for link and plain text
    @param orcid_postfix: postfix for link and plain text
    """
    CFG_BASE_URL = cfg['CFG_BASE_URL'].encode('utf-8')
    CFG_SITE_RECORD = cfg['CFG_BASE_URL'].encode('utf-8')

    from invenio.legacy.bibauthority.config import \
        CFG_BIBAUTHORITY_AUTHORITY_COLLECTION_NAME, \
        CFG_BIBAUTHORITY_TYPE_NAMES, \
        CFG_BIBAUTHORITY_PREFIX_SEP

    _ = gettext_set_language(bfo.lang)    # load the right message language

    authors = []
    authors_1 = bfo.fields('100__', repeatable_subfields_p=True)
    authors_2 = bfo.fields('700__', repeatable_subfields_p=True)

    authors.extend(authors_1)
    authors.extend(authors_2)

    # make unique string per key
    for author in authors:
        if 'a' in author:
            author['a'] = author['a'][0]
        if 'u' in author and multiple_affiliations == 'no':
            author['u'] = author['u'][0]
        if 'v' in author and multiple_affiliations == 'no':
            author['v'] = author['v'][0]
        pattern = '%s' + CFG_BIBAUTHORITY_PREFIX_SEP + "("
        for control_no in author.get('0', []):
            if pattern % (CFG_BIBAUTHORITY_TYPE_NAMES["INSTITUTE"]) in control_no:
                author['u0'] = control_no  # overwrite if multiples
            elif pattern % (CFG_BIBAUTHORITY_TYPE_NAMES["AUTHOR"]) in control_no:
                author['a0'] = control_no  # overwrite if multiples

    if relator_code_pattern:
        p = re.compile(relator_code_pattern)
        authors = filter(lambda x: p.match(x.get('4', '')), authors)

    nb_authors = len(authors)

    bibrec_id = bfo.control_field("001")

    # Process authors to add orcid, link, highlight and format affiliation
    for author in authors:

        if 'a' in author:
            if highlight == 'yes':
                from invenio.modules.formatter import utils as bibformat_utils
                author['a'] = bibformat_utils.highlight(author['a'],
                                                        bfo.search_pattern)

            if print_links.lower() == "yes":
                if link_author_pages == "yes":
                    author['a'] = '<a rel="author" href="' + CFG_BASE_URL + \
                                  '/author/profile/' + quote(author['a']) + \
                                  '?recid=' + bibrec_id + \
                                  '&ln=' + bfo.lang + \
                                  '">' + escape(author['a']) + '</a>'
                elif link_mobile_pages == 'yes':
                    author['a'] = '<a rel="external" href="#page=search' + \
                                  '&amp;f=author&amp;p=' + quote(author['a']) + \
                                  '">' + escape(author['a']) + '</a>'
                else:
                    auth_coll_param = ''
                    if 'a0' in author:
                        recIDs = get_low_level_recIDs_from_control_no(
                            author['a0'])
                        if len(recIDs):
                            auth_coll_param = '&amp;c=' + \
                                CFG_BIBAUTHORITY_AUTHORITY_COLLECTION_NAME
                        author['a'] = '<a href="' + CFG_BASE_URL + \
                        '/record/' + str(recIDs[0]) + \
                        '?ln=' + bfo.lang + \
                        '">' + escape(author['a']) + '</a>'
                    else:
                        author['a'] = '<a href="' + CFG_BASE_URL + \
                                  '/search?f=author&amp;p=' + quote(author['a']) + \
                        auth_coll_param + \
                                  '&amp;ln=' + bfo.lang + \
                                  '">' + escape(author['a']) + '</a>'

        if 'u' in author or 'v' in author:
            if print_affiliations == "yes":
                if 'u0' in author:
                    recIDs = get_low_level_recIDs_from_control_no(author['u0'])
                    # if there is more than 1 recID, clicking on link and
                    # thus displaying the authority record's page should
                    # contain a warning that there are multiple authority
                    # records with the same control number
                    if isinstance(author['u'], (list, tuple)):
                        author['u'] = author['u'][0]
                    if len(recIDs):
                        author['u'] = '<a href="' + CFG_BASE_URL + '/' + CFG_SITE_RECORD + '/' + \
                                      str(recIDs[0]) + \
                                      '?ln=' + bfo.lang + \
                                      '">' + author['u'] + '</a>'
                if 'u' not in author and 'v' in author:
                    author['u'] = author['v']
                if isinstance(author['u'], (list, tuple)):
                    author['u'] = ' '.join([affiliation_prefix + aff +
                                            affiliation_suffix for aff in author['u']])
                else:
                    author['u'] = affiliation_prefix + author['u'] + \
                        affiliation_suffix

        if 'j' in author:
            if print_orcid == "yes":
                orcid = author.get('j', "")
                if orcid[0]:
                    orcid = orcid[0].split(':')[1]
                    if orcid_type == 'logo':
                        author['j'] = '<a href="http://orcid.org/%s" target="_blank" class="author_orcid_image_link" title="%s">&nbsp;</a>' % (orcid, orcid)
                    elif orcid_type == 'link':
                        if orcid_text == "no":
                            author['j'] = '%s<a href="http://orcid.org/%s" target="_blank">%s</a>%s' % (orcid_prefix, orcid, orcid, orcid_postfix)
                        else:
                            author['j'] = '%s<a href="http://orcid.org/%s" target="_blank">%s</a>%s' % (orcid_prefix, orcid, orcid_text, orcid_postfix)
                    else:
                        author['j'] = '%s%s%s' % (orcid_prefix, orcid, orcid_postfix)
                else:
                    author['j'] = ""

    # Flatten author instances
    new_authors = []
    for author in authors:
        auth = author.get('a', '')
        if print_orcid == 'yes':
            auth = auth + author.get('j', '')
        if print_affiliations == 'yes':
            auth = auth + author.get('u', '')
        new_authors.append(auth)
    authors = new_authors

    if limit.isdigit() and nb_authors > int(limit) and interactive != "yes":
        return separator.join(authors[:int(limit)]) + extension

    elif limit.isdigit() and nb_authors > int(limit) and interactive == "yes":
        out = '<a name="show_hide" />'
        out += separator.join(authors[:int(limit)])
        out += '<span id="more_%s" style="">' % bibrec_id + separator + \
               separator.join(authors[int(limit):]) + '</span>'
        out += ' <span id="extension_%s"></span>' % bibrec_id
        out += ' <small><i><a id="link_%s" href="#" style="color:rgb(204,0,0);"></a></i></small>' % bibrec_id
        out += '''
        <script type="text/javascript">
        $('#link_%(recid)s').click(function(event) {
            event.preventDefault();
            var more = document.getElementById('more_%(recid)s');
            var link = document.getElementById('link_%(recid)s');
            var extension = document.getElementById('extension_%(recid)s');
            if (more.style.display=='none'){
                more.style.display = '';
                extension.style.display = 'none';
                link.innerHTML = "%(show_less)s"
            } else {
                more.style.display = 'none';
                extension.style.display = '';
                link.innerHTML = "%(show_more)s"
            }
            link.style.color = "rgb(204,0,0);"
        });

        function set_up_%(recid)s(){
            var extension = document.getElementById('extension_%(recid)s');
            extension.innerHTML = "%(extension)s";
            $('#link_%(recid)s').click();
        }

        </script>
        ''' % {'show_less': _("Hide"),
               'show_more': _("Show all %(x_num)i authors", x_num=nb_authors),
               'extension': extension,
               'recid': bibrec_id}
        out += '<script type="text/javascript">set_up_%s()</script>' % bibrec_id

        return out
    elif nb_authors > 0:
        return separator.join(authors)


def escape_values(bfo):
    """Escape values.

    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
