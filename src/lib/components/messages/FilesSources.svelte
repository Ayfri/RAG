<script lang="ts">
	import type {FileListResult} from '$lib/types.d.ts';
	import {ChevronDown, FileIcon, FolderOpen} from '@lucide/svelte';

	interface Props {
		fileLists: FileListResult[];
	}

	let { fileLists }: Props = $props();

	let isOpen = $state(false);

	function toggle() {
		isOpen = !isOpen;
	}

	function getFileType(fileName: string): 'file' | 'folder' {
		return fileName.includes('(folder,') ? 'folder' : 'file';
	}

	function getFileName(fileName: string): string {
		// Extract just the file name without size info
		return fileName.split(' (')[0];
	}

	function getFileSize(fileName: string): string {
		// Extract size info
		const match = fileName.match(/\((file|folder), (.+?)\)/);
		return match ? match[2] : '';
	}

	let successfulFileLists = $derived(fileLists.filter(list => list.success && list.files.length > 0));
	let totalFiles = $derived(successfulFileLists.reduce((count, list) => count + list.files.length, 0));
</script>

{#if successfulFileLists.length > 0}
	<div class="space-y-3">
		<!-- Header with toggle -->
		<button
			type="button"
			class="flex items-center gap-2 w-full text-left focus:outline-none group text-[0.7rem] cursor-pointer"
			onclick={toggle}
			aria-expanded={isOpen}
		>
			<FolderOpen class="w-4 h-4 text-orange-400 flex-shrink-0" />
			<strong class="text-slate-400">File listings ({totalFiles} files):</strong>
			<ChevronDown
				class="w-4 h-4 text-slate-300 transition-transform duration-200"
				style="transform: rotate({isOpen ? 180 : 0}deg);"
				aria-hidden="true"
			/>
		</button>

		<!-- Collapsible content -->
		<div
			class="overflow-hidden transition-all duration-300"
			style="max-height: {isOpen ? '500px' : '0'}; opacity: {isOpen ? 1 : 0};"
			aria-hidden={!isOpen}
		>
			{#if isOpen}
				<div class="space-y-4">
					{#each successfulFileLists as fileList}
						<div class="space-y-2">
							<div class="text-orange-300 font-mono text-xs font-medium">
								📂 {fileList.directory_path}/ ({fileList.files.length} items)
							</div>
							<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-1 ml-4">
								{#each fileList.files.slice(0, 20) as file}
									{@const fileType = getFileType(file)}
									{@const fileName = getFileName(file)}
									{@const fileSize = getFileSize(file)}
									<div class="flex items-center gap-1.5 text-xs">
										{#if fileType === 'folder'}
											<FolderOpen class="w-3 h-3 text-orange-400 flex-shrink-0" />
											<span class="text-orange-200 font-mono truncate" title={fileName}>
												{fileName}
											</span>
										{:else}
											<FileIcon class="w-3 h-3 text-purple-400 flex-shrink-0" />
											<span class="text-purple-200 font-mono truncate" title={fileName}>
												{fileName}
											</span>
										{/if}
										{#if fileSize}
											<span class="text-slate-500 text-xs">({fileSize})</span>
										{/if}
									</div>
								{/each}
								{#if fileList.files.length > 20}
									<div class="text-slate-500 text-xs col-span-full">
										... and {fileList.files.length - 20} more files
									</div>
								{/if}
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</div>
	</div>
{/if}
