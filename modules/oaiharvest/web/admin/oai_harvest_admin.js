/*
 * This file is part of Invenio.
 * Copyright (C) 2010, 2011, 2012 CERN.
 *
 * Invenio is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
 * License, or (at your option) any later version.
 *
 * Invenio is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Invenio; if not, write to the Free Software Foundation, Inc.,
 * 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
 */

/*
$(function(){
  // initialise tha AJAX library
	  $.ajaxSetup(
    {cache: false,
      dataType: 'json',
      error: onAjaxError,
      type: 'POST',
      url: 'admin/oaiharvest/oaiharvestadmin.py/get_entries_fragment'
    }
  );
});
*/

function onAjaxError(XHR, textStatus, errorThrown){
    alert("Invenio encounted problems when retrieving the data : " + textStatus.toString() + " XHR : " + XHR.toString() + " ERROR: " + errorThrown.toString() );
}

function createPagerPage(baseIdentifier, pageNumber){
  // A function creating a pager page
  var page = document.createElement("div");
  page.setAttribute("id", baseIdentifier + "_" + pageNumber.toString());
  page.setAttribute("style", "border-width: 1px;");
  page.setAttribute("class", "oaiHarvestPagerPage");
  page.innerHTML = "Loading page " + (parseInt(pageNumber) + 1).toString() + "...";
  return page;
}

function onPageDataRetrieved(json){
  /** The operation performed upon the AJAX success */

  var el =$("#" + json.pagerPrefix.toString() + "_" +
      json.pageNumber.toString());
  el[0].innerHTML = json["html"];
  el.data("loaded", true);
}

function retrievePageAjax(pagerPrefix, pageNumber){
  /**
  * Create Ajax request.
  */

  var pageElement = $("#" + pagerPrefix.toString() + "_" + pageNumber.toString());

  if (pageElement.data("loaded") == true){
    return;
  }

  var year = pageElement.data("year");
  var month = pageElement.data("month");
  var day = pageElement.data("day");
  var start = pageElement.data("start");
  var limit = pageElement.data("limit");
  var filter = pageElement.data("filter");

  $.ajax({data: {"pagerPrefix" : pagerPrefix,
                 "pageNumber" : pageNumber,
                 "year" : year,
                 "month": month,
                 "day": day,
                 "start": start,
                 "limit": limit,
                 "filter": filter
	  },
          success: function(json){
            onPageDataRetrieved(json);
	  },
          async: true,
          dataType: 'json',
          error: onAjaxError,
          type: 'GET',
          url: 'get_entries_fragment'
  });
}

function adjustButtonsVisibility(pagerPrefix){
  /** A function adjusting the visbility of buttons on the navigation bar*/
  var visibilityRadius = 5; // how many entries should be visible before and
                            // after the current page
  var currentPage = $("#" + pagerPrefix).data("currentPage");
  var numberOfPages = $("#" + pagerPrefix.toString()).data("numberOfPages");

  $("#" + pagerPrefix).find(".oaiHarvestPagerNavigationLink").
      addClass("oaiHarvestPagerHiddenNavigationLink");

  for (i = (currentPage - visibilityRadius); i < (currentPage +
						  visibilityRadius); i++){
    // we do not care about the negative or exceeding the maximum
    // as they will simply not exist
    $("#" + pagerPrefix.toString() + "_btn_" + i.toString()).
	removeClass("oaiHarvestPagerHiddenNavigationLink");
  }

  if (currentPage != 0){
      $("#" + pagerPrefix + "_btn_previous").
	  removeClass("oaiHarvestPagerHiddenNavigationLink");
      $("#" + pagerPrefix + "_btn_first").
	  removeClass("oaiHarvestPagerHiddenNavigationLink");
  }

  if (currentPage != (numberOfPages - 1)){
      $("#" + pagerPrefix + "_btn_next").
	  removeClass("oaiHarvestPagerHiddenNavigationLink");
      $("#" + pagerPrefix + "_btn_last").
	  removeClass("oaiHarvestPagerHiddenNavigationLink");
  }
}

function chooseVisiblePage(pagerPrefix, pageNumber){
  $("#" + pagerPrefix).find(".oaiHarvestPagerPage").addClass("oaiHarvestPagerHiddenPage");
  $("#" + pagerPrefix.toString() + "_" + pageNumber.toString()).removeClass("oaiHarvestPagerHiddenPage");
  $("#" + pagerPrefix).find(".oaiHarvestPagerCurrentPageLink").removeClass("oaiHarvestPagerCurrentPageLink");
  $("#" + pagerPrefix.toString() + "_btn_" + pageNumber.toString()).addClass("oaiHarvestPagerCurrentPageLink");
  adjustButtonsVisibility(pagerPrefix);
}

function createPageChoiceBar(baseIdentifier, pages){
  // A function creating the page alowing to navigate inside the pager pages
  var bar = document.createElement("div");
  bar.setAttribute("class", "oaiHarvestPagerNavigationBar");

  var firstPageBtn = document.createElement("div");
  firstPageBtn.innerHTML = "&lt;&lt;";
  firstPageBtn.setAttribute("id", baseIdentifier + "_btn_first");
  firstPageBtn.setAttribute("class", "oaiHarvestPagerNavigationLink");
  bar.appendChild(firstPageBtn);

  var previousPageBtn = document.createElement("div");
  previousPageBtn.innerHTML = "&lt;";
  previousPageBtn.setAttribute("id", baseIdentifier + "_btn_previous");
  previousPageBtn.setAttribute("class", "oaiHarvestPagerNavigationLink");
  bar.appendChild(previousPageBtn);

  for (pageIndex in pages){
    var pageChoiceBtn = document.createElement("div");
    pageChoiceBtn.innerHTML = (parseInt(pageIndex) + 1).toString();
    pageChoiceBtn.setAttribute("id", baseIdentifier + "_btn_" + pageIndex.toString());
    pageChoiceBtn.setAttribute("class", "oaiHarvestPagerNavigationLink");
    bar.appendChild(pageChoiceBtn);
  }

  var nextPageBtn = document.createElement("div");
  nextPageBtn.innerHTML = "&gt;";
  nextPageBtn.setAttribute("id", baseIdentifier + "_btn_next");
  nextPageBtn.setAttribute("class", "oaiHarvestPagerNavigationLink");
  bar.appendChild(nextPageBtn);

  var lastPageBtn = document.createElement("div");
  lastPageBtn.innerHTML = "&gt;&gt;";
  lastPageBtn.setAttribute("id", baseIdentifier + "_btn_last");
  lastPageBtn.setAttribute("class", "oaiHarvestPagerNavigationLink");
  bar.appendChild(lastPageBtn);

  return bar;
}

function buildPagerFromData(data){
  // We start by adding layers for all the possible pages
  var containerLayer = $("#" + data.pagerId)[0];
  for (pageInd in data.pages){
    var page = createPagerPage(data.pagerId, pageInd);
    containerLayer.appendChild(page);
  }

  var pageChoiceBar = createPageChoiceBar(data.pagerId, data.pages);
  containerLayer.appendChild(pageChoiceBar);
}

function onPagerFirstPageClicked(pagerPrefix){
  retrievePageAjax(pagerPrefix, 0);
  $("#" + pagerPrefix.toString()).data("currentPage", 0);
  chooseVisiblePage(pagerPrefix, 0);
}

function prepareOnPagerFirstPageClickedHandler(pagerPrefix){
  return function(){
    return onPagerFirstPageClicked(pagerPrefix);
  }
}

function onPagerPreviousPageClicked(pagerPrefix){
  var currentPage = $("#" + pagerPrefix.toString()).data("currentPage") - 1;

  if (currentPage < 0){
      currentPage = 0;
  }

  retrievePageAjax(pagerPrefix, currentPage);
  $("#" + pagerPrefix.toString()).data("currentPage", currentPage);
  chooseVisiblePage(pagerPrefix, currentPage);
}

function prepareOnPagerPreviousPageClickedHandler(pagerPrefix){
  return function() {
    return onPagerPreviousPageClicked(pagerPrefix);
  };
}

function onPagerNextPageClicked(pagerPrefix){
  /** A handler for the operation of retrieving next page
   */
  var currentPage = $("#" + pagerPrefix.toString()).data("currentPage") + 1;
  var numberOfPages  = $("#" + pagerPrefix.toString()).data("numberOfPages");
  if (currentPage >= numberOfPages){
      currentPage = numberOfPages - 1;
  }

  retrievePageAjax(pagerPrefix, currentPage);
  $("#" + pagerPrefix.toString()).data("currentPage", currentPage);
  chooseVisiblePage(pagerPrefix, currentPage);
}

function prepareOnPagerNextPageClickedHandler(pagerPrefix){
  return function(){
    return onPagerNextPageClicked(pagerPrefix);
  };
}

function onPagerLastPageClicked(pagerPrefix){
  var currentPage  = $("#" + pagerPrefix.toString()).data("numberOfPages") - 1;
  retrievePageAjax(pagerPrefix, currentPage);
  $("#" + pagerPrefix.toString()).data("currentPage", currentPage);
  chooseVisiblePage(pagerPrefix, currentPage);
}

function prepareOnPagerLastPageClickedHandler(pagerPrefix){
  return function(){
    return onPagerLastPageClicked(pagerPrefix);
  }
}

function onPagerPageClicked(pagerPrefix, pageNumber){
  retrievePageAjax(pagerPrefix, pageNumber);
  $("#" + pagerPrefix.toString()).data("currentPage", pageNumber);
  chooseVisiblePage(pagerPrefix, pageNumber);
}

function prepareOnPagerPageClickedHandler(pagerPrefix, pageNumber){
  return function(){
    return onPagerPageClicked(pagerPrefix, pageNumber);
  };
}

function attachPagerData(baseId, pages){
  // making the pager alive - attaching all the necessary events causing pages
  // to be loaded using AJAX requests

  $("#" + baseId + "_btn_first").bind("click",
    prepareOnPagerFirstPageClickedHandler(baseId));
  $("#" + baseId + "_btn_previous").bind("click",
    prepareOnPagerPreviousPageClickedHandler(baseId));
  $("#" + baseId + "_btn_next").bind("click",
    prepareOnPagerNextPageClickedHandler(baseId));
  $("#" + baseId + "_btn_last").bind("click",
    prepareOnPagerLastPageClickedHandler(baseId));

  for (pageIndex in pages){
    $("#" + baseId + "_btn_" + pageIndex.toString()).
	bind("click", prepareOnPagerPageClickedHandler(baseId, parseInt(pageIndex)));
  }

  // saving the data related to the pager and its subpages
  $("#" + baseId.toString()).data("numberOfPages", pages.length);
  $("#" + baseId.toString()).data("currentPage", 0);

  for (pageIndex in pages){
      var linkElement = $("#" + baseId + "_" + pageIndex.toString());
      linkElement.data("loaded", false);
      linkElement.data("year", pages[pageIndex].year);
      linkElement.data("month", pages[pageIndex].month);
      linkElement.data("day", pages[pageIndex].day);
      linkElement.data("start", pages[pageIndex].start)
      linkElement.data("limit", pages[pageIndex].limit);
      linkElement.data("filter", pages[pageIndex].filter);
  }

  retrievePageAjax(baseId, 0);
  chooseVisiblePage(baseId, 0);
}

function buildPager(data){
	$("#" + data.pagerId).ajaxPager({
		previous: true, // previous page link is going to be displayed
		previousText: "&lsaquo; prev",   // prevous page link text
		next: true,             // whether to display a next page link
		nextText: "next &rsaquo;",       // next page link text
		first: true,            // whether to display a first page link
		firstText: "&laquo; first",// first page link text
		last: true,             // whether to display a last page link
		lastText: "last &raquo;", // last page link text
		linkPagesStart: 1,      // number of page links at start
		linkPagesBefore: 2,     // number of page links before current page
		linkPagesAfter: 4,      // number of page links after current page
		linkPagesEnd: 1,        // number of page link at end
		linkPagesBreak: "...",  // text for breaks in page links
		preLoad: 4,  // how many pages to preload ahead of current page
		selector: "#page{i} .content", // css selector for ajax response and same page elements
		destroyOriginal: true,  // whether to destory to original if content from same page elements
		page: 1,                // starting page
		type: 'ajax',           // default page type
		linkOverflow: true,// whether to let wasted links from one area of the pager to be added to another
		loadingText: "<h4>Loading page...</h4>", // Text to display before page loads
		linkText: "dasdasd",
		pages: data.pages
	});
}

$(document).ready(function(){
  $("#holdingpencontainer").treeview({
    animated: "fast",
    speed: 1,
    collapsed: "true",
    toggle: function(){
      if (!$(this).hasClass("loaded")){
        elementId = $(this).attr("id");
        var p = $("<li><span>Loading...</span></li>").appendTo("#" + elementId + "_ul");
        $("#holdingpencontainer").treeview({add : p});

        $.getJSON(serverAddress + "/admin/oaiharvest/oaiharvestadmin.py/getHoldingPenData",
          {elementId : $(this).attr("id")},
          function(json){
            $("#" + json.elementId + "_ul").empty();
            var p = $(json.html).appendTo("#" + json.elementId + "_ul");
            $("#holdingpencontainer").treeview({add : p});
            $("#" + json.elementId).addClass("loaded");
            if (json.additionalData != null){
              //buildPager(json.additionalData); <--- this was the opriginal call
	      //TODO: Piotr: Remove if everythion works
              buildPagerFromData(json.additionalData);
              attachPagerData(json.additionalData.pagerId, json.additionalData.pages);
            }
          });
      }
    }
  });
});
