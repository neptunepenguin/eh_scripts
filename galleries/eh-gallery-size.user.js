// ==UserScript==
// @name        gallery-size
// @namespace   EH
// @description Adds the number of files in each gallery, uses the EH API
// @include     https://e-hentai.org/
// @include     https://e-hentai.org/?page=*
// @include     https://e-hentai.org/?f_search=*
// @include     https://e-hentai.org/tag/*
// @include     https://exhentai.org/
// @include     https://exhentai.org/?page=*
// @include     https://exhentai.org/?f_search=*
// @include     https://exhentai.org/tag/*
// @license     GNU GPL v3
// @copyright   Aquamarine Penguin
// @version     2.0
// @grant       none
// ==/UserScript==
/*
@licstart

gallery-size.user.js - adds number of files in gallery minimal list.

Copyright (C) 2013 Aquamarine Penguin

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

(function() {
  var apiurl = "https://api.e-hentai.org/api.php";
  var apimax = 25;

  function addCount(elem, metadata) {
    var filecount = "";
    if ("undefined" !== typeof metadata.error) {
      console.error('gallery-size: no filecount in ' + metadata.gid);
      filecount += "error";
    } else {
      filecount += "fc: " + String(metadata.filecount);
    }
    filecount += " | "
    var count = document.createTextNode(filecount);
    var div = elem.getElementsByTagName("div")[0]
    div.insertBefore(count, div.firstChild);
  }

  function sendReq(gdata, elems, aurl) {
    var req = new XMLHttpRequest();
    req.addEventListener("load", function () {
      console.log("API Answer", req.status);
      var apirsp = JSON.parse(req.responseText);
      elems.forEach(function(e,i,arr) {
        addCount(e, apirsp.gmetadata[i]);
      });
    });
    req.open("POST", aurl, true);
    req.send(JSON.stringify(gdata));
  }

  var glinks = document.getElementsByClassName("glname");
  var all = Array.prototype.slice.call(glinks);
  var apiReqs = [];
  for (var i=0; i<all.length; i+=apimax)
    apiReqs.push(all.slice(i, i+apimax));
  apiReqs.forEach(function(elems) {
    var ids = elems.map(function(e) {
      var anchor = e.getElementsByTagName("a")[0];
      var ref = anchor.href.split("/");
      return [ref[4], ref[5]];
    });
    var gdata = {"method": "gdata", "gidlist": ids, "namespace": 1};
    // console.log eats repeated text
    console.log("send", gdata.gidlist[0], "of", gdata.gidlist.length);
    sendReq(gdata, elems, apiurl);
  });
})();

console.log("eh-gallery-size is active");

