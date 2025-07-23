
<script lang="ts">
	import { X } from '@lucide/svelte';
	import { fly } from 'svelte/transition';

	interface Props {
		onclose: () => void;
		title: string;
		children: any;
	}

	let { onclose, title, children }: Props = $props();
</script>

<div
	class="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50"
	transition:fly={{ y: 20, duration: 300, delay: 50 }}
>
	<div class="glass rounded-2xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
		<div class="flex justify-between items-center p-4 border-b border-slate-600 bg-gradient-to-r from-slate-800 to-slate-700">
			<h2 class="text-xl font-bold text-slate-100">{title}</h2>
			<button onclick={onclose} class="text-slate-400 hover:text-slate-200 hover:bg-slate-700 p-1.5 rounded-xl transition-all duration-200 cursor-pointer">
				<X class="w-5 h-5" />
			</button>
		</div>

		<div class="p-4">
			{@render children()}
		</div>
	</div>
</div>
