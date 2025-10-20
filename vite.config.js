// SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
//
// SPDX-License-Identifier: AGPL-3.0-only

import fs from 'fs';
import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import { sveltePreprocess } from 'svelte-preprocess';

/**
 * Simple plugin to create a "hot" file while dev mode is running. tThis file contains
 * host:port of the dev server (the port might change if it's already in use)!
 *
 * Adapted von laravel/blade integration of vite, from the vite-laravel plugin:
 * https://github.com/laravel/vite-plugin/blob/7271dcd048a8450afc92d9cb861e2795b2b43ec6/src/index.ts#L209
 *
 */
// SPDX-SnippetBegin
// SPDX-SnippetCopyrightText: Taylor Otwell
// SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
//
// SPDX-License-Identifier: MIT
const hotFilePlugin = () => ({
	name: 'hotfile-server',
	configureServer(server) {

		function isIpv6(address) {
			return address.family === 'IPv6'
				// In node >=18.0 <18.4 this was an integer value. This was changed in a minor version.
				// See: https://github.com/laravel/vite-plugin/issues/103
				// eslint-disable-next-line @typescript-eslint/ban-ts-comment
				// @ts-ignore-next-line
				|| address.family === 6;
		}

		/**
		 * Resolve the dev server URL from the server address and configuration.
		 */
		function resolveDevServerUrl(address, config, userConfig) {
			const configHmrProtocol = typeof config.server.hmr === 'object' ? config.server.hmr.protocol : null
			const clientProtocol = configHmrProtocol ? (configHmrProtocol === 'wss' ? 'https' : 'http') : null
			const serverProtocol = config.server.https ? 'https' : 'http'
			const protocol = clientProtocol ?? serverProtocol

			const configHmrHost = typeof config.server.hmr === 'object' ? config.server.hmr.host : null
			const configHost = typeof config.server.host === 'string' ? config.server.host : null
			const sailHost = process.env.LARAVEL_SAIL && ! userConfig.server?.host ? 'localhost' : null
			const serverAddress = isIpv6(address) ? `[${address.address}]` : address.address
			const host = configHmrHost ?? sailHost ?? configHost ?? serverAddress

			const configHmrClientPort = typeof config.server.hmr === 'object' ? config.server.hmr.clientPort : null
			const port = configHmrClientPort ?? address.port

			return `${protocol}://${host}:${port}`
		}

		let exitHandlersBound = false;

		let hotFile = 'app/static/hot';

		server.httpServer?.once('listening', () => {
			const address = server.httpServer?.address()

			const isAddressInfo = (x) => typeof x === 'object'
			if (isAddressInfo(address)) {
				let viteDevServerUrl = resolveDevServerUrl(address, server.config, {})
				fs.writeFileSync(hotFile, `${viteDevServerUrl}${server.config.base.replace(/\/$/, '')}`)
			}
		})

		if (! exitHandlersBound) {
			const clean = () => {
				if (fs.existsSync(hotFile)) {
					fs.rmSync(hotFile)
				}
			}

			process.on('exit', clean)
			process.on('SIGINT', () => process.exit())
			process.on('SIGTERM', () => process.exit())
			process.on('SIGHUP', () => process.exit())

			exitHandlersBound = true
		}
	},
});
// SPDX-SnippetEnd

export default defineConfig({
	//root: 'app/resources',
	build: {
		// explicitly set path of manifest, the value true would lead to it being
		// created at ./.vite/ and Djangos collectstatic ignores dot folders
		manifest: "manifest.json",
		outDir: 'app/static/build',
		rollupOptions: {
			input: [
				'app/resources/js/app.js',
				'app/resources/css/app.css',
			]
		},

		minify: true,
	},
	plugins: [
		hotFilePlugin(),
		svelte({
			preprocess: sveltePreprocess(),
			/* plugin options */
			compilerOptions: {
				customElement: true,
			},
		})
	],
})
