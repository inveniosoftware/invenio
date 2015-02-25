#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This file is part of Invenio.
# Copyright (C) 2009, 2010, 2011 CERN.
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
"""
WebJournal Element - display article body. Also has support for old
CERN Bulletin articles.
"""
import re
import types
from invenio.utils.html import HTMLWasher
from invenio.base.i18n import gettext_set_language
from invenio.utils.url import create_html_mailto
from invenio.config import CFG_CERN_SITE
from invenio.modules.formatter.format_elements import bfe_fulltext

def format_element(bfo, separator='<br/>', max_chars=""):
    """
    Display article body

    @param separator: separator between each body
    @param max_chars: if defined, limit the output to given char length
    """
    ln = bfo.lang
    _ = gettext_set_language(ln)

    if ln == "fr":
        article = bfo.fields('590__b')
        if not article or \
               (len(article) == 1 and \
                (article[0].strip() in ['', '<br />', '<!--HTML--><br />'])):
            article = bfo.fields('520__b')
    else:
        article = bfo.fields('520__b')
        if not article or \
               (len(article) == 1 and \
                (article[0].strip() in ['', '<br />', '<!--HTML--><br />'])):
            article = bfo.fields('590__b')

    if not CFG_CERN_SITE or \
           not bfo.field('980__a').startswith('BULLETIN'):
        output = separator.join(article)
        if max_chars.isdigit() and \
               int(max_chars) > 0 and len(output) > int(max_chars):
            output = output[:int(max_chars)] + ' [...]'
        return output

    ################################################################
    #                  CERN Bulletin-specific code                 #
    ################################################################

    # We need a compatibility layer for old CERN Bulletin
    # articles. Identify them and process them if needed.
    is_old_cern_bulletin_article = False
    if bfo.field('980__a').startswith('BULLETIN'):
        try:
            year = int(bfo.fields('260__c')[0])
        except IndexError:
            year = 2000
        if year < 2009 or \
           (bfo.field('980__a').startswith('BULLETINSTAFF') and \
            ("CERN EDS" in bfo.field('595__a'))):
            is_old_cern_bulletin_article = True

    header_out = ''
    if not is_old_cern_bulletin_article:
        # Return the same as any other journal article
        output = separator.join(article)
        if max_chars.isdigit() and \
               int(max_chars) > 0 and len(output) > int(max_chars):
            output = output[:int(max_chars)] + ' [...]'
        return output

    # Old CERN articles
    if year < 2007 or bfo.field('980__a').startswith('BULLETINSTAFF'):
        # Really old CERN articles
        if len(article) > 0:
            # CERN-only: old CERN Bulletin articles
            return __backward_compatible_HTML(article[0]) + \
                   (bfo.field('980__a').startswith('BULLETINSTAFF') and \
                    ('<br/><br/>' + bfe_fulltext.format_element(bfo, style="", show_icons='yes')) \
                    or '')
        else:
            return ''

    # Not-so-old CERN articles follow:

    # 2. prepare regex's for the elements
    #=====================================================
    from invenio.legacy.webjournal.utils import \
         image_pattern, \
         para_pattern, \
         header_pattern

    page_elements = {}

    # 3. get the header (either from marc xml or regex)
    #=====================================================
    if bfo.lang == "fr":
        header = bfo.field('590__a')
        if header == '':
            header = bfo.field('520__a')
    else:
        header = bfo.field('520__a')
        if header == '':
            header = bfo.field('590__a')

    if not header:
        try:
            header_obj = re.search(header_pattern, article[0])
            header_text = header_obj.group("header")
        except:
            header_text = ""
    else:
        header_text = header


    washer = HTMLWasher()
    header_text_clean = washer.wash(html_buffer=header_text,
                                    allowed_tag_whitelist=['a'],
                                    allowed_attribute_whitelist=['href'])

    header_out = '<p class="articleHeader">' + header_text_clean + '</p>'

    # strip out all empty p tags and the header
    try:
        article = article[0].replace("<p/>", "")
        article = article.replace(header_text, "")
        article = article.replace(header_text_clean, "")
    except IndexError:
        article = ""

    image_iter = image_pattern.finditer(article)

    difference_from_original = 0
    for image in image_iter:
        page_elements[image.start()] = {"link" : image.group("hyperlink"),
                                        "image" : image.group("image"),
                                        "caption" : image.group("caption")}
        # make sure we delete the image from the article (else might be used twice)
        start_index = image.span()[0] - difference_from_original
        end_index = image.span()[1] - difference_from_original
        article = article.replace(article[start_index:end_index], "")
        difference_from_original += image.span()[1] - image.span()[0]


    # replace <center> by <p><center>
    article = article.replace("<center>", "<p><center>")
    article = article.replace("</center>", "</center></p>")

    para_iter = para_pattern.finditer(article)

    for paragraph in para_iter:
        page_elements[paragraph.start()] = paragraph.group("paragraph")


    # TODO: find a way to do this inline in the dict
    ordered_keys = page_elements.keys()
    ordered_keys.sort()

    article_out = ""
    left_right_lever = True
    did_you_know_box = False
    for key in ordered_keys:
        if type(page_elements[key]) == types.DictType:
            if left_right_lever == True:
                article_out += '<div class="phrwithcaption"><div class="imageScale">'
            else:
                article_out += '<div class="phlwithcaption"><div class="imageScale">'
            if page_elements[key]["link"] != None:
                article_out += '<a href="' + page_elements[key]["link"] + '">'
            article_out += '<img class="featureImageScaleHolder" src="' + \
                           page_elements[key]["image"] + '" border="0" />' + \
                           '</a>' + \
                           '</div>'
            if page_elements[key]["caption"] != None:
                article_out += '<p>' + page_elements[key]["caption"] + \
                               '</p>'
            article_out += '</div>'
        elif type(page_elements[key]) == types.StringType:
            left_right_lever = not left_right_lever
            if (page_elements[key].lower().find("did you know") != -1) or \
                   (page_elements[key].lower().find("le saviez-vous ?") != -1):
                did_you_know_box = True
                continue
            if did_you_know_box == True:
                did_you_know_box = False
                article_out += __did_you_know_box(page_elements[key],
                                                  left_right_lever,
                                                  bfo.lang)
                continue
            article_out += '<p>'
            article_out += page_elements[key]
            article_out += '</p>'

    output = header_out + article_out
    if max_chars.isdigit() and \
           int(max_chars) > 0 and len(output) > int(max_chars):
        output = output[:int(max_chars)] + ' [...]'

    return output

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0

def __did_you_know_box(content, left_right_lever, ln):
    """
    Formats a did you know box
    """
    _ = gettext_set_language(ln)

    box_out = ""
    box_out += '<div class="phlwithcaption">'
    box_out += '<h3 style="margin-top:0px;border-bottom:0px;" class="active">%s</h3>' % _("Did you know?")
    box_out += '<p>%s</p>' % content
    box_out += '</div>'
    return box_out

def __backward_compatible_HTML(article):
    """
    Basically only by-passing the HTML.
    Add HTML treating to old articles here.
    """
    return article

def __add_publish_buttons(title, header, uri, ln):
    """
    Prints digg, delicious, etc button
    """
    publish_area = '<ul class="publish">'
    publish_area += __add_email_button(title, uri, ln)
    publish_area += __add_digg_button(title, header)
    publish_area += __add_reddit_button(title, uri)
    publish_area += __add_delicious_button(title, uri)
    publish_area += '</ul>'
    return publish_area

def __add_email_button(title, uri, ln):
    """
    adds an email this article button, providing a standard subject text,
    title and a link to the article.
    """
    _ = gettext_set_language(ln)

    email_button = '<li id="mail">'
    email_body = _('''Hi,

Have a look at the following article:
<%(url)s>''') % uri
    email_button += create_html_mailto('',
                                       subject=title,
                                       body=email_body,
                                       link_label=_("Send this article"))
    email_button += '</li>'

    return email_button

def __add_reddit_button(title, url):
    """
    adds a button for reddit (www.reddit.com) publishing and adds url and
    title automatically to the setup.
    """
    reddit_setup = '<script>reddit_url=\'%s\'</script>' % url
    reddit_setup += '<script>reddit_title=\'%s\'</script>' % title
    reddit_button = '<li id="reddit">%s%s</li>' % (reddit_setup,
                                        '<script language="javascript" src="http://reddit.com/button.js?t=1"></script>')
    return reddit_button

def __add_delicious_button(title, url):
    """
    Sends the link with title to del.icio.us (www.del.icio.us)
    """
    delicious_button = '<li id="delicious">'
    delicious_button += '<a href="http://del.icio.us/post?url=%s&title=%s" target="_blank">Post to del.icio.us</a>' % (url,
                                                                                                                       title)
    delicious_button += '</li>'
    return delicious_button

def __add_digg_button(title, header):
    """
    provides the setup for the digg button look&feel aswell as automatically
    filled content.
    """
    digg_setup = '<script type="text/javascript">\n'
    digg_setup += 'digg_skin = \'compact\';\n'
    digg_setup += 'digg_window = \'new\';\n'
    digg_setup += 'digg_title = \'%s\';\n' % title
    digg_setup += 'digg_bodytext = \'%s\';\n' % header
    digg_setup += '</script>\n'
    digg_button = '<li id="digg">%s<script src="http://digg.com/tools/diggthis.js" type="text/javascript"></script></li>' % digg_setup
    return digg_button
