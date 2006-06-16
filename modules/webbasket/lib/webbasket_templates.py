## $Id$

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
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

from invenio.messages import gettext_set_language
from invenio.webbasket_config import cfg_webbasket_categories, \
                                     cfg_webbasket_share_levels, \
                                     cfg_webbasket_max_number_of_displayed_baskets
from invenio.webmessage_mailutils import email_quoted_txt2html, email_quote_txt
from invenio.config import weburl, sweburl, cdslang
from invenio.textutils import indent_text
from invenio.webuser import get_user_info
from invenio.dateutils import convert_datetext_to_dategui

class Template:
    
    ######################## General interface ###############################

    def tmpl_display(self,
                     topicsbox='',
                     baskets_infobox='',
                     baskets=[],
                     selected_category=cfg_webbasket_categories['PRIVATE'],
                     nb_groups=0,
                     nb_external_baskets=0,
                     ln=cdslang):
        """Generic display. takes already formatted baskets (list of formatted baskets), infobox and topicsbox, 
        add tabs and returns complete interface"""
        _ = gettext_set_language(ln)
        if type(baskets) not in (list, tuple):
            baskets = [baskets]
        tabs = self.__create_tabs(selected_category, nb_groups, nb_external_baskets, ln)
        
        out = """
<div id="bskcontainer">
  <div id="bsktabs">%s
  </div>
  <div id="bskcontent">""" % indent_text(tabs, 2)
        if topicsbox:
            out += indent_text(topicsbox, 6)
        out += """
    <div id="bskbaskets">"""
        if baskets_infobox:
            out += """
      <div id="bskinfos">%s
      </div>""" % indent_text(baskets_infobox, 5)
        for basket in baskets:
            out += indent_text(basket, 4)
        out += """
    </div>
  </div>
</div>"""
        return out
    
    def __create_tabs(self,
                      selected_category=cfg_webbasket_categories['PRIVATE'],
                      nb_groups=0,
                      nb_external_baskets=0,
                      ln=cdslang):
        """private function, display tabs (private baskets, group baskets, others' basket)."""
        _ = gettext_set_language(ln)
        selected = ' id="bsktab_selected"'
        private = cfg_webbasket_categories['PRIVATE']
        group = cfg_webbasket_categories['GROUP']
        external = cfg_webbasket_categories['EXTERNAL']
        tab = """
<div class="bsktab"%(selected)s>
  <img src="%(url)s/img/%(img)s" alt="%(label)s" />
  <a href="%(url)s/yourbaskets/display?category=%(cat)s&amp;ln=%(ln)s">%(label)s</a>
</div>"""
        out = tab % {'selected': selected_category == private and selected or '',
                     'url': weburl,
                     'img': 'webbasket_us.png',
                     'label': _("Personal baskets"),
                     'cat': private,
                     'ln': ln}
        if nb_groups:
            out += tab % {'selected': selected_category == group and selected or '',
                          'url': weburl,
                          'img': 'webbasket_ugs.png',
                          'label': _("Group baskets"),
                          'cat': group,
                          'ln': ln}
        if nb_external_baskets:            
            out += tab % {'selected': selected_category == external and selected or '',
                          'url': weburl,
                          'img': 'webbasket_ws.png',
                          'label': _("Others' baskets"),
                          'cat': external,
                          'ln': ln}
        return out

    def tmpl_topic_selection(self,
                             topics_list=[],
                             selected_topic=0,
                             ln=cdslang):
        """Display the topics selection area.
        @param topics_list: list of (topic name, number of baskets) tuples
        @param selected_topic: # of selected topic in topics_list"""
        category = cfg_webbasket_categories['PRIVATE']
        if len(topics_list):
            selected_topic = selected_topic <= len(topics_list) and selected_topic or 0
            i = 0
            out = ''
            for (topic, number_of_baskets) in topics_list:
                out += '<span class="bsktopic">'
                topic_label = topic + ' (' + str(number_of_baskets) + ')'
                if i != selected_topic:
                    topic_link = '%s/yourbaskets/display?category=%s&amp;topic=%i&amp;ln=%s'
                    topic_link %= (weburl, category, i, ln)
                    out += '<a href="%s">' % topic_link
                    out += topic_label + '</a>'
                else:
                    out += topic_label
                out += '</span> '    
                i += 1
            out = """
<table id="bsktopics">
  <tr>
    <td>%s
    </td>
  </tr>
</table>""" % out
        else:
            out = self.tmpl_create_basket(ln=cdslang)
            
        return out

    def tmpl_group_selection(self,
                             groups_list=[],
                             selected_group_id=0,
                             ln=cdslang):
        """Display the group selection area which appears on the top of group baskets category.
        @param groups_list: list of (group id, group name, number of baskets) tuples
        @param selected_group id: id of group selected"""
        out = ''
        category = cfg_webbasket_categories['GROUP']
        if len(groups_list): 
            for (group_id, group_name, number_of_baskets) in groups_list:
                out += '<span class="bsktopic">'
                group_label = group_name + ' (' + str(number_of_baskets) + ')'
                if group_id != selected_group_id:
                    group_link = '%s/yourbaskets/display?category=%s&amp;group=%i&amp;ln=%s'
                    group_link %= (weburl, category, group_id, ln)
                    out += '<a href="%s">' % group_link
                    out += group_label + '</a>'
                else:
                    out += group_label
            out += '</span>'
            out = """
<table id="bsktopics">
  <tr>
    <td>%s
    </td>
  </tr>
</table>""" % out
        return out

    def tmpl_baskets_infobox(self, basket_infos=[], create_link='', ln=cdslang):
        """
        displays infos about baskets.
        @param basket_infos: list of (bskid, bsk_name, bsk_last_update) tuples
        @param create_link: link for the creation of basket (will appear next to descriptions)
        @param ln: language
        @return html as string
        """
        _ = gettext_set_language(ln)
        label = _("There are %i baskets") % len(basket_infos)
        basket_list = ''
        if len(basket_infos):
            basket_list += '<ul>\n'
            for (bskid, name, last_update) in basket_infos:
                last_update = convert_datetext_to_dategui(last_update)
                basket_list += '<li><a href="#bsk%i">%s</a> - ' % (bskid, name)
                basket_list += _("updated on") + ' ' + last_update + '</li>\n'
            basket_list += '</ul>'
        if len(basket_infos) < 2:
            label = ''
            basket_list = ''
        out = """
<table style="vertical-align: top;">
  <tr>
    <td style="vertical-align: top">%s</td>
    <td>%s</td>
    <td style="vertical-align: top; padding-left: 80px; text-align: right">%s</td>
  </tr>
</table>""" % (label, basket_list, create_link)
        return out
        
    def tmpl_display_public(self,
                             (bskid, bsk_name,          
                             bsk_date_modification,bsk_nb_views, 
                             bskid_owner, bsk_owner_nickname, bsk_share_level),
                             bsk_items=[],
                             ln=cdslang):
        """
        Display public basketwith link to subscribe to it.
        @param bsk_share_level is not currently used.  
        """
        _ = gettext_set_language(ln)
        items_html = ''
        if not(len(bsk_items)):
            items_html = """
<tr>
  <td colspan="3" style="text-align:center; height:100px">
    %s
  </td>
</tr>""" % _("Basket is empty")
        for item in bsk_items:
            items_html += self.__tmpl_basket_item(bskid=bskid, item=item, ln=ln)
        
        if bsk_owner_nickname:
            display = bsk_owner_nickname
        else:
            (bskid_owner, bsk_owner_nickname, display) = get_user_info(int(bskid_owner))
        messaging_link = self.__create_messaging_link(bsk_owner_nickname, display, ln)
        link_subscribe = '<a href="%s/yourbaskets/subscribe?bskid=%i&amp;ln=%s">' % (weburl, bskid, ln)
        end_link_subscribe = '</a>'
        general_label = _("This basket belongs to %s. You can freely %ssubscribe%s to it") % (messaging_link, link_subscribe, end_link_subscribe)      
        out = """
%(general_label)s      
<table class="bskbasket">
  <thead class="bskbasketheader">
    <tr>
      <td>
        <img src="%(weburl)s/img/webbasket_world.png" alt="%(image_label)s"/>
      </td>
      <td class="bsktitle">
        <b>%(name)s</b></a>
        %(nb_items)i %(records_label)s - %(last_update_label)s: %(last_update)s
      </td>
      <td class="bskcmtcol">
        %(link_subscribe)s%(subscribe_label)s</a>
      </td>
    </tr>
  </thead>
  <tbody>
%(items)s
  </tbody>
</table>""" % {'general_label': general_label,
               'weburl': weburl,
               'image_label': _("Public basket"),
               'name': bsk_name,
               'nb_items': len(bsk_items),
               'records_label': _("records"),
               'last_update_label': _("last update"),
               'last_update': convert_datetext_to_dategui(bsk_date_modification),
               'bskid': bskid,
               'ln': ln,
               'link_subscribe': link_subscribe,
               'subscribe_label': _("Subscribe to this basket"),
               'items': items_html}
        return out        
     
    def tmpl_display_list_public_baskets(self, baskets, inf_limit, total_baskets, order, asc, ln=cdslang):
        """Display list of public baskets.
        @param baskets: list of (bskid, name, nb_views, owner_id, owner_nickname) tuples
        @param inf limit: inferior limit
        @param total baskets: nb of baskets in total (>len(baskets) generally
        @param order: 1: order by name, 2: order by nb of views, 3: order by owner
        @param asc: 1 for ascending, 0 for descending  
        """       
        _ = gettext_set_language(ln)
        name_label = _("Basket's name")
        nb_views_label = _("Number of views")
        owner_label = _("Owner")
        base_url = weburl + '/yourbaskets/list_public_baskets?order=%i&asc=%i&amp;ln=' + ln
        asc_image = '<img src="' + weburl + '/img/webbasket_' + (asc and 'down.png' or 'up.png') + '" style="vertical-align: middle; border: 0px;" />'
        if order == 1:
            name_label = '<a href="' + base_url % (1, int(not(asc))) + '">' + name_label + ' ' + asc_image + '</a>'
            nb_views_label = '<a href="' + base_url % (2, 1) + '">' + nb_views_label + '</a>'
            owner_label = '<a href="' + base_url % (3, 1) + '">' + owner_label + '</a>'
        elif order == 2:
            name_label = '<a href="' + base_url % (1, 1) + '">' + name_label + '</a>'
            nb_views_label = '<a href="' + base_url % (2, int(not(asc))) + '">' + nb_views_label + ' ' + asc_image + '</a>'
            owner_label = '<a href="' + base_url % (3, 1) + '">' + owner_label + '</a>'
        else:
            name_label = '<a href="' + base_url % (1, 1) + '">' + name_label + '</a>'
            nb_views_label = '<a href="' + base_url % (2, 1) + '">' + nb_views_label + '</a>'
            owner_label = '<a href="' + base_url % (3, int(not(asc))) + '">' + owner_label + ' ' + asc_image + '</a>'
        baskets_html = ''
        for (bskid, name, nb_views, owner_id, owner_nickname) in baskets:
            if owner_nickname:
                display = owner_nickname
            else:
                (owner_id, owner_nickname, display) = get_user_info(owner_id)
            messaging_link = self.__create_messaging_link(owner_nickname, display, ln)
            form_view = """
<form action="%(weburl)s/yourbaskets/display_public" method="GET">
  <input type="hidden" name="ln" value="%(ln)s" />
  <input type="hidden" name="bskid" value="%(bskid)i" />
  <input type="submit" value="%(display_public_label)s" class="formbutton" />
</form>""" % {'weburl': weburl,
              'ln': ln,
              'bskid': bskid,
              'display_public_label': _("View")}
            form_subscribe = """
<form action="%(weburl)s/yourbaskets/subscribe" method="GET">
  <input type="hidden" name="ln" value="%(ln)s" />
  <input type="hidden" name="bskid" value="%(bskid)i" />
  <input type="submit" value="%(subscribe_label)s" class="formbutton"/>
</form>""" % {'weburl': weburl,
              'ln': ln,
              'bskid': bskid,
              'subscribe_label': _("Subscribe")}                      

            baskets_html += """
    <tr>
      <td>%s</td><td style="text-align:center">%i</td><td>%s</td><td style="vertical-align: middle; text-align:center;">%s</td><td style="vertical-align: middle">%s</td>
    </tr>""" % (name, nb_views, messaging_link, form_view, form_subscribe)
        if not(len(baskets_html)):
            baskets_html = '<tr><td colspan="5">' + _("There is currently no publicly accessible basket") + '</td></tr>'
        change_page = '<a href="' + weburl + '/yourbaskets/list_public_baskets?inf_limit=%i&amp;order=' + str(order)
        change_page += '&amp;asc=' + str(asc) + '&amp;ln=' + str(ln) + '"><img src="%s" style="border: 0px;"/></a> '
        footer = ''
        if inf_limit > (cfg_webbasket_max_number_of_displayed_baskets * 2)-1:
            footer += change_page % (0, weburl + '/img/sb.gif')
        if inf_limit > 0:
            footer += change_page % (inf_limit - cfg_webbasket_max_number_of_displayed_baskets, weburl + '/img/sp.gif')
        footer += ' ' + _("Displaying baskets %i-%i out of %i total baskets.") % (inf_limit+1, inf_limit + len(baskets), total_baskets) + ' '
        if inf_limit + len(baskets) < total_baskets:
            footer += change_page % (inf_limit + cfg_webbasket_max_number_of_displayed_baskets, weburl + '/img/sn.gif')
        if inf_limit + len(baskets) < total_baskets - cfg_webbasket_max_number_of_displayed_baskets:
            footer += change_page % (total_baskets - cfg_webbasket_max_number_of_displayed_baskets, weburl + '/img/se.gif')

        out = """
<table>
  <thead class="bskbasketheader">
    <tr>
      <td style="vertical-align:middle; padding: 0 20 0 20"><span class="bsktopic">%(name)s</span></td>
      <td style="vertical-align:middle; padding: 0 20 0 20""><span class="bsktopic">%(nb_views)s</span></td>
      <td style="vertical-align:middle; padding: 0 20 0 20""><span class="bsktopic">%(user)s</span></td>
      <td colspan="2" style="vertical-align:middle; padding: 0 20 0 20""><span class="bsktopic" style="text-weight:normal;">%(actions)s</span></td>
    </tr>
  </thead>
  <tbody>
    %(baskets)s
  </tbody>
  <tfooter>
    <tr>
      <td colspan="5" class="bskbasketfooter" style="text-align:center">%(footer)s</td>
    </tr>
  </tfooter>
</table>""" % {'name': name_label,
               'nb_views': nb_views_label, 
               'user': owner_label, 
               'actions': _("Actions"),
               'baskets': baskets_html,
               'footer': footer}
        return out
        
    ############################ Baskets ###################################
    
    def tmpl_basket(self, bskid,
                    name,
                    date_modification,
                    nb_views,
                    nb_items, last_added,
                    (user_can_view_content, user_can_edit_basket, 
                    user_can_view_comments, user_can_add_item, user_can_delete_item),
                    nb_comments, last_comment,
                    group_sharing_level,
                    selected_category=cfg_webbasket_categories['PRIVATE'],
                    selected_topic=0, selected_group=0,
                    items=[],
                    ln=cdslang):
        """
        display a basket.
        @param group_sharing_level: Indicate to which level a basket is shared 
                                    (None for nobody, 0 for everybody, any other positive int for group)
        @param items: list of (record id, nb of comments, last comment (date), body to display, score (int)) tuples
        """
        _ = gettext_set_language(ln)
        items_html = ''
        actions = '<table class="bskbasketheaderactions"><tr>'
        if group_sharing_level == None:
            group_img_name = 'webbasket_user.png'
            group_alt = _("Non shared basket")
        elif group_sharing_level == 0:
            group_img_name = 'webbasket_world.png'
            group_alt = _("Shared basket")
        else:
            group_img_name = 'webbasket_usergroup.png'
            group_alt = _("Group shared basket")
        edit_link = ''
        logo = "<img src=\"%s/img/%s\" alt=\"%s\" />" % (weburl, group_img_name, group_alt)
        if user_can_edit_basket:
            url = weburl + '/yourbaskets/edit?bskid=%i&amp;topic=%i&amp;ln=%s'
            url %= (bskid, selected_topic, ln)
            logo = '<a href="%s">%s</a>' % (url, logo + '<br />' + _("Edit basket")) 
        actions += "<td>" + logo + "</td>"
        actions += "</tr></table>"
        if user_can_view_content:
            if not(len(items)):
                items_html = """
<tr>
  <td colspan="3" style="text-align:center; height:100px">
    %s
  </td>
</tr>""" % _("Basket is empty")
            for item in items:
                copy = 1
                up = down = delete = 0
                if user_can_add_item:
                    up = down = 1
                    if item == items[0]:
                        up = 0
                    if item == items[-1]:
                        down = 0
                if user_can_delete_item:
                    delete = 1
                items_html += self.__tmpl_basket_item(bskid=bskid,
                                                      item=item,
                                                      uparrow=up,
                                                      downarrow=down,
                                                      copy_item=copy,
                                                      delete_item=delete,
                                                      view_comments=user_can_view_comments,
                                                      selected_category=selected_category,
                                                      selected_topic=selected_topic,
                                                      selected_group=selected_group,
                                                      ln=ln)
        else:
            items_html = """
<tr>
  <td colspan="3" style="text-align:center; height:100px">
    %s
  </td>
</tr>""" % _("You don't have sufficient rights to view this basket's content")
        content = ''
        if selected_category == cfg_webbasket_categories['EXTERNAL']:
            url = "%s/yourbaskets/unsubscribe?bskid=%i&amp;ln=%s" % (weburl, bskid, ln)
            action = "<a href=\"%s\">%s</a>"
            action %= (url, _("Unsubscribe from this basket"))
            content += action
        footer = self.tmpl_basket_footer(bskid,
                                         selected_category,
                                         selected_topic,
                                         selected_group,
                                         group_sharing_level,
                                         content,
                                         ln)
        comments_field = ''
        if nb_comments:
            comments_field = """
%i %s<br/>
%s %s""" % (nb_comments,  _("comments"), _("last comment:"), last_comment)
        out = """       
<table class="bskbasket">
  <thead class="bskbasketheader">
    <tr>
      <td>%(actions)s</td>
      <td class="bsktitle">
        <a name="bsk%(bskid)i"><b>%(name)s</b></a><br />
        %(nb_items)i %(records_label)s - %(last_update_label)s: %(last_update)s
      </td>
      <td class="bskcmtcol">
%(comments_field)s
      </td>
    </tr>
  </thead>
  <tbody>
%(items)s
%(footer)s
  </tbody>
</table>"""
        out %= {'actions': actions,
                'name': name,
                'bskid': bskid,
                'nb_items': nb_items,
                'records_label': _('records'),
                'last_update_label': _("last update"),
                'last_update': date_modification,
                'comments_field': user_can_view_comments and indent_text(comments_field, 4) or '',
                'items': items_html,
                'footer': footer}
        return out
               
    def __tmpl_basket_item(self,
                         bskid,
                         item,
                         uparrow=0, downarrow=0, copy_item=0, delete_item=0, view_comments=0,
                         selected_category=cfg_webbasket_categories['PRIVATE'],
                         selected_topic=0, selected_group=0,
                         ln=cdslang):
        """
        display a row in a basket (row is item description and actions).
        @param bskid: basket id (int)
        @param item: (record id, nb of comments, last comment (date), body to display, score (int)) tuple
        @param uparrow, downarrow, copy_item, delete_item, view_comments: actions. set to 1 to display these actions.
        """
        _ = gettext_set_language(ln)
        (recid, nb_cmt, last_cmt, val, score) = item
        actions = ''
        if uparrow:
            url = "%s/yourbaskets/modify?action=moveup&amp;bskid=%i&amp;recid=%i"
            url += "&amp;category=%s&amp;topic=%i&amp;group=%i&amp;ln=%s"
            url = url % (weburl,
                         bskid,
                         recid,
                         selected_category,
                         selected_topic,
                         selected_group,
                         ln)
            img = "%s/img/webbasket_up.png" % weburl
            actions += "<a href=\"%s\"><img src=\"%s\" alt=\"%s\" /></a>"
            actions = actions % (url,
                                 img,
                                 _("Bring item up"))
        if downarrow:
            url = "%s/yourbaskets/modify?action=movedown&amp;bskid=%i&amp;recid=%i"
            url += "&amp;category=%s&amp;topic=%i&amp;group=%i&amp;ln=%s"
            url = url % (weburl,
                         bskid,
                         recid,
                         selected_category,
                         selected_topic,
                         selected_group,
                         ln)
            img = "%s/img/webbasket_down.png" % weburl
            actions += "<a href=\"%s\"><img src=\"%s\" alt=\"%s\" /></a>"
            actions = actions % (url,
                                 img,
                                 _("Bring item down"))
        if copy_item:
            url = "%s/yourbaskets/modify?action=copy&amp;bskid=%i&amp;recid=%i"
            url += "&amp;category=%s&amp;topic=%i&amp;group_id=%i&amp;ln=%s"
            url = url % (weburl,
                         bskid,
                         recid,
                         selected_category,
                         selected_topic,
                         selected_group,
                         ln)
            img = "%s/img/webbasket_move.png" % weburl
            actions += "<a href=\"%s\"><img src=\"%s\" alt=\"%s\" /></a>"
            actions = actions % (url,
                                 img,
                                 _("Copy item"))
        if delete_item:
            url = "%s/yourbaskets/modify?action=delete&amp;bskid=%i&amp;recid=%i"
            url += "&amp;category=%s&amp;topic=%i&amp;group=%i&amp;ln=%s"
            url = url % (weburl,
                         bskid,
                         recid,
                         selected_category,
                         selected_topic,
                         selected_group,
                         ln)
            img = "%s/img/webbasket_delete.png" % weburl
            actions += "<a href=\"%s\"><img src=\"%s\" alt=\"%s\" /></a>"
            actions = actions % (url,
                                 img,
                                 _("Remove item"))
        if recid < 0:
            actions += "<img src=\"%s/img/webbasket_extern.png\" alt=\"%s\" />"
            actions = actions % (weburl, _("Extern record"))
        else:
            pass
            #actions += "<img src=\"%s/img/webbasket_intern.png\" alt=\"%s\" />"
            #actions = actions % (weburl, _("Intern record"))
        out = """
<tr>
  <td class="bskactions">%(actions)s</td>
  <td class="bskcontentcol" colspan="2">
    %(content)s
    <hr />"""
        if view_comments:
            if nb_cmt > 0:
                out += """
%(nb_cmts)i %(cmts_label)s; %(last_cmt_label)s: %(last_cmt)s<br />
"""
            out += """
<a href="%(weburl)s/yourbaskets/display_item?bskid=%(bskid)s&amp;recid=%(recid)i&amp;category=%(category)s&amp;group=%(group)i&amp;topic=%(topic)i&amp;ln=%(ln)s">%(detailed_label)s</a>
"""
        out += """
  </td>
</tr>"""
        out = out % {'actions': actions,
                     'content': val,
                     'nb_cmts': nb_cmt,
                     'last_cmt': last_cmt,
                     'weburl': weburl,
                     'bskid': bskid,
                     'recid': recid,
                     'cmts_label': _("comments"),
                     'last_cmt_label': _("last"),
                     'detailed_label': _("Details and comments"),
                     'category': selected_category,
                     'topic': selected_topic,
                     'group': selected_group,
                     'ln': ln}
        return out

    def tmpl_basket_footer(self,
                           bskid,
                           selected_category=cfg_webbasket_categories['PRIVATE'],
                           selected_topic=0,
                           selected_group=0,
                           group_sharing_level=None,
                           content='',
                           ln=cdslang):
        """display footer of a basket.
        @param group sharing level: None: basket is not shared, 
                                    0: basket is publcly accessible, 
                                    any positive int: basket is shared to groups"""
        _ = gettext_set_language(ln)
        public_infos = ''
        if group_sharing_level == 0:
            public_url = weburl + '/yourbaskets/display_public?bskid=' + str(bskid)
            public_link = '<a href="%s">%s</a>' % (public_url, public_url)
            public_infos = _("This basket is publicly accessible at this adress: %s.") % public_link
        if content:
            content += '<br />'
        if not(content) and not(public_infos):
            content += '<br />'
        out = """ 
<tr>
  <td colspan="3" class="bskbasketfooter">
    <!-- Commented. Ready for next release
    <form name="bsk_sort_%(bskid)i" action="%(weburl)s/yourbaskets/display" method="GET">
      <input type="hidden" name="bsk_to_sort" value="%(bskid)i" />
      <input type="hidden" name="category" value="%(category)s" />
      <input type="hidden" name="topic" value="%(topic)i" />
      <input type="hidden" name="group" value="%(group_id)i" />
      <input type="hidden" name="ln" value="%(ln)s" />
      %(sort_label)s:
      <input type="submit" name="sort_by_title" value="%(title_label)s" class="nonsubmitbutton" />
      <input type="submit" name="sort_by_date" value="%(date_label)s" class="nonsubmitbutton" />
    </form>-->
    %(content)s
    %(public_infos)s
  </td>
</tr>
"""
        out %= {'weburl': weburl,
                 'bskid': int(bskid),
                 'category': selected_category,
                 'topic': int(selected_topic),
                 'group_id': int(selected_group),
                 'ln': ln,
                 'sort_label': _("Sort by"),
                 'title_label': _("Title"),
                 'date_label': _("Date"),
                 'content': content,
                 'public_infos': public_infos
                 }
        return out

    ######################## Display of items and commenting ###################
   
    def tmpl_item(self,
                  (bskid, bsk_name, bsk_date_modification, bsk_nb_views, bsk_nb_records, bsk_id_owner), 
                  recid, record, comments,
                  group_sharing_level, 
                  (user_can_view_comments, user_can_add_comment, user_can_delete_comment),
                  selected_category=cfg_webbasket_categories['PRIVATE'],
                  selected_topic=0, selected_group_id=0, ln=cdslang):
        """display a specific item inside a basket. first parameter is this a big tuple which defines a basket.
        @param group sharing level: None: basket is not shared, 
                                    0: basket is publcly accessible, 
                                    any positive int: basket is shared to groups
        @param comments: list of comments  as string
        """
        _ = gettext_set_language(ln)
        total_comments = len(comments)
        action = weburl + '/yourbaskets/write_comment?bskid=%i&amp;recid=%i'
        action += '&amp;category=%s&amp;topic=%i&amp;group=%i&amp;ln=%s'
        action %= (bskid, recid, selected_category, selected_topic, selected_group_id, ln)
        back_url = weburl + '/yourbaskets/display?category=%s&amp;topic=%i&amp;group=%i'
        back_url %= (selected_category, selected_topic, selected_group_id)
                
        def list_to_str(elt1, elt2):
            """return elt1 <br /> elt2"""
            return elt1 + "<br />\n" + elt2
        if comments and user_can_view_comments:
            comments = [self.__tmpl_display_comment(bskid, recid, comment, 
                                                    (user_can_add_comment, user_can_delete_comment), 
                                                    selected_category, selected_topic, selected_group_id, 
                                                    ln)
                        for comment in comments]
            comments = reduce(list_to_str, comments)
        else:
            comments = ''
        record_text = ''
        if record:
            record_text = record[-1]
        body = """
%(record)s
<hr /><br />"""
        if user_can_view_comments:
            body += """
<h2>%(comments_label)s</h2>
%(total_label)s<br />"""
        if user_can_add_comment:
            body += """
<form name="write_comment" method="POST" action="%(action)s">
  <input type="submit" value="%(button_label)s" style="margin: 10px;" class="formbutton" />
</form>"""
        if user_can_view_comments:
            body += """
<br />
%(comments)s"""
        body %= {'record': record_text,
                'comments_label': _("Comments"),
                'total_label': _("There is a total of %i comments") % total_comments,
                'action': action,
                'button_label': _("Write a comment"),
                'comments': comments}
        if sharing_level == None:
            img = '<img src="%s/img/webbasket_user.png" alt="%s" />' % (weburl, _("Non shared basket"))
        elif sharing_level == 0:
            img = '<img src="%s/img/webbasket_world.png" alt="%s" />' % (weburl, _("Shared basket"))
        else:
            img = '<img src="%s/img/webbasket_usergroup.png" alt="%s" />' % (weburl, _("Group shared basket"))
        content = ''
        if selected_category == cfg_webbasket_categories['EXTERNAL']:
            url = "%s/yourbaskets/unsubscribe?bskid=%i&amp;ln=%s" % (weburl, bskid, ln)
            action = "<a href=\"%s\">%s</a>"
            action %= (url, _("Unsubscribe from this basket"))
            content += action
        footer = self.tmpl_basket_footer(bskid,
                                         selected_category,
                                         selected_topic,
                                         selected_group_id,
                                         sharing_level,
                                         content,
                                         ln)
        out = """      
<table class="bskbasket">
  <thead class="bskbasketheader">
    <tr>
      <td>%(img)s</td>
      <td class="bsktitle" style="height: 65px">
        <b><a href="%(weburl)s/yourbaskets/display?bskid=%(bskid)s&amp;category=%(category)s&amp;topic=%(topic)i&amp;group=%(group)i&amp;ln=%(ln)s">%(name)s</a></b><br />
        %(nb_items)i %(records_label)s - %(last_update_label)s: %(last_update)s
      </td>
      <td class="bskcmtcol"></td>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td colspan="3" style="padding: 5px;">
%(body)s
      </td>
    </tr>
%(footer)s
  </tbody>
</table>""" % {'img': img,
               'weburl': weburl,
               'bskid': bskid,
               'category': selected_category,
               'topic': selected_topic,
               'group': selected_group_id,
               'ln': ln,
               'name': bsk_name,
               'nb_items': bsk_nb_records,
               'records_label': _("records"),
               'last_update_label': _("last update"),
               'last_update': convert_datetext_to_dategui(bsk_date_modification),
               'body': body,
               'footer': footer}
        out += """
<a href="%s">%s</a>""" % (back_url, _("Back to baskets"))
        return out

    def __tmpl_display_comment(self, bskid, recid, 
                               (cmt_uid, cmt_nickname, cmt_title, cmt_body, cmt_date, cmt_priority, cmtid),
                               (user_can_add_comment, user_can_delete_comment),
                               selected_category=cfg_webbasket_categories['PRIVATE'],
                               selected_topic=0, selected_group_id=0, ln=cdslang):
        """Display a given comment. """
        _ = gettext_set_language(ln)
        out = """
<div class="bskcomment">
  <b>%(title)s</b>, %(label_author)s <a href="%(url)s/yourmessages/write?msg_to=%(user)s">%(user_display)s</a> %(label_date)s <i>%(date)s</i><br/><br/>
  %(body)s
  <br />"""
        if user_can_add_comment:
            out += """ 
<a href="%(url)s/yourbaskets/write_comment?bskid=%(bskid)i&amp;recid=%(recid)i&amp;cmtid=%(cmtid)i&amp;category=%(category)s&amp;topic=%(topic)i&amp;group=%(group_id)i&amp;ln=%(ln)s">%(reply_label)s</a>""" 
        if user_can_delete_comment:
            out += """ 
| <a href="%(url)s/yourbaskets/delete_comment?bskid=%(bskid)i&amp;recid=%(recid)i&amp;cmtid=%(cmtid)i&amp;category=%(category)s&amp;topic=%(topic)i&amp;group=%(group_id)i&amp;ln=%(ln)s">%(delete_label)s</a>""" 
        out += """
</div>"""
        out %= {'title': cmt_title,
                'url': weburl,
                'label_author': _("by"),
                'label_date': _("on"),
                'user': cmt_nickname or cmt_uid,
                'user_display': cmt_nickname or get_user_info(cmt_uid)[2],
                'date': convert_datetext_to_dategui(cmt_date),
                'body': email_quoted_txt2html(cmt_body),
                'bskid': bskid,
                'recid': recid,
                'cmtid': cmtid,
                'category': selected_category,
                'topic': selected_topic,
                'group_id': selected_group_id,
                'ln': ln,
                'reply_label': _("Reply"),
                'delete_label': _("Delete comment")}
        return out

    def tmpl_quote_comment(self, title, uid, nickname, date, body, ln=cdslang):
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
        out = title + ', ' + _("by") + ' ' + nickname + ' ' + _("on") + ' ' + date + '\n' + body
        return email_quote_txt(out)

    def tmpl_write_comment(self, bskid, recid,
                           record,
                           cmt_body='',
                           selected_category=cfg_webbasket_categories['PRIVATE'],
                           selected_topic=0, selected_group_id=0,
                           ln=cdslang,
                           warnings=[]):
        """Display interface to write a comment.
        @param bskid: basket id (int)
        @param recid: record id (int)
        @param record: text of the record (str)
        @param selected_category: cfg_webbasket_categories
        @param selected_topic: # of topic
        @param selected_group_id: in case of category: group, id of selected group
        @param ln: language
        @param warnings: list of warnings"""
        _ = gettext_set_language(ln)
        action = '%s/yourbaskets/save_comment?bskid=%i&amp;recid=%i'
        action += '&amp;category=%s&amp;topic=%i&amp;group=%i&amp;ln=%s'
        action %= (weburl, bskid, recid,
                   selected_category, selected_topic, selected_group_id, ln)
        if warnings:
            warnings_box = self.tmpl_warnings(warnings, ln)
        else:
            warnings_box = ''
        out = """
<div style="width:100%%">%(warnings)s
  %(record)s
  <hr />
  <h2>%(write_label)s</h2>
  <form name="write_comment" method="POST" action="%(action)s">
    <p class="bsklabel">%(title_label)s:</p>
    <input type="text" name="title" size="80" />
    <p class="bsklabel">%(comment_label)s:</p>
    <textarea name="text" rows="20" cols="80">%(cmt_body)s</textarea><br />
    <input type="submit" class="formbutton" value="%(button_label)s" />
  </form>
</div>""" % {'warnings': warnings_box,
             'record': record and record[-1] or '',
             'write_label': _("Add Comment"),
             'title_label': _("Title"),
             'comment_label': _("Comment"),
             'action': action,
             'cmt_body': cmt_body,
             'button_label': _("Add Comment")
            }
                
        return out
        
        ############################ Basket creation ###################################
   
    def tmpl_create_basket_link(self, selected_topic=0, ln=cdslang):
        """ Create link to basket creation """
        _ = gettext_set_language(ln)
        url = weburl + '/yourbaskets/create_basket?topic_number=%i&amp;ln=%s'
        url %= (selected_topic, ln) 
        image = '<img src="%s/img/webbasket_create_small.png" style="vertical-align: middle; margin-right: 5px" />' % weburl
        out = """
<div class="bsk_create_link">
  <a href="%s">%s%s</a>
</div>""" % (url, image, _("Create new basket"))
        return out

    def __tmpl_basket_box(self, img='', title='&nbsp;', subtitle='&nbsp;', body=''):
        """ private function, display a basket/topic selection box """ 
        out = """
<table class="bskbasket">
  <thead class="bskbasketheader">
    <tr>
      <td class="bskactions">
        <img src="%(logo)s" alt="%(label)s" />
      </td>
      <td class="bsktitle">
        <b>%(label)s</b><br />
        %(count)s
      </td>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td colspan="2">
        <table>%(basket_list)s
        </table>
      </td>
    </tr>
  </tbody>
</table>"""
        out %= {'logo': img,
              'label': title, 'count': subtitle,
              'basket_list': indent_text(body, 5)}
        return out

    def tmpl_create_box(self, new_basket_name='', new_topic_name='',
                        topics=[], selected_topic=None,
                        ln=cdslang):
        """Display a HTML box for creation of a new basket
        @param new_basket_name: prefilled value (string)
        @param new_topic_name: prefilled value (string)
        @param topics: list of topics (list of strings)
        @param selected_topic: preselected value for topic selection
        @param ln: language"""
        _ = gettext_set_language(ln)
        topics_html = ''
        if selected_topic:
            try:
                selected_topic = topics.index(selected_topic)
            except:
                selected_topic = None
        if len(topics):
            topics = zip(range(len(topics)), topics)
            topics.insert(0, (-1, _("Select topic")))
            topics_html = self.__create_select_menu('create_in_topic', topics, selected_topic)
        create_html = """
<tr>
  <td style="padding: 10 5 0 5;">%s</td>
  <td style="padding: 10 5 0 0;">
    <input type="text" name="new_basket_name" value="%s"/>
  </td>
</tr>
<tr>
  <td style="padding: 10 5 0 5;">%s</td>
  <td style="padding: 10 5 0 0;">%s</td>
</tr>
  <td style="padding: 10 5 0 5;">%s</td>
  <td style="padding: 10 5 0 0;"><input type="text" name="new_topic_name" value="%s"/></td>
</tr>""" % (_("Basket's name"), new_basket_name,
            topics_html != '' and _("Choose topic") or '', topics_html,
            topics_html != '' and _("or create a new one") or _("Create new topic"), new_topic_name)
        return self.__tmpl_basket_box(img=weburl + '/img/webbasket_create.png',
                                      title=_("Create a new basket"),
                                      body=create_html)

    def tmpl_create_basket(self, new_basket_name='',
                           new_topic_name='', create_in_topic=None, topics=[],
                           ln=cdslang):
        """Template for basket creation 
        @param new_basket_name: prefilled value (string)
        @param new_topic_name: prefilled value (string)
        @param topics: list of topics (list of strings)
        @param create_in_topic: preselected value for topic selection
        @param ln: language"""
        _ = gettext_set_language(ln)
        out = """
<form name="create_basket" action="%(action)s" method="POST">
  <input type="hidden" name="ln" value="%(ln)s" />
  <div style="padding:10px;">
    %(create_box)s
    <input type="submit" value="%(label)s" class="formbutton"/>
  </div>
</form>""" % {'action': weburl + '/yourbaskets/create_basket',
              'ln': ln,
              'create_box': indent_text(self.tmpl_create_box(new_basket_name=new_basket_name,
                                                             new_topic_name=new_topic_name,
                                                             topics=topics,
                                                             selected_topic=create_in_topic,
                                                             ln=ln),
                                        2),
              'label': _("Create new basket")}
        return out

    
    ########################## functions on baskets #########################
    
    def tmpl_add(self, recids,
                 personal_baskets,
                 group_baskets,
                 external_baskets,
                 topics,
                 referer, ln=cdslang):
        """ returns HTML for the basket selection form when adding new records
        @param recids: list of record ids
        @param personal_baskets: list of (basket id, basket name, topic) tuples
        @param group_baskets: list of (bskid, bsk_name, group_name) tuples
        @param external_baskets: list of (bskid, bsk_name) tuples
        @param topics: list of all the topics the user owns
        @param referer: url from where this page has been reached
        @param ln: language"""
        _ = gettext_set_language(ln)
        personal = ''
        group = ''
        external = ''
        if personal_baskets:
            topic_names = {}
            map(topic_names.setdefault, [row[2] for row in personal_baskets])
            topic_names = topic_names.keys()
            topic_names.sort()
            personal_html = ''
            for topic_name in topic_names:
                baskets = map(lambda x: (x[0], x[1]),
                              filter(lambda x: x[2]==topic_name,
                                     personal_baskets))
                baskets.insert(0, (-1, _("Select basket"))) 
                personal_html += """<tr>
  <td>%s</td>
  <td>%s</td>
</tr>"""
                personal_html %= (topic_name,
                                  indent_text(self.__create_select_menu('bskids',
                                                                        baskets),
                                              2))
            personal = self.__tmpl_basket_box(weburl + '/img/webbasket_user.png',
                                              _("Add to a personal basket"),
                                              _("%i baskets") % len(personal_baskets),
                                              personal_html) 
        if group_baskets:
            group_names = {}
            map(group_names.setdefault, [row[2] for row in group_baskets])
            group_names = group_names.keys()
            group_names.sort()
            groups_html = ''
            for group_name in group_names:
                baskets = map(lambda x: (x[0], x[1]),
                              filter(lambda x: x[2]==group_name,
                                     group_baskets))
                baskets.insert(0, (-1, _("Select basket"))) 
                groups_html += """<tr>
  <td>%s</td>
  <td>%s</td>
</tr>"""
                groups_html %= (group_name,
                                indent_text(self.__create_select_menu('bskids',
                                                                      baskets),
                                            2))

            group = self.__tmpl_basket_box(weburl + '/img/webbasket_usergroup.png',
                                           _("Add to a group shared basket"),
                                           _("%i baskets") % len(group_baskets),
                                           groups_html)    
        if external_baskets:
            external_html = """
<tr>
  <td>
    <select name="bskids">
      <option value="-1">%s</option>""" % _("Select basket")
            for basket in external_baskets:
                value = int(basket[0])
                label = basket[1]
                external_html += indent_text('<option value="%i">%s</option>'% (value, label), 3)
            external_html += """
    </select>
  </td>
</tr>"""
            external = self.__tmpl_basket_box(weburl + '/img/webbasket_world.png',
                                              _("Add to a public basket"),
                                              _("%i baskets") % len(external_baskets),
                                              external_html)
        create = self.tmpl_create_box(topics=topics, ln=ln)
        out_hidden_recids = ""
        for recid in recids:
            out_hidden_recids += """<input type="hidden" name="recid" value="%s" />""" % recid
        fields = filter(lambda x: x != '', [personal, group, external, create])
        while (len(fields) != 4): 
            fields.append('')
        out = """
<form name="add_to_basket" action="%(action)s" method="POST">
  <p>%(label)s:</p>
  <input type="hidden" name="referer" value="%(referer)s" />
  %(out_hidden_recids)s
  <table style="width:100%%;">
    <tr>
    <td style="width:50%%;vertical-align:top;">%(field1)s</td>
    <td style="width: 50%%;vertical-align:top;">%(field2)s</td>
    </tr>
    <tr>
      <td style="vertical-align:top;">%(field3)s</td>
      <td style="vertical-align:top;">%(field4)s</td>
    </tr>
    <tr>
      <td colspan="2">
        <input name="submit" type="submit" class="formbutton" value="%(submit_label)s" />
      </td>
    </tr>
  </table>
</form>""" % {'action': weburl + '/yourbaskets/add?ln=' + ln,
              'referer': referer,
              'out_hidden_recids': out_hidden_recids,
              'label': _("Adding %i records to these baskets") % len(recids),
              'field1': fields[0],
              'field2': fields[1],
              'field3': fields[2],
              'field4': fields[3],
              'submit_label': _("Add to baskets")}
        return out

    def tmpl_added_to_basket(self, nb_baskets_modified=0, ln=cdslang):
        """Display message for addition of records to baskets"""
        _ = gettext_set_language(ln)
        if nb_baskets_modified:
            out = _("The selected records have been successfully added to %i baskets")
            out %= nb_baskets_modified
        else:
            out = _("No records were added to the selected baskets.")
        return '<p>' + out + '</p>'
    
    
    def tmpl_confirm_delete(self, bskid,
                            (nb_users, nb_groups, nb_alerts),
                            category=cfg_webbasket_categories['PRIVATE'],
                            selected_topic=0, selected_group_id=0,
                            ln=cdslang):
        """
        display a confirm message
        @param bskid: basket id
        @param nb*: nb of users/groups/alerts linked to this basket
        @param category: private, group or external baskets are selected
        @param selected_topic: if private baskets, topic nb
        @param selected_group_id: if group: group to display baskets of
        @param ln: language
        @return html output
        """
        _ = gettext_set_language(ln)
        message = _("Are you sure you want to delete this basket?")
        if nb_users:
            message += '<p>' + _("%i users have subscribed to this basket")% nb_users + '</p>'
        if nb_groups:
            message += '<p>' + _("%i usergroups have subscribed to this basket")% nb_groups + '</p>'
        if nb_alerts:
            message += '<p>' + _("You have set %i alerts on this basket")% nb_alerts + '</p>'
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
        <input type="hidden" name="topic" value="%(topic)i" />
        <input type="hidden" name="ln" value="%(ln)s" />
        <input type="hidden" name="bskid" value="%(bskid)i" />
        <input type="submit" value="%(yes_label)s" class="formbutton" />
      </form>
    </td>
    <td>
      <form name="cancel" action="%(url_cancel)s" method="get">
        <input type="hidden" name="category" value="%(category)s" />
        <input type="hidden" name="group" value="%(group)i" />
        <input type="hidden" name="topic" value="%(topic)i" />
        <input type="hidden" name="ln" value="%(ln)s" />
        <input type="submit" value="%(no_label)s" class="formbutton" />
      </form>
    </td>
  </tr>
</table>"""% {'message': message,
              'bskid': bskid,
              'url_ok': 'delete',
              'url_cancel': 'display',
              'category': category,
              'topic': selected_topic,
              'group': selected_group_id,
              'ln':ln,
              'yes_label': _("Yes"),
              'no_label': _("Cancel")}
        return indent_text(out, 2)

    def tmpl_edit(self, bskid, bsk_name, topic, topics, groups_rights, external_rights,
                  display_general=0, display_delete=0, ln=cdslang):
        """Display interface for rights management over the given basket
        @param group_rights: list of (group id, name, rights) tuples
        @param external_rights: rights as defined in cfg_webbasket_share_levels for public access.
        @param display_general: display fields name and topic, used with personal baskets
        @param display_delete: display delete basket button
        """
        _ = gettext_set_language(ln)
        general_body = ''
        if display_general:
            general_body = """
<tr>
  <td class="bskcontentcol">%s</td>
  <td class="bskcontentcol"><input type="text" name="new_name" value="%s"/></td>
</tr>""" % (_("Basket's name"), bsk_name)
            topics_selection = zip(range(len(topics)), topics)
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
             indent_text(self.__create_select_menu('new_topic', topics_selection, topic), 2),
             _("or create a new one"))
            general_body += topics_body
        general_box = self.__tmpl_basket_box(img=weburl + '/img/webbasket_user.png',
                                             title=_("General settings"),
                                             body = general_body)
        groups_body = ''
        for (group_id, name, rights) in groups_rights:
            groups_body += """
<tr>
  <td>%s</td>
  <td>%s</td>
</tr>""" % (name, self.__create_group_rights_selection_menu(group_id, rights, ln))
        groups_body += """
<tr>
  <td colspan="2">
    <input type="submit" name="add_group" class="nonsubmitbutton" value="%s"/>
  </td>
</tr>""" % _("Add group")
        groups_box = self.__tmpl_basket_box(img=weburl + '/img/webbasket_usergroup.png',
                                            title=_("Manage groups rights"),
                                            body=groups_body)
        external_body = """
<tr>
  <td>%s</td>
</tr>""" % self.__create_rights_selection_menu('external', external_rights, ln)
        external_box = self.__tmpl_basket_box(img=weburl + '/img/webbasket_world.png',
                                              title=_("Manage global sharing rights"),
                                              body=external_body)
        delete_button = ''
        if display_delete:
            delete_button = '<input type="submit" class="nonsubmitbutton" name="delete" value="%s" />'
            delete_button %=  _("Delete basket")
        out = """
<form name="edit" action="%(action)s" method="POST">
  <p>%(label)s</p>
  <input type="hidden" name="ln" value="%(ln)s" />
  <input type="hidden" name="bskid" value="%(bskid)i" />
  <input type="hidden" name="topic" value ="%(topic)i" />
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
      <td><input type="submit" class="formbutton" name="submit" value="%(submit_label)s" /></td>
      <td><input type="submit" class="nonsubmitbutton" name="cancel" value="%(cancel_label)s" /></td>
      <td>%(delete_button)s</td>
    </tr>
  </table>
      
</form>""" % {'label': _('Editing basket "%s"') % bsk_name,
              'action': weburl + '/yourbaskets/edit',
              'ln': ln,
              'topic': topic,
              'bskid': bskid,
              'general': indent_text(general_box, 1),
              'groups': indent_text(groups_box, 1),
              'external': indent_text(external_box, 1),
              'submit_label': _("Save changes"),
              'cancel_label': _("Cancel"),
              'delete_button': delete_button}
        return out

    
    def __create_rights_selection_menu(self, name, current_rights, ln=cdslang):
        """Private function. create a drop down menu for selection of rights
        @param name: name of menu (for HTML name attribute)
        @param current_rights: rights as defined in cfg_webbasket_share_levels
        @param ln: language
        """
        _ = gettext_set_language(ln)
        elements = [('NO', _("No rights")),
                    (cfg_webbasket_share_levels['READITM'],
                     _("View records")),
                    (cfg_webbasket_share_levels['READCMT'],
                     '... ' + _("and") + ' ' + _("view comments")),
                    (cfg_webbasket_share_levels['ADDCMT'],
                     '... ' + _("and") + ' ' + _("add comments")),
                    (cfg_webbasket_share_levels['ADDITM'],
                     '... ' + _("and") + ' ' + _("add records")),
                    (cfg_webbasket_share_levels['DELCMT'],
                     '... ' + _("and") + ' ' + _("delete comments")),
                    (cfg_webbasket_share_levels['DELITM'],
                     '... ' + _("and") + ' ' + _("remove records")),
                    (cfg_webbasket_share_levels['MANAGE'],
                     '... ' + _("and") + ' ' + _("manage sharing rights"))
                    ]
        return self.__create_select_menu(name, elements, current_rights)

    def __create_group_rights_selection_menu(self, group_id, current_rights, ln=cdslang):
        """Private function. create a drop down menu for selection of rights
        @param current_rights: rights as defined in cfg_webbasket_share_levels
        @param ln: language
        """
        _ = gettext_set_language(ln)
        elements = [(str(group_id) + '_' + 'NO', _("No rights")),
                    (str(group_id) + '_' + cfg_webbasket_share_levels['READITM'],
                     _("View records")),
                    (str(group_id) + '_' + cfg_webbasket_share_levels['READCMT'],
                     '... ' + _("and") + ' ' + _("view comments")),
                    (str(group_id) + '_' + cfg_webbasket_share_levels['ADDCMT'],
                     '... ' + _("and") + ' ' + _("add comments")),
                    (str(group_id) + '_' + cfg_webbasket_share_levels['ADDITM'],
                     '... ' + _("and") + ' ' + _("add records")),
                    (str(group_id) + '_' + cfg_webbasket_share_levels['DELCMT'],
                     '... ' + _("and") + ' ' + _("delete comments")),
                    (str(group_id) + '_' + cfg_webbasket_share_levels['DELITM'],
                     '... ' + _("and") + ' ' + _("remove records")),
                    (str(group_id) + '_' + cfg_webbasket_share_levels['MANAGE'],
                     '... ' + _("and") + ' ' + _("manage sharing rights"))
                    ]
        return self.__create_select_menu('groups', elements, str(group_id) + '_' + current_rights)

    def tmpl_add_group(self, bskid, selected_topic, groups=[], ln=cdslang):
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
</tr>""" % _("You're not member of a group")
        groups_box = self.__tmpl_basket_box(img=weburl + '/img/webbasket_usergroup.png',
                                            title=_("Add group"),
                                            body=groups_body)
        out = """
<form name="add_group" action="%(action)s" method="POST">
  <p>%(label)s</p>
  <input type="hidden" name="ln" value="%(ln)s" />
  <input type="hidden" name="bskid" value="%(bskid)i" />
  <input type="hidden" name="topic" value ="%(topic)i" />
  <table style="width:100%%;">
    <tr>
      <td style="width:50%%;vertical-align:top;">%(groups)s</td>
      <td style="width:50%%;vertical-align:top;"></td>
    </tr>
    <tr>
      <td colspan="2">
        <input type="submit" class="formbutton" name="group_cancel" value="%(cancel_label)s" />
        <input type="submit" class="formbutton" name="add_group" value="%(submit_label)s" />
      </td>
    </tr>
  </table>
</form>""" % {'label': _('Sharing basket to a new group'),
              'action': weburl + '/yourbaskets/edit',
              'ln': ln,
              'topic': selected_topic,
              'bskid': bskid,
              'groups': indent_text(groups_box, 4),
              'cancel_label': _("Cancel"),
              'submit_label': _("Add group")}
        return out

    def tmpl_personal_baskets_selection_box(self,
                                            baskets=[],
                                            select_box_name='baskets',
                                            selected_bskid=None,
                                            ln=cdslang):
        """return an HTML popupmenu
        @param baskets: list of (bskid, bsk_name, bsk_topic) tuples
        @param select_box_name: name that will be used for the control
        @param selected_bskid: id of the selcte basket, use None for no selection
        @param ln: language"""
        _ = gettext_set_language(ln)
        elements = [(0, '- ' + _("no basket") + ' -')]
        for (bskid, bsk_name, bsk_topic) in baskets:
            elements.append((bskid, bsk_topic + ' > ' + bsk_name))
        return self.__create_select_menu(select_box_name, elements, selected_bskid)

    def tmpl_create_guest_warning_box(self, ln=cdslang):
        """return html warning box for non registered users"""
        _ = gettext_set_language(ln)
        message = _("You are logged in as a guest user, so your baskets will disappear at the end of the current session. If you wish you can %slogin or register here%s.")
        message %= ('<a href="%s/youraccount/login?ln=%s">'% (sweburl, ln), '</a>')
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
            out += indent_text('<option value="%s"%s>%s</option>'% (key, selected, label), 1)
        out += '</select>'
        return out
     
    def tmpl_warnings(self, warnings=[], ln=cdslang):
        """ returns HTML for warnings """
        from invenio.errorlib import get_msgs_for_code_list
        out = ''
        if type(warnings) is not list:
            warnings = [warnings]
        if len(warnings):
            warnings_parsed = get_msgs_for_code_list(warnings, 'warning', ln)
            for (warning_code, warning_text) in warnings_parsed:
                out += '<div class="important" style="padding: 10px;">%s</div>' % warning_text 
        return out

    def tmpl_back_link(self, link, ln=cdslang):
        """ returns HTML for a link whose label should be
        'Back to search results'
        """
        _ = gettext_set_language(ln)
        label = _("(Back to search results)")
        out = '<a href="%s">%s</a>' % (link, label)
        return out
       
    def __create_messaging_link(self, to, display_name, ln=cdslang):
        """prints a link to the messaging system"""
        link = "%s/yourmessages/write?msg_to=%s&amp;ln=%s" % (weburl, to, ln)
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
