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
    import { MapManager } from "./MapManager";
    import autoComplete from "@tarekraafat/autocomplete.js";

    import {
        DataLayer,
        DataLayerItem,
        MapSource,
        SourceType,
    } from "./DatahubTypes";

    interface AutocompleteOptions {
        scope: string;
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
        explore = false,
        showExploreButton = true,
        sources: initialSources = "[]",
    } = $props();

    let container; // reference to the DOM node of the component

    let mapContainer: HTMLElement;
    let mapManager: MapManager;

    /**
     * Configurable Data Layers
     */
    let datalayers = $state<DataLayerItem[]>([]);

    /**
     * Actual loaded sources. Can be Data Layers, or just shapes, or Vector, ...
     *
     */
    //let sources = $state<MapSource[]>([]);

    let showExplore: boolean = $state(false);
    let showShare: boolean = $state(false);

    let newDataLayerKey = $state("");
    let newShapeKey = $state("");

    let shareEmbedCode = $derived(getEmbedCode(sources));

    onMount(async () => {
        // fetch datalayer layout information for charts
        if (dl) {
            const res = await fetch("/api/datalayers/meta?datalayer_key=" + dl);
            const response = await res.json();
            const datalayer: DataLayer = response.datalayer;

            datalayers.push({
                key: dl,
                datalayer: datalayer,
                query: {
                    shape_type: datalayer.shape_types[0].key,
                    start_date:
                        datalayer.temporal_resolution == "year"
                            ? datalayer.first_time
                            : null,
                    end_date: null,
                    aggregate: null,
                },
            });
        }

        mapManager = new MapManager(mapContainer, {
            layerControlNodeId: layerControlNodeId,
        });

        // normalize values after meta data for datalayer are fetched, and update
        // sources value at latest time, the addSource needs a map object.

        if (typeof initialSources === "string") {
            try {
                const newSources = JSON.parse(initialSources) as MapSource[];
                newSources.forEach((source) => {
                    console.log(source);
                    mapManager.addSource(source);
                });
            } catch (e) {
                console.warn("Invalid JSON in sources:", initialSources);
            }
        }

        /*map.on("load", () => {
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
        });*/

        if (explore) {
            showExplore = true;
        }
    });

    export function getMapManager() {
        return mapManager;
    }

    export function getMapLibre() {
        return mapManager.getMapLibre();
    }

    function handleEndDate(event) {
        if (!query.end_date) {
            query.aggregate = null;
        }
    }

    function getEmbedCode(sources: MapSource[]) {
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

    /**
     * Add Data Layer to the selection UI.
     */
    async function addDataLayer() {
        dl = newDataLayerKey;

        const res = await fetch("/api/datalayers/meta?datalayer_key=" + dl);

        if (!res.ok) {
            alert("Data Layer could not be found.");
            return;
        }

        const response = await res.json();
        const datalayer: DataLayer = response.datalayer;

        datalayers.push({
            key: newDataLayerKey,
            datalayer: datalayer,
            query: {
                shape_type: datalayer.shape_types[0].key,
                start_date: null,
                end_date: null,
                aggregate: null,
            },
        });
    }

    /**
     * Add da new source to map, based on the selected datalayer item.
     *
     * @param item
     */
    function addDataLayerSource(item: DataLayerItem) {
        let actualQuery = JSON.parse(JSON.stringify(item.query)); // deep copy of query

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
        const sourceId = `dh-datalayer-${mapManager.getNextSourceId()}-source`;

        const source: MapSource = {
            id: sourceId,
            type: SourceType.Datalayer,
            visible: true,
            alpha: 1,
            mode: "min_max",
            cmap: "YlGnBu",
            query: actualQuery,
            datalayer: item.datalayer,
        };

        mapManager.loadSource(source);
    }

    function addShapeSource() {
        const sourceId = `dh-datalayer-${mapManager.getNextSourceId()}-source`;

        const source: MapSource = {
            id: sourceId,
            type: SourceType.Shape,
            //name: "DE14 Tübingen"
            query: {
                shape_key: newShapeKey,
            },
        };

        mapManager.loadSource(source);
    }

    function initAutocomplete(
        node: HTMLInputElement,
        options: AutocompleteOptions,
    ) {
        const { scope } = options;

        const instance = new autoComplete({
            selector: () => node, // pass the node directly instead of a selector string
            data: {
                src: async (query: string) => {
                    try {
                        const response = await fetch(
                            `/search?f=${scope}&q=${query}`,
                        );
                        const results = await response.json();
                        // @todo: remove nesting of results
                        console.log(results["results"][0]);
                        return results["results"][0];
                    } catch (error) {
                        return error;
                    }
                },
                keys: ["key"], // key is the value inserted into the input after selecting an item
            },
            searchEngine: function (query, record) {
                // we search/filter on the server, so in this case we don't want to search
                // just show all results.
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

            node.value = selection;
            node.dispatchEvent(new Event("input")); // needed so svelte catches the change for the binding
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
                            class:active={showExplore}
                            onclick={() => (showExplore = !showExplore)}
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

    {#if showShare}
        <div class="card-body">
            <div class="row">
                <div class="col-12">
                    <div class="d-flex align-items-center gap-1">
                        <button class="btn btn-sm btn-outline-primary"
                            >Download image</button
                        >

                        <button class="btn btn-sm btn-outline-primary"
                            >Copy Embed</button
                        >

                        <button class="btn btn-sm btn-outline-primary"
                            >Copy URL</button
                        >
                        <button class="btn btn-sm btn-outline-primary"
                            >Copy Python API</button
                        >
                        <button class="btn btn-sm btn-outline-primary"
                            >Copy R API</button
                        >
                    </div>
                </div>
            </div>
        </div>
    {/if}

    {#if showExplore}
        <div class="card-body">
            <div class="row g-3">
                <div class="col-auto">
                    <div class="input-group">
                        <input
                            use:initAutocomplete={{
                                scope: "datalayers",
                            }}
                            bind:value={newDataLayerKey}
                            type="text"
                            class="form-control form-control-sm"
                        />
                        <button
                            onclick={() => addDataLayer()}
                            class="btn btn-outline-primary btn-sm"
                            >Add Data Layer</button
                        >
                    </div>
                </div>
                <div class="col-auto">
                    <div class="input-group">
                        <select
                            class="form-select form-select-sm"
                            name=""
                            id=""
                        >
                            <option>Country</option>
                            <option>Region</option>
                        </select>
                        <button
                            onclick={() => addDataLayer()}
                            class="btn btn-outline-primary btn-sm"
                            >Add shape type</button
                        >
                    </div>
                </div>
                <div class="col-auto">
                    <div class="input-group">
                        <input
                            use:initAutocomplete={{
                                scope: "shapes",
                            }}
                            bind:value={newShapeKey}
                            type="text"
                            class="form-control form-control-sm"
                        />
                        <button
                            onclick={() => addShapeSource()}
                            class="btn btn-outline-primary btn-sm"
                            >Add shape</button
                        >
                    </div>
                </div>
            </div>
        </div>
    {/if}

    {#each datalayers as item, i (item.key)}
        <div class="card-body">
            {#if explore || datalayers.length > 1}
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
