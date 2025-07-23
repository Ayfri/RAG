<script lang="ts">
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

	let { disabled, id, onchange, options, placeholder, value = $bindable(), class: className, ...rest }: Props = $props();

	function handleChange(e: Event) {
		const target = e.target as HTMLSelectElement;
		value = target.value;
		onchange?.(e);
	}
</script>

<select
	class="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-xl text-slate-100 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition-all duration-200 cursor-pointer {className}"
	{disabled}
	{id}
	bind:value={value}
	onchange={handleChange}
	{...rest}
>
	{#if placeholder}
		<option value="" disabled>{placeholder}</option>
	{/if}
	{#each options.toSorted((a, b) => a.label.localeCompare(b.label)) as option}
		<option value={option.value}>{option.label}</option>
	{/each}
</select>
