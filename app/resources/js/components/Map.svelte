<!--
SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>

SPDX-License-Identifier: AGPL-3.0-only
-->
<svelte:options
    customElement={{
        tag: "dh-map",
        shadow: "none",
        props: {
            // type: Boolean converts only presence -> true, absence -> false
            // we can't do explore="false", to set it to false we need to remove it.
            explore: { type: "Boolean" },
            openExplore: { type: "Boolean" },
            sidebar: { type: "Boolean" },
        },
    }}
/>

<script lang="ts">
    import autoComplete from "@tarekraafat/autocomplete.js";
    import type { Map as MapLibreMap } from "maplibre-gl";

    import { onMount } from "svelte";
    import { MapManager } from "./MapManager";
    import { mapControl } from "./MapControl";
    import MapSource from "./MapSource.svelte";
    import { SourceType, MapSourceSchema } from "./DatahubTypes";
    import type {
        MapSource as TMapSource,
        DataLayer,
        DataLayerItem,
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
        layerControlNodeId = null,
        height = "500px",
        sidebar = false,
        explore = false,
        openExplore = false,
        sources: initialSources = "[]",
    } = $props();

    let container; // reference to the DOM node of the component

    let mapContainer: HTMLElement;
    let sidebarContainer: HTMLElement;
    let mapManager: MapManager;

    let map = $state<MapLibreMap | undefined>();

    /**
     * Configurable Data Layers
     */
    let datalayers = $state<DataLayerItem[]>([]);

    /**
     * Actual loaded sources. Can be Data Layers, or just shapes, or Vector, ...
     *
     */
    let sources = $state<TMapSource[]>([]);

    let showShare: boolean = $state(false);

    const instanceId = $props.id();

    onMount(async () => {
        // if explore is disabled, but the initial showExplore is true, set to false.
        // if explore is disabled, we don't want to show the UI for exploring as well
        if (!explore && openExplore) {
            openExplore = false;
        }

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
                    resample: null,
                },
            });
        }

        mapManager = new MapManager(mapContainer, {
            layerControlNodeId: layerControlNodeId || sidebarContainer,
        });
        //map = mapManager.getMap();
        mapManager.ready.then((m) => {
            map = m;
        });

        // normalize values after meta data for datalayer are fetched, and update
        // sources value at latest time, the addSource needs a map object.
        if (typeof initialSources === "string") {
            try {
                const newSources = JSON.parse(initialSources);

                for (const userSource of newSources) {
                    userSource.id = mapManager.getNextSourceIdString();

                    if (!userSource.hasOwnProperty("alpha")) {
                        userSource.alpha = userSource.type == "shape" ? 0.3 : 1;
                    }

                    let source = MapSourceSchema.parse(userSource);

                    sources.push(source);
                    fetchSource(source.id);

                    //await mapManager.addSource(userSource);
                }
            } catch (e) {
                console.warn(e, "Invalid JSON in sources:", initialSources);
            }
        }
    });

    export function getMapManager() {
        return mapManager;
    }

    export function getMapLibre() {
        return mapManager.getMapLibre();
    }

    /**
     * Load (or reload) geometry + data for a source via the manager, then merge
     * the derived fields back onto the reactive source. The manager owns the
     * geometry payload and all the heavy transformation; here we only manage the
     * reactive `status` and apply the returned patch.
     */
    async function fetchSource(id: string) {
        const source = sources.find((i) => i.id === id);
        if (!source) return;

        source.status = "loading";

        // pass a plain snapshot across the imperative boundary
        const patch = await mapManager.loadSource($state.snapshot(source));

        // the source may have been deleted while we were loading
        const current = sources.find((i) => i.id === id);
        if (!current) return;

        // patch carries derived fields + the new status ("ready"/"error"),
        // or {} if the load was superseded by a newer one.
        Object.assign(current, patch);
    }

    $effect(() => {
        if (!map) return; // wait for the map; re-runs when set
        const desired = sources.map((i) => ({
            // reading these tracks them; `status` is what re-runs this effect
            // once geometry has been loaded into the manager.
            id: i.id,
            visible: i.visible,
            type: i.type,
            status: i.status,
            alpha: i.alpha,
            color: i.color,
            fitBounds: i.fitBounds,
        }));

        mapManager.reconcile(desired); // imperative map work + geometry live in the manager
    });

    function handleEndDate() {
        if (!query.end_date) {
            query.aggregate = null;
        }
    }

    function hasTop() {
        if (title) {
            return true;
        }

        return false;
    }

    function getCanvasRadiusStyle() {
        if (hasTop()) {
            if (sidebar) {
                return "border-bottom-right-radius: 0.25rem;";
            }
            return "border-bottom-left-radius: 0.25rem; border-bottom-right-radius: 0.25rem;";
        }

        if (sidebar) {
            return "border-top-right-radius: 0.25rem; border-bottom-right-radius: 0.25rem;";
        }

        return "border-radius: 0.25rem;";
    }

    /**
     * Add Data Layer to the selection UI.
     */
    async function addDataLayer(key: string) {
        const res = await fetch("/api/datalayers/meta?datalayer_key=" + key);

        if (!res.ok) {
            alert("Data Layer could not be found.");
            return;
        }

        const response = await res.json();
        const datalayer: DataLayer = response.datalayer;

        datalayers.push({
            key: key,
            datalayer: datalayer,
            query: {
                shape_type: datalayer.shape_types[0].key,
                start_date: null,
                end_date: null,
                aggregate: null,
                resample: null,
            },
        });
    }

    /**
     * Add da new source to map, based on the selected datalayer item.
     *
     * @param item
     */
    function addDataLayerSourceFromExplore(item: DataLayerItem) {
        let actualQuery = JSON.parse(JSON.stringify(item.query)); // deep copy of query

        // check query
        if (!actualQuery.end_date) {
            actualQuery.end_date = actualQuery.start_date;
        }

        if (!actualQuery.datalayer_key) {
            actualQuery.datalayer_key = item.datalayer.key;
        }

        if (!actualQuery.start_date) {
            alert("Please select a date first.");
            return;
        }

        const id = mapManager.getNextSourceIdString();

        sources.unshift(
            MapSourceSchema.parse({
                id: id,
                type: "datalayer",
                alpha: 1,
                query: actualQuery,
                datalayer: item.datalayer,
            }),
        );
        fetchSource(id);
    }

    export function addSource(source: any) {
        // pull the (non-serializable) color scale out before Zod parsing; it's
        // only available via this JS call, not the serialized `sources` attribute.
        const { colorScale, ...rest } = source;

        rest.id = rest.id ?? mapManager.getNextSourceIdString();
        const parsed = MapSourceSchema.parse(rest);
        sources.unshift(parsed);

        mapManager.setColorScale(parsed.id, colorScale);
        fetchSource(parsed.id);
    }

    /**
     * Public API for power users: apply an externally-supplied datalayer data
     * payload to an existing source.
     *
     *   1. flips the source into the "loading" state
     *   2. resolves `data` (awaits it if it's a promise / thunk)
     *   3. applies the data to the source's geometry and pushes it live to the map
     *   4. flips the source back to "ready"
     *
     * `data` may be the payload itself, a Promise of it, or a function returning
     * a Promise of it. Pass a promise/thunk if you want the loading spinner to
     * cover your fetch — the source stays in "loading" for the whole await:
     *
     *   await el.updateSourceData(id, fetch(url).then((r) => r.json()));
     *   await el.updateSourceData(id, () => myApi.getData(id));
     *   await el.updateSourceData(id, alreadyFetchedData); // no visible spinner
     *
     * Because a source stays on the map as long as the manager holds its
     * geometry, the loading -> ready flip here does NOT tear down + rebuild the
     * source, so popups/handlers are left untouched (no duplication).
     *
     * The resolved payload must match the /api/datalayers/data response shape:
     *   { name, is_categorical, categorical_values, categorical_labels,
     *     value_type, data: [{ dh_shape_id, value, formatted }, ...] }
     */
    export async function updateSourceData(
        id: string,
        data: any | Promise<any> | (() => any | Promise<any>),
    ) {
        const source = sources.find((i) => i.id === id);
        if (!source) {
            console.warn(`Source not found: ${id}`);
            return;
        }
        if (source.type !== "datalayer") {
            console.warn(
                `updateSourceData only supports datalayer sources (got "${source.type}")`,
            );
            return;
        }
        if (!mapManager.hasGeometry(id)) {
            console.warn(`Source ${id} has no loaded geometry yet`);
            return;
        }

        source.status = "loading";
        try {
            // await covers both plain values and promises; a function is a
            // lazy producer so the fetch only starts once we're in "loading".
            const resolved =
                typeof data === "function" ? await data() : await data;

            // the source may have been deleted while we were awaiting
            const current = sources.find((i) => i.id === id);
            if (!current) return;

            const patch = mapManager.applyDatalayerData(
                $state.snapshot(current),
                resolved,
            );
            Object.assign(current, patch);
            current.status = "ready";
        } catch (e) {
            console.error("updateSourceData failed", id, e);
            const current = sources.find((i) => i.id === id);
            if (current) current.status = "error";
        }
    }

    /**
     * Public API: manually toggle a source's loading spinner. Useful when you
     * want to drive the loading state around your own arbitrary async work
     * instead of handing it to {@link updateSourceData}:
     *
     *   el.setSourceLoading(id, true);
     *   const data = await myFetch();
     *   el.updateSourceData(id, data); // flips back to ready
     */
    export function setSourceLoading(id: string, loading: boolean) {
        const source = sources.find((i) => i.id === id);
        if (!source) {
            console.warn(`Source not found: ${id}`);
            return;
        }
        source.status = loading ? "loading" : "ready";
    }

    /**
     * Public API: re-fetch a source's geometry (+ data) from the server,
     * optionally with a new query. Use this when you want the component to do
     * the loading itself; use {@link updateSourceData} when you already hold the
     * data payload. Query is shallow-merged onto the existing one.
     *
     *   await el.reloadSource("dh-0-source", { start_date: "2020" });
     */
    export async function reloadSource(
        id: string,
        query?: Record<string, unknown>,
    ) {
        const source = sources.find((i) => i.id === id);
        if (!source) {
            console.warn(`Source not found: ${id}`);
            return;
        }
        if (query) {
            source.query = { ...source.query, ...query };
        }
        await fetchSource(id);
    }

    function addDatalayerVectorSource(datalayer_key: string) {
        addSource({
            type: SourceType.Vector,
            query: {
                datalayer_key: datalayer_key,
            },
        });
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

            const type = feedback.selection.value.type;

            if (type == "datalayer") {
                // datalayer for query definition
                addDataLayer(feedback.selection.value.key);
            } else if (type == "shape") {
                // shape is added directly as source
                addSource({
                    type: "shape",
                    name: feedback.selection.value.label,
                    query: {
                        shape_key: feedback.selection.value.key,
                    },
                });
            } else if (type == "shape_type") {
                // shape is added directly as source
                addSource({
                    type: "shape",
                    name: feedback.selection.value.label,
                    query: {
                        shape_type: feedback.selection.value.key,
                    },
                });
            }

            /*callback(feedback.selection.value);

            // Access the matched key's value from the original object
            const selection = feedback.selection.value[feedback.selection.key];

            node.value = selection;
            node.dispatchEvent(new Event("input")); // needed so svelte catches the change for the binding*/
        });

        return {
            destroy() {
                instance.unInit();
            },
        };
    }

    function moveSource(id: string, dir: number) {
        const i = sources.findIndex((x) => x.id === id);
        const j = i + dir;
        if (j < 0 || j >= sources.length) return;
        [sources[i], sources[j]] = [sources[j], sources[i]];
    }

    function deleteSource(id: string) {
        mapManager.dropSource(id); // abort in-flight fetch + drop geometry
        sources = sources.filter((i) => i.id !== id);
    }
</script>

<div bind:this={container} class="card bg-light mb-3">
    {#if title}
        <div class="card-header">
            <div class="d-flex align-items-center justify-content-between">
                <span>{title}</span>
                <div class="d-flex align-items-center gap-1">
                    {#if explore}
                        <button
                            class="btn btn-outline-secondary btn-xs"
                            class:active={openExplore}
                            onclick={() => (openExplore = !openExplore)}
                            >Explore</button
                        >
                    {/if}

                    <!--
                    <button
                        class="btn btn-outline-secondary btn-xs"
                        class:active={showShare}
                        onclick={() => (showShare = !showShare)}>Share</button
                    >
                        -->
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

    {#if openExplore}
        <div class="card-body border-bottom">
            <div class="row g-3">
                <!--
                    The <div> around the labels is needed for wrapping label/input.
                    The autocomplete would be shown alongside otherwise.
                -->
                <div class="col-12">
                    Search for Data Layers, Shapes or Shape types by name or
                    key, to add them to the map.
                </div>
                <div class="col-12 col-md-4">
                    <label for={`${instanceId}-datalayer`} class="form-label"
                        >Datalayers</label
                    >
                    <input
                        id={`${instanceId}-datalayer`}
                        use:initAutocomplete={{
                            scope: "datalayers",
                        }}
                        placeholder="Search…"
                        type="text"
                        class="form-control form-control-sm"
                    />
                </div>
                <div class="col-12 col-md-4">
                    <label for={`${instanceId}-shapes`} class="form-label"
                        >Shapes</label
                    >
                    <input
                        id={`${instanceId}-shapes`}
                        use:initAutocomplete={{
                            scope: "shapes",
                        }}
                        placeholder="Search…"
                        type="text"
                        class="form-control form-control-sm"
                    />
                </div>
                <div class="col-12 col-md-4">
                    <label for={`${instanceId}-shape_types`} class="form-label">
                        Shape Types</label
                    >
                    <input
                        id={`${instanceId}-shape_types`}
                        use:initAutocomplete={{
                            scope: "shape_types",
                        }}
                        placeholder="Search…"
                        type="text"
                        class="form-control form-control-sm"
                    />
                </div>
            </div>
        </div>
    {/if}

    {#if datalayers.length > 0}
        <div class="border-bottom">
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
                            <label
                                for="aggregate_function"
                                class="form-label small"
                                >Select shape
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
                            <label
                                for="aggregate_function"
                                class="form-label small"
                                >Select temporal
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
                            <label
                                for="aggregate_function"
                                class="form-label small"
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
                            <label
                                for="aggregate_function"
                                class="form-label small"
                                >&nbsp;
                            </label>

                            <div class="">
                                <button
                                    onclick={() => {
                                        addDataLayerSourceFromExplore(item);
                                    }}
                                    class="btn btn-outline-primary btn-sm"
                                    >Add</button
                                >

                                {#if item.datalayer.has_vector_data}
                                    <button
                                        onclick={() =>
                                            addDatalayerVectorSource(
                                                item.datalayer.key,
                                            )}
                                        class="btn btn-outline-primary btn-sm"
                                        >Load vector data</button
                                    >
                                {/if}
                            </div>
                        </div>
                    </div>
                </div>
            {/each}
        </div>
    {/if}

    <!--
        {#if map} meeds to duplicated, so that if sidebar is requested, the map-sidebar
        container is drawn, and the map container gets the correct width.
        otherwise the centering of the map would be moved by the width of the sidebar.
    -->
    <div class="d-md-flex">
        {#if sidebar}
            <div class="bg-light p-3 map-sidebar">
                <!-- is this if map required? -->
                {#if true}
                    {#each sources as source, i (source.id)}
                        <MapSource
                            bind:source={sources[i]}
                            manager={mapManager}
                            onmove={(dir: number) => moveSource(source.id, dir)}
                            ondelete={() => deleteSource(source.id)}
                            first={i === 0}
                            last={i === sources.length - 1}
                        />
                    {:else}
                        <div
                            class="w-100 h-100 d-flex justify-content-center align-items-center text-muted"
                        >
                            Add new sources to the Map.
                        </div>
                    {/each}
                {/if}
            </div>
        {:else if map}
            <div
                class="source-list"
                {@attach mapControl(mapManager.getMap(), "top-left")}
            >
                {#each sources as source, i (source.id)}
                    <MapSource
                        bind:source={sources[i]}
                        manager={mapManager}
                        onmove={(dir: number) => moveSource(source.id, dir)}
                        ondelete={() => deleteSource(source.id)}
                        first={i === 0}
                        last={i === sources.length - 1}
                    />
                {/each}
            </div>
        {/if}

        <div
            class="flex-grow-1"
            style="{getCanvasRadiusStyle()} height: {height}"
            bind:this={mapContainer}
        ></div>
    </div>

    {#if import.meta.env.DEV}
        <div>
            <details>
                <summary>Debug sources</summary>
                <pre><code>{JSON.stringify(sources, null, 4)}</code></pre>
            </details>
        </div>
    {/if}
</div>

<style>
    .map-sidebar {
        min-height: 100%;
        overflow-y: scroll;

        font-size: 12px;
        border-bottom-left-radius: 0.25rem;
    }

    @media (min-width: 768px) {
        .map-sidebar {
            width: 360px;
            border-right: var(--bs-border-width) var(--bs-border-style)
                var(--bs-border-color);
        }
    }
</style>
