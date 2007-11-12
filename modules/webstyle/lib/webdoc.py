# -*- coding: utf-8 -*-
## $Id$
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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

"""
WebDoc -- Transform webdoc sources into static html files
"""

__revision__ = \
    "$Id$"


from invenio.config import \
     CFG_PREFIX, \
     cdslang, \
     cdslangs, \
     cdsname, \
     supportemail, \
     adminemail, \
     weburl, \
     sweburl, \
     version, \
     cdsnameintl, \
     cachedir
from invenio.webpage import page

#try:
from invenio.messages import \
     gettext_set_language, \
     wash_language
## except ImportError:
##     cdslang = 'en'
##     gettext_set_language = lambda x: lambda y: y
##     wash_language = lambda x:x
import re
import getopt
import os
import sys

# List of (webdoc_source_dir, webdoc_cache_dir)
webdoc_dirs = [('%s/lib/webdoc/help' % CFG_PREFIX, '%s/webdoc/help-pages' % cachedir),
               ('%s/lib/webdoc/admin' % CFG_PREFIX, '%s/webdoc/admin-pages' % cachedir),
               ('%s/lib/webdoc/hacking' % CFG_PREFIX, '%s/webdoc/hacking-pages' % cachedir,)]

# Regular expression for finding text to be translated in format
# templates
translation_pattern = re.compile(r'''
    _\((?P<word>.*?)\)_
    ''',\
                                 re.IGNORECASE | re.DOTALL | re.VERBOSE)

# # Regular expression for finding comments
comments_pattern = re.compile(r'^\s*#.*$',\
                                   re.MULTILINE)

# Regular expression for finding <lang:current/> tag
pattern_lang_current = re.compile(r'<lang \s*:\s*current\s*\s*/>',\
                                  re.IGNORECASE | re.DOTALL | re.VERBOSE)

# Regular expression for finding <: print function(..) > tag
function_pattern = re.compile(r'''
    <:\s*print\s*(?P<function>.*?)\s*\(\s*(\'|\")
    (?P<param>.*?)
    (\'|\")\s*\)\s*;\s*:>
    ''',\
                                   re.IGNORECASE | re.DOTALL | re.VERBOSE)

# Regular expression for finding <!-- %s: %s --> tag in format templates,
# where %s will be replaced at run time
pattern_tag = r'''
    <!--\s*(?P<tag>%s)   #<!-- %%s tag (no matter case)
    \s*:\s*
    (?P<value>.*?)         #description value. any char that is not end tag
    (\s*-->)            #end tag
    '''

# List of available tags in wml, and the pattern to find it
pattern_tags = {'WebDoc-Page-Title': '',
                'WebDoc-Page-Navtrail-Previous-Links': '',
                'WebDoc-Page-Navbar-Name': '',
                'WebDoc-Page-Navtrail-Body': '',
                'WebDoc-Page-Navbar-Select': '',
                'WebDoc-Page-Description': '',
                'WebDoc-Page-Keywords': '',
                'WebDoc-Page-Header-Add': '',
                'WebDoc-Page-Box-Left-Top-Add': '',
                'WebDoc-Page-Box-Left-Bottom-Add': '',
                'WebDoc-Page-Box-Right-Top-Add': '',
                'WebDoc-Page-Box-Right-Bottom-Add': '',
                'WebDoc-Page-Footer-Add': ''
                }
for tag in pattern_tags.keys():
    pattern_tags[tag] = re.compile(pattern_tag % tag, \
                                   re.IGNORECASE | re.DOTALL | re.VERBOSE)

## cdslangs = []
## try:
##     cdslangs = [lang.strip() for lang in \
##                 file(os.path.abspath(sys.path[0]+'/../../../po/LINGUAS'),'r').readlines() \
##                 if not lang.strip().startswith('#') and \
##                 not lang.strip() == '']
## except Exception, e:
##     print e
##     print "Cannot read LINGUAS file"
##     sys.exit(1)

# Regular expression for finding variable defined in config file:
# Eg: <define-tag CDSLANG whitespace=delete>
#       en
#     </define-tag>
# TODO: extend to deal with more parameters than just
# 'whitespace=delete' ?
pattern_define_tag = re.compile(r'''
    <define-tag \s*
    (?P<tag>\S*?) \s*
    (?P<whitespace>whitespace\s*=\s*delete)\s*
    >                                #closing start tag
    (?P<value>.*?)
    (</define-tag\s*>)               #end tag
    ''', re.IGNORECASE | re.DOTALL | re.VERBOSE)

# Regular expression for finding <lang>...</lang> tag in format templates
pattern_lang = re.compile(r'''
    <lang              #<lang tag (no matter case)
    \s*
    (?P<keep>keep=all)*
    \s*                #any number of white spaces
    >                  #closing <lang> start tag
    (?P<langs>.*?)     #anything but the next group (greedy)
    (</lang\s*>)       #end tag
    ''', re.IGNORECASE | re.DOTALL | re.VERBOSE)

# Builds regular expression for finding each known language in <lang> tags
ln_pattern_text = r"<("
for lang in cdslangs:
    ln_pattern_text += lang +r"|"

ln_pattern_text = ln_pattern_text.rstrip(r"|")
ln_pattern_text += r")>(.*?)</\1>"

ln_pattern =  re.compile(ln_pattern_text, re.IGNORECASE | re.DOTALL)

defined_tags = {'<CDSNAME>': cdsname,
                '<SUPPORTEMAIL>': supportemail,
                '<ADMINEMAIL>': adminemail,
                '<WEBURL>': weburl,
                '<SWEBURL>': sweburl,
                '<VERSION>': version,
                '<CDSNAMEINTL>': cdsnameintl}

def get_webdoc_parts(webdoc, parts=['title','keywords'],
                     update_cache=True, ln=cdslang):
    """
    Returns the html of the specified 'webdoc' part(s).

    Also update the cache if 'update_cache' is True.

    Parameters:

            webdoc       - *string* the name of a webdoc that can be
                           found in standard webdoc dir, or a webdoc
                           filepath. Priority is given to filepath if
                           both match.

            parts        - *list(string)* the parts that should be
                            returned by this function. Can be in:
                            'title', 'keywords', 'navbar-name',
                            'navtrail-previous-links', 'body'

            update_cache - *boolean* update the cached version of the
                           given 'webdoc'.

    Returns : *dictionary* with keys being in 'parts' input parameter and values
              being the corresponsding html part.
    """
    html_parts = {}

    if update_cache == True:
        update_webdoc_cache(webdoc)

    for part in parts:
        for (_webdoc_source_dir, _web_doc_cache_dir) in webdoc_dirs:
            webdoc_cached_part_path = _web_doc_cache_dir + os.sep + webdoc + \
                                      os.sep + webdoc + '.' + part + '-' + \
                                      ln + '.html'

            if os.path.exists(webdoc_cached_part_path):
                webdoc_cached_part = file(webdoc_cached_part_path, 'r').read()
                html_parts[part] = webdoc_cached_part
                break

    return html_parts

def update_webdoc_cache(webdoc):
    """
    Update the cache (on disk) of the given webdoc.

    Parameters:

            webdoc       - *string* the name of a webdoc that can be
                           found in standard webdoc dir, or a webdoc
                           filepath.
    """

    (webdoc_source, webdoc_cache_dir, webdoc_name) = read_webdoc_source(webdoc)

    if webdoc_source is not None:
        htmls = transform(webdoc_source)
        for (lang, body, title, keywords, navbar_name, \
             navtrail_previous_links) in htmls:
            # Body
            if body is not None:
                write_cache_file('%(name)s.body%(lang)s.html' % {'name': webdoc_name,
                                                                 'lang': '-'+lang},
                                 webdoc_cache_dir,
                                 body)
            # Title
            if title is not None:
                write_cache_file('%(name)s.title%(lang)s.html' % {'name': webdoc_name,
                                                                  'lang': '-'+lang},
                                 webdoc_cache_dir,
                                 title)
            # Keywords
            if keywords is not None:
                write_cache_file('%(name)s.keywords%(lang)s.html' % {'name': webdoc_name,
                                                                     'lang': '-'+lang},
                                 webdoc_cache_dir,
                                 keywords)
            # Navtrail previous links
            if navtrail_previous_links is not None:
                write_cache_file('%(name)s.navtrail-previous-links%(lang)s.html' % {'name': webdoc_name,
                                                                                    'lang': '-'+lang},
                                 webdoc_cache_dir,
                                 navtrail_previous_links)
            # Navbar name
            if navbar_name is not None:
                write_cache_file('%(name)s.navbar-name%(lang)s.html' % {'name': webdoc_name,
                                                                        'lang': '-'+lang},
                                 webdoc_cache_dir,
                                 navbar_name)

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
    webdoc_source_path = None
    webdoc_cache_dir = None
    webdoc_name = None

    # Search at given path or in webdoc cache dir
    if os.path.exists(os.path.abspath(webdoc)):
        webdoc_source_path = os.path.abspath(webdoc)
        (webdoc_cache_dir, webdoc_name) = os.path.split(webdoc_source_path)
        webdoc_name = os.path.splitext(webdoc_name)
    else:
        for (_webdoc_source_dir, _web_doc_cache_dir) in webdoc_dirs:
            webdoc_source_path = _webdoc_source_dir + os.sep + webdoc + '.webdoc'
            if os.path.exists(webdoc_source_path):
                webdoc_cache_dir = _web_doc_cache_dir + os.sep + webdoc
                webdoc_name = webdoc
                break
            else:
                webdoc_source_path = None
                webdoc_name = None

    if webdoc_source_path is not None:
        webdoc_source = file(webdoc_source_path, 'r').read()
    else:
        webdoc_source = None

    return (webdoc_source, webdoc_cache_dir, webdoc_name)

def transform(webdoc_source,  verbose=0, req=None, header_p=True):
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
        Analyses 'match', get the parameter and return empty string to remove it.

        Called by substitution in 'transform(...)'

        @param match a match object corresponding to the special tag that must be interpreted
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

##     def current_lang(match):
##         """
##         Returns the value with * char replaced by current language
##         """
##         value = match.group("value")
##         value = value.replace('*', ln)

##         return value

    def function_print(match):
        """
        Format the given document version
        """
        function = match.group("function")
        param = match.group("param")
        out = ''
        if function == 'generate_pretty_revision_date_string':
            # Input: CVS DOLLAR Id DOLLAR string
            # Output: nicely formatted revision/date number suitable for Admin Guides
            # Example: ``DOLLAR Id: webcoll.wml,v 1.41 2004/04/21 11:20:06 tibor Exp DOLLAR''
            #          will generate output like ``CDS Invenio/0
            (junk, filename, revision, date, junk, junk, junk, junk) = param.split(' ')
            out = revision + ', ' + date
        elif function == 'generate_language_list_for_python':
            # Return Python-ready language list out of user-configured WML language list.
            # May return short or long version, depending on the first argument.
            # Output example: ['en','fr']
            # Output example: [['en','English'],['fr','French']]
            # TODO MAYBE
            pass

        return out

    # 1 step
    ## First filter, used to remove comments
    ## and <protect> tags
    uncommented_webdoc = ''
    for line in webdoc_source.splitlines(True):
        if not line.strip().startswith('#'):
            uncommented_webdoc += line
    webdoc_source = uncommented_webdoc.replace('<protect>', '')
    webdoc_source = webdoc_source.replace('</protect>', '')

    # 2 step
    ## Execute custom functions
    ## TODO : remove
    webdoc_source = function_pattern.sub(function_print, webdoc_source)

    html_texts = []
    # Language dependent filters
    for ln in cdslangs:
        _ = gettext_set_language(ln)

        # 3 step
        ## Filter used to translate string in _(..)_
        localized_webdoc = translation_pattern.sub(translate, webdoc_source)

        # 4 step
        ## Print current language 'en', 'fr', .. instead of
        ## <lang:current /> tags
        localized_webdoc = pattern_lang_current.sub(ln, localized_webdoc)

        # 5 step
        ## Filter out languages
        localized_webdoc = filter_languages(localized_webdoc, ln, defined_tags)

        # 6 Step
        ## Replace defined tags with their value from config file
        ## Eg. replace <weburl> with 'http://cdsweb.cern.ch/':
        for defined_tag, value in defined_tags.iteritems():
            if defined_tag.upper() == '<CDSNAMEINTL>':
                localized_webdoc = localized_webdoc.replace(defined_tag, \
                                                            value.get(ln, value['en']))
            else:
                localized_webdoc = localized_webdoc.replace(defined_tag, value)

        # 7 Step
        # Second language filtering, in case some <lang> tags have been
        # introduced by previous step
        #localized_webdoc = filter_languages(localized_webdoc, ln)

        # 8 step
        ## Get the parameters defined in dedicated tags in the wml,
        ## and use them later to build the page:
        ## title
        ## navtrail_previous_links
        ## navbar_name
        ## navtrail_body
        ## navbar_select
        ## description
        ## keywords
        ## cdspageheaderadd
        ## cdspageboxlefttopadd
        ## cdspageboxleftbottomadd
        ## cdspageboxrighttopadd
        ## cdspageboxrightbottomadd
        ## cdspagefooteradd
        ##
##         if header_p == True:
        localized_body = localized_webdoc
        for tag, pattern in pattern_tags.iteritems():
            localized_body = pattern.sub(get_param_and_remove, localized_body)
##         if page is not None:
##             out = page(title=parameters.get('WML-Page-Title', ''),
##                        body=localized_body,
##                        navtrail=parameters.get('WML-Page-Navtrail-Previous-Links', ''), # or navtrail_body ?
##                        description=parameters.get('WML-Page-Description', ''),
##                        keywords=parameters.get('WML-Page-Keywords', ''),
##                        uid=0,
##                        cdspageheaderadd=parameters.get('WML-Page-Header-Add', ''),
##                        cdspageboxlefttopadd=parameters.get('WML-Page-Box-Left-Top-Add', ''),
##                        cdspageboxleftbottomadd=parameters.get('WML-Page-Box-Left-Bottom-Add', ''),
##                        cdspageboxrighttopadd=parameters.get('WML-Page-Box-Right-Top-Add', ''),
##                        cdspageboxrightbottomadd=parameters.get('WML-Page-Box-Right-Bottom-Add', ''),
##                        cdspagefooteradd=parameters.get('WML-Page-Footer-Add', ''),
##                        lastupdated="",
##                        language=ln,
##                        verbose=verbose,
##                        titleprologue="",
##                        titleepilogue="",
##                        secure_page_p=0,
##                        req=req,
##                        errors=[],
##                        warnings=[],
##                        navmenuid=parameters.get('WML-Page-Navbar-Name', ''),
##                        navtrail_append_title_p=1,
##                        of="")
##         else:
##             out = localized_webdoc
##         else:
##             out = localized_webdoc

        out = localized_body

        html_texts.append((ln,
                           out,
                           parameters.get('WebDoc-Page-Title'),
                           parameters.get('WebDoc-Page-Keywords'),
                           parameters.get('WebDoc-Page-Navbar-Name'),
                           parameters.get('WebDoc-Page-Navtrail-Previous-Links')))
    return html_texts

def mymkdir(newdir, mode=0777):
    """works the way a good mkdir should :)
        - already exists, silently complete
        - regular file in the way, raise an exception
        - parent directory(ies) does not exist, make them as well
    """
    if os.path.isdir(newdir):
        pass
    elif os.path.isfile(newdir):
        raise OSError("a file with the same name as the desired " \
                      "dir, '%s', already exists." % newdir)
    else:
        head, tail = os.path.split(newdir)
        if head and not os.path.isdir(head):
            mymkdir(head, mode)
        if tail:
            os.umask(022)
            os.mkdir(newdir, mode)

def write_cache_file(filename, webdoc_cache_dir, filebody):
    "Write a file inside WebDoc cache dir."
    # open file:
    mymkdir(webdoc_cache_dir)
    fullfilename = webdoc_cache_dir + os.sep + filename
    try:
        os.umask(022)
        f = open(fullfilename, "w")
    except IOError, v:
        try:
            (code, message) = v
        except:
            code = 0
            message = v
        raise "I/O Error: " + str(message) + " (" + str(code) + ")"
        #sys.exit(1)
    # print user info:
    #write_message("... creating %s" % fullfilename, verbose=6)
    #sys.stdout.flush()
    # print page body:
    f.write(filebody)
    # close file:
    f.close()

## def transform(wml_text, config_text='', lns=[cdslang], verbose=0, req=None, header_p=True):
##     """
##     Transform a WebDoc into html

##     This is made through a serie of transformations, mainly substitutions.

##     Parameters:

##       - wml_text   :  *string* the WebDoc input to transform to HTML
##       - config_text:  *string* the configuration with the defined tags
##       - lns        :  *list[string]* the list of languages to return
##       - header_p   :  *boolean* when True, print html headers
##     """

##     body = wml_text
##     parameters = {}

##     def get_param_and_remove(match):
##         """
##         Analyses 'match', get the parameter and return empty string to remove it.

##         Called by substitution in 'transform(...)'

##         @param match a match object corresponding to the special tag that must be interpreted
##         """
##         tag = match.group("tag")
##         value = match.group("value")
##         parameters[tag] = value
##         return ''

##     def translate(match):
##         """
##         Translate matching values
##         """
##         word = match.group("word")
##         translated_word = _(word)
##         return translated_word

##     def current_lang(match):
##         """
##         Returns the value with * char replaced by current language
##         """
##         value = match.group("value")
##         value = value.replace('*', ln)

##         return value

##     def function_print(match):
##         """
##         Format the given document version
##         """
##         function = match.group("function")
##         param = match.group("param")
##         out = ''
##         if function == 'generate_pretty_revision_date_string':
##             # Input: CVS DOLLAR Id DOLLAR string
##             # Output: nicely formatted revision/date number suitable for Admin Guides
##             # Example: ``DOLLAR Id: webcoll.wml,v 1.41 2004/04/21 11:20:06 tibor Exp DOLLAR''
##             #          will generate output like ``CDS Invenio/0
##             (junk, filename, revision, date, junk, junk, junk, junk) = param.split(' ')
##             out = revision + ', ' + date
##         elif function == 'generate_language_list_for_python':
##             # Return Python-ready language list out of user-configured WML language list.
##             # May return short or long version, depending on the first argument.
##             # Output example: ['en','fr']
##             # Output example: [['en','English'],['fr','French']]
##             # TODO MAYBE
##             pass

##         return out

##     # 1 step
##     ## First filter, used to remove comments
##     #wml_text = comments_pattern.sub('', wml_text)
##     uncommented_wml_text = ''
##     for line in wml_text.splitlines(True):
##         if not line.strip().startswith('#'):
##             uncommented_wml_text += line
##     wml_text = uncommented_wml_text.replace('<protect>', '')
##     wml_text = wml_text.replace('</protect>', '')

##     # 2 step
##     ## Execute custom functions
##     wml_text = function_pattern.sub(function_print, wml_text)

##     html_texts = []
##     defined_tags = parse_config(config_text)
##     # Language dependent filters
##     for ln in lns:
##         _ = gettext_set_language(ln)

##         # 3 step
##         ## Filter used to translate string in _(..)_
##         localized_wml_text = translation_pattern.sub(translate, wml_text)

##         # 4 step
##         ## Print current language 'en', 'fr', .. instead of
##         ## * in <lang:star ..> tags
##         localized_wml_text = pattern_lang_star.sub(current_lang, localized_wml_text)

##         # 5 step
##         ## Filter out languages
##         localized_wml_text = filter_languages(localized_wml_text, ln, defined_tags)

##         # 6 Step
##         ## Replace defined tags with their value from config file
##         ## Eg. replace <weburl> with 'http://cdsweb.cern.ch/':
##         for defined_tag, value in defined_tags.iteritems():
##             localized_wml_text = localized_wml_text.replace('<%s>' % defined_tag, value)

##         # 7 Step
##         # Second language filtering, in case some <lang> tags have been
##         # introduced by previous step
##         localized_wml_text = filter_languages(localized_wml_text, ln)

##         # 8 step
##         ## Get the parameters defined in dedicated tags in the wml,
##         ## and use them later to build the page:
##         ## title
##         ## navtrail_previous_links
##         ## navbar_name
##         ## navtrail_body
##         ## navbar_select
##         ## description
##         ## keywords
##         ## cdspageheaderadd
##         ## cdspageboxlefttopadd
##         ## cdspageboxleftbottomadd
##         ## cdspageboxrighttopadd
##         ## cdspageboxrightbottomadd
##         ## cdspagefooteradd
##         ##
## ##         if header_p == True:
## ##             localized_body = localized_wml_text
## ##             for tag, pattern in pattern_tags.iteritems():
## ##                 localized_body = pattern.sub(get_param_and_remove, localized_body)
## ##             if page is not None:
## ##                 out = page(title=parameters.get('WML-Page-Title', ''),
## ##                            body=localized_body,
## ##                            navtrail=parameters.get('WML-Page-Navtrail-Previous-Links', ''), # or navtrail_body ?
## ##                            description=parameters.get('WML-Page-Description', ''),
## ##                            keywords=parameters.get('WML-Page-Keywords', ''),
## ##                            uid=0,
## ##                            cdspageheaderadd=parameters.get('WML-Page-Header-Add', ''),
## ##                            cdspageboxlefttopadd=parameters.get('WML-Page-Box-Left-Top-Add', ''),
## ##                            cdspageboxleftbottomadd=parameters.get('WML-Page-Box-Left-Bottom-Add', ''),
## ##                            cdspageboxrighttopadd=parameters.get('WML-Page-Box-Right-Top-Add', ''),
## ##                            cdspageboxrightbottomadd=parameters.get('WML-Page-Box-Right-Bottom-Add', ''),
## ##                            cdspagefooteradd=parameters.get('WML-Page-Footer-Add', ''),
## ##                            lastupdated="",
## ##                            language=ln,
## ##                            verbose=verbose,
## ##                            titleprologue="",
## ##                            titleepilogue="",
## ##                            secure_page_p=0,
## ##                            req=req,
## ##                            errors=[],
## ##                            warnings=[],
## ##                            navmenuid=parameters.get('WML-Page-Navbar-Name', ''),
## ##                            navtrail_append_title_p=1,
## ##                            of="")
## ##             else:
## ##                 out = localized_wml_text
## ##         else:
## ##             out = localized_wml_text

##         out = localized_wml_text

##         html_texts.append((ln, out))
##     return html_texts

def filter_languages(text, ln='en', defined_tags=None):
    """
    Filters the language tags that do not correspond to the specified language.
    Eg: <lang><en>A book</en><de>Ein Buch</de></lang> will return
         - with ln = 'de': "Ein Buch"
         - with ln = 'en': "A book"
         - with ln = 'fr': "A book"

    Also replace variables such as <WEBURL> and <CDSNAMEINTL> inside
    <lang><..><..></lang> tags in order to print them with the correct
    language

    @param text the input text
    @param ln the language that is NOT filtered out from the input
    @return the input text as string with unnecessary languages filtered out
    @see bibformat_engine.py, from where this function was originally extracted
    """
    # First define search_lang_tag(match) and clean_language_tag(match), used
    # in re.sub() function
    def search_lang_tag(match):
        """
        Searches for the <lang>...</lang> tag and remove inner localized tags
        such as <en>, <fr>, that are not current_lang.

        If current_lang cannot be found inside <lang> ... </lang>, try to use 'cdslang'

        @param match a match object corresponding to the special tag that must be interpreted
        """
        current_lang = ln

        # If <lang keep=all> is used, keep all languages
        keep = False
        if match.group("keep") is not None:
            keep = True

        def clean_language_tag(match):
            """
            Return tag text content if tag language of match is output language.

            Called by substitution in 'filter_languages(...)'

            @param match a match object corresponding to the special tag that must be interpreted
            """
            if match.group(1) == current_lang or \
                   keep == True:
                # Additional step:
                # if there are tags such as <WEBURL> and <CDSNAMEINTL>,
                # replace them with their value, and apply the correct
                # language to them (especially CDSNAMEINTL)
                localized_text = match.group(2)
                if defined_tags is not None:
                    for defined_tag, value in defined_tags.iteritems():
                        if defined_tag.upper() == '<CDSNAMEINTL>':
                            localized_text = localized_text.replace(defined_tag, \
                                                                    value.get(current_lang, value['en']))
                        else:
                            localized_text = localized_text.replace(defined_tag, value)
                    localized_text = filter_languages(localized_text, match.group(1))

                return localized_text # match.group(2)
            else:
                return ""
            # End of clean_language_tag(..)

        lang_tag_content = match.group("langs")
        # Try to find tag with current lang. If it does not exists,
        # then current_lang becomes cdslang until the end of this
        # replace
        pattern_current_lang = re.compile(r"<("+current_lang+ \
                                          r")\s*>(.*?)(</"+current_lang+r"\s*>)", re.IGNORECASE | re.DOTALL)

        if re.search(pattern_current_lang, lang_tag_content) is None:
            current_lang = cdslang

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

def parse_config(config_text):
    """
    Get the variables defined in dedicated tags in the config file,
    and return them as dict.
    """
    defined_tags = {}
    for match in pattern_define_tag.finditer(config_text):
        tag = match.group('tag')
        value = match.group('value')
        delete_whitespace = match.group('whitespace')
        if 'delete' in delete_whitespace:
            value = value.strip()

        # Also replace <%s> with already parsed tags
        for defined_tag, defined_value in defined_tags.iteritems():
            value = value.replace('<%s>' % defined_tag, defined_value)
        defined_tags[tag] = value

    return defined_tags

def usage(exitcode=1, msg=""):
    """Prints usage info."""
    if msg:
        sys.stderr.write("Error: %s.\n" % msg)
    sys.stderr.write("Usage: %s [options]\n" % sys.argv[0])
    sys.stderr.write("  -h,  --help                \t\t Print this help.\n")
    sys.stderr.write("  -V,  --version             \t\t Print version information.\n")
    sys.stderr.write("  -v,  --verbose=LEVEL       \t\t Verbose level (0=min,1=normal,9=max).\n")
    sys.stderr.write("  -l,  --language=LN1,LN2,.. \t\t Language(s) of the output (default all)\n")
    sys.stderr.write("  -i,  --input=input.html.wml \t\t Input WML file\n")
    sys.stderr.write("  -o,  --output=output.html \t\t Path of the output file (default: same as input, without .wml extension)\n")
    sys.stderr.write("  -c,  --config=config.wml \t\t Config file\n")
    sys.stderr.write("\n")
    sys.stderr.write(" Example: webdoc -i inputfile.wml -o outputfile.html\n")
    sys.stderr.write(" Example: webdoc -i inputfile.wml -o outputfile.html -l en,fr,\n")
    sys.stderr.write(" Example: webdoc -i ../../miscutil/lib/config.py.wml -c ../../../config/config.wml -c ../../../config/configbis.wml  -o /tmp/config.py -l en ")
    sys.stderr.write("\n")

    sys.exit(exitcode)

def main():
    """
    main entry point for webdoc via command line
    """
    options = {'language':cdslangs, 'verbose':0}

    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   "hVv:l:i:o:c:",
                                   ["help",
                                    "version",
                                    "verbose=",
                                    "language=",
                                    "output="])
    except getopt.GetoptError, err:
        usage(1, err)

    try:
        for opt in opts:
            if opt[0] in ["-h", "--help"]:
                usage(0)
            elif opt[0] in ["-V", "--version"]:
                print __revision__
                sys.exit(0)
            elif opt[0] in ["-v", "--verbose"]:
                options["verbose"]  = int(opt[1])
            elif opt[0] in ["-l", "--language"]:
                options["language"]  = [wash_language(lang.strip().lower()) for lang in opt[1].split(',')]
            elif opt[0] in ["-o", "--output"]:
                options["outputfile"] = opt[1]
    except StandardError, e:
        usage(e)

    #options["inputfile"] = os.path.abspath(args[0])
    options["inputfile"] = args[0]

    if not options.has_key("inputfile"):
        usage(0)

    if not options.has_key("outputfile"):
        outputfile_components = options["inputfile"].split('.')
        options["outputfile"] = '.'.join(outputfile_components[:-1])

    if len(options["language"]) > 1 and '%(ln)s' not in options["outputfile"]:
        outputfile_components = options["outputfile"].split('.')
        options["outputfile"] = '.'.join(outputfile_components[:-1]) +'.%(ln)s.' +\
                                outputfile_components[-1]

    options["outputfile"] = os.path.abspath(options["outputfile"])

    try:
        # Load input file
        webdoc_text = file(options["inputfile"], 'r').read()
    except:
        usage(1, "Could not open file %s" %  options["inputfile"])

    config_text = ''
    if options.has_key("configfile"):
        for config_file in options["configfile"]:
            try:
                # Load config file(s).
                # We can simply concatenate them
                config_text += file(config_file, 'r').read()
            except Exception,e :
                usage(1, "Could not open file %s" %  config_file)

    # Print HTML header only when doing html output
    if options["outputfile"].endswith('html') or \
       options["outputfile"].endswith('htm') or \
       options["outputfile"].endswith('php'):
        header_p = True
    else:
        header_p = False

    # Then process for each language
##     html_texts = transform(webdoc_text,
##                            config_text,
##                            options["language"],
##                            verbose=options["verbose"],
##                            req=None,
##                            header_p=header_p)
##     for lang, html_text in html_texts:
##         html_file = open(options["outputfile"] % {'ln':lang}, 'w')
##         html_file.write(html_text)
##         html_file.close()

if __name__ == "__main__":
    main()
