export async function fetchData(type, year, selectedLayers) {
	try {
		return await $.ajax({
			url: "/dashboard/info-map/get-dl-count-for-year-shapes/",
			data: {'type_id': type, 'year': year, 'data_layers': selectedLayers.join(',')},
		});
	} catch (error) {
		console.error(`Error fetching data`);
		throw error;
	}
}
