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
		const onMobile = window.innerWidth < 768;
		if (e.key === 'Enter' && !e.shiftKey && !onMobile) {
			e.preventDefault();
			onSubmit();
		}
	}

	function handleSubmit(e: Event) {
		e.preventDefault();
		onSubmit();
		// Keep focus on textarea after submit
		if (textareaElement) {
			textareaElement.focus();
		}
	}
</script>

<div class="border-t border-slate-600 py-2 md:py-4 px-1">
	<form onsubmit={handleSubmit} class="flex space-x-1 md:space-x-3 items-start">
		<div class="flex flex-col gap-1 w-full">
			<TextArea
				bind:value
				bind:textareaRef={textareaElement}
				placeholder="Ask your question..."
				disabled={loading}
				onkeydown={handleKeydown}
				minHeight="44px"
				class="max-h-[200px] overflow-y-auto"
			/>
			<div class="flex items-center justify-between">
				<div class="text-xs text-slate-400">
					Press <span class="font-bold">Enter</span> to submit
				</div>
				{#if value.length > 0}
					<div class="text-xs text-slate-400">
						{value.length}
					</div>
				{/if}
			</div>
		</div>
		<Button
			type="submit"
			disabled={!value.trim() || loading}
			size="icon"
			variant="secondary"
		>
			{#if loading}
				<Loader size={24} class="animate-spin" />
			{:else}
				<SendHorizontal size={24} class="group-hover:scale-110 transition-transform duration-200" />
			{/if}
		</Button>
	</form>

</div>
