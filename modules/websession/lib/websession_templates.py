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

import urllib
import time
import cgi
import gettext
import string
import locale

from invenio.config import *
from invenio.messages import gettext_set_language

class Template:
    def tmpl_lost_password_message(self, ln, supportemail):
        """
        Defines the text that will be displayed on the 'lost password' page

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'supportemail' *string* - The email of the support team
        """

        # load the right message language
        _ = gettext_set_language(ln)

        return _("If you have lost password for your CDS Invenio internal account, then please enter your email address below and the lost password will be emailed to you.") +\
               "<br /><br />" +\
               _("Note that if you have been using an external login system (such as CERN NICE), then we cannot do anything and you have to ask there.") +\
               _("Alternatively, you can ask %s to change your login system from external to internal.") % ("""<a href="mailto:%(email)s">%(email)s</a>""" % { 'email' : supportemail }) +\
               "<br><br>"

    def tmpl_back_form(self, ln, message, act, link):
        """
        A standard one-message-go-back-link page.

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'message' *string* - The message to display

          - 'act' *string* - The action to accomplish when going back

          - 'link' *string* - The link text
        """
        out = """
                 <table>
                    <tr>
                      <td align=center>%(message)s
                       <A href="./%(act)s">%(link)s</A></td>
                    </tr>
                 </table>
             """% {
               'message' : message,
               'act'     : act,
               'link'    : link
             }

        return out

    def tmpl_user_preferences(self, ln, email, email_disabled, password, password_disabled):
        """
        Displays a form for the user to change his email/password.

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'email' *string* - The email of the user

          - 'email_disabled' *boolean* - If the user has the right to edit his email

          - 'password' *string* - The password of the user

          - 'password_disabled' *boolean* - If the user has the right to edit his password

        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """
                <p><big><strong class="headline">Edit parameters</strong></big></p>
                <form method="post" action="%(sweburl)s/youraccount.py/change">
                <p>%(change_user_pass)s</p>
                <table>
                  <tr><td align="right"><strong>
                      %(new_email)s:</strong><br/>
                      <small class="important">(%(mandatory)s)</small>
                    </td><td>
                      <input type="text" size="25" name="email" %(email_disabled)s value="%(email)s"><br>
                      <small><span class="quicknote">%(example)s:</span>
                        <span class="example">johndoe@example.com</span>
                      </small>
                    </td>
                    <td></td>
                  </tr>
                  <tr>
                    <td align="right"><strong>%(new_password)s:</strong><br>
                      <small class="quicknote">(%(optional)s)</small>
                    </td><td align="left">
                      <input type="password" size="25" name="password" %(password_disabled)s value="%(password)s"><br>
                      <small><span class=quicknote>%(note)s:</span>
                       %(password_note)s
                      </small>
                    </td>
                  </tr>
                  <tr>
                    <td align="right"><strong>%(retype_password)s:</strong></td>
                    <td align="left">
                      <input type="password" size="25" name="password2" %(password_disabled)s value="">
                    </td>
                    <td><input type="hidden" name="action" value="edit"></td>
                  </tr>
                  <tr><td align="center" colspan="3">
                    <code class="blocknote"><input class="formbutton" type="submit" value="%(set_values)s"></code>&nbsp;&nbsp;&nbsp;
                  </td></tr>
                </table>
              </form>
        """ % {
          'change_user_pass' : _("If you want to change your email address or password, please set new values in the form below."),
          'new_email' : _("New email address"),
          'mandatory' : _("mandatory"),
          'example' : _("Example"),
          'new_password' : _("New password"),
          'optional' : _("optional"),
          'note' : _("Note"),
          'password_note' : _("The password phrase may contain punctuation, spaces, etc."),
          'retype_password' : _("Retype password"),
          'set_values' : _("Set new values"),

          'email' : email,
          'email_disabled' : email_disabled and "disabled" or "",
          'password' : password,
          'password_disabled' : password_disabled and "disabled" or "",
          'sweburl': sweburl,
        }
        return out

    def tmpl_user_external_auth(self, ln, methods, current, method_disabled):
        """
        Displays a form for the user to change his authentication method.

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'methods' *array* - The methods of authentication

          - 'method_disabled' *boolean* - If the user has the right to change this

          - 'current' *string* - The currently selected method
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """
                 <form method="post" action="%(sweburl)s/youraccount.py/change">
                   <big><strong class="headline">%(edit_method)s</strong></big>
                   <p>%(explain_method)s:</p>
                   <table>
                     <tr><td valign="top"><b>%(select_method)s:</b></td><td>
               """ % {
                 'edit_method' : _("Edit login method"),
                 'explain_method' : _("Please select which login method you would like to use to authenticate yourself"),
                 'select_method' : _("Select method"),
                 'sweburl': sweburl,
               }
        for system in methods:
            out += """<input type="radio" name="login_method" value="%(system)s" %(disabled)s %(selected)s>%(system)s<br>""" % {
                     'system' : system,
                     'disabled' : method_disabled and "disabled" or "",
                     'selected' : current == system and "disabled" or "",
                   }
        out += """  </td><td></td></tr>
                   <tr><td></td>
                     <td><input class="formbutton" type="submit" value="%(select_method)s"></td></tr></table>
                    </form>""" % {
                     'select_method' : _("Select method"),
                   }

        return out

    def tmpl_lost_password_form(self, ln, msg):
        """
        Displays a form for the user to ask for his password sent by email.

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'msg' *string* - Explicative message on top of the form.
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """
          <form  method="post" action="../youraccount.py/send_email">
            %(msg)s
          <table>
                <tr>
              <td align="right"><strong>%(email)s:</strong></td>
              <td><input type="text" size="25" name="p_email" value=""></td>
              <td><input type="hidden" name="action" value="lost"></td>
            </tr>
            <tr><td></td>
              <td><code class="blocknote"><input class="formbutton" type="submit" value="%(send)s"></code></td>
            </tr>
          </table>

          </form>
          """ % {
            'msg' : msg,
            'email' : _("Email address"),
            'send' : _("Send lost password"),
          }
        return out

    def tmpl_account_info(self, ln, uid, guest, cfg_cern_site):
        """
        Displays the account information

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'uid' *string* - The user id

          - 'guest' *boolean* - If the user is guest

          - 'cfg_cern_site' *boolean* - If the site is a CERN site
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """<P>%(account_offer)s</P>
                 <blockquote>
                 <dl>
              """ % {
                'account_offer' : _("The CDS Search offers you a possibility to personalize the interface, to set up your own personal library of documents, or to set up an automatic alert query that would run periodically and would notify you of search results by email."),
              }

        if not guest:
            out += """
                   <dt>
                   <A href="./edit?ln=%(ln)s">%(your_settings)s</A>
                   <dd>%(change_account)s""" % {
                     'ln' : ln,
                     'your_settings' : _("Your Settings"),
                     'change_account' : _("Set or change your account Email address or password. Specify your preferences about the way the interface looks like.")
                   }

        out += """
        <dt><A href="../youralerts.py/display?ln=%(ln)s">%(your_searches)s</A>
        <dd>%(search_explain)s

        <dt><A href="../yourbaskets.py/display?ln=%(ln)s">%(your_baskets)s</A>
        <dd>%(basket_explain)s""" % {
          'ln' : ln,
          'your_searches' : _("Your Searches"),
          'search_explain' : _("View all the searches you performed during the last 30 days."),
          'your_baskets' : _("Your Baskets"),
          'basket_explain' : _("With baskets you can define specific collections of items, store interesting records you want to access later or share with others."),
        }
        if guest:
            out += self.tmpl_warning_guest_user(ln = ln, type = "baskets")
        out += """
        <dt><A href="../youralerts.py/list?ln=%s">%(your_alerts)s</A>
        <dd>%(explain_alerts)s""" % {
          'ln' : ln,
          'your_alerts' : _("Your Alerts"),
          'explain_alerts' : _("Subscribe to a search which will be run periodically by our service.  The result can be sent to you via Email or stored in one of your baskets."),
        }
        if guest:
            out += self.tmpl_warning_guest_user(type="alerts", ln = ln)

        if cfg_cern_site:
            out += """
            <dt><A href="http://weblib.cern.ch/cgi-bin/checkloan?uid=&version=2">%(your_loans)s</A>
            <dd>%(explain_loans)s""" % {
              'your_loans' : _("Your Loans"),
              'explain_loans' : _("Check out book you have on load, submit borrowing requests, etc.  Requires CERN ID."),
            }

        out += """
        </dl>
        </blockquote>"""

        return out

    def tmpl_warning_guest_user(self, ln, type):
        """
        Displays a warning message about the specified type

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'type' *string* - The type of data that will get lost in case of guest account
        """

        # load the right message language
        _ = gettext_set_language(ln)

        msg= _("""You are logged in as a guest user, so your %s will disappear at the end of the current session. If you wish you can
               <a href="%s/youraccount.py/login?ln=%s">login or register here</a>.""") % (type, sweburl, ln)
        return """<table class="errorbox" summary="">
                           <thead>
                            <tr>
                             <th class="errorboxheader">%s</th>
                            </tr>
                           </thead>
                          </table>""" % msg

    def tmpl_account_body(self, ln, user):
        """
        Displays the body of the actions of the user

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'user' *string* - The user name
        """

        # load the right message language
        _ = gettext_set_language(ln)

        return _("""You are logged in as %(user)s. You may want to a) <A href="%(logout)s">logout</A>; b) edit your <A href="%(edit)s">account settings</a>.""") % {
            'user': user,
            'logout': '%s/youraccount.py/logout?ln=%s' % (sweburl, ln),
            'edit': '%s/youraccount.py/edit?ln=%s' % (sweburl, ln)
            } + "<BR><BR>"

    def tmpl_account_template(self, title, body, ln):
        """
        Displays a block of the your account page

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'title' *string* - The title of the block

          - 'body' *string* - The body of the block
        """

        out =""
        out +="""
              <table class="searchbox" width="90%%" summary=""  >
                           <thead>
                            <tr>
                             <th class="searchboxheader">%s</th>
                            </tr>
                           </thead>
                           <tbody>
                            <tr>
                             <td class="searchboxbody">%s</td>
                            </tr>
                           </tbody>
                          </table>""" % (title, body)
        return out

    def tmpl_account_page(self, ln, weburl, accBody, baskets, alerts, searches, messages, administrative):
        """
        Displays the your account page

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'weburl' *string* - The URL of CDS Invenio

          - 'accBody' *string* - The body of the heading block

          - 'baskets' *string* - The body of the baskets block

          - 'alerts' *string* - The body of the alerts block

          - 'searches' *string* - The body of the searches block

          - 'messages' *string* - The body of the messages block

          - 'administrative' *string* - The body of the administrative block
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = ""
        out += self.tmpl_account_template(_("Your Account"), accBody, ln)
        #your baskets
        out += self.tmpl_account_template(_("Your Baskets"), baskets, ln)
        out += self.tmpl_account_template(_("Your Messages"), messages, ln)
        out += self.tmpl_account_template(_("Your Alert Searches"), alerts, ln)
        out += self.tmpl_account_template(_("Your Searches"), searches, ln)
        out += self.tmpl_account_template(_("Your Submissions"),
                               _("You can consult the list of %(your_submissions)s and inquire about their status.") % {
                                 'your_submissions' :
                                    """<a href="%(weburl)s/yoursubmissions.py?ln=%(ln)s">%(your_sub)s</a>""" % {
                                      'ln' : ln,
                                      'weburl' : weburl,
                                      'your_sub' : _("your submissions")
                                    }
                               }, ln)
        out += self.tmpl_account_template(_("Your Approvals"),
                               _("You can consult the list of %(your_approvals)s with the documents you approved or refereed.") % {
                                 'your_approvals' :
                                    """ <a href="%(weburl)s/yourapprovals.py?ln=%(ln)s">%(your_app)s</a>""" % {
                                      'ln' : ln,
                                      'weburl' : weburl,
                                      'your_app' : _("your approvals"),
                                    }
                               }, ln)
        out += self.tmpl_account_template(_("Your Administrative Activities"), administrative, ln)
        return out

    def tmpl_account_emailMessage(self, ln, msg):
        """
        Displays a link to retrieve the lost password

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'msg' *string* - Explicative message on top of the form.
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out =""
        out +="""
        <body>
           %(msg)s <A href="../youraccount.py/lost?ln=%(ln)s">%(try_again)s</A>

              </body>

          """ % {
            'ln' : ln,
            'msg' : msg,
            'try_again' : _("Try again")
          }
        return out

    def tmpl_account_emailSent(self, ln, email):
        """
        Displays a confirmation message for an email sent

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'email' *string* - The email to which the message has been sent
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out =""
        out += _("Okay, password has been emailed to %s") % email
        return out

    def tmpl_account_delete(self, ln):
        """
        Displays a confirmation message about deleting the account

        Parameters:

          - 'ln' *string* - The language to display the interface in
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = "<p>" + _("""Deleting your account""")
        return out

    def tmpl_account_logout(self, ln):
        """
        Displays a confirmation message about logging out

        Parameters:

          - 'ln' *string* - The language to display the interface in
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = ""
        out += _("""You are no longer recognized.  If you wish you can <A href="./login?ln=%s">login here</A>.""") % ln
        return out

    def tmpl_login_form(self, ln, referer, internal, register_available, methods, selected_method, supportemail):
        """
        Displays a login form

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'referer' *string* - The referer URL - will be redirected upon after login

          - 'internal' *boolean* - If we are producing an internal authentication

          - 'register_available' *boolean* - If users can register freely in the system

          - 'methods' *array* - The available authentication methods

          - 'selected_method' *string* - The default authentication method

          - 'supportemail' *string* - The email of the support team
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = "<p>%(please_login)s<br>" % {
                'please_login' : _("If you already have an account, please login using the form below.")
              }

        if register_available:
            out += _("""If you don't own an account yet, please <a href="../youraccount.py/register?ln=%s">register</a> an internal account.""") % ln
        else:
            out += _("""It is not possible to create an account yourself. Contact %s if you want an account.""") % (
                      """<a href="mailto:%(email)s">%(email)s</a>""" % { 'email' : supportemail }
                    )
        out += """<form method="post" action="../youraccount.py/login">
                  <table>

               """
        if len(methods) > 1:
            # more than one method, must make a select
            login_select = """<select name="login_method">"""
            for method in methods:
                login_select += """<option value="%(method)s" %(selected)s>%(method)s</option>""" % {
                                  'method' : method,
                                  'selected' : (method == selected_method and "selected" or "")
                                }
            login_select += "</select>"
            out += """
                   <tr>
                      <td align="right">%(login_title)s</td>
                      <td>%(login_select)s</td>
                      <td></td>
                   </tr>""" % {
                     'login_title' : _("Login via:"),
                     'login_select' : login_select,
                   }
        else:
            # only one login method available
            out += """<input type="hidden" name="login_method" value="%s">""" % (methods[0])

        out += """<tr>
                   <td align="right">
                     <input type="hidden" name="ln" value="%(ln)s">
                     <input type="hidden" name="referer" value="%(referer)s">
                     <strong>%(username)s:</strong>
                   </td>
                   <td><input type="text" size="25" name="p_email" value=""></td>
                   <td></td>
                  </tr>
                  <tr>
                   <td align="right"><strong>%(password)s:</strong></td>
                   <td align="left"><input type="password" size="25" name="p_pw" value=""></td>
                   <td></td>
                  </tr>
                  <tr>
                   <td></td>
                   <td align="center" colspan="3"><code class="blocknote"><input class="formbutton" type="submit" name="action" value="%(login)s"></code>""" % {
                       'ln': ln,
                       'referer' : cgi.escape(referer),
                       'username' : _("Username"),
                       'password' : _("Password"),
                       'login' : _("login"),
                       }
        if internal:
            out += """&nbsp;&nbsp;&nbsp;(<a href="./lost?ln=%(ln)s">%(lost_pass)s</a>)""" % {
                     'ln' : ln,
                     'lost_pass' : _("Lost your password?")
                   }
        out += """</td><td></td>
                    </tr>
                  </table></form>"""
        return out

    def tmpl_register_page(self, ln, referer, level, supportemail, cdsname):
        """
        Displays a login form

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'referer' *string* - The referer URL - will be redirected upon after login

          - 'level' *int* - Login level (0 - all access, 1 - accounts activated, 2+ - no self-registration)

          - 'supportemail' *string* - The email of the support team

          - 'cdsname' *string* - The name of the installation
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = ""
        if level <= 1:
            out += _("""Please enter your email address and desired password:""")
            if level == 1:
                out += _("The account will not be possible to use before it has been verified and activated.")
            out += """
              <form method="post" action="../youraccount.py/register">
              <input type="hidden" name="referer" value="%(referer)s">
              <table>
                <tr>
                 <td align="right"><strong>%(email_address)s:</strong><br><small class="important">(%(mandatory)s)</small></td>
                 <td><input type="text" size="25" name="p_email" value=""><br>
                     <small><span class="quicknote">%(example)s:</span>
                     <span class="example">johndoe@example.com</span></small>
                 </td>
                 <td></td>
                </tr>
                <tr>
                 <td align="right"><strong>%(password)s:</strong><br><small class="quicknote">(%(optional)s)</small></td>
                 <td align="left"><input type="password" size="25" name="p_pw" value=""><br>
                    <small><span class="quicknote">%(note)s:</span> %(password_contain)s</small>
                 </td>
                 <td></td>
                </tr>
                <tr>
                 <td align="right"><strong>%(retype)s:</strong></td>
                 <td align="left"><input type="password" size="25" name="p_pw2" value=""></td>
                 <td></td>
                </tr>
                <tr>
                 <td></td>
                 <td align="left" colspan="3"><code class="blocknote"><input class="formbutton" type="submit" name="action" value="%(register)s"></code></td>
                </tr>
              </table>
              <p><strong>%(note)s:</strong> %(explain_acc)s""" % {
                'referer' : cgi.escape(referer),
                'email_address' : _("Email address"),
                'password' : _("Password"),
                'mandatory' : _("mandatory"),
                'optional' : _("optional"),
                'example' : _("Example"),
                'note' : _("Note"),
                'password_contain' : _("The password phrase may contain punctuation, spaces, etc."),
                'retype' : _("Retype Password"),
                'register' : _("register"),
                'explain_acc' : _("Please do not use valuable passwords such as your Unix, AFS or NICE passwords with this service. Your email address will stay strictly confidential and will not be disclosed to any third party. It will be used to identify you for personal services of %s. For example, you may set up an automatic alert search that will look for new preprints and will notify you daily of new arrivals by email.") % cdsname,
              }
        return out

    def tmpl_account_adminactivities(self, ln, weburl, uid, guest, roles, activities):
        """
        Displays the admin activities block for this user

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'weburl' *string* - The address of the site

          - 'uid' *string* - The used id

          - 'guest' *boolean* - If the user is guest

          - 'roles' *array* - The current user roles

          - 'activities' *array* - The user allowed activities
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = ""
        # guest condition
        if guest:
            return _("""You seem to be the guest user.  You have to <a href="../youraccount.py/login?ln=%s">login</a> first.""") % ln

        # no rights condition
        if not roles:
            return "<p>" + _("You are not authorized to access administrative functions.") + "</p>"

        # displaying form
        out += "<p>" + _("You seem to be <em>%s</em>.") % string.join(roles, ", ") + " "
        out += _("Here are some interesting web admin links for you:")

        # print proposed links:
        activities.sort(lambda x, y: cmp(string.lower(x), string.lower(y)))
        for action in activities:
            if action == "cfgbibformat":
                out += """<br>&nbsp;&nbsp;&nbsp; <a href="%s/admin/bibformat/?ln=%s">%s</a>""" % (weburl, ln, _("Configure BibFormat"))
            if action == "cfgbibharvest":
                out += """<br>&nbsp;&nbsp;&nbsp; <a href="%s/admin/bibharvest/bibharvestadmin.py?ln=%s">%s</a>""" % (weburl, ln, _("Configure BibHarvest"))
            if action == "cfgbibindex":
                out += """<br>&nbsp;&nbsp;&nbsp; <a href="%s/admin/bibindex/bibindexadmin.py?ln=%s">%s</a>""" % (weburl, ln, _("Configure BibIndex"))
            if action == "cfgbibrank":
                out += """<br>&nbsp;&nbsp;&nbsp; <a href="%s/admin/bibrank/bibrankadmin.py?ln=%s">%s</a>""" % (weburl, ln, _("Configure BibRank"))
            if action == "cfgwebaccess":
                out += """<br>&nbsp;&nbsp;&nbsp; <a href="%s/admin/webaccess/?ln=%s">%s</a>""" % (weburl, ln, _("Configure WebAccess"))
            if action == "cfgwebcomment":
                out += """<br>&nbsp;&nbsp;&nbsp; <a href="%s/admin/webcomment/webcommentadmin.py?ln=%s">%s</a>""" % (weburl, ln, _("Configure WebComment"))
            if action == "cfgwebsearch":
                out += """<br>&nbsp;&nbsp;&nbsp; <a href="%s/admin/websearch/websearchadmin.py?ln=%s">%s</a>""" % (weburl, ln, _("Configure WebSearch"))
            if action == "cfgwebsubmit":
                out += """<br>&nbsp;&nbsp;&nbsp; <a href="%s/admin/websubmit/?ln=%s">%s</a>""" % (weburl, ln, _("Configure WebSubmit"))
        out += "<br>" + _("""For more admin-level activities, see the complete %(admin_area)s""") % {
                           'admin_area' : """<a href="%s/admin/index.%s.html">%s</a>.""" % (weburl, ln, _("Admin Area"))
                         }

        return out

    def tmpl_create_userinfobox(self, ln, weburl, guest, email, submitter, referee, admin):
        """
        Displays the user block

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'weburl' *string* - The address of the site

          - 'guest' *boolean* - If the user is guest

          - 'email' *string* - The user email (if known)

          - 'submitter' *boolean* - If the user is submitter

          - 'referee' *boolean* - If the user is referee

          - 'admin' *boolean* - If the user is admin
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """<img src="%s/img/head.gif" border="0" alt="">""" % weburl
        if guest:
            out += """%(guest_msg)s ::
    	       <a class="userinfo" href="%(weburl)s/youraccount.py/display?ln=%(ln)s">%(session)s</a> ::
                   <a class="userinfo" href="%(weburl)s/youralerts.py/list?ln=%(ln)s">%(alerts)s</a> ::
                   <a class="userinfo" href="%(weburl)s/yourbaskets.py/display?ln=%(ln)s">%(baskets)s</a> ::
                   <a class="userinfo" href="%(sweburl)s/youraccount.py/login?ln=%(ln)s">%(login)s</a>""" % {
                     'weburl' : weburl,
                     'sweburl': sweburl,
                     'ln' : ln,
                     'guest_msg' : _("guest"),
                     'session' : _("session"),
                     'alerts' : _("alerts"),
                     'baskets' : _("baskets"),
                     'login' : _("login"),
                   }
        else:
            out += """%(email)s ::
    	       <a class="userinfo" href="%(weburl)s/youraccount.py/display?ln=%(ln)s">%(account)s</a> ::
                   <a class="userinfo" href="%(weburl)s/youralerts.py/list?ln=%(ln)s">%(alerts)s</a> ::
                   <a class="userinfo" href="%(weburl)s/yourmessages.py/display?ln=%(ln)s">%(messages)s</a> ::
		   <a class="userinfo" href="%(weburl)s/yourbaskets.py/display?ln=%(ln)s">%(baskets)s</a> :: """ % {
                     'email' : email,
                     'weburl' : weburl,
                     'ln' : ln,
                     'account' : _("account"),
                     'alerts' : _("alerts"),
		     'messages': _("messages"),
                     'baskets' : _("baskets"),
                   }
            if submitter:
                out += """<a class="userinfo" href="%(weburl)s/yoursubmissions.py?ln=%(ln)s">%(submission)s</a> :: """ % {
                         'weburl' : weburl,
                         'ln' : ln,
                         'submission' : _("submissions"),
                       }
            if referee:
                out += """<a class="userinfo" href="%(weburl)s/yourapprovals.py?ln=%(ln)s">%(approvals)s</a> :: """ % {
                         'weburl' : weburl,
                         'ln' : ln,
                         'approvals' : _("approvals"),
                       }
            if admin:
                out += """<a class="userinfo" href="%(weburl)s/youraccount.py/youradminactivities?ln=%(ln)s">%(administration)s</a> :: """ % {
                         'weburl' : weburl,
                         'ln' : ln,
                         'administration' : _("administration"),
                       }
            out += """<a class="userinfo" href="%(weburl)s/youraccount.py/logout?ln=%(ln)s">%(logout)s</a>""" % {
                     'weburl' : weburl,
                     'ln' : ln,
                     'logout' : _("logout"),
                   }
        return out
