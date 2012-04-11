//
// This file is part of Invenio.
// Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
//
// Invenio is free software; you can redistribute it and / or
// modify it under the terms of the GNU General Public License as
// published by the Free Software Foundation; either version 2 of the
// License, or (at your option) any later version.
//
// Invenio is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
// General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Invenio; if not, write to the Free Software Foundation, Inc.,
// 59 Temple Place, Suite 330, Boston, MA 02111 - 1307, USA.

$(document).ready(function() {

    // Control 'view more info' behavior in search
    $('[class^=more-]').hide();
    $('[class^=mpid]').click(function() {
        var $this = $(this);
        var x = $this.prop("className");
        $('.more-' + x).toggle();
        var toggleimg = $this.find('img').attr('src');

        if (toggleimg == '../img/aid_plus_16.png') {
            $this.find('img').attr({src:'../img/aid_minus_16.png'});
        } else {
            $this.find('img').attr({src:'../img/aid_plus_16.png'});
        }
        return false;
    });

    // Handle Comments
    if ( $('#jsonForm').length ) {

        $('#jsonForm').ajaxForm({
            // dataType identifies the expected content type of the server response
            dataType:  'json',

            // success identifies the function to invoke when the server response
            // has been received
            success:   processJson
        });

        $.ajax({
            url: '/person/comments',
            dataType: 'json',
            data: { 'pid': $('span[id^=pid]').attr('id').substring(3), 'action': 'get_comments' },
            success: processJson
        });
    }

    // Initialize DataTable
    $('.paperstable').dataTable({
                "bJQueryUI": true,
                "sPaginationType": "full_numbers",
                "aoColumns": [
                        { "bSortable": false,
                          "sWidth": "" },
                        { "bSortable": false,
                          "sWidth": "" },
                        { "sWidth": "" },
			{ "sWidth": "" },
			{ "sWidth": "" },
                        { "sWidth": "120px" },
                        { "sWidth": "320px" }
                ],
                "aLengthMenu": [500],
                'iDisplayLength': 500,
                "fnDrawCallback": function() {
                    $('.dataTables_length').css('display','none');
                }
    });

    $('.reviewstable').dataTable({
                "bJQueryUI": true,
                "sPaginationType": "full_numbers",
                "aoColumns": [
                        { "bSortable": false,
                          "sWidth": "" },
                        { "bSortable": false,
                          "sWidth": "" },
                        { "bSortable": false,
                          "sWidth": "120px" }
                ],
                "aLengthMenu": [500],
                'iDisplayLength': 500,
                "fnDrawCallback": function() {
                    $('.dataTables_length').css('display','none');
                }
    });


    // Activate Tabs
    $("#aid_tabbing").tabs();

    // Style buttons in jQuery UI Theme
	//$(function() {
	//	$( "button, input:submit, a", ".aid_person" ).button();
	//	$( "a", ".demo" ).click(function() { return false; });
	//});

    // Show Message
    $("#aid_notification").fadeIn("slow");
    $("#aid_notification a.aid_close-notify").click(function() {
        $("#aid_notification").fadeOut("slow");
        return false;
    });

    // Set Focus on last input field w/ class 'focus'
    $("input.focus:last").focus();

    // Select all
    $("A[href='#select_all']").click( function() {
        $('input[name=selection]').attr('checked', true);
        return false;
    });

    // Select none
    $("A[href='#select_none']").click( function() {
        $('input[name=selection]').attr('checked', false);
        return false;
    });

    // Invert selection
    $("A[href='#invert_selection']").click( function() {
        $('input[name=selection]').each( function() {
            $(this).attr('checked', !$(this).attr('checked'));
        });
        return false;
    });

//    update_action_links();
});


function toggle_claimed_rows() {
    $("img[alt^=Confirmed.]").parents("tr").toggle()

    if ($("#toggle_claimed_rows").attr("alt") == 'hide') {
        $("#toggle_claimed_rows").attr("alt", 'show');
        $("#toggle_claimed_rows").html("Show successful claims");
    } else {
        $("#toggle_claimed_rows").attr("alt", 'hide');
        $("#toggle_claimed_rows").html("Hide successful claims");
    }
}


function confirm_bibref(claimid) {
// Performs the action of confirming a paper through an AJAX request
    var cid = claimid.replace(/\,/g, "\\," )
    var cid = cid.replace(/\:/g, "\\:")
    $('#bibref'+cid).html('<p><img src="../img/loading" style="background: none repeat scroll 0% 0% transparent;"/></p>');
    $('#bibref'+cid).load('/person/status', { 'pid': $('span[id^=pid]').attr('id').substring(3),
                                                'bibref': claimid,
                                                'action': 'confirm_status' } );
//    update_action_links();
}


function repeal_bibref(claimid) {
// Performs the action of repealing a paper through an AJAX request
    var cid = claimid.replace(/\,/g, "\\," )
    var cid = cid.replace(/\:/g, "\\:")
    $('#bibref'+cid).html('<p><img src="../img/loading" style="background: none repeat scroll 0% 0% transparent;"/></p>');
    $('#bibref'+cid).load('/person/status', { 'pid': $('span[id^=pid]').attr('id').substring(3),
                                                'bibref': claimid,
                                                'action': 'repeal_status' } );
//    update_action_links();
}


function reset_bibref(claimid) {
    var cid = claimid.replace(/\,/g, "\\," )
    var cid = cid.replace(/\:/g, "\\:")
    $('#bibref'+cid).html('<p><img src="../img/loading.gif" style="background: none repeat scroll 0% 0% transparent;"/></p>');
    $('#bibref'+cid).load('/person/status', { 'pid': $('span[id^=pid]').attr('id').substring(3),
                                                'bibref': claimid,
                                                'action': 'reset_status' } );
//    update_action_links();
}


function action_request(claimid, action) {
// Performs the action of reseting the choice on a paper through an AJAX request
    $.ajax({
        url: "/person/status",
        dataType: 'json',
        data: { 'pid': $('span[id^=pid]').attr('id').substring(3), 'action': 'json_editable', 'bibref': claimid },
        success: function(result){
            if (result.editable.length > 0) {
                if (result.editable[0] == "not_authorized") {
                    $( "<p title=\"Not Authorized\">Sorry, you are not authorized to perform this action, since this record has been assigned to another user already. Please contact the support to receive assistance</p>" ).dialog({
                        modal: true,
                        buttons: {
                            Ok: function() {
                                $( this ).dialog( "close" );
//                                update_action_links();
                            }
                        }
                    });
                } else if (result.editable[0] == "touched") {
                    $( "<p title=\"Transaction Review\">This record has been touched before (possibly by yourself). Perform action and overwrite previous decision?</p>" ).dialog({
                        resizable: true,
                        height:250,
                        modal: true,
                        buttons: {
                            "Perform Action!": function() {
                                if (action == "confirm") {
                                    confirm_bibref(claimid);
                                } else if (action == "repeal") {
                                    repeal_bibref(claimid);
                                } else if (action == "reset") {
                                    reset_bibref(claimid);
                                }

                                $( this ).dialog( "close" );
//                                update_action_links();
                            },
                            Cancel: function() {
                                $( this ).dialog( "close" );
//                                update_action_links();
                            }
                        }
                    });

                } else if (result.editable[0] == "OK") {
                    if (action == "confirm") {
                        confirm_bibref(claimid);
                    } else if (action == "repeal") {
                        repeal_bibref(claimid);
                    } else if (action == "reset") {
                        reset_bibref(claimid);
                    }
//                    update_action_links();
                } else {
//                    update_action_links();
                }

            } else {
                return false;
            }
        }
    });
}


function processJson(data) {
// Callback function of the comment's AJAX request
// 'data' is the json object returned from the server

    if (data.comments.length > 0) {
        if ($("#comments").text() == "No comments yet.") {
            $("#comments").html('<p><strong>Comments:</strong></p>\n');
        }

        $.each(data.comments, function(i, msg) {
            var values = msg.split(";;;")
            $("#comments").append('<p><em>' + values[0] + '</em><br />' + values[1] + '</p>\n');
        })
    } else {
        $("#comments").html('No comments yet.');
    }

    $('#message').val("");
}


//function update_action_links() {
//    // Alter claim links in the DOM (ensures following the non-destructive JS paradigm)
//    $('div[id^=bibref]').each(function() {
//        var claimid = $(this).attr('id').substring(6);
//        var cid = claimid.replace(/\,/g, "\\," );
//        var cid = cid.replace(/\:/g, "\\:");
//        $("#bibref"+ cid +" > #aid_status_details > #aid_confirm").attr("href", "javascript:action_request('"+ claimid +"', 'confirm')");
//        $("#bibref"+ cid +" > #aid_status_details > #aid_reset").attr("href", "javascript:action_request('"+ claimid +"', 'reset')");
//        $("#bibref"+ cid +" > #aid_status_details > #aid_repeal").attr("href", "javascript:action_request('"+ claimid +"', 'repeal')");
//   });
//}
