# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2007, 2008, 2009, 2010, 2011 CERN.
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
"""BibFormat element - Prints a links to fulltext
"""
__revision__ = "$Id$"

from invenio.bibformat_elements.bfe_fulltext import get_files, sort_alphanumerically
from invenio.messages import gettext_set_language
from invenio.config import CFG_SITE_URL, CFG_CERN_SITE, CFG_SITE_RECORD
from cgi import escape

def format_element(bfo, style, separator='; ', show_icons='no', focus_on_main_file='yes', show_subformat_icons='no'):
    """
    This is the format for formatting fulltext links in the mini panel.
    @param separator: the separator between urls.
    @param style: CSS class of the link
    @param show_icons: if 'yes', print icons for fulltexts
    @param focus_on_main_file: if 'yes' and a doctype 'Main' is found,
    prominently display this doctype. In that case other doctypes are
    summarized with a link to the Files tab, named"Additional files".
    @param show_subformat_icons: shall we display subformats considered as icons?
    """
    _ = gettext_set_language(bfo.lang)
    out = ''

    # Retrieve files
    (parsed_urls, old_versions, additionals) = \
                  get_files(bfo, distinguish_main_and_additional_files=focus_on_main_file.lower() == 'yes',
                            include_subformat_icons=show_subformat_icons == 'yes')

    main_urls = parsed_urls['main_urls']
    others_urls = parsed_urls['others_urls']
    if parsed_urls.has_key('cern_urls'):
        cern_urls = parsed_urls['cern_urls']

    # Prepare style
    if style != "":
        style = 'class="'+style+'"'

    # Build urls list.
    # Escape special chars for <a> tag value.

    additional_str = ''
    if additionals:
        additional_str = separator + '<small>(<a '+style+' href="'+CFG_SITE_URL+'/'+ CFG_SITE_RECORD +'/'+str(bfo.recID)+'/files/">%s</a>)</small>' % _("additional files")

    versions_str = ''
    #if old_versions:
        #versions_str = separator + '<small>(<a '+style+' href="'+CFG_SITE_URL+'/CFG_SITE_RECORD/'+str(bfo.recID)+'/files/">%s</a>)</small>' % _("older versions")

    if main_urls:
        # Put a big file icon if only one file
        if len(main_urls.keys()) == 1 and len(main_urls.items()[0][1]) == 1 and \
               (not CFG_CERN_SITE or len(cern_urls) == 0) and len(others_urls) == 0 and \
               show_icons.lower() == 'yes':
            file_icon = '<img style="border:none" src="%s/img/file-icon-text-34x48.gif" alt="%s" /><br />' % (CFG_SITE_URL, _("Download fulltext"))

        elif show_icons.lower() == 'yes':
            file_icon = '<img style="border:none" src="%s/img/file-icon-text-12x16.gif" alt="%s"/>' % (CFG_SITE_URL, _("Download fulltext"))
        else:
            file_icon = ''

        last_name = ""
        main_urls_keys = sort_alphanumerically(main_urls.keys())
        for descr in main_urls_keys:
            urls = main_urls[descr]
            out += '<div><small class="detailedRecordActions">%s:</small> ' % descr
            url_list = []
            ## FIXME: This is so ugly!
            urls_dict = {}
            for url, name, format in urls:
                urls_dict[url] = (name, format)
            urls_dict_keys = sort_alphanumerically(urls_dict.keys())
            for url in urls_dict_keys:
                name, format = urls_dict[url]
                if not name == last_name and len(main_urls) > 1:
                    print_name = "<em>%s</em> - " % name
                else:
                    print_name = ""
                last_name = name
                url_list.append(print_name + '<a '+style+' href="'+escape(url)+'">'+file_icon+format.upper()+'</a>')
            out += separator + separator.join(url_list) + \
                   additional_str + versions_str + '</div>'

    if CFG_CERN_SITE and cern_urls:
        # Put a big file icon if only one file
        if len(main_urls.keys()) == 0 and \
               len(cern_urls) == 1 and len(others_urls) == 0 and \
               show_icons.lower() == 'yes':
            file_icon = '<img style="border:none" src="%s/img/file-icon-text-34x48.gif" alt="%s" /><br />' % (CFG_SITE_URL, _("Download fulltext"))

        elif show_icons.lower() == 'yes':
            file_icon = '<img style="border:none" src="%s/img/file-icon-text-12x16.gif" alt="%s"/>' % (CFG_SITE_URL, _("Download fulltext"))
        else:
            file_icon = ''

        link_word = len(cern_urls) == 1 and _('%(x_sitename)s link') or _('%(x_sitename)s links')
        out += '<small class="detailedRecordActions">%s:</small><br />' % (link_word % {'x_sitename': 'CERN'})
        url_list = []
        for url, descr in cern_urls:
            url_list.append('<a '+style+' href="'+escape(url)+'">'+file_icon+escape(str(descr))+'</a>')
        out += '<small>' + separator.join(url_list) + '</small>'
        out += "<br/>"

    if others_urls:
        # Put a big file icon if only one file
        if len(main_urls.keys()) == 0 and \
               (not CFG_CERN_SITE or len(cern_urls) == 0) and len(others_urls) == 1 and \
               show_icons.lower() == 'yes':
            file_icon = '<img style="border:none" src="%s/img/file-icon-text-34x48.gif" alt="%s" /><br />' % (CFG_SITE_URL, _("Download fulltext"))
        elif show_icons.lower() == 'yes':
            file_icon = '<img style="border:none" src="%s/img/file-icon-text-12x16.gif" alt="%s"/>' % (CFG_SITE_URL, _("Download fulltext"))
        else:
            file_icon = ''
        external_link = len(others_urls) == 1 and _('external link') or _('external links')
        out += '<small class="detailedRecordActions">%s:</small>%s' % (external_link.capitalize(), separator)
        url_list = []
        for url, descr in others_urls:
            # we don't need to show the plot links here, and all are pngs.
            if url.find('.png') > -1:
                continue
            url_list.append('<a '+style+' href="'+escape(url)+'">'+file_icon+escape(str(descr))+'</a>')
        out += '<small>' + separator.join(url_list) + '</small>'
    if out.endswith('<br />'):
        out = out[:-len('<br />')]

    return out

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
