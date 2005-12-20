## $Id$

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

import urllib
import time
import cgi
import gettext
import string
import locale

from cdsware.config import *
from cdsware.messages import gettext_set_language

class Template:
    def tmpl_delete_basket_form(self, ln, alerts, id_basket, basket_name):
        """
        Creates the form that demands confirmation for the deletion of a basket.

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'alerts' *array* - An array of alerts associated to the basket

          - 'id_basket' *int* - The database basket id

          - 'basket_name' *string* - The basket display name
        """

        # load the right message language
        _ = gettext_set_language(ln)

        # search for related alerts
        out = """<FORM name="deletebasket" action="display" method="post">
                  <TABLE style="background-color:F1F1F1; border:thin groove grey" cellspacing="0" cellpadding="0" width="650">
                    <TR><TD>
                      <TABLE border="0" cellpadding="0" cellspacing ="10">""" % {
                        'ln' : ln,
                      }
        if len(alerts) == 0:
            out += """<TR><TD colspan="2" align="left">%(err)s</TD></TR>""" % {
                     'err' : _("There isn't any alert related to this basket.")
                   }
        else:
            Msg = _("""The following <A href="../youralerts.py/list">alerts</A> are related to this basket:""")
            i = 1
            for alert in alerts:
                if i != 1:
                    Msg += ", "
                Msg += """<B>%s</B>""" % alert
                i+=1
            out += """<TR><TD colspan="2" align="left">%(alerts)s</TD></TR>""" % {
                     'alerts' : Msg
                   }
            out += """<TR><TD align="right">%(remove_alerts)s</TD>
                      <TD>&nbsp;<SELECT name="delete_alerts">
                        <OPTION value="n" selected>%(no)s</OPTION>
                        <OPTION value="y">%(yes)s</OPTION>
                        </SELECT>
                      </TD></TR>""" % {
                        'remove_alerts' : _("Do you want to remove the related alerts too?"),
                        'no'  : _("No"),
                        'yes' : _("Yes"),
                      }

        # confirm delete action? yes or no
        out += '''
        <TR>
          <TD align="right" width="400">
            %(delete)s <NOBR><B>%(basket_name)s</B></NOBR> ?
          </TD>
          <TD>&nbsp;
            <CODE class="blocknote"><INPUT class="formbutton" type="submit" name="confirm_action" value="%(confirm)s"></CODE>
            &nbsp;<CODE class="blocknote"><INPUT class="formbutton" type="submit" name="confirm_action" value="%(cancel)s"></CODE>
            <INPUT type="hidden" name="id_basket" value="%(id)s">
            <INPUT type="hidden" name="action" value="%(delete_action)s">
            <INPUT type="hidden" name="ln" value="%(ln)s">
          </TD>
        </TR>
        </TABLE></TD></TR></TABLE></FORM>
        ''' % {
            'confirm': _("CONFIRM"),
            'cancel': _("CANCEL"),
            'id' : id_basket,
            'basket_name' : basket_name,
            'delete' : _("Delete the basket"),
            'delete_action' : _("DELETE"),
            'ln' : ln,
            }

        return out

    def tmpl_display_basket_actions(self, ln, weburl, messages, baskets, id_basket, basket_name, alerts, basket_permission):
        """
        Displays a basket actions.

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'messages' *array* - An array of messages to display to the user (confirmation/warning messages)

          - 'baskets' *array* - An array of all the baskets

          - 'id_basket' *int* - The database basket id

          - 'basket_name' *string* - The basket display name

          - 'basket_permission' *string* - If the basket is public (value=yes        or not value=no)

          - 'alerts' *array* - An array of all the alerts associated to this basket (if existing)

        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = self.tmpl_display_messages(messages, ln)

        out += """<FORM name="displaybasket" action="display" method="post">"""

        if len(baskets) == 0:
            # create new basket form
            out += _("""No baskets have been defined.""") + "<BR>"
            out += _("""New basket name:""") + """&nbsp;
                     <INPUT type="text" name="newname" size="20" maxlength="50">&nbsp;
                     <CODE class="blocknote"><INPUT class="formbutton" type="submit" name="action" value=""" + '"' + _("CREATE NEW") + '"' + """></CODE>"""
        else:
            # display the list of baskets
            out += _("""You own <B>%s</B> baskets.""") % len(baskets) + "<BR>"
            out +=  "<NOBR>" + _("""Select an existing basket""") + """</NOBR>
                    <SELECT name="id_basket">
                      <OPTION value="0">- %(basket_name)s -</OPTION>
                    """ % {
                      'basket_name' : _("basket name")
                    }
            for basket in baskets:
                if str(id_basket) == str(basket['id']):
                    basket_selected = " selected"
                else:
                    basket_selected = ""
                out += """<OPTION value="%s"%s>%s</OPTION>""" % (basket['id'], basket_selected, basket['name'])
            out += """</SELECT>\n"""

            # buttons for basket's selection or creation
            out += """&nbsp;<CODE class="blocknote"><INPUT class="formbutton" type="submit" name="action" value=""" + '"' + _("SELECT") + '"' + "></CODE> " + _("or") +\
                   """ <INPUT type="text" name="newname" size="10" maxlength="50">&nbsp;<CODE class="blocknote"><INPUT class="formbutton" type="submit" name="action" value=""" + '"' + _("CREATE NEW") + '"' + "></CODE><BR><BR>"

            if ((id_basket != '0') and (id_basket != 0)):
                out += """<TABLE style="background-color:F1F1F1; border:thin groove grey" cellspacing="0" cellpadding="4">
                            <TR><TD colspan="2"><NOBR>%(selected_name)s <B>%(basket_name)s</B>.</NOBR></TD>
                                <TD align="right">
                                  <CODE class="blocknote"><INPUT class="formbutton" type="submit" name="action" value="%(delete)s"></CODE><br>
                                  <CODE class="blocknote"><input type="text" name="newbname"><INPUT class="formbutton" type="submit" name="action" value="%(rename)s"></CODE>
                                </TD></TR>
                       """ % {
                         'selected_name' : _("The selected basket is"),
                         'basket_name' : basket_name,
                         'delete' : _("DELETE"),
                         'rename' : _("RENAME"),
                       }

                if basket_permission == 'n':
                    public_basket="no"
                    out += """<TR><TD colspan="2">%(is_private)s</TD><TD>
                                <CODE class="blocknote"><INPUT class="formbutton" type="submit" name="action" value="%(set_public)s"></CODE>
                              </TD></TR>""" % {
                             'is_private' : _("Basket access is set to <I>private</I>, convert to <I>public</I>?"),
                             'set_public' : _("SET PUBLIC"),
                           }
                else:
                    public_basket="yes"
                    out += """<TR><TD colspan="2">%(is_public)s</TD><TD>
                                 <CODE class="blocknote"><INPUT class="formbutton" type="submit" name="action" value="%(set_private)s"></CODE>
                              </TD></TR>
                              <TR><TD colspan="3">%(public_url)s: <FONT size="-1"><NOBR><A href="%(url)s">%(url)s</A></NOBR></FONT></TD></TR>
                              """ % {
                                'is_public' : _("Basket access is set to <I>public</I>, convert to <I>private</I>?"),
                                'set_private' : _("SET PRIVATE"),
                                'public_url' : _("Public URL"),
                                'url' : """%s/yourbaskets.py/display_public?id_basket=%s""" % (weburl, id_basket)
                              }

                if len(alerts) == 0:
                    out += """<TR><TD colspan="3">%(err)s</TD></TR>""" % {
                             'err' : _("There isn't any alert related to this basket.")
                           }
                else:
                    Msg = _("""The following <A href="../youralerts.py/list">alerts</A> are related to this basket: """)
                    i = 1
                    for alert in alerts:
                        if i != 1:
                            Msg += ", "
                        Msg += """<B>%s</B>""" % alert
                        i+=1
                    out += """<TR><TD colspan="3">%(alerts)s</TD></TR>""" % {
                             'alerts' : Msg
                           }
                out += """</TABLE>"""

            # hidden parameters
            out += """<INPUT type="hidden" name="bname" value="%s">
                      <INPUT type="hidden" name="ln" value="%s">
                   """ % (basket_name, ln)

        out += """</FORM>"""

        return out

    def tmpl_display_basket_content(self, ln, items, baskets, id_basket, basket_name, imagesurl):
        """
        Displays a basket's items and options (move/copy items)

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'items' *array* - The items to display

          - 'baskets' *array* - An array of all the baskets

          - 'id_basket' *int* - The database basket id

          - 'basket_name' *string* - The basket display name

          - 'imagesurl' *string* - The URL to the images directory

        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = ""
        if len(items) > 0:
            # display the list of items
            out += """<FORM name="basketform" action="display" method="post">
                  <TABLE cellspacing="0" cellpadding="0">
                    <TR><TD>
                      <TABLE border="0" cellpadding="0" cellspacing ="3" width="650">
                        <TR><TD colspan="2">
                          %(selected_items)s:
                          <CODE class="blocknote"><INPUT class="formbutton" type="submit" name="action" value="%(remove)s"></CODE> """ % {
                        'selected_items' : _("Selected items"),
                        'remove'         : _("REMOVE")
                       }
            if len(baskets) > 0:
                out += """&nbsp;&nbsp;%(or)s&nbsp;&nbsp;
                                <SELECT name="copy_move">
                                  <OPTION value="1">%(copy)s</OPTION>
                                  <OPTION value="2">%(move)s</OPTION>
                                </SELECT> %(to)s

                      <SELECT name="to_basket">
                        <OPTION value="0">- %(select_basket)s -</OPTION>""" % {
                      'or'             : _("or"),
                      'copy'           : _("Copy"),
                      'move'           : _("Move"),
                      'to'             : _("to"),
                      'select_basket'  : _("select basket"),
                    }
                for basket in baskets:
                    out += """<OPTION value="%s">%s</OPTION>""" % (basket['id'], basket['name'])
                out += """</SELECT>
                          <CODE class="blocknote"><INPUT class="formbutton" type="submit" name="action" value="%(execute)s"></CODE><BR><BR></TD></TR>""" % {
                            'execute' : _("EXECUTE")
                          }

            out += self.tmpl_display_basket_items(ln, items, id_basket, basket_name, imagesurl)
            out += """</TABLE></TD></TR></TABLE></FORM>"""
        else:
            out += "<p>" + _("""The basket <B>%s</B> is empty.""") % basket_name + "</p>"

        return out

    def tmpl_display_messages(self, messages, ln="en", of = "hd"):
        """
        Displays a basket actions.

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'messages' *array* - An array of messages to display to the user (confirmation/warning messages)
        """

        if of and of [0] == 'x':
            out = '<!-- '
        else:
            out = ""
            
        for msg in messages:
            out += msg + "<BR>\n"
            
        if of and of [0] == 'x':
            out += ' -->'
            
        return out

    def tmpl_display_public_basket_content(self, ln, items, baskets, id_basket, basket_name, imagesurl):
        """
        Displays a public basket's items and options (copy items to other baskets)

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'items' *array* - The items to display

          - 'baskets' *array* - An array of all the baskets

          - 'id_basket' *int* - The database basket id

          - 'basket_name' *string* - The basket display name

          - 'imagesurl' *string* - The URL to the images directory

        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = ""
        if len(items) > 0:
            # display the list of items
            out += """<FORM name="basketform" action="display_public" method="post">
                  <TABLE cellspacing="0" cellpadding="0">
                    <TR><TD>
                      <TABLE border="0" cellpadding="0" cellspacing ="3" width="650">
                        <TR><TD colspan="2">"""
            if len(baskets) > 0:
                out += _("""Copy the selected items to """) +\
                        """<SELECT name="to_basket">
                          <OPTION value="0">- %(select_basket)s -</OPTION>""" % {
                        'select_basket'  : _("select basket"),
                      }
                for basket in baskets:
                    out += """<OPTION value="%s">%s</OPTION>""" % (basket['id'], basket['name'])
                out += "</SELECT>"
            else:
                out += _("""Copy the selected items to new basket""") + " "

                out += """<INPUT type="text" name="newname" size="10" maxlength="50">&nbsp;&nbsp;"""
            out += """<CODE class="blocknote"><INPUT class="formbutton" type="submit" name="action" value="%(execute)s"></CODE><BR><BR>
                       </TD></TR></TABLE><TABLE>""" % {
                            'execute' : _("EXECUTE")
                          }

            out += self.tmpl_display_basket_items(ln, items, id_basket, basket_name, imagesurl)
            out += """</TABLE></TD></TR></TABLE></FORM>"""
        else:
            out += "<p>" + _("""The basket <B>%s</B> is empty.""") % basket_name + "</p>"

        return out


    def tmpl_display_basket_items(self, ln, items, id_basket, basket_name, imagesurl):
        """
        Displays a basket's list of items.

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'items' *array* - The items to display

          - 'id_basket' *int* - The database basket id

          - 'basket_name' *string* - The basket display name

          - 'imagesurl' *string* - The URL to the images directory

        """
        out = ""
        i = 1
        for item in items :
            out += """<TR valign="top"><TD width="60">%s<input type="checkbox" name="mark" value="%s">""" % (i, item['id'])
            if i == 1:
                out += """<IMG src="%s/arrow_up.gif" border="0">""" % (imagesurl)
            else:
                out += """<A href="display?id_basket=%(bid)s&amp;action=ORDER&amp;idup=%(upid)s&amp;ordup=%(upord)s&amp;iddown=%(downid)s&amp;orddown=%(downord)s"><IMG src="%(imgurl)s/arrow_up.gif" border="0"></A>""" % {
                            'bid'     : id_basket,
                            'upid'    : item['id'],
                            'upord'   : item['order'],
                            'downid'  : items[i - 2]['id'],
                            'downord' : items[i - 2]['order'],
                            'imgurl'  : imagesurl
                          }
            if i == len(items):
                out += """<IMG src="%s/arrow_down.gif" border="0">""" % (imagesurl)
            else:
                out += """<A href="display?id_basket=%(bid)s&amp;action=ORDER&amp;idup=%(upid)s&amp;ordup=%(upord)s&amp;iddown=%(downid)s&amp;orddown=%(downord)s"><IMG src="%(imgurl)s/arrow_down.gif" border="0"></A>"""  % {
                            'bid'     : id_basket,
                            'upid'    : items[i]['id'],
                            'upord'   : items[i]['order'],
                            'downid'  : item['id'],
                            'downord' : item['order'],
                            'imgurl'  : imagesurl
                          }
            out += """</TD><TD>%s</TD></TR>
                      <TR><TD colspan="2"></TD></TR>""" % item['abstract']
            i += 1
        # hidden parameters
        out += """<INPUT type="hidden" name="id_basket" value="%s"></TD></TR><INPUT type="hidden" name="ln" value="%s">""" % (id_basket, ln)
        return out

    def tmpl_add_choose_basket(self, ln, baskets, recids):
        """
        Displays form to add the records to the basket

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'baskets' *array* - The baskets array

          - 'recids' *array* - The record ids to add to the basket

        """
        out = ""

        # load the right message language
        _ = gettext_set_language(ln)

        out += """<p>%s
                  <form action="%s/yourbaskets.py/add" method="post">""" % (
                 _("Please choose the basket you want to add %d records to:") % len(recids),
                 weburl
               )
        for recid in recids:
            out += """<input type="hidden" name="recid" value="%s">""" % recid
        out += """<select name="bid">"""
        for basket_id, basket_name in baskets:
            out += """<option value="%s">%s""" % (basket_id, basket_name)
        out += """</select>
                  <INPUT type="hidden" name="ln" value="%(ln)s">
                  <input class="formbutton" type="submit" name="action" value="%(add_to_basket)s">
               </form>""" % {
                 'ln' : ln,
                 'add_to_basket' : _("ADD TO BASKET")
               }

        return out

    def tmpl_add_create_basket(self, ln, recids):
        """
        Displays form to create a new basket (in case no baskets exist)

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'recids' *array* - The record ids to add to the basket

        """
        out = ""

        # load the right message language
        _ = gettext_set_language(ln)

        # user have to create a basket first
        out += """<p>%s
                  <form action="%s/yourbaskets.py/add" method="post">""" % (
                    _("You don't own baskets defined yet."),
                    weburl
                  )
        for recid in recids:
            out += """<input type="hidden" name="recid" value="%s">""" % recid
        out += """%(new_basket)s
                  <input type="text" size="30" name="bname" value="">
                  <INPUT type="hidden" name="ln" value="%(ln)s">
                  <input class="formbutton" type="submit" name="action" value="%(create_new)s">
                 </form>""" % {
                   'ln' : ln,
                   'new_basket' : _("New basket name:"),
                   'create_new' : _("CREATE NEW BASKET")
                 }

        return out

    def tmpl_add_messages(self, messages, ln="en"):
        """
        Displays the messages from the add interface.

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'messages' *array* - An array of messages to display to the user (confirmation/warning messages)
        """
        out = "<p>"
        for msg in messages:
            out += """<span class="info">%s</span>""" % msg
        return out

    def tmpl_account_list_baskets(self, ln, baskets):
        """
        Displays form to add the records to the basket

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'baskets' *array* - The baskets array

        """
        out = ""

        # load the right message language
        _ = gettext_set_language(ln)

        out += """<FORM name="displaybasket" action="../yourbaskets.py/display" method="post">"""
        if len(baskets):
            out += _("You own the following baskets") +\
                   """<SELECT name="id_basket"><OPTION value="0">- %(basket_name)s -</OPTION>""" % {
                        'basket_name' : _("basket name")
                      }
            for basket in baskets:
                out += """<option value="%s" %s>%s""" % (basket['id'], basket['selected'], basket['name'])
            # button for basket's selection
            out += """</SELECT> <CODE class="blocknote">
                      <INPUT class="formbutton" type="submit" name="action" value="%(select)s"></CODE> %(or)s """ % {
                        'select' : _("SELECT"),
                        'or' : _("or")
                      }

        else:
            # create new basket form
            out += _("""No baskets have been defined.""") + "<BR>"

        out += """<INPUT type="text" name="newname" size="10" maxlength="50">
                  <CODE class="blocknote"><INPUT class="formbutton" type="submit" name="action" value="%(create)s"></CODE><BR><BR> </FORM>""" % {
                    'create' : _("CREATE NEW"),
                  }
        return out

