// SPDX-FileCopyrightText: 2026 Jonathan Ströbele <mail@jonathanstroebele.de>
//
// SPDX-License-Identifier: AGPL-3.0-only


import { z } from "zod";

export type DataLayerItem = {

    /**
     * Data Layer key
     */
    key: string,

    query: DataLayerQuery,
    yaxis?: string,
    datalayer: DataLayer,
}

export type ShapeType = {
    key: string,
    name: string,
}

export type DataLayer = {
    key: string,
    name: string,

    shape_types: ShapeType[],

    has_vector_data: boolean,

    temporal_resolution: string,
    available_years: number[],

    first_time: string,
    last_time: string,
}

export type DataLayerQuery = {
    shape_key: string | null,
    shape_type: string | null,
    start_date: string | null,
    end_date: string | null,
    aggregate: string | null,
    resample: string | null,
}


/**
 * Types of data that can be added to a map.
 *
 * datalayer -> a datalayer choropleth map
 * shape -> a single shape, or all shapes of a shape type
 */
export enum SourceType {
    Datalayer = "datalayer",
    Shape = "shape",
    BBox = "bbox",
    Vector = "vector",
}

export enum LegendMode {
    MinMax = "min_max",
    From0_1 = "from0_1",
    Fixed = "fixed",
}

export const MapSourceSchema = z.object({
    /**
     * Source Id for MapLibre
     */
    id: z.string(),
    status: z.enum(["loading", "ready", "error"]).default("loading"),
    type: z.enum(SourceType),
    loading: z.boolean().default(true),
    visible: z.boolean().default(true),
    fitBounds: z.boolean().default(false),
    name: z.string().nullable().default(null),

    showControls: z.boolean().default(true),

    query: z.record(z.string(), z.union([z.string(), z.number(), z.null()])),
    showQueryLabel: z.boolean().default(true),

    alpha: z.number().min(0).max(1).optional(),


    /**
     * Color for shapes or vectors
     */
    color: z.string().default('#5385f8'),


    /**
     * Color map for datalayers
     */
    cmap: z.string().default("YlGnBu"),
    mode: z.enum(LegendMode).default(LegendMode.MinMax),
    isCategorical: z.boolean().default(false),
    categoricalValues: z.array(z.string()).default([]),
    categoricalLabels: z.array(z.string()).default([]),
    categoricalColors: z.array(z.string()).default([]),
    isPercentage: z.boolean().default(false),
    extent: z.tuple([z.number(), z.number()]).nullable().default(null),
    actualExtent: z.tuple([z.number(), z.number()]).nullable().default(null)


}).transform((data) => ({
    ...data,
    alpha: data.alpha ?? (data.type === SourceType.Shape ? 0.3 : 1),
}));;

export type MapSource = z.infer<typeof MapSourceSchema>;


export const ChartSourceSchema = z.object({
    yaxis: z.enum(["y1", "y2"]).default("y1"),
    query: z.record(z.string(), z.union([z.string(), z.number(), z.null()])),
});

export type ChartSource = z.infer<typeof ChartSourceSchema>;
