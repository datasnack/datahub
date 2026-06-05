import maplibregl from "maplibre-gl";
import type { Map as MapLibreMap, IControl } from "maplibre-gl";
import { Protocol } from "pmtiles";

import StyleControl from "../maplibre/StyleControl";
import ScreenshotControl from "../maplibre/ScreenshotControl";
import FullScreenControl from "../maplibre/FullScreenControl";

import { SvelteMapControl } from "./SvelteMapControl";

import MapBBoxControl from "./MapBBoxControl.svelte";
import MapDatalayerControl from "./MapDatalayerControl.svelte"
import MapVectorControl from "./MapVectorControl.svelte"
import MapShapeControl from "./MapShapeControl.svelte"

import type { DataLayer, UserSourceInput, MapSource, DatalayerMapSource, VectorMapSource } from "./DatahubTypes";
import { SourceType } from "./DatahubTypes";


export class MapManager {

    private map: MapLibreMap;

    private sources: MapSource[] = [];

    private sourceIdCounter: number = 0;

    private layerControlNodeId: string | null = null;

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
                this.layerControlNodeId = options.layerControlNodeId;
            }
        }

        this.map = new maplibregl.Map({
            container: container,
            style: mapStyles[0].url,
            center: [DATAHUB.CENTER_X, DATAHUB.CENTER_Y], // [lng, lat]
            zoom: DATAHUB.CENTER_ZOOM,
        });

        this.map.on("error", (e) => {
            console.error("MapLibre error:", e.error);
        });

        this.map.addControl(new FullScreenControl(), "top-right");

        // Add zoom and rotation controls to the map.
        this.map.addControl(
            new maplibregl.NavigationControl({
                visualizePitch: true,
                visualizeRoll: true,
                showZoom: true,
                showCompass: true,
            }),
        );

        // Scale
        this.map.addControl(
            new maplibregl.ScaleControl({
                maxWidth: 80,
                unit: "metric",
            }),
        );

        this.map.addControl(new ScreenshotControl(), "top-right");

        const styleControl = new StyleControl(mapStyles);
        this.map.addControl(styleControl, "bottom-right");
    }

    getMap(): MapLibreMap { return this.map; }

    getMapLibre() { return maplibregl; }


    getNextSourceId(): number {
        return this.sourceIdCounter++;
    }

    async fitToSourceBounds(sourceId: string) {
        const bounds = await this.map.getSource(sourceId).getBounds();
        this.map.fitBounds(bounds, {
            linear: true,
            padding: 42,
        });
    }

    // Function to get popup content for a feature
    getPopupContent(feature, show_all_as_table = false) {
        const props = feature.properties;
        let content = '<div class="">';

        // Customize based on your GeoJSON properties
        if (props.shape_name) {
            content += `<h5 class="mb-0">${props.shape_name}</h5>`;
        }

        if (props.type_key) {
            content += `<div class="small text-muted mb-1">${props.type_key}</div>`;
        }

        if (props.value) {
            content += `<div class="">Value: ${props.value}</div>`;
        }

        if (props.url) {
            content += `<a href="${props.url}" class="">Details</a>`;
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



    /****
     *
     * Add a new source to the map.
     */
    async loadSource(input: UserSourceInput) {

        const id = input.id ?? `dh-${input.type}-${this.getNextSourceId()}-source`;
        let ctrl: IControl;

        if (input.type == SourceType.Datalayer) {


            // fetch Data Layer metadata
            //const datalayer = input.datalayer ?? await this.fetchDatalayer(input.query.datalayer_key);
            const datalayer = input.datalayer ?? null;

            // Fetch required geometry
            //const geometry = input.geometry ?? await this.fetchGeometry(input.query);
            const geometry = input.geometry ?? null;
            // Fetch data
            const value_map = input.value_map ?? null;

            const completedSource: DatalayerMapSource = {
                id: id,
                type: SourceType.Datalayer,
                query: input.query,
                visible: input.visible ?? true,
                geometry: geometry,
                name: input.name ?? datalayer.name,
                showQueryLabel: input.showQueryLabel ?? true,
                alpha: input.alpha ?? 1,
                showControls: input.showControls ?? true,
                fitBounds: input.fitBounds ?? false,
                mode: input.mode ?? "min_max",
                cmap: input.cmap ?? "YlGnBu",
                datalayer: datalayer,
                value_map: value_map,
                extent: input.extent ?? null,
                getPopupContent: input.getPopupContent ?? null,
            };

            ctrl = new SvelteMapControl(MapDatalayerControl, { source: completedSource, datalayer: datalayer, manager: this });
        }


        if (input.type == SourceType.Vector) {
            //this.addShape(source);

            // Fetch required geometry
            //const geometry = await this.fetchDataLayerVector(input.query.datalayer_key);
            const completedSource: VectorMapSource = {
                id: id,
                type: SourceType.Vector,
                query: input.query,
                visible: input.visible ?? true,
                geometry: input.geometry ?? null,
                name: input.name ?? "Vector data",
                alpha: input.alpha ?? 1,
                color: input.color ?? '#5385f8',
                showControls: input.showControls ?? true,
                fitBounds: input.fitBounds ?? false,
                getPopupContent: input.getPopupContent ?? null,
            };

            ctrl = new SvelteMapControl(MapVectorControl, { source: completedSource, manager: this });
        }


        if (input.type == SourceType.Shape) {
            //this.addShape(source);

            // Fetch required geometry
            const geometry = input.geometry ?? await this.fetchGeometry(input.query);

            const completedSource: VectorMapSource = {
                id: id,
                type: SourceType.Shape,
                query: input.query,
                visible: input.visible ?? true,
                geometry: geometry,
                name: input.name ?? geometry['features'][0]['properties']['shape_name'],
                alpha: input.alpha ?? 0.3,
                color: input.color ?? '#5385f8',
                showControls: input.showControls ?? true,
                fitBounds: input.fitBounds ?? false,
                getPopupContent: input.getPopupContent ?? null,
            };

            ctrl = new SvelteMapControl(MapShapeControl, { source: completedSource });
        }

        if (input.type == SourceType.BBox) {
            //this.addShape(source);

            // Fetch required geometry
            const geometry = await this.fetchBBox(input.query);

            const completedSource: VectorMapSource = {
                id: id,
                type: SourceType.Shape,
                query: input.query,
                visible: input.visible ?? true,
                geometry: geometry,
                name: input.name ?? "BBox",
                alpha: input.alpha ?? 0,
                color: input.color ?? '#5385f8',
                showControls: input.showControls ?? true,
                fitBounds: input.fitBounds ?? false,
                getPopupContent: input.getPopupContent ?? null,
            };

            ctrl = new SvelteMapControl(MapBBoxControl, { source: completedSource });
        }



        if (ctrl) {
            const node = this.layerControlNodeId
                ? document.getElementById(this.layerControlNodeId)
                : null;

            if (node) {
                // if a custom DOM node id is given to position the layer control
                // components, we need to manually add the control to the map
                // and then insert the html node to the target.
                ctrl.onAdd(this.map);
                node.appendChild(ctrl.container);
            } else {
                this.map.addControl(ctrl, "top-left");
            }

            return ctrl;
        }

        throw new Error(`Unknown source type: ${input.type}`)
    }

    async addSource(source: UserSourceInput) {
        // when the map is already fully loaded
        // isStyleLoaded() seems also to be false during a source being added
        // in this case the style.load part get's never fired again.
        if (this.map.isStyleLoaded()) {
            //this.sources.push(source);
            await this.loadSource(source);
        } else {
            this.map.once("style.load", async () => {
                //this.sources.push(source);
                await this.loadSource(source);
            });
        }
    }

    async fetchGeometry(query: Record<string, string>): Promise<object> {
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

    async fetchDataLayerVector(datalayer_key: string): Promise<object> {
        const res = await fetch(`/api/datalayers/vector?datalayer_key=${datalayer_key}`);
        if (!res.ok) throw new Error(`Failed to fetch Vector data for Data Layer: ${res.status}`);
        return res.json();
    }
}
