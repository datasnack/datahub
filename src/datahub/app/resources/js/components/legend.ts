// SPDX-FileCopyrightText: 2026 Jonathan Ströbele <mail@jonathanstroebele.de>
//
// SPDX-License-Identifier: AGPL-3.0-only

import { scaleSequential, scaleOrdinal, type ScaleSequential } from 'd3-scale';
import * as d3 from "d3";


import { LegendMode, type LegendMode as TLegendMode } from './DatahubTypes.js';

export const COLOR_SCALES = {
    YlGnBu: d3.interpolateYlGnBu,
    Viridis: d3.interpolateViridis,
    Reds: d3.interpolateReds,
    Greens: d3.interpolateGreens,
    Blues: d3.interpolateBlues,
    Oranges: d3.interpolateOranges,
} as const;
export type ColorScaleKey = keyof typeof COLOR_SCALES;

export function buildScale(isCategorical: boolean, cmap: ColorScaleKey, extent: [number, number], values: [], colors: string[]) {
    if (isCategorical) {
        return scaleOrdinal(
            values,
            colors && colors.length > 0 ? colors : d3.schemeCategory10);
    }

    const interpolator = COLOR_SCALES[cmap];
    return scaleSequential(extent, interpolator);
}
