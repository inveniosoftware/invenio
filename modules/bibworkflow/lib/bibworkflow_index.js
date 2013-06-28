function load_data(){
    a = "";
    tags = $("span.sort_tag");
    for (i=0; i<tags.length; i++){
        a += $(tags[i]).attr('name')+" ";
    }
    jQuery.ajax({
                url: "/admin/bibworkflow/get_redis_values?key=" + a,
                success: function(json){
                    alert(json)}
                })
}

$(document).ready(function(){
            $("tbody > tr.workflow").bind('click', function(){
                            hp_id = $(this).attr('name');
                            jQuery.ajax({
                                url: "/admin/bibworkflow/workflow_details?id_workflow=" + hp_id,
                                success: function(json){
                                    $("#myModal").html(json);
                                    $('#myModal').modal('show');}
                                })
            });
            $("tbody > tr.object").bind('click', function(){
                            hp_id = $(this).attr('name');
                            jQuery.ajax({
                                url: "/admin/bibworkflow/entry_details?id_entry=" + hp_id,
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
                        url: "/admin/bibworkflow/get_redis_keys?key=" + $("form select#search_key_1").val(),
                        success: function(json){
                            $("form select#search_key_2").html(json);
                            $("form select#search_key_2").removeAttr('disabled');
                        }});
            $("form select#search_key_1").bind('change', function(){
                            key = $(this).val();
                            jQuery.ajax({
                                url: "/admin/bibworkflow/get_redis_keys?key=" + key,
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
