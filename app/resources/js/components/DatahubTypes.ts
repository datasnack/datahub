export type DataLayerItem = {

    /**
     * Data Layer key
     */
    key: string,

    query: DataLayerQuery,

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
    BBox = "bbox",
    Vector = "vector",
}

export interface MapSource {
    id: string,
    type: SourceType,
    query: Record<string, string>,
    visible: boolean,
    name: string,
    geometry: object,
    alpha: number,
    showControls: boolean,
    fitBounds: boolean,
    getPopupContent: Function | null,
}
export type UserSourceInput =
    | {
        type: SourceType.Shape | SourceType.BBox | SourceType.Vector;
        query: Record<string, string>;
        visible?: boolean,
        id?: string;
        name?: string;
        color?: string;
        geometry?: object,
        alpha?: number;
        showControls?: boolean,
        fitBounds?: boolean,
        getPopupContent?: Function | null,
    }
    | {
        type: SourceType.Datalayer;
        query: Record<string, string>;
        visible?: boolean;
        id?: string;
        name?: string;
        cmap?: string;
        alpha?: number;
        mode?: string;
        geometry?: object,
        showControls?: boolean;
        fitBounds?: boolean;
        datalayer?: DataLayer,
        value_map?: object,
        extent?: [number, number] | null,
        showQueryLabel?: boolean,
        getPopupContent?: Function | null,
    };


export interface VectorMapSource extends MapSource {
    color: string,
}

export interface DatalayerMapSource extends MapSource {
    showQueryLabel: boolean,
    mode: string,
    cmap: string,
    datalayer: DataLayer,
    value_map: object | null,
    extent: [number, number] | null,
}
