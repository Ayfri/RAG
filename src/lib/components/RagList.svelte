<script lang="ts">
	import { FolderOpen, Loader, Settings, Trash2 } from '@lucide/svelte';
	import Button from '$lib/components/common/Button.svelte';

	interface Props {
		loading: boolean;
		onconfig: (ragName: string) => void;
		ondelete: () => void;
		rags: string[];
		selectedRag: string | null;
	}

	let { rags, loading, selectedRag = $bindable(), onconfig, ondelete }: Props = $props();

	let deletingRag = $state('');

	async function deleteRag(ragName: string) {
		if (!confirm(`Are you sure you want to delete "${ragName}"? This action cannot be undone.`)) {
			return;
		}

		try {
			deletingRag = ragName;
			const response = await fetch(`/api/rag/${ragName}`, { method: 'DELETE' });
			if (!response.ok) throw new Error('Failed to delete RAG');
			ondelete();
		} catch (error) {
			alert('Failed to delete RAG: ' + (error instanceof Error ? error.message : 'Unknown error'));
		} finally {
			deletingRag = '';
		}
	}
</script>

<div class="divide-y divide-slate-600">
	{#if loading}
		<div class="p-8 text-center">
			<Loader class="w-8 h-8 animate-spin text-cyan-400 mx-auto mb-3" />
			<p class="text-slate-400">Loading RAGs...</p>
		</div>
	{:else if rags.length === 0}
		<div class="p-8 text-center">
			<FolderOpen class="w-16 h-16 text-slate-600 mx-auto mb-4" />
			<p class="text-slate-300 mb-2 font-medium">No RAGs available</p>
			<p class="text-slate-500 text-sm">Create your first RAG to get started</p>
		</div>
	{:else}
		{#each rags.toSorted((a, b) => a.localeCompare(b)) as rag}
			<div
				class="p-4 hover:bg-slate-700/50 cursor-pointer transition-all duration-200 group {selectedRag === rag ? 'bg-gradient-to-r from-cyan-900/30 to-cyan-800/20 border-r-2 border-cyan-400' : ''}"
				onclick={() => selectedRag = rag}
			>
				<div class="flex items-center justify-between">
					<div class="flex-1 min-w-0">
						<h3 class="text-slate-100 font-medium truncate group-hover:text-cyan-300 transition-colors">
							{rag}
						</h3>
						<p class="text-slate-500 text-xs mt-1">Click to query this RAG</p>
					</div>
					<div class="flex items-center space-x-2 ml-3">
						<Button
							size="icon"
							variant="default"
							onclick={(e) => {
								e.stopPropagation();
								onconfig(rag);
							}}
							title="Configure RAG"
						>
							<Settings class="w-4 h-4" />
						</Button>
						<Button
							size="icon"
							variant="danger"
							onclick={(e) => {
								e.stopPropagation();
								deleteRag(rag);
							}}
							disabled={deletingRag === rag}
							title="Delete RAG"
						>
							{#if deletingRag === rag}
								<Loader class="w-4 h-4 animate-spin" />
							{:else}
								<Trash2 class="w-4 h-4" />
							{/if}
						</Button>
					</div>
				</div>
			</div>
		{/each}
	{/if}
</div>
