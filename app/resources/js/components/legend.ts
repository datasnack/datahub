// SPDX-FileCopyrightText: 2026 Jonathan Ströbele <mail@jonathanstroebele.de>
//
// SPDX-License-Identifier: AGPL-3.0-only

import { scaleSequential, scaleOrdinal, type ScaleSequential } from 'd3-scale';
import * as d3 from "../d3/d3.js"; // custom d3 with only needed parts


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

export function buildScale(isCategorical: boolean, cmap: ColorScaleKey, extent: [number, number], values: []) {

    if (isCategorical) {
        return scaleOrdinal(
            values,
            d3.schemeCategory10,
        );
    }

    const interpolator = COLOR_SCALES[cmap];
    return scaleSequential(extent, interpolator);
}
