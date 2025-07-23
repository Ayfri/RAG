<script lang="ts">
	import { onMount } from 'svelte';
	import { Plus, FileText, Search, Database } from '@lucide/svelte';
	import RagList from '$lib/components/RagList.svelte';
	import CreateRagModal from '$lib/components/CreateRagModal.svelte';
	import RagConfigModal from '$lib/components/RagConfigModal.svelte';
	import QueryInterface from '$lib/components/QueryInterface.svelte';
	import Button from '$lib/components/common/Button.svelte';

	let rags: string[] = $state([]);
	let selectedRag: string | null = $state(null);
	let showCreateModal = $state(false);
	let showConfigModal = $state(false);
	let configRagName = $state('');
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

	function handleConfigRag(ragName: string) {
		configRagName = ragName;
		showConfigModal = true;
	}

	function handleConfigUpdated() {
		// Configuration updated, no need to reload RAGs as the list doesn't change
		showConfigModal = false;
	}

	onMount(loadRags);
</script>

<div class="min-h-screen bg-slate-900">
	<!-- Header -->
	<header class="bg-slate-800 border-b border-slate-700 shadow-xl">
		<div class="max-w-7xl mx-auto px-4 lg:px-6">
			<div class="flex justify-between items-center py-4">
				<div class="flex items-center space-x-3">
					<div class="p-1.5 bg-gradient-to-br from-cyan-500 to-cyan-600 rounded-xl">
						<Database class="w-7 h-7 text-white" />
					</div>
					<div>
						<h1 class="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-cyan-200 bg-clip-text text-transparent">
							RAG Application
						</h1>
						<p class="text-slate-400 text-xs">Retrieval-Augmented Generation made simple</p>
					</div>
				</div>
				<button
					onclick={() => showCreateModal = true}
					class="group flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-cyan-500 to-cyan-600 hover:from-cyan-600 hover:to-cyan-700 text-white rounded-xl font-medium transition-all duration-200 shadow-lg hover:shadow-cyan-500/25 cursor-pointer"
				>
					<Plus class="w-4 h-4 group-hover:rotate-90 transition-transform duration-200" />
					<span class="text-base">New RAG</span>
				</button>
			</div>
		</div>
	</header>

	<!-- Main Content -->
	<div class="max-w-7xl mx-auto px-4 lg:px-6 py-6">
		{#if error}
			<div class="mb-8 bg-red-900/50 border border-red-700 rounded-xl p-6 flex items-center space-x-4">
				<div class="p-2 bg-red-800 rounded-lg">
					<FileText class="w-6 h-6 text-red-200" />
				</div>
				<div>
					<h3 class="text-red-200 font-medium">Error</h3>
					<p class="text-red-300 text-sm">{error}</p>
				</div>
			</div>
		{/if}

		<div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
			<!-- RAG List Sidebar -->
			<div class="lg:col-span-1">
				<div class="glass rounded-2xl shadow-2xl overflow-hidden">
					<div class="p-4 border-b border-slate-600 bg-gradient-to-r from-slate-800 to-slate-700">
						<h2 class="text-lg font-bold text-slate-100 flex items-center space-x-2">
							<Search class="w-5 h-5 text-cyan-400" />
							<span>Available RAGs</span>
						</h2>
					</div>
					<RagList
						{rags}
						{loading}
						bind:selectedRag
						onconfig={handleConfigRag}
						ondelete={handleRagDeleted}
					/>
				</div>
			</div>

			<!-- Query Interface -->
			<div class="lg:col-span-2">
				{#if selectedRag}
					<QueryInterface ragName={selectedRag} />
				{:else}
					<div class="glass rounded-2xl shadow-2xl p-8 text-center">
						<Database class="w-20 h-20 text-slate-600 mx-auto mb-4" />
						<h3 class="text-xl font-bold text-slate-200 mb-2">Select a RAG to Query</h3>
						<p class="text-slate-400 text-base max-w-md mx-auto leading-relaxed">
							Choose a RAG from the sidebar to start asking questions about your documents.
							Each RAG contains its own set of documents and can be queried independently.
						</p>
						{#if rags.length === 0 && !loading}
							<div class="mt-6">
								<Button
									onclick={() => showCreateModal = true}
									variant="primary"
									class="group"
								>
									<Plus class="w-5 h-5 group-hover:rotate-90 transition-transform duration-200" />
									<span class="text-base">Create Your First RAG</span>
								</Button>
							</div>
						{/if}
					</div>
				{/if}
			</div>
		</div>
	</div>

	<!-- Create RAG Modal -->
	{#if showCreateModal}
		<CreateRagModal
			onclose={() => showCreateModal = false}
			oncreated={handleRagCreated}
		/>
	{/if}

	<!-- Config RAG Modal -->
	{#if showConfigModal && configRagName}
		<RagConfigModal
			ragName={configRagName}
			onclose={() => showConfigModal = false}
			onupdated={handleConfigUpdated}
		/>
	{/if}
</div>
