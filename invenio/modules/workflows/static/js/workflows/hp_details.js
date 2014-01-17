// -*- coding: utf-8 -*-
// This file is part of Invenio.
// Copyright (C) 2013 CERN.
//
// Invenio is free software; you can redistribute it and/or
// modify it under the terms of the GNU General Public License as
// published by the Free Software Foundation; either version 2 of the
// License, or (at your option) any later version.
//
// Invenio is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
// General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Invenio; if not, write to the Free Software Foundation, Inc.,
// 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

url = new Object();
var bwoid;

function init_url_details(url_, bwoid_){
    url = url_;
    bwoid = bwoid_;
}


function action_buttons(url, bwoid) {

    $('#restart_button').on('click', function() {
        jQuery.ajax({
            url: url.url_restart_record,
            data: {'bwobject_id': bwoid},
            success: function(json){
                bootstrap_alert('Object restarted');
            }
        });
    });

    $('#restart_button_prev').on('click', function() {
        console.log(bwoid);
        jQuery.ajax({
            url: url.url_restart_record_prev,
            data: {'bwobject_id': bwoid},
            success: function(json){
                bootstrap_alert('Object restarted from previous task');
            }
        });
    });

    $('#continue_button').on('click', function() {
        jQuery.ajax({
            url: url.url_continue,
            data: {'bwobject_id': bwoid},
            success: function(json){
                bootstrap_alert('Object continued from next task');
            }
        });
    });

    $('#edit_form').on('submit', function(event){
        event.preventDefault();
        var form_data = new Object;
        $("#edit_form input").each(function() {
            console.log($(this)[0].name);
            if($(this)[0].name != 'submitButton'){
                if($(this)[0].name == 'core'){
                    form_data[$(this)[0].name] = $(this)[0].checked;
                }
                else{
                    form_data[$(this)[0].name] = $(this)[0].value;
                }
            }
        });

        console.log(form_data);
        jQuery.ajax({
            type: 'POST',
            url: url.url_resolve_edit,
            data: {'objectid': bwoid,
                   'data': form_data},
            success: function(json){
                bootstrap_alert('Record successfully edited');
            }
        });
    });
}

function bootstrap_alert(message) {
    $('#alert_placeholder').html('<div class="alert"><a class="close" data-dismiss="alert">×</a><span>'+message+'</span></div>');
}

if ( window.addEventListener ) {
    $("div.btn-group[name='data_version']").bind('click', function(event){
        version = event.target.name;
    });
}