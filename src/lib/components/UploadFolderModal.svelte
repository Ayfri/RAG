<script lang="ts">
	import { FolderPlus, Loader, Plus, X, Check, AlertCircle, FolderOpen, Upload } from '@lucide/svelte';
	import Button from '$lib/components/common/Button.svelte';
	import Input from '$lib/components/common/Input.svelte';
	import Modal from '$lib/components/common/Modal.svelte';
	import { notifications } from '$lib/stores/notifications';
	import FileInput from './common/FileInput.svelte';

	interface Props {
		ragName?: string;
		open: boolean;
		onFolderUploaded: () => void; // New prop
	}

	let { ragName, open = $bindable(false), onFolderUploaded }: Props = $props(); // Destructure new prop

	const MAX_FILES_TO_SHOW = 200;

	let folderName = $state('');
	let selectedFiles = $state<File[]>([]);
	let includePatterns = $state<string[]>(['**/*']);
	let excludePatterns = $state<string[]>([]);
	let currentInclude = $state('');
	let currentExclude = $state('');
	let loading = $state(false);
	let processingFiles = $state(false);
	let editingIncludeIndex = $state<number | null>(null);
	let editingExcludeIndex = $state<number | null>(null);
	let editingIncludeValue = $state('');
	let editingExcludeValue = $state('');
	let hideIgnoredFiles = $state(false);

	// Computed filtered files
	let filteredFiles = $derived(() => {
		if (selectedFiles.length === 0) return [];

		const allFiles = selectedFiles.map(file => {
			const relativePath = file.webkitRelativePath;
			const isIncluded = includePatterns.some(pattern => matchesGlob(relativePath, pattern));
			const isExcluded = excludePatterns.some(pattern => matchesGlob(relativePath, pattern));

			return {
				file,
				relativePath,
				willBeProcessed: isIncluded && !isExcluded
			};
		});

		// Filter out ignored files if hideIgnoredFiles is true
		if (hideIgnoredFiles) {
			return allFiles.filter(f => f.willBeProcessed);
		}

		return allFiles;
	});

		// Glob matching function that mimics SimpleDirectoryReader's glob behavior
	function matchesGlob(path: string, pattern: string): boolean {
		// Handle special case for **/* which should match everything
		if (pattern === '**/*') {
			return true;
		}

		// Normalize path separators for consistent matching
		const normalizedPath = path.replace(/\\/g, '/');

		// Convert glob pattern to regex
		let regexPattern = pattern
			.replace(/\./g, '\\.') // Escape dots
			.replace(/\?/g, '[^/]') // ? matches any single character except /
			.replace(/\*\*/g, '__DOUBLE_STAR__') // Placeholder for **
			.replace(/\*/g, '[^/]*') // * matches any characters except /
			.replace(/__DOUBLE_STAR__/g, '.*'); // ** matches any characters including /

		// Create regex and test against the full path
		const regex = new RegExp(`^${regexPattern}$`);
		return regex.test(normalizedPath);
	}

	function reset() {
		folderName = '';
		selectedFiles = [];
		includePatterns = ['**/*'];
		excludePatterns = [];
		currentInclude = '';
		currentExclude = '';
		processingFiles = false;
		hideIgnoredFiles = false;
		editingIncludeIndex = null;
		editingExcludeIndex = null;
	}

	function addIncludePattern() {
		const pattern = currentInclude.trim();
		if (pattern && !includePatterns.includes(pattern)) {
			includePatterns = [...includePatterns, pattern];
			currentInclude = '';		}
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

	async function createFolder() {
		if (!ragName || !folderName.trim()) return;

		loading = true;
		try {
			// Create the folder with filters (empty folder first)
			const createFolderResponse = await fetch(`/api/rag/${ragName}/files`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					type: 'folder',
					name: folderName.trim(),
					include_patterns: includePatterns,
					exclude_patterns: excludePatterns
				})
			});

			if (!createFolderResponse.ok) {
				const errorData = await createFolderResponse.text();
				throw new Error(errorData || 'Failed to create folder');
			}

			// Upload filtered files one by one
			processingFiles = true;
			const filesToUpload = filteredFiles().filter(f => f.willBeProcessed).map(f => f.file);

			const uploadPromises = filesToUpload.map(async (file: File) => {
				const formData = new FormData();
				// Use the webkitRelativePath to maintain folder structure
				formData.append('file', file, file.webkitRelativePath);

				const uploadResponse = await fetch(`/api/rag/${ragName}/files`, {
					method: 'POST',
					body: formData
				});

				if (!uploadResponse.ok) {
					const errorData = await uploadResponse.text();
					// Log error but don't stop the whole process for one file
					console.error(`Failed to upload file ${file.webkitRelativePath}:`, errorData);
					notifications.add({
						type: 'error',
						message: `Failed to upload ${file.webkitRelativePath}: ${errorData || 'Unknown error'}`
					});
				}
			});

			await Promise.all(uploadPromises);

			notifications.add({
				type: 'success',
				message: `Folder "${folderName}" created and files uploaded successfully.`
			});

			reset();
			open = false;
			onFolderUploaded(); // Call the new prop on success
		} catch (error) {
			notifications.add({
				type: 'error',
				message: error instanceof Error ? error.message : 'Failed to create folder or upload files'
			});
		} finally {
			loading = false;
			processingFiles = false; // Ensure processingFiles is reset
		}
	}

	function handleFolderChange(e: Event) {
		const input = e.target as HTMLInputElement;
		const files = input.files;
		if (files && files.length > 0) {
			processingFiles = true;

			// Use setTimeout to allow UI to update before processing
			setTimeout(() => {
				selectedFiles = Array.from(files);
				folderName = files[0].webkitRelativePath.split('/')[0];
				processingFiles = false;
			}, 50);
		}
	}

	$effect(() => {
		if (!open) {
			reset();
		}
	});
</script>

<Modal bind:open title="Upload Folder with File Filters" size="lg">
	<div class="space-y-3">
		<!-- Folder Name -->
		<div>
			<label class="block text-slate-300 text-sm font-medium mb-2">
				{folderName || 'Select a folder'}
			</label>
			<div class="flex items-center gap-2">
				<Button
					class="bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700"
					onclick={() => {
						const fileInput = document.getElementById('folder-input') as HTMLInputElement;
						fileInput?.click();
					}}
					variant="primary"
					disabled={loading || processingFiles}
				>
					{#if processingFiles}
						<Loader size={16} class="animate-spin" />
						Processing...
					{:else}
						<Upload size={16} />
						Select
					{/if}
				</Button>
			</div>
			<FileInput
				disabled={loading || processingFiles}
				id="folder-input"
				onchange={handleFolderChange}
				webkitdirectory
			/>
		</div>

		<!-- Selected Files Display -->
		{#if selectedFiles.length > 0}
			{@const allFiles = selectedFiles.map(file => {
				const relativePath = file.webkitRelativePath;
				const isIncluded = includePatterns.some(pattern => matchesGlob(relativePath, pattern));
				const isExcluded = excludePatterns.some(pattern => matchesGlob(relativePath, pattern));
				return { file, relativePath, willBeProcessed: isIncluded && !isExcluded };
			})}
			{@const processedCount = allFiles.filter(f => f.willBeProcessed).length}
			{@const skippedCount = allFiles.length - processedCount}
			<div class="bg-slate-800/50 rounded-lg p-3">
				<div class="flex items-center justify-between mb-2">
					<h4 class="text-slate-300 text-sm font-medium flex items-center gap-2">
						<FolderOpen size={16} />
						Selected Files ({selectedFiles.length})

						<span class="text-xs bg-green-900/30 text-green-200 px-2 py-1 rounded">
							{processedCount} will be processed
						</span>
						{#if skippedCount > 0}
							<span class="text-xs bg-red-900/30 text-red-200 px-2 py-1 rounded">
								{skippedCount} will be skipped
							</span>
						{/if}
					</h4>

					{#if skippedCount > 0}
						<label class="flex items-center gap-2 text-xs text-slate-300">
							<input
								type="checkbox"
								bind:checked={hideIgnoredFiles}
								class="w-3 h-3 text-blue-600 bg-slate-700 border-slate-600 rounded focus:ring-blue-500 focus:ring-2"
							/>
							Hide ignored files
						</label>
					{/if}
				</div>
				<div class="space-y-1 text-xs max-h-32 overflow-y-auto">
					{#each filteredFiles().slice(0, MAX_FILES_TO_SHOW) as { relativePath, willBeProcessed }}
						<div class="flex items-center gap-2">
							<span
								class="w-2 h-2 rounded-full flex-shrink-0 {willBeProcessed ? 'bg-green-500' : 'bg-red-500'}"
							></span>
							<span
								class="truncate {willBeProcessed || hideIgnoredFiles ? 'text-slate-300' : 'text-slate-500 line-through'}"
							>
								{relativePath}
							</span>
						</div>
					{/each}
					{#if filteredFiles().length > MAX_FILES_TO_SHOW}
						{@const remainingProcessed = filteredFiles().slice(MAX_FILES_TO_SHOW).filter(f => f.willBeProcessed).length}
						{@const remainingSkipped = filteredFiles().slice(MAX_FILES_TO_SHOW).length - remainingProcessed}
						<div class="flex items-center gap-2 text-slate-500 font-medium">
							<span class="w-2 h-2 bg-slate-500 rounded-full flex-shrink-0"></span>
							<span>
								... and {filteredFiles().length - MAX_FILES_TO_SHOW} more files
								{#if remainingProcessed > 0}
									<span class="text-green-400">({remainingProcessed} processed</span>{#if remainingSkipped > 0}, <span class="text-red-400">{remainingSkipped} skipped</span>{/if})
								{:else if remainingSkipped > 0}
									<span class="text-red-400">({remainingSkipped} skipped)</span>
								{/if}
							</span>
						</div>
					{/if}
				</div>
			</div>
		{/if}

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
				<div><code class="bg-slate-700 px-1 py-0.5 rounded">*.py</code> - Python files in current folder</div>
				<div><code class="bg-slate-700 px-1 py-0.5 rounded">**/*.ts</code> - TypeScript files everywhere</div>
				<div><code class="bg-slate-700 px-1 py-0.5 rounded">src/**/*.md</code> - Markdown files in src folder and subfolders</div>
				<div><code class="bg-slate-700 px-1 py-0.5 rounded">*.log</code> - Exclude log files</div>
				<div><code class="bg-slate-700 px-1 py-0.5 rounded">**/node_modules/**</code> - Exclude all files in all node_modules folders</div>
			</div>
		</div>
	</div>

	<div class="flex justify-end gap-3 pt-4 border-t border-slate-700">
		<Button
			onclick={() => open = false}
			variant="secondary"
			disabled={loading}
		>
			<X size={16} />
			Cancel
		</Button>
		<Button
			onclick={createFolder}
			disabled={loading || !folderName.trim()}
		>
			{#if loading}
				<Loader size={16} class="animate-spin" />
				Creating...
			{:else}
				<FolderPlus size={16} />
				Upload Folder
			{/if}
		</Button>
	</div>
</Modal>
