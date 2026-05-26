
import type { Map, IControl } from "maplibre-gl";
import { mount } from "svelte";
import { reactive } from "svelte/reactivity";

export class SvelteMapControl<T> implements IControl {

    container!: HTMLElement;
    map!: Map;
    private _ctrl: any;

    constructor(
        private Component: any,
        private props: T
    ) { }

    onAdd(map: Map): HTMLElement {
        this.map = map;
        this.container = document.createElement("div");
        this.container.className = "maplibregl-ctrl maplibregl-ctrl-group py-1 px-2";

        this._ctrl = mount(this.Component, {
            target: this.container,
            props: { map, ...this.props, control: this },
        });
        return this.container;
    }

    onRemove() {
        this.container.parentNode?.removeChild(this.container);
        this.map = null!;
    }

    // forward any public component methods
    call<K extends keyof any>(method: K, ...args: any[]) {
        return this._ctrl[method]?.(...args);
    }

    setLoading() {
        this._ctrl.setLoading();
    }

    setData(value_map) {
        this._ctrl.setData(value_map);
    }

}
