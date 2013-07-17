$(document).ready(function(){

    function bootstrap_alert(message) {
        $('#alert_placeholder').html('<div class="alert"><a class="close" data-dismiss="alert">×</a><span>'+message+'</span></div>')
    }

    $('#restart_button').on('click', function() {
        hpo_id = $(this).attr('name');
        console.log(hpo_id);
        jQuery.ajax({
            url: "/admin/holdingpen/restart_record?hpcontainerid=" + hpo_id,
            success: function(json){
                bootstrap_alert('Object restarted');
            }
        })
    });

    $('#restart_button_prev').on('click', function() {
        hpo_id = $(this).attr('name');
        console.log(hpo_id);
        jQuery.ajax({
            url: "/admin/holdingpen/restart_record_prev?hpcontainerid=" + hpo_id,
            success: function(json){
                bootstrap_alert('Object restarted from previous task');        
            }
        })
    });

    window.setTimeout(function() {
        $("#alert_placeholder").fadeTo(500, 0).slideUp(500, function(){
        });
    }, 2000);

    var hpid = "{{ hpcontainer.id }}";
    var datapreview = "hd";

    window.data_preview = function(format){
        jQuery.ajax({
            url: "/admin/holdingpen/entry_data_preview?oid="+hpid+"&recformat="+format,
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

