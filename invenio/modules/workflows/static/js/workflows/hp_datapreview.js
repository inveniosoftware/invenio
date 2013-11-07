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

$(document).ready(function(){    
    var bwoid = getURLParameter('bwobject_id');
    var datapreview = "hd";
    var url_preview = "/admin/holdingpen/entry_data_preview";

    window.data_preview = function(format){
        jQuery.ajax({
            url: url_preview + "?oid=" + bwoid + "&recformat=" + format,
            success: function(json){
                if(format == "xm" || format == "marcxml"){
                    if( json === ""){
                        json = "Preview not available";
                    }
                    $('div[id="object_preview"]').remove();
                    $('pre[name="object_preview"]').remove();
                    if( $('pre[name="object_preview"]').length === 0 ){
                        $('div[id="object_preview_container"]').append("<pre name='object_preview'></pre>");
                    }
                    $('pre[name="object_preview"]').html(json);

                }else{
                    if( json === ""){
                        json = "Preview not available";
                    }
                    $('pre[name="object_preview"]').remove();
                    $('div[id="object_preview"]').remove();
                    $('div[id="object_preview_container"]').append("<div id='object_preview'></div>");
                    $('div[id="object_preview"]').html(json);
                }
            }
        });
    };

    window.setbwoid = function(id){
        bwoid = id;
        data_preview(datapreview);
        console.log(id);
    };

    window.setDataPreview = function(dp){
        datapreview = dp;
        data_preview(datapreview);
    };
});