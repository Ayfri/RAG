<script lang="ts">
	import { CheckCircle, File, Loader, Upload } from '@lucide/svelte';
	import Button from './common/Button.svelte';
	import Input from './common/Input.svelte';
	import Modal from './common/Modal.svelte';

	interface Props {
		onclose: () => void;
		oncreated: (event: CustomEvent<string>) => void;
	}

	let { onclose, oncreated }: Props = $props();

	let ragName = $state('');
	let files: FileList | null = $state(null);
	let dragOver = $state(false);
	let loading = $state(false);
	let error = $state('');
	let step = $state<'name' | 'files' | 'creating'>('name');

	async function handleSubmit() {
		if (!ragName.trim()) {
			error = 'RAG name is required';
			return;
		}

		try {
			loading = true;
			step = 'creating';
			error = '';

			// Upload files if any are selected
			if (files && files.length > 0) {
				for (const file of Array.from(files)) {
					const formData = new FormData();
					formData.append('file', file);

					const uploadResponse = await fetch(`/api/rag/${ragName}/files`, {
						method: 'POST',
						body: formData
					});

					if (!uploadResponse.ok) {
						throw new Error(`Failed to upload ${file.name}`);
					}
				}
			}

			// Create the RAG index (or rebuild if files were uploaded)
			const createResponse = await fetch(`/api/rag/${ragName}`, {
				method: 'POST'
			});

			if (!createResponse.ok) {
				throw new Error('Failed to create RAG index');
			}

			oncreated(new CustomEvent('created', { detail: ragName }));
		} catch (err) {
			error = err instanceof Error ? err.message : 'Unknown error';
			step = 'files';
		} finally {
			loading = false;
		}
	}

	function handleDrop(event: DragEvent) {
		event.preventDefault();
		dragOver = false;
		files = event.dataTransfer?.files || null;
	}

	function handleDragOver(event: DragEvent) {
		event.preventDefault();
		dragOver = true;
	}

	function handleDragLeave() {
		dragOver = false;
	}

	function nextStep() {
		if (step === 'name' && ragName.trim()) {
			step = 'files';
			error = '';
		}
	}

	function previousStep() {
		if (step === 'files') {
			step = 'name';
			error = '';
		}
	}
</script>

<Modal onclose={onclose} title="Create New RAG">
	{#if step === 'name'}
		<div class="space-y-6">
			<div>
				<label for="rag-name" class="block text-sm font-medium text-slate-200 mb-3">
					RAG Name
				</label>
				<Input
					id="rag-name"
					bind:value={ragName}
					placeholder="Enter a unique name for your RAG"
					onkeydown={(e: KeyboardEvent) => e.key === 'Enter' && nextStep()}
				/>
				<p class="text-xs text-slate-500 mt-2">
					Use letters, numbers, hyphens, and underscores only
				</p>
			</div>

			{#if error}
				<div class="bg-red-900/50 border border-red-700 rounded-xl p-4">
					<p class="text-red-200 text-sm">{error}</p>
				</div>
			{/if}

			<div class="flex justify-end space-x-4 pt-4">
				<Button onclick={onclose} variant="secondary">
					{#snippet children()}
						Cancel
					{/snippet}
				</Button>
				<Button onclick={nextStep} disabled={!ragName.trim()}>
					{#snippet children()}
						Next
					{/snippet}
				</Button>
			</div>
		</div>

	{:else if step === 'files'}
		<div class="space-y-6">
			<div>
				<label class="block text-sm font-medium text-slate-200 mb-3">
					Upload Documents (Optional)
				</label>
				<div
					class="border-2 border-dashed border-slate-600 rounded-xl p-8 text-center transition-all duration-200 {dragOver ? 'border-cyan-400 bg-cyan-900/20' : 'hover:border-slate-500'}"
					ondrop={handleDrop}
					ondragover={handleDragOver}
					ondragleave={handleDragLeave}
				>
					<Upload class="w-16 h-16 text-slate-500 mx-auto mb-4" />
					<p class="text-slate-300 mb-3">
						Drag and drop files here, or
						<label class="text-cyan-400 hover:text-cyan-300 cursor-pointer font-medium">
							browse
							<input
								type="file"
								multiple
								bind:files
								class="hidden"
								accept=".txt,.pdf,.docx,.md"
							/>
						</label>
					</p>
					<p class="text-xs text-slate-500">
						Supports: PDF, TXT, DOCX, MD files
					</p>
				</div>

				{#if files && files.length > 0}
					<div class="mt-4 space-y-3">
						<p class="text-sm font-medium text-slate-200">Selected files:</p>
						<div class="space-y-2">
							{#each Array.from(files) as file}
								<div class="flex items-center space-x-3 p-3 bg-slate-700/50 rounded-lg">
									<File class="w-5 h-5 text-cyan-400" />
									<span class="text-slate-200 flex-1">{file.name}</span>
									<span class="text-slate-500 text-sm">({Math.round(file.size / 1024)} KB)</span>
								</div>
							{/each}
						</div>
					</div>
				{/if}
			</div>

			{#if error}
				<div class="bg-red-900/50 border border-red-700 rounded-xl p-4">
					<p class="text-red-200 text-sm">{error}</p>
				</div>
			{/if}

			<div class="flex justify-between pt-4">
				<Button onclick={previousStep} variant="secondary">
					{#snippet children()}
						Back
					{/snippet}
				</Button>
				<div class="space-x-4">
					<Button onclick={onclose} variant="secondary">
						{#snippet children()}
							Cancel
						{/snippet}
					</Button>
					<Button onclick={handleSubmit} disabled={loading}>
						{#snippet children()}
							{#if loading}
								<Loader class="w-5 h-5 animate-spin" />
								<span>Creating...</span>
							{:else}
								<span>Create RAG</span>
							{/if}
						{/snippet}
					</Button>
				</div>
			</div>
		</div>

	{:else if step === 'creating'}
		<div class="text-center py-12">
			<CheckCircle class="w-20 h-20 text-cyan-400 mx-auto mb-6" />
			<h3 class="text-2xl font-bold text-slate-100 mb-3">RAG Created Successfully!</h3>
			<p class="text-slate-400 text-lg">Your RAG "{ragName}" is ready to use.</p>
		</div>
	{/if}
</Modal>
