/*
 * This file is part of CDS Invenio.
 * Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 2009 CERN.
 *
 * CDS Invenio is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
 * License, or (at your option) any later version.
 *
 * CDS Invenio is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
 * 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
 */

/*
 * Global variables
 */

// Defines the different actions performed by AJAX calls
var gActionTypes = {
	testSearch :"testSearch",
	displayDetailedRecord :"displayDetailedRecord",
	previewResults :"previewResults",
	displayDetailedResult :"displayDetailedResult",
	submitChanges :"submitChanges"
};

// Defines the different output formats of the results
var gOutputFormatTypes = {
	bibTeX :"hx",
	marcXML :"xm",
	nlm :"xn",
	htmlBrief :"hb",
	htmlDetailed :"hd",
	marc :"hm"
};

// Defines different types of commands for manipulation of records
var gCommandTypes = {
	replaceTextInField :"replaceTextInField",
	replaceFieldContent :"replaceFieldContent",
	deleteField :"deleteField",
	addField :"addField"
};

// current action
var gActionToPerform = "";
// ID of the record that will be displayed
var gCurrentRecordID = -1;
// Keeps the commands entered by the user
var gCommands = {};
var gCurrentCommandID = 0;
var gPageToDiplay = 1;
var gDeleteCommandIDPrefix = "deleteCommandID_";
var gCommandDisplayTemplateIDPrefix = "commandDisplayTemplateID_";
var gOutputFormat = gOutputFormatTypes.htmlBrief;
var gOutputFormatDetails = gOutputFormatTypes.htmlDetailed;
var gOutputFormatPreview = gOutputFormatTypes.htmlBrief;

$(document).ready( function() {
	rebindControls();
	updateView();
});

function updateView() {
	$("#displayTemplates").hide();
}

function rebindControls() {
	/*
	 * Binds controls with the appropriate events
	 */

	rebindActionsRelatedControls();

	$("#buttonTestSearch").bind("click", onButtonTestSearchClick);
	$("#buttonPreviewResults").bind("click", onButtonPreviewResultsClick);
	$("#buttonSubmitChanges").bind("click", onButtonSubmitChangesClick);
	$(".buttonBackToResults").bind("click", onButtonBackToResultsClick);
	$(".buttonOutputFormatMarcXML").bind("click", onButtonOutputFormatMarcXMLClick);
	$(".buttonOutputFormatHTMLBrief").bind("click", onButtonOutputFormatHTMLBriefClick);
	$(".buttonOutputFormatHTMLDetailed").bind("click", onButtonOutputFormatHTMLDetailedClick);
	$(".buttonOutputFormatMARC").bind("click", onButtonOutputFormatMARCClick);
	$(".resultItem").bind("click", onResultItemClick);
	$(".buttonGoToFirstPage").bind("click", onButtonGoToFirstPageClick);
	$(".buttonGoToPreviousPage").bind("click", onButtonGoToPreviousPageClick);
	$(".buttonGoToNextPage").bind("click", onButtonGoToNextPageClick);
}


// Page in results preview
function onButtonGoToFirstPageClick(){
	gPageToDiplay = 1;
	performAJAXRequest();
}
function onButtonGoToPreviousPageClick(){
	gPageToDiplay--;
	performAJAXRequest();
}
function onButtonGoToNextPageClick(){
	gPageToDiplay++;
	performAJAXRequest();
}

function onResultItemClick() {
	/*
	 * Displays details about the record when the user click on it in the
	 * results list
	 */
	var recordID = $(this).attr("id");
	gCurrentRecordID = recordID.split("_")[1];

	if (gActionToPerform == gActionTypes.testSearch) {
		gActionToPerform = gActionTypes.displayDetailedRecord;
	} else {
		gActionToPerform = gActionTypes.displayDetailedResult;
	}

	gOutputFormat = gOutputFormatDetails;

	performAJAXRequest();
}

function onButtonOutputFormatMarcXMLClick(){
	setOutputFormat(gOutputFormatTypes.marcXML);
}
function onButtonOutputFormatHTMLBriefClick(){
	setOutputFormat(gOutputFormatTypes.htmlBrief);
}
function onButtonOutputFormatHTMLDetailedClick(){
	setOutputFormat(gOutputFormatTypes.htmlDetailed);
}
function onButtonOutputFormatMARCClick(){
	setOutputFormat(gOutputFormatTypes.marc);
}
function setOutputFormat(outputFormat){
	// We have separate format for the preview and detailed view
	// so we have to set the proper variable depending
	// what are we currently displaying
	if (gActionToPerform == gActionTypes.testSearch || gActionToPerform == gActionTypes.previewResults ){
		gOutputFormatPreview = outputFormat;
	}
	else{
		gOutputFormatDetails = outputFormat;
	}

	gOutputFormat = outputFormat;

	if (gActionToPerform!=""){
		performAJAXRequest();
	}
}

function onButtonBackToResultsClick() {
	/*
	 * Brings back the user to the results list
	 */
	if (gActionToPerform == gActionTypes.displayDetailedRecord) {
		onButtonTestSearchClick();
	} else {
		onButtonPreviewResultsClick();
	}
}

function onButtonGoToNextPageClick(){
	gPageToDiplay++;
	performAJAXRequest();
}

function onButtonTestSearchClick() {
	/*
	 * Displays preview of the results of the search
	 */
	gActionToPerform = gActionTypes.testSearch;
	gOutputFormat = gOutputFormatPreview;
	gPageToDiplay = 1;
	performAJAXRequest();
}

function onButtonPreviewResultsClick() {
	/*
	 * Displays preview of the results of the search All the changes defined
	 * with the commands are reflected in the results
	 */
	gActionToPerform = gActionTypes.previewResults;
	gOutputFormat = gOutputFormatPreview;
	gPageToDiplay = 1;
	performAJAXRequest();
}

function onButtonSubmitChangesClick(){
	/*
	 * Submits changes defined by user
	 */
	alert("This functionality is disabled during the testing period.");
	//gActionToPerform = gActionTypes.submitChanges;
	//performAJAXRequest();
}

function performAJAXRequest() {
	/*
	 * Perform an AJAX request
	 */

	$.ajax( {
		cache :false,
		type :"POST",
		dataType :"text",
		data : {
			jsondata :createJSONData()
		},
		success :displayResultsPreview,
		error :onRequestError
	});
}

function createJSONData() {
	/*
	 * Gathers the necessary data and creates a JSON structure that can be used
	 * with the AJAX requests
	 */

	var searchCriteria = $("#textBoxSearchCriteria").val();
	var language = $("#language").val();
	var actionType = gActionToPerform;
	var currentRecordID = gCurrentRecordID;
	var outputFormat = gOutputFormat;
	var pageToDisplay = gPageToDiplay;

	var commands = createCommandsList();

	var data = {
		language :language,
		searchCriteria :searchCriteria,
		actionType :actionType,
		currentRecordID :currentRecordID,
		commands :commands,
		outputFormat :outputFormat,
		pageToDisplay :pageToDisplay
	};

	return JSON.stringify(data);
}

function createCommandsList(){
	/*
	 * Creates structure with information about the commands
	 */
	var commands = Array();

	for (fieldID in gFields) {
		var currentField = gFields[fieldID];

		subfieldsList = Array();
		subfields = currentField.subfields;
		for (subfieldID in subfields) {
			currentSubfield = subfields[subfieldID];
			subfieldsList.push(currentSubfield);
		}

		var field = {
	        tag :currentField.tag,
	        ind1 :currentField.ind1,
	        ind2 :currentField.ind2,
	        action :currentField.action,
	        subfields :subfieldsList
    	};

    	commands.push(field);
	}

	return commands;
}

function onRequestError(XMLHttpRequest, textStatus, errorThrown) {
	/*
	 * Handle AJAX request errors.
	 */

	// FIXME: Change this method. At least strings should be localazed.
	// It is better if the message is more friendly and displayed in a
	// better way
	// alert('Request completed with status ' + textStatus + '\nResult: '
	// + XMLHttpRequest.responseText + '\nError: ' + errorThrown);
	error_message = 'Request completed with status ' + textStatus
			+ '\nResult: ' + XMLHttpRequest.responseText + '\nError: '
			+ errorThrown;

	displayResultsPreview(error_message);
}

function displayResultsPreview(data) {
	$("#preview_area").html(data);
	rebindControls();
}

/*
 * ********************************************************
 * Methods related to action edition
 * ********************************************************
 * */

/*
* Global variables
*/

var gFields = {};
var gCurrentFieldID = 0;
var gCurrentSubfieldID = 0;
var gFieldDisplayIDPrefix = "fieldDisplayID";
var gSubfieldDisplayIDPrefix = "subfieldDisplayID";

var gSubfieldActionTypes = {
    addSubfield :0,
    deleteSubfield :1,
    replaceContent :2,
    replaceText :3
};

var gFieldActionTypes = {
    addField :0,
    deleteField :1,
    updateField :2
};

function rebindActionsRelatedControls() {
	/*
	 * Binds controls with the appropriate events
	 */
    // Field related
    $(".buttonNewField").bind("click", onButtonNewFieldClick);
    $(".buttonSaveNewField").bind("click", onButtonSaveNewFieldClick);
    $(".buttonCancelNewField").bind("click", onButtonCancelNewFieldClick);
    $(".buttonDeleteField").bind("click", onButtonDeleteFieldClick);
    // Subfield related
    $(".buttonNewSubfield").bind("click", onButtonNewSubfieldClick);
    $(".buttonSaveNewSubfield").bind("click", onButtonSaveNewSubfieldClick);
    $(".buttonCancelNewSubfield").bind("click", onButtonCancelNewSubfieldClick);
    $(".buttonDeleteSubfield").bind("click", onButtonDeleteSubfieldClick);
    $(".subfieldActionType").bind("change", onSubfieldActionTypeChange);
}

function generateFieldDisplayID() {
	/*
	 * Returns identifier for field that could be used
	 * in the html elements
	 */
    var fieldDisplayID = gFieldDisplayIDPrefix + "_" +gCurrentFieldID;
    gCurrentFieldID++;

    return fieldDisplayID;
}

function generateSubfieldDisplayID(fieldID, subfieldID) {
	/*
	 * Returns identifier for subfield that could be used
	 * in the html elements
	 */
    if (subfieldID == null){
        subfieldID = gCurrentSubfieldID;
        gCurrentSubfieldID++;
    }
    var subfieldDisplayID = gFieldDisplayIDPrefix + "_" + fieldID + "_" + subfieldID;

    return subfieldDisplayID;
}

function getFieldID(displayID){
    var fieldID = displayID.split("_")[1];
    return fieldID;
}

function getSubfieldID(displayID){
    var subfieldID = displayID.split("_")[2];
    return subfieldID;
}

function onButtonNewFieldClick() {
    var templateNewField = $("#displayTemplates .templateNewField").clone();
    templateNewField.attr("id", generateFieldDisplayID());
    $("#actionsDisplayArea .lastRow").before(templateNewField);

    rebindControls();
}

function onButtonCancelNewFieldClick() {
    $(this).parents(".templateNewField").remove();
}

function getIndicatorText(indicator) {
    var text = (indicator == "" || indicator == " ") ? "_" : indicator;
    return text;
}

function cleanIndicator(indicator) {
    var cleanedValue = (indicator != "_" && indicator != "") ? indicator : " ";
    return cleanedValue;
}

function createField(jqueryElement) {
    /*
    * Creates a field from the informaiton contained in an
    * element. This element is expected to contain specific
    * fields with all the necessary information
    */

    var tag = jqueryElement.find(".textBoxFieldTag").eq(0).val();
    var ind1 = jqueryElement.find(".textBoxFieldInd1").eq(0).val();
    var ind2 = jqueryElement.find(".textBoxFieldInd2").eq(0).val();
    var action = jqueryElement.find(".fieldActionType").eq(0).val();

    ind1 = cleanIndicator(ind1);
    ind2 = cleanIndicator(ind2);

    var subfields = {};


    var field = {
        tag :tag,
        ind1 :ind1,
        ind2 :ind2,
        action :action,
        subfields :subfields
    };

    return field;
}

function createSubfield(templateNewSubield){
    /*
    * Creates a subfield from the informaiton contained in
    * templateNewSubield. It is expected to contain specific
    * fields with all the necessary information
    */

    var subfieldCode = templateNewSubield.find(".textBoxSubfieldCode").eq(0).val();
    var value = templateNewSubield.find(".textBoxValue").eq(0).val();
    var newValue = templateNewSubield.find(".textBoxNewValue").eq(0).val();
    var action = templateNewSubield.find(".subfieldActionType").eq(0).val();

    var subfield = {
        subfieldCode :subfieldCode,
        value :value,
        newValue :newValue,
        action :action
    };

    return subfield;
}

function onButtonSaveNewFieldClick() {

    // template for displaying the information
    var templateDisplayField = $("#displayTemplates .templateDisplayField").clone();
    // here is where the user entered the information
    var templateNewField = $(this).parents(".templateNewField");

    var field = createField(templateNewField);

    var fieldDisplayID = templateNewField.attr("id");
    var fieldID = getFieldID(fieldDisplayID);
    gFields[fieldID] = field;

    // update field appearence at the user interface
    var actionText = templateNewField.find(".fieldActionType").eq(0).find('option').filter(':selected').text();

    templateDisplayField.attr("id", fieldDisplayID);
    templateDisplayField.find(".tag").eq(0).text(field.tag);
    templateDisplayField.find(".ind1").eq(0).text(getIndicatorText(field.ind1));
    templateDisplayField.find(".ind2").eq(0).text(getIndicatorText(field.ind2));
    templateDisplayField.find(".action").eq(0).text(actionText);

    // When deleting fields, we don't have to define subfields
    if(field.action == gFieldActionTypes.deleteField){
    	templateDisplayField.find(".buttonNewSubfield").remove();
    }

    templateNewField.replaceWith(templateDisplayField);

    rebindControls();
}

function onButtonDeleteFieldClick() {
    var fieldElement = $(this).parents(".templateDisplayField");

    var fieldDisplayID = fieldElement.attr("id");

    var fieldID = getFieldID(fieldDisplayID);

    // delete subfileds from the UI
    for (subfieldID in gFields[fieldID].subfields){
        var subfieldSelector = "#" + generateSubfieldDisplayID(fieldID, subfieldID);
        $(subfieldSelector).remove();
    }

    // delete field itself
    delete gFields[fieldID];
    fieldElement.remove();
}

function onButtonNewSubfieldClick() {
    // find the id of the field that is parent of the subfield
    var templateField = $(this).parents(".templateDisplayField");
    var fieldDisplayID = templateField.attr("id");
    var fieldID = getFieldID(fieldDisplayID);

    // generate ID for the the element of the new subfield
    var subfieldDisplayID = generateSubfieldDisplayID(fieldID);

    // add the new subfield to the UI
    var templateNewSubfield = $("#displayTemplates .templateNewSubfield").clone();
    templateNewSubfield.attr("id", subfieldDisplayID);
    displayProperSubfieldInformation(templateNewSubfield);
    templateField.after(templateNewSubfield);

    rebindControls();
}

function onButtonCancelNewSubfieldClick() {
    $(this).parents(".templateNewSubfield").remove();
}

function onButtonSaveNewSubfieldClick() {
    // template for displaying the information
    var templateDisplaySubfield = $("#displayTemplates .templateDisplaySubfield").clone();
    // here is where the user entered the information
    var templateNewSubfield = $(this).parents(".templateNewSubfield");

    var subfieldDisplayID = templateNewSubfield.attr("id");
    var fieldID = getFieldID(subfieldDisplayID);
    var subfieldID = getSubfieldID(subfieldDisplayID);

    var currentSubfield = createSubfield(templateNewSubfield);
    var field = gFields[fieldID];
    field.subfields[subfieldID] = currentSubfield;

    // update subfield appearence at the user interface
    var actionText = templateNewSubfield.find(".subfieldActionType").eq(0).find('option').filter(':selected').text();

    templateDisplaySubfield.attr("id", subfieldDisplayID);
    templateDisplaySubfield.find(".action").eq(0).text(actionText);
    templateDisplaySubfield.find(".subfieldCode").eq(0).text(currentSubfield.subfieldCode);
    templateDisplaySubfield.find(".value").eq(0).text(currentSubfield.value);
    templateDisplaySubfield.find(".newValue").eq(0).text(currentSubfield.newValue);

    displayProperSubfieldInformation(templateDisplaySubfield, currentSubfield.action);

    templateNewSubfield.replaceWith(templateDisplaySubfield );

    rebindControls();
}

function onButtonDeleteSubfieldClick() {
    var subfieldElement = $(this).parents(".templateDisplaySubfield");

    var subfieldDisplayID = subfieldElement.attr("id");

    var fieldID = getFieldID(subfieldDisplayID);
    var subfieldID = getSubfieldID(subfieldDisplayID);

    delete gFields[fieldID].subfields[subfieldID];
    subfieldElement.remove();
}

function onSubfieldActionTypeChange() {
    var parentElement = $(this).parents(".templateNewSubfield").eq(0);

    displayProperSubfieldInformation(parentElement);
}

function displayProperSubfieldInformation(actionParentElement, actionType) {
    actionParentElement.find(".valueParameters").hide();
    actionParentElement.find(".newValueParameters").hide();

    if (actionType == null){
        actionType = actionParentElement.find(".subfieldActionType").eq(0).val();
    }

    if(actionType != gSubfieldActionTypes.deleteSubfield) {
        actionParentElement.find(".valueParameters").show();
    }

    if(actionType == gSubfieldActionTypes.replaceText) {
        actionParentElement.find(".newValueParameters").show();
    }

	// Fix subfield action type to "add" when adding fields
	// We assume that by default this is the selected value
    var subfieldDisplayID = actionParentElement.attr("id");
    var fieldID = getFieldID(subfieldDisplayID);
    var field = gFields[fieldID];

    if(field.action == gFieldActionTypes.addField){
    	actionParentElement.find(".subfieldActionType").attr("disabled", "disabled");
    }
}

 /*
 * ********************************************************
 * */
