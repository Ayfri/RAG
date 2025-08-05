<script lang="ts">
	import Button from '$lib/components/common/Button.svelte';
	import Input from '$lib/components/common/Input.svelte';
	import Modal from '$lib/components/common/Modal.svelte';
	import {AlertCircle, Check, Loader, Plus, Settings, X} from '@lucide/svelte';

	interface Props {
		ragName?: string;
		folderName?: string | null;
		open: boolean;
	}

	let { ragName, folderName, open = $bindable(false) }: Props = $props();

	let includePatterns = $state<string[]>(['**/*']);
	let excludePatterns = $state<string[]>([]);
	let currentInclude = $state('');
	let currentExclude = $state('');
	let loading = $state(false);
	let error = $state('');
	let editingIncludeIndex = $state<number | null>(null);
	let editingExcludeIndex = $state<number | null>(null);
	let editingIncludeValue = $state('');
	let editingExcludeValue = $state('');

	function addIncludePattern() {
		if (!currentInclude.trim()) return;

		const patterns = currentInclude.split(',').map(p => p.trim()).filter(p => p);
		includePatterns = [...includePatterns, ...patterns];
		currentInclude = '';
	}

	function addExcludePattern() {
		if (!currentExclude.trim()) return;

		const patterns = currentExclude.split(',').map(p => p.trim()).filter(p => p);
		excludePatterns = [...excludePatterns, ...patterns];
		currentExclude = '';
	}

	function removeIncludePattern(index: number) {
		includePatterns = includePatterns.filter((_, i) => i !== index);
	}

	function removeExcludePattern(index: number) {
		excludePatterns = excludePatterns.filter((_, i) => i !== index);
	}

	function startEditingInclude(index: number) {
		editingIncludeIndex = index;
		editingIncludeValue = includePatterns[index];
	}

	function startEditingExclude(index: number) {
		editingExcludeIndex = index;
		editingExcludeValue = excludePatterns[index];
	}

	function saveIncludeEdit() {
		if (editingIncludeIndex !== null && editingIncludeValue.trim()) {
			includePatterns[editingIncludeIndex] = editingIncludeValue.trim();
			editingIncludeIndex = null;
			editingIncludeValue = '';
		}
	}

	function saveExcludeEdit() {
		if (editingExcludeIndex !== null && editingExcludeValue.trim()) {
			excludePatterns[editingExcludeIndex] = editingExcludeValue.trim();
			editingExcludeIndex = null;
			editingExcludeValue = '';
		}
	}

	function cancelIncludeEdit() {
		editingIncludeIndex = null;
		editingIncludeValue = '';
	}

	function cancelExcludeEdit() {
		editingExcludeIndex = null;
		editingExcludeValue = '';
	}

	function handleIncludeKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter' || event.key === ',') {
			event.preventDefault();
			addIncludePattern();
		}
	}

	function handleExcludeKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter' || event.key === ',') {
			event.preventDefault();
			addExcludePattern();
		}
	}

	function handleEditIncludeKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter') {
			event.preventDefault();
			saveIncludeEdit();
		} else if (event.key === 'Escape') {
			editingIncludeIndex = null;
			editingIncludeValue = '';
		}
	}

	function handleEditExcludeKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter') {
			event.preventDefault();
			saveExcludeEdit();
		} else if (event.key === 'Escape') {
			editingExcludeIndex = null;
			editingExcludeValue = '';
		}
	}

	async function loadConfig() {
		if (!ragName) return;

		try {
			loading = true;
			error = '';

			const response = await fetch(`/api/rag/${ragName}/config`);
			if (!response.ok) {
				throw new Error('Failed to load configuration');
			}

			const config = await response.json();
			const fileFilters = config.file_filters || {};
			const key = folderName || '_base';
			const filters = fileFilters[key] || { include: ['**/*'], exclude: [] };

			includePatterns = [...filters.include];
			excludePatterns = [...filters.exclude];
		} catch (err) {
			error = err instanceof Error ? err.message : 'Unknown error occurred';
		} finally {
			loading = false;
		}
	}

	async function saveConfig() {
		if (!ragName) return;

		try {
			loading = true;
			error = '';

			// Load current config first
			const response = await fetch(`/api/rag/${ragName}/config`);
			if (!response.ok) {
				throw new Error('Failed to load current configuration');
			}

			const currentConfig = await response.json();
			const fileFilters = currentConfig.file_filters || {};
			const key = folderName || '_base';

			// Update the file filters for this specific folder/symlink
			fileFilters[key] = {
				include: includePatterns.length > 0 ? includePatterns : ['**/*'],
				exclude: excludePatterns
			};

			// Save updated config
			const updateResponse = await fetch(`/api/rag/${ragName}/config`, {
				method: 'PUT',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					...currentConfig,
					file_filters: fileFilters
				})
			});

			if (!updateResponse.ok) {
				throw new Error('Failed to save configuration');
			}

			open = false;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Unknown error occurred';
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		if (open && ragName) {
			loadConfig();
		}
	});
</script>

<Modal title="Configure File Filters" bind:open size="lg">
	<div class="space-y-6">
		<div class="flex items-center space-x-3 text-slate-300 mb-4">
			<Settings class="w-5 h-5 text-cyan-400" />
			<span class="text-sm">
				Configure file inclusion and exclusion patterns for
				{folderName ? `folder "${folderName}"` : 'base directory'}
			</span>
		</div>

		{#if error}
			<div class="bg-red-900/20 border border-red-500 rounded-lg p-4">
				<div class="flex items-center space-x-2">
					<AlertCircle class="w-5 h-5 text-red-400" />
					<p class="text-red-400 text-sm">{error}</p>
				</div>
			</div>
		{/if}

		<div class="space-y-6">
			<!-- Include Patterns -->
			<div>
				<label class="block text-sm font-medium text-slate-200 mb-3">
					Include Patterns
				</label>
				<p class="text-xs text-slate-400 mb-3">
					Files must match at least one include pattern. Use glob patterns like *.pdf, **/*.md, etc.
				</p>

				<div class="space-y-3">
					<div class="flex space-x-2">
						<Input
							bind:value={currentInclude}
							placeholder="Add pattern (e.g., *.pdf, **/*.md)"
							class="flex-1"
							onkeydown={handleIncludeKeydown}
							disabled={loading}
						/>
						<Button
							onclick={addIncludePattern}
							disabled={loading || !currentInclude.trim()}
							class="cursor-pointer"
						>
							<Plus size={16} />
						</Button>
					</div>

					<div class="flex flex-wrap gap-2">
						{#each includePatterns as pattern, index}
							<div class="flex items-center bg-green-900/30 border border-green-600 rounded-lg px-3 py-1">
								{#if editingIncludeIndex === index}
									<Input
										bind:value={editingIncludeValue}
										class="text-xs bg-transparent border-none p-0 min-w-20"
										onkeydown={handleEditIncludeKeydown}
									/>
									<Button
										onclick={saveIncludeEdit}
										variant="ghost"
										size="icon"
										class="ml-2"
									>
										<Check size={12} />
									</Button>
								{:else}
									<span
										class="text-green-200 text-xs cursor-pointer"
										onclick={() => startEditingInclude(index)}
									>
										{pattern}
									</span>
									<Button
										onclick={() => removeIncludePattern(index)}
										variant="ghost"
										size="icon"
										class="ml-2 text-green-200 hover:text-red-400"
									>
										<X size={12} />
									</Button>
								{/if}
							</div>
						{/each}
					</div>
				</div>

				<div class="space-y-3">
					<label class="block text-slate-300 text-sm font-medium">
						Exclude patterns (files to ignore)
					</label>

					<div class="flex gap-2">
						<Input
							bind:value={currentExclude}
							placeholder="e.g., *.log, node_modules/**"
							class="flex-1"
							onkeydown={handleExcludeKeydown}
						/>
						<Button
							onclick={addExcludePattern}
							disabled={loading || !currentExclude.trim()}
						>
							<Plus size={16} />
						</Button>
					</div>

					<div class="flex flex-wrap gap-2">
						{#each excludePatterns as pattern, index}
							<div class="flex items-center bg-red-900/30 border border-red-600 rounded-lg px-3 py-1">
								{#if editingExcludeIndex === index}
									<Input
										bind:value={editingExcludeValue}
										class="text-xs bg-transparent border-none p-0 min-w-20"
										onkeydown={handleEditExcludeKeydown}
									/>
									<Button
										onclick={saveExcludeEdit}
										variant="ghost"
										size="icon"
										class="ml-2"
									>
										<Check size={12} />
									</Button>
								{:else}
									<span
										class="text-red-200 text-xs cursor-pointer"
										onclick={() => startEditingExclude(index)}
									>
										{pattern}
									</span>
									<Button
										onclick={() => removeExcludePattern(index)}
										variant="ghost"
										size="icon"
										class="ml-2 text-red-200 hover:text-red-400"
									>
										<X size={12} />
									</Button>
								{/if}
							</div>
						{/each}
					</div>
				</div>

				<div class="bg-slate-800/50 rounded-lg p-4">
					<h4 class="text-slate-300 text-sm font-medium mb-2 flex items-center gap-2">
						<AlertCircle size={16} />
						Pattern Examples
					</h4>
					<div class="space-y-1 text-xs text-slate-400">
						<div><code class="bg-slate-700 px-1 py-0.5 rounded">**/*</code> - All files (default)</div>
						<div><code class="bg-slate-700 px-1 py-0.5 rounded">*.py</code> - Python files only</div>
						<div><code class="bg-slate-700 px-1 py-0.5 rounded">docs/**/*.md</code> - Markdown files in docs folder</div>
						<div><code class="bg-slate-700 px-1 py-0.5 rounded">*.log</code> - Exclude log files</div>
						<div><code class="bg-slate-700 px-1 py-0.5 rounded">node_modules/**</code> - Exclude node_modules</div>
					</div>
				</div>
			</div>

			<div class="flex justify-end gap-3 pt-4 border-t border-slate-700">
				<Button
					onclick={() => open = false}
					variant="secondary"
				>
					Cancel
				</Button>
				<Button
					onclick={saveConfig}
					disabled={loading}
				>
					{#if loading}
						<Loader size={16} class="animate-spin" />
						Saving...
					{:else}
						<Settings size={16} />
						Save Configuration
					{/if}
				</Button>
			</div>
	</div>
</Modal>
