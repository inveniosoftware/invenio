/*
 * This file is part of Invenio.
 * Copyright (C) 2011, 2012 CERN.
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


/* How often to ping server for updates? (in ms) */
var PING_INTERVAL = 5000;
/* After how long of inactivity do we stop pinging the server? (in ms) */
var TIMEOUT_TIME = 120 * 1000;
/* Is the session timed out? */
var IS_SESSION_TIMEOUT = false;


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


function createReq() {
    /*
     * Perform AJAX request and update page content
     */
    $.ajax({data: {jsondata: JSON.stringify("dummy")},
        success: function(json) {
              $('#bibsched_table').html(json['bibsched']);
        }
    });
}


function onTimeout() {
    /*
     * Stop pinging the server and alert the user
     */
    var timeout_msg_html = "<br><div style='color:red;'>Your session has timed out. Refresh the page to keep seeing updates.<div>"

    clearInterval(pingTimer);
    IS_SESSION_TIMEOUT = true;

    $("#bibsched_table").after(timeout_msg_html);
}


function renewSession() {
    /*
     * There is some activity on the screen, avoid time out
     */
    clearInterval(timeoutTimer);
    if ( !IS_SESSION_TIMEOUT ) {
        timeoutTimer = setTimeout(onTimeout, TIMEOUT_TIME);
    }
}


function initBibSchedPing() {
    /*
     * Specify the interval to ping the server
     */
    timeoutTimer = setTimeout(onTimeout, TIMEOUT_TIME);
    pingTimer = setInterval("createReq()", PING_INTERVAL);
}


function bindHandlers() {
    /*
     * Definition of event handlers
     */
    $(document).on("mousemove", renewSession);
}


$(function() {
    /*
     * DOM ready. Init functions
     */
    initAjax();
    bindHandlers();
    initBibSchedPing();
});
