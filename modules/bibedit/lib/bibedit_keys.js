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
 * This is the BibEdit Javascript for handling keyboard shortcuts, here after
 * called hotkeys.
 */

/*
 * Global variables
 */

var gSelectionModeOn = false;
var gReady = true;

function initInputHotkeys(input_element) {
    /* Binding of shortcuts for input elements */

    // Lauch autosuggest
    $(input_element).bind('keydown', 'ctrl+shift+a', function (event)  { onAutosuggest(event); } );
    // Save content and jump to next content field.
    $(input_element).bind('keydown', 'tab', onKeyTab);
    // Save content and jump to previous content field.
    $(input_element).bind('keydown', 'shift+tab', onKeyTab);
    // Add subfield in form.
    $(input_element).bind('keydown', 'ctrl+shift+e', onKeyCtrlShiftE);
    // Remove subfield from form.
    $(input_element).bind('keydown', 'ctrl+shift+d', onKeyCtrlShiftD);
}

function initHotkeys() {
  /*
   * Initialize non-input hotkeys.
   * Using https://github.com/jeresig/jquery.hotkeys
   *
   * Plugin notes:
   * If you want to use more than one modifiers (e.g. alt+ctrl+z) you should
   * define them by an alphabetical order e.g. alt+ctrl+shift
   *
   * Hotkeys aren't tracked if you're inside of an input element (use function
   * initInputHotkeys)
   */
  // New record.
  $(document).bind('keydown', 'shift+n', function(event) {
      $('#imgNewRecord').trigger('click');
      event.preventDefault();
  });
  // Clone record.
  $(document).bind('keydown', 'shift+l', function(event) {
      var imgCloneRecord = $('#imgCloneRecord');
      if (!imgCloneRecord.hasClass('bibEditImgFaded')) {
	imgCloneRecord.trigger('click');
	event.preventDefault();
      }
  });
  // Focus on record selection field.
  $(document).bind('keydown','g', function(event) {
      $('#txtSearchPattern').focus();
      event.preventDefault();
  });
  // Previous record.
  $(document).bind('keydown', 'ctrl+right', function(event) {
      var btnNext = $('#btnNext');
      if (!btnNext.attr('disabled')) {
	btnNext.trigger('click');
	event.preventDefault();
      }
  });
  // Next record.
  $(document).bind('keydown', 'ctrl+left', function(event) {
      var btnPrev = $('#btnPrev');
      if (!btnPrev.attr('disabled')) {
	btnPrev.trigger('click');
	event.preventDefault();
      }
  });
  // Submit record.
  $(document).bind('keydown','shift+s', function(event) {
      var btnSubmit = $('#btnSubmit');
      if (!btnSubmit.attr('disabled')) {
	btnSubmit.trigger('click');
	event.preventDefault();
      }
  });
  // Cancel editing.
  $(document).bind('keydown','shift+c', function(event) {
      var btnCancel = $('#btnCancel');
      if (!btnCancel.attr('disabled')){
	btnCancel.trigger('click');
	event.preventDefault();
      }
  });
  // Toggle MARC/human tags.
  $(document).bind('keydown','shift+t', function(event) {
      if (gTagFormat == 'MARC') {
	var btnHumanTags = $('#btnHumanTags');
	if (!btnHumanTags.attr('disabled')){
	  btnHumanTags.trigger('click');
	  event.preventDefault();
	}
      }
      else if (gTagFormat == 'human') {
	var btnMARCTags = $('#btnMARCTags');
	if (!btnMARCTags.attr('disabled')) {
	  btnMARCTags.trigger('click');
	  event.preventDefault();
	}
      }
  });
  // Add new field.
  $(document).bind('keydown', 'a', function(event) {
      var btnAddField = $('#btnAddField');
      if (!btnAddField.attr('disabled')) {
	btnAddField.trigger('click');
	event.preventDefault();
      }
  });
  // Delete selected field(s).
  $(document).bind('keydown', 'del', function(event) {
      var btnDeleteSelected = $('#btnDeleteSelected');
      if (!btnDeleteSelected.attr('disabled')) {
	onDeleteClick(event);
	event.preventDefault();
      }
  });

  // Toggle 'selection mode'.
  $(document).bind('keydown', 'alt+s', onKeyAltS);
  // Edit focused subfield.
  $(document).bind('keydown', 'return',
		   onKeyReturn);
  // Move selected field/subfield up.
  $(document).bind('keydown', 'ctrl+up', onKeyCtrlUp);
  // Move selected field/subfield down.
  $(document).bind('keydown', 'ctrl+down', onKeyCtrlDown);
  // Binding the undo/redo operations
  $(document).bind('keydown', 'ctrl+shift+z', onUndo);
  $(document).bind('keydown', 'ctrl+shift+y', onRedo);
}

function onKeyAltS(event) {
  /*
   * Handle key 'alt+s' (toggle selection mode).
   */
  if (gRecID){
    if (gSelectionModeOn){
      $('#bibEditContentTable td').unbind('mouseover');
      gSelectionModeOn = false;
      updateStatus('report', 'Selection mode: Off');
    }
    else{
      $('#bibEditContentTable td').bind('mouseover', function(event){
       var targetID = event.target.id;
       if (targetID.slice(0, targetID.indexOf('_')) == 'fieldTag' &&
           !$(event.target).hasClass('bibEditSelected')) {
          onSelectHandle(event);
       }
      });
      gSelectionModeOn = true;
      updateStatus('report', 'Selection mode: On');
    }
    if (!event.isDefaultPrevented())
      event.preventDefault();
  }
}

function onSelectHandle(event) {
  /*
   * On selection mode, decide whether to select or not a whole field
   */
  if (event.target.nodeName == 'TD') {
    var targetID = event.target.id;
    var type = targetID.slice(0, targetID.indexOf('_'));
    if (type == 'fieldTag'){
      var id = targetID.slice(targetID.indexOf('_') + 1);
      var box = $('#boxField_' + id).get(0);

      if ($('#boxField_' + id).is(':checked')) {
        $('#boxField_' + id).attr("checked", false);
      }
      else {
        $('#boxField_' + id).attr("checked", true);
      }

      var rowGroup = $('#rowGroup_' + box.id.slice(box.id.indexOf('_') + 1));
      if (box.checked) {
        $(rowGroup).find('td[id^=content]').andSelf().addClass('bibEditSelected');
        if (gReadOnlyMode == false) {
          $('#btnDeleteSelected').removeAttr('disabled');
        }
      }
      else {
        $(rowGroup).find('td[id^=content]').andSelf().removeClass(
          'bibEditSelected');
        if (!$('.bibEditSelected').length)
          // Nothing is selected, disable "Delete selected"-button.
          $('#btnDeleteSelected').attr('disabled', 'disabled');
      }
      $(rowGroup).find('input[type="checkbox"]').attr('checked', box.checked);
    }
  }
}


function onKeyReturn(event) {
  /*
   * Handle key return (edit subfield).
   */
  if (event.target.nodeName == 'TEXTAREA') {
    $(event.target).parent().submit();
    event.preventDefault();
  }
  else if (event.target.nodeName == 'TD') {
    var targetID = event.target.id;
    var type = targetID.slice(0, targetID.indexOf('_'));
    if (type == 'content'){
      $('#' + targetID).trigger('click');
      event.preventDefault();
    }
  }
}

function onKeyTab(event){
  /*
   * Handle key tab (save content and jump to next content field).
   */
  if (event.target.nodeName == 'TEXTAREA'){
    var contentCells = $('.bibEditCellContent');
    var cell = $(event.target).parent().parent();
    var foo = $(event.target).parent();
    foo.submit();
    if (!event.shiftKey) {
      $(contentCells).eq($(contentCells).index(cell)+1).trigger('click');
    }
    else {
      $(contentCells).eq($(contentCells).index(cell)-1).trigger('click');
    }
    event.preventDefault();
  }
}

function onKeyCtrlUp(event) {
  /*
   * Handle key ctrl+up (move subfield up).
   */
  if (gReady==false)
    return;
  gReady = false;
  // check if we want to move a field or subfield
  var selectedFields = $('#bibEditTable tbody.bibEditSelected');
  var selectedSubfields = $('#bibEditTable td.bibEditSelected');
  //move unique selected field
  if (selectedFields.length == 1) {
    var targetID = selectedFields.eq(0).attr('id');
    var targetInfo = targetID.split('_');
    var tag = targetInfo[1], fieldPos = targetInfo[2];
    onMoveFieldUp(tag, fieldPos);
  }
  else if (selectedSubfields.length == 1) {// move subfield
    var targetID = selectedSubfields.eq(0).attr('id');
    var tmpArray = targetID.split('_');
    if (tmpArray[0] == 'content'){
      var tag = tmpArray[1], fieldPos = tmpArray[2], subfieldIndex = tmpArray[3];
      onMoveSubfieldClick('up', tag, fieldPos, subfieldIndex);
    }
  }
  event.preventDefault();
  gReady = true;
}

function onKeyCtrlDown(event) {
  /*
   * Handle key ctrl+down (move subfield down).
   */
  if (gReady==false)
    return;
  gReady = false;
  // check if we want to move a field or subfield
  var selectedFields = $('#bibEditTable tbody.bibEditSelected');
  var selectedSubfields = $('#bibEditTable td.bibEditSelected');
  //move unique selected field
  if (selectedFields.length == 1) {
    var targetID = selectedFields.eq(0).attr('id');
    var targetInfo = targetID.split('_');
    var tag = targetInfo[1], fieldPos = targetInfo[2];
    onMoveFieldDown(tag, fieldPos);
  }
  else if (selectedSubfields.length == 1) {// move subfield
    var targetID = selectedSubfields.eq(0).attr('id');
    var tmpArray = targetID.split('_');
    if (tmpArray[0] == 'content'){
      var tag = tmpArray[1], fieldPos = tmpArray[2], subfieldIndex = tmpArray[3];
      onMoveSubfieldClick('down', tag, fieldPos, subfieldIndex);
    }
  }
  event.preventDefault();
  gReady = true;
}

function onKeyCtrlShiftE(event) {
  /*
   * Handle key 'Ctrl+Shift+e' (add subfield to form).
   */
  var nodeName = event.target.nodeName;
  if (nodeName == 'TD' || nodeName == 'INPUT' || nodeName == 'BUTTON' ||
      nodeName == 'TEXTAREA'){
    var rowGroup = $(event.target).closest('tbody')[0];
    if (rowGroup){
      var btnAddSubfield;
      if (rowGroup.id.indexOf('rowGroupAddField')+1) {
	// Add extra subfield to 'Add field' form.
	var fieldID = rowGroup.id.slice(rowGroup.id.indexOf('_')+1);
	if (!$('#chkAddFieldControlfield_' + fieldID).attr('checked'))
	  btnAddSubfield = $('#btnAddFieldAddSubfield_' + fieldID);
      }
      else if (rowGroup.id.indexOf('rowGroup')+1)
	// Add extra subfield to 'Add subfields' form.
	btnAddSubfield = $('#btnAddSubfield_' + rowGroup.id.slice(
			   rowGroup.id.indexOf('_')+1));
      if (btnAddSubfield){
	$(btnAddSubfield).trigger('click');
	event.preventDefault();
      }
    }
  }
}

function onKeyCtrlShiftD(event) {
  /*
   * Handle key 'Ctrl+Shift+d' (remove subfield from form).
   */
  var nodeName = event.target.nodeName;
  if (nodeName == 'TD' || nodeName == 'INPUT' || nodeName == 'BUTTON' ||
      nodeName == 'TEXTAREA'){
    var rowGroup = $(event.target).closest('tbody')[0];
    if (rowGroup){
      var fieldID, tmpNo, btnRemoveSubfield;
      if (rowGroup.id.indexOf('rowGroupAddField')+1) {
	// Remove extra subfield from 'Add field' form.
	fieldID = rowGroup.id.slice(rowGroup.id.indexOf('_')+1);
	tmpNo = $('#rowGroupAddField_' + fieldID).data('freeSubfieldTmpNo')-1;
	btnRemoveSubfield = $('#btnAddFieldRemove_' + fieldID + '_' + tmpNo);
	while (!btnRemoveSubfield.length && tmpNo >= 1){
	  tmpNo--;
	  btnRemoveSubfield = $('#btnAddFieldRemove_' + fieldID + '_' + tmpNo);
	}
      }
      else if (rowGroup.id.indexOf('rowGroup')+1) {
	// Remove extra subfield from 'Add subfields' form.
      	fieldID = rowGroup.id.slice(rowGroup.id.indexOf('_')+1);
	tmpNo = $('#rowGroup_' + fieldID).data('freeSubfieldTmpNo')-1;
	btnRemoveSubfield = $('#btnAddSubfieldsRemove_' + fieldID + '_' +
			      tmpNo);
	while (!btnRemoveSubfield.length && tmpNo > 1) {
	  tmpNo--;
	  btnRemoveSubfield = $('#btnAddSubfieldsRemove_' + fieldID + '_' +
				tmpNo);
	}
      }
      if (btnRemoveSubfield.length) {
	       $(btnRemoveSubfield).trigger('click');
	       event.preventDefault();
      }
    }
  }
}
