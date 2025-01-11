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

    let dataLayerData = {};

	createNormalizedGraph(shapeName)

    $('.datalayer-dropdown').each(async function () {
        const dataLayerKey = $(this).val();
        if (dataLayerKey) {
            const data = await fetchHistoricalData(dataLayerKey, shapeId);
			const {historical_data: historicalData} = data
            dataLayerData[dataLayerKey] = historicalData;
			if (historicalData) {
				const dataLayerName = $(this).find("option:selected").text();
        		const dropdownId = $(this).attr('id');
        		const dropdownNumber = dropdownId.match(/datalayer-(\S+)-dropdown/)[1];
				createNewGraph(shapeId, dataLayerKey, dataLayerName, parseInt(dropdownNumber), dataLayerData[dataLayerKey]);
				addNormalizedTraceToGraph(dataLayerName, dataLayerData[dataLayerKey])
			}
        }
    });
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
        <div class="border rounded m-2" id="graph-${dataLayerKey}">
        </div>`;
    $('#graphs-container').append(newGraph);

    let traces = [];
    if (historicalData.length > 0) {
        traces.push({
            x: historicalData.map(d => d.year),
            y: historicalData.map(d => d.value),
            mode: 'lines+markers',
            showlegend: true,
            name: dataLayerKey,
        });

        let layout = {
            title: 'Data Layer ' + dropdownNumber + ': ' + dataLayerName + ' - ' + dataLayerKey,
            xaxis: { title: 'Year' },
            yaxis: { title: 'Value' },
            width: 1250,
            height: 400
        };

        Plotly.newPlot($(`#graph-${dataLayerKey}`)[0], traces, layout);
    }
}

function createNormalizedGraph(shapeName) {
	let newNormalizedGraph = `
        <div class="border rounded m-2" id="normalized-graph">
        </div>`;
	$('#graphs-container').append(newNormalizedGraph);

	let layout = {
		title: 'Normalized Graph for ' + shapeName,
		xaxis: {title: 'Year'},
		yaxis: {title: 'Value'},
		width: 1250,
		height: 400
	};
	Plotly.newPlot($('#normalized-graph')[0], [], layout);
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

