<script lang="ts">
	import { ChevronDown } from '@lucide/svelte';

	interface Option {
		label: string;
		value: string;
	}

	interface Props {
		class?: string;
		disabled?: boolean;
		id?: string;
		onchange?: (e: Event) => void;
		options: Option[];
		placeholder?: string;
		value?: string;
	}

	let {
		class: className = '',
		disabled,
		id,
		onchange,
		options,
		placeholder,
		value = $bindable(),
		...rest
	}: Props = $props();

	function handleChange(e: Event) {
		const target = e.target as HTMLSelectElement;
		value = target.value;
		onchange?.(e);
	}
</script>

<div class="relative w-full {className}">
	<select
		class="w-full appearance-none rounded-xl border border-slate-600 bg-slate-700/50 py-2 pl-3 pr-10 text-slate-100 transition-all duration-200 hover:bg-slate-700/80 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-cyan-500 cursor-pointer"
		{disabled}
		{id}
		bind:value
		onchange={handleChange}
		{...rest}
	>
		{#if placeholder}
			<option value="" disabled>{placeholder}</option>
		{/if}
		{#each options.toSorted((a, b) => a.label.localeCompare(b.label)) as option}
			<option class="bg-slate-800 text-white" value={option.value}>{option.label}</option>
		{/each}
	</select>
	<div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-400">
		<ChevronDown size={18} />
	</div>
</div>
