<!--
SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>

SPDX-License-Identifier: AGPL-3.0-only
-->
<svelte:options
    customElement={{
        tag: "dh-chart",
        shadow: "none",
        props: {
            // type: Boolean converts only presence -> true, absence -> false
            // we can't do explore="false", to set it to false we need to remove it.
            explore: { type: "Boolean" },
            openExplore: { type: "Boolean" },
            noControls: { type: "Boolean" },
        },
    }}
/>

<script lang="ts">
    import { onMount } from "svelte";
    import autoComplete from "@tarekraafat/autocomplete.js";

    import { schemeCategory10 } from "d3";

    //import Plotly, { addTraces, reverse } from 'plotly.js-dist';
    import type { ChartSource, DataLayer, DataLayerItem } from "./DatahubTypes";
    import { ChartSourceSchema } from "./DatahubTypes";

    let Plotly;

    interface AutocompleteOptions {
        scope: string;
        item: DataLayerItem | null;
    }

    const instanceId = $props.id();

    let {
        title = "Temporal",
        dl = null,
        dl2 = null,
        noControls = false,
        explore = false,
        openExplore = false,
        sources: initialSources = "[]",
    } = $props();

    let container: HTMLElement; // reference to the DOM node of the component

    /**
     * Configurable Data Layers
     */
    let datalayers = $state<DataLayerItem[]>([]);

    let chart: HTMLElement;

    let y1: DataLayer | null = null;
    let y2: DataLayer | null = null;

    let data = [];
    let layout: any = {};
    let config = {};

    let showControls = true;

    const colors = schemeCategory10;
    let i = 0;
    function nextColor() {
        return colors[i++ % colors.length];
    }

    onMount(async () => {
        // if explore is disabled, but the initial showExplore is true, set to false.
        // if explore is disabled, we don't want to show the UI for exploring as well
        if (!explore && openExplore) {
            openExplore = false;
        }

        Plotly = await import("plotly.js-cartesian-dist-min");

        // fetch datalayer layout information for yaxis1
        if (dl) {
            const res = await fetch("/api/datalayers/meta?datalayer_key=" + dl);
            const response = await res.json();
            const datalayer: DataLayer = response.datalayer;

            layout = response.plotly.layout;
            config = response.plotly.config;

            y1 = datalayer;

            datalayers.push({
                key: dl,
                datalayer: datalayer,
                yaxis: "y1",
                query: {
                    shape_type: datalayer.shape_types[0].key,
                    start_date: datalayer.first_time,
                    end_date: datalayer.last_time,
                    aggregate: null,
                    resample: null,
                },
            });
        }

        // if present, use for yaxis2
        if (dl2) {
            const res = await fetch(
                "/api/datalayers/meta?datalayer_key=" + dl2,
            );
            const response = await res.json();
            const datalayer: DataLayer = response.datalayer;

            y2 = datalayer;
            datalayers.push({
                key: dl2,
                datalayer: datalayer,
                yaxis: "y2",
                query: {
                    shape_type: datalayer.shape_types[0].key,
                    start_date: datalayer.first_time,
                    end_date: datalayer.last_time,
                    aggregate: null,
                    resample: null,
                },
            });

            let yaxis2 = response.plotly.layout.yaxis;
            yaxis2["side"] = "right";
            yaxis2["overlaying"] = "y";

            layout["yaxis2"] = yaxis2;
        }

        Plotly.newPlot(chart, data, layout, config);

        if (typeof initialSources === "string") {
            try {
                const newSources = JSON.parse(initialSources);

                for (const userSource of newSources) {
                    let source = ChartSourceSchema.parse(userSource);
                    await addTrace(source);
                }
            } catch (e) {
                console.warn(e, "Invalid JSON in sources:", initialSources);
            }
        }
    });

    /**
     * Add Data Layer to the selection UI.
     */
    async function addDataLayer(key: string) {
        const res = await fetch("/api/datalayers/meta/?datalayer_key=" + key);

        if (!res.ok) {
            alert("Data Layer could not be found.");
            return;
        }

        const response = await res.json();
        const datalayer: DataLayer = response.datalayer;
        let yaxis = "y1";

        // has the plot already an layout?
        if (!y1) {
            layout = response.plotly.layout;
            config = response.plotly.config;
            y1 = datalayer;

            Plotly.newPlot(chart, data, layout, config);
        } else if (!y2) {
            // do we need a second axis?
            if (y1.format_suffix != datalayer.format_suffix) {
                y2 = datalayer;
                yaxis = "y2";
                let yaxis2 = response.plotly.layout.yaxis;
                yaxis2["side"] = "right";
                yaxis2["overlaying"] = "y";

                Plotly.relayout(chart, {
                    yaxis2: yaxis2,
                });
            }
        }

        datalayers.push({
            key: key,
            datalayer: datalayer,
            yaxis: yaxis,
            query: {
                shape_type: datalayer.shape_types[0].key,
                start_date: datalayer.first_time,
                end_date: datalayer.last_time,
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

        const yaxis = item.yaxis;

        actualQuery.datalayer_key = item.datalayer.key;

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

        const source = ChartSourceSchema.parse({
            yaxis: yaxis,
            query: actualQuery,
        });

        addTrace(source);
    }

    async function addTrace(source: ChartSource) {
        let newTraces;
        let query = source.query;

        if (query.shape_key === null) {
            delete query.shape_key;
        }
        if (query.shape_type === null) {
            delete query.shape_type;
        }

        if (query.aggregate === null) {
            delete query.aggregate;
        } else {
            // in case we aggregate data over a shape type (affecting all  shapes of this type)
            // we don't want to aggregate spatially but on the temporal axis
            // get the the aggregated value at each temporal step for all shapes, instead of
            // getting one value off all shapes over the whole time frame.
            if ("shape_type" in query) {
                query.aggregate_group_by = "temporal";
            }
        }

        if (query.resample === null) {
            delete query.resample;
        }

        query.color = nextColor();

        const res = await fetch(
            `/api/datalayers/data/?${new URLSearchParams(query).toString()}&format=plotly`,
        );

        if (!res.ok) {
            const message = await res.text();
            alert(message);
            return;
        }

        if (res.status == 204) {
            alert("No data did match the query.");
            return;
        }

        const data = await res.json();
        newTraces = data.traces;

        let traceOverwrite = {};
        if (source.yaxis != "y1") {
            traceOverwrite = {
                yaxis: source.yaxis,
            };

            newTraces = newTraces.map((item) => ({
                ...item,
                ...traceOverwrite,
            }));
        }

        Plotly.addTraces(chart, newTraces).then(() => {
            updateBottomMargin();
        });
    }

    /**
     * Ploty has a height and new trace legends would make the plot area smaller.
     * This calculates a new height and bottom margin to make room for the new legend
     * entry.
     */
    function updateBottomMargin() {
        const BASE_HEIGHT = 450;
        const BASE_MARGIN_B = 12;
        const ROW_HEIGHT = 28;

        // shape type traces actually can contain 3 traces (avg/min/max). The min/max
        // traces have no legend and don't need to be counted.
        const rows = chart.data.filter(
            (trace) => trace.showlegend !== false,
        ).length;

        const newMarginB = BASE_MARGIN_B + rows * ROW_HEIGHT;
        const totalHeight = BASE_HEIGHT + rows * ROW_HEIGHT;

        Plotly.relayout(chart, {
            height: totalHeight,
            "margin.b": newMarginB,
        });
    }

    function clearTraces() {
        data = [];
        Plotly.newPlot(chart, data, layout, config);
    }

    function initAutocomplete(
        node: HTMLInputElement,
        options: AutocompleteOptions,
    ) {
        const { scope, item } = options;

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
                node.value = "";
            } else if (type == "shape" && item) {
                // shape is added directly as source

                item.query.shape_key = feedback.selection.value.key;
                item.query.shape_type = null;
                node.value = feedback.selection.value.label;

                //addTrace({
                //    shape_key: feedback.selection.value.key,
                //});
            } else if (type == "shape_type" && item) {
                // shape is added directly as source
                item.query.shape_key = null;
                item.query.shape_type = feedback.selection.value.key;

                item.query.aggregate = "mean";

                node.value = feedback.selection.value.label;
                //addTrace({
                //    shape_type: feedback.selection.value.key,
                //});
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
</script>

<div bind:this={container} class="card bg-light mb-3">
    {#if title}
        <div class="card-header">
            <div class="d-flex align-items-center justify-content-between">
                <span>{title}</span>
                <div class="d-flex align-items-center gap-1">
                    {#if !noControls}
                        {#if explore}
                            <button
                                class="btn btn-outline-secondary btn-xs"
                                class:active={openExplore}
                                onclick={() => (openExplore = !openExplore)}
                                >Explore</button
                            >
                        {/if}
                    {/if}
                </div>
            </div>
        </div>
    {/if}

    {#if !noControls}
        {#if showControls}
            {#if openExplore}
                <div class="card-body border-bottom">
                    <div class="row g-3">
                        <!--
                    The <div> around the labels is needed for wrapping label/input.
                    The autocomplete would be shown alongside otherwise.
                -->
                        <div class="col-12">
                            Search for Data Layers by name or key, to add them
                            to the chart selector.
                        </div>
                        <div class="col-12 col-md-4">
                            <label
                                for={`${instanceId}-datalayer`}
                                class="form-label">Datalayers</label
                            >
                            <input
                                id={`${instanceId}-datalayer`}
                                use:initAutocomplete={{
                                    scope: "datalayers",
                                    item: null,
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
                <div class="card-body">
                    {#each datalayers as item, i (item.key)}
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
                            <div class="col-12 col-md-3 col-lg-2">
                                <div>
                                    <label
                                        for={`${instanceId}-${i}-shapes`}
                                        class="form-label">Select shape</label
                                    >
                                </div>
                                <input
                                    id={`${instanceId}-${i}-shapes`}
                                    use:initAutocomplete={{
                                        scope: "shapes,shape_types",
                                        item: item,
                                    }}
                                    placeholder="Search…"
                                    type="text"
                                    class="form-control form-control-sm"
                                />
                            </div>
                            <div class="col-6 c col-md-3 col-lg-2">
                                <div class="mb-3">
                                    <label
                                        for={`${instanceId}-${i}-start_date`}
                                        class="form-label small"
                                        >Start date</label
                                    >

                                    {#if item.datalayer.temporal_resolution == "year"}
                                        <select
                                            id={`${instanceId}-${i}-start_date`}
                                            class="form-select form-select-sm"
                                            bind:value={item.query.start_date}
                                        >
                                            <!-- expand the array with [...var] and reverse, so we don't reverse the original array! -->
                                            {#each [...item.datalayer.available_years].reverse() as year}
                                                <option value={year}
                                                    >{year}</option
                                                >
                                            {/each}
                                        </select>
                                    {:else if item.datalayer.temporal_resolution == "month"}
                                        <input
                                            id={`${instanceId}-${i}-start_date`}
                                            type="text"
                                            class="form-control form-control-sm"
                                            placeholder="yyyy-mm"
                                            bind:value={item.query.start_date}
                                        />
                                    {:else if item.datalayer.temporal_resolution == "week"}
                                        <input
                                            id={`${instanceId}-${i}-start_date`}
                                            type="text"
                                            class="form-control form-control-sm"
                                            placeholder="yyyy-Www"
                                            bind:value={item.query.start_date}
                                        />
                                    {:else if item.datalayer.temporal_resolution == "date"}
                                        <input
                                            id={`${instanceId}-${i}-start_date`}
                                            type="date"
                                            class="form-control form-control-sm"
                                            bind:value={item.query.start_date}
                                            min={item.datalayer.first_time}
                                            max={item.datalayer.last_time}
                                        />
                                    {/if}
                                </div>
                            </div>

                            <div class="col-6 col-md-3 col-lg-2">
                                <div class="mb-3">
                                    <label
                                        for={`${instanceId}-${i}-end_date`}
                                        class="form-label small">End date</label
                                    >

                                    {#if item.datalayer.temporal_resolution == "year"}
                                        <select
                                            id={`${instanceId}-${i}-end_date`}
                                            class="form-select form-select-sm"
                                            bind:value={item.query.end_date}
                                        >
                                            {#each item.datalayer.available_years as year}
                                                <option value={year}
                                                    >{year}</option
                                                >
                                            {/each}
                                        </select>
                                    {:else if item.datalayer.temporal_resolution == "month"}
                                        <input
                                            id={`${instanceId}-${i}-end_date`}
                                            type="text"
                                            class="form-control form-control-sm"
                                            placeholder="yyyy-mm"
                                            bind:value={item.query.end_date}
                                        />
                                    {:else if item.datalayer.temporal_resolution == "week"}
                                        <input
                                            id={`${instanceId}-${i}-end_date`}
                                            type="text"
                                            class="form-control form-control-sm"
                                            placeholder="yyyy-Www"
                                            bind:value={item.query.end_date}
                                        />
                                    {:else if item.datalayer.temporal_resolution == "date"}
                                        <input
                                            id={`${instanceId}-${i}-end_date`}
                                            type="date"
                                            class="form-control form-control-sm"
                                            bind:value={item.query.end_date}
                                            min={item.datalayer.first_time}
                                            max={item.datalayer.last_time}
                                        />
                                    {/if}
                                </div>
                            </div>

                            <div class="col-6 col-md-3 col-lg-2">
                                <div class="mb-3">
                                    <label
                                        for={`${instanceId}-${i}-temporal_resolution`}
                                        class="form-label small"
                                        >Temporal resampling</label
                                    >

                                    {#if item.datalayer.temporal_resolution == "date"}
                                        <select
                                            id={`${instanceId}-${i}-temporal_resolution`}
                                            class="form-select form-select-sm"
                                            bind:value={item.query.resample}
                                        >
                                            <option value={null}>None</option>
                                            <option value="W-MON"
                                                >Week (W-MON)</option
                                            >
                                            <option value="MS"
                                                >Month (MS)</option
                                            >
                                            <option value="YS">Year (YS)</option
                                            >
                                        </select>
                                    {:else if item.datalayer.temporal_resolution == "week"}
                                        <select
                                            id={`${instanceId}-${i}-temporal_resolution`}
                                            class="form-select form-select-sm"
                                            bind:value={item.query.resample}
                                        >
                                            <option value={null}>None</option>
                                            <option value="MS"
                                                >Month (MS)</option
                                            >
                                            <option value="YS">Year (YS)</option
                                            >
                                        </select>
                                    {:else if item.datalayer.temporal_resolution == "month"}
                                        <select
                                            id={`${instanceId}-${i}-temporal_resolution`}
                                            class="form-select form-select-sm"
                                            bind:value={item.query.resample}
                                        >
                                            <option value={null}>None</option>
                                            <option value="YS"
                                                >Year start (YS)</option
                                            >
                                            <option value="YE"
                                                >Year end (YE)</option
                                            >
                                        </select>
                                    {:else}
                                        <div
                                            class="col-form-label-sm text-muted fst-italic"
                                        >
                                            No resampling.
                                        </div>
                                    {/if}
                                </div>
                            </div>

                            <div class="col-6 col-md-3 col-lg-2">
                                <div class="mb-3">
                                    <label
                                        for={`${instanceId}-${i}-aggregate_function`}
                                        class="form-label small"
                                        >Aggregate function</label
                                    >

                                    <select
                                        id={`${instanceId}-${i}-aggregate_function`}
                                        class="form-select form-select-sm"
                                        bind:value={item.query.aggregate}
                                    >
                                        <option value={null}>None</option>
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

                            <div class="col-12 col-sm-4 col-lg-2">
                                <label
                                    for="aggregate_function"
                                    class="form-label small"
                                    >Select y-axis
                                </label>

                                <div class="input-group">
                                    <select
                                        class="form-select form-select-sm"
                                        bind:value={item.yaxis}
                                    >
                                        <option value="y1">y1</option>
                                        <option value="y2">y2</option>
                                    </select>

                                    <button
                                        onclick={() => {
                                            addDataLayerSourceFromExplore(item);
                                        }}
                                        class="btn btn-outline-primary btn-sm"
                                        >Add</button
                                    >
                                </div>
                            </div>
                        </div>
                    {/each}
                </div>
            {/if}
        {/if}
    {/if}

    <div class="rounded-bottom overflow-hidden">
        <div style="min-height: 450px" bind:this={chart}></div>
    </div>
</div>
