$(document).ready(function() {

    var url_base = "/admin/holdingpen";
    var url_load_table = url_base + "/load_table";
    var url_refresh = url_base + "/refresh";

    $('#example').dataTable( {
        "bProcessing": true,
        "bServerSide": true,
        "bDestroy": true,
        "sAjaxSource": url_load_table,
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
            url: url_refresh,
            success: function(json){
                bootstrap_alert('Objects refreshed');
            }
        })
    });
});