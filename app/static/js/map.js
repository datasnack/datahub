function get_base_map(container, options = {}) {
	// allow local overwrite if required
	const config = {
		'lat':  DATAHUB.CENTER_Y,
		'lng':  DATAHUB.CENTER_X,
		'zoom': DATAHUB.CENTER_ZOOM,
	};
	let settings = {...config, ...options};

	var osmUrl       = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
	var osmAttrib    = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';
	var osm          = L.tileLayer(osmUrl, {maxZoom: 18, attribution: osmAttrib});
	var map_position = {lat: settings.lng, lng: settings.lng, zoom: settings.zoom};

	var map = L.map(container, {
		preferCanvas: true,
		loadingControl: true
	}).setView([map_position.lat, map_position.lng], map_position.zoom).addLayer(osm);

	L.control.scale({imperial: false}).addTo(map);

	return map;
}

function load_shape(map, query) {
	map.fire('dataloading');

	if (!query.hasOwnProperty('format')) {
		query['format'] = 'geojson';
	}
	query_string = new URLSearchParams(query).toString();

	$.getJSON(`/api/shapes/geometry/?${query_string}`, function(data) {
		var m = L.geoJSON(data, {
			onEachFeature: function (feature, layer) {
				const p = feature.properties;
				layer.bindPopup(`<h5 class="mb-0">${p['name']}</h5>
				<p class="mt-0 mb-1">
				<small class="text-muted">${p['type']}</small>
				</p>
				<a href="${p['url']}" class="">Details</a>`);
			}
		}).addTo(map);
		map.fitBounds(m.getBounds());

		map.fire('dataload');
	}).fail(function(data) {
		alert("Something went wrong during loading the geometry of the shape.");
		map.fire('dataload');
	});
}

function load_data_for_layer(map, dl, layerControl) {
  map.fire('dataloading');

  $.getJSON(`/api/v1/parameter_data_map/${dl.id}/2023`, function(data) {

    var markers = new L.MarkerClusterGroup({ disableClusteringAtZoom: 19});
		var markersList = [];

    var m = L.geoJSON(data['geojson'], {
      style: {
        color: 'red'
      },
      onEachFeature: function (feature, layer) {
        var html = "";
        Object.keys(feature.properties).forEach(function(key) {
          var value = feature.properties[key];

          // ignore empty values (not all properties are set on each feature)
          // this reduces the visual space needed for the popup!
          if (value == null) {
            return;
          }

          // the values of same special keys can be enhanced with additional formatting
          if (key == 'wikidata') {
            value = `<a href="https://www.wikidata.org/wiki/${value}" target="_blank">${value}</a>`;
          } else if (key == 'nodes') {
            // usually a long list of OSM ids
            value = value.substring(0, 20) + "…";
          } else if (key == 'meteostat_id') {
            value = `<a href="https://meteostat.net/de/station/${value}" target="_blank">${value}</a>`
          }

          html += `<tr><th><code>${key}</code></th><td>${value}</td>`;
        });

        layer.bindPopup(`<table><tbody>${html}</tbody></table>`);
      }

    });

    markersList.push(m);
		markers.addLayer(m);

    map.addLayer(markers);

    if (layerControl) {
      layerControl.addOverlay(markers, dl.id);
    }

    map.fire('dataload');
  }).fail(function(data) {
    alert("Something went wrong during loading the data.");
    map.fire('dataload');
  });
}




/**
 * https://leafletjs.com/examples/choropleth/
 */
function load_choropleth_map(map) {

}
