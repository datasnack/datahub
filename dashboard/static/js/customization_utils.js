export function getColor(value, minValue, maxValue, presetColors) {
	const norm_val = (value - minValue) / (maxValue - minValue);
	if (norm_val > 0.8) return presetColors[4];
	if (norm_val > 0.6) return presetColors[3];
	if (norm_val > 0.4) return presetColors[2];
	if (norm_val > 0.2) return presetColors[1];
	return presetColors[0];
}

export function updateLegendBar(legendBar, presetColors, layout) {
    $(legendBar).empty();

    const parentDiv = $('<div>')
        .addClass('d-flex w-100')
        .addClass(layout === 'row' ? 'flex-row' : 'flex-column');

    presetColors.forEach(color => {
        const childDiv = $('<div>')
            .addClass('flex-fill')
            .css({
                background: color,
                height: layout === 'row' ? '10px' : '20px',
                width: layout === 'row' ? 'auto' : '10px',
            });
        parentDiv.append(childDiv);
    });

    $(legendBar).append(parentDiv);
}

export function applyPreset(presetColors, legendBar, transparencyInput, minValue, maxValue, layerGroup, dataLayerKey = null) {
	const defaultTransparency = 0.9;

    if (dataLayerKey) {
        updateLegendBar(legendBar, presetColors, 'column');
    } else {
        updateLegendBar(legendBar, presetColors, 'row');
    }

    const transparency = transparencyInput ? parseFloat(transparencyInput) : defaultTransparency;

    layerGroup.eachLayer(layer => {
        if (layer._layers) {
            Object.values(layer._layers).forEach(subLayer => {
                if (subLayer.feature && subLayer.feature.properties) {
                    const value = dataLayerKey
                        ? subLayer.feature.properties.value
                        : subLayer.feature.properties.availableCount;

                    const color = getColor(value, minValue, maxValue, presetColors);
                    subLayer.setStyle({
                        fillColor: color,
                        fillOpacity: transparency,
                    });
                } else {
                    console.warn('Sub-layer lacks feature or properties:', subLayer);
                }
            });
        }
    });
}
