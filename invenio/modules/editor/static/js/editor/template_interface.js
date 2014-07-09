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

/*
 * This is BibEdit's template interface JavaScript.
 */


/*
 * **************************** 1. Initialization ******************************
 */

window.onload = function(){
  if (typeof(jQuery) == 'undefined'){
    alert('ERROR: jQuery not found!\n\n' +
    'The Record Editor requires jQuery, which does not appear to be ' +
    'installed on this server. Please alert your system ' +
    'administrator.\n\nInstructions on how to install jQuery and other ' +
    "required plug-ins can be found in Invenio's INSTALL file.");
  }
};

$(function(){
  /*
   * Initialize all components.
   */
  initAjax();
  createTemplateList();
  bindEditTemplateHandlers();
});

/*
 * **************************** 2. AJAX ******************************
 */

function initAjax(){
  /*
   * Initialize Ajax.
   */
  $.ajaxSetup(
    {cache: false,
      dataType: 'json',
      error: onAjaxError,
      type: 'POST',
      url: '/'+ gSITE_RECORD +'/edit/templates'
    }
  );
}

function createReq(data, onSuccess, asynchronous){
  /*
   * Create Ajax request.
   */
  if (asynchronous == undefined){
    asynchronous = true;
  }
  $.ajax({data: {jsondata: JSON.stringify(data)},
           success: function(json){
                      onAjaxSuccess(json, onSuccess);
                    },
           async: asynchronous
  });
}

function onAjaxError(XHR, textStatus, errorThrown){
  /*
   * Handle Ajax request errors.
   */
  alert('Request completed with status ' + textStatus +
    '\nResult: ' + XHR.responseText +
    '\nError: ' + errorThrown);
}

function onAjaxSuccess(json, onSuccess){
  /*
   * Handle server response to Ajax requests, in particular error situations.
   * See BibEdit config for result codes.
   * If a function onSuccess is specified this will be called in the end,
   * if no error was encountered.
   */
  var resCode = json['resultCode'];
  if (resCode == 100){
      // User's session has timed out.
      gRecID = null;
      gRecIDLoading = null;
      window.location = gSITE_URL + '/'+ gSITE_RECORD +'/templates';
      return;
  }
  else if (resCode == 1){
      $('#bibEditTemplateEdit').html('There was an error with AJAX');
  }

   if (onSuccess)
      // No critical errors; call onSuccess function.
      onSuccess(json);

}

/*
 * **************************** 3. Bindings ******************************
 */

function bindEditTemplateHandlers() {
    /*
     * Bind template links to display its content once the user clicks
     */
    for (var i=0, n=gRECORD_TEMPLATES.length; i<n; i++)
    $('#lnkEditTemplateRecord_' + i).bind('click', function(event){
      var templateNo = this.id.split('_')[1];
      createReq({requestType: 'editTemplate',
 templateFilename: gRECORD_TEMPLATES[templateNo][0]}, function(json){
   editTemplate(json['templateMARCXML']);
      });
      event.preventDefault();
    });
}


/*
 * **************************** 4. Other functions ******************************
 */


function editTemplate(recordMARCXML){
    /*
     * Display the template content in the appropriate textbox
     */
    $('#bibEditTemplateEdit').html('<div style="margin:10px 0px 0px 10px;">\n\
                                    <textarea id="marcxml" rows="40" cols="80">' +
                                    recordMARCXML + '</textarea></div><br />\n\
                                    <b>Note:</b> Modifications to these templates will\n\
                                    be possible later; for the time being, please send\n\
                                    your desired changes to developers.');
}