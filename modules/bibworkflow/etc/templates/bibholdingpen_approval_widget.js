$(document).ready(function(){
    var hpid = "{{ hpcontainer.id }}";
    var datapreview = "hd";

    window.data_preview = function(format){
        jQuery.ajax({
            url: "/admin/bibholdingpen/entry_data_preview?oid="+hpid+"&recformat="+format,
            success: function(json){
                if(format == 'xm' || format == 'marcxml'){
                    if( json == ""){
                        json = "Preview not available"
                    }
                    $('div[id="object_preview"]').remove();
                    $('pre[name="object_preview"]').remove();
                    if( $('pre[name="object_preview"]').length == 0 ){
                        $('div[id="object_preview_container"]').append("<pre name='object_preview'></pre>");
                    }
                    $('pre[name="object_preview"]').html(json);

                }else{
                    if( json == ""){
                        json = "Preview not available"
                    }
                    $('pre[name="object_preview"]').remove();
                    $('div[id="object_preview"]').remove();
                    $('div[id="object_preview_container"]').append("<div id='object_preview'></div>");
                    $('div[id="object_preview"]').html(json);
                }
            }
        })
    }

    window.setHpid = function(id){
        hpid = id;
        data_preview(datapreview);
    }

    window.setDataPreview = function(dp){
        datapreview = dp;
        data_preview(datapreview);
    }

    if ( window.addEventListener ) {
        $("div.btn-group[name='data_version']").bind('click', function(event){
            version = event.target.name;
        })
    };
});
