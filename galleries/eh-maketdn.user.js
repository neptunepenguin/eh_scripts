// ==UserScript==
// @name        eh-maketdn
// @namespace   e-hentai
// @description generates a downvote request for the gallery
// @include     http://e-hentai.org/g/*
// @include     https://e-hentai.org/g/*
// @include     https://exhentai.org/g/*
// @version     0.5
// @grant       none
// ==/UserScript==
/*
@usage_start

The script provides a clickable toggle in the top left corner of the page.
Clicking the box opens a dialog containing text about all the tags you have
voted down in the current gallery.  The text is formatted in a way easy to copy
paste into the Tagging and Abuse thread.

Q&A

1. Can you automate the posting to the thread?
No, do not want to make it easier for uselessly spamming the thread.

2. Can you make a request for upvotes too?
No, we have enough people already who will upvote it without checking anyway.

@usage_end

@licstart

eh-maketdn.user.js - downvote request maker

Copyright (C) 2021 Aquamarine Penguin

This JavaScript code is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License (GNU GPL) as published by the
Free Software Foundation, either version 3 of the License, or (at your option)
any later version.

This JavaScript code is distributed WITHOUT ANY WARRANTY; without even the
implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See
the GNU GPL for more details.

The full text of the license can be found in the COPYING file.  If you cannot
find this file, see <http://www.gnu.org/licenses/>.

@licend
*/

"use strict;";

(function () {
  var script_uuid = "eh-maketdn";

  function scriptPanel() {
    var panelId = "penguin-script-panel";
    var panel = document.getElementById(panelId);
    if (panel) {
      return panel;
    }
    var panel = document.createElement("div");
    var style = "position:fixed;z-index:100;top:0;left:0;";
    style += "padding:20px;border-radius:3px;border:2px solid white;";
    style += "text-align:left;font-size:10pt;";
    panel.style = style;
    panel.setAttribute("id", panelId);
    document.body.appendChild(panel);
    // we may wish to override this one often
    panel.style.cursor = "auto";
    return panel;
  }

  function getTagText(el) {
    var ns = el.parentNode.parentNode.parentNode.firstChild.textContent;
    return ns + el.textContent;
  }

  function makeTdnList() {
    var innerdiv = document.createElement("div");
    var downvotes = document.getElementsByClassName("tdn");
    var loc = window.location;  // just in case
    var url = loc.protocol + "//" + loc.host + loc.pathname;
    var urltext = document.createTextNode(url);
    var urlp = document.createElement("div");
    urlp.appendChild(urltext);
    innerdiv.appendChild(urlp);
    var i, j, arr, chunk = 3;
    for (i=0, j=downvotes.length; i<j; i+=chunk) {
      arr = Array.prototype.slice.call(downvotes, i, i+chunk);
      var p = document.createElement("div");
      arr = arr.map(getTagText);
      var txt = document.createTextNode(arr.join(" , "));
      p.appendChild(txt);
      innerdiv.appendChild(p);
    }
    return innerdiv;
  }

  var vote = document.createElement("div");
  var div_style = "opacity:0.9;position:fixed;z-index:110;top:0;left:20%;";
  div_style += "padding:20px;border-radius:3px;border:2px solid beige;";
  div_style += "text-align:left;font-size:10pt;background:snow;color:black;";
  vote.style = div_style;
  document.body.appendChild(vote);
  vote.style.display = "none";

  var label = document.createElement("div");
  var down = document.createTextNode("down");
  label.style.textAlign = "center";
  label.appendChild(down);

  var toggle = document.createElement("div");
  toggle.style.textAlign = "center";
  var show = document.createTextNode("show");
  var hide = document.createTextNode("hide");
  toggle.style.padding = "2px";
  toggle.style.cursor = "pointer";
  toggle.style.color = "turquoise";
  toggle.appendChild(show);
  toggle.addEventListener("click", function(e) {
    if (toggle.contains(show)) {
      innerdiv = makeTdnList();
      innerdiv.setAttribute("id", "eh-downvotes-user-panel");
      vote.appendChild(innerdiv);
      vote.style.display = "block";
      toggle.style.color = "sienna";
      localStorage.setItem(script_uuid, "show");
      toggle.replaceChild(hide, show);
    } else {
      document.getElementById("eh-downvotes-user-panel").remove();
      vote.style.display = "none";
      toggle.style.color = "turquoise";
      localStorage.setItem(script_uuid, "hide");
      toggle.replaceChild(show, hide);
    }
  });

  var panel = scriptPanel();
  panel.appendChild(label);
  panel.appendChild(toggle);
  var state = localStorage.getItem(script_uuid);
  if ("show" === state) {
    toggle.click();
  }
})();

// useful to tell us if something blew up
console.log("eh-maketdn is active");

