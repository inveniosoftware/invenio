# -*- coding: utf-8 -*-
# $Id: bfe_webjournal_MainArticleOverview.py,v 1.28 2009/02/12 10:00:57 jerome Exp $
#
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
WebJournal Element - Creates an overview of all the articles of a
certain category in one specific issue.
"""
import re
import os
import urllib, urllib2
try:
    from PIL import Image
    PIL_imported = True
except ImportError:
    PIL_imported = False
from invenio.modules.formatter.engine import BibFormatObject
from invenio.utils.html import HTMLWasher, remove_html_markup
from invenio.base.i18n import gettext_set_language
from invenio.config import \
     CFG_ACCESS_CONTROL_LEVEL_SITE, \
     CFG_TMPDIR, \
     CFG_SITE_LANG
from invenio.legacy.webjournal.utils import \
     cache_index_page, \
     get_index_page_from_cache, \
     parse_url_string, \
     make_journal_url, \
     get_journal_articles, \
     issue_is_later_than, \
     get_current_issue
from invenio.legacy.webjournal.utils import \
     img_pattern, \
     header_pattern, \
     header_pattern2, \
     para_pattern
from invenio.utils.url import create_html_link
from invenio.legacy.bibdocfile.api import decompose_file

def format_element(bfo, number_of_featured_articles="1",
           number_of_articles_with_image="3", new_articles_first='yes',
           image_px_width="300", small_image_px_width="200",
           subject_to_css_class_kb="WebJournalSubject2CSSClass",
           link_image_to_article='yes', image_alignment='left'):
    """
    Creates an overview of all the articles of a certain category in one
    specific issue.

    Note the following:
    <ul>
    <li>The element consider only the latest issue: when viewing
    archives of your journal, readers will see the newest articles of
    the latest issue, not the ones of the issue they are looking
    at</li>

    <li>This is not an index of the articles of the latest issue: it
    display only <b>new</b> articles, that is articles that have never
    appeared in a previous issue</li>

    <li>This element produces a table-based layout, in order to have a
    more or less readable HTML alert when sent some Email clients
    (Outlook 2007)</li>

    <li>When producing the HTML output of images, this element tries to
    insert the width and height attributes to the img tag: this is
    necessary in order to produce nice HTML alerts. This dimension
    therefore overrides any dimension defined in the CSS. The Python
    Image Library (PIL) should be installed for this element to
    recognize the size of images.</li>
    </ul>

    @param number_of_featured_articles: the max number of records with emphasized title
    @param number_of_articles_with_image: the max number of records for which their image is displayed
    @param new_articles_first: if 'yes', display new articles before other articles
    @param image_px_width: (integer) width of first image featured on this page
    @param small_image_px_width: (integer) width of small images featured on this page
    @param subject_to_css_class_kb: knowledge base that maps 595__a to a CSS class
    @param link_image_to_article: if 'yes', link image (if any) to article
    @param image_alignment: 'left', 'center' or 'right'. To help rendering in Outlook.
    """
    args = parse_url_string(bfo.user_info['uri'])
    journal_name = args["journal_name"]
    this_issue_number = args["issue"]
    category_name = args["category"]
    verbose = args["verbose"]
    ln = bfo.lang
    _ = gettext_set_language(ln)

    if image_px_width.isdigit():
        image_px_width = int(image_px_width)
    else:
        image_px_width = None
    if small_image_px_width.isdigit():
        small_image_px_width = int(small_image_px_width)
    else:
        small_image_px_width = None

    # We want to put emphasis on the n first articles (which are not
    # new)
    if number_of_featured_articles.isdigit():
        number_of_featured_articles = int(number_of_featured_articles)
    else:
        number_of_featured_articles = 0

    # Only n first articles will display images
    if number_of_articles_with_image.isdigit():
        number_of_articles_with_image = int(number_of_articles_with_image)
    else:
        number_of_articles_with_image = 0

    # Help image alignement without CSS, to have better rendering in Outlook
    img_align = ''
    if image_alignment:
        img_align = 'align="%s"' % image_alignment

    # Try to get the page from cache. Only if issue is older or equal
    # to latest release.
    latest_released_issue = get_current_issue(ln, journal_name)
    if verbose == 0 and not issue_is_later_than(this_issue_number,
                                                latest_released_issue):
        cached_html = get_index_page_from_cache(journal_name, category_name,
                                                this_issue_number, ln)
        if cached_html:
            return cached_html

    out = '<table border="0" cellpadding="0" cellspacing="0">'
    # Get the id list
    ordered_articles = get_journal_articles(journal_name,
                                            this_issue_number,
                                            category_name,
                                            newest_first=new_articles_first.lower() == 'yes')
    new_articles_only = False
    if ordered_articles.keys() and max(ordered_articles.keys()) < 0:
        # If there are only new articles, don't bother marking them as
        # new
        new_articles_only = True

    order_numbers = ordered_articles.keys()
    order_numbers.sort()
    img_css_class = "featuredImageScale"

    for order_number in order_numbers:
        for article_id in ordered_articles[order_number]:
            # A record is considered as new if its position is
            # negative and there are some non-new articles
            article_is_new = (order_number < 0 and not new_articles_only)

            temp_rec = BibFormatObject(article_id)
            title = ''
            if ln == "fr":
                title = temp_rec.field('246_1a')
                if title == '':
                    title = temp_rec.field('245__a')
            else:
                title = temp_rec.field('245__a')
                if title == '':
                    title = temp_rec.field('246_1a')

            # Get CSS class (if relevant)
            notes = temp_rec.fields('595__a')
            css_classes = [temp_rec.kb(subject_to_css_class_kb, note, None) \
                           for note in notes]
            css_classes = [css_class for css_class in css_classes \
                           if css_class is not None]

            if article_is_new:
                css_classes.append('new')

            # Maybe we want to force image to appear?
            display_image_on_index = False
            if 'display_image_on_index' in notes:
                display_image_on_index = True

            # Build generic link to this article
            article_link = make_journal_url(bfo.user_info['uri'], {'recid':str(article_id),
                                                                   'ln': bfo.lang})

            # Build the "more" link
            more_link = '''<a class="readMore" title="link to the article" href="%s"> &gt;&gt; </a>
                        ''' % (article_link)

            # If we should display an image along with the text,
            # prepare it here
            img = ''
            if (number_of_articles_with_image > 0 and \
                   not article_is_new) or display_image_on_index:
                img = _get_feature_image(temp_rec, ln)
                if img != "":
                    # Now we will try to identify image size in order
                    # to resize it in the HTML for a nicer rendering
                    # of the HTML alert in email clients (Outlook wants
                    # both height and width)
                    img_width = None
                    img_height = None
                    small_img_width = None
                    small_img_height = None
                    width_and_height = ''
                    if PIL_imported:
                        try:
                            local_img = os.path.join(CFG_TMPDIR,
                                                     'webjournal_' + \
                                                     ''.join([char for char in img \
                                                              if char.isalnum()]))
                            if len(local_img) > 255:
                                # Shorten to 255 chars
                                local_img = local_img[0:100] + '_' + local_img[156:]
                            if not os.path.exists(local_img):
                                # Too bad, must download entire image for PIL
                                content_type = get_content_type(img)
                                if 'image' in content_type:
                                    (local_img, headers) = urllib.urlretrieve(img, local_img)
                                    img_file = Image.open(local_img) # IOError if not readable image
                                else:
                                    raise IOError('Not an image')
                            else:
                                img_file = Image.open(local_img) # IOError if not readable image
                        except IOError as e:
                            pass
                        else:
                            orig_img_width = img_file.size[0]
                            orig_img_height = img_file.size[1]
                            # Then scale according to user-defined width
                            ## First image
                            ratio = float(orig_img_width) / image_px_width
                            img_width = image_px_width
                            img_height = int(orig_img_height / ratio)
                            ## Other smaller images
                            ratio = float(orig_img_width) / small_image_px_width
                            small_img_width = small_image_px_width
                            small_img_height = int(orig_img_height / ratio)

                    # Note that we cannot reuse the nice phl, ph and
                    # phr classes to put a frame around the image:
                    # this is not supported in Outlook 2007 when HTML
                    # alert is sent.
                    if not img_css_class == "featuredImageScale":
                        # Not first image: display smaller
                        img_width = small_img_width
                        img_height = small_img_height

                    if img_width and img_height:
                        width_and_height = 'width="%i" height="%i"' % \
                                           (img_width, img_height)
                    img = '<img alt="" class="%s" src="%s" %s %s/>' % \
                          (img_css_class, img, img_align, width_and_height)
                    number_of_articles_with_image -= 1

                    # Next images will be displayed smaller
                    img_css_class = "featuredImageScaleSmall"

            # Determine size of the title
            header_tag_size = '3'
            if number_of_featured_articles > 0 and \
                   not article_is_new:
                # n first articles are especially featured
                header_tag_size = '2'
                number_of_featured_articles -= 1

            # Finally create the output. Two different outputs
            # depending on if we have text to display or not
            text = ''
            if not article_is_new:
                text = _get_feature_text(temp_rec, ln)
            # Link image to article if wanted
            if link_image_to_article.lower() == 'yes':
                img = create_html_link(urlbase=article_link,
                                       link_label=img,
                                       urlargd={})
            if text != '':
                out += '''
                        <tr><td class="article">
                           <h%(header_tag_size)s class="%(css_classes)s articleTitle" style="clear:both;">
                               <a title="link to the article" href="%(article_link)s">%(title)s</a>
                           </h%(header_tag_size)s>
                           <div class="articleBody">
                               %(img)s
                               %(text)s
                               %(more_link)s
                           </div>
                       </td></tr>
                    ''' % {'article_link': article_link,
                           'title': title,
                           'img': img,
                           'text': text,
                           'more_link': more_link,
                           'css_classes': ' '.join(css_classes),
                           'header_tag_size': header_tag_size}
            else:
                out += '''
                       <tr><td class="article">
                           <h%(header_tag_size)s class="%(css_classes)s articleTitle" style="clear:both;">
                               <a title="link to the article" href="%(article_link)s">%(title)s</a>&nbsp;&nbsp;
                               %(more_link)s
                           </h%(header_tag_size)s>
                           %(img)s
                       </td></tr>
                       ''' % {'article_link': article_link,
                              'title': title,
                              'more_link': more_link,
                              'img': img,
                              'css_classes': ' '.join(css_classes),
                              'header_tag_size': header_tag_size}
    out += '</table>'
    if verbose == 0 and not CFG_ACCESS_CONTROL_LEVEL_SITE == 2 :
        cache_index_page(out, journal_name, category_name,
                         this_issue_number, ln)

    return out

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0

def _get_feature_image(record, ln=CFG_SITE_LANG):
    """
    Looks for an image that can be featured on the article overview page.
    """
    src = ''
    if ln == "fr":
        article = ''.join(record.fields('590__b'))
        if not article:
            article = ''.join(record.fields('520__b'))
    else:
        article = ''.join(record.fields('520__b'))
        if not article:
            article = ''.join(record.fields('590__b'))

    image = re.search(img_pattern, article)
    if image:
        src = image.group("image")
    if not src:
        # Look for an attached image
        icons = [icon for icon in record.fields('8564_q') if \
                (decompose_file(icon)[2] in ['jpg', 'jpeg', 'png', 'gif'])]
        if icons:
            src = icons[0]
    return src

def _get_first_sentence_or_part(header_text):
    """
    Tries to cut the text at the end of the first sentence or an empty space
    between char 200 and 300. Else return 250 first chars.
    """
    header_text = header_text.lstrip()
    first_sentence = header_text[100:].find(".")
    if first_sentence == -1:
        # try question mark
        first_sentence = header_text[100:].find("?")
    if first_sentence == -1:
        # try exclamation mark
        first_sentence = header_text[100:].find("!")
    if first_sentence != -1 and first_sentence < 250:
        return "%s." % header_text[:(100+first_sentence)]
    else:
        an_empty_space = header_text[200:].find(" ")
        if an_empty_space != -1 and an_empty_space < 300:
            return "%s..." % header_text[:(200+an_empty_space)]
        else:
            return "%s..." % header_text[:250]

def _get_feature_text(record, language):
    """
    Looks for a text (header) that can be featured on the article overview
    page.
    """
    washer = HTMLWasher()
    header_text = ""
    # Check if there is a header
    if language == "fr":
        header = record.field('590__a')
        if header.strip() in \
               ['', '<br/>', '<!--HTML--><br />', '<!--HTML-->']:
            header = record.field('520__a')
    else:
        header = record.field('520__a')
        if header.strip() in \
               ['', '<br/>', '<!--HTML--><br />', '<!--HTML-->']:
            header = record.field('590__a')
    header = washer.wash(html_buffer=header,
                         allowed_tag_whitelist=[],
                         allowed_attribute_whitelist=[])
    if header != "":
        header_text = header
    else:
        if language == "fr":
            article = record.fields('590__b')
            if not article or \
                   (len(article) == 1 and \
                    article[0].strip() in \
                    ['', '<br />', '<!--HTML--><br />', '<!--HTML-->']):
                article = record.fields('520__b')
        else:
            article = record.fields('520__b')
            if not article or \
                   (len(article) == 1 and \
                    article[0].strip() in \
                    ['', '<br />', '<!--HTML--><br />', '<!--HTML-->']):
                article = record.fields('590__b')
        try:
            article = article[0]
        except:
            return ''

        match_obj = re.search(header_pattern, article)
        if not match_obj:
            match_obj = re.search(header_pattern2, article)
        try:
            header_text = match_obj.group("header")
            header_text = washer.wash(html_buffer=header_text,
                                      allowed_tag_whitelist=['a'],
                                      allowed_attribute_whitelist=['href',
                                                                   'target',
                                                                   'class'])
            if header_text == "":
                raise Exception
        except:
            article = article.replace(header_text, '')
            article = article.replace('<p/>', '')
            article = article.replace('<p>&nbsp;</p>', '')
            match_obj = re.search(para_pattern, article)
            try:
                # get the first paragraph
                header_text = match_obj.group("paragraph")
                try:
                    header_text = washer.wash(html_buffer=header_text,
                                              allowed_tag_whitelist=[],
                                              allowed_attribute_whitelist=[])
                except:
                    # was not able to parse correctly the HTML. Use
                    # this safer function, but producing less good
                    # results
                    header_text = remove_html_markup(header_text)

                if header_text.strip() == "":
                    raise Exception
                else:
                    if len(header_text) > 250:
                        header_text = _get_first_sentence_or_part(header_text)
            except:
                # in a last instance get the first sentence
                try:
                    article = washer.wash(article,
                                          allowed_tag_whitelist=[],
                                          allowed_attribute_whitelist=[])
                except:
                    # was not able to parse correctly the HTML. Use
                    # this safer function, but producing less good
                    # results
                    article = remove_html_markup(article)

                header_text = _get_first_sentence_or_part(article)

    return header_text

def get_content_type(url):
    """
    Returns the content-type of the given URL.
    Return empty string if content-type could not be resolved

    @param url: URL for which we would like to get the content-type
    @type url: string
    @return: the content-type of the given URL
    @rtype: string
    """
    req = urllib2.Request(url)
    try:
        response = urllib2.urlopen(req)
        return response.info().getheader('content-type')
    except Exception as e:
        return ''
