<script lang="ts">
	import { notifications, type Notification } from '$lib/stores/notifications';
	import { onMount } from 'svelte';
	import { fly } from 'svelte/transition';
	import { X, Info, CheckCircle, AlertTriangle, AlertCircle } from '@lucide/svelte';

	interface Props {
		notification: Notification;
	}

	let { notification }: Props = $props();

	const icons = {
		info: Info,
		success: CheckCircle,
		warning: AlertTriangle,
		error: AlertCircle
	};

	const colors = {
		info: 'bg-blue-500',
		success: 'bg-green-500',
		warning: 'bg-yellow-500',
		error: 'bg-red-500'
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
	class="notification flex items-start p-4 rounded-lg shadow-lg text-white {colors[notification.type]}"
>
	<div class="flex-shrink-0">
		<Icon class="w-6 h-6" />
	</div>
	<div class="ml-3 flex-1">
		<p class="text-sm font-medium">
			{notification.message}
		</p>
	</div>
	<div class="ml-4 flex-shrink-0 flex">
		<button onclick={handleRemove} class="inline-flex rounded-md text-white hover:text-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-white">
			<span class="sr-only">Close</span>
			<X class="h-5 w-5" />
		</button>
	</div>
</div>
