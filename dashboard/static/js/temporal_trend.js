import {fetchHistoricalData, fetchShapesByType} from "./temporal_trend_api.js";

$(document).ready(function () {
	$('#type-dropdown').prop('selectedIndex', 0);
	$('#shape-dropdown').prop('selectedIndex', 0);
	$('#datalayer-1-dropdown').prop('selectedIndex', 0);
	populateDatalayerDropdown('#datalayer-1-dropdown')
});

$('#type-dropdown').change(async function () {
	let typeId = $(this).val();
	$('#shape-dropdown').empty();
	if (typeId) {
		const data = await fetchShapesByType(typeId)
		$('#shape-dropdown').append('<option value="">Select Shape</option>');
		$.each(data, function (key, shape) {
			$('#shape-dropdown').append(`<option value="${shape.id}">${shape.name}</option>`);
		});
	}
	else {
		$('#shape-dropdown').append('<option value="">Select Shape</option>');
	}
});

$('#datalayers-container').on('change', '.datalayer-dropdown', function () {
    handleDropdownChange($(this));
});

$('#load-button').click(async function () {
    const shapeId = $('#shape-dropdown').val();
    const shapeName = $('#shape-dropdown').find("option:selected").text();
	$('#normalized-graph-container').empty();
	$('#raw-graphs-container').empty();
	$('#error-graphs-container').empty();

    let dataLayerData = {};

    createNormalizedGraph(shapeName);

    const dropdowns = $('.datalayer-dropdown');

    for (const dropdown of dropdowns) {
        const dataLayerKey = $(dropdown).val();
        if (dataLayerKey) {
            const data = await fetchHistoricalData(dataLayerKey, shapeId);
            const { historical_data: historicalData } = data;
            dataLayerData[dataLayerKey] = historicalData;
            const dataLayerName = $(dropdown).find("option:selected").text();
            const dropdownId = $(dropdown).attr('id');
            const dropdownNumber = dropdownId.match(/datalayer-(\S+)-dropdown/)[1];

            if (historicalData.length > 0) {
                createNewGraph(shapeId, dataLayerKey, dataLayerName, parseInt(dropdownNumber), dataLayerData[dataLayerKey]);
                addNormalizedTraceToGraph(dataLayerName, dataLayerData[dataLayerKey]);
            } else {
                createErrorContainer(dataLayerKey, dataLayerName, parseInt(dropdownNumber));
            }
        }
    }
});


let datalayerCount = 1;

function populateDatalayerDropdown(dropdownElement) {
	datalayers.forEach(datalayer => {

		let newOption = `<option value="${datalayer.key}">${datalayer.name}</option>`;

		$(dropdownElement).append(newOption);
	});
}

function addDataLayerDropdown() {
	let newDropdown = `
		<label for="datalayer-${datalayerCount + 1}-dropdown" class="form-label fw-bold">Select Data Layer ${datalayerCount + 1}:</label>
		<select id="datalayer-${datalayerCount + 1}-dropdown" class="datalayer-dropdown form-select">
			<option value="">Select Data Layer</option>
		</select>`

	$('#datalayers-container').append(newDropdown)

	populateDatalayerDropdown(`#datalayer-${datalayerCount + 1}-dropdown`)

	datalayerCount += 1
}

function handleDropdownChange(dropdown) {
	const dropdownId = dropdown.attr("id");

	if (dropdownId === `datalayer-${datalayerCount}-dropdown` && dropdown.value !== "") {
		addDataLayerDropdown();
	}
}

function createNewGraph(shapeId, dataLayerKey, dataLayerName, dropdownNumber, historicalData) {
	let newGraph = `
        <div class="col-6 mb-3">
            <div id="graph-${dataLayerKey}" style="width: 100%; height: 250px;">
            </div>
        </div>`;

	if ($('#raw-graphs-container .row').length === 0 || $('#raw-graphs-container .row').last().children().length === 2) {
		$('#raw-graphs-container').append('<div class="row">');
	}

	$('#raw-graphs-container .row').last().append(newGraph);

	let traces = [];
	if (historicalData.length > 0) {
		traces.push({
			x: historicalData.map(d => d.year),
			y: historicalData.map(d => d.value),
			mode: 'lines+markers',
			showlegend: false,
			name: dataLayerKey,
		});

		let layout = {
			title: `<b>Data Layer ${dropdownNumber}: ${dataLayerName}<br>${dataLayerKey}</b>`,
			// title: 'Data Layer ' + dropdownNumber + ': ' + dataLayerName + ' - ' + dataLayerKey,
			xaxis: {title: 'Year'},
			yaxis: {title: 'Value'},
			width: null,
			height: 250
		};

		Plotly.newPlot($(`#graph-${dataLayerKey}`)[0], traces, layout);
	}
}

function createNormalizedGraph(shapeName) {
	let newNormalizedGraph = `
        <div id="normalized-graph">
        </div>`;
	$('#normalized-graph-container').append(newNormalizedGraph);

	let layout = {
		title: `<b>Normalized Graph for ${shapeName}</b>`,
		xaxis: {title: 'Year'},
		yaxis: {title: 'Value'},
		width: null,
		height: 400
	};
	Plotly.newPlot($('#normalized-graph')[0], [], layout);
}

function createErrorContainer(dataLayerKey, dataLayerName, dropdownNumber){
	let newContainer = `<div class="border rounded m-2 text-center" id="error-container-${dataLayerKey}">
		<label class="form-label text-danger">Data Layer ${dropdownNumber}: ${dataLayerName} - ${dataLayerKey} not found!</label>
        </div>`;
	$('#error-graphs-container').append(newContainer);
}

function addNormalizedTraceToGraph(dataLayerName, historicalData) {
    let allData = historicalData.map(d => d.value);

    const min = Math.min(...allData);
    const max = Math.max(...allData);
    let normalizedValues;

    if (min === max) {
        normalizedValues = historicalData.map(() => 0.5);
    } else {
        normalizedValues = historicalData.map(d => normalize(d.value, min, max));
    }

    Plotly.addTraces($('#normalized-graph')[0], [{
        x: historicalData.map(d => d.year),
        y: normalizedValues,
        mode: 'lines+markers',
        showlegend: true,
        name: dataLayerName,
    }]);
}

function normalize(value, min, max) {
    return (value - min) / (max - min);
}

