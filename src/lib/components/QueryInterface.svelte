<script lang="ts">
	import { Send, Loader, FileText, Trash2, Upload, Zap, RefreshCw, Link, FolderOpen } from '@lucide/svelte';
	import Button from '$lib/components/common/Button.svelte';
	import TextArea from '$lib/components/common/TextArea.svelte';
	import FileInput from '$lib/components/common/FileInput.svelte';
	import CreateSymlinkModal from '$lib/components/CreateSymlinkModal.svelte';
	import Markdown from '$lib/components/common/Markdown.svelte';

	interface Props {
		ragName: string;
	}

	interface FileItem {
		name: string;
		type: 'file' | 'directory';
		is_symlink: boolean;
		target?: string;
		resolved_target_type?: 'file' | 'directory' | 'unknown';
		file_count?: number;
	}

	let { ragName }: Props = $props();

	let query = $state('');
	let response = $state('');
	let loading = $state(false);
	let streaming = $state(false);
	let files: FileItem[] = $state([]);
	let loadingFiles = $state(false);
	let uploadingFile = $state(false);
	let reindexing = $state(false);
	let showSymlinkModal = $state(false);

	async function submitQuery(useStream = false) {
		if (!query.trim() || loading) return;

		try {
			loading = true;
			streaming = useStream;
			response = '';

			if (useStream) {
				const res = await fetch(`/api/rag/${ragName}/stream`, {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({ query: query.trim() })
				});

				if (!res.ok) throw new Error('Failed to stream response');

				const reader = res.body?.getReader();
				if (!reader) throw new Error('No response body');

				const decoder = new TextDecoder();

				while (true) {
					const { done, value } = await reader.read();
					if (done) break;

					const chunk = decoder.decode(value);
					response += chunk;
				}
			} else {
				const res = await fetch(`/api/rag/${ragName}/query`, {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({ query: query.trim() })
				});

				if (!res.ok) throw new Error('Failed to get response');
				const data = await res.json();
				response = data.content || 'No response received';
			}
		} catch (err) {
			response = `Error: ${err instanceof Error ? err.message : 'Unknown error'}`;
		} finally {
			loading = false;
			streaming = false;
		}
	}

	async function loadFiles() {
		try {
			loadingFiles = true;
			const res = await fetch(`/api/rag/${ragName}/files`);
			if (!res.ok) throw new Error('Failed to load files');
			files = await res.json();
		} catch (err) {
			console.error('Failed to load files:', err);
		} finally {
			loadingFiles = false;
		}
	}

	async function uploadFile(event: Event) {
		const input = event.target as HTMLInputElement;
		const file = input.files?.[0];
		if (!file) return;

		try {
			uploadingFile = true;
			const formData = new FormData();
			formData.append('file', file);

			const res = await fetch(`/api/rag/${ragName}/files`, {
				method: 'POST',
				body: formData
			});

			if (!res.ok) throw new Error('Failed to upload file');

			loadFiles();
		} catch (err) {
			alert(`Upload failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
		} finally {
			uploadingFile = false;
			input.value = '';
		}
	}

	async function uploadFolder(event: Event) {
		const input = event.target as HTMLInputElement;
		const files_list = input.files;
		if (!files_list || files_list.length === 0) return;

		try {
			uploadingFile = true;

			// Upload each file individually
			for (const file of files_list) {
				const formData = new FormData();
				formData.append('file', file);

				const res = await fetch(`/api/rag/${ragName}/files`, {
					method: 'POST',
					body: formData
				});

				if (!res.ok) throw new Error(`Failed to upload ${file.name}`);
			}

			loadFiles();
		} catch (err) {
			alert(`Folder upload failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
		} finally {
			uploadingFile = false;
			input.value = '';
		}
	}

	async function deleteFile(filename: string) {
		if (!confirm(`Delete ${filename}?`)) return;

		try {
			const res = await fetch(`/api/rag/${ragName}/files/${filename}`, { method: 'DELETE' });
			if (!res.ok) throw new Error('Failed to delete file');

			loadFiles();
		} catch (err) {
			alert(`Delete failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
		}
	}

	async function reindexRAG() {
		if (!confirm('Reindex this RAG? This will rebuild the vector index from all current files.')) return;

		try {
			reindexing = true;
			const res = await fetch(`/api/rag/${ragName}/reindex`, { method: 'POST' });
			if (!res.ok) throw new Error('Failed to reindex RAG');

			alert('RAG reindexed successfully!');
		} catch (err) {
			alert(`Reindex failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
		} finally {
			reindexing = false;
		}
	}

	function handleSymlinkCreated() {
		loadFiles();
	}

	function getFileIcon(item: FileItem) {
		if (item.type === 'directory') {
			return item.is_symlink ? FolderOpen : FolderOpen;
		} else {
			return item.is_symlink ? Link : FileText;
		}
	}

	function getFileDisplayName(item: FileItem) {
		if (item.is_symlink && item.target) {
			return `${item.name} → ${item.target}`;
		}
		return item.name;
	}

	// Load files when component mounts or ragName changes
	$effect(() => {
		if (ragName) {
			loadFiles();
		}
	});
</script>

<div class="space-y-8">
	<!-- Query Section -->
	<div class="glass rounded-2xl shadow-2xl overflow-hidden">
		<div class="p-6 border-b border-slate-600 bg-gradient-to-r from-slate-800 to-slate-700">
			<h2 class="text-xl font-bold text-slate-100">
				Query RAG: <span class="text-cyan-400">{ragName}</span>
			</h2>
		</div>
		<div class="p-6">
			<div class="space-y-6">
				<div>
					<label for="query" class="block text-sm font-medium text-slate-200 mb-3">
						Ask a question about your documents
					</label>
					<TextArea
						id="query"
						bind:value={query}
						placeholder="What would you like to know about your documents?"
						rows={4}
						onkeydown={(e) => {
							if (e.key === 'Enter' && !e.shiftKey) {
								e.preventDefault();
								submitQuery();
							}
						}}
					/>
				</div>

				<div class="flex space-x-4">
					<Button
						onclick={() => submitQuery(false)}
						disabled={!query.trim() || loading}
						class="group flex items-center space-x-3 px-6 py-3 bg-gradient-to-r from-cyan-500 to-cyan-600 hover:from-cyan-600 hover:to-cyan-700 text-white rounded-xl font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-cyan-500/25 cursor-pointer"
						variant="primary"
					>
						{#if loading && !streaming}
							<Loader class="w-5 h-5 animate-spin" />
						{:else}
							<Send class="w-5 h-5 group-hover:translate-x-1 transition-transform duration-200" />
						{/if}
						<span>Ask</span>
					</Button>

					<Button
						onclick={() => submitQuery(true)}
						disabled={!query.trim() || loading}
						class="group flex items-center space-x-3 px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white rounded-xl font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-green-500/25 cursor-pointer"
					>
						{#if loading && streaming}
							<Loader class="w-5 h-5 animate-spin" />
						{:else}
							<Zap class="w-5 h-5 group-hover:scale-110 transition-transform duration-200" />
						{/if}
						<span>Stream</span>
					</Button>
				</div>
			</div>
		</div>
	</div>

	<!-- Response Section -->
	{#if response}
		<div class="glass rounded-2xl shadow-2xl overflow-hidden">
			<div class="p-6 border-b border-slate-600 bg-gradient-to-r from-slate-800 to-slate-700">
				<h3 class="text-xl font-bold text-slate-100">Response</h3>
			</div>
			<div class="p-6">
				<div class="bg-slate-800/50 rounded-xl p-6 border border-slate-600">
					<Markdown content={response} />
				</div>
			</div>
		</div>
	{/if}

	<!-- Files Management -->
	<div class="glass rounded-2xl shadow-2xl overflow-hidden">
		<div class="p-6 border-b border-slate-600 bg-gradient-to-r from-slate-800 to-slate-700">
			<div class="flex justify-between items-center">
				<h3 class="text-xl font-bold text-slate-100 flex items-center space-x-3">
					<FileText class="w-6 h-6 text-cyan-400" />
					<span>Documents</span>
				</h3>
				<div class="flex space-x-3">
					<Button
						onclick={reindexRAG}
						disabled={reindexing}
						class="group flex items-center space-x-2 px-3 py-2 bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white rounded-xl cursor-pointer text-sm font-medium transition-all duration-200 shadow-lg hover:shadow-orange-500/25"
						title="Manually reindex RAG"
					>
						{#if reindexing}
							<Loader class="w-4 h-4 animate-spin" />
							<span>Reindexing...</span>
						{:else}
							<RefreshCw class="w-4 h-4 group-hover:rotate-90 transition-transform duration-200" />
							<span>Reindex</span>
						{/if}
					</Button>

					<Button
						onclick={() => showSymlinkModal = true}
						class="group flex items-center space-x-2 px-3 py-2 bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 text-white rounded-xl cursor-pointer text-sm font-medium transition-all duration-200 shadow-lg hover:shadow-purple-500/25"
						title="Create symbolic link"
					>
						<Link class="w-4 h-4 group-hover:scale-110 transition-transform duration-200" />
						<span>Link</span>
					</Button>

					<label class="group flex items-center space-x-2 px-3 py-2 bg-gradient-to-r from-cyan-500 to-cyan-600 hover:from-cyan-600 hover:to-cyan-700 text-white rounded-xl cursor-pointer text-sm font-medium transition-all duration-200 shadow-lg hover:shadow-cyan-500/25">
						{#if uploadingFile}
							<Loader class="w-4 h-4 animate-spin" />
							<span>Uploading...</span>
						{:else}
							<Upload class="w-4 h-4 group-hover:-translate-y-1 transition-transform duration-200" />
							<span>Add File</span>
						{/if}
						<FileInput
							accept='.txt,.pdf,.docx,.md'
							disabled={uploadingFile}
							id='file-input'
							onchange={uploadFile}
						/>
					</label>

					<label class="group flex items-center space-x-2 px-3 py-2 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white rounded-xl cursor-pointer text-sm font-medium transition-all duration-200 shadow-lg hover:shadow-blue-500/25">
						{#if uploadingFile}
							<Loader class="w-4 h-4 animate-spin" />
							<span>Uploading...</span>
						{:else}
							<FolderOpen class="w-4 h-4 group-hover:scale-110 transition-transform duration-200" />
							<span>Add Folder</span>
						{/if}
						<input
							type="file"
							webkitdirectory
							disabled={uploadingFile}
							id='folder-input'
							onchange={uploadFolder}
							class="hidden"
						/>
					</label>
				</div>
			</div>
		</div>
		<div class="divide-y divide-slate-600">
			{#if loadingFiles}
				<div class="p-8 text-center">
					<Loader class="w-8 h-8 animate-spin text-cyan-400 mx-auto mb-3" />
					<p class="text-slate-400">Loading files...</p>
				</div>
			{:else if files.length === 0}
				<div class="p-8 text-center">
					<FileText class="w-16 h-16 text-slate-600 mx-auto mb-4" />
					<p class="text-slate-300 font-medium">No documents in this RAG</p>
					<p class="text-slate-500 text-sm mt-1">Upload some files to get started</p>
				</div>
			{:else}
				{#each files as file}
					{@const IconComponent = getFileIcon(file)}
					<div class="p-4 flex items-center justify-between hover:bg-slate-700/30 transition-all duration-200 group">
						<div class="flex items-center space-x-4">
							<IconComponent class="w-6 h-6 {file.is_symlink ? 'text-purple-400' : file.type === 'directory' ? 'text-blue-400' : 'text-cyan-400'}" />
							<div>
								<span class="text-slate-200 group-hover:text-cyan-300 transition-colors {file.is_symlink ? 'italic' : ''}">{file.name}</span>
								{#if file.is_symlink && file.target}
									<div class="text-xs text-slate-500">→ {file.target}</div>
									{#if file.resolved_target_type === 'directory' && file.file_count !== undefined}
										<div class="text-xs text-slate-500">({file.file_count} files)</div>
									{/if}
								{/if}
								{#if file.type === 'directory' && !file.is_symlink}
									<div class="text-xs text-slate-500">Directory</div>
								{/if}
							</div>
						</div>
						<Button
							onclick={() => deleteFile(file.name)}
							class="p-2 text-slate-500 hover:text-red-400 hover:bg-red-900/20 rounded-lg transition-all duration-200 cursor-pointer"
							title="Delete {file.type}"
						>
							<Trash2 class="w-5 h-5" />
						</Button>
					</div>
				{/each}
			{/if}
		</div>
	</div>
</div>

<CreateSymlinkModal
	{ragName}
	isOpen={showSymlinkModal}
	onClose={() => showSymlinkModal = false}
	onSymlinkCreated={handleSymlinkCreated}
/>
