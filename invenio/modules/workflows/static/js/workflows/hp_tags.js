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
var WORKFLOWS_HP_TAGS = function ( $, holdingpen ){
    var tagList = [];
    var oTable = holdingpen.oTable;

    var init = function () {

        $('.task-btn').on('click', function(){
            if($.inArray($(this)[0].name, tagList) <= -1){
                var widget_name = $(this)[0].name;
                $('#tagsinput').tagsinput('add', $(this)[0].name);
                tagList.push($(this)[0].name);
                WORKFLOWS_HP_UTILITIES.requestNewObjects();
            }
            else{
                closeTag(widget_name);
                oTable.fnFilter( '^$', 4, true, false );
                oTable.fnDraw(false);
            }
        });


        $('.version-selection').on('click', function(){
            if($.inArray($(this)[0].name, tagList) <= -1){
                $('#tagsinput').tagsinput('add', $(this)[0].name);
                tagList.push($(this)[0].name);
                WORKFLOWS_HP_UTILITIES.requestNewObjects();
            }
        });

        $("#tagsinput").on('itemRemoved', function(event) {
            tagList.splice(tagList.indexOf(event.item), 1);
            console.log('item removed : '+event.item);
            oTable.fnFilter('');
            WORKFLOWS_HP_UTILITIES.requestNewObjects();
        });

        $("#tagsinput").on('itemAdded', function(event){
            console.log(tagList);
            console.log(event.item);
            if(event.item != 'Halted' && event.item != 'Final' && event.item != 'Running'){
                oTable.fnFilter(event.item);
            }
        });
    };

    var closeTag = function (tag_name){
        console.log(tag_name);
        tagList.splice(tagList.indexOf(tag_name), 1);
        $('#tagsinput').tagsinput('remove', tag_name);
        console.log($("#tagsinput").tagsinput('items'));
        WORKFLOWS_HP_UTILITIES.requestNewObjects();
    };

    return {
        init: init,
        tagList: tagList,
        closeTag: closeTag,
    };
}($, WORKFLOWS_HOLDINGPEN);
//***********************************