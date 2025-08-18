<script lang="ts">
	import { Loader, RefreshCw, Save, Settings, Sparkles, X } from '@lucide/svelte';
    import { openAIModels } from '$lib/stores/openai-models.js';
    import Button from '$lib/components/common/Button.svelte';
    import MessageStats from '$lib/components/common/MessageStats.svelte';
    import Modal from '$lib/components/common/Modal.svelte';
    import Select from '$lib/components/common/Select.svelte';
    import SystemPromptGeneratorModal from '$lib/components/modals/SystemPromptGeneratorModal.svelte';
    import TextArea from '$lib/components/common/TextArea.svelte';
	import type { OpenAIModel, RagConfig } from '$lib/types.d.ts';
	import { fetchRagConfig, updateRagConfig } from '$lib/helpers/rag-api';

	interface Props {
		ragName: string;
		onupdated: () => void;
		open: boolean;
	}

	let { ragName, onupdated, open = $bindable(false) }: Props = $props();

	let config: RagConfig = $state({
		chat_model: 'gpt-4o-mini',
		embedding_model: 'text-embedding-3-large',
		system_prompt: 'You are a helpful assistant that answers questions based on the provided context. Be concise and accurate.',
		file_filters: {}
	});

	let loading = $state(false);
	let saving = $state(false);
	let error = $state('');
	let showPromptGeneratorModal = $state(false);
    let systemPromptTextArea: HTMLTextAreaElement | undefined = $state();

	async function reloadModels() {
		try {
			await fetch('/api/models', { headers: { 'Cache-Control': 'no-cache' }});
		} catch (err) {
			console.warn('Failed to reload models:', err);
		}
	}

	async function loadConfig() {
		try {
			loading = true;
			error = '';

			const data = await fetchRagConfig(ragName);
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

			await updateRagConfig(ragName, config);

			onupdated();
			open = false;
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

<Modal title="Configure RAG" bind:open>
	<div class="flex justify-between items-start">
		<div class="flex items-center space-x-3 mb-4">
			<Settings class="w-6 h-6 text-cyan-400" />
			<div>
				<h2 class="text-2xl font-bold text-slate-100">Configure RAG</h2>
				{#if $openAIModels.chat.length === 0 && $openAIModels.embedding.length === 0}
					<p class="text-xs text-slate-400 flex items-center space-x-1">
						<Loader class="w-3 h-3 animate-spin" />
						<span>Loading latest models...</span>
					</p>
				{:else}
					<p class="text-xs text-green-400">✓ Models loaded ({$openAIModels.chat.length + $openAIModels.thinking.length} chat, {$openAIModels.embedding.length} embedding)</p>
				{/if}
			</div>
		</div>
		<Button
			size="icon"
			onclick={reloadModels}
			disabled={false}
			class="group"
			variant="secondary"
			title="Reload OpenAI models"
		>
			<RefreshCw class={`w-5 h-5 group-hover:rotate-45 ${false ? 'animate-spin' : ''}`} />
		</Button>
	</div>

	{#if loading}
		<div class="text-center py-12">
			<Loader class="w-12 h-12 animate-spin text-cyan-400 mx-auto mb-4" />
			<p class="text-slate-400">Loading configuration...</p>
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
				{#if $openAIModels.chat.length === 0 && $openAIModels.thinking.length === 0}
					<Select
						id="chat-model"
						bind:value={config.chat_model}
						disabled={true}
						options={[{ label: 'Loading models...', value: '' }]}
					/>
				{:else}
					<Select
						id="chat-model"
						bind:value={config.chat_model}
						disabled={false}
						options={[
							...$openAIModels.chat.toSorted((a: OpenAIModel, b: OpenAIModel) => a.name.localeCompare(b.name)).map((model: OpenAIModel) => ({ label: model.name, value: model.id })),
							...$openAIModels.thinking.filter((model: OpenAIModel) => !model.id.includes('deep-research')).toSorted((a: OpenAIModel, b: OpenAIModel) => a.name.localeCompare(b.name)).map((model: OpenAIModel) => ({ label: `${model.name} (Reasoning)`, value: model.id })),
							...($openAIModels.chat.length === 0 && $openAIModels.thinking.length === 0 ? [{ label: 'GPT-4o Mini (fallback)', value: 'gpt-4o-mini' }] : [])
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
				{#if $openAIModels.embedding.length === 0}
					<Select
						id="embedding-model"
						bind:value={config.embedding_model}
						disabled={true}
						options={[{ label: 'Loading models...', value: '' }]}
					/>
				{:else}
					<Select
						id="embedding-model"
						bind:value={config.embedding_model}
						disabled={false}
						options={[
							...$openAIModels.embedding.filter((model: OpenAIModel) => !model.id.includes('deep-research')).toSorted((a: OpenAIModel, b: OpenAIModel) => a.name.localeCompare(b.name)).map((model: OpenAIModel) => ({ label: model.name, value: model.id })),
							...($openAIModels.embedding.length === 0 ? [{ label: 'Text Embedding 3 Large (fallback)', value: 'text-embedding-3-large' }] : [])
						]}
					/>
				{/if}
				<p class="text-xs text-slate-500">The OpenAI model used for creating document embeddings.</p>
			</div>

			<!-- System Prompt -->
			<div class="space-y-3">
                <div class="flex justify-between items-center">
					<label for="system-prompt" class="block text-sm font-medium text-slate-200">
						System Prompt
					</label>
					<Button
						onclick={() => showPromptGeneratorModal = true}
						variant="secondary"
						class="px-2 py-1 text-xs"
						title="Generate system prompt"
					>
						<Sparkles size={16} />
						<span>Generate</span>
					</Button>
				</div>
				<div class="flex flex-col space-y-2 items-end">
					<TextArea
						id="system-prompt"
						bind:value={config.system_prompt}
						placeholder="Enter the system prompt that will guide the AI's responses..."
						minHeight="120px"
						bind:textareaRef={systemPromptTextArea}
					/>
					<MessageStats class="text-slate-400" text={config.system_prompt} hideWhenEmpty={false} targetElement={systemPromptTextArea!} />
				</div>
				<p class="text-xs text-slate-500">Instructions that guide how the AI should respond to queries.</p>
			</div>

			{#if error}
				<div class="bg-red-900/50 border border-red-700 rounded-xl p-4">
					<p class="text-red-200 text-sm">{error}</p>
				</div>
			{/if}

			<!-- Actions -->
			<div class="flex justify-end space-x-4 pt-6">
				<Button class="group" type="button" onclick={() => open = false} variant="secondary">
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

<SystemPromptGeneratorModal
	{ragName}
	bind:open={showPromptGeneratorModal}
	onPromptGenerated={(prompt) => {
		config.system_prompt = prompt;
	}}
/>
