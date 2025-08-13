<script lang="ts">
    import Button from '$lib/components/common/Button.svelte';
    import MessageStats from '$lib/components/common/MessageStats.svelte';
    import TextArea from '$lib/components/common/TextArea.svelte';
    import {AlertCircle, Loader, SendHorizontal} from '@lucide/svelte';

	interface Props {
		value: string;
		loading: boolean;
		error?: string | null;
		onSubmit: () => void;
		class?: string;
	}

	let { value = $bindable(), loading, error = null, onSubmit }: Props = $props();
	let textareaElement = $state<HTMLTextAreaElement | undefined>(undefined);

	function autoResize() {
		if (textareaElement) {
			if (!value) {
				textareaElement.style.height = '44px';
				return;
			}

			textareaElement.style.height = 'auto';
			textareaElement.style.height = `${textareaElement.scrollHeight}px`;
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

	// Keep focus on textarea when it becomes available and is not loading
	$effect(() => {
		if (textareaElement && !loading) {
			// Small delay to ensure the element is fully rendered
			setTimeout(() => {
				if (textareaElement && document.activeElement !== textareaElement) {
					textareaElement.focus();
				}
			}, 0);
		}
	});

	function handleKeydown(e: KeyboardEvent) {
		const onMobile = window.innerWidth < 768;
		if (e.key === 'Enter' && !e.shiftKey && !onMobile && !loading) {
			e.preventDefault();
			onSubmit();
		}
	}

	function handleSubmit(e: Event) {
		e.preventDefault();
		if (!loading && value.trim()) {
			onSubmit();
			// Keep focus on textarea after submit with a small delay to ensure DOM updates are complete
			setTimeout(() => {
				if (textareaElement) {
					textareaElement.focus();
				}
			}, 0);
		}
	}
</script>

<div class="border-t border-slate-600 pt-1 md:py-2 md:px-1">
	{#if error}
		<div class="mb-2 p-2 bg-red-900/20 border border-red-500/30 rounded-md flex items-center gap-2 text-red-400">
			<AlertCircle size={16} />
			<span class="text-sm">{error}</span>
		</div>
	{/if}

	<form onsubmit={handleSubmit} class="flex space-x-1 md:space-x-2 items-start">
		<div class="flex flex-col gap-1 w-full">
			<TextArea
				bind:value
				bind:textareaRef={textareaElement}
				placeholder={loading ? "Message being sent..." : "Ask your question..."}
				disabled={loading}
				onkeydown={handleKeydown}
				minHeight="40px"
				class="max-h-[240px] overflow-y-auto {error ? 'border-red-500/30' : ''}"
			/>
			<div class="flex items-center justify-between">
				<div class="hidden md:block text-xs text-slate-400">
					{#if loading}
						<span class="text-amber-400">⏳ Message being sent...</span>
					{:else if error}
						<span class="text-red-400">❌ Error occurred</span>
					{:else}
						Press <span class="font-bold">Enter</span> to submit
					{/if}
				</div>

                <MessageStats text={value} targetElement={textareaElement} />
			</div>
		</div>
		<Button
			type="submit"
			disabled={!value.trim() || loading}
			size="icon"
			variant="secondary"
			title={loading ? "Message being sent..." : error ? "Fix error to send" : "Send message"}
		>
			{#if loading}
				<Loader size={24} class="animate-spin text-slate-400" />
			{:else}
				<SendHorizontal size={24} class="group-hover:scale-110 transition-transform duration-200" />
			{/if}
		</Button>
	</form>
</div>
