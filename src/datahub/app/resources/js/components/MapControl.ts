// SPDX-FileCopyrightText: 2026 Jonathan Ströbele <mail@jonathanstroebele.de>
//
// SPDX-License-Identifier: AGPL-3.0-only


import type { Attachment } from 'svelte/attachments';
import type { Map as MapLibreMap, IControl, ControlPosition } from 'maplibre-gl';

class NodeControl implements IControl {
    #node: HTMLElement;

    constructor(node: HTMLElement) {
        this.#node = node;
    }

    onAdd(): HTMLElement {
        this.#node.classList.add('maplibregl-ctrl',);
        return this.#node;
    }

    onRemove(): void {
        this.#node.parentNode?.removeChild(this.#node);
    }
}

export function mapControl(
    map: MapLibreMap,
    position: ControlPosition = 'top-left'
): Attachment<HTMLElement> {
    return (node) => {
        const control = new NodeControl(node);
        map.addControl(control, position);
        return () => map.removeControl(control); // cleanup, also re-run on dep change
    };
}
