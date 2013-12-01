// ==UserScript==
// @name        mpv-autostart
// @namespace   EH
// @description Automatically starts multi page viewer for certain categories
// @include     http://g.e-hentai.org/
// @include     http://g.e-hentai.org/?page=*
// @include     http://g.e-hentai.org/*Apply+Filter
// @license     GNU GPL v3
// @copyright   Aquamarine Penguin
// @version     1.1
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

var mpv   = ['doujinshi','manga','western','non-h','cosplay'];
var nompv = ['artistcg','gamecg','imageset','asianporn','misc'];
HTMLCollection.prototype.forEach = Array.prototype.forEach;  // dirty hack
(function(classes) {
  var all_elems = classes.map(function(x) {
    return document.getElementsByClassName(x);
  });
  all_elems.forEach(function(elems) { elems.forEach(function(e) {
    atype  = (e.getElementsByClassName('itdc')[0]).firstElementChild;
    type   = atype.firstElementChild.alt;
    if (-1 < mpv.indexOf(type)) {
      anchor      = (e.getElementsByClassName('it5')[0]).firstElementChild;
      ref         = anchor.href.split('/');
      ref[3]      = 'mpv';
      anchor.href = ref.join('/');
    }
  });});
})(['gtr0','gtr1']);

