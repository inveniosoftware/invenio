## $Id$

## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002 CERN.
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

"""Web Baskets features."""

import sys
import time
import zlib
import urllib
from config import *
from webpage import page
from dbquery import run_sql
from webuser import getUid, getDataUid,isGuestUser
from search_engine import print_record
from webaccount import warning_guest_user

imagesurl = "%s/img" % weburl

from messages import gettext_set_language

import template
webbasket_templates = template.load('webbasket')


### IMPLEMENTATION

# perform_display(): display the baskets defined by the current user
# input:  default action="" display the list of baskets and the content of the selected basket;
#         action="DELETE" delete the selected basket;
#         action="RENAME" modify the basket name;
#         action="CREATE NEW" create a new basket;
#         action="SET PUBLIC" set access permission to public;
#         action="SET PRIVATE" set access permission to private;
#         action="REMOVE" remove selected items from basket;
#         action="EXECUTE" copy/move selected items to another basket;
#         action="ORDER" change the order of the items in the basket;
#         id_basket is the identifier of the selected basket
#         delete_alerts='n' if releted alerts shouldn't be deleted; 'y' if yes
#         confirm_action="CANCEL"cancel the delete action/="CONFIRM" confirm the delete action;
#         bname is the old basket name for renaming
#         newname is the new name for renaming the basket
#         mark[] contains the list of identifiers of the items to be removed
#         to_basket is the destination basket identifier for copy or move items
#         copy_move="1" if copy items is requested,"2" if move items is requested
#         idup, ordup are the identifier and the order of the item to be moved up
#         iddown, orddown are the identifier and the order of the item to be moved down
#         of is the output format code
# output: list of baskets in formatted html+content of the selected basket
def perform_display(uid, action="", delete_alerts="", confirm_action="", id_basket=0, bname="", newname="", newbname="", mark=[], to_basket="", copy_move="", idup="", ordup="", iddown="", orddown="", of="hb", ln="en"):

    # set variables
    out = ""
    basket_name = ""
    public_basket="no"
    permission = []
    bname = get_basket_name( id_basket )

    messages = []

    # load the right message language
    _ = gettext_set_language(ln)

    # execute the requested action
    if (action == _("DELETE")) and (id_basket != '0') and (id_basket != 0):

        if (confirm_action == _("CANCEL")) or (confirm_action == _("CONFIRM")):
            try:
                msg = perform_delete(uid, delete_alerts, confirm_action, id_basket, ln)
                # out += "%s<BR>" % msg
                messages.append(msg)
            except BasketException, e:
                msg = _("The basket has not been deleted: %s") % e
                messages.append(msg)
            show_actions = 1
        else:
            # goes to the form which deletes the selected basket
            out += delete_basket(uid, id_basket, bname, ln)
            basket_name = bname
            show_actions = 0

        id_basket = '0'
    else:
        show_actions = 1
        if action == _("CREATE NEW"):
            # create a new basket
            if newname != "":
                # create a new basket newname
                try:
                    id_basket = perform_create_basket(uid, newname, ln)
                    messages.append(_("""The <I>private</I> basket <B>%s</B> has been created.""") % newname)
                    bname = newname
                except BasketException, e:
                    messages.append(_("""The basket %s has not been created: %s""") % (newname, e))
            else:
                messages.append(_("""The basket has not been created: specify a basket name."""))
        else:
            if (id_basket != '0') and (id_basket != 0):
                if action == _("RENAME"):
                    # rename the selected basket
                    if newbname != "":
                        # rename basket to newname
                        try:
                            id_basket = perform_rename_basket(uid, id_basket,newbname, ln)
                            messages.append(_("""The basket <B>%s</B> has been renamed to <B>%s</B>.\n""") % (bname, newbname))
                            bname = newbname
                        except BasketException, e:
                            messages.append(_("""The basket has not been renamed: %s""") % e)
                    else:
                        messages.append(_("""The basket has not been renamed: specify a basket name."""))
                else:
                    if action == _("SET PUBLIC"):
                        try:
                            # set public permission
                            set_permission(uid, id_basket, "y", ln)
                            url_public_basket = """%s/yourbaskets.py/display_public?id_basket=%s""" \
                                                % (weburl, id_basket)
                            messages.append(_("""The selected basket is now publicly accessible at the following URL:""") +
                                              """<A href="%s">%s</A><BR><BR>""" % (url_public_basket, url_public_basket))
                        except BasketException, e:
                            messages.append(_("The basket has not been made public: %s") % e)
                    else:
                        if action == _("SET PRIVATE"):
                            # set private permission
                            try:
                                set_permission(uid, id_basket, "n", ln)
                                messages.append(_("""The selected basket is no more publically accessible."""))
                            except BasketException, e:
                                 messages.append(_("The basket has not been made private: %s") % e)
                        else:
                            if action == _("REMOVE"):
                                # remove the selected items from the basket
                                try:
                                    remove_items(uid, id_basket, mark, ln)
                                    messages.append(_("""The selected items have been removed."""))
                                except BasketException, e:
                                    messages.append(_("""The items have not been removed: %s""")%e)
                            else:
                                if action == _("EXECUTE"):
                                    # copy/move the selected items to another basket
                                    if to_basket == '0':
                                        messages.append(_("""Select a destination basket to copy/move items."""))
                                    else:
                                        move_items(uid, id_basket, mark, to_basket, copy_move, ln)
                                        messages.append(_("""The selected items have been copied/moved."""))
                                else:
                                    if action == "ORDER":
                                        # change the order of the items in the basket
                                        try:
                                            order_items(uid, id_basket,idup,ordup,iddown,orddown, ln)
                                        except BasketException, e:
                                            messages.append(_("""The items have not been re-ordered: %s""") % e)


    # display the basket's action form
    if (show_actions):

        baskets = []
        basket_permission = ''
        # query the database for the list of baskets
        query_result = run_sql("SELECT b.id, b.name, b.public, ub.date_modification "\
                               "FROM basket b, user_basket ub "\
                               "WHERE ub.id_user=%s AND b.id=ub.id_basket "\
                               "ORDER BY b.name ASC ",
                               (uid,))
        if len(query_result) :
            for row in query_result :
                if str(id_basket) == str(row[0]):
                    basket_permission = row[2]
                baskets.append({
                                'id'   : row[0],
                                'name' : row[1],
                                'permission' : row[2],
                              })

        alerts = []
        if ((id_basket != '0') and (id_basket != 0)):
            # is basket related to some alerts?
            alert_query_result = run_sql("SELECT alert_name FROM user_query_basket WHERE id_user=%s AND id_basket=%s",
                                         (uid, id_basket))
            if len(alert_query_result):
                for row in alert_query_result:
                    alerts.append(row[0])

        out += webbasket_templates.tmpl_display_basket_actions(
                 ln          = ln,
                 weburl      = weburl,
                 messages    = messages,
                 baskets     = baskets,
                 id_basket   = id_basket,
                 basket_name = bname,
                 basket_permission = basket_permission,
                 alerts      = alerts,
               )

    # display the content of the selected basket
    if ((id_basket != '0') and (id_basket != 0)):
        if (basket_name == ""):
            if (newname != ""):
                basket_name = newname
            else:
                if (newbname != ""):
                    basket_name = newbname

        out += display_basket_content(uid, id_basket, basket_name, of, ln)
    # if is guest user print message of relogin
    if isGuestUser(uid):
        out += warning_guest_user(type="baskets", ln = ln) # modified it for gettext also
    return out


# display_basket_content: display the content of the selected basket
# input:  the identifier of the basket
#         the name of the basket
# output: the basket's content
def display_basket_content(uid, id_basket, basket_name, of, ln):

    out = ""
    out_tmp=""

    # search for basket's items
    if (id_basket != '0') and (id_basket != 0):
        query_result = run_sql("SELECT br.id_record,br.nb_order "\
                               "FROM basket_record br "\
                               "WHERE br.id_basket=%s "\
                               "ORDER BY br.nb_order DESC ",
                               (id_basket,))
        items = []
        if len(query_result) > 0:
            for row in query_result:
                items.append({
                              'id' : row[0],
                              'order' : row[1],
                              'abstract' : print_record(row[0], of),
                             })
        query_result = run_sql("SELECT b.id, b.name "\
                               "FROM basket b, user_basket ub "\
                               "WHERE ub.id_user=%s AND b.id=ub.id_basket AND b.id<>%s "\
                               "ORDER BY b.name ASC ",
                               (uid,id_basket))
        baskets = []
        if len(query_result) > 0:
            for row in query_result:
                baskets.append({
                                'id'   : row[0],
                                'name' : row[1],
                              })
        out = webbasket_templates.tmpl_display_basket_content(
                ln          = ln,
                items       = items,
                baskets     = baskets,
                id_basket   = id_basket,
                basket_name = basket_name,
                imagesurl   = imagesurl,
              )
    return out


# delete_basket: present a form for the confirmation of the delete action
# input:  the identifier of the selected basket
#         the name of the selected basket
# output: the information about the selected basket and the form for the confirmation of the delete action
def delete_basket(uid, id_basket, basket_name, ln):

    # set variables
    out = ""

    alerts = []
    query_result = run_sql("SELECT alert_name FROM user_query_basket WHERE id_user=%s AND id_basket=%s",
                           (uid, id_basket))
    if len(query_result):
        for row in query_result:
            alerts.append(row[0])

    return webbasket_templates.tmpl_delete_basket_form(
             ln = ln,
             alerts = alerts,
             id_basket = id_basket,
             basket_name = basket_name,
           )

# perform_delete: present a form for the confirmation of the delete action
# input:  delete_alerts='n' if releted alerts shouldn't be deleted; 'y' if yes
#         action='YES' if delete action has been confirmed; 'NO' otherwise
#         id_basket contains the identifier of the selected basket
# output: go back to the display baskets form with confirmation message
def perform_delete(uid, delete_alerts, confirm_action, id_basket, ln):

    # set variables
    out = ""

    # load the right message language
    _ = gettext_set_language(ln)

    if (confirm_action == _('CONFIRM')):
        #check that the user which is changing the basket name is the owner of it
        if not is_basket_owner( uid, id_basket ):
            raise NotBasketOwner(_("You are not the owner of this basket"))
        # perform the cancellation
        msg = _("The selected basket has been deleted.")

        if (delete_alerts=='y'):
            # delete the related alerts, remove from the alerts table: user_query_basket
            query_result = run_sql("DELETE FROM user_query_basket WHERE id_user=%s AND id_basket=%s",
                                   (uid, id_basket))
            msg += " " + _("The related alerts have been removed.")
        else:
            # replace the basket identifier with 0
            # select the records to update
            query_result = run_sql("SELECT id_query,alert_name,frequency,notification,date_creation,date_lastrun "\
                                   "FROM user_query_basket WHERE id_user=%s AND id_basket=%s",
                                   (uid, id_basket))
            # update the records
            for row in query_result:
                query_result_temp = run_sql("UPDATE user_query_basket "\
                                            "SET alert_name=%s,frequency=%s,notification=%s,"\
                                            "date_creation=%s,date_lastrun=%s,id_basket='0' "\
                                            "WHERE id_user=%s AND id_query=%s AND id_basket=%s",
                                            (row[1],row[2],row[3],row[4],row[5],uid,row[0],id_basket))

        # delete the relation with the user table
        query_result = run_sql("DELETE FROM user_basket WHERE id_user=%s AND id_basket=%s", (uid, id_basket))
        # delete the basket information
        query_result = run_sql("DELETE FROM basket WHERE id=%s", (id_basket,))
        # delete the basket content
        query_result = run_sql("DELETE FROM basket_record WHERE id_basket=%s", (id_basket,))

    else:
        msg=""

    return msg

# perform_rename_basket: rename an existing basket
# input:  basket identifier, basket new name
# output: basket identifier
def perform_rename_basket(uid, id_basket, newname, ln):
    # load the right message language
    _ = gettext_set_language(ln)

    # check that there's no basket owned by this user with the same name
    if has_user_basket( uid, newname):
        raise BasketNameAlreadyExists(_("You already have a basket which name is '%s'") % newname)
    #check that the user which is changing the basket name is the owner of it
    if not is_basket_owner( uid, id_basket ):
        raise NotBasketOwner(_("You are not the owner of this basket"))
    # update a row to the basket table
    tmp = run_sql("UPDATE basket SET name=%s WHERE id=%s", (newname, id_basket))

    return id_basket

class BasketException(Exception):
    """base exception class for basket related errors
    """
    pass

class BasketNameAlreadyExists(BasketException):
    """exception which is raised when a basket already exists with a certain name for a user
    """
    pass

class NotBasketOwner(BasketException):
    """exception which is raised when a user which is not the owner of a basket tries
        to perform an operation over it for which he has no privileges
    """
    pass

def has_user_basket(uid, basket_name):
    """checks if a user (uid) already has a basket which name is 'basket_name' (case-sensitive)
    """
    return run_sql("select b.id from basket b, user_basket ub where ub.id_user=%s and b.id=ub.id_basket and b.name=%s",
                   (uid, basket_name.strip()))

def is_basket_owner(uid, bid):
    """checks whether or not the user (uid) is owner for the indicated basket (bid)
    """
    return run_sql("select id_basket from user_basket where id_user=%s and id_basket=%s",
                   (uid, bid))


def get_basket_name(bid):
    """returns the name of the basket corresponding to the given id
    """
    res = run_sql("select name from basket where id=%s", (bid,))
    if not res:
        return ""
    return res[0][0]


# perform_create_basket: create a new basket and the relation with the user table
# input:  basket name
# output: basket identifier
def perform_create_basket(uid, basket_name, ln):

    # load the right message language
    _ = gettext_set_language(ln)

    # check that there's no basket owned by this user with the same name
    if has_user_basket(uid, basket_name):
        raise BasketNameAlreadyExists(_("You already have a basket which name is '%s'") % basket_name)
    # add a row to the basket table
    id_basket = run_sql("INSERT INTO basket(id,name,public) VALUES ('0',%s,'n')", (basket_name,))

    # create the relation between the user and the basket: user_basket
    query_result = run_sql("INSERT INTO user_basket(id_user,id_basket,date_modification) VALUES (%s,%s,%s)",
                           (uid, id_basket, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
    return id_basket


# basket_exists checks if a basket is in the database
# input:  the name of the basket
# output: the id of the basket if it exists, 0 otherwise
def basket_exists (basket_name, uid):
    id_basket = run_sql("SELECT b.id FROM basket b, user_basket ub "\
                        "WHERE b.name=%s "\
                        "AND b.id=ub.id_basket "\
                        "AND ub.id_user=%s",
                        (basket_name, uid))
    return id_basket

# set_permission: set access permission on a basket
# input:  basket identifier, basket public permission
# output: basket identifier
def set_permission(uid, id_basket, permission, ln):

    # load the right message language
    _ = gettext_set_language(ln)

    #check that the user which is changing the basket name is the owner of it
    if not is_basket_owner( uid, id_basket ):
        raise NotBasketOwner(_("You are not the owner of this basket"))
    # update a row to the basket table
    id_basket = run_sql("UPDATE basket SET public=%s WHERE id=%s", (permission, id_basket))

    return id_basket

# remove_items: remove the selected items from the basket
# input:  basket identifier, list of selected items
# output: basket identifier
def remove_items(uid, id_basket, mark, ln):

    # load the right message language
    _ = gettext_set_language(ln)

    #check that the user which is changing the basket name is the owner of it
    if not is_basket_owner( uid, id_basket ):
        raise NotBasketOwner(_("You are not the owner of this basket"))
    if type(mark)==list:
        selected_items=mark
    else:
        selected_items=[mark]
    for i in selected_items:
        # delete the basket content
        query_result = run_sql("DELETE FROM basket_record WHERE id_basket=%s AND id_record=%s",
                               (id_basket, i))

    return id_basket

# check_copy: check if the record exists already in the basket
# input:  basket identifier, list of selected items
# output: boolean
def check_copy(idbask,i):

    query_result = run_sql("select * from basket_record where id_basket=%s and id_record=%s",
                           (idbask,i))
    if len(query_result)>0 :
        return 0
    return 1

# copy/move the selected items to another basket
# input: original basket identifier, list of selected items,
#        destination basket identifier, copy or move option: "1"=copy, "2"=move
#output: basket identifier
def move_items(uid, id_basket, mark, to_basket, copy_move="1", ln="en"):
    if type(mark)==list:
        selected_items=mark
    else:
        selected_items=[mark]
    for i in selected_items:
	if check_copy(to_basket,i):
            query_result = run_sql("INSERT INTO basket_record(id_basket,id_record,nb_order) VALUES (%s,%s,'0')",
                                   (to_basket, i))

    if copy_move=="2":
        #delete from previous basket
        remove_items(uid, id_basket, mark, ln)

    return id_basket

# change the order of the items in the basket
# input: basket identifier
#        identifiers and positions of the items to be moved
#output: basket identifier
def order_items(uid, id_basket,idup,ordup,iddown,orddown, ln):

    # load the right message language
    _ = gettext_set_language(ln)

    #check that the user which is changing the basket name is the owner of it
    if not is_basket_owner( uid, id_basket ):
        raise NotBasketOwner(_("You are not the owner of this basket"))
    # move up the item idup (by switching its order number with the other item):
    query_result = run_sql("UPDATE basket_record SET nb_order=%s WHERE id_basket=%s AND id_record=%s",
                           (orddown,id_basket,idup))

    # move down the item iddown (by switching its order number with the other item):
    query_result = run_sql("UPDATE basket_record SET nb_order=%s WHERE id_basket=%s AND id_record=%s",
                           (ordup,id_basket,iddown))

    return id_basket


# perform_display_public: display the content of the selected basket, if public
# input:  the identifier of the basket
#         the name of the basket
#         of is the output format code
# output: the basket's content
def perform_display_public(uid, id_basket, basket_name, action, to_basket, mark, newname, of, ln = "en"):
    out = ""
    messages = []

    # load the right message language
    _ = gettext_set_language(ln)

    if action == _("EXECUTE"):
        # perform actions
        if newname != "":
            # create a new basket
            try:
                to_basket = perform_create_basket(uid, newname, ln)
                messages.append(_("""The <I>private</I> basket <B>%s</B> has been created.""") % newname)
            except BasketException, e:
                messages.append(_("""The basket %s has not been created: %s""") % (newname, e))
        # copy the selected items
        if to_basket == '0':
            messages.append(_("""Select a destination basket to copy the selected items."""))
        else:
            move_items(uid, id_basket, mark, to_basket, '1', ln)
            messages.append(_("""The selected items have been copied."""))

    # search for basket's items
    if (id_basket != '0') and (id_basket != 0):
        res = run_sql("select public from basket where id=%s", (id_basket,))
        if len(res) == 0:
            messages.append(_("""Non existing basket"""))

            out += '<collection>'
            out += webbasket_templates.tmpl_display_messages (of = of, ln = ln, messages = messages)
            out += '</collection>'
            return out

        if str(res[0][0]).strip() != 'y':
            messages.append(_("""The basket is private"""))

            out += '<collection>'
            out += webbasket_templates.tmpl_display_messages (of = of, ln = ln, messages = messages)
            out += '</collection>'
            return out

        query_result = run_sql("SELECT br.id_record,br.nb_order "\
                               "FROM basket_record br "\
                               "WHERE br.id_basket=%s "\
                               "ORDER BY br.nb_order DESC ",
                               (id_basket,))

        # Shortcut the output in the case of XML format
        if of == 'xm':
            out = '<collection xmlns="http://www.loc.gov/MARC21/slim">\n'
            for r in query_result:
                out += print_record (r [0], of)
            out += '\n</collection>\n'

            return out
        
            
        items = []
        if len(query_result) > 0:
            for row in query_result:
                items.append({
                              'id' : row[0],
                              'order' : row[1],
                              'abstract' : print_record(row[0], of),
                             })

        # copy selected items to basket
        query_result = run_sql("SELECT b.id, b.name "\
                               "FROM basket b, user_basket ub "\
                               "WHERE ub.id_user=%s AND b.id=ub.id_basket "\
                               "ORDER BY b.name ASC ",
                               (uid,))
        baskets = []
        if len(query_result) > 0:
            for row in query_result:
                baskets.append({
                                'id'   : row[0],
                                'name' : row[1],
                              })

        out += webbasket_templates.tmpl_display_messages (of = of, ln = ln, messages = messages)

        out += _("""Content of the public basket <B>%s</B> :""") % get_basket_name(id_basket) + "<BR>"
        out += webbasket_templates.tmpl_display_public_basket_content(
                ln          = ln,
                items       = items,
                baskets     = baskets,
                id_basket   = id_basket,
                basket_name = basket_name,
                imagesurl   = imagesurl,
              )
    return out

## --- new stuff starts here ---

def perform_request_add(uid=-1, recid=[], bid=[], bname=[], ln="en"):
    """Add records recid to baskets bid for user uid. If bid isn't set, it'll ask user into which baskets to add them.
    If bname is set, it'll create new basket with this name, and add records there rather than to bid."""
    out = ""

    # load the right message language
    _ = gettext_set_language(ln)

    # wash arguments:
    recIDs = recid
    bskIDs = bid
    if not type(recid) is list:
        recIDs = [recid]
    if not type(bid) is list:
        bskIDs = [bid]
    # sanity checking:
    if recIDs == []:
        return _("No records to add.")
    # do we have to create some baskets?
    if bname:
        try:
            new_basket_ID = perform_create_basket(uid, bname, ln)
            bskIDs = [new_basket_ID]
        except BasketException, e:
            out += _("""The basket %s has not been created: %s""") % (bname, e)
    basket_id_name_list = get_list_of_user_baskets(uid)
    if len(basket_id_name_list) == 1:
        bskIDs = [basket_id_name_list[0][0]]
    if bskIDs == []:
        # A - some information missing, so propose list of baskets to choose from
        if basket_id_name_list != []:
            # there are some baskets; good
            out += webbasket_templates.tmpl_add_choose_basket(
                     ln = ln,
                     baskets = basket_id_name_list,
                     recids = recIDs,
                   )
        else:
            out += webbasket_templates.tmpl_add_create_basket(
                     ln = ln,
                     recids = recIDs,
                   )
            
        if isGuestUser(uid):
            out += warning_guest_user (type = _("baskets"), ln = ln)
    else:
        # B - we have baskets IDs, so we can add records
        messages = []
        messages.append(_("Adding %s records to basket(s)...") % len(recIDs))
        for bskID in bskIDs:
            if is_basket_owner(uid, bskID):
                for recID in recIDs:
                    try:
                        res = run_sql("INSERT INTO basket_record(id_basket,id_record,nb_order) VALUES (%s,%s,%s)",
                                      (bskID,recID,'0'))
                    except:
                        pass # maybe records were already there? page reload happened?
                messages.append(_("...done."))
            else:
                messages.append(_("sorry, you are not the owner of this basket."))
        out += webbasket_templates.tmpl_add_messages(
                 ln = ln,
                 messages = messages,
               )
        out += perform_display(uid=uid, id_basket=bskIDs[0], ln=ln)
    return out

def get_list_of_user_baskets(uid):
    """Return list of lists [[basket_id, basket_name],[basket_id, basket_name],...] for the given user."""
    out = []
    res = run_sql("SELECT b.id, b.name "\
                  "FROM basket b, user_basket ub "\
                  "WHERE ub.id_user=%s AND b.id=ub.id_basket "\
                  "ORDER BY b.name ASC ",
                  (uid,))
    for row in res:
        out.append([row[0], row[1]])
    return out

def account_list_baskets(uid, action="", id_basket=0, newname="", ln="en"):

    out = ""
    # query the database for the list of baskets
    query_result = run_sql("SELECT b.id, b.name, b.public, ub.date_modification "\
                           "FROM basket b, user_basket ub "\
                           "WHERE ub.id_user=%s AND b.id=ub.id_basket "\
                           "ORDER BY b.name ASC ",
                           (uid,))

    baskets = []
    if len(query_result) :
        for row in query_result :
            if str(id_basket) == str(row[0]):
                basket_permission = row[2]
            baskets.append({
                            'id'   : row[0],
                            'name' : row[1],
                            'permission' : row[2],
                            'selected' : (str(id_basket) == str(row[0])) and "selected" or "",
                          })

    return webbasket_templates.tmpl_account_list_baskets(
             ln = ln,
             baskets = baskets,
           )
