<script lang="ts">
	import { X, Settings, Loader, CheckCircle } from '@lucide/svelte';
	import { fly } from 'svelte/transition';

	interface Props {
		ragName: string;
		onclose: () => void;
		onupdated: () => void;
	}

	let { ragName, onclose, onupdated }: Props = $props();

	interface RagConfig {
		chat_model: string;
		embedding_model: string;
		system_prompt: string;
	}

	let config: RagConfig = $state({
		chat_model: 'gpt-4o-mini',
		embedding_model: 'text-embedding-3-large',
		system_prompt: 'You are a helpful assistant that answers questions based on the provided context. Be concise and accurate.'
	});

	let loading = $state(false);
	let saving = $state(false);
	let error = $state('');
	let success = $state(false);

	const openaiModels = [
		'gpt-4o',
		'gpt-4o-mini',
		'gpt-4-turbo',
		'gpt-4',
		'gpt-3.5-turbo'
	];

	const embeddingModels = [
		'text-embedding-3-large',
		'text-embedding-3-small',
		'text-embedding-ada-002'
	];

	async function loadConfig() {
		try {
			loading = true;
			error = '';

			const response = await fetch(`/api/rag/${ragName}/config`);

			if (!response.ok) {
				throw new Error('Failed to load configuration');
			}

			const data = await response.json();
			config = { ...data };
		} catch (err) {
			error = err instanceof Error ? err.message : 'Unknown error';
		} finally {
			loading = false;
		}
	}

	async function saveConfig() {
		try {
			saving = true;
			error = '';
			success = false;

			const response = await fetch(`/api/rag/${ragName}/config`, {
				method: 'PUT',
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify(config),
			});

			if (!response.ok) {
				throw new Error('Failed to save configuration');
			}

			success = true;
			setTimeout(() => {
				onupdated();
				onclose();
			}, 1500);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Unknown error';
		} finally {
			saving = false;
		}
	}

	// Load config when component mounts
	$effect(() => {
		loadConfig();
	});
</script>

<!-- Modal backdrop -->
<div
	class="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50"
	in:fly={{ y: 20, duration: 300, delay: 50 }}
>
	<div class="glass rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
		<!-- Header -->
		<div class="flex justify-between items-center p-6 border-b border-slate-600 bg-gradient-to-r from-slate-800 to-slate-700">
			<div class="flex items-center space-x-3">
				<Settings class="w-6 h-6 text-cyan-400" />
				<h2 class="text-2xl font-bold text-slate-100">Configure RAG</h2>
			</div>
			<button onclick={onclose} class="text-slate-400 hover:text-slate-200 hover:bg-slate-700 p-2 rounded-xl transition-all duration-200 cursor-pointer">
				<X class="w-6 h-6" />
			</button>
		</div>

		<div class="p-6">
			{#if loading}
				<div class="text-center py-12">
					<Loader class="w-12 h-12 animate-spin text-cyan-400 mx-auto mb-4" />
					<p class="text-slate-400">Loading configuration...</p>
				</div>
			{:else if success}
				<div class="text-center py-12">
					<CheckCircle class="w-20 h-20 text-green-400 mx-auto mb-6" />
					<h3 class="text-2xl font-bold text-slate-100 mb-3">Configuration Updated!</h3>
					<p class="text-slate-400 text-lg">Settings for "{ragName}" have been saved.</p>
				</div>
			{:else}
				<form onsubmit={(e) => { e.preventDefault(); saveConfig(); }} class="space-y-6">
					<div class="bg-slate-800/50 rounded-xl p-4 border border-slate-600">
						<h3 class="text-lg font-semibold text-slate-100 mb-2">RAG: <span class="text-cyan-400">{ragName}</span></h3>
						<p class="text-slate-400 text-sm">Configure the OpenAI models and system prompt for this RAG instance.</p>
					</div>

					<!-- Chat Model Selection -->
					<div class="space-y-3">
						<label for="chat-model" class="block text-sm font-medium text-slate-200">
							Chat Model
						</label>
						<select
							id="chat-model"
							bind:value={config.chat_model}
							class="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-xl text-slate-100 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition-all duration-200 cursor-pointer"
						>
							{#each openaiModels as model}
								<option value={model}>{model}</option>
							{/each}
						</select>
						<p class="text-xs text-slate-500">The OpenAI model used for generating responses.</p>
					</div>

					<!-- Embedding Model Selection -->
					<div class="space-y-3">
						<label for="embedding-model" class="block text-sm font-medium text-slate-200">
							Embedding Model
						</label>
						<select
							id="embedding-model"
							bind:value={config.embedding_model}
							class="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-xl text-slate-100 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition-all duration-200 cursor-pointer"
						>
							{#each embeddingModels as model}
								<option value={model}>{model}</option>
							{/each}
						</select>
						<p class="text-xs text-slate-500">The OpenAI model used for creating document embeddings.</p>
					</div>

					<!-- System Prompt -->
					<div class="space-y-3">
						<label for="system-prompt" class="block text-sm font-medium text-slate-200">
							System Prompt
						</label>
						<textarea
							id="system-prompt"
							bind:value={config.system_prompt}
							rows="6"
							class="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-xl text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent resize-none transition-all duration-200"
							placeholder="Enter the system prompt that will guide the AI's responses..."
						></textarea>
						<p class="text-xs text-slate-500">Instructions that guide how the AI should respond to queries.</p>
					</div>

					{#if error}
						<div class="bg-red-900/50 border border-red-700 rounded-xl p-4">
							<p class="text-red-200 text-sm">{error}</p>
						</div>
					{/if}

					<!-- Actions -->
					<div class="flex justify-end space-x-4 pt-6">
						<button
							type="button"
							onclick={onclose}
							class="px-6 py-3 text-slate-400 hover:text-slate-200 hover:bg-slate-700 rounded-xl transition-all duration-200 cursor-pointer"
						>
							Cancel
						</button>
						<button
							type="submit"
							disabled={saving}
							class="px-6 py-3 bg-gradient-to-r from-cyan-500 to-cyan-600 hover:from-cyan-600 hover:to-cyan-700 text-white rounded-xl font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-3 transition-all duration-200 cursor-pointer"
						>
							{#if saving}
								<Loader class="w-5 h-5 animate-spin" />
								<span>Saving...</span>
							{:else}
								<span>Save Configuration</span>
							{/if}
						</button>
					</div>
				</form>
			{/if}
		</div>
	</div>
</div>
