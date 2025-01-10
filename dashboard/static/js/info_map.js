import {applyPreset, getColor, updateLegendBar} from './customization_utils.js';
import {fetchData} from "./info_map_api.js";

const {centerX, centerY, centerZoom, minYear, maxYear, presets} = config;

let map;
let layerGroup = L.layerGroup();
let defaultTransparency = 0.9;

$(document).ready(function () {
	$('#type-dropdown').prop('selectedIndex', 0);
	$('#transparency-input').val(defaultTransparency);
	$('.form-check-input').prop('checked', false);
	$('#loading-message').hide();
	if (!map) {
		map = L.map('map').setView(
			[centerY, centerX], centerZoom
		);

		L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
			attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
		}).addTo(map);

		layerGroup.addTo(map);

		addLegend();
	}
	$('#select-all-btn').click(function () {
		$('.form-check-input').prop('checked', true);
	});

	$('#clear-all-btn').click(function () {
		$('.form-check-input').prop('checked', false);
	});

	initializeSlider(minYear, maxYear);
	populateLegendSelect();
});

function initializeSlider(minYear, maxYear) {
	const slider = $('#year-slider')[0];
	if (slider && slider.noUiSlider) {
		slider.noUiSlider.destroy();
	}
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

function addLegend() {
	const legend = L.control({position: 'bottomright'});

	legend.onAdd = function (map) {
		const div = L.DomUtil.create('div', 'info legend');
		div.innerHTML = `
					<button id="customize-legend-btn" class="btn btn-sm btn-primary" style="z-index: 500">Customize Legend</button>
					<div class="legend-bar p-2"></div>
					<div class="legend-labels d-flex justify-content-between"">
						<span id="min-label"></span>
						<span id="max-label"></span>
					</div>
				`;
		return div;
	};

	legend.addTo(map);

	$('#customize-legend-btn').on('click', function () {
		$('#legend-popup').toggle();
	});

	$('#close-legend-btn').on('click', function () {
		$('#legend-popup').css('display', 'none');
	});
}

$('#load-button').on('click', updateMap);

async function updateMap() {
	$('#loading-message').show();
	const type = $('#type-dropdown').val();
	const year = parseInt($('#year-slider')[0].noUiSlider.get());
	const selectedLayers = [];
	$('.form-check-input:checked').each(function () {
		selectedLayers.push($(this).data('datalayer'));
	});
	if (year && selectedLayers.length > 0 && type) {
		const data = await fetchData(type, year, selectedLayers)
		const selectedPreset = $('#preset-select').val();
		const presetColors = presets[selectedPreset].colors;
		updateOrCreateLayer(data, 0, selectedLayers.length, presetColors)
		applyPreset(presetColors, '.legend-bar', $('#transparency-input').val(), 0, $('#datalayer-checkbox .form-check-input:checked').length, layerGroup);
	} else {
		alert('Missing input. Please make sure that the type and data layers are selected.');
		$('#loading-message').hide();
	}
}

function updateOrCreateLayer(data, minValue, maxValue, presetColors) {
	layerGroup.clearLayers();

	const {shape_dl_dict: availableDlDict, shape_missing_dl_dict: missingDlDict, geometries, names} = data;

	$('#min-label').text(Math.round(minValue));
	$('#max-label').text(Math.round(maxValue));
	updateLegendBar('.legend-bar', presetColors, 'row');

	const shapeData = [];
	for (const shapeId in geometries) {
		const availableDls = availableDlDict[shapeId] || 'No available data layer';
		const missingDls = missingDlDict[shapeId] || 'No missing data layer';
		const availableCount = availableDls.length || 0;
		const missingCount = missingDls.length || 0;
		const name = names[shapeId] || 'Unknown';
		shapeData.push({id: shapeId, name, availableDls, missingDls, availableCount, missingCount});

		let geometry;

		if (typeof geometries[shapeId] === 'string') {
			geometry = JSON.parse(geometries[shapeId]);
		} else {
			geometry = geometries[shapeId];
		}

		const color = getColor(availableCount, minValue, maxValue, presetColors);

		const geoJsonFeature = {
			type: 'Feature',
			geometry: geometry,
			properties: {id: shapeId, name, availableCount, missingCount}
		};

		const geoJsonLayer = L.geoJSON(geoJsonFeature, {
			style: () => ({
				fillColor: color,
				weight: 2,
				opacity: 1,
				color: 'black',
				fillOpacity: 1
			}),
			onEachFeature: (feature, layer) => {
				layer.on('mouseover', function (e) {
					let popupContent = `<b>${feature.properties.name}</b>
										<br>Available Data Layers: ${feature.properties.availableCount}`;
					let popup = L.popup()
						.setLatLng(e.latlng)
						.setContent(popupContent)
						.openOn(layer._map);
				});

				layer.on('mouseout', function () {
					layer._map.closePopup();
				});
				layer.bindPopup()
			}
		});

		geoJsonLayer.addTo(layerGroup);
	}

	shapeData.sort((a, b) => b.availableCount - a.availableCount);

	const rankingList = $('#ranking-list');
	rankingList.empty();

	shapeData.forEach((shape, index) => {
		let availableDl = shape.availableDls.map(dl => `<li class="list-group-item fw-light">
										<a href="/datalayers/${dl[1]}" class="text-decoration-none">${dl[0]}</a></li>`).join('');

		let missingDl = shape.missingDls.map(dl => `<li class="list-group-item fw-light">
										<a href="/datalayers/${dl[1]}" class="text-decoration-none">${dl[0]}</a></li>`).join('');

		rankingList.append(`
									<li class="list-group-item">
										<b class="shape-name"
										   data-bs-toggle="collapse"
										   data-bs-target="#details-dls-${index}"
										   data-index="${index}"
										   style="cursor: pointer;">
											<a href="/shapes/${shape.id}" class="text-decoration-none">
												${shape.name}
											</a>
											<span class="badge text-bg-primary rounded-pill">${shape.availableCount}</span>
											<span class="badge text-bg-danger rounded-pill">${shape.missingCount}</span>
										</b>
										<div id="details-dls-${index}" class="details-dls collapse container text-center m-4">
											<div class="row">
												<div class="col">
													<label class="form-label fw-bold">Available Data Layers</label>
													<ul class="available-dls list-group list-group-flush">
														${availableDl}
													</ul>
												</div>
												<div class="col">
													<label class="form-label fw-bold">Missing Data Layers</label>
													<ul class="missing-dls list-group list-group-flush">
														${missingDl}
													</ul>
												</div>
											</div>
										</div>
									</li>
								`);
	});

	$('#loading-message').hide();
}

$('#apply-legend-btn').on('click', function () {
	const selectedPreset = $('#preset-select').val();
	if (presets[selectedPreset]) {
		const presetColors = presets[selectedPreset].colors;
		applyPreset(presetColors, '.legend-bar', $('#transparency-input').val(), 0, $('#datalayer-checkbox .form-check-input:checked').length, layerGroup);
		$('#legend-popup').css('display', 'none');
	} else {
		alert('Invalid preset selected.');
	}
});

function populateLegendSelect() {
	const presetSelect = $('#preset-select');
	Object.keys(presets).forEach(presetKey => {
		const option = $('<option>')
			.attr('value', presetKey)
			.text(presets[presetKey].name);
		presetSelect.append(option);
	});
}
