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
    export let control;

    onMount(async () => {
        // Geometries
        source.geometry.features.forEach((feature) => {
            feature.properties.color = source.color;
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

        // Add outline
        map.addLayer({
            id: `${source.id}-outline`,
            type: "line",
            source: source.id,
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
        const markerLayerId = `${source.id}-markers`;
        map.addLayer({
            id: markerLayerId,
            type: "circle",
            source: source.id,
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

        // Add click handler for popup
        map.on("click", markerLayerId, (e) => {
            const coordinates = e.lngLat;
            const feature = e.features[0];

            const popupFnc = source.getPopupContent || getPopupContent;

            new maplibregl.Popup()
                .setLngLat(coordinates)
                .setHTML(popupFnc(feature))
                .addTo(map);
        });

        // Change cursor on hover
        map.on("mouseenter", markerLayerId, () => {
            map.getCanvas().style.cursor = "pointer";
        });

        map.on("mouseleave", markerLayerId, () => {
            map.getCanvas().style.cursor = "";
        });

        setSourceVisibility();
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
    function getPopupContent(feature) {
        const props = feature.properties;
        let content = '<div class="">';

        content += `<h5 class="mb-0">${props.name}</h5>`;

        let values = {};
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

        if (values) {
            var table = "";
            Object.keys(values).forEach(function (key) {
                if (key == "name") {
                    return;
                }
                const value = values[key];

                table += `<tr><th><code>${key}</code></th><td>${value}</td>`;
            });
            content += `<div class="overflow-y-scroll" style="max-height:200px"><table class="table table-sm"><tbody>${table}</tbody></table></div>`;
        }

        content += "</div>";

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
        </div>
    {/if}

    {#if source.showControls}
        <button on:click={deleteLayer} class="maplibregl-popup-close-button"
            >×</button
        >
    {/if}
</div>
