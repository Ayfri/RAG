<script lang='ts'>
	interface Props {
		accept?: string
		class?: string
		disabled?: boolean
		id?: string
		onchange?: (e: Event) => void
		webkitdirectory?: boolean
	}

	let { id, class: className, disabled, accept, onchange, webkitdirectory, ...rest }: Props = $props()

	function handleChange(e: Event) {
		onchange?.(e)
	}
</script>

<input
    class="hidden {className}"
    onchange={handleChange}
    type='file'
    {accept}
    {disabled}
    {id}
    {webkitdirectory}
    {...rest}
/>
