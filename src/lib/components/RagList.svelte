<script lang="ts">
	import { Trash2, Loader, FolderOpen, AlertCircle, Settings } from '@lucide/svelte';

	interface Props {
		rags: string[];
		loading: boolean;
		selectedRag: string | null;
		onconfig: (ragName: string) => void;
		ondelete: () => void;
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
						<button
							onclick={(e) => {
								e.stopPropagation();
								onconfig(rag);
							}}
							class="p-2 text-slate-500 hover:text-cyan-400 hover:bg-cyan-900/20 rounded-lg transition-all duration-200 cursor-pointer"
							title="Configure RAG"
						>
							<Settings class="w-4 h-4" />
						</button>
						<button
							onclick={(e) => {
								e.stopPropagation();
								deleteRag(rag);
							}}
							disabled={deletingRag === rag}
							class="p-2 text-slate-500 hover:text-red-400 hover:bg-red-900/20 rounded-lg transition-all duration-200 disabled:opacity-50 cursor-pointer"
							title="Delete RAG"
						>
							{#if deletingRag === rag}
								<Loader class="w-4 h-4 animate-spin" />
							{:else}
								<Trash2 class="w-4 h-4" />
							{/if}
						</button>
					</div>
				</div>
			</div>
		{/each}
	{/if}
</div>
