export async function fetchMinMaxValues(dataLayerKey, shapeType) {
	try {
		return await $.ajax({
			url: "/dashboard/slider/get-min-max-dl-value/",
			data: {'data_layer_key': dataLayerKey, 'shape_type': shapeType}
		});
	} catch (error) {
		console.error(`Error fetching min/max for ${dataLayerKey}:`, error);
		throw error;
	}
}

export async function fetchLayerData(dataLayerKey, shapeType, selectedYear) {
	try {
		return await $.ajax({
			url: "/dashboard/slider/get-dl-value-for-year-shapes/",
			data: {'data_layer_key': dataLayerKey, 'shape_type': shapeType, 'year': selectedYear}
		});
	} catch (error) {
		console.error(`Error fetching layer data for ${dataLayerKey}:`, error);
		throw error;
	}
}
