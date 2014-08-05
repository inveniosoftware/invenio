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


define(function(require, exports, module) {
    "use strict";

    var $ = require("jquery")

    require('ui/autocomplete')
    require('ui/datepicker')
    require('jqueryui-timepicker/jquery-ui-sliderAccess')
    require('jqueryui-timepicker/jquery-ui-timepicker-addon')
    // Uncomment once the language pick is not the default one
    //require('jqueryui-timepicker/i18n/jquery-ui-timepicker-addon-i18n')

    function split(val) {
        return val.split(/,\s*/);
    }

    function extractLast(term) {
        return split(term).pop();
    }

    module.exports = function(config) {
        config = $.extend({}, {
            selector: {
                sent_to_user_nicks: "#sent_to_user_nicks",
                sent_to_group_names: "#sent_to_group_names",
                datepicker: "input.datepicker",
                datetimepicker: "input.datetimepicker",
                timepicker: "input.timepicker"
            },
            format: {
                date: 'yy-mm-dd',
                time: 'hh:mm:ss'
            },
            url: {
                search: "#required"
            },
            lang: 'N/A'
        }, config)

        // addon-i18n must be enabled above.
        //$.timepicker.setDefaults($.timepicker.regional[config.lang])

        var autocomplete = {
            minLength: 3,
            selectLast: function(event, ui) {
                var terms = split(this.value);
                terms.pop();
                terms.push(ui.item.value);
                terms.push("");
                this.value = terms.join(", ");
                return false;
            }
        }

        $(config.selector.sent_to_user_nicks).autocomplete($.extend({
            source: function(request, response) {
                $.ajax({
                    url: config.url.search,
                    data: {
                        query: "users",
                        term: extractLast(request.term)
                    },
                    focus: function() {
                        return false
                    },
                    success: function(data, textStatus, jqXHR){
                        response(data.nicknames)
                    }
                })
            }
        }, autocomplete))

        $(config.selector.sent_to_group_names).autocomplete($.extend({
            source: function(request, response) {
                $.ajax({
                    url: config.url.search,
                    data: {
                        query: "groups",
                        term: extractLast(request.term)
                    },
                    focus: function() {
                        return false
                    },
                    success: function(data, textStatus, jqXHR){
                        response(data.groups)
                    }
                })
            }
        }, autocomplete))

        $(config.selector.datepicker).datepicker({
            dateFormat: config.format.date
        })

        $(config.selector.datetimepicker).datetimepicker({
            showSecond: true,
            dateFormat: config.format.date,
            timeFormat: config.format.time
        })

        $(config.selector.timepicker).timepicker({
            timeFormat: config.format.time,
            showSecond: true
        })
    }
})
