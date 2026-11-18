<!--
SPDX-FileCopyrightText: 2026 Jonathan Ströbele <mail@jonathanstroebele.de>

SPDX-License-Identifier: AGPL-3.0-only
-->
<script lang="ts">
    import { onMount } from "svelte";

    import type { MapSource as TMapSource, DataLayer } from "./DatahubTypes";
    import { MapManager } from "./MapManager";

    let {
        source = $bindable(),
        manager,
    }: { source: TMapSource; manager: MapManager } = $props();

    onMount(async () => {});
</script>

<input
    class="form-control form-control-sm form-control-color"
    style="border-radius: 50%; width: 1em; height: 1em; display: block; padding: 0; min-height: auto;"
    type="color"
    bind:value={source.color}
/>
