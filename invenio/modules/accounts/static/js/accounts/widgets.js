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
    "use strict";

    var $ = require("jquery")

    require("ui/sortable")

    var defaults = {
        url: {
            edit: "#required",
            view: "#required"
        }
    }

    module.exports = function(config) {
        config = $.extend("deep", {}, defaults, config);

        function saveWidgets() {
            var newOrderLeft = $("#widgetsLeft").sortable('toArray'),
                newOrderMiddle = $("#widgetsMiddle").sortable('toArray'),
                newOrderRight= $("#widgetsRight").sortable('toArray')

            $.ajax({
                url: config.url.edit,
                type: 'POST',
                data: $.param({
                    orderLeft: newOrderLeft,
                    orderMiddle: newOrderMiddle,
                    orderRight: newOrderRight
                }, true)
            })
        }

        function addToClosedList(title, id) {
            $("#closed-list").append(
                "<li id='" + id + "' class='btn display-widget'>" + title +
                "<i class='glyphicon glyphicon-plus'></i></li>");
            bindDisplayWidgetEvents()
        }

        function displayWidget(widgetName) {
            $.ajax({
                url: config.url.view,
                type: 'GET',
                data: $.param({
                    name: widgetName
                }, true),
                dataType: "html",
                success: function(r) {
                    $("#" + widgetName).remove();
                    // Find widgetColumn with least children
                    var $lists = $('.widgetColumn > ul').toArray(),
                        elem = $lists[
                            $lists.map(function(item, idx) {
                                return [$(item).children().length, idx]
                            }).reduce(function(pv, cv) {
                                return cv[0] < pv[0] ? cv : pv
                            })[1]]

                    $(elem).append(r)
                    saveWidgets()
                    bindWidgetEvents()
                }
            })
        }

        function bindDisplayWidgetEvents() {
            $(".display-widget").off()
                                .on("click", function() {
                displayWidget(this.id)
            })
        }

        function bindWidgetEvents() {
            $(".widget")
                .off()
                .on('mouseenter', function() {
                    $(this).find(".close.hide").removeClass("hide");
                })
                .on('mouseleave', function() {
                    $(this).find(".close").addClass("hide");
                })

            $(".close")
                .off()
                .on('click', function(event) {
                    var widget = $(event.target).closest(".widget"),
                        title = widget.find("h4").text().replace("×", " ").trim()

                    addToClosedList(title, widget.attr("id"));
                    $(this).closest("li").remove();
                    saveWidgets();
                })
        }

        $('input[name=widget]').keyup(function(e) {
            var filter = $(this).val()

            if (filter.length > 0 && e.keyCode === 13) {
                var l = $('#widgets li:visible').find('a.edit').first().attr('href')
                if (l.length > 0) {
                    window.location.href = l
                }
                return false
            }

            $('#widgets li').each(function(i, li) {
                if ($(li).find('.caption').text().indexOf(filter) > -1 || filter === '') {
                    $(this).show()
                } else {
                    $(this).hide()
                }
            })
        })

        $("#widgets li").each(function() {
            var $e = $(this)
            $e.find('.close').on('click', function() {
                $e.hide()
            })
        })

        $("#widgetsLeft, #widgetsMiddle, #widgetsRight").sortable({
            connectWith: ".connectedWidgets",
            cursor: "move",
            placeholder: "placeholder",
            forcePlaceholderSize: true,
            forceHelperSize : true,
            stop: function(event, ui) {
                saveWidgets();
            }
        }).disableSelection()

        bindDisplayWidgetEvents()
        bindWidgetEvents()
    }
})
