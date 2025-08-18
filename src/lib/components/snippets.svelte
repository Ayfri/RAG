<script module lang="ts">
	import type { SearchResultUrl, RagDocument, FileListResult } from '$lib/types.d.ts';

    export { WebUrlChips, DocNamesInline, FileNamesInline };

	function isExternalUrl(str: string) {
		try {
            const u = new URL(str); return u.protocol !== 'file:';
        } catch {
            return false;
        }
	}

	function base(path: string) {
        return new URL(path).pathname.split('/').pop() || path;
    }
</script>

{#snippet WebUrlChips(urls: SearchResultUrl[])}
	<div class="flex flex-wrap gap-1 items-center mt-1">
		{#each urls.toSorted((a, b) => a.title.localeCompare(b.title)) as url}
			{#if isExternalUrl(url.url)}
				<a href={url.url} target="_blank" rel="noopener" class="inline-block bg-cyan-900/60 text-cyan-200 px-2 py-0.5 rounded-full font-mono hover:bg-cyan-800/80 hover:underline transition-all duration-150 shadow-sm border border-cyan-700">
					{url.title}
				</a>
			{:else}
				<span class="inline-block bg-slate-700/80 text-slate-100 px-3 py-1 rounded-full font-mono border border-slate-600 shadow-sm">{url.url}</span>
			{/if}
		{/each}
	</div>
{/snippet}

{#snippet DocNamesInline(docs: RagDocument[], max: number = 3)}
	<div class="flex flex-wrap gap-1 items-center mt-1">
		{#each docs.slice(0, max) as d}
			<span class="inline-block bg-emerald-900/50 text-emerald-200 px-2 py-0.5 rounded-full font-mono border border-emerald-700 shadow-sm" title={d.source}>
				{base(d.source)}
			</span>
		{/each}
		{#if docs.length > max}
			<span class="text-slate-500 text-[0.65rem]">+{docs.length - max} more</span>
		{/if}
	</div>
{/snippet}

{#snippet FileNamesInline(list: FileListResult, max: number = 3)}
	<div class="flex flex-wrap gap-1 items-center mt-1">
		{#each list.files.slice(0, max) as f}
			<span class="inline-block bg-orange-900/40 text-orange-200 px-2 py-0.5 rounded-full font-mono border border-orange-700 shadow-sm" title={f}>
				{base(f.split(' (')[0])}
			</span>
		{/each}
		{#if list.files.length > max}
			<span class="text-slate-500 text-[0.65rem]">+{list.files.length - max} more</span>
		{/if}
	</div>
{/snippet}
