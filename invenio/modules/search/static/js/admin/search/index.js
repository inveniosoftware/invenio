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


define(function(require, exports, module) {

    var $ = require('jquery')

    // load the jQueryUI required features.
    require('ui/sortable')
    require('ui/draggable')
    require('ui/droppable')

    var defaults = {
        url: {
            modifycollectiontree: "#required"
        },
        message: {
            invalid: "Invalid tree modification.",
            panic: "Server error'd. Please refresh the page."
        },
        revert: function(item, sthis) {
            return false
        }
    }

    module.exports = function(config) {
        config = $.extend("deep", {}, defaults, config)

        /*
         * Callback for drop event.
         *
         * ui: jquery-ui prepared ui object.
         * index: new index of the collection.
         * sthis: sortable source object.
         */
        function drop_callback(ui, index, sthis) {
            // Makes the ajax request
            $.ajax(config.url.modifycollectiontree, {
                statusCode: {
                    406: function() {
                        alert(config.message.invalid)
                        $(ui.item).hide('shake', {times: 2}, 200, function() {
                            if (sthis !== null) {
                                $(sthis).sortable('cancel')
                            } else {
                                $(ui.item).hide()
                            }
                        })
                        return false
                    },
                    500: function() {
                        alert(config.message.panic)
                        return false
                    }
                },
                type: 'POST',
                data: $.param({
                    id_son: $(ui.item).attr("data-id-son"),
                    id_dad: $(ui.item).attr("data-id-dad"),
                    id_new_dad: $(ui.item).parent().attr("data-id"),
                    score: index,
                    type: $(ui.item).attr("data-type")
                })
            }).done(function(data) {
                $(ui.item).attr("data-id-dad", $(ui.item).parent().attr("data-id"))
            })
        }

        // Drag and drop JS code for manipulating collections.

        $(".sortable").sortable({
            connectWith: ".connectedSortable",
            placeholder: 'invenio-state-highlight',
            revert: true,
            distance: 30,
            delay: 200,
            cursor: "move",
            helper: function(event, elt) {
                if (event.shiftKey) {
                    /*
                     * Clone the object while SHIFT key is pressed during dragging.
                     */
                    var l = $(elt).clone()
                    $(elt).after(l)
                    $(elt).attr('data-id-dad', 0)
                    return elt
                } else {
                    return elt
                }
            },
            stop: function(event, ui) {
                drop_callback(ui, ui.item.index(), this)
            }
        }).disableSelection()

        /*
         * BEWARE: it's important to connect only with parent
         * sortable because of their nesting the event is cloned
         * to all connected lists.
         */
        $(".draggable li").draggable({
            connectToSortable: "ul.connectedSortable[data-id=1]",
            cursor: "move",
            helper: "clone",
            distance: 30,
            delay: 200,
            revert: "invalid"
        })

        $(".droppable").droppable({
            hoverClass: "invenio-state-active",
            accept: ".sortable li",
            activeClass: "invenio-state-highlight",
            drop: function(event, ui) {
                ui.item = ui.draggable
                drop_callback(ui, 0, null)
                $(ui.item).remove()
                ui.item = null
                $(this).find(".placeholder").remove()
                return false
            }
        })
    }
})
