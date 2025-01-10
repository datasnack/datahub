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

export async function fetchHistoricalDataHighestShape(dataLayerKey) {
	try {
		return await $.ajax({
			url: "/dashboard/slider/get-historical-data-highest-type/",
			data: {'data_layer_key': dataLayerKey},
		});
	} catch (error) {
		console.error(`Error fetching historical data for the highest shape`);
		throw error
	}
}

export async function fetchAvailableYears(dataLayerKey) {
	try {
		return await $.ajax({
			url: "/dashboard/slider/get-datalayer-available-years/",
			data: {'data_layer_key': dataLayerKey},
		});
	} catch (error) {
		console.error(`Error fetching historical data for the highest shape`);
		throw error
	}
}
