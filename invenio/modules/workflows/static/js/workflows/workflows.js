/*
 * This file is part of Invenio.
 * Copyright (C) 2013, 2014 CERN.
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

var WORKFLOWS_APP = (function($) {

    var workflows_app = {};

    workflows_app.init_workflow = function(url_run_workflow) {

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

        workflows_app.bind_alerts();
    };

    workflows_app.activate_button = function(){
        $("input[type=submit]").removeAttr("disabled");
    };

    return workflows_app;

}(window.jQuery);
