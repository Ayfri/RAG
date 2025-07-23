/**
 * OpenAI models store with automatic loading
 */

import { writable } from 'svelte/store';
import { persistentStore } from './persistentStore.js';

export interface OpenAIModel {
	id: string;
	name: string;
	created: string;
	year: number;
}

/**
 * Store for OpenAI models, categorized by type
 */
export interface OpenAIModels {
	chat: OpenAIModel[];
	embedding: OpenAIModel[];
	thinking: OpenAIModel[];
}

const defaultModels: OpenAIModels = {
	chat: [],
	embedding: [],
	thinking: []
};

export const openaiModels = persistentStore<OpenAIModels>('openai-models', defaultModels);

const isLoading = writable(false);

/**
 * Get loading state
 */
export function getModelsLoadingState() {
	return isLoading;
}

/**
 * Fetch and store OpenAI models from the API
 */
export async function loadOpenAIModels(force = false) {
	let currentModels: OpenAIModels;
	const unsubscribe = openaiModels.subscribe(value => currentModels = value);
	unsubscribe();

	if (!force && (currentModels!.chat.length > 0 || currentModels!.embedding.length > 0)) {
		return currentModels!;
	}

	try {
		isLoading.set(true);

		const response = await fetch('/api/models');

		if (!response.ok) {
			throw new Error(`Failed to fetch models: ${response.status}`);
		}

		const models: OpenAIModels = await response.json();
		openaiModels.set(models);

		return models;
	} catch (error) {
		console.error('Failed to fetch OpenAI models:', error);
		throw error;
	} finally {
		isLoading.set(false);
	}
}

/**
 * Get models, loading them if not already loaded
 */
export async function getOpenAIModels() {
	return await loadOpenAIModels(false);
}
