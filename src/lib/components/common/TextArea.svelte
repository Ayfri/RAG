<script lang="ts">
	interface Props {
		disabled?: boolean;
		id?: string;
		placeholder?: string;
		onkeydown?: (e: KeyboardEvent) => void;
		value?: string;
		textareaRef?: HTMLTextAreaElement;
		class?: string;
		minHeight?: string;
	}

	let { placeholder, disabled, value = $bindable(), id, onkeydown, textareaRef = $bindable(), class: className, minHeight = '44px', ...rest }: Props = $props();
</script>

<textarea
	class="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-xl text-slate-100 text-base placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent resize-none transition-all duration-200 {className || ''}"
	style:min-height={minHeight}
	{placeholder}
	{disabled}
	bind:value
	bind:this={textareaRef}
	{id}
	{onkeydown}
	{...rest}
></textarea>
