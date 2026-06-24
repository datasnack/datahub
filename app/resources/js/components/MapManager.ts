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
import { extent } from "d3-array";
import type { DataLayer, MapSource } from "./DatahubTypes";
import { buildScale } from "./legend";


export class MapManager {

    #map: MapLibreMap;

    #ready: Promise<MapLibreMap>;

    // bookkeeping: source id -> its layer ids, in top-to-bottom order
    #added = new Map<string, string[]>();

    // geometry payloads, owned by the manager (NOT reactive on purpose:
    // FeatureCollections are large and we don't want Svelte deep-proxying them).
    // A source is "present on the map" iff we hold geometry for it here.
    #geometry = new Map<string, GeoJSON.FeatureCollection>();

    // in-flight fetches, so a newer load can supersede an older one
    #controllers = new Map<string, AbortController>();

    // per-source teardown for popup/cursor event handlers, so we can remove
    // exactly the listeners we added (map.removeLayer does NOT remove them).
    #popupCleanups = new Map<string, () => void>();

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





    async fetchGeometry(query: Record<string, string>, signal?: AbortSignal): Promise<GeoJSON> {
        const qs = new URLSearchParams(query).toString();
        const res = await fetch(`/api/shapes/geometry?${qs}`, { signal });
        if (!res.ok) throw new Error(`Failed to fetch geometry: ${res.status}`);
        return res.json();
    }

    async fetchBBox(query: Record<string, string>, signal?: AbortSignal): Promise<object> {
        const qs = new URLSearchParams(query).toString();
        const res = await fetch(`/api/shapes/bbox/?${qs}`, { signal });
        if (!res.ok) throw new Error(`Failed to fetch BBox: ${res.status}`);
        return res.json();
    }

    async fetchDatalayer(datalayer_key: string): Promise<DataLayer> {
        const res = await fetch("/api/datalayers/meta/?datalayer_key=" + datalayer_key);
        if (!res.ok) throw new Error(`Failed to fetch Data Layer: ${res.status} `);
        const json = await res.json();
        return json.datalayer;
    }

    async fetchDatalayerData(query: Record<string, string>, signal?: AbortSignal): Promise<any> {
        const qs = new URLSearchParams(Object.entries(query).filter(([_, value]) => value != null)).toString();

        const res = await fetch(`/api/datalayers/data/?${qs}`, { signal });
        if (!res.ok) throw new Error(`Failed to fetch Data Layer data: ${res.status} `);
        const json = await res.json();
        return json;
    }

    async fetchDataLayerVector(query: Record<string, string>, signal?: AbortSignal): Promise<object> {
        const qs = new URLSearchParams(Object.entries(query).filter(([_, value]) => value != null)).toString();
        const res = await fetch(`/api/datalayers/vector/?${qs}`, { signal });
        if (!res.ok) throw new Error(`Failed to fetch Vector data for Data Layer: ${res.status} `);
        return res.json();
    }

    setData(id: string, data: GeoJSON.FeatureCollection): void {
        const src = this.#map.getSource(id) as maplibregl.GeoJSONSource | undefined;
        src?.setData(data);
    }

    // ---- geometry store ---------------------------------------------------

    hasGeometry(id: string): boolean {
        return this.#geometry.has(id);
    }

    getGeometry(id: string): GeoJSON.FeatureCollection | undefined {
        return this.#geometry.get(id);
    }

    /**
     * Fetch geometry (+ datalayer data) for a source and store it.
     *
     * Pure imperative IO: it does NOT touch reactive state. It returns a patch
     * of derived fields for the caller to merge back onto the reactive source
     * (status, extent, categorical info, ...). Never throws – on failure it
     * returns a patch describing the failure, on supersede it returns {}.
     */
    async loadSource(source: MapSource): Promise<Partial<MapSource>> {
        // a newer load for the same id wins
        this.#controllers.get(source.id)?.abort();
        const ac = new AbortController();
        this.#controllers.set(source.id, ac);

        try {
            const geom = await this.#fetchGeometryFor(source, ac.signal);

            let patch: Partial<MapSource> = {};
            if (source.type === "datalayer") {
                const data = await this.fetchDatalayerData(source.query, ac.signal);
                patch = this.#applyDatalayerData(source, geom, data);
            }

            this.#geometry.set(source.id, geom);
            return { ...patch, status: "ready" };
        } catch (e: any) {
            if (e?.name === "AbortError") return {}; // superseded – leave state untouched
            console.error("Failed to load source", source.id, e);
            return { status: "error" };
        } finally {
            if (this.#controllers.get(source.id) === ac) {
                this.#controllers.delete(source.id);
            }
        }
    }

    /**
     * Apply a datalayer data payload to a source's already-loaded geometry and
     * push it live to the map. Used by external/power-user updates where the
     * caller supplies the data instead of it being fetched.
     *
     * Returns a patch of derived fields to merge onto the reactive source.
     */
    applyDatalayerData(source: MapSource, data: any): Partial<MapSource> {
        const geom = this.#geometry.get(source.id);
        if (!geom) {
            throw new Error(`No geometry loaded for source ${source.id}`);
        }
        const patch = this.#applyDatalayerData(source, geom, data);
        this.setData(source.id, geom); // live update if the source is on the map
        return patch;
    }

    /** Forget a source entirely: abort its fetch and drop its geometry. */
    dropSource(id: string): void {
        this.#controllers.get(id)?.abort();
        this.#controllers.delete(id);
        this.#geometry.delete(id);
    }

    #fetchGeometryFor(source: MapSource, signal: AbortSignal): Promise<any> {
        switch (source.type) {
            case "bbox":
                return this.fetchBBox(source.query, signal);
            case "vector":
                return this.fetchDataLayerVector(source.query, signal);
            default:
                return this.fetchGeometry(source.query, signal);
        }
    }

    /**
     * Mutates `geom`'s feature properties (value/formatted/color/alpha) from a
     * datalayer data payload and returns the derived reactive fields.
     */
    #applyDatalayerData(
        source: MapSource,
        geom: GeoJSON.FeatureCollection,
        data: any,
    ): Partial<MapSource> {
        const isCategorical: boolean = data.is_categorical;
        const categoricalValues: string[] = data.categorical_values;
        const categoricalLabels: string[] = data.categorical_labels;
        const isPercentage = data.value_type === "percentage";

        const value_map = new Map(data.data.map((d: any) => [d.dh_shape_id, d.value]));
        const formatted_map = new Map(data.data.map((d: any) => [d.dh_shape_id, d.formatted]));

        const actualExtent = extent(value_map.values() as Iterable<number>) as [number, number];
        const nextExtent = source.extent ?? actualExtent;

        const color = buildScale(
            isCategorical,
            source.cmap as any,
            nextExtent,
            categoricalValues as any,
        );

        for (const feature of geom.features) {
            const dh_shape_id = feature.properties!.dh_shape_id;
            const value = value_map.has(dh_shape_id) ? value_map.get(dh_shape_id) : null;
            const formatted = formatted_map.has(dh_shape_id) ? formatted_map.get(dh_shape_id) : null;

            feature.properties!.alpha = 1;
            if (value === null || value === undefined) {
                feature.properties!.value = null;
                feature.properties!.formatted = null;
                feature.properties!.color = "rgba(0, 0, 0, 0.1)";
            } else {
                feature.properties!.value = value;
                feature.properties!.formatted = formatted;
                feature.properties!.color = color(value as any);
            }
        }

        return {
            isCategorical,
            categoricalValues,
            categoricalLabels,
            isPercentage,
            actualExtent,
            extent: nextExtent,
            name: source.name ?? data.name,
        };
    }

    /** Recolor a datalayer source from a d3 scale and push it live. */
    setColor(id: string, color: (v: number) => string) {
        const fc = this.#geometry.get(id);
        if (!fc) return;
        for (const feature of fc.features) {
            const value = feature.properties?.value;
            if (value !== null && value !== undefined) {
                feature.properties!.color = color(value);
            }
        }
        this.setData(id, fc);
    }



    reconcile(desired: MapSource[]): void {
        const map = this.#map;
        const desiredIds = new Set(desired.map((d) => d.id));

        // 0. forget geometry/fetches for sources that no longer exist at all
        for (const id of [...this.#geometry.keys()]) {
            if (!desiredIds.has(id)) this.dropSource(id);
        }

        // a source is shown on the map iff we hold geometry for it.
        // NOTE: this is deliberately decoupled from `status`. A source that is
        // re-loading ("loading") but already has geometry stays on the map, so
        // we never tear down + rebuild its layers/popups on a refresh.
        const present = new Map(
            desired
                .filter((d) => this.#geometry.has(d.id))
                .map((d) => [d.id, d] as const),
        );

        // 1. remove sources that should no longer be displayed
        for (const [id, layerIds] of this.#added) {
            if (!present.has(id)) {
                this.#popupCleanups.get(id)?.(); // remove click/hover listeners
                this.#popupCleanups.delete(id);
                for (const l of layerIds) if (map.getLayer(l)) map.removeLayer(l);
                if (map.getSource(id)) map.removeSource(id);
                this.#added.delete(id);
            }
        }

        // 2. add newly-present sources + their layers (+ popups, once)
        for (const d of present.values()) {
            if (this.#added.has(d.id)) continue;
            const data = this.#geometry.get(d.id);
            if (!data) continue;
            map.addSource(d.id, { type: "geojson", data });
            const layers = this.#buildLayers(d); // top-to-bottom
            for (const layer of layers) map.addLayer(layer);
            this.#added.set(d.id, layers.map((l) => l.id));

            this.#attachPopup(d);

            if (d.fitBounds) {
                this.fitToSourceBounds(d.id);
            }
        }

        // 3. visibility
        for (const d of desired) {
            const ids = this.#added.get(d.id);
            if (!ids) continue;
            const v = d.visible ? "visible" : "none";
            for (const l of ids) map.setLayoutProperty(l, "visibility", v);
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
        // guard: never attach twice for the same source
        if (this.#popupCleanups.has(d.id)) return;

        const popupLayerMapping: Record<string, string[]> = {
            "shape": ["-fill"],
            "datalayer": ["-fill"],
            "bbox": ["-markers"],
            "vector": ["-point", "-linestring", "-polygon"],
        };

        if (!popupLayerMapping.hasOwnProperty(d.type)) return;

        const offs: Array<() => void> = [];

        popupLayerMapping[d.type].forEach((suffix) => {
            const layerId = `${d.id}${suffix}`;

            const onClick = (e: any) => {
                const coordinates = e.lngLat;
                const feature = e.features[0];
                const popupFnc = this.getPopupContent;

                new maplibregl.Popup()
                    .setLngLat(coordinates)
                    .setHTML(popupFnc(feature, (d.type === "vector")))
                    .addTo(this.#map);
            };
            const onEnter = () => {
                this.#map.getCanvas().style.cursor = "pointer";
            };
            const onLeave = () => {
                this.#map.getCanvas().style.cursor = "";
            };

            this.#map.on("click", layerId, onClick);
            this.#map.on("mouseenter", layerId, onEnter);
            this.#map.on("mouseleave", layerId, onLeave);

            offs.push(() => {
                this.#map.off("click", layerId, onClick);
                this.#map.off("mouseenter", layerId, onEnter);
                this.#map.off("mouseleave", layerId, onLeave);
            });
        });

        this.#popupCleanups.set(d.id, () => offs.forEach((off) => off()));
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
