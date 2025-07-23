<script lang="ts">
	import { notifications } from '$lib/stores/notifications';
	import Notification from './Notification.svelte';
</script>

<div class="fixed top-4 right-4 z-50 w-full max-w-xs space-y-2">
	{#each $notifications as notification (notification.id)}
		<Notification {notification} />
	{/each}
</div>
