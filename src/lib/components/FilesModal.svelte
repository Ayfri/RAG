<script lang="ts">
	import { FileText, Trash2, Upload, RefreshCw, Link, FolderOpen, Loader, HardDrive, Clock, FileStack } from '@lucide/svelte';
	import Button from '$lib/components/common/Button.svelte';
	import FileInput from '$lib/components/common/FileInput.svelte';
	import CreateSymlinkModal from '$lib/components/CreateSymlinkModal.svelte';
	import Modal from '$lib/components/common/Modal.svelte';

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

	interface Props {
		ragName: string;
		files: FileItem[];
		loading: boolean;
		uploading: boolean;
		reindexing: boolean;
		onUploadFile: (event: Event) => void;
		onUploadFolder: (event: Event) => void;
		onDeleteFile: (filename: string) => void;
		onReindex: () => void;
		onSymlinkCreated: () => void;
		open: boolean;
	}

	let {
		ragName,
		files,
		loading,
		uploading,
		reindexing,
		onUploadFile,
		onUploadFolder,
		onDeleteFile,
		onReindex,
		onSymlinkCreated,
		open = $bindable(false)
	}: Props = $props();

	let showSymlinkModal = $state(false);

	function getFileIcon(item: FileItem) {
		if (item.type === 'directory') {
			return item.is_symlink ? Link : FolderOpen;
		} else {
			return item.is_symlink ? Link : FileText;
		}
	}

	function handleSymlinkCreated() {
		onSymlinkCreated();
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
</script>

<Modal title="Manage Files" bind:open size="xl">
	<div class="flex flex-col h-full">
		<div class="p-4 border-b border-slate-700">
			<div class="grid grid-cols-4 gap-3">
				<Button
					onclick={onReindex}
					disabled={reindexing}
					class="flex items-center justify-center space-x-2 px-3 py-2 bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white rounded-lg cursor-pointer text-sm font-medium transition-all duration-200"
					title="Manually reindex RAG"
				>
					{#if reindexing}
						<Loader class="w-4 h-4 animate-spin" />
						<span>Reindexing...</span>
					{:else}
						<RefreshCw class="w-4 h-4" />
						<span>Reindex All</span>
					{/if}
				</Button>

				<Button
					onclick={() => showSymlinkModal = true}
					class="flex items-center justify-center space-x-2 px-3 py-2 bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 text-white rounded-lg cursor-pointer text-sm font-medium transition-all duration-200"
					title="Create symbolic link"
				>
					<Link class="w-4 h-4" />
					<span>Create Link</span>
				</Button>

				<label class="flex items-center justify-center space-x-2 px-3 py-2 bg-gradient-to-r from-cyan-500 to-cyan-600 hover:from-cyan-600 hover:to-cyan-700 text-white rounded-lg cursor-pointer text-sm font-medium transition-all duration-200">
					{#if uploading}
						<Loader class="w-4 h-4 animate-spin" />
						<span>Uploading...</span>
					{:else}
						<Upload class="w-4 h-4" />
						<span>Upload File</span>
					{/if}
					<FileInput
						accept='.txt,.pdf,.docx,.md'
						disabled={uploading}
						id='file-input'
						onchange={onUploadFile}
					/>
				</label>

				<label class="flex items-center justify-center space-x-2 px-3 py-2 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white rounded-lg cursor-pointer text-sm font-medium transition-all duration-200">
					{#if uploading}
						<Loader class="w-4 h-4 animate-spin" />
						<span>Uploading...</span>
					{:else}
						<FolderOpen class="w-4 h-4" />
						<span>Upload Folder</span>
					{/if}
					<input
						type="file"
						webkitdirectory
						disabled={uploading}
						id='folder-input'
						onchange={onUploadFolder}
						class="hidden"
					/>
				</label>
			</div>
		</div>

		<div class="p-3 bg-slate-800 border-b border-slate-700 flex items-center justify-between text-xs text-slate-400">
			<div class="flex items-center space-x-2">
				<FileStack class="w-4 h-4" />
				<span>{files.length} entries</span>
				<span class="ml-2 px-2 py-0.5 rounded-full bg-slate-700 text-xs text-slate-300">{files.reduce((acc, file) => acc + (file.file_count ?? 0), 0)} total files</span>
			</div>
			<div class="flex items-center space-x-2">
				<HardDrive class="w-4 h-4" />
				<span>Total size: {formatBytes(totalSize)}</span>
			</div>
		</div>

		{#if reindexing}
			<div class="flex-1 flex flex-col items-center justify-center p-6 text-center bg-slate-900/50">
				<Loader class="w-12 h-12 animate-spin text-orange-400" />
				<h3 class="mt-4 text-lg font-semibold text-slate-200">Rebuilding Index</h3>
				<p class="mt-1 text-sm text-slate-400">This may take a few moments. Please don't close this window.</p>
				<div class="w-full max-w-md bg-slate-700 rounded-full h-2.5 mt-4">
					<div class="bg-orange-500 h-2.5 rounded-full animate-pulse"></div>
				</div>
			</div>
		{:else}
			<div class="flex-1 overflow-y-auto">
				{#if loading}
					<div class="p-6 text-center">
						<Loader class="w-8 h-8 animate-spin text-cyan-400 mx-auto mb-4" />
						<p class="text-slate-300 text-md">Loading files...</p>
					</div>
				{:else if files.length === 0}
					<div class="p-6 text-center">
						<FileText class="w-16 h-16 text-slate-600 mx-auto mb-4" />
						<p class="text-slate-300 font-semibold text-lg">No Documents</p>
						<p class="text-slate-500 text-sm mt-1">Upload files or folders to get started.</p>
					</div>
				{:else}
					<div class="divide-y divide-slate-800">
						{#each files as file}
							{@const IconComponent = getFileIcon(file)}
							<div class="p-2.5 hover:bg-slate-700/50 transition-all duration-200 group">
								<div class="grid grid-cols-12 items-center gap-4">
									<div class="col-span-6 flex items-center space-x-3">
										<IconComponent class="w-5 h-5 flex-shrink-0 {file.is_symlink ? 'text-purple-400' : file.type === 'directory' ? 'text-blue-400' : 'text-cyan-400'}" />
										<div class="min-w-0 flex-1">
											<span class="text-slate-200 text-base font-medium block truncate {file.is_symlink ? 'italic' : ''}">{file.name}</span>
											{#if file.is_symlink && file.target}
												<div class="text-xs text-slate-500 truncate mt-1">→ {file.target}</div>
											{/if}
										</div>
									</div>

									<div class="col-span-2 text-sm text-slate-400 flex items-center space-x-2">
										<HardDrive class="w-4 h-4" />
										<span>{file.size != null ? formatBytes(file.size) : 'N/A'}</span>
										{#if (file.type === 'directory' || (file.is_symlink && file.resolved_target_type === 'directory')) && file.file_count != null}
											<span class="ml-2 px-2 py-0.5 rounded-full bg-slate-700 text-xs text-slate-300">{file.file_count} files</span>
										{/if}
									</div>

									<div class="col-span-3 text-sm text-slate-400 flex items-center space-x-2">
										<Clock class="w-4 h-4" />
										<span>{file.last_modified ? formatDate(file.last_modified) : 'N/A'}</span>
									</div>

									<div class="col-span-1 flex justify-end">
										<Button
											onclick={() => onDeleteFile(file.name)}
											class="p-2 text-slate-500 hover:text-red-400 cursor-pointer opacity-0 group-hover:opacity-100 transition-all duration-200"
											size="icon"
											variant="danger"
											title="Delete {file.type}"
										>
											<Trash2 class="w-4 h-4" />
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
	onSymlinkCreated={handleSymlinkCreated}
	bind:open={showSymlinkModal}
/>
