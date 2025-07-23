/**
 * Creates a persistent store that syncs with localStorage using Svelte stores.
 */

import { browser } from '$app/environment';
import { writable } from 'svelte/store';

/**
 * Creates a Svelte writable store that automatically persists its value
 * to localStorage and initializes from localStorage if a value exists,
 * handling SSR correctly.
 * @param key The key to use for localStorage.
 * @param initialValue The initial value to use if nothing is found in localStorage or on the server.
 */
export function persistentStore<T>(key: string, initialValue: T) {
	const keyName = `rag-app-${key}`;
	let value = initialValue;

	if (browser) {
		const storedString = localStorage.getItem(keyName);
		if (storedString !== null) {
			try {
				value = JSON.parse(storedString);
			} catch (e) {
				localStorage.removeItem(keyName);
			}
		}
	}

	const store = writable(value);

	if (browser) {
		store.subscribe(currentValue => {
			if (currentValue !== undefined && currentValue !== null) {
				localStorage.setItem(keyName, JSON.stringify(currentValue));
			} else {
				localStorage.removeItem(keyName);
			}
		});
	}

	return store;
}
