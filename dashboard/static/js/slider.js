import {applyPreset, getColor, updateLegendBar} from './customization_utils.js';
import {fetchLayerData, fetchMinMaxValues} from "./slider_api.js";

const {centerX, centerY, centerZoom, presets} = config;

let map;
let layerGroups = {};
let defaultTransparency = 0.9

$(document).ready(function () {
	$('#type-dropdown').prop('selectedIndex', 0);
	$('#loading-message').hide();
	if (!map) {
		map = L.map('map').setView(
			[centerY, centerX], centerZoom
		);

		L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
			attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
		}).addTo(map);
	}

});

$('.add-datalayer').on('click', function () {
	const shapeType = $('#type-dropdown').val();
	$('#type-dropdown').prop('disabled', true);
	if (shapeType) {
		let datalayerKey = $(this).data('datalayer');
		let datalayerName = $(this).text();

		let selectedItem = `
					<div class="datalayer-item border rounded m-2 p-2" id="selected-${datalayerKey}">
						<label class="col-form-label-sm" data-bs-toggle="collapse" data-bs-target="#selected-${datalayerKey}-util" style="cursor: pointer;">
							${datalayerName}
						</label>
						<div class="collapse" id="selected-${datalayerKey}-util">
						</div>
					</div>
				`;
		$('#selected-datalayers').append(selectedItem);
		$(this).prop('disabled', true);
		processObjects(datalayerKey)
	} else {
		alert("Please select the type!");
	}
});


function processObjects(dataLayerKey) {
	$.ajax({
		url: "/dashboard/slider/get-datalayer-available-years/",
		data: {'data_layer_key': dataLayerKey},
		success: function (data) {
			const slider = $('#year-slider')[0];
			if (slider && slider.noUiSlider) {
				updateSlider(slider, data)
			} else {
				initializeSlider(slider, data)
			}
			createNewLayer(slider, dataLayerKey);
			createNewGraph(dataLayerKey)
		}
	});
}

function initializeSlider(slider, availableYears) {
	const minYear = Math.min(...availableYears);
	const maxYear = Math.max(...availableYears);
	noUiSlider.create(slider, {
		start: minYear,
		step: 1,
		range: {
			'min': minYear,
			'max': maxYear
		},
		tooltips: {
			to: function (value) {
				return value.toFixed(0);
			},
			from: function (value) {
				return Number(value);
			}
		},
		pips: {
			mode: 'values',
			values: [minYear, maxYear],
			density: 10
		}
	});
	slider.noUiSlider.on('change', updateMap);
}

function updateSlider(slider, availableYears) {
	const range = slider.noUiSlider.options.range;
	const newMinYear = Math.min(range.min, Math.min(...availableYears))
	const newMaxYear = Math.max(range.max, Math.max(...availableYears))
	slider.noUiSlider.updateOptions({
		range: {
			'min': newMinYear,
			'max': newMaxYear
		}
	});
}

function createLayerGroup(dataLayerKey, minValue, maxValue, data, presetColors) {
	const {names, geometries, dl_values: dlValues} = data;
	const layerGroup = L.layerGroup();

	Object.entries(geometries).forEach(([shapeId, geometryData]) => {
		const value = dlValues[shapeId];
		const name = names[shapeId] || 'Unknown';
		const geometry = typeof geometryData === 'string' ? JSON.parse(geometryData) : geometryData;

		const color = getColor(value, minValue, maxValue, presetColors);

		const geoJsonFeature = {
			type: 'Feature',
			geometry: geometry,
			properties: {id: shapeId, name, value}
		};

		const geoJsonLayer = L.geoJSON(geoJsonFeature, {
			style: () => ({
				fillColor: color,
				weight: 2,
				opacity: 1,
				color: 'black',
				fillOpacity: defaultTransparency
			}),
			onEachFeature: (feature, layer) => {
				layer.on('mouseover', function (e) {
					let popupContent = `<b>${feature.properties.name}</b><br>Value: <br>${feature.properties.value}`;
					let popup = L.popup()
						.setLatLng(e.latlng)
						.setContent(popupContent)
						.openOn(layer._map);
				});

				layer.on('mouseout', function () {
					layer._map.closePopup();
				});


				layer.on('click', () => {
					addToGraph(feature.properties.id)
				});
			}

		});

		geoJsonLayer.addTo(layerGroup);
	});

	return layerGroup;
}

async function updateOrCreateLayer(dataLayerKey, shapeType, selectedYear, layerGroup, presetColors) {
	try {
		const minMaxData = await fetchMinMaxValues(dataLayerKey, shapeType);
		const {min_value: minValue, max_value: maxValue} = minMaxData;

		const layerData = await fetchLayerData(dataLayerKey, shapeType, selectedYear);

		$(`#min-label-${dataLayerKey}`).text(Math.round(minValue));
		$(`#max-label-${dataLayerKey}`).text(Math.round(maxValue));
		updateLegendBar(`#legend-bar-${dataLayerKey}`, presetColors, 'column');

		if (layerGroup) {
			layerGroup.clearLayers();
			createLayerGroup(dataLayerKey, minValue, maxValue, layerData, presetColors).eachLayer(layer => layer.addTo(layerGroup));
			applyPreset(presetColors, `#legend-bar-${dataLayerKey}`, $(`#transparency-input-${dataLayerKey}`).val(), parseInt($(`#min-label-${dataLayerKey}`).text()), parseInt($(`#max-label-${dataLayerKey}`).text()), layerGroup, dataLayerKey);
		} else {
			const newLayerGroup = createLayerGroup(dataLayerKey, minValue, maxValue, layerData, presetColors);
			layerGroups[dataLayerKey] = newLayerGroup;
			newLayerGroup.addTo(map);
		}
	} catch (error) {
		console.error(`Error processing layer ${dataLayerKey}:`, error);
	} finally {
		$('#loading-message').hide();
	}
}

async function updateMap() {
	$('#loading-message').show();
	const shapeType = $('#type-dropdown').val();
	const selectedYear = parseInt($('#year-slider')[0].noUiSlider.get());

	for (const [dataLayerKey, layerGroup] of Object.entries(layerGroups)) {
		const selectedPreset = $(`#preset-select-${dataLayerKey}`).val();
		const presetColors = presets[selectedPreset].colors;
		await updateOrCreateLayer(dataLayerKey, shapeType, selectedYear, layerGroup, presetColors);
	}

	$('#loading-message').hide();
}

async function createNewLayer(slider, dataLayerKey) {
	$('#loading-message').show();
	const shapeType = $('#type-dropdown').val();
	const selectedYear = parseInt(slider.noUiSlider.get());

	let newUtilItems = `
				<div class="d-flex align-items-stretch border rounded m-2 p-2" id="legend-items-${dataLayerKey}">
					<div id="legend-description-${dataLayerKey}" class="d-flex align-items-stretch">
						<div class="d-flex flex-column justify-content-between" id="legend-labels-column-${dataLayerKey}">
							<label class="col-form-label-sm" id="min-label-${dataLayerKey}">Min</label>
							<label class="col-form-label-sm" id="max-label-${dataLayerKey}">Max</label>
						</div>
						<div class="p-2 flex-grow-1" id="legend-bar-${dataLayerKey}"></div>
					</div>
					<div class="legend-customize-${dataLayerKey} mx-4 d-flex align-items-sm-center">
						<div>
							<label for="preset-select-${dataLayerKey}" class="col-form-label-sm">Adjust Preset:</label>
							<select id="preset-select-${dataLayerKey}" class="form-control">
							</select>
							<label for="transparency-input-${dataLayerKey}" class="col-form-label-sm">Adjust Transparency (0-1):</label>
							<input class="form-control" id="transparency-input-${dataLayerKey}">
						</div>
					</div>
					<div id="util-buttons-${dataLayerKey}" class="mx-4 d-flex flex-column align-items-sm-center justify-content-center">
						<button id="apply-customization-${dataLayerKey}-btn" class="btn btn-primary btn-sm m-4 apply-customization">Apply Customization</button>
						<button id="remove-${dataLayerKey}-btn" class="btn btn-danger btn-sm remove-datalayer">Remove Layer</button>
					</div>
				</div>`;

	$(`#selected-${dataLayerKey}-util`).append(newUtilItems);
	$(`#selected-${dataLayerKey}-util`).removeClass("d-none");

	populateLegendSelect(dataLayerKey)
	const defaultPresetColors = presets[Object.keys(presets)[0]].colors;

	await updateOrCreateLayer(dataLayerKey, shapeType, selectedYear, null, defaultPresetColors);

	$('#loading-message').hide();
}

$(document).on('click', '.apply-customization', function () {
	let buttonId = $(this).attr('id');
	let dataLayerKey = buttonId.match(/apply-customization-(\S+)-btn/)[1];
	const selectedPreset = $(`#preset-select-${dataLayerKey}`).val();
	if (presets[selectedPreset]) {
		const presetColors = presets[selectedPreset].colors;
			applyPreset(presetColors, `#legend-bar-${dataLayerKey}`, $(`#transparency-input-${dataLayerKey}`).val(), parseInt($(`#min-label-${dataLayerKey}`).text()), parseInt($(`#max-label-${dataLayerKey}`).text()), layerGroups[dataLayerKey], dataLayerKey);
	} else {
		alert('Invalid preset selected.');
	}
});

$(document).on('click', '.remove-datalayer', function () {
	let buttonId = $(this).attr('id');
	let dataLayerKey = buttonId.match(/remove-(\S+)-btn/)[1];
	removeLayer(dataLayerKey)
});


function populateLegendSelect(dataLayerKey) {
	const presetSelect = $(`#preset-select-${dataLayerKey}`);
	Object.keys(presets).forEach(presetKey => {
		const option = $('<option>')
			.attr('value', presetKey)
			.text(presets[presetKey].name);
		presetSelect.append(option);
	});
}

function removeLayer(dataLayerKey) {
	map.removeLayer(layerGroups[dataLayerKey])
	$(`#add-datalayer-${dataLayerKey}-btn`).prop('disabled', false);
	$(`#selected-${dataLayerKey}`).remove();
	delete layerGroups[dataLayerKey];
}

function createNewGraph(dataLayerKey) {
	let newGraph = `
				<div class="border rounded" id="graph-${dataLayerKey}">
				</div>`;
	$('#graph-container').append(newGraph)
	let traces = [];
	$.ajax({
		url: "/dashboard/slider/get-historical-data-highest-type/",
		data: {'data_layer_key': dataLayerKey},
		success: function (data) {
			let historicalData = data.historical_data;
			let highestShapeName = data.highest_shape_name;
			if (historicalData.length > 0) {
				traces.push({
					x: historicalData.map(d => d.year),
					y: historicalData.map(d => d.value),
					mode: 'lines+markers',
					showlegend: true,
					name: highestShapeName,
					line: {color: '#8979da'}
				});
				let layout = {
					title: dataLayerKey,
					xaxis: {title: 'Year'},
					yaxis: {title: 'Value'},
					width: null,
					height: 400
				};
				Plotly.newPlot($(`#graph-${dataLayerKey}`)[0], traces, layout);
			}
		},
		error: function (xhr, status, error) {
			console.error('Error creating graph:', error);
		}
	})
}


function addToGraph(shapeId) {
	$('#selected-datalayers').children().each(function (index, element) {
		let childId = $(element).attr('id');
		let dataLayerKey = childId.match(/selected-(\S+)/)[1];
		const traceExists = $(`#graph-${dataLayerKey}`)[0].data.some(trace => trace.id === shapeId);
		if (!traceExists) {
			$.ajax({
				url: "/dashboard/slider/get-historical-data-shape/",
				data: {'data_layer_key': dataLayerKey, 'shape_id': shapeId},
				success: function (data) {
					const historicalData = data.historical_data;
					const shapeName = data.shape_name
					if (historicalData.length > 0) {
						const newTrace = {
							x: historicalData.map(d => d.year),
							y: historicalData.map(d => d.value),
							mode: 'lines+markers',
							showlegend: true,
							name: shapeName,
							id: shapeId
						};

						Plotly.addTraces($(`#graph-${dataLayerKey}`)[0], newTrace);
					}

				},
				error: function (xhr, status, error) {
					console.error('Error adding to graph:', error);
				}
			})
		}
	});

}
