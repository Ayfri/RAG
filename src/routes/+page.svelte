<script lang="ts">
	import { onMount } from 'svelte';
	import { Plus, FileText, Search, Database, MessageSquare } from '@lucide/svelte';
	import Header from '$lib/components/Header.svelte';
	import CreateRagModal from '$lib/components/CreateRagModal.svelte';
	import RagConfigModal from '$lib/components/RagConfigModal.svelte';
	import QueryInterface from '$lib/components/QueryInterface.svelte';
	import ChatSessions from '$lib/components/ChatSessions.svelte';
	import Button from '$lib/components/common/Button.svelte';

	let rags: string[] = $state([]);
	let selectedRag: string | null = $state(null);
	let showCreateModal = $state(false);
	let showConfigModal = $state(false);
	let configRagName = $state('');
	let loading = $state(true);
	let error = $state('');
	let showRagList = $state(false);
	let totalChatCount = $state(0);

	async function loadRags() {
		try {
			loading = true;
			const response = await fetch('/api/rag');
			if (!response.ok) throw new Error('Failed to load RAGs');
			rags = await response.json();
			await loadTotalChatCount();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Unknown error';
		} finally {
			loading = false;
		}
	}

	async function loadTotalChatCount() {
		try {
			// Import chatStorage to count all sessions across all RAGs
			const { chatStorage } = await import('$lib/helpers/chat-storage');
			await chatStorage.init();
			const allSessions = await chatStorage.getAllSessions();
			totalChatCount = allSessions.length;
		} catch (err) {
			console.error('Failed to load chat count:', err);
			totalChatCount = 0;
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

	// Listen for session events to update chat count
	function handleSessionEvent() {
		loadTotalChatCount();
	}

	function handleConfigRag(ragName: string) {
		configRagName = ragName;
		showConfigModal = true;
	}

	function handleConfigUpdated() {
		// Configuration updated, no need to reload RAGs as the list doesn't change
		showConfigModal = false;
	}

	onMount(() => {
		loadRags();

		// Listen for session events
		window.addEventListener('sessionCreated', handleSessionEvent);
		window.addEventListener('sessionDeleted', handleSessionEvent);
		window.addEventListener('sessionRenamed', handleSessionEvent);
	});
</script>

<div class="h-screen bg-slate-900 flex flex-col">
	<!-- Header -->
	<Header ragCount={rags.length} chatCount={totalChatCount} />

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

		<!-- RAG Selector - Compact top bar -->
		<div class="mb-4">
			<div class="glass rounded-xl shadow-xl p-3">
				<div class="flex items-center justify-between">
					<div class="flex items-center space-x-3">
						<Search class="w-4 h-4 text-cyan-400" />
						<span class="text-sm font-medium text-slate-300">RAGs:</span>
						{#if loading}
							<div class="flex items-center space-x-2">
								<div class="w-4 h-4 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin"></div>
								<span class="text-xs text-slate-400">Loading...</span>
							</div>
						{:else}
							<div class="flex items-center justify-center flex-wrap gap-2">
								{#each rags as rag}
									<Button
										variant="secondary"
										onclick={() => selectedRag = rag}
										class={`!px-3 !py-1.5 text-xs ${selectedRag === rag ? 'bg-cyan-600 text-white shadow-lg' : 'bg-slate-700 text-slate-300 hover:bg-slate-600 hover:text-slate-200'}`}
										title="Click to query this RAG"
									>
										{rag} <span class="text-[0.675rem] {selectedRag === rag ? 'text-slate-200' : 'text-slate-400'}">({rag.length} documents)</span>
									</Button>
								{/each}
								{#if rags.length === 0}
									<span class="text-xs text-slate-500 italic">No RAGs available</span>
								{/if}
							</div>
						{/if}
					</div>
					<Button
						onclick={() => showCreateModal = true}
						class="px-3 py-1.5 bg-gradient-to-r from-cyan-500 to-cyan-600 hover:from-cyan-600 hover:to-cyan-700 text-white rounded-lg text-xs font-medium transition-all duration-200 shadow-lg hover:shadow-cyan-500/25"
					>
						<Plus class="w-3 h-3" />
						<span class="ml-1">New RAG</span>
					</Button>
				</div>
			</div>
		</div>

		<!-- Main Content Area -->
		<div class="flex-1 min-h-0 flex flex-col lg:flex-row gap-3 lg:gap-6">
			<!-- Chat Sessions Sidebar -->
			<div class="lg:w-80 flex-shrink-0">
				<div class="glass rounded-xl shadow-2xl overflow-hidden h-full">
					<div class="p-3 border-b border-slate-600 bg-gradient-to-r from-slate-800 to-slate-700">
						<div class="flex items-center justify-between">
							<div class="flex items-center space-x-2">
								<MessageSquare class="w-4 h-4 text-cyan-400" />
								<span class="text-sm font-bold text-slate-100">Chat Sessions</span>
							</div>
							{#if selectedRag}
								<span class="text-xs text-cyan-400 bg-cyan-900/30 px-2 py-1 rounded-full">
									{selectedRag}
								</span>
							{/if}
						</div>
					</div>
					{#if selectedRag}
						<div class="h-full">
							<ChatSessions
								ragName={selectedRag}
								onSessionSelected={(sessionId, messages) => {
									// Pass the session data to QueryInterface via custom event
									window.dispatchEvent(new CustomEvent('sessionSelected', {
										detail: { sessionId, messages, ragName: selectedRag }
									}));
								}}
							/>
						</div>
					{:else}
						<div class="p-4 text-center text-slate-400">
							<MessageSquare class="w-8 h-8 mx-auto mb-2 text-slate-600" />
							<p class="text-xs">Select a RAG to view sessions</p>
						</div>
					{/if}
				</div>
			</div>

			<!-- Query Interface -->
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
								: 'Choose a RAG from the top bar to start asking questions about your documents.'}
						</p>
						{#if rags.length === 0 && !loading}
							<div class="mt-2">
								<Button
									onclick={() => showCreateModal = true}
									variant="primary"
									class="group"
								>
									<Plus class="w-4 h-4 group-hover:rotate-90 transition-transform duration-200" />
									<span class="text-sm">Create{rags.length === 0 ? ' Your First' : ''} RAG</span>
								</Button>
							</div>
						{/if}
					</div>
				{/if}
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
