<script lang="ts">
	import { Wrench, Globe, FileText, FileIcon, FolderOpen } from '@lucide/svelte';
	import type { ToolActivity } from '$lib/types.d.ts';

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

	$inspect(activity);
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
		<div class="flex-1">Web search completed</div>
	{:else if activity.type === 'documents'}
		<FileText class="w-3 h-3 text-green-400 flex-shrink-0" />
		<div class="flex-1">Document search completed</div>
	{:else if activity.type === 'read_file'}
		<FileIcon class="w-3 h-3 text-purple-400 flex-shrink-0" />
		<div class="flex-1">File read</div>
	{:else if activity.type === 'list_files'}
		<FolderOpen class="w-3 h-3 text-orange-400 flex-shrink-0" />
		<div class="flex-1">Directory listing</div>
	{/if}
</div>

<style></style>
