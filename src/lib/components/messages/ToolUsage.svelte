<script lang="ts">
	import { Wrench, Globe, FileText, FileIcon, FolderOpen } from '@lucide/svelte';
	import type { ToolActivity } from '$lib/types.d.ts';
	import { WebUrlChips, DocNamesInline, FileNamesInline } from '$lib/components/snippets.svelte';

	interface Props {
		activity: ToolActivity;
	}
	
	let { activity }: Props = $props();

	// live elapsed timer
	let now = $state(new Date());
	let interval: number | null = null;
	$effect(() => {
		if (activity.type === 'tool_call' && activity.status !== 'completed') {
			interval = window.setInterval(() => { now = new Date() }, 100);
			return () => { if (interval) { window.clearInterval(interval); interval = null } };
		}
	});

	function fmt(ms?: number): string {
		if (!ms || ms < 0) return '0.0s';
		const s = Math.round(ms / 100) / 10;
		return `${s.toFixed(1)}s`;
	}
</script>

<div class="flex items-center space-x-2 text-xs text-slate-400 bg-slate-900/30 rounded-lg px-2 py-1.5 border border-slate-700/50 my-1.5">
	{#if activity.type === 'tool_call'}
		<Wrench class="w-3 h-3 text-yellow-400 flex-shrink-0" />
		<div class="flex-1">
			<div class="text-slate-300">
				Running tool: <span class="text-yellow-300 font-mono">{activity.toolName || 'tool'}</span>
			</div>
			{#if activity.params && Object.keys(activity.params).length > 0}
				<div class="text-slate-500 text-[0.65rem]">
					with {Object.keys(activity.params).slice(0,3).join(', ')}{Object.keys(activity.params).length > 3 ? `, +${Object.keys(activity.params).length - 3} more` : ''}
				</div>
			{/if}
		</div>
		<div class="inline-flex items-center gap-1 text-slate-500">
			<span>{fmt(((activity.status === 'completed' ? activity.endedAt ?? now : now).getTime()) - ((activity.startedAt ?? activity.timestamp).getTime()))}</span>
		</div>
	{:else if activity.type === 'sources'}
		<Globe class="w-3 h-3 text-blue-400 flex-shrink-0" />
		<div class="flex-1">
			<div>Web search completed</div>
			{#if 'urls' in activity.data}
				{@const urls = activity.data.urls}
				{#if urls.length > 0}
					<div class="mt-1 text-[0.7rem]">
						{@render WebUrlChips(urls)}
					</div>
				{/if}
			{/if}
		</div>
	{:else if activity.type === 'documents'}
		<FileText class="w-3 h-3 text-green-400 flex-shrink-0" />
		<div class="flex-1">
			<div>Document search completed</div>
			{#if activity.data && Array.isArray(activity.data)}
				<div class="mt-1">
					{@render DocNamesInline(activity.data, 5)}
				</div>
			{/if}
		</div>
	{:else if activity.type === 'read_file'}
		<FileIcon class="w-3 h-3 text-purple-400 flex-shrink-0" />
		<div class="flex-1">File read</div>
	{:else if activity.type === 'list_files'}
		<FolderOpen class="w-3 h-3 text-orange-400 flex-shrink-0" />
		<div class="flex-1">
			<div>Directory listing</div>
			{#if activity.data && typeof activity.data === 'object' && 'files' in activity.data}
				<div class="mt-1">
					{@render FileNamesInline(activity.data, 6)}
				</div>
			{/if}
		</div>
	{/if}
</div>

