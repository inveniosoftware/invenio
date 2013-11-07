/*
 * This file is part of Invenio.
 * Copyright (C) 2013 CERN.
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


var url_base = "/admin/holdingpen";
var url_workflow_details = url_base + "/workflow_details";
var url_entry_details = url_base + "/entry_details";
var url_continue = url_base + "/continue_record";
var url_redis_get_keys = url_base + "/get_redis_keys";
var url_redis_get_values = url_base + "/get_redis_values";

function load_data(){
    a = "";
    tags = $("span.sort_tag");
    for (i=0; i<tags.length; i++){
        a += $(tags[i]).attr('name')+" ";
    }
    jQuery.ajax({
                url: url_redis_get_values + "?key=" + a,
                success: function(json){
                    alert(json)}
                })
}

$(document).ready(function(){
            $("tbody > tr.workflow").bind('click', function(){
                            hp_id = $(this).attr('name');
                            jQuery.ajax({
                                url: url_workflow_details + "?id_workflow=" + hp_id,
                                success: function(json){
                                    $("#myModal").html(json);
                                    $('#myModal').modal('show');}
                                })
            });
            $("tbody > tr.object").bind('click', function(){
                            hp_id = $(this).attr('name');
                            jQuery.ajax({
                                url: url_entry_details + "?id_entry=" + hp_id,
                                success: function(json){
                                    $("#myModal").html(json);
                                    $('#myModal').modal('show');}
                                })
            });
            
            $(".entry_message_button").bind('click', function(){
                            hp_id = $(this).attr('name');
                            TINY.box.show({url:"/match_details/1" + hp_id,width:"800",height:"600", animate:false});
            });

            jQuery.ajax({
                        url: url_get_redis_keys + "?key=" + $("form select#search_key_1").val(),
                        success: function(json){
                            $("form select#search_key_2").html(json);
                            $("form select#search_key_2").removeAttr('disabled');
                        }});
            $("form select#search_key_1").bind('change', function(){
                            key = $(this).val();
                            jQuery.ajax({
                                url: url_get_redis_keys + "?key=" + key,
                                success: function(json){
                                    $("form select#search_key_2").html(json);
                                    $("form select#search_key_2").removeAttr('disabled');
                                }});
            });

            $("form span#search_button").bind('click', function(){
                a = $("div#search_tags").html()
                a += "<span class='label sort_tag' name='"+$("form select#search_key_1").val()+":"+$("form select#search_key_2").val()+"'>"+$("form select#search_key_1").val()+": "+$("form select#search_key_2").val()+"&nbsp;<i class='icon-remove remove_sort_tag'></i></span>&nbsp;"
                $("div#search_tags").html(a)
                load_data();
            });
        });
