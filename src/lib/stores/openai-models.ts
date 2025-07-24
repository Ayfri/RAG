/**
 * OpenAI models store with automatic loading
 */

import { readable } from 'svelte/store';
import type { OpenAIModel } from '$lib/types';

export interface CategorizedOpenAIModels {
	chat: OpenAIModel[];
	embedding: OpenAIModel[];
	thinking: OpenAIModel[];
	special: OpenAIModel[];
}

export const openAIModels = readable<CategorizedOpenAIModels>({
	chat: [],
	embedding: [],
	thinking: [],
	special: []
}, set => {
	let mounted = true;

	async function fetchModels() {
		try {
			const res = await fetch('/api/models');
			if (!res.ok) {
				throw new Error('Failed to fetch models');
			}
			const data: CategorizedOpenAIModels = await res.json();
			if (mounted) {
				set(data);
			}
		} catch (error) {
			console.error('Error fetching OpenAI models:', error);
			if (mounted) {
				set({
					chat: [],
					embedding: [],
					thinking: [],
					special: []
				});
			}
		}
	}

	fetchModels();

	return () => {
		mounted = false;
	};
});
