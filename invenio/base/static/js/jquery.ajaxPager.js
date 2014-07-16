/*
 * jQuery pager plugin
 * Version 0.4.2 (11/8/2009)
 * @requires jQuery v1.3.1 or later
 * @requires jQuery UI v1.7.2 or later
 *
 *
 * Copyright (c) 2008-2009 Matthew Spence
 * Licensed under the GPL licenses:
 * http://www.gnu.org/licenses/gpl.html
 * 
 * For documentation, demos and more visit www.digitalintiution.co.uk/portfolio/ajaxpager-jquery-ui-widget
 *
 */

/*
 * First a little function to convert integer digits (eg 1,2,3) into words eg (one,two, three)
 */
var units = new Array ("Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen");
var tens = new Array ("Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety");

function ajax_pager_int_to_word(it) {
	var theword = "";
	var started;
	if (it>999) return it;
	if (it==0) return units[0];
	for (var i = 9; i >= 1; i--){
		if (it>=i*100) {
			theword += units[i];
			started = 1;
			theword += " hundred";
			if (it!=i*100) theword += " and ";
			it -= i*100;
			i=0;
		}
	};
	for (var i = 9; i >= 2; i--){
		if (it>=i*10) {
			theword += (started?tens[i-2].toLowerCase():tens[i-2]);
			started = 1;
			if (it!=i*10) theword += "-";
			it -= i*10;
			i=0
		}
	};
	
	for (var i=1; i < 20; i++) {
		if (it==i) {
			theword += (started?units[i].toLowerCase():units[i]);
		}
	};
	return theword;
}

(function($) {

	$.widget("ui.ajaxPager", {

		// Initial function to create html and behaviours
		_init: function() {

			this.initiated = false;

			// merger user defined animations with default animations
			this.options.animations = $.extend(true,this.options._animations,this.options.animations);


			// create cache
			if (typeof document.ajaxPagerCache != 'object') {
				document.ajaxPagerCache = {};
			}

			// find out the number of pages
			this.numberOfPages = 0;
			this.numberOfPages += this.options.pages.length;
			this.numberOfPages += this.element.children('*').length;

			this.currentPageNumber = this.options.page;

			// create the html and behaviours
			this.element.html(this._render());
      
      links = this._renderLinks();
      
			if (this.options.linkPosition=='above' || this.options.linkPosition=='both') {
				this.element.prepend(links);
			} 
			
			if (this.options.linkPosition=='below' || this.options.linkPosition=='both') {
				this.element.append(links);
			}

			this.setPage(this.currentPageNumber);

			this.initiated = true;	

			return this;

		},
		
		destroy: function() {
			$.widget.prototype.apply(this, arguments); // default destroy
		},

		// Create the the html and behaviours
		_render: function () {

			var pager = this;

			// find predfined pages
			var elements = this.element.children('*');

			this.element.empty();

			$.each(elements,function(t,element){
				if ($(element).attr('class').search(/page(\d+)/)!=-1) {
					pager.options.pages.splice([$(element).attr('class').match(/page(\d+)/)[1]-1],0, {
						content: $(element).html(),
						type: "string"
					});
				}

			});


			// page holder
			this.pagesElement = $("<div class='ajaxPagerPages'></div>");


			var pages = Array();

			var a = this;

			// foreach page
			$.each(this.options.pages, function (k,page) {
				var page = this;

				pages[k]={};

				// find content
				if (typeof page == 'string' && pager.type == 'string') {
					page = {
						content: page
					}
				} else if (typeof page == 'string') {
					page = {
						url: page
					}
				}

				// store page options in the page 
				pages[k].options = page;
				pages[k].pageNumber = k+1; 


			});
			this.pages = pages;

			$.each(pages, function (k,page) {

				if (typeof page != 'object' || typeof page.options != 'object') {
					i++;
					return true;
				}

				// add the global on show function to the page if it doesnt have one
				if (typeof page.options.onShow=='function') {
					page.options._onShow = function (i) {
						page.options.onShow(i);
						a.options.onPageShow(i); 
					}; 

				} else {
					page.options._onShow = function (i) {
						a.options.onPageShow(i);
					};
				}
				// add the global on load function to the page if it doesnt have one
				if (typeof page.options.onLoad=='function') {
					page.options._onLoad = function (i) {
						page.options.onLoad(i);
						a.options.onPageLoad(i); 
						page.loaded=true;
					}; 

				} else {
					page.options._onLoad = function (i) {
						a.options.onPageLoad(i);
						page.loaded=true;
					};
				}


				// if page type is undefined use the default
				if (typeof page.options.type != 'string') {
					page.options.type = pager.options.type;
				}

				// if page on demand is undefined use the default
				if (typeof page.options.preLoad == 'undefined') {
					if (pager.options.preLoad===true) {
						page.options.preLoad = true;
					} else {
						page.options.preLoad = false;
					}
				}

				// if page doesnt have a destroyOriginal use global
				if (typeof page.options.destroyOriginal == 'undefined') {
					if (pager.options.destroyOriginal === true) {
						page.options.destroyOriginal = true;
					} else {
						page.options.destroyOriginal = false;
					}
				}

				// add the global selector to the page if it doesn't have one
				if (page.options.selector!=false && typeof page.options.selector!='string' && typeof a.options.selector=='string') {
					page.options.selector = a.options.selector.replace(/{i}/g, k+1).replace("{k}",ajax_pager_int_to_word(k+1));
				} 

				// if not on demand load
				if (page.options.preLoad || page.options.type == 'element' || page.options.type=='string') {
					pager._loadPage(page);
				}

			});

			// Set up first page
			this.currentPage = this.pages[this.currentPageNumber-1];
			this.currentPage.element = $("<div id='ajaxPagerPage"+this.currentPageNumber+"' class='ajaxPagerPage ajaxPagerCurrentPage'></div>");
			this.currentPage.animationHandler = $("<div class='animationHandler'></div>");
			this.currentPage.element.html(this.currentPage.animationHandler);
			this.pagesElement.html(this.currentPage.element);
			return this.pagesElement;

		},

		_renderLinks: function () {

			this.links = Array();
			var links = this.links;

			// links holder
			this.linksE = $('<div class="ajaxPagerLinks"></div>');

			this._refreshLinks();

			return this.linksE;

		},
		
		// refresh the status on pages
		_refresh: function (pageChanged) {

			if (typeof pageChanged != 'boolean') {
				pageChanged = true;
			}

			var pager = this;
			var currentPage = this.currentPage;
			var previousPage = this.previousCurrentPage;

			// add page prefix
			if (typeof currentPage.options.prefix == 'string') {
				this.currentPage.prefix = currentPage.options.prefix.replace("{i}",this.currentPageNumber).replace("{k}",ajax_pager_int_to_word(this.currentPageNumber));
			} else if (typeof this.options.pagePrefix == 'string') {
				this.currentPage.prefix = this.options.pagePrefix.replace("{i}",this.currentPageNumber).replace("{k}",ajax_pager_int_to_word(this.currentPageNumber));;
			} else {
				this.currentPage.prefix = "";
			}

			// add page suffix
			if (typeof currentPage.options.suffix == 'string') {
				this.currentPage.suffix =	currentPage.options.suffix.replace("{i}",this.currentPageNumber).replace("{k}",ajax_pager_int_to_word(this.currentPageNumber));;
			} else if (typeof this.options.pageSuffix == 'string') {
				this.currentPage.suffix = this.options.pageSuffix.replace("{i}",this.currentPageNumber).replace("{k}",ajax_pager_int_to_word(this.currentPageNumber));;
			} else {
				this.currentPage.suffix = "";
			}

			// animation 
			if (pager.options.animation && pager.initiated && pageChanged) {

	 			// make current page the previous page
	 			previousPage.element.removeClass('ajaxPagerCurrentPage').addClass('ajaxPagerPreviousPage');

	 			// find if previous page should be animated out
	 			if (typeof previousPage.options.animation != 'boolean') {
	 				previousPage.options.animation = pager.options.animation;
	 			}

	 			// find if next page should be animated out
	 			if (typeof currentPage.options.animation != 'boolean') {
	 				currentPage.options.animation = pager.options.animation;
	 			}

	 			// find previous pages out animation
	 			if (typeof previousPage.options.animationOutPrevious != 'boolean' && typeof previousPage.options.animationOutPrevious != 'string' && this.previousPageNumber > this.currentPageNumber && typeof pager.options.animationOutPrevious == 'string') {
	 				previousPage.animationOut = pager.options.animationOutPrevious;
	 			} else if (this.previousPageNumber > this.currentPageNumber && typeof previousPage.options.animationOutPrevious == 'string') {
	 				previousPage.animationOut = previousPage.options.animationOutPrevious; 				
	 			} else if (typeof previousPage.options.animationOut != 'boolean' && typeof previousPage.options.animationOut != 'string') {
	 				previousPage.animationOut = pager.options.animationOut;
	 			} else {
	 				previousPage.animationOut = previousPage.options.animationOut;
	 			}

	 			// find next pages in animation
	 			if (typeof currentPage.options.animationInPrevious != 'boolean' && typeof currentPage.options.animationInPrevious != 'string' && this.previousPageNumber > this.currentPageNumber && typeof pager.options.animationInPrevious == 'string') {
	 				currentPage.animationIn = pager.options.animationInPrevious;
	 			} else if (this.previousPageNumber > this.currentPageNumber && typeof currentPage.options.animationInPrevious=='string') {
	 				currentPage.animationIn = currentPage.options.animationInPrevious; 				
	 			} else if (typeof currentPage.options.animationIn != 'boolean' && typeof currentPage.options.animationIn != 'string') {
	 				currentPage.animationIn = pager.options.animationIn;
	 			} else {
	 				currentPage.animationIn = currentPage.options.animationIn;
	 			}

	 			// find previous pages easing in effect
	 			if (typeof previousPage.options.easingIn != 'string') {
						previousPage.options.easingIn =	pager.options.easingIn;
	 			}

	 			// find previous pages easing out effect
	 			if (typeof previousPage.options.easingOut != 'string') {
						previousPage.options.easingOut =	pager.options.easingOut;
	 			}

	 			// find this pages easing in effect
	 			if (typeof currentPage.options.easingIn != 'string') {
						currentPage.options.easingIn =	pager.options.easingIn;
	 			}

	 			// find this pages easing out effect
	 			if (typeof currentPage.options.easingOut != 'string') {
						currentPage.options.easingOut =	pager.options.easingOut;
	 			}

	 			// find this pages in animation duration
	 			if (typeof currentPage.options.animationInDuration != 'integer') {
						currentPage.options.animationInDuration =	pager.options.animationInDuration;
	 			}

	 			// find this previous pages out animation duration
	 			if (typeof previousPage.options.animationOutDuration != 'integer') {
						previousPage.options.animationOutDuration =	pager.options.animationOutDuration;
	 			}

	 			// set up next page
	 			currentPage.animationHandler = $("<div class='animationHandler'></div>");
	 			currentPage.element = $("<div class='ajaxPagerPage ajaxPagerCurrentPage'></div>");
	 			currentPage.element.html(currentPage.animationHandler);

	 			this.pagesElement.append(currentPage.element);

	 			this._setCurrentContent();

	 			// Find page overlap 			
	 			if (typeof currentPage.options.animationOverlap != 'boolean' && typeof currentPage.options.animationOverlap != 'integer') {
	 				currentPage.options.animationOverlap = pager.options.animationOverlap;
	 			}

	 			// if no overlap - delay is same as in duration
	 			if (!currentPage.options.animationOverlap) {
	 				currentPage.animationInDelay = previousPage.options.animationOutDuration;
	 			} else 
	 			// if overlap is true no delay
	 			if (typeof currentPage.options.animationOverlap == 'boolean' && currentPage.options.animationOverlap) {
	 				currentPage.animationInDelay = 0;
	 			} 
	 			// other wise delay is in duration minus overlay
	 			else {
	 				currentPage.animationInDelay = previousPage.options.animationOutDuration - currentPage.options.animationOverlap; 					
	 			}

	 			// if this page is to be animated out
	 			if (previousPage.options.animation && typeof previousPage.animationOut == 'string') {

	 				// check that called animation is defined
	 				if (typeof this.options.animations[previousPage.animationOut]!='object') {
	 					throw new Error("ajaxPager: "+previousPage.animationOut+" is not a defined animation.");
	 				} else {

	 					// process animation
	 					var animation = this.options.animations[previousPage.animationOut];
	 					var mask = previousPage.element;
	 					var page = previousPage.animationHandler;
	 					for(var key in animation) {
	 						for(var key2 in animation[key]) {
	 							if (animation[key][key2].match(/['"]{1}/)) {
	 								animation[key][key2]=eval(animation[key][key2]); 								
	 							}
	 						}
	 					}

	 					previousPage.animationHandler.css('overflow','hidden');
	 					previousPage.element.css('overflow','hidden');

	 					// Apply animation handlers from css
	 					if (typeof animation['in'] == 'object') {
	 						previousPage.animationHandler.css(animation['in']);
	 					}

	 					// Apply animation masks from css
	 					if (typeof animation['maskIn'] == 'object') {
	 						previousPage.element.css(animation['maskIn']);
	 					}
	 					// Apply animation handlers animation
	 					if (typeof animation['out'] == 'object') {
	
	 						previousPage.animationHandler.animate(animation['out'],previousPage.options.animationOutDuration,previousPage.options.easingOut)
	 					}

	 					// Apply animation masks animation
	 					if (typeof animation['maskOut'] == 'object') {
	 						previousPage.element.animate(animation['maskOut'],previousPage.options.animationOutDuration,previousPage.options.easingOut);
	 					}

	 					// destroy previous page
	 					setTimeout(function() {
	 						previousPage.element.remove();
	 					},previousPage.options.animationOutDuration);

	 				}
						
	 			} else {
	 				// if no animation then just remove
	 				previousPage.element.remove();
	 			}

	 			// if next page is to be animationd in
	 			if (currentPage.options.animation && typeof currentPage.animationIn == 'string') {

	 				// check that called animation is defined
	 				if (typeof this.options.animations[currentPage.animationIn]!='object') {
	 					throw new Error("ajaxPager: "+currentPage.animationIn+" is not a defined animation.");
	 				} else {

	 					var animation = this.options.animations[currentPage.animationIn];
	 					var mask = previousPage.element;
	 					var page = previousPage.animationHandler;
	 					for(var key in animation) {
	 						for(var key2 in animation[key]) {
	 							if (animation[key][key2].match(/['"]{1}/)) {
	 								animation[key][key2]=eval(animation[key][key2]);
	 							}
	 						}
	 					}

	 					currentPage.animationHandler.css('overflow','hidden');
	 					currentPage.element.css('overflow','hidden');

	 					// Apply animation handlers from css
	 					if (typeof animation['out'] == 'object') {
	 						currentPage.animationHandler.css(animation['out']);
	 					}

	 					// Apply animation masks from css
	 					if (typeof animation['maskOut'] == 'object') {
	 						currentPage.element.css(animation['maskOut']);
	 					}

	 					// Apply animation handlers animation
	 					if (typeof animation['in'] == 'object') {
	 						setTimeout(function () {
	 							currentPage.animationHandler.animate(animation['in'],currentPage.options.animationInDuration,currentPage.options.easingIn); 						
	 						}, currentPage.animationInDelay);
	 					}

	 					// Apply animation masks animation
	 					if (typeof animation['maskIn'] == 'object') {
	 						setTimeout(function () {
	 							currentPage.element.animate(animation['maskIn'],currentPage.options.animationInDuration,currentPage.options.easingIn);
	 						}, currentPage.animationInDelay);
	 					}

	 					setTimeout(function () {
	 						currentPage.animationHandler.css('overflow','auto');
	 					}, currentPage.animationInDelay+currentPage.options.animationInDuration);
	 				}

	 			} else {
	 				// if no animation then just show
	 				currentPage.element.show();
	 			}

			} else {
	 			this._setCurrentContent();
			}

			return this;

		},
		
		// refresh the links for pages 
		_refreshLinks: function () {

			var pager = this;
			pager.linksE.find('*').remove();

			// Find out if wasted links before current page 			
			if (pager.options.linkPagesAfter +pager.options.linkPagesEnd - (pager.currentPageNumber)>0 && pager.options.linkOverflow) {
				wastedLinksBefore = pager.options.linkPagesAfter + pager.options.linkPagesEnd - (pager.currentPageNumber);
			} else {
				wastedLinksBefore = 0;
			}


			// Find out if wasted links before
			if (pager.options.linkPagesBefore +pager.options.linkPagesStart - (pager.numberOfPages - pager.currentPageNumber - 1)>0 && pager.options.linkOverflow) {
				wastedLinksAfter = pager.options.linkPagesBefore + pager.options.linkPagesStart - (pager.numberOfPages - pager.currentPageNumber-1);
			} else {
				wastedLinksAfter = 0;
			}

			$.each(this.pages,function (k,page) {

				if ((typeof pager.pages[k] == 'object') && (k+1<=pager.options.linkPagesStart || k>=pager.numberOfPages-pager.options.linkPagesEnd || (k>=pager.currentPageNumber-(pager.options.linkPagesBefore+wastedLinksAfter)-1 && k<=pager.currentPageNumber+(pager.options.linkPagesAfter+wastedLinksBefore)-1) || (k+1<pager.currentPageNumber && pager.options.linkPagesBefore==0) || (k+1>pager.currentPageNumber && (pager.options.linkPagesAfter)==0))) {

					// create link
					if (typeof page.options.linkText != 'string') {
						page.options.linkText = pager.options.linkText;
					}
					var linkText = page.options.linkText.replace("{i}",k+1).replace("{k}",ajax_pager_int_to_word(k+1));
					pager.links[k] = $("<div class='ajaxPagerPageLink page-"+(k+1)+"'>"+linkText+"</div>");

					// set status
					if (k+1!=pager.currentPageNumber) {
						pager.links[k].addClass('active');
					} else {
						pager.links[k].addClass('disabled').addClass('current');
					}

					// store page number
					pager.links[k][0].pageNumber = k+1;

					// bind event
					pager.links[k].click(function () {
						if($(this).hasClass('active')) { pager.setPage(this.pageNumber); }
					});

					pager.linksE.append(pager.links[k]);

				} else if (k==pager.currentPageNumber-(pager.options.linkPagesBefore+wastedLinksAfter)-2 || k==pager.currentPageNumber+(pager.options.linkPagesAfter+wastedLinksBefore)) {

					// create ...
					pager.links[k] = $("<div class='ajaxPagerPageBreak'>"+pager.options.linkPagesBreak+"</div>");

					pager.linksE.append(pager.links[k]);

				}
				
			});

			// add previous link
			if (this.options.previous) {
				previousLink = $('<div class="ajaxPagerPreviousLink">'+this.options.previousText+'</div>')
					.click(function () { if($(this).hasClass('active')) { pager.previousPage() }});
				// set status
				if (1!=pager.currentPageNumber) {
					previousLink.addClass('active');
				} else {
					previousLink.addClass('disabled').addClass('current');
				} 
				this.linksE.prepend(previousLink);
			}

			// add first link
			if (this.options.first) {
				var firstLink = $('<div class="ajaxPagerFirstLink">'+this.options.firstText+'</div>')
					.click(function () { if($(this).hasClass('active')) { pager.firstPage() }});

				// set status
				if (1!=pager.currentPageNumber) {
					firstLink.addClass('active');
				} else {
					firstLink.addClass('disabled').addClass('current');
				} 
				this.linksE.prepend(firstLink);

			}

			// add next link
			if (this.options.next) {
				var nextLink = $('<div class="ajaxPagerNextLink">'+this.options. nextText+'</div>')
					.click(function () { if($(this).hasClass('active')) { pager.nextPage() }});

				// set status	
				if (pager.numberOfPages!=pager.currentPageNumber) {
					nextLink.addClass('active');
				} else {
					nextLink.addClass('disabled').addClass('current');
				}	
				this.linksE.append(nextLink);

			}

			// add last link
			if (this.options.last) {
				var lastLink = $('<div class="ajaxPagerLastLink">'+this.options.lastText+'</div>')
					.click(function () { if($(this).hasClass('active')) { pager.lastPage() }});
				// set status
				if (pager.numberOfPages!=pager.currentPageNumber) {
					lastLink.addClass('active');
				} else {
					lastLink.addClass('disabled').addClass('current');
				} 
				this.linksE.append(lastLink);
			}

			return this;

		},
		
		_recalculatePageNumbers: function () {

			$.each(this.pages,function(k,page) {
				page.pageNumber = k+1;
			});
			
			return this;

		},
		
		_setCurrentContent: function () {

			// add prefix
			this.currentPage.prefixElement = $("<div class='prefix'></div>");
			this.currentPage.prefixElement.html(this.currentPage.prefix); 
			this.currentPage.animationHandler.html(this.currentPage.prefixElement);

			// add content
			this.currentPage.contentElement = $("<div class='content'></div>");
			this.currentPage.contentElement.html(this.pages[this.currentPageNumber-1].content); 
			this.currentPage.animationHandler.append(this.currentPage.contentElement);

			// add suffix
			this.currentPage.suffixElement = $("<div class='suffix'></div>");
			this.currentPage.suffixElement.html(this.currentPage.suffix); 
			this.currentPage.animationHandler.append(this.currentPage.suffixElement);

			return this;

		},

		_loadPage: function (page) {

			var pager = this;

			if (typeof page == 'number') {
				var page = this.pages[page-1]
			}

			// generate page content
			switch (page.options.type) {

				// for static strings
				case "string":
					page.content = page.options.content;
					page.options._onLoad(page.pageNumber); 									
					break;

				// for ajax
				case "ajax":

					// set content to "Loading..."
					if (typeof page.options.loadingText == 'string') {
						page.content = page.options.loadingText.replace("{i}",page.pageNumber).replace("{k}",ajax_pager_int_to_word(page.pageNumber));	
					} else {
						page.content = this.options.loadingText.replace("{i}",page.pageNumber).replace("{k}",ajax_pager_int_to_word(page.pageNumber));
					}

					// Find if page should use cache if avaliable
					if (typeof page.options.useCache != 'boolean') {
						page.options.useCache = this.options.useCache;
					}

					if (typeof document.ajaxPagerCache[page.options.url] == 'string' && page.options.useCache) {

						var data = document.ajaxPagerCache[page.options.url];

						if (typeof page.options.treatData != 'function') {
							page.options.treatData = pager.options.treatData;
						}

						data = page.options.treatData(data);

						if (typeof page.options.selector != 'undefined' && page.options.selector != false) {
							page.content = $(page.options.selector,$("<div>"+data+"</div>")).html();
						} else if ($(data).find('body').length>0) {
							page.content = $(data).find('body').html();
						} else {
							page.content = data;
						}

						page.options._onLoad(page.pageNumber);

						// set content 
						pager.currentPage.contentElement.html(page.content);

					} else {

						$.ajax({
						'url': page.options.url,
							success: function (data) {

								// write result into cache
								document.ajaxPagerCache[page.options.url] = data;

								if (typeof page.options.treatData != 'function') {
									page.options.treatData = pager.options.treatData;
								}

								data = page.options.treatData(data);

								if (typeof page.options.selector != 'undefined' && page.options.selector != false) {
									page.content = $(page.options.selector,$("<div>"+data+"</div>")).html();
								} else if ($(data).find('body').length>0) {
									page.content = $(data).find('body').html();
								} else {
									page.content = data;
								}

								// if it this page has a content element then load it in
								if (typeof page.contentElement == 'object') {

									if (page.pageNumber==pager.currentPageNumber && ((typeof page.options.fadeLoading == 'boolean' && page.options.fadeLoading) || (typeof page.options.fadeLoading != 'boolean' && typeof pager.options.fadeLoading == 'boolean' && pager.options.fadeLoading))) {
										// find loading fade duration
										if (typeof page.options.fadeLoadingDuration != 'number') {
											page.options.fadeLoadingDuration = pager.options.fadeLoadingDuration;
										}

										// fade out loading 
										page.contentElement.animate({'opacity':'0'},pager.options.fadeLoadingDuration/2);


										setTimeout(function() {
											// set content 
											pager.currentPage.contentElement.html(page.content);
											// fade in content
											page.contentElement.animate({'opacity':'1'},pager.options.fadeLoadingDuration/2);
										},pager.options.fadeLoadingDuration/2);

									} 
								}	
								page.options._onLoad(page.pageNumber);
							}							
						});
					}

					break;
				
				// for iframes
				case "iframe":

					page.content = '<iframe src ="'+page.options.url+'"><p>Your browser does not support iframes.</p></iframe>';
					page.options._onLoad(page.pageNumber);

					break;

				// other elements
				case "element":

					if ($(page.options.selector).length>0) {					
						page.content = $(page.options.selector).html()
					};
					if (page.options.destroyOriginal) {
						$(page.options.selector).remove();
					}
					page.options._onLoad(page.pageNumber);

					break;

			}

			return this;

		},

		_preLoad: function (pageNumber) { 	

			var pager = this;
			$.each(this.pages, function(k,page) {

				var pageExists = typeof pager.pages[k] == 'object';
				var preLoad = (typeof pager.options.preLoad == 'number' && k<pager.currentPageNumber+pager.options.preLoad && k>pager.currentPageNumber-1);
				var preLoadPrevious = (typeof pager.options.preLoadPrevious == 'number' && k>pager.currentPageNumber-2-pager.options.preLoadPrevious && k<pager.currentPageNumber-1);
				var pagerPreLoadAll = (typeof pager.options.preLoad == 'boolean' && pager.options.preLoad);
				var pagePreLoad = (typeof page.options.preLoad == 'boolean' && page.options.preLoad);

				if (pageExists && !page.loaded && (preLoad || preLoadPrevious || pagerPreLoadAll || pagePreLoad)) {
					pager._loadPage(pager.pages[k]);
				}
				
			});

			return this;

		},

		// set the page to pageNumber
		setPage: function (pageNumber) {

			// save previousPageNumber
			this.previousPageNumber = this.currentPageNumber;

			// save pageNumber
			this.currentPageNumber = pageNumber;

			// find out if the page has changed
			if (this.currentPageNumber == this.previousPageNumber) {
				var pageChanged = false;
			} else {
				var pageChanged = true;
			}

			// if the new page isn't loaded
			if (!this.pages[pageNumber-1].loaded) {
				// load the page
				this.loadPage(pageNumber);
			}

			// preload other pages based on the new current page
			this._preLoad();
			
			// save currentPage and previous page
			this.previousCurrentPage= this.currentPage;
			this.currentPage = this.pages[pageNumber-1];

			// refresh
			this._refresh(pageChanged);

			// refresh links
			this._refreshLinks();

			return this;

		},

		// set page to one more than current
		nextPage: function () {
			this.setPage(this.currentPageNumber+1);
			return this;
		},

		// set page to one less than current
		previousPage: function () {
			this.setPage(this.currentPageNumber-1);
			return this;
		},

		// set to first page
		firstPage: function () {
			this.setPage(1);
			return this;
		},

		// set to last page
		lastPage: function () {
			this.setPage(this.numberOfPages);
			return this;
		},

		loadPage: function (pageNumber) {
			this._loadPage(pageNumber);
			return this;
		},

		reloadPage: function (pageNumber) {
			this.pages[pageNumber-1].loaded = false;
			this.loadPage(pageNumber);
			this._refresh(false);
			return this;
		},

		reloadAll: function () {
			for(var k in this.pages) {
				this.reloadPage(parseInt(k)+1);
			}
			return this;
		},

		loadAll: function () {
			for(var k in this.pages) {
				this.loadPage(parseInt(k)+1);
			}
			return this;
		},

		reloadPageOnDemand: function (pageNumber) {
			this.pages[pageNumber-1].loaded = false;
			return this;
		},

		reloadAllOnDemand: function () {
			for(var k in this.pages) {
				this.reloadPageOnDemand(parseInt(k)+1);
			}
			return this;
		},

		addPage: function () {

			var pager = this;

			var pages = Array.prototype.splice.call(arguments, 0);


			// reverse sort array so that offset caused by the previously added items are not an issue
			pages.sort(function(a,b){return b.pageNumber - a.pageNumber});

			$.each(pages,function (i,pageOptions) {

				var page = {};

				// give page default pager options
				page.options = $.extend(true,pager.options,pageOptions);

				// calculate on load function
				if (typeof page.options.onLoad=='function') {
					page.options._onLoad = function (i) {
						page.options.onLoad(i);
						pager.options.onPageLoad(i); 
						page.loaded=true;
					};					
				} else {
					page.options._onLoad = function (i) {
						pager.options.onPageLoad(i);
						page.loaded=true;
					};
				}

				// page is not yet loaded
				page.loaded = false;

				// add the page
				var pos = page.options.pageNumber-1;

				pager.pages.splice(pos,0,$.extend(true, {}, page));

				pager.numberOfPages++;

				// recalculate current page number
				// if the page is before or equal to the current 
				// then current page is +1
				if (page.options.pageNumber<=pager.currentPageNumber) {
					pager.currentPageNumber++;
				}

			});

			// refresh
			pager._refreshLinks(false);
			pager._recalculatePageNumbers();

			return this;

		},

		removePage: function (pageNumbers) {

			var pager = this;
			// if pageNumbers is a single number just pop it in an array for easy handling
			if (typeof pageNumbers == 'number') {
				pageNumbers = [pageNumbers];
			}

			// reverse sort array so that offset caused by the previously removed items are not an issue
			pageNumbers.sort(function(a,b){return b - a});

			$.each(pageNumbers,function (i,pageNumber) {

				// If the page being removed is the current page set that pager to the next page
				// if there isn't a next page then the previous

				if (pager.currentPageNumber == pageNumber) {
					if (typeof pager.pages[pageNumber] == 'object') {
						pager.setPage(pageNumber+1);
					} else {
						pager.setPage(pageNumber-1);
					}
				}	

				// remove the page
				var pos = pageNumber-1;
				pager.pages.splice(pos,1);
				pager.numberOfPages--;

			});

			// refresh
			pager._refresh(false);
			pager._refreshLinks(false);
			pager._recalculatePageNumbers();

			return this;

		}


	});

	$.extend($.ui.ajaxPager, {
		defaults: {
			previous: true,
			destroyOriginal: true,
			previousText: "&lt;",
			next: true,
			nextText: "&gt;",
			first: true,
			firstText: "&#x7c;&lt;",
			last: true,
			lastText: "&gt;&#x7c;",
			linkPagesStart: 2,
			linkPagesBefore: 5,
			linkPagesAfter: 5,
			linkPagesEnd: 2,
			linkPagesBreak: "...",
			linkOverflow: true,
			linkPagesMax: 0,
			linkText: "{i}",
			onDemand: 0,
			preLoad: 0,
			preLoadPrevious: 0,
			pagePrefix: "",
			pageSuffix: "",
			animation: true,
			animationIn: "slide left",
			animationOut: "slide left",
			animationIn: "slide right",
			animationOut: "slide right",
			animationOutDuration: 300,
			animationInDuration: 300,
			animationOverlap: true,
			fadeLoading: true,
			fadeLoadingDuration: 300,
			easingIn: 'swing',
			easingOut: 'swing',
			useCache: true,
			page: 1,
			type: 'string',
			onPageShow: function () {},
			onPageLoad: function () {},
			pagePrefix: null,
			pageSuffix: null,
			loadingText: "Loading...",
			linkPosition: "below",
			pages: Array(),
			treatData: function (data) {return data},
			animations: {},
			_animations: {
				'fade': {
					'out': {
						'opacity':'0'
					},
					'in': {
						'opacity':'1'
					}
				},
				'slide top': {
					'out': {
						'top':'"-"+page.height()+"px"'
					},
					'in': {
						'top':'0px'
					}
				},
				'slide right': {
					'out': {
						'left': 'page.width()+"px"'
					},
					'in': {
						'left':'0px'
					}
				},
				'slide bottom': {
					'out': {
						'top': 'page.height()+"px"',
						'bottom':'"-"+page.height()+"px"'
					},
					'in': {
						'top':'0px',
						'bottom':'0px'
					}
				},
				'slide left': {
					'out': {
						'left':'"-"+page.width()+"px"'
					},
					'in': {
						'left':'0px'
					}
				},
				'swipe top': {
					'out':{
						'bottom':'+page.height()+"px"'
					},
					'in': {
						'bottom':'0px'
					}
				},
				'swipe right': {
					'out':{
						'left':'"-"+page.width()+"px"'
					},
					'in': {
						'left':'0px'
					},
					'maskOut': {
						'left':'+page.width()+"px"'
					},
					'maskIn': {
						'left':'0px'
					}
				},
				'swipe bottom': {
					'out':{
						'top':'"-"+page.height()+"px"'
					},
					'in': {
						'top':'0px'
					},
					'maskOut': {
						'top':'+page.height()+"px"'
					},
					'maskIn': {
						'top':'0px'
					}
				},
				'swipe left': {
					'maskOut':{
						'right':'page.width()+"px"'
					},
					'maskIn': {
						'right':'0px'
					}
				}
			}
		}
	});

})(jQuery);
