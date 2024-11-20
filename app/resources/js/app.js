/**
 * Svelte components.
 *
 *
 */
import Chart from './components/Chart.svelte';

import $ from 'jquery'
window.jQuery = window.$ = $

import DataTable from 'datatables.net-bs5';
window.DataTable = DataTable;

import * as bootstrap from 'bootstrap'

const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]')
const popoverList = [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl))


/**
 * Leaflet
 *
 */
import L from "leaflet";

// leaflet marker icon are not recognized by Vite automatically.
// This somehow loads the needed images from the package folder and transforms
// the to inline/base64 images.
// See https://github.com/vue-leaflet/Vue2Leaflet/issues/103#issuecomment-2137388444
import markerIconUrl from 'leaflet/dist/images/marker-icon.png';
import markerIconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png';
import markerShadowUrl from 'leaflet/dist/images/marker-shadow.png';
L.Icon.Default.prototype.options.iconUrl = markerIconUrl;
L.Icon.Default.prototype.options.iconRetinaUrl = markerIconRetinaUrl;
L.Icon.Default.prototype.options.shadowUrl = markerShadowUrl;
L.Icon.Default.imagePath = '';

window.L = L;

import "leaflet-fullscreen";
import "leaflet-loading";

/**
 * D3
 *
 */
import * as d3 from './d3/d3.js'; // custom d3 with only needed parts
//import * as d3 from 'd3';
window.d3 = d3;

import { Legend } from './d3/d3.legend.js';
window.Legend = Legend;


import hljs from 'highlight.js/lib/core';
import python from 'highlight.js/lib/languages/python';
hljs.registerLanguage('python', python);

window.hljs = hljs;

/**
 * Own scripts
 *
 */
import "./search";
import { MyMap } from "./map";
window.MyMap  = MyMap;
