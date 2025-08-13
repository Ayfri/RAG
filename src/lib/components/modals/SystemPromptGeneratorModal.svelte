<script lang="ts">
	import Modal from '$lib/components/common/Modal.svelte';
	import Button from '$lib/components/common/Button.svelte';
	import TextArea from '$lib/components/common/TextArea.svelte';
	import { notifications } from '$lib/stores/notifications';
	import { Sparkles, Copy, Check } from '@lucide/svelte';

	interface Props {
		ragName: string;
		open: boolean;
		onPromptGenerated: (prompt: string) => void;
	}

	let { ragName, open = $bindable(false), onPromptGenerated }: Props = $props();

	let description = $state('');
	let generatedPrompt = $state('');
	let loading = $state(false);
	let copied = $state(false);

	async function generatePrompt() {
		if (!description.trim()) {
			notifications.error('Please enter a description');
			return;
		}

		try {
			loading = true;
			const res = await fetch(`/api/rag/${ragName}/generate-prompt`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ description: description.trim() })
			});

			if (!res.ok) throw new Error('Failed to generate prompt');

			const data = await res.json();
			generatedPrompt = data.prompt;
			notifications.success('Prompt generated successfully!');
		} catch (err) {
			console.error('Failed to generate prompt:', err);
			notifications.error(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
		} finally {
			loading = false;
		}
	}

	async function applyPrompt() {
		if (!generatedPrompt.trim()) {
			notifications.error('No generated prompt to apply');
			return;
		}

		onPromptGenerated(generatedPrompt);
		notifications.success('System prompt applied to form!');
		open = false;
	}

	async function copyToClipboard() {
		try {
			await navigator.clipboard.writeText(generatedPrompt);
			copied = true;
			notifications.success('Prompt copied to clipboard!');
			setTimeout(() => copied = false, 2000);
		} catch (err) {
			notifications.error('Unable to copy prompt');
		}
	}

	function reset() {
		description = '';
		generatedPrompt = '';
		copied = false;
	}

	$effect(() => {
		if (open) {
			reset();
		}
	});
</script>

<Modal {open} title="System Prompt Generator" size="xl">
	<div class="space-y-6">
		<!-- Description input -->
		<div class="space-y-3">
			<label for="description" class="block text-sm font-medium text-slate-200">
				Desired Role Description
			</label>
			<TextArea
				id="description"
				bind:value={description}
				placeholder="Ex: I'd like the model to be super good at web development with React and Node.js"
				minHeight="88px"
				class="w-full"
			/>
			<div class="flex justify-between items-center">
				<p class="text-xs text-slate-400">
					Describe the role or expertise you want for your assistant
				</p>
				<Button
					onclick={generatePrompt}
					disabled={!description.trim() || loading}
					class="flex items-center bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700"
				>
					<Sparkles size={16} />
					<span>{loading ? 'Generating...' : 'Generate Prompt'}</span>
				</Button>
			</div>
		</div>

		<!-- Generated prompt -->
		{#if generatedPrompt}
			<div class="space-y-3">
				<div class="flex justify-between items-center">
					<h3 class="text-sm font-medium text-slate-200">Generated Prompt</h3>
					<div class="flex space-x-2">
						<Button
							onclick={copyToClipboard}
							variant="secondary"
							class="px-2 py-1 text-xs"
						>
							{#if copied}
								<Check size={14} />
								<span>Copied</span>
							{:else}
								<Copy size={14} />
								<span>Copy</span>
							{/if}
						</Button>
						<Button
							onclick={applyPrompt}
							class="bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600"
						>
							<Check size={14} />
							Apply to RAG
						</Button>
					</div>
				</div>
				<div class="bg-slate-800 border border-slate-600 rounded-lg p-4">
					<pre class="text-sm text-slate-200 whitespace-pre-wrap font-mono">{generatedPrompt}</pre>
				</div>
			</div>
		{/if}

		<!-- Tips -->
		<div class="bg-slate-800/50 border border-slate-600 rounded-lg p-4">
			<h4 class="text-sm font-medium text-slate-200 mb-2">💡 Tips for a good system prompt</h4>
			<ul class="text-xs text-slate-400 space-y-1">
				<li>• Be specific about the desired domain of expertise</li>
				<li>• Mention the communication style (formal, casual, technical)</li>
				<li>• Specify the expected level of detail in responses</li>
				<li>• Indicate the types of tasks the assistant should perform</li>
				<li>• Include any particular constraints or preferences</li>
			</ul>
		</div>
	</div>
</Modal>
