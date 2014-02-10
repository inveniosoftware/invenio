/*
 * This file is part of Invenio.
 * Copyright (C) 2013 CERN.
 *
 * Invenio is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
 * License, or (at your option) any later version.
 *
 * Invenio is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Invenio; if not, write to the Free Software Foundation, Inc.,
 * 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
 */


function init_workflow(url_run_workflow) {

    $("#example_my_workflow").popover({
        trigger: 'hover',
        placement: 'right',
        content: "Workflow has been started."
    });
    $("input[type=submit]").bind('click', function(){
        w_name = $(this).attr('name');
        jQuery.ajax({
            url: url_run_workflow + "?workflow_name=" + w_name,
            success: function(json){
                    bootstrap_alert.warning('Workflow has been started');
            }
        })
    });

    bind_alerts();
}

function bind_alerts() {
    bootstrap_alert = function() {}
    bootstrap_alert.warning = function(message) {
        $('#alert_placeholder').html('<div class="alert"><a class="close" data-dismiss="alert">×</a><span>'+message+'</span></div>')
    }

    window.setTimeout(function() {
        $("#alert_placeholder").fadeTo(500, 0).slideUp(500, function(){
            // $(this).slideDown(500);
        });
    }, 3500);
}

function activate_button(){
    $("input[type=submit]").removeAttr("disabled");
}
