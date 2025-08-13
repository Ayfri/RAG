<script lang="ts">
	import { FileText, Trash2, Upload, RefreshCw, Link, FolderOpen, Loader, HardDrive, Clock, FileStack, Settings, FolderPlus, Globe } from '@lucide/svelte';
	import Button from '$lib/components/common/Button.svelte';
	import FileInput from '$lib/components/common/FileInput.svelte';
	import CreateSymlinkModal from '$lib/components/modals/CreateSymlinkModal.svelte';
	import UploadFolderModal from '$lib/components/modals/UploadFolderModal.svelte';
	import ConfigureFiltersModal from '$lib/components/modals/ConfigureFiltersModal.svelte';
	import AddUrlModal from '$lib/components/modals/AddUrlModal.svelte';
	import Modal from '$lib/components/common/Modal.svelte';
	import { notifications } from '$lib/stores/notifications';

	interface FileItem {
		name: string;
		type: 'file' | 'directory';
		is_symlink: boolean;
		target?: string;
		resolved_target_type?: 'file' | 'directory' | 'unknown';
		file_count?: number;
		size?: number;
		last_modified?: number;
	}

	interface UrlItem {
		url: string;
		title?: string;
		added_at?: string;
	}

	interface Props {
		ragName: string;
		open: boolean;
	}

	let { ragName, open = $bindable(false) }: Props = $props();

	// Local state
	let files: FileItem[] = $state([]);
	let urls: UrlItem[] = $state([]);
	let loading = $state(false);
	let uploading = $state(false);
	let reindexing = $state(false);
	let deletingUrl = $state(false);

	// Modal states
	let showSymlinkModal = $state(false);
	let showFiltersModal = $state(false);
	let showUploadFolderModal = $state(false);
	let showAddUrlModal = $state(false);
	let selectedFolder = $state<string | null>(null);

	function getFileIcon(item: FileItem) {
		if (item.type === 'directory') {
			return item.is_symlink ? Link : FolderOpen;
		} else {
			return item.is_symlink ? Link : FileText;
		}
	}

	function formatBytes(bytes: number, decimals = 2) {
		if (bytes === 0) return '0 Bytes';
		const k = 1024;
		const dm = decimals < 0 ? 0 : decimals;
		const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
		const i = Math.floor(Math.log(bytes) / Math.log(k));
		return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
	}

	function formatDate(timestamp: number) {
		return new Date(timestamp * 1000).toLocaleString();
	}

	const totalSize = $derived(files.reduce((acc, file) => acc + (file.size ?? 0), 0));
	const totalItems = $derived(files.length + urls.length);

	// API functions
	async function loadFiles() {
		try {
			loading = true;
			const res = await fetch(`/api/rag/${ragName}/files`);
			if (!res.ok) throw new Error('Failed to load files');
			files = await res.json();
		} catch (err) {
			console.error('Failed to load files:', err);
		} finally {
			loading = false;
		}
	}

	async function loadUrls() {
		try {
			const res = await fetch(`/api/rag/${ragName}/urls`);
			if (!res.ok) throw new Error('Failed to load URLs');
			urls = await res.json();
		} catch (err) {
			console.error('Failed to load URLs:', err);
		}
	}

	async function deleteUrl(url: string) {
		if (deletingUrl) return; // Prevent multiple clicks

		try {
			deletingUrl = true;
			const res = await fetch(`/api/rag/${ragName}/urls`, {
				method: 'DELETE',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ url })
			});
			if (!res.ok) throw new Error('Failed to delete URL');

			notifications.success('URL deleted successfully!');
			await loadUrls();
			await loadFiles(); // Also reload files to update the UI
		} catch (err) {
			notifications.error(`Delete failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
		} finally {
			deletingUrl = false;
		}
	}

	async function deleteFile(filename: string) {
		try {
			const res = await fetch(`/api/rag/${ragName}/files/${filename}`, { method: 'DELETE' });
			if (!res.ok) throw new Error('Failed to delete file');

			notifications.success(`Deleted ${filename}`);
			await loadFiles();
		} catch (err) {
			notifications.error(`Delete failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
		}
	}

	async function uploadFile(event: Event) {
		const input = event.target as HTMLInputElement;
		const file = input.files?.[0];
		if (!file) return;

		try {
			uploading = true;
			const formData = new FormData();
			formData.append('file', file);

			const res = await fetch(`/api/rag/${ragName}/files`, {
				method: 'POST',
				body: formData
			});

			if (!res.ok) throw new Error('Failed to upload file');

			notifications.success('File uploaded successfully!');
			await loadFiles();
		} catch (err) {
			notifications.error(`Upload failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
		} finally {
			uploading = false;
			input.value = '';
		}
	}

	async function uploadFolder(event: Event) {
		const input = event.target as HTMLInputElement;
		const files_list = input.files;
		if (!files_list || files_list.length === 0) return;

		try {
			uploading = true;

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

			notifications.success('Folder uploaded successfully!');
			await loadFiles();
		} catch (err) {
			notifications.error(`Folder upload failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
		} finally {
			uploading = false;
			input.value = '';
		}
	}

	async function reindexRAG() {
		try {
			reindexing = true;
			const res = await fetch(`/api/rag/${ragName}/reindex`, { method: 'POST' });
			if (!res.ok) throw new Error('Failed to reindex RAG');

			notifications.success('RAG reindexed successfully!');
			await loadFiles(); // Reload files after successful reindex
		} catch (err) {
			notifications.error(`Reindex failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
		} finally {
			reindexing = false;
		}
	}

	function handleSymlinkCreated() {
		loadFiles();
	}

	function handleUrlAdded() {
		loadUrls();
	}

	// Load data when modal opens
	$effect(() => {
		if (open && ragName) {
			loadFiles();
			loadUrls();
		}
	});
</script>

<Modal title="Manage Files" bind:open size="xl">
	<div class="flex flex-col h-full">
		<!-- Action buttons - responsive grid -->
		<div class="p-3 sm:p-4 border-b border-slate-700">
			<div class="grid grid-cols-2 sm:grid-cols-5 gap-2 sm:gap-3">
				<Button
					onclick={reindexRAG}
					disabled={reindexing}
					class="flex items-center justify-center space-x-1 sm:space-x-2 px-2 sm:px-3 py-2 bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white rounded-lg cursor-pointer text-xs sm:text-sm font-medium transition-all duration-200"
					title="Manually reindex RAG"
				>
					{#if reindexing}
						<Loader size={16} class="animate-spin sm:w-[18px] sm:h-[18px]" />
						<span class="hidden sm:inline">Reindexing...</span>
						<span class="sm:hidden">Reindex</span>
					{:else}
						<RefreshCw size={16} class="sm:w-[18px] sm:h-[18px]" />
						<span class="hidden sm:inline">Reindex All</span>
						<span class="sm:hidden">Reindex</span>
					{/if}
				</Button>

				<Button
					onclick={() => showSymlinkModal = true}
					class="flex items-center justify-center space-x-1 sm:space-x-2 px-2 sm:px-3 py-2 bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 text-white rounded-lg cursor-pointer text-xs sm:text-sm font-medium transition-all duration-200"
					title="Create symbolic link"
				>
					<Link size={16} class="sm:w-[18px] sm:h-[18px]" />
					<span class="hidden sm:inline">Create Link</span>
					<span class="sm:hidden">Link</span>
				</Button>

				<label class="flex items-center justify-center space-x-1 sm:space-x-2 px-2 sm:px-3 py-2 bg-gradient-to-r from-cyan-500 to-cyan-600 hover:from-cyan-600 hover:to-cyan-700 text-white rounded-lg cursor-pointer text-xs sm:text-sm font-medium transition-all duration-200">
					{#if uploading}
						<Loader size={16} class="animate-spin sm:w-[18px] sm:h-[18px]" />
						<span class="hidden sm:inline">Uploading...</span>
						<span class="sm:hidden">Upload</span>
					{:else}
						<Upload size={16} class="sm:w-[18px] sm:h-[18px]" />
						<span class="hidden sm:inline">Upload File</span>
						<span class="sm:hidden">File</span>
					{/if}
					<FileInput
						accept='.txt,.pdf,.docx,.md'
						disabled={uploading}
						id='file-input'
						onchange={uploadFile}
					/>
				</label>

				<Button
					onclick={() => showUploadFolderModal = true}
					class="flex items-center justify-center space-x-1 sm:space-x-2 px-2 sm:px-3 py-2 bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white rounded-lg cursor-pointer text-xs sm:text-sm font-medium transition-all duration-200"
					title="Upload a folder"
				>
					<FolderPlus size={16} class="sm:w-[18px] sm:h-[18px]" />
					<span class="hidden sm:inline">Upload Folder</span>
					<span class="sm:hidden">Folder</span>
				</Button>

				<Button
					onclick={() => showAddUrlModal = true}
					class="flex items-center justify-center space-x-1 sm:space-x-2 px-2 sm:px-3 py-2 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white rounded-lg cursor-pointer text-xs sm:text-sm font-medium transition-all duration-200"
					title="Add a website URL"
				>
					<Globe size={16} class="sm:w-[18px] sm:h-[18px]" />
					<span class="hidden sm:inline">Add URL</span>
					<span class="sm:hidden">URL</span>
				</Button>
			</div>
		</div>

		<!-- Stats bar - responsive layout -->
		<div class="p-2 sm:p-3 bg-slate-800 border-b border-slate-700">
			<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-0 text-xs text-slate-400">
				<div class="flex items-center space-x-2">
					<FileStack size={16} class="sm:w-[18px] sm:h-[18px]" />
					<span>{totalItems} entries</span>
					<span class="px-2 py-0.5 rounded-full bg-slate-700 text-xs text-slate-300">{files.reduce((acc, file) => acc + (file.file_count ?? 0), 0)} files</span>
					{#if urls.length > 0}
						<span class="px-2 py-0.5 rounded-full bg-blue-700 text-xs text-blue-300">{urls.length} URLs</span>
					{/if}
				</div>
				<div class="flex items-center space-x-2">
					<HardDrive size={16} class="sm:w-[18px] sm:h-[18px]" />
					<span>Total: {formatBytes(totalSize)}</span>
				</div>
			</div>
		</div>

		{#if reindexing}
			<div class="flex-1 flex flex-col items-center justify-center p-4 sm:p-6 text-center bg-slate-900/50">
				<Loader size={48} class="animate-spin text-orange-400 sm:w-16 sm:h-16" />
				<h3 class="mt-4 text-base sm:text-lg font-semibold text-slate-200">Rebuilding Index</h3>
				<p class="mt-1 text-xs sm:text-sm text-slate-400 px-4">This may take a few moments. Please don't close this window.</p>
				<div class="w-full max-w-md bg-slate-700 rounded-full h-2 sm:h-2.5 mt-4">
					<div class="bg-orange-500 h-2 sm:h-2.5 rounded-full animate-pulse"></div>
				</div>
			</div>
		{:else}
			<div class="flex-1 overflow-y-auto">
				{#if loading}
					<div class="p-4 sm:p-6 text-center">
						<Loader size={48} class="animate-spin text-cyan-400 mx-auto mb-4 sm:w-16 sm:h-16" />
						<p class="text-slate-300 text-sm sm:text-md">Loading files...</p>
					</div>
				{:else if files.length === 0 && urls.length === 0}
					<div class="p-4 sm:p-6 text-center">
						<FileText size={48} class="text-slate-600 mx-auto mb-4 sm:w-16 sm:h-16" />
						<p class="text-slate-300 font-semibold text-base sm:text-lg">No Documents</p>
						<p class="text-slate-500 text-xs sm:text-sm mt-1 px-4">Upload files or folders to get started.</p>
					</div>
				{:else}
					<div class="divide-y divide-slate-800">
						{#each files as file}
							{@const IconComponent = getFileIcon(file)}
							<div class="p-3 sm:p-2.5 hover:bg-slate-700/50 transition-all duration-200 group active:bg-slate-700/75">
								<!-- Mobile layout (single column) -->
								<div class="sm:hidden">
									<div class="flex items-start justify-between">
										<div class="flex items-start space-x-3 flex-1 min-w-0">
											<IconComponent size={18} class="flex-shrink-0 mt-0.5 {file.is_symlink ? 'text-purple-400' : file.type === 'directory' ? 'text-blue-400' : 'text-cyan-400'}" />
											<div class="min-w-0 flex-1">
												<span class="text-slate-200 text-sm font-medium block {file.is_symlink ? 'italic' : ''}">{file.name}</span>
												{#if file.is_symlink && file.target}
													<div class="text-xs text-slate-500 mt-1 break-all">→ {file.target}</div>
												{/if}
												<div class="flex flex-wrap items-center gap-3 mt-2 text-xs text-slate-400">
													<div class="flex items-center space-x-1">
														<HardDrive size={14} />
														<span>{file.size != null ? formatBytes(file.size) : 'N/A'}</span>
													</div>
													{#if (file.type === 'directory' || (file.is_symlink && file.resolved_target_type === 'directory')) && file.file_count != null}
														<span class="px-2 py-0.5 rounded-full bg-slate-700 text-xs text-slate-300">{file.file_count} files</span>
													{/if}
													<div class="flex items-center space-x-1">
														<Clock size={14} />
														<span>{file.last_modified ? formatDate(file.last_modified) : 'N/A'}</span>
													</div>
												</div>
											</div>
										</div>
										<div class="flex items-center space-x-1 ml-2">
											{#if file.type === 'directory' || file.is_symlink}
												<Button
													onclick={() => { selectedFolder = file.name; showFiltersModal = true; }}
													size="icon"
													variant="secondary"
													title="Configure filters for {file.name}"
												>
													<Settings size={14} />
												</Button>
											{/if}
											<Button
												onclick={() => deleteFile(file.name)}
												size="icon"
												variant="danger"
												title="Delete {file.type}"
											>
												<Trash2 size={16} />
											</Button>
										</div>
									</div>
								</div>

								<!-- Desktop layout (grid) -->
								<div class="hidden sm:grid grid-cols-12 items-center gap-4">
									<div class="col-span-5 flex items-center space-x-3">
										<IconComponent size={18} class="flex-shrink-0 {file.is_symlink ? 'text-purple-400' : file.type === 'directory' ? 'text-blue-400' : 'text-cyan-400'}" />
										<div class="min-w-0 flex-1">
											<span class="text-slate-200 text-base font-medium block truncate {file.is_symlink ? 'italic' : ''}">{file.name}</span>
											{#if file.is_symlink && file.target}
												<div class="text-xs text-slate-500 truncate mt-1">→ {file.target}</div>
											{/if}
										</div>
									</div>

									<div class="col-span-2 text-sm text-slate-400 flex items-center space-x-2">
										<HardDrive size={18} />
										<span>{file.size != null ? formatBytes(file.size) : 'N/A'}</span>
										{#if (file.type === 'directory' || (file.is_symlink && file.resolved_target_type === 'directory')) && file.file_count != null}
											<span class="ml-2 px-2 py-0.5 rounded-full bg-slate-700 text-xs text-slate-300">{file.file_count} files</span>
										{/if}
									</div>

									<div class="col-span-3 text-sm text-slate-400 flex items-center space-x-2">
										<Clock size={18} />
										<span>{file.last_modified ? formatDate(file.last_modified) : 'N/A'}</span>
									</div>

									<div class="col-span-2 flex justify-end space-x-1">
										{#if file.type === 'directory' || file.is_symlink}
											<Button
												onclick={() => { selectedFolder = file.name; showFiltersModal = true; }}
												size="icon"
												variant="secondary"
												title="Configure filters for {file.name}"
											>
												<Settings size={16} />
											</Button>
										{/if}
										<Button
											onclick={() => deleteFile(file.name)}
											size="icon"
											variant="danger"
											title="Delete {file.type}"
										>
											<Trash2 size={18} />
										</Button>
									</div>
								</div>
							</div>
						{/each}
					</div>
				{/if}

				<!-- URLs Section -->
				{#if urls.length > 0}
					<div class="divide-y divide-slate-800">
						{#each urls as url}
							<div class="px-2.5 py-1 hover:bg-slate-700/50 transition-all duration-200 group active:bg-slate-700/75">
								<!-- Mobile layout (single column) -->
								<div class="sm:hidden">
									<div class="flex items-start justify-between">
										<div class="flex items-start space-x-3 flex-1 min-w-0">
											<Globe size={18} class="flex-shrink-0 mt-0.5 text-blue-400" />
											<div class="min-w-0 flex-1">
												<a href={url.url} target="_blank" rel="noopener" class="text-slate-200 text-sm font-medium block hover:text-blue-300 transition-colors">
													{url.title || url.url}
												</a>
												<div class="text-xs text-slate-500 break-all">{url.url}</div>
												{#if url.added_at}
													<div class="flex items-center space-x-1 mt-2 text-xs text-slate-400">
														<Clock size={14} />
														<span>{new Date(url.added_at).toLocaleString()}</span>
													</div>
												{/if}
											</div>
										</div>
										<div class="flex items-center ml-2">
											<Button
												onclick={(e) => {
													e.preventDefault();
													e.stopPropagation();
													deleteUrl(url.url);
												}}
												size="icon"
												variant="danger"
												title="Delete URL"
												disabled={deletingUrl}
											>
												<Trash2 size={16} />
											</Button>
										</div>
									</div>
								</div>

								<!-- Desktop layout (grid) -->
								<div class="hidden sm:grid grid-cols-12 items-center gap-4">
									<div class="col-span-8 flex items-center space-x-3">
										<Globe size={18} class="flex-shrink-0 text-blue-400" />
										<div class="min-w-0 flex-1">
											<a href={url.url} target="_blank" rel="noopener" class="text-slate-200 text-base font-medium block truncate hover:text-blue-300 transition-colors">
												{url.title || url.url}
											</a>
											<div class="text-xs text-slate-500 truncate">{url.url}</div>
										</div>
									</div>

									<div class="col-span-2 text-sm text-slate-400 flex items-center space-x-2">
										<Clock size={18} />
										<span>{url.added_at ? new Date(url.added_at).toLocaleString() : 'N/A'}</span>
									</div>

									<div class="col-span-2 flex justify-end space-x-1">
										<Button
											onclick={(e) => {
												e.preventDefault();
												e.stopPropagation();
												deleteUrl(url.url);
											}}
											size="icon"
											variant="danger"
											title="Delete URL"
											disabled={deletingUrl}
										>
											<Trash2 size={18} />
										</Button>
									</div>
								</div>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		{/if}
	</div>
</Modal>

<CreateSymlinkModal
	{ragName}
	bind:open={showSymlinkModal}
	onSymlinkCreated={handleSymlinkCreated}
/>

<UploadFolderModal
	{ragName}
	bind:open={showUploadFolderModal}
	onFolderUploaded={reindexRAG}
/>

<ConfigureFiltersModal
	{ragName}
	bind:open={showFiltersModal}
	folderName={selectedFolder}
/>

<AddUrlModal
	{ragName}
	bind:open={showAddUrlModal}
	onUrlAdded={handleUrlAdded}
/>
