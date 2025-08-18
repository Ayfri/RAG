<script lang="ts">
	import { notifications, type Notification } from '$lib/stores/notifications';
	import { onMount } from 'svelte';
	import { fly } from 'svelte/transition';
	import { X, Info, CircleCheck, TriangleAlert, CircleAlert } from '@lucide/svelte';
	import Button from '$lib/components/common/Button.svelte';

	interface Props {
		notification: Notification;
	}

	let { notification }: Props = $props();

	const icons = {
		info: Info,
		success: CircleCheck,
		warning: TriangleAlert,
		error: CircleAlert
	};

	const colors = {
		info: 'bg-blue-800/80 text-blue-100 border border-blue-700',
		success: 'bg-green-800/80 text-green-100 border border-green-700',
		warning: 'bg-yellow-800/80 text-yellow-100 border border-yellow-700',
		error: 'bg-red-800/80 text-red-100 border border-red-700'
	};

	let timeoutId: number;

	const Icon = $derived(icons[notification.type]);

	function handleRemove() {
		notifications.remove(notification.id);
	}

	onMount(() => {
		if (notification.duration) {
			timeoutId = window.setTimeout(handleRemove, notification.duration);
		}
		return () => clearTimeout(timeoutId);
	});
</script>

<div
	in:fly={{ y: -20, duration: 300 }}
	out:fly={{ x: '100%', duration: 200 }}
	class="notification flex items-center p-3 rounded-lg shadow-md text-sm {colors[notification.type]} space-x-3 w-80"
>
	<div class="flex-shrink-0">
		<Icon class="w-5 h-5" />
	</div>
	<div class="flex-1">
		<p class="font-medium">
			{notification.message}
		</p>
	</div>
	<div class="flex-shrink-0">
		<Button onclick={handleRemove} variant="ghost" size="icon" class="text-white/70 hover:text-white hover:bg-white/10">
			<span class="sr-only">Close</span>
			<X class="h-4 w-4" />
		</Button>
	</div>
</div>
