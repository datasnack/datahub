import { autocomplete } from "@algolia/autocomplete-js";

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
		container: "#autocomplete",
		detachedMediaQuery: "",
		// performs q= (empty string) search on open if true, i don't want that
		// but true is needed for custom trigger button, so we initalize a
		// search on each action...
		// see: https://github.com/algolia/autocomplete/discussions/1029
		openOnFocus: false,
		initialState: {
			isOpen: true,
		},
		defaultActiveItemId: 0,
		//onStateChange: function(e) {
		// onStateChange catches a lot of events, even multiple
		// per key stroke. Also there doesn't seem to be a way to
		// detect of detached Mode is active or not? "isOpen" is the
		// autocomplete panel, not the detchedmode modal thing.
		//},
		placeholder: "Search for Shapes or Data Layers",
		getSources({ query }) {
			return [
				{
					sourceId: "suggestions",
					getItems() {
						return fetch("/search?q=" + encodeURIComponent(query))
							.then((response) => response.json())
							.then((data) => {
								return data.results;
							})
							.catch((error) => {
								return [];
							});
					},
					getItemUrl({ item }) {
						return item.url;
					},
					templates: {
						item({ item, createElement }) {
							let icon = ""
							if (item.type == "shape") {
								icon = '<svg class="c-icon " xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><path d="m12.596 11.596-3.535 3.536a1.5 1.5 0 0 1-2.122 0l-3.535-3.536a6.5 6.5 0 1 1 9.192-9.193 6.5 6.5 0 0 1 0 9.193Zm-1.06-8.132v-.001a5 5 0 1 0-7.072 7.072L8 14.07l3.536-3.534a5 5 0 0 0 0-7.072ZM8 9a2 2 0 1 1-.001-3.999A2 2 0 0 1 8 9Z"></path></svg>';
							} else if (item.type == "datalayer") {
								icon = '<svg class="c-icon " xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><path d="M7.122.392a1.75 1.75 0 0 1 1.756 0l5.003 2.902c.83.481.83 1.68 0 2.162L8.878 8.358a1.75 1.75 0 0 1-1.756 0L2.119 5.456a1.251 1.251 0 0 1 0-2.162ZM8.125 1.69a.248.248 0 0 0-.25 0l-4.63 2.685 4.63 2.685a.248.248 0 0 0 .25 0l4.63-2.685ZM1.601 7.789a.75.75 0 0 1 1.025-.273l5.249 3.044a.248.248 0 0 0 .25 0l5.249-3.044a.75.75 0 0 1 .752 1.298l-5.248 3.044a1.75 1.75 0 0 1-1.756 0L1.874 8.814A.75.75 0 0 1 1.6 7.789Zm0 3.5a.75.75 0 0 1 1.025-.273l5.249 3.044a.248.248 0 0 0 .25 0l5.249-3.044a.75.75 0 0 1 .752 1.298l-5.248 3.044a1.75 1.75 0 0 1-1.756 0l-5.248-3.044a.75.75 0 0 1-.273-1.025Z"></path></svg>';
							}

							return createElement("div", {
								dangerouslySetInnerHTML: {
									__html: `<a class="text-reset text-decoration-none" href="${item.url}">${icon} <span class="link-primary text-decoration-underline">${item.label}</span> (<code class="text-code">${item.key}</code>)</a>`,
								},
							});
						},
						noResults() {
							return "No results matching.";
						},
					},
				},
			];
		},
	});
}

var searchNode = document.getElementById("open-search");
if (searchNode) {
	searchNode.addEventListener("click", () => {
		createSearch();
	});
}

document.addEventListener("keydown", ({ key }) => {
	if (key === "Escape") {
		if (myautosearch) {
			myautosearch.destroy();
			myautosearch = null;
		}
	}
});

document.addEventListener("keydown", function (event) {
	if (event.key.toLowerCase() === "k" && (event.ctrlKey || event.metaKey)) {
		event.preventDefault(); // prevent focus/popup of Search Bar in Firefox
		if (document.querySelectorAll(".aa-DetachedOverlay").length > 0) {
			myautosearch.destroy();
			myautosearch = null;
		} else {
			createSearch();
		}
	}
});
