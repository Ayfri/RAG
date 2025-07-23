<script lang='ts'>
	interface Props {
		accept?: string
		class?: string
		disabled?: boolean
		id?: string
		onchange?: (e: Event) => void
	}

	let { id, class: className, disabled, accept, onchange, ...rest }: Props = $props()

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
    {...rest}
/>
