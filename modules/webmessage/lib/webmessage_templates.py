# -*- coding: utf-8 -*-
## $Id$
## 
## handles rendering of webmessage module
##
## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002, 2003, 2004, 2005 CERN.
##
## The CDSware is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## The CDSware is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDSware; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.


# CDS imports
from cdsware.webmessage_mailutils import email_quoted_txt2html, email_quote_txt
from cdsware.webmessage_config import cfg_webmessage_status_code, \
                                      cfg_webmessage_separator, \
                                      cfg_webmessage_max_nb_of_messages
from cdsware.textutils import indent_text
from cdsware.dateutils import get_i18n_dbdatetext, \
                              create_day_selectbox, \
                              create_month_selectbox, \
                              create_year_selectbox
from cdsware.config import weburl, cdslang
from cdsware.messages import gettext_set_language


class Template:
    def tmpl_display_inbox(self, messages, infos=[], warnings=[], nb_messages=0, ln=cdslang):
        """
        Displays a list of messages, with the appropriate links and buttons
        @param messages: a list of tuples:
                         [(message_id,
                           user_from_id,
                           user_from_nickname,
                           subject,
                           sent_date,
                           status=]
        @param infos: a list of informations to print on top of page
        @param ln: language of the page.
        @return the list in HTML format                                            
        """
        _ = gettext_set_language(ln)
        junk = 0
        inbox = self.tmpl_warning(warnings, ln)
        inbox += self.tmpl_infobox(infos, ln)
        inbox += self.tmpl_quota(nb_messages, ln)
        inbox += """
<table class="mailbox">
  <thead class="mailboxheader">
    <tr> 
      <td>%s</td>
      <td>%s</td>
      <td>%s</td>
      <td>&nbsp;</td>
    </tr>
  </thead>
  <tfoot>
    <tr style="height:0px;">
      <td></td>
      <td></td>
      <td></td>
      <td></td>
    </tr>
  </tfoot>
  <tbody class="mailboxbody">""" %(_("Subject"), _("Sender"), _("Date"))
        if len(messages) == 0:
            inbox += """
    <tr class="mailboxrecords" style="height: 100px;">
      <td colspan="4" style="text-align: center;">
        <b>%s</b>
      </td>
    </tr>""" %(_("No new mail"),)
        for (msgid, junk, user_from_nick, subject, sent_date, status) in messages:
            subject_link = '<a href="display_msg?msgid=%i&amp;ln=%s">%s</a>'% (msgid, ln, subject)
            from_link = '<a href="write?msg_to=%s&amp;ln=%s">%s</a>'% (user_from_nick, ln, user_from_nick)
            action_link = '<a href="delete?msgid=%i&amp;ln=%s">%s</a>'% (msgid, ln, _("Delete"))
            
            s_date = get_i18n_dbdatetext(sent_date, ln)
            stat_style = ''
            if (status == cfg_webmessage_status_code['NEW']):
                stat_style = ' style="font-weight:bold"' 
            inbox += """
    <tr class="mailboxrecords">
      <td%s>%s</td>
      <td>%s</td>
      <td>%s</td>
      <td>%s</td>
    </tr>""" %(stat_style, subject_link, from_link, s_date, action_link)
        inbox += """
    <tr class="mailboxfoot">
      <td colspan="2">
        <form name="newMessage" action="write?ln=%(ln)s" method="post">
          <input type="submit" name="del_all" value="%(write_label)s" class="formbutton" />
        </form>
      </td>
      <td>&nbsp;</td>
      <td>
        <form name="deleteAll" action="delete_all?ln=%(ln)s" method="post">
          <input type="submit" name="del_all" value="%(delete_all_label)s" class="formbutton" />
        </form>
      </td>
    </tr> 
  </tbody>
</table>""" % {'ln': ln,
               'write_label': _("New message"),
               'delete_all_label': _("Delete All")}
        return indent_text(inbox, 2)

    def tmpl_write(self,
                   msg_to="",
                   msg_to_group="",
                   msg_id=0,
                   msg_subject="",
                   msg_body="",
                   msg_send_year=0,
                   msg_send_month=0,
                   msg_send_day=0,
                   warnings=[],
                   users_to_add=[],
                   groups_to_add=[],
                   user_search_pattern="",
                   group_search_pattern="",
                   display_users_to_add=1,
                   ln=cdslang):
        """
        Displays a writing message form with optional prefilled fields
        @param msg_to: nick of the user (prefills the To: field)
        @param msg_subject: subject of the message (prefills the Subject: field)
        @param msg_body: body of the message (prefills the Message: field)
        @param msg_send_year: prefills to year field
        @param msg_send_month: prefills the month field
        @param msg_send_day: prefills the day field
        @param warnings: display warnings on top of page
        @param users_to_add: list to select users
        @param groups_to_add: list to select groups
        @param user_search_pattern: prefills this field!
        @param group_search_pattern: idem
        @param display_users_to_add: 1: display user search box, 0: group... 
        @param ln: language of the form
        @return the form in HTML format
        """
        
        _ = gettext_set_language(ln)
        write_box = self.tmpl_warning(warnings)

        # escape forbidden character
        msg_to = msg_to.replace('"', '&quot;')
        msg_to_group = msg_to_group.replace('"', '&quot;')
        msg_subject = msg_subject.replace('"', '&quot;')
        user_search_pattern = user_search_pattern.replace('"','&quot;')
        group_search_pattern = group_search_pattern.replace('"','&quot;')

        if display_users_to_add:
            to_select = self.tmpl_user_or_group_search(users_to_add,
                                                       user_search_pattern,
                                                       1,
                                                       ln)
        else:
            to_select = self.tmpl_user_or_group_search(groups_to_add,
                                                       group_search_pattern,
                                                       0,
                                                       ln)
        if (msg_id != 0):
            msg_subject = _("Re: ") + msg_subject
            msg_body = email_quote_txt(msg_body)
            msg_body = msg_body.replace('>', '&gt;')
        write_box += """
<form name="write_message" action="send" method="post">
  <input type="hidden" name="ln" value="%(ln)s"/>
  <table style="width:100%%; ">
    <tr>
      <td style="width:70%%; vertical-align:text-top; padding:5px;">
        <table class="mailbox">
          <thead class="mailboxheader">
            <tr>
              <td class="mailboxlabel">%(to_label)s</td>
              <td class="mailboxlabel">%(users_label)s</td>
              <td>
                <input class="mailboxinput" type="text" name="msg_to_user" value="%(to_users)s"/>
              </td>
            </tr>
            <tr>
              <td class="mailboxlabel">&nbsp;</td>
              <td class="mailboxlabel">%(groups_label)s</td>
              <td>
                <input class="mailboxinput" type="text" name="msg_to_group" value="%(to_groups)s"/>
              </td>
            </tr>
            <tr>
              <td class="mailboxlabel">&nbsp;</td>
              <td>&nbsp;</td>
              <td>&nbsp;</td>
            </tr>
            <tr>
              <td class="mailboxlabel">%(subject_label)s</td>
              <td colspan="2">
                <input class="mailboxinput" type="text" name="msg_subject" value="%(subject)s"/>
              </td>
            </tr>
          </thead>
          <tfoot>
            <tr>
              <td style="height:0px" colspan="3"></td>
            </tr>
          </tfoot>
          <tbody class="mailboxbody">
            <tr>
              <td class="mailboxlabel">%(message_label)s</td>
              <td colspan="2" class="mailboxrecords">
                <textarea name="msg_body" rows="10" cols="50">"""
        write_box = indent_text(write_box, 2)
        write_box_part2 = """
              </td>
            </tr>
            <tr>
              <td class="mailboxlabel">
                %(send_later_label)s
              </td>
              <td colspan="2" class="mailbox_records">
                %(day_field)s
                %(month_field)s
                %(year_field)s
              </td>
            </tr>
            <!-- This should normally go in a tfoot tag. Old browsers have problems with it
                 as order must be: thead, tfoot, tbody.
                 Tfoot is thus empty :(
            -->
            <tr class="mailboxfoot">
              <td colspan="3" class="mailboxfoot">
                <input type="submit" name="send_button" value="%(send_label)s" class="formbutton"/>
              </td>
            </tr>
          </tbody>
        </table>
      </td>
      <td style="width:30%%; vertical-align:top;padding:5px;">
        %(to_select)s
      </td>
    </tr>
  </table>
</form>
"""
        write_box_part2 = indent_text(write_box_part2, 2)
        write_box += "%(body)s" "</textarea>"+ write_box_part2
        day_field = create_day_selectbox('msg_send_day', msg_send_day, ln)
        month_field = create_month_selectbox('msg_send_month', msg_send_month, ln)
        year_field = create_year_selectbox('msg_send_year', -1, 10, msg_send_year, ln)
        write_box = write_box % {'to_users' : msg_to,
                                 'to_groups': msg_to_group,
                                 'subject' : msg_subject,
                                 'body' : msg_body,
                                 'ln': ln,
                                 'day_field': day_field,
                                 'month_field': month_field,
                                 'year_field': year_field,
                                 'to_select': to_select,
                                 'send_later_label': _("Send Later:"),
                                 'to_label': _("To:"),
                                 'users_label': _("Users"),
                                 'groups_label': _("Groups"),
                                 'subject_label': _("Subject:"),
                                 'message_label': _("Message:"),
                                 'send_label': _("SEND")}
        return write_box 
    
    def tmpl_display_msg(self, 
                         msg_id="",
                         msg_from_id="",
                         msg_from_nickname="",
                         msg_sent_to="", 
                         msg_sent_to_group="",
                         msg_subject="",
                         msg_body="",
                         msg_sent_date="",
                         msg_received_date="0000-00-00 00:00:00",
                         ln=cdslang):
        """
        Displays a given message
        @param msg_id: id of the message
        @param msg_from_id: id of user who sent the message
        @param msg_from_nickname: nickname of the user who sent the message
        @param msg_sent_to: list of users who received the message
                            (comma separated string)
        @param msg_sent_to_group: list of groups who received the message
                                  (comma separated string)
        @param msg_subject: subject of the message
        @param msg_body: body of the message
        @param msg_sent_date: date at which the message was sent
        @param msg_received_date: date at which the message had to be received
                                  (if this argument != 0000-00-00 => reminder
        @param ln: language of the page
        @return the message in HTML format
        """

        # load the right message language
        _ = gettext_set_language(ln)
        
        sent_to_link = ""
        tos = msg_sent_to.split(cfg_webmessage_separator)
        if (tos):
            for to in tos[0:-1]:
                sent_to_link += '<a href="write?msg_to=%s&amp;ln=%s">'% (to, ln)
                sent_to_link += '%s</a>%s '% (to, cfg_webmessage_separator)
            sent_to_link += '<a href="write?msg_to=%s&amp;ln=%s">%s</a>'% (tos[-1], ln, tos[-1])
        group_to_link = ""
        groups = msg_sent_to_group.split(cfg_webmessage_separator)
        if (groups):
            for group in groups[0:-1]:
                group_to_link += '<a href="write?msg_to_group=%s&amp;ln=%s">'% (group, ln)
                group_to_link += '%s</a>%s '% (group, cfg_webmessage_separator)
            group_to_link += '<a href="write?msg_to_group=%s&amp;ln=%s">%s</a>'% (groups[-1], ln, groups[-1])
        # format the msg so that the '>>' chars give vertical lines
        final_body = email_quoted_txt2html(msg_body)

        out = """
<table class="mailbox">
  <thead class="mailboxheader">
    <tr>
      <td class="mailboxlabel">From:</td>
      <td><a href="write?msg_to=%(from)s&amp;ln=%(ln)s">%(from)s</a></td>
    </tr>
    <tr>
      <td class="mailboxlabel">Subject:</td>
      <td>%(subject)s</td>
    </tr>
    <tr>
      <td class="mailboxlabel">Sent:</td>
      <td>%(sent_date)s</td>
    </tr>"""
        if (msg_received_date != '0000-00-00 00:00:00'):
            out += """
    <tr>
      <td class="mailboxlabel">Received:</td>
      <td>%(received_date)s</td>
    </tr>"""
        out += """
    <tr>
      <td class="mailboxlabel">CC:</td>
      <td>%(sent_to)s</td>
    </tr>"""
        if (msg_sent_to_group != ""):
            out += """
    <tr>
      <td class="mailboxlabel">Groups:</td>
      <td>%(sent_to_group)s</td>
    </tr>"""
        out += """
  </thead>
  <tfoot>
    <tr>
      <td></td>
      <td></td>
    </tr>
  </tfoot>
  <tbody class="mailboxbody">
    <tr>
      <td colspan="2" class="mailboxrecords">%(body)s</td>
    </tr>
    <tr class="mailboxfoot">
      <td>
        <form name="reply" action="write?msg_reply_id=%(msg_id)s" method="post">
          <input class="formbutton" name="reply" value="%(reply_txt)s" type="submit" />
        </form>
      </td>
      <td>
        <form name="deletemsg" action="delete?msgid=%(msg_id)s&amp;ln=%(ln)s" method="post">
          <input class="formbutton" name="delete" value="%(delete_txt)s" type="submit" />
        </form>
      </td>
    </tr>
  </tbody>
</table>
        """
        out = out % {'from' : msg_from_nickname,
                     'sent_date' : get_i18n_dbdatetext(msg_sent_date, ln),
                     'received_date': get_i18n_dbdatetext(msg_received_date, ln),
                     'sent_to': sent_to_link,
                     'sent_to_group': group_to_link,
                     'subject' : msg_subject,
                     'body' : final_body,
                     'reply_to': msg_from_id,
                     'msg_id': msg_id,
                     'ln': ln,
                     'reply_txt':_("REPLY"),
                     'delete_txt': _("DELETE")}
        return indent_text(out, 2)

    def tmpl_navtrail(self, ln=cdslang, title=""):
        """
        display the navtrail, e.g.:
        Your account > Your messages > title
        @param title: the last part of the navtrail. Is not a link
        @param ln: language
        return html formatted navtrail
        """
        _ = gettext_set_language(ln)
        nav_h1 = '<a class="navtrail" href="%s/youraccount.py/display">%s</a>'
        nav_h2 = ""
        if (title != ""):
            nav_h2 = ' &gt; <a class="navtrail" href="%s/yourmessages.py/display">%s</a>'
            nav_h2 = nav_h2 % (weburl, _("Your Messages"))

        return  nav_h1% (weburl,_("Your Account")) + nav_h2

    
    def tmpl_confirm_delete(self, ln=cdslang):
        """
        display a confirm message
        @param ln: language
        @return html output
        """
        _ = gettext_set_language(ln)
        out = """
<table class="confirmoperation">
  <tr>
    <td colspan="2" class="confirmmessage">
      %(message)s
    </td>
  </tr>
  <tr>
    <td>
      <form name="validate" action="delete_all" method="post">
        <input type="hidden" name="confirmed" value="1" />
        <input type="hidden" name="ln" value="%(ln)s" />
        <input type="submit" value="%(yes_label)s" class="formbutton" />
      </form>
    </td>
    <td>
      <form name="cancel" action="display" method="post">
        <input type="hidden" name="ln" value="%(ln)s" />
        <input type="submit" value="%(no_label)s" class="formbutton" />
      </form>
    </td>
  </tr>
</table>"""% {'message': _("Are your sure you want to empty your whole mailbox?"),
              'ln':ln,
              'yes_label': _("Yes"),
              'no_label': _("No")}
        return indent_text(out, 2)

    def tmpl_infobox(self, infos, ln=cdslang):
        """Display len(infos) information fields
        @param infos: list of strings
        @param ln=language
        @return html output
        """
        _ = gettext_set_language(ln)
        if not((type(infos) is list) or (type(infos) is tuple)):
            infos = [infos]       
        infobox = ""
        for info in infos:
            infobox += "<div class=\"infobox\">"
            lines = info.split("\n")
            for line in lines[0:-1]:
                infobox += line + "<br/>\n"
            infobox += lines[-1] + "</div><br/>\n"
        return infobox


    def tmpl_warning(self, warnings, ln=cdslang):
        """
        Display len(warnings) warning fields
        @param infos: list of strings
        @param ln=language
        @return html output
        """
        if not((type(warnings) is list) or (type(warnings) is tuple)):
            warnings = [warnings]
        warningbox = ""
        if warnings != []:
            warningbox = "<div class=\"warningbox\">\n  <b>Warning:</b>\n"
            for warning in warnings:
                lines = warning.split("\n")
                warningbox += "  <p>"
                for line in lines[0:-1]:
                    warningbox += line + "    <br/>\n"
                warningbox += lines[-1] + "  </p>"
            warningbox += "</div><br/>\n"
        return warningbox


    def tmpl_quota(self, nb_messages=0, ln=cdslang):
        """
        Display a quota bar.
        @nb_messages: number of messages in inbox.
        @ln=language
        @return html output
        """
        _ = gettext_set_language(ln)
        quota = float(cfg_webmessage_max_nb_of_messages)
        ratio = float(nb_messages) / quota
        out = """
%(quota_label)s<br/>
<div class="quotabox">
  <div class="quotabar" style="width:%(width)ipx"></div>
</div>""" %{'quota_label' : _("Quota: %.1f%%")%(ratio * 100.0),
            'width' : int(ratio * 200)
            }

        return out

    
    def tmpl_multiple_select(self, select_name, tuples_list, ln=cdslang):
        """displays a multiple select environment
        @param tuples_list: a list of (value, isSelected) tuples
        @return HTML output
        """
        _ = gettext_set_language(ln)
        if not((type(tuples_list) is list) or (type(tuples_list) is tuple)):
            tuples_list = [tuples_list]
        out = """
<select name="%s" multiple="multiple" style="width:100%%">
  <option value="" disabled="disabled">%s</option>
""" % (select_name,_("Please select value(s)"))
        for (value, is_selected) in tuples_list:
            out += "  <option value=\"%s\""% value
            if is_selected:
                out += " selected=\"selected\""
            out += ">%s</option>\n"% value
        out += "</select>\n"
        return out    


    def tmpl_user_or_group_search(self,
                                  tuples_list=[],
                                  search_pattern="",
                                  display_user=1,
                                  ln=cdslang):
        """
        Display a box for user searching
        @param tuples_list: list of (value, is_selected) tuples
        @param search_pattern: text to display in this field
        @param display_user: 1 for user 0 for group
        @param ln: language
        @return html output
        """
        _ = gettext_set_language(ln)
        if display_user:
            header = """
  <thead class="mailboxheader">
    <tr>
      <td>
        %(search_user_label)s
      </td>
      <td>
        <input type="submit" name="switch_to_group_button" value="%(search_group_label)s" class="nonsubmitbutton" />
      </td>
    </tr>
  </thead>
"""
            search_field_name = "user_search_pattern"
            search_button_name = "search_user_button"
            multiple_select = self.tmpl_multiple_select('users_to_add', tuples_list)
            add_button = "<input type=\"submit\" name=\"add_to_user_button\" value=\"%s\" class=\"nonsubmitbutton\" />"
            add_button = add_button % _("Add to users")
        else:
            header = """
  <thead class="mailboxheader">
    <tr>
      <td>
        <input type="submit" name="switch_to_user_button" value="%(search_user_label)s" class="nonsubmitbutton" />
      </td>
      <td>
        %(search_group_label)s
      </td>
    </tr>
  </thead>
"""
            search_field_name = "group_search_pattern"
            search_button_name = "search_group_button"
            multiple_select = self.tmpl_multiple_select('groups_to_add', tuples_list)
            add_button = "<input type=\"submit\" name=\"add_to_group_button\" value=\"%s\" class=\"nonsubmitbutton\" />"
            add_button = add_button % _("Add to groups")

        out = "<table class=\"mailbox\">\n" + header
        out += """
  <tbody class="mailboxbody">
    <tr>
      <td style="text-align:center;">
        <input type="text" name="%(search_field_name)s" value="%(search_pattern)s" />
      </td>
      <td style="text-align:center">
        <input type="submit" name="%(search_button_name)s" value="%(search_button_label)s" class="nonsubmitbutton" />
    </tr>
    <tr>
      <td>
        %(multiple_select)s
      </td>
      <td>
        %(add_button)s
      </td>
    </tr>
  </tbody>
</table>
"""
        out = out% {'search_user_label'  : _("Find a user"),
                    'search_group_label' : _("Find a group"),
                    'search_button_label': _("Search"),
                    'search_field_name'  : search_field_name,
                    'search_pattern'     : search_pattern,
                    'search_button_name' : search_button_name,
                    'multiple_select'    : multiple_select,
                    'add_button'         : add_button}
        return out

    def tmpl_account_new_mail(self, nb_new_mail=0, ln=cdslang):
        """
        display infos about inbox (used by myaccount.py)
        @param nb_new_mail: number of new mails
        @param ln: language
        retourn: html output.
        """
        _ = gettext_set_language(ln)
        out = _("You got <b>%i</b> new messages.<br/>\n")% nb_new_mail
        out += _("You can see all your messages in your <a href=\"/yourmessages.py?ln=%s\">inbox</a>")% ln
        return out

    
