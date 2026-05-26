<!--
SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>

SPDX-License-Identifier: AGPL-3.0-only
-->
<script lang="ts">
    import { onMount } from "svelte";
    import maplibregl from "maplibre-gl";
    import type { Map, IControl } from "maplibre-gl";

    import {
        DataLayer,
        DataLayerItem,
        MapSource,
        VectorMapSource,
        SourceType,
    } from "./DatahubTypes";

    export let map: Map;
    export let source: VectorMapSource;
    export let control;

    onMount(async () => {
        // Geometries
        source.geometry.features.forEach((feature) => {
            feature.properties.alpha = source.alpha;
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

        const layerId = `${source.id}-fill`;
        map.addLayer({
            id: layerId,
            type: "fill",
            source: source.id,
            paint: {
                "fill-color": ["get", "color"],
                "fill-opacity": ["get", "alpha"],
            },
        });

        // Add outline
        map.addLayer({
            id: `${source.id}-outline`,
            type: "line",
            source: source.id,
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
        map.on("click", layerId, (e) => {
            const coordinates = e.lngLat;
            const feature = e.features[0];

            const popupFnc = source.getPopupContent || getPopupContent;

            new maplibregl.Popup()
                .setLngLat(coordinates)
                .setHTML(popupFnc(feature))
                .addTo(map);
        });

        // Change cursor on hover
        map.on("mouseenter", layerId, () => {
            map.getCanvas().style.cursor = "pointer";
        });

        map.on("mouseleave", layerId, () => {
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

    function setSourceAlpha() {
        /*const mapSource = map.getSource(source.id);

        if (mapSource) {
            const data = mapSource._data; // Private MapLibre API, not update save!

            data.geojson.features.forEach((feature) => {
                feature.properties.alpha = source.alpha;
            });

            mapSource.setData(data.geojson);
        }*/

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
    function getPopupContent(feature) {
        const props = feature.properties;
        let content = '<div class="">';

        // Customize based on your GeoJSON properties
        if (props.shape_name) {
            content += `<h5 class="mb-0">${props.shape_name}</h5>`;
        }

        if (props.type_key) {
            content += `<div class="small text-muted mb-1">${props.type_key}</div>`;
        }

        content += `<a href="${props.url}" class="">Details</a>`;

        // Add other properties
        /*Object.keys(props).forEach((key) => {
            if (key !== "name" && key !== "color") {
                content += `<p style="margin: 4px 0;"><strong>${key}:</strong> ${props[key]}</p>`;
            }
        });*/

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

    {#if source.showControls}
        <button on:click={deleteLayer} class="maplibregl-popup-close-button"
            >×</button
        >
    {/if}
</div>
