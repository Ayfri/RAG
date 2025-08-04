<script lang="ts">
	import { ChevronDown, Globe } from '@lucide/svelte';
	import type { SearchResult, SearchResultUrl } from '$lib/types.d.ts';

	interface Props {
		sources: SearchResult[];
	}

	let { sources }: Props = $props();

	let isOpen = $state(false);

	function isUrl(str: string) {
		try {
			const url = new URL(str);
			return url.protocol !== 'file:';
		} catch {
			return false;
		}
	}

	function toggle() {
		isOpen = !isOpen;
	}

	let filteredSources = $derived(sources.filter((source) => source.urls.length > 0));
	let totalUrls = $derived(filteredSources.reduce((count, source) => count + source.urls.length, 0));
</script>

{#if filteredSources.length > 0}
	<div class="space-y-3">
		<!-- Header with toggle -->
		<button
			type="button"
			class="flex items-center gap-2 w-full text-left focus:outline-none group text-[0.7rem] cursor-pointer"
			onclick={toggle}
			aria-expanded={isOpen}
		>
			<Globe class="w-4 h-4 text-blue-400 flex-shrink-0" />
			<strong class="text-slate-400">Web sources ({totalUrls}):</strong>
			<ChevronDown
				class="w-4 h-4 text-slate-300 transition-transform duration-200"
				style="transform: rotate({isOpen ? 180 : 0}deg);"
				aria-hidden="true"
			/>
		</button>

		<!-- Collapsible content -->
		<div
			class="overflow-hidden transition-all duration-300"
			style="max-height: {isOpen ? '500px' : '0'}; opacity: {isOpen ? 1 : 0};"
			aria-hidden={!isOpen}
		>
			{#if isOpen}
				<div class="space-y-3">
					{#each filteredSources as source}
						<div class="mb-2">
							{#if source.urls && source.urls.length > 0}
								<div class="flex flex-wrap gap-1 items-center mt-1">
									{#each source.urls.toSorted((a: SearchResultUrl, b: SearchResultUrl) => a.title.localeCompare(b.title)) as url}
										{#if isUrl(url.url)}
											<a href={url.url} target="_blank" rel="noopener" class="inline-block bg-cyan-900/60 text-cyan-200 px-2 py-0.5 rounded-full font-mono hover:bg-cyan-800/80 hover:underline transition-all duration-150 shadow-sm border border-cyan-700">
												{url.title}
											</a>
										{:else}
											<span class="inline-block bg-slate-700/80 text-slate-100 px-3 py-1 rounded-full font-mono border border-slate-600 shadow-sm">{url.url}</span>
										{/if}
									{/each}
								</div>
							{/if}
						</div>
					{/each}
				</div>
			{/if}
		</div>
	</div>
{/if}
