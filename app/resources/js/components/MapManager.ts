import maplibregl from "maplibre-gl";
import type { Map, IControl } from "maplibre-gl";
import { Protocol } from "pmtiles";

import StyleControl from "../maplibre/StyleControl";
import ScreenshotControl from "../maplibre/ScreenshotControl";
import FullScreenControl from "../maplibre/FullScreenControl";
import SourcesControl from "../maplibre/SourcesControl";
import LegendControl from "./LegendControl";

import { DataLayer, DataLayerItem, MapSource, SourceType } from "./DatahubTypes";


export class MapManager {

    private map: Map;
    private sourcesControl: SourcesControl | null = null;

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

    getMap(): Map { return this.map; }

    getMapLibre() { return maplibregl; }



    _sourceIdFromQuery(query) {
        return (
            "dh-" +
            Object.entries(query)
                .map(([key, value]) => `${key}-${value}`)
                .join("_")
        );
    }

    async fitToSourceBounds(sourceId: string) {
        const bounds = await this.map.getSource(sourceId).getBounds();
        this.map.fitBounds(bounds, {
            linear: true,
            padding: 42,
        });
    }

    /**
     * Vector data
     */
    async addVectorData(datalayer_key) {
        const sourceId = `dh-${datalayer_key}-vector`;
        if (map.getSource(sourceId)) {
            return;
        }

        if (!mapSourceControl) {
            mapSourceControl = new SourcesControl();
            map.addControl(mapSourceControl, "top-left");
        }

        fetch(`/api/datalayers/vector?datalayer_key=${datalayer_key}`)
            .then((response) => {
                if (!response.ok)
                    throw new Error("Network response was not ok");
                return response.json();
            })
            .then((geojsonData) => {
                geojsonData.features.forEach((feature) => {
                    const values = feature.properties;
                    feature.properties = {
                        color: "#5385f8",
                        values: values,
                    };
                });

                map.addSource(sourceId, {
                    type: "geojson",
                    data: geojsonData,
                });

                mapSourceControl.addSource({
                    id: sourceId,
                    name: "Vector data",
                });

                const types = ["Point", "LineString", "Polygon"];
                const layers = {
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
                        paint: { "line-color": "#0000ff", "line-width": 3 },
                    },
                    Polygon: {
                        type: "fill",
                        paint: { "fill-color": "#00ff00", "fill-opacity": 0.4 },
                    },
                };

                types.forEach((t) => {
                    const layerId = `${sourceId}-${t.toLocaleLowerCase()}`;
                    map.addLayer({
                        id: layerId,
                        source: sourceId,
                        filter: ["==", "$type", t],
                        ...layers[t],
                    });

                    map.on("click", layerId, (e) => {
                        const coordinates = e.lngLat;
                        const feature = e.features[0];

                        new maplibregl.Popup()
                            .setLngLat(coordinates)
                            .setHTML(getPopupContent(feature))
                            .addTo(map);
                    });

                    // Change cursor on hover
                    map.on("mouseenter", layerId, () => {
                        map.getCanvas().style.cursor = "pointer";
                    });

                    map.on("mouseleave", layerId, () => {
                        map.getCanvas().style.cursor = "";
                    });
                });
            });
    }



    /**
     * Shape
     *
     */

    async addShape(source: MapSource) {
        let query = source.query;

        if (!this.sourcesControl) {
            this.sourcesControl = new SourcesControl();
            this.map.addControl(this.sourcesControl, "top-left");
        }

        const queryString = new URLSearchParams(query).toString();
        const sourceId = this._sourceIdFromQuery(query);

        if (this.map.getSource(sourceId)) {
            return;
        }

        fetch(`/api/shapes/geometry?${queryString}`)
            .then((response) => {
                if (!response.ok)
                    throw new Error("Network response was not ok");
                return response.json();
            })
            .then((geojsonData) => {
                geojsonData.features.forEach((feature) => {
                    feature.properties.alpha = 0.2;
                    feature.properties.color = "#5385f8";
                });

                this.sourcesControl.addSource({
                    id: sourceId,
                    name: source.name,
                });

                // Add as a source when the map is ready
                this.map.addSource(sourceId, {
                    type: "geojson",
                    data: geojsonData,
                });

                const layerId = `${sourceId}-fill`;
                this.map.addLayer({
                    id: layerId,
                    type: "fill",
                    source: sourceId,
                    paint: {
                        "fill-color": ["get", "color"],
                        "fill-opacity": ["get", "alpha"],
                    },
                });

                // Add outline
                this.map.addLayer({
                    id: `${sourceId}-outline`,
                    type: "line",
                    source: sourceId,
                    paint: {
                        "line-color": ["get", "color"],
                        "line-width": [
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
                        "line-opacity": 1,
                    },
                });

                // Add click handler for popup
                this.map.on("click", layerId, (e) => {
                    const coordinates = e.lngLat;
                    const feature = e.features[0];

                    new maplibregl.Popup()
                        .setLngLat(coordinates)
                        .setHTML(this.getPopupContent(feature))
                        .addTo(this.map);
                });

                // Change cursor on hover
                this.map.on("mouseenter", layerId, () => {
                    this.map.getCanvas().style.cursor = "pointer";
                });

                this.map.on("mouseleave", layerId, () => {
                    this.map.getCanvas().style.cursor = "";
                });

                if (source.fitBounds) {
                    this.fitToSourceBounds(sourceId);
                }
            })
            .catch((error) => {
                console.error("Error loading GeoJSON:", error);
                deleteLayer();
            });
    }

    async addShapeBBox(source) {
        let query = source.query;

        if (!mapSourceControl) {
            mapSourceControl = new SourcesControl();
            map.addControl(mapSourceControl, "top-left");
        }

        const queryString = new URLSearchParams(query).toString();
        const sourceId = `dh-shape_id-${query.shape_id}-bbox`;

        if (map.getSource(sourceId)) {
            return;
        }

        fetch(`/api/shapes/bbox?${queryString}`)
            .then((response) => {
                if (!response.ok)
                    throw new Error("Network response was not ok");
                return response.json();
            })
            .then((geojsonData) => {
                geojsonData.features.forEach((feature) => {
                    feature.properties.color = "#5385f8";
                });

                mapSourceControl.addSource({
                    id: sourceId,
                    name: source.name,
                });

                // Add as a source when the map is ready
                map.addSource(sourceId, {
                    type: "geojson",
                    data: geojsonData,
                });

                // Add outline
                map.addLayer({
                    id: `${sourceId}-outline`,
                    type: "line",
                    source: sourceId,
                    paint: {
                        "line-color": ["get", "color"],
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
                    },
                });

                // add markers
                const markerLayerId = `${sourceId}-markers`;
                map.addLayer({
                    id: markerLayerId,
                    type: "circle",
                    source: sourceId,
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
                });

                map.on("click", markerLayerId, (e) => {
                    const coordinates = e.lngLat;
                    const feature = e.features[0];

                    new maplibregl.Popup()
                        .setLngLat(coordinates)
                        .setHTML(getPopupContent(feature))
                        .addTo(map);

                    e.originalEvent.stopPropagation();
                });

                // Change cursor on hover
                map.on("mouseenter", markerLayerId, () => {
                    map.getCanvas().style.cursor = "pointer";
                });

                map.on("mouseleave", markerLayerId, () => {
                    map.getCanvas().style.cursor = "";
                });
            })
            .catch((error) => {
                console.error("Error loading GeoJSON:", error);
                deleteLayer();
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


    getNextSourceId(): number {
        return this.sourceIdCounter++;
    }


    /****
     *
     * Add a new source to the map.
     */
    async loadSource(source: MapSource) {
        if (source.type == SourceType.Datalayer) {
            const ctrl = new LegendControl(source, source.datalayer);


            if (this.layerControlNodeId && document.getElementById(this.layerControlNodeId)) {
                // if a custom DOM node id is given to position the layer control
                // components, we need to manually add the control to the map
                // and then insert the html node to the target.
                ctrl.onAdd(this.map);
                const node = document.getElementById(this.layerControlNodeId);
                if (node) {
                    node.appendChild(ctrl.container);
                }
            } else {
                this.map.addControl(ctrl, "top-left");
            }

            return ctrl;
        }

        if (source.type == SourceType.Shape) {
            this.addShape(source);
            return;
        }

        console.log("Unknown source type:", source);
    }

    async addSource(userSource: MapSource) {
        const defaults: MapSource = {
            type: SourceType.Datalayer,
            visible: true,
            alpha: 1,
            mode: "min_max",
            cmap: "YlGnBu",
        };
        const source = { ...defaults, ...userSource };

        // when the map is already fully loaded
        // isStyleLoaded() seems also to be false during a source being added
        // in this case the style.load part get's never fired again.
        if (this.map.isStyleLoaded()) {
            this.sources.push(source);
            this.loadSource(source);
        } else {
            this.map.on("style.load", () => {
                this.sources.push(source);
                this.loadSource(source);
            });
        }
    }
}
