# This file is part of Invenio.
# Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2014, 2015 CERN.
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

""" Templating for webbasket module """

__revision__ = "$Id$"

import cgi
import urllib

from invenio.base.globals import cfg
from invenio.base.i18n import gettext_set_language
from invenio.utils.mail import email_quoted_txt2html, \
                                         email_quote_txt, \
                                         escape_email_quoted_text
from invenio.utils.html import get_html_text_editor
from invenio.config import \
     CFG_SITE_URL, \
     CFG_SITE_SECURE_URL, \
     CFG_SITE_LANG
from invenio.legacy.webuser import get_user_info
from invenio.utils.date import convert_datetext_to_dategui
from invenio.legacy.webbasket.db_layer import get_basket_ids_and_names

ICON_BACK = 'icon-arrow-left'
ICON_CREATE_BASKET = 'glyphicon glyphicon-plus'
ICON_EDIT_BASKET = 'icon-wrench'
ICON_DELETE_BASKET = 'icon-trash'

ICON_ADD_ITEM = 'glyphicon glyphicon-plus'
ICON_MOVE_ITEM = 'icon-share-alt'
ICON_COPY_ITEM = 'glyphicon glyphicon-plus-sign'
ICON_REMOVE_ITEM = 'icon-trash'

ICON_MOVE_UP = 'icon-arrow-up'
ICON_MOVE_UP_MUTED = 'icon-arrow-up text-muted'
ICON_MOVE_DOWN = 'icon-arrow-down'
ICON_MOVE_DOWN_MUTED = 'icon-arrow-down text-muted'
ICON_NEXT_ITEM = 'icon-arrow-right'
ICON_NEXT_ITEM_MUTED = 'icon-arrow-right text-muted'
ICON_PREVIOUS_ITEM = 'icon-arrow-left'
ICON_PREVIOUS_ITEM_MUTED = 'icon-arrow-left text-muted'

ICON_NOTES = 'icon-file'
ICON_ADD_NOTE = 'glyphicon glyphicon-pencil'


class Template:
    """Templating class for webbasket module"""
    ######################## General interface ################################

    def tmpl_create_directory_box(self,
                                  category, topic,
                                  (grpid, group_name),
                                  bskid,
                                  (personal_info, personal_baskets_info),
                                  (group_info, group_baskets_info),
                                  public_info,
                                  ln):
        """Template for the directory-like menu.
        @param category: the selected category
        @param topic: the selected topic (optional)
        @param (grpid, groupname): the id and name of the selected group (optional)
        @param bskid: the id of the selected basket (optional)
        @param (personal_info, personal_baskets_info): personal baskets data
        @param (group_info, group_baskets_info): group baskets data
        @param public_info: public baskets data
        @param ln: language"""

        _ = gettext_set_language(ln)

        def __calculate_prettify_name_char_limit(nb_baskets, max_chars=45, nb_dots=3):
            """Private function. Calculates the char_limit to be fed to the
            prettify_name function according to the max_chars limit and the nb_dots."""

            # Let's do some initial calculations:
            D = nb_dots
            B = nb_baskets
            M = max_chars
            # some assisting abbreviations
            Y = ( B > 3 and 2 or B - 1 )
            Z = ( B > 3 and 5 or 0 )
            # and the desired result
            X = ( ( M - Z - ( ( 2 + D ) * Y ) - D ) / ( Y + 1 ) )
            return X

        if not personal_info and not group_info and not public_info:
            return """
    %(no_baskets_label)s
    <br /><br />
    %(create_basket_label)s""" % \
    {'no_baskets_label': _('You have no personal or group baskets or are subscribed to any public baskets.'),
     'create_basket_label': _('You may want to start by %(x_url_open)screating a new basket%(x_url_close)s.',
                              x_url_open='<a href="%s/yourbaskets/create_basket?ln=%s">' % (CFG_SITE_URL, ln),
                              x_url_close='</a>')}

        ## First, create the tabs area.
        if personal_info:
            ## If a specific topic is selected display the name of the topic
            ## and the options on it.
            if personal_baskets_info:
                personalbaskets_link = """<a href="%(url)s/yourbaskets/display?category=%(category)s&amp;ln=%(ln)s">%(label)s</a>""" % \
                                       {'url': CFG_SITE_URL,
                                        'category': cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE'],
                                        'ln': ln,
                                        'label': _('Personal baskets')}
                topic_link = """<a href="%(url)s/yourbaskets/display?category=%(category)s&amp;topic=%(topic)s&amp;ln=%(ln)s">%(label)s</a>""" % \
                             {'url': CFG_SITE_URL,
                              'category': cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE'],
                              'topic': urllib.quote(topic),
                              'ln': ln,
                              'label': cgi.escape(topic, True)}
                go_back_link = """<a href="%(url)s/yourbaskets/display?ln=%(ln)s"><i class="icon %(icon)s"></i> %(label)s</a>""" % \
                               {'url': CFG_SITE_URL,
                                'ln': ln,
                                'icon': ICON_BACK,
                                'label': _('Back to Your Baskets')}
                create_basket_link = """<a href="%(url)s/yourbaskets/create_basket?topic=%(topic)s&amp;ln=%(ln)s"><i class="icon %(icon)s"></i> %(label)s</a>""" % \
                                     {'url': CFG_SITE_URL,
                                      'topic': urllib.quote(topic),
                                      'ln': ln,
                                      'icon': ICON_CREATE_BASKET,
                                      'label': _('Create basket')}
                edit_topic_link = """<a href="%(url)s/yourbaskets/edit_topic?topic=%(topic)s&amp;ln=%(ln)s"><i class="icon %(icon)s"></i> %(label)s</a>""" % \
                                  {'url': CFG_SITE_URL,
                                   'topic': urllib.quote(topic),
                                   'ln': ln,
                                   'icon': ICON_EDIT_BASKET,
                                   'label': _('Edit topic')}
                personal_tab = """
              <div class="row-fluid">
                <div class="col-md-7 bsk_directory_box_nav_tab_content">
                  %(personalbaskets_link)s&nbsp;&gt;&nbsp;%(topic_link)s
                </div>
                <div class="col-md-5 pagination-right bsk_directory_box_nav_tab_options">
                  %(go_back)s
                  &nbsp;&nbsp;
                  %(create_basket)s
                  &nbsp;&nbsp;
                  %(edit_topic)s
                </div>""" % {'topic_link': topic_link,
                             'personalbaskets_link': personalbaskets_link,
                             'go_back': go_back_link,
                             'create_basket': create_basket_link,
                             'edit_topic': edit_topic_link}
            ## If no specific topic is selected display the personal baskets tab.
            else:
                personal_tab = """
              <td class="%(class)s">
              <a href="%(url)s/yourbaskets/display?category=%(category)s&amp;ln=%(ln)s">%(label)s</a>
              </td>""" % {'class': category == cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE'] \
                          and "bsk_directory_box_tab_content_selected" \
                          or "bsk_directory_box_tab_content",
                          'url': CFG_SITE_URL,
                          'category': cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE'],
                          'ln': ln,
                          'label': _('Personal baskets')}
        else:
            personal_tab = """
              <td class="%(class)s">
              %(label)s
              </td>""" % {'class': 'bsk_directory_box_tab_content_inactive',
                          'label': _('Personal baskets')}

        if group_info:
            ## If a specific group is selected display the name of the group
            ## and the options on it.
            if group_baskets_info:
                groupbaskets_link = """<a href="%(url)s/yourbaskets/display?category=%(category)s&amp;ln=%(ln)s">%(label)s</a>""" % \
                                    {'url': CFG_SITE_URL,
                                     'category': cfg['CFG_WEBBASKET_CATEGORIES']['GROUP'],
                                     'ln': ln,
                                     'label': _('Group baskets')}
                group_link = """<a href="%(url)s/yourbaskets/display?category=%(category)s&amp;group=%(grpid)i&amp;ln=%(ln)s">%(label)s</a>""" % \
                             {'url': CFG_SITE_URL,
                              'category': cfg['CFG_WEBBASKET_CATEGORIES']['GROUP'],
                              'grpid': grpid,
                              'ln': ln,
                              'label': cgi.escape(group_name, True)}
                go_back_link = """<a href="%(url)s/yourbaskets/display?ln=%(ln)s"><i class="icon %(icon)s"></i> %(label)s</a>""" % \
                               {'url': CFG_SITE_URL,
                                'ln': ln,
                                'icon': ICON_BACK,
                                'label': _('Back to Your Baskets')}
                group_tab = """
              <td class="bsk_directory_box_nav_tab_content">
              %(groupbaskets_link)s&nbsp;&gt;&nbsp;%(group_link)s
              </td>
              <td class="bsk_directory_box_nav_tab_options">
              %(go_back)s
              </td>""" % {'groupbaskets_link': groupbaskets_link,
                          'group_link': group_link,
                          'go_back': go_back_link}
            ## If no specific group is selected display the group baskets tab.
            else:
                group_tab = """
              <td class="%(class)s">
              <a href="%(url)s/yourbaskets/display?category=%(category)s&amp;ln=%(ln)s">%(label)s</a>
              </td>""" % {'class': category == cfg['CFG_WEBBASKET_CATEGORIES']['GROUP'] \
                          and "bsk_directory_box_tab_content_selected" \
                          or "bsk_directory_box_tab_content",
                          'url': CFG_SITE_URL,
                          'category': cfg['CFG_WEBBASKET_CATEGORIES']['GROUP'],
                          'ln': ln,
                          'label': _('Group baskets')}
        else:
            group_tab = """
              <td class="%(class)s">
              %(label)s
              </td>""" % {'class': 'bsk_directory_box_tab_content_inactive',
                          'label': _('Group baskets')}

        if public_info:
            ## Display the public baskets tab.
            public_tab = """
              <td class="%(class)s">
              <a href="%(url)s/yourbaskets/display?category=%(category)s&amp;ln=%(ln)s">%(label)s</a>
              </td>""" % {'class': category == cfg['CFG_WEBBASKET_CATEGORIES']['EXTERNAL'] \
                          and "bsk_directory_box_tab_content_selected" \
                          or "bsk_directory_box_tab_content",
                          'url': CFG_SITE_URL,
                          'category': cfg['CFG_WEBBASKET_CATEGORIES']['EXTERNAL'],
                          'ln': ln,
                          'label': _('Public baskets')}
        else:
            public_tab = """
              <td class="%(class)s">
              %(label)s
              </td>""" % {'class': 'bsk_directory_box_tab_content_inactive',
                          'label': _('Public baskets')}

        ## If a specific topic is selected display the name of the topic
        ## and the options on it.

        tabs = """<div class="row-fluid well bsk_directory_box_tabs">"""

        if personal_baskets_info:
            tabs += """
            <div class="col-md-12">
              %s
            </div>""" % (personal_tab,)

        ## If a specific group is selected display the name of the group
        ## and the options on it.
        elif group_baskets_info:
            tabs += """
            <div class="col-md-12">
              %s
            </div>""" % (group_tab,)
        ## If only a sepcific category is selected (or eveb none) display
        ## all the available tabs (selected, normal, inactive).
        else:
            tabs += """

            <div class="col-md-4">
                %(personal_tab)s
            </div>
            <div class="col-md-4">
                %(group_tab)s
            </div>
            <div class="col-md-4">
                %(public_tab)s
            </div>""" % {'personal_tab': personal_tab,
                         'group_tab': group_tab,
                         'public_tab': public_tab}

        tabs += """</div>"""

        ## Secondly, create the content.
        if personal_info and category==cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE']:
            content_list = []
            ## If a specific topic is selected create a list of baskets for that topic.
            if personal_baskets_info:
                for basket in personal_baskets_info:
                    basket_id = basket[0]
                    basket_name = basket[1]
                    nb_items = basket[4]
                    basket_link = """%(opening_tag)s<a href="%(url)s/yourbaskets/display?category=%(category)s&amp;topic=%(topic)s&amp;bskid=%(bskid)i&amp;ln=%(ln)s" title="%(title_name)s">%(basket_name)s</a>%(closing_tag)s <span class="bsk_directory_box_content_list_number_of">(%(nb_items)i)</span>""" % \
                                 {'opening_tag': basket_id==bskid and "<em>" or "",
                                  'closing_tag': basket_id==bskid and "</em>" or "",
                                  'url': CFG_SITE_URL,
                                  'category': category,
                                  'topic': urllib.quote(topic),
                                  'bskid': basket_id,
                                  'ln': ln,
                                  'title_name': cgi.escape(basket_name, True),
                                  'basket_name': cgi.escape(prettify_name(basket_name, 27), True),
                                  'nb_items': nb_items}
                    content_list_item = """
                      %(basket_link)s""" % {'basket_link': basket_link}
                    content_list.append(content_list_item)
            ## If no specific topic is selected create a list of topics with a preview of their baskets.
            else:
                for topic_and_bskids in personal_info:
                    topic_name = topic_and_bskids[0]
                    bskids = topic_and_bskids[1].split(',')
                    nb_baskets = len(bskids)
                    topic_link = """<strong><a href="%(url)s/yourbaskets/display?category=%(category)s&amp;topic=%(topic)s&amp;ln=%(ln)s" title="%(title_name)s">%(topic_name)s</a></strong> <span class="bsk_directory_box_content_list_number_of">(%(nb_baskets)s)</span>""" % \
                                 {'url': CFG_SITE_URL,
                                  'category': category,
                                  'topic': urllib.quote(topic_name),
                                  'ln': ln,
                                  'title_name': cgi.escape(topic_name, True),
                                  'topic_name': cgi.escape(prettify_name(topic_name, 25), True),
                                  'nb_baskets': nb_baskets}
                    basket_links = ""
                    basket_links_list = []
                    #TODO: Not have the number of basket names displayed hardcoded (3 in this case)
                    bskids_and_names = get_basket_ids_and_names(bskids, 3)
                    for bskid_and_name in bskids_and_names:
                        bskid = bskid_and_name[0]
                        basket_name = bskid_and_name[1]
                        #TODO: adapt the prettify_name char_limit variable according to nb_baskets
                        basket_link = """<a href="%(url)s/yourbaskets/display?category=%(category)s&amp;topic=%(topic)s&amp;bskid=%(bskid)i&amp;ln=%(ln)s" title="%(title_name)s">%(basket_name)s</a>""" % \
                                      {'url': CFG_SITE_URL,
                                       'category': category,
                                       'topic': urllib.quote(topic_name),
                                       'bskid': bskid,
                                       'ln': ln,
                                       'title_name': cgi.escape(basket_name, True),
                                       'basket_name': cgi.escape(prettify_name(basket_name, __calculate_prettify_name_char_limit(nb_baskets, 135/cfg['CFG_WEBBASKET_DIRECTORY_BOX_NUMBER_OF_COLUMNS'])), True)}
                        basket_links_list.append(basket_link)
                        basket_links = ', '.join(basket_links_list)
                    if nb_baskets > 3:
                        basket_links += ", ..."
                    content_list_item = """
                      %(topic_link)s
                      <br />
                      <small>%(basket_links)s</small>""" % \
                                     {'topic_link': topic_link,
                                      'basket_links': basket_links}
                    content_list.append(content_list_item)

            nb_cells = cfg['CFG_WEBBASKET_DIRECTORY_BOX_NUMBER_OF_COLUMNS']
            nb_items = len(content_list)
            content_list.reverse()
            content = """
                <div class="row-fluid">
                    <div class="col-md-12">
                        <table cellspacing="0px" cellpadding="0px" align="center" width="100%">
                          <tr>"""
            for i in range(nb_cells):
                content += """
                    <td class="bsk_directory_box_content_list_cell" width="%s%%">""" % \
                              (100/nb_cells,)
                nb_lines = (nb_items/nb_cells) + ((nb_items%nb_cells) > i and 1 or 0)
                for j in range(nb_lines):
                    content += content_list.pop()
                    if j < (nb_lines-1):
                        content += personal_baskets_info and "<br />" or "<br /><br />"
                content += """
                    </td>"""
            content += """
                  </tr>
                        </table>
                    </div>
                </div>"""
            if not personal_baskets_info:
                create_basket_link = """<a href="%(url)s/yourbaskets/create_basket?topic=%(topic)s&amp;ln=%(ln)s"><i class="icon %(icon)s"></i> %(label)s</a>""" % \
                                     {'url': CFG_SITE_URL,
                                      'topic': urllib.quote(topic),
                                      'ln': ln,
                                      'icon': ICON_CREATE_BASKET,
                                      'label': _('Create basket')}
                content += """
                <div class="row-fluid well">
                    <div class="col-md-5 offset7 pagination-right bsk_directory_box_nav_extra_options">
                        %s
                    </div>
                </div>""" % (create_basket_link,)

        elif group_info and category==cfg['CFG_WEBBASKET_CATEGORIES']['GROUP']:
            content_list = []
            ## If a specific grpid is selected create a list of baskets for that group.
            if group_baskets_info:
                for basket in group_baskets_info:
                    basket_id = basket[0]
                    basket_name = basket[1]
                    nb_items = basket[4]
                    basket_link = """%(opening_tag)s<a href="%(url)s/yourbaskets/display?category=%(category)s&amp;group=%(grpid)i&amp;bskid=%(bskid)i&amp;ln=%(ln)s" title="%(title_name)s">%(basket_name)s</a>%(closing_tag)s <span class="bsk_directory_box_content_list_number_of">(%(nb_items)i)</span>""" % \
                                 {'opening_tag': basket_id==bskid and "<em>" or "",
                                  'closing_tag': basket_id==bskid and "</em>" or "",
                                  'url': CFG_SITE_URL,
                                  'category': cfg['CFG_WEBBASKET_CATEGORIES']['GROUP'],
                                  'grpid': grpid,
                                  'bskid': basket_id,
                                  'ln': ln,
                                  'title_name': cgi.escape(basket_name, True),
                                  'basket_name': cgi.escape(prettify_name(basket_name, 27), True),
                                  'nb_items': nb_items}
                    content_list_item = """
                      %(basket_link)s""" % {'basket_link': basket_link}
                    content_list.append(content_list_item)
            ## If no specific grpid is selected create a list of groups with a preview of their baskets.
            else:
                for group_and_bskids in group_info:
                    group_id = group_and_bskids[0]
                    group_name = group_and_bskids[1]
                    bskids = group_and_bskids[2].split(',')
                    nb_baskets = len(bskids)
                    group_link = """<strong><a href="%(url)s/yourbaskets/display?category=%(category)s&amp;group=%(group)i&amp;ln=%(ln)s" title="%(title_name)s">%(group_name)s</a></strong> <span class="bsk_directory_box_content_list_number_of">(%(nb_baskets)s)</span>""" % \
                                 {'url': CFG_SITE_URL,
                                  'category': category,
                                  'group': group_id,
                                  'ln': ln,
                                  'title_name': cgi.escape(group_name, True),
                                  'group_name': cgi.escape(prettify_name(group_name, 25), True),
                                  'nb_baskets': nb_baskets}
                    basket_links = ""
                    basket_links_list = []
                    #TODO: Not have the number of basket names displayed hardcoded (3 in this case)
                    bskids_and_names = get_basket_ids_and_names(bskids, 3)
                    for bskid_and_name in bskids_and_names:
                        bskid = bskid_and_name[0]
                        basket_name = bskid_and_name[1]
                        # TODO: adapt the prettify_name char_limit variable according to nb_baskets
                        basket_link = """<a href="%(url)s/yourbaskets/display?category=%(category)s&amp;group=%(group)i&amp;bskid=%(bskid)i&amp;ln=%(ln)s" title="%(title_name)s">%(basket_name)s</a>""" % \
                                      {'url': CFG_SITE_URL,
                                       'category': category,
                                       'group': group_id,
                                       'bskid': bskid,
                                       'ln': ln,
                                       'title_name': cgi.escape(basket_name, True),
                                       'basket_name': cgi.escape(prettify_name(basket_name, __calculate_prettify_name_char_limit(nb_baskets, 135/CFG_WEBBASKET_DIRECTORY_BOX_NUMBER_OF_COLUMNS)), True)}
                        basket_links_list.append(basket_link)
                        basket_links = ', '.join(basket_links_list)
                    if nb_baskets > 3:
                        basket_links += ", ..."
                    content_list_item = """
                      %(group_link)s
                      <br />
                      <small>%(basket_links)s</small>""" % \
                                     {'group_link': group_link,
                                      'basket_links': basket_links}
                    content_list.append(content_list_item)

            nb_cells = cfg['CFG_WEBBASKET_DIRECTORY_BOX_NUMBER_OF_COLUMNS']
            nb_items = len(content_list)
            content_list.reverse()
            content = """
            <div class="row-fluid">
              <table cellspacing="0px" cellpadding="0px" align="center" width="100%">
                <tr>"""
            for i in range(nb_cells):
                content += """
                  <td class="bsk_directory_box_content_list_cell" width="%s%%">""" % \
                              (100/nb_cells,)
                nb_lines = (nb_items/nb_cells) + ((nb_items%nb_cells) > i and 1 or 0)
                for j in range(nb_lines):
                    content += content_list.pop()
                    if j < (nb_lines-1):
                        #content += "<br /><br />"
                        content += group_baskets_info and "<br />" or "<br /><br />"
                content += """
                  </td>"""
            content += """
                </tr>
              </table>
            </div>"""

        elif public_info and category==cfg['CFG_WEBBASKET_CATEGORIES']['EXTERNAL']:
            content_list = []
            for basket in public_info:
                basket_id = basket[0]
                basket_name = basket[1]
                nb_items = basket[2]
                basket_link = """<a href="%(url)s/yourbaskets/display?category=%(category)s&amp;bskid=%(bskid)i&amp;ln=%(ln)s" title="%(title_name)s">%(basket_name)s</a> <span class="bsk_directory_box_content_list_number_of">(%(nb_items)i)</span>""" % \
                             {'url': CFG_SITE_URL,
                              'category': category,
                              'bskid': basket_id,
                              'ln': ln,
                              'title_name': cgi.escape(basket_name, True),
                              'basket_name': cgi.escape(prettify_name(basket_name, 27), True),
                              'nb_items': nb_items}
                content_list_item = """
                      %(basket_link)s""" % {'basket_link': basket_link}
                content_list.append(content_list_item)

            nb_cells = cfg['CFG_WEBBASKET_DIRECTORY_BOX_NUMBER_OF_COLUMNS']
            nb_items = len(content_list)
            content_list.reverse()
            content = """
                <table cellspacing="0px" cellpadding="0px" align="center" width="100%">
                  <tr>"""
            for i in range(nb_cells):
                content += """
                    <td class="bsk_directory_box_content_list_cell" width="%s%%">""" % \
                              (100/nb_cells,)
                nb_lines = (nb_items/nb_cells) + ((nb_items%nb_cells) > i and 1 or 0)
                for j in range(nb_lines):
                    content += content_list.pop()
                    if j < (nb_lines-1):
                        content += "<br />"
                content += """
                    </td>"""
            content += """
                  </tr>
                </table>"""

        out = """
    <div class="bsk_directory_box">
      <div class="row-fluid">
        %(tabs)s
      </div>
      <div class="row-fluid bsk_directory_box_content">
        <div class="col-md-12 %(class)s">
          %(content)s
        </div>
      </div>
    </div>""" % {'class': ((category == cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE'] and topic) or \
                          (category == cfg['CFG_WEBBASKET_CATEGORIES']['GROUP'] and grpid)) and \
                          "bsk_directory_box_content_list_baskets" or \
                          "bsk_directory_box_content_list_topics_groups",
                 'tabs': tabs,
                 'content': content}
        return out

    def tmpl_create_search_box(self,
                               category="",
                               topic="",
                               grpid=0,
                               topic_list=(),
                               group_list=(),
                               number_of_public_baskets=0,
                               p="",
                               n=0,
                               ln=CFG_SITE_LANG):
        """EXPERIMENTAL UI"""

        _ = gettext_set_language(ln)

        action = """%s/yourbaskets/search""" % (CFG_SITE_URL,)

        select_options = create_search_box_select_options(category,
                                                          topic,
                                                          grpid,
                                                          topic_list,
                                                          group_list,
                                                          number_of_public_baskets,
                                                          ln)

        out = """
    <table cellspacing="0px" cellpadding="5px" class="bsk_search_box">
    <form name="search_baskets" action="%(action)s" method="get">
      <thead>
        <tr>
          <td colspan="4">
          <small><strong>%(search_for_label)s:</strong><small>
          </td>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>
          <input name="p" value="%(p)s" type="text" />
          </td>
          <td>
          <small><strong>%(in_label)s</strong><small>
          </td>
          <td>
          <select name="b">%(select_options)s
          </select>
          </td>
          <td>
          <input class="btn btn-primary formbutton" type="submit" value="%(search_label)s" />
          </td>
        </tr>
        <tr>
          <td>
          <input type="checkbox" name="n" value="1"%(notes_checked)s />
          <small>%(notes_label)s</small>
          </td>
        </tr>
      </tbody>
    <input type="hidden" name="ln" value="%(ln)s" />
    </form>
    </table>""" % {'action': action,
                   'search_for_label': _('Search baskets for'),
                   'notes_label': _('Search also in notes (where allowed)'),
                   'notes_checked': n and ' checked="checked"' or '',
                   'p': p,
                   'select_options': select_options,
                   'ln': ln,
                   'search_label': _('Search'),
                   'in_label': _('%(x_search_for_term)s in %(x_collection_list)s',
                                 x_search_for_term='', x_collection_list='')
                  }
        return out

    def tmpl_search_results(self,
                            personal_search_results={},
                            total_no_personal_search_results=0,
                            group_search_results={},
                            total_no_group_search_results=0,
                            public_search_results={},
                            total_no_public_search_results=0,
                            all_public_search_results={},
                            total_no_all_public_search_results=0,
                            ln=CFG_SITE_LANG):
        """Template for the search results."""

        _ = gettext_set_language(ln)

        out = """
    <table cellspacing="0px" cellpadding="5px">"""

        total_no_search_results = total_no_personal_search_results + \
                               total_no_group_search_results + \
                               total_no_public_search_results + \
                               total_no_all_public_search_results
        if total_no_search_results:
            if total_no_search_results != max(total_no_personal_search_results, \
                                              total_no_group_search_results, \
                                              total_no_public_search_results, \
                                              total_no_all_public_search_results):
                out += """
      <tr>
        <td class="webbasket_search_results_results_overview_cell">
        <strong>%(results_overview_label)s:</strong> %(items_found_label)s
        </td>
      </tr>""" % {'results_overview_label': _('Results overview'),
                  'items_found_label': _('%(x_num)i matching items', x_num=total_no_search_results)}
                if total_no_personal_search_results:
                    out += """
      <tr>
        <td>
        <a href="#%(personal_baskets_name)s">%(personal_baskets_label)s</a>
        <span class="webbasket_search_results_number_of_items">(%(items_found)i)</span>
        </td>
      </tr>""" % {'personal_baskets_label': _('Personal baskets'),
                  'personal_baskets_name': "P",
                  'items_found': total_no_personal_search_results}
                if total_no_group_search_results:
                    out += """
      <tr>
        <td>
        <a href="#%(group_baskets_name)s">%(group_baskets_label)s<a/>
        <span class="webbasket_search_results_number_of_items">(%(items_found)s)</span>
        </td>
      </tr>""" % {'group_baskets_label': _('Group baskets'),
                  'group_baskets_name': "G",
                  'items_found': total_no_group_search_results}
                if total_no_public_search_results:
                    out += """
      <tr>
        <td>
        <a href="#%(public_baskets_name)s">%(public_baskets_label)s</a>
        <span class="webbasket_search_results_number_of_items">(%(items_found)s)</span>
        </td>
      </tr>""" % {'public_baskets_label': _('Public baskets'),
                  'public_baskets_name': "E",
                  'items_found': total_no_public_search_results}
                if total_no_all_public_search_results:
                    out += """
      <tr>
        <td>
        <a href="#%(all_public_baskets_name)s">%(all_public_baskets_label)s</a>
        <span class="webbasket_search_results_number_of_items">(%(items_found)s)</span>
        </td>
      </tr>""" % {'all_public_baskets_label': _('All public baskets'),
                  'all_public_baskets_name': "A",
                  'items_found': total_no_all_public_search_results}
                out += """
      <tr>
        <td>
        &nbsp;
        </td>
      </tr>"""

        else:
            out += """
      <tr>
        <td>
        %(no_items_found_label)s
        </td>
      </tr>""" % {'no_items_found_label': _('No items found.')}


        ### Search results from the user's personal baskets ###
        if total_no_personal_search_results:
            # Print out the header for the personal baskets
            out += """
      <tr>
        <td class="webbasket_search_results_results_overview_cell">
        <a name="%(personal_baskets_name)s"></a><strong>%(personal_baskets_label)s:</strong> %(items_found_label)s
        </td>
      </tr>""" % {'personal_baskets_label': _('Personal baskets'),
                  'personal_baskets_name': "P",
                  'items_found_label': _('%(x_num)i matching items', x_num=total_no_personal_search_results)}

            # For every basket print a link to the basket and the number of items
            # found in that basket
            for bskid in personal_search_results.keys():
                basket_link = """<a href="%(url)s/yourbaskets/display?category=%(category)s&amp;topic=%(topic)s&amp;bskid=%(bskid)i&amp;ln=%(ln)s">%(basket_name)s</a>""" % \
                              {'url': CFG_SITE_URL,
                               'category': cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE'],
                               'topic': urllib.quote(personal_search_results[bskid][1]),
                               'bskid': bskid,
                               'ln': ln,
                               'basket_name': cgi.escape(personal_search_results[bskid][0], True)}
                out += """
      <tr>
        <td>
        %(in_basket_label)s <span class="webbasket_search_results_number_of_items">(%(items_found)i)</span>
        </td>
      </tr>""" % {'in_basket_label': _('In %(x_linked_basket_name)s') % \
                                     {'x_linked_basket_name': basket_link},
                                      'items_found': personal_search_results[bskid][2]}

                # Print the list of records found in that basket
                out += """
      <tr>
        <td class="webbasket_search_results_basket">
          <ol>"""
                personal_search_result_records = personal_search_results[bskid][3]
                for personal_search_result_record in personal_search_result_records:
                    recid = personal_search_result_record[0]
                    number_of_notes = personal_search_result_record[1]
                    record_html = personal_search_result_record[2]
                    # If this a local record print the detailed record link and
                    # the view/add notes link
                    if recid > 0:
                        detailed_record_html = """<a class="moreinfo" href="%(siteurl)s/%(CFG_SITE_RECORD)s/%(recid)i">%(detailed_record_label)s</a>""" % \
                                               {'siteurl': CFG_SITE_URL,
                                                'CFG_SITE_RECORD': cfg['CFG_SITE_RECORD'],
                                                'recid': recid,
                                                'detailed_record_label': _('Detailed record')}
                        notes_html = """<a class="moreinfo" href="%(siteurl)s/yourbaskets/%(notes_action)s?"""\
                                     """category=P&amp;topic=%(topic)s&amp;bskid=%(bskid)s&amp;recid=%(recid)i"""\
                                     """&amp;ln=%(ln)s%(notes_inline_anchor)s">%(notes_label)s</a>""" % \
                                     {'siteurl': CFG_SITE_URL,
                                      'topic': urllib.quote(personal_search_results[bskid][1]),
                                      'bskid' : bskid,
                                      'recid' : recid,
                                      'ln' : ln,
                                      'notes_action': number_of_notes and 'display' or 'write_note',
                                      'notes_inline_anchor': not number_of_notes and '#note' or '',
                                      'notes_label': number_of_notes and _('Notes') + ' (' + str(number_of_notes) + ')' or _('Add a note...')}

                        out += """
                        <li>
                        %(record_html)s
                        <br />
                        %(more_info)s
                        </li>""" % \
                        {'record_html': record_html,
                         'more_info': """<span class="moreinfo">%(detailed_record_html)s - %(notes_html)s</span>""" % \
                                                       {'detailed_record_html': detailed_record_html,
                                                        'notes_html': notes_html}}
                    # If this an external record print only the view/add notes link
                    else:
                        notes_html = """<a class="moreinfo" href="%(siteurl)s/yourbaskets/%(notes_action)s?"""\
                                     """category=P&amp;topic=%(topic)s&amp;bskid=%(bskid)s&amp;recid=%(recid)i"""\
                                     """&amp;ln=%(ln)s%(notes_inline_anchor)s">%(notes_label)s</a>""" % \
                                     {'siteurl': CFG_SITE_URL,
                                      'topic': urllib.quote(personal_search_results[bskid][1]),
                                      'bskid' : bskid,
                                      'recid' : recid,
                                      'ln' : ln,
                                      'notes_action': number_of_notes and 'display' or 'write_note',
                                      'notes_inline_anchor': not number_of_notes and '#note' or '',
                                      'notes_label': number_of_notes and _('Notes') + ' (' + str(number_of_notes) + ')' or _('Add a note...')}

                        out += """
                        <li>
                        %(record_html)s
                        <br />
                        %(more_info)s
                        </li>""" % \
                        {'record_html': record_html,
                         'more_info':  notes_html}

                out += """
          </ol>
        </td>
      </tr>"""

            out += """
      <tr>
        <td>
        &nbsp;
        </td>
      </tr>"""

        ### Search results from the user's group baskets ###
        if total_no_group_search_results:
            # Print out the header for the group baskets
            out += """
      <tr>
        <td class="webbasket_search_results_results_overview_cell">
        <a name="%(group_baskets_name)s"></a><strong>%(group_baskets_label)s:</strong> %(items_found_label)s
        </td>
      </tr>""" % {'group_baskets_label': _('Group baskets'),
                  'group_baskets_name': "G",
                  'items_found_label': _('%(x_num)i matching items', x_num=total_no_group_search_results)}

            # For every basket print a link to the basket and the number of items
            # found in that basket
            for bskid in group_search_results.keys():
                basket_link = """<a href="%(url)s/yourbaskets/display?category=%(category)s&amp;group=%(grpid)i&amp;bskid=%(bskid)i&amp;ln=%(ln)s">%(basket_name)s</a>""" % \
                              {'url': CFG_SITE_URL,
                               'category': cfg['CFG_WEBBASKET_CATEGORIES']['GROUP'],
                               'grpid': group_search_results[bskid][1],
                               'bskid': bskid,
                               'ln': ln,
                               'basket_name': cgi.escape(group_search_results[bskid][0], True)}
                out += """
      <tr>
        <td>
        %(in_basket_label)s <span class="webbasket_search_results_number_of_items">(%(items_found)i)</span>
        </td>
      </tr>""" % {'in_basket_label': _('In %(x_linked_basket_name)s') % \
                                     {'x_linked_basket_name': basket_link},
                                      'items_found': group_search_results[bskid][4]}

                # Print the list of records found in that basket
                out += """
      <tr>
        <td class="webbasket_search_results_basket">
          <ol>"""
                group_search_result_records = group_search_results[bskid][5]
                (share_rights_view_notes, share_rights_add_notes) = group_search_results[bskid][3]
                for group_search_result_record in group_search_result_records:
                    recid = group_search_result_record[0]
                    number_of_notes = group_search_result_record[1]
                    record_html = group_search_result_record[2]
                    share_rights_notes = bool(share_rights_view_notes and (number_of_notes or share_rights_add_notes))
                    # If this a local record print the detailed record link and
                    # the view/add notes link
                    if recid > 0:
                        detailed_record_html = """<a class="moreinfo" href="%(siteurl)s/%(CFG_SITE_RECORD)s/%(recid)i">%(detailed_record_label)s</a>""" % \
                                               {'siteurl': CFG_SITE_URL,
                                                'CFG_SITE_RECORD': cfg['CFG_SITE_RECORD'],
                                                'recid': recid,
                                                'detailed_record_label': _('Detailed record')}
                        if share_rights_notes:
                            notes_html = """<a class="moreinfo" href="%(siteurl)s/yourbaskets/%(notes_action)s?"""\
                                         """category=G&amp;group=%(grpid)i&amp;bskid=%(bskid)s&amp;recid=%(recid)i"""\
                                         """&amp;ln=%(ln)s%(notes_inline_anchor)s">%(notes_label)s</a>""" % \
                                         {'siteurl': CFG_SITE_URL,
                                          'grpid': group_search_results[bskid][1],
                                          'bskid' : bskid,
                                          'recid' : recid,
                                          'ln' : ln,
                                          'notes_action': number_of_notes and 'display' or 'write_note',
                                          'notes_inline_anchor': not number_of_notes and '#note' or '',
                                          'notes_label': number_of_notes and _('Notes') + ' (' + str(number_of_notes) + ')' or _('Add a note...')}

                        out += """
                        <li>
                        %(record_html)s
                        <br />
                        %(more_info)s
                        </li>""" % \
                        {'record_html': record_html,
                         'more_info': """<span class="moreinfo">%(detailed_record_html)s%(separator)s%(notes_html)s</span>""" % \
                                                       {'detailed_record_html': detailed_record_html,
                                                        'separator': share_rights_notes and ' - ' or '',
                                                        'notes_html': share_rights_notes and notes_html or ''}}
                    # If this an external record print only the view/add notes link
                    else:
                        if share_rights_notes:
                            notes_html = """<a class="moreinfo" href="%(siteurl)s/yourbaskets/%(notes_action)s?"""\
                                         """category=G&amp;group=%(grpid)i&amp;bskid=%(bskid)s&amp;recid=%(recid)i"""\
                                         """&amp;ln=%(ln)s%(notes_inline_anchor)s">%(notes_label)s</a>""" % \
                                         {'siteurl': CFG_SITE_URL,
                                          'grpid': group_search_results[bskid][1],
                                          'bskid' : bskid,
                                          'recid' : recid,
                                          'ln' : ln,
                                          'notes_action': number_of_notes and 'display' or 'write_note',
                                          'notes_inline_anchor': not number_of_notes and '#note' or '',
                                          'notes_label': number_of_notes and _('Notes') + ' (' + str(number_of_notes) + ')' or _('Add a note...')}

                        out += """
                        <li>
                        %(record_html)s
                        %(more_info)s
                        </li>""" % \
                        {'record_html': record_html,
                         'more_info': share_rights_notes and '<br />' + notes_html or ''}

                out += """
          </ol>
        </td>
      </tr>"""

            out += """
      <tr>
        <td>
        &nbsp;
        </td>
      </tr>"""

        ### Search results from the user's public baskets ###
        if total_no_public_search_results:
            out += """
      <tr>
        <td class="webbasket_search_results_results_overview_cell">
        <a name="%(public_baskets_name)s"></a><strong>%(public_baskets_label)s:</strong> %(items_found_label)s
        </td>
      </tr>""" % {'public_baskets_label': _('Public baskets'),
                  'public_baskets_name': "E",
                  'items_found_label': _('%(x_num)i matching items', x_num=total_no_public_search_results)}

            for bskid in public_search_results.keys():
                basket_link = """<a href="%(url)s/yourbaskets/display?category=%(category)s&amp;bskid=%(bskid)i&amp;ln=%(ln)s">%(basket_name)s</a>""" % \
                              {'url': CFG_SITE_URL,
                               'category': cfg['CFG_WEBBASKET_CATEGORIES']['EXTERNAL'],
                               'bskid': bskid,
                               'ln': ln,
                               'basket_name': cgi.escape(public_search_results[bskid][0], True)}
                out += """
      <tr>
        <td>
        %(in_basket_label)s <span class="webbasket_search_results_number_of_items">(%(items_found)i)</span>
        </td>
      </tr>""" % {'in_basket_label': _('In %(x_linked_basket_name)s') % \
                                     {'x_linked_basket_name': basket_link},
                  'items_found': public_search_results[bskid][2]}

                # Print the list of records found in that basket
                out += """
      <tr>
        <td class="webbasket_search_results_basket">
          <ol>"""
                public_search_result_records = public_search_results[bskid][3]
                (share_rights_view_notes, share_rights_add_notes) = public_search_results[bskid][1]
                for public_search_result_record in public_search_result_records:
                    recid = public_search_result_record[0]
                    number_of_notes = public_search_result_record[1]
                    record_html = public_search_result_record[2]
                    share_rights_notes = bool(share_rights_view_notes and (number_of_notes or share_rights_add_notes))
                    # If this a local record print the detailed record link and
                    # the view/add notes link
                    if recid > 0:
                        detailed_record_html = """<a class="moreinfo" href="%(siteurl)s/%(CFG_SITE_RECORD)s/%(recid)i">%(detailed_record_label)s</a>""" % \
                                               {'siteurl': CFG_SITE_URL,
                                                'CFG_SITE_RECORD': cfg['CFG_SITE_RECORD'],
                                                'recid': recid,
                                                'detailed_record_label': _('Detailed record')}
                        if share_rights_notes:
                            notes_html = """<a class="moreinfo" href="%(siteurl)s/yourbaskets/%(notes_action)s?"""\
                                         """bskid=%(bskid)s&amp;recid=%(recid)i"""\
                                         """&amp;ln=%(ln)s%(notes_inline_anchor)s">%(notes_label)s</a>""" % \
                                         {'siteurl': CFG_SITE_URL,
                                          'bskid' : bskid,
                                          'recid' : recid,
                                          'ln' : ln,
                                          'notes_action': number_of_notes and 'display_public' or 'write_public_note',
                                          'notes_inline_anchor': not number_of_notes and '#note' or '',
                                          'notes_label': number_of_notes and _('Notes') + ' (' + str(number_of_notes) + ')' or _('Add a note...')}

                        out += """
                        <li>
                        %(record_html)s
                        <br />
                        %(more_info)s
                        </li>""" % \
                        {'record_html': record_html,
                         'more_info': """<span class="moreinfo">%(detailed_record_html)s%(separator)s%(notes_html)s</span>""" % \
                                                       {'detailed_record_html': detailed_record_html,
                                                        'separator': share_rights_notes and ' - ' or '',
                                                        'notes_html': share_rights_notes and notes_html or ''}}
                    # If this an external record print only the view/add notes link
                    else:
                        if share_rights_notes:
                            notes_html = """<a class="moreinfo" href="%(siteurl)s/yourbaskets/%(notes_action)s?"""\
                                         """bskid=%(bskid)s&amp;recid=%(recid)i"""\
                                         """&amp;ln=%(ln)s%(notes_inline_anchor)s">%(notes_label)s</a>""" % \
                                         {'siteurl': CFG_SITE_URL,
                                          'bskid' : bskid,
                                          'recid' : recid,
                                          'ln' : ln,
                                          'notes_action': number_of_notes and 'display_public' or 'write_public_note',
                                          'notes_inline_anchor': not number_of_notes and '#note' or '',
                                          'notes_label': number_of_notes and _('Notes') + ' (' + str(number_of_notes) + ')' or _('Add a note...')}

                        out += """
                        <li>
                        %(record_html)s
                        %(more_info)s
                        </li>""" % \
                        {'record_html': record_html,
                         'more_info': share_rights_notes and '<br />' + notes_html or ''}

                out += """
          </ol>
        </td>
      </tr>"""

            out += """
      <tr>
        <td>
        &nbsp;
        </td>
      </tr>"""

        ### Search results from all the public baskets ###
        if total_no_all_public_search_results:
            out += """
      <tr>
        <td class="webbasket_search_results_results_overview_cell">
        <a name="%(all_public_baskets_name)s"></a><strong>%(all_public_baskets_label)s:</strong> %(items_found_label)s
        </td>
      </tr>""" % {'all_public_baskets_label': _('All public baskets'),
                  'all_public_baskets_name': "A",
                  'items_found_label': _('%(x_num)i matching items', x_num=total_no_all_public_search_results)}

            for bskid in all_public_search_results.keys():
                basket_link = """<a href="%(url)s/yourbaskets/display_public?bskid=%(bskid)i&amp;ln=%(ln)s">%(basket_name)s</a>""" % \
                              {'url': CFG_SITE_URL,
                               'bskid': bskid,
                               'ln': ln,
                               'basket_name': cgi.escape(all_public_search_results[bskid][0], True)}
                out += """
      <tr>
        <td>
        %(in_basket_label)s <span class="webbasket_search_results_number_of_items">(%(items_found)i)</span>
        </td>
      </tr>""" % {'in_basket_label': _('In %(x_linked_basket_name)s') % \
                                     {'x_linked_basket_name': basket_link},
                  'items_found': all_public_search_results[bskid][2]}

                # Print the list of records found in that basket
                out += """
      <tr>
        <td class="webbasket_search_results_basket">
          <ol>"""
                all_public_search_result_records = all_public_search_results[bskid][3]
                (share_rights_view_notes, share_rights_add_notes) = all_public_search_results[bskid][1]
                for all_public_search_result_record in all_public_search_result_records:
                    recid = all_public_search_result_record[0]
                    number_of_notes = all_public_search_result_record[1]
                    record_html = all_public_search_result_record[2]
                    share_rights_notes = bool(share_rights_view_notes and (number_of_notes or share_rights_add_notes))
                    # If this a local record print the detailed record link and
                    # the view/add notes link
                    if recid > 0:
                        detailed_record_html = """<a class="moreinfo" href="%(siteurl)s/%(CFG_SITE_RECORD)s/%(recid)i">%(detailed_record_label)s</a>""" % \
                                               {'siteurl': CFG_SITE_URL,
                                                'CFG_SITE_RECORD': cfg['CFG_SITE_RECORD'],
                                                'recid': recid,
                                                'detailed_record_label': _('Detailed record')}
                        if share_rights_notes:
                            notes_html = """<a class="moreinfo" href="%(siteurl)s/yourbaskets/%(notes_action)s?"""\
                                         """bskid=%(bskid)s&amp;recid=%(recid)i"""\
                                         """&amp;ln=%(ln)s%(notes_inline_anchor)s">%(notes_label)s</a>""" % \
                                         {'siteurl': CFG_SITE_URL,
                                          'bskid' : bskid,
                                          'recid' : recid,
                                          'ln' : ln,
                                          'notes_action': number_of_notes and 'display_public' or 'write_public_note',
                                          'notes_inline_anchor': not number_of_notes and '#note' or '',
                                          'notes_label': number_of_notes and _('Notes') + ' (' + str(number_of_notes) + ')' or _('Add a note...')}

                        out += """
                        <li>
                        %(record_html)s
                        <br />
                        %(more_info)s
                        </li>""" % \
                        {'record_html': record_html,
                         'more_info': """<span class="moreinfo">%(detailed_record_html)s%(separator)s%(notes_html)s</span>""" % \
                                                       {'detailed_record_html': detailed_record_html,
                                                        'separator': share_rights_notes and ' - ' or '',
                                                        'notes_html': share_rights_notes and notes_html or ''}}
                    # If this an external record print only the view/add notes link
                    else:
                        if share_rights_notes:
                            notes_html = """<a class="moreinfo" href="%(siteurl)s/yourbaskets/%(notes_action)s?"""\
                                         """bskid=%(bskid)s&amp;recid=%(recid)i"""\
                                         """&amp;ln=%(ln)s%(notes_inline_anchor)s">%(notes_label)s</a>""" % \
                                         {'siteurl': CFG_SITE_URL,
                                          'bskid' : bskid,
                                          'recid' : recid,
                                          'ln' : ln,
                                          'notes_action': number_of_notes and 'display_public' or 'write_public_note',
                                          'notes_inline_anchor': not number_of_notes and '#note' or '',
                                          'notes_label': number_of_notes and _('Notes') + ' (' + str(number_of_notes) + ')' or _('Add a note...')}

                        out += """
                        <li>
                        %(record_html)s
                        %(more_info)s
                        </li>""" % \
                        {'record_html': record_html,
                         'more_info': share_rights_notes and '<br />' + notes_html or ''}

                out += """
          </ol>
        </td>
      </tr>"""

            out += """
      <tr>
        <td>
        &nbsp;
        </td>
      </tr>"""

        out += """
    </table>"""

        return out

    def tmpl_display(self,
                     directory='',
                     content='',
                     search_box='',
                     search_results=''):
        """Template for the generic display.
        @param directory: the directory-like menu (optional)
        @param content: content (of a basket) (optional)
        @param search_box: the search form (optional)
        @param search_results: the search results (optional)"""

        display_items = []

        if directory:
            container_directory = """
  <div id="bskcontainerdirectory">%s
  </div>
""" % (directory,)
            display_items.append(container_directory)

        if content:
            container_content = """
  <div id="bskcontainercontent">%s
  </div>
""" % (content,)
            display_items.append(container_content)

        if search_box:
            container_search_box = """
  <div id="webbasket_container_search_box">%s
  </div>
""" % (search_box,)
            display_items.append(container_search_box)

        if search_results:
            container_search_results = """
  <div id="webbasket_container_search_results">%s
  </div>
""" % (search_results,)
            display_items.append(container_search_results)

        display_separator= """
  <div height="10px">
  &nbsp;
  </div>
"""

        display = display_separator.join(display_items)

        out = """
<div id="bskcontainer">
%s
</div>""" % (display,)

        return out

    def tmpl_display_list_public_baskets(self,
                                         all_public_baskets,
                                         limit,
                                         number_of_all_public_baskets,
                                         sort,
                                         asc,
                                         nb_views_show_p=False,
                                         ln=CFG_SITE_LANG):
        """Template for the list of public baskets.
        @param all_public_baskets: tuple
                                   (bskid, basket_name, owner_id, nickname, date_modification, nb_views, nb_items)
        @param limit: display baskets from the incrementally numbered 'limit' and on
        @param number_of_all_public_baskets: the number of all the public baskets
        @param sort: 'name': sort by basket name
                     'views': sort by number of basket views
                     'nickname': sort by user nickname
                     'date': sort by basket modification date
                     'items': sort by number of basket items
        @param asc: ascending sort or not
        @param nb_views_show_p: show the views column or not
        @param ln: language"""

        _ = gettext_set_language(ln)

        basket_name_label = _("Public basket")
        owner_label = _("Owner")
        date_modification_label = _("Last update")
        nb_items_label = _("Items")
        nb_views_label = _("Views")

        if sort == "name":
            if asc:
                basket_name_sort_img = """<img src="%s/img/wb-sort-asc.gif" />""" % (CFG_SITE_URL,)
            else:
                basket_name_sort_img = """<img src="%s/img/wb-sort-desc.gif" />""" % (CFG_SITE_URL,)
        else:
            basket_name_sort_img = """<img src="%s/img/wb-sort-none.gif" />""" % (CFG_SITE_URL,)
        if sort == "owner":
            if asc:
                owner_sort_img = """<img src="%s/img/wb-sort-asc.gif" />""" % (CFG_SITE_URL,)
            else:
                owner_sort_img = """<img src="%s/img/wb-sort-desc.gif" />""" % (CFG_SITE_URL,)
        else:
            owner_sort_img = """<img src="%s/img/wb-sort-none.gif" />""" % (CFG_SITE_URL,)
        if sort == "date":
            if asc:
                date_modification_sort_img = """<img src="%s/img/wb-sort-asc.gif" />""" % (CFG_SITE_URL,)
            else:
                date_modification_sort_img = """<img src="%s/img/wb-sort-desc.gif" />""" % (CFG_SITE_URL,)
        else:
            date_modification_sort_img = """<img src="%s/img/wb-sort-none.gif" />""" % (CFG_SITE_URL,)
        if sort == "items":
            if asc:
                nb_items_sort_img = """<img src="%s/img/wb-sort-asc.gif" />""" % (CFG_SITE_URL,)
            else:
                nb_items_sort_img = """<img src="%s/img/wb-sort-desc.gif" />""" % (CFG_SITE_URL,)
        else:
            nb_items_sort_img = """<img src="%s/img/wb-sort-none.gif" />""" % (CFG_SITE_URL,)
        if sort == "views":
            if asc:
                nb_views_sort_img = """<img src="%s/img/wb-sort-asc.gif" />""" % (CFG_SITE_URL,)
            else:
                nb_views_sort_img = """<img src="%s/img/wb-sort-desc.gif" />""" % (CFG_SITE_URL,)
        else:
            nb_views_sort_img = """<img src="%s/img/wb-sort-none.gif" />""" % (CFG_SITE_URL,)

        basket_name_sort = """<a href="%s/yourbaskets/list_public_baskets?limit=%i&amp;sort=name&amp;asc=%i&amp;ln=%s">%s</a>""" % \
                           (CFG_SITE_URL, limit, not(asc), ln, basket_name_sort_img)
        owner_sort = """<a href="%s/yourbaskets/list_public_baskets?limit=%i&amp;sort=owner&amp;asc=%i&amp;ln=%s">%s</a>""" % \
                     (CFG_SITE_URL, limit, not(asc), ln, owner_sort_img)
        date_modification_sort = """<a href="%s/yourbaskets/list_public_baskets?limit=%i&amp;sort=date&amp;asc=%i&amp;ln=%s">%s</a>""" % \
                                 (CFG_SITE_URL, limit, not(asc), ln, date_modification_sort_img)
        nb_items_sort = """<a href="%s/yourbaskets/list_public_baskets?limit=%i&amp;sort=items&amp;asc=%i&amp;ln=%s">%s</a>""" % \
                        (CFG_SITE_URL, limit, not(asc), ln, nb_items_sort_img)
        nb_views_sort = """<a href="%s/yourbaskets/list_public_baskets?limit=%i&amp;sort=views&amp;asc=%i&amp;ln=%s">%s</a>""" % \
                        (CFG_SITE_URL, limit, not(asc), ln, nb_views_sort_img)

        baskets_html = ''
        for (bskid, basket_name, owner_id, nickname, date_modification, nb_items, nb_views) in all_public_baskets:
            if nickname:
                display = nickname
            else:
                (owner_id, nickname, display) = get_user_info(owner_id)
            webmessage_link = self.__create_webmessage_link(nickname, display, ln)

            basket_link = """<a href="%s/yourbaskets/display_public?category=%s&amp;bskid=%s&amp;ln=%s">%s<a/>""" % \
                          (CFG_SITE_URL, cfg['CFG_WEBBASKET_CATEGORIES']['EXTERNAL'], bskid, ln, cgi.escape(basket_name, True))

            nb_views_td = """<td class="bsk_list_public_baskets_basket_right">%i</td>""" % (nb_views,)

            baskets_html += """
    <tr>
      <td class="bsk_list_public_baskets_basket_left">%(basket_link)s</td>
      <td class="bsk_list_public_baskets_basket_left">%(webmessage_link)s</td>
      <td class="bsk_list_public_baskets_basket_left">%(date_modification)s</td>
      <td class="bsk_list_public_baskets_basket_right">%(nb_items)i</td>
      %(nb_views)s
    </tr>""" % {'basket_link': basket_link,
                'webmessage_link': webmessage_link,
                'date_modification': date_modification,
                'nb_items': nb_items,
                'nb_views': nb_views_show_p and nb_views_td or ''}

        if not all_public_baskets:
            baskets_html = """
    <tr>
      <td colspan="%i">
      %s
      </td>
    </tr>""" % (nb_views_show_p and 5 or 4,
                _("There is currently no publicly accessible basket"))

        footer = ''

        if limit > cfg['CFG_WEBBASKET_MAX_NUMBER_OF_DISPLAYED_BASKETS']:
            limit_first = 1
            page_first = """<a href="%s/yourbaskets/list_public_baskets?limit=%i&amp;sort=%s&amp;asc=%i&amp;ln=%s"><img src="%s" /></a>""" % \
                         (CFG_SITE_URL, limit_first, sort, asc, ln, '/img/sb.gif')
            footer += page_first

        if limit > 0:
            limit_previous = limit > cfg['CFG_WEBBASKET_MAX_NUMBER_OF_DISPLAYED_BASKETS'] \
                             and limit - cfg['CFG_WEBBASKET_MAX_NUMBER_OF_DISPLAYED_BASKETS'] + 1 \
                             or 1
            page_previous = """<a href="%s/yourbaskets/list_public_baskets?limit=%i&amp;sort=%s&amp;asc=%i&amp;ln=%s"><img src="%s" /></a>""" % \
                            (CFG_SITE_URL, limit_previous, sort, asc, ln, '/img/sp.gif')
            footer += page_previous

        display_from = limit + 1
        display_to = limit + cfg['CFG_WEBBASKET_MAX_NUMBER_OF_DISPLAYED_BASKETS'] > number_of_all_public_baskets \
                     and number_of_all_public_baskets \
                     or limit + cfg['CFG_WEBBASKET_MAX_NUMBER_OF_DISPLAYED_BASKETS']
        footer += _('Displaying public baskets %(x_from)i - %(x_to)i out of %(x_total_public_basket)i public baskets in total.') % \
               {'x_from': display_from, 'x_to': display_to, 'x_total_public_basket': number_of_all_public_baskets}

        if limit < number_of_all_public_baskets - cfg['CFG_WEBBASKET_MAX_NUMBER_OF_DISPLAYED_BASKETS']:
            limit_next = limit + cfg['CFG_WEBBASKET_MAX_NUMBER_OF_DISPLAYED_BASKETS'] + 1
            page_next = """<a href="%s/yourbaskets/list_public_baskets?limit=%i&amp;sort=%s&amp;asc=%i&amp;ln=%s"><img src="%s" /></a>""" % \
                        (CFG_SITE_URL, limit_next, sort, asc, ln, '/img/sn.gif')
            footer += page_next

        if limit < number_of_all_public_baskets - ( 2 * cfg['CFG_WEBBASKET_MAX_NUMBER_OF_DISPLAYED_BASKETS'] ):
            limit_last = number_of_all_public_baskets - cfg['CFG_WEBBASKET_MAX_NUMBER_OF_DISPLAYED_BASKETS'] + 1
            page_last = """<a href="%s/yourbaskets/list_public_baskets?limit=%i&amp;sort=%s&amp;asc=%i&amp;ln=%s"><img src="%s" /></a>""" % \
                        (CFG_SITE_URL, limit_last, sort, asc, ln, '/img/se.gif')
            footer += page_last

        if nb_views_show_p:
            nb_views_label_td = """<td>%(nb_views_label)s&nbsp;%(nb_views_sort)s</td>""" % \
                                {'nb_views_label': nb_views_label,
                                 'nb_views_sort': nb_views_sort}

        out = """
<table class="bsk_list_public_baskets" cellpadding="5px">
  <thead class="bsk_list_public_baskets_header">
    <tr>
      <td>%(basket_name_label)s&nbsp;%(basket_name_sort)s</td>
      <td>%(owner_label)s&nbsp;%(owner_sort)s</td>
      <td>%(date_modification_label)s&nbsp;%(date_modification_sort)s</td>
      <td>%(nb_items_label)s&nbsp;%(nb_items_sort)s</td>
      %(nb_views_label_td)s
    </tr>
  </thead>
  <tfoot class="bsk_list_public_baskets_footer">
    <tr>
      <td colspan="%(colspan)s" style="text-align:center">%(footer)s</td>
    </tr>
  </tfoot>
  <tbody>
    %(baskets)s
  </tbody>
</table>""" % {'basket_name_label': basket_name_label,
               'basket_name_sort': basket_name_sort,
               'owner_label': owner_label,
               'owner_sort': owner_sort,
               'date_modification_label': date_modification_label,
               'date_modification_sort': date_modification_sort,
               'nb_items_label': nb_items_label,
               'nb_items_sort': nb_items_sort,
               'nb_views_label_td': nb_views_show_p and nb_views_label_td or '',
               'colspan': nb_views_show_p and 5 or 4,
               'footer': footer,
               'baskets': baskets_html}

        return out

    def tmpl_quote_comment_textual(self, title, uid, nickname, date, body, ln=CFG_SITE_LANG):
        """Return a comment in a quoted form (i.e. with '>' signs before each line)
        @param title: title of comment to quote
        @param uid: user id of user who posted comment to quote
        @param nickname: nickname of user who posted comment to quote
        @param date: date of post of comment to quote
        @param body: body of comment to quote
        @param ln: language"""
        _ = gettext_set_language(ln)
        if not(nickname):
            nickname = get_user_info(uid)[2]

        if title:
            msg = _("%(x_title)s, by %(x_name)s on %(x_date)s:") % \
                  {'x_title': title, 'x_name': nickname, 'x_date': date}
        else:
            msg = _("%(x_name)s wrote on %(x_date)s:") % {'x_name': nickname, 'x_date': date}

        msg += '\n\n'
        msg += body
        return email_quote_txt(msg)

    def tmpl_quote_comment_html(self, title, uid, nickname, date, body, ln=CFG_SITE_LANG):
        """Return a comment in a quoted form (i.e. indented using HTML
        table) for HTML output (i.e. in CKEditor).

        @param title: title of comment to quote
        @param uid: user id of user who posted comment to quote
        @param nickname: nickname of user who posted comment to quote
        @param date: date of post of comment to quote
        @param body: body of comment to quote
        @param ln: language"""
        _ = gettext_set_language(ln)
        if not(nickname):
            nickname = get_user_info(uid)[2]

        if title:
            msg = _("%(x_title)s, by %(x_name)s on %(x_date)s:") % \
                  {'x_title': title, 'x_name': nickname, 'x_date': date}
        else:
            msg = _("%(x_name)s wrote on %(x_date)s:") % {'x_name': nickname, 'x_date': date}

        msg += '<br/><br/>'
        msg += body
        msg = email_quote_txt(text=msg)
        msg = email_quoted_txt2html(text=msg)

        return '<br/>' + msg + '<br/>'

    def __tmpl_basket_box(self, img='', title='&nbsp;', subtitle='&nbsp;', body=''):
        """ private function, display a basket/topic selection box """
        out = """
<div class="bskbasket">
    <div class="row-fluid bskbasketheader">
        <div class="col-md-1 bskactions">
            <img src="%(logo)s" alt="%(label)s" />
        </div>
        <div class="col-md-11 bsktitle">
            <b>%(label)s</b><br />
            %(count)s
        </div>
    </div>
    <div class="row-fluid">
        %(basket_list)s
    </div>
</div>"""
        out %= {'logo': img,
              'label': title, 'count': subtitle,
              'basket_list': body}
        return out

    def tmpl_create_box(self, new_basket_name='', new_topic_name='',
                        topics=[], selected_topic="",
                        ln=CFG_SITE_LANG):
        """Display a HTML box for creation of a new basket
        @param new_basket_name: prefilled value (string)
        @param new_topic_name: prefilled value (string)
        @param topics: list of topics (list of strings)
        @param selected_topic: preselected value for topic selection
        @param ln: language"""
        _ = gettext_set_language(ln)
        topics_html = ''
        #if selected_topic:
        #    try:
        #        selected_topic = topics.index(selected_topic)
        #    except:
        #        selected_topic = None
        if topics:
            topics = zip(topics, topics)
            topics.insert(0, (-1, _("Select topic")))
            topics_html = self.__create_select_menu('create_in_topic', topics, selected_topic)
        create_html = """
<tr>
  <td style="padding: 10 5 0 5;"><label>%s</label></td>
  <td style="padding: 10 5 0 0;">%s</td>
</tr>
<tr>
  <td style="padding: 10 5 0 5;"><label>%s</label></td>
  <td style="padding: 10 5 0 0;"><input type="text" name="new_topic_name" value="%s"/></td>
</tr>
<tr>
  <td style="padding: 10 5 0 5;"><label>%s</label></td>
  <td style="padding: 10 5 0 0;">
    <input type="text" name="new_basket_name" value="%s"/>
  </td>
</tr>""" % (topics_html != '' and _("Choose topic") or '',
            topics_html,
            topics_html != '' and _("or create a new one") or _("Create new topic"),
            cgi.escape(new_topic_name, True),
            _("Basket name"),
            cgi.escape(new_basket_name, True))
        return self.__tmpl_basket_box(img=CFG_SITE_URL + '/img/webbasket_create.png',
                                      title=_("Create a new basket"),
                                      body=create_html)

    def tmpl_create_basket(self,
                           new_basket_name='',
                           new_topic_name='',
                           create_in_topic=None,
                           topics=[],
                           recids=[],
                           colid=-1,
                           es_title='',
                           es_desc='',
                           es_url='',
                           copy=False,
                           move_from_basket=0,
                           referer='',
                           ln=CFG_SITE_LANG):
        """Template for basket creation
        @param new_basket_name: prefilled value (string)
        @param new_topic_name: prefilled value (string)
        @param topics: list of topics (list of strings)
        @param create_in_topic: preselected value for topic selection
        @param ln: language"""
        _ = gettext_set_language(ln)
        out = """
<form name="create_basket" action="%(action)s" method="post">
  <input type="hidden" name="ln" value="%(ln)s" />
  <div style="padding:10px;">
    %(create_box)s
    %(recids)s
    %(es_title)s
    %(es_desc)s
    %(es_url)s
    <input type="hidden" name="colid" value="%(colid)s" />
    <input type="hidden" name="copy" value="%(copy)i" />
    <input type="hidden" name="referer" value="%(referer)s" />
    <input type="hidden" name="move_from_basket" value="%(move_from_basket)s" />
    <input type="submit" value="%(label)s" class="btn btn-primary formbutton"/>
  </div>
</form>""" % {'action': CFG_SITE_URL + '/yourbaskets/create_basket',
              'ln': ln,
              'create_box': self.tmpl_create_box(new_basket_name=new_basket_name,
                                                 new_topic_name=new_topic_name,
                                                 topics=topics,
                                                 selected_topic=create_in_topic,
                                                 ln=ln),
              'recids': recids and '\n'.join(['<input type="hidden" name="recid" value="%s" />' % \
                                              recid for recid in recids]) or '',
              'es_title': es_title and \
                '<input type="hidden" name="es_title" value="%s" />' % \
                (cgi.escape(es_title, True),) or '',
              'es_desc': es_desc and \
                '<input type="hidden" name="es_desc" value="%s" />' % \
                (cgi.escape(es_desc, True),) or '',
              'es_url': es_url and \
                '<input type="hidden" name="es_url" value="%s" />' % \
                (cgi.escape(es_url, True),) or '',
              'colid': colid,
              'copy': copy and 1 or 0,
              'referer': referer,
              'move_from_basket': move_from_basket,
              'label': _("Create new basket")}
        return out

    ############################ external sources ###########################

    def tmpl_external_source_add_box(self,
                                     title="",
                                     desc="",
                                     url="",
                                     ln=CFG_SITE_LANG):
        """Template for adding external items."""

        _ = gettext_set_language(ln)

        # Instead of the rich editor we choose to use everytime a simple textarea
        # because a rich text editor may already be used in the add to baskets
        # page to anotate.
        #desc_editor = get_html_text_editor(name="es_desc",
        #                                   content=desc,
        #                                   textual_content=desc,
        #                                   width="640px",
        #                                   height="100px",
        #                                   enabled=cfg['CFG_WEBBASKET_USE_RICH_TEXT_EDITOR'],
        #                                   toolbar_set="WebComment")
        desc_editor = """<textarea name="es_desc" style="width: 600px; height: 100px;">%(value)s</textarea>""" % \
                      {'value': cgi.escape(desc, True)}

        out = """
<table class="bskbasket" width="100%%">
  <thead>
    <tr>
      <td class="bskbasketheader">
        <table>
          <tr>
            <td class="bskbasketheadertitle">
              <strong>
              %(header_label)s
              </strong>
            </td>
        </table>
      </td>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="padding: 10px;">
        %(instructions_label)s:
      </td>
    </tr>
    <tr>
      <td style="padding: 10px;">
        <p align="left">
        <small>%(title_label)s:</small>
        <br />
        <input type="text" name="es_title" size="65" value="%(es_title)s" />
        </p>
        <p align="left">
        <small>%(desc_label)s:</small>
        <br />
        %(desc_editor)s
        </p>
        <p align="left">
        <small>%(url_label)s:</small>
        <br />
        <input type="text" name="es_url" size="65" value="%(es_url)s" />
        <input type="hidden" name="colid" value="-1" />
        </p>
      </td>
    </tr>
  </tbody>
</table>""" % {'header_label': _('External item'),
               'instructions_label': _('Provide a url for the external item you wish to add and fill in a title and description'),
               'title_label': _('Title'),
               'es_title': cgi.escape(title, True),
               'desc_label': _('Description'),
               'desc_editor': desc_editor,
               'url_label': _('URL'),
               'es_url': cgi.escape(url, True)}

        return out

    ########################## functions on baskets #########################

    def tmpl_add(self,
                 recids=[],
                 category="",
                 bskid=0,
                 colid=0,
                 es_title="",
                 es_desc="",
                 es_url="",
                 note_body="",
                 personal_basket_list=(),
                 group_basket_list=(),
                 successful_add=False,
                 copy=False,
                 move_from_basket=0,
                 referer='',
                 ln=CFG_SITE_LANG):
        """Template for addding items to baskets."""

        _ = gettext_set_language(ln)

        if successful_add:
            out = """
%(success_label)s.
<br /><br />
%(proceed_label)s""" % {'success_label': _('%(number)i items have been successfully added to your basket', number=(colid == -1 and 1 or len(recids))),
                        'proceed_label': _('Proceed to the %(x_url_open)sbasket%(x_url_close)s') % \
                                         {'x_url_open': '<a href="%s/yourbaskets/display?category=%s&amp;bskid=%i&amp;ln=%s">' % (CFG_SITE_URL, category, bskid, ln),
                                         'x_url_close': "</a>"}}
            if referer:
                if copy:
                    out +=  _(' or return to your %(x_url_open)sprevious basket%(x_url_close)s') % \
                            {'x_url_open': '<a href="%s">' % referer,
                             'x_url_close': '</a>'}
                else:
                    out +=  _(' or go %(x_url_open)sback%(x_url_close)s') % \
                            {'x_url_open': '<a href="%s">' % referer,
                             'x_url_close': '</a>'}
            out += "."

            return out

        out=""

        #If no recids were specified the page is asking which external item to add,
        #so we remind to the user to use the search engine for internal items.
        #(having no recids specified is just like having a colid equal -1)
        if len(recids) == 0:
        #if colid == -1:

            out += """
    <div class="bskbasket">
        <div class="well bskbasketheader">
            <div class="row-fluid bskactions">
                <div class="col-md-1 bskactions">
                    <img src="%(logo)s" alt="%(label)s" />
                </div>
                <div class="col-md-11 bsktitle">
                    <b>Adding items to your basket</b>
                </div>
            </div>
            <div class="row-fluid bskbasketheader bskactions">
                <div class="col-md-12">
                    To add internal items to your basket please select them
                    through the  <a href="%(search_link)s">search page</a>
                    and use the "Add to basket" functionality.
                    For any external resource please use the
                    "External item" form below.
                </div>
            </div>
        </div>"""
            out %= {'logo': "%s/img/tick.gif" % (CFG_SITE_URL,),
                    'label': "tick",
                    'search_link': "%s" % (CFG_SITE_URL, )}

        note_editor = get_html_text_editor(name="note_body",
                                           content=note_body,
                                           textual_content=note_body,
                                           width="600px",
                                           height="110px",
                                           enabled=cfg['CFG_WEBBASKET_USE_RICH_TEXT_EDITOR'],
                                           toolbar_set="WebComment")

        select_options = create_add_box_select_options(category,
                                                       bskid,
                                                       personal_basket_list,
                                                       group_basket_list,
                                                       ln)

        hidden_recids = ""
        for recid in recids:
            hidden_recids += """
        <input type="hidden" name="recid" value="%s" />""" % (recid,)

        action = "%s/yourbaskets/add" % (CFG_SITE_URL,)

        out += """
<form name="add_to_basket" action="%(action)s" method="post">""" % {'action': action}

        if colid == -1:
            out += self.tmpl_external_source_add_box(es_title, es_desc, es_url, ln)

        out += """
<div class="row-fluid">
    <div class="col-md-12 well bskbasketheader bskbasketheadertitle">
        <strong>
            %(header_label)s
        </strong>
    </div>
</div>
<div class="row-fluid">
    %(create_new_basket)s
</div>
<div class="row-fluid">
    <fieldset>
        <label><small>%(note_label)s:</small></label>
        %(note_editor)s
    </fieldset>
</div>
<div class="row-fluid">
    %(hidden_recids)s
    <input type="hidden" name="colid" value="%(colid)s" />
    <input type="hidden" name="copy" value="%(copy)i" />
    <input type="hidden" name="referer" value="%(referer)s" />
	<input type="hidden" name="move_from_basket" value="%(move_from_basket)s" />
	<input type="submit" class="btn btn-primary formbutton" value="%(add_label)s" />
    <input type="button" class="btn nonsubmitbutton" value="%(cancel_label)s" onClick="window.location='/'" />
</div>"""   % {'header_label': _("Adding %(number)i items to your baskets", number=(colid == -1 and 1 or len(recids))),
               'create_new_basket': _("Please choose a basket: %(x_basket_selection_box)s %(x_fmt_open)s(or %(x_url_open)screate a new one%(x_url_close)s first)%(x_fmt_close)s",
                                    **{'x_basket_selection_box': '&nbsp;<select name="b">%s</select>' % select_options,
                                       'x_url_open': colid == -1 and ('''<a href="%s/yourbaskets/create_basket?colid=-1" onClick="this.href+= \
                                                                        '&amp;es_title=' + encodeURIComponent(document.add_to_basket.es_title.value) + \
                                                                        '&amp;es_url=' + encodeURIComponent(document.add_to_basket.es_url.value) + \
                                                                        '&amp;es_desc=' + encodeURIComponent(document.add_to_basket.es_desc.value);">''' % \
                                                                    (CFG_SITE_URL,))
                                                                or ('<a href="%s/yourbaskets/create_basket?copy=%i&amp;referer=%s&amp;colid=%i&amp;move_from_basket=%i&amp;recid=%s">' % \
                                                                    (CFG_SITE_URL,
                                                                     copy and 1 or 0,
                                                                     urllib.quote(referer),
                                                                     colid,
                                                                     int(move_from_basket),
                                                                     '&amp;recid='.join(str(recid) for recid in recids))),
                                       'x_url_close': '</a>',
                                       'x_fmt_open': '<br /><small>',
                                       'x_fmt_close': '</small>'}),
               'move_from_basket': move_from_basket,
               'note_label': len(recids) > 1 and _('Optionally, add a note to each one of these items') \
               or _('Optionally, add a note to this item'),
               'note_editor': note_editor,
               'hidden_recids': hidden_recids,
               'colid': colid,
               'copy': copy and 1 or 0,
               'referer': referer,
               'add_label': _('Add items'),
               'cancel_label': _('Cancel')}

        out += """
</form>"""

        return out

    def tmpl_confirm_delete(self, bskid,
                            (nb_users, nb_groups, nb_alerts),
                            category=cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE'],
                            selected_topic="", selected_group_id=0,
                            ln=CFG_SITE_LANG):
        """
        display a confirm message
        @param bskid: basket id
        @param nb*: nb of users/groups/alerts linked to this basket
        @param category: private, group or external baskets are selected
        @param selected_topic: if private baskets, topic nb
        @param selected_group_id: if group: group to display baskets of
        @param ln: language
        @return: html output
        """
        _ = gettext_set_language(ln)
        message = cgi.escape(_("Are you sure you want to delete this basket?"), True)
        if nb_users:
            message += '<p>' + cgi.escape(_("%(x_num)i users are subscribed to this basket.", x_num=nb_users), True) + '</p>'
        if nb_groups:
            message += '<p>' + cgi.escape(_("%(x_num)i user groups are subscribed to this basket.", x_num=nb_groups), True) + '</p>'
        if nb_alerts:
            message += '<p>' + cgi.escape(_("You have set %(x_num)i alerts on this basket.", x_num=nb_alerts), True) + '</p>'
        out = """
<table class="confirmoperation">
  <tr>
    <td colspan="2" class="confirmmessage">
      %(message)s
    </td>
  </tr>
  <tr>
    <td>
      <form name="validate" action="%(url_ok)s" method="post">
        <input type="hidden" name="confirmed" value="1" />
        <input type="hidden" name="category" value="%(category)s" />
        <input type="hidden" name="group" value="%(group)i" />
        <input type="hidden" name="topic" value="%(topic)s" />
        <input type="hidden" name="ln" value="%(ln)s" />
        <input type="hidden" name="bskid" value="%(bskid)i" />
        <input type="submit" value="%(yes_label)s" class="btn btn-primary formbutton" />
      </form>
    </td>
    <td>
      <form name="cancel" action="%(url_cancel)s" method="get">
        <input type="hidden" name="category" value="%(category)s" />
        <input type="hidden" name="group" value="%(group)i" />
        <input type="hidden" name="topic" value="%(topic)s" />
        <input type="hidden" name="ln" value="%(ln)s" />
        <input type="submit" value="%(no_label)s" class="btn btn-primary formbutton" />
      </form>
    </td>
  </tr>
</table>"""% {'message': message,
              'bskid': bskid,
              'url_ok': 'delete',
              'url_cancel': 'display',
              'category': category,
              'topic': cgi.escape(selected_topic, True),
              'group': selected_group_id,
              'ln':ln,
              'yes_label': _("Yes"),
              'no_label': _("Cancel")}
        return out

    def tmpl_edit(self, bskid, bsk_name, topic, topics, groups_rights, external_rights,
                  display_general=0, display_sharing=0, display_delete=0, ln=CFG_SITE_LANG):
        """Display interface for rights management over the given basket
        @param group_rights: list of (group id, name, rights) tuples
        @param external_rights: rights as defined in cfg['CFG_WEBBASKET_SHARE_LEVELS']for public access.
        @param display_general: display fields name and topic, used with personal baskets
        @param display_sharing: display sharing possibilities
        @param display_delete: display delete basket button
        """
        _ = gettext_set_language(ln)
        general_body = ''
        if display_general:
            general_body = """
<tr>
  <td class="bskcontentcol">%s</td>
  <td class="bskcontentcol"><input type="text" name="new_name" value="%s"/></td>
</tr>""" % (_("Basket name"), cgi.escape(bsk_name, True))
            #topics_selection = zip(range(len(topics)), topics)
            topics_selection = zip(topics, topics)
            topics_selection.insert(0, (-1, _("Choose topic")))
            topics_body = """
<tr>
  <td style="padding: 10 5 0 5;">%s</td>
  <td style="padding: 10 5 0 0;">%s</td>
</tr>
<tr>
  <td style="padding: 0 5 10 5;">%s</td>
  <td style="padding: 0 5 10 0;"><input type="text" name="new_topic_name" />
</tr>""" %  (_("Choose topic"),
             self.__create_select_menu('new_topic', topics_selection, topic),
             _("or create a new one"))
            general_body += topics_body
        general_box = self.__tmpl_basket_box(img=CFG_SITE_URL + '/img/webbasket_user.png',
                                             title=_("General settings"),
                                             body = general_body)
        groups_body = ''
        if display_sharing:
            for (group_id, name, rights) in groups_rights:
                groups_body += """
<tr>
  <td>%s</td>
  <td>%s</td>
</tr>""" % (name, self.__create_group_rights_selection_menu(group_id, rights, ln))
            groups_body += """
<tr>
  <td colspan="2">
    <input type="submit" name="add_group" class="btn nonsubmitbutton" value="%s"/>
  </td>
</tr>""" % _("Add group")
        else:
            groups_body = '<tr><td colspan="2">%s</td></tr>'
            groups_body %= self.tmpl_create_guest_forbidden_box(ln)
        groups_box = self.__tmpl_basket_box(img=CFG_SITE_URL + '/img/webbasket_usergroup.png',
                                            title=_("Manage group rights"),
                                            body=groups_body)
        if display_sharing:
            external_body = """
<tr>
  <td>%s</td>
</tr>""" % self.__create_rights_selection_menu('external', external_rights, ln)
        else:
            external_body = '<tr><td colspan="2">%s</td></tr>'
            external_body %= self.tmpl_create_guest_forbidden_box(ln)

        external_box = self.__tmpl_basket_box(img=CFG_SITE_URL + '/img/webbasket_world.png',
                                              title=_("Manage global sharing rights"),
                                              body=external_body)
        delete_button = ''
        if display_delete:
            delete_button = '<input type="submit" class="btn nonsubmitbutton" name="delete" value="%s" />'
            delete_button %=  _("Delete basket")
        out = """
<form name="edit" action="%(action)s" method="post">
  <p>%(label)s</p>
  <input type="hidden" name="ln" value="%(ln)s" />
  <input type="hidden" name="bskid" value="%(bskid)i" />
  <input type="hidden" name="topic" value ="%(topic)s" />
  <table>
    <tr>
      <td colspan="3">%(general)s</td>
    </tr>
    <tr>
      <td colspan="3">%(groups)s</td>
    </tr>
    <tr>
      <td colspan="3">%(external)s</td>
    </tr>
    <tr>
      <td><input type="submit" class="btn btn-primary formbutton" name="submit" value="%(submit_label)s" /></td>
      <td><input type="submit" class="btn nonsubmitbutton" name="cancel" value="%(cancel_label)s" /></td>
      <td>%(delete_button)s</td>
    </tr>
  </table>

</form>""" % {'label': _('Editing basket %(x_basket_name)s',
                         x_basket_name=cgi.escape(bsk_name, True)),
              'action': CFG_SITE_URL + '/yourbaskets/edit',
              'ln': ln,
              'topic': cgi.escape(topic, True),
              'bskid': bskid,
              'general': general_box,
              'groups': groups_box,
              'external': external_box,
              'submit_label': _("Save changes"),
              'cancel_label': _("Cancel"),
              'delete_button': delete_button}
        return out

    def tmpl_edit_topic(self, topic, display_general=0, display_delete=0, ln=CFG_SITE_LANG):
        """Display interface for topic editing.
        @param display_general: display topic name
        @param display_delete: display delete topic button
        """
        _ = gettext_set_language(ln)
        general_body = ''
        if not topic:
            general_body = """<div class="important" style="padding: 10px;">%s</div>"""
            general_body %= ("You must provide a valid topic name.",)
            display_general = False
        if display_general:
            general_body = """
<tr>
  <td>%s</td>
  <td><input type="text" name="new_name" value="%s"/></td>
</tr>""" % (_("Topic name"), cgi.escape(topic, True))
  #<td class="bskcontentcol">%s</td>
  #<td class="bskcontentcol"><input type="text" name="new_name" value="%s"/></td>

        general_box = self.__tmpl_basket_box(img=CFG_SITE_URL + '/img/webbasket_user.png',
                                             title=_("General settings"),
                                             body = general_body)

        delete_button = ''
        display_delete = False
        if display_delete:
            delete_button = '<input type="submit" class="btn nonsubmitbutton" name="delete" value="%s" />'
            delete_button %=  _("Delete basket")
        out = """
<form name="edit" action="%(action)s" method="post">
  <p>%(label)s</p>
  <input type="hidden" name="ln" value="%(ln)s" />
  <input type="hidden" name="topic" value ="%(topic)s" />
  <table>
    <tr>
      <td colspan="3">%(general)s</td>
    </tr>
    <tr>
      <td><input type="submit" class="btn btn-primary formbutton" name="submit" value="%(submit_label)s" /></td>
      <td><input type="submit" class="btn nonsubmitbutton" name="cancel" value="%(cancel_label)s" /></td>
      <td>%(delete_button)s</td>
    </tr>
  </table>

</form>""" % {'label': _('Editing topic: %(x_topic_name)s',
                         x_topic_name=cgi.escape(topic, True)),
              'action': CFG_SITE_URL + '/yourbaskets/edit_topic',
              'ln': ln,
              'topic': cgi.escape(topic, True),
              'general': general_box,
              'submit_label': _("Save changes"),
              'cancel_label': _("Cancel"),
              'delete_button': delete_button}
        return out

    def __create_rights_selection_menu(self, name, current_rights, ln=CFG_SITE_LANG):
        """Private function. create a drop down menu for selection of rights
        @param name: name of menu (for HTML name attribute)
        @param current_rights: rights as defined in cfg['CFG_WEBBASKET_SHARE_LEVELS']
        @param ln: language
        """
        _ = gettext_set_language(ln)
        elements = [('NO', _("No rights")),
                    (cfg['CFG_WEBBASKET_SHARE_LEVELS']['READITM'],
                     _("View records")),
                    (cfg['CFG_WEBBASKET_SHARE_LEVELS']['READCMT'],
                     '... ' + _("and") + ' ' + _("view comments")),
                    (cfg['CFG_WEBBASKET_SHARE_LEVELS']['ADDCMT'],
                     '... ' + _("and") + ' ' + _("add comments"))]
        return self.__create_select_menu(name, elements, current_rights)

    def __create_group_rights_selection_menu(self, group_id, current_rights, ln=CFG_SITE_LANG):
        """Private function. create a drop down menu for selection of rights
        @param current_rights: rights as defined in cfg['CFG_WEBBASKET_SHARE_LEVELS']
        @param ln: language
        """
        _ = gettext_set_language(ln)
        elements = [(str(group_id) + '_' + 'NO', _("No rights")),
                    (str(group_id) + '_' + cfg['CFG_WEBBASKET_SHARE_LEVELS']['READITM'],
                     _("View records")),
                    (str(group_id) + '_' + cfg['CFG_WEBBASKET_SHARE_LEVELS']['READCMT'],
                     '... ' + _("and") + ' ' + _("view notes")),
                    (str(group_id) + '_' + cfg['CFG_WEBBASKET_SHARE_LEVELS']['ADDCMT'],
                     '... ' + _("and") + ' ' + _("add notes")),
                    (str(group_id) + '_' + cfg['CFG_WEBBASKET_SHARE_LEVELS']['ADDITM'],
                     '... ' + _("and") + ' ' + _("add records")),
                    (str(group_id) + '_' + cfg['CFG_WEBBASKET_SHARE_LEVELS']['DELCMT'],
                     '... ' + _("and") + ' ' + _("delete notes")),
                    (str(group_id) + '_' + cfg['CFG_WEBBASKET_SHARE_LEVELS']['DELITM'],
                     '... ' + _("and") + ' ' + _("remove records")),
                    (str(group_id) + '_' + cfg['CFG_WEBBASKET_SHARE_LEVELS']['MANAGE'],
                     '... ' + _("and") + ' ' + _("manage sharing rights"))
                    ]
        return self.__create_select_menu('groups', elements, str(group_id) + '_' + current_rights)

    def tmpl_add_group(self, bskid, selected_topic, groups=[], ln=CFG_SITE_LANG):
        """
        return form for selection of groups.
        @param bskid: basket id (int)
        @param selected_topic: topic currently displayed (int)
        @param groups: list of tuples (group id, group name)
        @param ln: language
        """
        _ = gettext_set_language(ln)
        if len(groups):
            groups_body = """
<tr>
  <td>%s</td>
</tr>""" % self.__create_select_menu('new_group', groups, selected_key=None)
        else:
            groups_body = """
<tr>
  <td>%s</td>
</tr>""" % _("You are not a member of a group.")
        groups_box = self.__tmpl_basket_box(img=CFG_SITE_URL + '/img/webbasket_usergroup.png',
                                            title=_("Add group"),
                                            body=groups_body)
        out = """
<form name="add_group" action="%(action)s" method="post">
  <p>%(label)s</p>
  <input type="hidden" name="ln" value="%(ln)s" />
  <input type="hidden" name="bskid" value="%(bskid)i" />
  <input type="hidden" name="topic" value ="%(topic)s" />
  <table style="width:100%%;">
    <tr>
      <td style="width:50%%;vertical-align:top;">%(groups)s</td>
      <td style="width:50%%;vertical-align:top;"></td>
    </tr>
    <tr>
      <td colspan="2">
        <input type="submit" class="btn formbutton" name="group_cancel" value="%(cancel_label)s" />
        <input type="submit" class="btn btn-primary formbutton" name="add_group" value="%(submit_label)s" />
      </td>
    </tr>
  </table>
</form>""" % {'label': _('Sharing basket to a new group'),
              'action': CFG_SITE_URL + '/yourbaskets/edit',
              'ln': ln,
              'topic': cgi.escape(selected_topic, True),
              'bskid': bskid,
              'groups': groups_box,
              'cancel_label': _("Cancel"),
              'submit_label': _("Add group")}
        return out

    def tmpl_personal_baskets_selection_box(self,
                                            baskets=[],
                                            select_box_name='baskets',
                                            selected_bskid=None,
                                            ln=CFG_SITE_LANG):
        """return an HTML popupmenu
        @param baskets: list of (bskid, bsk_name, bsk_topic) tuples
        @param select_box_name: name that will be used for the control
        @param selected_bskid: id of the selcte basket, use None for no selection
        @param ln: language"""
        _ = gettext_set_language(ln)
        elements = [(0, '- ' + _("no basket") + ' -')]
        for (bskid, bsk_name, bsk_topic) in baskets:
            elements.append((bskid, bsk_topic + ' &gt; ' + bsk_name))
        return self.__create_select_menu(select_box_name, elements, selected_bskid)

    def tmpl_create_guest_warning_box(self, ln=CFG_SITE_LANG):
        """return html warning box for non registered users"""
        _ = gettext_set_language(ln)
        message = _("You are logged in as a guest user, so your baskets will disappear at the end of the current session.") + ' '
        message += _("If you wish you can %(x_url_open)slogin or register here%(x_url_close)s.") %\
            {'x_url_open': '<a href="' + CFG_SITE_SECURE_URL + '/youraccount/login?ln=' + ln + '">',
             'x_url_close': '</a>'}
        out = """
<table class="errorbox">
    <tr>
      <th class="errorboxheader">%s</th>
    </tr>
</table>"""
        return out % message

    def tmpl_create_guest_forbidden_box(self, ln=CFG_SITE_LANG):
        """return html warning box for non registered users"""
        _ = gettext_set_language(ln)
        message = _("This functionality is forbidden to guest users.") + ' '
        message += _("If you wish you can %(x_url_open)slogin or register here%(x_url_close)s.") %\
            {'x_url_open': '<a href="' + CFG_SITE_SECURE_URL + '/youraccount/login?ln=' + ln + '">',
             'x_url_close': '</a>'}
        out = """
<table class="errorbox">
  <thead>
    <tr>
      <th class="errorboxheader">%s</th>
    </tr>
  </thead>
</table>"""
        return out % message


    ############################ Utilities ###################################

    def __create_select_menu(self, name, elements, selected_key=None):
        """ private function, returns a popup menu
        @param name: name of HTML control
        @param elements: list of (key, value)
        @param selected_key: item that should be selected (key of elements tuple)
        """
        out = '<select name="%s">' % name
        for (key, label) in elements:
            selected = ''
            if key == selected_key:
                selected = ' selected="selected"'
            out += '<option value="%s"%s>%s</option>'% (cgi.escape(str(key), True), selected, cgi.escape(label, True))
        out += '</select>'
        return out

    def tmpl_warnings(self, warnings=[], ln=CFG_SITE_LANG):
        """ returns HTML for warnings """
        if type(warnings) is not list:
            warnings = [warnings]
        warningbox = ""
        if warnings:
            warningbox = "<div class=\"important\">\n"
            for warning in warnings:
                lines = warning.split("\n")
                warningbox += "  <p>"
                for line in lines[0:-1]:
                    warningbox += line + "    <br />\n"
                warningbox += lines[-1] + "  </p>"
            warningbox += "</div><br />\n"
        return warningbox

    def tmpl_back_link(self, link, ln=CFG_SITE_LANG):
        """ returns HTML for a link whose label should be
        'Back to search results'
        """
        _ = gettext_set_language(ln)
        label = _("Back to search results")
        out = '<a href="%s">%s</a>' % (link, label)
        return out

    def __create_webmessage_link(self, to, display_name, ln=CFG_SITE_LANG):
        """prints a link to the messaging system"""
        link = "%s/yourmessages/write?msg_to=%s&amp;ln=%s" % (CFG_SITE_URL, to, ln)
        if to:
            return '<a href="%s" class="maillink">%s</a>' % (link, display_name)
        else:
            return display_name

    def tmpl_xml_basket(self, items=[]):
        """Template for XML output of basket
        @param items: XML version of each item (list)"""
        items_xml = ''
        for item in items:
            items_xml += '  ' + item + '\n'
        return """<?xml version="1.0" encoding="UTF-8"?>
<collection>
%s
</collection>
""" % items_xml

    ############################ Baskets ###################################

    ##################################
    ########### BASKET VIEW ##########
    ##################################

    def tmpl_basket(self,
                    bskid,
                    name,
                    date_modification,
                    nb_items,
                    nb_subscribers,
                    (user_can_view_content,
                     user_can_edit_basket,
                     user_can_view_notes,
                     user_can_add_notes,
                     user_can_add_item,
                     user_can_delete_item),
                    nb_comments,
                    share_level,
                    selected_category=cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE'],
                    selected_topic="",
                    selected_group=0,
                    items=[],
                    of='hb',
                    ln=CFG_SITE_LANG):
        """Template for basket display."""

        if not of.startswith('x'):
            out = """
<table class="bskbasket" width="100%">"""
        else:
            out = ""

        if not of.startswith('x'):
            out += self.tmpl_basket_header(bskid,
                                           name,
                                           nb_items,
                                           nb_subscribers,
                                           date_modification,
                                           (user_can_view_content,
                                            user_can_add_item,
                                            user_can_edit_basket,
                                            user_can_view_notes),
                                           selected_category,
                                           nb_comments,
                                           selected_topic,
                                           share_level,
                                           ln)

        out += self.tmpl_basket_content(bskid,
                                        (user_can_view_content,
                                         user_can_view_notes,
                                         user_can_add_notes,
                                         user_can_add_item,
                                         user_can_delete_item),
                                        selected_category,
                                        selected_topic,
                                        selected_group,
                                        items,
                                        of,
                                        ln)

        # Moved footer after content - a footer should be last anyway?
        if not of.startswith('x'):
            out += self.tmpl_basket_footer(bskid,
                                           nb_items,
                                           (user_can_view_content,
                                            user_can_add_item,
                                            user_can_edit_basket),
                                           selected_category,
                                           selected_topic,
                                           share_level,
                                           ln)

        if not of.startswith('x'):
            out += """
</table>"""

        if not of.startswith('x'):
            out += self.tmpl_create_export_as_list(selected_category,
                                                   selected_topic,
                                                   selected_group,
                                                   bskid,
                                                   None,
                                                   False)
        return out

    def tmpl_basket_header(self,
                           bskid,
                           name,
                           nb_items,
                           nb_subscribers,
                           date_modification,
                           (user_can_view_content,
                            user_can_add_item,
                            user_can_edit_basket,
                            user_can_view_notes),
                           selected_category,
                           nb_comments,
                           selected_topic,
                           share_level,
                           ln=CFG_SITE_LANG):
        """Template for basket header display."""

        _ = gettext_set_language(ln)

        optional_colspan = nb_items and user_can_view_content and ' colspan="3"' or ''
        records_field = '<br />' + _('%(x_num)i items', x_num=nb_items)
        comments_field = user_can_view_notes and (nb_comments and (', ' + _('%(x_num)i notes', x_num=nb_comments)) or ', ' + _('no notes yet')) or ''
        subscribers_field = selected_category == cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE'] and \
                            share_level == 0 and \
                            ', ' + (_('%(x_sub)i subscribers', x_sub=nb_subscribers)) or \
                            ''
        last_update_field = '<br />' + _('last update') + ': ' + date_modification

        ## By default we assume the user has no rights on the basket
        #edit_basket = """<small>%s</small>""" % (_("You cannot edit this basket"),)
        #delete_basket = """<small>%s</small>""" % (_("You cannot delete this basket"),)
        edit_basket = ""
        delete_basket = ""
        add_ext_resource = ""

        if user_can_add_item:
            add_ext_resource_url = """%s/yourbaskets/add?category=%s&amp;bskid=%i&amp;wait=1""" % (CFG_SITE_URL,selected_category,bskid,)
            add_ext_resource_logo = """<i class="icon %s"></i> """ % (ICON_ADD_ITEM,)
            add_ext_resource = """<a href="%s">%s%s</a>""" % (add_ext_resource_url, add_ext_resource_logo, _("Add item"))

        if user_can_edit_basket:
            edit_basket_url = """%s/yourbaskets/edit?bskid=%i&amp;topic=%s&amp;ln=%s""" % (CFG_SITE_URL, bskid, urllib.quote(selected_topic), ln)
            edit_basket_logo = """<i class="icon %s"></i> """ % (ICON_EDIT_BASKET,)
            edit_basket = """&nbsp;&nbsp;\n<a href="%s">%s%s</a>""" % (edit_basket_url, edit_basket_logo, _("Edit basket"))
            delete_basket_url = """%s/yourbaskets/edit?bskid=%i&amp;topic=%s&amp;delete=1&amp;ln=%s""" % (CFG_SITE_URL, bskid, urllib.quote(selected_topic), ln)
            delete_basket_logo = """<i class="icon %s"></i> """ % (ICON_DELETE_BASKET,)
            delete_basket = """&nbsp;&nbsp;\n<a href="%s">%s%s</a>""" % (delete_basket_url, delete_basket_logo, _("Delete basket"))

        if selected_category==cfg['CFG_WEBBASKET_CATEGORIES']['EXTERNAL']:
            unsubscribe_url = """%s/yourbaskets/unsubscribe?bskid=%i&amp;ln=%s""" % (CFG_SITE_URL, bskid, ln)
            unsubscribe_logo = """<i class="icon %s"></i> """ % (ICON_UNSUBSCRIBE,)
            unsubscribe = """&nbsp;&nbsp;\n<a href="%s">%s%s</a>""" % (unsubscribe_url, unsubscribe_logo, _("Unsubscribe from basket"))
        else:
            unsubscribe = ""

        out = """

    <div class="row-fluid well" %(optional_colspan)s>
      <!-- bskbasketheadertitle -->
      <div class="col-md-4">
        <strong>
          %(name)s
        </strong>
        <small>
          %(records_field)s%(comments_field)s%(subscribers_field)s
          %(last_update_field)s
        </small>
      </div>

      <!-- bskbasketheaderoptions -->
      <div class="col-md-5 col-md-offset-3 pagination-right">
        %(add_ext_resource)s
        %(edit_basket)s
        %(delete_basket)s
        %(unsubscribe)s
      </div>
    </div>

  """

        out %= {'optional_colspan': optional_colspan,
                'name': cgi.escape(name, True),
                'nb_items': nb_items,
                'records_field': records_field,
                'comments_field': comments_field,
                'subscribers_field': subscribers_field,
                'last_update_field': last_update_field,
                'add_ext_resource': add_ext_resource,
                'edit_basket': edit_basket,
                'delete_basket': delete_basket,
                'unsubscribe': unsubscribe,
                }

        return out

    def tmpl_basket_footer(self,
                           bskid,
                           nb_items,
                           (user_can_view_content,
                            user_can_add_item,
                            user_can_edit_basket),
                           selected_category,
                           selected_topic,
                           share_level=None,
                           ln=CFG_SITE_LANG):
        """Template for basket footer display."""

        _ = gettext_set_language(ln)

        ## By default we assume the user has no rights on the basket
        edit_basket = ""
        delete_basket = ""
        add_ext_resource = ""

        if user_can_add_item:
            add_ext_resource_url = """%s/yourbaskets/add?category=%s&amp;bskid=%i&amp;wait=1""" % (CFG_SITE_URL,selected_category,bskid,)
            add_ext_resource_logo = """<i class="icon %s"></i> """ % (ICON_ADD_ITEM,)
            add_ext_resource = """<a href="%s">%s%s</a>""" % (add_ext_resource_url, add_ext_resource_logo, _("Add item"))

        if user_can_edit_basket:
            edit_basket_url = """%s/yourbaskets/edit?bskid=%i&amp;topic=%s&amp;ln=%s""" % (CFG_SITE_URL, bskid, urllib.quote(selected_topic), ln)
            edit_basket_logo = """<i class="icon %s"></i> """ % (ICON_EDIT_BASKET)
            edit_basket = """&nbsp;&nbsp;\n<a href="%s">%s%s</a>""" % (edit_basket_url, edit_basket_logo, _("Edit basket"))
            delete_basket_url = """%s/yourbaskets/edit?bskid=%i&amp;topic=%s&amp;delete=1&amp;ln=%s""" % (CFG_SITE_URL, bskid, urllib.quote(selected_topic), ln)
            delete_basket_logo = """<i class="icon %s"></i> """ % (ICON_DELETE_BASKET,)
            delete_basket = """&nbsp;&nbsp;\n<a href="%s">%s%s</a>""" % (delete_basket_url, delete_basket_logo, _("Delete basket"))

        if selected_category==cfg['CFG_WEBBASKET_CATEGORIES']['EXTERNAL']:
            unsubscribe_url = """%s/yourbaskets/unsubscribe?bskid=%i&amp;ln=%s""" % (CFG_SITE_URL, bskid, ln)
            unsubscribe_logo = """<i class="icon %s"></i> """ % (ICON_UNSUBSCRIBE,)
            unsubscribe = """&nbsp;&nbsp;\n<a href="%s">%s%s</a>""" % (unsubscribe_url, unsubscribe_logo, _("Unsubscribe from basket"))
        else:
            unsubscribe = ""
        if share_level == 0:
            display_public_url = """%s/yourbaskets/display_public?bskid=%i""" % (CFG_SITE_URL, bskid)
            display_public_text = _("This basket is publicly accessible at the following address:")
            display_public = """%s<br /><a href="%s">%s</a>""" % (display_public_text, display_public_url, display_public_url)
        else:
            display_public = ""

        out = """
        <div class="row-fluid well">
            <div class="col-md-4 bskbasketfootertitle">
                <small>
                %(display_public)s
                </small>
            </div>
            <div class="col-md-5 col-md-offset-3 pagination-right bskbasketfooteroptions">
                %(add_ext_resource)s
                %(edit_basket)s
                %(delete_basket)s
                %(unsubscribe)s
            </div>
        </div>"""

        out %= {'display_public': display_public,
                'add_ext_resource': add_ext_resource,
                'edit_basket': edit_basket,
                'delete_basket': delete_basket,
                'unsubscribe': unsubscribe}

        return out

    def tmpl_basket_content(self,
                            bskid,
                            (user_can_view_content,
                             user_can_view_notes,
                             user_can_add_notes,
                             user_can_add_item,
                             user_can_delete_item),
                            selected_category=cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE'],
                            selected_topic="",
                            selected_group=0,
                            items=[],
                            of='hb',
                            ln=CFG_SITE_LANG):
        """Template for basket content display."""

        if not of.startswith('x'):
            _ = gettext_set_language(ln)
            items_html = """
  <tbody>"""
            if user_can_view_content:
                if not(items):
                    items_html += """
    <tr>
      <td style="text-align:center; height:100px">
      %s
      </td>
    </tr>""" % _("This basket does not contain any records yet.")
                else:
                    count = 0
                    for item in items:
                        count += 1
                        copy = 1
                        go_up = go_down = delete = 0
                        if user_can_add_item:
                            go_up = go_down = 1
                            if item == items[0]:
                                go_up = 0
                            if item == items[-1]:
                                go_down = 0
                        if user_can_delete_item:
                            delete = 1
                        items_html += self.__tmpl_basket_item(count=count,
                                                              bskid=bskid,
                                                              item=item,
                                                              uparrow=go_up,
                                                              downarrow=go_down,
                                                              copy_item=copy,
                                                              delete_item=delete,
                                                              view_notes=user_can_view_notes,
                                                              add_notes=user_can_add_notes,
                                                              selected_category=selected_category,
                                                              selected_topic=selected_topic,
                                                              selected_group=selected_group,
                                                              ln=ln)
            else:
                items_html += """
    <tr>
      <td style="text-align:center; height:100px">
      %s
      </td>
    </tr>""" % _("You do not have sufficient rights to view this basket's content.")
            items_html += """
  </tbody>"""
            return items_html
        else:
            items_xml = ""
            for item in items:
                items_xml += item[4] + "\n"
            return items_xml


    def __tmpl_basket_item(self,
                           count,
                           bskid,
                           item,
                           uparrow=0,
                           downarrow=0,
                           copy_item=0,
                           delete_item=0,
                           view_notes=0,
                           add_notes=0,
                           selected_category=cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE'],
                           selected_topic="",
                           selected_group=0,
                           ln=CFG_SITE_LANG):
        """Template for basket item display within the basket content."""

        _ = gettext_set_language(ln)

        (recid, colid, nb_cmt, last_cmt, val, dummy) = item

        if uparrow:
            moveup_url = "%(siteurl)s/yourbaskets/modify?action=moveup&amp;bskid=%(bskid)i&amp;recid=%(recid)i"\
                         "&amp;category=%(category)s&amp;topic=%(topic)s&amp;group_id=%(group)i&amp;ln=%(ln)s" % \
                         {'siteurl': CFG_SITE_URL,
                          'bskid': bskid,
                          'recid': recid,
                          'category': selected_category,
                          'topic': urllib.quote(selected_topic),
                          'group': selected_group,
                          'ln': ln}
            moveup_icon = ICON_MOVE_UP
            moveup = """<a href="%s"><i class="icon %s" alt="%s"></i></a>""" % \
                       (moveup_url, moveup_icon, _("Move item up"))
        else:
            moveup_icon = ICON_MOVE_UP_MUTED
            moveup = """<i class="icon %s" alt="%s"></i>""" % \
                       (moveup_icon, _("You cannot move this item up"))

        if downarrow:
            movedown_url = "%(siteurl)s/yourbaskets/modify?action=movedown&amp;bskid=%(bskid)i&amp;recid=%(recid)i"\
                         "&amp;category=%(category)s&amp;topic=%(topic)s&amp;group_id=%(group)i&amp;ln=%(ln)s" % \
                         {'siteurl': CFG_SITE_URL,
                          'bskid': bskid,
                          'recid': recid,
                          'category': selected_category,
                          'topic': urllib.quote(selected_topic),
                          'group': selected_group,
                          'ln': ln}
            movedown_icon = ICON_MOVE_DOWN
            movedown = """<a href="%s"><i class="icon %s" alt="%s"></i></a>""" % \
                       (movedown_url, movedown_icon, _("Move item down"))
        else:
            movedown_icon = ICON_MOVE_DOWN_MUTED
            movedown = """<i class="icon %s" alt="%s"></i>""" % \
                       (movedown_icon, _("You cannot move this item down"))

        if copy_item:
            copy_url = "%(siteurl)s/yourbaskets/modify?action=copy&amp;bskid=%(bskid)i&amp;recid=%(recid)i"\
                       "&amp;category=%(category)s&amp;topic=%(topic)s&amp;group_id=%(group)i&amp;ln=%(ln)s" % \
                       {'siteurl': CFG_SITE_URL,
                        'bskid': bskid,
                        'recid': recid,
                        'category': selected_category,
                        'topic': urllib.quote(selected_topic),
                        'group': selected_group,
                        'ln': ln}
            copy_icon = ICON_COPY_ITEM
            copy = """<a href="%s"><i class="icon %s" alt="%s"></i> %s</a>""" % \
                       (copy_url, copy_icon, _("Copy item"), _("Copy item"))
        else:
            copy = ""

        # Move = copy + delete, so we can use their config
        if copy_item and delete_item:
            move_url = "%(siteurl)s/yourbaskets/modify?action=%(action)s&amp;bskid=%(bskid)i&amp;recid=%(recid)i"\
                       "&amp;category=%(category)s&amp;topic=%(topic)s&amp;group_id=%(group)i&amp;ln=%(ln)s" % \
                       {'siteurl': CFG_SITE_URL,
                        'action': cfg['CFG_WEBBASKET_ACTIONS']['MOVE'],
                        'bskid': bskid,
                        'recid': recid,
                        'category': selected_category,
                        'topic': urllib.quote(selected_topic),
                        'group': selected_group,
                        'ln': ln}
            move_icon = ICON_MOVE_ITEM
            move = """<a href="%s"><i class="icon %s" alt="%s"></i> %s</a>""" % \
                   (move_url, move_icon, _("Move item"), _("Move item"))
        else:
            move = ""

        if delete_item:
            remove_url = "%(siteurl)s/yourbaskets/modify?action=delete&amp;bskid=%(bskid)i&amp;recid=%(recid)i"\
                         "&amp;category=%(category)s&amp;topic=%(topic)s&amp;group=%(group)i&amp;ln=%(ln)s" % \
                         {'siteurl': CFG_SITE_URL,
                          'bskid': bskid,
                          'recid': recid,
                          'category': selected_category,
                          'topic': urllib.quote(selected_topic),
                          'group': selected_group,
                          'ln': ln}
            remove_icon = ICON_REMOVE_ITEM
            remove = """<a href="%s"><i class="icon %s" alt="%s"></i> %s</a>""" % \
                   (remove_url, remove_icon, _("Remove item"), _("Remove item"))
        else:
            remove = ""

        if recid < 0:
            external_item_img = '<img src="%s/img/wb-external-item.png" alt="%s" style="vertical-align: top;" />&nbsp;' % \
                                 (CFG_SITE_URL, _("External item"))
        else:
            external_item_img = ''

        out = """

    <div class="row-fluid">
      <div class="col-md-1 bskcontentcount">
        %(count)i.
      </div>
      <div class="col-md-11 bskcontentcol">
        %(icon)s%(content)s
      </div>
    </div>

    <div class="row-fluid">
      <div class="col-md-1 bskcontentoptions">
        %(moveup)s%(movedown)s
      </div>
      <div class="col-md-4 moreinfo">"""

        if item[0] > 0:
            detailed_record = """<a class="moreinfo" href="%(siteurl)s/%(CFG_SITE_RECORD)s/%(recid)s">%(detailed_record_label)s</a>"""
            out += detailed_record + (view_notes and " - " or "")
            external_url = ""
        else:
            ## Uncomment the following lines if you want the Detailed record link to be
            ## displayed for external records but not for external sources (such as urls)
            #external_colid_and_url = db.get_external_colid_and_url(item[0])
            #if external_colid_and_url and external_colid_and_url[0][0] and external_colid_and_url[0][1]:
            #    detailed_record = '<a class="moreinfo" href="%(external_url)s">%(detailed_record_label)s</a>'
            #    out += detailed_record + (view_notes and " - " or "")
            #    external_url = external_colid_and_url[0][1]
            #else:
            #    external_url = ""
            ## Currently no external items (records or sources) have a Detailed record link
            external_url = ""

        # TODO: If a user has the right to view the notes but not to add new ones,
        # and there are no notes for some item an anchor to write notes will be
        # created but with no text, hence invisible. Fix this so that no anchor
        # is created whatsoever.
        if view_notes:
            notes = """\n<a class="moreinfo" href="%(siteurl)s/yourbaskets/%(add_and_view_notes_action)s?"""\
                    """category=%(category)s&amp;topic=%(topic)s&amp;group=%(group)i&amp;"""\
                    """bskid=%(bskid)s&amp;recid=%(recid)i&amp;ln=%(ln)s%(add_and_view_notes_inline_anchor)s">%(add_and_view_notes_label)s</a>"""
            out += notes

        out += """
      </div>
      <div class="col-md-5 col-md-offset-2 pagination-right bskbasketheaderoptions">
        %(copy)s
        &nbsp;
        %(move)s
        &nbsp;
        %(remove)s
      </div>
    </div>"""

        out = out % {'moveup': moveup,
                     'movedown': movedown,
                     'count': count,
                     'icon': external_item_img,
                     'content': colid >= 0 and val or val and self.tmpl_create_pseudo_item(val) or _("This record does not seem to exist any more"),
                     'add_and_view_notes_action': nb_cmt and 'display' or 'write_note',
                     'add_and_view_notes_inline_anchor': not nb_cmt and '#note' or '',
                     'add_and_view_notes_label': nb_cmt and _('Notes') + ' (' + str(nb_cmt) + ')' or add_notes and _('Add a note...') or '',
                     'last_cmt': last_cmt,
                     'siteurl': CFG_SITE_URL,
                     'CFG_SITE_RECORD': cfg['CFG_SITE_RECORD'],
                     'bskid': bskid,
                     'recid': recid,
                     'external_url': external_url,
                     'detailed_record_label': _("Detailed record"),
                     'category': selected_category,
                     'topic': urllib.quote(selected_topic),
                     'group': selected_group,
                     'copy': copy,
                     'move': move,
                     'remove': remove,
                     'ln': ln}
        return out

    #############################################
    ########## BASKET SINGLE ITEM VIEW ##########
    #############################################

    def tmpl_basket_single_item(self,
                                bskid,
                                name,
                                nb_items,
                                (user_can_view_content,
                                 user_can_view_notes,
                                 user_can_add_notes,
                                 user_can_delete_notes),
                                selected_category=cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE'],
                                selected_topic="",
                                selected_group=0,
                                item=(),
                                comments=(),
                                previous_item_recid=0,
                                next_item_recid=0,
                                item_index=0,
                                optional_params={},
                                of='hb',
                                ln=CFG_SITE_LANG):
        """Template for basket's single item display."""

        if of != 'xm':
            out = """
<table class="bskbasket" width="100%">"""
        else:
            out = ""

        if of != 'xm':
            out += self.tmpl_basket_single_item_header(bskid,
                                                       name,
                                                       nb_items,
                                                       selected_category,
                                                       selected_topic,
                                                       selected_group,
                                                       previous_item_recid,
                                                       next_item_recid,
                                                       item_index,
                                                       ln)

        if of != 'xm':
            out += self.tmpl_basket_single_item_footer(bskid,
                                                       selected_category,
                                                       selected_topic,
                                                       selected_group,
                                                       previous_item_recid,
                                                       next_item_recid,
                                                       ln)

        out += self.tmpl_basket_single_item_content(bskid,
                                                    (user_can_view_content,
                                                     user_can_view_notes,
                                                     user_can_add_notes,
                                                     user_can_delete_notes),
                                                    selected_category,
                                                    selected_topic,
                                                    selected_group,
                                                    item,
                                                    comments,
                                                    item_index,
                                                    optional_params,
                                                    of,
                                                    ln)

        if of != 'xm':
            out += """
</table>"""

        if of != 'xm':
            out += self.tmpl_create_export_as_list(selected_category,
                                                   selected_topic,
                                                   selected_group,
                                                   bskid,
                                                   item,
                                                   False)

        return out

    def tmpl_basket_single_item_header(self,
                                       bskid,
                                       name,
                                       nb_items,
                                       selected_category,
                                       selected_topic,
                                       selected_group,
                                       previous_item_recid,
                                       next_item_recid,
                                       item_index,
                                       ln=CFG_SITE_LANG):
        """Template for basket's single item header display."""

        _ = gettext_set_language(ln)

        records_field = '<br />' + _('Item %(x_item_index)i of %(x_item_total)i') % \
                        {'x_item_index': item_index, 'x_item_total': nb_items}

        if previous_item_recid:
            previous_item_url = """%s/yourbaskets/display?category=%s&amp;topic=%s&amp;group=%i&amp;bskid=%i&amp;recid=%s&amp;ln=%s""" % \
                                (CFG_SITE_URL,
                                 selected_category,
                                 urllib.quote(selected_topic),
                                 selected_group,
                                 bskid,
                                 previous_item_recid,
                                 ln)
            previous_item_logo = """<i class="icon %s"></i> """ % (ICON_PREVIOUS_ITEM,)
            previous_item = """<a href="%s">%s%s</a>""" % (previous_item_url, previous_item_logo, _("Previous item"))
        else:
            previous_item_logo = """<i class="icon %s"></i> """ % (ICON_PREVIOUS_ITEM_MUTED,)
            previous_item = """%s%s""" % (previous_item_logo, _("Previous item"))

        if next_item_recid:
            next_item_url = """%s/yourbaskets/display?category=%s&amp;topic=%s&amp;group=%i&amp;bskid=%i&amp;recid=%s&amp;ln=%s""" % \
                            (CFG_SITE_URL,
                             selected_category,
                             urllib.quote(selected_topic),
                             selected_group,
                             bskid,
                             next_item_recid,
                             ln)
            next_item_logo = """<i class="icon %s"></i> """ % (ICON_NEXT_ITEM,)
            next_item = """<a href="%s">%s%s</a>""" % (next_item_url, next_item_logo, _("Next item"))
        else:
            next_item_logo ="""<i class="icon %s"></i> """ % (ICON_NEXT_ITEM_MUTED,)
            next_item = """%s%s""" % (next_item_logo, _("Next item"))

        go_back_url = """%s/yourbaskets/display?category=%s&amp;topic=%s&amp;group=%i&amp;bskid=%i&amp;ln=%s""" % \
                      (CFG_SITE_URL,
                       selected_category,
                       urllib.quote(selected_topic),
                       selected_group,
                       bskid,
                       ln)
        go_back_logo = """<i class="icon %s"></i> """ % (ICON_BACK,)
        go_back = """<a href="%s">%s%s</a>""" % (go_back_url, go_back_logo, _("Return to basket"))

        out = """
  <thead>
    <tr>
      <td class="bskbasketheader">
        <table>
          <tr>
            <td class="bskbasketheadertitle">
              <strong>
              %(name)s
              </strong>
              <small>
              %(records_field)s
              </small>
            </td>
            <td class="bskbasketheaderoptions">
              %(go_back)s
              &nbsp;&nbsp;
              %(previous_item)s
              &nbsp;&nbsp;
              %(next_item)s
            </td>
        </table>
      </td>
    </tr>
  </thead>"""

        out %= {'name': name,
                'records_field': records_field,
                'go_back': go_back,
                'previous_item': previous_item,
                'next_item': next_item,
        }

        return out

    def tmpl_basket_single_item_footer(self,
                                       bskid,
                                       selected_category,
                                       selected_topic,
                                       selected_group,
                                       previous_item_recid,
                                       next_item_recid,
                                       ln=CFG_SITE_LANG):
        """Template for basket's single item footer display."""

        _ = gettext_set_language(ln)

        if previous_item_recid:
            previous_item_url = """%s/yourbaskets/display?category=%s&amp;topic=%s&amp;group=%i&amp;bskid=%i&amp;recid=%s&amp;ln=%s""" % \
                                (CFG_SITE_URL,
                                 selected_category,
                                 urllib.quote(selected_topic),
                                 selected_group,
                                 bskid,
                                 previous_item_recid,
                                 ln)
            previous_item_logo = """<i class="icon %s"></i> """ % (ICON_PREVIOUS_ITEM,)
            previous_item = """<a href="%s">%s%s</a>""" % (previous_item_url, previous_item_logo, _("Previous item"))
        else:
            previous_item_logo = """<i class="icon %s"></i> """ % (ICON_PREVIOUS_ITEM_MUTED,)
            previous_item = """%s%s""" % (previous_item_logo, _("Previous item"))

        if next_item_recid:
            next_item_url = """%s/yourbaskets/display?category=%s&amp;topic=%s&amp;group=%i&amp;bskid=%i&amp;recid=%s&amp;ln=%s""" % \
                            (CFG_SITE_URL,
                             selected_category,
                             urllib.quote(selected_topic),
                             selected_group,
                             bskid,
                             next_item_recid,
                             ln)
            next_item_logo = """<i class="icon %s"></i> """ % (ICON_NEXT_ITEM,)
            next_item = """<a href="%s">%s%s</a>""" % (next_item_url, next_item_logo, _("Next item"))
        else:
            next_item_logo = """<i class="icon %s"></i> """ % (ICON_NEXT_ITEM_MUTED,)
            next_item = """%s%s""" % (next_item_logo, _("Next item"))

        go_back_url = """%s/yourbaskets/display?category=%s&amp;topic=%s&amp;group=%i&amp;bskid=%i&amp;ln=%s""" % \
                      (CFG_SITE_URL,
                       selected_category,
                       urllib.quote(selected_topic),
                       selected_group,
                       bskid,
                       ln)
        go_back_logo = """<i class="icon %s"></i> """ % (ICON_BACK,)
        go_back = """<a href="%s">%s%s</a>""" % (go_back_url, go_back_logo, _("Return to basket"))

        out = """
  <tfoot>
    <tr>
      <td class="bskbasketfooter">
        <table width="100%%">
          <tr>
            <td class="bskbasketfootertitle">
              &nbsp;
            </td>
            <td class="bskbasketfooteroptions">
              %(go_back)s
              &nbsp;&nbsp;
              %(previous_item)s
              &nbsp;&nbsp;
              %(next_item)s
            </td>
        </table>
      </td>
    </tr>
  </tfoot>"""

        out %= {'go_back': go_back,
                'previous_item': previous_item,
                'next_item': next_item,
        }

        return out

    def tmpl_basket_single_item_content(self,
                                        bskid,
                                        (user_can_view_content,
                                         user_can_view_notes,
                                         user_can_add_notes,
                                         user_can_delete_notes),
                                        selected_category=cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE'],
                                        selected_topic="",
                                        selected_group=0,
                                        item=(),
                                        notes=(),
                                        index_item=0,
                                        optional_params={},
                                        of='hb',
                                        ln=CFG_SITE_LANG):
        """Template for basket's single item content display."""

        if of != 'xm':
            _ = gettext_set_language(ln)

            item_html = """
  <tbody>"""

            if user_can_view_content:
                if not item:
                    item_html += """
    <tr>
      <td style="text-align: center; height: 100px">
        %s
      </td>
    </tr>""" % _("The item you have selected does not exist.")

                else:
                    (recid, colid, dummy, last_cmt, val, dummy) = item

                    if recid < 0:
                        external_item_img = '<img src="%s/img/wb-external-item.png" alt="%s" style="vertical-align: top;" />&nbsp;' % \
                                             (CFG_SITE_URL, _("External item"))
                    else:
                        external_item_img = ''

                    if user_can_view_notes:
                        notes_html = self.__tmpl_display_notes(recid,
                                                               bskid,
                                                               (user_can_add_notes,
                                                                user_can_delete_notes),
                                                               selected_category,
                                                               selected_topic,
                                                               selected_group,
                                                               notes,
                                                               optional_params,
                                                               ln)
                        notes = """
          <tr>
            <td colspan="2" class="bskcontentnotes">%(notes_html)s
            </td>
          </tr>""" % {'notes_html': notes_html}
                    else:
                        notes_msg = _("You do not have sufficient rights to view this item's notes.")
                        notes = """
          <tr>
            <td colspan="2" style="text-align: center; height: 50px">
              %(notes_msg)s
            </td>
          </tr>""" % {'notes_msg': notes_msg}

                    item_html += """
    <tr>
      <td style="border-bottom: 1px solid #fc0;">
        <table>
          <tr>
            <td class="bskcontentcount">
            %(count)i.
            </td>
            <td class="bskcontentcol">
            %(icon)s%(content)s
            </td>
          </tr>%(notes)s
        </table>
      </td>
    </tr>""" % {'count': index_item,
                'icon': external_item_img,
                'content': colid >=0 and val or val and self.tmpl_create_pseudo_item(val) or _("This record does not seem to exist any more"),
                'notes': notes}

            else:
                item_html += """
    <tr>
      <td style="text-align: center; height: 100px">
        %s
      </td>
    </tr>""" % _("You do not have sufficient rights to view this item.")

            item_html += """
  </tbody>"""

            return item_html
        else:
            item_xml = item[4]
            return item_xml

    def __tmpl_display_notes(self,
                             recid,
                             bskid,
                             (user_can_add_notes,
                              user_can_delete_notes),
                             selected_category,
                             selected_topic,
                             selected_group,
                             notes,
                             optional_params,
                             ln=CFG_SITE_LANG):
        """Template for basket's single item notes display."""

        _ = gettext_set_language(ln)

        warnings_html = ""

        add_note_p = False
        if user_can_add_notes and ("Add note" in optional_params or "Incomplete note" in optional_params):
            add_note_p = True
            if "Add note" in optional_params and optional_params['Add note']:
                replied_to_note = optional_params['Add note']
                note_body_html = self.tmpl_quote_comment_html(replied_to_note[2],
                                                              replied_to_note[1],
                                                              replied_to_note[0],
                                                              replied_to_note[4],
                                                              replied_to_note[3],
                                                              ln)
                note_body_textual = self.tmpl_quote_comment_textual(replied_to_note[2],
                                                                    replied_to_note[1],
                                                                    replied_to_note[0],
                                                                    replied_to_note[4],
                                                                    replied_to_note[3],
                                                                    ln)
                note_title = "Re: " + replied_to_note[2]
            elif "Incomplete note" in optional_params and optional_params['Incomplete note']:
                incomplete_note = optional_params['Incomplete note']
                note_body_html = incomplete_note[1]
                # TODO: Do we need to format incomplete body correctly as textual
                # and html as above?
                note_body_textual = incomplete_note[1]
                note_title = incomplete_note[0]
                if "Warnings" in optional_params:
                    warnings = optional_params["Warnings"]
                    warnings_html = self.tmpl_warnings(warnings, ln)
            else:
                note_body_html = ""
                note_body_textual = ""
                note_title = ""
                if "Warnings" in optional_params:
                    warnings = optional_params["Warnings"]
                    warnings_html = self.tmpl_warnings(warnings, ln)
            # TODO: calculate the url
            file_upload_url = ""
            action = """%s/yourbaskets/save_note?category=%s&amp;topic=%s&amp;group=%i&amp;bskid=%i&amp;recid=%i&amp;ln=%s%s""" % \
                     (CFG_SITE_URL, selected_category, urllib.quote(selected_topic), selected_group, bskid, recid, ln, '#note')
            cancel = """%s/yourbaskets/display?category=%s&amp;topic=%s&amp;group=%i&amp;bskid=%i&amp;recid=%i&amp;ln=%s""" % \
                     (CFG_SITE_URL, selected_category, urllib.quote(selected_topic), selected_group, bskid, recid, ln)
            editor = get_html_text_editor(name="note_body",
                                          content=note_body_html,
                                          textual_content=note_body_textual,
                                          width="99%",
                                          height="160px",
                                          enabled=cfg['CFG_WEBBASKET_USE_RICH_TEXT_EDITOR'],
                                          file_upload_url=file_upload_url,
                                          toolbar_set="WebComment")
            add_note_html = """
                    <table cellspacing="0" cellpadding="0" class="bsknotescontentaddnote">
                      <tr>
                        <td class="bsknotescontentaddform">
                          <form name="write_note" method="post" action="%(action)s">
                            <a name="note"></a><strong>%(add_a_note_label)s</strong>
                            %(warnings_html)s
                            <p align="left">
                            <small>Subject:</small>
                            <br />
                            <input type="text" name="note_title" size="65" value="%(note_title)s" />
                            </p>
                            <p align="left">
                            <small>Note:</small>
                            <br />
                            %(editor)s
                            </p>
                            <input type="hidden" name="reply_to" value="%(reply_to)s" />
                            <p align="left">
                            <input type="submit" class="btn btn-primary formbutton" value="%(submit_label)s" />
                            <input type="button" class="btn nonsubmitbutton" value="%(cancel_label)s" onClick="window.location='%(cancel)s'" />
                            </p>
                          </form>
                        </td>
                      </tr>
                    </table>""" % {'action': action,
                                   'warnings_html': warnings_html,
                                   'cancel': cancel,
                                   'cancel_label': _('Cancel'),
                                   'note_title': note_title,
                                   'editor': editor,
                                   'add_a_note_label': _('Add a note'),
                                   'submit_label': _('Add note'),
                                   'reply_to': optional_params.get("Reply to")}

        notes_icon = '<i class="icon %s"></i> &nbsp;' % (ICON_NOTES,)
        #notes_icon = '<img src="%s/img/wb-notes.png" style="vertical-align: top;" />&nbsp;' % (CFG_SITE_URL,)

        if user_can_add_notes and not add_note_p:
            add_note_url = """%s/yourbaskets/write_note?category=%s&amp;topic=%s&amp;group=%i&amp;bskid=%i&amp;recid=%i&amp;ln=%s%s""" % \
                           (CFG_SITE_URL, selected_category, urllib.quote(selected_topic), selected_group, bskid, recid, ln, '#note')
            add_note_logo = """<i class="icon %s"></i> """ % (ICON_ADD_NOTE,)
            add_note = """<a href="%s">%s%s</a>""" % (add_note_url, add_note_logo, _("Add a note"))
        else:
            add_note = ""

        notes_html = """
              <table>
                <tr>
                  <td class="bsknotesheadertitle">
                  <br />
                  <strong>%(notes_icon)s%(notes_label)s</strong>
                  <br />
                  <small>%(nb_notes)i notes in total</small>
                  </td>
                  <td class="bsknotesheaderoptions">
                  %(add_note)s
                  </td>
                </tr>""" % {'notes_label': _('Notes'),
                            'notes_icon': notes_icon,
                            'add_note': (notes and user_can_add_notes and not add_note_p) and add_note or "&nbsp;",
                            'nb_notes': len(notes)}

        if notes or add_note or add_note_p:
            notes_html += """
                <tr>
                  <td colspan="2" class="bsknotescontent">"""
            thread_history = [0]
            for (cmt_uid, cmt_nickname, cmt_title, cmt_body, cmt_date, dummy, cmtid, reply_to) in notes:
                if reply_to not in thread_history:
                    # Going one level down in the thread
                    thread_history.append(reply_to)
                    depth = thread_history.index(reply_to)
                else:
                    depth = thread_history.index(reply_to)
                    thread_history = thread_history[:depth + 1]
                notes_html += '<div style="margin-left:%spx">' % (depth*20)
                if user_can_add_notes:
                    reply_to_note = """<a href="%s/yourbaskets/write_note?category=%s&amp;topic=%s&amp;group=%i&amp;bskid=%i&amp;recid=%i&amp;cmtid=%i&amp;ln=%s%s">%s</a>""" % \
                                    (CFG_SITE_URL, selected_category, urllib.quote(selected_topic), selected_group, bskid, recid, cmtid, ln, '#note', _('Reply'))
                else:
                    reply_to_note = ""
                if user_can_delete_notes:
                    delete_note = """&nbsp;|&nbsp;<a href="%s/yourbaskets/delete_note?category=%s&amp;topic=%s&amp;group=%i&amp;bskid=%i&amp;recid=%i&amp;cmtid=%i&amp;ln=%s">%s</a>""" % \
                                  (CFG_SITE_URL, selected_category, urllib.quote(selected_topic), selected_group, bskid, recid, cmtid, ln, _('Delete'))
                else:
                    delete_note = ""
                notes_html += """
                    <table cellspacing="0" cellpadding="0" class="bsknotescontentnote">
                      <tr>
                        <td class="bsknotescontenttitle">
                        %(inline_anchor)s<img src="%(CFG_SITE_URL)s/img/user-icon-1-24x24.gif" />%(authorship)s
                        </td>
                      </tr>
                      <tr>
                        <td class="bsknotescontentbody">
                        <blockquote>
                        %(body)s
                        </blockquote>
                        </td>
                      </tr>
                      <tr>
                        <td class="bsknotescontentoptions">
                        %(reply_to_note)s%(delete_note)s
                        </td>
                      </tr>
                    </table>
                    <br />""" % {'inline_anchor': (not add_note_p and notes[-1][-1]==cmtid) and '<a name="note"></a>' or '',
                                 'CFG_SITE_URL': CFG_SITE_URL,
                                 'authorship': _("%(x_title)s, by %(x_name)s on %(x_date)s") % \
                                               {'x_title': '<strong>' + (cmt_title and cgi.escape(cmt_title, True) \
                                                                         or _('Note')) + '</strong>',
                                                'x_name': '<a href="%(CFG_SITE_URL)s/yourmessages/write?msg_to=%(user)s">%(user_display)s</a>' % \
                                                          {'CFG_SITE_URL': CFG_SITE_URL,
                                                           'user': cmt_nickname or cmt_uid,
                                                           'user_display': cmt_nickname or get_user_info(cmt_uid)[2]},
                                                'x_date': '<em>' + convert_datetext_to_dategui(cmt_date) + '</em>'},
                                 'body': email_quoted_txt2html(escape_email_quoted_text(cmt_body)),
                                 'reply_to_note': reply_to_note,
                                 'delete_note': delete_note}
                notes_html += '</div>'
            if add_note_p:
                notes_html += add_note_html
            notes_html += """
                  </td>
                </tr>"""

        notes_html += """
                <tr>
                  <td class="bsknotesfootertitle">
                  &nbsp;
                  </td>
                  <td class="bsknotesfooteroptions">
                  %(add_note)s
                  </td>
                </tr>
              </table>""" % {'add_note': (user_can_add_notes and not add_note_p) and add_note or '&nbsp;'}

        return notes_html

    ########################################
    ########## PUBLIC BASKET VIEW ##########
    ########################################

    def tmpl_public_basket(self,
                           bskid,
                           basket_name,
                           date_modification,
                           nb_items,
                           (user_can_view_comments,),
                           nb_comments,
                           items=[],
                           id_owner=0,
                           subscription_status=0,
                           of='hb',
                           ln=CFG_SITE_LANG):
        """Template for public basket display."""

        if of == 'hb':
            out = """
<table class="bskbasket" width="100%">"""
        else:
            out = ""

        if of == 'hb':
            out += self.tmpl_public_basket_header(bskid,
                                                  basket_name,
                                                  nb_items,
                                                  date_modification,
                                                  (user_can_view_comments,),
                                                  nb_comments,
                                                  subscription_status,
                                                  ln)

        if of == 'hb':
            out += self.tmpl_public_basket_footer(bskid,
                                                  nb_items,
                                                  id_owner,
                                                  subscription_status,
                                                  ln)

        out += self.tmpl_public_basket_content(bskid,
                                               (user_can_view_comments,),
                                               items,
                                               of,
                                               ln)

        if of == 'hb':
            out += """
</table>"""

        if of == 'hb':
            out += self.tmpl_create_export_as_list(bskid=bskid,
                                                   item=None,
                                                   public=True)

        return out

    def tmpl_public_basket_header(self,
                                  bskid,
                                  name,
                                  nb_items,
                                  date_modification,
                                  (user_can_view_comments,),
                                  nb_comments,
                                  subscription_status,
                                  ln=CFG_SITE_LANG):
        """Template for public basket header display."""

        _ = gettext_set_language(ln)

        optional_colspan = nb_items and ' colspan="3"' or ''
        records_field = '<br />' + _('%(x_num)i items', x_num=nb_items)
        comments_field = user_can_view_comments and \
                         (nb_comments and ', ' + (_('%(x_notes)i notes', x_notes=nb_comments)) or ', ' + _('no notes yet')) \
                         or ''
        last_update_field = '<br />' + _('last update') + ': ' + date_modification

        if subscription_status:
            subscribe_url = """%s/yourbaskets/subscribe?bskid=%i&amp;ln=%s""" % (CFG_SITE_URL, bskid, ln)
            subscribe_logo = """<i class="icon %s"></i> ;""" % (ICON_SUBSCRIBE,)
            subscribe = """<a href="%s">%s%s</a>""" % (subscribe_url, subscribe_logo, _("Subscribe to basket"))
            unsubscribe_url = """%s/yourbaskets/unsubscribe?bskid=%i&amp;ln=%s""" % (CFG_SITE_URL, bskid, ln)
            unsubscribe_logo = """<i class="icon %s"></i> ;""" % (ICON_UNSUBSCRIBE,)
            unsubscribe = """<a href="%s">%s%s</a>""" % (unsubscribe_url, unsubscribe_logo, _("Unsubscribe from basket"))

        out = """
  <thead>
    <tr>
      <td class="bskbasketheader"%(optional_colspan)s>
        <table width="100%%">
          <tr>
            <td class="bskbasketheadertitle">
              <strong>
              %(name)s
              </strong>
              <small>
              %(records_field)s%(comments_field)s
              %(last_update_field)s
              </small>
            </td>
            <td class="bskbasketheaderoptions">
              %(subscribe_unsubscribe_basket)s
            </td>
        </table>
      </td>
    </tr>
  </thead>"""

        out %= {'optional_colspan': optional_colspan,
                'name': name,
                'nb_items': nb_items,
                'records_field': records_field,
                'comments_field': comments_field,
                'last_update_field': last_update_field,
                'subscribe_unsubscribe_basket': subscription_status > 0 and unsubscribe or subscription_status < 0 and subscribe or not subscription_status and '&nbsp;'}

        return out

    def tmpl_public_basket_footer(self,
                                  bskid,
                                  nb_items,
                                  id_owner,
                                  subscription_status,
                                  ln=CFG_SITE_LANG):
        """Template for public basket footer display."""

        _ = gettext_set_language(ln)

        optional_colspan = nb_items and ' colspan="3"' or ''

        if subscription_status:
            subscribe_url = """%s/yourbaskets/subscribe?bskid=%i&amp;ln=%s""" % (CFG_SITE_URL, bskid, ln)
            subscribe_logo = """<i class="icon %s"></i> ;""" % (ICON_SUBSCRIBE,)
            subscribe = """<a href="%s">%s%s</a>""" % (subscribe_url, subscribe_logo, _("Subscribe to basket"))
            unsubscribe_url = """%s/yourbaskets/unsubscribe?bskid=%i&amp;ln=%s""" % (CFG_SITE_URL, bskid, ln)
            unsubscribe_logo = """<i class="icon %s"></i> ;""" % (ICON_UNSUBSCRIBE,)
            unsubscribe = """<a href="%s">%s%s</a>""" % (unsubscribe_url, unsubscribe_logo, _("Unsubscribe from basket"))
            (uid, nickname, display_name) = get_user_info(id_owner)
            display_owner_url = """%s/yourmessages/write?msg_to=%s""" % (CFG_SITE_URL, nickname or str(uid))
            display_owner_text = _("This public basket belongs to the user ")
            display_owner = """%s<a href="%s">%s</a>.""" % (display_owner_text, display_owner_url, nickname or display_name)

        out = """
  <tfoot>
    <tr>
      <td class="bskbasketfooter"%(optional_colspan)s>
        <table width="100%%">
          <tr>
            <td class="bskbasketfootertitle">
              <small>
              %(display_owner)s
              </small>
            </td>
            <td class="bskbasketfooteroptions">
              %(subscribe_unsubscribe_basket)s
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </tfoot>"""

        out %= {'optional_colspan': optional_colspan,
                'display_owner': subscription_status and display_owner or _('This public basket belongs to you.'),
                'subscribe_unsubscribe_basket': subscription_status > 0 and unsubscribe or subscription_status < 0 and subscribe or not subscription_status and '&nbsp;'}

        return out

    def tmpl_public_basket_content(self,
                                   bskid,
                                   (user_can_view_comments,),
                                   items=[],
                                   of='hb',
                                   ln=CFG_SITE_LANG):
        """Template for public basket footer display."""

        if of == 'hb':
            _ = gettext_set_language(ln)
            items_html = """
  <tbody>"""
            if not(items):
                items_html += """
    <tr>
      <td style="text-align:center; height:100px">
      %s
      </td>
    </tr>""" % _("Basket is empty")
            else:
                count = 0
                for item in items:
                    count += 1
                    items_html += self.__tmpl_public_basket_item(count=count,
                                                                 bskid=bskid,
                                                                 item=item,
                                                                 view_notes=user_can_view_comments,
                                                                 ln=ln)

            items_html += """
  </tbody>"""
            return items_html
        elif of.startswith('x'):
            items_xml = ""
            for item in items:
                items_xml += item[4] + "\n"
            return items_xml
        else:
            return ""

    def __tmpl_public_basket_item(self,
                                  count,
                                  bskid,
                                  item,
                                  view_notes=0,
                                  ln=CFG_SITE_LANG):
        """Template for basket item display within the basket content."""

        _ = gettext_set_language(ln)

        (recid, colid, nb_cmt, last_cmt, val, dummy) = item

        copy_url = "%(siteurl)s/yourbaskets/modify?action=copy&amp;bskid=%(bskid)i&amp;recid=%(recid)i&amp;ln=%(ln)s" % \
                   {'siteurl': CFG_SITE_URL,
                    'bskid': bskid,
                    'recid': recid,
                    'ln': ln}
        copy_icon = ICON_COPY_ITEM
        copy = """<a href="%s"><i class="icon %s"></i> %s</a>""" % \
               (copy_url, copy_icon, _("Copy item"))

        if recid < 0:
            external_item_img = '<img src="%s/img/wb-external-item.png" alt="%s" style="vertical-align: top;" />&nbsp;' % \
                                 (CFG_SITE_URL, _("External item"))
        else:
            external_item_img = ''

        out = """
    <tr>
      <td style="border-bottom: 1px solid #fc0;">
        <table>
          <tr>
            <td class="bskcontentcount">
            %(count)i.
            </td>
            <td class="bskcontentcol" colspan="2">
            %(icon)s%(content)s
            </td>
          </tr>
          <tr>
            <td class="bskcontentoptions">
            &nbsp;
            </td>
            <td>
              <span class="moreinfo">"""

        if item[0] > 0:
            detailed_record = """<a class="moreinfo" href="%(siteurl)s/%(CFG_SITE_RECORD)s/%(recid)s">%(detailed_record_label)s</a>"""
            out += detailed_record + (view_notes and " - " or "")
            external_url = ""
        else:
            ## Uncomment the following lines if you want the Detailed record link to be
            ## displayed for external records but not for external sources (such as urls)
            #external_colid_and_url = db.get_external_colid_and_url(item[0])
            #if external_colid_and_url and external_colid_and_url[0][0] and external_colid_and_url[0][1]:
            #    detailed_record = '<a class="moreinfo" href="%(external_url)s">%(detailed_record_label)s</a>'
            #    out += detailed_record + (view_notes and " - " or "")
            #    external_url = external_colid_and_url[0][1]
            #else:
            #    external_url = ""
            ## Currently no external items (records or sources) have a Detailed record link
            external_url = ""

        if view_notes:
            notes = """\n<a class="moreinfo" href="%(siteurl)s/yourbaskets/%(add_and_view_notes_action)s?"""\
                    """bskid=%(bskid)s&amp;recid=%(recid)i&amp;ln=%(ln)s%(add_and_view_notes_inline_anchor)s">%(add_and_view_notes_label)s</a>"""
            out += notes

        out += """
              </span>
            </td>
            <td class="bskbasketheaderoptions">
            %(copy)s
            </td>
          </tr>
        </table>
      </td>
    </tr>"""
        out = out % {'count': count,
                     'icon': external_item_img,
                     'content': colid >= 0 and val or val and self.tmpl_create_pseudo_item(val) or _("This record does not seem to exist any more"),
                     'add_and_view_notes_action': nb_cmt and 'display_public' or 'write_public_note',
                     'add_and_view_notes_inline_anchor': not nb_cmt and '#note' or '',
                     'add_and_view_notes_label': nb_cmt and _('Notes') + ' (' + str(nb_cmt) + ')' or _('Add a note...'),
                     'last_cmt': last_cmt,
                     'siteurl': CFG_SITE_URL,
                     'CFG_SITE_RECORD': cfg['CFG_SITE_RECORD'],
                     'bskid': bskid,
                     'recid': recid,
                     'external_url': external_url,
                     'detailed_record_label': _("Detailed record"),
                     'copy': copy,
                     'ln': ln}
        return out

    ####################################################
    ########## PUBLIC BASKET SINGLE ITEM VIEW ##########
    ####################################################

    def tmpl_public_basket_single_item(self,
                                       bskid,
                                       name,
                                       nb_items,
                                       (user_can_view_notes,
                                        user_can_add_notes),
                                       item=(),
                                       notes=(),
                                       previous_item_recid=0,
                                       next_item_recid=0,
                                       item_index=0,
                                       optional_params={},
                                       of='hb',
                                       ln=CFG_SITE_LANG):
        """Template for public basket's single item display."""

        _ = gettext_set_language(ln)

        if of == 'hb':
            out = """
<table class="bskbasket" width="100%">"""
        else:
            out = ""

        if of == 'hb':
            out += self.tmpl_public_basket_single_item_header(bskid,
                                                              name,
                                                              nb_items,
                                                              previous_item_recid,
                                                              next_item_recid,
                                                              item_index,
                                                              ln=CFG_SITE_LANG)

        if of == 'hb':
            out += self.tmpl_public_basket_single_item_footer(bskid,
                                                              previous_item_recid,
                                                              next_item_recid,
                                                              ln=CFG_SITE_LANG)

        out += self.tmpl_public_basket_single_item_content(bskid,
                                                           (user_can_view_notes,
                                                            user_can_add_notes),
                                                           item,
                                                           notes,
                                                           item_index,
                                                           optional_params,
                                                           of,
                                                           ln=CFG_SITE_LANG)

        if of == 'hb':
            out += """
</table>"""

        if of == 'hb':
            out += self.tmpl_create_export_as_list(bskid=bskid,
                                                   item=item,
                                                   public=True)

        return out

    def tmpl_public_basket_single_item_header(self,
                                              bskid,
                                              name,
                                              nb_items,
                                              previous_item_recid,
                                              next_item_recid,
                                              item_index,
                                              ln=CFG_SITE_LANG):
        """Template for public basket's single item header display."""

        _ = gettext_set_language(ln)

        records_field = '<br />' + _('Item %(x_item_index)i of %(x_item_total)i') % \
                        {'x_item_index': item_index, 'x_item_total': nb_items}

        if previous_item_recid:
            previous_item_url = """%s/yourbaskets/display_public?bskid=%i&amp;recid=%s&amp;ln=%s""" % \
                                (CFG_SITE_URL,
                                 bskid,
                                 previous_item_recid,
                                 ln)
            previous_item_logo = """<i class="icon %s"></i> """ % (ICON_PREVIOUS_ITEM,)
            previous_item = """<a href="%s">%s%s</a>""" % (previous_item_url, previous_item_logo, _("Previous item"))
        else:
            previous_item_logo = """<i class="icon %s"></i> """ % (ICON_PREVIOUS_ITEM_MUTED,)
            previous_item = """%s%s""" % (previous_item_logo, _("Previous item"))

        if next_item_recid:
            next_item_url = """%s/yourbaskets/display_public?bskid=%i&amp;recid=%s&amp;ln=%s""" % \
                            (CFG_SITE_URL,
                             bskid,
                             next_item_recid,
                             ln)
            next_item_logo = """<i class="icon %s"></i> """ % (ICON_NEXT_ITEM,)
            next_item = """<a href="%s">%s%s</a>""" % (next_item_url, next_item_logo, _("Next item"))
        else:
            next_item_logo = """<i class="icon %s"></i> """ % (ICON_NEXT_ITEM_MUTED,)
            next_item = """%s%s""" % (next_item_logo, _("Next item"))

        go_back_url = """%s/yourbaskets/display_public?bskid=%i&amp;ln=%s""" % \
                      (CFG_SITE_URL,
                       bskid,
                       ln)
        go_back_logo = """<i class="icon %s"></i> """ % (ICON_BACK,)
        go_back = """<a href="%s">%s%s</a>""" % (go_back_url, go_back_logo, _("Return to basket"))

        out = """
  <thead>
    <tr>
      <td class="bskbasketheader">
        <table>
          <tr>
            <td class="bskbasketheadertitle">
              <strong>
              %(name)s
              </strong>
              <small>
              %(records_field)s
              </small>
            </td>
            <td class="bskbasketheaderoptions">
              %(go_back)s
              &nbsp;&nbsp;
              %(previous_item)s
              &nbsp;&nbsp;
              %(next_item)s
            </td>
        </table>
      </td>
    </tr>
  </thead>"""

        out %= {'name': name,
                'records_field': records_field,
                'go_back': go_back,
                'previous_item': previous_item,
                'next_item': next_item,
        }

        return out

    def tmpl_public_basket_single_item_footer(self,
                                              bskid,
                                              previous_item_recid,
                                              next_item_recid,
                                              ln=CFG_SITE_LANG):
        """Template for public basket's single item footer display."""

        _ = gettext_set_language(ln)

        if previous_item_recid:
            previous_item_url = """%s/yourbaskets/display_public?bskid=%i&amp;recid=%s&amp;ln=%s""" % \
                                (CFG_SITE_URL,
                                 bskid,
                                 previous_item_recid,
                                 ln)
            previous_item_logo = """<i class="icon %s"></i> """ % (ICON_PREVIOUS_ITEM,)
            previous_item = """<a href="%s">%s%s</a>""" % (previous_item_url, previous_item_logo, _("Previous item"))
        else:
            previous_item_logo = """<i class="icon %s"></i> """ % (ICON_PREVIOUS_ITEM_MUTED,)
            previous_item = """%s%s""" % (previous_item_logo, _("Previous item"))

        if next_item_recid:
            next_item_url = """%s/yourbaskets/display_public?bskid=%i&amp;recid=%s&amp;ln=%s""" % \
                            (CFG_SITE_URL,
                             bskid,
                             next_item_recid,
                             ln)
            next_item_logo = """<i class="icon %s"></i> """ % (ICON_NEXT_ITEM,)
            next_item = """<a href="%s">%s%s</a>""" % (next_item_url, next_item_logo, _("Next item"))
        else:
            next_item_logo = """<i class="icon %s"></i> """ % (ICON_NEXT_ITEM_MUTED,)
            next_item = """%s%s""" % (next_item_logo, _("Next item"))

        go_back_url = """%s/yourbaskets/display_public?bskid=%i&amp;ln=%s""" % \
                      (CFG_SITE_URL,
                       bskid,
                       ln)
        go_back_logo = """<i class="icon %s"></i> """ % (ICON_BACK,)
        go_back = """<a href="%s">%s%s</a>""" % (go_back_url, go_back_logo, _("Return to basket"))

        out = """
  <tfoot>
    <tr>
      <td class="bskbasketfooter">
        <table width="100%%">
          <tr>
            <td class="bskbasketfootertitle">
              &nbsp;
            </td>
            <td class="bskbasketfooteroptions">
              %(go_back)s
              &nbsp;&nbsp;
              %(previous_item)s
              &nbsp;&nbsp;
              %(next_item)s
            </td>
        </table>
      </td>
    </tr>
  </tfoot>"""

        out %= {'go_back': go_back,
                'previous_item': previous_item,
                'next_item': next_item,
        }

        return out

    def tmpl_public_basket_single_item_content(self,
                                               bskid,
                                               (user_can_view_notes,
                                                user_can_add_notes),
                                               item=(),
                                               notes=(),
                                               index_item=0,
                                               optional_params={},
                                               of='hb',
                                               ln=CFG_SITE_LANG):
        """Template for public basket's single item content display."""

        if of == 'hb':
            _ = gettext_set_language(ln)

            item_html = """
  <tbody>"""

            if not item:
                item_html += """
    <tr>
      <td style="text-align: center; height: 100px">
        %s
      </td>
    </tr>""" % _("The item you have selected does not exist.")

            else:
                (recid, colid, dummy, dummy, val, dummy) = item

                if recid < 0:
                    external_item_img = '<img src="%s/img/wb-external-item.png" alt="%s" style="vertical-align: top;" />&nbsp;' % \
                                        (CFG_SITE_URL, _("External item"))
                else:
                    external_item_img = ''

                if user_can_view_notes:
                    notes_html = self.__tmpl_display_public_notes(recid,
                                                                  bskid,
                                                                  (user_can_add_notes,),
                                                                  notes,
                                                                  optional_params,
                                                                  ln)
                    notes = """
          <tr>
            <td colspan="2" class="bskcontentnotes">%(notes_html)s
            </td>
          </tr>""" % {'notes_html': notes_html}
                else:
                    notes_msg = _("You do not have sufficient rights to view this item's notes.")
                    notes = """
          <tr>
            <td colspan="2" style="text-align: center; height: 50px">
              %(notes_msg)s
            </td>
          </tr>""" % {'notes_msg': notes_msg}

                item_html += """
    <tr>
      <td style="border-bottom: 1px solid #fc0;">
        <table>
          <tr>
            <td class="bskcontentcount">
            %(count)i.
            </td>
            <td class="bskcontentcol">
            %(icon)s%(content)s
            </td>
          </tr>%(notes)s
        </table>
      </td>
    </tr>""" % {'count': index_item,
                'icon': external_item_img,
                'content': colid >= 0 and val or val and self.tmpl_create_pseudo_item(val) or _("This record does not seem to exist any more"),
                'notes': notes,
                'ln': ln}

            item_html += """
  </tbody>"""

            return item_html

        elif of == 'xm':
            item_xml = item[4]
            return item_xml

    def __tmpl_display_public_notes(self,
                                    recid,
                                    bskid,
                                    (user_can_add_notes,),
                                    notes,
                                    optional_params,
                                    ln=CFG_SITE_LANG):
        """Template for public basket's single item notes display."""

        _ = gettext_set_language(ln)

        warnings_html = ""

        add_note_p = False
        if user_can_add_notes and ("Add note" in optional_params or "Incomplete note" in optional_params):
            add_note_p = True
            if "Add note" in optional_params and optional_params['Add note']:
                replied_to_note = optional_params['Add note']
                note_body_html = self.tmpl_quote_comment_html(replied_to_note[2],
                                                              replied_to_note[1],
                                                              replied_to_note[0],
                                                              replied_to_note[4],
                                                              replied_to_note[3],
                                                              ln)
                note_body_textual = self.tmpl_quote_comment_textual(replied_to_note[2],
                                                                    replied_to_note[1],
                                                                    replied_to_note[0],
                                                                    replied_to_note[4],
                                                                    replied_to_note[3],
                                                                    ln)
                note_title = "Re: " + replied_to_note[2]
            elif "Incomplete note" in optional_params and optional_params['Incomplete note']:
                incomplete_note = optional_params['Incomplete note']
                note_body_html = incomplete_note[1]
                # TODO: Do we need to format incomplete body correctly as textual
                # and html as above?
                note_body_textual = incomplete_note[1]
                note_title = incomplete_note[0]
                if "Warnings" in optional_params:
                    warnings = optional_params["Warnings"]
                    warnings_html = self.tmpl_warnings(warnings, ln)
            else:
                note_body_html = ""
                note_body_textual = ""
                note_title = ""
                if "Warnings" in optional_params:
                    warnings = optional_params["Warnings"]
                    warnings_html = self.tmpl_warnings(warnings, ln)
            # TODO: calculate the url
            file_upload_url = ""
            action = """%s/yourbaskets/save_public_note?bskid=%i&amp;recid=%i&amp;ln=%s%s""" % \
                     (CFG_SITE_URL, bskid, recid, ln, '#note')
            cancel = """%s/yourbaskets/display_public?bskid=%i&amp;recid=%i&amp;ln=%s""" % \
                     (CFG_SITE_URL, bskid, recid, ln)
            editor = get_html_text_editor(name="note_body",
                                          content=note_body_html,
                                          textual_content=note_body_textual,
                                          width="100%",
                                          height="200px",
                                          enabled=cfg['CFG_WEBBASKET_USE_RICH_TEXT_EDITOR'],
                                          file_upload_url=file_upload_url,
                                          toolbar_set="WebComment")
            add_note_html = """
                    <table cellspacing="0" cellpadding="0" class="bsknotescontentaddnote">
                      <tr>
                        <td class="bsknotescontentaddform">
                          <form name="write_note" method="post" action="%(action)s">
                            <a name="note"></a><strong>%(add_a_note_label)s</strong>
                            %(warnings_html)s
                            <p align="left">
                            <small>Subject:</small>
                            <br />
                            <input type="text" name="note_title" size="65" value="%(note_title)s" />
                            </p>
                            <p align="left">
                            <small>Note:</small>
                            <br />
                            %(editor)s
                            </p>
                            <input type="hidden" name="reply_to" value="%(reply_to)s" />
                            <p align="right">
                            <input type="submit" class="btn btn-primary formbutton" value="%(submit_label)s" />
                            <input type="button" class="btn nonsubmitbutton" value="%(cancel_label)s" onClick="window.location='%(cancel)s'" />
                            </p>
                          </form>
                        </td>
                      </tr>
                    </table>""" % {'action': action,
                                   'warnings_html': warnings_html,
                                   'cancel': cancel,
                                   'cancel_label': _('Cancel'),
                                   'note_title': note_title,
                                   'editor': editor,
                                   'add_a_note_label': _('Add a note'),
                                   'submit_label': _('Add note'),
                                   'reply_to': optional_params.get("Reply to")}

        notes_icon = '<i class="icon %s"></i> &nbsp;' % (ICON_NOTES,)
        #notes_icon = '<img src="%s/img/wb-notes.png" style="vertical-align: top;" />' % (CFG_SITE_URL,)

        if user_can_add_notes and not add_note_p:
            add_note_url = """%s/yourbaskets/write_public_note?bskid=%i&amp;recid=%i&amp;ln=%s%s""" % \
                           (CFG_SITE_URL, bskid, recid, ln, '#note')
            add_note_logo = """<i class="icon %s"></i> """ % (ICON_ADD_NOTE,)
            add_note = """<a href="%s">%s%s</a>""" % (add_note_url, add_note_logo, _("Add a note"))
        else:
            add_note = ""

        notes_html = """
              <table>
                <tr>
                  <td class="bsknotesheadertitle">
                  <br />
                  <strong>%(notes_icon)s%(notes_label)s</strong>
                  <br />
                  <small>%(nb_notes)i notes in total</small>
                  </td>
                  <td class="bsknotesheaderoptions">
                  %(add_note)s
                  </td>
                </tr>""" % {'notes_label': _('Notes'),
                            'notes_icon': notes_icon,
                            'add_note': (notes and user_can_add_notes and not add_note_p) and add_note or "&nbsp;",
                            'nb_notes': len(notes)}

        if notes or add_note or add_note_p:
            notes_html += """
                <tr>
                  <td colspan="2" class="bsknotescontent">"""
            thread_history = [0]
            for (cmt_uid, cmt_nickname, cmt_title, cmt_body, cmt_date, dummy, cmtid, reply_to) in notes:
                if reply_to not in thread_history:
                    # Going one level down in the thread
                    thread_history.append(reply_to)
                    depth = thread_history.index(reply_to)
                else:
                    depth = thread_history.index(reply_to)
                    thread_history = thread_history[:depth + 1]
                notes_html += '<div style="margin-left:%spx">' % (depth*20)
                if user_can_add_notes:
                    reply_to_note = """<a href="%s/yourbaskets/write_public_note?bskid=%i&amp;recid=%i&amp;cmtid=%i&amp;ln=%s%s">%s</a>""" % \
                                    (CFG_SITE_URL, bskid, recid, cmtid, ln, '#note', _('Reply'))
                else:
                    reply_to_note = ""
                notes_html += """
                    <table cellspacing="0" cellpadding="0" class="bsknotescontentnote">
                      <tr>
                        <td class="bsknotescontenttitle">
                        %(inline_anchor)s<img src="%(CFG_SITE_URL)s/img/user-icon-1-24x24.gif" />%(authorship)s
                        </td>
                      </tr>
                      <tr>
                        <td class="bsknotescontentbody">
                        <blockquote>
                        %(body)s
                        </blockquote>
                        </td>
                      </tr>
                      <tr>
                        <td class="bsknotescontentoptions">
                        %(reply_to_note)s
                        </td>
                      </tr>
                    </table>
                    <br />""" % {'inline_anchor': (not add_note_p and notes[-1][-1]==cmtid) and '<a name="note"></a>' or '',
                                 'CFG_SITE_URL': CFG_SITE_URL,
                                 'authorship': _("%(x_title)s, by %(x_name)s on %(x_date)s") % \
                                               {'x_title': '<strong>' + (cmt_title and cgi.escape(cmt_title, True) \
                                                                         or _('Note')) + '</strong>',
                                                'x_name': '<a href="%(CFG_SITE_URL)s/yourmessages/write?msg_to=%(user)s">%(user_display)s</a>' % \
                                                          {'CFG_SITE_URL': CFG_SITE_URL,
                                                           'user': cmt_nickname or cmt_uid,
                                                           'user_display': cmt_nickname or get_user_info(cmt_uid)[2]},
                                                'x_date': '<em>' + convert_datetext_to_dategui(cmt_date) + '</em>'},

                                 'body': email_quoted_txt2html(escape_email_quoted_text(cmt_body)),
                                 'reply_to_note': reply_to_note}
                notes_html += '</div>'
            if add_note_p:
                notes_html += add_note_html
            notes_html += """
                  </td>
                </tr>"""

        notes_html += """
                <tr>
                  <td class="bsknotesfootertitle">
                  &nbsp;
                  </td>
                  <td class="bsknotesfooteroptions">
                  %(add_note)s
                  </td>
                </tr>
              </table>""" % {'add_note': (user_can_add_notes and not add_note_p) and add_note or '&nbsp;'}

        return notes_html

    def tmpl_create_pseudo_item(self, item, of='hb'):
        """"""

        if not item:
            # normally this function should never be run if "item"
            # is empty or does not exist anyway.
            return ""

        if of == 'hb':
            (es_title, es_desc, es_url) = tuple(item.split('\n'))
            es_title = cgi.escape(es_title, True)
            es_desc = cgi.escape(es_desc.replace('<br />', '\n'), True).replace('\n', '<br />')
            es_url_label = cgi.escape(prettify_url(es_url))
            es_url = cgi.escape(es_url, True)
            out = """<strong>%s</strong>
<br />
<small>%s
<br />
<strong>URL:</strong> <a class="note" target="_blank" href="%s">%s</a>
</small>
""" % (es_title, es_desc, es_url, es_url_label)

        if of == 'xm':
            # TODO: xml output...
            out = ""

        return out

    def tmpl_export_xml(self, body):
        """Template for the xml represantation for the selected basket/items."""

        out = """
<collection xmlns="http://www.loc.gov/MARC21/slim">
%s
</collection>""" % (body,)

        return out

    def tmpl_create_export_as_list(self,
                                   selected_category=cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE'],
                                   selected_topic="",
                                   selected_group=0,
                                   bskid=0,
                                   item=(),
                                   public=False):
        """Tamplate that creates a bullet list of export as formats for a basket or an item."""

        list_of_export_as_formats = [('BibTeX','hx'),
                                     ('DC','xd'),
                                     ('EndNote','xe'),
                                     ('MARCXML', 'xm'),
                                     ('NLM','xn'),
                                     ('RefWorks','xw'),
                                     ('RSS','xr')]

        recid = item and "&amp;recid=" + str(item[0]) or ""

        if not public:
            href = "%s/yourbaskets/display?category=%s&amp;topic=%s&amp;group=%i&amp;bskid=%i%s" % \
                   (CFG_SITE_URL,
                    selected_category,
                    urllib.quote(selected_topic),
                    selected_group,
                    bskid,
                    recid)
        else:
            href = "%s/yourbaskets/display_public?bskid=%i%s" % \
                   (CFG_SITE_URL,
                    bskid,
                    recid)

        export_as_html = ""
        for format in list_of_export_as_formats:
            export_as_html += """<a style="text-decoration:underline;font-weight:normal" href="%s&amp;of=%s">%s</a>, """ % \
                              (href, format[1], format[0])
        if export_as_html:
            export_as_html = export_as_html[:-2]
        out = """
<div style="float:right; text-align:right;">
  <ul class="bsk_export_as_list">
    <li>Export as
      %s
    </li>
  </ul>
</div>""" % (export_as_html,)

        return out

#############################################
########## SUPPLEMENTARY FUNCTIONS ##########
#############################################

def prettify_name(name, char_limit=10, nb_dots=3):
    """If name has more characters than char_limit return a shortened version of it
    keeping the beginning (up to char_limit) and replacing the rest with dots."""

    name = unicode(name, 'utf-8')
    if len(name) > char_limit:
        while name[char_limit-1] == ' ':
            char_limit -= 1
        prettified_name = name[:char_limit] + '.'*nb_dots
        return prettified_name.encode('utf-8')
    else:
        return name.encode('utf-8')

def prettify_url(url, char_limit=50, nb_dots=3):
    """If the url has more characters than char_limit return a shortened version of it
    keeping the beginning and ending and replacing the rest with dots."""

    if len(url) > char_limit:
        # let's set a minimum character limit
        if char_limit < 5:
            char_limit = 5
        # let's set a maximum number of dots in relation to the character limit
        if nb_dots > char_limit/4:
            nb_dots = char_limit/5
        nb_char_url = char_limit - nb_dots
        nb_char_end = nb_char_url/4
        nb_char_beg = nb_char_url - nb_char_end
        return url[:nb_char_beg] + '.'*nb_dots + url[-nb_char_end:]
    else:
        return url

def create_search_box_select_options(category,
                                     topic,
                                     grpid,
                                     topic_list,
                                     group_list,
                                     number_of_public_baskets,
                                     ln):
    """Returns an html list of options for the select form field of the search box."""

    _ = gettext_set_language(ln)

    out = ""

    if category:
        if topic:
            b = cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE'] + '_' + cgi.escape(topic, True)
        elif grpid:
            b = cfg['CFG_WEBBASKET_CATEGORIES']['GROUP'] + '_' + str(grpid)
        else:
            b = category
    else:
        b = ""

    if topic_list or group_list:
        out += """<option value=""%(selected)s>%(label)s</option>""" % \
               {'selected': not b and ' selected="selected"' or '',
                'label': _("All your baskets")}
    if topic_list:
        out += """<optgroup label="%(label)s">""" % \
               {'label': _("Your personal baskets")}
        if len(topic_list) > 1:
            out += """<option value="%(value)s"%(selected)s>%(label)s</option>""" % \
                   {'value': cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE'],
                    'selected': b == cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE'] and ' selected="selected"' or '',
                    'label': _("All your topics")}
        for topic_name in topic_list:
            topic_label = cgi.escape(topic_name[0], True)
            topic_value = "P_%s" % (topic_label,)
            out += """<option value="%(value)s"%(selected)s>%(label)s</option>""" % \
                   {'value': topic_value,
                    'selected': b == topic_value and ' selected="selected"' or '',
                    'label': topic_label}
        out += "</optgroup>"
    if group_list:
        out += """<optgroup label="%(label)s">""" % \
               {'label': _("Your group baskets")}
        if len(group_list) > 1:
            out += """<option value="%(value)s"%(selected)s>%(label)s</option>""" % \
                   {'value': cfg['CFG_WEBBASKET_CATEGORIES']['GROUP'],
                    'selected': b == cfg['CFG_WEBBASKET_CATEGORIES']['GROUP'] and ' selected="selected"' or '',
                    'label': _("All your groups")}
        for group_id_and_name in group_list:
            group_label = cgi.escape(group_id_and_name[1], True)
            group_value = "G_%i" % (group_id_and_name[0],)
            out += """<option value="%(value)s"%(selected)s>%(label)s</option>""" % \
                   {'value': group_value,
                    'selected': b == group_value and ' selected="selected"' or '',
                    'label': group_label}
        out += "</optgroup>"
    if number_of_public_baskets:
        out += """<optgroup label="%(label)s">""" % \
               {'label': _("Your public baskets")}
        out += """<option value="%(value)s"%(selected)s>%(label)s</option>""" % \
               {'value': cfg['CFG_WEBBASKET_CATEGORIES']['EXTERNAL'],
                'selected': b == cfg['CFG_WEBBASKET_CATEGORIES']['EXTERNAL'] and ' selected="selected"' or '',
                'label': _("All your public baskets")}
        out += "</optgroup>"
    out += """<option value="%(value)s"%(selected)s>%(label)s</option>""" % \
           {'value': cfg['CFG_WEBBASKET_CATEGORIES']['ALLPUBLIC'],
            'selected': b == cfg['CFG_WEBBASKET_CATEGORIES']['ALLPUBLIC'] and ' selected="selected"' or '',
            'label': _("All the public baskets")}

    return out

def create_add_box_select_options(category,
                                  bskid,
                                  personal_basket_list,
                                  group_basket_list,
                                  ln):
    """Returns an html list of options for the select form field of the add box."""

    _ = gettext_set_language(ln)

    out = ""

    # Calculate the selected basket if there is one pre-selected.
    if category and bskid:
        if category == cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE']:
            b = cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE'] + '_' + str(bskid)
        elif category == cfg['CFG_WEBBASKET_CATEGORIES']['GROUP']:
            b = cfg['CFG_WEBBASKET_CATEGORIES']['GROUP'] + '_' + str(bskid)
        elif category == cfg['CFG_WEBBASKET_CATEGORIES']['EXTERNAL']:
            b = cfg['CFG_WEBBASKET_CATEGORIES']['EXTERNAL'] + '_' + str(bskid)
        else:
            b = ""
    else:
        b = ""

    # Create the default disabled label option.
    out += """
            <option disabled="disabled" value="%(value)i"%(selected)s>%(label)s</option>""" % \
                             {'value': -1,
                              'selected': not b and ' selected="selected"' or '',
                              'label': _('Please select a basket...')}

    # Check if there is only one basket to select from. If that is the case,
    # set the selected basket to its value so that it will automatically be
    # pre-selected. We want to make it easier for the user if they only have
    # one basket.
    if not (personal_basket_list and group_basket_list):
        if len(personal_basket_list) == 1:
            bskids = personal_basket_list[0][1].split(',')
            if len(bskids) == 1:
               b = cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE'] + '_' + bskids[0]
        elif len(group_basket_list) == 1:
            bskids = group_basket_list[0][1].split(',')
            if len(bskids) == 1:
               b = cfg['CFG_WEBBASKET_CATEGORIES']['GROUP'] + '_' + bskids[0]

    # Create the <optgroup>s and <option>s for the user personal baskets.
    if personal_basket_list:
        out += """
            <optgroup label="%s">""" % ('* ' + _('Your personal baskets') + ' *',)
        for personal_basket_list_topic_and_bskids in personal_basket_list:
            topic = personal_basket_list_topic_and_bskids[0]
            bskids = personal_basket_list_topic_and_bskids[1].split(',')
            out += """
              <optgroup label="%s">""" % (cgi.escape(topic, True),)
            bskids_and_names = get_basket_ids_and_names(bskids)
            for bskid_and_name in bskids_and_names:
                basket_value = cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE'] + '_' + str(bskid_and_name[0])
                basket_name = bskid_and_name[1]
                out += """
                <option value="%(value)s"%(selected)s>%(label)s</option>""" % \
                              {'value': basket_value,
                               'selected': basket_value == b and ' selected="selected"' or '',
                               'label': cgi.escape(basket_name, True)}
            out += """
              </optgroup>"""
        out += """
            </optgroup>"""

    # Create the <optgroup>s and <option>s for the user group baskets.
    if group_basket_list:
        out += """
            <optgroup label="%s">""" % ('* ' + _('Your group baskets') + ' *',)
        for group_basket_list_topic_and_bskids in group_basket_list:
            group = group_basket_list_topic_and_bskids[0]
            bskids = group_basket_list_topic_and_bskids[1].split(',')
            out += """
              <optgroup label="%s">""" % (cgi.escape(group, True),)
            bskids_and_names = get_basket_ids_and_names(bskids)
            for bskid_and_name in bskids_and_names:
                basket_value = cfg['CFG_WEBBASKET_CATEGORIES']['GROUP'] + '_' + str(bskid_and_name[0])
                basket_name = bskid_and_name[1]
                out += """
                <option value="%(value)s"%(selected)s>%(label)s</option>""" % \
                              {'value': basket_value,
                               'selected': basket_value == b and ' selected="selected"' or '',
                               'label': cgi.escape(basket_name, True)}
            out += """
              </optgroup>"""
        out += """
            </optgroup>"""

    return out
