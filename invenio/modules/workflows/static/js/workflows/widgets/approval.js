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

$(document).ready(function(){    
    var bwoid;
    var datapreview = "hd";
    var number_of_objs = $(".theform").length;
    var current_number = number_of_objs-1;
    console.log(number_of_objs);

    $(".message").hide();

    window.data_preview = function(format){
        console.log(bwoid);
        jQuery.ajax({
            url: "/admin/holdingpen/entry_data_preview?oid="+bwoid+"&recformat="+format,
            success: function(json){
                if(format == 'xm' || format == 'marcxml'){
                    if( json === ""){
                        json = "Preview not available";
                    }
                    $('div[id="object_preview'+bwoid+'"]').remove();
                    $('pre[id=data_preview'+ bwoid +']').remove();
                    if( $('pre[id=data_preview'+ bwoid +']').length === 0 ){
                        $('div[id="object_preview_container'+bwoid+'"]').append("<pre id=data_preview"+bwoid+" name='object_preview'></pre>");
                    }
                    $('pre[id=data_preview'+ bwoid +']').html(json);

                }else{
                    if( json === ""){
                        json = "Preview not available";
                    }
                    $('pre[id=data_preview'+ bwoid +']').remove();
                    $('div[id="object_preview'+bwoid+'"]').remove();
                    $('div[id="object_preview_container'+bwoid+'"]').append("<div id='object_preview"+bwoid+"'></div>");
                    $('div[id="object_preview'+bwoid+'"]').html(json);
                }
            }
        });
    };

    $('.theform #submitButton').click( function(event) {
        event.preventDefault();

        var form_id = $(this)[0].form.parentElement.previousElementSibling.id;
        console.log(form_id);

        id_number = form_id.substring(form_id.indexOf("d")+1);
        console.log(id_number);
        btn_div_id = "decision-btns"+id_number;
        hr_id = "hr"+id_number;
        
        formdata = $(this)[0].value;
        formurl = event.currentTarget.parentElement.name;
        $.ajax({
            type: "POST",
            url: formurl,
            data: formdata,
            success: function(data){
                $("#"+form_id).fadeOut(400);                
                $("#"+btn_div_id).fadeOut(400);
                $("#"+hr_id).fadeOut(400);
                current_number--;
            }
        });
        console.log(current_number);
        if (current_number === 0){
            $("#goodbye-msg").text("All Done!");
        }
        
    });

    window.setbwoid = function(id){
        bwoid = id;
        data_preview(datapreview);
    };

    window.setDataPreview = function(dp){
        datapreview = dp;
        data_preview(datapreview);
    };
});