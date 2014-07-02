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

// Tags functions
//***********************************
var WORKFLOWS_HP_TAGS = function ($, holdingpen) {
    "use strict";
    var tagList = [];

    $("#tags").tagsinput({
        tagClass: function (item) {
            switch (item) {
            case 'In process':
                return 'label label-warning';
            case 'Need action':
                return 'label label-danger';
            case 'Done':
                return 'label label-success';
            case 'New':
                return 'label label-info';
            default:
                return 'badge badge-warning';
            }
        }
    });

    var init = function () {
        $('.task-btn').on('click', function () {
            if ($.inArray($(this)[0].name, tagList) <= -1) {
                var widget_name = $(this)[0].name;
                $("#tags").tagsinput('add', $(this)[0].text);
                WORKFLOWS_HP_UTILITIES.requestNewObjects();
            } else {
                closeTag(widget_name);
                holdingpen.oTable.fnFilter('^$', 4, true, false);
                holdingpen.oTable.fnDraw(false);
            }
        });

        $('#option-autorefresh').on('click', function () {
             console.log($('#option-autorefresh').hasClass("btn-danger"));
             if($('#option-autorefresh').hasClass("btn-danger")) {
                $('#option-autorefresh').removeClass("btn-danger");
             } else {
                $('#option-autorefresh').addClass("btn-danger");
             }
        });

        $('.version-selection').on('click', function () {
            if ($.inArray($(this)[0].name, tagList) <= -1) {
                $('#tags').tagsinput('add', $(this)[0].text);
            }
        });

        $("#tags").on('itemRemoved', function (event) {
            tagList = $("#tags").val().split(',');
            tagList = taglist_translation(tagList);
            WORKFLOWS_HP_UTILITIES.requestNewObjects();
            holdingpen.oTable.fnDraw(false);
        });

        $("#tags").on('itemAdded', function (event) {
            tagList =  $("#tags").val().split(',');
            tagList = taglist_translation(tagList);
            WORKFLOWS_HP_UTILITIES.requestNewObjects();
        });
    };

    function taglist_translation(my_taglist) {
        var i;
        for (i = 0; i <= my_taglist.length; i++) {
            if (my_taglist[i] === 'Done') {
                my_taglist[i] = 'Completed';
            } else if (my_taglist[i] === 'Need action') {
                my_taglist[i] = 'Halted';
            } else if (my_taglist[i] === 'In process') {
                my_taglist[i] = 'Running';
            } else if (my_taglist[i] === 'New') {
                my_taglist[i] = 'Initial';
            }
        }
        return my_taglist;
    }

    var closeTag = function (tag_name) {
        tagList.splice(tagList.indexOf(tag_name), 1);
        $('#tags').tagsinput('remove', tag_name);
    };

    return {
        init: init,
        tagList: function () { return tagList; },
        closeTag: closeTag
    };
}($, WORKFLOWS_HOLDINGPEN);
//***********************************