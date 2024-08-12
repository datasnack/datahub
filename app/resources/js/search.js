import { autocomplete } from '@algolia/autocomplete-js';

// the setOpen() API does not work in combination with detached work
// see https://github.com/algolia/autocomplete/issues/843
let myautosearch = null;

function createSearch() {

	// returned struct contains the following functions:
	/* const {
		setActiveItemId,
		setQuery,
		setCollections,
		setIsOpen,
		setStatus,
		setContext,
		refresh,
		update,
		destroy,
	} */
	myautosearch = autocomplete({
		container: '#autocomplete',
		detachedMediaQuery: '',
		// performs q= (empty string) search on open if true, i don't want that
		// but true is needed for custom trigger button, so we initalize a
		// search on each action...
		// see: https://github.com/algolia/autocomplete/discussions/1029
		openOnFocus: false,
		initialState: {
			isOpen: true,
		},
		//onStateChange: function(e) {
			// onStateChange catches a lot of events, even multiple
			// per key stroke. Also ther doesn't seem to be a way to
			// detect of detached Mode is active or not? "isOpen" is the
			// autcomplete panel, not the detchedmode modal thing.
		//},
		placeholder: 'Search for Shapes or Data Layers',
		getSources({ query }) {
			return [
				{
				sourceId: 'suggestions',
				getItems() {
					return fetch('/search?q=' + encodeURIComponent(query))
					.then(response => response.json())
					.then(data => {
						return data.results;
					})
					.catch(error => {
						return [];
					});
				},
				getItemUrl({ item }) {
					return item.url;
				},
				templates: {
					item({ item, createElement }) {
						return createElement("div", {
						dangerouslySetInnerHTML: {
							__html: `<a href="${item.url}">${item.label}</a>`
						}
						});
					},
					noResults() {
					return 'No results matching.';
					},
				},
				},
			];
		},
	});
}

var searchNode = document.getElementById('open-search')
if (searchNode) {
	searchNode.addEventListener("click", function() {
		createSearch();
	});
}

document.addEventListener("keydown", ({key}) => {
	if (key === "Escape") {
		if (myautosearch) {
			myautosearch.destroy();
			myautosearch  = null;
		}
	}
});

document.addEventListener('keydown', function(event) {
	if (event.key.toLowerCase() === 'k' && (event.ctrlKey || event.metaKey)) {
		event.preventDefault(); // prevent focus/popup of Search Bar in Firefox
		if (document.querySelectorAll('.aa-DetachedOverlay').length > 0) {
			myautosearch.destroy();
			myautosearch = null;
		} else {
			createSearch();
		}
	}
  });
