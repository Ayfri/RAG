
<script lang="ts">
	import { X } from '@lucide/svelte';
	import { fly, fade } from 'svelte/transition';
	import Button from '$lib/components/common/Button.svelte';

	interface Props {
		children: any;
		open: boolean;
		title: string;
	}

	let { title, children, open = $bindable(false) }: Props = $props();
</script>

<svelte:window
	on:keydown={(e) => e.key === 'Escape' && (open = false)}
	on:click={(e) => e.target === e.currentTarget && (open = false)}
/>

{#if open}
	<div
		class="absolute inset-0 flex items-center justify-center z-50 w-screen h-screen bg-black/50 backdrop-blur-sm"
		aria-modal="true"
		aria-labelledby={title}
	>
		<div
			class="glass rounded-2xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto"
			transition:fly={{ y: 20, duration: 300, delay: 50 }}
			onclick={(e) => e.stopPropagation()}
		>
			<div class="flex justify-between items-center p-4 border-b border-slate-600 bg-gradient-to-r from-slate-800 to-slate-700">
				<h2 class="text-xl font-bold text-slate-100">{title}</h2>
				<Button onclick={() => open = false} variant="secondary" size="icon" title="Close modal">
					<X class="w-5 h-5" />
				</Button>
			</div>

			<div class="p-4">
				{@render children()}
			</div>
		</div>
	</div>
{/if}
