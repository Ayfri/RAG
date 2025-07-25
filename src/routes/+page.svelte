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
	let showRagList = $state(false);

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

<div class="h-screen bg-slate-900 flex flex-col">
	<!-- Header -->
	<header class="bg-slate-800 border-b border-slate-700 shadow-xl flex-shrink-0">
		<div class="px-3 md:px-4 lg:px-6">
			<div class="flex justify-between items-center py-3 md:py-4">
				<div class="flex items-center space-x-2 md:space-x-3 min-w-0 flex-1">
					<div class="p-1 md:p-1.5 bg-gradient-to-br from-cyan-500 to-cyan-600 rounded-lg md:rounded-xl flex-shrink-0">
						<Database class="w-5 h-5 md:w-7 md:h-7 text-white" />
					</div>
					<div class="min-w-0 flex-1">
						<h1 class="text-lg md:text-2xl font-bold bg-gradient-to-r from-cyan-400 to-cyan-200 bg-clip-text text-transparent truncate">
							RAG Application
						</h1>
						<p class="text-slate-400 text-xs hidden sm:block">Retrieval-Augmented Generation made simple</p>
					</div>
				</div>
				<button
					onclick={() => showCreateModal = true}
					class="group flex items-center space-x-1.5 md:space-x-2 px-2.5 md:px-4 py-2 bg-gradient-to-r from-cyan-500 to-cyan-600 hover:from-cyan-600 hover:to-cyan-700 text-white rounded-lg md:rounded-xl font-medium transition-all duration-200 shadow-lg hover:shadow-cyan-500/25 cursor-pointer flex-shrink-0"
				>
					<Plus class="w-4 h-4 group-hover:rotate-90 transition-transform duration-200" />
					<span class="text-sm md:text-base hidden sm:inline">New RAG</span>
					<span class="text-sm md:text-base sm:hidden">New</span>
				</button>
			</div>
		</div>
	</header>

	<!-- Main Content -->
	<main class="px-3 md:px-4 lg:px-6 py-3 md:py-6 w-full flex-1 overflow-hidden flex flex-col">
		{#if error}
			<div class="mb-4 md:mb-8 bg-red-900/50 border border-red-700 rounded-xl p-4 md:p-6 flex items-center space-x-4">
				<div class="p-2 bg-red-800 rounded-lg flex-shrink-0">
					<FileText class="w-5 h-5 md:w-6 md:h-6 text-red-200" />
				</div>
				<div class="min-w-0">
					<h3 class="text-red-200 font-medium text-sm md:text-base">Error</h3>
					<p class="text-red-300 text-xs md:text-sm">{error}</p>
				</div>
			</div>
		{/if}

		<!-- Mobile: Stack layout, Desktop: Grid layout -->
		<div class="flex-1 min-h-0">
			<!-- Mobile Layout -->
			<div class="flex flex-col gap-3 h-full lg:hidden">
				<!-- RAG List (collapsible on mobile) -->
				<div class="glass rounded-xl shadow-2xl overflow-hidden flex-shrink-0">
					<button
						onclick={() => showRagList = !showRagList}
						class="w-full p-3 border-b border-slate-600 bg-gradient-to-r from-slate-800 to-slate-700 flex items-center justify-between cursor-pointer hover:from-slate-700 hover:to-slate-600 transition-colors"
					>
						<div class="flex items-center space-x-2">
							<Search class="w-4 h-4 text-cyan-400" />
							<span class="text-base font-bold text-slate-100">RAGs ({rags.length})</span>
							{#if selectedRag}
								<span class="text-sm text-cyan-400">• {selectedRag}</span>
							{/if}
						</div>
						<div class="transform transition-transform {showRagList ? 'rotate-180' : ''}">
							<svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
							</svg>
						</div>
					</button>
					{#if showRagList}
						<div class="max-h-48 overflow-y-auto">
							<RagList
								{rags}
								{loading}
								bind:selectedRag
								onconfig={handleConfigRag}
								ondelete={handleRagDeleted}
							/>
						</div>
					{/if}
				</div>

				<!-- Query Interface (takes remaining space) -->
				<div class="flex-1 min-h-0">
					{#if selectedRag}
						<QueryInterface ragName={selectedRag} />
					{:else}
						<div class="glass rounded-xl shadow-2xl p-6 text-center h-full flex flex-col justify-center">
							<Database class="w-16 h-16 text-slate-600 mx-auto mb-4" />
							<h3 class="text-lg font-bold text-slate-200 mb-2">
								{rags.length === 0 ? 'Create Your First RAG' : 'Select a RAG to Query'}
							</h3>
							<p class="text-slate-400 text-sm max-w-sm mx-auto leading-relaxed mb-4">
								{rags.length === 0
									? 'Get started by creating your first RAG to organize and query your documents.'
									: 'Choose a RAG from the list above to start asking questions about your documents.'
								}
							</p>
							{#if rags.length === 0 && !loading}
								<Button
									onclick={() => showCreateModal = true}
									variant="primary"
									class="group"
								>
									<Plus class="w-4 h-4 group-hover:rotate-90 transition-transform duration-200" />
									<span class="text-sm">Create RAG</span>
								</Button>
							{/if}
						</div>
					{/if}
				</div>
			</div>

			<!-- Desktop Layout -->
			<div class="hidden lg:grid grid-cols-3 gap-8 h-full">
				<!-- RAG List Sidebar -->
				<div class="col-span-1">
					<div class="glass rounded-2xl shadow-2xl overflow-hidden h-full">
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
				<div class="col-span-2 h-full min-h-0">
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
	</main>

	<!-- Create RAG Modal -->
	<CreateRagModal
		oncreated={handleRagCreated}
		bind:open={showCreateModal}
	/>

	<!-- Config RAG Modal -->
	{#if configRagName}
		<RagConfigModal
			ragName={configRagName}
			onupdated={handleConfigUpdated}
			bind:open={showConfigModal}
		/>
	{/if}
</div>
