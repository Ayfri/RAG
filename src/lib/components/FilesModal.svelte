<script lang="ts">
	import { FileText, Trash2, Upload, RefreshCw, Link, FolderOpen, Loader } from '@lucide/svelte';
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
			return item.is_symlink ? FolderOpen : FolderOpen;
		} else {
			return item.is_symlink ? Link : FileText;
		}
	}

	function handleSymlinkCreated() {
		onSymlinkCreated();
	}
</script>

<Modal title="Files" bind:open>
	<div class="flex flex-col h-full -m-4">
		<div class="p-4 border-b border-slate-600">
			<div class="grid grid-cols-2 gap-2">
				<Button
					onclick={onReindex}
					disabled={reindexing}
					class="flex items-center justify-center space-x-1 px-2 py-2 bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white rounded-lg cursor-pointer text-xs font-medium transition-all duration-200"
					title="Manually reindex RAG"
				>
					{#if reindexing}
						<Loader class="w-3 h-3 animate-spin" />
						<span>Reindexing...</span>
					{:else}
						<RefreshCw class="w-3 h-3" />
						<span>Reindex</span>
					{/if}
				</Button>

				<Button
					onclick={() => showSymlinkModal = true}
					class="flex items-center justify-center space-x-1 px-2 py-2 bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 text-white rounded-lg cursor-pointer text-xs font-medium transition-all duration-200"
					title="Create symbolic link"
				>
					<Link class="w-3 h-3" />
					<span>Link</span>
				</Button>

				<label class="flex items-center justify-center space-x-1 px-2 py-2 bg-gradient-to-r from-cyan-500 to-cyan-600 hover:from-cyan-600 hover:to-cyan-700 text-white rounded-lg cursor-pointer text-xs font-medium transition-all duration-200">
					{#if uploading}
						<Loader class="w-3 h-3 animate-spin" />
						<span>Uploading...</span>
					{:else}
						<Upload class="w-3 h-3" />
						<span>Add File</span>
					{/if}
					<FileInput
						accept='.txt,.pdf,.docx,.md'
						disabled={uploading}
						id='file-input'
						onchange={onUploadFile}
					/>
				</label>

				<label class="flex items-center justify-center space-x-1 px-2 py-2 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white rounded-lg cursor-pointer text-xs font-medium transition-all duration-200">
					{#if uploading}
						<Loader class="w-3 h-3 animate-spin" />
						<span>Uploading...</span>
					{:else}
						<FolderOpen class="w-3 h-3" />
						<span>Add Folder</span>
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

		<div class="flex-1 overflow-y-auto">
			{#if loading}
				<div class="p-6 text-center">
					<Loader class="w-6 h-6 animate-spin text-cyan-400 mx-auto mb-2" />
					<p class="text-slate-400 text-sm">Loading files...</p>
				</div>
			{:else if files.length === 0}
				<div class="p-6 text-center">
					<FileText class="w-12 h-12 text-slate-600 mx-auto mb-3" />
					<p class="text-slate-300 font-medium text-sm">No documents</p>
					<p class="text-slate-500 text-xs mt-1">Upload files to get started</p>
				</div>
			{:else}
				<div class="divide-y divide-slate-700">
					{#each files as file}
						{@const IconComponent = getFileIcon(file)}
						<div class="p-3 hover:bg-slate-700/30 transition-all duration-200 group">
							<div class="flex items-start justify-between">
								<div class="flex items-start space-x-2 flex-1 min-w-0">
									<IconComponent class="w-4 h-4 mt-0.5 flex-shrink-0 {file.is_symlink ? 'text-purple-400' : file.type === 'directory' ? 'text-blue-400' : 'text-cyan-400'}" />
									<div class="min-w-0 flex-1">
										<span class="text-slate-200 text-sm block truncate {file.is_symlink ? 'italic' : ''}">{file.name}</span>
										{#if file.is_symlink && file.target}
											<div class="text-xs text-slate-500 truncate">→ {file.target}</div>
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
									onclick={() => onDeleteFile(file.name)}
									class="p-1 text-slate-500 hover:text-red-400 cursor-pointer opacity-0 group-hover:opacity-100 transition-opacity"
									size="icon"
									variant="danger"
									title="Delete {file.type}"
								>
									<Trash2 class="w-3 h-3" />
								</Button>
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</div>
	</div>
</Modal>

<CreateSymlinkModal
	{ragName}
	onSymlinkCreated={handleSymlinkCreated}
	bind:open={showSymlinkModal}
/>
