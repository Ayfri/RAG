<script lang="ts">
	import { Bot, Copy, Loader, RefreshCcw, Trash2, User, FileText, ChevronDown } from '@lucide/svelte';
	import Markdown from '$lib/components/common/Markdown.svelte';
	import type { SearchResult, SearchResultUrl, RagDocument } from '$lib/types.d.ts';

	interface Message {
		content: string;
		documents?: RagDocument[];
		id: string;
		role: 'user' | 'assistant';
		sources?: SearchResult[];
		timestamp: Date;
	}

	interface Props {
		isLastMessage?: boolean;
		isStreaming?: boolean;
		message: Message;
		onDelete?: (id: string) => void;
		onRegenerate?: (id: string) => void;
	}

	let { message, isStreaming = false, isLastMessage = false, onDelete, onRegenerate }: Props = $props();

	function copyToClipboard() {
		navigator.clipboard.writeText(message.content);
	}

	function formatTime(date: Date) {
		return date.toLocaleTimeString('en-US', {
			hour: '2-digit',
			minute: '2-digit'
		});
	}

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
	// Track open/closed state for each file preview
	let openFiles: boolean[] = $state([]);

	$effect(() => {
		if (message.documents) {
			if (openFiles.length !== message.documents.length) {
				openFiles = message.documents.map(() => false);
			}
		}
	});

	function toggleFile(idx: number) {
		openFiles = openFiles.map((open, i) => (i === idx ? !open : open));
	}
</script>

<div class="group flex items-start space-x-4 {message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}">
	<div class="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center {message.role === 'user' ? 'bg-cyan-500' : 'bg-slate-600'}">
		{#if message.role === 'user'}
			<User class="w-5 h-5 text-white" />
		{:else}
			<Bot class="w-5 h-5 text-white" />
		{/if}
	</div>
	<div class="flex-1 w-0">
		<div class="flex items-center gap-2 mb-2 {message.role === 'user' ? 'justify-end' : ''}">
			<span class="text-sm font-medium text-slate-300">
				{message.role === 'user' ? 'You' : 'Assistant'}
			</span>
			<span class="text-xs text-slate-500">
				{formatTime(message.timestamp)}
			</span>

			<div class="flex items-center opacity-0 group-hover:opacity-100 transition-opacity duration-200">
				<button title="Copy" onclick={copyToClipboard} class="p-1 rounded-md hover:bg-slate-700 cursor-pointer">
					<Copy class="w-4 h-4 text-slate-400" />
				</button>
				{#if message.role === 'assistant' && onRegenerate}
					<button title="Regenerate" onclick={() => onRegenerate?.(message.id)} class="p-1 rounded-md hover:bg-slate-700 cursor-pointer">
						<RefreshCcw class="w-4 h-4 text-slate-400" />
					</button>
				{/if}
				{#if onDelete}
					<button title="Delete" onclick={() => onDelete?.(message.id)} class="p-1 rounded-md hover:bg-slate-700 cursor-pointer">
						<Trash2 class="w-4 h-4 text-slate-400" />
					</button>
				{/if}
			</div>
		</div>
		<div class="flex items-start {message.role === 'user' ? 'flex-row-reverse' : ''} gap-2">
			<div class="p-4 rounded-2xl {message.role === 'user'
				? 'bg-gradient-to-r from-cyan-500 to-cyan-600 text-white'
				: 'bg-slate-800/50 border border-slate-600'
			} flex-1 min-w-0 break-words">
				{#if message.role === 'user'}
					<p class="whitespace-pre-wrap break-words">{message.content}</p>
				{:else}
					{@const hasUrls = message.sources?.some((source) => source.urls.length > 0)}
					{@const hasDocuments = message.documents && message.documents.length > 0}

					{#if message.content.length > 0}
						<Markdown content={message.content} />
					{/if}

					{#if isStreaming && isLastMessage}
						<div class="flex items-center space-x-2">
							<Loader class="w-4 h-4 animate-spin text-cyan-400" />
							<span class="text-xs text-slate-400">Assistant is typing...</span>
						</div>
					{/if}

					{#if hasUrls || hasDocuments}
						<div class="mt-4 pt-3 border-t border-slate-700 text-[0.7rem]">
							{#if message.sources && message.sources.length > 0}
								<div class="space-y-3 mb-2">
									{#each message.sources.filter((source) => source.urls.length > 0) as source}
										<div class="mb-2">
											{#if source.urls && source.urls.length > 0}
												<div class="flex flex-wrap gap-1 items-center mt-1">
													{#each source.urls.toSorted((a: SearchResultUrl, b: SearchResultUrl) => a.title.localeCompare(b.title)) as url}
														{#if isUrl(url.url)}
															<a href={url.url} target="_blank" rel="noopener" class="inline-block bg-cyan-900/60 text-cyan-200 px-2 py-0.5 rounded-full font-mono hover:bg-cyan-800/80 hover:underline transition-all duration-150 shadow-sm border border-cyan-700">
																{url.title}
															</a>
														{:else}
															<span class="inline-block bg-slate-700/80 text-slate-100 px-3 py-1 rounded-full font-mono border border-slate-600 shadow-sm">{url.url}</span>
														{/if}
													{/each}
												</div>
											{/if}
										</div>
									{/each}
								</div>
							{/if}
							{#if message.documents && message.documents.length > 0}
								<div class="space-y-3">
									<strong class="text-slate-400">Files used ({message.documents.length}):</strong>
									<ul class="space-y-1.5 mt-1">
										{#each message.documents as doc, index}
											{#if doc && doc.source !== '' && doc.content !== ''}
												{@const fileName = getFileName(doc.source)}

												<li class="glass bg-slate-900/70 rounded-xl px-2.5 py-1.5 border border-slate-700 shadow-lg flex flex-col">
													<!-- Collapsible header -->
													<button
														type="button"
														class="flex items-center gap-2 w-full text-left focus:outline-none group"
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
								</div>
							{/if}
						</div>
					{/if}
				{/if}
			</div>
		</div>
	</div>
</div>
