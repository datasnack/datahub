// SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
//
// SPDX-License-Identifier: AGPL-3.0-only

class ScreenshotControl {
  constructor({ title = "Take Screenshot", filename = "map-screenshot.png" } = {}) {
    this._map = null;
    this._container = null;
    this._title = title;
    this._filename = filename;
  }

  onAdd(map) {
    this._map = map;

    this._container = document.createElement("div");
    this._container.className = "maplibregl-ctrl maplibregl-ctrl-group";

    const button = document.createElement("button");
    button.type = "button";
    button.title = this._title;
    button.innerHTML = "📸";
    button.onclick = () => this._takeScreenshot();

    this._container.appendChild(button);
    return this._container;
  }

  onRemove() {
    this._container.remove();
    this._map = null;
  }

  _takeScreenshot() {
    this._capture().then(dataURL => {
      const link = document.createElement("a");
      link.download = this._filename;
      link.href = dataURL;
      link.click();
    });
  }

  _capture() {
    return new Promise((resolve) => {
      this._map.once("render", () => {
        resolve(this._map.getCanvas().toDataURL("image/png"));
      });
      // Trigger a re-render
      this._map.setBearing(this._map.getBearing());
    });
  }
}


export default ScreenshotControl;
