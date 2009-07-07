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
from invenio import bibformat_utils
from invenio.htmlutils import HTMLWasher
import re
import types
from invenio.access_control_engine import acc_authorize_action
from invenio.webuser import getUid

from invenio.bibformat_engine import BibFormatObject
from invenio.config import weburl
from invenio.htmlutils import HTMLWasher
from invenio.webjournal_utils import parse_url_string

from urllib import urlencode, quote

cfg_messages = {}
cfg_messages["did_you_know"] = {"en" : "Did you know?",
                    "fr" : "Le saviez-vous ?"}

def format(bfo):
    """
    formats articles of the eBulletin   
    """
    # 0. construct the editor links if needed
    # =========================================
    out = ''
    args = parse_url_string(bfo.req)
    try:
        editor = args["editor"]
    except KeyError:
        editor = False
    try:
        journal_name = args["name"]
    except:
        journal_name = ""
    try:
        issue_number = args["issue"]
    except:
        issue_number = ""
    if editor == 'True':
        try:
            report_number = bfo.field('037__a')
        except:
            report_number = "not found" # todo: exception
        try:
            recid = bfo.control_field('001')
        except:
            recid = ""
        out += '''<div style="float:right">
                    <p>
                        <a href="%s/submit/sub?RNBULLETIN=%s@MBIBULIS" target="_blank"> >> edit article</a>
                    </p>
                    <p>
                        <a href="%s/record/%s" target="_blank"> >> record on CDS</a>
                    </p>
                    <p>
                        <a href="%s/journal/regenerate?name=%s&issue=%s"> >> publish changes</a>
                    </p>
                </div>''' % (weburl, report_number,
                             weburl, recid,
                             weburl, journal_name, issue_number)
    # once req or bfo.uid are passed this would be nicer
    #try:
    #    if acc_authorize_action(bfo.uid, 'cfgwebjournal', name="CERNBulletin")[0] == 0:
    #        try:
    #           report_number = bfo.field('037__a')
    #        except:
    #            report_number = "not found" # todo: exception
    #        out += '''<div style="float:right">
    #                        <a href="%s/submit/sub?RNBULLETIN=%s@MBIBULIS" target="_blank"> >> edit article</a>
    #                </div>''' % (weburl, report_number)
    #except Exception, e:
    #    return e
            
    # 1. get the fields needed to construct an article body
    #=====================================================
    header = []
    article = []
    title = []
    if bfo.lang == "en":
        header = bfo.field('520__a')
        article = bfo.fields('520__b')
        title = bfo.fields('245__a')
        
    elif bfo.lang == "fr":
        header = bfo.field('590__a')
        article = bfo.fields('590__b')
        title = bfo.fields('246_1a')
    
    try:
        internalnotes = bfo.fields('595__a')
        if "Open Day" in internalnotes:
            openday = True
        else:
            openday = False
    except:
        openday = False
        
    try:    
        year = bfo.fields('260__c')[0]
    except:
        year = 2000
    if int(year) < int(2007):
        try:
            title = title[0]
            title_out = '<h2>' + str(title) + '</h2>'
        except:
            title_out = ''
            
        old_html = title_out + __backward_compatible_HTML(article[0])
        return old_html
    
    # 2. prepare regex's for the elements
    #=====================================================
    from invenio.webjournal_utils import image_pattern, \
                                        para_pattern, \
                                        header_pattern
    page_elements = {}    

    # 3. get the header (either from marc xml or regex)
    #=====================================================
    header_text = ""
    if header == "":
#        header = ""
        try:
            header = re.search(header_pattern, article[0])
            header_text = header.group("header")
        except:
            header = ""
    else:
        try:
            header_text = header
        except KeyError:
            header_text = ""
    washer = HTMLWasher()
    header_text_clean = washer.wash(html_buffer=header_text, allowed_tag_whitelist=[], allowed_attribute_whitelist=[])
    header_out = '<h3 id="header">' + header_text_clean + '</h3>'
    
    # strip out all empty p tags and the header
    try:
        article = article[0].replace("<p/>", "")
        article = article.replace(header_text, "")
        article = article.replace(header_text_clean, "")
    except KeyError:
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
            article_out += '<img class="featureImageScaleHolder" src="' + page_elements[key]["image"] + '" border="0" />'
            article_out += '</a>'
            article_out += '</div>'
            if page_elements[key]["caption"] != None:
                article_out += '<p>' + page_elements[key]["caption"] + '</p>'
            article_out += '</div>'
        elif type(page_elements[key]) == types.StringType:
            left_right_lever = not left_right_lever
            if (page_elements[key].lower().find("did you know") != -1) or (page_elements[key].lower().find("le saviez-vous ?") != -1):
                #if len(page_elements[key]) > len("did you know") + 8:
                #    article_out += __did_you_know_box(page_elements[key], left_right_lever, bfo.lang)
                #else:
                did_you_know_box = True
                continue
            if did_you_know_box == True:
                did_you_know_box = False
                article_out += __did_you_know_box(page_elements[key], left_right_lever, bfo.lang)
                continue
            article_out += '<p>'
            article_out += page_elements[key]
            article_out += '</p>'
            
        
    try:
        title = title[0]
    except KeyError:
        title = "untitled"
    
    title_out = '<h2 class="%s">%s</h2>'% ((openday==True) and "openday" or "",
        title)
        
    out += title_out + header_out + article_out

    
    url_params = []
    try:
        url_params.append('name=%s' % args["name"])
    except:
        pass
    try:
        url_params.append('issue=%s' % args["issue"])
    except:
        pass
    try:
        url_params.append('category=%s' % args["category"])
    except:
        pass
    try:
        url_params.append('number=%s' % args["number"])
    except:
        pass
    try:
        url_params.append('ln=' % args["ln"])
    except:
        pass
    url_string = "?" + "&".join(url_params)
    #return url_string
    try:
        this_url = '%s%s%s' % (weburl,
                                str(bfo.req.uri),
                                url_string)
    except:
        this_url = "bulletin.cern.ch"
    #out += __add_publish_buttons(title, header_text_clean, this_url, bfo.lang)
    
    return out

def __did_you_know_box(content, left_right_lever, lang):
    """
    formats a did you know box
    """
    box_out = ""
    #if left_right_lever == True:
    #    box_out += '<div class="phrwithcaption">'
    #else:
    #    box_out += '<div class="phlwithcaption">'
    box_out += '<div class="phlwithcaption">'
    box_out += '<h3 style="margin-top:0px;border-bottom:0px;" class="active">%s</h3>' % cfg_messages["did_you_know"][str(lang)]
    box_out += '<p>%s</p>' % content
    box_out += '</div>'
    return box_out

def __backward_compatible_HTML(article):
    """
    basically only by-passing the HTML.
    Add HTML treating to old articles here.
    """
    return article

def __add_publish_buttons(title, header, uri, lang):
    """
    """
    title = title.decode('utf-8')
    title = title.encode('utf-8')
    publish_area = '<ul class="publish">'
    publish_area += __add_email_button(title, uri, lang)
    publish_area += __add_digg_button(title, header)
    publish_area += __add_reddit_button(title, uri)
    publish_area += __add_delicious_button(title, uri)
    publish_area += '</ul>'
    return publish_area

def __add_email_button(title, uri, lang):
    """
    adds an email this article button, providing a standard subject text,
    title and a link to the article.
    """
    # todo: because of the "&" in urls we cannot use them in html mails, once
    # we have new url scheme we can introduce this though
    email_button = '<li id="mail">'
    #uri = uri.replace("&", "&amp;")
    #uri.encode('utf.8')
    #return uri
    if lang == 'fr':
        email_subject = 'Envoyer cet article'
        email_body = 'Cet article du Bulletin du CERN vient de vous être envoyé. Pour y accéder, cliquez sur le lien ci-dessous : %0D%0A%0D%0A' + quote(uri)
    else:
        email_subject = 'Email this article'
        email_body = 'This article from the CERN Bulletin has been sent to you. To view it, click on the link below: %0D%0A%0D%0A' + quote(uri)
        
        #email_button += '<a href="mailto:?Subject=%s&Body=%s">Email</a>' % ("This article from the CERN Bulletin has been sent to you. To view it, click on the link below:\n",
        #                                                                title+"%0A%0A"+uri)
        
    email_button += '<a href="mailto:?Subject=%s&Body=%s">Email</a>' % (email_subject,
                                                                        email_body)
    #email_button += '<a href="mailto:?%s">Email</a>' % urlencode({'Subject' : email_subject, 'Body' : email_body})
    email_button += '</li>'
    return email_button

def __add_rss_button():
    """
    """
    pass

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
            
def escape_values(bfo):
    """
    """
    return 0

if __name__ == "__main__":
    myrec = BibFormatObject(52)
    format(myrec)
