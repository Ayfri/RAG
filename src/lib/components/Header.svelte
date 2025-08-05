<script lang="ts">
	import Button from '$lib/components/common/Button.svelte';
	import {ChevronDown, Database, Menu, MessageSquare, X} from '@lucide/svelte';
	import {slide} from 'svelte/transition';

	interface Props {
		ragCount?: number;
		chatCount?: number;
		selectedRag?: string | null;
		onToggleSidebar?: () => void;
		onSelectRag?: (rag: string) => void;
		rags?: string[];		loading?: boolean;
	}

	let {
		ragCount = 0,
		chatCount = 0,
		selectedRag = null,
		onToggleSidebar = () => {},
		onSelectRag = () => {},
		rags = []
	}: Props = $props();

	let showRagDropdown = $state(false);

	function toggleRagDropdown() {
		showRagDropdown = !showRagDropdown;
	}

	function selectRag(rag: string) {
		onSelectRag(rag);
		showRagDropdown = false;
	}

	function closeRagDropdown() {
		showRagDropdown = false;
	}

	// Close dropdown when clicking outside
	$effect(() => {
		if (showRagDropdown) {
			const handleClickOutside = (event: MouseEvent) => {
				const target = event.target as HTMLElement;
				if (!target.closest('.rag-dropdown')) {
					closeRagDropdown();
				}
			};

			document.addEventListener('click', handleClickOutside);
			return () => document.removeEventListener('click', handleClickOutside);
		}
	});
</script>

<header class="bg-slate-800 border-b border-slate-700 shadow-xl flex-shrink-0">
	<div class="px-3 md:px-4 lg:px-6">
		<div class="flex justify-between items-center gap-2 py-2">
			<!-- Left section: Menu + Logo -->
			<div class="flex items-center space-x-2 md:space-x-3 min-w-0 flex-1">
				<!-- Mobile menu button -->
				<Button
					onclick={onToggleSidebar}
					variant="secondary"
					size="icon"
					class="lg:hidden"
					title="Toggle sidebar"
				>
					<Menu class="w-5 h-5" />
				</Button>

				<div class="p-1 md:p-1.5 bg-gradient-to-br from-cyan-500 to-cyan-600 rounded-lg md:rounded-xl flex-shrink-0">
					<Database class="w-4 h-4 md:w-6 md:h-6 text-white" />
				</div>
				<div class="min-w-0 flex-1">
					<h1 class="text-base md:text-xl font-bold bg-gradient-to-r from-cyan-400 to-cyan-200 bg-clip-text text-transparent truncate">
						RAG Application
					</h1>
					<p class="text-slate-400 text-xs hidden sm:block">Retrieval-Augmented Generation made simple</p>
				</div>
			</div>

			<!-- Center section: Mobile RAG selector -->
			<div class="lg:hidden relative rag-dropdown flex justify-end max-w-32">
				{#if selectedRag}
					<Button
						onclick={toggleRagDropdown}
						variant="secondary"
						class="px-2 py-1.5 text-xs font-medium flex items-center justify-end"
						title="Select RAG"
					>
						<span class="truncate">{selectedRag}</span>
						<ChevronDown class="w-3 h-3 transition-transform duration-200 {showRagDropdown ? 'rotate-180' : ''}" />
					</Button>
				{:else if rags.length > 0}
					<Button
						onclick={toggleRagDropdown}
						variant="secondary"
						class="px-2 py-1.5 text-xs font-medium flex items-center justify-end"
						title="Select RAG"
					>
						<span class="truncate">RAG ({ragCount})</span>
						<ChevronDown class="w-3 h-3 transition-transform duration-200 {showRagDropdown ? 'rotate-180' : ''}" />
					</Button>
				{/if}

				<!-- RAG Dropdown -->
				{#if showRagDropdown}
					<div class="absolute top-full w-32 left-0 right-0 mt-1 bg-slate-800 border border-slate-600 rounded-lg shadow-xl z-50" transition:slide={{ duration: 200 }}>
						<div class="p-2">
							<div class="flex items-center justify-between mb-2">
								<span class="text-xs font-medium text-slate-300">Select RAG</span>
								<Button
									onclick={closeRagDropdown}
									variant="secondary"
									size="icon"
									title="Close"
								>
									<X class="w-3 h-3" />
								</Button>
							</div>
							<div class="space-y-1 max-h-48 overflow-y-auto">
								{#each rags as rag}
									<Button
										onclick={() => selectRag(rag)}
										class="px-3 py-2 text-sm {selectedRag === rag ? 'bg-cyan-600 text-white' : 'text-slate-300 hover:bg-slate-700'}"
									>
										{rag}
									</Button>
								{/each}
							</div>
						</div>
					</div>
				{/if}
			</div>

			<!-- Right section: Desktop stats + GitHub -->
			<div class="flex items-center space-x-2 md:space-x-3">
				<!-- Desktop stats -->
				<div class="hidden md:flex items-center space-x-3 text-xs text-slate-400">
					<div class="flex items-center space-x-1">
						<Database class="w-3 h-3" />
						<span>{ragCount} RAGs</span>
					</div>
					<div class="flex items-center space-x-1">
						<MessageSquare class="w-3 h-3" />
						<span>{chatCount} chats</span>
					</div>
				</div>

				<a
					aria-label="View on GitHub"
					href="https://github.com/Ayfri/RAG"
					target="_blank"
					rel="noopener noreferrer"
					class="p-2 text-slate-400 hover:text-slate-200 transition-colors duration-200 rounded-lg hover:bg-slate-700"
					title="View on GitHub"
				>
					<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 16 16" fill="none">
						<path
							fill-rule="evenodd"
							clip-rule="evenodd"
							d="M8 0C3.58 0 0 3.58 0 8C0 11.54 2.29 14.53 5.47 15.59C5.87 15.66 6.02 15.42 6.02 15.21C6.02 15.02 6.01 14.39 6.01 13.72C4 14.09 3.48 13.23 3.32 12.78C3.23 12.55 2.84 11.84 2.5 11.65C2.22 11.5 1.82 11.13 2.49 11.12C3.12 11.11 3.57 11.7 3.72 11.94C4.44 13.15 5.59 12.81 6.05 12.6C6.12 12.08 6.33 11.73 6.56 11.53C4.78 11.33 2.92 10.64 2.92 7.58C2.92 6.71 3.23 5.99 3.74 5.43C3.66 5.23 3.38 4.41 3.82 3.31C3.82 3.31 4.49 3.1 6.02 4.13C6.66 3.95 7.34 3.86 8.02 3.86C8.7 3.86 9.38 3.95 10.02 4.13C11.55 3.09 12.22 3.31 12.22 3.31C12.66 4.41 12.38 5.23 12.3 5.43C12.81 5.99 13.12 6.7 13.12 7.58C13.12 10.65 11.25 11.33 9.47 11.53C9.76 11.78 10.01 12.26 10.01 13.01C10.01 14.08 10 14.94 10 15.21C10 15.42 10.15 15.67 10.55 15.59C13.71 14.53 16 11.53 16 8C16 3.58 12.42 0 8 0Z"
							fill="currentColor"
						/>
					</svg>
				</a>
			</div>
		</div>
	</div>
</header>
