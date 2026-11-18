<!--
SPDX-FileCopyrightText: 2026 Jonathan Ströbele <mail@jonathanstroebele.de>

SPDX-License-Identifier: AGPL-3.0-only
-->
<script lang="ts">
    import { onMount } from "svelte";

    import { LegendMode } from "./DatahubTypes";
    import type { MapSource as TMapSource, DataLayer } from "./DatahubTypes";
    import { MapManager } from "./MapManager";

    import { Legend } from "../d3/d3.legend.js";
    import { Swatches } from "../d3/d3.swatches.js";

    import { COLOR_SCALES, buildScale } from "./legend";

    let {
        source = $bindable(),
        manager,
    }: { source: TMapSource; manager: MapManager } = $props();

    let legendContainer: HTMLElement;

    onMount(async () => {});

    const color = $derived(
        manager.getColorScale(source.id) ??
            buildScale(
                source.isCategorical,
                source.cmap,
                source.extent,
                source.categoricalValues,
                source.categoricalColors,
            ),
    );

    // an external scale defines its own grading, so the cmap/mode controls and
    // the extent-from-mode effect below don't apply to it.
    const hasCustomScale = $derived(!!manager.getColorScale(source.id));

    $effect(() => {
        if (hasCustomScale) return; // external scale owns its own domain
        if (source.mode == "from0_1") {
            source.extent = [0, 1];
        } else if (source.mode == "min_max") {
            source.extent = source.actualExtent;
        }
    });

    $effect(() => {
        if (source.status != "ready") {
            return;
        }

        let legend;
        if (source.isCategorical) {
            legend = Swatches(color, {
                format: (v) => {
                    return (
                        source.categoricalLabels[
                            source.categoricalValues.indexOf(v)
                        ] ?? v
                    );
                },
            });
        } else if (source.isPercentage) {
            legend = Legend(color, {
                tickFormat: "%",
            });
        } else {
            legend = Legend(color, {});
        }

        legendContainer.replaceChildren(legend);

        // update on map
        manager.setColor(source.id, color);

        /*const fc = geometry.get(source.id);
        if (!fc) return;
        recolor(fc, values, scale); // reads `scale` → reruns when colorScale changes
        manager.setData(source.id, fc); // live update, no layer/paint touched*/
    });
</script>

<div>
    {#if source.showQueryLabel}
        <small class="d-block lh-1 text-muted">
            <code>{source.query.datalayer_key}</code>:
            {source.query.shape_type}, {source.query
                .start_date}{#if source.query.start_date != source.query.end_date}–{source
                    .query.end_date} | {source.query.aggregate}
            {/if}</small
        >
    {/if}

    <div bind:this={legendContainer}></div>

    {#if source.showControls}
        {#if !source.isCategorical && !hasCustomScale}
            {#if source.isPercentage}
                <select bind:value={source.mode}>
                    <option value="min_max">[min, max]</option>
                    <option value="from0_1">[0, 100]</option>
                </select>
            {/if}

            <select bind:value={source.cmap}>
                {#each Object.keys(COLOR_SCALES) as name}
                    <option value={name}>{name}</option>
                {/each}
            </select>
        {/if}
    {/if}
</div>
