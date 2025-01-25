import {applyPreset, getColor, updateLegendBar} from './customization_utils.js';
import {fetchData} from "./info_map_api.js";

const {centerX, centerY, centerZoom, minYear, maxYear, presets} = config;

let map;
let layerGroup = L.layerGroup();
let defaultTransparency = 0.9;
let datalayerDict = {}
let shapeDict = {}


$(document).ready(function () {
	$('#type-dropdown').prop('selectedIndex', 0);
	$('#transparency-input').val(defaultTransparency);
	$('.form-check-input').prop('checked', false);
	$('#loading-message').hide();
	$('#current-year').hide();
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
	datalayerDict = {}
	shapeDict = {}
	$('.form-check-input:checked').each(function (index) {
		selectedLayers.push($(this).data('datalayer'));
		datalayerDict[index + 1] = $(this).next('label').text().trim();
	});
	writeTableRowHeaders();
	if (year && selectedLayers.length > 0 && type) {
		$('#current-year').show();
		$('#current-year').text(year);
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
				layer.on('click', function (e) {
					let detail = $(`#details-dls-${feature.properties.id}`)[0];

					if (detail.classList.contains('collapse')) {
						if (detail.classList.contains('show')) {
							detail.classList.remove('show');
						} else {
							detail.classList.add('show');
						}
					}

					$(`#shape-name-${feature.properties.id}`)[0].scrollIntoView({
						behavior: 'smooth',
						block: 'center'
					});
				});

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

	populateRankingListAndTable(shapeData);
	$('#loading-message').hide();
}

function populateRankingListAndTable(shapeData) {
	shapeData.sort((a, b) => a.name.localeCompare(b.name))
	writeTableColumnHeaders(shapeData);

	shapeData.sort((a, b) => b.availableCount - a.availableCount);

	const rankingList = $('#ranking-list');
	rankingList.empty();

	shapeData.forEach((shape, index) => {
		let availableDl = shape.availableDls.map(dl => {
			fillTableCell(dl[0], shape.name, '<i class="bi bi-check text-success fs-3"></i>');
			return `<li class="list-group-item fw-light small">
                        <a href="/datalayers/${dl[1]}" class="text-decoration-none">${dl[0]}</a>
                    </li>`;
		}).join('');

		let missingDl = shape.missingDls.map(dl => {
			fillTableCell(dl[0], shape.name, '<i class="bi bi-x text-danger fs-3"></i>');
			return `<li class="list-group-item fw-light small">
                        <a href="/datalayers/${dl[1]}" class="text-decoration-none">${dl[0]}</a>
                    </li>`;
		}).join('');

		let percentage = ((shape.availableCount / (shape.availableCount + shape.missingCount)) * 100).toFixed(2);

		rankingList.append(`
									<li class="list-group-item">
										<b class="shape-name"
										   id="shape-name-${shape.id}"
										   data-bs-toggle="collapse"
										   data-bs-target="#details-dls-${shape.id}"
										   data-index="${shape.id}"
										   style="cursor: pointer;">
											<a href="/shapes/${shape.id}" class="text-decoration-none">
												${shape.name}
											</a>
											<span class="badge text-bg-primary rounded-pill">${shape.availableCount}</span>
											<span class="badge text-bg-danger rounded-pill">${shape.missingCount}</span>
											<span class="badge text-bg-success rounded-pill">${percentage}%</span>
										</b>
										<div id="details-dls-${shape.id}" class="details-dls collapse container text-center m-4">
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
}


function writeTableRowHeaders() {
	const tbody = $('#info-matrix tbody');
	tbody.empty();
	$.each(datalayerDict, function (index, selectedLayerName) {
		const row = $('<tr></tr>');
		row.append(`<th scope="row">${selectedLayerName}</th>`);
		tbody.append(row);
	});
}

function writeTableColumnHeaders(shapeData) {
	const thead = $('#info-matrix thead');
	thead.empty();
	let headerRow = '<tr><th scope="col"></th>';
	shapeData.forEach((shape, index) => {
		shapeDict[index + 1] = shape.name;
		headerRow += `<th scope="col">${shape.name}</th>`;
	});
	headerRow += '</tr>';
	thead.append(headerRow);
	createTds(shapeData.length)
}

function createTds(columnsCount) {
	const tbody = $('#info-matrix tbody');
	tbody.find('tr').each(function () {
		const row = $(this);
		for (let i = 0; i < columnsCount; i++) {
			row.append('<td></td>');
		}
	});
}

function fillTableCell(datalayerName, shapeName, value) {
	const rowIndex = Object.keys(datalayerDict).find(key => datalayerDict[key] === datalayerName);
	const colIndex = Object.keys(shapeDict).find(key => shapeDict[key] === shapeName);

	const row = $('#info-matrix tr').eq(parseInt(rowIndex));
	let cell = row.find('td').eq(parseInt(colIndex) - 1);

	cell.html(value);
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


