<script lang="ts">
	import { ChevronDown, FileText } from '@lucide/svelte';
	import type { RagDocument } from '$lib/types.d.ts';

	interface Props {
		documents: RagDocument[];
	}

	let { documents }: Props = $props();

	let isOpen = $state(false);
	let openFiles: boolean[] = $state([]);

	function isUrl(str: string) {
		try {
			const url = new URL(str);
			return url.protocol !== 'file:';
		} catch {
			return false;
		}
	}

	function isFilePath(str: string) {
		try {
			const url = new URL(str);
			return url.protocol === 'file:';
		} catch {
			return false;
		}
	}

	function getFileName(str: string) {
		try {
			const url = new URL(str);
			return url.pathname.split('/').pop();
		} catch {
			return str.split('/').pop();
		}
	}

	function getPreview(content: string, maxLength = 200) {
		if (!content) return '';
		return content.length > maxLength ? content.slice(0, maxLength) + '…' : content;
	}

	function toggle() {
		isOpen = !isOpen;
	}

	function toggleFile(idx: number) {
		openFiles = openFiles.map((open, i) => (i === idx ? !open : open));
	}

	$effect(() => {
		if (documents) {
			if (openFiles.length !== documents.length) {
				openFiles = documents.map(() => false);
			}
		}
	});
</script>

{#if documents && documents.length > 0}
	<div class="space-y-3">
		<!-- Header with toggle -->
		<button
			type="button"
			class="flex items-center gap-2 w-full text-left focus:outline-none group text-[0.7rem] cursor-pointer"
			onclick={toggle}
			aria-expanded={isOpen}
		>
			<FileText class="w-4 h-4 text-green-400 flex-shrink-0" />
			<strong class="text-slate-400">Files used ({documents.length}):</strong>
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
				<ul class="space-y-1.5 mt-1">
					{#each documents as doc, index}
						{#if doc && doc.source !== '' && doc.content !== ''}
							{@const fileName = getFileName(doc.source)}

							<li class="glass bg-slate-900/70 rounded-xl px-2.5 py-1.5 border border-slate-700 shadow-lg flex flex-col">
								<!-- Collapsible header -->
								<button
									type="button"
									class="flex items-center gap-2 w-full text-left focus:outline-none group cursor-pointer"
									onclick={() => toggleFile(index)}
									aria-expanded={openFiles[index]}
								>
									<FileText class="w-4 h-4 text-cyan-400 flex-shrink-0" />
									{#if isUrl(doc.source)}
										<a href={doc.source} target="_blank" rel="noopener" class="font-mono text-cyan-300 hover:underline hover:text-cyan-200 transition-all duration-150">{doc.source}</a>
									{:else if isFilePath(doc.source)}
										<span class="font-mono text-slate-200 text-[0.7rem]" title={doc.source}>{fileName}</span>
									{:else}
										<span class="font-mono text-slate-100 break-all">{doc.source}</span>
									{/if}
									<span class="flex items-center gap-1 w-fit ml-2">
										<span class="text-slate-400 italic text-xs">{getPreview(doc.content)}</span>
										<ChevronDown
											class="w-4 h-4 text-cyan-300 transition-transform duration-200"
											style="transform: rotate({openFiles[index] ? 180 : 0}deg);"
											aria-hidden="true"
										/>
									</span>
								</button>
								<!-- Collapsible content -->
								<div
									class="overflow-hidden transition-all duration-300 space-y-1"
									style="max-height: {openFiles[index] ? '500px' : '0'}; opacity: {openFiles[index] ? 1 : 0};"
									aria-hidden={!openFiles[index]}
									class:pt-1={openFiles[index]}
								>
									{#if isUrl(doc.source)}
										<a href={doc.source} target="_blank" rel="noopener" class="font-mono text-cyan-300 hover:underline hover:text-cyan-200 transition-all duration-150">{doc.source}</a>
									{:else if isFilePath(doc.source)}
										<span class="font-mono text-slate-200 text-[0.7rem] break-all">{doc.source}</span>
									{:else}
										<span class="font-mono text-slate-100 break-all">{doc.source}</span>
									{/if}
									<pre class="text-slate-300 text-[0.65rem] bg-slate-900/60 rounded-lg p-2 border border-slate-700 whitespace-pre-wrap">
{doc.content.slice(0, 5000).trim()}{doc.content.length > 5000 ? '…' : ''}
									</pre>
								</div>
							</li>
						{/if}
					{/each}
				</ul>
			{/if}
		</div>
	</div>
{/if}
