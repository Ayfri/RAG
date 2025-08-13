<script lang="ts">
	import Button from '$lib/components/common/Button.svelte';
	import Input from '$lib/components/common/Input.svelte';
	import Modal from '$lib/components/common/Modal.svelte';
	import {notifications} from '$lib/stores/notifications';
	import {AlertCircle, Check, FolderOpen, Link, Loader, Plus, X} from '@lucide/svelte';

	interface Props {
		ragName: string;
		onSymlinkCreated: () => void;
		open: boolean;
	}

	let { ragName, onSymlinkCreated, open = $bindable(false) }: Props = $props();

	let targetPath = $state('');
	let linkName = $state('');
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

	function reset() {
		targetPath = '';
		linkName = '';
		includePatterns = ['**/*'];
		excludePatterns = [];
		currentInclude = '';
		currentExclude = '';
		error = '';
		editingIncludeIndex = null;
		editingExcludeIndex = null;
	}

	function addIncludePattern() {
		const pattern = currentInclude.trim();
		if (pattern && !includePatterns.includes(pattern)) {
			includePatterns = [...includePatterns, pattern];
			currentInclude = '';
		}
	}

	function addExcludePattern() {
		const pattern = currentExclude.trim();
		if (pattern && !excludePatterns.includes(pattern)) {
			excludePatterns = [...excludePatterns, pattern];
			currentExclude = '';
		}
	}

	function removeIncludePattern(index: number) {
		if (includePatterns.length > 1) {
			includePatterns = includePatterns.filter((_, i) => i !== index);
		}
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
			includePatterns = [...includePatterns];
		}
		editingIncludeIndex = null;
		editingIncludeValue = '';
	}

	function saveExcludeEdit() {
		if (editingExcludeIndex !== null && editingExcludeValue.trim()) {
			excludePatterns[editingExcludeIndex] = editingExcludeValue.trim();
			excludePatterns = [...excludePatterns];
		}
		editingExcludeIndex = null;
		editingExcludeValue = '';
	}

	function handleIncludeKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' || e.key === ',') {
			e.preventDefault();
			addIncludePattern();
		}
	}

	function handleExcludeKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' || e.key === ',') {
			e.preventDefault();
			addExcludePattern();
		}
	}

	function handleEditIncludeKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') {
			e.preventDefault();
			saveIncludeEdit();
		} else if (e.key === 'Escape') {
			editingIncludeIndex = null;
			editingIncludeValue = '';
		}
	}

	function handleEditExcludeKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') {
			e.preventDefault();
			saveExcludeEdit();
		} else if (e.key === 'Escape') {
			editingExcludeIndex = null;
			editingExcludeValue = '';
		}
	}

	async function createSymlink() {
		if (!targetPath.trim() || !linkName.trim()) {
			error = 'Both target path and link name are required';
			return;
		}

		try {
			loading = true;
			error = '';

			// Create the symlink with filters
			const response = await fetch(`/api/rag/${ragName}/symlink`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					target_path: targetPath.trim(),
					link_name: linkName.trim(),
					include_patterns: includePatterns,
					exclude_patterns: excludePatterns
				})
			});

			if (!response.ok) {
				const errorData = await response.text();
				throw new Error(errorData || 'Failed to create symbolic link');
			}

			notifications.add({
				type: 'success',
				message: `Symlink "${linkName}" created with file filters`
			});

			reset();
			open = false;
			onSymlinkCreated();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Unknown error occurred';
		} finally {
			loading = false;
		}
	}

	function suggestLinkName() {
		if (targetPath.trim()) {
			const path = targetPath.trim();
			const name = path.split(/[\\/]/).pop() || 'link';
			linkName = name;
		}
	}

	$effect(() => {
		if (!open) {
			reset();
		}
	});
</script>

<Modal title="Create Symbolic Link with File Filters" bind:open size="lg">
	<div class="space-y-4">
		<div class="flex items-center space-x-3 text-slate-300 mb-4">
			<Link class="w-5 h-5 text-cyan-400" />
			<span class="text-sm">Create a symbolic link to an external file or directory</span>
		</div>

		{#if error}
			<div class="bg-red-900/20 border border-red-500 rounded-lg p-4">
				<p class="text-red-400 text-sm">{error}</p>
			</div>
		{/if}

		<div class="space-y-4">
			<div>
				<label for="target-path" class="block text-sm font-medium text-slate-200 mb-2">
					Target Path
				</label>
				<Input
					id="target-path"
					bind:value={targetPath}
					placeholder="C:\path\to\your\files or /path/to/your/files"
					class="w-full"
					onchange={suggestLinkName}
					disabled={loading}
				/>
				<p class="text-xs text-slate-400 mt-1">
					Absolute path to the file or directory you want to link to
				</p>
			</div>

			<div>
				<label for="link-name" class="block text-sm font-medium text-slate-200 mb-2">
					Link Name
				</label>
				<Input
					id="link-name"
					bind:value={linkName}
					placeholder="my-documents"
					class="w-full"
					disabled={loading}
				/>
				<p class="text-xs text-slate-400 mt-1">
					Name for the symbolic link in your RAG directory
				</p>
			</div>
		</div>

		<!-- Include Patterns -->
		<div class="space-y-2">
			<label class="block text-slate-300 text-sm font-medium">
				Include patterns (files to process)
			</label>

			<div class="flex gap-2">
				<Input
					bind:value={currentInclude}
					placeholder="e.g., *.py, docs/**/*.md"
					class="flex-1"
					onkeydown={handleIncludeKeydown}
				/>
				<Button
					onclick={addIncludePattern}
					disabled={loading || !currentInclude.trim()}
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
								disabled={includePatterns.length === 1}
							>
								<X size={12} />
							</Button>
						{/if}
					</div>
				{/each}
			</div>
		</div>

		<!-- Exclude Patterns -->
		<div class="space-y-2">
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

		<!-- Examples -->
		<div class="bg-slate-800/50 rounded-lg p-4">
			<h4 class="text-slate-300 text-sm font-medium mb-2 flex items-center gap-2">
				<AlertCircle size={16} />
				Pattern Examples
			</h4>
			<div class="space-y-1 text-xs text-slate-400">
				<div><code class="bg-slate-700 px-1 py-0.5 rounded">**/*</code> - All files (default)</div>
				<div><code class="bg-slate-700 px-1 py-0.5 rounded">**/*.ts</code> - TypeScript files everywhere</div>
				<div><code class="bg-slate-700 px-1 py-0.5 rounded">src/**/*.md</code> - Markdown files in src folder and subfolders</div>
				<div><code class="bg-slate-700 px-1 py-0.5 rounded">*.log</code> - Exclude log files</div>
				<div><code class="bg-slate-700 px-1 py-0.5 rounded">**/node_modules/**</code> - Exclude all files in all node_modules folders</div>
			</div>
		</div>

		<div class="bg-slate-800/50 border border-slate-600 rounded-lg p-4">
			<div class="flex items-start space-x-3">
				<FolderOpen class="w-5 h-5 text-cyan-400 mt-0.5 flex-shrink-0" />
				<div class="text-sm text-slate-300">
					<p class="font-medium mb-1">How symbolic links work:</p>
					<ul class="space-y-1 text-slate-400 list-disc list-inside text-xs">
						<li>Links reference files/folders outside your RAG directory</li>
						<li>LlamaIndex will automatically include linked content during indexing</li>
						<li>Changes to the original files will be reflected when you reindex</li>
						<li>Perfect for large document repositories or shared folders</li>
						<li>File filters will apply to all files found through the symbolic link</li>
					</ul>
				</div>
			</div>
		</div>
	</div>

	<div class="flex justify-end space-x-3 pt-4 border-t border-slate-600">
		<Button
			onclick={() => open = false}
			disabled={loading}
			variant="secondary"
		>
			<X size={16} />
			Cancel
		</Button>
		<Button
			onclick={createSymlink}
			disabled={loading || !targetPath.trim() || !linkName.trim()}
			variant="primary"
		>
			{#if loading}
				<Loader size={16} class="animate-spin" />
				Creating...
			{:else}
				<Link size={16} />
				Create Link
			{/if}
		</Button>
	</div>
</Modal>
