/*
 * This file is part of Invenio.
 * Copyright (C) 2010, 2011, 2012 CERN.
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

$(function() {
        $( "#holdingpencontainer" ).accordion({collapsible: true, autoHeight: false});
        $( "#holdingpencontainer > div" ).accordion({collapsible: true, autoHeight: false});
        $( "#holdingpencontainer > div > div" ).accordion({collapsible: true, active: false, autoHeight: false, clearStyle: true});

        $( "#holdingpencontainer > div > div").bind("accordionchangestart", function(event, ui) {
            console.dir(ui.newHeader); // jQuery, activated header
            console.dir(ui.oldHeader); 
            if(ui.newHeader[0]){
                console.log(ui.newHeader[0].id); //this has the id attribute of the header that was clicked
                elementId = ui.newHeader[0].id;
            

                $(elementId).next().empty().append("<p>Loading...</p>");

                $.getJSON(serverAddress + "/admin/oaiharvest/oaiharvestadmin.py/getHoldingPenData",
                          {elementId : elementId},
                           function(json){
                               $("#" + json.elementId).next().empty();
                               $("#" + json.elementId).next().append(json.html);
                               //$("#" + json.elementId).next().css({'height': $("#" + json.elementId).next().find('.brtable').eq(0).height()}).page();
                               //console.log($("#" + json.elementId).next().find('.brtable').eq(0).height());
                           });
            }
        });
});

