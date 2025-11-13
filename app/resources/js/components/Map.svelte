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
    import "maplibre-gl/dist/maplibre-gl.css";

    import MapDatalayerControl from "./MapDatalayerControl.svelte";
    import StyleControl from "../maplibre/StyleControl";
    import ScreenshotControl from "../maplibre/ScreenshotControl";

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

    let container; // reference to the DOM node of the component

    let mapContainer;
    let map;

    let datalayer = {
        shape_types: [],
    };

    onMount(async () => {
        // fetch datalayer layout information for charts
        const res = await fetch("/api/datalayers/meta?datalayer_key=" + dl);
        const meta = await res.json();
        datalayer = meta.datalayer;

        query.shape_type = datalayer.shape_types[0].key;
        if (datalayer.temporal_resolution == "year") {
            query.start_date = datalayer.available_years[0];
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
        if (typeof sources === "string") {
            try {
                sources = JSON.parse(sources);
            } catch (e) {
                console.warn("Invalid JSON in sources:", sources);
                sources = [];
            }
        }
    });

    async function loadSource(source) {
        const ctrl = new LegendControl(source, datalayer);
        map.addControl(ctrl, "top-left");
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
            visible: true,
            alpha: 1,
            mode: "min_max",
            cmap: "YlGnBu",
            query: actualQuery,
        };
        sources = [...sources, source];
    }

    async function addVectorData() {
        fetch(`/api/datalayers/vector?datalayer_key=${datalayer.key}`)
            .then((response) => {
                if (!response.ok)
                    throw new Error("Network response was not ok");
                return response.json();
            })
            .then((geojsonData) => {
                const source_id = `dh-${datalayer.key}-vector`;
                map.addSource(source_id, {
                    type: "geojson",
                    data: geojsonData,
                });

                const types = ["Point", "LineString", "Polygon"];
                const layers = {
                    Point: {
                        type: "circle",
                        paint: {
                            "circle-radius": 6,
                            "circle-color": "#ff0000",
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
                    map.addLayer({
                        id: `${source_id}-${t.toLocaleLowerCase()}`,
                        source: source_id,
                        filter: ["==", "$type", t],
                        ...layers[t],
                    });
                });
            });
    }

    // Reactive statement — reruns when 'sources' changes
    let prevLength = 0;

    $: if (Array.isArray(sources) && sources.length > prevLength) {
        const newItems = sources.slice(prevLength);
        console.log(newItems);
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
</script>

<div bind:this={container} class="card bg-light mb-3">
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

    <div class="row">
        <div class="col-12">
            <div style="height: 550px" bind:this={mapContainer}></div>
        </div>
    </div>

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
                        tbd
                    {:else if datalayer.temporal_resolution == "week"}
                        tbd
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
                        tbd
                    {:else if datalayer.temporal_resolution == "week"}
                        tbd
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
                        class="btn btn-outline-primary btn-sm">Add map</button
                    >

                    {#if datalayer.has_vector_data}
                        <button
                            on:click={addVectorData}
                            class="btn btn-outline-primary btn-sm"
                            >Load Vector date</button
                        >
                    {/if}
                </div>
            </div>
        </div>
    </div>
</div>
