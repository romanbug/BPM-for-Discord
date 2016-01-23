/**
 * Discord integration for BPM
 * (c) 2015-2016 ByzantineFailure
 *
 * Search panel settings
 **/

module.exports = {
    init: initSearchSubpanel,
    teardown: teardownSearchSubpanel,
    html: require('raw!./html/search.html')
};

var BPM_utils = require('../utils.js');

function initSearchSubpanel(subpanel) {
    function initSearchPrefs(prefs) {
        var limitInput = document.getElementById('bpm-option-search-limit');
        limitInput.value = prefs.searchLimit;
        limitInput.addEventListener('blur', function(e) {
            e.preventDefault();
            
            var newValue = parseInt(limitInput.value);
            if(!newValue || newValue < 0) {
                alert('Search limit must be a positive integer');
                return;
            }

            prefs.searchLimit = newValue;
            BPM_utils.setOption('searchLimit', newValue);
        });
    }
    BPM_utils.retrievePrefs(initSearchPrefs);
}

function teardownSearchSubpanel(subpanel) {
    var limitInput = document.getElementById('bpm-option-search-limit');
    limitInput.removeEventListener('blur'); 
}

