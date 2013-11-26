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
            success: function(json){
                          $('#bibsched_table').html(json['bibsched']);
                      }
            });
}

function initBibSchedPing() {
    /*
     * Specify the interval to ping the server
     */
    setInterval("createReq()", 5000);
}

$(function(){
    /*
     * Init functions
     */
    initAjax();
    initBibSchedPing();
});
