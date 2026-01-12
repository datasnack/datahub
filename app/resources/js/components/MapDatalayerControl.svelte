<!--
SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>

SPDX-License-Identifier: AGPL-3.0-only
-->
<script>
    import { onMount } from "svelte";
    import maplibregl from "maplibre-gl";

    /**
     * D3
     *
     */
    import * as d3 from "../d3/d3.js"; // custom d3 with only needed parts
    //import * as d3 from 'd3';

    import { Legend } from "../d3/d3.legend.js";
    import { Swatches } from "../d3/d3.swatches.js";

    export let map;
    export let source;
    export let datalayer;
    export let control;

    let value_map;

    const colorModes = {
        YlGnBu: d3.interpolateYlGnBu,
        Viridis: d3.interpolateViridis,
        Reds: d3.interpolateReds,
        Greens: d3.interpolateGreens,
        Blues: d3.interpolateBlues,
    };

    let legendContainer;
    let color;

    onMount(async () => {
        // todo: load datalayer meta if not set

        const query = source.query;

        const url = new URL("/api/datalayers/data/", window.location.origin);
        let params = {
            datalayer_key: query.datalayer_key,
            shape_type: query.shape_type,
            start_date: query.start_date,
            end_date: query.end_date,
        };
        if (query.aggregate) {
            params["aggregate"] = query.aggregate;
        }
        url.search = new URLSearchParams(params);

        // Data
        if (source.value_map) {
            value_map = source.value_map;
        } else {
            const response = await d3.json(url);
            value_map = new Map(
                response.data.map((d) => [d.dh_shape_id, d.value]),
            );
        }

        buildColor();

        // Geometries
        const queryString = new URLSearchParams(query).toString();
        console.log(queryString);

        fetch(`/api/shapes/geometry?${queryString}`)
            .then((response) => {
                if (!response.ok)
                    throw new Error("Network response was not ok");
                return response.json();
            })
            .then((geojsonData) => {
                geojsonData.features.forEach((feature) => {
                    const dh_shape_id = feature.properties.dh_shape_id;

                    // the shape might not have a known value and so not be
                    // present in in the returned result
                    let value = value_map.get(dh_shape_id) || null;

                    feature.properties.alpha = 1;

                    if (value === null) {
                        feature.properties.value = "n/a";
                        feature.properties.color = "rgba(0, 0, 0, 0.1)";
                    } else {
                        feature.properties.value = value;
                        feature.properties.color = color(value);
                    }
                });

                let legend;
                if (datalayer && datalayer.value_type == "nominal") {
                    legend = Swatches(color, {
                        //title: getSourceLabel(),
                    });
                } else if (datalayer && datalayer.value_type == "percentage") {
                    legend = Legend(color, {
                        //title: getSourceLabel(),
                        tickFormat: "%",
                    });
                } else {
                    legend = Legend(color, {
                        //title: getSourceLabel(),
                    });
                }
                legendContainer.appendChild(legend);

                // Add as a source when the map is ready
                map.addSource(source.id, {
                    type: "geojson",
                    data: geojsonData,
                });

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
                        "line-color": "#000",
                        "line-width": 1,
                        "line-opacity": 0.5,
                    },
                });

                // Add click handler for popup
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
            })
            .catch((error) => {
                console.error("Error loading GeoJSON:", error);
                deleteLayer();
            });
    });

    function buildColor() {
        const interpolator = colorModes[source.cmap];

        if (source.mode && source.mode == "from0_1") {
            color = d3.scaleSequential([0, 1], interpolator);
        } else if (source.extent) {
            color = d3.scaleSequential(source.extent, interpolator);
        } else {
            color = d3.scaleSequential(
                d3.extent(value_map.values()),
                interpolator,
            );
        }
    }

    function buildLegend() {
        buildColor();
        setSourceColor();

        let legend;
        if (datalayer.value_type == "nominal") {
            legend = Swatches(color, {
                //title: getSourceLabel(),
            });
        } else if (datalayer.value_type == "percentage") {
            legend = Legend(color, {
                //title: getSourceLabel(),
                tickFormat: "%",
            });
        } else {
            legend = Legend(color, {
                //title: getSourceLabel(),
            });
        }
        legendContainer.replaceChildren(legend);
    }

    function setSourceColor() {
        const mapSource = map.getSource(source.id);
        const data = mapSource._data; // OR keep your original GeoJSON reference

        data.features.forEach((feature) => {
            const value = feature.properties.value;
            if (value) {
                feature.properties.color = color(value);
            }
        });
        mapSource.setData(data);
    }

    function getSourceLabel() {
        console.log(source);
        if (source.hasOwnProperty("name") && source.name) {
            return source.name;
        }

        let name = `${datalayer.name}`;

        let date = `${source.query.start_date}`;
        if (source.query.start_date != source.query.end_date) {
            date = `${date}–${source.query.end_date}`;
        }
        let agg = "";
        if (source.query.aggregate) {
            agg = `, ${source.query.aggregate}`;
        }

        return `${name}, ${source.query.shape_type} (${date}${agg})`;
    }

    function showControls() {
        if (source.hasOwnProperty("showControls")) {
            return source.showControls;
        }

        return true;
    }

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
        const mapSource = map.getSource(source.id);
        const data = mapSource._data; // OR keep your original GeoJSON reference

        // Modify all features
        data.features.forEach((feature) => {
            feature.properties.alpha = source.alpha; // add/change properties
        });

        // Update the source with modified data
        mapSource.setData(data);
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
        if (props.name) {
            content += `<h5 class="mb-0">${props.name}</h5>`;
        }

        if (props.type) {
            content += `<div class="small text-muted mb-1">${props.type}</div>`;
        }

        content += `<div class="">Value: ${props.value}</div>`;
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
    <div class="d-flex align-items-center gap-2 mb-1">
        <input
            type="checkbox"
            bind:checked={source.visible}
            on:change={setSourceVisibility}
        />
        <span class="fw-bold">{getSourceLabel()}</span>
    </div>

    {#if showControls()}
        <div class="d-flex align-items-center gap-2">
            {#if datalayer && datalayer.value_type == "percentage"}
                <select bind:value={source.mode} on:change={buildLegend}>
                    <option value="min_max">[min, max]</option>
                    <option value="from0_1">[0, 100]</option>
                </select>
            {/if}

            <select bind:value={source.cmap} on:change={buildLegend}>
                {#each Object.keys(colorModes) as name}
                    <option value={name}>{name}</option>
                {/each}
            </select>

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
    {/if}

    <div bind:this={legendContainer}></div>

    {#if showControls()}
        <button on:click={deleteLayer} class="maplibregl-popup-close-button"
            >×</button
        >
    {/if}
</div>
