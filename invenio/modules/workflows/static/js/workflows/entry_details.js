if ( window.addEventListener ) {
        $("div.btn-group[name='object_preview_btn']").bind('click', function(event){
          var format = event.target.name;
          jQuery.ajax({
                            url: "/admin/bibworkflow/entry_data_preview?oid={{ entry.id }}&format=" + format,
                            success: function(json){
                                if(format == 'xm' || format == 'marcxml'){
                                    $('div[name="object_preview"]').wrapAll('<debug>').text(json);
                                }else{
                                    $('div[name="object_preview"]').html(json);
                                }
                            }
                     })
    });
}

