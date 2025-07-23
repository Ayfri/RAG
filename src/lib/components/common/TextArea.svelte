<script lang="ts">
	interface Props {
		disabled?: boolean;
		id?: string;
		placeholder?: string;
		rows?: number;
		onkeydown?: (e: KeyboardEvent) => void;
		value?: string;
	}

	let { placeholder, disabled, rows = 6, value = $bindable(), id, onkeydown, ...rest }: Props = $props();
</script>

<textarea
	class="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-xl text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent resize-none transition-all duration-200"
	{placeholder}
	{disabled}
	{rows}
	bind:value={value}
	{id}
	{onkeydown}
	{...rest}
></textarea>
