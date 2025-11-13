// SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
//
// SPDX-License-Identifier: AGPL-3.0-only

/**
 * Basemap style switcher, inspired by: https://github.com/leoneljdias/maplibre-gl-style-flipper
 *
 */
class StyleControl {
	constructor(styles) {
		this.styles = styles;
	}

	onAdd(map) {
		this.map = map;

		// Create a container for MapLibre
		this.container = document.createElement("div");
		this.container.className = "maplibregl-ctrl maplibregl-ctrl-group style-ctrl-group";

		this.styles.forEach(((style) => {
			this.createStyleButton(style);
		}))

		return this.container;
	}

	createStyleButton(style) {
		const button = document.createElement("button");
		button.type = "button";
		button.className = `map-style ${style.code}`;
		button.title = `Switch to ${style.title}`;

		// Add an image to the button
		const img = document.createElement("img");
		img.src = style.image;
		img.alt = style.title;
		img.style.width = "100%";
		button.appendChild(img);

		// Add a click event listener
		button.addEventListener("click", () => {
			this.switchStyle(style);
		});

		this.container.appendChild(button);
	}


	switchStyle(style) {
		// backup all layers not related to the basemap
		// a style change removes those
		this.saveCustomSourcesAndLayers();

		// explicitly set diff: false. if not set MapLibre tries to optimize the
		// style change and this leads to strange behavior regarding the available
		// sources/layers in SECOND change. it leads to a noticeable delay during the
		// swap though.
		this.map.setStyle(style.url, {diff: false});

		this.map.once("style.load", () => {
			this.restoreCustomSourcesAndLayers();
		});
	}

	saveCustomSourcesAndLayers() {
		this.customSourcesAndLayers = {
			sources: {},
			layers: [],
		};

		// store all dynamically added sources, identified by the ID prefix
		const sources = this.map.getStyle().sources;
		for (const [sourceId, source] of Object.entries(sources)) {
			if (sourceId.startsWith('dh-')) {
				this.customSourcesAndLayers.sources[sourceId] = source;
			}
		}

		// store all dynamically added layers, based on the previous sources
		const layers = this.map.getStyle().layers;
		for (const layer of layers) {
			if (this.customSourcesAndLayers.sources[layer.source]) {
				this.customSourcesAndLayers.layers.push(layer);
			}
		}
	}

	restoreCustomSourcesAndLayers() {
		for (const [sourceId, source] of Object.entries(
			this.customSourcesAndLayers.sources
		)) {
			if (!this.map.getSource(sourceId)) {
				this.map.addSource(sourceId, source);
			}
		}

		for (const layer of this.customSourcesAndLayers.layers) {
			if (!this.map.getLayer(layer.id)) {
				this.map.addLayer(layer);
			}
		}
	}

	onRemove() {
		if (this.container.parentNode) {
			this.container.parentNode.removeChild(this.container);
		}
		this.map = undefined;
	}
}

export default StyleControl;
