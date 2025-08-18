<script lang="ts">
    import Button from '$lib/components/common/Button.svelte';
    import MessageStats from '$lib/components/common/MessageStats.svelte';
	import Markdown from '$lib/components/common/Markdown.svelte';
	import TextArea from '$lib/components/common/TextArea.svelte';
    import DocumentSources from '$lib/components/messages/DocumentSources.svelte';
	import FilesSources from '$lib/components/messages/FilesSources.svelte';
	import WebSources from '$lib/components/messages/WebSources.svelte';
	import ToolActivityRow from '$lib/components/messages/ToolActivityRow.svelte';
    import type {ChatMessage as ChatMessageType} from '$lib/types.d.ts';
	import {Bot, Copy, Loader, Pencil, RefreshCcw, SendHorizontal, Trash2, User, X} from '@lucide/svelte';
	import { countTokensFromText } from '$lib/helpers/tokenizer';

	interface Props {
		isLastMessage?: boolean;
		isStreaming?: boolean;
		message: ChatMessageType;
		onDelete?: (id: string) => void;
		onEdit?: (id: string, newContent: string) => void;
		onRegenerate?: (id: string) => void;
	}

	let { message, isStreaming = false, isLastMessage = false, onDelete, onEdit, onRegenerate }: Props = $props();

    let isEditing = $state(false);
	let editedContent = $state(message.content);
	let displayParagraph: HTMLParagraphElement | undefined = $state(undefined);
	let assistantContentEl: HTMLDivElement | undefined = $state(undefined);

	console.log($state.snapshot(message));

	function copyToClipboard() {
		navigator.clipboard.writeText(message.content);
	}

	function startEditing() {
		isEditing = true;
		editedContent = message.content;
	}

	function cancelEditing() {
		isEditing = false;
		editedContent = message.content;
	}

	function saveEdit() {
		if (editedContent.trim() && editedContent !== message.content) {
			onEdit?.(message.id, editedContent.trim());
		}
		isEditing = false;
	}

	function formatTimeShort(date: Date) {
		return date.toLocaleTimeString('en-US', {
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function formatTimeLong(date: Date) {
		return date.toLocaleTimeString('en-US', {
			hour: '2-digit',
			minute: '2-digit',
			second: '2-digit',
			hourCycle: 'h24',
			timeZoneName: 'shortOffset'
		});
	}
</script>

<div class="group flex items-start space-x-3 {message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}">
	<div class="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center {message.role === 'user' ? 'bg-cyan-500' : 'bg-slate-600'}">
		{#if message.role === 'user'}
			<User class="w-4 h-4 text-white" />
		{:else}
			<Bot class="w-4 h-4 text-white" />
		{/if}
	</div>
	<div class="flex-1 w-0">
		<div class="flex items-center gap-2 mb-1.5 {message.role === 'user' ? 'flex-row-reverse' : ''}">
			<span class="text-xs font-medium text-slate-300">
				{message.role === 'user' ? 'You' : 'Assistant'}
			</span>
			<span class="text-xs text-slate-500" title={formatTimeLong(message.timestamp)}>
				{formatTimeShort(message.timestamp)}
			</span>

			<!-- Stats -->
			<div class="flex items-center gap-1 text-xs text-slate-500">
				<MessageStats text={message.content} targetElement={message.role === 'user' ? displayParagraph : assistantContentEl} hideWhenEmpty={false} />
				{#if message.role === 'assistant'}
					{@const timeToFirstToken = Math.round((message.ttftMs ?? 0) / 100) / 10}
					{@const responseTime = Math.round(((message.responseMs ?? 0) - (message.ttftMs ?? 0)) / 100) / 10}
					{@const tokensPerSecond = Math.round((countTokensFromText(message.content) / responseTime) * 10) / 10}
					{#if message.ttftMs !== undefined}
						<span title="Time to first token">• {timeToFirstToken}s</span>
					{/if}
					{#if message.responseMs !== undefined}
						<span title="Response time ({tokensPerSecond} tokens/s)">, {responseTime}s</span>
					{/if}
				{/if}
			</div>

			<div class="flex items-center lg:opacity-0 group-hover:opacity-100 transition-opacity duration-200">
				{#if message.role === 'user' && !isEditing}
					<Button title="Edit" onclick={startEditing} size="icon" variant="secondary">
						<Pencil size={14} />
					</Button>
				{/if}
				<Button title="Copy" onclick={copyToClipboard} size="icon" variant="secondary">
					<Copy size={14} />
				</Button>
				{#if message.role === 'assistant' && onRegenerate}
					<Button title="Regenerate" onclick={() => onRegenerate?.(message.id)} size="icon" variant="secondary">
						<RefreshCcw size={14} />
					</Button>
				{/if}
				{#if onDelete}
					<Button title="Delete" onclick={() => onDelete?.(message.id)} size="icon" variant="secondary">
						<Trash2 size={14} />
					</Button>
				{/if}
			</div>
		</div>
		<div class="flex items-start {message.role === 'user' ? 'flex-row-reverse' : ''} gap-2">
			<div class="p-2.5 rounded-xl {message.role === 'user'
					? 'bg-gradient-to-r from-cyan-700 to-cyan-800 text-white'
					: 'bg-slate-800/50 border border-slate-600'
				} flex-1 min-w-0 break-words {message.isError ? '!bg-red-900/20 !border-red-700/60' : ''}"
				bind:this={assistantContentEl}
			>
				{#if message.role === 'user' && isEditing}
					<!-- Edit mode for user messages -->
					<div class="space-y-3">
						<TextArea
							bind:value={editedContent}
							placeholder="Edit your message..."
							class="w-full min-h-[80px] bg-white/10 border-white/20 text-white placeholder-white/60"
							onkeydown={(e) => {
								if (e.key === 'Enter' && e.ctrlKey) {
									saveEdit();
								} else if (e.key === 'Escape') {
									cancelEditing();
								}
							}}
						/>
						<div class="flex items-center justify-end space-x-2">
							<Button onclick={cancelEditing} size="default" variant="secondary">
								<X size={14} />
								Cancel
							</Button>
							<Button onclick={saveEdit} size="default" variant="primary">
								<SendHorizontal size={14} />
								Send
							</Button>
						</div>
					</div>
                {:else if message.role === 'user'}
					<!-- Display mode for user messages -->
                    <p class="whitespace-pre-wrap break-words text-sm" bind:this={displayParagraph}>{message.content}</p>
				{:else}
					{@const hasUrls = message.sources?.some(source => source.urls.length > 0)}
					{@const hasDocuments = message.documents && message.documents.length > 0}
					{@const hasFileLists = message.fileLists && message.fileLists.length > 0}

					<!-- Content with inline tool activities -->
					{#if message.contentParts && message.contentParts.length > 0}
						<div class="space-y-1.5">
							{#each message.contentParts as part, index (index)}
								{#if part.type === 'text' && part.content.trim()}
									<Markdown content={part.content} />
								{:else if part.type === 'tool' && part.activity}
									<ToolActivityRow activity={part.activity} />
								{/if}
							{/each}
						</div>
					{:else if message.content.length > 0}
						<!-- Fallback to regular content display -->
						<Markdown content={message.content} />
					{:else if message.isError}
						<!-- Explicit empty content placeholder -->
						<div class="text-xs text-red-300 rounded-md px-2 py-1">
							No answer was generated.
						</div>
					{/if}

					{#if isStreaming && isLastMessage}
						<div class="flex items-center space-x-2" class:mt-2={message.content.length}>
							<Loader class="w-3 h-3 animate-spin text-cyan-400" />
							<span class="text-xs text-slate-400 animate-pulse">Assistant is thinking...</span>
						</div>
					{/if}

					{#if hasUrls || hasDocuments || hasFileLists}
						<div class="mt-3 pt-2 border-t border-slate-700 text-[0.65rem] space-y-2">
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
