import { DataLayer, DataLayerItem, MapSource, SourceType } from "./DatahubTypes";
import type { Map, IControl } from "maplibre-gl";
import MapDatalayerControl from "./MapDatalayerControl.svelte"

import { mount } from "svelte";


class LegendControl {

    source: MapSource;
    private datalayer: DataLayer;
    map!: Map;
    container!: HTMLElement;

    constructor(source: MapSource, datalayer: DataLayer) {
        this.source = source;
        this.datalayer = datalayer;
    }

    onAdd(map: Map): HTMLElement {
        this.map = map;

        // Create a container for MapLibre
        this.container = document.createElement("div");
        this.container.className =
            "maplibregl-ctrl maplibregl-ctrl-group py-1 px-2";

        this.ctrl = mount(MapDatalayerControl, {
            target: this.container,
            props: {
                map: map,
                source: this.source,
                datalayer: this.datalayer,
                control: this,
            },
        });

        return this.container;
    }

    setData(value_map) {
        this.ctrl.setData(value_map);
    }

    onRemove() {
        if (this.container.parentNode) {
            this.container.parentNode.removeChild(this.container);
        }
        this.map = null;
    }
}

export default LegendControl;
