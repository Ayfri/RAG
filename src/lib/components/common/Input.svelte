<script lang="ts">
	interface Props {
		class?: string;
		disabled?: boolean;
		id?: string;
		placeholder?: string;
		type?: 'text' | 'number' | 'email' | 'file' | 'password' | 'search' | 'tel' | 'url';
		onkeydown?: (e: KeyboardEvent) => void;
		onchange?: (e: Event) => void;
		value?: string;
	}

	let { type = 'text', placeholder, disabled, value = $bindable(), id, onkeydown, onchange, class: className, ...rest }: Props = $props();
</script>

<input
	class="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-xl text-slate-100 text-base placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition-all duration-200 {className}"
	{type}
	{placeholder}
	{disabled}
	bind:value={value}
	{id}
	{onkeydown}
	{onchange}
	{...rest}
/>
