/**
  Manipulating the interface of HEPData
*/

function expandCollapseDataPlots(start_point, class_main, class_plots, class_conditional, expander_id, expanded_msg, collapsed_msg, filescell_id){
  /**
     Expands or collapses layers
     table_obj - pointer to the table
     class_main - class of layer on which we will decide if to expand (and which should be expanded)
     class_plots - class of layers with plots (will be conditionally expanded)
     class_conditional - class of the layer deciding if plots should be expanded (expanding if this is visible)
  */


  if ($('.' + class_main).is(":hidden")){
    // collect existing heights
    var heights =  collectHeights(start_point);
    // expand
    $('.' + class_main).show();// css("display", null);
    //    $('.' + class_main).slideDown('slow', function() {});
    //    if ($('.' + class_conditional).css("display") != "none"){
    if (!$('.' + class_conditional).is(":hidden")){
      // in the case masterplot is expanded, expand also other plots
      $('.' + class_plots).show();//css("display", null);
      //      $('.' + class_plots).slideDown('slow', function(){});
    }
    $('#' + expander_id).html(expanded_msg);
    // now adjust heights ... we want to keep header heights intact
    var masterplotHeight = $(start_point).find(".masterplot_cell").height();
    var correctNewHeight = masterplotHeight - heights["titlesHeight"];
    if (correctNewHeight < 0){
	correctNewHeight = 0;
    }

    $($(start_point).find("tr")[0]).height(correctNewHeight);
  } else {
    var heights =  collectHeights(start_point);
    $('.' + class_main).hide(); //css("display", "none");
    $('.' + class_plots).hide(); //css("display", "none");
    $('#' + expander_id).html(collapsed_msg);

    $($(start_point).find("tr")[0]).height(0); // setting as small height as possible
    var heights2 =  collectHeights(start_point);
    if (heights2["titlesHeight"] - 10 > heights["titlesHeight"]){
	// restore !
	$($(start_point).find("tr")[0]).height(heights["firstHeight"]);
    }
  }
}

function selectDataColumn(column_class){
  $("." + column_class).addClass('dataSelected');//css("background-color", "yellow");
}

function unselectDataColumn(column_class){
  $("." + column_class).removeClass('dataSelected');//css("background-color", null);
}


function collectHeights(tableObject){
    /* Colelcts heights of different components of a */
    var rows = $(tableObject).find("tr");
    var firstHeight = $(rows[0]).height();
    var i = 1;
    var totalHeight = 0;

    while ($(rows[i]).attr("class") != "expander_row"){
	totalHeight += $(rows[i]).height();
	i += 1;
    }

    var masterplotHeight = $(tableObject).find(".masterplot_cell").height();

    return {"firstHeight" : firstHeight, "titlesHeight" : totalHeight, "masterHeight" : masterplotHeight};
}

$(window).load(function() {
    var images_to_check = $(".hepdataimg");
    for (var i = 0; i< images_to_check.length; i++){
	var img = images_to_check[i];

        if (typeof img.naturalWidth != "undefined" && img.naturalWidth == 0) {
	    $(img.parentNode).html("&nbsp;Image temporarly&nbsp;<br>&nbsp; not available&nbsp;")
        }
    }
});
