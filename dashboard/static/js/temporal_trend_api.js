export async function fetchShapesByType(typeId) {
	try {
		return await $.ajax({
			url: "/dashboard/temporal-trend/get-shapes-by-type/",
			data: {'type_id': typeId}
		});
	} catch (error) {
		console.error(`Error fetching shapes according to type ${typeId}:`, error);
		throw error;
	}
}

export async function fetchHistoricalData(dataLayerKey, shapeId) {
	try {
		return await $.ajax({
			url: "/dashboard/slider/get-historical-data-shape/",
			data: {'data_layer_key': dataLayerKey, 'shape_id': shapeId},
		});
	} catch (error) {
		console.error(`Error fetching historical data for ${dataLayerKey}:`, error);
		throw error;
	}
}
