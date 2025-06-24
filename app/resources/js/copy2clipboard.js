document.querySelectorAll(".js-clipboard").forEach((button) => {
	button.addEventListener("click", (event) => {
		// in case the button is inside a dropdown, we don't want to close it by clicking on it
		event.stopPropagation();

		const content = button.dataset.clipboardContent;
		const sourceSelector = button.dataset.clipboardSource;
		const url = button.dataset.clipboardUrl;
		let textToCopy = "";

		if (content) {
			copyToClipboard(content, button);
		} else if (sourceSelector) {
			const sourceElement = document.querySelector(sourceSelector);
			if (sourceElement) {
				if (
					sourceElement.tagName === "TEXTAREA" ||
					sourceElement.tagName === "INPUT"
				) {
					textToCopy = sourceElement.value;
				} else {
					textToCopy = sourceElement.textContent;
				}
			}
			copyToClipboard(textToCopy, button);
		} else if (url) {
			showLoadingIcon(button);
			fetch(url)
				.then((response) => {
					if (!response.ok) {
						throw new Error(`HTTP error! status: ${response.status}`);
					}
					return response.text();
				})
				.then((text) => {
					copyToClipboard(text, button);
				})
				.catch((err) => {
					alert(`Error fetching content: ${err}`);
				});
			return; // Exit early since fetch is async
		}
	});
});

function copyToClipboard(text, button) {
	if (text) {
		navigator.clipboard
			.writeText(text)
			.then(() => {
				toggleIcons(button);
			})
			.catch((err) => {
				alert(`Error copying to clipboard: ${err}`);
			});
	} else {
		alert("Nothing to copy!");
	}
}

function showLoadingIcon(button) {
	const copyIcon = button.querySelector(".js-copy");
	const doneIcon = button.querySelector(".js-done");
	const loadingIcon = button.querySelector(".js-loading");

	copyIcon.style.display = "none";
	doneIcon.style.display = "none";
	loadingIcon.style.display = "inline-block";
}

function toggleIcons(button) {
	const copyIcon = button.querySelector(".js-copy");
	const doneIcon = button.querySelector(".js-done");
	const loadingIcon = button.querySelector(".js-loading");

	if (copyIcon && doneIcon) {
		copyIcon.style.display = "none";
		loadingIcon.style.display = "none";
		doneIcon.style.display = "inline-block";

		setTimeout(() => {
			copyIcon.style.display = "inline-block";
			doneIcon.style.display = "none";
		}, 1000);
	}
}
