<svelte:options
    customElement={{
        tag: "dh-chart",
        shadow: 'none',
    }}
/>

<script>
    import { onMount } from 'svelte';
    import { autocomplete } from '@algolia/autocomplete-js';

    //import Plotly, { addTraces, reverse } from 'plotly.js-dist';


    export let dl;
    export let query = "";


    let Plotly;
    let datalayer = {
        shape_types: [],
    };
    let chart;
    let shapeselect;

    let data = [];
    let layout = {};
    let config = {};

    let resampleTo = "";
    let shapeType = "";
    let zoomStart;
    let zoomEnd;

    onMount(async () => {

        Plotly = await import('plotly.js-dist');

        // fetch datalayer layout information for charts
        const res = await fetch('/api/datalayers/meta?datalayer_key='+dl)
        const meta = await res.json();

        layout = meta.plotly.layout;
        config = meta.plotly.config;
        datalayer = meta.datalayer;

        Plotly.newPlot(chart, data, layout, config);

        if (query && (typeof query === 'string' || query instanceof String)) {
            addTrace(JSON.parse(query));
        }

        autocomplete({
            container: shapeselect,
            placeholder: 'Add individual shapes…',
            getSources({ query }) {
                return [
                    {
                    sourceId: 'suggestions',
                    getItems() {
                        return fetch('/search?f=shapes&q=' + encodeURIComponent(query))
                        .then(response => response.json())
                        .then(data => {
                            return data.results;
                        })
                        .catch(error => {
                            return [];
                        });
                    },
                    onSelect: function(event) {
                        addTrace({
                            'shape_id': event.item.objectID,
                            'resample': resampleTo,
                        }, {'name': event.item.label});
                    },
                    templates: {
                        item({ item, createElement }) {
                            return createElement("div", {
                            dangerouslySetInnerHTML: {
                                __html: `${item.label}`
                            }
                            });
                        },
                        noResults() {
                            return 'No results matching.';
                        },
                    },
                    },
                ];
            }
        });
    });


    async function addTrace(query, traceOverwrites = {}) {
        let newTraces;

        query['resample'] = resampleTo;

        if ("shape_type" in query) {
            const res = await fetch(`/api/datalayers/plotly?datalayer_key=${dl}&${new URLSearchParams(query).toString()}`)
            const traces = await res.json();
            newTraces = traces.traces;
        } else {
            const res = await fetch(`/api/datalayers/data?datalayer_key=${dl}&${new URLSearchParams(query).toString()}&format=plotly`)
            const trace = await res.json();
            newTraces = {...trace, ...traceOverwrites};
        }

		Plotly.addTraces(chart, newTraces);
    };

    async function addShapeType(event) {
        addTrace({
            shape_type: shapeType,
        });
        shapeType = "";
    }

    function zoomChart() {
        var update = {
		    'xaxis.range': [zoomStart.toString(), zoomEnd.toString()],
	    };
    	Plotly.relayout(chart, update)
    };

    function clearTraces() {
        data = [];
        Plotly.newPlot(chart, data, layout, config);
    }

</script>

<div class="card bg-light mb-3">

    <div class="rounded-top overflow-hidden">
        <div bind:this={chart}></div>
    </div>

    <div class="card-body">


        <p class="mb-1">
            Add data to the chart:
        </p>
        <div class="row mb-3">
            <div class="col-4 col-md-2">
                {#if datalayer.temporal_resolution == 'date' }
                <select class="form-select" bind:value={resampleTo}>
                    <option value="">Original resolution</option>
                    <option value="W-MON">Resample on week (W-MON)</option>
                    <option value="M">Resample on month (M)</option>
                </select>
                {:else}
                    <div class="col-form-label text-muted fst-italic">No resampling.</div>
                {/if}
            </div>
            <div class="col-8 col-md-4">
                <select class="form-select" bind:value={shapeType} on:change={addShapeType}>
                    <option value="">Add shape types…</option>
                    {#each datalayer.shape_types as shape_type}
                    <option value="{ shape_type.key }">{ shape_type.name }</option>
                    {/each}
                </select>
            </div>

            <div class="col-12 col-md-6">
                <div bind:this={shapeselect}></div>
            </div>
        </div>


        <p class="mb-1 border-top pt-3">
            Work with the chart:
        </p>
        <div class="row">
            <div class="col-12 col-md-6">

                <div class="input-group">
                    {#if datalayer.temporal_resolution == 'year' }
                        <select class="form-select form-select-sm" bind:value={zoomStart}>
                            <!-- expand the array with [...var] and reverse, so we don't reverse the original array! -->
                            {#each [...datalayer.available_years].reverse() as year}
                            <option value="{ year }">{ year }</option>
                            {/each}
                        </select>
                        <select class="form-select form-select-sm" bind:value={zoomEnd}>
                            {#each datalayer.available_years as year }
                            <option value="{year}">{year}</option>
                            {/each}
                        </select>
                    {:else if datalayer.temporal_resolution == 'date'}
                        <input type="date" class="form-control form-control-sm" bind:value={zoomStart} min="{ datalayer.first_time}" max="{ datalayer.last_time }">
                        <input type="date" class="form-control form-control-sm" bind:value={zoomEnd} min="{ datalayer.first_time }" max="{ datalayer.last_time}">
                    {/if}
                <button on:click={zoomChart} class="btn btn-sm btn-outline-secondary" type="button">Zoom</button>
                </div>

            </div>
            <div class="col-12 col-md-6">
                <div class="d-flex justify-content-end">
                    <button on:click={clearTraces} class="btn btn-sm btn-outline-secondary">Clear chart</button>
                </div>
            </div>
        </div>
    </div>
</div>
