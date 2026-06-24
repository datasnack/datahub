// SPDX-FileCopyrightText: 2026 Jonathan Ströbele <mail@jonathanstroebele.de>
//
// SPDX-License-Identifier: AGPL-3.0-only

import type { Map as MapLibreMap, IControl } from "maplibre-gl";

import maplibregl, {
    type StyleSpecification,
    type LayerSpecification,
} from 'maplibre-gl';

import StyleControl from "../maplibre/StyleControl";
import ScreenshotControl from "../maplibre/ScreenshotControl";
import FullScreenControl from "../maplibre/FullScreenControl";

import { Protocol } from "pmtiles";
import type { DataLayer, MapSource } from "./DatahubTypes";


export class MapManager {

    #map: MapLibreMap;

    #ready: Promise<MapLibreMap>;

    // bookkeeping: source id -> its layer ids, in top-to-bottom order
    #added = new Map<string, string[]>();

    private sources: MapSource[] = [];

    private sourceIdCounter: number = 0;

    private layerControlNodeId: string | null = null;
    private layerControlNode: HTMLElement | null = null;

    constructor(container: HTMLElement, options) {
        const protocol = new Protocol();
        maplibregl.addProtocol("pmtiles", protocol.tile);

        const mapStyles = [
            /*{
                title: "Local",
                code: "datahub",
                url: "http://localhost:8000/static/map/style.json",
                image: "/static/map/openfreemap-liberty.png",
            },*/
            {
                title: "OpenStreetMap",
                code: "openfreemap-liberty",
                url: "https://tiles.openfreemap.org/styles/liberty",
                image: "/static/map/openfreemap-liberty.png",
            },
            {
                title: "Satellite",
                code: "eox-cloudless",
                url: "/static/map/eox_cloudless.json",
                image: "/static/map/eox-cloudless.png",
            },
        ];

        if (options) {
            if (options.layerControlNodeId) {
                if (options.layerControlNodeId instanceof HTMLElement) {
                    this.layerControlNode = options.layerControlNodeId
                } else {
                    this.layerControlNode = this.layerControlNodeId
                        ? document.getElementById(this.layerControlNodeId)
                        : null;

                }
            }
        }

        this.#map = new maplibregl.Map({
            container: container,
            style: mapStyles[0].url,
            center: [DATAHUB.CENTER_X, DATAHUB.CENTER_Y], // [lng, lat]
            zoom: DATAHUB.CENTER_ZOOM,
        });

        this.#map.on("error", (e) => {
            console.error("MapLibre error:", e.error);
        });

        this.#map.addControl(new FullScreenControl(), "top-right");

        // Add zoom and rotation controls to the map.
        this.#map.addControl(
            new maplibregl.NavigationControl({
                visualizePitch: true,
                visualizeRoll: true,
                showZoom: true,
                showCompass: true,
            }),
        );

        // Scale
        this.#map.addControl(
            new maplibregl.ScaleControl({
                maxWidth: 80,
                unit: "metric",
            }),
        );

        this.#map.addControl(new ScreenshotControl(), "top-right");

        const styleControl = new StyleControl(mapStyles);
        this.#map.addControl(styleControl, "bottom-right");


        this.#ready = new Promise((resolve) => {
            if (this.#map.loaded()) resolve(this.#map);
            else this.#map.once('load', () => resolve(this.#map));
        });
    }

    get ready(): Promise<MapLibreMap> {
        return this.#ready;
    }

    getMap(): MapLibreMap { return this.#map; }

    getMapLibre() { return maplibregl; }


    getNextSourceId(): number {
        return this.sourceIdCounter++;
    }

    getNextSourceIdString(): string {
        return `dh-${this.getNextSourceId()}-source`;
    }

    async fitToSourceBounds(sourceId: string) {
        const bounds = await this.#map.getSource(sourceId).getBounds();
        this.#map.fitBounds(bounds, {
            linear: true,
            padding: 42,
        });
    }

    // Function to get popup content for a feature
    getPopupContent(feature, show_all_as_table = false) {
        const props = feature.properties;
        let content = '<div class="">';

        // Customize based on your GeoJSON properties
        const name = props.shape_name ?? props.name;
        if (name) {
            content += `<h6 class="mb-0">${name}</h6>`;
        }

        // if shape
        if (props.shape_key) {
            content += `<div class="small text-muted mb-1"><code>${props.shape_key}</code> | ${props.type_key} | <a href="${props.url}"">Details</a></div>`;
        }

        // if datalayer choropleth
        if (Object.hasOwn(props, 'value')) {

            content += '<hr class="my-1" />';

            let color = "";
            if (props.color) {
                color = `<span class="d-inline-block" style="border: 1px solid #000; width: 1em; height: 1em; border-radius: 50%; background-color: ${props.color}"></span>`;
            }
            content += `<div class="">Value: ${props.formatted} ${color}</div>`;
            content += `<div class="text-muted small">Raw: ${props.value}</div>`;
        }

        // Add other properties
        let values = {};
        if (show_all_as_table) {
            values = props;
        } else {
            if (props.values) {
                // MapLibre doesn't parse nested properties
                // https://github.com/maplibre/maplibre-gl-js/issues/1325
                if (typeof props.values === "string") {
                    try {
                        values = JSON.parse(props.values);
                    } catch (e) {
                        console.warn(
                            "Invalid JSON feature properties.values:",
                            props.values,
                        );
                        values = {};
                    }
                } else {
                    values = props.values;
                }
            }
        }

        if (values) {
            var table = "";
            Object.keys(values).forEach(function (key) {
                if (key == "name") {
                    return;
                }
                const value = values[key];

                // ignore empty values (not all properties are set on each feature)
                // this reduces the visual space needed for the popup!
                if (value == null) {
                    return;
                }
                table += `<tr><th><code>${key}</code></th><td>${value}</td>`;
            });
            content += `<div class="overflow-y-scroll" style="max-height:200px"><table class="table table-sm"><tbody>${table}</tbody></table></div>`;
            content += "</div>";
        }
        return content;
    }

    getMapLibreLayers() {
        console.log(this.#map.getStyle());
    }





    async fetchGeometry(query: Record<string, string>): Promise<GeoJSON> {
        const qs = new URLSearchParams(query).toString();
        const res = await fetch(`/api/shapes/geometry?${qs}`);
        if (!res.ok) throw new Error(`Failed to fetch geometry: ${res.status}`);
        return res.json();
    }

    async fetchBBox(query: Record<string, string>): Promise<object> {
        const qs = new URLSearchParams(query).toString();
        const res = await fetch(`/api/shapes/bbox?${qs}`);
        if (!res.ok) throw new Error(`Failed to fetch BBox: ${res.status}`);
        return res.json();
    }

    async fetchDatalayer(datalayer_key: string): Promise<DataLayer> {
        const res = await fetch("/api/datalayers/meta?datalayer_key=" + datalayer_key);
        if (!res.ok) throw new Error(`Failed to fetch Data Layer: ${res.status} `);
        const json = await res.json();
        return json.datalayer;
    }

    async fetchDatalayerData(query: Record<string, string>): Promise<any> {
        const qs = new URLSearchParams(Object.entries(query).filter(([_, value]) => value != null)).toString();

        const res = await fetch(`/api/datalayers/data?${qs}`);
        if (!res.ok) throw new Error(`Failed to fetch Data Layer data: ${res.status} `);
        const json = await res.json();
        return json;
    }

    async fetchDataLayerVector(query: Record<string, string>): Promise<object> {
        const qs = new URLSearchParams(Object.entries(query).filter(([_, value]) => value != null)).toString();
        const res = await fetch(`/api/datalayers/vector?${qs}`);
        if (!res.ok) throw new Error(`Failed to fetch Vector data for Data Layer: ${res.status} `);
        return res.json();
    }

    setData(id: string, data: GeoJSON.FeatureCollection): void {
        const src = this.#map.getSource(id) as maplibregl.GeoJSONSource | undefined;
        src?.setData(data);
    }


    setColor(id: string, color) {
        const mapSource = this.#map.getSource(id) as maplibregl.GeoJSONSource | undefined

        if (mapSource) {
            const data = mapSource._data; // Private MapLibre API, not update save!

            data.geojson.features.forEach((feature) => {
                const value = feature.properties.value;
                if (value !== null) {
                    feature.properties.color = color(value);
                }
            });
            mapSource.setData(data.geojson);
        }

    }



    reconcile(desired: MapSource[], geometry: Map<string, GeoJSON.FeatureCollection>): void {
        const map = this.#map;
        const wanted = new Map(desired.filter((d) => d.ready).map((d) => [d.id, d] as const));

        // 1. remove sources that are gone (layers first, then the source)
        for (const [id, layerIds] of this.#added) {
            if (!wanted.has(id)) {
                for (const l of layerIds) if (map.getLayer(l)) map.removeLayer(l);
                if (map.getSource(id)) map.removeSource(id);
                this.#added.delete(id);
            }
        }

        // 2. add newly-ready sources + their layers
        for (const d of wanted.values()) {
            if (this.#added.has(d.id)) continue;
            const data = geometry.get(d.id);
            if (!data) continue; // ready but payload not in the store yet — skip defensively
            map.addSource(d.id, { type: 'geojson', data });
            const layers = this.#buildLayers(d); // top-to-bottom
            for (const layer of layers) map.addLayer(layer);
            this.#added.set(d.id, layers.map((l) => l.id));

            // attach popup
            this.#attachPopup(d);

            // fit to bounds?
            if (d.fitBounds) {
                this.fitToSourceBounds(d.id);
            }

        }

        // 3. visibility
        for (const d of desired) {
            const ids = this.#added.get(d.id);
            if (!ids) continue;
            const v = d.visible ? 'visible' : 'none';
            for (const l of ids) map.setLayoutProperty(l, 'visibility', v);
        }

        // update color/opacity
        for (const s of desired) this.#applyStyle(s);

        // 4. THE order authority — flatten items (display order) → layer ids, then chain moveLayer
        const order = desired
            .filter((d) => this.#added.has(d.id))
            .flatMap((d) => this.#added.get(d.id)!);
        let beforeId: string | undefined;
        for (const layerId of order) {
            map.moveLayer(layerId, beforeId); // places layerId just below beforeId
            beforeId = layerId;               // first call (undefined) = top
        }



    }

    #attachPopup(d: MapSource): void {

        const popupLayerMapping: Record<string, string[]> = {
            "shape": ["-fill"],
            "datalayer": ["-fill"],
            "bbox": ["-markers"],
            "vector": ["-point", "-linestring", "-polygon"],
        }

        if (popupLayerMapping.hasOwnProperty(d.type)) {

            popupLayerMapping[d.type].forEach((suffix) => {
                const layerId = `${d.id}${suffix}`;

                this.#map.on("click", layerId, (e) => {
                    const coordinates = e.lngLat;
                    const feature = e.features[0];

                    const popupFnc = this.getPopupContent;

                    new maplibregl.Popup()
                        .setLngLat(coordinates)
                        .setHTML(popupFnc(feature, (d.type == "vector")))
                        .addTo(this.#map);
                });

                // Change cursor on hover
                this.#map.on("mouseenter", layerId, () => {
                    this.#map.getCanvas().style.cursor = "pointer";
                });

                this.#map.on("mouseleave", layerId, () => {
                    this.#map.getCanvas().style.cursor = "";
                });
            });
        }
    }


    /** The one place that knows about source types. Returns layers top-to-bottom. */
    #buildLayers(d: MapSource): LayerSpecification[] {
        switch (d.type) {
            case 'shape':
                return [
                    {
                        id: `${d.id}-line`, type: 'line', source: d.id,
                        paint: {
                            'line-color': d.color, 'line-width': [
                                "interpolate",
                                ["linear"],
                                ["zoom"],
                                3,
                                1, // very zoomed-out → thin
                                6,
                                1.5,
                                8,
                                2,
                                10,
                                3,
                            ],
                        }
                    },
                    {
                        id: `${d.id}-fill`, type: 'fill', source: d.id,
                        paint: { 'fill-color': d.color, 'fill-opacity': d.alpha }
                    },
                ];
            case 'bbox':
                return [
                    {
                        id: `${d.id}-markers`, type: 'circle', source: d.id,
                        filter: ["==", "$type", "Point"],
                        paint: {
                            "circle-radius": [
                                "interpolate",
                                ["linear"],
                                ["zoom"],
                                0,
                                0.5,
                                3,
                                3.5,
                                6,
                                6,
                            ],

                            "circle-color": '#5385f8',
                            "circle-stroke-width": [
                                "interpolate",
                                ["linear"],
                                ["zoom"],
                                0,
                                0.5,
                                3,
                                1,
                                6,
                                2,
                            ],
                            "circle-stroke-color": "#ffffff",
                        },
                    },
                    {
                        id: `${d.id}-outline`, type: 'line', source: d.id,
                        paint: {
                            "line-color": '#5385f8',
                            "line-dasharray": [2, 2],
                            "line-width": [
                                "interpolate",
                                ["linear"],
                                ["zoom"],
                                3,
                                2, // very zoomed-out → thin
                                6,
                                2.5,
                                8,
                                3,
                                10,
                                4,
                            ],
                            "line-opacity": 1,
                        }
                    },
                ];
            case 'datalayer':
                return [
                    {
                        id: `${d.id}-line`, type: 'line', source: d.id,
                        paint: {
                            "line-color": "#000",
                            'line-width': [
                                "interpolate",
                                ["linear"],
                                ["zoom"],
                                3, // 3 is very zoomed-out → thin
                                0.125, // this is the width for zoom=3
                                6,
                                0.5,
                                8,
                                0.5,
                                10,
                                1,
                            ],
                            "line-opacity": 1,
                        }
                    },
                    {
                        id: `${d.id}-fill`, type: 'fill', source: d.id,
                        paint: {
                            "fill-color": ["get", "color"],
                            "fill-opacity": ["get", "alpha"],
                        }
                    },
                ];

            case 'vector':
                let layers: LayerSpecification[] = [];

                const types = ["Point", "LineString", "Polygon"];
                const layerTypes = {
                    Point: {
                        type: "circle",
                        paint: {
                            "circle-radius": [
                                "interpolate",
                                ["linear"],
                                ["zoom"],
                                0,
                                0.5,
                                3,
                                3.5,
                                6,
                                6,
                            ],

                            "circle-color": ["get", "color"],
                            "circle-stroke-width": [
                                "interpolate",
                                ["linear"],
                                ["zoom"],
                                0,
                                0.5,
                                3,
                                1,
                                6,
                                2,
                            ],
                            "circle-stroke-color": "#ffffff",
                        },
                    },
                    LineString: {
                        type: "line",
                        paint: { "line-color": ["get", "color"], "line-width": 3 },
                    },
                    Polygon: {
                        type: "fill",
                        paint: { "fill-color": ["get", "color"], "fill-opacity": 0.4 },
                    },
                };

                types.forEach((t) => {
                    const layerId = `${d.id}-${t.toLocaleLowerCase()}`;
                    layers.push(
                        {
                            id: layerId,
                            source: d.id,
                            filter: ["==", "$type", t],
                            ...layerTypes[t],
                        });

                })

                return layers;
        }
        throw new Error(`No layer styles for source of type ${d.type} `)
    }

    // apply current visibility + paint to a source's existing layers (no-op if not added)
    #applyStyle(s: MapSource): void {
        const map = this.#map;
        const ids = this.#added.get(s.id);
        if (!ids) return;
        const visibility = s.visible ? 'visible' : 'none';
        const paint = this.#paintFor(s);
        for (const layerId of ids) {
            if (!map.getLayer(layerId)) continue;
            map.setLayoutProperty(layerId, 'visibility', visibility);
            for (const [prop, value] of Object.entries(paint[layerId] ?? {})) {
                map.setPaintProperty(layerId, prop, value);
            }
        }
    }

    // style — paint props per layer id, recomputed from current state
    #paintFor(s: MapSource): Record<string, Record<string, unknown>> {
        switch (s.type) {
            case 'shape': return {
                [`${s.id}-line`]: { 'line-color': s.color, 'line-width': 2 },
                [`${s.id}-fill`]: { 'fill-color': s.color, 'fill-opacity': s.alpha },
            };
            //case 'bbox': return { [`${s.id}-outline`]: { 'line-color': '#ff3333', 'line-width': 2 } };
            case 'datalayer': return { [`${s.id}-fill`]: { 'fill-opacity': s.alpha } };
            case 'vector': return {
                [`${s.id}-linestring`]: { 'line-color': s.color }, // , 'line-opacity': s.alpha
                [`${s.id}-point`]: { 'circle-color': s.color, 'circle-opacity': s.alpha },
                [`${s.id}-polygon`]: { 'fill-color': s.color, 'fill-opacity': s.alpha },


                //[`${s.id}-fill`]: { 'fill-color': s.color, 'fill-opacity': s.alpha },
            };
        }
        return {};
        throw new Error(`No layer styles for source of type ${s.type} `)
    }

    destroy(): void {
        this.#map.remove();
    }

}
