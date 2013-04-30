$(document).ready(function(){
            $("tbody > tr.workflow").bind('click', function(){
                            hp_id = $(this).attr('name');
                            jQuery.ajax({
                                url: "/admin/bibworkflow/workflow_details?workflow_id=" + hp_id,
                                success: function(json){
                                    $("#myModal").html(json);
                                    $('#myModal').modal('show');}
                                })
            });
            $("tbody > tr.object").bind('click', function(){
                            hp_id = $(this).attr('name');
                            jQuery.ajax({
                                url: "/admin/bibworkflow/entry_details?entry_id=" + hp_id,
                                success: function(json){
                                    $("#myModal").html(json);
                                    $('#myModal').modal('show');}
                                })
            });
            
            $(".entry_message_button").bind('click', function(){
                            hp_id = $(this).attr('name');
                            TINY.box.show({url:"/match_details/1" + hp_id,width:"800",height:"600", animate:false});
            });
        });
