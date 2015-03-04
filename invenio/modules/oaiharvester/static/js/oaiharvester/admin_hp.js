/*
 * This file is part of Invenio.
 * Copyright (C) 2010, 2011 CERN.
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


function buildPager(data){
    $("#" + data.pagerId).ajaxPager({
        previous: true, // previous page link is going to be displayed
        previousText: "&lsaquo; prev",   // prevous page link text
        next: true,             // whether to display a next page link
        nextText: "next &rsaquo;",       // next page link text
        first: true,            // whether to display a first page link
        firstText: "&laquo; first",// first page link text
        last: true,             // whether to display a last page link
        lastText: "last &raquo;", // last page link text
        linkPagesStart: 1,      // number of page links at start
        linkPagesBefore: 2,     // number of page links before current page
        linkPagesAfter: 4,      // number of page links after current page
        linkPagesEnd: 1,        // number of page link at end
        linkPagesBreak: "...",  // text for breaks in page links
        preLoad: 4,  // how many pages to preload ahead of current page
        selector: "#page{i} .content", // css selector for ajax response and same page elements
        destroyOriginal: true,  // whether to destory to original if content from same page elements
        page: 1,                // starting page
        type: 'ajax',           // default page type
        linkOverflow: true,// whether to let wasted links from one area of the pager to be added to another
        loadingText: "<h4>Loading page...</h4>", // Text to display before page loads
        pages: data.pages
    });
}

$(document).ready(function(){
    $("#holdingpencontainer").treeview({
        animated: "fast",
        speed: 1,
        collapsed: "true",
        toggle: function(){
            if (!$(this).hasClass("loaded")){
                elementId = $(this).attr("id");
                var p = $("<li><span>Loading...</span></li>").appendTo("#" + elementId + "_ul");
                $("#holdingpencontainer").treeview({add : p});

                $.getJSON(serverAddress + "/admin/bibharvest/oaiharvestadmin.py/getHoldingPenData",
                        {elementId : $(this).attr("id")},
                        function(json){
                            $("#" + json.elementId + "_ul").empty();
                            var p = $(json.html).appendTo("#" + json.elementId + "_ul");
                            $("#holdingpencontainer").treeview({add : p});
                            $("#" + json.elementId).addClass("loaded");
                            if (json.additionalData != null){
                                buildPager(json.additionalData);
                            }
                        });
            }
        }
    })
});
