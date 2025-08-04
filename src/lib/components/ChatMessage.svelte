<script lang="ts">
	import { Bot, Copy, Loader, RefreshCcw, Trash2, User, FileText, Globe, FolderOpen, FileIcon } from '@lucide/svelte';
	import Markdown from '$lib/components/common/Markdown.svelte';
	import WebSources from '$lib/components/WebSources.svelte';
	import DocumentSources from '$lib/components/DocumentSources.svelte';
	import FilesSources from '$lib/components/FilesSources.svelte';
	import type { SearchResult, SearchResultUrl, RagDocument, ToolActivity, FileReadResult, FileListResult } from '$lib/types.d.ts';

	interface Message {
		content: string;
		documents?: RagDocument[];
		fileLists?: FileListResult[];
		id: string;
		role: 'user' | 'assistant';
		sources?: SearchResult[];
		timestamp: Date;
		toolActivities?: ToolActivity[];
		contentParts?: Array<{type: 'text' | 'tool'; content: string; activity?: ToolActivity}>;
	}

	interface Props {
		isLastMessage?: boolean;
		isStreaming?: boolean;
		message: Message;
		onDelete?: (id: string) => void;
		onRegenerate?: (id: string) => void;
	}

	let { message, isStreaming = false, isLastMessage = false, onDelete, onRegenerate }: Props = $props();

	console.log($state.snapshot(message));

	function copyToClipboard() {
		navigator.clipboard.writeText(message.content);
	}

	function formatTime(date: Date) {
		return date.toLocaleTimeString('en-US', {
			hour: '2-digit',
			minute: '2-digit'
		});
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
					{@const hasFileLists = message.fileLists && message.fileLists.length > 0}

					<!-- Content with inline tool activities -->
					{#if message.contentParts && message.contentParts.length > 0}
						<div class="space-y-2">
							{#each message.contentParts as part, index (index)}
								{#if part.type === 'text' && part.content.trim()}
									<Markdown content={part.content} />
								{:else if part.type === 'tool' && part.activity}
									{@const activity = part.activity}
									<div class="flex items-center space-x-2 text-xs text-slate-400 bg-slate-900/30 rounded-lg px-3 py-2 border border-slate-700/50 my-2">
										{#if activity.type === 'sources'}
											{@const data = activity.data as SearchResult}
											<Globe class="w-4 h-4 text-blue-400 flex-shrink-0" />
											<div class="flex-1">
												<div class="text-slate-300 mb-2">
													Web search completed - found {data.urls?.length || 0} sources
												</div>
												{#if data.urls && data.urls.length > 0}
													<div class="flex flex-wrap gap-1 items-center">
														{#each data.urls as url}
															<a href={url.url} target="_blank" rel="noopener" class="inline-block bg-blue-900/60 text-blue-200 px-2 py-0.5 rounded-full text-xs hover:bg-blue-800/80 hover:underline transition-all duration-150 shadow-sm border border-blue-700">
																{url.title}
															</a>
														{/each}
													</div>
												{/if}
											</div>
										{:else if activity.type === 'documents'}
											{@const data = activity.data as RagDocument[]}
											<FileText class="w-4 h-4 text-green-400 flex-shrink-0" />
											<span class="flex-1">
												Document search completed - found {data.length} documents
												{#if data.length > 0}
													<span class="ml-2 text-slate-500">
														({data.map(d => d.source.split('/').pop()).slice(0, 3).join(', ')}{data.length > 3 ? `, +${data.length - 3} more` : ''})
													</span>
												{/if}
											</span>
										{:else if activity.type === 'read_file'}
											{@const data = activity.data as FileReadResult}
											<FileIcon class="w-4 h-4 text-purple-400 flex-shrink-0" />
											<div class="flex-1">
												{#if data.success}
													<div class="text-slate-300 mb-1">
														File read: <span class="text-purple-300 font-mono">{data.file_path}</span>
													</div>
													<div class="text-slate-500 text-xs">
														Content length: {data.content.length} characters
													</div>
												{:else}
													<div class="text-red-300 mb-1">
														Failed to read: <span class="text-red-200 font-mono">{data.file_path}</span>
													</div>
													<div class="text-red-400 text-xs">
														{data.error}
													</div>
												{/if}
											</div>
										{:else if activity.type === 'list_files'}
											{@const data = activity.data as FileListResult}
											<FolderOpen class="w-4 h-4 text-orange-400 flex-shrink-0" />
											<div class="flex-1">
												{#if data.success}
													<div class="text-slate-300 mb-1">
														Directory listing: <span class="text-orange-300 font-mono">{data.directory_path}</span>
													</div>
													<div class="text-slate-500 text-xs">
														Found {data.files.length} items
														{#if data.files.length > 0}
															<span class="ml-2">
																({data.files.slice(0, 3).map(f => f.split(' ')[0]).join(', ')}{data.files.length > 3 ? `, +${data.files.length - 3} more` : ''})
															</span>
														{/if}
													</div>
												{:else}
													<div class="text-red-300 mb-1">
														Failed to list: <span class="text-red-200 font-mono">{data.directory_path}</span>
													</div>
													<div class="text-red-400 text-xs">
														{data.error}
													</div>
												{/if}
											</div>
										{/if}
										<span class="text-slate-500 text-xs">
											{activity.timestamp.toLocaleTimeString('en-US', {
												hour: '2-digit',
												minute: '2-digit',
												second: '2-digit'
											})}
										</span>
									</div>
								{/if}
							{/each}
						</div>
					{:else if message.content.length > 0}
						<!-- Fallback to regular content display -->
						<Markdown content={message.content} />
					{/if}

					{#if isStreaming && isLastMessage}
						<div class="flex items-center space-x-2" class:mt-3={message.content.length}>
							<Loader class="w-4 h-4 animate-spin text-cyan-400" />
							<span class="text-xs text-slate-400">Assistant is thinking...</span>
						</div>
					{/if}

					{#if hasUrls || hasDocuments || hasFileLists}
						<div class="mt-4 pt-3 border-t border-slate-700 text-[0.7rem] space-y-3">
							<WebSources sources={message.sources || []} />
							<DocumentSources documents={message.documents || []} />
							<FilesSources fileLists={message.fileLists || []} />
						</div>
					{/if}
				{/if}
			</div>
		</div>
	</div>
</div>
