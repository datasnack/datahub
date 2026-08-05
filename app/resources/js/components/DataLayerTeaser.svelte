<!--
SPDX-FileCopyrightText: 2026 Jonathan Ströbele <mail@jonathanstroebele.de>

SPDX-License-Identifier: AGPL-3.0-only
-->
<script lang="ts">
    import type { DataLayer } from "./DatahubTypes";

    interface Props {
        datalayer: DataLayer;
    }

    let { datalayer }: Props = $props();
</script>

<a href="/datalayers/{datalayer.key}">{datalayer.name}</a>
(<code>{datalayer.key}</code>) | {#if datalayer.is_categorical}
    {datalayer.categorical_type}<code>&lt;{datalayer.value_type}&gt;</code>
{:else}
    <code>{datalayer.value_type}</code>
{/if}
{datalayer.format_suffix}

| <code>{datalayer.shape_types.at(-1)?.key}</code>

| {datalayer.temporal_resolution}
<span class="small text-muted">
    {datalayer.first_time}–{datalayer.last_time}
</span>
