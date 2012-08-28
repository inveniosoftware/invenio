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
 * Global variables
 */

/*global performAJAXRequest, setOutputFormat, rebindActionsRelatedControls */

// Defines the different actions performed by AJAX calls
var gActionTypes = {
	testSearch : "testSearch",
	displayDetailedRecord : "displayDetailedRecord",
	previewResults : "previewResults",
	displayDetailedResult : "displayDetailedResult",
	submitChanges : "submitChanges"
};

// Defines the different output formats of the results
var gOutputFormatTypes = {
	bibTeX : "hx",
	marcXML : "xm",
	nlm : "xn",
	htmlBrief : "hb",
	htmlDetailed : "hd",
	marc : "hm"
};

// Defines different types of commands for manipulation of records
var gCommandTypes = {
	replaceTextInField : "replaceTextInField",
	replaceFieldContent : "replaceFieldContent",
	deleteField : "deleteField",
	addField : "addField"
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
var gOutputFormat = gOutputFormatTypes.marc;
var gOutputFormatDetails = gOutputFormatTypes.htmlDetailed;
var gOutputFormatPreview = gOutputFormatTypes.marc;
var gComputeModifications = 0;

/*
* Global variables
*/

var gFields = {};
var gCurrentFieldID = 0;
var gCurrentSubfieldID = 0;
var gFieldDisplayIDPrefix = "fieldDisplayID";
var gSubfieldDisplayIDPrefix = "subfieldDisplayID";

var gSubfieldActionTypes = {
    addSubfield : 0,
    deleteSubfield : 1,
    replaceContent : 2,
    replaceText : 3
};

var gFieldActionTypes = {
    addField : 0,
    deleteField : 1,
    updateField : 2
};

function updateView() {
	$("#displayTemplates").hide();
        $('#buttonSubmitChanges').attr('disabled', 'true').addClass('buttonDisabled');
}
function showLoading() {
    $('#preview_area').html('<span class="multiedit_loading">Loading...</span><br /><img src=/img/ajax-loader.gif>').css("text-align", "center");
}

function createCommandsList(){
	/*
	 * Creates structure with information about the commands
	 */
	var commands = Array();

	var fieldID = "";
	for (fieldID in gFields) {
		var currentField = gFields[fieldID];

		subfieldsList = Array();
		subfields = currentField.subfields;
		var subfieldID = "";
		for (subfieldID in subfields) {
                    currentSubfield = subfields[subfieldID];
                    if (currentSubfield != "None")
                        subfieldsList.push(currentSubfield);
		}

		var field = {
            tag : currentField.tag,
            ind1 : currentField.ind1,
            ind2 : currentField.ind2,
            action : currentField.action,
                condition : currentField.condition,
                conditionSubfield : currentField.conditionSubfield,
                conditionSubfieldExactMatch: currentField.conditionSubfieldExactMatch,
            subfields : subfieldsList
		};

		commands.push(field);
	}

	return commands;
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

function onButtonTestSearchClick() {
	/*
	 * Displays preview of the results of the search
	 */
	gActionToPerform = gActionTypes.testSearch;
	gOutputFormat = gOutputFormatPreview;
	gPageToDiplay = 1;
        showLoading();
	performAJAXRequest();
        $('#buttonSubmitChanges').attr('disabled', 'true').addClass('buttonDisabled');
}

function onButtonPreviewResultsClick() {
	/*
	 * Displays preview of the results of the search All the changes defined
	 * with the commands are reflected in the results
	 */
	gActionToPerform = gActionTypes.previewResults;
	gOutputFormat = gOutputFormatPreview;
	gPageToDiplay = 1;
        gComputeModifications = 1;
        showLoading();
	performAJAXRequest();
        $('#buttonSubmitChanges').removeAttr('disabled').removeClass('buttonDisabled');
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

function onButtonSubmitChangesClick(){
	/*
	 * Submits changes defined by user
	 */
	var confirmation = confirm('Are you sure you want to submit the changes?');
	if (confirmation == true) {
		gActionToPerform = gActionTypes.submitChanges;
		performAJAXRequest();
	}
}

function rebindControls() {
	/*
	 * Binds controls with the appropriate events
	 */

	rebindActionsRelatedControls();
	initTextBoxes();

    $("#buttonTestSearch").live("click", onButtonTestSearchClick);
	$("#buttonPreviewResults").live("click", onButtonPreviewResultsClick);
	$("#buttonSubmitChanges").live("click", onButtonSubmitChangesClick);
	$(".buttonBackToResults").live("click", onButtonBackToResultsClick);
	$(".buttonOutputFormatMarcXML").live("click", onButtonOutputFormatMarcXMLClick);
	$(".buttonOutputFormatHTMLBrief").live("click", onButtonOutputFormatHTMLBriefClick);
	$(".buttonOutputFormatHTMLDetailed").live("click", onButtonOutputFormatHTMLDetailedClick);
	$(".buttonOutputFormatMARC").live("click", onButtonOutputFormatMARCClick);
    $(".buttonGoToFirstPage").live("click", onButtonGoToFirstPageClick);
	$(".buttonGoToPreviousPage").live("click", onButtonGoToPreviousPageClick);
	$(".buttonGoToNextPage").live("click", onButtonGoToNextPageClick);
}

function onAjaxSuccess(json) {
        var display_info_box = json['display_info_box'];
        var info_html = json['info_html'];
        var search_html = json['search_html'];
        if (display_info_box === 1) {
            $("#info_area").html(info_html);
            gComputeModifications = 0;

        }
        $("#preview_area").css("text-align", "");
        $("#preview_area").html(search_html);
}

function displayError(msg) {
    $("#preview_area").css("text-align", "");
    $("#preview_area").html(msg);
}

function createJSONData() {
	/*
	 * Gathers the necessary data and creates a JSON structure that can be used
	 * with the AJAX requests
	 */

	var searchCriteria = $("#textBoxSearchCriteria").val();
	var outputTags = $("#textBoxOutputTags").val();
	var language = $("#language").val();
	var actionType = gActionToPerform;
	var currentRecordID = gCurrentRecordID;
	var outputFormat = gOutputFormat;
	var pageToDisplay = gPageToDiplay;
        var collection = $("#collection").val();
	var commands = createCommandsList();
        var compute_modifications = gComputeModifications;

	var data = {
		language : language,
		searchCriteria : searchCriteria,
		outputTags : outputTags,
		actionType : actionType,
		currentRecordID : currentRecordID,
		commands : commands,
		outputFormat : outputFormat,
		pageToDisplay : pageToDisplay,
		collection : collection,
                compute_modifications : compute_modifications
	};

	return JSON.stringify(data);
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
	error_message = 'Request completed with status ' + textStatus +
			'\nResult: ' + XMLHttpRequest.responseText + '\nError: ' + errorThrown;

	displayError(error_message);
}

function performAJAXRequest() {
	/*
	 * Perform an AJAX request
	 */
	$.ajax( {
		cache : false,
		type : "POST",
		dataType : "json",
		data : {
			jsondata : createJSONData()
		},
		success : function(json){
                      onAjaxSuccess(json);
                    },
		error : onRequestError
	});
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

function initTextBoxes(){
    $('#textBoxOutputTags, #textBoxCondition').focus(function() {
        if (this.value == this.defaultValue){
            this.value = '';
        }
        if(this.value != this.defaultValue){
            this.select();
        }
    });

    $('#textBoxOutputTags, #textBoxCondition').blur(function() {
        if ($.trim(this.value) == ''){
            this.value = (this.defaultValue ? this.defaultValue : '');
        }
    });

}

$(document).ready( function() {
	rebindControls();
	updateView();
});


/*
 * ********************************************************
 * Methods related to action edition
 * ********************************************************
 * */


function getFieldID(displayID){
    var fieldID = displayID.split("_")[1];
    return fieldID;
}

function getSubfieldID(displayID){
    var subfieldID = displayID.split("_")[2];
    return subfieldID;
}


function getIndicatorText(indicator) {
    var text = (indicator === "" || indicator === " ") ? "_" : indicator;
    return text;
}

function cleanIndicator(indicator) {
    var cleanedValue = (indicator != "_" && indicator != "") ? indicator : " ";
    return cleanedValue;
}

function displayProperSubfieldInformation(actionParentElement, actionType, displayCondition) {
    actionParentElement.find(".valueParameters").hide();
    actionParentElement.find(".newValueParameters").hide();
    actionParentElement.find(".conditionParameters").hide();
    actionParentElement.find(".conditionSubfieldParameters").hide();

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
        actionParentElement.find(".subfieldActionType").attr("disabled", "true");
    }

    if (displayCondition == 'true') {
        actionParentElement.find(".conditionParameters").show();
        actionParentElement.find(".conditionSubfieldParameters").show();
    }

}

function unbindControls(filter_field){
    if (filter_field == 'true'){
        $("#actOnFields, #actOnFieldsDelete").unbind("click");
        $("#actOnFieldsRemove, #actOnFieldsDeleteRemove").unbind("click");
        $("#actOnFieldsRemove, #actOnFieldsDeleteRemove").bind("click", onActOnFieldsRemoveClick);
    }
    else{
        $("#actOnFields, #actOnFieldsDelete").unbind("click");
        $("#actOnFields, #actOnFieldsDelete").bind("click", onActOnFieldsClick);
        $("#actOnFieldsRemove, #actOnFieldsDeleteRemove").unbind("click");
    }

}

function onActOnFieldsClick() {
    var parentElement;
    if ($(this).attr("id") == "actOnFields"){
        parentElement = $(this).parents(".templateNewSubfield").eq(0);
    
        parentElement.find(".conditionParameters").show();
        parentElement.find("#actOnFields").html('<u>Act on all fields</u>');
        parentElement.find("#actOnFields").attr('id', 'actOnFieldsRemove');
    }
    else {
        parentElement = $(this).parents(".templateDisplayField").eq(0);

        parentElement.find(".conditionParameters").show();
        parentElement.find("#actOnFieldsDelete").html('<u>Act on all fields</u>');
        parentElement.find("#actOnFieldsDelete").attr('id', 'actOnFieldsDeleteRemove');
        parentElement.find(".conditionActOnFieldsSave").show();
    }

    unbindControls('true');
    initTextBoxes();
}

function onActOnFieldsRemoveClick() {

    if ($(this).attr("id") == "actOnFieldsRemove"){
        var parentElement = $(this).parents(".templateNewSubfield").eq(0);

        parentElement.find(".conditionParameters").hide();
        parentElement.find("#actOnFieldsRemove").html('<u>Apply only to specific field instances</u>');
        parentElement.find("#actOnFieldsRemove").attr('id', 'actOnFields');
    }
    else {
        var parentElement = $(this).parents(".templateDisplayField").eq(0);

        parentElement.find(".conditionParameters").hide();
        parentElement.find("#actOnFieldsDeleteRemove").html('<u>Apply only to specific field instances</u>');
        parentElement.find("#actOnFieldsDeleteRemove").attr('id', 'actOnFieldsDelete');
        parentElement.find(".conditionActOnFieldsSave").hide();
    }


    unbindControls('false');
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


function addMessage(fieldID, actionText) {
    if (actionText != "Delete field") {
        var templateMsg = $("#displayTemplates .templateMsg").clone();

        templateMsg.attr("id", 'Msg_' + fieldID);
        templateMsg.find(".msg").eq(0).text("Warning: add one subfield action before applying changes");

        $("#actionsDisplayArea .lastRow").before(templateMsg);
    }
}

function deleteMsg(fieldID) {
    var msgID = "#" + 'Msg_' + fieldID;
    $(msgID).remove();
}

function createSubfield(templateNewSubfield){
    /*
    * Creates a subfield from the informaiton contained in
    * templateNewSubield. It is expected to contain specific
    * fields with all the necessary information
    */

    if (templateNewSubfield === "None"){
        return "None"
    }

    var subfieldCode = templateNewSubfield.find(".textBoxSubfieldCode").eq(0).val();
    var value = templateNewSubfield.find(".textBoxValue").eq(0).val();
    var newValue = templateNewSubfield.find(".textBoxNewValue").eq(0).val();
    var action = templateNewSubfield.find(".subfieldActionType").eq(0).val();
    var condition = templateNewSubfield.find(".textBoxCondition").eq(0).val();
    var conditionSubfieldExactMatch = templateNewSubfield.find(".selectConditionExactMatch").eq(0).val();
    var conditionSubfield = templateNewSubfield.find(".textBoxConditionSubfield").eq(0).val();

    var subfield = {
        subfieldCode : subfieldCode,
        value : value,
        newValue : newValue,
        action : action,
        condition : condition,
        conditionSubfieldExactMatch: conditionSubfieldExactMatch,
        conditionSubfield : conditionSubfield
    };

    return subfield;
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
    var conditionSubfield = "";
    var condition = "";
    var conditionSubfieldExactMatch = 0;


    var field = {
        tag : tag,
        ind1 : ind1,
        ind2 : ind2,
        action : action,
        subfields : subfields,
        conditionSubfield : conditionSubfield,
        condition: condition,
        conditionSubfieldExactMatch: conditionSubfieldExactMatch
    };

    return field;
}

function onFieldActionTypeChange(instance) {
    onButtonSaveNewFieldClick(instance);
}

function onSubfieldActionTypeChange() {
    var parentElement = $(this).parents(".templateNewSubfield").eq(0);

    displayProperSubfieldInformation(parentElement);
}

function onButtonNewSubfieldClick(instance) {
    // find the id of the field that is parent of the subfield

    var templateField = $(this).parents(".templateDisplayField");
    var fieldDisplayID = templateField.attr("id");
    var fieldID = getFieldID(fieldDisplayID);

    // generate ID for the the element of the new subfield
    var subfieldDisplayID = generateSubfieldDisplayID(fieldID);
    var subfieldID = getSubfieldID(subfieldDisplayID);

    // create empty subfield to be able to delete it in
    // case the field is deleted
    var emptySubfield = createSubfield("None");
    var field = gFields[fieldID];
    field.subfields[subfieldID] = emptySubfield;

    // add the new subfield to the UI
    var templateNewSubfield = $("#displayTemplates .templateNewSubfield").clone();
    templateNewSubfield.attr("id", subfieldDisplayID);
    displayProperSubfieldInformation(templateNewSubfield);
    templateField.after(templateNewSubfield);

    initTextBoxes();
}

function onButtonCancelNewSubfieldClick() {
    $(this).parents(".templateNewSubfield").remove();
}

function onButtonNewFieldClick() {
    var templateNewField = $("#displayTemplates .templateNewField").clone();
    templateNewField.attr("id", generateFieldDisplayID());
    $("#actionsDisplayArea .lastRow").before(templateNewField);
}

function onButtonCancelNewFieldClick(instance) {
    $(instance).parents(".templateNewField").remove();
}

function onButtonDeleteFieldClick() {
    var fieldElement = $(this).parents(".templateDisplayField");

    var fieldDisplayID = fieldElement.attr("id");

    var fieldID = getFieldID(fieldDisplayID);

    // delete subfields from the UI
    var subfieldID = "";
    for (subfieldID in gFields[fieldID].subfields){
        var subfieldSelector = "#" + generateSubfieldDisplayID(fieldID, subfieldID);
        $(subfieldSelector).remove();
    }

    // delete field itself
    delete gFields[fieldID];
    fieldElement.remove();
    deleteMsg(fieldID);
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
    var conditionExactText;
    if (currentSubfield.conditionSubfieldExactMatch === "0") {
        conditionExactText = "is equal to";
    } else if (currentSubfield.conditionSubfieldExactMatch === "1") {
        conditionExactText = "contains";
    } else conditionExactText = "does not exist";

    templateDisplaySubfield.attr("id", subfieldDisplayID);
    templateDisplaySubfield.find(".action").eq(0).text(actionText);
    templateDisplaySubfield.find(".subfieldCode").eq(0).text(currentSubfield.subfieldCode);
    templateDisplaySubfield.find(".textBoxValue").eq(0).attr("value", currentSubfield.value);
    templateDisplaySubfield.find(".textBoxNewValue").eq(0).attr("value", currentSubfield.newValue);
    templateDisplaySubfield.find(".conditionExact").eq(0).text(conditionExactText);
    templateDisplaySubfield.find(".textBoxCondition").eq(0).attr("value", currentSubfield.condition);
    if (currentSubfield.conditionSubfield){
        templateDisplaySubfield.find(".textBoxConditionSubfield").eq(0).attr("value", currentSubfield.conditionSubfield);
    }

    // show "when subfield $$..." does not exist without "condition" textBox
    if (templateDisplaySubfield.find(".conditionExact").eq(0).text() == 'does not exist') {
        displayProperSubfieldInformation(templateDisplaySubfield, currentSubfield.action, 'true');
        templateDisplaySubfield.find(".textBoxCondition").hide();
    }
    else if (templateDisplaySubfield.find(".textBoxCondition").eq(0).val() != 'condition') {
        displayProperSubfieldInformation(templateDisplaySubfield, currentSubfield.action, 'true');
    }
    else {
        displayProperSubfieldInformation(templateDisplaySubfield, currentSubfield.action);
    }
    templateNewSubfield.replaceWith(templateDisplaySubfield );

    deleteMsg(fieldID);
}

function onButtonDeleteSubfieldClick() {
    var subfieldElement = $(this).parents(".templateDisplaySubfield");

    var subfieldDisplayID = subfieldElement.attr("id");

    var fieldID = getFieldID(subfieldDisplayID);
    var subfieldID = getSubfieldID(subfieldDisplayID);

    delete gFields[fieldID].subfields[subfieldID];
    subfieldElement.remove();
}

function onButtonSaveNewFieldClick(instance) {
    // template for displaying the information
    var templateDisplayField = $("#displayTemplates .templateDisplayField").clone();

    // Possibility to add a condition is only valid when deleting a field
    templateDisplayField.find(".conditionParameters").hide();
    templateDisplayField.find(".conditionActOnFields").hide();
    templateDisplayField.find(".conditionActOnFieldsSave").hide();
    templateDisplayField.find(".conditionParametersDisplay").hide();

    // here is where the user entered the information
    var templateNewField = $(instance).parents(".templateNewField");

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
        templateDisplayField.find(".conditionActOnFields").show();
    }

    templateNewField.replaceWith(templateDisplayField);

    addMessage(fieldID, actionText);

    // If we are not deleting fields, we want the first subfield action to be opened automatically
    if(field.action !== gFieldActionTypes.deleteField){
        templateDisplayField.find(".buttonNewSubfield").eq(0).click();
    }
}

function onButtonSaveNewFieldConditionClick() {
    /* Event handler to save the condition when a field is deleted */
    var templateDisplayField = $(this).parents(".templateDisplayField");

    var fieldDisplayID = templateDisplayField.attr("id");
    var fieldID = getFieldID(fieldDisplayID);

    var condition = templateDisplayField.find("#textBoxCondition").eq(0).val();
    var conditionSubfieldExactMatch = templateDisplayField.find(".selectConditionExactMatch").eq(0).val();
    var conditionSubfield = templateDisplayField.find("#textBoxConditionSubfield").eq(0).val();

    gFields[fieldID].conditionSubfield = conditionSubfield;
    gFields[fieldID].condition = condition;
    gFields[fieldID].conditionSubfieldExactMatch = conditionSubfieldExactMatch;

    if (conditionSubfieldExactMatch === "0") {
        conditionExactText = "is equal to";
    }
    else if(conditionSubfieldExactMatch === "1") {
        conditionExactText = "contains";
    }
    else conditionExactText = "does not exist";

    templateDisplayField.find(".conditionExact").eq(0).text(conditionExactText);
    templateDisplayField.find("#textBoxConditionFieldDisplay").eq(0).attr("value", condition);
    if (conditionSubfield){
        templateDisplayField.find("#textBoxConditionSubfieldDisplay").eq(0).attr("value", conditionSubfield);
    }

    templateDisplayField.find(".conditionParameters").hide();
    templateDisplayField.find(".conditionActOnFields").hide();
    templateDisplayField.find(".conditionActOnFieldsSave").hide();

    templateDisplayField.find(".conditionParametersDisplay").show();

    // show "when subfield $$..." does not exist without "condition" textBox
    if (templateDisplayField.find(".conditionExact").eq(0).text() == 'does not exist') {
        templateDisplayField.find("#textBoxConditionFieldDisplay").hide();
    }

}

function onTextBoxValueDisplayChange(){

    var subfieldElement = $(this).parents(".templateDisplaySubfield");

    var subfieldDisplayID = subfieldElement.attr("id");

    var fieldID = getFieldID(subfieldDisplayID);
    var subfieldID = getSubfieldID(subfieldDisplayID);

    var value = subfieldElement.find(".textBoxValue").eq(0).val();
    gFields[fieldID].subfields[subfieldID].value = value;
}

function onTextBoxNewValueDisplayChange(){
    var subfieldElement = $(this).parents(".templateDisplaySubfield");

    var subfieldDisplayID = subfieldElement.attr("id");

    var fieldID = getFieldID(subfieldDisplayID);
    var subfieldID = getSubfieldID(subfieldDisplayID);

    var newValue = subfieldElement.find(".textBoxNewValue").eq(0).val();
    gFields[fieldID].subfields[subfieldID].newValue = newValue;
}

function onTextBoxConditionDisplayChange(){
    var subfieldElement = $(this).parents(".templateDisplaySubfield");

    var subfieldDisplayID = subfieldElement.attr("id");

    var fieldID = getFieldID(subfieldDisplayID);
    var subfieldID = getSubfieldID(subfieldDisplayID);

    var condition = subfieldElement.find(".textBoxCondition").eq(0).val();
    gFields[fieldID].subfields[subfieldID].condition = condition;
}

function onTextBoxConditionSubfieldDisplayChange(){
    var subfieldElement = $(this).parents(".templateDisplaySubfield");

    var subfieldDisplayID = subfieldElement.attr("id");

    //when deleting field, we need to use .templateDisplayField instead of .templateDisplaySubfield
    if (typeof subfieldDisplayID === "undefined")
    {
        subfieldElement = $(this).parents(".templateDisplayField");
        subfieldDisplayID = subfieldElement.attr("id");
    }

    var fieldID = getFieldID(subfieldDisplayID);
    var subfieldID = getSubfieldID(subfieldDisplayID);

    var conditionSubfield = subfieldElement.find(".textBoxConditionSubfield").eq(0).val();

    if (typeof subfieldID === "undefined") {
        gFields[fieldID].conditionSubfield = conditionSubfield;
    } else {
        gFields[fieldID].subfields[subfieldID].conditionSubfield = conditionSubfield;
    }
}

function onTextBoxConditionFieldDisplayChange() {
    var templateDisplayField = $(this).parents(".templateDisplayField");

    var fieldDisplayID = templateDisplayField.attr("id");

    var fieldID = getFieldID(fieldDisplayID);

    var condition = templateDisplayField.find("#textBoxConditionFieldDisplay").eq(0).val();
    gFields[fieldID].condition = condition;
}

function onSelectConditionExactMatchValueDisplayChange(){
    var conditionOption = $("option:selected",this).val();

    var subfieldElement = $(this).parents(".conditionParameters");

    if (conditionOption == 2){
        subfieldElement.find(".textBoxCondition").hide();
    } else {
        subfieldElement.find(".textBoxCondition").show();
    }
}

function rebindActionsRelatedControls() {
    /*
    * lives controls with the appropriate events
    */
    // Field related
    $(".buttonNewField").live("click", onButtonNewFieldClick);
    $("#buttonSaveNewField").live("click", onButtonSaveNewFieldClick);
    $("#buttonCancelNewField").live("click", onButtonCancelNewFieldClick);
    $("#buttonSaveNewFieldCondition").live("click", onButtonSaveNewFieldConditionClick);
    $("#buttonCancelFieldCondition").live("click", onActOnFieldsRemoveClick);
    $(".buttonDeleteField").live("click", onButtonDeleteFieldClick);
    // Subfield related
    $(".buttonNewSubfield").live("click", onButtonNewSubfieldClick);
    $("#buttonSaveNewSubfield").live("click", onButtonSaveNewSubfieldClick);
    $("#buttonCancelNewSubfield").live("click", onButtonCancelNewSubfieldClick);
    $(".buttonDeleteSubfield").live("click", onButtonDeleteSubfieldClick);
    $(".subfieldActionType").live("change", onSubfieldActionTypeChange);
    $("#actOnFields, #actOnFieldsDelete").live("click", onActOnFieldsClick);
    $("#actOnFieldsRemove, #actOnFieldsDeleteRemove").live("click", onActOnFieldsRemoveClick);
    // Edit actions
    $("#textBoxValueDisplay").live("change", onTextBoxValueDisplayChange);
    $("#textBoxNewValueDisplay").live("change", onTextBoxNewValueDisplayChange);
    $("#textBoxConditionDisplay").live("change", onTextBoxConditionDisplayChange);
    $("#textBoxConditionFieldDisplay").live("change", onTextBoxConditionFieldDisplayChange);
    $("#textBoxConditionSubfieldDisplay").live("change", onTextBoxConditionSubfieldDisplayChange);
    $(".selectConditionExactMatch").live("change", onSelectConditionExactMatchValueDisplayChange);
    // Cancel text boxes
    $(".txtTag, .txtInd").live("keyup", onPressEsc);
    // Submit form when pressing Enter
    $("#textBoxSearchCriteria, #textBoxOutputTags").live("keyup", onEnter);
}

function onSelectOutputFormatChange(value){
	if (value == "Marc"){
		setOutputFormat(gOutputFormatTypes.marc);
	}
	else{
		setOutputFormat(gOutputFormatTypes.htmlBrief);
	}
}

function onEnter(evt){
	var keyCode = null;
	if( evt.which ) {
		keyCode = evt.which;
	} else if( evt.keyCode ) {
		keyCode = evt.keyCode;
	}if( 13 == keyCode ) {
		onButtonTestSearchClick();
	}
}

function onPressEsc(evt){
    var keyCode = null;

    if( evt.which ) {
        keyCode = evt.which;
    }
    else if( evt.keyCode ) {
        keyCode = evt.keyCode;
    }
    if( 27 == keyCode ) {
        onButtonCancelNewFieldClick(evt.target);
    }
}

function onSelectCollectionChange(evt){
    onButtonTestSearchClick();
}

