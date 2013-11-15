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

});