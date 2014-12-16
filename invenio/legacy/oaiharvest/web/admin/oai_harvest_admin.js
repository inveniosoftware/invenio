/*
 * This file is part of Invenio.
 * Copyright (C) 2010, 2011, 2012, 2014 CERN.
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

function has_placeholder_support() {
    var input = document.createElement('input');
    return ('placeholder' in input);
}

function prefill_boxes() {
    /* Find all of the boxes with class 'placeholder' having attribute 'placeholder=...
       and set their value to be the placeholder. Then add handlers to them:
       on focus, check whether value = placeholder and blank it if it is;
       on focus lost, check whether value = blank and set to prefill if it is
     */
    var i, to_fill;
    i = 0;
    to_fill = document.getElementsByClassName('placeholder');
    for (i = 0; i < to_fill.length; i++) {
        to_fill[i].value = to_fill[i].getAttribute('placeholder');
        function blank_placeholder__on_focus(e) {
            if (this.value === this.getAttribute('placeholder')) {
                this.value = '';
                this.classList.toggle('placeholder_default_text');
            }
        }
        function placeholder_blank_on_blur(e) {
            if (this.value === '') {
                this.value = this.getAttribute('placeholder');
                this.classList.toggle('placeholder_default_text');
            }
        }
        to_fill[i].onblur = placeholder_blank_on_blur;
        to_fill[i].onfocus = blank_placeholder__on_focus;
    }
}

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
                           });
            }
        });
});

$(document).ready(function(){
    if (!has_placeholder_support()) {
        prefill_boxes();
    } else {
        // HTML5 takes over - remove styling for 'old' style placeholder
        $('.placeholder_default_text').toggleClass('placeholder_default_text');
    }

    $('input[id^=post_input]').each(function() {
        var div_id = $(this).attr('id').replace('post_input', 'post_args');
        if ($('#'+div_id).html() != "") {
            $('#'+div_id).toggle(this.checked);
        } else {
            $('#'+div_id).hide();
        }
    });

    $('input[id^=post_input]').click(function(){
        var div_id = $(this).attr('id').replace('post_input', 'post_args');
        if ($('#'+div_id).html() != "") {
            $('#'+div_id).toggle(this.checked);
        }
    });
});
