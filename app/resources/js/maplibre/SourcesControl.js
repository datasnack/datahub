// SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
//
// SPDX-License-Identifier: AGPL-3.0-only

class SourcesControl {

    constructor(options = {}) {
        this._sources = [];
        if (options && options.sources) {
            this._sources = options.sources;
        }
    }

	onAdd(map) {
        this._map = map;

        if (!this._container) this._container = this._map.getContainer();

		this._controlContainer = document.createElement("div");
    	this._controlContainer.className = "maplibregl-ctrl maplibregl-ctrl-group";
    	this._controlContainer.style = "padding: 0.25rem";

        this._setupUI();
        return this._controlContainer;
    }

	onRemove(map) {
		this._controlContainer.remove();
		this._map = null;
    }

    _setupUI() {
		this._sources.forEach((source) => {

			// label
			const label = document.createElement("label");

			// checkbox
			const input = document.createElement("input");
			input.type = "checkbox";
			input.checked = source.visible || true;
			input.style = "margin-top: 2px; position: relative; top: 1px;";

			input.addEventListener("change", (event) => {
				const visibility = event.currentTarget.checked ? "visible" : "none";

				const layers = this._map
					.getStyle()
					.layers.filter((l) => l.source === source.id);

				for (const layer of layers) {
					this._map.setLayoutProperty(layer.id, "visibility", visibility);
				}
			});

			// span
			const span = document.createElement("span");
			span.title = source.name;
			span.innerText = source.name;
			span.style = "padding-left: 1ch";

			label.appendChild(input);
			label.appendChild(span);

			const wrapper = document.createElement("div");
			wrapper.appendChild(label);

			this._controlContainer.appendChild(wrapper);
		});
    }

	addSource(source) {
		this._sources.push(source);
		this._controlContainer.innerHTML = '';
		this._setupUI();
	}
}

export default SourcesControl;
