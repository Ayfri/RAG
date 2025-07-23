<script lang="ts">
	import { User, Bot, Loader } from '@lucide/svelte';
	import Markdown from '$lib/components/common/Markdown.svelte';

	interface ChatMessage {
		id: string;
		role: 'user' | 'assistant';
		content: string;
		timestamp: Date;
	}

	interface Props {
		message: ChatMessage;
		isStreaming?: boolean;
		isLastMessage?: boolean;
	}

	let { message, isStreaming = false, isLastMessage = false }: Props = $props();

	function formatTime(date: Date) {
		return date.toLocaleTimeString('en-US', {
			hour: '2-digit',
			minute: '2-digit'
		});
	}
</script>

<div class="flex items-start space-x-4 {message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}">
	<div class="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center {message.role === 'user' ? 'bg-cyan-500' : 'bg-slate-600'}">
		{#if message.role === 'user'}
			<User class="w-5 h-5 text-white" />
		{:else}
			<Bot class="w-5 h-5 text-white" />
		{/if}
	</div>
	<div class="flex-1 max-w-3xl">
		<div class="flex items-center space-x-2 mb-2 {message.role === 'user' ? 'justify-end' : ''}">
			<span class="text-sm font-medium text-slate-300">
				{message.role === 'user' ? 'You' : 'Assistant'}
			</span>
			<span class="text-xs text-slate-500">
				{formatTime(message.timestamp)}
			</span>
		</div>
		<div class="p-4 rounded-2xl {message.role === 'user'
			? 'bg-gradient-to-r from-cyan-500 to-cyan-600 text-white'
			: 'bg-slate-800/50 border border-slate-600'
		}">
			{#if message.role === 'user'}
				<p class="whitespace-pre-wrap">{message.content}</p>
			{:else}
				<Markdown content={message.content} />
				{#if isStreaming && isLastMessage}
					<div class="flex items-center space-x-2 mt-3 pt-3 border-t border-slate-600">
						<Loader class="w-4 h-4 animate-spin text-cyan-400" />
						<span class="text-xs text-slate-400">Assistant is typing...</span>
					</div>
				{/if}
			{/if}
		</div>
	</div>
</div>
