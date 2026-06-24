<!--
SPDX-FileCopyrightText: 2026 Jonathan Ströbele <mail@jonathanstroebele.de>

SPDX-License-Identifier: AGPL-3.0-only
-->
<script lang="ts">
    import { onMount } from "svelte";

    import type { MapSource as TMapSource, DataLayer } from "./DatahubTypes";
    import { MapManager } from "./MapManager";

    import MapSourceShape from "./MapSourceShape.svelte";
    import MapSourceDatalayer from "./MapSourceDatalayer.svelte";

    interface Prop {
        source: TMapSource;
        manager: MapManager;
        ondelete: () => void;
        onmove: (dir: -1 | 1) => void;
        first?: boolean;
        last?: boolean;
    }

    let {
        source = $bindable(),
        manager,
        onmove,
        ondelete,
        first = false,
        last = false,
    }: Prop = $props();

    onMount(async () => {});

    function fitToBounds(id: string) {
        manager.fitToSourceBounds(id);
    }
</script>

<div class="border p-1 ps-2 bg-white rounded-2 mb-2">
    <div class="d-flex justify-content-between align-items-start pb-1">
        <div class="d-flex align-items-start pt-1">
            <input type="checkbox" bind:checked={source.visible} />
            <div class="px-1 d-block lh-sm text-break">
                <b>{source.name || source.type}</b>
            </div>
        </div>

        <div class="btn-toolbar flex-nowrap">
            {#if source.status == "loading"}
                <div
                    class="spinner-border me-2 mt-2"
                    role="status"
                    style="width: 1em; height: 1em; border-width: 0.125em;"
                >
                    <span class="visually-hidden">Loading...</span>
                </div>
            {/if}

            <div class="btn-group me-1">
                <button
                    onclick={() => fitToBounds(source.id)}
                    class="btn btn-outline-secondary btn-xs"
                >
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        viewBox="0 0 16 16"
                        width="16"
                        height="16"
                        ><path
                            d="M2.75 2.5a.25.25 0 0 0-.25.25v2.5a.75.75 0 0 1-1.5 0v-2.5C1 1.784 1.784 1 2.75 1h2.5a.75.75 0 0 1 0 1.5h-2.5ZM10 1.75a.75.75 0 0 1 .75-.75h2.5c.966 0 1.75.784 1.75 1.75v2.5a.75.75 0 0 1-1.5 0v-2.5a.25.25 0 0 0-.25-.25h-2.5a.75.75 0 0 1-.75-.75ZM1.75 10a.75.75 0 0 1 .75.75v2.5c0 .138.112.25.25.25h2.5a.75.75 0 0 1 0 1.5h-2.5A1.75 1.75 0 0 1 1 13.25v-2.5a.75.75 0 0 1 .75-.75Zm12.5 0a.75.75 0 0 1 .75.75v2.5A1.75 1.75 0 0 1 13.25 15h-2.5a.75.75 0 0 1 0-1.5h2.5a.25.25 0 0 0 .25-.25v-2.5a.75.75 0 0 1 .75-.75ZM8 10a2 2 0 1 0 .001-3.999A2 2 0 0 0 8 10Z"
                        ></path><path
                            d="M8 10a2 2 0 1 0 .001-3.999A2 2 0 0 0 8 10Z"
                        ></path></svg
                    >
                </button>
            </div>

            <div class="btn-group me-1">
                <button
                    class="btn btn-outline-secondary btn-xs"
                    onclick={() => onmove(-1)}
                    disabled={first}>↑</button
                >
                <button
                    class="btn btn-outline-secondary btn-xs"
                    onclick={() => onmove(1)}
                    disabled={last}>↓</button
                >
            </div>
            <div class="btn-group">
                <button
                    class="btn btn-outline-secondary btn-xs"
                    onclick={() => ondelete()}>×</button
                >
            </div>
        </div>
    </div>

    {#if source.status == "error"}
        <div class="alert alert-danger p-1 mb-1">Could not load source.</div>
    {:else}
        <div>
            {#if source.type === "datalayer"}
                <MapSourceDatalayer bind:source {manager} />
            {:else if source.type === "shape" || source.type === "vector"}
                <MapSourceShape bind:source {manager} />
            {:else if source.type === "bbox"}
                <!--<BboxControls bind:source />-->
            {/if}
        </div>
    {/if}

    <div>
        <label class="d-flex align-items-center w-50">
            <abbr title="Alpha">A</abbr>:
            <input
                class="ms-1 w-100"
                type="range"
                min="0"
                max="1"
                step="0.01"
                bind:value={source.alpha}
            />
        </label>
    </div>
</div>
