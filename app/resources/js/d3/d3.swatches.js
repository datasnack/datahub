// Copyright 2021, Observable Inc.
// Released under the ISC license.
// https://observablehq.com/@d3/color-legend
export function Swatches(color, {
	columns = null,
	format,
	unknown: formatUnknown,
	swatchSize = 15,
	swatchWidth = swatchSize,
	swatchHeight = swatchSize,
	marginLeft = 0
  } = {}) {
	const id = `-swatches-${Math.random().toString(16).slice(2)}`;
	const unknown = formatUnknown == null ? undefined : color.unknown();
	const unknowns = unknown == null || unknown === d3.scaleImplicit ? [] : [unknown];
	const domain = color.domain().concat(unknowns);
	if (format === undefined) format = x => x === unknown ? formatUnknown : x;

	function entity(character) {
	  return `&#${character.charCodeAt(0).toString()};`;
	}

	// source of htmlToNode() https://stackoverflow.com/a/35385518
	function htmlToNode(html) {
		const template = document.createElement('template');
		template.innerHTML = html;
		const nNodes = template.content.childNodes.length;
		if (nNodes !== 1) {
			throw new Error(
				`html parameter must represent a single node; got ${nNodes}. ` +
				'Note that leading or trailing spaces around an element in your ' +
				'HTML, like " <img/> ", get parsed as text nodes neighbouring ' +
				'the element; call .trim() on your input to avoid this.'
			);
		}
		return template.content.firstChild;
	}


	if (columns !== null) return htmlToNode(`<div style="display: flex; align-items: center; margin-left: ${+marginLeft}px; min-height: 33px; font: 10px sans-serif;">
	<style>

  .${id}-item {
	break-inside: avoid;
	display: flex;
	align-items: center;
	padding-bottom: 1px;
  }

  .${id}-label {
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
	max-width: calc(100% - ${+swatchWidth}px - 0.5em);
  }

  .${id}-swatch {
	width: ${+swatchWidth}px;
	height: ${+swatchHeight}px;
	margin: 0 0.5em 0 0;
  }

	</style>
	<div style=${{width: "100%", columns}}>${domain.map(value => {
	  const label = `${format(value)}`;
	  return htl.html`<div class=${id}-item>
		<div class=${id}-swatch style=${{background: color(value)}}></div>
		<div class=${id}-label title=${label}>${label}</div>
	  </div>`;
	})}
	</div>
  </div>`);

	return htmlToNode(`<div style="display: flex; align-items: center; min-height: 33px; margin-left: ${+marginLeft}px; font: 10px sans-serif;">
	<style>

  .${id} {
	display: inline-flex;
	align-items: center;
	margin-right: 1em;
  }

  .${id}::before {
	content: "";
	width: ${+swatchWidth}px;
	height: ${+swatchHeight}px;
	margin-right: 0.5em;
	background: var(--color);
  }

	</style>
	<div>${domain.map(value => htmlToNode(`<span class="${id}" style="--color: ${color(value)}">${format(value)}</span>`).outerHTML)}</div>`);
  }
