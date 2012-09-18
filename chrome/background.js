/*******************************************************************************
**
** Copyright (C) 2012 Typhos
**
** This Source Code Form is subject to the terms of the Mozilla Public
** License, v. 2.0. If a copy of the MPL was not distributed with this
** file, You can obtain one at http://mozilla.org/MPL/2.0/.
**
*******************************************************************************/

function sync_prefs(prefs) {
    localStorage.prefs = JSON.stringify(prefs);
}

function prefs_updated(prefs) {
}

function dl_file(url, callback) {
    var request = new XMLHttpRequest();
    request.onreadystatechange = function() {
        if(request.readyState == 4) {
            if(request.status == 200) {
                callback(request.responseText);
            } else {
                console.log("BPM: ERROR: Reddit returned HTTP status " + request.status + " for " + url);
            }
        }
    };
    request.open("GET", url, true);
    // Not permitted because Chrome sucks
    //request.setRequestHeader("User-Agent", "BetterPonymotes Client CSS Updater (/u/Typhos)");
    request.send();
}

if(localStorage.prefs === undefined) {
    localStorage.prefs = "{}";
}

var pref_manager = manage_prefs(localStorage, JSON.parse(localStorage.prefs), sync_prefs, prefs_updated, dl_file);

// Content script requests
chrome.extension.onMessage.addListener(function(message, sender, sendResponse) {
    switch(message.method) {
        case "get_prefs":
            sendResponse(pref_manager.get());
            break;

        case "set_prefs":
            pref_manager.write(message.prefs)
            break;

        case "force_update":
            pref_manager.cm.force_update(message.subreddit);
            break;

        case "get_custom_css":
            sendResponse(pref_manager.cm.css_cache);
            break;

        default:
            console.log("BPM: ERROR: Unknown request from content script: '" + message.request + "'");
            break;
    }
});
