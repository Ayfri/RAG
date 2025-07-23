<script lang="ts">
	import { onMount } from 'svelte';
	import { Plus, FileText, Search, Database } from '@lucide/svelte';
	import RagList from '$lib/components/RagList.svelte';
	import CreateRagModal from '$lib/components/CreateRagModal.svelte';
	import QueryInterface from '$lib/components/QueryInterface.svelte';

	let rags: string[] = $state([]);
	let selectedRag: string | null = $state(null);
	let showCreateModal = $state(false);
	let loading = $state(true);
	let error = $state('');

	async function loadRags() {
		try {
			loading = true;
			const response = await fetch('/api/rag');
			if (!response.ok) throw new Error('Failed to load RAGs');
			rags = await response.json();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Unknown error';
		} finally {
			loading = false;
		}
	}

	function handleRagCreated(event: CustomEvent<string>) {
		loadRags();
		showCreateModal = false;
	}

	function handleRagDeleted() {
		loadRags();
		selectedRag = null;
	}

	onMount(loadRags);
</script>

<div class="min-h-screen bg-slate-900">
	<!-- Header -->
	<header class="bg-slate-800 border-b border-slate-700 shadow-xl">
		<div class="max-w-7xl mx-auto px-6 lg:px-8">
			<div class="flex justify-between items-center py-6">
				<div class="flex items-center space-x-4">
					<div class="p-2 bg-gradient-to-br from-cyan-500 to-cyan-600 rounded-xl">
						<Database class="w-8 h-8 text-white" />
					</div>
					<div>
						<h1 class="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-cyan-200 bg-clip-text text-transparent">
							RAG Manager
						</h1>
						<p class="text-slate-400 text-sm">Intelligent Document Search & Analysis</p>
					</div>
				</div>
				<button
					onclick={() => showCreateModal = true}
					class="group inline-flex items-center px-6 py-3 bg-gradient-to-r from-cyan-500 to-cyan-600 hover:from-cyan-600 hover:to-cyan-700 text-white rounded-xl font-medium shadow-lg hover:shadow-cyan-500/25 transition-all duration-200 space-x-3 cursor-pointer"
				>
					<Plus class="w-5 h-5 group-hover:rotate-90 transition-transform duration-200" />
					<span>New RAG</span>
				</button>
			</div>
		</div>
	</header>

	<div class="max-w-7xl mx-auto px-6 lg:px-8 py-8">
		{#if error}
			<div class="bg-red-900/50 border border-red-700 rounded-xl p-4 mb-6 backdrop-blur-sm">
				<p class="text-red-200">{error}</p>
			</div>
		{/if}

		<div class="grid grid-cols-1 lg:grid-cols-4 gap-8">
			<!-- RAG List Sidebar -->
			<div class="lg:col-span-1">
				<div class="glass rounded-2xl shadow-2xl overflow-hidden">
					<div class="p-6 border-b border-slate-600 bg-gradient-to-r from-slate-800 to-slate-700">
						<h2 class="text-xl font-semibold text-slate-100 flex items-center space-x-3">
							<FileText class="w-6 h-6 text-cyan-400" />
							<span>Available RAGs</span>
						</h2>
					</div>
					<RagList
						{rags}
						{loading}
						bind:selectedRag
						ondelete={handleRagDeleted}
					/>
				</div>
			</div>

			<!-- Main Content -->
			<div class="lg:col-span-3">
				{#if selectedRag}
					<QueryInterface
						ragName={selectedRag}
					/>
				{:else}
					<div class="glass rounded-2xl shadow-2xl p-16 text-center">
						<div class="mb-8">
							<Search class="w-24 h-24 text-slate-600 mx-auto mb-6" />
							<h3 class="text-2xl font-bold text-slate-200 mb-3">Select a RAG to Query</h3>
							<p class="text-slate-400 text-lg">Choose a RAG from the sidebar to start asking intelligent questions about your documents.</p>
						</div>
						<div class="flex justify-center">
							<div class="w-16 h-1 bg-gradient-to-r from-cyan-500 to-cyan-400 rounded-full"></div>
						</div>
					</div>
				{/if}
			</div>
		</div>
	</div>
</div>

{#if showCreateModal}
	<CreateRagModal
		onclose={() => showCreateModal = false}
		oncreated={handleRagCreated}
	/>
{/if}
