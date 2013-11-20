// -*- coding: utf-8 -*-
// This file is part of Invenio.
// Copyright (C) 2013 CERN.
//
// Invenio is free software; you can redistribute it and/or
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
// 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.


var bwoid;
var datapreview = "hd";
var number_of_objs = $(".theform").length;
var current_number = number_of_objs-1;
url = new Object();

function init_urls_approval(url_){
    url = url_;
}

function checkRecordsToApprove(){
    if(recordsToApprove.length > 1){
        hideApproveAll();
        approveAll();
    }
    else{
        hideApproveAll();
    }
}

function disapproveRecords(){
    console.log("deleting");
    deleteRecords(recordsToApprove);
    recordsToApprove = [];
    // TODO: 
    // the bug here will occur when there are records with other widgets
    // than approval.
    emptyLists();
    checkRecordsToApprove();
}

function hideApproveAll(){
    $('#multi-approval').empty();
}

function approveAll() {
    var rejectBtn = '<button type="button" class="btn btn-danger">'+
                    '<a id="reject-multi" href="#confirmationModal" class="mini-approval-btn" data-toggle="modal">'+
                    'Reject</a></button>';
    var acceptBtn = '<button type="button" class="btn btn-success">'+
                    '<a id="accept-multi" href="javascript:void(0)" class="mini-approval-btn">'+
                    'Accept</a></button>';
    $('#multi-approval').append(rejectBtn, acceptBtn);
    $('#accept-multi').click( function(){
        for(i=0; i<recordsToApprove.length; i++){
            jQuery.ajax({
                type: "POST",
                url: url.resolve_widget,
                data: {'bwobject_id': recordsToApprove[i],
                       'widget': 'approval_widget',
                       'decision': 'Accept'},
                success: function(json){
                    recordsToApprove = [];
                    $('#refresh_button').click();
                    checkRecordsToApprove();
                }
            });
        }
    });
};

function mini_approval(decision, event){
    var bwobject_id = event.currentTarget.parentElement.parentElement.cells[1].innerText;

    jQuery.ajax({
        type: "POST",
        url: url.resolve_widget,
        data: {'bwobject_id': bwobject_id,
               'widget': "approval_widget",
               'decision': decision},
        success: function(json){
            deselectAll();
            recordsToApprove = [];
            $('#refresh_button').click();     
            checkRecordsToApprove();
        }
    });
    oTable.fnDraw(false);
};

function deleteRecords(bwolist){
    for(i=0; i<recordsToApprove.length; i++){
        console.log(bwolist[i]);
        jQuery.ajax({
            url: url.delete_single,
            data: {'bwobject_id': bwolist[i]},
            success: function(){
                $('#refresh_button').click();
            }
        });
    }
};

$(document).ready(function(){
    $(".message").hide();

    $('.theform #submitButton').click( function(event) {
        event.preventDefault();

        var form_id = $(this)[0].form.parentElement.previousElementSibling.id;
        id_number = form_id.substring(form_id.indexOf("d")+1);
        btn_div_id = "decision-btns"+id_number;
        hr_id = "hr"+id_number;
        
        formdata = $(this)[0].value;
        formurl = event.currentTarget.parentElement.name;
        $.ajax({
            type: "POST",
            url: formurl,
            data: {'decision': formdata},
            success: function(data){
                $("#"+form_id).fadeOut(400);                
                $("#"+btn_div_id).fadeOut(400);
                $("#"+hr_id).fadeOut(400);
                current_number--;
            }
        });
        if (current_number === 0){
            $("#goodbye-msg").text("All Done!");
        }
    });

    window.setbwoid = function(id){
        bwoid = id;
        console.log(bwoid);
        data_preview(url_preview, bwoid, datapreview);
    };

    window.setDataPreview = function(dp, id){
        bwoid = id;
        datapreview = dp;
        console.log(url_preview);
        data_preview(url_preview, bwoid, datapreview);
    }

    $('#submitButtonMini').click( function (event){
        console.log(event);
    });

    $('body').append(
        '<div id="confirmationModal" class="modal hide fade" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">'+
            '<div class="modal-header">'+
                '<button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button>'+
                '<h3 id="myModalLabel">Please Confirm</h3>'+
            '</div>'+
            '<div class="modal-body">'+
                '<p>Are you sure you want to delete the selected records?</p>'+
            '</div>'+
            '<div class="modal-footer">'+
                '<button class="btn" data-dismiss="modal" aria-hidden="true">Cancel</button>'+
                '<a class="btn btn-danger" href="#" data-dismiss="modal" onclick="disapproveRecords()">Delete Records</a>'+
            '</div>'+
        '</div>');
    // $.ajax({
    //     url: "hp_maintable.html",
    //     success: function (data) { $('body').append(
    //         '<div id="confirmationModal" class="modal hide fade" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">'+
    //             '<div class="modal-header">'+
    //                 '<button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button>'+
    //                 '<h3 id="myModalLabel">Please Confirm</h3>'+
    //             '</div>'+
    //             '<div class="modal-body">'+
    //                 '<p>Are you sure you want to delete the selected records?</p>'+
    //             '</div>'+
    //             '<div class="modal-footer">'+
    //                 '<button class="btn" data-dismiss="modal" aria-hidden="true">Cancel</button>'+
    //                 '<a class="btn btn-danger" href="#" data-dismiss="modal" onclick="disapproveRecords()">Delete Records</a>'+
    //             '</div>'+
    //         '</div>'); },
    //     dataType: 'html'
    // });
});