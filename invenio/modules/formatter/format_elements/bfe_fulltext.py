# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014 CERN.
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
"""BibFormat element - Prints a links to fulltext
"""
__revision__ = "$Id$"

import re
from invenio.legacy.bibdocfile.api import BibRecDocs, file_strip_ext, normalize_format, compose_format
from invenio.base.i18n import gettext_set_language
from invenio.config import CFG_SITE_URL, CFG_BASE_URL, CFG_CERN_SITE, CFG_SITE_RECORD, \
    CFG_BIBFORMAT_HIDDEN_FILE_FORMATS
from invenio.legacy.bibdocfile.config import CFG_BIBDOCFILE_ICON_SUBFORMAT_RE
from invenio.utils.url import get_relative_url

from cgi import escape, parse_qs
from six.moves.urllib.parse import urlparse
from os.path import basename
import urllib

_CFG_NORMALIZED_BIBFORMAT_HIDDEN_FILE_FORMATS = set(normalize_format(fmt) for fmt in CFG_BIBFORMAT_HIDDEN_FILE_FORMATS)

_CFG_BIBFORMAT_HIDDEN_DOCTYPES = ['Plot']
if CFG_CERN_SITE:
    _CFG_BIBFORMAT_HIDDEN_DOCTYPES.append('arXiv')

cern_arxiv_categories = ["astro-ph", "chao-dyn", "cond-mat", "gr-qc",
                         "hep-ex", "hep-lat", "hep-ph", "hep-th", "math-ph",
                         "math", "nucl-ex", "nucl-th", "out", "physics",
                         "quant-ph", "q-alg", "cs", "adap-org", "comp-gas",
                         "chem-ph", "cs", "math", "neuro-sys", "patt-sol",
                         "solv-int", "acc-phys", "alg-geom", "ao-sci",
                         "atom-ph", "cmp-lg", "dg-ga", "funct-an", "mtrl-th",
                         "plasm-ph", "q-alg", "supr-con"]

def format_element(bfo, style, separator='; ', show_icons='no', focus_on_main_file='no', show_subformat_icons='no'):
    """
    This is the default format for formatting fulltext links.

    When possible, it returns only the main file(s) (+ link to
    additional files if needed). If no distinction is made at
    submission time between main and additional files, returns
    all the files

    @param separator: the separator between urls.
    @param style: CSS class of the link
    @param show_icons: if 'yes', print icons for fulltexts
    @param focus_on_main_file: if 'yes' and a doctype 'Main' is found,
    prominently display this doctype. In that case other doctypes are
    summarized with a link to the Files tab, named "Additional files"
    @param show_subformat_icons: shall we display subformats considered as icons?
    """
    _ = gettext_set_language(bfo.lang)

    out = ''

    # Retrieve files
    (parsed_urls, old_versions, additionals) = get_files(bfo, \
                                                         distinguish_main_and_additional_files=focus_on_main_file.lower() == 'yes',
                                                         include_subformat_icons=show_subformat_icons == 'yes',
                                                         hide_doctypes=_CFG_BIBFORMAT_HIDDEN_DOCTYPES)

    main_urls = parsed_urls['main_urls']
    others_urls = parsed_urls['others_urls']
    if 'cern_urls' in parsed_urls:
        cern_urls = parsed_urls['cern_urls']

    # Prepare style and icon
    if style != "":
        style = 'class="'+style+'"'

    if show_icons.lower() == 'yes':
        file_icon = '<img style="border:none" src="%s/img/file-icon-text-12x16.gif" alt="%s"/>' % (CFG_BASE_URL, _("Download fulltext"))
    else:
        file_icon = ''

    # Build urls list.
    # Escape special chars for <a> tag value.

    additional_str = ''
    if additionals:
        additional_str = ' <small>(<a '+style+' href="'+CFG_BASE_URL+'/%s/' % CFG_SITE_RECORD + str(bfo.recID)+'/files/">%s</a>)</small>' % _("additional files")

    versions_str = ''
    #if old_versions:
        #versions_str = ' <small>(<a '+style+' href="'+CFG_BASE_URL+'/CFG_SITE_RECORD/'+str(bfo.recID)+'/files/">%s</a>)</small>' % _("older versions")

    if main_urls:
        out = []
        main_urls_keys = sort_alphanumerically(main_urls.keys())
        for descr in main_urls_keys:
            urls = main_urls[descr]
            if re.match(r'^\d+\s', descr) and urls[0][2] == 'png':
                # FIXME: we have probably hit a Plot (as link
                # description looks like '0001 This is Caption'), so
                # do not take it.  This test is not ideal, we should
                # rather study doc type, and base ourselves on
                # Main/Additional/Plot etc.
                continue
            out += ['<li class="dropdown-header"><strong>%s:</strong></li>' % descr]
            urls_dict = {}
            for url, name, url_format in urls:
                if name not in urls_dict:
                    urls_dict[name] = [(url, url_format)]
                else:
                    urls_dict[name].append((url, url_format))
            for name, urls_and_format in urls_dict.items():
                if len(urls_dict) > 1:
                    print_name = "<em>%s</em>" % name
                    url_list = ['<li class="dropdown-header">' + print_name + "</li>"]
                else:
                    url_list = []
                for url, url_format in urls_and_format:
                    if CFG_CERN_SITE and url_format == 'ps.gz' and len(urls_and_format) > 1:
                        ## We skip old PS.GZ files
                        continue
                    url_list.append('<li><a %(style)s href="%(url)s">%(file_icon)s %(url_format)s</a></li>' % {
                        'style': style,
                        'url': escape(url, True),
                        'file_icon': file_icon,
                        'url_format': escape(url_format.upper())
                    })
                out += url_list
        return '<ul class="dropdown-menu pull-right">' + "\n".join(out) + '</ul>'

    if main_urls:
        main_urls_keys = sort_alphanumerically(main_urls.keys())
        for descr in main_urls_keys:
            urls = main_urls[descr]
            out += "<strong>%s:</strong> " % descr
            urls_dict = {}
            for url, name, url_format in urls:
                if name not in urls_dict:
                    urls_dict[name] = [(get_relative_url(url), url_format)]
                else:
                    urls_dict[name].append((get_relative_url(url), url_format))
            for name, urls_and_format in urls_dict.items():
                if len(urls_dict) > 1:
                    print_name = "<em>%s</em> - " % name
                    url_list = [print_name]
                else:
                    url_list = []
                for url, url_format in urls_and_format:
                    if CFG_CERN_SITE and url_format == 'ps.gz' and len(urls_and_format) > 1:
                        ## We skip old PS.GZ files
                        continue
                    url_list.append('<a %(style)s href="%(url)s">%(file_icon)s%(url_format)s</a>' % {
                        'style': style,
                        'url': escape(url, True),
                        'file_icon': file_icon,
                        'url_format': escape(url_format.upper())
                    })
                out += " ".join(url_list) + additional_str + versions_str + separator

    if CFG_CERN_SITE and cern_urls:
        link_word = len(cern_urls) == 1 and _('%(x_sitename)s link') or _('%(x_sitename)s links')
        out += '<strong>%s</strong>: ' % (link_word % {'x_sitename': 'CERN'})
        url_list = []
        for url, descr in cern_urls:
            url_list.append('<a '+style+' href="'+escape(url)+'">'+ \
                            file_icon + escape(str(descr))+'</a>')
        out += separator.join(url_list)

    if others_urls:
        external_link = len(others_urls) == 1 and _('external link') or _('external links')
        out += '<strong>%s</strong>: ' % external_link.capitalize()
        url_list = []
        for url, descr in others_urls:
            url_list.append('<a '+style+' href="'+escape(url)+'">'+ \
                            file_icon + escape(str(descr))+'</a>')
        out += separator.join(url_list) + '<br />'

    if out.endswith('<br />'):
        out = out[:-len('<br />')]

    # When exported to text (eg. in WebAlert emails) we do not want to
    # display the link to the fulltext:
    if out:
        out = '<!--START_NOT_FOR_TEXT-->' + out + '<!--END_NOT_FOR_TEXT-->'

    return out

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0

def get_files(bfo, distinguish_main_and_additional_files=True, include_subformat_icons=False,
              hide_doctypes=None):
    """
    Returns the files available for the given record.
    Returned structure is a tuple (parsed_urls, old_versions, additionals):
     - parsed_urls: contains categorized URLS (see details below)
     - old_versions: set to True if we can have access to old versions
     - additionals: set to True if we have other documents than the 'main' document

     Parameter 'include_subformat_icons' decides if subformat
     considered as icons should be returned

     Parameter hide_doctypes (list) decides which doctypes should not
     be included in the returned structure

    'parsed_urls' is a dictionary in the form::
        {'main_urls' : {'Main'      : [('http://CFG_SITE_URL/CFG_SITE_RECORD/1/files/aFile.pdf', 'aFile', 'PDF'),
                                       ('http://CFG_SITE_URL/CFG_SITE_RECORD/1/files/aFile.gif', 'aFile', 'GIF')],
                        'Additional': [('http://CFG_SITE_URL/CFG_SITE_RECORD/1/files/bFile.pdf', 'bFile', 'PDF')]},

         'other_urls': [('http://externalurl.com/aFile.pdf', 'Fulltext'),      # url(8564_u), description(8564_z/y)
                        ('http://externalurl.com/bFile.pdf', 'Fulltext')],

         'cern_urls' : [('http://cern.ch/aFile.pdf', 'Fulltext'),              # url(8564_u), description(8564_z/y)
                        ('http://cern.ch/bFile.pdf', 'Fulltext')],
        }

    Some notes about returned structure:
        - key 'cern_urls' is only available on CERN site
        - keys in main_url dictionaries are defined by the BibDoc.
        - older versions are not part of the parsed urls
        - returns only main files when possible, that is when doctypes
          make a distinction between 'Main' files and other
          files. Otherwise returns all the files as main. This is only
          enabled if distinguish_main_and_additional_files is set to True
    """

    _ = gettext_set_language(bfo.lang)

    if hide_doctypes is None:
        hide_doctypes = []

    urls = bfo.fields("8564_")
    bibarchive = BibRecDocs(bfo.recID)

    old_versions = False # We can provide link to older files. Will be
                         # set to True if older files are found.
    additionals = False  # We have additional files. Will be set to
                         # True if additional files are found.

    # Prepare object to return
    parsed_urls = {'main_urls':{},    # Urls hosted by Invenio (bibdocs)
                  'others_urls':[]    # External urls
                  }
    if CFG_CERN_SITE:
        parsed_urls['cern_urls'] = [] # cern.ch urls

        if [url for url in urls if url.get('u', '').startswith('http://arxiv.org/pdf/')]:
            # We have a link to arXiv PDF. We can hide the files on
            # CDS in some cases:
            hide_doctypes.append('CMSPUB_SOURCEF')
            hide_doctypes.append('ATLPUB_SOURCEF')
            hide_doctypes.append('LHCBPB_SOURCEF')

    # Doctypes can of any type, but when there is one file marked as
    # 'Main', we consider that there is a distinction between "main"
    # and "additional" files. Otherwise they will all be considered
    # equally as main files
    distinct_main_and_additional_files = False
    if len(bibarchive.list_bibdocs(doctype='Main')) > 0 and \
           distinguish_main_and_additional_files:
        distinct_main_and_additional_files = True
    # Parse URLs
    for complete_url in urls:
        if 'u' in complete_url:
            url = complete_url['u']
            (dummy, host, path, dummy, params, dummy) = urlparse(url)
            subformat = complete_url.get('x', '')
            filename = urllib.unquote(basename(path))
            name = file_strip_ext(filename)
            url_format = filename[len(name):]
            if url_format.startswith('.'):
                url_format = url_format[1:]
            if compose_format(url_format, subformat) in _CFG_NORMALIZED_BIBFORMAT_HIDDEN_FILE_FORMATS:
                ## This format should be hidden.
                continue

            descr = _("Fulltext")
            if 'y' in complete_url:
                descr = complete_url['y']
                if descr == 'Fulltext':
                    descr = _("Fulltext")
            if not url.startswith(CFG_SITE_URL): # Not a bibdoc?
                if not descr: # For not bibdoc let's have a description
                    # Display the URL in full:
                    descr = url
                if CFG_CERN_SITE and 'cern.ch' in host and \
                       ('/setlink?' in url or \
                        'cms' in host or \
                        'documents.cern.ch' in url or \
                        'doc.cern.ch' in url or \
                        'preprints.cern.ch' in url):
                    url_params_dict = dict([part.split('=') for part in params.split('&') if len(part.split('=')) == 2])
                    if 'categ' in url_params_dict and \
                           (url_params_dict['categ'].split('.', 1)[0] in cern_arxiv_categories) and \
                           'id' in url_params_dict:
                        # Old arXiv links, used to be handled by
                        # setlink. Provide direct links to arXiv
                        for file_format, label in [('pdf', "PDF")]:#,
                            #('ps', "PS"),
                            #('e-print', "Source (generally TeX or LaTeX)"),
                            #('abs', "Abstract")]:
                            url = "http://arxiv.org/%(format)s/%(category)s/%(id)s" % \
                                  {'format': file_format,
                                   'category': url_params_dict['categ'],
                                   'id': url_params_dict['id']}
                            parsed_urls['others_urls'].append((url, "%s/%s %s" % \
                                                               (url_params_dict['categ'],
                                                                url_params_dict['id'],
                                                                label)))
                else:
                    parsed_urls['others_urls'].append((url, descr)) # external url
            else: # It's a bibdoc!
                assigned = False
                for doc in bibarchive.list_bibdocs():
                    if int(doc.get_latest_version()) > 1:
                        old_versions = True
                    if True in [f.get_full_name().startswith(filename) \
                                    for f in doc.list_all_files()]:
                        assigned = True
                        if not include_subformat_icons and \
                               CFG_BIBDOCFILE_ICON_SUBFORMAT_RE.match(subformat):
                            # This is an icon and we want to skip it
                            continue
                        doctype = doc.get_doctype(bfo.recID)
                        if doctype in hide_doctypes:
                            continue
                        if not doctype == 'Main' and \
                               distinct_main_and_additional_files == True:
                            # In that case we record that there are
                            # additional files, but don't add them to
                            # returned structure.
                            additionals = True
                        else:
                            if not descr:
                                descr = _('Fulltext')
                            if descr not in parsed_urls['main_urls']:
                                parsed_urls['main_urls'][descr] = []
                            params_dict = parse_qs(params)
                            if 'subformat' in params_dict:
                                url_format += ' (%s)' % params_dict['subformat'][0]
                            parsed_urls['main_urls'][descr].append((url, name, url_format))
                if not assigned: # Url is not a bibdoc :-S
                    if not descr:
                        descr = filename
                    parsed_urls['others_urls'].append((url, descr)) # Let's put it in a general other url
    return (parsed_urls, old_versions, additionals)

_RE_SPLIT = re.compile(r"\d+|\D+")
def sort_alphanumerically(elements):
    elements = [([not token.isdigit() and token or int(token) for token in _RE_SPLIT.findall(element)], element) for element in elements]
    elements.sort()
    return [element[1] for element in elements]
