<!--
SPDX-FileCopyrightText: 2026 Jonathan Ströbele <mail@jonathanstroebele.de>

SPDX-License-Identifier: AGPL-3.0-only
-->
<script lang="ts">
    import { onMount } from "svelte";
    import { Calendar, type Options, weeks } from "vanilla-calendar-pro";

    let {
        id,
        value = $bindable(""),
        datalayer,
    }: { id: string; value?: string; datalayer: any } = $props();

    let el: HTMLInputElement | undefined = $state();

    const pad = (n: number) => String(n).padStart(2, "0");

    function getConfig(): Options {
        switch (datalayer.temporal_resolution) {
            case "year":
                const yearToFirstDay = (y: string) => `${y}-01-01`;
                const yearToLastDay = (y: string) => `${y}-12-31`;

                return {
                    dateMin: yearToFirstDay(datalayer.first_time),
                    dateMax: yearToLastDay(datalayer.last_time),
                    type: "year",
                    onClickYear(self) {
                        const { selectedYear } = self.context;
                        value = `${selectedYear}`;
                        self.hide();
                    },
                };

            case "month":
                const toFirstDay = (ym: string) => `${ym}-01`;
                const toLastDay = (ym: string) => {
                    const [y, m] = ym.split("-").map(Number);
                    const d = new Date(y, m, 0).getDate(); // day 0 of next month = last day of this month
                    return `${ym}-${String(d).padStart(2, "0")}`;
                };

                // convert yyyy-mm to yyyy-mm-dd string
                // dateMin/dateMax needs to be in yyyy-md-dd format
                const min = toFirstDay(datalayer.first_time);
                const max = toLastDay(datalayer.last_time);

                return {
                    type: "month",
                    dateMin: min,
                    dateMax: max,
                    onClickMonth(self) {
                        const { selectedYear, selectedMonth } = self.context;
                        value = `${selectedYear}-${pad(selectedMonth + 1)}`;
                        self.hide();
                    },
                };
            case "week": {
                // --- ISO week helpers (weeks start Monday, week 1 = the week containing Jan 4) ---
                const ymd = (d: Date) =>
                    `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;

                // "2025-W03" -> Date of that week's Monday
                const isoWeekMonday = (yw: string) => {
                    const [y, w] = yw.split("-W").map(Number);
                    const jan4 = new Date(y, 0, 4);
                    const monday = new Date(
                        y,
                        0,
                        4 - ((jan4.getDay() + 6) % 7),
                    ); // Monday of week 1
                    monday.setDate(monday.getDate() + (w - 1) * 7);
                    return monday;
                };
                const toWeekStart = (yw: string) => ymd(isoWeekMonday(yw));
                const toWeekEnd = (yw: string) => {
                    const d = isoWeekMonday(yw);
                    d.setDate(d.getDate() + 6); // Sunday
                    return ymd(d);
                };

                // "2024-12-30" -> "2025-W01" (uses the ISO week-year, not the calendar year)
                const toIsoWeek = (dateStr: string) => {
                    const [y, m, d] = dateStr.split("-").map(Number);
                    const t = new Date(y, m - 1, d);
                    t.setDate(t.getDate() + 3 - ((t.getDay() + 6) % 7)); // Thursday of this week
                    const weekYear = t.getFullYear();
                    const dayOfYear = Math.round(
                        (t.getTime() - new Date(weekYear, 0, 1).getTime()) /
                            86400000,
                    );
                    return `${weekYear}-W${pad(Math.floor(dayOfYear / 7) + 1)}`;
                };

                const min = toWeekStart(datalayer.first_time); // Monday of first week
                const max = toWeekEnd(datalayer.last_time); // Sunday of last week

                return {
                    extensions: [weeks],
                    enableWeekNumbers: true,
                    firstWeekday: 1, // Monday
                    dateMin: min,
                    dateMax: max,
                    styles: { calendar: "vc vc-week-picker" }, // keep vc, the setting replaces existing values

                    onClickDate(self) {
                        const d = self.context.selectedDates[0];
                        if (d) {
                            value = toIsoWeek(d);
                            self.hide();
                        }
                    },
                    // optional: let users click the week number itself
                    onClickWeekNumber(self, _week, _year, dateEls) {
                        const week = toIsoWeek(dateEls[0].dataset.vcDate!);
                        const monday = toWeekStart(week);
                        // min is a Monday and max a Sunday, so the week is valid if its Monday falls in [min, max]
                        if (monday < min || monday > max) return;
                        value = week;
                        self.hide();
                    },
                };
            }
            default: // date
                return {
                    dateMin: datalayer.first_time,
                    dateMax: datalayer.last_time,
                    displayDateMin: datalayer.first_time,
                    displayDateMax: datalayer.last_time,

                    onClickDate(self) {
                        const d = self.context.selectedDates[0];
                        if (d) {
                            value = d;
                            self.hide();
                        }
                    },
                };
        }
    }

    onMount(() => {
        if (!el) return; // year → plain select, no calendar
        const calendar = new Calendar(el, { inputMode: true, ...getConfig() });
        calendar.init();
        return () => calendar.destroy();
    });

    const placeholders: Record<string, string> = {
        month: "yyyy-mm",
        week: "yyyy-Www",
        date: "yyyy-mm-dd",
    };
</script>

{#if datalayer.temporal_resolution === "year"}
    <select {id} class="form-select form-select-sm" bind:value>
        {#each [...datalayer.available_years].reverse() as year}
            <option value={year}>{year}</option>
        {/each}
    </select>
{:else}
    <input
        bind:this={el}
        {id}
        type="text"
        class="form-control form-control-sm"
        placeholder={placeholders[datalayer.temporal_resolution]}
        bind:value
    />
{/if}
