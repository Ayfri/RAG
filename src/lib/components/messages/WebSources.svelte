<script lang="ts">
	import type {SearchResult, SearchResultUrl} from '$lib/types.d.ts';
	import {ChevronDown, Globe} from '@lucide/svelte';
	import { WebUrlChips } from '$lib/components/snippets.svelte';

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

	let filteredSources = $derived(sources.filter(source => source.urls.length > 0));
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
								{@render WebUrlChips(source.urls)}
							{/if}
						</div>
					{/each}
				</div>
			{/if}
		</div>
	</div>
{/if}
