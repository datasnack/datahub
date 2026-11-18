// SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
//
// SPDX-License-Identifier: AGPL-3.0-only

class FullScreenControl {

    constructor(options = {}) {
        this._fullscreen = false;

        if (options && options.container) {
            if (options.container instanceof HTMLElement) {
                this._container = options.container;
            } else {
                warnOnce('Full screen control \'container\' must be a DOM element.');
            }
        }

        if ('onfullscreenchange' in document) {
            this._fullscreenchange = 'fullscreenchange';
        } else if ('onmozfullscreenchange' in document) {
            this._fullscreenchange = 'mozfullscreenchange';
        } else if ('onwebkitfullscreenchange' in document) {
            this._fullscreenchange = 'webkitfullscreenchange';
        } else if ('onmsfullscreenchange' in document) {
            this._fullscreenchange = 'MSFullscreenChange';
        }
    }

	onAdd(map) {
        this._map = map;

        if (!this._container) this._container = this._map.getContainer();

		this._controlContainer = document.createElement("div");
    	this._controlContainer.className = "maplibregl-ctrl maplibregl-ctrl-group";

        this._setupUI();
        return this._controlContainer;
    }

    /** {@inheritDoc IControl.onRemove} */
    onRemove(map) {
		this._controlContainer.remove();
		this._map = null;
        window.document.removeEventListener(this._fullscreenchange, this._onFullscreenChange);
    }


    _setupUI() {
		const button = this._fullscreenButton = document.createElement("button");
		button.type = "button";
		button.className = "maplibregl-ctrl-fullscreen";

		const span = document.createElement("span");
		span.className = "maplibregl-ctrl-icon";
		span.setAttribute('aria-hidden', 'true');

		button.appendChild(span);

        this._updateTitle();
        this._fullscreenButton.addEventListener('click', this._onClickFullscreen);
        window.document.addEventListener(this._fullscreenchange, this._onFullscreenChange);

		this._controlContainer.appendChild(button);
    }

    _updateTitle() {
        const title = this._getTitle();
        this._fullscreenButton.setAttribute('aria-label', title);
        this._fullscreenButton.title = title;
    }

    _getTitle() {
        return this._map._getUIString(this._isFullscreen() ? 'FullscreenControl.Exit' : 'FullscreenControl.Enter');
    }

    _isFullscreen() {
        return this._fullscreen;
    }

    _onFullscreenChange = () => {
        let fullscreenElement =
            window.document.fullscreenElement ||
            (window.document).mozFullScreenElement ||
            (window.document).webkitFullscreenElement ||
            (window.document).msFullscreenElement;

        while (fullscreenElement?.shadowRoot?.fullscreenElement) {
            fullscreenElement = fullscreenElement.shadowRoot.fullscreenElement;
        }

        if ((fullscreenElement === this._container) !== this._fullscreen) {
            this._handleFullscreenChange();
        }
    };

    _handleFullscreenChange() {
        this._fullscreen = !this._fullscreen;
        this._fullscreenButton.classList.toggle('maplibregl-ctrl-shrink');
        this._fullscreenButton.classList.toggle('maplibregl-ctrl-fullscreen');
        this._updateTitle();

        if (this._fullscreen) {
            this.fire(new Event('fullscreenstart'));
            this._prevCooperativeGesturesEnabled = this._map.cooperativeGestures.isEnabled();
            this._map.cooperativeGestures.disable();
        } else {
            this.fire(new Event('fullscreenend'));
            if (this._prevCooperativeGesturesEnabled) {
                this._map.cooperativeGestures.enable();
            }
        }
    }

    _onClickFullscreen = () => {
        if (this._isFullscreen()) {
            this._exitFullscreen();
        } else {
            this._requestFullscreen();
        }
    };

    _exitFullscreen() {
        this._togglePseudoFullScreen();
    }

    _requestFullscreen() {
        this._togglePseudoFullScreen();
    }



    _togglePseudoFullScreen() {
        this._container.classList.toggle('maplibregl-pseudo-fullscreen');
        this._handleFullscreenChange();
        this._map.resize();
    }

}

export default FullScreenControl;
