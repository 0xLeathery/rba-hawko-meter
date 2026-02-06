/**
 * DataModule - Data fetching with caching and UI state helpers.
 * Uses safe DOM methods (createElement/textContent) throughout.
 */
var DataModule = (function () {
  'use strict';

  var cache = {};

  /**
   * Fetch JSON from a URL with simple caching.
   * @param {string} url - URL to fetch
   * @returns {Promise<any>} Parsed JSON data
   */
  function fetchData(url) {
    if (cache[url]) {
      return Promise.resolve(cache[url]);
    }

    return fetch(url)
      .then(function (response) {
        if (!response.ok) {
          throw new Error('HTTP ' + response.status + ' loading ' + url);
        }
        return response.json();
      })
      .then(function (data) {
        cache[url] = data;
        return data;
      });
  }

  /**
   * Display an error message inside a container using safe DOM methods.
   * @param {string} containerId - Target element ID
   * @param {string} message - Error message text
   */
  function showError(containerId, message) {
    var container = document.getElementById(containerId);
    if (!container) return;

    while (container.firstChild) {
      container.removeChild(container.firstChild);
    }

    var errorDiv = document.createElement('div');
    errorDiv.className = 'bg-red-900/20 border border-red-500/50 text-red-200 px-6 py-4 rounded-lg';

    var titleP = document.createElement('p');
    titleP.className = 'font-semibold mb-1';
    titleP.textContent = 'Error Loading Data';

    var messageP = document.createElement('p');
    messageP.className = 'text-sm text-red-300';
    messageP.textContent = message;

    errorDiv.appendChild(titleP);
    errorDiv.appendChild(messageP);
    container.appendChild(errorDiv);
  }

  /**
   * Display a loading indicator inside a container using safe DOM methods.
   * @param {string} containerId - Target element ID
   * @param {string} message - Loading message text
   */
  function showLoading(containerId, message) {
    var container = document.getElementById(containerId);
    if (!container) return;

    while (container.firstChild) {
      container.removeChild(container.firstChild);
    }

    var loadingDiv = document.createElement('div');
    loadingDiv.className = 'flex items-center justify-center h-full';

    var textEl = document.createElement('p');
    textEl.className = 'text-gray-500 text-sm animate-pulse';
    textEl.textContent = message || 'Loading...';

    loadingDiv.appendChild(textEl);
    container.appendChild(loadingDiv);
  }

  // Clear cache on page unload
  window.addEventListener('beforeunload', function () {
    cache = {};
  });

  return {
    fetch: fetchData,
    showError: showError,
    showLoading: showLoading
  };
})();
