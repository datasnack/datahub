<!--
SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>

SPDX-License-Identifier: AGPL-3.0-only
-->
<script lang="ts">
    import { onMount } from "svelte";
    import maplibregl from "maplibre-gl";
    import type { Map, IControl } from "maplibre-gl";

    import type { VectorMapSource } from "./DatahubTypes";

    export let map: Map;
    export let source: VectorMapSource;
    export let manager;
    export let control;

    let loading = true;

    onMount(async () => {
        if (!source.geometry) {
            source.geometry = await manager.fetchDataLayerVector(
                source.query.datalayer_key,
            );
        }

        // Geometries
        source.geometry.features.forEach((feature) => {
            // todo: why?
            const values = feature.properties;

            feature.properties = {
                alpha: source.alpha,
                color: source.color,
                values: values,
            };
        });

        // Add as a source when the map is ready
        map.addSource(source.id, {
            type: "geojson",
            data: source.geometry,
        });

        if (source.fitBounds) {
            const bounds = await map.getSource(source.id).getBounds();
            map.fitBounds(bounds, {
                linear: true,
                padding: 42,
            });
        }

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
                paint: { "line-color": ["get", "color"], "line-width": 3 },
            },
            Polygon: {
                type: "fill",
                paint: { "fill-color": ["get", "color"], "fill-opacity": 0.4 },
            },
        };

        types.forEach((t) => {
            const layerId = `${source.id}-${t.toLocaleLowerCase()}`;
            map.addLayer({
                id: layerId,
                source: source.id,
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

        setSourceVisibility();

        loading = false;
    });

    function deleteLayer() {
        const style = map.getStyle();

        // if the style has a problem loading, getStyle() returns nothing
        if (style) {
            const layers = style.layers.filter((l) => l.source === source.id);

            // Remove each layer
            layers.forEach((layer) => {
                if (map.getLayer(layer.id)) {
                    map.removeLayer(layer.id);
                }
            });
        }

        // Remove the source
        if (map.getSource(source.id)) {
            map.removeSource(source.id);
        }

        // remove itself
        control.onRemove();
    }

    function setSourceAlpha() {
        setSourceProperty(source.id, "alpha", source.alpha);
    }

    function setSourceColor() {
        setSourceProperty(source.id, "color", source.color);
    }

    function setSourceProperty(id: string, key: string, value: any) {
        const mapSource = map.getSource(id);

        if (mapSource) {
            const data = mapSource._data; // Private MapLibre API, not update save!

            data.geojson.features.forEach((feature) => {
                feature.properties[key] = value;
            });

            mapSource.setData(data.geojson);
        }
    }

    function setSourceVisibility() {
        const visibility = source.visible ? "visible" : "none";

        const layers = map
            .getStyle()
            .layers.filter((l) => l.source === source.id);

        for (const layer of layers) {
            map.setLayoutProperty(layer.id, "visibility", visibility);
        }
    }

    // Function to get popup content for a feature
    function getPopupContent(feature, show_all_as_table = false) {
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
</script>

<div class="flex flex-col gap-1">
    <div class="d-flex align-items-center gap-2">
        <input
            type="checkbox"
            bind:checked={source.visible}
            on:change={setSourceVisibility}
        />
        <span class="fw-bold">{source.name}</span>
    </div>

    {#if source.showControls}
        <div class="d-flex align-items-center gap-2 mt-1">
            <div>
                <input
                    class="form-control form-control-sm form-control-color"
                    style="border-radius: 50%; width: 1em; height: 1em; display: block; padding: 0; min-height: auto;"
                    type="color"
                    bind:value={source.color}
                    on:input={setSourceColor}
                />
            </div>
            <div class="d-flex align-items-center gap-2">
                <label class="d-flex align-items-center">
                    <abbr title="Alpha">A</abbr>:
                    <input
                        class="ms-1"
                        type="range"
                        min="0"
                        max="1"
                        step="0.01"
                        bind:value={source.alpha}
                        on:input={setSourceAlpha}
                    />
                </label>
            </div>
        </div>
    {/if}

    {#if loading}
        <div
            class="spinner-border"
            role="status"
            style="position: absolute;top: 0.8em; right:0.8em; width: 1em; height: 1em; border-width: 0.125em;"
        >
            <span class="visually-hidden">Loading...</span>
        </div>
    {/if}

    {#if source.showControls && !loading}
        <button on:click={deleteLayer} class="maplibregl-popup-close-button"
            >×</button
        >
    {/if}
</div>
