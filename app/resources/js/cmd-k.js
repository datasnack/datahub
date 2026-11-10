/**
 * SPDX-FileCopyrightText: 2026 Jonathan Ströbele <mail@jonathanstroebele.de>
 *
 * SPDX-License-Identifier: AGPL-3.0-only
 *
 *
 * CmdK Search Component
 * A vanilla JS web component for command palette-style search
 *
 * Usage:
 * <cmd-k endpoint="/api/search" debounce="300" min-chars="2">
 *   <form action="/search" method="get">
 *     <input type="search" name="q" placeholder="Search...">
 *   </form>
 * </cmd-k>
 */

class CmdK extends HTMLElement {
  constructor() {
    super();

    this.useShadow = true;

    this.root = this.useShadow
      ? this.attachShadow({ mode: "open" })
      : this;

    // State
    this.isOpen = false;
    this.results = [];
    this.selectedIndex = -1;
    this.searchTimeout = null;
    this.controller = null;

    // Bindings
    this.handleKeydown = this.handleKeydown.bind(this);
    this.handleInput = this.handleInput.bind(this);
    this.handleResultClick = this.handleResultClick.bind(this);
    this.close = this.close.bind(this);
  }

  static get observedAttributes() {
    return ['endpoint', 'debounce', 'min-chars', 'placeholder', 'shortcut'];
  }

  connectedCallback() {
    this.render();
    this.setupEventListeners();
    this.registerKeyboardShortcut();
    this.renderSearchButton();
  }

  disconnectedCallback() {
    this.cleanup();
  }

  // Getters for component configuration
  get endpoint() {
    return this.getAttribute('endpoint') || '/api/search';
  }

  get debounce() {
    return parseInt(this.getAttribute('debounce') || '300', 10);
  }

  get minChars() {
    return parseInt(this.getAttribute('min-chars') || '2', 10);
  }

  get placeholder() {
    return this.getAttribute('placeholder') || 'Search...';
  }

  get shortcut() {
    return this.getAttribute('shortcut') || 'k';
  }

  // Template system - check for custom template
  get resultTemplate() {
    const customTemplate = this.querySelector('template[slot="result-template"]');
    if (customTemplate) {
      return customTemplate.innerHTML;
    }
    return this.defaultResultTemplate;
  }

  get defaultResultTemplate() {
    return `
      <div class="result-icon">\${icon}</div>
      <div class="result-content">
        <div class="result-title">\${title} (<small><code>\${key}</code></small>)</div>
        <div class="result-description">\${description}</div>
      </div>
      <div class="result-meta">\${meta}</div>
    `;
  }

  render() {
    const styles = `
      <style>
        :host {
          --cmd-k-bg: rgba(0, 0, 0, 0.8);
          --cmd-k-modal-bg: light-dark(#ffffff, oklch(37.3% 0.034 259.733));
          --cmd-k-modal-border: light-dark(oklch(92.8% 0.006 264.531), oklch(44.6% 0.03 256.802));
          --cmd-k-modal-shadow: 0 16px 70px rgba(0, 0, 0, 0.3);
          --cmd-k-input-border: #e0e0e0;
          --cmd-k-input-focus: oklch(54.6% 0.245 262.881);
          --cmd-k-result-hover: #f5f5f5;
          --cmd-k-result-selected: #e0e7ff;
          --cmd-k-text: light-dark( #1f2937, oklch(44.6% 0.03 256.802));
          --cmd-k-text-secondary: #6b7280;
          --cmd-k-group-bg: #f9fafb;
          --cmd-k-border-radius: .5rem;

          --cmd-k-trigger-bg: light-dark(oklch(98.5% 0.002 247.839), oklch(21% 0.034 264.665));
          --cmd-k-trigger-border: light-dark(oklch(0.872 0.01 258.338), oklch(55.1% 0.027 264.364));
          --cmd-k-trigger-color: light-dark(oklch(44.6% 0.03 256.802), oklch(87.2% 0.01 258.338));
        }

        @media (prefers-color-scheme: dark) {
            :host {
                color-scheme: dark;
            }
        }

        .cmd-k-backdrop {
          display: none;
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: var(--cmd-k-bg);
          z-index: 9999;
        }

        .cmd-k-backdrop.open {
          display: flex;
          align-items: flex-start;
          justify-content: center;
          padding-top: 15vh;
        }

        .cmd-k-modal {
          background: var(--cmd-k-modal-bg);
          border-radius: var(--cmd-k-border-radius);
          border: 1px solid var(--cmd-k-modal-border);
          box-shadow: var(--cmd-k-modal-shadow);
          width: 90%;
          max-width: 640px;
          max-height: 70vh;
          display: flex;
          flex-direction: column;
        }

        .cmd-k-search {
          padding: 16px;
          border-bottom: 1px solid var(--cmd-k-input-border);
        }

        .cmd-k-input {
          width: 100%;
          padding: 12px 16px;
          font-size: 16px;
          border: 2px solid var(--cmd-k-input-border);
          border-radius: var(--cmd-k-border-radius);
          outline: none;
          color: var(--cmd-k-text);
          transition: border-color 0.2s;
        }

        .cmd-k-input:focus {
          border-color: var(--cmd-k-input-focus);
        }

        .cmd-k-results {
          overflow-y: auto;
          max-height: calc(70vh - 100px);
        }

        .cmd-k-group {
          margin: 0;
        }

        .cmd-k-group-title {
          padding: 8px 16px;
          font-size: 12px;
          font-weight: 600;
          text-transform: uppercase;
          color: var(--cmd-k-text-secondary);
          background: var(--cmd-k-group-bg);
          letter-spacing: 0.05em;
          position: sticky;
          top: 0;
        }

        .cmd-k-result {
          display: flex;
          align-items: center;
          padding: 12px 16px;
          cursor: pointer;
          border-bottom: 1px solid var(--cmd-k-input-border);
          transition: background-color 0.15s;
          gap: 12px;
		  text-decoration: none;
        }

        .cmd-k-result:last-child {
          border-bottom: none;
        }

        .cmd-k-result:hover {
          background: var(--cmd-k-result-hover);
        }

        .cmd-k-result.selected {
          background: var(--cmd-k-result-selected);
        }

        .result-icon {
          width: 32px;
          height: 32px;
          flex-shrink: 0;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 20px;
        }

        .result-icon:empty {
          display: none;
        }

        .result-content {
          flex: 1;
          min-width: 0;
        }

        .result-title {
          font-weight: 500;
          color: var(--cmd-k-text);
          margin-bottom: 2px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .result-description {
          font-size: 14px;
          color: var(--cmd-k-text-secondary);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .result-description:empty {
          display: none;
        }

        .result-meta {
          font-size: 12px;
          color: var(--cmd-k-text-secondary);
          flex-shrink: 0;
        }

        .result-meta:empty {
          display: none;
        }

        .cmd-k-empty,
        .cmd-k-loading {
          padding: 48px 16px;
          text-align: center;
          color: var(--cmd-k-text-secondary);
        }

        .cmd-k-spinner {
          display: inline-block;
          width: 24px;
          height: 24px;
          border: 3px solid var(--cmd-k-input-border);
          border-top-color: var(--cmd-k-input-focus);
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .cmd-k-footer {
          padding: 12px 16px;
          border-top: 1px solid var(--cmd-k-input-border);
          font-size: 12px;
          color: var(--cmd-k-text-secondary);
          display: flex;
          justify-content: space-between;
        }

        .cmd-k-hint {
          display: flex;
          gap: 16px;
        }

        .cmd-k-hint span {
          display: flex;
          align-items: center;
          gap: 4px;
        }

        .cmd-k-key {
          background: var(--cmd-k-group-bg);
          padding: 2px 6px;
          border-radius: 4px;
          font-family: monospace;
          font-size: 11px;
        }

        .cmd-k-trigger {
            font-size: 14px;
            background: none;
            border: 1px solid var(--cmd-k-trigger-border);
            border-radius: 0.5rem;
            padding: 6px 4px 6px 12px;
        }

        .cmd-k-trigger-keys {
            border: 1px solid var(--cmd-k-trigger-border);
            border-radius: 0.25rem;
            padding: 0 4px;
            margin-left: 0.5rem;
            background: var(--cmd-k-trigger-bg);
            color: var(--cmd-k-trigger-color);
        }

        @media (width < 48rem) {
            .cmd-k-trigger-keys {
                display: none;
            }

            .cmd-k-trigger-label {
                color: var(--cmd-k-trigger-color);
                background-image: url("data:image/svg+xml,%3Csvg width='24' height='24' viewBox='0 0 24 24' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Ccircle cx='10.5' cy='10.5' r='5.75' stroke='currentColor' stroke-width='1.5' /%3E%3Cpath d='M15 15L20 20' stroke='currentColor' stroke-width='1.5' stroke-linecap='round' /%3E%3C/svg%3E");
                text-indent: -500%;
                white-space: nowrap;
                display: block;
                overflow: hidden;
                width: 1.5em;
                background-position: center;
                background-repeat: no-repeat;
            }

        @media (prefers-color-scheme: dark) {
            .cmd-k-trigger-label {
                background-image: url("data:image/svg+xml,%3Csvg width='24' height='24' viewBox='0 0 24 24' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Ccircle cx='10.5' cy='10.5' r='5.75' stroke='oklch(87.2% 0.01 258.338)' stroke-width='1.5' /%3E%3Cpath d='M15 15L20 20' stroke='oklch(87.2% 0.01 258.338)' stroke-width='1.5' stroke-linecap='round' /%3E%3C/svg%3E");
            }
        }

            .cmd-k-trigger {
                padding-left: 6px;
            }

        }

        mark {
          background: #fef08a;
          padding: 0 2px;
          border-radius: 2px;
        }
      </style>
    `;

    const template = `
      ${styles}
      <div class="cmd-k-backdrop" part="backdrop">
        <div class="cmd-k-modal" part="modal">
          <div class="cmd-k-search">
            <input
              type="search"
              class="cmd-k-input"
              placeholder="${this.placeholder}"
              autocomplete="off"
              spellcheck="false"
              part="input"
            >
          </div>
          <div class="cmd-k-results" part="results"></div>
          <div class="cmd-k-footer" part="footer">
            <div class="cmd-k-hint">
              <span><kbd class="cmd-k-key">↑↓</kbd> Navigate</span>
              <span><kbd class="cmd-k-key">↵</kbd> Select</span>
              <span><kbd class="cmd-k-key">Esc</kbd> Close</span>
            </div>
          </div>
        </div>
      </div>
    `;

    this.root.innerHTML = template;
  }

  setupEventListeners() {
    this.backdrop = this.root.querySelector('.cmd-k-backdrop');
    this.modal = this.root.querySelector('.cmd-k-modal');
    this.input = this.root.querySelector('.cmd-k-input');
    this.resultsContainer = this.root.querySelector('.cmd-k-results');

    // Input events
    this.input.addEventListener('input', this.handleInput);
    this.input.addEventListener('keydown', this.handleKeydown);

    // Click outside to close
    this.backdrop.addEventListener('click', (e) => {
      if (e.target === this.backdrop) {
        this.close();
      }
    });

    // Prevent modal click from closing
    this.modal.addEventListener('click', (e) => {
      e.stopPropagation();
    });
  }

  registerKeyboardShortcut() {
    this.shortcutHandler = (e) => {
      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
      const modifier = isMac ? e.metaKey : e.ctrlKey;

      if (modifier && e.key.toLowerCase() === this.shortcut.toLowerCase()) {
        e.preventDefault();

        if (!this.isOpen) {
            this.open();
        } else {
            this.close();
        }
      }

      // Also handle Escape globally
      if (e.key === 'Escape' && this.isOpen) {
        this.close();
      }
    };

    document.addEventListener('keydown', this.shortcutHandler);
  }

  handleKeydown(e) {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        this.selectNext();
        break;
      case 'ArrowUp':
        e.preventDefault();
        this.selectPrevious();
        break;
      case 'Enter':
        e.preventDefault();
        this.selectCurrent();
        break;
      case 'Escape':
        e.preventDefault();
        this.close();
        break;
    }
  }

  handleInput(e) {
    const query = e.target.value.trim();

    // Clear previous timeout
    if (this.searchTimeout) {
      clearTimeout(this.searchTimeout);
    }

    // Dispatch search event
    this.dispatchEvent(new CustomEvent('cmd-k:search', {
      detail: { query },
      bubbles: true,
      composed: true
    }));

    if (query.length < this.minChars) {
      this.showEmpty('Type at least ' + this.minChars + ' characters to search');
      return;
    }

    // Show loading state
    this.showLoading();

    // Debounced search
    this.searchTimeout = setTimeout(() => {
      this.performSearch(query);
    }, this.debounce);
  }

  async performSearch(query) {
    // Cancel previous request
    if (this.controller) {
      this.controller.abort();
    }

    this.controller = new AbortController();

    try {
      const url = new URL(this.endpoint, window.location.origin);
      url.searchParams.set('q', query);

      const response = await fetch(url.toString(), {
        signal: this.controller.signal,
        headers: {
          'Accept': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      this.results = data.results || [];
      this.groups = data.groups || [];

      if (this.results.length === 0) {
        this.showEmpty('No results found for "' + query + '"');
      } else {
        this.renderResults(query);
      }

    } catch (error) {
      if (error.name === 'AbortError') {
        return; // Request was cancelled
      }
      console.error('Search error:', error);
      this.showEmpty('An error occurred. Please try again.');
    }
  }

  renderResults(query) {
    this.selectedIndex = -1;
    const resultsHTML = [];

    if (this.groups && this.groups.length > 0) {
      // Grouped results
      this.groups.forEach(groupName => {
        const groupResults = this.results.filter(r => r.group === groupName);
        if (groupResults.length > 0) {
          resultsHTML.push(`<div class="cmd-k-group">`);
          resultsHTML.push(`<div class="cmd-k-group-title">${this.escapeHtml(groupName)}</div>`);
          groupResults.forEach((result, index) => {
            resultsHTML.push(this.renderResult(result, index, query));
          });
          resultsHTML.push(`</div>`);
        }
      });
    } else {
      // Ungrouped results
      this.results.forEach((result, index) => {
        resultsHTML.push(this.renderResult(result, index, query));
      });
    }

    this.resultsContainer.innerHTML = resultsHTML.join('');
    this.selectNext(); // select first result by default
    this.attachResultListeners();
  }

  renderResult(result, index, query) {

	console.log(result);
	const template = this.resultTemplate;


	// Prepare data with defaults
    const data = {
      id: result.id || index,
      title: result.label || '',
      description: result.description || '',
      url: result.url || '#',
      icon: result.icon || '',
      meta: result.meta || '',
      key: result.key || '',
      group: result.group || ''
    };

    // Simple template replacement
    let html = template.replace(/\$\{(\w+)\}/g, (match, key) => {
      return this.escapeHtml(data[key] || '', query);
    });

    return `<a class="cmd-k-result" data-index="${index}" href="${this.escapeHtml(data.url)}" data-url="${this.escapeHtml(data.url)}">${html}</a>`;
  }

attachResultListeners() {
  this.mouseHasMoved = false;

  // Only enable hover selection after the mouse actually moves.
  // This prevents phantom mouseenter events firing when results
  // render under a stationary cursor.
  this.mouseMoveHandler = () => {
    this.mouseHasMoved = true;
    this.resultsContainer.removeEventListener('mousemove', this.mouseMoveHandler);
  };
  this.resultsContainer.addEventListener('mousemove', this.mouseMoveHandler);

  const results = this.resultsContainer.querySelectorAll('.cmd-k-result');
  results.forEach((result, index) => {
    result.addEventListener('click', () => this.handleResultClick(index));
    result.addEventListener('mouseenter', () => {
      if (this.mouseHasMoved) {
        this.setSelected(index);
      }
    });
  });
}

  handleResultClick(index) {
    this.selectedIndex = index;
    this.selectCurrent();
  }

  selectNext() {
    const results = this.resultsContainer.querySelectorAll('.cmd-k-result');
    if (results.length === 0) return;

    this.selectedIndex = (this.selectedIndex + 1) % results.length;
    this.setSelected(this.selectedIndex);
    this.scrollToSelected();
  }

  selectPrevious() {
    const results = this.resultsContainer.querySelectorAll('.cmd-k-result');
    if (results.length === 0) return;

    this.selectedIndex = this.selectedIndex <= 0 ? results.length - 1 : this.selectedIndex - 1;
    this.setSelected(this.selectedIndex);
    this.scrollToSelected();
  }

  setSelected(index) {
    const results = this.resultsContainer.querySelectorAll('.cmd-k-result');
    results.forEach((el, i) => {
      el.classList.toggle('selected', i === index);
    });
    this.selectedIndex = index;
  }

  scrollToSelected() {
    const results = this.resultsContainer.querySelectorAll('.cmd-k-result');
    const selected = results[this.selectedIndex];
    if (selected) {
      selected.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
  }

  selectCurrent() {
    if (this.selectedIndex < 0 || this.selectedIndex >= this.results.length) return;

    const result = this.results[this.selectedIndex];

    // Dispatch select event
    this.dispatchEvent(new CustomEvent('cmd-k:select', {
      detail: { result },
      bubbles: true,
      composed: true
    }));

    // Navigate to URL
    if (result.url) {
      window.location.href = result.url;
    }

    this.close();
  }

  showLoading() {
    this.resultsContainer.innerHTML = `
      <div class="cmd-k-loading">
        <div class="cmd-k-spinner"></div>
      </div>
    `;
  }

  showEmpty(message = 'No results found') {
    this.resultsContainer.innerHTML = `
      <div class="cmd-k-empty">${this.escapeHtml(message)}</div>
    `;
  }

  open() {
    if (this.isOpen) return;

    this.isOpen = true;
    this.backdrop.classList.add('open');
    this.input.value = '';
    this.input.focus();
    this.showEmpty('Start typing to search...');

    // Dispatch open event
    this.dispatchEvent(new CustomEvent('cmd-k:open', {
      bubbles: true,
      composed: true
    }));

    // Prevent body scroll
    document.body.style.overflow = 'hidden';
  }

  close() {
    if (!this.isOpen) return;

    this.isOpen = false;
    this.backdrop.classList.remove('open');
    this.results = [];
    this.selectedIndex = -1;

    // Cancel any pending requests
    if (this.controller) {
      this.controller.abort();
    }

    // Dispatch close event
    this.dispatchEvent(new CustomEvent('cmd-k:close', {
      bubbles: true,
      composed: true
    }));

    // Restore body scroll
    document.body.style.overflow = '';
  }

  cleanup() {
    if (this.shortcutHandler) {
      document.removeEventListener('keydown', this.shortcutHandler);
    }
    if (this.searchTimeout) {
      clearTimeout(this.searchTimeout);
    }
    if (this.controller) {
      this.controller.abort();
    }
  }

  renderSearchButton() {
    // Check if there's a custom button slot
    const customButton = this.root.querySelector('[slot="search-button"]');
    if (customButton) {
        const content = customButton.content.cloneNode(true);
        content.addEventListener('click', () => this.open());
        this.parentNode.insertBefore(content, this);
        return;
    }


    // Check if we should render a default button
    if (this.hasAttribute('show-button')) {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'cmd-k-trigger';
      button.setAttribute('aria-label', 'Search');

      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
      const modKey = isMac ? '⌘' : 'Ctrl';

      button.innerHTML = `
        <span class="cmd-k-trigger-content">
          <span class="cmd-k-trigger-label">Search</span>
        </span>
        <span class="cmd-k-trigger-keys">
          <kbd class="cmd-k-trigger-key">${modKey}</kbd>
          <kbd class="cmd-k-trigger-key">K</kbd>
        </span>
      `;

        button.addEventListener('click', () => this.open());
       this.root.appendChild(button);
    }
  }

  // Utility functions
  escapeHtml(text, query = null) {
    const div = document.createElement('div');
    div.textContent = text;

    const safeString = div.innerHTML;

    if (query) {
        return this.highlightMatch(safeString, query)
    }

    return div.innerHTML;
  }

  highlightMatch(text, query) {
    if (!query || !text) return text;

    const regex = new RegExp(`(${this.escapeRegex(query)})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
  }

  escapeRegex(text) {
    return text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }
}

// Register the custom element
customElements.define('cmd-k', CmdK);
