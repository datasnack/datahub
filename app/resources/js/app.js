// SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
//
// SPDX-License-Identifier: AGPL-3.0-only

/**
 * Svelte components.
 *
 *
 */
import Chart from "./components/Chart.svelte";
import Map from "./components/Map.svelte";

import $ from "jquery";
window.jQuery = window.$ = $;

import DataTable from "datatables.net-bs5";
window.DataTable = DataTable;

import * as bootstrap from "bootstrap";


/**
 * D3
 *
 */
import * as d3 from "./d3/d3.js"; // custom d3 with only needed parts
//import * as d3 from 'd3';
window.d3 = d3;

import { Legend } from "./d3/d3.legend.js";
window.Legend = Legend;

import { Swatches } from "./d3/d3.swatches.js";
window.Swatches = Swatches;

import hljs from "highlight.js/lib/core";
import python from "highlight.js/lib/languages/python";
import r from "highlight.js/lib/languages/r";

hljs.registerLanguage("python", python);
hljs.registerLanguage("r", r);

window.hljs = hljs;

/**
 * Own scripts
 *
 */
import "./search";

window.loadPlotly = async function () {
	if (!window.Plotly) {
		window.Plotly = await import("plotly.js-dist");
	}
	return Plotly;
};

import "./copy2clipboard";
