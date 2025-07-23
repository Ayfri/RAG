<script lang="ts">
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';

	import '../app.css';
	import { getOpenAIModels } from '$lib/stores/openai-models.js';

	let { children } = $props();

	// Load OpenAI models on app startup
	onMount(async () => {
		if (browser) {
			try {
				await getOpenAIModels();
				console.log('OpenAI models loaded');
			} catch (error) {
				console.warn('Failed to load OpenAI models on startup:', error);
			}
		}
	});
</script>

{@render children()}
