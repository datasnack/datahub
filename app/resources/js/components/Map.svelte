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

<script>
    import { mount } from "svelte";
    import { onMount } from "svelte";
    import maplibregl from "maplibre-gl";

    import MapDatalayerControl from "./MapDatalayerControl.svelte";
    import StyleControl from "../maplibre/StyleControl";
    import ScreenshotControl from "../maplibre/ScreenshotControl";
    import FullScreenControl from "../maplibre/FullScreenControl";
    import SourcesControl from "../maplibre/SourcesControl";

    class LegendControl {
        constructor(source, datalayer) {
            this.source = source;
            this.datalayer = datalayer;
        }

        onAdd(map) {
            this.map = map;

            // Create a container for MapLibre
            this.container = document.createElement("div");
            this.container.className =
                "maplibregl-ctrl maplibregl-ctrl-group py-1 px-2";

            let ui = mount(MapDatalayerControl, {
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

        onRemove() {
            if (this.container.parentNode) {
                this.container.parentNode.removeChild(this.container);
            }
            this.map = undefined;
        }
    }

    export let title = "Spatial";
    export let dl;
    export let query = {
        shape_type: null,
        start_date: null,
        end_date: null,
        aggregate: null,
    };
    export let sources = [];
    export let show_remove = false;

    export let height = "500px";

    let container; // reference to the DOM node of the component

    let mapContainer;
    let map;
    let mapSourceControl;

    let datalayer = null;

    onMount(async () => {
        // fetch datalayer layout information for charts
        if (dl) {
            const res = await fetch("/api/datalayers/meta?datalayer_key=" + dl);
            const meta = await res.json();
            datalayer = meta.datalayer;

            query.shape_type = datalayer.shape_types[0].key;
            if (datalayer.temporal_resolution == "year") {
                query.start_date = datalayer.available_years[0];
            }
        }

        const mapStyles = [
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
        // sources value at latest time, ther addSource needs a map object.
        map.on("load", () => {
            if (typeof sources === "string") {
                try {
                    sources = JSON.parse(sources);
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

    export async function loadSource(source) {
        if (source.type == "datalayer") {
            const ctrl = new LegendControl(source, datalayer);
            map.addControl(ctrl, "top-left");
        } else if (source.type == "shape") {
            addShape(source);
        } else {
            console.log("Unknown source type:", source);
        }
    }

    export async function addSource(userSource) {
        if (map.isStyleLoaded()) {
            const defaults = {
                type: "datalayer",
                visible: true,
                alpha: 1,
                mode: "min_max",
                cmap: "YlGnBu",
            };
            const source = { ...defaults, ...userSource };
            sources = [...sources, source];
        } else {
            map.on("style.load", () => {
                const defaults = {
                    type: "datalayer",
                    visible: true,
                    alpha: 1,
                    mode: "min_max",
                    cmap: "YlGnBu",
                };
                const source = { ...defaults, ...userSource };
                sources = [...sources, source];
            });
        }
    }

    async function addLayer(traceOverwrites = {}) {
        let actualQuery = JSON.parse(JSON.stringify(query));

        // check query
        if (!actualQuery.end_date) {
            actualQuery.end_date = actualQuery.start_date;
        }

        if (!actualQuery.datalayer_key) {
            actualQuery.datalayer_key = datalayer.key;
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

        const source = {
            id: sourceId,
            type: "datalayer",
            visible: true,
            alpha: 1,
            mode: "min_max",
            cmap: "YlGnBu",
            query: actualQuery,
        };
        sources = [...sources, source];
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

    // Reactive statement — reruns when 'sources' changes
    let prevLength = 0;

    $: if (Array.isArray(sources) && sources.length > prevLength) {
        const newItems = sources.slice(prevLength);
        newItems.forEach((source) => loadSource(source));
        prevLength = sources.length;
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

    function getEmbedCode() {
        return `<dh-map dl='${dl.key}' sources='${JSON.stringify(sources)}'></dh-map>`;
    }

    function hasTop() {
        if (datalayer || title) {
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
</script>

<div bind:this={container} class="card bg-light mb-3">
    {#if title}
        <div class="card-header">
            <div class="d-flex align-items-center justify-content-between">
                <span>{title}</span>
                <div class="d-flex align-items-center">
                    <!--
                <button class="btn p-0" on:click={togglePopup}>Embed</button>
                -->
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

    {#if datalayer}
        <div class="card-body">
            <div class="row">
                <div class="col-12 col-sm-2">
                    <label for="aggregate_function" class="form-label small"
                        >Shape
                    </label>

                    <div class="input-group input-group-sm">
                        <select
                            class="form-select form-select-sm"
                            bind:value={query.shape_type}
                        >
                            {#each datalayer.shape_types as shape_type}
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

                        {#if datalayer.temporal_resolution == "year"}
                            <select
                                class="form-select form-select-sm"
                                bind:value={query.start_date}
                            >
                                {#each datalayer.available_years as year}
                                    <option value={year}>{year}</option>
                                {/each}
                            </select>
                        {:else if datalayer.temporal_resolution == "month"}
                            <input
                                class="form-control form-control-sm"
                                bind:value={query.start_date}
                                placeholder="yyyy-mm"
                            />
                        {:else if datalayer.temporal_resolution == "week"}
                            <input
                                class="form-control form-control-sm"
                                bind:value={query.start_date}
                                placeholder="yyyy-Www"
                            />
                        {:else if datalayer.temporal_resolution == "date"}
                            <input
                                type="date"
                                class="form-control form-control-sm"
                                bind:value={query.start_date}
                                min={datalayer.first_time}
                                max={datalayer.last_time}
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
                        {#if datalayer.temporal_resolution == "year"}
                            <select
                                class="form-select form-select-sm"
                                on:change={handleEndDate}
                                bind:value={query.end_date}
                            >
                                <option value={null}>None</option>
                                {#each datalayer.available_years as year}
                                    <option value={year}>{year}</option>
                                {/each}
                            </select>
                        {:else if datalayer.temporal_resolution == "month"}
                            <input
                                type="text"
                                class="form-control form-control-sm"
                                placeholder="yyyy-mm"
                                bind:value={query.end_date}
                                on:change={handleEndDate}
                            />
                        {:else if datalayer.temporal_resolution == "week"}
                            <input
                                type="text"
                                class="form-control form-control-sm"
                                placeholder="yyyy-Www"
                                bind:value={query.end_date}
                                on:change={handleEndDate}
                            />
                        {:else if datalayer.temporal_resolution == "date"}
                            <input
                                type="date"
                                class="form-control form-control-sm"
                                bind:value={query.end_date}
                                on:change={handleEndDate}
                                min={datalayer.first_time}
                                max={datalayer.last_time}
                            />
                        {/if}

                        <select
                            bind:value={query.aggregate}
                            disabled={!query.end_date}
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
                            on:click={addLayer}
                            class="btn btn-outline-primary btn-sm"
                            >Add map</button
                        >

                        {#if datalayer.has_vector_data}
                            <button
                                on:click={() => addVectorData(datalayer.key)}
                                class="btn btn-outline-primary btn-sm"
                                >Load Vector date</button
                            >
                        {/if}
                    </div>
                </div>
            </div>
        </div>
    {/if}

    <div
        style="{getCanvasRadiusStyle()} height: {height}"
        bind:this={mapContainer}
    ></div>
</div>
