/*
 * This file is part of Invenio.
 * Copyright (C) 2012, 2013 CERN.
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
 * Javascript functions related to BatchUploader Web Interface
 */


/*
 * ************************* Validation functions****************************
 */

function correct_date(date){
    /* Checks if the date is in the correct format
     */
    if (date === '' || date === "yyyy-mm-dd") {
        return true;
    }
    /* First check that date is in the correct format */
    var re_date = new RegExp(/2[01]\d\d-[01]?\d-[0-3]?\d/);
    if (date.match(re_date)){
         /* Then check that the date selected is not previous to today */
        var today = new Date();
        var submit_date = new Date(date);
        if (submit_date >= today) {
            return true;
        }
    }
    return false;
}

function correct_time(time) {
    /* Checks if the time is in the correct format
     */
    if (time === '' || time === "hh:mm:ss") {
        return true;
    }
    var re_time = new RegExp(/[0-2]\d:[0-5]\d:[0-5]\d/);
    if (time.match(re_time)){
        return true;
    }
    else {
        return false;
    }
}

function correct_input_file(input_file) {
    /* Checks if input file is correct (not empty)
     */
    if (input_file !== "") {
        return true;
    }
    return false;
}

function validateFormFields(){
    /*
     * Checks form fields and returns tuple [error_boolean, error_msg]
     */
    var date = $('#datepicker').val();
    var time = $('#submit_time').val();
    var input_file = $('[name=metafile]').val();
    var doc_folder = $('[name=docfolder]').val();
    var msg_input;
    if (typeof input_file == "undefined") {
        input_file = doc_folder;
        msg_input = "Warning: Please, select a folder to upload";
    }
    else {
        msg_input = "Warning: Please, select a file to upload";
    }
    if (!correct_date(date)) {
        return [false, "Warning: Please, select a valid date"];
    }
    else if (!correct_time(time)) {
        return [false, "Warning: Please, select a valid time"];
    }
    else if (!correct_input_file(input_file)) {
        return [false, msg_input];
    }
    else {
        return [true, ''];
    }
}

/*
 * ************************* Bindings ****************************
 */

function onFormSubmitClick() {
    /*
     * Handles click event on submit button
     */
    /* function that returns tuple [error_boolean, error_msg] */
    var validForm = validateFormFields();
    if (validForm[0]) {
        this.submit();
        return true;
    }
    else {
        $('#error_div').html(validForm[1]);
        return false;
    }
}

function onFileTypeChange(event) {
    if ( $(event.target).val() === 'textmarc' ) {
        var $select_first_value = $('select[name="mode"]').children().eq(0);
        if ( $select_first_value.val() === "--insert" ) {
            $select_first_value.remove();
        }
    }
    else {
        var $select_first_value = $('select[name="mode"]').children().eq(0);
        if ( $select_first_value.val() !== "--insert" ) {
            var insert_option = $("<option>--insert</option>");
            $select_first_value.parent().prepend(insert_option);
        }
    }
}

function createBindings() {
    /*
     * Bind UI elements to functions
     */
    $('.adminbutton').bind('click', onFormSubmitClick);
    $('select[name="filetype"]').on("change", onFileTypeChange)
}

/*
 * ************************* Initialize components ****************************
 */

$(function(){
  /*
   * Initialize all components.
   */
  createBindings();
});