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
(<code>{datalayer.key}</code>)
