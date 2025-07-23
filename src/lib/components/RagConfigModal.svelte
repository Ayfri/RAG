<script lang="ts">
	import { CheckCircle, Loader, RefreshCw, Save, Settings, X } from '@lucide/svelte';
	import { getModelsLoadingState, loadOpenAIModels, openaiModels } from '$lib/stores/openai-models.js';
	import Button from '$lib/components/common/Button.svelte';
	import Modal from '$lib/components/common/Modal.svelte';
	import Select from '$lib/components/common/Select.svelte';
	import TextArea from '$lib/components/common/TextArea.svelte';

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

	// Get loading state and models from stores
	const modelsState = getModelsLoadingState();

	async function ensureModelsLoaded() {
		try {
			await loadOpenAIModels();
		} catch (err) {
			console.warn('Failed to load models:', err);
		}
	}

	async function reloadModels() {
		try {
			await loadOpenAIModels(true);
		} catch (err) {
			console.warn('Failed to reload models:', err);
		}
	}

	async function loadConfig() {
		try {
			loading = true;
			error = '';

			await ensureModelsLoaded();

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
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(config)
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

	$effect(() => {
		loadConfig();
	});
</script>

<Modal onclose={onclose} title="Configure RAG">
	<div class="flex justify-between items-start">
		<div class="flex items-center space-x-3 mb-4">
			<Settings class="w-6 h-6 text-cyan-400" />
			<div>
				<h2 class="text-2xl font-bold text-slate-100">Configure RAG</h2>
				{#if $modelsState}
					<p class="text-xs text-slate-400 flex items-center space-x-1">
						<Loader class="w-3 h-3 animate-spin" />
						<span>Loading latest models...</span>
					</p>
				{:else if $openaiModels.chat.length > 0 || $openaiModels.embedding.length > 0}
					<p class="text-xs text-green-400">✓ Models loaded ({$openaiModels.chat.length + $openaiModels.thinking.length} chat, {$openaiModels.embedding.length} embedding)</p>
				{/if}
			</div>
		</div>
		<Button
			size="icon"
			onclick={reloadModels}
			disabled={$modelsState}
			class="group"
			variant="secondary"
			title="Reload OpenAI models"
		>
			<RefreshCw class={`w-5 h-5 group-hover:rotate-45 ${$modelsState ? 'animate-spin' : ''}`} />
		</Button>
	</div>

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
		<form onsubmit={(e) => {
			e.preventDefault();
			saveConfig();
		}} class="space-y-6">
			<div class="bg-slate-800/50 rounded-xl p-4 border border-slate-600">
				<h3 class="text-lg font-semibold text-slate-100 mb-2">RAG: <span class="text-cyan-400">{ragName}</span></h3>
				<p class="text-slate-400 text-sm">Configure the OpenAI models and system prompt for this RAG instance.</p>
			</div>

			<!-- Chat Model Selection -->
			<div class="space-y-3">
				<label for="chat-model" class="block text-sm font-medium text-slate-200">
					Chat Model
				</label>
				{#if $modelsState}
					<Select
						id="chat-model"
						bind:value={config.chat_model}
						disabled={$modelsState}
						options={[{ label: 'Loading models...', value: '' }]}
					/>
				{:else}
					<Select
						id="chat-model"
						bind:value={config.chat_model}
						disabled={$modelsState}
						options={[
							...$openaiModels.chat.toSorted((a, b) => a.name.localeCompare(b.name)).map(model => ({ label: model.name, value: model.id })),
							...$openaiModels.thinking.map(model => ({ label: `${model.name} (Reasoning)`, value: model.id })),
							...($openaiModels.chat.length === 0 && $openaiModels.thinking.length === 0 ? [{ label: 'GPT-4o Mini (fallback)', value: 'gpt-4o-mini' }] : [])
						]}
					/>
				{/if}
				<p class="text-xs text-slate-500">The OpenAI model used for generating responses.</p>
			</div>

			<!-- Embedding Model Selection -->
			<div class="space-y-3">
				<label for="embedding-model" class="block text-sm font-medium text-slate-200">
					Embedding Model
				</label>
				{#if $modelsState}
					<Select
						id="embedding-model"
						bind:value={config.embedding_model}
						disabled={$modelsState}
						options={[{ label: 'Loading models...', value: '' }]}
					/>
				{:else}
					<Select
						id="embedding-model"
						bind:value={config.embedding_model}
						disabled={$modelsState}
						options={[
							...$openaiModels.embedding.toSorted((a, b) => a.name.localeCompare(b.name)).map(model => ({ label: model.name, value: model.id })),
							...($openaiModels.embedding.length === 0 ? [{ label: 'Text Embedding 3 Large (fallback)', value: 'text-embedding-3-large' }] : [])
						]}
					/>
				{/if}
				<p class="text-xs text-slate-500">The OpenAI model used for creating document embeddings.</p>
			</div>

			<!-- System Prompt -->
			<div class="space-y-3">
				<label for="system-prompt" class="block text-sm font-medium text-slate-200">
					System Prompt
				</label>
				<TextArea
					id="system-prompt"
					bind:value={config.system_prompt}
					placeholder="Enter the system prompt that will guide the AI's responses..."
				/>
				<p class="text-xs text-slate-500">Instructions that guide how the AI should respond to queries.</p>
			</div>

			{#if error}
				<div class="bg-red-900/50 border border-red-700 rounded-xl p-4">
					<p class="text-red-200 text-sm">{error}</p>
				</div>
			{/if}

			<!-- Actions -->
			<div class="flex justify-end space-x-4 pt-6">
				<Button class="group" type="button" onclick={onclose} variant="secondary">
					<X class="w-5 h-5 group-hover:animate-shake transition-transform duration-200" />
					<span>Cancel</span>
				</Button>
				<Button class="group" type="submit" disabled={saving}>
					{#if saving}
						<Loader class="w-5 h-5 animate-spin" />
						<span>Saving...</span>
					{:else}
						<Save class="w-5 h-5 group-hover:rotate-8 group-hover:scale-110 transition-transform duration-200" />
						<span>Save Configuration</span>
					{/if}
				</Button>
			</div>
		</form>
	{/if}
</Modal>
