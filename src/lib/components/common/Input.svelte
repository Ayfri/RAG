<script lang="ts">
	interface Props {
		disabled?: boolean;
		id?: string;
		placeholder?: string;
		type?: 'text' | 'number' | 'email' | 'password' | 'search' | 'tel' | 'url';
		onkeydown?: (e: KeyboardEvent) => void;
		value?: string;
	}

	let { type = 'text', placeholder, disabled, value = $bindable(), id, onkeydown, ...rest }: Props = $props();
</script>

<input
	class="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-xl text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition-all duration-200"
	{type}
	{placeholder}
	{disabled}
	bind:value={value}
	{id}
	{onkeydown}
	{...rest}
/>
