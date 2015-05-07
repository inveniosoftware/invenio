# -*- coding: utf-8 -*-
# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2009, 2010, 2011, 2014, 2015 CERN.
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

from __future__ import print_function

"""
WebDoc -- Transform webdoc sources into static html files
"""

__revision__ = \
    "$Id$"

from six import iteritems

from . import registry

from invenio.config import \
     CFG_LOCALEDIR, \
     CFG_SITE_LANG, \
     CFG_SITE_LANGS, \
     CFG_SITE_NAME, \
     CFG_SITE_SUPPORT_EMAIL, \
     CFG_SITE_ADMIN_EMAIL, \
     CFG_SITE_URL, \
     CFG_SITE_SECURE_URL, \
     CFG_SITE_RECORD, \
     CFG_VERSION, \
     CFG_SITE_NAME_INTL, \
     CFG_CACHEDIR
from invenio.utils.date import \
     convert_datestruct_to_datetext, \
     convert_datestruct_to_dategui, \
     convert_datecvs_to_datestruct
from invenio.utils.shell import mymkdir
from invenio.base.i18n import \
     gettext_set_language, \
     wash_language, \
     language_list_long

import re
import getopt
import os
import sys
import time

# List of (webdoc_source_dir, webdoc_cache_dir)
webdoc_dirs = {'help':('',
                       '%s/webdoc/help-pages' % CFG_CACHEDIR),
               'admin':('admin',
                        '%s/webdoc/admin-pages' % CFG_CACHEDIR),
               'hacking':('hacking',
                          '%s/webdoc/hacking-pages' % CFG_CACHEDIR),
               'info':('info',
                       '%s/webdoc/info-pages' % CFG_CACHEDIR)}

# Regular expression for finding text to be translated
translation_pattern = re.compile(r'_\((?P<word>.*?)\)_', \
                                 re.IGNORECASE | re.DOTALL | re.VERBOSE)

# # Regular expression for finding comments
comments_pattern = re.compile(r'^\s*#.*$', \
                                   re.MULTILINE)

# Regular expression for finding <lang:current/> tag
pattern_lang_current = re.compile(r'<lang \s*:\s*current\s*\s*/>', \
                                  re.IGNORECASE | re.DOTALL | re.VERBOSE)


# Regular expression for finding <lang:link/> tag
pattern_lang_link_current = re.compile(r'<lang \s*:\s*link\s*\s*/>', \
                                  re.IGNORECASE | re.DOTALL | re.VERBOSE)


# Regular expression for finding <!-- %s: %s --> tag
# where %s will be replaced at run time
pattern_tag = r'''
    <!--\s*(?P<tag>%s)   #<!-- %%s tag (no matter case)
    \s*:\s*
    (?P<value>.*?)         #description value. any char that is not end tag
    (\s*-->)            #end tag
    '''

# List of available tags in webdoc, and the pattern to find it
pattern_tags = {'WebDoc-Page-Title': '',
                'WebDoc-Page-Navtrail': '',
                'WebDoc-Page-Description': '',
                'WebDoc-Page-Keywords': '',
                'WebDoc-Page-Header-Add': '',
                'WebDoc-Page-Box-Left-Top-Add': '',
                'WebDoc-Page-Box-Left-Bottom-Add': '',
                'WebDoc-Page-Box-Right-Top-Add': '',
                'WebDoc-Page-Box-Right-Bottom-Add': '',
                'WebDoc-Page-Footer-Add': '',
                'WebDoc-Page-Revision': ''
                }
for tag in pattern_tags.keys():
    pattern_tags[tag] = re.compile(pattern_tag % tag, \
                                   re.IGNORECASE | re.DOTALL | re.VERBOSE)

# Regular expression for finding <lang>...</lang> tag
pattern_lang = re.compile(r'''
    <lang              #<lang tag (no matter case)
    \s*
    (?P<keep>keep=all)*
    \s*                #any number of white spaces
    >                  #closing <lang> start tag
    (?P<langs>.*?)     #anything but the next group (greedy)
    (</lang\s*>)       #end tag
    ''', re.IGNORECASE | re.DOTALL | re.VERBOSE)

# Regular expression for finding <en>...</en> tag (particular case of
# pattern_lang)
pattern_CFG_SITE_LANG = re.compile(r"<("+CFG_SITE_LANG+ \
                             r")\s*>(.*?)(</"+CFG_SITE_LANG+r"\s*>)",
                             re.IGNORECASE | re.DOTALL)

# Builds regular expression for finding each known language in <lang> tags
ln_pattern_text = r"<(?P<lang>"
ln_pattern_text += r"|".join([lang[0] for lang in \
                              language_list_long(enabled_langs_only=False)])
ln_pattern_text += r')\s*(revision="[^"]"\s*)?>(?P<translation>.*?)</\1>'
ln_pattern =  re.compile(ln_pattern_text, re.IGNORECASE | re.DOTALL)

defined_tags = {'<CFG_SITE_NAME>': CFG_SITE_NAME,
                '<CFG_SITE_SUPPORT_EMAIL>': CFG_SITE_SUPPORT_EMAIL,
                '<CFG_SITE_ADMIN_EMAIL>': CFG_SITE_ADMIN_EMAIL,
                '<CFG_SITE_URL>': CFG_SITE_URL,
                '<CFG_SITE_SECURE_URL>': CFG_SITE_SECURE_URL,
                '<CFG_SITE_RECORD>': CFG_SITE_RECORD,
                '<CFG_VERSION>': CFG_VERSION,
                '<CFG_SITE_NAME_INTL>': CFG_SITE_NAME_INTL}

def get_webdoc_parts(webdoc,
                     parts=['title', \
                            'keywords', \
                            'navtrail', \
                            'body',
                            'lastupdated',
                            'description'],
                     categ="",
                     update_cache_mode=1,
                     ln=CFG_SITE_LANG,
                     verbose=0,
                     req=None):
    """
    Returns the html of the specified 'webdoc' part(s).

    Also update the cache if 'update_cache' is True.

    Parameters:

                  webdoc - *string* the name of a webdoc that can be
                            found in standard webdoc dir, or a webdoc
                            filepath. Priority is given to filepath if
                            both match.

                   parts - *list(string)* the parts that should be
                            returned by this function. Can be in:
                            'title', 'keywords', 'navtrail', 'body',
                            'description', 'lastupdated'.

                   categ - *string* (optional) The category to which
                            the webdoc file belongs. 'help', 'admin'
                            or 'hacking'. If "", look in all categories.

       update_cache_mode - *int* update the cached version of the
                            given 'webdoc':
                               - 0 : do not update
                               - 1 : update if needed
                               - 2 : always update

    Returns : *dictionary* with keys being in 'parts' input parameter and values
              being the corresponding html part.
    """
    html_parts = {}

    if update_cache_mode in [1, 2]:
        update_webdoc_cache(webdoc, update_cache_mode, verbose)

    def get_webdoc_cached_part_path(webdoc_cache_dir, webdoc, ln, part):
        "Build path for given webdoc, ln and part"
        return webdoc_cache_dir + os.sep + webdoc + \
               os.sep + webdoc + '.' + part + '-' + \
               ln + '.html'

    for part in parts:
        if categ != "":
            if categ == 'info':
                uri_parts = req.uri.split(os.sep)
                locations = list(webdoc_dirs.get(categ, ('','')))
                locations[0] = locations[0] + os.sep + os.sep.join(uri_parts[uri_parts.index('info')+1:-1])
                locations = [tuple(locations)]
            else:
                locations = [webdoc_dirs.get(categ, ('',''))]
        else:
            locations = webdoc_dirs.values()

        for (_webdoc_source_dir, _web_doc_cache_dir) in locations:
            webdoc_cached_part_path = None
            if os.path.exists(get_webdoc_cached_part_path(_web_doc_cache_dir,
                                                          webdoc, ln, part)):
                # Check given language
                webdoc_cached_part_path = get_webdoc_cached_part_path(_web_doc_cache_dir, webdoc, ln, part)
            elif os.path.exists(get_webdoc_cached_part_path(_web_doc_cache_dir, webdoc, CFG_SITE_LANG, part)):
                # Check CFG_SITE_LANG
                webdoc_cached_part_path = get_webdoc_cached_part_path(_web_doc_cache_dir, webdoc, CFG_SITE_LANG, part)
            elif os.path.exists(get_webdoc_cached_part_path(_web_doc_cache_dir, webdoc, 'en', part)):
                # Check English
                webdoc_cached_part_path = get_webdoc_cached_part_path(_web_doc_cache_dir, webdoc, 'en', part)

            if webdoc_cached_part_path is not None:
                try:
                    webdoc_cached_part = file(webdoc_cached_part_path, 'r').read()
                    html_parts[part] = webdoc_cached_part
                except IOError:
                    # Could not read cache file. Generate on-the-fly,
                    # get all the parts at the same time, and return
                    (webdoc_source_path, \
                     webdoc_cache_dir, \
                     webdoc_name,\
                     webdoc_source_modification_date, \
                     webdoc_cache_modification_date) = get_webdoc_info(webdoc)
                    webdoc_source = file(webdoc_source_path, 'r').read()
                    htmls = transform(webdoc_source, languages=[ln])
                    if len(htmls) > 0:
                        (lang, body, title, keywords, \
                         navtrail, lastupdated, description) = htmls[-1]
                        html_parts =  {'body': body or '',
                                       'title': title or '',
                                       'keywords': keywords or '',
                                       'navtrail': navtrail or '',
                                       'lastupdated': lastupdated or '',
                                       'description': description or ''}
                    # We then have all the parts, or there is no
                    # translation for this file (if len(htmls)==0)
                    break
            else:
                # Look in other categories
                continue

        if html_parts == {}:
            # Could not find/read the folder where cache should
            # be. Generate on-the-fly, get all the parts at the
            # same time, and return
            dirs = None
            if categ == "info":
                dirs = locations
            (webdoc_source_path, \
             webdoc_cache_dir, \
             webdoc_name,\
             webdoc_source_modification_date, \
             webdoc_cache_modification_date) = get_webdoc_info(webdoc, dirs=dirs)
            if webdoc_source_path is not None:
                try:
                    webdoc_source = file(webdoc_source_path, 'r').read()
                    htmls = transform(webdoc_source, languages=[ln])
                    if len(htmls) > 0:
                        (lang, body, title, keywords, \
                         navtrail, lastupdated, description) = htmls[-1]
                        html_parts =  {'body': body or '',
                                       'title': title or '',
                                       'keywords': keywords or '',
                                       'navtrail': navtrail or '',
                                       'lastupdated': lastupdated or '',
                                       'description': description or ''}
                    # We then have all the parts, or there is no
                    # translation for this file (if len(htmls)==0)
                    break
                except IOError:
                    # Nothing we can do..
                    pass

    return html_parts

def update_webdoc_cache(webdoc, mode=1, verbose=0, languages=CFG_SITE_LANGS):
    """
    Update the cache (on disk) of the given webdoc.

    Parameters:

            webdoc       - *string* the name of a webdoc that can be
                           found in standard webdoc dir, or a webdoc
                           filepath.

            mode         - *int* update cache mode:
                                - 0 : do not update
                                - 1 : only if necessary (webdoc source
                                      is newer than its cache)
                                - 2 : always update
    """
    if mode in [1, 2]:
        (webdoc_source_path, \
         webdoc_cache_dir, \
         webdoc_name,\
         webdoc_source_modification_date, \
         webdoc_cache_modification_date) = get_webdoc_info(webdoc)

        if mode == 1 and \
               webdoc_source_modification_date < webdoc_cache_modification_date and \
               get_mo_last_modification() < webdoc_cache_modification_date:
            # Cache was updated after source. No need to update
            return
        (webdoc_source, \
         webdoc_cache_dir, \
         webdoc_name) = read_webdoc_source(webdoc)

        if webdoc_source is not None:
            htmls = transform(webdoc_source, languages=languages)
            for (lang, body, title, keywords, \
                 navtrail, lastupdated, description) in htmls:
                # Body
                if body is not None or lang == CFG_SITE_LANG:
                    try:
                        write_cache_file('%(name)s.body%(lang)s.html' % \
                                         {'name': webdoc_name,
                                          'lang': '-'+lang},
                                         webdoc_cache_dir,
                                         body,
                                         verbose)
                    except IOError as e:
                        print(e)
                    except OSError as e:
                        print(e)

                # Title
                if title is not None or lang == CFG_SITE_LANG:
                    try:
                        write_cache_file('%(name)s.title%(lang)s.html' % \
                                         {'name': webdoc_name,
                                          'lang': '-'+lang},
                                         webdoc_cache_dir,
                                         title,
                                         verbose)
                    except IOError as e:
                        print(e)
                    except OSError as e:
                        print(e)

                # Keywords
                if keywords is not None or lang == CFG_SITE_LANG:
                    try:
                        write_cache_file('%(name)s.keywords%(lang)s.html' % \
                                         {'name': webdoc_name,
                                          'lang': '-'+lang},
                                         webdoc_cache_dir,
                                         keywords,
                                         verbose)
                    except IOError as e:
                        print(e)
                    except OSError as e:
                        print(e)

                # Navtrail
                if navtrail is not None or lang == CFG_SITE_LANG:
                    try:
                        write_cache_file('%(name)s.navtrail%(lang)s.html' % \
                                         {'name': webdoc_name,
                                          'lang': '-'+lang},
                                         webdoc_cache_dir,
                                         navtrail,
                                         verbose)
                    except IOError as e:
                        print(e)
                    except OSError as e:
                        print(e)

                # Description
                if description is not None or lang == CFG_SITE_LANG:
                    try:
                        write_cache_file('%(name)s.description%(lang)s.html' % \
                                         {'name': webdoc_name,
                                          'lang': '-'+lang},
                                         webdoc_cache_dir,
                                         description,
                                         verbose)
                    except IOError as e:
                        print(e)
                    except OSError as e:
                        print(e)

                # Last updated timestamp (CVS timestamp)
                if lastupdated is not None or lang == CFG_SITE_LANG:
                    try:
                        write_cache_file('%(name)s.lastupdated%(lang)s.html' % \
                                         {'name': webdoc_name,
                                          'lang': '-'+lang},
                                         webdoc_cache_dir,
                                         lastupdated,
                                         verbose)
                    except IOError as e:
                        print(e)
                    except OSError as e:
                        print(e)

                # Last updated cache file
                try:
                    write_cache_file('last_updated',
                                     webdoc_cache_dir,
                                     convert_datestruct_to_dategui(time.localtime()),
                                     verbose=0)
                except IOError as e:
                    print(e)
                except OSError as e:
                    print(e)

            if verbose > 0:
                print('Written cache in %s' % webdoc_cache_dir)

def read_webdoc_source(webdoc):
    """
    Returns the source of the given webdoc, along with the path to its
    cache directory.

    Returns (None, None, None) if webdoc cannot be found.

    Parameters:

            webdoc       - *string* the name of a webdoc that can be
                           found in standard webdoc dir, or a webdoc
                           filepath. Priority is given to filepath if
                           both match.

    Returns: *tuple* (webdoc_source, webdoc_cache_dir, webdoc_name)
    """

    (webdoc_source_path, \
     webdoc_cache_dir, \
     webdoc_name,\
     webdoc_source_modification_date, \
     webdoc_cache_modification_date) = get_webdoc_info(webdoc)

    if webdoc_source_path is not None:
        try:
            webdoc_source = file(webdoc_source_path, 'r').read()
        except IOError:
            webdoc_source = None
    else:
        webdoc_source = None

    return (webdoc_source, webdoc_cache_dir, webdoc_name)

def get_webdoc_info(webdoc, dirs=None):
    """
    Locate the file corresponding to given webdoc and return its
    path, the path to its cache directory (even if it does not exist
    yet), the last modification dates of the source and the cache, and
    the webdoc name (i.e. webdoc id)

    Parameters:

       webdoc - *string* the name of a webdoc that can be found in
                 standard webdoc dirs.  (Without extension '.webdoc',
                 hence 'search-guide', not'search-guide.webdoc'.)

    Returns: *tuple* (webdoc_source_path, webdoc_cache_dir,
                      webdoc_name webdoc_source_modification_date,
                      webdoc_cache_modification_date)
    """
    webdoc_source_path = None
    webdoc_cache_dir = None
    webdoc_name = None
    last_updated_date = None
    webdoc_source_modification_date = 1
    webdoc_cache_modification_date  = 0

    for (_webdoc_source_dir, _web_doc_cache_dir) in webdoc_dirs.values():
        webdoc_source_path = registry.doc_category_topics(
            _webdoc_source_dir).get(webdoc)
        if webdoc_source_path is not None and os.path.exists(webdoc_source_path):
            webdoc_cache_dir = _web_doc_cache_dir + os.sep + webdoc
            webdoc_name = webdoc
            webdoc_source_modification_date = os.stat(webdoc_source_path).st_mtime
            break
        else:
            webdoc_source_path = None
            webdoc_name = None
            webdoc_source_modification_date = 1

    if webdoc_cache_dir is not None and \
           os.path.exists(webdoc_cache_dir + os.sep + 'last_updated'):
        webdoc_cache_modification_date = os.stat(webdoc_cache_dir + \
                                                os.sep + \
                                                 'last_updated').st_mtime

    return (webdoc_source_path, webdoc_cache_dir, webdoc_name,
            webdoc_source_modification_date, webdoc_cache_modification_date)

def get_webdoc_topics(sort_by='name', sc=0, limit=-1,
                      categ=['help', 'admin', 'hacking'],
                      ln=CFG_SITE_LANG):
    """
    List the available webdoc files in html format.

      sort_by - *string* Sort topics by 'name' or 'date'.

           sc - *int* Split the topics by categories if sc=1.

        limit - *int* Max number of topics to be printed.
                 No limit if limit < 0.

        categ - *list(string)* the categories to consider

           ln - *string* Language of the page
    """
    _ = gettext_set_language(ln)

    topics = {}
    ln_link = '?ln=' + ln

    for category in categ:
        if category not in webdoc_dirs:
            continue
        (source_path, cache_path) =  webdoc_dirs[category]
        if category not in topics:
            topics[category] = []
        # Build list of tuples(webdoc_name, webdoc_date, webdoc_url)
        for webdoc_name, webdocfile in registry.doc_category_topics(source_path).items():
            webdoc_url = CFG_SITE_URL + "/help/" + \
                         ((category != 'help' and category + '/') or '') + \
                         webdoc_name
            try:
                webdoc_date = time.strptime(get_webdoc_parts(webdoc_name,
                                                             parts=['lastupdated']).get('lastupdated', "1970-01-01 00:00:00"),
                                            "%Y-%m-%d %H:%M:%S")
            except:
                webdoc_date = time.strptime("1970-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")

            topics[category].append((webdoc_name, webdoc_date, webdoc_url))

    # If not split by category, merge everything
    if sc == 0:
        all_topics = []
        for topic in topics.values():
            all_topics.extend(topic)
        topics.clear()
        topics[''] = all_topics

    # Sort topics
    if sort_by == 'name':
        for topic in topics.values():
            topic.sort()
    elif sort_by == 'date':
        for topic in topics.values():
            topic.sort(lambda x, y:cmp(x[1], y[1]))
            topic.reverse()

    out = ''
    for category, topic in iteritems(topics):
        if category != '' and len(categ) > 1:
            out += '<strong>'+ _("%(category)s Pages")  % \
                   {'category': _(category).capitalize()} + '</strong>'
        if limit < 0:
            limit = len(topic)
        out += '<ul class="nav nav-tabs nav-stacked"><li>' + \
               '</li><li>'.join(['<a href="%s%s">%s %s</a>' %
                                 ((topic_item[2],
                                   ln_link,
                                   get_webdoc_parts(topic_item[0],
                                                    parts=['title'],
                                                    ln=ln).get('title') or topic_item[2].split('/')[-1],
                                   '<span class="label pull-right">' +
                                   time.strftime('%Y-%m-%d', topic_item[1]) +
                                   '</span>' if sort_by == 'date' else
                                   '<i class="glyphicon glyphicon-chevron-right pull-right"></i>'))
                                for topic_item in topic[:limit]]) + \
            '</li></ul>'

    return out

def transform(webdoc_source, verbose=0, req=None, languages=CFG_SITE_LANGS):
    """
    Transform a WebDoc into html

    This is made through a serie of transformations, mainly substitutions.

    Parameters:

      - webdoc_source   :  *string* the WebDoc input to transform to HTML
    """
    parameters = {} # Will store values for specified parameters, such
                    # as 'Title' for <!-- WebDoc-Page-Title: Title -->

    def get_param_and_remove(match):
        """
        Analyses 'match', get the parameter and return empty string to
        remove it.

        Called by substitution in 'transform(...)', used to collection
        parameters such as <!-- WebDoc-Page-Title: Title -->

        @param match: a match object corresponding to the special tag
        that must be interpreted
        """
        tag = match.group("tag")
        value = match.group("value")
        parameters[tag] = value
        return ''

    def translate(match):
        """
        Translate matching values
        """
        word = match.group("word")
        translated_word = _(word)
        return translated_word

    # 1 step
    ## First filter, used to remove comments
    ## and <protect> tags
    uncommented_webdoc = ''
    for line in webdoc_source.splitlines(True):
        if not line.strip().startswith('#'):
            uncommented_webdoc += line
    webdoc_source = uncommented_webdoc.replace('<protect>', '')
    webdoc_source = webdoc_source.replace('</protect>', '')

    html_texts = {}
    # Language dependent filters
    for ln in languages:
        _ = gettext_set_language(ln)

        # Check if translation is really needed
        ## Just a quick check. Might trigger false negative, but it is
        ## ok.
        if ln != CFG_SITE_LANG and \
           translation_pattern.search(webdoc_source) is None and \
           pattern_lang_link_current.search(webdoc_source) is None and \
           pattern_lang_current.search(webdoc_source) is None and \
           '<%s>' % ln not in webdoc_source and \
           ('_(') not in webdoc_source:
            continue

        # 2 step
        ## Filter used to translate string in _(..)_
        localized_webdoc = translation_pattern.sub(translate, webdoc_source)

        # 3 step
        ## Print current language 'en', 'fr', .. instead of
        ## <lang:current /> tags and '?ln=en', '?ln=fr', .. instead of
        ## <lang:link />
        localized_webdoc = pattern_lang_link_current.sub('?ln=' + ln,
                                                         localized_webdoc)
        localized_webdoc = pattern_lang_current.sub(ln, localized_webdoc)

        # 4 step
        ## Filter out languages
        localized_webdoc = filter_languages(localized_webdoc, ln, defined_tags)

        # 5 Step
        ## Replace defined tags with their value from config file
        ## Eg. replace <CFG_SITE_URL> with 'http://cds.cern.ch/':
        for defined_tag, value in iteritems(defined_tags):
            if defined_tag.upper() == '<CFG_SITE_NAME_INTL>':
                vget = value.get(ln, value['en'])
                if isinstance(vget, str):
                    vget = vget.decode('utf-8')
                localized_webdoc = localized_webdoc.replace(defined_tag, \
                                                            vget)
            else:
                localized_webdoc = localized_webdoc.replace(defined_tag, value)

        # 6 step
        ## Get the parameters defined in HTML comments, like
        ## <!-- WebDoc-Page-Title: My Title -->
        localized_body = localized_webdoc
        for tag, pattern in iteritems(pattern_tags):
            localized_body = pattern.sub(get_param_and_remove, localized_body)

        out = localized_body

        # Pre-process date
        last_updated = parameters.get('WebDoc-Page-Revision', '')
        last_updated = convert_datecvs_to_datestruct(last_updated)
        last_updated = convert_datestruct_to_datetext(last_updated)

        html_texts[ln] = (ln,
                          out,
                          parameters.get('WebDoc-Page-Title'),
                          parameters.get('WebDoc-Page-Keywords'),
                          parameters.get('WebDoc-Page-Navtrail'),
                          last_updated,
                          parameters.get('WebDoc-Page-Description'))

    # Remove duplicates
    filtered_html_texts = []
    if CFG_SITE_LANG in html_texts:
        filtered_html_texts = [(html_text[0], \
                                (html_text[1] != html_texts[CFG_SITE_LANG][1] and html_text[1]) or None, \
                                (html_text[2] != html_texts[CFG_SITE_LANG][2] and html_text[2]) or None, \
                                (html_text[3] != html_texts[CFG_SITE_LANG][3] and html_text[3]) or None, \
                                (html_text[4] != html_texts[CFG_SITE_LANG][4] and html_text[4]) or None, \
                                (html_text[5] != html_texts[CFG_SITE_LANG][5] and html_text[5]) or None, \
                                (html_text[6] != html_texts[CFG_SITE_LANG][6] and html_text[6]) or None)
                               for html_text in html_texts.values() \
                               if html_text[0] != CFG_SITE_LANG]
        filtered_html_texts.append(html_texts[CFG_SITE_LANG])
    else:
        filtered_html_texts = html_texts.values()

    return filtered_html_texts

def write_cache_file(filename, webdoc_cache_dir, filebody, verbose=0):
    """Write a file inside WebDoc cache dir.
    Raise an exception if not possible
    """
    # open file:
    mymkdir(webdoc_cache_dir)
    fullfilename = webdoc_cache_dir + os.sep + filename

    if filebody is None:
        filebody = ''

    os.umask(0o022)
    f = open(fullfilename, "w")
    f.write(filebody)
    f.close()
    if verbose > 2:
        print('Written %s' % fullfilename)

def get_mo_last_modification():
    """
    Returns the timestamp of the most recently modified mo (compiled
    po) file
    """
    # Take one of the mo files. They are all installed at the same
    # time, so last modication date should be the same
    mo_file = os.path.join(CFG_LOCALEDIR, CFG_SITE_LANG, 'LC_MESSAGES',
                           'invenio.mo')

    if os.path.exists(os.path.abspath(mo_file)):
        return os.stat(mo_file).st_mtime
    else:
        return 0

def filter_languages(text, ln='en', defined_tags=None):
    """
    Filters the language tags that do not correspond to the specified language.
    Eg: <lang><en>A book</en><de>Ein Buch</de></lang> will return
         - with ln = 'de': "Ein Buch"
         - with ln = 'en': "A book"
         - with ln = 'fr': "A book"

    Also replace variables such as <CFG_SITE_URL> and <CFG_SITE_NAME_INTL> inside
    <lang><..><..></lang> tags in order to print them with the correct
    language

    @param text: the input text
    @param ln: the language that is NOT filtered out from the input
    @return: the input text as string with unnecessary languages filtered out
    @see: bibformat_engine.py, from where this function was originally extracted
    """
    # First define search_lang_tag(match) and clean_language_tag(match), used
    # in re.sub() function
    def search_lang_tag(match):
        """
        Searches for the <lang>...</lang> tag and remove inner localized tags
        such as <en>, <fr>, that are not current_lang.

        If current_lang cannot be found inside <lang> ... </lang>, try to use 'CFG_SITE_LANG'

        @param match: a match object corresponding to the special tag that must be interpreted
        """
        current_lang = ln

        # If <lang keep=all> is used, keep all empty line (this is
        # currently undocumented and behaviour might change)
        keep = False
        if match.group("keep") is not None:
            keep = True

        def clean_language_tag(match):
            """
            Return tag text content if tag language of match is output language.

            Called by substitution in 'filter_languages(...)'

            @param match: a match object corresponding to the special tag that must be interpreted
            """
            if match.group('lang') == current_lang or \
                   keep == True:
                return match.group('translation')
            else:
                return ""
            # End of clean_language_tag(..)

        lang_tag_content = match.group("langs")
        # Try to find tag with current lang. If it does not exists,
        # then try to look for CFG_SITE_LANG. If still does not exist, use
        # 'en' as current_lang
        pattern_current_lang = re.compile(r"<(" + current_lang + \
                                          r")\s*>(.*?)(</"+current_lang+r"\s*>)",
                                          re.IGNORECASE | re.DOTALL)

        if re.search(pattern_current_lang, lang_tag_content) is None:
            current_lang = CFG_SITE_LANG
            # Can we find translation in 'CFG_SITE_LANG'?
            if re.search(pattern_CFG_SITE_LANG, lang_tag_content) is None:
                current_lang = 'en'

        cleaned_lang_tag = ln_pattern.sub(clean_language_tag, lang_tag_content)
        # Remove empty lines
        # Only if 'keep' has not been set
        if keep == False:
            stripped_text = ''
            for line in cleaned_lang_tag.splitlines(True):
                if line.strip():
                    stripped_text += line
            cleaned_lang_tag = stripped_text

        return cleaned_lang_tag
        # End of search_lang_tag(..)

    filtered_text = pattern_lang.sub(search_lang_tag, text)
    return filtered_text

def usage(exitcode=1, msg=""):
    """Prints usage info."""
    if msg:
        sys.stderr.write("Error: %s.\n" % msg)
    sys.stderr.write("Usage: %s [options] <webdocname>\n" % sys.argv[0])
    sys.stderr.write("  -h,  --help                \t\t Print this help.\n")
    sys.stderr.write("  -V,  --version             \t\t Print version information.\n")
    sys.stderr.write("  -v,  --verbose=LEVEL       \t\t Verbose level (0=min,1=normal,9=max).\n")
    sys.stderr.write("  -l,  --language=LN1,LN2,.. \t\t Language(s) to process (default all)\n")
    sys.stderr.write("  -m,  --mode=MODE           \t\t Update cache mode(0=Never,1=if necessary,2=always) (default 2)\n")
    sys.stderr.write("\n")
    sys.stderr.write(" Example: webdoc search-guide\n")
    sys.stderr.write(" Example: webdoc -l en,fr search-guide\n")
    sys.stderr.write(" Example: webdoc -m 1 search-guide")
    sys.stderr.write("\n")

    sys.exit(exitcode)

def main():
    """
    main entry point for webdoc via command line
    """
    options = {'language':CFG_SITE_LANGS, 'verbose':1, 'mode':2}

    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   "hVv:l:m:",
                                   ["help",
                                    "version",
                                    "verbose=",
                                    "language=",
                                    "mode="])
    except getopt.GetoptError as err:
        usage(1, err)

    try:
        for opt in opts:
            if opt[0] in ["-h", "--help"]:
                usage(0)
            elif opt[0] in ["-V", "--version"]:
                print(__revision__)
                sys.exit(0)
            elif opt[0] in ["-v", "--verbose"]:
                options["verbose"]  = int(opt[1])
            elif opt[0] in ["-l", "--language"]:
                options["language"]  = [wash_language(lang.strip().lower()) \
                                        for lang in opt[1].split(',') \
                                        if lang in CFG_SITE_LANGS]
            elif opt[0] in ["-m", "--mode"]:
                options["mode"] = opt[1]
    except StandardError as e:
        usage(e)

    try:
        options["mode"] = int(options["mode"])
    except ValueError:
        usage(1, "Mode must be an integer")

    if len(args) > 0:
        options["webdoc"] = args[0]

    if "webdoc" not in options:
        usage(0)

    # check if webdoc exists
    infos = get_webdoc_info(options["webdoc"])
    if infos[0] is None:
        usage(1, "Could not find %s" % options["webdoc"])

    update_webdoc_cache(webdoc=options["webdoc"],
                        mode=options["mode"],
                        verbose=options["verbose"],
                        languages=options["language"])

if __name__ == "__main__":
    main()
