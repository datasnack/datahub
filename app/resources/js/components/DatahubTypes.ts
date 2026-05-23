export interface DataLayerItem {

    /**
     * Data Layer key
     */
    key: string,

    query: DataLayerQuery,

    datalayer: DataLayer,
}

export interface ShapeType {
    key: string,
    name: string,
}

export interface DataLayer {
    key: string,
    name: string,

    shape_types: ShapeType[],

    has_vector_data: boolean,

    temporal_resolution: string,
    available_years: number[],

    first_time: string,
    last_time: string,
}

export interface DataLayerQuery {
    shape_type: string | null,
    start_date: string | null,
    end_date: string | null,
    aggregate: string | null,
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
}

export interface XMapSource {
    id: string;
    type: SourceType;
    visible: boolean;
    alpha: number;
    mode: "min_max";
    cmap: string;
    query: object;
    datalayer: DataLayer | null;
}

export interface MapSource {
    id: string,
    type: SourceType,
    name: string,
    geometry: object,
}


export interface ShapeMapSource extends MapSource {

    query: Record<string, string>,
}

/***
 *

Types:

- Datalayer
- Shapes
- Geometry (bbox)
- Vector?


 */


export interface DatalayerMapSource extends MapSource {
    id: string;
    type: SourceType;
    name: string,
    visible: boolean;
    alpha: number;
    mode: "min_max";
    cmap: string;
    query: object;
    datalayer: DataLayer | null;
}



const sourceDefaults = {
    id: "assd",
    type: SourceType.Datalayer,
    visible: true,
    alpha: 1,
    mode: "min_max",
    cmap: "YlGnBu",
} satisfies Partial<MapSource>;


function createSource(userSource: Partial<MapSource>): MapSource {
    return {
        ...sourceDefaults,
        ...userSource,
    };
}
