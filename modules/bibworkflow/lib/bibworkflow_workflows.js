$(document).ready(function(){
    bootstrap_alert = function() {}
    bootstrap_alert.warning = function(message) {
        $('#alert_placeholder').html('<div class="alert"><a class="close" data-dismiss="alert">×</a><span>'+message+'</span></div>')
    }


            window.setTimeout(function() {
                $("#alert_placeholder").fadeTo(500, 0).slideUp(500, function(){
                    // $(this).slideDown(500); 
                });
            }, 3500);
            $("#example_my_workflow").popover({
                trigger: 'hover',
                placement: 'right',
                content: "Workflow has been started."
            });  
            $("input[type=submit]").bind('click', function(){
                w_name = $(this).attr('name');
                jQuery.ajax({
                    url: "/admin/bibworkflow/run_workflow?workflow_name=" + w_name,
                    success: function(json){
                            bootstrap_alert.warning('Workflow has been started');
                    }
                })
            });
        });
        function activate_button(){
            $("input[type=submit]").removeAttr("disabled");
        }
