<script lang="ts">
	import {countTokensFromText} from '$lib/helpers/tokenizer';

	interface Props {
		class?: string;
		text: string;
		hideWhenEmpty?: boolean;
	}

	let { class: className, text, hideWhenEmpty = true }: Props = $props();

	const chars = $derived(text?.length ?? 0);
	const tokens = $derived(countTokensFromText(text || ''));
	const isEmpty = $derived(!text || text.length === 0);
</script>

{#if !hideWhenEmpty || !isEmpty}
	<span class="inline-flex items-center gap-1 text-xs {className || ''}">
		<span>{chars.toLocaleString()} chars</span>
		<span>•</span>
		<span>{tokens.toLocaleString()} tokens</span>
	</span>
{/if}
