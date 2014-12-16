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

/*
  Supporting operations on a clipoard
 */

var useLocalClipboard = false;
var localClipboardContent = "";

function initClipboardLibrary(){
  /** Initialisation of the clipboard - creating an appropriate entry*/
  // building the DOM elements
  var layer = document.createElement('div');
  var iframe = document.createElement('iframe');
  iframe.setAttribute("id", "clipboardEditArea");
  iframe.setAttribute("style", "width:1 px; height: 1px; border-width:0px;");
  var parentNode = $('.bibEditMenuSection')[0];
  // positioning the elements
  layer.appendChild(iframe);
  parentNode.insertBefore(layer, parentNode.firstChild);
  $("#clipboardEditArea")[0].contentWindow.document.designMode="on";
}

function clipboardCopyValue(val){
  /**
     Copies a value into the clipboard
  */
  if (!useLocalClipboard){
    try{
      netscape.security.PrivilegeManager.enablePrivilege("UniversalXPConnect");
      $("#clipboardEditArea")[0].contentWindow.document.designMode="on";
      doc = document.getElementById("clipboardEditArea").contentWindow.document;
      doc.designMode="on";
      doc.body.textContent = val;
      doc.execCommand("SelectAll", false, null);
      $("#clipboardEditArea")[0].focus();
      doc.execCommand("Copy", false, null);
    } catch(err){
      // we probably do not have permissions to use the clipboard ...
      // it requires the configuration modification orsigning the code
      useLocalClipboard = true;
    }
  }
  if (useLocalClipboard){
    localClipboardContent = val;
  }
}

function clipboardPasteValue(){
  /**
     Pastes a value from the clipboard
  */
  if (!useLocalClipboard){
    try{
      netscape.security.PrivilegeManager.enablePrivilege("UniversalXPConnect");
      $("#clipboardEditArea")[0].contentWindow.document.designMode = "on";
      $("#clipboardEditArea")[0].focus();
      doc = document.getElementById("clipboardEditArea").contentWindow.document;
      doc.body.innerHTML = "";
      doc.execCommand("SelectAll", false, null);
      doc.execCommand("Paste", false, null);
      return doc.body.textContent.replace(/\n/g," ");
    }
    catch (err){
      useLocalClipboard = true;
    }
  }
  // in this case we are sure to use the local clipboard
  return localClipboardContent;
}
