/*
* This file is part of Invenio.
* Copyright (C) 2012 CERN.
*
* Invenio is free software; you can redistribute it and/or
* modify it under the terms of the GNU General Public License as
* published by the Free Software Foundation; either version 2 of the
* License, or (at your option) any later version.
*
* Invenio is distributed in the hope that it will be useful, but
* WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
* General Public License for more details.
*
* You should have received a copy of the GNU General Public License
* along with Invenio; if not, write to the Free Software Foundation, Inc.,
* 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
*/

/* buttons handlers and helpers for communities UI. */

function community_approval(btn, action) {
    recid = $(btn).data('recid');
    coll = $(btn).data('collection');
    url = $(btn).data('url');
    spanid = "#curate_"+recid+"_"+coll;
    if(action == 'remove'){
        spanid = spanid + "_rm";
    }

    $(spanid + " .loader").addClass("loading");
    $.ajax({
        url: url,
        type: 'POST',
        cache: false,
        data: $.param({'action': action, 'recid': recid, 'collection': coll}),
        dataType: 'json'
    }).done(function(data) {
        if(data.status == 'success' ){
            set_community_buttons(spanid, action);
        } else {
            set_ajaxmsg(spanid, "Server problem ", "warning-sign");
        }
        $(spanid + " .loader").removeClass("loading");
    }).fail(function(data) {
        set_ajaxmsg(spanid, "Server problem ", "warning-sign");
        $(spanid + " .loader").removeClass("loading");
    });
}

function set_ajaxmsg(selector, message, icon){
    $(selector+ " .ajaxmsg").show();
    $(selector+ " .ajaxmsg").html(ajaxmsg_template.render({"message": message, "icon": icon}));
}

function set_community_buttons(selector, action) {
    // Disabled buttons
    $(selector+ " .btn").attr('disabled', '');
    // Show selected
    if(action=="accept"){
        $(selector+ " ."+action+"-coll-btn").addClass('btn-success','');
    } else {
        $(selector+ " ."+action+"-coll-btn").addClass('btn-danger','');
    }
}

$(document).ready(function(){
    $(".accept-coll-btn").click(function(e){
        community_approval(this,"accept");
        e.preventDefault();
    });
    $(".reject-coll-btn").click(function(e){
        community_approval(this,"reject");
        e.preventDefault();
    });
    $(".remove-coll-btn").click(function(e){
        community_approval(this,"remove");
        e.preventDefault();
    });
});