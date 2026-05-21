<!--
SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>

SPDX-License-Identifier: AGPL-3.0-only
-->
<svelte:options
    customElement={{
        tag: "dh-map",
        shadow: "none",
    }}
/>

<script lang="ts">
    import { mount } from "svelte";
    import { onMount } from "svelte";
    import maplibregl from "maplibre-gl";
    import type { Map } from "maplibre-gl";
    import { Protocol } from "pmtiles";

    import MapDatalayerControl from "./MapDatalayerControl.svelte";
    import StyleControl from "../maplibre/StyleControl";
    import ScreenshotControl from "../maplibre/ScreenshotControl";
    import FullScreenControl from "../maplibre/FullScreenControl";
    import SourcesControl from "../maplibre/SourcesControl";

    import autoComplete from "@tarekraafat/autocomplete.js";

    class LegendControl {
        constructor(source, datalayer) {
            this.source = source;
            this.datalayer = datalayer;
        }

        onAdd(map: Map) {
            this.map = map;

            // Create a container for MapLibre
            this.container = document.createElement("div");
            this.container.className =
                "maplibregl-ctrl maplibregl-ctrl-group py-1 px-2";

            this.ctrl = mount(MapDatalayerControl, {
                target: this.container,
                props: {
                    map: map,
                    source: this.source,
                    datalayer: this.datalayer,
                    control: this,
                },
            });

            return this.container;
        }

        setData(value_map) {
            this.ctrl.setData(value_map);
        }

        onRemove() {
            if (this.container.parentNode) {
                this.container.parentNode.removeChild(this.container);
            }
            this.map = undefined;
        }
    }

    let {
        title = "Spatial",
        dl = null,
        query = {
            shape_type: null,
            start_date: null,
            end_date: null,
            aggregate: null,
        },
        show_remove = false,
        layerControlNodeId = null,
        height = "500px",
        showExplore = false,
        sources: initialSources = "[]",
    } = $props();

    let container; // reference to the DOM node of the component

    let mapContainer;
    let map: Map;
    let mapSourceControl;

    enum SourceType {
        Datalayer = "datalayer",
        Shape = "shape",
    }

    interface Source {
        id: string;
        type: SourceType;
        visible: boolean;
        alpha: number;
        mode: "min_max";
        cmap: string;
        query: object;
        datalayer: object;
    }

    /**
     * Configurable Data Layers
     */
    let datalayers = $state([]);

    /**
     * Actual loaded sources. Can be Data Layers, or just shapes, or Vector, ...
     *
     */
    let sources = $state<Source[]>([]);

    let showExploreButton = showExplore !== false && showExplore !== "false";
    let localExplore = $state(showExplore !== false && showExplore !== "false");
    let isExplore = $derived(
        showExplore !== false && showExplore !== "false" && localExplore,
    );

    let showShare: boolean = $state(false);

    let shareEmbedCode = $derived(getEmbedCode(sources));

    onMount(async () => {
        // fetch datalayer layout information for charts
        if (dl) {
            const res = await fetch("/api/datalayers/meta?datalayer_key=" + dl);
            const response = await res.json();

            datalayers.push({
                key: dl,
                datalayer: response.datalayer,
                query: {},
            });
        }

        const protocol = new Protocol();
        maplibregl.addProtocol("pmtiles", protocol.tile);

        const mapStyles = [
            /*{
                title: "Local",
                code: "datahub",
                url: "http://localhost:8000/static/map/style.json",
                image: "/static/map/openfreemap-liberty.png",
            },*/
            {
                title: "OpenStreetMap",
                code: "openfreemap-liberty",
                url: "https://tiles.openfreemap.org/styles/liberty",
                image: "/static/map/openfreemap-liberty.png",
            },
            {
                title: "Satellite",
                code: "eox-cloudless",
                url: "/static/map/eox_cloudless.json",
                image: "/static/map/eox-cloudless.png",
            },
        ];

        map = new maplibregl.Map({
            container: mapContainer,
            style: mapStyles[0].url,
            center: [DATAHUB.CENTER_X, DATAHUB.CENTER_Y], // [lng, lat]
            zoom: DATAHUB.CENTER_ZOOM,
        });

        map.on("error", (e) => {
            console.error("MapLibre error:", e.error);
        });

        map.addControl(new FullScreenControl(), "top-right");

        // Add zoom and rotation controls to the map.
        map.addControl(
            new maplibregl.NavigationControl({
                visualizePitch: true,
                visualizeRoll: true,
                showZoom: true,
                showCompass: true,
            }),
        );

        // Scale
        map.addControl(
            new maplibregl.ScaleControl({
                maxWidth: 80,
                unit: "metric",
            }),
        );

        map.addControl(new ScreenshotControl(), "top-right");

        const styleControl = new StyleControl(mapStyles);
        map.addControl(styleControl, "bottom-right");

        // normalize values after meta data for datalayer are fetched, and update
        // sources value at latest time, the addSource needs a map object.
        map.on("load", () => {
            if (typeof initialSources === "string") {
                try {
                    const newSources = JSON.parse(initialSources) as Source[];

                    newSources.forEach((source) => {
                        console.log(source);
                        loadSource(source);
                    });
                } catch (e) {
                    console.warn("Invalid JSON in sources:", sources);
                    sources = [];
                }
            }
        });
    });

    export function getMap() {
        return map;
    }

    export function getMapLibre() {
        return maplibregl;
    }

    export async function loadSource(source: Source) {
        if (source.type == SourceType.Datalayer) {
            const ctrl = new LegendControl(source, source.datalayer);

            if (layerControlNodeId) {
                // if a custom DOM node id is given to position the layer control
                // components, we need to manually add the control to the map
                // and then insert the html node to the target.
                ctrl.onAdd(map);
                document
                    .getElementById(layerControlNodeId)
                    .appendChild(ctrl.container);
            } else {
                map.addControl(ctrl, "top-left");
            }

            return ctrl;
        } else if (source.type == SourceType.Shape) {
            addShape(source);
        } else {
            console.log("Unknown source type:", source);
        }
    }

    export async function addSource(userSource: Source) {
        console.log("wtd");
        console.log(userSource);

        const defaults: Source = {
            type: SourceType.Datalayer,
            visible: true,
            alpha: 1,
            mode: "min_max",
            cmap: "YlGnBu",
        };
        const source = { ...defaults, ...userSource };

        // when the map is already fully loaded
        // isStyleLoaded() seems also to be false during a source being added
        // in this case the style.load part get's never fired again.
        if (map.isStyleLoaded()) {
            sources.push(source);
            loadSource(source);
        } else {
            map.on("style.load", () => {
                sources.push(source);
                loadSource(source);
            });
        }
    }

    async function addDataLayerSource(item) {
        let actualQuery = JSON.parse(JSON.stringify(item.query));

        // check query
        if (!actualQuery.end_date) {
            actualQuery.end_date = actualQuery.start_date;
        }

        if (!actualQuery.datalayer_key) {
            actualQuery.datalayer_key = item.datalayer.key;
        }

        if (!actualQuery.hasOwnProperty("format")) {
            actualQuery["format"] = "geojson";
        }

        if (!actualQuery.start_date) {
            alert("Please select a date first.");
            return;
        }

        // store query
        const sourceId = `dh-datalayer-${sources.length}-source`;

        const source: Source = {
            id: sourceId,
            type: SourceType.Datalayer,
            visible: true,
            alpha: 1,
            mode: "min_max",
            cmap: "YlGnBu",
            query: actualQuery,
            datalayer: item.datalayer,
        };

        sources.push(source);
        loadSource(source);
    }

    export async function addShapeBBox(source) {
        let query = source.query;

        if (!mapSourceControl) {
            mapSourceControl = new SourcesControl();
            map.addControl(mapSourceControl, "top-left");
        }

        const queryString = new URLSearchParams(query).toString();
        const sourceId = `dh-shape_id-${query.shape_id}-bbox`;

        if (map.getSource(sourceId)) {
            return;
        }

        fetch(`/api/shapes/bbox?${queryString}`)
            .then((response) => {
                if (!response.ok)
                    throw new Error("Network response was not ok");
                return response.json();
            })
            .then((geojsonData) => {
                geojsonData.features.forEach((feature) => {
                    feature.properties.color = "#5385f8";
                });

                mapSourceControl.addSource({
                    id: sourceId,
                    name: source.name,
                });

                // Add as a source when the map is ready
                map.addSource(sourceId, {
                    type: "geojson",
                    data: geojsonData,
                });

                // Add outline
                map.addLayer({
                    id: `${sourceId}-outline`,
                    type: "line",
                    source: sourceId,
                    paint: {
                        "line-color": ["get", "color"],
                        "line-dasharray": [2, 2],
                        "line-width": [
                            "interpolate",
                            ["linear"],
                            ["zoom"],
                            3,
                            2, // very zoomed-out → thin
                            6,
                            2.5,
                            8,
                            3,
                            10,
                            4,
                        ],
                        "line-opacity": 1,
                    },
                });

                // add markers
                const markerLayerId = `${sourceId}-markers`;
                map.addLayer({
                    id: markerLayerId,
                    type: "circle",
                    source: sourceId,
                    filter: ["==", "$type", "Point"],
                    paint: {
                        "circle-radius": [
                            "interpolate",
                            ["linear"],
                            ["zoom"],
                            0,
                            0.5,
                            3,
                            3.5,
                            6,
                            6,
                        ],

                        "circle-color": ["get", "color"],
                        "circle-stroke-width": [
                            "interpolate",
                            ["linear"],
                            ["zoom"],
                            0,
                            0.5,
                            3,
                            1,
                            6,
                            2,
                        ],
                        "circle-stroke-color": "#ffffff",
                    },
                });

                map.on("click", markerLayerId, (e) => {
                    const coordinates = e.lngLat;
                    const feature = e.features[0];

                    new maplibregl.Popup()
                        .setLngLat(coordinates)
                        .setHTML(getPopupContent(feature))
                        .addTo(map);

                    e.originalEvent.stopPropagation();
                });

                // Change cursor on hover
                map.on("mouseenter", markerLayerId, () => {
                    map.getCanvas().style.cursor = "pointer";
                });

                map.on("mouseleave", markerLayerId, () => {
                    map.getCanvas().style.cursor = "";
                });
            })
            .catch((error) => {
                console.error("Error loading GeoJSON:", error);
                deleteLayer();
            });
    }

    function _sourceIdFromQuery(query) {
        return (
            "dh-" +
            Object.entries(query)
                .map(([key, value]) => `${key}-${value}`)
                .join("_")
        );
    }

    export async function addShape(source) {
        let query = source.query;

        if (!mapSourceControl) {
            mapSourceControl = new SourcesControl();
            map.addControl(mapSourceControl, "top-left");
        }

        const queryString = new URLSearchParams(query).toString();
        const sourceId = _sourceIdFromQuery(query);

        if (map.getSource(sourceId)) {
            return;
        }

        fetch(`/api/shapes/geometry?${queryString}`)
            .then((response) => {
                if (!response.ok)
                    throw new Error("Network response was not ok");
                return response.json();
            })
            .then((geojsonData) => {
                geojsonData.features.forEach((feature) => {
                    feature.properties.alpha = 0.2;
                    feature.properties.color = "#5385f8";
                });

                mapSourceControl.addSource({
                    id: sourceId,
                    name: source.name,
                });

                // Add as a source when the map is ready
                map.addSource(sourceId, {
                    type: "geojson",
                    data: geojsonData,
                });

                const layerId = `${sourceId}-fill`;
                map.addLayer({
                    id: layerId,
                    type: "fill",
                    source: sourceId,
                    paint: {
                        "fill-color": ["get", "color"],
                        "fill-opacity": ["get", "alpha"],
                    },
                });

                // Add outline
                map.addLayer({
                    id: `${sourceId}-outline`,
                    type: "line",
                    source: sourceId,
                    paint: {
                        "line-color": ["get", "color"],
                        "line-width": [
                            "interpolate",
                            ["linear"],
                            ["zoom"],
                            3,
                            1, // very zoomed-out → thin
                            6,
                            1.5,
                            8,
                            2,
                            10,
                            3,
                        ],
                        "line-opacity": 1,
                    },
                });

                // Add click handler for popup
                map.on("click", layerId, (e) => {
                    const coordinates = e.lngLat;
                    const feature = e.features[0];

                    new maplibregl.Popup()
                        .setLngLat(coordinates)
                        .setHTML(getPopupContent(feature))
                        .addTo(map);
                });

                // Change cursor on hover
                map.on("mouseenter", layerId, () => {
                    map.getCanvas().style.cursor = "pointer";
                });

                map.on("mouseleave", layerId, () => {
                    map.getCanvas().style.cursor = "";
                });

                if (source.fitBounds) {
                    fitToSourceBounds(sourceId);
                }
            })
            .catch((error) => {
                console.error("Error loading GeoJSON:", error);
                deleteLayer();
            });
    }

    async function fitToSourceBounds(sourceId) {
        const bounds = await map.getSource(sourceId).getBounds();
        map.fitBounds(bounds, {
            linear: true,
            padding: 42,
        });
    }

    export async function addVectorData(datalayer_key) {
        const sourceId = `dh-${datalayer_key}-vector`;
        if (map.getSource(sourceId)) {
            return;
        }

        if (!mapSourceControl) {
            mapSourceControl = new SourcesControl();
            map.addControl(mapSourceControl, "top-left");
        }

        fetch(`/api/datalayers/vector?datalayer_key=${datalayer_key}`)
            .then((response) => {
                if (!response.ok)
                    throw new Error("Network response was not ok");
                return response.json();
            })
            .then((geojsonData) => {
                geojsonData.features.forEach((feature) => {
                    const values = feature.properties;
                    feature.properties = {
                        color: "#5385f8",
                        values: values,
                    };
                });

                map.addSource(sourceId, {
                    type: "geojson",
                    data: geojsonData,
                });

                mapSourceControl.addSource({
                    id: sourceId,
                    name: "Vector data",
                });

                const types = ["Point", "LineString", "Polygon"];
                const layers = {
                    Point: {
                        type: "circle",
                        paint: {
                            "circle-radius": [
                                "interpolate",
                                ["linear"],
                                ["zoom"],
                                0,
                                0.5,
                                3,
                                3.5,
                                6,
                                6,
                            ],

                            "circle-color": ["get", "color"],
                            "circle-stroke-width": [
                                "interpolate",
                                ["linear"],
                                ["zoom"],
                                0,
                                0.5,
                                3,
                                1,
                                6,
                                2,
                            ],
                            "circle-stroke-color": "#ffffff",
                        },
                    },
                    LineString: {
                        type: "line",
                        paint: { "line-color": "#0000ff", "line-width": 3 },
                    },
                    Polygon: {
                        type: "fill",
                        paint: { "fill-color": "#00ff00", "fill-opacity": 0.4 },
                    },
                };

                types.forEach((t) => {
                    const layerId = `${sourceId}-${t.toLocaleLowerCase()}`;
                    map.addLayer({
                        id: layerId,
                        source: sourceId,
                        filter: ["==", "$type", t],
                        ...layers[t],
                    });

                    map.on("click", layerId, (e) => {
                        const coordinates = e.lngLat;
                        const feature = e.features[0];

                        new maplibregl.Popup()
                            .setLngLat(coordinates)
                            .setHTML(getPopupContent(feature))
                            .addTo(map);
                    });

                    // Change cursor on hover
                    map.on("mouseenter", layerId, () => {
                        map.getCanvas().style.cursor = "pointer";
                    });

                    map.on("mouseleave", layerId, () => {
                        map.getCanvas().style.cursor = "";
                    });
                });
            });
    }

    function handleEndDate(event) {
        if (!query.end_date) {
            query.aggregate = null;
        }
    }

    let showPopup = false;

    function togglePopup() {
        showPopup = !showPopup;
    }

    function getEmbedCode(sources: Source[]) {
        let embedSources = [];

        sources.forEach((source) => {
            embedSources.push({
                type: source.type,
                query: source.query,
                mode: source.mode,
                cmap: source.cmap,
            });
        });

        return `<dh-map sources='${JSON.stringify(embedSources)}'></dh-map>`;
    }

    function hasTop() {
        if (title) {
            return true;
        }

        return false;
    }

    function getCanvasRadiusStyle() {
        if (hasTop()) {
            return "border-bottom-left-radius: 0.25rem; border-bottom-right-radius: 0.25rem;";
        }
        return "border-radius: 0.25rem;";
    }

    // Function to get popup content for a feature
    function getPopupContent(feature, show_all_as_table = false) {
        const props = feature.properties;
        let content = '<div class="">';

        // Customize based on your GeoJSON properties
        if (props.shape_name) {
            content += `<h5 class="mb-0">${props.shape_name}</h5>`;
        }

        if (props.type_key) {
            content += `<div class="small text-muted mb-1">${props.type_key}</div>`;
        }

        if (props.value) {
            content += `<div class="">Value: ${props.value}</div>`;
        }

        if (props.url) {
            content += `<a href="${props.url}" class="">Details</a>`;
        }

        // Add other properties
        let values = {};
        if (show_all_as_table) {
            values = props;
        } else {
            if (props.values) {
                // MapLibre doesn't parse nested properties
                // https://github.com/maplibre/maplibre-gl-js/issues/1325
                if (typeof props.values === "string") {
                    try {
                        values = JSON.parse(props.values);
                    } catch (e) {
                        console.warn(
                            "Invalid JSON feature properties.values:",
                            props.values,
                        );
                        values = {};
                    }
                } else {
                    values = props.values;
                }
            }
        }

        if (values) {
            var table = "";
            Object.keys(values).forEach(function (key) {
                if (key == "name") {
                    return;
                }
                const value = values[key];

                // ignore empty values (not all properties are set on each feature)
                // this reduces the visual space needed for the popup!
                if (value == null) {
                    return;
                }
                table += `<tr><th><code>${key}</code></th><td>${value}</td>`;
            });
            content += `<div class="overflow-y-scroll" style="max-height:200px"><table class="table table-sm"><tbody>${table}</tbody></table></div>`;

            content += "</div>";
        }
        return content;
    }

    let newDataLayerKey = $state("meteo_tmin");

    async function addDataLayer() {
        dl = newDataLayerKey;

        const res = await fetch("/api/datalayers/meta?datalayer_key=" + dl);

        if (!res.ok) {
            alert("Data Layer could not be found.");
            return;
        }

        const response = await res.json();

        /*
        query.shape_type = datalayer.shape_types[0].key;
        if (datalayer.temporal_resolution == "year") {
            query.start_date = datalayer.available_years[0];
        }*/

        console.log(newDataLayerKey);

        datalayers.push({
            key: newDataLayerKey,
            datalayer: response.datalayer,
            query: {},
        });
    }

    function initAutocomplete(node) {
        const instance = new autoComplete({
            selector: () => node, // pass the node directly instead of a selector string
            data: {
                src: async (query: string) => {
                    try {
                        const response = await fetch(
                            `/search?f=datalayers&q=${query}`,
                        );
                        const results = await response.json();
                        // @todo: remove nesting of results
                        console.log(results["results"][0]);
                        return results["results"][0];
                    } catch (error) {
                        return error;
                    }
                },
                keys: ["key"],
            },
            searchEngine: function (query, record) {
                return 1;
            },
            debounce: 300,
            resultsList: {
                class: "dropdown-menu",
                maxResults: 20,
            },
            resultItem: {
                element: (item, data) => {
                    item.innerHTML = `<span class="dropdown-item">
            <span class="d-block">${data.value.label}</span>
            <small class="text-muted">
                ${data.value.key}
            </small></span>
        `;
                },
            },
            events: {
                input: {
                    // open dropdown on focus and fetch items from API
                    focus() {
                        const inputValue = instance.input.value;

                        if (inputValue.length) instance.start();
                    },
                },
            },
        });

        node.addEventListener("selection", function (event) {
            const feedback = event.detail;

            // Access the matched key's value from the original object
            const selection = feedback.selection.value[feedback.selection.key];
            console.log(selection);
            newDataLayerKey = selection;
        });

        return {
            destroy() {
                instance.unInit();
            },
        };
    }
</script>

<div bind:this={container} class="card bg-light mb-3">
    {#if title}
        <div class="card-header">
            <div class="d-flex align-items-center justify-content-between">
                <span>{title}</span>
                <div class="d-flex align-items-center gap-1">
                    <!--
                <button class="btn p-0" on:click={togglePopup}>Embed</button>
                -->
                    {#if showExploreButton}
                        <button
                            class="btn btn-outline-secondary btn-xs"
                            class:active={isExplore}
                            onclick={() => (localExplore = !localExplore)}
                            >Explore</button
                        >
                    {/if}
                    <button
                        class="btn btn-outline-secondary btn-xs"
                        class:active={showShare}
                        onclick={() => (showShare = !showShare)}>Share</button
                    >
                </div>
            </div>
        </div>
    {/if}

    <!--
    {#if showPopup}
        <div class="popup-backdrop" on:click={togglePopup}>
            <div class="popup" on:click|stopPropagation>
                <h2>Share</h2>
                <pre><code>{getEmbedCode()}</code></pre>
                <button on:click={togglePopup}>Close</button>
            </div>
        </div>
    {/if}
    -->

    {#if showShare}
        <div class="card-body">
            <div class="row">
                <div class="col-12">Share</div>
                <div class="col-12">
                    <textarea value={shareEmbedCode}></textarea>
                </div>
            </div>
        </div>
    {/if}

    {#if isExplore}
        <div class="card-body">
            <div class="row g-3">
                <div class="col-auto">
                    <input
                        use:initAutocomplete
                        bind:value={newDataLayerKey}
                        type="text"
                        class="form-control form-control-sm"
                    />
                </div>
                <div class="col-auto">
                    <button
                        onclick={() => addDataLayer()}
                        class="btn btn-outline-primary btn-sm"
                        >Add Data Layer</button
                    >
                </div>
            </div>
        </div>
    {/if}

    {#each datalayers as item, i (item.key)}
        <div class="card-body">
            {#if isExplore || datalayers.length > 1}
                <div class="row">
                    <div class="col-12">
                        {item.datalayer.name}
                        (<code>{item.key}</code>)

                        <button
                            class="btn btn-outline-secondary btn-xs"
                            onclick={() => {
                                datalayers.splice(i, 1);
                            }}>Remove</button
                        >
                    </div>
                </div>
            {/if}
            <div class="row">
                <div class="col-12 col-sm-2">
                    <label for="aggregate_function" class="form-label small"
                        >Shape
                    </label>

                    <div class="input-group input-group-sm">
                        <select
                            class="form-select form-select-sm"
                            bind:value={item.query.shape_type}
                        >
                            {#each item.datalayer.shape_types as shape_type}
                                <option value={shape_type.key}
                                    >{shape_type.name}</option
                                >
                            {/each}
                        </select>
                    </div>
                </div>
                <div class="col-12 col-sm-3">
                    <label for="aggregate_function" class="form-label small"
                        >Temporal
                    </label>

                    <div class="input-group input-group-sm">
                        <!--
                    <button class="btn btn-outline-secondary btn-sm">
                        &lt;
                    </button>
                     -->

                        {#if item.datalayer.temporal_resolution == "year"}
                            <select
                                class="form-select form-select-sm"
                                bind:value={item.query.start_date}
                            >
                                {#each item.datalayer.available_years as year}
                                    <option value={year}>{year}</option>
                                {/each}
                            </select>
                        {:else if item.datalayer.temporal_resolution == "month"}
                            <input
                                class="form-control form-control-sm"
                                bind:value={item.query.start_date}
                                placeholder="yyyy-mm"
                            />
                        {:else if item.datalayer.temporal_resolution == "week"}
                            <input
                                class="form-control form-control-sm"
                                bind:value={item.query.start_date}
                                placeholder="yyyy-Www"
                            />
                        {:else if item.datalayer.temporal_resolution == "date"}
                            <input
                                type="date"
                                class="form-control form-control-sm"
                                bind:value={item.query.start_date}
                                min={item.datalayer.first_time}
                                max={item.datalayer.last_time}
                            />
                        {/if}

                        <!--
                    <button disabled class="btn btn-outline-secondary btn-sm">
                        &gt;
                    </button>
                    -->
                    </div>
                </div>

                <div class="col-12 col-sm-3">
                    <label for="aggregate_function" class="form-label small"
                        ><i>Optional</i>: range with aggregation
                    </label>

                    <div class="input-group input-group-sm">
                        {#if item.datalayer.temporal_resolution == "year"}
                            <select
                                class="form-select form-select-sm"
                                onchange={handleEndDate}
                                bind:value={item.query.end_date}
                            >
                                <option value={null}>None</option>
                                {#each item.datalayer.available_years as year}
                                    <option value={year}>{year}</option>
                                {/each}
                            </select>
                        {:else if item.datalayer.temporal_resolution == "month"}
                            <input
                                type="text"
                                class="form-control form-control-sm"
                                placeholder="yyyy-mm"
                                bind:value={item.query.end_date}
                                onchange={handleEndDate}
                            />
                        {:else if item.datalayer.temporal_resolution == "week"}
                            <input
                                type="text"
                                class="form-control form-control-sm"
                                placeholder="yyyy-Www"
                                bind:value={item.query.end_date}
                                onchange={handleEndDate}
                            />
                        {:else if item.datalayer.temporal_resolution == "date"}
                            <input
                                type="date"
                                class="form-control form-control-sm"
                                bind:value={item.query.end_date}
                                onchange={handleEndDate}
                                min={item.datalayer.first_time}
                                max={item.datalayer.last_time}
                            />
                        {/if}

                        <select
                            bind:value={item.query.aggregate}
                            disabled={!item.query.end_date}
                            id="aggregate_function"
                            class="form-select form-select-sm"
                        >
                            <option value={null}>--</option>
                            <option value="sum">sum</option>
                            <option value="min">min</option>
                            <option value="max">max</option>
                            <option value="mean">mean</option>
                            <option value="median">median</option>
                            <option value="std">std</option>
                            <option value="count">count</option>
                        </select>
                    </div>
                </div>

                <div class="col-12 col-sm-4">
                    <label for="aggregate_function" class="form-label small"
                        >&nbsp;
                    </label>

                    <div class="">
                        <button
                            onclick={() => {
                                addDataLayerSource(item);
                            }}
                            class="btn btn-outline-primary btn-sm"
                            >Add map</button
                        >

                        {#if item.datalayer.has_vector_data}
                            <button
                                onclick={() =>
                                    addVectorData(item.datalayer.key)}
                                class="btn btn-outline-primary btn-sm"
                                >Load vector data</button
                            >
                        {/if}
                    </div>
                </div>
            </div>
        </div>
    {/each}

    <div
        style="{getCanvasRadiusStyle()} height: {height}"
        bind:this={mapContainer}
    ></div>
</div>
