/******************************************************************************
* WebNews JavaScript Library
*
* Includes functions to create and place the tooltips, and re-place them
* in case the browser window is resized.
*
* TODO: remove magic numbers and colors
*
******************************************************************************/

// Tooltips entry function. Create all the tooltips.
function create_tooltips(data) {

    // Get all the tooltips.
    var tooltips = data['tooltips'];

    // Only proceed if there are tooltips.
    if ( tooltips != undefined ) {

        // Get the story id and ln, to be used to create the "Read more" URL.
        var story_id = data['story_id'];
        var ln = data['ln'];

        // Keep an array of the tooltip notification and target elements,
        // to be used to speed up the window resize function later.
        var tooltips_elements = [];

        // Create each tooltip and get its notification and target elements.
        for (var i = 0; i < tooltips.length; i++) {
            tooltip = tooltips[i];
            tooltip_elements = create_tooltip(tooltip, story_id, ln);
            tooltips_elements.push(tooltip_elements);
        }

        /*
        // To cover most cases, we need to call re_place_tooltip both on page
        // resize and page scroll. So, let's combine both events usings ".on()"
        $(window).resize(function() {
            for (var i = 0; i < tooltips_elements.length; i++) {
                var tooltip_notification = tooltips_elements[i][0];
                var tooltip_target = tooltips_elements[i][1];
                re_place_tooltip(tooltip_notification, tooltip_target);
            }
        });

        $(window).scroll(function() {
            for (var i = 0; i < tooltips_elements.length; i++) {
                var tooltip_notification = tooltips_elements[i][0];
                var tooltip_target = tooltips_elements[i][1];
                re_place_tooltip(tooltip_notification, tooltip_target);
            }
        });
        */

        $(window).on("resize scroll", function() {
            for (var i = 0; i < tooltips_elements.length; i++) {
                var tooltip_notification = tooltips_elements[i][0];
                var tooltip_target = tooltips_elements[i][1];
                re_place_tooltip(tooltip_notification, tooltip_target);
            }
        });

    }

}

function create_tooltip(tooltip, story_id, ln) {

    // Get the tooltip data.
    var id       = tooltip['id'];
    var target   = tooltip['target'];
    var body     = tooltip['body'];
    var readmore = tooltip['readmore'];
    var dismiss  = tooltip['dismiss'];

    // Create the "Read more" URL.
    var readmore_url = '/news/story?id=' + story_id + '&ln=' + ln

    // Construct the tooltip html.
    var tooltip_html  = '<div id="' + id + '" class="ttn">\n';
    tooltip_html     += '    <div class="ttn_text">' + body + '</div>\n';
    tooltip_html     += '    <div class="ttn_actions">\n';
    // TODO: Do not add the "Read more" label until the /news interface is ready.
    //tooltip_html     += '        <a class="ttn_actions_read_more" href="' + readmore_url + '">' + readmore + '</a>\n';
    //tooltip_html     += '        &nbsp;|&nbsp;\n';
    tooltip_html     += '        <a class="ttn_actions_dismiss" href="#">' + dismiss + '</a>\n';
    tooltip_html     += '    </div>\n';
    tooltip_html     += '    <div class="ttn_arrow"></div>\n';
    tooltip_html     += '    <div class="ttn_arrow_border"></div>\n';
    tooltip_html     += '</div>\n';

    // Append the tooltip html to the body.
    $('body').append(tooltip_html);

    // Create the jquery element selectors for the tooltip notification and target.
    var tooltip_notification = $("#" + id);
    var tooltip_target = eval(target);

    // Place and display the tooltip.
    place_tooltip(tooltip_notification, tooltip_target);

    // Return the tooltip notification and target elements in an array.
    return [tooltip_notification, tooltip_target];
}

function place_tooltip(tooltip_notification, tooltip_target) {

    // Only display the tooltip if the tooltip_notification exists
    // and the tooltip exists and is visible.
    if ( tooltip_notification.length > 0 && tooltip_target.length > 0 && tooltip_target.is(":visible") ) {

        // First, calculate the top of tooltip_notification:
        // This comes from tooltip_target's top with some adjustments
        // in order to place the tooltip in the middle of the tooltip_target.
        var tooltip_target_height = tooltip_target.outerHeight();
        var tooltip_target_top = tooltip_target.offset().top;
        // The distance from the top of the tooltip_notifcation to the
        // arrow's tip is 16px (half the arrow's size + arrow's top margin)
        var tooltip_notification_top = tooltip_target_top + ( tooltip_target_height / 2 ) - 16
        if ( tooltip_notification_top < 0 ) {
            tooltip_notification_top = 0;
        }

        // Second, calculate the left of tooltip_notification:
        // This comes from the sum of tooltip_target's left and width
        var tooltip_target_left = tooltip_target.offset().left;
        var tooltip_target_width = tooltip_target.outerWidth();
        var tooltip_notification_left = tooltip_target_left + tooltip_target_width;

        // However, if tooltip_notification appears to be displayed outside the window,
        // then we have to place it on the other side of tooltip_target
        var tooltip_notification_width = tooltip_notification.outerWidth();
        var window_width = $(window).width();
        if ( ( tooltip_notification_left + tooltip_notification_width ) > window_width ) {
            // Place tooltip_notification on the other side, taking into account the arrow's size
            // The left margin of the tooltip_notification and half the
            // arrow's size is 16px
            tooltip_notification_left = tooltip_target_left - tooltip_notification_width - 16;
            // Why does 4px work perfectly here?
            tooltip_notification.children("div[class='ttn_arrow']").css("left", (tooltip_notification_width - 4) + "px");
            tooltip_notification.children("div[class='ttn_arrow']").css("border-color", "transparent transparent transparent #FFFFCC");
            tooltip_notification.children("div[class='ttn_arrow']").css("border-color", "rgba(255,255,255,0) rgba(255,255,255,0) rgba(255,255,255,0) #FFFFCC");
            // 2px is 4px - 2px here, since the arrow's border has a 2px offset from the arrow
            tooltip_notification.children("div[class='ttn_arrow_border']").css("left", "").css("left", (tooltip_notification_width - 2) + "px");
            tooltip_notification.children("div[class='ttn_arrow_border']").css("border-color", "transparent transparent transparent #FFCC00");
            tooltip_notification.children("div[class='ttn_arrow_border']").css("border-color", "rgba(255,255,255,0) rgba(255,255,255,0) rgba(255,255,255,0) #FFCC00");
            tooltip_notification.css("-moz-box-shadow", "-1px 1px 3px gray");
            tooltip_notification.css("-webkit-box-shadow", "-1px 1px 3px gray");
            tooltip_notification.css("-o-box-shadow", "-1px 1px 3px gray");
            tooltip_notification.css("box-shadow", "-1px 1px 3px gray");
        }

        // Set the final attributes and display tooltip_notification
        tooltip_notification.css('top',  tooltip_notification_top  + 'px');
        tooltip_notification.css('left', tooltip_notification_left + 'px');
        tooltip_notification.fadeIn();
        tooltip_notification.find("a[class='ttn_actions_dismiss']").click(function() {
            $.ajax({
                url: "/news/dismiss",
                data: { tooltip_notification_id: tooltip_notification.attr("id") },
                success: function(data) {
                    if ( data["success"] == 1 ) {
                        tooltip_notification.fadeOut();
                    }
                },
                dataType: "json"
            });
        });

    }

}

function re_place_tooltip(tooltip_notification, tooltip_target) {

    // Only display the tooltip if the tooltip_notification exists
    // and the tooltip exists and is visible.
    if ( tooltip_notification.length > 0 && tooltip_notification.is(":visible") && tooltip_target.length > 0 && tooltip_target.is(":visible") ) {

        // First, calculate the top of tooltip_notification:
        // This comes from tooltip_target's top with some adjustments
        // in order to place the tooltip in the middle of the tooltip_target.
        var tooltip_target_height = tooltip_target.outerHeight();
        var tooltip_target_top = tooltip_target.offset().top;
        // The distance from the top of the tooltip_notifcation to the
        // arrow's tip is 16px (half the arrow's size + arrow's top margin)
        var tooltip_notification_top = tooltip_target_top + ( tooltip_target_height / 2 ) - 16
        if ( tooltip_notification_top < 0 ) {
            tooltip_notification_top = 0;
        }

        // Second, calculate the left of tooltip_notification:
        // This comes from the sum of tooltip_target's left and width
        var tooltip_target_left = tooltip_target.offset().left;
        var tooltip_target_width = tooltip_target.outerWidth();
        var tooltip_notification_left = tooltip_target_left + tooltip_target_width;

        // However, if tooltip_notification appears to be displayed outside the window,
        // then we have to place it on the other side of tooltip_target
        var tooltip_notification_width = tooltip_notification.outerWidth();
        var window_width = $(window).width();
        if ( ( tooltip_notification_left + tooltip_notification_width ) > window_width ) {
            // Place tooltip_notification on the other side, taking into account the arrow's size
            // The left margin of the tooltip_notification and half the
            // arrow's size is 16px
            tooltip_notification_left = tooltip_target_left - tooltip_notification_width - 16;
            // Why does 4px work perfectly here?
            tooltip_notification.children("div[class='ttn_arrow']").css("left", (tooltip_notification_width - 4) + "px");
            tooltip_notification.children("div[class='ttn_arrow']").css("border-color", "transparent transparent transparent #FFFFCC");
            tooltip_notification.children("div[class='ttn_arrow']").css("border-color", "rgba(255,255,255,0) rgba(255,255,255,0) rgba(255,255,255,0) #FFFFCC");
            // 2px is 4px - 2px here, since the arrow's border has a 2px offset from the arrow
            tooltip_notification.children("div[class='ttn_arrow_border']").css("left", "").css("left", (tooltip_notification_width - 2) + "px");
            tooltip_notification.children("div[class='ttn_arrow_border']").css("border-color", "transparent transparent transparent #FFCC00");
            tooltip_notification.children("div[class='ttn_arrow_border']").css("border-color", "rgba(255,255,255,0) rgba(255,255,255,0) rgba(255,255,255,0) #FFCC00");
            tooltip_notification.css("-moz-box-shadow", "-1px 1px 3px gray");
            tooltip_notification.css("-webkit-box-shadow", "-1px 1px 3px gray");
            tooltip_notification.css("-o-box-shadow", "-1px 1px 3px gray");
            tooltip_notification.css("box-shadow", "-1px 1px 3px gray");
        }
        else {
            // The original left position of the tooltip_notification's arrow is -14px
            tooltip_notification.children("div[class='ttn_arrow']").css("left", "-14px");
            tooltip_notification.children("div[class='ttn_arrow']").css("border-color", "transparent #FFFFCC transparent transparent");
            tooltip_notification.children("div[class='ttn_arrow']").css("border-color", "rgba(255,255,255,0) #FFFFCC rgba(255,255,255,0) rgba(255,255,255,0)");
            // The original left position of the tooltip_notification's arrow border is -16px
            tooltip_notification.children("div[class='ttn_arrow_border']").css("left", "").css("left", "-16px");
            tooltip_notification.children("div[class='ttn_arrow_border']").css("border-color", "transparent #FFCC00 transparent transparent");
            tooltip_notification.children("div[class='ttn_arrow_border']").css("border-color", "rgba(255,255,255,0) #FFCC00 rgba(255,255,255,0) rgba(255,255,255,0)");
            tooltip_notification.css("-moz-box-shadow", "1px 1px 3px gray");
            tooltip_notification.css("-webkit-box-shadow", "1px 1px 3px gray");
            tooltip_notification.css("-o-box-shadow", "1px 1px 3px gray");
            tooltip_notification.css("box-shadow", "1px 1px 3px gray");
        }

        // Set the final attributes for tooltip_notification
        tooltip_notification.css('top',  tooltip_notification_top  + 'px');
        tooltip_notification.css('left', tooltip_notification_left + 'px');

        // If the tooltip_notification was previously hidden, show it.
        if ( !tooltip_notification.is(":visible") ) {
            tooltip_notification.show();
        }

    }

    else {

        // If the tooltip_notification was previously visible, hide it.
        if ( tooltip_notification.is(":visible") ) {
            tooltip_notification.hide();
        }

    }

}

