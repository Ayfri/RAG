<script lang="ts">
	import '../app.css';
	import Notifications from '$lib/components/common/Notifications.svelte';

	let { children } = $props();
</script>

<Notifications />
{@render children()}
