# -*- coding: utf-8 -*-
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



import re

from invenio.bibformat_engine import BibFormatObject
from invenio.search_engine import search_pattern
from invenio.htmlutils import HTMLWasher
from invenio.config import weburl

from invenio.webjournal_utils import get_order_dict_from_recid_list_CERNBulletin, \
                                    pop_newest_article_CERNBulletin, \
                                    cache_index_page, \
                                    get_index_page_from_cache, \
                                    parse_url_string
cfg_messages = {}
cfg_messages["more"] = {"en": "more",
                       "fr": "plus"}

# limit the detail view (header, image) to n entries
Detail_Limit = 3

from invenio.webjournal_utils import image_pattern, header_pattern, para_pattern


def _get_feature_image(record):
    """
    Looks for an image that can be featured on the article overview page.
    """
    #look if there is an icon
    icon = record.fields('8564_q')
    if len(icon) > 0:
        src = icon[0]
    else:
        article = record.fields('520__b')
        image = re.search(image_pattern, article[0])
        try:
            src = image.group("image")
        except:
            # no image there, do nothing
            src = ""
    return src

def _get_first_sentence_or_part(header_text):
    """
    Tries to cut the text at the end of the first sentence or an empty space
    between char 200 and 300. Else return 250 first chars.
    """
    header_text = header_text.lstrip()
    first_sentence = header_text[100:].find(".")
    if first_sentence != -1 and first_sentence < 250:
        bla = header_text[:(100+first_sentence)]
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
    #look if there is a header
    if language == "fr":
        header = record.field('590__a')
    else:
        header = record.field('520__a')
    header = washer.wash(html_buffer=header,
                            allowed_tag_whitelist=[],
                            allowed_attribute_whitelist=[])
    if header != "":
        header_text = header
    else:
        try:
            if language == "fr":
                article = record.fields('590__b')[0]
            else:
                article = record.fields('520__b')[0]
        except:
            return ""
        header = re.search(header_pattern, article)
        try:
            header_text = header.group("header")
            header_text = washer.wash(html_buffer=header_text,
                                          allowed_tag_whitelist=[],
                                          allowed_attribute_whitelist=[])
            if header_text == "":
                raise Exception
        except:
            article = article.replace(header_text, '')
            article = article.replace('<p/>', '')
            header = re.search(para_pattern, article)
            try:
                # get the first paragraph
                header_text = header.group("paragraph")
                header_text = washer.wash(html_buffer=header_text,
                                          allowed_tag_whitelist=[],
                                          allowed_attribute_whitelist=[])
                if header_text == "":
                    raise Exception
                else:
                    if len(header_text) > 250:
                        header_text = _get_first_sentence_or_part(header_text)
            except:
                # in a last instance get the first empty space
                article = washer.wash(article,
                                          allowed_tag_whitelist=[],
                                          allowed_attribute_whitelist=[])
                header_text = _get_first_sentence_or_part(article)
                #header_text = (len(article) > 150) and article[:150] or article
                header_text = washer.wash(html_buffer=header_text,
                                          allowed_tag_whitelist=[],
                                          allowed_attribute_whitelist=[])
    return header_text

def format(bfo, number_of_featured_articles="10"):
    """
    Creates an overview of all the articles of a certain category in one
    specific issue.
    There are certain categories:
        - New additions -> all stored in order 1, contain a special "new"
                           icon and are featured by title only
        - Lead article -> original order 1, featured with big title, image and
                          header
        - Detail range -> can be set by var Detail_Limit. Features an article
                          with title, image and header text
        - Rest -> All Articles after Detail_Limit. Featured with title and
                  header text.
    """
    try:
        journal_name = bfo.req.journal_defaults["name"]
        this_issue_number = bfo.req.journal_defaults["issue"]
        category_name = bfo.req.journal_defaults["category"]
        #raise '%s %s %s' % (journal_name, this_issue_number, category_name)
        # try to get the page from cache
        cached_html = get_index_page_from_cache(journal_name, category_name,
                                                this_issue_number, bfo.lang)
        if cached_html:
            return cached_html   
        out = u''
        # get the id list
        if this_issue_number[0] == '0':
            # search for 09/ and 9/
            alternative_issue_number = this_issue_number[1:]
            all_records = list(search_pattern(p='65017a:"%s" and 773__n:%s' %
                                          (category_name, this_issue_number),
                                          f="&action_search=Search"))
            alternative_all_records = list(search_pattern(p='65017a:"%s" and 773__n:%s' %
                                          (category_name, alternative_issue_number),
                                          f="&action_search=Search"))
            if len(all_records) > 0:
                ordered_articles = get_order_dict_from_recid_list_CERNBulletin(all_records,
                                                                this_issue_number)
            elif len(alternative_all_records) > 0:
                ordered_articles = get_order_dict_from_recid_list_CERNBulletin(alternative_all_records,
                                                                alternative_issue_number)
            #ordered_articles = get_order_dict_from_recid_list_CERNBulletin(all_records,
            #                                                    this_issue_number)
            #alternative_ordered_articles = get_order_dict_from_recid_list_CERNBulletin(all_records,
            #                                                    alternative_issue_number)
            #ordered_articles.update(alternative_ordered_articles)
        else:
            all_records = list(search_pattern(p='65017a:"%s" and 773__n:%s' %
                                          (category_name, this_issue_number),
                                          f="&action_search=Search"))
            ordered_articles = get_order_dict_from_recid_list_CERNBulletin(all_records,
                                                                this_issue_number) 
        # The CERN Bulletin is special, the first number can have multiple entries
        if len(ordered_articles.keys()) > 0:
            number_of_articles = len(ordered_articles.keys()) + len(
                ordered_articles[1].keys()) -1
            ordered_articles_indexes = ordered_articles.keys()
            ordered_articles_indexes.sort()
        else:
            number_of_articles = 0
            ordered_articles_indexes = []
        
        condition = int(number_of_featured_articles) < number_of_articles
        number_of_featured_articles = (condition
                                       and
                                       [int(number_of_featured_articles)] 
                                       or
                                       [len(ordered_articles.keys())])[0]
        i = 0
        while i < number_of_articles:
            flag = False
            number = str(ordered_articles_indexes[i])
            try:
                temp_recid_dict = ordered_articles[ordered_articles_indexes[i]]
                if len(temp_recid_dict.keys()) > 1:
                    i = -1 # cycle through 2nd level in 1
                    number_of_articles = number_of_articles -1
                    number = 2-len(temp_recid_dict.keys())
                    # go in the other direction of 1 -> 0, -1, -2, etc.
                    key = pop_newest_article_CERNBulletin(temp_recid_dict)
                    temp_news_tuple = temp_recid_dict.pop(int(key))
                    temp_recid = temp_news_tuple[0]
                    flag = temp_news_tuple[1]
                    if category_name == "News Articles":
                        # we don't want new news articles
                        raise KeyError
                else:
                    temp_recid = temp_recid_dict.popitem()[1][0]
            except:
                i+=1
                continue
            temp_rec = BibFormatObject(temp_recid)
            if bfo.lang == "fr":
                try:
                    title = temp_rec.fields('246_1a')[0]
                except:
                    i+=1
                    continue
                # if the french version of this article does not exist, skip to next
            else:
                try:
                    title = temp_rec.fields('245__a')[0]
                except:
                    title = "error in title"
            # OPEN DAY CODE
            try:
                internal_notes = temp_rec.fields('595__a')
                if 'Open Day' in internal_notes:
                    open_day = True
                else:
                    open_day = False
            except:
                open_day = False
            #if open_day == True:
            #    return "THIS IS AN OPEN DAY"
            article_link = (weburl + '/journal/article?issue=' + this_issue_number +
                            '&name=CERNBulletin' + '&category=' + category_name +
                            '&number=' + str(number) + '&ln=' + bfo.lang)
            more_link = '''<span class="more">
                            <a title="link to the article" href="%s"> >> </a>
                            </span>''' % (article_link)
            if i < Detail_Limit:    
                img = _get_feature_image(temp_rec)
                text = _get_feature_text(temp_rec, bfo.lang)
                out += '<div class="homesubtext">'
                # add a special "new" icon 
                if i < 0:
                    out += '''<h3 class="new %s">
                    <a title="link to the article" href="%s">%s</a>&nbsp;&nbsp;%s
                    </h3>''' % ((open_day == True) and "openday" or "",
                        article_link, title.decode('utf-8'), more_link)
                # first article is especially featured
                elif i == 0:
                    if text == "":
                        out += '''<h2 class="%s">
                        <a title="link to the article" href="%s">%s</a>
                        &nbsp;&nbsp;%s</h2>''' % ((open_day == True) and "openday" or "",
                            article_link,
                                                  title.decode('utf-8'), more_link)
                    else:
                        out += '''<h2 class="%s">
                        <a title="link to the article" href="%s">%s</a>
                        </h2>''' % ((open_day == True) and "openday" or "",
                            article_link, title.decode('utf-8'))
                    if img != "":
                        out += '''<h4><div class="phl">
                            <div class="featureImageScale">
                            <img class="featureImageScaleHolder" src="%s" />
                        </div></div>%s %s</h4>''' % (img,
                                                    text.decode('utf-8'), more_link) 
                    elif text != "":
                        out += '<h4>%s %s</h4>' % (text.decode('utf-8'), more_link)
                else:
                    if text == "":
                        out += '''<h3 class="%s" style="clear:both;">
                        <a title="link to the article" href="%s">%s</a>
                        &nbsp;&nbsp;%s</h3>''' % ((open_day == True) and "openday" or "",
                            article_link,
                                                  title.decode('utf-8'), more_link)
                    else:
                        out += '''<h3 class="%s" style="clear:both;">
                        <a title="link to the article" href="%s">%s</a>
                        </h3>''' % ((open_day == True) and "openday" or "",
                            article_link, title.decode('utf-8'))
                    if img != "":
                        out += '''<h4><div class="phl">
                        <div class="featureImageScaleSmall">
                        <img class="featureImageScaleHolder" src="%s" />
                        </div></div>%s %s</h4>''' % (img,
                                                    text.decode('utf-8'), more_link)
                    elif text != "":
                        out += '<h4>%s %s</h4>' % (text.decode('utf-8'), more_link)
                out += '</div>'
            else:
                text = _get_feature_text(temp_rec, bfo.lang)
                out += '<div class="homesubtext">'
                if text == "":
                    out += '''<h3 class="%s" style="clear:both;">
                    <a title="link to the article" href="%s">%s</a>
                    &nbsp;&nbsp;%s</h3>''' % ((open_day == True) and "openday" or "",
                        article_link,
                                              title.decode('utf-8'), more_link)
                else:
                    out += '''<h3 class="%s" style="clear:both;">
                    <a title="link to the article" href="%s">%s</a>
                    </h3>''' % ((open_day == True) and "openday" or "",
                        article_link, title.decode('utf-8'))
                    out += '<h4>%s %s</h4>' % (text.decode('utf-8'), more_link)
                out += '</div>'
            i+=1
        
        cache_index_page(out.encode('utf-8'), journal_name, category_name,
                         this_issue_number, bfo.lang)    
            
        return out.encode('utf-8')
    except Exception, e:
        return "Error: %s" % e
        

def escape_values(bfo):
    """
    """
    return 0

if __name__ == "__main__":
    myrec = BibFormatObject(87)
    format(myrec)
