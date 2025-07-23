<script lang="ts">
	import { Send, Loader } from '@lucide/svelte';
	import Button from '$lib/components/common/Button.svelte';
	import Input from '$lib/components/common/Input.svelte';

	interface Props {
		value: string;
		loading: boolean;
		onSubmit: () => void;
	}

	let { value = $bindable(), loading, onSubmit }: Props = $props();

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
	<form onsubmit={handleSubmit} class="flex space-x-3 items-center h-11">
		<div class="flex-1 h-full">
			<Input
				bind:value
				class="h-full"
				placeholder="Ask your question..."
				disabled={loading}
				onkeydown={handleKeydown}
			/>
		</div>
		<Button
			type="submit"
			disabled={!value.trim() || loading}
			class="h-full px-6"
			variant="primary"
		>
			{#if loading}
				<Loader class="w-5 h-5 animate-spin" />
			{:else}
				<Send class="w-5 h-5 group-hover:translate-x-1 transition-transform duration-200" />
			{/if}
		</Button>
	</form>
</div>
