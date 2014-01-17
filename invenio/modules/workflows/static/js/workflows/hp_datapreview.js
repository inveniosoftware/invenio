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

function data_preview(url_preview, bwoid, format) {
    jQuery.ajax({
        url: url_preview,
        data: {'oid': bwoid,
               'of': format},
        success: function(json){
            if(format == "xm" || format == "marcxml"){
                if( json.data === ""){
                    json.data = "Preview not available";
                }
                $('div[id="object_preview_container'+bwoid+'"]').empty();
                $('div[id="object_preview_container'+bwoid+'"]').append("<pre><code id='object_preview' class='language-markup'></code></pre>");
                $('code[id="object_preview"]').append(json.data);
                Prism.highlightElement($('code[id="object_preview"]')[0]);
            }else{
                if( json.data === ""){
                    json.data = "Preview not available";
                }
                $('div[id="object_preview_container'+bwoid+'"]').empty();
                $('div[id="object_preview_container'+bwoid+'"]').append(json.data);
            }
        }
    });
};