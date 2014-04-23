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

    //call name variants
    data = { 'personId': gPID };
    funcs = ['create_authorpage_name_variants', 'create_authorpage_combined_papers', 'create_authorpage_keywords', 'create_authorpage_fieldcodes', 'create_authorpage_affiliations',
                 'create_authorpage_coauthors', 'create_authorpage_citations', 'create_authorpage_pubs_graph',
                 'create_authorpage_hepdata', 'create_authorpage_collaborations', 'create_authorpage_pubs_list'];
    funcsLength = funcs.length;
    var count = Math.min( gNumOfWorkers, funcs.length);
    xhrPool = [];
    // Send gNumofWorkers requests to server
    // For every response we get, we send a new request, in order the server to serve maximum gNumofWorkers requests
    for (currentFunc=0; currentFunc < count; currentFunc++) {
      createReq(funcs[currentFunc]);
    }
    setTimeout("cancelPendingRequests()", gPageTimeout);
});

function isProfile() {
    var profileMatch = /profile=/;
    return profileMatch.test(window.location.search);
}

function createReq( calledFunc ) {
  /* Prepare and send ajax requests */
  var errorCallback = onAjaxError(calledFunc);
  $.ajax({
    cache: false,
    dataType: 'json',
    type: 'POST',
    url: '/author/profile/' + calledFunc,
    data: isProfile() ? {jsondata: JSON.stringify(data), ajaxProfile: true} : {jsondata: JSON.stringify(data)},
    success: onAjaxSuccess,
    error: errorCallback,
    timeout: gReqTimeout,
    beforeSend: function(jqXHR) { // before jQuery send the request we will push it to our array
        xhrPool.push(jqXHR);
    },
    complete: function(jqXHR) { // when a request is completed it will be removed from the array
        xhrPool = $.grep(xhrPool, function(x){return x!=jqXHR;});
    }
  });
}

function add_box_content(id, html_content) {
    var $box = $('#' + id);
    $box.html(html_content);
    $box.find('[class^=more-]').hide();
    $box.find('[class^=lmore]').each(function() {
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
    if (id == "pubs_list") {
        MathJax.Hub.Queue(["Typeset", MathJax.Hub, $box.get(0)]);
        $(".pub-tabs a:first").tab('show');
    }
}

function onAjaxSuccess(json) {
    /* Get info about boxes to update */
    gBOX_STATUS = json['boxes_info'];
    for (var box_id in gBOX_STATUS) {
        var box_info = gBOX_STATUS[box_id];
        if (box_info['status'] === true) {
            if (json.hasOwnProperty("profilerStats")) {
                box_info['html_content'] += "<div class=\"profiler-stats\">" + json['profilerStats'] + "</div>";
            }
            add_box_content(box_id, box_info['html_content']);
        }

    }
    if ( currentFunc < funcsLength ) {
      createReq(funcs[currentFunc]);
      currentFunc++;
    }


}

function onAjaxError(func) {
  /*
   * Handle failed ajax requests.
   */
   return function (XHR, textStatus, errorThrown) {
      var callFunc = func;
      if ( textStatus === "timeout") {
        createReq(callFunc);
      }
      else {}// todo
   };
}

function cancelPendingRequests() {
  /* Cancel all pending requests and display proper message on the loading boxes*/
  $.each( xhrPool, function( index, jqXHR){
    jqXHR.abort();
  });
  $('.loadingGif').each( function(){
    $(this).siblings('span').remove();
    $(this).replaceWith("<span>Data could not be retrieved</span>");
  });
}
