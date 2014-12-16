// Globals for original video size when going fullscreen
var normalHeight = 0;
var normalWidth = 0;

$(document).ready(function() {
	// Takes the selectbox containing the video sources and initiates the video tag with it
	$('#mejs-resolution').each(function() {
		// Assumes that the select element (dropdown) is in the same div or other element as the video element
		var parent = $(this).parent()
		var video = parent.find("video")[0]
		initiate_video(this, video)
	});
	// Initialised the ME player
	$('#mediaelement').mediaelementplayer({
		features: ['playpause', 'current', 'progress', 'duration', 'invresolution', 'volume', 'invfullscreen'],
		defaultVideoWidth: 854,
		defaultVideoHeight: 480
	});
	// The Download Button and Popup
	var download_popup_shown = false;
	$("#video_download_button").click(function(e) {
		e.stopPropagation();
		if (!download_popup_shown) {
			var button_position = $("#video_download_button").position();
			var button_height = $("#video_download_button").height();
			var button_width = $("#video_download_button").width();
			var popup_height = $("#video_download_popup_box").height();
			var popup_width = $("#video_download_popup_box").width();
			$("#video_download_popup_box").css("left", button_position.left - popup_width/2.0 + button_width/2.0);
			$("#video_download_popup_box").css("top", button_position.top - popup_height - button_height - 10);
			$("#video_download_popup_box").fadeIn("fast");
			download_popup_shown = true
		}
		else {
			$("#video_download_popup_box").fadeOut("fast");
			download_popup_shown = false;
		};
	});
	$(document).click(function(){
		$("#video_download_popup_box").fadeOut("fast");
		download_popup_shown = false;
	});
});

// Appends the selectbox to the ME player controls
(function($) {
	// Currently only works for the HTML5 player
	if (!!document.createElement('video').canPlayType) {
		MediaElementPlayer.prototype.buildinvresolution = function(player, controls, layer, media) {
			var resolution_div = $('<div class="mejs-resolution"></div>');
			var resolution_control = $('#mejs-resolution');
			resolution_div.append(resolution_control);
			resolution_div.appendTo(controls);
			resolution_control.each(function() {
				// When the selection is changed, reinitialise the video tag
					this.onchange = function() {
						initiate_video(this, $('#mediaelement')[0]);
						player.options.alwaysShowControls = false;
						
					};
				// Makes the control bar of ME player fade in a nice way when we change the source
					this.onmouseover = function() {
						player.options.alwaysShowControls = true;
					}
					this.onblur = function() {
						player.options.alwaysShowControls = false;
						controls.stop(true, true).fadeOut(200, function() {
							$(this).css('visibility','hidden');
							$(this).css('display','block');
						});
					}
				});
		};
	};
})(jQuery);

// Hack to the original fullscreen plugin of ME player to remember the size in case we switch to higher or lower resolution sources
(function($) {
	MediaElementPlayer.prototype.buildinvfullscreen = function(player, controls, layers, media) {

		if (!player.isVideo)
			return;

		var			 
			container = player.container,
			fullscreenBtn = 
				$('<div class="mejs-button mejs-fullscreen-button"><button type="button"></button></div>')
				.appendTo(controls)
				.click(function() {
					var goFullscreen = (mejs.MediaFeatures.hasNativeFullScreen) ?
									!media.webkitDisplayingFullscreen :
									!media.isFullScreen;
					setFullScreen(goFullscreen);
				}),
			setFullScreen = function(goFullScreen) {
				switch (media.pluginType) {
					case 'flash':
					case 'silverlight':
						media.setFullscreen(goFullScreen);
						break;
					case 'native':

						if (mejs.MediaFeatures.hasNativeFullScreen) {
							if (goFullScreen) {
								media.webkitEnterFullScreen();
								media.isFullScreen = true;
							} else {
								media.webkitExitFullScreen();
								media.isFullScreen = false;
							}
						} else {
							if (goFullScreen) {

								// make full size
								container
									.addClass('mejs-container-fullscreen')
									.width('100%')
									.height('100%')
									.css('z-index', 1000);

								player.$media
									.width('100%')
									.height('100%');


								layers.children('div')
									.width('100%')
									.height('100%');

								fullscreenBtn
									.removeClass('mejs-fullscreen')
									.addClass('mejs-unfullscreen');

								player.setControlsSize();
								media.isFullScreen = true;
							} else {

								container
									.removeClass('mejs-container-fullscreen')
									.width(normalWidth)
									.height(normalHeight)
									.css('z-index', 1);

								player.$media
									.width(normalWidth)
									.height(normalHeight);

								layers.children('div')
									.width(normalWidth)
									.height(normalHeight);

								fullscreenBtn
									.removeClass('mejs-unfullscreen')
									.addClass('mejs-fullscreen');

								player.setControlsSize();
								media.isFullScreen = false;
							}
						}
				}
			};

		$(document).bind('keydown',function (e) {
			if (media.isFullScreen && e.keyCode == 27) {
				setFullScreen(false);
			}
		});

	}

})(jQuery);

// Initialises a video tag by parsing data attributes of a selectbox
// Tryes to do some tricks to MediaElement if it is initialised
function initiate_video(dropdown, video) {
	// If no video element is given, fail
	if(!video) return;
	
	// Initialise variables from dropdown (html select element) data attributes
	var webm_src = $(dropdown.options[dropdown.selectedIndex]).attr('data-src-webm');
	var ogv_src = $(dropdown.options[dropdown.selectedIndex]).attr('data-src-ogv');
	var mp4_src = $(dropdown.options[dropdown.selectedIndex]).attr('data-src-mp4');
	var webm_type = $(dropdown.options[dropdown.selectedIndex]).attr('data-type-webm');
	var ogv_type = $(dropdown.options[dropdown.selectedIndex]).attr('data-type-ogv');
	var mp4_type = $(dropdown.options[dropdown.selectedIndex]).attr('data-type-mp4');
	var poster_src = $(dropdown.options[dropdown.selectedIndex]).attr('data-poster');
	var video_width = $(dropdown.options[dropdown.selectedIndex]).attr('data-video-width');
	var video_height = $(dropdown.options[dropdown.selectedIndex]).attr('data-video-height');
	
	// The video might have been running, save its position
	var position = video.currentTime;
	var playing = !(video.paused);
	
	// After the video was loaded, jump to the old position
	try {
		video.addEventListener("loadedmetadata", function() {
			// don't set if zero; that will drop the poster and cause preload
			if(position>0) video.currentTime = position;
			if(playing) video.play();
			this.removeEventListener("loadedmetadata",arguments.callee,true);
		}, true);
	}
	catch(err) {
		// IE will crash 
	};
	
	// Set the new dimensions
	video.style.width = video_width;
	video.style.height = video_height;
	normalWidth = video_width;
	normalHeight = video_height;
		
	// Apply the new poster
	if (poster_src != "None") {
		$(video).attr("poster", poster_src);
	};
	
	// Determine which video should be played and set it as source
	// First check HTML5 support
	if (!!document.createElement('video').canPlayType) {
		$(video).empty()
		if (mp4_type) {
			$('<source/>', {
				src: mp4_src, type: mp4_type
			}).appendTo(video);
		};
		if (webm_type) {
			$('<source/>', {
				src: webm_src, type: webm_type
			}).appendTo(video);
		};
		if (ogv_type) {
			$('<source/>', {
				src: webm_src, type: webm_type
			}).appendTo(video);
		};
	}
	// If not, we can only use Flash, set the mp4 source if available
	else {
		try {
			$(video).empty()
			if (mp4_type) {
				$('<source/>', {
					src: mp4_src, type: mp4_type
				}).appendTo(video);
				video.player.setSrc(mp4_src);
			};
		}
		catch(err) {
			
		};
	};
	
	// Update the mediaelement
	try {
		if(!video.player.media.isFullScreen) {
			$('.mejs-container').each(function(){
				this.style.width = video_width;
				this.style.height = video_height;
			});
			$('.mejs-overlay').each(function(){
				this.style.width = video_width;
				this.style.height = video_height;
			});
			video.player.$media.width(video_width).height(video_height);
			video.player.setControlsSize();
		}
		else {
			video.style.width = "100%";
			video.style.height = "100%"
		};
	}
	catch(err) {
		// Mediaelement was not initialized
	};
	
	// Make the control visible
	dropdown.style.display = "inline";
	
	// Reload the video

	try {
		video.load();
	}
	catch(err) {
		// IE  will crash
	}
}

