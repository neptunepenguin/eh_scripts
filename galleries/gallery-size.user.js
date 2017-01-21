// ==UserScript==
// @name        gallery-size
// @namespace   EH
// @description Adds the number of files in each gallery, uses the EH API
// @include     https://e-hentai.org/
// @include     https://e-hentai.org/?page=*
// @include     https://e-hentai.org/*Apply+Filter
// @include     https://exhentai.org/
// @include     https://exhentai.org/?page=*
// @include     https://exhentai.org/*Apply+Filter
// @include     http://e-hentai.org/
// @include     http://e-hentai.org/?page=*
// @include     http://e-hentai.org/*Apply+Filter
// @include     http://g.e-hentai.org/
// @include     http://g.e-hentai.org/?page=*
// @include     http://g.e-hentai.org/*Apply+Filter
// @license     GNU GPL v3
// @copyright   Aquamarine Penguin
// @version     1.2
// @grant       none
// ==/UserScript==
/*
@licstart

gallery-size.user.js - adds number of files in gallery list.

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

var apiurl = "http://g.e-hentai.org/api.php";
var apimax = 25;
(function(classes) {
  var reqs = get_reqs(classes, apimax);
  reqs.forEach(function(elems) {
    var ids   = elems.map(function(e) {
      var anchor = (e.getElementsByClassName('it5')[0]).firstElementChild;
      var ref    = anchor.href.split('/');
      return [ref[4], ref[5]];
    });
    var gdata = { "method" : "gdata", "gidlist" : ids };
    send_req(gdata, elems, apiurl);
  });
})(['gtr0','gtr1']);
function get_reqs(classes, maxlen) {
  var elems = classes.map(function(x) {
    return Array.prototype.slice.call(document.getElementsByClassName(x));
  });
  var all = elems[0];
  for (var i=1; i < elems.length; i++) all = all.concat(elems[i]);
  var api_reqs = [];
  for (var i=0; i<all.length; i+=maxlen) api_reqs.push(all.slice(i, i+maxlen));
  return api_reqs;
}
function addfcount(elem, metadata) {
  var itds = elem.getElementsByClassName('itd'),
      filecount = " | ";
  if ("undefined" !== typeof metadata.error) {
    console.error('gallery-size: no filecount in ' + metadata.gid);
    filecount += "error";
  } else {
    filecount += "fc: " + String(metadata.filecount);
  }
  itds[0].firstChild.nodeValue += filecount;
}
function send_req(gdata, elems, aurl) {
  var req = new XMLHttpRequest();
  req.onreadystatechange = (function() {
    if (4 === req.readyState) {
      if (200 !== req.status) {
        console.error('gallery-size: cannot send request to ' + aurl);
      } else {
        var apirsp = JSON.parse(req.responseText);
        elems.forEach(function(e,i,arr) { addfcount(e,apirsp.gmetadata[i]); });
      }
    }
  });
  req.open("POST", aurl, true);
  req.send(JSON.stringify(gdata));
}

