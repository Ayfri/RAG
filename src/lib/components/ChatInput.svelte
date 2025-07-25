<script lang="ts">
	import Button from '$lib/components/common/Button.svelte';
	import TextArea from '$lib/components/common/TextArea.svelte';
	import {Loader, SendHorizontal} from '@lucide/svelte';

	interface Props {
		value: string;
		loading: boolean;
		onSubmit: () => void;
		class?: string;
	}

	let { value = $bindable(), loading, onSubmit }: Props = $props();
	let textareaElement = $state<HTMLTextAreaElement | undefined>(undefined);

	function autoResize() {
		if (textareaElement) {
			if (!value) {
				textareaElement.style.height = '44px';
				return;
			}

			textareaElement.style.height = 'auto';
			textareaElement.style.height = textareaElement.scrollHeight + 'px';
		}
	}

	// Auto-resize when value changes
	$effect(() => {
		if (value !== undefined) {
			autoResize();
		}

		// Auto-resize when textarea element is available
		if (textareaElement) {
			autoResize();
		}
	});

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			onSubmit();
		}
	}

	function handleSubmit(e: Event) {
		e.preventDefault();
		onSubmit();
	}
</script>

<div class="border-t border-slate-600 py-4 px-1">
	<form onsubmit={handleSubmit} class="flex space-x-3 items-start">
		<TextArea
			bind:value
			bind:textareaRef={textareaElement}
			placeholder="Ask your question..."
			disabled={loading}
			onkeydown={handleKeydown}
			minHeight="44px"
			class="max-h-[200px] overflow-y-auto"
		/>
		<Button
			type="submit"
			disabled={!value.trim() || loading}
			size="icon"
			variant="secondary"
		>
			{#if loading}
				<Loader class="w-5 h-5 animate-spin" />
			{:else}
				<SendHorizontal class="w-5 h-5 group-hover:scale-110 transition-transform duration-200" />
			{/if}
		</Button>
	</form>
</div>
