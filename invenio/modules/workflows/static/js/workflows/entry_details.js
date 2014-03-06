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

var WORKFLOWS_OBJECT_PREVIEW = (function($){
    var object_preview_module = {};

    object_preview_module.bind_object_preview = function(url_prefix, entry_id) {
        $("div.btn-group[name='object_preview_btn']").bind('click', function(event){
            var format = event.target.name;
            jQuery.ajax({
                    url: url_prefix,
                    data: {'oid': entry_id,
                           'format': format},
                    success: function(json){
                        if(format == 'xm' || format == 'marcxml'){
                            $('div[name="object_preview"]').wrapAll('<debug>').text(json);
                        }else{
                            $('div[name="object_preview"]').html(json);
                        }
                    }
            })
        });
    };

    return object_preview_module;
}( window.jQuery ));
