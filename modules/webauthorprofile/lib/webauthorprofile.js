/*
 * This file is part of Invenio.
 * Copyright (C) 2009, 2010, 2011 CERN.
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

$(document).ready(function() {
    $('[class^=more-]').hide();

    $('[class^=lmore]').each(function() {
        $(this).click(function () {
            var link_class = $(this).prop("className");
            var content = $("." + "more-" + link_class);
            if (content.hasClass("hidden")) {
                content.removeClass("hidden").slideDown();
                $(this).html("<img src='/img/aid_minus_16.png' alt='hide information' width='11' height='11'> less");
            }
            else {
              content.addClass("hidden").slideUp();
              $(this).html("<img src='/img/aid_plus_16.png' alt='toggle additional information.' width='11' height='11'> more");
            }
        return false;
        });
    });
});
    
function initAjax(){
  /*
   * Initialize Ajax.
   */
  $.ajaxSetup(
    {cache: false,
      dataType: 'json',
      type: 'POST',
      url: '.'
    }
  );
}

function add_box_content(id, html_content) {
    $('#' + id).html(html_content);
}

function onAjaxSuccess(json) {
    /* Get info about boxes to update */
    gBOX_STATUS = json['boxes_info'];
    var stop_ping = true;
    for (var box_id in gBOX_STATUS) {
        var box_info = gBOX_STATUS[box_id];
        if (box_info['status'] == true)
            add_box_content(box_id, box_info['html_content'])
        else
            stop_ping = false;
    }
    if (stop_ping == true)
        stopPing();
}

function prepare_json_data() {
  data = {
    box_status: gBOX_STATUS
  };
  return data;
}

function createReq() {
    /*
     * Perform AJAX request and update page content
     */
    var data = prepare_json_data();
    $.ajax({data: {jsondata: JSON.stringify(data)},
            success: function(json){
                      onAjaxSuccess(json);
            }
    });
}

function stopPing() {
    /*
     * Stop ping to server
     */
    clearInterval(intervalId);
}

function initPing() {
    /*
     * Specify the interval to ping the server
     */
    intervalId = setInterval("createReq()", 2500);
}



$(function(){
    /*
     * Init functions
     */
    initAjax();
    if (gBOX_STATUS != 'noAjax') {
        initPing();
    	setTimeout("stopPing()", 360000);
    }
});
