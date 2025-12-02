<!--
SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>

SPDX-License-Identifier: AGPL-3.0-only
-->
<svelte:options
    customElement={{
        tag: "dh-chart",
        shadow: "none",
    }}
/>

<script>
    import { onMount } from "svelte";

    //import Plotly, { addTraces, reverse } from 'plotly.js-dist';

    export let title = "Temporal";
    export let dl;
    export let query = "";
    export let show_remove = false;

    let container; // reference to the DOM node of the component

    let Plotly;
    let datalayer = {
        shape_types: [],
    };
    let chart;

    let data = [];
    let layout = {};
    let config = {};

    let resampleTo = "";
    let shapeType = "";
    let shapeId = "";

    let aggregate;
    let dateStart;
    let dateEnd;

    onMount(async () => {
        Plotly = await import("plotly.js-dist");

        // fetch datalayer layout information for charts
        const res = await fetch("/api/datalayers/meta?datalayer_key=" + dl);
        const meta = await res.json();

        layout = meta.plotly.layout;
        config = meta.plotly.config;
        datalayer = meta.datalayer;

        shapeType = datalayer.shape_types[0].key;
        shapeId = datalayer.shapes[0].id;

        Plotly.newPlot(chart, data, layout, config);

        if (query && (typeof query === "string" || query instanceof String)) {
            addTrace(JSON.parse(query));
        }
    });

    async function addTrace(query, traceOverwrites = {}) {
        let newTraces;

        if (aggregate) {
            query["aggregate"] = aggregate;
        }
        if (resampleTo) {
            query["resample"] = resampleTo;
        }
        if (dateStart) {
            query["start_date"] = dateStart;
        }
        if (dateEnd) {
            query["end_date"] = dateEnd;
        }

        if ("shape_type" in query) {
            const res = await fetch(
                `/api/datalayers/plotly?datalayer_key=${dl}&${new URLSearchParams(query).toString()}`,
            );
            const traces = await res.json();
            newTraces = traces.traces;
        } else {
            const res = await fetch(
                `/api/datalayers/data?datalayer_key=${dl}&${new URLSearchParams(query).toString()}&format=plotly`,
            );
            const trace = await res.json();
            newTraces = { ...trace, ...traceOverwrites };
        }

        Plotly.addTraces(chart, newTraces);
    }

    async function addShapeType(event) {
        addTrace({
            shape_type: shapeType,
        });
    }

    async function addShape(event) {
        addTrace({
            shape_id: shapeId,
        });
    }

    function zoomChart() {
        if (dateStart && dateEnd) {
            Plotly.relayout(chart, {
                "xaxis.range": [dateStart.toString(), dateEnd.toString()],
            });
        }
    }

    function clearTraces() {
        data = [];
        Plotly.newPlot(chart, data, layout, config);
    }
</script>

<div bind:this={container} class="card bg-light mb-3">
    <div class="card-header">{title}</div>

    <div class="card-body">
        <div class="row">
            <div class="col-6 col-md-3 col-lg-2">
                <div class="mb-3">
                    <label for="temporal_resolution" class="form-label small"
                        >Temporal resolution</label
                    >

                    {#if datalayer.temporal_resolution == "date"}
                        <select
                            id="temporal_resolution"
                            class="form-select form-select-sm"
                            bind:value={resampleTo}
                        >
                            <option value="">Original (D)</option>
                            <option value="W-MON">Week (W-MON)</option>
                            <option value="M">Month (M)</option>
                            <option value="Y">Year (Y)</option>
                        </select>
                    {:else if datalayer.temporal_resolution == "week"}
                        <select
                            id="temporal_resolution"
                            class="form-select form-select-sm"
                            bind:value={resampleTo}
                        >
                            <option value="">Original (W-MON)</option>
                            <option value="M">Month (M)</option>
                            <option value="Y">Year (Y)</option>
                        </select>
                    {:else}
                        <div class="col-form-label-sm text-muted fst-italic">
                            No resampling.
                        </div>
                    {/if}
                </div>
            </div>

            <div class="col-6 col-md-3 col-lg-2">
                <div class="mb-3">
                    <label for="aggregate_function" class="form-label small"
                        >Aggregate function</label
                    >

                    <select
                        id="aggregate_function"
                        class="form-select form-select-sm"
                        bind:value={aggregate}
                    >
                        <option value="">None</option>
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

            <div class="col-6 c col-md-3 col-lg-2">
                <div class="mb-3">
                    <label for="start_date" class="form-label small"
                        >Start date</label
                    >

                    {#if datalayer.temporal_resolution == "year"}
                        <select
                            id="start_date"
                            class="form-select form-select-sm"
                            bind:value={dateStart}
                        >
                            <!-- expand the array with [...var] and reverse, so we don't reverse the original array! -->
                            {#each [...datalayer.available_years].reverse() as year}
                                <option value={year}>{year}</option>
                            {/each}
                        </select>
                    {:else if datalayer.temporal_resolution == "date"}
                        <input
                            id="start_date"
                            type="date"
                            class="form-control form-control-sm"
                            bind:value={dateStart}
                            min={datalayer.first_time}
                            max={datalayer.last_time}
                        />
                    {/if}
                </div>
            </div>

            <div class="col-6 col-md-3 col-lg-2">
                <div class="mb-3">
                    <label for="end_date" class="form-label small"
                        >End date</label
                    >

                    {#if datalayer.temporal_resolution == "year"}
                        <select
                            id="end_date"
                            class="form-select form-select-sm"
                            bind:value={dateEnd}
                        >
                            {#each datalayer.available_years as year}
                                <option value={year}>{year}</option>
                            {/each}
                        </select>
                    {:else if datalayer.temporal_resolution == "date"}
                        <input
                            id="end_date"
                            type="date"
                            class="form-control form-control-sm"
                            bind:value={dateEnd}
                            min={datalayer.first_time}
                            max={datalayer.last_time}
                        />
                    {/if}
                </div>
            </div>

            <div class="col-4 col-sm-6 col-md-2 d-flex align-items-end">
                <div class="mb-3">
                    <button
                        on:click={zoomChart}
                        class="btn btn-sm btn-outline-secondary"
                        type="button">Zoom chart</button
                    >
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-4 col-md-2">
                <div class="mb-3 mb-sm-0">
                    <label for="formGroupExampleInput" class="form-label small"
                        >Shape type means</label
                    >
                    <div class="input-group">
                        <select
                            class="form-select form-select-sm"
                            bind:value={shapeType}
                        >
                            {#each datalayer.shape_types as shape_type}
                                <option value={shape_type.key}
                                    >{shape_type.name}</option
                                >
                            {/each}
                        </select>

                        <button
                            on:click={addShapeType}
                            class="btn btn-sm btn-outline-secondary"
                            type="button">Add</button
                        >
                    </div>
                </div>
            </div>
            <div class="col-8 col-md-4">
                <div class="mb-3 mb-sm-0">
                    <label for="formGroupExampleInput" class="form-label small"
                        >Individual Shape</label
                    >
                    <div class="input-group">
                        <select
                            class="form-select form-select-sm"
                            bind:value={shapeId}
                        >
                            {#each datalayer.shapes as shape}
                                {#if shape.disabled}
                                    <option disabled value={shape.id}
                                        >{shape.name}</option
                                    >
                                {:else}
                                    <option value={shape.id}
                                        >{shape.name}</option
                                    >
                                {/if}
                            {/each}
                        </select>

                        <button
                            on:click={addShape}
                            class="btn btn-sm btn-outline-secondary"
                            type="button">Add</button
                        >
                    </div>
                </div>
            </div>

            <div
                class="col-12 col-md-6 d-flex align-items-end justify-content-end"
            >
                <button
                    on:click={clearTraces}
                    class="btn btn-sm btn-outline-secondary">Clear chart</button
                >

                {#if show_remove}
                    <span class="ms-3 me-3 border-start d-inline-block"></span>
                    <button
                        on:click={() => container.parentNode.remove()}
                        class="btn btn-sm btn-outline-danger"
                        >Delete chart</button
                    >
                {/if}
            </div>
        </div>
    </div>

    <div class="rounded-bottom overflow-hidden">
        <div style="min-height: 450px" bind:this={chart}></div>
    </div>
</div>
