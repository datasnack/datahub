// Inserts shortcut buttons for fetching DataCite Metadata after:
//     <input type="text" class="js-pidfetch">
'use strict';
{
    const PIDFetcher = {

		pidInputs: [],

        init: function() {
			PIDFetcher.pidInputs = [];
			document.querySelectorAll('.js-pidfetch-wrapper').forEach(el => {
				el.remove();
			});

            for (const inp of document.getElementsByTagName('input')) {
                if (inp.type === 'text' && inp.classList.contains('js-pidfetch')) {
                    PIDFetcher.addButton(inp);
                }
            }
        },

        // Add clock widget to a given field
        addButton: function(inp) {
            const num = PIDFetcher.pidInputs.length;
            PIDFetcher.pidInputs[num] = inp;

            const shortcuts_span = document.createElement('span');
			shortcuts_span.classList.add("js-pidfetch-wrapper");
            inp.parentNode.insertBefore(shortcuts_span, inp.nextSibling);

            const now_link = document.createElement('button');
			now_link.type = "button";
            now_link.textContent = gettext('Fetch DOI data');

			now_link.style.background = 'var(--button-bg)';
			now_link.style.padding = '5px 8px';
			now_link.style.margin = '0 0.25em';
			now_link.style.border = 'none';
			now_link.style.borderRadius = '4px';
			now_link.style.color = 'var(--button-fg)';
			now_link.style.cursor = 'pointer';
			now_link.style.transition = 'background 0.15s';

            now_link.addEventListener('click', function(e) {
                e.preventDefault();
                PIDFetcher.fetchPID(inp);
            });

			const spinnerHTML = '<span class="js-pidfetch-spinner" style="display:none";><svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><style>.spinner_P7sC{transform-origin:center;animation:spinner_svv2 .75s infinite linear}@keyframes spinner_svv2{100%{transform:rotate(360deg)}}</style><path d="M10.14,1.16a11,11,0,0,0-9,8.92A1.59,1.59,0,0,0,2.46,12,1.52,1.52,0,0,0,4.11,10.7a8,8,0,0,1,6.66-6.61A1.42,1.42,0,0,0,12,2.69h0A1.57,1.57,0,0,0,10.14,1.16Z" class="spinner_P7sC"/></svg></span>';

            shortcuts_span.appendChild(now_link);
			shortcuts_span.insertAdjacentHTML('beforeend', spinnerHTML);

        },

		fetchPID: function(inp) {
			const fieldset = inp.closest('fieldset');
			const pid_type = fieldset.querySelector('select[name$="pid_type"]');
			const spinner = fieldset.querySelector('.js-pidfetch-spinner');

			if (pid_type.value != 'DOI') {
				alert(gettext("Only Metadata for DOIs can be fetched."));
				return;
			}

			if (!inp.value) {
				alert(gettext("You need to provide a DOI."));
				return;
			}

			spinner.style.display = "inline";
			fetch('/api/datalayers/datacite/?pid='+encodeURIComponent(inp.value))
				.then(function(response) {
					return response.json();
				})
				.then(function(myJson) {
					console.log(myJson);
					if (myJson.datacite) {
						const datacite = fieldset.querySelector('textarea[name$="datacite"]');
						datacite.value = JSON.stringify(myJson.datacite)


						if (myJson.datacite.titles && myJson.datacite.titles.length > 0) {
							fieldset.querySelector('input[name$="name"]').value = myJson.datacite.titles[0].title;
						} else {
							console.log("DataCite records contains less/more than one title");
						}

						if (myJson.datacite.rightsList) {
							let licenses = [];

							myJson.datacite.rightsList.forEach(element => {
								if (element.rightsIdentifierScheme  && element.rightsIdentifierScheme == "SPDX") {
									licenses.push(element.rightsIdentifier);
								}
							});

							fieldset.querySelector('input[name$="license"]').value = licenses.join(", ");
						} else {
							console.log("DataCite records contains no licenses");
						}

					} else {
						alert(gettext("No metadata found on the DataCite API for the given DOI."));
					}

					spinner.style.display = "none";
				});

        },
    };

    window.addEventListener('load', PIDFetcher.init);
    window.addEventListener('formset:added', PIDFetcher.init);

    window.PIDFetcher = PIDFetcher;
}
