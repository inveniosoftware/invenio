$(document).ready(function() {
    $('#example').dataTable( {
        "bProcessing": true,
        "bServerSide": true,
        "bDestroy": true,
        "sAjaxSource": "/admin/holdingpen/load_table",
        // "sPaginationType": "bootstrap",
        // "fnServerData": fnDataTablesPipeline
    } );

    window.setTimeout(function() {
        $(".alert-message").fadeTo(500, 0).slideUp(500, function(){
            $(this).remove(); 
        });
    }, 5000);

    $('#refresh_button').on('click', function() {
        jQuery.ajax({
            url: "/admin/holdingpen/refresh",
            success: function(json){
                bootstrap_alert('Objects refreshed');
            }
        })
    });
});