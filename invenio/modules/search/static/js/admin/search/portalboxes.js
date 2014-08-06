/*
 * This file is part of Invenio.
 * Copyright (C) 2014 CERN.
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


// FIXME
define(function(require, exports, module) {

    var $ = require('jquery')

    require('ui/sortable')

    module.exports = function(config) {
        $( "#sortable" ).sortable({
            cursor: "'move",
            stop: function(event, ui) {
                $.ajax(config.url, {
                    type: 'GET',
                    data: $.param({
                        id: $(ui.item).attr("data-id"),
                        id_collection: $(ui.item).parent().attr("data-id"),
                        score: ui.item.index()
                    })
                }).success(function(data) {
                    console.log(data)
                }).error(function() {
                    alert("Error!")
                })
            }
        })

        /*$("a.modalloader").each(
        $(this).click(function(){
            $.ajax( '{{url_for('.edit_portalbox')}}', {
                type: 'GET',
                data: 'id='+ $(ui.item).attr("data-id")
              }
            ).done(function(data) {});
          });
        );*/
    }
})
